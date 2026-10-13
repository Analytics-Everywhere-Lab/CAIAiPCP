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
    assert tier_for(0.35)["tier"] == "deferred"
    assert tier_for(0.1)["tier"] == "not_recommended"


def test_delta_detects_ranking_tier_and_new_options():
    before = evaluate_qbaf(OPTIONS, [arg("A1", "support", 0.9, 0)])
    after = evaluate_qbaf(OPTIONS + ["Adult day program"], [arg("A1", "support", 0.9, 1)])
    delta = qbaf_delta(before, after)
    assert delta["ranking_changed"] and delta["tier_changed"]
    assert delta["options_added"] == ["Adult day program"]
    assert delta["max_strength_shift"] > 0
    assert qbaf_delta(None, after)["has_previous"] is False
