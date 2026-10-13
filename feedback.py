"""Clinician feedback on the care plan, formulated as QBAF operations.

Free-text feedback (on a section, on a quoted passage, or on the whole plan)
is translated into operations on the argument graph -- add, reject or edit an
argument, or add a care option -- so it changes the plan through the same
verified, weighed reasoning as the care team's own arguments. Feedback that is
purely about presentation becomes a writer directive instead.

After the graph has been re-verified and re-evaluated, plan_revision_strategy()
reasons about how to update the plan: rewrite only the affected sections,
regenerate the whole plan, or rewrite its presentation without changing content.
"""
import hashlib
import re
from typing import Any, Dict, List, Optional

from arguments import (
    active_arguments,
    find_argument,
    new_arg_id,
    option_id,
    option_index,
    record_human_op,
    resolve_option,
)
from care_plan_document import SECTION_TITLES, STRATEGY_LABELS, now_iso
from llm_caller import call_llm, call_llm_json
from qbaf import TIER_LABELS
from state import Argument
from utils import clip_text

MAX_OPS_PER_ITEM = 4
GRAPH_OPS = ("add_argument", "reject_argument", "edit_argument", "add_option")
STRATEGIES = ("targeted_revision", "full_regeneration", "presentation_rewrite")

_STANCES = {
    "support": "support", "supports": "support", "pro": "support", "for": "support",
    "attack": "attack", "attacks": "attack", "challenge": "attack", "concern": "attack",
    "against": "attack", "con": "attack", "oppose": "attack",
}
_OPS = {
    "add_argument": "add_argument", "add": "add_argument",
    "reject_argument": "reject_argument", "reject": "reject_argument", "remove_argument": "reject_argument",
    "remove": "reject_argument",
    "edit_argument": "edit_argument", "edit": "edit_argument", "modify_argument": "edit_argument",
    "add_option": "add_option", "new_option": "add_option",
    "directive": "directive", "presentation": "directive", "writer_directive": "directive",
}


# --------------------------------------------------------------------- items

def normalize_feedback_items(raw_items, existing_count: int, known_sections=None) -> List[Dict[str, Any]]:
    """Validate submitted feedback and give each item a stable id (F1, F2, ...)."""
    known_sections = set(known_sections or SECTION_TITLES)
    items = []
    for raw in raw_items or []:
        if isinstance(raw, str):
            raw = {"text": raw}
        text = " ".join(str(raw.get("text") or "").split())
        if not text:
            continue
        section_id = raw.get("section_id")
        quote = " ".join(str(raw.get("quote") or "").split())
        items.append({
            "id": f"F{existing_count + len(items) + 1}",
            "text": text[:2000],
            "section_id": section_id if section_id in known_sections else None,
            "quote": quote[:400] or None,
            "created_at": now_iso(),
        })
    return items


def describe_item(item: Dict[str, Any], section_titles: Optional[Dict[str, str]] = None) -> str:
    titles = section_titles or SECTION_TITLES
    anchor = []
    if item.get("section_id"):
        anchor.append(f'on section "{titles.get(item["section_id"], item["section_id"])}"')
    if item.get("quote"):
        anchor.append(f'quoting "{clip_text(item["quote"], 200)}"')
    prefix = f"{item['id']} [{', '.join(anchor)}]" if anchor else item["id"]
    return f"{prefix}: {item['text']}"


def feedback_context(history: List[Dict[str, Any]], max_items: int = 12) -> str:
    """Compact text of all applied clinician feedback, for re-verification prompts."""
    return "\n".join(f"- {describe_item({**item, 'text': clip_text(item['text'], 300)})}"
                     for item in (history or [])[-max_items:])


def feedback_signature(history: List[Dict[str, Any]]) -> str:
    basis = "|".join(f"{item['id']}:{item['text']}" for item in history or [])
    return hashlib.sha1(basis.encode()).hexdigest()[:12] if basis else "none"


# ------------------------------------------------------------ interpretation

