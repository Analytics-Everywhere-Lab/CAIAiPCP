"""Memory lifecycle, adapted from SEMV's memory tests to care-planning feedback."""
import json
import subprocess
import sys

import pytest

from memory.reflection import case_fingerprint, profile_tags
from memory.schema import MemoryUpdateCandidate
from memory.verifier import deidentify

PATIENTS = {
    "A": "82-year-old woman living alone after a fall, wants to stay home",
    "B": "79-year-old man living alone with falls, prefers his own home",
    "C": "85-year-old widow, two falls this year, refuses to move",
    "D": "88-year-old man with heart failure who wants to remain at home",
}


def case(case_id, patient, ops=None):
    return {
        "case_id": case_id,
        "fingerprint": case_fingerprint(PATIENTS[patient]),
        "profile_tags": ["lives alone", "fall"],
        "options": [{"option_id": "O1", "option": "Home safety", "tier_label": "Recommended"}],
        "ops": ops or [{"op_id": "H1", "op": "reject", "stance": "support", "option": "Assisted living",
                        "content": "[Geriatrician] Mrs. Smith would be safer in assisted living", "source": "agent",
                        "reason": "She wants to stay home"}],
        "feedback": [],
        "ops_signature": "sig",
    }


def by_type(service, memory_type, status="active"):
    return [r for r in service.store.load_long_term([memory_type]) if r.status == status]


def test_deidentify_removes_identifiers_and_coarsens_ages():
    text = deidentify("Mrs. Johnson, 82-year-old, aged 91, call 506-555-1234 or j@x.org on 2026-01-02, MRN: 12345")
    assert "Johnson" not in text and "82" not in text and "91" not in text
    assert "80s-year-old" in text and "in their 90s" in text
    assert "[phone]" in text and "[email]" in text and "[date]" in text and "[identifier]" in text


def test_profile_tags_and_fingerprints():
    tags = profile_tags("Lives alone; recent fall; insulin twice daily", {"medical_conditions": ["diabetes"]}, "High")
    assert tags == ["diabetes", "lives alone", "fall", "insulin", "severity high"]
    assert case_fingerprint("Same  text") == case_fingerprint("same text")


def test_lifecycle_promotes_merges_and_generalizes(memory_service):
    service = memory_service
    first = service.reflect(case("s1", "A"))
    assert first["verified"] == 2 and first["consolidation"]["promoted"] == 1
    assert len(by_type(service, "episodic")) == 1 and not by_type(service, "failure")  # failures need 2 patients
    episodic = by_type(service, "episodic")[0]
    assert "Smith" not in json.dumps(episodic.model_dump())  # stored memory is de-identified

    service.reflect(case("s2", "B"))
    assert by_type(service, "episodic")[0].support_count == 2
    assert len(by_type(service, "failure")) == 1

    # Re-running the same patient description is not independent support.
    repeat = service.reflect(case("s3", "A"))
    assert repeat["rejected"] == 2
    assert by_type(service, "episodic")[0].support_count == 2

    service.reflect(case("s4", "C"))
    rules = by_type(service, "semantic_rule")
    assert len(rules) == 1  # the episodic and failure records generalize into one rule, not two
    assert rules[0].support_count == 3 and rules[0].verified_by == "memory_consolidator_generalization"

    service.reflect(case("s5", "D"))
    assert by_type(service, "semantic_rule")[0].support_count == 4  # later support reaches the rule

    hits = service.retrieve("argument_generation", "woman living alone after a fall who wants to stay at home",
                            ["lives alone", "fall"])
    assert {hit.memory_type for hit in hits} == {"episodic", "failure", "semantic_rule"}
    assert all(hit.metadata["retrieval_score"] > 0 for hit in hits)
    assert service.retrieve("plan_writing", "unrelated pediatric asthma inhaler technique", []) == []
    # A case never retrieves the lessons it produced itself.
    own = service.retrieve("argument_generation", "woman living alone after a fall", ["fall"], exclude_case_id="s1")
    assert all("s1" not in hit.source_case_ids for hit in own)


