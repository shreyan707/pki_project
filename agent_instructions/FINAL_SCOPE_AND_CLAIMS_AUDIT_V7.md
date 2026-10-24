# Final Scope and Claims Audit: PKI-Based Trust Management (v7.0-FINAL-FREEZE)

**Document Version:** 7.0.0-FINAL-FREEZE  
**Date:** October 9, 2026  
**Auditor / Author:** Candidate Shreyan Nayak (23BKT0039)  
**Audit Reference:** [`PHASE8_10_REGRESSION_AND_FREEZE_REPORT.md`](file:///d:/pki_casestudy/PHASE8_10_REGRESSION_AND_FREEZE_REPORT.md)  
**Target Synthesis Document:** [`FINAL_CASE_STUDY_SYNTHESIS_V7.md`](file:///d:/pki_casestudy/FINAL_CASE_STUDY_SYNTHESIS_V7.md)  
**Evaluated Prior Reports:**  
- [`PHASE8_2_BENCHMARK_REPORT.md`](file:///d:/pki_casestudy/PHASE8_2_BENCHMARK_REPORT.md)  
- [`PHASE8_3_REPRODUCIBILITY_AUDIT.md`](file:///d:/pki_casestudy/PHASE8_3_REPRODUCIBILITY_AUDIT.md)  
- [`PHASE8_5_FINAL_CONSISTENCY_REPORT.md`](file:///d:/pki_casestudy/PHASE8_5_FINAL_CONSISTENCY_REPORT.md)  
- [`PHASE8_6_SUBMISSION_READINESS_REPORT.md`](file:///d:/pki_casestudy/PHASE8_6_SUBMISSION_READINESS_REPORT.md)  
- [`PHASE8_7_FINAL_FREEZE_REPORT.md`](file:///d:/pki_casestudy/PHASE8_7_FINAL_FREEZE_REPORT.md)  
- [`PHASE8_8_FINAL_FREEZE_REPORT.md`](file:///d:/pki_casestudy/PHASE8_8_FINAL_FREEZE_REPORT.md)  
- [`PHASE8_9_INTEGRITY_AND_FREEZE_REPORT.md`](file:///d:/pki_casestudy/PHASE8_9_INTEGRITY_AND_FREEZE_REPORT.md)  
- [`PHASE8_10_REGRESSION_AND_FREEZE_REPORT.md`](file:///d:/pki_casestudy/PHASE8_10_REGRESSION_AND_FREEZE_REPORT.md)  

---

## 1. Audit Purpose and Scope Boundaries

The purpose of this audit is to enforce strict evidentiary verification, remove over-generalized claims, and establish defensible boundaries between:
1. **Implemented, Tested, and Empirically Evaluated Functionality** (P2P File-Sharing System).
2. **Specified and Architecturally Mapped Extensions** (P2P Social-Networking Platforms).
3. **Automated Software Test Verification vs. Formal Mathematical Proof / Production Deployment**.

This audit verifies claims against executable source code under `src/`, 75 passing unit/regression tests under `tests/` (logged to `tests_scratch/unittest_phase8_9.log`), preregistered hypotheses in [`PHASE8_2_PREREGISTRATION.md`](file:///d:/pki_casestudy/PHASE8_2_PREREGISTRATION.md), and empirical data files [`results/phase8_2_statistical_comparison.csv`](file:///d:/pki_casestudy/results/phase8_2_statistical_comparison.csv), [`results/phase8_2_summary.csv`](file:///d:/pki_casestudy/results/phase8_2_summary.csv), and [`results/phase8_2_raw_results.json`](file:///d:/pki_casestudy/results/phase8_2_raw_results.json).

---

## 2. Topic Scope Reconciliation: Three-Tier Categorization

The formal case-study topic is:
> **"PKI-Based Trust Management for Peer-to-Peer File-Sharing and Social Networking Platforms."**

The table below reconciles this title against actual project deliverables across three explicit tiers:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    SCOPE RECONCILIATION & VALIDATION STATUS                  │
├──────────────────────┬───────────────────────────────────────┬───────────────┤
│ Scope Tier           │ Technical Domain & Artifacts          │ Status        │
├──────────────────────┼───────────────────────────────────────┼───────────────┤
│ Tier 1: Shared       │ Layers 1–4: Ed25519, did:peer-style,  │ TEST-SUITE    │
│ Infrastructure       │ PoW, Web-of-Trust mesh PKI,           │ VERIFIED      │
│                      │ EW-EigenTrust v1.8, CRR quorum,       │ (75 tests     │
│                      │ Shamir key recovery.                  │ passing)      │
├──────────────────────┼───────────────────────────────────────┼───────────────┤
│ Tier 2: Evaluated    │ P2P File Sharing: Content manifests,  │ EMPIRICALLY   │
│ Application          │ Merkle trees, chunk delivery proofs,  │ VALIDATED     │
│                      │ poisoning, collusion, receipt         │ (Simulator:   │
│                      │ grinding benchmarks.                  │ 1,140 trials) │
├──────────────────────┼───────────────────────────────────────┼───────────────┤
│ Tier 3: Extension    │ P2P Social Networking: Profile DIDs,  │ CONCEPTUAL    │
│ Application          │ follower endorsements, message stamps,│ ONLY          │
│                      │ social guardian recovery.             │ (No dataset,  │
│                      │                                       │ no trials)    │
└──────────────────────┴───────────────────────────────────────┴───────────────┘
```

### 2.1 Differentiation of Social Networking and Transactional Primitives
To prevent conceptual conflation, social networking primitives are explicitly differentiated from transactional file-sharing primitives:
- **PKI Cross-Certificates vs. Social Follows:** A PKI cross-certificate is a signed delegation statement binding a public key to an identity with explicit validity constraints. A social "follow" is an unauthenticated pub/sub subscription pointer.
- **PKI Cross-Certificates vs. Social Endorsements:** An endorsement is a subjective reputation claim (Layer 3) that does not certify cryptographic key ownership unless a separate, specified cryptographic certification mechanism exists.
- **Bilateral Receipts vs. Message Attestation:** A `BilateralReceipt` is a co-signed transactional receipt certifying bilateral agreement. A message attestation is a unilateral author signature verifying post origin.
- **Bilateral Receipts vs. Portable Delivery Proofs:** A `BilateralReceipt` contains `tx_id` and `merkle_root` references; without raw chunks or inclusion proofs, it does not provide a standalone third-party verifiable delivery proof.
- **`did:peer` Implementation vs. Specification Syntax:** The Python reference implementation emits custom simulation strings formatted as `did:peer:2.Ez<64-hex>`. It does NOT implement DIF numalgo 2 multicodec/multibase encoding, nor does it use purpose code `V` for verification keys.
- **Lifecycle State Machine:** The state machine starts in `UNKNOWN`, progresses to `ACTIVE` upon PoW admission, transitions to `SUSPECTED` on unverified suspicion or certified fault, and requires 3-of-5 supernode quorum signatures for CRR eviction. Timeout fallback reverts to `SUSPECTED`, never directly to `ACTIVE`.
- **Threshold Authorization vs. Distributed Consensus:** The 3-of-5 supernode quorum mechanism enforces threshold signature collection for administrative revocation proposals. It does not constitute Byzantine fault-tolerant consensus.

### 2.2 Missing Mechanisms Requiring Future Empirical Specification
To validate P2P social networking empirically, the following mechanisms must be specified and evaluated:
1. Dynamic follow/unfollow churn on scale-free directed graphs.
2. Feed ranking and spam filtering algorithms operating on unstructured posts rather than Merkle chunk trees.
3. Collusion and follow-farming botnet modeling on empirical social graph topologies (e.g., Stanford SNAP datasets).
4. Social guardian threshold secret recovery dynamics under guardian churn and network latency.

---

## 3. Claim-by-Claim Verification Audit

The following table audits every technical claim advanced across the case study synthesis:

| # | Specific Claim Made in Documentation | Evidentiary Basis in Code / Data | Verification Status | Required Qualification or Wording Correction |
| :-: | :--- | :--- | :---: | :--- |
| **1** | *"PoW provides Sybil resistance."* | `src/layer1_identity.py`: Hashcash PoW ($d \ge 8$). Verification $O(1)$. | **QUALIFIED** | Imposes verifiable computational cost ($O(2^d)$ hash trials) that eliminates zero-cost identity generation, but does NOT prevent determined, hardware-rich attackers. |
| **2** | *"Web-of-Trust bounds transitive trust propagation."* | `src/layer2_mesh_pki.py`: DFS vertex-disjoint trust paths bounded at $k \le 4$. | **TEST-SUITE VERIFIED** | Enforces strict path-length cutoff ($k \le 4$) and intermediate-vertex disjointness filtering, preventing unbounded transitivity in mesh networks. |
| **3** | *"Arbiter cryptographically proves malicious server poisoning."* | `FaultEvidenceRecord` generation/verification in `src/layer3_eigentrust.py`; quorum voting and CRR in `src/layer4_recovery.py`. | **TEST-SUITE VERIFIED** | Cryptographically proves attributable delivery of inconsistent data via authentic manifest, leaf proof, and server-signed envelope; does not prove subjective malicious intent (e.g., bit rot vs deliberate poisoning). |
| **4** | *"EW-EigenTrust suppresses colluding coalitions by >40%."* | `results/phase8_2_statistical_comparison.csv`, Scenario 3: $-40.88\%$ (std), $-41.50\%$ (ext), $p = 1.44 \times 10^{-18}$ (std), $p = 1.07 \times 10^{-21}$ (ext), $d_z \le -7.68$. | **EMPIRICALLY VALIDATED (SIMULATOR)** | Strictly conditioned on **leaky coalitions** where colluders interact with and rate honest peers. Internal Tier 1 discounting ($\mu=0.10$) drains trust into honest community. (Note: reported $p$-values are uncorrected for multiple testing across the 9 scenarios). |
| **5** | *"Concave edge ceilings ($\Phi_{\text{edge}}$) bound closed collusive coalitions."* | `results/phase8_2_statistical_comparison.csv`, Scenarios 2, 4, 6. | **THEORETICAL DERIVATION & EMPIRICAL OBSERVATION** | Closed-Set Flow Identity ($T_C = \frac{1-\alpha}{\alpha} F_{H \to C}$). Under closed coalitions, symmetric internal edge ceilings do not reduce colluder trust. Empirically, EW produced no statistically significant reduction in S2 Standard ($+4.53\%, p = 0.158$) and statistically significant increases in S2 Extended ($+13.50\%, p = 8.70 \times 10^{-4}$), S4 at bridge probabilities $q \in \{0.05, 0.10, 0.20\}$ ($+6.9\%$ to $+25.9\%, p < 2 \times 10^{-8}$), and S6 ($+13.38\%, p = 1.06 \times 10^{-3}$ std; $+17.92\%, p = 8.55 \times 10^{-5}$ ext); a small reduction occurred only at $q = 0.40$ ($-1.90\%, p = 1.25 \times 10^{-4}$). The flow identity does not explain the direction of change; explaining direction would require per-trial $F_{H \to C}$, which was not recorded. |
| **6** | *"Preregistered Hypothesis H-1 (Grinding Suppression) passed."* | Empirical data from Scenario 6: $T_C$ increased from $9.2\%$ to $10.5\%$ (std, $p = 1.06 \times 10^{-3}$) and $5.6\%$ to $6.6\%$ (ext, $p = 8.55 \times 10^{-5}$). | **REFUTED** | Preregistered Hypothesis H-1 was **formally refuted**. The report accepted the negative result honestly; parameters were not tuned to force a pass. Preregistered hypotheses H-2 and H-4 passed; H-3 was a diagnostic reality check; hypotheses H-5 through H-7 never existed in preregistration. |
| **7** | *"Dedicated honest uploaders are preserved without suppression."* | `results/phase8_2_raw_results.json`, Scenario 8: Uploader trust $t_{\text{uploader}}$ increased from $0.1574$ to $0.1754$ ($+11.43\%$, $t = +54.177, p = 2.74 \times 10^{-22}$) in standard, and $0.1584$ to $0.1786$ ($+12.74\%$, $t = +73.490, p = 8.57 \times 10^{-25}$) in extended. Retention ratio $\ge 1.11$. | **EMPIRICALLY VALIDATED (SIMULATOR)** | Verified downloads receive Tier 3 credit ($\gamma=1.00$), elevating dedicated seeders over unverified peers (H-2 Confirmed). Depends on simulator key oracle for third-party recognition. |
| **8** | *"Complete rejection of replayed receipts and zero false revocations."* | `src/layer3_eigentrust.py` and Scenario 7: Nonce caching; subjective disputes trigger $\gamma_{\text{dispute}}$, not CRR eviction. | **TEST-SUITE VERIFIED** | Replay rejections $100.00\%$; false accusations = 0; false revocations = 0 across all 20 paired seeds. |
| **9** | *"Scenario 7 demonstrates dispute manipulation resistance."* | Scenario 7 in `experiments/phase8_2_benchmark.py:707-746`: Colluders had 0 incoming edges from honest peers ($C'_{hc} = 0$). Stationary trust was 0 by topology. | **DEGENERATE** | Zero colluder trust is structurally degenerate because colluders received no incoming flow. Validates that disputes do not cause false revocations, but does not test dispute defense against active bridge edges. Holds under both $\mathbf{p}$ and $1/n$ fallback rules. |
| **10** | *"Local-Only baseline is sufficient for P2P networks."* | Scenario 6: Local-Only assigned $99.32\%$ (std) and $99.73\%$ (ext) trust to colluders under receipt grinding. | **REFUTED** | Local direct rating aggregation completely collapsed under grinding attacks in this evaluation; global spectral propagation with pre-trusted anchors provided substantial dampening compared to local aggregation, though the necessity of spectral methods in general is not proven. |
| **11** | *"Tier 3 evidence is fully decentralized in production."* | Simulator centralizes delivery keys in `verified_delivery_keys` across all clients globally. | **QUALIFIED** | Simulation represents an upper bound. Decentralized production networks require third-party verifiable delivery proofs or bilateral counter-signatures. |
| **12** | *"Implementation adopts official DIF did:peer Method 2 and W3C DID Core."* | `src/layer1_identity.py:68`: `did:peer:2.Ez{public_key_hex}` string formatting. | **NOT COMPLIANT / SIMULATION FORMAT** | Code emits custom simulation strings; uses purpose code `E` (encryption) for Ed25519 signing keys, raw 64-hex rather than multicodec + multibase base58btc, and does not implement DIF Method 2 resolution or full W3C DID Core document schemas. |

---

## 4. Specific Wording Guidelines and Guardrails

To maintain rigorous standards and avoid unsupported assertions, the following phrases must be strictly observed:

1. **Avoid:** *"EW-EigenTrust is a collusion-resistant trust algorithm."*  
   **Use Instead:** *"EW-EigenTrust significantly reduces collusion in leaky networks ($>40\%$ suppression), but is characterized by the Closed-Set Flow Identity ($T_C = \frac{1-\alpha}{\alpha} F_{H \to C}$) under closed coalitions; internal edge ceilings did not reduce closed coalition trust in benchmark trials and produced statistically significant increases across S2 Extended, S4 ($q \le 0.20$), and S6."*
2. **Avoid:** *"The framework eliminates Sybil attacks via Proof-of-Work."*  
   **Use Instead:** *"The framework eliminates zero-cost identity creation by imposing a verifiable computational proof-of-work admission barrier."*
3. **Avoid:** *"The protocol was experimentally evaluated on social networks and file sharing."*  
   **Use Instead:** *"The protocol was empirically validated on P2P file sharing; its application to social networking is formulated as an architectural conceptual extension."*
4. **Avoid:** *"Scenario 7 proves that dispute manipulation is neutralized."*  
   **Use Instead:** *"Scenario 7 confirms that subjective negative disputes do not trigger false CRR revocations; colluder trust was zero due to topological disconnection (structurally degenerate baseline)."*
5. **Avoid:** *"The algorithm is production frozen and fully formally verified."*  
   **Use Instead:** *"The algorithm is specification-frozen and test-suite verified across 75 automated unit and regression tests in Python simulation."*
6. **Avoid:** *"Bilateral receipts provide portable third-party proofs of delivery."*  
   **Use Instead:** *"Bilateral receipts provide co-signed transaction records; because raw chunks and Merkle inclusion proofs are omitted, independent third-party verification requires out-of-band delivery proofs or simulator oracles."*
7. **Avoid:** *"Edge ceilings and evidence discounting are mathematically powerless against closed coalitions."*  
   **Use Instead:** *"Internal edge ceilings and symmetric evidence discounting alone cannot reduce stationary coalition trust when the coalition is strictly closed and incoming trust-weighted flow remains fixed."*
8. **Avoid:** *"Supernodes execute threshold consensus."*  
   **Use Instead:** *"Supernodes execute $m$-of-$n$ threshold signature collection for CRR authorization without dynamic leader election."*
9. **Avoid:** *"Adopts official DIF did:peer Method 2 conforming to W3C DID Core."*  
   **Use Instead:** *"Emits did:peer-style identifiers (`did:peer:2.Ez<64-hex>`); non-compliant with DIF numalgo 2 specification."*

---

## 5. Summary Audit Conclusion

The scope and claims audit confirms that [`FINAL_CASE_STUDY_SYNTHESIS_V7.md`](file:///d:/pki_casestudy/FINAL_CASE_STUDY_SYNTHESIS_V7.md):
- Strictly respects the boundary between implemented file sharing and conceptual social networking.
- Distinguishes automated unit and regression tests (75 passing tests) from formal mathematical proofs and production deployments.
- Accurately reports negative empirical findings (Hypothesis H-1 refutation, closed-set flow identity behavior) without selective omissions.
- Eliminates non-compliant standards claims regarding DIF `did:peer` Method 2 and W3C DID Core.
- Uses exact $p$-values, handles zero-variance paired comparisons as undefined, reports actual uploader metrics for Scenario 8, and applies mathematically precise flow identity language throughout.
