"""
Layer 4: Distributed Revocation & Shamir Threshold Key Recovery
Implements m-of-n Supernode Quorum Certificate Revocation Records (CRR),
revocation state machine transitions, eviction foundations,
and Shamir's (k, n) Threshold Secret Sharing with authorized key recovery and rotation.
"""

import time
import secrets
import copy
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Set, Any
from cryptography.hazmat.primitives import serialization
from src.layer1_identity import PeerIdentity, PeerState


# 256-bit prime for modular arithmetic in Shamir's Secret Sharing
# Standard NIST prime (secp256k1 order or similar safe large prime)
PRIME = 2**256 - 189


# =============================================================================
# 1. CERTIFICATE REVOCATION RECORD (CRR)
# =============================================================================

@dataclass
class CertificateRevocationRecord:
    revoked_did: str
    revoked_pubkey_hex: str
    reason: str
    timestamp: float
    supernode_signatures: Dict[str, str] = field(default_factory=dict)
    revocation_id: str = ""
    evidence_id: str = ""

    def payload_bytes(self) -> bytes:
        """
        Canonical signed payload per PROTOCOL_SPEC v2.2.0:
        PKI_V2_CRR:<revocation_id>:<revoked_did>:<revoked_pubkey_hex>:<reason>:<evidence_id>:<timestamp>
        Dual-mode fallback to legacy format if revocation_id and evidence_id are omitted.
        """
        if self.revocation_id or self.evidence_id:
            data = f"PKI_V2_CRR:{self.revocation_id}:{self.revoked_did}:{self.revoked_pubkey_hex}:{self.reason}:{self.evidence_id}:{self.timestamp}"
        else:
            data = f"{self.revoked_did}:{self.revoked_pubkey_hex}:{self.reason}:{self.timestamp}"
        return data.encode("utf-8")

    def is_quorum_approved(self, supernode_pubkeys: Dict[str, str], threshold_m: int) -> bool:
        """
        Validates threshold quorum authorization:
        1. Configurable threshold m (> 0)
        2. Known eligible signer set
        3. Unique signer enforcement (distinct valid signers)
        4. Valid Ed25519 signatures
        5. Signer identity DID binding
        """
        if threshold_m <= 0:
            return False
        valid_signers: Set[str] = set()
        payload = self.payload_bytes()

        for sn_did, sig_hex in self.supernode_signatures.items():
            if sn_did in supernode_pubkeys:
                pubkey_hex = supernode_pubkeys[sn_did]
                # Validate DID binding
                if not PeerIdentity.is_valid_did(sn_did, pubkey_hex):
                    continue
                if PeerIdentity.verify_peer_signature(pubkey_hex, payload, sig_hex):
                    valid_signers.add(sn_did)

        return len(valid_signers) >= threshold_m


# =============================================================================
# 2. REVOCATION PROPOSAL
# =============================================================================

@dataclass
class RevocationProposal:
    proposal_id: str
    reporter_did: str
    accused_did: str
    evidence: Any  # Must bind a certified FaultEvidenceRecord
    timestamp: float
    timeout: float = 600.0
    reporter_sig_hex: str = ""
    evidence_id: str = ""

    def __post_init__(self):
        if not self.evidence_id and hasattr(self.evidence, "evidence_id"):
            self.evidence_id = getattr(self.evidence, "evidence_id", "")

    def payload_bytes(self) -> bytes:
        data = f"PKI_V2_REVOCATION_PROPOSAL:{self.proposal_id}:{self.reporter_did}:{self.accused_did}:{self.evidence_id}:{self.timestamp}:{self.timeout}"
        return data.encode("utf-8")

    def verify(self, reporter_pubkey_hex: str, max_drift_seconds: float = 300.0) -> bool:
        if not self.reporter_sig_hex:
            return False
        if not PeerIdentity.is_valid_did(self.reporter_did, reporter_pubkey_hex):
            return False
        now = time.time()
        if abs(now - self.timestamp) > max_drift_seconds:
            return False
        # Proposal must bind genuine fault evidence with mathematical contradiction
        if not hasattr(self.evidence, "delivered_chunk_hash") or not hasattr(self.evidence, "authentic_chunk_hash"):
            return False
        if getattr(self.evidence, "reporter_did", "") != self.reporter_did:
            return False
        if getattr(self.evidence, "accused_did", "") != self.accused_did:
            return False
        return PeerIdentity.verify_peer_signature(reporter_pubkey_hex, self.payload_bytes(), self.reporter_sig_hex)


