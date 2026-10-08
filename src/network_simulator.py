"""
P2P Network Simulation & Adversarial Benchmark Engine
Integrates the complete 4-layer PKI and Trust Management architecture:
- Layer 1: Self-sovereign Ed25519 identity, full 64-hex DIDs, PoW admission.
- Layer 2: Web-of-Trust mesh certification, multi-path routing, peer eviction.
- Layer 3: Merkle inclusion proofs, content manifests, bilateral receipts,
           fault evidence contradiction, processed-evidence journal, vanilla EigenTrust.
- Layer 4: Revocation proposals, supernode quorum authorization (m-of-n CRR),
           re-admission prevention, authorized Shamir key recovery and key rotation.

NO DIRECT REPUTATION OR S-MATRIX MUTATION IS PERMITTED.
"""

import time
import random
import copy
import hashlib
import sys
import os
from typing import List, Dict, Tuple, Optional, Any, Set
import numpy as np

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Layer 1
from src.layer1_identity import PeerIdentity, PeerState, P2PCertificate

# Layer 2
from src.layer2_mesh_pki import MeshPKINetwork, CrossCertificate

# Layer 3
from src.layer3_eigentrust import (
    MerkleTree, BilateralReceipt, EigenTrustEngine,
    verify_merkle_proof, hash_proof,
    ContentManifest, ContentRequest, ChunkResponse, FaultEvidenceRecord,
    SimulatorCanonicalJournal
)

# Layer 4
from src.layer4_recovery import (
    CertificateRevocationRecord, ShamirSecretSharing,
    RevocationProposal, LocalRevocationStore, RevocationCoordinator,
    evict_peer_from_mesh, process_incoming_crr,
    RecoveryAuthorizationToken, RecoveryRequest, KeyRecoveryCoordinator,
    KeyRotationCertificate, rotate_key_after_recovery, is_key_valid_for_operations
)


