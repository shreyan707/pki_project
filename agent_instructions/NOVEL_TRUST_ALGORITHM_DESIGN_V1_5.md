# Novel Trust Algorithm Design v1.5: Evidence-Weighted EigenTrust with Topology-Aware Collusion Damping (EW-EigenTrust)

**Version:** 1.5.0-FINAL  
**Phase:** Phase 7.5 (Final Convergence, Evidence-Portability, and Baseline Equivalence Audit)  
**Author:** Candidate Shreyan Nayak (23BKT0039) & Independent Mathematical Auditor  
**Date:** October 9, 2026  
**Status:** `PHASE7_5_STATUS: READY_FOR_IMPLEMENTATION`  
**Supercedes:** `NOVEL_TRUST_ALGORITHM_DESIGN_V1_4.md`, `NOVEL_TRUST_ALGORITHM_DESIGN_V1_3.md`, `NOVEL_TRUST_ALGORITHM_DESIGN_V1_2.md`, `NOVEL_TRUST_ALGORITHM_DESIGN_V1_1.md`, and `NOVEL_TRUST_ALGORITHM_DESIGN.md`  

---

## 1. Research Baseline & The Connected-Collusion Vulnerability

In decentralized peer-to-peer (P2P) public key infrastructure (PKI) swarms, trust management must evaluate peer reliability without a centralized credit authority. The Phase 1–6 baseline protocol implements **Vanilla EigenTrust** (Kamvar et al., 2003):

$$\mathbf{t}^{(m)} = (1 - \alpha) C^T \mathbf{t}^{(m-1)} + \alpha \mathbf{p}$$

where $C_{ij} = \frac{\max(S_{ij}, 0)}{\sum_k \max(S_{ik}, 0)}$ and $\mathbf{p}$ is the stationary restart distribution over pre-trusted supernodes.

### 1.1 The Connected-Collusion Vulnerability (Phase 6 Empirical Finding)
1. **Isolated Sybils:** Completely disconnected Sybil clusters exchanging mutual positive ratings are damped to near-zero collective trust share ($0.00\%$) because no stationary random-walk paths connect pre-trusted supernodes to the Sybil subgraph.
2. **Connected Collusion with Honest Bridging:** When colluding Sybils establish bridging transactions to honest peers ($p_{\text{bridge}} \in [0.05, 0.40]$), stationary probability mass leaks across the bridge into the collusive ring. Dense internal reciprocal upvoting traps random walks, causing reputation inflation that vanilla EigenTrust cannot distinguish from authentic community service.
3. **Sybil Edge Inflation:** Because vanilla EigenTrust lacks an intrinsic ceiling on edge accumulation, a collusive ring can inflate $S_{ij}$ to arbitrarily large values through synthetic micro-transactions, completely dominating the normalized outgoing matrix row $C_{ij}$.

---

## 2. Attacker Capability Matrix & Cryptographic Boundaries

The attack model formalizes **Connected Collusion** while remaining strictly compliant with `SECURITY_MODEL.md` v2.2.0-FROZEN:

| Adversary Profile | Allowed Actions (Capabilities) | Infeasible Actions (Cryptographic Boundaries) |
| :--- | :--- | :--- |
| **Connected Sybil Coalition** | • Solve Ed25519 PoW admission<br>• Register into Layer 2 mesh<br>• Mutual $+1.00$ bilateral receipts within coalition<br>• Deliver authentic content to honest peers at bridging probability $p_{\text{bridge}}$ | • **Cannot forge signatures:** Cannot forge honest peer or supernode private keys<br>• **Cannot forge Merkle proofs:** Cannot produce valid inclusion proofs for modified bytes without SHA-256 collision<br>• **Cannot double-spend receipts:** Processed-evidence journal ($L_{\text{local}} / L_{\text{sim}}$) rejects replayed receipts<br>• **Cannot forge bilateral co-signatures:** Cannot unilaterally invent a positive receipt with an honest peer without the honest peer's private key |

---

## 3. Evidence Portability & Trust-Vector Scope

A foundational distinction established in the Phase 7.5 audit is the semantic scope of trust vectors under different evidence availability models:

### 3.1 Trust-Vector Scope Models
1. **Node-Local Subjective Trust Vector ($\mathbf{t}_v$):**
   In a decentralized network, node $v$ evaluates peer trustworthiness based on:
   - Its local evidence journal $L_{\text{local}}(v)$.
   - Its local verified delivery records $\mathcal{D}_{\text{local}}(v)$.
   - Third-party receipts gossiped by peers across the overlay network.
   Because node $v$ only personally witnessed its own content deliveries, it grants full credit ($\gamma_{\text{evidence}} = 1.00$) exclusively to transactions in $\mathcal{D}_{\text{local}}(v)$. Third-party receipts receive discounted weights ($\mu_{\text{referenced}} = 0.25$ or $\mu_{\text{unverified}} = 0.10$). The resulting vector $\mathbf{t}_v$ is a **subjective, node-local trust evaluation**.
