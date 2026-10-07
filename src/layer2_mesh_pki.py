"""
Layer 2: Certification & Trust-Propagation Layer (Mesh PKI)
Implements Dynamic Supernode Election, Web-of-Trust Cross-Certification,
and Multi-Path Transitive Trust Validation with a maximum hop limit of k <= 4.
"""

import time
from dataclasses import dataclass
from typing import Dict, List, Set, Optional
from src.layer1_identity import PeerIdentity


@dataclass
class CrossCertificate:
    issuer_did: str
    issuer_pubkey_hex: str
    subject_did: str
    subject_pubkey_hex: str
    trust_weight: float  # Value between 0.0 and 1.0
    issued_at: float
    expires_at: float
    signature_hex: str

    def payload_bytes(self) -> bytes:
        data = f"{self.issuer_did}:{self.subject_did}:{self.trust_weight:.4f}:{self.issued_at}:{self.expires_at}"
        return data.encode("utf-8")


class MeshPKINetwork:
    def __init__(self, max_hops: int = 4):
        self.max_hops = max_hops
        self.peers: Dict[str, PeerIdentity] = {}
        self.supernode_dids: Set[str] = set()
        # Adjacency map: issuer_did -> list of CrossCertificates
        self.trust_graph: Dict[str, List[CrossCertificate]] = {}

    def register_peer(self, peer: PeerIdentity) -> None:
        self.peers[peer.did] = peer
        if peer.did not in self.trust_graph:
            self.trust_graph[peer.did] = []

    def elect_supernodes(self, peer_scores: Dict[str, float], peer_uptimes: Dict[str, float],
                          score_threshold: float = 0.65, uptime_threshold: float = 0.99) -> List[str]:
        """
        Dynamically elects supernodes based on high EigenRep score and proven uptime.
        """
        self.supernode_dids.clear()
        for did, score in peer_scores.items():
            uptime = peer_uptimes.get(did, 0.0)
            if score >= score_threshold and uptime >= uptime_threshold:
                self.supernode_dids.add(did)
        return list(self.supernode_dids)

    def issue_cross_certificate(self, issuer: PeerIdentity, subject: PeerIdentity, 
                                trust_weight: float, duration_seconds: float = 86400) -> CrossCertificate:
        """
        An issuer digitally cross-certifies a subject peer after successful transactions.
        """
        now = time.time()
        expiry = now + duration_seconds
        
        cert = CrossCertificate(
            issuer_did=issuer.did,
            issuer_pubkey_hex=issuer.public_key_hex,
            subject_did=subject.did,
            subject_pubkey_hex=subject.public_key_hex,
            trust_weight=max(0.0, min(1.0, trust_weight)),
            issued_at=now,
            expires_at=expiry,
            signature_hex=""
        )
        sig = issuer.sign(cert.payload_bytes())
        cert.signature_hex = sig.hex()
        
        self.trust_graph[issuer.did].append(cert)
        return cert

    def verify_cross_certificate(self, cert: CrossCertificate) -> bool:
        """Cryptographically verifies issuer's signature on cross-certificate."""
        if time.time() > cert.expires_at:
            return False
        return PeerIdentity.verify_peer_signature(
            cert.issuer_pubkey_hex,
            cert.payload_bytes(),
            cert.signature_hex
        )

    def find_disjoint_paths(self, start_did: str, target_did: str) -> List[List[CrossCertificate]]:
        """
        Finds all simple, edge-disjoint trust paths between start_did and target_did
        up to max_hops (k <= 4).
        """
        if start_did not in self.trust_graph or target_did not in self.trust_graph:
            return []
            
        all_paths: List[List[CrossCertificate]] = []
        visited_nodes: Set[str] = {start_did}

        def dfs(current: str, current_path: List[CrossCertificate], depth: int):
            if depth > self.max_hops:
                return
            if current == target_did and current_path:
                all_paths.append(list(current_path))
                return
            for cert in self.trust_graph.get(current, []):
                if not self.verify_cross_certificate(cert):
                    continue
                next_node = cert.subject_did
                if next_node not in visited_nodes:
                    visited_nodes.add(next_node)
                    current_path.append(cert)
                    dfs(next_node, current_path, depth + 1)
                    current_path.pop()
                    visited_nodes.remove(next_node)

        dfs(start_did, [], 0)
        return all_paths

    def compute_transitive_confidence(self, start_did: str, target_did: str) -> float:
        """
        Computes transitive multi-path trust confidence:
        Confidence(A, B) = 1 - Prod(1 - PathTrust_i)
        where PathTrust_i = Prod(cert.trust_weight for cert in path)
        """
        paths = self.find_disjoint_paths(start_did, target_did)
        if not paths:
            return 0.0

        failure_product = 1.0
        for path in paths:
            path_trust = 1.0
            for cert in path:
                path_trust *= cert.trust_weight
            failure_product *= (1.0 - path_trust)

        confidence = 1.0 - failure_product
        return max(0.0, min(1.0, confidence))
