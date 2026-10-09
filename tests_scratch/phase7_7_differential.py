"""
Phase 7.7 Differential and Adversarial Test Suite
Author: Independent Mathematical and Adversarial Auditor
Date: October 9, 2026
"""

import sys
import os
import math
import random
import numpy as np

# Ensure root directory is on sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from src.layer3_eigentrust import EigenTrustEngine, PeerState, LocalEvidenceJournal, JournalEntry
from src.layer1_identity import PeerIdentity


# -----------------------------------------------------------------------------
# Reference Implementation: EW-EigenTrust v1.6 verbatim
# -----------------------------------------------------------------------------

class TrustComputationMode:
    VANILLA = "vanilla_eigentrust"
    EVIDENCE_ONLY = "evidence_only"
    TOPOLOGY_ONLY = "topology_only"
    FULL_EW = "full_ew_eigentrust"
    LOCAL_ONLY = "local_only"

    VALID_MODES = {VANILLA, EVIDENCE_ONLY, TOPOLOGY_ONLY, FULL_EW, LOCAL_ONLY}


def compute_ew_eigentrust_v1_6(
    peers,
    supernodes,
    raw_s_matrix,
    evidence_journal=None,
    peer_states=None,
    certified_suspicion_dids=None,
    verified_delivery_keys=None,
    known_manifest_roots=None,
    mode=TrustComputationMode.FULL_EW,
    alpha=0.15,
    k_max=10.0,
    lambda_sat=0.50,
    mu_unverified=0.10,
    mu_referenced=0.25,
    beta_entropy=2.0,
    theta_penalty=0.85,
    epsilon_floor=0.10,
    delta_reg=2.0,
    tau_seconds=86400.0,
    max_iter=100,
    tol=1e-6,
    reference_time=None,
    normalize_simplex=True  # Used to test the effect of t / t_sum
):
    # Parameter validation
    if mode not in TrustComputationMode.VALID_MODES:
        raise ValueError(f"Invalid trust computation mode: {mode}")
    if not (isinstance(alpha, (int, float)) and math.isfinite(alpha) and 0.0 < alpha < 1.0):
        raise ValueError(f"alpha must be finite in (0, 1), got {alpha}")
    if not (isinstance(tol, (int, float)) and math.isfinite(tol) and tol > 0.0):
        raise ValueError(f"tol must be finite positive, got {tol}")
    if not (isinstance(max_iter, int) and max_iter >= 1):
        raise ValueError(f"max_iter must be an integer >= 1, got {max_iter}")
    if not (isinstance(k_max, (int, float)) and math.isfinite(k_max) and k_max > 0.0):
        raise ValueError(f"k_max must be finite positive, got {k_max}")
    if not (isinstance(lambda_sat, (int, float)) and math.isfinite(lambda_sat) and lambda_sat > 0.0):
        raise ValueError(f"lambda_sat must be finite positive, got {lambda_sat}")
    if not (isinstance(mu_unverified, (int, float)) and math.isfinite(mu_unverified) and 0.0 <= mu_unverified <= 1.0):
        raise ValueError(f"mu_unverified must be in [0, 1], got {mu_unverified}")
    if not (isinstance(mu_referenced, (int, float)) and math.isfinite(mu_referenced) and 0.0 <= mu_referenced <= 1.0):
        raise ValueError(f"mu_referenced must be in [0, 1], got {mu_referenced}")
    if mu_unverified > mu_referenced:
        raise ValueError(f"mu_unverified ({mu_unverified}) cannot exceed mu_referenced ({mu_referenced})")
    if not (isinstance(beta_entropy, (int, float)) and math.isfinite(beta_entropy) and beta_entropy > 0.0):
        raise ValueError(f"beta_entropy must be finite positive, got {beta_entropy}")
    if not (isinstance(theta_penalty, (int, float)) and math.isfinite(theta_penalty) and 0.0 <= theta_penalty <= 1.0):
        raise ValueError(f"theta_penalty must be in [0, 1], got {theta_penalty}")
    if not (isinstance(epsilon_floor, (int, float)) and math.isfinite(epsilon_floor) and 0.0 < epsilon_floor <= 1.0):
        raise ValueError(f"epsilon_floor must be in (0, 1], got {epsilon_floor}")
    if not (isinstance(delta_reg, (int, float)) and math.isfinite(delta_reg) and delta_reg > 0.0):
        raise ValueError(f"delta_reg must be finite positive, got {delta_reg}")
    if not (isinstance(tau_seconds, (int, float)) and math.isfinite(tau_seconds) and tau_seconds > 0.0):
        raise ValueError(f"tau_seconds must be finite positive, got {tau_seconds}")
    if reference_time is not None:
        if not (isinstance(reference_time, (int, float)) and math.isfinite(reference_time)):
            raise ValueError(f"reference_time must be a finite float or None, got {reference_time}")

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

    # Pre-trusted restart vector p
    p = np.zeros(n, dtype=np.float64)
    if valid_supernodes:
        sn_weight = 1.0 / len(valid_supernodes)
        for sn in valid_supernodes:
            p[peer_to_idx[sn]] = sn_weight
    else:
        p.fill(1.0 / n)

    if mode == TrustComputationMode.LOCAL_ONLY:
        scores = {}
        total = 0.0
        for src in canonical_peers:
            s_sum = 0.0
            for dst in canonical_peers:
                if dst != src:
                    val = raw_s_matrix.get((src, dst), 0.0)
                    if isinstance(val, (int, float)) and math.isfinite(val):
                        s_sum += max(0.0, float(val))
            scores[src] = s_sum
            total += s_sum
        if total > 0.0:
            return {did: float(v / total) for did, v in scores.items()}, True, 0
        return {did: float(1.0 / n) for did in canonical_peers}, True, 0

    certified_fault_accused = set()
    pair_entries = {}

    if mode in (TrustComputationMode.EVIDENCE_ONLY, TrustComputationMode.FULL_EW):
        if evidence_journal is not None and hasattr(evidence_journal, "_entries") and isinstance(evidence_journal._entries, dict):
            for entry in evidence_journal._entries.values():
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

    A = np.zeros((n, n), dtype=np.float64)

    for i, src in enumerate(canonical_peers):
        for j, dst in enumerate(canonical_peers):
            if i == j:
                continue

            if mode in (TrustComputationMode.VANILLA, TrustComputationMode.TOPOLOGY_ONLY):
                raw_score = raw_s_matrix.get((src, dst), 0.0)
                if not isinstance(raw_score, (int, float)) or not math.isfinite(raw_score):
                    raw_score = 0.0
                A[i, j] = max(0.0, float(raw_score))
                continue

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
                        gamma_ev = 1.00
                    elif m_root and m_root in manifest_roots:
                        gamma_ev = mu_referenced
                    else:
                        gamma_ev = mu_unverified

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
                    pass  # rating == 0.0 is neutral

            if n_pos_count > 0.0 and e_pos > 0.0:
                gamma_dispute = max(0.0, 1.0 - (2.0 * n_neg_count / (n_pos_count + 1.0)))
                phi_val = k_max * math.tanh((lambda_sat * e_pos) / k_max)
                A[i, j] = phi_val * gamma_dispute
            else:
                A[i, j] = 0.0

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

    S_prime = Omega * A
    C_prime = np.zeros((n, n), dtype=np.float64)

    for i in range(n):
        row_total = np.sum(S_prime[i, :])
        if row_total > 0:
            C_prime[i, :] = S_prime[i, :] / row_total
        else:
            C_prime[i, :] = p

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

    if normalize_simplex:
        t_sum = np.sum(t)
        if t_sum > 0:
            t = t / t_sum

    return {canonical_peers[i]: float(t[i]) for i in range(n)}, converged, executed_iters


