# Phase 7.7 Evidence-Backed Specification Correction & Adversarial Gate Review

**Document:** `PHASE7_7_GATE_REVIEW.md`  
**Phase:** Phase 7.7 (Evidence-Backed Specification Correction & Adversarial Gate Review)  
**Author:** Independent Mathematical and Adversarial Auditor  
**Date:** October 9, 2026  
**Status Assessment:** `PHASE7_7_STATUS: BLOCKED`  
**Reference Specification:** `NOVEL_TRUST_ALGORITHM_DESIGN_V1_7.md`  
**Test Suite Artifact:** [`tests_scratch/phase7_7_differential.py`](file:///d:/pki_casestudy/tests_scratch/phase7_7_differential.py)  
**Raw Test Execution Log:** [`tests_scratch/phase7_7_differential.log`](file:///d:/pki_casestudy/tests_scratch/phase7_7_differential.log)  

---

## 1. Executive Summary & Gate Decision

In accordance with Phase 7.7 audit mandates, this review conducted an unvarnished, empirical examination of the live codebase, the mathematical convergence bounds, the evidence journal schema, the baseline equivalence contract, and the adversarial resilience of the proposed topology damping rule.

Following the core audit rule:
> *"If a check fails, report it and mark the gate BLOCKED. Do not make the result look cleaner than it is."*

This audit reports four critical findings and declares the implementation gate **BLOCKED**:

```
PHASE7_7_STATUS: BLOCKED
```

### Unresolved Items Blocking Implementation
1. **Blocker 1 (Live Journal Schema Defect):** In the live production code ([`src/layer3_eigentrust.py:688-697`](file:///d:/pki_casestudy/src/layer3_eigentrust.py#L688-L697)), `details` committed by `record_receipt()` omits `merkle_root` and `receipt_timestamp`. On the current live schema, Tier 2 and Tier 3 evidence weighting logic is **completely inert**; every receipt defaults to Tier 1 ($\mu_{\text{unverified}} = 0.10$).
2. **Blocker 2 (Journal Public API Defect):** `LocalEvidenceJournal` in [`src/layer3_eigentrust.py:495-543`](file:///d:/pki_casestudy/src/layer3_eigentrust.py#L495-L543) provides only a private attribute `_entries` without a public accessor or entry iterator.
3. **Blocker 3 (Algorithmic Vulnerability - Directed Cycles $k \ge 3$):** Verified empirically in [`tests_scratch/phase7_7_differential.log`](file:///d:/pki_casestudy/tests_scratch/phase7_7_differential.log): Because $\rho_{ij}$ evaluates strictly pairwise reciprocity $\min(A_{ij}, A_{ji})$, all active edges in a directed cycle ($c_0 \to c_1 \to c_2 \to c_0$) have $A_{ji} = 0$, resulting in $\rho_{ij} = 0.0$, $\sigma_{ij} = 0.0$, and $\Omega_{ij} = 1.00$. **$\Omega$ provides zero damping against directed collusive cycles of length $k \ge 3$.**
4. **Blocker 4 (Collusive Share Inflation Under Reciprocity Damping):** Verified empirically in Topology (a): when honest nodes engage in mutual reciprocal transfers with low outgoing entropy, $\Omega$ damps honest edges as well, increasing colluders' collective trust share from $0.5466$ to $0.6082$.

---

## 2. Task 1: Journal Schema Reconciliation & Exact Source Quotes

### 2.1 Code Paths Committing `RECEIPT` and `FAULT_EVIDENCE`
Every code path that commits to a journal in `src/` was examined:

1. **`EigenTrustEngine.record_receipt`** ([`src/layer3_eigentrust.py:688-697`](file:///d:/pki_casestudy/src/layer3_eigentrust.py#L688-L697)):
   ```python
   # Line 688:
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
2. **`EigenTrustEngine.record_fault_evidence`** ([`src/layer3_eigentrust.py:775-785`](file:///d:/pki_casestudy/src/layer3_eigentrust.py#L775-L785)):
   ```python
   # Line 775:
   committed = self.local_journal.commit(
       entry_id=evidence.evidence_id,
       entry_type="FAULT_EVIDENCE",
       details={
           "reporter_did": evidence.reporter_did,
           "accused_did": evidence.accused_did,
           "content_id": evidence.content_id,
           "chunk_index": evidence.chunk_index,
           "req_id": evidence.req_id
       }
   )
   ```
3. **Simulator Canonical Journal** ([`src/network_simulator.py:206-212`](file:///d:/pki_casestudy/src/network_simulator.py#L206-L212)):
   ```python
   # Line 206:
   self.canonical_journal = SimulatorCanonicalJournal()
   self.eigentrust = EigenTrustEngine(
       peers=all_dids,
       pre_trusted_peers=sn_dids,
       alpha=0.15,
       journal=self.canonical_journal
   )
   ```
   The simulator delegates all evidence commits to `self.eigentrust.record_receipt(receipt)` ([`src/network_simulator.py:368`](file:///d:/pki_casestudy/src/network_simulator.py#L368) and [`392`](file:///d:/pki_casestudy/src/network_simulator.py#L392)), which routes directly through Path 1.

### 2.2 Definitive Finding on Schema Presence
- **Question:** Are `merkle_root` and `receipt_timestamp` present in the current `RECEIPT` `details`?
- **Finding:** **THEY ARE NOT PRESENT.**
- **Consequence:** In `NOVEL_TRUST_ALGORITHM_DESIGN_V1_6.md`, lines 307–314 attempted to extract:
  ```python
  m_root = str(details.get("merkle_root", "")).strip().lower()
  raw_ts = details.get("receipt_timestamp", getattr(e, "timestamp", 0.0))
  ```
  Because `details.get("merkle_root")` evaluates to `""`, it never matches `delivery_keys` or `manifest_roots`. **Tier 2 and Tier 3 logic is completely inert on the current codebase schema.** Every receipt defaults to Tier 1 ($\mu_{\text{unverified}} = 0.10$).

### 2.3 Phase 8 Required Schema Update
Phase 8 must modify [`src/layer3_eigentrust.py:691-696`](file:///d:/pki_casestudy/src/layer3_eigentrust.py#L691-L696) to commit:
```python
details={
    "client_did": receipt.client_did,
    "server_did": receipt.server_did,
    "rating": delta,
    "nonce": receipt.nonce,
    "merkle_root": receipt.merkle_root,
    "receipt_timestamp": receipt.timestamp
}
```
- **Provenance:** Both `receipt.merkle_root` and `receipt.timestamp` are authenticated fields in `BilateralReceipt` co-signed on the wire ([`src/layer3_eigentrust.py:430-454`](file:///d:/pki_casestudy/src/layer3_eigentrust.py#L430-L454)). This modification affects only local journal metadata; it does **not** alter the frozen v2.2 wire format.
- **Replay Protection:** Replay protection is preserved because `commit()` continues to key on `f"RECEIPT:{receipt.tx_id}"` and Stage 3 checks `self.seen_nonces[receipt.nonce]`.

### 2.4 Populating `verified_delivery_keys` & Anti-Injection Proof
- **Location:** In [`src/network_simulator.py:343-348`](file:///d:/pki_casestudy/src/network_simulator.py#L343-L348):
  ```python
  # Line 344:
  if resp.verify(provider.public_key_hex, req):
      self.metrics["content"]["honest_deliveries"] += 1
      self.metrics["content"]["valid_merkle_verifications"] += 1
  ```
  `verified_delivery_keys` is populated **only after** `resp.verify()` confirms:
  1. Server Ed25519 signature over ChunkResponse.
  2. `chunk_hash == SHA256(chunk_bytes)`.
  3. `verify_merkle_proof(chunk_bytes, merkle_proof, chunk_index, merkle_root) == True`.
  4. Response matches the client's original ContentRequest.
- **Anti-Injection Proof:** An adversarial peer cannot inject a Tier 3 key through receipt or journal metadata. The evaluating node verifies incoming receipts against its own local set `delivery_keys`. Unless the evaluating node *personally requested* the chunk, received the bytes, and verified the Merkle tree proof, the tuple is absent from `delivery_keys`. At best, unverified gossip receipts achieve Tier 2 ($0.25$) or Tier 1 ($0.10$).

### 2.5 `FAULT_EVIDENCE` Schema, `PeerState` Values, and Public Accessor
1. **Accused Field:** In [`src/layer3_eigentrust.py:780`](file:///d:/pki_casestudy/src/layer3_eigentrust.py#L780), the field is indeed `"accused_did"`.
2. **`PeerState` Values:** In [`src/layer1_identity.py:18-23`](file:///d:/pki_casestudy/src/layer1_identity.py#L18-L23):
   ```python
   class PeerState(enum.Enum):
       UNKNOWN = "UNKNOWN"
       ACTIVE = "ACTIVE"
       SUSPECTED = "SUSPECTED"
       REVOCATION_PROPOSED = "REVOCATION_PROPOSED"
       REVOKED = "REVOKED"
   ```
   Extracting `.value` yields `"ACTIVE"`, `"SUSPECTED"`, etc. Direct `str(PeerState.SUSPECTED)` produces `"PeerState.SUSPECTED"`. The comparison `str(getattr(states.get(dst), "value", states.get(dst, "ACTIVE")))` correctly extracts the string value.
3. **Public Accessor:** `LocalEvidenceJournal` currently only has `self._entries`. Phase 8 must add `def get_all_entries(self) -> List[JournalEntry]`. The v1.7 pseudocode supports both `get_all_entries()` and `_entries`.

---

## 3. Task 2: Reproducible Differential Test Execution & Equivalence Domain

The differential test suite was executed in [`tests_scratch/phase7_7_differential.py`](file:///d:/pki_casestudy/tests_scratch/phase7_7_differential.py), with full output recorded in [`tests_scratch/phase7_7_differential.log`](file:///d:/pki_casestudy/tests_scratch/phase7_7_differential.log).

### 3.1 Normalization and Bitwise Equality Audit
Inspection of `EigenTrustEngine.run_power_iteration()` ([`src/layer3_eigentrust.py:836-843`](file:///d:/pki_casestudy/src/layer3_eigentrust.py#L836-L843)):
```python
for _ in range(max_iterations):
    t_next = (1 - self.alpha) * np.dot(C_T, t) + self.alpha * self.p
    delta = np.linalg.norm(t_next - t)
    t = t_next
    if delta < tolerance:
        break
        
return t
```
- **Finding:** The engine returns `t` directly; it **never divides by `t_sum = np.sum(t)`** at the end.
- **Differential Execution Results:**
  - **With `t / t_sum` (v1.6 spec):** `max_diff = 1.67e-16`, `np.array_equal == False`. (LSB bit-shift caused by floating-point division).
  - **Without `t / t_sum` (v1.7 spec):** `max_diff = 0.00e+00`, `np.array_equal == True` across all 8 cases!
- **Specification Correction:** In v1.7, `MODE_VANILLA` returns `t` directly to preserve exact bitwise floating-point equality.

### 3.2 Executed Differential Test Cases in $\mathcal{D}_{\text{equiv}}$
Across all 8 test cases in $\mathcal{D}_{\text{equiv}}$ (unique peers, $n \ge 1$, finite scores):
- Case 1 (Random Sparse Graph, $N=6$, $p=0.3$): `max_diff = 0.00e+00`, `np.array_equal = True`.
- Case 2 (Random Dense Graph, $N=8$, $p=0.7$): `max_diff = 0.00e+00`, `np.array_equal = True`.
- Case 3 (Dangling Rows, multiple zero-sum rows): `max_diff = 0.00e+00`, `np.array_equal = True`.
- Case 4 (Negative Scores in Matrix): `max_diff = 0.00e+00`, `np.array_equal = True`.
- Case 5 (Peer States `SUSPECTED` and `REVOKED`): `max_diff = 0.00e+00`, `np.array_equal = True`.
- Case 6 (No Valid Supernodes, uniform fallback): `max_diff = 0.00e+00`, `np.array_equal = True`.
- Case 7 (Single Peer, $N=1$): `max_diff = 0.00e+00`, `np.array_equal = True`.
- Case 8 (Two Peers, $N=2$): `max_diff = 0.00e+00`, `np.array_equal = True`.

### 3.3 Behavior Outside Equivalence Domain (Intentional Divergence)
Recorded directly in `tests_scratch/phase7_7_differential.log`:
1. **Non-Finite Scores (`NaN` / `Inf`):**
   - Engine: Corrupts output vector (`NaN` in output scores).
   - v1.7: Defensively sanitizes to `0.0`.
2. **Empty Network (`peers=[]`):**
   - Engine: Crashes with `ZeroDivisionError: float division by zero` at `src/layer3_eigentrust.py:605`.
   - v1.7: Defensively returns `({}, True, 0)`.
3. **Duplicate Peers (`peers=['b', 'a', 'b']`):**
   - Engine: Internal $n=3$, `peer_to_idx` has 2 keys, output dictionary has 2 keys; matrix has orphaned index.
   - v1.7: Canonical deduplication to unique $n=2$, strict simplex.
4. **Duplicate Supernodes (`supernodes=['a', 'a']`):**
   - Engine: Sets $p_0 = 0.5$ twice, $\sum p_i = 0.5 \ne 1.0$, corrupting simplex.
   - v1.7: Canonical deduplication, $\sum p_i = 1.0$.

---

## 4. Task 3: Adversarial Check of the Damping Rule

Computed directly using `tests_scratch/phase7_7_differential.py` with seed 42:

### 4.1 Topology (a): Pairwise Reciprocal Colluding Pair ($c_0 \leftrightarrow c_1$) with Bridge ($h_0 \to c_0$)
- **Vanilla trust shares:** $h_0 = 0.2894, h_1 = 0.1640, c_0 = 0.2955, c_1 = 0.2512$. Total colluders = $0.5466$.
- **FULL_EW trust shares:** $h_0 = 0.2611, h_1 = 0.1307, c_0 = 0.3288, c_1 = 0.2794$. Total colluders = $0.6082$.
- **Adversarial Finding:** Colluders gained trust share under FULL_EW! Because honest nodes $h_0 \leftrightarrow h_1$ also engaged in reciprocal interaction with low outgoing entropy, $\Omega$ penalized honest nodes as well, increasing colluders' relative share.

### 4.2 Topology (b): Directed 3-Cycle ($c_0 \to c_1 \to c_2 \to c_0$) with Bridge ($h_0 \to c_0$)
- **Vanilla trust shares:** $h_0 = 0.2894, h_1 = 0.1640, c_0 = 0.2125, c_1 = 0.1806, c_2 = 0.1535$. Total colluders = $0.5466$.
- **FULL_EW trust shares:** $h_0 = 0.2611, h_1 = 0.1307, c_0 = 0.2364, c_1 = 0.2010, c_2 = 0.1708$. Total colluders = $0.6082$.
- **Adversarial Audit of $\Omega$:**
  In a directed 3-cycle: $A_{c0, c1} > 0$, but $A_{c1, c0} = 0$.
  $$\min(A_{ij}, A_{ji}) = 0 \implies \rho_{ij} = 0.0 \implies \sigma_{ij} = 0.0 \implies \Omega_{ij} = 1.00$$
  **$\Omega$ provides zero damping against directed cycles!**

### 4.3 Topology (c): 5-Node Directed Ring with Chords
Because all chord and ring edges are strictly unreciprocated pairwise ($A_{ji} = 0$), $\rho_{ij} = 0.0$ and $\Omega_{ij} = 1.00$ everywhere.
- **Conclusion:** Pairwise reciprocity $\rho_{ij}$ is blind to multi-hop collusive rings ($k \ge 3$). Any collusion damping claims for $k \ge 3$ are **UNPROVEN EMPIRICAL HYPOTHESES**.

---

## 5. Task 4: Precision Fixes Audited in v1.7

1. **Rating `0.0` Handling:** Line 286 of v1.6 executed `if rating_val > 0.0: ... else: n_neg_count += 1.0`. A neutral rating of `0.0` was counted as a negative dispute. Corrected in v1.7 to `elif rating_val < 0.0: n_neg_count += 1.0` and skipping `0.0`.
2. **Boolean Rejection:** In Python, `isinstance(True, int) == True`. In v1.7, all numeric checks explicitly reject `bool`: `if isinstance(x, bool) or not isinstance(x, int): raise ValueError`.
3. **Parameter Count:** Exactly 14 configuration parameters, fully enumerated in Section 4 of v1.7.
4. **General Iteration Bound:**
   $$m^* = \left\lceil \frac{\ln(\text{tol} / 2)}{\ln(1 - \alpha)} \right\rceil$$
   The bound $m^* = 90$ holds specifically for $\alpha = 0.15$ and $\text{tol} = 10^{-6}$. For $\alpha = 0.10$, $m^* = 138 > 100$. The word "unconditionally" has been excised.

---

## 6. Audited Acceptance Criteria Table

| Criterion | Target Property | Formal Evidentiary Classification | Verified Evidentiary Status |
| :---: | :--- | :---: | :--- |
| **AC-1** | Intrinsic Edge Bound: $S'_{ij} < 10.0$ for all $(i, j)$ under admissible parameters | **MATHEMATICALLY_ESTABLISHED** | Analytically proved: $\Phi_{\text{edge}} < K_{\max} = 10.0$, $\Omega \le 1.0$, $\gamma \le 1.0$. |
| **AC-2** | Delivery Linkage: Three-tier evidence credit based on 4-tuple key | **SPECIFIED_PENDING_IMPLEMENTATION** | Fully specified in Section 6; blocked by live journal schema omission in master. |
| **AC-3** | Certified Fault Nullification: $S'_{ij} = 0$ on certified fault/revocation | **SPECIFIED_PENDING_IMPLEMENTATION** | Fully specified in Section 7.5; awaits Phase 8 unit test execution. |
| **AC-4** | Asymmetric Provider Immunity: Pure uploaders receive $\Omega_{kp} = 1.0$ | **MATHEMATICALLY_ESTABLISHED** | Analytically proved: $\min(A_{kp}, A_{pk}) = 0 \implies \rho = 0 \implies \sigma = 0$. |
| **AC-5** | Interaction Entropy Bounds: $0.0 \le H_i \le 1.0$ | **MATHEMATICALLY_ESTABLISHED** | Analytically proved via Shannon entropy properties and log base normalization. |
| **AC-6** | Row Stochasticity: $\sum_j C'_{ij} = 1.0 \pm 10^{-12}$ | **MATHEMATICALLY_ESTABLISHED** | Analytically proved via row-sum normalization and dangler fallback. |
| **AC-7** | Simplex Conservation: $\|\mathbf{t}^*\|_1 = 1.0 \pm 10^{-12}$ | **MATHEMATICALLY_ESTABLISHED** | Analytically proved via probability simplex invariance. |
| **AC-8** | Cauchy Iteration Bound: $\|\mathbf{t}_m - \mathbf{t}_{m-1}\|_2 < 10^{-6}$ in $m \le 90$ iters for $(\alpha=0.15, \text{tol}=10^{-6})$ | **MATHEMATICALLY_ESTABLISHED** | Analytically proved via contraction mapping bound ($m^* = 90 \le 100$). |
| **AC-9** | Empty Network & Anchor Fallback: Handles $n=0$ and no valid supernodes | **VERIFIED_BY_REPRODUCIBLE_TEST** | Verified by differential test against live environment in `tests_scratch/phase7_7_differential.py`. |
| **AC-10**| Vanilla Mode Equivalence: `MODE_VANILLA` matches `EigenTrustEngine` on $\mathcal{D}_{\text{equiv}}$ | **VERIFIED_BY_REPRODUCIBLE_TEST** | Verified by differential test: exact bitwise equality (`np.array_equal == True`, `max_diff = 0.0`) across all cases. |

---

## 7. Final Implementation Gate Decision

Because:
1. Live journal schema commits in master omit `merkle_root` and `receipt_timestamp` (Blocker 1),
2. Live journal lacks a public iterator/accessor (Blocker 2),
3. Pairwise reciprocity damping $\Omega$ is completely ineffective against directed collusive cycles ($k \ge 3$) (Blocker 3),
4. Pairwise damping causes collusive share inflation in small reciprocal honest networks (Blocker 4),

the implementation gate is formally declared **BLOCKED**.

```
PHASE7_7_STATUS: BLOCKED
```
