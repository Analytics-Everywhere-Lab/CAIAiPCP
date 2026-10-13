"""Post-review reflection: lessons from the clinician's operations on the QBAF.

Every kind of human feedback reaches memory in one form: operations on the
argument graph (table edits, and free-text plan feedback that was formulated
as QBAF operations). Reflection classifies the failure modes those operations
reveal, then asks the LLM once for grounded lesson candidates, following
SEMV's LessonGenerator:

- episodic: what the clinician changed for a patient with this profile;
- failure: what the system got wrong, its trigger and the corrective action;
- semantic: a candidate general principle (only trusted after consolidation).

A clinician rejecting an argument that was instantiated from memory is direct
evidence against that memory record; it becomes a conflict observation.
"""
import logging
from typing import Any, Callable, Dict, List, Optional

from memory.schema import MemoryUpdateCandidate, STAGES
from memory.similarity import normalize_text, semantic_signature, stable_hash
from memory.verifier import deidentify

logger = logging.getLogger(__name__)

FAILURE_TYPES_BY_OP = {
    "reject": ["irrelevant_argument", "inaccurate_argument", "unsafe_argument"],
    "edit": ["inaccurate_argument", "imprecise_argument"],
    "add": ["missing_consideration", "patient_preference_ignored", "safety_concern_missed"],
    "add_option": ["missing_option"],
    "directive": ["plan_presentation"],
}
DEFAULT_STAGE = {
    "irrelevant_argument": "argument_generation",
    "inaccurate_argument": "argument_validation",
    "unsafe_argument": "argument_validation",
    "imprecise_argument": "argument_generation",
    "missing_consideration": "argument_generation",
    "patient_preference_ignored": "argument_generation",
    "safety_concern_missed": "argument_generation",
    "missing_option": "option_generation",
    "plan_presentation": "plan_writing",
}

# Profile vocabulary used to tag cases when no structured patient analysis is available.
_PROFILE_TERMS = [
    "lives alone", "fall", "dementia", "cognitive impairment", "memory loss", "diabetes", "stroke",
    "parkinson", "heart failure", "heart disease", "copd", "arthritis", "osteoporosis", "depression",
    "anxiety", "social isolation", "hearing loss", "vision loss", "incontinence", "polypharmacy",
    "caregiver", "wheelchair", "walker", "mobility", "insulin", "pain", "frailty", "malnutrition",
    "stairs", "widowed", "palliative",
]


def profile_tags(patient_info: str, patient_analysis: Optional[Dict[str, Any]] = None, severity: Optional[str] = None) -> List[str]:
    """Short, de-identified descriptors of the patient used to match memory to cases."""
    tags = []
    analysis = patient_analysis or {}
    for key in ("medical_conditions", "safety_risks", "psychosocial_needs"):
        for value in analysis.get(key) or []:
            if isinstance(value, str) and 2 < len(value) <= 60:
                tags.append(value.lower().strip())
    functional = analysis.get("functional_status") or {}
    for key, value in functional.items() if isinstance(functional, dict) else []:
        if isinstance(value, str) and value not in ("unknown", "intact", "independent", "none"):
            tags.append(f"{key} {value}".replace("_", " ").lower())
    lowered = (patient_info or "").lower()
    for term in _PROFILE_TERMS:
        # Skip vocabulary already covered by an analysed tag ("fall" vs "falls").
        if term in lowered and not any(term in tag or tag in term for tag in tags):
            tags.append(term)
    if severity and severity.lower() not in ("default", ""):
        tags.append(f"severity {severity.lower()}")
    return list(dict.fromkeys(tag for tag in tags if tag))[:15]


def case_fingerprint(patient_info: str) -> str:
    """Re-running the same patient description must never count as an independent case."""
    return f"fp_{stable_hash(normalize_text(patient_info))}"


def detected_failure_types(ops: List[Dict[str, Any]]) -> List[str]:
    found = []
    for op in ops:
        found.extend(FAILURE_TYPES_BY_OP.get(op.get("op"), []))
    return list(dict.fromkeys(found))


def describe_op(op: Dict[str, Any]) -> str:
    text = " ".join(str(op.get("content") or "").split())[:220]
    parts = [op.get("op_id", "?"), op.get("op", "?"), op.get("stance") or "-", (op.get("option") or "-")[:80], text]
    if op.get("original_content") and op.get("op") == "edit":
        parts.append("was: " + " ".join(str(op["original_content"]).split())[:160])
    if op.get("reason"):
        parts.append("reason: " + str(op["reason"])[:160])
    if op.get("source") == "memory":
        parts.append(f"(argument came from memory {op.get('memory_id')})")
    return " | ".join(deidentify(str(part)) for part in parts)


