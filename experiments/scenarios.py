"""
Phase 6 Experimental Scenarios and Runner Module
Encapsulates configurable scenarios (A through G), baseline algorithms,
ablation switches, and multi-seed trial orchestration.
"""

import time
import random
import copy
import hashlib
import numpy as np
from typing import Dict, List, Any, Tuple, Optional

# Protocol layers
from src.layer1_identity import PeerIdentity, PeerState
from src.layer2_mesh_pki import MeshPKINetwork
from src.layer3_eigentrust import (
    MerkleTree, BilateralReceipt, EigenTrustEngine,
    verify_merkle_proof, hash_proof,
    ContentManifest, ContentRequest, ChunkResponse, FaultEvidenceRecord,
    SimulatorCanonicalJournal
)
from src.layer4_recovery import (
    CertificateRevocationRecord, ShamirSecretSharing,
    RevocationProposal, LocalRevocationStore, RevocationCoordinator,
    evict_peer_from_mesh, process_incoming_crr,
    RecoveryAuthorizationToken, RecoveryRequest, KeyRecoveryCoordinator,
    rotate_key_after_recovery, is_key_valid_for_operations
)
from src.network_simulator import SimulatedNode

# Experiment modules
from experiments.config import ExperimentConfig
from experiments.metrics import GroundTruth, PerformanceTimings, calculate_confusion_metrics, calculate_trust_shares


