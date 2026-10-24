# Novel Trust Algorithm Design v1.7: Evidence-Weighted EigenTrust with Topology-Aware Collusion Damping (EW-EigenTrust)

**Version:** 1.7.0-FINAL  
**Phase:** Phase 7.7 (Evidence-Backed Specification Correction & Adversarial Audit)  
**Author:** Candidate Shreyan Nayak (23BKT0039) & Independent Mathematical Auditor  
**Date:** October 9, 2026  
**Status:** `SPECIFICATION_CORRECTED (GATE: BLOCKED PENDING RESOLUTION OF JOURNAL SCHEMA & DIRECTED CYCLE LIMITATIONS)`  
**Supercedes:** `NOVEL_TRUST_ALGORITHM_DESIGN_V1_6.md`, `NOVEL_TRUST_ALGORITHM_DESIGN_V1_5.md`, and all prior design documents  

---

## 1. Problem Statement & Baseline Architecture

In decentralized peer-to-peer (P2P) public key infrastructure (PKI) swarms, trust management must evaluate peer reliability without a centralized credit authority. The Phase 1–6 baseline protocol implements **Vanilla EigenTrust** (Kamvar et al., 2003):

$$\mathbf{t}^{(m)} = (1 - \alpha) C^T \mathbf{t}^{(m-1)} + \alpha \mathbf{p}$$

where $C_{ij} = \frac{\max(S_{ij}, 0)}{\sum_k \max(S_{ik}, 0)}$ and $\mathbf{p}$ is the stationary restart distribution over pre-trusted supernodes.

### 1.1 The Connected-Collusion Vulnerability
1. **Isolated Collusion:** Completely disconnected Sybil clusters exchanging mutual positive ratings are damped to near-zero collective trust share ($0.00\%$) because no stationary random-walk paths connect pre-trusted supernodes to the Sybil subgraph.
2. **Connected Collusion with Honest Bridging:** When colluding Sybils establish bridging transactions to honest peers ($p_{\text{bridge}} \in [0.05, 0.40]$), stationary probability mass leaks across the bridge into the collusive ring. Dense internal reciprocal upvoting traps random walks, causing reputation inflation that vanilla EigenTrust cannot distinguish from authentic community service.
3. **Unbounded Edge Accumulation:** Vanilla EigenTrust places no intrinsic ceiling on pairwise score accumulation ($S_{ij}$), allowing colluding nodes to execute synthetic micro-transactions and dominate row-normalized transition probabilities ($C_{ij} \to 1.0$).

---

## 2. Attacker Capability Matrix & Cryptographic Boundaries

The attack model formalizes **Connected Collusion** while remaining strictly compliant with `SECURITY_MODEL.md` v2.2.0-FROZEN:

| Adversary Profile | Allowed Actions (Capabilities) | Infeasible Actions (Cryptographic Boundaries) |
| :--- | :--- | :--- |
| **Connected Sybil Coalition** | • Solve Ed25519 PoW admission<br>• Register into Layer 2 mesh<br>• Mutual $+1.00$ bilateral receipts within coalition<br>• Deliver authentic content to honest peers at bridging probability $p_{\text{bridge}}$ | • **Cannot forge signatures:** Cannot forge honest peer or supernode private keys<br>• **Cannot forge Merkle proofs:** Cannot produce valid inclusion proofs for modified bytes without SHA-256 collision<br>• **Cannot double-spend receipts:** Processed-evidence journal ($L_{\text{local}} / L_{\text{sim}}$) rejects replayed receipts<br>• **Cannot forge bilateral co-signatures:** Cannot unilaterally invent a positive receipt with an honest peer without the honest peer's private key |

---

## 3. Canonical Peer Set & Dimensional Consistency Contract

To eliminate dimensional mismatch hazards, orphaned indices, and crashes observed in unvalidated baseline inputs:

### 3.1 Canonical Peer Definition
Let the input peer sequence be $\mathcal{P}_{\text{in}} = (p_1, p_2, \dots)$. The **canonical peer sequence** is defined deterministically as:
$$\mathcal{V} = \text{sorted}(\text{unique}(\{p \in \mathcal{P}_{\text{in}} \mid p \text{ is a non-empty string}\}))$$
- Dimension: $n = |\mathcal{V}|$.
- Index mapping: $\text{idx}(v) \in \{0, 1, \dots, n-1\}$ for each $v \in \mathcal{V}$.
- Strict Matrix Dimension: All intermediate and final matrices ($A, \Omega, S', C'$) are strictly $(n \times n)$.
- Strict Vector Dimension: The restart vector $\mathbf{p}$ and trust iterates $\mathbf{t}_m$ are strictly $n$-dimensional.

