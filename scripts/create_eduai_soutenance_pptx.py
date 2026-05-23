from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Inches, Pt


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "EduAI_Soutenance_19_20.pptx"
LOGO_ESTE = ROOT / "rapport" / "figures" / "logo_este.png"

W = 13.333
H = 7.5

BLUE = RGBColor(37, 99, 235)
DARK = RGBColor(30, 41, 59)
ACCENT = RGBColor(184, 91, 42)
BG = RGBColor(248, 250, 252)
WHITE = RGBColor(255, 255, 255)
MUTED = RGBColor(100, 116, 139)
LIGHT = RGBColor(226, 232, 240)
GREEN = RGBColor(22, 163, 74)
RED = RGBColor(220, 38, 38)
AMBER = RGBColor(217, 119, 6)


def cm(x):
    return Inches(x)


def rgb(hex_value):
    hex_value = hex_value.strip("#")
    return RGBColor(
        int(hex_value[0:2], 16),
        int(hex_value[2:4], 16),
        int(hex_value[4:6], 16),
    )


def set_fill(shape, color):
    shape.fill.solid()
    shape.fill.fore_color.rgb = color


def set_line(shape, color=LIGHT, width=1):
    shape.line.color.rgb = color
    shape.line.width = Pt(width)


def no_line(shape):
    shape.line.fill.background()


def add_rect(slide, x, y, w, h, fill=WHITE, line=LIGHT, radius=True):
    kind = MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE
    shape = slide.shapes.add_shape(kind, cm(x), cm(y), cm(w), cm(h))
    set_fill(shape, fill)
    if line is None:
        no_line(shape)
    else:
        set_line(shape, line)
    return shape


def add_text(
    slide,
    text,
    x,
    y,
    w,
    h,
    size=18,
    color=DARK,
    bold=False,
    align=PP_ALIGN.LEFT,
    valign=MSO_ANCHOR.TOP,
    font="Aptos",
    line_spacing=None,
):
    box = slide.shapes.add_textbox(cm(x), cm(y), cm(w), cm(h))
    tf = box.text_frame
    tf.clear()
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    tf.vertical_anchor = valign
    p = tf.paragraphs[0]
    p.alignment = align
    if line_spacing:
        p.line_spacing = line_spacing
    run = p.add_run()
    run.text = text
    run.font.name = font
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    return box


def add_multiline(slide, lines, x, y, w, h, size=15, color=DARK, gap=0.18):
    cy = y
    for line in lines:
        add_text(slide, line, x, cy, w, 0.3, size=size, color=color)
        cy += 0.3 + gap


def add_badge(slide, text, x, y, w, fill=BLUE, color=WHITE, size=11):
    shape = add_rect(slide, x, y, w, 0.35, fill=fill, line=None)
    tf = shape.text_frame
    tf.clear()
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = text
    r.font.name = "Aptos"
    r.font.size = Pt(size)
    r.font.bold = True
    r.font.color.rgb = color
    return shape


def add_title(slide, eyebrow, title, subtitle=None, dark=False):
    color = WHITE if dark else DARK
    muted = rgb("CBD5E1") if dark else MUTED
    if eyebrow:
        add_text(slide, eyebrow.upper(), 0.65, 0.35, 4.5, 0.25, 9, BLUE if not dark else rgb("93C5FD"), True)
    add_text(slide, title, 0.65, 0.62, 9.2, 0.55, 26, color, True)
    if subtitle:
        add_text(slide, subtitle, 0.67, 1.16, 8.4, 0.35, 12.5, muted)


def add_footer(slide, n, dark=False):
    color = rgb("CBD5E1") if dark else MUTED
    add_text(slide, "EduAI - Soutenance PFE 2025/2026", 0.65, 7.16, 4.2, 0.2, 8.5, color)
    add_text(slide, f"{n:02d}/15", 12.05, 7.16, 0.65, 0.2, 8.5, color, align=PP_ALIGN.RIGHT)


def add_bg(slide, color=BG):
    bg = slide.background
    bg.fill.solid()
    bg.fill.fore_color.rgb = color


def add_brand_mark(slide, x, y, dark=False):
    outer = add_rect(slide, x, y, 0.48, 0.48, fill=BLUE, line=None)
    tf = outer.text_frame
    tf.clear()
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = "E"
    r.font.name = "Aptos Display"
    r.font.size = Pt(18)
    r.font.bold = True
    r.font.color.rgb = WHITE
    add_text(slide, "EduAI", x + 0.58, y + 0.07, 1.3, 0.25, 14, WHITE if dark else DARK, True)


def add_notes(slide, notes):
    slide.notes_slide.notes_text_frame.text = notes.strip()


def add_card(slide, title, body, x, y, w, h, accent=BLUE, value=None):
    add_rect(slide, x, y, w, h, WHITE, LIGHT)
    add_rect(slide, x, y, 0.08, h, accent, None, radius=False)
    if value:
        add_text(slide, value, x + 0.28, y + 0.22, w - 0.4, 0.45, 26, accent, True)
        add_text(slide, title, x + 0.3, y + 0.82, w - 0.4, 0.25, 11, DARK, True)
        add_text(slide, body, x + 0.3, y + 1.15, w - 0.45, h - 1.25, 10.5, MUTED)
    else:
        add_text(slide, title, x + 0.28, y + 0.2, w - 0.4, 0.28, 13, DARK, True)
        add_text(slide, body, x + 0.28, y + 0.62, w - 0.45, h - 0.7, 10.5, MUTED)


def add_step(slide, num, title, body, x, y, w, h, accent=BLUE):
    add_rect(slide, x, y, w, h, WHITE, LIGHT)
    add_rect(slide, x + 0.2, y + 0.22, 0.48, 0.48, accent, None)
    add_text(slide, num, x + 0.2, y + 0.31, 0.48, 0.2, 11, WHITE, True, align=PP_ALIGN.CENTER)
    add_text(slide, title, x + 0.82, y + 0.2, w - 1.0, 0.28, 13, DARK, True)
    add_text(slide, body, x + 0.82, y + 0.58, w - 1.0, 0.48, 10.5, MUTED)


