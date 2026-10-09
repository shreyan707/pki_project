# Phase 8.2 Preregistration: Empirical Validation of EW-EigenTrust v1.8

**Document Version:** 1.0.0-PREREGISTERED  
**Date:** October 9, 2026  
**Author:** Candidate Shreyan Nayak (23BKT0039) & Independent Statistical Auditor  
**Status:** SEALED BEFORE BENCHMARK EXECUTION  
**Target Artifact:** `experiments/phase8_2_benchmark.py`  

---

## 1. Experimental Objective & Scope

The objective of Phase 8.2 is to conduct an empirical, reproducible, and mathematically rigorous evaluation comparing:
1. **Vanilla EigenTrust** (`TrustComputationMode.VANILLA`): Standard PageRank/EigenTrust formulation using raw interaction satisfaction accumulation.
2. **Evidence-Weighted EigenTrust v1.8** (`TrustComputationMode.EVIDENCE_ONLY`): Authoritative proposed algorithm featuring bounded concave edge ceilings ($\Phi_{\text{edge}}$), 3-tier cryptographic delivery weighting, timestamp freshness decay, dispute penalties, and certified fault nullification.
3. **Local-Only Baseline** (`TrustComputationMode.LOCAL_ONLY`): Direct unpropagated rating aggregation (no transitive reputation propagation).

In accordance with strict scientific discipline:
- **No Hyping or Premature Confirmation:** EW-EigenTrust is treated as an empirical hypothesis to be rigorously tested.
- **Pre-Determined Evaluation Criteria:** All evaluation criteria, metrics, statistical tests, and exclusion rules are recorded herein *prior* to executing the main benchmark.
- **Fair Paired Evaluation:** Every scenario runs paired trials using identical random seeds, node identities, network topologies, interaction opportunities, and attacker behaviors.

---

## 2. Experimental Scenarios (9 Scenarios)

The evaluation covers nine scenarios designed to isolate specific attack vectors, honest behaviors, and network topologies:

### Scenario 1: Honest Baseline
- **Description:** A purely honest network with varying interaction rates among honest nodes and supernodes. Zero malicious or colluding peers.
- **Purpose:** Establish baseline trust distribution, verify simplex conservation, and measure variance across seeds.
- **Configuration:** 15 honest peers, 5 supernodes, 0 Sybils. 8 transaction rounds.

### Scenario 2: Closed Colluding Coalition
- **Description:** A coalition of colluders exchange mutual $+1.00$ receipts among themselves with dummy roots. Colluders have zero outgoing edges to honest peers. An honest peer bridges into the coalition by downloading content from a colluder ($p_{\text{bridge}} > 0$).
- **Purpose:** Test whether bounded edge strength and Tier 1 discounting reduce colluder trust share under closed-set invariance.
- **Configuration:** 15 honest peers, 5 supernodes, 10 colluders. Fixed bridge: 1 honest downloader. 8 transaction rounds.

### Scenario 3: Leaky Coalition
- **Description:** Colluders engage in mutual internal reinforcement while also interacting with honest peers (providing authentic files to honest downloaders and rating honest peers).
- **Purpose:** Evaluate whether EW-EigenTrust outperforms vanilla EigenTrust when colluders leak trust back into the honest community.
- **Configuration:** 15 honest peers, 5 supernodes, 10 colluders. Bridge probability $p_{\text{bridge}} = 0.20$. 8 transaction rounds.

### Scenario 4: Connected Collusion (Bridge Density Sweep)
- **Description:** Systematic parameter sweep over bridge probability $p_{\text{bridge}} \in \{0.00, 0.05, 0.10, 0.20, 0.40\}$ connecting the colluder coalition to the honest network.
- **Purpose:** Measure colluder trust share as a function of external incoming transition flow.
- **Configuration:** 15 honest peers, 5 supernodes, 10 colluders. 8 transaction rounds per sweep point.

### Scenario 5: Adaptive Attacker
- **Description:** Colluders adapt their internal topology across trials: dense clique vs. directed cycle vs. hub-and-spoke with a dedicated bridgehead node, while selectively providing authentic chunks to honest clients to gain Tier 3 credit on bridge edges.
- **Purpose:** Test whether the observed benefits of EW-EigenTrust survive structural attacker adaptation.
- **Configuration:** 15 honest peers, 5 supernodes, 10 colluders. Mixed internal topologies. 8 transaction rounds.

