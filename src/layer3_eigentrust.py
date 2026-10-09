"""
Layer 3: Cryptographic Reputation Engine (EigenTrust & Merkle File Verification)
Implements Merkle Tree file integrity checking with genuine inclusion proofs,
content manifests, requests, chunk responses, fault evidence records,
bilateral co-signed transaction receipts, node-local processed-evidence journals,
ordered 7-stage evidence validation pipeline, and the EigenTrust power-iteration convergence algorithm.
"""

import hashlib
import math
import time
import uuid
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any, Set, Union
import numpy as np

from src.layer1_identity import PeerIdentity, PeerState


# =============================================================================
# TRUST COMPUTATION MODES
# =============================================================================

class TrustComputationMode:
    VANILLA = "vanilla_eigentrust"
    EVIDENCE_ONLY = "evidence_only"       # Authoritative proposed EW-EigenTrust
    TOPOLOGY_ONLY = "topology_only"       # Experimental ablation
    FULL_EW = "full_ew_eigentrust"         # Experimental ablation
    LOCAL_ONLY = "local_only"

    VALID_MODES = {VANILLA, EVIDENCE_ONLY, TOPOLOGY_ONLY, FULL_EW, LOCAL_ONLY}



# =============================================================================
# MERKLE INCLUSION PROOFS & CONTENT ENVELOPES
# =============================================================================

@dataclass
class MerkleProofStep:
    sibling_hash: str
    direction: str  # Invariant: strictly "L" or "R"


def canonical_proof_str(proof: List[MerkleProofStep]) -> str:
    """
    Produces canonical serialized representation of a Merkle proof:
    sibling_hash:direction,sibling_hash:direction,...
    For an empty proof, returns an empty string.
    """
    if not proof:
        return ""
    return ",".join(f"{step.sibling_hash.lower()}:{step.direction}" for step in proof)


def hash_proof(proof: List[MerkleProofStep]) -> str:
    """
    Computes SHA-256 digest of canonical_proof_str(proof).
    Returns lowercase 64-hex string.
    """
    return hashlib.sha256(canonical_proof_str(proof).encode("utf-8")).hexdigest().lower()


def verify_merkle_proof_from_hash(
    leaf_hash: str,
    proof: List[MerkleProofStep],
    chunk_index: int,
    root_hash: str
) -> bool:
    """
    Verifies that leaf_hash at chunk_index accompanied by proof ascends to root_hash.
    """
    if not isinstance(leaf_hash, str) or len(leaf_hash) != 64:
        return False
    if not isinstance(root_hash, str) or len(root_hash) != 64:
        return False
    if not isinstance(proof, list) or chunk_index < 0:
        return False

    try:
        bytes.fromhex(leaf_hash)
        bytes.fromhex(root_hash)
    except ValueError:
        return False

    if len(proof) > 0 and (chunk_index >> len(proof)) != 0:
        return False
    if len(proof) == 0 and chunk_index != 0:
        return False

    curr = leaf_hash.lower()
    for step_num, step in enumerate(proof):
        if not isinstance(step, MerkleProofStep):
            return False
        if step.direction not in ("L", "R"):
            return False
        if not isinstance(step.sibling_hash, str) or len(step.sibling_hash) != 64:
            return False
        try:
            sibling_bytes = bytes.fromhex(step.sibling_hash)
        except ValueError:
            return False

        # Direction must match the bit-path for chunk_index
        expected_dir = "L" if ((chunk_index >> step_num) & 1) else "R"
        if step.direction != expected_dir:
            return False

        curr_bytes = bytes.fromhex(curr)
        if step.direction == "R":
            curr = hashlib.sha256(curr_bytes + sibling_bytes).hexdigest().lower()
        else:
            curr = hashlib.sha256(sibling_bytes + curr_bytes).hexdigest().lower()

    return curr == root_hash.lower()


def verify_merkle_proof(
    chunk_bytes: bytes,
    proof: List[MerkleProofStep],
    chunk_index: int,
    root_hash: str
) -> bool:
    """
    Standalone verification of Merkle inclusion proof:
    1. curr = SHA256(chunk_bytes)
    2. For each step:
       If 'R': curr = SHA256(raw(curr) || raw(sibling))
       If 'L': curr = SHA256(raw(sibling) || raw(curr))
    3. Compare final digest against root_hash.
    """
    if not isinstance(chunk_bytes, bytes):
        return False
    leaf_hash = hashlib.sha256(chunk_bytes).hexdigest().lower()
    return verify_merkle_proof_from_hash(leaf_hash, proof, chunk_index, root_hash)


class MerkleTree:
    def __init__(self, data_chunks: List[bytes]):
        self.chunks = data_chunks
        self.leaf_hashes = [hashlib.sha256(chunk).hexdigest().lower() for chunk in data_chunks]
        self.tree_levels = self._build_tree()
        self.root_hash = self.tree_levels[-1][0] if self.tree_levels and self.tree_levels[-1] else ""

    def _build_tree(self) -> List[List[str]]:
        if not self.leaf_hashes:
            return [[""]]
        levels = [self.leaf_hashes]
        while len(levels[-1]) > 1:
            current_level = levels[-1]
            next_level = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i + 1] if i + 1 < len(current_level) else left
                combined = hashlib.sha256(bytes.fromhex(left) + bytes.fromhex(right)).hexdigest().lower()
                next_level.append(combined)
            levels.append(next_level)
        return levels

    def generate_proof(self, chunk_index: int) -> List[MerkleProofStep]:
        """
        Generates genuine Merkle inclusion proof for chunk at chunk_index.
        Returns list of MerkleProofStep climbing the tree to root.
        """
        if chunk_index < 0 or chunk_index >= len(self.chunks):
            raise IndexError(f"Chunk index {chunk_index} out of bounds (total chunks: {len(self.chunks)})")

        proof: List[MerkleProofStep] = []
        k = chunk_index
        for d in range(len(self.tree_levels) - 1):
            level = self.tree_levels[d]
            if k % 2 == 0:
                sibling_idx = k + 1 if k + 1 < len(level) else k
                sibling_hash = level[sibling_idx]
                direction = "R"
            else:
                sibling_idx = k - 1
                sibling_hash = level[sibling_idx]
                direction = "L"

            proof.append(MerkleProofStep(sibling_hash=sibling_hash, direction=direction))
            k = k // 2

        return proof

    def verify_chunk(self, chunk_index: int, chunk_bytes: bytes) -> bool:
        """
        Validates that a received chunk matches the root hash via genuine Merkle inclusion proof.
        Eliminates the previous in-memory leaf-array shortcut.
        """
        if chunk_index < 0 or chunk_index >= len(self.chunks):
            return False
        proof = self.generate_proof(chunk_index)
        return verify_merkle_proof(chunk_bytes, proof, chunk_index, self.root_hash)


