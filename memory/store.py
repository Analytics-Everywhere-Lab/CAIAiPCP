"""JSONL memory store, ported from SEMV's memory_store.py: short-term and
long-term files, consolidation and usage event logs, an archive (nothing is
silently deleted), snapshots, atomic rewrites and a re-entrant file lock."""
import json
import os
import shutil
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional

from memory.config import MemoryConfig
from memory.schema import ConsolidationEvent, MemoryRecord, MemoryUsageEvent, ShortTermMemoryRecord

try:
    import fcntl
except ImportError:  # pragma: no cover - non-posix fallback
    fcntl = None

LONG_TERM_FILES = {
    "episodic": "episodic_memory.jsonl",
    "failure": "failure_memory.jsonl",
    "semantic_rule": "semantic_rules.jsonl",
}
SHORT_TERM_FILE = "short_term_memory.jsonl"
EVENT_LOG_FILE = "consolidation_events.jsonl"
USAGE_LOG_FILE = "memory_usage_events.jsonl"


def _read_jsonl(path: Path) -> List[dict]:
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue  # a torn line never takes the whole store down
    return rows


def _dump(row) -> str:
    data = row.model_dump(mode="json") if hasattr(row, "model_dump") else row
    return json.dumps(data, ensure_ascii=False)


