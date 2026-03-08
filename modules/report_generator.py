from __future__ import annotations

import io
from typing import Any

from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

from config import (
    APP_BASELINE,
    APP_NAME,
    DISCLAIMER_TEXT,
    METHODOLOGY_TEXT,
    PDF_COLORS,
    PDF_FILENAME_TEMPLATE,
    SCORE_LABELS,
)
from modules import storage
from modules.utils import format_display_datetime, relative_to_base, truncate_text, utc_now_iso
from modules.visualizations import build_profile_history_chart, build_scores_chart, build_theme_chart

PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 44
COLORS = {key: HexColor(value) for key, value in PDF_COLORS.items()}


def _wrap_lines(text: str, font_name: str, font_size: int, max_width: float) -> list[str]:
    words = text.split()
    if not words:
        return []
    lines: list[str] = []
    current_line = words[0]
    for word in words[1:]:
        candidate = f"{current_line} {word}".strip()
        if stringWidth(candidate, font_name, font_size) <= max_width:
            current_line = candidate
        else:
            lines.append(current_line)
            current_line = word
    lines.append(current_line)
    return lines


def _draw_wrapped_text(
    pdf: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    max_width: float,
    font_name: str = "Helvetica",
    font_size: int = 11,
    color: Any = None,
    leading: float | None = None,
) -> float:
    if color is None:
        color = COLORS["text"]
    if leading is None:
        leading = font_size * 1.4

    pdf.setFillColor(color)
    pdf.setFont(font_name, font_size)
    current_y = y
    for paragraph in text.split("\n"):
        lines = _wrap_lines(paragraph.strip(), font_name, font_size, max_width) if paragraph.strip() else [""]
        for line in lines:
            pdf.drawString(x, current_y, line)
            current_y -= leading
        current_y -= leading * 0.25
    return current_y


def _draw_bullets(
    pdf: canvas.Canvas,
    items: list[str],
    x: float,
    y: float,
    max_width: float,
    font_name: str = "Helvetica",
    font_size: int = 11,
) -> float:
    current_y = y
    for item in items:
        pdf.setFillColor(COLORS["accent"])
        pdf.circle(x + 3, current_y + 4, 2, stroke=0, fill=1)
        current_y = _draw_wrapped_text(pdf, item, x + 12, current_y, max_width - 12, font_name, font_size)
        current_y -= 4
    return current_y


def _draw_page_header(pdf: canvas.Canvas, title: str, subtitle: str, page_number: int) -> None:
    pdf.setFillColor(COLORS["background"])
    pdf.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, stroke=0, fill=1)
    pdf.setFillColor(COLORS["primary"])
    pdf.setFont("Helvetica-Bold", 22)
    pdf.drawString(MARGIN, PAGE_HEIGHT - 48, title)
    pdf.setFillColor(COLORS["muted"])
    pdf.setFont("Helvetica", 10)
    pdf.drawString(MARGIN, PAGE_HEIGHT - 66, subtitle)
    pdf.setStrokeColor(COLORS["grid"])
    pdf.line(MARGIN, PAGE_HEIGHT - 78, PAGE_WIDTH - MARGIN, PAGE_HEIGHT - 78)
    pdf.setFillColor(COLORS["muted"])
    pdf.drawRightString(PAGE_WIDTH - MARGIN, 26, f"InnerShift · Page {page_number}")


def _draw_panel(pdf: canvas.Canvas, x: float, y: float, width: float, height: float, fill: Any) -> None:
    pdf.setFillColor(fill)
    pdf.roundRect(x, y, width, height, 16, stroke=0, fill=1)


def _draw_image(pdf: canvas.Canvas, image_bytes: bytes | None, x: float, y: float, width: float, height: float) -> None:
    if not image_bytes:
        pdf.setStrokeColor(COLORS["grid"])
        pdf.roundRect(x, y, width, height, 12, stroke=1, fill=0)
        pdf.setFillColor(COLORS["muted"])
        pdf.setFont("Helvetica", 10)
        pdf.drawCentredString(x + width / 2, y + height / 2, "Visualisation indisponible")
        return
    pdf.drawImage(ImageReader(io.BytesIO(image_bytes)), x, y, width=width, height=height, preserveAspectRatio=True, mask="auto")