def add_arrow_text(slide, x, y):
    add_text(slide, "->", x, y, 0.35, 0.25, 18, BLUE, True, align=PP_ALIGN.CENTER)


def browser_mock(slide, x, y, w, h, title, pills=None, accent=BLUE):
    add_rect(slide, x, y, w, h, WHITE, LIGHT)
    add_rect(slide, x, y, w, 0.42, rgb("F8FAFC"), LIGHT, radius=True)
    for i, c in enumerate([rgb("EF4444"), rgb("F59E0B"), rgb("22C55E")]):
        dot = slide.shapes.add_shape(MSO_SHAPE.OVAL, cm(x + 0.18 + i * 0.18), cm(y + 0.15), cm(0.08), cm(0.08))
        set_fill(dot, c)
        no_line(dot)
    add_text(slide, title, x + 0.55, y + 0.13, w - 0.7, 0.18, 7.5, MUTED)
    add_rect(slide, x + 0.25, y + 0.68, w - 0.5, 0.45, fill=rgb("EFF6FF"), line=None)
    add_text(slide, title.split(" - ")[0], x + 0.42, y + 0.8, w - 0.8, 0.18, 10, DARK, True)
    yy = y + 1.35
    if pills:
        for label, color in pills[:4]:
            add_badge(slide, label, x + 0.35, yy, min(w - 0.7, 1.65), fill=color, size=7.5)
            yy += 0.45
    else:
        for i in range(4):
            add_rect(slide, x + 0.35, yy, w - 0.7, 0.16, fill=rgb("E2E8F0"), line=None)
            yy += 0.38
    add_rect(slide, x + w - 0.75, y + h - 0.55, 0.43, 0.2, accent, None)


def chat_mock(slide, x, y, w, h):
    add_rect(slide, x, y, w, h, WHITE, LIGHT)
    add_text(slide, "Q&A RAG", x + 0.3, y + 0.23, 1.8, 0.28, 13, DARK, True)
    add_badge(slide, "Streaming SSE", x + w - 1.55, y + 0.2, 1.2, fill=rgb("DBEAFE"), color=BLUE, size=8)
    add_rect(slide, x + 0.35, y + 0.8, w - 1.3, 0.58, rgb("EFF6FF"), rgb("BFDBFE"))
    add_text(slide, "Quelle est l'idée principale du chapitre ?", x + 0.55, y + 0.98, w - 1.8, 0.18, 10, DARK)
    add_rect(slide, x + 0.9, y + 1.65, w - 1.25, 1.25, rgb("F8FAFC"), LIGHT)
    add_text(slide, "Réponse pédagogique", x + 1.12, y + 1.86, w - 1.7, 0.2, 11.5, BLUE, True)
    add_multiline(
        slide,
        [
            "Définition claire du concept",
            "Explication avec le contexte du cours",
            "À retenir + sources [1] [2]",
        ],
        x + 1.12,
        y + 2.18,
        w - 1.7,
        0.9,
        8.8,
        MUTED,
        0.05,
    )
    for i, label in enumerate(["Source 1 - p. 4", "Source 2 - p. 7", "Source 3 - p. 9"]):
        add_rect(slide, x + 0.55 + i * 1.65, y + 3.15, 1.45, 0.38, rgb("FFF7ED"), rgb("FED7AA"))
        add_text(slide, label, x + 0.65 + i * 1.65, y + 3.26, 1.2, 0.15, 7.5, ACCENT, True)


def summary_mock(slide, x, y, w, h):
    add_rect(slide, x, y, w, h, WHITE, LIGHT)
    add_text(slide, "Résumé pédagogique", x + 0.3, y + 0.25, 2.5, 0.25, 13, DARK, True)
    add_badge(slide, "Export PDF", x + w - 1.35, y + 0.22, 1.0, fill=ACCENT, size=8)
    for i, chapter in enumerate(["Chapitre 1", "Chapitre 2", "Chapitre 3"]):
        yy = y + 0.85 + i * 1.05
        add_rect(slide, x + 0.35, yy, w - 0.7, 0.78, rgb("F8FAFC"), LIGHT)
        add_text(slide, chapter, x + 0.55, yy + 0.15, 1.2, 0.18, 9.5, BLUE, True)
        add_rect(slide, x + 1.55, yy + 0.18, w - 2.2, 0.09, rgb("CBD5E1"), None)
        add_rect(slide, x + 0.55, yy + 0.48, w - 1.1, 0.08, rgb("E2E8F0"), None)


def quiz_flash_mind_mock(slide, x, y, w, h):
    card_w = (w - 0.3) / 3
    items = [
        ("Quiz", "Tester", BLUE),
        ("Flashcards", "Mémoriser", ACCENT),
        ("Mindmap", "Relier", GREEN),
    ]
    for i, (title, action, color) in enumerate(items):
        xx = x + i * (card_w + 0.15)
        add_rect(slide, xx, y, card_w, h, WHITE, LIGHT)
        add_text(slide, title, xx + 0.22, y + 0.22, card_w - 0.4, 0.22, 12, DARK, True)
        add_badge(slide, action, xx + 0.22, y + 0.6, 1.05, fill=color, size=8)
        if title == "Quiz":
            for j in range(4):
                add_rect(slide, xx + 0.26, y + 1.1 + j * 0.33, card_w - 0.52, 0.18, rgb("EFF6FF") if j == 1 else rgb("F8FAFC"), rgb("DBEAFE"))
        elif title == "Flashcards":
            add_rect(slide, xx + 0.34, y + 1.05, card_w - 0.68, 1.05, rgb("FFF7ED"), rgb("FED7AA"))
            add_text(slide, "Recto", xx + 0.5, y + 1.22, card_w - 1.0, 0.18, 9, ACCENT, True, align=PP_ALIGN.CENTER)
            add_text(slide, "Question courte", xx + 0.45, y + 1.58, card_w - 0.9, 0.18, 8, DARK, align=PP_ALIGN.CENTER)
        else:
            center = slide.shapes.add_shape(MSO_SHAPE.OVAL, cm(xx + card_w / 2 - 0.28), cm(y + 1.15), cm(0.56), cm(0.56))
            set_fill(center, rgb("DCFCE7"))
            set_line(center, rgb("BBF7D0"))
            add_text(slide, "Concept", xx + card_w / 2 - 0.36, y + 1.33, 0.72, 0.12, 6.5, GREEN, True, align=PP_ALIGN.CENTER)
            for dx, dy in [(-0.55, -0.22), (0.55, -0.22), (-0.55, 0.58), (0.55, 0.58)]:
                node = slide.shapes.add_shape(MSO_SHAPE.OVAL, cm(xx + card_w / 2 + dx - 0.2), cm(y + 1.43 + dy), cm(0.4), cm(0.4))
                set_fill(node, WHITE)
                set_line(node, rgb("BBF7D0"))


