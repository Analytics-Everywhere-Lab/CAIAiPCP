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


def group(*specs):
    from state import Argument

    return [Argument(text, stance, parent_option="Home", arg_id=arg_id, **extra) for arg_id, stance, text, extra in specs]


def test_group_result_is_applied_strictly():
    args = group(("A1", "support", "Grab bars help", {}), ("A2", "attack", "Costly", {}),
                 ("A3", "attack", "Costly too", {}), ("A4", "support", "Clinician fact", {"source": "human"}))
    result = {
        "arguments": [
            {"id": "A1", "validity": 0.9, "relevance": "High", "same_as": None, "refs": [1, 99], "note": "Central."},
            {"id": "A2", "validity": "0.5", "relevance": 0.2, "same_as": "A3", "refs": [], "note": "Minor."},
            {"id": "A3", "validity": 7, "relevance": "medium", "same_as": "A2", "refs": ["1"], "note": "Repeat."},
        ],
        "rebuttals": [{"from": "A1", "to": "A2", "reason": "Cheap."}, {"from": "A2", "to": "A3", "reason": "same side"},
                      {"from": "A1", "to": "A9", "reason": "unknown"}],
        "summary": "Strong fit.",
    }
    review = node._apply_group_result(args, result, [{"id": 1}])
    a1, a2, a3, a4 = args
    assert (a1.validity_score, a1.relevance, a1.supporting_docs, a1.rebuts) == (0.9, "high", [1], ["A2"])
    assert (a2.validity_score, a2.relevance, a2.same_as) == (0.5, "low", None)  # same_as must point backwards
    assert (a3.validity_score, a3.relevance, a3.same_as) == (1.0, "moderate", "A2")
    assert a4.flags == ["unverified"] and review["unverified"] == ["A4"]  # no result is never a pass
    assert review["rebuttals"] == [{"from": "A1", "to": "A2", "reason": "Cheap."}]
    assert review["summary"] == "Strong fit." and review["verified"]


def test_group_cache_survives_removals_but_not_edits_or_feedback():
    args = group(("A1", "support", "Grab bars help", {}), ("A2", "attack", "Costly", {}),
                 ("A3", "attack", "Costly", {}))
    state = {"patient_info": "p", "arguments": args}
    node._apply_group_result(args, {"arguments": [
        {"id": "A1", "validity": 0.9, "relevance": "high"},
        {"id": "A2", "validity": 0.5, "relevance": "low"},
        {"id": "A3", "validity": 0.5, "relevance": "low", "same_as": "A2"},
    ], "rebuttals": [{"from": "A1", "to": "A2", "reason": "Cheap."}], "summary": "s"}, [])
    basis = node._group_basis("Home", state, "none")
    cached = node._cache_group(args, state, basis, {"summary": "s", "rebuttals": [{"from": "A1", "to": "A2", "reason": "Cheap."}]})

    remaining = [args[0], args[2]]  # A2 removed by the clinician
    assert node._reusable(cached, remaining, state, basis)
    review = node._reuse_group(cached, remaining)
    assert args[2].same_as is None and args[0].rebuts == [] and review["rebuttals"] == []

    assert not node._reusable(cached, args, state, node._group_basis("Home", state, "fb1"))  # new feedback
    args[0].content = "Grab bars and rails help"
    assert not node._reusable(cached, args, state, basis)  # an edit re-verifies the group