# =============================================================================
# 3. LOCAL REVOCATION STORE
# =============================================================================

class LocalRevocationStore:
    """
    Deterministic node-local store for processed CRRs and active proposals.
    Strictly node-local state; makes no claim of global distributed consensus.
    """
    def __init__(self):
        self._records_by_did: Dict[str, CertificateRevocationRecord] = {}
        self._records_by_id: Dict[str, CertificateRevocationRecord] = {}
        self._proposals: Dict[str, RevocationProposal] = {}
        self._seen_crr_ids: Set[str] = set()

    def store_crr(
        self,
        crr: CertificateRevocationRecord,
        eligible_supernodes: Dict[str, str],
        threshold_m: int
    ) -> bool:
        """
        Stores CRR after strict quorum and format verification. Rejects duplicates.
        """
        if not crr.is_quorum_approved(eligible_supernodes, threshold_m):
            return False
        crr_id = crr.revocation_id or f"crr-{crr.revoked_did}-{crr.timestamp}"
        if crr_id in self._seen_crr_ids:
            return False  # Duplicate rejection
        self._seen_crr_ids.add(crr_id)
        self._records_by_did[crr.revoked_did] = crr
        self._records_by_id[crr_id] = crr
        return True

    def is_revoked(self, did: str) -> bool:
        return did in self._records_by_did

    def get_crr(self, did: str) -> Optional[CertificateRevocationRecord]:
        return self._records_by_did.get(did)

    def get_by_revocation_id(self, revocation_id: str) -> Optional[CertificateRevocationRecord]:
        return self._records_by_id.get(revocation_id)

    def store_proposal(self, proposal: RevocationProposal) -> bool:
        if proposal.proposal_id in self._proposals:
            return False
        self._proposals[proposal.proposal_id] = proposal
        return True

    def get_proposal(self, proposal_id: str) -> Optional[RevocationProposal]:
        return self._proposals.get(proposal_id)


# =============================================================================
# 4. REVOCATION STATE MACHINE & COORDINATOR
# =============================================================================

