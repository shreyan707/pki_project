# Decentralized P2P PKI & Trust Management — Protocol Specification
**Document Version:** 2.2.0-FROZEN (Frozen Protocol Specification)  
**Status:** Approved & Frozen for Implementation  
**Target Architecture:** 4-Layer Hybrid P2P Trust Mesh  
**Baseline References:** [AUDIT.md](reports/AUDIT.md), [PROTOCOL_FREEZE_REVIEW.md](reports/PROTOCOL_FREEZE_REVIEW.md)

---

## 1. System Overview & Architectural Baseline

This specification defines the protocol operations, cryptographic message formats, state transition machines, and verification rules for the decentralized peer-to-peer (P2P) public key infrastructure (PKI) and trust management framework.

### 1.1 Architectural Layers

```
+-------------------------------------------------------------------------+
| Layer 4: Revocation, Quorum Governance & Key Lifecycle                 |
|  - CRR Quorum Voting (m-of-n) | Gossip Propagation | Shamir + Recovery  |
+-------------------------------------------------------------------------+
| Layer 3: Reputation & Data Integrity Engine                             |
|  - Merkle Audit Paths | Bilateral Receipts | Evidence Matrix | EigenTrust|
+-------------------------------------------------------------------------+
| Layer 2: Certification & Topology Infrastructure                        |
|  - Web-of-Trust Cross-Certificates | Vertex-Disjoint Paths | Supernodes  |
+-------------------------------------------------------------------------+
| Layer 1: Identity & Admission Layer                                     |
|  - Ed25519 Keypairs | Un-truncated did:peer | SHA-256 PoW Admission     |
+-------------------------------------------------------------------------+
```

### 1.2 Strict Separation of Protocol Concerns

The protocol strictly separates six decoupled functional layers to prevent conflating distinct security guarantees:

1. **Identity:** Binds cryptographic key material (Ed25519 public key) to a decentralized identifier (`did:peer:2.Ez<pubkey_hex>`).
2. **Identity Admission Cost:** Imposes a computational work proof (PoW) to throttle mass automated identity generation.
3. **Content Integrity:** Guarantees cryptographic immutability and chunk-level inclusion against an authoritative Merkle root.
4. **Transaction Evidence:** Verifiable, dual-signed interaction records (`BilateralReceipt`) or cryptographically attributable delivery contradictions (`FaultEvidenceRecord`).
5. **Behavioral Reputation:** Mathematically computed global trust scores derived strictly from aggregated transaction evidence via EigenTrust power iteration.
6. **Revocation:** Quorum-authorized permanent revocation and network-wide eviction of demonstrably compromised or faulty peers via Certificate Revocation Records (CRRs).

```
+---------------+      +----------------+      +-------------------+
| 1. IDENTITY   | ---> | 2. ADMISSION   | ---> | 3. CONTENT        |
| Ed25519 Keys  |      | PoW Cost Barrier|      | Merkle Root/Proof |
+---------------+      +----------------+      +-------------------+
                                                         |
+---------------+      +----------------+                |
| 6. REVOCATION | <--- | 5. REPUTATION  | <--- +-------------------+
| Quorum Eviction|      | EigenTrust Run |      | 4. EVIDENCE       |
+---------------+      +----------------+      | Bilateral Receipts|
                                               +-------------------+
```

### 1.3 Cryptographic Standards & Domain Separation

- **Signature Scheme:** Ed25519 pure signatures (RFC 8032). Key size: 32 bytes (256 bits). Signature size: 64 bytes.
- **Hash Function:** SHA-256 (FIPS 180-4). Digest size: 32 bytes.
- **Identifier Format:** `did:peer:2.Ez<full_64_hex_pubkey>` preserving the complete 32-byte public key (no truncation).
- **Domain Separation Prefixes:** All message signing payloads prepend a strict ASCII domain prefix to prevent cross-protocol replay:
  - `PKI_V2_CERT:` for Identity Certificates
  - `PKI_V2_CROSSCERT:` for Mesh Cross-Certificates
  - `PKI_V2_MANIFEST:` for Content Manifests
  - `PKI_V2_REQ:` for Content Requests
  - `PKI_V2_RESP:` for Chunk Delivery Responses
  - `PKI_V2_RECEIPT:` for Bilateral Transaction Receipts
  - `PKI_V2_EVIDENCE_FAULT:` for Server-Attributable Fault Reports
  - `PKI_V2_CRR:` for Certificate Revocation Records
  - `PKI_V2_ROTATE:` for Key Rotation Certificates
  - `PKI_V2_RECOVER_REQ:` for Recovery Requests
  - `PKI_V2_RECOVER_SHARE:` for Share Delivery

---

## 2. Protocol State & Core Data Structures

### 2.1 Peer Lifecycle States & Transition Model

Every peer in the network resides in exactly one lifecycle state:
$$\mathcal{S} \in \{\text{UNKNOWN}, \text{ACTIVE}, \text{SUSPECTED}, \text{REVOCATION\_PROPOSED}, \text{REVOKED}\}$$

```
   [ UNKNOWN ]
        |
        | [T1] Admission (PoW + Sig Valid)
        v
   [ ACTIVE ] <------------------------------------+
        |                                          |
        | [T2] Certified Fault OR                  | [T3a] Unverified Subjective
        |      Unverified Suspicion                |       Suspicion Expired (T_susp)
        v                                          |
   [ SUSPECTED ] ----------------------------------+
        |
        | [T4] Quorum Threshold Sponsor Reached
        v
   [ REVOCATION_PROPOSED ]
        |                   \
        | [T5a] Quorum       \ [T5b] Quorum Timeout (T_vote)
        |       Approved      \       Fallback to SUSPECTED (k < m)
        v                      v
   [ REVOKED ]            [ SUSPECTED ]
   (Permanent Eviction)   (Retains Degraded Trust)
```

#### Deterministic State Transition Rules

| Transition | From | To | Condition | Authorization / Verification |
| :--- | :--- | :--- | :--- | :--- |
| **T1: Admission** | `UNKNOWN` | `ACTIVE` | Valid PoW ($D \ge D_{\min}$) + valid self-signature + fresh timestamp | Admission Verifier |
| **T2a: Attributable Fault** | `ACTIVE` | `SUSPECTED` | Validated `FaultEvidenceRecord` submitted | Detecting Client / Local Engine |
| **T2b: Subjective Suspicion** | `ACTIVE` | `SUSPECTED` | Interaction timeout or uncooperative peer | Local Node |
| **T3a: Exoneration (Subjective)** | `SUSPECTED` | `ACTIVE` | $T_{\text{susp}}$ expires without corroborating fault evidence | Local Node (Only for unverified suspicion) |
| **T3b: Certified Suspicion Persistence** | `SUSPECTED` | `SUSPECTED` | $T_{\text{susp}}$ expires for certified fault | **NO EXPIRATION.** Retains certified suspicion until T4, administrative adjudication, or key rotation. |
| **T4: Revocation Escalation** | `SUSPECTED` | `REVOCATION_PROPOSED` | Formal `PROPOSE_REVOCATION` with certified evidence bundle | Supernode Committee |
| **T5a: Quorum Eviction** | `REVOCATION_PROPOSED` | `REVOKED` | $\ge m$ valid supernode signatures assembled on CRR | Supernode Coordinator / Gossip Relay |
| **T5b: Quorum Timeout Fallback** | `REVOCATION_PROPOSED` | `SUSPECTED` | $T_{\text{vote}}$ expires without reaching threshold ($k < m$) | Committee / Swarm (Reverts to SUSPECTED, **NEVER** to ACTIVE) |

---

### 2.2 Core Data Structures

#### `P2PCertificate`
```json
{
  "did": "did:peer:2.Ez9a4b8c...",
  "public_key_hex": "9a4b8c...",
  "alias": "Peer_A",
  "timestamp": 1775500000.0,
  "pow_nonce": 48291,
  "pow_difficulty": 16,
  "capabilities": {
    "bandwidth_mbps": 100,
    "storage_gb": 50,
    "protocol_version": "2.0-pki"
  },
  "signature_hex": "e1f4..."
}
```
*Signed Payload:* `PKI_V2_CERT:<did>:<public_key_hex>:<alias>:<timestamp>:<pow_nonce>:<pow_difficulty>:<canonical_capabilities_json>`

