"""Minimal HMAC-SHA256 JWT mint/verify with audience binding.

Stdlib-only (no PyJWT dep). Sufficient for in-process reference
servers; **not** a substitute for a real JWT library in
production. Phase 8 ships this; Phase 9 may swap for PyJWT.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Any


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


@dataclass
class JWT:
    header: dict[str, Any]
    payload: dict[str, Any]
    signature: bytes


class JWTError(Exception):
    """JWT verification failed."""


def mint_jwt(
    secret: str,
    audience: str,
    tenant_id: str,
    session_id: str,
    ttl_seconds: int = 3600,
) -> str:
    """Mint a HS256 JWT with the given claims."""
    header = {"alg": "HS256", "typ": "JWT"}
    now = int(time.time())
    payload = {
        "iss": "mcp-iso-research",
        "aud": audience,
        "iat": now,
        "exp": now + ttl_seconds,
        "tenant_id": tenant_id,
        "session_id": session_id,
    }
    h_b64 = _b64url_encode(json.dumps(header, sort_keys=True).encode())
    p_b64 = _b64url_encode(json.dumps(payload, sort_keys=True).encode())
    signing_input = f"{h_b64}.{p_b64}".encode("ascii")
    sig = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    return f"{h_b64}.{p_b64}.{_b64url_encode(sig)}"


def verify_jwt(token: str, secret: str, expected_audience: str) -> dict[str, Any]:
    """Verify ``token`` and return its payload if valid."""
    try:
        h_b64, p_b64, s_b64 = token.split(".")
    except ValueError as exc:
        raise JWTError("malformed token") from exc

    signing_input = f"{h_b64}.{p_b64}".encode("ascii")
    expected_sig = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    actual_sig = _b64url_decode(s_b64)
    if not hmac.compare_digest(expected_sig, actual_sig):
        raise JWTError("bad signature")

    payload = json.loads(_b64url_decode(p_b64))
    if payload.get("aud") != expected_audience:
        raise JWTError(f"audience mismatch: {payload.get('aud')!r}")
    if payload.get("exp", 0) < int(time.time()):
        raise JWTError("token expired")
    return payload


__all__ = ["JWT", "JWTError", "mint_jwt", "verify_jwt"]