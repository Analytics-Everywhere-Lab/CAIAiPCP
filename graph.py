from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from node import (
    argument_validator,
    feedback_integration,
    memory_reflection,
    multi_agent_argument_generator,
    care_plan_generator,
    care_plan_reviser,
    human_review,
    qbaf_evaluation,
    rag_retrieval,
    revision_planning,
    route_after_human_review,
    route_after_plan_revision,
    route_entry,
    scheduling,
)
from state import GraphState


def create_care_plan_graph():
    """Create and configure the LangGraph workflow

    A new case runs from retrieval to the human review, where the graph pauses.
    Once a plan exists, the same thread re-enters to apply the clinician's
    contestation: table edits go straight to re-verification ("contest"),
    free-text plan feedback is first formulated as QBAF operations ("feedback").
    """
    workflow = StateGraph(GraphState)

    # Add nodes
    workflow.add_node("rag_retrieval", rag_retrieval)
    workflow.add_node("care_plan_generation", care_plan_generator)
    workflow.add_node("argument_generation", multi_agent_argument_generator)
    workflow.add_node("human_review", human_review)
    workflow.add_node("feedback_integration", feedback_integration)
    workflow.add_node("argument_validation", argument_validator)
    workflow.add_node("qbaf_evaluation", qbaf_evaluation)
    workflow.add_node("revision_planning", revision_planning)
    workflow.add_node("plan_revision", care_plan_reviser)
    workflow.add_node("scheduling", scheduling)
    workflow.add_node("memory_reflection", memory_reflection)

    # Add edges
    workflow.set_conditional_entry_point(
        route_entry,
        {
            "rag_retrieval": "rag_retrieval",
            "argument_validation": "argument_validation",
            "feedback_integration": "feedback_integration",
        },
    )
    workflow.add_edge("rag_retrieval", "care_plan_generation")
    workflow.add_edge("care_plan_generation", "argument_generation")
    workflow.add_edge("argument_generation", "human_review")

    # Conditional edge for human review
    workflow.add_conditional_edges(
        "human_review",
        route_after_human_review,
        {"human_review": "human_review", "argument_validation": "argument_validation"},
    )

    workflow.add_edge("feedback_integration", "argument_validation")
    workflow.add_edge("argument_validation", "qbaf_evaluation")
    workflow.add_edge("qbaf_evaluation", "revision_planning")
    workflow.add_edge("revision_planning", "plan_revision")
    workflow.add_conditional_edges(
        "plan_revision",
        route_after_plan_revision,
        {"scheduling": "scheduling", "memory_reflection": "memory_reflection"},
    )
    workflow.add_edge("scheduling", "memory_reflection")
    workflow.add_edge("memory_reflection", END)

    # Compile with memory for checkpointing. Pausing after the human review
    # replaces spinning the review node until the recursion limit; accepting
    # the review updates the state, which re-evaluates the route above.
    memory = MemorySaver()
    graph = workflow.compile(checkpointer=memory, interrupt_after=["human_review"])
    return graph
