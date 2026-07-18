"""Tests for mcp_servers.secure.server."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from framework.core.errors import ManifestError, TransportError  # noqa: E402
from mcp_servers.secure.keys import JWTError, mint_jwt, verify_jwt  # noqa: E402
from mcp_servers.secure.manifest import load_manifest  # noqa: E402
from mcp_servers.secure.server import SecureServer, _canonical_path  # noqa: E402


def test_mint_and_verify_jwt_roundtrip() -> None:
    tok = mint_jwt("k", "aud", "tenant-A", "sess-1")
    payload = verify_jwt(tok, "k", "aud")
    assert payload["tenant_id"] == "tenant-A"
    assert payload["aud"] == "aud"


def test_verify_jwt_rejects_bad_signature() -> None:
    tok = mint_jwt("k", "aud", "tenant-A", "sess-1")
    with __import__("pytest").raises(JWTError):
        verify_jwt(tok, "wrong-key", "aud")


def test_verify_jwt_rejects_wrong_audience() -> None:
    tok = mint_jwt("k", "aud", "tenant-A", "sess-1")
    with __import__("pytest").raises(JWTError):
        verify_jwt(tok, "k", "other-aud")


def test_secure_server_constructs() -> None:
    s = SecureServer()
    assert s is not None


def test_secure_list_tools_empty_without_token() -> None:
    s = SecureServer()
    assert s.list_tools("") == []


def test_secure_list_tools_with_valid_token() -> None:
    s = SecureServer()
    tok = s.mint_token("tenant-A", "sess-1")
    tools = s.list_tools(tok)
    assert {t["name"] for t in tools} >= {"echo", "scratchpad_write", "scratchpad_read", "cache_lookup", "fetch_url"}


def test_secure_call_tool_per_tenant_scratchpad() -> None:
    s = SecureServer()
    tok_a = s.mint_token("tenant-A", "sess-A")
    tok_b = s.mint_token("tenant-B", "sess-B")
    s.call_tool(tok_a, "scratchpad_write", {"key": "secret", "value": "AAA"})
    s.call_tool(tok_b, "scratchpad_write", {"key": "secret", "value": "BBB"})
    out_a = s.call_tool(tok_a, "scratchpad_read", {"key": "secret"})
    out_b = s.call_tool(tok_b, "scratchpad_read", {"key": "secret"})
    assert out_a == {"result": {"value": "AAA"}}
    assert out_b == {"result": {"value": "BBB"}}


def test_secure_cache_key_includes_prompt_hash() -> None:
    s = SecureServer()
    tok = s.mint_token("tenant-A", "sess-1")
    s.call_tool(tok, "cache_lookup", {"tool": "t", "q": "alpha"})
    s.call_tool(tok, "cache_lookup", {"tool": "t", "q": "beta"})
    # Two distinct prompt_hashes -> two distinct cache entries.
    state = s._tenants["tenant-A"]
    assert len(state.cache) == 2


def test_secure_fetch_url_allowlist() -> None:
    s = SecureServer()
    tok = s.mint_token("tenant-A", "sess-1")
    bad = s.call_tool(tok, "fetch_url", {"url": "http://evil.example/"})
    assert "error" in bad["result"]
    good = s.call_tool(tok, "fetch_url", {"url": "https://allowed.example/x"})
    assert "result" in good


def test_secure_resource_rejects_path_escape(tmp_path: Path) -> None:
    s = SecureServer()
    tok = s.mint_token("tenant-A", "sess-1")
    s.set_fixtures_root("tenant-A", tmp_path)
    bad = s.read_resource(tok, "file:///../etc/passwd")
    assert "error" in bad


def test_secure_resource_rejects_symlink(tmp_path: Path) -> None:
    import os
    if not hasattr(os, "symlink") or os.name == "nt":
        pytest.skip("symlinks require elevated privileges on Windows")
    s = SecureServer()
    tok = s.mint_token("tenant-A", "sess-1")
    target = tmp_path / "real.txt"
    target.write_text("data")
    link = tmp_path / "link.txt"
    link.symlink_to(target)
    s.set_fixtures_root("tenant-A", tmp_path)
    bad = s.read_resource(tok, f"file:///{link.name}")
    assert "error" in bad


def test_canonical_path_rejects_escape(tmp_path: Path) -> None:
    with __import__("pytest").raises(TransportError):
        _canonical_path(tmp_path, Path("../etc/passwd"))


def test_load_manifest_default() -> None:
    m = load_manifest(Path(__file__).resolve().parents[1] / "mcp_servers" / "secure" / "manifest.json")
    assert "echo" in m.tool_names()


def test_load_manifest_missing_file(tmp_path: Path) -> None:
    with __import__("pytest").raises(ManifestError):
        load_manifest(tmp_path / "nope.json")