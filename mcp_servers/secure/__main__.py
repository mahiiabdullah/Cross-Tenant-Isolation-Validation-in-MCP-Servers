"""Run the secure server on stdio for manual smoke-testing."""

from __future__ import annotations

import json
import logging
import sys

from mcp_servers.secure.server import build_server

logger = logging.getLogger(__name__)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    server = build_server()
    logger.info("secure server ready; send newline-delimited JSON-RPC envelopes on stdin")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError as exc:
            print(json.dumps({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": str(exc)}}))
            continue
        method = req.get("method", "")
        params = req.get("params", {})
        req_id = req.get("id")
        token = params.get("__token__", "")
        if method == "tools/list":
            result = {"tools": server.list_tools(token)}
        elif method == "tools/call":
            name = params.get("name", "")
            arguments = params.get("arguments", {})
            result = server.call_tool(token, name, arguments)
        elif method == "resources/read":
            uri = params.get("uri", "")
            result = server.read_resource(token, uri)
        else:
            result = {"error": {"code": -32601, "message": f"unknown method {method!r}"}}
        print(json.dumps({"jsonrpc": "2.0", "id": req_id, "result": result}))
    return 0


if __name__ == "__main__":
    sys.exit(main())