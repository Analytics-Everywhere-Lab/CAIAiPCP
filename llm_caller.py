import json
import re
import requests
import sys
from typing import Any, Optional
from env_config import OLLAMA_BASE_URL, OLLAMA_MODEL


def call_llm(
    prompt: str, temperature: float = 0.7, max_tokens: int = 50000,
    response_format: Optional[str] = None,
) -> str:
    """Make a call to Ollama generation API"""
    try:
        print(f"DEBUG [call_llm] prompt_len={len(prompt)} max_tokens={max_tokens} temp={temperature}", file=sys.stderr)
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "think": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }
        if response_format:
            # Ollama constrains decoding to valid JSON when format="json".
            payload["format"] = response_format
        response = requests.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload)
        response.raise_for_status()
        data = response.json()
        print(f"DEBUG [call_llm] raw keys={list(data.keys())} response_len={len(data.get('response',''))} done={data.get('done')} done_reason={data.get('done_reason')}", file=sys.stderr)
        if "error" in data:
            print(f"[ERROR] Ollama returned error: {data['error']}", file=sys.stderr)
            return ""
        result = data.get("response", "").strip()
        if not result:
            print(f"DEBUG [call_llm] WARNING: empty response. Full data: {data}", file=sys.stderr)
        return result

    except Exception as e:
        print(f"[ERROR] call_llm exception: {e}", file=sys.stderr)
        return ""


def call_llm_stream(
    prompt: str, temperature: float = 0.7, max_tokens: int = 50000
):
    """Stream responses from Ollama generation API"""
    try:
        print(f"DEBUG [call_llm_stream] prompt_len={len(prompt)} max_tokens={max_tokens} temp={temperature}", file=sys.stderr)
        print(f"DEBUG [call_llm_stream] Requesting {OLLAMA_BASE_URL}/api/generate with {OLLAMA_MODEL}...", file=sys.stderr)
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": True,
                "think": True,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                }
            },
            stream=True
        )
        response.raise_for_status()

        total_tokens = 0
        for line in response.iter_lines():
            if line:
                chunk = json.loads(line)
                if "error" in chunk:
                    print(f"\n[ERROR] Ollama stream error: {chunk['error']}", file=sys.stderr)
                    return
                if chunk.get("done"):
                    print(f"\nDEBUG [call_llm_stream] done_reason={chunk.get('done_reason')} total_tokens_yielded={total_tokens} eval_count={chunk.get('eval_count')} prompt_eval_count={chunk.get('prompt_eval_count')} chunk_keys={list(chunk.keys())}", file=sys.stderr)
                text = chunk.get("response", "")
                if text:
                    total_tokens += 1
                print(text, end='', file=sys.stderr, flush=True)
                yield text
        print(f"\nDEBUG [call_llm_stream] stream finished. total_tokens_yielded={total_tokens}\n", file=sys.stderr, flush=True)

    except Exception as e:
        print(f"[ERROR] call_llm_stream exception: {e}", file=sys.stderr)
        yield f" [Error: {e}]"


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
    """Call Ollama in JSON mode and parse the result.

    Returns None when no valid JSON comes back so callers can fall back to a
    deterministic path instead of failing the whole pipeline."""
    data = extract_json(call_llm(prompt, temperature=temperature, max_tokens=max_tokens, response_format="json"))
    if data is None:
        # Some models ignore or break under JSON mode; retry once in free-text mode.
        print("DEBUG [call_llm_json] JSON mode returned no valid JSON; retrying without format", file=sys.stderr)
        data = extract_json(call_llm(prompt, temperature=temperature, max_tokens=max_tokens))
    return data
