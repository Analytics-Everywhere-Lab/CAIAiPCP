from arguments import net_human_ops
from feedback import (
    apply_feedback_ops,
    interpret_feedback,
    normalize_feedback_items,
    plan_revision_strategy,
    rule_strategy,
    validate_operations,
)
from qbaf import evaluate_qbaf, qbaf_delta
from state import Argument
from care_plan_document import SECTION_TITLES

OPTIONS = ["Home safety modification", "Assisted living transfer"]


def make_state():
    arguments = [
        Argument("[RN] Grab bars reduce falls.", "support", 0.8, OPTIONS[0], arg_id="A1", agent_role="Registered Nurse"),
        Argument("[SW] Renovation is costly.", "attack", 0.6, OPTIONS[0], arg_id="A2", agent_role="Social Worker"),
        Argument("[GER] Supervision is constant.", "support", 0.7, OPTIONS[1], arg_id="A3", agent_role="Geriatrician"),
    ]
    return {"patient_info": "82-year-old woman living alone", "handling_options": list(OPTIONS),
            "arguments": arguments, "next_arg_seq": 3, "human_ops_log": [],
            "healthcare_team": [{"name": "Registered Nurse", "role": "Registered Nurse"}]}


def items(*texts, **anchor):
    return normalize_feedback_items([{"text": text, **anchor} for text in texts], 0)


def test_normalize_assigns_ids_and_drops_empty_items():
    normalized = normalize_feedback_items(["  first  ", {"text": ""}, {"text": "second", "section_id": "bogus"}], 2)
    assert [item["id"] for item in normalized] == ["F3", "F4"]
    assert normalized[0]["text"] == "first" and normalized[1]["section_id"] is None


def test_validate_operations_is_strict():
    state = make_state()
    feedback = items("Cost is covered by a grant.", "Shorter please.")
    raw = [
        {"feedback_id": "F1", "op": "add", "option_id": "O1", "stance": "challenge", "content": "A provincial grant covers the renovation cost.", "target_arg_id": "A2"},
        {"feedback_id": "F1", "op": "reject_argument", "arg_id": "A99"},  # unknown argument
        {"feedback_id": "F9", "op": "directive", "content": "x"},  # unknown feedback id
        {"feedback_id": "F2", "op": "directive", "content": "Keep it under one page.", "section_ids": ["summary", "nope"]},
        {"feedback_id": "F2", "op": "directive", "content": "Keep it under one page.", "section_ids": ["summary"]},  # duplicate
        {"feedback_id": "F1", "op": "add_option", "content": "home safety modification"},  # already an option
        "not an op",
    ]
    ops = validate_operations(raw, feedback, state, SECTION_TITLES)
    assert [op["op"] for op in ops] == ["add_argument", "directive"]
    assert ops[0]["stance"] == "attack" and ops[0]["target_arg_id"] == "A2" and ops[0]["option"] == OPTIONS[0]
    assert ops[1]["section_ids"] == ["summary"]


def test_single_item_feedback_id_is_inferred():
    state = make_state()
    ops = validate_operations([{"op": "reject_argument", "arg_id": "A2", "reason": "wrong"}], items("A2 is wrong"), state, SECTION_TITLES)
    assert ops[0]["feedback_id"] == "F1"


def test_unmappable_feedback_falls_back_to_a_directive(fake_llm):
    fake_llm.fail_json = True
    state = make_state()
    ops = interpret_feedback(state, items("Please make it friendlier", section_id="summary"))
    assert ops == [{"feedback_id": "F1", "op": "directive", "content": "Please make it friendlier",
                    "section_ids": ["summary"], "rationale": ops[0]["rationale"], "fallback": True}]


def test_apply_operations_updates_the_graph_and_logs_human_operations(fake_llm):
    state = make_state()
    feedback = items("Grant covers cost", "Add day program", "A3 overstates supervision", "Fix A1")
    ops = [
        {"feedback_id": "F1", "op": "add_argument", "option": OPTIONS[0], "stance": "attack",
         "content": "A grant covers the renovation cost.", "target_arg_id": "A2"},
        {"feedback_id": "F2", "op": "add_option", "content": "Adult day program three days a week"},
        {"feedback_id": "F3", "op": "reject_argument", "arg_id": "A3", "reason": "overstated"},
        {"feedback_id": "F4", "op": "edit_argument", "arg_id": "A1", "content": "Grab bars and night lights reduce falls."},
        {"feedback_id": "F4", "op": "directive", "content": "Use plain language.", "section_ids": []},
    ]
    applied = apply_feedback_ops(state, ops, feedback)
    by_id = {arg.arg_id: arg for arg in state["arguments"]}
    assert by_id["A4"].source == "feedback" and by_id["A4"].target_arg_id == "A2" and by_id["A4"].feedback_id == "F1"
    assert "Adult day program three days a week" in state["handling_options"]
    day_args = [arg for arg in state["arguments"] if arg.parent_option == "Adult day program three days a week"]
    assert any(arg.source == "feedback" for arg in day_args)  # the clinician's own supporting argument
    assert any(arg.source == "agent" and arg.agent_role == "Registered Nurse" for arg in day_args)  # team view
    assert by_id["A3"].human_status == "rejected" and by_id["A3"].rejection_reason == "overstated"
    assert by_id["A1"].human_status == "edited" and by_id["A1"].original_content == "[RN] Grab bars reduce falls."
    assert state["writer_directives"] == [{"feedback_id": "F4", "content": "Use plain language.", "section_ids": []}]
    assert [entry["op"] for entry in state["human_ops_log"]] == ["add", "add_option", "reject", "edit", "directive"]
    assert len(applied) == 5
    net = {op["op"] for op in net_human_ops(state)}
    assert {"add", "reject", "edit", "add_option", "directive"} <= net


