"""
Phase 6 Experiment Configuration Module
Defines configuration schemas and default parameters for multi-seed reproducible evaluations.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class ExperimentConfig:
    """
    Master configuration for an experimental run or trial.
    """
    scenario_name: str
    num_honest: int = 15
    num_supernodes: int = 5
    num_sybils: int = 10
    total_rounds: int = 10
    difficulty_bits: int = 8
    seed: int = 42

    # Attack & Behavior parameters
    poisoning_rate: float = 0.0          # Probability of chunk poisoning during interaction
    bridge_probability: float = 0.0      # Probability of colluder bridging to honest nodes
    replay_rate: float = 0.0             # Rate of replaying committed receipts / evidence
    benign_fault_rate: float = 0.0       # Rate of benign transmission corruption

    # Ablation / Mechanism Switches (Harness-level, production protocol semantics unmodified)
    enable_pow: bool = True
    enable_merkle: bool = True
    enable_evidence: bool = True
    enable_replay_protection: bool = True
    enable_eigentrust: bool = True
    enable_revocation: bool = True
    enable_quorum: bool = True

    # Trust Model Baseline Selection
    # "vanilla_eigentrust": standard Layer 3 EigenTrust with evidence pipeline
    # "local_only": no global propagation (rely on local direct rating sums)
    # "naive_direct": unweighted direct rating aggregation without damping
    trust_baseline: str = "vanilla_eigentrust"

    # Extra arbitrary parameters
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_name": self.scenario_name,
            "num_honest": self.num_honest,
            "num_supernodes": self.num_supernodes,
            "num_sybils": self.num_sybils,
            "total_rounds": self.total_rounds,
            "difficulty_bits": self.difficulty_bits,
            "seed": self.seed,
            "poisoning_rate": self.poisoning_rate,
            "bridge_probability": self.bridge_probability,
            "replay_rate": self.replay_rate,
            "benign_fault_rate": self.benign_fault_rate,
            "enable_pow": self.enable_pow,
            "enable_merkle": self.enable_merkle,
            "enable_evidence": self.enable_evidence,
            "enable_replay_protection": self.enable_replay_protection,
            "enable_eigentrust": self.enable_eigentrust,
            "enable_revocation": self.enable_revocation,
            "enable_quorum": self.enable_quorum,
            "trust_baseline": self.trust_baseline,
            "extra": self.extra
        }
