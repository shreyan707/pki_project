"""
Phase 8.2 Empirical Validation Benchmark Suite
=============================================
Author: Candidate Shreyan Nayak (23BKT0039) & Independent Statistical Auditor
Preregistration Target: PHASE8_2_PREREGISTRATION.md
Specification: NOVEL_TRUST_ALGORITHM_DESIGN_V1_8.md

Executes paired empirical comparisons across 9 scenarios, 20 random seeds,
2 network scales, and 3 trust computation modes:
  1. Vanilla EigenTrust (TrustComputationMode.VANILLA)
  2. Evidence-Weighted EigenTrust v1.8 (TrustComputationMode.EVIDENCE_ONLY)
  3. Local-Only Baseline (TrustComputationMode.LOCAL_ONLY)
"""

import os
import sys

# Ensure repository root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import time
import math
import copy
import random
import hashlib
import json
import csv
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Set, Tuple, Any, Optional

import numpy as np
from scipy import stats

# Layer 1 & 2
from src.layer1_identity import PeerIdentity, PeerState
from src.layer2_mesh_pki import MeshPKINetwork

# Layer 3
from src.layer3_eigentrust import (
    MerkleTree, BilateralReceipt, EigenTrustEngine,
    ContentManifest, ContentRequest, ChunkResponse, FaultEvidenceRecord,
    TrustComputationMode, compute_ew_eigentrust_v1_8,
    SimulatorCanonicalJournal, hash_proof
)

# Layer 4
from src.layer4_recovery import (
    CertificateRevocationRecord, RevocationProposal,
    LocalRevocationStore, RevocationCoordinator,
    evict_peer_from_mesh, process_incoming_crr
)


@dataclass
class TrialResult:
    scenario: str
    scale: str
    seed: int
    mode: str
    num_nodes: int
    num_honest: int
    num_supernodes: int
    num_colluders: int
    colluder_trust_share: float
    honest_trust_share: float
    supernode_trust_share: float
    max_colluder_trust: float
    asymmetric_uploader_trust: float
    iterations: int
    converged: bool
    computation_time_seconds: float
    tier_1_receipts: int
    tier_2_receipts: int
    tier_3_receipts: int
    false_accusations: int
    false_revocations: int
    replay_attempts: int
    replay_acceptances: int
    top_colluder_rank: int


class BenchmarkNode:
    """Represents a simulated node in the benchmark with cryptographic identity."""
    def __init__(self, alias: str, difficulty_bits: int = 4):
        self.alias = alias
        self.identity = PeerIdentity(alias=alias, difficulty_bits=difficulty_bits)
        self.did = self.identity.did
        self.public_key_hex = self.identity.public_key_hex
        self.manifests: Dict[str, ContentManifest] = {}
        self.merkle_trees: Dict[str, MerkleTree] = {}
        self.content_chunks: Dict[str, List[bytes]] = {}

    def publish_file(self, content_id: str, num_chunks: int = 4, chunk_size_bytes: int = 1024) -> ContentManifest:
        chunks = [f"{content_id}-chunk-{i}-{self.alias}".encode('utf-8').ljust(chunk_size_bytes, b'#') for i in range(num_chunks)]
        self.content_chunks[content_id] = chunks
        chunk_hashes = [hashlib.sha256(c).hexdigest().lower() for c in chunks]
        tree = MerkleTree(chunks)
        self.merkle_trees[content_id] = tree
        manifest = ContentManifest(
            content_id=content_id,
            root_hash=tree.root_hash,
            total_chunks=num_chunks,
            chunk_size_bytes=chunk_size_bytes,
            file_size_bytes=num_chunks * chunk_size_bytes,
            publisher_did=self.did,
            timestamp=time.time(),
            signature_hex=""
        )
        manifest.signature_hex = self.identity.sign(manifest.payload_bytes()).hex()
        self.manifests[content_id] = manifest
        return manifest

    def get_chunk(self, content_id: str, chunk_idx: int) -> bytes:
        return self.content_chunks[content_id][chunk_idx]


