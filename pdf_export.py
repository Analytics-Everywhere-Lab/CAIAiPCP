"""Render a care plan version as a typeset PDF with reportlab.

Only the markdown subset the plan writer is asked for is supported: section
and subsection headings, paragraphs, bulleted and numbered lists (two levels),
pipe tables, bold/italic/code spans and [REF-x] citations.
"""
import io
import re
from datetime import datetime
from functools import partial
from typing import Any, Dict, List, Optional
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

INK = colors.HexColor("#1e293b")
PRIMARY = colors.HexColor("#3730a3")
ACCENT = colors.HexColor("#4f46e5")
MUTED = colors.HexColor("#64748b")
BORDER = colors.HexColor("#e2e8f0")
LIGHT = colors.HexColor("#f1f5f9")
HEADER_FILL = colors.HexColor("#eef2ff")

TIER_COLORS = {
    "recommended": "#166534",
    "conditional": "#3f6212",
    "uncertain": "#92400e",
    "set_aside": "#64748b",
}

PAGE_MARGIN = 0.75 * inch
FRAME_PADDING = 6  # SimpleDocTemplate's frame pads each side by 6pt

# Characters outside cp1252 (what the built-in PDF fonts can draw) that plans commonly contain.
_UNICODE_FALLBACKS = {
    "\u2265": ">=", "\u2264": "<=", "\u2192": "->", "\u2190": "<-", "\u2194": "<->",
    "\u2248": "~", "\u2260": "!=", "\u2713": "", "\u2714": "", "\u2717": "x", "\u2718": "x",
    "\u2212": "-", "\u2011": "-", "\u00a0": " ", "\u202f": " ", "\u2009": " ", "\u200b": "",
}


def _safe_text(text: str) -> str:
    text = "".join(_UNICODE_FALLBACKS.get(ch, ch) for ch in str(text or ""))
    return text.encode("cp1252", "ignore").decode("cp1252")


def _inline(text: str) -> str:
    """Convert inline markdown to reportlab paragraph markup."""
    text = _safe_text(text)
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"\[([^\]]+)\]\((?:[^)]+)\)", r"\1", text)  # links -> their text
    text = re.sub(r"`([^`]+)`", r'<font face="Courier">\1</font>', text)
    text = re.sub(r"\*\*(.+?)\*\*|__(.+?)__", lambda m: f"<b>{m.group(1) or m.group(2)}</b>", text)
    text = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", text)
    text = re.sub(r"(?<![\w_])_(?!\s)(.+?)(?<!\s)_(?![\w_])", r"<i>\1</i>", text)
    text = text.replace("**", "")
    # Citations are stored as [REF-n] and printed IEEE-style: [1], [2].
    text = re.sub(r"(\[REF-\d+\])(?=\[REF-\d+\])", r"\1, ", text)
    text = re.sub(r"\[REF-(\d+)\]", r'<font color="#4f46e5">[\1]</font>', text)
    return text


def _styles() -> Dict[str, ParagraphStyle]:
    base = ParagraphStyle("Body", fontName="Helvetica", fontSize=9.5, leading=13.5,
                          textColor=INK, spaceAfter=5)
    return {
        "title": ParagraphStyle("Title", fontName="Helvetica-Bold", fontSize=19, leading=23,
                                textColor=colors.white),
        "subtitle": ParagraphStyle("Subtitle", fontName="Helvetica", fontSize=9, leading=12,
                                   textColor=colors.HexColor("#c7d2fe")),
        "band_right": ParagraphStyle("BandRight", fontName="Helvetica", fontSize=8.5, leading=12,
                                     textColor=colors.white, alignment=2),
        "section": ParagraphStyle("Section", fontName="Helvetica-Bold", fontSize=12.5, leading=16,
                                  textColor=PRIMARY, spaceBefore=14, spaceAfter=3),
        "subheading": ParagraphStyle("Subheading", fontName="Helvetica-Bold", fontSize=10.5,
                                     leading=14, textColor=INK, spaceBefore=7, spaceAfter=3),
        "body": base,
        "small": ParagraphStyle("Small", parent=base, fontSize=8, leading=10.5, textColor=MUTED,
                                spaceAfter=3),
        "label": ParagraphStyle("Label", parent=base, fontName="Helvetica-Bold", fontSize=8,
                                leading=11, textColor=MUTED, spaceAfter=0),
        "value": ParagraphStyle("Value", parent=base, fontSize=9, leading=12.5, spaceAfter=0),
        "cell": ParagraphStyle("Cell", parent=base, fontSize=8.5, leading=11, spaceAfter=0),
        "cell_header": ParagraphStyle("CellHeader", parent=base, fontName="Helvetica-Bold",
                                      fontSize=8.5, leading=11, textColor=PRIMARY, spaceAfter=0),
        "bullet0": ParagraphStyle("Bullet0", parent=base, leftIndent=15, bulletIndent=4,
                                  spaceAfter=2.5),
        "bullet1": ParagraphStyle("Bullet1", parent=base, leftIndent=29, bulletIndent=18,
                                  spaceAfter=2.5),
    }