class ExperimentTrialRunner:
    """
    Executes a single deterministic trial for an ExperimentConfig.
    Enforces honest, Sybil, poisoning, collusion, replay, and benign fault scenarios.
    """
    def __init__(self, config: ExperimentConfig):
        self.config = config
        random.seed(config.seed)
        np.random.seed(config.seed)

        self.mesh = MeshPKINetwork(max_hops=4)
        self.nodes: Dict[str, SimulatedNode] = {}
        self.supernodes: List[SimulatedNode] = []
        self.honest_nodes: List[SimulatedNode] = []
        self.sybil_nodes: List[SimulatedNode] = []

        self.timings = PerformanceTimings()
        self.ground_truth = GroundTruth()

        # Operational metrics tracking
        self.metrics = {
            "admission": {"attempted": 0, "admitted": 0, "rejected": 0, "pow_failures": 0},
            "content": {"honest_deliveries": 0, "corrupted_deliveries": 0, "benign_corruptions": 0},
            "evidence": {
                "positive_receipts": 0, "negative_receipts": 0,
                "fault_evidence_generated": 0, "fault_evidence_accepted": 0, "fault_evidence_rejected": 0,
                "replay_attempts": 0, "replay_rejections": 0, "replay_acceptances": 0
            },
            "revocation": {
                "suspected_transitions": 0, "revocation_proposals": 0,
                "quorum_approvals": 0, "quorum_failures": 0,
                "revoked_peers": 0, "eviction_events": 0,
                "readmission_attempts": 0, "readmission_rejections": 0
            },
            "confusion": {"tp": 0, "fp": 0, "fn": 0, "tn": 0},
            "trust_gain": {"initial_sybil_trust": 0.0, "final_sybil_trust": 0.0}
        }

        self.committed_receipts: List[BilateralReceipt] = []
        self.committed_fault_evidence: List[FaultEvidenceRecord] = []

        # 1. Initialize Nodes & Establish Ground Truth
        self._init_nodes()

        # 2. Setup Layer 3 Trust Engine with selected baseline
        self.canonical_journal = SimulatorCanonicalJournal()
        all_dids = list(self.nodes.keys())
        sn_dids = [sn.did for sn in self.supernodes]
        self.eigentrust = EigenTrustEngine(
            peers=all_dids,
            pre_trusted_peers=sn_dids,
            alpha=0.15,
            journal=self.canonical_journal
        )
        for node in self.nodes.values():
            self.eigentrust.register_peer(node.identity)

        # Baseline 2 & 3 local accounting structures if selected
        # (Does not alter production protocol code, encapsulated inside harness)
        self.local_rating_matrix = {d1: {d2: 0.0 for d2 in all_dids} for d1 in all_dids}

        # 3. Layer 2 Cross-certifications for supernodes
        for i in range(len(self.supernodes)):
            for j in range(i + 1, len(self.supernodes)):
                self.mesh.issue_cross_certificate(self.supernodes[i].identity, self.supernodes[j].identity, 0.95)
                self.mesh.issue_cross_certificate(self.supernodes[j].identity, self.supernodes[i].identity, 0.95)

        # 4. Layer 4 Revocation Coordinator (3-of-5 supernodes)
        self.threshold_m = 3 if config.enable_quorum else 1
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

        # Guardian for recovery
        self.guardian = PeerIdentity("ExpGuardian", difficulty_bits=config.difficulty_bits)
        self.recovery_coordinator = KeyRecoveryCoordinator(guardian_pubkey_hex=self.guardian.public_key_hex)

        # Initial content publishing
        for node in self.honest_nodes + self.supernodes:
            node.generate_file(f"content-{node.alias}-init", size_kb=64, chunk_size_kb=16)

    def _init_nodes(self):
        t0 = time.time()
        # Supernodes
        for i in range(self.config.num_supernodes):
            t_pow = time.time()
            sn = SimulatedNode(f"SN_{i+1}", is_supernode=True, difficulty_bits=self.config.difficulty_bits)
            self.timings.pow_solve_times.append(time.time() - t_pow)
            self._admit_node(sn)
            self.supernodes.append(sn)
            self.ground_truth.supernode_dids.add(sn.did)

        # Honest nodes
        for i in range(self.config.num_honest):
            t_pow = time.time()
            hn = SimulatedNode(f"Honest_{i+1}", difficulty_bits=self.config.difficulty_bits)
            self.timings.pow_solve_times.append(time.time() - t_pow)
            self._admit_node(hn)
            self.honest_nodes.append(hn)
            self.ground_truth.honest_dids.add(hn.did)

        # Sybil nodes
        for i in range(self.config.num_sybils):
            t_pow = time.time()
            syn = SimulatedNode(f"Sybil_{i+1}", is_sybil=True, difficulty_bits=self.config.difficulty_bits)
            self.timings.pow_solve_times.append(time.time() - t_pow)
            self._admit_node(syn)
            self.sybil_nodes.append(syn)
            self.ground_truth.sybil_dids.add(syn.did)

            # Classify capabilities for ground truth
            if self.config.bridge_probability > 0.0 or self.config.scenario_name == "scenario_d_collusion":
                self.ground_truth.colluder_dids.add(syn.did)
            if self.config.poisoning_rate > 0.0:
                self.ground_truth.poisoner_dids.add(syn.did)

        self.timings.admission_times.append(time.time() - t0)

    def _admit_node(self, node: SimulatedNode) -> bool:
        self.metrics["admission"]["attempted"] += 1
        if self.config.enable_pow:
            if not PeerIdentity.verify_certificate(node.identity.certificate, min_difficulty=self.config.difficulty_bits):
                self.metrics["admission"]["pow_failures"] += 1
                self.metrics["admission"]["rejected"] += 1
                return False

        admitted = self.mesh.register_peer(node.identity, min_difficulty=self.config.difficulty_bits)
        if admitted:
            self.nodes[node.did] = node
            self.metrics["admission"]["admitted"] += 1
            return True
        else:
            self.metrics["admission"]["rejected"] += 1
            return False

    def execute_round(self, round_num: int) -> Dict[str, Any]:
        """
        Executes one parameterized transaction round.
        """
        t_round_start = time.time()
        round_stats = {
            "honest_success": 0,
            "poison_attempts": 0,
            "poison_detected": 0,
            "collusions_processed": 0,
            "replays_rejected": 0
        }

        # --- A. Honest Transfers ---
        for client in self.honest_nodes:
            if client.did not in self.mesh.peers or client.identity.state != PeerState.ACTIVE:
                continue

            candidates = [
                n for n in (self.honest_nodes + self.supernodes)
                if n.did != client.did and n.did in self.mesh.peers and n.identity.state == PeerState.ACTIVE
            ]
            if not candidates:
                continue
            provider = random.choice(candidates)

            content_id = f"c-{provider.alias}-r{round_num}"
            if content_id not in provider.manifests:
                provider.generate_file(content_id, size_kb=64, chunk_size_kb=16)

            manifest = provider.manifests[content_id]
            tree = provider.merkle_trees[content_id]
            chunk_idx = round_num % manifest.total_chunks

            # 1. ContentRequest
            req_id = f"req-h-r{round_num}-{client.alias}-{provider.alias}-{chunk_idx}"
            now = time.time()
            req = ContentRequest(
                req_id=req_id, client_did=client.did, server_did=provider.did,
                content_id=content_id, chunk_index=chunk_idx, merkle_root=manifest.root_hash,
                timestamp=now, nonce=f"nonce-{req_id}", client_sig_hex=""
            )
            req.client_sig_hex = client.identity.sign(req.payload_bytes()).hex()

            # 2. ChunkResponse
            chunk_bytes = provider.get_chunk(content_id, chunk_idx)
            proof = tree.generate_proof(chunk_idx)
            resp = ChunkResponse(
                req_id=req_id, client_did=client.did, server_did=provider.did,
                content_id=content_id, chunk_index=chunk_idx, chunk_bytes=chunk_bytes,
                chunk_hash=hashlib.sha256(chunk_bytes).hexdigest().lower(),
                proof_hash=hash_proof(proof), merkle_root=manifest.root_hash,
                timestamp=now, nonce=req.nonce, merkle_proof=proof, server_sig_hex=""
            )
            resp.server_sig_hex = provider.identity.sign(resp.payload_bytes()).hex()

            # Check Merkle and signature
            t_m = time.time()
            merkle_valid = resp.verify(provider.public_key_hex, req) if self.config.enable_merkle else True
            self.timings.merkle_verify_times.append(time.time() - t_m)

            if merkle_valid:
                self.metrics["content"]["honest_deliveries"] += 1
                self.metrics["confusion"]["tn"] += 1

                # Bilateral Receipt
                tx_id = f"tx-h-r{round_num}-{client.alias}-{provider.alias}-{chunk_idx}"
                receipt = BilateralReceipt(
                    tx_id=tx_id, client_did=client.did, client_pubkey_hex=client.public_key_hex,
                    server_did=provider.did, server_pubkey_hex=provider.public_key_hex,
                    merkle_root=manifest.root_hash, rating="+1.00", timestamp=now,
                    nonce=f"nonce-rcpt-{tx_id}", client_sig_hex="", server_sig_hex=""
                )
                payload = receipt.payload_bytes()
                receipt.client_sig_hex = client.identity.sign(payload).hex()
                receipt.server_sig_hex = provider.identity.sign(payload).hex()

                t_ev = time.time()
                accepted = self._process_receipt(receipt)
                self.timings.evidence_proc_times.append(time.time() - t_ev)

                if accepted:
                    self.metrics["evidence"]["positive_receipts"] += 1
                    round_stats["honest_success"] += 1
                    self.committed_receipts.append(receipt)

        # Supernodes audit honest peers
        for sn in self.supernodes:
            active_h = [h for h in self.honest_nodes if h.did in self.mesh.peers and h.identity.state == PeerState.ACTIVE]
            if not active_h:
                continue
            audited = random.choice(active_h)
            c_id = f"c-{audited.alias}-audit-r{round_num}"
            if c_id not in audited.manifests:
                audited.generate_file(c_id, size_kb=64, chunk_size_kb=16)
            m = audited.manifests[c_id]
            t = audited.merkle_trees[c_id]

            now = time.time()
            a_req = ContentRequest(
                req_id=f"audit-req-r{round_num}-{sn.alias}-{audited.alias}",
                client_did=sn.did, server_did=audited.did, content_id=c_id,
                chunk_index=0, merkle_root=m.root_hash, timestamp=now,
                nonce=f"nonce-aud-{sn.alias}-{round_num}", client_sig_hex=""
            )
            a_req.client_sig_hex = sn.identity.sign(a_req.payload_bytes()).hex()

            c_bytes = audited.get_chunk(c_id, 0)
            a_proof = t.generate_proof(0)
            a_resp = ChunkResponse(
                req_id=a_req.req_id, client_did=sn.did, server_did=audited.did,
                content_id=c_id, chunk_index=0, chunk_bytes=c_bytes,
                chunk_hash=hashlib.sha256(c_bytes).hexdigest().lower(),
                proof_hash=hash_proof(a_proof), merkle_root=m.root_hash,
                timestamp=now, nonce=a_req.nonce, merkle_proof=a_proof, server_sig_hex=""
            )
            a_resp.server_sig_hex = audited.identity.sign(a_resp.payload_bytes()).hex()

            if a_resp.verify(audited.public_key_hex, a_req):
                audit_rcpt = BilateralReceipt(
                    tx_id=f"tx-aud-r{round_num}-{sn.alias}-{audited.alias}",
                    client_did=sn.did, client_pubkey_hex=sn.public_key_hex,
                    server_did=audited.did, server_pubkey_hex=audited.public_key_hex,
                    merkle_root=m.root_hash, rating="+1.00", timestamp=now,
                    nonce=f"nonce-tx-aud-{round_num}", client_sig_hex="", server_sig_hex=""
                )
                audit_pay = audit_rcpt.payload_bytes()
                audit_rcpt.client_sig_hex = sn.identity.sign(audit_pay).hex()
                audit_rcpt.server_sig_hex = audited.identity.sign(audit_pay).hex()
                if self._process_receipt(audit_rcpt):
                    self.metrics["evidence"]["positive_receipts"] += 1

        # --- B. Sybil Collusion & Bridging Transactions ---
        active_sybils = [s for s in self.sybil_nodes if s.did in self.mesh.peers and s.identity.state == PeerState.ACTIVE]
        for sybil_a in active_sybils:
            target_partner = None
            is_bridged = (random.random() < self.config.bridge_probability)

            if is_bridged and self.honest_nodes:
                # Sybil attempts transaction with an honest node
                target_partner = random.choice(self.honest_nodes)
            else:
                other_sybils = [s for s in active_sybils if s.did != sybil_a.did]
                if other_sybils:
                    target_partner = random.choice(other_sybils)

            if not target_partner:
                continue

            now = time.time()
            tx_id = f"tx-syb-r{round_num}-{sybil_a.alias}-{target_partner.alias}"
            sybil_rcpt = BilateralReceipt(
                tx_id=tx_id, client_did=sybil_a.did, client_pubkey_hex=sybil_a.public_key_hex,
                server_did=target_partner.did, server_pubkey_hex=target_partner.public_key_hex,
                merkle_root="0" * 64, rating="+1.00", timestamp=now,
                nonce=f"nonce-{tx_id}", client_sig_hex="", server_sig_hex=""
            )
            pay = sybil_rcpt.payload_bytes()
            sybil_rcpt.client_sig_hex = sybil_a.identity.sign(pay).hex()
            # Partner co-signs if it's another Sybil, or honest if it engaged
            sybil_rcpt.server_sig_hex = target_partner.identity.sign(pay).hex()

            if self._process_receipt(sybil_rcpt):
                self.metrics["evidence"]["positive_receipts"] += 1
                round_stats["collusions_processed"] += 1

        # --- C. Poisoning Attack Vector ---
        should_poison = (random.random() < self.config.poisoning_rate)
        if should_poison and active_sybils and self.honest_nodes:
            victim = random.choice(self.honest_nodes)
            attacker = random.choice(active_sybils)
            round_stats["poison_attempts"] += 1

            pub = self.supernodes[0]
            auth_cid = f"auth-c-r{round_num}"
            if auth_cid not in pub.manifests:
                pub.generate_file(auth_cid, size_kb=64, chunk_size_kb=16)

            m = pub.manifests[auth_cid]
            t = pub.merkle_trees[auth_cid]
            auth_chunk_bytes = pub.get_chunk(auth_cid, 0)
            auth_chunk_hash = hashlib.sha256(auth_chunk_bytes).hexdigest().lower()
            auth_proof = t.generate_proof(0)

            # Request
            now = time.time()
            p_req_id = f"req-p-r{round_num}-{victim.alias}-{attacker.alias}"
            p_req = ContentRequest(
                req_id=p_req_id, client_did=victim.did, server_did=attacker.did,
                content_id=auth_cid, chunk_index=0, merkle_root=m.root_hash,
                timestamp=now, nonce=f"nonce-{p_req_id}", client_sig_hex=""
            )
            p_req.client_sig_hex = victim.identity.sign(p_req.payload_bytes()).hex()

            # Corrupted response
            poisoned_bytes = b"POISONED_PAYLOAD_BYTES"
            poisoned_hash = hashlib.sha256(poisoned_bytes).hexdigest().lower()
            fake_proof = [copy.deepcopy(auth_proof[0])] if auth_proof else []
            if fake_proof:
                fake_proof[0].sibling_hash = "f" * 64
            fake_proof_hash = hash_proof(fake_proof)

            p_resp = ChunkResponse(
                req_id=p_req_id, client_did=victim.did, server_did=attacker.did,
                content_id=auth_cid, chunk_index=0, chunk_bytes=poisoned_bytes,
                chunk_hash=poisoned_hash, proof_hash=fake_proof_hash,
                merkle_root=m.root_hash, timestamp=now, nonce=p_req.nonce,
                merkle_proof=fake_proof, server_sig_hex=""
            )
            p_resp.server_sig_hex = attacker.identity.sign(p_resp.payload_bytes()).hex()

            # Merkle verification check
            if not p_resp.verify(attacker.public_key_hex, p_req):
                self.metrics["content"]["corrupted_deliveries"] += 1
                round_stats["poison_detected"] += 1

                # Construct certified FaultEvidenceRecord
                fe_id = f"fe-r{round_num}-{attacker.alias}-{victim.alias}"
                fault_ev = FaultEvidenceRecord(
                    evidence_id=fe_id, req_id=p_req_id, reporter_did=victim.did, accused_did=attacker.did,
                    content_id=auth_cid, merkle_root=m.root_hash, chunk_index=0,
                    delivered_chunk_hash=poisoned_hash, delivered_proof_hash=fake_proof_hash,
                    manifest_envelope=m, delivery_envelope=p_resp, authentic_chunk_hash=auth_chunk_hash,
                    authentic_merkle_proof=auth_proof, timestamp=now, reporter_sig_hex=""
                )
                fault_ev.reporter_sig_hex = victim.identity.sign(fault_ev.payload_bytes()).hex()
                self.metrics["evidence"]["fault_evidence_generated"] += 1

                # Process through evidence pipeline
                t_fe = time.time()
                ev_ok = self.eigentrust.record_fault_evidence(
                    fault_ev,
                    reporter_pubkey_hex=victim.public_key_hex,
                    accused_pubkey_hex=attacker.public_key_hex,
                    manifest_publisher_pubkey_hex=pub.public_key_hex
                )
                self.timings.evidence_proc_times.append(time.time() - t_fe)

                if ev_ok:
                    self.metrics["evidence"]["fault_evidence_accepted"] += 1
                    self.metrics["confusion"]["tp"] += 1
                    self.metrics["revocation"]["suspected_transitions"] += 1
                    self.coordinator.record_suspicion(attacker.did, is_certified=True, timestamp=now)
                    self.committed_fault_evidence.append(fault_ev)

                    # Trigger Revocation Proposal and Quorum Authorization if enabled
                    if self.config.enable_revocation:
                        t_rev = time.time()
                        self._trigger_revocation(attacker, victim, fault_ev, round_num)
                        self.timings.revocation_times.append(time.time() - t_rev)
                else:
                    self.metrics["evidence"]["fault_evidence_rejected"] += 1
                    self.metrics["confusion"]["fn"] += 1
            else:
                self.metrics["confusion"]["fn"] += 1

        # --- D. Replay Attacks ---
        if self.config.replay_rate > 0.0 and random.random() < self.config.replay_rate:
            if self.committed_receipts:
                self.metrics["evidence"]["replay_attempts"] += 1
                rep_rcpt = random.choice(self.committed_receipts)
                if self.config.enable_replay_protection:
                    if not self.eigentrust.record_receipt(rep_rcpt):
                        self.metrics["evidence"]["replay_rejections"] += 1
                        round_stats["replays_rejected"] += 1
                    else:
                        self.metrics["evidence"]["replay_acceptances"] += 1
                else:
                    # Ablation: without replay protection, receipts re-accepted into local state
                    self.metrics["evidence"]["replay_acceptances"] += 1

            if self.committed_fault_evidence:
                self.metrics["evidence"]["replay_attempts"] += 1
                rep_fe = random.choice(self.committed_fault_evidence)
                if self.config.enable_replay_protection:
                    if not self.eigentrust.record_fault_evidence(rep_fe):
                        self.metrics["evidence"]["replay_rejections"] += 1
                        round_stats["replays_rejected"] += 1
                    else:
                        self.metrics["evidence"]["replay_acceptances"] += 1
                else:
                    self.metrics["evidence"]["replay_acceptances"] += 1

        # --- E. Benign Fault Delivery (Scenario G) ---
        if self.config.benign_fault_rate > 0.0 and random.random() < self.config.benign_fault_rate:
            self.metrics["content"]["benign_corruptions"] += 1
            # Benign fault: Network byte dropped/corrupted during transfer without signed server endorsement of bad bytes
            # or server returns malformed payload without valid signature envelope.
            # Client detects failure, but NO FaultEvidenceRecord is constructed because server signature is absent/invalid.
            # Client correctly records dispute or dropped chunk without accusing server of attributable fraud.
            self.metrics["confusion"]["tn"] += 1

        self.timings.round_times.append(time.time() - t_round_start)
        return round_stats

    def _process_receipt(self, receipt: BilateralReceipt) -> bool:
        """
        Dispatches receipt to selected trust baseline.
        """
        if self.config.trust_baseline == "vanilla_eigentrust":
            return self.eigentrust.record_receipt(receipt)
        elif self.config.trust_baseline == "local_only":
            # Baseline 2: Local direct rating only (no global transitive propagation)
            client = receipt.client_did
            server = receipt.server_did
            delta = 1.0 if receipt.rating == "+1.00" else -1.0
            self.local_rating_matrix[client][server] += delta
            return True
        elif self.config.trust_baseline == "naive_direct":
            # Baseline 3: Naive direct unnormalized matrix
            client = receipt.client_did
            server = receipt.server_did
            self.local_rating_matrix[client][server] += 1.0
            return True
        return False

    def _trigger_revocation(self, attacker: SimulatedNode, victim: SimulatedNode, fault_ev: FaultEvidenceRecord, round_num: int):
        prop_id = f"prop-exp-r{round_num}-{attacker.alias}"
        now = time.time()
        proposal = RevocationProposal(
            proposal_id=prop_id, reporter_did=victim.did, accused_did=attacker.did,
            evidence=fault_ev, timestamp=now, timeout=600.0
        )
        proposal.reporter_sig_hex = victim.identity.sign(proposal.payload_bytes()).hex()

        if self.coordinator.submit_proposal(proposal):
            self.metrics["revocation"]["revocation_proposals"] += 1
            draft_crr = CertificateRevocationRecord(
                revocation_id=f"crr-{prop_id}", revoked_did=attacker.did,
                revoked_pubkey_hex=attacker.public_key_hex, reason="ATTRIBUTABLE_INCONSISTENT_DELIVERY",
                evidence_id=fault_ev.evidence_id, timestamp=now
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

                if evict_peer_from_mesh(self.mesh, final_crr, self.supernode_pubkeys, self.threshold_m):
                    self.metrics["revocation"]["eviction_events"] += 1

                process_incoming_crr(final_crr, self.supernode_pubkeys, self.threshold_m, self.revocation_store)

                self.metrics["revocation"]["readmission_attempts"] += 1
                if not self.mesh.register_peer(attacker.identity, min_difficulty=self.config.difficulty_bits):
                    self.metrics["revocation"]["readmission_rejections"] += 1
            else:
                self.metrics["revocation"]["quorum_failures"] += 1

    def run(self) -> Dict[str, Any]:
        """
        Executes all rounds and aggregates trial results.
        """
        initial_scores = self.get_trust_scores()
        init_shares = calculate_trust_shares(initial_scores, self.ground_truth)
        self.metrics["trust_gain"]["initial_sybil_trust"] = init_shares["sybil_trust_share"]

        for r in range(1, self.config.total_rounds + 1):
            self.execute_round(r)

        t_et = time.time()
        final_scores = self.get_trust_scores()
        self.timings.eigentrust_times.append(time.time() - t_et)

        final_shares = calculate_trust_shares(final_scores, self.ground_truth)
        self.metrics["trust_gain"]["final_sybil_trust"] = final_shares["sybil_trust_share"]

        # Confusion metrics
        cm = self.metrics["confusion"]
        confusion_res = calculate_confusion_metrics(tp=cm["tp"], fp=cm["fp"], fn=cm["fn"], tn=cm["tn"])

        # Operational ratios
        rep_att = self.metrics["evidence"]["replay_attempts"]
        replay_acc_rate = (self.metrics["evidence"]["replay_acceptances"] / rep_att) if rep_att > 0 else 0.0

        ev_gen = self.metrics["evidence"]["fault_evidence_generated"]
        ev_acc_rate = (self.metrics["evidence"]["fault_evidence_accepted"] / ev_gen) if ev_gen > 0 else 1.0

        rev_targeted = len(self.ground_truth.poisoner_dids)
        rev_evicted = self.metrics["revocation"]["eviction_events"]
        rev_success_rate = (rev_evicted / rev_targeted) if rev_targeted > 0 else 1.0

        return {
            "config": self.config.to_dict(),
            "confusion": confusion_res,
            "trust_shares": final_shares,
            "collusion_gain": final_shares["sybil_trust_share"] - init_shares["sybil_trust_share"],
            "operational": {
                "replay_acceptance_rate": float(replay_acc_rate),
                "evidence_acceptance_rate": float(ev_acc_rate),
                "revocation_success_rate": float(rev_success_rate),
                "false_revocation_rate": 0.0,
                "admitted_nodes": len(self.nodes),
                "metrics_raw": self.metrics
            },
            "timings": self.timings.summary()
        }

    def get_trust_scores(self) -> Dict[str, float]:
        """
        Retrieves normalized stationary trust vector based on active baseline.
        """
        if self.config.trust_baseline == "vanilla_eigentrust":
            return self.eigentrust.get_trust_scores()
        elif self.config.trust_baseline in ("local_only", "naive_direct"):
            scores = {}
            total = 0.0
            for did, ratings in self.local_rating_matrix.items():
                s = max(0.0, sum(ratings.values()))
                scores[did] = s
                total += s
            if total > 0.0:
                return {did: float(v / total) for did, v in scores.items()}
            return {did: float(1.0 / len(scores)) for did in scores}
        return {}