@dataclass
class ContentManifest:
    content_id: str
    root_hash: str
    total_chunks: int
    chunk_size_bytes: int
    file_size_bytes: int
    publisher_did: str
    timestamp: float
    signature_hex: str

    def payload_bytes(self) -> bytes:
        data = f"PKI_V2_MANIFEST:{self.content_id}:{self.root_hash}:{self.total_chunks}:{self.chunk_size_bytes}:{self.file_size_bytes}:{self.publisher_did}:{self.timestamp}"
        return data.encode("utf-8")

    def verify_signature(self, publisher_pubkey_hex: str) -> bool:
        if not PeerIdentity.is_valid_did(self.publisher_did, publisher_pubkey_hex):
            return False
        return PeerIdentity.verify_peer_signature(
            publisher_pubkey_hex,
            self.payload_bytes(),
            self.signature_hex
        )


@dataclass
class ContentRequest:
    req_id: str
    client_did: str
    server_did: str
    content_id: str
    chunk_index: int
    merkle_root: str
    timestamp: float
    nonce: str
    client_sig_hex: str

    def payload_bytes(self) -> bytes:
        data = f"PKI_V2_REQ:{self.req_id}:{self.client_did}:{self.server_did}:{self.content_id}:{self.chunk_index}:{self.merkle_root}:{self.timestamp}:{self.nonce}"
        return data.encode("utf-8")

    def verify_signature(self, client_pubkey_hex: str) -> bool:
        if not PeerIdentity.is_valid_did(self.client_did, client_pubkey_hex):
            return False
        return PeerIdentity.verify_peer_signature(
            client_pubkey_hex,
            self.payload_bytes(),
            self.client_sig_hex
        )


@dataclass
class ChunkResponse:
    req_id: str
    client_did: str
    server_did: str
    content_id: str
    chunk_index: int
    chunk_bytes: bytes
    chunk_hash: str
    proof_hash: str
    merkle_root: str
    timestamp: float
    nonce: str
    merkle_proof: List[MerkleProofStep]
    server_sig_hex: str

    def payload_bytes(self) -> bytes:
        data = f"PKI_V2_RESP:{self.req_id}:{self.client_did}:{self.server_did}:{self.content_id}:{self.chunk_index}:{self.chunk_hash}:{self.proof_hash}:{self.merkle_root}:{self.timestamp}:{self.nonce}"
        return data.encode("utf-8")

    def matches_request(self, request: ContentRequest) -> bool:
        """
        Asserts strict binding between request and response:
        req_id, client_did, server_did, content_id, chunk_index, merkle_root, nonce.
        """
        return (
            self.req_id == request.req_id and
            self.client_did == request.client_did and
            self.server_did == request.server_did and
            self.content_id == request.content_id and
            self.chunk_index == request.chunk_index and
            self.merkle_root.lower() == request.merkle_root.lower() and
            self.nonce == request.nonce
        )

    def verify(self, server_pubkey_hex: str, expected_request: Optional[ContentRequest] = None) -> bool:
        """
        Validates ChunkResponse per Protocol Spec Flow 6:
        1. Server DID matches public key
        2. Server Ed25519 signature over signed payload
        3. chunk_hash == SHA256(chunk_bytes)
        4. proof_hash == hash_proof(merkle_proof)
        5. verify_merkle_proof(chunk_bytes, merkle_proof, chunk_index, merkle_root) == True
        6. If expected_request provided: validates request/response binding
        """
        if not PeerIdentity.is_valid_did(self.server_did, server_pubkey_hex):
            return False

        if not PeerIdentity.verify_peer_signature(
            server_pubkey_hex,
            self.payload_bytes(),
            self.server_sig_hex
        ):
            return False

        computed_chunk_hash = hashlib.sha256(self.chunk_bytes).hexdigest().lower()
        if self.chunk_hash.lower() != computed_chunk_hash:
            return False

        computed_proof_hash = hash_proof(self.merkle_proof).lower()
        if self.proof_hash.lower() != computed_proof_hash:
            return False

        if not verify_merkle_proof(self.chunk_bytes, self.merkle_proof, self.chunk_index, self.merkle_root):
            return False

        if expected_request is not None:
            if not self.matches_request(expected_request):
                return False

        return True


