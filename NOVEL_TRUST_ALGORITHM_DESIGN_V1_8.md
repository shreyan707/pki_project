# Novel Trust Algorithm Design v1.8: Evidence-Weighted EigenTrust (EW-EigenTrust) with Structural Collusion Analysis and Descoping of Row-Normalized Damping

**Version:** 1.8.0-FINAL  
**Phase:** Phase 7.8 (Structural Diagnosis, Damping Descoping & Final Specification Seal)  
**Author:** Candidate Shreyan Nayak (23BKT0039) & Independent Mathematical Auditor  
**Date:** October 9, 2026  
**Status:** `PHASE7_8_STATUS: READY_FOR_IMPLEMENTATION`  
**Supercedes:** `NOVEL_TRUST_ALGORITHM_DESIGN_V1_7.md`, `NOVEL_TRUST_ALGORITHM_DESIGN_V1_6.md`, and all earlier versions  

---

## 1. Executive Summary & Core Architectural Decision

Following the rigorous Phase 7.8 structural diagnosis of topology-aware collusion damping, this specification introduces a definitive architectural correction:

1. **The Structural Nullification of Row-Normalized Multiplicative Damping:**
   Analytical derivation and numerical experiments prove that for any closed colluder set $C$, applying multiplicative edge damping $\Omega_{ij}$ *prior* to row normalization **cannot reduce the total stationary trust share of $C$**. Row normalization strictly divides out internal edge scalings. Moreover, when honest peers engage in mutual cooperation, pairwise damping $\Omega$ penalizes honest edges, paradoxically *increasing* transition probabilities from honest nodes into the colluder coalition (inflating colluder trust from $0.5466$ to $0.7342$).
2. **Definitive Descoping of Multiplicative Topology Damping (Recommendation B):**
   In accordance with Phase 7.8 pre-registered experimental controls, **multiplicative topology damping ($\Omega_{ij}$) is descoped from the core novel algorithm to a documented negative ablation result**.
3. **Authoritative Proposed Algorithm: Evidence-Weighted EigenTrust (`MODE_EVIDENCE_ONLY`):**
   The primary proposed algorithm is **Evidence-Weighted EigenTrust (EW-EigenTrust)**, which achieves collusion resistance through:
   - **Intrinsically Bounded Concave Edge Ceilings ($\Phi_{\text{edge}}$):** Strictly caps pairwise trust accumulation at $K_{\max} = 10.0$, eliminating unbounded credit grinding.
   - **Multi-Tier Cryptographic Verification:** Distinguishes verified local deliveries ($\gamma = 1.00$), publisher-manifest references ($\mu = 0.25$), and unindexed co-receipts ($\mu = 0.10$).
   - **Bilateral Dispute Penalties ($\gamma_{\text{dispute}}$):** Exponentially penalizes contested edges.
   - **Certified Fault Nullification ($\gamma_{\text{fault}}$):** Instantly zeroes incoming edges for cryptographic violators.

---

## 2. Attacker Capability Matrix & Cryptographic Boundaries

Strictly compliant with `SECURITY_MODEL.md` v2.2.0-FROZEN:

| Adversary Profile | Allowed Actions (Capabilities) | Infeasible Actions (Cryptographic Boundaries) |
| :--- | :--- | :--- |
| **Connected Sybil Coalition** | • Solve Ed25519 PoW admission<br>• Register into Layer 2 mesh<br>• Mutual $+1.00$ bilateral receipts within coalition<br>• Deliver authentic content to honest peers at bridging probability $p_{\text{bridge}}$ | • **Cannot forge signatures:** Cannot forge honest peer or supernode private keys<br>• **Cannot forge Merkle proofs:** Cannot produce valid inclusion proofs for modified bytes without SHA-256 collision<br>• **Cannot double-spend receipts:** Processed-evidence journal ($L_{\text{local}} / L_{\text{sim}}$) rejects replayed receipts<br>• **Cannot forge bilateral co-signatures:** Cannot unilaterally invent a positive receipt with an honest peer without the honest peer's private key |

---

## 3. Canonical Peer Set & Exact Equivalence Domain ($\mathcal{D}_{\text{equiv}}$)

