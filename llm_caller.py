"""LLM access for the whole pipeline: a local Ollama model or the Claude API.

The provider is read from the runtime settings (llm_settings.py) on every call,
so switching it in the UI takes effect for the next step without a restart.

Prefer ``stream_text`` for streaming: it yields the accumulated text, which
lets it drop output that a declined Claude model streamed before a server-side
fallback model took over the request.
"""
import json
import re
import sys
import threading
import time
from typing import Any, Dict, Iterator, Optional, Tuple

import requests

from llm_settings import LLMSettings, get_settings

try:  # Optional: only needed when the Claude API provider is selected.
    import anthropic
except ImportError:  # pragma: no cover - exercised only without the package
    anthropic = None

# Thinking on current Claude models counts toward max_tokens. Callers size
# max_tokens for the visible answer (a one-word label, a full care plan), so the
# Claude path adds room for adaptive thinking on top and caps the total.
CLAUDE_THINKING_ALLOWANCE = 8192
CLAUDE_MAX_TOKENS = 64000
# With effort "auto", short structured calls (labels, scores, search queries)
# run at low effort; longer writing uses the model's default effort.
AUTO_LOW_EFFORT_MAX_TOKENS = 512
# Prompt caching only pays off for prefixes above the API's minimum cacheable size.
MIN_CACHE_PREFIX_CHARS = 2048

# Models that accept output_config.effort, and those that support server-side
# refusal fallbacks (re-running a declined request on another model).
_EFFORT_MODEL_PREFIXES = (
    "claude-opus-5", "claude-sonnet-5", "claude-haiku-5", "claude-fable-5", "claude-mythos-5",
    "claude-opus-4-8", "claude-opus-4-7", "claude-opus-4-6", "claude-sonnet-4-6",
)
_FALLBACK_MODELS = {"claude-opus-5-5", "claude-opus-5", "claude-sonnet-5-5", "claude-fable-5-1", "claude-fable-5"}
FALLBACK_BETA = "server-side-fallback-2026-07-01"
JSON_SYSTEM_PROMPT = "Respond with a single valid JSON value and nothing else: no prose before or after it, no code fences."


class LLMError(RuntimeError):
    """A provider failed or declined; the message is safe to show to the user."""


# ---------------------------------------------------------------- status

_status_lock = threading.Lock()
_status: Dict[str, Any] = {"last_error": None, "last_fallback": None, "usage": {}}


def _record_error(settings: LLMSettings, message: str) -> None:
    print(f"[ERROR] LLM ({settings.provider}): {message}", file=sys.stderr)
    with _status_lock:
        _status["last_error"] = {"provider": settings.provider, "model": settings.active_model(),
                                 "message": message, "at": time.time()}


