"""
Layer 1: Identity & Key Lifecycle Management Layer
Implements Self-Sovereign Identity using Ed25519 asymmetric cryptography,
Proof-of-Work (PoW) computational admission throttling, and W3C did:peer structured certificates.
"""

import time
import hashlib
import json
import enum
from dataclasses import dataclass, asdict
from typing import Dict, Any, Tuple, Optional
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature


class PeerState(enum.Enum):
    UNKNOWN = "UNKNOWN"
    ACTIVE = "ACTIVE"
    SUSPECTED = "SUSPECTED"
    REVOCATION_PROPOSED = "REVOCATION_PROPOSED"
    REVOKED = "REVOKED"


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

    def payload_bytes(self) -> bytes:
        """
        Signed payload format:
        PKI_V2_CERT:<did>:<public_key_hex>:<alias>:<timestamp>:<pow_nonce>:<pow_difficulty>:<canonical_capabilities_json>
        """
        cap_json = json.dumps(self.capabilities, sort_keys=True, separators=(",", ":"))
        data = f"PKI_V2_CERT:{self.did}:{self.public_key_hex}:{self.alias}:{self.timestamp}:{self.pow_nonce}:{self.pow_difficulty}:{cap_json}"
        return data.encode("utf-8")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PeerIdentity:
    def __init__(self, alias: str, difficulty_bits: int = 12):
        self.alias = alias
        self.difficulty_bits = difficulty_bits
        self.state: PeerState = PeerState.UNKNOWN
        
        # 1. Generate Ed25519 keypair
        self.private_key = ed25519.Ed25519PrivateKey.generate()
        self.public_key = self.private_key.public_key()
        
        # Public key raw bytes and 64 lowercase hex representation
        pub_bytes = self.public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        self.public_key_hex = pub_bytes.hex().lower()
        
        # 2. W3C did:peer representation with full 64-hex public key
        self.did = f"did:peer:2.Ez{self.public_key_hex}"
        
        # 3. Solve Proof-of-Work (computational admission throttling)
        self.pow_nonce, self.pow_hash = self._solve_pow()
        
        # 4. Assemble and self-sign Certificate
        self.certificate = self._generate_certificate()

    def _solve_pow(self) -> Tuple[int, str]:
        """
        Solves SHA-256(PublicKey || Alias || Nonce) < Target.
        difficulty_bits defines the required number of leading zero bits.
        """
        nonce = 0
        if self.difficulty_bits <= 0:
            payload = f"{self.public_key_hex}:{self.alias}:{nonce}".encode("utf-8")
            return nonce, hashlib.sha256(payload).hexdigest()

        target = 1 << (256 - self.difficulty_bits)
        while True:
            payload = f"{self.public_key_hex}:{self.alias}:{nonce}".encode("utf-8")
            digest_bytes = hashlib.sha256(payload).digest()
            if int.from_bytes(digest_bytes, byteorder="big") < target:
                return nonce, digest_bytes.hex()
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
        cert = P2PCertificate(
            did=self.did,
            public_key_hex=self.public_key_hex,
            alias=self.alias,
            timestamp=now,
            pow_nonce=self.pow_nonce,
            pow_difficulty=self.difficulty_bits,
            capabilities=capabilities,
            signature_hex=""
        )
        signature = self.sign(cert.payload_bytes())
        cert.signature_hex = signature.hex()
        return cert

    @staticmethod
    def is_valid_did(did: str, public_key_hex: str) -> bool:
        """Validates that did strictly matches did:peer:2.Ez<64 lowercase hex characters>."""
        if not isinstance(did, str) or not isinstance(public_key_hex, str):
            return False
        if len(public_key_hex) != 64:
            return False
        expected_did = f"did:peer:2.Ez{public_key_hex.lower()}"
        return did == expected_did

    @staticmethod
    def verify_pow(public_key_hex: str, alias: str, nonce: int, difficulty_bits: int) -> bool:
        """
        Verifies the PoW nonce in O(1) hash evaluation with bit-level precision.
        Difficulty is interpreted as the exact number of leading ZERO BITS.
        """
        if difficulty_bits < 0 or difficulty_bits > 256:
            return False
        if difficulty_bits == 0:
            return True
        payload = f"{public_key_hex}:{alias}:{nonce}".encode("utf-8")
        digest_bytes = hashlib.sha256(payload).digest()
        target = 1 << (256 - difficulty_bits)
        return int.from_bytes(digest_bytes, byteorder="big") < target

    @staticmethod
    def verify_certificate(
        cert: P2PCertificate,
        min_difficulty: int = 12,
        max_drift_seconds: float = 300.0,
        current_time: Optional[float] = None
    ) -> bool:
        """
        Validates certificate:
        1. pow_difficulty >= min_difficulty
        2. certificate timestamp freshness
        3. DID matches the supplied public key
        4. PoW is valid for the supplied public key, alias, nonce, and difficulty
        5. Ed25519 certificate signature is valid
        """
        # 1. pow_difficulty >= min_difficulty
        if cert.pow_difficulty < min_difficulty:
            return False

        # 2. certificate timestamp freshness
        now = time.time() if current_time is None else current_time
        if abs(now - cert.timestamp) > max_drift_seconds:
            return False

        # 3. DID matches the supplied public key
        if not PeerIdentity.is_valid_did(cert.did, cert.public_key_hex):
            return False

        # 4. PoW is valid for the supplied public key, alias, nonce, and difficulty
        if not PeerIdentity.verify_pow(cert.public_key_hex, cert.alias, cert.pow_nonce, cert.pow_difficulty):
            return False

        # 5. Ed25519 certificate signature is valid
        try:
            if len(cert.public_key_hex) != 64:
                return False
            pub_key = ed25519.Ed25519PublicKey.from_public_bytes(bytes.fromhex(cert.public_key_hex))
            pub_key.verify(bytes.fromhex(cert.signature_hex), cert.payload_bytes())
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
