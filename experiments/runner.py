"""
Phase 6 Experiment Suite Runner
Orchestrates multi-seed execution of Scenarios A through G, parameter sweeps,
statistical aggregation, and machine-readable output generation (JSON/CSV).
"""

import os
import json
import csv
import time
from typing import List, Dict, Any, Optional
import numpy as np

from experiments.config import ExperimentConfig
from experiments.scenarios import ExperimentTrialRunner
from experiments.statistics import calculate_distribution_stats, perform_welch_ttest


class ExperimentSuiteRunner:
    """
    Coordinates execution of experimental campaigns and statistical summarization.
    """
    def __init__(self, output_dir: str = "results", default_seeds: int = 20):
        self.output_dir = output_dir
        self.default_seeds = default_seeds
        os.makedirs(self.output_dir, exist_ok=True)

    def run_suite(self, num_seeds: Optional[int] = None) -> Dict[str, Any]:
        """
        Executes the full evaluation suite across all scenarios with multiple seeds.
        """
        n_seeds = num_seeds if num_seeds is not None else self.default_seeds
        seeds = [42 + i * 17 for i in range(n_seeds)]

        all_raw_results: List[Dict[str, Any]] = []

        print(f"\n=======================================================")
        print(f" Starting Phase 6 Multi-Seed Experiment Suite ({n_seeds} seeds)")
        print(f"=======================================================")

        # 1. Scenario A: Honest Baseline
        print("\n--- Running Scenario A: Honest Baseline ---")
        for s in seeds:
            cfg = ExperimentConfig(
                scenario_name="scenario_a_honest",
                num_honest=15, num_supernodes=5, num_sybils=0,
                total_rounds=8, seed=s, difficulty_bits=6
            )
            runner = ExperimentTrialRunner(cfg)
            res = runner.run()
            all_raw_results.append(res)

        # 2. Scenario B: Poisoning Parameter Sweep
        print("\n--- Running Scenario B: Poisoning Rate Sweep ---")
        poison_rates = [0.0, 0.05, 0.10, 0.20, 0.30, 0.50]
        for p_rate in poison_rates:
            for s in seeds:
                cfg = ExperimentConfig(
                    scenario_name="scenario_b_poisoning",
                    num_honest=15, num_supernodes=5, num_sybils=5,
                    total_rounds=8, seed=s, poisoning_rate=p_rate,
                    difficulty_bits=6
                )
                runner = ExperimentTrialRunner(cfg)
                res = runner.run()
                all_raw_results.append(res)

        # 3. Scenario C: Isolated Sybil Sweep
        print("\n--- Running Scenario C: Isolated Sybil Sweep ---")
        sybil_counts = [0, 5, 10, 15, 20]
        for s_cnt in sybil_counts:
            for s in seeds:
                cfg = ExperimentConfig(
                    scenario_name="scenario_c_isolated_sybil",
                    num_honest=15, num_supernodes=5, num_sybils=s_cnt,
                    bridge_probability=0.0, total_rounds=8, seed=s,
                    difficulty_bits=6
                )
                runner = ExperimentTrialRunner(cfg)
                res = runner.run()
                all_raw_results.append(res)

        # 4. Scenario D: Connected Collusion (Bridge Probability Sweep)
        print("\n--- Running Scenario D: Connected Collusion Sweep ---")
        bridge_probs = [0.0, 0.05, 0.10, 0.20, 0.40]
        for b_prob in bridge_probs:
            for s in seeds:
                cfg = ExperimentConfig(
                    scenario_name="scenario_d_collusion",
                    num_honest=15, num_supernodes=5, num_sybils=10,
                    bridge_probability=b_prob, total_rounds=8, seed=s,
                    difficulty_bits=6
                )
                runner = ExperimentTrialRunner(cfg)
                res = runner.run()
                all_raw_results.append(res)

        # 5. Scenario E: Replay Resistance Sweep
        print("\n--- Running Scenario E: Replay Resistance Sweep ---")
        replay_rates = [0.0, 0.10, 0.25, 0.50, 1.00]
        for r_rate in replay_rates:
            for s in seeds:
                cfg = ExperimentConfig(
                    scenario_name="scenario_e_replay",
                    num_honest=15, num_supernodes=5, num_sybils=5,
                    replay_rate=r_rate, total_rounds=8, seed=s,
                    difficulty_bits=6
                )
                runner = ExperimentTrialRunner(cfg)
                res = runner.run()
                all_raw_results.append(res)

        # 6. Scenario F: Revocation Quorum & Eviction
        print("\n--- Running Scenario F: Revocation Scaling ---")
        for s in seeds:
            cfg = ExperimentConfig(
                scenario_name="scenario_f_revocation",
                num_honest=15, num_supernodes=5, num_sybils=5,
                poisoning_rate=0.50, enable_revocation=True, enable_quorum=True,
                total_rounds=8, seed=s, difficulty_bits=6
            )
            runner = ExperimentTrialRunner(cfg)
            res = runner.run()
            all_raw_results.append(res)

        # 7. Scenario G: Benign Fault / False Positive Evaluation
        print("\n--- Running Scenario G: Benign Delivery Faults ---")
        for s in seeds:
            cfg = ExperimentConfig(
                scenario_name="scenario_g_benign_fault",
                num_honest=15, num_supernodes=5, num_sybils=0,
                benign_fault_rate=0.40, total_rounds=8, seed=s,
                difficulty_bits=6
            )
            runner = ExperimentTrialRunner(cfg)
            res = runner.run()
            all_raw_results.append(res)

        # 8. Baselines Comparison (Scenario D under 3 Baselines)
        print("\n--- Running Baseline Comparison Suite ---")
        for b_name in ["vanilla_eigentrust", "local_only", "naive_direct"]:
            for s in seeds[:5]:  # 5 seeds for comparative baseline profiling
                cfg = ExperimentConfig(
                    scenario_name=f"baseline_cmp_{b_name}",
                    num_honest=15, num_supernodes=5, num_sybils=10,
                    bridge_probability=0.20, total_rounds=8, seed=s,
                    trust_baseline=b_name, difficulty_bits=6
                )
                runner = ExperimentTrialRunner(cfg)
                res = runner.run()
                all_raw_results.append(res)

        print("\n=======================================================")
        print(f" Suite Completed: {len(all_raw_results)} total trial executions.")
        print(f" Writing machine-readable summaries to {self.output_dir}...")
        print(f"=======================================================")

        # Save machine-readable outputs
        self._save_raw_json(all_raw_results)
        self._save_raw_csv(all_raw_results)
        summary_stats = self._compute_summary_statistics(all_raw_results)
        self._save_summary_csv(summary_stats)
        self._save_confidence_intervals_csv(summary_stats)

        return {
            "total_trials": len(all_raw_results),
            "summary_stats": summary_stats,
            "output_dir": self.output_dir
        }

    def _save_raw_json(self, raw_results: List[Dict[str, Any]]):
        path = os.path.join(self.output_dir, "raw_results.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(raw_results, f, indent=2)

    def _save_raw_csv(self, raw_results: List[Dict[str, Any]]):
        path = os.path.join(self.output_dir, "raw_results.csv")
        fieldnames = [
            "scenario_name", "seed", "num_honest", "num_sybils", "total_rounds",
            "poisoning_rate", "bridge_probability", "replay_rate", "benign_fault_rate", "trust_baseline",
            "detection_rate", "false_positive_rate", "precision", "recall", "f1_score",
            "sybil_trust_share", "honest_trust_share", "supernode_trust_share",
            "collusion_gain", "replay_acceptance_rate", "evidence_acceptance_rate",
            "revocation_success_rate", "false_revocation_rate"
        ]
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in raw_results:
                cfg = r["config"]
                cm = r["confusion"]
                ts = r["trust_shares"]
                op = r["operational"]
                writer.writerow({
                    "scenario_name": cfg["scenario_name"],
                    "seed": cfg["seed"],
                    "num_honest": cfg["num_honest"],
                    "num_sybils": cfg["num_sybils"],
                    "total_rounds": cfg["total_rounds"],
                    "poisoning_rate": cfg["poisoning_rate"],
                    "bridge_probability": cfg["bridge_probability"],
                    "replay_rate": cfg["replay_rate"],
                    "benign_fault_rate": cfg["benign_fault_rate"],
                    "trust_baseline": cfg["trust_baseline"],
                    "detection_rate": cm["detection_rate"],
                    "false_positive_rate": cm["false_positive_rate"],
                    "precision": cm["precision"],
                    "recall": cm["recall"],
                    "f1_score": cm["f1_score"],
                    "sybil_trust_share": ts["sybil_trust_share"],
                    "honest_trust_share": ts["honest_trust_share"],
                    "supernode_trust_share": ts["supernode_trust_share"],
                    "collusion_gain": r["collusion_gain"],
                    "replay_acceptance_rate": op["replay_acceptance_rate"],
                    "evidence_acceptance_rate": op["evidence_acceptance_rate"],
                    "revocation_success_rate": op["revocation_success_rate"],
                    "false_revocation_rate": op["false_revocation_rate"]
                })

    def _compute_summary_statistics(self, raw_results: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        # Group trials by (scenario_name, relevant parameter)
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for r in raw_results:
            cfg = r["config"]
            scen = cfg["scenario_name"]
            key = scen
            if scen == "scenario_b_poisoning":
                key = f"{scen}_p{cfg['poisoning_rate']:.2f}"
            elif scen == "scenario_c_isolated_sybil":
                key = f"{scen}_s{cfg['num_sybils']}"
            elif scen == "scenario_d_collusion":
                key = f"{scen}_b{cfg['bridge_probability']:.2f}"
            elif scen == "scenario_e_replay":
                key = f"{scen}_r{cfg['replay_rate']:.2f}"

            if key not in grouped:
                grouped[key] = []
            grouped[key].append(r)

        summaries = {}
        metrics_keys = [
            ("detection_rate", lambda x: x["confusion"]["detection_rate"]),
            ("false_positive_rate", lambda x: x["confusion"]["false_positive_rate"]),
            ("precision", lambda x: x["confusion"]["precision"]),
            ("recall", lambda x: x["confusion"]["recall"]),
            ("f1_score", lambda x: x["confusion"]["f1_score"]),
            ("sybil_trust_share", lambda x: x["trust_shares"]["sybil_trust_share"]),
            ("honest_trust_share", lambda x: x["trust_shares"]["honest_trust_share"]),
            ("collusion_gain", lambda x: x["collusion_gain"]),
            ("replay_acceptance_rate", lambda x: x["operational"]["replay_acceptance_rate"]),
            ("revocation_success_rate", lambda x: x["operational"]["revocation_success_rate"])
        ]

        for group_key, trial_list in grouped.items():
            summaries[group_key] = {}
            for m_name, extractor in metrics_keys:
                vals = [extractor(t) for t in trial_list]
                summaries[group_key][m_name] = calculate_distribution_stats(vals)

        return summaries

    def _save_summary_csv(self, summary_stats: Dict[str, Dict[str, Any]]):
        path = os.path.join(self.output_dir, "summary.csv")
        fieldnames = ["group_key", "metric", "count", "mean", "median", "std", "min", "max", "ci_lower", "ci_upper"]
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for g_key, m_dict in summary_stats.items():
                for m_name, stats_dict in m_dict.items():
                    row = {"group_key": g_key, "metric": m_name}
                    row.update(stats_dict)
                    writer.writerow(row)

    def _save_confidence_intervals_csv(self, summary_stats: Dict[str, Dict[str, Any]]):
        path = os.path.join(self.output_dir, "confidence_intervals.csv")
        fieldnames = ["group_key", "metric", "mean", "std", "ci_lower", "ci_upper"]
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for g_key, m_dict in summary_stats.items():
                for m_name, stats_dict in m_dict.items():
                    writer.writerow({
                        "group_key": g_key,
                        "metric": m_name,
                        "mean": stats_dict["mean"],
                        "std": stats_dict["std"],
                        "ci_lower": stats_dict["ci_lower"],
                        "ci_upper": stats_dict["ci_upper"]
                    })
