"""Care plan document model.

The plan writer is asked for a fixed set of professional sections. This module
holds that template, parses the writer's markdown back into sections (so
feedback can target a section and a revision can rewrite only the sections it
affects), and builds the versioned payload served to the UI and PDF exporter.
"""
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

PLAN_SECTIONS = [
    {
        "id": "summary",
        "title": "Care Plan Summary",
        "keywords": ["summary", "overview", "synopsis"],
        "guidance": "Two to four sentences on the patient's situation, the main risks, and the overall direction of the plan.",
    },
    {
        "id": "goals",
        "title": "Goals of Care",
        "keywords": ["goal", "objective"],
        "guidance": "Three to five specific, measurable goals that reflect the patient's own priorities, as a bulleted list.",
    },
    {
        "id": "interventions",
        "title": "Recommended Interventions",
        "keywords": ["intervention", "recommend", "option"],
        "guidance": "One subsection per care option (### heading) in priority order. State its assessment, the strongest supporting and challenging arguments behind it, and any conditions for its use.",
    },
    {
        "id": "implementation",
        "title": "Implementation Plan",
        "keywords": ["implementation", "action plan", "steps", "timeline"],
        "guidance": "A markdown table with the columns Action | Responsible | Timeline | Notes.",
    },
    {
        "id": "risks",
        "title": "Risk Management",
        "keywords": ["risk", "safety", "mitigation"],
        "guidance": "A markdown table with the columns Risk | Mitigation | Owner.",
    },
    {
        "id": "monitoring",
        "title": "Monitoring and Follow-up",
        "keywords": ["monitor", "follow", "reassess", "review schedule"],
        "guidance": "Review intervals, indicators to track, and the triggers for reassessment or escalation, as a bulleted list.",
    },
    {
        "id": "coordination",
        "title": "Care Team Coordination",
        "keywords": ["team", "coordination", "communication", "responsibilit"],
        "guidance": "Who is responsible for what, and how the care team, the patient and the family stay in contact.",
    },
]

SECTION_IDS = [section["id"] for section in PLAN_SECTIONS]
SECTION_TITLES = {section["id"]: section["title"] for section in PLAN_SECTIONS}

# Sections the writer may add that the document renders from structured data instead.
_DROPPED_TITLE_RE = re.compile(r"\b(references?|sources|bibliography|citations?|disclaimer)\b", re.IGNORECASE)

STRATEGY_LABELS = {
    "initial": "Initial plan",
    "targeted_revision": "Targeted revision",
    "full_regeneration": "Full regeneration",
    "presentation_rewrite": "Presentation rewrite",
}

_HEADING_RE = re.compile(r"^\s{0,3}(#{1,6})\s+(.+?)\s*#*\s*$")
_BOLD_LINE_RE = re.compile(r"^\s*\*\*([^*].*?)\*\*\s*:?\s*$")
_NUMBER_PREFIX_RE = re.compile(r"^\s*(?:section\s+)?(?:\d+|[ivx]+)[.):]\s*", re.IGNORECASE)
_OPTION_HEADING_RE = re.compile(r"^option\s*\d", re.IGNORECASE)


def section_template_prompt() -> str:
    """Instructions describing the required section layout."""
    lines = [
        "Write the care plan in markdown using exactly these level-2 headings, in this order:",
    ]
    for section in PLAN_SECTIONS:
        lines.append(f"## {section['title']}\n   {section['guidance']}")
    lines.append(
        "Use ### only for subsections inside a section. Do not add a title line, a references "
        "section or a disclaimer; the document adds those itself."
    )
    return "\n".join(lines)


def _normalize_title(text: str) -> str:
    text = re.sub(r"[*_`]", "", text or "")
    text = _NUMBER_PREFIX_RE.sub("", text)
    return " ".join(text.strip().strip(":").split())


def match_section_id(title: str) -> Optional[str]:
    """Map a heading to a template section id by keyword."""
    lowered = _normalize_title(title).lower()
    for section in PLAN_SECTIONS:
        if lowered == section["title"].lower() or any(word in lowered for word in section["keywords"]):
            return section["id"]
    return None