@dataclass
class FaultEvidenceRecord:
    evidence_id: str
    req_id: str
    reporter_did: str
    accused_did: str
    content_id: str
    merkle_root: str
    chunk_index: int
    delivered_chunk_hash: str
    delivered_proof_hash: str
    manifest_envelope: ContentManifest
    delivery_envelope: ChunkResponse
    authentic_chunk_hash: str
    authentic_merkle_proof: List[MerkleProofStep]
    timestamp: float
    reporter_sig_hex: str

    def payload_bytes(self) -> bytes:
        data = f"PKI_V2_EVIDENCE_FAULT:{self.evidence_id}:{self.req_id}:{self.reporter_did}:{self.accused_did}:{self.content_id}:{self.merkle_root}:{self.chunk_index}:{self.delivered_chunk_hash}:{self.authentic_chunk_hash}:{self.timestamp}"
        return data.encode("utf-8")

    def verify(
        self,
        reporter_pubkey_hex: str,
        accused_pubkey_hex: str,
        manifest_publisher_pubkey_hex: str
    ) -> bool:
        """
        Cryptographic verification of FaultEvidenceRecord:
        1. manifest signature is valid
        2. delivery signature is valid
        3. delivery response is correctly bound to evidence fields
        4. delivery chunk hash matches delivered bytes
        5. delivery proof hash matches delivered proof
        6. authentic proof reaches expected root
        7. authentic leaf hash differs from delivered chunk hash (contradiction)
        8. reporter signature is valid
        """
        # DID consistency
        if not PeerIdentity.is_valid_did(self.reporter_did, reporter_pubkey_hex):
            return False
        if not PeerIdentity.is_valid_did(self.accused_did, accused_pubkey_hex):
            return False
        if not PeerIdentity.is_valid_did(self.manifest_envelope.publisher_did, manifest_publisher_pubkey_hex):
            return False

        # 1. Manifest envelope signature
        if not self.manifest_envelope.verify_signature(manifest_publisher_pubkey_hex):
            return False

        if self.manifest_envelope.content_id != self.content_id:
            return False
        if self.manifest_envelope.root_hash.lower() != self.merkle_root.lower():
            return False

        # 2. Delivery envelope signature
        if not PeerIdentity.verify_peer_signature(
            accused_pubkey_hex,
            self.delivery_envelope.payload_bytes(),
            self.delivery_envelope.server_sig_hex
        ):
            return False

        # 3. Delivery envelope matches evidence bindings
        if self.delivery_envelope.req_id != self.req_id:
            return False
        if self.delivery_envelope.server_did != self.accused_did:
            return False
        if self.delivery_envelope.client_did != self.reporter_did:
            return False
        if self.delivery_envelope.content_id != self.content_id:
            return False
        if self.delivery_envelope.chunk_index != self.chunk_index:
            return False
        if self.delivery_envelope.merkle_root.lower() != self.merkle_root.lower():
            return False
        if self.delivery_envelope.chunk_hash.lower() != self.delivered_chunk_hash.lower():
            return False
        if self.delivery_envelope.proof_hash.lower() != self.delivered_proof_hash.lower():
            return False

        # 4. Delivery chunk hash matches delivered bytes
        if hashlib.sha256(self.delivery_envelope.chunk_bytes).hexdigest().lower() != self.delivered_chunk_hash.lower():
            return False

        # 5. Delivery proof hash matches delivered proof
        if hash_proof(self.delivery_envelope.merkle_proof).lower() != self.delivered_proof_hash.lower():
            return False

        # 6. Authentic proof reaches expected root
        if not verify_merkle_proof_from_hash(
            self.authentic_chunk_hash,
            self.authentic_merkle_proof,
            self.chunk_index,
            self.merkle_root
        ):
            return False

        # 7. Contradiction: authentic leaf differs from delivered chunk hash
        if self.authentic_chunk_hash.lower() == self.delivered_chunk_hash.lower():
            return False

        # 8. Reporter signature
        if not PeerIdentity.verify_peer_signature(
            reporter_pubkey_hex,
            self.payload_bytes(),
            self.reporter_sig_hex
        ):
            return False

        return True


# =============================================================================
# BILATERAL RECEIPTS & CANONICAL JOURNALS
# =============================================================================

@dataclass
class BilateralReceipt:
    tx_id: str
    client_did: str
    client_pubkey_hex: str
    server_did: str
    server_pubkey_hex: str
    merkle_root: str
    rating: Any  # Frozen: strictly "+1.00" or "-1.00" (supports numeric 1.0/-1.0 for backward compatibility)
    timestamp: float
    nonce: str = ""
    client_sig_hex: str = ""
    server_sig_hex: str = ""

    def payload_bytes(self) -> bytes:
        if isinstance(self.rating, str):
            rating_str = self.rating
        elif isinstance(self.rating, (int, float)):
            rating_str = f"{self.rating:+.2f}" if self.nonce else f"{self.rating:.2f}"
        else:
            rating_str = str(self.rating)

        # Legacy backward-compatibility format if nonce is omitted and rating is float
        if not self.nonce and isinstance(self.rating, (int, float)):
            data = f"{self.tx_id}:{self.client_did}:{self.server_did}:{self.merkle_root}:{float(self.rating):.2f}:{self.timestamp}"
            return data.encode("utf-8")

        # Frozen v2.2 specification format:
        # PKI_V2_RECEIPT:<tx_id>:<client_did>:<server_did>:<merkle_root>:<rating>:<timestamp>:<nonce>
        data = f"PKI_V2_RECEIPT:{self.tx_id}:{self.client_did}:{self.server_did}:{self.merkle_root}:{rating_str}:{self.timestamp}:{self.nonce}"
        return data.encode("utf-8")

    def is_valid(self) -> bool:
        """Verifies that BOTH client and server cryptographically co-signed the receipt."""
        if not PeerIdentity.is_valid_did(self.client_did, self.client_pubkey_hex):
            return False
        if not PeerIdentity.is_valid_did(self.server_did, self.server_pubkey_hex):
            return False

        data = self.payload_bytes()
        valid_client = PeerIdentity.verify_peer_signature(
            self.client_pubkey_hex, data, self.client_sig_hex
        )
        valid_server = PeerIdentity.verify_peer_signature(
            self.server_pubkey_hex, data, self.server_sig_hex
        )
        if valid_client and valid_server:
            return True

        # Fallback to legacy payload if nonce was empty
        if not self.nonce:
            legacy_data = f"{self.tx_id}:{self.client_did}:{self.server_did}:{self.merkle_root}:{float(self.rating):.2f}:{self.timestamp}".encode("utf-8")
            valid_client_leg = PeerIdentity.verify_peer_signature(
                self.client_pubkey_hex, legacy_data, self.client_sig_hex
            )
            valid_server_leg = PeerIdentity.verify_peer_signature(
                self.server_pubkey_hex, legacy_data, self.server_sig_hex
            )
            return valid_client_leg and valid_server_leg

        return False


@dataclass
class JournalEntry:
    entry_id: str
    entry_type: str        # "RECEIPT" or "FAULT_EVIDENCE"
    status: str            # "COMMITTED"
    timestamp: float
    details: Dict[str, Any] = field(default_factory=dict)