def _cover_page(pdf: canvas.Canvas, session: dict[str, Any]) -> None:
    pdf.setFillColor(COLORS["primary"])
    pdf.rect(0, PAGE_HEIGHT - 250, PAGE_WIDTH, 250, stroke=0, fill=1)
    pdf.setFillColor(COLORS["background"])
    pdf.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT - 250, stroke=0, fill=1)

    pdf.setFillColor(white)
    pdf.setFont("Helvetica", 11)
    pdf.drawString(MARGIN, PAGE_HEIGHT - 60, "Rapport de clarification conversationnelle")
    pdf.setFont("Helvetica-Bold", 34)
    pdf.drawString(MARGIN, PAGE_HEIGHT - 118, APP_NAME)
    pdf.setFont("Helvetica", 14)
    pdf.drawString(MARGIN, PAGE_HEIGHT - 145, APP_BASELINE)

    pdf.setFillColor(COLORS["text"])
    pdf.setFont("Helvetica-Bold", 24)
    pdf.drawString(MARGIN, PAGE_HEIGHT - 340, session.get("title") or "Session de reflection")
    pdf.setFillColor(COLORS["muted"])
    pdf.setFont("Helvetica", 12)
    pdf.drawString(MARGIN, PAGE_HEIGHT - 366, format_display_datetime(session.get("created_at")))

    _draw_panel(pdf, MARGIN, 120, PAGE_WIDTH - (MARGIN * 2), 118, COLORS["panel"])
    pdf.setFillColor(COLORS["primary"])
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(MARGIN + 20, 210, "Intent editorial")
    _draw_wrapped_text(
        pdf,
        "Un support sobre et actionnable pour rendre tangibles les themes dominants, les tensions du moment et les prochains leviers de clarification.",
        MARGIN + 20,
        188,
        PAGE_WIDTH - (MARGIN * 2) - 40,
        font_size=11,
        color=COLORS["text"],
    )
    pdf.setFillColor(COLORS["muted"])
    pdf.setFont("Helvetica", 10)
    pdf.drawRightString(PAGE_WIDTH - MARGIN, 36, "InnerShift · Rapport exploratoire")


def _summary_page(pdf: canvas.Canvas, analysis: dict[str, Any], onboarding: dict[str, Any] | None = None) -> None:
    _draw_page_header(pdf, "Resume executif", "Lecture synthesee de la session", 2)
    _draw_panel(pdf, MARGIN, PAGE_HEIGHT - 260, PAGE_WIDTH - (MARGIN * 2), 150, COLORS["panel_alt"])
    pdf.setFillColor(COLORS["primary"])
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(MARGIN + 18, PAGE_HEIGHT - 132, "Vue d'ensemble")
    _draw_wrapped_text(
        pdf,
        analysis.get("summary", ""),
        MARGIN + 18,
        PAGE_HEIGHT - 156,
        PAGE_WIDTH - (MARGIN * 2) - 36,
        font_size=11,
    )

    column_width = (PAGE_WIDTH - (MARGIN * 2) - 24) / 3
    columns = [
        ("3 idees fortes", analysis.get("major_ideas", [])[:3]),
        ("3 tensions", analysis.get("tensions", [])[:3]),
        ("3 pistes d'action", analysis.get("recommendations", [])[:3]),
    ]
    for index, (title, items) in enumerate(columns):
        x = MARGIN + index * (column_width + 12)
        _draw_panel(pdf, x, 150, column_width, 270, COLORS["panel"] if index != 1 else COLORS["panel_alt"])
        pdf.setFillColor(COLORS["primary"])
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(x + 16, 394, title)
        _draw_bullets(pdf, items or ["Aucun element distinctif n'a ete detecte pour cette rubrique."], x + 16, 372, column_width - 32, font_size=10)