class RevocationCoordinator:
    """
    Coordinates supernode voting, timeout fallback, and deterministic
    revocation state transitions per PROTOCOL_SPEC v2.2.0:
    UNKNOWN -> ACTIVE -> SUSPECTED -> REVOCATION_PROPOSED -> REVOKED.
    """
    def __init__(
        self,
        supernode_pubkeys: Dict[str, str],
        threshold_m: int,
        voting_timeout: float = 600.0,
        subjective_suspicion_timeout: float = 300.0
    ):
        self.supernode_pubkeys = dict(supernode_pubkeys)
        self.threshold_m = threshold_m
        self.voting_timeout = voting_timeout
        self.subjective_suspicion_timeout = subjective_suspicion_timeout

        self.peer_states: Dict[str, PeerState] = {}
        # did -> {"is_certified": bool, "timestamp": float, "timeout": float}
        self.suspicion_records: Dict[str, Dict[str, Any]] = {}
        self.proposals: Dict[str, RevocationProposal] = {}
        # proposal_id -> Dict[supernode_did, signature_hex]
        self.proposal_votes: Dict[str, Dict[str, str]] = {}
        self.revocation_store = LocalRevocationStore()

    def set_peer_state(self, did: str, state: PeerState) -> None:
        self.peer_states[did] = state

    def get_peer_state(self, did: str) -> PeerState:
        return self.peer_states.get(did, PeerState.UNKNOWN)

    def record_suspicion(self, did: str, is_certified: bool, timestamp: Optional[float] = None) -> bool:
        """
        ACTIVE -> SUSPECTED transition upon certified fault or subjective dispute.
        """
        curr = self.get_peer_state(did)
        if curr == PeerState.REVOKED:
            return False  # Revoked peer cannot transition
        ts = time.time() if timestamp is None else timestamp
        self.peer_states[did] = PeerState.SUSPECTED
        self.suspicion_records[did] = {
            "is_certified": is_certified,
            "timestamp": ts,
            "timeout": self.subjective_suspicion_timeout
        }
        return True

    def check_suspicion_expiry(self, did: str, current_time: Optional[float] = None) -> bool:
        """
        SUSPECTED -> ACTIVE ONLY for unverified subjective suspicion after timer.
        CERTIFIED SUSPICION NEVER EXPIRES TO ACTIVE.
        """
        curr = self.get_peer_state(did)
        if curr != PeerState.SUSPECTED:
            return False
        rec = self.suspicion_records.get(did)
        if not rec:
            return False
        if rec["is_certified"]:
            # Rule T3b: Certified suspicion retains degraded state until adjudication/revocation
            return False

        now = time.time() if current_time is None else current_time
        if now >= rec["timestamp"] + rec["timeout"]:
            self.peer_states[did] = PeerState.ACTIVE
            del self.suspicion_records[did]
            return True
        return False

    def submit_proposal(self, proposal: RevocationProposal, current_time: Optional[float] = None) -> bool:
        """
        SUSPECTED -> REVOCATION_PROPOSED transition upon valid proposal submission.
        Rejects proposals if peer is ACTIVE (skipping SUSPECTED forbidden) or REVOKED.
        """
        accused_did = proposal.accused_did
        curr_state = self.get_peer_state(accused_did)
        if curr_state != PeerState.SUSPECTED:
            return False  # Cannot skip SUSPECTED or propose non-suspected peer
        if proposal.proposal_id in self.proposals:
            return False  # Duplicate proposal ID

        self.proposals[proposal.proposal_id] = proposal
        self.proposal_votes[proposal.proposal_id] = {}
        self.peer_states[accused_did] = PeerState.REVOCATION_PROPOSED
        self.revocation_store.store_proposal(proposal)
        return True

    def cast_vote(
        self,
        proposal_id: str,
        supernode_did: str,
        supernode_sig_hex: str
    ) -> Tuple[bool, Optional[CertificateRevocationRecord]]:
        """
        Casts a supernode vote on a pending proposal.
        If quorum m-of-n is reached, transitions REVOCATION_PROPOSED -> REVOKED.
        """
        if proposal_id not in self.proposals:
            return False, None
        if supernode_did not in self.supernode_pubkeys:
            return False, None  # Ineligible signer
        votes = self.proposal_votes[proposal_id]
        if supernode_did in votes:
            return False, None  # Duplicate vote from same signer

        prop = self.proposals[proposal_id]
        crr_id = f"crr-{prop.proposal_id}"
        accused_pubkey = prop.accused_did[len("did:peer:2.Ez"):]
        draft_crr = CertificateRevocationRecord(
            revoked_did=prop.accused_did,
            revoked_pubkey_hex=accused_pubkey,
            reason="ATTRIBUTABLE_INCONSISTENT_DELIVERY",
            timestamp=prop.timestamp,
            supernode_signatures={supernode_did: supernode_sig_hex},
            revocation_id=crr_id,
            evidence_id=prop.evidence_id
        )

        sn_pub = self.supernode_pubkeys[supernode_did]
        if not PeerIdentity.verify_peer_signature(sn_pub, draft_crr.payload_bytes(), supernode_sig_hex):
            return False, None  # Invalid signature

        votes[supernode_did] = supernode_sig_hex

        # Check if threshold reached
        if len(votes) >= self.threshold_m:
            final_crr = CertificateRevocationRecord(
                revoked_did=prop.accused_did,
                revoked_pubkey_hex=accused_pubkey,
                reason="ATTRIBUTABLE_INCONSISTENT_DELIVERY",
                timestamp=prop.timestamp,
                supernode_signatures=copy.deepcopy(votes),
                revocation_id=crr_id,
                evidence_id=prop.evidence_id
            )
            self.revocation_store.store_crr(final_crr, self.supernode_pubkeys, self.threshold_m)
            self.peer_states[prop.accused_did] = PeerState.REVOKED
            return True, final_crr

        return True, None

    def check_proposal_timeout(self, proposal_id: str, current_time: Optional[float] = None) -> bool:
        """
        REVOCATION_PROPOSED -> SUSPECTED transition when voting window T_vote expires.
        NEVER TRANSITIONS TO ACTIVE.
        """
        if proposal_id not in self.proposals:
            return False
        votes = self.proposal_votes.get(proposal_id, {})
        if len(votes) >= self.threshold_m:
            return False  # Already approved

        prop = self.proposals[proposal_id]
        now = time.time() if current_time is None else current_time
        if now >= prop.timestamp + prop.timeout:
            # Fallback to SUSPECTED, NEVER ACTIVE
            self.peer_states[prop.accused_did] = PeerState.SUSPECTED
            del self.proposals[proposal_id]
            return True
        return False

    def validate_transition(self, current_state: PeerState, target_state: PeerState, is_certified: bool = False) -> None:
        """
        Explicit guard enforcing forbidden state machine transitions.
        """
        if current_state == PeerState.REVOCATION_PROPOSED and target_state == PeerState.ACTIVE:
            raise ValueError("Forbidden transition: REVOCATION_PROPOSED cannot transition to ACTIVE")
        if current_state == PeerState.SUSPECTED and target_state == PeerState.ACTIVE and is_certified:
            raise ValueError("Forbidden transition: Certified SUSPECTED cannot expire to ACTIVE")
        if current_state == PeerState.ACTIVE and target_state == PeerState.REVOCATION_PROPOSED:
            raise ValueError("Forbidden transition: Cannot skip SUSPECTED state to reach REVOCATION_PROPOSED")
        if current_state == PeerState.REVOKED and target_state != PeerState.REVOKED:
            raise ValueError("Forbidden transition: REVOKED is permanent")