class LessonGenerator:
    def __init__(self, llm_json: Optional[Callable[..., Any]]) -> None:
        self.llm_json = llm_json

    def generate(self, case: Dict[str, Any]) -> List[MemoryUpdateCandidate]:
        ops = case.get("ops") or []
        if not ops:
            return []
        failure_types = detected_failure_types(ops)
        try:
            if self.llm_json is None:
                raise RuntimeError("llm_unavailable")
            data = self.llm_json(self._prompt(case, failure_types), temperature=0.2, max_tokens=3072)
            if not isinstance(data, dict):
                raise ValueError("lesson response is not a JSON object")
        except Exception as exc:
            logger.warning("Lesson generation failed for %s: %s", case.get("case_id"), exc)
            return [self._fallback(case)]

        candidates = []
        episodic = data.get("episodic")
        if isinstance(episodic, dict) and episodic.get("observation"):
            candidates.append(self._candidate(
                case, "episodic", 0, text=episodic["observation"],
                trigger_pattern=episodic.get("profile_pattern"), stage="general",
                confidence=episodic.get("confidence"), op_ids=episodic.get("op_ids"),
            ))
        for index, failure in enumerate((data.get("failures") or [])[:3]):
            if not isinstance(failure, dict) or failure.get("failure_type") not in failure_types:
                continue
            if not failure.get("lesson"):
                continue
            stage = failure.get("stage") if failure.get("stage") in STAGES else DEFAULT_STAGE[failure["failure_type"]]
            candidates.append(self._candidate(
                case, "failure", index, text=failure["lesson"], lesson=failure["lesson"],
                trigger_pattern=failure.get("trigger_pattern"), recommended_action=failure.get("recommended_action"),
                failure_type=failure["failure_type"], polarity=failure.get("polarity"), stage=stage,
                confidence=failure.get("confidence"), op_ids=failure.get("op_ids"),
            ))
        semantic = data.get("semantic")
        if isinstance(semantic, dict) and semantic.get("lesson") and semantic.get("generalizable_pattern"):
            stage = semantic.get("stage") if semantic.get("stage") in STAGES else "general"
            candidates.append(self._candidate(
                case, "semantic_rule", 0, text=semantic["lesson"], lesson=semantic["lesson"],
                trigger_pattern=semantic.get("trigger_pattern"), argument_pattern=semantic.get("argument_pattern"),
                recommended_action=semantic.get("recommended_action"),
                applicability_scope=semantic.get("applicability_scope"),
                exceptions=semantic.get("exceptions") or [], polarity=semantic.get("polarity"), stage=stage,
                confidence=semantic.get("confidence"), op_ids=semantic.get("op_ids"),
                rationale=semantic.get("generalizable_pattern"),
            ))
        return candidates or [self._fallback(case)]

    def _prompt(self, case: Dict[str, Any], failure_types: List[str]) -> str:
        options = "\n".join(f"- {row['option_id']} [{row.get('tier_label', '')}] {row['option']}" for row in case.get("options") or [])
        feedback = "\n".join(f"- {item['id']}: {deidentify(item['text'])[:300]}" for item in case.get("feedback") or [])
        return f"""You are the reflection module of an aging-in-place care-planning assistant. A clinician reviewed the care plan drafted by a multi-agent care team for one patient and contested its argument graph. Learn reusable lessons from the clinician's operations. Return JSON only:
{{
  "episodic": {{"observation": "what the clinician changed and why, for a patient with this profile", "profile_pattern": "the patient characteristics that made it matter", "confidence": 0.0, "op_ids": ["H1"]}},
  "failures": [{{"failure_type": "one of the detected types", "stage": "one of the stages", "trigger_pattern": "...", "lesson": "...", "recommended_action": "...", "polarity": "do|avoid", "confidence": 0.0, "op_ids": ["..."]}}],
  "semantic": null or {{"generalizable_pattern": "why this generalizes beyond this patient", "stage": "...", "trigger_pattern": "...", "lesson": "...", "argument_pattern": "...", "recommended_action": "...", "applicability_scope": "...", "exceptions": ["..."], "polarity": "do|avoid", "confidence": 0.0, "op_ids": ["..."]}}
}}
Rules: cite only the op_ids listed below; describe patients by their characteristics, never by name, exact age, date or place; set "semantic" to null unless the pattern clearly generalizes to other patients; add a "failures" entry only for a detected failure type.

Patient profile: {', '.join(case.get('profile_tags') or []) or 'not available'}
Care options and their final assessment:
{options or '- none'}
Clinician operations (op_id | operation | stance | option | text | details):
{chr(10).join(describe_op(op) for op in case.get('ops') or [])}
Clinician feedback on the plan:
{feedback or '- none'}
Detected failure types: {', '.join(failure_types) or 'none'}
Stages: {', '.join(STAGES)}"""

    def _candidate(self, case: Dict[str, Any], memory_type: str, index: int, text: str, op_ids=None,
                   confidence=None, **fields) -> MemoryUpdateCandidate:
        op_ids = [op_id for op_id in (op_ids or []) if isinstance(op_id, str)]
        cited = [op for op in case.get("ops") or [] if op["op_id"] in set(op_ids)]
        try:
            confidence = max(0.0, min(1.0, float(confidence)))
        except (TypeError, ValueError):
            confidence = 0.6
        fields = {key: (deidentify(str(value))[:600] if isinstance(value, str) else value)
                  for key, value in fields.items() if value is not None}
        stage = fields.pop("stage", "general")
        return MemoryUpdateCandidate(
            candidate_id=f"cand_{stable_hash(case['case_id'] + memory_type + str(index) + case.get('ops_signature', ''))}",
            memory_type=memory_type,
            text=deidentify(" ".join(str(text).split()))[:600],
            source_case_id=case["case_id"],
            source_fingerprint=case.get("fingerprint"),
            stage=stage,
            semantic_signature=semantic_signature(memory_type, stage, fields.get("failure_type"), fields.get("polarity")),
            profile_tags=list(case.get("profile_tags") or []),
            grounding_op_ids=op_ids,
            grounding={"operations": [describe_op(op) for op in cited]},
            supervision_source="human_feedback",
            confidence=confidence,
            **fields,
        )

    def _fallback(self, case: Dict[str, Any]) -> MemoryUpdateCandidate:
        """Without a structured reflection, keep a plain episodic summary held for human review."""
        ops = case.get("ops") or []
        counts = {}
        for op in ops:
            counts[op["op"]] = counts.get(op["op"], 0) + 1
        summary = ", ".join(f"{count} {kind}" for kind, count in counts.items())
        tags = ", ".join((case.get("profile_tags") or [])[:5]) or "this profile"
        examples = "; ".join(describe_op(op).split(" | ", 4)[-1][:140] for op in ops[:2])
        candidate = self._candidate(
            case, "episodic", 0,
            text=f"For a patient with {tags}, the clinician made these changes ({summary}): {examples}",
            trigger_pattern=tags, stage="general", confidence=0.6, op_ids=[op["op_id"] for op in ops[:5]],
        )
        return candidate.model_copy(update={"verification_status": "under_review",
                                            "rejected_reason": "lesson_generation_failed"})