def _indicator_page(pdf: canvas.Canvas, analysis: dict[str, Any], score_chart: bytes | None, theme_chart: bytes | None) -> None:
    _draw_page_header(pdf, "Indicateurs et themes", "Scores heuristiques et motifs dominants", 3)
    scores = analysis.get("scores", {})
    card_width = (PAGE_WIDTH - (MARGIN * 2) - 24) / 3
    score_items = list(scores.items())
    card_positions = [
        (MARGIN, PAGE_HEIGHT - 205),
        (MARGIN + card_width + 12, PAGE_HEIGHT - 205),
        (MARGIN + (card_width + 12) * 2, PAGE_HEIGHT - 205),
        (MARGIN, PAGE_HEIGHT - 320),
        (MARGIN + card_width + 12, PAGE_HEIGHT - 320),
    ]

    for index, (metric, value) in enumerate(score_items[:5]):
        x, y = card_positions[index]
        _draw_panel(pdf, x, y, card_width, 92, COLORS["panel_alt"] if index % 2 == 0 else COLORS["panel"])
        pdf.setFillColor(COLORS["muted"])
        pdf.setFont("Helvetica", 9)
        pdf.drawString(x + 14, y + 64, SCORE_LABELS.get(metric, metric))
        pdf.setFillColor(COLORS["primary"])
        pdf.setFont("Helvetica-Bold", 24)
        pdf.drawString(x + 14, y + 30, f"{value}/100")

    _draw_panel(pdf, MARGIN, 122, 246, 260, COLORS["panel_alt"])
    _draw_panel(pdf, MARGIN + 258, 122, PAGE_WIDTH - MARGIN - (MARGIN + 258), 260, COLORS["panel"])
    _draw_image(pdf, score_chart, MARGIN + 12, 136, 222, 228)
    _draw_image(pdf, theme_chart, MARGIN + 270, 136, PAGE_WIDTH - (MARGIN * 2) - 282, 228)

    keywords = ", ".join(item["term"] for item in analysis.get("keyword_frequencies", [])[:8])
    pdf.setFillColor(COLORS["muted"])
    pdf.setFont("Helvetica", 10)
    pdf.drawString(MARGIN, 96, "Mots-cles dominants")
    _draw_wrapped_text(pdf, keywords or "Aucun mot-cle saillant n'a ete extrait.", MARGIN, 78, PAGE_WIDTH - (MARGIN * 2), font_size=10)


def _quotes_page(pdf: canvas.Canvas, session: dict[str, Any], analysis: dict[str, Any]) -> None:
    _draw_page_header(pdf, "Phrases saillantes", "Extraits marquants et lecture structuree", 4)
    quotes = analysis.get("quotes_or_salient_sentences", [])[:4]
    current_y = PAGE_HEIGHT - 122
    for quote in quotes:
        _draw_panel(pdf, MARGIN, current_y - 76, PAGE_WIDTH - (MARGIN * 2), 66, COLORS["panel_alt"])
        current_y = _draw_wrapped_text(pdf, f'"{quote}"', MARGIN + 18, current_y - 28, PAGE_WIDTH - (MARGIN * 2) - 36, font_name="Helvetica-Oblique", font_size=11, color=COLORS["text"])
        current_y -= 8

    category_y = 330
    pdf.setFillColor(COLORS["primary"])
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(MARGIN, category_y, "Lecture structuree")
    category_y -= 22
    categories = analysis.get("categories", {})
    for label, excerpts in list(categories.items())[:4]:
        _draw_panel(pdf, MARGIN, category_y - 66, PAGE_WIDTH - (MARGIN * 2), 58, COLORS["panel"])
        pdf.setFillColor(COLORS["primary"])
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(MARGIN + 16, category_y - 26, label)
        _draw_wrapped_text(pdf, truncate_text(" / ".join(excerpts), 200), MARGIN + 16, category_y - 42, PAGE_WIDTH - (MARGIN * 2) - 32, font_size=9, color=COLORS["muted"])
        category_y -= 72

    transcript_excerpt = truncate_text(session.get("transcription", {}).get("text", ""), 420)
    pdf.setFillColor(COLORS["muted"])
    pdf.setFont("Helvetica", 10)
    pdf.drawString(MARGIN, 86, "Extrait de transcription")
    _draw_wrapped_text(pdf, transcript_excerpt or "Transcription indisponible.", MARGIN, 68, PAGE_WIDTH - (MARGIN * 2), font_size=9)