#### `CrossCertificate`
```json
{
  "issuer_did": "did:peer:2.EzAlice...",
  "issuer_pubkey_hex": "1122...",
  "subject_did": "did:peer:2.EzBob...",
  "subject_pubkey_hex": "3344...",
  "trust_weight": 0.9000,
  "issued_at": 1775500005.0,
  "expires_at": 1775586405.0,
  "signature_hex": "7788..."
}
```
*Signed Payload:* `PKI_V2_CROSSCERT:<issuer_did>:<subject_did>:<trust_weight_4dec>:<issued_at>:<expires_at>`  
*(where `<trust_weight_4dec>` is strictly formatted as `f"{trust_weight:.4f}"`, e.g., `"0.9000"`).*

#### `ContentManifest`
```json
{
  "content_id": "file-uuid-001",
  "root_hash": "a1b2c3...",
  "total_chunks": 8,
  "chunk_size_bytes": 65536,
  "file_size_bytes": 524288,
  "publisher_did": "did:peer:2.EzServer...",
  "timestamp": 1775500010.0,
  "signature_hex": "f8a0..."
}
```
*Signed Payload:* `PKI_V2_MANIFEST:<content_id>:<root_hash>:<total_chunks>:<chunk_size_bytes>:<file_size_bytes>:<publisher_did>:<timestamp>`

#### `ContentRequest`
```json
{
  "req_id": "req-c1-s1-1001",
  "client_did": "did:peer:2.EzClient...",
  "server_did": "did:peer:2.EzServer...",
  "content_id": "file-uuid-001",
  "chunk_index": 0,
  "merkle_root": "a1b2c3...",
  "timestamp": 1775500015.0,
  "nonce": "n-88192a",
  "client_sig_hex": "bba1..."
}
```
*Signed Payload:* `PKI_V2_REQ:<req_id>:<client_did>:<server_did>:<content_id>:<chunk_index>:<merkle_root>:<timestamp>:<nonce>`

#### `MerkleProofStep` & Canonical Proof Serialization
A Merkle inclusion proof $\Pi_k$ is an ordered list of sibling steps:
```json
[
  {"sibling_hash": "c4d5e6...", "direction": "R"},
  {"sibling_hash": "f7a8b9...", "direction": "L"}
]
```
*Canonical Proof Serialization:*
$$\text{CanonicalProofStr}(\Pi_k) = \text{join}(",", [f"{step.sibling\_hash}:{step.direction}" \text{ for } step \in \Pi_k])$$
$$\text{proof\_hash} = H(\Pi_k) = \text{SHA-256}(\text{CanonicalProofStr}(\Pi_k).\text{encode}("utf-8")).\text{hexdigest}()$$

#### `ChunkResponse`
```json
{
  "req_id": "req-c1-s1-1001",
  "client_did": "did:peer:2.EzClient...",
  "server_did": "did:peer:2.EzServer...",
  "content_id": "file-uuid-001",
  "chunk_index": 0,
  "chunk_bytes": "<raw bytes>",
  "chunk_hash": "e3b0c4...",
  "proof_hash": "7a91bb...",
  "merkle_root": "a1b2c3...",
  "timestamp": 1775500016.0,
  "nonce": "n-88192a",
  "merkle_proof": [
    {"sibling_hash": "c4d5e6...", "direction": "R"}
  ],
  "server_sig_hex": "44cc..."
}
```
*Signed Payload (Server Envelope):*  
`PKI_V2_RESP:<req_id>:<client_did>:<server_did>:<content_id>:<chunk_index>:<chunk_hash>:<proof_hash>:<merkle_root>:<timestamp>:<nonce>`

#### `BilateralReceipt`
```json
{
  "tx_id": "tx-8f7b-4a21-99c0",
  "client_did": "did:peer:2.EzClient...",
  "client_pubkey_hex": "b3c2...",
  "server_did": "did:peer:2.EzServer...",
  "server_pubkey_hex": "9a4b...",
  "merkle_root": "a1b2c3...",
  "rating": "+1.00",
  "timestamp": 1775500025.0,
  "nonce": "7c9f8021a",
  "client_sig_hex": "1122...",
  "server_sig_hex": "3344..."
}
```
*Signed Payload:* `PKI_V2_RECEIPT:<tx_id>:<client_did>:<server_did>:<merkle_root>:<rating>:<timestamp>:<nonce>`  
*(where `<rating>` is strictly the 5-character string `"+1.00"` or `"-1.00"`).*

*Rating Semantics:*
- `"+1.00"`: Successful bilateral fulfillment. Both parties co-sign certifying successful delivery.
- `"-1.00"`: Bilateral dispute receipt. Both parties co-sign acknowledging unfulfilled contract or cancelled transaction. (Does NOT constitute cryptographic fault proof; treated strictly as a mutual behavioral dispute signal).

#### `FaultEvidenceRecord` (Server-Attributable Delivery Contradiction)
```json
{
  "evidence_id": "ev-fault-9821-44ab",
  "req_id": "req-c1-s1-1001",
  "reporter_did": "did:peer:2.EzClient...",
  "accused_did": "did:peer:2.EzServer...",
  "content_id": "file-uuid-001",
  "merkle_root": "a1b2c3...",
  "chunk_index": 0,
  "delivered_chunk_hash": "e3b0c4...",
  "delivered_proof_hash": "7a91bb...",
  "manifest_envelope": {
    "content_id": "file-uuid-001",
    "root_hash": "a1b2c3...",
    "total_chunks": 8,
    "chunk_size_bytes": 65536,
    "file_size_bytes": 524288,
    "publisher_did": "did:peer:2.EzServer...",
    "timestamp": 1775500010.0,
    "signature_hex": "f8a0..."
  },
  "delivery_envelope": {
    "req_id": "req-c1-s1-1001",
    "client_did": "did:peer:2.EzClient...",
    "server_did": "did:peer:2.EzServer...",
    "content_id": "file-uuid-001",
    "chunk_index": 0,
    "chunk_hash": "e3b0c4...",
    "proof_hash": "7a91bb...",
    "merkle_root": "a1b2c3...",
    "timestamp": 1775500016.0,
    "nonce": "n-88192a",
    "server_sig_hex": "44cc..."
  },
  "authentic_chunk_hash": "99aa88...",
  "authentic_merkle_proof": [
    {"sibling_hash": "112233...", "direction": "R"}
  ],
  "timestamp": 1775500020.0,
  "reporter_sig_hex": "5566..."
}
```
*Signed Payload:* `PKI_V2_EVIDENCE_FAULT:<evidence_id>:<req_id>:<reporter_did>:<accused_did>:<content_id>:<merkle_root>:<chunk_index>:<delivered_chunk_hash>:<authentic_chunk_hash>:<timestamp>`

#### `CertificateRevocationRecord` (CRR)
```json
{
  "revocation_id": "crr-8821-ff0a",
  "revoked_did": "did:peer:2.EzServer...",
  "revoked_pubkey_hex": "9a4b...",
  "reason": "ATTRIBUTABLE_INCONSISTENT_DELIVERY",
  "evidence_id": "ev-fault-9821-44ab",
  "timestamp": 1775500050.0,
  "supernode_signatures": {
    "did:peer:2.EzSN1...": "aa11...",
    "did:peer:2.EzSN2...": "bb22...",
    "did:peer:2.EzSN3...": "cc33..."
  }
}
```
*Signed Payload:* `PKI_V2_CRR:<revocation_id>:<revoked_did>:<revoked_pubkey_hex>:<reason>:<evidence_id>:<timestamp>`

---

## 3. End-to-End Protocol Flows (Flows 1 to 22)

```
================================================================================
FLOW 1: PEER IDENTITY CREATION
================================================================================
```
- **Actors:** Proposing Peer ($P$)
- **Inputs:** Peer alias string $A$, difficulty target $D$ (bits), initial capability attributes $C$
- **Outputs:** Private key $sk_P$, Public key $pk_P$ (32 bytes raw, 64 hex chars), Identifier $DID_P = \text{"did:peer:2.Ez"} \,\|\, \text{hex}(pk_P)$, Unsigned identity record
- **Messages Exchanged:** None (local operation)
- **Cryptographic Operations:**
  1. Generate Ed25519 keypair: $(sk_P, pk_P) \leftarrow \text{Ed25519.GenerateKeyPair}()$.
  2. Compute canonical $DID_P = \text{"did:peer:2.Ez"} \,\|\, \text{hex}(pk_P)$ preserving full 64 hex characters.
