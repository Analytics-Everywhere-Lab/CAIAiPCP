from dataclasses import dataclass, field

from env_config import MEMORY_CONSOLIDATE_EVERY_N, MEMORY_DIR, MEMORY_TOP_K


@dataclass
class PromotionThresholds:
    min_confidence: float
    min_distinct_cases: int


@dataclass
class MemoryConfig:
    """Lifecycle thresholds, following SEMV's configs/memory.yaml.

    A "case" is one care-planning session; independent support is counted per
    distinct patient description, so re-running the same patient text never
    counts as new evidence."""

    memory_dir: str = MEMORY_DIR
    short_term_max_records: int = 2000
    short_term_ttl_days: int = 60

    # Verification is fail-closed: any doubt keeps a candidate out of memory.
    verification_min_confidence: float = 0.60
    fail_policy: str = "under_review"  # or "reject"
    require_grounding: bool = True

    # Relation classification (lexical, with an LLM check for ambiguous pairs).
    duplicate_similarity: float = 0.85
    contradiction_similarity: float = 0.75
    lexical_shortlist_k: int = 20
    use_llm_relation_check: bool = True

    # Promotion from short-term to long-term memory. One clinician-reviewed
    # case may yield an episodic record; a semantic rule needs several cases.
    episodic: PromotionThresholds = field(default_factory=lambda: PromotionThresholds(0.75, 1))
    failure: PromotionThresholds = field(default_factory=lambda: PromotionThresholds(0.70, 2))
    semantic_rule: PromotionThresholds = field(default_factory=lambda: PromotionThresholds(0.75, 3))
    max_conflict_ratio: float = 0.20
    under_review_conflict_ratio: float = 0.30
    deprecate_confidence_below: float = 0.45
    generalize_repeated_episodes: bool = True
    consolidate_every_n_cases: int = MEMORY_CONSOLIDATE_EVERY_N

    # Retrieval of active long-term records as guidance.
    retrieval_top_k: int = MEMORY_TOP_K
    retrieval_min_similarity: float = 0.04
    retrieval_min_score: float = 0.12

    backups_to_keep: int = 20

    def thresholds_for(self, memory_type: str) -> PromotionThresholds:
        return {"episodic": self.episodic, "failure": self.failure}.get(memory_type, self.semantic_rule)
