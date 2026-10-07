"""
Layer 3: Cryptographic Reputation Engine (EigenTrust & Merkle File Verification)
Implements Merkle Tree file integrity checking, bilateral co-signed transaction receipts,
and the EigenTrust power-iteration convergence algorithm with pre-trusted seed damping.
"""

import hashlib
import time
import uuid
import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from src.layer1_identity import PeerIdentity


class MerkleTree:
    def __init__(self, data_chunks: List[bytes]):
        self.chunks = data_chunks
        self.leaf_hashes = [hashlib.sha256(chunk).hexdigest() for chunk in data_chunks]
        self.tree_levels = self._build_tree()
        self.root_hash = self.tree_levels[-1][0] if self.tree_levels else ""

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
                combined = hashlib.sha256(f"{left}{right}".encode("utf-8")).hexdigest()
                next_level.append(combined)
            levels.append(next_level)
        return levels

    def verify_chunk(self, chunk_index: int, chunk_bytes: bytes) -> bool:
        """Validates that a received chunk matches the leaf hash in the tree."""
        if chunk_index < 0 or chunk_index >= len(self.leaf_hashes):
            return False
        expected_hash = hashlib.sha256(chunk_bytes).hexdigest()
        return expected_hash == self.leaf_hashes[chunk_index]


@dataclass
class BilateralReceipt:
    tx_id: str
    client_did: str
    client_pubkey_hex: str
    server_did: str
    server_pubkey_hex: str
    merkle_root: str
    rating: float  # +1.0 for authentic file, -1.0 for corrupted/malicious
    timestamp: float
    client_sig_hex: str
    server_sig_hex: str

    def payload_bytes(self) -> bytes:
        data = f"{self.tx_id}:{self.client_did}:{self.server_did}:{self.merkle_root}:{self.rating:.2f}:{self.timestamp}"
        return data.encode("utf-8")

    def is_valid(self) -> bool:
        """Verifies that BOTH client and server cryptographically co-signed the receipt."""
        data = self.payload_bytes()
        valid_client = PeerIdentity.verify_peer_signature(
            self.client_pubkey_hex, data, self.client_sig_hex
        )
        valid_server = PeerIdentity.verify_peer_signature(
            self.server_pubkey_hex, data, self.server_sig_hex
        )
        return valid_client and valid_server


class EigenTrustEngine:
    def __init__(self, peers: List[str], pre_trusted_peers: List[str], alpha: float = 0.15):
        """
        peers: list of peer DIDs.
        pre_trusted_peers: subset of DIDs designated as seed anchors.
        alpha: pre-trusted damping probability (default 0.15).
        """
        self.peers = sorted(peers)
        self.peer_to_idx = {did: idx for idx, did in enumerate(self.peers)}
        self.n = len(self.peers)
        self.alpha = alpha
        
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

    def record_receipt(self, receipt: BilateralReceipt) -> bool:
        """Audits bilateral receipt and updates local satisfaction score."""
        if not receipt.is_valid():
            return False
        if receipt.client_did not in self.peer_to_idx or receipt.server_did not in self.peer_to_idx:
            return False
            
        i = self.peer_to_idx[receipt.client_did]
        j = self.peer_to_idx[receipt.server_did]
        
        # S_ij increases or decreases based on transaction rating
        self.S[i, j] += receipt.rating
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
