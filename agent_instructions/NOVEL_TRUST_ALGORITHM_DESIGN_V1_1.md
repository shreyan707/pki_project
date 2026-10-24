# Novel Trust Algorithm Design v1.1: Evidence-Weighted EigenTrust with Topology-Aware Collusion Damping (EW-EigenTrust)

**Version:** 1.1.0-CORRECTED  
**Phase:** Phase 7.1 (Mathematical Correction & Implementation Readiness)  
**Author:** Candidate Shreyan Nayak (23BKT0039)  
**Security Classification:** Strict Research Specification  
**Supercedes:** `NOVEL_TRUST_ALGORITHM_DESIGN.md` (v1.0.0 preserved as historical record)  

---

## 1. Problem Statement & Baseline Vulnerability

In decentralized peer-to-peer file-sharing systems, trust management must differentiate between authentic content providers and malicious adversaries. The existing Phase 1–6 baseline protocol couples cryptographic transaction evidence (signed manifests, Merkle tree inclusion proofs, and dual-signed bilateral receipts) with the **Vanilla EigenTrust** algorithm (Kamvar et al., 2003):

$$\mathbf{t}^{(k+1)} = (1 - \alpha) C^T \mathbf{t}^{(k)} + \alpha \mathbf{p}$$

where $C_{ij} = \frac{\max(S_{ij}, 0)}{\sum_k \max(S_{ik}, 0)}$ and $\mathbf{p}$ is the stationary distribution over pre-trusted supernodes.

### The Connected-Collusion Vulnerability
As empirically demonstrated in Phase 6:
1. **Isolated Sybil Clusters:** Completely disconnected Sybil cliques exchanging mutual $+1.00$ upvotes are effectively damped by vanilla EigenTrust to near-zero collective trust share ($\text{TrustShare} = 0.00\%$) because no random-walk paths link pre-trusted supernodes to the Sybil subgraph.
2. **Connected Collusion with Honest Bridging:** When colluding Sybil nodes establish legitimate-looking bridging interactions with honest nodes (even at low probabilities $p_{\text{bridge}} \in [0.05, 0.40]$), stationary probability mass leaks across the bridge into the collusive clique. Inside the clique, dense reciprocal upvoting traps random-walk transitions. Consequently, colluders achieve an inflated trust share proportional to bridge volume, which vanilla EigenTrust cannot distinguish from authentic community reputation.

---

## 2. Research Questions

- **Primary Research Question:**  
  *How can decentralized trust propagation incorporate cryptographic transaction evidence and interaction topology into local edge weighting such that coordinated collusive cliques are damped without penalizing legitimate, highly-connected peer communities?*
- **RQ1 (Bridging Vulnerability):** Does damping mutual reciprocal trust based on counterparty interaction diversity significantly reduce collusive trust gain across bridge probabilities $p_{\text{bridge}} \in [0.05, 0.40]$ compared to vanilla EigenTrust?
- **RQ2 (False-Positive Discrimination):** Can a topology-aware evidence-weighting mechanism preserve the trust share of legitimate, dense, specialized file-sharing communities within a 5% margin of vanilla EigenTrust?
- **RQ3 (Computational Overhead):** Can topology-aware evidence weighting be computed with localized, sub-quadratic computational complexity ($O(|\mathcal{E}|)$) per transaction round without requiring global graph clustering?

---

## 3. Threat Model & Attacker Capabilities

The attack model formalizes **Connected Collusion** while remaining strictly compliant with `SECURITY_MODEL.md` v2.2.0-FROZEN:

### A. Adversary Capabilities
- Can generate valid Layer 1 identities and solve required Proof-of-Work nonces.
- Can establish valid Layer 2 mesh connections and register into the network.
- Can coordinate mutually beneficial $+1.00$ bilateral receipts within coalition $\mathcal{A}$ without defecting.
- Can deliver authentic content to honest peers at bridging probability $p_{\text{bridge}}$ to earn legitimate positive receipts.
- Can selectively deliver poisoned chunks to victim peers outside $\mathcal{A}$.

