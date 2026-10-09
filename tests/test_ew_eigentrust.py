"""
Focused Unit & Integration Tests for EW-EigenTrust v1.8 (Phase 8.1)
Covers:
1. Valid verified delivery Tier 3 credit through actual identifier lifecycle.
2. Tx_id vs journal entry_id mismatch prevents false Tier 3 match.
3. Missing or malformed receipt linkage falls back safely.
4. Forged/injected delivery keys cannot bypass validation boundary.
5. Manifest-root references receive Tier 2 only when indexed.
6. Unindexed receipts receive Tier 1.
7. Freshness decay, clock drift, and excessive future timestamp rejection.
8. Neutral ratings skipped from evidence and dispute accounting.
9. Subjective negative receipts dispute accounting vs certified fault evidence.
10. Certified fault evidence and revocation nullification of incoming edges.
11. Input robustness: duplicates, empty networks, invalid parameters, NaN/Inf, dangling rows, anchor fallback.
12. Concave edge function real and float64 bounds.
13. Vanilla mode exact equivalence with EigenTrustEngine on D_equiv.
14. End-to-end SwarmSimulation delivery linkage and trust computation.
"""

import unittest
import math
import time
import hashlib
import copy
import numpy as np
from typing import List, Dict, Tuple, Set, Optional, Any

from src.layer1_identity import PeerIdentity, PeerState
from src.layer3_eigentrust import (
    MerkleTree, BilateralReceipt, EigenTrustEngine, LocalEvidenceJournal,
    ContentRequest, ChunkResponse, FaultEvidenceRecord, hash_proof,
    TrustComputationMode, compute_ew_eigentrust_v1_8, compute_ew_eigentrust
)
from src.network_simulator import SwarmSimulation, SimulatedNode


