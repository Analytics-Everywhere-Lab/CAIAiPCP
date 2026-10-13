import json
import asyncio
import queue
import threading
import traceback
from typing import Any, Dict, List, Optional
from uuid import uuid4
from fastapi import FastAPI
from fastapi.responses import JSONResponse, Response, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from arguments import (
    arguments_payload,
    ensure_argument_ids,
    find_argument,
    is_human_authored,
    new_arg_id,
    record_human_op,
    resolve_option,
)
from care_plan_document import now_iso
from chat_context import ChatMemory
from graph import create_care_plan_graph
from llm_caller import call_llm, call_llm_stream
from memory.service import consolidation_summary, get_memory_service
from state import Argument, active_progress
from utils import clip_text

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
    target_id: Optional[int] = None  # positional index, kept for older clients
    arg_id: Optional[str] = None
    new_content: Optional[str] = None
    new_type: Optional[str] = None
    new_option: Optional[str] = None
    new_role: Optional[str] = None
    reason: Optional[str] = None

class FeedbackItem(BaseModel):
    text: str
    section_id: Optional[str] = None
    quote: Optional[str] = None

class RegenerateRequest(BaseModel):
    feedback: List[FeedbackItem] = []

class ApproveRequest(BaseModel):
    version: Optional[int] = None

class ChatMessageRequest(BaseModel):
    message: str

class MemoryReviewRequest(BaseModel):
    decision: str
    note: Optional[str] = None

class ConsolidateRequest(BaseModel):
    dry_run: bool = False
    retry_under_review: bool = False

# In-memory session tracking for active reviews
sessions = {}

# Shown as a reasoning-trace card when each node starts.
NODE_MESSAGES = {
    "rag_retrieval": "Retrieving information from historical medical databases...",
    "care_plan_generation": "Generating care options...",
    "argument_generation": "Assembling the care team and preparing plan rationale...",
    "feedback_integration": "Interpreting your feedback as changes to the argument graph...",
    "argument_validation": "Verifying arguments...",
    "qbaf_evaluation": "Weighing arguments in the argumentation framework...",
    "revision_planning": "Choosing how to update the care plan...",
    "plan_revision": "Writing the care plan...",
    "scheduling": "Checking provider availability...",
    "memory_reflection": "Learning from your contestations...",
}


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
        "run_mode": "generate",
        "next_arg_seq": 0,
        "human_ops_log": [],
        "plan_feedback": [],
        "feedback_history": [],
        "feedback_ops": [],
        "writer_directives": [],
        "validation_cache": {},
        "qbaf": None,
        "previous_qbaf": None,
        "revision_plan": None,
        "care_plan_versions": [],
        "memory_guidance": {},
        "memory_reflection": None,
        "reflected_ops_signature": None,
    }


def _sse(data: Dict[str, Any]) -> str:
    return f"data: {json.dumps(data, default=str)}\n\n"


def pending_changes(state: Dict[str, Any]) -> int:
    """Contestations of the argument table since the latest plan version."""
    versions = state.get("care_plan_versions") or []
    cursor = versions[-1].get("ops_cursor", 0) if versions else 0
    return max(0, len(state.get("human_ops_log") or []) - cursor)


def client_payload(state: Dict[str, Any]) -> Dict[str, Any]:
    """Everything the review dashboard and plan view need, in one shape."""
    return {
        "options": state.get("handling_options") or [],
        "arguments": arguments_payload(state),
        "care_plan": state.get("revised_care_plan") or None,
        "versions": state.get("care_plan_versions") or [],
        "team": state.get("healthcare_team") or [],
        "team_rationale": state.get("team_selection_rationale"),
        "feedback_history": state.get("feedback_history") or [],
        "pending_changes": pending_changes(state),
        "memory_reflection": state.get("memory_reflection"),
        # Per-argument strength and impact on its option, as of the latest evaluation.
        "qbaf_arguments": (state.get("qbaf") or {}).get("arguments", {}),
    }


def _review_note(state: Dict[str, Any]) -> str:
    arguments = state.get("arguments") or []
    team = ", ".join(member["name"] for member in state.get("healthcare_team") or [])
    learned = sum(1 for arg in arguments if arg.source == "memory")
    note = (f"Your care team ({team or 'multidisciplinary'}) drafted {len(arguments)} arguments across "
            f"{len(state.get('handling_options') or [])} care options")
    note += f", including {learned} drawn from lessons of earlier reviews." if learned else "."
    note += " Review them in the panel on the right, then accept to generate the care plan."
    if state.get("team_selection_rationale"):
        note += f"\n\n_{clip_text(state['team_selection_rationale'], 400)}_"
    return note