def memory_conflict_candidates(case: Dict[str, Any]) -> List[MemoryUpdateCandidate]:
    """A rejected memory-derived argument is direct, clinician-verified evidence against its memory."""
    candidates = []
    for op in case.get("ops") or []:
        if op.get("op") != "reject" or op.get("source") != "memory" or not op.get("memory_id"):
            continue
        reason = op.get("reason") or "the clinician removed it from the plan"
        candidates.append(MemoryUpdateCandidate(
            candidate_id=f"cand_{stable_hash(case['case_id'] + 'conflict' + op['memory_id'])}",
            memory_type=op.get("memory_type") or "episodic",
            text=deidentify(f"Did not apply for a patient with {', '.join((case.get('profile_tags') or [])[:4]) or 'this profile'}: "
                            f"{' '.join(str(op.get('content') or '').split())[:200]} ({reason})"),
            source_case_id=case["case_id"],
            source_fingerprint=case.get("fingerprint"),
            stage="argument_generation",
            semantic_relation="contradicts",
            related_memory_id=op["memory_id"],
            grounding_op_ids=[op["op_id"]],
            grounding={"operations": [describe_op(op)]},
            supervision_source="human_feedback",
            confidence=0.8,
            verified=True,
            verification_status="verified",
            verified_by="clinician_contestation",
            metadata={"conflict_target_memory_id": op["memory_id"]},
        ))
    return candidates

