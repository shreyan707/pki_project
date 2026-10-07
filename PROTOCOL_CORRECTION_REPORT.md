# Decentralized P2P PKI & Trust Management — Protocol Correction Report
**Document Version:** 1.0.0  
**Date:** October 8, 2026  
**Role:** Protocol Correction Agent  
**Baseline References:** [AUDIT.md](file:///d:/pki_casestudy/AUDIT.md), [PROTOCOL_SPEC.md](file:///d:/pki_casestudy/PROTOCOL_SPEC.md), [SECURITY_MODEL.md](file:///d:/pki_casestudy/SECURITY_MODEL.md)

---

## Executive Summary

Following the Phase 1 audit and initial protocol formulation, a rigorous adversarial review identified five critical specification-level gaps in chunk poisoning evidence attribution, request/response cryptographic binding, negative receipt semantics, global evidence accounting, and security property claims.

This report documents the precise corrections applied exclusively to:
- [`PROTOCOL_SPEC.md`](file:///d:/pki_casestudy/PROTOCOL_SPEC.md)
- [`SECURITY_MODEL.md`](file:///d:/pki_casestudy/SECURITY_MODEL.md)

No source code, unit tests, benchmark scripts, or presentation assets were modified.

---

## Correction 1: Chunk Poisoning Evidence & Server Attribution

### 1. Issue
In the initial protocol draft, `FaultEvidenceRecord` attempted to prove chunk poisoning using only the publisher-signed manifest, the received corrupted chunk, a Merkle proof, and the reporting client's signature.

### 2. Original Specification
- Client received corrupted chunk $B'$.
- Client created `FaultEvidenceRecord` containing `manifest_signature`, $B'$, and client's own signature $\sigma_D$.
- Verifier checked that $B'$ did not match the manifest root.

### 3. Why It Was Insufficient
This structure suffered from an attribution gap:
- Anyone could fabricate corrupted chunk bytes $B'$, pair them with a legitimate server-signed manifest, and claim the server sent them.
- Because the server never signed a delivery envelope committing to having served those specific bytes for that specific request, the evidence could not cryptographically attribute the delivery of $B'$ to the accused server.
- The accused server could credibly claim the client corrupted the chunk locally or received it from a third party.

### 4. Corrected Specification
- **Signed Delivery Envelope:** Flow 6 and Flow 16 now require `ChunkResponse` to include a server signature $\sigma_S$ covering:
  $$\text{"PKI\_V2\_RESP:"} \,\|\, ReqID \,\|\, C.DID \,\|\, S.DID \,\|\, ContentID \,\|\, k \,\|\, H(B') \,\|\, R \,\|\, t_{resp} \,\|\, \nu_{req}$$
- **Seven-Step Verifier Deduction:** A `FaultEvidenceRecord` must bundle:
  1. The server-signed `ContentManifest` committing to root $R$.
  2. The server-signed `ChunkResponse` delivery envelope committing to $H(B')$ for chunk index $k$ under root $R$.
  3. The raw delivered chunk $B'$.
  4. The verifier verifies $\text{SHA-256}(B') == H(B')$.
  5. The verifier proves that $H(B')$ mathematically contradicts root $R$ at index $k$.
  6. The verifier confirms all signatures under the server's public key.
  7. **Deduction:** The server's own private key cryptographically committed to delivering a chunk hash that contradicts its own signed manifest root.

### 5. Security Property Obtained
- **Cryptographic Attribution of Inconsistent Delivery:** Proves non-repudiably that the server emitted a delivery commitment conflicting with its published manifest root for a specific request.

### 6. Security Property NOT Obtained
- **Proof of Malicious Intent:** Does not prove subjective malicious intent. Cryptography cannot distinguish between intentional poisoning, a storage drive bit-flip, a proxy caching bug, or a software indexing error.

### 7. Implementation Consequence
- Serving nodes must sign every `ChunkResponse` envelope over the full parameter tuple.
- The simulator and fault validation pipeline must verify both the manifest envelope and the delivery envelope before admitting a fault record into the journal or triggering a revocation proposal.

---

## Correction 2: Request/Response Cryptographic Binding

### 1. Issue
Delivery responses (`CHUNK_RESP`) lacked strict end-to-end cryptographic binding to the initiating request, creating vulnerability to cross-request transplant and replay.

### 2. Original Specification
- `CHUNK_RESP` signature covered only: `ReqID || k || SHA-256(B_k)`.
- Client DID, server DID, content ID, root hash, and request nonce were omitted from the server's signed response payload.

### 3. Why It Was Insufficient
- An attacker could intercept a signed chunk response for one file/request and present it as a response to a completely different request or client.
- Without binding client DID and content root, an adversary could transplant signed chunk deliveries across sessions or substitute chunk indices without invalidating the envelope signature.

### 4. Corrected Specification
- Flow 5 defines `ContentRequest` signed by the client:
  $$\sigma_C \leftarrow \text{Ed25519.Sign}(sk_C, \text{"PKI\_V2\_REQ:"} \,\|\, ReqID \,\|\, C.DID \,\|\, S.DID \,\|\, ContentID \,\|\, k \,\|\, R \,\|\, t_{req} \,\|\, \nu_{req})$$
- Flow 6 defines `ChunkResponse` signed by the server:
  $$\sigma_S \leftarrow \text{Ed25519.Sign}(sk_S, \text{"PKI\_V2\_RESP:"} \,\|\, ReqID \,\|\, C.DID \,\|\, S.DID \,\|\, ContentID \,\|\, k \,\|\, H(B_k) \,\|\, R \,\|\, t_{resp} \,\|\, \nu_{req})$$
- The server's signature strictly binds all 9 parameters together.

### 5. Security Property Obtained
- **Session & Request Uniqueness:** Responses cannot be transplanted across requests, clients, content items, or sessions.

### 6. Security Property NOT Obtained
- **Physical Network Delivery Verification:** Proves that the server created a signed commitment for the client; does not prove IP packet routing or network-level throughput.

### 7. Implementation Consequence
- `ChunkResponse` dataclass in Layer 3 must include `client_did`, `server_did`, `content_id`, `merkle_root`, and `nonce`.
- Verification routines must assert exact matching of all fields against pending request records.

---

## Correction 3: Negative Receipts vs. Cryptographic Fault Semantics

### 1. Issue
The original specification permitted bilateral receipts with rating $-1.0$ without defining what a co-signed negative receipt represents or how it differs from objective fault evidence.

### 2. Original Specification
- `BilateralReceipt` had a `rating` field accepting $+1.0$ or $-1.0$.
- Any negative rating deducted from $S_{C, S}$ and was ambiguous with regard to triggering eviction.

### 3. Why It Was Insufficient
- In a bilateral receipt, **both parties co-sign**. A server has no incentive to sign an admission of malicious poisoning.
- Conflating a mutual contractual dispute (e.g., cancelled order, timeout) with cryptographically proven poisoning creates severe confusion in reputation accounting. Treating a $-1.0$ receipt as evidence for revocation would allow colluding parties to trigger supernode evictions improperly.

### 4. Corrected Specification
The protocol establishes three strictly separated evidence tiers:
1. **Tier 1: Successful Bilateral Receipt (`BilateralReceipt`, rating $+1.0$):**
   - Co-signed by Client and Server.
   - Matrix update: $S_{C, S} \leftarrow S_{C, S} + 1.0$.
   - Semantics: Certified successful delivery. Peer remains `ACTIVE`.
2. **Tier 2: Bilateral Dispute Receipt (`BilateralReceipt`, rating $-1.0$):**
   - Co-signed by Client and Server.
   - Matrix update: $S_{C, S} \leftarrow S_{C, S} - 1.0$.
   - Semantics: Mutually acknowledged failed transaction or cancellation. It is a behavioral dispute signal, **NOT** cryptographic proof of fraud. It does **NOT** trigger supernode revocation proposals.
3. **Tier 3: Certified Fault Evidence (`FaultEvidenceRecord`):**
   - Unilateral report backed by server's own signed manifest and delivery envelope (Tier 3 does not require server consent).
   - Matrix update: $S_{\text{reporter}, \text{accused}} \leftarrow S_{\text{reporter}, \text{accused}} - 2.0$.
   - Semantics: Cryptographically certified inconsistent delivery. Accused transitions immediately to `SUSPECTED` and triggers `PROPOSE_REVOCATION`.

### 5. Security Property Obtained
- **Separation of Subjective Disputes from Objective Proofs:** Distinguishes mutual commercial/contractual disputes from verifiable mathematical violations.

### 6. Security Property NOT Obtained
- **Automatic Truthfulness of Dispute Content:** A co-signed $-1.0$ receipt proves mutual agreement to log a negative rating; it does not prove which party was technically at fault.

### 7. Implementation Consequence
- The reputation engine must dispatch updates conditionally based on record type: receipts adjust satisfaction scores; only certified `FaultEvidenceRecord` objects can escalate peer state to `SUSPECTED` or trigger supernode voting.

---

## Correction 4: Canonical Global Evidence Accounting & Replay Layering

### 1. Issue
Local in-memory replay caches alone did not guarantee that a single valid receipt could not be counted multiple times across different nodes or relays.

### 2. Original Specification
- Verifiers maintained local `seen_tx_ids` and timestamp checks.
- Accounting rules lacked clear distinction between transport-level deduplication, replay prevention, and canonical reputation uniqueness.

### 3. Why It Was Insufficient
- In a decentralized swarm, multiple peers relay receipts via gossip. Without a canonical accounting rule, a node receiving the same receipt from five peers might record it five times if it treated each relay as an interaction.
- Alternatively, across simulation rounds, clearing or desynchronizing local caches could lead to double-counting.

### 4. Corrected Specification
The protocol defines a Four-Layer Evidence & Replay Pipeline:
1. **Layer A — Transport Duplicate Suppression:** Discards redundant gossip packets via rolling message hash filters.
2. **Layer B — Local Replay & Freshness Filter:** Enforces sliding window $W = 600\text{ seconds}$ and interaction nonce cache $\mathcal{N}_{\text{seen}}$.
3. **Layer C — Canonical Evidence Uniqueness:** Every transaction has an immutable, globally unique identifier ($TxID$ or $EvidenceID$). The reputation engine maintains a persistent canonical ledger $\mathcal{L}_{\text{canon}}$.
4. **Layer D — Deterministic Reputation Accounting:**
   $$\textbf{CANONICAL RULE: } \text{A record contributes at most once to matrix } S \text{ based on its unique canonical ID, regardless of relay count.}$$
   $$\text{TxID} \notin \mathcal{L}_{\text{canon}} \implies \text{Commit to } \mathcal{L}_{\text{canon}} \land S_{C, S} \mathrel{+}= \text{rating}$$

### 5. Security Property Obtained
- **At-Most-Once Reputation Accounting:** Eliminates duplicate credit inflation from message replay, gossip loops, or multi-peer relays.

### 6. Security Property NOT Obtained
- **Prevention of Fresh Collusive Nonces:** Does not prevent colluders from generating infinite continuous fresh nonces and unique transaction IDs for new dummy transactions.

### 7. Implementation Consequence
- `EigenTrustEngine` must maintain a persistent `canonical_ledger: Set[str]` tracking processed IDs.
- In `network_simulator.py`, transaction processing must check `canonical_ledger` before applying matrix increments. Direct writes to matrix `S` without an uncommitted canonical record remain strictly prohibited.

---

## Correction 5: Cryptographic Claims & Non-Properties Rigor

### 1. Issue
Previous project materials and initial specifications contained imprecise or overstated security claims (e.g., claiming PoW prevents Sybils, claiming Merkle proofs prove semantic content validity, or claiming Shamir provides authenticated recovery).

### 2. Original Specification
- General assertions of "Sybil resistance", "Byzantine fault tolerance", and "zero key exposure".

### 3. Why It Was Insufficient
- In an academic and security-critical context, conflating mechanism properties (e.g., threshold authorization vs. Byzantine consensus) undermines protocol integrity and creates false security expectations.

### 4. Corrected Specification
Both `PROTOCOL_SPEC.md` and `SECURITY_MODEL.md` now enforce an explicit **Security Properties and Non-Properties** matrix for every single primitive:

| Mechanism | Property Provided | Property NOT Provided |
| :--- | :--- | :--- |
| **Proof-of-Work (PoW)** | Computational admission cost ($2^D$ hash evaluations); throttles automated generation rate. | **Does NOT prevent** Sybil attacks; provides zero guarantee of post-admission honesty. |
| **Merkle Inclusion Proof** | Verifies chunk membership under a trusted root in $O(\log N)$ hash evaluations. | **Does NOT prove** semantic correctness, safety, or absence of malware; does not prove root authenticity by itself. |
| **Ed25519 Signatures** | Origin authenticity and non-repudiation of the signed byte string. | **Does NOT prove** truthfulness of the statements in the payload. |
| **Bilateral Receipts** | Mutual non-repudiation of an agreed transaction outcome. | **Does NOT prevent** collusive upvoting rings between colluding peers. |
| **Bilateral Dispute Receipts** | Mutual co-signed acknowledgement of a transaction failure or dispute. | **Does NOT prove** malicious behavior or fraud; cannot trigger revocation. |
| **Fault Evidence Records** | Cryptographic proof attributing inconsistent delivery to the server's private key. | **Does NOT prove** malicious intent (cannot distinguish intentional attack from bit rot or bug). |
| **EigenTrust Engine** | Global reputation propagation; mathematical damping of isolated disconnected cliques. | **Does NOT automatically detect** collusion within connected subgraphs; does not propagate negative trust; does not provide Byzantine consensus. |
| **CRR Quorum Voting** | Threshold authorization ($m$-of-$n$) by supernodes. | **Does NOT provide** Byzantine consensus (PBFT/Raft); does not provide total ordering or automated evidence discovery. |
| **Shamir Secret Sharing** | Information-theoretic threshold secrecy under $k-1$ shares; reconstruction with $k$ valid shares. | **Does NOT provide** authentication of the requester, access control, or detection of corrupted shares (non-verifiable). |
| **Canonical Accounting** | Guarantees at-most-once contribution to reputation per unique transaction/evidence ID. | **Does NOT prevent** colluders from generating new fresh nonces for additional dummy transactions. |

### 5. Security Property Obtained
- **Verifiable Truth in Advertising:** A rigorous, mathematically defensible security specification that withstands adversarial peer review.

### 6. Security Property NOT Obtained
- N/A (this is a meta-specification correction).

### 7. Implementation Consequence
- All benchmark metrics, reporting scripts, and presentation slides must be calibrated to these explicit boundaries.

---

## Summary of File Modifications

| File | Status | Nature of Modifications |
| :--- | :--- | :--- |
| [`PROTOCOL_SPEC.md`](file:///d:/pki_casestudy/PROTOCOL_SPEC.md) | **UPDATED** | Added request/response binding in Flows 5 & 6; updated Flow 13 & 16 with 7-step attribution deduction; differentiated negative receipt semantics in Flow 10, 11, 14; formalized 4-layer canonical accounting in Section 5. |
| [`SECURITY_MODEL.md`](file:///d:/pki_casestudy/SECURITY_MODEL.md) | **UPDATED** | Added Delivery Failure Taxonomy (integrity vs. attribution vs. intent); expanded Properties and Non-Properties matrix to cover all 10 mechanisms; aligned threat model. |
| [`PROTOCOL_CORRECTION_REPORT.md`](file:///d:/pki_casestudy/PROTOCOL_CORRECTION_REPORT.md) | **CREATED** | Comprehensive report detailing all 5 issues, original vs. corrected specifications, properties obtained/not obtained, and implementation consequences. |

*No source code, unit tests, benchmark scripts, or presentation assets were modified.*