def signals(**overrides):
    base = {"graph_operations": 1, "directives": 0, "global_directives": 0, "options_added": [],
            "ranking_changed": False, "tier_changes": [], "max_strength_shift": 0.0,
            "anchored_sections": ["risks"]}
    base.update(overrides)
    return base


def test_rule_strategy():
    known = list(SECTION_TITLES)
    assert rule_strategy(signals(), known) == {"strategy": "targeted_revision", "sections": ["risks"], "structural": False}
    assert rule_strategy(signals(tier_changes=[{}]), known)["strategy"] == "full_regeneration"
    assert rule_strategy(signals(ranking_changed=True), known)["structural"] is True
    assert rule_strategy(signals(graph_operations=0, directives=1, global_directives=1), known)["strategy"] == "presentation_rewrite"
    assert rule_strategy(signals(graph_operations=0, directives=0, anchored_sections=[]), known)["strategy"] == "full_regeneration"
    many = signals(anchored_sections=known[:6])
    assert rule_strategy(many, known)["strategy"] == "full_regeneration"


def _delta(state, mutate):
    before = evaluate_qbaf(state["handling_options"], state["arguments"])
    mutate(state)
    return qbaf_delta(before, evaluate_qbaf(state["handling_options"], state["arguments"]))


def test_a_changed_assessment_always_regenerates_the_whole_plan(fake_llm):
    state = make_state()
    delta = _delta(state, lambda s: setattr(s["arguments"][0], "human_status", "rejected"))
    assert delta["tier_changed"] or delta["ranking_changed"]
    fake_llm.strategy_response = {"strategy": "targeted_revision", "sections": ["summary"], "rationale": "small"}
    plan = plan_revision_strategy(state, delta, [{"op": "reject", "stance": "support"}], [], dict(SECTION_TITLES))
    assert plan["strategy"] == "full_regeneration" and plan["decided_by"] == "rules"
    assert 'the assessment of O1 changed from "Clinical judgment required" to "Set aside"' in plan["rationale"]
    assert fake_llm.count("You are deciding how to update a care plan") == 0  # no choice left to reason about


def test_llm_refines_a_local_change(fake_llm):
    state = make_state()
    delta = _delta(state, lambda s: setattr(s["arguments"][1], "validity_score", 0.55))
    fake_llm.strategy_response = {"strategy": "targeted_revision", "sections": ["interventions"],
                                  "rationale": "Only the cost argument moved."}
    feedback = items("Cost concern is overstated", section_id="risks")
    plan = plan_revision_strategy(state, delta, [{"op": "edit", "stance": "attack"}], feedback, dict(SECTION_TITLES))
    assert plan["strategy"] == "targeted_revision" and plan["decided_by"] == "llm"
    assert set(plan["sections"]) == {"interventions", "risks"}  # the anchored section is always included
    assert plan["rationale"] == "Only the cost argument moved."


def test_presentation_rewrite_is_refused_for_clinical_changes(fake_llm):
    state = make_state()
    delta = _delta(state, lambda s: setattr(s["arguments"][1], "validity_score", 0.55))
    fake_llm.strategy_response = {"strategy": "presentation_rewrite", "sections": [], "rationale": "style"}
    plan = plan_revision_strategy(state, delta, [{"op": "edit", "stance": "attack"}], [], dict(SECTION_TITLES))
    assert plan["strategy"] == "targeted_revision" and plan["decided_by"] == "rules"


def test_strategy_falls_back_to_rules_without_llm(fake_llm):
    fake_llm.fail_json = True
    state = make_state()
    delta = _delta(state, lambda s: setattr(s["arguments"][1], "validity_score", 0.55))
    plan = plan_revision_strategy(state, delta, [{"op": "edit", "stance": "attack"}], [], dict(SECTION_TITLES))
    assert plan["decided_by"] == "rules" and plan["strategy"] == "targeted_revision"
    assert plan["sections"] == ["interventions", "risks"]