### B. Cryptographic Boundaries (Infeasible Adversary Actions)
- **Cannot forge signatures:** Cannot forge Ed25519 signatures of honest peers or pre-trusted supernodes.
- **Cannot corrupt Merkle proofs:** Cannot forge valid Merkle inclusion proofs for tampered bytes without finding a SHA-256 collision or pre-image.
- **Cannot double-spend receipts:** Cannot re-submit committed receipts past the processed-evidence journal ($L_{\text{local}} / L_{\text{sim}}$).
- **Cannot forge bilateral co-signatures:** Cannot unilaterally invent a positive receipt with an honest peer without the honest peer's private key.
- **Sub-threshold control:** Colluders control strictly fewer than $m$ supernodes ($K_{\text{supernode}} < m$, where $m=3$ of $n=5$).

---

## 4. Evidence Weight Formulation ($W_{ij}$)

Unlike v1.0, which incorrectly weighted edges by raw receipt counts, **v1.1 grounds evidence weighting strictly on protocol-observable, verified Merkle deliveries, dispute ratios, and certified fault records**.

### 4.1 Committed Evidence Extraction
For any directed pair $(i, j)$ in peer set $\mathcal{V}$, peer $i$ extracts from its local evidence journal all committed entries where $i$ evaluated $j$:
$$\mathcal{E}_{ij} = \{ e \in L_{\text{local}} \mid e.\text{details}["\text{client\_did}"] = i \land e.\text{details}["\text{server\_did}"] = j \}$$

The entries are partitioned into positive receipts $\mathcal{E}_{ij}^{+}$, negative dispute receipts $\mathcal{E}_{ij}^{-}$, and certified fault records $\mathcal{F}_{ij}$.

### 4.2 Mathematical Formulation
$$W_{ij} = \tanh\left(\frac{\lambda_{\text{sat}} \cdot E_{\text{pos}}(i, j)}{2}\right) \cdot \gamma_{\text{dispute}}(i, j) \cdot \gamma_{\text{fault}}(i, j)$$

where:
1. **Positive Verified Evidence ($E_{\text{pos}}$):**
   $$E_{\text{pos}}(i, j) = \sum_{e \in \mathcal{E}_{ij}^{+}} \gamma_{\text{root}}(e) \cdot \gamma_{\text{time}}(t_{\text{ref}} - t_e)$$
   - $\gamma_{\text{root}}(e) = 1.0$ if the receipt commits to a valid, non-zero Merkle root matching a known signed `ContentManifest`.
   - $\gamma_{\text{root}}(e) = \mu_{\text{unverified}} = 0.15$ if the receipt is signed but references an unindexed/dummy root (prevents Sybils from grinding ungrounded receipts to inflate weight).
   - $\gamma_{\text{time}}(\Delta t) = \exp(-\Delta t / \tau)$ with $\tau = 86400.0\text{ s}$ (1 day). If $\Delta t < 0$, $\gamma_{\text{time}} = 1.0$.
2. **Dispute Penalty ($\gamma_{\text{dispute}}$):**
   $$\gamma_{\text{dispute}}(i, j) = \max\left(0.0, \, 1.0 - \frac{2 \cdot |\mathcal{E}_{ij}^{-}|}{|\mathcal{E}_{ij}^{+}| + 1}\right)$$
   If mutual disputes equal or exceed $50\%$ of positive interactions, $\gamma_{\text{dispute}} \to 0.0$.
3. **Certified Fault Nullification ($\gamma_{\text{fault}}$):**
   $$\gamma_{\text{fault}}(i, j) = \begin{cases} 
   0.0 & \text{if } |\mathcal{F}_{ij}| > 0 \text{ or peer } j \text{ is } \text{SUSPECTED}/\text{REVOKED} \\
   1.0 & \text{otherwise}
   \end{cases}$$
