# Zhu et al. 2025 — LSPFuzz: Hunting Bugs in Language Servers

> **Citation status: VERIFIED** (arXiv abstract fetched 2026-07-18).
> Canonical URL: <https://arxiv.org/abs/2510.00532>

**arXiv ID:** 2510.00532

**Title:** LSPFuzz: Hunting Bugs in Language Servers

**Authors:** Hengcheng Zhu, Songqiang Chen, Valerio Terragni,
Lili Wei, Yepang Liu, Jiarong Wu, Shing-Chi Cheung

**Year:** 2025

**Venue:** arXiv preprint

## Problem addressed

The Language Server Protocol (LSP) is the closest architectural
analogue to MCP: a JSON-RPC-based protocol between a host (editor)
and a language-specific server, with similar concerns around input
validation, resource access, and lifecycle management. This paper
applies property-based fuzzing to discover real bugs in production
LSP server implementations.

## Method

- Built **LSPFuzz**, a grammar-aware fuzzer that generates
  well-formed LSP messages and observes server behavior.
- Ran the fuzzer against ~300 LSP server implementations across
  many languages.
- Triaged discovered bugs into crashes, hangs, and resource-exhaustion
  classes.

## Key results

- Found numerous crashes, hangs, and resource-exhaustion bugs in
  widely-used LSP servers.
- Many bugs are *not* random input issues: they are triggered by
  well-formed-but-malicious LSP messages, mirroring the prompt-
  injection analogue.
- Vulnerability-pattern taxonomy transferable to other JSON-RPC
  protocols (i.e. MCP).

## Relevance to MCP isolation research

The architectural similarity between LSP and MCP makes LSPFuzz a
direct methodological precedent for our Phase 7 attack library.
LSP's 300+ server implementations are a useful *test corpus* for
analogous vulnerabilities in MCP servers — bugs that arise from
common JSON-RPC fuzzer triggers (malformed params, oversized
payloads, capability-negotiation confusion) are likely to have
MCP-side counterparts.

## Open questions for our work

- Can we adapt LSPFuzz's grammar to MCP's JSON-RPC surface and run
  it against the public MCP-server ecosystem?
- Which LSPFuzz bug classes (crashes, hangs, resource exhaustion)
  correspond to which Phase-1 MCP tickets?
- Does the *absence* of a publicly available MCP-server corpus
  (Chen et al. 2026 noted this gap) limit the breadth of our
  fuzzing campaign?