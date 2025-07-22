from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from node import (
    argument_generator,
    argument_validator,
    care_plan_generator,
    care_plan_reviser,
    human_review,
    route_after_human_review,
)
from state import GraphState


def create_care_plan_graph():
    """Create and configure the LangGraph workflow"""
    workflow = StateGraph(GraphState)

    # Add nodes
    workflow.add_node("care_plan_generation", care_plan_generator)
    workflow.add_node("argument_generation", argument_generator)
    workflow.add_node("human_review", human_review)
    workflow.add_node("argument_validation", argument_validator)
    workflow.add_node("plan_revision", care_plan_reviser)

    # Add edges
    workflow.set_entry_point("care_plan_generation")
    workflow.add_edge("care_plan_generation", "argument_generation")
    workflow.add_edge("argument_generation", "human_review")

    # Conditional edge for human review
    workflow.add_conditional_edges(
        "human_review",
        route_after_human_review,
        {"human_review": "human_review", "argument_validation": "argument_validation"},
    )

    workflow.add_edge("argument_validation", "plan_revision")
    workflow.add_edge("plan_revision", END)

    # Compile with memory for checkpointing
    memory = MemorySaver()
    graph = workflow.compile(checkpointer=memory)
    return graph


# Main execution functions
def generate_elderly_care_plan_terminal(patient_info: str):
    """Terminal-based function to generate an argumentative care plan"""
    # Initialize the graph
    graph = create_care_plan_graph()

    # Initial state
    initial_state = {
        "patient_info": patient_info,
        "handling_options": [],
        "arguments": [],
        "validated_arguments": [],
        "revised_care_plan": {},
        "human_feedback": None,
        "current_step": "care_plan_generation",
        "human_review_complete": True,  # Skip human review for terminal version
        "user_action": None,
    }

    # Run the workflow
    config = {
        "configurable": {"thread_id": "care_plan_terminal"},
        "recursion_limit": 1000,
    }
    final_state = graph.invoke(initial_state, config)

    # Display results
    print("\n=== FINAL CARE PLAN ===")
    print(
        f"\nDecision Confidence: {final_state['revised_care_plan']['decision_confidence']}"
    )
    print(f"\nArgument Summary: {final_state['revised_care_plan']['argument_summary']}")
    print(f"\nRecommendations:\n{final_state['revised_care_plan']['recommendations']}")

    return final_state
