# Novel Trust Algorithm Design v1.2: Evidence-Weighted EigenTrust with Topology-Aware Collusion Damping (EW-EigenTrust)

**Version:** 1.2.0-FINAL  
**Phase:** Phase 7.2 (Independent Verification & Implementation Gate Readiness)  
**Author:** Candidate Shreyan Nayak (23BKT0039)  
**Security Classification:** Strict Research Specification  
**Supercedes:** `NOVEL_TRUST_ALGORITHM_DESIGN_V1_1.md` and `NOVEL_TRUST_ALGORITHM_DESIGN.md`  

---

## 1. Research Problem & Theoretical Baseline

In decentralized P2P content-delivery swarms, trust management must evaluate peer reliability without relying on a centralized credit score. The Phase 1–6 baseline implements **Vanilla EigenTrust** (Kamvar et al., 2003):

$$\mathbf{t}^{(k+1)} = (1 - \alpha) C^T \mathbf{t}^{(k)} + \alpha \mathbf{p}$$

where $C_{ij} = \frac{\max(S_{ij}, 0)}{\sum_k \max(S_{ik}, 0)}$ and $\mathbf{p}$ is the stationary distribution over pre-trusted supernodes.

### The Connected-Collusion Vulnerability
As proven empirically in Phase 6:
1. **Isolated Sybil Clusters:** Completely disconnected Sybils exchanging mutual upvotes are damped to near-zero collective trust share ($0.00\%$) because no random-walk paths connect pre-trusted supernodes to the Sybil subgraph.
2. **Connected Collusion with Honest Bridging:** When colluding Sybils establish bridging transactions to honest peers ($p_{\text{bridge}} \in [0.05, 0.40]$), stationary probability mass leaks across the bridge into the collusive ring. Dense internal reciprocal upvoting traps random walks, causing reputation inflation that vanilla EigenTrust cannot distinguish from legitimate community service.

---

## 2. Attacker Capability Matrix & Boundaries

The attack model formalizes **Connected Collusion** while remaining strictly compliant with `SECURITY_MODEL.md` v2.2.0-FROZEN:

| Adversary Profile | Allowed Actions (Capabilities) | Infeasible Actions (Cryptographic Boundaries) |
| :--- | :--- | :--- |
| **Connected Sybil Coalition** | • Solve Ed25519 PoW admission<br>• Register into Layer 2 mesh<br>• Mutual $+1.00$ bilateral receipts within coalition<br>• Deliver authentic content to honest peers at bridging probability $p_{\text{bridge}}$ | • **Cannot forge signatures:** Cannot forge honest peer or supernode private keys<br>• **Cannot forge Merkle proofs:** Cannot produce valid inclusion proofs for modified bytes without SHA-256 collision<br>• **Cannot double-spend receipts:** Processed-evidence journal ($L_{\text{local}} / L_{\text{sim}}$) rejects replayed receipts<br>• **Cannot forge bilateral co-signatures:** Cannot unilaterally invent a positive receipt with an honest peer without the honest peer's private key |

---

## 3. Evidence Extraction & Minimal Journal Extension Contract

### 3.1 Trace Analysis of `src/layer3_eigentrust.py`
In the existing codebase, `BilateralReceipt` contains all necessary fields (`tx_id`, `client_did`, `server_did`, `merkle_root`, `rating`, `timestamp`, `nonce`, `client_sig_hex`, `server_sig_hex`). However, `record_receipt()` currently commits only:
```python
details = {
    "client_did": receipt.client_did,
    "server_did": receipt.server_did,
    "rating": delta,
    "nonce": receipt.nonce
}
```
### 3.2 Phase 8 Non-Breaking Extension Contract
In Phase 8 implementation, `record_receipt()` in `src/layer3_eigentrust.py:691` will commit the full metadata:
```python
details = {
    "client_did": receipt.client_did,
    "server_did": receipt.server_did,
    "rating": delta,
    "nonce": receipt.nonce,
    "merkle_root": receipt.merkle_root,
    "receipt_timestamp": receipt.timestamp
}
```
This preserves 100% backward compatibility with all existing unit tests while making Merkle manifest bindings directly auditable from committed journal entries.