class LocalEvidenceJournal:
    """
    Node-Local Processed Evidence Journal (L_local).
    Guarantees at-most-once evidence accounting on the local node.
    Strictly node-local accounting; does NOT provide distributed consensus or a global ledger.
    """
    def __init__(self):
        # Keyed by f"{entry_type}:{entry_id}" to ensure cross-evidence uniqueness
        self._entries: Dict[str, JournalEntry] = {}

    def contains(self, entry_id: str, entry_type: Optional[str] = None) -> bool:
        """Lookup whether an entry_id has already been committed."""
        if entry_type is not None:
            return f"{entry_type}:{entry_id}" in self._entries
        # If entry_type is omitted, check either namespace
        return (f"RECEIPT:{entry_id}" in self._entries or
                f"FAULT_EVIDENCE:{entry_id}" in self._entries or
                entry_id in self._entries)

    def get(self, entry_id: str, entry_type: Optional[str] = None) -> Optional[JournalEntry]:
        """Retrieve journal entry if present."""
        if entry_type is not None:
            return self._entries.get(f"{entry_type}:{entry_id}")
        return (self._entries.get(f"RECEIPT:{entry_id}") or
                self._entries.get(f"FAULT_EVIDENCE:{entry_id}") or
                self._entries.get(entry_id))

    def commit(self, entry_id: str, entry_type: str, details: Optional[Dict[str, Any]] = None) -> bool:
        """
        Atomic check-then-commit.
        Returns True if newly committed, False if already present.
        """
        key = f"{entry_type}:{entry_id}"
        if key in self._entries:
            return False

        self._entries[key] = JournalEntry(
            entry_id=entry_id,
            entry_type=entry_type,
            status="COMMITTED",
            timestamp=time.time(),
            details=details or {}
        )
        return True

    def get_all_entries(self) -> List[JournalEntry]:
        """Public accessor returning all committed journal entries."""
        return list(self._entries.values())

    def __len__(self) -> int:
        return len(self._entries)


class SimulatorCanonicalJournal(LocalEvidenceJournal):
    """
    Simulator Canonical Evidence Journal (L_sim).
    Simulation-level test harness construct to ensure simulated interactions
    are processed at-most-once in the global simulation matrix.
    Explicitly NOT a distributed blockchain or BFT consensus ledger.
    """
    pass


# =============================================================================
# EIGENTRUST ENGINE WITH EVIDENCE-DRIVEN REPUTATION ACCOUNTING
# =============================================================================