def _version_note(plan: Dict[str, Any]) -> str:
    note = f"Care plan v{plan['version']} is ready ({plan['strategy_label'].lower()})."
    if plan["version"] > 1:
        note += f" {plan['rationale']}"
    return note


def _record_node(session: Dict[str, Any], node_name: str, node_state: Dict[str, Any]) -> None:
    """Session-level side effects of a completed node; runs in the graph worker so
    they happen even if the browser disconnects mid-run."""
    chat: ChatMemory = session["chat"]
    if node_name == "human_review":
        chat.add_event(f"Care team drafted {len(node_state.get('arguments') or [])} arguments for review.")
    elif node_name == "plan_revision":
        plan = node_state.get("revised_care_plan") or {}
        chat.add_event(f"Care plan v{plan.get('version')} generated ({plan.get('strategy_label')}): "
                       f"{plan.get('change_summary', '')}")


def _node_events(session: Dict[str, Any], node_name: str, node_state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """SSE events for a completed node."""
    if node_name == "human_review":
        payload = client_payload(node_state)
        return [
            {"type": "message", "node": "human_review", "content": _review_note(node_state)},
            {"type": "review_needed", "options": payload["options"], "arguments": payload["arguments"],
             "team": payload["team"]},
        ]
    if node_name == "revision_planning":
        plan = node_state.get("revision_plan") or {}
        return [{"type": "revision", "strategy": plan.get("strategy"), "strategy_label": plan.get("strategy_label"),
                 "rationale": plan.get("rationale"), "sections": plan.get("sections")}]
    if node_name == "plan_revision":
        payload = client_payload(node_state)
        return [
            {"type": "final_plan", **payload},
            {"type": "message", "node": "system", "content": _version_note(payload["care_plan"])},
        ]
    if node_name == "scheduling":
        return [{"type": "schedule", "care_plan": node_state.get("revised_care_plan"),
                 "versions": node_state.get("care_plan_versions") or []}]
    if node_name == "memory_reflection" and node_state.get("memory_reflection"):
        return [{"type": "memory", "reflection": node_state["memory_reflection"]}]
    return []


def _start_run(session: Dict[str, Any], graph_input: Optional[Dict[str, Any]]) -> "queue.Queue":
    """Run the graph in a worker thread; events are queued for the SSE response."""
    event_q: "queue.Queue" = queue.Queue()

    def worker():
        try:
            for mode, chunk in graph.stream(graph_input, session["cfg"], stream_mode=["tasks", "updates"]):
                if mode == "updates":
                    for node_name, node_state in chunk.items():
                        if node_name.startswith("__") or not isinstance(node_state, dict):
                            continue  # e.g. the "__interrupt__" marker after human review
                        session["state"] = node_state
                        _record_node(session, node_name, node_state)
                event_q.put((mode, chunk))
        except Exception as e:
            traceback.print_exc()
            event_q.put(("error", str(e)))
        finally:
            session["running"] = False
            event_q.put(("done", None))

    threading.Thread(target=worker, daemon=True).start()
    return event_q


@app.post("/api/chat/start")
async def start_generation(req: StartRequest):
    thread_id = f"session_{uuid4().hex}"
    cfg = {"configurable": {"thread_id": thread_id}, "recursion_limit": 200}
    state = initial_state(req.patient_info, req.severity, thread_id)
    sessions[thread_id] = {
        "cfg": cfg,
        "state": state,
        "next_input": state,
        "running": False,
        "lock": threading.Lock(),
        "chat": ChatMemory(),
        "chat_lock": threading.Lock(),
    }
    return {"thread_id": thread_id}

@app.get("/api/chat/stream/{thread_id}")
async def stream_generation(thread_id: str):
    async def event_generator():
        session = sessions.get(thread_id)
        if session is None:
            yield _sse({'type': 'error', 'content': 'Thread not found'})
            return
        with session["lock"]:
            if session["running"]:
                yield _sse({"type": "error", "content": "A generation is already running for this session."})
                return
            session["running"] = True
            graph_input = session.pop("next_input", None)
        active_progress.pop(thread_id, None)  # drop progress text left over from the previous run
        event_q = _start_run(session, graph_input)

        try:
            last_progress = {}
            is_done = False

            def reset_stream():
                last_progress["stream_len"] = 0
                last_progress["sub_step"] = ""
                if thread_id in active_progress:
                    active_progress[thread_id]["current_stream_text"] = ""
                    active_progress[thread_id]["current_sub_step"] = ""

            while not is_done or not event_q.empty():
                while not event_q.empty():
                    msg_type, data = event_q.get()
                    if msg_type == "tasks":
                        # A node is starting: open a reasoning-trace card for it.
                        if "input" in data and data.get("name") in NODE_MESSAGES:
                            reset_stream()
                            yield _sse({'type': 'message', 'node': data['name'], 'content': NODE_MESSAGES[data['name']]})
                    elif msg_type == "updates":
                        for node_name, node_state in data.items():
                            if node_name.startswith("__") or not isinstance(node_state, dict):
                                continue
                            reset_stream()
                            for event in _node_events(session, node_name, node_state):
                                yield _sse(event)
                    elif msg_type == "error":
                        yield _sse({'type': 'message', 'node': 'Error', 'content': str(data)})
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
                        yield _sse({'type': 'message', 'node': 'progress', 'content': prog_arg})

                    if prog_val and prog_val != last_progress.get("val"):
                        last_progress["val"] = prog_val
                        yield _sse({'type': 'message', 'node': 'progress', 'content': prog_val})

                    # Emit granular sub-step cards
                    if sub_step and sub_step != last_progress.get("sub_step"):
                        last_progress["sub_step"] = sub_step
                        last_progress["stream_len"] = 0  # reset stream for new sub-step
                        if thread_id in active_progress:
                            active_progress[thread_id]["current_stream_text"] = ""
                        yield _sse({'type': 'sub_step', 'title': sub_step})

                    # Stream LLM text to frontend – send only new characters since last poll
                    last_len = last_progress.get("stream_len", 0)
                    if stream_text and len(stream_text) > last_len:
                        new_chunk = stream_text[last_len:]
                        last_progress["stream_len"] = len(stream_text)
                        yield _sse({'type': 'stream_text', 'chunk': new_chunk, 'full': stream_text})

                await asyncio.sleep(0.05)

            yield _sse({'type': 'done', 'pending_changes': pending_changes(session.get("state") or {})})
        except Exception as e:
            yield _sse({'type': 'message', 'node': 'Error', 'content': str(e)})

    return StreamingResponse(event_generator(), media_type="text/event-stream")


def _busy(session) -> Optional[JSONResponse]:
    if session is None:
        return JSONResponse(status_code=404, content={"error": "Session not found"})
    if session["running"]:
        return JSONResponse(status_code=409, content={"error": "The care plan is still being generated."})
    return None


@app.get("/api/chat/state/{thread_id}")
async def get_session_state(thread_id: str):
    session = sessions.get(thread_id)
    if session is None:
        return JSONResponse(status_code=404, content={"error": "Session not found"})
    payload = client_payload(session["state"] or {})
    service = get_memory_service()
    if service is not None and service.reflection_status(thread_id):
        payload["memory_reflection"] = service.reflection_status(thread_id)
    return {"running": session["running"], **payload}


@app.post("/api/chat/action/{thread_id}")
async def handle_action(thread_id: str, req: ActionRequest):
    session = sessions.get(thread_id)
    blocked = _busy(session)
    if blocked is not None:
        return blocked

    state = session["state"]
    ensure_argument_ids(state)
    action = req.action.lower().strip()
    chat: ChatMemory = session["chat"]

    if action == "accept":
        state["human_review_complete"] = True
        session["next_input"] = None  # resume the paused graph
        graph.update_state(session["cfg"], {
            "human_review_complete": True,
            "arguments": state["arguments"],
            "human_ops_log": state.get("human_ops_log") or [],
            "next_arg_seq": state.get("next_arg_seq") or 0,
        })
        chat.add_event(f"Clinician accepted the arguments after {len(state.get('human_ops_log') or [])} change(s).")
        return {"status": "ok"}

    arguments = state["arguments"]
    target = find_argument(arguments, req.arg_id)
    if target is None and req.target_id is not None and 0 <= req.target_id < len(arguments):
        target = arguments[req.target_id]

    if action == "remove" and target is not None and target.human_status != "rejected":
        target.human_status = "rejected"
        target.rejection_reason = req.reason
        record_human_op(state, "reject", target, origin="table", reason=req.reason)
        chat.add_event(f"Clinician removed {target.arg_id}: {clip_text(target.content, 120)}")
    elif action == "restore" and target is not None and target.human_status == "rejected":
        if is_human_authored(target):
            target.human_status = "added"
        else:
            target.human_status = "edited" if target.original_content is not None else "unreviewed"
        target.rejection_reason = None
        record_human_op(state, "restore", target, origin="table")
        chat.add_event(f"Clinician restored {target.arg_id}.")
    elif action == "modify" and target is not None and req.new_content and req.new_content != target.content:
        before = target.content
        if target.original_content is None:
            target.original_content = before
        target.content = req.new_content
        if target.human_status not in ("added",):
            target.human_status = "edited"
        record_human_op(state, "edit", target, origin="table", before=before)
        chat.add_event(f"Clinician edited {target.arg_id}: {clip_text(req.new_content, 120)}")
    elif action == "add" and req.new_content:
        options = state.get("handling_options") or [""]
        new_arg = Argument(
            content=req.new_content,
            argument_type="attack" if req.new_type in ("attack", "challenge") else "support",
            parent_option=resolve_option(options, req.new_option) or options[0],
            agent_role=req.new_role or "Clinician",
            source="human",
            human_status="added",
        )
        new_arg.arg_id = new_arg_id(state)
        arguments.append(new_arg)
        record_human_op(state, "add", new_arg, origin="table")
        chat.add_event(f"Clinician added {new_arg.arg_id} ({new_arg.argument_type}): {clip_text(new_arg.content, 120)}")

    return {"status": "ok", "arguments": arguments_payload(state), "pending_changes": pending_changes(state)}


@app.post("/api/chat/regenerate/{thread_id}")
async def regenerate_plan(thread_id: str, req: RegenerateRequest):
    """Re-enter the graph to apply the clinician's contestation of the plan."""
    session = sessions.get(thread_id)
    blocked = _busy(session)
    if blocked is not None:
        return blocked
    state = session["state"]
    if not state.get("care_plan_versions"):
        return JSONResponse(status_code=400, content={"error": "No care plan yet: accept the arguments first."})
    feedback = [item.model_dump() for item in req.feedback if item.text.strip()]
    mode = "feedback" if feedback else "contest"
    session["next_input"] = {
        "run_mode": mode,
        "plan_feedback": feedback,
        "feedback_ops": [],
        "arguments": state["arguments"],
        "human_ops_log": state.get("human_ops_log") or [],
        "next_arg_seq": state.get("next_arg_seq") or 0,
        "care_plan_versions": state.get("care_plan_versions") or [],
        "human_review_complete": True,
    }
    chat: ChatMemory = session["chat"]
    for item in feedback:
        anchor = f" on {item['section_id']}" if item.get("section_id") else ""
        chat.add_event(f"Clinician feedback{anchor}: {clip_text(item['text'], 160)}")
    chat.add_event(f"Regeneration requested ({len(feedback)} feedback item(s), {pending_changes(state)} table change(s)).")
    return {"status": "ok", "mode": mode}


def _approval_outcomes(state: Dict[str, Any]) -> Dict[str, str]:
    """Usage outcomes for the memory used in an approved plan."""
    arguments = state.get("arguments") or []
    outcomes: Dict[str, str] = {}
    contested_agents = any(arg.source == "agent" and arg.human_status == "rejected" for arg in arguments)
    if not contested_agents:
        for records in (state.get("memory_guidance") or {}).values():
            for record in records:
                outcomes.setdefault(record["memory_id"], "successful")
    for arg in arguments:
        if arg.source == "memory" and arg.memory_id:
            outcomes[arg.memory_id] = "contested" if arg.human_status in ("rejected", "edited") else "successful"
    return outcomes


@app.post("/api/chat/approve/{thread_id}")
async def approve_plan(thread_id: str, req: ApproveRequest):
    session = sessions.get(thread_id)
    blocked = _busy(session)
    if blocked is not None:
        return blocked
    state = session["state"]
    versions = state.get("care_plan_versions") or []
    if not versions:
        return JSONResponse(status_code=400, content={"error": "No care plan to approve."})
    number = req.version or versions[-1]["version"]
    plan = next((version for version in versions if version["version"] == number), None)
    if plan is None:
        return JSONResponse(status_code=404, content={"error": f"Version {number} not found."})
    plan["status"] = "approved"
    plan["approved_at"] = now_iso()
    if number == versions[-1]["version"]:
        state["revised_care_plan"] = plan
        service = get_memory_service()
        if service is not None:
            service.record_outcomes(thread_id, _approval_outcomes(state))
            # Fold the outcomes into usage statistics without blocking the response.
            service.consolidate_in_background()
    session["chat"].add_event(f"Clinician approved care plan v{number}.")
    return {"status": "ok", "care_plan": state.get("revised_care_plan"), "versions": versions}


@app.get("/api/care-plan/{thread_id}/pdf")
async def care_plan_pdf(thread_id: str, version: Optional[int] = None):
    from pdf_export import render_care_plan_pdf

    session = sessions.get(thread_id)
    if session is None:
        return JSONResponse(status_code=404, content={"error": "Session not found"})
    versions = (session["state"] or {}).get("care_plan_versions") or []
    plan = next((v for v in versions if v["version"] == version), None) if version else (versions[-1] if versions else None)
    if plan is None:
        return JSONResponse(status_code=404, content={"error": "No care plan available."})
    pdf = await asyncio.to_thread(render_care_plan_pdf, plan)
    filename = f"care-plan-v{plan['version']}.pdf"
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@app.post("/api/chat/message/{thread_id}")
async def send_chat_message(thread_id: str, req: ChatMessageRequest):
    """Stream a follow-up LLM response about the generated care plan.

    The prompt carries a compact encoding of every argument and of the current
    plan, plus a rolling summary of the conversation (see chat_context.py)."""
    session = sessions.get(thread_id)
    if not session:
        return {"error": "Session not found"}

    chat: ChatMemory = session["chat"]
    event_q: "queue.Queue" = queue.Queue()

    def worker():
        full = ""
        with session["chat_lock"]:
            try:
                prompt = chat.build_prompt(chat.case_context(session.get("state") or {}), req.message)
                stats = chat.stats(prompt)
                for chunk in call_llm_stream(prompt, temperature=0.7, max_tokens=1024):
                    full += chunk
                    event_q.put(("chunk", chunk, full))
                chat.add_turn("user", req.message)
                chat.add_turn("assistant", full)
                event_q.put(("done", stats, full))
                chat.compact(lambda summary_prompt: call_llm(summary_prompt, temperature=0.2, max_tokens=400))
            except Exception as e:
                event_q.put(("error", str(e), full))

    threading.Thread(target=worker, daemon=True).start()

    async def event_generator():
        while True:
            try:
                kind, data, full = event_q.get_nowait()
            except queue.Empty:
                await asyncio.sleep(0.03)
                continue
            if kind == "chunk":
                yield _sse({'type': 'stream_text', 'chunk': data, 'full': full})
            elif kind == "done":
                yield _sse({'type': 'message', 'node': 'bot', 'content': full})
                yield _sse({'type': 'done', 'context': data})
                return
            else:
                yield _sse({'type': 'error', 'content': data})
                return

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/api/memory")
async def memory_overview():
    service = get_memory_service()
    if service is None:
        return {"enabled": False}
    return {"enabled": True, **(await asyncio.to_thread(service.overview))}


@app.get("/api/memory/reflection/{thread_id}")
async def memory_reflection_status(thread_id: str):
    """Status of the background learning from this case's contestations."""
    service = get_memory_service()
    if service is None:
        return {"status": "disabled"}
    return service.reflection_status(thread_id) or {"status": "none"}


@app.post("/api/memory/consolidate")
async def memory_consolidate(req: ConsolidateRequest):
    service = get_memory_service()
    if service is None:
        return {"enabled": False}
    result = await asyncio.to_thread(service.consolidate, req.dry_run, req.retry_under_review)
    return {
        "enabled": True,
        "result": consolidation_summary(result),
        "events": [event.model_dump() for event in result.events][-100:],
        **(await asyncio.to_thread(service.overview)),
    }


@app.post("/api/memory/{memory_id}/review")
async def memory_review(memory_id: str, req: MemoryReviewRequest):
    service = get_memory_service()
    if service is None:
        return {"enabled": False}
    try:
        result = await asyncio.to_thread(service.review, memory_id, req.decision, req.note)
    except KeyError:
        return JSONResponse(status_code=404, content={"error": f"Memory {memory_id} not found."})
    except ValueError as e:
        return JSONResponse(status_code=400, content={"error": str(e)})
    return {"enabled": True, "result": result, **(await asyncio.to_thread(service.overview))}
