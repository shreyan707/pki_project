# PKI-Based Trust Management for Peer-to-Peer File-Sharing and Social Networking Platforms

**Author:** Shreyan Nayak (Registration No. 23BKT0039)  
**Affiliation:** School of Computer Science and Engineering (SCOPE), Vellore Institute of Technology (VIT), Chennai, Tamil Nadu, India  
**Course Code / Assessment:** VL2026270102689 — Case Study Assessment CS1  
**Project Freeze Baseline:** v9.0-FINAL-FREEZE  
**Date:** October 9, 2026  

---

### Abstract
Decentralized peer-to-peer (P2P) systems operating in the absence of centralized Certificate Authorities (CAs) face fundamental vulnerabilities to identity spoofing, Sybil multiplication, free-riding, strategic collusion, and malicious content distribution. While classical Public Key Infrastructure (PKI) enforces strict cryptographic identity bindings, its conventional hierarchical trust model introduces single points of failure and censorship vulnerabilities. Conversely, classical distributed reputation algorithms like EigenTrust compute global spectral trust vectors but assume unauthenticated feedback, leaving them exposed to feedback forgery, receipt grinding, and identity whitewashing. This paper presents a vertically integrated four-layer decentralized PKI trust management architecture designed for P2P file sharing and architecturally mapped to decentralized social networking. The system integrates: (1) self-certifying `did:peer`-style cryptographic identities with verifiable Hashcash proof-of-work (PoW) admission barriers; (2) a dynamic Web-of-Trust mesh PKI utilizing bounded vertex-disjoint path discovery up to four hops; (3) Evidence-Weighted EigenTrust (EW-EigenTrust v1.8), featuring three-tier cryptographic delivery verification, concave edge ceilings, exponential freshness decay, and dispute accounting; and (4) an $m$-of-$n$ supernode threshold certificate revocation mechanism ($3$-of-$5$) combined with Shamir $(3, 5)$ secret-shared master identity recovery. The reference implementation was evaluated across 1,140 paired benchmark trials spanning 20 random seeds and two network scales. Empirical findings reveal that while asymmetric evidence discounting suppresses colluder trust by $40.88\%$ to $41.50\%$ ($p < 10^{-18}$) in leaky topologies where colluders interact with honest peers, internal edge ceilings fail to suppress closed colluding coalitions. Aggregate closed-coalition trust is dictated by external incoming flow in accordance with the derived Closed-Set Flow Identity ($T_C = \frac{1-\alpha}{\alpha} F_{H \to C}$), formally refuting preregistered Hypothesis H-1 under receipt grinding. Furthermore, Merkle-based fault contradiction proofs enable efficient $O(\log N)$ arbiter verification of corrupted chunk deliveries without transferring full file payloads. We establish the evidentiary boundaries between empirical file-sharing validation, simulator oracle dependencies, and conceptual social-networking extensions.

### Index Terms
Decentralized Public Key Infrastructure, Web-of-Trust, EigenTrust, Peer-to-Peer File Sharing, Proof-of-Work, Threshold Cryptography, Merkle Inclusion Proofs, Collusion Resistance, Social Networking.

---

## I. Introduction

Decentralized peer-to-peer (P2P) file-sharing networks (e.g., BitTorrent, IPFS) and distributed social networking platforms (e.g., Nostr, Matrix, Mastodon) operate without central intermediaries. While eliminating centralized gatekeepers confers resilience against single points of failure, structural bottlenecking, and administrative censorship, it simultaneously deprives participants of authoritative identity verification and accountability. In open distributed networks, peers encounter unauthenticated participants under severe information asymmetry, exposing systems to identity spoofing, Sybil attacks, free-riding, malicious data poisoning, and strategic reputation inflation [1], [3].

In classical client-server and enterprise environments, Public Key Infrastructure (PKI) resolves identity authenticity through hierarchical Certificate Authorities (CAs). A relying party verifies arbitrary certificates by validating signature chains rooted in a trusted anchor. In decentralized networks, however, reliance on centralized CAs reintroduces single points of failure, single points of legal compromise, and administrative chokepoints that contradict decentralized fault tolerance. Conversely, distributed reputation management protocols—most notably the seminal EigenTrust algorithm [3]—aggregate local satisfaction ratings into global trust distributions via spectral power iteration. However, classical EigenTrust assumes honest rating submission and authentic transaction accounting. Without an underlying cryptographic identity layer, malicious peers can mass-produce zero-cost pseudonyms (Sybil attacks), fabricate unauthenticated transaction feedback, and execute receipt grinding to dominate spectral trust distributions [1], [3].

To resolve this architectural tension, this paper presents a unified, vertically integrated four-layer decentralized PKI trust framework. The primary research question investigated is: *How can cryptographic identity assurance and distributed reputation management be synthesized into a decentralized architecture that bounds Sybil creation, authenticates transactions, suppresses collusion, and manages certificate lifecycles without centralized authorities?*

