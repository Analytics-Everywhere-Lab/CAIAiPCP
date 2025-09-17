from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, TypedDict, Any


@dataclass
class Argument:
    """Represents an argument with its content, type, and validity score"""

    content: str
    argument_type: str  # "support" or "attack"
    validity_score: Optional[float] = None
    parent_option: Optional[str] = None
    supporting_docs: List[Dict[str, Any]] = field(default_factory=list)
    # Additional fields for multi-agent support
    agent_role: Optional[str] = None
    agent_name: Optional[str] = None


class GraphState(TypedDict):
    """Complete state schema for the LangGraph workflow"""
    
    # Core patient and care planning data
    patient_info: str
    handling_options: List[str]
    arguments: List[Argument]
    validated_arguments: List[Argument]
    revised_care_plan: Dict[str, Any]
    
    # Human interaction and feedback
    human_feedback: Optional[str]
    current_step: str
    human_review_complete: bool
    user_action: Optional[str]
    
    # RAG and document retrieval
    retrieved_documents: List[Dict[str, Any]]
    search_queries: List[str]
    rag_context: str  # Always a string, can be empty
    adaptive_retrieval_summary: Optional[Dict[str, Any]]
    document_references: List[Dict[str, Any]] 
    cited_documents: Set[int]
    
    # Multi-agent healthcare team management
    custom_team_requirements: Optional[Dict[str, Any]]
    team_selection_rationale: Optional[str]
    patient_analysis: Optional[Dict[str, Any]]
    healthcare_team: List[Dict[str, Any]]
    agent_arguments_tracking: Dict[str, List[Dict[str, Any]]]
    team_selection_logs: Optional[List[str]]
    
    # Streaming and progress tracking (all optional since they're used conditionally)
    enable_streaming: bool
    options_generation_progress: Optional[str]
    argument_generation_progress: Optional[str]
    current_argument_stream: Optional[str]
    validation_progress: Optional[str]
    current_validation_stream: Optional[str]
    streaming_chunk: Optional[str]
    partial_response: Optional[str]
    rag_progress: Optional[str]

    # Scheduling
    scheduling_query: Optional[Dict[str, Any]]  # optional filter, e.g., date range
    scheduling_slots: Optional[Dict[str, List[Dict[str, Any]]]]  # provider_name -> slot dicts
    scheduling_summary: Optional[str]