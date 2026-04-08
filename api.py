import json
import asyncio
from uuid import uuid4
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from graph import create_care_plan_graph
from state import Argument
import re

app = FastAPI(title="Care Plan Generator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

graph = create_care_plan_graph()

class StartRequest(BaseModel):
    patient_info: str

class ActionRequest(BaseModel):
    action: str

# In-memory session tracking for active reviews
sessions = {}

def initial_state(patient_info):
    return {
        "patient_info": patient_info,
        "handling_options": [],
        "arguments": [],
        "validated_arguments": [],
        "revised_care_plan": {},
        "human_feedback": None,
        "current_step": "rag_retrieval",
        "human_review_complete": False,
        "user_action": None,
        "retrieved_documents": [],
        "search_queries": [],
        "rag_context": "",
        "adaptive_retrieval_summary": None,
        "document_references": [],
        "cited_documents": set(),
        "custom_team_requirements": None,
        "team_selection_rationale": None,
        "patient_analysis": None,
        "healthcare_team": [],
        "agent_arguments_tracking": {},
        "team_selection_logs": None,
        "enable_streaming": True,
        "options_generation_progress": None,
        "argument_generation_progress": None,
        "current_argument_stream": None,
        "validation_progress": None,
        "current_validation_stream": None,
        "streaming_chunk": None,
        "partial_response": None,
        "rag_progress": None,
    }

def format_arguments_display(state):
    display_text = "## 🏥 Multi-Agents Collaboration\n\n"
    if "team_selection_rationale" in state:
        display_text += f"### 🤖 AI Team Selection Rationale:\n_{state['team_selection_rationale']}_\n\n"
    
    if "healthcare_team" in state and state["healthcare_team"]:
        display_text += "### 👥 Healthcare Team Assembled:\n"
        for member in state["healthcare_team"]:
            display_text += f"- **{member['name']}** - {member['role']}\n"
        display_text += "\n---\n\n"

    for i, option in enumerate(state.get("handling_options", [])):
        display_text += f"### Option {i+1}: {option}\n\n"
        option_args = [arg for arg in state.get("arguments", []) if arg.parent_option == option]
        for arg in option_args:
            arg_idx = state["arguments"].index(arg)
            display_text += f"- `[{arg_idx}]` {arg.argument_type.upper()}: {arg.content}\n"
        display_text += "\n"
    return display_text

@app.post("/api/chat/start")
async def start_generation(req: StartRequest):
    thread_id = f"session_{uuid4().hex}"
    cfg = {"configurable": {"thread_id": thread_id}}
    state = initial_state(req.patient_info)
    sessions[thread_id] = {"cfg": cfg, "state": state}
    return {"thread_id": thread_id}

@app.get("/api/chat/stream/{thread_id}")
async def stream_generation(thread_id: str):
    async def event_generator():
        if thread_id not in sessions:
            yield f"data: {json.dumps({'type': 'error', 'content': 'Thread not found'})}\n\n"
            return
            
        session = sessions[thread_id]
        cfg = session["cfg"]
        state = session.get("state")
        
        try:
            # Note: LangGraph .stream() can be synchronous or async depending on the graph
            # If using async graph, it would be astream. For now, wrap sync stream if it is sync.
            for event in graph.stream(state if state else None, cfg):
                for node_name, node_state in event.items():
                    # Update local state cache
                    sessions[thread_id]["state"] = node_state
                    
                    if node_name == "rag_retrieval":
                        msg = "🔍 Retrieving information..."
                        yield f"data: {json.dumps({'type': 'message', 'node': node_name, 'content': msg})}\n\n"
                    elif node_name == "care_plan_generation":
                        msg = "🤖 Generating care plan..."
                        yield f"data: {json.dumps({'type': 'message', 'node': node_name, 'content': msg})}\n\n"
                    elif node_name == "argument_generation":
                        msg = "🗣️ Preparing plan rationale..."
                        yield f"data: {json.dumps({'type': 'message', 'node': node_name, 'content': msg})}\n\n"
                    elif node_name == "human_review":
                        display = format_arguments_display(node_state)
                        yield f"data: {json.dumps({'type': 'message', 'node': node_name, 'content': display})}\n\n"
                        yield f"data: {json.dumps({'type': 'review_needed'})}\n\n"
                        # Stop yielding, wait for human review
                        return
                    elif node_name == "argument_validation":
                        msg = "✅ Validating arguments..."
                        yield f"data: {json.dumps({'type': 'message', 'node': node_name, 'content': msg})}\n\n"
                    elif node_name == "plan_revision":
                        msg = "📝 Revising care plan..."
                        yield f"data: {json.dumps({'type': 'message', 'node': node_name, 'content': msg})}\n\n"
                    elif node_name == "scheduling":
                        msg = "📋 Checking provider availability..."
                        if "scheduling_slots" in node_state:
                            msg += "\n\nProviders available:\n" + str(node_state["scheduling_slots"])
                        yield f"data: {json.dumps({'type': 'message', 'node': node_name, 'content': msg})}\n\n"
                        
                    # Also sleep momentarily to flush SSE
                    await asyncio.sleep(0.1)
                    
            # Completed
            if sessions[thread_id].get("state") and "revised_care_plan" in sessions[thread_id]["state"]:
                cp = sessions[thread_id]["state"]["revised_care_plan"]
                final_msg = "✅ Generation Complete.\n\nRecommendations:\n" + cp.get("recommendations", "")
                yield f"data: {json.dumps({'type': 'message', 'node': 'Complete', 'content': final_msg})}\n\n"
            
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'message', 'node': 'Error', 'content': str(e)})}\n\n"
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/api/chat/action/{thread_id}")
async def handle_action(thread_id: str, req: ActionRequest):
    if thread_id not in sessions:
        return {"error": "Session not found"}
        
    session = sessions[thread_id]
    state = session["state"]
    action = req.action.lower().strip()
    
    if action == "accept":
        pass # state arguments remain as is
    elif action.startswith("remove "):
        try:
            idx = int(action.split()[1])
            if 0 <= idx < len(state["arguments"]):
                state["arguments"].pop(idx)
        except:
            pass
    elif action.startswith("modify "):
        try:
            parts = action.split(maxsplit=2)
            idx = int(parts[1])
            new_content = parts[2]
            if 0 <= idx < len(state["arguments"]):
                state["arguments"][idx].content = new_content
        except:
            pass
            
    # Mark review as complete and specify next node
    state["human_review_complete"] = True
    session["state"] = None # Let graph stream use configured state entirely
    
    cfg = session["cfg"]
    graph.update_state(cfg, {"human_review_complete": True, "arguments": state["arguments"]})
    
    return {"status": "ok"}