4. **Saturation Parameter:**
   $\lambda_{\text{sat}} = 0.25$ enforces concave diminishing returns:
   - $0.0 \le W_{ij} < 1.0$.
   - A single verified interaction yields $W_{ij} \approx \tanh(0.125) \approx 0.124$.
   - Ten verified interactions yield $W_{ij} \approx \tanh(1.25) \approx 0.848$.
   - Grinding 1,000 interactions asymptotically saturates at $1.0$, preventing infinite trust accumulation.

---

## 5. Topology-Aware Collusion Damping Matrix ($\Omega_{ij}$)

To penalize collusive cliques that establish reciprocal upvoting rings, the algorithm computes a **Localized Topological Collusion Damping Factor** $\Omega_{ij} \in [\epsilon_{\text{floor}}, 1.0]$.

### 5.1 Outgoing Positive Base Ratings ($A$)
Self-edges are strictly zero ($A_{ii} = 0$). For $i \ne j$:
$$A_{ij} = W_{ij} \cdot \max(S_{ij}, 0)$$

### 5.2 Outgoing Counterparty Interaction Entropy ($H_i$)
For any node $i \in \mathcal{V}$:
- If $\sum_{k \ne i} A_{ik} = 0 \implies H_i = 0.0$.
- Otherwise, define the outgoing distribution over distinct peers $k \ne i$:
  $$p_{ik} = \frac{A_{ik}}{\sum_{m \ne i} A_{im}}$$
  The normalized Shannon entropy is:
  $$H_i = -\frac{1}{\ln(\max(2, |\mathcal{V}| - 1))} \sum_{k \ne i, p_{ik} > 0} p_{ik} \ln(p_{ik})$$
  - Range: $0.0 \le H_i \le 1.0$.
  - Low entropy ($H_i \to 0$) indicates ratings concentrated in 1 or 2 partners.
  - High entropy ($H_i \to 1$) indicates ratings distributed broadly across the network.

### 5.3 Regularized Reciprocity Symmetry ($\rho_{ij}$)
For any pair $(i, j)$:
$$\rho_{ij} = \frac{2 \cdot \min(A_{ij}, A_{ji})}{A_{ij} + A_{ji} + \delta_{\text{reg}}}$$
where $\delta_{\text{reg}} = 2.0$.
- **Regularization:** If $A_{ij} = 1, A_{ji} = 1 \implies \rho_{ij} = \frac{2}{4} = 0.50$ (prevents low-volume noise from registering as 100% collusion).
- **Asymmetric Provider Immunity:** If $A_{ji} \gg 0$ but $A_{ij} = 0$ (pure content uploader / seedbox), $\min(A_{ij}, A_{ji}) = 0 \implies \rho_{ij} = 0.0$.

### 5.4 Closed-Loop Suspicion Index ($\sigma_{ij}$) & Damping Factor ($\Omega_{ij}$)
$$\sigma_{ij} = \rho_{ij} \cdot \left(1.0 - \min(H_i, H_j)\right)^{\beta_{\text{entropy}}}$$
$$\Omega_{ij} = \max\left(\epsilon_{\text{floor}}, \, 1.0 - \theta_{\text{penalty}} \cdot \sigma_{ij}\right)$$

**Default Parameters:**
- $\beta_{\text{entropy}} = 2.0$ (entropy sensitivity exponent)
- $\theta_{\text{penalty}} = 0.85$ (penalty scale)
- $\epsilon_{\text{floor}} = 0.10$ (connectivity floor ensuring $\Omega_{ij} > 0$)

---

## 6. Complete Mathematical Iteration (EW-EigenTrust)

### Step 1: Effective Trust Matrix ($S'$)
$$S'_{ij} = \Omega_{ij} \cdot A_{ij} = \Omega_{ij} \cdot W_{ij} \cdot \max(S_{ij}, 0) \quad \text{for } i \ne j, \quad S'_{ii} = 0$$

