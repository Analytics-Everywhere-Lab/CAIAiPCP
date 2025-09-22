import asyncio
import json
import threading
from typing import Dict, List, Any
from llm_caller import call_llm
import os

try:
    from langchain_mcp_adapters.client import MultiServerMCPClient
except ImportError:
    MultiServerMCPClient = None

_MCP_CLIENT = None
_MCP_TOOLS_CACHE = None


def _get_mcp_client():
    global _MCP_CLIENT
    if _MCP_CLIENT is None:
        mcp_url = os.environ.get("MCP_SERVER_URL", "http://localhost:8000/sse")
        _MCP_CLIENT = MultiServerMCPClient(
            {
                "Demo": {  # name of your server in mcp_server.py
                    "url": mcp_url,
                    "transport": "sse",
                }
            }
        )
    return _MCP_CLIENT


def _run_async_blocking(coro):
    """Run an async coroutine even if there’s already a running loop (e.g., Gradio)."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    # If we're already in an event loop, run in a separate thread
    result_container = {}

    def _runner():
        result_container["value"] = asyncio.run(coro)

    t = threading.Thread(target=_runner, daemon=True)
    t.start()
    t.join()
    return result_container.get("value")


def _load_tools():
    """Fetch and cache LC tool wrappers from the MCP client."""
    global _MCP_TOOLS_CACHE
    if _MCP_TOOLS_CACHE is not None:
        return _MCP_TOOLS_CACHE

    client = _get_mcp_client()

    async def _get():
        tools_obj = await client.get_tools()
        # Some versions return dict[server, List[Tool]], others a flat List[Tool]
        if isinstance(tools_obj, dict):
            flat = []
            for _server, lst in tools_obj.items():
                flat.extend(lst)
            return flat
        return tools_obj

    _MCP_TOOLS_CACHE = _run_async_blocking(_get())
    return _MCP_TOOLS_CACHE


def _get_tool(tool_name: str):
    """Find tool by name; supports fully qualified names like 'Demo:tool'."""
    for tool in _load_tools():
        n = getattr(tool, "name", "") or ""
        if n == tool_name or n.endswith(":" + tool_name):
            return tool
    raise RuntimeError(f"MCP tool not found: {tool_name}")


def _fetch_available_slots_for_provider(provider_name: str) -> List[Dict[str, Any]]:
    tool = _get_tool("get_available_booking_slots_for_provider")
    # Prefer sync invoke; fallback to async
    try:
        res = tool.invoke({"provider_name": provider_name})
    except Exception:
        res = _run_async_blocking(tool.ainvoke({"provider_name": provider_name}))

    # Normalize outputs
    try:
        if isinstance(res, str):
            parsed = json.loads(res)
            return parsed.get("result", parsed) if isinstance(parsed, dict) else parsed
        if isinstance(res, dict) and "result" in res:
            return res["result"]
        if isinstance(res, list):
            return res
    except Exception:
        pass
    return []


def _fetch_available_slots_for_roles(role: str) -> List[Dict[str, Any]]:
    """
    Fetch the earliest available booking slots for a given provider role.

    This wraps the `get_available_booking_slots_by_roles` tool exposed by the MCP server.
    It returns a list of dictionaries with keys `slot_number`, `provider_name`, and `time_slot`.
    """
    tool = _get_tool("get_available_booking_slots_by_roles")
    # Prefer synchronous invocation; fallback to asynchronous if necessary
    try:
        res = tool.invoke({"role": role})
    except Exception:
        res = _run_async_blocking(tool.ainvoke({"role": role}))

    # Normalize output to always return a list
    try:
        if isinstance(res, str):
            parsed = json.loads(res)
            return parsed.get("result", parsed) if isinstance(parsed, dict) else parsed
        if isinstance(res, dict) and "result" in res:
            return res["result"]
        if isinstance(res, list):
            return res
    except Exception:
        pass
    return []