class EigenTrustEngine:
    def __init__(
        self,
        peers: List[str],
        pre_trusted_peers: List[str],
        alpha: float = 0.15,
        journal: Optional[LocalEvidenceJournal] = None,
        freshness_window: float = 600.0
    ):
        """
        peers: list of peer DIDs.
        pre_trusted_peers: subset of DIDs designated as seed anchors.
        alpha: pre-trusted damping probability (default 0.15).
        journal: node-local evidence journal (L_local) or simulator journal (L_sim).
        freshness_window: max allowed timestamp drift (default 600 seconds).
        """
        self.peers = sorted(peers)
        self.peer_to_idx = {did: idx for idx, did in enumerate(self.peers)}
        self.pre_trusted_peers = list(pre_trusted_peers)
        self.n = len(self.peers)
        self.alpha = alpha
        self.freshness_window = freshness_window

        # Node-Local Processed Evidence Journal (L_local)
        self.local_journal = journal if journal is not None else LocalEvidenceJournal()

        # Interaction Nonce Replay Cache (seen_nonces: nonce -> timestamp)
        self.seen_nonces: Dict[str, float] = {}

        # Transport duplicate suppression cache
        self.seen_transport_hashes: Set[str] = set()

        # Request ID deduplication cache for evidence
        self.seen_req_ids: Set[str] = set()

        # Local peer identity and public key registry
        self.public_keys: Dict[str, str] = {}
        self.peer_identities: Dict[str, Any] = {}
        self.peer_states: Dict[str, PeerState] = {did: PeerState.ACTIVE for did in self.peers}

        # Pre-trusted seed distribution vector p
        self.p = np.zeros(self.n)
        valid_pretrusted = [p for p in pre_trusted_peers if p in self.peer_to_idx]
        if valid_pretrusted:
            prob = 1.0 / len(valid_pretrusted)
            for p in valid_pretrusted:
                self.p[self.peer_to_idx[p]] = prob
        else:
            self.p.fill(1.0 / self.n)

        # Raw satisfaction matrix: S[i][j] = sum(satisfactions of i regarding j)
        self.S = np.zeros((self.n, self.n))

    def register_peer(self, peer: PeerIdentity) -> None:
        """Registers peer identity and public key for evidence verification."""
        self.public_keys[peer.did] = peer.public_key_hex
        self.peer_identities[peer.did] = peer
        if peer.did not in self.peer_states:
            self.peer_states[peer.did] = getattr(peer, "state", PeerState.ACTIVE)

    def register_peer_pubkey(self, did: str, pubkey_hex: str) -> None:
        """Registers public key for a DID."""
        self.public_keys[did] = pubkey_hex

    def record_receipt(
        self,
        receipt: BilateralReceipt,
        current_time: Optional[float] = None
    ) -> bool:
        """
        Executes the 7-stage ordered evidence validation pipeline for BilateralReceipt:
        Stage 1 — Timestamp/freshness validation
        Stage 2 — Transport duplicate suppression
        Stage 3 — Nonce/replay validation
        Stage 4 — Cryptographic signature/evidence validation
        Stage 5 — Canonical evidence journal lookup
        Stage 6 — Canonical journal commit
        Stage 7 — Deterministic reputation accounting
        """
        now = time.time() if current_time is None else current_time

        # --- Stage 1: Timestamp / Freshness Validation ---
        if abs(now - receipt.timestamp) > self.freshness_window:
            return False
        if receipt.timestamp > now + 60.0:  # Excessive future timestamp drift
            return False

        # --- Stage 2: Transport Duplicate Suppression ---
        transport_id = hashlib.sha256(
            receipt.payload_bytes() +
            receipt.client_sig_hex.encode("utf-8") +
            receipt.server_sig_hex.encode("utf-8")
        ).hexdigest()
        if transport_id in self.seen_transport_hashes:
            return False

        # --- Stage 3: Nonce / Replay Validation ---
        if receipt.nonce:
            if receipt.nonce in self.seen_nonces:
                return False

        # --- Stage 4: Cryptographic Signature / Evidence Validation ---
        if receipt.client_did not in self.peer_to_idx or receipt.server_did not in self.peer_to_idx:
            return False
        if receipt.client_did == receipt.server_did:
            return False

        # Rating check: strictly +1.00 or -1.00
        if isinstance(receipt.rating, str):
            if receipt.rating not in ("+1.00", "-1.00"):
                return False
            delta = 1.0 if receipt.rating == "+1.00" else -1.0
        elif isinstance(receipt.rating, (int, float)):
            if receipt.rating == 1.0:
                delta = 1.0
            elif receipt.rating == -1.0:
                delta = -1.0
            else:
                return False
        else:
            return False

        # Validate signatures & participant DID bindings
        if not receipt.is_valid():
            return False

        # --- Stage 5: Canonical Evidence Journal Lookup ---
        if self.local_journal.contains(receipt.tx_id, entry_type="RECEIPT"):
            return False

        # --- Stage 6: Canonical Journal Commit ---
        committed = self.local_journal.commit(
            entry_id=receipt.tx_id,
            entry_type="RECEIPT",
            details={
                "client_did": receipt.client_did,
                "server_did": receipt.server_did,
                "rating": delta,
                "nonce": receipt.nonce,
                "merkle_root": receipt.merkle_root,
                "receipt_timestamp": receipt.timestamp
            }
        )
        if not committed:
            return False

        if receipt.nonce:
            self.seen_nonces[receipt.nonce] = receipt.timestamp
        self.seen_transport_hashes.add(transport_id)

        # --- Stage 7: Deterministic Reputation Accounting ---
        c_idx = self.peer_to_idx[receipt.client_did]
        s_idx = self.peer_to_idx[receipt.server_did]
        self.S[c_idx, s_idx] += delta

        return True

    def record_fault_evidence(
        self,
        evidence: FaultEvidenceRecord,
        reporter_pubkey_hex: Optional[str] = None,
        accused_pubkey_hex: Optional[str] = None,
        manifest_publisher_pubkey_hex: Optional[str] = None,
        current_time: Optional[float] = None
    ) -> bool:
        """
        Executes the 7-stage ordered evidence validation pipeline for FaultEvidenceRecord:
        Stage 1 — Timestamp/freshness validation
        Stage 2 — Transport duplicate suppression
        Stage 3 — Nonce/replay validation
        Stage 4 — Cryptographic signature/evidence validation (Merkle contradiction)
        Stage 5 — Canonical evidence journal lookup
        Stage 6 — Canonical journal commit
        Stage 7 — Deterministic reputation accounting (S -= 2.0, state -> SUSPECTED)
        """
        now = time.time() if current_time is None else current_time

        # --- Stage 1: Timestamp / Freshness Validation ---
        if abs(now - evidence.timestamp) > self.freshness_window:
            return False
        if evidence.timestamp > now + 60.0:
            return False

        # --- Stage 2: Transport Duplicate Suppression ---
        transport_id = hashlib.sha256(
            evidence.payload_bytes() + evidence.reporter_sig_hex.encode("utf-8")
        ).hexdigest()
        if transport_id in self.seen_transport_hashes:
            return False

        # --- Stage 3: Nonce / Replay Validation ---
        delivery_nonce = evidence.delivery_envelope.nonce
        if delivery_nonce and delivery_nonce in self.seen_nonces:
            return False
        if evidence.req_id in self.seen_req_ids:
            return False

        # --- Stage 4: Cryptographic Signature / Evidence Validation ---
        if evidence.reporter_did not in self.peer_to_idx or evidence.accused_did not in self.peer_to_idx:
            return False
        if evidence.reporter_did == evidence.accused_did:
            return False

        # Resolve public keys if not explicitly provided
        rep_pub = reporter_pubkey_hex or self.public_keys.get(evidence.reporter_did)
        acc_pub = accused_pubkey_hex or self.public_keys.get(evidence.accused_did)
        pub_pub = manifest_publisher_pubkey_hex or self.public_keys.get(evidence.manifest_envelope.publisher_did)

        if not rep_pub or not acc_pub or not pub_pub:
            return False

        # Full cryptographic verification (manifest, delivery commitment, authentic proof, contradiction)
        if not evidence.verify(rep_pub, acc_pub, pub_pub):
            return False

        # --- Stage 5: Canonical Evidence Journal Lookup ---
        if self.local_journal.contains(evidence.evidence_id, entry_type="FAULT_EVIDENCE"):
            return False

        # --- Stage 6: Canonical Journal Commit ---
        committed = self.local_journal.commit(
            entry_id=evidence.evidence_id,
            entry_type="FAULT_EVIDENCE",
            details={
                "reporter_did": evidence.reporter_did,
                "accused_did": evidence.accused_did,
                "content_id": evidence.content_id,
                "chunk_index": evidence.chunk_index,
                "req_id": evidence.req_id
            }
        )
        if not committed:
            return False

        if delivery_nonce:
            self.seen_nonces[delivery_nonce] = evidence.timestamp
        self.seen_req_ids.add(evidence.req_id)
        self.seen_transport_hashes.add(transport_id)

        # --- Stage 7: Deterministic Reputation Accounting ---
        r_idx = self.peer_to_idx[evidence.reporter_did]
        a_idx = self.peer_to_idx[evidence.accused_did]
        self.S[r_idx, a_idx] -= 2.0

        # Accused peer state transitions from ACTIVE to SUSPECTED
        self.peer_states[evidence.accused_did] = PeerState.SUSPECTED
        if evidence.accused_did in self.peer_identities:
            peer_obj = self.peer_identities[evidence.accused_did]
            if hasattr(peer_obj, "state"):
                peer_obj.state = PeerState.SUSPECTED

        return True

    def compute_normalized_matrix(self) -> np.ndarray:
        """
        Computes row-normalized trust matrix C:
        C_ij = max(S_ij, 0) / sum_k(max(S_ik, 0))
        If sum is 0 (peer has no interactions), row defaults to pre-trusted vector p.
        """
        C = np.zeros((self.n, self.n))
        for i in range(self.n):
            pos_ratings = np.maximum(self.S[i, :], 0)
            total = np.sum(pos_ratings)
            if total > 0:
                C[i, :] = pos_ratings / total
            else:
                C[i, :] = self.p
        return C

    def run_power_iteration(self, max_iterations: int = 100, tolerance: float = 1e-6) -> np.ndarray:
        """
        Runs EigenTrust power iteration:
        t^(k+1) = (1 - alpha) * C^T * t^(k) + alpha * p
        Returns the stationary global trust vector.
        """
        C = self.compute_normalized_matrix()
        C_T = C.T
        
        # Initialize trust vector to pre-trusted vector
        t = np.copy(self.p)
        
        for _ in range(max_iterations):
            t_next = (1 - self.alpha) * np.dot(C_T, t) + self.alpha * self.p
            delta = np.linalg.norm(t_next - t)
            t = t_next
            if delta < tolerance:
                break
                
        return t

    def compute_ew_trust_scores(
        self,
        mode: str = TrustComputationMode.EVIDENCE_ONLY,
        verified_delivery_keys: Optional[Set[Tuple[str, str, str, str]]] = None,
        known_manifest_roots: Optional[Set[str]] = None,
        certified_suspicion_dids: Optional[Set[str]] = None,
        reference_time: Optional[float] = None,
        k_max: float = 10.0,
        lambda_sat: float = 0.50,
        mu_unverified: float = 0.10,
        mu_referenced: float = 0.25,
        beta_entropy: float = 2.0,
        theta_penalty: float = 0.85,
        epsilon_floor: float = 0.10,
        delta_reg: float = 2.0,
        tau_seconds: float = 86400.0,
        max_iter: int = 100,
        tol: float = 1e-6,
        **kwargs
    ) -> Tuple[Dict[str, float], bool, int]:
        """
        Computes trust scores using EW-EigenTrust v1.8.
        Returns: (trust_scores: Dict[str, float], converged: bool, executed_iters: int)
        """
        raw_s: Dict[Tuple[str, str], float] = {}
        for i in range(self.n):
            for j in range(self.n):
                if i != j and self.S[i, j] != 0:
                    raw_s[(self.peers[i], self.peers[j])] = float(self.S[i, j])

        return compute_ew_eigentrust_v1_8(
            peers=self.peers,
            supernodes=getattr(self, "pre_trusted_peers", []),
            raw_s_matrix=raw_s,
            evidence_journal=self.local_journal,
            peer_states=self.peer_states,
            certified_suspicion_dids=certified_suspicion_dids,
            verified_delivery_keys=verified_delivery_keys,
            known_manifest_roots=known_manifest_roots,
            mode=mode,
            alpha=self.alpha,
            k_max=k_max,
            lambda_sat=lambda_sat,
            mu_unverified=mu_unverified,
            mu_referenced=mu_referenced,
            beta_entropy=beta_entropy,
            theta_penalty=theta_penalty,
            epsilon_floor=epsilon_floor,
            delta_reg=delta_reg,
            tau_seconds=tau_seconds,
            max_iter=max_iter,
            tol=tol,
            reference_time=reference_time
        )

    def get_trust_scores(
        self,
        mode: str = TrustComputationMode.VANILLA,
        verified_delivery_keys: Optional[Set[Tuple[str, str, str, str]]] = None,
        known_manifest_roots: Optional[Set[str]] = None,
        certified_suspicion_dids: Optional[Set[str]] = None,
        reference_time: Optional[float] = None,
        **kwargs
    ) -> Dict[str, float]:
        """
        Returns dictionary of DID -> normalized global trust score.
        If mode is VANILLA, uses standard power iteration on raw S.
        If mode is EVIDENCE_ONLY (or other EW mode), computes via compute_ew_eigentrust_v1_8.
        """
        if mode == TrustComputationMode.VANILLA:
            scores = self.run_power_iteration()
            return {self.peers[i]: float(scores[i]) for i in range(self.n)}

        scores, _, _ = self.compute_ew_trust_scores(
            mode=mode,
            verified_delivery_keys=verified_delivery_keys,
            known_manifest_roots=known_manifest_roots,
            certified_suspicion_dids=certified_suspicion_dids,
            reference_time=reference_time,
            **kwargs
        )
        return scores