### Step 2: Stochastic Matrix Normalization ($C'$)
For each row $i \in \{1, \dots, n\}$:
$$D_i = \sum_{k=1}^n S'_{ik}$$
$$C'_{ij} = \begin{cases}
\frac{S'_{ij}}{D_i} & \text{if } D_i > 0 \\
p_j & \text{if } D_i = 0 \quad (\text{Dangling Node})
\end{cases}$$
where $\mathbf{p} = [p_1, \dots, p_n]^T$ is the pre-trusted restart vector:
$$p_j = \begin{cases}
\frac{1}{|\mathcal{S}_{\text{valid}}|} & \text{if } j \in \mathcal{S}_{\text{valid}} = \mathcal{S}_{\text{supernodes}} \cap \mathcal{V} \\
\frac{1}{n} & \text{if } |\mathcal{S}_{\text{valid}}| = 0 \quad (\text{Fallback}) \\
0 & \text{otherwise}
\end{cases}$$

### Step 3: Power Iteration Operator
Initialize $\mathbf{t}^{(0)} = \mathbf{p}$. For $k = 0, 1, 2, \dots$:
$$\mathbf{t}^{(k+1)} = (1 - \alpha) (C')^T \mathbf{t}^{(k)} + \alpha \mathbf{p}$$
where $\alpha = 0.15$ is the restart damping probability.

### Step 4: Convergence Guarantee
- **Contraction Factor:** $\|T(\mathbf{u}) - T(\mathbf{v})\|_1 \le (1 - \alpha) \|\mathbf{u} - \mathbf{v}\|_1$.
- **Theorem:** By the Banach Fixed-Point Theorem, the iteration has a **unique fixed point** $\mathbf{t}^* \in \Delta^n$ and converges geometrically with rate $O((1 - \alpha)^k)$.
- **Termination:** Iterate until $\|\mathbf{t}^{(k+1)} - \mathbf{t}^{(k)}\|_1 < 10^{-6}$ or $k \ge 50$.

---

## 7. Implementation-Ready Pseudocode

```python
"""
Evidence-Weighted EigenTrust with Topology-Aware Collusion Damping (EW-EigenTrust v1.1)
Implementation Contract for Phase 8.
"""

import math
import numpy as np
from typing import List, Dict, Tuple, Optional, Any, Set


def compute_ew_eigentrust(
    peers: List[str],
    supernodes: List[str],
    raw_s_matrix: Dict[Tuple[str, str], float],
    evidence_journal: Any,  # LocalEvidenceJournal / SimulatorCanonicalJournal
    known_manifest_roots: Optional[Set[str]] = None,
    alpha: float = 0.15,
    lambda_sat: float = 0.25,
    mu_unverified: float = 0.15,
    beta_entropy: float = 2.0,
    theta_penalty: float = 0.85,
    epsilon_floor: float = 0.10,
    delta_reg: float = 2.0,
    max_iter: int = 50,
    tol: float = 1e-6,
    reference_time: Optional[float] = None
) -> Dict[str, float]:
    """
    Computes global trust scores using Evidence-Weighted EigenTrust (EW-EigenTrust v1.1).
    Strictly deterministic, row-stochastic, and compatible with the frozen protocol.
    """
    n = len(peers)
    if n == 0:
        return {}

    sorted_peers = sorted(peers)
    peer_to_idx = {did: idx for idx, did in enumerate(sorted_peers)}
    valid_supernodes = [sn for sn in supernodes if sn in peer_to_idx]
    manifest_roots = {r.lower() for r in (known_manifest_roots or set())}

    # 1. Construct pre-trusted restart vector p
    p = np.zeros(n, dtype=np.float64)
    if valid_supernodes:
        sn_weight = 1.0 / len(valid_supernodes)
        for sn in valid_supernodes:
            p[peer_to_idx[sn]] = sn_weight
    else:
        p.fill(1.0 / n)

    # 2. Extract Evidence Weights W_ij and Positive Ratings S_pos
    W = np.zeros((n, n), dtype=np.float64)
    S_pos = np.zeros((n, n), dtype=np.float64)

    for (src, dst), score in raw_s_matrix.items():
        if src in peer_to_idx and dst in peer_to_idx and src != dst and score > 0:
            i, j = peer_to_idx[src], peer_to_idx[dst]
            S_pos[i, j] = score

            # Query evidence journal for committed entries between (src, dst)
            entries = []
            if hasattr(evidence_journal, "get_pair_evidence"):
                entries = evidence_journal.get_pair_evidence(src, dst)
            elif hasattr(evidence_journal, "_entries"):
                # Direct traversal fallback for existing journal data structures
                for key, j_entry in evidence_journal._entries.items():
                    d = j_entry.details
                    if d.get("client_did") == src and d.get("server_did") == dst:
                        entries.append(j_entry)

            # Classify entries
            n_pos = 0.0
            n_neg = 0.0
            has_certified_fault = False

            for entry in entries:
                if entry.entry_type == "FAULT_EVIDENCE":
                    has_certified_fault = True
                elif entry.entry_type == "RECEIPT":
                    rating_val = entry.details.get("rating", 1.0)
                    if rating_val > 0:
                        m_root = entry.details.get("merkle_root", "").lower()
                        # Verify Merkle root backing
                        gamma_root = 1.0 if (m_root and m_root in manifest_roots) else mu_unverified
                        n_pos += gamma_root
                    else:
                        n_neg += 1.0

            if has_certified_fault:
                W[i, j] = 0.0
            else:
                gamma_dispute = max(0.0, 1.0 - (2.0 * n_neg / (n_pos + 1.0)))
                w_sat = math.tanh(lambda_sat * n_pos / 2.0)
                W[i, j] = max(0.0, min(1.0, w_sat * gamma_dispute))

    # Base positive effective interaction matrix A
    A = W * S_pos

    # 3. Compute Outgoing Interaction Entropy H_i
    H = np.zeros(n, dtype=np.float64)
    denom_norm = math.log(max(2, n - 1))
    for i in range(n):
        row_sum = np.sum(A[i, :])
        if row_sum > 0:
            p_dist = A[i, :] / row_sum
            nonzero_p = p_dist[p_dist > 0]
            entropy = -np.sum(nonzero_p * np.log(nonzero_p))
            H[i] = min(1.0, max(0.0, entropy / denom_norm))
        else:
            H[i] = 0.0

    # 4. Compute Reciprocity and Topological Damping Matrix Omega_ij
    Omega = np.ones((n, n), dtype=np.float64)
    for i in range(n):
        for j in range(n):
            if i != j and A[i, j] > 0:
                a_ij = A[i, j]
                a_ji = A[j, i]
                # Regularized reciprocity symmetry
                rho_ij = (2.0 * min(a_ij, a_ji)) / (a_ij + a_ji + delta_reg)
                # Closed-loop suspicion index
                min_entropy = min(H[i], H[j])
                sigma_ij = rho_ij * math.pow(1.0 - min_entropy, beta_entropy)
                Omega[i, j] = max(epsilon_floor, 1.0 - (theta_penalty * sigma_ij))

    # 5. Build Effective Matrix S_prime and Stochastic Matrix C_prime
    S_prime = Omega * A
    C_prime = np.zeros((n, n), dtype=np.float64)

    for i in range(n):
        row_total = np.sum(S_prime[i, :])
        if row_total > 0:
            C_prime[i, :] = S_prime[i, :] / row_total
        else:
            C_prime[i, :] = p  # Dangling node restart to pre-trusted seed

    # 6. Stationary Power Iteration
    t = p.copy()
    C_prime_T = C_prime.T

    for iteration in range(max_iter):
        t_next = (1.0 - alpha) * (C_prime_T @ t) + (alpha * p)
        if np.sum(np.abs(t_next - t)) < tol:
            t = t_next
            break
        t = t_next

    # Ensure exact probability simplex normalization
    t_sum = np.sum(t)
    if t_sum > 0:
        t = t / t_sum

    return {sorted_peers[i]: float(t[i]) for i in range(n)}
```

---

## 8. False-Positive Analysis & Community Defense

### A. Dedicated Asymmetric Seedboxes
- High upload volume, zero download volume ($A_{ji} \gg 0$, $A_{ij} = 0$).
- $\min(A_{ij}, A_{ji}) = 0 \implies \rho_{ij} = 0.0$.
- $\sigma_{ij} = 0 \implies \Omega_{ij} = 1.0$ (Zero penalty mathematically guaranteed).

### B. Specialized Academic Peer Group
- Small cluster of nodes trading rare datasets frequently with each other.
- Periodic downloads served to external peers or supernode auditors ensure $H_i \ge 0.35$.
- Because $(1 - H)^{\beta}$ decays quadratically ($\beta = 2.0$), $\sigma_{ij} \le 0.65^2 \approx 0.42$.
- Damping factor $\Omega_{ij} \ge 1.0 - (0.85 \times 0.42) \approx 0.64$, maintaining substantial community flow while preventing closed-loop explosion.

### C. Low-Volume Emerging Peers
- Initial reciprocal transaction ($A_{ij} = 1, A_{ji} = 1$).
- Regularization $\delta_{\text{reg}} = 2.0$ yields $\rho_{ij} = \frac{2}{4} = 0.50$ instead of $1.0$.
- Concave evidence weight $W_{ij} \approx \tanh(0.125) \approx 0.124$ naturally dampens early weight without premature blacklisting.

---

## 9. Implementation Mapping for Phase 8

| Component | Target Location | Implementation Action |
| :--- | :--- | :--- |
| **Journal Query API** | `src/layer3_eigentrust.py` (`LocalEvidenceJournal`) | Add non-breaking helper `get_pair_evidence(client_did, server_did)`. |
| **Algorithm Engine** | `src/layer3_eigentrust.py` | Add `EvidenceWeightedEigenTrustEngine` as a clean subclass or companion class to `EigenTrustEngine`. |
| **Experiment Runner** | `experiments/config.py` & `experiments/scenarios.py` | Add `"ew_eigentrust"` to `ExperimentConfig.trust_baseline` and dispatch in `ExperimentTrialRunner`. |
| **Ablation Suite** | `experiments/runner.py` | Configure 5-way ablation sweeps (Vanilla, Weight-only, Topology-only, Full EW, Local). |
| **Unit & Property Tests** | `tests/test_trust_framework.py` | Add test cases validating Acceptance Criteria AC-1 through AC-10. |

---

## 10. Evidentiary Claim Discipline

- **[STANDARD]:** Ed25519 signatures, full 64-hex DIDs, PoW admission, SHA-256 Merkle trees, Shamir secret sharing, vanilla EigenTrust power iteration.
- **[IMPLEMENTED]:** 7-stage bilateral evidence pipeline, processed-evidence journal ($L_{\text{local}} / L_{\text{sim}}$), certified Merkle contradiction attribution, 3-of-5 supernode quorum revocation.
- **[PROPOSED]:** Bounded concave evidence-weighting function $W_{ij}$, counterparty interaction entropy $H_i$, regularized reciprocity index $\rho_{ij}$, and topology-aware damping factor $\Omega_{ij}$.
- **[HYPOTHESIS]:** Hypotheses $H_1$ through $H_4$ concerning collusive trust reduction and honest community preservation.
- **[MEASURED]:** Empirical metrics reported in `PHASE6_EXPERIMENT_REPORT.md` (e.g. 0% replay acceptance across 495 trials).
- **[NOT ESTABLISHED]:** Universal collusion immunity against arbitrary Byzantine colluders performing majority honest work across all network partitions.
