from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum


class HealthcareRole(Enum):
    """Enumeration of healthcare professional roles"""

    NURSE = "Registered Nurse"
    GENERAL_PRACTITIONER = "General Practitioner"
    GERIATRICIAN = "Geriatrician"
    PHYSICAL_THERAPIST = "Physical Therapist"
    OCCUPATIONAL_THERAPIST = "Occupational Therapist"
    SOCIAL_WORKER = "Social Worker"
    PSYCHIATRIST = "Psychiatrist"
    NUTRITIONIST = "Nutritionist"
    HOME_HEALTH_AIDE = "Home Health Aide"
    PHARMACIST = "Pharmacist"
    CARE_COORDINATOR = "Care Coordinator"


@dataclass
class HealthcareAgent:
    """Represents a healthcare professional agent"""

    role: HealthcareRole
    name: str
    expertise_areas: List[str]
    focus_priorities: List[str]
    argument_style: str

    def get_perspective_prompt(self) -> str:
        """Generate a prompt that captures this agent's perspective"""
        expertise_str = ", ".join(self.expertise_areas)
        priorities_str = ", ".join(self.focus_priorities)
        prompt = f"""You are a {self.role.value} named {self.name} providing expert input on elderly care planning.
            Your areas of expertise: {expertise_str}
            Your priorities when evaluating care options: {priorities_str}
            Your professional perspective: {self.argument_style}

            Based on your professional background and expertise, provide arguments that reflect your specific concerns and insights."""

        return prompt


