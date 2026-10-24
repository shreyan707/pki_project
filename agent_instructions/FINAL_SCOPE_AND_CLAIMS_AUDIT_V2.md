# Final Scope and Claims Audit: PKI-Based Trust Management Framework (v2.0-AUDITED)

**Document Version:** 2.0.0-AUDITED  
**Date:** October 9, 2026  
**Auditor:** Independent Statistical and Scope Integrity Auditor  
**Audit Reference:** [`PHASE8_5_FINAL_CONSISTENCY_REPORT.md`](file:///d:/pki_casestudy/PHASE8_5_FINAL_CONSISTENCY_REPORT.md)  
**Target Documents:**  
- [`FINAL_CASE_STUDY_SYNTHESIS_V2.md`](file:///d:/pki_casestudy/FINAL_CASE_STUDY_SYNTHESIS_V2.md)  
- [`PHASE8_2_BENCHMARK_REPORT.md`](file:///d:/pki_casestudy/PHASE8_2_BENCHMARK_REPORT.md)  
- [`PHASE8_3_REPRODUCIBILITY_AUDIT.md`](file:///d:/pki_casestudy/PHASE8_3_REPRODUCIBILITY_AUDIT.md)  
- [`NOVEL_TRUST_ALGORITHM_DESIGN_V1_8.md`](file:///d:/pki_casestudy/NOVEL_TRUST_ALGORITHM_DESIGN_V1_8.md)  

---

## 1. Executive Purpose

This document provides a submission-grade reconciliation between the original project scope, the implemented software artifacts, the empirical benchmark outcomes, and the claims made in research reports. Its objective is to prevent academic overclaiming, eliminate scope ambiguity, and establish an unassailable evidentiary baseline for project examination and defense.

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

### 2.1 Differentiation of Social Networking Primitives
To prevent conceptual conflation, social networking primitives are explicitly differentiated from P2P file-sharing constructs:
- **PKI Cross-Certificates vs Social Follows:** A PKI cross-certificate is a signed delegation statement binding a public key to an identity with explicit validity constraints. A social "follow" is an unauthenticated pub/sub subscription pointer.
- **PKI Cross-Certificates vs Social Endorsements:** An endorsement is a subjective reputation claim that does not certify cryptographic key ownership.
- **Bilateral Receipts vs Message Attestation:** A `BilateralReceipt` is a co-signed transactional receipt proving bilateral service delivery. A message attestation is a unilateral author signature verifying post origin.

### 2.2 Missing Mechanisms Requiring Future Empirical Specification
To validate P2P social networking empirically, the following mechanisms must be specified and evaluated in future work:
1. Dynamic follow/unfollow churn on scale-free directed graphs.
2. Feed ranking and spam filtering algorithms operating on unstructured posts rather than Merkle chunk trees.
3. Collusion and follow-farming botnet modeling on empirical social graph topologies (e.g., Stanford SNAP datasets).
4. Social guardian threshold secret recovery dynamics under guardian churn and network latency.

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
| **9** | *"Scenario 7 demonstrates dispute manipulation resistance."* | Scenario 7: Colluders had 0 incoming edges from honest peers ($C_{hc} = 0$). Stationary trust was 0 by topology. | **DEGENERATE** | Zero colluder trust is structurally degenerate because colluders received no incoming flow. Validates that disputes do not cause false revocations, but does not test dispute defense against active bridge edges. |
| **10** | *"Local-Only baseline is sufficient for P2P networks."* | Scenario 6: Local-Only assigned $99.32\%$ (std) and $99.73\%$ (ext) trust to colluders under receipt grinding. | **REFUTED** | Local direct rating aggregation completely collapses under grinding attacks; global spectral propagation with pre-trusted anchors is essential. |
| **11** | *"Tier 3 evidence is fully decentralized in production."* | Simulator centralizes delivery keys in `verified_delivery_keys` across all clients globally. | **QUALIFIED** | Simulation represents an upper bound. Decentralized production networks require third-party verifiable delivery proofs or bilateral counter-signatures. |

---

## 4. Specific Wording That Must Be Weakened or Avoided

To prevent criticism during peer review or project examination, the following phrases must be strictly avoided or replaced:

1. **Avoid:** *"EW-EigenTrust is a collusion-resistant trust algorithm."*  
   **Use Instead:** *"EW-EigenTrust significantly reduces collusion in leaky networks ($>40\%$ suppression), but is mathematically bounded by the Closed-Set Invariance Theorem under strictly closed coalitions."*
2. **Avoid:** *"The framework eliminates Sybil attacks via Proof-of-Work."*  
   **Use Instead:** *"The framework eliminates zero-cost identity creation by imposing a verifiable computational proof-of-work admission barrier."*
3. **Avoid:** *"The protocol was experimentally evaluated on social networks and file sharing."*  
   **Use Instead:** *"The protocol was empirically validated on P2P file sharing; its application to social networking is formulated as an architectural conceptual extension."*
4. **Avoid:** *"Scenario 7 proves that dispute manipulation is neutralized."*  
   **Use Instead:** *"Scenario 7 confirms that subjective negative disputes do not trigger false CRR revocations; colluder trust was zero due to topological disconnection (structurally degenerate baseline)."*
5. **Avoid:** *"The algorithm is ready for production deployment."*  
   **Use Instead:** *"The algorithm demonstrates clear empirical advantages in leaky topologies and provider preservation, but requires zero-knowledge delivery proofs and incremental indexing before production deployment."*

---

## 5. Audit Conclusion

The scope and claims audit confirms that:
- All implemented components in `src/` are fully verified by automated tests (75/75 passing).
- All empirical claims in file sharing are backed by reproducible, paired-seed data.
- Negative findings (Hypothesis H-1 refutation, closed coalition invariance) and degenerate metrics (Scenario 7) are transparently acknowledged.
- The boundary between implemented file sharing and conceptual social networking is clearly delineated.

```
PHASE8_5_STATUS: PASS
```