def _interpretation_prompt(state, items, section_titles) -> str:
    options = state.get("handling_options") or []
    option_lines = "\n".join(f"{option_id(i)}: {option}" for i, option in enumerate(options))
    arg_lines = []
    for arg in active_arguments(state.get("arguments") or []):
        idx = option_index(options, arg.parent_option)
        strength = f"{arg.strength:.2f}" if arg.strength is not None else "-"
        arg_lines.append(
            f"{arg.arg_id} | {option_id(idx) if idx is not None else '?'} | {arg.argument_type} | "
            f"{strength} | {clip_text(arg.content, 220)}"
        )
    section_lines = ", ".join(f"{sid} ({title})" for sid, title in section_titles.items())
    feedback_lines = "\n".join(describe_item(item, section_titles) for item in items)
    return f"""You are the contestation interpreter of a care-planning system that reasons with a quantitative bipolar argumentation framework (QBAF). A clinician reviewed the care plan and left feedback. Translate every feedback item into the smallest set of operations on the argument graph, so the plan can be recomputed from verified, weighed arguments.

Operations:
- add_argument: a new argument. Fields: option_id (e.g. "O1"), stance ("support" or "attack"), content (one self-contained sentence in clinical language). Optional target_arg_id: set it only when the feedback rebuts or reinforces one specific existing argument; the stance is then relative to that argument.
- reject_argument: the feedback says an existing argument is wrong, irrelevant or unsafe. Fields: arg_id, reason.
- edit_argument: the feedback corrects an existing argument. Fields: arg_id, content (the corrected sentence).
- add_option: the feedback asks for a care option that is not in the plan yet. Fields: content (the option, one sentence).
- directive: the feedback is only about presentation (length, tone, format, wording) and does not change clinical reasoning. Fields: content (the instruction for the writer), section_ids (optional list).

Use graph operations whenever a feedback item carries clinical content; use directive only for presentation. Every operation needs "feedback_id" and a short "rationale" explaining why this operation reflects the feedback.

Care options:
{option_lines}

Arguments (id | option | stance | strength | text):
{chr(10).join(arg_lines) or "(none)"}

Plan sections: {section_lines}

Feedback:
{feedback_lines}

Return JSON only: {{"operations": [{{"feedback_id": "F1", "op": "...", "rationale": "...", ...}}]}}"""


def interpret_feedback(state, items: List[Dict[str, Any]], section_titles=None) -> List[Dict[str, Any]]:
    """Ask the LLM to map feedback to graph operations; validate them strictly.

    A feedback item with no valid operation falls back to a writer directive,
    so no feedback is ever silently dropped."""
    if not items:
        return []
    section_titles = section_titles or SECTION_TITLES
    data = call_llm_json(_interpretation_prompt(state, items, section_titles), temperature=0.2, max_tokens=4096)
    if isinstance(data, dict):
        raw_ops = data.get("operations") or data.get("ops") or []
    elif isinstance(data, list):
        raw_ops = data
    else:
        raw_ops = []
    ops = validate_operations(raw_ops, items, state, section_titles)
    covered = {op["feedback_id"] for op in ops}
    for item in items:
        if item["id"] not in covered:
            ops.append({
                "feedback_id": item["id"],
                "op": "directive",
                "content": item["text"],
                "section_ids": [item["section_id"]] if item.get("section_id") else [],
                "rationale": "Not mapped to the argument graph; passed to the plan writer as an instruction.",
                "fallback": True,
            })
    return ops


