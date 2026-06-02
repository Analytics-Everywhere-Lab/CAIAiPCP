"""Run the Authorization Code OAuth flow and persist tokens.json.

Usage:
    python scripts/login.py
"""
from __future__ import annotations

import secrets
import sys
import threading
import time
import webbrowser
from pathlib import Path

# Make src/ importable when running this file directly.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import uvicorn  # noqa: E402

from accuro_sample.callback_server import CallbackResult, build_app  # noqa: E402
from accuro_sample.config import get_settings  # noqa: E402
from accuro_sample.oauth import build_authorize_url  # noqa: E402


def main() -> None:
    settings = get_settings()
    state = secrets.token_urlsafe(24)
    done = threading.Event()
    result = CallbackResult()
    app = build_app(expected_state=state, done_event=done, result=result)

    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=settings.callback_port,
        log_level="warning",
    )
    server = uvicorn.Server(config)

    server_thread = threading.Thread(target=server.run, daemon=True)
    server_thread.start()

    # Wait briefly for the server to bind before opening the browser.
    for _ in range(50):
        if server.started:
            break
        time.sleep(0.05)

    authorize_url = build_authorize_url(state)
    print(f"Opening browser to:\n  {authorize_url}\n")
    webbrowser.open(authorize_url)

    print(f"Waiting for callback on http://127.0.0.1:{settings.callback_port}/oauth/callback ...")
    completed = done.wait(timeout=300)
    # Allow time for the HTML response to flush before shutting down uvicorn.
    time.sleep(0.5)
    server.should_exit = True
    server_thread.join(timeout=5)

    if not completed:
        print("\nTimed out after 5 minutes waiting for the OAuth callback.")
        sys.exit(1)
    if not result.ok:
        print(f"\nLogin failed: {result.error}")
        sys.exit(1)

    token_path = Path(settings.token_store_path)
    print(f"\nTokens saved to {token_path.resolve()}")


if __name__ == "__main__":
    main()
