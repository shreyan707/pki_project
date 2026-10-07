# Decentralized P2P PKI & Trust Management — Security Model
**Document Version:** 2.1.0-SEC (Corrected Architecture Baseline)  
**Status:** Approved Security Architecture  
**Target Architecture:** 4-Layer Hybrid P2P Trust Mesh  
**Baseline Reference:** [AUDIT.md](file:///d:/pki_casestudy/AUDIT.md), [PROTOCOL_SPEC.md](file:///d:/pki_casestudy/PROTOCOL_SPEC.md)

---

## 1. Introduction & Security Objectives

This document establishes the formal security model, adversarial threat boundaries, cryptographic assumptions, and explicit security property guarantees for the decentralized peer-to-peer (P2P) PKI and trust management system.

The primary objective is to replace unsubstantiated security claims with mathematically defensible guarantees, defining precisely what each protocol component provides, under what conditions, and what it fundamentally cannot guarantee.

---

## 2. Threat Model & Adversary Capabilities

### 2.1 Adversary Power Classes

We model an active, computationally bounded adversary $\mathcal{A}$ with polynomial-time computational capabilities ($\text{PPT}$). The adversary can control a subset of network entities and can manipulate, delay, or inject network packets.

```
+-------------------------------------------------------------------------------+
|                        ADVERSARIAL CAPABILITY SPECTRUM                        |
+-------------------------------------------------------------------------------+
| Class 1: Sybil Generator         - Infinite key creation bounded only by PoW  |
| Class 2: Collusive Ring          - Mutual fake transaction upvoting           |
| Class 3: Content Inconsistent    - Serves chunk bytes conflicting with root   |
| Class 4: Replay Attacker         - Resubmits historical valid receipts        |
| Class 5: Dishonest Supernode     - Corrupts shares / withholds quorum votes   |
| Class 6: Whitewasher / On-Off    - Discards identity after bad behavior       |
+-------------------------------------------------------------------------------+
```

### 2.2 Attack Vectors & Adversary Profiles

1. **Sybil Identity Generation:**
   - $\mathcal{A}$ attempts to spawn thousands of virtual identities to dominate network voting or routing.
   - *Adversary Power:* Bounded by aggregate hash rate $H_{\mathcal{A}}$.
2. **Collusion & Ballot Stuffing:**
   - $\mathcal{A}$ controls a closed clique of $K$ peers who generate bilateral transactions praising each other with $+1.0$ ratings.
   - *Adversary Power:* Complete control over all identities within the collusive clique.
3. **Chunk Inconsistency & Poisoning:**
   - $\mathcal{A}$ advertises authentic files or responds to download requests with chunk bytes that do not match the published Merkle root.
   - *Adversary Power:* Arbitrary byte manipulation of served payloads.
4. **Receipt Replay Attack:**
   - $\mathcal{A}$ captures legitimate historical transaction receipts and re-submits them across multiple epochs or nodes to artificially inflate reputation.
5. **Malicious / Byzantine Supernodes:**
   - A minority of supernodes $f < m$ may defect, withhold signatures, sign false revocation records, or return corrupt secret recovery shares.
6. **Whitewashing (Identity Reset):**
   - A peer with degraded reputation discards its keypair and registers a fresh identity to reset its trust score to baseline.

### 2.3 Network Assumptions & Bound Limits

- **Network Synchrony:** Partially synchronous network. Message latency between honest peers is bounded by $\Delta t_{\max}$ under normal conditions.
- **Clock Drift:** Local peer clocks are synchronized within a maximum tolerance $\Delta t_{\text{drift}} \le 15\text{ seconds}$ via NTP or gossip clock consensus.
- **Pre-Trusted Seed Integrity:** At least one pre-trusted seed anchor in $\mathcal{P}_0$ remains honest and uncompromised.
- **Supernode Quorum Condition:** For an $m$-of-$n$ supernode committee, at least $m$ supernodes are honest and non-colluding, and no more than $f < m$ supernodes are Byzantine or compromised.

---

## 3. Cryptographic Primitives & Foundations

| Primitive | Concrete Algorithm | Security Parameter | Hardness Assumption / Standard |
| :--- | :--- | :--- | :--- |
| **Digital Signature** | Ed25519 | 128-bit security level | Discrete Logarithm over Curve25519; EUF-CMA (RFC 8032) |
| **Cryptographic Hash** | SHA-256 | 256-bit digest | Collision Resistance & Pre-image Resistance (FIPS 180-4) |
| **Proof-of-Work** | SHA-256 Partial Inversion | Difficulty $D$ bits | Random Oracle Model; Expected iterations $2^D$ |
| **Secret Sharing** | Shamir's Polynomial $(k, n)$ | Prime $P = 2^{256} - 189$ | Information-theoretic security in $\mathbb{F}_P$ |
| **Canonical Formatting**| Explicit Domain Separation | Prefixed ASCII | Domain separation prevents cross-protocol signature forgery |

---

## 4. Trust Boundaries & Separation of Concerns

The protocol strictly separates six decoupled functional layers:

```
+--------------------------+----------------------------------------------------+
| Layer Concern            | Actual Function                                    |
+--------------------------+----------------------------------------------------+
| 1. Identity              | Binds Ed25519 public key to DID                    |
| 2. Identity Admission    | Imposes computational join cost (PoW)              |
| 3. Content Integrity     | Verifies chunk bits against signed Merkle root     |
| 4. Transaction Evidence  | Dual-signed receipts & attributable fault proofs   |
| 5. Behavioral Reputation | Global propagation of receipt scores via EigenTrust|
| 6. Revocation            | m-of-n Supernode Quorum eviction of bad actors     |
+--------------------------+----------------------------------------------------+
```

### 4.1 Tripartite Distinction in Delivery Failures

To maintain scientific integrity, the security model strictly separates three concepts:

```
+-------------------------------------------------------------------------------+
|                       DELIVERY FAILURE TAXONOMY                               |
+-------------------------------------------------------------------------------+
| 1. Content Integrity Failure:                                                 |
|    A received chunk B' fails SHA-256(B') == ExpectedLeafHash.                 |
|    Observation: Raw data corruption detected.                                 |
|    Does NOT prove: Who caused it (could be transmission bit-flip or MITM).    |
+-------------------------------------------------------------------------------+
| 2. Server-Attributable Inconsistent Delivery:                                 |
|    Server signed a manifest committing to root R, AND signed a delivery       |
|    envelope committing to H(B') for chunk k under root R, where H(B')         |
|    mathematically contradicts root R.                                         |
|    Observation: Cryptographic contradiction bound to server's private key.    |
|    Does NOT prove: Malicious intent.                                          |
+-------------------------------------------------------------------------------+
| 3. Malicious Intent:                                                          |
|    The subjective cognitive decision by an operator to sabotage or poison.   |
|    Observation: Unobservable via cryptography.                                |
|    Protocol Policy: The protocol penalizes attributable bad delivery without  |
|    making unfalsifiable claims about subjective mental state.                 |
+-------------------------------------------------------------------------------+
```

---

## 5. Security Properties and Non-Properties

This section explicitly defines what each mechanism **PROVIDES** and what it **DOES NOT PROVIDE**.

### 5.1 Proof-of-Work (PoW) Admission Puzzle

- **PROPERTY PROVIDED:**
  - **Computational Admission Cost:** Imposes a deterministic lower bound on the expected CPU/hash cycles ($2^D$ evaluations) required to create a single valid `P2PCertificate`.
  - **Sybil Throttling (Rate Limiting):** Constrains the rate of identity generation per unit of adversary hash power.
- **PROPERTY NOT PROVIDED:**
  - **Sybil Prevention:** PoW **does not prevent** Sybil attacks. An adversary with sufficient computational capacity can generate arbitrarily many identities over time.
  - **Behavioral Honesty:** A valid PoW provides **zero guarantee** that the peer will behave honestly after admission.
  - **Dynamic Retargeting:** A static bit difficulty does not automatically adapt to global network hashrate fluctuations.

### 5.2 Merkle Inclusion Proof

- **PROPERTY PROVIDED:**
  - **Chunk-Level Membership:** Guarantees that a chunk $B_k$ belongs to the file committed to by trusted Merkle root $R$ in $O(\log N)$ hash operations.
  - **Auditable Proof Paths:** Allows a verifier to validate a chunk without possessing the entire leaf hash array or other chunk contents.
- **PROPERTY NOT PROVIDED:**
  - **Semantic Correctness / Safety:** A valid Merkle proof **does not prove** that the file content is safe, accurate, uncorrupted prior to hashing, or malware-free.
  - **Root Authenticity:** A Merkle proof **does not prove** the root $R$ itself is legitimate. Root trustworthiness depends entirely on publisher signature verification.

### 5.3 Digital Signatures (Ed25519)

- **PROPERTY PROVIDED:**
  - **Origin Authenticity & Integrity:** Proves that a specific byte string was signed by the holder of private key $sk$ corresponding to public key $pk$.
  - **Non-Repudiation:** The signer cannot claim they did not emit the signed statement.
- **PROPERTY NOT PROVIDED:**
  - **Truthfulness of Statement:** A digital signature **does not guarantee** that the claims within the payload are true. A malicious peer can sign false receipts, corrupted manifests, or dishonest ratings.
  - **Real-World Identity Verification:** Proves ownership of a cryptographic key, not the legal, physical, or moral identity of the operator.

### 5.4 Bilateral Transaction Receipts

- **PROPERTY PROVIDED:**
  - **Mutual Interaction Agreement:** Proves that both Client $C$ and Server $S$ agreed to a transaction outcome and rating at timestamp $t_{tx}$.
  - **Unilateral Forgery Resistance:** Neither party can unilaterally fabricate a valid positive bilateral receipt without the counterparty's private key.
- **PROPERTY NOT PROVIDED:**
  - **Collusion Resistance:** Two colluding malicious peers can freely co-sign infinite positive receipts for dummy or non-existent file transfers.
  - **Physical Delivery Verification:** Proves cryptographic consensus between two keys, not physical packet delivery across IP networks.

### 5.5 Bilateral Negative Receipts ($-1.0$ Rating)

- **PROPERTY PROVIDED:**
  - **Mutual Dispute Acknowledgement:** Proves that both parties co-signed an agreement that a transaction was cancelled, unfulfilled, or disputed.
  - **Subjective Behavioral Signal:** Provides a negative delta in the local satisfaction matrix ($S_{C, S} \leftarrow S_{C, S} - 1.0$).
- **PROPERTY NOT PROVIDED:**
  - **Proof of Malicious Behavior:** A $-1.0$ receipt **does not prove** malicious behavior, fraud, or chunk poisoning. It is a mutually acknowledged contractual dispute and does not trigger supernode revocation.

### 5.6 Server-Attributable Delivery Evidence (`FaultEvidenceRecord`)

- **PROPERTY PROVIDED:**
  - **Cryptographic Attribution of Inconsistency:** Mathematically proves that the server's private key signed a delivery commitment for request $ReqID$ containing a chunk hash that contradicts the root published in the server's signed manifest.
  - **Admissible Revocation Evidence:** Provides objective, verifiable justification for supernode quorum evaluation and CRR generation.
- **PROPERTY NOT PROVIDED:**
  - **Proof of Malicious Intent:** Cryptography **cannot distinguish** between intentional poisoning, a storage drive bit-flip, a faulty caching proxy, or a software index bug.

### 5.7 Canonical Evidence Accounting & Replay Protection

- **PROPERTY PROVIDED:**
  - **At-Most-Once Reputation Contribution:** Guarantees that any transaction or evidence item contributes to the satisfaction matrix at most once based on its globally unique canonical identifier ($TxID$ or $EvidenceID$), regardless of relay count.
  - **Freshness Bounding:** Rejects historical receipts generated outside sliding window $W = 600\text{ seconds}$.
- **PROPERTY NOT PROVIDED:**
  - **Fresh Collusion Nonce Prevention:** Does not prevent colluders from generating continuous fresh nonces and unique transaction IDs for new dummy transactions.

### 5.8 EigenTrust Algorithm

- **PROPERTY PROVIDED:**
  - **Reputation Propagation:** Computes the stationary distribution of peer trustworthiness using transitive trust paths anchored in pre-trusted seeds $\mathcal{P}$.
  - **Isolated Clique Damping:** Mathematically attenuates the global trust of completely disconnected collusive rings to zero, provided they have zero incoming trust from honest paths.
- **PROPERTY NOT PROVIDED:**
  - **Automatic Connected Collusion Detection:** If malicious peers interact with honest nodes and receive legitimate incoming trust edges, EigenTrust **does not automatically separate** collusive upvotes from authentic ratings.
  - **Negative Trust Propagation:** Vanilla EigenTrust clips negative ratings to zero during row normalization; it does not propagate distrust transitively.
  - **Byzantine Convergence:** If a pre-trusted seed defects or is compromised, EigenTrust trust scores will be distorted.

### 5.9 CRR Quorum Revocation ($m$-of-$n$)

- **PROPERTY PROVIDED:**
  - **Threshold Authorization:** Requires at least $m$ distinct, authorized supernode signatures to certify a `CertificateRevocationRecord`.
  - **Minority Compromise Resistance:** Up to $m-1$ compromised supernodes cannot unilaterally revoke an honest peer.
- **PROPERTY NOT PROVIDED:**
  - **Byzantine Consensus:** Simple $m$-of-$n$ signature collection is **not a Byzantine agreement protocol** (e.g., PBFT or Raft). It does not guarantee total ordering, atomicity, or liveness under adversarial network partitions.
  - **Automated Evidence Discovery:** The quorum authorizes the revocation; it cannot magically detect attacks without certified input evidence.

### 5.10 Shamir Secret Sharing ($(k, n)$ Threshold)

- **PROPERTY PROVIDED:**
  - **Information-Theoretic Secrecy:** Any coalition of fewer than $k$ share holders learns strictly zero information about the secret $S$.
  - **Threshold Reconstruction:** Any authorized subset of $k$ valid shares can reconstruct the exact secret $S$ via Lagrange interpolation.
- **PROPERTY NOT PROVIDED:**
  - **Authenticated Access Control:** Shamir's scheme **has no built-in authentication**. Any adversary who obtains $k$ shares can reconstruct the secret regardless of identity ownership.
  - **Verifiable Shares (VSS):** Vanilla Shamir **cannot detect** a malicious custodian who supplies a corrupted share $(x_i, y'_i)$. Corrupted shares result in a silent, incorrect reconstructed secret.
  - **Key Protection After Recovery:** Reconstruction exposes the secret in plaintext memory; Shamir provides no forward secrecy without immediate post-recovery key rotation.

---

## 6. Peer Lifecycle State Machine & Transition Rules

```
                      +-------------------+
                      |      UNKNOWN      |
                      +-------------------+
                                |
                                | [T1] REGISTER_REQ (PoW + Self-Sig Valid)
                                v
     +------------------->+---------------+
     |                    |    ACTIVE     |
     |                    +---------------+
     |                            |
     | [T3] Evidence Disproven    | [T2] Attributable Inconsistency Certified
     |      or Timeout Expired    v
     |                    +---------------+
     +--------------------|   SUSPECTED   |
                          +---------------+
                                  |
                                  | [T4] Quorum Threshold Sponsor
                                  v
                      +-----------------------+
                      |  REVOCATION_PROPOSED  |
                      +-----------------------+
                                  |
                                  | [T5] m-of-n Supernode Quorum (CRR Signed)
                                  v
                          +---------------+
                          |    REVOKED    |  (Terminal State / Eviction)
                          +---------------+
```

### Transition Specifications

| Transition | From State | To State | Trigger Condition | Validating Entity |
| :--- | :--- | :--- | :--- | :--- |
| **T1: Admission** | `UNKNOWN` | `ACTIVE` | Valid PoW ($D \ge D_{\min}$) + valid self-signature + fresh timestamp | Admission Verifier |
| **T2: Detection** | `ACTIVE` | `SUSPECTED` | Attributable inconsistent delivery certified via signed manifest + signed delivery envelope | Downloading Peer |
| **T3: Exoneration** | `SUSPECTED` | `ACTIVE` | Suspicion timer $T_{\text{susp}}$ expires without corroboration, or proof rebutted | Local Peer Engine |
| **T4: Escalation** | `SUSPECTED` | `REVOCATION_PROPOSED` | Formal `PROPOSE_REVOCATION` message accompanied by certified `FaultEvidenceRecord` | Supernode Committee |
| **T5: Revocation** | `REVOCATION_PROPOSED` | `REVOKED` | $\ge m$ valid supernode signatures assembled on CRR payload | Network / All Peers |

---

## 7. Residual Risks, Boundaries & Future Hardening

1. **Sybil Resistance Limitations:**
   - PoW raises the marginal cost of identity generation, but does not prevent an adversary with large compute resources from gradually amassing identities.
2. **Whitewashing Residual Vector:**
   - An attacker who discards an identity with low trust only incurs the computational cost of solving a fresh PoW puzzle ($2^D$ hashes). Quarantine and slow trust accrual are required to limit whitewashing utility.
3. **Collusion within Connected Subgraphs:**
   - Vanilla EigenTrust dampens disconnected cliques. However, if colluding nodes successfully conduct authentic transactions with honest nodes, their collusive upvotes will leak into the global trust vector. Advanced spectral clustering or anomaly detection is required for deeper defense.
4. **Verifiable Secret Sharing (VSS):**
   - The current Shamir recovery relies on honest custodians. Future upgrades should incorporate Feldman's Verifiable Secret Sharing (VSS) or Pedersen commitments to enable the requester to detect and identify rogue custodians who return corrupted shares.
