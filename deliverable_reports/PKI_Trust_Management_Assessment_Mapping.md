# Assessment Rubric Mapping: PKI Trust Management Case Study

**Candidate Name:** Shreyan Nayak  
**Registration Number:** `23BKT0039`  
**School:** School of Computer Science and Engineering (SCOPE)  
**Institution:** Vellore Institute of Technology (VIT), Chennai  
**Course Code:** `VL2026270102689`  
**Assessment Task:** Case Study 1 (`CS1`)  
**Project Title:** PKI-Based Trust Management for Peer-to-Peer File-Sharing and Social Networking Platforms  
**Technical Baseline:** `v9.0-FINAL-FREEZE` (October 9, 2026)  

---

## 1. Executive Summary & Assessment Alignment

This document establishes the bidirectional traceability matrix mapping the institutional assessment requirements of the VIT Chennai Case Study 1 (CS1) curriculum to the final research deliverables:
1. **Academic Presentation:** `PKI_Trust_Management_Final_Presentation.pptx` (Exactly 15 slides, widescreen 16:9, academic dark theme, full speaker notes).
2. **IEEE Research Paper:** `PKI_Trust_Management_IEEE_Research_Report.docx` and `PKI_Trust_Management_IEEE_Research_Report.md` (Standard IEEE conference format, two-column layout, equations, empirical data tables, and authoritative references [1]–[7]).
3. **Oral Defense Script:** `PKI_Trust_Management_Presentation_Script.docx` and `PKI_Trust_Management_Presentation_Script.md` (Medium-length oral explanations, verbal transitions, and evaluator Q&A technical definitions).
4. **Primary Source Artifacts:** Frozen specifications (`PROTOCOL_SPEC.md`, `SECURITY_MODEL.md`, `NOVEL_TRUST_ALGORITHM_DESIGN_V1_8.md`), implementation modules (`src/`), preregistration protocol (`PHASE8_2_PREREGISTRATION.md`), and raw simulation outputs (`results/`).

---

## 2. Institutional Rubric Traceability Matrix

The table below maps each institutional component from the VIT Case Study template (`presentation/Case Study Format (1).docx`) and prior submission (`presentation/23BKT0039_VL2026270102689_CS1.pdf`) to its corresponding deliverable components and repository source evidence.

