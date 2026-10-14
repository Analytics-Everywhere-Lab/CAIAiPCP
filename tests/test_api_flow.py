"""End-to-end flow through the FastAPI app with a scripted LLM."""
import json

import pytest
from fastapi.testclient import TestClient

from tests.conftest import CASE_RECORDS

PATIENT = ("82-year-old female living alone. Mild cognitive impairment, history of falls "
           "but wants to stay at home.")


GROUP_VERIFICATION = "verification panel for an interdisciplinary aging-in-place care plan"


def sse_events(response):
    return [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith("data: ")]


def plan2_options(event):
    return [row["option"] for row in event["care_plan"]["options"]]


def of_type(events, kind):
    return [event for event in events if event["type"] == kind]


@pytest.fixture
def client():
    from api import app

    return TestClient(app)


def start_session(client):
    thread_id = client.post("/api/chat/start", json={"patient_info": PATIENT}).json()["thread_id"]
    events = sse_events(client.get(f"/api/chat/stream/{thread_id}"))
    return thread_id, events


def test_review_stage_keeps_arguments_out_of_the_chat(client, fake_llm):
    thread_id, events = start_session(client)
    review = of_type(events, "review_needed")
    assert len(review) == 1
    arguments = review[0]["arguments"]
    assert arguments and all(arg["arg_id"].startswith("A") for arg in arguments)
    assert {arg["status"] for arg in arguments} == {"unreviewed"}
    assert review[0]["options"] == ["Home safety assessment and modification", "Transition to assisted living"]

    chat_notes = [e["content"] for e in of_type(events, "message") if e["node"] == "human_review"]
    assert len(chat_notes) == 1
    for arg in arguments:
        assert arg["content"] not in chat_notes[0]  # no argument is displayed in the chat
    # Node-start cards drive the reasoning trace; the graph pauses after the review.
    assert [e["node"] for e in of_type(events, "message")][:3] == ["rag_retrieval", "care_plan_generation", "argument_generation"]
    assert fake_llm.count("write a professional, evidence-based care plan") == 0


