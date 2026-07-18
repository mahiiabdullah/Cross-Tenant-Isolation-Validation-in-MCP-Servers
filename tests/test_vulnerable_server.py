"""Tests for mcp_servers.vulnerable.server."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from mcp_servers.vulnerable.server import (  # noqa: E402
    VulnFlags,
    VulnerableServer,
)


def test_vuln_flags_default_all_on() -> None:
    f = VulnFlags()
    assert f.dynamic_tools and f.follow_symlinks and f.no_auth_list
    assert f.shared_cache_key and f.shared_transport


def test_vuln_flags_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VULN_DYNAMIC_TOOLS", "0")
    monkeypatch.setenv("VULN_FOLLOW_SYMLINKS", "false")
    monkeypatch.setenv("VULN_NO_AUTH_LIST", "no")
    f = VulnFlags()
    assert not f.dynamic_tools
    assert not f.follow_symlinks
    assert not f.no_auth_list


def test_vulnerable_server_constructs() -> None:
    s = VulnerableServer()
    assert s is not None


def test_vulnerable_list_tools_has_defaults() -> None:
    s = VulnerableServer()
    tools = s.list_tools()
    names = {t["name"] for t in tools}
    assert {"echo", "scratchpad_write", "scratchpad_read", "cache_lookup", "fetch_url"} <= names


def test_dynamic_tool_registration_with_flag() -> None:
    s = VulnerableServer(flags=VulnFlags(dynamic_tools=True))
    s.register_tool("ping", lambda args: {"pong": args})
    assert "ping" in {t["name"] for t in s.list_tools()}


def test_dynamic_tool_registration_blocked_without_flag() -> None:
    s = VulnerableServer(flags=VulnFlags(dynamic_tools=False))
    with __import__("pytest").raises(PermissionError):
        s.register_tool("ping", lambda args: {"pong": args})


def test_call_tool_as_deliberately_ignores_tenant() -> None:
    """The shared-transport flag means tenant_id is not used."""
    s = VulnerableServer(flags=VulnFlags(shared_transport=True))
    r = s.call_tool_as("tenant-A", "echo", {"x": 1})
    assert r == {"result": {"echo": {"x": 1}}}


def test_shared_cache_key_omits_prompt_hash() -> None:
    """With the vuln flag on, two calls with different 'q' hit the same cache key."""
    s = VulnerableServer(flags=VulnFlags(shared_cache_key=True))
    s.call_tool_as("tenant-A", "cache_lookup", {"tool": "t", "q": "alpha"})
    s.call_tool_as("tenant-A", "cache_lookup", {"tool": "t", "q": "beta"})
    # Both calls hit the same cache entry.
    assert ("cache", "t") in s._worker.cache