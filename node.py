import hashlib
import json
from typing import Any, Dict, List, Optional, Set
from mcp_utils import _fetch_available_slots_for_roles
from rag import literature
from rag.vector_db import MedicalVectorDB
from state import Argument, GraphState, active_progress
from llm_caller import call_llm, call_llm_json, stream_text

def _report_progress(state: GraphState, key: str, msg: str):
    state[key] = msg
    tid = state.get("thread_id")
    if tid:
        if tid not in active_progress:
            active_progress[tid] = {}
        active_progress[tid][key] = msg
from utils import calculate_decision_confidence, clip_text
from agent_selection import (
    get_agents_for_condition_llm,
    explain_team_selection,
    analyze_patient_needs,
)
from arguments import (
    active_arguments,
    ensure_argument_ids,
    find_argument,
    is_human_authored,
    net_human_ops,
    option_id,
    option_index,
    resolve_option,
)
from care_plan_document import (
    PLAN_SECTIONS,
    SECTION_IDS,
    SECTION_TITLES,
    STRATEGY_LABELS,
    changed_section_ids,
    merge_sections,
    now_iso,
    parse_sections,
    reference_list,
    section_template_prompt,
    sections_to_markdown,
    strip_section_heading,
)
from env_config import MEMORY_INSTANTIATE_ARGUMENTS
from feedback import (
    apply_feedback_ops,
    describe_feedback_op,
    describe_item,
    describe_ops,
    feedback_context,
    feedback_signature,
    interpret_feedback,
    normalize_feedback_items,
    ops_since,
    plan_revision_strategy,
)
from memory.reflection import case_fingerprint, profile_tags
from memory.retriever import guidance_lines, record_summary
from memory.service import get_memory_service
from qbaf import evaluate_qbaf, qbaf_delta, qbaf_prompt_summary
import re


def _memory_guidance(state: GraphState, stage: str, query_text: str, top_k: Optional[int] = None) -> List[Any]:
    """Retrieve long-term memory for a pipeline stage and record its use for this case."""
    service = get_memory_service()
    if service is None:
        return []
    try:
        tags = profile_tags(state.get("patient_info", ""), state.get("patient_analysis"), state.get("severity"))
        records = service.retrieve(stage, query_text, tags, top_k, exclude_case_id=state.get("thread_id"))
        if records:
            guidance = state.get("memory_guidance") or {}
            guidance[stage] = [record_summary(record) for record in records]
            state["memory_guidance"] = guidance
            if state.get("thread_id"):
                service.log_usage(state["thread_id"], [record.memory_id for record in records], "prompted")
        return records
    except Exception as e:
        print(f"[memory] retrieval failed for {stage}: {e}")
        return []


def _guidance_block(records: List[Any]) -> str:
    if not records:
        return ""
    lines = "\n".join(f"- {line}" for line in guidance_lines(records))
    return (
        "\nLessons from earlier clinician reviews of other patients (guidance only, not evidence about "
        f"this patient; apply a lesson only where it clearly fits):\n{lines}\n"
    )


def _stream_llm(state: GraphState, prompt: str, temperature: float, max_tokens: int) -> str:
    """Call the LLM, streaming partial text to the progress tracker when enabled."""
    if not state.get("enable_streaming", False):
        return call_llm(prompt, temperature=temperature, max_tokens=max_tokens)
    partial = ""
    for partial in stream_text(prompt, temperature=temperature, max_tokens=max_tokens):
        state["partial_response"] = partial
        _report_progress(state, "current_stream_text", partial)
    return partial


MAX_SIMILAR_CASES = 6
CASE_RECORDS_RULE = ("They describe OTHER patients: use them only as background for clinical reasoning. Never cite, "
                     "quote or describe them, and never mention that other patients' records were consulted.")
FULL_CONTEXT = {"max_refs": 10, "max_cases": 5, "ref_chars": 1200, "case_chars": 1200}
COMPACT_CONTEXT = {"max_refs": 8, "max_cases": 3, "ref_chars": 600, "case_chars": 500}


def _venue(ref: Dict[str, Any]) -> str:
    return ", ".join(part for part in (ref.get("kind"), ref.get("journal"), ref.get("year")) if part)


def _knowledge_context(state: GraphState, max_refs: int, max_cases: int, ref_chars: int, case_chars: int) -> str:
    """Retrieved knowledge for prompts, in two parts that are never mixed: published sources the plan
    may cite as [REF-n], and case records of other patients that are background only."""
    references = state.get("document_references") or []
    cases = state.get("similar_cases") or []
    if not references and not cases:
        return ""
    if references:
        lines = ["PUBLISHED EVIDENCE (cite as [REF-n] where you use it):"]
        for ref in references[:max_refs]:
            lines.append(f"[REF-{ref['id']}] {ref.get('title', '')} ({_venue(ref)}): {clip_text(ref.get('full_content', ''), ref_chars)}")
    else:
        lines = ["PUBLISHED EVIDENCE: none retrieved, so use no [REF-n] citations."]
    if cases:
        lines.append(f"\nSIMILAR CASE RECORDS (background only). {CASE_RECORDS_RULE}")
        lines += [f"- {clip_text(case['document'], case_chars)}" for case in cases[:max_cases]]
    return "\n".join(lines)


_CITATION_GROUP = re.compile(r"\[(REF-\d+(?:\s*[,;]\s*(?:REF-)?\d+)+)\]")
_CITATION = re.compile(r"\s?\[REF-(\d+)\]")
_PLACEHOLDER_CITATION = re.compile(r"\s?\[REF-(?!\d)[^\]]{0,12}\]")


def _source_ids(state: GraphState) -> Set[int]:
    return {ref["id"] for ref in state.get("document_references") or []}


def _clean_citations(text: str, valid_ids: Set[int]) -> str:
    """Keep only citations of the case's published sources: "[REF-1, REF-2]" becomes "[REF-1][REF-2]",
    and a number that no source has, or a placeholder such as [REF-X], is dropped."""
    text = _CITATION_GROUP.sub(lambda m: "".join(f"[REF-{n}]" for n in re.findall(r"\d+", m.group(1))), text or "")
    text = _CITATION.sub(lambda m: m.group(0) if int(m.group(1)) in valid_ids else "", text)
    return _PLACEHOLDER_CITATION.sub("", text)


def determine_severity_from_patient_info(patient_info: str) -> str:
    prompt = f"""You are a medical triage assistant. Based on this patient information, assess the severity of their condition as one of: Low, Moderate, High, or Very High.
    Patient Info: {patient_info}
    Output ONLY the severity level word(s)."""
    response = call_llm(prompt, temperature=0.1, max_tokens=10)
    res = response.strip()
    for s in ["Very High", "High", "Moderate", "Low"]:
        if s.lower() in res.lower():
            return s
    return "Moderate"

def get_max_tokens_for_severity(base_tokens: int, severity: str) -> int:
    s = (severity or "moderate").lower()
    if s == "low": return max(8000, int(base_tokens * 1.25))
    if s == "moderate": return max(10000, int(base_tokens * 1.5))
    if "very high" in s: return max(15000, int(base_tokens * 2.5))
    if "high" in s: return max(12000, int(base_tokens * 2))
    return base_tokens
MAX_CARE_OPTIONS = 2
OPTION_CANDIDATES = 3
_FIT_ORDER = {"strong": 0, "possible": 1}