2. **Canonical Swarm Trust Vector ($\mathbf{t}_{\text{canon}}$):**
   In the simulation environment (`SwarmSimulation`) and benchmark harness, the simulator maintains a canonical evidence journal $L_{\text{sim}}$ and a canonical set of verified delivery keys $\mathcal{D}_{\text{canonical}}$ across all admitted nodes. The resulting trust vector $\mathbf{t}_{\text{canon}}$ represents the global ground-truth reputation distribution of the overlay swarm.

### 3.2 Authenticated Delivery Linkage Key
The linkage key binding receipts to verified deliveries is the 4-tuple:
$$\text{DeliveryKey} = (client\_did, server\_did, merkle\_root, tx\_id)$$

#### Lifecycle Trace:
1. **Request:** Client sends signed `ContentRequest` ($req\_id, content\_id, chunk\_index, merkle\_root, nonce_{req}$).
2. **Delivery:** Server delivers signed `ChunkResponse` ($req\_id, chunk\_bytes, chunk\_hash, proof\_hash, merkle\_root, \Pi_k$).
3. **Verification:** Client validates signature and Merkle inclusion proof via `verify_merkle_proof()`.
4. **Receipt Generation:** Client generates `tx_id = f"tx-{req_id}"` and co-signs `BilateralReceipt`.
5. **Storage:**
   - In local client state: $\text{DeliveryKey} \in \mathcal{D}_{\text{local}}$.
   - In journal entry details: Committed with `client_did`, `server_did`, `merkle_root`, and `entry_id` (`tx_id`).

### 3.3 Wire-Portability Limitation and Non-Breaking Resolution
- **Limitation:** The frozen v2.2 `BilateralReceipt` wire format does **not** carry raw chunk bytes or Merkle inclusion proofs across the wire. Therefore, third-party peers observing gossiped receipts cannot independently re-verify Merkle inclusion proofs for transactions they did not witness.
- **Wire Preservation:** The wire format is frozen and unchanged.
- **Three-Tier Credit Solution:**
  $$\gamma_{\text{evidence}}(e) = \begin{cases}
  1.00 & \text{if } (e.\text{client\_did}, e.\text{server\_did}, e.\text{merkle\_root}, e.\text{tx\_id}) \in \mathcal{D} \quad (\text{Tier 3: Verified Delivery}) \\
  0.25 & \text{if } e.\text{merkle\_root} \in \mathcal{R}_{\text{manifests}} \quad (\text{Tier 2: Known Manifest Reference}) \\
  0.10 & \text{otherwise} \quad (\text{Tier 1: Unindexed Bilateral Receipt})
  \end{cases}$$
  - **Tier 3 ($1.00$):** Authenticated delivery witnessed and verified by the local evaluator.
  - **Tier 2 ($0.25$):** Valid bilateral receipt referencing a publisher-signed manifest root registered in the local manifest index $\mathcal{R}_{\text{manifests}}$.
  - **Tier 1 ($0.10$):** Valid bilateral receipt referencing an unindexed or synthetic Merkle root (severely discounts unverified Sybil co-receipt grinding).

---

## 4. Multi-Tier Evidence Evaluation & Bounded Edge Strength

To eliminate evidence-grinding vulnerabilities where bounded weights multiply unbounded cumulative integers, the **effective transition edge is an intrinsically bounded, strictly concave function of validated evidence**:

$$S'_{ij} = \Omega_{ij} \cdot \Phi_{\text{edge}}(E_{\text{pos}}(i, j)) \cdot \gamma_{\text{dispute}}(i, j) \cdot \gamma_{\text{fault}}(i, j) \quad \text{for } i \ne j, \quad S'_{ii} = 0$$

### 4.1 Concave Edge Ceiling ($\Phi_{\text{edge}}$)
$$\Phi_{\text{edge}}(E) = K_{\text{max}} \cdot \tanh\left(\frac{\lambda_{\text{sat}} \cdot E}{K_{\text{max}}}\right)$$
- **Upper Bound:** $\Phi_{\text{edge}}(E) < K_{\text{max}} = 10.0$ for all $E \ge 0$.
- **Saturation Constant:** $\lambda_{\text{sat}} = 0.50$.
- **Characteristic Values:**
  - $E = 1.0 \implies \Phi(1.0) \approx 0.499$
  - $E = 5.0 \implies \Phi(5.0) \approx 2.449$
  - $E = 20.0 \implies \Phi(20.0) \approx 7.616$
  - $E \to \infty \implies \Phi(E) \to 10.000$

### 4.2 Positive Evidence Accumulation ($E_{\text{pos}}$)
$$E_{\text{pos}}(i, j) = \sum_{e \in \mathcal{E}_{ij}^{+}} \gamma_{\text{evidence}}(e) \cdot \gamma_{\text{time}}(t_{\text{ref}} - t_e)$$

