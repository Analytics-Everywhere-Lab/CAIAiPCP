import hashlib
import json
from typing import Any, Dict, List, Optional, Set
from mcp_utils import _fetch_available_slots_for_roles
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


def _compact_rag_context(state: GraphState, max_docs: int = 8, max_chars: int = 600) -> str:
    """Retrieved documents truncated for revision prompts, which only need enough to cite."""
    documents = state.get("retrieved_documents") or []
    if not documents:
        return ""
    lines = ["RELEVANT MEDICAL DOCUMENTS (excerpts):"]
    for doc in documents[:max_docs]:
        lines.append(f"[REF-{doc['doc_id']}] {clip_text(doc['document'], max_chars)}")
    return "\n".join(lines)

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
    
    Focus on practical, implementable options that support independent living while ensuring safety and quality of life."""

    max_toks = get_max_tokens_for_severity(2048, state["severity"])
    if state.get("enable_streaming", False):
        response = ""
        for response in stream_text(prompt, temperature=0.6, max_tokens=max_toks):
            _report_progress(state, "options_generation_progress", response)
            _report_progress(state, "current_stream_text", response)
    else:
        response = call_llm(prompt, temperature=0.6, max_tokens=max_toks)

    # Parse handling options
    options = []
    for line in response.split("\n"):
        clean_line = line.strip().lstrip('*#- ')
        if clean_line.startswith("Option") or clean_line.startswith("**Option"):
            option_text = clean_line.split(":", 1)[1].strip() if ":" in clean_line else clean_line
            option_text = option_text.replace("**", "").strip()
            if option_text:
                options.append(option_text)

    # Ensure we have at least one option
    if not options:
        print("Warning: No options parsed from LLM response. Using default options.")
        options = [
            "Home Safety Assessment and Modification",
            "Social Engagement and Support Groups",
            "Regular Health Monitoring and Care Coordination",
        ]

    state["handling_options"] = options
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

            # Agent-specific prompt for supporting arguments
            support_prompt = f"""{agent.get_perspective_prompt()}
            
                {rag_context}
                {memory_section}
                Patient Information:
                {patient_info}

                Care Option Being Evaluated:
                {option}

                From your professional perspective as a {agent.role.value}, provide 1-2 supporting arguments for this care option.
                Focus on aspects most relevant to your expertise: {', '.join(agent.expertise_areas[:3])}

                Format each argument on a new line starting with "Support:"
                Be specific about benefits from your professional viewpoint."""

            max_toks = get_max_tokens_for_severity(1024, state["severity"])
            if state.get("enable_streaming", False):
                support_response = ""
                for support_response in stream_text(support_prompt, temperature=0.7, max_tokens=max_toks):
                    state["current_argument_stream"] = f"{agent.name}: {support_response}"
                    _report_progress(state, "current_stream_text", f"{agent.name}: {support_response}")
            else:
                support_response = call_llm(support_prompt, temperature=0.7, max_tokens=max_toks)

            # Agent-specific prompt for challenging arguments
            attack_prompt = f"""{agent.get_perspective_prompt()}
                {memory_section}
                Patient Information:
                {patient_info}

                Care Option Being Evaluated:
                {option}

                From your professional perspective as a {agent.role.value}, provide 1-2 concerns or challenges about this care option.
                Focus on risks or limitations most relevant to your expertise: {', '.join(agent.focus_priorities[:3])}

                Format each argument on a new line starting with "Challenge:"
                Be specific about concerns from your professional viewpoint."""

            if state.get("enable_streaming", False):
                attack_response = ""
                for attack_response in stream_text(attack_prompt, temperature=0.7, max_tokens=max_toks):
                    state["current_argument_stream"] = f"{agent.name}: {attack_response}"
                    _report_progress(state, "current_stream_text", f"{agent.name}: {attack_response}")
            else:
                attack_response = call_llm(attack_prompt, temperature=0.7, max_tokens=max_toks)

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
                if clean_line.startswith("Challenge") or clean_line.startswith("Attack"):
                    if ":" in clean_line:
                        arg_content = clean_line.split(":", 1)[1].replace("**", "").strip()
                    else:
                        arg_content = clean_line.replace("Challenge", "").replace("Attack", "").replace("**", "").strip()
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


def _validation_key(arg: Argument, state: GraphState, feedback_sig: str) -> str:
    """Cache key for a verification result: the argument as written, what it targets,
    the patient, and the clinician feedback in force when it was verified."""
    target = find_argument(state.get("arguments") or [], arg.target_arg_id)
    basis = "|".join([
        arg.content, arg.argument_type, arg.parent_option or "", target.content if target else "",
        hashlib.sha1((state.get("patient_info") or "").encode()).hexdigest(), feedback_sig,
    ])
    return hashlib.sha1(basis.encode()).hexdigest()[:20]


def _explanation(response: str, marker: str) -> str:
    """The verifier's explanation without its score line."""
    text = re.sub(rf"(?i)\**\s*{marker}\s*:?\s*\**\s*[0-9.]+\s*\**", " ", response or "")
    return clip_text(text.replace("**", ""), 280)


