import re
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from enum import Enum
import json
from healthcare_agents import HealthcareRole, HealthcareAgent, HEALTHCARE_AGENTS
from llm_caller import call_llm


class TeamComposition:
    """Manages the composition of the healthcare team"""

    # Define minimum and maximum team sizes
    MIN_TEAM_SIZE = 1
    MAX_TEAM_SIZE = 3

    # Core roles that should almost always be present
    CORE_ROLES = {HealthcareRole.NURSE}


def analyze_patient_needs(patient_info: str) -> Dict:
    """
    Use LLM to deeply analyze patient needs and identify key care areas
    """
    analysis_prompt = f"""You are a healthcare coordinator analyzing a patient case to determine their care needs.
    
        Patient Information:
        {patient_info}

        Analyze this patient and identify:
        1. PRIMARY medical conditions (list up to 5 most important)
        2. FUNCTIONAL needs (mobility, daily activities, cognitive function)
        3. PSYCHOLOGICAL/SOCIAL needs (mental health, isolation, family dynamics)
        4. CARE COMPLEXITY level (low/moderate/high/very high)
        5. SAFETY RISKS (falls, medication errors, self-harm, wandering, etc.)
        6. COORDINATION needs (multiple conditions, transitions, family involvement)

        Must provide a structured analysis in JSON format:
        {{
            "medical_conditions": ["condition1", "condition2", ...],
            "functional_status": {{
                "mobility": "independent/assisted/dependent",
                "adl_support": "none/minimal/moderate/extensive",
                "cognitive": "intact/mild_impairment/moderate_impairment/severe_impairment"
            }},
            "psychosocial_needs": ["need1", "need2", ...],
            "complexity_level": "low/moderate/high/very_high",
            "safety_risks": ["risk1", "risk2", ...],
            "coordination_intensity": "low/moderate/high",
            "special_considerations": ["consideration1", ...]
        }}"""

    try:
        response = call_llm(analysis_prompt, temperature=0.3, max_tokens=512)
        json_match = re.search(r"\{.*\}", response, re.DOTALL)
        if json_match:
            analysis = json.loads(json_match.group())
            return analysis
        else:
            # Fallback to basic analysis if JSON parsing fails
            return {
                "medical_conditions": [],
                "functional_status": {
                    "mobility": "unknown",
                    "adl_support": "unknown",
                    "cognitive": "unknown",
                },
                "psychosocial_needs": [],
                "complexity_level": "moderate",
                "safety_risks": [],
                "coordination_intensity": "moderate",
                "special_considerations": [],
            }
    except Exception as e:
        print(f"Error in patient analysis: {e}")
        return {"complexity_level": "moderate", "coordination_intensity": "moderate"}