def _slug(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", _normalize_title(text).lower()).strip("_")
    return slug[:40] or "section"


def _heading_lines(lines: List[str]):
    found = []
    for index, line in enumerate(lines):
        match = _HEADING_RE.match(line)
        if match:
            found.append((index, len(match.group(1)), match.group(2)))
            continue
        bold = _BOLD_LINE_RE.match(line)
        if bold and len(bold.group(1)) <= 60:
            found.append((index, 7, bold.group(1)))  # bold-only lines rank below real headings
    return found


def _demote_headings(text: str) -> str:
    """Headings inside a section are subsections; keep them below the section level."""
    return re.sub(r"(?m)^\s{0,3}#{1,2}\s+", "### ", text)


def _strip_heading_lines(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not _HEADING_RE.match(line)).strip()


def parse_sections(markdown: str) -> List[Dict[str, str]]:
    """Split the writer's markdown into template sections.

    The section heading level is the shallowest level at which at least two
    headings match the template; deeper headings stay inside their section, as
    do per-option headings ("Option 2: ...") written at the section level.
    Text outside any recognised structure is kept rather than lost: it becomes
    part of the summary, or a single catch-all section."""
    text = (markdown or "").strip()
    if not text:
        return []
    lines = text.splitlines()
    headings = [
        heading for heading in _heading_lines(lines)
        if not _OPTION_HEADING_RE.match(_normalize_title(heading[2]))
    ]
    level = None
    for candidate in sorted({lvl for _, lvl, _ in headings}):
        matches = sum(1 for _, lvl, title in headings if lvl == candidate and match_section_id(title))
        if matches >= 2:
            level = candidate
            break
    if level is None:
        return [{"id": "summary", "title": SECTION_TITLES["summary"], "content": _demote_headings(text)}]

    cuts = [(index, title) for index, lvl, title in headings if lvl == level]
    preamble_parts = [_strip_heading_lines("\n".join(lines[: cuts[0][0]]))]
    matched: Dict[str, Dict[str, str]] = {}
    extras: List[Dict[str, str]] = []
    for position, (index, title) in enumerate(cuts):
        end = cuts[position + 1][0] if position + 1 < len(cuts) else len(lines)
        content = _demote_headings("\n".join(lines[index + 1:end]).strip())
        clean_title = _normalize_title(title)
        if _DROPPED_TITLE_RE.search(clean_title):
            continue
        section_id = match_section_id(title)
        if section_id in matched:
            # A second heading for the same section becomes a subsection of it.
            matched[section_id]["content"] += f"\n\n### {clean_title}\n\n{content}"
        elif section_id:
            matched[section_id] = {"id": section_id, "title": SECTION_TITLES[section_id], "content": content}
        elif not matched:
            preamble_parts.append(content)  # e.g. a document title before the first section
        elif content:
            extras.append({"id": _slug(title), "title": clean_title, "content": content})

    preamble = "\n\n".join(part for part in preamble_parts if part.strip()).strip()
    if preamble:
        if "summary" in matched:
            matched["summary"]["content"] = (preamble + "\n\n" + matched["summary"]["content"]).strip()
        else:
            matched["summary"] = {"id": "summary", "title": SECTION_TITLES["summary"], "content": preamble}

    ordered = [matched[section_id] for section_id in SECTION_IDS if section_id in matched]
    return ordered + extras


def sections_to_markdown(sections: List[Dict[str, str]]) -> str:
    return "\n\n".join(f"## {section['title']}\n\n{section['content'].strip()}" for section in sections).strip()


def _normalized(text: str) -> str:
    return " ".join((text or "").split())


def changed_section_ids(previous: List[Dict[str, str]], current: List[Dict[str, str]]) -> List[str]:
    before = {section["id"]: _normalized(section["content"]) for section in previous or []}
    return [
        section["id"] for section in current
        if before.get(section["id"]) != _normalized(section["content"])
    ]


def merge_sections(previous: List[Dict[str, str]], rewritten: Dict[str, str]) -> List[Dict[str, str]]:
    """Replace the content of the rewritten sections and keep every other section verbatim."""
    merged = []
    seen = set()
    for section in previous:
        seen.add(section["id"])
        if section["id"] in rewritten:
            merged.append({**section, "content": rewritten[section["id"]].strip()})
        else:
            merged.append(dict(section))
    for section_id, content in rewritten.items():
        if section_id not in seen:
            merged.append({"id": section_id, "title": SECTION_TITLES.get(section_id, section_id.title()), "content": content.strip()})
    order = {section_id: position for position, section_id in enumerate(SECTION_IDS)}
    return sorted(merged, key=lambda section: order.get(section["id"], len(order)))


def strip_section_heading(text: str, section_id: Optional[str] = None) -> str:
    """Remove the heading a model tends to repeat at the top of a single rewritten section.

    Level-1/2 headings and a heading equal to the section title are dropped;
    genuine subsection headings (e.g. "### Option 1: ...") are kept."""
    title_of_section = SECTION_TITLES.get(section_id or "", "").lower()
    lines = (text or "").strip().splitlines()
    while lines:
        heading = _HEADING_RE.match(lines[0])
        bold = _BOLD_LINE_RE.match(lines[0])
        if heading:
            level, title = len(heading.group(1)), heading.group(2)
        elif bold:
            level, title = 7, bold.group(1)
        else:
            break
        if level <= 2 or _normalize_title(title).lower() == title_of_section:
            lines = lines[1:]
            while lines and not lines[0].strip():
                lines = lines[1:]
            continue
        break
    return _demote_headings("\n".join(lines).strip())


def reference_list(document_references: List[Dict[str, Any]], cited_ids) -> List[Dict[str, Any]]:
    rows = []
    for ref in sorted(document_references or [], key=lambda r: r["id"]):
        if ref["id"] not in cited_ids:
            continue
        metadata = ref.get("metadata") or {}
        rows.append({
            "id": ref["id"],
            "title": metadata.get("title") or "Medical knowledge base record",
            "source": metadata.get("source") or "MedicalRAG",
            "preview": ref.get("content", ""),
            "relevance": round(ref.get("similarity_score", 0.0), 2),
            "search_query": ref.get("search_query"),
        })
    return rows


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
