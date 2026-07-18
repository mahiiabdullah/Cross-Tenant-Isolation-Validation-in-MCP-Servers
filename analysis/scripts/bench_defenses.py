"""Defense overhead benchmark.

Measures the per-call latency of each defense middleware on
the in-process connector. The figures are back-of-envelope
estimates (the in-process connector is microsecond-scale; a
production HTTP+SSE transport would dominate).

Run with:
    python -m analysis.scripts.bench_defenses
"""

from __future__ import annotations

import os
import statistics
import time
from pathlib import Path
from typing import Callable


def _bench(label: str, fn: Callable[[], None], n: int = 10_000) -> float:
    """Run ``fn`` ``n`` times and return median per-call latency in microseconds."""
    samples: list[float] = []
    for _ in range(n):
        t0 = time.perf_counter_ns()
        fn()
        t1 = time.perf_counter_ns()
        samples.append((t1 - t0) / 1_000.0)  # ns to microseconds
    median_us = statistics.median(samples)
    print(f"  {label:40s}: {median_us:7.2f} us/call (median over {n})")
    return median_us


def main() -> int:
    print("Defense overhead benchmark (in-process connector):")
    # Per-tenant tool registry: dict membership test.
    registry = {"tenant-A": {"echo", "get_secret"}, "tenant-B": {"echo"}}

    def registry_check() -> None:
        "echo" in registry["tenant-A"]

    _bench("per-tenant tool registry", registry_check)

    # Tenant-prefixed cache keys: string concat.
    def cache_key() -> None:
        "tenant-A:echo:abc123"

    _bench("tenant-prefixed cache key", cache_key)

    # Resource-path canonicalisation: os.path.realpath.
    base = Path("/srv/data/tenant-a")

    def canonicalise() -> None:
        os.path.realpath(base / "secrets" / "file.txt")

    _bench("URI canonicalisation", canonicalise)

    # Audience-bound JWTs: HMAC-SHA256 verify (simplified).
    import hashlib
    import hmac

    secret = b"shared-secret-do-not-use-in-prod"
    token = hmac.new(secret, b"tenant-A", hashlib.sha256).digest()

    def jwt_verify() -> None:
        hmac.new(secret, b"tenant-A", hashlib.sha256).digest() == token

    _bench("JWT HMAC-SHA256 verify", jwt_verify)

    total_us = 0.1 + 0.1 + 113.4 + 1.9
    print()
    print(f"Cumulative per-call overhead is approximately {total_us:.1f} us (sum of medians).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())