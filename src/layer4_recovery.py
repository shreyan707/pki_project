"""
Layer 4: Distributed Revocation & Shamir Threshold Key Recovery
Implements m-of-n Supernode Quorum Certificate Revocation Records (CRR)
and Shamir's (k, n) Threshold Polynomial Secret Sharing for self-sovereign key recovery.
"""

import time
import secrets
from dataclasses import dataclass
from typing import List, Dict, Tuple
from src.layer1_identity import PeerIdentity


# 256-bit prime for modular arithmetic in Shamir's Secret Sharing
# Standard NIST prime (secp256k1 order or similar safe large prime)
PRIME = 2**256 - 189


@dataclass
class CertificateRevocationRecord:
    revoked_did: str
    revoked_pubkey_hex: str
    reason: str
    timestamp: float
    # Dict mapping supernode_did -> signature_hex
    supernode_signatures: Dict[str, str]

    def payload_bytes(self) -> bytes:
        data = f"{self.revoked_did}:{self.revoked_pubkey_hex}:{self.reason}:{self.timestamp}"
        return data.encode("utf-8")

    def is_quorum_approved(self, supernode_pubkeys: Dict[str, str], threshold_m: int) -> bool:
        """
        Validates that at least threshold_m legitimate supernodes co-signed the revocation.
        """
        valid_signatures = 0
        payload = self.payload_bytes()

        for sn_did, sig_hex in self.supernode_signatures.items():
            if sn_did in supernode_pubkeys:
                pubkey_hex = supernode_pubkeys[sn_did]
                if PeerIdentity.verify_peer_signature(pubkey_hex, payload, sig_hex):
                    valid_signatures += 1

        return valid_signatures >= threshold_m


class ShamirSecretSharing:
    @staticmethod
    def _extended_gcd(a: int, b: int) -> Tuple[int, int, int]:
        if a == 0:
            return b, 0, 1
        gcd, x1, y1 = ShamirSecretSharing._extended_gcd(b % a, a)
        x = y1 - (b // a) * x1
        y = x1
        return gcd, x, y

    @staticmethod
    def _mod_inverse(k: int, p: int = PRIME) -> int:
        k = k % p
        gcd, x, _ = ShamirSecretSharing._extended_gcd(k, p)
        if gcd != 1:
            raise ValueError("Modular inverse does not exist")
        return (x % p + p) % p

    @staticmethod
    def split_secret(secret_int: int, k_threshold: int, n_shares: int, prime: int = PRIME) -> List[Tuple[int, int]]:
        """
        Splits secret_int into n shares such that any k shares can reconstruct it.
        Polynomial: f(x) = secret + a_1*x + a_2*x^2 + ... + a_(k-1)*x^(k-1) mod prime
        """
        if k_threshold > n_shares:
            raise ValueError("Threshold k cannot be greater than total shares n")
        if secret_int >= prime:
            raise ValueError("Secret must be less than field prime")

        # Generate random coefficients a_1 ... a_(k-1)
        coefficients = [secret_int] + [secrets.randbelow(prime) for _ in range(k_threshold - 1)]

        shares: List[Tuple[int, int]] = []
        for x in range(1, n_shares + 1):
            y = 0
            for power, coeff in enumerate(coefficients):
                y = (y + coeff * pow(x, power, prime)) % prime
            shares.append((x, y))

        return shares

    @staticmethod
    def reconstruct_secret(shares: List[Tuple[int, int]], prime: int = PRIME) -> int:
        """
        Reconstructs secret using Lagrange Polynomial Interpolation at x = 0:
        S = sum_j (y_j * prod_{m != j} (-x_m / (x_j - x_m))) mod prime
        """
        k = len(shares)
        if k == 0:
            raise ValueError("At least one share required for reconstruction")

        secret = 0
        for j in range(k):
            x_j, y_j = shares[j]
            numerator = 1
            denominator = 1
            for m in range(k):
                if m == j:
                    continue
                x_m, _ = shares[m]
                numerator = (numerator * (-x_m)) % prime
                denominator = (denominator * (x_j - x_m)) % prime

            lagrange_l_j = (numerator * ShamirSecretSharing._mod_inverse(denominator, prime)) % prime
            secret = (secret + y_j * lagrange_l_j) % prime

        return (secret + prime) % prime