def exam_mock(slide, x, y, w, h):
    add_rect(slide, x, y, w, h, WHITE, LIGHT)
    add_text(slide, "Mode examen", x + 0.3, y + 0.25, 2.2, 0.25, 13, DARK, True)
    add_badge(slide, "24:36", x + w - 1.25, y + 0.22, 0.9, fill=RED, size=8)
    add_rect(slide, x + 0.35, y + 0.85, w - 0.7, 0.95, rgb("F8FAFC"), LIGHT)
    add_text(slide, "Question 4 / 20", x + 0.55, y + 1.05, 1.7, 0.2, 10, BLUE, True)
    add_rect(slide, x + 0.55, y + 1.43, w - 1.1, 0.1, rgb("CBD5E1"), None)
    add_rect(slide, x + 0.35, y + 2.12, 1.55, 1.05, rgb("EFF6FF"), rgb("BFDBFE"))
    add_text(slide, "Score", x + 0.68, y + 2.33, 0.8, 0.2, 11, MUTED, True, align=PP_ALIGN.CENTER)
    add_text(slide, "82%", x + 0.62, y + 2.62, 0.9, 0.32, 22, BLUE, True, align=PP_ALIGN.CENTER)
    add_rect(slide, x + 2.1, y + 2.12, 1.55, 1.05, rgb("ECFDF5"), rgb("BBF7D0"))
    add_text(slide, "Note", x + 2.42, y + 2.33, 0.8, 0.2, 11, MUTED, True, align=PP_ALIGN.CENTER)
    add_text(slide, "B", x + 2.5, y + 2.58, 0.62, 0.35, 24, GREEN, True, align=PP_ALIGN.CENTER)
    add_rect(slide, x + 3.85, y + 2.12, w - 4.2, 1.05, rgb("FFF7ED"), rgb("FED7AA"))
    add_text(slide, "Corrections pédagogiques", x + 4.1, y + 2.38, w - 4.7, 0.22, 10, ACCENT, True)