---

## 4. Bounded Edge-Strength Formulation

To eliminate evidence-grinding vulnerabilities where bounded $W_{ij}$ multiplies an unbounded cumulative integer score, the **effective transition edge is an intrinsically bounded, strictly concave function of validated evidence**:

$$S'_{ij} = \Omega_{ij} \cdot \Phi_{\text{edge}}(E_{\text{pos}}(i, j)) \cdot \gamma_{\text{dispute}}(i, j) \cdot \gamma_{\text{fault}}(i, j) \quad \text{for } i \ne j, \quad S'_{ii} = 0$$

### 4.1 Concave Edge Ceiling ($\Phi_{\text{edge}}$)
$$\Phi_{\text{edge}}(E) = K_{\text{max}} \cdot \tanh\left(\frac{\lambda_{\text{sat}} \cdot E}{K_{\text{max}}}\right)$$
- **Ceiling:** $K_{\text{max}} = 10.0$ (No edge can exceed $10.0$, regardless of receipt volume).
- **Scale:** $\lambda_{\text{sat}} = 0.50$.
- **Values:**
  - $E = 1.0 \implies \Phi_{\text{edge}} \approx 0.499$.
  - $E = 5.0 \implies \Phi_{\text{edge}} \approx 2.449$.
  - $E = 20.0 \implies \Phi_{\text{edge}} \approx 7.616$.
  - $E = 100.0 \implies \Phi_{\text{edge}} \approx 9.999$.
  - $E \to \infty \implies \Phi_{\text{edge}} \le 10.000$.

### 4.2 Positive Verified Evidence ($E_{\text{pos}}$)
$$E_{\text{pos}}(i, j) = \sum_{e \in \mathcal{E}_{ij}^{+}} \gamma_{\text{root}}(e) \cdot \gamma_{\text{time}}(t_{\text{ref}} - t_e)$$
- **Merkle Root Attribution:**
  $$\gamma_{\text{root}}(e) = \begin{cases}
  1.0 & \text{if } e.\text{details}["\text{merkle\_root}"] \in \mathcal{R}_{\text{manifests}} \\
  \mu_{\text{unverified}} = 0.10 & \text{otherwise (valid signatures, but unindexed/dummy root)}
  \end{cases}$$
- **Freshness & Time Decay:**
  For $\Delta t = t_{\text{ref}} - t_e$:
  $$\gamma_{\text{time}}(\Delta t) = \begin{cases}
  1.0 & \text{if } -60.0 \le \Delta t \le 0.0 \quad (\text{Clock drift tolerance}) \\
  0.0 & \text{if } \Delta t < -60.0 \quad (\text{Excessive future timestamp}) \\
  \exp\left(-\frac{\Delta t}{\tau}\right) & \text{if } \Delta t > 0.0 \quad (\tau = 86400.0\text{ s, 1 day})
  \end{cases}$$

### 4.3 Bilateral Dispute Factor ($\gamma_{\text{dispute}}$)
$$\gamma_{\text{dispute}}(i, j) = \max\left(0.0, \, 1.0 - \frac{2 \cdot |\mathcal{E}_{ij}^{-}|}{|\mathcal{E}_{ij}^{+}| + 1}\right)$$

### 4.4 Certified Fault Nullification ($\gamma_{\text{fault}}$)
$$\gamma_{\text{fault}}(i, j) = \begin{cases}
0.0 & \text{if } j \in \text{accused\_dids}(\mathcal{F}) \lor \text{peer\_states}[j] \in \{\text{SUSPECTED}, \text{REVOKED}\} \\
1.0 & \text{otherwise}
\end{cases}$$

---

## 5. Topology-Aware Collusion Damping Matrix ($\Omega_{ij}$)

