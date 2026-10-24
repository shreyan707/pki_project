# Novel Trust Algorithm Design v1.4: Evidence-Weighted EigenTrust with Topology-Aware Collusion Damping (EW-EigenTrust)

**Version:** 1.4.0-FINAL  
**Phase:** Phase 7.4 (Adversarial Security Audit & Final Implementation Gate Readiness)  
**Author:** Candidate Shreyan Nayak (23BKT0039) & Independent Security Auditor  
**Date:** October 9, 2026  
**Status:** `PHASE7_4_STATUS: READY_FOR_IMPLEMENTATION`  
**Supercedes:** `NOVEL_TRUST_ALGORITHM_DESIGN_V1_3.md`, `NOVEL_TRUST_ALGORITHM_DESIGN_V1_2.md`, `NOVEL_TRUST_ALGORITHM_DESIGN_V1_1.md`, and `NOVEL_TRUST_ALGORITHM_DESIGN.md`  

---

## 1. Research Baseline & The Connected-Collusion Problem

In decentralized P2P content-delivery swarms, trust management must evaluate peer reliability without a centralized credit authority. The Phase 1–6 baseline protocol implements **Vanilla EigenTrust** (Kamvar et al., 2003):

$$\mathbf{t}^{(k+1)} = (1 - \alpha) C^T \mathbf{t}^{(k)} + \alpha \mathbf{p}$$

where $C_{ij} = \frac{\max(S_{ij}, 0)}{\sum_k \max(S_{ik}, 0)}$ and $\mathbf{p}$ is the stationary distribution over pre-trusted supernodes.

### The Connected-Collusion Vulnerability (Phase 6 Empirical Finding)
1. **Isolated Sybils:** Completely disconnected Sybil clusters exchanging mutual upvotes are damped to near-zero collective trust share ($0.00\%$) because no stationary random-walk paths connect pre-trusted supernodes to the Sybil subgraph.
2. **Connected Collusion with Honest Bridging:** When colluding Sybils establish bridging transactions to honest peers ($p_{\text{bridge}} \in [0.05, 0.40]$), stationary probability mass leaks across the bridge into the collusive ring. Dense internal reciprocal upvoting traps random walks, causing reputation inflation that vanilla EigenTrust cannot distinguish from authentic community service.

---

## 2. Attacker Capability Matrix & Cryptographic Boundaries

The attack model formalizes **Connected Collusion** while remaining strictly compliant with `SECURITY_MODEL.md` v2.2.0-FROZEN:

| Adversary Profile | Allowed Actions (Capabilities) | Infeasible Actions (Cryptographic Boundaries) |
| :--- | :--- | :--- |
| **Connected Sybil Coalition** | • Solve Ed25519 PoW admission<br>• Register into Layer 2 mesh<br>• Mutual $+1.00$ bilateral receipts within coalition<br>• Deliver authentic content to honest peers at bridging probability $p_{\text{bridge}}$ | • **Cannot forge signatures:** Cannot forge honest peer or supernode private keys<br>• **Cannot forge Merkle proofs:** Cannot produce valid inclusion proofs for modified bytes without SHA-256 collision<br>• **Cannot double-spend receipts:** Processed-evidence journal ($L_{\text{local}} / L_{\text{sim}}$) rejects replayed receipts<br>• **Cannot forge bilateral co-signatures:** Cannot unilaterally invent a positive receipt with an honest peer without the honest peer's private key |

---

## 3. Cryptographic Linkage Contract & Journal Storage

### 3.1 Authenticated Delivery Linkage
A critical finding of the Phase 7.4 audit is that `BilateralReceipt` does **not** contain a `content_id` on the wire. Inferring verified delivery from an unauthenticated `content_id` is insecure.

In the protocol lifecycle (`src/network_simulator.py:305-365`):
1. Client sends signed `ContentRequest` ($req\_id, content\_id, chunk\_index, merkle\_root, nonce_{req}$).
2. Server responds with signed `ChunkResponse` ($req\_id, chunk\_bytes, chunk\_hash, proof\_hash, merkle\_root, \Pi_k$).
3. Client executes `resp.verify(server_pubkey, req)` and verifies Merkle inclusion `verify_merkle_proof()`.
4. Upon successful verification, client creates `tx_id = f"tx-{req_id}"` and co-signs `BilateralReceipt`.

The client-local verified delivery record $\mathcal{D}_{\text{local}}$ is therefore indexed by the 4-tuple:
$$\text{DeliveryKey} = (client\_did, server\_did, merkle\_root, tx\_id)$$

### 3.2 Phase 8 Non-Breaking Journal Extension Contract
In `src/layer3_eigentrust.py:691`, `record_receipt()` commits:
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
Existing unit tests checking `details["rating"]` or `details["client_did"]` continue to pass without change.

