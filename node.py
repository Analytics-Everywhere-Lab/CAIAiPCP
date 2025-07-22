from typing import Dict, List
from state import Argument, GraphState
from llm_caller import call_llm
from utils import calculate_decision_confidence


def care_plan_generator(state: GraphState) -> GraphState:
    """First LLM: Generate handling options based on patient information"""
    prompt = f"""You are an expert geriatric care planner. Based on the following patient information, 
    generate 1-3 specific handling options for their care plan in aging-in-place context.
    
    Patient Information:
    {state['patient_info']}
    
    Please provide handling options in the following format:
    Option 1: [Description]
    Option 2: [Description]
    ...
    
    Focus on practical, implementable options that support independent living while ensuring safety and quality of life."""

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
    """Second LLM: Generate support and attack arguments for each handling option"""
    arguments = []

    print(f"Generating arguments for options: {state['handling_options']}")

    for option in state["handling_options"]:
        # Generate supporting arguments
        support_prompt = f"""Generate 2 strong supporting arguments for the following elderly care handling option:
        
        Option: {option}
        
        Provide arguments that highlight benefits, feasibility, and positive outcomes.
        Format each argument on a new line starting with "Support:"."""

        support_response = call_llm(support_prompt, temperature=0.8)

        # Generate attacking arguments
        attack_prompt = f"""Generate 2 critical arguments against the following elderly care handling option:
        
        Option: {option}
        
        Provide arguments that highlight potential risks, challenges, or limitations.
        Format each argument on a new line starting with "Attack:"."""

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
            if line.strip().startswith("Attack:"):
                arg_content = line.replace("Attack:", "").strip()
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
    # Don't override human_review_complete if it's already set
    if "human_review_complete" not in state:
        state["human_review_complete"] = False
    return state


def human_review(state: GraphState) -> GraphState:
    """Human-in-the-loop: Placeholder for Gradio interface"""
    # This node doesn't modify the state
    # The actual review happens in the Gradio interface
    return state


def argument_validator(state: GraphState) -> GraphState:
    """Third LLM: Evaluate validity and relevance of arguments"""
    validated_arguments = []

    for arg in state["arguments"]:
        prompt = f"""You are an expert analyst evaluating the validity and relevance of arguments 
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

        response = call_llm(prompt, temperature=0.3, max_tokens=256)

        # Extract validity score
        validity_score = 0.5  # default
        try:
            if "Validity Score:" in response:
                score_text = response.split("Validity Score:")[1].split()[0]
                validity_score = float(score_text.strip())
                validity_score = max(0, min(1, validity_score))  # Clamp to [0,1]
        except:
            pass

        arg.validity_score = validity_score
        validated_arguments.append(arg)

    state["validated_arguments"] = validated_arguments
    state["current_step"] = "plan_revision"
    return state


def care_plan_reviser(state: GraphState) -> GraphState:
    """Fourth LLM: Revise care plan based on validated arguments"""
    # Organize arguments by option and type

    arguments_by_option = {}
    for option in state["handling_options"]:
        arguments_by_option[option] = {"support": [], "attack": []}

    # Match arguments to options (handle potential mismatches)
    for arg in state["validated_arguments"]:
        matched = False
        # First try exact match
        if arg.parent_option in arguments_by_option:
            arguments_by_option[arg.parent_option][arg.argument_type].append(arg)
            matched = True
        else:
            # Try fuzzy matching if exact match fails
            for option in state["handling_options"]:
                # Check if the parent_option is a substring or vice versa
                if (
                    arg.parent_option in option
                    or option in arg.parent_option
                    or arg.parent_option.lower() in option.lower()
                    or option.lower() in arg.parent_option.lower()
                ):
                    arguments_by_option[option][arg.argument_type].append(arg)
                    matched = True
                    print(f"Fuzzy matched '{arg.parent_option}' to '{option}'")
                    break

        if not matched:
            print(
                f"Warning: Could not match argument with parent_option '{arg.parent_option}' to any handling option"
            )

    # Create prompt with weighted arguments
    prompt = f"""You are an expert geriatric care planner. Based on the validated arguments, 
    create a comprehensive revised care plan for the elderly patient.
    
    Patient Information:
    {state['patient_info']}
    
    Original Handling Options with Validated Arguments:
    """

    for option in state["handling_options"]:
        prompt += f"\n\nOption: {option}"

        # Add supporting arguments
        support_args = arguments_by_option[option]["support"]
        if support_args:
            prompt += "\n  Supporting arguments:"
            for arg in sorted(
                support_args, key=lambda x: x.validity_score, reverse=True
            ):
                prompt += f"\n    - [{arg.validity_score:.2f}] {arg.content}"

        # Add attacking arguments
        attack_args = arguments_by_option[option]["attack"]
        if attack_args:
            prompt += "\n  Attacking arguments (Concerns/Challenges):"
            for arg in sorted(
                attack_args, key=lambda x: x.validity_score, reverse=True
            ):
                prompt += f"\n    - [{arg.validity_score:.2f}] {arg.content}"

    prompt += """
    Based on the arguments and their validity scores, provide:
    1. A prioritized list of recommended handling options
    2. Specific implementation steps for each recommended option
    3. Risk mitigation strategies for identified concerns
    4. A faithful explanation of why certain options are prioritized
    
    Consider the strength of arguments (validity scores) in your recommendations."""

    response = call_llm(prompt, temperature=0.6, max_tokens=1536)

    # Calculate decision confidence based on argument strengths
    decision_confidence = calculate_decision_confidence(state["validated_arguments"])

    state["revised_care_plan"] = {
        "recommendations": response,
        "decision_confidence": decision_confidence,
        "argument_summary": summarize_arguments(state["validated_arguments"]),
    }

    print(f"Care plan revised. Decision confidence: {decision_confidence}")
    return state


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
