"""RunConfig schema for the MCP isolation framework.

Loaded from YAML. Validated by pydantic. Consumed by
``framework.scheduler.scheduler.Scheduler``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, field_validator

from framework.core.types import Boundary


class RunSettings(BaseModel):
    seed: int = 42
    repeats: int = 1
    concurrency: int = 4


class TenantConfig(BaseModel):
    id: str
    name: str = "unnamed"
    allowed_tools: list[str] = Field(default_factory=list)
    allowed_resources: list[str] = Field(default_factory=list)


class AttackRef(BaseModel):
    """A reference to an attack registered in ``attacks.REGISTRY``."""

    id: str
    parameters: dict[str, str] = Field(default_factory=dict)

    @field_validator("id")
    @classmethod
    def _id_format(cls, v: str) -> str:
        if not v.startswith("A-") or len(v.split("-")) != 3:
            raise ValueError(
                f"attack id must be of form 'A-PREFIX-NNN' (got {v!r})"
            )
        return v


class Defenses(BaseModel):
    per_tenant_tool_registry: bool = False
    tenant_prefixed_cache_keys: bool = False
    resource_path_canonicalisation: bool = False
    mtls: bool = False


class TargetConfig(BaseModel):
    transport: Literal["stdio", "http_sse", "streamable_http", "dummy"] = "dummy"
    command: str | None = None
    url: str | None = None
    token: str | None = None


class OutputConfig(BaseModel):
    log_dir: Path = Path("experiments/logs")
    output_dir: Path = Path("experiments/outputs")
    log_format: Literal["jsonl"] = "jsonl"


class RunConfig(BaseModel):
    """Top-level experiment configuration."""

    run: RunSettings = Field(default_factory=RunSettings)
    tenants: list[TenantConfig] = Field(default_factory=list)
    attacks: list[AttackRef] = Field(default_factory=list)
    defenses: Defenses = Field(default_factory=Defenses)
    target: TargetConfig = Field(default_factory=TargetConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)

    @field_validator("tenants")
    @classmethod
    def _at_least_two_tenants(cls, v: list[TenantConfig]) -> list[TenantConfig]:
        if len(v) < 2:
            raise ValueError(
                "RunConfig requires at least 2 tenants to detect cross-tenant leakage."
            )
        return v

    @classmethod
    def from_yaml(cls, path: str | Path) -> "RunConfig":
        """Load and validate a YAML config file."""
        text = Path(path).read_text(encoding="utf-8")
        data = yaml.safe_load(text)
        return cls.model_validate(data)

    @classmethod
    def example(cls) -> "RunConfig":
        """Return the canonical Phase-6 smoke-test example."""
        return cls(
            run=RunSettings(seed=42, repeats=1, concurrency=2),
            tenants=[
                TenantConfig(id="tenant-A", name="Alice"),
                TenantConfig(id="tenant-B", name="Bob"),
            ],
            attacks=[
                AttackRef(id="A-TRN-S"),
                AttackRef(id="A-CCH-T"),
            ],
            defenses=Defenses(per_tenant_tool_registry=False),
            target=TargetConfig(transport="dummy"),
        )


def attacks_by_boundary(cfg: RunConfig) -> dict[Boundary, list[AttackRef]]:
    """Group attack refs by their inferred boundary from the id prefix."""
    out: dict[Boundary, list[AttackRef]] = {b: [] for b in Boundary}
    for ref in cfg.attacks:
        prefix = ref.id.split("-")[1]
        for b in Boundary:
            if b.value.upper()[:3] == prefix:
                out[b].append(ref)
                break
    return out


__all__ = [
    "AttackRef",
    "Defenses",
    "OutputConfig",
    "RunConfig",
    "RunSettings",
    "TargetConfig",
    "TenantConfig",
    "attacks_by_boundary",
]