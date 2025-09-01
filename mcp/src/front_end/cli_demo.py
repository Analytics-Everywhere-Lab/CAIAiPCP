from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_ollama import ChatOllama
from langchain_core.messages import AnyMessage, HumanMessage, AIMessage
from typing import TypedDict, List
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, END
import uuid
import asyncio


MCP_SERVER_URL="http://localhost:8000/sse"
OLLAMA_URL="http://localhost:11434"

CLIENT = MultiServerMCPClient(
    {
        "Demo": {
            "url": MCP_SERVER_URL,
            "transport": "sse",
        }
    }
)

LLM = ChatOllama(model="qwen3:8b", base_url=OLLAMA_URL, reasoning=True, temperature=0)


class AgentState(TypedDict):
    messages: List[AnyMessage]


async def get_agent():
    tools = await CLIENT.get_tools()
    prompts = await CLIENT.get_prompt('Demo', 'configure_assistant')

    agent = create_react_agent(
        LLM,
        tools, 
        prompt=prompts[0].content
    )
    return agent


async def reasoning_node(state: AgentState):
    last_msg_text = next((m.content for m in reversed(state["messages"]) if isinstance(m, HumanMessage)), "<no message provided>") 
    state["messages"].append(AIMessage(content=f"Message - In reasoning node ..."))
    request = {
        "messages": [HumanMessage(content=last_msg_text)]
    }
    agent = await get_agent()
    result = await agent.ainvoke(request)
    state['messages'] += result['messages']
    return {**state}


def start_node(state: AgentState):
    # No action; just pass through
    return state


def assemble_graph():
    graph = StateGraph(AgentState)

    # Graph odes
    graph.add_node("start_node", start_node)
    graph.add_node("reasoning_node", reasoning_node)

    # Graph edges
    graph.set_entry_point("start_node")
    graph.add_edge("start_node", "reasoning_node")
    graph.add_edge("reasoning_node", END)

    checkpointer = InMemorySaver()
    app = graph.compile(checkpointer=checkpointer)


    thread_id = str(uuid.uuid4())

    state: AgentState = {
        "messages": []
    }

    config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 100}

    return app, state, config


# Function to call model
async def async_call_model(graph, state, config):
    res = await graph.ainvoke(state, config)
    return res


async def prompt():
    app, state, config = assemble_graph()

    # Loop that asks for user input until the user types 'exit'
    while True:
        # Prompt for user input
        user_input = input("Type your question (or 'exit' to quit): ")

        # If the user types 'exit', break out of the loop
        if user_input.lower() == 'exit':
            print("Exiting the loop.")
            break

        # Append the user input to the state as a HumanMessage
        state['messages'].append(HumanMessage(content=user_input))
        # Call the model and get a response
        resp = await async_call_model(app, state, config)
        # Print the response
        print(resp['messages'][-1].content)
        print('\n')


if __name__ == '__main__':
    asyncio.run(prompt())