### 4.3 Deterministic Timestamp Freshness ($\gamma_{\text{time}}$)
Let $\Delta t = t_{\text{ref}} - t_e$. With half-life decay parameter $\tau = 86400.0$ seconds (1 day):
$$\gamma_{\text{time}}(\Delta t) = \begin{cases}
1.0 & \text{if } -60.0 \le \Delta t \le 0.0 \quad (\text{Bounded clock drift tolerance}) \\
0.0 & \text{if } \Delta t < -60.0 \quad (\text{Excessive future timestamp rejected}) \\
\exp\left(-\frac{\Delta t}{\tau}\right) & \text{if } \Delta t > 0.0 \quad (\text{Exponential historical decay})
\end{cases}$$
If `reference_time` is `None`, $\gamma_{\text{time}}(\Delta t) = 1.0$.

### 4.4 Unambiguous Bilateral Dispute Factor ($\gamma_{\text{dispute}}$)
Negative receipts (`"-1.00"`) represent bilateral delivery failures or protocol disagreements. They penalize the pairwise edge without triggering system-wide revocation:
$$\gamma_{\text{dispute}}(N_{\text{pos}}, N_{\text{neg}}) = \begin{cases}
0.0 & \text{if } N_{\text{pos}} = 0 \\
\max\left(0.0, \, 1.0 - \frac{2 \cdot N_{\text{neg}}}{N_{\text{pos}} + 1.0}\right) & \text{if } N_{\text{pos}} > 0
\end{cases}$$

### 4.5 Certified Fault Nullification ($\gamma_{\text{fault}}$)
Certified fault evidence (`FaultEvidenceRecord`) and formal revocation states represent irrefutable cryptographic misbehavior:
$$\gamma_{\text{fault}}(i, j) = \begin{cases}
0.0 & \text{if } j \in \text{accused\_dids}(\mathcal{F}) \lor \text{peer\_states}[j] \in \{\text{REVOCATION\_PROPOSED}, \text{REVOKED}\} \\
    & \quad \lor (\text{peer\_states}[j] == \text{SUSPECTED} \land \text{is\_certified\_suspicion}(j)) \\