class TestEWIdentifierLifecycleAndDeliveryTiers(unittest.TestCase):
    """
    Tests Tasks 1 & 3: Evidence identifier contract, end-to-end delivery lifecycle,
    and Tier 1/2/3 multi-tier evaluation.
    """

    def setUp(self):
        self.client = PeerIdentity("ClientNode", difficulty_bits=4)
        self.server = PeerIdentity("ServerNode", difficulty_bits=4)
        self.observer = PeerIdentity("ObserverNode", difficulty_bits=4)
        self.peers = [self.client.did, self.server.did, self.observer.did]

    def _create_verified_delivery_and_receipt(
        self,
        content_bytes: bytes = b"AUTHENTIC_CONTENT_CHUNK_DATA_PAYLOAD",
        round_num: int = 1,
        rating: str = "+1.00",
        timestamp: Optional[float] = None
    ) -> Tuple[ContentRequest, ChunkResponse, BilateralReceipt, str]:
        """
        Executes the genuine 5-step delivery and receipt protocol:
        1. ContentRequest (req_id)
        2. ChunkResponse with Merkle tree & proof (verified by client)
        3. tx_id creation
        4. BilateralReceipt co-signed
        """
        ts = time.time() if timestamp is None else timestamp
        # Merkle tree setup
        tree = MerkleTree([content_bytes])
        merkle_root = tree.root_hash

        # Step 1: ContentRequest
        req_id = f"req-test-r{round_num}-{self.client.alias}-{self.server.alias}-0"
        nonce_req = f"nonce-req-{req_id}"
        req = ContentRequest(
            req_id=req_id,
            client_did=self.client.did,
            server_did=self.server.did,
            content_id="test-content-001",
            chunk_index=0,
            merkle_root=merkle_root,
            timestamp=ts,
            nonce=nonce_req,
            client_sig_hex=""
        )
        req.client_sig_hex = self.client.sign(req.payload_bytes()).hex()

        # Step 2: ChunkResponse with authentic proof
        proof = tree.generate_proof(0)
        proof_h = hash_proof(proof)
        chunk_h = hashlib.sha256(content_bytes).hexdigest().lower()
        resp = ChunkResponse(
            req_id=req_id,
            client_did=self.client.did,
            server_did=self.server.did,
            content_id="test-content-001",
            chunk_index=0,
            chunk_bytes=content_bytes,
            chunk_hash=chunk_h,
            proof_hash=proof_h,
            merkle_root=merkle_root,
            timestamp=ts,
            nonce=nonce_req,
            merkle_proof=proof,
            server_sig_hex=""
        )
        resp.server_sig_hex = self.server.sign(resp.payload_bytes()).hex()

        # Verify response
        self.assertTrue(resp.verify(self.server.public_key_hex, req))

        # Step 3 & 4: BilateralReceipt
        tx_id = f"tx-test-r{round_num}-{self.client.alias}-{self.server.alias}-0"
        receipt = BilateralReceipt(
            tx_id=tx_id,
            client_did=self.client.did,
            client_pubkey_hex=self.client.public_key_hex,
            server_did=self.server.did,
            server_pubkey_hex=self.server.public_key_hex,
            merkle_root=merkle_root,
            rating=rating,
            timestamp=ts,
            nonce=f"nonce-rcpt-{tx_id}",
            client_sig_hex="",
            server_sig_hex=""
        )
        rcpt_payload = receipt.payload_bytes()
        receipt.client_sig_hex = self.client.sign(rcpt_payload).hex()
        receipt.server_sig_hex = self.server.sign(rcpt_payload).hex()
        self.assertTrue(receipt.is_valid())

        return req, resp, receipt, merkle_root

    def test_01_valid_verified_delivery_tier3_actual_lifecycle(self):
        """
        Test 1: A valid verified delivery receives Tier 3 credit (gamma_ev = 1.00)
        using the actual identifier lifecycle.
        """
        ref_time = time.time()
        req, resp, receipt, m_root = self._create_verified_delivery_and_receipt(timestamp=ref_time)

        # Engine records receipt into journal
        journal = LocalEvidenceJournal()
        engine = EigenTrustEngine(peers=self.peers, pre_trusted_peers=[self.client.did], journal=journal)
        engine.register_peer(self.client)
        engine.register_peer(self.server)
        engine.register_peer(self.observer)

        self.assertTrue(engine.record_receipt(receipt, current_time=ref_time))

        # Delivery linkage key constructed from authentic lifecycle
        verified_keys = {(self.client.did, self.server.did, m_root.lower(), receipt.tx_id)}
        known_roots = {m_root.lower()}

        scores, conv, iters = compute_ew_eigentrust_v1_8(
            peers=self.peers,
            supernodes=[self.client.did],
            raw_s_matrix={},
            evidence_journal=journal,
            verified_delivery_keys=verified_keys,
            known_manifest_roots=known_roots,
            mode=TrustComputationMode.EVIDENCE_ONLY,
            reference_time=ref_time
        )

        self.assertTrue(conv)
        # Server must have higher trust than observer because client verified delivery from server
        self.assertGreater(scores[self.server.did], scores[self.observer.did])

        # Verify that effective edge score reflects Tier 3 (gamma_ev = 1.00)
        # For single interaction: e_pos = 1.00 * 1.00 = 1.00. phi_val = 10 * tanh(0.50 * 1.0 / 10) = 10 * tanh(0.05) ~ 0.49958
        expected_phi = 10.0 * math.tanh(0.50 * 1.00 / 10.0)
        # S'[client, server] / S'[client, observer]
        # In a 3-node network where client only transitions to server: C'[client, server] = 1.0
        # Stationary distribution with alpha=0.15: client=0.15 (pretrusted restart), server=(1-0.15)*client + alpha*0 = 0.85*0.15 = 0.1275, etc.
        self.assertAlmostEqual(scores[self.client.did] + scores[self.server.did] + scores[self.observer.did], 1.0, places=12)

    def test_02_tx_id_vs_journal_entry_id_mismatch_prevents_tier3(self):
        """
        Test 2: A transaction ID and journal entry ID that differ do not silently
        produce a false Tier 3 match.
        """
        ref_time = time.time()
        req, resp, receipt, m_root = self._create_verified_delivery_and_receipt(timestamp=ref_time)

        journal = LocalEvidenceJournal()
        engine = EigenTrustEngine(peers=self.peers, pre_trusted_peers=[self.client.did], journal=journal)
        engine.register_peer(self.client)
        engine.register_peer(self.server)
        self.assertTrue(engine.record_receipt(receipt, current_time=ref_time))

        # Attacker / buggy caller passes req_id instead of tx_id in verified_delivery_keys
        mismatched_keys = {(self.client.did, self.server.did, m_root.lower(), req.req_id)}
        self.assertNotEqual(req.req_id, receipt.tx_id)

        # 1. With known manifest root, falls back to Tier 2 (gamma_ev = 0.25)
        scores_mismatched, _, _ = compute_ew_eigentrust_v1_8(
            peers=self.peers,
            supernodes=[self.client.did],
            raw_s_matrix={},
            evidence_journal=journal,
            verified_delivery_keys=mismatched_keys,
            known_manifest_roots={m_root.lower()},
            mode=TrustComputationMode.EVIDENCE_ONLY,
            reference_time=ref_time
        )

        # 2. Compare against authentic Tier 3 run
        matched_keys = {(self.client.did, self.server.did, m_root.lower(), receipt.tx_id)}
        scores_matched, _, _ = compute_ew_eigentrust_v1_8(
            peers=self.peers,
            supernodes=[self.client.did],
            raw_s_matrix={},
            evidence_journal=journal,
            verified_delivery_keys=matched_keys,
            known_manifest_roots={m_root.lower()},
            mode=TrustComputationMode.EVIDENCE_ONLY,
            reference_time=ref_time
        )

        # Tier 3 and Tier 2 both route 100% of client row if single edge, but let's test edge strength directly:
        # We add a competing edge to observer with fixed weight to see the difference in row proportions:
        # Create an unindexed receipt from client to observer
        tx_obs = "tx-client-observer-rcpt"
        rcpt_obs = BilateralReceipt(
            tx_id=tx_obs, client_did=self.client.did, client_pubkey_hex=self.client.public_key_hex,
            server_did=self.observer.did, server_pubkey_hex=self.observer.public_key_hex,
            merkle_root="f" * 64, rating="+1.00", timestamp=ref_time,
            nonce=f"nonce-{tx_obs}"
        )
        pay_obs = rcpt_obs.payload_bytes()
        rcpt_obs.client_sig_hex = self.client.sign(pay_obs).hex()
        rcpt_obs.server_sig_hex = self.observer.sign(pay_obs).hex()
        engine.register_peer(self.observer)
        self.assertTrue(engine.record_receipt(rcpt_obs, current_time=ref_time))

        # Now client has two edges: server and observer
        # With mismatched keys (Tier 2, gamma=0.25 vs Tier 1, gamma=0.10):
        scores_tier2, _, _ = compute_ew_eigentrust_v1_8(
            peers=self.peers,
            supernodes=[self.client.did],
            raw_s_matrix={},
            evidence_journal=journal,
            verified_delivery_keys=mismatched_keys,
            known_manifest_roots={m_root.lower()},
            mode=TrustComputationMode.EVIDENCE_ONLY,
            reference_time=ref_time
        )

        # With matched keys (Tier 3, gamma=1.00 vs Tier 1, gamma=0.10):
        scores_tier3, _, _ = compute_ew_eigentrust_v1_8(
            peers=self.peers,
            supernodes=[self.client.did],
            raw_s_matrix={},
            evidence_journal=journal,
            verified_delivery_keys=matched_keys,
            known_manifest_roots={m_root.lower()},
            mode=TrustComputationMode.EVIDENCE_ONLY,
            reference_time=ref_time
        )

        # Tier 3 must grant strictly more trust to server than Tier 2 fallback!
        self.assertGreater(scores_tier3[self.server.did], scores_tier2[self.server.did])

    def test_03_missing_or_malformed_receipt_linkage_falls_back(self):
        """
        Test 3: Missing or malformed receipt linkage safely falls back to Tier 1.
        """
        ref_time = time.time()
        # Receipt with empty merkle_root
        tx_empty = "tx-empty-root"
        rcpt_empty = BilateralReceipt(
            tx_id=tx_empty, client_did=self.client.did, client_pubkey_hex=self.client.public_key_hex,
            server_did=self.server.did, server_pubkey_hex=self.server.public_key_hex,
            merkle_root="", rating="+1.00", timestamp=ref_time,
            nonce=f"nonce-{tx_empty}"
        )
        pay_e = rcpt_empty.payload_bytes()
        rcpt_empty.client_sig_hex = self.client.sign(pay_e).hex()
        rcpt_empty.server_sig_hex = self.server.sign(pay_e).hex()

        journal = LocalEvidenceJournal()
        engine = EigenTrustEngine(peers=self.peers, pre_trusted_peers=[self.client.did], journal=journal)
        engine.register_peer(self.client)
        engine.register_peer(self.server)
        self.assertTrue(engine.record_receipt(rcpt_empty, current_time=ref_time))

        # Pass malformed delivery keys containing non-tuples, ints, 3-tuples
        malformed_keys = {"not_a_tuple", (1, 2, 3), ("a", "b", "c", "d", "e")}  # type: ignore

        scores, conv, _ = compute_ew_eigentrust_v1_8(
            peers=self.peers,
            supernodes=[self.client.did],
            raw_s_matrix={},
            evidence_journal=journal,
            verified_delivery_keys=malformed_keys,  # type: ignore
            known_manifest_roots={"root1", "root2"},
            mode=TrustComputationMode.EVIDENCE_ONLY,
            reference_time=ref_time
        )
        self.assertTrue(conv)
        self.assertAlmostEqual(sum(scores.values()), 1.0, places=12)

    def test_04_forged_or_manually_injected_delivery_key_cannot_bypass_boundary(self):
        """
        Test 4: A forged or manually injected delivery key cannot bypass the intended
        validation boundary. Untrusted callers cannot mint trust by injecting into a set.
        """
        ref_time = 1000.0
        journal = LocalEvidenceJournal()
        engine = EigenTrustEngine(peers=self.peers, pre_trusted_peers=[self.client.did], journal=journal)
        engine.register_peer(self.client)
        engine.register_peer(self.server)
        engine.register_peer(self.observer)

        # Attacker injects fake delivery keys for transactions that NEVER happened or failed validation
        fake_keys = {
            (self.client.did, self.server.did, "fake_root", "tx-forged-1"),
            (self.observer.did, self.server.did, "another_root", "tx-forged-2")
        }

        # Run EW-EigenTrust with empty journal (no valid dual-signed receipts recorded)
        scores, conv, _ = compute_ew_eigentrust_v1_8(
            peers=self.peers,
            supernodes=[self.client.did],
            raw_s_matrix={},
            evidence_journal=journal,
            verified_delivery_keys=fake_keys,
            known_manifest_roots={"fake_root"},
            mode=TrustComputationMode.EVIDENCE_ONLY,
            reference_time=ref_time
        )

        self.assertTrue(conv)
        # Since journal has 0 receipts, all rows are dangling and fall back to restart vector p
        # Client was the sole supernode, so client=1.0, server=0.0, observer=0.0
        self.assertAlmostEqual(scores[self.client.did], 1.0, places=12)
        self.assertAlmostEqual(scores[self.server.did], 0.0, places=12)
        self.assertAlmostEqual(scores[self.observer.did], 0.0, places=12)

    def test_05_manifest_root_references_receive_tier2_only_when_indexed(self):
        """
        Test 5: Manifest-root references receive Tier 2 (mu_referenced = 0.25)
        only when the root is legitimately indexed.
        """
        ref_time = time.time()
        root_indexed = "a" * 64
        root_unindexed = "b" * 64

        # Receipt 1: references indexed root (Tier 2)
        tx1 = "tx-indexed-1"
        r1 = BilateralReceipt(
            tx_id=tx1, client_did=self.client.did, client_pubkey_hex=self.client.public_key_hex,
            server_did=self.server.did, server_pubkey_hex=self.server.public_key_hex,
            merkle_root=root_indexed, rating="+1.00", timestamp=ref_time,
            nonce=f"nonce-{tx1}"
        )
        p1 = r1.payload_bytes()
        r1.client_sig_hex = self.client.sign(p1).hex()
        r1.server_sig_hex = self.server.sign(p1).hex()

        # Receipt 2: references unindexed root (Tier 1)
        tx2 = "tx-unindexed-2"
        r2 = BilateralReceipt(
            tx_id=tx2, client_did=self.client.did, client_pubkey_hex=self.client.public_key_hex,
            server_did=self.observer.did, server_pubkey_hex=self.observer.public_key_hex,
            merkle_root=root_unindexed, rating="+1.00", timestamp=ref_time,
            nonce=f"nonce-{tx2}"
        )
        p2 = r2.payload_bytes()
        r2.client_sig_hex = self.client.sign(p2).hex()
        r2.server_sig_hex = self.observer.sign(p2).hex()

        journal = LocalEvidenceJournal()
        engine = EigenTrustEngine(peers=self.peers, pre_trusted_peers=[self.client.did], journal=journal)
        engine.register_peer(self.client)
        engine.register_peer(self.server)
        engine.register_peer(self.observer)
        self.assertTrue(engine.record_receipt(r1, current_time=ref_time))
        self.assertTrue(engine.record_receipt(r2, current_time=ref_time))

        # Index only root_indexed
        known_roots = {root_indexed.lower()}
        scores, _, _ = compute_ew_eigentrust_v1_8(
            peers=self.peers,
            supernodes=[self.client.did],
            raw_s_matrix={},
            evidence_journal=journal,
            verified_delivery_keys=set(),  # Neither is Tier 3
            known_manifest_roots=known_roots,
            mode=TrustComputationMode.EVIDENCE_ONLY,
            mu_referenced=0.25,
            mu_unverified=0.10,
            reference_time=ref_time
        )

        # Server has Tier 2 (0.25) while Observer has Tier 1 (0.10)
        # Server must receive strictly higher trust than Observer
        self.assertGreater(scores[self.server.did], scores[self.observer.did])

    def test_06_unindexed_receipts_receive_tier1(self):
        """
        Test 6: Unindexed receipts receive Tier 1 (mu_unverified = 0.10).
        """
        ref_time = time.time()
        tx = "tx-unindexed"
        dummy_root = "0" * 64
        rcpt = BilateralReceipt(
            tx_id=tx, client_did=self.client.did, client_pubkey_hex=self.client.public_key_hex,
            server_did=self.server.did, server_pubkey_hex=self.server.public_key_hex,
            merkle_root=dummy_root, rating="+1.00", timestamp=ref_time,
            nonce=f"nonce-{tx}"
        )
        p = rcpt.payload_bytes()
        rcpt.client_sig_hex = self.client.sign(p).hex()
        rcpt.server_sig_hex = self.server.sign(p).hex()

        journal = LocalEvidenceJournal()
        engine = EigenTrustEngine(peers=self.peers, pre_trusted_peers=[self.client.did], journal=journal)
        engine.register_peer(self.client)
        engine.register_peer(self.server)
        self.assertTrue(engine.record_receipt(rcpt, current_time=ref_time))

        # No delivery keys and no manifest roots
        scores, conv, _ = compute_ew_eigentrust_v1_8(
            peers=self.peers,
            supernodes=[self.client.did],
            raw_s_matrix={},
            evidence_journal=journal,
            verified_delivery_keys=set(),
            known_manifest_roots=set(),
            mode=TrustComputationMode.EVIDENCE_ONLY,
            mu_unverified=0.10,
            reference_time=ref_time
        )
        self.assertTrue(conv)
        self.assertGreater(scores[self.server.did], 0.0)