def argument_validator(state: GraphState) -> GraphState:
    """Third LLM: Validate arguments with option to retrieve more evidence.

    Every active argument is (re-)verified against the patient and the
    clinician's cumulative feedback. Results are cached on the argument and the
    feedback in force, so a contest that only edits the argument table
    re-verifies just the changed arguments, while new free-text feedback
    re-verifies all of them."""
    print("🫡 Validating arguments...")
    ensure_argument_ids(state)
    validated_arguments = []
    vector_db = MedicalVectorDB()
    cache = state.get("validation_cache") or {}
    history = state.get("feedback_history") or []
    feedback_sig = feedback_signature(history)
    feedback_section = ""
    if history:
        feedback_section = (
            "\n            Clinician feedback on earlier versions of this care plan (the clinician knows the "
            f"patient; take it into account):\n{feedback_context(history)}\n"
        )
    memory_section = _guidance_block(_memory_guidance(
        state, "argument_validation",
        f"{state.get('patient_info', '')} {' '.join(state.get('handling_options') or [])}",
    ))
    patient_summary = clip_text(state.get("patient_info", ""), 800)

    # Track which arguments needed additional evidence
    arguments_with_additional_evidence = []
    active = active_arguments(state["arguments"])
    total_args = len(active)
    reused = 0

    for i, arg in enumerate(active):
        key = _validation_key(arg, state, feedback_sig)
        cached = cache.get(key)
        if cached is not None:
            arg.validity_score = cached["score"]
            arg.validation_note = cached.get("note")
            arg.supporting_docs = cached.get("docs", [])
            arg.flags = list(cached.get("flags", []))
            reused += 1
            validated_arguments.append(arg)
            if state.get("enable_streaming", False):
                _report_progress(state, "validation_progress", f"Validating argument {i+1}/{total_args}")
                _report_progress(state, "current_sub_step",
                    f"♻️ Argument {i+1}/{total_args} ({arg.arg_id}): unchanged since its last verification — score {arg.validity_score:.2f} kept")
            continue

        if state.get("enable_streaming", False):
            _report_progress(state, "validation_progress", f"Validating argument {i+1}/{total_args}")
            _report_progress(state, "current_sub_step",
                f"✅ Argument {i+1}/{total_args} ({arg.arg_id}): evaluating factual accuracy & clinical relevance...")

        target = find_argument(state["arguments"], arg.target_arg_id)
        target_section = ""
        if target is not None:
            target_section = f"\n            This argument responds to another argument ({target.argument_type}): {target.content}\n"

        # First validation pass
        initial_prompt = f"""
            You are an expert analyst evaluating the validity and relevance of arguments 
            for elderly care planning.
            
            Patient Information (summary): {patient_summary}
            {feedback_section}{memory_section}
            Handling Option: {arg.parent_option}
            {target_section}
            Argument ({arg.argument_type}): {arg.content}
            
            Please evaluate this argument based on:
            1. Factual accuracy
            2. Relevance to elderly care and aging-in-place, and to this patient
            3. Practical considerations
            4. Evidence-based reasoning
            
            Provide a validity score between 0 and 1, where:
            - 0 = completely invalid/irrelevant
            - 0.5 = moderately valid
            - 1 = highly valid and relevant
            
            Response format: "Validity Score: X.XX"
            Include a brief explanation."""

        max_toks = get_max_tokens_for_severity(256, state["severity"])
        if state.get("enable_streaming", False):
            initial_response = ""
            for initial_response in stream_text(
                initial_prompt, temperature=0.3, max_tokens=max_toks
            ):
                state["current_validation_stream"] = initial_response
                _report_progress(state, "current_stream_text", initial_response)
        else:
            initial_response = call_llm(initial_prompt, temperature=0.3, max_tokens=max_toks)

        # Extract initial validity score
        initial_validity_score = 0.5  # default
        try:
            if "Validity Score:" in initial_response:
                score_text = initial_response.split("Validity Score:")[1].split()[0]
                initial_validity_score = float(score_text.strip().strip("*"))
                initial_validity_score = max(0, min(1, initial_validity_score))
        except:
            pass
        arg.validation_note = _explanation(initial_response, "Validity Score")

        # Check if we need additional evidence for weak arguments
        if initial_validity_score < 0.5:
            print(
                f"Low validity score ({initial_validity_score:.2f}) for argument. Retrieving additional evidence..."
            )

            # Generate intelligent search query for this specific argument
            search_query_prompt = f"""
                Generate a specific medical search query to find evidence about this elderly care argument:
                Option: {arg.parent_option}
                Argument Type: {arg.argument_type}
                Argument: {arg.content}       
                Create ONE focused search query that would help validate or refute this argument:"""

            sq_toks = get_max_tokens_for_severity(128, state["severity"])
            search_query = call_llm(
                search_query_prompt, temperature=0.2, max_tokens=sq_toks
            ).strip()

            # Retrieve additional evidence
            additional_docs = vector_db.search(search_query, n_results=3)

            if additional_docs:
                # Track which documents were used for this argument
                doc_refs_used = []

                # Format additional evidence
                additional_context = "\nADDITIONAL MEDICAL EVIDENCE:\n"
                for doc_index, doc in enumerate(additional_docs, 1):
                    additional_context += (
                        f"\n[Evidence {doc_index}] (Relevance: {doc['similarity_score']:.2f})\n"
                    )
                    additional_context += f"{doc['document'][:500]}...\n"

                    # Track this document usage
                    if "document_references" in state:
                        # Find matching reference
                        for ref in state["document_references"]:
                            if ref["full_content"] == doc["document"]:
                                ref["used_in"].append(
                                    f"validation_{arg.content[:30]}..."
                                )
                                doc_refs_used.append(ref["id"])
                                break

                # Store which docs supported this argument
                arg.supporting_docs = doc_refs_used

                # Re-validate with additional context
                revalidation_prompt = f"""You are an expert analyst. Re-evaluate this elderly care argument 
                with additional medical evidence.
                
                Handling Option: {arg.parent_option}
                
                Argument ({arg.argument_type}): {arg.content}
                
                Initial Assessment: The argument initially scored {initial_validity_score:.2f} in validity.
                
                {additional_context}
                
                Based on the additional evidence above, re-evaluate this argument considering:
                1. Whether the evidence supports or contradicts the argument
                2. The reliability and relevance of the evidence
                3. How this changes the practical validity of the argument
                
                Provide an updated validity score between 0 and 1.
                
                Response format: "Updated Validity Score: X.XX"
                Explain how the evidence influenced your assessment."""

                rv_toks = get_max_tokens_for_severity(512, state["severity"])
                if state.get("enable_streaming", False):
                    revalidation_response = ""
                    for revalidation_response in stream_text(
                        revalidation_prompt, temperature=0.3, max_tokens=rv_toks
                    ):
                        _report_progress(state, "current_stream_text", revalidation_response)
                else:
                    revalidation_response = call_llm(revalidation_prompt, temperature=0.3, max_tokens=rv_toks)

                # Extract updated validity score
                updated_validity_score = initial_validity_score  # fallback to initial
                try:
                    if "Updated Validity Score:" in revalidation_response:
                        score_text = revalidation_response.split(
                            "Updated Validity Score:"
                        )[1].split()[0]
                        updated_validity_score = float(score_text.strip().strip("*"))
                        updated_validity_score = max(0, min(1, updated_validity_score))
                    elif "Validity Score:" in revalidation_response:
                        score_text = revalidation_response.split("Validity Score:")[
                            1
                        ].split()[0]
                        updated_validity_score = float(score_text.strip().strip("*"))
                        updated_validity_score = max(0, min(1, updated_validity_score))
                except:
                    pass

                # Track that this argument had additional evidence retrieved
                arguments_with_additional_evidence.append(
                    {
                        "argument": arg.content,
                        "initial_score": initial_validity_score,
                        "updated_score": updated_validity_score,
                        "evidence_used": len(additional_docs),
                    }
                )

                arg.validity_score = updated_validity_score
                arg.validation_note = _explanation(revalidation_response, "Updated Validity Score") or arg.validation_note
                print(
                    f"  Score updated: {initial_validity_score:.2f} → {updated_validity_score:.2f}"
                )

            else:
                # No additional evidence found, keep initial score
                arg.validity_score = initial_validity_score
                print(
                    f"  No additional evidence found. Keeping score: {initial_validity_score:.2f}"
                )

        elif initial_validity_score >= 0.8:
            # High validity arguments - optionally verify with evidence
            print(
                f"High validity score ({initial_validity_score:.2f}). Checking for supporting evidence..."
            )

            # Quick verification search
            verification_query = f"{arg.parent_option} elderly care evidence"
            verification_docs = vector_db.search(verification_query, n_results=2)

            if verification_docs and verification_docs[0]["similarity_score"] > 0.7:
                # Found strong supporting evidence
                verification_context = f"\nSUPPORTING EVIDENCE (Relevance: {verification_docs[0]['similarity_score']:.2f}):\n"
                verification_context += f"{verification_docs[0]['document'][:300]}...\n"

                # Quick verification
                verification_prompt = f"""Quickly verify this highly-rated argument with supporting evidence:
                
                Argument: {arg.content}
                Current Score: {initial_validity_score:.2f}
                
                {verification_context}
                
                Does this evidence support the high validity score? 
                Response: "Confirmed Score: X.XX" (can be same or adjusted)"""

                vf_toks = get_max_tokens_for_severity(1280, state["severity"])
                if state.get("enable_streaming", False):
                    verification_response = ""
                    for verification_response in stream_text(
                        verification_prompt, temperature=0.2, max_tokens=vf_toks
                    ):
                        _report_progress(state, "current_stream_text", verification_response)
                else:
                    verification_response = call_llm(verification_prompt, temperature=0.2, max_tokens=vf_toks)

                # Extract confirmed score
                confirmed_score = initial_validity_score
                try:
                    if "Confirmed Score:" in verification_response:
                        score_text = verification_response.split("Confirmed Score:")[
                            1
                        ].split()[0]
                        confirmed_score = float(score_text.strip().strip("*"))
                        confirmed_score = max(0, min(1, confirmed_score))
                except:
                    pass

                arg.validity_score = confirmed_score
                if confirmed_score != initial_validity_score:
                    print(
                        f"  Score adjusted: {initial_validity_score:.2f} → {confirmed_score:.2f}"
                    )
            else:
                arg.validity_score = initial_validity_score

        else:
            # Moderate validity scores (0.5 - 0.8) - keep as is
            arg.validity_score = initial_validity_score
            print(
                f"Moderate validity score ({initial_validity_score:.2f}). No additional retrieval needed."
            )

        # The clinician stays the decision-maker, but a weak verification of their
        # argument is surfaced rather than hidden.
        arg.flags = ["verifier_disagrees"] if is_human_authored(arg) and arg.validity_score < 0.4 else []
        cache[key] = {"score": arg.validity_score, "note": arg.validation_note,
                      "docs": list(arg.supporting_docs), "flags": list(arg.flags)}
        validated_arguments.append(arg)

    state["validation_cache"] = cache
    print(f"Verification reused for {reused}/{total_args} unchanged arguments")

    # Add summary of adaptive retrieval to state
    if arguments_with_additional_evidence:
        adaptive_retrieval_summary = {
            "arguments_enhanced": len(arguments_with_additional_evidence),
            "average_score_improvement": sum(
                a["updated_score"] - a["initial_score"]
                for a in arguments_with_additional_evidence
            )
            / len(arguments_with_additional_evidence),
            "details": arguments_with_additional_evidence,
        }

        # Store in state for transparency
        state["adaptive_retrieval_summary"] = adaptive_retrieval_summary

        print(f"\nAdaptive Retrieval Summary:")
        print(
            f"  Arguments enhanced: {adaptive_retrieval_summary['arguments_enhanced']}"
        )
        print(
            f"  Avg score improvement: {adaptive_retrieval_summary['average_score_improvement']:.3f}"
        )

    state["validated_arguments"] = validated_arguments
    state["current_step"] = "qbaf_evaluation"

    # Log final statistics
    avg_validity = (
        sum(arg.validity_score for arg in validated_arguments)
        / len(validated_arguments)
        if validated_arguments
        else 0
    )
    print(f"\nValidation complete. Average validity: {avg_validity:.2f}")
    print(
        f"  High validity (>0.8): {sum(1 for arg in validated_arguments if arg.validity_score > 0.8)}"
    )
    print(
        f"  Moderate (0.5-0.8): {sum(1 for arg in validated_arguments if 0.5 <= arg.validity_score <= 0.8)}"
    )
    print(
        f"  Low validity (<0.5): {sum(1 for arg in validated_arguments if arg.validity_score < 0.5)}"
    )

    return state


