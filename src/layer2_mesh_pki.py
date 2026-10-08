"""
Layer 2: Certification & Trust-Propagation Layer (Mesh PKI)
Implements Web-of-Trust Cross-Certification, Multi-Path Transitive Trust Validation
with strict intermediate-vertex disjointness and a maximum hop limit of k <= 4.
Dynamic Supernode Election is deferred per protocol freeze.
"""

import time
from dataclasses import dataclass
from typing import Dict, List, Set, Optional, Union, Any
from src.layer1_identity import PeerIdentity, P2PCertificate, PeerState


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
        data = f"PKI_V2_CROSSCERT:{self.issuer_did}:{self.subject_did}:{self.trust_weight:.4f}:{self.issued_at}:{self.expires_at}"
        return data.encode("utf-8")


class MeshPKINetwork:
    def __init__(self, max_hops: int = 4):
        self.max_hops = max_hops
        self.peers: Dict[str, Any] = {}
        self.supernode_dids: Set[str] = set()
        # Adjacency map: issuer_did -> list of CrossCertificates
        self.trust_graph: Dict[str, List[CrossCertificate]] = {}
        # Local revocation store: revoked_did -> record
        self.local_revocation_store: Dict[str, Any] = {}

    def register_peer(
        self,
        peer_or_cert: Union[PeerIdentity, P2PCertificate],
        min_difficulty: int = 12
    ) -> bool:
        """
        Registers peer after strictly validating certificate, PoW, freshness, DID binding,
        and checking against the local revocation store.
        If admitted, peer.state transitions to PeerState.ACTIVE.
        """
        if isinstance(peer_or_cert, PeerIdentity):
            peer = peer_or_cert
            cert = peer.certificate
        elif isinstance(peer_or_cert, P2PCertificate):
            peer = None
            cert = peer_or_cert
        else:
            return False

        # Check local revocation store
        if cert.did in self.local_revocation_store or cert.public_key_hex in self.local_revocation_store:
            return False

        # Validate certificate against Layer 1 requirements
        if not PeerIdentity.verify_certificate(cert, min_difficulty=min_difficulty):
            return False

        # Admission successful
        if peer is not None:
            peer.state = PeerState.ACTIVE
            self.peers[peer.did] = peer
        else:
            self.peers[cert.did] = cert

        if cert.did not in self.trust_graph:
            self.trust_graph[cert.did] = []

        return True

    def evict_peer(self, revoked_did: str, crr: Optional[Any] = None) -> bool:
        """
        Evicts a peer from the active mesh network upon revocation.
        """
        if crr is not None:
            self.local_revocation_store[revoked_did] = crr
        else:
            self.local_revocation_store[revoked_did] = True

        if revoked_did in self.peers:
            peer = self.peers[revoked_did]
            if hasattr(peer, "state"):
                peer.state = PeerState.REVOKED
            del self.peers[revoked_did]

        if revoked_did in self.trust_graph:
            del self.trust_graph[revoked_did]

        for issuer_did in list(self.trust_graph.keys()):
            self.trust_graph[issuer_did] = [
                c for c in self.trust_graph[issuer_did]
                if c.subject_did != revoked_did
            ]

        if revoked_did in self.supernode_dids:
            self.supernode_dids.remove(revoked_did)

        return True

    def elect_supernodes(
        self,
        peer_scores: Optional[Dict[str, float]] = None,
        peer_uptimes: Optional[Dict[str, float]] = None,
        score_threshold: float = 0.65,
        uptime_threshold: float = 0.99
    ) -> List[str]:
        """
        Dynamic supernode election is explicitly deferred per PROTOCOL_SPEC v2.2.0.
        """
        raise NotImplementedError("Dynamic supernode election is deferred to a future phase")

    def issue_cross_certificate(
        self,
        issuer: PeerIdentity,
        subject: PeerIdentity,
        trust_weight: float,
        duration_seconds: float = 86400
    ) -> CrossCertificate:
        """
        An issuer digitally cross-certifies a subject peer.
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
        
        if issuer.did not in self.trust_graph:
            self.trust_graph[issuer.did] = []
        self.trust_graph[issuer.did].append(cert)
        return cert

    def verify_cross_certificate(self, cert: CrossCertificate) -> bool:
        """
        Cryptographically verifies issuer's signature on cross-certificate and validity.
        Validates signature, expiration, and DID/public key bindings.
        """
        if time.time() > cert.expires_at:
            return False
        if not PeerIdentity.is_valid_did(cert.issuer_did, cert.issuer_pubkey_hex):
            return False
        if not PeerIdentity.is_valid_did(cert.subject_did, cert.subject_pubkey_hex):
            return False
        return PeerIdentity.verify_peer_signature(
            cert.issuer_pubkey_hex,
            cert.payload_bytes(),
            cert.signature_hex
        )

    def find_disjoint_paths(self, start_did: str, target_did: str) -> List[List[CrossCertificate]]:
        """
        Finds simple trust paths between start_did and target_did up to max_hops (k <= 4),
        filtered to guarantee strict intermediate-vertex disjointness:
        - start node may appear in every path
        - target node may appear in every path
        - no intermediate vertex may occur in more than one returned path
        """
        if start_did not in self.trust_graph or target_did not in self.trust_graph:
            return []
            
        candidate_paths: List[List[CrossCertificate]] = []
        visited_nodes: Set[str] = {start_did}

        def dfs(current: str, current_path: List[CrossCertificate], depth: int):
            if depth > self.max_hops:
                return
            if current == target_did and current_path:
                candidate_paths.append(list(current_path))
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

        def get_path_trust(path: List[CrossCertificate]) -> float:
            val = 1.0
            for c in path:
                val *= c.trust_weight
            return val

        # Sort candidate paths by path trust descending, then shorter hop count first
        candidate_paths.sort(key=lambda p: (get_path_trust(p), -len(p)), reverse=True)

        selected_paths: List[List[CrossCertificate]] = []
        used_intermediate_vertices: Set[str] = set()
        has_direct_path = False

        for path in candidate_paths:
            intermediate = {c.subject_did for c in path[:-1]}
            if not intermediate:
                # Direct edge start_did -> target_did
                if not has_direct_path:
                    selected_paths.append(path)
                    has_direct_path = True
            else:
                if not intermediate.intersection(used_intermediate_vertices):
                    selected_paths.append(path)
                    used_intermediate_vertices.update(intermediate)

        return selected_paths

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