- **State Changes:** $P$ initial state: $\mathcal{S}_P = \text{UNKNOWN}$. Keys stored in secure local memory/keystore.
- **Validation Rules:** $pk_P$ must be exactly 32 bytes (64 hex characters).
- **Failure Conditions:** PRNG entropy exhaustion during keypair generation.
- **Attacker Opportunities:** Generating keys using compromised local PRNG.
- **Security Assumptions:** Local execution environment provides cryptographically secure pseudo-random numbers (CSPRNG).

```
================================================================================
FLOW 2: PoW GENERATION
================================================================================
```
- **Actors:** Proposing Peer ($P$)
- **Inputs:** $pk_P$, Alias $A$, Difficulty target $D$, Nonce counter initialized to 0
- **Outputs:** Valid nonce $N \in \mathbb{N}$, Digest $H_{pow} = \text{SHA-256}(\text{hex}(pk_P) \,\|\, ":" \,\|\, A \,\|\, ":" \,\|\, N)$
- **Messages Exchanged:** None (local computation)
- **Cryptographic Operations:**
  1. Iterate $N \leftarrow 0, 1, 2, \dots$
  2. Evaluate $H = \text{SHA-256}(\text{encode}(pk_P \,\|\, ":" \,\|\, A \,\|\, ":" \,\|\, N))$.
  3. Terminate when $\text{int}(H) < 2^{256 - D}$ (i.e., top $D$ bits are zero).
- **State Changes:** Nonce $N$ and digest $H_{pow}$ bound to peer identity state.
- **Validation Rules:** $H$ must satisfy leading zero-bit constraint $D$.
- **Failure Conditions:** Arithmetic overflow.
- **Attacker Opportunities:** Use of specialized ASIC/GPU clusters to find valid nonces rapidly.
- **Security Assumptions:** SHA-256 behaves as a random oracle; finding solution requires $O(2^D)$ expected operations.

```
================================================================================
FLOW 3: PEER ADMISSION AND PoW VERIFICATION
================================================================================
```
- **Actors:** Candidate Peer ($P$), Admission Verifier / Network Node ($V$)
- **Inputs:** Peer Certificate $Cert_P = \langle DID_P, pk_P, A, t_0, N, D, C, \sigma_P \rangle$
- **Outputs:** Boolean admission status $\text{Admitted} \in \{\text{True}, \text{False}\}$, Peer admission record
- **Messages Exchanged:**
  - $M_{1.1} (P \to V): \text{REGISTER\_REQ}(Cert_P)$
  - $M_{1.2} (V \to P): \text{REGISTER\_RESP}(\text{status}, \text{timestamp}, \sigma_V)$
- **Cryptographic Operations:**
  1. $V$ checks PoW: Verify that $\text{SHA-256}(\text{hex}(pk_P) \,\|\, ":" \,\|\, A \,\|\, ":" \,\|\, N)$ has at least $D$ leading zero bits.
  2. $V$ checks self-signature: $\text{Ed25519.Verify}(pk_P, \text{"PKI\_V2\_CERT:"} \,\|\, DID_P \,\|\, \dots, \sigma_P)$.
- **State Changes:**
  - If valid: $V$ sets $P$ lifecycle state in its peer table: $\mathcal{S}_P \leftarrow \text{ACTIVE}$.
  - If invalid: Rejected; no state change in peer registry.
- **Validation Rules:**
  1. $D \ge D_{\min}$ (enforced by network admission policy).
  2. $|t_{\text{current}} - t_0| \le \Delta t_{\text{admission}}$ (timestamp freshness within 300 seconds).
  3. $DID_P == \text{"did:peer:2.Ez"} \,\|\, \text{hex}(pk_P)$.
  4. Nonce meets target difficulty.
  5. Signature $\sigma_P$ is valid under $pk_P$.
  6. $P$ is not in the local revocation list ($\mathcal{S}_P \ne \text{REVOKED}$).
- **Failure Conditions:** Insufficient PoW bits, stale timestamp, mismatched DID, invalid signature, or already revoked peer.
- **Attacker Opportunities:** Flood admission endpoints with invalid nonces to exhaust verifier CPU (mitigated by verifying PoW before costly signature operations).
- **Security Assumptions:** Verifier possesses synchronized clock ($\pm \Delta t$).

```
================================================================================
FLOW 4: IDENTITY / KEY VERIFICATION
================================================================================
```
- **Actors:** Verifying Peer ($V$), Target Peer ($P$)
- **Inputs:** Target identifier $DID_P$, claimed public key $pk_P$, signature $\sigma$, message $M$
- **Outputs:** Verification result $\in \{\text{VALID}, \text{INVALID}\}$
- **Messages Exchanged:**
  - $M_{2.1} (V \to P): \text{KEY\_CHALLENGE}(\text{nonce}_V)$
  - $M_{2.2} (P \to V): \text{KEY\_RESPONSE}(Cert_P, \sigma_P(\text{nonce}_V))$
- **Cryptographic Operations:**
  1. Verify string binding: Assert $DID_P == \text{"did:peer:2.Ez"} \,\|\, \text{hex}(pk_P)$.
  2. Verify challenge signature: $\text{Ed25519.Verify}(pk_P, \text{nonce}_V, \sigma_P(\text{nonce}_V))$.
- **State Changes:** None (read-only verification).
- **Validation Rules:** $pk_P$ matches DID; challenge signature matches challenge nonce.
- **Failure Conditions:** Mismatched key; corrupted signature; timed-out challenge.
- **Attacker Opportunities:** Replay of historical signature (thwarted by random nonces).
- **Security Assumptions:** Ed25519 is Existentially Unforgeable under Chosen Message Attack (EUF-CMA).

```
================================================================================
FLOW 5: CONTENT REQUEST
================================================================================
```
- **Actors:** Downloader Peer ($C$, Client), Serving Peer ($S$, Server)
- **Inputs:** Content Identifier $ContentID$, chunk index $k$, trusted Merkle root $R$, fresh nonce $\nu_{req}$
- **Outputs:** Formatted, signed request message `ContentRequest`
- **Messages Exchanged:**
  - $M_{3.1} (C \to S): \text{CONTENT\_REQ}(ReqID, C.DID, S.DID, ContentID, k, R, t_{req}, \nu_{req}, \sigma_C)$
- **Cryptographic Operations:**
  1. $C$ computes request ID: $ReqID \leftarrow \text{UUIDv4}()$.
  2. $C$ signs request payload:
     $$\sigma_C \leftarrow \text{Ed25519.Sign}(sk_C, \text{"PKI\_V2\_REQ:"} \,\|\, ReqID \,\|\, C.DID \,\|\, S.DID \,\|\, ContentID \,\|\, k \,\|\, R \,\|\, t_{req} \,\|\, \nu_{req})$$
- **State Changes:** $C$ logs pending request context: $\text{PendingReq}[ReqID] \leftarrow \langle S.DID, ContentID, k, R, t_{req}, \nu_{req} \rangle$.
- **Validation Rules:** $S$ verifies $C.DID$ is $\text{ACTIVE}$, timestamp $|t_{\text{current}} - t_{req}| \le 60\text{s}$, and $\sigma_C$ is valid.
- **Failure Conditions:** Client revoked; server unreachable; invalid signature; stale request.
- **Attacker Opportunities:** Denial-of-Service via high-frequency bogus requests (rate-limited per authenticated DID).
- **Security Assumptions:** End-to-end message authentication via Ed25519.

```
================================================================================
FLOW 6: CONTENT / CHUNK DISTRIBUTION WITH CRYPTOGRAPHIC & PROOF BINDING
================================================================================
```
- **Actors:** Serving Peer ($S$), Downloader Peer ($C$)
- **Inputs:** Validated `ContentRequest` ($ReqID, C.DID, S.DID, ContentID, k, R, t_{req}, \nu_{req}$), chunk bytes $B_k$, Merkle inclusion proof $\Pi_k$, Content Manifest $Man_F$
- **Outputs:** Formatted, signed delivery payload `ChunkResponse`
- **Messages Exchanged:**
  - $M_{3.2} (S \to C): \text{CHUNK\_RESP}(ReqID, C.DID, S.DID, ContentID, k, B_k, H(B_k), H(\Pi_k), R, t_{resp}, \nu_{req}, \Pi_k, \sigma_S)$