def _table(rows: List[List[str]], styles, width: float, header: bool = True) -> Table:
    """Pipe-table rows -> wrapped reportlab table with proportional column widths."""
    columns = max(len(row) for row in rows)
    rows = [row + [""] * (columns - len(row)) for row in rows]
    lengths = [max(len(_safe_text(row[col])) for row in rows) or 1 for col in range(columns)]
    weights = [max(min(length, 60), 8) for length in lengths]
    total = sum(weights)
    col_widths = [width * weight / total for weight in weights]
    data = []
    for index, row in enumerate(rows):
        style = styles["cell_header"] if header and index == 0 else styles["cell"]
        data.append([Paragraph(_inline(cell), style) for cell in row])
    table = Table(data, colWidths=col_widths, repeatRows=1 if header else 0, hAlign="LEFT")
    commands = [
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
    ]
    if header:
        commands.append(("BACKGROUND", (0, 0), (-1, 0), HEADER_FILL))
    for index in range(1 if header else 0, len(data)):
        if index % 2 == 0:
            commands.append(("BACKGROUND", (0, index), (-1, index), colors.HexColor("#f8fafc")))
    table.setStyle(TableStyle(commands))
    return table


def _split_row(line: str) -> List[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def markdown_to_flowables(markdown: str, styles, width: float) -> List[Any]:
    flowables: List[Any] = []
    paragraph: List[str] = []
    lines = (markdown or "").splitlines()

    def flush():
        if paragraph:
            flowables.append(Paragraph(_inline(" ".join(paragraph)), styles["body"]))
            paragraph.clear()

    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if not stripped:
            flush()
            index += 1
            continue
        if stripped.startswith("|"):
            flush()
            rows = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                if not re.fullmatch(r"\|?[\s:\-|]+\|?", lines[index].strip()):
                    rows.append(_split_row(lines[index]))
                index += 1
            if rows:
                flowables.append(Spacer(1, 3))
                flowables.append(_table(rows, styles, width))
                flowables.append(Spacer(1, 6))
            continue
        heading = re.match(r"^#{1,6}\s+(.+?)\s*#*$", stripped)
        if heading:
            flush()
            flowables.append(Paragraph(_inline(heading.group(1)), styles["subheading"]))
            index += 1
            continue
        if re.fullmatch(r"[-*_]{3,}", stripped):
            flush()
            flowables.append(HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceBefore=4, spaceAfter=4))
            index += 1
            continue
        bullet = re.match(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$", line)
        if bullet:
            flush()
            level = 1 if len(bullet.group(1).replace("\t", "  ")) >= 2 else 0
            marker = bullet.group(2)
            symbol = marker if marker[0].isdigit() else ("\u2022" if level == 0 else "\u2013")
            flowables.append(Paragraph(_inline(bullet.group(3)), styles[f"bullet{level}"], bulletText=symbol))
            index += 1
            continue
        paragraph.append(stripped)
        index += 1
    flush()
    return flowables


class _NumberedCanvas(canvas.Canvas):
    """Canvas that knows the page count, for "Page X of Y" footers."""

    def __init__(self, *args, footer_left: str = "", **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []
        self._footer_left = footer_left

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self._draw_footer(total)
            super().showPage()
        super().save()

    def _draw_footer(self, total: int):
        width, _ = self._pagesize
        self.saveState()
        self.setStrokeColor(BORDER)
        self.setLineWidth(0.5)
        self.line(PAGE_MARGIN, 0.6 * inch, width - PAGE_MARGIN, 0.6 * inch)
        self.setFont("Helvetica", 7.5)
        self.setFillColor(MUTED)
        self.drawString(PAGE_MARGIN, 0.45 * inch, _safe_text(self._footer_left))
        self.drawRightString(width - PAGE_MARGIN, 0.45 * inch, f"Page {self._pageNumber} of {total}")
        self.restoreState()


def _format_date(value: Optional[str]) -> str:
    if not value:
        return ""
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime("%d %b %Y, %H:%M UTC")
    except ValueError:
        return value


def _header_band(plan: Dict[str, Any], styles, width: float) -> Table:
    status = "Approved" if plan.get("status") == "approved" else "Draft for clinical review"
    left = [
        Paragraph("Aging-in-Place Care Plan", styles["title"]),
        Paragraph(f"Version {plan.get('version', 1)} \u00b7 {_safe_text(status)}", styles["subtitle"]),
    ]
    right = Paragraph(
        f"Generated {_safe_text(_format_date(plan.get('created_at')))}"
        + (f"<br/>Approved {_safe_text(_format_date(plan.get('approved_at')))}" if plan.get("approved_at") else ""),
        styles["band_right"],
    )
    band = Table([[left, right]], colWidths=[width * 0.62, width * 0.38])
    band.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PRIMARY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 11),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 11),
    ]))
    return band


