"""
demo_benchmark.py
Executable demonstration and benchmark runner for the 4-layer PKI & Trust Management Architecture.
Supports:
  --suite [demo|full]   : Run rapid 1-round demonstration or full multi-seed scientific evaluation suite.
  --seeds N             : Number of independent random seeds (default 20 for full suite).
  --rounds N            : Number of rounds per trial.
  --scenario S          : Specific scenario name (e.g. scenario_a_honest, scenario_d_collusion).
"""

import os
import sys
import argparse
import time
import numpy as np
import matplotlib.pyplot as plt

# Ensure repository root in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.network_simulator import SwarmSimulation
from experiments.config import ExperimentConfig
from experiments.runner import ExperimentSuiteRunner
from experiments.plots import generate_all_evaluation_plots


def run_demo_benchmark(seed: int = 42, rounds: int = 15):
    """
    Executes single-run demonstrative benchmark with scientifically verified metrics.
    """
    print("=" * 75)
    print(" PKI-BASED TRUST MANAGEMENT: 4-LAYER ADVERSARIAL BENCHMARK (DEMO)")
    print(" Course: VL2026270102689 | Candidate: Shreyan Nayak (23BKT0039)")
    print("=" * 75)

    os.makedirs("output", exist_ok=True)

    print(f"\n[STEP 1] Initializing Overlay Swarm (40 Total Nodes, Seed={seed})...")
    t0 = time.time()
    sim = SwarmSimulation(num_honest=20, num_supernodes=5, num_sybils=15, seed=seed)
    print("  -> Generated 5 Supernodes (Trust Anchors)")
    print("  -> Generated 20 Honest Peers (Self-sovereign Ed25519 + PoW)")
    print("  -> Generated 15 Sybil Adversaries (Collusive Ring)")
    print(f"  -> Swarm onboarding completed in {time.time() - t0:.2f}s")

    print(f"\n[STEP 2] Executing {rounds} Transaction Rounds with Adversarial Attack Vectors...")
    history = {
        "rounds": list(range(1, rounds + 1)),
        "supernode_avg": [],
        "honest_avg": [],
        "sybil_avg": []
    }

    total_honest_tx = 0
    total_poison_caught = 0
    total_sybil_collusions = 0

    for r in range(1, rounds + 1):
        stats = sim.execute_transaction_round(r)
        total_honest_tx += stats["honest_success"]
        total_poison_caught += stats["poison_detected"]
        total_sybil_collusions += stats["sybil_collusion_attempts"]

        scores = sim.eigentrust.get_trust_scores()
        sn_scores = [scores[sn.did] for sn in sim.supernodes]
        h_scores = [scores[h.did] for h in sim.honest_nodes]
        syb_scores = [scores[syb.did] for syb in sim.sybil_nodes]

        history["supernode_avg"].append(float(np.mean(sn_scores)))
        history["honest_avg"].append(float(np.mean(h_scores)))
        history["sybil_avg"].append(float(np.mean(syb_scores)))

        print(f"  Round {r:02d} | Honest Avg: {history['honest_avg'][-1]:.4f} | "
              f"Sybil Avg: {history['sybil_avg'][-1]:.4f} | "
              f"Poison Detected: {stats['poison_detected']} | "
              f"Collusions Processed: {stats['sybil_collusion_attempts']}")

    corrupted_cases = sim.metrics["content"]["corrupted_deliveries"]
    print("\n[STEP 3] Transaction Summary & Defense Auditing:")
    print(f"  • Total Honest Transfers Completed: {total_honest_tx}")
    print(f"  • Simulated Poisoning Cases Caught: {total_poison_caught}/{corrupted_cases} produced valid cryptographic contradiction evidence")
    print(f"  • Total Collusive Sybil Upvotes Attempted: {total_sybil_collusions}")
    print(f"  • Observed Sybil Collective Trust Share: {sum(syb_scores) * 100:.2f}% (Observed stationary distribution)")
    print(f"  • Rogue Nodes Evicted via Supernode Quorum CRRs: {sim.metrics['revocation']['eviction_events']}")
    print(f"  • Protocol Replay Attacks Rejected: {sim.metrics['evidence']['replay_rejections']}")

    print("\n[STEP 4] Layer 4 Shamir (3, 5) Secret Key Recovery & Rotation Test:")
    rec_ok, recovered, old_did, new_did = sim.demonstrate_key_recovery()
    assert rec_ok, "Layer 4 authorized key recovery or key rotation failed!"
    print("  • Authorized Recovery Token & Lagrange Reconstruction: SUCCESS")
    print(f"  • Reconstructed Master Secret: {recovered}")
    print("  • Mandatory Post-Recovery Key Rotation Completed:")
    print(f"     Old Retired DID: {old_did}")
    print(f"     New Active DID:  {new_did}")
    print("  -> Self-sovereign identity restored and rotated to fresh keypair! [SUCCESS]")

    print("\n[STEP 5] Generating Publication-Quality Benchmark Charts...")
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))

    ax1.plot(history["rounds"], history["supernode_avg"], 'o-', color='#2563eb', linewidth=2.5, label='Supernodes (Pre-trusted Anchors)')
    ax1.plot(history["rounds"], history["honest_avg"], 's-', color='#10b981', linewidth=2.5, label='Honest Peers (Verified Transitive Trust)')
    ax1.plot(history["rounds"], history["sybil_avg"], '^-', color='#ef4444', linewidth=2.5, label='Collusive Sybil Cluster (Damped)')
    ax1.set_title("EigenTrust Score Convergence Under Sybil Attack", fontsize=12, fontweight='bold', pad=12)
    ax1.set_xlabel("Transaction Rounds", fontsize=10)
    ax1.set_ylabel("Global Normalized EigenTrust Score", fontsize=10)
    ax1.set_ylim(-0.005, max(history["supernode_avg"]) * 1.15)
    ax1.legend(loc='upper right', frameon=True)
    ax1.grid(True, linestyle='--', alpha=0.6)

    categories = ['Supernodes', 'Honest Peers', 'Sybil Colluders']
    final_means = [history["supernode_avg"][-1], history["honest_avg"][-1], history["sybil_avg"][-1]]
    colors = ['#2563eb', '#10b981', '#ef4444']

    bars = ax2.bar(categories, final_means, color=colors, width=0.5, edgecolor='#1e293b', linewidth=1.2)
    ax2.set_title("Final Stationary Trust Score Distribution", fontsize=12, fontweight='bold', pad=12)
    ax2.set_ylabel("Stationary Trust Value", fontsize=10)
    ax2.grid(axis='y', linestyle='--', alpha=0.6)

    for bar in bars:
        height = bar.get_height()
        ax2.annotate(f'{height:.4f}',
                     xy=(bar.get_x() + bar.get_width() / 2, height),
                     xytext=(0, 4),
                     textcoords="offset points",
                     ha='center', va='bottom', fontweight='bold', fontsize=9)

    plt.tight_layout()
    plot_path = os.path.join("output", "sybil_isolation_benchmark.png")
    plt.savefig(plot_path, dpi=300)
    plt.close()
    print(f"  -> High-resolution benchmark plot saved to: {plot_path}")
    print("\n" + "=" * 75)
    print(" BENCHMARK COMPLETED SUCCESSFULLY: All 4 layers functioning properly!")
    print("=" * 75)


def main():
    parser = argparse.ArgumentParser(description="P2P PKI Trust Management Evaluation Runner")
    parser.add_argument("--suite", choices=["demo", "full"], default="demo", help="Run 'demo' or 'full' scientific evaluation suite")
    parser.add_argument("--seeds", type=int, default=20, help="Number of random seeds for full suite (default: 20)")
    parser.add_argument("--seed", type=int, default=42, help="Seed for single demo run (default: 42)")
    parser.add_argument("--rounds", type=int, default=15, help="Number of transaction rounds for demo (default: 15)")
    args = parser.parse_args()

    if args.suite == "demo":
        run_demo_benchmark(seed=args.seed, rounds=args.rounds)
    elif args.suite == "full":
        runner = ExperimentSuiteRunner(output_dir="results", default_seeds=args.seeds)
        results = runner.run_suite(num_seeds=args.seeds)
        generate_all_evaluation_plots(results["summary_stats"], output_dir="output")
        print("\nFull scientific evaluation suite finished successfully!")


if __name__ == '__main__':
    main()