This paper presents the formal specification, mathematical derivation, software implementation, and empirical benchmark evaluation of this architecture, establishing the following contributions:
1. **Four-Layer Synthesized Architecture:** An end-to-end decentralized trust model bridging cryptographic identity generation (Layer 1), Web-of-Trust mesh certification (Layer 2), evidence-weighted reputation propagation (Layer 3), and threshold certificate revocation with secret-shared recovery (Layer 4).
2. **Attributable Fault Contradiction Proofs:** A cryptographic contradiction protocol utilizing authentic publisher manifests, server-signed delivery envelopes, and binary Merkle inclusion proofs that enables third-party arbiters to verify corrupted chunk delivery in $O(\log N)$ hash operations without downloading full $O(N)$ file payloads [4].
3. **Rigorous Empirical Characterization of EW-EigenTrust v1.8:** A paired-seed benchmark evaluation across 1,140 trial evaluations demonstrating that while evidence weighting slashes leaky collusion by $>40\%$ ($p < 10^{-18}$), internal concave edge ceilings cannot suppress closed coalitions under fixed incoming bridge flow.
4. **Transparent Negative Results Reporting:** Formal mathematical derivation of the Closed-Set Flow Identity ($T_C = \frac{1-\alpha}{\alpha} F_{H \to C}$) explaining why closed coalitions remain invariant to internal discounting, and documentation of the empirical refutation of preregistered Hypothesis H-1 under receipt grinding.
5. **Rigorous Scope and Evidentiary Boundaries:** Explicit demarcation between empirically evaluated P2P file sharing, simulator delivery oracle bounds, and conceptual social-networking extensions.

---

## II. Background and Related Work

### A. Decentralized Identity and Sybil Resistance
Self-certifying cryptographic identifiers derive an entity's network address directly from its public key, eliminating central registries. The Decentralized Identity Foundation (DIF) and W3C have standardized Decentralized Identifiers (DIDs) [2], [6]. In permissionless networks, however, public keys can be generated at negligible computational cost, enabling Sybil attacks wherein an adversary creates vast clusters of fake identities to compromise voting or reputation pools. To impose an economic admission barrier, Hashcash proof-of-work (PoW) [1] mandates that peers compute a cryptographic preimage whose hash satisfies a difficulty target $d$:
$$H(DID \parallel \text{nonce}) < 2^{256-d}$$
Verifying this proof is $O(1)$ (a single SHA-256 block compression), while generating it requires an expected $O(2^d)$ hash evaluations, eliminating zero-cost identity generation.

### B. Web-of-Trust and Mesh PKI
Pioneered by Zimmermann in PGP [7], the Web-of-Trust (WoT) replaces hierarchical roots with peer-to-peer cross-certification. Peer $A$ signs a statement attesting to the binding between peer $B$'s public key and identity alias. In mesh topologies, verifying trust between strangers requires discovering multi-hop certificate chains. However, unconstrained transitive chaining permits distant, untrusted intermediaries to introduce malicious certifications. Maurer and Reiter established that transitive trust propagation requires bounded path lengths and disjoint paths to resist adversarial bridge insertion.

### C. Spectral Reputation and EigenTrust
The EigenTrust algorithm developed by Kamvar, Schlosser, and Garcia-Molina [3] computes global trust by modeling peer interactions as a discrete-time Markov chain. Given local normalized satisfaction matrix $\mathbf{C}$ where $c_{ij} = \max(s_{ij}, 0) / \sum_k \max(s_{ik}, 0)$, global trust vector $\mathbf{t} \in \mathbb{R}^n$ ($\sum t_i = 1$) satisfies stationary power iteration:
$$\mathbf{t} = (1 - \alpha) \mathbf{C}^T \mathbf{t} + \alpha \mathbf{p}$$
where $\alpha \in (0, 1)$ is a restart probability and $\mathbf{p}$ is a pre-trusted peer distribution ($p_s = 1/|S|$ for pre-trusted seeds $S$). While EigenTrust dampens isolated malicious nodes, strategic colluders who exchange high-volume positive ratings among themselves while obtaining external bridge edges can extract substantial global trust share.

### D. Cryptographic Fault Attribution and Merkle Trees
In content distribution, validating data authenticity without full file re-downloads relies on Merkle hash trees [4]. A file of $N$ chunks is committed to a single 32-byte root hash. Downloaders verify chunk $k$ by recomputing the root hash along a path of $\lceil \log_2 N \rceil$ sibling digests. Attributing delivery fraud requires binding the delivered chunk to a server-signed envelope that contradicts the published root.

### E. Threshold Key Recovery and Revocation
In CA-based PKI, revocation relies on centralized Certificate Revocation Lists (CRLs) or Online Certificate Status Protocol (OCSP) responders. In decentralized networks, revoking compromised keys requires distributed threshold signatures. Shamir's $(k, n)$ secret sharing [5] over $GF(256)$ enables a private seed to be split into $n$ shares such that any $k$ shares reconstruct the secret, enabling social or guardian-based identity recovery without a central custodian.

---

## III. Problem Formulation and Threat Model

### A. System Model
The network consists of a dynamic set of peers $V = H \cup C$, partitioned into honest peers $H$ (including pre-trusted supernodes $S \subset H$) and adversarial peers $C$, such that $H \cap C = \emptyset$. Peers communicate over an asynchronous P2P overlay network. Content is partitioned into fixed-size chunks addressed by binary Merkle trees.

