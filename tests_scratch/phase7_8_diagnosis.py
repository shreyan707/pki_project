"""
tests_scratch/phase7_8_diagnosis.py
Phase 7.8: Structural Diagnosis of the Damping Rule and Equivalence Domain
Author: Independent Mathematical and Adversarial Auditor
Date: October 9, 2026
"""

import sys
import os
import math
import hashlib
import numpy as np

# Ensure root directory is on sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from src.layer3_eigentrust import EigenTrustEngine, PeerState, LocalEvidenceJournal, JournalEntry


# =============================================================================
# Helper: SHA-256 of file
# =============================================================================
def get_file_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


# =============================================================================
# Core EW-EigenTrust Pipeline with Modular Modes & Candidates
# =============================================================================
def compute_trust_pipeline(
    peers,
    supernodes,
    raw_s_matrix,
    mode="vanilla",
    alpha=0.15,
    k_max=10.0,
    lambda_sat=0.50,
    mu_unverified=0.10,
    mu_referenced=0.25,
    beta_entropy=2.0,
    theta_penalty=0.85,
    epsilon_floor=0.10,
    delta_reg=2.0,
    max_iter=100,
    tol=1e-6,
    leak_to_restart=False,
    cycle_aware=False,
    verified_delivery_keys=None,
    known_manifest_roots=None,
    pair_receipt_counts=None  # dict (src, dst) -> (pos_count, neg_count, has_verified, has_manifest)
):
    canonical_peers = sorted(list(set(str(p) for p in peers if p and isinstance(p, str))))
    n = len(canonical_peers)
    if n == 0:
        return {}, True, 0, None

    peer_to_idx = {did: idx for idx, did in enumerate(canonical_peers)}
    valid_supernodes = sorted(list(set(str(sn) for sn in (supernodes or []) if str(sn) in peer_to_idx)))

    p = np.zeros(n, dtype=np.float64)
    if valid_supernodes:
        sn_weight = 1.0 / len(valid_supernodes)
        for sn in valid_supernodes:
            p[peer_to_idx[sn]] = sn_weight
    else:
        p.fill(1.0 / n)

    # 1. Base interaction matrix A_ij
    A = np.zeros((n, n), dtype=np.float64)

    for i, src in enumerate(canonical_peers):
        for j, dst in enumerate(canonical_peers):
            if i == j:
                continue

            if mode in ("vanilla", "topology_only"):
                val = raw_s_matrix.get((src, dst), 0.0)
                if isinstance(val, bool) or not isinstance(val, (int, float)) or not math.isfinite(val):
                    val = 0.0
                A[i, j] = max(0.0, float(val))
            else:
                # Evidence-weighted modes (evidence_only, full_ew)
                if pair_receipt_counts and (src, dst) in pair_receipt_counts:
                    pos_c, neg_c, has_ver, has_man = pair_receipt_counts[(src, dst)]
                    gamma_ev = 1.00 if has_ver else (mu_referenced if has_man else mu_unverified)
                    e_pos = pos_c * gamma_ev
                    gamma_dispute = max(0.0, 1.0 - (2.0 * neg_c / (pos_c + 1.0))) if pos_c > 0 else 0.0
                    A[i, j] = k_max * math.tanh((lambda_sat * e_pos) / k_max) * gamma_dispute
                else:
                    # If raw scores provided as proxy for positive receipts count
                    val = raw_s_matrix.get((src, dst), 0.0)
                    if isinstance(val, bool) or not isinstance(val, (int, float)) or not math.isfinite(val):
                        val = 0.0
                    val = max(0.0, float(val))
                    if val > 0:
                        A[i, j] = k_max * math.tanh((lambda_sat * val) / k_max)
                    else:
                        A[i, j] = 0.0

    # 2. Topology damping matrix Omega_ij
    Omega = np.ones((n, n), dtype=np.float64)

    if mode in ("topology_only", "full_ew"):
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

                    # Candidate (ii): Cycle-aware signal extension
                    if cycle_aware:
                        # Construct 1-step transition probability matrix P_norm
                        row_s = np.sum(A[i, :])
                        # Check 2-step and 3-step return from j back to i
                        # If j -> k -> i with high probability, cycle suspicion is triggered
                        P_base = np.zeros((n, n))
                        for r in range(n):
                            rs = np.sum(A[r, :])
                            if rs > 0:
                                P_base[r, :] = A[r, :] / rs
                        # 2-step return to i from j: P_base[j, i]
                        # 3-step return to i from j: sum_k P_base[j, k] * P_base[k, i]
                        cycle3 = np.sum(P_base[j, :] * P_base[:, i])
                        # Combines pairwise reciprocity + directed cycle return
                        cycle_score = max(rho_ij, cycle3)
                        sigma_ij = cycle_score * math.pow(1.0 - min_entropy, beta_entropy)

                    Omega[i, j] = max(epsilon_floor, 1.0 - (theta_penalty * sigma_ij))

    # 3. Transition matrix C_prime
    S_prime = Omega * A
    C_prime = np.zeros((n, n), dtype=np.float64)

    for i in range(n):
        row_total = np.sum(S_prime[i, :])
        base_total = np.sum(A[i, :])
        if row_total > 0:
            if leak_to_restart and base_total > 0:
                # Candidate (i): Leak-to-restart
                deficit = max(0.0, 1.0 - (row_total / base_total))
                C_prime[i, :] = (S_prime[i, :] / base_total) + deficit * p
            else:
                C_prime[i, :] = S_prime[i, :] / row_total
        else:
            C_prime[i, :] = p

    # 4. Power iteration
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

    scores = {canonical_peers[i]: float(t[i]) for i in range(n)}
    return scores, converged, executed_iters, C_prime


