"""Fail-closed verification of memory candidates, adapted from SEMV's
memory_verifier.py.

Stages: (0) de-identification, (1) grounding in the case's human operations,
(2) confidence threshold, (3) same-source duplicate check, (4) contradiction
with active memory (kept as conflict evidence, never as a competing rule),
(5) a deterministic over-generalization screen and (6) one batched LLM
safety check. Any LLM failure leaves a candidate under review -- never
silently accepted.
"""
import json
import re
from typing import Any, Callable, Dict, List, Optional, Set

from memory.config import MemoryConfig
from memory.schema import ConsolidationEvent, MemoryRecord, MemoryUpdateCandidate
from memory.similarity import HybridSimilarity, canonical_key, content_tokens, normalize_text, stable_hash
from memory.store import MemoryStore

_UNIVERSAL_TOKENS = {"always", "never", "all", "every", "guaranteed"}

_NAME_RE = re.compile(r"\b(?:Mr|Mrs|Ms|Miss|Mx|Dr)\.?\s+[A-Z][a-zA-Z'\-]+(?:\s+[A-Z][a-zA-Z'\-]+)?")
_EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
_PHONE_RE = re.compile(r"(?<!\w)(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}\b")
_DATE_RE = re.compile(r"\b(?:\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4})\b")
_ID_RE = re.compile(r"\b(?:MRN|HCN|health card(?: number)?|medical record(?: number)?)\s*[:#]?\s*[\w-]+", re.IGNORECASE)
_AGE_RE = re.compile(r"\b(\d{2,3})(\s*-?\s*years?\s*-?\s*old)\b", re.IGNORECASE)
_AGED_RE = re.compile(r"\baged?\s+(\d{2,3})\b", re.IGNORECASE)

TEXT_FIELDS = ("text", "lesson", "trigger_pattern", "argument_pattern", "recommended_action", "applicability_scope")


def deidentify(text: Optional[str]) -> Optional[str]:
    """Remove direct identifiers and coarsen exact ages to decades."""
    if not text:
        return text
    text = _NAME_RE.sub("the patient", text)
    text = _EMAIL_RE.sub("[email]", text)
    text = _PHONE_RE.sub("[phone]", text)
    text = _DATE_RE.sub("[date]", text)
    text = _ID_RE.sub("[identifier]", text)
    text = _AGE_RE.sub(lambda m: f"{int(m.group(1)) // 10 * 10}s{m.group(2)}", text)
    text = _AGED_RE.sub(lambda m: f"in their {int(m.group(1)) // 10 * 10}s", text)
    return text


def deidentify_candidate(candidate: MemoryUpdateCandidate) -> MemoryUpdateCandidate:
    updates: Dict[str, Any] = {field: deidentify(getattr(candidate, field)) for field in TEXT_FIELDS}
    updates["exceptions"] = [deidentify(item) for item in candidate.exceptions]
    return candidate.model_copy(update=updates)