def select_healthcare_team(
    patient_info: str,
    patient_analysis: Optional[Dict] = None,
    force_include: Optional[Set[HealthcareRole]] = None,
    max_team_size: int = 2,
) -> List[HealthcareAgent]:
    """
    Use LLM to intelligently select the most appropriate healthcare team
    based on comprehensive patient analysis

    Args:
        patient_info: Raw patient information
        patient_analysis: Pre-analyzed patient needs (optional)
        force_include: Roles that must be included
        max_team_size: Maximum number of team members
    """

    # Analyze patient if not already done
    if patient_analysis is None:
        patient_analysis = analyze_patient_needs(patient_info)

    # Create a description of available healthcare professionals
    available_roles = []
    for role, agent in HEALTHCARE_AGENTS.items():
        role_desc = {
            "role": role.value,
            "name": agent.name,
            "expertise": agent.expertise_areas,
            "priorities": agent.focus_priorities,
        }
        available_roles.append(role_desc)

    # Build the team selection prompt
    selection_prompt = f"""
    You are assembling an optimal interdisciplinary healthcare team for an elderly patient's care plan.

    PATIENT INFORMATION:
    {patient_info}

    PATIENT ANALYSIS:
    {json.dumps(patient_analysis, indent=2)}

    AVAILABLE HEALTHCARE PROFESSIONALS:
    {json.dumps(available_roles, indent=2)}

    TEAM ASSEMBLY GUIDELINES:
    … (same guidelines) …

    Return your selection strictly as a valid JSON object. Use double quotes around keys and string values, and do not include any trailing commas. The JSON must have this structure:

    {{
        "selected_team": [
            {{
                "role": "Registered Nurse",
                "reasoning": "Why this professional is essential for this patient"
            }},
            {{
                "role": "General Practitioner",
                "reasoning": "Why this professional is essential for this patient"
            }}
            // additional team members go here
        ],
        "team_size": <number of selected team members>,
        "overall_strategy": "<brief explanation of team composition strategy>",
        "key_collaborations": ["list of professionals who must work closely together"],
        "potential_gaps": ["areas that might need attention later"]
    }}
    Do not include any explanation outside the JSON.
    """

    try:
        # Get LLM response
        response = call_llm(selection_prompt, temperature=0.4, max_tokens=700)

        # Extract JSON from response
        json_match = re.search(r"\{.*\}", response, re.DOTALL)

        if json_match:
            selection_logs = []
            raw_json = json_match.group()
            try:
                selection_data = json.loads(raw_json)
            except json.JSONDecodeError:
                # try to clean common issues (e.g. trailing commas) and parse again
                selection_data = json.loads(clean_json_str(raw_json))

            # Extract selected roles
            selected_roles = []
            selected_agents = []

            selection_logs.append("\n🤖 LLM Team Selection Reasoning:")
            selection_logs.append(
                f"Strategy: {selection_data.get('overall_strategy', 'Not specified')}"
            )
            selection_logs.append(
                f"Team size: {selection_data.get('team_size', 'Unknown')}"
            )

            for member in selection_data.get("selected_team", []):
                role_name = member.get("role")
                reasoning = member.get("reasoning", "No specific reasoning provided")

                # Find matching role enum
                for role_enum, agent in HEALTHCARE_AGENTS.items():
                    if role_enum.value == role_name or agent.name in role_name:
                        if role_enum not in selected_roles:
                            selected_roles.append(role_enum)
                            selected_agents.append(agent)
                            selection_logs.append(
                                f"  ✓ {agent.name} ({role_enum.value})"
                            )
                            selection_logs.append(f"    Reasoning: {reasoning}")
                        break

            # Add any forced inclusions not already selected
            if force_include:
                for role in force_include:
                    if role not in selected_roles and role in HEALTHCARE_AGENTS:
                        selected_agents.append(HEALTHCARE_AGENTS[role])
                        selection_logs.append(
                            f"  ✓ {HEALTHCARE_AGENTS[role].name} (Required inclusion)"
                        )

            # Ensure core roles are included if not already
            for core_role in TeamComposition.CORE_ROLES:
                if core_role not in selected_roles and core_role in HEALTHCARE_AGENTS:
                    selected_agents.append(HEALTHCARE_AGENTS[core_role])
                    selection_logs.append(
                        f"  ✓ {HEALTHCARE_AGENTS[core_role].name} (Core team member)"
                    )

            # Print collaboration notes if available
            if "key_collaborations" in selection_data:
                selection_logs.append("\n🤝 Key Collaborations Needed:")
                for collab in selection_data["key_collaborations"]:
                    selection_logs.append(f"  • {collab}")

            # Print potential gaps
            if "potential_gaps" in selection_data:
                selection_logs.append("\n⚠️ Potential Care Gaps to Monitor:")
                for gap in selection_data["potential_gaps"]:
                    selection_logs.append(f"  • {gap}")

            return selected_agents[:max_team_size], selection_logs

    except Exception as e:
        print(f"Error in LLM team selection: {e}")
        print("Falling back to complexity-based selection...")

    # Fallback: Use complexity-based selection if LLM fails
    return select_team_by_complexity(patient_analysis, patient_info)


def clean_json_str(json_str: str) -> str:
    # remove trailing commas before closing braces/brackets
    json_str = re.sub(r",\s*([}\]])", r"\1", json_str)
    return json_str


