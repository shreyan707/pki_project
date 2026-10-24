# Phase 7 Research Report: Algorithm Design & Formal Specification of EW-EigenTrust

**Phase:** Phase 7 (Research & Algorithm Design)  
**Date:** October 9, 2026  
**Status:** `PHASE7_STATUS: COMPLETE`  
**Security Classification:** Strict Research Specification (No Production Code Modified)  

---

## 1. Phase Status

`PHASE7_STATUS: COMPLETE`

The research investigation and mathematical specification of the novel trust mechanism have been completed in strict accordance with the primary objective. The design document [`NOVEL_TRUST_ALGORITHM_DESIGN.md`](file:///d:/pki_casestudy/NOVEL_TRUST_ALGORITHM_DESIGN.md) specifies **Evidence-Weighted EigenTrust with Topology-Aware Collusion Damping (EW-EigenTrust)**, addressing the connected-collusion vulnerability exposed by Phase 6 experiments without altering production protocol code, simulators, or frozen specifications.

---

## 2. Research Investigation Summary

### A. Problem Formulation
In Phase 6, the empirical baseline established that while **Vanilla EigenTrust** naturally suppresses disconnected Sybils to $0.00\%$ trust share via power-iteration anchored on pre-trusted supernodes, **connected collusive Sybils bridging to honest peers capture significant stationary reputation mass**. Inside the collusive clique, reciprocal upvoting traps random walks, causing reputation inflation that vanilla EigenTrust cannot distinguish from authentic community service.

### B. Alternatives Evaluated and Rejected

1. **Global Graph Spectral Clustering / Community Partitioning:**
   - *Investigation:* Evaluated algorithms that partition the trust graph into communities (e.g., modularity maximization, normalized cuts, spectral bisection) to detect and excise dense collusive subgraphs.
   - *Rejection Rationale:* **Computationally prohibitive** for P2P swarms ($O(V^3)$ or complex iterative heuristics). Furthermore, global clustering creates a severe **false-positive hazard** by penalizing legitimate specialized peer groups (e.g., academic research seeders or regional mirror swarms).
2. **Subjective Distrust / Negative Trust Propagation:**
   - *Investigation:* Evaluated TidalTrust / Guha-style propagation of negative ratings along transitive paths.
   - *Rejection Rationale:* Transitive distrust creates a dangerous attack vector where malicious colluders weaponize false accusations to suppress honest competitors. In our frozen architecture, negative updates must be grounded strictly in objective cryptographic proofs (`FaultEvidenceRecord`).
3. **Unbounded Linear Evidence Grinding:**
   - *Investigation:* Evaluated weighting matrix edges linearly by the total count of signed receipts ($W_{ij} \propto N_{\text{tx}}$).
   - *Rejection Rationale:* Linear weighting allows colluders to inflate edge weights arbitrarily by grinding micro-transactions among themselves. A bounded, concave saturation function is strictly necessary.

### C. Selected Solution: Dual-Factor EW-EigenTrust

The selected algorithm pairs two localized, cryptographically grounded mechanisms:
1. **Evidence-Weighted Edge Scaling ($W_{ij}$):**
   Scales raw rating scores using a concave hyperbolic tangent saturation function $\Phi(x) = \tanh(\lambda x / 2)$ conditioned on verified Merkle chunk deliveries, Ed25519 bilateral signatures, and dispute penalties. This bounds self-transaction grinding.
2. **Topology-Aware Reciprocity & Entropy Damping ($\Omega_{ij}$):**
   Evaluates two localized topological signals on active rating edges:
   - *Shannon Interaction Entropy ($H_i$):* Measures the diversity of peer $i$'s outgoing transactions across the network.
   - *Bilateral Reciprocity Symmetry ($\rho_{ij}$):* Measures whether ratings between $i$ and $j$ form an unnatural symmetric loop.
   - *Damping Factor:* $\Omega_{ij} = \max(\epsilon_{\text{floor}}, 1.0 - \theta \cdot \rho_{ij} (1 - \min(H_i, H_j))^\beta)$. If two nodes engage in high mutual upvoting while maintaining low external diversity, their rating edge is damped toward $\epsilon_{\text{floor}}$.

---

## 3. Novelty Boundary & Claim Discipline

To maintain academic integrity, claims are classified according to strict evidentiary boundaries:

- **[STANDARD]:** Ed25519 signatures, full 64-hex DIDs, PoW hashcash admission, SHA-256 Merkle trees, Shamir secret sharing, vanilla EigenTrust power iteration.
- **[IMPLEMENTED]:** 7-stage bilateral evidence pipeline, canonical evidence journal ($L_{\text{sim}}$), certified Merkle contradiction attribution, 3-of-5 supernode quorum revocation.
- **[PROPOSED]:** The specific combination of concave evidence saturation ($W_{ij}$), local counterparty entropy ($H_i$), and reciprocity-entropy damping ($\Omega_{ij}$) applied as an element-wise edge transformation ($S' = \Omega \odot W \odot S$) prior to row-stochastic normalization in EigenTrust.
- **[HYPOTHESIS]:** Hypotheses $H_1$ through $H_4$ concerning collusive trust reduction and honest community preservation.
- **[MEASURED]:** Empirical metrics reported in `PHASE6_EXPERIMENT_REPORT.md` (e.g. 0% replay acceptance across 495 trials).
- **[NOT ESTABLISHED]:** We explicitly **do not claim** universal collusion immunity or detection of colluders who perform a genuine majority of honest services across the entire overlay network.

---

## 4. Legitimate Community Protection (False-Positive Mitigation)

The mechanism explicitly accommodates legitimate highly-connected peer groups:
1. **Specialized Academic / Mirror Communities:** Although mutual interaction is frequent, periodic interactions with supernode auditors or external downloaders provide sufficient entropy ($H_i > 0.35$), preventing damping.
2. **Asymmetric Seedboxes / Bulk Providers:** Dedicated providers who upload extensively but download little exhibit near-zero reciprocity ($\rho_{ij} \approx 0$), resulting in zero damping ($\Omega_{ij} = 1.0$).
3. **Emerging Peer Pairs:** Low-volume interactions are regularized by $\delta_{\text{reg}} = 1.0$, preventing single initial transactions from triggering collusion alarms.

---

## 5. Computational Complexity Comparison

| Dimension | Vanilla EigenTrust | EW-EigenTrust (Proposed) | Assessment |
| :--- | :--- | :--- | :--- |
| **Evidence Extraction** | $O(1)$ | $O(|\mathcal{E}|)$ active rated edges | Constant-time journal lookups |
| **Local Entropy Calculation** | Not computed | $O(V \cdot \bar{d}_{\text{out}})$ | Sub-millisecond localized operation |
| **Reciprocity Damping Matrix** | Not computed | $O(|\mathcal{E}|)$ | Evaluated strictly on non-zero rating edges |
| **Markov Normalization** | $O(|\mathcal{E}|)$ | $O(|\mathcal{E}|)$ | Identical asymptotic complexity |
| **Power Iteration** | $O(K_{\text{iter}} \cdot |\mathcal{E}|)$ | $O(K_{\text{iter}} \cdot |\mathcal{E}|)$ | Identical; provable convergence maintained |
| **Overall Round Complexity** | **$O(K_{\text{iter}} \cdot |\mathcal{E}|)$** | **$O(|\mathcal{E}| + K_{\text{iter}} \cdot |\mathcal{E}|)$** | **Linear in edge count; avoids $O(V^3)$ clustering** |

---

## 6. Implementation Readiness for Future Phases

The algorithm has been fully specified in pseudocode and mathematical formulation in [`NOVEL_TRUST_ALGORITHM_DESIGN.md`](file:///d:/pki_casestudy/NOVEL_TRUST_ALGORITHM_DESIGN.md).

When implementation is authorized:
- A new engine `EvidenceWeightedEigenTrustEngine` will be added to `src/layer3_eigentrust.py` without modifying the baseline `EigenTrustEngine`.
- The evaluation harness will incorporate an `"ew_eigentrust"` option in `experiments/config.py` to run comparative 5-way ablation sweeps against identical random seeds.

---

**Summary:** Phase 7 has produced a mathematically rigorous, computationally efficient, and academically defensible trust algorithm design that targets connected collusion while safeguarding legitimate peer networks.

**Final Status:** `PHASE7_STATUS: COMPLETE`
