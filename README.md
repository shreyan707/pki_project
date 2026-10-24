# PKI-Based Trust Management for P2P File-Sharing and Social Networking

**Case Study 1 (CS1)** · Course `VL2026270102689` · SCOPE, VIT Chennai
**Author:** Shreyan Nayak (`23BKT0039`) · **Baseline:** `v9.0-FINAL-FREEZE` (protocol/spec `v2.2.0-FROZEN`)

A four-layer decentralized PKI and reputation architecture that replaces centralized Certificate Authorities in peer-to-peer networks. It is implemented as a Python reference simulation and evaluated against Sybil, collusion, receipt-grinding and slander attacks.

## Architecture

| Layer | Module | Responsibility |
| :-- | :-- | :-- |
| 1. Identity | `src/layer1_identity.py` | Ed25519 self-sovereign identities (`did:peer`-style), Hashcash proof-of-work admission |
| 2. Mesh PKI | `src/layer2_mesh_pki.py` | Web-of-Trust cross-certification, bounded multi-path trust validation |
| 3. Reputation | `src/layer3_eigentrust.py` | Evidence-Weighted EigenTrust (EW-EigenTrust v1.8), Merkle chunk proofs, attributable fault evidence |
| 4. Recovery | `src/layer4_recovery.py` | m-of-n (3-of-5) threshold revocation records, Shamir key recovery |

`src/network_simulator.py` provides the swarm simulation used by the experiments.

**Scope.** P2P file sharing is implemented and empirically evaluated. Social-networking applicability is a conceptual/architectural extension only; no social-network simulation was run. Tests verify behaviour in simulation and are not formal proofs.

## Repository layout

```
src/                  Four-layer reference implementation + network simulator
tests/                Unit and regression tests
experiments/          Benchmark harness (scenarios, metrics, statistics, plots)
results/              Raw and summarised benchmark outputs (CSV/JSON)
demo_benchmark.py     Demo / full-suite runner
deliverable_reports/  Final IEEE paper, presentation, script, assessment mapping, checklist
agent_instructions/   Specs, design iterations, phase reports and audits (agent working docs)
tests_scratch/        Scripts that generate the deliverables and audit the results
reports/              Early audit and protocol correction reports
```

## Getting started

```bash
pip install numpy matplotlib          # runtime dependencies
python -m unittest discover -s tests -v

python demo_benchmark.py --suite demo                 # quick 1-run demonstration
python demo_benchmark.py --suite full --seeds 20      # multi-seed evaluation
python experiments/phase8_2_benchmark.py              # preregistered Phase 8.2 benchmark
```

Regenerating the presentation/report files additionally needs `python-docx`, `python-pptx` and `npm install` (for `pptxgenjs`); run the scripts in `tests_scratch/` from the repository root.

## Evaluation

The preregistered Phase 8.2 benchmark runs 20 seeds × 2 network scales (30 and 50 nodes) × 3 trust modes (Vanilla EigenTrust, EW-EigenTrust v1.8, Local-Only) = 1,140 paired trials across 9 scenarios (honest baseline, closed and leaky collusion, bridge sweep, adaptive attacker, receipt grinding, dispute manipulation, asymmetric uploader, reciprocal community). Outputs are in `results/phase8_2_*`.

## Deliverables (`deliverable_reports/`)

| Deliverable | Files |
| :-- | :-- |
| Final presentation (15 slides, with speaker notes) | `PKI_Trust_Management_Final_Presentation.pptx` |
| IEEE research report | `PKI_Trust_Management_IEEE_Research_Report.docx` / `.md` |
| Presentation script | `PKI_Trust_Management_Presentation_Script.docx` / `.md` |
| Assessment rubric mapping | `PKI_Trust_Management_Assessment_Mapping.md` |
| Quality-gate checklist (with checksums) | `FINAL_DELIVERABLES_CHECKLIST.md` |

## Key documents (`agent_instructions/`)

- **Specifications:** `PROTOCOL_SPEC.md`, `SECURITY_MODEL.md`, `NOVEL_TRUST_ALGORITHM_DESIGN_V1_8.md` (latest of V1–V1.8)
- **Experiments:** `PHASE8_2_PREREGISTRATION.md`, `PHASE8_2_BENCHMARK_REPORT.md`, `PHASE8_3_REPRODUCIBILITY_AUDIT.md`
- **Final synthesis and audit:** `FINAL_CASE_STUDY_SYNTHESIS_V9.md`, `FINAL_SCOPE_AND_CLAIMS_AUDIT_V9.md`, `PHASE8_12_FINAL_PRESENTATION_READINESS_REPORT.md`
- Earlier versions (V1–V8) and the Phase 3–8 reports are kept for the audit trail. Links inside them point to the original author's local paths and may not resolve.
