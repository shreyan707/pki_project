# Final Deliverables & Quality Gate Checklist: PKI Trust Management Case Study

**Candidate:** Shreyan Nayak (Reg. No: `23BKT0039`)  
**Institution:** School of Computer Science and Engineering (SCOPE), Vellore Institute of Technology (VIT), Chennai  
**Course Code:** `VL2026270102689` | **Assessment Task:** Case Study 1 (`CS1`)  
**Project Title:** PKI-Based Trust Management for Peer-to-Peer File-Sharing and Social Networking Platforms  
**Technical Baseline:** `v9.0-FINAL-FREEZE` (October 9, 2026)  

---

## 1. Inventory of Generated Deliverables

The table below lists all required final deliverables generated in the project workspace, including their exact byte sizes, file formats, and computed SHA-256 cryptographic checksums.

| Deliverable Name | File Path | Format | Size (Bytes) | SHA-256 Checksum | Verification Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Deliverable A: Academic Presentation** | `PKI_Trust_Management_Final_Presentation.pptx` | Microsoft PowerPoint (.pptx) | 92,358 | `5ea49bac38586f3349f8d2a1d24097e8c3ef26e9c69e05df7fab67c4624ca91e` | **VERIFIED** (Exactly 15 slides, full speaker notes) |
| **Deliverable B: IEEE Research Paper (Docx)** | `PKI_Trust_Management_IEEE_Research_Report.docx` | Microsoft Word (.docx) | 49,615 | `f5e69d1a2bd50dbdd3c79ef39a34356ca3a5f585461a5fa47aee2ffb6d767308` | **VERIFIED** (IEEE 2-column layout, tables, equations) |
| **Deliverable B: IEEE Research Paper (Source MD)** | `PKI_Trust_Management_IEEE_Research_Report.md` | GitHub Markdown (.md) | 39,444 | `5964455b439b191eb66365f569d1851df0e30c29c9b17be55633c639f4cf6baf` | **VERIFIED** (Complete sections I–XI + references) |
| **Deliverable C: Presentation Script (Docx)** | `PKI_Trust_Management_Presentation_Script.docx` | Microsoft Word (.docx) | 49,871 | `d83409a627b766fa11213ac6f12bbaed6a4cd655e16ec55d96c35fbd9ace649d` | **VERIFIED** (Full script, transitions, Q&A definitions) |
| **Deliverable C: Presentation Script (MD)** | `PKI_Trust_Management_Presentation_Script.md` | GitHub Markdown (.md) | 32,470 | `6aed227c9cbb9b7c64282e5172a84f63d44625916015b68600676c3fc5a1458d` | **VERIFIED** (Formatted speaker script, 15 slides) |
| **Deliverable D: Assessment Mapping** | `PKI_Trust_Management_Assessment_Mapping.md` | GitHub Markdown (.md) | 15,315 | `dec837fd94de8e6bcbe662fd5e25e9b25321b9ccaa7bd044ca1dde9c99bcb4ae` | **VERIFIED** (18 rubric items mapped + Q&A defense) |
| **Deliverable D: Final Checklist** | `FINAL_DELIVERABLES_CHECKLIST.md` | GitHub Markdown (.md) | ~10.9 KB | *Self-referential (Audited in Section 2)* | **VERIFIED** (Complete quality gate checklist) |

---

## 2. Technical Consistency Audit

Every deliverable has been audited against the primary source materials (`FINAL_CASE_STUDY_SYNTHESIS_V9.md`, `FINAL_SCOPE_AND_CLAIMS_AUDIT_V9.md`, `PHASE8_12_FINAL_PRESENTATION_READINESS_REPORT.md`, `PROTOCOL_SPEC.md`, `SECURITY_MODEL.md`, `NOVEL_TRUST_ALGORITHM_DESIGN_V1_8.md`, and raw experiment outputs in `results/`).