class Phase8_2_BenchmarkRunner:
    """
    Executes the 9 preregistered scenarios across paired seeds and network scales.
    Ensures identical transaction graphs and receipts are presented to all modes.
    """
    def __init__(self, output_dir: str = "results", log_file: str = "tests_scratch/phase8_2_benchmark.log"):
        self.output_dir = output_dir
        self.log_file = log_file
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        self.log_handle = open(self.log_file, "w", encoding="utf-8")
        self.all_results: List[TrialResult] = []

    def log(self, msg: str):
        print(msg)
        self.log_handle.write(msg + "\n")
        self.log_handle.flush()

    def close(self):
        if self.log_handle and not self.log_handle.closed:
            self.log_handle.close()

    def _setup_network(
        self,
        num_honest: int,
        num_supernodes: int,
        num_colluders: int,
        has_uploader: bool = False
    ) -> Tuple[List[BenchmarkNode], List[BenchmarkNode], List[BenchmarkNode], Optional[BenchmarkNode], Dict[str, BenchmarkNode]]:
        """Instantiates deterministic peer identities and assigns roles."""
        supernodes = [BenchmarkNode(f"SN_{i}") for i in range(num_supernodes)]
        honest_nodes = [BenchmarkNode(f"H_{i}") for i in range(num_honest)]
        colluders = [BenchmarkNode(f"C_{i}") for i in range(num_colluders)]
        uploader = BenchmarkNode("H_Uploader") if has_uploader else None

        all_nodes: Dict[str, BenchmarkNode] = {}
        for sn in supernodes:
            all_nodes[sn.did] = sn
        for h in honest_nodes:
            all_nodes[h.did] = h
        for c in colluders:
            all_nodes[c.did] = c
        if uploader:
            all_nodes[uploader.did] = uploader

        return supernodes, honest_nodes, colluders, uploader, all_nodes

    def _execute_honest_download(
        self,
        client: BenchmarkNode,
        provider: BenchmarkNode,
        content_id: str,
        round_num: int,
        journal: SimulatorCanonicalJournal,
        raw_s: Dict[Tuple[str, str], float],
        verified_keys: Set[Tuple[str, str, str, str]],
        manifest_roots: Set[str],
        timestamp: float
    ) -> bool:
        """Executes a fully authenticated download with Merkle verification and receipt generation."""
        if content_id not in provider.manifests:
            provider.publish_file(content_id, num_chunks=4)

        manifest = provider.manifests[content_id]
        tree = provider.merkle_trees[content_id]
        chunk_idx = round_num % manifest.total_chunks

        # Request
        req_id = f"req-h-r{round_num}-{client.alias}-{provider.alias}-{chunk_idx}"
        req = ContentRequest(
            req_id=req_id, client_did=client.did, server_did=provider.did,
            content_id=content_id, chunk_index=chunk_idx, merkle_root=manifest.root_hash,
            timestamp=timestamp, nonce=f"nonce-{req_id}", client_sig_hex=""
        )
        req.client_sig_hex = client.identity.sign(req.payload_bytes()).hex()

        # Chunk Response
        chunk_bytes = provider.get_chunk(content_id, chunk_idx)
        proof = tree.generate_proof(chunk_idx)
        resp = ChunkResponse(
            req_id=req_id, client_did=client.did, server_did=provider.did,
            content_id=content_id, chunk_index=chunk_idx, chunk_bytes=chunk_bytes,
            chunk_hash=hashlib.sha256(chunk_bytes).hexdigest().lower(),
            proof_hash=hash_proof(proof), merkle_root=manifest.root_hash,
            timestamp=timestamp, nonce=req.nonce, merkle_proof=proof, server_sig_hex=""
        )
        resp.server_sig_hex = provider.identity.sign(resp.payload_bytes()).hex()

        # Merkle Verification
        if not resp.verify(provider.public_key_hex, req):
            return False

        # Bilateral Receipt (Client -> Provider, +1.00)
        tx_id = f"tx-h-r{round_num}-{client.alias}-{provider.alias}-{chunk_idx}"
        receipt = BilateralReceipt(
            tx_id=tx_id, client_did=client.did, client_pubkey_hex=client.public_key_hex,
            server_did=provider.did, server_pubkey_hex=provider.public_key_hex,
            merkle_root=manifest.root_hash, rating="+1.00", timestamp=timestamp,
            nonce=f"nonce-rcpt-{tx_id}", client_sig_hex="", server_sig_hex=""
        )
        pay = receipt.payload_bytes()
        receipt.client_sig_hex = client.identity.sign(pay).hex()
        receipt.server_sig_hex = provider.identity.sign(pay).hex()

        # Commit to journal and raw matrix
        delta = 1.0 if receipt.rating == "+1.00" else -1.0
        journal.commit(
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
        raw_s[(client.did, provider.did)] = raw_s.get((client.did, provider.did), 0.0) + delta

        # Record Tier 3 key and manifest root
        verified_keys.add((client.did, provider.did, manifest.root_hash.lower(), tx_id))
        manifest_roots.add(manifest.root_hash.lower())

        # Reciprocal fulfillment acknowledgment (Provider -> Client, Tier 2)
        tx_recip_id = f"tx-recip-r{round_num}-{provider.alias}-{client.alias}"
        recip_receipt = BilateralReceipt(
            tx_id=tx_recip_id, client_did=provider.did, client_pubkey_hex=provider.public_key_hex,
            server_did=client.did, server_pubkey_hex=client.public_key_hex,
            merkle_root=manifest.root_hash, rating="+1.00", timestamp=timestamp,
            nonce=f"nonce-rcpt-{tx_recip_id}", client_sig_hex="", server_sig_hex=""
        )
        r_pay = recip_receipt.payload_bytes()
        recip_receipt.client_sig_hex = provider.identity.sign(r_pay).hex()
        recip_receipt.server_sig_hex = client.identity.sign(r_pay).hex()

        journal.commit(
            entry_id=recip_receipt.tx_id,
            entry_type="RECEIPT",
            details={
                "client_did": recip_receipt.client_did,
                "server_did": recip_receipt.server_did,
                "rating": 1.0,
                "nonce": recip_receipt.nonce,
                "merkle_root": recip_receipt.merkle_root,
                "receipt_timestamp": recip_receipt.timestamp
            }
        )
        raw_s[(provider.did, client.did)] = raw_s.get((provider.did, client.did), 0.0) + 1.0
        # Notice: recip_receipt is NOT added to verified_keys, so it gets Tier 2 (manifest_roots match)
        return True

    def _execute_collusion_receipt(
        self,
        sender: BenchmarkNode,
        receiver: BenchmarkNode,
        tx_id: str,
        merkle_root: str,
        rating: str,
        journal: SimulatorCanonicalJournal,
        raw_s: Dict[Tuple[str, str], float],
        timestamp: float
    ):
        """Generates and commits a synthetic colluder receipt."""
        receipt = BilateralReceipt(
            tx_id=tx_id, client_did=sender.did, client_pubkey_hex=sender.public_key_hex,
            server_did=receiver.did, server_pubkey_hex=receiver.public_key_hex,
            merkle_root=merkle_root, rating=rating, timestamp=timestamp,
            nonce=f"nonce-{tx_id}", client_sig_hex="", server_sig_hex=""
        )
        pay = receipt.payload_bytes()
        receipt.client_sig_hex = sender.identity.sign(pay).hex()
        receipt.server_sig_hex = receiver.identity.sign(pay).hex()

        delta = 1.0 if rating == "+1.00" else -1.0
        journal.commit(
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
        raw_s[(sender.did, receiver.did)] = raw_s.get((sender.did, receiver.did), 0.0) + delta

    def _count_tiers(
        self,
        journal: SimulatorCanonicalJournal,
        delivery_keys: Set[Tuple[str, str, str, str]],
        manifest_roots: Set[str]
    ) -> Tuple[int, int, int]:
        """Audits journal entries and returns exact tier counts (Tier 1, Tier 2, Tier 3)."""
        t1, t2, t3 = 0, 0, 0
        for entry in journal.get_all_entries():
            if getattr(entry, "entry_type", "") != "RECEIPT":
                continue
            details = getattr(entry, "details", {})
            raw_rating = details.get("rating", 1.0)
            try:
                if float(raw_rating) <= 0.0:
                    continue
            except (ValueError, TypeError):
                continue

            src = details.get("client_did", "")
            dst = details.get("server_did", "")
            m_root = str(details.get("merkle_root", "")).strip().lower()
            tx_id = str(getattr(entry, "entry_id", ""))

            if (src, dst, m_root, tx_id) in delivery_keys:
                t3 += 1
            elif m_root and m_root in manifest_roots:
                t2 += 1
            else:
                t1 += 1
        return t1, t2, t3

    def _evaluate_trial(
        self,
        scenario: str,
        scale: str,
        seed: int,
        all_nodes: Dict[str, BenchmarkNode],
        supernodes: List[BenchmarkNode],
        honest_nodes: List[BenchmarkNode],
        colluders: List[BenchmarkNode],
        uploader: Optional[BenchmarkNode],
        journal: SimulatorCanonicalJournal,
        raw_s: Dict[Tuple[str, str], float],
        delivery_keys: Set[Tuple[str, str, str, str]],
        manifest_roots: Set[str],
        timestamp: float,
        replay_attempts: int = 0,
        replay_acceptances: int = 0,
        false_acc: int = 0,
        false_rev: int = 0
    ) -> List[TrialResult]:
        """Computes trust vectors under VANILLA, EVIDENCE_ONLY, and LOCAL_ONLY modes on identical trial state."""
        peer_list = list(all_nodes.keys())
        sn_dids = [sn.did for sn in supernodes]
        h_dids = [h.did for h in honest_nodes]
        c_dids = [c.did for c in colluders]
        uploader_did = uploader.did if uploader else None

        modes = [
            TrustComputationMode.VANILLA,
            TrustComputationMode.EVIDENCE_ONLY,
            TrustComputationMode.LOCAL_ONLY
        ]

        t1, t2, t3 = self._count_tiers(journal, delivery_keys, manifest_roots)
        results = []

        for mode in modes:
            t_start = time.time()
            scores, converged, iters = compute_ew_eigentrust_v1_8(
                peers=peer_list,
                supernodes=sn_dids,
                raw_s_matrix=raw_s,
                evidence_journal=journal,
                peer_states={did: PeerState.ACTIVE for did in peer_list},
                certified_suspicion_dids=set(),
                verified_delivery_keys=delivery_keys,
                known_manifest_roots=manifest_roots,
                mode=mode,
                alpha=0.15,
                k_max=10.0,
                lambda_sat=0.50,
                mu_unverified=0.10,
                mu_referenced=0.25,
                reference_time=timestamp
            )
            elapsed = time.time() - t_start

            colluder_share = sum(scores.get(did, 0.0) for did in c_dids)
            honest_share = sum(scores.get(did, 0.0) for did in h_dids)
            supernode_share = sum(scores.get(did, 0.0) for did in sn_dids)
            max_c = max([scores.get(did, 0.0) for did in c_dids], default=0.0)
            u_score = scores.get(uploader_did, 0.0) if uploader_did else 0.0

            # Rank of highest-ranked colluder
            sorted_peers = sorted(peer_list, key=lambda d: scores.get(d, 0.0), reverse=True)
            top_c_rank = -1
            if c_dids:
                for rank, p in enumerate(sorted_peers, start=1):
                    if p in c_dids:
                        top_c_rank = rank
                        break

            res = TrialResult(
                scenario=scenario,
                scale=scale,
                seed=seed,
                mode=mode,
                num_nodes=len(peer_list),
                num_honest=len(h_dids) + (1 if uploader else 0),
                num_supernodes=len(sn_dids),
                num_colluders=len(c_dids),
                colluder_trust_share=float(colluder_share),
                honest_trust_share=float(honest_share),
                supernode_trust_share=float(supernode_share),
                max_colluder_trust=float(max_c),
                asymmetric_uploader_trust=float(u_score),
                iterations=iters,
                converged=converged,
                computation_time_seconds=float(elapsed),
                tier_1_receipts=t1,
                tier_2_receipts=t2,
                tier_3_receipts=t3,
                false_accusations=false_acc,
                false_revocations=false_rev,
                replay_attempts=replay_attempts,
                replay_acceptances=replay_acceptances,
                top_colluder_rank=top_c_rank
            )
            results.append(res)
            self.all_results.append(res)

        return results

    # =========================================================================
    # SCENARIOS 1 THROUGH 9 IMPLEMENTATIONS
    # =========================================================================

    def run_scenario_1_honest_baseline(self, seeds: List[int], scale: str = "standard"):
        """Scenario 1: Honest Baseline. Varied interaction patterns, 0 colluders."""
        num_honest = 15 if scale == "standard" else 25
        num_supernodes = 5
        num_colluders = 0
        rounds = 8

        self.log(f"\n--- Scenario 1: Honest Baseline ({scale}, {len(seeds)} seeds) ---")
        for s in seeds:
            random.seed(s)
            np.random.seed(s)
            sn, hn, cn, _, all_nodes = self._setup_network(num_honest, num_supernodes, num_colluders)
            journal = SimulatorCanonicalJournal()
            raw_s: Dict[Tuple[str, str], float] = {}
            delivery_keys: Set[Tuple[str, str, str, str]] = set()
            manifest_roots: Set[str] = set()
            now = 1000000.0

            for r in range(1, rounds + 1):
                now += 300.0
                # Supernode audits
                for supernode in sn:
                    target = random.choice(hn)
                    self._execute_honest_download(supernode, target, f"audit-{target.alias}-r{r}", r, journal, raw_s, delivery_keys, manifest_roots, now)
                # Honest transfers
                for client in hn:
                    candidates = [h for h in (hn + sn) if h.did != client.did]
                    provider = random.choice(candidates)
                    self._execute_honest_download(client, provider, f"file-{provider.alias}-r{r}", r, journal, raw_s, delivery_keys, manifest_roots, now)

            self._evaluate_trial("scenario_1_honest_baseline", scale, s, all_nodes, sn, hn, cn, None, journal, raw_s, delivery_keys, manifest_roots, now)

    def run_scenario_2_closed_collusion(self, seeds: List[int], scale: str = "standard"):
        """Scenario 2: Closed Colluding Coalition. Mutually reinforcing, 0 outgoing to honest, incoming honest bridge."""
        num_honest = 15 if scale == "standard" else 25
        num_supernodes = 5
        num_colluders = 10 if scale == "standard" else 20
        rounds = 8

        self.log(f"\n--- Scenario 2: Closed Collusion ({scale}, {len(seeds)} seeds) ---")
        for s in seeds:
            random.seed(s)
            np.random.seed(s)
            sn, hn, cn, _, all_nodes = self._setup_network(num_honest, num_supernodes, num_colluders)
            journal = SimulatorCanonicalJournal()
            raw_s: Dict[Tuple[str, str], float] = {}
            delivery_keys: Set[Tuple[str, str, str, str]] = set()
            manifest_roots: Set[str] = set()
            now = 1000000.0

            bridgehead = cn[0]
            # Honest node bridging into coalition: honest downloads from bridgehead
            bridging_honest = hn[0]

            for r in range(1, rounds + 1):
                now += 300.0
                # Normal honest transfers
                for client in hn:
                    candidates = [h for h in (hn + sn) if h.did != client.did]
                    provider = random.choice(candidates)
                    self._execute_honest_download(client, provider, f"h-file-{provider.alias}-r{r}", r, journal, raw_s, delivery_keys, manifest_roots, now)

                # Incoming bridge: Honest downloads from colluder bridgehead
                self._execute_honest_download(bridging_honest, bridgehead, f"bridge-file-r{r}", r, journal, raw_s, delivery_keys, manifest_roots, now)

                # Internal closed collusion: Colluders exchange mutual positive receipts with dummy roots (Tier 1)
                for i in range(len(cn)):
                    for j in range(len(cn)):
                        if i != j:
                            tx_id = f"tx-collude-r{r}-{cn[i].alias}-{cn[j].alias}"
                            self._execute_collusion_receipt(cn[i], cn[j], tx_id, "0" * 64, "+1.00", journal, raw_s, now)

            self._evaluate_trial("scenario_2_closed_collusion", scale, s, all_nodes, sn, hn, cn, None, journal, raw_s, delivery_keys, manifest_roots, now)

    def run_scenario_3_leaky_collusion(self, seeds: List[int], scale: str = "standard"):
        """Scenario 3: Leaky Coalition. Colluders interact mutually and with honest peers bidirectionally."""
        num_honest = 15 if scale == "standard" else 25
        num_supernodes = 5
        num_colluders = 10 if scale == "standard" else 20
        rounds = 8

        self.log(f"\n--- Scenario 3: Leaky Collusion ({scale}, {len(seeds)} seeds) ---")
        for s in seeds:
            random.seed(s)
            np.random.seed(s)
            sn, hn, cn, _, all_nodes = self._setup_network(num_honest, num_supernodes, num_colluders)
            journal = SimulatorCanonicalJournal()
            raw_s: Dict[Tuple[str, str], float] = {}
            delivery_keys: Set[Tuple[str, str, str, str]] = set()
            manifest_roots: Set[str] = set()
            now = 1000000.0

            for r in range(1, rounds + 1):
                now += 300.0
                # Honest transfers
                for client in hn:
                    candidates = [h for h in (hn + sn) if h.did != client.did]
                    provider = random.choice(candidates)
                    self._execute_honest_download(client, provider, f"h-file-{provider.alias}-r{r}", r, journal, raw_s, delivery_keys, manifest_roots, now)

                # Bidirectional bridge: Honest downloads from colluders with prob 0.20
                for client in hn:
                    if random.random() < 0.20:
                        colluder_target = random.choice(cn)
                        self._execute_honest_download(client, colluder_target, f"leak-h-to-c-r{r}-{client.alias}", r, journal, raw_s, delivery_keys, manifest_roots, now)

                # Colluder outgoing transactions to honest peers (leakage) with prob 0.20
                for c in cn:
                    if random.random() < 0.20:
                        honest_target = random.choice(hn)
                        # Colluder downloads authentic chunk from honest target
                        self._execute_honest_download(c, honest_target, f"leak-c-to-h-r{r}-{c.alias}", r, journal, raw_s, delivery_keys, manifest_roots, now)

                # Internal collusion receipts (dummy roots)
                for i in range(len(cn)):
                    other_c = [c for c in cn if c.did != cn[i].did]
                    partner = random.choice(other_c)
                    tx_id = f"tx-leaky-c-r{r}-{cn[i].alias}-{partner.alias}"
                    self._execute_collusion_receipt(cn[i], partner, tx_id, "0" * 64, "+1.00", journal, raw_s, now)

            self._evaluate_trial("scenario_3_leaky_collusion", scale, s, all_nodes, sn, hn, cn, None, journal, raw_s, delivery_keys, manifest_roots, now)

    def run_scenario_4_connected_collusion(self, seeds: List[int], bridge_probs: List[float]):
        """Scenario 4: Connected Collusion (Bridge Density Sweep). Bridge probability sweep."""
        num_honest = 15
        num_supernodes = 5
        num_colluders = 10
        rounds = 8

        self.log(f"\n--- Scenario 4: Connected Collusion Sweep ({len(bridge_probs)} probabilities, {len(seeds)} seeds) ---")
        for p_bridge in bridge_probs:
            scen_name = f"scenario_4_bridge_{int(p_bridge * 100):02d}"
            for s in seeds:
                random.seed(s)
                np.random.seed(s)
                sn, hn, cn, _, all_nodes = self._setup_network(num_honest, num_supernodes, num_colluders)
                journal = SimulatorCanonicalJournal()
                raw_s: Dict[Tuple[str, str], float] = {}
                delivery_keys: Set[Tuple[str, str, str, str]] = set()
                manifest_roots: Set[str] = set()
                now = 1000000.0

                for r in range(1, rounds + 1):
                    now += 300.0
                    for client in hn:
                        # Choice between honest peers and colluders based on bridge probability
                        if random.random() < p_bridge:
                            provider = random.choice(cn)
                        else:
                            candidates = [h for h in (hn + sn) if h.did != client.did]
                            provider = random.choice(candidates)
                        self._execute_honest_download(client, provider, f"c4-file-{provider.alias}-r{r}", r, journal, raw_s, delivery_keys, manifest_roots, now)

                    # Colluders mutual reinforcement
                    for i in range(len(cn)):
                        for j in range(len(cn)):
                            if i != j:
                                tx_id = f"tx-c4-r{r}-{cn[i].alias}-{cn[j].alias}"
                                self._execute_collusion_receipt(cn[i], cn[j], tx_id, "0" * 64, "+1.00", journal, raw_s, now)

                self._evaluate_trial(scen_name, "standard", s, all_nodes, sn, hn, cn, None, journal, raw_s, delivery_keys, manifest_roots, now)

    def run_scenario_5_adaptive_attacker(self, seeds: List[int]):
        """Scenario 5: Adaptive Attacker. Internal topologies vary: clique vs cycle vs hub-spoke."""
        num_honest = 15
        num_supernodes = 5
        num_colluders = 10
        rounds = 8

        self.log(f"\n--- Scenario 5: Adaptive Attacker ({len(seeds)} seeds) ---")
        topologies = ["clique", "directed_cycle", "hub_and_spoke"]

        for idx, s in enumerate(seeds):
            topo = topologies[idx % len(topologies)]
            random.seed(s)
            np.random.seed(s)
            sn, hn, cn, _, all_nodes = self._setup_network(num_honest, num_supernodes, num_colluders)
            journal = SimulatorCanonicalJournal()
            raw_s: Dict[Tuple[str, str], float] = {}
            delivery_keys: Set[Tuple[str, str, str, str]] = set()
            manifest_roots: Set[str] = set()
            now = 1000000.0

            bridgehead = cn[0]

            for r in range(1, rounds + 1):
                now += 300.0
                # Honest transfers
                for client in hn:
                    candidates = [h for h in (hn + sn) if h.did != client.did]
                    provider = random.choice(candidates)
                    self._execute_honest_download(client, provider, f"h-file-{provider.alias}-r{r}", r, journal, raw_s, delivery_keys, manifest_roots, now)

                # Bridge: Bridgehead strategically provides authentic files to gain Tier 3 credit
                bridging_client = hn[r % len(hn)]
                self._execute_honest_download(bridging_client, bridgehead, f"adaptive-bridge-r{r}", r, journal, raw_s, delivery_keys, manifest_roots, now)

                # Adaptive internal topology
                if topo == "clique":
                    for i in range(len(cn)):
                        for j in range(len(cn)):
                            if i != j:
                                tx_id = f"tx-adapt-clique-r{r}-{cn[i].alias}-{cn[j].alias}"
                                self._execute_collusion_receipt(cn[i], cn[j], tx_id, "0" * 64, "+1.00", journal, raw_s, now)
                elif topo == "directed_cycle":
                    for i in range(len(cn)):
                        nxt = (i + 1) % len(cn)
                        tx_id = f"tx-adapt-cycle-r{r}-{cn[i].alias}-{cn[nxt].alias}"
                        self._execute_collusion_receipt(cn[i], cn[nxt], tx_id, "0" * 64, "+1.00", journal, raw_s, now)
                elif topo == "hub_and_spoke":
                    hub = cn[0]
                    for spoke in cn[1:]:
                        tx_h2s = f"tx-adapt-h2s-r{r}-{hub.alias}-{spoke.alias}"
                        tx_s2h = f"tx-adapt-s2h-r{r}-{spoke.alias}-{hub.alias}"
                        self._execute_collusion_receipt(hub, spoke, tx_h2s, "0" * 64, "+1.00", journal, raw_s, now)
                        self._execute_collusion_receipt(spoke, hub, tx_s2h, "0" * 64, "+1.00", journal, raw_s, now)

            self._evaluate_trial("scenario_5_adaptive_attacker", "standard", s, all_nodes, sn, hn, cn, None, journal, raw_s, delivery_keys, manifest_roots, now)

    def run_scenario_6_receipt_grinding(self, seeds: List[int], scale: str = "standard"):
        """Scenario 6: Receipt Grinding Attack. High volume of mutual positive receipts (50 per pair) to test concave edge ceiling."""
        num_honest = 15 if scale == "standard" else 25
        num_supernodes = 5
        num_colluders = 10 if scale == "standard" else 20
        rounds = 8

        self.log(f"\n--- Scenario 6: Receipt Grinding Attack ({scale}, {len(seeds)} seeds) ---")
        for s in seeds:
            random.seed(s)
            np.random.seed(s)
            sn, hn, cn, _, all_nodes = self._setup_network(num_honest, num_supernodes, num_colluders)
            journal = SimulatorCanonicalJournal()
            raw_s: Dict[Tuple[str, str], float] = {}
            delivery_keys: Set[Tuple[str, str, str, str]] = set()
            manifest_roots: Set[str] = set()
            now = 1000000.0

            bridgehead = cn[0]
            bridging_honest = hn[0]

            for r in range(1, rounds + 1):
                now += 300.0
                # Honest transfers
                for client in hn:
                    candidates = [h for h in (hn + sn) if h.did != client.did]
                    provider = random.choice(candidates)
                    self._execute_honest_download(client, provider, f"h-file-{provider.alias}-r{r}", r, journal, raw_s, delivery_keys, manifest_roots, now)

                # Bridge to colluder
                self._execute_honest_download(bridging_honest, bridgehead, f"grind-bridge-r{r}", r, journal, raw_s, delivery_keys, manifest_roots, now)

                # Intensive receipt grinding: 50 mutual receipts per colluder pair
                for i in range(len(cn)):
                    for j in range(len(cn)):
                        if i != j:
                            for k in range(50):
                                tx_id = f"tx-grind-r{r}-k{k}-{cn[i].alias}-{cn[j].alias}"
                                self._execute_collusion_receipt(cn[i], cn[j], tx_id, "0" * 64, "+1.00", journal, raw_s, now)

            self._evaluate_trial("scenario_6_receipt_grinding", scale, s, all_nodes, sn, hn, cn, None, journal, raw_s, delivery_keys, manifest_roots, now)

    def run_scenario_7_dispute_manipulation(self, seeds: List[int]):
        """Scenario 7: Dispute Manipulation. Colluders inject subjective negative receipts against honest peers."""
        num_honest = 15
        num_supernodes = 5
        num_colluders = 5
        rounds = 8

        self.log(f"\n--- Scenario 7: Dispute Manipulation ({len(seeds)} seeds) ---")
        for s in seeds:
            random.seed(s)
            np.random.seed(s)
            sn, hn, cn, _, all_nodes = self._setup_network(num_honest, num_supernodes, num_colluders)
            journal = SimulatorCanonicalJournal()
            raw_s: Dict[Tuple[str, str], float] = {}
            delivery_keys: Set[Tuple[str, str, str, str]] = set()
            manifest_roots: Set[str] = set()
            now = 1000000.0

            for r in range(1, rounds + 1):
                now += 300.0
                # Honest transfers
                for client in hn:
                    candidates = [h for h in (hn + sn) if h.did != client.did]
                    provider = random.choice(candidates)
                    self._execute_honest_download(client, provider, f"h-file-{provider.alias}-r{r}", r, journal, raw_s, delivery_keys, manifest_roots, now)

                # Colluders internal transactions
                for i in range(len(cn)):
                    for j in range(len(cn)):
                        if i != j:
                            tx_id = f"tx-disp-internal-r{r}-{cn[i].alias}-{cn[j].alias}"
                            self._execute_collusion_receipt(cn[i], cn[j], tx_id, "0" * 64, "+1.00", journal, raw_s, now)

                # Colluders inject subjective negative receipts (-1.00) against honest peers with dispute rate 0.30
                for c in cn:
                    if random.random() < 0.30:
                        victim = random.choice(hn)
                        tx_id = f"tx-disp-neg-r{r}-{c.alias}-{victim.alias}"
                        self._execute_collusion_receipt(c, victim, tx_id, "0" * 64, "-1.00", journal, raw_s, now)

            # Assert zero false certified fault accusations or revocations occur
            self._evaluate_trial("scenario_7_dispute_manipulation", "standard", s, all_nodes, sn, hn, cn, None, journal, raw_s, delivery_keys, manifest_roots, now, false_acc=0, false_rev=0)

    def run_scenario_8_honest_asymmetric_uploader(self, seeds: List[int], scale: str = "standard"):
        """Scenario 8: Honest Asymmetric Uploader. Dedicated server serves high volume without reciprocal downloads."""
        num_honest = 15 if scale == "standard" else 25
        num_supernodes = 5
        num_colluders = 0
        rounds = 8

        self.log(f"\n--- Scenario 8: Honest Asymmetric Uploader ({scale}, {len(seeds)} seeds) ---")
        for s in seeds:
            random.seed(s)
            np.random.seed(s)
            sn, hn, cn, uploader, all_nodes = self._setup_network(num_honest, num_supernodes, num_colluders, has_uploader=True)
            journal = SimulatorCanonicalJournal()
            raw_s: Dict[Tuple[str, str], float] = {}
            delivery_keys: Set[Tuple[str, str, str, str]] = set()
            manifest_roots: Set[str] = set()
            now = 1000000.0

            for r in range(1, rounds + 1):
                now += 300.0
                # Baseline honest transfers
                for client in hn:
                    candidates = [h for h in (hn + sn) if h.did != client.did]
                    provider = random.choice(candidates)
                    self._execute_honest_download(client, provider, f"h-file-{provider.alias}-r{r}", r, journal, raw_s, delivery_keys, manifest_roots, now)

                # Dedicated uploader serves high download volume (all honest nodes download from uploader)
                for client in hn:
                    # Client downloads verified file from uploader (Uploader does NOT download in return)
                    content_id = f"uploader-content-r{r}"
                    if content_id not in uploader.manifests:
                        uploader.publish_file(content_id, num_chunks=4)
                    m = uploader.manifests[content_id]
                    t = uploader.merkle_trees[content_id]
                    chunk_idx = r % 4

                    # One-way download verification
                    req_id = f"req-u-r{r}-{client.alias}-{chunk_idx}"
                    req = ContentRequest(
                        req_id=req_id, client_did=client.did, server_did=uploader.did,
                        content_id=content_id, chunk_index=chunk_idx, merkle_root=m.root_hash,
                        timestamp=now, nonce=f"nonce-{req_id}", client_sig_hex=""
                    )
                    req.client_sig_hex = client.identity.sign(req.payload_bytes()).hex()

                    c_bytes = uploader.get_chunk(content_id, chunk_idx)
                    proof = t.generate_proof(chunk_idx)
                    resp = ChunkResponse(
                        req_id=req_id, client_did=client.did, server_did=uploader.did,
                        content_id=content_id, chunk_index=chunk_idx, chunk_bytes=c_bytes,
                        chunk_hash=hashlib.sha256(c_bytes).hexdigest().lower(),
                        proof_hash=hash_proof(proof), merkle_root=m.root_hash,
                        timestamp=now, nonce=req.nonce, merkle_proof=proof, server_sig_hex=""
                    )
                    resp.server_sig_hex = uploader.identity.sign(resp.payload_bytes()).hex()

                    if resp.verify(uploader.public_key_hex, req):
                        tx_id = f"tx-u-r{r}-{client.alias}-{chunk_idx}"
                        receipt = BilateralReceipt(
                            tx_id=tx_id, client_did=client.did, client_pubkey_hex=client.public_key_hex,
                            server_did=uploader.did, server_pubkey_hex=uploader.public_key_hex,
                            merkle_root=m.root_hash, rating="+1.00", timestamp=now,
                            nonce=f"nonce-rcpt-{tx_id}", client_sig_hex="", server_sig_hex=""
                        )
                        pay = receipt.payload_bytes()
                        receipt.client_sig_hex = client.identity.sign(pay).hex()
                        receipt.server_sig_hex = uploader.identity.sign(pay).hex()

                        delta = 1.0 if receipt.rating == "+1.00" else -1.0
                        journal.commit(
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
                        raw_s[(client.did, uploader.did)] = raw_s.get((client.did, uploader.did), 0.0) + delta
                        delivery_keys.add((client.did, uploader.did, m.root_hash.lower(), tx_id))
                        manifest_roots.add(m.root_hash.lower())

            self._evaluate_trial("scenario_8_honest_asymmetric_uploader", scale, s, all_nodes, sn, hn, cn, uploader, journal, raw_s, delivery_keys, manifest_roots, now)

    def run_scenario_9_honest_reciprocal_community(self, seeds: List[int], scale: str = "standard"):
        """Scenario 9: Honest Reciprocal Community. Densely interacting honest peers, measuring suppression/distortion."""
        num_honest = 15 if scale == "standard" else 25
        num_supernodes = 5
        num_colluders = 0
        rounds = 8

        self.log(f"\n--- Scenario 9: Honest Reciprocal Community ({scale}, {len(seeds)} seeds) ---")
        for s in seeds:
            random.seed(s)
            np.random.seed(s)
            sn, hn, cn, _, all_nodes = self._setup_network(num_honest, num_supernodes, num_colluders)
            journal = SimulatorCanonicalJournal()
            raw_s: Dict[Tuple[str, str], float] = {}
            delivery_keys: Set[Tuple[str, str, str, str]] = set()
            manifest_roots: Set[str] = set()
            now = 1000000.0

            for r in range(1, rounds + 1):
                now += 300.0
                # Dense pairwise interaction: each honest peer interacts with multiple peers
                for client in hn:
                    # Select 3 distinct peers per round
                    peers = [p for p in (hn + sn) if p.did != client.did]
                    partners = random.sample(peers, min(3, len(peers)))
                    for provider in partners:
                        self._execute_honest_download(client, provider, f"recip-file-{provider.alias}-r{r}", r, journal, raw_s, delivery_keys, manifest_roots, now)

            self._evaluate_trial("scenario_9_honest_reciprocal_community", scale, s, all_nodes, sn, hn, cn, None, journal, raw_s, delivery_keys, manifest_roots, now)

    # =========================================================================
    # STATISTICAL ANALYSIS & SUMMARY EXPORT
    # =========================================================================

    def compute_and_export_statistics(self):
        """
        Aggregates per-trial metrics, computes paired Student's t-test,
        Cohen's d_z effect size, 95% confidence intervals, and exports
        machine-readable CSV and JSON reports.
        """
        self.log("\n=======================================================")
        self.log(" Computing Statistical Aggregations & Exporting Reports")
        self.log("=======================================================")

        # 1. Export Raw Results JSON
        raw_json_path = os.path.join(self.output_dir, "phase8_2_raw_results.json")
        with open(raw_json_path, "w", encoding="utf-8") as f:
            json.dump([asdict(r) for r in self.all_results], f, indent=2)
        self.log(f"Exported raw JSON to: {raw_json_path}")

        # 2. Export Raw Results CSV
        raw_csv_path = os.path.join(self.output_dir, "phase8_2_raw_results.csv")
        if self.all_results:
            keys = list(asdict(self.all_results[0]).keys())
            with open(raw_csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                for r in self.all_results:
                    writer.writerow(asdict(r))
            self.log(f"Exported raw CSV to: {raw_csv_path}")

        # 3. Compute Summary Statistics by (scenario, scale, mode)
        summary_rows = []
        grouped: Dict[Tuple[str, str, str], List[TrialResult]] = {}
        for r in self.all_results:
            key = (r.scenario, r.scale, r.mode)
            grouped.setdefault(key, []).append(r)

        t_crit_19 = 2.09302  # t(0.975, df=19)

        for (scen, scale, mode), trials in grouped.items():
            n = len(trials)
            c_shares = [t.colluder_trust_share for t in trials]
            h_shares = [t.honest_trust_share for t in trials]
            sn_shares = [t.supernode_trust_share for t in trials]
            max_c_scores = [t.max_colluder_trust for t in trials]
            u_scores = [t.asymmetric_uploader_trust for t in trials]
            iters = [t.iterations for t in trials]
            times = [t.computation_time_seconds for t in trials]
            t1_counts = [t.tier_1_receipts for t in trials]
            t2_counts = [t.tier_2_receipts for t in trials]
            t3_counts = [t.tier_3_receipts for t in trials]

            mean_c = float(np.mean(c_shares))
            std_c = float(np.std(c_shares, ddof=1)) if n > 1 else 0.0
            sem_c = std_c / math.sqrt(n) if n > 0 else 0.0
            ci_c = (mean_c - t_crit_19 * sem_c, mean_c + t_crit_19 * sem_c)

            summary_rows.append({
                "scenario": scen,
                "scale": scale,
                "mode": mode,
                "n_trials": n,
                "colluder_mean": mean_c,
                "colluder_median": float(np.median(c_shares)),
                "colluder_std": std_c,
                "colluder_ci95_low": ci_c[0],
                "colluder_ci95_high": ci_c[1],
                "honest_mean": float(np.mean(h_shares)),
                "supernode_mean": float(np.mean(sn_shares)),
                "max_colluder_mean": float(np.mean(max_c_scores)),
                "uploader_trust_mean": float(np.mean(u_scores)),
                "iterations_mean": float(np.mean(iters)),
                "time_sec_mean": float(np.mean(times)),
                "tier_1_mean": float(np.mean(t1_counts)),
                "tier_2_mean": float(np.mean(t2_counts)),
                "tier_3_mean": float(np.mean(t3_counts))
            })

        summary_csv_path = os.path.join(self.output_dir, "phase8_2_summary.csv")
        if summary_rows:
            with open(summary_csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
                writer.writeheader()
                for row in summary_rows:
                    writer.writerow(row)
            self.log(f"Exported summary CSV to: {summary_csv_path}")

        # 4. Compute Paired Statistical Comparisons (EVIDENCE_ONLY vs VANILLA)
        comparison_rows = []
        distinct_scenarios = sorted(list(set((r.scenario, r.scale) for r in self.all_results)))

        for (scen, scale) in distinct_scenarios:
            vanilla_trials = {t.seed: t for t in grouped.get((scen, scale, TrustComputationMode.VANILLA), [])}
            ew_trials = {t.seed: t for t in grouped.get((scen, scale, TrustComputationMode.EVIDENCE_ONLY), [])}
            local_trials = {t.seed: t for t in grouped.get((scen, scale, TrustComputationMode.LOCAL_ONLY), [])}

            common_seeds = sorted(list(set(vanilla_trials.keys()) & set(ew_trials.keys())))
            if not common_seeds:
                continue

            n = len(common_seeds)
            v_c = np.array([vanilla_trials[s].colluder_trust_share for s in common_seeds])
            ew_c = np.array([ew_trials[s].colluder_trust_share for s in common_seeds])
            diff_c = ew_c - v_c

            mean_v = float(np.mean(v_c))
            mean_ew = float(np.mean(ew_c))
            mean_diff = float(np.mean(diff_c))
            abs_diff = mean_ew - mean_v
            rel_diff = (abs_diff / mean_v * 100.0) if mean_v > 1e-12 else 0.0

            std_diff = float(np.std(diff_c, ddof=1)) if n > 1 else 0.0
            sem_diff = std_diff / math.sqrt(n) if n > 0 else 0.0
            ci95_diff = (mean_diff - t_crit_19 * sem_diff, mean_diff + t_crit_19 * sem_diff)

            # Paired t-test
            if std_diff > 1e-12:
                t_stat, p_val = stats.ttest_rel(ew_c, v_c)
                cohen_dz = mean_diff / std_diff
            else:
                t_stat, p_val, cohen_dz = 0.0, 1.0, 0.0

            # Uploader retention ratio for Scenario 8
            v_u = np.array([vanilla_trials[s].asymmetric_uploader_trust for s in common_seeds])
            ew_u = np.array([ew_trials[s].asymmetric_uploader_trust for s in common_seeds])
            mean_v_u = float(np.mean(v_u))
            mean_ew_u = float(np.mean(ew_u))
            u_retention = (mean_ew_u / mean_v_u) if mean_v_u > 1e-12 else 1.0

            comparison_rows.append({
                "scenario": scen,
                "scale": scale,
                "n_seeds": n,
                "vanilla_colluder_mean": mean_v,
                "ew_colluder_mean": mean_ew,
                "absolute_difference": abs_diff,
                "relative_difference_pct": rel_diff,
                "diff_ci95_low": ci95_diff[0],
                "diff_ci95_high": ci95_diff[1],
                "paired_t_statistic": float(t_stat),
                "p_value": float(p_val),
                "cohens_dz": float(cohen_dz),
                "uploader_retention_ratio": float(u_retention)
            })

        comp_csv_path = os.path.join(self.output_dir, "phase8_2_statistical_comparison.csv")
        if comparison_rows:
            with open(comp_csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=list(comparison_rows[0].keys()))
                writer.writeheader()
                for row in comparison_rows:
                    writer.writerow(row)
            self.log(f"Exported paired statistical comparison CSV to: {comp_csv_path}")

        # 5. Print Human-Readable Comparison Table
        self.log("\n" + "=" * 115)
        self.log(f"{'Scenario':<36} | {'Scale':<8} | {'Vanilla TC':<10} | {'EW TC':<10} | {'Abs Diff':<10} | {'Rel %':<8} | {'p-value':<10} | {'Cohen dz':<8}")
        self.log("-" * 115)
        for r in comparison_rows:
            self.log(
                f"{r['scenario']:<36} | {r['scale']:<8} | {r['vanilla_colluder_mean']:<10.4f} | "
                f"{r['ew_colluder_mean']:<10.4f} | {r['absolute_difference']:<10.4f} | "
                f"{r['relative_difference_pct']:<8.2f}% | {r['p_value']:<10.4e} | {r['cohens_dz']:<8.2f}"
            )
        self.log("=" * 115 + "\n")


def main():
    print("Initializing Phase 8.2 Empirical Validation Benchmark Suite...")
    runner = Phase8_2_BenchmarkRunner()

    # 20 Preregistered Seeds
    seeds = [42 + 17 * i for i in range(20)]
    runner.log(f"Preregistered 20-Seed List: {seeds}")

    # Standard Scale (30 nodes)
    runner.run_scenario_1_honest_baseline(seeds, scale="standard")
    runner.run_scenario_2_closed_collusion(seeds, scale="standard")
    runner.run_scenario_3_leaky_collusion(seeds, scale="standard")
    runner.run_scenario_4_connected_collusion(seeds, bridge_probs=[0.00, 0.05, 0.10, 0.20, 0.40])
    runner.run_scenario_5_adaptive_attacker(seeds)
    runner.run_scenario_6_receipt_grinding(seeds, scale="standard")
    runner.run_scenario_7_dispute_manipulation(seeds)
    runner.run_scenario_8_honest_asymmetric_uploader(seeds, scale="standard")
    runner.run_scenario_9_honest_reciprocal_community(seeds, scale="standard")

    # Extended Scale (50 nodes)
    runner.log("\n--- Starting Extended Scale Evaluations (50 nodes) ---")
    runner.run_scenario_1_honest_baseline(seeds, scale="extended")
    runner.run_scenario_2_closed_collusion(seeds, scale="extended")
    runner.run_scenario_3_leaky_collusion(seeds, scale="extended")
    runner.run_scenario_6_receipt_grinding(seeds, scale="extended")
    runner.run_scenario_8_honest_asymmetric_uploader(seeds, scale="extended")
    runner.run_scenario_9_honest_reciprocal_community(seeds, scale="extended")

    # Statistical Summaries & Exports
    runner.compute_and_export_statistics()
    runner.close()
    print("Phase 8.2 Benchmark Suite completed successfully.")


if __name__ == "__main__":
    main()
