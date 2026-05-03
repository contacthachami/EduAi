"""Router Export — Génération de PDF des résumés."""

import html
import io
import logging
import unicodedata
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from backend.database.mongodb import get_db
from backend.services.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


def _safe_filename(name: str) -> str:
    """Retourne un nom de fichier ASCII-safe (sans accents) pour les headers HTTP."""
    # Décompose les caractères accentués (é → e + combining accent) puis supprime les non-ASCII
    normalized = unicodedata.normalize("NFKD", name)
    ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
    # Remplace les espaces et caractères spéciaux par des underscores
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in ascii_name)
    return safe[:40]


@router.get("/summary/{course_id}")
async def export_summary_pdf(course_id: str, current_user: dict = Depends(get_current_user)):
    """Exporter le résumé d'un cours en PDF stylisé."""
    from bson import ObjectId
    db = get_db()
    user_id = current_user["user_id"]

    course = await db.courses.find_one({"_id": ObjectId(course_id), "user_id": user_id})
    if not course:
        raise HTTPException(status_code=404, detail="Cours introuvable.")

    summary = await db.summaries.find_one({"course_id": course_id})
    if not summary:
        raise HTTPException(status_code=404, detail="Résumé non disponible. Générez-le d'abord.")

    # Générer le PDF
    pdf_buffer = _generate_summary_pdf(course["name"], summary.get("chapters", []))

    filename = f"resume_{_safe_filename(course['name'])}.pdf"
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/flashcards/{course_id}")
async def export_flashcards_pdf(course_id: str, current_user: dict = Depends(get_current_user)):
    """Exporter les flashcards d'un cours en PDF."""
    from bson import ObjectId
    db = get_db()
    user_id = current_user["user_id"]

    course = await db.courses.find_one({"_id": ObjectId(course_id), "user_id": user_id})
    if not course:
        raise HTTPException(status_code=404, detail="Cours introuvable.")

    flashcards = await db.flashcards.find(
        {"user_id": user_id, "course_id": course_id}
    ).to_list(length=None)

    if not flashcards:
        raise HTTPException(status_code=404, detail="Aucune flashcard pour ce cours.")

    pdf_buffer = _generate_flashcards_pdf(course["name"], flashcards)

    filename = f"flashcards_{_safe_filename(course['name'])}.pdf"
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── Génération PDF ──────────────────────────────────

