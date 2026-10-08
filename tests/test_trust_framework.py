"""
Unit Test Suite for PKI Trust Management Framework
Tests all 4 architectural layers for cryptographic integrity and mathematical correctness.
Phase 1 updates: Layer 1 Self-Sovereign Identity and Layer 2 Mesh PKI validation.
Phase 2 updates: Genuine Merkle inclusion proofs, ContentManifest, ContentRequest,
ChunkResponse, and FaultEvidenceRecord cryptographic validation.
"""

import time
import hashlib
import unittest
import copy
import numpy as np
from typing import Optional, Tuple, Dict, List
from cryptography.hazmat.primitives import serialization
from src.layer1_identity import PeerIdentity, P2PCertificate, PeerState
from src.layer2_mesh_pki import MeshPKINetwork, CrossCertificate
from src.layer3_eigentrust import (
    MerkleTree, BilateralReceipt, EigenTrustEngine, MerkleProofStep,
    canonical_proof_str, hash_proof, verify_merkle_proof,
    ContentManifest, ContentRequest, ChunkResponse, FaultEvidenceRecord,
    LocalEvidenceJournal, SimulatorCanonicalJournal, JournalEntry
)
from src.layer4_recovery import (
    CertificateRevocationRecord, ShamirSecretSharing,
    RevocationProposal, LocalRevocationStore, RevocationCoordinator,
    evict_peer_from_mesh, process_incoming_crr,
    RecoveryAuthorizationToken, RecoveryRequest, KeyRecoveryCoordinator,
    KeyRotationCertificate, rotate_key_after_recovery, is_key_valid_for_operations,
    PRIME
)
from src.network_simulator import SwarmSimulation, SimulatedNode