### Scenario 6: Receipt-Grinding Attack
- **Description:** Colluders execute an aggressive credit-grinding campaign by submitting high volumes of mutual unindexed bilateral receipts (10 to 50 receipts per edge) between colluder pairs.
- **Purpose:** Specifically evaluate the practical impact of the concave edge ceiling $\Phi_{\text{edge}}(E) \le K_{\max} = 10.0$ and Tier 1 discount ($\mu_{\text{unverified}} = 0.10$) against unbounded algebraic grinding ($S_{ij} \to \infty$).
- **Configuration:** 15 honest peers, 5 supernodes, 10 colluders. 50 internal receipts per colluder pair. 8 transaction rounds.

### Scenario 7: Dispute Manipulation
- **Description:** Colluders inject subjective negative bilateral receipts (`rating == -1.00`) against selected honest peers while generating unreciprocated positive claims, testing edge dispute accounting.
- **Purpose:** Verify that subjective disputes penalize edges via $\gamma_{\text{dispute}}$ without incorrectly triggering certified fault revocation or network eviction.
- **Configuration:** 15 honest peers, 5 supernodes, 5 colluders. Dispute injection rate 0.30. 8 transaction rounds.

### Scenario 8: Honest Asymmetric Uploader
- **Description:** A dedicated honest provider serves a high volume of download requests to client peers without consuming content or receiving reciprocal return downloads.
- **Purpose:** Verify that honest asymmetric providers are not penalized or suppressed under EW-EigenTrust relative to vanilla EigenTrust.
- **Configuration:** 15 honest peers, 5 supernodes, 1 dedicated high-volume server, 0 Sybils. 8 transaction rounds.

### Scenario 9: Honest Reciprocal Community
- **Description:** Densely connected honest community with mutual pairwise cooperation.
- **Purpose:** Measure whether EW-EigenTrust causes any unintended trust suppression or distortion among honest peers.
- **Configuration:** 15 honest peers, 5 supernodes, 0 Sybils. High pairwise interaction density. 8 transaction rounds.

---

## 3. Seed List & Network Scale Specifications

### 3.1 Paired Seed Convention
To ensure statistical power and variance estimation, all evaluations execute across **20 independent paired seeds**:
$$\mathcal{S} = \{42 + 17 \cdot i \mid i \in [0, 19]\} = \{42, 59, 76, 93, 110, 127, 144, 161, 178, 195, 212, 229, 246, 263, 280, 297, 314, 331, 348, 365\}$$

### 3.2 Network Scales Evaluated
1. **Standard Scale (30–35 nodes):** 15 honest nodes, 5 supernodes, 10–15 colluders.
2. **Extended Scale (50 nodes):** 25 honest nodes, 5 supernodes, 20 colluders (evaluates scaling behavior).

---

## 4. Primary Metrics & Mathematical Definitions

1. **Total Colluder Trust Share ($T_C$):**
   $$T_C = \sum_{c \in C} t_c, \quad \text{where } \sum_{i=1}^n t_i = 1.0$$
2. **Total Honest Trust Share ($T_H$):**
   $$T_H = \sum_{h \in H} t_h$$
3. **Supernode Trust Share ($T_{SN}$):**
   $$T_{SN} = \sum_{sn \in S} t_{sn}$$
4. **Max Individual Colluder Trust ($t_{C,\max}$):**
   $$t_{C,\max} = \max_{c \in C} t_c$$
5. **Asymmetric Provider Trust ($t_{\text{uploader}}$):**
   Stationary trust score assigned to the dedicated non-reciprocal uploader.
6. **Absolute Difference ($\Delta_T$):**
   $$\Delta_T = T_{C, \text{EW}} - T_{C, \text{Vanilla}}$$
7. **Relative Difference ($\% \Delta_T$):**
   $$\% \Delta_T = \frac{T_{C, \text{EW}} - T_{C, \text{Vanilla}}}{T_{C, \text{Vanilla}}} \times 100\%$$