# =============================================================================
# 5. EVICTION & PROPAGATION FOUNDATIONS
# =============================================================================

def evict_peer_from_mesh(
    mesh: Any,
    crr: CertificateRevocationRecord,
    eligible_supernodes: Dict[str, str],
    threshold_m: int
) -> bool:
    """
    Executes Layer 4 peer eviction through the existing Layer 2 mesh interface.
    Verifies CRR validity, quorum threshold, and target DID bindings.
    """
    if not crr.is_quorum_approved(eligible_supernodes, threshold_m):
        return False
    if not PeerIdentity.is_valid_did(crr.revoked_did, crr.revoked_pubkey_hex):
        return False
    return mesh.evict_peer(crr.revoked_did, crr)


def process_incoming_crr(
    crr: CertificateRevocationRecord,
    eligible_supernodes: Dict[str, str],
    threshold_m: int,
    store: LocalRevocationStore,
    coordinator: Optional[RevocationCoordinator] = None,
    max_drift_seconds: float = 300.0,
    current_time: Optional[float] = None
) -> bool:
    """
    Local handling for CRR received via propagation gossip:
    Verifies serialization, signatures, signer eligibility, unique signers,
    quorum threshold, target DID, and freshness.
    """
    if not crr.revoked_did or not crr.revoked_pubkey_hex or not crr.reason:
        return False
    now = time.time() if current_time is None else current_time
    if abs(now - crr.timestamp) > max_drift_seconds:
        return False
    if not PeerIdentity.is_valid_did(crr.revoked_did, crr.revoked_pubkey_hex):
        return False
    if not crr.is_quorum_approved(eligible_supernodes, threshold_m):
        return False
    if not store.store_crr(crr, eligible_supernodes, threshold_m):
        return False
    if coordinator is not None:
        coordinator.peer_states[crr.revoked_did] = PeerState.REVOKED
    return True


# =============================================================================
# 6. KEY RECOVERY AUTHORIZATION & TOKEN (AuthTok)
# =============================================================================

@dataclass
class RecoveryAuthorizationToken:
    token_id: str
    subject_did: str
    requester_pubkey_hex: str
    custodian_did: str
    timestamp: float
    expiry: float
    authorization_scope: str = "KEY_RECOVERY"
    guardian_signature_hex: str = ""

    def payload_bytes(self) -> bytes:
        data = f"PKI_V2_RECOVER_AUTHTOK:{self.token_id}:{self.subject_did}:{self.requester_pubkey_hex}:{self.custodian_did}:{self.timestamp}:{self.expiry}:{self.authorization_scope}"
        return data.encode("utf-8")

    def verify(self, guardian_pubkey_hex: str, current_time: Optional[float] = None) -> bool:
        if not self.guardian_signature_hex:
            return False
        now = time.time() if current_time is None else current_time
        if now > self.expiry or now < self.timestamp - 300.0:
            return False
        if len(self.requester_pubkey_hex) != 64:
            return False
        return PeerIdentity.verify_peer_signature(guardian_pubkey_hex, self.payload_bytes(), self.guardian_signature_hex)