# =============================================================================
# EW-EIGENTRUST V1.8 ALGORITHM (EVIDENCE-ONLY AUTHORITATIVE IMPLEMENTATION)
# =============================================================================

def compute_ew_eigentrust_v1_8(
    peers: List[str],
    supernodes: List[str],
    raw_s_matrix: Dict[Tuple[str, str], float],
    evidence_journal: Any = None,
    peer_states: Optional[Dict[str, Any]] = None,
    certified_suspicion_dids: Optional[Set[str]] = None,
    verified_delivery_keys: Optional[Set[Tuple[str, str, str, str]]] = None,
    known_manifest_roots: Optional[Set[str]] = None,
    mode: str = TrustComputationMode.EVIDENCE_ONLY,
    alpha: float = 0.15,
    k_max: float = 10.0,
    lambda_sat: float = 0.50,
    mu_unverified: float = 0.10,
    mu_referenced: float = 0.25,
    beta_entropy: float = 2.0,
    theta_penalty: float = 0.85,
    epsilon_floor: float = 0.10,
    delta_reg: float = 2.0,
    tau_seconds: float = 86400.0,
    max_iter: int = 100,
    tol: float = 1e-6,
    reference_time: Optional[float] = None
) -> Tuple[Dict[str, float], bool, int]:
    """
    Computes global trust vector using EW-EigenTrust v1.8.
    Returns: (trust_scores: Dict[str, float], converged: bool, executed_iters: int)
    """
    # 1. Parameter Validation (Reject bool strictly)
    if mode not in TrustComputationMode.VALID_MODES:
        raise ValueError(f"Invalid trust computation mode: {mode}")
    if isinstance(alpha, bool) or not (isinstance(alpha, (int, float)) and math.isfinite(alpha) and 0.0 < alpha < 1.0):
        raise ValueError(f"alpha must be finite in (0, 1), got {alpha}")
    if isinstance(tol, bool) or not (isinstance(tol, (int, float)) and math.isfinite(tol) and tol > 0.0):
        raise ValueError(f"tol must be finite positive, got {tol}")
    if isinstance(max_iter, bool) or not (isinstance(max_iter, int) and max_iter >= 1):
        raise ValueError(f"max_iter must be an integer >= 1, got {max_iter}")
    if isinstance(k_max, bool) or not (isinstance(k_max, (int, float)) and math.isfinite(k_max) and k_max > 0.0):
        raise ValueError(f"k_max must be finite positive, got {k_max}")
    if isinstance(lambda_sat, bool) or not (isinstance(lambda_sat, (int, float)) and math.isfinite(lambda_sat) and lambda_sat > 0.0):
        raise ValueError(f"lambda_sat must be finite positive, got {lambda_sat}")
    if isinstance(mu_unverified, bool) or not (isinstance(mu_unverified, (int, float)) and math.isfinite(mu_unverified) and 0.0 <= mu_unverified <= 1.0):
        raise ValueError(f"mu_unverified must be in [0, 1], got {mu_unverified}")
    if isinstance(mu_referenced, bool) or not (isinstance(mu_referenced, (int, float)) and math.isfinite(mu_referenced) and 0.0 <= mu_referenced <= 1.0):
        raise ValueError(f"mu_referenced must be in [0, 1], got {mu_referenced}")
    if mu_unverified > mu_referenced:
        raise ValueError(f"mu_unverified ({mu_unverified}) cannot exceed mu_referenced ({mu_referenced})")
    if isinstance(beta_entropy, bool) or not (isinstance(beta_entropy, (int, float)) and math.isfinite(beta_entropy) and beta_entropy > 0.0):
        raise ValueError(f"beta_entropy must be finite positive, got {beta_entropy}")
    if isinstance(theta_penalty, bool) or not (isinstance(theta_penalty, (int, float)) and math.isfinite(theta_penalty) and 0.0 <= theta_penalty <= 1.0):
        raise ValueError(f"theta_penalty must be in [0, 1], got {theta_penalty}")
    if isinstance(epsilon_floor, bool) or not (isinstance(epsilon_floor, (int, float)) and math.isfinite(epsilon_floor) and 0.0 < epsilon_floor <= 1.0):
        raise ValueError(f"epsilon_floor must be in (0, 1], got {epsilon_floor}")
    if isinstance(delta_reg, bool) or not (isinstance(delta_reg, (int, float)) and math.isfinite(delta_reg) and delta_reg > 0.0):
        raise ValueError(f"delta_reg must be finite positive, got {delta_reg}")
    if isinstance(tau_seconds, bool) or not (isinstance(tau_seconds, (int, float)) and math.isfinite(tau_seconds) and tau_seconds > 0.0):
        raise ValueError(f"tau_seconds must be finite positive, got {tau_seconds}")
    if reference_time is not None:
        if isinstance(reference_time, bool) or not (isinstance(reference_time, (int, float)) and math.isfinite(reference_time)):
            raise ValueError(f"reference_time must be a finite float or None, got {reference_time}")

    # 2. Canonical Peer Set & Empty Network Handling
    if not peers:
        return {}, True, 0

    canonical_peers = sorted(list(set(str(p) for p in peers if p and isinstance(p, str))))
    n = len(canonical_peers)
    if n == 0:
        return {}, True, 0

    peer_to_idx = {did: idx for idx, did in enumerate(canonical_peers)}
    valid_supernodes = sorted(list(set(str(sn) for sn in (supernodes or []) if str(sn) in peer_to_idx)))
    manifest_roots = {str(r).lower() for r in (known_manifest_roots or set()) if isinstance(r, str)}
    delivery_keys = set()
    if verified_delivery_keys:
        for k in verified_delivery_keys:
            if isinstance(k, tuple) and len(k) == 4:
                delivery_keys.add((str(k[0]), str(k[1]), str(k[2]).lower(), str(k[3])))

    states = peer_states or {}
    certified_suspected = set(str(s) for s in (certified_suspicion_dids or set()))
    t_ref = float(reference_time) if reference_time is not None else None

    # 3. Pre-trusted restart vector p
    p = np.zeros(n, dtype=np.float64)
    if valid_supernodes:
        sn_weight = 1.0 / len(valid_supernodes)
        for sn in valid_supernodes:
            p[peer_to_idx[sn]] = sn_weight
    else:
        p.fill(1.0 / n)

    # 4. Fast path: Local-only baseline
    if mode == TrustComputationMode.LOCAL_ONLY:
        scores = {}
        total = 0.0
        for src in canonical_peers:
            s_sum = 0.0
            for dst in canonical_peers:
                if dst != src:
                    val = raw_s_matrix.get((src, dst), 0.0)
                    if not isinstance(val, bool) and isinstance(val, (int, float)) and math.isfinite(val):
                        s_sum += max(0.0, float(val))
            scores[src] = s_sum
            total += s_sum
        if total > 0.0:
            return {did: float(v / total) for did, v in scores.items()}, True, 0
        return {did: float(1.0 / n) for did in canonical_peers}, True, 0

    # 5. Extract journal entries defensively
    certified_fault_accused: Set[str] = set()
    pair_entries: Dict[Tuple[str, str], List[Any]] = {}

    if mode in (TrustComputationMode.EVIDENCE_ONLY, TrustComputationMode.FULL_EW):
        raw_entries = []
        if evidence_journal is not None:
            if hasattr(evidence_journal, "get_all_entries") and callable(evidence_journal.get_all_entries):
                raw_entries = evidence_journal.get_all_entries()
            elif hasattr(evidence_journal, "_entries") and isinstance(evidence_journal._entries, dict):
                raw_entries = list(evidence_journal._entries.values())

        for entry in raw_entries:
            entry_type = getattr(entry, "entry_type", "")
            details = getattr(entry, "details", {})
            if not isinstance(details, dict):
                details = {}

            if entry_type == "FAULT_EVIDENCE":
                accused = details.get("accused_did")
                if isinstance(accused, str) and accused in peer_to_idx:
                    certified_fault_accused.add(accused)
            elif entry_type == "RECEIPT":
                c = details.get("client_did")
                s = details.get("server_did")
                if isinstance(c, str) and isinstance(s, str) and c in peer_to_idx and s in peer_to_idx and c != s:
                    pair_entries.setdefault((c, s), []).append(entry)

    # 6. Construct base interaction matrix A_ij
    A = np.zeros((n, n), dtype=np.float64)

    for i, src in enumerate(canonical_peers):
        for j, dst in enumerate(canonical_peers):
            if i == j:
                continue

            # Vanilla & Topology-Only Modes: Direct raw S matrix
            if mode in (TrustComputationMode.VANILLA, TrustComputationMode.TOPOLOGY_ONLY):
                raw_score = raw_s_matrix.get((src, dst), 0.0)
                if isinstance(raw_score, bool) or not isinstance(raw_score, (int, float)) or not math.isfinite(raw_score):
                    raw_score = 0.0
                A[i, j] = max(0.0, float(raw_score))
                continue

            # Evidence Modes (EVIDENCE_ONLY, FULL_EW):
            state_val = str(getattr(states.get(dst), "value", states.get(dst, "ACTIVE")))
            is_cert_fault = (dst in certified_fault_accused)
            is_revoking = (state_val in ("REVOCATION_PROPOSED", "REVOKED"))
            is_cert_susp = (state_val == "SUSPECTED" and dst in certified_suspected)

            if is_cert_fault or is_revoking or is_cert_susp:
                A[i, j] = 0.0
                continue

            entries = pair_entries.get((src, dst), [])
            e_pos = 0.0
            n_pos_count = 0.0
            n_neg_count = 0.0

            for e in entries:
                details = getattr(e, "details", {})
                if not isinstance(details, dict):
                    continue

                raw_rating = details.get("rating", 1.0)
                try:
                    if isinstance(raw_rating, bool):
                        continue
                    rating_val = float(raw_rating)
                    if not math.isfinite(rating_val):
                        continue
                except (ValueError, TypeError):
                    continue

                if rating_val > 0.0:
                    n_pos_count += 1.0
                    m_root = str(details.get("merkle_root", "")).strip().lower()
                    tx_id = str(getattr(e, "entry_id", ""))

                    if (src, dst, m_root, tx_id) in delivery_keys:
                        gamma_ev = 1.00  # Tier 3: Local Verified Delivery
                    elif m_root and m_root in manifest_roots:
                        gamma_ev = mu_referenced  # Tier 2: Manifest Referenced
                    else:
                        gamma_ev = mu_unverified  # Tier 1: Unindexed Receipt

                    raw_ts = details.get("receipt_timestamp", getattr(e, "timestamp", 0.0))
                    try:
                        e_ts = float(raw_ts)
                        if not math.isfinite(e_ts):
                            e_ts = 0.0
                    except (ValueError, TypeError):
                        e_ts = 0.0

                    if t_ref is not None:
                        dt = t_ref - e_ts
                        if dt < -60.0:
                            gamma_time = 0.0
                        elif dt <= 0.0:
                            gamma_time = 1.0
                        else:
                            gamma_time = math.exp(-dt / tau_seconds)
                    else:
                        gamma_time = 1.0

                    e_pos += gamma_ev * gamma_time
                elif rating_val < 0.0:
                    n_neg_count += 1.0
                else:
                    pass  # rating_val == 0.0 is neutral, skipped

            if n_pos_count > 0.0 and e_pos > 0.0:
                gamma_dispute = max(0.0, 1.0 - (2.0 * n_neg_count / (n_pos_count + 1.0)))
                phi_val = k_max * math.tanh((lambda_sat * e_pos) / k_max)
                A[i, j] = phi_val * gamma_dispute
            else:
                A[i, j] = 0.0

    # 7. Topology Damping (Active strictly in ablation modes)
    Omega = np.ones((n, n), dtype=np.float64)

    if mode in (TrustComputationMode.TOPOLOGY_ONLY, TrustComputationMode.FULL_EW):
        H = np.zeros(n, dtype=np.float64)
        denom_norm = math.log(max(2, n - 1))
        for i in range(n):
            row_sum = np.sum(A[i, :])
            if row_sum > 0:
                p_dist = A[i, :] / row_sum
                nonzero_p = p_dist[p_dist > 0]
                entropy = -np.sum(nonzero_p * np.log(nonzero_p))
                H[i] = min(1.0, max(0.0, entropy / denom_norm))
            else:
                H[i] = 0.0

        for i in range(n):
            for j in range(n):
                if i != j and A[i, j] > 0:
                    a_ij = A[i, j]
                    a_ji = A[j, i]
                    rho_ij = (2.0 * min(a_ij, a_ji)) / (a_ij + a_ji + delta_reg)
                    min_entropy = min(H[i], H[j])
                    sigma_ij = rho_ij * math.pow(1.0 - min_entropy, beta_entropy)
                    Omega[i, j] = max(epsilon_floor, 1.0 - (theta_penalty * sigma_ij))

    # 8. Effective Matrix S_prime and Stochastic Matrix C_prime
    S_prime = Omega * A
    C_prime = np.zeros((n, n), dtype=np.float64)

    for i in range(n):
        row_total = np.sum(S_prime[i, :])
        if row_total > 0:
            C_prime[i, :] = S_prime[i, :] / row_total
        else:
            C_prime[i, :] = p  # Dangling row fallback

    # 9. Power Iteration (Euclidean L2 norm stopping criterion)
    t = p.copy()
    C_prime_T = C_prime.T
    converged = False
    executed_iters = 0

    for iteration in range(1, max_iter + 1):
        executed_iters = iteration
        t_next = (1.0 - alpha) * np.dot(C_prime_T, t) + (alpha * p)
        delta = np.linalg.norm(t_next - t)
        t = t_next
        if delta < tol:
            converged = True
            break

    return {canonical_peers[i]: float(t[i]) for i in range(n)}, converged, executed_iters


compute_ew_eigentrust = compute_ew_eigentrust_v1_8

