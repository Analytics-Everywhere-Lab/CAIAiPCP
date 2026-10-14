import pytest

pytest.importorskip("reportlab")

from care_plan_document import parse_sections  # noqa: E402
from pdf_export import _inline, _plan_options, markdown_to_flowables, render_care_plan_pdf  # noqa: E402

PLAN = {
    "version": 3,
    "created_at": "2026-10-13T14:05:00+00:00",
    "status": "approved",
    "approved_at": "2026-10-13T15:00:00+00:00",
    "sections": parse_sections(
        "## Care Plan Summary\nShe wants to stay home [REF-1] — with **support**.\n\n"
        "## Goals of Care\n- Zero falls ≥ 6 months\n  - nested → detail\n\n"
        "## Implementation Plan\n| Action | Responsible |\n|---|---|\n| Grab bars | OT |\n"
    ),
    "patient_info": "82-year-old female living alone <with> cats & a garden.",
    "severity": "Moderate",
    "care_team": [{"name": "Registered Nurse"}],
    "decision_confidence": 0.42,
    "options": [{"option": "Home safety", "tier": "recommended", "tier_label": "Recommended", "strength": 0.81,
                 "rank": 1, "top_supports": [{"content": "Grab bars help"}], "top_attacks": []}],
    "reference_list": [{"id": 1, "title": "Falls prevention", "kind": "Practice guideline", "source": "Europe PMC",
                        "citation": "Smith A, Jones B, Lee C, et al. Falls prevention. Age Ageing. 2022. doi:10.0000/x",
                        "url": "https://doi.org/10.0000/x", "doi": "10.0000/x"}],
    "scheduling": {"slots": {"Registered Nurse": [{"time_slot": "2026-10-15 09:00"}]}},
    "provenance": {"arguments_considered": 9, "clinician_changes": 2, "feedback_items": 1},
    "memory_used": [{"memory_id": "mem_1"}],
    "strategy_label": "Targeted revision",
}


def test_renders_a_pdf():
    pdf = render_care_plan_pdf(PLAN)
    assert pdf.startswith(b"%PDF-") and len(pdf) > 2000
    assert b"https://doi.org/10.0000/x" in pdf  # each reference links to its published record


def test_options_set_aside_are_noted_not_ranked():
    set_aside = {"option": "Assisted living", "tier": "set_aside", "tier_label": "Set aside", "strength": 0.3,
                 "rank": 2, "top_supports": [], "top_attacks": [{"content": "She wants to stay home"}]}
    plan = {**PLAN, "options": PLAN["options"] + [set_aside]}
    in_plan, aside = _plan_options(plan)
    assert [row["option"] for row in in_plan] == ["Home safety"] and aside == [set_aside]
    assert render_care_plan_pdf(plan).startswith(b"%PDF-")
    # With every option set aside the decision summary still explains why the table is empty.
    assert render_care_plan_pdf({**PLAN, "options": [set_aside]}).startswith(b"%PDF-")


def test_inline_markup_is_escaped_and_converted():
    assert _inline("a <b> & **bold** *it* [REF-2] [link](http://x)") == (
        'a &lt;b&gt; &amp; <b>bold</b> <i>it</i> <font color="#4f46e5">[2]</font> link'
    )
    # IEEE style: adjacent citations are separated by a comma.
    assert _inline("[REF-1][REF-3]") == '<font color="#4f46e5">[1]</font>, <font color="#4f46e5">[3]</font>'
    assert _inline("x ≥ 3 → y") == "x &gt;= 3 -&gt; y"  # escaped markup, drawn as ">=" and "->"


def test_markdown_blocks_become_flowables():
    from reportlab.platypus import Paragraph, Table

    flowables = markdown_to_flowables("Para one\n\n- item\n1. first\n\n| A | B |\n|---|---|\n| 1 | 2 |", _styles(), 400)
    kinds = [type(f).__name__ for f in flowables]
    assert "Table" in kinds and kinds.count("Paragraph") >= 3
    assert any(isinstance(f, Paragraph) and f.bulletText == "1." for f in flowables)
    assert any(isinstance(f, Table) for f in flowables)


def _styles():
    from pdf_export import _styles as styles

    return styles()
