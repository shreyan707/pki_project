"""
Phase 6 Metrics and Ground-Truth Definitions
Defines precise mathematical formulas, classifications, and metrics calculation.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
import numpy as np


@dataclass
class GroundTruth:
    """
    Independent ground-truth labeling for simulated nodes.
    The trust algorithm or protocol must never modify this.
    """
    honest_dids: set = field(default_factory=set)
    supernode_dids: set = field(default_factory=set)
    sybil_dids: set = field(default_factory=set)
    colluder_dids: set = field(default_factory=set)
    poisoner_dids: set = field(default_factory=set)
    benign_fault_dids: set = field(default_factory=set)


@dataclass
class PerformanceTimings:
    """
    Execution latency and timing distributions across protocol phases.
    """
    admission_times: List[float] = field(default_factory=list)
    pow_solve_times: List[float] = field(default_factory=list)
    merkle_verify_times: List[float] = field(default_factory=list)
    sig_verify_times: List[float] = field(default_factory=list)
    evidence_proc_times: List[float] = field(default_factory=list)
    eigentrust_times: List[float] = field(default_factory=list)
    revocation_times: List[float] = field(default_factory=list)
    recovery_times: List[float] = field(default_factory=list)
    round_times: List[float] = field(default_factory=list)

    def summary(self) -> Dict[str, Dict[str, float]]:
        res = {}
        for name in [
            "admission_times", "pow_solve_times", "merkle_verify_times",
            "sig_verify_times", "evidence_proc_times", "eigentrust_times",
            "revocation_times", "recovery_times", "round_times"
        ]:
            arr = getattr(self, name)
            if arr:
                res[name] = {
                    "count": len(arr),
                    "mean_ms": float(np.mean(arr) * 1000.0),
                    "std_ms": float(np.std(arr) * 1000.0),
                    "median_ms": float(np.median(arr) * 1000.0),
                    "p95_ms": float(np.percentile(arr, 95) * 1000.0)
                }
            else:
                res[name] = {"count": 0, "mean_ms": 0.0, "std_ms": 0.0, "median_ms": 0.0, "p95_ms": 0.0}
        return res


def calculate_confusion_metrics(tp: int, fp: int, fn: int, tn: int) -> Dict[str, float]:
    """
    Calculates precise statistical confusion metrics:
    - detection_rate (recall): TP / (TP + FN)
    - false_positive_rate: FP / (FP + TN)
    - precision: TP / (TP + FP)
    - recall: TP / (TP + FN)
    - f1_score: 2 * precision * recall / (precision + recall)
    - accuracy: (TP + TN) / (TP + FP + FN + TN)
    """
    recall = tp / (tp + fn) if (tp + fn) > 0 else (1.0 if tp == 0 and fn == 0 else 0.0)
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    precision = tp / (tp + fp) if (tp + fp) > 0 else (1.0 if tp == 0 and fp == 0 else 0.0)
    
    if (precision + recall) > 0:
        f1 = 2.0 * (precision * recall) / (precision + recall)
    else:
        f1 = 0.0
        
    total = tp + fp + fn + tn
    accuracy = (tp + tn) / total if total > 0 else 1.0

    return {
        "detection_rate": float(recall),
        "false_positive_rate": float(fpr),
        "precision": float(precision),
        "recall": float(recall),
        "f1_score": float(f1),
        "accuracy": float(accuracy)
    }


def calculate_trust_shares(trust_scores: Dict[str, float], ground_truth: GroundTruth) -> Dict[str, float]:
    """
    Calculates trust shares partitioned by ground-truth peer categories:
    - sybil_trust_share: sum(trust of Sybil nodes) / sum(trust of all nodes)
    - honest_trust_share: sum(trust of Honest nodes) / sum(trust of all nodes)
    - supernode_trust_share: sum(trust of Supernodes) / sum(trust of all nodes)
    """
    total_trust = sum(trust_scores.values())
    if total_trust <= 0.0:
        return {
            "sybil_trust_share": 0.0,
            "honest_trust_share": 0.0,
            "supernode_trust_share": 0.0
        }

    sybil_trust = sum(trust_scores.get(did, 0.0) for did in ground_truth.sybil_dids)
    honest_trust = sum(trust_scores.get(did, 0.0) for did in ground_truth.honest_dids)
    supernode_trust = sum(trust_scores.get(did, 0.0) for did in ground_truth.supernode_dids)

    return {
        "sybil_trust_share": float(sybil_trust / total_trust),
        "honest_trust_share": float(honest_trust / total_trust),
        "supernode_trust_share": float(supernode_trust / total_trust)
    }