def _record_usage(model: str, usage: Any) -> None:
    with _status_lock:
        totals = _status["usage"].setdefault(model, {"calls": 0, "input_tokens": 0, "output_tokens": 0,
                                                     "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0})
        totals["calls"] += 1
        for key in ("input_tokens", "output_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"):
            totals[key] += getattr(usage, key, None) or 0


def provider_status() -> Dict[str, Any]:
    with _status_lock:
        return json.loads(json.dumps(_status))


def clear_status() -> None:
    with _status_lock:
        _status.update({"last_error": None, "last_fallback": None, "usage": {}})


def describe_error(exc: BaseException) -> str:
    if anthropic is not None:
        if isinstance(exc, anthropic.AuthenticationError):
            return "The Claude API rejected the API key."
        if isinstance(exc, anthropic.PermissionDeniedError):
            return "This API key is not allowed to use the selected Claude model."
        if isinstance(exc, anthropic.NotFoundError):
            return "The selected Claude model was not found. Pick another model."
        if isinstance(exc, anthropic.RateLimitError):
            return "The Claude API rate limit was reached. Wait a moment and try again."
        if isinstance(exc, anthropic.APIConnectionError):
            return "Could not reach the Claude API. Check the network connection."
        if isinstance(exc, anthropic.APIStatusError):
            return f"Claude API error {exc.status_code}: {getattr(exc, 'message', exc)}"
    if isinstance(exc, requests.ConnectionError):
        return "Could not reach Ollama. Is it running at the configured URL?"
    return str(exc) or exc.__class__.__name__


# ---------------------------------------------------------------- Ollama

def _ollama_payload(settings: LLMSettings, prompt: str, temperature: float, max_tokens: int, stream: bool,
                    response_format: Optional[str] = None) -> Dict[str, Any]:
    payload = {
        "model": settings.ollama_model,
        "prompt": prompt,
        "stream": stream,
        "think": True,
        "options": {"temperature": temperature, "num_predict": max_tokens},
    }
    if response_format:
        # Ollama constrains decoding to valid JSON when format="json".
        payload["format"] = response_format
    return payload


def _ollama_complete(settings: LLMSettings, prompt: str, temperature: float, max_tokens: int,
                     response_format: Optional[str]) -> str:
    response = requests.post(f"{settings.ollama_base_url}/api/generate",
                             json=_ollama_payload(settings, prompt, temperature, max_tokens, False, response_format))
    response.raise_for_status()
    data = response.json()
    if "error" in data:
        raise LLMError(f"Ollama returned an error: {data['error']}")
    print(f"DEBUG [call_llm] response_len={len(data.get('response', ''))} done_reason={data.get('done_reason')}", file=sys.stderr)
    return data.get("response", "").strip()


def _ollama_events(settings: LLMSettings, prompt: str, temperature: float, max_tokens: int) -> Iterator[Tuple[str, str]]:
    response = requests.post(f"{settings.ollama_base_url}/api/generate",
                             json=_ollama_payload(settings, prompt, temperature, max_tokens, True), stream=True)
    response.raise_for_status()
    for line in response.iter_lines():
        if not line:
            continue
        chunk = json.loads(line)
        if "error" in chunk:
            raise LLMError(f"Ollama stream error: {chunk['error']}")
        if chunk.get("done"):
            print(f"DEBUG [stream] done_reason={chunk.get('done_reason')} eval_count={chunk.get('eval_count')} "
                  f"prompt_eval_count={chunk.get('prompt_eval_count')}", file=sys.stderr)
        text = chunk.get("response", "")
        if text:
            yield "text", text


# ---------------------------------------------------------------- Claude

_clients: Dict[str, Any] = {}


def _claude_client(api_key: str):
    if anthropic is None:
        raise LLMError("The 'anthropic' package is not installed. Run: pip install anthropic")
    if not api_key:
        raise LLMError("No Claude API key is set.")
    with _status_lock:
        if api_key not in _clients:
            _clients.clear()  # keep at most one client; the key changed
            _clients[api_key] = anthropic.Anthropic(api_key=api_key)
        return _clients[api_key]


def claude_effort(setting: str, model: str, max_tokens: int) -> Optional[str]:
    if not model.startswith(_EFFORT_MODEL_PREFIXES):
        return None
    if setting == "auto":
        return "low" if max_tokens <= AUTO_LOW_EFFORT_MAX_TOKENS else None
    return setting


def _claude_content(prompt: str, cache_prefix: Optional[str]):
    """Split off a stable prefix (the chat's case context) as a cached block, so
    follow-up questions re-read it from the prompt cache at a fraction of the cost."""
    if cache_prefix and len(cache_prefix) >= MIN_CACHE_PREFIX_CHARS and prompt.startswith(cache_prefix):
        rest = prompt[len(cache_prefix):]
        if rest.strip():
            return [
                {"type": "text", "text": cache_prefix, "cache_control": {"type": "ephemeral"}},
                {"type": "text", "text": rest},
            ]
    return prompt


def claude_request(settings: LLMSettings, prompt: str, max_tokens: int, response_format: Optional[str] = None,
                   cache_prefix: Optional[str] = None) -> Dict[str, Any]:
    """Keyword arguments for client.beta.messages.stream.

    Sampling temperature is not sent: current Claude models reject it. Thinking
    is left at the model default (adaptive on current models)."""
    model = settings.anthropic_model
    request: Dict[str, Any] = {
        "model": model,
        "max_tokens": min(CLAUDE_MAX_TOKENS, max(max_tokens, 256) + CLAUDE_THINKING_ALLOWANCE),
        "messages": [{"role": "user", "content": _claude_content(prompt, cache_prefix)}],
    }
    effort = claude_effort(settings.anthropic_effort, model, max_tokens)
    if effort:
        request["output_config"] = {"effort": effort}
    if response_format == "json":
        request["system"] = JSON_SYSTEM_PROMPT
    if model in _FALLBACK_MODELS:
        # If a safety classifier declines a request, the API re-runs it on the
        # fallback model Anthropic recommends for that category, in the same call.
        request["betas"] = [FALLBACK_BETA]
        request["fallbacks"] = "default"
    return request


def _claude_events(settings: LLMSettings, prompt: str, max_tokens: int, response_format: Optional[str] = None,
                   cache_prefix: Optional[str] = None) -> Iterator[Tuple[str, str]]:
    client = _claude_client(settings.api_key())
    request = claude_request(settings, prompt, max_tokens, response_format, cache_prefix)
    with client.beta.messages.stream(**request) as stream:
        for event in stream:
            if event.type == "content_block_start" and event.content_block.type == "fallback":
                block = event.content_block
                with _status_lock:
                    _status["last_fallback"] = {"from": block.from_.model, "to": block.to.model, "at": time.time()}
                # The text streamed so far came from the model that declined; the
                # fallback model answers the whole request again.
                yield "reset", ""
            elif event.type == "text":
                yield "text", event.text
        message = stream.get_final_message()
    _record_usage(message.model, message.usage)
    if message.stop_reason == "refusal":
        category = getattr(message.stop_details, "category", None) if message.stop_details else None
        yield "reset", ""
        raise LLMError("Claude declined this request" + (f" ({category})." if category else "."))


# ---------------------------------------------------------------- public API

def _events(prompt: str, temperature: float, max_tokens: int, response_format: Optional[str] = None,
            cache_prefix: Optional[str] = None) -> Iterator[Tuple[str, str]]:
    settings = get_settings()
    print(f"DEBUG [llm] provider={settings.provider} model={settings.active_model()} prompt_len={len(prompt)} "
          f"max_tokens={max_tokens}", file=sys.stderr)
    if settings.provider == "anthropic":
        return _claude_events(settings, prompt, max_tokens, response_format, cache_prefix)
    return _ollama_events(settings, prompt, temperature, max_tokens)


def stream_text(prompt: str, temperature: float = 0.7, max_tokens: int = 50000, cache_prefix: Optional[str] = None,
                raise_errors: bool = False) -> Iterator[str]:
    """Stream a completion, yielding the accumulated text after each chunk.

    On failure the stream ends after recording the error (see provider_status),
    or raises LLMError when raise_errors is set."""
    text = ""
    settings = get_settings()
    try:
        for kind, delta in _events(prompt, temperature, max_tokens, cache_prefix=cache_prefix):
            text = "" if kind == "reset" else text + delta
            yield text
    except Exception as exc:
        message = exc.args[0] if isinstance(exc, LLMError) else describe_error(exc)
        _record_error(settings, message)
        if raise_errors:
            raise LLMError(message) from exc


def call_llm(
    prompt: str, temperature: float = 0.7, max_tokens: int = 50000,
    response_format: Optional[str] = None, cache_prefix: Optional[str] = None,
) -> str:
    """Complete a prompt; returns "" on failure so callers can fall back."""
    settings = get_settings()
    try:
        if settings.provider != "anthropic":
            return _ollama_complete(settings, prompt, temperature, max_tokens, response_format)
        # Claude requests are streamed even here: long completions would
        # otherwise hit request timeouts.
        text = ""
        for kind, delta in _claude_events(settings, prompt, max_tokens, response_format, cache_prefix):
            text = "" if kind == "reset" else text + delta
        return text.strip()
    except Exception as exc:
        _record_error(settings, exc.args[0] if isinstance(exc, LLMError) else describe_error(exc))
        return ""


def call_llm_stream(prompt: str, temperature: float = 0.7, max_tokens: int = 50000):
    """Yield text deltas (legacy interface; prefer stream_text).

    A Claude fallback restart is marked with a blank line rather than retracted."""
    previous = ""
    for text in stream_text(prompt, temperature=temperature, max_tokens=max_tokens):
        if text.startswith(previous):
            delta = text[len(previous):]
        else:
            delta = "\n\n" + text
        previous = text
        if delta:
            yield delta


def test_connection(settings: LLMSettings) -> Dict[str, Any]:
    """Check that the provider is reachable and the model exists, without generating text."""
    try:
        if settings.provider == "anthropic":
            info = _claude_client(settings.api_key()).models.retrieve(settings.anthropic_model)
            return {"ok": True, "message": f"Connected. {info.display_name} is available.", "model": info.id}
        response = requests.get(f"{settings.ollama_base_url}/api/tags", timeout=5)
        response.raise_for_status()
        models = [model.get("name", "") for model in response.json().get("models", [])]
        wanted = settings.ollama_model
        found = wanted in models or f"{wanted}:latest" in models
        message = (f"Connected. {wanted} is available." if found
                   else f"Connected to Ollama, but {wanted} is not pulled. Run: ollama pull {wanted}")
        return {"ok": found, "message": message, "models": models}
    except Exception as exc:
        return {"ok": False, "message": exc.args[0] if isinstance(exc, LLMError) else describe_error(exc)}


def extract_json(text: str) -> Optional[Any]:
    """Parse the first JSON object or array in an LLM response.

    Handles markdown code fences, leading prose and trailing commas, which local
    models produce often enough that every structured step needs this."""
    if not text:
        return None
    cleaned = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", cleaned, re.DOTALL)
    if fence:
        cleaned = fence.group(1).strip()
    for candidate in (cleaned, _first_json_block(cleaned)):
        if not candidate:
            continue
        for attempt in (candidate, re.sub(r",\s*([}\]])", r"\1", candidate)):
            try:
                return json.loads(attempt)
            except json.JSONDecodeError:
                continue
    return None


def _first_json_block(text: str) -> Optional[str]:
    """Return the first balanced {...} or [...] block, ignoring brackets inside strings."""
    start = next((i for i, ch in enumerate(text) if ch in "{["), None)
    if start is None:
        return None
    closing = {"{": "}", "[": "]"}
    stack = []
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        ch = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch in closing:
            stack.append(closing[ch])
        elif stack and ch == stack[-1]:
            stack.pop()
            if not stack:
                return text[start:index + 1]
    return None


def call_llm_json(
    prompt: str, temperature: float = 0.2, max_tokens: int = 4096
) -> Optional[Any]:
    """Call the LLM in JSON mode and parse the result.

    Returns None when no valid JSON comes back so callers can fall back to a
    deterministic path instead of failing the whole pipeline."""
    data = extract_json(call_llm(prompt, temperature=temperature, max_tokens=max_tokens, response_format="json"))
    if data is None:
        # Some models ignore or break under JSON mode; retry once in free-text mode.
        print("DEBUG [call_llm_json] JSON mode returned no valid JSON; retrying without format", file=sys.stderr)
        data = extract_json(call_llm(prompt, temperature=temperature, max_tokens=max_tokens))
    return data