def slide_title(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_bg(slide, WHITE)
    add_rect(slide, 0, 0, 13.333, 7.5, WHITE, None, radius=False)
    add_rect(slide, 8.1, 0, 5.25, 7.5, rgb("EFF6FF"), None, radius=False)
    add_rect(slide, 8.7, 0.72, 3.9, 5.85, WHITE, rgb("BFDBFE"))
    browser_mock(
        slide,
        9.05,
        1.08,
        3.2,
        2.1,
        "EduAI - Workspace",
        [("Q&A RAG", BLUE), ("Résumé", ACCENT), ("Quiz", GREEN)],
    )
    add_rect(slide, 9.05, 3.5, 3.2, 1.25, WHITE, LIGHT)
    add_text(slide, "PDF -> IA -> Révision", 9.35, 3.88, 2.5, 0.3, 15, DARK, True, align=PP_ALIGN.CENTER)
    add_rect(slide, 9.05, 5.05, 1.48, 0.85, rgb("DBEAFE"), None)
    add_text(slide, "Comprendre", 9.25, 5.37, 1.08, 0.18, 9, BLUE, True, align=PP_ALIGN.CENTER)
    add_rect(slide, 10.77, 5.05, 1.48, 0.85, rgb("FFF7ED"), None)
    add_text(slide, "S'évaluer", 10.99, 5.37, 1.02, 0.18, 9, ACCENT, True, align=PP_ALIGN.CENTER)

    add_brand_mark(slide, 0.65, 0.55)
    add_text(slide, "Assistant Pédagogique Intelligent", 0.65, 1.42, 5.6, 0.42, 17, BLUE, True)
    add_text(slide, "EduAI", 0.62, 1.88, 5.8, 0.75, 44, DARK, True, font="Aptos Display")
    add_text(
        slide,
        "Transformer un PDF de cours en espace de compréhension, de révision et d'auto-évaluation.",
        0.67,
        2.8,
        5.7,
        0.72,
        18,
        MUTED,
    )
    add_rect(slide, 0.65, 3.78, 5.9, 0.02, BLUE, None, radius=False)
    add_multiline(
        slide,
        [
            "Projet de Fin d'Études - 2025/2026",
            "EL Mehdi HACHAMI",
            "Bachelor IA & Sciences des Données",
            "EST Essaouira - Université Cadi Ayyad",
            "Encadrant : Pr. El Mahdi ERRAJI",
            "Entreprise : 2Pi eLearning SARL",
        ],
        0.68,
        4.05,
        5.7,
        2.0,
        12,
        DARK,
        0.06,
    )
    if LOGO_ESTE.exists():
        slide.shapes.add_picture(str(LOGO_ESTE), cm(0.68), cm(6.58), width=cm(0.42))
    add_footer(slide, 1)
    add_notes(
        slide,
        """
Bonjour Mesdames et Messieurs les membres du jury. Je suis EL Mehdi HACHAMI, étudiant en Bachelor Ingénierie Informatique en Intelligence Artificielle et Sciences des Données. Aujourd'hui, je vais vous présenter mon projet de fin d'études : EduAI, un assistant pédagogique intelligent. L'idée principale est simple : au lieu de laisser l'étudiant seul devant un PDF long et passif, EduAI transforme ce document en un espace interactif pour comprendre, réviser et s'auto-évaluer.
""",
    )


def slide_problem(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_bg(slide, BG)
    add_title(slide, "Constat", "Le PDF ne suffit pas pour apprendre", "Un support utile pour diffuser, mais trop passif pour réviser.")
    add_footer(slide, 2)

    add_rect(slide, 0.8, 1.75, 3.35, 4.25, WHITE, LIGHT)
    add_text(slide, "PDF dense", 1.15, 2.05, 2.6, 0.28, 16, DARK, True, align=PP_ALIGN.CENTER)
    for i in range(11):
        add_rect(slide, 1.2, 2.65 + i * 0.22, 2.45 if i % 3 else 1.9, 0.06, rgb("CBD5E1"), None)
    add_rect(slide, 1.3, 5.25, 2.2, 0.32, rgb("FEE2E2"), None)
    add_text(slide, "Lecture passive", 1.58, 5.34, 1.6, 0.12, 8, RED, True, align=PP_ALIGN.CENTER)

    add_arrow_text(slide, 4.45, 3.55)
    cards = [
        ("Comprendre seul", "Le document n'explique pas selon les besoins de l'étudiant.", BLUE),
        ("Résumer manuellement", "Identifier l'essentiel prend du temps et reste subjectif.", ACCENT),
        ("S'évaluer difficilement", "Pas de quiz, pas de feedback, pas de progression mesurable.", RED),
    ]
    y = 1.78
    for title, body, color in cards:
        add_card(slide, title, body, 5.05, y, 3.15, 1.08, color)
        y += 1.35
    add_rect(slide, 8.75, 1.78, 3.8, 4.18, DARK, None)
    add_text(slide, "Problème central", 9.18, 2.2, 3.0, 0.28, 14, rgb("BFDBFE"), True, align=PP_ALIGN.CENTER)
    add_text(
        slide,
        "L'étudiant doit comprendre, mémoriser et vérifier son niveau sans outil interactif adapté.",
        9.15,
        2.88,
        3.05,
        1.35,
        21,
        WHITE,
        True,
        align=PP_ALIGN.CENTER,
        valign=MSO_ANCHOR.MIDDLE,
    )
    add_badge(slide, "Opportunité : apprentissage actif", 9.25, 4.95, 2.8, fill=ACCENT, size=9.5)
    add_notes(
        slide,
        """
Le point de départ du projet vient d'une situation très courante dans l'enseignement supérieur marocain. L'étudiant reçoit un PDF de cours, parfois très long, parfois très dense, et il doit se débrouiller seul pour identifier l'essentiel, comprendre les notions, créer ses fiches, préparer des questions et vérifier s'il est prêt pour l'examen. Le PDF est donc utile comme support de distribution, mais il ne suffit pas comme outil d'apprentissage.
""",
    )


def slide_opportunity(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_bg(slide, WHITE)
    add_title(slide, "Marché", "Pourquoi maintenant au Maroc ?", "Un contexte favorable : étudiants connectés, besoin réel et transition numérique.")
    add_footer(slide, 3)

    metrics = [
        ("1,2M", "TAM", "Étudiants dans l'enseignement supérieur au Maroc", BLUE),
        ("400k", "SAM", "Étudiants connectés disposant d'un ordinateur ou smartphone", ACCENT),
        ("5k", "SOM A1", "Objectif réaliste d'utilisateurs la première année", GREEN),
    ]
    x = 0.85
    for value, title, body, color in metrics:
        add_card(slide, title, body, x, 1.75, 3.55, 2.25, color, value=value)
        x += 4.05

    add_rect(slide, 0.85, 4.65, 11.65, 1.35, rgb("F8FAFC"), LIGHT)
    add_text(slide, "Contexte favorable", 1.25, 4.98, 2.2, 0.26, 14, DARK, True)
    add_text(
        slide,
        "Maroc Digital 2030 + usage croissant du numérique éducatif + besoin d'outils accessibles et adaptés aux cours réels.",
        3.25,
        4.98,
        8.4,
        0.5,
        16,
        MUTED,
    )
    add_badge(slide, "Accessibilité", 1.25, 5.56, 1.25, fill=rgb("DBEAFE"), color=BLUE)
    add_badge(slide, "Web / Mobile", 2.68, 5.56, 1.25, fill=rgb("FFF7ED"), color=ACCENT)
    add_badge(slide, "Prix adapté", 4.1, 5.56, 1.25, fill=rgb("DCFCE7"), color=GREEN)
    add_notes(
        slide,
        """
Ce besoin n'est pas isolé. Le Maroc compte environ 1,2 million d'étudiants dans l'enseignement supérieur. Parmi eux, une population importante est déjà connectée et habituée aux outils numériques. En parallèle, la stratégie Maroc Digital 2030 encourage la transformation numérique, y compris dans l'éducation. Cela crée une opportunité claire : proposer une solution pensée pour les étudiants marocains, avec un prix accessible et une expérience adaptée à leurs vrais supports de cours.
""",
    )


def slide_vision(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_bg(slide, BG)
    add_title(slide, "Solution", "La vision EduAI", "Transformer un document statique en parcours d'apprentissage intelligent.")
    add_footer(slide, 4)

    stages = [
        ("PDF statique", "Cours importé", DARK),
        ("Espace intelligent", "Pipeline IA", BLUE),
        ("Progression", "Apprentissage actif", ACCENT),
    ]
    x = 0.95
    for i, (title, body, color) in enumerate(stages):
        add_rect(slide, x, 2.1, 3.15, 1.45, WHITE, LIGHT)
        add_text(slide, title, x + 0.25, 2.45, 2.65, 0.25, 18, color, True, align=PP_ALIGN.CENTER)
        add_text(slide, body, x + 0.35, 2.9, 2.45, 0.2, 10, MUTED, align=PP_ALIGN.CENTER)
        if i < 2:
            add_arrow_text(slide, x + 3.35, 2.7)
        x += 4.15

    actions = [
        ("Comprendre", BLUE),
        ("Réviser", ACCENT),
        ("S'auto-évaluer", GREEN),
        ("Progresser", DARK),
    ]
    x = 1.1
    for action, color in actions:
        add_badge(slide, action, x, 4.05, 2.25, fill=color, size=12)
        x += 2.75

    modules = ["Résumé", "Q&A RAG", "Quiz", "Flashcards SM-2", "Mindmap", "Examen"]
    x = 1.0
    y = 5.15
    for i, module in enumerate(modules):
        add_rect(slide, x, y, 1.75, 0.55, WHITE, LIGHT)
        add_text(slide, module, x + 0.13, y + 0.19, 1.49, 0.13, 8.8, DARK, True, align=PP_ALIGN.CENTER)
        x += 1.95
    add_notes(
        slide,
        """
La vision d'EduAI est de faire évoluer le PDF d'un simple document vers un espace de travail intelligent. L'étudiant importe son cours, et la plateforme génère automatiquement des outils d'apprentissage : résumé, questions-réponses, quiz, flashcards, carte mentale et examen simulé. L'objectif n'est pas seulement de lire plus vite, mais d'apprendre mieux, avec des activités qui poussent l'étudiant à comprendre, mémoriser et mesurer son niveau.
""",
    )


def slide_user_journey(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_bg(slide, WHITE)
    add_title(slide, "Produit", "Parcours utilisateur : simple en 3 étapes", "Créer un compte, importer un PDF, commencer à apprendre.")
    add_footer(slide, 5)

    add_step(slide, "1", "Créer un compte", "Authentification sécurisée JWT", 0.75, 1.65, 3.6, 1.1, BLUE)
    add_step(slide, "2", "Importer un cours PDF", "Extraction et indexation automatiques", 0.75, 3.0, 3.6, 1.1, ACCENT)
    add_step(slide, "3", "Apprendre avec l'IA", "Q&A, résumé, quiz, flashcards, mindmap, examen", 0.75, 4.35, 3.6, 1.1, GREEN)

    browser_mock(slide, 5.05, 1.55, 3.1, 2.05, "Landing - EduAI", [("Commencer", ACCENT), ("IA pédagogique", BLUE)], BLUE)
    browser_mock(slide, 8.65, 1.55, 3.1, 2.05, "Auth - JWT", [("Login", BLUE), ("Register", ACCENT)], ACCENT)
    browser_mock(slide, 5.05, 4.0, 3.1, 2.05, "Upload - PDF", [("Drag & drop", BLUE), ("Indexation", GREEN)], GREEN)
    browser_mock(slide, 8.65, 4.0, 3.1, 2.05, "Workspace - Cours", [("Chat", BLUE), ("Résumé", ACCENT), ("Examen", GREEN)], BLUE)
    add_notes(
        slide,
        """
J'ai voulu garder l'expérience très simple. L'étudiant n'a pas besoin de comprendre le fonctionnement interne de l'IA. Il crée un compte, importe son PDF, puis il accède à un espace de cours où tous les outils sont disponibles. Cette simplicité est importante, parce qu'une solution éducative doit réduire la charge de travail, pas ajouter une complexité supplémentaire.
""",
    )


def slide_qa(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_bg(slide, BG)
    add_title(slide, "Démonstration", "Comprendre avec le Q&A RAG", "Répondre à partir du cours, avec sources vérifiables.")
    add_footer(slide, 6)

    chat_mock(slide, 0.8, 1.65, 5.9, 4.4)
    flow = [
        ("Question", "L'étudiant interroge son cours"),
        ("Recherche", "Top-3 passages pertinents"),
        ("Réponse", "Explication + sources"),
    ]
    y = 1.78
    for i, (title, body) in enumerate(flow):
        add_card(slide, title, body, 7.25, y, 4.75, 0.88, [BLUE, ACCENT, GREEN][i])
        if i < 2:
            add_text(slide, "↓", 9.5, y + 0.86, 0.25, 0.25, 16, BLUE, True, align=PP_ALIGN.CENTER)
        y += 1.35
    add_rect(slide, 7.25, 5.55, 4.75, 0.5, rgb("EFF6FF"), rgb("BFDBFE"))
    add_text(slide, "RAG = réponse ancrée dans le document, pas seulement générée de mémoire.", 7.55, 5.73, 4.2, 0.12, 9.4, BLUE, True, align=PP_ALIGN.CENTER)
    add_notes(
        slide,
        """
La première fonctionnalité clé est le chat de questions-réponses. Contrairement à un chatbot généraliste, EduAI ne répond pas uniquement à partir de sa connaissance générale. Il recherche d'abord les passages les plus pertinents dans le cours importé, puis génère une réponse pédagogique à partir de ces passages. Les sources sont affichées pour que l'étudiant puisse vérifier. Le streaming SSE permet aussi d'avoir une réponse progressive, comme dans une expérience de chat moderne.
""",
    )


def slide_summary(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_bg(slide, WHITE)
    add_title(slide, "Démonstration", "Synthétiser le cours", "Des résumés pédagogiques par chapitre, sans remplacer le cours.")
    add_footer(slide, 7)

    summary_mock(slide, 0.85, 1.6, 5.65, 4.65)
    steps = [
        ("Analyse NLP", "Segmentation, extraction des idées importantes", BLUE),
        ("Reformulation LLM", "Fiche pédagogique lisible par chapitre", ACCENT),
        ("Cache + Export", "Consultation rapide et PDF téléchargeable", GREEN),
    ]
    y = 1.75
    for title, body, color in steps:
        add_card(slide, title, body, 7.15, y, 4.65, 1.0, color)
        y += 1.3
    add_rect(slide, 7.15, 5.55, 4.65, 0.7, rgb("F8FAFC"), LIGHT)
    add_text(slide, "But : aider l'étudiant à identifier l'essentiel, pas supprimer l'effort d'apprentissage.", 7.45, 5.77, 4.0, 0.2, 10.5, MUTED, True, align=PP_ALIGN.CENTER)
    add_notes(
        slide,
        """
Le résumé ne cherche pas à remplacer le cours original. Il sert à aider l'étudiant à identifier l'essentiel et à préparer sa révision. Techniquement, le système combine une première analyse NLP avec une reformulation pédagogique par LLM. Les résultats sont ensuite mis en cache pour éviter de recalculer inutilement. L'étudiant peut aussi exporter ses résumés en PDF.
""",
    )


def slide_revision(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_bg(slide, BG)
    add_title(slide, "Démonstration", "Réviser activement", "Quiz, flashcards et mindmap transforment la lecture en activité mesurable.")
    add_footer(slide, 8)

    quiz_flash_mind_mock(slide, 0.85, 1.65, 11.65, 3.25)
    add_rect(slide, 1.2, 5.35, 10.95, 0.72, DARK, None)
    add_text(
        slide,
        "Passer d'une lecture passive à une révision active : tester, mémoriser, relier.",
        1.55,
        5.58,
        10.25,
        0.2,
        16,
        WHITE,
        True,
        align=PP_ALIGN.CENTER,
    )
    add_notes(
        slide,
        """
EduAI ne se limite pas à expliquer. Il pousse l'étudiant à réviser activement. Les quiz permettent de tester la compréhension. Les flashcards utilisent l'algorithme SM-2, connu notamment dans Anki, pour organiser la répétition espacée. La carte mentale, elle, aide à visualiser les relations entre les concepts. Ces modules répondent à trois besoins différents : tester, mémoriser et structurer.
""",
    )


def slide_exam(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_bg(slide, WHITE)
    add_title(slide, "Démonstration", "S'évaluer avant l'examen", "Le mode examen mesure les acquis dans des conditions proches d'une épreuve.")
    add_footer(slide, 9)

    exam_mock(slide, 0.85, 1.65, 6.2, 4.55)
    features = [
        ("Chronomètre", "Conditions réalistes", RED),
        ("Score + %", "Résultat mesurable", BLUE),
        ("Note A-F", "Lecture immédiate du niveau", GREEN),
        ("Corrections", "Feedback pédagogique", ACCENT),
    ]
    x = 7.55
    y = 1.75
    for title, body, color in features:
        add_card(slide, title, body, x, y, 4.35, 0.9, color)
        y += 1.1
    add_rect(slide, 7.55, 6.02, 4.35, 0.25, rgb("DBEAFE"), None)
    add_text(slide, "Question clé : suis-je prêt pour le vrai examen ?", 7.78, 6.1, 3.9, 0.1, 8.5, BLUE, True, align=PP_ALIGN.CENTER)
    add_notes(
        slide,
        """
Le mode examen répond à une question très concrète : est-ce que je suis prêt ? L'étudiant lance une simulation chronométrée, répond aux questions, puis obtient un score, un pourcentage, une note de A à F et des corrections. Cette fonctionnalité est importante parce qu'elle transforme la révision en auto-évaluation mesurable, ce qui manque souvent dans l'apprentissage à partir de PDF.
""",
    )


def slide_pipeline(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_bg(slide, BG)
    add_title(slide, "Technique", "Pipeline IA : le coeur technique d'EduAI", "La valeur vient de l'orchestration complète du traitement PDF, vectoriel et LLM.")
    add_footer(slide, 10)

    blocks = [
        ("PDF", "Cours", DARK),
        ("PyMuPDF", "Extraction", BLUE),
        ("Chunks", "400 + 50", ACCENT),
        ("MiniLM", "384-d", GREEN),
        ("FAISS", "IndexFlatIP", BLUE),
        ("Top-3", "Passages", ACCENT),
        ("Llama 3.3", "RAG", DARK),
    ]
    x = 0.55
    for i, (title, sub, color) in enumerate(blocks):
        add_rect(slide, x, 2.05, 1.55, 1.05, WHITE, LIGHT)
        add_text(slide, title, x + 0.14, 2.36, 1.27, 0.22, 13, color, True, align=PP_ALIGN.CENTER)
        add_text(slide, sub, x + 0.14, 2.72, 1.27, 0.15, 8.2, MUTED, align=PP_ALIGN.CENTER)
        if i < len(blocks) - 1:
            add_arrow_text(slide, x + 1.65, 2.43)
        x += 1.82

    outputs = [
        ("Réponse", BLUE),
        ("Résumé", ACCENT),
        ("Quiz", GREEN),
        ("Flashcards", ACCENT),
        ("Mindmap", BLUE),
        ("Examen", DARK),
    ]
    add_text(slide, "Sorties pédagogiques générées", 0.85, 4.1, 3.5, 0.26, 15, DARK, True)
    x = 0.85
    for label, color in outputs:
        add_badge(slide, label, x, 4.65, 1.65, fill=color, size=10)
        x += 1.9
    add_rect(slide, 0.85, 5.55, 11.65, 0.62, WHITE, LIGHT)
    add_text(
        slide,
        "Choix clés : RAG pour réduire les hallucinations, FAISS pour la recherche rapide, MiniLM multilingue pour français/arabe/anglais technique.",
        1.12,
        5.76,
        11.05,
        0.16,
        10.5,
        MUTED,
        True,
        align=PP_ALIGN.CENTER,
    )
    add_notes(
        slide,
        """
Le coeur technique d'EduAI est ce pipeline. Lors de l'upload, le PDF est lu avec PyMuPDF, puis découpé en chunks de 400 tokens avec un overlap de 50 pour préserver le contexte. Chaque chunk est transformé en vecteur de 384 dimensions grâce au modèle multilingue MiniLM. Ces vecteurs sont indexés dans FAISS avec IndexFlatIP. Lorsqu'une question est posée, EduAI recherche les trois passages les plus pertinents, les injecte dans le prompt, puis Llama 3.3 70B génère une réponse contextualisée. Le même socle permet ensuite de produire résumés, quiz, flashcards, mindmap et examens.
""",
    )


def slide_architecture(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_bg(slide, WHITE)
    add_title(slide, "Technique", "Architecture moderne, modulaire et déployable", "Une base full-stack solide pour un produit SaaS.")
    add_footer(slide, 11)

    layers = [
        ("Utilisateur", "Navigateur web", rgb("F8FAFC"), DARK),
        ("Frontend", "Next.js 14 - React 18 - TypeScript - Tailwind", rgb("EFF6FF"), BLUE),
        ("Backend API", "FastAPI - Python - Pydantic - Motor", rgb("FFF7ED"), ACCENT),
        ("Services IA/NLP", "PyMuPDF - MiniLM - FAISS - Groq Llama 3.3 70B - fallback CamemBERT", rgb("ECFDF5"), GREEN),
        ("Données & Déploiement", "MongoDB - FAISS sur disque - Docker Compose - Portainer - health checks", rgb("F8FAFC"), DARK),
    ]
    y = 1.45
    for title, body, fill, color in layers:
        add_rect(slide, 1.1, y, 11.1, 0.82, fill, LIGHT)
        add_text(slide, title, 1.42, y + 0.22, 2.0, 0.18, 12.5, color, True)
        add_text(slide, body, 3.35, y + 0.22, 8.35, 0.22, 12, MUTED)
        y += 1.0
    add_rect(slide, 1.1, 6.43, 11.1, 0.25, DARK, None)
    add_text(slide, "Objectif : maintenabilité, sécurité, portabilité et évolution vers SaaS.", 1.45, 6.52, 10.4, 0.08, 8.5, WHITE, True, align=PP_ALIGN.CENTER)
    add_notes(
        slide,
        """
L'architecture a été pensée pour être modulaire. Le frontend est développé avec Next.js, React et TypeScript. Le backend repose sur FastAPI, ce qui est adapté à Python et aux traitements IA. MongoDB stocke les utilisateurs, les cours et les résultats générés, tandis que FAISS gère la recherche vectorielle. Le déploiement est prévu avec Docker Compose et Portainer, avec des volumes persistants et des vérifications de santé. L'objectif est d'avoir une base fonctionnelle, maintenable et déployable.
""",
    )


def slide_validation(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_bg(slide, BG)
    add_title(slide, "Validation", "Projet fonctionnel, testé, déployable", "Les modules principaux ont été validés avec des tests unitaires, intégration, E2E et manuels.")
    add_footer(slide, 12)

    modules = [
        "Auth JWT", "Upload PDF", "RAG Q&A", "Résumé", "Quiz", "Flashcards",
        "Mindmap", "Examen", "Admin"
    ]
    x0, y0 = 0.85, 1.62
    for i, module in enumerate(modules):
        x = x0 + (i % 3) * 3.95
        y = y0 + (i // 3) * 1.15
        add_rect(slide, x, y, 3.45, 0.82, WHITE, LIGHT)
        add_text(slide, "✓", x + 0.25, y + 0.2, 0.32, 0.22, 17, GREEN, True, align=PP_ALIGN.CENTER)
        add_text(slide, module, x + 0.72, y + 0.26, 2.35, 0.18, 12, DARK, True)
    add_rect(slide, 0.85, 5.45, 11.3, 0.82, DARK, None)
    add_text(slide, "Stratégie de test", 1.2, 5.72, 1.8, 0.18, 12.5, rgb("BFDBFE"), True)
    add_text(slide, "Unitaires - Intégration - E2E LLM - Postman - Parcours frontend", 3.15, 5.72, 8.4, 0.18, 12, WHITE)
    add_notes(
        slide,
        """
Pour la validation, j'ai testé les modules principaux à plusieurs niveaux : tests unitaires pour les services, tests d'intégration pour les endpoints, scripts de bout en bout pour la chaîne IA, et tests manuels sur des scénarios utilisateur réels. Les modules prévus dans le cahier des charges sont couverts : authentification, upload, RAG, résumé, quiz, flashcards, mindmap, examen et administration. Cela montre que le projet n'est pas seulement conceptuel, mais déjà fonctionnel et testable.
""",
    )


def slide_differentiation(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_bg(slide, WHITE)
    add_title(slide, "Positionnement", "EduAI combine ce que les autres solutions séparent", "Une plateforme centrée sur les vrais PDF des étudiants.")
    add_footer(slide, 13)

    headers = ["Solution", "PDF personnel", "RAG", "Quiz", "Flashcards", "Examen", "Prix adapté"]
    rows = [
        ("ChatGPT", "○", "△", "△", "○", "○", "△"),
        ("Quizlet / Anki", "○", "○", "✓", "✓", "○", "△"),
        ("Notion AI / SciSpace", "△", "△", "○", "○", "○", "△"),
        ("Coursera / EdX", "○", "○", "✓", "○", "✓", "○"),
        ("EduAI", "✓", "✓", "✓", "✓", "✓", "✓"),
    ]
    table_x, table_y = 0.65, 1.55
    col_w = [2.2, 1.55, 1.05, 1.05, 1.45, 1.15, 1.55]
    row_h = 0.58
    x = table_x
    for i, header in enumerate(headers):
        add_rect(slide, x, table_y, col_w[i], row_h, DARK, None, radius=False)
        add_text(slide, header, x + 0.07, table_y + 0.2, col_w[i] - 0.14, 0.12, 7.9, WHITE, True, align=PP_ALIGN.CENTER)
        x += col_w[i]
    for r, row in enumerate(rows):
        y = table_y + row_h * (r + 1)
        x = table_x
        is_eduai = row[0] == "EduAI"
        fill = rgb("EFF6FF") if is_eduai else rgb("F8FAFC")
        for c, val in enumerate(row):
            add_rect(slide, x, y, col_w[c], row_h, fill, WHITE if is_eduai else LIGHT, radius=False)
            color = BLUE if is_eduai else DARK
            size = 12 if c == 0 else 14
            add_text(slide, val, x + 0.07, y + 0.2, col_w[c] - 0.14, 0.12, size, color, True if is_eduai or c == 0 else False, align=PP_ALIGN.CENTER)
            x += col_w[c]
    add_rect(slide, 0.65, 5.55, 12.0, 0.72, rgb("FFF7ED"), rgb("FED7AA"))
    add_text(slide, "Différenciation : cours réel de l'étudiant + apprentissage actif + expérience intégrée.", 0.95, 5.78, 11.4, 0.15, 12.5, ACCENT, True, align=PP_ALIGN.CENTER)
    add_notes(
        slide,
        """
Les solutions existantes répondent chacune à une partie du problème. ChatGPT est puissant, mais il reste généraliste. Anki et Quizlet sont utiles, mais demandent souvent une création manuelle. Notion AI ou SciSpace peuvent aider à résumer, mais ils ne couvrent pas tout le cycle d'apprentissage. La différence d'EduAI est l'intégration : un cours PDF réel, traité automatiquement, puis transformé en plusieurs outils pédagogiques dans une seule plateforme, avec une logique adaptée aux étudiants marocains.
""",
    )


def slide_business(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_bg(slide, BG)
    add_title(slide, "Business", "SaaS freemium accessible et viable", "Un modèle adapté au pouvoir d'achat marocain, avec potentiel B2B.")
    add_footer(slide, 14)

    add_card(slide, "Plan Free", "0 MAD\nJusqu'à 3 cours\nDécouverte de la plateforme", 0.75, 1.55, 2.75, 2.15, BLUE, value="0 MAD")
    add_card(slide, "Plan Pro", "Accès illimité\nFonctions avancées\nExport, examen, mindmap", 3.75, 1.55, 2.75, 2.15, ACCENT, value="49 MAD")
    add_text(slide, "/mois", 5.23, 1.92, 0.55, 0.2, 10, MUTED, True)

    add_rect(slide, 7.0, 1.55, 5.35, 3.05, WHITE, LIGHT)
    add_text(slide, "Revenus annuels projetés", 7.35, 1.85, 3.2, 0.24, 14, DARK, True)
    values = [147000, 940800, 4233600]
    labels = ["A1", "A2", "A3"]
    max_v = max(values)
    x = 7.55
    for v, label, color in zip(values, labels, [BLUE, ACCENT, GREEN]):
        bar_h = 1.55 * (v / max_v)
        add_rect(slide, x, 3.75 - bar_h, 0.65, bar_h, color, None, radius=False)
        add_text(slide, label, x + 0.04, 3.98, 0.55, 0.16, 8.5, DARK, True, align=PP_ALIGN.CENTER)
        amount = "147k" if v == 147000 else ("940,8k" if v == 940800 else "4,23M")
        add_text(slide, amount, x - 0.12, 3.55 - bar_h, 0.9, 0.14, 8, color, True, align=PP_ALIGN.CENTER)
        x += 1.35
    add_text(slide, "MAD", 11.2, 3.9, 0.5, 0.15, 8, MUTED, True)

    add_rect(slide, 0.75, 4.45, 5.75, 1.18, DARK, None)
    add_text(slide, "Coût mensuel estimé au lancement", 1.05, 4.78, 3.5, 0.18, 12, rgb("BFDBFE"), True)
    add_text(slide, "1 300 MAD", 4.65, 4.67, 1.45, 0.3, 20, WHITE, True, align=PP_ALIGN.RIGHT)
    add_rect(slide, 7.0, 4.9, 5.35, 0.72, rgb("ECFDF5"), rgb("BBF7D0"))
    add_text(slide, "Perspective : offre B2B pour écoles, universités et centres de formation.", 7.35, 5.14, 4.7, 0.13, 10.5, GREEN, True, align=PP_ALIGN.CENTER)
    add_text(slide, "Projections basées sur des hypothèses de conversion progressives.", 0.85, 6.35, 8.0, 0.14, 8.5, MUTED)
    add_notes(
        slide,
        """
Le modèle économique choisi est un freemium adapté au pouvoir d'achat des étudiants marocains. Le plan gratuit permet de découvrir la plateforme, tandis que le plan Pro à 49 MAD par mois donne accès aux fonctions avancées. Les projections restent volontairement progressives : 5 000 utilisateurs en première année, puis une croissance organique. Le coût de lancement estimé est autour de 1 300 MAD par mois, ce qui rend l'expérimentation réaliste. À moyen terme, une piste importante est le B2B avec des écoles ou universités.
""",
    )


def slide_conclusion(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_bg(slide, DARK)
    add_rect(slide, 0, 0, 13.333, 7.5, DARK, None, radius=False)
    add_brand_mark(slide, 0.65, 0.55, dark=True)
    add_text(slide, "Conclusion", 0.72, 1.38, 2.3, 0.28, 12, rgb("93C5FD"), True)
    add_text(slide, "EduAI ne remplace pas l'enseignant.", 1.15, 2.15, 11.0, 0.5, 30, WHITE, True, align=PP_ALIGN.CENTER)
    add_text(
        slide,
        "Il donne à chaque étudiant un compagnon de révision intelligent, accessible et contextualisé.",
        1.85,
        3.05,
        9.65,
        0.75,
        24,
        rgb("FDBA74"),
        True,
        align=PP_ALIGN.CENTER,
    )
    add_badge(slide, "Comprendre mieux", 2.0, 4.75, 2.4, fill=BLUE, size=12)
    add_badge(slide, "Réviser efficacement", 5.12, 4.75, 2.7, fill=ACCENT, size=12)
    add_badge(slide, "S'auto-évaluer", 8.55, 4.75, 2.4, fill=GREEN, size=12)
    add_text(slide, "Merci pour votre attention", 4.4, 6.22, 4.5, 0.24, 16, rgb("CBD5E1"), True, align=PP_ALIGN.CENTER)
    add_footer(slide, 15, dark=True)
    add_notes(
        slide,
        """
Pour conclure, EduAI n'a pas vocation à remplacer l'enseignant. Le rôle de l'enseignant reste central. EduAI intervient plutôt entre le cours et l'examen, au moment où l'étudiant doit comprendre, réviser et vérifier son niveau. Ce projet m'a permis de construire une solution complète qui combine développement web, NLP, RAG, LLM, déploiement et réflexion business. Aujourd'hui, EduAI est une base fonctionnelle, testée et déployable, avec un potentiel d'évolution vers un produit EdTech adapté au contexte marocain.
""",
    )


def build():
    prs = Presentation()
    prs.slide_width = cm(W)
    prs.slide_height = cm(H)

    slide_title(prs)
    slide_problem(prs)
    slide_opportunity(prs)
    slide_vision(prs)
    slide_user_journey(prs)
    slide_qa(prs)
    slide_summary(prs)
    slide_revision(prs)
    slide_exam(prs)
    slide_pipeline(prs)
    slide_architecture(prs)
    slide_validation(prs)
    slide_differentiation(prs)
    slide_business(prs)
    slide_conclusion(prs)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    prs.save(OUT)
    print(f"Generated: {OUT}")
    print(f"Slides: {len(prs.slides)}")


if __name__ == "__main__":
    build()

