# Phase 8.11 — Final Mathematical and Evidence Consistency Report (V8)

**Document Version:** 8.0.0-FINAL-FREEZE  
**Date:** October 9, 2026  
**Author / Auditor:** Candidate Shreyan Nayak (23BKT0039)  
**Evaluated Artifacts:**  
- [`FINAL_CASE_STUDY_SYNTHESIS_V7.md`](file:///d:/pki_casestudy/FINAL_CASE_STUDY_SYNTHESIS_V7.md) (Preserved unchanged)  
- [`FINAL_SCOPE_AND_CLAIMS_AUDIT_V7.md`](file:///d:/pki_casestudy/FINAL_SCOPE_AND_CLAIMS_AUDIT_V7.md) (Preserved unchanged)  
- [`PHASE8_10_REGRESSION_AND_FREEZE_REPORT.md`](file:///d:/pki_casestudy/PHASE8_10_REGRESSION_AND_FREEZE_REPORT.md) (Preserved unchanged)  
- [`PROTOCOL_SPEC.md`](file:///d:/pki_casestudy/PROTOCOL_SPEC.md) (v2.2.0-FROZEN)  
- [`SECURITY_MODEL.md`](file:///d:/pki_casestudy/SECURITY_MODEL.md) (v2.2.0-FROZEN)  
- [`NOVEL_TRUST_ALGORITHM_DESIGN_V1_8.md`](file:///d:/pki_casestudy/NOVEL_TRUST_ALGORITHM_DESIGN_V1_8.md)  
- [`PHASE8_2_PREREGISTRATION.md`](file:///d:/pki_casestudy/PHASE8_2_PREREGISTRATION.md)  
- [`experiments/phase8_2_benchmark.py`](file:///d:/pki_casestudy/experiments/phase8_2_benchmark.py)  
- [`results/phase8_2_statistical_comparison.csv`](file:///d:/pki_casestudy/results/phase8_2_statistical_comparison.csv)  
- [`results/phase8_2_summary.csv`](file:///d:/pki_casestudy/results/phase8_2_summary.csv)  
- [`results/phase8_2_raw_results.json`](file:///d:/pki_casestudy/results/phase8_2_raw_results.json)  
- [`tests_scratch/verify_numbers.py`](file:///d:/pki_casestudy/tests_scratch/verify_numbers.py)  

---

## 1. Executive Summary

Phase 8.11 executes a narrowly scoped final correction to eliminate a mathematical contradiction regarding dangling-node fallback behavior, audit numerical verification claims against raw trial data and the verification script, tighten evidentiary terminology, and preserve all established empirical findings. 

All existing V7 artifacts (`FINAL_CASE_STUDY_SYNTHESIS_V7.md`, `FINAL_SCOPE_AND_CLAIMS_AUDIT_V7.md`, `PHASE8_10_REGRESSION_AND_FREEZE_REPORT.md`), frozen specifications (`PROTOCOL_SPEC.md`, `SECURITY_MODEL.md`, `NOVEL_TRUST_ALGORITHM_DESIGN_V1_8.md`), implementation source code under `src/`, and benchmark results under `results/` are preserved strictly unchanged. 

Three new deliverables are established:
1. [`FINAL_CASE_STUDY_SYNTHESIS_V8.md`](file:///d:/pki_casestudy/FINAL_CASE_STUDY_SYNTHESIS_V8.md)
2. [`FINAL_SCOPE_AND_CLAIMS_AUDIT_V8.md`](file:///d:/pki_casestudy/FINAL_SCOPE_AND_CLAIMS_AUDIT_V8.md)
3. [`PHASE8_11_FINAL_CONSISTENCY_REPORT.md`](file:///d:/pki_casestudy/PHASE8_11_FINAL_CONSISTENCY_REPORT.md)

---

## 2. Concise Correction Log (V7 $\to$ V8)

| # | Item / Location | Prior State in V7 | Corrected State in V8 | Rationale / Grounding |
| :-: | :--- | :--- | :--- | :--- |
| **1** | **Fallback Contradiction in Scenario 7**<br>([`FINAL_CASE_STUDY_SYNTHESIS_V8.md` §6.2](file:///d:/pki_casestudy/FINAL_CASE_STUDY_SYNTHESIS_V8.md#L273-L282), [`FINAL_SCOPE_AND_CLAIMS_AUDIT_V8.md` Claim 9](file:///d:/pki_casestudy/FINAL_SCOPE_AND_CLAIMS_AUDIT_V8.md#L94)) | Stated that the coalition source term remains zero *"under either fallback rule ($\mathbf{p}$ or $1/n$)"*. | Removed the "under either fallback rule" assertion. Stated that in benchmark execution, colluders rated each other, so **no colluder row dangled**. Stated that the implemented fallback is $C'_{i, :} = \mathbf{p}$; if a colluder dangled, falling back to $\mathbf{p}$ (supported only on honest supernodes) would send mass to honest nodes and **break coalition closure**. A uniform $1/n$ fallback is hypothetical, assigns mass across all nodes, and cannot be assumed to satisfy closure without separate derivation. | Implemented rule in [`src/layer3_eigentrust.py:1218`](file:///d:/pki_casestudy/src/layer3_eigentrust.py#L1218) and [`NOVEL_TRUST_ALGORITHM_DESIGN_V1_8.md:465`](file:///d:/pki_casestudy/NOVEL_TRUST_ALGORITHM_DESIGN_V1_8.md#L465) is $C'_{i, :} = \mathbf{p}$. In benchmark trials (`experiments/phase8_2_benchmark.py:723-744`), colluders exchanged internal ratings ($\sum_{c' \in C} A_{c c'} > 0$), so no dangling fallback was triggered. Zero colluder trust holds because incoming bridge edges are zero ($C'_{hc} = 0$), pre-trust is zero ($p_c = 0$), and no colluder dangled. |
| **2** | **Verification Terminology**<br>([`PHASE8_11_FINAL_CONSISTENCY_REPORT.md`](file:///d:/pki_casestudy/PHASE8_11_FINAL_CONSISTENCY_REPORT.md) §3) | Used phrasing such as matching formulas *"bit-for-bit"*. | Replaced with *"the inspected source expression and design equation are algebraically consistent"*. Delineated six mutually exclusive evidence categories: source inspection, test-suite execution, CSV consistency checks, recalculation from raw trial data, analytical derivation, and formal verification. | A literal byte comparison between LaTeX formulas and Python code is meaningless; algebraic consistency is the correct technical claim. Passing tests do not constitute formal machine-checked proofs. |
| **3** | **Verification Script Clarification**<br>([`PHASE8_11_FINAL_CONSISTENCY_REPORT.md`](file:///d:/pki_casestudy/PHASE8_11_FINAL_CONSISTENCY_REPORT.md) §3, §4) | Ambiguous descriptions could imply `tests_scratch/verify_numbers.py` independently recomputes results from raw trial data. | Clarified that `tests_scratch/verify_numbers.py` compares the formatted markdown table against `results/phase8_2_statistical_comparison.csv` (133 checks), without reading raw per-trial JSON data or computing statistical tests. Conducted direct independent recalculation from `results/phase8_2_raw_results.json` separately. | Full code inspection of `tests_scratch/verify_numbers.py` shows it parses hardcoded markdown string `table_lines` and compares against CSV dictionary rows. |
| **4** | **Deliverable Headers & Cross-References**<br>(V8 Deliverables) | Referenced V7 versioning and Phase 8.10 report. | Updated to `v8.0-FINAL-FREEZE`, dated October 9, 2026, referencing [`PHASE8_11_FINAL_CONSISTENCY_REPORT.md`](file:///d:/pki_casestudy/PHASE8_11_FINAL_CONSISTENCY_REPORT.md). | Clean cross-document reconciliation and version consistency across all V8 deliverables. |

---

## 3. Audit of `tests_scratch/verify_numbers.py`

### 3.1 Script Structure and Operation
The complete source code of [`tests_scratch/verify_numbers.py`](file:///d:/pki_casestudy/tests_scratch/verify_numbers.py) (122 lines) was inspected:
- **Data Source:** Opens `results/phase8_2_statistical_comparison.csv` and builds an in-memory lookup dictionary keyed by `(scenario, scale)`.
- **Target Comparison Text:** Hardcodes a string variable `table_lines` (lines 12–32) containing the 19 scenario-scale markdown table rows from earlier synthesis drafts.
- **Scenario Key Mapping:** Maps human-readable table labels (e.g., `'S2: Closed Collusion'`) to CSV scenario strings (e.g., `'scenario_2_closed_collusion'`) via `name_map` (lines 34–48).
- **Checks Executed:** Loops over each table line and executes comparisons across 7 numerical columns:
  1. `vanilla_colluder_mean` (tolerance $\pm 0.0005$)
  2. `ew_colluder_mean` (tolerance $\pm 0.0005$)
  3. `absolute_difference` (tolerance $\pm 0.0005$)
  4. `relative_difference_pct` (tolerance $\pm 0.05\%$)
  5. `paired_t_statistic` (tolerance $\pm 0.005$)
  6. `p_value` (relative tolerance $\pm 5\%$ for small $p$, absolute $\pm 0.005$ for large $p$)
  7. `cohens_dz` (tolerance $\pm 0.01$)
- **Total Checks:** Exactly $19 \text{ rows} \times 7 \text{ columns} = 133 \text{ checks}$.
- **Execution Result:** `Mechanical check complete: 133 checks executed. Mismatches found: 0`.

### 3.2 Evaluation of Independence and Scope Limitations
1. **Source of Expected Values:** The expected values are extracted by regex parsing of the embedded markdown table string inside the script itself. They are **not** computed dynamically from simulation runs or raw trial data.
2. **Independence from the CSV:** **Zero values are independent of `phase8_2_statistical_comparison.csv`.** The script verifies that the human-readable markdown table transcribed into the script matches the statistical CSV. It does not verify the mathematical generation of the CSV from underlying experimental observations.
3. **Missing Data in Script Coverage:**
   - Does **not** inspect or load [`results/phase8_2_raw_results.json`](file:///d:/pki_casestudy/results/phase8_2_raw_results.json) (the 1,140 individual trial evaluations).
   - Does **not** inspect [`results/phase8_2_summary.csv`](file:///d:/pki_casestudy/results/phase8_2_summary.csv).
   - Does **not** verify Scenario 8 honest asymmetric uploader trust ($t_{\text{uploader}}$) or uploader retention ratios. (In `verify_numbers.py` lines 28–29, rows for S8 still test colluder trust $0.0000$ from older drafts).
   - Does **not** calculate sample standard deviations, standard errors, degrees of freedom, or confidence intervals.

**Conclusion:** `tests_scratch/verify_numbers.py` is a **table-to-CSV transcription consistency check**, not an independent statistical recalculation from raw experimental data.

---

## 4. Independent Mechanical Recalculation from Raw Trial Data

To provide genuine independent verification, a Python script was executed to process [`results/phase8_2_raw_results.json`](file:///d:/pki_casestudy/results/phase8_2_raw_results.json) directly. This file contains 1,140 individual trial records spanning:
- 19 scenario-scale configurations.
- 20 random seeds per configuration ($\mathcal{S} = \{42 + 17 \cdot i \mid i \in [0, 19]\}$).
- 3 execution modes per seed (`vanilla_eigentrust`, `evidence_only`, `local_only`).

### 4.1 Statistical Recalculation Results

For each of the 19 configurations, paired vectors $\mathbf{x}_{\text{Vanilla}}$ and $\mathbf{x}_{\text{EW}}$ ($N=20$) were extracted, computing:
- Sample means: $\bar{x}_V = \frac{1}{N}\sum x_{V, s}$, $\bar{x}_{EW} = \frac{1}{N}\sum x_{EW, s}$.
- Absolute difference: $\Delta = \bar{x}_{EW} - \bar{x}_V$.
- Relative difference: $\% \Delta = (\Delta / \bar{x}_V) \cdot 100\%$ (for $\bar{x}_V > 0$).
- Paired differences: $d_s = x_{EW, s} - x_{V, s}$.
- Sample standard deviation of differences: $s_d = \sqrt{\frac{1}{N-1}\sum (d_s - \bar{d})^2}$.
- Paired Student's $t$-statistic: $t = \bar{d} / (s_d / \sqrt{N})$ (for $s_d > 10^{-12}$).
- Two-tailed $p$-value: $p = 2 \cdot (1 - F_t(|t|, \text{df}=19))$.
- Cohen's effect size: $d_z = \bar{d} / s_d$.

| Scenario | Scale | Vanilla Mean | EW Mean | Abs Diff $\Delta$ | Rel Diff | Paired $t$-stat | $p$-value | Cohen's $d_z$ | Verification Match Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **S1: Honest Baseline** | Standard | $0.0000$ | $0.0000$ | $0.0000$ | $0.00\%$ | Undefined ($0/0$) | Undefined | Undefined | Exact Match (Zero variance) |
| **S1: Honest Baseline** | Extended | $0.0000$ | $0.0000$ | $0.0000$ | $0.00\%$ | Undefined ($0/0$) | Undefined | Undefined | Exact Match (Zero variance) |
| **S2: Closed Collusion** | Standard | $0.0850$ | $0.0889$ | $+0.0039$ | $+4.53\%$ | $+1.472$ | $0.158$ | $+0.33$ | Exact Match ($p = 0.1575$) |
| **S2: Closed Collusion** | Extended | $0.0539$ | $0.0611$ | $+0.0073$ | $+13.50\%$ | $+3.944$ | $8.70 \times 10^{-4}$ | $+0.88$ | Exact Match ($p = 8.699 \times 10^{-4}$) |
| **S3: Leaky Collusion** | Standard | $0.1834$ | $0.1084$ | $-0.0750$ | $-40.88\%$ | $-34.354$ | $1.44 \times 10^{-18}$ | $-7.68$ | Exact Match ($p = 1.441 \times 10^{-18}$) |
| **S3: Leaky Collusion** | Extended | $0.1982$ | $0.1160$ | $-0.0823$ | $-41.50\%$ | $-50.410$ | $1.07 \times 10^{-21}$ | $-11.27$ | Exact Match ($p = 1.066 \times 10^{-21}$) |
| **S4: Connected ($q=0.00$)** | Standard | $0.0000$ | $0.0000$ | $0.0000$ | $0.00\%$ | Undefined ($0/0$) | Undefined | Undefined | Exact Match (Zero variance) |
| **S4: Connected ($q=0.05$)** | Standard | $0.0935$ | $0.1176$ | $+0.0242$ | $+25.89\%$ | $+11.757$ | $3.66 \times 10^{-10}$ | $+2.63$ | Exact Match ($p = 3.656 \times 10^{-10}$) |
| **S4: Connected ($q=0.10$)** | Standard | $0.1606$ | $0.1885$ | $+0.0279$ | $+17.34\%$ | $+13.621$ | $2.96 \times 10^{-11}$ | $+3.05$ | Exact Match ($p = 2.964 \times 10^{-11}$) |
| **S4: Connected ($q=0.20$)** | Standard | $0.2731$ | $0.2920$ | $+0.0189$ | $+6.92\%$ | $+9.209$ | $1.95 \times 10^{-8}$ | $+2.06$ | Exact Match ($p = 1.953 \times 10^{-8}$) |
| **S4: Connected ($q=0.40$)** | Standard | $0.4124$ | $0.4045$ | $-0.0079$ | $-1.90\%$ | $-4.799$ | $1.25 \times 10^{-4}$ | $-1.07$ | Exact Match ($p = 1.249 \times 10^{-4}$) |
| **S5: Adaptive Attacker** | Standard | $0.0964$ | $0.1004$ | $+0.0040$ | $+4.16\%$ | $+1.739$ | $0.098$ | $+0.39$ | Exact Match ($p = 0.0982$) |
| **S6: Receipt Grinding** | Standard | $0.0922$ | $0.1046$ | $+0.0123$ | $+13.38\%$ | $+3.860$ | $1.06 \times 10^{-3}$ | $+0.86$ | Exact Match ($p = 1.056 \times 10^{-3}$) |
| **S6: Receipt Grinding** | Extended | $0.0558$ | $0.0658$ | $+0.0100$ | $+17.92\%$ | $+4.968$ | $8.55 \times 10^{-5}$ | $+1.11$ | Exact Match ($p = 8.547 \times 10^{-5}$) |
| **S7: Dispute Manip** | Standard | $0.0000$ | $0.0000$ | $0.0000$ | $0.00\%$ | Undefined ($0/0$) | Undefined | Undefined | Exact Match (Zero variance) |
| **S8: Asym Uploader ($t_{\text{uploader}}$)** | Standard | $0.1574$ | $0.1754$ | $+0.0180$ | $+11.43\%$ | $+54.177$ | $2.74 \times 10^{-22}$ | $+12.11$ | Exact Match (Ratio: $1.1143$) |
| **S8: Asym Uploader ($t_{\text{uploader}}$)** | Extended | $0.1584$ | $0.1786$ | $+0.0202$ | $+12.74\%$ | $+73.490$ | $8.57 \times 10^{-25}$ | $+16.43$ | Exact Match (Ratio: $1.1274$) |
| **S9: Reciprocal Comm** | Standard | $0.0000$ | $0.0000$ | $0.0000$ | $0.00\%$ | Undefined ($0/0$) | Undefined | Undefined | Exact Match (Zero variance) |
| **S9: Reciprocal Comm** | Extended | $0.0000$ | $0.0000$ | $0.0000$ | $0.00\%$ | Undefined ($0/0$) | Undefined | Undefined | Exact Match (Zero variance) |

### 4.2 Diagnosis of Zero-Variance and Scenario 8 Reporting
1. **Zero-Variance Cases:** In Scenarios 1, 4 ($q=0.00$), 7, and 9, colluder trust is identically zero across all seeds. In `results/phase8_2_statistical_comparison.csv`, the script logged `t = 0.0, p = 1.0, dz = 0.0` due to a defensive branch (`experiments/phase8_2_benchmark.py:986`). Because $s_d = 0$, $t = \bar{d} / (0 / \sqrt{N}) = 0/0$, which is **mathematically undefined**. In Synthesis V8 §6.1, these cases are accurately reported as **Undefined (zero variance)**.
2. **Scenario 8 Reporting:** In `phase8_2_statistical_comparison.csv`, colluder trust for S8 is $0.0000$ (as colluders do not exist in S8). Honest asymmetric uploader trust is stored in `asymmetric_uploader_trust` in `phase8_2_raw_results.json` and summarized by `uploader_retention_ratio` ($1.1143$ and $1.1274$) in the CSV. In Synthesis V8 §6.1, row 8 explicitly evaluates $t_{\text{uploader}}$ directly ($0.1574 \to 0.1754$, $+11.43\%, t = +54.177, p = 2.74 \times 10^{-22}$ standard; $0.1584 \to 0.1786$, $+12.74\%, t = +73.490, p = 8.57 \times 10^{-25}$ extended).

### 4.3 Boundaries of What Could and Could Not Be Recomputed
- **Recomputed Directly from Raw Data:** All 1,140 trial trust scores, scenario means, pairwise differences, paired $t$-statistics, $p$-values, effect sizes ($d_z$), uploader trust values, and retention ratios.
- **NOT Available on Disk / Cannot Be Recomputed:**
  - Per-trial transition matrices $\mathbf{C}' \in \mathbb{R}^{n \times n}$.
  - Per-trial stationary trust vectors $\mathbf{t} \in \mathbb{R}^n$.
  - Per-trial trust-weighted flow values $F_{H \to C} = \sum_{h \in H} t_h \sum_{c \in C} C'_{hc}$.
  - Per-trial teleportation/restart vector allocations.
  
Because per-trial transition matrices and flow values were not serialized to disk during the Phase 8.2 benchmark run, empirical verification of the closed-set flow identity $T_C = \frac{1-\alpha}{\alpha} F_{H \to C}$ on a trial-by-trial basis cannot be reconstructed. Preregistered Hypothesis H-3 was an empirical diagnostic check observing lack of suppression, not a numerical verification of the flow identity equation.

---

## 5. Delineation of Six Distinct Evidence Categories

To prevent category inflation, all evidence across this project is categorized into six mutually exclusive classes:

| Evidence Category | Exact Project Scope | Grounding Artifacts | What It Proves | What It Does NOT Prove |
| :--- | :--- | :--- | :--- | :--- |
| **1. Source Inspection** | Direct manual/scripted reading of source code files. | `src/layer1_identity.py`<br>`src/layer2_mesh_pki.py`<br>`src/layer3_eigentrust.py`<br>`src/layer4_recovery.py`<br>`experiments/phase8_2_benchmark.py` | Implementation structure, algebraic formulas, fallback logic, variable types. | Does not prove absence of runtime bugs, numerical stability, or protocol security. |
| **2. Test-Suite Execution** | Deterministic unit and regression testing via Python `unittest`. | `tests/test_ew_eigentrust.py` (14 tests)<br>`tests/test_trust_framework.py` (61 tests)<br>`tests_scratch/unittest_phase8_9.log` | Software code passes 75 specific programmed assertions and unit edge cases. | Does not prove mathematical correctness for all inputs, security under arbitrary adversaries, or formal verification. |
| **3. CSV Consistency Checks** | Mechanical table comparison against exported benchmark CSVs. | `tests_scratch/verify_numbers.py`<br>`results/phase8_2_statistical_comparison.csv` | Document tables accurately transcribe summary CSV contents (133 checks passed). | Does not verify correctness of simulation execution or recalculate from raw trial observations. |
| **4. Recalculation from Raw Trial Data** | Independent Python recalculation from per-seed telemetry JSON. | `results/phase8_2_raw_results.json` (1,140 trials) processed independently. | Aggregate means, differences, paired $t$-tests, $p$-values, and effect sizes are mathematically correct. | Does not reconstruct unrecorded runtime objects (per-trial transition matrices $\mathbf{C}'$, flow $F_{H \to C}$). |
| **5. Analytical Mathematical Derivation** | Pen-and-paper deductive mathematical derivations from first principles. | Synthesis V8 §7.1, derivation from stationary equation $\mathbf{t} = (1-\alpha)(\mathbf{C}')^T\mathbf{t} + \alpha\mathbf{p}$. | Proves asymptotic stationary relations (e.g., $T_C = \frac{1-\alpha}{\alpha} F_{H \to C}$) under stated assumptions. | Does not prove that assumptions hold in unverified networks or predict finite-step convergence dynamics. |
| **6. Machine-Checked Formal Verification** | Proof assistants (Coq, Isabelle/HOL, Lean, TLA+, Dafny). | **None** *(Explicitly out of scope / Not performed)*. | Exhaustive machine-checked mathematical proof of state machine or protocol invariants. | **NOT CLAIMED.** Software tests and analytical derivations do not constitute formal verification. |

---

## 6. Preservation of Established Findings Checklist

All established technical, empirical, and boundary findings are preserved without weakening or silent alteration:

- [x] **Closed-Set Flow Identity Assumptions:** Strictly preserved. The identity $T_C = \frac{1-\alpha}{\alpha} F_{H \to C}$ applies only under three structural assumptions: strict coalition closure ($\forall c \in C, h \in H: C'_{ch} = 0$), zero pre-trust on colluders ($\mathbf{p}_C = \mathbf{0}$), and no dangling coalition rows ($\forall c \in C: \sum_{c' \in C} A_{cc'} > 0$).
- [x] **Invariance Condition:** Strictly preserved. For aggregate coalition trust to remain invariant under algorithmic alterations, incoming trust-weighted flow $F_{H \to C} = \sum_{h \in H} t_h \sum_{c \in C} C'_{hc}$ must remain constant. Fixed transition probabilities alone do not guarantee invariance if honest trust $\mathbf{t}_H$ shifts.
- [x] **Hypothesis H-1 Refutation:** Strictly preserved. Preregistered Hypothesis H-1 is formally refuted ($T_C$ increased from $9.2\%$ to $10.5\%$ in standard, $p = 1.06 \times 10^{-3}$, and $5.6\%$ to $6.6\%$ in extended, $p = 8.55 \times 10^{-5}$).
- [x] **Leaky-Coalition Suppression:** Strictly preserved. Suppression of $>40\%$ ($p < 10^{-18}$) is strictly conditional on leaky topologies where colluders interact with and rate honest peers.
- [x] **Scenario 7 Structural Degeneracy:** Strictly preserved. Zero colluder trust is a structurally degenerate artifact of topological disconnection ($C'_{hc} = 0, p_c = 0$, positive internal ratings); it does not validate dispute defense against active bridge ingress.
- [x] **Tier 3 Delivery Evidence & Portability Gap:** Strictly preserved. Tier 3 verification depends on local client verification or the simulator's global key pool; a bilateral receipt alone is not a portable third-party proof of delivery.
- [x] **Threshold Authorization vs BFT Consensus:** Strictly preserved. The 3-of-5 supernode quorum mechanism enforces threshold signature collection for administrative revocation; it is not Byzantine fault-tolerant consensus.
- [x] **Social Networking as Conceptual Extension:** Strictly preserved. P2P social networking is formulated as an architectural conceptual mapping without empirical trials or dataset evaluation.
- [x] **Attributable Fault Semantics:** Strictly preserved. Cryptographic contradiction proofs prove attributable delivery of inconsistent data; they do not prove subjective malicious intent (e.g., bit rot vs deliberate poisoning), and a failed Merkle proof alone does not prove non-membership or attributable inconsistency.

---

## 7. Artifact Byte Sizes and SHA-256 Hashes

The file sizes and SHA-256 checksums of the three Phase 8.11 deliverables were measured directly from the filesystem using Python:

```powershell
python -c "import hashlib; [(print(f, len(open(f,'rb').read()), hashlib.sha256(open(f,'rb').read()).hexdigest())) for f in ['FINAL_CASE_STUDY_SYNTHESIS_V8.md', 'FINAL_SCOPE_AND_CLAIMS_AUDIT_V8.md', 'PHASE8_11_FINAL_CONSISTENCY_REPORT.md']]"
```

| Deliverable Artifact | File Path | Measured Byte Size | Measured SHA-256 Checksum |
| :--- | :--- | :---: | :--- |
| **Final Synthesis V8** | [`FINAL_CASE_STUDY_SYNTHESIS_V8.md`](file:///d:/pki_casestudy/FINAL_CASE_STUDY_SYNTHESIS_V8.md) | `58,437` bytes | `71955e14378c570ba127f08ea7095bc426b6d07de027bd70b339abb919cfc497` |
| **Final Scope Audit V8** | [`FINAL_SCOPE_AND_CLAIMS_AUDIT_V8.md`](file:///d:/pki_casestudy/FINAL_SCOPE_AND_CLAIMS_AUDIT_V8.md) | `18,412` bytes | `1de6d1f6bb72b5782b710c8d67e2ee8c2e2b990877b68dbe31c382b767f75ff8` |
| **Consistency Report V8** | [`PHASE8_11_FINAL_CONSISTENCY_REPORT.md`](file:///d:/pki_casestudy/PHASE8_11_FINAL_CONSISTENCY_REPORT.md) | *Self-referential; measured via command above* | *Self-referential; measured via command above* |

*(Note: Per standard audit protocol, this report's own size and SHA-256 are designated as self-referential in its own internal table to avoid self-referential paradox, and are measured directly via the PowerShell execution command above).*

---

## 8. Final Status Declaration

The fallback explanation is mathematically rigorous and consistent with the frozen design, statistical verification claims accurately reflect raw experimental observations and script capabilities, verification terminology is precisely categorized across six distinct evidentiary classes, and all empirical findings and boundaries are preserved without compromise.

PHASE8_11_STATUS: PASS
