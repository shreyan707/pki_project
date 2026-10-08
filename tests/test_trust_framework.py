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
from src.layer1_identity import PeerIdentity, P2PCertificate, PeerState
from src.layer2_mesh_pki import MeshPKINetwork, CrossCertificate
from src.layer3_eigentrust import (
    MerkleTree, BilateralReceipt, EigenTrustEngine, MerkleProofStep,
    canonical_proof_str, hash_proof, verify_merkle_proof,
    ContentManifest, ContentRequest, ChunkResponse, FaultEvidenceRecord,
    LocalEvidenceJournal, SimulatorCanonicalJournal, JournalEntry
)
from src.layer4_recovery import CertificateRevocationRecord, ShamirSecretSharing


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


if __name__ == '__main__':
    unittest.main()