def select_team_by_complexity(
    patient_analysis: Dict, patient_info: str
) -> List[HealthcareAgent]:
    """
    Fallback method: Select team based on complexity level
    Used when LLM selection fails
    """
    complexity = patient_analysis.get("complexity_level", "moderate")

    team = [
        HEALTHCARE_AGENTS[HealthcareRole.NURSE],
        HEALTHCARE_AGENTS[HealthcareRole.GENERAL_PRACTITIONER],
    ]

    # Add based on complexity
    if complexity in ["moderate", "high", "very_high"]:
        team.append(HEALTHCARE_AGENTS[HealthcareRole.SOCIAL_WORKER])
        team.append(HEALTHCARE_AGENTS[HealthcareRole.OCCUPATIONAL_THERAPIST])

    if complexity in ["high", "very_high"]:
        team.append(HEALTHCARE_AGENTS[HealthcareRole.GERIATRICIAN])
        team.append(HEALTHCARE_AGENTS[HealthcareRole.CARE_COORDINATOR])

        # Add specialists based on keywords as last resort
        patient_lower = patient_info.lower()
        if "fall" in patient_lower or "mobil" in patient_lower:
            team.append(HEALTHCARE_AGENTS[HealthcareRole.PHYSICAL_THERAPIST])
        if (
            "depress" in patient_lower
            or "anxi" in patient_lower
            or "dement" in patient_lower
        ):
            team.append(HEALTHCARE_AGENTS[HealthcareRole.PSYCHIATRIST])

    if complexity == "very_high":
        team.append(HEALTHCARE_AGENTS[HealthcareRole.PHARMACIST])

    return team[: TeamComposition.MAX_TEAM_SIZE]


def get_agents_for_condition_llm(
    patient_info: str,
    enable_streaming: bool = False,
    custom_requirements: Optional[Dict] = None,
) -> List[HealthcareAgent]:
    """
    Main function to get healthcare agents using LLM selection

    Args:
        patient_info: Patient information text
        enable_streaming: Whether to show selection progress
        custom_requirements: Optional custom requirements for team selection

    Returns:
        List of selected healthcare agents
    """
    selection_logs = []
    if enable_streaming:
        selection_logs.append("🔍 Analyzing patient needs...")

    # First, analyze the patient
    patient_analysis = analyze_patient_needs(patient_info)

    if enable_streaming:
        selection_logs.append(
            f"📊 Complexity level: {patient_analysis.get('complexity_level', 'Unknown')}"
        )
        selection_logs.append(
            f"🏥 Coordination needs: {patient_analysis.get('coordination_intensity', 'Unknown')}"
        )

    # Determine max team size based on complexity
    complexity = patient_analysis.get("complexity_level", "moderate")
    # if complexity == "low":
    #     max_team_size = 4
    # elif complexity == "moderate":
    #     max_team_size = 6
    # elif complexity == "high":
    #     max_team_size = 7
    # else:  # very_high
    #     max_team_size = TeamComposition.MAX_TEAM_SIZE
    max_team_size = TeamComposition.MAX_TEAM_SIZE
    # Check for any custom requirements
    force_include = set()
    if custom_requirements:
        if "must_include" in custom_requirements:
            for role_name in custom_requirements["must_include"]:
                # Find matching role enum
                for role_enum in HealthcareRole:
                    if role_enum.value == role_name:
                        force_include.add(role_enum)
                        break

        if "max_team_size" in custom_requirements:
            max_team_size = min(
                custom_requirements["max_team_size"], TeamComposition.MAX_TEAM_SIZE
            )

    if enable_streaming:
        selection_logs.append(
            f"🏥 Assembling healthcare team (max size: {max_team_size})..."
        )

    # Select the team using LLM
    selected_team, team_selection_logs = select_healthcare_team(
        patient_info=patient_info,
        patient_analysis=patient_analysis,
        force_include=force_include,
        max_team_size=max_team_size,
    )

    if enable_streaming:
        selection_logs.append(
            f"✅ Team assembled with {len(selected_team)} healthcare professionals"
        )

    selection_logs.extend(team_selection_logs)

    return selected_team, selection_logs


def explain_team_selection(
    patient_info: str, selected_team: List[HealthcareAgent]
) -> str:
    """
    Generate an explanation of why this particular team was selected
    """
    team_roles = [agent.role.value for agent in selected_team]

    explanation_prompt = f"""Based on this patient case, explain why this specific healthcare team was assembled:

        Patient Information:
        {patient_info}

        Selected Team:
        {', '.join(team_roles)}

        Provide a brief, clear explanation (2-3 sentences) of:
        1. Why this team composition is optimal for this patient
        2. How these professionals will work together
        3. What key outcomes this team can achieve

        Keep it concise and focused on the value each professional brings."""

    try:
        explanation = call_llm(explanation_prompt, temperature=0.5, max_tokens=128)
        return explanation.strip()
    except:
        return "This interdisciplinary team was selected to address the patient's complex medical, functional, and psychosocial needs through coordinated care."