def test_rejecting_a_memory_derived_argument_is_conflict_evidence(memory_service):
    service = memory_service
    service.reflect(case("s1", "A"))
    record = by_type(service, "episodic")[0]
    for i, patient in enumerate(["B", "C"]):
        ops = [{"op_id": "H1", "op": "reject", "stance": "attack", "option": "Assisted living",
                "content": "[Learned from past reviews] relocation should come last", "source": "memory",
                "memory_id": record.memory_id, "reason": "Her dementia makes home unsafe"}]
        summary = service.reflect(case(f"c{i}", patient, ops))
        assert summary["conflicts"] == 1
    updated = next(r for r in service.store.load_long_term() if r.memory_id == record.memory_id)
    assert updated.conflict_count == 2
    assert updated.status in ("under_review", "deprecated") and updated.confidence < record.confidence
    events = [e.outcome for e in service.store.load_usage_events() if e.memory_id == record.memory_id]
    assert events.count("contested") == 2


def test_verification_fails_closed(memory_service, fake_llm):
    service = memory_service
    candidate = MemoryUpdateCandidate(candidate_id="c1", memory_type="episodic", text="Lesson about falls at home.",
                                      source_case_id="s1", grounding_op_ids=["H9"], confidence=0.9)
    assert service.verifier.verify_batch([candidate], {"H1"})[0].rejected_reason == "grounding_ops_not_in_case"
    ungrounded = candidate.model_copy(update={"grounding_op_ids": []})
    assert service.verifier.verify_batch([ungrounded], {"H1"})[0].verification_status == "rejected"
    weak = candidate.model_copy(update={"grounding_op_ids": ["H1"], "confidence": 0.3})
    assert service.verifier.verify_batch([weak], {"H1"})[0].rejected_reason == "confidence_below_threshold"
    universal = candidate.model_copy(update={"memory_type": "semantic_rule", "grounding_op_ids": ["H1"],
                                             "text": "Always avoid assisted living."})
    assert service.verifier.verify_batch([universal], {"H1"})[0].rejected_reason == "single_case_overgeneralization"
    fake_llm.fail_json = True
    unverifiable = candidate.model_copy(update={"grounding_op_ids": ["H1"]})
    result = service.verifier.verify_batch([unverifiable], {"H1"})[0]
    assert result.verification_status == "under_review"  # an LLM failure never means acceptance


def test_failed_reflection_is_held_for_review(memory_service, fake_llm):
    fake_llm.fail_json = True
    summary = memory_service.reflect(case("s1", "A"))
    assert summary["under_review"] == 1 and not memory_service.store.load_long_term()
    pending = memory_service.overview()["short_term"]
    assert pending[0]["reason"] == "lesson_generation_failed"
    # A human reviewer can approve it; the next consolidation then promotes it.
    memory_service.review(pending[0]["memory_id"], "approve")
    fake_llm.fail_json = False
    memory_service.consolidate()
    assert by_type(memory_service, "episodic")


def test_usage_outcomes_roll_up_once_per_case(memory_service):
    service = memory_service
    service.reflect(case("s1", "A"))
    record = by_type(service, "episodic")[0]
    service.log_usage("s7", [record.memory_id], "prompted")
    service.consolidate()
    service.record_outcomes("s7", {record.memory_id: "successful"})
    service.consolidate()
    service.consolidate()
    updated = by_type(service, "episodic")[0]
    assert updated.usage_count == 1 and updated.successful_usage_count == 1
    service.record_outcomes("s7", {record.memory_id: "contested"})  # a later contest overrides success
    service.consolidate()
    updated = by_type(service, "episodic")[0]
    assert updated.successful_usage_count == 0 and updated.contested_usage_count == 1


def test_governance_and_snapshot(memory_service):
    service = memory_service
    service.reflect(case("s1", "A"))
    record = by_type(service, "episodic")[0]
    assert service.review(record.memory_id, "hold")["status"] == "under_review"
    service.consolidate()
    assert by_type(service, "episodic", "under_review")  # a reviewer hold is not auto-reactivated
    assert service.review(record.memory_id, "reject")["status"] == "deprecated"
    with pytest.raises(KeyError):
        service.review("missing", "approve")
    assert service.snapshot("frozen").endswith("frozen")


def test_consolidation_cli_dry_run(tmp_path):
    result = subprocess.run(
        [sys.executable, "scripts/consolidate_memory.py", "--memory-dir", str(tmp_path / "m"), "--dry-run"],
        capture_output=True, text=True, check=True,
    )
    assert '"dry_run": true' in result.stdout