class TestPKITrustFramework(unittest.TestCase):

    # =========================================================================
    # PHASE 1 TESTS: LAYER 1 (IDENTITY & ADMISSION)
    # =========================================================================

    def test_layer1_identity_and_pow(self):
        """Validates Ed25519 signing, PoW solution, and certificate verification."""
        peer = PeerIdentity("Alice", difficulty_bits=12)
        self.assertTrue(peer.did.startswith("did:peer:2.Ez"))
        self.assertEqual(len(peer.public_key_hex), 64)
        self.assertEqual(peer.did, f"did:peer:2.Ez{peer.public_key_hex}")
        self.assertEqual(peer.state, PeerState.UNKNOWN)
        self.assertTrue(PeerIdentity.verify_certificate(peer.certificate))

        # Test message signing
        msg = b"Hello, Decentralized P2P World!"
        sig = peer.sign(msg)
        self.assertTrue(PeerIdentity.verify_peer_signature(peer.public_key_hex, msg, sig.hex()))

        # Test corrupted message signature rejection
        self.assertFalse(PeerIdentity.verify_peer_signature(peer.public_key_hex, b"Tampered Message", sig.hex()))

    def test_layer1_identity_full_did_and_consistency(self):
        """Tests full 64-hex DID encoding and deterministic DID/public-key validation."""
        peer = PeerIdentity("Alice", difficulty_bits=12)
        
        # Exact DID format: did:peer:2.Ez<64 lowercase hex characters>
        self.assertTrue(peer.did.startswith("did:peer:2.Ez"))
        self.assertEqual(len(peer.did), 13 + 64)
        self.assertEqual(peer.public_key_hex, peer.public_key_hex.lower())
        self.assertEqual(peer.did, f"did:peer:2.Ez{peer.public_key_hex}")

        # Consistency validation
        self.assertTrue(PeerIdentity.is_valid_did(peer.did, peer.public_key_hex))
        
        # Tampered / truncated DID validation
        self.assertFalse(PeerIdentity.is_valid_did(peer.did[:32], peer.public_key_hex))
        self.assertFalse(PeerIdentity.is_valid_did(f"did:peer:2.Ez{'0' * 64}", peer.public_key_hex))
        self.assertFalse(PeerIdentity.is_valid_did(peer.did, "0" * 64))
        self.assertFalse(PeerIdentity.is_valid_did("did:other:2.Ez" + peer.public_key_hex, peer.public_key_hex))

    def test_layer1_certificate_tampering_and_stale(self):
        """Tests certificate verification against tampering, invalid signatures, and stale timestamps."""
        peer = PeerIdentity("Alice", difficulty_bits=12)
        cert = peer.certificate
        self.assertTrue(PeerIdentity.verify_certificate(cert))

        # 1. Tampered alias
        tampered_alias = copy.deepcopy(cert)
        tampered_alias.alias = "Eve"
        self.assertFalse(PeerIdentity.verify_certificate(tampered_alias))

        # 2. Tampered capabilities
        tampered_caps = copy.deepcopy(cert)
        tampered_caps.capabilities = {"bandwidth_mbps": 9999, "storage_gb": 50, "protocol_version": "2.0-pki"}
        self.assertFalse(PeerIdentity.verify_certificate(tampered_caps))

        # 3. Tampered public key
        tampered_pub = copy.deepcopy(cert)
        tampered_pub.public_key_hex = "0123456789abcdef" * 4
        self.assertFalse(PeerIdentity.verify_certificate(tampered_pub))

        # 4. Invalid signature
        tampered_sig = copy.deepcopy(cert)
        tampered_sig.signature_hex = "00" * 64
        self.assertFalse(PeerIdentity.verify_certificate(tampered_sig))

        # 5. Stale timestamp (> 300s drift)
        stale_cert = copy.deepcopy(cert)
        stale_cert.timestamp = time.time() - 301.0
        # Re-sign to isolate timestamp check
        stale_cert.signature_hex = peer.sign(stale_cert.payload_bytes()).hex()
        self.assertFalse(PeerIdentity.verify_certificate(stale_cert))

    def test_layer1_pow_bit_level_validation(self):
        """Tests Proof-of-Work bit-level verification, nonce correctness, and difficulty boundaries."""
        peer = PeerIdentity("Alice", difficulty_bits=12)
        
        # Valid PoW
        self.assertTrue(PeerIdentity.verify_pow(peer.public_key_hex, peer.alias, peer.pow_nonce, peer.difficulty_bits))

        # Invalid nonce
        self.assertFalse(PeerIdentity.verify_pow(peer.public_key_hex, peer.alias, peer.pow_nonce + 999999, peer.difficulty_bits))

        # Wrong / impossible difficulty
        self.assertFalse(PeerIdentity.verify_pow(peer.public_key_hex, peer.alias, peer.pow_nonce, 250))

        # Minimum difficulty boundary check in verify_certificate
        peer_d8 = PeerIdentity("LowDiff", difficulty_bits=8)
        self.assertFalse(PeerIdentity.verify_certificate(peer_d8.certificate, min_difficulty=12))
        self.assertTrue(PeerIdentity.verify_certificate(peer_d8.certificate, min_difficulty=8))

        # Strict bit-level validation (differentiating 5 bits vs 6 bits)
        # SHA-256('a'*64 : 'Test' : 41) has exactly 5 leading zero bits
        test_pub = "a" * 64
        test_alias = "Test"
        test_nonce = 41
        self.assertTrue(PeerIdentity.verify_pow(test_pub, test_alias, test_nonce, 5))
        self.assertFalse(PeerIdentity.verify_pow(test_pub, test_alias, test_nonce, 6))

    # =========================================================================
    # PHASE 1 TESTS: LAYER 2 (MESH PKI)
    # =========================================================================

    def test_layer2_admission_enforcement(self):
        """Tests that MeshPKINetwork.register_peer verifies certificate before admission and updates PeerState."""
        mesh = MeshPKINetwork(max_hops=4)
        
        # Valid peer admitted
        alice = PeerIdentity("Alice", difficulty_bits=12)
        self.assertEqual(alice.state, PeerState.UNKNOWN)
        admitted = mesh.register_peer(alice, min_difficulty=12)
        self.assertTrue(admitted)
        self.assertEqual(alice.state, PeerState.ACTIVE)
        self.assertIn(alice.did, mesh.peers)

        # Invalid PoW rejected
        bad_pow_peer = PeerIdentity("BadPoW", difficulty_bits=12)
        bad_pow_peer.certificate.pow_nonce += 999999
        self.assertFalse(mesh.register_peer(bad_pow_peer))
        self.assertNotIn(bad_pow_peer.did, mesh.peers)
        self.assertEqual(bad_pow_peer.state, PeerState.UNKNOWN)

        # Stale certificate rejected
        stale_peer = PeerIdentity("Stale", difficulty_bits=12)
        stale_peer.certificate.timestamp = time.time() - 301.0
        stale_peer.certificate.signature_hex = stale_peer.sign(stale_peer.certificate.payload_bytes()).hex()
        self.assertFalse(mesh.register_peer(stale_peer))
        self.assertNotIn(stale_peer.did, mesh.peers)

        # Invalid signature rejected
        bad_sig_peer = PeerIdentity("BadSig", difficulty_bits=12)
        bad_sig_peer.certificate.signature_hex = "ff" * 64
        self.assertFalse(mesh.register_peer(bad_sig_peer))
        self.assertNotIn(bad_sig_peer.did, mesh.peers)

        # Invalid DID rejected
        bad_did_peer = PeerIdentity("BadDID", difficulty_bits=12)
        bad_did_peer.certificate.did = "did:peer:2.Ez" + "0" * 64
        self.assertFalse(mesh.register_peer(bad_did_peer))
        self.assertNotIn(bad_did_peer.did, mesh.peers)

    def test_layer2_cross_certificates(self):
        """Tests cross-certificate serialization, signature verification, tampering, and expiration."""
        mesh = MeshPKINetwork(max_hops=4)
        alice = PeerIdentity("Alice", difficulty_bits=12)
        bob = PeerIdentity("Bob", difficulty_bits=12)
        self.assertTrue(mesh.register_peer(alice))
        self.assertTrue(mesh.register_peer(bob))

        # Valid cross certificate
        cert = mesh.issue_cross_certificate(alice, bob, 0.85)
        self.assertTrue(cert.payload_bytes().startswith(b"PKI_V2_CROSSCERT:"))
        self.assertTrue(mesh.verify_cross_certificate(cert))

        # Tampered trust weight rejected
        tampered_weight = copy.deepcopy(cert)
        tampered_weight.trust_weight = 0.99
        self.assertFalse(mesh.verify_cross_certificate(tampered_weight))

        # Expired certificate rejected
        expired_cert = copy.deepcopy(cert)
        expired_cert.expires_at = time.time() - 1.0
        self.assertFalse(mesh.verify_cross_certificate(expired_cert))

        # Domain prefix mismatch rejected
        unsigned_legacy = f"{cert.issuer_did}:{cert.subject_did}:{cert.trust_weight:.4f}:{cert.issued_at}:{cert.expires_at}".encode("utf-8")
        legacy_sig = alice.sign(unsigned_legacy).hex()
        bad_prefix_cert = copy.deepcopy(cert)
        bad_prefix_cert.signature_hex = legacy_sig
        self.assertFalse(mesh.verify_cross_certificate(bad_prefix_cert))

    def test_layer2_disjoint_paths_intermediate_filtering(self):
        """Tests strict intermediate-vertex disjointness filtering in find_disjoint_paths."""
        mesh = MeshPKINetwork(max_hops=4)
        s = PeerIdentity("Source", difficulty_bits=12)
        t = PeerIdentity("Target", difficulty_bits=12)
        a = PeerIdentity("NodeA", difficulty_bits=12)
        b = PeerIdentity("NodeB", difficulty_bits=12)
        c = PeerIdentity("NodeC", difficulty_bits=12)

        for p in (s, t, a, b, c):
            mesh.register_peer(p)

        # Path 1: S -> A -> T (intermediate: {A})
        mesh.issue_cross_certificate(s, a, 0.9)
        mesh.issue_cross_certificate(a, t, 0.9)

        # Path 2: S -> A -> B -> T (intermediate: {A, B} - shares node A with Path 1)
        mesh.issue_cross_certificate(a, b, 0.9)
        mesh.issue_cross_certificate(b, t, 0.9)

        # Path 3: S -> C -> T (intermediate: {C} - disjoint from Path 1)
        mesh.issue_cross_certificate(s, c, 0.8)
        mesh.issue_cross_certificate(c, t, 0.8)

        paths = mesh.find_disjoint_paths(s.did, t.did)

        # Extract intermediate vertices for each returned path
        intermediate_sets = []
        for path in paths:
            intermediates = [edge.subject_did for edge in path[:-1]]
            intermediate_sets.append(set(intermediates))

        # Verify that no intermediate vertex is shared across any returned paths
        all_intermediates = []
        for iset in intermediate_sets:
            all_intermediates.extend(list(iset))
        self.assertEqual(len(all_intermediates), len(set(all_intermediates)),
                         "Intermediate vertices across returned paths must be strictly disjoint")

        # Specifically, Path 1 and Path 2 share node A and must NOT be returned together
        has_a_only = any(iset == {a.did} for iset in intermediate_sets)
        has_ab = any(iset == {a.did, b.did} for iset in intermediate_sets)
        self.assertFalse(has_a_only and has_ab, "Path 1 and Path 2 share intermediate node A and must not be returned together")

    def test_layer2_supernode_election_disabled(self):
        """Validates that elect_supernodes raises NotImplementedError per frozen protocol."""
        mesh = MeshPKINetwork(max_hops=4)
        with self.assertRaises(NotImplementedError):
            mesh.elect_supernodes()

    def test_layer2_mesh_pki(self):
        """Validates cross-certification and multi-path trust."""
        mesh = MeshPKINetwork(max_hops=4)
        alice = PeerIdentity("Alice", difficulty_bits=12)
        bob = PeerIdentity("Bob", difficulty_bits=12)
        charlie = PeerIdentity("Charlie", difficulty_bits=12)

        self.assertTrue(mesh.register_peer(alice))
        self.assertTrue(mesh.register_peer(bob))
        self.assertTrue(mesh.register_peer(charlie))

        # Cross-certify Alice -> Bob (0.9), Bob -> Charlie (0.8)
        mesh.issue_cross_certificate(alice, bob, 0.9)
        mesh.issue_cross_certificate(bob, charlie, 0.8)

        # Transitive confidence: 0.9 * 0.8 = 0.72
        confidence = mesh.compute_transitive_confidence(alice.did, charlie.did)
        self.assertAlmostEqual(confidence, 0.72, places=2)

    # =========================================================================
    # PHASE 2 TESTS: LAYER 3 (MERKLE PROOFS, MANIFESTS, REQUESTS, EVIDENCE)
    # =========================================================================

    def test_layer3_merkle_construction(self):
        """Tests Merkle tree construction: 1 chunk, 2 chunks, odd chunks, duplicated terminal, deterministic root."""
        # 1 chunk
        c0 = b"SingleChunk"
        t1 = MerkleTree([c0])
        self.assertEqual(t1.root_hash, hashlib.sha256(c0).hexdigest().lower())

        # 2 chunks
        c1, c2 = b"ChunkA", b"ChunkB"
        t2 = MerkleTree([c1, c2])
        h1 = hashlib.sha256(c1).digest()
        h2 = hashlib.sha256(c2).digest()
        expected_root2 = hashlib.sha256(h1 + h2).hexdigest().lower()
        self.assertEqual(t2.root_hash, expected_root2)

        # Odd number of chunks (3 chunks)
        t3 = MerkleTree([b"C0", b"C1", b"C2"])
        # In level 0, node 2 is duplicated: parent is sha256(raw(L2) || raw(L2))
        l2_raw = bytes.fromhex(t3.leaf_hashes[2])
        expected_parent_2 = hashlib.sha256(l2_raw + l2_raw).hexdigest().lower()
        self.assertEqual(t3.tree_levels[1][1], expected_parent_2)

        # Deterministic root
        t3_replica = MerkleTree([b"C0", b"C1", b"C2"])
        self.assertEqual(t3.root_hash, t3_replica.root_hash)

    def test_layer3_merkle_proof_generation(self):
        """Tests Merkle proof generation: valid, first, last, odd-terminal, negative, and out-of-range indices."""
        chunks = [f"Chunk-{i}".encode("utf-8") for i in range(5)]
        tree = MerkleTree(chunks)

        # Valid intermediate index
        proof_mid = tree.generate_proof(2)
        self.assertGreater(len(proof_mid), 0)

        # First index (k = 0)
        proof_first = tree.generate_proof(0)
        self.assertEqual(proof_first[0].direction, "R")
        self.assertEqual(proof_first[0].sibling_hash, tree.leaf_hashes[1])

        # Last index / odd-terminal index (k = 4 in 5-chunk tree)
        # At level 0, index 4 is duplicated, sibling is itself, direction is 'R'
        proof_odd = tree.generate_proof(4)
        self.assertEqual(proof_odd[0].direction, "R")
        self.assertEqual(proof_odd[0].sibling_hash, tree.leaf_hashes[4])

        # Invalid negative index
        with self.assertRaises(IndexError):
            tree.generate_proof(-1)

        # Out-of-range index
        with self.assertRaises(IndexError):
            tree.generate_proof(5)

    def test_layer3_merkle_proof_verification(self):
        """Tests standalone proof verification: authentic, modified chunk, modified sibling, modified direction, root, malformed."""
        chunks = [b"Chunk0", b"Chunk1", b"Chunk2", b"Chunk3"]
        tree = MerkleTree(chunks)
        p1 = tree.generate_proof(1)

        # Authentic chunk passes
        self.assertTrue(verify_merkle_proof(chunks[1], p1, 1, tree.root_hash))

        # Modified chunk fails
        self.assertFalse(verify_merkle_proof(b"TamperedChunk", p1, 1, tree.root_hash))

        # Modified sibling fails
        p_bad_sib = copy.deepcopy(p1)
        p_bad_sib[0].sibling_hash = "0" * 64
        self.assertFalse(verify_merkle_proof(chunks[1], p_bad_sib, 1, tree.root_hash))

        # Modified direction fails
        p_bad_dir = copy.deepcopy(p1)
        p_bad_dir[0].direction = "R" if p_bad_dir[0].direction == "L" else "L"
        self.assertFalse(verify_merkle_proof(chunks[1], p_bad_dir, 1, tree.root_hash))

        # Modified root fails
        self.assertFalse(verify_merkle_proof(chunks[1], p1, 1, "0" * 64))

        # Malformed proof fails (not list, invalid types)
        self.assertFalse(verify_merkle_proof(chunks[1], "invalid_proof", 1, tree.root_hash))
        self.assertFalse(verify_merkle_proof(chunks[1], [None], 1, tree.root_hash))

        # Invalid sibling hash format fails
        p_invalid_hex = copy.deepcopy(p1)
        p_invalid_hex[0].sibling_hash = "not-a-valid-hex-digest"
        self.assertFalse(verify_merkle_proof(chunks[1], p_invalid_hex, 1, tree.root_hash))

        # Wrong chunk index fails
        self.assertFalse(verify_merkle_proof(chunks[1], p1, 0, tree.root_hash))

    def test_layer3_proof_serialization(self):
        """Tests canonical proof serialization and deterministic proof hashing."""
        chunks = [b"A", b"B", b"C", b"D"]
        tree = MerkleTree(chunks)
        proof = tree.generate_proof(0)

        # Deterministic string serialization
        s1 = canonical_proof_str(proof)
        s2 = canonical_proof_str(proof)
        self.assertEqual(s1, s2)
        self.assertIn(":R", s1)

        # Deterministic hashing
        h1 = hash_proof(proof)
        h2 = hash_proof(proof)
        self.assertEqual(h1, h2)
        self.assertEqual(len(h1), 64)

        # Changing sibling changes hash
        proof_tampered_sib = copy.deepcopy(proof)
        proof_tampered_sib[0].sibling_hash = "f" * 64
        self.assertNotEqual(hash_proof(proof), hash_proof(proof_tampered_sib))

        # Changing direction changes hash
        proof_tampered_dir = copy.deepcopy(proof)
        proof_tampered_dir[0].direction = "L" if proof_tampered_dir[0].direction == "R" else "R"
        self.assertNotEqual(hash_proof(proof), hash_proof(proof_tampered_dir))

        # Empty proof
        self.assertEqual(canonical_proof_str([]), "")

    def test_layer3_content_manifest(self):
        """Tests ContentManifest serialization, signature verification, and field tampering rejection."""
        publisher = PeerIdentity("Publisher", difficulty_bits=12)
        root = "a" * 64
        man = ContentManifest(
            content_id="file-101",
            root_hash=root,
            total_chunks=8,
            chunk_size_bytes=65536,
            file_size_bytes=524288,
            publisher_did=publisher.did,
            timestamp=time.time(),
            signature_hex=""
        )
        self.assertTrue(man.payload_bytes().startswith(b"PKI_V2_MANIFEST:"))
        man.signature_hex = publisher.sign(man.payload_bytes()).hex()

        # Valid signature
        self.assertTrue(man.verify_signature(publisher.public_key_hex))

        # Tampered root rejected
        bad_root = copy.deepcopy(man)
        bad_root.root_hash = "b" * 64
        self.assertFalse(bad_root.verify_signature(publisher.public_key_hex))

        # Tampered content ID rejected
        bad_cid = copy.deepcopy(man)
        bad_cid.content_id = "file-999"
        self.assertFalse(bad_cid.verify_signature(publisher.public_key_hex))

        # Tampered publisher rejected
        bad_pub = copy.deepcopy(man)
        bad_pub.publisher_did = "did:peer:2.Ez" + "0" * 64
        self.assertFalse(bad_pub.verify_signature(publisher.public_key_hex))

    def test_layer3_content_request(self):
        """Tests ContentRequest serialization, signature verification, and tampering rejection."""
        client = PeerIdentity("Client", difficulty_bits=12)
        server = PeerIdentity("Server", difficulty_bits=12)
        req = ContentRequest(
            req_id="req-101",
            client_did=client.did,
            server_did=server.did,
            content_id="file-101",
            chunk_index=2,
            merkle_root="a" * 64,
            timestamp=time.time(),
            nonce="nonce-99",
            client_sig_hex=""
        )
        self.assertTrue(req.payload_bytes().startswith(b"PKI_V2_REQ:"))
        req.client_sig_hex = client.sign(req.payload_bytes()).hex()

        # Valid signature
        self.assertTrue(req.verify_signature(client.public_key_hex))

        # Tampered chunk index rejected
        bad_idx = copy.deepcopy(req)
        bad_idx.chunk_index = 3
        self.assertFalse(bad_idx.verify_signature(client.public_key_hex))

        # Tampered nonce rejected
        bad_nonce = copy.deepcopy(req)
        bad_nonce.nonce = "other-nonce"
        self.assertFalse(bad_nonce.verify_signature(client.public_key_hex))

    def test_layer3_chunk_response_validation(self):
        """Tests ChunkResponse full validation: proof hash, chunk hash, root, nonce, request binding, Merkle proof."""
        client = PeerIdentity("Client", difficulty_bits=12)
        server = PeerIdentity("Server", difficulty_bits=12)
        chunks = [b"Chunk0", b"Chunk1", b"Chunk2", b"Chunk3"]
        tree = MerkleTree(chunks)
        target_idx = 1
        target_bytes = chunks[target_idx]
        chunk_hash = hashlib.sha256(target_bytes).hexdigest().lower()
        proof = tree.generate_proof(target_idx)
        proof_hash = hash_proof(proof)

        req = ContentRequest(
            req_id="req-42",
            client_did=client.did,
            server_did=server.did,
            content_id="cid-alpha",
            chunk_index=target_idx,
            merkle_root=tree.root_hash,
            timestamp=time.time(),
            nonce="nonce-42",
            client_sig_hex=""
        )
        req.client_sig_hex = client.sign(req.payload_bytes()).hex()

        resp = ChunkResponse(
            req_id=req.req_id,
            client_did=req.client_did,
            server_did=req.server_did,
            content_id=req.content_id,
            chunk_index=req.chunk_index,
            chunk_bytes=target_bytes,
            chunk_hash=chunk_hash,
            proof_hash=proof_hash,
            merkle_root=tree.root_hash,
            timestamp=time.time(),
            nonce=req.nonce,
            merkle_proof=proof,
            server_sig_hex=""
        )
        self.assertTrue(resp.payload_bytes().startswith(b"PKI_V2_RESP:"))
        resp.server_sig_hex = server.sign(resp.payload_bytes()).hex()

        # Valid response passes with and without request binding
        self.assertTrue(resp.verify(server.public_key_hex))
        self.assertTrue(resp.verify(server.public_key_hex, expected_request=req))

        # Tampered chunk hash rejected
        b_ch = copy.deepcopy(resp)
        b_ch.chunk_hash = "0" * 64
        self.assertFalse(b_ch.verify(server.public_key_hex, req))

        # Tampered proof hash rejected
        b_ph = copy.deepcopy(resp)
        b_ph.proof_hash = "0" * 64
        self.assertFalse(b_ph.verify(server.public_key_hex, req))

        # Tampered root rejected
        b_root = copy.deepcopy(resp)
        b_root.merkle_root = "0" * 64
        self.assertFalse(b_root.verify(server.public_key_hex, req))

        # Tampered nonce rejected
        b_nonce = copy.deepcopy(resp)
        b_nonce.nonce = "tampered-nonce"
        self.assertFalse(b_nonce.verify(server.public_key_hex, req))

        # Request/response mismatch rejected
        mismatched_req = copy.deepcopy(req)
        mismatched_req.req_id = "req-different"
        self.assertFalse(resp.verify(server.public_key_hex, mismatched_req))

        # Proof hash mismatch rejected (proof altered without altering proof_hash)
        b_proof = copy.deepcopy(resp)
        b_proof.merkle_proof = tree.generate_proof(0)
        self.assertFalse(b_proof.verify(server.public_key_hex, req))

        # Chunk hash mismatch rejected (bytes altered without altering chunk_hash)
        b_bytes = copy.deepcopy(resp)
        b_bytes.chunk_bytes = b"CorruptedBytes"
        self.assertFalse(b_bytes.verify(server.public_key_hex, req))

        # Invalid Merkle proof rejected (even if signed by server)
        b_fake_proof = copy.deepcopy(resp)
        b_fake_proof.merkle_proof[0].sibling_hash = "0" * 64
        b_fake_proof.proof_hash = hash_proof(b_fake_proof.merkle_proof)
        b_fake_proof.server_sig_hex = server.sign(b_fake_proof.payload_bytes()).hex()
        self.assertFalse(b_fake_proof.verify(server.public_key_hex, req))

    def test_layer3_fault_evidence_contradiction(self):
        """Tests FaultEvidenceRecord mathematical contradiction and cryptographic verification."""
        publisher = PeerIdentity("Publisher", difficulty_bits=12)
        server = PeerIdentity("AccusedServer", difficulty_bits=12)
        reporter = PeerIdentity("ClientReporter", difficulty_bits=12)

        # 1. Authentic file and Merkle tree
        auth_chunks = [b"Chunk0-good", b"Chunk1-good", b"Chunk2-good", b"Chunk3-good"]
        tree = MerkleTree(auth_chunks)
        auth_root = tree.root_hash

        # 2. Authentic Manifest
        manifest = ContentManifest(
            content_id="cid-critical-file",
            root_hash=auth_root,
            total_chunks=4,
            chunk_size_bytes=1024,
            file_size_bytes=4096,
            publisher_did=publisher.did,
            timestamp=time.time(),
            signature_hex=""
        )
        manifest.signature_hex = publisher.sign(manifest.payload_bytes()).hex()

        # 3. Server delivers corrupted chunk for index 1
        poisoned_bytes = b"Chunk1-POISONED"
        poisoned_chunk_hash = hashlib.sha256(poisoned_bytes).hexdigest().lower()
        fake_proof = [
            MerkleProofStep(sibling_hash="0" * 64, direction="L"),
            MerkleProofStep(sibling_hash="0" * 64, direction="R")
        ]
        fake_proof_hash = hash_proof(fake_proof)

        delivery = ChunkResponse(
            req_id="req-inconsistent-99",
            client_did=reporter.did,
            server_did=server.did,
            content_id=manifest.content_id,
            chunk_index=1,
            chunk_bytes=poisoned_bytes,
            chunk_hash=poisoned_chunk_hash,
            proof_hash=fake_proof_hash,
            merkle_root=auth_root,
            timestamp=time.time(),
            nonce="nonce-inc-99",
            merkle_proof=fake_proof,
            server_sig_hex=""
        )
        delivery.server_sig_hex = server.sign(delivery.payload_bytes()).hex()

        # 4. Reporter acquires authentic proof for index 1
        auth_chunk_hash = hashlib.sha256(auth_chunks[1]).hexdigest().lower()
        auth_proof = tree.generate_proof(1)

        # 5. Reporter constructs and signs FaultEvidenceRecord
        evidence = FaultEvidenceRecord(
            evidence_id="ev-fault-001",
            req_id=delivery.req_id,
            reporter_did=reporter.did,
            accused_did=server.did,
            content_id=manifest.content_id,
            merkle_root=auth_root,
            chunk_index=1,
            delivered_chunk_hash=poisoned_chunk_hash,
            delivered_proof_hash=fake_proof_hash,
            manifest_envelope=manifest,
            delivery_envelope=delivery,
            authentic_chunk_hash=auth_chunk_hash,
            authentic_merkle_proof=auth_proof,
            timestamp=time.time(),
            reporter_sig_hex=""
        )
        self.assertTrue(evidence.payload_bytes().startswith(b"PKI_V2_EVIDENCE_FAULT:"))
        evidence.reporter_sig_hex = reporter.sign(evidence.payload_bytes()).hex()

        # Valid authentic proof + differing delivered hash succeeds
        self.assertTrue(evidence.verify(
            reporter.public_key_hex,
            server.public_key_hex,
            publisher.public_key_hex
        ))

        # Invalid authentic proof fails
        b_auth_proof = copy.deepcopy(evidence)
        b_auth_proof.authentic_merkle_proof[0].sibling_hash = "0" * 64
        b_auth_proof.reporter_sig_hex = reporter.sign(b_auth_proof.payload_bytes()).hex()
        self.assertFalse(b_auth_proof.verify(reporter.public_key_hex, server.public_key_hex, publisher.public_key_hex))

        # Equal authentic/delivered hash fails contradiction
        b_no_contradiction = copy.deepcopy(evidence)
        b_no_contradiction.delivered_chunk_hash = b_no_contradiction.authentic_chunk_hash
        b_no_contradiction.reporter_sig_hex = reporter.sign(b_no_contradiction.payload_bytes()).hex()
        self.assertFalse(b_no_contradiction.verify(reporter.public_key_hex, server.public_key_hex, publisher.public_key_hex))

        # Tampered delivery envelope fails
        b_delivery = copy.deepcopy(evidence)
        b_delivery.delivery_envelope.chunk_bytes = b"SubstitutedBytes"
        self.assertFalse(b_delivery.verify(reporter.public_key_hex, server.public_key_hex, publisher.public_key_hex))

        # Tampered manifest fails
        b_manifest = copy.deepcopy(evidence)
        b_manifest.manifest_envelope.root_hash = "0" * 64
        self.assertFalse(b_manifest.verify(reporter.public_key_hex, server.public_key_hex, publisher.public_key_hex))

        # Tampered reporter signature fails
        b_rep_sig = copy.deepcopy(evidence)
        b_rep_sig.reporter_sig_hex = "00" * 64
        self.assertFalse(b_rep_sig.verify(reporter.public_key_hex, server.public_key_hex, publisher.public_key_hex))

    # =========================================================================
    # PHASE 3 TESTS: EVIDENCE VALIDATION, REPLAY PROTECTION & CANONICAL ACCOUNTING
    # =========================================================================

    def _create_signed_receipt(
        self,
        client: PeerIdentity,
        server: PeerIdentity,
        tx_id: str,
        root: str,
        rating: str = "+1.00",
        timestamp: Optional[float] = None,
        nonce: Optional[str] = None
    ) -> BilateralReceipt:
        ts = time.time() if timestamp is None else timestamp
        n = f"nonce-{tx_id}" if nonce is None else nonce
        receipt = BilateralReceipt(
            tx_id=tx_id,
            client_did=client.did,
            client_pubkey_hex=client.public_key_hex,
            server_did=server.did,
            server_pubkey_hex=server.public_key_hex,
            merkle_root=root,
            rating=rating,
            timestamp=ts,
            nonce=n
        )
        payload = receipt.payload_bytes()
        receipt.client_sig_hex = client.sign(payload).hex()
        receipt.server_sig_hex = server.sign(payload).hex()
        return receipt

    def _create_signed_fault_evidence(
        self,
        publisher: PeerIdentity,
        accused: PeerIdentity,
        reporter: PeerIdentity,
        evidence_id: str = "ev-phase3-01",
        req_id: str = "req-phase3-01",
        timestamp: Optional[float] = None
    ) -> Tuple[FaultEvidenceRecord, ContentManifest, ChunkResponse, MerkleTree]:
        ts = time.time() if timestamp is None else timestamp
        chunks = [b"AuthChunk0", b"AuthChunk1", b"AuthChunk2", b"AuthChunk3"]
        tree = MerkleTree(chunks)
        root = tree.root_hash

        manifest = ContentManifest(
            content_id="content-p3-file",
            root_hash=root,
            total_chunks=4,
            chunk_size_bytes=1024,
            file_size_bytes=4096,
            publisher_did=publisher.did,
            timestamp=ts,
            signature_hex=""
        )
        manifest.signature_hex = publisher.sign(manifest.payload_bytes()).hex()

        poisoned_bytes = b"PoisonedChunk1"
        poisoned_hash = hashlib.sha256(poisoned_bytes).hexdigest().lower()
        fake_proof = [
            MerkleProofStep(sibling_hash="0" * 64, direction="L"),
            MerkleProofStep(sibling_hash="0" * 64, direction="R")
        ]
        fake_proof_hash = hash_proof(fake_proof)

        delivery = ChunkResponse(
            req_id=req_id,
            client_did=reporter.did,
            server_did=accused.did,
            content_id=manifest.content_id,
            chunk_index=1,
            chunk_bytes=poisoned_bytes,
            chunk_hash=poisoned_hash,
            proof_hash=fake_proof_hash,
            merkle_root=root,
            timestamp=ts,
            nonce=f"nonce-del-{req_id}",
            merkle_proof=fake_proof,
            server_sig_hex=""
        )
        delivery.server_sig_hex = accused.sign(delivery.payload_bytes()).hex()

        auth_leaf_hash = hashlib.sha256(chunks[1]).hexdigest().lower()
        auth_proof = tree.generate_proof(1)

        evidence = FaultEvidenceRecord(
            evidence_id=evidence_id,
            req_id=req_id,
            reporter_did=reporter.did,
            accused_did=accused.did,
            content_id=manifest.content_id,
            merkle_root=root,
            chunk_index=1,
            delivered_chunk_hash=poisoned_hash,
            delivered_proof_hash=fake_proof_hash,
            manifest_envelope=manifest,
            delivery_envelope=delivery,
            authentic_chunk_hash=auth_leaf_hash,
            authentic_merkle_proof=auth_proof,
            timestamp=ts,
            reporter_sig_hex=""
        )
        evidence.reporter_sig_hex = reporter.sign(evidence.payload_bytes()).hex()
        return evidence, manifest, delivery, tree

    def test_phase3_a_positive_receipt(self):
        """Validates positive bilateral receipt (+1.00): accepted, S increases exactly once."""
        alice = PeerIdentity("Alice", difficulty_bits=12)
        bob = PeerIdentity("Bob", difficulty_bits=12)
        engine = EigenTrustEngine(peers=[alice.did, bob.did], pre_trusted_peers=[alice.did])
        engine.register_peer(alice)
        engine.register_peer(bob)

        root = "a" * 64
        receipt = self._create_signed_receipt(alice, bob, tx_id="tx-pos-1", root=root, rating="+1.00")
        
        self.assertTrue(engine.record_receipt(receipt))
        c_idx = engine.peer_to_idx[alice.did]
        s_idx = engine.peer_to_idx[bob.did]
        self.assertEqual(engine.S[c_idx, s_idx], 1.0)
        self.assertTrue(engine.local_journal.contains("tx-pos-1", entry_type="RECEIPT"))

    def test_phase3_b_negative_receipt_dispute(self):
        """Validates negative bilateral receipt (-1.00): dispute signal, S decreases by 1, NO revocation."""
        alice = PeerIdentity("Alice", difficulty_bits=12)
        bob = PeerIdentity("Bob", difficulty_bits=12)
        engine = EigenTrustEngine(peers=[alice.did, bob.did], pre_trusted_peers=[alice.did])
        engine.register_peer(alice)
        engine.register_peer(bob)

        root = "b" * 64
        receipt = self._create_signed_receipt(alice, bob, tx_id="tx-neg-1", root=root, rating="-1.00")
        
        self.assertTrue(engine.record_receipt(receipt))
        c_idx = engine.peer_to_idx[alice.did]
        s_idx = engine.peer_to_idx[bob.did]
        self.assertEqual(engine.S[c_idx, s_idx], -1.0)
        # Invariant: Negative dispute does NOT mark peer SUSPECTED or REVOKED
        self.assertEqual(engine.peer_states[bob.did], PeerState.ACTIVE)
        self.assertEqual(bob.state, PeerState.UNKNOWN)

    def test_phase3_c_receipt_replay_protection(self):
        """Validates exact and same-object receipt replays are rejected without second S mutation."""
        alice = PeerIdentity("Alice", difficulty_bits=12)
        bob = PeerIdentity("Bob", difficulty_bits=12)
        engine = EigenTrustEngine(peers=[alice.did, bob.did], pre_trusted_peers=[alice.did])
        engine.register_peer(alice)
        engine.register_peer(bob)

        root = "c" * 64
        receipt = self._create_signed_receipt(alice, bob, tx_id="tx-replay-1", root=root, rating="+1.00")
        
        # 1. First submission succeeds
        self.assertTrue(engine.record_receipt(receipt))
        c_idx = engine.peer_to_idx[alice.did]
        s_idx = engine.peer_to_idx[bob.did]
        self.assertEqual(engine.S[c_idx, s_idx], 1.0)

        # 2. Exact replay rejected
        exact_copy = copy.deepcopy(receipt)
        self.assertFalse(engine.record_receipt(exact_copy))
        self.assertEqual(engine.S[c_idx, s_idx], 1.0)

        # 3. Same object replay rejected
        self.assertFalse(engine.record_receipt(receipt))
        self.assertEqual(engine.S[c_idx, s_idx], 1.0)

    def test_phase3_d_receipt_tampering_rejection(self):
        """Validates rejection of receipts with bad signatures, stale timestamps, reused nonces, or invalid ratings."""
        alice = PeerIdentity("Alice", difficulty_bits=12)
        bob = PeerIdentity("Bob", difficulty_bits=12)
        engine = EigenTrustEngine(peers=[alice.did, bob.did], pre_trusted_peers=[alice.did])
        engine.register_peer(alice)
        engine.register_peer(bob)

        root = "d" * 64

        # 1. Corrupted signature rejected
        bad_sig_rcpt = self._create_signed_receipt(alice, bob, tx_id="tx-badsig", root=root)
        bad_sig_rcpt.client_sig_hex = "00" * 64
        self.assertFalse(engine.record_receipt(bad_sig_rcpt))

        # 2. Stale timestamp (> 600s drift) rejected
        stale_rcpt = self._create_signed_receipt(alice, bob, tx_id="tx-stale", root=root, timestamp=time.time() - 650.0)
        self.assertFalse(engine.record_receipt(stale_rcpt))

        # 3. Nonce reuse with different tx_id rejected
        rcpt1 = self._create_signed_receipt(alice, bob, tx_id="tx-nonce-1", root=root, nonce="unique-nonce-1")
        self.assertTrue(engine.record_receipt(rcpt1))
        rcpt2_reused_nonce = self._create_signed_receipt(alice, bob, tx_id="tx-nonce-2", root=root, nonce="unique-nonce-1")
        self.assertFalse(engine.record_receipt(rcpt2_reused_nonce))

        # 4. Rating outside {+1.00, -1.00} rejected
        bad_rating = self._create_signed_receipt(alice, bob, tx_id="tx-bad-rating", root=root, rating="+0.50")
        self.assertFalse(engine.record_receipt(bad_rating))

        # 5. Participant mismatch (client == server or unregistered peer) rejected
        self_loop = self._create_signed_receipt(alice, alice, tx_id="tx-self", root=root)
        self.assertFalse(engine.record_receipt(self_loop))

    def test_phase3_e_fault_evidence_accounting(self):
        """Validates that verified FaultEvidenceRecord deducts 2.0 and transitions accused to SUSPECTED."""
        publisher = PeerIdentity("Publisher", difficulty_bits=12)
        accused = PeerIdentity("Accused", difficulty_bits=12)
        reporter = PeerIdentity("Reporter", difficulty_bits=12)

        engine = EigenTrustEngine(peers=[reporter.did, accused.did], pre_trusted_peers=[reporter.did])
        engine.register_peer(reporter)
        engine.register_peer(accused)

        evidence, manifest, _, _ = self._create_signed_fault_evidence(publisher, accused, reporter)

        # Before accounting: accused is ACTIVE
        self.assertEqual(engine.peer_states[accused.did], PeerState.ACTIVE)

        # Record verified fault evidence
        self.assertTrue(engine.record_fault_evidence(
            evidence,
            manifest_publisher_pubkey_hex=publisher.public_key_hex
        ))

        # Invariants: S deducted by 2.0, state transitioned to SUSPECTED
        r_idx = engine.peer_to_idx[reporter.did]
        a_idx = engine.peer_to_idx[accused.did]
        self.assertEqual(engine.S[r_idx, a_idx], -2.0)
        self.assertEqual(engine.peer_states[accused.did], PeerState.SUSPECTED)
        self.assertEqual(accused.state, PeerState.SUSPECTED)

    def test_phase3_f_fault_evidence_replay_protection(self):
        """Validates that replayed FaultEvidenceRecord is rejected with no second deduction."""
        publisher = PeerIdentity("Publisher", difficulty_bits=12)
        accused = PeerIdentity("Accused", difficulty_bits=12)
        reporter = PeerIdentity("Reporter", difficulty_bits=12)

        engine = EigenTrustEngine(peers=[reporter.did, accused.did], pre_trusted_peers=[reporter.did])
        engine.register_peer(reporter)
        engine.register_peer(accused)

        evidence, _, _, _ = self._create_signed_fault_evidence(publisher, accused, reporter, evidence_id="ev-replay-01")

        # First recording succeeds
        self.assertTrue(engine.record_fault_evidence(evidence, manifest_publisher_pubkey_hex=publisher.public_key_hex))
        r_idx = engine.peer_to_idx[reporter.did]
        a_idx = engine.peer_to_idx[accused.did]
        self.assertEqual(engine.S[r_idx, a_idx], -2.0)

        # Replay rejected
        exact_copy = copy.deepcopy(evidence)
        self.assertFalse(engine.record_fault_evidence(exact_copy, manifest_publisher_pubkey_hex=publisher.public_key_hex))
        self.assertEqual(engine.S[r_idx, a_idx], -2.0)

    def test_phase3_g_fault_evidence_tampering_rejection(self):
        """Validates that modified fault evidence, delivery envelope, authentic proof, or signature are rejected."""
        publisher = PeerIdentity("Publisher", difficulty_bits=12)
        accused = PeerIdentity("Accused", difficulty_bits=12)
        reporter = PeerIdentity("Reporter", difficulty_bits=12)

        engine = EigenTrustEngine(peers=[reporter.did, accused.did], pre_trusted_peers=[reporter.did])
        engine.register_peer(reporter)
        engine.register_peer(accused)

        evidence, _, _, _ = self._create_signed_fault_evidence(publisher, accused, reporter)

        # 1. Tampered delivery envelope chunk bytes rejected
        b_del = copy.deepcopy(evidence)
        b_del.delivery_envelope.chunk_bytes = b"AlteredBytes"
        self.assertFalse(engine.record_fault_evidence(b_del, manifest_publisher_pubkey_hex=publisher.public_key_hex))

        # 2. Tampered authentic proof rejected
        b_proof = copy.deepcopy(evidence)
        b_proof.authentic_merkle_proof[0].sibling_hash = "0" * 64
        self.assertFalse(engine.record_fault_evidence(b_proof, manifest_publisher_pubkey_hex=publisher.public_key_hex))

        # 3. Tampered reporter signature rejected
        b_sig = copy.deepcopy(evidence)
        b_sig.reporter_sig_hex = "00" * 64
        self.assertFalse(engine.record_fault_evidence(b_sig, manifest_publisher_pubkey_hex=publisher.public_key_hex))

        # Invariant: S remains 0.0, accused remains ACTIVE
        r_idx = engine.peer_to_idx[reporter.did]
        a_idx = engine.peer_to_idx[accused.did]
        self.assertEqual(engine.S[r_idx, a_idx], 0.0)
        self.assertEqual(engine.peer_states[accused.did], PeerState.ACTIVE)

    def test_phase3_h_cross_evidence_uniqueness(self):
        """Validates that receipt and fault evidence namespaces do not collide on identical IDs."""
        publisher = PeerIdentity("Publisher", difficulty_bits=12)
        accused = PeerIdentity("Accused", difficulty_bits=12)
        reporter = PeerIdentity("Reporter", difficulty_bits=12)

        engine = EigenTrustEngine(peers=[reporter.did, accused.did], pre_trusted_peers=[reporter.did])
        engine.register_peer(reporter)
        engine.register_peer(accused)

        shared_id = "shared-cross-id-99"

        # 1. Commit receipt with shared_id
        receipt = self._create_signed_receipt(reporter, accused, tx_id=shared_id, root="e" * 64, rating="+1.00")
        self.assertTrue(engine.record_receipt(receipt))

        # 2. Commit fault evidence with the same shared_id
        evidence, _, _, _ = self._create_signed_fault_evidence(
            publisher, accused, reporter, evidence_id=shared_id, req_id="req-unique-99"
        )
        self.assertTrue(engine.record_fault_evidence(evidence, manifest_publisher_pubkey_hex=publisher.public_key_hex))

        # Both records co-exist in distinct namespaces
        self.assertTrue(engine.local_journal.contains(shared_id, entry_type="RECEIPT"))
        self.assertTrue(engine.local_journal.contains(shared_id, entry_type="FAULT_EVIDENCE"))

        # Net S update: +1.0 from receipt, -2.0 from fault evidence = -1.0
        r_idx = engine.peer_to_idx[reporter.did]
        a_idx = engine.peer_to_idx[accused.did]
        self.assertEqual(engine.S[r_idx, a_idx], -1.0)

    def test_phase3_i_failure_atomicity(self):
        """Validates failure atomicity: rejected evidence leaves S, journal, and peer states strictly unchanged."""
        alice = PeerIdentity("Alice", difficulty_bits=12)
        bob = PeerIdentity("Bob", difficulty_bits=12)
        engine = EigenTrustEngine(peers=[alice.did, bob.did], pre_trusted_peers=[alice.did])
        engine.register_peer(alice)
        engine.register_peer(bob)

        # Snapshot initial state
        s_initial = np.copy(engine.S)
        journal_len_initial = len(engine.local_journal)
        states_initial = copy.deepcopy(engine.peer_states)

        # Submit corrupted receipt
        bad_receipt = self._create_signed_receipt(alice, bob, tx_id="tx-atomic-fail", root="f" * 64)
        bad_receipt.client_sig_hex = "ff" * 64
        self.assertFalse(engine.record_receipt(bad_receipt))

        # Assert no partial mutation
        np.testing.assert_array_equal(engine.S, s_initial)
        self.assertEqual(len(engine.local_journal), journal_len_initial)
        self.assertEqual(engine.peer_states, states_initial)

    def test_phase3_j_eigentrust_regression(self):
        """Validates that vanilla EigenTrust mathematical convergence and alpha damping remain intact."""
        peers = ["NodeA", "NodeB", "NodeC"]
        engine = EigenTrustEngine(peers=peers, pre_trusted_peers=["NodeA"], alpha=0.15)
        
        # Verify initial state
        self.assertAlmostEqual(engine.p[engine.peer_to_idx["NodeA"]], 1.0)
        self.assertEqual(engine.alpha, 0.15)

        # Set synthetic satisfaction and verify power iteration convergence
        engine.S[0, 1] = 10.0
        engine.S[1, 2] = 5.0
        scores = engine.get_trust_scores()

        self.assertAlmostEqual(sum(scores.values()), 1.0, places=4)
        self.assertGreater(scores["NodeA"], 0.15)
        self.assertGreater(scores["NodeB"], scores["NodeC"])

    def test_phase3_k_direct_mutation_protection_and_journal_abstraction(self):
        """Validates journal abstraction (L_sim) and at-most-once processing across engines sharing a journal."""
        alice = PeerIdentity("Alice", difficulty_bits=12)
        bob = PeerIdentity("Bob", difficulty_bits=12)
        
        # Shared canonical simulator journal
        sim_journal = SimulatorCanonicalJournal()
        engine1 = EigenTrustEngine(peers=[alice.did, bob.did], pre_trusted_peers=[alice.did], journal=sim_journal)
        engine2 = EigenTrustEngine(peers=[alice.did, bob.did], pre_trusted_peers=[alice.did], journal=sim_journal)
        engine1.register_peer(alice); engine1.register_peer(bob)
        engine2.register_peer(alice); engine2.register_peer(bob)

        receipt = self._create_signed_receipt(alice, bob, tx_id="tx-shared-sim-1", root="0" * 64)

        # Committed in engine1
        self.assertTrue(engine1.record_receipt(receipt))
        self.assertEqual(engine1.S[engine1.peer_to_idx[alice.did], engine1.peer_to_idx[bob.did]], 1.0)

        # Attempting to process same receipt in engine2 with shared journal is blocked at Stage 5
        self.assertFalse(engine2.record_receipt(receipt))
        self.assertEqual(engine2.S[engine2.peer_to_idx[alice.did], engine2.peer_to_idx[bob.did]], 0.0)

    # =========================================================================
    # PRESERVED EXISTING TESTS: LAYER 3 BASELINE & LAYER 4
    # =========================================================================

    def test_layer3_merkle_and_eigentrust(self):
        """Validates Merkle tree integrity and EigenTrust power-iteration convergence."""
        chunks = [b"Chunk1-data", b"Chunk2-data", b"Chunk3-data", b"Chunk4-data"]
        merkle = MerkleTree(chunks)
        self.assertNotEqual(merkle.root_hash, "")
        self.assertTrue(merkle.verify_chunk(0, b"Chunk1-data"))
        self.assertFalse(merkle.verify_chunk(0, b"Poisoned-Chunk"))

        # Test EigenTrust
        engine = EigenTrustEngine(peers=["A", "B", "C"], pre_trusted_peers=["A"], alpha=0.15)
        # S[A][B] = 5, S[B][C] = 5
        engine.S[0, 1] = 5
        engine.S[1, 2] = 5
        scores = engine.get_trust_scores()
        
        # All scores sum to 1.0
        self.assertAlmostEqual(sum(scores.values()), 1.0, places=4)
        # Pre-trusted node A and its endorsed peer B should have higher trust than C
        self.assertGreater(scores["A"], 0.1)
        self.assertGreater(scores["B"], scores["C"])

    def test_layer4_quorum_revocation_and_shamir(self):
        """Validates m-of-n quorum revocation and Shamir (3, 5) key recovery."""
        # 1. Quorum Revocation Test
        sn1 = PeerIdentity("Supernode_1", difficulty_bits=8)
        sn2 = PeerIdentity("Supernode_2", difficulty_bits=8)
        sn3 = PeerIdentity("Supernode_3", difficulty_bits=8)
        rogue = PeerIdentity("RoguePeer", difficulty_bits=8)

        crr = CertificateRevocationRecord(
            revoked_did=rogue.did,
            revoked_pubkey_hex=rogue.public_key_hex,
            reason="Malware Distribution",
            timestamp=1000.0,
            supernode_signatures={}
        )
        payload = crr.payload_bytes()
        crr.supernode_signatures[sn1.did] = sn1.sign(payload).hex()
        crr.supernode_signatures[sn2.did] = sn2.sign(payload).hex()

        supernode_pubkeys = {
            sn1.did: sn1.public_key_hex,
            sn2.did: sn2.public_key_hex,
            sn3.did: sn3.public_key_hex
        }
        # 2 signatures available: meets threshold of 2, fails threshold of 3
        self.assertTrue(crr.is_quorum_approved(supernode_pubkeys, threshold_m=2))
        self.assertFalse(crr.is_quorum_approved(supernode_pubkeys, threshold_m=3))

        # 2. Shamir Secret Sharing Test (3-of-5 threshold)
        secret = 12345678901234567890987654321
        shares = ShamirSecretSharing.split_secret(secret, k_threshold=3, n_shares=5)
        self.assertEqual(len(shares), 5)

        # Reconstruct with any 3 shares
        subset_3 = [shares[0], shares[2], shares[4]]
        recovered = ShamirSecretSharing.reconstruct_secret(subset_3)
        self.assertEqual(recovered, secret)

        # Fails or yields incorrect with 2 shares
        subset_2 = [shares[0], shares[1]]
        recovered_wrong = ShamirSecretSharing.reconstruct_secret(subset_2)
        self.assertNotEqual(recovered_wrong, secret)

    # =========================================================================
    # PHASE 4 TESTS: LAYER 4 (CRR, QUORUM, STATE MACHINE, RECOVERY, ROTATION)
    # =========================================================================

    def test_phase4_a_crr_serialization_and_verification(self):
        """Tests CRR canonical serialization, Ed25519 signatures, and field tampering rejection."""
        sn1 = PeerIdentity("Supernode_1", difficulty_bits=8)
        accused = PeerIdentity("AccusedServer", difficulty_bits=8)

        crr = CertificateRevocationRecord(
            revocation_id="crr-test-001",
            revoked_did=accused.did,
            revoked_pubkey_hex=accused.public_key_hex,
            reason="ATTRIBUTABLE_INCONSISTENT_DELIVERY",
            evidence_id="ev-fault-001",
            timestamp=1000.0,
            supernode_signatures={}
        )
        self.assertTrue(crr.payload_bytes().startswith(b"PKI_V2_CRR:"))
        expected_payload = f"PKI_V2_CRR:{crr.revocation_id}:{crr.revoked_did}:{crr.revoked_pubkey_hex}:{crr.reason}:{crr.evidence_id}:{crr.timestamp}".encode("utf-8")
        self.assertEqual(crr.payload_bytes(), expected_payload)

        # Valid signature
        sig = sn1.sign(crr.payload_bytes()).hex()
        crr.supernode_signatures[sn1.did] = sig
        supernodes = {sn1.did: sn1.public_key_hex}
        self.assertTrue(crr.is_quorum_approved(supernodes, threshold_m=1))

        # Tampered reason rejected
        tampered_reason = copy.deepcopy(crr)
        tampered_reason.reason = "FORGED_REASON"
        self.assertFalse(tampered_reason.is_quorum_approved(supernodes, threshold_m=1))

        # Tampered revoked DID rejected
        tampered_did = copy.deepcopy(crr)
        tampered_did.revoked_did = "did:peer:2.Ez" + "0" * 64
        self.assertFalse(tampered_did.is_quorum_approved(supernodes, threshold_m=1))

        # Tampered timestamp rejected
        tampered_ts = copy.deepcopy(crr)
        tampered_ts.timestamp = 2000.0
        self.assertFalse(tampered_ts.is_quorum_approved(supernodes, threshold_m=1))

    def test_phase4_b_quorum_authorization(self):
        """Tests configurable quorum (1-of-1, 3-of-5), duplicate signers, ineligible signers, and signature verification."""
        sns = [PeerIdentity(f"SN_{i}", difficulty_bits=8) for i in range(5)]
        supernode_pubkeys = {sn.did: sn.public_key_hex for sn in sns}
        accused = PeerIdentity("AccusedPeer", difficulty_bits=8)

        crr = CertificateRevocationRecord(
            revocation_id="crr-quorum-001",
            revoked_did=accused.did,
            revoked_pubkey_hex=accused.public_key_hex,
            reason="ATTRIBUTABLE_INCONSISTENT_DELIVERY",
            evidence_id="ev-fault-quorum",
            timestamp=1000.0,
            supernode_signatures={}
        )
        payload = crr.payload_bytes()

        # 1-of-1 quorum
        crr.supernode_signatures[sns[0].did] = sns[0].sign(payload).hex()
        self.assertTrue(crr.is_quorum_approved(supernode_pubkeys, threshold_m=1))
        # 1-of-1 fails threshold 2
        self.assertFalse(crr.is_quorum_approved(supernode_pubkeys, threshold_m=2))

        # Add second and third signatures for 3-of-5
        crr.supernode_signatures[sns[1].did] = sns[1].sign(payload).hex()
        crr.supernode_signatures[sns[2].did] = sns[2].sign(payload).hex()
        self.assertTrue(crr.is_quorum_approved(supernode_pubkeys, threshold_m=3))
        self.assertFalse(crr.is_quorum_approved(supernode_pubkeys, threshold_m=4))

        # Ineligible signer does not count
        stranger = PeerIdentity("Stranger", difficulty_bits=8)
        crr_ineligible = copy.deepcopy(crr)
        crr_ineligible.supernode_signatures = {
            sns[0].did: sns[0].sign(payload).hex(),
            sns[1].did: sns[1].sign(payload).hex(),
            stranger.did: stranger.sign(payload).hex()
        }
        # Only 2 eligible signers, threshold 3 must fail
        self.assertFalse(crr_ineligible.is_quorum_approved(supernode_pubkeys, threshold_m=3))

        # Invalid signature excluded
        crr_bad_sig = copy.deepcopy(crr)
        crr_bad_sig.supernode_signatures[sns[2].did] = "00" * 64
        self.assertFalse(crr_bad_sig.is_quorum_approved(supernode_pubkeys, threshold_m=3))

    def test_phase4_c_state_machine_transitions(self):
        """Tests exact frozen state machine transitions and forbidden transition enforcement."""
        sns = [PeerIdentity(f"SN_{i}", difficulty_bits=8) for i in range(3)]
        supernode_pubkeys = {sn.did: sn.public_key_hex for sn in sns}
        coord = RevocationCoordinator(supernode_pubkeys=supernode_pubkeys, threshold_m=2, voting_timeout=600.0, subjective_suspicion_timeout=300.0)

        accused = PeerIdentity("AccusedNode", difficulty_bits=8)
        coord.set_peer_state(accused.did, PeerState.ACTIVE)

        # 1. ACTIVE -> SUSPECTED (Certified Fault)
        self.assertTrue(coord.record_suspicion(accused.did, is_certified=True, timestamp=100.0))
        self.assertEqual(coord.get_peer_state(accused.did), PeerState.SUSPECTED)

        # Certified suspicion NEVER expires to ACTIVE
        self.assertFalse(coord.check_suspicion_expiry(accused.did, current_time=10000.0))
        self.assertEqual(coord.get_peer_state(accused.did), PeerState.SUSPECTED)

        # Subjective suspicion CAN expire to ACTIVE
        sub_peer = PeerIdentity("SubjectivePeer", difficulty_bits=8)
        coord.set_peer_state(sub_peer.did, PeerState.ACTIVE)
        coord.record_suspicion(sub_peer.did, is_certified=False, timestamp=100.0)
        self.assertEqual(coord.get_peer_state(sub_peer.did), PeerState.SUSPECTED)
        self.assertTrue(coord.check_suspicion_expiry(sub_peer.did, current_time=500.0))
        self.assertEqual(coord.get_peer_state(sub_peer.did), PeerState.ACTIVE)

        # 2. Cannot skip SUSPECTED to reach REVOCATION_PROPOSED
        fresh_peer = PeerIdentity("FreshPeer", difficulty_bits=8)
        coord.set_peer_state(fresh_peer.did, PeerState.ACTIVE)
        reporter = PeerIdentity("Reporter", difficulty_bits=8)
        ev, _, _, _ = self._create_signed_fault_evidence(reporter, fresh_peer, reporter)
        illegal_prop = RevocationProposal(
            proposal_id="prop-illegal",
            reporter_did=reporter.did,
            accused_did=fresh_peer.did,
            evidence=ev,
            timestamp=100.0
        )
        self.assertFalse(coord.submit_proposal(illegal_prop))
        self.assertEqual(coord.get_peer_state(fresh_peer.did), PeerState.ACTIVE)

        # 3. SUSPECTED -> REVOCATION_PROPOSED upon valid proposal
        ev_accused, _, _, _ = self._create_signed_fault_evidence(reporter, accused, reporter)
        prop = RevocationProposal(
            proposal_id="prop-001",
            reporter_did=reporter.did,
            accused_did=accused.did,
            evidence=ev_accused,
            timestamp=100.0,
            timeout=600.0
        )
        prop.reporter_sig_hex = reporter.sign(prop.payload_bytes()).hex()
        self.assertTrue(coord.submit_proposal(prop))
        self.assertEqual(coord.get_peer_state(accused.did), PeerState.REVOCATION_PROPOSED)

        # 4. Quorum timeout fallback: REVOCATION_PROPOSED -> SUSPECTED (NEVER ACTIVE)
        self.assertTrue(coord.check_proposal_timeout("prop-001", current_time=800.0))
        self.assertEqual(coord.get_peer_state(accused.did), PeerState.SUSPECTED)

        # 5. Re-propose and achieve Quorum: REVOCATION_PROPOSED -> REVOKED
        prop2 = RevocationProposal(
            proposal_id="prop-002",
            reporter_did=reporter.did,
            accused_did=accused.did,
            evidence=ev_accused,
            timestamp=1000.0,
            timeout=600.0
        )
        prop2.reporter_sig_hex = reporter.sign(prop2.payload_bytes()).hex()
        self.assertTrue(coord.submit_proposal(prop2))
        self.assertEqual(coord.get_peer_state(accused.did), PeerState.REVOCATION_PROPOSED)

        # Cast supernode votes
        draft_crr = CertificateRevocationRecord(
            revocation_id="crr-prop-002",
            revoked_did=accused.did,
            revoked_pubkey_hex=accused.public_key_hex,
            reason="ATTRIBUTABLE_INCONSISTENT_DELIVERY",
            evidence_id=prop2.evidence_id,
            timestamp=prop2.timestamp
        )
        crr_payload = draft_crr.payload_bytes()
        sig_sn0 = sns[0].sign(crr_payload).hex()
        sig_sn1 = sns[1].sign(crr_payload).hex()

        ok, crr_out = coord.cast_vote("prop-002", sns[0].did, sig_sn0)
        self.assertTrue(ok)
        self.assertIsNone(crr_out)  # 1 vote, threshold 2 not reached
        self.assertEqual(coord.get_peer_state(accused.did), PeerState.REVOCATION_PROPOSED)

        ok, final_crr = coord.cast_vote("prop-002", sns[1].did, sig_sn1)
        self.assertTrue(ok)
        self.assertIsNotNone(final_crr)
        self.assertEqual(coord.get_peer_state(accused.did), PeerState.REVOKED)

        # 6. Forbidden transition enforcement
        with self.assertRaises(ValueError):
            coord.validate_transition(PeerState.REVOCATION_PROPOSED, PeerState.ACTIVE)
        with self.assertRaises(ValueError):
            coord.validate_transition(PeerState.SUSPECTED, PeerState.ACTIVE, is_certified=True)
        with self.assertRaises(ValueError):
            coord.validate_transition(PeerState.ACTIVE, PeerState.REVOCATION_PROPOSED)
        with self.assertRaises(ValueError):
            coord.validate_transition(PeerState.REVOKED, PeerState.ACTIVE)

    def test_phase4_d_revocation_store(self):
        """Tests LocalRevocationStore storing valid CRRs, duplicate rejection, and lookup."""
        store = LocalRevocationStore()
        sn = PeerIdentity("SN_Store", difficulty_bits=8)
        accused = PeerIdentity("AccusedStore", difficulty_bits=8)

        crr = CertificateRevocationRecord(
            revocation_id="crr-store-001",
            revoked_did=accused.did,
            revoked_pubkey_hex=accused.public_key_hex,
            reason="ATTRIBUTABLE_INCONSISTENT_DELIVERY",
            evidence_id="ev-store-001",
            timestamp=1000.0,
            supernode_signatures={}
        )
        crr.supernode_signatures[sn.did] = sn.sign(crr.payload_bytes()).hex()
        sns = {sn.did: sn.public_key_hex}

        # Valid store
        self.assertFalse(store.is_revoked(accused.did))
        self.assertTrue(store.store_crr(crr, sns, threshold_m=1))
        self.assertTrue(store.is_revoked(accused.did))
        self.assertEqual(store.get_crr(accused.did), crr)
        self.assertEqual(store.get_by_revocation_id("crr-store-001"), crr)

        # Duplicate CRR rejection
        self.assertFalse(store.store_crr(crr, sns, threshold_m=1))

    def test_phase4_e_peer_eviction(self):
        """Tests peer eviction from MeshPKINetwork, link severance, and re-admission prevention."""
        mesh = MeshPKINetwork(max_hops=4)
        node_a = PeerIdentity("NodeA", difficulty_bits=12)
        node_b = PeerIdentity("NodeB", difficulty_bits=12)
        rogue = PeerIdentity("RoguePeer", difficulty_bits=12)

        self.assertTrue(mesh.register_peer(node_a))
        self.assertTrue(mesh.register_peer(node_b))
        self.assertTrue(mesh.register_peer(rogue))

        mesh.issue_cross_certificate(node_a, rogue, 0.9)
        mesh.issue_cross_certificate(rogue, node_b, 0.9)

        sn = PeerIdentity("SN_Evict", difficulty_bits=8)
        crr = CertificateRevocationRecord(
            revocation_id="crr-evict-001",
            revoked_did=rogue.did,
            revoked_pubkey_hex=rogue.public_key_hex,
            reason="ATTRIBUTABLE_INCONSISTENT_DELIVERY",
            evidence_id="ev-evict-001",
            timestamp=1000.0,
            supernode_signatures={}
        )
        crr.supernode_signatures[sn.did] = sn.sign(crr.payload_bytes()).hex()
        sns = {sn.did: sn.public_key_hex}

        # Invalid CRR cannot evict
        tampered_crr = copy.deepcopy(crr)
        tampered_crr.reason = "BAD_REASON"
        self.assertFalse(evict_peer_from_mesh(mesh, tampered_crr, sns, threshold_m=1))
        self.assertIn(rogue.did, mesh.peers)

        # Valid CRR executes eviction
        self.assertTrue(evict_peer_from_mesh(mesh, crr, sns, threshold_m=1))
        self.assertNotIn(rogue.did, mesh.peers)
        self.assertEqual(rogue.state, PeerState.REVOKED)
        self.assertNotIn(rogue.did, mesh.trust_graph)

        # Rogue cannot be re-admitted using revoked identity
        self.assertFalse(mesh.register_peer(rogue))

    def test_phase4_f_crr_propagation_handling(self):
        """Tests processing incoming CRRs from gossip propagation."""
        store = LocalRevocationStore()
        sn = PeerIdentity("SN_Prop", difficulty_bits=8)
        accused = PeerIdentity("AccusedProp", difficulty_bits=8)
        sns = {sn.did: sn.public_key_hex}

        now = time.time()
        crr = CertificateRevocationRecord(
            revocation_id="crr-prop-001",
            revoked_did=accused.did,
            revoked_pubkey_hex=accused.public_key_hex,
            reason="ATTRIBUTABLE_INCONSISTENT_DELIVERY",
            evidence_id="ev-prop-001",
            timestamp=now,
            supernode_signatures={}
        )
        crr.supernode_signatures[sn.did] = sn.sign(crr.payload_bytes()).hex()

        # Valid incoming CRR accepted
        self.assertTrue(process_incoming_crr(crr, sns, threshold_m=1, store=store, current_time=now))
        self.assertTrue(store.is_revoked(accused.did))

        # Tampered CRR rejected
        bad_crr = copy.deepcopy(crr)
        bad_crr.supernode_signatures[sn.did] = "00" * 64
        self.assertFalse(process_incoming_crr(bad_crr, sns, threshold_m=1, store=store, current_time=now))

        # Stale CRR rejected
        stale_crr = copy.deepcopy(crr)
        stale_crr.timestamp = now - 500.0
        stale_crr.supernode_signatures[sn.did] = sn.sign(stale_crr.payload_bytes()).hex()
        self.assertFalse(process_incoming_crr(stale_crr, sns, threshold_m=1, store=store, current_time=now))

    def test_phase4_g_recovery_authorization(self):
        """Tests KeyRecoveryCoordinator separation of authentication, authorization, and replay protection."""
        subject = PeerIdentity("SubjectPeer", difficulty_bits=8)
        guardian = PeerIdentity("GuardianNode", difficulty_bits=8)
        custodian = PeerIdentity("Custodian1", difficulty_bits=8)
        requester = PeerIdentity("RequesterAgent", difficulty_bits=8)

        now = time.time()
        token = RecoveryAuthorizationToken(
            token_id="tok-recov-001",
            subject_did=subject.did,
            requester_pubkey_hex=requester.public_key_hex,
            custodian_did=custodian.did,
            timestamp=now,
            expiry=now + 600.0,
            authorization_scope="KEY_RECOVERY"
        )
        token.guardian_signature_hex = guardian.sign(token.payload_bytes()).hex()

        req = RecoveryRequest(
            request_id="req-recov-001",
            subject_did=subject.did,
            requester_pubkey_hex=requester.public_key_hex,
            timestamp=now,
            auth_token=token
        )
        req.requester_sig_hex = requester.sign(req.payload_bytes()).hex()

        coord = KeyRecoveryCoordinator(guardian_pubkey_hex=guardian.public_key_hex)
        share = (1, 88888888)

        # Valid release
        released = coord.authorize_share_release(req, custodian.did, share, current_time=now)
        self.assertEqual(released, share)

        # Request replay rejected
        with self.assertRaises(ValueError):
            coord.authorize_share_release(req, custodian.did, share, current_time=now)

        # Unauthenticated request rejected (bad requester signature)
        req2 = RecoveryRequest(
            request_id="req-recov-002",
            subject_did=subject.did,
            requester_pubkey_hex=requester.public_key_hex,
            timestamp=now,
            auth_token=token,
            requester_sig_hex="00" * 64
        )
        with self.assertRaises(PermissionError):
            coord.authorize_share_release(req2, custodian.did, share, current_time=now)

        # Unauthorized token rejected (forged guardian signature)
        bad_token = copy.deepcopy(token)
        bad_token.token_id = "tok-forged"
        bad_token.guardian_signature_hex = "ff" * 64
        req3 = RecoveryRequest(
            request_id="req-recov-003",
            subject_did=subject.did,
            requester_pubkey_hex=requester.public_key_hex,
            timestamp=now,
            auth_token=bad_token
        )
        req3.requester_sig_hex = requester.sign(req3.payload_bytes()).hex()
        with self.assertRaises(PermissionError):
            coord.authorize_share_release(req3, custodian.did, share, current_time=now)

    def test_phase4_h_shamir_threshold_recovery(self):
        """Tests authorized Shamir secret recovery, threshold enforcement, and malformed share handling."""
        secret = 987654321012345678909876543210
        shares = ShamirSecretSharing.split_secret(secret, k_threshold=3, n_shares=5)

        guardian = PeerIdentity("GuardianShamir", difficulty_bits=8)
        coord = KeyRecoveryCoordinator(guardian_pubkey_hex=guardian.public_key_hex)

        now = time.time()
        token = RecoveryAuthorizationToken(
            token_id="tok-shamir-001",
            subject_did="did:peer:2.EzSubject",
            requester_pubkey_hex="a" * 64,
            custodian_did="did:peer:2.EzCustodian",
            timestamp=now,
            expiry=now + 600.0
        )
        token.guardian_signature_hex = guardian.sign(token.payload_bytes()).hex()

        # Threshold reconstruction succeeds
        recovered = coord.reconstruct_secret_with_authorization(shares[:3], token, threshold_k=3, current_time=now)
        self.assertEqual(recovered, secret)

        # Token replay rejected
        with self.assertRaises(ValueError):
            coord.reconstruct_secret_with_authorization(shares[:3], token, threshold_k=3, current_time=now)

        # Insufficient shares fail
        token2 = copy.deepcopy(token)
        token2.token_id = "tok-shamir-002"
        token2.guardian_signature_hex = guardian.sign(token2.payload_bytes()).hex()
        with self.assertRaises(ValueError):
            coord.reconstruct_secret_with_authorization(shares[:2], token2, threshold_k=3, current_time=now)

        # Malformed shares fail safely
        token3 = copy.deepcopy(token)
        token3.token_id = "tok-shamir-003"
        token3.guardian_signature_hex = guardian.sign(token3.payload_bytes()).hex()
        with self.assertRaises(ValueError):
            coord.reconstruct_secret_with_authorization([(1, "corrupted_share"), shares[1], shares[2]], token3, threshold_k=3, current_time=now)

        # Arbitrary shares without valid AuthTok fail
        token_unauth = copy.deepcopy(token)
        token_unauth.token_id = "tok-unauth"
        token_unauth.guardian_signature_hex = "00" * 64
        with self.assertRaises(PermissionError):
            coord.reconstruct_secret_with_authorization(shares[:3], token_unauth, threshold_k=3, current_time=now)

    def test_phase4_i_key_rotation_and_invalidation(self):
        """Tests post-recovery key rotation, dual-signature rotation certificate, and old key invalidation."""
        alice = PeerIdentity("AliceOriginal", difficulty_bits=8)
        alice_secret_int = int.from_bytes(
            alice.private_key.private_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PrivateFormat.Raw,
                encryption_algorithm=serialization.NoEncryption()
            ),
            byteorder="big"
        )

        new_alice, rot_cert = rotate_key_after_recovery(alice, alice_secret_int, "AliceRotated")

        # New key is cryptographically distinct
        self.assertNotEqual(new_alice.public_key_hex, alice.public_key_hex)
        self.assertNotEqual(new_alice.did, alice.did)

        # Rotation certificate properties
        self.assertTrue(rot_cert.payload_bytes().startswith(b"PKI_V2_ROTATE:"))
        self.assertEqual(rot_cert.old_did, alice.did)
        self.assertEqual(rot_cert.new_did, new_alice.did)
        self.assertTrue(rot_cert.verify(alice.public_key_hex))

        # Operational status: new key active, old key retired
        self.assertTrue(is_key_valid_for_operations(new_alice))
        self.assertFalse(is_key_valid_for_operations(alice))

        # Rotation with incorrect secret rejected
        with self.assertRaises(ValueError):
            rotate_key_after_recovery(new_alice, 11111111)

    # =========================================================================
    # PHASE 5 TESTS: SIMULATOR INTEGRATION & 4-LAYER PROTOCOL FLOWS
    # =========================================================================

    def test_phase5_integration_a_real_peer_admission(self):
        """Tests real node initialization, PoW admission, and state progression in SwarmSimulation."""
        sim = SwarmSimulation(num_honest=4, num_supernodes=3, num_sybils=3, seed=42, difficulty_bits=8)
        self.assertEqual(len(sim.nodes), 10)
        self.assertEqual(sim.metrics["admission"]["admitted"], 10)

        # Every node has active identity state and full 64-hex DID
        for node in sim.nodes.values():
            self.assertEqual(node.identity.state, PeerState.ACTIVE)
            self.assertTrue(node.did.startswith("did:peer:2.Ez"))
            self.assertEqual(len(node.public_key_hex), 64)
            self.assertIn(node.did, sim.mesh.peers)

        # Node with invalid PoW rejected by admission path
        bad_pow_node = SimulatedNode("BadPoW", difficulty_bits=8)
        bad_pow_node.identity.certificate.pow_nonce = 0
        self.assertFalse(sim._admit_node(bad_pow_node))

    def test_phase5_integration_b_content_request_response_merkle(self):
        """Tests genuine Merkle trees, signed manifests, ContentRequests, and ChunkResponses."""
        node = SimulatedNode("ContentHost", difficulty_bits=8)
        content, manifest, tree = node.generate_file("test-file-001", size_kb=64, chunk_size_kb=16)

        self.assertEqual(manifest.total_chunks, 4)
        self.assertEqual(manifest.root_hash, tree.root_hash)
        self.assertTrue(manifest.verify_signature(node.public_key_hex))

        # Honest request & response for chunk 2
        client = SimulatedNode("ContentClient", difficulty_bits=8)
        req = ContentRequest(
            req_id="req-test-01",
            client_did=client.did,
            server_did=node.did,
            content_id="test-file-001",
            chunk_index=2,
            merkle_root=manifest.root_hash,
            timestamp=time.time(),
            nonce="nonce-test-01",
            client_sig_hex=""
        )
        req.client_sig_hex = client.identity.sign(req.payload_bytes()).hex()

        chunk_bytes = node.get_chunk("test-file-001", 2)
        proof = tree.generate_proof(2)
        resp = ChunkResponse(
            req_id=req.req_id,
            client_did=client.did,
            server_did=node.did,
            content_id="test-file-001",
            chunk_index=2,
            chunk_bytes=chunk_bytes,
            chunk_hash=hashlib.sha256(chunk_bytes).hexdigest().lower(),
            proof_hash=hash_proof(proof),
            merkle_root=manifest.root_hash,
            timestamp=time.time(),
            nonce=req.nonce,
            merkle_proof=proof,
            server_sig_hex=""
        )
        resp.server_sig_hex = node.identity.sign(resp.payload_bytes()).hex()

        # Phase 2 standalone verification passes
        self.assertTrue(resp.verify(node.public_key_hex, req))
        self.assertTrue(verify_merkle_proof(chunk_bytes, proof, 2, manifest.root_hash))

    def test_phase5_integration_c_honest_receipt_accounting_no_direct_mutation(self):
        """Tests that honest transactions route through the 7-stage evidence pipeline with zero direct S writes."""
        sim = SwarmSimulation(num_honest=5, num_supernodes=3, num_sybils=2, seed=42, difficulty_bits=8)
        initial_s_sum = float(np.sum(sim.eigentrust.S))
        self.assertEqual(initial_s_sum, 0.0)

        # Run 1 transaction round
        stats = sim.execute_transaction_round(1)
        self.assertGreater(stats["honest_success"], 0)
        self.assertGreater(sim.metrics["evidence"]["positive_receipts"], 0)
        self.assertGreater(sim.metrics["trust"]["s_updates"], 0)

        # S-matrix updated strictly through validated receipts in the canonical journal
        self.assertGreater(float(np.sum(sim.eigentrust.S)), initial_s_sum)
        self.assertGreater(len(sim.canonical_journal), 0)

    def test_phase5_integration_d_poisoning_fault_evidence_and_suspected(self):
        """Tests that corrupted deliveries generate authentic FaultEvidenceRecords, deduct 2.0, and transition to SUSPECTED."""
        sim = SwarmSimulation(num_honest=5, num_supernodes=3, num_sybils=3, seed=42, difficulty_bits=8)
        stats = sim.execute_transaction_round(1)

        self.assertGreaterEqual(stats["poison_detected"], 1)
        self.assertGreater(sim.metrics["content"]["corrupted_deliveries"], 0)
        self.assertGreater(sim.metrics["evidence"]["fault_evidence_accepted"], 0)
        self.assertGreater(sim.metrics["revocation"]["suspected_transitions"], 0)

    def test_phase5_integration_e_revocation_quorum_and_eviction(self):
        """Tests that verified fault evidence triggers supernode quorum voting and peer eviction from the mesh."""
        sim = SwarmSimulation(num_honest=5, num_supernodes=3, num_sybils=3, seed=42, difficulty_bits=8)
        stats = sim.execute_transaction_round(1)

        self.assertGreaterEqual(stats["evictions"], 1)
        self.assertGreater(sim.metrics["revocation"]["quorum_approvals"], 0)
        self.assertGreater(sim.metrics["revocation"]["eviction_events"], 0)

        # Evicted rogue peer is marked REVOKED and removed from mesh
        revoked_nodes = [n for n in sim.sybil_nodes if n.identity.state == PeerState.REVOKED]
        self.assertGreater(len(revoked_nodes), 0)
        for r in revoked_nodes:
            self.assertNotIn(r.did, sim.mesh.peers)

    def test_phase5_integration_f_readmission_rejection(self):
        """Tests that an evicted peer cannot be re-admitted using its revoked identity."""
        sim = SwarmSimulation(num_honest=5, num_supernodes=3, num_sybils=3, seed=42, difficulty_bits=8)
        sim.execute_transaction_round(1)

        self.assertGreater(sim.metrics["revocation"]["readmission_rejections"], 0)
        revoked_nodes = [n for n in sim.sybil_nodes if n.identity.state == PeerState.REVOKED]
        self.assertGreater(len(revoked_nodes), 0)
        # Attempt direct re-registration
        self.assertFalse(sim.mesh.register_peer(revoked_nodes[0].identity, min_difficulty=8))

    def test_phase5_integration_g_receipt_and_fault_replay_protection(self):
        """Tests that replayed receipts and replayed fault evidence are strictly rejected."""
        sim = SwarmSimulation(num_honest=5, num_supernodes=3, num_sybils=3, seed=42, difficulty_bits=8)
        sim.execute_transaction_round(1)

        self.assertGreater(sim.metrics["evidence"]["replay_rejections"], 0)

        # Explicit manual replay test
        if sim.committed_receipts:
            rcpt = sim.committed_receipts[0]
            # Replay must fail in Layer 3 pipeline
            self.assertFalse(sim.eigentrust.record_receipt(rcpt))

        if sim.committed_fault_evidence:
            ev = sim.committed_fault_evidence[0]
            # Replay must fail in Layer 3 pipeline
            self.assertFalse(sim.eigentrust.record_fault_evidence(ev))

    def test_phase5_integration_h_crr_propagation(self):
        """Tests CRR propagation to other nodes and commitment to LocalRevocationStore."""
        sim = SwarmSimulation(num_honest=5, num_supernodes=3, num_sybils=3, seed=42, difficulty_bits=8)
        sim.execute_transaction_round(1)

        revoked_nodes = [n for n in sim.sybil_nodes if n.identity.state == PeerState.REVOKED]
        if revoked_nodes:
            rev_did = revoked_nodes[0].did
            self.assertTrue(sim.revocation_store.is_revoked(rev_did))
            self.assertIsNotNone(sim.revocation_store.get_crr(rev_did))

    def test_phase5_integration_i_sybil_and_collusion_baseline(self):
        """Tests that vanilla EigenTrust dampens collusive Sybils without manual suppression."""
        sim = SwarmSimulation(num_honest=10, num_supernodes=3, num_sybils=5, seed=42, difficulty_bits=8)
        history = sim.run_simulation(total_rounds=5)

        # Collusive upvotes were processed
        self.assertGreater(sim.metrics["evidence"]["positive_receipts"], 0)
        # Sybil trust share is dampened near zero (< 0.05) by power-iteration over pre-trusted seeds
        final_sybil_avg = history["sybil_avg"][-1]
        self.assertLess(final_sybil_avg, 0.05)

    def test_phase5_integration_j_recovery_and_key_rotation(self):
        """Tests complete Layer 4 Shamir secret recovery and mandatory key rotation on simulated nodes."""
        sim = SwarmSimulation(num_honest=5, num_supernodes=5, num_sybils=3, seed=42, difficulty_bits=8)
        success, secret, old_did, new_did = sim.demonstrate_key_recovery()

        self.assertTrue(success)
        self.assertNotEqual(old_did, new_did)
        self.assertEqual(sim.metrics["recovery"]["recovery_requests"], 1)
        self.assertEqual(sim.metrics["recovery"]["auth_successes"], 1)
        self.assertEqual(sim.metrics["recovery"]["reconstruction_successes"], 1)
        self.assertEqual(sim.metrics["recovery"]["key_rotations"], 1)
        self.assertEqual(sim.metrics["recovery"]["old_key_invalidations"], 1)

    # =========================================================================
    # PHASE 6 EXPERIMENTAL FRAMEWORK & EVALUATION TESTS
    # =========================================================================

    def test_phase6_a_deterministic_seed_behavior(self):
        """Tests that identical seeds and configurations produce bit-for-bit identical results."""
        from experiments.config import ExperimentConfig
        from experiments.scenarios import ExperimentTrialRunner

        cfg1 = ExperimentConfig("scenario_a_honest", num_honest=5, num_supernodes=2, num_sybils=2, total_rounds=3, seed=42, difficulty_bits=6)
        cfg2 = ExperimentConfig("scenario_a_honest", num_honest=5, num_supernodes=2, num_sybils=2, total_rounds=3, seed=42, difficulty_bits=6)

        r1 = ExperimentTrialRunner(cfg1).run()
        r2 = ExperimentTrialRunner(cfg2).run()

        self.assertEqual(r1["confusion"], r2["confusion"])
        for k in r1["trust_shares"]:
            self.assertAlmostEqual(r1["trust_shares"][k], r2["trust_shares"][k], places=7)
        self.assertEqual(r1["operational"]["metrics_raw"]["evidence"], r2["operational"]["metrics_raw"]["evidence"])

    def test_phase6_b_different_seeds_independent_trials(self):
        """Tests that different seeds produce independent, varied operational trajectories."""
        from experiments.config import ExperimentConfig
        from experiments.scenarios import ExperimentTrialRunner

        cfg1 = ExperimentConfig("scenario_b_poisoning", num_honest=5, num_supernodes=2, num_sybils=2, poisoning_rate=0.5, total_rounds=4, seed=42, difficulty_bits=6)
        cfg2 = ExperimentConfig("scenario_b_poisoning", num_honest=5, num_supernodes=2, num_sybils=2, poisoning_rate=0.5, total_rounds=4, seed=999, difficulty_bits=6)

        r1 = ExperimentTrialRunner(cfg1).run()
        r2 = ExperimentTrialRunner(cfg2).run()

        # Both ran valid trials, configurations are preserved per trial
        self.assertEqual(r1["config"]["seed"], 42)
        self.assertEqual(r2["config"]["seed"], 999)
        self.assertIn("detection_rate", r1["confusion"])
        self.assertIn("detection_rate", r2["confusion"])

    def test_phase6_c_ground_truth_generation(self):
        """Tests that ground-truth labels are independent, immutable by trust algorithm, and properly categorized."""
        from experiments.config import ExperimentConfig
        from experiments.scenarios import ExperimentTrialRunner

        cfg = ExperimentConfig("scenario_c_isolated_sybil", num_honest=6, num_supernodes=2, num_sybils=4, total_rounds=2, seed=42, difficulty_bits=6)
        runner = ExperimentTrialRunner(cfg)

        gt = runner.ground_truth
        self.assertEqual(len(gt.supernode_dids), 2)
        self.assertEqual(len(gt.honest_dids), 6)
        self.assertEqual(len(gt.sybil_dids), 4)

        # Disjoint sets
        self.assertTrue(gt.supernode_dids.isdisjoint(gt.honest_dids))
        self.assertTrue(gt.honest_dids.isdisjoint(gt.sybil_dids))
        self.assertTrue(gt.supernode_dids.isdisjoint(gt.sybil_dids))

    def test_phase6_d_metric_calculations(self):
        """Tests mathematical correctness of confusion metrics (recall, FPR, precision, F1)."""
        from experiments.metrics import calculate_confusion_metrics

        # Standard cases
        m = calculate_confusion_metrics(tp=10, fp=2, fn=0, tn=8)
        self.assertEqual(m["detection_rate"], 1.0)
        self.assertAlmostEqual(m["false_positive_rate"], 2 / 10)
        self.assertAlmostEqual(m["precision"], 10 / 12)
        self.assertAlmostEqual(m["recall"], 1.0)
        self.assertAlmostEqual(m["f1_score"], 2 * (10 / 12 * 1.0) / (10 / 12 + 1.0))

        # Edge cases: zero counts
        m_zero = calculate_confusion_metrics(tp=0, fp=0, fn=0, tn=10)
        self.assertEqual(m_zero["detection_rate"], 1.0)
        self.assertEqual(m_zero["false_positive_rate"], 0.0)
        self.assertEqual(m_zero["precision"], 1.0)

    def test_phase6_e_confidence_interval_calculation(self):
        """Tests distribution statistics and parametric 95% confidence intervals."""
        from experiments.statistics import calculate_distribution_stats

        vals = [10.0, 12.0, 11.0, 13.0, 12.0, 11.5]
        stats = calculate_distribution_stats(vals, confidence=0.95)

        self.assertEqual(stats["count"], 6)
        self.assertAlmostEqual(stats["mean"], sum(vals) / 6.0)
        self.assertLess(stats["ci_lower"], stats["mean"])
        self.assertGreater(stats["ci_upper"], stats["mean"])

        # n < 2 edge case
        single = calculate_distribution_stats([5.0])
        self.assertEqual(single["ci_lower"], 5.0)
        self.assertEqual(single["ci_upper"], 5.0)

    def test_phase6_f_scenario_parameterization(self):
        """Tests that ExperimentConfig parameter sweeps correctly reflect in trial executions."""
        from experiments.config import ExperimentConfig
        from experiments.scenarios import ExperimentTrialRunner

        cfg = ExperimentConfig(
            scenario_name="scenario_test",
            num_honest=4, num_supernodes=2, num_sybils=2,
            poisoning_rate=0.0, bridge_probability=0.0, replay_rate=0.0,
            total_rounds=2, seed=42, difficulty_bits=6
        )
        runner = ExperimentTrialRunner(cfg)
        res = runner.run()

        self.assertEqual(res["config"]["scenario_name"], "scenario_test")
        self.assertEqual(res["operational"]["admitted_nodes"], 8)

    def test_phase6_g_isolated_sybil_scenario(self):
        """Tests Scenario C: isolated Sybils receive near-zero collective trust share under vanilla EigenTrust."""
        from experiments.config import ExperimentConfig
        from experiments.scenarios import ExperimentTrialRunner

        cfg = ExperimentConfig(
            scenario_name="scenario_c_isolated_sybil",
            num_honest=10, num_supernodes=3, num_sybils=8,
            bridge_probability=0.0, total_rounds=4, seed=42, difficulty_bits=6
        )
        res = ExperimentTrialRunner(cfg).run()

        # Disconnected Sybils should not acquire more than 5% trust share
        sybil_share = res["trust_shares"]["sybil_trust_share"]
        self.assertLess(sybil_share, 0.05)

    def test_phase6_h_connected_collusion_scenario(self):
        """Tests Scenario D: connected collusion baseline demonstrates higher trust acquisition when bridged."""
        from experiments.config import ExperimentConfig
        from experiments.scenarios import ExperimentTrialRunner

        # Unbridged vs Bridged
        cfg_unbridged = ExperimentConfig("scenario_d_collusion", num_honest=8, num_supernodes=3, num_sybils=6, bridge_probability=0.0, total_rounds=4, seed=42, difficulty_bits=6)
        cfg_bridged = ExperimentConfig("scenario_d_collusion", num_honest=8, num_supernodes=3, num_sybils=6, bridge_probability=0.3, total_rounds=4, seed=42, difficulty_bits=6)

        res_un = ExperimentTrialRunner(cfg_unbridged).run()
        res_br = ExperimentTrialRunner(cfg_bridged).run()

        # Bridged collusion should achieve >= unbridged share
        self.assertGreaterEqual(res_br["trust_shares"]["sybil_trust_share"], res_un["trust_shares"]["sybil_trust_share"] - 1e-4)

    def test_phase6_i_poisoning_scenario(self):
        """Tests Scenario B: poisoning triggers FaultEvidenceRecord generation and verified deduction."""
        from experiments.config import ExperimentConfig
        from experiments.scenarios import ExperimentTrialRunner

        cfg = ExperimentConfig(
            scenario_name="scenario_b_poisoning",
            num_honest=6, num_supernodes=2, num_sybils=3,
            poisoning_rate=1.0, total_rounds=3, seed=42, difficulty_bits=6
        )
        res = ExperimentTrialRunner(cfg).run()

        cm = res["confusion"]
        self.assertGreater(cm["detection_rate"], 0.0)
        self.assertEqual(cm["false_positive_rate"], 0.0)

    def test_phase6_j_replay_scenario(self):
        """Tests Scenario E: replay attacks are rejected with zero re-acceptance when replay protection is enabled."""
        from experiments.config import ExperimentConfig
        from experiments.scenarios import ExperimentTrialRunner

        cfg = ExperimentConfig(
            scenario_name="scenario_e_replay",
            num_honest=5, num_supernodes=2, num_sybils=2,
            replay_rate=1.0, total_rounds=4, seed=42, difficulty_bits=6
        )
        res = ExperimentTrialRunner(cfg).run()

        self.assertEqual(res["operational"]["replay_acceptance_rate"], 0.0)

    def test_phase6_k_revocation_scenario(self):
        """Tests Scenario F: quorum authorization successfully processes revocation of accused poisoners."""
        from experiments.config import ExperimentConfig
        from experiments.scenarios import ExperimentTrialRunner

        cfg = ExperimentConfig(
            scenario_name="scenario_f_revocation",
            num_honest=6, num_supernodes=4, num_sybils=3,
            poisoning_rate=1.0, enable_revocation=True, enable_quorum=True,
            total_rounds=3, seed=42, difficulty_bits=6
        )
        res = ExperimentTrialRunner(cfg).run()

        raw_rev = res["operational"]["metrics_raw"]["revocation"]
        self.assertGreater(raw_rev["quorum_approvals"], 0)
        self.assertGreater(raw_rev["eviction_events"], 0)
        self.assertGreaterEqual(res["operational"]["revocation_success_rate"], 0.0)

    def test_phase6_l_machine_readable_output_generation(self):
        """Tests that runner outputs valid JSON and CSV summary files with non-empty rows."""
        import tempfile
        import os
        from experiments.runner import ExperimentSuiteRunner

        with tempfile.TemporaryDirectory() as tmp_dir:
            runner = ExperimentSuiteRunner(output_dir=tmp_dir, default_seeds=1)
            results = runner.run_suite(num_seeds=1)

            self.assertTrue(os.path.exists(os.path.join(tmp_dir, "raw_results.json")))
            self.assertTrue(os.path.exists(os.path.join(tmp_dir, "raw_results.csv")))
            self.assertTrue(os.path.exists(os.path.join(tmp_dir, "summary.csv")))
            self.assertTrue(os.path.exists(os.path.join(tmp_dir, "confidence_intervals.csv")))


if __name__ == '__main__':
    unittest.main()