### B. Adversarial Threat Model
We consider an active, computationally bounded adversary controlling coalition $C$ capable of coordinating malicious strategies:
1. **Sybil Attacks:** The adversary attempts to generate arbitrarily large numbers of identities to manipulate voting quorums and reputation aggregation.
2. **Strategic Collusion Rings:** Colluders execute mutual synthetic transactions and award each other maximum positive ratings without delivering genuine file chunks.
3. **Receipt Grinding:** Colluders generate massive volumes of self-signed bilateral receipts to inflate incoming edge weights into their cluster.
4. **Data Poisoning and Slander:** Malicious uploaders serve corrupted chunks to honest downloaders; malicious downloaders submit fabricated complaints against honest seeders.
5. **Key Compromise and Eclipse Attacks:** Attackers compromise peer signing keys or isolate honest peers by manipulating multi-hop routing paths.

### C. Security Objectives
- **Sybil Cost Imposition:** Enforce a non-zero computational cost $O(2^d)$ for identity registration.
- **Attributable Poisoning Non-Repudiation:** Guarantee that serving corrupted data produces an irrefutable cryptographic proof verifying in $O(\log N)$ hash operations.
- **Leaky Collusion Suppression:** Suppress global trust allocated to colluders who interact with honest downloaders by $\ge 30\%$.
- **Asymmetric Provider Preservation:** Ensure dedicated seeders serving high volumes of authentic data retain high global trust without requiring reciprocal downloads.
- **Threshold Revocation Safety:** Prevent unilateral or unauthorized peer eviction, requiring $m$-of-$n$ supernode authorization ($3$-of-$5$).

---

## IV. Proposed Four-Layer Architecture

The proposed decentralized PKI trust framework operates across four vertically integrated layers, depicted in Fig. 1.

```
+-----------------------------------------------------------------------------+
| LAYER 4: THRESHOLD REVOCATION & KEY RECOVERY                                |
| Fault Evidence -> Revocation Proposal -> 3-of-5 Quorum CRR -> Mesh Eviction|
| Shamir (3, 5) Secret Sharing -> Guardian AuthTok -> Seed Reconstruction     |
+-----------------------------------------------------------------------------+
                                      ^
                                      | Attributable Evidence / Revocation
+-----------------------------------------------------------------------------+
| LAYER 3: EVIDENCE-WEIGHTED EIGENTRUST (EW-EIGENTRUST v1.8)                  |
| Bilateral Receipts -> 3-Tier Weighting (gamma_ev) -> Dispute Ratio          |
| Concave Edge Saturation Phi_edge -> Power Iteration t = (1-a)C'^T t + a p   |
+-----------------------------------------------------------------------------+
                                      ^
                                      | Validated Interaction Matrix
+-----------------------------------------------------------------------------+
| LAYER 2: MESH WEB-OF-TRUST PKI                                              |
| Ed25519 Cross-Certificates -> Mesh Topology -> DFS Vertex-Disjoint Paths    |
| Hop Bounding (k <= 4) -> Multiplicative Path Trust -> Supernode Backbone    |
+-----------------------------------------------------------------------------+
                                      ^
                                      | Authenticated Cryptographic Identities
+-----------------------------------------------------------------------------+
| LAYER 1: CRYPTOGRAPHIC IDENTITY & ADMISSION BARRIER                         |
| Ed25519 Keypair -> did:peer Syntax -> SHA-256 Hashcash PoW (d >= 8)        |
| Strict 5-State Peer Lifecycle: UNKNOWN -> ACTIVE <-> SUSPECTED -> REVOKED   |
+-----------------------------------------------------------------------------+
Fig. 1. Consolidated Four-Layer Decentralized PKI Trust Architecture.
```

### A. Layer 1: Identity Admission and Lifecycle State Machine
1. **Identifier Derivation:** Each peer generates an Ed25519 signing keypair $(sk_i, pk_i)$. In our simulation reference implementation (`src/layer1_identity.py`), the peer identifier is formatted as `did:peer:2.Ez{public_key_hex}` using the 64-character lowercase hex encoding of $pk_i$.
   *(Standards Note: As documented in our scope audit, this string syntax is a simulation-specific format and does not strictly conform to official DIF did:peer Method 2 multicodec/multibase specifications [2]).*
2. **Hashcash Admission Barrier:** To prevent zero-cost Sybil instantiation, the peer computes a nonce satisfying $H(DID_i \parallel \text{nonce}) < 2^{256-d}$ for difficulty $d \ge 8$. Verifying the admission token requires a single $O(1)$ SHA-256 computation.
3. **Five-State Peer Lifecycle:** The node lifecycle follows a strict finite state machine:
   $$\text{UNKNOWN} \xrightarrow{\text{T1}} \text{ACTIVE} \underset{\text{T3a}}{\overset{\text{T2}}{\longleftrightarrow}} \text{SUSPECTED} \xrightarrow{\text{T4}} \text{REVOCATION\_PROPOSED} \xrightarrow{\text{T5a}} \text{REVOKED}$$
   - **T1 (Admission):** `UNKNOWN` $\to$ `ACTIVE` upon PoW verification and valid self-signature.
   - **T2 (Suspicion):** `ACTIVE` $\to$ `SUSPECTED` upon attributable fault evidence or unverified suspicion.
   - **T3a (Subjective Exoneration):** `SUSPECTED` $\to$ `ACTIVE` upon timeout $T_{\text{susp}}$ for uncertified suspicion. Certified fault suspicion (T3b) persists indefinitely.
   - **T4 (Escalation):** `SUSPECTED` $\to$ `REVOCATION_PROPOSED` upon formal supernode committee proposal.
   - **T5a (Quorum Eviction):** `REVOCATION_PROPOSED` $\to$ `REVOKED` upon assembling $m$-of-$n$ supernode signatures on a Certificate Revocation Record (CRR).
   - **T5b (Timeout Fallback):** If voting window $T_{\text{vote}}$ expires without quorum ($k < m$), the state **reverts to `SUSPECTED`, never directly to `ACTIVE`**.

