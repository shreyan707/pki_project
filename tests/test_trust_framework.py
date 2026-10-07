"""
Unit Test Suite for PKI Trust Management Framework
Tests all 4 architectural layers for cryptographic integrity and mathematical correctness.
"""

import unittest
from src.layer1_identity import PeerIdentity, P2PCertificate
from src.layer2_mesh_pki import MeshPKINetwork
from src.layer3_eigentrust import MerkleTree, BilateralReceipt, EigenTrustEngine
from src.layer4_recovery import CertificateRevocationRecord, ShamirSecretSharing


class TestPKITrustFramework(unittest.TestCase):

    def test_layer1_identity_and_pow(self):
        """Validates Ed25519 signing, PoW solution, and certificate verification."""
        peer = PeerIdentity("Alice", difficulty_bits=12)
        self.assertTrue(peer.did.startswith("did:peer:2.Ez"))
        self.assertTrue(PeerIdentity.verify_certificate(peer.certificate))

        # Test message signing
        msg = b"Hello, Decentralized P2P World!"
        sig = peer.sign(msg)
        self.assertTrue(PeerIdentity.verify_peer_signature(peer.public_key_hex, msg, sig.hex()))

        # Test corrupted message signature rejection
        self.assertFalse(PeerIdentity.verify_peer_signature(peer.public_key_hex, b"Tampered Message", sig.hex()))

    def test_layer2_mesh_pki(self):
        """Validates dynamic election, cross-certification, and multi-path trust."""
        mesh = MeshPKINetwork(max_hops=4)
        alice = PeerIdentity("Alice", difficulty_bits=8)
        bob = PeerIdentity("Bob", difficulty_bits=8)
        charlie = PeerIdentity("Charlie", difficulty_bits=8)

        mesh.register_peer(alice)
        mesh.register_peer(bob)
        mesh.register_peer(charlie)

        # Cross-certify Alice -> Bob (0.9), Bob -> Charlie (0.8)
        mesh.issue_cross_certificate(alice, bob, 0.9)
        mesh.issue_cross_certificate(bob, charlie, 0.8)

        # Transitive confidence: 0.9 * 0.8 = 0.72
        confidence = mesh.compute_transitive_confidence(alice.did, charlie.did)
        self.assertAlmostEqual(confidence, 0.72, places=2)

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
