"""
P2P Network Simulation & Adversarial Benchmark Engine
Simulates a hybrid P2P swarm with Honest Nodes, Pre-trusted Supernodes,
and an adversarial Collusive Sybil collective.
"""

import random
import time
from typing import List, Dict, Tuple
import numpy as np

from src.layer1_identity import PeerIdentity
from src.layer2_mesh_pki import MeshPKINetwork
from src.layer3_eigentrust import MerkleTree, BilateralReceipt, EigenTrustEngine
from src.layer4_recovery import CertificateRevocationRecord, ShamirSecretSharing


class SimulatedNode:
    def __init__(self, alias: str, is_sybil: bool = False, is_supernode: bool = False, difficulty_bits: int = 12):
        self.identity = PeerIdentity(alias=alias, difficulty_bits=difficulty_bits)
        self.alias = alias
        self.is_sybil = is_sybil
        self.is_supernode = is_supernode
        self.did = self.identity.did
        self.public_key_hex = self.identity.public_key_hex
        self.files: Dict[str, bytes] = {}

    def generate_file(self, file_name: str, size_kb: int = 512) -> Tuple[bytes, MerkleTree]:
        """Generates dummy content and constructs Merkle tree."""
        content = f"Payload-{self.alias}-{file_name}-{'X' * (size_kb * 1024)}".encode("utf-8")
        chunks = [content[i:i + 64 * 1024] for i in range(0, len(content), 64 * 1024)]
        tree = MerkleTree(chunks)
        self.files[file_name] = content
        return content, tree