---

## 4. Multi-Tier Evidence Evaluation & Bounded Edge Strength

To eliminate evidence-grinding vulnerabilities where bounded weights multiply unbounded cumulative integers, the **effective transition edge is an intrinsically bounded, strictly concave function of validated evidence**:

$$S'_{ij} = \Omega_{ij} \cdot \Phi_{\text{edge}}(E_{\text{pos}}(i, j)) \cdot \gamma_{\text{dispute}}(i, j) \cdot \gamma_{\text{fault}}(i, j) \quad \text{for } i \ne j, \quad S'_{ii} = 0$$

### 4.1 Concave Edge Ceiling ($\Phi_{\text{edge}}$)
$$\Phi_{\text{edge}}(E) = K_{\text{max}} \cdot \tanh\left(\frac{\lambda_{\text{sat}} \cdot E}{K_{\text{max}}}\right)$$
- **Ceiling:** $K_{\text{max}} = 10.0$ (No edge can exceed $10.0$, regardless of receipt volume).
- **Scale:** $\lambda_{\text{sat}} = 0.50$.
- **Values:** $E = 1 \implies 0.499$, $E = 5 \implies 2.449$, $E = 20 \implies 7.616$, $E \to \infty \implies 10.000$.

### 4.2 Positive Evidence Accumulation ($E_{\text{pos}}$)
$$E_{\text{pos}}(i, j) = \sum_{e \in \mathcal{E}_{ij}^{+}} \gamma_{\text{evidence}}(e) \cdot \gamma_{\text{time}}(t_{\text{ref}} - t_e)$$
where:
$$\gamma_{\text{evidence}}(e) = \begin{cases}
1.00 & \text{if } (e.\text{client\_did}, e.\text{server\_did}, e.\text{merkle\_root}, e.\text{tx\_id}) \in \mathcal{D}_{\text{local}} \quad (\text{Tier 3: Verified Delivery}) \\
0.25 & \text{if } e.\text{merkle\_root} \in \mathcal{R}_{\text{manifests}} \quad (\text{Tier 2: Known Root Reference}) \\
0.10 & \text{otherwise} \quad (\text{Tier 1: Unindexed Co-Receipt})
\end{cases}$$

### 4.3 Deterministic Timestamp Freshness
For $\Delta t = t_{\text{ref}} - t_e$:
$$\gamma_{\text{time}}(\Delta t) = \begin{cases}
1.0 & \text{if } -60.0 \le \Delta t \le 0.0 \quad (\text{Clock drift tolerance}) \\
0.0 & \text{if } \Delta t < -60.0 \quad (\text{Excessive future timestamp}) \\
\exp\left(-\frac{\Delta t}{\tau}\right) & \text{if } \Delta t > 0.0 \quad (\tau = 86400.0\text{ s, 1 day})
\end{cases}$$

### 4.4 Unambiguous Bilateral Dispute Factor ($\gamma_{\text{dispute}}$)
Negative receipts (`"-1.00"`) represent mutual dispute signals. They **do not constitute certified fault evidence**, but penalize the specific pairwise edge:
$$\gamma_{\text{dispute}}(N_{\text{pos}}, N_{\text{neg}}) = \begin{cases}
0.0 & \text{if } N_{\text{pos}} = 0 \\
\max\left(0.0, \, 1.0 - \frac{2 \cdot N_{\text{neg}}}{N_{\text{pos}} + 1.0}\right) & \text{if } N_{\text{pos}} > 0
\end{cases}$$

### 4.5 Certified Fault Nullification ($\gamma_{\text{fault}}$)
$$\gamma_{\text{fault}}(i, j) = \begin{cases}
0.0 & \text{if } j \in \text{accused\_dids}(\mathcal{F}) \lor \text{peer\_states}[j] \in \{\text{REVOCATION\_PROPOSED}, \text{REVOKED}\} \\
    & \quad \lor (\text{peer\_states}[j] == \text{SUSPECTED} \land \text{is\_certified\_suspicion}(j)) \\
1.0 & \text{otherwise}
\end{cases}$$
If peer $j$ has committed certified `FaultEvidenceRecord`s or has reached formal revocation proceedings, **all incoming edges $S'_{ij} = 0$ for all $i$**.

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
- If $A_{ij} = 1, A_{ji} = 1 \implies \rho_{ij} = \frac{2}{4} = 0.50$ (Regularization protects initial transfers).
- If $A_{ji} \gg 0, A_{ij} = 0$ (Dedicated uploader / seedbox) $\implies \min(A_{ij}, A_{ji}) = 0 \implies \rho_{ij} = 0.0$.