def _screened_options(state: GraphState, context_section: str, memory_section: str) -> List[str]:
    """Propose candidate options and keep only those the planner itself would recommend.

    An option that the system proposes and then weighs as "not recommended" reads as
    the system contradicting itself, so candidates are screened for fit with the
    patient's wishes, needs and safety before the care team argues them."""
    prompt = f"""You are an expert geriatric care planner. Propose care options for this older adult's aging-in-place care plan.
    {context_section}
    {memory_section}
    Patient Information:
    {state['patient_info']}

    Propose {OPTION_CANDIDATES} candidate options. Each is a concrete, implementable package of care: what is done, by whom,
    and how it helps this person live safely. Propose only options you would actually recommend for THIS patient:
    respect their stated wishes, address their main risks, and never add an option you would advise against just
    for contrast.

    Then screen each candidate as a careful clinician would:
    - "fit": "strong" (clearly right for this patient), "possible" (reasonable, with conditions) or "poor" (conflicts
      with the patient's wishes, needs or safety; you would not recommend it)
    - "why": one sentence.

    Return JSON only: {{"options": [{{"option": "<short title of what it involves>", "fit": "strong", "why": "..."}}]}}"""
    result = call_llm_json(prompt, temperature=0.5, max_tokens=get_max_tokens_for_severity(1536, state["severity"]))
    items = result.get("options") if isinstance(result, dict) else None
    candidates = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        text = " ".join(str(item.get("option") or "").replace("**", "").split())
        if text and text.lower() not in {c["option"].lower() for c in candidates}:
            fit = str(item.get("fit") or "").strip().lower()
            candidates.append({"option": text, "fit": fit if fit in ("strong", "possible", "poor") else "possible",
                               "why": clip_text(str(item.get("why") or "").strip(), 300)})
    kept = sorted((c for c in candidates if c["fit"] != "poor"), key=lambda c: _FIT_ORDER[c["fit"]])[:MAX_CARE_OPTIONS]
    for candidate in candidates:
        candidate["kept"] = candidate in kept
    state["option_screening"] = candidates
    if kept and state.get("enable_streaming", False):
        # Show only what is proposed: a candidate that failed the screen is never presented,
        # so the trace does not read as the system turning down its own suggestion.
        _report_progress(state, "current_stream_text",
                         "\n".join(f"Option {i}: {c['option']}. {c['why']}" for i, c in enumerate(kept, 1)))
    print(f"Option screening: kept {len(kept)} of {len(candidates)} candidates")
    return [c["option"] for c in kept]


def _unscreened_options(state: GraphState, context_section: str, memory_section: str) -> List[str]:
    prompt = f"""You are an expert geriatric care planner. Based on the following patient information and relevant medical knowledge provided,
    generate 1-2 specific handling options for their care plan in aging-in-place context.

    {context_section}
    {memory_section}
    Patient Information:
    {state['patient_info']}

    Please provide handling options in the following format:
    Option 1: [Description]
    Option 2: [Description]
    ...

    Only include options you would recommend for this patient. Focus on practical, implementable options that
    support independent living while ensuring safety and quality of life."""

    max_toks = get_max_tokens_for_severity(2048, state["severity"])
    if state.get("enable_streaming", False):
        response = ""
        for response in stream_text(prompt, temperature=0.6, max_tokens=max_toks):
            _report_progress(state, "options_generation_progress", response)
            _report_progress(state, "current_stream_text", response)
    else:
        response = call_llm(prompt, temperature=0.6, max_tokens=max_toks)

    options = []
    for line in response.split("\n"):
        clean_line = line.strip().lstrip('*#- ')
        if clean_line.startswith("Option") or clean_line.startswith("**Option"):
            option_text = clean_line.split(":", 1)[1].strip() if ":" in clean_line else clean_line
            option_text = option_text.replace("**", "").strip()
            if option_text:
                options.append(option_text)
    return options[:MAX_CARE_OPTIONS]


def care_plan_generator(state: GraphState) -> GraphState:
    """First LLM: Generate handling options based on patient information"""
    if not state.get("severity") or state.get("severity").lower() == "default":
        if state.get("enable_streaming", False):
            _report_progress(state, "current_sub_step", "🔍 Analyzing patient condition to determine severity level...")
        state["severity"] = determine_severity_from_patient_info(state["patient_info"])
        print(f"🤖 AI determined severity: {state['severity']}")
        if state.get("enable_streaming", False):
            _report_progress(state, "current_sub_step", f"📊 Severity assessed: {state['severity']} — configuring generation parameters...")

    # Include RAG context if available
    context_section = ""
    if state.get("rag_context"):
        context_section = f"\n{state['rag_context']}\n"
        if state.get("enable_streaming", False):
            _report_progress(state, "current_sub_step", "📚 Integrating retrieved medical knowledge into context...")

    if state.get("enable_streaming", False):
        _report_progress(state, "current_sub_step", "🧠 Generating personalised care handling options...")

    memory_section = _guidance_block(_memory_guidance(state, "option_generation", state["patient_info"]))

    options = _screened_options(state, context_section, memory_section)
    if not options:
        # No usable screening answer (or no candidate passed it): fall back to the
        # plain-text format, which asks only for options the planner would recommend.
        options = _unscreened_options(state, context_section, memory_section)

    # Ensure we have at least one option
    if not options:
        print("Warning: No options parsed from LLM response. Using default options.")
        options = [
            "Home Safety Assessment and Modification",
            "Social Engagement and Support Groups",
            "Regular Health Monitoring and Care Coordination",
        ]

    # Citations in an option may only point at published sources the case retrieved.
    source_ids = _source_ids(state)
    state["handling_options"] = [_clean_citations(option, source_ids).strip() for option in options]
    state["current_step"] = "argument_generation"
    print("Options generated: ", options)
    return state


def argument_generator(state: GraphState) -> GraphState:
    """Second LLM: Generate support and challenge arguments for each handling option"""
    arguments = []
    rag_context = state.get("rag_context", "")

    print(f"Generating arguments for options: {state['handling_options']}")

    for i, option in enumerate(state["handling_options"]):
        if state.get("enable_streaming", False):
            _report_progress(state, "argument_generation_progress", (
                f"Generating arguments for option {i+1}/{len(state['handling_options'])}: {option[:50]}..."
            ))

        # Generate supporting arguments
        support_prompt = f"""
            Generate 1 strong supporting argument for the following elderly care handling option:
            {rag_context}
            Option: {option}
            Provide arguments that highlight benefits, feasibility, and positive outcomes.
            Format each argument on a new line starting with "Support:"."""

        max_toks = get_max_tokens_for_severity(1024, state["severity"])
        if state.get("enable_streaming", False):
            support_response = ""
            for support_response in stream_text(support_prompt, temperature=0.8, max_tokens=max_toks):
                state["current_argument_stream"] = support_response
                _report_progress(state, "current_stream_text", support_response)
        else:
            support_response = call_llm(support_prompt, temperature=0.8, max_tokens=max_toks)

        # Generate attacking arguments
        attack_prompt = f"""
            Generate 1 critical argument against the following elderly care handling option:
            Option: {option}        
            Provide arguments that highlight potential risks, challenges, or limitations.
            Format each argument on a new line starting with "Challenge:"."""

        if state.get("enable_streaming", False):
            attack_response = ""
            for attack_response in stream_text(attack_prompt, temperature=0.8, max_tokens=max_toks):
                state["current_argument_stream"] = attack_response
                _report_progress(state, "current_stream_text", attack_response)
        else:
            attack_response = call_llm(attack_prompt, temperature=0.8, max_tokens=max_toks)

        # Parse arguments
        for line in support_response.split("\n"):
            if line.strip().startswith("Support:"):
                arg_content = line.replace("Support:", "").strip()
                if arg_content:
                    arguments.append(
                        Argument(
                            content=arg_content,
                            argument_type="support",
                            parent_option=option,  # This should match exactly
                        )
                    )

        for line in attack_response.split("\n"):
            if line.strip().startswith("Challenge:"):
                arg_content = line.replace("Challenge:", "").strip()
                if arg_content:
                    arguments.append(
                        Argument(
                            content=arg_content,
                            argument_type="attack",
                            parent_option=option,  # This should match exactly
                        )
                    )

    print(f"Generated {len(arguments)} arguments")
    state["arguments"] = arguments
    state["current_step"] = "human_review"

    if "human_review_complete" not in state:
        state["human_review_complete"] = False
    return state