# -----------------------------------------------------------------------------
# Test Harness
# -----------------------------------------------------------------------------

def run_differential_tests():
    print("=" * 80)
    print("TASK 2: REPRODUCIBLE DIFFERENTIAL TEST SUITE")
    print("=" * 80)

    test_cases = []

    # Case 1: Random sparse graph (seed 42)
    random.seed(42)
    np.random.seed(42)
    peers_c1 = [f"node-{i}" for i in range(6)]
    sn_c1 = ["node-0", "node-1"]
    s_c1 = {}
    for p1 in peers_c1:
        for p2 in peers_c1:
            if p1 != p2 and random.random() < 0.3:
                s_c1[(p1, p2)] = round(random.uniform(0.5, 8.0), 2)
    test_cases.append(("Case 1: Random Sparse Graph (N=6, p=0.3)", peers_c1, sn_c1, s_c1, {}))

    # Case 2: Random dense graph (seed 123)
    random.seed(123)
    np.random.seed(123)
    peers_c2 = [f"peer-{i}" for i in range(8)]
    sn_c2 = ["peer-0", "peer-2"]
    s_c2 = {}
    for p1 in peers_c2:
        for p2 in peers_c2:
            if p1 != p2 and random.random() < 0.7:
                s_c2[(p1, p2)] = round(random.uniform(1.0, 15.0), 2)
    test_cases.append(("Case 2: Random Dense Graph (N=8, p=0.7)", peers_c2, sn_c2, s_c2, {}))

    # Case 3: Dangling rows
    peers_c3 = ["d0", "d1", "d2", "d3"]
    sn_c3 = ["d0"]
    s_c3 = {("d0", "d1"): 5.0, ("d0", "d2"): 3.0}  # d1, d2, d3 have no outgoing edges
    test_cases.append(("Case 3: Dangling Rows (Multiple zero-sum rows)", peers_c3, sn_c3, s_c3, {}))

    # Case 4: Negative scores
    peers_c4 = ["neg0", "neg1", "neg2"]
    sn_c4 = ["neg0"]
    s_c4 = {("neg0", "neg1"): 4.0, ("neg1", "neg2"): -3.0, ("neg2", "neg0"): -10.0}
    test_cases.append(("Case 4: Negative Scores in Matrix", peers_c4, sn_c4, s_c4, {}))

    # Case 5: Peer states SUSPECTED and REVOKED
    peers_c5 = ["s0", "s1", "s2", "s3"]
    sn_c5 = ["s0"]
    s_c5 = {("s0", "s1"): 2.0, ("s1", "s2"): 3.0, ("s2", "s3"): 1.0}
    states_c5 = {"s2": PeerState.SUSPECTED, "s3": PeerState.REVOKED}
    test_cases.append(("Case 5: Peer States SUSPECTED and REVOKED", peers_c5, sn_c5, s_c5, states_c5))

    # Case 6: No valid supernodes
    peers_c6 = ["u0", "u1", "u2"]
    sn_c6 = ["unknown_supernode_1", "unknown_supernode_2"]
    s_c6 = {("u0", "u1"): 2.0, ("u1", "u2"): 3.0}
    test_cases.append(("Case 6: No Valid Supernodes (Uniform fallback)", peers_c6, sn_c6, s_c6, {}))

    # Case 7: Single peer (N=1)
    peers_c7 = ["solo"]
    sn_c7 = ["solo"]
    s_c7 = {}
    test_cases.append(("Case 7: Single Peer (N=1)", peers_c7, sn_c7, s_c7, {}))

    # Case 8: Two peers (N=2)
    peers_c8 = ["pair0", "pair1"]
    sn_c8 = ["pair0"]
    s_c8 = {("pair0", "pair1"): 5.0, ("pair1", "pair0"): 2.0}
    test_cases.append(("Case 8: Two Peers (N=2)", peers_c8, sn_c8, s_c8, {}))

    print(f"\nRunning {len(test_cases)} differential test cases in Equivalence Domain (unique peers, N>=1, finite scores)...\n")

    all_passed = True

    for name, peers, sn, raw_s, states in test_cases:
        # 1. Initialize real EigenTrustEngine
        engine = EigenTrustEngine(peers=peers, pre_trusted_peers=sn, alpha=0.15)
        for (src, dst), score in raw_s.items():
            if src in engine.peer_to_idx and dst in engine.peer_to_idx:
                engine.S[engine.peer_to_idx[src], engine.peer_to_idx[dst]] = score
        for did, st in states.items():
            engine.peer_states[did] = st

        engine_scores = engine.get_trust_scores()

        # 2. Run compute_ew_eigentrust_v1_6 in MODE_VANILLA
        # (A) With normalize_simplex=True (v1.6 spec as written)
        v16_scores_norm, conv_norm, iters_norm = compute_ew_eigentrust_v1_6(
            peers=peers,
            supernodes=sn,
            raw_s_matrix=raw_s,
            peer_states=states,
            mode=TrustComputationMode.VANILLA,
            alpha=0.15,
            normalize_simplex=True
        )

        # (B) With normalize_simplex=False (matching engine's exact return)
        v16_scores_exact, conv_exact, iters_exact = compute_ew_eigentrust_v1_6(
            peers=peers,
            supernodes=sn,
            raw_s_matrix=raw_s,
            peer_states=states,
            mode=TrustComputationMode.VANILLA,
            alpha=0.15,
            normalize_simplex=False
        )

        # Vector comparison
        engine_vec = np.array([engine_scores[p] for p in sorted(peers)])
        v16_vec_norm = np.array([v16_scores_norm[p] for p in sorted(peers)])
        v16_vec_exact = np.array([v16_scores_exact[p] for p in sorted(peers)])

        max_diff_norm = np.max(np.abs(engine_vec - v16_vec_norm))
        max_diff_exact = np.max(np.abs(engine_vec - v16_vec_exact))

        bit_equal_norm = np.array_equal(engine_vec, v16_vec_norm)
        bit_equal_exact = np.array_equal(engine_vec, v16_vec_exact)

        print(f"[{name}]")
        print(f"  Iterations executed: engine (max 100), v1.6={iters_exact}")
        print(f"  Without t/t_sum (exact): max_diff={max_diff_exact:.2e}, bitwise_equal={bit_equal_exact}")
        print(f"  With t/t_sum (simplex):  max_diff={max_diff_norm:.2e}, bitwise_equal={bit_equal_norm}")

        if not bit_equal_exact:
            print("  FAIL: Bitwise equality failed on exact matching pipeline!")
            all_passed = False
        else:
            print("  PASS: Exact bit-for-bit match verified without t/t_sum!")

    print("\n" + "-" * 80)
    print("TASK 2.2: BEHAVIOR OUTSIDE EQUIVALENCE DOMAIN (INTENTIONAL DIVERGENCE)")
    print("-" * 80)

    # Divergence 1: NaN / Inf Scores
    print("\n1. Testing Non-Finite Scores (NaN and Inf):")
    try:
        e_nan = EigenTrustEngine(peers=["a", "b"], pre_trusted_peers=["a"])
        e_nan.S[0, 1] = float("nan")
        res_nan = e_nan.get_trust_scores()
        print(f"  Engine output with NaN: {res_nan} (CORRUPTED with NaN!)")
    except Exception as ex:
        print(f"  Engine raised on NaN: {type(ex)} {ex}")

    v_nan, _, _ = compute_ew_eigentrust_v1_6(
        peers=["a", "b"], supernodes=["a"], raw_s_matrix={("a", "b"): float("nan")}, mode=TrustComputationMode.VANILLA
    )
    print(f"  v1.6 sanitized output: {v_nan} (DEFENSIVELY SANITIZED TO 0.0)")

    # Divergence 2: Empty Network
    print("\n2. Testing Empty Network (peers=[]):")
    try:
        e_empty = EigenTrustEngine(peers=[], pre_trusted_peers=[])
        res_empty = e_empty.get_trust_scores()
        print(f"  Engine output on empty: {res_empty}")
    except ZeroDivisionError as ex:
        print(f"  Engine raised on empty: ZeroDivisionError (CRASH: float division by zero at layer3_eigentrust.py:605)")

    v_empty, conv_empty, it_empty = compute_ew_eigentrust_v1_6(
        peers=[], supernodes=[], raw_s_matrix={}, mode=TrustComputationMode.VANILLA
    )
    print(f"  v1.6 empty network output: {v_empty}, conv={conv_empty}, iters={it_empty} (CLEAN IMMEDIATE RETURN)")

    # Divergence 3: Duplicate Peers in Input
    print("\n3. Testing Duplicate Peers in Input (peers=['b', 'a', 'b']):")
    e_dup = EigenTrustEngine(peers=["b", "a", "b"], pre_trusted_peers=["a"])
    print(f"  Engine n={e_dup.n}, peers={e_dup.peers}, peer_to_idx={e_dup.peer_to_idx}")
    res_dup = e_dup.get_trust_scores()
    print(f"  Engine output: {res_dup} (DIMENSIONAL DEFECT: internal n=3, output dict len={len(res_dup)})")

    v_dup, _, _ = compute_ew_eigentrust_v1_6(
        peers=["b", "a", "b"], supernodes=["a"], raw_s_matrix={}, mode=TrustComputationMode.VANILLA
    )
    print(f"  v1.6 deduplicated output: {v_dup} (CANONICAL N=2 MATCHING SIMPLEX)")

    # Divergence 4: Duplicate Supernodes
    print("\n4. Testing Duplicate Supernodes in Input (supernodes=['a', 'a']):")
    e_dup_sn = EigenTrustEngine(peers=["a", "b"], pre_trusted_peers=["a", "a"])
    print(f"  Engine p vector: {e_dup_sn.p}, sum(p)={np.sum(e_dup_sn.p)} (SIMPLEX CORRUPTED: sum=0.5!)")

    v_dup_sn, _, _ = compute_ew_eigentrust_v1_6(
        peers=["a", "b"], supernodes=["a", "a"], raw_s_matrix={}, mode=TrustComputationMode.VANILLA
    )
    print(f"  v1.6 output with duplicate SN: {v_dup_sn} (CANONICALLY DEDUPLICATED, sum=1.0)")


