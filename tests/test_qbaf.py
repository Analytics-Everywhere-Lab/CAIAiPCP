import pytest

from qbaf import evaluate_qbaf, qbaf_delta, qbaf_prompt_summary, tier_for
from state import Argument

OPTIONS = ["Home safety modification", "Assisted living transfer"]


def arg(arg_id, stance, score, option=0, **fields):
    return Argument(f"argument {arg_id}", stance, score, OPTIONS[option], arg_id=arg_id, **fields)


def strengths(qbaf):
    return {row["option_id"]: row["strength"] for row in qbaf["options"]}


def test_options_without_arguments_stay_neutral():
    qbaf = evaluate_qbaf(OPTIONS, [])
    assert strengths(qbaf) == {"O1": 0.5, "O2": 0.5}
    assert qbaf["decision_confidence"] == 0.0
    assert {row["tier"] for row in qbaf["options"]} == {"uncertain"}


def test_support_raises_and_attack_lowers_an_option():
    qbaf = evaluate_qbaf(OPTIONS, [arg("A1", "support", 0.8, 0), arg("A2", "attack", 0.8, 1)])
    assert strengths(qbaf)["O1"] > 0.5 > strengths(qbaf)["O2"]
    # Quadratic energy: base + (1 - base) * E^2 / (1 + E^2) with E = 0.8.
    assert strengths(qbaf)["O1"] == pytest.approx(0.5 + 0.5 * 0.64 / 1.64, abs=1e-4)
    rows = {row["option_id"]: row for row in qbaf["options"]}
    assert rows["O1"]["rank"] == 1 and rows["O2"]["rank"] == 2


def test_rejected_arguments_leave_the_graph():
    rejected = arg("A2", "attack", 0.9, 0, human_status="rejected")
    qbaf = evaluate_qbaf(OPTIONS, [arg("A1", "support", 0.6, 0), rejected])
    assert "A2" not in qbaf["arguments"] and rejected.strength is None
    assert strengths(qbaf)["O1"] > 0.5


def test_argument_targeting_an_argument_weakens_it():
    cost = arg("A2", "attack", 0.6, 0)
    rebuttal = arg("A3", "attack", 0.8, 0, target_arg_id="A2", source="feedback", human_status="added")
    without = strengths(evaluate_qbaf(OPTIONS, [arg("A1", "support", 0.7, 0), cost]))["O1"]
    qbaf = evaluate_qbaf(OPTIONS, [arg("A1", "support", 0.7, 0), cost, rebuttal])
    assert cost.strength < 0.6
    assert strengths(qbaf)["O1"] > without
    row = qbaf["arguments"]["A3"]
    assert row["target"] == "A2" and row["option_id"] == "O1" and row["contribution"] > 0


def test_clinician_arguments_blend_validity_with_authority():
    human = arg("A1", "support", 0.2, 0, source="human", human_status="added")
    qbaf = evaluate_qbaf(OPTIONS, [human])
    assert qbaf["arguments"]["A1"]["base"] == pytest.approx(0.5 * 0.9 + 0.5 * 0.2)


def test_unvalidated_arguments_default_to_moderate_validity():
    qbaf = evaluate_qbaf(OPTIONS, [arg("A1", "support", None, 0)])
    assert qbaf["arguments"]["A1"]["base"] == 0.5


def test_contributions_explain_drivers():
    qbaf = evaluate_qbaf(OPTIONS, [arg("A1", "support", 0.9, 0), arg("A2", "attack", 0.4, 0)])
    row = qbaf["options"][0]
    assert [d["arg_id"] for d in row["top_supports"]] == ["A1"]
    assert [d["arg_id"] for d in row["top_attacks"]] == ["A2"]
    assert row["top_supports"][0]["contribution"] > 0 > row["top_attacks"][0]["contribution"]
    summary = qbaf_prompt_summary(qbaf)
    assert "O1 [" in summary and "+ A1" in summary and "- A2" in summary


def test_cycles_terminate():
    first = arg("A1", "attack", 0.7, 0, target_arg_id="A2")
    second = arg("A2", "attack", 0.7, 0, target_arg_id="A1")
    qbaf = evaluate_qbaf(OPTIONS, [first, second])
    assert 0.0 <= first.strength <= 1.0 and 0.0 <= second.strength <= 1.0
    assert set(qbaf["arguments"]) == {"A1", "A2"}


def test_tiers():
    assert tier_for(0.8)["tier"] == "recommended"
    assert tier_for(0.6)["tier"] == "conditional"
    assert tier_for(0.5)["tier"] == "uncertain"
    assert tier_for(0.35)["tier"] == "set_aside"  # never presented as "not recommended"
    assert tier_for(0.1)["tier"] == "set_aside"


