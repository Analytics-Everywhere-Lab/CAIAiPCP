"""The Claude API provider and the runtime settings behind it, with a scripted client."""
import json
import os
import re
from dataclasses import replace
from types import SimpleNamespace as NS

import pytest
from fastapi.testclient import TestClient

import llm_caller
from llm_caller import JSON_SYSTEM_PROMPT, LLMError, call_llm, claude_request, provider_status, stream_text
from llm_settings import LLMSettings
from tests.fake_ollama import FakeOllama
from tests.test_api_flow import PATIENT, of_type, sse_events

KEY = "sk-ant-api03-" + "a" * 40 + "WXYZ"


class FakeStream:
    def __init__(self, events, message):
        self.events, self.message = events, message

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def __iter__(self):
        return iter(self.events)

    def get_final_message(self):
        return self.message


def text_events(text):
    return [NS(type="text", text=piece) for piece in re.findall(r"\S+\s*|\s+", text)]


def final(stop_reason="end_turn", model="claude-opus-5-5", category=None):
    usage = NS(input_tokens=120, output_tokens=30, cache_read_input_tokens=0, cache_creation_input_tokens=0)
    return NS(stop_reason=stop_reason, model=model, usage=usage,
              stop_details=NS(category=category) if category else None)


def fallback_block(source="claude-opus-5-5", target="claude-opus-5"):
    return NS(type="content_block_start", content_block=NS(type="fallback", from_=NS(model=source), to=NS(model=target)))


class FakeClaude:
    """Stands in for anthropic.Anthropic; answers with the scripted Ollama responses."""

    def __init__(self, script=None):
        self.requests = []
        self.script = script or self.scripted
        self.beta = NS(messages=NS(stream=self.stream))
        self.models = NS(retrieve=lambda model_id: NS(id=model_id, display_name="Claude Opus 5.5"))

    @staticmethod
    def prompt_text(request):
        content = request["messages"][0]["content"]
        return content if isinstance(content, str) else "".join(block["text"] for block in content)

    def scripted(self, request):
        return text_events(FakeOllama().respond(self.prompt_text(request))), final()

    def stream(self, **request):
        self.requests.append(request)
        events, message = self.script(request)
        return FakeStream(events, message)


@pytest.fixture
def claude(monkeypatch, llm_settings):
    fake = FakeClaude()

    def client_for(api_key):
        if not api_key:
            raise LLMError("No Claude API key is set.")
        return fake

    monkeypatch.setattr(llm_caller, "_claude_client", client_for)
    llm_settings.update_settings({"provider": "anthropic", "anthropic_api_key": KEY})
    return fake


@pytest.fixture
def client():
    from api import app

    return TestClient(app)


def test_claude_requests_follow_the_current_api():
    settings = LLMSettings(provider="anthropic", anthropic_model="claude-opus-5-5", anthropic_api_key=KEY)
    short = claude_request(settings, "Severity?", max_tokens=10)
    assert "temperature" not in short and "thinking" not in short  # rejected / adaptive by default
    assert short["max_tokens"] == 256 + llm_caller.CLAUDE_THINKING_ALLOWANCE  # room to think before a short label
    assert short["output_config"] == {"effort": "low"}  # "auto" effort: quick checks run at low effort
    assert short["betas"] == ["server-side-fallback-2026-07-01"] and short["fallbacks"] == "default"
    assert short["messages"] == [{"role": "user", "content": "Severity?"}]

    long = claude_request(settings, "Write the plan", max_tokens=60000)
    assert long["max_tokens"] == llm_caller.CLAUDE_MAX_TOKENS and "output_config" not in long

    assert claude_request(replace(settings, anthropic_effort="high"), "x", 10)["output_config"] == {"effort": "high"}
    haiku = claude_request(replace(settings, anthropic_model="claude-haiku-5-5"), "x", 10)
    assert "fallbacks" not in haiku and "betas" not in haiku  # no server-side fallback for Haiku
    assert "output_config" not in claude_request(replace(settings, anthropic_model="custom-gateway-model"), "x", 10)
    assert claude_request(settings, "x", 10, response_format="json")["system"] == JSON_SYSTEM_PROMPT

    prefix = "CASE CONTEXT " * 200
    cached = claude_request(settings, prefix + "\nUser: Why?", 100, cache_prefix=prefix)["messages"][0]["content"]
    assert cached[0] == {"type": "text", "text": prefix, "cache_control": {"type": "ephemeral"}}
    assert cached[1]["text"] == "\nUser: Why?"
    small = claude_request(settings, "short\nUser: Why?", 100, cache_prefix="short")["messages"][0]["content"]
    assert small == "short\nUser: Why?"  # below the cacheable minimum: sent as plain text