@dataclass
class RecoveryRequest:
    request_id: str
    subject_did: str
    requester_pubkey_hex: str
    timestamp: float
    auth_token: RecoveryAuthorizationToken
    requester_sig_hex: str = ""

    def payload_bytes(self) -> bytes:
        data = f"PKI_V2_RECOVER_REQ:{self.request_id}:{self.subject_did}:{self.requester_pubkey_hex}:{self.auth_token.token_id}:{self.timestamp}"
        return data.encode("utf-8")

    def verify(self, guardian_pubkey_hex: str, current_time: Optional[float] = None) -> bool:
        if not self.requester_sig_hex:
            return False
        now = time.time() if current_time is None else current_time
        if abs(now - self.timestamp) > 300.0:
            return False
        # 1. Requester must authenticate with their signature
        if not PeerIdentity.verify_peer_signature(self.requester_pubkey_hex, self.payload_bytes(), self.requester_sig_hex):
            return False
        # 2. Token must be validly authorized by guardian
        if not self.auth_token.verify(guardian_pubkey_hex, current_time=now):
            return False
        # 3. Token bindings must match
        if self.auth_token.subject_did != self.subject_did:
            return False
        if self.auth_token.requester_pubkey_hex != self.requester_pubkey_hex:
            return False
        return True


class KeyRecoveryCoordinator:
    """
    Separates authentication, authorization, secret reconstruction, and key rotation.
    Enforces replay protection on recovery tokens and requests.
    """
    def __init__(self, guardian_pubkey_hex: str):
        self.guardian_pubkey_hex = guardian_pubkey_hex
        self._used_token_ids: Set[str] = set()
        self._used_request_ids: Set[str] = set()

    def authorize_share_release(
        self,
        request: RecoveryRequest,
        custodian_did: str,
        share: Tuple[int, int],
        current_time: Optional[float] = None
    ) -> Tuple[int, int]:
        """
        Custodians release shares only after verifying AuthTok and replay protection.
        """
        if request.request_id in self._used_request_ids:
            raise ValueError(f"Recovery request replay detected: {request.request_id}")
        if request.auth_token.token_id in self._used_token_ids:
            raise ValueError(f"Recovery authorization token replay detected: {request.auth_token.token_id}")
        if request.auth_token.custodian_did != custodian_did:
            raise PermissionError("Authorization token is not bound to this custodian")
        if not request.verify(self.guardian_pubkey_hex, current_time=current_time):
            raise PermissionError("Invalid or unauthorized recovery request")

        self._used_request_ids.add(request.request_id)
        return share

    def reconstruct_secret_with_authorization(
        self,
        shares: List[Tuple[int, int]],
        auth_token: RecoveryAuthorizationToken,
        threshold_k: int,
        current_time: Optional[float] = None
    ) -> int:
        """
        Reconstructs secret only after verifying AuthTok authorization and share sufficiency.
        """
        if not auth_token.verify(self.guardian_pubkey_hex, current_time=current_time):
            raise PermissionError("Unauthorized secret reconstruction: AuthTok invalid or unverified")
        if auth_token.token_id in self._used_token_ids:
            raise ValueError(f"AuthTok replay detected: {auth_token.token_id}")
        if len(shares) < threshold_k:
            raise ValueError(f"Insufficient shares: got {len(shares)}, required threshold {threshold_k}")

        seen_x = set()
        for x, y in shares:
            if not isinstance(x, int) or not isinstance(y, int):
                raise ValueError("Malformed share: coordinates must be integers")
            if x <= 0 or x >= PRIME or y < 0 or y >= PRIME:
                raise ValueError("Malformed share: coordinates outside field range")
            if x in seen_x:
                raise ValueError(f"Duplicate share index {x} detected")
            seen_x.add(x)

        secret = ShamirSecretSharing.reconstruct_secret(shares[:threshold_k])
        self._used_token_ids.add(auth_token.token_id)
        return secret


# =============================================================================
# 7. KEY ROTATION CERTIFICATE & POST-RECOVERY ROTATION
# =============================================================================

@dataclass
class KeyRotationCertificate:
    old_did: str
    new_did: str
    new_pubkey_hex: str
    timestamp: float
    old_sig_hex: str = ""
    new_sig_hex: str = ""

    def payload_bytes(self) -> bytes:
        data = f"PKI_V2_ROTATE:{self.old_did}:{self.new_pubkey_hex}:{self.timestamp}"
        return data.encode("utf-8")

    def verify(self, old_pubkey_hex: str, max_drift_seconds: float = 300.0) -> bool:
        if not self.old_sig_hex or not self.new_sig_hex:
            return False
        now = time.time()
        if abs(now - self.timestamp) > max_drift_seconds:
            return False
        if not PeerIdentity.is_valid_did(self.old_did, old_pubkey_hex):
            return False
        if not PeerIdentity.is_valid_did(self.new_did, self.new_pubkey_hex):
            return False
        if old_pubkey_hex.lower() == self.new_pubkey_hex.lower():
            return False
        payload = self.payload_bytes()
        if not PeerIdentity.verify_peer_signature(old_pubkey_hex, payload, self.old_sig_hex):
            return False
        if not PeerIdentity.verify_peer_signature(self.new_pubkey_hex, payload, self.new_sig_hex):
            return False
        return True


