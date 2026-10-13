"""Inspect or run memory consolidation outside the web app.

    python scripts/consolidate_memory.py --dry-run
    python scripts/consolidate_memory.py --apply --snapshot
    python scripts/consolidate_memory.py --apply --retry-under-review
    python scripts/consolidate_memory.py --review mem_1234abcd --decision approve
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from memory.config import MemoryConfig  # noqa: E402
from memory.service import MemoryService, consolidation_summary  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--memory-dir", default=None, help="memory directory (default: MEMORY_DIR)")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="report what consolidation would change")
    mode.add_argument("--apply", action="store_true", help="consolidate and write the result")
    parser.add_argument("--retry-under-review", action="store_true",
                        help="retry rule proposals held because an LLM step failed")
    parser.add_argument("--snapshot", nargs="?", const="", default=None,
                        help="freeze the memory state after consolidating (optional label)")
    parser.add_argument("--review", metavar="MEMORY_ID", help="record a human review decision")
    parser.add_argument("--decision", choices=["approve", "reject", "hold"])
    parser.add_argument("--note", default=None)
    parser.add_argument("--show", action="store_true", help="print the memory overview")
    args = parser.parse_args()

    config = MemoryConfig(memory_dir=args.memory_dir) if args.memory_dir else MemoryConfig()
    service = MemoryService(config)

    if args.review:
        if not args.decision:
            parser.error("--review requires --decision")
        print(json.dumps(service.review(args.review, args.decision, args.note), indent=2))
    if args.dry_run or args.apply:
        result = service.consolidate(dry_run=args.dry_run, retry_under_review=args.retry_under_review)
        print(json.dumps(consolidation_summary(result), indent=2))
        for event in result.events:
            print(f"  {event.event_type:<26} {event.memory_id or ''} {json.dumps(event.details)}")
    if args.snapshot is not None:
        print("snapshot:", service.snapshot(args.snapshot or None))
    if args.show or not (args.review or args.dry_run or args.apply or args.snapshot is not None):
        print(json.dumps(service.overview(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
