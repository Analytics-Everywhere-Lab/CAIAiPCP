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
    # Contestability fields: every argument keeps a stable id so human edits,
    # free-text feedback and learned memory can refer to it across plan versions.
    arg_id: Optional[str] = None  # e.g. "A3"
    source: str = "agent"  # "agent" | "human" | "feedback" | "memory"
    human_status: str = "unreviewed"  # "unreviewed" | "edited" | "added" | "rejected"
    original_content: Optional[str] = None  # text before the first human edit
    rejection_reason: Optional[str] = None
    target_arg_id: Optional[str] = None  # set when the argument targets another argument, not the option
    feedback_id: Optional[str] = None  # free-text feedback item this argument was derived from
    memory_id: Optional[str] = None  # long-term memory record this argument was instantiated from
    validation_note: Optional[str] = None  # verifier explanation behind validity_score
    strength: Optional[float] = None  # final strength after QBAF propagation
    flags: List[str] = field(default_factory=list)
    # Set by the group verification of the argument's option (see node.argument_validator).
    relevance: Optional[str] = None  # "high" | "moderate" | "low" for this patient's decision
    same_as: Optional[str] = None  # id of an earlier argument making the same point
    rebuts: List[str] = field(default_factory=list)  # ids of opposing arguments this one answers
    partly_rebuts: List[str] = field(default_factory=list)  # ... and those it only partly answers


class GraphState(TypedDict):
    """Complete state schema for the LangGraph workflow"""

    # Core patient and care planning data
    patient_info: str
    severity: str
    handling_options: List[str]
    arguments: List[Argument]
    validated_arguments: List[Argument]
    revised_care_plan: Dict[str, Any]

    # Human interaction and feedback
    human_feedback: Optional[str]
    current_step: str
    human_review_complete: bool
    user_action: Optional[str]

    # RAG and document retrieval. Only published sources are citable references; case
    # records of other patients are prompt background and never leave the server.
    retrieved_documents: List[Dict[str, Any]]  # the published sources' text, by reference id
    search_queries: List[str]
    rag_context: str  # Always a string, can be empty
    adaptive_retrieval_summary: Optional[Dict[str, Any]]
    document_references: List[Dict[str, Any]]  # published sources, cited as [REF-<id>]
    similar_cases: List[Dict[str, Any]]  # case records of other patients: background only, never cited or shown
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

    # Contestation, plan feedback and versioning
    run_mode: str  # "generate" | "contest" | "feedback"
    next_arg_seq: int
    human_ops_log: List[Dict[str, Any]]  # every human operation on the QBAF, in order
    plan_feedback: List[Dict[str, Any]]  # free-text feedback submitted for the current run
    feedback_history: List[Dict[str, Any]]  # all feedback applied in earlier runs
    feedback_ops: List[Dict[str, Any]]  # QBAF operations derived from plan_feedback
    writer_directives: List[Dict[str, Any]]  # presentation-only feedback for the plan writer
    validation_cache: Dict[str, Dict[str, Any]]
    option_reviews: Dict[str, Dict[str, Any]]  # group verification per option id
    option_screening: List[Dict[str, Any]]  # candidate options and whether each passed the fit screen
    qbaf: Optional[Dict[str, Any]]
    previous_qbaf: Optional[Dict[str, Any]]
    revision_plan: Optional[Dict[str, Any]]
    care_plan_versions: List[Dict[str, Any]]

    # Self-evolving memory
    memory_guidance: Dict[str, List[Dict[str, Any]]]  # stage -> memory records used in prompts
    memory_reflection: Optional[Dict[str, Any]]
    reflected_ops_signature: Optional[str]

    thread_id: Optional[str]

# Global tracker for progress updates bypassing LangGraph state copying
active_progress = {}