### 3.2 Handling Input Edge Cases
1. **Duplicate Peer IDs:** Duplicate strings in $\mathcal{P}_{\text{in}}$ are collapsed into unique elements during canonical sorting. The resulting dimension $n$ matches $\text{len}(\text{peer\_to\_idx})$ identically.
2. **Empty Network ($n = 0$):** If $\mathcal{V}$ is empty, the algorithm returns `({}, True, 0)` immediately, completely bypassing matrix allocation and preventing division-by-zero errors.
3. **Unknown Matrix Endpoints:** For any entry $((u, v), s) \in \text{raw\_s\_matrix}$, if $u \notin \mathcal{V}$ or $v \notin \mathcal{V}$, the entry is discarded. It does not alter the $(n \times n)$ matrix.
4. **Self-Edges:** Self-ratings $(v, v)$ are explicitly zeroed ($A_{ii} = 0, S'_{ii} = 0$). Self-edges cannot generate trust.
5. **Pre-Trusted Supernode Filtering & Fallback:**
   $$\mathcal{S}_{\text{valid}} = \text{sorted}(\text{unique}(\{sn \in \mathcal{S}_{\text{in}} \mid sn \in \mathcal{V}\}))$$
   $$\mathbf{p}_j = \begin{cases}
   \frac{1}{|\mathcal{S}_{\text{valid}}|} & \text{if } j \in \mathcal{S}_{\text{valid}} \\
   \frac{1}{n} & \text{if } |\mathcal{S}_{\text{valid}}| = 0 \quad (\text{Uniform Fallback}) \\
   0 & \text{otherwise}
   \end{cases}$$
   This guarantees $\|\mathbf{p}\|_1 = 1.0$, avoiding the sum defect ($0.5$) that occurs when duplicates are present in unvalidated baselines.

---

## 4. Parameter Validation Specification (14 Parameters)

All algorithm parameters are validated deterministically before any computation begins. Boolean inputs are strictly rejected for numeric and integer parameters to avoid Python's `isinstance(True, int) == True` type coercion:

| Parameter | Type | Default | Admissible Range | Mathematical Purpose & Invariants Preserved | Validation Action on Violation |
| :--- | :---: | :---: | :---: | :--- | :--- |
| `mode` | `str` | `"full_ew_eigentrust"` | `TrustComputationMode.VALID_MODES` | Selects exact computational pipeline | Raises `ValueError` |
| `alpha` | `float` | `0.15` | $0.0 < \alpha < 1.0$ (reject `bool`) | Contraction modulus $c = 1 - \alpha \in (0, 1)$ | Raises `ValueError` |
| `tol` | `float` | `1e-6` | $\text{tol} > 0.0$ and finite (reject `bool`) | Convergence threshold | Raises `ValueError` |
| `max_iter` | `int` | `100` | $\text{max\_iter} \ge 1$ (reject `bool`) | Upper iteration bound | Raises `ValueError` |
| `k_max` | `float` | `10.0` | $k_{\max} > 0.0$ and finite (reject `bool`) | Intrinsic edge ceiling: $S'_{ij} < k_{\max}$ | Raises `ValueError` |
| `lambda_sat`| `float` | `0.50` | $\lambda_{\text{sat}} > 0.0$ and finite (reject `bool`) | Concave growth rate | Raises `ValueError` |
| `mu_unverified` | `float` | `0.10` | $0.0 \le \mu_{\text{unverified}} \le 1.0$ (reject `bool`) | Tier 1 unindexed receipt discount | Raises `ValueError` |
| `mu_referenced` | `float` | `0.25` | $0.0 \le \mu_{\text{referenced}} \le 1.0$ (reject `bool`) | Tier 2 manifest reference discount; requires $\mu_{\text{unverified}} \le \mu_{\text{referenced}}$ | Raises `ValueError` |
| `beta_entropy` | `float` | `2.0` | $\beta_{\text{entropy}} > 0.0$ and finite (reject `bool`) | Collusion penalty sharpness | Raises `ValueError` |
| `theta_penalty`| `float` | `0.85` | $0.0 \le \theta_{\text{penalty}} \le 1.0$ (reject `bool`) | Max damping penalty ($1 - \theta \ge 0$) | Raises `ValueError` |
| `epsilon_floor`| `float` | `0.10` | $0.0 < \epsilon_{\text{floor}} \le 1.0$ (reject `bool`) | Ergodicity floor: $\Omega_{ij} \ge \epsilon_{\text{floor}}$ | Raises `ValueError` |
| `delta_reg` | `float` | `2.0` | $\delta_{\text{reg}} > 0.0$ and finite (reject `bool`) | Reciprocity regularization: protects bootstrap | Raises `ValueError` |
| `tau_seconds` | `float` | `86400.0`| $\tau_{\text{seconds}} > 0.0$ and finite (reject `bool`) | Exponential freshness decay half-life | Raises `ValueError` |
| `reference_time`| `float` / `None` | `None` | Finite float or `None` (reject `bool`) | Reference epoch for timestamp freshness | Raises `ValueError` if non-finite float |

### 4.1 Score Sanitization
For any edge $((u, v), s) \in \text{raw\_s\_matrix}$:
- If $s$ is `None`, not of type `int` or `float`, is a `bool`, or satisfies `math.isnan(s)` or `math.isinf(s)`, it is sanitized to `0.0`.
- In `MODE_VANILLA` and `MODE_TOPOLOGY_ONLY`, $A_{ij} = \max(0.0, s)$. Negative scores are cleanly clamped to `0.0`, matching `EigenTrustEngine`.

---

## 5. Journal Schema Reconciliation & Phase 8 Prerequisites

### 5.1 Reconciliation of Live Code vs. Spec Schema
Inspection of live production code ([`src/layer3_eigentrust.py:688-697`](file:///d:/pki_casestudy/src/layer3_eigentrust.py#L688-L697)) reveals:
```python
# CURRENT LIVE CODE:
committed = self.local_journal.commit(
    entry_id=receipt.tx_id,
    entry_type="RECEIPT",
    details={
        "client_did": receipt.client_did,
        "server_did": receipt.server_did,
        "rating": delta,
        "nonce": receipt.nonce
    }
)
```
- **Current State:** The fields `merkle_root` and `receipt_timestamp` are **absent** from the live journal schema.
- **Consequence:** On the current live schema, Tier 2 and Tier 3 evidence weighting logic is **completely inert**; all receipts default to Tier 1 ($\mu_{\text{unverified}} = 0.10$).
- **Phase 8 Prerequisite:** Phase 8 must update `record_receipt()` to commit:
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
  Both `receipt.merkle_root` and `receipt.timestamp` are already present on `BilateralReceipt` and signed on the wire; this change affects only local journal metadata, leaving the frozen v2.2 wire format intact.
- **Public Journal Accessor:** `LocalEvidenceJournal` currently exposes only private `_entries`. In Phase 8, a public accessor `get_all_entries()` or iterator must be added. The spec defensively supports both `get_all_entries()` and `_entries`.

### 5.2 Hardened Journal Extraction & Rating Handling
- **Defensive Extraction:** If `details` is not a dict or is missing, it defaults to `{}`.
- **Neutral Rating Handling:**
  - `rating > 0.0`: Counted as positive evidence (`n_pos_count += 1.0`).
  - `rating < 0.0`: Counted as negative dispute (`n_neg_count += 1.0`).
  - `rating == 0.0`: Treated as neutral; skipped from both positive and negative counters.

---

## 6. Cryptographic Delivery Linkage Audit

### 6.1 Cryptographic Audit of `BilateralReceipt` Wire Payload
Under [`src/layer3_eigentrust.py:423-454`](file:///d:/pki_casestudy/src/layer3_eigentrust.py#L423-L454) and `PROTOCOL_SPEC.md` v2.2.0:
$$\text{payload} = \text{"PKI\_V2\_RECEIPT:"} + tx\_id + ":" + client\_did + ":" + server\_did + ":" + merkle\_root + ":" + rating\_str + ":" + timestamp + ":" + nonce$$

- **Cryptographically Authenticated by Co-Signatures:**
  `tx_id`, `client_did`, `server_did`, `merkle_root`, `rating_str`, `timestamp`, `nonce`.
- **NOT Authenticated on the Wire:**
  `content_id`, `chunk_index`, `chunk_bytes`, `chunk_hash`, `merkle_proof`.
  The receipt wire format carries neither chunk payloads nor Merkle inclusion proofs.

### 6.2 Evidence Portability Boundary
1. **Client-Local Delivery Records ($\mathcal{D}_{\text{local}}$):**
   A client node that personally requested content and executed `verify_merkle_proof()` in [`src/network_simulator.py:343-348`](file:///d:/pki_casestudy/src/network_simulator.py#L343-L348) records the delivery in its local state indexed by:
   $$\text{DeliveryKey} = (client\_did, server\_did, merkle\_root, tx\_id)$$
   When evaluating its subjective trust vector $\mathbf{t}_v$, this node awards **Tier 3 credit ($\gamma_{\text{evidence}} = 1.00$)** to matching receipts.
2. **Third-Party Gossip-Observed Receipts:**
   A third party observing a gossiped bilateral receipt can verify both Ed25519 signatures, but cannot independently verify Merkle inclusion because chunk bytes and tree proofs are absent from the receipt.
   - If `merkle_root` matches a publisher-signed `ContentManifest` indexed in $\mathcal{R}_{\text{manifests}}$, it receives **Tier 2 credit ($\gamma_{\text{evidence}} = \mu_{\text{referenced}} = 0.25$)**.
   - If `merkle_root` is unindexed or synthetic, it receives **Tier 1 credit ($\gamma_{\text{evidence}} = \mu_{\text{unverified}} = 0.10$)**.
3. **Adversary Key Injection Impossibility:**
   An adversary cannot gain Tier 3 credit by injecting keys into receipt or journal metadata. The lookup candidate `(src, dst, m_root, tx_id)` must exist in the evaluating node's independently verified delivery set $\mathcal{D}_{\text{local}}$, which is only populated upon successful local Merkle proof execution.

---

## 7. Mathematical Model & Bounded Edge Formulation

### 7.1 Effective Edge Formula
$$S'_{ij} = \Omega_{ij} \cdot \Phi_{\text{edge}}(E_{\text{pos}}(i, j)) \cdot \gamma_{\text{dispute}}(i, j) \cdot \gamma_{\text{fault}}(i, j) \quad \text{for } i \ne j, \quad S'_{ii} = 0$$

### 7.2 Strict Boundedness & Concavity ($\Phi_{\text{edge}}$)
$$\Phi_{\text{edge}}(E) = K_{\text{max}} \cdot \tanh\left(\frac{\lambda_{\text{sat}} \cdot E}{K_{\text{max}}}\right)$$
- **Theorem (Intrinsic Ceiling):** For all $E \ge 0$, $\Phi_{\text{edge}}(E) < K_{\max} = 10.0$.
  Because $\Omega_{ij} \le 1.0$, $\gamma_{\text{dispute}} \le 1.0$, and $\gamma_{\text{fault}} \le 1.0$, the effective edge satisfies $S'_{ij} < K_{\max} = 10.0$ for all $(i, j)$ under admissible parameters.

### 7.3 Positive Evidence Accumulation ($E_{\text{pos}}$)
$$E_{\text{pos}}(i, j) = \sum_{e \in \mathcal{E}_{ij}^{+}} \gamma_{\text{evidence}}(e) \cdot \gamma_{\text{time}}(t_{\text{ref}} - t_e)$$
$$\gamma_{\text{time}}(\Delta t) = \begin{cases}
1.0 & \text{if } -60.0 \le \Delta t \le 0.0 \quad (\text{Clock drift tolerance}) \\
0.0 & \text{if } \Delta t < -60.0 \quad (\text{Excessive future timestamp rejected}) \\
\exp\left(-\frac{\Delta t}{\tau}\right) & \text{if } \Delta t > 0.0 \quad (\text{Exponential freshness decay})
\end{cases}$$

### 7.4 Bilateral Dispute Penalty ($\gamma_{\text{dispute}}$)
$$\gamma_{\text{dispute}}(N_{\text{pos}}, N_{\text{neg}}) = \begin{cases}
0.0 & \text{if } N_{\text{pos}} = 0 \\
\max\left(0.0, \, 1.0 - \frac{2 \cdot N_{\text{neg}}}{N_{\text{pos}} + 1.0}\right) & \text{if } N_{\text{pos}} > 0
\end{cases}$$

### 7.5 Certified Fault Nullification ($\gamma_{\text{fault}}$)
$$\gamma_{\text{fault}}(i, j) = \begin{cases}
0.0 & \text{if } j \in \text{accused\_dids}(\mathcal{F}) \lor \text{peer\_states}[j] \in \{\text{REVOCATION\_PROPOSED}, \text{REVOKED}\} \\
    & \quad \lor (\text{peer\_states}[j] == \text{SUSPECTED} \land \text{is\_certified\_suspicion}(j)) \\
1.0 & \text{otherwise}
\end{cases}$$

---

## 8. Topology-Aware Collusion Damping Matrix ($\Omega_{ij}$) & Adversarial Limitations

### 8.1 Formulas
1. **Outgoing Interaction Entropy ($H_i$):**
   $$p_{ik} = \frac{A_{ik}}{\sum_{m \ne i} A_{im}}, \quad H_i = -\frac{1}{\ln(\max(2, n - 1))} \sum_{k \ne i, p_{ik} > 0} p_{ik} \ln(p_{ik})$$
   $H_i \in [0.0, 1.0]$ when $\sum_{k \ne i} A_{ik} > 0$; $H_i = 0.0$ otherwise.
2. **Regularized Reciprocity ($\rho_{ij}$):**
   $$\rho_{ij} = \frac{2 \cdot \min(A_{ij}, A_{ji})}{A_{ij} + A_{ji} + \delta_{\text{reg}}} \quad (\delta_{\text{reg}} = 2.0)$$
3. **Suspicion Index & Damping Factor:**
   $$\sigma_{ij} = \rho_{ij} \cdot \left(1.0 - \min(H_i, H_j)\right)^{\beta_{\text{entropy}}}, \quad \Omega_{ij} = \max\left(\epsilon_{\text{floor}}, \, 1.0 - \theta_{\text{penalty}} \cdot \sigma_{ij}\right)$$

### 8.2 Critical Known Limitations (Verified in Phase 7.7)
1. **Blindness to Directed Cycles ($k \ge 3$):**
   Because $\rho_{ij}$ depends strictly on $\min(A_{ij}, A_{ji})$, in any directed cycle ($c_0 \to c_1 \to c_2 \to c_0$), every active edge has $A_{ji} = 0$, yielding:
   $$\min(A_{ij}, A_{ji}) = 0 \implies \rho_{ij} = 0.0 \implies \sigma_{ij} = 0.0 \implies \Omega_{ij} = 1.00$$
   **$\Omega$ provides zero damping against directed cycles of length $k \ge 3$.** Colluding rings can organize into directed cycles or rings with chords to completely bypass topology damping.
2. **Collusive Share Inflation in Dense Honest Subgraphs:**
   When honest nodes engage in mutual reciprocal transfers with low outgoing entropy (e.g. small honest clusters), $\Omega$ damps honest edges as well, which can paradoxically increase the colluders' relative trust share.
   - Any claim of resistance against multi-hop or community collusion is labeled an **UNPROVEN EMPIRICAL HYPOTHESIS**.

---

## 9. Stochastic Normalization & Power Iteration Convergence

### 9.1 Row Stochastic Normalization ($C'$)
For each row $i \in \{0, \dots, n-1\}$:
$$C'_{ij} = \begin{cases}
\frac{S'_{ij}}{\sum_k S'_{ik}} & \text{if } \sum_k S'_{ik} > 0 \\
p_j & \text{if } \sum_k S'_{ik} = 0 \quad (\text{Dangling Row Fallback})
\end{cases}$$

### 9.2 Power Iteration & General Convergence Bound
Initialize $\mathbf{t}_0 = \mathbf{p}$. For loop iteration $m = 1, 2, \dots, \text{max\_iter}$:
$$\mathbf{t}_m = (1 - \alpha) (C')^T \mathbf{t}_{m-1} + \alpha \mathbf{p}$$
Stopping condition: $\Delta_m = \|\mathbf{t}_m - \mathbf{t}_{m-1}\|_2 < \text{tol}$.

#### Theorem (General Iteration Bound):
For any contraction parameter $\alpha \in (0, 1)$ and tolerance $\text{tol} > 0$, the successive-iterate Euclidean stopping condition is guaranteed to hold for:
$$m \ge m^*(\alpha, \text{tol}) = \left\lceil \frac{\ln(\text{tol} / 2)}{\ln(1 - \alpha)} \right\rceil$$
- For the default configuration $\alpha = 0.15$ and $\text{tol} = 10^{-6}$:
  $$m^*(0.15, 10^{-6}) = \left\lceil \frac{\ln(5 \times 10^{-7})}{\ln(0.85)} \right\rceil = 90 \le \text{max\_iter} = 100$$
- This guarantee holds **specifically for $\alpha = 0.15$ and $\text{tol} = 10^{-6}$** when $\text{max\_iter} \ge 90$. If $\alpha$ is decreased (e.g. $\alpha = 0.10 \implies m^* = 138$), $\text{max\_iter} = 100$ may be reached before convergence.

---

## 10. Exact Vanilla Equivalence & Five-Way Baseline Contract

### 10.1 Equivalence Domain ($\mathcal{D}_{\text{equiv}}$)
Equivalence between `MODE_VANILLA` and `EigenTrustEngine` ([`src/layer3_eigentrust.py:808-844`](file:///d:/pki_casestudy/src/layer3_eigentrust.py#L808-L844)) is defined strictly on:
$$\mathcal{D}_{\text{equiv}} = \{(\text{peers}, \text{supernodes}, \text{raw\_s}) \mid \text{peers are unique}, |\text{peers}| \ge 1, \text{supernodes} \subseteq \text{peers}, s \in \mathbb{R} \text{ finite}\}$$
- Within $\mathcal{D}_{\text{equiv}}$, `MODE_VANILLA` achieves **exact bitwise floating-point equality (`np.array_equal == True`, `max_diff = 0.0`)** by omitting the post-iteration `t / t_sum` division step that `EigenTrustEngine` does not perform.
- Outside $\mathcal{D}_{\text{equiv}}$ (empty networks, duplicate peers, `NaN`/`Inf` scores), `MODE_VANILLA` performs an **intentional defensive divergence** to prevent crashes and state corruption.

### 10.2 Five-Way Comparison Matrix

| Mode Identifier | Base Matrix Construction | Fault / State Nullification | Evidence Weighting ($\Phi_{\text{edge}}$) | Topology Damping ($\Omega_{ij}$) | Target Baseline |
| :--- | :--- | :---: | :---: | :---: | :--- |
| `MODE_VANILLA` | $A_{ij} = \max(S_{ij}, 0)$ | Disabled | Disabled | Disabled | **Exact Vanilla EigenTrust** (bitwise identical to `EigenTrustEngine` on $\mathcal{D}_{\text{equiv}}$) |
| `MODE_EVIDENCE_ONLY` | $A_{ij} = \Phi_{\text{edge}}(E) \cdot \gamma_{\text{dispute}}$ | Active ($\gamma_{\text{fault}}$) | Active | Disabled ($\Omega = 1$) | **Ablation B** (Evidence weighting isolation) |
| `MODE_TOPOLOGY_ONLY` | $A_{ij} = \max(S_{ij}, 0)$ | Disabled | Disabled | Active ($\Omega_{ij}$) | **Ablation C** (Topology damping isolation) |
| `MODE_FULL_EW` | $A_{ij} = \Phi_{\text{edge}}(E) \cdot \gamma_{\text{dispute}}$ | Active ($\gamma_{\text{fault}}$) | Active | Active ($\Omega_{ij}$) | **Proposed Algorithm** (EW-EigenTrust v1.7) |
| `MODE_LOCAL_ONLY` | Direct row sums $\sum_k \max(S_{ik}, 0)$ | Disabled | Disabled | Disabled | **Baseline 2** (Zero-propagation local tallies) |

---

## 11. Authoritative Pseudocode (v1.7)

```python
"""
Evidence-Weighted EigenTrust with Topology-Aware Collusion Damping (EW-EigenTrust v1.7)
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


def compute_ew_eigentrust_v1_7(
    peers: List[str],
    supernodes: List[str],
    raw_s_matrix: Dict[Tuple[str, str], float],
    evidence_journal: Any = None,
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
    Computes global trust vector using EW-EigenTrust v1.7.
    Returns: (trust_scores: Dict[str, float], converged: bool, executed_iters: int)
    """
    # 1. Parameter Validation (Reject bool explicitly)
    if mode not in TrustComputationMode.VALID_MODES:
        raise ValueError(f"Invalid trust computation mode: {mode}")
    if isinstance(alpha, bool) or not (isinstance(alpha, (int, float)) and math.isfinite(alpha) and 0.0 < alpha < 1.0):
        raise ValueError(f"alpha must be finite in (0, 1), got {alpha}")
    if isinstance(tol, bool) or not (isinstance(tol, (int, float)) and math.isfinite(tol) and tol > 0.0):
        raise ValueError(f"tol must be finite positive, got {tol}")
    if isinstance(max_iter, bool) or not (isinstance(max_iter, int) and max_iter >= 1):
        raise ValueError(f"max_iter must be an integer >= 1, got {max_iter}")
    if isinstance(k_max, bool) or not (isinstance(k_max, (int, float)) and math.isfinite(k_max) and k_max > 0.0):
        raise ValueError(f"k_max must be finite positive, got {k_max}")
    if isinstance(lambda_sat, bool) or not (isinstance(lambda_sat, (int, float)) and math.isfinite(lambda_sat) and lambda_sat > 0.0):
        raise ValueError(f"lambda_sat must be finite positive, got {lambda_sat}")
    if isinstance(mu_unverified, bool) or not (isinstance(mu_unverified, (int, float)) and math.isfinite(mu_unverified) and 0.0 <= mu_unverified <= 1.0):
        raise ValueError(f"mu_unverified must be in [0, 1], got {mu_unverified}")
    if isinstance(mu_referenced, bool) or not (isinstance(mu_referenced, (int, float)) and math.isfinite(mu_referenced) and 0.0 <= mu_referenced <= 1.0):
        raise ValueError(f"mu_referenced must be in [0, 1], got {mu_referenced}")
    if mu_unverified > mu_referenced:
        raise ValueError(f"mu_unverified ({mu_unverified}) cannot exceed mu_referenced ({mu_referenced})")
    if isinstance(beta_entropy, bool) or not (isinstance(beta_entropy, (int, float)) and math.isfinite(beta_entropy) and beta_entropy > 0.0):
        raise ValueError(f"beta_entropy must be finite positive, got {beta_entropy}")
    if isinstance(theta_penalty, bool) or not (isinstance(theta_penalty, (int, float)) and math.isfinite(theta_penalty) and 0.0 <= theta_penalty <= 1.0):
        raise ValueError(f"theta_penalty must be in [0, 1], got {theta_penalty}")
    if isinstance(epsilon_floor, bool) or not (isinstance(epsilon_floor, (int, float)) and math.isfinite(epsilon_floor) and 0.0 < epsilon_floor <= 1.0):
        raise ValueError(f"epsilon_floor must be in (0, 1], got {epsilon_floor}")
    if isinstance(delta_reg, bool) or not (isinstance(delta_reg, (int, float)) and math.isfinite(delta_reg) and delta_reg > 0.0):
        raise ValueError(f"delta_reg must be finite positive, got {delta_reg}")
    if isinstance(tau_seconds, bool) or not (isinstance(tau_seconds, (int, float)) and math.isfinite(tau_seconds) and tau_seconds > 0.0):
        raise ValueError(f"tau_seconds must be finite positive, got {tau_seconds}")
    if reference_time is not None:
        if isinstance(reference_time, bool) or not (isinstance(reference_time, (int, float)) and math.isfinite(reference_time)):
            raise ValueError(f"reference_time must be a finite float or None, got {reference_time}")

    # 2. Canonical Peer Set & Empty Network Handling
    if not peers:
        return {}, True, 0

    canonical_peers = sorted(list(set(str(p) for p in peers if p and isinstance(p, str))))
    n = len(canonical_peers)
    if n == 0:
        return {}, True, 0

    peer_to_idx = {did: idx for idx, did in enumerate(canonical_peers)}
    valid_supernodes = sorted(list(set(str(sn) for sn in (supernodes or []) if str(sn) in peer_to_idx)))
    manifest_roots = {str(r).lower() for r in (known_manifest_roots or set()) if isinstance(r, str)}
    delivery_keys = set()
    if verified_delivery_keys:
        for k in verified_delivery_keys:
            if isinstance(k, tuple) and len(k) == 4:
                delivery_keys.add((str(k[0]), str(k[1]), str(k[2]).lower(), str(k[3])))

    states = peer_states or {}
    certified_suspected = set(str(s) for s in (certified_suspicion_dids or set()))
    t_ref = float(reference_time) if reference_time is not None else None

    # 3. Pre-trusted restart vector p
    p = np.zeros(n, dtype=np.float64)
    if valid_supernodes:
        sn_weight = 1.0 / len(valid_supernodes)
        for sn in valid_supernodes:
            p[peer_to_idx[sn]] = sn_weight
    else:
        p.fill(1.0 / n)

    # 4. Fast path: Local-only baseline
    if mode == TrustComputationMode.LOCAL_ONLY:
        scores = {}
        total = 0.0
        for src in canonical_peers:
            s_sum = 0.0
            for dst in canonical_peers:
                if dst != src:
                    val = raw_s_matrix.get((src, dst), 0.0)
                    if not isinstance(val, bool) and isinstance(val, (int, float)) and math.isfinite(val):
                        s_sum += max(0.0, float(val))
            scores[src] = s_sum
            total += s_sum
        if total > 0.0:
            return {did: float(v / total) for did, v in scores.items()}, True, 0
        return {did: float(1.0 / n) for did in canonical_peers}, True, 0

    # 5. Extract journal entries defensively
    certified_fault_accused: Set[str] = set()
    pair_entries: Dict[Tuple[str, str], List[Any]] = {}

    if mode in (TrustComputationMode.EVIDENCE_ONLY, TrustComputationMode.FULL_EW):
        raw_entries = []
        if evidence_journal is not None:
            if hasattr(evidence_journal, "get_all_entries") and callable(evidence_journal.get_all_entries):
                raw_entries = evidence_journal.get_all_entries()
            elif hasattr(evidence_journal, "_entries") and isinstance(evidence_journal._entries, dict):
                raw_entries = list(evidence_journal._entries.values())

        for entry in raw_entries:
            entry_type = getattr(entry, "entry_type", "")
            details = getattr(entry, "details", {})
            if not isinstance(details, dict):
                details = {}

            if entry_type == "FAULT_EVIDENCE":
                accused = details.get("accused_did")
                if isinstance(accused, str) and accused in peer_to_idx:
                    certified_fault_accused.add(accused)
            elif entry_type == "RECEIPT":
                c = details.get("client_did")
                s = details.get("server_did")
                if isinstance(c, str) and isinstance(s, str) and c in peer_to_idx and s in peer_to_idx and c != s:
                    pair_entries.setdefault((c, s), []).append(entry)

    # 6. Construct base interaction matrix A_ij
    A = np.zeros((n, n), dtype=np.float64)

    for i, src in enumerate(canonical_peers):
        for j, dst in enumerate(canonical_peers):
            if i == j:
                continue

            # Pure Vanilla Mode: Bit-for-bit exact match to EigenTrustEngine
            if mode == TrustComputationMode.VANILLA:
                raw_score = raw_s_matrix.get((src, dst), 0.0)
                if isinstance(raw_score, bool) or not isinstance(raw_score, (int, float)) or not math.isfinite(raw_score):
                    raw_score = 0.0
                A[i, j] = max(0.0, float(raw_score))
                continue

            # Topology-Only Mode: Raw scores damped by topology
            if mode == TrustComputationMode.TOPOLOGY_ONLY:
                raw_score = raw_s_matrix.get((src, dst), 0.0)
                if isinstance(raw_score, bool) or not isinstance(raw_score, (int, float)) or not math.isfinite(raw_score):
                    raw_score = 0.0
                A[i, j] = max(0.0, float(raw_score))
                continue

            # Proposed Evidence Modes (EVIDENCE_ONLY, FULL_EW):
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
                details = getattr(e, "details", {})
                if not isinstance(details, dict):
                    continue

                raw_rating = details.get("rating", 1.0)
                try:
                    if isinstance(raw_rating, bool):
                        continue
                    rating_val = float(raw_rating)
                    if not math.isfinite(rating_val):
                        continue
                except (ValueError, TypeError):
                    continue

                if rating_val > 0.0:
                    n_pos_count += 1.0
                    m_root = str(details.get("merkle_root", "")).strip().lower()
                    tx_id = str(getattr(e, "entry_id", ""))

                    if (src, dst, m_root, tx_id) in delivery_keys:
                        gamma_ev = 1.00  # Tier 3: Local Verified Delivery
                    elif m_root and m_root in manifest_roots:
                        gamma_ev = mu_referenced  # Tier 2: Manifest Referenced
                    else:
                        gamma_ev = mu_unverified  # Tier 1: Unindexed Receipt

                    raw_ts = details.get("receipt_timestamp", getattr(e, "timestamp", 0.0))
                    try:
                        e_ts = float(raw_ts)
                        if not math.isfinite(e_ts):
                            e_ts = 0.0
                    except (ValueError, TypeError):
                        e_ts = 0.0

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
                elif rating_val < 0.0:
                    n_neg_count += 1.0
                else:
                    pass  # rating_val == 0.0 is neutral, ignored

            if n_pos_count > 0.0 and e_pos > 0.0:
                gamma_dispute = max(0.0, 1.0 - (2.0 * n_neg_count / (n_pos_count + 1.0)))
                phi_val = k_max * math.tanh((lambda_sat * e_pos) / k_max)
                A[i, j] = phi_val * gamma_dispute
            else:
                A[i, j] = 0.0

    # 7. Topology Damping Matrix Omega_ij
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

    # 8. Effective Matrix S_prime and Stochastic Matrix C_prime
    S_prime = Omega * A
    C_prime = np.zeros((n, n), dtype=np.float64)

    for i in range(n):
        row_total = np.sum(S_prime[i, :])
        if row_total > 0:
            C_prime[i, :] = S_prime[i, :] / row_total
        else:
            C_prime[i, :] = p  # Dangling row fallback

    # 9. Power Iteration (Euclidean L2 norm stopping criterion)
    t = p.copy()
    C_prime_T = C_prime.T
    converged = False
    executed_iters = 0

    for iteration in range(1, max_iter + 1):
        executed_iters = iteration
        t_next = (1.0 - alpha) * np.dot(C_prime_T, t) + (alpha * p)
        delta = np.linalg.norm(t_next - t)
        t = t_next
        if delta < tol:
            converged = True
            break

    # NOTE: In MODE_VANILLA, t is returned directly without t / np.sum(t)
    # to preserve bit-for-bit floating-point equality with EigenTrustEngine.
    return {canonical_peers[i]: float(t[i]) for i in range(n)}, converged, executed_iters
```

---

## 12. Audited Acceptance Criteria Table

| Criterion | Target Property | Formal Evidentiary Classification | Verified Evidentiary Status |
| :---: | :--- | :---: | :--- |
| **AC-1** | Intrinsic Edge Bound: $S'_{ij} < 10.0$ for all $(i, j)$ under admissible parameters | **MATHEMATICALLY_ESTABLISHED** | Analytically proved: $\Phi_{\text{edge}} < K_{\max} = 10.0$, $\Omega \le 1.0$, $\gamma \le 1.0$. |
| **AC-2** | Delivery Linkage: Three-tier evidence credit based on 4-tuple key | **SPECIFIED_PENDING_IMPLEMENTATION** | Fully specified in Section 6; requires Phase 8 journal schema update before execution. |
| **AC-3** | Certified Fault Nullification: $S'_{ij} = 0$ on certified fault/revocation | **SPECIFIED_PENDING_IMPLEMENTATION** | Fully specified in Section 7.5; awaits Phase 8 unit test execution. |
| **AC-4** | Asymmetric Provider Immunity: Pure uploaders receive $\Omega_{kp} = 1.0$ | **MATHEMATICALLY_ESTABLISHED** | Analytically proved: $\min(A_{kp}, A_{pk}) = 0 \implies \rho = 0 \implies \sigma = 0$. |
| **AC-5** | Interaction Entropy Bounds: $0.0 \le H_i \le 1.0$ | **MATHEMATICALLY_ESTABLISHED** | Analytically proved via Shannon entropy properties and log base normalization. |
| **AC-6** | Row Stochasticity: $\sum_j C'_{ij} = 1.0 \pm 10^{-12}$ | **MATHEMATICALLY_ESTABLISHED** | Analytically proved via row-sum normalization and dangler fallback. |
| **AC-7** | Simplex Conservation: $\|\mathbf{t}^*\|_1 = 1.0 \pm 10^{-12}$ | **MATHEMATICALLY_ESTABLISHED** | Analytically proved via probability simplex invariance. |
| **AC-8** | Cauchy Iteration Bound: $\|\mathbf{t}_m - \mathbf{t}_{m-1}\|_2 < 10^{-6}$ in $m \le 90$ iters for $(\alpha=0.15, \text{tol}=10^{-6})$ | **MATHEMATICALLY_ESTABLISHED** | Analytically proved via contraction mapping bound ($m^* = 90 \le 100$). |
| **AC-9** | Empty Network & Anchor Fallback: Handles $n=0$ and no valid supernodes | **VERIFIED_BY_REPRODUCIBLE_TEST** | Verified by differential test against live environment in `tests_scratch/phase7_7_differential.py`. |
| **AC-10**| Vanilla Mode Equivalence: `MODE_VANILLA` matches `EigenTrustEngine` on $\mathcal{D}_{\text{equiv}}$ | **VERIFIED_BY_REPRODUCIBLE_TEST** | Verified by differential test: exact bitwise equality (`np.array_equal == True`, `max_diff = 0.0`) across all cases. |

---

## 13. Evidentiary Claim Discipline

- **[STANDARD]:** Ed25519 signatures, full 64-hex DIDs, PoW admission, SHA-256 Merkle trees, Shamir secret sharing, vanilla EigenTrust power iteration.
- **[IMPLEMENTED]:** 7-stage bilateral evidence pipeline, processed-evidence journal ($L_{\text{local}} / L_{\text{sim}}$), certified Merkle contradiction attribution, 3-of-5 supernode quorum revocation.
- **[PROPOSED]:** 4-tuple delivery linkage, intrinsic edge ceiling $\Phi_{\text{edge}}$, regularized reciprocity $\rho_{ij}$, counterparty interaction entropy $H_i$, and topology damping $\Omega_{ij}$.
- **[HYPOTHESIS]:** Hypotheses regarding collusive trust reduction and community preservation under connected collusion.
- **[LIMITATION / BLOCKED]:** Pairwise reciprocity metric $\rho_{ij}$ fails to damp directed cycles ($k \ge 3$); live journal schema lacks `merkle_root` and `receipt_timestamp` in `details`.
