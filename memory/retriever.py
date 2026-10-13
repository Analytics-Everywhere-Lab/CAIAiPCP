"""Retrieval of active long-term memory as guidance, adapted from SEMV's
memory_retriever.py: a semantic gate plus a weighted final score that also
rewards stage compatibility, patient-profile overlap, confidence, independent
support and past usage success."""
from typing import Any, Dict, List, Optional

from memory.config import MemoryConfig
from memory.schema import MemoryRecord
from memory.similarity import HybridSimilarity, content_tokens
from memory.store import MemoryStore

SCORE_WEIGHTS = {
    "similarity": 0.50,
    "compatibility": 0.15,
    "profile": 0.15,
    "confidence": 0.10,
    "support": 0.05,
    "usage": 0.05,
}


class MemoryRetriever:
    def __init__(self, store: MemoryStore, config: MemoryConfig, similarity: HybridSimilarity) -> None:
        self.store = store
        self.config = config
        self.similarity = similarity

    def retrieve(self, stage: str, query_text: str, profile_tags: Optional[List[str]] = None,
                 top_k: Optional[int] = None, memory_types: Optional[List[str]] = None,
                 exclude_case_id: Optional[str] = None) -> List[MemoryRecord]:
        records = self.store.load_long_term(memory_types, statuses=["active"])
        if exclude_case_id:
            # Memory transfers lessons across cases; a case already holds its own feedback,
            # and must not earn usage credit for lessons it produced.
            records = [record for record in records if exclude_case_id not in record.source_case_ids]
        query_tags = {tag.lower() for tag in profile_tags or []}
        scored = []
        for record in records:
            components = self._score(record, stage, query_text, query_tags)
            if (components["semantic_similarity"] >= self.config.retrieval_min_similarity
                    and components["final_score"] >= self.config.retrieval_min_score):
                scored.append((components["final_score"], record, components))
        scored.sort(key=lambda item: (item[0], item[1].memory_id), reverse=True)
        limit = top_k if top_k is not None else self.config.retrieval_top_k
        kept: List[tuple] = []
        for score, record, components in scored:
            if any(record.canonical_key and record.canonical_key == other.canonical_key for _, other, _ in kept):
                continue
            kept.append((score, record, components))
            if len(kept) >= limit:
                break
        return [
            record.model_copy(update={"metadata": {
                **record.metadata,
                "retrieval_score": round(score, 4),
                "retrieval_components": {key: round(value, 4) for key, value in components.items()},
            }})
            for score, record, components in kept
        ]

    def _score(self, record: MemoryRecord, stage: str, query_text: str, query_tags: set) -> Dict[str, float]:
        record_text = " ".join(str(part) for part in [
            record.text, record.lesson, record.trigger_pattern, record.argument_pattern,
            record.applicability_scope, " ".join(record.profile_tags),
        ] if part)
        semantic = max(0.0, min(1.0, self.similarity.similarity(query_text, record_text)))
        # Long patient descriptions dilute Jaccard similarity; also credit coverage of the trigger.
        trigger_tokens = content_tokens(record.trigger_pattern or record.text)
        coverage = len(trigger_tokens & content_tokens(query_text)) / len(trigger_tokens) if trigger_tokens else 0.0
        semantic = max(semantic, 0.6 * coverage)

        compatibility = 0.0
        if record.stage == stage:
            compatibility += 0.7
        elif record.stage == "general" or stage == "general":
            compatibility += 0.4
        if record.memory_type == "semantic_rule":
            compatibility += 0.3
        elif record.memory_type == "failure":
            compatibility += 0.2
        record_tags = {tag.lower() for tag in record.profile_tags}
        profile = len(record_tags & query_tags) / len(record_tags) if record_tags else 0.0
        support = min(1.0, record.independent_support() / 5.0)
        outcomes = record.successful_usage_count + record.unsuccessful_usage_count + record.contested_usage_count
        usage = record.successful_usage_count / outcomes if outcomes else 0.5
        final = (
            SCORE_WEIGHTS["similarity"] * semantic
            + SCORE_WEIGHTS["compatibility"] * min(1.0, compatibility)
            + SCORE_WEIGHTS["profile"] * profile
            + SCORE_WEIGHTS["confidence"] * record.confidence
            + SCORE_WEIGHTS["support"] * support
            + SCORE_WEIGHTS["usage"] * usage
        )
        return {
            "semantic_similarity": semantic,
            "compatibility": min(1.0, compatibility),
            "profile_overlap": profile,
            "confidence": record.confidence,
            "support": support,
            "usage_success": usage,
            "final_score": max(0.0, min(1.0, final)),
        }


def guidance_lines(records: List[MemoryRecord], max_chars: int = 260) -> List[str]:
    """Render retrieved memory compactly for prompts (guidance, never evidence)."""
    lines = []
    for record in records:
        text = record.text
        if record.recommended_action and record.recommended_action not in text:
            text = f"{text} Action: {record.recommended_action}"
        text = " ".join(text.split())
        if len(text) > max_chars:
            text = text[: max_chars - 3].rstrip() + "..."
        label = {"semantic_rule": "rule", "failure": "past error", "episodic": "past case"}[record.memory_type]
        lines.append(f"[{record.memory_id}] ({label}, confidence {record.confidence:.2f}, "
                     f"{record.independent_support()} case{'s' if record.independent_support() != 1 else ''}) {text}")
    return lines


def record_summary(record: MemoryRecord) -> Dict[str, Any]:
    return {
        "memory_id": record.memory_id,
        "memory_type": record.memory_type,
        "stage": record.stage,
        "text": record.text,
        "confidence": round(record.confidence, 3),
        "support": record.independent_support(),
        "retrieval_score": record.metadata.get("retrieval_score"),
    }
