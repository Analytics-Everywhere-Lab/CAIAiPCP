"""Memory records, adapted from SEMV's src/schemas/memory_schema.py.

``stage`` names the pipeline step a lesson guides (SEMV's claim_type), and
grounding cites the ids of the human operations it was learned from.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

MemoryType = Literal["episodic", "failure", "semantic_rule"]
MemoryLevel = Literal["short_term", "long_term"]
VerificationStatus = Literal["pending", "verified", "rejected", "under_review"]
LifecycleStatus = Literal["staged", "active", "under_review", "deprecated", "promoted", "merged", "expired"]
SemanticRelation = Literal["equivalent", "a_entails_b", "b_entails_a", "contradicts", "unrelated"]
Stage = Literal["option_generation", "argument_generation", "argument_validation", "plan_writing", "general"]

STAGES = ("option_generation", "argument_generation", "argument_validation", "plan_writing", "general")
TASK_TYPE = "aging_in_place_care_planning"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class MemoryRecord(BaseModel):
    """A long-term memory record."""

    model_config = ConfigDict(extra="allow")

    memory_id: str
    memory_type: MemoryType
    memory_level: MemoryLevel = "long_term"
    version: int = 1
    stage: str = "general"
    task_type: str = TASK_TYPE
    text: str = ""
    trigger_pattern: Optional[str] = None
    lesson: Optional[str] = None
    argument_pattern: Optional[str] = None
    recommended_action: Optional[str] = None
    failure_type: Optional[str] = None
    canonical_key: Optional[str] = None
    semantic_signature: Optional[str] = None
    applicability_scope: Optional[str] = None
    exceptions: List[str] = Field(default_factory=list)
    polarity: Optional[str] = None  # "do" | "avoid"
    profile_tags: List[str] = Field(default_factory=list)
    source_case_ids: List[str] = Field(default_factory=list)
    source_fingerprints: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    support_count: int = 1
    conflict_count: int = 0
    support_weight: float = 0.0
    conflict_weight: float = 0.0
    usage_count: int = 0
    successful_usage_count: int = 0
    contested_usage_count: int = 0
    unsuccessful_usage_count: int = 0
    last_used_at: Optional[str] = None
    last_confirmed_at: Optional[str] = None
    created_at: Optional[str] = Field(default_factory=utc_now_iso)
    updated_at: Optional[str] = None
    verified_by: Optional[str] = None
    status: LifecycleStatus = "active"
    origin: str = "consolidated"  # "consolidated" | "manual" | "seed"
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def fill_text(cls, data: Any) -> Any:
        if isinstance(data, dict) and not data.get("text"):
            data = dict(data)
            parts = [data.get("lesson"), data.get("recommended_action"), data.get("trigger_pattern")]
            data["text"] = " ".join(str(part) for part in parts if part) or data.get("memory_id", "")
        return data

    def independent_support(self) -> int:
        return max(self.support_count, len(set(self.source_fingerprints)), len(set(self.source_case_ids)))


class MemoryUpdateCandidate(BaseModel):
    """A lesson proposed by reflection on one case, before verification."""

    model_config = ConfigDict(extra="allow")

    candidate_id: str
    memory_type: MemoryType
    text: str
    source_case_id: str
    stage: str = "general"
    task_type: str = TASK_TYPE
    failure_type: Optional[str] = None
    trigger_pattern: Optional[str] = None
    lesson: Optional[str] = None
    argument_pattern: Optional[str] = None
    recommended_action: Optional[str] = None
    applicability_scope: Optional[str] = None
    exceptions: List[str] = Field(default_factory=list)
    polarity: Optional[str] = None
    profile_tags: List[str] = Field(default_factory=list)
    normalized_text: Optional[str] = None
    canonical_key: Optional[str] = None
    semantic_signature: Optional[str] = None
    source_fingerprint: Optional[str] = None
    semantic_relation: Optional[SemanticRelation] = None
    related_memory_id: Optional[str] = None
    grounding_op_ids: List[str] = Field(default_factory=list)
    supervision_source: str = "human_feedback"
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    rationale: Optional[str] = None
    grounding: Dict[str, Any] = Field(default_factory=dict)
    verified: bool = False
    verification_status: VerificationStatus = "pending"
    verified_by: Optional[str] = None
    rejected_reason: Optional[str] = None
    created_at: Optional[str] = Field(default_factory=utc_now_iso)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ShortTermMemoryRecord(BaseModel):
    """A verified, case-grounded observation staged for consolidation."""

    model_config = ConfigDict(extra="allow")

    stm_id: str
    candidate_id: str
    memory_type: MemoryType
    memory_level: MemoryLevel = "short_term"
    text: str
    source_case_id: str
    stage: str = "general"
    task_type: str = TASK_TYPE
    failure_type: Optional[str] = None
    trigger_pattern: Optional[str] = None
    lesson: Optional[str] = None
    argument_pattern: Optional[str] = None
    recommended_action: Optional[str] = None
    applicability_scope: Optional[str] = None
    exceptions: List[str] = Field(default_factory=list)
    polarity: Optional[str] = None
    profile_tags: List[str] = Field(default_factory=list)
    normalized_text: Optional[str] = None
    canonical_key: Optional[str] = None
    semantic_signature: Optional[str] = None
    source_fingerprint: Optional[str] = None
    semantic_relation: Optional[SemanticRelation] = None
    related_memory_id: Optional[str] = None
    grounding_op_ids: List[str] = Field(default_factory=list)
    supervision_source: str = "human_feedback"
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    verification_status: VerificationStatus = "pending"
    verified_by: Optional[str] = None
    rejected_reason: Optional[str] = None
    status: LifecycleStatus = "staged"
    promoted_to_memory_id: Optional[str] = None
    created_at: Optional[str] = Field(default_factory=utc_now_iso)
    staged_at: Optional[str] = Field(default_factory=utc_now_iso)
    updated_at: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_candidate(cls, candidate: MemoryUpdateCandidate) -> "ShortTermMemoryRecord":
        data = candidate.model_dump(exclude={"verified", "rationale", "grounding", "created_at"})
        data["metadata"] = {**candidate.metadata, "rationale": candidate.rationale,
                            "grounding": candidate.grounding}
        return cls(
            stm_id=f"stm_{candidate.candidate_id}",
            status="under_review" if candidate.verification_status == "under_review" else "staged",
            **data,
        )

    def grounded(self) -> bool:
        return bool(self.grounding_op_ids)


class MemoryUsageEvent(BaseModel):
    model_config = ConfigDict(extra="allow")

    event_id: str
    case_id: str
    memory_id: str
    stage: Literal["prompted", "argument_cited", "outcome"]
    outcome: Literal["successful", "unsuccessful", "contested", "unknown"] = "unknown"
    argument_id: Optional[str] = None
    created_at: Optional[str] = Field(default_factory=utc_now_iso)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConsolidationEvent(BaseModel):
    model_config = ConfigDict(extra="allow")

    event_id: str
    event_type: Literal[
        "staged", "promoted", "merged", "support_increment", "conflict", "under_review",
        "deprecated", "expired", "generalized", "generalization_failed", "generalization_recovered",
        "reactivated", "candidate_verification", "usage_rollup", "human_review", "snapshot",
    ]
    memory_id: Optional[str] = None
    stm_ids: List[str] = Field(default_factory=list)
    details: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[str] = Field(default_factory=utc_now_iso)


class ConsolidationResult(BaseModel):
    model_config = ConfigDict(extra="allow")

    started_at: str = Field(default_factory=utc_now_iso)
    finished_at: Optional[str] = None
    dry_run: bool = False
    stm_considered: int = 0
    promoted: List[str] = Field(default_factory=list)
    merged: List[str] = Field(default_factory=list)
    conflicted: List[str] = Field(default_factory=list)
    generalized: List[str] = Field(default_factory=list)
    deprecated: List[str] = Field(default_factory=list)
    under_review: List[str] = Field(default_factory=list)
    reactivated: List[str] = Field(default_factory=list)
    expired: List[str] = Field(default_factory=list)
    unchanged: List[str] = Field(default_factory=list)
    support_increments: Dict[str, int] = Field(default_factory=dict)
    changed_long_term_ids: List[str] = Field(default_factory=list)
    counts_before: Dict[str, int] = Field(default_factory=dict)
    counts_after: Dict[str, int] = Field(default_factory=dict)
    events: List[ConsolidationEvent] = Field(default_factory=list)