def rotate_key_after_recovery(
    old_peer: PeerIdentity,
    recovered_secret: int,
    new_alias: Optional[str] = None
) -> Tuple[PeerIdentity, KeyRotationCertificate]:
    """
    Mandatory post-recovery key rotation per Flow 21 & Flow 22:
    Generates brand-new keypair, issues dual-signed rotation proof,
    retires the old key, and activates the new keypair.
    """
    old_secret_int = int.from_bytes(
        old_peer.private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        ),
        byteorder="big"
    )
    if recovered_secret != old_secret_int:
        raise ValueError("Recovered secret does not match target peer key")

    new_peer = PeerIdentity(new_alias or f"{old_peer.alias}_rotated", difficulty_bits=old_peer.difficulty_bits)
    now = time.time()
    cert = KeyRotationCertificate(
        old_did=old_peer.did,
        new_did=new_peer.did,
        new_pubkey_hex=new_peer.public_key_hex,
        timestamp=now
    )
    payload = cert.payload_bytes()
    cert.old_sig_hex = old_peer.sign(payload).hex()
    cert.new_sig_hex = new_peer.sign(payload).hex()

    # Invalidate old key
    old_peer.state = PeerState.UNKNOWN
    setattr(old_peer, "is_retired", True)

    # Transition new key to ACTIVE
    new_peer.state = PeerState.ACTIVE
    return new_peer, cert


def is_key_valid_for_operations(peer: PeerIdentity) -> bool:
    """
    Checks if a peer identity key is currently valid for active authenticated operations.
    """
    return peer.state == PeerState.ACTIVE and not getattr(peer, "is_retired", False)


# =============================================================================
# 8. SHAMIR SECRET SHARING (POLYNOMIAL SECRET SHARING)
# =============================================================================

class ShamirSecretSharing:
    @staticmethod
    def _extended_gcd(a: int, b: int) -> Tuple[int, int, int]:
        if a == 0:
            return b, 0, 1
        gcd, x1, y1 = ShamirSecretSharing._extended_gcd(b % a, a)
        x = y1 - (b // a) * x1
        y = x1
        return gcd, x, y

    @staticmethod
    def _mod_inverse(k: int, p: int = PRIME) -> int:
        k = k % p
        gcd, x, _ = ShamirSecretSharing._extended_gcd(k, p)
        if gcd != 1:
            raise ValueError("Modular inverse does not exist")
        return (x % p + p) % p

    @staticmethod
    def split_secret(secret_int: int, k_threshold: int, n_shares: int, prime: int = PRIME) -> List[Tuple[int, int]]:
        """
        Splits secret_int into n shares such that any k shares can reconstruct it.
        Polynomial: f(x) = secret + a_1*x + a_2*x^2 + ... + a_(k-1)*x^(k-1) mod prime
        """
        if k_threshold > n_shares:
            raise ValueError("Threshold k cannot be greater than total shares n")
        if secret_int >= prime:
            raise ValueError("Secret must be less than field prime")

        coefficients = [secret_int] + [secrets.randbelow(prime) for _ in range(k_threshold - 1)]

        shares: List[Tuple[int, int]] = []
        for x in range(1, n_shares + 1):
            y = 0
            for power, coeff in enumerate(coefficients):
                y = (y + coeff * pow(x, power, prime)) % prime
            shares.append((x, y))

        return shares

    @staticmethod
    def reconstruct_secret(shares: List[Tuple[int, int]], prime: int = PRIME) -> int:
        """
        Reconstructs secret using Lagrange Polynomial Interpolation at x = 0:
        S = sum_j (y_j * prod_{m != j} (-x_m / (x_j - x_m))) mod prime
        """
        k = len(shares)
        if k == 0:
            raise ValueError("At least one share required for reconstruction")

        secret = 0
        for j in range(k):
            x_j, y_j = shares[j]
            numerator = 1
            denominator = 1
            for m in range(k):
                if m == j:
                    continue
                x_m, _ = shares[m]
                numerator = (numerator * (-x_m)) % prime
                denominator = (denominator * (x_j - x_m)) % prime

            lagrange_l_j = (numerator * ShamirSecretSharing._mod_inverse(denominator, prime)) % prime
            secret = (secret + y_j * lagrange_l_j) % prime

        return (secret + prime) % prime