def test_only_the_clinicians_contest_sets_an_option_aside():
    concern = arg("A1", "attack", 0.9, 1)
    # The system's own arguments leave Option 2 weak: it stays for clinical judgment instead of
    # being turned down by the system that proposed it.
    row = evaluate_qbaf(OPTIONS, [concern])["options"][1]
    assert row["strength"] < 0.45
    assert row["tier"] == "uncertain" and row["in_plan"] and not row["contested"]
    # Once the clinician removes its support, the weak option is set aside.
    removed = arg("A2", "support", 0.6, 1, human_status="rejected")
    row = evaluate_qbaf(OPTIONS, [concern, removed])["options"][1]
    assert row["tier"] == "set_aside" and not row["in_plan"] and row["contested"]
    # ... and likewise when the clinician adds a concern of their own.
    added = arg("A3", "attack", 0.7, 1, source="human", human_status="added")
    assert evaluate_qbaf(OPTIONS, [arg("A1", "attack", 0.5, 1), added])["options"][1]["tier"] == "set_aside"
    # A change to the other option does not count against this one.
    other = arg("A4", "support", 0.6, 0, human_status="rejected")
    assert evaluate_qbaf(OPTIONS, [concern, other])["options"][1]["tier"] == "uncertain"


def test_delta_detects_ranking_tier_and_new_options():
    before = evaluate_qbaf(OPTIONS, [arg("A1", "support", 0.9, 0)])
    after = evaluate_qbaf(OPTIONS + ["Adult day program"], [arg("A1", "support", 0.9, 1)])
    delta = qbaf_delta(before, after)
    assert delta["ranking_changed"] and delta["tier_changed"]
    assert delta["options_added"] == ["Adult day program"]
    assert delta["max_strength_shift"] > 0
    assert qbaf_delta(None, after)["has_previous"] is False


def test_relevance_and_repetition_shape_base_scores():
    central = arg("A1", "support", 0.8, 0, relevance="high")
    generic = arg("A2", "attack", 0.8, 0, relevance="low")
    repeat = arg("A3", "attack", 0.8, 0, relevance="low", same_as="A2")
    qbaf = evaluate_qbaf(OPTIONS, [central, generic, repeat])
    rows = qbaf["arguments"]
    assert rows["A1"]["base"] == pytest.approx(0.8)
    assert rows["A2"]["base"] == pytest.approx(0.8 * 0.3)
    assert rows["A3"]["base"] == pytest.approx(0.8 * 0.3 * 0.35)  # a repeated point is not a second full vote
    # One central benefit is not cancelled out by generic concerns of the same validity,
    # as it was when every argument counted only by its validity.
    unweighted = evaluate_qbaf(OPTIONS, [arg("A1", "support", 0.8, 0), arg("A2", "attack", 0.8, 0),
                                         arg("A3", "attack", 0.8, 0)])
    assert strengths(unweighted)["O1"] < 0.45 < 0.55 < strengths(qbaf)["O1"]


def test_a_repeat_of_a_removed_argument_counts_in_full():
    lone = arg("A3", "attack", 0.8, 0, relevance="low", same_as="A2")
    assert evaluate_qbaf(OPTIONS, [lone])["arguments"]["A3"]["base"] == pytest.approx(0.8 * 0.3)


def test_a_rebuttal_weakens_the_concern_it_answers():
    support = arg("A1", "support", 0.8, 0, relevance="high")
    concern = arg("A2", "attack", 0.8, 0, relevance="high")
    unanswered = strengths(evaluate_qbaf(OPTIONS, [support, concern]))["O1"]
    support.rebuts = ["A2"]
    answered = evaluate_qbaf(OPTIONS, [support, concern])
    assert strengths(answered)["O1"] > unanswered and concern.strength < 0.8
    assert {"from": "A1", "to": "A2", "relation": "attack", "kind": "rebuttal"} in answered["edges"]


def test_confidence_combines_decisiveness_and_grounding():
    def option_row(validity):
        return evaluate_qbaf(OPTIONS, [arg("A1", "support", validity, 0, relevance="high"),
                                       arg("A2", "support", validity, 0, relevance="high")])["options"][0]
    sound, shaky = option_row(0.9), option_row(0.3)
    assert sound["grounding"] == pytest.approx(0.9) and sound["confidence"] > 0.75
    assert shaky["confidence"] < sound["confidence"]
    balanced = evaluate_qbaf(OPTIONS, [arg("A1", "support", 0.8, 0, relevance="high"),
                                       arg("A2", "attack", 0.8, 0, relevance="high")])["options"][0]
    assert balanced["decisiveness"] == pytest.approx(0.0) and balanced["confidence"] == pytest.approx(0.4)
