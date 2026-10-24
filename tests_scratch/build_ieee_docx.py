import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def create_ieee_docx():
    doc = docx.Document()

    # Page Margins: 0.75 in (IEEE Standard)
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.75)
        section.bottom_margin = Inches(0.75)
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)

    # Base Styles
    styles = doc.styles
    normal_style = styles['Normal']
    normal_font = normal_style.font
    normal_font.name = 'Times New Roman'
    normal_font.size = Pt(10)
    normal_font.color.rgb = RGBColor(30, 41, 59) # Slate 800

    # Helper: Add Title
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_p.paragraph_format.space_before = Pt(0)
    title_p.paragraph_format.space_after = Pt(6)
    title_run = title_p.add_run("PKI-Based Trust Management for Peer-to-Peer File-Sharing and Social Networking Platforms")
    title_run.font.name = 'Times New Roman'
    title_run.font.size = Pt(20)
    title_run.font.bold = True
    title_run.font.color.rgb = RGBColor(15, 23, 42)

    # Helper: Add Author Block
    author_p = doc.add_paragraph()
    author_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    author_p.paragraph_format.space_after = Pt(2)
    author_run = author_p.add_run("Shreyan Nayak (Registration No. 23BKT0039)\n")
    author_run.font.name = 'Times New Roman'
    author_run.font.size = Pt(11)
    author_run.font.bold = True

    affil_run = author_p.add_run("School of Computer Science and Engineering (SCOPE)\nVellore Institute of Technology (VIT), Chennai, Tamil Nadu, India\n")
    affil_run.font.name = 'Times New Roman'
    affil_run.font.size = Pt(9.5)
    affil_run.font.italic = True

    meta_run = author_p.add_run("Course Code: VL2026270102689 | Case Study Assessment CS1 | Project Baseline: v9.0-FINAL-FREEZE | October 9, 2026")
    meta_run.font.name = 'Times New Roman'
    meta_run.font.size = Pt(8.5)
    meta_run.font.color.rgb = RGBColor(100, 116, 139)

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # Helper: Abstract & Index Terms
    abs_p = doc.add_paragraph()
    abs_p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    abs_p.paragraph_format.left_indent = Inches(0.25)
    abs_p.paragraph_format.right_indent = Inches(0.25)
    abs_p.paragraph_format.space_after = Pt(4)

    abs_label = abs_p.add_run("Abstract— ")
    abs_label.font.name = 'Times New Roman'
    abs_label.font.size = Pt(9)
    abs_label.font.bold = True

    abs_text = abs_p.add_run(
        "Decentralized peer-to-peer (P2P) systems operating in the absence of centralized Certificate Authorities (CAs) face fundamental vulnerabilities to identity spoofing, Sybil multiplication, free-riding, strategic collusion, and malicious content distribution. While classical Public Key Infrastructure (PKI) enforces strict cryptographic identity bindings, its conventional hierarchical trust model introduces single points of failure and censorship vulnerabilities. Conversely, classical distributed reputation algorithms like EigenTrust compute global spectral trust vectors but assume unauthenticated feedback, leaving them exposed to feedback forgery, receipt grinding, and identity whitewashing. This paper presents a vertically integrated four-layer decentralized PKI trust management architecture designed for P2P file sharing and architecturally mapped to decentralized social networking. The system integrates: (1) self-certifying did:peer-style cryptographic identities with verifiable Hashcash proof-of-work (PoW) admission barriers; (2) a dynamic Web-of-Trust mesh PKI utilizing bounded vertex-disjoint path discovery up to four hops; (3) Evidence-Weighted EigenTrust (EW-EigenTrust v1.8), featuring three-tier cryptographic delivery verification, concave edge ceilings, exponential freshness decay, and dispute accounting; and (4) an m-of-n supernode threshold certificate revocation mechanism (3-of-5) combined with Shamir (3, 5) secret-shared master identity recovery. The reference implementation was evaluated across 1,140 paired benchmark trials spanning 20 random seeds and two network scales. Empirical findings reveal that while asymmetric evidence discounting suppresses colluder trust by 40.88% to 41.50% (p < 10^-18) in leaky topologies where colluders interact with honest peers, internal edge ceilings fail to suppress closed colluding coalitions. Aggregate closed-coalition trust is dictated by external incoming flow in accordance with the derived Closed-Set Flow Identity (T_C = ((1 - a) / a) * F_{H -> C}), formally refuting preregistered Hypothesis H-1 under receipt grinding. Furthermore, Merkle-based fault contradiction proofs enable efficient O(log N) arbiter verification of corrupted chunk deliveries without transferring full file payloads. We establish the evidentiary boundaries between empirical file-sharing validation, simulator oracle dependencies, and conceptual social-networking extensions."
    )
    abs_text.font.name = 'Times New Roman'
    abs_text.font.size = Pt(9)
    abs_text.font.italic = True

    idx_p = doc.add_paragraph()
    idx_p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    idx_p.paragraph_format.left_indent = Inches(0.25)
    idx_p.paragraph_format.right_indent = Inches(0.25)
    idx_p.paragraph_format.space_after = Pt(12)

    idx_label = idx_p.add_run("Index Terms— ")
    idx_label.font.name = 'Times New Roman'
    idx_label.font.size = Pt(9)
    idx_label.font.bold = True

    idx_text = idx_p.add_run("Decentralized Public Key Infrastructure, Web-of-Trust, EigenTrust, Peer-to-Peer File Sharing, Proof-of-Work, Threshold Cryptography, Merkle Inclusion Proofs, Collusion Resistance, Social Networking.")
    idx_text.font.name = 'Times New Roman'
    idx_text.font.size = Pt(9)
    idx_text.font.italic = True

    # Section Formatter
    def add_section_header(title):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(title.upper())
        run.font.name = 'Times New Roman'
        run.font.size = Pt(11)
        run.font.bold = True
        run.font.color.rgb = RGBColor(15, 23, 42)

    def add_subsection_header(title):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(title)
        run.font.name = 'Times New Roman'
        run.font.size = Pt(10)
        run.font.bold = True
        run.font.italic = True
        run.font.color.rgb = RGBColor(30, 41, 59)

    def add_body_paragraph(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.line_spacing = 1.15
        run = p.add_run(text)
        run.font.name = 'Times New Roman'
        run.font.size = Pt(10)

    def add_equation_box(eq_text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.left_indent = Inches(0.5)
        p.paragraph_format.right_indent = Inches(0.5)
        run = p.add_run(eq_text)
        run.font.name = 'Cambria Math'
        run.font.size = Pt(10)
        run.font.bold = True
        run.font.color.rgb = RGBColor(15, 23, 42)

    # I. INTRODUCTION
    add_section_header("I. Introduction")
    add_body_paragraph(
        "Decentralized peer-to-peer (P2P) file-sharing networks (e.g., BitTorrent, IPFS) and distributed social networking platforms (e.g., Nostr, Matrix, Mastodon) operate without central intermediaries. While eliminating centralized gatekeepers confers resilience against single points of failure, structural bottlenecking, and administrative censorship, it simultaneously deprives participants of authoritative identity verification and accountability. In open distributed networks, peers encounter unauthenticated participants under severe information asymmetry, exposing systems to identity spoofing, Sybil attacks, free-riding, malicious data poisoning, and strategic reputation inflation [1], [3]."
    )
    add_body_paragraph(
        "In classical client-server and enterprise environments, Public Key Infrastructure (PKI) resolves identity authenticity through hierarchical Certificate Authorities (CAs). A relying party verifies arbitrary certificates by validating signature chains rooted in a trusted anchor. In decentralized networks, however, reliance on centralized CAs reintroduces single points of failure, single points of legal compromise, and administrative chokepoints that contradict decentralized fault tolerance. Conversely, distributed reputation management protocols—most notably the seminal EigenTrust algorithm [3]—aggregate local satisfaction ratings into global trust distributions via spectral power iteration. However, classical EigenTrust assumes honest rating submission and authentic transaction accounting. Without an underlying cryptographic identity layer, malicious peers can mass-produce zero-cost pseudonyms (Sybil attacks), fabricate unauthenticated transaction feedback, and execute receipt grinding to dominate spectral trust distributions [1], [3]."
    )
    add_body_paragraph(
        "To resolve this architectural tension, this paper presents a unified, vertically integrated four-layer decentralized PKI trust framework. The primary research question investigated is: How can cryptographic identity assurance and distributed reputation management be synthesized into a decentralized architecture that bounds Sybil creation, authenticates transactions, suppresses collusion, and manages certificate lifecycles without centralized authorities?"
    )
    add_body_paragraph(
        "This paper presents the formal specification, mathematical derivation, software implementation, and empirical benchmark evaluation of this architecture across 1,140 paired trials. Crucially, the paper establishes complete fidelity to scientific findings: documenting the formal refutation of preregistered Hypothesis H-1 under receipt grinding, deriving the Closed-Set Flow Identity, diagnosing the structural degeneracy of Scenario 7, and distinguishing implemented P2P file sharing from conceptual social-networking extensions."
    )

    # II. BACKGROUND AND RELATED WORK
    add_section_header("II. Background and Related Work")
    add_subsection_header("A. Decentralized Identity and Sybil Resistance")
    add_body_paragraph(
        "Self-certifying cryptographic identifiers derive an entity's network address directly from its public key, eliminating central registries. The Decentralized Identity Foundation (DIF) and W3C have standardized Decentralized Identifiers (DIDs) [2], [6]. In permissionless networks, however, public keys can be generated at negligible computational cost, enabling Sybil attacks wherein an adversary creates vast clusters of fake identities to compromise voting or reputation pools. To impose an economic admission barrier, Hashcash proof-of-work (PoW) [1] mandates that peers compute a cryptographic preimage whose hash satisfies a difficulty target d: H(DID || nonce) < 2^(256 - d). Verifying this proof is O(1) (a single SHA-256 block compression), while generating it requires an expected O(2^d) hash trials, eliminating zero-cost identity generation."
    )
    add_subsection_header("B. Web-of-Trust and Mesh PKI")
    add_body_paragraph(
        "Pioneered by Zimmermann in PGP [7], the Web-of-Trust (WoT) replaces hierarchical roots with peer-to-peer cross-certification. Peer A signs a statement attesting to the binding between peer B's public key and identity alias. In mesh topologies, verifying trust between strangers requires discovering multi-hop certificate chains. However, unconstrained transitive chaining permits distant, untrusted intermediaries to introduce malicious certifications. Foundational work by Maurer and Reiter established that transitive trust propagation requires bounded path lengths and disjoint paths to resist adversarial bridge insertion."
    )
    add_subsection_header("C. Spectral Reputation and EigenTrust")
    add_body_paragraph(
        "The EigenTrust algorithm developed by Kamvar, Schlosser, and Garcia-Molina [3] computes global trust by modeling peer interactions as a discrete-time Markov chain. Given local normalized satisfaction matrix C where C_ij = max(S_ij, 0) / sum_k max(S_ik, 0), global trust vector t (sum t_i = 1) satisfies stationary power iteration: t = (1 - a) * C^T * t + a * p, where a in (0, 1) is a restart probability and p is a pre-trusted peer distribution (p_s = 1 / |S| for pre-trusted seeds S). While EigenTrust dampens isolated malicious nodes, strategic colluders who exchange high-volume positive ratings among themselves while obtaining external bridge edges can extract substantial global trust share."
    )
    add_subsection_header("D. Cryptographic Fault Attribution and Merkle Trees")
    add_body_paragraph(
        "In content distribution, validating data authenticity without full file re-downloads relies on Merkle hash trees [4]. A file of N chunks is committed to a single 32-byte root hash. Downloaders verify chunk k by recomputing the root hash along a path of ceil(log2 N) sibling digests. Attributing delivery fraud requires binding the delivered chunk to a server-signed envelope that contradicts the published root."
    )
    add_subsection_header("E. Threshold Key Recovery and Revocation")
    add_body_paragraph(
        "In CA-based PKI, revocation relies on centralized Certificate Revocation Lists (CRLs) or Online Certificate Status Protocol (OCSP) responders. In decentralized networks, revoking compromised keys requires distributed threshold signatures. Shamir's (k, n) secret sharing [5] over GF(256) enables a private seed to be split into n shares such that any k shares reconstruct the secret, enabling social or guardian-based identity recovery without a central custodian."
    )

    # III. PROBLEM FORMULATION AND THREAT MODEL
    add_section_header("III. Problem Formulation and Threat Model")
    add_subsection_header("A. System Model")
    add_body_paragraph(
        "The network consists of a dynamic set of peers V = H U C, partitioned into honest peers H (including pre-trusted supernodes S subset H) and adversarial peers C, such that H intersection C = empty set. Peers communicate over an asynchronous P2P overlay network. Content is partitioned into fixed-size chunks addressed by binary Merkle trees."
    )
    add_subsection_header("B. Adversarial Threat Model")
    add_body_paragraph(
        "We consider an active, computationally bounded adversary controlling coalition C capable of coordinating malicious strategies: (1) Sybil attacks attempting to generate arbitrary identities; (2) strategic collusion rings exchanging synthetic ratings; (3) receipt grinding generating massive synthetic transaction volumes; (4) chunk poisoning serving corrupted data while filing fabricated slander complaints; and (5) key compromise or eclipse attacks attempting to isolate honest nodes."
    )
    add_subsection_header("C. Security Objectives")
    add_body_paragraph(
        "The architecture enforces five formal security objectives: (1) Sybil cost barrier imposing O(2^d) expected computational cost; (2) non-repudiable fault attribution verifying in O(log N) hash operations; (3) leaky collusion suppression >= 30% against colluders interacting with honest peers; (4) asymmetric provider preservation ensuring dedicated uploaders retain global trust without reciprocal downloads; and (5) safe threshold revocation requiring m-of-n supernode authorization (3-of-5)."
    )

    # IV. PROPOSED FOUR-LAYER ARCHITECTURE
    add_section_header("IV. Proposed Four-Layer Architecture")
    add_body_paragraph(
        "The system operates across four vertically integrated layers: Layer 1 (Identity & PoW Admission Barrier), Layer 2 (Mesh Web-of-Trust PKI), Layer 3 (Evidence-Weighted EigenTrust v1.8), and Layer 4 (Threshold Revocation & Secret-Shared Recovery)."
    )
    add_subsection_header("A. Layer 1: Cryptographic Identity & Lifecycle FSM")
    add_body_paragraph(
        "Peers generate Ed25519 signing keypairs. Identifier strings are formatted as did:peer:2.Ez{public_key_hex}. Node admission requires computing a SHA-256 Hashcash nonce satisfying difficulty d >= 8 (verification is O(1)). Peers follow a strict five-state finite state machine (FSM): UNKNOWN -> ACTIVE <-> SUSPECTED -> REVOCATION_PROPOSED -> REVOKED. Quorum timeout fallback on voting reverts state to SUSPECTED, never directly to ACTIVE."
    )
    add_subsection_header("B. Layer 2: Mesh Web-of-Trust PKI")
    add_body_paragraph(
        "Peers issue signed CrossCertificate records asserting unidirectional trust with valid time windows [t_valid, t_expires]. Multi-hop trust paths are discovered via DFS with a strict hop cutoff k <= 4. Paths are filtered to enforce strict intermediate-vertex disjointness (no intermediate peer appears in more than one evaluated path). Cumulative path trust is the direct multiplicative product of cross-certificate weights."
    )
    add_subsection_header("C. Layer 3: Evidence-Weighted EigenTrust v1.8")
    add_body_paragraph(
        "Layer 3 replaces raw linear rating summation with evidence discounting: (1) Three-tier evidence weighting: Tier 1 unindexed bilateral receipts (mu = 0.10), Tier 2 manifest-referenced receipts (mu = 0.25), and Tier 3 locally verified chunk deliveries (gamma = 1.00); (2) Exponential freshness decay: gamma_time = exp(-Delta t / tau) with tau = 24 hours; (3) Dispute ratio accounting: gamma_dispute = max(0.0, 1.0 - 2 * N_neg / (N_pos + 1.0)); (4) Concave edge ceiling capping effective edge weight: Phi_edge(E) = K_max * tanh(lambda * E / K_max) with K_max = 10.0, lambda = 0.50; and (5) Dangling-node fallback setting dangling rows to the pre-trusted restart vector p (C'_i,: = p)."
    )
    add_subsection_header("D. Layer 4: Threshold Revocation & Key Recovery")
    add_body_paragraph(
        "Malicious or compromised peers are revoked via Certificate Revocation Records (CRRs) requiring m-of-n supernode quorum signatures (3-of-5). A 3-of-5 threshold signature mechanism enforces administrative multi-party authorization; it does not constitute Byzantine fault-tolerant consensus. Master identity keys are protected via Shamir (3, 5) secret sharing over GF(256). Reconstruction requires 3 guardian Recovery Authorization Tokens (AuthTok) and triggers mandatory post-recovery key rotation."
    )

    # V. IMPLEMENTATION AND PROTOCOL WORKFLOW
    add_section_header("V. Implementation and Protocol Workflow")
    add_subsection_header("A. File-Sharing Transaction Lifecycle")
    add_body_paragraph(
        "Content distribution follows a 4-stage pipeline: (1) Publisher builds binary Merkle tree over chunk digests and signs ContentManifest; (2) Downloader issues signed ContentRequest; Uploader serves ChunkResponse containing chunk index k, chunk digest, and server Ed25519 signature; (3) Downloader validates chunk integrity against manifest root in O(log N) hash operations; (4) Upon validation, peers exchange co-signed BilateralReceipt records carrying tx_id, chunk_index, and merkle_root."
    )
    add_subsection_header("B. Attributable Fault Contradiction Protocol")
    add_body_paragraph(
        "If an uploader serves corrupted chunk bytes c'_k: (1) Downloader detects hash mismatch against published root; (2) Downloader compiles FaultEvidenceRecord containing publisher manifest, server-signed ChunkResponse committing to c'_k, and authentic Merkle leaf inclusion proof for chunk k; (3) Any third-party arbiter verifies this contradiction in O(log N) hash operations and sibling hashes, proving attributable delivery inconsistency without downloading the full O(N) file payload. Certified fault evidence zeroes incoming edge weights to the accused peer (A_{i, accused} = 0.0)."
    )

    # VI. EXPERIMENTAL METHODOLOGY
    add_section_header("VI. Experimental Methodology")
    add_body_paragraph(
        "The empirical benchmark suite (experiments/phase8_2_benchmark.py) was executed in accordance with a sealed preregistration (PHASE8_2_PREREGISTRATION.md): 20 random seeds (S = {42 + 17*i | i in [0, 19]}), 2 network scales (Standard: 30 nodes; Extended: 50 nodes), and 3 trust modes (Vanilla EigenTrust, EW-EigenTrust v1.8, Local-Only Baseline), totaling 1,140 trial evaluations across 9 scenarios (S1 Honest Baseline, S2 Closed Collusion, S3 Leaky Collusion, S4 Bridge Sweep q in {0.00, 0.05, 0.10, 0.20, 0.40}, S5 Adaptive Attacker, S6 Receipt Grinding, S7 Dispute Manipulation, S8 Asymmetric Uploader, S9 Reciprocal Community)."
    )

    # VII. RESULTS AND STATISTICAL ANALYSIS
    add_section_header("VII. Results and Statistical Analysis")
    add_body_paragraph(
        "Table I summarizes the empirical findings across all 19 scenario-scale pairs. All reported p-values are paired Student's t-test values uncorrected for multiple testing across the 9 scenarios, as preregistered."
    )

    # Table I: Master Empirical Results
    table_data = [
        ["Scenario & Metric", "Scale", "Vanilla", "EW v1.8", "Diff (Delta)", "Rel %", "Paired t-stat", "p-value", "Cohen dz"],
        ["S1: Honest Baseline (T_C)", "Standard", "0.0000", "0.0000", "0.0000", "0.00%", "Undefined", "Undefined", "Undefined"],
        ["S1: Honest Baseline (T_C)", "Extended", "0.0000", "0.0000", "0.0000", "0.00%", "Undefined", "Undefined", "Undefined"],
        ["S2: Closed Collusion (T_C)", "Standard", "0.0850", "0.0889", "+0.0039", "+4.53%", "+1.472", "0.158", "+0.33"],
        ["S2: Closed Collusion (T_C)", "Extended", "0.0539", "0.0611", "+0.0073", "+13.50%", "+3.944", "8.70e-4", "+0.88"],
        ["S3: Leaky Collusion (T_C)", "Standard", "0.1834", "0.1084", "-0.0750", "-40.88%", "-34.354", "1.44e-18", "-7.68"],
        ["S3: Leaky Collusion (T_C)", "Extended", "0.1982", "0.1160", "-0.0823", "-41.50%", "-50.410", "1.07e-21", "-11.27"],
        ["S4: Connected q=0.00 (T_C)", "Standard", "0.0000", "0.0000", "0.0000", "0.00%", "Undefined", "Undefined", "Undefined"],
        ["S4: Connected q=0.05 (T_C)", "Standard", "0.0935", "0.1176", "+0.0242", "+25.89%", "+11.757", "3.66e-10", "+2.63"],
        ["S4: Connected q=0.10 (T_C)", "Standard", "0.1606", "0.1885", "+0.0279", "+17.34%", "+13.621", "2.96e-11", "+3.05"],
        ["S4: Connected q=0.20 (T_C)", "Standard", "0.2731", "0.2920", "+0.0189", "+6.92%", "+9.209", "1.95e-8", "+2.06"],
        ["S4: Connected q=0.40 (T_C)", "Standard", "0.4124", "0.4045", "-0.0079", "-1.90%", "-4.799", "1.25e-4", "-1.07"],
        ["S5: Adaptive Attacker (T_C)", "Standard", "0.0964", "0.1004", "+0.0040", "+4.16%", "+1.739", "0.098", "+0.39"],
        ["S6: Receipt Grinding (T_C)", "Standard", "0.0922", "0.1046", "+0.0123", "+13.38%", "+3.860", "1.06e-3", "+0.86"],
        ["S6: Receipt Grinding (T_C)", "Extended", "0.0558", "0.0658", "+0.0100", "+17.92%", "+4.968", "8.55e-5", "+1.11"],
        ["S7: Dispute Manip (T_C)", "Standard", "0.0000", "0.0000", "0.0000", "0.00%", "Undefined", "Undefined", "Undefined"],
        ["S8: Asym Uploader (t_up)", "Standard", "0.1574", "0.1754", "+0.0180", "+11.43%", "+54.177", "2.74e-22", "+12.11"],
        ["S8: Asym Uploader (t_up)", "Extended", "0.1584", "0.1786", "+0.0202", "+12.74%", "+73.490", "8.57e-25", "+16.43"],
        ["S9: Reciprocal Comm (T_C)", "Standard", "0.0000", "0.0000", "0.0000", "0.00%", "Undefined", "Undefined", "Undefined"],
        ["S9: Reciprocal Comm (T_C)", "Extended", "0.0000", "0.0000", "0.0000", "0.00%", "Undefined", "Undefined", "Undefined"]
    ]

    table = doc.add_table(rows=len(table_data), cols=9)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for r_idx, row in enumerate(table_data):
        for c_idx, val in enumerate(row):
            cell = table.cell(r_idx, c_idx)
            cell.text = val
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            set_cell_margins(cell, top=60, bottom=60, left=80, right=80)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c_idx > 0 else WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            run = p.runs[0]
            run.font.name = 'Times New Roman'
            if r_idx == 0:
                set_cell_background(cell, "0F172A")
                run.font.size = Pt(8.5)
                run.font.bold = True
                run.font.color.rgb = RGBColor(255, 255, 255)
            else:
                run.font.size = Pt(8)
                if r_idx % 2 == 1:
                    set_cell_background(cell, "F8FAFC")
                else:
                    set_cell_background(cell, "FFFFFF")
                if "S3" in row[0] or "S6" in row[0] or "S8" in row[0]:
                    run.font.bold = True

    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # VIII. DISCUSSION AND CRITICAL ANALYSIS
    add_section_header("VIII. Discussion and Critical Analysis")
    add_subsection_header("A. Derivation of the Closed-Set Flow Identity")
    add_body_paragraph(
        "To rigorously explain why edge ceilings fail to reduce colluder trust in closed topologies, we derive the stationary trust distribution from first principles. Let V = H U C partitioned into honest nodes H and colluders C. Let C' in R^(n x n) denote the row-stochastic normalized transition matrix (sum_j C'_ij = 1). The stationary trust vector satisfies t = (1 - a) * C'^T * t + a * p. Component-wise for node j: t_j = (1 - a) * sum_{i in V} C'_ij * t_i + a * p_j. Summing over all colluders c in C: sum_{c in C} t_c = (1 - a) * sum_{c in C} sum_{i in V} C'_ic * t_i + a * sum_{c in C} p_c. Splitting the summation over i into honest nodes h in H and colluders c' in C: sum_{c in C} t_c = (1 - a) * [sum_{c in C} sum_{h in H} C'_hc * t_h + sum_{c in C} sum_{c' in C} C'_{c' c} * t_{c'}] + a * sum_{c in C} p_c. Interchanging summation order in the internal term yields: sum_{c' in C} t_{c'} * (sum_{c in C} C'_{c' c})."
    )
    add_body_paragraph(
        "We impose three structural assumptions: (1) Strict Coalition Closure: colluders assign zero outgoing trust to honest peers (forall c' in C, h in H: C'_{c' h} = 0); (2) Zero Coalition Teleportation: pre-trust is concentrated exclusively on honest supernodes (sum_{c in C} p_c = 0); and (3) No Dangling Coalition Rows: internal unnormalized row sums are positive (sum_{c in C} A_{c' c} > 0), ensuring sum_{c in C} C'_{c' c} = 1.0. (Crucial Note: The implemented engine fallback sets dangling rows to p; because p is supported only on honest supernodes, a dangling colluder row sends probability mass to honest peers, breaking closure. Strict closure requires that no coalition row dangles)."
    )
    add_body_paragraph(
        "Substituting these conditions: sum_{c in C} t_c = (1 - a) * [sum_{h in H} t_h * sum_{c in C} C'_hc + sum_{c in C} t_c]. Subtracting (1 - a) * sum_{c in C} t_c from both sides yields: a * sum_{c in C} t_c = (1 - a) * sum_{h in H} t_h * sum_{c in C} C'_hc. Dividing by a establishes the Closed-Set Flow Identity:"
    )
    add_equation_box("T_C = sum_{c in C} t_c = ((1 - a) / a) * F_{H -> C}")
    add_body_paragraph(
        "where F_{H -> C} = sum_{h in H} t_h * sum_{c in C} C'_hc is the trust-weighted incoming flow. Crucially, the flow identity proves that total coalition trust depends strictly on incoming flow. For coalition trust to remain invariant under algorithmic alterations, incoming flow F_{H -> C} must remain constant. Because C'_hc = A_hc / sum_k A_hk, if honest bridge nodes saturate internal honest edges, the denominator changes, altering C'_hc. Furthermore, shifts in honest trust t_H alter F_{H -> C}. This explains why EW-EigenTrust exhibited statistically significant increases in S2 Extended (+13.50%), S4 (q <= 0.20), and S6 (+13.38% to +17.92%). Preregistered Hypothesis H-1 was formally refuted."
    )
    add_subsection_header("B. Diagnosis of Scenario 7 Degeneracy")
    add_body_paragraph(
        "In Scenario 7, colluder trust share was identically 0.0000 across all seeds. Root Cause: In benchmark execution (experiments/phase8_2_benchmark.py:723-744), honest peers selected partners strictly within their own pool (hn + sn). Honest nodes never transacted with or rated colluders (C'_hc = 0). Colluders had zero pre-trust (p_c = 0) and exchanged mutual ratings, meaning no dangling fallback occurred. Under these conditions, the non-homogeneous source term entering the coalition was identically zero: [I - (1 - a) * (C'_CC)^T] * t_C = 0, uniquely forcing t_C = 0. Zero colluder trust is a structurally degenerate artifact of topological disconnection, not proof of active dispute resistance."
    )

    # IX. LIMITATIONS AND THREATS TO VALIDITY
    add_section_header("IX. Limitations and Threats to Validity")
    add_body_paragraph(
        "1. Closed-Set Flow Vulnerability: EW-EigenTrust cannot suppress closed collusive clusters that obtain honest incoming bridge edges under low-to-moderate connectivity (q <= 0.20).\n"
        "2. Decentralized Evidence Portability Gap: In simulation, Tier 3 delivery verification relies on a global delivery key pool (D_sim). In decentralized networks, bilateral receipts do not carry raw chunks or Merkle proofs off-the-wire; third-party verification defaults to Tier 1/2 unless zero-knowledge delivery proofs or interactive challenges are deployed.\n"
        "3. Computational Runtime Overhead: Linear iteration over large evidence journals increased execution time from 1.81 ms (Vanilla) to 166.32 ms (92x overhead) in Scenario 6 extended scale (152,000 receipts). Production implementations require incremental matrix indexing.\n"
        "4. Network Scale Bounds: Empirical benchmarks were bounded to 20–50 simulated nodes; asymptotic behavior across thousands of dynamic peers remains unvalidated.\n"
        "5. No Production Claims: The reference codebase is an in-memory discrete-event simulation harness. It is not claimed to be formally verified or production-ready."
    )

    # X. SOCIAL-NETWORKING APPLICABILITY
    add_section_header("X. Social-Networking Applicability (Conceptual Extension)")
    add_body_paragraph(
        "While empirically validated on P2P file sharing, the four-layer architecture provides a conceptual mapping to decentralized social networks (e.g., Nostr, Scuttlebutt): (1) Identity: user profiles anchored in did:peer-style keys with PoW bot throttling; (2) WoT: peer key-signing establishing bounded follow-graph trust; (3) Reputation: signed post attestations with dispute spam damping; and (4) Revocation: social guardian secret recovery with key rotation."
    )
    add_body_paragraph(
        "Primitive Differentiation: A PKI cross-certificate is a signed Layer 2 cryptographic delegation statement binding a public key to an identity subject within a bounded validity window ([t_valid, t_expires]). In contrast, a social follow expresses a social subscription relationship whose authentication, signature, and integrity properties depend on the platform protocol (e.g., Nostr signed contact lists vs. application-level pointers). A follow establishes subscription interest, not cryptographic key ownership. A social endorsement is a subjective Layer 3 reputation assertion regarding social conduct. Scope Boundary: No custom social network simulator or user-feed dataset was evaluated; social networking applicability is strictly formulated as a theoretical architectural extension."
    )

    # XI. CONCLUSION AND FUTURE WORK
    add_section_header("XI. Conclusion and Future Work")
    add_body_paragraph(
        "This paper presented a four-layer decentralized PKI trust management architecture synthesizing self-certifying cryptographic identities, Web-of-Trust mesh PKI, Evidence-Weighted EigenTrust v1.8, and threshold certificate revocation. Empirical benchmarks across 1,140 trial runs demonstrated that while evidence weighting slashes leaky collusion by >40% (p < 10^-18) and preserves honest asymmetric uploaders (+11% to +13%), internal edge ceilings cannot suppress closed coalitions, in accordance with the Closed-Set Flow Identity (T_C = ((1 - a) / a) * F_{H -> C}). Preregistered Hypothesis H-1 was formally refuted under receipt grinding, and Scenario 7 was diagnosed as structurally degenerate. Future research will focus on spectral bridge-cut partitioning to discount incoming bridge edges dynamically, zero-knowledge delivery proofs to bridge the decentralized portability gap, and empirical evaluation on empirical social network graphs."
    )

    # REFERENCES
    add_section_header("References")
    references = [
        "[1] A. Back, \"Hashcash - A Denial of Service Counter-Measure,\" Technical Report, hashcash.org, 2002. [Online]. Available: http://www.hashcash.org/papers/hashcash.pdf",
        "[2] D. Hardman, S. Curran, and S. Curren, Eds., \"Peer DID Method Specification,\" Decentralized Identity Foundation (DIF) Community Specification Draft, 2021. [Online]. Available: https://identity.foundation/peer-did-method-spec/",
        "[3] S. D. Kamvar, M. T. Schlosser, and H. Garcia-Molina, \"The EigenTrust algorithm for reputation management in P2P networks,\" in Proc. 12th Int. Conf. World Wide Web (WWW '03), Budapest, Hungary, 2003, pp. 640–651. DOI: 10.1145/775152.775242.",
        "[4] R. C. Merkle, \"Protocols for public key cryptosystems,\" in Proc. 1980 IEEE Symp. Security and Privacy, Oakland, CA, USA, 1980, pp. 122–134. DOI: 10.1109/SP.1980.10006.",
        "[5] A. Shamir, \"How to share a secret,\" Commun. ACM, vol. 22, no. 11, pp. 612–613, Nov. 1979. DOI: 10.1145/359168.359176.",
        "[6] W3C Decentralized Identifier Working Group, \"Decentralized Identifiers (DIDs) v1.0: Core Architecture, Data Model, and Representations,\" W3C Recommendation, July 2022. [Online]. Available: https://www.w3.org/TR/did-core/",
        "[7] P. Zimmermann, The Official PGP User's Guide, Cambridge, MA, USA: MIT Press, 1995. ISBN: 978-0262740173."
    ]
    for ref in references:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.left_indent = Inches(0.25)
        p.paragraph_format.first_line_indent = Inches(-0.25)
        run = p.add_run(ref)
        run.font.name = 'Times New Roman'
        run.font.size = Pt(8.5)

    output_path = "deliverable_reports/PKI_Trust_Management_IEEE_Research_Report.docx"
    doc.save(output_path)
    print(f"Successfully generated {output_path} (Size: {os.path.getsize(output_path)} bytes)")

if __name__ == "__main__":
    create_ieee_docx()