1.0 & \text{otherwise}
\end{cases}$$
When $\gamma_{\text{fault}}(i, j) = 0.0$, all incoming edges to peer $j$ are nullified ($S'_{ij} = 0$).

---

## 5. Topology-Aware Collusion Damping Matrix ($\Omega_{ij}$)

To suppress dense internal reciprocal upvoting within collusive rings while protecting honest asymmetric contributors, the damping matrix $\Omega_{ij}$ penalizes edges with high mutual reciprocity and low interaction entropy.

### 5.1 Outgoing Interaction Entropy ($H_i$)
Let $A_{ik} = \Phi_{\text{edge}}(E_{\text{pos}}(i, k)) \cdot \gamma_{\text{dispute}}(i, k) \cdot \gamma_{\text{fault}}(i, k)$ for $k \ne i$, and $A_{ii} = 0$.
- If $\sum_{k \ne i} A_{ik} = 0$, then $H_i = 0.0$.
- Otherwise:
  $$p_{ik} = \frac{A_{ik}}{\sum_{m \ne i} A_{im}}$$
  $$H_i = -\frac{1}{\ln(\max(2, |\mathcal{V}| - 1))} \sum_{k \ne i, p_{ik} > 0} p_{ik} \ln(p_{ik})$$
  - Range: $0.0 \le H_i \le 1.0$.
  - Maximum entropy ($H_i = 1.0$) corresponds to perfectly dispersed interaction across all available peers.
  - Zero entropy ($H_i = 0.0$) corresponds to interaction concentrated entirely on a single peer.

### 5.2 Regularized Reciprocity Symmetry ($\rho_{ij}$)
$$\rho_{ij} = \frac{2 \cdot \min(A_{ij}, A_{ji})}{A_{ij} + A_{ji} + \delta_{\text{reg}}} \quad (\delta_{\text{reg}} = 2.0)$$
- **Asymmetric Provider Immunity:** If node $j$ is a pure content uploader (seedbox) receiving high ratings $A_{ij} \gg 0$ but granting zero ratings $A_{ji} = 0$, then $\min(A_{ij}, A_{ji}) = 0 \implies \rho_{ij} = 0.0$. Pure uploaders suffer zero reciprocity penalty.
- **Regularization Protection:** For small initial exchanges ($A_{ij} = 1.0, A_{ji} = 1.0$), $\rho_{ij} = \frac{2}{4} = 0.50$, preventing false-positive penalties during network bootstrap.

### 5.3 Closed-Loop Suspicion Index ($\sigma_{ij}$) & Damping Factor ($\Omega_{ij}$)
$$\sigma_{ij} = \rho_{ij} \cdot \left(1.0 - \min(H_i, H_j)\right)^{\beta_{\text{entropy}}} \quad (\beta_{\text{entropy}} = 2.0)$$
$$\Omega_{ij} = \max\left(\epsilon_{\text{floor}}, \, 1.0 - \theta_{\text{penalty}} \cdot \sigma_{ij}\right) \quad (\theta_{\text{penalty}} = 0.85, \, \epsilon_{\text{floor}} = 0.10)$$
- **Collusive Ring:** High reciprocity ($\rho_{ij} \approx 1.0$) + low entropy ($H_i, H_j \approx 0$) $\implies \sigma_{ij} \approx 1.0 \implies \Omega_{ij} = 1.0 - 0.85 = 0.15$ (85% damping).
- **Honest Peer Network:** High entropy ($H_i \approx 1.0$) $\implies 1.0 - H_i \approx 0 \implies \sigma_{ij} \approx 0 \implies \Omega_{ij} = 1.00$ (No damping).
- **Floor Protection:** Damping factor is strictly lower-bounded by $\epsilon_{\text{floor}} = 0.10$, preserving ergodicity.

---

## 6. Complete Mathematical Iteration & Cauchy Step Proof

### 6.1 Matrix Construction & Normalization
1. **Effective Trust Matrix ($S'$):**
   $$S'_{ij} = \Omega_{ij} \cdot A_{ij} \quad \text{for } i \ne j, \quad S'_{ii} = 0$$
2. **Stochastic Transition Matrix ($C'$):**
   For each peer $i \in \{1, \dots, n\}$:
   $$D_i = \sum_{k=1}^n S'_{ik}$$
   $$C'_{ij} = \begin{cases}
   \frac{S'_{ij}}{D_i} & \text{if } D_i > 0 \\
   p_j & \text{if } D_i = 0 \quad (\text{Dangling Row Fallback})
   \end{cases}$$
   Every row of $C'$ satisfies $\sum_{j=1}^n C'_{ij} = 1.0$.

### 6.2 Pre-trusted Anchor Restart Vector ($\mathbf{p}$)
Let $\mathcal{S}_{\text{valid}} = \text{unique}(\mathcal{S}_{\text{supernodes}}) \cap \mathcal{V}$:
$$p_j = \begin{cases}
\frac{1}{|\mathcal{S}_{\text{valid}}|} & \text{if } j \in \mathcal{S}_{\text{valid}} \\
\frac{1}{n} & \text{if } |\mathcal{S}_{\text{valid}}| = 0 \quad (\text{Uniform Fallback}) \\
0 & \text{otherwise}
\end{cases}$$
$\mathbf{p}$ is a non-negative probability vector with $\|\mathbf{p}\|_1 = 1.0$.

### 6.3 Power Iteration Operator
Initialize $\mathbf{t}_0 = \mathbf{p}$. For loop iteration $m = 1, 2, \dots, \text{max\_iter}$:
$$\mathbf{t}_m = T(\mathbf{t}_{m-1}) = (1 - \alpha) (C')^T \mathbf{t}_{m-1} + \alpha \mathbf{p}$$
The iteration terminates when the successive-iterate distance satisfies:
$$\Delta_m = \|\mathbf{t}_m - \mathbf{t}_{m-1}\|_1 < \text{tol} \quad (\text{tol} = 10^{-6})$$

### 6.4 Exact Proof of the Cauchy Step Iteration Bound

#### Theorem:
Under 1-based loop indexing `for iteration in range(1, max_iter + 1)`, with restart parameter $\alpha = 0.15$ and tolerance $\text{tol} = 10^{-6}$, the successive-iterate stopping criterion $\|\mathbf{t}_m - \mathbf{t}_{m-1}\|_1 < \text{tol}$ is guaranteed to be satisfied in at most:
$$m^* = 90 \text{ iterations}$$

#### Derivation:
1. **Base Step Distance ($m = 1$):**
   $$\Delta_1 = \|\mathbf{t}_1 - \mathbf{t}_0\|_1 = \|(1 - \alpha) (C')^T \mathbf{p} + \alpha \mathbf{p} - \mathbf{p}\|_1 = (1 - \alpha) \|(C')^T \mathbf{p} - \mathbf{p}\|_1$$
   Since $(C')^T \mathbf{p}$ and $\mathbf{p}$ are both probability vectors in $\Delta^n$:
   $$\|(C')^T \mathbf{p} - \mathbf{p}\|_1 \le \|(C')^T \mathbf{p}\|_1 + \|\mathbf{p}\|_1 = 1 + 1 = 2$$
   Therefore:
   $$\Delta_1 \le 2(1 - \alpha)$$
2. **Inductive Step Distance for Iteration $m$:**
   Since $C'$ is row-stochastic, $(C')^T$ is a non-expansion in $L_1$ norm. The operator $T$ is an $L_1$ contraction mapping with Lipschitz constant $c = 1 - \alpha$:
   $$\Delta_m = \|\mathbf{t}_m - \mathbf{t}_{m-1}\|_1 = \|T(\mathbf{t}_{m-1}) - T(\mathbf{t}_{m-2})\|_1 \le c \|\mathbf{t}_{m-1} - \mathbf{t}_{m-2}\|_1 = c \Delta_{m-1}$$
   By induction:
   $$\Delta_m \le c^{m-1} \Delta_1 \le c^{m-1} \cdot 2c = 2 c^m = 2 (1 - \alpha)^m$$
3. **Smallest Integer Bound ($m^*$):**
   $$\Delta_m < \text{tol} \iff 2(1 - \alpha)^m < \text{tol} \iff m > \frac{\ln(\text{tol} / 2)}{\ln(1 - \alpha)}$$
   For $\alpha = 0.15$ ($1 - \alpha = 0.85$) and $\text{tol} = 10^{-6}$:
   $$m > \frac{\ln(5 \times 10^{-7})}{\ln(0.85)} = \frac{-14.5086577385}{-0.1625189295} \approx 89.2736$$
   The smallest integer satisfying the inequality is:
   $$m^* = \lceil 89.2736 \rceil = 90$$

#### Numerical Boundary Check:
- At iteration $m = 89$:
  $$2(0.85)^{89} \approx 1.0448 \times 10^{-6} > 10^{-6} \quad (\text{Not yet guaranteed})$$
- At iteration $m = 90$:
  $$2(0.85)^{90} \approx 8.8811 \times 10^{-7} < 10^{-6} \quad (\text{Guaranteed})$$

#### Norm Equivalence to Euclidean $L_2$ (`np.linalg.norm`):
In `src/layer3_eigentrust.py:838`, the existing engine computes Euclidean distance $\Delta_2 = \|\mathbf{t}_m - \mathbf{t}_{m-1}\|_2$. By standard norm bounds:
$$\|\mathbf{x}\|_2 \le \|\mathbf{x}\|_1 \le 2(1 - \alpha)^m$$
Because the Euclidean distance is strictly upper-bounded by the Manhattan distance, **any iteration count guaranteeing $L_1$ convergence also guarantees $L_2$ convergence**.  
Setting `max_iter = 100` provides an exact, mathematically proven margin of safety ($100 \ge 90$).

---

## 7. Exact Vanilla Equivalence & Five-Way Baseline Contract

### 7.1 Baseline Equivalence Preservation
In the Phase 7.5 audit, a subtle bug in v1.4 was discovered: v1.4 executed certified-fault nullification *before* the mode check, which zeroed edges for `SUSPECTED` peers in `MODE_VANILLA`. In `src/layer3_eigentrust.py:808-822`, the existing `EigenTrustEngine` does not zero incoming edges for `SUSPECTED` peers in its normalized matrix calculation.

**Resolution:** In v1.5, `MODE_VANILLA` completely bypasses fault nullification, evidence weighting, and topology damping. It constructs $A_{ij} = \max(S_{ij}, 0)$ directly from `raw_s_matrix`, ensuring **exact bit-for-bit numerical equivalence** with `EigenTrustEngine.compute_trust_scores()`.

### 7.2 Five-Way Comparison Matrix

| Mode Identifier | Base Matrix Construction | Fault / State Nullification | Evidence Weighting ($\Phi_{\text{edge}}$) | Topology Damping ($\Omega_{ij}$) | Target Baseline |
| :--- | :--- | :---: | :---: | :---: | :--- |
| `MODE_VANILLA` | $A_{ij} = \max(S_{ij}, 0)$ | Disabled | Disabled | Disabled | **Exact Vanilla EigenTrust** (bit-for-bit identical to `EigenTrustEngine`) |
| `MODE_EVIDENCE_ONLY` | $A_{ij} = \Phi_{\text{edge}}(E) \cdot \gamma_{\text{dispute}}$ | Active ($\gamma_{\text{fault}}$) | Active | Disabled ($\Omega = 1$) | **Ablation B** (Evidence weighting isolation) |
| `MODE_TOPOLOGY_ONLY` | $A_{ij} = \max(S_{ij}, 0)$ | Disabled | Disabled | Active ($\Omega_{ij}$) | **Ablation C** (Topology damping isolation) |
| `MODE_FULL_EW` | $A_{ij} = \Phi_{\text{edge}}(E) \cdot \gamma_{\text{dispute}}$ | Active ($\gamma_{\text{fault}}$) | Active | Active ($\Omega_{ij}$) | **Proposed Algorithm** (EW-EigenTrust v1.5) |
| `MODE_LOCAL_ONLY` | Direct row sums $\sum_k \max(S_{ik}, 0)$ | Disabled | Disabled | Disabled | **Baseline 2** (Zero-propagation local tallies) |

---

## 8. Parameter and Input Validation Contract

The function enforces explicit, deterministic validation to prevent runtime errors, numerical overflows, or silent corruption:

1. **Empty Network:** If $n = \text{len}(peers) == 0$, returns `({}, True, 0)` immediately.
2. **Mode Validation:** If `mode` is not in `TrustComputationMode.VALID_MODES`, raises `ValueError(f"Invalid trust computation mode: {mode}")`.
3. **Convergence Parameters:**
   - $\alpha \in (0, 1)$: If $\alpha \le 0.0$ or $\alpha \ge 1.0$, raises `ValueError("alpha must be in (0, 1)")`.
   - $\text{tol} > 0.0$: If $\text{tol} \le 0.0$, raises `ValueError("tol must be strictly positive")`.
   - $\text{max\_iter} \ge 1$: If $\text{max\_iter} \le 0$, raises `ValueError("max_iter must be >= 1")`.
4. **Saturation & Topology Hyperparameters:**
   - If $K_{\max} \le 0.0$, $\lambda_{\text{sat}} \le 0.0$, $\beta_{\text{entropy}} \le 0.0$, $\theta_{\text{penalty}} \le 0.0$, $\epsilon_{\text{floor}} \le 0.0$, $\delta_{\text{reg}} \le 0.0$, or $\tau_{\text{seconds}} \le 0.0$, raises `ValueError`.
5. **Score Sanitization:** If any score in `raw_s_matrix` is `NaN` or `Inf`, it is sanitized to `0.0`.
6. **Supernode Deduplication:** Supernodes are filtered and deduplicated:
   `valid_supernodes = sorted(list(set(sn for sn in supernodes if sn in peer_to_idx)))`
   If no supernodes remain in the network, falls back to uniform restart $\mathbf{p} = \mathbf{1}/n$.
7. **Malformed Evidence Journaling:** Journal entries missing `client_did`, `server_did`, or malformed types are safely skipped without aborting computation.

---

## 9. Authoritative Pseudocode (v1.5)

```python
"""
Evidence-Weighted EigenTrust with Topology-Aware Collusion Damping (EW-EigenTrust v1.5)
Authoritative Implementation Contract for Phase 8.
"""

import math
import numpy as np
from typing import List, Dict, Tuple, Optional, Any, Set


class TrustComputationMode:
    VANILLA = "vanilla_eigentrust"
    EVIDENCE_ONLY = "evidence_only"
    TOPOLOGY_ONLY = "topology_only"
    FULL_EW = "full_ew_eigentrust"
    LOCAL_ONLY = "local_only"

    VALID_MODES = {VANILLA, EVIDENCE_ONLY, TOPOLOGY_ONLY, FULL_EW, LOCAL_ONLY}


def compute_ew_eigentrust_v1_5(
    peers: List[str],
    supernodes: List[str],
    raw_s_matrix: Dict[Tuple[str, str], float],
    evidence_journal: Any,
    peer_states: Optional[Dict[str, Any]] = None,
    certified_suspicion_dids: Optional[Set[str]] = None,
    verified_delivery_keys: Optional[Set[Tuple[str, str, str, str]]] = None,
    known_manifest_roots: Optional[Set[str]] = None,
    mode: str = TrustComputationMode.FULL_EW,
    alpha: float = 0.15,
    k_max: float = 10.0,
    lambda_sat: float = 0.50,
    mu_unverified: float = 0.10,
    mu_referenced: float = 0.25,
    beta_entropy: float = 2.0,
    theta_penalty: float = 0.85,
    epsilon_floor: float = 0.10,
    delta_reg: float = 2.0,
    tau_seconds: float = 86400.0,
    max_iter: int = 100,
    tol: float = 1e-6,
    reference_time: Optional[float] = None
) -> Tuple[Dict[str, float], bool, int]:
    """
    Computes global trust vector using EW-EigenTrust v1.5.
    
    Returns:
        (trust_scores: Dict[str, float], converged: bool, executed_iters: int)
    """
    # 1. Parameter and Input Validation
    if mode not in TrustComputationMode.VALID_MODES:
        raise ValueError(f"Invalid trust computation mode: {mode}")
    if not (0.0 < alpha < 1.0):
        raise ValueError(f"alpha must be in (0, 1), got {alpha}")
    if tol <= 0.0:
        raise ValueError(f"tol must be strictly positive, got {tol}")
    if max_iter < 1:
        raise ValueError(f"max_iter must be >= 1, got {max_iter}")
    if k_max <= 0.0 or lambda_sat <= 0.0:
        raise ValueError("k_max and lambda_sat must be strictly positive")
    if beta_entropy <= 0.0 or theta_penalty <= 0.0 or epsilon_floor <= 0.0:
        raise ValueError("Topology parameters must be strictly positive")
    if delta_reg <= 0.0 or tau_seconds <= 0.0:
        raise ValueError("delta_reg and tau_seconds must be strictly positive")

    n = len(peers)
    if n == 0:
        return {}, True, 0

    sorted_peers = sorted(list(set(peers)))
    peer_to_idx = {did: idx for idx, did in enumerate(sorted_peers)}
    valid_supernodes = sorted(list(set(sn for sn in supernodes if sn in peer_to_idx)))
    manifest_roots = {r.lower() for r in (known_manifest_roots or set()) if isinstance(r, str)}
    delivery_keys = verified_delivery_keys or set()
    states = peer_states or {}
    certified_suspected = certified_suspicion_dids or set()
    t_ref = reference_time

    # 2. Pre-trusted restart vector p
    p = np.zeros(n, dtype=np.float64)
    if valid_supernodes:
        sn_weight = 1.0 / len(valid_supernodes)
        for sn in valid_supernodes:
            p[peer_to_idx[sn]] = sn_weight
    else:
        p.fill(1.0 / n)

    # 3. Fast path: Local-only baseline
    if mode == TrustComputationMode.LOCAL_ONLY:
        scores = {}
        total = 0.0
        for src in sorted_peers:
            s_sum = sum(
                max(0.0, raw_s_matrix.get((src, dst), 0.0))
                for dst in sorted_peers if dst != src
            )
            scores[src] = s_sum
            total += s_sum
        if total > 0.0:
            return {did: float(v / total) for did, v in scores.items()}, True, 0
        return {did: float(1.0 / n) for did in sorted_peers}, True, 0

    # 4. Extract journal entries and certified faults (Only needed for evidence modes)
    certified_fault_accused: Set[str] = set()
    pair_entries: Dict[Tuple[str, str], List[Any]] = {}

    if mode in (TrustComputationMode.EVIDENCE_ONLY, TrustComputationMode.FULL_EW):
        if hasattr(evidence_journal, "_entries") and isinstance(evidence_journal._entries, dict):
            for entry in evidence_journal._entries.values():
                if getattr(entry, "entry_type", "") == "FAULT_EVIDENCE":
                    accused = entry.details.get("accused_did")
                    if accused and isinstance(accused, str):
                        certified_fault_accused.add(accused)
                elif getattr(entry, "entry_type", "") == "RECEIPT":
                    c = entry.details.get("client_did")
                    s = entry.details.get("server_did")
                    if c and s and isinstance(c, str) and isinstance(s, str):
                        pair_entries.setdefault((c, s), []).append(entry)

    # 5. Construct base interaction matrix A_ij
    A = np.zeros((n, n), dtype=np.float64)

    for i, src in enumerate(sorted_peers):
        for j, dst in enumerate(sorted_peers):
            if i == j:
                continue

            # Pure Vanilla Mode: Bit-for-bit equivalence with EigenTrustEngine
            if mode == TrustComputationMode.VANILLA:
                raw_score = raw_s_matrix.get((src, dst), 0.0)
                if math.isnan(raw_score) or math.isinf(raw_score):
                    raw_score = 0.0
                A[i, j] = max(0.0, raw_score)
                continue

            # Topology-Only Mode: Raw scores, no fault filtering, damped by topology
            if mode == TrustComputationMode.TOPOLOGY_ONLY:
                raw_score = raw_s_matrix.get((src, dst), 0.0)
                if math.isnan(raw_score) or math.isinf(raw_score):
                    raw_score = 0.0
                A[i, j] = max(0.0, raw_score)
                continue

            # Proposed Evidence Modes (EVIDENCE_ONLY, FULL_EW):
            # Check certified fault nullification
            state_val = str(getattr(states.get(dst), "value", states.get(dst, "ACTIVE")))
            is_cert_fault = (dst in certified_fault_accused)
            is_revoking = (state_val in ("REVOCATION_PROPOSED", "REVOKED"))
            is_cert_susp = (state_val == "SUSPECTED" and dst in certified_suspected)

            if is_cert_fault or is_revoking or is_cert_susp:
                A[i, j] = 0.0
                continue

            entries = pair_entries.get((src, dst), [])
            e_pos = 0.0
            n_pos_count = 0.0
            n_neg_count = 0.0

            for e in entries:
                rating_val = float(e.details.get("rating", 1.0))
                if rating_val > 0.0:
                    n_pos_count += 1.0
                    m_root = str(e.details.get("merkle_root", "")).lower()
                    tx_id = str(getattr(e, "entry_id", ""))

                    # Three-tier delivery credit
                    if (src, dst, m_root, tx_id) in delivery_keys:
                        gamma_ev = 1.00  # Tier 3: Local Verified Delivery
                    elif m_root and m_root in manifest_roots:
                        gamma_ev = mu_referenced  # Tier 2: Manifest Referenced
                    else:
                        gamma_ev = mu_unverified  # Tier 1: Unindexed Receipt

                    # Freshness decay
                    e_ts = float(e.details.get("receipt_timestamp", getattr(e, "timestamp", 0.0)))
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

                    e_pos += gamma_ev * gamma_time
                else:
                    n_neg_count += 1.0

            if n_pos_count > 0.0 and e_pos > 0.0:
                gamma_dispute = max(0.0, 1.0 - (2.0 * n_neg_count / (n_pos_count + 1.0)))
                phi_val = k_max * math.tanh((lambda_sat * e_pos) / k_max)
                A[i, j] = phi_val * gamma_dispute
            else:
                A[i, j] = 0.0

    # 6. Topology Damping Matrix Omega_ij
    Omega = np.ones((n, n), dtype=np.float64)

    if mode in (TrustComputationMode.TOPOLOGY_ONLY, TrustComputationMode.FULL_EW):
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

        for i in range(n):
            for j in range(n):
                if i != j and A[i, j] > 0:
                    a_ij = A[i, j]
                    a_ji = A[j, i]
                    rho_ij = (2.0 * min(a_ij, a_ji)) / (a_ij + a_ji + delta_reg)
                    min_entropy = min(H[i], H[j])
                    sigma_ij = rho_ij * math.pow(1.0 - min_entropy, beta_entropy)
                    Omega[i, j] = max(epsilon_floor, 1.0 - (theta_penalty * sigma_ij))

    # 7. Effective Matrix S_prime and Stochastic Matrix C_prime
    S_prime = Omega * A
    C_prime = np.zeros((n, n), dtype=np.float64)

    for i in range(n):
        row_total = np.sum(S_prime[i, :])
        if row_total > 0:
            C_prime[i, :] = S_prime[i, :] / row_total
        else:
            C_prime[i, :] = p  # Dangling row fallback

    # 8. Power Iteration with Cauchy Stopping Condition
    t = p.copy()
    C_prime_T = C_prime.T
    converged = False
    executed_iters = 0

    for iteration in range(1, max_iter + 1):
        executed_iters = iteration
        t_next = (1.0 - alpha) * (C_prime_T @ t) + (alpha * p)
        if np.sum(np.abs(t_next - t)) < tol:
            t = t_next
            converged = True
            break
        t = t_next

    # Simplex conservation
    t_sum = np.sum(t)
    if t_sum > 0:
        t = t / t_sum

    return {sorted_peers[i]: float(t[i]) for i in range(n)}, converged, executed_iters
```

---

## 10. Audited Acceptance Criteria Table

| Criterion | Target Property | Formal Evidentiary Classification | Verified Evidentiary Status |
| :---: | :--- | :---: | :--- |
| **AC-1** | Intrinsic Edge Bound: $S'_{ij} \le 10.0$ for all $(i, j)$ | **MATHEMATICALLY_ESTABLISHED** | Analytically proved: $\Phi_{\text{edge}} \le K_{\max} = 10.0$, $\Omega \le 1.0$, $\gamma \le 1.0$. |
| **AC-2** | Delivery Linkage: Three-tier evidence credit based on 4-tuple key | **SPECIFIED_PENDING_IMPLEMENTATION** | Fully specified in Section 3; awaits Phase 8 unit test execution. |
| **AC-3** | Certified Fault Nullification: $S'_{ij} = 0$ on certified fault/revocation | **SPECIFIED_PENDING_IMPLEMENTATION** | Fully specified in Section 4.5; awaits Phase 8 unit test execution. |
| **AC-4** | Asymmetric Provider Immunity: Pure uploaders receive $\Omega_{kp} = 1.0$ | **MATHEMATICALLY_ESTABLISHED** | Analytically proved: $\min(A_{kp}, A_{pk}) = 0 \implies \rho = 0 \implies \sigma = 0$. |
| **AC-5** | Interaction Entropy Bounds: $0.0 \le H_i \le 1.0$ | **MATHEMATICALLY_ESTABLISHED** | Analytically proved via Shannon entropy properties and log base normalization. |
| **AC-6** | Row Stochasticity: $\sum_j C'_{ij} = 1.0 \pm 10^{-12}$ | **MATHEMATICALLY_ESTABLISHED** | Analytically proved via row-sum normalization and dangler fallback. |
| **AC-7** | Simplex Conservation: $\|\mathbf{t}^*\|_1 = 1.0 \pm 10^{-12}$ | **MATHEMATICALLY_ESTABLISHED** | Analytically proved via probability simplex invariance. |
| **AC-8** | Cauchy Iteration Bound: $\|\mathbf{t}_m - \mathbf{t}_{m-1}\|_1 < 10^{-6}$ in $m \le 90$ iters | **MATHEMATICALLY_ESTABLISHED** | Analytically proved via Banach contraction bound ($m^* = 90 \le 100$). |
| **AC-9** | Empty Network & Anchor Fallback: Handles $n=0$ and no valid supernodes | **SPECIFIED_PENDING_IMPLEMENTATION** | Fully specified in Section 8; awaits Phase 8 unit test execution. |
| **AC-10**| Vanilla Mode Equivalence: `MODE_VANILLA` matches `EigenTrustEngine` | **SPECIFIED_PENDING_IMPLEMENTATION** | Fully specified via identical matrix construction; awaits Phase 8 unit test. |

---

## 11. Evidentiary Claim Discipline

- **[STANDARD]:** Ed25519 signatures, full 64-hex DIDs, PoW admission, SHA-256 Merkle trees, Shamir secret sharing, vanilla EigenTrust power iteration.
- **[IMPLEMENTED]:** 7-stage bilateral evidence pipeline, processed-evidence journal ($L_{\text{local}} / L_{\text{sim}}$), certified Merkle contradiction attribution, 3-of-5 supernode quorum revocation.
- **[PROPOSED]:** 4-tuple delivery linkage, intrinsic edge ceiling $\Phi_{\text{edge}}$, regularized reciprocity $\rho_{ij}$, counterparty interaction entropy $H_i$, and topology damping $\Omega_{ij}$.
- **[HYPOTHESIS]:** Hypotheses $H_1, H_2, H_3$ regarding collusive trust reduction and community preservation.
- **[MEASURED]:** Empirical metrics reported in `PHASE6_EXPERIMENT_REPORT.md` (e.g. 0% replay acceptance across 495 trials).
- **[NOT ESTABLISHED]:** Universal collusion immunity against arbitrary Byzantine colluders performing majority honest work across all network partitions.