### 5.3 Closed-Loop Suspicion Index ($\sigma_{ij}$) & Damping Factor ($\Omega_{ij}$)
$$\sigma_{ij} = \rho_{ij} \cdot \left(1.0 - \min(H_i, H_j)\right)^{\beta_{\text{entropy}}} \quad (\beta_{\text{entropy}} = 2.0)$$
$$\Omega_{ij} = \max\left(\epsilon_{\text{floor}}, \, 1.0 - \theta_{\text{penalty}} \cdot \sigma_{ij}\right) \quad (\theta_{\text{penalty}} = 0.85, \, \epsilon_{\text{floor}} = 0.10)$$

---

## 6. Complete Mathematical Iteration & Cauchy Step Proof

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
$$\mathcal{S}_{\text{valid}} = \text{unique}(\mathcal{S}_{\text{supernodes}}) \cap \mathcal{V}$$
$$p_j = \begin{cases}
\frac{1}{|\mathcal{S}_{\text{valid}}|} & \text{if } j \in \mathcal{S}_{\text{valid}} \\
\frac{1}{n} & \text{if } |\mathcal{S}_{\text{valid}}| = 0 \quad (\text{Fallback}) \\
0 & \text{otherwise}
\end{cases}$$

### Step 4: Power Iteration Operator & Cauchy Step Stopping Condition
Initialize $\mathbf{t}^{(0)} = \mathbf{p}$. For $k = 0, 1, 2, \dots$:
$$\mathbf{t}^{(k+1)} = (1 - \alpha) (C')^T \mathbf{t}^{(k)} + \alpha \mathbf{p} \quad (\alpha = 0.15)$$
Iterate until the Cauchy step difference satisfies:
$$\|\mathbf{t}^{(k+1)} - \mathbf{t}^{(k)}\|_1 < \text{tol} \quad (\text{tol} = 10^{-6})$$
or maximum iterations $k = 100$ is reached.

### Step 5: Proof of the Cauchy Step Iteration Bound
- Under $L_1$ norm contraction with Lipschitz constant $c = 1 - \alpha = 0.85$:
  $$\|\mathbf{t}^{(k+1)} - \mathbf{t}^{(k)}\|_1 \le c^k \|\mathbf{t}^{(1)} - \mathbf{t}^{(0)}\|_1 \le 2(1 - \alpha)^{k+1}$$
- Solving for $\|\mathbf{t}^{(k+1)} - \mathbf{t}^{(k)}\|_1 < \text{tol} = 10^{-6}$:
  $$2(0.85)^{k+1} < 10^{-6} \implies k > \frac{\ln(10^{-6} / 2)}{\ln(0.85)} - 1 \approx 89.27 - 1 = 88.27$$
- **Theorem:** The successive iterate Cauchy stopping condition is mathematically guaranteed to be satisfied in at most **$k^* = 89$ iterations**. Setting `max_iter = 100` provides an exact, proved margin of safety ($100 \ge 89$).

---

## 7. Authoritative Pseudocode (v1.4)

```python
"""
Evidence-Weighted EigenTrust with Topology-Aware Collusion Damping (EW-EigenTrust v1.4)
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


def compute_ew_eigentrust_v1_4(
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
    Computes global trust vector using EW-EigenTrust v1.4.
    Returns: (trust_scores, converged_bool, iterations_executed)
    """
    n = len(peers)
    if n == 0:
        return {}, True, 0

    sorted_peers = sorted(list(set(peers)))
    peer_to_idx = {did: idx for idx, did in enumerate(sorted_peers)}
    valid_supernodes = sorted(list(set(sn for sn in supernodes if sn in peer_to_idx)))
    manifest_roots = {r.lower() for r in (known_manifest_roots or set())}
    delivery_keys = verified_delivery_keys or set()
    states = peer_states or {}
    certified_suspected = certified_suspicion_dids or set()
    t_ref = reference_time

    # 1. Pre-trusted restart vector p
    p = np.zeros(n, dtype=np.float64)
    if valid_supernodes:
        sn_weight = 1.0 / len(valid_supernodes)
        for sn in valid_supernodes:
            p[peer_to_idx[sn]] = sn_weight
    else:
        p.fill(1.0 / n)

    # Fast path: Local-only baseline
    if mode == TrustComputationMode.LOCAL_ONLY:
        scores = {}
        total = 0.0
        for src in sorted_peers:
            s_sum = sum(max(0.0, raw_s_matrix.get((src, dst), 0.0)) for dst in sorted_peers if dst != src)
            scores[src] = s_sum
            total += s_sum
        if total > 0.0:
            return {did: float(v / total) for did, v in scores.items()}, True, 0
        return {did: float(1.0 / n) for did in sorted_peers}, True, 0

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

    # 3. Construct base interaction matrix A_ij
    A = np.zeros((n, n), dtype=np.float64)

    for i, src in enumerate(sorted_peers):
        for j, dst in enumerate(sorted_peers):
            if i == j:
                continue

            # Certified fault nullification
            state_val = str(getattr(states.get(dst), "value", states.get(dst, "ACTIVE")))
            is_cert_fault = (dst in certified_fault_accused)
            is_revoking = (state_val in ("REVOCATION_PROPOSED", "REVOKED"))
            is_cert_susp = (state_val == "SUSPECTED" and dst in certified_suspected)

            if is_cert_fault or is_revoking or is_cert_susp:
                continue

            if mode in (TrustComputationMode.VANILLA, TrustComputationMode.TOPOLOGY_ONLY):
                # Raw matrix S directly
                raw_score = raw_s_matrix.get((src, dst), 0.0)
                A[i, j] = max(0.0, raw_score)
            else:
                # Evidence-weighted mode
                entries = pair_entries.get((src, dst), [])
                e_pos = 0.0
                n_pos_count = 0.0
                n_neg_count = 0.0

                for e in entries:
                    rating_val = e.details.get("rating", 1.0)
                    if rating_val > 0:
                        n_pos_count += 1.0
                        m_root = e.details.get("merkle_root", "").lower()
                        tx_id = e.entry_id

                        # Authenticated 4-tuple delivery key
                        if (src, dst, m_root, tx_id) in delivery_keys:
                            gamma_ev = 1.00  # Tier 3: Verified Delivery
                        elif m_root and m_root in manifest_roots:
                            gamma_ev = mu_referenced  # Tier 2: Manifest Referenced
                        else:
                            gamma_ev = mu_unverified  # Tier 1: Unindexed Receipt

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

                        e_pos += gamma_ev * gamma_time
                    else:
                        n_neg_count += 1.0

                if n_pos_count > 0.0 and e_pos > 0.0:
                    gamma_dispute = max(0.0, 1.0 - (2.0 * n_neg_count / (n_pos_count + 1.0)))
                    phi_val = k_max * math.tanh((lambda_sat * e_pos) / k_max)
                    A[i, j] = phi_val * gamma_dispute
                else:
                    A[i, j] = 0.0

    # 4. Topology Damping Omega_ij
    Omega = np.ones((n, n), dtype=np.float64)

    if mode in (TrustComputationMode.TOPOLOGY_ONLY, TrustComputationMode.FULL_EW):
        # Entropy
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

        # Reciprocity
        for i in range(n):
            for j in range(n):
                if i != j and A[i, j] > 0:
                    a_ij = A[i, j]
                    a_ji = A[j, i]
                    rho_ij = (2.0 * min(a_ij, a_ji)) / (a_ij + a_ji + delta_reg)
                    min_entropy = min(H[i], H[j])
                    sigma_ij = rho_ij * math.pow(1.0 - min_entropy, beta_entropy)
                    Omega[i, j] = max(epsilon_floor, 1.0 - (theta_penalty * sigma_ij))

    # 5. Effective Matrix S_prime and Stochastic Matrix C_prime
    S_prime = Omega * A
    C_prime = np.zeros((n, n), dtype=np.float64)

    for i in range(n):
        row_total = np.sum(S_prime[i, :])
        if row_total > 0:
            C_prime[i, :] = S_prime[i, :] / row_total
        else:
            C_prime[i, :] = p  # Dangling row fallback

    # 6. Power Iteration
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

    # Simplex normalization
    t_sum = np.sum(t)
    if t_sum > 0:
        t = t / t_sum

    return {sorted_peers[i]: float(t[i]) for i in range(n)}, converged, executed_iters
```

---

## 8. Evidentiary Claim Discipline

- **[STANDARD]:** Ed25519 signatures, full 64-hex DIDs, PoW admission, SHA-256 Merkle trees, Shamir secret sharing, vanilla EigenTrust power iteration.
- **[IMPLEMENTED]:** 7-stage bilateral evidence pipeline, processed-evidence journal ($L_{\text{local}} / L_{\text{sim}}$), certified Merkle contradiction attribution, 3-of-5 supernode quorum revocation.
- **[PROPOSED]:** 4-tuple delivery linkage, intrinsic edge ceiling $\Phi_{\text{edge}}$, regularized reciprocity $\rho_{ij}$, counterparty interaction entropy $H_i$, and topology damping $\Omega_{ij}$.
- **[HYPOTHESIS]:** Hypotheses $H_1, H_2, H_3$ regarding collusive trust reduction and community preservation.
- **[MEASURED]:** Empirical metrics reported in `PHASE6_EXPERIMENT_REPORT.md` (e.g. 0% replay acceptance across 495 trials).
- **[NOT ESTABLISHED]:** Universal collusion immunity against arbitrary Byzantine colluders performing majority honest work across all network partitions.