def test_fallback_replaces_text_from_the_declined_model(claude):
    claude.script = lambda request: (
        text_events("Partial answer from the first model ") + [fallback_block()] + text_events("Complete answer."),
        final(model="claude-opus-5"),
    )
    snapshots = list(stream_text("Explain", max_tokens=500))
    assert "" in snapshots and snapshots[-1] == "Complete answer."
    assert provider_status()["last_fallback"]["to"] == "claude-opus-5"
    assert call_llm("Explain", max_tokens=500) == "Complete answer."
    assert provider_status()["usage"]["claude-opus-5"]["calls"] == 2


def test_refusal_is_reported_not_returned(claude):
    claude.script = lambda request: (text_events("Partial text"), final(stop_reason="refusal", category="bio"))
    assert call_llm("Question", max_tokens=100) == ""
    assert "declined" in provider_status()["last_error"]["message"]
    assert "bio" in provider_status()["last_error"]["message"]
    with pytest.raises(LLMError):
        list(stream_text("Question", max_tokens=100, raise_errors=True))


def test_settings_api_masks_the_key_and_saves_it_privately(client, llm_settings, monkeypatch):
    view = client.get("/api/settings").json()
    assert view["provider"] == "ollama" and view["anthropic_key_set"] is False
    assert "anthropic_api_key" not in view and view["claude_models"][0]["id"] == "claude-opus-5-5"

    saved = client.put("/api/settings", json={"provider": "anthropic", "anthropic_api_key": KEY})
    assert saved.status_code == 200 and KEY not in saved.text
    assert saved.json()["anthropic_key_hint"] == "…WXYZ" and saved.json()["active_model"] == "claude-opus-5-5"
    path = os.environ["SETTINGS_PATH"]
    assert os.stat(path).st_mode & 0o777 == 0o600
    assert json.load(open(path))["anthropic_api_key"] == KEY

    assert client.put("/api/settings", json={"provider": "openai"}).status_code == 400
    assert client.put("/api/settings", json={"ollama_base_url": "file:///etc/passwd"}).status_code == 400
    assert client.put("/api/settings", json={"anthropic_api_key": "short"}).status_code == 400

    cleared = client.put("/api/settings", json={"anthropic_api_key": ""}).json()
    assert cleared["anthropic_key_set"] is False
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-env-" + "b" * 30)
    assert client.get("/api/settings").json()["anthropic_key_source"] == "environment"


def test_connection_check_does_not_save(client, monkeypatch, claude):
    response = NS(raise_for_status=lambda: None, json=lambda: {"models": [{"name": "gemma4:latest"}]})
    monkeypatch.setattr(llm_caller.requests, "get", lambda url, timeout=None: response)
    checked = client.post("/api/settings/test", json={"provider": "ollama", "ollama_model": "gemma4"}).json()
    assert checked["ok"] and "gemma4:latest" in checked["models"]
    missing = client.post("/api/settings/test", json={"provider": "ollama", "ollama_model": "llama9"}).json()
    assert not missing["ok"] and "ollama pull llama9" in missing["message"]
    assert client.get("/api/settings").json()["provider"] == "anthropic"  # testing never saves

    assert client.post("/api/settings/test", json={}).json() == {
        "ok": True, "message": "Connected. Claude Opus 5.5 is available.", "model": "claude-opus-5-5"}


def test_care_plan_and_chat_run_on_claude(client, claude):
    thread_id = client.post("/api/chat/start", json={"patient_info": PATIENT}).json()["thread_id"]
    events = sse_events(client.get(f"/api/chat/stream/{thread_id}"))
    assert of_type(events, "review_needed")[0]["arguments"]
    client.post(f"/api/chat/action/{thread_id}", json={"action": "accept"})
    events = sse_events(client.get(f"/api/chat/stream/{thread_id}"))
    assert of_type(events, "final_plan")[0]["care_plan"]["sections"]
    assert not of_type(events, "provider_error")
    assert all("temperature" not in request for request in claude.requests)

    reply = sse_events(client.post(f"/api/chat/message/{thread_id}", json={"message": "Why grab bars?"}))
    assert of_type(reply, "message")[0]["content"].startswith("Argument A1")
    chat_request = claude.requests[-1]
    blocks = chat_request["messages"][0]["content"]
    assert blocks[0]["cache_control"] == {"type": "ephemeral"}  # the case context is cached
    assert "Why grab bars?" in blocks[1]["text"] and "Why grab bars?" not in blocks[0]["text"]


def test_provider_errors_reach_the_user(client, claude, llm_settings):
    llm_settings.update_settings({"anthropic_api_key": ""})
    thread_id = client.post("/api/chat/start", json={"patient_info": PATIENT}).json()["thread_id"]
    events = sse_events(client.get(f"/api/chat/stream/{thread_id}"))
    errors = of_type(events, "provider_error")
    assert errors and "No Claude API key" in errors[0]["content"]
    assert of_type(events, "done")
