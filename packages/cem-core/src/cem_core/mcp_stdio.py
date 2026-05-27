from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, TextIO

from .kernel import CEM
from .mcp_tools import CEMMCPToolServer

MCP_PROTOCOL_VERSION = "2025-11-25"


def handle_jsonrpc_message(server: CEMMCPToolServer, message: dict[str, Any]) -> dict[str, Any] | None:
    request_id = message.get("id")
    method = message.get("method")
    if request_id is None:
        return None
    try:
        if method == "initialize":
            result = {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "cem-0", "version": "0.1.0"},
            }
            return _response(request_id, result)
        if method == "ping":
            return _response(request_id, {})
        if method == "tools/list":
            return _response(request_id, {"tools": server.list_tools()})
        if method == "tools/call":
            params = message.get("params") or {}
            result = server.call_tool(
                str(params["name"]),
                params.get("arguments") if isinstance(params.get("arguments"), dict) else {},
            )
            return _response(request_id, result)
        return _error(request_id, -32601, f"Method not found: {method}")
    except (KeyError, TypeError, ValueError) as exc:
        return _error(request_id, -32602, str(exc))
    except Exception as exc:
        return _error(request_id, -32000, str(exc))


def run_stdio_server(root: str | Path, *, stdin: TextIO | None = None, stdout: TextIO | None = None) -> None:
    input_stream = stdin or sys.stdin
    output_stream = stdout or sys.stdout
    server = CEMMCPToolServer(CEM(root))
    for line in input_stream:
        if not line.strip():
            continue
        response = handle_jsonrpc_message(server, json.loads(line))
        if response is None:
            continue
        output_stream.write(json.dumps(response, ensure_ascii=False) + "\n")
        output_stream.flush()


def _response(request_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": code, "message": message},
    }
