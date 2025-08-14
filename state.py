from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, TypedDict


@dataclass
class Argument:
    """Represents an argument with its content, type, and validity score"""

    content: str
    argument_type: str  # "support" or "attack"
    validity_score: Optional[float] = None
    parent_option: Optional[str] = None
    supporting_docs: List[Dict[str, any]] = field(default_factory=list)


class GraphState(TypedDict):
    """State schema for the LangGraph workflow"""

    patient_info: str
    handling_options: List[str]
    arguments: List[Argument]
    validated_arguments: List[Argument]
    revised_care_plan: Dict[str, any]
    human_feedback: Optional[str]
    current_step: str
    human_review_complete: bool
    user_action: Optional[str]
    retrieved_documents: List[Dict[str, any]]
    search_queries: List[str]
    rag_context: str
    adaptive_retrieval_summary: Optional[Dict[str, any]]
    document_references: List[Dict[str, any]] 
    cited_documents: Set[int]