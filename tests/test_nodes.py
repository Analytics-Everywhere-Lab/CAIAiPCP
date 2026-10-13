import node
from tests.fake_ollama import PLAN_MARKDOWN


def test_writer_retries_once_when_it_ignores_the_section_template(monkeypatch):
    answers = iter(["A plan with no headings at all.", PLAN_MARKDOWN])
    prompts = []
    monkeypatch.setattr(node, "_stream_llm", lambda state, prompt, t, m: prompts.append(prompt) or next(answers))
    sections = node._write_document({}, "Write the plan.", 0.6, 1000)
    assert len(prompts) == 2 and "IMPORTANT" in prompts[1]
    assert [s["id"] for s in sections][:3] == ["summary", "goals", "interventions"]


def test_writer_keeps_a_structured_first_answer(monkeypatch):
    prompts = []
    monkeypatch.setattr(node, "_stream_llm", lambda state, prompt, t, m: prompts.append(prompt) or PLAN_MARKDOWN)
    assert len(node._write_document({}, "Write the plan.", 0.6, 1000)) == 7 and len(prompts) == 1


def test_validation_cache_key_tracks_content_target_and_feedback():
    from state import Argument

    state = {"patient_info": "p", "arguments": []}
    arg = Argument("Grab bars help", "support", parent_option="O", arg_id="A1")
    key = node._validation_key(arg, state, "none")
    assert node._validation_key(arg, state, "none") == key
    assert node._validation_key(arg, state, "fb1") != key  # new feedback re-verifies
    arg.content = "Grab bars and rails help"
    assert node._validation_key(arg, state, "none") != key  # an edit re-verifies


def test_explanation_strips_the_score_line():
    assert node._explanation("**Validity Score:** 0.72\nSound and relevant.", "Validity Score") == "Sound and relevant."