def _profile_page(pdf: canvas.Canvas, profile: dict[str, Any], history_chart: bytes | None) -> None:
    _draw_page_header(pdf, "Evolution du profil", "Tendances observees dans le temps", 5)
    if profile.get("session_count", 0) < 2:
        _draw_panel(pdf, MARGIN, PAGE_HEIGHT - 260, PAGE_WIDTH - (MARGIN * 2), 150, COLORS["panel"])
        _draw_wrapped_text(
            pdf,
            "Une seule session est disponible pour l'instant. L'evolution du profil deviendra plus parlante des que plusieurs analyses seront enregistrees.",
            MARGIN + 18,
            PAGE_HEIGHT - 172,
            PAGE_WIDTH - (MARGIN * 2) - 36,
            font_size=12,
        )
        return

    _draw_panel(pdf, MARGIN, PAGE_HEIGHT - 360, PAGE_WIDTH - (MARGIN * 2), 220, COLORS["panel_alt"])
    _draw_image(pdf, history_chart, MARGIN + 12, PAGE_HEIGHT - 344, PAGE_WIDTH - (MARGIN * 2) - 24, 184)

    left_width = (PAGE_WIDTH - (MARGIN * 2) - 12) / 2
    _draw_panel(pdf, MARGIN, 118, left_width, 200, COLORS["panel"])
    _draw_panel(pdf, MARGIN + left_width + 12, 118, left_width, 200, COLORS["panel_alt"])

    pdf.setFillColor(COLORS["primary"])
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(MARGIN + 16, 292, "Themes recurrents")
    _draw_bullets(
        pdf,
        [f"{item['theme']} ({item['count']})" for item in profile.get("top_themes", [])[:5]],
        MARGIN + 16,
        270,
        left_width - 32,
        font_size=10,
    )

    right_x = MARGIN + left_width + 12
    pdf.setFillColor(COLORS["primary"])
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(right_x + 16, 292, "Signaux de progression")
    _draw_bullets(
        pdf,
        profile.get("progress_signals", [])[:3],
        right_x + 16,
        270,
        left_width - 32,
        font_size=10,
    )




def _onboarding_page(pdf: canvas.Canvas, onboarding: dict[str, Any] | None, analysis: dict[str, Any]) -> None:
    _draw_page_header(pdf, "Onboarding synthesis", "Session topic, needs, posture, and action horizon", 6)
    insights = (onboarding or {}).get("insights", {}) or analysis.get("synthesis", {})
    _draw_panel(pdf, MARGIN, PAGE_HEIGHT - 250, PAGE_WIDTH - (MARGIN * 2), 150, COLORS["panel_alt"])
    pdf.setFillColor(COLORS["primary"])
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(MARGIN + 18, PAGE_HEIGHT - 132, "Current state")
    lines = [
        f"Session topic: {insights.get('session_topic', 'Not specified')}",
        f"Dominant intention: {insights.get('dominant_intention', 'Not specified')}",
        f"Current load: {insights.get('current_load', 'Not specified')}",
        f"Dominant needs: {', '.join(insights.get('current_needs', [])) or 'Not specified'}",
        f"Likely relational posture: {insights.get('likely_relational_posture', 'Not specified')}",
    ]
    _draw_bullets(pdf, lines, MARGIN + 18, PAGE_HEIGHT - 156, PAGE_WIDTH - (MARGIN * 2) - 36, font_size=10)

    _draw_panel(pdf, MARGIN, PAGE_HEIGHT - 500, PAGE_WIDTH - (MARGIN * 2), 206, COLORS["panel"])
    pdf.setFillColor(COLORS["primary"])
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(MARGIN + 18, PAGE_HEIGHT - 322, "Stress/watchout signals and actions")
    stress = analysis.get("possible_stress_signals", [])[:3]
    actions = analysis.get("actions_to_test", [])[:3]
    plan = insights.get("action_plan", analysis.get("synthesis", {}).get("action_plan", {}))
    bullets = [
        *(f"Stress signal: {item}" for item in stress),
        *(f"Action to test: {item}" for item in actions),
        f"24h plan: {plan.get('next_24h', 'Not specified')}",
        f"7d plan: {plan.get('next_7_days', 'Not specified')}",
        f"30d plan: {plan.get('next_30_days', 'Not specified')}",
    ]
    _draw_bullets(pdf, bullets, MARGIN + 18, PAGE_HEIGHT - 346, PAGE_WIDTH - (MARGIN * 2) - 36, font_size=10)

