# Final Case Study Synthesis: PKI-Based Trust Management for Peer-to-Peer File-Sharing and Social Networking Platforms (v8.0-FINAL-FREEZE)

**Document Version:** 8.0.0-FINAL-FREEZE  
**Date:** October 9, 2026  
**Author:** Candidate Shreyan Nayak (23BKT0039)  
**Technical Consistency Reference:** [`PHASE8_11_FINAL_CONSISTENCY_REPORT.md`](file:///d:/pki_casestudy/PHASE8_11_FINAL_CONSISTENCY_REPORT.md)  
**Target Specifications & Gate Reviews:**  
- [`PROTOCOL_SPEC.md`](file:///d:/pki_casestudy/PROTOCOL_SPEC.md) (v2.2.0-FROZEN)  
- [`SECURITY_MODEL.md`](file:///d:/pki_casestudy/SECURITY_MODEL.md) (v2.2.0-FROZEN)  
- [`reports/PROTOCOL_FINAL_CORRECTION_REPORT.md`](file:///d:/pki_casestudy/reports/PROTOCOL_FINAL_CORRECTION_REPORT.md)  
- [`NOVEL_TRUST_ALGORITHM_DESIGN_V1_8.md`](file:///d:/pki_casestudy/NOVEL_TRUST_ALGORITHM_DESIGN_V1_8.md)  
- [`PHASE8_1_IMPLEMENTATION_REPORT.md`](file:///d:/pki_casestudy/PHASE8_1_IMPLEMENTATION_REPORT.md)  
- [`PHASE8_2_PREREGISTRATION.md`](file:///d:/pki_casestudy/PHASE8_2_PREREGISTRATION.md)  
- [`PHASE8_2_BENCHMARK_REPORT.md`](file:///d:/pki_casestudy/PHASE8_2_BENCHMARK_REPORT.md)  
- [`PHASE8_3_REPRODUCIBILITY_AUDIT.md`](file:///d:/pki_casestudy/PHASE8_3_REPRODUCIBILITY_AUDIT.md)  
- [`PHASE8_5_FINAL_CONSISTENCY_REPORT.md`](file:///d:/pki_casestudy/PHASE8_5_FINAL_CONSISTENCY_REPORT.md)  
- [`PHASE8_6_SUBMISSION_READINESS_REPORT.md`](file:///d:/pki_casestudy/PHASE8_6_SUBMISSION_READINESS_REPORT.md)  
- [`PHASE8_7_FINAL_FREEZE_REPORT.md`](file:///d:/pki_casestudy/PHASE8_7_FINAL_FREEZE_REPORT.md)  
- [`PHASE8_8_FINAL_FREEZE_REPORT.md`](file:///d:/pki_casestudy/PHASE8_8_FINAL_FREEZE_REPORT.md)  
- [`PHASE8_9_INTEGRITY_AND_FREEZE_REPORT.md`](file:///d:/pki_casestudy/PHASE8_9_INTEGRITY_AND_FREEZE_REPORT.md)  
- [`PHASE8_10_REGRESSION_AND_FREEZE_REPORT.md`](file:///d:/pki_casestudy/PHASE8_10_REGRESSION_AND_FREEZE_REPORT.md)  
- [`PHASE8_11_FINAL_CONSISTENCY_REPORT.md`](file:///d:/pki_casestudy/PHASE8_11_FINAL_CONSISTENCY_REPORT.md)  

---

## 1. Research Problem and Motivation

### 1.1 The Decentralized Trust Dilemma
Traditional Public Key Infrastructure (PKI) relies on centralized Certificate Authorities (CAs) to establish identity authenticity and trust. In decentralized peer-to-peer (P2P) systems, this centralized root of trust represents a single point of failure, a vector for censorship, and a structural mismatch with the underlying network topology. 

Without centralized gatekeepers, decentralized networks face fundamental security challenges:
1. **Zero-Cost Identity Creation (Sybil Threat):** Adversaries can generate arbitrary numbers of pseudonymous identities at negligible cost to swamp honest peer votes.
2. **Attributable Inconsistent Delivery vs. Slander:** When a node serves corrupted data (e.g., poisoned file chunks), simple unauthenticated complaint mechanisms allow malicious downloaders to frame honest providers (slander), while naive reputation aggregation allows colluders to inflate each other's standing (collusion). Attributing fault without downloading full payloads requires cryptographic contradiction proofs. A failed Merkle proof alone does not prove third-party attributable inconsistency; certified contradiction requires authentic proof of the committed chunk hash conflicting with a signed delivery envelope for that exact chunk index. Furthermore, cryptographic contradiction proves attributable delivery of conflicting data; it does not prove subjective malicious intent (e.g., distinguishing hardware storage corruption from deliberate poisoning).
3. **Collusion and Edge Grinding:** Strategic colluders can exchange synthetic positive ratings amongst themselves without performing genuine work, manufacturing artificial reputation to capture network trust.
4. **Key Compromise and Revocation Deadlock:** In the absence of a central directory, disseminating key revocation records and recovering lost or compromised master keys without central custodians requires fault-tolerant threshold authorization (3-of-5 supernode quorum signatures). A 3-of-5 threshold signature mechanism enforces administrative multi-party authorization; it does not constitute Byzantine fault-tolerant consensus.

### 1.2 Dual Application Context: P2P File Sharing and Social Networking
The research problem spans two distinct peer-to-peer paradigms:
- **P2P File-Sharing Platforms (e.g., BitTorrent, IPFS):** Trust is operational, transactional, and objective. It governs content authenticity, delivery fulfillment, bandwidth reciprocity, chunk integrity, and non-repudiation of transfer failures.
- **P2P Social-Networking Platforms (e.g., Nostr, Scuttlebutt, Matrix, Mastodon):** Trust is relational, subjective, and identity-centric. It governs user impersonation, friendship/follow assertions, message attestation, spam/harassment mitigation, and social account recovery following device compromise.

---

## 2. Research Objectives and Explicit Scope Alignment

To maintain strict scientific integrity, this research delineates its contributions across three clearly bounded categories:

```
┌──────────────────────────────────────────────────────────────────────────┐
│                   SHARED DECENTRALIZED TRUST INFRASTRUCTURE              │
│  Layer 1: Identity & PoW   │  Layer 2: Mesh Web-of-Trust PKI             │
│  Layer 3: EigenTrust v1.8  │  Layer 4: Threshold Revocation & Recovery   │
└────────────────────────────────────┬─────────────────────────────────────┘
                                     │
           ┌─────────────────────────┴─────────────────────────┐
           ▼                                                   ▼
┌──────────────────────────────────────┐    ┌──────────────────────────────────────┐
│       IMPLEMENTED & EVALUATED        │    │        CONCEPTUAL APPLICATION        │
│          APPLICATION DOMAIN          │    │          EXTENSION DOMAIN            │
│ ──────────────────────────────────── │    │ ──────────────────────────────────── │
│ • P2P File Sharing (SwarmSimulation) │    │ • Decentralized Social Networking    │
│ • Merkle Chunk Trees & Proofs        │    │ • Follows vs Endorsements vs Certs   │
│ • Delivery Envelopes & Manifests     │    │ • Unilateral Message Attestations    │
│ • Attributable Fault Contradiction   │    │ • Social Guardian Secret Recovery    │
│ • Collusion & Grinding Benchmarks    │    │ • Sybil Cluster Moderation Dynamics  │
│ [Empirically Validated: Phases 5-8]  │    │ [Architecturally Specified: Phase 8] │
└──────────────────────────────────────┘    └──────────────────────────────────────┘
```

1. **Shared Trust Infrastructure (Implemented Reference Code & Test-Suite Verified in Simulation):**
   A four-layer decentralized PKI protocol comprising cryptographic peer identities (`did:peer`-style syntax), Hashcash proof-of-work admission barriers, Web-of-Trust bounded path discovery, evidence-weighted reputation propagation, and threshold certificate revocation with Shamir secret sharing. Verified across 75 automated unit and regression tests in Python (61 in `tests/test_trust_framework.py` and 14 in `tests/test_ew_eigentrust.py`).
   > [!NOTE]
   > Software test-suite execution verifies programmatic adherence to specified unit and integration test cases in Python; it does not constitute mathematical formal verification (such as machine-checked proofs in Coq or Isabelle), a cryptographic reduction proof, or production-grade network deployment.
2. **Implemented and Evaluated Application Domain (P2P File Sharing):**
   Full implementation of content-addressed chunk transfers, cryptographic manifests, binary Merkle tree proofs, delivery verification envelopes, attributable fault evidence generation, and empirical evaluation under adversarial conditions (poisoning, replay, receipt grinding, closed collusion, leaky collusion, and adaptive attackers).
3. **Social-Networking Applicability (Conceptual Architecture & Transfer Formulation):**
   A structural mapping explaining how the shared four-layer infrastructure extends to decentralized social networks. **Scope Boundary:** No custom social network simulator, user-feed dataset, or social graph empirical experiment was executed. Social networking applicability is strictly formulated as a theoretical and architectural generalization.

---

## 3. Background and Related-Work Positioning

The framework synthesizes and improves upon foundational literature across distributed systems and applied cryptography:

1. **Decentralized Identity:** 
   Derives self-certifying, offline-resolvable cryptographic identifiers from Ed25519 public keys using a custom `did:peer`-style string syntax (`did:peer:2.Ez<64-hex>`). Note that this implementation does **NOT** conform to the official Decentralized Identity Foundation (DIF) `did:peer` Method 2 specification (which mandates multicodec prefixes, multibase base58btc encoding `z...`, and purpose code `V` for verification keys rather than `E`), nor has full W3C DID Core conformance been validated in code (Hardman, Curran, & Curren, 2021; W3C, 2022).
2. **Sybil Resistance:**
   Integrates Hashcash-style proof-of-work (Back, 2002) at identity generation. While PoW does not prevent determined hardware-scale Sybil creation, it imposes a strictly verified computational cost ($O(2^d)$ hash trials) that eliminates zero-cost identity generation.
3. **Web-of-Trust PKI:**
   Extends PGP Web-of-Trust principles (Zimmermann, 1995) to dynamic mesh topologies. Peers cross-certify public keys with Ed25519 signatures, enabling multi-hop trust paths bounded by a strict hop limit ($k \le 4$) with intermediate-vertex disjointness filtering.
4. **Spectral Reputation & EigenTrust:**
   Builds upon the seminal EigenTrust algorithm (Kamvar, Schlosser, & Garcia-Molina, 2003). While vanilla EigenTrust relies on linear satisfaction accumulation $S_{ij} = \sum \text{sat} - \sum \text{unsat}$, our protocol introduces **Evidence-Weighted EigenTrust v1.8 (`EVIDENCE_ONLY`)**, incorporating concave saturation ceilings ($\Phi_{\text{edge}}$), 3-tier delivery verification, exponential freshness decay, dispute accounting, and certified fault nullification.
5. **Fault Attribution & Merkle Proofs:**
   Implements Merkle inclusion proofs (Merkle, 1980) over file chunk digests. In contrast to naive dispute mechanisms, fault attribution requires a cryptographic contradiction proof: the server's Ed25519 signature over a chunk hash combined with an authentic Merkle inclusion proof proving that a different chunk hash was committed to the publisher's root for that exact chunk index.
6. **Threshold Cryptography:**
   Employs Shamir's $(k, n)$ Threshold Secret Sharing (Shamir, 1979) over $GF(256)$ combined with guardian-signed Recovery Authorization Tokens (`AuthTok`) to achieve verifiable master key recovery without central key escrow.

---

## 4. Consolidated Technical Architecture

The complete system architecture operates across four distinct, vertically integrated protocol layers:

```mermaid
graph TD
    subgraph Layer1["Layer 1: Identity & Admission Barrier"]
        KEY[Ed25519 Key Pair] --> DID["did:peer-Style Identifier"]
        DID --> POW["Hashcash PoW (d >= 8)"]
        POW --> PEER["Active PeerState"]
    end

    subgraph Layer2["Layer 2: Mesh Web-of-Trust PKI"]
        CROSS[Ed25519 Cross-Certificates] --> MESH[Dynamic Mesh Graph]
        MESH --> DFS["DFS k <= 4 Vertex-Disjoint Paths"]
        DFS --> SUPERNODE["Pre-Trusted Supernode Backbone"]
    end

    subgraph Layer3["Layer 3: Evidence-Weighted EigenTrust v1.8"]
        RCPT[Bilateral Receipts & Manifests] --> TIER["3-Tier Evidence Weighting"]
        TIER --> CEIL["Concave Edge Ceiling Phi_edge"]
        CEIL --> DECAY["Freshness Decay & Dispute Accounting"]
        DECAY --> DANG["Dangling Row Fallback C'_i,: = p"]
        DANG --> POWER["Power Iteration Convergence"]
    end

    subgraph Layer4["Layer 4: Threshold Revocation & Key Recovery"]
        FAULT[Attributable Fault Evidence] --> PROP[Revocation Proposal]
        PROP --> QUORUM["m-of-n Supernode Quorum Authorization"]
        QUORUM --> CRR[Certificate Revocation Record]
        CRR --> EVICT[Mesh Eviction]
        SHAMIR["Shamir (k, n) Secret Sharing"] --> AUTHTOK[Guardian AuthTok]
        AUTHTOK --> RECOV[Master Seed Reconstruction]
        RECOV --> ROT[Mandatory Key Rotation]
    end

    Layer1 --> Layer2
    Layer2 --> Layer3
    Layer3 --> Layer4
```

### Layer 1: Cryptographic Identity & Admission Barrier
- **Identifier Generation:** Node generates an Ed25519 signing key pair. In the reference implementation (`src/layer1_identity.py:68`), the DID string is formatted as `did:peer:2.Ez{public_key_hex}` using the 64-character lowercase hex representation of the public key.
  > [!NOTE]
  > **Non-Compliance Note on DIF `did:peer` numalgo 2:**  
  > The emitted string `did:peer:2.Ez<64-hex>` is a simulation-specific custom identifier and is **NOT compliant** with the official DIF `did:peer` Method 2 specification:
  > 1. In the DIF specification, purpose codes designate method usage: `V` denotes verification/assertion (signing) methods, whereas `E` specifically denotes key-agreement/encryption methods (e.g., X25519). Using `E` for an Ed25519 signing key contradicts the spec.
  > 2. DIF numalgo 2 requires multicodec prefixing (`0xed01` for Ed25519) followed by multibase base58btc encoding (beginning with `z`), rather than raw lowercase hexadecimal.
  > 3. Claims of "adopting did:peer Method 2" or "conforming to W3C DID Core" are unsupported by the reference code, which implements a lightweight simulation string format.
- **Proof-of-Work Admission Barrier:** Node computes a SHA-256 Hashcash nonce satisfying difficulty $d$ ($H(DID \parallel \text{nonce}) < 2^{256-d}$). Verification is $O(1)$. This imposes a computational cost barrier ($O(2^d)$ hash trials) that eliminates zero-cost identity generation, though it does not prevent well-resourced adversaries.
- **Finite State Machine:** Peer states follow the strict 5-state lifecycle defined in `PROTOCOL_SPEC.md` (§2.1):
  $$\text{UNKNOWN} \xrightarrow{\text{T1}} \text{ACTIVE} \underset{\text{T3a}}{\overset{\text{T2}}{\longleftrightarrow}} \text{SUSPECTED} \xrightarrow{\text{T4}} \text{REVOCATION\_PROPOSED} \xrightarrow{\text{T5a}} \text{REVOKED}$$
  - **T1 (Admission):** `UNKNOWN` $\to$ `ACTIVE` upon valid PoW and self-signature.
  - **T2 (Suspicion):** `ACTIVE` $\to$ `SUSPECTED` upon attributable fault evidence or unverified suspicion.
  - **T3a (Subjective Exoneration):** `SUSPECTED` $\to$ `ACTIVE` upon expiration of $T_{\text{susp}}$ for unverified suspicion. Certified fault suspicion (T3b) persists indefinitely.
  - **T4 (Escalation):** `SUSPECTED` $\to$ `REVOCATION_PROPOSED` upon formal supernode committee proposal.
  - **T5a (Quorum Eviction):** `REVOCATION_PROPOSED` $\to$ `REVOKED` upon assembling $m$-of-$n$ supernode signatures on a CRR.
  - **T5b (Quorum Timeout Fallback):** If $T_{\text{vote}}$ expires without reaching quorum ($k < m$), the state **reverts to `SUSPECTED`, never directly to `ACTIVE`**.

### Layer 2: Mesh Web-of-Trust PKI
- **Cross-Certification:** Peers issue signed `CrossCertificate` records asserting unidirectional trust with valid time windows $[t_{\text{valid}}, t_{\text{expires}}]$. Signed payload format:
  $$\text{PKI\_V2\_CROSSCERT}:\langle\text{issuer\_did}\rangle:\langle\text{subject\_did}\rangle:\langle\text{trust\_weight\_4dec}\rangle:\langle\text{issued\_at}\rangle:\langle\text{expires\_at}\rangle$$
- **Bounded Path Discovery (`find_disjoint_paths`):** Implemented in `src/layer2_mesh_pki.py:168-220` using depth-first search (DFS) with a maximum hop limit $k \le 4$. Paths are filtered to guarantee **strict intermediate-vertex disjointness** (no intermediate vertex may occur in more than one returned path). Cumulative path trust is the direct multiplicative product of cross-certificate weights:
  $$\text{trust}(P) = \prod_{c \in P} \text{trust\_weight}(c)$$
  Candidate paths are prioritized by descending path trust, then shorter hop count.
- **Pre-Trusted Backbone:** Bootstrapped via 5 pre-trusted supernodes ($S \subset V$) with static trust distribution $\mathbf{p}$ ($p_s = 1/|S|$ for $s \in S$, $p_i = 0$ otherwise). Supernode election (`elect_supernodes`) is explicitly disabled (`NotImplementedError`) per `PROTOCOL_SPEC.md` §3.3.

### Layer 3: Evidence-Weighted EigenTrust v1.8 (`EVIDENCE_ONLY`)
- **Evidence Weighting ($\gamma_{\text{ev}}$):** Replaces linear satisfaction with a 3-tier evidence classification (`src/layer3_eigentrust.py:1144-1149`, `NOVEL_TRUST_ALGORITHM_DESIGN_V1_8.md:154-159`):
  - **Tier 1 (Unindexed Bilateral Receipts):** Missing, malformed, or unindexed delivery references receive heavy discounting ($\mu_{\text{unverified}} = 0.10$).
  - **Tier 2 (Manifest-Referenced Receipts):** Receipts referencing a known indexed Content Manifest root receive moderate discounting ($\mu_{\text{referenced}} = 0.25$).
  - **Tier 3 (Local Cryptographically Verified Deliveries):** Receipts referencing a verified chunk delivery key matching local client verification receive full credit ($\gamma_{\text{ev}} = 1.00$).
- **Freshness Decay ($\gamma_{\text{time}}$):** Exponential timestamp decay $\gamma_{\text{time}} = \exp(-\Delta t / \tau)$, where $\tau = 86,400\text{ s}$ (24 hours).
- **Dispute Accounting ($\gamma_{\text{dispute}}$):** Subjective negative receipts (`rating < 0.0`) scale positive edge strength via the exact bounded ratio (`src/layer3_eigentrust.py:1177`, `NOVEL_TRUST_ALGORITHM_DESIGN_V1_8.md:162`):
  $$\gamma_{\text{dispute}}(N_{\text{pos}}, N_{\text{neg}}) = \max\left(0.0, 1.0 - \frac{2 \cdot N_{\text{neg}}}{N_{\text{pos}} + 1.0}\right)$$
- **Certified Fault Nullification:** Attributable `FaultEvidenceRecord` or revoked/suspected state zeroes **incoming** edge weights to the accused peer (`src/layer3_eigentrust.py:1115-1117`, `NOVEL_TRUST_ALGORITHM_DESIGN_V1_8.md:357-364`):
  $$\forall i \in V: A_{i, \text{accused}} = 0.0$$
  Outbound ratings $A_{\text{accused}, j}$ from the accused peer are not zeroed by this check, allowing outbound weights to decay naturally while preventing reputation harvesting.
- **Concave Edge Ceiling ($\Phi_{\text{edge}}$):** Bounded hyperbolic tangent saturation function capping total effective evidence per directed edge (`src/layer3_eigentrust.py:1178`, `NOVEL_TRUST_ALGORITHM_DESIGN_V1_8.md:144`):
  $$\Phi_{\text{edge}}(E_{\text{pos}}) = K_{\max} \cdot \tanh\left(\frac{\lambda_{\text{sat}} \cdot E_{\text{pos}}}{K_{\max}}\right), \quad K_{\max} = 10.0, \, \lambda_{\text{sat}} = 0.50$$
  This ensures $\Phi_{\text{edge}}(E) < K_{\max} = 10.0$ strictly for all finite evidence in real arithmetic.
- **Dangling-Node Fallback Rule:** If a node $i$ has zero positive outgoing edge weight ($\sum_j S'_{ij} = 0$), the normalized transition row falls back to the **pre-trusted restart vector $\mathbf{p}$** ($C'_{i, :} = \mathbf{p}$), as implemented in `src/layer3_eigentrust.py:1218` and `NOVEL_TRUST_ALGORITHM_DESIGN_V1_8.md:465`.
  > [!IMPORTANT]
  > **Dangling Fallback and Coalition Closure:**  
  > If a colluder node $c \in C$ has zero outgoing edge weight and triggers the dangling fallback $C'_{c, :} = \mathbf{p}$, because pre-trust is concentrated on honest supernodes ($p_s > 0$ for $s \in S \subseteq H$), transition probability mass is assigned directly to honest peers ($C'_{c, s} > 0$). This **violates coalition closure** ($C'_{c, h} = 0$). Therefore, dangling colluder rows break coalition closure rather than preserving it; the Closed-Set Flow Identity holds strictly when no coalition node dangles.
- **Power Iteration Convergence:** Solves the stationary distribution $\mathbf{t} = (1 - \alpha) (\mathbf{C}')^T \mathbf{t} + \alpha \mathbf{p}$ with damping $\alpha = 0.15$ and convergence tolerance $\epsilon = 10^{-6}$.

### Layer 4: Threshold Revocation & Key Recovery
- **Quorum Eviction:** Revocation of compromised or malicious peers requires a Certificate Revocation Record (CRR) bearing $m$-of-$n$ valid supernode signatures ($m = 3, n = 5$). Valid CRRs trigger network-wide peer eviction and link severance. A 3-of-5 threshold signature mechanism enforces administrative multi-party authorization; it does not constitute Byzantine fault-tolerant consensus.
- **Key Recovery:** Master identity keys are protected via Shamir $(k, n)$ secret sharing ($k = 3, n = 5$) over $GF(256)$. Reconstruction requires $k$ authenticated Recovery Authorization Tokens (`AuthTok`). Mandatory post-recovery key rotation invalidates the compromised key and establishes a dual-signed rotation link.

---

## 5. Implementation Status and Testing Evidence

The protocol is implemented in Python across modular components in `src/`:

| Module Path | Core Responsibilities | Implementation Status | Automated Test Suite Coverage |
| :--- | :--- | :---: | :---: |
| [`src/layer1_identity.py`](file:///d:/pki_casestudy/src/layer1_identity.py) | Ed25519 keys, `did:peer`-style derivation, PoW Hashcash, 5-state lifecycle | Protocol Frozen (Simulation Implementation) | Test-Suite Verified (`test_trust_framework.py`: 4 tests) |
| [`src/layer2_mesh_pki.py`](file:///d:/pki_casestudy/src/layer2_mesh_pki.py) | Mesh network, cross-certification, DFS vertex-disjoint paths, hop limits | Protocol Frozen (Simulation Implementation) | Test-Suite Verified (`test_trust_framework.py`: 5 tests) |
| [`src/layer3_eigentrust.py`](file:///d:/pki_casestudy/src/layer3_eigentrust.py) | Merkle trees, Bilateral Receipts, FaultEvidenceRecord verification, EW-EigenTrust v1.8, Evidence Journal | Protocol Frozen (Simulation Implementation) | Test-Suite Verified (`test_trust_framework.py`: 9 tests; `test_ew_eigentrust.py`: 14 tests) |
| [`src/layer4_recovery.py`](file:///d:/pki_casestudy/src/layer4_recovery.py) | CRR quorum authorization, peer eviction, Shamir recovery, rotation | Protocol Frozen (Simulation Implementation) | Test-Suite Verified (`test_trust_framework.py`: 1 test direct + 9 Phase 4 tests) |
| [`src/network_simulator.py`](file:///d:/pki_casestudy/src/network_simulator.py) | Integrated multi-layer simulation harness (`SwarmSimulation`) | Protocol Frozen (Simulation Implementation) | Test-Suite Verified (`test_trust_framework.py`: 33 Phase 3/5/6 tests) |

### Test Suite Execution Evidence
The complete test suite runs deterministically via standard unittest discovery:
```powershell
python -m unittest discover -s tests -v
```
**Measured Test Breakdown by Module and Class (Logged to `tests_scratch/unittest_phase8_9.log`):**

1. **`tests/test_ew_eigentrust.py` (14 tests across 6 classes):**
   - `TestEWIdentifierLifecycleAndDeliveryTiers`: 6 tests (`test_01` to `test_06`)
   - `TestEWEvidenceFreshnessAndDispute`: 3 tests (`test_07` to `test_09`)
   - `TestEWCertifiedFaultNullification`: 1 test (`test_10`)
   - `TestEWEdgeBoundsAndRobustness`: 2 tests (`test_11`, `test_12`)
   - `TestEWVanillaEquivalence`: 1 test (`test_13`)
   - `TestEndToEndSimulationTrace`: 1 test (`test_14`)
2. **`tests/test_trust_framework.py` (61 tests in class `TestPKITrustFramework`):**
   - Layer 1 Unit Tests (`test_layer1_*`): 4 tests
   - Layer 2 Unit Tests (`test_layer2_*`): 5 tests
   - Layer 3 Unit Tests (`test_layer3_*`): 9 tests
   - Layer 4 Unit Tests (`test_layer4_*`): 1 test
   - Phase 3 Accounting Tests (`test_phase3_*`): 11 tests
   - Phase 4 Revocation & Recovery Tests (`test_phase4_*`): 9 tests
   - Phase 5 Integration Tests (`test_phase5_integration_*`): 10 tests
   - Phase 6 Benchmark Regression Tests (`test_phase6_*`): 12 tests
- **Total Discovered & Passing:** Exactly **75 tests** (`Ran 75 tests in 4.964s, OK`).

> [!NOTE]
> Passing 75 automated unit and regression tests verifies implementation consistency against defined test cases in Python simulation. It does not establish mathematical formal verification or readiness for production deployment on decentralized networks.

---

## 6. Experimental Methodology and Empirical Results

The empirical evaluation of EW-EigenTrust v1.8 was conducted under Phase 8.2 and reported in the Phase 8.3 reproducibility audit:
- **Preregistration:** Sealed in [`PHASE8_2_PREREGISTRATION.md`](file:///d:/pki_casestudy/PHASE8_2_PREREGISTRATION.md) prior to running trials.
- **Seeds:** 20 paired random seeds ($\mathcal{S} = \{42 + 17 \cdot i \mid i \in [0, 19]\}$).
- **Network Scales:** Standard Scale (20–35 nodes) and Extended Scale (30–50 nodes).
- **Execution Matrix:** 9 distinct scenarios, 3 trust computation modes (`VANILLA`, `EVIDENCE_ONLY`, `LOCAL_ONLY`), totaling 1,140 individual trial evaluations.
- **Data Source Files on Disk:** [`results/phase8_2_statistical_comparison.csv`](file:///d:/pki_casestudy/results/phase8_2_statistical_comparison.csv), [`results/phase8_2_summary.csv`](file:///d:/pki_casestudy/results/phase8_2_summary.csv), and [`results/phase8_2_raw_results.json`](file:///d:/pki_casestudy/results/phase8_2_raw_results.json).

### 6.1 Master Empirical Results Summary

In the table below, Scenarios 1–7 and 9 evaluate total colluder trust share $T_C = \sum_{c \in C} t_c$. Scenario 8 evaluates honest asymmetric provider trust $t_{\text{uploader}}$ directly. For scenarios where the difference is identically zero across all paired seeds, the standard deviation is zero, rendering the $t$-statistic mathematically undefined ($0/0$); these are reported as **Undefined (zero variance)** rather than substituting artificial test values.

| Scenario | Scale | Vanilla Baseline | EW-EigenTrust v1.8 | Difference $\Delta$ | Rel. Change | Paired $t$-stat | $p$-value | Cohen's $d_z$ | Empirical Outcome |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **S1: Honest Baseline ($T_C$)** | Standard | $0.0000$ | $0.0000$ | $0.0000$ | $0.00\%$ | Undefined | Undefined | Undefined | Simplex conserved ($\sum t_i = 1.0$, zero colluders) |
| **S1: Honest Baseline ($T_C$)** | Extended | $0.0000$ | $0.0000$ | $0.0000$ | $0.00\%$ | Undefined | Undefined | Undefined | Structural zero: zero colluders |
| **S2: Closed Collusion ($T_C$)** | Standard | $0.0850$ | $0.0889$ | $+0.0039$ | $+4.53\%$ | $+1.472$ | $0.158$ | $+0.33$ | Reported increase is not statistically significant ($p = 0.158$) |
| **S2: Closed Collusion ($T_C$)** | Extended | $0.0539$ | $0.0611$ | $+0.0073$ | $+13.50\%$ | $+3.944$ | $8.70 \times 10^{-4}$ | $+0.88$ | Statistically significant colluder gain ($p = 8.70 \times 10^{-4}$) |
| **S3: Leaky Collusion ($T_C$)** | **Standard** | **$0.1834$** | **$0.1084$** | **$-0.0750$** | **$-40.88\%$** | **$-34.354$** | **$1.44 \times 10^{-18}$** | **$-7.68$** | **Collusion suppression in leaky topologies ($>40\%$)** |
| **S3: Leaky Collusion ($T_C$)** | **Extended** | **$0.1982$** | **$0.1160$** | **$-0.0823$** | **$-41.50\%$** | **$-50.410$** | **$1.07 \times 10^{-21}$** | **$-11.27$** | **Collusion suppression in leaky topologies ($>40\%$)** |
| **S4: Connected ($q=0.00$) ($T_C$)**| Standard | $0.0000$ | $0.0000$ | $0.0000$ | $0.00\%$ | Undefined | Undefined | Undefined | Disconnected: structural zero |
| **S4: Connected ($q=0.05$) ($T_C$)**| Standard | $0.0935$ | $0.1176$ | $+0.0242$ | $+25.89\%$ | $+11.757$ | $3.66 \times 10^{-10}$ | $+2.63$ | Low bridge: statistically significant colluder gain ($p = 3.66 \times 10^{-10}$) |
| **S4: Connected ($q=0.10$) ($T_C$)**| Standard | $0.1606$ | $0.1885$ | $+0.0279$ | $+17.34\%$ | $+13.621$ | $2.96 \times 10^{-11}$ | $+3.05$ | Moderate bridge: statistically significant colluder gain ($p = 2.96 \times 10^{-11}$) |
| **S4: Connected ($q=0.20$) ($T_C$)**| Standard | $0.2731$ | $0.2920$ | $+0.0189$ | $+6.92\%$ | $+9.209$ | $1.95 \times 10^{-8}$ | $+2.06$ | Transition region: statistically significant colluder gain ($p = 1.95 \times 10^{-8}$) |
| **S4: Connected ($q=0.40$) ($T_C$)**| Standard | $0.4124$ | $0.4045$ | $-0.0079$ | $-1.90\%$ | $-4.799$ | $1.25 \times 10^{-4}$ | $-1.07$ | High bridge: small statistically significant reduction ($-1.90\%, p = 1.25 \times 10^{-4}$) |
| **S5: Adaptive Attacker ($T_C$)** | Standard | $0.0964$ | $0.1004$ | $+0.0040$ | $+4.16\%$ | $+1.739$ | $0.098$ | $+0.39$ | No statistically significant difference ($p = 0.098$) |
| **S6: Receipt Grinding ($T_C$)** | Standard | $0.0922$ | $0.1046$ | $+0.0123$ | $+13.38\%$ | $+3.860$ | $1.06 \times 10^{-3}$ | $+0.86$ | **H-1 Refuted: statistically significant colluder gain ($p = 1.06 \times 10^{-3}$)** |
| **S6: Receipt Grinding ($T_C$)** | Extended | $0.0558$ | $0.0658$ | $+0.0100$ | $+17.92\%$ | $+4.968$ | $8.55 \times 10^{-5}$ | $+1.11$ | **H-1 Refuted: statistically significant colluder gain ($p = 8.55 \times 10^{-5}$)** |
| **S7: Dispute Manip ($T_C$)** | Standard | $0.0000$ | $0.0000$ | $0.0000$ | $0.00\%$ | Undefined | Undefined | Undefined | **Structurally degenerate zero (topological disconnection)** |
| **S8: Asym Uploader ($t_{\text{uploader}}$)** | Standard | $0.1574$ | $0.1754$ | $+0.0180$ | $+11.43\%$ | $+54.177$ | $2.74 \times 10^{-22}$ | $+12.11$ | **Uploader trust $+11.43\%$ (Ratio $1.1143$, H-2 Confirmed)** |
| **S8: Asym Uploader ($t_{\text{uploader}}$)** | Extended | $0.1584$ | $0.1786$ | $+0.0202$ | $+12.74\%$ | $+73.490$ | $8.57 \times 10^{-25}$ | $+16.43$ | **Uploader trust $+12.74\%$ (Ratio $1.1274$, H-2 Confirmed)** |
| **S9: Reciprocal Comm ($T_C$)** | Standard | $0.0000$ | $0.0000$ | $0.0000$ | $0.00\%$ | Undefined | Undefined | Undefined | Honest community share = $100\%$ (H-4 Confirmed) |
| **S9: Reciprocal Comm ($T_C$)** | Extended | $0.0000$ | $0.0000$ | $0.0000$ | $0.00\%$ | Undefined | Undefined | Undefined | Zero suppression or distortion (H-4 Confirmed) |

> [!NOTE]
> **Note on Statistical Reporting:**  
> All reported $p$-values are paired Student's $t$-test values uncorrected for multiple comparisons across the 9 scenarios, as preregistered in Phase 8.2.

### 6.2 Explicit Diagnosis of Scenario 7 Degeneracy
In Scenario 7, colluder trust share is reported as $0.0000$ under both Vanilla EigenTrust and EW-EigenTrust across all seeds.  

**Root Cause Analysis:**  
In the benchmark implementation ([`experiments/phase8_2_benchmark.py:707-746`](file:///d:/pki_casestudy/experiments/phase8_2_benchmark.py#L707-L746), transaction loop lines 723–744), honest nodes and supernodes strictly selected transaction partners from within their own honest candidate pool (`hn + sn`). Consequently, honest peers never transacted with or rated colluders, meaning incoming normalized bridge flow was identically zero ($C'_{hc} = 0$).  
Furthermore, colluders had zero pre-trust allocation ($p_c = 0$). Because colluders exchanged internal ratings, their internal row sums were strictly positive ($\sum_{c' \in C} A_{c c'} > 0$); thus, **no dangling-row fallback was triggered during benchmark execution**.  

Under these conditions—zero incoming bridge flow from honest nodes ($C'_{hc} = 0$), zero colluder pre-trust ($p_c = 0$), and no dangling colluder rows—the non-homogeneous source term entering the coalition is strictly zero:
$$\left[\mathbf{I} - (1 - \alpha)(\mathbf{C}'_{CC})^T\right] \mathbf{t}_C = (1 - \alpha)(\mathbf{C}'_{HC})^T \mathbf{t}_H + \alpha \mathbf{p}_C = \mathbf{0}$$
Since $(1 - \alpha) < 1$ and $\mathbf{C}'_{CC}$ is row-stochastic, the matrix $\left[\mathbf{I} - (1 - \alpha)(\mathbf{C}'_{CC})^T\right]$ is strictly non-singular, uniquely forcing the stationary coalition trust vector to zero: $\mathbf{t}_C = \mathbf{0}$.  

**Fallback Rule Analysis:**  
The engine's implemented fallback rule ([`src/layer3_eigentrust.py:1218`](file:///d:/pki_casestudy/src/layer3_eigentrust.py#L1218), [`NOVEL_TRUST_ALGORITHM_DESIGN_V1_8.md:465`](file:///d:/pki_casestudy/NOVEL_TRUST_ALGORITHM_DESIGN_V1_8.md#L465)) sets dangling rows to the pre-trusted restart vector: $C'_{i, :} = \mathbf{p}$.  
Because pre-trust is concentrated exclusively on honest supernodes ($p_s > 0$ for $s \in S \subseteq H$, while $p_c = 0$ for all $c \in C$), if a colluder node $c \in C$ were ever dangling, this fallback would assign transition probability mass directly to honest supernodes ($C'_{c, s} > 0$). Such an assignment sends probability out of the coalition, **breaking coalition closure** ($C'_{c, h} = 0$) and invalidating the assumptions of the closed-set flow identity.  
(A hypothetical uniform $1/n$ fallback would assign transition probability $1/n$ across all nodes—both honest and colluding—similarly injecting mass into honest peers, and cannot be treated as satisfying the closure and zero-teleportation assumptions without a separate derivation; furthermore, it is not the rule implemented in the frozen design).  
In the Scenario 7 benchmark, zero colluder trust holds because colluders generated mutual ratings, preventing any dangling row from occurring in the first place.

**Conclusion:** Colluder trust share is zero due to **topological disconnection (a structurally degenerate baseline metric)**, not dynamic dispute handling. While Scenario 7 verified that dispute receipts do not trigger false CRR revocations, it did not test dispute defense against active bridge ingress.

---

## 7. Discussion of Negative Findings and Threats to Validity

### 7.1 Mathematical Derivation of the Closed-Set Flow Identity and Refutation of H-1

#### Complete Derivation from the Stationary EigenTrust Equation
Let $V = H \cup C$ be the set of peers partitioned into honest peers $H$ (including pre-trusted supernodes $S \subseteq H$) and colluders $C$ ($H \cap C = \emptyset$). Let $\mathbf{C}' \in \mathbb{R}^{n \times n}$ denote the row-stochastic normalized transition matrix where $\sum_{j \in V} C'_{ij} = 1$ for all $i \in V$.

The stationary trust vector $\mathbf{t} \in \mathbb{R}^n$ ($\sum_{i \in V} t_i = 1$) satisfies:
$$\mathbf{t} = (1 - \alpha) (\mathbf{C}')^T \mathbf{t} + \alpha \mathbf{p}$$
In component form for each node $j$:
$$t_j = (1 - \alpha) \sum_{i \in V} C'_{ij} t_i + \alpha p_j$$
Summing over all nodes $c \in C$ in the colluder coalition:
$$\sum_{c \in C} t_c = (1 - \alpha) \sum_{c \in C} \sum_{i \in V} C'_{ic} t_i + \alpha \sum_{c \in C} p_c$$
Splitting the sum over $i \in V$ into honest nodes $h \in H$ and colluders $c' \in C$:
$$\sum_{c \in C} t_c = (1 - \alpha) \left[ \sum_{c \in C} \sum_{h \in H} C'_{hc} t_h + \sum_{c \in C} \sum_{c' \in C} C'_{c' c} t_{c'} \right] + \alpha \sum_{c \in C} p_c$$
Interchanging the summation order in the internal coalition term:
$$\sum_{c \in C} \sum_{c' \in C} C'_{c' c} t_{c'} = \sum_{c' \in C} t_{c'} \left( \sum_{c \in C} C'_{c' c} \right)$$

#### Three Structural Assumptions
1. **Strict Coalition Closure:** Colluders assign zero outgoing trust to honest peers:
   $$\forall c' \in C, \forall h \in H: C'_{c' h} = 0$$
2. **Zero Teleportation Mass on Coalition Nodes:** Pre-trust is concentrated entirely on honest supernodes ($S \subseteq H$), so:
   $$\sum_{c \in C} p_c = 0$$
3. **No Dangling Coalition Rows:** For every $c' \in C$, the internal unnormalized edge sum is strictly positive ($\sum_{c \in C} A_{c' c} > 0$).  
   Row stochasticity therefore ensures:
   $$\sum_{c \in C} C'_{c' c} = 1.0$$
   *(Crucial Note: If any colluder row dangles, the fallback $C'_{c', :} = \mathbf{p}$ assigns probability mass to honest supernodes where $p_s > 0$, violating Assumption 1 and breaking coalition closure. The identity strictly requires that no coalition row dangles).*

#### The Closed-Set Flow Identity Equation
Substituting these conditions into the coalition sum:
$$\sum_{c \in C} t_c = (1 - \alpha) \left[ \sum_{h \in H} t_h \sum_{c \in C} C'_{hc} + \sum_{c \in C} t_c \right]$$
Subtracting $(1 - \alpha) \sum_{c \in C} t_c$ from both sides:
$$\alpha \sum_{c \in C} t_c = (1 - \alpha) \sum_{h \in H} t_h \sum_{c \in C} C'_{hc}$$
Dividing by $\alpha$ yields the exact relationship:
$$T_C = \sum_{c \in C} t_c = \left(\frac{1 - \alpha}{\alpha}\right) F_{H \to C}$$
where $F_{H \to C} \equiv \sum_{h \in H} t_h \sum_{c \in C} C'_{hc}$ is the **trust-weighted incoming flow**.

#### Separation: The Flow Identity vs. The Invariance Condition
The flow identity $T_C = \frac{1 - \alpha}{\alpha} F_{H \to C}$ holds whenever the three structural assumptions (closure, zero teleportation mass, and no dangling coalition rows) are satisfied.

However, for aggregate coalition trust $T_C$ to remain strictly **invariant** across internal edge-weight alterations, an **additional condition** is required: **the trust-weighted incoming flow $F_{H \to C}$ must remain constant**.

**Critical Distinction: Aggregate Transition Probability vs. Trust-Weighted Flow:**  
Fixed aggregate transition probabilities $\sum_{c \in C} C'_{hc}$ alone are **not** sufficient to guarantee trust invariance if the honest stationary trust distribution $\mathbf{t}_H$ changes. Because $F_{H \to C} = \sum_{h \in H} t_h \left(\sum_{c \in C} C'_{hc}\right)$, shifts in honest stationary trust $t_h$ directly alter coalition trust.  
Furthermore, $C'_{hc} = A_{hc} / \sum_{k \in V} A_{hk}$. Even if the bridge edge weight $A_{hc}$ is constant, if honest bridge nodes $h$ saturate their internal honest edges, the normalization denominator $\sum_{k \in V} A_{hk}$ changes, altering $C'_{hc}$.

#### Preregistered Hypothesis H-3 and Empirical Data
In [`PHASE8_2_PREREGISTRATION.md`](file:///d:/pki_casestudy/PHASE8_2_PREREGISTRATION.md) (§6), Hypothesis H-3 was formulated as follows:
- **Statement:** *"In a closed coalition with fixed honest bridge flow (Scenario 2), the reduction in colluder trust share may be limited or zero in accordance with the Closed-Set Invariance Theorem: $\sum_{c \in C} t_c = \left(\frac{1 - \alpha}{\alpha}\right) \sum_{h \in H} t_h \sum_{c \in C} C'_{hc}$."*
- **Evaluation Status & Pass Criterion:** *"Diagnostic test. If $T_{C, \text{EW}} \approx T_{C, \text{Vanilla}}$, this confirms theoretical invariance rather than implementation failure."*

**Actual Empirical Findings Across Scenarios:**
- **Scenario 2 Standard:** Vanilla $T_C = 0.0850$, EW $T_C = 0.0889$, $\Delta = +0.0039$ ($+4.53\%$). The reported increase is **not statistically significant** ($t = +1.472, p = 0.158$). In this configuration, $T_{C, \text{EW}} \approx T_{C, \text{Vanilla}}$ held.
- **Scenario 2 Extended:** Vanilla $T_C = 0.0539$, EW $T_C = 0.0611$, $\Delta = +0.0073$ ($+13.50\%$). This represents a **statistically significant increase** in colluder trust ($t = +3.944, p = 8.70 \times 10^{-4}$).
- **Scenario 4 (Bridge Probability Sweep $q$):**
  - $q = 0.05$: Statistically significant increase ($+25.89\%, p = 3.66 \times 10^{-10}$).
  - $q = 0.10$: Statistically significant increase ($+17.34\%, p = 2.96 \times 10^{-11}$).
  - $q = 0.20$: Statistically significant increase ($+6.92\%, p = 1.95 \times 10^{-8}$).
  - $q = 0.40$: Small statistically significant reduction ($-1.90\%, p = 1.25 \times 10^{-4}$).
- **Scenario 6 (Receipt Grinding, H-1 Refutation):** Statistically significant increase in colluder trust ($+13.38\%, p = 1.06 \times 10^{-3}$ standard; $+17.92\%, p = 8.55 \times 10^{-5}$ extended). Preregistered Hypothesis H-1 was **formally refuted**.

> [!IMPORTANT]
> **Explaining the Direction of Change:**  
> The stationary flow identity $T_C = \frac{1-\alpha}{\alpha} F_{H \to C}$ relates coalition trust to incoming flow, but it **does not predict the direction of change** (whether $T_C$ increases, decreases, or stays constant under algorithmic modifications). Explaining why colluder trust share increased in S2 Extended, S4 ($q \le 0.20$), and S6 would require evaluating per-trial trust-weighted flow $F_{H \to C} = \sum_{h \in H} t_h \sum_{c \in C} C'_{hc}$, which was not recorded in the benchmark output files. While denominator compression on honest bridge nodes is a hypothesized mechanism, it was not directly tested against serialized per-trial transition matrices. Furthermore, because per-trial $F_{H \to C}$ was not saved, H-3 did **not** verify the numerical flow identity against empirical flow; it served only as a diagnostic check observing that EW did not suppress closed coalitions.

#### Verification of Closure Assumptions Against the Benchmark Generator
Inspecting [`experiments/phase8_2_benchmark.py`](file:///d:/pki_casestudy/experiments/phase8_2_benchmark.py):
- **Scenario 2, Scenario 4, and Scenario 6:** Colluders strictly execute internal transactions among themselves and never generate transactions to honest peers ($C'_{c, h} = 0$). Pre-trust is concentrated entirely on supernodes ($p_c = 0$). Colluders exchange internal transactions, so no colluder row dangles. Therefore, **closure assumptions hold structurally** in these three scenarios.
- **Scenario 3 (Leaky Coalition):** Colluders actively transact with honest peers with probability $0.20$ (`lines 550-556`). This generates non-zero outgoing transition probability $C'_{c, h} > 0$, explicitly violating Assumption 1. Therefore, the Closed-Set Flow Identity is **structurally inapplicable** to Scenario 3.
- **Scenario 7 (Dispute Manipulation):** Colluders submit negative dispute receipts (`rating = -1.00`) against honest peers, but negative ratings produce zero positive edge weight ($A_{c, h} = 0$). Honest peers never transact with colluders, so incoming flow is identically zero ($F_{H \to C} = 0$). The identity predicts $T_C = 0$, matching the degenerate empirical zero.

---

## 7.2 Why Leaky Coalitions are Vulnerable
When colluders leak trust by interacting with honest nodes (Scenario 3), closed-set invariance breaks down. 
- Colluders' internal receipts receive Tier 1 discounting ($\mu_{\text{unverified}} = 0.10$).
- Colluders' downloads from honest nodes involve authentic chunk verification, awarding honest nodes Tier 3 credit ($\gamma_{\text{ev}} = 1.00$).

The transition probability from colluders back to honest nodes is hypothesized to be magnified relative to internal circulation (**hypothesized mechanism, not tested on per-trial matrices**). Trust drains out of the coalition into the honest community, producing a **$40.88\%$ to $41.50\%$ reduction** in colluder trust ($p < 10^{-18}, |d_z| > 7.5$).

---

## 7.3 Simulation Oracles and Decentralized Evidence Portability Gap
A critical threat to external validity is the distinction between local simulator oracles and portable decentralized evidence:
1. **Global Delivery Key Pool ($\mathcal{D}_{\text{sim}}$):** In the benchmark harness, verified delivery keys are collected globally in an in-memory set across all simulated clients. In an untrusted decentralized P2P network, an observing third-party peer evaluating edge $A \to B$ does not possess direct local verification of $B$'s chunk delivery to $A$.
2. **Third-Party Verifiability Gap:** Because the frozen `BilateralReceipt` does not carry raw chunks or Merkle inclusion proofs, observing peers cannot verify delivery integrity off-the-wire. Without portable zero-knowledge service proofs or independent delivery challenges, third-party receipts default to Tier 1 or Tier 2. The observed $+11.4\%$ to $+12.7\%$ gain for honest uploaders represents an **upper bound under complete local evidence knowledge**.
3. **Canonical Evidence Journal ($\mathcal{L}_{\text{sim}}$):** In a real mesh, peers maintain local journals ($\mathcal{L}_{\text{local}}$) and reconcile entries via gossip. Network partitions or asynchronous gossip could lead to temporary divergence in local trust views.

---

## 7.4 Computational Runtime Scaling
Under extreme receipt grinding (Scenario 6 extended scale, 152,000 journal receipts), EW-EigenTrust execution time increased from $1.81\text{ ms}$ (Vanilla) to $166.32\text{ ms}$ ($92\times$ overhead). This overhead arises from iterating over thousands of raw journal entries and performing hash-set lookups during matrix assembly. In production deployments, edge aggregation must be indexed incrementally rather than computed via full journal scans.

---

## 7.5 Local-Only Baseline Comparison
Under receipt grinding, Local-Only assigned **$99.32\%$ (standard) and $99.73\%$ (extended)** of all trust to colluders. Because Local-Only simply sums raw interaction scores without pre-trusted teleportation or global spectral normalization, colluders generating high volumes of mutual ratings completely overwhelm the honest community. This demonstrates that in the evaluated benchmark configuration, naive direct rating aggregation without pre-trusted anchoring completely collapsed under receipt grinding, whereas spectral propagation with pre-trusted anchors constrained colluder trust share (though other defense architectures remain unexamined).

---

## 8. Relevance to Both Application Domains

### 8.1 P2P File-Sharing Systems (Empirically Validated Domain)
In P2P file sharing, the protocol provides concrete, verified security properties:
- **Attributable Fault Detection:** Servers delivering corrupted file chunks are detected via Merkle inclusion contradiction proofs, enabling $O(1)$ arbiter verification without downloading full payloads.
- **Economic Admission Barrier:** PoW admission ($O(2^d)$ hash trials) eliminates zero-cost identity generation.
- **Provider Protection:** Dedicated asymmetric seeders serving high volumes of chunks receive Tier 3 verified evidence, elevating their global trust score ($+11\%$ to $+13\%$) without requiring reciprocal return downloads.
- **Collusion Bounds:** Colluders attempting to construct artificial reputation rings are dampened by $>40\%$ if they attempt to interact with or download from honest peers.

### 8.2 P2P Social-Networking Platforms (Conceptual Application Domain)
The four-layer architecture provides a direct conceptual foundation for decentralized social networks:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│             P2P SOCIAL NETWORKING MAPPING (CONCEPTUAL EXTENSION)             │
├─────────────────────────┬────────────────────────────────────────────────────┤
│ Protocol Component      │ Social Network Mapping & Operational Semantics     │
├─────────────────────────┼────────────────────────────────────────────────────┤
│ Layer 1: Identity & PoW │ User profiles anchored in did:peer-style keys.     │
│                         │ Hashcash PoW throttles automated bot creation.     │
├─────────────────────────┼────────────────────────────────────────────────────┤
│ Layer 2: Web-of-Trust   │ Mutual cryptographic key cross-signing (e.g., peer │
│                         │ keysigning) establishes bounded trust paths.       │
│                         │ Note: subjective social endorsements are Layer 3  │
│                         │ reputation inputs, not Layer 2 cross-certs.        │
├─────────────────────────┼────────────────────────────────────────────────────┤
│ Layer 3: EW-EigenTrust  │ Signed interaction attestations build reputation.  │
│                         │ Subjective disputes handle spam/abuse reports.     │
├─────────────────────────┼────────────────────────────────────────────────────┤
│ Layer 4: Revocation &   │ Compromised user accounts are recovered via social │
│ Shamir Secret Recovery  │ guardians holding Shamir secret shares, enforcing  │
│                         │ mandatory post-recovery key rotation.              │
└─────────────────────────┴────────────────────────────────────────────────────┘
```

**Cryptographic Primitive Differentiation:**
- **PKI Cross-Certificates vs. Social Follows:** A PKI cross-certificate is a signed delegation statement binding a public key to an identity with explicit validity constraints. A social "follow" is an unauthenticated pub/sub subscription pointer.
- **PKI Cross-Certificates vs. Social Endorsements:** An endorsement is a subjective reputation claim (Layer 3) that does not certify cryptographic key ownership unless a separate, specified cryptographic certification mechanism exists.
- **Bilateral Receipts vs. Message Attestation:** A `BilateralReceipt` is a co-signed transactional receipt certifying bilateral agreement. A message attestation is a unilateral author signature verifying post origin.

**Missing Mechanisms Requiring Future Specification and Testing:**
To validate P2P social networking empirically, the following mechanisms must be specified and evaluated:
1. Unilateral directed graph follow/unfollow churn dynamics.
2. Content feed ranking and spam filtering algorithms without Merkle chunk trees.
3. Bot-net follow-farming attack models in power-law social topologies (e.g., Stanford SNAP datasets).
4. Social guardian threshold recovery under guardian churn and latency.

---

## 9. Final Claim and Scope Audit Table

| Claim or Contribution | Supporting Implementation / Experiment | Evidence Status | Limitations & Boundary Conditions | Recommended Report Wording |
| :--- | :--- | :---: | :--- | :--- |
| **C-01: Identity Admission Barrier** | `src/layer1_identity.py`, verified in `tests/test_trust_framework.py`. | **TEST-SUITE VERIFIED** | Imposes computational cost $O(2^d)$; does not prevent hardware-scale attackers. | *"Imposes verifiable computational cost to eliminate zero-cost identity generation; not absolute Sybil prevention."* |
| **C-02: Bounded Web-of-Trust Paths** | `src/layer2_mesh_pki.py`, verified in `tests/test_trust_framework.py`. | **TEST-SUITE VERIFIED** | Trust path decay limits reachability; relies on supernode backbone connectivity. | *"Enforces bounded multi-hop trust path validation with intermediate-vertex disjointness filtering up to 4 hops."* |
| **C-03: Merkle Fault Contradiction Proofs** | `src/layer3_eigentrust.py`, verified in `tests/test_trust_framework.py`. | **TEST-SUITE VERIFIED** | Proves attributable delivery of inconsistent data via authentic manifest, leaf proof, and server envelope; does not prove subjective malicious intent. | *"Cryptographically proves attributable delivery of inconsistent data via server-signed envelope and authentic leaf proof."* |
| **C-04: Leaky Collusion Suppression** | `results/phase8_2_statistical_comparison.csv`, Scenario 3 (20 seeds, 2 scales). | **EMPIRICALLY VALIDATED (SIMULATOR)** | Benefit strictly requires colluders to interact with and rate honest peers. | *"Suppresses colluder trust share by $>40\%$ in leaky coalitions where colluders interact with honest peers."* |
| **C-05: Closed-Set Flow Identity** | Mathematical derivation; observed in Scenarios 2, 4, 6 (20 seeds). | **THEORETICAL DERIVATION & EMPIRICAL OBSERVATION** | Closed-Set Flow Identity ($T_C = \frac{1-\alpha}{\alpha} F_{H \to C}$). No reduction observed under closed collusion; colluders gained trust in S2 Extended, S4 ($q \le 0.20$), and S6. | *"Does NOT defend against closed colluding coalitions under fixed incoming bridge flow; aggregate trust is dictated by external flow."* |
| **C-06: Honest Asymmetric Provider Preservation** | `results/phase8_2_raw_results.json`, Scenario 8 (20 seeds, 2 scales). | **EMPIRICALLY VALIDATED (SIMULATOR)** | Verified delivery (Tier 3) relies on global simulator key pool in benchmark. | *"Preserves and enhances honest asymmetric uploader trust (+11% to +13%) under verified delivery weighting in simulation."* |
| **C-07: Threshold Revocation and Key Recovery** | `src/layer4_recovery.py`, verified in `tests/test_trust_framework.py`. | **TEST-SUITE VERIFIED** | Requires $m$-of-$n$ supernode threshold authorization and honest guardian authorization. Not BFT consensus. | *"Enforces threshold quorum authorization and secret-shared recovery with mandatory key rotation."* |
| **C-08: Dual-Domain Validation (P2P + Social)** | Case-study topic scope vs. `experiments/` implementation. | **QUALIFIED** | P2P file sharing is empirically validated; social networking is an architectural conceptual extension. | *"Empirically evaluated on P2P file sharing; social networking applicability is presented as a conceptual extension."* |

---

## 10. Research Contributions, Limitations, and Future Work

### 10.1 Primary Research Contributions
1. **End-to-End Four-Layer PKI Architecture:** Implemented and test-suite verified a CA-free trust architecture spanning identity admission, Web-of-Trust mesh PKI, evidence-weighted reputation, and threshold recovery.
2. **Attributable Fault Contradiction Proofs:** Formulated attributable delivery contradiction proofs using server-signed delivery envelopes and authentic Merkle proofs, enabling $O(1)$ arbiter verification of inconsistent delivery.
3. **Rigorous Empirical Characterization of EW-EigenTrust:** Conducted a preregistered, paired-seed empirical benchmark demonstrating that while asymmetric evidence discounting slashes leaky collusion by $>40\%$, concave edge ceilings did not suppress closed coalitions in the evaluated configurations, in accordance with the closed-set flow identity bounding aggregate coalition trust by external incoming flow.
4. **Transparent Negative Results Reporting:** Documented the refutation of preregistered Hypothesis H-1 under receipt grinding, establishing a clear scientific benchmark for future reputation research.

### 10.2 Documented Limitations
1. **Closed-Set Flow Identity Vulnerability:** Inability to suppress closed coalitions that successfully attract honest incoming bridge transactions under low-to-moderate bridge connectivity ($q \le 0.20$); a minor reduction ($-1.90\%$) only emerged under dense bridge connectivity ($q = 0.40$).
2. **Decentralized Evidence Portability Gap:** Reliance on local delivery verification keys, requiring third-party verifiable delivery proofs for full decentralization.
3. **Journal Processing Overhead:** Linear iteration over large evidence journals introduces computational overhead ($92\times$ under extreme grinding).
4. **Network Scale:** Empirical simulations were bounded to 20–50 nodes; asymptotic scalability to thousands of dynamic peers remains unvalidated.

### 10.3 Directions for Future Work
1. **Spectral Bridge-Cut Analysis:** Developing spectral graph partitioning techniques to detect and discount incoming bridge edges $C'_{hc}$ entering closed clusters.
2. **Zero-Knowledge Delivery Proofs:** Incorporating zero-knowledge contingent service proofs to allow third-party peers to independently verify Tier 3 delivery without downloading payloads.
3. **Empirical Evaluation of Social Graphs:** Implementing a dedicated social network simulation harness utilizing real-world social network topologies (e.g., Stanford SNAP datasets) to measure Web-of-Trust spam suppression.

---

## 11. Bibliographic References

1. **Back, A. (2002).** "Hashcash - A Denial of Service Counter-Measure." *Technical Report*, [hashcash.org](http://www.hashcash.org/papers/hashcash.pdf).
2. **Hardman, D., Curran, S., & Curren, S. (Eds.), with the DIF Peer DID Method Community. (2021).** "Peer DID Method Specification." *Decentralized Identity Foundation (DIF) Community Specification Draft*. Available at: [https://identity.foundation/peer-did-method-spec/](https://identity.foundation/peer-did-method-spec/).  
   *(Verification Note: The specification frontmatter at the primary URL `https://identity.foundation/peer-did-method-spec/` lists three distinct editors: Daniel Hardman of Provenant Inc, Stephen Curran of Cloud Compass Computing Inc, and Sam Curren of Indicio / Decentralized Identity Foundation, independently verifying that Stephen Curran and Sam Curren are two distinct individuals).*
3. **Kamvar, S. D., Schlosser, M. T., & Garcia-Molina, H. (2003).** "The EigenTrust algorithm for reputation management in P2P networks." *Proceedings of the 12th International World Wide Web Conference (WWW '03)*, pp. 640–651. DOI: [10.1145/775152.775242](https://doi.org/10.1145/775152.775242).
4. **Merkle, R. C. (1980).** "Protocols for public key cryptosystems." *1980 IEEE Symposium on Security and Privacy*, Oakland, CA, pp. 122–134. DOI: [10.1109/SP.1980.10006](https://doi.org/10.1109/SP.1980.10006).
5. **Shamir, A. (1979).** "How to share a secret." *Communications of the ACM*, 22(11), pp. 612–613. DOI: [10.1145/359168.359176](https://doi.org/10.1145/359168.359176).
6. **W3C Decentralized Identifier Working Group. (2022).** "Decentralized Identifiers (DIDs) v1.0: Core Architecture, Data Model, and Representations." *W3C Recommendation 19 July 2022*. Available at: [https://www.w3.org/TR/did-core/](https://www.w3.org/TR/did-core/).
7. **Zimmermann, P. (1995).** *The Official PGP User's Guide.* MIT Press, Cambridge, MA. ISBN: 978-0262740173.