# =============================================================================
# TASK 1: REPRODUCE AND ATTRIBUTE TOPOLOGY RESULTS
# =============================================================================
def run_task_1():
    print("=" * 80)
    print("TASK 1: REPRODUCE AND ATTRIBUTE PHASE 7.7 TOPOLOGY RESULTS")
    print("=" * 80)

    # -------------------------------------------------------------------------
    # TOPOLOGY (a): Pairwise reciprocal colluding pair
    # -------------------------------------------------------------------------
    peers_a = ["h0", "h1", "c0", "c1"]
    sn_a = ["h0"]
    # Closed:
    s_a_closed = {
        ("h0", "h1"): 10.0,
        ("h1", "h0"): 10.0,
        ("h0", "c0"): 5.0,
        ("c0", "c1"): 20.0,
        ("c1", "c0"): 20.0
    }
    # Leaky:
    s_a_leaky = dict(s_a_closed)
    s_a_leaky[("c0", "h1")] = 2.0
    s_a_leaky[("c1", "h0")] = 2.0

    # -------------------------------------------------------------------------
    # TOPOLOGY (b): Directed 3-cycle
    # -------------------------------------------------------------------------
    peers_b = ["h0", "h1", "c0", "c1", "c2"]
    sn_b = ["h0"]
    # Closed:
    s_b_closed = {
        ("h0", "h1"): 10.0,
        ("h1", "h0"): 10.0,
        ("h0", "c0"): 5.0,
        ("c0", "c1"): 20.0,
        ("c1", "c2"): 20.0,
        ("c2", "c0"): 20.0
    }
    # Leaky:
    s_b_leaky = dict(s_b_closed)
    s_b_leaky[("c1", "h1")] = 2.0
    s_b_leaky[("c2", "h0")] = 2.0

    # -------------------------------------------------------------------------
    # TOPOLOGY (c): 5-node directed ring with chords
    # -------------------------------------------------------------------------
    peers_c = ["h0", "h1", "c0", "c1", "c2", "c3", "c4"]
    sn_c = ["h0"]
    # Closed:
    s_c_closed = {
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
    # Leaky:
    s_c_leaky = dict(s_c_closed)
    s_c_leaky[("c2", "h1")] = 2.0
    s_c_leaky[("c4", "h0")] = 2.0

    topologies = [
        ("Topology (a) - Pairwise Pair [CLOSED]", peers_a, sn_a, s_a_closed, ["c0", "c1"], ["h0", "h1"], True),
        ("Topology (a) - Pairwise Pair [LEAKY]",  peers_a, sn_a, s_a_leaky,  ["c0", "c1"], ["h0", "h1"], False),
        ("Topology (b) - Directed 3-Cycle [CLOSED]", peers_b, sn_b, s_b_closed, ["c0", "c1", "c2"], ["h0", "h1"], True),
        ("Topology (b) - Directed 3-Cycle [LEAKY]",  peers_b, sn_b, s_b_leaky,  ["c0", "c1", "c2"], ["h0", "h1"], False),
        ("Topology (c) - 5-Node Ring + Chords [CLOSED]", peers_c, sn_c, s_c_closed, [f"c{i}" for i in range(5)], ["h0", "h1"], True),
        ("Topology (c) - 5-Node Ring + Chords [LEAKY]",  peers_c, sn_c, s_c_leaky,  [f"c{i}" for i in range(5)], ["h0", "h1"], False),
    ]

    modes = ["vanilla", "evidence_only", "topology_only", "full_ew"]

    for title, peers, sn, raw_s, c_set, h_set, is_closed in topologies:
        print(f"\n{'='*70}\n{title}\n{'='*70}")
        print("INPUT RAW EDGES:")
        for k, v in sorted(raw_s.items()):
            print(f"  {k[0]} -> {k[1]}: {v}")

        print("\n4-WAY ABLATION RESULTS:")
        for m in modes:
            scores, conv, iters, C_mat = compute_trust_pipeline(peers, sn, raw_s, mode=m, alpha=0.15)
            c_share = sum(scores[c] for c in c_set)
            h_share = sum(scores[h] for h in h_set)
            node_str = ", ".join(f"{k}:{scores[k]:.4f}" for k in sorted(scores.keys()))
            print(f"  [{m.upper():14s}] Colluders={c_share:.4f} | Honest={h_share:.4f} | Nodes: ({node_str})")

            # Check Closed-Set Identity if closed
            if is_closed:
                # Identity: sum_{c in C} t_c = ((1 - alpha)/alpha) * sum_{h in H} t_h * sum_{c in C} C'_{hc}
                t_c_sum = c_share
                alpha = 0.15
                scale = (1.0 - alpha) / alpha
                canonical_p = sorted(list(set(peers)))
                flow_from_h = 0.0
                for h in h_set:
                    h_idx = canonical_p.index(h)
                    t_h = scores[h]
                    row_weight_to_c = sum(C_mat[h_idx, canonical_p.index(c)] for c in c_set)
                    flow_from_h += t_h * row_weight_to_c

                predicted_c_sum = scale * flow_from_h
                residual = abs(t_c_sum - predicted_c_sum)
                print(f"    -> Closed-Set Identity Check: Actual={t_c_sum:.6f}, Predicted={predicted_c_sum:.6f}, Residual={residual:.2e}")
                assert residual < 1e-5, f"Identity violated! residual={residual}"


# =============================================================================
# TASK 2: EVALUATE CANDIDATE MECHANISMS & CONTROLS
# =============================================================================
def run_task_2():
    print("\n" + "=" * 80)
    print("TASK 2: STRUCTURAL ANALYSIS, CANDIDATE MECHANISMS & PRE-REGISTERED CONTROLS")
    print("=" * 80)

    # Pre-registered thresholds
    print("PRE-REGISTERED EVALUATION THRESHOLDS (written prior to candidate runs):")
    print("  1. Colluder trust share must fall >= 25% relative to VANILLA on (a), (b), (c), closed and leaky.")
    print("  2. Honest community trust must not fall > 5% on Control 1 (dense honest community).")
    print("  3. Honest asymmetric uploader trust must not fall > 5% on Control 2 (pure seedbox).")
    print("  4. Failing any control => Candidate FAILS.\n")

    # Control 1: Dense Honest Reciprocal Community with Bridge
    # h0 (SN), h1, h2, h3 mutual; h0 -> h_out (bridge)
    peers_ctrl1 = ["h0", "h1", "h2", "h3", "h_out"]
    sn_ctrl1 = ["h0"]
    s_ctrl1 = {
        ("h0", "h1"): 10.0, ("h1", "h0"): 10.0,
        ("h1", "h2"): 10.0, ("h2", "h1"): 10.0,
        ("h2", "h3"): 10.0, ("h3", "h2"): 10.0,
        ("h3", "h0"): 10.0, ("h0", "h3"): 10.0,
        ("h0", "h_out"): 5.0
    }
    honest_comm_ctrl1 = ["h0", "h1", "h2", "h3"]

    # Control 2: Honest Asymmetric Uploader
    # u0 uploads to h1..h5 (receives 10 from each), grants 0 ratings
    peers_ctrl2 = ["h0", "u0", "h1", "h2", "h3", "h4", "h5"]
    sn_ctrl2 = ["h0"]
    s_ctrl2 = {
        ("h0", "h1"): 5.0, ("h0", "h2"): 5.0,
        ("h1", "u0"): 10.0,
        ("h2", "u0"): 10.0,
        ("h3", "u0"): 10.0,
        ("h4", "u0"): 10.0,
        ("h5", "u0"): 10.0,
    }

    # Evaluate Vanilla on Controls
    van_ctrl1, _, _, _ = compute_trust_pipeline(peers_ctrl1, sn_ctrl1, s_ctrl1, mode="vanilla")
    van_ctrl1_comm = sum(van_ctrl1[h] for h in honest_comm_ctrl1)

    van_ctrl2, _, _, _ = compute_trust_pipeline(peers_ctrl2, sn_ctrl2, s_ctrl2, mode="vanilla")
    van_ctrl2_u0 = van_ctrl2["u0"]

    print(f"BASELINES ON CONTROLS (Vanilla):")
    print(f"  Control 1 Honest Community Share: {van_ctrl1_comm:.4f}")
    print(f"  Control 2 Asymmetric Uploader u0:  {van_ctrl2_u0:.4f}\n")

    candidates = [
        ("Candidate (i): Leak-to-Restart", True, False),
        ("Candidate (ii): Cycle-Aware Walk-Return", False, True),
        ("Candidate (i+ii): Leak-to-Restart + Cycle-Aware", True, True),
    ]

    # Evaluate Candidates on Controls
    for c_name, leak, cycle in candidates:
        print(f"Evaluating {c_name} on CONTROLS:")
        c1_res, _, _, _ = compute_trust_pipeline(peers_ctrl1, sn_ctrl1, s_ctrl1, mode="full_ew", leak_to_restart=leak, cycle_aware=cycle)
        c1_comm = sum(c1_res[h] for h in honest_comm_ctrl1)
        c1_diff_pct = ((c1_comm - van_ctrl1_comm) / van_ctrl1_comm) * 100.0

        c2_res, _, _, _ = compute_trust_pipeline(peers_ctrl2, sn_ctrl2, s_ctrl2, mode="full_ew", leak_to_restart=leak, cycle_aware=cycle)
        c2_u0 = c2_res["u0"]
        c2_diff_pct = ((c2_u0 - van_ctrl2_u0) / van_ctrl2_u0) * 100.0

        print(f"  Control 1 Honest Comm: {c1_comm:.4f} (diff: {c1_diff_pct:+.2f}%) -> {'PASS' if c1_diff_pct >= -5.0 else 'FAIL (>5% drop)'}")
        print(f"  Control 2 Asymmetric u0: {c2_u0:.4f} (diff: {c2_diff_pct:+.2f}%) -> {'PASS' if c2_diff_pct >= -5.0 else 'FAIL (>5% drop)'}")

    # Now evaluate Candidates on Collusion Topologies
    test_topos = [
        ("Topo (a) Pairwise [CLOSED]", ["h0", "h1", "c0", "c1"], ["h0"], {("h0", "h1"): 10.0, ("h1", "h0"): 10.0, ("h0", "c0"): 5.0, ("c0", "c1"): 20.0, ("c1", "c0"): 20.0}, ["c0", "c1"]),
        ("Topo (a) Pairwise [LEAKY]",  ["h0", "h1", "c0", "c1"], ["h0"], {("h0", "h1"): 10.0, ("h1", "h0"): 10.0, ("h0", "c0"): 5.0, ("c0", "c1"): 20.0, ("c1", "c0"): 20.0, ("c0", "h1"): 2.0, ("c1", "h0"): 2.0}, ["c0", "c1"]),
        ("Topo (b) 3-Cycle [CLOSED]",  ["h0", "h1", "c0", "c1", "c2"], ["h0"], {("h0", "h1"): 10.0, ("h1", "h0"): 10.0, ("h0", "c0"): 5.0, ("c0", "c1"): 20.0, ("c1", "c2"): 20.0, ("c2", "c0"): 20.0}, ["c0", "c1", "c2"]),
        ("Topo (b) 3-Cycle [LEAKY]",   ["h0", "h1", "c0", "c1", "c2"], ["h0"], {("h0", "h1"): 10.0, ("h1", "h0"): 10.0, ("h0", "c0"): 5.0, ("c0", "c1"): 20.0, ("c1", "c2"): 20.0, ("c2", "c0"): 20.0, ("c1", "h1"): 2.0, ("c2", "h0"): 2.0}, ["c0", "c1", "c2"]),
        ("Topo (c) 5-Ring [CLOSED]",   ["h0", "h1", "c0", "c1", "c2", "c3", "c4"], ["h0"], {("h0", "h1"): 10.0, ("h1", "h0"): 10.0, ("h0", "c0"): 5.0, ("c0", "c1"): 15.0, ("c1", "c2"): 15.0, ("c2", "c3"): 15.0, ("c3", "c4"): 15.0, ("c4", "c0"): 15.0, ("c0", "c2"): 10.0, ("c1", "c3"): 10.0}, [f"c{i}" for i in range(5)]),
        ("Topo (c) 5-Ring [LEAKY]",    ["h0", "h1", "c0", "c1", "c2", "c3", "c4"], ["h0"], {("h0", "h1"): 10.0, ("h1", "h0"): 10.0, ("h0", "c0"): 5.0, ("c0", "c1"): 15.0, ("c1", "c2"): 15.0, ("c2", "c3"): 15.0, ("c3", "c4"): 15.0, ("c4", "c0"): 15.0, ("c0", "c2"): 10.0, ("c1", "c3"): 10.0, ("c2", "h1"): 2.0, ("c4", "h0"): 2.0}, [f"c{i}" for i in range(5)]),
    ]

    print("\n" + "-" * 70)
    print("EVALUATING CANDIDATES ON COLLUSION TOPOLOGIES:")
    print("-" * 70)

    for t_name, p_list, sn_list, s_map, c_nodes in test_topos:
        van_res, _, _, _ = compute_trust_pipeline(p_list, sn_list, s_map, mode="vanilla")
        van_c = sum(van_res[c] for c in c_nodes)
        print(f"\n{t_name} (Vanilla Colluder Share: {van_c:.4f}):")

        for c_name, leak, cycle in candidates:
            cand_res, _, _, _ = compute_trust_pipeline(p_list, sn_list, s_map, mode="full_ew", leak_to_restart=leak, cycle_aware=cycle)
            cand_c = sum(cand_res[c] for c in c_nodes)
            reduc_pct = ((van_c - cand_c) / van_c) * 100.0
            passed = reduc_pct >= 25.0
            print(f"  {c_name:40s}: Colluder Share={cand_c:.4f} (Reduction: {reduc_pct:+.2f}%) -> {'PASS (>=25%)' if passed else 'FAIL (<25%)'}")

    # Adaptive Attacker Run
    print("\n" + "-" * 70)
    print("ADAPTIVE ATTACKER RUN:")
    print("-" * 70)
    # Colluders add external edges to multiple honest peers and disperse weights to lower reciprocity and raise entropy
    peers_adapt = ["h0", "h1", "h2", "c0", "c1", "c2"]
    sn_adapt = ["h0"]
    s_adapt = {
        ("h0", "h1"): 10.0, ("h1", "h0"): 10.0,
        ("h0", "c0"): 5.0,
        ("c0", "c1"): 10.0, ("c1", "c2"): 10.0, ("c2", "c0"): 10.0,
        # Adaptive camouflage: rate multiple honest nodes
        ("c0", "h1"): 5.0, ("c1", "h2"): 5.0, ("c2", "h0"): 5.0
    }
    c_adapt = ["c0", "c1", "c2"]
    van_ad, _, _, _ = compute_trust_pipeline(peers_adapt, sn_adapt, s_adapt, mode="vanilla")
    van_ad_c = sum(van_ad[c] for c in c_adapt)
    print(f"Adaptive Attacker Vanilla Colluder Share: {van_ad_c:.4f}")
    for c_name, leak, cycle in candidates:
        cand_ad, _, _, _ = compute_trust_pipeline(peers_adapt, sn_adapt, s_adapt, mode="full_ew", leak_to_restart=leak, cycle_aware=cycle)
        cand_ad_c = sum(cand_ad[c] for c in c_adapt)
        reduc_ad_pct = ((van_ad_c - cand_ad_c) / van_ad_c) * 100.0
        print(f"  {c_name:40s}: Colluder Share={cand_ad_c:.4f} (Reduction: {reduc_ad_pct:+.2f}%)")


# =============================================================================
# TASK 3: EVIDENCE-TIER ADVERSARIAL REVIEW (COMPUTED EXAMPLE)
# =============================================================================
def run_task_3():
    print("\n" + "=" * 80)
    print("TASK 3: EVIDENCE-TIER ADVERSARIAL REVIEW")
    print("=" * 80)

    # Label-Blind Rule: What if colluders perform real chunk deliveries to each other?
    # Test topology: h0 (SN), h1, c0, c1
    # Bridge h0 -> c0: verified delivery (10 transfers)
    # Colluders c0 <-> c1:
    #   Case A: Colluders cite manifest root only (Tier 2, weight 0.25)
    #   Case B: Colluders do genuine chunk deliveries to each other (Tier 3, weight 1.00)
    peers = ["h0", "h1", "c0", "c1"]
    sn = ["h0"]
    s_map = {("h0", "h1"): 10.0, ("h1", "h0"): 10.0, ("h0", "c0"): 5.0, ("c0", "c1"): 20.0, ("c1", "c0"): 20.0}

    # Case A: Tier 2 (manifest citation only for colluders)
    pair_counts_tier2 = {
        ("h0", "h1"): (10, 0, True, True),
        ("h1", "h0"): (10, 0, True, True),
        ("h0", "c0"): (5, 0, True, True),
        ("c0", "c1"): (20, 0, False, True),  # Tier 2 (manifest referenced)
        ("c1", "c0"): (20, 0, False, True),  # Tier 2 (manifest referenced)
    }

    # Case B: Tier 3 (genuine colluder-to-colluder deliveries in canonical journal)
    pair_counts_tier3 = {
        ("h0", "h1"): (10, 0, True, True),
        ("h1", "h0"): (10, 0, True, True),
        ("h0", "c0"): (5, 0, True, True),
        ("c0", "c1"): (20, 0, True, True),   # Tier 3 (verified delivery)
        ("c1", "c0"): (20, 0, True, True),   # Tier 3 (verified delivery)
    }

    # Case C: Tier 1 (unindexed co-receipts, weight 0.10)
    pair_counts_tier1 = {
        ("h0", "h1"): (10, 0, True, True),
        ("h1", "h0"): (10, 0, True, True),
        ("h0", "c0"): (5, 0, True, True),
        ("c0", "c1"): (20, 0, False, False), # Tier 1 (unindexed)
        ("c1", "c0"): (20, 0, False, False), # Tier 1 (unindexed)
    }

    sc_t1, _, _, _ = compute_trust_pipeline(peers, sn, s_map, mode="evidence_only", pair_receipt_counts=pair_counts_tier1)
    sc_t2, _, _, _ = compute_trust_pipeline(peers, sn, s_map, mode="evidence_only", pair_receipt_counts=pair_counts_tier2)
    sc_t3, _, _, _ = compute_trust_pipeline(peers, sn, s_map, mode="evidence_only", pair_receipt_counts=pair_counts_tier3)

    c_t1 = sc_t1["c0"] + sc_t1["c1"]
    c_t2 = sc_t2["c0"] + sc_t2["c1"]
    c_t3 = sc_t3["c0"] + sc_t3["c1"]

    print("Colluder Trust Share by Evidence Tier (EVIDENCE_ONLY mode - CLOSED colluders):")
    print(f"  Tier 1 (Unindexed co-receipts, mu=0.10): Colluder Share = {c_t1:.4f}")
    print(f"  Tier 2 (Public manifest cited, mu=0.25):  Colluder Share = {c_t2:.4f}")
    print(f"  Tier 3 (Label-blind verified delivery, gamma=1.00): Colluder Share = {c_t3:.4f}")
    print("  -> Closed Set Consequence: Internal tier scaling is completely cancelled by row normalization!")

    # Leaky colluder case:
    pair_counts_t1_leaky = dict(pair_counts_tier1)
    pair_counts_t1_leaky[("c0", "h1")] = (2, 0, True, True)
    pair_counts_t1_leaky[("c1", "h0")] = (2, 0, True, True)

    pair_counts_t2_leaky = dict(pair_counts_tier2)
    pair_counts_t2_leaky[("c0", "h1")] = (2, 0, True, True)
    pair_counts_t2_leaky[("c1", "h0")] = (2, 0, True, True)

    pair_counts_t3_leaky = dict(pair_counts_tier3)
    pair_counts_t3_leaky[("c0", "h1")] = (2, 0, True, True)
    pair_counts_t3_leaky[("c1", "h0")] = (2, 0, True, True)

    sc_t1_l, _, _, _ = compute_trust_pipeline(peers, sn, s_map, mode="evidence_only", pair_receipt_counts=pair_counts_t1_leaky)
    sc_t2_l, _, _, _ = compute_trust_pipeline(peers, sn, s_map, mode="evidence_only", pair_receipt_counts=pair_counts_t2_leaky)
    sc_t3_l, _, _, _ = compute_trust_pipeline(peers, sn, s_map, mode="evidence_only", pair_receipt_counts=pair_counts_t3_leaky)

    c_t1_l = sc_t1_l["c0"] + sc_t1_l["c1"]
    c_t2_l = sc_t2_l["c0"] + sc_t2_l["c1"]
    c_t3_l = sc_t3_l["c0"] + sc_t3_l["c1"]

    print("\nColluder Trust Share by Evidence Tier (EVIDENCE_ONLY mode - LEAKY colluders):")
    print(f"  Tier 1 (Unindexed co-receipts, mu=0.10): Colluder Share = {c_t1_l:.4f}")
    print(f"  Tier 2 (Public manifest cited, mu=0.25):  Colluder Share = {c_t2_l:.4f}")
    print(f"  Tier 3 (Label-blind verified delivery, gamma=1.00): Colluder Share = {c_t3_l:.4f}")
    print("  -> Leaky Set Consequence: Genuine verified deliveries within coalition (Tier 3) dilute the honest leakage,")
    print(f"     allowing colluders to retain {c_t3_l:.4f} of trust vs only {c_t1_l:.4f} under Tier 1 unindexed receipts!")


# =============================================================================
# TASK 4: EQUIVALENCE DOMAIN & NUMERICAL BOUNDS
# =============================================================================
def run_task_4():
    print("\n" + "=" * 80)
    print("TASK 4: EQUIVALENCE DOMAIN D_equiv & STRICT ARITHMETIC BOUNDS")
    print("=" * 80)

    # 1. Concrete float64 saturation of tanh
    print("1. Concrete Float64 Saturation of tanh:")
    for val in [10.0, 15.0, 18.7, 19.0, 20.0, 50.0]:
        t_val = math.tanh(val)
        prod = 10.0 * t_val
        is_exact_10 = (prod == 10.0)
        print(f"  x={val:4.1f}: tanh(x) = {t_val:.17f}, 10.0 * tanh(x) = {prod:.17f}, equals 10.0? {is_exact_10}")

    print("  -> PROOF: In IEEE 754 float64, math.tanh(19.1) saturates to exactly 1.0.")
    print("     Therefore in float64 arithmetic, S'_{ij} <= 10.0 (equality CAN be reached).")
    print("     In real arithmetic S'_{ij} < 10.0 strictly.")

    # 2. Convergence iteration count strict floor + 1 form
    print("\n2. Strict Convergence Theorem Iteration Formula:")
    for (alpha, tol) in [(0.15, 1e-6), (0.10, 1e-6), (0.20, 1e-6), (0.15, 1e-8)]:
        float_bound = math.log(tol / 2.0) / math.log(1.0 - alpha)
        m_ceil = math.ceil(float_bound)
        m_strict = math.floor(float_bound) + 1
        print(f"  alpha={alpha}, tol={tol}: float={float_bound:.4f} -> ceil={m_ceil}, floor+1={m_strict}")
        assert m_ceil == m_strict

    # 3. |sum(t) - 1| reporting on D_equiv test cases
    print("\n3. Simplex Deviation |sum(t) - 1| for Equivalence Domain Cases (without t/t_sum):")
    cases = [
        ("N=6 Sparse", ["n0","n1","n2","n3","n4","n5"], ["n0"], {("n0","n1"): 5.0, ("n1","n2"): 3.0}),
        ("N=4 Dangling", ["d0","d1","d2","d3"], ["d0"], {("d0","d1"): 2.0}),
        ("N=3 Negative", ["x0","x1","x2"], ["x0"], {("x0","x1"): 4.0, ("x1","x2"): -2.0}),
        ("N=1 Solo", ["solo"], ["solo"], {}),
    ]
    for c_name, p, sn, s in cases:
        engine = EigenTrustEngine(peers=p, pre_trusted_peers=sn, alpha=0.15)
        for (src, dst), v in s.items():
            engine.S[engine.peer_to_idx[src], engine.peer_to_idx[dst]] = v
        eng_scores = engine.get_trust_scores()
        t_sum = sum(eng_scores.values())
        dev = abs(t_sum - 1.0)
        print(f"  [{c_name}] sum(t) = {t_sum:.17f}, |sum(t) - 1| = {dev:.2e}")


if __name__ == "__main__":
    run_task_1()
    run_task_2()
    run_task_3()
    run_task_4()