8. **Power Iteration Convergence Iterations ($m_{\text{conv}}$):**
   Number of iterations until $\|\mathbf{t}_m - \mathbf{t}_{m-1}\|_2 < \text{tol}$.
9. **Evidence Tier Breakdown:**
   Total count of committed receipts evaluated at Tier 1 ($N_{T1}$), Tier 2 ($N_{T2}$), and Tier 3 ($N_{T3}$).

---

## 5. Statistical Testing Procedures

For all paired comparisons across the 20 seeds:
1. **Descriptive Statistics:** Report Sample Mean, Sample Median, Sample Standard Deviation ($s$), Sample Min, Sample Max.
2. **Parametric 95% Confidence Interval:**
   $$\text{CI}_{95\%} = \bar{x} \pm t_{0.975, \, n-1} \cdot \frac{s}{\sqrt{n}}, \quad \text{where } t_{0.975, 19} = 2.093$$
3. **Paired Difference Test:** Two-sided paired Student's t-test on differences $d_i = x_{i, \text{EW}} - x_{i, \text{Vanilla}}$.
4. **Effect Size (Cohen's $d_z$ for paired samples):**
   $$d_z = \frac{\bar{d}}{s_d}$$
   Classification: $|d_z| \ge 0.8$ (large), $0.5 \le |d_z| < 0.8$ (medium), $0.2 \le |d_z| < 0.5$ (small).
5. **Zero Reporting Rule:** A metric is reported as zero strictly if measured as zero; unexercised mechanisms are labeled `N/A (unexercised)`.

---

## 6. Pre-Registered Hypotheses & Evaluation Criteria

### Hypothesis H-1 (Receipt Grinding Suppression)
- **Statement:** Under intense internal receipt grinding (Scenario 6), EW-EigenTrust will reduce colluder trust share relative to Vanilla EigenTrust ($T_{C, \text{EW}} < T_{C, \text{Vanilla}}$) due to concave saturation $\Phi_{\text{edge}} \le 10.0$ and Tier 1 discounting ($\mu = 0.10$).
- **Success Criterion:** Statistically significant reduction ($p < 0.05$, $d_z < -0.5$).

### Hypothesis H-2 (Honest Asymmetric Uploader Preservation)
- **Statement:** Under pure asymmetric uploading (Scenario 8), EW-EigenTrust will preserve the honest uploader's trust score without significant suppression relative to Vanilla EigenTrust ($t_{\text{uploader}, \text{EW}} \ge 0.95 \cdot t_{\text{uploader}, \text{Vanilla}}$).
- **Success Criterion:** Honest provider trust retention ratio $\ge 0.95$.

### Hypothesis H-3 (Closed Coalition Invariance Reality Check)
- **Statement:** In a closed coalition with fixed honest bridge flow (Scenario 2), the reduction in colluder trust share may be limited or zero in accordance with the Closed-Set Invariance Theorem:
  $$\sum_{c \in C} t_c = \left(\frac{1 - \alpha}{\alpha}\right) \sum_{h \in H} t_h \sum_{c \in C} C'_{hc}$$
- **Evaluation Status:** Diagnostic test. If $T_{C, \text{EW}} \approx T_{C, \text{Vanilla}}$, this confirms theoretical invariance rather than implementation failure.

### Hypothesis H-4 (Honest Community Integrity)
- **Statement:** In honest reciprocal communities (Scenario 9), EW-EigenTrust maintains honest trust share $\ge 0.99$ with zero false accusations or revocations.
- **Success Criterion:** Honest trust share $\ge 0.99$, zero false accusations.

---

## 7. Exclusion Rules & Data Integrity

1. **No Outlier Truncation:** All 20 trials per scenario must be included in the statistical summaries.
2. **Deterministic Seed Control:** Any trial that diverges in node admission or sequence order between paired comparisons is discarded and re-run.
3. **Parameter Lock:** Algorithm parameters are locked to v1.8 specification defaults:
   $\alpha = 0.15, \text{tol} = 10^{-6}, \text{max\_iter} = 100, K_{\max} = 10.0, \lambda_{\text{sat}} = 0.50, \mu_{\text{unverified}} = 0.10, \mu_{\text{referenced}} = 0.25, \tau = 86400.0\text{ s}$.
   No parameter tuning is permitted during the Phase 8.2 evaluation.
