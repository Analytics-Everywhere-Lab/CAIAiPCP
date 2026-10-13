"""One memory facade shared by the graph nodes, the API and the CLI."""
import threading
from concurrent.futures import ThreadPoolExecutor, wait
from typing import Any, Callable, Dict, List, Optional

from memory.config import MemoryConfig
from memory.consolidator import MemoryConsolidator
from memory.reflection import LessonGenerator, memory_conflict_candidates
from memory.retriever import MemoryRetriever, guidance_lines, record_summary
from memory.schema import ConsolidationEvent, ConsolidationResult, MemoryRecord, MemoryUsageEvent, utc_now_iso
from memory.similarity import HybridSimilarity, stable_hash
from memory.store import MemoryStore
from memory.verifier import MemoryVerifier

HUMAN_APPROVED_CONFIDENCE = 0.85


class MemoryService:
    def __init__(self, config: Optional[MemoryConfig] = None, llm_json: Optional[Callable[..., Any]] = None) -> None:
        if llm_json is None:
            from llm_caller import call_llm_json
            llm_json = call_llm_json
        self.config = config or MemoryConfig()
        self.llm_json = llm_json
        self.store = MemoryStore(self.config)
        self.similarity = HybridSimilarity(
            duplicate_similarity=self.config.duplicate_similarity,
            contradiction_similarity=self.config.contradiction_similarity,
            shortlist_k=self.config.lexical_shortlist_k,
            llm_json=llm_json if self.config.use_llm_relation_check else None,
        )
        self.retriever = MemoryRetriever(self.store, self.config, self.similarity)
        self.verifier = MemoryVerifier(self.store, self.config, self.similarity, llm_json)
        self.consolidator = MemoryConsolidator(self.store, self.config, self.similarity, llm_json)
        self.lessons = LessonGenerator(llm_json)
        # Learning runs off the request path on one worker, so the clinician can keep
        # contesting while it runs and jobs for the same case complete in order.
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="memory")
        self._futures: List[Any] = []
        self._status_lock = threading.Lock()
        self._reflections: Dict[str, Dict[str, Any]] = {}
        self._submitted = 0

    # -------------------------------------------------------------- retrieval

    def retrieve(self, stage: str, query_text: str, profile_tags: Optional[List[str]] = None,
                 top_k: Optional[int] = None, memory_types: Optional[List[str]] = None,
                 exclude_case_id: Optional[str] = None) -> List[MemoryRecord]:
        return self.retriever.retrieve(stage, query_text, profile_tags, top_k, memory_types, exclude_case_id)

    @staticmethod
    def guidance(records: List[MemoryRecord]) -> List[str]:
        return guidance_lines(records)

    def log_usage(self, case_id: str, memory_ids: List[str], stage: str, outcome: str = "unknown",
                  argument_id: Optional[str] = None) -> None:
        for memory_id in dict.fromkeys(memory_ids):
            self.store.append_usage_event(MemoryUsageEvent(
                event_id=f"use_{stable_hash(case_id + memory_id + stage + outcome + (argument_id or ''))}",
                case_id=case_id, memory_id=memory_id, stage=stage, outcome=outcome, argument_id=argument_id,
            ))

    def record_outcomes(self, case_id: str, outcomes: Dict[str, str]) -> None:
        for memory_id, outcome in outcomes.items():
            self.log_usage(case_id, [memory_id], "outcome", outcome)

    # ------------------------------------------------------------- reflection

    def reflect(self, case: Dict[str, Any]) -> Dict[str, Any]:
        """Learn from one reviewed case: generate, verify and stage lesson candidates.

        A newer reflection on the same case supersedes its earlier staged
        candidates, because it covers the clinician's cumulative operations."""
        ops = case.get("ops") or []
        valid_op_ids = {op["op_id"] for op in ops}
        conflicts = memory_conflict_candidates(case)
        verified = self.verifier.verify_batch(self.lessons.generate(case), valid_op_ids)
        staged = self.consolidator.stage(verified + conflicts)
        self._supersede(case["case_id"], {row.stm_id for row in staged})

        contested = {op["memory_id"]: "contested" for op in ops
                     if op.get("op") in ("reject", "edit") and op.get("source") == "memory" and op.get("memory_id")}
        self.record_outcomes(case["case_id"], contested)

        summary = {
            "candidates": len(verified) + len(conflicts),
            "verified": sum(1 for c in verified if c.verification_status == "verified") + len(conflicts),
            "under_review": sum(1 for c in verified if c.verification_status == "under_review"),
            "rejected": sum(1 for c in verified if c.verification_status == "rejected"),
            "conflicts": len(conflicts),
            "staged": [{"stm_id": row.stm_id, "memory_type": row.memory_type, "text": row.text,
                        "status": row.status} for row in staged],
            "rejections": [{"memory_type": c.memory_type, "reason": c.rejected_reason}
                           for c in verified if c.verification_status == "rejected"],
        }
        result = self.maybe_consolidate()
        if result is not None:
            summary["consolidation"] = consolidation_summary(result)
        return summary

    def reflect_in_background(self, case: Dict[str, Any]) -> Dict[str, Any]:
        """Queue reflect(case); reflection_status() reports when it is done."""
        case_id = case["case_id"]
        with self._status_lock:
            self._submitted += 1
            seq = self._submitted
            status = {"status": "running", "seq": seq, "ops": len(case.get("ops") or [])}
            self._reflections[case_id] = status

        def job():
            try:
                result = {"status": "done", **self.reflect(case)}
            except Exception as exc:  # learning must never break the care plan workflow
                result = {"status": "failed", "error": str(exc)}
            with self._status_lock:
                if self._reflections.get(case_id, {}).get("seq") == seq:
                    self._reflections[case_id] = {**result, "seq": seq}

        self._futures.append(self._executor.submit(job))
        return dict(status)

    def consolidate_in_background(self) -> None:
        self._futures.append(self._executor.submit(self.consolidate))

    def reflection_status(self, case_id: str) -> Optional[Dict[str, Any]]:
        with self._status_lock:
            status = self._reflections.get(case_id)
            return dict(status) if status else None

    def close(self) -> None:
        self._executor.shutdown(wait=True)

    def wait_idle(self, timeout: float = 60.0) -> None:
        """Block until queued background work has finished (tests, CLI, shutdown)."""
        wait(list(self._futures), timeout=timeout)
        self._futures = [future for future in self._futures if not future.done()]

    def _supersede(self, case_id: str, keep: set) -> None:
        with self.store.transaction():
            superseded = [
                row.model_copy(update={"status": "expired", "updated_at": utc_now_iso(),
                                       "metadata": {**row.metadata, "superseded": True}})
                for row in self.store.load_short_term(statuses=["staged", "under_review"])
                if row.source_case_id == case_id and row.stm_id not in keep
            ]
            if superseded:
                self.store.archive(superseded, "short_term_superseded")
                self.store.upsert_short_term(superseded)

    # ---------------------------------------------------------- consolidation

    def maybe_consolidate(self) -> Optional[ConsolidationResult]:
        """Consolidate once enough reviewed cases are waiting in short-term memory."""
        waiting = {row.source_case_id for row in self.store.load_short_term(statuses=["staged"])
                   if row.verification_status == "verified"}
        if len(waiting) >= max(1, self.config.consolidate_every_n_cases):
            return self.consolidate()
        return None

    def consolidate(self, dry_run: bool = False, retry_under_review: bool = False) -> ConsolidationResult:
        return self.consolidator.consolidate(dry_run=dry_run, retry_under_review=retry_under_review)

    # ------------------------------------------------------------- governance

    def review(self, memory_id: str, decision: str, note: Optional[str] = None) -> Dict[str, Any]:
        """Human governance of memory: approve, hold or reject a record or staged observation."""
        if decision not in ("approve", "reject", "hold"):
            raise ValueError("decision must be approve, reject or hold")
        with self.store.transaction():
            for row in self.store.load_short_term():
                if row.stm_id != memory_id:
                    continue
                if decision == "approve":
                    # A reviewer's explicit approval is strong supervision: it lifts the
                    # observation to the confidence a verified human-feedback lesson carries.
                    updated = row.model_copy(update={"verification_status": "verified", "status": "staged",
                                                     "verified_by": "human_reviewer", "rejected_reason": None,
                                                     "confidence": max(row.confidence, HUMAN_APPROVED_CONFIDENCE)})
                elif decision == "reject":
                    updated = row.model_copy(update={"verification_status": "rejected", "status": "expired",
                                                     "rejected_reason": note or "rejected_by_reviewer"})
                else:
                    updated = row.model_copy(update={"status": "under_review"})
                self.store.upsert_short_term([updated.model_copy(update={"updated_at": utc_now_iso()})])
                self._review_event(memory_id, decision, note)
                return {"memory_id": memory_id, "level": "short_term", "status": updated.status}
            for record in self.store.load_long_term():
                if record.memory_id != memory_id:
                    continue
                metadata = {**record.metadata, "reviewer_note": note, "held_by_reviewer": decision == "hold"}
                if decision == "approve":
                    metadata.update({"proposal_only": False, "review_reason": None})
                    updates = {"status": "active", "verified_by": "human_reviewer"}
                elif decision == "reject":
                    updates = {"status": "deprecated"}
                else:
                    updates = {"status": "under_review"}
                updated = record.model_copy(update={**updates, "metadata": metadata, "version": record.version + 1,
                                                    "updated_at": utc_now_iso()})
                if updated.status == "deprecated":
                    self.store.archive([updated], "deprecated_long_term")
                self.store.upsert_long_term([updated])
                self._review_event(memory_id, decision, note)
                return {"memory_id": memory_id, "level": "long_term", "status": updated.status}
        raise KeyError(memory_id)

    def _review_event(self, memory_id: str, decision: str, note: Optional[str]) -> None:
        self.store.append_event(ConsolidationEvent(
            event_id=f"evt_{stable_hash('review' + memory_id + decision + utc_now_iso())}",
            event_type="human_review", memory_id=memory_id, details={"decision": decision, "note": note},
        ))

    # ---------------------------------------------------------------- overview

    def overview(self) -> Dict[str, Any]:
        long_term = sorted(self.store.load_long_term(), key=lambda r: (r.status != "active", -r.confidence))
        short_term = self.store.load_short_term(statuses=["staged", "under_review"])
        return {
            "counts": self.store.counts(),
            "consolidate_every_n_cases": self.config.consolidate_every_n_cases,
            "long_term": [
                {**record_summary(record),
                 "status": record.status,
                 "failure_type": record.failure_type,
                 "trigger_pattern": record.trigger_pattern,
                 "recommended_action": record.recommended_action,
                 "conflicts": record.conflict_count,
                 "usage": {"used": record.usage_count, "successful": record.successful_usage_count,
                           "contested": record.contested_usage_count},
                 "review_reason": record.metadata.get("review_reason"),
                 "updated_at": record.updated_at}
                for record in long_term
            ],
            "short_term": [
                {"memory_id": row.stm_id, "memory_type": row.memory_type, "stage": row.stage, "text": row.text,
                 "confidence": round(row.confidence, 3), "status": row.status,
                 "verification_status": row.verification_status, "reason": row.rejected_reason,
                 "staged_at": row.staged_at}
                for row in short_term
            ],
        }

    def snapshot(self, label: Optional[str] = None) -> str:
        return str(self.store.snapshot(label))


def consolidation_summary(result: ConsolidationResult) -> Dict[str, Any]:
    return {
        "promoted": len(result.promoted),
        "merged": len(result.merged),
        "conflicted": len(result.conflicted),
        "generalized": len(result.generalized),
        "deprecated": len(result.deprecated),
        "under_review": len(result.under_review),
        "reactivated": len(result.reactivated),
        "counts_after": result.counts_after,
        "dry_run": result.dry_run,
    }


_SERVICE: Optional[MemoryService] = None
_SERVICE_LOCK = threading.Lock()


def get_memory_service() -> Optional[MemoryService]:
    """The process-wide memory service, or None when memory is disabled."""
    from env_config import MEMORY_ENABLED

    global _SERVICE
    if not MEMORY_ENABLED:
        return None
    with _SERVICE_LOCK:
        if _SERVICE is None:
            _SERVICE = MemoryService()
        return _SERVICE


def set_memory_service(service: Optional[MemoryService]) -> None:
    """Override the process-wide service (tests, evaluation with a frozen snapshot)."""
    global _SERVICE
    with _SERVICE_LOCK:
        _SERVICE = service
