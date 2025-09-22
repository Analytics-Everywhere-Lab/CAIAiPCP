from typing import Any, Dict, List, Set
from mcp_utils import _fetch_available_slots_for_roles
from rag.vector_db import MedicalVectorDB
from state import Argument, GraphState
from llm_caller import call_llm, call_llm_stream
from utils import calculate_decision_confidence
from agent_selection import (
    get_agents_for_condition_llm,
    explain_team_selection,
    analyze_patient_needs,
)
import re


def care_plan_generator(state: GraphState) -> GraphState:
    """First LLM: Generate handling options based on patient information"""
    # Include RAG context if available
    context_section = ""
    if state.get("rag_context"):
        context_section = f"\n{state['rag_context']}\n"

    prompt = f"""You are an expert geriatric care planner. Based on the following patient information and relevant medical knowledge provided,
    generate 1-2 specific handling options for their care plan in aging-in-place context.

    {context_section}
    
    Patient Information:
    {state['patient_info']}
    
    Please provide handling options in the following format:
    Option 1: [Description]
    Option 2: [Description]
    ...
    
    Focus on practical, implementable options that support independent living while ensuring safety and quality of life."""

    if state.get("enable_streaming", False):
        response_chunks = []
        for chunk in call_llm_stream(prompt, temperature=0.6, max_tokens=1024):
            response_chunks.append(chunk)
            state["options_generation_progress"] = "".join(response_chunks)
        response = "".join(response_chunks)
    else:
        response = call_llm(prompt, temperature=0.6, max_tokens=1024)

    # Parse handling options
    options = []
    for line in response.split("\n"):
        if line.strip().startswith("Option"):
            option_text = line.split(":", 1)[1].strip() if ":" in line else line
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
            state["argument_generation_progress"] = (
                f"Generating arguments for option {i+1}/{len(state['handling_options'])}: {option[:50]}..."
            )

        # Generate supporting arguments
        support_prompt = f"""
            Generate 2 strong supporting arguments for the following elderly care handling option:
            {rag_context}
            Option: {option}
            Provide arguments that highlight benefits, feasibility, and positive outcomes.
            Format each argument on a new line starting with "Support:"."""

        if state.get("enable_streaming", False):
            support_response = ""
            for chunk in call_llm_stream(support_prompt, temperature=0.8):
                support_response += chunk
                state["current_argument_stream"] = support_response
        else:
            support_response = call_llm(support_prompt, temperature=0.8)

        # Generate attacking arguments
        attack_prompt = f"""
            Generate 2 critical arguments against the following elderly care handling option:
            Option: {option}        
            Provide arguments that highlight potential risks, challenges, or limitations.
            Format each argument on a new line starting with "Challenge:"."""

        if state.get("enable_streaming", False):
            attack_response = ""
            for chunk in call_llm_stream(attack_prompt, temperature=0.8):
                attack_response += chunk
                state["current_argument_stream"] = attack_response
        else:
            attack_response = call_llm(attack_prompt, temperature=0.8)

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

    # Store agent assignments for tracking
    agent_arguments_tracking = {}

    # Store patient analysis
    if state["patient_analysis"] is None:
        state["patient_analysis"] = analyze_patient_needs(patient_info)

    for i, option in enumerate(state["handling_options"]):
        print(f"\nOption {i+1}: {option}")

        if state.get("enable_streaming", False):
            state["argument_generation_progress"] = (
                f"Option {i+1}/{len(state['handling_options'])}: Gathering perspectives from {len(healthcare_team)} healthcare professionals..."
            )

        option_arguments = []

        # Each agent provides their perspective
        for agent_idx, agent in enumerate(healthcare_team):
            if state.get("enable_streaming", False):
                state["argument_generation_progress"] = (
                    f"Option {i+1}: [{agent_idx}] {agent.name} ({agent.role.value}) is analyzing..."
                )

            # Agent-specific prompt for supporting   arguments
            support_prompt = f"""{agent.get_perspective_prompt()}
            
                {rag_context}

                Patient Information:
                {patient_info}

                Care Option Being Evaluated:
                {option}

                From your professional perspective as a {agent.role.value}, provide 1-2 supporting arguments for this care option.
                Focus on aspects most relevant to your expertise: {', '.join(agent.expertise_areas[:3])}

                Format each argument on a new line starting with "Support:"
                Be specific about benefits from your professional viewpoint."""

            if state.get("enable_streaming", False):
                support_response = ""
                for chunk in call_llm_stream(support_prompt, temperature=0.7, max_tokens=256):
                    support_response += chunk
                    state["current_argument_stream"] = (
                        f"{agent.name}: {support_response}"
                    )
            else:
                support_response = call_llm(support_prompt, temperature=0.7, max_tokens=256)

            # Agent-specific prompt for challenging arguments
            attack_prompt = f"""{agent.get_perspective_prompt()}
            
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
                for chunk in call_llm_stream(attack_prompt, temperature=0.7, max_tokens=256):
                    attack_response += chunk
                    state["current_argument_stream"] = (
                        f"{agent.name}: {attack_response}"
                    )
            else:
                attack_response = call_llm(attack_prompt, temperature=0.7, max_tokens=256)

            # Parse and tag arguments with agent information
            for line in support_response.split("\n"):
                if line.strip().startswith("Support:"):
                    arg_content = line.replace("Support:", "").strip()
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
                if line.strip().startswith("Challenge:") or line.strip().startswith(
                    "Attack:"
                ):
                    arg_content = (
                        line.replace("Challenge:", "").replace("Attack:", "").strip()
                    )
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

    state["arguments"] = arguments
    state["current_step"] = "human_review"

    if "human_review_complete" not in state:
        state["human_review_complete"] = False

    return state


def human_review(state: GraphState) -> GraphState:
    """Human-in-the-loop: Placeholder for Gradio interface"""
    # This node doesn't modify the state
    # The actual review happens in the Gradio interface
    return state


def argument_validator(state: GraphState) -> GraphState:
    """Third LLM: Validate arguments with option to retrieve more evidence"""
    print("🫡 Validating arguments...")
    validated_arguments = []
    vector_db = MedicalVectorDB()

    # Track which arguments needed additional evidence
    arguments_with_additional_evidence = []
    total_args = len(state["arguments"])

    for i, arg in enumerate(state["arguments"]):
        if state.get("enable_streaming", False):
            state["validation_progress"] = f"Validating argument {i+1}/{total_args}"
        # First validation pass
        initial_prompt = f"""
            You are an expert analyst evaluating the validity and relevance of arguments 
            for elderly care planning.
            
            Handling Option: {arg.parent_option}
            
            Argument ({arg.argument_type}): {arg.content}
            
            Please evaluate this argument based on:
            1. Factual accuracy
            2. Relevance to elderly care and aging-in-place
            3. Practical considerations
            4. Evidence-based reasoning
            
            Provide a validity score between 0 and 1, where:
            - 0 = completely invalid/irrelevant
            - 0.5 = moderately valid
            - 1 = highly valid and relevant
            
            Response format: "Validity Score: X.XX"
            Include a brief explanation."""

        if state.get("enable_streaming", False):
            initial_response = ""
            for chunk in call_llm_stream(
                initial_prompt, temperature=0.3, max_tokens=256
            ):
                initial_response += chunk
                state["current_validation_stream"] = initial_response
        else:
            initial_response = call_llm(initial_prompt, temperature=0.3, max_tokens=256)

        # Extract initial validity score
        initial_validity_score = 0.5  # default
        try:
            if "Validity Score:" in initial_response:
                score_text = initial_response.split("Validity Score:")[1].split()[0]
                initial_validity_score = float(score_text.strip())
                initial_validity_score = max(0, min(1, initial_validity_score))
        except:
            pass

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

            if state.get("enable_streaming", False):
                search_query = ""
                for chunk in call_llm_stream(
                    search_query_prompt, temperature=0.2, max_tokens=128
                ):
                    search_query += chunk
            else:
                search_query = call_llm(
                    search_query_prompt, temperature=0.2, max_tokens=128
                ).strip()

            # Retrieve additional evidence
            additional_docs = vector_db.search(search_query, n_results=3)

            if additional_docs:
                # Track which documents were used for this argument
                doc_refs_used = []

                # Format additional evidence
                additional_context = "\nADDITIONAL MEDICAL EVIDENCE:\n"
                for i, doc in enumerate(additional_docs, 1):
                    additional_context += (
                        f"\n[Evidence {i}] (Relevance: {doc['similarity_score']:.2f})\n"
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

                revalidation_response = ""
                for chunk in call_llm_stream(
                    revalidation_prompt, temperature=0.3, max_tokens=512
                ):
                    revalidation_response += chunk

                # Extract updated validity score
                updated_validity_score = initial_validity_score  # fallback to initial
                try:
                    if "Updated Validity Score:" in revalidation_response:
                        score_text = revalidation_response.split(
                            "Updated Validity Score:"
                        )[1].split()[0]
                        updated_validity_score = float(score_text.strip())
                        updated_validity_score = max(0, min(1, updated_validity_score))
                    elif "Validity Score:" in revalidation_response:
                        score_text = revalidation_response.split("Validity Score:")[
                            1
                        ].split()[0]
                        updated_validity_score = float(score_text.strip())
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

                verification_response = ""
                for chunk in call_llm_stream(
                    verification_prompt, temperature=0.2, max_tokens=128
                ):
                    verification_response += chunk

                # Extract confirmed score
                confirmed_score = initial_validity_score
                try:
                    if "Confirmed Score:" in verification_response:
                        score_text = verification_response.split("Confirmed Score:")[
                            1
                        ].split()[0]
                        confirmed_score = float(score_text.strip())
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

        validated_arguments.append(arg)

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
        if state["adaptive_retrieval_summary"] is None:
            state["adaptive_retrieval_summary"] = adaptive_retrieval_summary

        print(f"\nAdaptive Retrieval Summary:")
        print(
            f"  Arguments enhanced: {adaptive_retrieval_summary['arguments_enhanced']}"
        )
        print(
            f"  Avg score improvement: {adaptive_retrieval_summary['average_score_improvement']:.3f}"
        )

    state["validated_arguments"] = validated_arguments
    state["current_step"] = "plan_revision"

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


def care_plan_reviser(state: GraphState) -> GraphState:
    """LLM: Revise care plan based on validated arguments with document references"""

    # Organize arguments by option and type
    arguments_by_option = {}
    for option in state["handling_options"]:
        arguments_by_option[option] = {"support": [], "attack": []}

    # Match arguments to options
    for arg in state["validated_arguments"]:
        if arg.parent_option in arguments_by_option:
            arguments_by_option[arg.parent_option][arg.argument_type].append(arg)

    # Create prompt with weighted arguments and ask for references
    prompt = f"""You are an expert geriatric care planner. Based on the validated arguments and medical knowledge, 
    create a comprehensive revised care plan for the elderly patient.
    
    IMPORTANT: When using information from the medical knowledge provided, cite it using [REF-X] format.
    
    {state.get('rag_context', '')}
    
    Patient Information:
    {state['patient_info']}
    
    Original Handling Options with Validated Arguments:
    """

    for option in state["handling_options"]:
        prompt += f"\n\nOption: {option}"

        support_args = arguments_by_option[option]["support"]
        if support_args:
            prompt += "\n  Support arguments:"
            for arg in sorted(
                support_args, key=lambda x: x.validity_score, reverse=True
            ):
                prompt += f"\n    - [{arg.validity_score:.2f}] {arg.content}"
                # Include doc references if available from adaptive retrieval
                if hasattr(arg, "supporting_docs") and arg.supporting_docs:
                    prompt += f" (Evidence from documents)"

        attack_args = arguments_by_option[option]["attack"]
        if attack_args:
            prompt += "\n  Challenge arguments:"
            for arg in sorted(
                attack_args, key=lambda x: x.validity_score, reverse=True
            ):
                prompt += f"\n    - [{arg.validity_score:.2f}] {arg.content}"

    prompt += """
        Based on the arguments, their validity scores, and the medical knowledge provided, provide:
        1. A prioritized list of recommended handling options
        2. Specific implementation steps for each recommended option
        3. Risk mitigation strategies for identified concerns
        4. Evidence-based justification with references to medical knowledge using [REF-X] format
        
        IMPORTANT: Cite relevant medical knowledge using [REF-X] where X is the reference number.
        Consider the strength of arguments (validity scores) in your recommendations."""

    if state.get("enable_streaming", False):
        response_chunks = []
        for chunk in call_llm_stream(prompt, temperature=0.8, max_tokens=1024):
            response_chunks.append(chunk)
            state["streaming_chunk"] = chunk
            state["partial_response"] = "".join(response_chunks)

        response = "".join(response_chunks)
    else:
        response = call_llm(prompt, temperature=0.8, max_tokens=1024)

    cited_refs = re.findall(r"\[REF-(\d+)\]", response)
    cited_doc_ids = set(int(ref) for ref in cited_refs)

    # Update document references with usage information
    if "document_references" in state:
        for ref in state["document_references"]:
            if ref["id"] in cited_doc_ids:
                ref["used_in"].append("final_care_plan")
                state["cited_documents"].add(ref["id"])

    # Calculate decision confidence
    decision_confidence = calculate_decision_confidence(state["validated_arguments"])

    # Create formatted references section
    references_text = _format_references(state, cited_doc_ids)

    state["revised_care_plan"] = {
        "recommendations": response,
        "decision_confidence": decision_confidence,
        "argument_summary": summarize_arguments(state["validated_arguments"]),
        "references": references_text,
        "cited_document_ids": list(cited_doc_ids),
        "total_documents_retrieved": len(state.get("retrieved_documents", [])),
        "documents_cited": len(cited_doc_ids),
    }

    print(f"Care plan revised. Decision confidence: {decision_confidence}")
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
        for chunk in call_llm_stream(prompt, temperature=0.3, max_tokens=256):
            queries_text += chunk
            state["rag_progress"] = f"Generating search queries:\n{queries_text}"
        queries = queries_text.strip().split("\n")
    else:
        queries = call_llm(prompt, temperature=0.3, max_tokens=256).strip().split("\n")

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
    state["current_step"] = "scheduling"
    return state
