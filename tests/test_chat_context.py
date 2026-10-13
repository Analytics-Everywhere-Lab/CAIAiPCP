from chat_context import ChatMemory, compact_arguments, compact_case_context, compact_plan, estimate_tokens
from state import Argument

OPTIONS = ["Home safety modification", "Assisted living transfer"]


def make_state(n_args=6, text_len=300):
    arguments = [
        Argument(f"[Registered Nurse] Argument {i} " + "detail " * (text_len // 7), "support" if i % 2 else "attack",
                 0.7, OPTIONS[i % 2], arg_id=f"A{i + 1}", agent_role="Registered Nurse")
        for i in range(n_args)
    ]
    arguments[0].human_status = "rejected"
    arguments[1].human_status = "edited"
    sections = [{"id": f"s{i}", "title": f"Section {i}", "content": "\n".join(f"- point {j} " + "x" * 80 for j in range(8))}
                for i in range(7)]
    return {
        "patient_info": "82-year-old woman living alone", "severity": "Moderate", "handling_options": OPTIONS,
        "arguments": arguments, "healthcare_team": [{"name": "Registered Nurse"}],
        "revised_care_plan": {"version": 2, "status": "draft", "strategy_label": "Targeted revision",
                              "decision_confidence": 0.4, "sections": sections},
        "feedback_history": [{"id": "F1", "text": "Mention her cat"}],
    }


def test_every_argument_is_present_and_the_block_fits_its_budget():
    state = make_state(n_args=30)
    block = compact_arguments(state, max_tokens=900)
    for arg in state["arguments"]:
        assert f"\n{arg.arg_id}|" in block
    assert "|removed|" in block and "|edited|" in block
    assert "[Registered Nurse]" not in block  # the role has its own column
    assert estimate_tokens(block) <= 900 * 1.1


def test_plan_is_kept_whole_when_small_and_compacted_when_large():
    small = {"sections": [{"id": "a", "title": "Goals of Care", "content": "| A | B |\n|---|---|\n| 1 | 2 |"}]}
    assert compact_plan(small, 500) == "## Goals of Care\n| A | B |\n| 1 | 2 |"
    state = make_state()
    compacted = compact_plan(state["revised_care_plan"], 300)
    assert estimate_tokens(compacted) < estimate_tokens(compact_plan(state["revised_care_plan"], 10_000))
    for i in range(7):
        assert f"## Section {i}" in compacted  # every section keeps its heading


def test_case_context_respects_the_overall_budget():
    state = make_state(n_args=40, text_len=400)
    context = compact_case_context(state, budget=1500)
    assert "PATIENT:" in context and "F1: Mention her cat" in context
    assert estimate_tokens(context) <= 1500 * 1.25


def test_case_context_is_cached_until_the_case_changes():
    memory, state = ChatMemory(), make_state()
    first = memory.case_context(state)
    assert memory.case_context(state) is first
    state["arguments"][2].human_status = "rejected"
    assert memory.case_context(state) != first


def test_rolling_summary_keeps_recent_turns():
    memory = ChatMemory(recent_turns=2, history_budget=50)
    for i in range(6):
        memory.add_turn("user", f"question {i} " + "about falls " * 10)
        memory.add_turn("assistant", f"answer {i} " + "use grab bars " * 10)
    seen = []
    assert memory.compact(lambda prompt: seen.append(prompt) or "Clinician asked about falls; advised grab bars.")
    assert len(memory.turns) == 2 and memory.turns[-1]["content"].startswith("answer 5")
    assert memory.summary == "Clinician asked about falls; advised grab bars."
    assert "question 0" in seen[0]
    assert memory.compact(lambda prompt: "unused") is False or len(memory.turns) == 2


def test_summary_falls_back_to_an_extractive_digest():
    memory = ChatMemory(recent_turns=1, history_budget=40)
    memory.add_turn("user", "What about medication timing for the evening dose? " * 3)
    memory.add_turn("assistant", "Give it with dinner.")
    memory.compact(lambda prompt: (_ for _ in ()).throw(RuntimeError("llm down")))
    assert "Q: What about medication timing" in memory.summary


def test_events_are_bounded_and_prompt_puts_stable_context_first():
    memory = ChatMemory(max_events=3)
    for i in range(5):
        memory.add_event(f"event {i}")
    assert memory.events == ["event 2", "event 3", "event 4"] and "event 0" in memory.summary
    memory.add_turn("user", "hi")
    prompt = memory.build_prompt("CONTEXT BLOCK", "What next?")
    assert prompt.index("CONTEXT BLOCK") < prompt.index("CONVERSATION SUMMARY") < prompt.index("RECENT EVENTS")
    assert prompt.rstrip().endswith("User: What next?\nAssistant:")