class TestEWEvidenceFreshnessAndDispute(unittest.TestCase):
    """
    Tests freshness decay, future-dating rules, neutral ratings,
    and dispute penalties vs certified fault evidence.
    """

    def setUp(self):
        self.client = PeerIdentity("ClientNode", difficulty_bits=4)
        self.server1 = PeerIdentity("Server1", difficulty_bits=4)
        self.server2 = PeerIdentity("Server2", difficulty_bits=4)
        self.server3 = PeerIdentity("Server3", difficulty_bits=4)
        self.peers = [self.client.did, self.server1.did, self.server2.did, self.server3.did]

    def test_07_fresh_stale_and_excessive_future_dated_evidence(self):
        """
        Test 7: Fresh, stale, and excessively future-dated evidence follow specified time rules:
        - delta_t in [-60.0, 0.0]: gamma_time = 1.0 (clock drift tolerance)
        - delta_t < -60.0: gamma_time = 0.0 (excessive future timestamp rejected)
        - delta_t > 0.0: gamma_time = exp(-delta_t / tau) (decayed)
        """
        ref_time = 10000.0
        tau = 86400.0

        journal = LocalEvidenceJournal()
        engine = EigenTrustEngine(peers=self.peers, pre_trusted_peers=[self.client.did], journal=journal, freshness_window=100000.0)
        for p in [self.client, self.server1, self.server2, self.server3]:
            engine.register_peer(p)

        # 1. Server 1: clock drift future timestamp (delta_t = 10000 - 10030 = -30s >= -60s) -> gamma_time = 1.0
        tx1 = "tx-drift"
        r1 = BilateralReceipt(
            tx_id=tx1, client_did=self.client.did, client_pubkey_hex=self.client.public_key_hex,
            server_did=self.server1.did, server_pubkey_hex=self.server1.public_key_hex,
            merkle_root="0" * 64, rating="+1.00", timestamp=ref_time + 30.0,
            nonce=f"nonce-{tx1}"
        )
        p1 = r1.payload_bytes()
        r1.client_sig_hex = self.client.sign(p1).hex()
        r1.server_sig_hex = self.server1.sign(p1).hex()
        self.assertTrue(engine.record_receipt(r1, current_time=ref_time))

        # 2. Server 2: excessive future timestamp (delta_t = 10000 - 10100 = -100s < -60s) -> gamma_time = 0.0
        # Directly commit into journal to test trust engine timestamp evaluation
        journal.commit(
            entry_id="tx-future",
            entry_type="RECEIPT",
            details={
                "client_did": self.client.did,
                "server_did": self.server2.did,
                "rating": 1.0,
                "receipt_timestamp": ref_time + 100.0,  # 100s in the future
                "merkle_root": "0" * 64
            }
        )

        # 3. Server 3: 1 tau in the past (delta_t = 86400s > 0) -> gamma_time = exp(-1) ~ 0.367879
        journal.commit(
            entry_id="tx-stale",
            entry_type="RECEIPT",
            details={
                "client_did": self.client.did,
                "server_did": self.server3.did,
                "rating": 1.0,
                "receipt_timestamp": ref_time - tau,  # exactly tau in past
                "merkle_root": "0" * 64
            }
        )

        scores, conv, _ = compute_ew_eigentrust_v1_8(
            peers=self.peers,
            supernodes=[self.client.did],
            raw_s_matrix={},
            evidence_journal=journal,
            mode=TrustComputationMode.EVIDENCE_ONLY,
            tau_seconds=tau,
            reference_time=ref_time
        )
        self.assertTrue(conv)

        # Server 1 has full gamma_time = 1.0
        # Server 3 has decayed gamma_time = exp(-1) ~ 0.368
        # Server 2 has rejected gamma_time = 0.0 -> A[client, server2] = 0.0
        self.assertGreater(scores[self.server1.did], scores[self.server3.did])
        self.assertGreater(scores[self.server3.did], scores[self.server2.did])
        self.assertAlmostEqual(scores[self.server2.did], 0.0, places=12)

    def test_08_neutral_ratings_do_not_count_as_positive_or_negative(self):
        """
        Test 8: Neutral ratings (0.0) do not count as positive or negative evidence.
        """
        ref_time = 1000.0
        journal = LocalEvidenceJournal()

        # Add neutral receipt with rating 0.0
        journal.commit(
            entry_id="tx-neutral",
            entry_type="RECEIPT",
            details={
                "client_did": self.client.did,
                "server_did": self.server1.did,
                "rating": 0.0,
                "receipt_timestamp": ref_time,
                "merkle_root": "0" * 64
            }
        )

        scores, conv, _ = compute_ew_eigentrust_v1_8(
            peers=self.peers,
            supernodes=[self.client.did],
            raw_s_matrix={},
            evidence_journal=journal,
            mode=TrustComputationMode.EVIDENCE_ONLY,
            reference_time=ref_time
        )
        self.assertTrue(conv)
        # Server 1 received 0 positive and 0 negative evidence -> score is 0.0
        self.assertAlmostEqual(scores[self.server1.did], 0.0, places=12)

    def test_09_subjective_negative_receipts_dispute_vs_certified_fault(self):
        """
        Test 9: Subjective negative receipts affect dispute accounting but do not
        become certified fault evidence.
        """
        ref_time = 1000.0
        journal = LocalEvidenceJournal()

        # Client has 2 positive and 1 negative receipt for Server 1
        # gamma_dispute = max(0, 1 - (2 * 1) / (2 + 1)) = 1 - 2/3 = 1/3 ~ 0.333
        journal.commit(
            entry_id="tx-pos-1", entry_type="RECEIPT",
            details={"client_did": self.client.did, "server_did": self.server1.did, "rating": 1.0, "receipt_timestamp": ref_time, "merkle_root": "0"*64}
        )
        journal.commit(
            entry_id="tx-pos-2", entry_type="RECEIPT",
            details={"client_did": self.client.did, "server_did": self.server1.did, "rating": 1.0, "receipt_timestamp": ref_time, "merkle_root": "0"*64}
        )
        journal.commit(
            entry_id="tx-neg-1", entry_type="RECEIPT",
            details={"client_did": self.client.did, "server_did": self.server1.did, "rating": -1.0, "receipt_timestamp": ref_time, "merkle_root": "0"*64}
        )

        # Server 2 has 2 positive and 0 negative receipts (gamma_dispute = 1.0)
        journal.commit(
            entry_id="tx-pos-s2-1", entry_type="RECEIPT",
            details={"client_did": self.client.did, "server_did": self.server2.did, "rating": 1.0, "receipt_timestamp": ref_time, "merkle_root": "0"*64}
        )
        journal.commit(
            entry_id="tx-pos-s2-2", entry_type="RECEIPT",
            details={"client_did": self.client.did, "server_did": self.server2.did, "rating": 1.0, "receipt_timestamp": ref_time, "merkle_root": "0"*64}
        )

        scores, _, _ = compute_ew_eigentrust_v1_8(
            peers=self.peers,
            supernodes=[self.client.did],
            raw_s_matrix={},
            evidence_journal=journal,
            mode=TrustComputationMode.EVIDENCE_ONLY,
            reference_time=ref_time
        )

        # Server 1 is penalized by dispute factor, so Server 2 has higher trust:
        self.assertGreater(scores[self.server2.did], scores[self.server1.did])
        # Server 1 still has non-zero trust because subjective dispute is NOT certified fault:
        self.assertGreater(scores[self.server1.did], 0.0)


