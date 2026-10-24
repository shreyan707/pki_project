import os
import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

def build_presentation():
    prs = pptx.Presentation()
    prs.slide_width = Inches(13.333) # 16:9 widescreen
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # Theme Palette (Academic Dark Theme)
    C_BG_DARK = RGBColor(11, 17, 32)        # Deep Navy #0B1120
    C_BG_CARD = RGBColor(30, 41, 59)        # Slate Card #1E293B
    C_BG_CARD_LIGHT = RGBColor(40, 53, 76)  # Elevated Slate #28354C
    C_BORDER_CARD = RGBColor(51, 65, 85)    # Border Slate #334155
    C_TEXT_WHITE = RGBColor(248, 250, 252)  # White #F8FAFC
    C_TEXT_MUTED = RGBColor(148, 163, 184)  # Slate 400 #94A3B8
    C_TEXT_SUBTLE = RGBColor(100, 116, 139) # Slate 500 #64748B
    C_ACCENT_CYAN = RGBColor(56, 189, 248)  # Cyan #38BDF8
    C_ACCENT_BLUE = RGBColor(37, 99, 235)   # Royal Blue #2563EB
    C_ACCENT_EMERALD = RGBColor(16, 185, 129)# Emerald #10B981
    C_ACCENT_AMBER = RGBColor(245, 158, 11) # Amber #F59E0B
    C_ACCENT_ROSE = RGBColor(244, 63, 94)   # Rose #F43F5E

    def set_slide_background(slide):
        background = slide.background
        fill = background.fill
        fill.solid()
        fill.fore_color.rgb = C_BG_DARK

    def add_header(slide, title, category="PKI-BASED TRUST MANAGEMENT FOR P2P & SOCIAL NETWORKS", slide_num=None):
        set_slide_background(slide)
        
        # Category Tag
        cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.733), Inches(0.3))
        tf_cat = cat_box.text_frame
        tf_cat.word_wrap = True
        p_cat = tf_cat.paragraphs[0]
        p_cat.text = category.upper()
        p_cat.font.name = 'Segoe UI'
        p_cat.font.size = Pt(9.5)
        p_cat.font.bold = True
        p_cat.font.color.rgb = C_ACCENT_CYAN

        # Title
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.7), Inches(11.733), Inches(0.6))
        tf_t = title_box.text_frame
        tf_t.word_wrap = True
        p_t = tf_t.paragraphs[0]
        p_t.text = title
        p_t.font.name = 'Segoe UI'
        p_t.font.size = Pt(22)
        p_t.font.bold = True
        p_t.font.color.rgb = C_TEXT_WHITE

        # Divider Line
        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.35), Inches(11.733), Inches(0.02))
        line.fill.solid()
        line.fill.fore_color.rgb = C_BORDER_CARD
        line.line.color.rgb = C_BORDER_CARD

        # Footer
        footer_box = slide.shapes.add_textbox(Inches(0.8), Inches(7.0), Inches(11.733), Inches(0.3))
        tf_f = footer_box.text_frame
        p_f = tf_f.paragraphs[0]
        slide_str = f"Slide {slide_num} of 15" if slide_num else ""
        p_f.text = f"Candidate: Shreyan Nayak (23BKT0039)  |  VIT Chennai  |  Course Code: VL2026270102689 (CS1)  |  Baseline: v9.0-FINAL-FREEZE       {slide_str}"
        p_f.font.name = 'Segoe UI'
        p_f.font.size = Pt(8.5)
        p_f.font.color.rgb = C_TEXT_SUBTLE

    def add_card(slide, left, top, width, height, title=None, border_color=C_BORDER_CARD, fill_color=C_BG_CARD):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = fill_color
        card.line.color.rgb = border_color
        card.line.width = Pt(1)

        if title:
            tb = slide.shapes.add_textbox(left + Inches(0.18), top + Inches(0.15), width - Inches(0.36), Inches(0.4))
            tf = tb.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.text = title
            p.font.name = 'Segoe UI'
            p.font.size = Pt(12.5)
            p.font.bold = True
            p.font.color.rgb = C_ACCENT_CYAN
        return card

    def add_speaker_notes(slide, notes_text):
        notes_slide = slide.notes_slide
        tf = notes_slide.notes_text_frame
        tf.text = notes_text

    # ==========================================
    # SLIDE 1: Title and Candidate Details
    # ==========================================
    slide1 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide1)

    dec = slide1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.1), Inches(11.733), Inches(5.3))
    dec.fill.solid()
    dec.fill.fore_color.rgb = C_BG_CARD
    dec.line.color.rgb = C_ACCENT_BLUE
    dec.line.width = Pt(2)

    t_box = slide1.shapes.add_textbox(Inches(1.2), Inches(1.4), Inches(10.9), Inches(2.4))
    tf1 = t_box.text_frame
    tf1.word_wrap = True

    p0 = tf1.paragraphs[0]
    p0.text = "RESEARCH DEFENSE & TECHNICAL CASE STUDY"
    p0.font.name = 'Segoe UI'
    p0.font.size = Pt(11)
    p0.font.bold = True
    p0.font.color.rgb = C_ACCENT_CYAN
    p0.space_after = Pt(8)

    p1 = tf1.add_paragraph()
    p1.text = "PKI-Based Trust Management for Peer-to-Peer File-Sharing and Social Networking Platforms"
    p1.font.name = 'Segoe UI'
    p1.font.size = Pt(23)
    p1.font.bold = True
    p1.font.color.rgb = C_TEXT_WHITE
    p1.space_after = Pt(10)

    p2 = tf1.add_paragraph()
    p2.text = "A Vertically Integrated Four-Layer Architecture Synthesizing Self-Sovereign Identity, Web-of-Trust PKI, Evidence-Weighted Spectral Reputation, and Threshold Governance"
    p2.font.name = 'Segoe UI'
    p2.font.size = Pt(12.5)
    p2.font.color.rgb = C_TEXT_MUTED

    card_auth = slide1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.2), Inches(4.3), Inches(5.3), Inches(1.8))
    card_auth.fill.solid()
    card_auth.fill.fore_color.rgb = RGBColor(15, 23, 42)
    card_auth.line.color.rgb = C_BORDER_CARD
    tb_a = slide1.shapes.add_textbox(Inches(1.4), Inches(4.4), Inches(4.9), Inches(1.6))
    tf_a = tb_a.text_frame
    tf_a.word_wrap = True
    p_a1 = tf_a.paragraphs[0]
    p_a1.text = "CANDIDATE DETAILS"
    p_a1.font.name = 'Segoe UI'
    p_a1.font.size = Pt(10)
    p_a1.font.bold = True
    p_a1.font.color.rgb = C_ACCENT_CYAN
    p_a2 = tf_a.add_paragraph()
    p_a2.text = "Shreyan Nayak (Reg. No: 23BKT0039)\nB.Tech Computer Science & Engineering\nSchool of Computer Science and Engineering (SCOPE)\nVellore Institute of Technology (VIT), Chennai"
    p_a2.font.name = 'Segoe UI'
    p_a2.font.size = Pt(10.5)
    p_a2.font.color.rgb = C_TEXT_WHITE

    card_meta = slide1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(4.3), Inches(5.3), Inches(1.8))
    card_meta.fill.solid()
    card_meta.fill.fore_color.rgb = RGBColor(15, 23, 42)
    card_meta.line.color.rgb = C_BORDER_CARD
    tb_m = slide1.shapes.add_textbox(Inches(7.0), Inches(4.4), Inches(4.9), Inches(1.6))
    tf_m = tb_m.text_frame
    tf_m.word_wrap = True
    p_m1 = tf_m.paragraphs[0]
    p_m1.text = "COURSE & ASSESSMENT"
    p_m1.font.name = 'Segoe UI'
    p_m1.font.size = Pt(10)
    p_m1.font.bold = True
    p_m1.font.color.rgb = C_ACCENT_CYAN
    p_m2 = tf_m.add_paragraph()
    p_m2.text = "Course: Information Security / PKI Case Study (VL2026270102689)\nAssessment Task: Case Study 1 (CS1)\nReview Date: October 9, 2026\nTechnical Baseline: v9.0-FINAL-FREEZE"
    p_m2.font.name = 'Segoe UI'
    p_m2.font.size = Pt(10.5)
    p_m2.font.color.rgb = C_TEXT_WHITE

    add_speaker_notes(
        slide1,
        "Good morning, esteemed evaluators and committee members. I am Shreyan Nayak, registration number 23BKT0039, presenting my final research case study titled: 'PKI-Based Trust Management for Peer-to-Peer File-Sharing and Social Networking Platforms.'\n\n"
        "This project investigates how to bridge the fundamental divide between Public Key Infrastructure and decentralized peer-to-peer systems. In client-server environments, trust is traditionally established by convention through centralized Certificate Authorities. However, decentralized P2P networks require open, censorship-resistant collaboration where central roots of trust cannot exist.\n\n"
        "Over the course of this presentation, I will walk you through our vertically integrated four-layer architecture, explain its cryptographic and mathematical mechanisms, present our preregistered empirical benchmark across 1,140 trial evaluations, and candidly examine both our validated successes—such as over 40% leaky collusion suppression—and our mathematically established theoretical limitations, including the Closed-Set Flow Identity and the refutation of preregistered Hypothesis H-1."
    )

    # ==========================================
    # SLIDE 2: Introduction and Background
    # ==========================================
    slide2 = prs.slides.add_slide(blank_layout)
    add_header(slide2, "Introduction: The Decentralized Trust Dilemma", slide_num=2)

    add_card(slide2, Inches(0.8), Inches(1.6), Inches(3.7), Inches(5.1), title="The Centralized PKI Dilemma")
    tb = slide2.shapes.add_textbox(Inches(0.95), Inches(2.2), Inches(3.4), Inches(4.3))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.paragraphs[0].text = "• Classical PKI relies on centralized Certificate Authorities (CAs) by convention."
    tf.paragraphs[0].font.name = 'Segoe UI'
    tf.paragraphs[0].font.size = Pt(10.5)
    tf.paragraphs[0].font.color.rgb = C_TEXT_WHITE
    tf.paragraphs[0].space_after = Pt(8)
    for b in [
        "• Single Point of Failure: Root CA compromise undermines the entire trust domain.",
        "• Censorship Vulnerability: Central authorities can arbitrarily revoke or withhold credentials.",
        "• Structural Mismatch: Hierarchical tree trust contradicts decentralized P2P topologies [1], [7]."
    ]:
        p = tf.add_paragraph()
        p.text = b
        p.font.name = 'Segoe UI'
        p.font.size = Pt(10.5)
        p.font.color.rgb = C_TEXT_MUTED
        p.space_after = Pt(8)

    add_card(slide2, Inches(4.8), Inches(1.6), Inches(3.7), Inches(5.1), title="Open Network Attack Vectors")
    tb = slide2.shapes.add_textbox(Inches(4.95), Inches(2.2), Inches(3.4), Inches(4.3))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.paragraphs[0].text = "• Zero-Cost Sybil Attacks: Pseudonyms generated freely to manipulate voting quorums."
    tf.paragraphs[0].font.name = 'Segoe UI'
    tf.paragraphs[0].font.size = Pt(10.5)
    tf.paragraphs[0].font.color.rgb = C_TEXT_WHITE
    tf.paragraphs[0].space_after = Pt(8)
    for b in [
        "• Strategic Collusion Rings: Cliques award mutual unearned positive ratings.",
        "• Receipt Grinding: Sybils generate synthetic transaction volumes to harvest reputation.",
        "• Data Poisoning & Slander: Servers serve corrupted chunks; downloaders file false complaints [3], [4]."
    ]:
        p = tf.add_paragraph()
        p.text = b
        p.font.name = 'Segoe UI'
        p.font.size = Pt(10.5)
        p.font.color.rgb = C_TEXT_MUTED
        p.space_after = Pt(8)

    add_card(slide2, Inches(8.8), Inches(1.6), Inches(3.7), Inches(5.1), title="Dual Application Paradigms")
    tb = slide2.shapes.add_textbox(Inches(8.95), Inches(2.2), Inches(3.4), Inches(4.3))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.paragraphs[0].text = "• P2P File Sharing (BitTorrent, IPFS):"
    tf.paragraphs[0].font.name = 'Segoe UI'
    tf.paragraphs[0].font.size = Pt(10.5)
    tf.paragraphs[0].font.bold = True
    tf.paragraphs[0].font.color.rgb = C_ACCENT_EMERALD
    p_f = tf.add_paragraph()
    p_f.text = "Operational & transactional. Governs chunk integrity, content authenticity, seeder reciprocity, and non-repudiation."
    p_f.font.name = 'Segoe UI'
    p_f.font.size = Pt(10)
    p_f.font.color.rgb = C_TEXT_MUTED
    p_f.space_after = Pt(10)

    p_s_t = tf.add_paragraph()
    p_s_t.text = "• Decentralized Social (Nostr, Matrix):"
    p_s_t.font.name = 'Segoe UI'
    p_s_t.font.size = Pt(10.5)
    p_s_t.font.bold = True
    p_s_t.font.color.rgb = C_ACCENT_CYAN
    p_s = tf.add_paragraph()
    p_s.text = "Relational & subjective. Governs follow assertions, message origins, spam mitigation, and guardian recovery."
    p_s.font.name = 'Segoe UI'
    p_s.font.size = Pt(10)
    p_s.font.color.rgb = C_TEXT_MUTED
    p_s.space_after = Pt(10)

    p_note = tf.add_paragraph()
    p_note.text = "Scope Boundary: File sharing is empirically evaluated (1,140 trials); social networking is conceptually formulated."
    p_note.font.name = 'Segoe UI'
    p_note.font.size = Pt(9.5)
    p_note.font.italic = True
    p_note.font.color.rgb = C_ACCENT_AMBER

    add_speaker_notes(
        slide2,
        "To contextualize our investigation, consider the central trust dilemma in distributed networks. Traditional PKI depends entirely on hierarchical Certification Authorities. If you access a secure website, your browser trusts a pre-installed root certificate. But in a peer-to-peer network like BitTorrent or Nostr, there is no root CA. Introducing one creates a single point of failure and invites administrative censorship.\n\n"
        "However, completely abandoning identity infrastructure creates a catastrophic attack surface. Without identity barriers, adversaries can launch Sybil attacks—generating millions of cryptographic keys for zero cost—to swamp voting quorums. Strategic colluders can form mutual rating cliques to harvest reputation, while malicious uploaders can poison content and downloaders can slander honest providers.\n\n"
        "We address this challenge across two complementary P2P paradigms: transactional file sharing, which deals with concrete chunk integrity and seeder reciprocity, and social networking, which deals with relational endorsements and spam moderation. As we will emphasize throughout, file sharing was fully implemented and empirically evaluated, whereas social networking is formulated as an architectural conceptual extension."
    )

    # ==========================================
    # SLIDE 3: Problem Statement and Research Objectives
    # ==========================================
    slide3 = prs.slides.add_slide(blank_layout)
    add_header(slide3, "Problem Statement & Formal Research Objectives", slide_num=3)

    add_card(slide3, Inches(0.8), Inches(1.6), Inches(11.733), Inches(1.3), title="Core Research Problem Statement", border_color=C_ACCENT_BLUE)
    tb_prob = slide3.shapes.add_textbox(Inches(0.95), Inches(2.05), Inches(11.4), Inches(0.75))
    tf_prob = tb_prob.text_frame
    tf_prob.word_wrap = True
    p_prob = tf_prob.paragraphs[0]
    p_prob.text = (
        "\"How can autonomous peers establish cryptographically verifiable identity and compute robust global reputation "
        "in the absence of centralized Certificate Authorities, while bounding Sybil injection and resisting strategic collusion cliques?\""
    )
    p_prob.font.name = 'Segoe UI'
    p_prob.font.size = Pt(12)
    p_prob.font.italic = True
    p_prob.font.color.rgb = C_TEXT_WHITE

    ro_cards = [
        ("RO-1: Admission & Identity", "Design a self-sovereign identity scheme binding Ed25519 public keys to DIDs with non-interactive Proof-of-Work to throttle zero-cost Sybil key generation."),
        ("RO-2: Web-of-Trust PKI", "Implement a decentralized peer-to-peer certificate mesh with bounded transitive path verification (depth <= 3) and local revocation caching."),
        ("RO-3: Spectral Trust Algorithm", "Develop EW-EigenTrust v1.8, integrating bilateral interaction receipts, Merkle fault attribution, and pre-trusted restart vectors for collusion resistance."),
        ("RO-4: Fault Attribution & Recovery", "Establish deterministic Merkle tree corruption proof localization, certificate revocation broadcasting, and Shamir (k,n) key recovery governance.")
    ]
    for i, (ro_title, ro_desc) in enumerate(ro_cards):
        left = Inches(0.8 + (i % 2) * 5.95)
        top = Inches(3.1 + (i // 2) * 1.85)
        add_card(slide3, left, top, Inches(5.78), Inches(1.65), title=ro_title)
        tb_r = slide3.shapes.add_textbox(left + Inches(0.18), top + Inches(0.55), Inches(5.42), Inches(1.0))
        tf_r = tb_r.text_frame
        tf_r.word_wrap = True
        p_r = tf_r.paragraphs[0]
        p_r.text = ro_desc
        p_r.font.name = 'Segoe UI'
        p_r.font.size = Pt(10.5)
        p_r.font.color.rgb = C_TEXT_MUTED

    add_speaker_notes(
        slide3,
        "Our core problem statement asks how autonomous peers can establish verifiable cryptographic identity and compute defensible global reputation without relying on centralized CAs, while simultaneously bounding Sybil injection and containing strategic collusion rings.\n\n"
        "To solve this problem systematically, we formulated four specific research objectives:\n"
        "First, Research Objective 1 focuses on admission and identity: establishing an asymmetric Proof-of-Work barrier bound to Ed25519 DIDs so that identity creation carries real computational cost.\n"
        "Second, Research Objective 2 constructs a decentralized Web-of-Trust mesh PKI where peers cross-sign certificates and validate trust paths within bounded horizons.\n"
        "Third, Research Objective 3 designs Evidence-Weighted EigenTrust v1.8, augmenting classical spectral iteration with bilateral receipts, dispute penalties, and pre-trusted teleportation.\n"
        "Fourth, Research Objective 4 provides Merkle-based fault attribution for poisoned chunks and Shamir threshold secret sharing for distributed key recovery."
    )

    # ==========================================
    # SLIDE 4: Literature Review and Research Gap
    # ==========================================
    slide4 = prs.slides.add_slide(blank_layout)
    add_header(slide4, "Literature Review & Identified Research Gap", slide_num=4)

    lit_cols = [
        ("Classical Web-of-Trust", "PGP / Zimmermann (1995) [6]\nIETF RFC 2693 SPKI [2]", [
            "Decentralized cross-signing of public key certificates without root CAs.",
            "Limitations: Subjective path explosion; rapid confidence decay over multi-hop paths.",
            "Lacks global reputation convergence; vulnerable to Sybil trust inflation."
        ]),
        ("Spectral Reputation", "EigenTrust / Kamvar (2003) [3]\nPageRank / Brin & Page", [
            "Computes global trust via left principal eigenvector of normalized rating matrix.",
            "Limitations: Assumes static honest pre-trusted seeds; lacks objective transaction proofs.",
            "Vulnerable to unweighted receipt grinding and coordinated rating cliques."
        ]),
        ("Decentralized Identity & PoW", "DIF W3C DIDs (2022) [1]\nBitcoin / Nakamoto (2008) [4]", [
            "Self-sovereign identifiers and computational admission barriers.",
            "Limitations: DIDs decouple identity from operational accountability.",
            "PoW throttles creation rates but provides no mechanism for evaluating behavioral trust."
        ])
    ]
    for i, (title, author, bullets) in enumerate(lit_cols):
        left = Inches(0.8 + i * 3.98)
        add_card(slide4, left, Inches(1.6), Inches(3.78), Inches(3.4), title=title)
        tb_col = slide4.shapes.add_textbox(left + Inches(0.18), Inches(2.1), Inches(3.42), Inches(2.8))
        tf_col = tb_col.text_frame
        tf_col.word_wrap = True
        p_auth = tf_col.paragraphs[0]
        p_auth.text = author
        p_auth.font.name = 'Segoe UI'
        p_auth.font.size = Pt(9.5)
        p_auth.font.bold = True
        p_auth.font.color.rgb = C_ACCENT_AMBER
        p_auth.space_after = Pt(6)
        for b in bullets:
            p_b = tf_col.add_paragraph()
            p_b.text = f"• {b}"
            p_b.font.name = 'Segoe UI'
            p_b.font.size = Pt(9.5)
            p_b.font.color.rgb = C_TEXT_MUTED
            p_b.space_after = Pt(5)

    add_card(slide4, Inches(0.8), Inches(5.15), Inches(11.733), Inches(1.55), title="The Critical Research Gap & Proposed Synthesis", border_color=C_ACCENT_EMERALD)
    tb_gap = slide4.shapes.add_textbox(Inches(0.95), Inches(5.55), Inches(11.4), Inches(1.05))
    tf_gap = tb_gap.text_frame
    tf_gap.word_wrap = True
    p_gap = tf_gap.paragraphs[0]
    p_gap.text = (
        "Prior systems decouple cryptographic authentication from reputation feedback: PKI architectures ignore operational behavior, "
        "while reputation algorithms compute ratings over malleable pseudonyms vulnerable to whitewashing. "
        "Our contribution is a vertically integrated 4-layer architecture synthesizing PoW admission, mesh WoT PKI, "
        "evidence-weighted spectral trust, and Merkle fault attribution into a unified, cryptographically enforced pipeline."
    )
    p_gap.font.name = 'Segoe UI'
    p_gap.font.size = Pt(10.5)
    p_gap.font.color.rgb = C_TEXT_WHITE

    add_speaker_notes(
        slide4,
        "To understand where our work sits, we surveyed three major pillars in the literature.\n\n"
        "First, classical Web-of-Trust schemes like PGP pioneered decentralized key certification. However, PGP relies on manual user signatures, suffers from confidence decay over multi-hop chains, and provides no mathematical mechanism for computing global consensus.\n\n"
        "Second, spectral reputation algorithms like Kamvar et al.'s EigenTrust formulate global trust as the stationary distribution of a Markov chain. While mathematically elegant, EigenTrust assumes pre-trusted nodes are permanently honest and treats all subjective ratings equally, leaving it vulnerable to receipt grinding and collusion.\n\n"
        "Third, decentralized identity standards from the W3C and Proof-of-Work mechanisms from Nakamoto provide self-sovereign naming and computational admission barriers, but they deliberately decouple identity from operational accountability.\n\n"
        "The critical research gap is this separation: PKI systems authenticate keys without knowing if peers act honestly, while reputation systems score interactions without authenticating identities. Our work bridges this gap by unifying cryptographic authentication and spectral reputation into a single vertical stack."
    )

    # ==========================================
    # SLIDE 5: Proposed Four-Layer Architecture
    # ==========================================
    slide5 = prs.slides.add_slide(blank_layout)
    add_header(slide5, "Proposed Vertically Integrated Four-Layer Architecture", slide_num=5)

    layers = [
        ("Layer 4: Revocation & Key Governance", C_ACCENT_ROSE, "Merkle chunk fault proofs, CRL gossip broadcasting, and Shamir (3,5) polynomial secret sharing for key recovery."),
        ("Layer 3: Evidence-Weighted EigenTrust v1.8", C_ACCENT_AMBER, "Spectral trust iteration over evidence-weighted matrix C', incorporating bilateral receipts, dispute penalties, and restart vector p."),
        ("Layer 2: Web-of-Trust Mesh PKI", C_ACCENT_CYAN, "Peer-to-peer X.509-like certificates, Ed25519 cross-signing, 30-day validity windows, and bounded path discovery (depth <= 3)."),
        ("Layer 1: Identity & PoW Admission", C_ACCENT_EMERALD, "Deterministic 'did:pki:ed25519:<pubkey>' identifiers bound to SHA-256 Proof-of-Work challenge (D >= 16 bits).")
    ]
    for i, (l_title, l_col, l_desc) in enumerate(layers):
        top = Inches(1.6 + i * 1.25)
        card = slide5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), top, Inches(11.733), Inches(1.1))
        card.fill.solid()
        card.fill.fore_color.rgb = C_BG_CARD
        card.line.color.rgb = l_col
        card.line.width = Pt(1.5)

        badge = slide5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.0), top + Inches(0.2), Inches(3.6), Inches(0.7))
        badge.fill.solid()
        badge.fill.fore_color.rgb = RGBColor(15, 23, 42)
        badge.line.color.rgb = l_col
        tb_b = slide5.shapes.add_textbox(Inches(1.05), top + Inches(0.25), Inches(3.5), Inches(0.6))
        tf_b = tb_b.text_frame
        tf_b.word_wrap = True
        p_b = tf_b.paragraphs[0]
        p_b.text = l_title
        p_b.font.name = 'Segoe UI'
        p_b.font.size = Pt(11)
        p_b.font.bold = True
        p_b.font.color.rgb = l_col

        tb_desc = slide5.shapes.add_textbox(Inches(4.8), top + Inches(0.2), Inches(7.5), Inches(0.7))
        tf_desc = tb_desc.text_frame
        tf_desc.word_wrap = True
        p_d = tf_desc.paragraphs[0]
        p_d.text = l_desc
        p_d.font.name = 'Segoe UI'
        p_d.font.size = Pt(10.5)
        p_d.font.color.rgb = C_TEXT_WHITE

    add_speaker_notes(
        slide5,
        "Here we present our core architectural contribution: a vertically integrated four-layer stack where each layer enforces distinct security invariants.\n\n"
        "At Layer 1, the Identity and Admission layer binds Ed25519 public keys into deterministic DIDs and requires solving a non-interactive Proof-of-Work puzzle to deter Sybil generation.\n\n"
        "At Layer 2, the Web-of-Trust PKI layer organizes peers into a decentralized cross-certification mesh, establishing key authenticity through bounded transitive trust paths without any central root authority.\n\n"
        "At Layer 3, the Evidence-Weighted EigenTrust engine computes global reputation by feeding cryptographic interaction receipts and dispute penalties into a damped power-iteration Markov process.\n\n"
        "Finally, at Layer 4, the Revocation and Key Governance layer provides deterministic Merkle chunk fault attribution for automated revocation and Shamir threshold secret sharing for distributed master key recovery.\n\n"
        "Crucially, information flows upward deterministically: higher-level trust decisions depend on mathematically validated cryptographic proofs generated at lower layers."
    )

    # ==========================================
    # SLIDE 6: Layer 1 — Identity and Proof-of-Work Admission
    # ==========================================
    slide6 = prs.slides.add_slide(blank_layout)
    add_header(slide6, "Layer 1: Self-Sovereign Identity & Proof-of-Work Admission", slide_num=6)

    add_card(slide6, Inches(0.8), Inches(1.6), Inches(5.7), Inches(5.1), title="Deterministic Identity Binding")
    tb1 = slide6.shapes.add_textbox(Inches(0.95), Inches(2.2), Inches(5.4), Inches(4.3))
    tf1 = tb1.text_frame
    tf1.word_wrap = True
    tf1.paragraphs[0].text = "• DID Specification:"
    tf1.paragraphs[0].font.name = 'Segoe UI'
    tf1.paragraphs[0].font.size = Pt(11)
    tf1.paragraphs[0].font.bold = True
    tf1.paragraphs[0].font.color.rgb = C_ACCENT_CYAN
    p_did = tf1.add_paragraph()
    p_did.text = "did:pki:ed25519:<64-character-hex-encoded-pubkey>"
    p_did.font.name = 'Consolas'
    p_did.font.size = Pt(9.5)
    p_did.font.color.rgb = C_ACCENT_EMERALD
    p_did.space_after = Pt(8)

    for b in [
        ("Self-Sovereign Cryptographic Root", "Keypair generation requires no central registry. Ed25519 provides 128-bit security level with compact 32-byte public keys and 64-byte signatures."),
        ("Tamper-Proof Binding", "Public keys are embedded directly in the DID URI. Identity spoofing is prevented because the public key defines the identity itself."),
        ("Mutual Authentication", "Used during TLS session handshake: peers mutually sign challenge nonces to prove possession of the private key corresponding to their DID.")
    ]:
        p_t = tf1.add_paragraph()
        p_t.text = f"• {b[0]}:"
        p_t.font.name = 'Segoe UI'
        p_t.font.size = Pt(10.5)
        p_t.font.bold = True
        p_t.font.color.rgb = C_TEXT_WHITE
        p_d = tf1.add_paragraph()
        p_d.text = b[1]
        p_d.font.name = 'Segoe UI'
        p_d.font.size = Pt(10)
        p_d.font.color.rgb = C_TEXT_MUTED
        p_d.space_after = Pt(6)

    add_card(slide6, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.1), title="Non-Interactive Proof-of-Work (PoW)")
    tb2 = slide6.shapes.add_textbox(Inches(6.95), Inches(2.2), Inches(5.4), Inches(4.3))
    tf2 = tb2.text_frame
    tf2.word_wrap = True
    tf2.paragraphs[0].text = "• Cryptographic Challenge Condition:"
    tf2.paragraphs[0].font.name = 'Segoe UI'
    tf2.paragraphs[0].font.size = Pt(11)
    tf2.paragraphs[0].font.bold = True
    tf2.paragraphs[0].font.color.rgb = C_ACCENT_CYAN
    p_pow = tf2.add_paragraph()
    p_pow.text = "SHA-256( DID || nonce ) < 2^(256 - D)"
    p_pow.font.name = 'Consolas'
    p_pow.font.size = Pt(10)
    p_pow.font.color.rgb = C_ACCENT_AMBER
    p_pow.space_after = Pt(8)

    for b in [
        ("Baseline Difficulty", "Configured to D = 16 bits. Requires an expected 2^16 = 65,536 hash operations (~15-50 ms on standard commodity CPUs)."),
        ("Asymmetric Verification", "Solver must perform O(2^D) brute-force hashing operations; verifying peers validate in O(1) time via a single SHA-256 hash calculation."),
        ("Economic Sybil Throttling", "Generating 1,000 Sybil identities imposes ~65.5 million hash operations, eliminating instantaneous zero-cost pseudonym swarms."),
        ("Important Qualification", "PoW provides an economic cost barrier, NOT an absolute Sybil defense. Well-funded attackers or GPU clusters can surmount static difficulty barriers [4].")
    ]:
        p_t = tf2.add_paragraph()
        p_t.text = f"• {b[0]}:"
        p_t.font.name = 'Segoe UI'
        p_t.font.size = Pt(10.5)
        p_t.font.bold = True
        p_t.font.color.rgb = C_TEXT_WHITE
        p_d = tf2.add_paragraph()
        p_d.text = b[1]
        p_d.font.name = 'Segoe UI'
        p_d.font.size = Pt(10)
        p_d.font.color.rgb = C_TEXT_MUTED
        p_d.space_after = Pt(6)

    add_speaker_notes(
        slide6,
        "Slide 6 details Layer 1, our identity and admission engine. We define a self-sovereign DID method string: did:pki:ed25519 followed by the hex public key. Because the public key is embedded in the identifier, an identity cannot be registered without possessing the underlying private key.\n\n"
        "To prevent adversaries from generating millions of Sybils instantaneously, peers must solve a non-interactive Proof-of-Work challenge. The challenge requires finding a nonce such that the SHA-256 hash of the DID concatenated with the nonce begins with D leading zero bits.\n\n"
        "At our baseline difficulty of D=16 bits, finding a solution requires an average of 65,536 hash evaluations. Crucially, verification is completely asymmetric: verifying peers compute exactly one hash in constant time, or O(1).\n\n"
        "However, as we note under our rigorous academic audit, Proof-of-Work is an economic throttle, not a permanent mathematical defense against Sybils. A determined adversary with specialized ASIC hardware can still compute batches of identities."
    )

    # ==========================================
    # SLIDE 7: Layer 2 — Web-of-Trust Mesh PKI
    # ==========================================
    slide7 = prs.slides.add_slide(blank_layout)
    add_header(slide7, "Layer 2: Web-of-Trust Mesh PKI & Bounded Verification", slide_num=7)

    add_card(slide7, Inches(0.8), Inches(1.6), Inches(5.7), Inches(5.1), title="PeerCertificate Architecture")
    tb1 = slide7.shapes.add_textbox(Inches(0.95), Inches(2.2), Inches(5.4), Inches(4.3))
    tf1 = tb1.text_frame
    tf1.word_wrap = True
    tf1.paragraphs[0].text = "• Core Data Structure:"
    tf1.paragraphs[0].font.name = 'Segoe UI'
    tf1.paragraphs[0].font.size = Pt(11)
    tf1.paragraphs[0].font.bold = True
    tf1.paragraphs[0].font.color.rgb = C_ACCENT_CYAN

    code_str = (
        "struct PeerCertificate {\n"
        "  issuer_did:  DIDString,\n"
        "  subject_did: DIDString,\n"
        "  subject_pubkey: Ed25519PublicKey,\n"
        "  valid_from:  Timestamp,\n"
        "  valid_to:    Timestamp,  // 30-day default\n"
        "  signature:   Ed25519Signature\n"
        "}"
    )
    p_code = tf1.add_paragraph()
    p_code.text = code_str
    p_code.font.name = 'Consolas'
    p_code.font.size = Pt(9.5)
    p_code.font.color.rgb = C_ACCENT_EMERALD
    p_code.space_after = Pt(8)

    for b in [
        ("Decentralized Cross-Signing", "Peers cross-sign certificates after successful verified transactions or mutual verification handshakes."),
        ("Temporal Expiration", "Mandatory validity window (default 30 days) prevents stale key retention and forces periodic re-evaluation [7].")
    ]:
        p_t = tf1.add_paragraph()
        p_t.text = f"• {b[0]}:"
        p_t.font.name = 'Segoe UI'
        p_t.font.size = Pt(10.5)
        p_t.font.bold = True
        p_t.font.color.rgb = C_TEXT_WHITE
        p_d = tf1.add_paragraph()
        p_d.text = b[1]
        p_d.font.name = 'Segoe UI'
        p_d.font.size = Pt(10)
        p_d.font.color.rgb = C_TEXT_MUTED
        p_d.space_after = Pt(6)

    add_card(slide7, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.1), title="Trust Mesh & Path Search Pipeline")
    tb2 = slide7.shapes.add_textbox(Inches(6.95), Inches(2.2), Inches(5.4), Inches(4.3))
    tf2 = tb2.text_frame
    tf2.word_wrap = True
    tf2.paragraphs[0].text = "• Bounded Breadth-First Trust Search:"
    tf2.paragraphs[0].font.name = 'Segoe UI'
    tf2.paragraphs[0].font.size = Pt(11)
    tf2.paragraphs[0].font.bold = True
    tf2.paragraphs[0].font.color.rgb = C_ACCENT_CYAN

    for b in [
        ("Bounded Path Depth (d_max <= 3)", "Graph traversal is strictly truncated at 3 hops. Prevents exponential search space explosion in large P2P meshes."),
        ("Exponential Confidence Decay", "Path confidence decays exponentially: Conf(path) = Product_{i=1}^k delta, where default delta = 0.5 per hop."),
        ("Local CRL Revocation Cache", "Before certifying any edge, the verifier checks its local Certificate Revocation List (CRL) for active revocations."),
        ("Trust vs. Recommendation", "A Web-of-Trust path confirms public key binding authenticity, NOT operational reliability. Operational trust is computed by Layer 3.")
    ]:
        p_t = tf2.add_paragraph()
        p_t.text = f"• {b[0]}:"
        p_t.font.name = 'Segoe UI'
        p_t.font.size = Pt(10.5)
        p_t.font.bold = True
        p_t.font.color.rgb = C_TEXT_WHITE
        p_d = tf2.add_paragraph()
        p_d.text = b[1]
        p_d.font.name = 'Segoe UI'
        p_d.font.size = Pt(10)
        p_d.font.color.rgb = C_TEXT_MUTED
        p_d.space_after = Pt(6)

    add_speaker_notes(
        slide7,
        "Moving to Layer 2, we implement a decentralized Web-of-Trust mesh PKI. Rather than relying on hierarchical X.509 CA roots, peers issue lightweight PeerCertificates cross-signing the public keys of other peers.\n\n"
        "Each certificate contains the issuer's DID, subject's DID, public key, validity timestamp—set to a strict 30-day window—and an Ed25519 digital signature.\n\n"
        "When peer A needs to verify peer B's key, it executes a bounded Breadth-First Search over the local trust graph. To prevent search explosion and transitive trust dilution, we enforce a strict maximum depth of 3 hops and apply an exponential confidence decay factor delta of 0.5 per hop.\n\n"
        "Importantly, we distinguish key binding trust from behavioral reputation: a valid WoT certificate proves that a public key belongs to the advertised peer, but it does not guarantee that the peer won't send corrupted data. That behavioral evaluation is handled by Layer 3."
    )

    # ==========================================
    # SLIDE 8: Layer 3 — Evidence-Weighted EigenTrust v1.8
    # ==========================================
    slide8 = prs.slides.add_slide(blank_layout)
    add_header(slide8, "Layer 3: Evidence-Weighted EigenTrust v1.8 (EW-EigenTrust)", slide_num=8)

    add_card(slide8, Inches(0.8), Inches(1.6), Inches(5.7), Inches(5.1), title="Evidence Matrix Formulation")
    tb1 = slide8.shapes.add_textbox(Inches(0.95), Inches(2.2), Inches(5.4), Inches(4.3))
    tf1 = tb1.text_frame
    tf1.word_wrap = True
    tf1.paragraphs[0].text = "• Raw Score Formulation S_ij:"
    tf1.paragraphs[0].font.name = 'Segoe UI'
    tf1.paragraphs[0].font.size = Pt(11)
    tf1.paragraphs[0].font.bold = True
    tf1.paragraphs[0].font.color.rgb = C_ACCENT_CYAN

    eq_str = "S_ij = max(0, w_pos * R_ij^(pos) - w_dispute * D_ij - w_neg * R_ij^(neg))"
    p_eq = tf1.add_paragraph()
    p_eq.text = eq_str
    p_eq.font.name = 'Consolas'
    p_eq.font.size = Pt(9.5)
    p_eq.font.color.rgb = C_ACCENT_AMBER
    p_eq.space_after = Pt(8)

    for b in [
        ("Evidence Weights", "w_pos = 1.0 (bilateral delivery receipt)\nw_neg = 2.0 (timeout or delivery failure)\nw_dispute = 5.0 (substantiated Merkle corruption proof)"),
        ("Asymmetric Dispute Penalty", "Disputes are penalized at 5x the weight of positive transactions, making malicious attacks economically expensive to sustain."),
        ("Row Normalization", "C_ij = S_ij / Sum_k S_ik if Sum_k S_ik > 0.\nFallback: If peer i has zero evidence (Sum_k S_ik = 0), row i defaults to restart vector p_j.")
    ]:
        p_t = tf1.add_paragraph()
        p_t.text = f"• {b[0]}:"
        p_t.font.name = 'Segoe UI'
        p_t.font.size = Pt(10.5)
        p_t.font.bold = True
        p_t.font.color.rgb = C_TEXT_WHITE
        p_d = tf1.add_paragraph()
        p_d.text = b[1]
        p_d.font.name = 'Segoe UI'
        p_d.font.size = Pt(10)
        p_d.font.color.rgb = C_TEXT_MUTED
        p_d.space_after = Pt(6)

    add_card(slide8, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.1), title="Spectral Power Iteration")
    tb2 = slide8.shapes.add_textbox(Inches(6.95), Inches(2.2), Inches(5.4), Inches(4.3))
    tf2 = tb2.text_frame
    tf2.word_wrap = True
    tf2.paragraphs[0].text = "• Damped Markov Iteration:"
    tf2.paragraphs[0].font.name = 'Segoe UI'
    tf2.paragraphs[0].font.size = Pt(11)
    tf2.paragraphs[0].font.bold = True
    tf2.paragraphs[0].font.color.rgb = C_ACCENT_CYAN

    p_iter = tf2.add_paragraph()
    p_iter.text = "t^(k+1) = (1 - alpha) * (C')^T * t^(k) + alpha * p"
    p_iter.font.name = 'Consolas'
    p_iter.font.size = Pt(10)
    p_iter.font.color.rgb = C_ACCENT_EMERALD
    p_iter.space_after = Pt(8)

    for b in [
        ("Damping Factor (alpha = 0.15)", "Guarantees ergodicity and unique stationary distribution via the Perron-Frobenius theorem [3]."),
        ("Pre-Trusted Teleportation Vector p", "Concentrates probability mass on verified bootstrap anchors. Prevents disconnected sink traps from accumulating arbitrary reputation."),
        ("Convergence Criterion", "Terminates when || t^(k+1) - t^(k) ||_1 < epsilon = 10^(-6) (typically 12-25 iterations)."),
        ("Mathematical Determinism", "Global trust vector t represents the stationary probability distribution of an ergodic random walk on the evidence graph.")
    ]:
        p_t = tf2.add_paragraph()
        p_t.text = f"• {b[0]}:"
        p_t.font.name = 'Segoe UI'
        p_t.font.size = Pt(10.5)
        p_t.font.bold = True
        p_t.font.color.rgb = C_TEXT_WHITE
        p_d = tf2.add_paragraph()
        p_d.text = b[1]
        p_d.font.name = 'Segoe UI'
        p_d.font.size = Pt(10)
        p_d.font.color.rgb = C_TEXT_MUTED
        p_d.space_after = Pt(6)

    add_speaker_notes(
        slide8,
        "Layer 3 contains our reputation algorithm: Evidence-Weighted EigenTrust v1.8. In classical EigenTrust, ratings are simple integer scores. In EW-EigenTrust, raw scores are computed from cryptographically authenticated evidence.\n\n"
        "We assign weight 1.0 to mutually signed bilateral receipts, weight 2.0 to timeouts, and a heavy penalty of 5.0 to substantiated Merkle disputes. This creates an asymmetric penalty regime where a single poisoned chunk wipes out the trust earned from five successful transactions.\n\n"
        "The evidence scores are row-normalized to yield stochastic matrix C'. If a peer has zero interactions, its row falls back to the teleportation vector p.\n\n"
        "Global trust is then computed using power iteration: t equals (1 minus alpha) times C-transpose times t, plus alpha times p, with damping factor alpha set to 0.15. By Perron-Frobenius theory, this guarantees convergence to a unique stationary trust vector regardless of initial initialization."
    )

    # ==========================================
    # SLIDE 9: Layer 4 — Revocation and Key Recovery
    # ==========================================
    slide9 = prs.slides.add_slide(blank_layout)
    add_header(slide9, "Layer 4: Revocation & Shamir Threshold Key Recovery", slide_num=9)

    add_card(slide9, Inches(0.8), Inches(1.6), Inches(5.7), Inches(5.1), title="Deterministic Certificate Revocation")
    tb1 = slide9.shapes.add_textbox(Inches(0.95), Inches(2.2), Inches(5.4), Inches(4.3))
    tf1 = tb1.text_frame
    tf1.word_wrap = True
    tf1.paragraphs[0].text = "• Revocation Trigger & Propagation:"
    tf1.paragraphs[0].font.name = 'Segoe UI'
    tf1.paragraphs[0].font.size = Pt(11)
    tf1.paragraphs[0].font.bold = True
    tf1.paragraphs[0].font.color.rgb = C_ACCENT_CYAN

    for b in [
        ("Two Revocation Triggers", "1. Key Compromise: Peer signs a self-revocation announcement.\n2. Proven Malfeasance: Peer is convicted via Merkle contradiction proof of distributing corrupted data."),
        ("Gossip-Based CRL Dissemination", "Revocation messages are broadcast across the P2P overlay via epidemic gossip. Peering nodes verify the signature before caching in their local CRL."),
        ("Immediate Trust Isolation", "Once revoked, all incoming and outgoing WoT edges are pruned, and the node's trust share collapses to the zero baseline."),
        ("No Reliance on Central OCSP", "Unlike centralized PKI which depends on OCSP responders [7], our revocation verification is autonomous and local.")
    ]:
        p_t = tf1.add_paragraph()
        p_t.text = f"• {b[0]}:"
        p_t.font.name = 'Segoe UI'
        p_t.font.size = Pt(10.5)
        p_t.font.bold = True
        p_t.font.color.rgb = C_TEXT_WHITE
        p_d = tf1.add_paragraph()
        p_d.text = b[1]
        p_d.font.name = 'Segoe UI'
        p_d.font.size = Pt(10)
        p_d.font.color.rgb = C_TEXT_MUTED
        p_d.space_after = Pt(6)

    add_card(slide9, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.1), title="Shamir (3, 5) Threshold Key Recovery")
    tb2 = slide9.shapes.add_textbox(Inches(6.95), Inches(2.2), Inches(5.4), Inches(4.3))
    tf2 = tb2.text_frame
    tf2.word_wrap = True
    tf2.paragraphs[0].text = "• Secret Sharing Formulation:"
    tf2.paragraphs[0].font.name = 'Segoe UI'
    tf2.paragraphs[0].font.size = Pt(11)
    tf2.paragraphs[0].font.bold = True
    tf2.paragraphs[0].font.color.rgb = C_ACCENT_CYAN

    p_shamir = tf2.add_paragraph()
    p_shamir.text = "f(x) = S + a_1*x + a_2*x^2 (mod p)"
    p_shamir.font.name = 'Consolas'
    p_shamir.font.size = Pt(10)
    p_shamir.font.color.rgb = C_ACCENT_EMERALD
    p_shamir.space_after = Pt(8)

    for b in [
        ("Polynomial Threshold Sharing", "Master secret key S is split across n=5 trusted guardians using a degree k-1 = 2 polynomial over GF(2^8) [5]."),
        ("k=3 Reconstruction Quorum", "Any 3 valid guardian shares can reconstruct S via Lagrange interpolation; 2 or fewer shares reveal mathematically zero information."),
        ("Social Recovery Semantics", "Guardians can be selected from highly trusted WoT neighbors or offline cold-storage nodes."),
        ("Evaluation Qualification", "Shamir secret sharing is fully implemented and tested at the single-node cryptographic unit level; multi-party live network consensus was not simulated.")
    ]:
        p_t = tf2.add_paragraph()
        p_t.text = f"• {b[0]}:"
        p_t.font.name = 'Segoe UI'
        p_t.font.size = Pt(10.5)
        p_t.font.bold = True
        p_t.font.color.rgb = C_TEXT_WHITE
        p_d = tf2.add_paragraph()
        p_d.text = b[1]
        p_d.font.name = 'Segoe UI'
        p_d.font.size = Pt(10)
        p_d.font.color.rgb = C_TEXT_MUTED
        p_d.space_after = Pt(6)

    add_speaker_notes(
        slide9,
        "Slide 9 outlines Layer 4: Revocation and Key Governance. In centralized PKI, certificate revocation is notoriously fragile, relying on Online Certificate Status Protocol (OCSP) servers that introduce latency, privacy leaks, and single points of failure.\n\n"
        "In our architecture, revocations are triggered either voluntarily upon key rotation or involuntarily when a peer is convicted by a Merkle dispute proof. Revocation vectors are broadcast via epidemic gossip and validated locally against cryptographic signatures.\n\n"
        "For key recovery, we implement Shamir's (k, n) secret sharing with threshold k=3 out of n=5 guardians. The master secret is embedded as the constant term of a random degree-2 polynomial over Galois Field GF(2^8). Any three guardians can reconstruct the key using Lagrange interpolation, while two colluding guardians gain zero mathematical information.\n\n"
        "In our scope audit, we explicitly clarify that Shamir sharing is implemented and tested at the cryptographic module level, but multi-party live network recovery was not part of the Phase 8.2 simulation trials."
    )

    # ==========================================
    # SLIDE 10: End-to-End File-Sharing Workflow and Merkle Fault Attribution
    # ==========================================
    slide10 = prs.slides.add_slide(blank_layout)
    add_header(slide10, "End-to-End File-Sharing & Merkle Fault Attribution", slide_num=10)

    # Top visual flow diagram (5 step cards)
    steps = [
        ("1. Discovery & Handshake", "TLS 1.3 + mutual DID Ed25519 challenge"),
        ("2. WoT Path Verification", "BFS path search (depth <= 3, conf >= 0.25)"),
        ("3. Manifest Exchange", "Downloader receives root hash R and chunk list"),
        ("4. Chunk Audit & Delivery", "Verify O(log N) Merkle path against root R"),
        ("5. Evidence Settlement", "Exchange BilateralReceipt or issue dispute")
    ]
    for i, (s_title, s_sub) in enumerate(steps):
        left = Inches(0.8 + i * 2.4)
        card = slide10.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, Inches(1.6), Inches(2.25), Inches(1.3))
        card.fill.solid()
        card.fill.fore_color.rgb = C_BG_CARD
        card.line.color.rgb = C_ACCENT_CYAN
        card.line.width = Pt(1)

        tb_s = slide10.shapes.add_textbox(left + Inches(0.08), Inches(1.68), Inches(2.09), Inches(1.15))
        tf_s = tb_s.text_frame
        tf_s.word_wrap = True
        p1 = tf_s.paragraphs[0]
        p1.text = s_title
        p1.font.name = 'Segoe UI'
        p1.font.size = Pt(10)
        p1.font.bold = True
        p1.font.color.rgb = C_TEXT_WHITE
        p2 = tf_s.add_paragraph()
        p2.text = s_sub
        p2.font.name = 'Segoe UI'
        p2.font.size = Pt(8.5)
        p2.font.color.rgb = C_TEXT_MUTED

    # Bottom Two Deep-Dive Cards
    add_card(slide10, Inches(0.8), Inches(3.1), Inches(5.7), Inches(3.6), title="Merkle Fault Attribution Complexity")
    tb_m = slide10.shapes.add_textbox(Inches(0.95), Inches(3.6), Inches(5.4), Inches(2.9))
    tf_m = tb_m.text_frame
    tf_m.word_wrap = True
    for b in [
        ("Logarithmic Verification", "For a file split into N chunks, proof verification takes exactly O(log N) hash operations and requires O(log N) sibling hashes."),
        ("Avoids Full Payload Download", "A downloader verifies chunk i in isolation without downloading all N chunks, immediately isolating corrupted transmissions."),
        ("Contradiction Proof", "If computed root R_calc != R_manifest, the downloader generates an undeniable proof of malfeasance containing: chunk_index, chunk_data, and audit_path."),
        ("Slander Resistance", "A malicious downloader cannot falsely accuse an honest uploader because the uploader's signature is bound to the verifiable Merkle root.")
    ]:
        p_t = tf_m.add_paragraph() if tf_m.paragraphs[0].text else tf_m.paragraphs[0]
        p_t.text = f"• {b[0]}:"
        p_t.font.name = 'Segoe UI'
        p_t.font.size = Pt(10)
        p_t.font.bold = True
        p_t.font.color.rgb = C_TEXT_WHITE
        p_d = tf_m.add_paragraph()
        p_d.text = b[1]
        p_d.font.name = 'Segoe UI'
        p_d.font.size = Pt(9.5)
        p_d.font.color.rgb = C_TEXT_MUTED
        p_d.space_after = Pt(4)

    add_card(slide10, Inches(6.8), Inches(3.1), Inches(5.7), Inches(3.6), title="Tier 3 Evidence Portability Gap")
    tb_g = slide10.shapes.add_textbox(Inches(6.95), Inches(3.6), Inches(5.4), Inches(2.9))
    tf_g = tb_g.text_frame
    tf_g.word_wrap = True
    for b in [
        ("Simulator Global Key Oracle", "In the evaluated Phase 8.2 simulator, delivery receipts rely on a global simulator key oracle D_sim to cross-verify signatures."),
        ("BilateralReceipt Limitation", "Real-world BilateralReceipt instances are signed pairwise between peer i and peer j; they are not inherently portable third-party proofs."),
        ("Upper-Bound Idealization", "The simulation assumes perfect global receipt visibility, representing an empirical upper-bound on dispute resolution."),
        ("Practical Mitigation", "Production decentralized deployment would require threshold multi-signatures or cryptographic zero-knowledge proofs for trustless third-party verification.")
    ]:
        p_t = tf_g.add_paragraph() if tf_g.paragraphs[0].text else tf_g.paragraphs[0]
        p_t.text = f"• {b[0]}:"
        p_t.font.name = 'Segoe UI'
        p_t.font.size = Pt(10)
        p_t.font.bold = True
        p_t.font.color.rgb = C_ACCENT_AMBER if "Oracle" in b[0] else C_TEXT_WHITE
        p_d = tf_g.add_paragraph()
        p_d.text = b[1]
        p_d.font.name = 'Segoe UI'
        p_d.font.size = Pt(9.5)
        p_d.font.color.rgb = C_TEXT_MUTED
        p_d.space_after = Pt(4)

    add_speaker_notes(
        slide10,
        "Slide 10 details our end-to-end file sharing protocol and Merkle fault attribution mechanism.\n\n"
        "The workflow follows five discrete stages: first, peers perform an authenticated handshake. Second, they verify the uploader's public key across the Web-of-Trust mesh. Third, the downloader retrieves the file manifest containing the Merkle root hash.\n\n"
        "Fourth, during chunk delivery, the uploader provides the chunk payload along with its Merkle audit path. As emphasized in our technical corrections, verifying this proof requires exactly O(log N) hash operations and O(log N) sibling hashes. This allows the downloader to mathematically verify chunk integrity in isolation without downloading the rest of the file.\n\n"
        "Fifth, if verification succeeds, peers exchange a bilateral delivery receipt. If the chunk is corrupted, the downloader publishes a Merkle contradiction proof, triggering an immediate dispute penalty.\n\n"
        "We also highlight our Tier 3 Evidence Portability Gap: in the simulation, delivery receipts rely on a global key oracle. In a live decentralized network, bilateral receipts require additional threshold attestation to be fully portable across third parties."
    )

    # ==========================================
    # SLIDE 11: Experimental Methodology and Benchmark Setup
    # ==========================================
    slide11 = prs.slides.add_slide(blank_layout)
    add_header(slide11, "Experimental Methodology & Simulation Benchmark", slide_num=11)

    add_card(slide11, Inches(0.8), Inches(1.6), Inches(3.7), Inches(5.1), title="Experimental Protocol Setup")
    tb1 = slide11.shapes.add_textbox(Inches(0.95), Inches(2.2), Inches(3.4), Inches(4.3))
    tf1 = tb1.text_frame
    tf1.word_wrap = True
    for b in [
        ("Preregistered Baseline", "1,140 total trial runs executed under strict preregistration (Phase 8.2 protocol)."),
        ("Network Topology", "N = 30 and N = 50 nodes:\n• 20 Honest nodes\n• 5 Colluding nodes\n• 5 Sybils / Malicious nodes"),
        ("Simulation Engine", "Custom discrete-event P2P simulator with paired random seeds (S = 100) across all modes."),
        ("Evaluation Modes", "1. Standard EigenTrust [3]\n2. EW-EigenTrust v1.8\n3. PoW-Gated EW-EigenTrust")
    ]:
        p_t = tf1.add_paragraph() if tf1.paragraphs[0].text else tf1.paragraphs[0]
        p_t.text = f"• {b[0]}:"
        p_t.font.name = 'Segoe UI'
        p_t.font.size = Pt(10.5)
        p_t.font.bold = True
        p_t.font.color.rgb = C_TEXT_WHITE
        p_d = tf1.add_paragraph()
        p_d.text = b[1]
        p_d.font.name = 'Segoe UI'
        p_d.font.size = Pt(10)
        p_d.font.color.rgb = C_TEXT_MUTED
        p_d.space_after = Pt(6)

    add_card(slide11, Inches(4.8), Inches(1.6), Inches(7.733), Inches(5.1), title="Preregistered Attack Scenarios Matrix")
    tb2 = slide11.shapes.add_textbox(Inches(4.95), Inches(2.2), Inches(7.4), Inches(4.3))
    tf2 = tb2.text_frame
    tf2.word_wrap = True

    scenarios = [
        ("Scenarios 1-3: Identity & Whitewashing Attacks", [
            "Scen 1 (Sybil Swarm): Rapid generation of unverified pseudonyms; throttled by Layer 1 PoW.",
            "Scen 2 (Whitewashing): Malicious nodes discard low-reputation identities; prevented by fresh identity baseline.",
            "Scen 3 (Transaction Spam): Low-value uncoordinated spamming; filtered by receipt weighting."
        ]),
        ("Scenarios 4-5: Collusion Ring Topologies", [
            "Scen 4 (Closed Collusion): 5 colluders rate each other exclusively; no external interactions.",
            "Scen 5 (Leaky Coalition): Colluders engage in honest transactions with honest nodes while boosting confederates."
        ]),
        ("Scenarios 6-8: Exploitation & Dynamic Perturbations", [
            "Scen 6 (Receipt Grinding): Colluders generate high synthetic transaction volumes to harvest trust.",
            "Scen 7 (Slander Disputes): Colluders file false complaints; structurally degenerate in simulation.",
            "Scen 8 (Churn & Partition): High node arrival/departure rates; validates convergence stability."
        ])
    ]
    for cat_title, s_list in scenarios:
        p_cat = tf2.add_paragraph() if tf2.paragraphs[0].text else tf2.paragraphs[0]
        p_cat.text = cat_title
        p_cat.font.name = 'Segoe UI'
        p_cat.font.size = Pt(11)
        p_cat.font.bold = True
        p_cat.font.color.rgb = C_ACCENT_CYAN
        p_cat.space_after = Pt(3)
        for s in s_list:
            p_s = tf2.add_paragraph()
            p_s.text = f"• {s}"
            p_s.font.name = 'Segoe UI'
            p_s.font.size = Pt(9.5)
            p_s.font.color.rgb = C_TEXT_MUTED
            p_s.space_after = Pt(3)

    add_speaker_notes(
        slide11,
        "Turning to our empirical evaluation, Slide 11 outlines our experimental methodology.\n\n"
        "Rather than running ad-hoc trials, our experiments followed a preregistered protocol executed across 1,140 simulation runs. We evaluated networks of 30 and 50 nodes containing 20 honest peers, 5 strategic colluders, and 5 malicious Sybil nodes.\n\n"
        "We utilized paired random seeds—exactly 100 identical seed runs per scenario—to directly compare three modes: standard EigenTrust as our baseline, Evidence-Weighted EigenTrust, and PoW-Gated EW-EigenTrust.\n\n"
        "We tested eight distinct adversarial scenarios covering identity flooding, whitewashing, closed collusion rings, leaky coalitions, receipt grinding, and slander disputes. This rigorous comparative setup allows us to make statistically robust claims backed by two-sided Wilcoxon signed-rank tests and Cohen's d effect sizes."
    )

    # ==========================================
    # SLIDE 12: Key Empirical Results and Statistical Findings
    # ==========================================
    slide12 = prs.slides.add_slide(blank_layout)
    add_header(slide12, "Key Empirical Results & Statistical Findings", slide_num=12)

    # Table of Results
    table_shape = slide12.shapes.add_table(5, 5, Inches(0.8), Inches(1.6), Inches(11.733), Inches(2.6))
    table = table_shape.table
    table.columns[0].width = Inches(3.2)
    table.columns[1].width = Inches(2.1)
    table.columns[2].width = Inches(2.1)
    table.columns[3].width = Inches(2.1)
    table.columns[4].width = Inches(2.233)

    headers = ["Scenario & Attack Vector", "Standard EigenTrust", "EW-EigenTrust v1.8", "Relative Shift (%)", "Statistical Significance"]
    for col_idx, h in enumerate(headers):
        cell = table.cell(0, col_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = RGBColor(15, 23, 42)
        p = cell.text_frame.paragraphs[0]
        p.text = h
        p.font.name = 'Segoe UI'
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = C_ACCENT_CYAN

    data = [
        ("Scenario 5: Leaky Coalition Colluder Trust", "0.1834 ± 0.012", "0.1068 ± 0.009", "-41.8% (Suppressed)", "p < 10^(-6), d = 2.45"),
        ("Scenario 6: Receipt Grinding (Standard)", "0.1420 ± 0.010", "0.1610 ± 0.011", "+13.38% (Colluder Gain)", "H-1 Refuted (p < 0.001)"),
        ("Scenario 6: Extended Receipt Grinding", "0.1420 ± 0.010", "0.1674 ± 0.012", "+17.92% (Colluder Gain)", "H-1 Refuted (p < 0.001)"),
        ("Scenario 7: Slander / False Accusations", "0.0000 ± 0.000", "0.0000 ± 0.000", "0.00% (Degenerate)", "Structurally Disconnected")
    ]
    for row_idx, row in enumerate(data, start=1):
        for col_idx, val in enumerate(row):
            cell = table.cell(row_idx, col_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = C_BG_CARD if row_idx % 2 == 1 else RGBColor(24, 34, 52)
            p = cell.text_frame.paragraphs[0]
            p.text = val
            p.font.name = 'Segoe UI'
            p.font.size = Pt(9.5)
            p.font.color.rgb = C_ACCENT_EMERALD if "Suppressed" in val else (C_ACCENT_ROSE if "Gain" in val else C_TEXT_WHITE)

    # Bottom Metric Cards
    add_card(slide12, Inches(0.8), Inches(4.5), Inches(5.7), Inches(2.2), title="Validated Success: Leaky Collusion Suppression", border_color=C_ACCENT_EMERALD)
    tb_s = slide12.shapes.add_textbox(Inches(0.95), Inches(4.95), Inches(5.4), Inches(1.65))
    tf_s = tb_s.text_frame
    tf_s.word_wrap = True
    for b in [
        ("Statistically Significant Reduction", "In Scenario 5, colluder trust share drops from 18.34% to 10.68% (>40% suppression, p < 10^(-6))."),
        ("Substantiated Mechanism", "Honest peers downgrade colluders following protocol non-compliance, restricting the flow of positive evidence into the coalition.")
    ]:
        p_t = tf_s.add_paragraph() if tf_s.paragraphs[0].text else tf_s.paragraphs[0]
        p_t.text = f"• {b[0]}:"
        p_t.font.name = 'Segoe UI'
        p_t.font.size = Pt(10)
        p_t.font.bold = True
        p_t.font.color.rgb = C_TEXT_WHITE
        p_d = tf_s.add_paragraph()
        p_d.text = b[1]
        p_d.font.name = 'Segoe UI'
        p_d.font.size = Pt(9.5)
        p_d.font.color.rgb = C_TEXT_MUTED
        p_d.space_after = Pt(4)

    add_card(slide12, Inches(6.8), Inches(4.5), Inches(5.7), Inches(2.2), title="Computational Overhead & Scaling Bottlenecks", border_color=C_ACCENT_AMBER)
    tb_o = slide12.shapes.add_textbox(Inches(6.95), Inches(4.95), Inches(5.4), Inches(1.65))
    tf_o = tb_o.text_frame
    tf_o.word_wrap = True
    for b in [
        ("Baseline Performance", "Standard EigenTrust takes 28.4 ms; EW-EigenTrust takes 34.2 ms (~20% overhead) in normal 30-node operations."),
        ("Extended Grinding Overhead", "Under 152,000 synthetic receipts, matrix assembly jumps to 2.76 seconds (~92x runtime overhead), demonstrating quadratic scaling under unpruned history.")
    ]:
        p_t = tf_o.add_paragraph() if tf_o.paragraphs[0].text else tf_o.paragraphs[0]
        p_t.text = f"• {b[0]}:"
        p_t.font.name = 'Segoe UI'
        p_t.font.size = Pt(10)
        p_t.font.bold = True
        p_t.font.color.rgb = C_TEXT_WHITE
        p_d = tf_o.add_paragraph()
        p_d.text = b[1]
        p_d.font.name = 'Segoe UI'
        p_d.font.size = Pt(9.5)
        p_d.font.color.rgb = C_TEXT_MUTED
        p_d.space_after = Pt(4)

    add_speaker_notes(
        slide12,
        "Slide 12 presents our key empirical findings from the 1,140 benchmark trials. The results demonstrate both clear successes and critical boundaries.\n\n"
        "Our primary validated success is in Scenario 5, the leaky coalition scenario. Here, colluders interact with honest peers while secretly boosting each other. Under standard EigenTrust, colluders captured 18.34% of global trust. Under EW-EigenTrust, their trust dropped to 10.68%—a 41.8% reduction with extreme statistical significance (p < 10^-6, Cohen's d = 2.45).\n\n"
        "However, in Scenario 6—receipt grinding—colluders actually increased their trust share by +13.38% in standard grinding and +17.92% under extended grinding. This directly refuted our preregistered Hypothesis H-1.\n\n"
        "Finally, regarding computational performance: while matrix assembly takes only 34 ms under normal operations, under extended grinding with 152,000 receipts, runtime jumped to 2.76 seconds—a 92-fold increase that reveals significant scaling bottlenecks when interaction histories are unpruned."
    )

    # ==========================================
    # SLIDE 13: Critical Analysis: Closed-Set Flow Identity, H-1 Refutation, & Scenario 7 Degeneracy
    # ==========================================
    slide13 = prs.slides.add_slide(blank_layout)
    add_header(slide13, "Critical Analysis: Theory, Negative Findings & Degeneracy", slide_num=13)

    add_card(slide13, Inches(0.8), Inches(1.6), Inches(3.7), Inches(5.1), title="Closed-Set Flow Identity")
    tb1 = slide13.shapes.add_textbox(Inches(0.95), Inches(2.2), Inches(3.4), Inches(4.3))
    tf1 = tb1.text_frame
    tf1.word_wrap = True
    tf1.paragraphs[0].text = "• Invariance Theorem:"
    tf1.paragraphs[0].font.name = 'Segoe UI'
    tf1.paragraphs[0].font.size = Pt(10.5)
    tf1.paragraphs[0].font.bold = True
    tf1.paragraphs[0].font.color.rgb = C_ACCENT_CYAN
    p_f = tf1.add_paragraph()
    p_f.text = "T_C = ((1 - alpha) / alpha) * F_(H -> C)"
    p_f.font.name = 'Consolas'
    p_f.font.size = Pt(9.5)
    p_f.font.color.rgb = C_ACCENT_AMBER
    p_f.space_after = Pt(6)

    for b in [
        ("3 Structural Assumptions", "1. Closure: C'_ch = 0\n2. Zero Teleportation: p_c = 0\n3. No Dangling Rows: Sum_j S_cj > 0"),
        ("Vital Finding", "Total coalition trust T_C depends strictly on incoming flow F_(H->C)."),
        ("Invariance Requirement", "Internal reshuffling cannot alter T_C if and only if trust-weighted incoming flow F_(H->C) remains fixed.")
    ]:
        p_t = tf1.add_paragraph()
        p_t.text = f"• {b[0]}:"
        p_t.font.name = 'Segoe UI'
        p_t.font.size = Pt(10)
        p_t.font.bold = True
        p_t.font.color.rgb = C_TEXT_WHITE
        p_d = tf1.add_paragraph()
        p_d.text = b[1]
        p_d.font.name = 'Segoe UI'
        p_d.font.size = Pt(9.5)
        p_d.font.color.rgb = C_TEXT_MUTED
        p_d.space_after = Pt(4)

    add_card(slide13, Inches(4.8), Inches(1.6), Inches(3.7), Inches(5.1), title="Refutation of Hypothesis H-1")
    tb2 = slide13.shapes.add_textbox(Inches(4.95), Inches(2.2), Inches(3.4), Inches(4.3))
    tf2 = tb2.text_frame
    tf2.word_wrap = True
    tf2.paragraphs[0].text = "• Preregistered Expectation:"
    tf2.paragraphs[0].font.name = 'Segoe UI'
    tf2.paragraphs[0].font.size = Pt(10.5)
    tf2.paragraphs[0].font.bold = True
    tf2.paragraphs[0].font.color.rgb = C_ACCENT_CYAN
    p_h1 = tf2.add_paragraph()
    p_h1.text = "H-1: Dispute weighting suppresses colluder trust during receipt grinding."
    p_h1.font.name = 'Segoe UI'
    p_h1.font.size = Pt(9.5)
    p_h1.font.italic = True
    p_h1.font.color.rgb = C_TEXT_WHITE
    p_h1.space_after = Pt(6)

    for b in [
        ("Empirical Refutation", "Colluders gained +13.38% (std) and +17.92% (ext) trust share under grinding!"),
        ("Root Mechanism", "Colluders generated synthetic mutual receipts without triggering disputes; dispute penalty w_dispute was never invoked."),
        ("Academic Candor", "Honest reporting of negative results advances protocol science over unverified marketing.")
    ]:
        p_t = tf2.add_paragraph()
        p_t.text = f"• {b[0]}:"
        p_t.font.name = 'Segoe UI'
        p_t.font.size = Pt(10)
        p_t.font.bold = True
        p_t.font.color.rgb = C_ACCENT_ROSE if "Refutation" in b[0] else C_TEXT_WHITE
        p_d = tf2.add_paragraph()
        p_d.text = b[1]
        p_d.font.name = 'Segoe UI'
        p_d.font.size = Pt(9.5)
        p_d.font.color.rgb = C_TEXT_MUTED
        p_d.space_after = Pt(4)

    add_card(slide13, Inches(8.8), Inches(1.6), Inches(3.7), Inches(5.1), title="Scenario 7 Degeneracy")
    tb3 = slide13.shapes.add_textbox(Inches(8.95), Inches(2.2), Inches(3.4), Inches(4.3))
    tf3 = tb3.text_frame
    tf3.word_wrap = True
    tf3.paragraphs[0].text = "• Zero-Trust Artifact (0.0000):"
    tf3.paragraphs[0].font.name = 'Segoe UI'
    tf3.paragraphs[0].font.size = Pt(10.5)
    tf3.paragraphs[0].font.bold = True
    tf3.paragraphs[0].font.color.rgb = C_ACCENT_CYAN

    for b in [
        ("Surface Reading", "Appears as perfect defense against slander disputes."),
        ("Structural Reality", "Result is mathematically degenerate: colluders had zero incoming trust (F_(H->C) = 0), zero teleportation (p_c = 0), and no dangling rows."),
        ("Topological Disconnection", "Trust was zero because colluders were completely disconnected from the honest subgraph, NOT because disputes adapted."),
        ("Scientific Integrity", "Must be labeled as topological artifact, not general slander resistance.")
    ]:
        p_t = tf3.add_paragraph()
        p_t.text = f"• {b[0]}:"
        p_t.font.name = 'Segoe UI'
        p_t.font.size = Pt(10)
        p_t.font.bold = True
        p_t.font.color.rgb = C_ACCENT_AMBER if "Reality" in b[0] else C_TEXT_WHITE
        p_d = tf3.add_paragraph()
        p_d.text = b[1]
        p_d.font.name = 'Segoe UI'
        p_d.font.size = Pt(9.5)
        p_d.font.color.rgb = C_TEXT_MUTED
        p_d.space_after = Pt(4)

    add_speaker_notes(
        slide13,
        "Slide 13 provides the critical theoretical and empirical analysis demanded by rigorous academic evaluation.\n\n"
        "First, we examine the Closed-Set Flow Identity: T_C equals (1-alpha)/alpha times F_(H->C). This theorem proves that the total trust share of any closed coalition C is strictly bounded by the trust-weighted flow entering it from honest nodes. It relies on three strict assumptions: closure, zero coalition teleportation, and no dangling rows. It proves that internal collusion cannot increase total coalition trust unless trust-weighted incoming flow F_(H->C) is increased.\n\n"
        "Second, we address the refutation of Hypothesis H-1. We hypothesized that dispute weighting would prevent receipt grinding. In reality, colluders gained 13% to 18% more trust. Why? Because colluders exchanged synthetic mutual positive receipts among themselves without ever triggering disputes against honest peers. Dispute weighting was powerless because no disputes occurred.\n\n"
        "Third, we uncover the truth behind Scenario 7. Reporting zero colluder trust looked like perfect slander defense. In reality, it was a structural artifact: colluders had zero incoming edges, zero teleportation, and no dangling rows. They received zero trust purely due to topological disconnection."
    )

    # ==========================================
    # SLIDE 14: Limitations, Conceptual Social-Networking Extension, Conclusion, & Future Work
    # ==========================================
    slide14 = prs.slides.add_slide(blank_layout)
    add_header(slide14, "Limitations, Social-Networking Scope & Conclusion", slide_num=14)

    add_card(slide14, Inches(0.8), Inches(1.6), Inches(3.7), Inches(5.1), title="Acknowledged Limitations")
    tb1 = slide14.shapes.add_textbox(Inches(0.95), Inches(2.2), Inches(3.4), Inches(4.3))
    tf1 = tb1.text_frame
    tf1.word_wrap = True
    for b in [
        ("Tier 3 Evidence Portability", "Bilateral receipts rely on global key oracle D_sim; not fully portable across decentralized third parties without threshold proofs."),
        ("Proof-of-Work Constraints", "Static D=16 provides economic friction, not absolute defense against dedicated ASIC miners."),
        ("Closed-World Simulation", "Evaluated in synthetic 30-50 node simulations; WAN latency and Byzantine churn not fully stress-tested.")
    ]:
        p_t = tf1.add_paragraph() if tf1.paragraphs[0].text else tf1.paragraphs[0]
        p_t.text = f"• {b[0]}:"
        p_t.font.name = 'Segoe UI'
        p_t.font.size = Pt(10.5)
        p_t.font.bold = True
        p_t.font.color.rgb = C_ACCENT_AMBER
        p_d = tf1.add_paragraph()
        p_d.text = b[1]
        p_d.font.name = 'Segoe UI'
        p_d.font.size = Pt(9.5)
        p_d.font.color.rgb = C_TEXT_MUTED
        p_d.space_after = Pt(6)

    add_card(slide14, Inches(4.8), Inches(1.6), Inches(3.7), Inches(5.1), title="Conceptual Social-Networking Scope")
    tb2 = slide14.shapes.add_textbox(Inches(4.95), Inches(2.2), Inches(3.4), Inches(4.3))
    tf2 = tb2.text_frame
    tf2.word_wrap = True
    for b in [
        ("Platform-Neutral Mapping", "Mutual follows map to WoT edges; content attestations map to receipts; social recovery maps to Shamir guardian sets."),
        ("Subjective vs. Objective", "Social follows reflect subjective preference, unlike objective Merkle chunk corruption proofs."),
        ("Strict Scope Boundary", "Formulated as an architectural conceptual extension. No live trials were conducted on Nostr or Matrix.")
    ]:
        p_t = tf2.add_paragraph() if tf2.paragraphs[0].text else tf2.paragraphs[0]
        p_t.text = f"• {b[0]}:"
        p_t.font.name = 'Segoe UI'
        p_t.font.size = Pt(10.5)
        p_t.font.bold = True
        p_t.font.color.rgb = C_ACCENT_CYAN
        p_d = tf2.add_paragraph()
        p_d.text = b[1]
        p_d.font.name = 'Segoe UI'
        p_d.font.size = Pt(9.5)
        p_d.font.color.rgb = C_TEXT_MUTED
        p_d.space_after = Pt(6)

    add_card(slide14, Inches(8.8), Inches(1.6), Inches(3.7), Inches(5.1), title="Conclusion & Future Work")
    tb3 = slide14.shapes.add_textbox(Inches(8.95), Inches(2.2), Inches(3.4), Inches(4.3))
    tf3 = tb3.text_frame
    tf3.word_wrap = True
    for b in [
        ("Core Research Takeaway", "Synthesizes 4-layer PKI stack; validates >40% leaky collusion containment while mathematically bounding spectral reputation limits."),
        ("Future Work — ZK Receipts", "Zero-knowledge proof compression to resolve the 92x runtime scaling bottleneck under large transaction histories."),
        ("Future Work — Threshold Consensus", "Multi-party threshold consensus for decentralized key recovery and portable cross-cluster receipts.")
    ]:
        p_t = tf3.add_paragraph() if tf3.paragraphs[0].text else tf3.paragraphs[0]
        p_t.text = f"• {b[0]}:"
        p_t.font.name = 'Segoe UI'
        p_t.font.size = Pt(10.5)
        p_t.font.bold = True
        p_t.font.color.rgb = C_ACCENT_EMERALD
        p_d = tf3.add_paragraph()
        p_d.text = b[1]
        p_d.font.name = 'Segoe UI'
        p_d.font.size = Pt(9.5)
        p_d.font.color.rgb = C_TEXT_MUTED
        p_d.space_after = Pt(6)

    add_speaker_notes(
        slide14,
        "In our concluding analysis on Slide 14, we review our project limitations, clarify our social networking scope, and summarize future work.\n\n"
        "We candidly acknowledge three key limitations: first, the Tier 3 evidence portability gap; second, the computational ceiling of static Proof-of-Work; and third, that evaluations were conducted in synthetic simulation rather than wild WAN deployments.\n\n"
        "Regarding decentralized social networks: we established a platform-neutral conceptual mapping linking Nostr follows to WoT edges and content attestations to receipts. However, because social trust is subjective, we clearly delineate this as a conceptual architectural contribution without claiming empirical validation.\n\n"
        "In conclusion, this case study demonstrates that vertically integrating cryptographic identity, Web-of-Trust mesh certification, and evidence-weighted spectral trust successfully suppresses leaky collusion by over 40%, while formally establishing the mathematical boundaries of decentralized reputation. Future work will focus on zero-knowledge receipt compression and multi-party decentralized threshold recovery."
    )

    # ==========================================
    # SLIDE 15: References
    # ==========================================
    slide15 = prs.slides.add_slide(blank_layout)
    add_header(slide15, "Authoritative Academic References", slide_num=15)

    add_card(slide15, Inches(0.8), Inches(1.6), Inches(11.733), Inches(5.1), title="IEEE Formatted Bibliography")
    tb_ref = slide15.shapes.add_textbox(Inches(0.95), Inches(2.1), Inches(11.4), Inches(4.4))
    tf_ref = tb_ref.text_frame
    tf_ref.word_wrap = True

    references = [
        ("[1]", "Decentralized Identity Foundation (DIF), \"Decentralized Identifiers (DIDs) v1.0: Core Architecture, Data Model, and Representations,\" W3C Recommendation, 2022. [Online]. Available: https://www.w3.org/TR/did-core/"),
        ("[2]", "C. Ellison, B. Frantz, B. Lampson, R. Rivest, B. Thomas, and T. Ylonen, \"SPKI Certificate Theory,\" IETF RFC 2693, Sep. 1999."),
        ("[3]", "S. D. Kamvar, M. T. Schlosser, and H. Garcia-Molina, \"The EigenTrust algorithm for reputation management in P2P networks,\" in Proc. 12th Int. Conf. World Wide Web (WWW '03), Budapest, Hungary, 2003, pp. 640-651."),
        ("[4]", "S. Nakamoto, \"Bitcoin: A Peer-to-Peer Electronic Cash System,\" White Paper, 2008. [Online]. Available: https://bitcoin.org/bitcoin.pdf"),
        ("[5]", "A. Shamir, \"How to share a secret,\" Communications of the ACM, vol. 22, no. 11, pp. 612-613, Nov. 1979."),
        ("[6]", "P. R. Zimmermann, The Official PGP User's Guide, Cambridge, MA, USA: MIT Press, 1995."),
        ("[7]", "D. Cooper, S. Santesson, S. Farrell, S. Boeyen, R. Housley, and W. Polk, \"Internet X.509 Public Key Infrastructure Certificate and Certificate Revocation List (CRL) Profile,\" IETF RFC 5280, May 2008.")
    ]

    for ref_id, ref_text in references:
        p = tf_ref.add_paragraph() if tf_ref.paragraphs[0].text else tf_ref.paragraphs[0]
        p.text = f"{ref_id}  {ref_text}"
        p.font.name = 'Segoe UI'
        p.font.size = Pt(9.5)
        p.font.color.rgb = C_TEXT_MUTED
        p.space_after = Pt(7)

    add_speaker_notes(
        slide15,
        "Slide 15 concludes our presentation with our complete list of authoritative references, formatted in standard IEEE style.\n\n"
        "These seven citations represent the primary theoretical foundations of our work: W3C Decentralized Identifiers for Layer 1; SPKI RFC 2693, Zimmermann's PGP, and RFC 5280 for Layer 2 PKI and revocation; Kamvar et al.'s seminal EigenTrust paper for Layer 3 spectral reputation; Nakamoto's Proof-of-Work for computational admission; and Shamir's 1979 secret sharing scheme for Layer 4 key recovery.\n\n"
        "All claims, formulas, and baseline parameters in this defense have been verified against these foundational texts and our preregistered experimental records.\n\n"
        "Thank you very much for your time and attention. I am now open to questions from the evaluation committee."
    )

    out_path = "deliverable_reports/PKI_Trust_Management_Final_Presentation.pptx"
    prs.save(out_path)
    print(f"Successfully generated {out_path} with {len(prs.slides)} slides.")

if __name__ == '__main__':
    build_presentation()
