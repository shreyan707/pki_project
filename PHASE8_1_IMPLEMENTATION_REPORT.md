# Phase 8.1 Implementation Report: Evidence-Weighted EigenTrust (EW-EigenTrust v1.8) with End-to-End Evidence Linkage

**Document:** `PHASE8_1_IMPLEMENTATION_REPORT.md`  
**Phase:** Phase 8.1 (Production Implementation of EW-EigenTrust v1.8 & End-to-End Linkage)  
**Author:** Candidate Shreyan Nayak (23BKT0039) & Autonomous Verification Agent  
**Date:** October 9, 2026  
**Status Assessment:** `PHASE8_1_STATUS: PASS`  
**Authoritative Design:** [`NOVEL_TRUST_ALGORITHM_DESIGN_V1_8.md`](file:///d:/pki_casestudy/NOVEL_TRUST_ALGORITHM_DESIGN_V1_8.md)  
**Gate Review Reference:** [`PHASE7_8_GATE_REVIEW.md`](file:///d:/pki_casestudy/PHASE7_8_GATE_REVIEW.md)  
**Test Suite Artifact:** [`tests/test_ew_eigentrust.py`](file:///d:/pki_casestudy/tests/test_ew_eigentrust.py) (SHA-256: `5a4cc95a626111e4e091e5daa8c265673b675c33a551a66346f672e179ecf069`)  
**Raw Test Execution Log:** [`tests_scratch/phase8_1_test_execution.log`](file:///d:/pki_casestudy/tests_scratch/phase8_1_test_execution.log) (SHA-256: `325ca86e68da820e2617e20b399219ceb4044304c00442178d0e0fb127d3ce41`)  

---

## 1. Executive Summary & Gate Decision

Phase 8.1 has successfully implemented the approved `MODE_EVIDENCE_ONLY` algorithm from `NOVEL_TRUST_ALGORITHM_DESIGN_V1_8.md` directly in the active PKI case-study repository. 

All requirements established in the Phase 8.1 mandate have been fulfilled:
1. **Identifier Contract Fully Resolved:** Traced the complete content delivery lifecycle, disambiguated all identifier types (`req_id`, `tx_id`, `entry_id`, simulator tokens), and established the 4-tuple delivery linkage contract `(client_did, server_did, merkle_root.lower(), tx_id)`.
2. **Production Algorithm Implemented:** Implemented `compute_ew_eigentrust_v1_8` (with `compute_ew_eigentrust` alias) in `src/layer3_eigentrust.py` with 14 strictly validated parameters, canonical peer indexing, bounded concave edge ceiling $\Phi_{\text{edge}}$, three evidence tiers, exponential timestamp freshness decay, bilateral dispute penalties, certified fault nullification, and robust power iteration.
3. **Public Journal Accessor & Commit Schema Extension:** Added public `get_all_entries()` method to `LocalEvidenceJournal`. Updated `record_receipt()` to commit authenticated `merkle_root` and `receipt_timestamp` to journal entry details.
4. **Simulator Delivery Linkage:** Updated `SwarmSimulation` in `src/network_simulator.py` to register verified delivery keys strictly upon successful `resp.verify()` and `record_receipt()` execution.
5. **Complete Test Execution:** Executed all 61 existing regression tests and 14 new focused tests (75 total tests). **Zero failures, zero errors, zero skips.**

```
PHASE8_1_STATUS: PASS
```

---

## 2. Task 1: Resolution of the Evidence Identifier Contract

### 2.1 Complete Content Delivery Lifecycle Tracing

A successful content delivery traverses six distinct lifecycle phases across Layer 3:

```
[1. ContentRequest]       Client signs req_id, client_did, server_did, content_id, chunk_index, merkle_root, nonce
        |
        v
[2. ChunkResponse]        Server signs req_id, chunk_bytes, chunk_hash, proof_hash, merkle_root, merkle_proof
        |                 Client executes resp.verify() -> validates signature, hashes, Merkle proof
        v
[3. Transaction ID]       Client generates unique tx_id for bilateral transaction settlement
        |
        v
[4. BilateralReceipt]     Client & Server dual-sign tx_id, client_did, server_did, merkle_root, rating, nonce
        |
        v
[5. Evidence Journal]     record_receipt() validates 7 stages -> commits receipt.tx_id as entry_id with details
        |
        v
[6. Delivery Linkage]     (client_did, server_did, merkle_root.lower(), tx_id) added to verified_delivery_keys
```

### 2.2 Relevant Existing Code Prior to Modification

Prior to Phase 8.1, the code paths had an identifier naming and schema gap:

1. **Request Creation (`src/network_simulator.py:305-318`):**
   ```python
   req_id = f"req-h-r{round_num}-{client.alias}-{provider.alias}-{chunk_idx}"
   now = time.time()
   nonce_req = f"nonce-req-{req_id}"
   req = ContentRequest(
       req_id=req_id,
       client_did=client.did,
       server_did=provider.did,
       content_id=content_id,
       chunk_index=chunk_idx,
       merkle_root=manifest.root_hash,
       timestamp=now,
       nonce=nonce_req,
       client_sig_hex=""
   )
   ```

2. **Chunk Response Verification (`src/network_simulator.py:344`):**
   ```python
   if resp.verify(provider.public_key_hex, req):
       self.metrics["content"]["honest_deliveries"] += 1
       self.metrics["content"]["valid_merkle_verifications"] += 1
   ```

3. **Receipt Construction (`src/network_simulator.py:349-365`):**
   ```python
   tx_id = f"tx-h-r{round_num}-{client.alias}-{provider.alias}-{chunk_idx}"
   receipt = BilateralReceipt(
       tx_id=tx_id,
       client_did=client.did,
       client_pubkey_hex=client.public_key_hex,
       server_did=provider.did,
       server_pubkey_hex=provider.public_key_hex,
       merkle_root=manifest.root_hash,
       rating="+1.00",
       timestamp=now,
       nonce=f"nonce-rcpt-{tx_id}",
       client_sig_hex="",
       server_sig_hex=""
   )
   ```

4. **Journal Commit Schema (`src/layer3_eigentrust.py:688-697`):**
   ```python
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
   *Deficiency identified in Phase 7.7/7.8:* `details` omitted `merkle_root` and `receipt_timestamp`, preventing journal-based evidence algorithms from determining content roots or transaction ages.

### 2.3 Unambiguous Identifier Contract

The protocol strictly differentiates five identifier scopes:

| Identifier Type | Protocol Name | Originating Protocol Message | Cryptographic Binding / Enveloping | Replay & Deduplication Scope | Interchangeability Rule |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Request ID** (`req_id`) | Content Request ID | Flow 5 (`ContentRequest`) | Signed by client in `PKI_V2_REQ` and by server in `PKI_V2_RESP` | Ephemeral chunk request deduplication | **NEVER interchangeable** with `tx_id`. Does not appear in `BilateralReceipt`. |
| **Transaction ID** (`tx_id`) | Protocol Transaction ID | Flow 10 (`PROPOSE_RECEIPT`) | Dual-signed by client and server in `PKI_V2_RECEIPT` | Processed evidence journal deduplication ($\mathcal{L}_{\text{local}}$) | Identifies the receipt itself. Canonical handle for the bilateral interaction. |
| **Receipt ID** | Receipt Identifier | Flow 10/11 | In frozen specification, identical to `tx_id` | Dual-signed payload field 1 | Syntactically equivalent to `tx_id`. |
| **Journal Entry ID** (`entry_id`) | Journal Entry Identifier | Flow 12 (`LocalEvidenceJournal`) | Keyed internally as `f"{entry_type}:{entry_id}"` | Guarantees at-most-once commit across namespace | Set strictly to `receipt.tx_id` on `RECEIPT` commit, or `evidence.evidence_id` on `FAULT_EVIDENCE` commit. |
| **Simulator ID** | Test Harness Token | `src/network_simulator.py` | String formatted prefix (e.g. `req-h-r...`, `tx-h-r...`) | Simulation observability and deterministic tracing | Test harness convenience; carries no wire semantics. |

### 2.4 Tier 3 Evidence Key Contract

The Tier 3 key contract is formally defined as:
$$\text{DeliveryKey} = (C.\text{DID}, \, S.\text{DID}, \, \text{lowercase}(R), \, \text{tx\_id})$$

1. **Field Authenticity:**
   - $C.\text{DID}$ and $S.\text{DID}$ are bound to public keys via `did:peer:2.Ez<pubkey_hex>`.
   - $R$ (`merkle_root`) is the authoritative root hash of the file manifest.
   - $\text{tx\_id}$ is the authenticated transaction identifier dual-signed by both peers.
2. **Backward-Compatible Journal Extension:**
   - In `src/layer3_eigentrust.py:709-722`, `details` now includes:
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
   - This adds fields to the journal entry without changing `BilateralReceipt`'s frozen wire format (`PKI_V2_RECEIPT:<tx_id>:<client_did>:<server_did>:<merkle_root>:<rating>:<timestamp>:<nonce>`).

### 2.5 Trust Boundary & In-Memory Simulator Boundaries

- **Local Subjectivity of Tier 3:** In a decentralized P2P network, a third party observing a bilateral receipt cannot cryptographically verify whether bytes were physically transmitted across the wire without observing the transmission or having the client provide the full chunk and proof. Therefore, **Tier 3 credit ($\gamma = 1.00$) is strictly a local subjective assessment** performed by the client node that downloaded and verified the chunk (or by the simulation oracle tracking verified transactions).
- **Remote Verifier Security:** Any remote peer evaluating receipts submitted by others grants Tier 2 ($\mu_{\text{referenced}} = 0.25$) if `merkle_root` matches an indexed publisher manifest, or Tier 1 ($\mu_{\text{unverified}} = 0.10$) if unindexed.
- **Protection Against Injected Tuples:** An adversary cannot mint Tier 3 status simply by inserting arbitrary tuples into `verified_delivery_keys`. The algorithm iterates through *committed journal entries*, requiring valid dual Ed25519 signatures, un-replayed nonces, fresh timestamps, and matching participant DIDs before any delivery key is looked up. An injected delivery key with no matching committed journal entry receives exactly zero credit.

---

## 3. Task 2: Production Implementation of EW-EigenTrust v1.8

### 3.1 Parameter Validation Specification

All 14 parameters are validated with strict rejection of boolean inputs:

| Parameter | Type | Default | Admissible Range | Enforcement Behavior |
| :--- | :---: | :---: | :---: | :--- |
| `mode` | `str` | `"evidence_only"` | `TrustComputationMode.VALID_MODES` | Raises `ValueError` if unrecognized |
| `alpha` | `float` | `0.15` | $0.0 < \alpha < 1.0$, reject `bool` | Raises `ValueError` |
| `tol` | `float` | `1e-6` | $\text{tol} > 0.0$ and finite, reject `bool` | Raises `ValueError` |
| `max_iter` | `int` | `100` | $\text{max\_iter} \ge 1$, reject `bool` | Raises `ValueError` |
| `k_max` | `float` | `10.0` | $k_{\max} > 0.0$ and finite, reject `bool` | Raises `ValueError` |
| `lambda_sat` | `float` | `0.50` | $\lambda_{\text{sat}} > 0.0$ and finite, reject `bool` | Raises `ValueError` |
| `mu_unverified` | `float` | `0.10` | $0.0 \le \mu \le 1.0$, reject `bool` | Raises `ValueError` |
| `mu_referenced` | `float` | `0.25` | $0.0 \le \mu \le 1.0$, $\mu_{\text{unverified}} \le \mu_{\text{referenced}}$ | Raises `ValueError` |
| `beta_entropy` | `float` | `2.0` | $\beta_{\text{entropy}} > 0.0$ and finite, reject `bool` | Raises `ValueError` |
| `theta_penalty` | `float` | `0.85` | $0.0 \le \theta \le 1.0$, reject `bool` | Raises `ValueError` |
| `epsilon_floor` | `float` | `0.10` | $0.0 < \epsilon \le 1.0$, reject `bool` | Raises `ValueError` |
| `delta_reg` | `float` | `2.0` | $\delta_{\text{reg}} > 0.0$ and finite, reject `bool` | Raises `ValueError` |
| `tau_seconds` | `float` | `86400.0` | $\tau > 0.0$ and finite, reject `bool` | Raises `ValueError` |
| `reference_time` | `float` / `None` | `None` | Finite float or `None`, reject `bool` | Raises `ValueError` |

### 3.2 Canonical Peer Set & Robustness

1. **Deduplication:** Input `peers` are deduplicated, stripped of non-strings and empty strings, and lexicographically sorted:
   $$\mathcal{V} = \text{sorted}(\text{unique}(\{p \in \mathcal{P}_{\text{in}} \mid p \text{ is a non-empty string}\}))$$
2. **Dimension:** All matrices and vectors are strictly $(n \times n)$ where $n = |\mathcal{V}|$.
3. **Empty Network:** If $n == 0$, returns `({}, True, 0)` immediately.
4. **Anchor Fallback:** If `supernodes` contains no valid peers in $\mathcal{V}$, pre-trusted restart vector falls back to uniform distribution $\mathbf{p} = [1/n, \dots, 1/n]^T$.

### 3.3 Bounded Concave Edge Ceiling ($\Phi_{\text{edge}}$)

Pairwise accumulated positive evidence $E_{\text{pos}}(i, j)$ is bounded by:
$$\Phi_{\text{edge}}(E_{\text{pos}}) = K_{\max} \cdot \tanh\left(\frac{\lambda_{\text{sat}} \cdot E_{\text{pos}}}{K_{\max}}\right)$$
- Strict real bound: $\Phi_{\text{edge}}(E) < K_{\max} = 10.0$ for all finite $E \ge 0$.
- Float64 bound: Saturated at $10.0$ when $\frac{\lambda_{\text{sat}} \cdot E}{K_{\max}} \ge 19.1$.

### 3.4 Multi-Tier Evidence Accumulation ($E_{\text{pos}}$)

$$E_{\text{pos}}(i, j) = \sum_{e \in \mathcal{E}_{ij}^{+}} \gamma_{\text{evidence}}(e) \cdot \gamma_{\text{time}}(t_{\text{ref}} - t_e)$$
$$\gamma_{\text{evidence}}(e) = \begin{cases}
1.00 & \text{if } (i, j, \text{merkle\_root}, \text{entry\_id}) \in \mathcal{D}_{\text{local}} \quad (\text{Tier 3: Verified Delivery}) \\
0.25 & \text{if } \text{merkle\_root} \in \mathcal{R}_{\text{manifests}} \quad (\text{Tier 2: Known Manifest Reference}) \\
0.10 & \text{otherwise} \quad (\text{Tier 1: Unindexed Bilateral Receipt})
\end{cases}$$

### 3.5 Timestamp Freshness & Dispute Penalties

$$\gamma_{\text{time}}(\Delta t) = \begin{cases}
1.0 & \text{if } -60.0 \le \Delta t \le 0.0 \quad (\text{Clock drift tolerance}) \\
0.0 & \text{if } \Delta t < -60.0 \quad (\text{Excessive future timestamp rejected}) \\
\exp\left(-\frac{\Delta t}{\tau}\right) & \text{if } \Delta t > 0.0 \quad (\tau = 86400.0\text{ s})
\end{cases}$$

$$\gamma_{\text{dispute}}(N_{\text{pos}}, N_{\text{neg}}) = \begin{cases}
0.0 & \text{if } N_{\text{pos}} = 0 \\
\max\left(0.0, \, 1.0 - \frac{2 \cdot N_{\text{neg}}}{N_{\text{pos}} + 1.0}\right) & \text{if } N_{\text{pos}} > 0
\end{cases}$$
- Neutral ratings (`rating == 0.0`) are skipped and do not increment $N_{\text{pos}}$ or $N_{\text{neg}}$.
- Negative ratings (`rating == -1.0`) increment $N_{\text{neg}}$ and penalize the edge, but do **not** trigger certified fault nullification.

### 3.6 Certified Fault Nullification ($\gamma_{\text{fault}}$)

$$\gamma_{\text{fault}}(i, j) = \begin{cases}
0.0 & \text{if } j \in \text{accused\_dids}(\mathcal{F}) \lor \text{peer\_states}[j] \in \{\text{REVOCATION\_PROPOSED}, \text{REVOKED}\} \\
    & \quad \lor (\text{peer\_states}[j] == \text{SUSPECTED} \land j \in \text{certified\_suspected}) \\
1.0 & \text{otherwise}
\end{cases}$$
When nullified, all incoming edges $A_{ij} = 0.0$ for all $i$.

### 3.7 Public Evidence-Journal Accessor

Added to `LocalEvidenceJournal` in `src/layer3_eigentrust.py:556-559`:
```python
def get_all_entries(self) -> List[JournalEntry]:
    """Public accessor returning all committed journal entries."""
    return list(self._entries.values())
```

---

## 4. Task 3: Focused Test Suite Verification

Fourteen focused tests were implemented in [`tests/test_ew_eigentrust.py`](file:///d:/pki_casestudy/tests/test_ew_eigentrust.py):

| Test Identifier | Test Target & Purpose | Verification Outcome |
| :--- | :--- | :---: |
| `test_01_valid_verified_delivery_tier3_actual_lifecycle` | Valid delivery through actual 5-step lifecycle receives Tier 3 credit ($\gamma = 1.00$) | **PASSED** |
| `test_02_tx_id_vs_journal_entry_id_mismatch_prevents_tier3` | Mismatched `tx_id` and `req_id` fails Tier 3 lookup and safely falls back to Tier 2 | **PASSED** |
| `test_03_missing_or_malformed_receipt_linkage_falls_back` | Empty `merkle_root` and malformed non-tuple keys safely fall back to Tier 1 | **PASSED** |
| `test_04_forged_or_manually_injected_delivery_key_cannot_bypass_boundary` | Forged delivery keys injected into set with no valid journal entries grant zero credit | **PASSED** |
| `test_05_manifest_root_references_receive_tier2_only_when_indexed` | Receipts referencing known manifest roots receive Tier 2 ($\mu = 0.25$) over unindexed Tier 1 | **PASSED** |
| `test_06_unindexed_receipts_receive_tier1` | Unindexed bilateral receipts receive Tier 1 ($\mu = 0.10$) | **PASSED** |
| `test_07_fresh_stale_and_excessive_future_dated_evidence` | Freshness decay ($\exp(-1)$), clock drift (within 60s), and future rejection ($> 60\text{s}$) | **PASSED** |
| `test_08_neutral_ratings_do_not_count_as_positive_or_negative` | Receipts with rating 0.0 are ignored from positive evidence and dispute counts | **PASSED** |
| `test_09_subjective_negative_receipts_dispute_vs_certified_fault` | Subjective disputes penalize edges via $\gamma_{\text{dispute}}$ without certified fault eviction | **PASSED** |
| `test_10_certified_fault_and_revocation_nullification` | Certified faults, revocation states, and certified suspicions nullify incoming edges to 0.0 | **PASSED** |
| `test_11_input_robustness_empty_duplicates_nan_dangling` | Empty networks, duplicate peers, missing supernodes, NaN/Inf scores, and invalid params | **PASSED** |
| `test_12_concave_edge_function_bounds` | Concave edge function strictly satisfies real bound $< 10.0$ and float64 bound $\le 10.0$ | **PASSED** |
| `test_13_vanilla_mode_exact_equivalence_on_d_equiv` | `MODE_VANILLA` matches `EigenTrustEngine` with exact bitwise equality (`diff == 0.0`) on $\mathcal{D}_{\text{equiv}}$ | **PASSED** |
| `test_14_end_to_end_simulation_linkage_trace` | Full `SwarmSimulation` runs with `trust_mode=EVIDENCE_ONLY`, populating delivery keys | **PASSED** |

---

## 5. Task 4: Test Results, Changed Files, and Raw Output

### 5.1 Test Execution Summary

- **Total Test Suites Executed:** 2 (`tests/test_trust_framework.py`, `tests/test_ew_eigentrust.py`)
- **Total Tests Run:** 75
- **Passed:** 75
- **Failed:** 0
- **Errors:** 0
- **Skipped:** 0
- **Total Execution Time:** 4.572 seconds
- **Raw Test Log File:** [`tests_scratch/phase8_1_test_execution.log`](file:///d:/pki_casestudy/tests_scratch/phase8_1_test_execution.log)

### 5.2 Artifact Hashes

- `tests/test_ew_eigentrust.py`: `5a4cc95a626111e4e091e5daa8c265673b675c33a551a66346f672e179ecf069`
- `tests_scratch/phase8_1_test_execution.log`: `325ca86e68da820e2617e20b399219ceb4044304c00442178d0e0fb127d3ce41`

### 5.3 Changed Files and Purpose of Each Change

1. **[`src/layer3_eigentrust.py`](file:///d:/pki_casestudy/src/layer3_eigentrust.py):**
   - Added `TrustComputationMode` enum-like class defining `VANILLA`, `EVIDENCE_ONLY`, `TOPOLOGY_ONLY`, `FULL_EW`, `LOCAL_ONLY`.
   - Added public accessor `get_all_entries()` on `LocalEvidenceJournal`.
   - Stored `self.pre_trusted_peers` on `EigenTrustEngine`.
   - Updated `record_receipt()` to include authenticated `merkle_root` and `receipt_timestamp` in journal `details`.
   - Implemented `compute_ew_eigentrust_v1_8` (with `compute_ew_eigentrust` alias).
   - Added `compute_ew_trust_scores()` and backward-compatible `get_trust_scores(mode=...)` to `EigenTrustEngine`.
2. **[`src/network_simulator.py`](file:///d:/pki_casestudy/src/network_simulator.py):**
   - Added `trust_mode`, `verified_delivery_keys`, and `known_manifest_roots` attributes to `SwarmSimulation`.
   - Indexed manifest root hashes when initial files are generated.
   - Populated `verified_delivery_keys` with `(client.did, provider.did, manifest.root_hash.lower(), tx_id)` upon successful `resp.verify()` and `record_receipt()`.
   - Populated `verified_delivery_keys` for supernode audit downloads upon successful `a_resp.verify()` and `record_receipt()`.
   - Passed delivery keys, manifest roots, and certified suspicion DIDs into `get_trust_scores` in `run_simulation()`.
3. **[`tests/test_ew_eigentrust.py`](file:///d:/pki_casestudy/tests/test_ew_eigentrust.py):**
   - New dedicated test suite verifying all 14 Phase 8.1 acceptance criteria.

---

## 6. End-to-End Trace: Verified Delivery Credit

Here is the exact end-to-end trace proving that a verified delivery receives Tier 3 credit:

```python
# 1. Authentic file and Merkle tree established
content_bytes = b"AUTHENTIC_CONTENT_CHUNK_DATA_PAYLOAD"
tree = MerkleTree([content_bytes])
merkle_root = tree.root_hash

# 2. Client creates signed ContentRequest (Flow 5)
req_id = "req-test-r1-ClientNode-ServerNode-0"
req = ContentRequest(req_id=req_id, client_did=client.did, server_did=server.did,
                     content_id="c1", chunk_index=0, merkle_root=merkle_root,
                     timestamp=now, nonce=f"nonce-req-{req_id}", client_sig_hex="")
req.client_sig_hex = client.sign(req.payload_bytes()).hex()

# 3. Server generates signed ChunkResponse with inclusion proof (Flow 6)
proof = tree.generate_proof(0)
resp = ChunkResponse(req_id=req_id, client_did=client.did, server_did=server.did,
                     content_id="c1", chunk_index=0, chunk_bytes=content_bytes,
                     chunk_hash=hashlib.sha256(content_bytes).hexdigest().lower(),
                     proof_hash=hash_proof(proof), merkle_root=merkle_root,
                     timestamp=now, nonce=req.nonce, merkle_proof=proof, server_sig_hex="")
resp.server_sig_hex = server.sign(resp.payload_bytes()).hex()

# 4. Client verifies response (Flow 9)
assert resp.verify(server.public_key_hex, req) == True

# 5. Client & Server co-sign BilateralReceipt (Flow 10 & 11)
tx_id = "tx-test-r1-ClientNode-ServerNode-0"
receipt = BilateralReceipt(tx_id=tx_id, client_did=client.did, client_pubkey_hex=client.public_key_hex,
                           server_did=server.did, server_pubkey_hex=server.public_key_hex,
                           merkle_root=merkle_root, rating="+1.00", timestamp=now,
                           nonce=f"nonce-rcpt-{tx_id}", client_sig_hex="", server_sig_hex="")
receipt.client_sig_hex = client.sign(receipt.payload_bytes()).hex()
receipt.server_sig_hex = server.sign(receipt.payload_bytes()).hex()
assert receipt.is_valid() == True

# 6. Ordered Evidence Validation & Journal Commit (Flow 12)
assert engine.record_receipt(receipt, current_time=now) == True
# Journal entry committed with:
# entry_id = "tx-test-r1-ClientNode-ServerNode-0"
# details = {"client_did": client.did, "server_did": server.did, "rating": 1.0,
#            "nonce": ..., "merkle_root": merkle_root, "receipt_timestamp": now}

# 7. Local delivery tracking
delivery_key = (client.did, server.did, merkle_root.lower(), tx_id)
verified_delivery_keys.add(delivery_key)

# 8. EW-EigenTrust v1.8 Execution (compute_ew_eigentrust_v1_8)
# Inspection loop:
# (src, dst, m_root, tx_id) == delivery_key in verified_delivery_keys -> True!
# gamma_ev = 1.00 (Tier 3: Verified Delivery Credit)
# e_pos = 1.00 * gamma_time(0.0) = 1.00
# S'[client, server] = 10.0 * tanh(0.50 * 1.00 / 10.0) = 0.49958 * gamma_dispute(1.0) = 0.49958
```

---

## 7. Protocol Limitations and Implementation Boundaries

In accordance with scientific and adversarial integrity:

1. **Local Subjectivity of Tier 3 Credit:** Tier 3 credit ($\gamma = 1.00$) requires either a local node observing genuine byte delivery or a trusted simulation oracle. Third-party observers evaluating foreign receipts across the P2P network cannot distinguish an authentic receipt from a collusive receipt without access to delivery proof streams, and therefore must bound third-party receipts to Tier 2 ($\mu_{\text{referenced}} = 0.25$) or Tier 1 ($\mu_{\text{unverified}} = 0.10$).
2. **The Closed-Set Invariance Limit:** As mathematically proven by the Closed-Set Identity Theorem in Phase 7.8:
   $$\sum_{c \in C} t_c = \left(\frac{1 - \alpha}{\alpha}\right) \sum_{h \in H} t_h \sum_{c \in C} C'_{hc}$$
   No local reputation algorithm operating on row-normalized Markov transition matrices can reduce a closed colluder set's stationary trust share below the level dictated by honest nodes' external outgoing transition flow ($\sum_{c \in C} C'_{hc}$). Bounding edge strength ($\Phi_{\text{edge}}$) and discounting unverified receipts ($\mu = 0.10$) successfully caps collusive grinding, but preventing bridging requires honest peers to refrain from interacting with unverified colluders.
3. **Hypothesis Status of Collusion Reduction:** Although concave edge bounding and multi-tier evidence discounting are implemented and mathematically verified, claiming empirical collusion resistance across arbitrary large-scale attacker topologies remains an empirical hypothesis that must be rigorously tested against the baseline in Phase 8.2 benchmarks.

---

## 8. Final Gate Decision

Every requirement of Phase 8.1 is satisfied:
- The evidence identifier contract is resolved and documented.
- `MODE_EVIDENCE_ONLY` of EW-EigenTrust v1.8 is implemented in production source.
- Public evidence journal accessor and schema extension are in place.
- All 14 focused tests execute and pass.
- All 61 existing regression tests continue to pass without deviation.
- Raw logs and cryptographic hashes are preserved on disk.

```
PHASE8_1_STATUS: PASS
```
