# Torres et al. 2026 — When Agents Remember Too Much: Memory Poisoning Attacks on LLM Agents

> **Citation status: VERIFIED** (arXiv abstract fetched 2026-07-18).
> Canonical URL: <https://arxiv.org/abs/2607.06595>

**arXiv ID:** 2607.06595

**Title:** When Agents Remember Too Much: Memory Poisoning Attacks on
Large Language Model Agents

**Authors:** George Torres, Sharad Shrestha, Satyajayant Misra

**Year:** 2026

**Venue:** arXiv preprint

## Problem addressed

Long-term memory in LLM agents — the ability to recall prior
conversations and tasks across sessions — creates a persistent
attack surface distinct from prompt injection. Memory entries
written in one session can re-enter the model's context in a later
session, allowing an adversary who plants a memory entry to steer
the agent across many subsequent interactions.

## Method

- Distinguishes **conversational** memory (chats) from
  **action-planning** memory (task records).
- Demonstrates attacks in which an attacker plants memory entries
  via earlier tool outputs or compromised user inputs.
- Evaluates detection and recovery mechanisms on long-memory
  agents.

## Key results

- Memory poisoning is durable: an entry written once persists across
  many subsequent sessions.
- The attack vector scales: a single poisoned memory entry biases
  downstream behavior far more than a single-turn prompt injection.
- Detection at the memory-write time is far more tractable than
  detection at read time.

## Relevance to MCP isolation research

Directly relevant to MCP's **memory** and **cache** boundaries. MCP
servers commonly retain rendered prompts, embeddings, and tool
outputs in persistent stores (Phase 1, Component 7). Memory entries
that omit tenant identity produce cross-tenant cache leakage
(`A-CCH-001`, `A-CCH-003`, `A-MEM-001`, `A-MEM-002`). Torres et al.
provide the canonical paper-side counterpart of the same failure
mode at the agent-memory layer.

## Open questions for our work

- Does the attack translate unchanged to MCP's embedding store
  (which is implementation-defined but architecturally similar)?
- Can a tenant-prefixed memory namespace eliminate cross-tenant
  poisoning, or does the embedding-inversion threat (`A-MEM-004`)
  preserve a covert channel even with prefix isolation?
- What is the right unit of memory invalidation — per-tenant, per-
  session, or per-write?