### B. Layer 2: Mesh Web-of-Trust PKI
1. **Cross-Certification:** Peers issue signed `CrossCertificate` records asserting unidirectional trust with valid time windows $[t_{\text{valid}}, t_{\text{expires}}]$. Signed payload format:
   $$\text{PKI\_V2\_CROSSCERT}:\langle\text{issuer\_did}\rangle:\langle\text{subject\_did}\rangle:\langle\text{trust\_weight}\rangle:\langle\text{issued\_at}\rangle:\langle\text{expires\_at}\rangle$$
2. **Bounded Path Discovery:** Paths are discovered using depth-first search (DFS) with a strict hop cutoff $k \le 4$. To prevent bridge recycling, candidate paths are filtered to enforce **intermediate-vertex disjointness** (no intermediate peer appears in more than one evaluated path). Cumulative path trust is the multiplicative product:
   $$\text{trust}(P) = \prod_{c \in P} \text{trust\_weight}(c)$$
3. **Pre-Trusted Backbone:** Bootstrapped via 5 static supernodes ($S \subset V$) with static restart distribution $\mathbf{p}$ ($p_s = 1/|S|$ for $s \in S$, $p_i = 0$ otherwise).

### C. Layer 3: Evidence-Weighted EigenTrust v1.8
Layer 3 replaces raw linear rating accumulation with four evidence-discounting mechanisms:
1. **Three-Tier Evidence Weighting ($\gamma_{\text{ev}}$):**
   - **Tier 1 (Unindexed Bilateral Receipts):** Missing or unindexed delivery references receive severe discounting ($\mu_{\text{unverified}} = 0.10$).
   - **Tier 2 (Manifest-Referenced Receipts):** Receipts referencing a known indexed Content Manifest root receive moderate discounting ($\mu_{\text{referenced}} = 0.25$).
   - **Tier 3 (Local Cryptographically Verified Deliveries):** Receipts matching local client chunk delivery verification receive full credit ($\gamma_{\text{ev}} = 1.00$).
2. **Freshness Decay ($\gamma_{\text{time}}$):** Exponential timestamp decay $\gamma_{\text{time}} = \exp(-\Delta t / \tau)$, where $\tau = 86,400\text{ s}$ (24 hours).
3. **Dispute Accounting ($\gamma_{\text{dispute}}$):** Subjective negative receipts (`rating < 0.0`) scale positive edge strength via the exact bounded ratio:
   $$\gamma_{\text{dispute}}(N_{\text{pos}}, N_{\text{neg}}) = \max\left(0.0, 1.0 - \frac{2 \cdot N_{\text{neg}}}{N_{\text{pos}} + 1.0}\right)$$
4. **Concave Edge Saturation Ceiling ($\Phi_{\text{edge}}$):** Bounded hyperbolic tangent function capping total accumulated evidence per directed edge:
   $$\Phi_{\text{edge}}(E_{\text{pos}}) = K_{\max} \cdot \tanh\left(\frac{\lambda_{\text{sat}} \cdot E_{\text{pos}}}{K_{\max}}\right), \quad K_{\max} = 10.0, \, \lambda_{\text{sat}} = 0.50$$
5. **Certified Fault Nullification:** Attributable `FaultEvidenceRecord` zeroes incoming edges to the accused peer:
   $$\forall i \in V: A_{i, \text{accused}} = 0.0$$