def validate_operations(raw_ops, items, state, section_titles) -> List[Dict[str, Any]]:
    options = state.get("handling_options") or []
    arguments = state.get("arguments") or []
    item_ids = [item["id"] for item in items]
    per_item: Dict[str, int] = {}
    seen = set()
    ops: List[Dict[str, Any]] = []
    for raw in raw_ops if isinstance(raw_ops, list) else []:
        if not isinstance(raw, dict):
            continue
        kind = _OPS.get(str(raw.get("op") or raw.get("operation") or "").strip().lower())
        feedback_id = str(raw.get("feedback_id") or "").strip()
        if feedback_id not in item_ids:
            if len(item_ids) != 1:
                continue
            feedback_id = item_ids[0]
        if kind is None or per_item.get(feedback_id, 0) >= MAX_OPS_PER_ITEM:
            continue
        content = " ".join(str(raw.get("content") or "").split())
        rationale = clip_text(str(raw.get("rationale") or ""), 300)
        op: Optional[Dict[str, Any]] = None
        if kind == "add_argument":
            stance = _STANCES.get(str(raw.get("stance") or "").strip().lower())
            target = find_argument(active_arguments(arguments), str(raw.get("target_arg_id") or "").strip())
            option_text = target.parent_option if target else resolve_option(options, raw.get("option_id") or raw.get("option"))
            if stance and option_text and len(content) >= 8:
                op = {"op": kind, "option": option_text, "stance": stance, "content": content,
                      "target_arg_id": target.arg_id if target else None}
        elif kind in ("reject_argument", "edit_argument"):
            target = find_argument(active_arguments(arguments), str(raw.get("arg_id") or "").strip())
            if target is not None and kind == "reject_argument":
                op = {"op": kind, "arg_id": target.arg_id,
                      "reason": clip_text(str(raw.get("reason") or rationale), 300) or None}
            elif target is not None and len(content) >= 8 and content != target.content:
                op = {"op": kind, "arg_id": target.arg_id, "content": content}
        elif kind == "add_option":
            existing = {" ".join(option.lower().split()) for option in options}
            if len(content) >= 8 and content.lower() not in existing:
                op = {"op": kind, "content": content}
        elif kind == "directive" and content:
            sections = raw.get("section_ids") or []
            sections = [sections] if isinstance(sections, str) else sections
            op = {"op": kind, "content": content,
                  "section_ids": [sid for sid in sections if sid in section_titles]}
        if op is None:
            continue
        key = (feedback_id, kind, op.get("arg_id"), op.get("content"), op.get("option"))
        if key in seen:
            continue
        seen.add(key)
        per_item[feedback_id] = per_item.get(feedback_id, 0) + 1
        ops.append({"feedback_id": feedback_id, **op, "rationale": rationale})
    return ops


# ------------------------------------------------------------------- applying