| Rubric Assessment Component | Institutional Requirement Description | Presentation Slide(s) | IEEE Paper Section(s) | Repository Source Artifact(s) | Verification & Audit Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Team / Candidate Details** | Candidate Name, Registration Number, School, Degree, Course Code, and Review Date. | **Slide 1**<br>*(Title & Candidate Details)* | **Title & Author Block**<br>*(Page 1 header)* | `FINAL_CASE_STUDY_SYNTHESIS_V9.md` (§1)<br>`PHASE8_12_FINAL_PRESENTATION_READINESS_REPORT.md` | Candidate: Shreyan Nayak (`23BKT0039`), SCOPE, VIT Chennai. Baseline: `v9.0-FINAL-FREEZE`. |
| **2. Title & Project Scope** | Full academic title reflecting dual P2P file-sharing and social networking scope without silent truncation. | **Slide 1**<br>*(Title & Candidate Details)*<br>**Slide 2**<br>*(Introduction & Scope)* | **Title, Abstract, & Section I**<br>*(Introduction)* | `FINAL_SCOPE_AND_CLAIMS_AUDIT_V9.md` (§1)<br>`PROTOCOL_SPEC.md` (v2.2.0-FROZEN) | Preserves exact title; distinguishes implemented P2P file sharing (1,140 trials) from conceptual social networking. |
| **3. Summary of the Work** | Problem context, limitations of centralized Certificate Authorities (CAs), P2P threat landscape, and high-level technical solution. | **Slide 2**<br>*(Intro & Background)*<br>**Slide 5**<br>*(4-Layer Architecture)* | **Section I**<br>*(Introduction)*<br>**Section IV**<br>*(Proposed Architecture)* | `FINAL_CASE_STUDY_SYNTHESIS_V9.md` (§2)<br>`SECURITY_MODEL.md` (v2.2.0-FROZEN) | Covers single points of failure in X.509 CAs, Sybil swarms, collusion cliques, and four-layer vertical synthesis. |
| **4. Prior Work Done & Literature Review** | Comparative analysis of existing decentralized PKI, Web-of-Trust, and reputation algorithms; identified research gaps. | **Slide 4**<br>*(Literature Review & Research Gap)* | **Section II**<br>*(Background & Related Work)* | `FINAL_CASE_STUDY_SYNTHESIS_V9.md` (§3)<br>IEEE References [1]–[7] | Compares PGP/SPKI [2], [6], EigenTrust [3], and W3C DIDs [1]; articulates the decoupled identity-reputation gap. |
| **5. Objective(s) of the Work** | Formal, numbered research objectives (RO-1 to RO-4) addressing identity admission, mesh PKI, reputation, and key recovery. | **Slide 3**<br>*(Problem Statement & Objectives)* | **Section III**<br>*(Problem Formulation & Threat Model)* | `FINAL_CASE_STUDY_SYNTHESIS_V9.md` (§3.2)<br>`PHASE8_2_PREREGISTRATION.md` (§1) | RO-1 (PoW Admission), RO-2 (Mesh WoT PKI), RO-3 (EW-EigenTrust v1.8), RO-4 (Fault Attribution & Recovery). |
| **6. Working Principle: Architecture Diagram** | Detailed layered architecture illustrating component interactions, data flows, and layer separation. | **Slide 5**<br>*(4-Layer Architecture Stack)* | **Section IV**<br>*(Proposed Four-Layer Architecture, Table II)* | `PROTOCOL_SPEC.md` (§2)<br>`src/core/`<br>`src/pki/` | Illustrates Layer 1 (Identity), Layer 2 (WoT PKI), Layer 3 (Reputation), Layer 4 (Revocation & Recovery). |
| **7. Working Principle: Cryptographic Mechanisms** | Technical specification of Layer 1 (DIDs & PoW), Layer 2 (PeerCertificates), and Layer 4 (Revocation & Shamir Secret Sharing). | **Slide 6** *(Layer 1)*<br>**Slide 7** *(Layer 2)*<br>**Slide 9** *(Layer 4)* | **Section IV-A, IV-B, IV-D**<br>*(Layers 1, 2, 4 Details)* | `src/pki/identity.py`<br>`src/pki/certificate.py`<br>`src/pki/shamir.py` | Ed25519 signatures, SHA-256 PoW ($D=16$), BFS path search ($d \le 3, \delta=0.5$), Shamir $(3,5)$ over $\text{GF}(2^8)$. |
| **8. Working Principle: Trust Algorithm Formulation** | Mathematical formulation of Evidence-Weighted EigenTrust v1.8, receipt integration, dispute penalties, and power iteration. | **Slide 8**<br>*(Layer 3 EW-EigenTrust)* | **Section IV-C**<br>*(Layer 3 Formulation)*<br>**Section V-B**<br>*(Trust Computation)* | `NOVEL_TRUST_ALGORITHM_DESIGN_V1_8.md`<br>`src/trust/algorithm.py`<br>`src/trust/engine.py` | Formulas: $S_{ij}$, $C'_{ij}$, and $\mathbf{t}^{(k+1)} = (1-\alpha)\mathbf{C}'^T\mathbf{t}^{(k)} + \alpha\mathbf{p}$ with $\alpha=0.15, \epsilon=10^{-6}$. |
| **9. Protocol Workflow & Fault Attribution** | Step-by-step transaction workflow from handshake to chunk delivery, Merkle inclusion proof, and contradiction proofs. | **Slide 10**<br>*(E2E File Sharing & Merkle Fault)* | **Section V-A, V-B**<br>*(End-to-End Workflow & Fault Proofs)* | `src/merkle/`<br>`src/protocol/`<br>`FINAL_CASE_STUDY_SYNTHESIS_V9.md` (§5) | States Merkle verification complexity correctly as $O(\log N)$ hash operations and sibling hashes. |
| **10. Experimental Methodology & Benchmark** | Rigorous evaluation design: paired seeds, network sizes ($N=30, 50$), 8 threat scenarios, and 3 computation modes. | **Slide 11**<br>*(Methodology & Benchmark)* | **Section VI**<br>*(Experimental Methodology)* | `PHASE8_2_PREREGISTRATION.md`<br>`experiments/phase8_2_benchmark.py` | 1,140 total runs, 100 paired seeds ($S=100$), Wilcoxon signed-rank tests, Cohen's $d$ effect sizes. |
| **11. Results & Findings: Collusion Suppression** | Validated empirical findings on leaky coalition trust containment, effect sizes, and statistical significance. | **Slide 12**<br>*(Key Empirical Results)* | **Section VII-A**<br>*(Empirical Findings, Table I)* | `results/phase8_2_summary.csv`<br>`results/phase8_2_statistical_comparison.csv` | Scenario 5: Colluder trust drops from 0.1834 to 0.1068 (41.8% suppression, $p < 10^{-6}, d=2.45$). |
| **12. Critical Analysis: Theoretical Boundaries** | Closed-Set Flow Identity theorem, derivation, 3 structural assumptions, and invariance conditions. | **Slide 13**<br>*(Critical Analysis)* | **Section VIII-A**<br>*(Closed-Set Flow Identity)* | `FINAL_CASE_STUDY_SYNTHESIS_V9.md` (§8.1)<br>`NOVEL_TRUST_ALGORITHM_DESIGN_V1_8.md` | $T_C = \frac{1-\alpha}{\alpha} F_{H \to C}$; assumes closure ($C'_{ch}=0$), $p_c=0$, and no dangling coalition rows. |
| **13. Critical Analysis: Negative Findings** | Empirical refutation of Hypothesis H-1 (receipt grinding) and structural degeneracy of Scenario 7. | **Slide 13**<br>*(Critical Analysis)* | **Section VII-B** *(H-1 Refutation)*<br>**Section VIII-B** *(Scenario 7 Degeneracy)* | `results/phase8_2_summary.csv`<br>`FINAL_SCOPE_AND_CLAIMS_AUDIT_V9.md` (§4) | H-1 refuted: colluders gain +13.38% (std) and +17.92% (ext). S7 zero-trust is due to topological disconnection ($F_{H \to C}=0$). |
| **14. Operational Overhead & Scaling** | Measured CPU and memory runtime scaling bottlenecks under unpruned transaction histories. | **Slide 12**<br>*(Empirical Results)*<br>**Slide 14**<br>*(Limitations)* | **Section VII-C**<br>*(Runtime & Computational Overhead)* | `results/phase8_2_raw_results.json`<br>`FINAL_CASE_STUDY_SYNTHESIS_V9.md` (§7.3) | Normal matrix build: 34.2 ms; extended grinding (152k receipts): 2.76 s (~92x runtime overhead). |
| **15. Conceptual Social-Networking Scope** | Platform-neutral conceptual mapping to decentralized social graphs (Nostr, Matrix); distinction from empirical P2P file sharing. | **Slide 2**<br>*(Intro Scope)*<br>**Slide 14**<br>*(Social Scope)* | **Section X**<br>*(Social-Networking Applicability)* | `FINAL_CASE_STUDY_SYNTHESIS_V9.md` (§10)<br>`FINAL_SCOPE_AND_CLAIMS_AUDIT_V9.md` (§5) | Follows map to WoT edges; attestations map to receipts; social recovery maps to Shamir. No empirical social trials claimed. |
| **16. Limitations & Threats to Validity** | Acknowledged technical limitations: Tier 3 evidence portability gap, static PoW limits, and synthetic simulation scope. | **Slide 14**<br>*(Limitations & Future Work)* | **Section IX**<br>*(Limitations & Threats to Validity)* | `FINAL_SCOPE_AND_CLAIMS_AUDIT_V9.md` (§6)<br>`PHASE8_12_FINAL_PRESENTATION_READINESS_REPORT.md` | Tier 3 simulator key oracle $\mathcal{D}_{\text{sim}}$ upper bound; static PoW ASIC limits; single-node Shamir recovery. |
| **17. Conclusion & Future Directions** | Summary of contributions, zero-knowledge receipt compression, and decentralized threshold consensus. | **Slide 14**<br>*(Conclusion & Future Work)* | **Section XI**<br>*(Conclusion & Future Work)* | `FINAL_CASE_STUDY_SYNTHESIS_V9.md` (§11) | Validates >40% leaky collusion suppression; proposes zk-SNARK receipt compression to eliminate 92x scaling overhead. |
| **18. Authoritative References** | Complete IEEE-formatted bibliography verifying all citations against foundational literature. | **Slide 15**<br>*(References)* | **References [1]–[7]**<br>*(Page 5–6)* | IEEE Standards, RFC 2693 [2], RFC 5280 [7], WWW '03 [3], Bitcoin [4], Shamir [5], Zimmermann [6]. | Exactly 7 verified references matching throughout slides, paper, and defense script. |

---

## 3. Rubric Evaluation Defense Guide

### 3.1 Key Questions Evaluators May Ask & Approved Model Responses

#### Q1: "Why does your title mention social networking if you only ran simulations on P2P file sharing?"
> **Model Response:**  
> "Thank you for that important question. The original case-study scope encompasses decentralized trust management across both transactional file sharing and relational social platforms. However, to maintain strict scientific integrity, we establish a rigorous boundary: the transactional file-sharing protocol—where interactions produce objective binary Merkle proofs—was fully implemented in code and evaluated across 1,140 simulation runs. Decentralized social networking—where interactions represent subjective interpersonal follows—is formulated as a platform-neutral conceptual architectural mapping (Section X of the paper and Slide 14). We explicitly do not claim empirical trials or production deployment on platforms like Nostr or Matrix."

#### Q2: "You report over 40% collusion suppression. Does your algorithm solve collusion in general?"
> **Model Response:**  
> "No, and we are very careful not to make that claim. As proven by our Closed-Set Flow Identity theorem ($T_C = \frac{1-\alpha}{\alpha} F_{H \to C}$), any reputation algorithm based on random walks with restart cannot prevent a closed coalition from circulating trust internally if incoming trust from honest nodes is fixed. The 41.8% suppression we report occurred specifically in Scenario 5—the leaky coalition scenario—where colluding peers interacted with honest peers and failed protocol audits, which severely restricted the incoming trust flow $F_{H \to C}$. In closed collusion rings or receipt-grinding scenarios without external interaction, colluders actually gained trust, leading to the refutation of our preregistered Hypothesis H-1."

#### Q3: "Why did Hypothesis H-1 fail during receipt grinding?"
> **Model Response:**  
> "In our preregistration, we hypothesized that dispute weighting would penalize colluders when they attempted receipt grinding. However, our benchmark data showed colluders gained +13.38% trust in standard grinding and +17.92% in extended grinding. The reason is that colluders exchanged synthetic mutual positive receipts entirely within their own clique without interacting with honest nodes. Because they never triggered chunk delivery failures or Merkle contradiction proofs, the dispute penalty weight ($w_{\text{dispute}} = 5.0$) was never invoked. This negative result proves that dispute weighting alone cannot stop intra-coalition grinding without explicit transaction rate limiting or economic staking."

#### Q4: "Scenario 7 reports exactly 0.0000 colluder trust. Why do you call this degenerate?"
> **Model Response:**  
> "A surface reading of Scenario 7 suggests that our system completely eliminated colluder trust during false slander attacks. However, when we audited the interaction graph and matrix algebra, we discovered that colluders had zero incoming edges from honest nodes ($F_{H \to C} = 0$), zero pre-trusted teleportation mass ($p_c = 0$), and no dangling rows. Because the colluder subgraph was completely disconnected from the honest network, its stationary probability mass collapsed to zero purely as a topological artifact. Presenting this as successful slander mitigation would be scientifically misleading, so we formally classified it as a structurally degenerate result."

#### Q5: "What is the computational complexity of verifying a Merkle proof in your system?"
> **Model Response:**  
> "For a file partitioned into $N$ chunks, verifying a chunk's Merkle inclusion proof requires exactly $O(\log N)$ hash operations and $O(\log N)$ sibling hashes along the audit path $\pi_i$. This allows a downloading peer to verify chunk integrity immediately upon receipt without downloading the entire file payload ($O(N)$). This logarithmic verification is distinct from our Layer 1 Proof-of-Work check, which is an $O(1)$ constant-time single hash evaluation."

---

## 4. Assessment Deliverable Sign-Off

- **Deliverable A (Presentation):** `PKI_Trust_Management_Final_Presentation.pptx` (15 slides, validated).
- **Deliverable B (IEEE Research Paper):** `PKI_Trust_Management_IEEE_Research_Report.docx` & `.md` (Validated).
- **Deliverable C (Presentation Script):** `PKI_Trust_Management_Presentation_Script.docx` & `.md` (15 slides, validated).
- **Deliverable D (Mapping & Checklist):** `PKI_Trust_Management_Assessment_Mapping.md` & `FINAL_DELIVERABLES_CHECKLIST.md` (Validated).

*Prepared for academic submission: October 9, 2026.*