6. **Dangling-Node Fallback Rule:** If a peer has zero positive outgoing edge weight ($\sum_j A_{ij} = 0$), the transition row falls back to the **pre-trusted restart vector $\mathbf{p}$** ($C'_{i, :} = \mathbf{p}$).

### D. Layer 4: Threshold Revocation and Secret-Shared Recovery
1. **Quorum Eviction:** Revoking malicious peers requires assembling $m$-of-$n$ valid supernode signatures on a CRR ($m = 3, n = 5$). Valid CRRs trigger network-wide peer eviction and link severance. This mechanism enforces administrative multi-party authorization; it does not constitute Byzantine fault-tolerant consensus.
2. **Shamir Secret-Shared Recovery:** Peer identity seeds are protected via Shamir $(3, 5)$ secret sharing over $GF(256)$. Reconstructing a compromised key requires 3 authenticated guardian Recovery Authorization Tokens (`AuthTok`). Mandatory post-recovery key rotation invalidates the compromised key and establishes a dual-signed rotation link.

---

## V. Protocol Workflow and Fault Attribution

### A. Content Transfer Workflow
1. **Manifest Publication:** The content provider constructs a binary Merkle tree over file chunks $\{c_0, c_1, \dots, c_{N-1}\}$ and signs a `ContentManifest` containing `root_hash`, `chunk_count`, and file metadata.
2. **Chunk Request & Delivery Envelope:** Downloader $D$ sends a signed `ContentRequest` for chunk index $k$. Uploader $U$ serves chunk bytes $c_k$ packaged in a signed `ChunkResponse` containing $(k, H(c_k), \text{Sig}_U(H(c_k) \parallel k))$.
3. **Local Merkle Verification:** Downloader $D$ validates chunk integrity by computing the inclusion path against the authentic manifest root in $O(\log N)$ hash operations.
4. **Bilateral Receipt Exchange:** Upon successful verification, $D$ and $U$ exchange a co-signed `BilateralReceipt` containing `tx_id`, `chunk_index`, `merkle_root`, and transaction timestamp.

### B. Attributable Fault Contradiction Protocol
If uploader $U$ delivers corrupted chunk $c'_k \ne c_k$:
1. $D$ verifies that $H(c'_k)$ does not match the manifest root.
2. $D$ constructs a `FaultEvidenceRecord` containing:
   - The publisher-signed `ContentManifest` committing to authentic root $R$.
   - The server-signed `ChunkResponse` proving that $U$ delivered chunk digest $h' = H(c'_k)$ for index $k$.
   - The valid Merkle inclusion proof establishing that authentic chunk digest $h \ne h'$ belongs to root $R$ at index $k$.
3. **Arbiter Verification Complexity:** Any third-party arbiter verifies this contradiction in **$O(\log N)$ hash evaluations and sibling hashes** by verifying the server's Ed25519 signature on $h'$ and computing the Merkle inclusion path from $h$ to $R$. This avoids downloading the full $O(N)$ file payload.
4. **Attributable Semantics:** The arbiter cryptographically proves that $U$ delivered data conflicting with the committed manifest. As established in our audit, this proves attributable inconsistency; it does not prove subjective malicious intent (e.g., distinguishing hardware bit rot from deliberate tampering).

---

## VI. Experimental Methodology

The empirical evaluation was conducted under a sealed preregistration (`PHASE8_2_PREREGISTRATION.md`) to prevent post-hoc parameter tuning.

### A. Execution Matrix and Parameters
- **Paired Seeds:** 20 random seeds $\mathcal{S} = \{42 + 17 \cdot i \mid i \in [0, 19]\}$.
- **Network Scales:**
  - *Standard Scale:* 30 nodes (20 honest, 5 supernodes, 5 colluders/adversaries).
  - *Extended Scale:* 50 nodes (35 honest, 5 supernodes, 10 colluders/adversaries).
- **Trust Computation Modes:**
  1. *Vanilla EigenTrust (`MODE_VANILLA`):* Classical linear satisfaction accumulation.
  2. *Evidence-Weighted EigenTrust v1.8 (`MODE_EVIDENCE_ONLY`):* 3-tier weighting, concave edge ceilings, dispute discounting, and fault nullification.
  3. *Local-Only Baseline (`MODE_LOCAL_ONLY`):* Naive local rating summation without spectral propagation.
- **Total Evaluations:** 9 scenarios evaluated across 20 seeds, 2 scales, and 3 modes, totaling 1,140 individual trial runs.

### B. Evaluated Attack Scenarios
- **S1 (Honest Baseline):** Zero adversaries; validates distribution conservation ($\sum t_i = 1.0$).
- **S2 (Closed Collusion):** 5 colluders exchange mutual ratings; zero outgoing ratings to honest peers; 1 honest seeder bridges into coalition.
- **S3 (Leaky Collusion):** Colluders actively transact with and rate honest peers with leak probability $p_{\text{leak}} = 0.20$.
- **S4 (Connected Collusion Sweep):** Bridge connectivity probability swept across $q \in \{0.00, 0.05, 0.10, 0.20, 0.40\}$.
- **S5 (Adaptive Attacker):** Dynamic switching between honest seeding and chunk poisoning.
- **S6 (Receipt Grinding, H-1 Target):** Colluders generate up to 152,000 synthetic bilateral receipts to inflate incoming edge weight.
- **S7 (Dispute Manipulation):** Colluders file fabricated dispute complaints against honest seeders.
- **S8 (Asymmetric Uploader, H-2 Target):** Dedicated seeder serves authentic chunks without reciprocal downloading.
- **S9 (Reciprocal Community, H-4 Target):** Dense mutual sharing among honest peers.

---

## VII. Results and Statistical Analysis

Table I presents the master empirical comparison between Vanilla EigenTrust and EW-EigenTrust v1.8 across all evaluated configurations.

```
TABLE I
MASTER EMPIRICAL RESULTS SUMMARY (20 PAIRED SEEDS PER CONFIGURATION)
========================================================================================================================
Scenario & Metric               Scale    Vanilla    EW v1.8     Diff (Delta)   Rel %     Paired t-stat   p-value    Cohen dz
------------------------------------------------------------------------------------------------------------------------
S1: Honest Baseline (T_C)       Std      0.0000     0.0000        0.0000        0.00%      Undefined    Undefined  Undefined
S1: Honest Baseline (T_C)       Ext      0.0000     0.0000        0.0000        0.00%      Undefined    Undefined  Undefined
S2: Closed Collusion (T_C)      Std      0.0850     0.0889       +0.0039       +4.53%       +1.472       0.158      +0.33
S2: Closed Collusion (T_C)      Ext      0.0539     0.0611       +0.0073      +13.50%       +3.944      8.70e-4     +0.88
S3: Leaky Collusion (T_C)       Std      0.1834     0.1084       -0.0750      -40.88%      -34.354      1.44e-18    -7.68
S3: Leaky Collusion (T_C)       Ext      0.1982     0.1160       -0.0823      -41.50%      -50.410      1.07e-21   -11.27
S4: Connected q=0.00 (T_C)      Std      0.0000     0.0000        0.0000        0.00%      Undefined    Undefined  Undefined
S4: Connected q=0.05 (T_C)      Std      0.0935     0.1176       +0.0242      +25.89%      +11.757      3.66e-10    +2.63
S4: Connected q=0.10 (T_C)      Std      0.1606     0.1885       +0.0279      +17.34%      +13.621      2.96e-11    +3.05
S4: Connected q=0.20 (T_C)      Std      0.2731     0.2920       +0.0189       +6.92%       +9.209      1.95e-8     +2.06
S4: Connected q=0.40 (T_C)      Std      0.4124     0.4045       -0.0079       -1.90%       -4.799      1.25e-4     -1.07
S5: Adaptive Attacker (T_C)     Std      0.0964     0.1004       +0.0040       +4.16%       +1.739       0.098      +0.39
S6: Receipt Grinding (T_C)      Std      0.0922     0.1046       +0.0123      +13.38%       +3.860      1.06e-3     +0.86
S6: Receipt Grinding (T_C)      Ext      0.0558     0.0658       +0.0100      +17.92%       +4.968      8.55e-5     +1.11
S7: Dispute Manip (T_C)         Std      0.0000     0.0000        0.0000        0.00%      Undefined    Undefined  Undefined
S8: Asym Uploader (t_up)        Std      0.1574     0.1754       +0.0180      +11.43%      +54.177      2.74e-22   +12.11
S8: Asym Uploader (t_up)        Ext      0.1584     0.1786       +0.0202      +12.74%      +73.490      8.57e-25   +16.43
S9: Reciprocal Comm (T_C)       Std      0.0000     0.0000        0.0000        0.00%      Undefined    Undefined  Undefined
S9: Reciprocal Comm (T_C)       Ext      0.0000     0.0000        0.0000        0.00%      Undefined    Undefined  Undefined
========================================================================================================================
Note: Reported p-values are uncorrected paired Student's t-tests. Zero-variance cases (sd = 0) yield indeterminate 0/0,
reported as Undefined. Scenarios 1-7 and 9 evaluate colluder trust T_C; Scenario 8 evaluates uploader trust t_up.
```

### A. Key Statistical Findings
1. **Collusion Suppression in Leaky Topologies (Scenario 3):** Under leaky collusion, EW-EigenTrust achieved a statistically significant **$40.88\%$ reduction** in colluder trust at standard scale ($0.1834 \to 0.1084, t = -34.354, p = 1.44 \times 10^{-18}, d_z = -7.68$) and a **$41.50\%$ reduction** at extended scale ($0.1982 \to 0.1160, t = -50.410, p = 1.07 \times 10^{-21}, d_z = -11.27$).
2. **Refutation of Hypothesis H-1 (Scenario 6):** Preregistered Hypothesis H-1 asserted that edge saturation ceilings would suppress receipt grinding. In empirical execution, colluder trust **increased by $+13.38\%$** at standard scale ($0.0922 \to 0.1046, t = +3.860, p = 1.06 \times 10^{-3}$) and **$+17.92\%$** at extended scale ($0.0558 \to 0.0658, t = +4.968, p = 8.55 \times 10^{-5}$). **H-1 was formally refuted.**
3. **Preservation of Honest Asymmetric Providers (Scenario 8):** Uploader trust $t_{\text{uploader}}$ increased by **$+11.43\%$** at standard scale ($0.1574 \to 0.1754, t = +54.177, p = 2.74 \times 10^{-22}$) and **$+12.74\%$** at extended scale ($0.1584 \to 0.1786, t = +73.490, p = 8.57 \times 10^{-25}$), confirming preregistered Hypothesis H-2 (retention ratio $\ge 1.11$).
4. **Collapse of Local-Only Baseline:** Under receipt grinding (S6), Local-Only assigned **$99.32\%$ (std) and $99.73\%$ (ext)** of network trust to colluders, demonstrating that naive local aggregation collapses completely under synthetic ratings.

---

## VIII. Discussion and Critical Analysis

### A. Derivation of the Closed-Set Flow Identity
To explain why edge ceilings failed to reduce colluder trust in closed topologies (Scenarios 2, 4, 6), we derive the stationary trust relationship from first principles.

Let $V = H \cup C$ be partitioned into honest peers $H$ and colluders $C$. Let $\mathbf{C}' \in \mathbb{R}^{n \times n}$ denote the row-stochastic normalized transition matrix ($\sum_{j \in V} C'_{ij} = 1$). The stationary trust vector satisfies:
$$\mathbf{t} = (1 - \alpha) (\mathbf{C}')^T \mathbf{t} + \alpha \mathbf{p}$$
In component form for node $j$:
$$t_j = (1 - \alpha) \sum_{i \in V} C'_{ij} t_i + \alpha p_j$$
Summing over all coalition nodes $c \in C$:
$$\sum_{c \in C} t_c = (1 - \alpha) \left[ \sum_{c \in C} \sum_{h \in H} C'_{hc} t_h + \sum_{c \in C} \sum_{c' \in C} C'_{c' c} t_{c'} \right] + \alpha \sum_{c \in C} p_c$$
Interchanging the summation order in the internal term:
$$\sum_{c \in C} \sum_{c' \in C} C'_{c' c} t_{c'} = \sum_{c' \in C} t_{c'} \left( \sum_{c \in C} C'_{c' c} \right)$$

#### Three Structural Assumptions:
1. **Strict Coalition Closure:** Colluders assign zero outgoing trust to honest peers:
   $$\forall c' \in C, \forall h \in H: C'_{c' h} = 0$$
2. **Zero Teleportation Mass on Colluders:** Pre-trust is concentrated exclusively on honest supernodes ($S \subseteq H$):
   $$\sum_{c \in C} p_c = 0$$
3. **No Dangling Coalition Rows:** Every colluder has positive unnormalized internal edge weight ($\sum_{c \in C} A_{c' c} > 0$). Row stochasticity guarantees:
   $$\sum_{c \in C} C'_{c' c} = 1.0$$
   *(Crucial Fallback Note: The implemented engine fallback sets dangling rows to the pre-trust vector: $C'_{i, :} = \mathbf{p}$. Because $\mathbf{p}$ is supported only on honest supernodes, a dangling colluder row sends probability mass to honest peers, breaking closure. Strict closure requires that no coalition row dangles).*

Substituting these conditions yields:
$$\sum_{c \in C} t_c = (1 - \alpha) \left[ \sum_{h \in H} t_h \sum_{c \in C} C'_{hc} + \sum_{c \in C} t_c \right]$$
Subtracting $(1 - \alpha) \sum_{c \in C} t_c$ from both sides:
$$\alpha \sum_{c \in C} t_c = (1 - \alpha) \sum_{h \in H} t_h \sum_{c \in C} C'_{hc}$$
Dividing by $\alpha$ establishes the **Closed-Set Flow Identity**:
$$T_C = \sum_{c \in C} t_c = \left(\frac{1 - \alpha}{\alpha}\right) F_{H \to C}$$
where $F_{H \to C} \equiv \sum_{h \in H} t_h \sum_{c \in C} C'_{hc}$ is the **trust-weighted incoming flow**.

#### Separation of Flow Identity and Invariance Condition:
The flow identity proves that total coalition trust depends strictly on incoming flow $F_{H \to C}$. For coalition trust to remain strictly **invariant** across internal algorithm changes, the incoming flow $F_{H \to C}$ must remain constant.  
Because $C'_{hc} = A_{hc} / \sum_{k \in V} A_{hk}$, if honest bridge nodes saturate internal honest edges, the normalization denominator changes, altering $C'_{hc}$. Furthermore, shifts in honest trust distribution $\mathbf{t}_H$ alter $F_{H \to C}$. This explains why EW-EigenTrust exhibited statistically significant increases in S2 Extended ($+13.50\%$), S4 ($q \le 0.20$), and S6 ($+13.38\%$ to $+17.92\%$).

### B. Diagnosis of Scenario 7 Degeneracy
In Scenario 7, colluder trust share was identically $0.0000$ across all seeds.  
**Root Cause:** In the benchmark harness (`experiments/phase8_2_benchmark.py:723-744`), honest peers selected transaction partners strictly within their own candidate pool (`hn + sn`). Honest nodes never transacted with or rated colluders ($C'_{hc} = 0$). Colluders held zero pre-trust ($p_c = 0$) and exchanged mutual ratings ($\sum_{c'} A_{cc'} > 0$), meaning no dangling fallback occurred. Under these conditions, the non-homogeneous source term entering the coalition was identically zero:
$$\left[\mathbf{I} - (1 - \alpha)(\mathbf{C}'_{CC})^T\right] \mathbf{t}_C = \mathbf{0} \implies \mathbf{t}_C = \mathbf{0}$$
Zero colluder trust is a **structurally degenerate artifact of topological disconnection**, not proof of active dispute resistance.

---

## IX. Limitations and Threats to Validity

1. **Closed-Set Flow Vulnerability:** EW-EigenTrust cannot suppress closed collusive clusters that obtain honest incoming bridge edges under low-to-moderate connectivity ($q \le 0.20$).
2. **Decentralized Evidence Portability Gap:** In simulation, Tier 3 delivery verification relies on a global delivery key pool ($\mathcal{D}_{\text{sim}}$). In decentralized networks, bilateral receipts do not carry raw chunks or Merkle proofs off-the-wire; third-party verification defaults to Tier 1/2 unless zero-knowledge delivery proofs or interactive challenges are deployed.
3. **Computational Runtime Overhead:** Linear iteration over large evidence journals increased execution time from $1.81\text{ ms}$ (Vanilla) to $166.32\text{ ms}$ ($92\times$ overhead) in Scenario 6 extended scale (152,000 receipts). Production implementations require incremental matrix indexing.
4. **Network Scale Bounds:** Empirical benchmarks were bounded to 20–50 simulated nodes; asymptotic behavior across thousands of dynamic peers remains unvalidated.
5. **No Production Claims:** The reference codebase is an in-memory discrete-event simulation harness. It is not claimed to be formally verified or production-ready.

---

## X. Social-Networking Applicability (Conceptual Extension)

While empirically validated on P2P file sharing, the four-layer architecture provides an architectural foundation for decentralized social networks (e.g., Nostr, Scuttlebutt):

```
TABLE II
ARCHITECTURAL MAPPING TO DECENTRALIZED SOCIAL NETWORKS
========================================================================================================
Protocol Layer      P2P File Sharing (Evaluated)             P2P Social Networking (Conceptual Mapping)
--------------------------------------------------------------------------------------------------------
Layer 1: Identity   did:peer-style keys; Hashcash PoW        User profiles; PoW bot throttling
Layer 2: WoT PKI    Cross-certificates; DFS disjoint paths   Peer key-signing; bounded follow-graph trust
Layer 3: Reputation 3-tier delivery weighting; edge ceilings Signed post/interaction attestations; spam damping
Layer 4: Revocation Quorum CRR eviction; Shamir key recovery Social guardian recovery; key rotation
========================================================================================================
```

### Primitive Differentiation:
- **PKI Cross-Certificates vs. Social Follows:** A PKI cross-certificate is a signed Layer 2 cryptographic delegation statement binding a public key to an identity subject within a bounded validity window ($[t_{\text{valid}}, t_{\text{expires}}]$). In contrast, a social follow expresses a social subscription relationship whose authentication, signature, and integrity properties depend on the platform protocol (e.g., Nostr signed contact lists vs. application-level pointers). A follow establishes subscription interest, not cryptographic key ownership.
- **PKI Cross-Certificates vs. Social Endorsements:** An endorsement is a subjective Layer 3 reputation assertion regarding another peer's social conduct; it does not certify cryptographic key ownership.
- **Bilateral Receipts vs. Message Attestations:** A bilateral receipt co-certifies a two-party exchange; a message attestation is a unilateral author signature verifying post origin.

**Scope Boundary:** No custom social network simulator or user-feed dataset was evaluated. Social networking applicability is strictly formulated as a theoretical architectural extension.

---

## XI. Conclusion and Future Work

This paper presented a four-layer decentralized PKI trust management architecture synthesizing self-certifying cryptographic identities, Web-of-Trust mesh PKI, Evidence-Weighted EigenTrust v1.8, and threshold certificate revocation. Empirical benchmarks across 1,140 trial runs demonstrated that while evidence weighting slashes leaky collusion by $>40\%$ ($p < 10^{-18}$) and preserves honest asymmetric uploaders ($+11\%$ to $+13\%$), internal edge ceilings cannot suppress closed coalitions, in accordance with the Closed-Set Flow Identity ($T_C = \frac{1-\alpha}{\alpha} F_{H \to C}$). Preregistered Hypothesis H-1 was formally refuted under receipt grinding, and Scenario 7 was diagnosed as structurally degenerate. Future research will focus on spectral bridge-cut partitioning to discount incoming bridge edges dynamically, zero-knowledge delivery proofs to bridge the decentralized portability gap, and empirical evaluation on empirical social network graphs.

---

## References

1. A. Back, "Hashcash - A Denial of Service Counter-Measure," *Technical Report*, hashcash.org, 2002. [Online]. Available: http://www.hashcash.org/papers/hashcash.pdf
2. D. Hardman, S. Curran, and S. Curren, Eds., "Peer DID Method Specification," *Decentralized Identity Foundation (DIF) Community Specification Draft*, 2021. [Online]. Available: https://identity.foundation/peer-did-method-spec/
3. S. D. Kamvar, M. T. Schlosser, and H. Garcia-Molina, "The EigenTrust algorithm for reputation management in P2P networks," in *Proc. 12th Int. Conf. World Wide Web (WWW '03)*, Budapest, Hungary, 2003, pp. 640–651. DOI: 10.1145/775152.775242.
4. R. C. Merkle, "Protocols for public key cryptosystems," in *Proc. 1980 IEEE Symp. Security and Privacy*, Oakland, CA, USA, 1980, pp. 122–134. DOI: 10.1109/SP.1980.10006.
5. A. Shamir, "How to share a secret," *Commun. ACM*, vol. 22, no. 11, pp. 612–613, Nov. 1979. DOI: 10.1145/359168.359176.
6. W3C Decentralized Identifier Working Group, "Decentralized Identifiers (DIDs) v1.0: Core Architecture, Data Model, and Representations," *W3C Recommendation*, July 2022. [Online]. Available: https://www.w3.org/TR/did-core/
7. P. Zimmermann, *The Official PGP User's Guide*, Cambridge, MA, USA: MIT Press, 1995. ISBN: 978-0262740173.
