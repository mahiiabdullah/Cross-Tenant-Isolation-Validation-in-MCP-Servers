"""Fixture tenant datasets for the vulnerable reference server.

Phase-8 Code-Gen Rule: no real PII; only synthetic strings.
"""

from __future__ import annotations

TENANT_A_DOCS: dict[str, str] = {
    "doc_a1.txt": "Tenant A — document 1 (synthetic).",
    "doc_a2.txt": "Tenant A — document 2 (synthetic).",
}

TENANT_B_DOCS: dict[str, str] = {
    "doc_b1.txt": "Tenant B — document 1 (synthetic).",
    "doc_b2.txt": "Tenant B — document 2 (synthetic).",
}


def fixtures() -> dict[str, dict[str, str]]:
    """Return the bundled tenant fixtures."""
    return {
        "tenant-A": TENANT_A_DOCS,
        "tenant-B": TENANT_B_DOCS,
    }


__all__ = ["TENANT_A_DOCS", "TENANT_B_DOCS", "fixtures"]