def _patient_box(plan: Dict[str, Any], styles, width: float) -> Table:
    team = ", ".join(member.get("name") or member.get("role", "") for member in plan.get("care_team") or [])
    rows = [
        ("Patient", plan.get("patient_info") or "Not provided"),
        ("Severity", plan.get("severity") or "Not assessed"),
        ("Care team", team or "Not assigned"),
        ("Decision confidence", f"{round(100 * (plan.get('decision_confidence') or 0))}% "
                                "(how decisively the verified arguments settle each option, scaled by how well they are grounded)"),
    ]
    data = [[Paragraph(label.upper(), styles["label"]), Paragraph(_inline(value), styles["value"])]
            for label, value in rows]
    box = Table(data, colWidths=[width * 0.2, width * 0.8], hAlign="LEFT")
    box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return box


def _plan_options(plan: Dict[str, Any]):
    """(options in the plan, options set aside), each ranked."""
    ranked = sorted(plan.get("options") or [], key=lambda row: row.get("rank", 0))
    return ([row for row in ranked if row.get("tier") != "set_aside"],
            [row for row in ranked if row.get("tier") == "set_aside"])


def _decision_table(plan: Dict[str, Any], styles, width: float) -> Optional[Table]:
    options, _ = _plan_options(plan)
    if not options:
        return None
    header = ["Care option", "Assessment", "Strength", "Leading support", "Leading concern"]
    data = [[Paragraph(text, styles["cell_header"]) for text in header]]
    for row in options:
        color = TIER_COLORS.get(row.get("tier"), "#1e293b")
        support = row.get("top_supports") or []
        concern = row.get("top_attacks") or []
        data.append([
            Paragraph(_inline(row["option"]), styles["cell"]),
            Paragraph(f'<font color="{color}"><b>{_inline(row.get("tier_label", ""))}</b></font>', styles["cell"]),
            Paragraph(f"{row.get('strength', 0):.2f}", styles["cell"]),
            Paragraph(_inline(_clip(support[0]["content"])) if support else "-", styles["cell"]),
            Paragraph(_inline(_clip(concern[0]["content"])) if concern else "-", styles["cell"]),
        ])
    table = Table(data, colWidths=[width * w for w in (0.23, 0.15, 0.11, 0.255, 0.255)],
                  repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_FILL),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
    ]))
    return table


def _clip(text: str, limit: int = 160) -> str:
    text = " ".join((text or "").split())
    return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."


def _section_heading(number: int, title: str, styles, width: float) -> List[Any]:
    return [
        Paragraph(f"{number}. {_inline(title)}", styles["section"]),
        HRFlowable(width=width, thickness=0.75, color=ACCENT, spaceBefore=0, spaceAfter=5),
    ]