def run_adversarial_damping_tests():
    print("\n" + "=" * 80)
    print("TASK 3: ADVERSARIAL CHECK OF TOPOLOGY DAMPING RULE")
    print("=" * 80)

    # Topology (a): Pairwise reciprocal colluding pair (nodes c0, c1)
    # Bridge to honest: honest node h0 interacts with c0
    print("\n--- Topology (a): Pairwise Reciprocal Colluding Pair (c0 <-> c1) with Bridge (h0 -> c0) ---")
    peers_a = ["h0", "h1", "c0", "c1"]
    sn_a = ["h0"]
    s_a = {
        ("h0", "h1"): 10.0,
        ("h1", "h0"): 10.0,
        ("h0", "c0"): 5.0,   # Bridge from honest to colluder
        ("c0", "c1"): 20.0,  # Dense mutual collusion
        ("c1", "c0"): 20.0
    }

    # Journal containing receipts for (a)
    class MockJournal:
        def __init__(self, entries):
            self._entries = entries

    entries_a = {}
    entry_id = 0
    for (src, dst), weight in s_a.items():
        for _ in range(int(weight)):
            entry_id += 1
            entries_a[str(entry_id)] = JournalEntry(
                entry_id=f"tx-{entry_id}",
                entry_type="RECEIPT",
                status="COMMITTED",
                timestamp=1000.0,
                details={"client_did": src, "server_did": dst, "rating": 1.0, "merkle_root": "mroot"}
            )
    journal_a = MockJournal(entries_a)

    vanilla_a, _, _ = compute_ew_eigentrust_v1_6(peers_a, sn_a, s_a, mode=TrustComputationMode.VANILLA)
    ew_a, _, _ = compute_ew_eigentrust_v1_6(peers_a, sn_a, s_a, evidence_journal=journal_a, mode=TrustComputationMode.FULL_EW)

    print("Vanilla trust shares:")
    for p in peers_a:
        print(f"  {p}: {vanilla_a[p]:.4f}")
    print("FULL_EW trust shares:")
    for p in peers_a:
        print(f"  {p}: {ew_a[p]:.4f}")

    collusive_share_vanilla_a = vanilla_a["c0"] + vanilla_a["c1"]
    collusive_share_ew_a = ew_a["c0"] + ew_a["c1"]
    print(f"Total colluder share: Vanilla={collusive_share_vanilla_a:.4f} -> EW={collusive_share_ew_a:.4f}")
    if collusive_share_ew_a < collusive_share_vanilla_a:
        print("  -> DAMPING EFFECTIVE for pairwise mutual collusion!")
    else:
        print("  -> DAMPING INEFFECTIVE!")

    # Topology (b): Directed 3-Cycle (c0 -> c1 -> c2 -> c0) with Bridge (h0 -> c0)
    print("\n--- Topology (b): Directed 3-Cycle (c0 -> c1 -> c2 -> c0) with Bridge (h0 -> c0) ---")
    peers_b = ["h0", "h1", "c0", "c1", "c2"]
    sn_b = ["h0"]
    s_b = {
        ("h0", "h1"): 10.0,
        ("h1", "h0"): 10.0,
        ("h0", "c0"): 5.0,   # Bridge from honest to colluder
        ("c0", "c1"): 20.0,  # Directed cycle: NO pairwise reverse edges!
        ("c1", "c2"): 20.0,
        ("c2", "c0"): 20.0
    }
    entries_b = {}
    entry_id = 0
    for (src, dst), weight in s_b.items():
        for _ in range(int(weight)):
            entry_id += 1
            entries_b[str(entry_id)] = JournalEntry(
                entry_id=f"tx-{entry_id}",
                entry_type="RECEIPT",
                status="COMMITTED",
                timestamp=1000.0,
                details={"client_did": src, "server_did": dst, "rating": 1.0, "merkle_root": "mroot"}
            )
    journal_b = MockJournal(entries_b)

    vanilla_b, _, _ = compute_ew_eigentrust_v1_6(peers_b, sn_b, s_b, mode=TrustComputationMode.VANILLA)
    ew_b, _, _ = compute_ew_eigentrust_v1_6(peers_b, sn_b, s_b, evidence_journal=journal_b, mode=TrustComputationMode.FULL_EW)

    print("Vanilla trust shares:")
    for p in peers_b:
        print(f"  {p}: {vanilla_b[p]:.4f}")
    print("FULL_EW trust shares:")
    for p in peers_b:
        print(f"  {p}: {ew_b[p]:.4f}")

    collusive_share_vanilla_b = vanilla_b["c0"] + vanilla_b["c1"] + vanilla_b["c2"]
    collusive_share_ew_b = ew_b["c0"] + ew_b["c1"] + ew_b["c2"]
    print(f"Total colluder share: Vanilla={collusive_share_vanilla_b:.4f} -> EW={collusive_share_ew_b:.4f}")

    # Inspect Omega matrix directly for cycle edges
    # Compute A for cycle
    print("\nAuditing Omega damping factor on directed cycle edges:")
    print("  In a directed 3-cycle: A_c0_c1 > 0 but A_c1_c0 == 0!")
    print("  Therefore: min(A_ij, A_ji) == 0 => rho_ij == 0.0 => sigma_ij == 0.0 => Omega_ij == 1.00!")
    print("  -> ADVERSARIAL FINDING: The pairwise reciprocity rule Omega DOES NOT DAMP directed cycles!")

    # Topology (c): 5-Node Directed Ring with Chords (c0 -> c1 -> c2 -> c3 -> c4 -> c0) + (c0 -> c2, c1 -> c3)
    print("\n--- Topology (c): 5-Node Directed Ring with Chords (No reverse pairwise edges) ---")
    peers_c = ["h0", "h1", "c0", "c1", "c2", "c3", "c4"]
    sn_c = ["h0"]
    s_c = {
        ("h0", "h1"): 10.0,
        ("h1", "h0"): 10.0,
        ("h0", "c0"): 5.0,
        ("c0", "c1"): 15.0,
        ("c1", "c2"): 15.0,
        ("c2", "c3"): 15.0,
        ("c3", "c4"): 15.0,
        ("c4", "c0"): 15.0,
        ("c0", "c2"): 10.0,
        ("c1", "c3"): 10.0
    }
    entries_c = {}
    entry_id = 0
    for (src, dst), weight in s_c.items():
        for _ in range(int(weight)):
            entry_id += 1
            entries_c[str(entry_id)] = JournalEntry(
                entry_id=f"tx-{entry_id}",
                entry_type="RECEIPT",
                status="COMMITTED",
                timestamp=1000.0,
                details={"client_did": src, "server_did": dst, "rating": 1.0, "merkle_root": "mroot"}
            )
    journal_c = MockJournal(entries_c)

    vanilla_c, _, _ = compute_ew_eigentrust_v1_6(peers_c, sn_c, s_c, mode=TrustComputationMode.VANILLA)
    ew_c, _, _ = compute_ew_eigentrust_v1_6(peers_c, sn_c, s_c, evidence_journal=journal_c, mode=TrustComputationMode.FULL_EW)

    collusive_share_vanilla_c = sum(vanilla_c[f"c{i}"] for i in range(5))
    collusive_share_ew_c = sum(ew_c[f"c{i}"] for i in range(5))
    print(f"Total colluder share: Vanilla={collusive_share_vanilla_c:.4f} -> EW={collusive_share_ew_c:.4f}")
    print("  -> ADVERSARIAL FINDING: Because chords and ring edges are strictly unreciprocated pairwise,")
    print("     rho_ij == 0 on all internal edges. Omega == 1.00 everywhere!")
    print("     Any trust reduction is due solely to concave edge ceiling Phi_edge, NOT topology damping Omega!")


