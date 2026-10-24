# Final Scope and Claims Audit: PKI-Based Trust Management Framework

**Document Identifier:** `FINAL_SCOPE_AND_CLAIMS_AUDIT`  
**Date:** October 9, 2026  
**Author:** Independent Statistical and Scope Integrity Auditor  
**Target Documents:**  
- [`FINAL_CASE_STUDY_SYNTHESIS.md`](file:///d:/pki_casestudy/FINAL_CASE_STUDY_SYNTHESIS.md)  
- [`PHASE8_2_BENCHMARK_REPORT.md`](file:///d:/pki_casestudy/PHASE8_2_BENCHMARK_REPORT.md)  
- [`PHASE8_3_REPRODUCIBILITY_AUDIT.md`](file:///d:/pki_casestudy/PHASE8_3_REPRODUCIBILITY_AUDIT.md)  
- [`NOVEL_TRUST_ALGORITHM_DESIGN_V1_8.md`](file:///d:/pki_casestudy/NOVEL_TRUST_ALGORITHM_DESIGN_V1_8.md)  

---

## 1. Executive Purpose

This document provides a focused, audit-grade reconciliation between the original project scope, the implemented software artifacts, the empirical benchmark outcomes, and the claims made in research reports. Its objective is to prevent academic overclaiming, eliminate scope ambiguity, and establish an unassailable evidentiary baseline for project defense.

---

## 2. Topic Scope Reconciliation: Three-Tier Categorization

The formal case-study topic is:
> **"PKI-Based Trust Management for Peer-to-Peer File-Sharing and Social Networking Platforms."**

The table below reconciles this title against actual project deliverables:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    SCOPE RECONCILIATION & VALIDATION STATUS                  │
├───────────────────┬────────────────────────────────────────┬─────────────────┤
│ Scope Tier        │ Technical Domain & Artifacts           │ Evidence Status │
├───────────────────┼────────────────────────────────────────┼─────────────────┤
│ Tier 1: Shared    │ Layers 1–4: Ed25519, did:peer, PoW,    │ FULLY VERIFIED  │
│ Infrastructure    │ Web-of-Trust mesh, EW-EigenTrust v1.8, │ Code: src/      │
│                   │ CRR quorum, Shamir key recovery.       │ Tests: 75/75 OK │
├───────────────────┼────────────────────────────────────────┼─────────────────┤
│ Tier 2: Evaluated │ P2P File Sharing: Content manifests,   │ FULLY VERIFIED  │
│ Application       │ Merkle trees, chunk delivery proofs,   │ Benchmarks:     │
│                   │ poisoning, collusion, receipt grinding.│ 1,140 trials    │
├───────────────────┼────────────────────────────────────────┼─────────────────┤
│ Tier 3: Extension │ P2P Social Networking: Profile DIDs,   │ CONCEPTUAL ONLY │
│ Application       │ follower endorsements, message stamps, │ No dataset,     │
│                   │ social guardian recovery.              │ no experiments. │
└───────────────────┴────────────────────────────────────────┴─────────────────┘
```

### Mandatory Scope Boundary Guidelines:
1. **Never assert that social networking was empirically validated:** The codebase contains zero social graph simulations, zero follower datasets, and zero social interaction benchmarks.
2. **Present social networking strictly as a conceptual extension:** Frame it as an architectural mapping demonstrating how the shared four-layer PKI infrastructure generalizes from chunk delivery to social attestations.
3. **Do not abbreviate the project title:** Retain the full title while clearly explaining the distinction between the implemented evaluation (file sharing) and the conceptual extension (social networking).

---

## 3. Comprehensive Claim-by-Claim Audit Table

| # | Specific Claim Made in Documentation | Evidentiary Basis in Code / Data | Verification Status | Required Qualification or Wording Correction |
| :-: | :--- | :--- | :---: | :--- |
| **1** | *"PoW provides Sybil resistance."* | `src/layer1_identity.py`: Hashcash PoW ($d \ge 8$). Verification $O(1)$. | **QUALIFIED** | Imposes verifiable computational cost ($O(2^d)$ hash trials) that eliminates zero-cost identity generation, but does NOT prevent determined, hardware-rich attackers. |
| **2** | *"Web-of-Trust bounds transitive trust propagation."* | `src/layer2_mesh_pki.py`: Dijkstra trust path bounded at $L \le 4$ with decay $\beta=0.90$. | **VERIFIED** | Enforces strict path-length cutoff and multiplicative attenuation, preventing unbounded transitivity in mesh networks. |
| **3** | *"Arbiter cryptographically proves malicious server poisoning."* | `src/layer3_eigentrust.py`: `FaultEvidenceRecord` binds server signature to authentic Merkle proof contradiction. | **VERIFIED** | Cryptographically proves attributable delivery of inconsistent data; does not prove subjective malicious intent (e.g., benign storage fault vs deliberate poisoning). |
| **4** | *"EW-EigenTrust suppresses colluding coalitions by >40%."* | `experiments/phase8_2_benchmark.py`, Scenario 3: $-40.88\%$ (std), $-41.50\%$ (ext), $p < 10^{-18}, d_z \le -7.68$. | **VERIFIED** | Strictly conditioned on **leaky coalitions** where colluders interact with and rate honest peers. Internal Tier 1 discounting ($\mu=0.10$) drains trust into honest community. |
| **5** | *"Concave edge ceilings ($\Phi_{\text{edge}}$) bound closed collusive coalitions."* | `experiments/phase8_2_benchmark.py`, Scenarios 2 & 6: Colluders gained $+4.5\%$ to $+17.9\%$ trust ($p \le 0.001$). | **REFUTED** | Closed-Set Invariance Theorem: row-normalization cancels symmetric internal edge compression. Edge ceilings alone CANNOT defend closed coalitions with incoming bridges. |
| **6** | *"Preregistered Hypothesis H-1 (Grinding Suppression) passed."* | Empirical data from Scenario 6: $T_C$ increased from $9.2\%$ to $10.5\%$ (std) and $5.6\%$ to $6.6\%$ (ext). | **REFUTED** | Preregistered Hypothesis H-1 was **formally refuted**. The report accepted the negative result honestly; parameters were not tuned to force a pass. |
| **7** | *"Dedicated honest uploaders are preserved without suppression."* | `experiments/phase8_2_benchmark.py`, Scenario 8: Uploader trust $+11.43\%$ (std) and $+12.74\%$ (ext), retention ratio $\ge 1.11$. | **VERIFIED** | Verified downloads receive Tier 3 credit ($\gamma=1.00$), elevating dedicated seeders over unverified or reciprocal peers. |
| **8** | *"Complete rejection of replayed receipts and zero false revocations."* | `src/layer3_eigentrust.py` and Scenario 7: Nonce caching; subjective disputes trigger $\gamma_{\text{dispute}}$, not CRR eviction. | **VERIFIED** | Replay rejections $100.00\%$; false accusations = 0; false revocations = 0 across all 20 paired seeds. |
| **9** | *"Local-Only baseline is sufficient for P2P networks."* | Scenario 6: Local-Only assigned $99.32\%$ (std) and $99.73\%$ (ext) trust to colluders under receipt grinding. | **REFUTED** | Local direct rating aggregation completely collapses under grinding attacks; global spectral propagation with pre-trusted anchors is essential. |
| **10** | *"Tier 3 evidence is fully decentralized in production."* | Simulator centralizes delivery keys in `verified_delivery_keys` across all clients globally. | **QUALIFIED** | Simulation represents an upper bound. Decentralized production networks require third-party verifiable delivery proofs or bilateral counter-signatures. |

---

## 4. Specific Wording That Must Be Weakened or Avoided

To prevent criticism during peer review or project examination, the following phrases must be strictly avoided or replaced:

1. **Avoid:** *"EW-EigenTrust is a collusion-resistant trust algorithm."*  
   **Use Instead:** *"EW-EigenTrust significantly reduces collusion in leaky networks ($>40\%$ suppression), but is mathematically bounded by the Closed-Set Invariance Theorem under strictly closed coalitions."*
2. **Avoid:** *"The framework eliminates Sybil attacks via Proof-of-Work."*  
   **Use Instead:** *"The framework eliminates zero-cost identity creation by imposing a verifiable computational proof-of-work admission barrier."*
3. **Avoid:** *"The protocol was experimentally evaluated on social networks and file sharing."*  
   **Use Instead:** *"The protocol was empirically validated on P2P file sharing; its application to social networking is formulated as an architectural conceptual extension."*
4. **Avoid:** *"The algorithm is ready for production deployment."*  
   **Use Instead:** *"The algorithm demonstrates clear empirical advantages in leaky topologies and provider preservation, but requires zero-knowledge delivery proofs and incremental indexing before production deployment."*

---

## 5. Audit Conclusion

The scope and claims audit confirms that:
- All implemented components in `src/` are fully verified by automated tests (75/75 passing).
- All empirical claims in file sharing are backed by reproducible, paired-seed data.
- Negative findings (Hypothesis H-1 refutation, closed coalition invariance) are transparently acknowledged.
- The boundary between implemented file sharing and conceptual social networking is clearly delineated.

```
PHASE8_4_STATUS: PASS
```