def render_care_plan_pdf(plan: Dict[str, Any]) -> bytes:
    """Render one care plan version (the payload built by the plan writer) to PDF bytes."""
    buffer = io.BytesIO()
    status = "Approved" if plan.get("status") == "approved" else "Draft"
    doc = SimpleDocTemplate(
        buffer, pagesize=LETTER,
        leftMargin=PAGE_MARGIN, rightMargin=PAGE_MARGIN,
        topMargin=0.7 * inch, bottomMargin=0.85 * inch,
        title="Aging-in-Place Care Plan", author="CAIAiPCP",
        subject=f"Care plan version {plan.get('version', 1)}",
    )
    width = doc.width - 2 * FRAME_PADDING
    styles = _styles()
    story: List[Any] = [_header_band(plan, styles, width), Spacer(1, 10), _patient_box(plan, styles, width)]

    number = 0
    decision = _decision_table(plan, styles, width)
    _, set_aside = _plan_options(plan)
    if decision is not None or set_aside:
        number += 1
        story += _section_heading(number, "Decision Summary", styles, width)
        story.append(Paragraph(
            "Each care option was weighed by a quantitative bipolar argumentation framework: "
            "supporting and challenging arguments from the care team, verified against the medical "
            "knowledge base and contested by the reviewing clinician.", styles["small"]))
        if decision is not None:
            story.append(decision)
        else:
            story.append(Paragraph("No option is supported strongly enough to include in this plan.", styles["small"]))
        if set_aside:
            names = "; ".join(_inline(row["option"]) for row in set_aside)
            story.append(Spacer(1, 6))
            story.append(Paragraph(
                f"<b>Set aside after clinician review:</b> {names}. With the reviewing clinician's changes, the "
                f"weighed arguments no longer support {'it' if len(set_aside) == 1 else 'them'} for this patient, so "
                f"{'it is' if len(set_aside) == 1 else 'they are'} not part of this plan.", styles["small"]))

    for section in plan.get("sections") or []:
        number += 1
        heading = _section_heading(number, section.get("title", ""), styles, width)
        body = markdown_to_flowables(section.get("content", ""), styles, width)
        # Keep each heading with the start of its section.
        story.append(KeepTogether(heading + body[:1]))
        story.extend(body[1:])

    slots = (plan.get("scheduling") or {}).get("slots") or {}
    slot_rows = [["Provider", "Next available"]]
    for provider, provider_slots in slots.items():
        times = ", ".join(str(slot.get("time_slot", "")) for slot in (provider_slots or [])[:2] if isinstance(slot, dict))
        if times:
            slot_rows.append([provider, times])
    if len(slot_rows) > 1:
        number += 1
        story += _section_heading(number, "Provider Availability", styles, width)
        story.append(_table(slot_rows, styles, width))

    references = plan.get("reference_list") or []
    if references:
        number += 1
        story += _section_heading(number, "References", styles, width)
        # Published sources only: case records of other patients are never references.
        for ref in references:
            kind = f' <font color="#64748b">({_inline(ref["kind"])})</font>' if ref.get("kind") else ""
            story.append(Paragraph(
                f'<font color="#4f46e5"><b>[{ref["id"]}]</b></font> '
                f'{_inline(ref.get("citation") or ref.get("title", ""))}{kind}', styles["body"]))
            if ref.get("url"):
                url = escape(ref["url"], {'"': "&quot;"})
                story.append(Paragraph(f'<link href="{url}" color="#4f46e5">{url}</link>', styles["small"]))

    notes = plan.get("provenance") or {}
    lines = [
        f"{notes.get('arguments_considered', 0)} arguments weighed "
        f"({notes.get('clinician_changes', 0)} clinician contestations applied)",
        f"Plan revision strategy: {plan.get('strategy_label', 'Initial plan')}",
    ]
    if notes.get("feedback_items"):
        lines.append(f"{notes['feedback_items']} free-text feedback items incorporated")
    if plan.get("memory_used"):
        lines.append(f"{len(plan['memory_used'])} lessons from earlier clinician reviews used as guidance")
    story.append(Spacer(1, 12))
    story.append(HRFlowable(width=width, thickness=0.5, color=BORDER, spaceAfter=4))
    story.append(Paragraph("<b>About this document.</b> " + _inline("; ".join(lines)) + ". "
                           "This plan was drafted by an AI decision-support system and must be reviewed "
                           "by a qualified clinician; it does not replace professional judgment.",
                           styles["small"]))

    footer = f"Confidential  |  Aging-in-Place Care Plan v{plan.get('version', 1)} ({status})"
    doc.build(story, canvasmaker=partial(_NumberedCanvas, footer_left=footer))
    return buffer.getvalue()
