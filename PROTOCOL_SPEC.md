# Decentralized P2P PKI & Trust Management — Protocol Specification
**Document Version:** 2.1.0-SPEC (Corrected Architecture Baseline)  
**Status:** Approved Protocol Specification  
**Target Architecture:** 4-Layer Hybrid P2P Trust Mesh  
**Baseline Reference:** [AUDIT.md](file:///d:/pki_casestudy/AUDIT.md)

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

### 2.1 Peer Lifecycle States

Every peer in the network resides in exactly one lifecycle state:
$$\mathcal{S} \in \{\text{UNKNOWN}, \text{ACTIVE}, \text{SUSPECTED}, \text{REVOCATION\_PROPOSED}, \text{REVOKED}\}$$

```
   [ UNKNOWN ]
        |
        | Register (PoW + Sig Valid)
        v
   [ ACTIVE ] <-------------------+
        |                         | Inconsistency Disproven /
        | Attributable Bad        | Timeout Expired
        | Delivery Certified      |
        v                         |
   [ SUSPECTED ] -----------------+
        |
        | Quorum Threshold Sponsor Reached
        v
   [ REVOCATION_PROPOSED ]
        |
        | m-of-n Supernode Quorum Approved (CRR)
        v
   [ REVOKED ] (Permanent Eviction)
```

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
  "merkle_root": "a1b2c3...",
  "timestamp": 1775500016.0,
  "nonce": "n-88192a",
  "merkle_proof": [
    {"sibling_hash": "c4d5e6...", "is_left": false}
  ],
  "server_sig_hex": "44cc..."
}
```
*Signed Payload (Server Envelope):* `PKI_V2_RESP:<req_id>:<client_did>:<server_did>:<content_id>:<chunk_index>:<chunk_hash>:<merkle_root>:<timestamp>:<nonce>`

#### `BilateralReceipt`
```json
{
  "tx_id": "tx-8f7b-4a21-99c0",
  "client_did": "did:peer:2.EzClient...",
  "client_pubkey_hex": "b3c2...",
  "server_did": "did:peer:2.EzServer...",
  "server_pubkey_hex": "9a4b...",
  "merkle_root": "a1b2c3...",
  "rating": 1.0,
  "timestamp": 1775500025.0,
  "nonce": "7c9f8021a",
  "client_sig_hex": "1122...",
  "server_sig_hex": "3344..."
}
```
*Signed Payload:* `PKI_V2_RECEIPT:<tx_id>:<client_did>:<server_did>:<merkle_root>:<rating>:<timestamp>:<nonce>`
*Rating Semantics:*
- `+1.0`: Successful bilateral fulfillment. Both parties co-sign certifying successful delivery.
- `-1.0`: Bilateral negative/dispute receipt. Both parties co-sign acknowledging unfulfilled contract or settled dispute. (Does NOT constitute cryptographic fault proof; treated as a mutual behavioral dispute signal).

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
  "delivered_chunk_bytes_hex": "504f49534f4e...",
  "delivered_chunk_hash": "e3b0c4...",
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
    "merkle_root": "a1b2c3...",
    "timestamp": 1775500016.0,
    "nonce": "n-88192a",
    "server_sig_hex": "44cc..."
  },
  "timestamp": 1775500020.0,
  "reporter_sig_hex": "5566..."
}
```
*Signed Payload:* `PKI_V2_EVIDENCE_FAULT:<evidence_id>:<req_id>:<reporter_did>:<accused_did>:<content_id>:<merkle_root>:<chunk_index>:<delivered_chunk_hash>:<timestamp>`

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
FLOW 6: CONTENT / CHUNK DISTRIBUTION WITH CRYPTOGRAPHIC BINDING
================================================================================
```
- **Actors:** Serving Peer ($S$), Downloader Peer ($C$)
- **Inputs:** Validated `ContentRequest` ($ReqID, C.DID, S.DID, ContentID, k, R, t_{req}, \nu_{req}$), chunk bytes $B_k$, Merkle inclusion proof $\Pi_k$, Content Manifest $Man_F$
- **Outputs:** Formatted, signed delivery payload `ChunkResponse`
- **Messages Exchanged:**
  - $M_{3.2} (S \to C): \text{CHUNK\_RESP}(ReqID, C.DID, S.DID, ContentID, k, B_k, H(B_k), R, t_{resp}, \nu_{req}, \Pi_k, \sigma_S)$
- **Cryptographic Operations:**
  1. $S$ computes chunk digest: $H(B_k) = \text{SHA-256}(B_k)$.
  2. $S$ signs the comprehensive delivery envelope binding request, chunk hash, root, and client DID:
     $$\sigma_S \leftarrow \text{Ed25519.Sign}(sk_S, \text{"PKI\_V2\_RESP:"} \,\|\, ReqID \,\|\, C.DID \,\|\, S.DID \,\|\, ContentID \,\|\, k \,\|\, H(B_k) \,\|\, R \,\|\, t_{resp} \,\|\, \nu_{req})$$
- **State Changes:** $S$ logs chunk dispatch in pending receipt queue.
- **Validation Rules:**
  1. $\text{Ed25519.Verify}(pk_S, \text{"PKI\_V2\_RESP:"} \dots, \sigma_S) == \text{True}$.
  2. Envelope fields ($ReqID, C.DID, S.DID, ContentID, k, R, \nu_{req}$) strictly match client's pending request record.
  3. Computed $\text{SHA-256}(B_k)$ strictly matches envelope's $H(B_k)$.
- **Failure Conditions:** Chunk read error on server; connection reset; signature verification failure.
- **Attacker Opportunities:** Malicious server attempts to substitute chunk $B_k$ with poisoned bytes $B'_k$. Crucially, because $\sigma_S$ explicitly commits to $H(B'_k)$ bound to $ReqID$ and $R$, any mismatch provides non-repudiable evidence against $S$.
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
     - If $k$ is even: sibling is at $k+1$ (or $k$ if odd terminal); direction is RIGHT.
     - If $k$ is odd: sibling is at $k-1$; direction is LEFT.
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
     - If $\text{dir}_j == \text{RIGHT}$: $H_{j+1} \leftarrow \text{SHA-256}(\text{raw}(H_j) \,\|\, \text{raw}(S_j))$.
     - If $\text{dir}_j == \text{LEFT}$: $H_{j+1} \leftarrow \text{SHA-256}(\text{raw}(S_j) \,\|\, \text{raw}(H_j))$.
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
     $$\sigma_C \leftarrow \text{Ed25519.Sign}(sk_C, \text{"PKI\_V2\_RECEIPT:"} \,\|\, TxID \,\|\, C.DID \,\|\, S.DID \,\|\, R \,\|\, \text{f"{rating:.2f}"} \,\|\, t_{tx} \,\|\, \nu)$$
- **State Changes:** Client records receipt state as `PROPOSED_SENT`.
- **Validation Rules:**
  - Rating must be $+1.0$ (satisfactory fulfillment) or $-1.0$ (bilateral dispute/unfulfilled contract).
  - Timestamp freshness $|t_{\text{current}} - t_{tx}| \le 60\text{s}$.
- **Failure Conditions:** Connection dropped before receipt negotiation.
- **Attacker Opportunities:** Client attempts to propose rating $< 1.0$ despite receiving valid chunks, or demands rating without transaction. Server refuses to sign.
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
     $$\sigma_S \leftarrow \text{Ed25519.Sign}(sk_S, \text{"PKI\_V2\_RECEIPT:"} \,\|\, TxID \,\|\, C.DID \,\|\, S.DID \,\|\, R \,\|\, \text{f"{rating:.2f}"} \,\|\, t_{tx} \,\|\, \nu)$$
- **State Changes:** Both $C$ and $S$ persist completed bilateral receipt $Rcpt$ in their local transaction journals.
- **Validation Rules:** Both $\sigma_C$ and $\sigma_S$ must verify under their respective public keys against the exact same byte string.
- **Failure Conditions:** Signature verification failure; payload discrepancy.
- **Attacker Opportunities:** Server refuses to co-sign after providing data (server denies itself positive credit; client still possesses file).
- **Security Assumptions:** Mutual non-repudiation: neither party can claim the receipt was generated unilaterally.

```
================================================================================
FLOW 12: RECEIPT REPLAY DETECTION & CANONICAL ACCOUNTING
================================================================================
```
- **Actors:** Reputation Accounting Node / Verifier ($V$)
- **Inputs:** Candidate receipt $Rcpt = \langle TxID, C.DID, S.DID, R, \text{rating}, t_{tx}, \nu, \sigma_C, \sigma_S \rangle$
- **Outputs:** Verification status $\in \{\text{ACCEPTED}, \text{DUPLICATE\_REJECTED}, \text{STALE\_REJECTED}\}$
- **State Maintained:**
  - Canonical Processed Ledger: $\mathcal{L}_{\text{canon}} = \{TxID_1, TxID_2, \dots \}$
  - Replay Nonce Cache: $\mathcal{N}_{\text{seen}} = \{\nu_1, \nu_2, \dots \}$
  - Max Freshness Window: $W = 600\text{ seconds}$
- **Messages Exchanged:** None (internal validation pipeline)
- **Cryptographic Operations:** None (cache and integer comparisons prior to crypto checks)
- **State Changes:**
  - If valid: $\mathcal{L}_{\text{canon}} \leftarrow \mathcal{L}_{\text{canon}} \cup \{TxID\}$; $\mathcal{N}_{\text{seen}} \leftarrow \mathcal{N}_{\text{seen}} \cup \{\nu\}$.
  - Periodic garbage collection: Nonce entries older than $t_{\text{current}} - W$ may be evicted; canonical $TxID$ ledger entries persist to guarantee at-most-once reputation accounting.
- **Validation Rules:**
  1. $t_{tx} \ge t_{\text{current}} - W$ (receipt is within freshness window).
  2. $t_{tx} \le t_{\text{current}} + \Delta t_{\text{drift}}$ (timestamp is not in the future; $\Delta t_{\text{drift}} = 15\text{s}$).
  3. $TxID \notin \mathcal{L}_{\text{canon}}$ (receipt has never contributed to reputation before).
  4. $\nu \notin \mathcal{N}_{\text{seen}}$ (entropy nonce is unique).
- **Failure Conditions:** Replayed transaction ID; expired timestamp; future timestamp.
- **Attacker Opportunities:** Re-submitting a captured valid receipt to multiple nodes or across rounds (thwarted by the canonical uniqueness check on $TxID$).
- **Security Assumptions:** Verifier storage persistence across restarts.

```
================================================================================
FLOW 13: EVIDENCE VALIDATION & INCONSISTENT DELIVERY PROOF
================================================================================
```
- **Actors:** Reputation Engine ($E$)
- **Inputs:** Candidate evidence item $\mathcal{E}$ (either `BilateralReceipt` or `FaultEvidenceRecord`)
- **Outputs:** Validated evidence status $\in \{\text{VALID}, \text{INVALID}\}$
- **Messages Exchanged:**
  - $M_{6.1} (P \to E): \text{SUBMIT\_EVIDENCE}(\mathcal{E})$
- **Cryptographic Operations & Deduction Logic:**
  - **Case A: `BilateralReceipt`:**
    1. Verify client signature $\sigma_C$ on `PKI_V2_RECEIPT:` payload.
    2. Verify server signature $\sigma_S$ on `PKI_V2_RECEIPT:` payload.
    3. Check canonical uniqueness: $TxID \notin \mathcal{L}_{\text{canon}}$.
    4. *Classification:*
       - If `rating == +1.0`: Certified successful bilateral interaction.
       - If `rating == -1.0`: Certified bilateral transaction dispute (behavioral signal).
  - **Case B: `FaultEvidenceRecord` (Server-Attributable Delivery Contradiction):**
    A verifier evaluates the 7-step deduction:
    1. Verify server signature on `manifest_envelope`: Server published and signed root $R$ for $ContentID$.
    2. Confirm manifest commits to Merkle root $R$.
    3. Verify server signature $\sigma_S$ on `delivery_envelope`: Server cryptographically signed delivery response for $ReqID$, $ContentID$, chunk index $k$, root $R$, committing to chunk digest $H(B')$.
    4. Verify that $H(B') == \text{SHA-256}(B')$, proving that client received chunk $B'$ corresponding to server's signed commitment.
    5. Evaluate Merkle inclusion: Prove that $H(B')$ contradicts root $R$ at index $k$ (no valid inclusion proof exists linking $H(B')$ to $R$, or provided proof evaluates to root $R' \ne R$).
    6. Verify reporter signature $\sigma_R$ on `PKI_V2_EVIDENCE_FAULT:` payload.
    7. **Deduction:** The evidence mathematically binds the contradictory delivery to the server's private key.
    *(Explicit Non-Property: This proves server-attributable inconsistent delivery; it does NOT prove malicious intent. Causes may include hardware bit-rot, cache bug, or intentional poisoning).*
- **State Changes:** Validated record entered into raw interaction journal $\mathcal{J}$ and committed to $\mathcal{L}_{\text{canon}}$.
- **Validation Rules:** All public keys unrevoked; signatures mathematically sound; canonical ID unique.
- **Failure Conditions:** Invalid signature; delivered chunk actually matches root; accused server did not sign delivery envelope.
- **Attacker Opportunities:** Fabricate fault evidence (impossible because client cannot forge server's signature $\sigma_S$ over $H(B')$).
- **Security Assumptions:** EUF-CMA security of Ed25519; collision resistance of SHA-256.

```
================================================================================
FLOW 14: TRUST-MATRIX UPDATE & SEPARATED EVIDENCE SEMANTICS
================================================================================
```
- **Actors:** Local Trust Accounting Node ($E$)
- **Inputs:** Validated interaction journal $\mathcal{J}$ containing validated receipts and fault reports
- **Outputs:** Updated satisfaction matrix $S \in \mathbb{R}^{N \times N}$
- **Messages Exchanged:** None (local deterministic state transition)
- **Cryptographic Operations:** None
- **State Changes & Evidence Semantics:**
  For each new, validated, non-replayed record $r \in \mathcal{J}$:
  1. **Successful Bilateral Receipt (`BilateralReceipt`, rating $+1.0$):**
     $$S_{C, S} \leftarrow S_{C, S} + 1.0$$
     *(If mutual exchange swarm tit-for-tat credit is enabled):*
     $$S_{S, C} \leftarrow S_{S, C} + 1.0$$
  2. **Bilateral Dispute Receipt (`BilateralReceipt`, rating $-1.0$):**
     $$S_{C, S} \leftarrow S_{C, S} - 1.0$$
     *Semantics:* Reflects mutual acknowledgement of a failed or cancelled transaction. It is a behavioral dispute signal. It does NOT trigger revocation.
  3. **Certified Fault Evidence (`FaultEvidenceRecord`):**
     $$S_{\text{reporter}, \text{accused}} \leftarrow S_{\text{reporter}, \text{accused}} - 2.0$$
     *Semantics:* Cryptographically verified inconsistent delivery. Triggers immediate local transition of accused to $\text{SUSPECTED}$ and escalation to Flow 17 (`PROPOSE_REVOCATION`).
- **Validation Rules:**
  **CANONICAL EVIDENCE ACCOUNTING RULE:**
  A transaction or evidence record contributes at most once to reputation based on its globally unique canonical identifier ($TxID$ or $EvidenceID$), regardless of how many peers relay or submit it.
  Every modification to $S_{i, j}$ MUST originate from an uncommitted record in $\mathcal{J}$. Direct in-memory mutation without proof is an illegal protocol violation.
- **Failure Conditions:** Mismatched index mapping; journal corruption.
- **Attacker Opportunities:** Colluding nodes generate infinite valid bilateral receipts between themselves (damped by Flow 15 pre-trusted seed damping).
- **Security Assumptions:** Integrity of local storage and canonical ledger.

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
- **Attacker Opportunities:** Sybil collectives upvote each other infinitely. Damping factor $\alpha \vec{p}$ guarantees that trust without incoming edges from honest paths connected to $\mathcal{P}$ converges to zero.
- **Security Assumptions:** At least one pre-trusted seed peer remains uncompromised.

```
================================================================================
FLOW 16: ATTRIBUTABLE INCONSISTENT DELIVERY DETECTION
================================================================================
```
- **Actors:** Client / Detecting Peer ($D$), Accused Server ($S$)
- **Inputs:** Received chunk bytes $B'$, server-signed `ChunkResponse` envelope $M_{3.2}$, server-signed `ContentManifest` $Man_F$
- **Outputs:** Certified `FaultEvidenceRecord` $\mathcal{E}_{\text{fault}}$
- **Messages Exchanged:** None (local detection upon Flow 9 failure)
- **Cryptographic Operations:**
  1. Re-evaluate chunk hash: $H(B') = \text{SHA-256}(B')$.
  2. Assert $H(B') \ne \text{ExpectedLeafHash}$.
  3. Confirm that server signed the response envelope committing to $H(B')$ for this $ReqID$.
  4. Confirm that server signed the manifest committing to root $R$.
  5. Assemble `FaultEvidenceRecord` binding manifest envelope, response envelope, and raw delivered chunk.
  6. Client signs fault report:
     $$\sigma_D \leftarrow \text{Ed25519.Sign}(sk_D, \text{"PKI\_V2\_EVIDENCE_FAULT:"} \,\|\dots)$$
- **State Changes:** $D$ locally moves $S$'s state: $\mathcal{S}_S \leftarrow \text{SUSPECTED}$.
- **Validation Rules:** The evidence contains a mathematically verifiable contradiction signed by $S$'s private key.
- **Failure Conditions:** Accused did not sign the delivery envelope; chunk actually matches root.
- **Attacker Opportunities:** Server claims client tampered with chunk (refuted because server's signed envelope contains $H(B')$ matching client's delivered chunk).
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
  2. Each receiving supernode $SN_j$ verifies $\sigma_D$ and independently verifies the cryptographic validity of $\mathcal{E}_{\text{fault}}$ (Flow 13).
- **State Changes:** Supernodes record accused peer in state: $\mathcal{S}_S \leftarrow \text{REVOCATION\_PROPOSED}$. Proposal logged into pending ballot table.
- **Validation Rules:** $\mathcal{E}_{\text{fault}}$ passes Flow 13 validation; $S.DID$ is not already revoked.
- **Failure Conditions:** Malicious peer submits bogus proposal without valid proof; supernode drops unverified proposal.
- **Attacker Opportunities:** Spamming supernodes with fake proposals (mitigated by requiring verifiable cryptographic fault proofs before opening a ballot).
- **Security Assumptions:** Supernode committee receives broadcast messages within latency bound.

```
================================================================================
FLOW 18: m-of-n REVOCATION APPROVAL
================================================================================
```
- **Actors:** Supernodes ($SN_1, \dots, SN_n$)
- **Inputs:** Pending proposal $ProposalID$, Target $S.DID$, Threshold $m$ (where $m \le n$, e.g., 3-of-5)
- **Outputs:** Fully signed `CertificateRevocationRecord` (CRR)
- **Messages Exchanged:**
  - Intra-committee voting:
    $M_{7.2} (SN_j \to SN_{\text{coord}}): \text{VOTE\_CRR}(ProposalID, S.DID, \sigma_{SN_j})$
  - Supernode signature payload:
    $$\sigma_{SN_j} \leftarrow \text{Ed25519.Sign}(sk_{SN_j}, \text{"PKI\_V2\_CRR:"} \,\|\, CRRID \,\|\, S.DID \,\|\, pk_S \,\|\, \text{Reason} \,\|\, EvID \,\|\, t_{\text{crr}})$$
- **Cryptographic Operations:**
  1. Coordinator aggregates $k$ signatures.
  2. For each signature, verify against supernode public key:
     $\text{Ed25519.Verify}(pk_{SN_j}, \dots, \sigma_{SN_j})$.
- **State Changes:** When valid signature count $k \ge m$:
  - Assemble finalized CRR: $CRR = \langle \dots, \{\text{did}_j: \sigma_j\}_{j=1}^m \rangle$.
  - Accused peer state: $\mathcal{S}_S \leftarrow \text{REVOKED}$.
- **Validation Rules:**
  1. Exactly $\ge m$ distinct, verified supernodes.
  2. All signatures cover the identical CRR payload.
  3. Supernode public keys belong to current recognized committee.
- **Failure Conditions:** Quorum not reached ($k < m$) within timeout window $T_{\text{vote}}$; proposal expires.
- **Attacker Opportunities:** Up to $m-1$ compromised supernodes refuse to sign or attempt to sign bogus revocations (thwarted by requiring $m$ signatures and attached cryptographic evidence).
- **Security Assumptions:** Fewer than $m$ supernodes are actively malicious.

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

## 4. Supernode Requirements & Election Specification

### 4.1 Identified Flaws from Phase 1 Audit
As documented in [AUDIT.md](file:///d:/pki_casestudy/AUDIT.md), the original threshold of `score >= 0.65` is mathematically unreachable in an $N$-node network where $\sum_{i=1}^N t_i = 1.0$.

### 4.2 Supernode Role Requirements
A node is eligible to serve as a Supernode / Quorum Validator only if it satisfies the following verifiable preconditions:
1. **Cryptographic Identity & Admission:** Fully verified `P2PCertificate` with valid PoW.
2. **Reputation Ranking:** Positioned within the top rank of converged EigenTrust scores (e.g., top percentile or committee size quota).
3. **Availability & Liveness:** Proven continuous availability authenticated by periodic signed heartbeat receipts over a minimum window $T_{\text{epoch}}$.
4. **Clean Evidence History:** Zero active `FaultEvidenceRecord` entries and zero `SUSPECTED` or `REVOCATION_PROPOSED` flags in the local and gossip registry.
5. **Capacity Commitment:** Published capabilities exceeding minimum supernode thresholds (e.g., bandwidth, storage, routing capacity).

### 4.3 Deferred Decision Notice
> [!IMPORTANT]
> The dynamic supernode election algorithm, including the specific mathematical threshold function (e.g., dynamic percentile vs. staking vs. multi-metric scoring), epoch transition protocol, and Byzantine fault handling, is explicitly designated as an **OPEN ARCHITECTURAL DECISION** to be finalized in the next design phase. In the interim, initial supernode seeds are established as a static bootstrap set $\mathcal{P}_0$.

---

## 5. Replay Protection, Canonical Accounting & Evidence Pipeline

### 5.1 Four-Layer Evidence & Replay Pipeline

To guarantee system consistency across distributed nodes and prevent double-counting of reputation, the protocol defines four distinct, non-overlapping filtering stages:

```
+-------------------------------------------------------------------------------+
| Layer A: Transport Duplicate Suppression                                       |
|  - Drops duplicate gossip/network packets via rolling message hash filter     |
+-------------------------------------------------------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------------+
| Layer B: Local Replay & Freshness Filter                                      |
|  - Validates timestamp window |t_current - t_tx| <= W (600s) & unique nonces  |
+-------------------------------------------------------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------------+
| Layer C: Canonical Evidence Uniqueness                                        |
|  - Checks global processed ledger: TxID / EvidenceID not in L_canon           |
+-------------------------------------------------------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------------+
| Layer D: Reputation Accounting Engine                                         |
|  - Commits validated record to L_canon and updates satisfaction matrix S      |
+-------------------------------------------------------------------------------+
```

1. **Layer A — Transport Duplicate Suppression:** Discards redundant peer-to-peer network frames (e.g., gossip duplicates) using a bounded rolling filter.
2. **Layer B — Local Replay & Freshness Filter:** Enforces sliding window $W = 600\text{ seconds}$ and cache $\mathcal{N}_{\text{seen}}$ for interaction nonces to prevent attackers from replaying stale messages.
3. **Layer C — Canonical Evidence Uniqueness:** Ensures that each semantic transaction or fault record is identified by an authoritative, immutable identifier ($TxID$ or $EvidenceID$). A node checks its persistent processed set $\mathcal{L}_{\text{canon}}$. If present, the record is recognized as already counted and ignored for further accounting.
4. **Layer D — Reputation Accounting Engine:** Applies the deterministic state update to matrix $S$ exactly once per canonical record:
   $$\text{TxID / EvidenceID} \notin \mathcal{L}_{\text{canon}} \implies \text{Commit to } \mathcal{L}_{\text{canon}} \land \text{Update } S_{ij}$$

### 5.2 Distinct Evidence Semantics

The protocol establishes three separate evidence tiers with strictly defined effects on the trust matrix and node lifecycle:

| Evidence Tier | Structure | Signatures Required | Effect on Matrix $S$ | Lifecycle Impact |
| :--- | :--- | :--- | :--- | :--- |
| **Tier 1: Successful Delivery** | `BilateralReceipt` ($+1.0$) | Client + Server | $S_{C, S} \leftarrow S_{C, S} + 1.0$ | Peer remains `ACTIVE` |
| **Tier 2: Mutual Dispute** | `BilateralReceipt` ($-1.0$) | Client + Server | $S_{C, S} \leftarrow S_{C, S} - 1.0$ | Peer remains `ACTIVE` (behavioral signal only; no revocation) |
| **Tier 3: Attributable Bad Delivery** | `FaultEvidenceRecord` | Server (manifest) + Server (delivery envelope) + Client (report) | $S_{C, S} \leftarrow S_{C, S} - 2.0$ | Accused moves to `SUSPECTED` $\to$ triggers `PROPOSE_REVOCATION` |

### 5.3 Cryptographic Attribution of Inconsistent Delivery

To prevent uncorroborated accusations, a `FaultEvidenceRecord` is admissible if and only if a verifier can establish all seven conditions:
1. **Manifest Authenticity:** Accused server $S$ signed the `ContentManifest` containing root $R$.
2. **Root Commitment:** Manifest establishes root $R$ as the authoritative root for $ContentID$.
3. **Delivery Response Authenticity:** Accused server $S$ signed `ChunkResponse` for request $ReqID$.
4. **Request/Response Parameter Binding:** Signed delivery envelope explicitly binds $ReqID$, client $DID$, server $DID$, $ContentID$, chunk index $k$, root $R$, and delivered chunk hash $H(B')$.
5. **Physical Byte Match:** Received chunk bytes $B'$ hash to $H(B')$ ($\text{SHA-256}(B') == H(B')$).
6. **Mathematical Contradiction:** Chunk hash $H(B')$ contradicts Merkle root $R$ for chunk index $k$ (the inclusion proof fails or proves contradiction).
7. **Attribution:** The contradiction is bound to the server's private key via its own signature on the delivery envelope.

> [!CAUTION]
> **Attribution vs. Intent:** This proof establishes **cryptographically attributable inconsistent delivery**. It does **not** prove malicious intent. Inconsistent delivery may arise from storage bit-rot, cache bug, or intentional poisoning.

---

## 6. Summary of Protocol Message Schemas

| Message Code | Name | Sender | Receiver | Content Summary |
| :--- | :--- | :--- | :--- | :--- |
| `0x01` | `REGISTER_REQ` | Peer | Verifier | `P2PCertificate` with PoW nonce and self-signature |
| `0x02` | `REGISTER_RESP` | Verifier | Peer | Admission status, timestamp, verifier signature |
| `0x10` | `CONTENT_REQ` | Client | Server | `ContentRequest` binding $ReqID$, client/server DIDs, root, index, nonce, client sig |
| `0x11` | `CHUNK_RESP` | Server | Client | `ChunkResponse` binding $ReqID$, chunk hash, root, index, server sig |
| `0x20` | `PROPOSE_RECEIPT`| Client | Server | Receipt proposal, rating ($+1.0$ or $-1.0$), client signature |
| `0x21` | `ACK_RECEIPT` | Server | Client | Server counter-signature on identical receipt payload |
| `0x30` | `SUBMIT_EVIDENCE`| Peer | Engine | Dual-signed receipt or certified fault report |
| `0x40` | `PROPOSE_REVOCATION`| Peer | Supernodes | Certified `FaultEvidenceRecord`, accused DID, proposal signature |
| `0x41` | `VOTE_CRR` | Supernode | Coordinator | Supernode co-signature on proposed CRR |
| `0x42` | `GOSSIP_CRR` | Supernode | Swarm | Finalized CRR with $m$-of-$n$ supernode signatures |
| `0x50` | `ANNOUNCE_ROTATION`| Peer | Swarm | `KeyRotationCertificate` dual-signed with old and new keys |
| `0x60` | `SHARE_REQ` | Requester | Custodian | Authorization token, identity challenge |
| `0x61` | `SHARE_RESP` | Custodian | Requester | Encrypted Shamir polynomial share, custodian signature |
