"""
Layer 3: Cryptographic Reputation Engine (EigenTrust & Merkle File Verification)
Implements Merkle Tree file integrity checking with genuine inclusion proofs,
content manifests, requests, chunk responses, fault evidence records,
bilateral co-signed transaction receipts, node-local processed-evidence journals,
ordered 7-stage evidence validation pipeline, and the EigenTrust power-iteration convergence algorithm.
"""

import hashlib
import time
import uuid
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any, Set, Union
import numpy as np

from src.layer1_identity import PeerIdentity, PeerState


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
                "nonce": receipt.nonce
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

    def get_trust_scores(self) -> Dict[str, float]:
        """Returns dictionary of DID -> normalized global trust score."""
        scores = self.run_power_iteration()
        return {self.peers[i]: float(scores[i]) for i in range(self.n)}