def multi_agent_argument_generator(state: GraphState) -> GraphState:
    """
    Enhanced multi-agent argument generation with LLM-based team selection
    Replaces the original multi_agent_argument_generator function
    """
    arguments = []
    rag_context = state.get("rag_context", "")
    patient_info = state["patient_info"]

    print(f"Generating arguments for options: {state['handling_options']}")
    print("\n🤖 Using AI to analyze patient and select optimal healthcare team...")

    if state.get("enable_streaming", False):
        _report_progress(state, "current_sub_step", "🤖 AI selecting optimal healthcare team for this patient profile...")

    # Check if user has specified custom team requirements
    custom_requirements = state.get("custom_team_requirements", None)

    # Use LLM to select the healthcare team
    healthcare_team, team_selection_logs = get_agents_for_condition_llm(
        patient_info=patient_info,
        enable_streaming=state.get("enable_streaming", False),
        custom_requirements=custom_requirements,
    )

    state["team_selection_logs"] = team_selection_logs

    team_explanation = explain_team_selection(
        patient_info=patient_info, selected_team=healthcare_team
    )

    state["team_selection_rationale"] = team_explanation

    print(
        f"\n✨ Healthcare team assembled: {[agent.name for agent in healthcare_team]}"
    )
    print(f"📝 Rationale: {team_explanation}\n")

    if state.get("enable_streaming", False):
        names = ", ".join(agent.name for agent in healthcare_team)
        _report_progress(state, "current_sub_step", f"👥 Team assembled: {names}")

    # Store agent assignments for tracking
    agent_arguments_tracking = {}

    # Store patient analysis
    if state["patient_analysis"] is None:
        state["patient_analysis"] = analyze_patient_needs(patient_info)

    memory_records = _memory_guidance(
        state, "argument_generation", f"{patient_info} {' '.join(state['handling_options'])}"
    )
    memory_section = _guidance_block(memory_records)

    for i, option in enumerate(state["handling_options"]):
        print(f"\nOption {i+1}: {option}")

        if state.get("enable_streaming", False):
            _report_progress(state, "current_sub_step",
                f"💭 Option {i+1}/{len(state['handling_options'])}: Gathering multi-disciplinary perspectives...")
            _report_progress(state, "argument_generation_progress", (
                f"Option {i+1}/{len(state['handling_options'])}: Gathering perspectives from {len(healthcare_team)} healthcare professionals..."
            ))

        option_arguments = []

        # Each agent provides their perspective
        for agent_idx, agent in enumerate(healthcare_team):
            if state.get("enable_streaming", False):
                _report_progress(state, "current_sub_step",
                    f"🔬 {agent.name} analyzing option {i+1}")
                _report_progress(state, "argument_generation_progress", (
                    f"Option {i+1}: [{agent_idx+1}/{len(healthcare_team)}] {agent.name} is analyzing..."
                ))

            # One balanced assessment per discipline and option. Asking separately for
            # pros and cons forced every option into the same number of each, padding
            # options with generic concerns (and generic benefits) that cancelled out.
            assessment_prompt = f"""{agent.get_perspective_prompt()}

                {rag_context}
                {memory_section}
                Patient Information:
                {patient_info}

                Care Option Being Evaluated:
                {option}

                Assess this care option for this patient from your perspective as a {agent.role.value}.
                Give 1-2 supporting arguments and 1-2 concerns, drawing on your expertise in
                {', '.join(agent.expertise_areas[:3])} and your priorities ({', '.join(agent.focus_priorities[:3])}).
                Only raise a concern that genuinely applies to this patient; do not pad with generic risks.
                State each concern as the risk or cost itself, not as a verdict on the option ("not recommended"):
                the clinician weighs the arguments and decides.
                Write each argument as one or two specific sentences about this patient, and never mention
                other patients or their case records.

                Format each argument on its own line, starting with "Support:" or "Challenge:"."""

            max_toks = get_max_tokens_for_severity(1024, state["severity"])
            if state.get("enable_streaming", False):
                assessment = ""
                for assessment in stream_text(assessment_prompt, temperature=0.7, max_tokens=max_toks):
                    state["current_argument_stream"] = f"{agent.name}: {assessment}"
                    _report_progress(state, "current_stream_text", f"{agent.name}: {assessment}")
            else:
                assessment = call_llm(assessment_prompt, temperature=0.7, max_tokens=max_toks)
            support_response = attack_response = assessment

            # Parse and tag arguments with agent information
            for line in support_response.split("\n"):
                clean_line = line.strip().lstrip('*#- ')
                if clean_line.startswith("Support") and ":" in clean_line:
                    arg_content = clean_line.split(":", 1)[1].replace("**", "").strip()
                    if arg_content:
                        tagged_content = f"[{agent.role.value}] {arg_content}"
                        arg = Argument(
                            content=tagged_content,
                            argument_type="support",
                            parent_option=option,
                        )
                        arg.agent_role = agent.role.value
                        arg.agent_name = agent.name
                        arguments.append(arg)
                        option_arguments.append(arg)

                        if agent.name not in agent_arguments_tracking:
                            agent_arguments_tracking[agent.name] = []
                        agent_arguments_tracking[agent.name].append(
                            {
                                "type": "support",
                                "content": arg_content,
                                "option": option,
                            }
                        )

            for line in attack_response.split("\n"):
                clean_line = line.strip().lstrip('*#- ')
                if clean_line.startswith(("Challenge", "Attack", "Concern")):
                    if ":" in clean_line:
                        arg_content = clean_line.split(":", 1)[1].replace("**", "").strip()
                    else:
                        arg_content = re.sub(r"^(Challenge|Attack|Concern)", "", clean_line).replace("**", "").strip()
                    if arg_content:
                        tagged_content = f"[{agent.role.value}] {arg_content}"
                        arg = Argument(
                            content=tagged_content,
                            argument_type="attack",
                            parent_option=option,
                        )
                        arg.agent_role = agent.role.value
                        arg.agent_name = agent.name
                        arguments.append(arg)
                        option_arguments.append(arg)

                        if agent.name not in agent_arguments_tracking:
                            agent_arguments_tracking[agent.name] = []
                        agent_arguments_tracking[agent.name].append(
                            {"type": "attack", "content": arg_content, "option": option}
                        )

        print(
            f"Generated {len(option_arguments)} arguments from {len(healthcare_team)} agents"
        )

    # Store all the tracking information
    state["agent_arguments_tracking"] = agent_arguments_tracking
    state["healthcare_team"] = [
        {
            "name": agent.name,
            "role": agent.role.value,
            "expertise": agent.expertise_areas,
        }
        for agent in healthcare_team
    ]

    print(f"\nTotal arguments generated: {len(arguments)}")
    print(f"Arguments by agent:")
    for agent_name, agent_args in agent_arguments_tracking.items():
        print(f"  {agent_name}: {len(agent_args)} arguments")

    memory_arguments = _instantiate_memory_arguments(state, memory_records)
    arguments.extend(memory_arguments)
    source_ids = _source_ids(state)
    for arg in arguments:
        arg.content = _clean_citations(arg.content, source_ids)

    state["arguments"] = arguments
    ensure_argument_ids(state)
    service = get_memory_service()
    if service is not None and state.get("thread_id"):
        for arg in memory_arguments:
            service.log_usage(state["thread_id"], [arg.memory_id], "argument_cited", argument_id=arg.arg_id)
    state["current_step"] = "human_review"

    if "human_review_complete" not in state:
        state["human_review_complete"] = False

    return state


def _instantiate_memory_arguments(state: GraphState, records: List[Any]) -> List[Argument]:
    """Turn applicable long-term lessons into arguments the clinician can contest.

    Reused feedback enters the QBAF like any other argument: it is verified,
    weighed, shown with a "learned" badge, and if the clinician rejects it,
    that rejection becomes conflict evidence against the lesson."""
    if not MEMORY_INSTANTIATE_ARGUMENTS or not records:
        return []
    options = state["handling_options"]
    lessons = "\n".join(f"- {line}" for line in guidance_lines(records))
    option_lines = "\n".join(f"{option_id(i)}: {option}" for i, option in enumerate(options))
    if state.get("enable_streaming", False):
        _report_progress(state, "current_sub_step", "🧠 Checking which lessons from past clinician reviews apply...")
    prompt = f"""Lessons learned from earlier clinician reviews of other patients' care plans are listed below. Decide which lessons apply to this patient and these care options. For each lesson that clearly applies, write ONE argument for or against ONE option, adapted to this patient. Skip lessons that do not clearly apply.

Patient Information:
{clip_text(state['patient_info'], 1500)}

Care options:
{option_lines}

Lessons:
{lessons}

Return JSON only: {{"arguments": [{{"memory_id": "...", "option_id": "O1", "stance": "support or attack", "content": "one sentence"}}]}}"""
    data = call_llm_json(prompt, temperature=0.2, max_tokens=2048)
    rows = data.get("arguments") if isinstance(data, dict) else data if isinstance(data, list) else []
    valid_ids = {record.memory_id for record in records}
    arguments, used = [], set()
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        memory_id = str(row.get("memory_id") or "")
        stance = str(row.get("stance") or "").lower()
        option = resolve_option(options, row.get("option_id"))
        content = " ".join(str(row.get("content") or "").split())
        if memory_id not in valid_ids or memory_id in used or stance not in ("support", "attack") \
                or option is None or len(content) < 12:
            continue
        used.add(memory_id)
        arguments.append(Argument(
            content=f"[Learned from past reviews] {content}",
            argument_type=stance,
            parent_option=option,
            agent_role="Learned guidance",
            agent_name="Self-evolving memory",
            source="memory",
            memory_id=memory_id,
        ))
    print(f"Memory-derived arguments: {len(arguments)}")
    return arguments


