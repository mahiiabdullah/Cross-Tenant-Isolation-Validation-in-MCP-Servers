# Dipta et al. 2024 — Dynamic Frequency-Based Fingerprinting Attacks against Modern Sandbox Environments

> **Citation status: VERIFIED** (arXiv abstract fetched 2026-07-18).
> Canonical URL: <https://arxiv.org/abs/2404.10715>

**arXiv ID:** 2404.10715

**Title:** Dynamic Frequency-Based Fingerprinting Attacks against
Modern Sandbox Environments

**Authors:** Debopriya Roy Dipta, Thore Tiemann, Berk Gulmezoglu,
Eduard Marin, Thomas Eisenbarth

**Year:** 2024

**Venue:** arXiv preprint

## Problem addressed

Cloud sandboxes — containers (Docker, gVisor), microVMs (Firecracker),
and TEEs (Intel SGX, AMD SEV) — share physical hardware across
tenants. Even when sandboxing is correctly enforced at the access-
control layer, residual hardware state (CPU frequency, cache lines,
memory access patterns) can be observed across sandbox boundaries,
creating side-channel leakage. This paper characterises such leakage
in modern sandbox environments.

## Method

- Catalogued the sandboxing primitives (gVisor, Firecracker, SGX,
  SEV) and the side channels available in each.
- Implemented dynamic frequency-based fingerprinting attacks that
  infer workload characteristics across sandbox boundaries.
- Evaluated leakage rates across sandbox types.

## Key results

- All surveyed sandbox technologies exhibit non-trivial side-channel
  leakage under realistic workloads.
- The leakage is sufficient to fingerprint workload types
  (e.g. distinguishing "ML inference" from "web serving") across
  sandbox boundaries, even when logical isolation is intact.
- Defenses based on constant-time execution are insufficient against
  dynamic frequency attacks.

## Relevance to MCP isolation research

The MCP multi-tenant threat model assumes that *logical* isolation
(transport, session, namespace, tool, resource, memory, cache, auth)
is sufficient. Dipta et al. show that *physical* side channels
remain a covert channel even when logical isolation is perfect.
For our Phase 5 STRIDE enumeration, the **Information Disclosure**
column at every boundary must include physical side channels as a
residual leakage source.

## Open questions for our work

- Do our Phase 9 experiments measure side-channel leakage, or only
  logical leakage? (Current scope is logical; side channels are a
  threat-model limitation we should disclose honestly.)
- Can the per-tenant microVM defense (analogous to Firecracker)
  reduce side-channel leakage to acceptable levels for MCP?