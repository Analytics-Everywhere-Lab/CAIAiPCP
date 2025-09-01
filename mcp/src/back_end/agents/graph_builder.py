from agents.booking import get_booking_agent

from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from langchain_core.messages import AnyMessage, HumanMessage, AIMessage
import asyncio
import logging
from langchain_ollama import ChatOllama
from utils.settings import OLLAMA_LLM_MODEL
from utils.utility import picky_json


__all__ = ["LLM", "AgentState", "build_graph"]


LLM = ChatOllama(model=OLLAMA_LLM_MODEL, reasoning=True, temperature=0)


###################################################
# Agent state definition
class AgentState(TypedDict):
    messages: List[AnyMessage]
    current_node: str
    original_question: str
    updated_question: str
    summary: str
    question_approval_status: str
    question_relevant: str
    reformulated_question: str
    next_node: str


###################################################
# Logging utility function used in most nodes
def log_agent_info(state):
    logging.info(f'\n\n{"*" * 50}')
    logging.info(f'State in node : \n {picky_json(state, ['messages'])}')
    for m in state['messages']:
        logging.info(m.pretty_repr())
    logging.info(f'{"*" * 50}')


def refresh_state(state):
    state = {k: "" if isinstance(v, str) or isinstance(v, int) else [] for k, v in state.items()}
    return state


###################################################
# Nodes

async def question_relevance_check_node(state: AgentState):
    state["messages"].append(AIMessage(content=f'Question relevance to research check - Processing : {state["original_question"]}'))
    state["current_node"] = "question_relevance_check_node"

    ref_question = state.get('reformulated_question', '')
    if ref_question == '':
        question = state['original_question']
    else:
        question = ref_question

    agent = get_relevance_checker_agent(LLM)

    # Sometimes the LLM just can't resist in being more verbose than it needs to be.
    result = await agent.ainvoke({"messages": [HumanMessage(content=question)]})
    is_relevant = 'yes' in result['messages'][-1].content.lower()

    if is_relevant:
        rel = 'yes'
        next_node = "rag_node"
    else:
        rel = 'no'
        next_node = "question_reformulation_node"

    state["messages"].append(AIMessage(content=f'Question relevance checker returned : {rel}'))
    state["question_relevant"] = rel
    state["next_node"] = next_node
    log_agent_info(state)
    await asyncio.sleep(1)
    return {**state}


###################################################
# Graph building
def build_graph():
    graph = StateGraph(AgentState)
    # Graph
    builder = StateGraph(MessagesState)

    # Define nodes: these do the work
    builder.add_node("assistant", assistant)
    builder.add_node("tools", ToolNode(tools))

    # Define edges: these determine the control flow
    builder.add_edge(START, "assistant")
    builder.add_conditional_edges(
        "assistant",
        # If the latest message (result) from assistant is a tool call -> tools_condition routes to tools
        # If the latest message (result) from assistant is a not a tool call -> tools_condition routes to END
        tools_condition,
    )
    builder.add_edge("tools", "assistant")
    graph = builder.compile()
    return graph


if __name__ == '__main__':
    pass
