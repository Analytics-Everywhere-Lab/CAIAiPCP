"""Stable argument identity, human contestation bookkeeping and serialization.

Every argument carries an id ("A3") and every option an index-based id ("O1").
Human operations on the argument graph (table edits and operations derived
from free-text plan feedback) are appended to ``state["human_ops_log"]`` so the
chatbot, the revision planner and the memory module all see the same record.
"""
import re
from typing import Any, Dict, List, Optional

from state import Argument

HUMAN_SOURCES = ("human", "feedback")


def option_id(index: int) -> str:
    return f"O{index + 1}"


def option_index(options: List[str], option_text: Optional[str]) -> Optional[int]:
    if option_text is None:
        return None
    for index, option in enumerate(options):
        if option == option_text:
            return index
    return None


def resolve_option(options: List[str], ref: Any) -> Optional[str]:
    """Map an option reference ("O2", 2, or the option text) to the option text."""
    if ref is None:
        return None
    if isinstance(ref, int):
        return options[ref - 1] if 1 <= ref <= len(options) else None
    text = str(ref).strip()
    match = re.fullmatch(r"[Oo](?:ption)?\s*(\d+)", text)
    if match:
        index = int(match.group(1)) - 1
        return options[index] if 0 <= index < len(options) else None
    return text if text in options else None


def _id_number(arg_id: Optional[str]) -> int:
    match = re.fullmatch(r"A(\d+)", arg_id or "")
    return int(match.group(1)) if match else 0


def ensure_argument_ids(state) -> None:
    """Assign stable ids to arguments that lack one, continuing the sequence."""
    arguments = state.get("arguments") or []
    seq = max([state.get("next_arg_seq") or 0] + [_id_number(arg.arg_id) for arg in arguments])
    for arg in arguments:
        if not arg.arg_id:
            seq += 1
            arg.arg_id = f"A{seq}"
    state["next_arg_seq"] = seq


def new_arg_id(state) -> str:
    ensure_argument_ids(state)
    state["next_arg_seq"] = (state.get("next_arg_seq") or 0) + 1
    return f"A{state['next_arg_seq']}"


def find_argument(arguments: List[Argument], arg_id: Optional[str]) -> Optional[Argument]:
    if not arg_id:
        return None
    return next((arg for arg in arguments if arg.arg_id == arg_id), None)


def active_arguments(arguments: List[Argument]) -> List[Argument]:
    """Arguments that take part in the QBAF (rejected ones are kept for audit only)."""
    return [arg for arg in arguments if arg.human_status != "rejected"]


def is_human_authored(arg: Argument) -> bool:
    return arg.source in HUMAN_SOURCES


def record_human_op(state, op: str, arg: Optional[Argument] = None, **details) -> Dict[str, Any]:
    """Append one human operation to the log and return it."""
    log = state.get("human_ops_log")
    if log is None:
        log = []
        state["human_ops_log"] = log
    entry: Dict[str, Any] = {"op_id": f"H{len(log) + 1}", "op": op}
    if arg is not None:
        entry.update({
            "arg_id": arg.arg_id,
            "stance": arg.argument_type,
            "option": arg.parent_option,
            "role": arg.agent_role,
            "source": arg.source,
            "content": arg.content,
            "memory_id": arg.memory_id,
        })
    entry.update({key: value for key, value in details.items() if value is not None})
    log.append(entry)
    return entry


def net_human_ops(state) -> List[Dict[str, Any]]:
    """Net effect of all human operations, one entry per changed argument.

    An argument the clinician added and later removed cancels out; an edit
    followed by a removal is a removal. Option additions and writer directives
    are kept as logged. Each entry keeps the op_id of the latest operation that
    produced it, which is what memory candidates cite as grounding."""
    log = state.get("human_ops_log") or []
    latest_by_arg: Dict[str, Dict[str, Any]] = {}
    for entry in log:
        if entry.get("arg_id"):
            latest_by_arg[entry["arg_id"]] = entry
    ops: List[Dict[str, Any]] = []
    for arg in state.get("arguments") or []:
        if arg.human_status == "rejected":
            if is_human_authored(arg):
                continue
            op = "reject"
        elif arg.human_status == "edited":
            op = "edit"
        elif arg.human_status == "added" or is_human_authored(arg):
            op = "add"
        else:
            continue
        latest = latest_by_arg.get(arg.arg_id or "", {})
        ops.append({
            "op_id": latest.get("op_id", f"H_{arg.arg_id}"),
            "op": op,
            "arg_id": arg.arg_id,
            "stance": arg.argument_type,
            "option": arg.parent_option,
            "role": arg.agent_role,
            "source": arg.source,
            "content": arg.content,
            "original_content": arg.original_content,
            "reason": arg.rejection_reason,
            "feedback_id": arg.feedback_id,
            "memory_id": arg.memory_id,
            "target_arg_id": arg.target_arg_id,
        })
    ops.extend(dict(entry) for entry in log if entry.get("op") in ("add_option", "directive"))
    return ops


def argument_to_dict(arg: Argument, index: int, options: List[str]) -> Dict[str, Any]:
    """Serialize an argument for the frontend."""
    idx = option_index(options, arg.parent_option)
    return {
        "id": index,  # positional index, kept for older clients
        "arg_id": arg.arg_id,
        "content": arg.content,
        "type": arg.argument_type,
        "option": arg.parent_option,
        "option_id": option_id(idx) if idx is not None else None,
        "role": arg.agent_role or "General",
        "source": arg.source,
        "status": arg.human_status,
        "original_content": arg.original_content,
        "rejection_reason": arg.rejection_reason,
        "target_arg_id": arg.target_arg_id,
        "feedback_id": arg.feedback_id,
        "memory_id": arg.memory_id,
        "score": round(arg.validity_score, 2) if arg.validity_score is not None else None,
        "strength": round(arg.strength, 3) if arg.strength is not None else None,
        "validation_note": arg.validation_note,
        "flags": list(arg.flags or []),
        "relevance": arg.relevance,
        "same_as": arg.same_as,
        "rebuts": list(arg.rebuts or []),
    }


def arguments_payload(state) -> List[Dict[str, Any]]:
    options = state.get("handling_options") or []
    return [argument_to_dict(arg, i, options) for i, arg in enumerate(state.get("arguments") or [])]