def human_review(state: GraphState) -> GraphState:
    """Human-in-the-loop: Placeholder for Gradio interface"""
    # This node doesn't modify the state
    # The actual review happens in the Gradio interface
    return state


GROUP_VERIFICATION_ROLE = "verification panel for an interdisciplinary aging-in-place care plan"
DEFAULT_UNVERIFIED_VALIDITY = 0.6


def _argument_signature(arg: Argument, state: GraphState) -> str:
    """What one argument's verification depends on: its text, stance and target."""
    target = find_argument(state.get("arguments") or [], arg.target_arg_id)
    basis = "|".join([arg.content, arg.argument_type, target.content if target else ""])
    return hashlib.sha1(basis.encode()).hexdigest()[:16]


def _group_basis(option: str, state: GraphState, feedback_sig: str) -> str:
    """What every result in an option group depends on: the option, the patient and
    the clinician feedback in force."""
    patient = hashlib.sha1((state.get("patient_info") or "").encode()).hexdigest()
    return hashlib.sha1("|".join([option, patient, feedback_sig]).encode()).hexdigest()[:20]


def _normalize_relevance(value: Any) -> str:
    if isinstance(value, (int, float)):
        return "high" if value >= 0.7 else "moderate" if value >= 0.4 else "low"
    text = str(value or "").strip().lower()
    if text.startswith("high"):
        return "high"
    if text.startswith("low"):
        return "low"
    return "moderate"


def _unit_score(value: Any, default: float = DEFAULT_UNVERIFIED_VALIDITY) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return default


def _strip_role_tag(content: str) -> str:
    content = content or ""
    if content.startswith("[") and "]" in content[:60]:
        return content.split("]", 1)[1].strip()
    return content