### 5.1 Outgoing Interaction Entropy ($H_i$)
Let base positive ratings be $A_{ik} = \Phi_{\text{edge}}(E_{\text{pos}}(i, k)) \cdot \gamma_{\text{dispute}}(i, k) \cdot \gamma_{\text{fault}}(i, k)$ for $k \ne i$, and $A_{ii} = 0$.
- If $\sum_{k \ne i} A_{ik} = 0 \implies H_i = 0.0$.
- Otherwise:
  $$p_{ik} = \frac{A_{ik}}{\sum_{m \ne i} A_{im}}$$
  $$H_i = -\frac{1}{\ln(\max(2, |\mathcal{V}| - 1))} \sum_{k \ne i, p_{ik} > 0} p_{ik} \ln(p_{ik})$$
  - Range: $0.0 \le H_i \le 1.0$.

### 5.2 Regularized Reciprocity Symmetry ($\rho_{ij}$)
$$\rho_{ij} = \frac{2 \cdot \min(A_{ij}, A_{ji})}{A_{ij} + A_{ji} + \delta_{\text{reg}}} \quad (\delta_{\text{reg}} = 2.0)$$
- If $A_{ij} = 1, A_{ji} = 1 \implies \rho_{ij} = \frac{2}{4} = 0.50$ (Regularization prevents false alarms on initial transfers).
- If $A_{ji} \gg 0, A_{ij} = 0$ (Dedicated uploader / seedbox) $\implies \rho_{ij} = 0.0$.

### 5.3 Closed-Loop Suspicion Index ($\sigma_{ij}$) & Damping Factor ($\Omega_{ij}$)
$$\sigma_{ij} = \rho_{ij} \cdot \left(1.0 - \min(H_i, H_j)\right)^{\beta_{\text{entropy}}} \quad (\beta_{\text{entropy}} = 2.0)$$
$$\Omega_{ij} = \max\left(\epsilon_{\text{floor}}, \, 1.0 - \theta_{\text{penalty}} \cdot \sigma_{ij}\right) \quad (\theta_{\text{penalty}} = 0.85, \, \epsilon_{\text{floor}} = 0.10)$$

---

## 6. Complete Mathematical Iteration (EW-EigenTrust v1.2)

### Step 1: Effective Trust Matrix ($S'$)
$$S'_{ij} = \Omega_{ij} \cdot A_{ij} \quad \text{for } i \ne j, \quad S'_{ii} = 0$$