- **Cryptographic Operations:**
  1. $S$ computes chunk digest: $H(B_k) = \text{SHA-256}(B_k)$.
  2. $S$ computes canonical proof digest: $H(\Pi_k) = \text{SHA-256}(\text{CanonicalProofStr}(\Pi_k).\text{encode}("utf-8")).\text{hexdigest}()$.
  3. $S$ signs the comprehensive delivery envelope binding request, chunk hash, proof hash, root, and client DID:
     $$\sigma_S \leftarrow \text{Ed25519.Sign}(sk_S, \text{"PKI\_V2\_RESP:"} \,\|\, ReqID \,\|\, C.DID \,\|\, S.DID \,\|\, ContentID \,\|\, k \,\|\, H(B_k) \,\|\, H(\Pi_k) \,\|\, R \,\|\, t_{resp} \,\|\, \nu_{req})$$
- **State Changes:** $S$ logs chunk dispatch in pending receipt queue.
- **Validation Rules:**
  1. $\text{Ed25519.Verify}(pk_S, \text{"PKI\_V2\_RESP:"} \dots, \sigma_S) == \text{True}$.
  2. Envelope fields ($ReqID, C.DID, S.DID, ContentID, k, R, \nu_{req}$) strictly match client's pending request record.
  3. Computed $\text{SHA-256}(B_k)$ strictly matches envelope's $H(B_k)$.
  4. Computed proof digest $\text{SHA-256}(\text{CanonicalProofStr}(\Pi_k))$ strictly matches envelope's $H(\Pi_k)$.
- **Failure Conditions:** Chunk read error on server; connection reset; signature verification failure.
- **Attacker Opportunities:** Malicious server attempts to substitute chunk bytes or supply a malformed proof path. Because $\sigma_S$ explicitly commits to both $H(B_k)$ and $H(\Pi_k)$, any discrepancy is non-repudiably bound to $S$.
- **Security Assumptions:** Second pre-image resistance of SHA-256; EUF-CMA security of Ed25519.

```
================================================================================
FLOW 7: MERKLE ROOT ESTABLISHMENT
================================================================================
```
- **Actors:** Publisher / Authoritative Uploader ($S$), Content Verifier ($C$)
- **Inputs:** Complete data chunks $[B_0, B_1, \dots, B_{N-1}]$, Content ID
- **Outputs:** Merkle root digest $R \in \{0, 1\}^{256}$, signed `ContentManifest`
- **Messages Exchanged:**
  - $M_{4.1} (S \to C): \text{MANIFEST\_PUB}(Man_F)$
- **Cryptographic Operations:**
  1. Compute leaf digests: $L_i = \text{SHA-256}(B_i)$ for $i \in [0, N-1]$.
  2. Pairwise interior hashing: For level nodes $u, v$, compute $Parent = \text{SHA-256}(\text{raw}(u) \,\|\, \text{raw}(v))$.
     *(If odd number of nodes at level, duplicate last node under deterministic rule: $Parent = \text{SHA-256}(\text{raw}(u) \,\|\, \text{raw}(u))$).*
  3. Ascend to single root $R$.
  4. Generate manifest signature:
     $$\sigma_{man} \leftarrow \text{Ed25519.Sign}(sk_S, \text{"PKI\_V2\_MANIFEST:"} \,\|\, ContentID \,\|\, R \,\|\, N \,\|\, \text{ChunkSize} \,\|\, \text{FileSize} \,\|\, S.DID \,\|\, t_{man})$$
- **State Changes:** Client records trusted/expected root: $\text{ExpectedRoot}[ContentID] \leftarrow R$.
- **Validation Rules:**
  1. Client verifies $\text{Ed25519.Verify}(pk_S, \text{"PKI\_V2\_MANIFEST:"}\dots, \sigma_{man})$.
  2. Manifest publisher key matches known peer or trusted index.
- **Failure Conditions:** Corrupted manifest signature; untrusted publisher.
- **Attacker Opportunities:** Malicious peer signs a manifest containing a bogus root hash $R'$.
- **Security Assumptions:** The client accepts root $R$ only from an authenticated publisher or established out-of-band manifest index.

```
================================================================================
FLOW 8: MERKLE INCLUSION PROOF GENERATION
================================================================================
```
- **Actors:** Serving Peer ($S$) holding full tree $\mathcal{T}$
- **Inputs:** Target chunk index $k$, Leaf array $L_0, \dots, L_{N-1}$
- **Outputs:** Audit path $\Pi_k = [(\text{sibling}_0, \text{dir}_0), (\text{sibling}_1, \text{dir}_1), \dots, (\text{sibling}_{h-1}, \text{dir}_{h-1})]$ of length $h = \lceil \log_2 N \rceil$
- **Messages Exchanged:** None (local computation before sending Flow 6)
- **Cryptographic Operations:**
  1. Identify leaf node at index $k$.
  2. At each tree layer $d$ from bottom to top:
     - If $k$ is even: sibling is at $k+1$ (or $k$ if odd terminal); direction is `"R"`.
     - If $k$ is odd: sibling is at $k-1$; direction is `"L"`.
     - Append $(SiblingHash_d, Direction_d)$ to $\Pi_k$.
     - Set $k \leftarrow \lfloor k / 2 \rfloor$.
- **State Changes:** None.
- **Validation Rules:** Proof path length must equal tree depth.
- **Failure Conditions:** Chunk index out of bounds.
- **Attacker Opportunities:** Provide malformed, truncated, or cyclic proof elements.
- **Security Assumptions:** Hash tree structure is deterministic and binary.

```
================================================================================
FLOW 9: MERKLE INCLUSION PROOF VERIFICATION
================================================================================
```
- **Actors:** Downloader Peer ($C$)
- **Inputs:** Received chunk bytes $B_k$, index $k$, proof path $\Pi_k$, trusted root hash $R$
- **Outputs:** Boolean result $\text{InclusionValid} \in \{\text{True}, \text{False}\}$
- **Messages Exchanged:** None (local verification upon receiving $M_{3.2}$)
- **Cryptographic Operations:**
  1. Compute leaf hash: $H_0 \leftarrow \text{SHA-256}(B_k)$.
  2. For each step $(S_j, \text{dir}_j) \in \Pi_k$:
     - If $\text{dir}_j == \text{"R"}$: $H_{j+1} \leftarrow \text{SHA-256}(\text{raw}(H_j) \,\|\, \text{raw}(S_j))$.
     - If $\text{dir}_j == \text{"L"}$: $H_{j+1} \leftarrow \text{SHA-256}(\text{raw}(S_j) \,\|\, \text{raw}(H_j))$.
  3. Compare computed root $H_{\text{final}} == R$.
- **State Changes:**
  - If valid: Mark chunk $k$ as verified in local download manager.
  - If invalid: Trigger Flow 16 (Attributable Inconsistent Delivery Detection).
- **Validation Rules:**
  1. Length of $\Pi_k \le 32$ (for files up to $2^{32}$ chunks).
  2. Sibling hashes must be valid 32-byte binary digests.
  3. Final reconstructed hash strictly equals trusted root $R$.
- **Failure Conditions:** Bit flip in chunk; fake sibling hash; incorrect traversal direction.
- **Attacker Opportunities:** Pre-image attacks on SHA-256 (infeasible, $2^{256}$ security).
- **Security Assumptions:** Second pre-image resistance of SHA-256.

```
================================================================================
FLOW 10: BILATERAL TRANSACTION RECEIPT CREATION
================================================================================
```
- **Actors:** Client ($C$), Server ($S$)
- **Inputs:** Transaction context $\langle ReqID, C.DID, S.DID, R, \text{rating}, t_{tx} \rangle$, fresh entropy nonce $\nu$
- **Outputs:** Unsigned receipt proposal
- **Messages Exchanged:**
  - $M_{5.1} (C \to S): \text{PROPOSE\_RECEIPT}(TxID, C.DID, S.DID, R, \text{rating}, t_{tx}, \nu, \sigma_C)$
- **Cryptographic Operations:**
  1. $C$ computes unique transaction ID: $TxID \leftarrow \text{UUIDv4}()$.
  2. $C$ signs canonical receipt payload:
     $$\sigma_C \leftarrow \text{Ed25519.Sign}(sk_C, \text{"PKI\_V2\_RECEIPT:"} \,\|\, TxID \,\|\, C.DID \,\|\, S.DID \,\|\, R \,\|\, \text{rating} \,\|\, t_{tx} \,\|\, \nu)$$