class MemoryVerifier:
    def __init__(self, store: MemoryStore, config: MemoryConfig, similarity: HybridSimilarity,
                 llm_json: Optional[Callable[..., Any]] = None) -> None:
        self.store = store
        self.config = config
        self.similarity = similarity
        self.llm_json = llm_json

    def verify_batch(self, candidates: List[MemoryUpdateCandidate], valid_op_ids: Set[str]) -> List[MemoryUpdateCandidate]:
        existing = self.store.load_long_term(statuses=["active"])
        results: Dict[str, MemoryUpdateCandidate] = {}
        needs_llm: List[MemoryUpdateCandidate] = []
        for candidate in candidates:
            checked = self._deterministic(self._ensure_keys(deidentify_candidate(candidate)), valid_op_ids, existing)
            if checked.verification_status == "pending":
                needs_llm.append(checked)
            else:
                results[checked.candidate_id] = checked
        for checked in self._llm_verify(needs_llm):
            results[checked.candidate_id] = checked
        ordered = [results[candidate.candidate_id] for candidate in candidates]
        for result in ordered:
            self.store.append_event(ConsolidationEvent(
                event_id=f"evt_{stable_hash('verify' + result.candidate_id + result.verification_status)}",
                event_type="candidate_verification",
                stm_ids=[f"stm_{result.candidate_id}"],
                details={"candidate_id": result.candidate_id, "status": result.verification_status,
                         "reason": result.rejected_reason},
            ))
        return ordered

    # ---------------------------------------------------------- deterministic

    def _deterministic(self, candidate: MemoryUpdateCandidate, valid_op_ids: Set[str],
                       existing: List[MemoryRecord]) -> MemoryUpdateCandidate:
        if candidate.verification_status == "under_review" and candidate.rejected_reason:
            return candidate  # flagged by lesson generation (e.g. its fallback path)

        if self.config.require_grounding:
            if not candidate.grounding_op_ids:
                conflict = self._find_contradiction(candidate, existing)
                if conflict is not None:
                    return self._under_review(self._as_conflict(candidate, conflict), "ungrounded_contradiction")
                return self._rejected(candidate, "missing_grounding")
            if any(op_id not in valid_op_ids for op_id in candidate.grounding_op_ids):
                return self._under_review(candidate, "grounding_ops_not_in_case")

        if candidate.confidence < self.config.verification_min_confidence:
            return self._rejected(candidate, "confidence_below_threshold")

        for record in existing:
            if (record.canonical_key or "") == candidate.canonical_key and (
                candidate.source_case_id in record.source_case_ids
                or (candidate.source_fingerprint and candidate.source_fingerprint in record.source_fingerprints)
            ):
                return self._rejected(candidate, "duplicate_from_same_source")

        conflict = self._find_contradiction(candidate, existing)
        if conflict is not None:
            return self._as_conflict(candidate, conflict)  # still verified by the LLM below

        if candidate.memory_type == "semantic_rule" and content_tokens(candidate.text) & _UNIVERSAL_TOKENS:
            return self._under_review(candidate, "single_case_overgeneralization")
        return candidate

    def _find_contradiction(self, candidate: MemoryUpdateCandidate, existing: List[MemoryRecord]) -> Optional[MemoryRecord]:
        items = [record.model_dump() for record in existing]
        shortlisted = [item for _, item in self.similarity.shortlist(candidate.text, items)]
        if not shortlisted:
            return None
        relations = self.similarity.relations_batch([(candidate.model_dump(), item) for item in shortlisted])
        by_id = {record.memory_id: record for record in existing}
        for relation, item in zip(relations, shortlisted):
            if relation == "contradicts":
                return by_id.get(item.get("memory_id", ""))
        return None

    # ------------------------------------------------------------------- LLM

    def _llm_verify(self, candidates: List[MemoryUpdateCandidate]) -> List[MemoryUpdateCandidate]:
        if not candidates:
            return []
        if self.llm_json is None:
            return [self._fail_closed(candidate, "llm_verification_unavailable") for candidate in candidates]
        payload = [
            {
                "candidate_id": candidate.candidate_id,
                "memory_type": candidate.memory_type,
                "stage": candidate.stage,
                "lesson": candidate.text,
                "trigger": candidate.trigger_pattern,
                "recommended_action": candidate.recommended_action,
                "contradicts_existing_lesson": candidate.semantic_relation == "contradicts",
                "rationale": candidate.rationale,
                "grounding": candidate.grounding.get("operations", []),
            }
            for candidate in candidates
        ]
        prompt = (
            "You verify lessons before they are stored in the long-term memory of an aging-in-place "
            "care-planning assistant. Each lesson was learned from one clinician's review of a care plan. "
            "Approve a lesson only if it is clinically safe, supported by its grounding (the clinician's "
            "operations on the argument graph), and phrased so it can guide future cases without "
            "identifying anyone (no names, exact ages, dates or places). Reject lessons that turn one case "
            "into a universal rule, or that the grounding does not support.\n"
            'Return JSON {"results": [{"candidate_id": "...", "verified": true, "reason": "..."}]}\n'
            f"Candidates: {json.dumps(payload, ensure_ascii=False)}"
        )
        try:
            data = self.llm_json(prompt, temperature=0.0, max_tokens=2048)
            rows = data.get("results") if isinstance(data, dict) else data
            by_id = {str(row.get("candidate_id")): row for row in rows or [] if isinstance(row, dict)}
        except Exception:
            by_id = {}
        checked = []
        for candidate in candidates:
            row = by_id.get(candidate.candidate_id)
            if row is None or "verified" not in row:
                checked.append(self._fail_closed(candidate, "llm_verification_invalid_response"))
            elif row.get("verified") is True or str(row.get("verified")).lower() == "true":
                checked.append(candidate.model_copy(update={
                    "verified": True, "verification_status": "verified",
                    "verified_by": "memory_verifier_llm", "rejected_reason": None,
                }))
            else:
                checked.append(self._rejected(candidate, str(row.get("reason") or "llm_rejected")[:300]))
        return checked

    # --------------------------------------------------------------- helpers

    @staticmethod
    def _ensure_keys(candidate: MemoryUpdateCandidate) -> MemoryUpdateCandidate:
        return candidate.model_copy(update={
            "normalized_text": normalize_text(candidate.text),
            "canonical_key": canonical_key(candidate.memory_type, candidate.stage, candidate.text),
        })

    @staticmethod
    def _as_conflict(candidate: MemoryUpdateCandidate, record: MemoryRecord) -> MemoryUpdateCandidate:
        return candidate.model_copy(update={
            "semantic_relation": "contradicts",
            "related_memory_id": record.memory_id,
            "metadata": {**candidate.metadata, "conflict_target_memory_id": record.memory_id},
        })

    def _fail_closed(self, candidate: MemoryUpdateCandidate, reason: str) -> MemoryUpdateCandidate:
        if self.config.fail_policy == "reject":
            return self._rejected(candidate, reason)
        return self._under_review(candidate, reason)

    @staticmethod
    def _rejected(candidate: MemoryUpdateCandidate, reason: str) -> MemoryUpdateCandidate:
        return candidate.model_copy(update={"verified": False, "verification_status": "rejected", "rejected_reason": reason})

    @staticmethod
    def _under_review(candidate: MemoryUpdateCandidate, reason: str) -> MemoryUpdateCandidate:
        return candidate.model_copy(update={"verified": False, "verification_status": "under_review", "rejected_reason": reason})