### 3.1 Canonical Peer Definition
Let the input peer sequence be $\mathcal{P}_{\text{in}} = (p_1, p_2, \dots)$. The **canonical peer sequence** is:
$$\mathcal{V} = \text{sorted}(\text{unique}(\{p \in \mathcal{P}_{\text{in}} \mid p \text{ is a non-empty string}\}))$$
- Dimension: $n = |\mathcal{V}|$.
- Index mapping: $\text{idx}(v) \in \{0, 1, \dots, n-1\}$ for each $v \in \mathcal{V}$.
- Strict Matrix Dimension: All intermediate and final matrices are strictly $(n \times n)$.

### 3.2 Exact Equivalence Domain ($\mathcal{D}_{\text{equiv}}$)
Equivalence between `MODE_VANILLA` and `EigenTrustEngine` ([`src/layer3_eigentrust.py:808-844`](file:///d:/pki_casestudy/src/layer3_eigentrust.py#L808-L844)) is defined strictly on the domain $\mathcal{D}_{\text{equiv}}$, which requires:
1. **Unique Peers:** $\text{len}(\mathcal{P}_{\text{in}}) == \text{len}(\mathcal{V})$.
2. **Non-Empty Network:** $n \ge 1$.
3. **Finite Real Scores:** $s \in \mathbb{R}$ for all entries in `raw_s_matrix` (no `NaN`, `Inf`, or boolean types).
4. **No Self-Edges:** $s_{ii} = 0$ for all $i$.
5. **No External Endpoints:** For all $((u, v), s) \in \text{raw\_s\_matrix}$, $u, v \in \mathcal{V}$.
6. **Unique Supernodes:** $\mathcal{S}_{\text{in}} \subseteq \mathcal{V}$ with $|\mathcal{S}_{\text{in}}| \ge 1$ and no duplicate entries.

#### Verified Equivalence Result:
On $\mathcal{D}_{\text{equiv}}$, `MODE_VANILLA` achieves **exact bitwise floating-point equality (`np.array_equal == True`, `max_diff = 0.0`)** with `EigenTrustEngine`. Across all evaluated cases, the simplex deviation satisfies $|\sum t_i - 1.0| \le 2.22 \times 10^{-16}$.

#### Defensive Intentional Divergence Outside $\mathcal{D}_{\text{equiv}}$:
Outside $\mathcal{D}_{\text{equiv}}$, `compute_ew_eigentrust_v1_8` performs defensive sanitization:
- `NaN` / `Inf` scores are sanitized to `0.0` (preventing output vector corruption).
- Empty networks ($n=0$) return `({}, True, 0)` (preventing `ZeroDivisionError`).
- Duplicate peers and duplicate supernodes are canonicalized (preventing orphaned indices and defective $\sum p_i = 0.5$ vectors).

---

## 4. Parameter Validation Specification (14 Parameters)

Boolean inputs are explicitly rejected for all numeric and integer parameters:

| Parameter | Type | Default | Admissible Range | Mathematical Purpose & Invariants Preserved | Validation Action on Violation |
| :--- | :---: | :---: | :---: | :--- | :--- |
| `mode` | `str` | `"evidence_only"` | `TrustComputationMode.VALID_MODES` | Selects exact computational pipeline | Raises `ValueError` |
| `alpha` | `float` | `0.15` | $0.0 < \alpha < 1.0$ (reject `bool`) | Contraction modulus $c = 1 - \alpha \in (0, 1)$ | Raises `ValueError` |
| `tol` | `float` | `1e-6` | $\text{tol} > 0.0$ and finite (reject `bool`) | Convergence threshold | Raises `ValueError` |
| `max_iter` | `int` | `100` | $\text{max\_iter} \ge 1$ (reject `bool`) | Upper iteration bound | Raises `ValueError` |
| `k_max` | `float` | `10.0` | $k_{\max} > 0.0$ and finite (reject `bool`) | Intrinsic edge ceiling: $S'_{ij} \le k_{\max}$ | Raises `ValueError` |
| `lambda_sat`| `float` | `0.50` | $\lambda_{\text{sat}} > 0.0$ and finite (reject `bool`) | Concave growth rate | Raises `ValueError` |
| `mu_unverified` | `float` | `0.10` | $0.0 \le \mu_{\text{unverified}} \le 1.0$ (reject `bool`) | Tier 1 unindexed receipt discount | Raises `ValueError` |
| `mu_referenced` | `float` | `0.25` | $0.0 \le \mu_{\text{referenced}} \le 1.0$ (reject `bool`) | Tier 2 manifest reference discount; requires $\mu_{\text{unverified}} \le \mu_{\text{referenced}}$ | Raises `ValueError` |
| `beta_entropy` | `float` | `2.0` | $\beta_{\text{entropy}} > 0.0$ and finite (reject `bool`) | Collusion penalty sharpness (ablation) | Raises `ValueError` |
| `theta_penalty`| `float` | `0.85` | $0.0 \le \theta_{\text{penalty}} \le 1.0$ (reject `bool`) | Max damping penalty (ablation) | Raises `ValueError` |
| `epsilon_floor`| `float` | `0.10` | $0.0 < \epsilon_{\text{floor}} \le 1.0$ (reject `bool`) | Ergodicity floor (ablation) | Raises `ValueError` |
| `delta_reg` | `float` | `2.0` | $\delta_{\text{reg}} > 0.0$ and finite (reject `bool`) | Reciprocity regularization (ablation) | Raises `ValueError` |
| `tau_seconds` | `float` | `86400.0`| $\tau_{\text{seconds}} > 0.0$ and finite (reject `bool`) | Exponential freshness decay half-life | Raises `ValueError` |
| `reference_time`| `float` / `None` | `None` | Finite float or `None` (reject `bool`) | Reference epoch for timestamp freshness | Raises `ValueError` if non-finite float |

---

## 5. Structural Diagnosis of the Damping Rule: The Closed-Set Identity

### 5.1 Theorem: Closed-Set Stationary Trust Invariance
Let the network be partitioned into honest peers $H$ and a colluder coalition $C$, with pre-trusted restart vector $\mathbf{p}$ supported strictly on $H$ ($\sum_{c \in C} p_c = 0$). Suppose $C$ is **closed** (no transitions from $C$ to $H$, i.e. $\sum_{h \in H} C'_{ch} = 0$ for all $c \in C$) and contains no dangling rows.

Then for any transition matrix $C'$ and restart parameter $\alpha \in (0, 1)$, the total stationary trust share of the colluder set satisfies:
$$\sum_{c \in C} t_c = \left(\frac{1 - \alpha}{\alpha}\right) \sum_{h \in H} t_h \sum_{c \in C} C'_{hc}$$

#### Proof:
From the stationary distribution equation $t_j = (1 - \alpha) \sum_i t_i C'_{ij} + \alpha p_j$, summing over $j \in C$:
$$\sum_{c \in C} t_c = (1 - \alpha) \sum_{c \in C} \left( \sum_{h \in H} t_h C'_{hc} + \sum_{c' \in C} t_{c'} C'_{c' c} \right) + \alpha \sum_{c \in C} p_c$$
Because $p_c = 0$ for all $c \in C$, the restart term vanishes. Because $C$ is closed, for every $c' \in C$, $\sum_{c \in C} C'_{c' c} = 1$. Thus:
$$\sum_{c' \in C} t_{c'} \sum_{c \in C} C'_{c' c} = \sum_{c' \in C} t_{c'} = \sum_{c \in C} t_c$$
Substituting this into the sum:
$$\sum_{c \in C} t_c = (1 - \alpha) \sum_{h \in H} t_h \sum_{c \in C} C'_{hc} + (1 - \alpha) \sum_{c \in C} t_c$$
$$\alpha \sum_{c \in C} t_c = (1 - \alpha) \sum_{h \in H} t_h \sum_{c \in C} C'_{hc} \implies \sum_{c \in C} t_c = \left(\frac{1 - \alpha}{\alpha}\right) \sum_{h \in H} t_h \sum_{c \in C} C'_{hc} \quad \blacksquare$$

### 5.2 Mathematical & Security Consequences
1. **Internal Damping Invariance:** Any multiplicative damping $\Omega_{c_1, c_2}$ applied to edges *between* colluders is strictly divided out by row normalization ($\sum_{j \in C} C'_{c_1, j} = 1$). It cannot alter $\sum_{c \in C} t_c$ by a single bit.
2. **Honest Damping Vulnerability:** When honest nodes engage in dense mutual cooperation, $\Omega$ penalizes honest-to-honest edges. This shrinks the honest row denominator, which *increases* the relative transition weight into the colluder set ($C'_{h, c} \uparrow$). In Topology (a), this caused colluder trust share to inflate from $0.5466$ to $0.7342$.
3. **Directed Cycle Blindness:** Pure-uploader immunity (AC-4) requires that unreciprocated edges receive $\Omega = 1.00$. In any directed cycle of length $k \ge 3$, all edges are pairwise unreciprocated ($A_{ji} = 0$). Thus $\Omega_{ij} = 1.00$ on all directed cycles, providing zero damping.

---

## 6. Multi-Tier Evidence Evaluation & Bounded Edge Strength

In EW-EigenTrust v1.8, the effective transition matrix is constructed directly from cryptographically validated evidence:

$$S'_{ij} = \Phi_{\text{edge}}(E_{\text{pos}}(i, j)) \cdot \gamma_{\text{dispute}}(i, j) \cdot \gamma_{\text{fault}}(i, j) \quad \text{for } i \ne j, \quad S'_{ii} = 0$$

### 6.1 Bounded Concave Edge Ceiling ($\Phi_{\text{edge}}$)
$$\Phi_{\text{edge}}(E) = K_{\text{max}} \cdot \tanh\left(\frac{\lambda_{\text{sat}} \cdot E}{K_{\text{max}}}\right)$$
- **Real Arithmetic Bound:** $\Phi_{\text{edge}}(E) < K_{\max} = 10.0$ strictly for all finite $E \ge 0$.
- **IEEE 754 Float64 Bound:** In float64 arithmetic, $\tanh(x)$ saturates to `1.0` for $x \ge 19.1$. Thus $S'_{ij} \le 10.0$ holds in float64 (equality can be attained at saturation).

### 6.2 Three-Tier Evidence Accumulation ($E_{\text{pos}}$)
$$E_{\text{pos}}(i, j) = \sum_{e \in \mathcal{E}_{ij}^{+}} \gamma_{\text{evidence}}(e) \cdot \gamma_{\text{time}}(t_{\text{ref}} - t_e)$$
$$\gamma_{\text{evidence}}(e) = \begin{cases}
1.00 & \text{if } (e.\text{client\_did}, e.\text{server\_did}, e.\text{merkle\_root}, e.\text{tx\_id}) \in \mathcal{D}_{\text{local}} \quad (\text{Tier 3: Verified Delivery}) \\
0.25 & \text{if } e.\text{merkle\_root} \in \mathcal{R}_{\text{manifests}} \quad (\text{Tier 2: Known Manifest Reference}) \\
0.10 & \text{otherwise} \quad (\text{Tier 1: Unindexed Bilateral Receipt})
\end{cases}$$

### 6.3 Timestamp Freshness ($\gamma_{\text{time}}$) & Dispute Penalties ($\gamma_{\text{dispute}}$)
$$\gamma_{\text{time}}(\Delta t) = \begin{cases}
1.0 & \text{if } -60.0 \le \Delta t \le 0.0 \quad (\text{Clock drift tolerance}) \\
0.0 & \text{if } \Delta t < -60.0 \quad (\text{Excessive future timestamp rejected}) \\
\exp\left(-\frac{\Delta t}{\tau}\right) & \text{if } \Delta t > 0.0 \quad (\tau = 86400.0\text{ s})
\end{cases}$$
$$\gamma_{\text{dispute}}(N_{\text{pos}}, N_{\text{neg}}) = \begin{cases}
0.0 & \text{if } N_{\text{pos}} = 0 \\
\max\left(0.0, \, 1.0 - \frac{2 \cdot N_{\text{neg}}}{N_{\text{pos}} + 1.0}\right) & \text{if } N_{\text{pos}} > 0
\end{cases}$$
Receipts with `rating == 0.0` are neutral and skipped from both $N_{\text{pos}}$ and $N_{\text{neg}}$.

### 6.4 Certified Fault Nullification ($\gamma_{\text{fault}}$)
$$\gamma_{\text{fault}}(i, j) = \begin{cases}
0.0 & \text{if } j \in \text{accused\_dids}(\mathcal{F}) \lor \text{peer\_states}[j] \in \{\text{REVOCATION\_PROPOSED}, \text{REVOKED}\} \\
    & \quad \lor (\text{peer\_states}[j] == \text{SUSPECTED} \land \text{is\_certified\_suspicion}(j)) \\
1.0 & \text{otherwise}
\end{cases}$$

---

## 7. Phase 8 Implementation Prerequisites

The following three items represent Phase 8 code changes and unit tests; they do **not** block the mathematical specification:
1. **Journal Commit Schema Update:** In `src/layer3_eigentrust.py:691`, `record_receipt()` must commit `merkle_root` and `receipt_timestamp` into `details`. (Values are authenticated fields from `BilateralReceipt`).
2. **Public Journal Accessor:** `LocalEvidenceJournal` in `src/layer3_eigentrust.py` must provide a public method `get_all_entries() -> List[JournalEntry]`.
3. **Verified Delivery Set Population:** In `src/network_simulator.py:344`, upon successful execution of `resp.verify()`, the client must populate `verified_delivery_keys.add((req.client_did, req.server_did, req.merkle_root.lower(), tx_id))`.

---

## 8. Power Iteration & Strict Convergence Bound

Let row-normalized stochastic matrix $C'$ be defined by $C'_{ij} = S'_{ij} / \sum_k S'_{ik}$ if row sum $> 0$, else $p_j$.
Initialize $\mathbf{t}_0 = \mathbf{p}$. For loop iteration $m = 1, 2, \dots, \text{max\_iter}$:
$$\mathbf{t}_m = (1 - \alpha) (C')^T \mathbf{t}_{m-1} + \alpha \mathbf{p}$$
Stopping condition: $\Delta_m = \|\mathbf{t}_m - \mathbf{t}_{m-1}\|_2 < \text{tol}$.

#### Theorem (Strict General Convergence Bound):
For any contraction parameter $\alpha \in (0, 1)$ and tolerance $\text{tol} > 0$, the stopping condition is guaranteed to be satisfied in:
$$m \ge m^*(\alpha, \text{tol}) = \left\lfloor \frac{\ln(\text{tol} / 2)}{\ln(1 - \alpha)} \right\rfloor + 1 \text{ iterations}$$
- For $\alpha = 0.15$ and $\text{tol} = 10^{-6}$:
  $$m^*(0.15, 10^{-6}) = \left\lfloor \frac{-14.508658}{-0.162519} \right\rfloor + 1 = \lfloor 89.2736 \rfloor + 1 = 89 + 1 = 90 \le \text{max\_iter} = 100$$
- This guarantee holds specifically for $\alpha = 0.15, \text{tol} = 10^{-6}$. For smaller $\alpha$ (e.g. $\alpha = 0.10 \implies m^* = 138$), $\text{max\_iter}$ must be increased accordingly.

---

## 9. Authoritative Pseudocode (v1.8)

```python
"""
Evidence-Weighted EigenTrust (EW-EigenTrust v1.8)
Authoritative Implementation Contract for Phase 8.
"""

import math
import numpy as np
from typing import List, Dict, Tuple, Optional, Any, Set


class TrustComputationMode:
    VANILLA = "vanilla_eigentrust"
    EVIDENCE_ONLY = "evidence_only"       # Authoritative proposed EW-EigenTrust
    TOPOLOGY_ONLY = "topology_only"       # Experimental ablation
    FULL_EW = "full_ew_eigentrust"         # Experimental ablation
    LOCAL_ONLY = "local_only"

    VALID_MODES = {VANILLA, EVIDENCE_ONLY, TOPOLOGY_ONLY, FULL_EW, LOCAL_ONLY}


def compute_ew_eigentrust_v1_8(
    peers: List[str],
    supernodes: List[str],
    raw_s_matrix: Dict[Tuple[str, str], float],
    evidence_journal: Any = None,
    peer_states: Optional[Dict[str, Any]] = None,
    certified_suspicion_dids: Optional[Set[str]] = None,
    verified_delivery_keys: Optional[Set[Tuple[str, str, str, str]]] = None,
    known_manifest_roots: Optional[Set[str]] = None,
    mode: str = TrustComputationMode.EVIDENCE_ONLY,
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
    Computes global trust vector using EW-EigenTrust v1.8.
    Returns: (trust_scores: Dict[str, float], converged: bool, executed_iters: int)
    """
    # 1. Parameter Validation (Reject bool strictly)
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

            # Vanilla & Topology-Only Modes: Direct raw S matrix
            if mode in (TrustComputationMode.VANILLA, TrustComputationMode.TOPOLOGY_ONLY):
                raw_score = raw_s_matrix.get((src, dst), 0.0)
                if isinstance(raw_score, bool) or not isinstance(raw_score, (int, float)) or not math.isfinite(raw_score):
                    raw_score = 0.0
                A[i, j] = max(0.0, float(raw_score))
                continue

            # Evidence Modes (EVIDENCE_ONLY, FULL_EW):
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
                    pass  # rating_val == 0.0 is neutral, skipped

            if n_pos_count > 0.0 and e_pos > 0.0:
                gamma_dispute = max(0.0, 1.0 - (2.0 * n_neg_count / (n_pos_count + 1.0)))
                phi_val = k_max * math.tanh((lambda_sat * e_pos) / k_max)
                A[i, j] = phi_val * gamma_dispute
            else:
                A[i, j] = 0.0

    # 7. Topology Damping (Active strictly in ablation modes)
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

    return {canonical_peers[i]: float(t[i]) for i in range(n)}, converged, executed_iters
```

---

## 10. Audited Acceptance Criteria Table

| Criterion | Target Property | Formal Evidentiary Classification | Verified Evidentiary Status |
| :---: | :--- | :---: | :--- |
| **AC-1** | Intrinsic Edge Bound: $S'_{ij} < 10.0$ in $\mathbb{R}$, $S'_{ij} \le 10.0$ in float64 | **MATHEMATICALLY_ESTABLISHED** | Analytically proved: $\Phi_{\text{edge}} < K_{\max}$ in $\mathbb{R}$; saturated to 10.0 in float64. |
| **AC-2** | Delivery Linkage: Three-tier evidence credit based on 4-tuple key | **SPECIFIED_PENDING_IMPLEMENTATION** | Fully specified in Section 6; Phase 8 prerequisite with required tests. |
| **AC-3** | Certified Fault Nullification: $S'_{ij} = 0$ on certified fault/revocation | **SPECIFIED_PENDING_IMPLEMENTATION** | Fully specified in Section 6.4; awaits Phase 8 unit test execution. |
| **AC-4** | Asymmetric Provider Immunity: Pure uploaders receive $\Omega_{kp} = 1.0$ | **MATHEMATICALLY_ESTABLISHED** | Analytically proved: $\min(A_{kp}, A_{pk}) = 0 \implies \rho = 0 \implies \sigma = 0$. |
| **AC-5** | Interaction Entropy Bounds: $0.0 \le H_i \le 1.0$ | **MATHEMATICALLY_ESTABLISHED** | Analytically proved via Shannon entropy properties and log base normalization. |
| **AC-6** | Row Stochasticity: $\sum_j C'_{ij} = 1.0 \pm 10^{-12}$ | **MATHEMATICALLY_ESTABLISHED** | Analytically proved via row-sum normalization and dangler fallback. |
| **AC-7** | Simplex Conservation: $\|\mathbf{t}^*\|_1 = 1.0 \pm 10^{-12}$ | **MATHEMATICALLY_ESTABLISHED** | Analytically proved via probability simplex invariance. |
| **AC-8** | Cauchy Iteration Bound: $\|\mathbf{t}_m - \mathbf{t}_{m-1}\|_2 < 10^{-6}$ in $m \le 90$ iters for $(\alpha=0.15, \text{tol}=10^{-6})$ | **MATHEMATICALLY_ESTABLISHED** | Analytically proved via strict bound $m^* = \lfloor \ln(\text{tol}/2)/\ln(1-\alpha) \rfloor + 1 = 90$. |
| **AC-9** | Empty Network & Anchor Fallback: Handles $n=0$ and no valid supernodes | **VERIFIED_BY_REPRODUCIBLE_TEST** | Verified on `MODE_VANILLA` in `tests_scratch/phase7_7_differential.log`. |
| **AC-10**| Vanilla Mode Equivalence: `MODE_VANILLA` matches `EigenTrustEngine` on $\mathcal{D}_{\text{equiv}}$ | **VERIFIED_BY_REPRODUCIBLE_TEST** | Verified: exact bitwise equality (`np.array_equal == True`, `max_diff = 0.0`) on $\mathcal{D}_{\text{equiv}}$. |

---

## 11. Evidentiary Claim Discipline

- **[STANDARD]:** Ed25519 signatures, full 64-hex DIDs, PoW admission, SHA-256 Merkle trees, Shamir secret sharing, vanilla EigenTrust power iteration.
- **[IMPLEMENTED]:** 7-stage bilateral evidence pipeline, processed-evidence journal ($L_{\text{local}} / L_{\text{sim}}$), certified Merkle contradiction attribution, 3-of-5 supernode quorum revocation.
- **[PROPOSED]:** 4-tuple delivery linkage, intrinsic concave edge ceiling $\Phi_{\text{edge}}$, dispute penalty $\gamma_{\text{dispute}}$, and certified fault nullification $\gamma_{\text{fault}}$.
- **[DESCOPED / ABLATION]:** Multiplicative topology damping $\Omega_{ij}$ is descoped from the core algorithm and preserved strictly as an experimental ablation due to the closed-set identity invariance and honest-edge damping vulnerability.
- **[HYPOTHESIS]:** Hypotheses regarding collusive trust reduction under EW-EigenTrust in large swarms.