def test_full_contestation_cycle(client, fake_llm, memory_service):
    thread_id, events = start_session(client)
    arguments = of_type(events, "review_needed")[0]["arguments"]
    attack = next(arg for arg in arguments if arg["type"] == "attack" and "facility" in arg["content"])
    support = next(arg for arg in arguments if arg["type"] == "support")

    # Contest during review: edit, remove, add.
    result = client.post(f"/api/chat/action/{thread_id}", json={
        "action": "modify", "arg_id": support["arg_id"], "new_content": support["content"] + " (edited)"}).json()
    assert next(a for a in result["arguments"] if a["arg_id"] == support["arg_id"])["status"] == "edited"
    result = client.post(f"/api/chat/action/{thread_id}", json={
        "action": "remove", "arg_id": attack["arg_id"], "reason": "not relevant"}).json()
    removed = next(a for a in result["arguments"] if a["arg_id"] == attack["arg_id"])
    assert removed["status"] == "rejected"  # kept for audit and memory, not deleted
    result = client.post(f"/api/chat/action/{thread_id}", json={
        "action": "add", "new_content": "Patient strongly wants to stay home", "new_type": "attack",
        "new_option": "Transition to assisted living", "new_role": "Registered Nurse"}).json()
    added = result["arguments"][-1]
    assert added["status"] == "added" and added["source"] == "human"

    assert client.post(f"/api/chat/action/{thread_id}", json={"action": "accept"}).json()["status"] == "ok"
    events = sse_events(client.get(f"/api/chat/stream/{thread_id}"))
    final = of_type(events, "final_plan")
    assert len(final) == 1
    plan = final[0]["care_plan"]
    assert plan["version"] == 1 and plan["strategy"] == "initial"
    assert [s["id"] for s in plan["sections"]] == [
        "summary", "goals", "interventions", "implementation", "risks", "monitoring", "coordination"]
    assert {row["tier"] for row in plan["options"]} <= {"recommended", "conditional", "uncertain", "set_aside"}
    # Options were screened for fit before arguing: the poor-fit candidate was never proposed.
    assert "Immediate nursing home admission" not in plan2_options(final[0])
    # Arguments are verified per option, in one call each, and weighted by relevance:
    # the well-grounded home option is recommended rather than stuck near 0.5.
    assert fake_llm.count(GROUP_VERIFICATION) == 2
    tiers = {row["option"]: row["tier"] for row in plan["options"]}
    assert tiers["Home safety assessment and modification"] == "recommended"
    assert plan["decision_confidence"] >= 0.45
    reviews = final[0]["option_reviews"]
    assert reviews["O1"]["summary"].startswith("Strong fit") and reviews["O1"]["rebuttals"]
    by_id = {a["arg_id"]: a for a in final[0]["arguments"]}
    answered = reviews["O1"]["rebuttals"][0]
    assert answered["to"] in by_id[answered["from"]]["rebuts"] and by_id[answered["to"]]["relevance"] == "low"
    assert plan["reference_list"] and plan["reference_list"][0]["id"] == 1
    # References are published sources only, and no case record of another patient reaches the browser.
    assert all(ref["source"] == "Europe PMC" and ref["url"] for ref in plan["reference_list"])
    sent = json.dumps(events) + json.dumps(client.get(f"/api/chat/state/{thread_id}").json())
    assert not any(case[:40] in sent for case in CASE_RECORDS)
    assert "Background Falls are common" not in sent  # nor the text of the published sources
    # The case records still inform the plan: the writer reads them as background, apart from the sources.
    writer_prompt = next(c["prompt"] for c in fake_llm.calls if "write a professional, evidence-based care plan" in c["prompt"])
    assert CASE_RECORDS[0] in writer_prompt.split("SIMILAR CASE RECORDS")[1]
    assert "[REF-1] Falls prevention for older adults" in writer_prompt
    assert all(arg["score"] is not None for arg in final[0]["arguments"] if arg["status"] != "rejected")
    assert any("v1 is ready" in e["content"] for e in of_type(events, "message") if e["node"] == "system")
    # The clinician's changes are learned in the background after the plan is delivered.
    memory = of_type(events, "memory")
    assert memory and memory[0]["reflection"]["status"] == "running"
    memory_service.wait_idle()
    reflection = client.get(f"/api/memory/reflection/{thread_id}").json()
    assert reflection["status"] == "done" and reflection["verified"] >= 1
    assert memory_service.store.counts()["long_term"] >= 1

    # The chatbot knows every argument and the plan, in compact form.
    reply = sse_events(client.post(f"/api/chat/message/{thread_id}", json={"message": "Why grab bars?"}))
    assert of_type(reply, "message")[0]["content"].startswith("Argument A1")
    chat_prompt = next(c["prompt"] for c in reversed(fake_llm.calls) if "Why grab bars?" in c["prompt"])
    for arg in final[0]["arguments"]:
        assert arg["arg_id"] + "|" in chat_prompt
    assert "## Risk Management" in chat_prompt
    assert not any(case[:40] in chat_prompt for case in CASE_RECORDS)  # the assistant never sees case records
    assert "REFERENCES CITED: [REF-1] Smith A, Jones B, Lee C, et al." in chat_prompt  # but knows what it cites
    assert of_type(reply, "done")[0]["context"]["prompt_tokens"] > 0

    # Contest from the argument table after the plan exists: only changed arguments are re-verified.
    other_attack = next(a for a in final[0]["arguments"] if a["type"] == "attack" and a["status"] == "unreviewed")
    client.post(f"/api/chat/action/{thread_id}", json={"action": "remove", "arg_id": other_attack["arg_id"]})
    state = client.get(f"/api/chat/state/{thread_id}").json()
    assert state["pending_changes"] == 1
    validations_before = fake_llm.count(GROUP_VERIFICATION)
    assert client.post(f"/api/chat/regenerate/{thread_id}", json={"feedback": []}).json()["mode"] == "contest"
    events = sse_events(client.get(f"/api/chat/stream/{thread_id}"))
    assert fake_llm.count(GROUP_VERIFICATION) == validations_before  # a removal needs no new verification
    plan2 = of_type(events, "final_plan")[0]
    assert plan2["care_plan"]["version"] == 2 and len(plan2["versions"]) == 2
    assert plan2["pending_changes"] == 0
    assert of_type(events, "revision")[0]["strategy"] in ("targeted_revision", "full_regeneration")

    # Free-text feedback on a section: formulated as QBAF operations, and every argument is re-verified.
    fake_llm.feedback_ops = lambda prompt: {"operations": [
        {"feedback_id": "F1", "op": "add_argument", "option_id": "O1", "stance": "support",
         "content": "Her daughter can supervise the renovation, which removes the cost barrier.",
         "rationale": "New fact about family support."},
        {"feedback_id": "F1", "op": "directive", "content": "Use plain language for the family.",
         "section_ids": ["risks"], "rationale": "Presentation request."},
    ]}
    validations_before = fake_llm.count(GROUP_VERIFICATION)
    client.post(f"/api/chat/regenerate/{thread_id}", json={"feedback": [
        {"text": "The daughter will help with renovations; explain risks simply.", "section_id": "risks",
         "quote": "Falls on stairs"}]})
    events = sse_events(client.get(f"/api/chat/stream/{thread_id}"))
    assert fake_llm.count(GROUP_VERIFICATION) - validations_before == 2  # new feedback re-verifies every option
    plan3 = of_type(events, "final_plan")[0]
    v3 = plan3["care_plan"]
    assert v3["version"] == 3 and v3["feedback_applied"][0]["id"] == "F1"
    assert v3["feedback_ops"] and v3["feedback_ops"][0].startswith("F1 -> new argument")
    feedback_arg = next(a for a in plan3["arguments"] if a["source"] == "feedback")
    assert feedback_arg["feedback_id"] == "F1" and feedback_arg["strength"] is not None
    revision = of_type(events, "revision")[0]
    if revision["strategy"] == "targeted_revision":
        assert "risks" in revision["sections"]
        # Untouched sections are kept word for word.
        before = {s["id"]: s["content"] for s in plan2["care_plan"]["sections"]}
        for section in v3["sections"]:
            if section["id"] not in revision["sections"]:
                assert section["content"] == before[section["id"]]

    # Download as PDF, then approve.
    pdf = client.get(f"/api/care-plan/{thread_id}/pdf")
    assert pdf.status_code == 200 and pdf.headers["content-type"] == "application/pdf"
    assert pdf.content[:5] == b"%PDF-" and 'filename="care-plan-v3.pdf"' in pdf.headers["content-disposition"]
    assert client.get(f"/api/care-plan/{thread_id}/pdf?version=1").status_code == 200
    approved = client.post(f"/api/chat/approve/{thread_id}", json={}).json()
    assert approved["care_plan"]["status"] == "approved" and approved["care_plan"]["approved_at"]

    # Memory is visible and governable through the API.
    overview = client.get("/api/memory").json()
    assert overview["enabled"] and overview["long_term"]
    record = overview["long_term"][0]
    reviewed = client.post(f"/api/memory/{record['memory_id']}/review", json={"decision": "hold"}).json()
    assert reviewed["result"]["status"] == "under_review"
    consolidated = client.post("/api/memory/consolidate", json={"dry_run": True}).json()
    assert consolidated["result"]["dry_run"] is True


