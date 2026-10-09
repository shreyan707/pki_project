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

    # Theme Palette (Strictly 6-digit hex equivalents in RGBColor)
    C_BG_DARK = RGBColor(11, 17, 32)      # Deep Navy #0B1120
    C_BG_CARD = RGBColor(30, 41, 59)      # Slate Card #1E293B
    C_BORDER_CARD = RGBColor(51, 65, 85)  # Border #334155
    C_TEXT_WHITE = RGBColor(248, 250, 252)# White #F8FAFC
    C_TEXT_MUTED = RGBColor(148, 163, 184)# Slate 400 #94A3B8
    C_TEXT_SUBTLE = RGBColor(100, 116, 139)# Slate 500 #64748B
    C_ACCENT_CYAN = RGBColor(56, 189, 248)# Sky/Cyan #38BDF8
    C_ACCENT_BLUE = RGBColor(37, 99, 235) # Blue #2563EB
    C_ACCENT_EMERALD = RGBColor(16, 185, 129)# Emerald #10B981
    C_ACCENT_AMBER = RGBColor(245, 158, 11)# Amber #F59E0B
    C_ACCENT_ROSE = RGBColor(244, 63, 94) # Rose #F43F5E

    def set_slide_background(slide):
        background = slide.background
        fill = background.fill
        fill.solid()
        fill.fore_color.rgb = C_BG_DARK

    def add_header(slide, title, category="PKI-BASED TRUST MANAGEMENT FOR P2P & SOCIAL NETWORKS", slide_num=None):
        set_slide_background(slide)
        
        # Category Tag
        cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.3))
        tf_cat = cat_box.text_frame
        tf_cat.word_wrap = True
        p_cat = tf_cat.paragraphs[0]
        p_cat.text = category.upper()
        p_cat.font.name = 'Segoe UI'
        p_cat.font.size = Pt(9.5)
        p_cat.font.bold = True
        p_cat.font.color.rgb = C_ACCENT_CYAN

        # Title
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.7), Inches(11.7), Inches(0.6))
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

    def add_card(slide, left, top, width, height, title=None, border_color=C_BORDER_CARD):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = C_BG_CARD
        card.line.color.rgb = border_color
        card.line.width = Pt(1)

        if title:
            tb = slide.shapes.add_textbox(left + Inches(0.15), top + Inches(0.15), width - Inches(0.3), Inches(0.4))
            tf = tb.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.text = title
            p.font.name = 'Segoe UI'
            p.font.size = Pt(13)
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

    # Accent decorative block
    dec = slide1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.2), Inches(11.733), Inches(5.0))
    dec.fill.solid()
    dec.fill.fore_color.rgb = C_BG_CARD
    dec.line.color.rgb = C_ACCENT_BLUE
    dec.line.width = Pt(2)

    # Main Title Frame
    t_box = slide1.shapes.add_textbox(Inches(1.2), Inches(1.6), Inches(10.9), Inches(2.2))
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
    p1.font.size = Pt(24)
    p1.font.bold = True
    p1.font.color.rgb = C_TEXT_WHITE
    p1.space_after = Pt(10)

    p2 = tf1.add_paragraph()
    p2.text = "A Vertically Integrated Four-Layer Architecture Synthesizing Self-Sovereign Identity, Web-of-Trust PKI, Evidence-Weighted Spectral Reputation, and Threshold Governance"
    p2.font.name = 'Segoe UI'
    p2.font.size = Pt(13)
    p2.font.color.rgb = C_TEXT_MUTED

    # Author & Academic Meta Grid
    card_auth = slide1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.2), Inches(4.2), Inches(5.3), Inches(1.6))
    card_auth.fill.solid()
    card_auth.fill.fore_color.rgb = RGBColor(15, 23, 42)
    card_auth.line.color.rgb = C_BORDER_CARD
    tb_a = slide1.shapes.add_textbox(Inches(1.4), Inches(4.3), Inches(4.9), Inches(1.4))
    tf_a = tb_a.text_frame
    p_a1 = tf_a.paragraphs[0]
    p_a1.text = "CANDIDATE DETAILS"
    p_a1.font.size = Pt(9.5)
    p_a1.font.bold = True
    p_a1.font.color.rgb = C_ACCENT_CYAN
    p_a2 = tf_a.add_paragraph()
    p_a2.text = "Shreyan Nayak (Reg. No: 23BKT0039)\nB.Tech Computer Science & Engineering\nSCOPE, Vellore Institute of Technology (VIT), Chennai"
    p_a2.font.size = Pt(11)
    p_a2.font.color.rgb = C_TEXT_WHITE

    card_meta = slide1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(4.2), Inches(5.3), Inches(1.6))
    card_meta.fill.solid()
    card_meta.fill.fore_color.rgb = RGBColor(15, 23, 42)
    card_meta.line.color.rgb = C_BORDER_CARD
    tb_m = slide1.shapes.add_textbox(Inches(7.0), Inches(4.3), Inches(4.9), Inches(1.4))
    tf_m = tb_m.text_frame
    p_m1 = tf_m.paragraphs[0]
    p_m1.text = "COURSE & ASSESSMENT"
    p_m1.font.size = Pt(9.5)
    p_m1.font.bold = True
    p_m1.font.color.rgb = C_ACCENT_CYAN
    p_m2 = tf_m.add_paragraph()
    p_m2.text = "Course: Information Security / PKI Case Study (VL2026270102689)\nAssessment Task: Case Study 1 (CS1)\nTechnical Baseline: v9.0-FINAL-FREEZE (October 9, 2026)"
    p_m2.font.size = Pt(11)
    p_m2.font.color.rgb = C_TEXT_WHITE

    add_speaker_notes(
        slide1,
        "Good morning, esteemed evaluators and committee members. I am Shreyan Nayak, registration number 23BKT0039, from the School of Computer Science and Engineering at VIT Chennai. Today, I am defending my final research case study titled: 'PKI-Based Trust Management for Peer-to-Peer File-Sharing and Social Networking Platforms.'\n\n"
        "This project investigates how to bridge the fundamental divide between Public Key Infrastructure and decentralized peer-to-peer systems. In client-server environments, trust is traditionally established by convention through centralized Certificate Authorities. However, decentralized P2P networks require open, censorship-resistant collaboration where central roots of trust cannot exist.\n\n"
        "Over the course of this presentation, I will walk you through our vertically integrated four-layer architecture, explain its cryptographic and mathematical mechanisms, present our preregistered empirical benchmark across 1,140 trial evaluations, and candidly examine both our validated successes—such as over 40% leaky collusion suppression—and our mathematically established theoretical limitations, including the Closed-Set Flow Identity and the refutation of preregistered Hypothesis H-1."
    )

    # ==========================================
    # SLIDE 2: Introduction and Background
    # ==========================================
    slide2 = prs.slides.add_slide(blank_layout)
    add_header(slide2, "Introduction: The Decentralized Trust Dilemma", slide_num=2)

    # Card 1: The Centralized PKI Paradox
    add_card(slide2, Inches(0.8), Inches(1.6), Inches(3.7), Inches(5.1), title="The Centralized PKI Dilemma")
    tb = slide2.shapes.add_textbox(Inches(0.95), Inches(2.2), Inches(3.4), Inches(4.3))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.paragraphs[0].text = "• Classical PKI relies on centralized Certificate Authorities (CAs) by convention."
    tf.paragraphs[0].font.size = Pt(11)
    tf.paragraphs[0].font.color.rgb = C_TEXT_WHITE
    tf.paragraphs[0].space_after = Pt(8)
    for b in [
        "• Single Point of Failure: Root CA compromise undermines the entire trust domain.",
        "• Censorship Vulnerability: Central authorities can arbitrarily revoke or withhold credentials.",
        "• Structural Mismatch: Hierarchical tree trust contradicts decentralized P2P topologies [1], [7]."
    ]:
        p = tf.add_paragraph()
        p.text = b
        p.font.size = Pt(11)
        p.font.color.rgb = C_TEXT_MUTED
        p.space_after = Pt(8)

    # Card 2: The Open Network Attack Surface
    add_card(slide2, Inches(4.8), Inches(1.6), Inches(3.7), Inches(5.1), title="Open Network Attack Vectors")
    tb = slide2.shapes.add_textbox(Inches(4.95), Inches(2.2), Inches(3.4), Inches(4.3))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.paragraphs[0].text = "• Zero-Cost Sybil Attacks: Pseudonyms generated freely to manipulate voting quorums."
    tf.paragraphs[0].font.size = Pt(11)
    tf.paragraphs[0].font.color.rgb = C_TEXT_WHITE
    tf.paragraphs[0].space_after = Pt(8)
    for b in [
        "• Strategic Collusion Rings: Cliques award mutual unearned positive ratings.",
        "• Receipt Grinding: Sybils generate synthetic transaction volumes to harvest reputation.",
        "• Data Poisoning & Slander: Servers serve corrupted chunks; downloaders file false complaints [3], [4]."
    ]:
        p = tf.add_paragraph()
        p.text = b
        p.font.size = Pt(11)
        p.font.color.rgb = C_TEXT_MUTED
        p.space_after = Pt(8)

    # Card 3: Dual Application Paradigms
    add_card(slide2, Inches(8.8), Inches(1.6), Inches(3.7), Inches(5.1), title="Dual Application Domains")
    tb = slide2.shapes.add_textbox(Inches(8.95), Inches(2.2), Inches(3.4), Inches(4.3))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.paragraphs[0].text = "• P2P File Sharing (BitTorrent, IPFS):"
    tf.paragraphs[0].font.size = Pt(11)
    tf.paragraphs[0].font.bold = True
    tf.paragraphs[0].font.color.rgb = C_ACCENT_EMERALD
    p_f = tf.add_paragraph()
    p_f.text = "Operational & transactional. Governs chunk integrity, content authenticity, seeder reciprocity, and non-repudiation."
    p_f.font.size = Pt(10.5)
    p_f.font.color.rgb = C_TEXT_MUTED
    p_f.space_after = Pt(10)

    p_s_t = tf.add_paragraph()
    p_s_t.text = "• Decentralized Social (Nostr, Matrix):"
    p_s_t.font.size = Pt(11)
    p_s_t.font.bold = True
    p_s_t.font.color.rgb = C_ACCENT_CYAN
    p_s = tf.add_paragraph()
    p_s.text = "Relational & subjective. Governs follow assertions, message origins, spam mitigation, and guardian recovery."
    p_s.font.size = Pt(10.5)
    p_s.font.color.rgb = C_TEXT_MUTED
    p_s.space_after = Pt(10)

    p_note = tf.add_paragraph()
    p_note.text = "Boundary: File sharing is empirically validated; social networking is conceptually mapped."
    p_note.font.size = Pt(9.5)
    p_note.font.italic = True
    p_note.font.color.rgb = C_ACCENT_AMBER

    add_speaker_notes(
        slide2,
        "To contextualize our investigation, consider the central trust dilemma in distributed networks. Traditional PKI depends entirely on hierarchical Certification Authorities. If you access a secure website, your browser trusts a pre-installed root certificate. But in a peer-to-peer network like BitTorrent or Nostr, there is no root CA. Introducing one creates a single point of failure and invites administrative censorship.\n\n"
        "However, completely abandoning identity infrastructure creates a catastrophic attack surface. Without identity barriers, adversaries can launch Sybil attacks—generating millions of cryptographic keys for zero cost—to swamp voting quorums. Strategic colluders can form mutual rating cliques to harvest reputation, while malicious uploaders can poison content and downloaders can slander honest providers.\n\n"
        "We address this challenge across two complementary P2P paradigms: transactional file sharing, which deals with concrete chunk integrity and seeder reciprocity, and social networking, which deals with relational endorsements and spam moderation. As we will emphasize throughout, file sharing was fully implemented and empirically evaluated, whereas social networking is formulated as an architectural conceptual extension."
    )

    # Save initial slides to verify progress
    prs.save("PKI_Trust_Management_Final_Presentation.pptx")
    print("Base slides created. Continuing with all 15 slides...")

build_presentation()