### 2.1 Fixed Slide Count Verification
- [x] **Strict 15-Slide Limit:** The presentation contains **exactly 15 slides** (verified programmatically: `len(prs.slides) == 15`).
- [x] **No Appendix Slides:** No additional or hidden slides were introduced.
- [x] **Fixed Structure 1–15 Adherence:**
  1. Title and candidate details
  2. Introduction and background
  3. Problem statement and research objectives
  4. Literature review and research gap
  5. Proposed four-layer architecture
  6. Layer 1 — Identity and Proof-of-Work admission
  7. Layer 2 — Web-of-Trust mesh PKI
  8. Layer 3 — Evidence-Weighted EigenTrust v1.8
  9. Layer 4 — Revocation and key recovery
  10. End-to-end file-sharing workflow and Merkle-based fault attribution
  11. Experimental methodology and benchmark setup
  12. Key empirical results and statistical findings
  13. Critical analysis: closed-set flow identity, H-1 refutation, and Scenario 7 degeneracy
  14. Limitations, conceptual social-networking extension, conclusion, and future work
  15. References
- [x] **Speaker Notes:** Every single slide includes medium-length spoken explanations (114–177 words per slide) populated in `notes_slide.notes_text_frame`.

### 2.2 Mandatory Empirical Findings Audit
- [x] **Leaky Collusion Suppression:** Reported strictly as over 40% suppression (specifically $-41.8\%$, from $0.1834 \pm 0.012$ to $0.1068 \pm 0.009$, $p < 10^{-6}$, Cohen's $d = 2.45$) in the tested leaky-coalition scenario (Scenario 5) only.
- [x] **Preregistered Hypothesis H-1 Refutation:** Explicitly reported across slides, paper, and script that Hypothesis H-1 was refuted by benchmark data. Receipt grinding caused colluders to *gain* trust ($+13.38\%$ in standard grinding, $+17.92\%$ in extended grinding, $p < 0.001$) because intra-coalition synthetic transactions did not trigger disputes.
- [x] **Closed-Set Flow Identity Theorem:** Formulated accurately as $T_C = \frac{1-\alpha}{\alpha} F_{H \to C}$, where $F_{H \to C} = \sum_{h \in H} t_h \sum_{c \in C} C'_{hc}$. All three structural assumptions are stated:
  1. Coalition closure ($C'_{ch} = 0$),
  2. Zero coalition teleportation ($p_c = 0$),
  3. No dangling coalition rows ($\sum_j S_{cj} > 0$).
  Invariance is explicitly conditioned on fixed trust-weighted incoming flow $F_{H \to C}$.
- [x] **Scenario 7 Degeneracy:** Zero colluder trust ($0.0000$) is formally explained as a structural artifact caused by topological disconnection ($F_{H \to C} = 0, p_c = 0$, no dangling rows), not general resistance to false slander accusations.
- [x] **Tier 3 Evidence Portability Gap:** Documented across paper, slides, and script that the evaluated simulator delivery receipts rely on a global key oracle $\mathcal{D}_{\text{sim}}$, forming an upper-bound idealization rather than fully portable external proofs.
- [x] **Runtime Overhead Bottleneck:** Measured runtime scaling reported accurately: normal matrix assembly requires $34.2\text{ ms}$ (~20% overhead over standard EigenTrust's $28.4\text{ ms}$), but jumps to $2.76\text{ s}$ (~92x overhead) under extended grinding (152,000 receipts).
- [x] **Social Networking Scope:** Consistently qualified across all documents as a platform-neutral conceptual architectural extension; no live trials or empirical deployments on Nostr or Matrix are claimed.
- [x] **Merkle Verification Complexity:** Correctly stated as $O(\log N)$ hash operations and $O(\log N)$ sibling hashes for a tree with $N$ leaves, explaining that this avoids downloading the entire payload ($O(N)$). Distinguished from Layer 1 PoW verification, which is $O(1)$.
- [x] **Implementation Claims:** No claims of machine-checked formal verification, security proofs, or production readiness are made; described strictly as a Python prototype validated via automated test suites and simulation benchmarks.

---

## 3. Citation and Bibliography Consistency

The bibliography contains exactly seven foundational peer-reviewed references, cited consistently using IEEE numbered citations `[1]` through `[7]` across the IEEE research paper, presentation slides, speaker script, and assessment mapping:

- **[1] Decentralized Identifiers (DIDs):** DIF / W3C Recommendation, 2022. (Foundational standard for Layer 1 deterministic naming).
- **[2] SPKI Certificate Theory:** C. Ellison et al., IETF RFC 2693, 1999. (Decentralized certificate structure and authorization theory).
- **[3] EigenTrust Algorithm:** S. D. Kamvar, M. T. Schlosser, and H. Garcia-Molina, WWW '03, pp. 640–651, 2003. (Seminal spectral reputation baseline for Layer 3).
- **[4] Bitcoin Proof-of-Work:** S. Nakamoto, White Paper, 2008. (Computational admission friction for Layer 1).
- **[5] Secret Sharing:** A. Shamir, *Communications of the ACM*, vol. 22, no. 11, pp. 612–613, 1979. (Galois Field polynomial threshold sharing for Layer 4).
- **[6] PGP Web-of-Trust:** P. R. Zimmermann, *The Official PGP User's Guide*, MIT Press, 1995. (Decentralized key cross-certification for Layer 2).
- **[7] Internet X.509 PKI & CRL:** D. Cooper et al., IETF RFC 5280, 2008. (Certificate revocation list profiling and comparison baseline).

*Audit finding:* All citations match their corresponding literature, with no fabricated DOIs, authors, or publication venues.

---

## 4. Figures and Tables Requiring Manual Review

Prior to physical projection or final PDF submission, the following visual artifacts should be manually inspected by the candidate:

1. **Table I in IEEE Research Paper (`PKI_Trust_Management_IEEE_Research_Report.docx`):**
   - Verify that column borders, font sizes (8.5 pt), and numerical alignments for Scenarios 1–8 display cleanly within the two-column margins.
2. **Table II in IEEE Research Paper (`PKI_Trust_Management_IEEE_Research_Report.docx`):**
   - Confirm that the four-layer architectural mapping table aligns with section headers IV-A through IV-D.
3. **Slide 10 Diagram (`PKI_Trust_Management_Final_Presentation.pptx`):**
   - Check projection legibility of the 5-step horizontal protocol flow cards (Discovery $\to$ WoT Path $\to$ Manifest $\to$ Chunk Delivery $\to$ Evidence Settlement).
4. **Slide 12 Results Table (`PKI_Trust_Management_Final_Presentation.pptx`):**
   - Verify that the 5-column results table text contrast (Cyan headers on deep navy, emerald green for suppression, rose for colluder gain) is easily readable on university projectors.
5. **Slide 13 Invariance Equations (`PKI_Trust_Management_Final_Presentation.pptx`):**
   - Confirm visual placement of the Closed-Set Flow Identity equation $T_C = \frac{1-\alpha}{\alpha} F_{H \to C}$.

---

## 5. Unresolved Claims and Outstanding Items

- **Unresolved Claims:** **NONE.** All empirical numbers, theoretical claims, and negative findings are fully reconciled with `FINAL_CASE_STUDY_SYNTHESIS_V9.md` and raw data files.
- **Protocol Modifications:** **NONE.** Protocol specifications remain frozen at `v2.2.0-FROZEN`.
- **Parameter Retuning:** **NONE.** Algorithmic parameters remain strictly locked ($\alpha = 0.15, \epsilon = 10^{-6}, w_{\text{pos}} = 1.0, w_{\text{neg}} = 2.0, w_{\text{dispute}} = 5.0, D = 16$).
- **Experiment Reruns:** **NONE.** All reported figures originate from the frozen 1,140 preregistered trials.

---

## 6. Final Quality Gate Certification

The final deliverable generation for the PKI Trust Management Case Study has passed all quality gates. The technical narrative is mathematically sound, empirically grounded, and candidly conservative regarding system boundaries and negative findings.

**Submission Package Status:** **READY FOR INSTITUTIONAL SUBMISSION AND REVIEW DEFENSE.**

*Date of Sign-off:* October 9, 2026  
*Candidate:* Shreyan Nayak (`23BKT0039`)  
*Course:* Information Security / PKI Case Study (`VL2026270102689`, CS1)  
*Institution:* SCOPE, Vellore Institute of Technology (VIT), Chennai  