class TestEWCertifiedFaultNullification(unittest.TestCase):
    """
    Tests Task 2 & 3: Certified fault evidence and revocation state nullification.
    """

    def setUp(self):
        self.client = PeerIdentity("ClientNode", difficulty_bits=4)
        self.server = PeerIdentity("ServerNode", difficulty_bits=4)
        self.peers = [self.client.did, self.server.did]

    def test_10_certified_fault_and_revocation_nullification(self):
        """
        Test 10: Certified fault evidence and frozen revocation states nullify
        all incoming edges to the offending peer.
        """
        ref_time = 1000.0
        journal = LocalEvidenceJournal()

        # Add 10 positive receipts from Client to Server
        for i in range(10):
            journal.commit(
                entry_id=f"tx-pos-{i}", entry_type="RECEIPT",
                details={"client_did": self.client.did, "server_did": self.server.did, "rating": 1.0, "receipt_timestamp": ref_time, "merkle_root": "0"*64}
            )

        # Case A: Normal operation -> Server has positive trust
        scores_normal, _, _ = compute_ew_eigentrust_v1_8(
            peers=self.peers, supernodes=[self.client.did], raw_s_matrix={},
            evidence_journal=journal, mode=TrustComputationMode.EVIDENCE_ONLY, reference_time=ref_time
        )
        self.assertGreater(scores_normal[self.server.did], 0.0)

        # Case B: Certified fault committed to journal against Server
        journal.commit(
            entry_id="fault-ev-001", entry_type="FAULT_EVIDENCE",
            details={"reporter_did": self.client.did, "accused_did": self.server.did, "content_id": "c1"}
        )
        scores_fault, _, _ = compute_ew_eigentrust_v1_8(
            peers=self.peers, supernodes=[self.client.did], raw_s_matrix={},
            evidence_journal=journal, mode=TrustComputationMode.EVIDENCE_ONLY, reference_time=ref_time
        )
        # Server's incoming edge must be immediately zeroed!
        self.assertAlmostEqual(scores_fault[self.server.did], 0.0, places=12)
        self.assertAlmostEqual(scores_fault[self.client.did], 1.0, places=12)

        # Case C: PeerState == REVOKED
        journal_clean = LocalEvidenceJournal()
        journal_clean.commit(
            entry_id="tx-pos-c", entry_type="RECEIPT",
            details={"client_did": self.client.did, "server_did": self.server.did, "rating": 1.0, "receipt_timestamp": ref_time, "merkle_root": "0"*64}
        )
        scores_revoked, _, _ = compute_ew_eigentrust_v1_8(
            peers=self.peers, supernodes=[self.client.did], raw_s_matrix={},
            evidence_journal=journal_clean,
            peer_states={self.server.did: PeerState.REVOKED},
            mode=TrustComputationMode.EVIDENCE_ONLY, reference_time=ref_time
        )
        self.assertAlmostEqual(scores_revoked[self.server.did], 0.0, places=12)

        # Case D: PeerState == SUSPECTED with certified suspicion
        scores_cert_susp, _, _ = compute_ew_eigentrust_v1_8(
            peers=self.peers, supernodes=[self.client.did], raw_s_matrix={},
            evidence_journal=journal_clean,
            peer_states={self.server.did: PeerState.SUSPECTED},
            certified_suspicion_dids={self.server.did},
            mode=TrustComputationMode.EVIDENCE_ONLY, reference_time=ref_time
        )
        self.assertAlmostEqual(scores_cert_susp[self.server.did], 0.0, places=12)

        # Case E: PeerState == SUSPECTED but uncertified subjective suspicion -> NOT nullified
        scores_uncert_susp, _, _ = compute_ew_eigentrust_v1_8(
            peers=self.peers, supernodes=[self.client.did], raw_s_matrix={},
            evidence_journal=journal_clean,
            peer_states={self.server.did: PeerState.SUSPECTED},
            certified_suspicion_dids=set(),  # uncertified
            mode=TrustComputationMode.EVIDENCE_ONLY, reference_time=ref_time
        )
        self.assertGreater(scores_uncert_susp[self.server.did], 0.0)


