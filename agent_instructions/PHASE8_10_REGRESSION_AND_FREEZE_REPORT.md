# Phase 8.10 Regression Check and Final Freeze Report

**Phase:** 8.10 (V5→V6 Regression Check and Final Patch V7)  
**Date:** October 9, 2026  
**Auditor / Candidate:** Shreyan Nayak (23BKT0039)  
**Target Deliverables Created:**  
- [`FINAL_CASE_STUDY_SYNTHESIS_V7.md`](file:///d:/pki_casestudy/FINAL_CASE_STUDY_SYNTHESIS_V7.md)  
- [`FINAL_SCOPE_AND_CLAIMS_AUDIT_V7.md`](file:///d:/pki_casestudy/FINAL_SCOPE_AND_CLAIMS_AUDIT_V7.md)  
- [`PHASE8_10_REGRESSION_AND_FREEZE_REPORT.md`](file:///d:/pki_casestudy/PHASE8_10_REGRESSION_AND_FREEZE_REPORT.md)  

---

## Executive Summary

Phase 8.10 conducts a comprehensive regression analysis comparing V5 and V6 deliverables, verifies implementation and design semantics against `src/` and frozen specifications, resolves mathematical and topological nuances of the Closed-Set Flow Identity, handles zero-variance paired statistical comparisons properly, restores actual uploader metrics for Scenario 8, restores unrequested omissions in the claims audit, and provides independent verification of bibliographic records from primary sources.

All formulas across documentation now match the frozen design specification [`NOVEL_TRUST_ALGORITHM_DESIGN_V1_8.md`](file:///d:/pki_casestudy/NOVEL_TRUST_ALGORITHM_DESIGN_V1_8.md) and Python implementation `src/layer3_eigentrust.py` bit-for-bit. Preregistered Hypothesis H-3 and all closed-coalition findings are accurately grounded without over-claiming empirical flow verification.

---

## 1. V5→V6 Regression Analysis

A programmatic diff was generated between V5 and V6 for both the Synthesis and Audit documents using Python's `difflib`:
```powershell
python -c "import difflib; l1 = open('FINAL_CASE_STUDY_SYNTHESIS_V5.md', encoding='utf-8').readlines(); l2 = open('FINAL_CASE_STUDY_SYNTHESIS_V6.md', encoding='utf-8').readlines(); open('tests_scratch/diff_synthesis_v5_v6.diff', 'w', encoding='utf-8').writelines(difflib.unified_diff(l1, l2))"
python -c "import difflib; l1 = open('FINAL_SCOPE_AND_CLAIMS_AUDIT_V5.md', encoding='utf-8').readlines(); l2 = open('FINAL_SCOPE_AND_CLAIMS_AUDIT_V6.md', encoding='utf-8').readlines(); open('tests_scratch/diff_audit_v5_v6.diff', 'w', encoding='utf-8').writelines(difflib.unified_diff(l1, l2))"
```

### Classification of Material Changes

| Document | Section / Hunk | Description of Change | Classification | Resolution in V7 |
| :--- | :--- | :--- | :---: | :--- |
| **Synthesis** | §5 Test Table | Replaced conceptual layer counts (10/12/26/14/13) with real test class counts (14 in `test_ew_eigentrust.py`, 61 in `test_trust_framework.py`). | **Requested (8.9 B2)** | Preserved. |
| **Synthesis** | §6.1 Table | Renamed bridge parameter $p=0.xx$ to bridge probability $q=0.xx$. | **Requested (8.9 B4)** | Preserved. |
| **Synthesis** | §6.1 Table | Quoted exact $p$-values and replaced blanket "$\le 0.001$" statements. | **Requested (8.9 B3)** | Preserved. |
| **Synthesis** | §7.1 Heading | Renamed "Closed-Set Invariance Theorem" to "Closed-Set Flow Identity". | **Requested (8.9 B4)** | Preserved. |
| **Synthesis** | §7.1 Flow Eq. | Trust vector dimension typed as $\mathbf{t} \in \mathbb{R}$ (typo in V6). | **Unrequested Typo** | Corrected to $\mathbf{t} \in \mathbb{R}^n$. |
| **Synthesis** | §7.1 Explanation | Removed "consistent with flow identity" as causal reason for trust increase; noted unsaved per-trial flow. | **Requested (8.9 B4)** | Preserved & elaborated. |
| **Synthesis** | §3.1, §4 L1 | Clarified `did:peer:2.Ez` non-compliance with DIF numalgo 2; removed W3C DID Core conformance claims. | **Requested (8.9 B5)** | Preserved. |
| **Synthesis** | End of Doc | Removed `Completion Gate Decision` and `PHASE8_x_STATUS` lines. | **Requested (8.9 B6)** | Preserved. |
| **Audit** | §2 Scope Table | Replaced three-tier categorization table with a truncated two-row table. | **Unrequested Omission** | **Restored in V7** (Three-tier scope table restored). |
| **Audit** | §2.1 Primitives | Omitted detailed differentiation of social networking vs transactional primitives (7 bullets). | **Unrequested Omission** | **Restored in V7** (All 7 primitive distinctions restored). |
| **Audit** | §2.2 Missing Mech | Omitted 4 missing mechanisms for future social network empirical validation. | **Unrequested Omission** | **Restored in V7** (All 4 missing mechanisms restored). |
| **Audit** | §3 Claims Table | Updated claims with exact $p$-values, DIF non-compliance, and flow identity wording. | **Requested (8.9 B3-B5)** | Preserved. |
| **Audit** | End of Doc | Removed `Completion Gate Decision` and `PHASE8_x_STATUS` lines. | **Requested (8.9 B6)** | Preserved. |

---

## 2. Verification of Implementation and Design Semantics

To ensure complete fidelity to the frozen design and executable source code, [`src/layer3_eigentrust.py`](file:///d:/pki_casestudy/src/layer3_eigentrust.py), [`src/layer2_mesh_pki.py`](file:///d:/pki_casestudy/src/layer2_mesh_pki.py), and [`NOVEL_TRUST_ALGORITHM_DESIGN_V1_8.md`](file:///d:/pki_casestudy/NOVEL_TRUST_ALGORITHM_DESIGN_V1_8.md) were inspected.

### Source-versus-Design Semantic Verification

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 SEMANTIC VERIFICATION AUDIT MATRIX                                     │
├─────────────────────┬─────────────────────────────────┬───────────────────────────────┬────────────────┤
│ Feature Semantics   │ Frozen Design Spec (v1.8)       │ Python Source Code (src/)     │ Status         │
├─────────────────────┼─────────────────────────────────┼───────────────────────────────┼────────────────┤
│ 1. Edge Ceiling     │ K_max * tanh(lambda_sat*E/K_max)│ phi_val = k_max * math.tanh(  │ EXACT MATCH    │
│    Phi_edge         │ (Section 6.1, line 144)         │   (lambda_sat*e_pos)/k_max)   │ (tanh verified;│
│                     │                                 │ (layer3_eigentrust.py:1178)   │ algebraic rmvd)│
├─────────────────────┼─────────────────────────────────┼───────────────────────────────┼────────────────┤
│ 2. Dispute Penalty  │ max(0.0, 1.0 - 2*N_neg/         │ gamma_dispute = max(0.0,      │ EXACT MATCH    │
│    gamma_dispute    │   (N_pos + 1.0))                │   1.0 - (2.0*n_neg_count /    │ (Linear ratio; │
│                     │ (Section 6.3, line 162)         │   (n_pos_count + 1.0)))       │ kappa removed) │
│                     │                                 │ (layer3_eigentrust.py:1177)   │                │
├─────────────────────┼─────────────────────────────────┼───────────────────────────────┼────────────────┤
│ 3. Certified Fault  │ Zeroes INCOMING edges to        │ dst in certified_fault_accused│ EXACT MATCH    │
│    Nullification    │ accused peer (A_ij = 0.0);      │   A[i, j] = 0.0; continue     │ (Incoming only;│
│                     │ outbound ratings decay.         │ (layer3_eigentrust.py:1115-17)│ outbound decay)│
│                     │ (Section 1.1, line 17; L357-64) │                               │                │
├─────────────────────┼─────────────────────────────────┼───────────────────────────────┼────────────────┤
│ 4. Evidence Tiers   │ Tier 3: 1.00 (4-tuple key)      │ Tier 3: gamma_ev = 1.00       │ EXACT MATCH    │
│    and Weights      │ Tier 2: 0.25 (manifest root)    │ Tier 2: gamma_ev = 0.25       │ (Default       │
│                     │ Tier 1: 0.10 (unindexed)        │ Tier 1: gamma_ev = 0.10       │ weights match) │
│                     │ (Section 6.2, lines 154-159)    │ (layer3_eigentrust.py:1144-49)│                │
├─────────────────────┼─────────────────────────────────┼───────────────────────────────┼────────────────┤
│ 5. Dangling Node    │ Falls back to restart vector p  │ C_prime[i, :] = p             │ EXACT MATCH    │
│    Fallback Rule    │ (C'_i,: = p)                    │ (layer3_eigentrust.py:1218)   │ (Fallback to p;│
│                     │ (Section 8.2, line 465)         │                               │ breaks closure)│
├─────────────────────┼─────────────────────────────────┼───────────────────────────────┼────────────────┤
│ 6. Layer 2 Cross-   │ PKI_V2_CROSSCERT payload format;│ CrossCertificate signed bytes;│ EXACT MATCH    │
│    Certificate      │ bounded path trust product;     │ DFS k <= 4 disjoint filtering;│ (No beta^k;    │
│    Semantics        │ k <= 4 hops.                    │ trust = prod(c.trust_weight)  │ vertex disjoint│
│                     │ (PROTOCOL_SPEC:141-155)         │ (layer2_mesh_pki.py:25,168-205│ DFS verified)  │
└─────────────────────┴─────────────────────────────────┴───────────────────────────────┴────────────────┘
```

#### Detailed Source Excerpts

1. **Edge Transformation $\Phi_{\text{edge}}$ (`src/layer3_eigentrust.py:1178`):**
   ```python
   phi_val = k_max * math.tanh((lambda_sat * e_pos) / k_max)
   ```
   *Correction in V7:* Replaced older algebraic draft formula $K_{\max} \cdot \frac{E}{E + \lambda}$ with the authoritative hyperbolic tangent formulation.

2. **Dispute Penalty $\gamma_{\text{dispute}}$ (`src/layer3_eigentrust.py:1177`):**
   ```python
   gamma_dispute = max(0.0, 1.0 - (2.0 * n_neg_count / (n_pos_count + 1.0)))
   ```
   *Correction in V7:* Replaced draft formula $1/(1 + \kappa N)$ with the exact bounded linear ratio implemented and specified in v1.8.

3. **Certified-Fault Nullification (`src/layer3_eigentrust.py:1115-1117`):**
   ```python
   if is_cert_fault or is_revoking or is_cert_susp:
       A[i, j] = 0.0
       continue
   ```
   Here, `dst` is index `j`. The check zeroes incoming edges to the accused peer ($A_{ij} = 0$). Outgoing ratings ($A_{ji}$) from the accused peer are not zeroed by this block, allowing existing ratings to decay naturally while preventing incoming reputation harvesting.

4. **Evidence Tiers (`src/layer3_eigentrust.py:1144-1149`):**
   ```python
   if (src, dst, m_root, tx_id) in delivery_keys:
       gamma_ev = 1.00  # Tier 3: Local Verified Delivery
   elif m_root and m_root in manifest_roots:
       gamma_ev = mu_referenced  # Tier 2: Manifest Referenced (0.25)
   else:
       gamma_ev = mu_unverified  # Tier 1: Unindexed Receipt (0.10)
   ```

5. **Dangling-Node Fallback (`src/layer3_eigentrust.py:1218`):**
   ```python
   for i in range(n):
       row_total = np.sum(S_prime[i, :])
       if row_total > 0:
           C_prime[i, :] = S_prime[i, :] / row_total
       else:
           C_prime[i, :] = p  # Dangling row fallback
   ```
   *Crucial Mathematical Insight:* The restart vector $\mathbf{p}$ allocates positive weight $p_s = 1/|S|$ to honest supernodes $s \in S \subseteq H$, and zero weight $p_c = 0$ to colluders $c \in C$. If a colluder dangles, its transition row becomes $\mathbf{p}$, which directs non-zero transition probability to honest peers ($C'_{c, s} > 0$). This **violates coalition closure** ($C'_{c, h} = 0$). Therefore, dangling colluder rows break closure; the Closed-Set Flow Identity holds strictly when no coalition node dangles.

6. **Layer 2 Cross-Certificate Semantics (`src/layer2_mesh_pki.py:25-27, 201-205`):**
   ```python
   def payload_bytes(self) -> bytes:
       data = f"PKI_V2_CROSSCERT:{self.issuer_did}:{self.subject_did}:{self.trust_weight:.4f}:{self.issued_at}:{self.expires_at}"
       return data.encode("utf-8")
   ```
   ```python
   def get_path_trust(path: List[CrossCertificate]) -> float:
       val = 1.0
       for c in path:
           val *= c.trust_weight
       return val
   ```
   Path discovery uses depth-first search (DFS) with a maximum hop limit $k \le 4$, filtered to guarantee strict intermediate-vertex disjointness. Cumulative path trust is the direct product of cross-certificate weights.

---

## 3. Mathematical Analysis and Scenario Grounding

### Dimensionality Correction
Corrected trust vector dimensionality from typo $\mathbf{t} \in \mathbb{R}$ to $\mathbf{t} \in \mathbb{R}^n$.

### Hypothesis H-3 Definition and Pass Criterion
Quoted verbatim from [`PHASE8_2_PREREGISTRATION.md`](file:///d:/pki_casestudy/PHASE8_2_PREREGISTRATION.md) (§6):
> **Hypothesis H-3 (Closed Coalition Invariance Reality Check)**  
> - **Statement:** In a closed coalition with fixed honest bridge flow (Scenario 2), the reduction in colluder trust share may be limited or zero in accordance with the Closed-Set Invariance Theorem:  
>   $$\sum_{c \in C} t_c = \left(\frac{1 - \alpha}{\alpha}\right) \sum_{h \in H} t_h \sum_{c \in C} C'_{hc}$$  
> - **Evaluation Status:** Diagnostic test. If $T_{C, \text{EW}} \approx T_{C, \text{Vanilla}}$, this confirms theoretical invariance rather than implementation failure.

### Empirical Data and Reality Check
- **Scenario 2 Standard:** Vanilla $T_C = 0.0850$, EW $T_C = 0.0889$, $\Delta = +0.0039$ ($+4.53\%$). The paired $t$-test yielded $t = +1.472, p = 0.158$. The difference is **not statistically significant** ($p > 0.05$); $T_{C, \text{EW}} \approx T_{C, \text{Vanilla}}$ held.
- **Scenario 2 Extended:** Vanilla $T_C = 0.0539$, EW $T_C = 0.0611$, $\Delta = +0.0073$ ($+13.50\%$). The paired $t$-test yielded $t = +3.944, p = 8.70 \times 10^{-4}$, representing a **statistically significant increase** in colluder trust.
- **Limitation on Flow Verification:** Because per-trial trust-weighted flow $F_{H \to C}$ was not saved to disk during the benchmark execution, H-3 did **not** numerically verify the flow identity against empirical transition flow. It served only as a diagnostic reality check observing that EW did not reduce closed coalition trust.

### Closed-Coalition Findings by Scenario
1. **Scenario 2 Standard:** Reported increase ($+4.53\%$) is **not statistically significant** ($p = 0.158$).
2. **Scenario 2 Extended:** **Statistically significant increase** in colluder trust ($+13.50\%, p = 8.70 \times 10^{-4}$).
3. **Scenario 4 (Bridge Probability Sweep $q$):**
   - $q = 0.05$: Statistically significant increase ($+25.89\%, p = 3.66 \times 10^{-10}$).
   - $q = 0.10$: Statistically significant increase ($+17.34\%, p = 2.96 \times 10^{-11}$).
   - $q = 0.20$: Statistically significant increase ($+6.92\%, p = 1.95 \times 10^{-8}$).
   - $q = 0.40$: Small statistically significant reduction ($-1.90\%, p = 1.25 \times 10^{-4}$).
4. **Scenario 6 (Receipt Grinding):** **Statistically significant increase** in colluder trust ($+13.38\%, p = 1.06 \times 10^{-3}$ standard; $+17.92\%, p = 8.55 \times 10^{-5}$ extended). Preregistered Hypothesis H-1 was formally refuted.

### Topological Closure Verification in Benchmark Generator
Inspecting [`experiments/phase8_2_benchmark.py`](file:///d:/pki_casestudy/experiments/phase8_2_benchmark.py):
- **Scenarios 2, 4, and 6:** Colluders execute strictly internal positive transactions among themselves; colluders generate zero outgoing transactions to honest peers ($C'_{c, h} = 0$); pre-trust is zero on colluders ($p_c = 0$); internal transactions ensure no colluder row is dangling. Therefore, **closure assumptions hold structurally**.
- **Scenario 3 (Leaky Coalition):** Colluders actively download chunks from honest peers with probability $0.20$ (`lines 550-556`). This creates outgoing transition probability $C'_{c, h} > 0$, explicitly violating Assumption 1. Therefore, the Closed-Set Flow Identity is **structurally inapplicable** to Scenario 3.
- **Scenario 7 (Dispute Manipulation):** Honest peers never download from colluders ($F_{H \to C} = 0$). The identity predicts $T_C = 0$, matching the degenerate empirical zero.

---

## 4. Reconcile File Integrity and Statistics

### Comprehensive File Inventory: Bytes, Characters, and Hashes

Measured using Python `os.stat`, `len(text)`, and `hashlib.sha256`:
```powershell
python -c "import hashlib; files = ['PROTOCOL_SPEC.md', 'SECURITY_MODEL.md', 'NOVEL_TRUST_ALGORITHM_DESIGN_V1_8.md', 'FINAL_CASE_STUDY_SYNTHESIS_V3.md', 'FINAL_SCOPE_AND_CLAIMS_AUDIT_V3.md', 'FINAL_CASE_STUDY_SYNTHESIS_V4.md', 'FINAL_SCOPE_AND_CLAIMS_AUDIT_V4.md', 'FINAL_CASE_STUDY_SYNTHESIS_V5.md', 'FINAL_SCOPE_AND_CLAIMS_AUDIT_V5.md', 'FINAL_CASE_STUDY_SYNTHESIS_V6.md', 'FINAL_SCOPE_AND_CLAIMS_AUDIT_V6.md', 'FINAL_CASE_STUDY_SYNTHESIS_V7.md', 'FINAL_SCOPE_AND_CLAIMS_AUDIT_V7.md']; print('\n'.join([f'{f}: {len(open(f, \"rb\").read())} bytes, {len(open(f, encoding=\"utf-8\").read())} chars, {hashlib.sha256(open(f, \"rb\").read()).hexdigest().upper()}' for f in files]))"
```

| File Path | Byte Size | Character Count | SHA-256 Checksum |
| :--- | :---: | :---: | :---: |
| [`PROTOCOL_SPEC.md`](file:///d:/pki_casestudy/PROTOCOL_SPEC.md) | 59,444 | 59,442 | `A23F3F63D314F17A580CB0E2C7326850A590D76984230F885B5AA74D7FE988FB` |
| [`SECURITY_MODEL.md`](file:///d:/pki_casestudy/SECURITY_MODEL.md) | 20,390 | 20,388 | `D2D0C4BA8F5E08698C5C9E917B7A28B15FAAE14E943B7F816A79BA9C261F9B53` |
| [`NOVEL_TRUST_ALGORITHM_DESIGN_V1_8.md`](file:///d:/pki_casestudy/NOVEL_TRUST_ALGORITHM_DESIGN_V1_8.md) | 32,508 | 32,492 | `6454E7394DAE9654B912BE7F8E1BBC8F41E0AB16102DCAC950295FC32B74FD17` |
| [`FINAL_CASE_STUDY_SYNTHESIS_V3.md`](file:///d:/pki_casestudy/FINAL_CASE_STUDY_SYNTHESIS_V3.md) | 45,096 | 42,900 | `CAC5AEF3B66773CEA416E622A148A27BC577FE8B6A33C75A036214B8C103FA79` |
| [`FINAL_SCOPE_AND_CLAIMS_AUDIT_V3.md`](file:///d:/pki_casestudy/FINAL_SCOPE_AND_CLAIMS_AUDIT_V3.md) | 13,140 | 12,094 | `EC730A488ADAAB431AAA33CC7F13BE5249AF11A0899087E31BA0389091375F84` |
| [`FINAL_CASE_STUDY_SYNTHESIS_V4.md`](file:///d:/pki_casestudy/FINAL_CASE_STUDY_SYNTHESIS_V4.md) | 47,899 | 45,691 | `B6F338C816E3C47456A55B3E3DFB5BF8DCC940A95BF5E602E57D496CCFA0EC0A` |
| [`FINAL_SCOPE_AND_CLAIMS_AUDIT_V4.md`](file:///d:/pki_casestudy/FINAL_SCOPE_AND_CLAIMS_AUDIT_V4.md) | 14,568 | 13,522 | `8B36471E088FDF72312C16CEC9C82533641B9392A7B1115036FBA1201F944D76` |
| [`FINAL_CASE_STUDY_SYNTHESIS_V5.md`](file:///d:/pki_casestudy/FINAL_CASE_STUDY_SYNTHESIS_V5.md) | 51,052 | 48,849 | `7C62C5FB20BD876494CAF01B97366FD8B5454DEFE1C71E3FCFAF41895EE20EC1` |
| [`FINAL_SCOPE_AND_CLAIMS_AUDIT_V5.md`](file:///d:/pki_casestudy/FINAL_SCOPE_AND_CLAIMS_AUDIT_V5.md) | 15,720 | 14,674 | `6654F4DA9A135B72887D94B3BC25FB59604386278D99638826E0E83347D5E076` |
| [`FINAL_CASE_STUDY_SYNTHESIS_V6.md`](file:///d:/pki_casestudy/FINAL_CASE_STUDY_SYNTHESIS_V6.md) | 51,635 | 49,431 | `D332DC71FAB77F86407319D06CA4DE87CD76BA47E5969FB0E7EC3C754C62F03A` |
| [`FINAL_SCOPE_AND_CLAIMS_AUDIT_V6.md`](file:///d:/pki_casestudy/FINAL_SCOPE_AND_CLAIMS_AUDIT_V6.md) | 12,701 | 12,701 | `574600412C6E9372B615380EAF0EAA6B8D2CC69FCA88A2C01BD08757A5441C2D` |
| [`FINAL_CASE_STUDY_SYNTHESIS_V7.md`](file:///d:/pki_casestudy/FINAL_CASE_STUDY_SYNTHESIS_V7.md) | 56,978 | 54,775 | `39A17A505688DF1DD316F474B288793F900ABDD226DA0CAEB9A421EAA3A9CBFB` |
| [`FINAL_SCOPE_AND_CLAIMS_AUDIT_V7.md`](file:///d:/pki_casestudy/FINAL_SCOPE_AND_CLAIMS_AUDIT_V7.md) | 17,875 | 16,805 | `F7FF9E2349B462B9D22D74F2CE61F772FCAE0BC75F2439C42BB04720B949DCC7` |

#### Resolution of Conflicting Records
1. **Phase 8.7 vs 8.8 Size Records:** In Phase 8.7 report, V4 synthesis was listed as 46,290 and audit as 13,878. Filesystem measurement shows V4 synthesis is 47,899 bytes (45,691 chars) and audit is 14,568 bytes (13,522 chars). The Phase 8.8 report updated the table to the true filesystem byte sizes. The file content and hash (`B6F3...` and `8B36...`) never changed.
2. **Phase 8.6 Hashes Origin:** Stated plainly: **The exact origin of the phantom hashes reported in Phase 8.6 (`C58B35A1...`, `CC2DA27D...`, `B531393A...`) remains unknown.** These strings never corresponded to any committed git revision or filesystem state of the frozen specs.

### Mechanical Number Verification Script Rerun
Reran [`tests_scratch/verify_numbers.py`](file:///d:/pki_casestudy/tests_scratch/verify_numbers.py):
```powershell
python tests_scratch/verify_numbers.py
```
**Output:**
```
Running mechanical check against results/phase8_2_statistical_comparison.csv...
Mechanical check complete: 133 checks executed. Mismatches found: 0
```
*Exact Cells Checked:* The script checks 19 rows corresponding to all scenario/scale pairs across 7 numerical columns: `vanilla_colluder_mean`, `ew_colluder_mean`, `absolute_difference`, `relative_difference_pct`, `paired_t_statistic`, `p_value`, and `cohens_dz`. All 133 cells match `results/phase8_2_statistical_comparison.csv` with zero mismatches.

### Zero-Variance Paired Comparisons and Scenario 8 Grounding
- **Zero-Variance Comparisons:** In Scenarios 1, 4 ($q=0.00$), 7, and 9, colluder trust is identically zero across all paired seeds. In `results/phase8_2_statistical_comparison.csv`, the script logged `t = 0.0, p = 1.0, dz = 0.0` due to a fallback block in `experiments/phase8_2_benchmark.py:986`. Mathematically, $s_d = 0$, so $t = \bar{d}/(s_d/\sqrt{n}) = 0/0$, which is **undefined**. In V7 §6.1, these test statistics are reported as **Undefined (zero variance)**.
- **Scenario 8 Actual Metric:** Scenario 8 evaluates honest asymmetric provider trust $t_{\text{uploader}}$ directly. In `results/phase8_2_raw_results.json`:
  - **Standard Scale (20 seeds):** Vanilla mean $0.1574$, EW mean $0.1754$, Diff $+0.0180$, Rel Change $+11.43\%$, Retention ratio $1.1143$, Paired $t$-stat $+54.177$, $p = 2.74 \times 10^{-22}$, Cohen's $d_z = +12.11$. (H-2 Confirmed).
  - **Extended Scale (20 seeds):** Vanilla mean $0.1584$, EW mean $0.1786$, Diff $+0.0202$, Rel Change $+12.74\%$, Retention ratio $1.1274$, Paired $t$-stat $+73.490$, $p = 8.57 \times 10^{-25}$, Cohen's $d_z = +16.43$. (H-2 Confirmed).
  These actual statistics are now presented directly in V7 §6.1.

### Automated Test Suite Execution
Executed full test suite via standard `unittest` discovery:
```powershell
python -m unittest discover -s tests -v
```
**Output Trace (Saved in `tests_scratch/unittest_phase8_9.log`):**
```
Ran 75 tests in 4.964s
OK
```
**Measured Breakdown by Module and Class:**
- `tests/test_ew_eigentrust.py`: Exactly **14 tests** across 6 test classes.
- `tests/test_trust_framework.py`: Exactly **61 tests** in class `TestPKITrustFramework`.
- **Total Discovered & Passing:** Exactly **75 tests**.

---

## 5. Bibliography and Primary Source Verification

### Decentralized Identity Foundation (DIF) `did:peer` Editors
- **Primary Source URL:** [`https://identity.foundation/peer-did-method-spec/`](https://identity.foundation/peer-did-method-spec/)
- **Retrieved Specification Frontmatter Excerpt:**
  ```markdown
  Editors:
  - Daniel Hardman, Provenant, Inc
  - Stephen Curran - Cloud Compass Computing Inc.
  - Sam Curren - Indicio / Decentralized Identity Foundation
  ```
- **Independent Verification Result:** Stephen Curran (Cloud Compass Computing Inc.) and Sam Curren (Indicio / DIF) are confirmed to be **two distinct individuals** from two different organizations serving as editors alongside Daniel Hardman.

---

## 6. Correction Log (V6 -> V7)

| # | Item / Section | V6 State | V7 Corrected State | Rationale / Evidence |
| :-: | :--- | :--- | :--- | :--- |
| **1** | $\Phi_{\text{edge}}$ Formula (§4 L3) | Stated older algebraic form $K_{\max} \cdot \frac{E}{E + \lambda}$. | Authoritative hyperbolic tangent: $K_{\max} \cdot \tanh(\lambda E / K_{\max})$. | Matches `src/layer3_eigentrust.py:1178` and `NOVEL_TRUST_ALGORITHM_DESIGN_V1_8.md:144`. |
| **2** | $\gamma_{\text{dispute}}$ Formula (§4 L3) | Stated draft formula $1 / (1 + \kappa N)$. | Exact bounded ratio: $\max(0.0, 1.0 - 2 N_{\text{neg}} / (N_{\text{pos}} + 1.0))$. | Matches `src/layer3_eigentrust.py:1177` and `NOVEL_TRUST_ALGORITHM_DESIGN_V1_8.md:162`. |
| **3** | Fault Nullification (§4 L3) | Claimed zeroed incoming and outgoing edges ($A_{ij} = 0, A_{ji} = 0$). | Zeroes incoming edges to accused peer ($A_{ij} = 0$ for $j = \text{accused}$); outbound edges decay. | Matches `src/layer3_eigentrust.py:1115-1117` and `NOVEL_TRUST_ALGORITHM_DESIGN_V1_8.md:17`. |
| **4** | Dangling Fallback & Closure (§4 L3, §7.1) | Claimed falling back to $\mathbf{p}$ preserves closure because $\sum_{c \in C} p_c = 0$. | Falling back to $\mathbf{p}$ directs transition flow to honest supernodes ($C'_{c, s} > 0$), **breaking closure**. | Correct mathematical analysis: closure requires no coalition node dangles. |
| **5** | Trust Dimensionality (§7.1) | $\mathbf{t} \in \mathbb{R}$ (typo). | $\mathbf{t} \in \mathbb{R}^n$. | Correct mathematical notation. |
| **6** | Zero-Variance Tests (§6.1) | Reported $t = 0.00, p = 1.000, d_z = 0.00$. | Reported as **Undefined (zero variance)**. | Mathematically $s_d = 0$, so $t = 0/0$ is undefined. |
| **7** | Scenario 8 Table (§6.1) | Reported colluder trust $0.0000$ with footnote. | Reported actual Asymmetric Uploader Trust $t_{\text{uploader}}$ ($+11.43\%$ std, $+12.74\%$ ext, $t > 54$). | Aligns table row with the actual evaluated metric and H-2. |
| **8** | Hypothesis H-3 Status (§7.1, Audit) | Implied H-3 verified the flow identity. | Quoted verbatim H-3; clarified H-3 was a diagnostic reality check and did not verify empirical flow (unsaved $F_{H \to C}$). | Precise empirical accounting. |
| **9** | Audit Scope Tiers (Audit §2) | Truncated to a 2-row boundary table. | Restored full three-tier scope table (Shared Infra, Evaluated App, Extension App). | Restores unrequested omission from V6. |
| **10** | Primitive Differentiations (Audit §2.1) | Omitted from V6. | Restored all 7 primitive distinctions (cross-certs vs follows, endorsements, receipts, state machine, etc.). | Restores unrequested omission from V6. |
| **11** | Missing Mechanisms (Audit §2.2) | Omitted from V6. | Restored all 4 missing social networking mechanisms. | Restores unrequested omission from V6. |
| **12** | Primary Source Bibliography (§11) | Narrative note without primary URL. | Included primary URL `https://identity.foundation/peer-did-method-spec/` and verbatim frontmatter excerpt. | Verifiable primary source documentation. |

---

## 7. Claim-by-Claim Verification Table

| Claim / Component | Supporting Code / Artifact | Verified This Phase? | Evidentiary Basis / Command Executed |
| :--- | :--- | :---: | :--- |
| **$\Phi_{\text{edge}}$ Hyperbolic Tangent** | `src/layer3_eigentrust.py:1178`, design spec L144 | **YES** | Inspected source code; verified exact formula `k_max * math.tanh((lambda_sat * e_pos) / k_max)`. |
| **$\gamma_{\text{dispute}}$ Linear Ratio** | `src/layer3_eigentrust.py:1177`, design spec L162 | **YES** | Inspected source code; verified exact formula `max(0.0, 1.0 - (2.0 * n_neg_count / (n_pos_count + 1.0)))`. |
| **Certified Fault Nullification Direction** | `src/layer3_eigentrust.py:1115-1117`, design spec L17 | **YES** | Inspected source code; verified destination check zeroes incoming edges ($A_{ij} = 0$). |
| **Dangling Fallback Breaks Closure** | `src/layer3_eigentrust.py:1218` | **YES** | Verified mathematically: $C'_{c, :} = \mathbf{p}$ assigns probability mass to honest supernodes ($p_s > 0$). |
| **Benchmark Statistical Numbers** | Section 6.1 master empirical table | **YES** | 133 numbers mechanically verified against CSV with 0 mismatches (`verify_numbers.py`). |
| **Scenario 8 Uploader Metric** | `results/phase8_2_raw_results.json` | **YES** | Extracted from raw JSON: $+11.43\%$ std ($t = +54.177$), $+12.74\%$ ext ($t = +73.490$). |
| **Zero-Variance Comparisons Undefined** | Mathematical derivation ($s_d = 0$) | **YES** | Verified indeterminate form $0/0$; updated S1, S4 ($q=0$), S7, S9 to Undefined. |
| **Preregistration Hypothesis Scope** | `PHASE8_2_PREREGISTRATION.md` | **YES** | Inspected preregistration document; confirmed exactly 4 hypotheses (H1–H4). |
| **Test Suite Execution (75 Tests)** | `tests/test_ew_eigentrust.py`, `tests/test_trust_framework.py` | **YES** | Full test suite executed (`Ran 75 tests in 4.964s, OK`); logged to disk. |
| **DIF `did:peer` Editors Independent Verification** | DIF Specification Frontmatter | **YES** | Fetched `https://identity.foundation/peer-did-method-spec/`; verified Hardman, Curran, Curren. |
| **Re-execution of Full Simulation Matrix** | `experiments/phase8_2_benchmark.py` (1,140 trials) | **NO** *(Constraint)* | Not re-executed in Phase 8.10 pursuant to strict freeze constraints ("no new experiments"). |
| **Formal Machine-Checked Proof** | Mathematical derivations in §7.1 | **NO** | Automated unit tests verify Python simulation; mathematical proofs are analytical, not machine-checked. |
| **Production Network Readiness** | Core implementation | **NO** | Code is a research discrete-event simulation harness, not a production P2P deployment. |

---

## 8. Remaining Research Limitations

1. **Closed-Set Flow Identity Limit:** Inability to suppress closed coalitions that successfully bridge into honest networks without leaking return edges under low-to-moderate bridge connectivity ($q \le 0.20$).
2. **Decentralized Evidence Portability Gap:** Reliance on a global simulator key pool for Tier 3 delivery evidence; third-party verification on an untrusted mesh requires portable cryptographic delivery proofs.
3. **Journal Processing Scalability:** Full linear scans of evidence journals during matrix assembly introduce significant overhead ($92\times$ under extreme receipt grinding).
4. **Network Scale:** Empirical evaluation was bounded to 20–50 simulated nodes; asymptotic scalability on networks with thousands of dynamic nodes remains unvalidated.
5. **Domain Separation:** Empirical results apply strictly to P2P file sharing; social networking applications are formulated conceptually without empirical testing.

---

## 9. Final Inventory of Deliverables

| File Path | Byte Size | Character Count | SHA-256 Checksum |
| :--- | :---: | :---: | :---: |
| [`PROTOCOL_SPEC.md`](file:///d:/pki_casestudy/PROTOCOL_SPEC.md) | 59,444 | 59,442 | `A23F3F63D314F17A580CB0E2C7326850A590D76984230F885B5AA74D7FE988FB` |
| [`SECURITY_MODEL.md`](file:///d:/pki_casestudy/SECURITY_MODEL.md) | 20,390 | 20,388 | `D2D0C4BA8F5E08698C5C9E917B7A28B15FAAE14E943B7F816A79BA9C261F9B53` |
| [`NOVEL_TRUST_ALGORITHM_DESIGN_V1_8.md`](file:///d:/pki_casestudy/NOVEL_TRUST_ALGORITHM_DESIGN_V1_8.md) | 32,508 | 32,492 | `6454E7394DAE9654B912BE7F8E1BBC8F41E0AB16102DCAC950295FC32B74FD17` |
| [`FINAL_CASE_STUDY_SYNTHESIS_V3.md`](file:///d:/pki_casestudy/FINAL_CASE_STUDY_SYNTHESIS_V3.md) | 45,096 | 42,900 | `CAC5AEF3B66773CEA416E622A148A27BC577FE8B6A33C75A036214B8C103FA79` |
| [`FINAL_SCOPE_AND_CLAIMS_AUDIT_V3.md`](file:///d:/pki_casestudy/FINAL_SCOPE_AND_CLAIMS_AUDIT_V3.md) | 13,140 | 12,094 | `EC730A488ADAAB431AAA33CC7F13BE5249AF11A0899087E31BA0389091375F84` |
| [`FINAL_CASE_STUDY_SYNTHESIS_V4.md`](file:///d:/pki_casestudy/FINAL_CASE_STUDY_SYNTHESIS_V4.md) | 47,899 | 45,691 | `B6F338C816E3C47456A55B3E3DFB5BF8DCC940A95BF5E602E57D496CCFA0EC0A` |
| [`FINAL_SCOPE_AND_CLAIMS_AUDIT_V4.md`](file:///d:/pki_casestudy/FINAL_SCOPE_AND_CLAIMS_AUDIT_V4.md) | 14,568 | 13,522 | `8B36471E088FDF72312C16CEC9C82533641B9392A7B1115036FBA1201F944D76` |
| [`FINAL_CASE_STUDY_SYNTHESIS_V5.md`](file:///d:/pki_casestudy/FINAL_CASE_STUDY_SYNTHESIS_V5.md) | 51,052 | 48,849 | `7C62C5FB20BD876494CAF01B97366FD8B5454DEFE1C71E3FCFAF41895EE20EC1` |
| [`FINAL_SCOPE_AND_CLAIMS_AUDIT_V5.md`](file:///d:/pki_casestudy/FINAL_SCOPE_AND_CLAIMS_AUDIT_V5.md) | 15,720 | 14,674 | `6654F4DA9A135B72887D94B3BC25FB59604386278D99638826E0E83347D5E076` |
| [`FINAL_CASE_STUDY_SYNTHESIS_V6.md`](file:///d:/pki_casestudy/FINAL_CASE_STUDY_SYNTHESIS_V6.md) | 51,635 | 49,431 | `D332DC71FAB77F86407319D06CA4DE87CD76BA47E5969FB0E7EC3C754C62F03A` |
| [`FINAL_SCOPE_AND_CLAIMS_AUDIT_V6.md`](file:///d:/pki_casestudy/FINAL_SCOPE_AND_CLAIMS_AUDIT_V6.md) | 12,701 | 12,701 | `574600412C6E9372B615380EAF0EAA6B8D2CC69FCA88A2C01BD08757A5441C2D` |
| [`FINAL_CASE_STUDY_SYNTHESIS_V7.md`](file:///d:/pki_casestudy/FINAL_CASE_STUDY_SYNTHESIS_V7.md) | 56,978 | 54,775 | `39A17A505688DF1DD316F474B288793F900ABDD226DA0CAEB9A421EAA3A9CBFB` |
| [`FINAL_SCOPE_AND_CLAIMS_AUDIT_V7.md`](file:///d:/pki_casestudy/FINAL_SCOPE_AND_CLAIMS_AUDIT_V7.md) | 17,875 | 16,805 | `F7FF9E2349B462B9D22D74F2CE61F772FCAE0BC75F2439C42BB04720B949DCC7` |

*(Note: Per instruction, this report's own size and SHA-256 are excluded from the table to avoid self-referential paradox).*

PHASE8_10_STATUS: PASS