def apply_feedback_ops(state, ops: List[Dict[str, Any]], items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Apply validated operations to the argument graph and log them as human operations."""
    text_by_item = {item["id"]: item["text"] for item in items}
    state.setdefault("writer_directives", [])
    applied = []
    for op in ops:
        kind = op["op"]
        feedback_id = op["feedback_id"]
        if kind == "add_argument":
            arg = Argument(
                content=op["content"],
                argument_type=op["stance"],
                parent_option=op["option"],
                agent_role="Clinician feedback",
                source="feedback",
                human_status="added",
                feedback_id=feedback_id,
                target_arg_id=op.get("target_arg_id"),
            )
            arg.arg_id = new_arg_id(state)
            state["arguments"].append(arg)
            record_human_op(state, "add", arg, origin="feedback", feedback_id=feedback_id)
            applied.append({**op, "arg_id": arg.arg_id})
        elif kind == "reject_argument":
            arg = find_argument(state["arguments"], op["arg_id"])
            if arg is None or arg.human_status == "rejected":
                continue
            arg.human_status = "rejected"
            arg.rejection_reason = op.get("reason")
            record_human_op(state, "reject", arg, origin="feedback", feedback_id=feedback_id, reason=op.get("reason"))
            applied.append(op)
        elif kind == "edit_argument":
            arg = find_argument(state["arguments"], op["arg_id"])
            if arg is None:
                continue
            before = arg.content
            if arg.original_content is None:
                arg.original_content = before
            arg.content = op["content"]
            if arg.human_status != "added":
                arg.human_status = "edited"
            record_human_op(state, "edit", arg, origin="feedback", feedback_id=feedback_id, before=before)
            applied.append(op)
        elif kind == "add_option":
            option = op["content"]
            state["handling_options"].append(option)
            clinician_arg = Argument(
                content=f"The reviewing clinician recommends this option: {clip_text(text_by_item.get(feedback_id, option), 400)}",
                argument_type="support",
                parent_option=option,
                agent_role="Clinician feedback",
                source="feedback",
                human_status="added",
                feedback_id=feedback_id,
            )
            clinician_arg.arg_id = new_arg_id(state)
            state["arguments"].append(clinician_arg)
            team_args = generate_option_arguments(state, option)
            for arg in team_args:
                arg.arg_id = new_arg_id(state)
                state["arguments"].append(arg)
            record_human_op(state, "add_option", None, origin="feedback", feedback_id=feedback_id, content=option,
                            option=option, arg_id=clinician_arg.arg_id)
            applied.append({**op, "arg_id": clinician_arg.arg_id,
                            "team_arg_ids": [arg.arg_id for arg in team_args]})
        elif kind == "directive":
            directive = {"feedback_id": feedback_id, "content": op["content"], "section_ids": op.get("section_ids") or []}
            state["writer_directives"].append(directive)
            record_human_op(state, "directive", None, origin="feedback", feedback_id=feedback_id,
                            content=op["content"], section_ids=directive["section_ids"])
            applied.append(op)
    return applied


def generate_option_arguments(state, option: str) -> List[Argument]:
    """One call for the care team's view on an option the clinician added."""
    team = state.get("healthcare_team") or []
    roles = [member.get("role") or member.get("name") for member in team if member.get("role") or member.get("name")]
    if not roles:
        return []
    prompt = f"""A reviewing clinician proposed a new care option for this older adult. Give the care team's perspective on it.

Patient Information:
{clip_text(state.get('patient_info', ''), 1500)}

New Care Option:
{option}

For each of these professionals: {', '.join(roles)}
write one supporting argument and one concern, each on its own line, formatted exactly as:
Support: [Role] argument
Challenge: [Role] concern"""
    response = call_llm(prompt, temperature=0.5, max_tokens=2048)
    arguments = []
    for line in response.splitlines():
        clean = line.strip().lstrip("*#- ").replace("**", "")
        match = re.match(r"(Support|Challenge|Attack)\s*:\s*(?:\[([^\]]+)\])?\s*(.+)", clean, re.IGNORECASE)
        if not match or len(match.group(3)) < 8:
            continue
        role = (match.group(2) or "").strip()
        if role not in roles:
            role = next((r for r in roles if r.lower() in role.lower() or role.lower() in r.lower()), roles[0])
        arguments.append(Argument(
            content=f"[{role}] {match.group(3).strip()}",
            argument_type="support" if match.group(1).lower() == "support" else "attack",
            parent_option=option,
            agent_role=role,
            agent_name=role,
        ))
    return arguments[: 2 * len(roles)]


# ------------------------------------------------------------ revision strategy

def ops_since(state, cursor: int) -> List[Dict[str, Any]]:
    return list((state.get("human_ops_log") or [])[cursor:])


def _sections_for_ops(ops: List[Dict[str, Any]], items: List[Dict[str, Any]], known: List[str]) -> List[str]:
    sections = []
    for op in ops:
        kind = op.get("op")
        if kind in ("add", "reject", "edit", "restore", "add_argument", "reject_argument", "edit_argument"):
            sections.append("interventions")
            if op.get("stance") == "attack":
                sections.append("risks")
        elif kind == "directive":
            sections.extend(op.get("section_ids") or [])
    sections.extend(item["section_id"] for item in items if item.get("section_id"))
    return [sid for sid in dict.fromkeys(sections) if sid in known]


def strategy_signals(state, delta: Dict[str, Any], recent_ops: List[Dict[str, Any]],
                     items: List[Dict[str, Any]], known_sections: List[str]) -> Dict[str, Any]:
    tier_changes = [
        {"option_id": row["option_id"], "option": row["option"],
         "before": row["tier_before"], "after": row["tier_after"]}
        for row in delta.get("options", [])
        if row["tier_before"] is not None and row["tier_before"] != row["tier_after"]
    ]
    graph_ops = [op for op in recent_ops if op.get("op") != "directive"]
    directives = [op for op in recent_ops if op.get("op") == "directive"]
    return {
        "graph_operations": len(graph_ops),
        "directives": len(directives),
        "global_directives": sum(1 for op in directives if not op.get("section_ids")),
        "options_added": delta.get("options_added", []),
        "ranking_changed": delta.get("ranking_changed", False),
        "tier_changes": tier_changes,
        "max_strength_shift": delta.get("max_strength_shift", 0.0),
        "anchored_sections": _sections_for_ops(recent_ops, items, known_sections),
    }


def rule_strategy(signals: Dict[str, Any], known_sections: List[str]) -> Dict[str, Any]:
    """Deterministic strategy choice; the LLM may refine it but never weaken a structural rewrite."""
    structural = bool(signals["options_added"] or signals["ranking_changed"] or signals["tier_changes"])
    if structural:
        return {"strategy": "full_regeneration", "sections": list(known_sections), "structural": True}
    if signals["graph_operations"] == 0 and signals["directives"] == 0:
        # Nothing was contested: regenerating means re-drafting from the current evaluation.
        return {"strategy": "full_regeneration", "sections": list(known_sections), "structural": False}
    if signals["graph_operations"] == 0 and signals["directives"] and signals["global_directives"]:
        return {"strategy": "presentation_rewrite", "sections": list(known_sections), "structural": False}
    if signals["global_directives"]:
        return {"strategy": "full_regeneration", "sections": list(known_sections), "structural": False}
    sections = signals["anchored_sections"] or (["interventions"] if signals["graph_operations"] else [])
    if not sections:
        return {"strategy": "presentation_rewrite", "sections": list(known_sections), "structural": False}
    if len(sections) >= max(5, len(known_sections) - 1):
        return {"strategy": "full_regeneration", "sections": list(known_sections), "structural": False}
    return {"strategy": "targeted_revision", "sections": sections, "structural": False}


def rule_rationale(strategy: str, signals: Dict[str, Any], sections: List[str], titles: Dict[str, str]) -> str:
    if strategy == "full_regeneration":
        reasons = []
        if signals["options_added"]:
            reasons.append("a new care option was added (" + "; ".join(clip_text(o, 80) for o in signals["options_added"]) + ")")
        for change in signals["tier_changes"]:
            reasons.append(f"the assessment of {change['option_id']} changed from "
                           f"\"{TIER_LABELS.get(change['before'], change['before'])}\" to "
                           f"\"{TIER_LABELS.get(change['after'], change['after'])}\"")
        if signals["ranking_changed"]:
            reasons.append("the priority order of the care options changed")
        if signals["global_directives"] and not reasons:
            reasons.append("the feedback applies to the whole plan")
        if not reasons and not signals["graph_operations"] and not signals["directives"]:
            return ("No argument was contested since the last version, so the plan was re-drafted from "
                    "the current argument evaluation.")
        if not reasons:
            reasons.append("the feedback touches most sections of the plan")
        return ("The whole plan was regenerated because " + "; ".join(reasons) + ". Every section depends on "
                "the option priorities, so a partial edit would have left the plan inconsistent.")
    if strategy == "presentation_rewrite":
        return ("The feedback concerns presentation only, so the plan was rewritten for style and format while "
                "its recommendations, assessments and responsibilities were kept unchanged.")
    names = ", ".join(titles.get(sid, sid) for sid in sections)
    return (f"The re-weighed arguments did not change any option's assessment or priority, so only the affected "
            f"sections ({names}) were rewritten and the rest of the plan was kept as it was.")


def plan_revision_strategy(state, delta: Dict[str, Any], recent_ops: List[Dict[str, Any]],
                           items: List[Dict[str, Any]], section_titles: Dict[str, str]) -> Dict[str, Any]:
    """Reason about how to update the plan, with rule-based guardrails."""
    known = list(section_titles)
    signals = strategy_signals(state, delta, recent_ops, items, known)
    rules = rule_strategy(signals, known)
    if rules["structural"]:
        # A changed option assessment or ranking leaves no choice: every section depends on
        # the priorities, so the plan is regenerated and the rules explain exactly why.
        return {
            "strategy": "full_regeneration",
            "strategy_label": STRATEGY_LABELS["full_regeneration"],
            "sections": known,
            "rationale": rule_rationale("full_regeneration", signals, known, section_titles),
            "decided_by": "rules",
            "rule_strategy": rules["strategy"],
            "signals": signals,
        }

    change_lines = []
    for row in delta.get("options", []):
        before = (f"{row['strength_before']:.2f} ({TIER_LABELS.get(row['tier_before'], row['tier_before'])})"
                  if row["strength_before"] is not None else "new option")
        change_lines.append(f"{row['option_id']} {clip_text(row['option'], 80)}: {before} -> "
                            f"{row['strength_after']:.2f} ({TIER_LABELS.get(row['tier_after'], row['tier_after'])})")
    guidance = f"A rule-based check suggests {rules['strategy']} on {', '.join(rules['sections'])}."
    op_lines = [_describe_op(op) for op in recent_ops[:20]]
    prompt = f"""You are deciding how to update a care plan after a clinician contested it. The argument graph has been updated, re-verified and re-weighed. Choose ONE strategy:
- targeted_revision: rewrite only the listed sections and keep every other section word for word. Best when the change is local and no option's assessment or priority changed.
- full_regeneration: rewrite the whole plan from the re-weighed arguments. Needed when an option's assessment or the option ranking changed, a care option was added, or the feedback affects most of the plan.
- presentation_rewrite: rewrite the plan's presentation without changing its clinical content. Only for feedback that is purely about style, length or format.

Clinician feedback:
{chr(10).join(describe_item(item, section_titles) for item in items) or "(none: the clinician edited the argument table directly)"}

Operations applied to the argument graph:
{chr(10).join(op_lines) or "(none)"}

Option assessment changes (strength 0-1):
{chr(10).join(change_lines) or "(none)"}

Plan sections: {", ".join(f"{sid} ({title})" for sid, title in section_titles.items())}

{guidance}

Return JSON only: {{"strategy": "targeted_revision|full_regeneration|presentation_rewrite", "sections": ["section ids to rewrite"], "rationale": "two or three sentences for the clinician explaining the choice"}}"""
    data = call_llm_json(prompt, temperature=0.2, max_tokens=2048)

    strategy, sections, rationale, decided_by = rules["strategy"], rules["sections"], None, "rules"
    if isinstance(data, dict) and data.get("strategy") in STRATEGIES:
        proposed = data["strategy"]
        proposed_sections = [sid for sid in (data.get("sections") or []) if sid in section_titles]
        llm_rationale = clip_text(str(data.get("rationale") or ""), 700) or None
        if proposed == "presentation_rewrite" and signals["graph_operations"]:
            decided_by = "rules"  # clinical changes cannot be handled as a presentation rewrite
        elif proposed == "targeted_revision":
            sections = list(dict.fromkeys(proposed_sections + signals["anchored_sections"])) or rules["sections"]
            strategy, rationale, decided_by = proposed, llm_rationale, "llm"
            if len(sections) >= max(5, len(known) - 1):
                strategy, sections, rationale, decided_by = "full_regeneration", known, None, "rules"
        else:
            strategy, sections, rationale, decided_by = proposed, known, llm_rationale, "llm"
    if strategy != "targeted_revision":
        sections = known
    return {
        "strategy": strategy,
        "strategy_label": STRATEGY_LABELS[strategy],
        "sections": sections,
        "rationale": rationale or rule_rationale(strategy, signals, sections, section_titles),
        "decided_by": decided_by,
        "rule_strategy": rules["strategy"],
        "signals": signals,
    }


def _describe_op(op: Dict[str, Any]) -> str:
    kind = op.get("op")
    origin = f" (from {op['feedback_id']})" if op.get("feedback_id") else ""
    if kind in ("add", "reject", "edit", "restore"):
        verb = {"add": "added", "reject": "removed", "edit": "edited", "restore": "restored"}[kind]
        target = f" against {op['target_arg_id']}" if op.get("target_arg_id") else ""
        return f"- {verb} {op.get('arg_id')} ({op.get('stance')}{target}): {clip_text(op.get('content', ''), 160)}{origin}"
    if kind == "add_option":
        return f"- added care option: {clip_text(op.get('content', ''), 160)}{origin}"
    if kind == "directive":
        return f"- writer instruction: {clip_text(op.get('content', ''), 160)}{origin}"
    return f"- {kind}{origin}"


def describe_ops(ops: List[Dict[str, Any]]) -> List[str]:
    return [_describe_op(op) for op in ops]


def describe_feedback_op(op: Dict[str, Any]) -> str:
    """One line per feedback-derived operation, with the interpreter's rationale."""
    kind = op.get("op")
    if kind == "add_argument":
        target = f" {op['target_arg_id']}" if op.get("target_arg_id") else f" {clip_text(op.get('option', ''), 60)}"
        verb = "supports" if op.get("stance") == "support" else "challenges"
        what = f"new argument {op.get('arg_id', '')} {verb}{target}: {clip_text(op.get('content', ''), 160)}"
    elif kind == "reject_argument":
        what = f"remove {op.get('arg_id')}"
    elif kind == "edit_argument":
        what = f"correct {op.get('arg_id')}: {clip_text(op.get('content', ''), 160)}"
    elif kind == "add_option":
        what = f"add care option: {clip_text(op.get('content', ''), 160)}"
    else:
        what = f"writer instruction: {clip_text(op.get('content', ''), 160)}"
    why = f" ({clip_text(op['rationale'], 160)})" if op.get("rationale") else ""
    return f"{op.get('feedback_id')} -> {what}{why}"