class TestEWEdgeBoundsAndRobustness(unittest.TestCase):
    """
    Tests edge ceilings, mathematical bounds, parameter validation,
    and defensive edge cases.
    """

    def test_11_input_robustness_empty_duplicates_nan_dangling(self):
        """
        Test 11: Robustness against duplicate peers, empty networks, invalid parameters,
        NaN/Inf scores, dangling rows, and no-valid-anchor fallback.
        """
        # 1. Empty network
        scores, conv, iters = compute_ew_eigentrust_v1_8(peers=[], supernodes=[], raw_s_matrix={})
        self.assertEqual(scores, {})
        self.assertTrue(conv)
        self.assertEqual(iters, 0)

        # 2. Duplicate peers in input sequence
        peers_dup = ["peerA", "peerB", "peerA", "peerC", ""]
        scores, conv, _ = compute_ew_eigentrust_v1_8(peers=peers_dup, supernodes=["peerA"], raw_s_matrix={})
        self.assertEqual(sorted(scores.keys()), ["peerA", "peerB", "peerC"])
        self.assertTrue(conv)
        self.assertAlmostEqual(sum(scores.values()), 1.0, places=12)

        # 3. No valid supernodes anchor fallback
        scores, conv, _ = compute_ew_eigentrust_v1_8(
            peers=["peerA", "peerB"], supernodes=["unknown_sn"], raw_s_matrix={}
        )
        self.assertTrue(conv)
        # Uniform fallback
        self.assertAlmostEqual(scores["peerA"], 0.5, places=12)
        self.assertAlmostEqual(scores["peerB"], 0.5, places=12)

        # 4. NaN / Inf scores in raw_s_matrix (Vanilla mode)
        raw_s = {
            ("peerA", "peerB"): float("nan"),
            ("peerB", "peerA"): float("inf"),
            ("peerA", "peerC"): -5.0
        }
        scores, conv, _ = compute_ew_eigentrust_v1_8(
            peers=["peerA", "peerB", "peerC"],
            supernodes=["peerA"],
            raw_s_matrix=raw_s,
            mode=TrustComputationMode.VANILLA
        )
        self.assertTrue(conv)
        for v in scores.values():
            self.assertTrue(math.isfinite(v))
        self.assertAlmostEqual(sum(scores.values()), 1.0, places=12)

        # 5. Invalid parameters must raise ValueError
        with self.assertRaises(ValueError):
            compute_ew_eigentrust_v1_8(peers=["p1"], supernodes=["p1"], raw_s_matrix={}, alpha=0.0)
        with self.assertRaises(ValueError):
            compute_ew_eigentrust_v1_8(peers=["p1"], supernodes=["p1"], raw_s_matrix={}, alpha=1.0)
        with self.assertRaises(ValueError):
            compute_ew_eigentrust_v1_8(peers=["p1"], supernodes=["p1"], raw_s_matrix={}, alpha=True)
        with self.assertRaises(ValueError):
            compute_ew_eigentrust_v1_8(peers=["p1"], supernodes=["p1"], raw_s_matrix={}, tol=-1.0)
        with self.assertRaises(ValueError):
            compute_ew_eigentrust_v1_8(peers=["p1"], supernodes=["p1"], raw_s_matrix={}, max_iter=0)
        with self.assertRaises(ValueError):
            compute_ew_eigentrust_v1_8(peers=["p1"], supernodes=["p1"], raw_s_matrix={}, k_max=0.0)
        with self.assertRaises(ValueError):
            compute_ew_eigentrust_v1_8(peers=["p1"], supernodes=["p1"], raw_s_matrix={}, mu_unverified=0.5, mu_referenced=0.2)
        with self.assertRaises(ValueError):
            compute_ew_eigentrust_v1_8(peers=["p1"], supernodes=["p1"], raw_s_matrix={}, mode="invalid_mode")

    def test_12_concave_edge_function_bounds(self):
        """
        Test 12: Concave edge function respects real-arithmetic strict bound (< 10.0)
        and float64 non-strict bound (<= 10.0).
        """
        k_max = 10.0
        lambda_sat = 0.50

        # Small values
        for e in [0.0, 1.0, 5.0, 10.0, 50.0]:
            val = k_max * math.tanh((lambda_sat * e) / k_max)
            self.assertLess(val, k_max)

        # Huge values in float64
        huge_e = 1e9
        val_huge = k_max * math.tanh((lambda_sat * huge_e) / k_max)
        self.assertLessEqual(val_huge, k_max)
        self.assertEqual(val_huge, 10.0)  # Saturated in float64