class SimulatedNode:
    """
    Simulated node backed by complete Layer 1 cryptographic identity and protocol state.
    """
    def __init__(self, alias: str, is_sybil: bool = False, is_supernode: bool = False, difficulty_bits: int = 8):
        self.alias = alias
        self.is_sybil = is_sybil
        self.is_supernode = is_supernode
        self.difficulty_bits = difficulty_bits

        # Real Layer 1 cryptographic identity and PoW
        self.identity = PeerIdentity(alias=alias, difficulty_bits=difficulty_bits)
        self.did = self.identity.did
        self.public_key_hex = self.identity.public_key_hex

        # Local storage for content and manifests
        self.files: Dict[str, bytes] = {}
        self.manifests: Dict[str, ContentManifest] = {}
        self.merkle_trees: Dict[str, MerkleTree] = {}
        self.shares: List[Tuple[int, int]] = []

    def generate_file(self, content_id: str, size_kb: int = 64, chunk_size_kb: int = 16) -> Tuple[bytes, ContentManifest, MerkleTree]:
        """
        Splits content into chunks, constructs authentic Merkle tree, and creates signed ContentManifest.
        """
        chunk_bytes_len = chunk_size_kb * 1024
        total_len = size_kb * 1024
        payload = (f"{content_id}:{self.alias}:" + ("A" * 64)).encode("utf-8")
        repeats = (total_len // len(payload)) + 1
        content = (payload * repeats)[:total_len]

        chunks = [content[i:i + chunk_bytes_len] for i in range(0, len(content), chunk_bytes_len)]
        tree = MerkleTree(chunks)

        now = time.time()
        manifest = ContentManifest(
            content_id=content_id,
            root_hash=tree.root_hash,
            total_chunks=len(chunks),
            chunk_size_bytes=chunk_bytes_len,
            file_size_bytes=len(content),
            publisher_did=self.did,
            timestamp=now,
            signature_hex=""
        )
        manifest.signature_hex = self.identity.sign(manifest.payload_bytes()).hex()

        self.files[content_id] = content
        self.manifests[content_id] = manifest
        self.merkle_trees[content_id] = tree
        return content, manifest, tree

    def get_chunk(self, content_id: str, chunk_index: int, chunk_size_kb: int = 16) -> bytes:
        chunk_bytes_len = chunk_size_kb * 1024
        content = self.files.get(content_id, b"")
        start = chunk_index * chunk_bytes_len
        return content[start:start + chunk_bytes_len]


class SwarmSimulation:
    """
    Adversarial Swarm Simulator enforcing all four protocol layers without shortcuts.
    """
    def __init__(
        self,
        num_honest: int = 20,
        num_supernodes: int = 5,
        num_sybils: int = 15,
        seed: int = 42,
        difficulty_bits: int = 8
    ):
        self.seed = seed
        random.seed(seed)
        np.random.seed(seed)

        self.difficulty_bits = difficulty_bits
        self.mesh = MeshPKINetwork(max_hops=4)
        self.nodes: Dict[str, SimulatedNode] = {}
        self.supernodes: List[SimulatedNode] = []
        self.honest_nodes: List[SimulatedNode] = []
        self.sybil_nodes: List[SimulatedNode] = []

        # Comprehensive protocol execution metrics
        self.metrics: Dict[str, Dict[str, Any]] = {
            "admission": {
                "attempted": 0,
                "admitted": 0,
                "rejected": 0,
                "pow_failures": 0
            },
            "content": {
                "honest_deliveries": 0,
                "corrupted_deliveries": 0,
                "valid_merkle_verifications": 0,
                "invalid_merkle_verifications": 0
            },
            "evidence": {
                "positive_receipts": 0,
                "negative_receipts": 0,
                "fault_evidence_generated": 0,
                "fault_evidence_accepted": 0,
                "fault_evidence_rejected": 0,
                "replay_attempts": 0,
                "replay_rejections": 0
            },
            "trust": {
                "s_updates": 0,
                "eigentrust_iterations": 0,
                "final_trust_vector": {}
            },
            "revocation": {
                "suspected_transitions": 0,
                "revocation_proposals": 0,
                "quorum_approvals": 0,
                "quorum_failures": 0,
                "revoked_peers": 0,
                "eviction_events": 0,
                "readmission_attempts": 0,
                "readmission_rejections": 0
            },
            "recovery": {
                "recovery_requests": 0,
                "auth_successes": 0,
                "auth_failures": 0,
                "reconstruction_successes": 0,
                "reconstruction_failures": 0,
                "key_rotations": 0,
                "old_key_invalidations": 0
            }
        }

        # Cache of committed artifacts for replay testing
        self.committed_receipts: List[BilateralReceipt] = []
        self.committed_fault_evidence: List[FaultEvidenceRecord] = []

        # 1. Real Admission: Supernodes
        for i in range(num_supernodes):
            sn = SimulatedNode(f"Supernode_{i+1}", is_supernode=True, difficulty_bits=difficulty_bits)
            self._admit_node(sn)
            self.supernodes.append(sn)

        # 2. Real Admission: Honest Nodes
        for i in range(num_honest):
            hn = SimulatedNode(f"Honest_{i+1}", difficulty_bits=difficulty_bits)
            self._admit_node(hn)
            self.honest_nodes.append(hn)

        # 3. Real Admission: Sybil Nodes
        for i in range(num_sybils):
            syn = SimulatedNode(f"Sybil_{i+1}", is_sybil=True, difficulty_bits=difficulty_bits)
            self._admit_node(syn)
            self.sybil_nodes.append(syn)

        # Initialize Layer 3 EigenTrust Engine with canonical journal
        all_dids = list(self.nodes.keys())
        sn_dids = [sn.did for sn in self.supernodes]
        self.canonical_journal = SimulatorCanonicalJournal()
        self.eigentrust = EigenTrustEngine(
            peers=all_dids,
            pre_trusted_peers=sn_dids,
            alpha=0.15,
            journal=self.canonical_journal
        )
        for node in self.nodes.values():
            self.eigentrust.register_peer(node.identity)

        # Cross-certify supernodes with each other (Layer 2 mesh foundation)
        for i in range(len(self.supernodes)):
            for j in range(i + 1, len(self.supernodes)):
                self.mesh.issue_cross_certificate(self.supernodes[i].identity, self.supernodes[j].identity, 0.95)
                self.mesh.issue_cross_certificate(self.supernodes[j].identity, self.supernodes[i].identity, 0.95)

        # Initialize Layer 4 Revocation Coordinator (3-of-5 supernode quorum)
        self.threshold_m = 3
        self.supernode_pubkeys = {sn.did: sn.public_key_hex for sn in self.supernodes}
        self.coordinator = RevocationCoordinator(
            supernode_pubkeys=self.supernode_pubkeys,
            threshold_m=self.threshold_m,
            voting_timeout=600.0,
            subjective_suspicion_timeout=300.0
        )
        self.revocation_store = self.coordinator.revocation_store
        for node in self.nodes.values():
            self.coordinator.set_peer_state(node.did, PeerState.ACTIVE)

        # Key recovery coordinator with guardian
        self.guardian = PeerIdentity("RecoveryGuardian", difficulty_bits=difficulty_bits)
        self.recovery_coordinator = KeyRecoveryCoordinator(guardian_pubkey_hex=self.guardian.public_key_hex)

        # Honest nodes and supernodes publish initial content
        for node in self.honest_nodes + self.supernodes:
            node.generate_file(f"content-{node.alias}-init", size_kb=64, chunk_size_kb=16)

    def _admit_node(self, node: SimulatedNode) -> bool:
        """
        Admit peer through real Layer 1/2 validation path.
        """
        self.metrics["admission"]["attempted"] += 1
        # Check Layer 1 PoW validity
        if not PeerIdentity.verify_certificate(node.identity.certificate, min_difficulty=self.difficulty_bits):
            self.metrics["admission"]["pow_failures"] += 1
            self.metrics["admission"]["rejected"] += 1
            return False

        # Check Layer 2 registration
        admitted = self.mesh.register_peer(node.identity, min_difficulty=self.difficulty_bits)
        if admitted:
            self.nodes[node.did] = node
            self.metrics["admission"]["admitted"] += 1
            return True
        else:
            self.metrics["admission"]["rejected"] += 1
            return False

    def execute_transaction_round(self, round_num: int) -> Dict[str, int]:
        """
        Executes one transaction round strictly through the 4-layer protocol pipeline:
        - Honest Merkle-authenticated chunk requests and dual bilateral receipts.
        - Collusive Sybil ring transactions.
        - Malicious chunk poisoning -> FaultEvidenceRecord -> SUSPECTED -> Quorum CRR -> Eviction.
        - Replay attacks on receipts and fault evidence.
        - Zero direct S-matrix mutation.
        """
        stats = {
            "honest_success": 0,
            "poison_detected": 0,
            "sybil_collusion_attempts": 0,
            "replays_rejected": 0,
            "evictions": 0
        }

        # --- A. Honest Content Delivery & Receipt Accounting ---
        for client in self.honest_nodes:
            if client.did not in self.mesh.peers or client.identity.state != PeerState.ACTIVE:
                continue

            # Select available active provider
            candidates = [
                n for n in (self.honest_nodes + self.supernodes)
                if n.did != client.did and n.did in self.mesh.peers and n.identity.state == PeerState.ACTIVE
            ]
            if not candidates:
                continue
            provider = random.choice(candidates)

            # Ensure provider has content
            content_id = f"content-{provider.alias}-r{round_num}"
            if content_id not in provider.manifests:
                provider.generate_file(content_id, size_kb=64, chunk_size_kb=16)

            manifest = provider.manifests[content_id]
            tree = provider.merkle_trees[content_id]
            chunk_idx = round_num % manifest.total_chunks

            # 1. Client creates signed ContentRequest
            req_id = f"req-h-r{round_num}-{client.alias}-{provider.alias}-{chunk_idx}"
            now = time.time()
            nonce_req = f"nonce-req-{req_id}"
            req = ContentRequest(
                req_id=req_id,
                client_did=client.did,
                server_did=provider.did,
                content_id=content_id,
                chunk_index=chunk_idx,
                merkle_root=manifest.root_hash,
                timestamp=now,
                nonce=nonce_req,
                client_sig_hex=""
            )
            req.client_sig_hex = client.identity.sign(req.payload_bytes()).hex()

            # 2. Provider generates signed ChunkResponse with authentic Merkle proof
            chunk_bytes = provider.get_chunk(content_id, chunk_idx)
            proof = tree.generate_proof(chunk_idx)
            proof_h = hash_proof(proof)
            chunk_h = hashlib.sha256(chunk_bytes).hexdigest().lower()
            resp = ChunkResponse(
                req_id=req_id,
                client_did=client.did,
                server_did=provider.did,
                content_id=content_id,
                chunk_index=chunk_idx,
                chunk_bytes=chunk_bytes,
                chunk_hash=chunk_h,
                proof_hash=proof_h,
                merkle_root=manifest.root_hash,
                timestamp=now,
                nonce=nonce_req,
                merkle_proof=proof,
                server_sig_hex=""
            )
            resp.server_sig_hex = provider.identity.sign(resp.payload_bytes()).hex()

            # 3. Client validates response using Phase 2 verification
            if resp.verify(provider.public_key_hex, req):
                self.metrics["content"]["honest_deliveries"] += 1
                self.metrics["content"]["valid_merkle_verifications"] += 1

                # 4. Client and Provider co-sign BilateralReceipt (+1.00)
                tx_id = f"tx-h-r{round_num}-{client.alias}-{provider.alias}-{chunk_idx}"
                receipt = BilateralReceipt(
                    tx_id=tx_id,
                    client_did=client.did,
                    client_pubkey_hex=client.public_key_hex,
                    server_did=provider.did,
                    server_pubkey_hex=provider.public_key_hex,
                    merkle_root=manifest.root_hash,
                    rating="+1.00",
                    timestamp=now,
                    nonce=f"nonce-rcpt-{tx_id}",
                    client_sig_hex="",
                    server_sig_hex=""
                )
                payload = receipt.payload_bytes()
                receipt.client_sig_hex = client.identity.sign(payload).hex()
                receipt.server_sig_hex = provider.identity.sign(payload).hex()

                # 5. Process through Phase 3 evidence pipeline
                if self.eigentrust.record_receipt(receipt):
                    self.metrics["evidence"]["positive_receipts"] += 1
                    self.metrics["trust"]["s_updates"] += 1
                    stats["honest_success"] += 1
                    self.committed_receipts.append(receipt)

                    # Tit-for-tat uploader fulfillment receipt
                    tx_recip_id = f"tx-recip-r{round_num}-{provider.alias}-{client.alias}"
                    recip_receipt = BilateralReceipt(
                        tx_id=tx_recip_id,
                        client_did=provider.did,
                        client_pubkey_hex=provider.public_key_hex,
                        server_did=client.did,
                        server_pubkey_hex=client.public_key_hex,
                        merkle_root=manifest.root_hash,
                        rating="+1.00",
                        timestamp=now,
                        nonce=f"nonce-rcpt-{tx_recip_id}",
                        client_sig_hex="",
                        server_sig_hex=""
                    )
                    recip_payload = recip_receipt.payload_bytes()
                    recip_receipt.client_sig_hex = provider.identity.sign(recip_payload).hex()
                    recip_receipt.server_sig_hex = client.identity.sign(recip_payload).hex()
                    if self.eigentrust.record_receipt(recip_receipt):
                        self.metrics["evidence"]["positive_receipts"] += 1
                        self.metrics["trust"]["s_updates"] += 1

        # Supernodes perform verified audit downloads on random active honest peers
        for sn in self.supernodes:
            active_honest = [h for h in self.honest_nodes if h.did in self.mesh.peers and h.identity.state == PeerState.ACTIVE]
            if not active_honest:
                continue
            audited = random.choice(active_honest)
            c_id = f"content-{audited.alias}-audit-r{round_num}"
            if c_id not in audited.manifests:
                audited.generate_file(c_id, size_kb=64, chunk_size_kb=16)

            m = audited.manifests[c_id]
            t = audited.merkle_trees[c_id]
            audit_req_id = f"req-audit-r{round_num}-{sn.alias}-{audited.alias}"
            now = time.time()
            a_req = ContentRequest(
                req_id=audit_req_id, client_did=sn.did, server_did=audited.did,
                content_id=c_id, chunk_index=0, merkle_root=m.root_hash,
                timestamp=now, nonce=f"nonce-{audit_req_id}", client_sig_hex=""
            )
            a_req.client_sig_hex = sn.identity.sign(a_req.payload_bytes()).hex()

            c_bytes = audited.get_chunk(c_id, 0)
            a_proof = t.generate_proof(0)
            a_resp = ChunkResponse(
                req_id=audit_req_id, client_did=sn.did, server_did=audited.did,
                content_id=c_id, chunk_index=0, chunk_bytes=c_bytes,
                chunk_hash=hashlib.sha256(c_bytes).hexdigest().lower(),
                proof_hash=hash_proof(a_proof), merkle_root=m.root_hash,
                timestamp=now, nonce=a_req.nonce, merkle_proof=a_proof, server_sig_hex=""
            )
            a_resp.server_sig_hex = audited.identity.sign(a_resp.payload_bytes()).hex()

            if a_resp.verify(audited.public_key_hex, a_req):
                audit_tx_id = f"tx-audit-r{round_num}-{sn.alias}-{audited.alias}"
                audit_receipt = BilateralReceipt(
                    tx_id=audit_tx_id, client_did=sn.did, client_pubkey_hex=sn.public_key_hex,
                    server_did=audited.did, server_pubkey_hex=audited.public_key_hex,
                    merkle_root=m.root_hash, rating="+1.00", timestamp=now,
                    nonce=f"nonce-{audit_tx_id}", client_sig_hex="", server_sig_hex=""
                )
                audit_payload = audit_receipt.payload_bytes()
                audit_receipt.client_sig_hex = sn.identity.sign(audit_payload).hex()
                audit_receipt.server_sig_hex = audited.identity.sign(audit_payload).hex()
                if self.eigentrust.record_receipt(audit_receipt):
                    self.metrics["evidence"]["positive_receipts"] += 1
                    self.metrics["trust"]["s_updates"] += 1

        # --- B. Sybil Collusion Ring (Connected Baseline) ---
        active_sybils = [s for s in self.sybil_nodes if s.did in self.mesh.peers and s.identity.state == PeerState.ACTIVE]
        for sybil_a in active_sybils:
            other_sybils = [s for s in active_sybils if s.did != sybil_a.did]
            if not other_sybils:
                continue
            sybil_b = random.choice(other_sybils)

            # Sybils exchange valid mutual receipts
            now = time.time()
            tx_sybil_id = f"tx-sybil-r{round_num}-{sybil_a.alias}-{sybil_b.alias}"
            dummy_root = "0" * 64
            sybil_receipt = BilateralReceipt(
                tx_id=tx_sybil_id, client_did=sybil_a.did, client_pubkey_hex=sybil_a.public_key_hex,
                server_did=sybil_b.did, server_pubkey_hex=sybil_b.public_key_hex,
                merkle_root=dummy_root, rating="+1.00", timestamp=now,
                nonce=f"nonce-{tx_sybil_id}", client_sig_hex="", server_sig_hex=""
            )
            s_payload = sybil_receipt.payload_bytes()
            sybil_receipt.client_sig_hex = sybil_a.identity.sign(s_payload).hex()
            sybil_receipt.server_sig_hex = sybil_b.identity.sign(s_payload).hex()

            # Processed through Phase 3 evidence pipeline
            if self.eigentrust.record_receipt(sybil_receipt):
                self.metrics["evidence"]["positive_receipts"] += 1
                self.metrics["trust"]["s_updates"] += 1
                stats["sybil_collusion_attempts"] += 1

        # --- C. Poisoning Attack, Contradiction Evidence, Quorum CRR & Eviction ---
        active_honest = [h for h in self.honest_nodes if h.did in self.mesh.peers and h.identity.state == PeerState.ACTIVE]
        if active_sybils and active_honest:
            victim = random.choice(active_honest)
            attacker = random.choice(active_sybils)

            # Authentic content setup
            pub = self.supernodes[0]
            auth_cid = f"auth-content-r{round_num}"
            if auth_cid not in pub.manifests:
                pub.generate_file(auth_cid, size_kb=64, chunk_size_kb=16)

            auth_manifest = pub.manifests[auth_cid]
            auth_tree = pub.merkle_trees[auth_cid]
            auth_chunk_bytes = pub.get_chunk(auth_cid, 0)
            auth_chunk_hash = hashlib.sha256(auth_chunk_bytes).hexdigest().lower()
            auth_proof = auth_tree.generate_proof(0)

            # 1. Victim requests chunk 0 from attacker
            poison_req_id = f"req-poison-r{round_num}-{victim.alias}-{attacker.alias}"
            now = time.time()
            nonce_p = f"nonce-{poison_req_id}"
            p_req = ContentRequest(
                req_id=poison_req_id, client_did=victim.did, server_did=attacker.did,
                content_id=auth_cid, chunk_index=0, merkle_root=auth_manifest.root_hash,
                timestamp=now, nonce=nonce_p, client_sig_hex=""
            )
            p_req.client_sig_hex = victim.identity.sign(p_req.payload_bytes()).hex()

            # 2. Attacker returns poisoned chunk with server-signed delivery envelope
            poisoned_bytes = b"POISONED_CORRUPTED_PAYLOAD_CHUNK_DATA"
            poisoned_chunk_hash = hashlib.sha256(poisoned_bytes).hexdigest().lower()
            fake_proof = [copy.deepcopy(auth_proof[0])] if auth_proof else []
            if fake_proof:
                fake_proof[0].sibling_hash = "f" * 64
            fake_proof_hash = hash_proof(fake_proof)

            poison_resp = ChunkResponse(
                req_id=poison_req_id, client_did=victim.did, server_did=attacker.did,
                content_id=auth_cid, chunk_index=0, chunk_bytes=poisoned_bytes,
                chunk_hash=poisoned_chunk_hash, proof_hash=fake_proof_hash,
                merkle_root=auth_manifest.root_hash, timestamp=now, nonce=nonce_p,
                merkle_proof=fake_proof, server_sig_hex=""
            )
            poison_resp.server_sig_hex = attacker.identity.sign(poison_resp.payload_bytes()).hex()

            # 3. Victim validates chunk: Merkle contradiction caught
            if not poison_resp.verify(attacker.public_key_hex, p_req):
                self.metrics["content"]["corrupted_deliveries"] += 1
                self.metrics["content"]["invalid_merkle_verifications"] += 1
                stats["poison_detected"] += 1

                # 4. Construct certified FaultEvidenceRecord
                ev_id = f"ev-fault-r{round_num}-{attacker.alias}-{victim.alias}"
                fault_ev = FaultEvidenceRecord(
                    evidence_id=ev_id,
                    req_id=poison_req_id,
                    reporter_did=victim.did,
                    accused_did=attacker.did,
                    content_id=auth_cid,
                    merkle_root=auth_manifest.root_hash,
                    chunk_index=0,
                    delivered_chunk_hash=poisoned_chunk_hash,
                    delivered_proof_hash=fake_proof_hash,
                    manifest_envelope=auth_manifest,
                    delivery_envelope=poison_resp,
                    authentic_chunk_hash=auth_chunk_hash,
                    authentic_merkle_proof=auth_proof,
                    timestamp=now,
                    reporter_sig_hex=""
                )
                fault_ev.reporter_sig_hex = victim.identity.sign(fault_ev.payload_bytes()).hex()
                self.metrics["evidence"]["fault_evidence_generated"] += 1

                # 5. Process through Phase 3 evidence validation pipeline
                # Deducts -2.0 and transitions attacker to SUSPECTED
                if self.eigentrust.record_fault_evidence(
                    fault_ev,
                    reporter_pubkey_hex=victim.public_key_hex,
                    accused_pubkey_hex=attacker.public_key_hex,
                    manifest_publisher_pubkey_hex=pub.public_key_hex
                ):
                    self.metrics["evidence"]["fault_evidence_accepted"] += 1
                    self.metrics["revocation"]["suspected_transitions"] += 1
                    self.coordinator.record_suspicion(attacker.did, is_certified=True, timestamp=now)
                    self.committed_fault_evidence.append(fault_ev)

                    # 6. Revocation Proposal (Flow 17)
                    prop_id = f"prop-r{round_num}-{attacker.alias}"
                    proposal = RevocationProposal(
                        proposal_id=prop_id,
                        reporter_did=victim.did,
                        accused_did=attacker.did,
                        evidence=fault_ev,
                        timestamp=now,
                        timeout=600.0
                    )
                    proposal.reporter_sig_hex = victim.identity.sign(proposal.payload_bytes()).hex()

                    if self.coordinator.submit_proposal(proposal):
                        self.metrics["revocation"]["revocation_proposals"] += 1

                        # 7. Supernode Quorum Authorization (Flow 18, 3-of-5)
                        draft_crr = CertificateRevocationRecord(
                            revocation_id=f"crr-{prop_id}",
                            revoked_did=attacker.did,
                            revoked_pubkey_hex=attacker.public_key_hex,
                            reason="ATTRIBUTABLE_INCONSISTENT_DELIVERY",
                            evidence_id=fault_ev.evidence_id,
                            timestamp=now
                        )
                        crr_payload = draft_crr.payload_bytes()

                        final_crr = None
                        for sn in self.supernodes[:self.threshold_m]:
                            sig_sn = sn.identity.sign(crr_payload).hex()
                            ok, res_crr = self.coordinator.cast_vote(prop_id, sn.did, sig_sn)
                            if res_crr is not None:
                                final_crr = res_crr

                        if final_crr is not None:
                            self.metrics["revocation"]["quorum_approvals"] += 1
                            self.metrics["revocation"]["revoked_peers"] += 1

                            # 8. Eviction from Layer 2 Mesh Network (Flow 20)
                            if evict_peer_from_mesh(self.mesh, final_crr, self.supernode_pubkeys, self.threshold_m):
                                self.metrics["revocation"]["eviction_events"] += 1
                                stats["evictions"] += 1

                            # 9. Propagation of CRR to Local Revocation Store
                            process_incoming_crr(final_crr, self.supernode_pubkeys, self.threshold_m, self.revocation_store)

                            # 10. Attempt Re-Admission (Must be rejected)
                            self.metrics["revocation"]["readmission_attempts"] += 1
                            if not self.mesh.register_peer(attacker.identity, min_difficulty=self.difficulty_bits):
                                self.metrics["revocation"]["readmission_rejections"] += 1

        # --- D. Replay Attack Demonstrations ---
        # 1. Replay previously committed receipt
        if self.committed_receipts:
            prev_rcpt = random.choice(self.committed_receipts)
            self.metrics["evidence"]["replay_attempts"] += 1
            if not self.eigentrust.record_receipt(prev_rcpt):
                self.metrics["evidence"]["replay_rejections"] += 1
                stats["replays_rejected"] += 1

        # 2. Replay previously committed fault evidence
        if self.committed_fault_evidence:
            prev_fe = random.choice(self.committed_fault_evidence)
            self.metrics["evidence"]["replay_attempts"] += 1
            if not self.eigentrust.record_fault_evidence(prev_fe):
                self.metrics["evidence"]["replay_rejections"] += 1
                stats["replays_rejected"] += 1

        return stats

    def demonstrate_key_recovery(self) -> Tuple[bool, int, str, str]:
        """
        Executes complete Layer 4 Shamir Secret Sharing recovery and mandatory post-recovery key rotation.
        Demonstrates:
        RecoveryRequest -> Authentication -> AuthTok Authorization -> Threshold Shares -> Reconstruction -> Key Rotation.
        """
        target_peer = self.honest_nodes[0]
        # Private master seed from target peer's actual Ed25519 private key
        from cryptography.hazmat.primitives import serialization
        master_secret = int.from_bytes(
            target_peer.identity.private_key.private_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PrivateFormat.Raw,
                encryption_algorithm=serialization.NoEncryption()
            ),
            byteorder="big"
        )

        # 1. Split secret among 5 supernodes (3-of-5 threshold)
        shares = ShamirSecretSharing.split_secret(master_secret, k_threshold=3, n_shares=5)
        for idx, sn in enumerate(self.supernodes):
            sn.shares.append(shares[idx])

        # 2. Guardian issues signed RecoveryAuthorizationToken (AuthTok)
        now = time.time()
        token = RecoveryAuthorizationToken(
            token_id=f"tok-recov-{target_peer.alias}",
            subject_did=target_peer.did,
            requester_pubkey_hex=target_peer.public_key_hex,
            custodian_did=self.supernodes[0].did,
            timestamp=now,
            expiry=now + 600.0,
            authorization_scope="KEY_RECOVERY"
        )
        token.guardian_signature_hex = self.guardian.sign(token.payload_bytes()).hex()

        # 3. Requester submits authenticated RecoveryRequest
        req = RecoveryRequest(
            request_id=f"req-recov-{target_peer.alias}",
            subject_did=target_peer.did,
            requester_pubkey_hex=target_peer.public_key_hex,
            timestamp=now,
            auth_token=token
        )
        req.requester_sig_hex = target_peer.identity.sign(req.payload_bytes()).hex()

        self.metrics["recovery"]["recovery_requests"] += 1

        # 4. Custodian authorizes release of share
        try:
            released_share_0 = self.recovery_coordinator.authorize_share_release(
                req, self.supernodes[0].did, self.supernodes[0].shares[-1], current_time=now
            )
            self.metrics["recovery"]["auth_successes"] += 1
        except Exception:
            self.metrics["recovery"]["auth_failures"] += 1
            return False, 0, "", ""

        # Collect 3 shares
        collected_shares = [released_share_0, self.supernodes[1].shares[-1], self.supernodes[2].shares[-1]]

        # 5. Reconstruct secret with authorization
        try:
            token_reconstruct = copy.deepcopy(token)
            token_reconstruct.token_id = f"tok-recon-{target_peer.alias}"
            token_reconstruct.guardian_signature_hex = self.guardian.sign(token_reconstruct.payload_bytes()).hex()
            reconstructed = self.recovery_coordinator.reconstruct_secret_with_authorization(
                collected_shares, token_reconstruct, threshold_k=3, current_time=now
            )
            self.metrics["recovery"]["reconstruction_successes"] += 1
        except Exception:
            self.metrics["recovery"]["reconstruction_failures"] += 1
            return False, 0, "", ""

        # 6. Mandatory Post-Recovery Key Rotation
        new_peer_identity, rot_cert = rotate_key_after_recovery(
            target_peer.identity, reconstructed, f"{target_peer.alias}_Recovered"
        )
        self.metrics["recovery"]["key_rotations"] += 1
        self.metrics["recovery"]["old_key_invalidations"] += 1

        # Register rotated identity into mesh
        new_node = SimulatedNode(f"{target_peer.alias}_Recovered", difficulty_bits=self.difficulty_bits)
        new_node.identity = new_peer_identity
        new_node.did = new_peer_identity.did
        new_node.public_key_hex = new_peer_identity.public_key_hex

        self.mesh.register_peer(new_node.identity, min_difficulty=self.difficulty_bits)
        self.nodes[new_node.did] = new_node

        success = (reconstructed == master_secret) and is_key_valid_for_operations(new_peer_identity) and not is_key_valid_for_operations(target_peer.identity)
        return success, reconstructed, target_peer.did, new_node.did

    def run_simulation(self, total_rounds: int = 15) -> Dict[str, Any]:
        """
        Runs full simulation trajectory over specified rounds.
        """
        history: Dict[str, Any] = {
            "rounds": list(range(1, total_rounds + 1)),
            "supernode_avg": [],
            "honest_avg": [],
            "sybil_avg": [],
            "stats": []
        }

        for r in range(1, total_rounds + 1):
            stats = self.execute_transaction_round(r)
            history["stats"].append(stats)

            scores = self.eigentrust.get_trust_scores()
            sn_scores = [scores[sn.did] for sn in self.supernodes if sn.did in scores]
            h_scores = [scores[h.did] for h in self.honest_nodes if h.did in scores]
            syb_scores = [scores[s.did] for s in self.sybil_nodes if s.did in scores]

            history["supernode_avg"].append(float(np.mean(sn_scores)) if sn_scores else 0.0)
            history["honest_avg"].append(float(np.mean(h_scores)) if h_scores else 0.0)
            history["sybil_avg"].append(float(np.mean(syb_scores)) if syb_scores else 0.0)

        self.metrics["trust"]["eigentrust_iterations"] = total_rounds
        self.metrics["trust"]["final_trust_vector"] = self.eigentrust.get_trust_scores()
        return history


if __name__ == '__main__':
    print("Initializing full 4-layer SwarmSimulation...")
    sim = SwarmSimulation(num_honest=10, num_supernodes=3, num_sybils=5, seed=42, difficulty_bits=8)
    print("Admitted nodes:", len(sim.nodes))
    hist = sim.run_simulation(total_rounds=5)
    print("Simulation completed successfully across 5 rounds.")
    print("Metrics snapshot:")
    for k, v in sim.metrics.items():
        if k != "trust":
            print(f"  {k}: {v}")
    rec_ok, sec, old_did, new_did = sim.demonstrate_key_recovery()
    print(f"Key recovery test: success={rec_ok}, old={old_did[:24]}..., new={new_did[:24]}...")