def _methodology_page(pdf: canvas.Canvas, analysis: dict[str, Any]) -> None:
    _draw_page_header(pdf, "Note methodologique", "Cadre d'interpretation et prudence d'usage", 7)
    _draw_panel(pdf, MARGIN, PAGE_HEIGHT - 250, PAGE_WIDTH - (MARGIN * 2), 138, COLORS["panel_alt"])
    pdf.setFillColor(COLORS["primary"])
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(MARGIN + 18, PAGE_HEIGHT - 136, "Methodologie")
    _draw_wrapped_text(pdf, METHODOLOGY_TEXT, MARGIN + 18, PAGE_HEIGHT - 162, PAGE_WIDTH - (MARGIN * 2) - 36, font_size=11)

    _draw_panel(pdf, MARGIN, PAGE_HEIGHT - 470, PAGE_WIDTH - (MARGIN * 2), 180, COLORS["panel"])
    pdf.setFillColor(COLORS["primary"])
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(MARGIN + 18, PAGE_HEIGHT - 316, "Lecture des indicateurs")
    score_lines = [
        f"{label} : {analysis.get('score_explanations', {}).get(metric, '')}"
        for metric, label in SCORE_LABELS.items()
    ]
    _draw_bullets(pdf, score_lines, MARGIN + 18, PAGE_HEIGHT - 340, PAGE_WIDTH - (MARGIN * 2) - 36, font_size=10)

    _draw_panel(pdf, MARGIN, 110, PAGE_WIDTH - (MARGIN * 2), 110, COLORS["panel_alt"])
    pdf.setFillColor(COLORS["warning"])
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(MARGIN + 18, 190, "Prudence")
    _draw_wrapped_text(pdf, DISCLAIMER_TEXT, MARGIN + 18, 166, PAGE_WIDTH - (MARGIN * 2) - 36, font_size=11)


def generate_report(session: dict[str, Any], profile: dict[str, Any], onboarding: dict[str, Any] | None = None) -> dict[str, Any]:
    analysis = session.get("analysis") or {}
    if not analysis:
        raise ValueError("Impossible de generer un PDF sans analyse disponible.")

    storage.initialize_storage()
    filename = PDF_FILENAME_TEMPLATE.format(session_id=session["id"])
    target_path = storage.report_file_path(session["id"], filename)

    score_chart = build_scores_chart(analysis.get("scores", {}))
    theme_chart = build_theme_chart(analysis.get("dominant_themes", []))
    history_chart = build_profile_history_chart(profile)

    pdf = canvas.Canvas(str(target_path), pagesize=A4)
    _cover_page(pdf, session)
    pdf.showPage()
    _summary_page(pdf, analysis, onboarding)
    pdf.showPage()
    _indicator_page(pdf, analysis, score_chart, theme_chart)
    pdf.showPage()
    _quotes_page(pdf, session, analysis)
    pdf.showPage()
    _profile_page(pdf, profile, history_chart)
    pdf.showPage()
    _onboarding_page(pdf, onboarding, analysis)
    pdf.showPage()
    _methodology_page(pdf, analysis)
    pdf.save()

    return {
        "pdf_path": relative_to_base(target_path),
        "generated_at": utc_now_iso(),
    }