class MemoryStore:
    def __init__(self, config: Optional[MemoryConfig] = None) -> None:
        self.config = config or MemoryConfig()
        self.memory_dir = Path(self.config.memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        for filename in list(LONG_TERM_FILES.values()) + [SHORT_TERM_FILE]:
            (self.memory_dir / filename).touch(exist_ok=True)
        self._lock_state = threading.local()

    # ------------------------------------------------------------------ paths

    @property
    def short_term_path(self) -> Path:
        return self.memory_dir / SHORT_TERM_FILE

    @property
    def event_log_path(self) -> Path:
        return self.memory_dir / EVENT_LOG_FILE

    @property
    def usage_log_path(self) -> Path:
        return self.memory_dir / USAGE_LOG_FILE

    @property
    def archive_dir(self) -> Path:
        return self.memory_dir / "archive"

    @property
    def snapshot_dir(self) -> Path:
        return self.memory_dir / "snapshots"

    def long_term_path(self, memory_type: str) -> Path:
        return self.memory_dir / LONG_TERM_FILES[memory_type]

    # ------------------------------------------------------------------- lock

    @contextmanager
    def transaction(self):
        """Re-entrant, process-safe lock around a read/modify/write cycle."""
        depth = getattr(self._lock_state, "depth", 0)
        if depth:
            self._lock_state.depth = depth + 1
            try:
                yield self
            finally:
                self._lock_state.depth -= 1
            return
        handle = open(self.memory_dir / ".memory.lock", "a+", encoding="utf-8")
        self._lock_state.depth = 1
        try:
            if fcntl is not None:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            yield self
        finally:
            if fcntl is not None:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            handle.close()
            self._lock_state.depth = 0

    # ------------------------------------------------------------- atomic I/O

    def _atomic_write(self, path: Path, rows: Iterable) -> None:
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        with tmp_path.open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(_dump(row) + "\n")
        os.replace(tmp_path, path)

    def _append(self, path: Path, row) -> None:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(_dump(row) + "\n")

    def _backup(self, path: Path) -> None:
        """Timestamped backup before rewriting a non-empty file, keeping the newest few."""
        if not path.exists() or path.stat().st_size == 0:
            return
        backup_dir = self.archive_dir / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
        shutil.copy2(path, backup_dir / f"{stamp}_{path.name}")
        backups = sorted(backup_dir.glob(f"*_{path.name}"))
        for old in backups[: max(0, len(backups) - self.config.backups_to_keep)]:
            old.unlink(missing_ok=True)

    # ---------------------------------------------------------------- loading

    def load_long_term(self, memory_types: Optional[List[str]] = None,
                       statuses: Optional[List[str]] = None) -> List[MemoryRecord]:
        records = []
        for memory_type, filename in LONG_TERM_FILES.items():
            if memory_types is not None and memory_type not in memory_types:
                continue
            for row in _read_jsonl(self.memory_dir / filename):
                row.setdefault("memory_type", memory_type)
                record = MemoryRecord.model_validate(row)
                if statuses is None or record.status in statuses:
                    records.append(record)
        return records

    def load_short_term(self, statuses: Optional[List[str]] = None) -> List[ShortTermMemoryRecord]:
        records = [ShortTermMemoryRecord.model_validate(row) for row in _read_jsonl(self.short_term_path)]
        return [record for record in records if statuses is None or record.status in statuses]

    def load_usage_events(self) -> List[MemoryUsageEvent]:
        return [MemoryUsageEvent.model_validate(row) for row in _read_jsonl(self.usage_log_path)]

    def load_consolidation_events(self) -> List[ConsolidationEvent]:
        return [ConsolidationEvent.model_validate(row) for row in _read_jsonl(self.event_log_path)]

    # ---------------------------------------------------------------- writing

    def stage(self, record: ShortTermMemoryRecord) -> ShortTermMemoryRecord:
        """Upsert one short-term record by stm_id.

        A record that already reached a terminal state (promoted or merged) is
        preserved: re-reflecting on a case must not resurrect a consolidated
        observation."""
        with self.transaction():
            by_id = {row.stm_id: row for row in self.load_short_term()}
            previous = by_id.get(record.stm_id)
            if previous is not None and previous.status in ("promoted", "merged"):
                return previous
            record = record.model_copy(update={"updated_at": datetime.now(timezone.utc).isoformat()})
            by_id[record.stm_id] = record
            rows = list(by_id.values())
            overflow = len(rows) - self.config.short_term_max_records
            if overflow > 0:
                rows.sort(key=lambda row: row.staged_at or "")
                dropped, rows = rows[:overflow], rows[overflow:]
                self.archive(dropped, "short_term_overflow")
            self._atomic_write(self.short_term_path, rows)
        return record

    def upsert_short_term(self, records: List[ShortTermMemoryRecord]) -> None:
        if not records:
            return
        with self.transaction():
            by_id = {row.stm_id: row for row in self.load_short_term()}
            for record in records:
                by_id[record.stm_id] = record
            self._backup(self.short_term_path)
            self._atomic_write(self.short_term_path, by_id.values())

    def replace_short_term(self, records: List[ShortTermMemoryRecord]) -> None:
        with self.transaction():
            self._backup(self.short_term_path)
            self._atomic_write(self.short_term_path, records)

    def upsert_long_term(self, records: List[MemoryRecord]) -> None:
        """Update or insert long-term records, preserving ids and file order."""
        if not records:
            return
        with self.transaction():
            by_type = {}
            for record in records:
                by_type.setdefault(record.memory_type, []).append(record)
            for memory_type, type_records in by_type.items():
                path = self.long_term_path(memory_type)
                rows = {}
                for row in _read_jsonl(path):
                    rows[row.get("memory_id", "")] = row
                for record in type_records:
                    rows[record.memory_id] = record.model_dump(mode="json")
                self._backup(path)
                self._atomic_write(path, rows.values())

    def append_event(self, event: ConsolidationEvent) -> None:
        with self.transaction():
            known = {row.get("event_id") for row in _read_jsonl(self.event_log_path)}
            if event.event_id not in known:
                self._append(self.event_log_path, event)

    def append_usage_event(self, event: MemoryUsageEvent) -> None:
        with self.transaction():
            known = {row.get("event_id") for row in _read_jsonl(self.usage_log_path)}
            if event.event_id not in known:
                self._append(self.usage_log_path, event)

    def archive(self, records: list, name: str) -> None:
        if not records:
            return
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        for record in records:
            self._append(self.archive_dir / f"{name}.jsonl", record)

    # ---------------------------------------------------------------- snapshot

    def snapshot(self, label: Optional[str] = None) -> Path:
        """Freeze the full memory state, e.g. before a paired memory-on/off evaluation."""
        with self.transaction():
            stamp = label or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
            target = self.snapshot_dir / stamp
            target.mkdir(parents=True, exist_ok=False)
            files = list(LONG_TERM_FILES.values()) + [SHORT_TERM_FILE, EVENT_LOG_FILE]
            for filename in files:
                source = self.memory_dir / filename
                if source.exists():
                    shutil.copy2(source, target / filename)
            manifest = {"created_at": datetime.now(timezone.utc).isoformat(), "files": files, "counts": self.counts()}
            (target / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            return target

    def counts(self) -> dict:
        counts = {"short_term": 0, "long_term": 0}
        for record in self.load_long_term():
            counts["long_term"] += 1
            counts[f"long_term_{record.memory_type}"] = counts.get(f"long_term_{record.memory_type}", 0) + 1
            counts[f"long_term_status_{record.status}"] = counts.get(f"long_term_status_{record.status}", 0) + 1
        for record in self.load_short_term():
            counts["short_term"] += 1
            counts[f"short_term_status_{record.status}"] = counts.get(f"short_term_status_{record.status}", 0) + 1
        return counts
