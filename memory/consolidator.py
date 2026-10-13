"""Multi-case consolidation from short-term to long-term memory, adapted from
SEMV's memory_consolidator.py.

Verified short-term observations are compared with long-term memory through
semantic relations. Equivalent or entailing observations add independent
support (one vote per distinct patient description) with a Beta-style
confidence update; contradicting ones are recorded as conflict evidence
against the existing record and never promoted as a competing rule. The rest
are clustered and promoted once they meet the per-type thresholds. A
long-term episodic or failure record that accumulates enough independent cases
is generalized into a semantic rule, which is only activated after an LLM
check confirms it is consistent with every source observation. Nothing is
silently deleted: expired and deprecated records are archived.
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from memory.config import MemoryConfig
from memory.schema import (
    ConsolidationEvent,
    ConsolidationResult,
    MemoryRecord,
    MemoryUpdateCandidate,
    ShortTermMemoryRecord,
    utc_now_iso,
)
from memory.similarity import HybridSimilarity, canonical_key, semantic_signature, stable_hash
from memory.store import MemoryStore
from memory.verifier import deidentify

logger = logging.getLogger(__name__)

ENTAILING = ("equivalent", "a_entails_b", "b_entails_a")
RETRYABLE_REVIEW_REASONS = (
    "generalization_synthesis_failed",
    "generalization_verification_unavailable",
    "generalization_confidence_below_threshold",
)


class GeneralizedRule(BaseModel):
    trigger_pattern: str
    lesson: str
    argument_pattern: Optional[str] = None
    recommended_action: str
    applicability_scope: Optional[str] = None
    exceptions: List[str] = Field(default_factory=list)
    polarity: Optional[str] = None
    confidence: float = Field(default=0.75, ge=0.0, le=1.0)


def _event(event_type: str, key: str, memory_id: Optional[str] = None,
           stm_ids: Optional[List[str]] = None, **details) -> ConsolidationEvent:
    return ConsolidationEvent(
        event_id=f"evt_{stable_hash(event_type + key)}",
        event_type=event_type,
        memory_id=memory_id,
        stm_ids=stm_ids or [],
        details=details,
    )


def _fingerprint(row) -> str:
    if isinstance(row, dict):
        return str(row.get("source_fingerprint") or f"fp_case_{row.get('case_id')}")
    return str(row.source_fingerprint or f"fp_case_{row.source_case_id}")


def _case_id(row) -> str:
    return str(row.get("case_id")) if isinstance(row, dict) else str(row.source_case_id)


def independent(rows: list, seen_cases=(), seen_fingerprints=()) -> list:
    """Keep rows whose case and source fingerprint are both unseen."""
    cases, fingerprints = set(seen_cases), set(seen_fingerprints)
    accepted = []
    for row in rows:
        case_id, fingerprint = _case_id(row), _fingerprint(row)
        if case_id in cases or fingerprint in fingerprints:
            continue
        cases.add(case_id)
        fingerprints.add(fingerprint)
        accepted.append(row)
    return accepted


def _observation(row: ShortTermMemoryRecord) -> Dict[str, Any]:
    return {
        "case_id": row.source_case_id,
        "source_fingerprint": _fingerprint(row),
        "stm_id": row.stm_id,
        "text": row.text,
        "trigger_pattern": row.trigger_pattern,
        "recommended_action": row.recommended_action,
        "confidence": row.confidence,
        "grounded": row.grounded(),
    }


def _parse_time(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


class MemoryConsolidator:
    def __init__(self, store: MemoryStore, config: MemoryConfig, similarity: HybridSimilarity,
                 llm_json: Optional[Callable[..., Any]] = None) -> None:
        self.store = store
        self.config = config
        self.similarity = similarity
        self.llm_json = llm_json

    # ---------------------------------------------------------------- staging

    def stage(self, candidates: List[MemoryUpdateCandidate]) -> List[ShortTermMemoryRecord]:
        """Stage verified (or held-for-review) candidates; promotion only happens in consolidate()."""
        staged = []
        for candidate in candidates:
            if candidate.verification_status not in ("verified", "under_review"):
                continue
            staged.append(self.store.stage(ShortTermMemoryRecord.from_candidate(candidate)))
        return staged

    # ----------------------------------------------------------- consolidation

    def consolidate(self, dry_run: bool = False, retry_under_review: bool = False) -> ConsolidationResult:
        with self.store.transaction():
            return self._consolidate(dry_run, retry_under_review)

    def _consolidate(self, dry_run: bool, retry_under_review: bool) -> ConsolidationResult:
        result = ConsolidationResult(dry_run=dry_run, counts_before=self.store.counts())
        events: List[ConsolidationEvent] = []
        now = datetime.now(timezone.utc)
        stm_all = self.store.load_short_term()
        ltm_by_id = {record.memory_id: record for record in self.store.load_long_term()}
        changed: Dict[str, MemoryRecord] = {}
        stm_updates: Dict[str, ShortTermMemoryRecord] = {}
        expired_rows: List[ShortTermMemoryRecord] = []

        def current() -> List[MemoryRecord]:
            return list({**ltm_by_id, **changed}.values())

        usage_updates, usage_events = self._rollup_usage(ltm_by_id)
        changed.update(usage_updates)
        events.extend(usage_events)

        # A. Select verified, unprocessed observations; expire stale ones.
        cutoff = now - timedelta(days=self.config.short_term_ttl_days)
        actionable = []
        for row in stm_all:
            if row.status in ("promoted", "merged", "expired"):
                continue
            if (_parse_time(row.staged_at) or now) < cutoff:
                expired = row.model_copy(update={"status": "expired", "updated_at": utc_now_iso()})
                stm_updates[row.stm_id] = expired
                expired_rows.append(expired)
                result.expired.append(row.stm_id)
                events.append(_event("expired", row.stm_id, stm_ids=[row.stm_id]))
            elif row.status == "staged" and row.verification_status == "verified":
                actionable.append(row)
            elif row.status == "under_review":
                result.under_review.append(row.stm_id)
        result.stm_considered = len(actionable)

        # B. Relate each observation to long-term memory.
        remaining = []
        for row in actionable:
            relation, target = self._best_relation(row, current())
            if relation in ENTAILING and target is not None:
                updated, incremented = self._merge_support(target, row, relation)
                if incremented:
                    changed[updated.memory_id] = updated
                    result.support_increments[updated.memory_id] = result.support_increments.get(updated.memory_id, 0) + 1
                    events.append(_event("support_increment", "merge" + row.stm_id, updated.memory_id, [row.stm_id],
                                         relation=relation, source_case_id=row.source_case_id))
                stm_updates[row.stm_id] = row.model_copy(update={
                    "status": "merged", "promoted_to_memory_id": updated.memory_id, "updated_at": utc_now_iso()})
                result.merged.append(row.stm_id)
                events.append(_event("merged", row.stm_id, updated.memory_id, [row.stm_id], relation=relation,
                                     counted=incremented))
            elif relation == "contradicts" and target is not None:
                updated, counted = self._apply_conflict(target, row)
                if counted:
                    changed[updated.memory_id] = updated
                stm_updates[row.stm_id] = row.model_copy(update={
                    "status": "under_review", "promoted_to_memory_id": updated.memory_id, "updated_at": utc_now_iso()})
                result.conflicted.append(row.stm_id)
                if updated.status == "under_review" and target.status != "under_review":
                    result.under_review.append(updated.memory_id)
                    events.append(_event("under_review", updated.memory_id + row.stm_id, updated.memory_id,
                                         [row.stm_id], reason="conflict_ratio_exceeded"))
                events.append(_event("conflict", row.stm_id, updated.memory_id, [row.stm_id], counted=counted,
                                     source_case_id=row.source_case_id))
            else:
                remaining.append(row)

        # C. Cluster the rest and promote clusters that meet the thresholds.
        for cluster in self._cluster(remaining):
            promoted = self._try_promote(cluster, {**ltm_by_id, **changed})
            if promoted is None:
                result.unchanged.extend(row.stm_id for row in cluster)
                continue
            changed[promoted.memory_id] = promoted
            for row in cluster:
                stm_updates[row.stm_id] = row.model_copy(update={
                    "status": "promoted", "promoted_to_memory_id": promoted.memory_id, "updated_at": utc_now_iso()})
                result.promoted.append(row.stm_id)
            events.append(_event("promoted", promoted.memory_id, promoted.memory_id, [row.stm_id for row in cluster],
                                 memory_type=promoted.memory_type, support_count=promoted.support_count,
                                 confidence=round(promoted.confidence, 4)))

        # D. Generalize repeated episodes and failures into semantic rules.
        if self.config.generalize_repeated_episodes:
            for record in current():
                if record.metadata.get("generalized_rule_id"):
                    self._propagate_to_rule(record, {**ltm_by_id, **changed}, changed, result, events)
                    continue
                generalized = self._try_generalize(record, current(), events)
                if generalized is None:
                    continue
                rule, created = generalized
                changed[rule.memory_id] = rule
                linked = changed.get(record.memory_id, record)
                changed[record.memory_id] = linked.model_copy(update={
                    "metadata": {**linked.metadata, "generalized_rule_id": rule.memory_id,
                                 "generalized_at_support": len(linked.metadata.get("observations", []))},
                    "updated_at": utc_now_iso(),
                })
                if created:
                    result.generalized.append(rule.memory_id)
                else:
                    result.support_increments[rule.memory_id] = result.support_increments.get(rule.memory_id, 0) + 1

        # E. Explicitly retry rule proposals whose LLM-dependent step could not complete.
        if retry_under_review:
            for proposal in current():
                metadata = proposal.metadata or {}
                if (proposal.memory_type == "semantic_rule" and proposal.status == "under_review"
                        and metadata.get("proposal_only")
                        and metadata.get("review_reason") in RETRYABLE_REVIEW_REASONS):
                    retried = self._reconsider(proposal, events)
                    changed[retried.memory_id] = retried
                    if retried.status == "active":
                        result.reactivated.append(retried.memory_id)

        # F. Lifecycle re-check across long-term memory.
        for record in current():
            rechecked = self._lifecycle(record, result, events)
            if rechecked is not record:
                changed[record.memory_id] = rechecked

        result.changed_long_term_ids = sorted(changed)
        result.events = events
        if not dry_run:
            deprecated = [record for record in changed.values() if record.status == "deprecated"]
            self.store.archive(deprecated, "deprecated_long_term")
            self.store.upsert_long_term(list(changed.values()))
            if expired_rows:
                self.store.archive(expired_rows, "short_term_expired")
                kept = [row for row in {**{r.stm_id: r for r in stm_all}, **stm_updates}.values()
                        if row.status != "expired"]
                self.store.replace_short_term(kept)
            else:
                self.store.upsert_short_term(list(stm_updates.values()))
            for event in events:
                self.store.append_event(event)
            result.counts_after = self.store.counts()
        else:
            result.counts_after = result.counts_before
        result.finished_at = utc_now_iso()
        return result

    # ------------------------------------------------------------- relations

    def _best_relation(self, row: ShortTermMemoryRecord, ltm: List[MemoryRecord]) -> Tuple[str, Optional[MemoryRecord]]:
        if row.semantic_relation == "contradicts" and row.related_memory_id:
            target = next((item for item in ltm if item.memory_id == row.related_memory_id
                           and item.status in ("active", "under_review")), None)
            if target is not None:
                return "contradicts", target
        candidates = [item for item in ltm if item.memory_type == row.memory_type
                      and item.status in ("active", "under_review")]
        if not candidates:
            return "unrelated", None
        shortlisted = [item for _, item in self.similarity.shortlist(row.text, [c.model_dump() for c in candidates])]
        relations = self.similarity.relations_batch([(row.model_dump(), item) for item in shortlisted])
        priority = {"equivalent": 4, "contradicts": 3, "a_entails_b": 2, "b_entails_a": 2}
        ranked = [
            (priority.get(relation, 0), self.similarity.similarity(row.text, item.get("text") or ""), relation, item)
            for relation, item in zip(relations, shortlisted) if relation != "unrelated"
        ]
        if not ranked:
            return "unrelated", None
        _, _, relation, item = max(ranked, key=lambda value: (value[0], value[1]))
        by_id = {record.memory_id: record for record in candidates}
        return relation, by_id.get(item.get("memory_id", ""))

    @staticmethod
    def _prior(record: MemoryRecord) -> Tuple[float, float]:
        metadata = record.metadata or {}
        if "alpha" in metadata and "beta" in metadata:
            return float(metadata["alpha"]), float(metadata["beta"])
        strength = max(1, record.support_count)
        return record.confidence * strength, (1.0 - record.confidence) * strength

    def _merge_support(self, target: MemoryRecord, row: ShortTermMemoryRecord, relation: str) -> Tuple[MemoryRecord, bool]:
        if not independent([row], target.source_case_ids, target.source_fingerprints):
            return target, False  # the same patient never counts twice
        alpha, beta = self._prior(target)
        alpha += row.confidence
        beta += 1.0 - row.confidence
        metadata = dict(target.metadata)
        metadata.update({"alpha": alpha, "beta": beta})
        metadata["observations"] = list(metadata.get("observations", [])) + [_observation(row)]
        text = target.text
        if relation in ("a_entails_b", "b_entails_a"):
            # Keep the more specific statement; remember the broader one.
            broader = metadata.setdefault("broader_variants", [])
            if relation == "a_entails_b":  # the new observation is the more specific one
                if target.text not in broader:
                    broader.append(target.text)
                text = row.text
            elif row.text not in broader:
                broader.append(row.text)
        return target.model_copy(update={
            "text": text,
            "version": target.version + 1,
            "confidence": alpha / (alpha + beta),
            "support_count": target.support_count + 1,
            "support_weight": target.support_weight + row.confidence,
            "source_case_ids": target.source_case_ids + [row.source_case_id],
            "source_fingerprints": target.source_fingerprints + [_fingerprint(row)],
            "profile_tags": sorted(set(target.profile_tags) | set(row.profile_tags))[:20],
            "last_confirmed_at": utc_now_iso(),
            "updated_at": utc_now_iso(),
            "metadata": metadata,
        }), True

    def _apply_conflict(self, target: MemoryRecord, row: ShortTermMemoryRecord) -> Tuple[MemoryRecord, bool]:
        """Record contradicting evidence on the target; the observation itself is never promoted."""
        metadata = dict(target.metadata)
        conflict_cases = list(metadata.get("conflict_case_ids", []))
        conflict_fingerprints = list(metadata.get("conflict_fingerprints", []))
        if row.source_case_id in conflict_cases or _fingerprint(row) in conflict_fingerprints:
            return target, False
        alpha, beta = self._prior(target)
        alpha += 1.0 - row.confidence
        beta += row.confidence
        metadata.update({
            "alpha": alpha, "beta": beta,
            "conflict_case_ids": conflict_cases + [row.source_case_id],
            "conflict_fingerprints": conflict_fingerprints + [_fingerprint(row)],
            "conflict_texts": (list(metadata.get("conflict_texts", [])) + [row.text])[-10:],
        })
        conflict_count = target.conflict_count + 1
        ratio = conflict_count / max(1, target.support_count + conflict_count)
        status = target.status
        if status == "active" and ratio > self.config.under_review_conflict_ratio:
            status = "under_review"
        return target.model_copy(update={
            "version": target.version + 1,
            "confidence": alpha / (alpha + beta),
            "conflict_count": conflict_count,
            "conflict_weight": target.conflict_weight + row.confidence,
            "status": status,
            "updated_at": utc_now_iso(),
            "metadata": metadata,
        }), True

    # -------------------------------------------------------------- promotion

    def _cluster(self, rows: List[ShortTermMemoryRecord]) -> List[List[ShortTermMemoryRecord]]:
        blocks: Dict[str, List[ShortTermMemoryRecord]] = {}
        for row in rows:
            signature = row.semantic_signature or semantic_signature(row.memory_type, row.stage, row.failure_type, row.polarity)
            blocks.setdefault(signature, []).append(row)
        clusters = []
        for block in blocks.values():
            unassigned = list(block)
            while unassigned:
                seed = unassigned.pop(0)
                cluster, rest = [seed], []
                for other in unassigned:
                    if self.similarity.relation(seed.model_dump(), other.model_dump()) in ENTAILING:
                        cluster.append(other)
                    else:
                        rest.append(other)
                unassigned = rest
                clusters.append(cluster)
        return clusters

    def _try_promote(self, cluster: List[ShortTermMemoryRecord], ltm_by_id: Dict[str, MemoryRecord]) -> Optional[MemoryRecord]:
        representative = max(cluster, key=lambda row: row.confidence)
        thresholds = self.config.thresholds_for(representative.memory_type)
        rows = independent(cluster)
        alpha = sum(row.confidence for row in rows)
        beta = sum(1.0 - row.confidence for row in rows)
        confidence = alpha / (alpha + beta) if alpha + beta else 0.0
        if len(rows) < thresholds.min_distinct_cases or confidence < thresholds.min_confidence:
            return None
        if not representative.grounded():
            return None
        key = representative.canonical_key or canonical_key(representative.memory_type, representative.stage, representative.text)
        memory_id = f"mem_{stable_hash(key)}"
        if memory_id in ltm_by_id:
            return None  # same identity already exists; it should have been merged
        now = utc_now_iso()
        return MemoryRecord(
            memory_id=memory_id,
            memory_type=representative.memory_type,
            stage=representative.stage,
            text=representative.text,
            trigger_pattern=representative.trigger_pattern,
            lesson=representative.lesson,
            argument_pattern=representative.argument_pattern,
            recommended_action=representative.recommended_action,
            failure_type=representative.failure_type,
            canonical_key=key,
            semantic_signature=representative.semantic_signature,
            applicability_scope=representative.applicability_scope,
            exceptions=list(representative.exceptions),
            polarity=representative.polarity,
            profile_tags=sorted({tag for row in rows for tag in row.profile_tags})[:20],
            source_case_ids=sorted(row.source_case_id for row in rows),
            source_fingerprints=sorted(_fingerprint(row) for row in rows),
            confidence=confidence,
            support_count=len(rows),
            support_weight=alpha,
            status="active",
            origin="consolidated",
            verified_by="memory_consolidator",
            created_at=now,
            updated_at=now,
            last_confirmed_at=now,
            metadata={
                "alpha": alpha,
                "beta": beta,
                "stm_ids": [row.stm_id for row in cluster],
                "observations": [_observation(row) for row in rows],
                "supervision_sources": sorted({row.supervision_source for row in rows}),
            },
        )

    # --------------------------------------------------------- generalization

    def _try_generalize(self, record: MemoryRecord, ltm: List[MemoryRecord],
                        events: List[ConsolidationEvent]) -> Optional[Tuple[MemoryRecord, bool]]:
        """Generalize a well-supported episodic/failure record into a semantic rule.

        Returns (rule, created). When an equivalent rule already exists (e.g. an
        episodic and a failure record describe the same pattern), the source
        observations are merged into it instead of creating a duplicate."""
        if record.memory_type not in ("episodic", "failure") or record.status != "active":
            return None
        if record.metadata.get("generalized_rule_id"):
            return None
        observations = independent(list(record.metadata.get("observations", [])))
        thresholds = self.config.semantic_rule
        if len(observations) < thresholds.min_distinct_cases:
            return None
        rule, synthesized = self._synthesize(observations)
        verified, verification_reason = self._verify_rule(rule, observations) if synthesized else (False, "generalization_synthesis_failed")
        review_reason = None
        if not synthesized:
            review_reason = "generalization_synthesis_failed"
        elif not verified:
            review_reason = verification_reason
        elif rule.confidence < thresholds.min_confidence:
            review_reason = "generalization_confidence_below_threshold"
        elif not all(row.get("grounded") for row in observations):
            review_reason = "generalization_grounding_unavailable"
        active = review_reason is None
        key = canonical_key("semantic_rule", record.stage, rule.lesson)
        memory_id = f"mem_{stable_hash(key)}"
        if any(item.memory_id == memory_id for item in ltm):
            return None
        alpha = sum(float(row.get("confidence", 0.0)) for row in observations)
        beta = sum(1.0 - float(row.get("confidence", 0.0)) for row in observations)
        now = utc_now_iso()
        proposed = MemoryRecord(
            memory_id=memory_id,
            memory_type="semantic_rule",
            stage=record.stage,
            text=rule.lesson,
            trigger_pattern=rule.trigger_pattern,
            lesson=rule.lesson,
            argument_pattern=rule.argument_pattern,
            recommended_action=rule.recommended_action,
            canonical_key=key,
            semantic_signature=semantic_signature("semantic_rule", record.stage, None, rule.polarity),
            applicability_scope=rule.applicability_scope,
            exceptions=list(rule.exceptions),
            polarity=rule.polarity,
            profile_tags=list(record.profile_tags),
            source_case_ids=sorted({str(row["case_id"]) for row in observations}),
            source_fingerprints=sorted({_fingerprint(row) for row in observations}),
            confidence=rule.confidence,
            support_count=len(observations),
            support_weight=alpha,
            status="active" if active else "under_review",
            origin="consolidated",
            verified_by="memory_consolidator_generalization" if active else None,
            created_at=now,
            updated_at=now,
            last_confirmed_at=now,
            metadata={
                "alpha": alpha,
                "beta": beta,
                "generalized_from_memory_id": record.memory_id,
                "observations": observations,
                "proposal_only": not active,
                "review_reason": review_reason,
                "attempts": 1,
            },
        )
        equivalent = self._equivalent_rule(proposed, ltm)
        if equivalent is not None:
            merged = self._merge_rule_support(equivalent, observations)
            events.append(_event("support_increment", "generalize" + record.memory_id + equivalent.memory_id,
                                 equivalent.memory_id, source_memory_id=record.memory_id, generalized=True))
            return merged, False
        events.append(_event("generalized" if active else "generalization_failed", memory_id, memory_id,
                             source_memory_id=record.memory_id, support=len(observations), reason=review_reason))
        return proposed, True

    def _propagate_to_rule(self, record: MemoryRecord, ltm_by_id: Dict[str, MemoryRecord],
                           changed: Dict[str, MemoryRecord], result: ConsolidationResult,
                           events: List[ConsolidationEvent]) -> None:
        """New independent support for a generalized record also supports its rule."""
        rule = ltm_by_id.get(record.metadata["generalized_rule_id"])
        observations = list(record.metadata.get("observations", []))
        seen = int(record.metadata.get("generalized_at_support", len(observations)))
        if rule is None or rule.status not in ("active", "under_review") or len(observations) <= seen:
            return
        merged = self._merge_rule_support(rule, observations[seen:])
        changed[record.memory_id] = record.model_copy(update={
            "metadata": {**record.metadata, "generalized_at_support": len(observations)}})
        if merged is not rule:
            changed[rule.memory_id] = merged
            result.support_increments[rule.memory_id] = result.support_increments.get(rule.memory_id, 0) + 1
            events.append(_event("support_increment", "propagate" + rule.memory_id + str(len(observations)),
                                 rule.memory_id, source_memory_id=record.memory_id, generalized=True))

    def _equivalent_rule(self, proposed: MemoryRecord, ltm: List[MemoryRecord]) -> Optional[MemoryRecord]:
        rules = [row for row in ltm if row.memory_type == "semantic_rule" and row.status in ("active", "under_review")]
        if not rules:
            return None
        relations = self.similarity.relations_batch([(proposed.model_dump(), row.model_dump()) for row in rules])
        related = [(self.similarity.similarity(proposed.text, row.text), row)
                   for row, relation in zip(rules, relations) if relation in ENTAILING]
        return max(related, key=lambda pair: pair[0])[1] if related else None

    def _merge_rule_support(self, rule: MemoryRecord, observations: List[Dict[str, Any]]) -> MemoryRecord:
        unseen = independent(observations, rule.source_case_ids, rule.source_fingerprints)
        if not unseen:
            return rule
        alpha, beta = self._prior(rule)
        alpha += sum(float(row.get("confidence", 0.0)) for row in unseen)
        beta += sum(1.0 - float(row.get("confidence", 0.0)) for row in unseen)
        metadata = {**rule.metadata, "alpha": alpha, "beta": beta,
                    "observations": list(rule.metadata.get("observations", [])) + unseen}
        # The synthesized rule keeps its own confidence; alpha/beta track grounded support.
        return rule.model_copy(update={
            "version": rule.version + 1,
            "support_count": rule.support_count + len(unseen),
            "support_weight": rule.support_weight + sum(float(row.get("confidence", 0.0)) for row in unseen),
            "source_case_ids": sorted(set(rule.source_case_ids) | {str(row["case_id"]) for row in unseen}),
            "source_fingerprints": sorted(set(rule.source_fingerprints) | {_fingerprint(row) for row in unseen}),
            "last_confirmed_at": utc_now_iso(),
            "updated_at": utc_now_iso(),
            "metadata": metadata,
        })

    def _synthesize(self, observations: List[Dict[str, Any]]) -> Tuple[GeneralizedRule, bool]:
        prompt = (
            "These observations come from independent clinician reviews of aging-in-place care plans and "
            "describe the same pattern. Synthesize ONE general rule that would improve future care plans. "
            "Do not include names, ages, dates or places. Return JSON only: "
            '{"trigger_pattern": "patients or situations it applies to", "lesson": "...", '
            '"argument_pattern": "...", "recommended_action": "...", "applicability_scope": "...", '
            '"exceptions": ["..."], "polarity": "do|avoid", "confidence": 0.0}\n'
            f"Observations: {[{k: row.get(k) for k in ('text', 'trigger_pattern', 'recommended_action', 'confidence')} for row in observations]}"
        )
        try:
            if self.llm_json is None:
                raise RuntimeError("llm_unavailable")
            data = self.llm_json(prompt, temperature=0.2, max_tokens=1024)
            rule = GeneralizedRule.model_validate(data)
            return rule.model_copy(update={
                "lesson": deidentify(rule.lesson),
                "trigger_pattern": deidentify(rule.trigger_pattern),
                "recommended_action": deidentify(rule.recommended_action),
            }), True
        except Exception as exc:
            logger.warning("Rule generalization held for review: %s", exc)
            best = max(observations, key=lambda row: float(row.get("confidence", 0.0)))
            return GeneralizedRule(
                trigger_pattern=best.get("trigger_pattern") or best.get("text") or "",
                lesson=best.get("text") or "",
                recommended_action="Review the repeated pattern before reuse.",
                confidence=min(0.6, float(best.get("confidence", 0.0))),
            ), False

    def _verify_rule(self, rule: GeneralizedRule, observations: List[Dict[str, Any]]) -> Tuple[bool, str]:
        prompt = (
            "Check whether this generalized care-planning rule is consistent with EVERY source observation "
            "and safe to apply to future patients. Return JSON only: "
            '{"consistent_with_all": true, "reason": "..."}\n'
            f"Rule: {rule.model_dump()}\nObservations: {[row.get('text') for row in observations]}"
        )
        try:
            if self.llm_json is None:
                raise RuntimeError("llm_unavailable")
            data = self.llm_json(prompt, temperature=0.0, max_tokens=512)
            if isinstance(data, dict) and data.get("consistent_with_all") is True:
                return True, "generalization_verified"
            return False, "generalization_verification_failed"
        except Exception:
            return False, "generalization_verification_unavailable"

    def _reconsider(self, proposal: MemoryRecord, events: List[ConsolidationEvent]) -> MemoryRecord:
        observations = independent(list(proposal.metadata.get("observations", [])))
        rule, synthesized = self._synthesize(observations)
        verified = synthesized and self._verify_rule(rule, observations)[0]
        active = verified and rule.confidence >= self.config.semantic_rule.min_confidence
        metadata = {**proposal.metadata, "attempts": int(proposal.metadata.get("attempts", 1)) + 1,
                    "proposal_only": not active,
                    "review_reason": None if active else proposal.metadata.get("review_reason")}
        updates: Dict[str, Any] = {"metadata": metadata, "version": proposal.version + 1, "updated_at": utc_now_iso()}
        if synthesized:
            updates.update({"text": rule.lesson, "lesson": rule.lesson, "trigger_pattern": rule.trigger_pattern,
                            "recommended_action": rule.recommended_action, "confidence": rule.confidence})
        if active:
            updates.update({"status": "active", "verified_by": "memory_consolidator_generalization"})
        events.append(_event("generalization_recovered" if active else "generalization_failed",
                             proposal.memory_id + str(metadata["attempts"]), proposal.memory_id,
                             attempt=metadata["attempts"]))
        return proposal.model_copy(update=updates)

    # ------------------------------------------------------------------ usage

    def _rollup_usage(self, ltm_by_id: Dict[str, MemoryRecord]) -> Tuple[Dict[str, MemoryRecord], List[ConsolidationEvent]]:
        """Fold usage events into per-record counters, once per (case, memory) pair.

        An outcome that arrives after the use was first counted (e.g. the
        clinician approves the plan later) updates the pair's outcome."""
        precedence = {"contested": 3, "unsuccessful": 2, "successful": 1, "unknown": 0}
        grouped: Dict[Tuple[str, str], List[Any]] = {}
        for event in self.store.load_usage_events():
            grouped.setdefault((event.case_id, event.memory_id), []).append(event)
        updates: Dict[str, MemoryRecord] = {}
        events: List[ConsolidationEvent] = []
        for (case_id, memory_id), rows in grouped.items():
            target = updates.get(memory_id) or ltm_by_id.get(memory_id)
            if target is None:
                continue
            outcome = max((row.outcome for row in rows), key=lambda value: precedence[value])
            pair_id = f"use_{stable_hash(case_id + memory_id)}"
            seen = dict(target.metadata.get("usage_outcomes", {}))
            previous = seen.get(pair_id)
            if previous == outcome:
                continue
            counters = {
                "usage_count": target.usage_count + (1 if previous is None else 0),
                "successful_usage_count": target.successful_usage_count,
                "contested_usage_count": target.contested_usage_count,
                "unsuccessful_usage_count": target.unsuccessful_usage_count,
            }
            if previous not in (None, "unknown"):
                counters[f"{previous}_usage_count"] -= 1
            if outcome != "unknown":
                counters[f"{outcome}_usage_count"] += 1
            seen[pair_id] = outcome
            updates[memory_id] = target.model_copy(update={
                **counters,
                "version": target.version + 1,
                "last_used_at": max(row.created_at or "" for row in rows) or target.last_used_at,
                "updated_at": utc_now_iso(),
                "metadata": {**target.metadata, "usage_outcomes": seen},
            })
            events.append(_event("usage_rollup", pair_id + outcome, memory_id, case_id=case_id, outcome=outcome))
        return updates, events

    # -------------------------------------------------------------- lifecycle

    def _lifecycle(self, record: MemoryRecord, result: ConsolidationResult,
                   events: List[ConsolidationEvent]) -> MemoryRecord:
        if record.status in ("deprecated", "merged", "promoted", "expired"):
            return record
        ratio = record.conflict_count / max(1, record.support_count + record.conflict_count)
        if record.confidence < self.config.deprecate_confidence_below and record.conflict_count > 0:
            # Deprecation needs contradiction pressure, never age alone.
            result.deprecated.append(record.memory_id)
            events.append(_event("deprecated", record.memory_id + str(record.version), record.memory_id,
                                 confidence=round(record.confidence, 4), conflict_ratio=round(ratio, 4)))
            return record.model_copy(update={"status": "deprecated", "updated_at": utc_now_iso()})
        if record.status == "active" and ratio > self.config.under_review_conflict_ratio:
            if record.memory_id not in result.under_review:
                result.under_review.append(record.memory_id)
            events.append(_event("under_review", "ratio" + record.memory_id + str(record.version), record.memory_id,
                                 conflict_ratio=round(ratio, 4)))
            return record.model_copy(update={"status": "under_review", "updated_at": utc_now_iso()})
        if (record.status == "under_review" and not record.metadata.get("proposal_only")
                and not record.metadata.get("held_by_reviewer")
                and ratio <= self.config.max_conflict_ratio
                and record.confidence >= self.config.deprecate_confidence_below):
            result.reactivated.append(record.memory_id)
            events.append(_event("reactivated", record.memory_id + str(record.version), record.memory_id,
                                 conflict_ratio=round(ratio, 4)))
            return record.model_copy(update={"status": "active", "updated_at": utc_now_iso()})
        return record
