# Chen et al. 2026 — Rethinking MCP Security: A Large-Scale Study of Runtime MCP Servers and Security Scanner Reliability

> **Citation status: VERIFIED** (arXiv abstract fetched 2026-07-18).
> Canonical URL: <https://arxiv.org/abs/2607.11086>

**arXiv ID:** 2607.11086

**Title:** Rethinking MCP Security: A Large-Scale Study of Runtime MCP
Servers and Security Scanner Reliability

**Authors:** Pei Chen, Baichao An, Mengying Wu, Binwang Wan,
Geng Hong, Jinsong Chen, Xudong Pan, Jiarun Dai, Min Yang

**Year:** 2026

**Venue:** arXiv preprint

## Problem addressed

MCP servers are increasingly entrusted with security-sensitive
operations, but the community's understanding of their real-world
risk has been limited to static scanners applied to small samples.
This paper asks two questions: (i) what does the *runtime* MCP-server
ecosystem actually look like? (ii) how reliable are existing MCP
security scanners?

## Method

- Collected and analysed a large corpus of runtime MCP servers
  deployed in production-like settings.
- Benchmarked existing MCP security scanners against this corpus.
- Compared scanner-reported risks against observed runtime behaviors.

## Key results

- Existing scanners systematically *under*-report runtime risks
  because they reason about suspicious *semantic signals* rather
  than real execution behaviors.
- Many production MCP servers exhibit dangerous defaults (per the
  Phase 1 taxonomy: shared stdio, symlink-following resolvers,
  cache keys without tenant identity).
- Scanner reliability varies substantially across server
  implementations, undermining trust in scanner-only assurance.

## Relevance to MCP isolation research

This is one of the *most directly on-topic* papers for our work. It
empirically validates the threat model Phase 1 derived from spec
analysis: the vulnerabilities catalogued in `docs/02_Threat_Model.md`
appear at scale in real deployments. It also argues, in line with
our Phase 6 framework design, that *runtime* observation (not
static analysis) is necessary to characterise MCP isolation
failures.

## Open questions for our work

- How does the scanner-reliability finding generalise to
  multi-tenant settings (the original paper appears single-tenant)?
- Does the runtime-observation methodology scale to >1000 concurrent
  tenants, as our Phase 9 experiments plan?
- Can we reproduce the scanner under-reporting finding against our
  vulnerable vs. secure reference servers?