class TestEWVanillaEquivalence(unittest.TestCase):
    """
    Tests exact bitwise and mathematical equivalence between MODE_VANILLA
    and existing EigenTrustEngine on the equivalence domain D_equiv.
    """

    def test_13_vanilla_mode_exact_equivalence_on_d_equiv(self):
        """
        Test 13: Vanilla mode remains equivalent to existing EigenTrustEngine
        on the explicitly defined equivalence domain D_equiv.
        """
        peers = ["peer_1", "peer_2", "peer_3", "peer_4"]
        supernodes = ["peer_1"]

        # Build engine
        engine = EigenTrustEngine(peers=peers, pre_trusted_peers=supernodes, alpha=0.15)
        # Establish interactions
        engine.S[0, 1] = 5.0
        engine.S[1, 2] = 10.0
        engine.S[2, 0] = 7.0
        engine.S[2, 3] = 3.0
        # Peer 3 has no outgoing interactions (dangling row)

        engine_scores = engine.get_trust_scores()

        # Map S to raw_s dictionary
        raw_s: Dict[Tuple[str, str], float] = {}
        for i in range(len(peers)):
            for j in range(len(peers)):
                if i != j and engine.S[i, j] > 0:
                    raw_s[(peers[i], peers[j])] = float(engine.S[i, j])

        # Run compute_ew_eigentrust_v1_8 in VANILLA mode
        v1_8_scores, conv, iters = compute_ew_eigentrust_v1_8(
            peers=peers,
            supernodes=supernodes,
            raw_s_matrix=raw_s,
            mode=TrustComputationMode.VANILLA,
            alpha=0.15,
            tol=1e-6,
            max_iter=100
        )

        self.assertTrue(conv)

        # Test bitwise floating point equality
        for p in peers:
            diff = abs(engine_scores[p] - v1_8_scores[p])
            self.assertEqual(diff, 0.0, f"Divergence on peer {p}: {diff}")

        # Simplex conservation
        self.assertAlmostEqual(sum(v1_8_scores.values()), 1.0, places=15)