def qbaf_evaluation(state: GraphState) -> GraphState:
    """Weigh the verified arguments in the QBAF (quadratic energy semantics)."""
    if state.get("enable_streaming", False):
        _report_progress(state, "current_sub_step", "⚖️ Weighing the verified arguments in the argumentation framework...")
    state["qbaf"] = evaluate_qbaf(state["handling_options"], state["arguments"])
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
    context = state.get("rag_context", "") if initial else _compact_rag_context(state)
    feedback_text = _feedback_and_directives(state, history, directives, dict(SECTION_TITLES))
    return f"""You are an expert geriatric care planner. Based on the weighed arguments and the medical knowledge provided,
    write a professional, evidence-based care plan for this older adult, who wishes to age in place.

    IMPORTANT: When using information from the medical knowledge provided, cite it using [REF-X] format.

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
    - Order the interventions by assessment. Recommend the options assessed "Recommended" or "Recommended with
      conditions"; for lower-assessed options, briefly explain why they are not recommended now and what would change that.
    - Justify each recommendation with the strongest supporting and challenging arguments above, and cite the medical
      knowledge as [REF-X] only where it is relevant. Never invent references.
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
{_compact_rag_context(state)}
Cite the medical knowledge as [REF-X] only where it is used; never invent references.

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

    response = sections_to_markdown(sections)
    cited_refs = re.findall(r"\[REF-(\d+)\]", response)
    cited_doc_ids = set(int(ref) for ref in cited_refs)

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
        "total_documents_retrieved": len(state.get("retrieved_documents", [])),
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
        f"Documents cited: {len(cited_doc_ids)} out of {len(state.get('retrieved_documents', []))} retrieved"
    )

    return state


def _format_references(state: GraphState, cited_doc_ids: Set[int]) -> str:
    """Format document references for display"""
    if not cited_doc_ids or len(state["document_references"]) == 0:
        return "No external references cited."

    references_text = "DOCUMENT REFERENCES:\n\n"

    # Sort by reference ID
    sorted_refs = sorted(
        [ref for ref in state["document_references"] if ref["id"] in cited_doc_ids],
        key=lambda x: x["id"],
    )

    for ref in sorted_refs:
        references_text += f"[REF-{ref['id']}]\n"
        references_text += f"  Search Query: {ref['search_query']}\n"
        references_text += f"  Relevance Score: {ref['similarity_score']:.2f}\n"

        # Add metadata if available
        if ref.get("metadata"):
            if "source" in ref["metadata"]:
                references_text += f"  Source: {ref['metadata']['source']}\n"
            if "title" in ref["metadata"]:
                references_text += f"  Title: {ref['metadata']['title']}\n"

        references_text += f"  Content Preview: {ref['content']}\n"
        references_text += "\n"

    return references_text


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
    """Agentic RAG: Retrieve relevant documents using RAG"""
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

    all_documents = []
    seen_docs = set()  # Avoid duplicates
    document_references = []

    doc_id = 1
    for query in queries[:5]:  # Limit to first 5 queries
        if query.strip():
            results = vector_db.search(query.strip(), n_results=3)
            for doc in results:
                doc_text = doc["document"]
                if doc_text not in seen_docs:
                    doc_with_id = doc.copy()
                    doc_with_id["doc_id"] = doc_id
                    doc_with_id["search_query"] = query.strip()
                    all_documents.append(doc_with_id)
                    seen_docs.add(doc_text)
                    reference = {
                        "id": doc_id,
                        "content": (
                            doc_text[:200] + "..." if len(doc_text) > 200 else doc_text
                        ),
                        "full_content": doc_text,
                        "similarity_score": doc["similarity_score"],
                        "metadata": doc.get("metadata", {}),
                        "search_query": query.strip(),
                        "used_in": [],  # Will track where this doc was used
                    }
                    document_references.append(reference)
                    doc_id += 1

    state["retrieved_documents"] = all_documents
    state["document_references"] = document_references
    state["cited_documents"] = set()

    rag_context = "RELEVANT MEDICAL DOCUMENTS:\n\n"
    for doc in all_documents[:10]:  # Limit context
        rag_context += (
            f"[REF-{doc['doc_id']}] (Relevance: {doc['similarity_score']:.2f})\n"
        )
        rag_context += f"{doc['document']}\n\n"

    state["rag_context"] = rag_context
    print(f"Retrieved {len(all_documents)} relevant documents with references")

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
