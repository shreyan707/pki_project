"""
Layer 1: Identity & Key Lifecycle Management Layer
Implements Self-Sovereign Identity using Ed25519 asymmetric cryptography,
Proof-of-Work (PoW) Sybil deterrence, and W3C did:peer structured certificates.
"""

import time
import hashlib
import json
from dataclasses import dataclass, asdict
from typing import Dict, Any, Tuple
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature


@dataclass
class P2PCertificate:
    did: str
    public_key_hex: str
    alias: str
    timestamp: float
    pow_nonce: int
    pow_difficulty: int
    capabilities: Dict[str, Any]
    signature_hex: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PeerIdentity:
    def __init__(self, alias: str, difficulty_bits: int = 16):
        self.alias = alias
        self.difficulty_bits = difficulty_bits
        
        # 1. Generate Ed25519 keypair
        self.private_key = ed25519.Ed25519PrivateKey.generate()
        self.public_key = self.private_key.public_key()
        
        # Public key raw bytes and hex representation
        pub_bytes = self.public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        self.public_key_hex = pub_bytes.hex()
        
        # 2. W3C did:peer representation
        self.did = f"did:peer:2.Ez{self.public_key_hex[:32]}"
        
        # 3. Solve Proof-of-Work
        self.pow_nonce, self.pow_hash = self._solve_pow()
        
        # 4. Assemble and self-sign Certificate
        self.certificate = self._generate_certificate()

    def _solve_pow(self) -> Tuple[int, str]:
        """
        Solves SHA-256(PublicKey || Alias || Nonce) < Target.
        difficulty_bits defines the required number of leading zero bits.
        """
        nonce = 0
        target_prefix = "0" * (self.difficulty_bits // 4)
        while True:
            payload = f"{self.public_key_hex}:{self.alias}:{nonce}".encode("utf-8")
            digest = hashlib.sha256(payload).hexdigest()
            if digest.startswith(target_prefix):
                return nonce, digest
            nonce += 1

    def sign(self, message: bytes) -> bytes:
        """Signs arbitrary bytes using private Ed25519 key."""
        return self.private_key.sign(message)

    def _generate_certificate(self) -> P2PCertificate:
        """Constructs self-signed P2P certificate."""
        now = time.time()
        capabilities = {
            "bandwidth_mbps": 100,
            "storage_gb": 50,
            "protocol_version": "2.0-pki"
        }
        unsigned_data = f"{self.did}:{self.public_key_hex}:{self.alias}:{now}:{self.pow_nonce}:{self.difficulty_bits}:{json.dumps(capabilities, sort_keys=True)}"
        signature = self.sign(unsigned_data.encode("utf-8"))
        
        return P2PCertificate(
            did=self.did,
            public_key_hex=self.public_key_hex,
            alias=self.alias,
            timestamp=now,
            pow_nonce=self.pow_nonce,
            pow_difficulty=self.difficulty_bits,
            capabilities=capabilities,
            signature_hex=signature.hex()
        )

    @staticmethod
    def verify_pow(public_key_hex: str, alias: str, nonce: int, difficulty_bits: int) -> bool:
        """Verifies the PoW nonce in O(1) hash evaluation."""
        target_prefix = "0" * (difficulty_bits // 4)
        payload = f"{public_key_hex}:{alias}:{nonce}".encode("utf-8")
        digest = hashlib.sha256(payload).hexdigest()
        return digest.startswith(target_prefix)

    @staticmethod
    def verify_certificate(cert: P2PCertificate) -> bool:
        """Validates PoW correctness and self-signature."""
        # Check PoW
        if not PeerIdentity.verify_pow(cert.public_key_hex, cert.alias, cert.pow_nonce, cert.pow_difficulty):
            return False
            
        # Reconstruct unsigned payload
        unsigned_data = f"{cert.did}:{cert.public_key_hex}:{cert.alias}:{cert.timestamp}:{cert.pow_nonce}:{cert.pow_difficulty}:{json.dumps(cert.capabilities, sort_keys=True)}"
        
        # Verify Ed25519 Signature
        try:
            pub_key = ed25519.Ed25519PublicKey.from_public_bytes(bytes.fromhex(cert.public_key_hex))
            pub_key.verify(bytes.fromhex(cert.signature_hex), unsigned_data.encode("utf-8"))
            return True
        except (InvalidSignature, ValueError):
            return False

    @staticmethod
    def verify_peer_signature(public_key_hex: str, message: bytes, signature_hex: str) -> bool:
        """Verifies signature on arbitrary message using peer's public key."""
        try:
            pub_key = ed25519.Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_key_hex))
            pub_key.verify(bytes.fromhex(signature_hex), message)
            return True
        except (InvalidSignature, ValueError):
            return False