HEALTHCARE_AGENTS = {
    HealthcareRole.NURSE: HealthcareAgent(
        role=HealthcareRole.NURSE,
        name="Registered Nurse",
        expertise_areas=[
            "medication management",
            "wound care",
            "daily health monitoring",
            "patient education",
            "symptom assessment",
        ],
        focus_priorities=[
            "medication adherence",
            "infection prevention",
            "comfort and pain management",
            "family education",
        ],
        argument_style="Practical and patient-centered, focusing on daily care needs and quality of life",
    ),
    HealthcareRole.GENERAL_PRACTITIONER: HealthcareAgent(
        role=HealthcareRole.GENERAL_PRACTITIONER,
        name="General Practitioner",
        expertise_areas=[
            "comprehensive medical care",
            "chronic disease management",
            "preventive care",
            "medication prescribing",
            "medical history evaluation",
        ],
        focus_priorities=[
            "overall health stability",
            "disease progression prevention",
            "medication optimization",
            "coordination with specialists",
        ],
        argument_style="Holistic medical perspective, balancing multiple health conditions and treatments",
    ),
    HealthcareRole.GERIATRICIAN: HealthcareAgent(
        role=HealthcareRole.GERIATRICIAN,
        name="Geriatrician",
        expertise_areas=[
            "age-related conditions",
            "polypharmacy management",
            "cognitive assessment",
            "frailty evaluation",
            "end-of-life planning",
        ],
        focus_priorities=[
            "maintaining functional independence",
            "cognitive preservation",
            "fall prevention",
            "quality vs quantity of life decisions",
        ],
        argument_style="Specialized in elderly care, emphasizing dignity, autonomy, and age-appropriate interventions",
    ),
    HealthcareRole.PHYSICAL_THERAPIST: HealthcareAgent(
        role=HealthcareRole.PHYSICAL_THERAPIST,
        name="Physical Therapist",
        expertise_areas=[
            "mobility assessment",
            "strength training",
            "balance improvement",
            "gait analysis",
            "adaptive equipment training",
        ],
        focus_priorities=[
            "fall risk reduction",
            "maintaining mobility",
            "pain-free movement",
            "independence in transfers",
        ],
        argument_style="Movement-focused, emphasizing physical function and fall prevention strategies",
    ),
    HealthcareRole.OCCUPATIONAL_THERAPIST: HealthcareAgent(
        role=HealthcareRole.OCCUPATIONAL_THERAPIST,
        name="Occupational Therapist",
        expertise_areas=[
            "activities of daily living",
            "home safety assessment",
            "adaptive equipment selection",
            "cognitive strategies",
            "environmental modifications",
        ],
        focus_priorities=[
            "maintaining independence in daily tasks",
            "home environment safety",
            "cognitive compensation strategies",
            "energy conservation",
        ],
        argument_style="Functional and adaptive, focusing on enabling safe and independent daily activities",
    ),
    HealthcareRole.SOCIAL_WORKER: HealthcareAgent(
        role=HealthcareRole.SOCIAL_WORKER,
        name="Social Worker",
        expertise_areas=[
            "community resources",
            "family dynamics",
            "financial assistance programs",
            "support group coordination",
            "care transitions",
        ],
        focus_priorities=[
            "social support systems",
            "resource accessibility",
            "family caregiver support",
            "quality of life beyond medical needs",
        ],
        argument_style="Holistic social perspective, addressing psychosocial needs and community integration",
    ),
    HealthcareRole.PSYCHIATRIST: HealthcareAgent(
        role=HealthcareRole.PSYCHIATRIST,
        name="Psychiatrist",
        expertise_areas=[
            "mental health assessment",
            "dementia evaluation",
            "depression treatment",
            "anxiety management",
            "psychotropic medications",
        ],
        focus_priorities=[
            "cognitive function preservation",
            "mood stability",
            "behavioral symptom management",
            "medication interactions",
        ],
        argument_style="Mental health focused, addressing cognitive and emotional wellbeing in aging",
    ),
    HealthcareRole.NUTRITIONIST: HealthcareAgent(
        role=HealthcareRole.NUTRITIONIST,
        name="Nutritionist",
        expertise_areas=[
            "nutritional assessment",
            "special diets",
            "weight management",
            "supplement recommendations",
            "meal planning",
        ],
        focus_priorities=[
            "adequate nutrition",
            "managing dietary restrictions",
            "preventing malnutrition",
            "medication-food interactions",
        ],
        argument_style="Nutrition-centered, emphasizing the role of diet in health maintenance and disease management",
    ),
    HealthcareRole.HOME_HEALTH_AIDE: HealthcareAgent(
        role=HealthcareRole.HOME_HEALTH_AIDE,
        name="Home Health Aide",
        expertise_areas=[
            "personal care assistance",
            "daily routine support",
            "companionship",
            "basic health monitoring",
            "household tasks",
        ],
        focus_priorities=[
            "dignity in personal care",
            "maintaining daily routines",
            "emotional support",
            "practical daily challenges",
        ],
        argument_style="Hands-on practical perspective, focusing on day-to-day realities of home care",
    ),
    HealthcareRole.PHARMACIST: HealthcareAgent(
        role=HealthcareRole.PHARMACIST,
        name="Pharmacist",
        expertise_areas=[
            "medication interactions",
            "dosing optimization",
            "compliance strategies",
            "side effect management",
            "medication delivery systems",
        ],
        focus_priorities=[
            "medication safety",
            "preventing adverse drug events",
            "simplifying medication regimens",
            "cost-effective alternatives",
        ],
        argument_style="Medication-focused, emphasizing safe and effective pharmaceutical care",
    ),
    HealthcareRole.CARE_COORDINATOR: HealthcareAgent(
        role=HealthcareRole.CARE_COORDINATOR,
        name="Care Coordinator",
        expertise_areas=[
            "care plan coordination",
            "insurance navigation",
            "appointment scheduling",
            "provider communication",
            "transition planning",
        ],
        focus_priorities=[
            "continuity of care",
            "reducing care fragmentation",
            "preventing readmissions",
            "optimizing resource utilization",
        ],
        argument_style="Systems-thinking approach, focusing on coordination and integration of services",
    ),
}

def format_agent_argument_display(arguments_by_agent: Dict[str, List]) -> str:
    """
    Format arguments grouped by healthcare professional for display
    """
    display_text = ""
    
    for agent_name, agent_args in arguments_by_agent.items():
        if agent_args:
            display_text += f"\n### {agent_name}:\n"
            
            supports = [arg for arg in agent_args if arg['type'] == 'support']
            attacks = [arg for arg in agent_args if arg['type'] == 'challenge']
            
            if supports:
                display_text += "**Supports:**\n"
                for arg in supports:
                    display_text += f"- {arg['content']}\n"
            
            if attacks:
                display_text += "**Challenges:**\n"
                for arg in attacks:
                    display_text += f"- {arg['content']}\n"
    
    return display_text