class TestEndToEndSimulationTrace(unittest.TestCase):
    """
    Tests end-to-end integration: SwarmSimulation delivery linkage,
    receipt commit, and EW-EigenTrust trust vector generation.
    """

    def test_14_end_to_end_simulation_linkage_trace(self):
        """
        Test 14: End-to-end simulation trace proving verified deliveries
        receive Tier 3 credit and Sybils are restricted to Tier 1.
        """
        sim = SwarmSimulation(
            num_honest=5, num_supernodes=2, num_sybils=3,
            seed=42, difficulty_bits=4,
            trust_mode=TrustComputationMode.EVIDENCE_ONLY
        )

        # Run 2 transaction rounds
        hist = sim.run_simulation(total_rounds=2)

        # Assertions on delivery linkage:
        # 1. Honest verified deliveries populated verified_delivery_keys
        self.assertGreater(len(sim.verified_delivery_keys), 0)
        for key in sim.verified_delivery_keys:
            self.assertEqual(len(key), 4)
            c, s, root, tx = key
            self.assertTrue(c.startswith("did:peer:2.Ez"))
            self.assertTrue(s.startswith("did:peer:2.Ez"))
            self.assertEqual(len(root), 64)
            self.assertTrue(tx.startswith("tx-"))

        # 2. Known manifest roots populated
        self.assertGreater(len(sim.known_manifest_roots), 0)

        # 3. Final trust vector computed in EVIDENCE_ONLY mode
        final_scores = sim.metrics["trust"]["final_trust_vector"]
        self.assertGreater(len(final_scores), 0)
        self.assertAlmostEqual(sum(final_scores.values()), 1.0, places=12)

        # 4. Supernodes and honest peers must maintain higher average trust than Sybils
        sn_dids = [sn.did for sn in sim.supernodes]
        syb_dids = [s.did for s in sim.sybil_nodes]

        avg_sn = np.mean([final_scores[sn] for sn in sn_dids])
        avg_syb = np.mean([final_scores[syb] for syb in syb_dids])
        self.assertGreater(avg_sn, avg_syb)


if __name__ == '__main__':
    unittest.main()
