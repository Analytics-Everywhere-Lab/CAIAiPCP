"""Compact chat context: the assistant knows every argument and the current
care plan at a bounded token cost, while none of it is shown in the chat.

Techniques:
1. Structured encoding of the argument graph: one pipe-delimited row per
   argument with short ids, role abbreviations, rounded scores and truncated
   text; argument text is shortened adaptively until the block fits its budget.
2. Plan compaction: the whole plan when it fits; otherwise each section keeps
   its heading and leading lines within its share of the budget.
3. Rolling conversation summary: turns older than the most recent few are
   folded into a running summary (LLM-written, extractive fallback) once the
   history exceeds its budget.
4. A bounded event log of contestations and plan versions, folded into the
   summary when it grows.
5. Prefix stability: the case context is cached per plan version and argument
   state, and placed before the volatile conversation, so Ollama can reuse its
   KV cache for the unchanged prompt prefix across turns, and the Claude API
   serves it from the prompt cache.

Only what the assistant reads is compacted; its answers are written in full.
"""
import hashlib
import json
from typing import Any, Callable, Dict, List, Optional

from arguments import option_id, option_index
from care_plan_document import sections_to_markdown
from env_config import CHAT_CONTEXT_TOKEN_BUDGET, CHAT_HISTORY_TOKEN_BUDGET, CHAT_RECENT_TURNS
from utils import clip_text

ROLE_ABBREVIATIONS = {
    "Registered Nurse": "RN",
    "General Practitioner": "GP",
    "Geriatrician": "GER",
    "Physical Therapist": "PT",
    "Occupational Therapist": "OT",
    "Social Worker": "SW",
    "Psychiatrist": "PSY",
    "Nutritionist": "NUT",
    "Home Health Aide": "HHA",
    "Pharmacist": "PHA",
    "Care Coordinator": "CC",
    "Clinician feedback": "CLIN",
    "Learned guidance": "MEM",
}
STATUS_CODES = {"unreviewed": "-", "edited": "edited", "added": "added", "rejected": "removed"}

SYSTEM_PROMPT = """You are an expert geriatric care coordinator assisting a clinician with one patient's aging-in-place care plan.
You know every argument the care team weighed (+ supports an option, - challenges it) and the current version of the plan.
They are given below in a compact machine notation that only saves reading cost; never answer in that notation.
Answer the clinician fully, in clear and compassionate clinical prose. Use Markdown (short headings, lists, tables) when it helps.
Describe arguments and options in words, spell out role abbreviations (RN = Registered Nurse), and cite ids such as A3 or O1 only in parentheses.
If the clinician wants the plan changed, say they can add feedback notes on the plan or edit the argument table, then regenerate.
Do not invent clinical facts that are not in the context."""


def estimate_tokens(text: str) -> int:
    return (len(text or "") + 3) // 4


def _role(role: Optional[str]) -> str:
    return ROLE_ABBREVIATIONS.get(role or "", (role or "GEN")[:4].upper())


def _strip_role_tag(content: str) -> str:
    """Drop the "[Role] " prefix agent arguments carry; the role has its own column."""
    content = content or ""
    if content.startswith("[") and "]" in content[:60]:
        return content.split("]", 1)[1].strip()
    return content


def compact_arguments(state: Dict[str, Any], max_tokens: int) -> str:
    options = state.get("handling_options") or []
    qbaf_rows = {row["option_id"]: row for row in (state.get("qbaf") or {}).get("options", [])}
    option_lines = ["OPTIONS (id|assessment|strength|text)"]
    for index, option in enumerate(options):
        row = qbaf_rows.get(option_id(index), {})
        strength = f"{row['strength']:.2f}" if "strength" in row else "-"
        option_lines.append(f"{option_id(index)}|{row.get('tier_label', 'not yet weighed')}|{strength}|{clip_text(option, 160)}")
    arguments = state.get("arguments") or []
    header = "ARGUMENTS (id|option|stance|role|validity|strength|status|text)"

    def render(limit: int) -> str:
        rows = [header]
        for arg in arguments:
            idx = option_index(options, arg.parent_option)
            stance = "+" if arg.argument_type == "support" else "-"
            if arg.target_arg_id:
                stance += f">{arg.target_arg_id}"
            validity = f"{arg.validity_score:.2f}" if arg.validity_score is not None else "-"
            strength = f"{arg.strength:.2f}" if arg.strength is not None else "-"
            rows.append("|".join([
                arg.arg_id or "?", option_id(idx) if idx is not None else "?", stance, _role(arg.agent_role),
                validity, strength, STATUS_CODES.get(arg.human_status, arg.human_status),
                clip_text(_strip_role_tag(arg.content), limit),
            ]))
        return "\n".join(option_lines + rows)

    limit = 220
    block = render(limit)
    while estimate_tokens(block) > max_tokens and limit > 50:
        limit -= 30
        block = render(limit)
    return block