def _option_evidence(state: GraphState, option: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Published evidence for one option: a literature search for the option, then the case's other
    sources, strongest evidence first. New sources become citable references of the case."""
    references = state.get("document_references")
    if references is None:
        references = state["document_references"] = []
    known = {literature.record_key(ref): ref for ref in references}
    found: List[Dict[str, Any]] = []
    for record in literature.search(f"older adults {option}"):
        ref = known.get(literature.record_key(record))
        if ref is None:
            ref = literature.as_reference(record, max((r["id"] for r in references), default=0) + 1)
            references.append(ref)
            known[literature.record_key(ref)] = ref
            state.setdefault("retrieved_documents", []).append(
                {"doc_id": ref["id"], "document": ref["full_content"], "search_query": ref.get("search_query")})
        if ref not in found:
            found.append(ref)
    for ref in sorted(references, key=lambda r: -(r.get("evidence_weight") or 0)):
        if len(found) >= limit:
            break
        if ref not in found:
            found.append(ref)
    return found[:limit]


def _option_cases(state: GraphState, vector_db: Any, option: str, limit: int = 3) -> List[str]:
    """Case records of other patients similar to this option and patient: background for the
    verification panel, never numbered, cited or shown."""
    query = f"elderly {option} {clip_text(state.get('patient_info', ''), 160)}"
    try:
        results = vector_db.search(query, n_results=limit)
    except Exception as exc:  # background only, never a reason to fail
        print(f"Case search failed for option: {exc}")
        results = []
    return [doc["document"] for doc in results if doc.get("document")]


def _group_prompt(state: GraphState, oid: str, option: str, group: List[Argument], evidence: List[Dict[str, Any]],
                  cases: List[str], context: str, patient_summary: str) -> str:
    def author(arg: Argument) -> str:
        if is_human_authored(arg):
            return "clinician"
        if arg.source == "memory":
            return "learned guidance"
        return arg.agent_role or "care team"

    rows = []
    for arg in group:
        stance = "support" if arg.argument_type == "support" else "challenge"
        target = f" (responds to {arg.target_arg_id})" if arg.target_arg_id else ""
        rows.append(f"{arg.arg_id} | {stance} | {author(arg)}{target} | {_strip_role_tag(arg.content)}")
    evidence_lines = "\n".join(
        f"[{ref['id']}] {ref.get('title', '')} ({_venue(ref)}): {clip_text(ref['full_content'], 500)}" for ref in evidence
    ) or "(no published sources were retrieved)"
    case_lines = ""
    if cases:
        case_lines = (f"\nSimilar case records (background only). {CASE_RECORDS_RULE}\n"
                      + "\n".join(f"- {clip_text(case, 400)}" for case in cases) + "\n")
    rows_text = "\n".join(rows)
    return f"""You are the {GROUP_VERIFICATION_ROLE}.
Verify all the arguments about ONE care option together, as a group: compare them with each other,
with the patient's situation and with the evidence, so that strong, patient-specific points count
for more than generic ones.

Patient: {patient_summary}
{context}
Care option {oid}: {option}

Evidence excerpts (published sources):
{evidence_lines}
{case_lines}
Arguments (id | stance | author | text):
{rows_text}

For EVERY argument give:
- validity: 0.0 to 1.0, how accurate and well grounded the claim is for this patient (clinical knowledge and the evidence above).
- relevance: "high" if it bears on this patient's main risks or stated goals, "moderate" if it matters but is secondary, "low" if it is generic or speculative for this patient.
- same_as: the id of an EARLIER argument in the list that makes the same point and adds nothing new; if it adds
  anything (a different reason, risk, action or discipline's angle), use null.
- refs: numbers of the published evidence excerpts it relies on, e.g. [1, 3], or [].
- note: one sentence explaining your judgement, without mentioning case records or other patients.
Then list rebuttals: when an argument directly answers an argument of the opposite stance (for example a
support showing that a concern is manageable for this patient), give
{{"from": "<id>", "to": "<id>", "strength": "full" or "partial", "reason": "<one sentence>"}}:
"full" if it resolves the point for this patient, "partial" if it only reduces it. Do not list an argument that
merely coexists with the other one.
Finally write a summary: two or three sentences on how well the arguments support this option for this patient
and what it depends on. Describe the balance; do not give a verdict such as "not recommended", since the weighing
and the clinician decide that.

Return JSON only, in this shape:
{{"arguments": [{{"id": "A1", "validity": 0.8, "relevance": "high", "same_as": null, "refs": [1], "note": "..."}}],
 "rebuttals": [{{"from": "A1", "to": "A2", "strength": "full", "reason": "..."}}],
 "summary": "..."}}"""


def _apply_group_result(group: List[Argument], result: Optional[Dict[str, Any]],
                        evidence: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Write a group verification onto its arguments and return the option's review."""
    result = result if isinstance(result, dict) else {}
    by_id = {
        str(item.get("id")).strip(): item
        for item in result.get("arguments") or []
        if isinstance(item, dict) and item.get("id") is not None
    }
    order = {arg.arg_id: index for index, arg in enumerate(group)}
    ref_ids = {ref["id"] for ref in evidence}
    missing = []
    for arg in group:
        item = by_id.get(arg.arg_id)
        arg.rebuts, arg.partly_rebuts = [], []
        if item is None:
            missing.append(arg.arg_id)
            arg.validity_score, arg.relevance, arg.same_as = DEFAULT_UNVERIFIED_VALIDITY, "moderate", None
            arg.supporting_docs = []
            arg.validation_note = "Not verified: the verification panel returned no result for this argument."
            arg.flags = ["unverified"]
            continue
        arg.validity_score = _unit_score(item.get("validity"))
        arg.relevance = _normalize_relevance(item.get("relevance"))
        same = str(item.get("same_as") or "").strip()
        arg.same_as = same if same in order and order[same] < order[arg.arg_id] else None
        arg.supporting_docs = [
            int(ref) for ref in item.get("refs") or [] if str(ref).strip().isdigit() and int(ref) in ref_ids
        ]
        arg.validation_note = clip_text(str(item.get("note") or "").strip(), 400) or None
        # The clinician stays the decision-maker, but a weak verification of their
        # argument is surfaced rather than hidden.
        arg.flags = ["verifier_disagrees"] if is_human_authored(arg) and arg.validity_score < 0.4 else []
    by_arg = {arg.arg_id: arg for arg in group}
    rebuttals = []
    for item in result.get("rebuttals") or []:
        if not isinstance(item, dict):
            continue
        source = by_arg.get(str(item.get("from") or "").strip())
        target = by_arg.get(str(item.get("to") or "").strip())
        if (source is None or target is None or source is target or source.argument_type == target.argument_type
                or target.arg_id in source.rebuts + source.partly_rebuts):
            continue
        partial = str(item.get("strength") or "").strip().lower().startswith("partial")
        (source.partly_rebuts if partial else source.rebuts).append(target.arg_id)
        rebuttals.append({"from": source.arg_id, "to": target.arg_id, "strength": "partial" if partial else "full",
                          "reason": clip_text(str(item.get("reason") or "").strip(), 300)})
    return {
        "summary": str(result.get("summary") or "").strip(),
        "rebuttals": rebuttals,
        "verified": bool(by_id),
        "unverified": missing,
    }


def _cache_group(group: List[Argument], state: GraphState, basis: str, review: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "basis": basis,
        "review": review,
        "args": {
            arg.arg_id: {
                "sig": _argument_signature(arg, state),
                "validity": arg.validity_score,
                "relevance": arg.relevance,
                "same_as": arg.same_as,
                "rebuts": list(arg.rebuts),
                "partly_rebuts": list(arg.partly_rebuts),
                "docs": list(arg.supporting_docs),
                "note": arg.validation_note,
                "flags": list(arg.flags),
            }
            for arg in group
        },
    }


def _reusable(cached: Optional[Dict[str, Any]], group: List[Argument], state: GraphState, basis: str) -> bool:
    """A group needs no new verification when nothing it depends on changed and every
    argument was verified as written; arguments may have been removed since."""
    if not cached or cached.get("basis") != basis:
        return False
    return all(
        arg.arg_id in cached["args"] and cached["args"][arg.arg_id]["sig"] == _argument_signature(arg, state)
        for arg in group
    )


def _reuse_group(cached: Dict[str, Any], group: List[Argument]) -> Dict[str, Any]:
    present = {arg.arg_id for arg in group}
    for arg in group:
        entry = cached["args"][arg.arg_id]
        arg.validity_score = entry["validity"]
        arg.relevance = entry["relevance"]
        # A repeat of a removed argument now carries the point itself.
        arg.same_as = entry["same_as"] if entry["same_as"] in present else None
        arg.rebuts = [target for target in entry["rebuts"] if target in present]
        arg.partly_rebuts = [target for target in entry.get("partly_rebuts", []) if target in present]
        arg.supporting_docs = list(entry["docs"])
        arg.validation_note = entry["note"]
        arg.flags = list(entry["flags"])
    review = dict(cached["review"])
    review["rebuttals"] = [
        item for item in review.get("rebuttals", []) if item["from"] in present and item["to"] in present
    ]
    return review


def _group_report(group: List[Argument], review: Dict[str, Any]) -> str:
    lines = []
    for arg in group:
        stance = "support" if arg.argument_type == "support" else "challenge"
        repeat = f", repeats {arg.same_as}" if arg.same_as else ""
        lines.append(f"{arg.arg_id} {stance}: validity {arg.validity_score:.2f}, {arg.relevance} relevance{repeat}")
    for item in review.get("rebuttals", []):
        verb = "partly answers" if item.get("strength") == "partial" else "answers"
        lines.append(f"{item['from']} {verb} {item['to']}: {item['reason']}")
    if review.get("summary"):
        lines.append(f"Panel: {review['summary']}")
    return "\n".join(lines)


def argument_validator(state: GraphState) -> GraphState:
    """Verify the arguments for each care option together, as a group.

    One call per option judges every argument's validity and its relevance to
    this patient, spots repeated points and finds the arguments that answer an
    opposing one, then summarises the option. Judging the arguments side by side
    is quicker than one call per argument and lets strong, patient-specific
    points outweigh generic ones in the QBAF.

    Results are cached per option on the patient, the clinician feedback in force
    and each argument as written: a contest that only removes or restores
    arguments re-verifies nothing, an edit or a new argument re-verifies its
    option's group, and new free-text feedback re-verifies every group."""
    print("🫡 Verifying arguments by option group...")
    ensure_argument_ids(state)
    options = state.get("handling_options") or []
    cache = state.get("validation_cache") or {}
    groups_cache = cache.setdefault("groups", {})
    history = state.get("feedback_history") or []
    feedback_sig = feedback_signature(history)
    context = ""
    if history:
        context += (
            "Clinician feedback on earlier versions of this care plan (the clinician knows the patient; "
            f"take it into account):\n{feedback_context(history)}\n"
        )
    context += _guidance_block(_memory_guidance(
        state, "argument_validation", f"{state.get('patient_info', '')} {' '.join(options)}",
    ))
    patient_summary = clip_text(state.get("patient_info", ""), 800)
    vector_db = MedicalVectorDB()
    active = active_arguments(state["arguments"])
    reviews: Dict[str, Dict[str, Any]] = {}
    verified_groups = reused_groups = 0
    streaming = state.get("enable_streaming", False)

    for index, option in enumerate(options):
        oid = option_id(index)
        group = [arg for arg in active if option_index(options, arg.parent_option) == index]
        if not group:
            reviews[oid] = {"summary": "", "rebuttals": [], "verified": False, "unverified": []}
            continue
        basis = _group_basis(option, state, feedback_sig)
        cached = groups_cache.get(option)
        label = f"Option {index + 1}/{len(options)}"
        if _reusable(cached, group, state, basis):
            reviews[oid] = _reuse_group(cached, group)
            reused_groups += 1
            if streaming:
                _report_progress(state, "validation_progress", f"{label}: verification reused")
                _report_progress(state, "current_sub_step",
                                 f"♻️ {label}: {len(group)} arguments unchanged since their last verification")
            continue

        if streaming:
            _report_progress(state, "validation_progress", f"{label}: verifying {len(group)} arguments together")
            _report_progress(state, "current_sub_step",
                             f"🧪 {label}: verifying {len(group)} arguments together against the evidence...")
        evidence = _option_evidence(state, option)
        cases = _option_cases(state, vector_db, option)
        prompt = _group_prompt(state, oid, option, group, evidence, cases, context, patient_summary)
        result = call_llm_json(prompt, temperature=0.2, max_tokens=max(1200, 180 * len(group) + 500))
        review = _apply_group_result(group, result, evidence)
        reviews[oid] = review
        groups_cache[option] = _cache_group(group, state, basis, review)
        verified_groups += 1
        if streaming:
            _report_progress(state, "current_stream_text", _group_report(group, review))
        print(f"{label}: {len(group)} arguments verified together; "
              f"{len(review['rebuttals'])} rebuttals; {len(review['unverified'])} without a result")

    state["validation_cache"] = cache
    state["option_reviews"] = reviews
    state["validated_arguments"] = active
    state["adaptive_retrieval_summary"] = {"groups_verified": verified_groups, "groups_reused": reused_groups}
    state["current_step"] = "qbaf_evaluation"
    if active:
        average = sum(arg.validity_score or 0.0 for arg in active) / len(active)
        relevance = {level: sum(1 for arg in active if arg.relevance == level) for level in ("high", "moderate", "low")}
        print(f"Verification: {verified_groups} option groups verified, {reused_groups} reused; "
              f"average validity {average:.2f}; relevance {relevance}")
    return state


def qbaf_evaluation(state: GraphState) -> GraphState:
    """Weigh the verified arguments in the QBAF (quadratic energy semantics)."""
    if state.get("enable_streaming", False):
        _report_progress(state, "current_sub_step", "⚖️ Weighing the verified arguments in the argumentation framework...")
    state["qbaf"] = evaluate_qbaf(state["handling_options"], state["arguments"])
    reviews = state.get("option_reviews") or {}
    for row in state["qbaf"]["options"]:
        row["review"] = (reviews.get(row["option_id"]) or {}).get("summary") or None
    summary = "; ".join(
        f"{row['option_id']} {row['strength']:.2f} ({row['tier_label']})" for row in state["qbaf"]["options"]
    )
    print(f"QBAF evaluated: {summary}")
    if state.get("enable_streaming", False):
        _report_progress(state, "current_stream_text", qbaf_prompt_summary(state["qbaf"]))
    state["current_step"] = "revision_planning"
    return state


def _section_titles(sections: List[Dict[str, str]]) -> Dict[str, str]:
    return {section["id"]: section["title"] for section in sections} or dict(SECTION_TITLES)


def revision_planning(state: GraphState) -> GraphState:
    """Reason about the best way to update the care plan after the clinician's contestation."""
    versions = state.get("care_plan_versions") or []
    if not versions:
        state["revision_plan"] = {
            "strategy": "initial",
            "strategy_label": STRATEGY_LABELS["initial"],
            "sections": list(SECTION_IDS),
            "rationale": "First version of the care plan, written from the verified and weighed arguments.",
            "decided_by": "rules",
        }
        return state
    previous = versions[-1]
    delta = qbaf_delta(previous.get("qbaf_snapshot"), state["qbaf"])
    recent_ops = ops_since(state, previous.get("ops_cursor", 0))
    if state.get("enable_streaming", False):
        _report_progress(state, "current_sub_step", "🧭 Reasoning about the best way to update the care plan...")
    plan = plan_revision_strategy(
        state, delta, recent_ops, state.get("plan_feedback") or [], _section_titles(previous.get("sections") or [])
    )
    plan["delta"] = delta
    state["revision_plan"] = plan
    print(f"Revision strategy: {plan['strategy']} ({plan['decided_by']}) sections={plan['sections']}")
    if state.get("enable_streaming", False):
        _report_progress(state, "current_stream_text", f"{plan['strategy_label']}: {plan['rationale']}")
    state["current_step"] = "plan_revision"
    return state


def _care_team_line(state: GraphState) -> str:
    return ", ".join(member.get("name") or member.get("role", "") for member in state.get("healthcare_team") or []) or "Not assigned"


def _feedback_and_directives(state: GraphState, items: List[Dict[str, Any]],
                             directives: List[Dict[str, Any]], titles: Dict[str, str]) -> str:
    text = ""
    if items:
        text += "\nClinician feedback to address:\n" + "\n".join(f"- {describe_item(item, titles)}" for item in items) + "\n"
    if directives:
        text += "\nInstructions from the clinician for the writer:\n" + "\n".join(f"- {d['content']}" for d in directives) + "\n"
    return text


def _full_plan_prompt(state: GraphState, qbaf: Dict[str, Any], memory_section: str, initial: bool) -> str:
    history = state.get("feedback_history") or []
    directives = state.get("writer_directives") or []
    context = _knowledge_context(state, **(FULL_CONTEXT if initial else COMPACT_CONTEXT))
    feedback_text = _feedback_and_directives(state, history, directives, dict(SECTION_TITLES))
    return f"""You are an expert geriatric care planner. Based on the weighed arguments and the medical knowledge provided,
    write a professional, evidence-based care plan for this older adult, who wishes to age in place.

    IMPORTANT: When you use the published evidence provided, cite it as [REF-X]. The similar case records describe
    other patients: use them only as background, never cite, quote or describe them, and never mention them.

    {context}

    Patient Information:
    {state['patient_info']}

    Severity: {state.get('severity')}
    Care team: {_care_team_line(state)}

    Argument evaluation (quantitative bipolar argumentation framework). Each option's strength (0-1) combines the
    verified validity of its supporting and challenging arguments, and its assessment follows from that strength:
{qbaf_prompt_summary(qbaf, max_drivers=4)}
    {feedback_text}{memory_section}
    Requirements:
    - Write up as interventions only the options in the plan, ordered by assessment: "Recommended", "Recommended
      with conditions" (state the conditions) and "Clinical judgment required" (say what the clinician should weigh).
    - Options assessed "Set aside" are not part of this plan: do not write them up as interventions and never
      describe any option as "not recommended".
    - Justify each recommendation with the strongest supporting and challenging arguments above, and cite the published
      evidence as [REF-X] only where it is relevant. Never invent references and never refer to other patients.
    - Address every clinician feedback item and instruction listed above.
    - Write for the care team and the patient's family: precise, concise and professional.
    - DO NOT use any emoji, icons, or special symbols anywhere in your response. Use plain text and markdown only.

    {section_template_prompt()}"""


def _presentation_prompt(state: GraphState, previous: Dict[str, Any], memory_section: str) -> str:
    directives = state.get("writer_directives") or []
    instructions = "\n".join(f"- {d['content']}" for d in directives) or "- Improve clarity and professional tone."
    return f"""Rewrite the presentation of this aging-in-place care plan following the clinician's instructions.
    Do not change its clinical content: keep every recommendation, assessment, responsibility, timeline and [REF-X] citation.

    Instructions from the clinician:
{instructions}
    {memory_section}
    Current care plan:
{sections_to_markdown(previous.get('sections') or [])}

    DO NOT use any emoji, icons, or special symbols anywhere in your response.

    {section_template_prompt()}"""


def _section_prompt(state: GraphState, section: Dict[str, str], guidance: str, qbaf: Dict[str, Any],
                    recent_ops: List[Dict[str, Any]], items: List[Dict[str, Any]],
                    directives: List[Dict[str, Any]], titles: Dict[str, str], memory_section: str) -> str:
    changes = "\n".join(describe_ops(recent_ops)) or "- none"
    return f"""You are revising one section of an existing aging-in-place care plan after the clinician contested it.
Rewrite ONLY the section "{section['title']}". Keep what is still correct, and change what the clinician's feedback
and the re-weighed arguments require. Section format: {guidance}

Patient Information:
{clip_text(state['patient_info'], 1500)}

Argument evaluation after the clinician's changes:
{qbaf_prompt_summary(qbaf, max_drivers=3)}

Changes to the arguments since the previous version:
{changes}
{_feedback_and_directives(state, items, directives, titles)}{memory_section}
{_knowledge_context(state, **COMPACT_CONTEXT)}
Cite the published evidence as [REF-X] only where it is used; never invent references and never refer to other
patients or their records.

Current text of the section:
<<<
{section['content']}
>>>

Return only the revised section body in markdown, without the section heading.
DO NOT use any emoji, icons, or special symbols."""


def _revise_sections(state: GraphState, previous: Dict[str, Any], plan: Dict[str, Any], qbaf: Dict[str, Any],
                     recent_ops: List[Dict[str, Any]], memory_section: str, max_tokens: int) -> List[Dict[str, str]]:
    """Targeted revision: rewrite only the planned sections and keep the rest verbatim."""
    sections = previous.get("sections") or []
    titles = _section_titles(sections)
    items = state.get("plan_feedback") or []
    directives = state.get("writer_directives") or []
    guidance_by_id = {section["id"]: section["guidance"] for section in PLAN_SECTIONS}
    rewritten = {}
    for section_id in plan["sections"]:
        section = next((row for row in sections if row["id"] == section_id),
                       {"id": section_id, "title": titles.get(section_id, SECTION_TITLES.get(section_id, section_id)), "content": ""})
        if state.get("enable_streaming", False):
            _report_progress(state, "current_sub_step", f"✏️ Revising section: {section['title']}")
        prompt = _section_prompt(
            state, section, guidance_by_id.get(section_id, "Keep the section's existing format."), qbaf, recent_ops,
            [item for item in items if item.get("section_id") in (None, section_id)],
            [d for d in directives if not d.get("section_ids") or section_id in d["section_ids"]],
            titles, memory_section,
        )
        body = strip_section_heading(_stream_llm(state, prompt, 0.5, max_tokens), section_id)
        if body:
            rewritten[section_id] = body
    return merge_sections(sections, rewritten)


def _write_document(state: GraphState, prompt: str, temperature: float, max_tokens: int) -> List[Dict[str, str]]:
    """Write the whole plan, retrying once if the writer ignored the section template."""
    sections = parse_sections(_stream_llm(state, prompt, temperature, max_tokens))
    if len(sections) < 3:
        print(f"Plan writer returned {len(sections)} section(s); retrying with the template reminder")
        reminder = ("\n\nIMPORTANT: a previous answer did not follow the required structure. Use exactly the "
                    "level-2 (##) headings listed above, in that order.")
        retry = parse_sections(_stream_llm(state, prompt + reminder, temperature, max_tokens))
        if len(retry) > len(sections):
            sections = retry
    return sections


def _memory_used(state: GraphState) -> List[Dict[str, Any]]:
    used: Dict[str, Dict[str, Any]] = {}
    for stage, records in (state.get("memory_guidance") or {}).items():
        for record in records:
            used.setdefault(record["memory_id"], {**record, "stages": []})["stages"].append(stage)
    for arg in active_arguments(state.get("arguments") or []):
        if arg.source == "memory" and arg.memory_id:
            entry = used.setdefault(arg.memory_id, {"memory_id": arg.memory_id, "stages": []})
            entry.setdefault("argument_ids", []).append(arg.arg_id)
    return list(used.values())


def care_plan_reviser(state: GraphState) -> GraphState:
    """LLM: Write or revise the care plan from the weighed arguments, following the revision strategy"""
    versions = state.get("care_plan_versions") or []
    previous = versions[-1] if versions else None
    qbaf = state.get("qbaf") or evaluate_qbaf(state["handling_options"], state["arguments"])
    plan = state.get("revision_plan") or {}
    strategy = plan.get("strategy", "initial") if previous else "initial"
    recent_ops = ops_since(state, previous.get("ops_cursor", 0)) if previous else []

    if state.get("enable_streaming", False):
        _report_progress(state, "current_sub_step", "📊 Organizing validated arguments by evidence strength...")
    memory_section = _guidance_block(_memory_guidance(
        state, "plan_writing", f"{state['patient_info']} {' '.join(state['handling_options'])}"
    ))

    cp_toks = get_max_tokens_for_severity(2048, state["severity"])
    if state.get("enable_streaming", False) and strategy != "targeted_revision":
        label = "Drafting" if strategy in ("initial", "full_regeneration") else "Restyling"
        _report_progress(state, "current_sub_step", f"✍️ {label} the care plan document...")

    if strategy == "targeted_revision":
        sections = _revise_sections(state, previous, plan, qbaf, recent_ops, memory_section, cp_toks)
    elif strategy == "presentation_rewrite":
        sections = _write_document(state, _presentation_prompt(state, previous, memory_section), 0.4, cp_toks)
    else:
        prompt = _full_plan_prompt(state, qbaf, memory_section, initial=previous is None)
        sections = _write_document(state, prompt, 0.6, cp_toks)

    rationale = plan.get("rationale") or "First version of the care plan, written from the verified and weighed arguments."
    if not sections:
        if previous:
            sections = previous["sections"]
            rationale += " The writer returned no text, so the previous version was kept."
        else:
            sections = [{"id": "summary", "title": SECTION_TITLES["summary"],
                         "content": "The care plan could not be generated. Please regenerate it."}]

    source_ids = _source_ids(state)
    sections = [{**section, "content": _clean_citations(section.get("content", ""), source_ids)} for section in sections]
    response = sections_to_markdown(sections)
    # The decision table shows the option names and their leading arguments, so their citations count too.
    shown = [response] + [
        f"{row['option']} {' '.join(d.get('content', '') for d in row.get('top_supports', [])[:1] + row.get('top_attacks', [])[:1])}"
        for row in qbaf.get("options", [])
    ]
    cited_doc_ids = {int(ref) for text in shown for ref in re.findall(r"\[REF-(\d+)\]", text)} & source_ids

    # Update document references with usage information
    if "document_references" in state:
        for ref in state["document_references"]:
            if ref["id"] in cited_doc_ids:
                ref["used_in"].append("final_care_plan")
                state["cited_documents"].add(ref["id"])

    # Calculate decision confidence from the QBAF (falls back to validity balance without options)
    decision_confidence = qbaf["decision_confidence"] if qbaf.get("options") else calculate_decision_confidence(state["validated_arguments"])

    # Create formatted references section
    references_text = _format_references(state, cited_doc_ids)

    changed = changed_section_ids(previous["sections"], sections) if previous else [section["id"] for section in sections]
    titles = _section_titles(sections)
    feedback_ops = (state.get("feedback_ops") or []) if state.get("run_mode") == "feedback" else []
    if previous is None:
        change_summary = "First version."
    else:
        change_summary = (f"{STRATEGY_LABELS[strategy]}: "
                          + (f"updated {', '.join(titles.get(sid, sid) for sid in changed)}." if changed else "no section text changed.")
                          + (f" {len(recent_ops)} change(s) to the argument graph." if recent_ops else ""))
    active = active_arguments(state["arguments"])
    version = {
        "version": len(versions) + 1,
        "created_at": now_iso(),
        "status": "draft",
        "approved_at": None,
        "strategy": strategy,
        "strategy_label": STRATEGY_LABELS[strategy],
        "rationale": rationale,
        "decided_by": plan.get("decided_by", "rules"),
        "changed_sections": changed,
        "change_summary": change_summary,
        "feedback_applied": list(state.get("plan_feedback") or []) if state.get("run_mode") == "feedback" else [],
        "feedback_ops": [describe_feedback_op(op) for op in feedback_ops],
        "contested_ops": describe_ops(recent_ops),
        "sections": sections,
        "recommendations": response,
        "decision_confidence": decision_confidence,
        "options": qbaf.get("options", []),
        "qbaf_snapshot": {"options": [
            {key: row[key] for key in ("option_id", "option", "strength", "tier", "tier_label", "rank")}
            for row in qbaf.get("options", [])
        ]},
        "argument_summary": summarize_arguments(state["validated_arguments"]),
        "references": references_text,
        "reference_list": reference_list(state.get("document_references") or [], cited_doc_ids),
        "cited_document_ids": list(cited_doc_ids),
        "total_documents_retrieved": len(state.get("document_references") or []),
        "documents_cited": len(cited_doc_ids),
        "patient_info": state["patient_info"],
        "severity": state.get("severity"),
        "care_team": [{"name": m.get("name"), "role": m.get("role")} for m in state.get("healthcare_team") or []],
        "memory_used": _memory_used(state),
        "provenance": {
            "arguments_considered": len(active),
            "clinician_changes": len(net_human_ops(state)),
            "feedback_items": len(state.get("feedback_history") or []),
        },
        "ops_cursor": len(state.get("human_ops_log") or []),
        "scheduling": previous.get("scheduling") if previous else None,
    }
    state["care_plan_versions"] = versions + [version]
    state["revised_care_plan"] = version
    state["current_step"] = "plan_ready"

    print(f"Care plan v{version['version']} ({strategy}). Decision confidence: {decision_confidence}")
    print(
        f"Published sources cited: {len(cited_doc_ids)} out of {len(state.get('document_references') or [])} retrieved"
    )

    return state


def _format_references(state: GraphState, cited_doc_ids: Set[int]) -> str:
    """The plan's references as text: the published sources it cites, never case records."""
    cited = sorted((ref for ref in state.get("document_references") or [] if ref["id"] in cited_doc_ids),
                   key=lambda ref: ref["id"])
    if not cited:
        return "No published sources cited."
    return "\n".join(
        f"[REF-{ref['id']}] {ref.get('citation') or ref.get('title', '')}" + (f" {ref['url']}" if ref.get("url") else "")
        for ref in cited
    )


def route_after_human_review(state: GraphState) -> str:
    """Route based on whether human review is complete"""
    if state.get("human_review_complete", False):
        return "argument_validation"
    else:
        return "human_review"


def route_entry(state: GraphState) -> str:
    """Start a new case, or re-enter after the plan exists to apply the clinician's contestation."""
    mode = state.get("run_mode") or "generate"
    if mode == "feedback":
        return "feedback_integration"
    if mode == "contest":
        return "argument_validation"
    return "rag_retrieval"


def route_after_plan_revision(state: GraphState) -> str:
    # The care team (and so its availability) only changes when a new case starts.
    return "scheduling" if (state.get("run_mode") or "generate") == "generate" else "memory_reflection"


def feedback_integration(state: GraphState) -> GraphState:
    """Formulate the clinician's free-text plan feedback as operations on the QBAF."""
    history = state.get("feedback_history") or []
    versions = state.get("care_plan_versions") or []
    titles = _section_titles(versions[-1]["sections"]) if versions else dict(SECTION_TITLES)
    items = normalize_feedback_items(state.get("plan_feedback"), len(history), titles)
    if state.get("enable_streaming", False):
        _report_progress(state, "current_sub_step",
            f"🗣️ Interpreting {len(items)} feedback item(s) as changes to the argument graph...")
    ops = interpret_feedback(state, items, titles)
    applied = apply_feedback_ops(state, ops, items)
    state["plan_feedback"] = items
    state["feedback_history"] = history + items
    state["feedback_ops"] = applied
    lines = [describe_feedback_op(op) for op in applied]
    print("Feedback operations:\n" + "\n".join(lines))
    if state.get("enable_streaming", False):
        _report_progress(state, "current_stream_text", "\n".join(lines) or "No operations derived.")
    state["current_step"] = "argument_validation"
    return state


def memory_reflection(state: GraphState) -> GraphState:
    """Self-evolving memory: learn from the clinician's contestations of this case.

    Only new contestations are reflected on. The learning itself runs in the
    memory service's background worker, so it never delays the next
    contestation, and a memory failure never affects the care plan."""
    service = get_memory_service()
    ops = net_human_ops(state)
    signature = hashlib.sha1(json.dumps(ops, sort_keys=True, default=str).encode()).hexdigest()[:16]
    if service is None or not ops or signature == state.get("reflected_ops_signature"):
        return state
    if state.get("enable_streaming", False):
        _report_progress(state, "current_sub_step", "🧠 Queuing your contestations for memory consolidation...")
    qbaf = state.get("qbaf") or {}
    case = {
        "case_id": state.get("thread_id") or "unknown",
        "fingerprint": case_fingerprint(state.get("patient_info", "")),
        "profile_tags": profile_tags(state.get("patient_info", ""), state.get("patient_analysis"), state.get("severity")),
        "options": [
            {"option_id": row["option_id"], "option": row["option"], "tier_label": row["tier_label"]}
            for row in qbaf.get("options", [])
        ],
        "ops": ops,
        "feedback": state.get("feedback_history") or [],
        "ops_signature": signature,
    }
    try:
        summary = service.reflect_in_background(case)
    except Exception as e:
        print(f"[memory] reflection could not be queued: {e}")
        summary = {"status": "failed", "error": str(e)}
    state["memory_reflection"] = summary
    state["reflected_ops_signature"] = signature
    return state


def summarize_arguments(arguments: List[Argument]) -> Dict:
    """Summarize argument statistics"""
    summary = {
        "total_arguments": len(arguments),
        "support_arguments": len(
            [a for a in arguments if a.argument_type == "support"]
        ),
        "attack_arguments": len([a for a in arguments if a.argument_type == "attack"]),
        "avg_validity": (
            sum(a.validity_score for a in arguments) / len(arguments)
            if arguments
            else 0
        ),
    }
    return summary


def rag_retrieval(state: GraphState) -> GraphState:
    """Agentic RAG: published literature the plan may cite, and similar case records of other
    patients that inform generation as background but are never cited or shown."""
    vector_db = MedicalVectorDB()
    prompt = f"""Based on this ELDERLY patient information, generate 3-5 specific search queries 
        to retrieve relevant medical knowledge for GERIATRIC care planning (patients age 65+ ONLY).

        IMPORTANT: Add elderly-specific terms to EVERY query like:
        - "elderly" or "geriatric" or "senior" or "older adult"
        - OR specific ages: "age 70", "age 80", "over 65", etc.

        Patient Info: {state['patient_info']}

        Generate queries about:
        - ELDERLY patients with similar conditions
        - GERIATRIC care strategies for symptoms
        - Safety for OLDER ADULTS (65+)
        ...

        Example queries:
        - "elderly patient 75 years diabetes management"
        - "geriatric fall prevention age 80+"
        """

    if state.get("enable_streaming", False):
        queries_text = ""
        for queries_text in stream_text(prompt, temperature=0.3):
            _report_progress(state, "rag_progress", f"Generating search queries:\n{queries_text}")
        queries = queries_text.strip().split("\n")
    else:
        queries = call_llm(prompt, temperature=0.3).strip().split("\n")

    state["search_queries"] = queries

    # Case records of other patients: background for generation only. They are never
    # numbered, cited, listed as references or sent to the browser.
    cases, seen = [], set()
    for query in queries[:5]:
        if not query.strip():
            continue
        for doc in vector_db.search(query.strip(), n_results=3):
            text = doc.get("document") or ""
            if text and text not in seen:
                seen.add(text)
                cases.append({"document": text, "similarity_score": doc.get("similarity_score") or 0.0,
                              "search_query": query.strip()})
    cases.sort(key=lambda case: -case["similarity_score"])
    state["similar_cases"] = cases[:MAX_SIMILAR_CASES]

    # Published literature: the only sources a care plan cites.
    if state.get("enable_streaming", False):
        _report_progress(state, "current_sub_step", "📚 Searching the published literature for citable evidence...")
    records = literature.search_many(queries)
    references = [literature.as_reference(record, ref_id) for ref_id, record in enumerate(records, 1)]
    state["document_references"] = references
    state["retrieved_documents"] = [
        {"doc_id": ref["id"], "document": ref["full_content"], "search_query": ref.get("search_query")}
        for ref in references
    ]
    state["cited_documents"] = set()
    state["rag_context"] = _knowledge_context(state, **FULL_CONTEXT)
    if state.get("enable_streaming", False):
        found = f"{len(references)} published source{'' if len(references) == 1 else 's'} found" if references \
            else "No published sources found (the plan will carry no references)"
        _report_progress(state, "current_sub_step", f"📚 {found}; similar case records inform the plan as background only")
    print(f"Retrieved {len(references)} published sources and {len(state['similar_cases'])} similar case records "
          "(background only, never cited)")

    return state


def scheduling(state: Dict[str, Any]) -> Dict[str, Any]:
    team = state.get("healthcare_team", []) or []
    slots_by_provider: Dict[str, List[Dict[str, Any]]] = {}

    for member in team:
        provider_name = (
            member.get("name") or member.get("agent_name") or member.get("role")
        )
        if not provider_name:
            continue
        try:
            slots = _fetch_available_slots_for_roles(provider_name)
        except Exception as e:
            print(f"[scheduling] MCP call failed for {provider_name}: {e}")
            slots = []
        slots_by_provider[provider_name] = slots

    if not any(slots_by_provider.values()):
        summary = "No provider availability was found."
    else:
        try:
            summary_prompt = (
                "You are a concise scheduling assistant.\n"
                "Given the provider availability (JSON), produce a brief bullet list with provider name and the first 2 upcoming slots only.\n"
                "Use a friendly, neutral tone. Do NOT invent times.\n\n"
                f"AVAILABILITY JSON:\n{slots_by_provider}\n"
            )
            summary = call_llm(summary_prompt, temperature=0.2, max_tokens=180)
        except Exception:
            summary = (
                "Availability found. See the table below for each provider’s next slots."
            )

    state["scheduling_slots"] = slots_by_provider
    state["scheduling_summary"] = summary.strip()
    if state.get("care_plan_versions"):
        state["care_plan_versions"][-1]["scheduling"] = {"summary": state["scheduling_summary"], "slots": slots_by_provider}
        state["revised_care_plan"] = state["care_plan_versions"][-1]
    state["current_step"] = "scheduling"
    return state
