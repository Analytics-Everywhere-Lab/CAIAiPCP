"""Runtime LLM provider settings, editable from the web UI.

The pipeline runs on a local Ollama model by default; Settings can switch it to
the Claude API. Settings persist to data/settings.json (gitignored, readable by
the owner only). The API key never leaves the server in full: the browser only
sees whether a key is set and its last four characters. Without a saved key the
ANTHROPIC_API_KEY environment variable is used.
"""
import json
import os
import re
import tempfile
import threading
from dataclasses import asdict, dataclass, replace
from typing import Any, Dict, Optional
from urllib.parse import urlparse

from env_config import OLLAMA_BASE_URL, OLLAMA_MODEL, PROJECT_ROOT

PROVIDERS = ("ollama", "anthropic")
EFFORTS = ("auto", "low", "medium", "high")
DEFAULT_CLAUDE_MODEL = "claude-opus-5-5"
CLAUDE_MODELS = [
    {"id": "claude-opus-5-5", "label": "Claude Opus 5.5", "note": "Recommended: strongest reasoning for care planning"},
    {"id": "claude-sonnet-5-5", "label": "Claude Sonnet 5.5", "note": "Faster and lower cost"},
    {"id": "claude-haiku-5-5", "label": "Claude Haiku 5.5", "note": "Fastest and cheapest; lighter reasoning"},
    {"id": "claude-fable-5-1", "label": "Claude Fable 5.1", "note": "Highest capability tier, highest cost"},
]
_MODEL_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{1,99}$")


def settings_path() -> str:
    return os.environ.get("SETTINGS_PATH", os.path.join(PROJECT_ROOT, "data", "settings.json"))


@dataclass(frozen=True)
class LLMSettings:
    provider: str = os.environ.get("LLM_PROVIDER", "ollama")
    ollama_base_url: str = OLLAMA_BASE_URL
    ollama_model: str = OLLAMA_MODEL
    anthropic_model: str = os.environ.get("ANTHROPIC_MODEL", DEFAULT_CLAUDE_MODEL)
    anthropic_effort: str = "auto"
    anthropic_api_key: str = ""

    def api_key(self) -> str:
        return self.anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY", "")

    def active_model(self) -> str:
        return self.anthropic_model if self.provider == "anthropic" else self.ollama_model


_lock = threading.Lock()
_settings: Optional[LLMSettings] = None


def _load() -> LLMSettings:
    defaults = LLMSettings()
    try:
        with open(settings_path(), encoding="utf-8") as handle:
            stored = json.load(handle)
    except (OSError, ValueError):
        return defaults
    known = {key: value for key, value in stored.items() if key in asdict(defaults) and isinstance(value, str)}
    try:
        return validate(defaults, known)
    except ValueError:
        return defaults


def get_settings() -> LLMSettings:
    global _settings
    with _lock:
        if _settings is None:
            _settings = _load()
        return _settings


def reset_settings_cache() -> None:
    """Forget the in-memory copy so the next read comes from disk (tests, CLI)."""
    global _settings
    with _lock:
        _settings = None


def validate(base: LLMSettings, patch: Dict[str, Any]) -> LLMSettings:
    """Apply a partial update. A key of None leaves the field unchanged; an empty
    API key clears the saved one."""
    changes = {key: value for key, value in patch.items() if value is not None}
    unknown = set(changes) - set(asdict(base))
    if unknown:
        raise ValueError(f"Unknown setting: {', '.join(sorted(unknown))}")
    for key, value in changes.items():
        if not isinstance(value, str):
            raise ValueError(f"{key} must be a string")
        changes[key] = value.strip()
    if changes.get("provider", base.provider) not in PROVIDERS:
        raise ValueError("Provider must be 'ollama' or 'anthropic'")
    if changes.get("anthropic_effort", base.anthropic_effort) not in EFFORTS:
        raise ValueError(f"Effort must be one of {', '.join(EFFORTS)}")
    for key in ("ollama_model", "anthropic_model"):
        if key in changes and not _MODEL_ID.match(changes[key]):
            raise ValueError("Model names may only contain letters, digits and . _ : / -")
    if "ollama_base_url" in changes:
        url = urlparse(changes["ollama_base_url"])
        if url.scheme not in ("http", "https") or not url.netloc:
            raise ValueError("The Ollama URL must start with http:// or https://")
        changes["ollama_base_url"] = changes["ollama_base_url"].rstrip("/")
    key = changes.get("anthropic_api_key")
    if key and (len(key) < 20 or any(ch.isspace() for ch in key)):
        raise ValueError("That does not look like an Anthropic API key")
    return replace(base, **changes)


def update_settings(patch: Dict[str, Any]) -> LLMSettings:
    global _settings
    updated = validate(get_settings(), patch)
    with _lock:
        _save(updated)
        _settings = updated
    return updated


def _save(settings: LLMSettings) -> None:
    path = settings_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    handle, temp_path = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".settings-")
    try:
        os.chmod(temp_path, 0o600)  # the file can hold an API key
        with os.fdopen(handle, "w", encoding="utf-8") as out:
            json.dump(asdict(settings), out, indent=2)
        os.replace(temp_path, path)
    except BaseException:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise


def key_hint(key: str) -> str:
    return f"…{key[-4:]}" if key else ""


def public_view(settings: Optional[LLMSettings] = None) -> Dict[str, Any]:
    """Everything the UI needs, without the API key itself."""
    settings = settings or get_settings()
    data = asdict(settings)
    data.pop("anthropic_api_key")
    source = "settings" if settings.anthropic_api_key else ("environment" if settings.api_key() else None)
    data.update({
        "anthropic_key_set": bool(settings.api_key()),
        "anthropic_key_hint": key_hint(settings.api_key()),
        "anthropic_key_source": source,
        "active_model": settings.active_model(),
        "claude_models": CLAUDE_MODELS,
        "efforts": list(EFFORTS),
    })
    return data
