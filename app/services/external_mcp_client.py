from __future__ import annotations

import atexit
import json
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any


class ExternalMCPClient:
    """Simple JSON-RPC client for the local finance_mcp_server.py process."""

    def __init__(self):
        self._process: subprocess.Popen[str] | None = None
        self._request_id = 0
        self._lock = threading.Lock()
        self._server_path = Path(__file__).resolve().parents[2] / "finance_mcp_server.py"
        atexit.register(self.close)

    def list_tools(self) -> list[dict[str, Any]]:
        response = self._request("tools/list")
        return response.get("result", {}).get("tools", [])

    def call_tool(self, tool: str, args: dict[str, Any] | None = None) -> dict[str, Any]:
        response = self._request("tools/call", {"name": tool, "arguments": args or {}})
        if "error" in response:
            return {"error": response["error"]}
        return response.get("result", {})

    def close(self) -> None:
        with self._lock:
            if self._process is None:
                return
            if self._process.poll() is None:
                self._process.terminate()
                try:
                    self._process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self._process.kill()
            self._process = None

    def _request(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        with self._lock:
            process = self._ensure_process()
            self._request_id += 1
            payload = {
                "jsonrpc": "2.0",
                "id": self._request_id,
                "method": method,
                "params": params or {},
            }
            assert process.stdin is not None
            assert process.stdout is not None
            process.stdin.write(json.dumps(payload) + "\n")
            process.stdin.flush()
            line = process.stdout.readline()
            if not line:
                stderr_output = ""
                if process.stderr is not None:
                    stderr_output = process.stderr.read()
                raise RuntimeError(f"External MCP server stopped responding. {stderr_output}".strip())
            return json.loads(line)

    def _ensure_process(self) -> subprocess.Popen[str]:
        if self._process is not None and self._process.poll() is None:
            return self._process

        self._process = subprocess.Popen(
            [sys.executable, str(self._server_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self._initialize()
        return self._process

    def _initialize(self) -> None:
        process = self._process
        if process is None:
            return
        assert process.stdin is not None
        assert process.stdout is not None
        self._request_id += 1
        payload = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": "initialize",
            "params": {},
        }
        process.stdin.write(json.dumps(payload) + "\n")
        process.stdin.flush()
        process.stdout.readline()