- **State Changes:** Client records receipt state as `PROPOSED_SENT`.
- **Validation Rules:**
  - Rating must be strictly formatted as `"+1.00"` (satisfactory fulfillment) or `"-1.00"` (bilateral dispute).
  - Timestamp freshness $|t_{\text{current}} - t_{tx}| \le 60\text{s}$.
- **Failure Conditions:** Connection dropped before receipt negotiation.
- **Attacker Opportunities:** Client attempts to propose rating other than $+1.00$ or $-1.00$, or demands rating without transaction.
- **Security Assumptions:** Synchronized clocks within $\Delta t_{tx} = 60\text{s}$.

```
================================================================================
FLOW 11: RECEIPT CO-SIGNING
================================================================================
```
- **Actors:** Server ($S$), Client ($C$)
- **Inputs:** Received proposal $M_{5.1}$, Server private key $sk_S$
- **Outputs:** Complete bilateral receipt $Rcpt = \langle \dots, \sigma_C, \sigma_S \rangle$
- **Messages Exchanged:**
  - $M_{5.2} (S \to C): \text{ACK\_RECEIPT}(TxID, \sigma_S)$
- **Cryptographic Operations:**
  1. $S$ validates $C$'s signature: $\text{Ed25519.Verify}(pk_C, \text{"PKI\_V2\_RECEIPT:"} \dots, \sigma_C)$.
  2. $S$ counter-signs identical payload:
     $$\sigma_S \leftarrow \text{Ed25519.Sign}(sk_S, \text{"PKI\_V2\_RECEIPT:"} \,\|\, TxID \,\|\, C.DID \,\|\, S.DID \,\|\, R \,\|\, \text{rating} \,\|\, t_{tx} \,\|\, \nu)$$
- **State Changes:** Both $C$ and $S$ persist completed bilateral receipt $Rcpt$ in their local transaction journals.
- **Validation Rules:** Both $\sigma_C$ and $\sigma_S$ must verify under their respective public keys against the exact same byte string.
- **Failure Conditions:** Signature verification failure; payload discrepancy.
- **Attacker Opportunities:** Server refuses to co-sign after providing data (server denies itself positive credit; client still possesses file).
- **Security Assumptions:** Mutual non-repudiation: neither party can claim the receipt was generated unilaterally.

```
================================================================================
FLOW 12: RECEIPT REPLAY DETECTION & ORDERED VALIDATION
================================================================================
```
- **Actors:** Reputation Accounting Node / Verifier ($V$)
- **Inputs:** Candidate receipt $Rcpt = \langle TxID, C.DID, S.DID, R, \text{rating}, t_{tx}, \nu, \sigma_C, \sigma_S \rangle$
- **Outputs:** Verification status $\in \{\text{ACCEPTED}, \text{DUPLICATE\_REJECTED}, \text{STALE\_REJECTED}\}$
- **State Maintained:**
  - Node-Local Processed Evidence Journal: $\mathcal{L}_{\text{local}} = \{TxID_1, TxID_2, \dots \}$
  - Replay Nonce Cache: $\mathcal{N}_{\text{seen}} = \{\nu_1, \nu_2, \dots \}$
  - Max Freshness Window: $W = 600\text{ seconds}$
- **Messages Exchanged:** None (internal validation pipeline)
- **Deterministic Validation Order (Strict Sequence):**
  1. **Step 1 (Timestamp Freshness):** Check $|t_{\text{current}} - t_{tx}| \le W$.
     If $|t_{\text{current}} - t_{tx}| > W$ or $t_{tx} > t_{\text{current}} + \Delta t_{\text{drift}}$, **REJECT IMMEDIATELY** (`STALE_REJECTED`).
  2. **Step 2 (Nonce Replay Cache):** Query nonce set $\mathcal{N}_{\text{seen}}$.
     If $\nu \in \mathcal{N}_{\text{seen}}$, **REJECT** (`DUPLICATE_REJECTED`).
  3. **Step 3 (Journal Deduplication):** Query $\mathcal{L}_{\text{local}}$ (or $\mathcal{L}_{\text{sim}}$ in simulation harness).
     If $TxID \in \mathcal{L}_{\text{local}}$, **REJECT** (`DUPLICATE_REJECTED`).
  4. **Step 4 (Signature Verification):** Verify both $\sigma_C$ and $\sigma_S$ under public keys.
     If invalid, **REJECT** (`INVALID_SIGNATURE`).
  5. **Step 5 (Journal Commit & Accounting):**
     Commit $TxID \to \mathcal{L}_{\text{local}}$, add $\nu \to \mathcal{N}_{\text{seen}}$, and apply trust update to satisfaction matrix $S$.
- **Failure Conditions:** Replayed transaction ID; expired timestamp; invalid signature.
- **Attacker Opportunities:** Re-submitting valid receipts to inflate scores (blocked at Steps 1, 2, and 3).
- **Security Assumptions:** Node storage persistence across restarts.

```
================================================================================
FLOW 13: EVIDENCE VALIDATION & MERKLE INCONSISTENCY VERIFICATION
================================================================================
```
- **Actors:** Reputation Engine / Supernode Arbiter ($E$)
- **Inputs:** Candidate evidence item $\mathcal{E}$ (either `BilateralReceipt` or `FaultEvidenceRecord`)
- **Outputs:** Validated evidence status $\in \{\text{VALID}, \text{INVALID}\}$
- **Messages Exchanged:**
  - $M_{6.1} (P \to E): \text{SUBMIT\_EVIDENCE}(\mathcal{E})$
