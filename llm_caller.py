import json
import requests
import sys
from env_config import OLLAMA_BASE_URL, OLLAMA_MODEL


def call_llm(
    prompt: str, temperature: float = 0.7, max_tokens: int = 50000
) -> str:
    """Make a call to Ollama generation API"""
    try:
        print(f"DEBUG [call_llm] prompt_len={len(prompt)} max_tokens={max_tokens} temp={temperature}", file=sys.stderr)
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "think": True,  
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                }
            }
        )
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