def _generate_summary_pdf(course_name: str, chapters: list) -> io.BytesIO:
    """Génère un PDF pédagogique structuré, moderne et professionnel."""
    import re
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.colors import HexColor, white
    from reportlab.lib.units import cm
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
        Table, TableStyle, PageBreak, KeepTogether,
    )

    # ── Palette ───────────────────────────────────────────────
    INK    = HexColor("#171412")
    ACCENT = HexColor("#B85B2A")
    BG     = HexColor("#F6F3EF")
    MUTED  = HexColor("#8D837A")
    RULE   = HexColor("#E0D5CB")
    W, H   = A4

    buffer = io.BytesIO()

    # ── Canvas callbacks ──────────────────────────────────────
    def _cover(c, doc):
        c.saveState()
        c.setFillColor(BG)
        c.rect(0, 0, W, H, fill=1, stroke=0)
        # Top accent band (6 cm)
        c.setFillColor(ACCENT)
        c.rect(0, H - 6 * cm, W, 6 * cm, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 38)
        c.drawCentredString(W / 2, H - 3.2 * cm, "EduAI")
        c.setFont("Helvetica", 12)
        c.drawCentredString(W / 2, H - 4.4 * cm, "Assistant Pedagogique Intelligent")
        # Bottom bar
        c.setFillColor(ACCENT)
        c.rect(0, 0, W, 1.6 * cm, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont("Helvetica", 9)
        date_str = datetime.now(timezone.utc).strftime("%d/%m/%Y")
        c.drawCentredString(W / 2, 0.55 * cm, f"Resume Pedagogique  -  Genere le {date_str}")
        c.restoreState()

    def _page(c, doc):
        c.saveState()
        # Header bar (2 cm)
        c.setFillColor(ACCENT)
        c.rect(0, H - 2 * cm, W, 2 * cm, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(2 * cm, H - 1.25 * cm, "EduAI")
        c.setFont("Helvetica", 8)
        c.drawRightString(W - 2 * cm, H - 1.25 * cm, course_name[:55])
        # Footer bar (0.8 cm)
        c.setFillColor(ACCENT)
        c.rect(0, 0, W, 0.8 * cm, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont("Helvetica", 8)
        c.drawCentredString(W / 2, 0.25 * cm, f"Page {doc.page}")
        c.restoreState()

    # ── Document ──────────────────────────────────────────────
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=2.2 * cm, bottomMargin=1.5 * cm,
        leftMargin=2 * cm, rightMargin=2 * cm,
    )

    # ── Styles ────────────────────────────────────────────────
    s = getSampleStyleSheet()

    C_TITLE  = ParagraphStyle("CTitle", parent=s["Normal"],
        fontSize=26, textColor=INK, fontName="Helvetica-Bold",
        alignment=TA_CENTER, leading=32, spaceAfter=8)
    C_SUB    = ParagraphStyle("CSub", parent=s["Normal"],
        fontSize=12, textColor=MUTED, fontName="Helvetica",
        alignment=TA_CENTER, leading=18)
    C_INFO   = ParagraphStyle("CInfo", parent=s["Normal"],
        fontSize=10, textColor=MUTED, fontName="Helvetica",
        alignment=TA_CENTER, leading=15)
    CH_NUM   = ParagraphStyle("ChNum", parent=s["Normal"],
        fontSize=10, textColor=white, fontName="Helvetica-Bold",
        alignment=TA_CENTER)
    CH_TTL   = ParagraphStyle("ChTtl", parent=s["Normal"],
        fontSize=14, textColor=INK, fontName="Helvetica-Bold", leading=18)
    SEC_LBL  = ParagraphStyle("SecLbl", parent=s["Normal"],
        fontSize=7, textColor=ACCENT, fontName="Helvetica-Bold",
        spaceBefore=10, spaceAfter=4, leading=10)
    BULLET   = ParagraphStyle("Bullet", parent=s["Normal"],
        fontSize=9.5, textColor=INK, fontName="Helvetica",
        leading=14, spaceAfter=3, leftIndent=14, firstLineIndent=-10)
    CONCEPT  = ParagraphStyle("Concept", parent=s["Normal"],
        fontSize=9.5, textColor=ACCENT, fontName="Helvetica-Bold",
        leading=14, spaceAfter=2)
    CONTEXT  = ParagraphStyle("Context", parent=s["Normal"],
        fontSize=9, textColor=MUTED, fontName="Helvetica",
        leading=13, spaceAfter=2, alignment=TA_JUSTIFY)
    PG_REF   = ParagraphStyle("PgRef", parent=s["Normal"],
        fontSize=8, textColor=MUTED, fontName="Helvetica",
        leading=11, spaceAfter=5)

    # ── Helpers ───────────────────────────────────────────────
    def make_chapter_header(num: int, title: str):
        """Badge numéroté + titre du chapitre."""
        badge_t = Table(
            [[Paragraph(str(num), CH_NUM)]],
            colWidths=[0.75 * cm], rowHeights=[0.75 * cm],
        )
        badge_t.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), ACCENT),
            ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",    (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("LEFTPADDING",   (0, 0), (-1, -1), 0),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ]))
        row_t = Table(
            [[badge_t, Paragraph(html.escape(title), CH_TTL)]],
            colWidths=[1 * cm, None],
        )
        row_t.setStyle(TableStyle([
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING",   (0, 0), (-1, -1), 0),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
            ("TOPPADDING",    (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("LEFTPADDING",   (1, 0), (1, 0),   10),
        ]))
        return row_t

    def parse_bullets(text: str):
        """Découpe le texte en points séparés par '•'."""
        parts = re.split(r'[\u2022\uf0b4\n]+', text)
        return [p.strip() for p in parts if len(p.strip()) > 4]

    def short_context(pedagogic: str, max_chars: int = 520) -> str:
        """Retourne les premières phrases du texte pédagogique (max_chars)."""
        text = pedagogic.strip()
        if len(text) <= max_chars:
            return text
        cut = text.rfind(". ", 0, max_chars)
        return text[: cut + 1] if cut > 0 else text[:max_chars] + "..."

    # ── Page de couverture ────────────────────────────────────
    story = []
    story.append(Spacer(1, 5 * cm))   # pousse sous la bande de 6 cm
    story.append(Paragraph(html.escape(course_name), C_TITLE))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("Resume Pedagogique Complet", C_SUB))
    story.append(Spacer(1, 1.2 * cm))
    story.append(HRFlowable(width="45%", color=ACCENT, thickness=1.5, hAlign="CENTER"))
    story.append(Spacer(1, 1.2 * cm))
    total_pages_count = 0
    for ch in chapters:
        pg = ch.get("pages") or []
        if pg:
            try:
                total_pages_count = max(total_pages_count, max(int(p) for p in pg))
            except (ValueError, TypeError):
                pass
    story.append(Paragraph(
        f"{len(chapters)} chapitres analyses  -  {total_pages_count} pages de cours",
        C_INFO,
    ))
    story.append(PageBreak())

    # ── Chapitres ─────────────────────────────────────────────
    for i, chapter in enumerate(chapters, 1):
        title      = str(chapter.get("title")     or "Chapitre")
        summary_r  = str(chapter.get("summary")   or "")
        concepts   = [str(c) for c in (chapter.get("key_concepts") or []) if c]
        pedagogic  = str(chapter.get("pedagogic") or "")
        pages_list = chapter.get("pages")         or []

        bullets    = parse_bullets(summary_r)
        ctx        = short_context(pedagogic)

        # En-tête du chapitre (à garder ensemble)
        head = [make_chapter_header(i, title), Spacer(1, 4)]
        if pages_list:
            head.append(Paragraph(
                "Pages du cours : " + "  ".join(str(p) for p in pages_list),
                PG_REF,
            ))
        head.append(HRFlowable(width="100%", color=RULE, thickness=0.5))
        head.append(Spacer(1, 6))

        body = []

        # Résumé (points clés)
        if bullets:
            body.append(Paragraph("RESUME", SEC_LBL))
            for b in bullets:
                body.append(Paragraph(f"&#8226;  {html.escape(b)}", BULLET))
            body.append(Spacer(1, 5))

        # Concepts clés
        if concepts:
            body.append(Paragraph("CONCEPTS CLES", SEC_LBL))
            body.append(Paragraph(
                "  &#183;  ".join(html.escape(c) for c in concepts),
                CONCEPT,
            ))
            body.append(Spacer(1, 5))

        # Contexte pédagogique
        if ctx:
            body.append(Paragraph("CONTEXTE PEDAGOGIQUE", SEC_LBL))
            body.append(Paragraph(html.escape(ctx), CONTEXT))
            body.append(Spacer(1, 5))

        body.append(Spacer(1, 10))
        body.append(HRFlowable(width="100%", color=RULE, thickness=0.3))
        body.append(Spacer(1, 18))

        story.append(KeepTogether(head))
        story.extend(body)

    doc.build(story, onFirstPage=_cover, onLaterPages=_page)
    buffer.seek(0)
    return buffer


def _generate_flashcards_pdf(course_name: str, flashcards: list) -> io.BytesIO:
    """Génère un PDF structuré et moderne pour les flashcards."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.colors import HexColor, white
    from reportlab.lib.units import cm
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
        Table, TableStyle, PageBreak, KeepTogether,
    )

    INK    = HexColor("#171412")
    ACCENT = HexColor("#B85B2A")
    BG     = HexColor("#F6F3EF")
    MUTED  = HexColor("#8D837A")
    RULE   = HexColor("#E0D5CB")
    W, H   = A4

    buffer = io.BytesIO()

    def _cover(c, doc):
        c.saveState()
        c.setFillColor(BG)
        c.rect(0, 0, W, H, fill=1, stroke=0)
        c.setFillColor(ACCENT)
        c.rect(0, H - 6 * cm, W, 6 * cm, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 38)
        c.drawCentredString(W / 2, H - 3.2 * cm, "EduAI")
        c.setFont("Helvetica", 12)
        c.drawCentredString(W / 2, H - 4.4 * cm, "Assistant Pedagogique Intelligent")
        c.setFillColor(ACCENT)
        c.rect(0, 0, W, 1.6 * cm, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont("Helvetica", 9)
        date_str = datetime.now(timezone.utc).strftime("%d/%m/%Y")
        c.drawCentredString(W / 2, 0.55 * cm, f"Fiches de Revision  -  Genere le {date_str}")
        c.restoreState()

    def _page(c, doc):
        c.saveState()
        c.setFillColor(ACCENT)
        c.rect(0, H - 2 * cm, W, 2 * cm, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(2 * cm, H - 1.25 * cm, "EduAI")
        c.setFont("Helvetica", 8)
        c.drawRightString(W - 2 * cm, H - 1.25 * cm, course_name[:55])
        c.setFillColor(ACCENT)
        c.rect(0, 0, W, 0.8 * cm, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont("Helvetica", 8)
        c.drawCentredString(W / 2, 0.25 * cm, f"Page {doc.page}")
        c.restoreState()

    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=2.2 * cm, bottomMargin=1.5 * cm,
        leftMargin=2 * cm, rightMargin=2 * cm,
    )

    s = getSampleStyleSheet()

    C_TITLE  = ParagraphStyle("FCTitle", parent=s["Normal"],
        fontSize=26, textColor=INK, fontName="Helvetica-Bold",
        alignment=TA_CENTER, leading=32, spaceAfter=8)
    C_SUB    = ParagraphStyle("FCSub", parent=s["Normal"],
        fontSize=12, textColor=MUTED, fontName="Helvetica",
        alignment=TA_CENTER, leading=18)
    C_INFO   = ParagraphStyle("FCInfo", parent=s["Normal"],
        fontSize=10, textColor=MUTED, fontName="Helvetica",
        alignment=TA_CENTER, leading=15)
    NUM_ST   = ParagraphStyle("FCNum", parent=s["Normal"],
        fontSize=10, textColor=white, fontName="Helvetica-Bold",
        alignment=TA_CENTER)
    Q_STYLE  = ParagraphStyle("FCQ", parent=s["Normal"],
        fontSize=11, textColor=INK, fontName="Helvetica-Bold",
        leading=15, spaceAfter=4)
    A_STYLE  = ParagraphStyle("FCA", parent=s["Normal"],
        fontSize=10, textColor=HexColor("#3A3530"), fontName="Helvetica",
        leading=14, spaceAfter=3, leftIndent=4)
    DIFF_ST  = ParagraphStyle("FCDiff", parent=s["Normal"],
        fontSize=7.5, textColor=white, fontName="Helvetica-Bold",
        alignment=TA_CENTER)

    DIFF_COLORS = {
        "facile":    HexColor("#4A7C59"),
        "moyen":     HexColor("#B85B2A"),
        "difficile": HexColor("#8B2E2E"),
    }

    def make_card(num, front, back, difficulty):
        diff_color = DIFF_COLORS.get(difficulty.lower(), HexColor("#B85B2A"))
        badge_t = Table(
            [[Paragraph(str(num), NUM_ST)]],
            colWidths=[0.75 * cm], rowHeights=[0.75 * cm],
        )
        badge_t.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), ACCENT),
            ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",    (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("LEFTPADDING",   (0, 0), (-1, -1), 0),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ]))
        q_row = Table(
            [[badge_t, Paragraph(front, Q_STYLE)]],
            colWidths=[0.9 * cm, None],
        )
        q_row.setStyle(TableStyle([
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING",   (0, 0), (-1, -1), 0),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
            ("TOPPADDING",    (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("LEFTPADDING",   (1, 0), (1, 0), 10),
        ]))
        diff_t = Table(
            [[Paragraph(difficulty.upper(), DIFF_ST)]],
            colWidths=[2.2 * cm], rowHeights=[0.45 * cm],
        )
        diff_t.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), diff_color),
            ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",    (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        return [
            q_row,
            Spacer(1, 4),
            Paragraph(f">> {back}", A_STYLE),
            Spacer(1, 6),
            diff_t,
            Spacer(1, 8),
            HRFlowable(width="100%", color=RULE, thickness=0.4),
            Spacer(1, 12),
        ]

    # Page de couverture
    story = []
    story.append(Spacer(1, 5 * cm))
    story.append(Paragraph(html.escape(course_name), C_TITLE))
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph("Fiches de Revision", C_SUB))
    story.append(Spacer(1, 1.2 * cm))
    story.append(HRFlowable(width="45%", color=ACCENT, thickness=1.5, hAlign="CENTER"))
    story.append(Spacer(1, 1.2 * cm))
    story.append(Paragraph(f"{len(flashcards)} flashcards", C_INFO))
    story.append(PageBreak())

    # Cartes
    for i, card in enumerate(flashcards, 1):
        front      = html.escape(str(card.get("front")      or ""))
        back       = html.escape(str(card.get("back")       or ""))
        difficulty = str(card.get("difficulty") or "moyen")
        story.append(KeepTogether(make_card(i, front, back, difficulty)))

    doc.build(story, onFirstPage=_cover, onLaterPages=_page)
    buffer.seek(0)
    return buffer
