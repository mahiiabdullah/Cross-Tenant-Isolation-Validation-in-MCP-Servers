# 03 — Literature Prompt

> **Phase 3.** Conduct a rigorous literature review across AI Agent Security,
> Multi-Tenant Cloud Isolation, Prompt Injection, and Tool Security — without
> hallucinating citations.

## Strict Constraint

> Do NOT invent citations. Only use verifiable, published work. If there is no
> exact paper on MCP cross-tenant isolation, state so explicitly and pivot to
> the closest analogue (LangChain security, multi-tenant LLM isolation, RPC
> isolation history, etc.).

## Deliverable 1 — Literature Matrix

Markdown table with the columns:

```
| Paper Title | Authors & Year | Venue | Core Problem | Methodology |
Key Findings | Relevance to our MCP Research |
```

Provide **at least 10 highly relevant, real-world papers**. For each row, link
to a PDF stored under `literature/papers/` and a summary under
`literature/summaries/`.

## Deliverable 2 — Synthesis & Gap Analysis

- Cluster the existing work into research areas.
- List the exact unanswered questions in the current literature.
- Explicitly map out the **Research Gap** that this project fills.

## Workflow

1. Search arXiv, IACR, USENIX, ACM, IEEE, NDSS, IEEE S&P for related work.
2. For each paper: download to `literature/papers/`, write summary in
   `literature/summaries/`, add an entry to `literature/spreadsheet.xlsx`
   (planned).
3. Cross-link from `literature/related_work.md`.
4. Highlight papers where MCP itself is the subject, separately from
   analogue domains.

## Summary File Format

Each `literature/summaries/<key>.md` must contain:

- Problem addressed.
- Method.
- Key results.
- Relevance to MCP isolation research.
- Open questions for our work.

## Done When

- [ ] ≥10 verifiable papers catalogued.
- [ ] Every paper has a PDF + summary + spreadsheet row.
- [ ] `literature/related_work.md` cites every paper once.
- [ ] Research gap is stated in one sentence and reproduced in `docs/01_Research_Gap.md`.
