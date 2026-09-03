# Week 25 Research Corpus — Context Engineering as a discipline

> Phase 7 — Supplementary Electives (Weeks 25–29)  
> **Status:** COMPLETE (deep pass)  
> Raw research corpus (not textbook). Legal sources only.

This directory is the **Phase 7 elective Week 25** research repository. It is **not** a replacement for Weeks 1–24. Suggested slot: after Phase 3 (Week 15), before Evals (Phase 4) — or append after the Week 24 capstone. Read concept files in order, then the source map.

| # | File | Concept |
|---|------|---------|
| 00 | [00-week-overview.md](00-week-overview.md) | Syllabus mapping: make context explicit; build a context-management layer |
| 01 | [01-context-vs-prompt-engineering.md](01-context-vs-prompt-engineering.md) | Actual distinction: prompts vs the full token set under a finite attention budget |
| 02 | [02-context-sources-and-layers.md](02-context-sources-and-layers.md) | Sources (system, tools, RAG, history, memory) and assembly layers |
| 03 | [03-memory-systems.md](03-memory-systems.md) | Short-term/session vs long-term/persistent; checkpointers vs stores |
| 04 | [04-context-compaction.md](04-context-compaction.md) | Summarizing / compressing history to stay under budget |
| 05 | [05-context-isolation.md](05-context-isolation.md) | Why one agent's context must not leak into another's |
| 06 | [06-multi-agent-context-sharing.md](06-multi-agent-context-sharing.md) | Sharing patterns: summaries, scratchpads, shared stores, handoff contracts |
| 07 | [07-context-failure-modes.md](07-context-failure-modes.md) | Stale context, poisoning, lost handoffs — Week 9–style taxonomy for context |
| — | [99-source-map.md](99-source-map.md) | Master URL / paper / blog / YouTube index |

## Completeness checklist (Week 25)

- [x] All syllabus Week 25 concepts covered with **7 required fields**  
- [x] **Context vs prompt engineering** — Anthropic “Effective context engineering for AI agents” (2025-09-29)  
- [x] **Context sources and layers** — system / tools / MCP / RAG / history / memory anatomy  
- [x] **Memory systems** — LangGraph checkpointers (short-term) vs stores (long-term); Claude Managed Agents memory stores  
- [x] **Context compaction** — Anthropic compaction + Claude Code `/compact`; OpenAI Responses `context_management` / `/responses/compact`  
- [x] **Context isolation** — sub-agents, Dual LLM (Willison), sandboxes, state schema isolation  
- [x] **Multi-agent context sharing** — Anthropic multi-agent research; summary-at-boundary patterns  
- [x] **Context failure modes** — Breunig (poisoning / distraction / confusion / clash); Lost in the Middle; OWASP / Willison injection  
- [x] Chip Huyen public blogs cited (agents, genai platform, open challenges)  
- [x] Liu et al. **Lost in the Middle** arXiv:2307.03172  
- [x] YouTube / talks: Chip Huyen AI Engineer keynote; Lamis Mukta (Anthropic) AI Native DevCon; Drew Breunig  
- [x] Build task documented: session memory + compaction threshold + isolation + failure-mode log  
- [x] Per-week research **directory** (not a single thin file)  
- [x] Phase 7 elective note: supplementary; can interleave after Week 15 or after capstone  

## Syllabus build task (Week 25)

Add an explicit **context-management layer** to the Phase 3 agentic stack (do not invent a new model API):

1. **Session memory** — persist thread/session state (messages + scratchpad fields). Compact (summarize / trim / clear tool results) when token count crosses a configured threshold.  
2. **Isolation** — separate context namespaces per agentic system (or per sub-agent). No accidental shared message lists across tenants or sibling agents.  
3. **Failure-mode log** — document incidents the way Week 9 documents RAG failures: stale context, context poisoning, lost context across handoffs (plus distraction / confusion / clash as subtypes). Join on `session_id` / `handoff_id`.

Do not skip this week for “we already have RAG and a system prompt.” Flagship systems do context work **implicitly**; this week makes the discipline **explicit** and measurable.

## Default path (synthesis)

1. Inventory every token source that lands in the window (system, tools, retrieved docs, history, memory mounts).  
2. Implement **write / select / compress / isolate** (LangChain framing) as named modules with traces.  
3. Set a **compaction threshold** (token or % of window) and evaluate fidelity before/after on long traces.  
4. Give each agent its own thread_id / memory namespace; pass only **summaries** across boundaries.  
5. Keep a portfolio **context failure log** paired with Week 9 RAG taxonomy and Week 15 agent evals.
