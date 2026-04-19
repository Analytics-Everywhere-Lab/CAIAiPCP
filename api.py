import json
import asyncio
from uuid import uuid4
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from graph import create_care_plan_graph
from state import Argument, active_progress
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
    severity: str = "Default"

class ActionRequest(BaseModel):
    action: str
    target_id: int = None
    new_content: str = None
    new_type: str = None
    new_option: str = None

# In-memory session tracking for active reviews
sessions = {}

def initial_state(patient_info, severity="Default", thread_id=None):
    return {
        "thread_id": thread_id,
        "patient_info": patient_info,
        "severity": severity,
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
    display_text = "## Multi-Agents Collaboration\n\n"
    if "team_selection_rationale" in state:
        display_text += f"### AI Team Selection Rationale:\n_{state['team_selection_rationale']}_\n\n"
    
    if "healthcare_team" in state and state["healthcare_team"]:
        display_text += "### Healthcare Team Assembled:\n"
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
    cfg = {"configurable": {"thread_id": thread_id}, "recursion_limit": 200}
    state = initial_state(req.patient_info, req.severity, thread_id)
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
            import threading
            import queue
            event_q = queue.Queue()
            
            def run_graph():
                try:
                    for event in graph.stream(state if state else None, cfg):
                        event_q.put(("event", event))
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    event_q.put(("error", str(e)))
                finally:
                    event_q.put(("done", None))
                    
            t = threading.Thread(target=run_graph)
            t.start()
            
            last_progress = {}
            is_done = False
            
            while not is_done or not event_q.empty():
                while not event_q.empty():
                    msg_type, data = event_q.get()
                    if msg_type == "event":
                        for node_name, node_state in data.items():
                            sessions[thread_id]["state"] = node_state
                            # Reset stream cursor and sub-step when a new node completes
                            last_progress["stream_len"] = 0
                            last_progress["sub_step"] = ""
                            if thread_id in active_progress:
                                active_progress[thread_id]["current_stream_text"] = ""
                                active_progress[thread_id]["current_sub_step"] = ""
                            
                            if node_name == "rag_retrieval":
                                msg = "Retrieving information from historical medical databases..."
                                yield f"data: {json.dumps({'type': 'message', 'node': node_name, 'content': msg})}\n\n"
                            elif node_name == "care_plan_generation":
                                msg = "Generating care plan..."
                                yield f"data: {json.dumps({'type': 'message', 'node': node_name, 'content': msg})}\n\n"
                            elif node_name == "argument_generation":
                                msg = "Preparing plan rationale..."
                                yield f"data: {json.dumps({'type': 'message', 'node': node_name, 'content': msg})}\n\n"
                            elif node_name == "human_review":
                                display = format_arguments_display(node_state)
                                yield f"data: {json.dumps({'type': 'message', 'node': node_name, 'content': display})}\n\n"
                                
                                args_list = []
                                for i, arg in enumerate(node_state.get('arguments', [])):
                                    args_list.append({
                                        'id': i,
                                        'content': arg.content,
                                        'type': arg.argument_type,
                                        'option': arg.parent_option,
                                        'role': arg.agent_role or 'General'
                                    })
                                
                                yield f"data: {json.dumps({'type': 'review_needed', 'options': node_state.get('handling_options', []), 'arguments': args_list})}\n\n"
                                return
                            elif node_name == "argument_validation":
                                msg = "Validating arguments..."
                                yield f"data: {json.dumps({'type': 'message', 'node': node_name, 'content': msg})}\n\n"
                            elif node_name == "plan_revision":
                                msg = "Revising care plan..."
                                yield f"data: {json.dumps({'type': 'message', 'node': node_name, 'content': msg})}\n\n"
                            elif node_name == "scheduling":
                                msg = "Checking provider availability..."
                                if "scheduling_slots" in node_state:
                                    msg += "\n\nProviders available:\n" + str(node_state["scheduling_slots"])
                                yield f"data: {json.dumps({'type': 'message', 'node': node_name, 'content': msg})}\n\n"
                    elif msg_type == "error":
                        yield f"data: {json.dumps({'type': 'message', 'node': 'Error', 'content': str(data)})}\n\n"
                        is_done = True
                    elif msg_type == "done":
                        is_done = True
                        
                # Check for global real-time progress updates
                if not is_done:
                    tracker = active_progress.get(thread_id, {})
                    prog_arg = tracker.get("argument_generation_progress")
                    prog_val = tracker.get("validation_progress")
                    stream_text = tracker.get("current_stream_text", "")
                    sub_step = tracker.get("current_sub_step", "")

                    if prog_arg and prog_arg != last_progress.get("arg"):
                        last_progress["arg"] = prog_arg
                        yield f"data: {json.dumps({'type': 'message', 'node': 'progress', 'content': prog_arg})}\n\n"
                        
                    if prog_val and prog_val != last_progress.get("val"):
                        last_progress["val"] = prog_val
                        yield f"data: {json.dumps({'type': 'message', 'node': 'progress', 'content': prog_val})}\n\n"

                    # Emit granular sub-step cards
                    if sub_step and sub_step != last_progress.get("sub_step"):
                        last_progress["sub_step"] = sub_step
                        last_progress["stream_len"] = 0  # reset stream for new sub-step
                        if thread_id in active_progress:
                            active_progress[thread_id]["current_stream_text"] = ""
                        yield f"data: {json.dumps({'type': 'sub_step', 'title': sub_step})}\n\n"

                    # Stream LLM text to frontend – send only new characters since last poll
                    last_len = last_progress.get("stream_len", 0)
                    if stream_text and len(stream_text) > last_len:
                        new_chunk = stream_text[last_len:]
                        last_progress["stream_len"] = len(stream_text)
                        yield f"data: {json.dumps({'type': 'stream_text', 'chunk': new_chunk, 'full': stream_text})}\n\n"

                await asyncio.sleep(0.05)
                    
            # Completed
            if sessions[thread_id].get("state") and "revised_care_plan" in sessions[thread_id]["state"]:
                cp = sessions[thread_id]["state"]["revised_care_plan"]
                # Yield raw care plan data — no chat bubble
                yield f"data: {json.dumps({'type': 'final_plan', 'care_plan': cp})}\n\n"
            
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
        state["human_review_complete"] = True
        session["state"] = None # Let graph stream use configured state entirely
        
        cfg = session["cfg"]
        graph.update_state(cfg, {"human_review_complete": True, "arguments": state["arguments"]})
    elif action == "remove":
        if req.target_id is not None and 0 <= req.target_id < len(state["arguments"]):
            state["arguments"].pop(req.target_id)
    elif action == "modify":
        if req.target_id is not None and 0 <= req.target_id < len(state["arguments"]):
            if req.new_content:
                state["arguments"][req.target_id].content = req.new_content
    elif action == "add":
        if req.new_content:
            new_arg = Argument(
                content=req.new_content,
                argument_type=req.new_type or "support",
                parent_option=req.new_option or state.get("handling_options", [""])[0]
            )
            state["arguments"].append(new_arg)
            
    return {"status": "ok"}


class ChatMessageRequest(BaseModel):
    message: str

@app.post("/api/chat/message/{thread_id}")
async def send_chat_message(thread_id: str, req: ChatMessageRequest):
    """Stream a follow-up LLM response about the generated care plan."""
    from node import call_llm_stream

    session = sessions.get(thread_id)
    if not session:
        return {"error": "Session not found"}

    state = session.get("state") or {}
    care_plan = ""
    if state.get("revised_care_plan"):
        care_plan = state["revised_care_plan"].get("recommendations", "")
    patient_info = state.get("patient_info", "")

    system_prompt = f"""You are an expert geriatric care coordinator. The following care plan has been generated for a patient.
Answer the user's follow-up question clearly, concisely, and compassionately.

Patient Information:
{patient_info}

Generated Care Plan:
{care_plan[:3000]}

Answer the user's question below:"""

    async def event_generator():
        try:
            full = ""
            for chunk in call_llm_stream(f"{system_prompt}\n\nUser: {req.message}", temperature=0.7, max_tokens=1024):
                full += chunk
                yield f"data: {json.dumps({'type': 'stream_text', 'chunk': chunk, 'full': full})}\n\n"
            yield f"data: {json.dumps({'type': 'message', 'node': 'bot', 'content': full})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
