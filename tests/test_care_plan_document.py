from care_plan_document import (
    changed_section_ids,
    merge_sections,
    parse_sections,
    reference_list,
    section_template_prompt,
    sections_to_markdown,
    strip_section_heading,
)

MESSY_PLAN = """# Comprehensive Care Plan

Intro paragraph about the plan.

## 1. Care Plan Summary
Lives alone after a fall.

## Goals of Care
- Prevent falls

## Recommended Interventions
### Option 1: Home safety
Strong support [REF-2].

## Option 2: Assisted living
Weak.

## Implementation Plan
| Action | Responsible |
|---|---|
| Grab bars | OT |

## Risk Management
- Falls

## Short-term goals
- Walk daily

## Monitoring and Follow-up
- Monthly review

## Care Team Coordination
Nurse leads.

## References
[REF-2] something

## Patient Preferences
Wants to stay home.
"""


def test_parses_messy_writer_output_into_the_template():
    sections = parse_sections(MESSY_PLAN)
    ids = [section["id"] for section in sections]
    assert ids == ["summary", "goals", "interventions", "implementation", "risks", "monitoring",
                   "coordination", "patient_preferences"]
    by_id = {section["id"]: section["content"] for section in sections}
    assert by_id["summary"].startswith("Intro paragraph")  # text before the first section is kept
    assert "### Short-term goals" in by_id["goals"]  # a repeated section heading becomes a subsection
    assert "### Option 2: Assisted living" in by_id["interventions"]  # per-option headings stay inside
    assert "References" not in sections_to_markdown(sections)  # rendered from structured data instead


def test_unstructured_text_becomes_a_single_section():
    assert parse_sections("Just text.") == [{"id": "summary", "title": "Care Plan Summary", "content": "Just text."}]
    assert parse_sections("") == []


def test_bold_lines_work_as_headings():
    sections = parse_sections("**Care Plan Summary**\nabc\n\n**Goals of Care**\n- x")
    assert [section["id"] for section in sections] == ["summary", "goals"]


def test_strip_section_heading_keeps_subsections():
    assert strip_section_heading("## Goals of Care\n\n- a", "goals") == "- a"
    assert strip_section_heading("**Recommended Interventions**\n### Option 1: Home\ntext", "interventions") \
        == "### Option 1: Home\ntext"


def test_merge_keeps_untouched_sections_verbatim():
    sections = parse_sections(MESSY_PLAN)
    merged = merge_sections(sections, {"risks": "- New risk table"})
    assert changed_section_ids(sections, merged) == ["risks"]
    assert [s["content"] for s in merged if s["id"] != "risks"] == [s["content"] for s in sections if s["id"] != "risks"]


def test_reference_list_only_includes_cited_documents():
    refs = [{"id": 1, "content": "a", "similarity_score": 0.9, "metadata": {}},
            {"id": 2, "content": "b", "similarity_score": 0.7, "metadata": {"title": "T", "source": "S"}}]
    rows = reference_list(refs, {2})
    assert rows == [{"id": 2, "title": "T", "source": "S", "preview": "b", "relevance": 0.7, "search_query": None}]


def test_template_prompt_lists_every_section():
    prompt = section_template_prompt()
    for title in ("Care Plan Summary", "Goals of Care", "Recommended Interventions", "Implementation Plan",
                  "Risk Management", "Monitoring and Follow-up", "Care Team Coordination"):
        assert f"## {title}" in prompt