def test_regenerate_requires_a_plan(client, fake_llm):
    thread_id, _ = start_session(client)
    response = client.post(f"/api/chat/regenerate/{thread_id}", json={"feedback": [{"text": "shorter"}]})
    assert response.status_code == 400


def test_memory_from_one_case_guides_the_next(client, fake_llm, memory_service):
    """Lessons learned from a reviewed case become contestable arguments in a new case."""
    thread_id, events = start_session(client)
    arguments = of_type(events, "review_needed")[0]["arguments"]
    relocation = next(a for a in arguments if a["option"] == "Transition to assisted living" and a["type"] == "support")
    client.post(f"/api/chat/action/{thread_id}", json={"action": "remove", "arg_id": relocation["arg_id"],
                                                       "reason": "She wants to age in place"})
    client.post(f"/api/chat/action/{thread_id}", json={"action": "accept"})
    sse_events(client.get(f"/api/chat/stream/{thread_id}"))
    memory_service.wait_idle()
    assert memory_service.store.load_long_term(statuses=["active"])

    other = client.post("/api/chat/start", json={
        "patient_info": "79-year-old man living alone after a fall; wants to remain in his home."}).json()["thread_id"]
    events = sse_events(client.get(f"/api/chat/stream/{other}"))
    learned = [a for a in of_type(events, "review_needed")[0]["arguments"] if a["source"] == "memory"]
    assert learned and learned[0]["memory_id"].startswith("mem_") and learned[0]["role"] == "Learned guidance"