def compact_plan(plan: Optional[Dict[str, Any]], max_tokens: int) -> str:
    if not plan:
        return "No care plan yet."
    sections = plan.get("sections") or []
    full = "\n".join(
        line.rstrip() for line in sections_to_markdown(sections).splitlines()
        if line.strip() and not set(line.strip()) <= set("|-: ")  # blank lines and table separators
    )
    if estimate_tokens(full) <= max_tokens or not sections:
        return full
    share = max(120, (max_tokens * 4) // len(sections))
    parts = []
    for section in sections:
        kept, used = [f"## {section['title']}"], 0
        for line in (section.get("content") or "").splitlines():
            line = line.strip()
            if not line or set(line) <= set("|-: "):
                continue  # blank lines and table separators carry no information
            if line.startswith("|"):
                line = "|".join(cell.strip() for cell in line.strip("|").split("|"))
            line = clip_text(line, 160)
            if used + len(line) > share:
                kept.append("...")
                break
            kept.append(line)
            used += len(line)
        parts.append("\n".join(kept))
    return "\n".join(parts)


def case_context_key(state: Dict[str, Any]) -> str:
    plan = state.get("revised_care_plan") or {}
    args = [(a.arg_id, a.human_status, a.content, a.validity_score, a.strength) for a in state.get("arguments") or []]
    basis = json.dumps([plan.get("version"), plan.get("status"), args, len(state.get("feedback_history") or [])],
                       default=str)
    return hashlib.sha1(basis.encode()).hexdigest()[:16]


def compact_case_context(state: Dict[str, Any], budget: int = CHAT_CONTEXT_TOKEN_BUDGET) -> str:
    plan = state.get("revised_care_plan") or {}
    team = ", ".join(member.get("name") or member.get("role", "") for member in state.get("healthcare_team") or [])
    header = [
        f"PATIENT: {clip_text(state.get('patient_info', ''), 600)}",
        f"SEVERITY: {state.get('severity') or '-'} | CARE TEAM: {team or '-'}",
    ]
    if plan:
        header.append(
            f"PLAN: v{plan.get('version')} ({plan.get('status', 'draft')}), {plan.get('strategy_label', '')}, "
            f"decision confidence {round(100 * (plan.get('decision_confidence') or 0))}%"
        )
    feedback = state.get("feedback_history") or []
    if feedback:
        header.append("CLINICIAN FEEDBACK: " + " ; ".join(
            f"{item['id']}: {clip_text(item['text'], 120)}" for item in feedback[-6:]))
    remaining = max(200, budget - estimate_tokens("\n".join(header)))
    arguments = compact_arguments(state, int(remaining * 0.45))
    plan_text = compact_plan(plan, remaining - estimate_tokens(arguments))
    return "\n".join(header + [arguments, "CURRENT CARE PLAN:", plan_text])


class ChatMemory:
    """Conversation history with rolling summarization and a bounded event log."""

    def __init__(self, recent_turns: int = CHAT_RECENT_TURNS, history_budget: int = CHAT_HISTORY_TOKEN_BUDGET,
                 max_events: int = 12) -> None:
        self.recent_turns = recent_turns
        self.history_budget = history_budget
        self.max_events = max_events
        self.turns: List[Dict[str, str]] = []
        self.summary = ""
        self.events: List[str] = []
        self.context_key: Optional[str] = None
        self.context_text = ""
        self.compactions = 0

    def case_context(self, state: Dict[str, Any]) -> str:
        key = case_context_key(state)
        if key != self.context_key:
            self.context_key, self.context_text = key, compact_case_context(state)
        return self.context_text

    def add_turn(self, role: str, content: str) -> None:
        self.turns.append({"role": role, "content": content})

    def add_event(self, text: str) -> None:
        self.events.append(clip_text(text, 240))
        if len(self.events) > self.max_events:
            overflow, self.events = self.events[: -self.max_events], self.events[-self.max_events:]
            self.summary = clip_text((self.summary + " Earlier events: " + "; ".join(overflow)).strip(),
                                     self.history_budget * 2)

    def history_tokens(self) -> int:
        return estimate_tokens(self.summary) + sum(estimate_tokens(turn["content"]) for turn in self.turns)

    def compact(self, summarize: Optional[Callable[[str], str]] = None) -> bool:
        """Fold turns older than the recent window into the running summary when over budget."""
        if self.history_tokens() <= self.history_budget or len(self.turns) <= self.recent_turns:
            return False
        older, self.turns = self.turns[: -self.recent_turns], self.turns[-self.recent_turns:]
        transcript = "\n".join(f"{turn['role'].title()}: {turn['content']}" for turn in older)
        updated = None
        if summarize is not None:
            prompt = (
                "Update the running summary of a conversation between a clinician and a care-planning assistant. "
                "Keep facts, decisions, the clinician's preferences and open questions; drop pleasantries. "
                "Write at most 120 words of plain text.\n\n"
                f"Current summary:\n{self.summary or '(empty)'}\n\nNew exchanges:\n{transcript}\n\nUpdated summary:"
            )
            try:
                updated = (summarize(prompt) or "").strip()
            except Exception:
                updated = None
        if not updated:
            digest = " ".join(
                f"{'Q' if turn['role'] == 'user' else 'A'}: {clip_text(turn['content'], 120)}" for turn in older)
            updated = (self.summary + " " + digest).strip()
        self.summary = clip_text(updated, self.history_budget * 2)
        self.compactions += 1
        return True

    @staticmethod
    def prompt_prefix(case_context: str) -> str:
        """The stable head of every chat prompt for this plan version and argument state."""
        return "\n".join([SYSTEM_PROMPT, "", "CASE CONTEXT (compact notation)", case_context])

    def build_prompt(self, case_context: str, question: str) -> str:
        parts = [self.prompt_prefix(case_context)]
        if self.summary:
            parts += ["", "CONVERSATION SUMMARY", self.summary]
        if self.events:
            parts += ["", "RECENT EVENTS"] + [f"- {event}" for event in self.events]
        if self.turns:
            parts += ["", "RECENT CONVERSATION"]
            parts += [f"{'User' if turn['role'] == 'user' else 'Assistant'}: {turn['content']}" for turn in self.turns]
        parts += ["", f"User: {question}", "Assistant:"]
        return "\n".join(parts)

    def stats(self, prompt: str) -> Dict[str, Any]:
        return {
            "prompt_tokens": estimate_tokens(prompt),
            "context_tokens": estimate_tokens(self.context_text),
            "history_tokens": self.history_tokens(),
            "turns_kept": len(self.turns),
            "compactions": self.compactions,
        }