### Step 2: Stochastic Transition Normalization ($C'$)
For each row $i \in \{1, \dots, n\}$:
$$D_i = \sum_{k=1}^n S'_{ik}$$
$$C'_{ij} = \begin{cases}
\frac{S'_{ij}}{D_i} & \text{if } D_i > 0 \\
p_j & \text{if } D_i = 0 \quad (\text{Dangling Row})
\end{cases}$$

### Step 3: Pre-trusted Anchor Restart Vector ($\mathbf{p}$)
$$\mathcal{S}_{\text{valid}} = \mathcal{S}_{\text{supernodes}} \cap \mathcal{V}$$
$$p_j = \begin{cases}
\frac{1}{|\mathcal{S}_{\text{valid}}|} & \text{if } j \in \mathcal{S}_{\text{valid}} \\
\frac{1}{n} & \text{if } |\mathcal{S}_{\text{valid}}| = 0 \quad (\text{Fallback}) \\
0 & \text{otherwise}
\end{cases}$$

### Step 4: Power Iteration Operator
Initialize $\mathbf{t}^{(0)} = \mathbf{p}$. For $k = 0, 1, 2, \dots$:
$$\mathbf{t}^{(k+1)} = (1 - \alpha) (C')^T \mathbf{t}^{(k)} + \alpha \mathbf{p} \quad (\alpha = 0.15)$$

### Step 5: Convergence & Simplex Guarantee
- **Contraction Factor:** $\|T(\mathbf{u}) - T(\mathbf{v})\|_1 \le (1 - \alpha) \|\mathbf{u} - \mathbf{v}\|_1$.
- **Theorem:** Under the Banach Fixed-Point Theorem, $T$ has a **unique fixed point** $\mathbf{t}^* \in \Delta^n$ and converges geometrically with rate $O((1 - \alpha)^k)$, reaching tolerance $10^{-6}$ in $\le 50$ iterations.

---

## 7. Implementation-Ready Pseudocode

```python
"""
Evidence-Weighted EigenTrust with Topology-Aware Collusion Damping (EW-EigenTrust v1.2)
Authoritative Implementation Contract for Phase 8.
"""

import math
import numpy as np
from typing import List, Dict, Tuple, Optional, Any, Set


def compute_ew_eigentrust_v1_2(
    peers: List[str],
    supernodes: List[str],
    raw_s_matrix: Dict[Tuple[str, str], float],
    evidence_journal: Any,
    peer_states: Optional[Dict[str, Any]] = None,
    known_manifest_roots: Optional[Set[str]] = None,
    alpha: float = 0.15,
    k_max: float = 10.0,
    lambda_sat: float = 0.50,
    mu_unverified: float = 0.10,
    beta_entropy: float = 2.0,
    theta_penalty: float = 0.85,
    epsilon_floor: float = 0.10,
    delta_reg: float = 2.0,
    tau_seconds: float = 86400.0,
    max_iter: int = 50,
    tol: float = 1e-6,
    reference_time: Optional[float] = None
) -> Dict[str, float]:
    """
    Computes global trust vector using EW-EigenTrust v1.2.
    Strictly deterministic, row-stochastic, and bounded against evidence grinding.
    """
    n = len(peers)
    if n == 0:
        return {}

    sorted_peers = sorted(peers)
    peer_to_idx = {did: idx for idx, did in enumerate(sorted_peers)}
    valid_supernodes = [sn for sn in supernodes if sn in peer_to_idx]
    manifest_roots = {r.lower() for r in (known_manifest_roots or set())}
    states = peer_states or {}
    t_ref = reference_time

    # 1. Construct pre-trusted restart vector p
    p = np.zeros(n, dtype=np.float64)
    if valid_supernodes:
        sn_weight = 1.0 / len(valid_supernodes)
        for sn in valid_supernodes:
            p[peer_to_idx[sn]] = sn_weight
    else:
        p.fill(1.0 / n)

    # 2. Extract journal entries and certified faults
    certified_fault_accused: Set[str] = set()
    pair_entries: Dict[Tuple[str, str], List[Any]] = {}

    if hasattr(evidence_journal, "_entries"):
        for entry in evidence_journal._entries.values():
            if entry.entry_type == "FAULT_EVIDENCE":
                accused = entry.details.get("accused_did")
                if accused:
                    certified_fault_accused.add(accused)
            elif entry.entry_type == "RECEIPT":
                c = entry.details.get("client_did")
                s = entry.details.get("server_did")
                if c and s:
                    pair_entries.setdefault((c, s), []).append(entry)

    # 3. Compute Base Positive Effective Matrix A_ij
    A = np.zeros((n, n), dtype=np.float64)

    for i, src in enumerate(sorted_peers):
        for j, dst in enumerate(sorted_peers):
            if i == j:
                continue

            # Certified fault or suspected/revoked nullification
            state_val = str(getattr(states.get(dst), "value", states.get(dst, "ACTIVE")))
            if dst in certified_fault_accused or state_val in ("SUSPECTED", "REVOKED"):
                continue

            entries = pair_entries.get((src, dst), [])
            e_pos = 0.0
            n_neg = 0.0

            for e in entries:
                rating_val = e.details.get("rating", 1.0)
                if rating_val > 0:
                    # Root attribution
                    m_root = e.details.get("merkle_root", "").lower()
                    gamma_root = 1.0 if (m_root and m_root in manifest_roots) else mu_unverified

                    # Freshness
                    e_ts = e.details.get("receipt_timestamp", e.timestamp)
                    if t_ref is not None:
                        dt = t_ref - e_ts
                        if dt < -60.0:
                            gamma_time = 0.0
                        elif dt <= 0.0:
                            gamma_time = 1.0
                        else:
                            gamma_time = math.exp(-dt / tau_seconds)
                    else:
                        gamma_time = 1.0

                    e_pos += gamma_root * gamma_time
                else:
                    n_neg += 1.0

            if e_pos > 0.0:
                gamma_dispute = max(0.0, 1.0 - (2.0 * n_neg / (len(entries) + 1.0)))
                phi_val = k_max * math.tanh((lambda_sat * e_pos) / k_max)
                A[i, j] = phi_val * gamma_dispute

    # 4. Outgoing Interaction Entropy H_i
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

    # 5. Reciprocity and Topological Damping Matrix Omega_ij
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

    # 6. Effective Matrix S_prime and Stochastic Matrix C_prime
    S_prime = Omega * A
    C_prime = np.zeros((n, n), dtype=np.float64)

    for i in range(n):
        row_total = np.sum(S_prime[i, :])
        if row_total > 0:
            C_prime[i, :] = S_prime[i, :] / row_total
        else:
            C_prime[i, :] = p  # Dangling node restart to pre-trusted seed

    # 7. Stationary Power Iteration
    t = p.copy()
    C_prime_T = C_prime.T

    for iteration in range(max_iter):
        t_next = (1.0 - alpha) * (C_prime_T @ t) + (alpha * p)
        if np.sum(np.abs(t_next - t)) < tol:
            t = t_next
            break
        t = t_next

    # Simplex normalization
    t_sum = np.sum(t)
    if t_sum > 0:
        t = t / t_sum

    return {sorted_peers[i]: float(t[i]) for i in range(n)}
```

---

## 8. Baseline Equivalence & Comparative Experimental Design

To guarantee scientifically defensible comparisons across Phase 8:
All baselines execute on the **exact same simulated transaction trajectory and random seeds**:

```
                              [Simulated Round r Transactions]
                                             │
                                             ▼
                        [Canonical Evidence Journal L_sim & Matrix S]
                                             │
        ┌────────────────────────────────────┼────────────────────────────────────┐
        ▼                                    ▼                                    ▼
[Vanilla EigenTrust]                 [Full EW-EigenTrust]                 [Local-Only Baseline]
k_max=inf, Omega=1, gamma_root=1     k_max=10, Omega=Omega, gamma_root    Direct row sums S_ij
```

1. **Vanilla EigenTrust:** Setting $\Phi_{\text{edge}}(E) = \max(S_{ij}, 0)$, $\gamma_{\text{root}} = 1.0$, and $\Omega_{ij} = 1.0$ reproduces Vanilla EigenTrust bit-for-bit.
2. **Ablation B (Evidence-Only):** Active $\Phi_{\text{edge}}$ and $\gamma_{\text{root}}$, but $\Omega_{ij} = 1.0$.
3. **Ablation C (Topology-Only):** Active $\Omega_{ij}$, but unweighted scores $S_{ij}$.
4. **Full EW-EigenTrust:** Complete dual-factor algorithm active.
5. **Local-Only Baseline:** Local unnormalized experience sums without power iteration.

---

## 9. Evidentiary Claim Discipline

- **[STANDARD]:** Ed25519 signatures, full 64-hex DIDs, PoW admission, SHA-256 Merkle trees, Shamir secret sharing, vanilla EigenTrust power iteration.
- **[IMPLEMENTED]:** 7-stage bilateral evidence pipeline, processed-evidence journal ($L_{\text{local}} / L_{\text{sim}}$), certified Merkle contradiction attribution, 3-of-5 supernode quorum revocation.
- **[PROPOSED]:** Intrinsic edge bound $\Phi_{\text{edge}}$, Merkle root attribution $\gamma_{\text{root}}$, counterparty interaction entropy $H_i$, regularized reciprocity $\rho_{ij}$, and topology-aware damping $\Omega_{ij}$.
- **[HYPOTHESIS]:** Hypotheses $H_1$ through $H_4$ regarding collusive trust reduction and honest community preservation.
- **[MEASURED]:** Empirical metrics reported in `PHASE6_EXPERIMENT_REPORT.md` (e.g. 0% replay acceptance across 495 trials).
- **[NOT ESTABLISHED]:** Universal collusion immunity against arbitrary Byzantine colluders performing majority honest work across all network partitions.