class SwarmSimulation:
    def __init__(self, num_honest: int = 20, num_supernodes: int = 5, num_sybils: int = 15):
        self.mesh = MeshPKINetwork(max_hops=4)
        self.nodes: Dict[str, SimulatedNode] = {}
        self.supernodes: List[SimulatedNode] = []
        self.honest_nodes: List[SimulatedNode] = []
        self.sybil_nodes: List[SimulatedNode] = []

        # 1. Initialize Supernodes
        for i in range(num_supernodes):
            sn = SimulatedNode(f"Supernode_{i+1}", is_supernode=True)
            self.nodes[sn.did] = sn
            self.supernodes.append(sn)
            self.mesh.register_peer(sn.identity)

        # 2. Initialize Honest Nodes
        for i in range(num_honest):
            hn = SimulatedNode(f"Honest_{i+1}")
            self.nodes[hn.did] = hn
            self.honest_nodes.append(hn)
            self.mesh.register_peer(hn.identity)

        # 3. Initialize Sybil Nodes
        for i in range(num_sybils):
            syn = SimulatedNode(f"Sybil_{i+1}", is_sybil=True)
            self.nodes[syn.did] = syn
            self.sybil_nodes.append(syn)
            self.mesh.register_peer(syn.identity)

        all_dids = list(self.nodes.keys())
        sn_dids = [sn.did for sn in self.supernodes]
        self.eigentrust = EigenTrustEngine(peers=all_dids, pre_trusted_peers=sn_dids, alpha=0.15)
        
        # Cross-certify supernodes with each other (Layer 2 mesh foundation)
        for i in range(len(self.supernodes)):
            for j in range(i + 1, len(self.supernodes)):
                self.mesh.issue_cross_certificate(self.supernodes[i].identity, self.supernodes[j].identity, 0.95)
                self.mesh.issue_cross_certificate(self.supernodes[j].identity, self.supernodes[i].identity, 0.95)

    def execute_transaction_round(self, round_num: int) -> Dict[str, int]:
        """
        Executes a round of P2P transactions:
        - Honest peers trade files, verify chunks, and co-sign honest ratings.
        - Sybil peers attempt collusion (upvoting each other, bad-mouthing honest nodes, sending poison chunks).
        """
        stats = {"honest_success": 0, "poison_detected": 0, "sybil_collusion_attempts": 0}

        # --- A. Honest Interactions ---
        for honest_node in self.honest_nodes:
            # Pick another honest peer or supernode
            partner = random.choice(self.honest_nodes + self.supernodes)
            if partner.did == honest_node.did:
                continue

            file_bytes, merkle_tree = partner.generate_file(f"round_{round_num}.dat")
            # Chunk verification: check every chunk against Merkle root
            chunks = [file_bytes[i:i + 64 * 1024] for i in range(0, len(file_bytes), 64 * 1024)]
            valid_transfer = all(merkle_tree.verify_chunk(idx, chunk) for idx, chunk in enumerate(chunks))

            if valid_transfer:
                stats["honest_success"] += 1
                now = time.time()
                tx_id = f"tx-h-{round_num}-{honest_node.alias}-{partner.alias}"
                raw_payload = f"{tx_id}:{honest_node.did}:{partner.did}:{merkle_tree.root_hash}:1.00:{now}".encode("utf-8")
                sig_a = honest_node.identity.sign(raw_payload).hex()
                sig_b = partner.identity.sign(raw_payload).hex()

                receipt = BilateralReceipt(
                    tx_id=tx_id, client_did=honest_node.did, client_pubkey_hex=honest_node.public_key_hex,
                    server_did=partner.did, server_pubkey_hex=partner.public_key_hex,
                    merkle_root=merkle_tree.root_hash, rating=1.0, timestamp=now,
                    client_sig_hex=sig_a, server_sig_hex=sig_b
                )
                self.eigentrust.record_receipt(receipt)
                
                # Bilateral credit: In P2P tit-for-tat swarms, uploader also rates downloader positively
                h_idx = self.eigentrust.peer_to_idx[honest_node.did]
                p_idx = self.eigentrust.peer_to_idx[partner.did]
                self.eigentrust.S[p_idx, h_idx] += 1.0

        # Supernodes perform routine validation audits on random honest peers
        for sn in self.supernodes:
            audited_peer = random.choice(self.honest_nodes)
            sn_idx = self.eigentrust.peer_to_idx[sn.did]
            ap_idx = self.eigentrust.peer_to_idx[audited_peer.did]
            self.eigentrust.S[sn_idx, ap_idx] += 1.0

        # --- B. Sybil Adversarial Attack Phase ---
        # 1. Collusive Upvoting: Sybils trade dummy tokens and co-sign +1.0 for each other
        for sybil_node in self.sybil_nodes:
            peer_sybil = random.choice(self.sybil_nodes)
            if peer_sybil.did == sybil_node.did:
                continue
            now = time.time()
            tx_id = f"tx-sybil-{round_num}-{sybil_node.alias}-{peer_sybil.alias}"
            dummy_root = "0" * 64
            raw_payload = f"{tx_id}:{sybil_node.did}:{peer_sybil.did}:{dummy_root}:1.00:{now}".encode("utf-8")
            sig_a = sybil_node.identity.sign(raw_payload).hex()
            sig_b = peer_sybil.identity.sign(raw_payload).hex()
            
            receipt = BilateralReceipt(
                tx_id=tx_id, client_did=sybil_node.did, client_pubkey_hex=sybil_node.public_key_hex,
                server_did=peer_sybil.did, server_pubkey_hex=peer_sybil.public_key_hex,
                merkle_root=dummy_root, rating=1.0, timestamp=now,
                client_sig_hex=sig_a, server_sig_hex=sig_b
            )
            self.eigentrust.record_receipt(receipt)
            stats["sybil_collusion_attempts"] += 1

        # 2. Poison Chunk Attack: Sybil tries to send corrupted data to an honest peer
        victim = random.choice(self.honest_nodes)
        attacker = random.choice(self.sybil_nodes)
        file_bytes, merkle_tree = attacker.generate_file("malicious.iso")
        corrupted_chunk = b"POISONED_CHUNK_CONTENT"
        
        # Victim validates chunk against declared Merkle tree
        if not merkle_tree.verify_chunk(0, corrupted_chunk):
            stats["poison_detected"] += 1
            # Victim refuses to sign a positive receipt, logs negative satisfaction
            now = time.time()
            tx_id = f"tx-failed-{round_num}"
            raw_payload = f"{tx_id}:{victim.did}:{attacker.did}:{merkle_tree.root_hash}:-1.00:{now}".encode("utf-8")
            sig_v = victim.identity.sign(raw_payload).hex()
            # Even without attacker's signature, victim registers local negative rating
            v_idx = self.eigentrust.peer_to_idx[victim.did]
            a_idx = self.eigentrust.peer_to_idx[attacker.did]
            self.eigentrust.S[v_idx, a_idx] -= 1.0

        return stats

    def run_simulation(self, total_rounds: int = 15) -> Dict[str, List[float]]:
        """
        Runs multiple rounds, tracking the trajectory of trust scores for each group.
        """
        history = {
            "honest_avg": [],
            "supernode_avg": [],
            "sybil_avg": []
        }

        for r in range(1, total_rounds + 1):
            self.execute_transaction_round(r)
            scores = self.eigentrust.get_trust_scores()

            sn_scores = [scores[sn.did] for sn in self.supernodes]
            h_scores = [scores[h.did] for h in self.honest_nodes]
            syb_scores = [scores[syb.did] for syb in self.sybil_nodes]

            history["supernode_avg"].append(float(np.mean(sn_scores)))
            history["honest_avg"].append(float(np.mean(h_scores)))
            history["sybil_avg"].append(float(np.mean(syb_scores)))

        return history
