from dataclasses import dataclass
from typing import List, Dict, Optional, TypedDict


@dataclass
class Argument:
    """Represents an argument with its content, type, and validity score"""

    content: str
    argument_type: str  # "support" or "attack"
    validity_score: Optional[float] = None
    parent_option: Optional[str] = None


class GraphState(TypedDict):
    """State schema for the LangGraph workflow"""

    patient_info: str
    handling_options: List[str]
    arguments: List[Argument]
    validated_arguments: List[Argument]
    revised_care_plan: Dict[str, any]
    human_feedback: Optional[str]
    current_step: str
    human_review_complete: bool  # Added for Gradio integration
    user_action: Optional[str]  # Added for storing user's choice