- **Cryptographic Operations & Arbiter Deduction Logic:**
  - **Case A: `BilateralReceipt`:**
    1. Verify client signature $\sigma_C$ on `PKI_V2_RECEIPT:` payload.
    2. Verify server signature $\sigma_S$ on `PKI_V2_RECEIPT:` payload.
    3. Execute Flow 12 Ordered Validation.
    4. *Classification:*
       - If `rating == "+1.00"`: Certified successful bilateral interaction.
       - If `rating == "-1.00"`: Certified bilateral transaction dispute (behavioral signal).
  - **Case B: `FaultEvidenceRecord` (Server-Attributable Delivery Contradiction):**
    A third-party arbiter evaluates the complete mathematical proof:
    1. **Verify Manifest:** Confirm server signed `manifest_envelope` committing to root $R$ for $ContentID$.
    2. **Verify Delivery Commitment:** Confirm server signed `delivery_envelope` committing to $H(B')$, $H(\Pi_S)$, $k$, and root $R$ for request $ReqID$.
    3. **Verify Authentic Leaf Inclusion:** The complainant supplies an authentic leaf digest $L_{\text{authentic}}$ and authentic proof $\Pi_{\text{authentic}}$.
       The arbiter evaluates $\text{VerifyProof}(L_{\text{authentic}}, \Pi_{\text{authentic}}, k, R)$.
       *Assertion:* $\text{VerifyProof}(L_{\text{authentic}}, \Pi_{\text{authentic}}, k, R) == \text{True}$.
    4. **Evaluate Mathematical Contradiction:**
       *Assertion:* $L_{\text{authentic}} \ne H(B')$.
    5. **Deduction:** Under the collision resistance of SHA-256, for a fixed binary Merkle tree structure, there exists at most **one** unique digest at index $k$ that can evaluate to root $R$. Because $\Pi_{\text{authentic}}$ proves that $L_{\text{authentic}}$ is the unique committed leaf at index $k$, and the server's own signed delivery envelope commits to $H(B') \ne L_{\text{authentic}}$, the delivery is **cryptographically proven inconsistent** with the server's signed manifest root.
    6. **Explicit Boundary Statements:**
       - *Failed inclusion proof is NOT non-membership evidence:* Merely showing a proof that fails does not establish server fault, because a malicious complainant could submit a malformed proof path.
       - *Arbiter requirement:* The arbiter must verify an independently valid authentic leaf proof $\Pi_{\text{authentic}}$ reaching root $R$.
       - *Attribution vs. Intent:* This proves server-attributable inconsistent delivery; it does **not** prove malicious intent (cannot distinguish intentional attack from hardware bit-rot or software bug).
- **State Changes:** Validated record entered into journal $\mathcal{J}$ and committed to $\mathcal{L}_{\text{local}}$ (or $\mathcal{L}_{\text{sim}}$).
- **Validation Rules:** All public keys unrevoked; signatures valid; contradiction mathematically established.
- **Failure Conditions:** Authentic proof does not reach root $R$; server did not sign delivery envelope; $L_{\text{authentic}} == H(B')$.
- **Security Assumptions:** Collision resistance of SHA-256; EUF-CMA security of Ed25519.

```
================================================================================
FLOW 14: TRUST-MATRIX UPDATE & EVIDENCE ACCOUNTING SEMANTICS
================================================================================
```
- **Actors:** Local Trust Accounting Node ($E$)
- **Inputs:** Validated interaction journal $\mathcal{J}$
- **Outputs:** Updated satisfaction matrix $S \in \mathbb{R}^{N \times N}$
- **Messages Exchanged:** None (local deterministic state transition)
- **Cryptographic Operations:** None
- **State Changes & Evidence Semantics:**
  For each new, validated, non-replayed record $r \in \mathcal{J}$:
  1. **Successful Bilateral Receipt (`BilateralReceipt`, rating `"+1.00"`):**
     $$S_{C, S} \leftarrow S_{C, S} + 1.0$$
  2. **Bilateral Dispute Receipt (`BilateralReceipt`, rating `"-1.00"`):**
     $$S_{C, S} \leftarrow S_{C, S} - 1.0$$
     *Semantics:* Reflects mutual acknowledgement of a failed or cancelled transaction. It is a behavioral dispute signal. It does NOT trigger revocation.
  3. **Certified Fault Evidence (`FaultEvidenceRecord`):**
     $$S_{\text{reporter}, \text{accused}} \leftarrow S_{\text{reporter}, \text{accused}} - 2.0$$
     *Semantics:* Cryptographically verified inconsistent delivery. Triggers transition of accused to `SUSPECTED` and escalation to Flow 17 (`PROPOSE_REVOCATION`).
- **Accounting Architecture & Consensus Boundary:**
  - **In the Decentralized P2P Protocol:** Each peer maintains a **Node-Local Processed Evidence Journal** ($\mathcal{L}_{\text{local}}$). It guarantees that an individual peer applies a given $TxID$ or $EvidenceID$ at most once to its local matrix $S$. Without distributed consensus, different peers may hold different local evidence journals and therefore may hold different local trust matrices.
  - **In the Simulation Harness:** The simulator maintains a centralized **Simulator Canonical Evidence Journal** ($\mathcal{L}_{\text{sim}}$) as a harness construct to ensure simulated interactions are credited at most once in the global simulation matrix.
  - **No Direct Simulator Mutation:** Direct in-memory writes to matrix $S$ without an uncommitted journal record remain strictly prohibited.
- **Failure Conditions:** Mismatched index mapping; corrupted journal.
- **Security Assumptions:** Integrity of local storage and journal.

```
================================================================================
FLOW 15: EIGENTRUST COMPUTATION
================================================================================
```
- **Actors:** EigenTrust Engine ($E$)
- **Inputs:** Satisfaction matrix $S$, Pre-trusted seed set $\mathcal{P}$, damping factor $\alpha = 0.15$, convergence tolerance $\epsilon = 10^{-6}$, max iterations $K = 100$
- **Outputs:** Global reputation vector $\vec{t} \in \mathbb{R}^N$ such that $\sum_{i=1}^N t_i = 1.0$
- **Messages Exchanged:** None (local power-iteration calculation)
- **Mathematical Operations:**
  1. Construct normalized local trust matrix $C$:
     $$C_{ij} = \begin{cases} \frac{\max(S_{ij}, 0)}{\sum_k \max(S_{ik}, 0)} & \text{if } \sum_k \max(S_{ik}, 0) > 0 \\ p_j & \text{otherwise} \end{cases}$$
     where $\vec{p}$ is the uniform distribution vector over pre-trusted seed peers:
     $$p_j = \begin{cases} \frac{1}{|\mathcal{P}|} & \text{if } j \in \mathcal{P} \\ 0 & \text{otherwise} \end{cases}$$
  2. Initialize trust vector: $\vec{t}^{(0)} \leftarrow \vec{p}$.
  3. Power Iteration: For $k = 0, 1, \dots, K-1$:
     $$\vec{t}^{(k+1)} = (1 - \alpha) C^T \vec{t}^{(k)} + \alpha \vec{p}$$
     $$\delta = \|\vec{t}^{(k+1)} - \vec{t}^{(k)}\|_2$$
     If $\delta < \epsilon$, break.
- **State Changes:** Updates global score cache $\text{TrustScores}[DID] \leftarrow t_i$.
- **Validation Rules:** $\|\vec{t}\|_1 = 1.0$; $t_i \ge 0$ for all $i$.
- **Failure Conditions:** Singular matrix or non-convergence (guaranteed convergent by Perron-Frobenius theorem for column-stochastic $M = (1-\alpha)C^T + \alpha \vec{p} \vec{1}^T$).
- **Attacker Opportunities:** Colluding rings upvote each other. Damping factor $\alpha \vec{p}$ guarantees that trust without incoming edges from honest paths connected to $\mathcal{P}$ converges to zero.
- **Security Assumptions:** At least one pre-trusted seed peer remains uncompromised.

```
================================================================================
FLOW 16: ATTRIBUTABLE INCONSISTENT DELIVERY DETECTION
================================================================================
```
- **Actors:** Client / Detecting Peer ($D$), Accused Server ($S$)
- **Inputs:** Received chunk bytes $B'$, server-signed `ChunkResponse` envelope $M_{3.2}$, server-signed `ContentManifest` $Man_F$, authentic leaf proof $\Pi_{\text{authentic}}$
- **Outputs:** Certified `FaultEvidenceRecord` $\mathcal{E}_{\text{fault}}$
- **Messages Exchanged:** None (local detection upon Flow 9 failure)
- **Cryptographic Operations:**
  1. Re-evaluate chunk hash: $H(B') = \text{SHA-256}(B')$.
  2. Obtain authentic leaf digest $L_{\text{authentic}}$ and inclusion proof $\Pi_{\text{authentic}}$ for chunk index $k$ (from authentic publisher, redundant peer, or manifest).
  3. Verify authentic proof reaches root $R$: $\text{VerifyProof}(L_{\text{authentic}}, \Pi_{\text{authentic}}, k, R) == \text{True}$.
  4. Assert mathematical contradiction: $H(B') \ne L_{\text{authentic}}$.
  5. Confirm server signed delivery envelope committing to $H(B')$ and $H(\Pi_S)$ for $ReqID$.
  6. Assemble complete `FaultEvidenceRecord` containing both server's signed delivery envelope and authentic proof $\Pi_{\text{authentic}}$.
  7. Client signs fault report:
     $$\sigma_D \leftarrow \text{Ed25519.Sign}(sk_D, \text{"PKI\_V2\_EVIDENCE\_FAULT:"} \,\|\dots)$$
- **State Changes:** $D$ locally moves $S$'s state: $\mathcal{S}_S \leftarrow \text{SUSPECTED}$ (Certified Attributable Suspicion).
- **Validation Rules:** Evidence contains authentic proof reaching root $R$ and server signature committing to conflicting hash.
- **Failure Conditions:** Client cannot obtain authentic proof; delivered chunk matches authentic leaf.
- **Attacker Opportunities:** Client fabricates accusation (thwarted because client cannot forge server's signature on $H(B')$).
- **Security Assumptions:** Hash functions are collision-resistant; Ed25519 signatures are unforgeable.

```
================================================================================
FLOW 17: REVOCATION PROPOSAL
================================================================================
```
- **Actors:** Detecting Peer ($D$), Supernode Committee Members ($SN_1, \dots, SN_m$)
- **Inputs:** Certified fault evidence $\mathcal{E}_{\text{fault}}$
- **Outputs:** Revocation proposal submitted to governance queue
- **Messages Exchanged:**
  - $M_{7.1} (D \to SN_j): \text{PROPOSE\_REVOCATION}(ProposalID, D.DID, S.DID, \mathcal{E}_{\text{fault}}, t_{\text{prop}}, \sigma_D)$
- **Cryptographic Operations:**
  1. $D$ signs proposal message using $sk_D$.
  2. Each receiving supernode $SN_j$ verifies $\sigma_D$ and independently verifies the cryptographic validity of $\mathcal{E}_{\text{fault}}$ (Flow 13 Case B).
- **State Changes:** Supernodes record accused peer in state: $\mathcal{S}_S \leftarrow \text{REVOCATION\_PROPOSED}$. Proposal logged into pending ballot table with voting window $T_{\text{vote}}$.
- **Validation Rules:** $\mathcal{E}_{\text{fault}}$ passes Flow 13 validation; $S.DID$ is not already revoked.
- **Failure Conditions:** Malicious peer submits bogus proposal without authentic leaf proof; supernodes reject unproven proposal.
- **Attacker Opportunities:** Spamming supernodes (mitigated by requiring authentic Merkle contradiction proofs before opening a ballot).
- **Security Assumptions:** Supernode committee receives broadcast messages within latency bound.

```
================================================================================
FLOW 18: m-of-n REVOCATION APPROVAL & TIMEOUT FALLBACK
================================================================================
```
- **Actors:** Supernodes ($SN_1, \dots, SN_n$), Coordinator
- **Inputs:** Pending proposal $ProposalID$, Target $S.DID$, Threshold $m$ (e.g., 3-of-5), Voting window $T_{\text{vote}}$
- **Outputs:** Fully signed `CertificateRevocationRecord` (CRR) OR Quorum Timeout Fallback
- **Messages Exchanged:**
  - Intra-committee voting:
    $M_{7.2} (SN_j \to SN_{\text{coord}}): \text{VOTE\_CRR}(ProposalID, S.DID, \sigma_{SN_j})$
  - Supernode signature payload:
    $$\sigma_{SN_j} \leftarrow \text{Ed25519.Sign}(sk_{SN_j}, \text{"PKI\_V2\_CRR:"} \,\|\, CRRID \,\|\, S.DID \,\|\, pk_S \,\|\, \text{Reason} \,\|\, EvID \,\|\, t_{\text{crr}})$$
- **Cryptographic Operations:**
  1. Coordinator aggregates $k$ valid supernode signatures.
  2. For each signature, verify against recognized supernode public key.
- **State Changes:**
  - **Case 1 (Quorum Reached, $k \ge m$ within $T_{\text{vote}}$):**
    Assemble finalized CRR: $CRR = \langle \dots, \{\text{did}_j: \sigma_j\}_{j=1}^m \rangle$.
    Accused peer transitions to: $\mathcal{S}_S \leftarrow \text{REVOKED}$ (Permanent Eviction).
  - **Case 2 (Quorum Timeout, $k < m$ after $T_{\text{vote}}$):**
    Proposal expires. Accused peer transitions from `REVOCATION_PROPOSED` back to: $\mathcal{S}_S \leftarrow \text{SUSPECTED}$ (**NEVER** to `ACTIVE`).
    *Rationale:* An un-revoked peer with pending cryptographic fault evidence remains suspected and retains degraded trust until formal administrative adjudication or key rotation.
- **Validation Rules:**
  1. Exactly $\ge m$ distinct, verified supernodes for CRR approval.
  2. All signatures cover identical CRR payload.
- **Failure Conditions:** Insufficient supernodes online ($k < m$).
- **Attacker Opportunities:** Up to $m-1$ compromised supernodes refuse to sign (thwarted if threshold $m$ honest supernodes participate).
- **Security Assumptions:** At least $m$ supernodes are honest and non-colluding.

```
================================================================================
FLOW 19: REVOCATION PROPAGATION
================================================================================
```
- **Actors:** Coordinating Supernode ($SN_{\text{coord}}$), Swarm Peers ($P_1, \dots, P_N$)
- **Inputs:** Finalized CRR
- **Outputs:** Network-wide delivery of revocation record
- **Messages Exchanged:**
  - Gossip broadcast protocol:
    $M_{7.3} (SN \to \text{Peers}): \text{GOSSIP\_CRR}(CRR)$
    $M_{7.4} (P_i \to P_k): \text{GOSSIP\_CRR}(CRR)$
- **Cryptographic Operations:**
  Every receiving peer $P_i$ checks quorum:
  1. Count valid signatures: $k = \sum_{j} \mathbf{1}_{\text{Valid}}(\text{Ed25519.Verify}(pk_{SN_j}, \text{CRR\_Payload}, \sigma_{SN_j}))$.
  2. Assert $k \ge m$.
- **State Changes:**
  Peer $P_i$ updates local registry:
  - $\mathcal{S}_S \leftarrow \text{REVOKED}$.
  - Append to Local Revocation Store: $\mathcal{LRS} \leftarrow \mathcal{LRS} \cup \{CRR\}$.
  - Zero out all satisfaction entries: $S_{*, S} \leftarrow 0$; $S_{S, *} \leftarrow 0$.
- **Validation Rules:** Quorum verification must pass before relaying the gossip packet.
- **Failure Conditions:** Network partition delaying propagation.
- **Attacker Opportunities:** Malicious peer drops CRR packets (circumvented by multi-path epidemic gossip relay).
- **Security Assumptions:** Gossip network has expander graph connectivity ensuring $O(\log N)$ broadcast diameter.

```
================================================================================
FLOW 20: PEER EVICTION
================================================================================
```
- **Actors:** Local Node ($V$), Revoked Peer ($S$)
- **Inputs:** Certified CRR in local revocation store $\mathcal{LRS}$
- **Outputs:** Severed connections, blocked routing, purged trust state
- **Messages Exchanged:**
  - Optional termination notice:
    $M_{8.1} (V \to S): \text{EVICT\_NOTICE}(S.DID, CRRID)$
- **Cryptographic Operations:** None
- **State Changes:**
  1. Terminate all active transport sockets/channels to $S$.
  2. Block incoming connection attempts from $S.DID$ and $pk_S$.
  3. Remove $S$ from routing tables and neighbor lists.
  4. Invalidate all cross-certificates where $S$ is issuer or subject.
  5. Exclude $S$ from future EigenTrust iteration matrices.
- **Validation Rules:** Eviction is irrevocable unless a valid recovery/rotation certificate superseding the CRR is established under governance rules.
- **Failure Conditions:** None.
- **Attacker Opportunities:** Revoked peer changes alias (thwarted because eviction is keyed to $pk_S$; creating new key requires new PoW and reset reputation).
- **Security Assumptions:** Local enforcement logic correctly filters network packets.

```
================================================================================
FLOW 21: KEY ROTATION
================================================================================
```
- **Actors:** Peer ($P$) wishing to rotate key, Swarm Peers ($V$)
- **Inputs:** Old keypair $(sk_{\text{old}}, pk_{\text{old}})$, New keypair $(sk_{\text{new}}, pk_{\text{new}})$, Fresh PoW nonce $N_{\text{new}}$
- **Outputs:** `KeyRotationCertificate` $RotCert$
- **Messages Exchanged:**
  - $M_{9.1} (P \to \text{Network}): \text{ANNOUNCE\_ROTATION}(RotCert)$
- **Cryptographic Operations:**
  1. $P$ solves PoW for new key: $\text{SHA-256}(pk_{\text{new}} \,\|\dots) < Target$.
  2. Dual-signing rotation proof:
     $$\sigma_{\text{old}} \leftarrow \text{Ed25519.Sign}(sk_{\text{old}}, \text{"PKI\_V2\_ROTATE:"} \,\|\, DID_{\text{old}} \,\|\, pk_{\text{new}} \,\|\, t_{\text{rot}})$$
     $$\sigma_{\text{new}} \leftarrow \text{Ed25519.Sign}(sk_{\text{new}}, \text{"PKI\_V2\_ROTATE:"} \,\|\, DID_{\text{old}} \,\|\, pk_{\text{new}} \,\|\, t_{\text{rot}})$$
- **State Changes:**
  - $V$ updates identity mapping: $DID_{\text{new}} \leftarrow \text{RotateAlias}(DID_{\text{old}})$.
  - Mark $pk_{\text{old}}$ as `RETIRED`.
  - Transfer historical reputation or cross-certificates to $pk_{\text{new}}$ according to rotation policy.
- **Validation Rules:**
  1. Both $\sigma_{\text{old}}$ and $\sigma_{\text{new}}$ are valid.
  2. $pk_{\text{old}}$ was not in `REVOKED` state prior to $t_{\text{rot}}$.
  3. Freshness check: $t_{\text{rot}}$ within acceptable window.
- **Failure Conditions:** Old private key lost before signing rotation (must use Flow 22); old key already revoked.
- **Attacker Opportunities:** Thief of $sk_{\text{old}}$ rushes rotation (mitigated by key recovery authorization delay).
- **Security Assumptions:** $P$ controls both $sk_{\text{old}}$ and $sk_{\text{new}}$ at the moment of planned rotation.

```
================================================================================
FLOW 22: KEY RECOVERY
================================================================================
```
- **Actors:** Requester ($P_{\text{recov}}$), Custodian Nodes ($C_1, \dots, C_n$), Recovery Coordinator
- **Inputs:** Shamir threshold $k$, total shares $n$, pre-shared secret key or seed integer $S \in \mathbb{F}_P$, field prime $P = 2^{256} - 189$
- **Outputs:** Reconstructed key material, followed by mandatory immediate key rotation
- **Detailed Protocol Sub-Stages:**
  1. **Secret Sharing (Setup Phase):**
     - Peer $P$ splits root identity seed $S$ into $n$ shares using Shamir's polynomial $f(x) = S + \sum_{i=1}^{k-1} a_i x^i \pmod P$.
     - Each custodian $C_j$ receives $(j, f(j))$ encrypted under $C_j$'s public key.
  2. **Authorization to Request Recovery:**
     - Requester $P_{\text{recov}}$ must present an authorized recovery credential (e.g., pre-registered out-of-band identity proof, multi-party guardian authorization token $AuthTok$).
     - Shamir alone provides zero authentication; custodians reject requests lacking valid $AuthTok$.
  3. **Authentication of Recovery Participants:**
     - Custodian $C_j$ verifies requester's authorization challenge: $\text{Verify}(AuthTok)$.
     - Custodian $C_j$ signs and encrypts share payload:
       $$M_{10.1} (C_j \to P_{\text{recov}}): \text{SHARE\_RESP}(j, \text{Enc}_{pk_{\text{recov}}}(f(j)), \sigma_{C_j})$$
     - Requester verifies custodian signature $\sigma_{C_j}$.
  4. **Reconstruction:**
     - Requester gathers $k$ distinct shares $\{(x_1, y_1), \dots, (x_k, y_k)\}$.
     - Evaluates Lagrange interpolation at $x=0 \pmod P$:
       $$S = \sum_{j=1}^k y_j \prod_{m \ne j} \frac{-x_m}{x_j - x_m} \pmod P$$
  5. **Mandatory Post-Recovery Key Rotation:**
     - Reconstructed key $S$ is considered exposed/compromised during transit.
     - Requester MUST immediately execute Flow 21: generate brand-new keypair $(sk_{\text{fresh}}, pk_{\text{fresh}})$, issue a rotation certificate signed by recovered $S$, retire $S$, and bind the identity to $pk_{\text{fresh}}$.
- **State Changes:** Identity keys updated; historical identity resumed under new key; custodians log recovery event.
- **Validation Rules:** Exactly $\ge k$ valid shares; authorized requester token verified.
- **Failure Conditions:** Fewer than $k$ custodians respond; rogue custodian delivers corrupted share.
- **Attacker Opportunities:** Unauthorized party requests shares (prevented by strict authorization challenge).
- **Security Assumptions:** At least $k$ custodians remain honest, online, and do not collude against the secret owner.

---

## 4. Supernode Requirements & Deferred Election Specification

### 4.1 Identified Flaws from Phase 1 Audit
As documented in [AUDIT.md](reports/AUDIT.md), the original threshold of `score >= 0.65` is mathematically unreachable in an $N$-node network where $\sum_{i=1}^N t_i = 1.0$.

### 4.2 Supernode Role Requirements
A node is eligible to serve as a Supernode / Quorum Validator only if it satisfies the following verifiable preconditions:
1. **Cryptographic Identity & Admission:** Fully verified `P2PCertificate` with valid PoW.
2. **Reputation Ranking:** Positioned within the top rank of converged EigenTrust scores (e.g., top percentile or committee size quota).
3. **Availability & Liveness:** Proven continuous availability authenticated by periodic signed heartbeat receipts over a minimum window $T_{\text{epoch}}$.
4. **Clean Evidence History:** Zero active `FaultEvidenceRecord` entries and zero `SUSPECTED` or `REVOCATION_PROPOSED` flags in the local and gossip registry.
5. **Capacity Commitment:** Published capabilities exceeding minimum supernode thresholds (e.g., bandwidth, storage, routing capacity).

### 4.3 Deferred Decision Notice
> [!IMPORTANT]
> The dynamic supernode election algorithm, including the specific mathematical threshold function (e.g., dynamic percentile vs. staking vs. multi-metric scoring), epoch transition protocol, and Byzantine fault handling, is explicitly designated as an **OPEN ARCHITECTURAL DECISION** to be finalized in a future phase. In the prototype, initial supernode seeds are established as a static bootstrap set $\mathcal{P}_0$.

---

## 5. Replay Protection, Accounting Architecture & Evidence Pipeline

### 5.1 Replay Protection & Accounting Pipeline

To prevent double-counting of reputation, the protocol defines five strictly ordered filtering stages:

```
+-------------------------------------------------------------------------------+
| Step 1: Timestamp Freshness Filter                                            |
|  - Validates |t_current - t_tx| <= W (600s). Rejects stale receipts instantly. |
+-------------------------------------------------------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------------+
| Step 2: Interaction Nonce Replay Cache                                        |
|  - Checks nu not in N_seen. Rejects duplicate interaction nonces.             |
+-------------------------------------------------------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------------+
| Step 3: Journal Deduplication Check                                           |
|  - Checks TxID / EvidenceID not in L_local (or L_sim in harness).             |
+-------------------------------------------------------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------------+
| Step 4: Cryptographic Signature Verification                                  |
|  - Verifies counterparty signatures and domain-separated payloads.            |
+-------------------------------------------------------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------------+
| Step 5: Journal Commit & Matrix Update                                        |
|  - Commits ID to journal and updates satisfaction matrix S.                   |
+-------------------------------------------------------------------------------+
```

### 5.2 Accounting Architecture: Local vs. Simulator

The protocol explicitly distinguishes between local peer accounting and simulation harness accounting:
1. **Node-Local Processed Evidence Journal ($\mathcal{L}_{\text{local}}$):**
   - Maintained independently by each decentralized peer.
   - Ensures that an individual peer never credits the same $TxID$ or $EvidenceID$ more than once to its local satisfaction matrix $S$.
   - **No Global Ledger:** In the absence of distributed consensus, different peers may observe different interactions, possess different local journals, and temporarily or permanently hold different local trust matrices.
2. **Simulator Canonical Evidence Journal ($\mathcal{L}_{\text{sim}}$):**
   - Maintained exclusively by the `SwarmSimulation` test harness.
   - Acts as an experimental coordinator ensuring simulated transactions are applied at most once to the benchmark simulation matrix.

---

## 6. Summary of Protocol Message Schemas

| Message Code | Name | Sender | Receiver | Content Summary |
| :--- | :--- | :--- | :--- | :--- |
| `0x01` | `REGISTER_REQ` | Peer | Verifier | `P2PCertificate` with PoW nonce and self-signature |
| `0x02` | `REGISTER_RESP` | Verifier | Peer | Admission status, timestamp, verifier signature |
| `0x05` | `CROSS_CERT` | Issuer | Subject | `CrossCertificate` with 4-decimal weight and issuer signature |
| `0x10` | `CONTENT_REQ` | Client | Server | `ContentRequest` binding $ReqID$, client/server DIDs, root, index, nonce, client sig |
| `0x11` | `CHUNK_RESP` | Server | Client | `ChunkResponse` binding $ReqID$, chunk hash, proof hash, root, index, server sig |
| `0x20` | `PROPOSE_RECEIPT`| Client | Server | Receipt proposal, rating (`"+1.00"` or `"-1.00"`), client signature |
| `0x21` | `ACK_RECEIPT` | Server | Client | Server counter-signature on identical receipt payload |
| `0x30` | `SUBMIT_EVIDENCE`| Peer | Engine | Dual-signed receipt or certified fault report |
| `0x40` | `PROPOSE_REVOCATION`| Peer | Supernodes | Certified `FaultEvidenceRecord`, accused DID, authentic proof, proposal sig |
| `0x41` | `VOTE_CRR` | Supernode | Coordinator | Supernode co-signature on proposed CRR |
| `0x42` | `GOSSIP_CRR` | Supernode | Swarm | Finalized CRR with $m$-of-$n$ supernode signatures |
| `0x50` | `ANNOUNCE_ROTATION`| Peer | Swarm | `KeyRotationCertificate` dual-signed with old and new keys |
| `0x60` | `SHARE_REQ` | Requester | Custodian | Authorization token, identity challenge |
| `0x61` | `SHARE_RESP` | Custodian | Requester | Encrypted Shamir polynomial share, custodian signature |