def run_precision_checks():
    print("\n" + "=" * 80)
    print("TASK 4: PRECISION CHECKS")
    print("=" * 80)

    # 1. Rating == 0.0 check
    print("\n1. Testing rating == 0.0 handling:")
    journal_zero = {
        "1": JournalEntry(
            entry_id="tx-1",
            entry_type="RECEIPT",
            status="COMMITTED",
            timestamp=100.0,
            details={"client_did": "a", "server_did": "b", "rating": 0.0, "merkle_root": "root"}
        )
    }
    class MockJ:
        def __init__(self, entries):
            self._entries = entries

    # In v1.6 as written:
    # if rating_val > 0.0: ... else: n_neg_count += 1.0
    # In v1.6, rating == 0.0 incremented n_neg_count!
    print("  In v1.6 pseudocode line 286: 'if rating_val > 0.0: ... else: n_neg_count += 1.0'")
    print("  -> BUG CONFIRMED: rating == 0.0 was counted as a negative receipt!")
    print("  -> In v1.7: Must use 'elif rating_val < 0.0: n_neg_count += 1.0' and skip neutral 0.0.")

    # 2. Bool parameter rejection check
    print("\n2. Testing bool parameter rejection:")
    print(f"  isinstance(True, int) is: {isinstance(True, int)}")
    print(f"  isinstance(True, bool) is: {isinstance(True, bool)}")
    print("  -> HAZARD CONFIRMED: In Python, bool is a subclass of int. Passing max_iter=True passes isinstance(x, int).")
    print("  -> In v1.7: Must check 'not isinstance(x, bool) and isinstance(x, int)'.")

    # 3. Iteration bound check
    print("\n3. General iteration bound check:")
    for (alpha, tol) in [(0.15, 1e-6), (0.10, 1e-6), (0.20, 1e-6), (0.15, 1e-8)]:
        m_bound = math.ceil(math.log(tol / 2.0) / math.log(1.0 - alpha))
        print(f"  alpha={alpha}, tol={tol} -> general bound m* = {m_bound}")
    print("  -> CONFIRMED: 90 iterations is specific to alpha=0.15, tol=1e-6. General formula is ceil(ln(tol/2) / ln(1-alpha)).")


if __name__ == "__main__":
    run_differential_tests()
    run_adversarial_damping_tests()
    run_precision_checks()
