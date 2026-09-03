# 00 — Week overview & syllabus mapping

> Week 25 — Context Engineering as a discipline  
> Phase 7 elective (supplementary). Suggested after Phase 3 / before Evals.  
> Research notes (raw).

---

## Fundamentals

Week 25 makes **context engineering** an explicit curriculum discipline. Flagship agent stacks already do it implicitly: RAG packs evidence, agents accumulate tool results, checkpointers resume threads, memory stores persist preferences. The elective forces those mechanisms into one vocabulary and one build surface.

**Prompt engineering** (Week 5 spine) is how you write and version instructions. **Context engineering** is how you curate *everything* that consumes the model's finite attention budget on each inference turn — system instructions, tool schemas, MCP metadata, retrieved documents, message history, scratchpads, and long-term memories (Anthropic, *Effective context engineering for AI agents*, 2025-09-29).

Karpathy (via LangChain's framing): fill the context window with **just the right information for the next step**. Anthropic's guiding principle: the **smallest set of high-signal tokens** that maximizes the likelihood of the desired outcome. Chip Huyen frames the same problem as **context construction** — gathering the information a model needs for a query, whether via RAG, tools, or memory (*Building a Generative AI Platform*; *Agents*).

Why it is distinct from “just longer windows”:

| Observation | Implication |
|-------------|-------------|
| **Context rot** (Anthropic) — recall accuracy degrades as token count rises | Treat context as a scarce resource, not free storage |
| **Lost in the Middle** (Liu et al., arXiv:2307.03172) — U-shaped position sensitivity | Order and packing matter as much as inclusion |
| **Distraction ceilings** (Breunig; Gemini Pokémon agent anecdote ~100k) | Agents can fail *before* the hard window limit |
| **Attention is n²** (transformer pairwise) | Every token taxes every other token |

Syllabus concepts map to files 01–07. The **build** is a context-management layer: session memory that **compacts** past a token threshold; **isolation** between agentic systems; a **failure-mode log** analogous to Week 9's RAG taxonomy.

**Suggested placement:** after Week 15 (agent evaluation) so students have loops, tools, multi-agent, and traces — before or alongside Phase 4 evals flywheels. Alternatively append after Week 24. It does **not** replace Weeks 1–24.

---

## Alternatives & Tradeoffs

| Path | What you optimize | What you sacrifice |
|------|-------------------|-------------------|
| Stay in “prompt engineering only” | Familiar Week 5 tooling | Blind to history/tool/RAG bloat; wrong owner when failures are packing |
| “Just buy a 1M window” | Less summarization code | Cost, latency, rot, distraction; still need selection |
| Implicit RAG+agent state (no named layer) | Ships faster | Cannot A/B compaction; cannot isolate tenants cleanly |
| **Explicit context layer** (this week) | Measurable write/select/compress/isolate | Extra modules, thresholds, eval harness |
| Full multi-agent from day one | Parallel exploration | 3–15× tokens; coordination tax (Anthropic research system) |

| Build scope | Pros | Cons |
|-------------|------|------|
| Compaction only | Immediate budget relief | Does not stop cross-agent leak |
| Isolation only | Tenant/agent safety | Long threads still rot |
| **Compaction + isolation + failure log** (syllabus) | Complete elective artifact | Needs traces + golden long sessions |

---

## Necessity

Concrete failure modes if Week 25 is skipped:

- Teams “fix the system prompt” when the bug is **stale retrieved policy**, **poisoned memory**, or **handoff that dropped constraints**.  
- Session cost explodes because raw tool JSON accumulates forever — no compaction threshold.  
- Multi-tenant demos share one message list; Agent A’s PII or secrets appear in Agent B’s window.  
- Compaction fires too late (at hard limit) when the model is already at peak **context rot** — Anthropic: model is least intelligent when forced to compact.  
- Week 9 RAG failures and Week 15 trajectory failures get no sibling taxonomy for **context** failures (poisoning, distraction, clash).  
- Interview / FDE narrative cannot explain *why* Claude Code subagents, LangGraph stores, or Responses compaction exist.

Without this week, “context” remains a vibes word. With it, context is an engineered budget with owners, thresholds, and failure codes.

---

## Industry Practice

- **Common (demo AI):** dump full chat + all tool results + top-k RAG into one prompt; raise `max_tokens` when it breaks. One global memory blob for all users.  
- **Strong:** inventory context anatomy; version system prompts separately from dynamic packs; checkpointer per `thread_id`; store per `user_id` namespace; compact at a **threshold** (Claude Code ~95% default / override; OpenAI `compact_threshold`); clear old tool results; isolate subagent windows and return 1–2k summaries.  
- **FDE bar:** quote Anthropic context vs prompt distinction; cite LangGraph checkpointer vs store; name Breunig’s four failure modes + Lost-in-the-Middle; show a failure log with `session_id`, token counts before/after compact, and handoff payload hashes; refuse “we have a million tokens so we’re fine.”

Production references: Anthropic engineering post + Managed Agents memory docs; LangGraph persistence; OpenAI Responses compaction; Claude Code session management blog; LangChain write/select/compress/isolate.

---

## Concrete Scenario

**Anthropic — Effective context engineering for AI agents** (published 2025-09-29):  
https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents

The Applied AI team defines context engineering as curating the optimal token set during inference (beyond prompt wording), documents **context rot**, and elaborates three long-horizon strategies used in production agents: **compaction**, **structured note-taking** (agentic memory / files), and **sub-agent architectures** (isolated windows returning distilled summaries). Claude Code is the running example: summarize history while preserving decisions and recent files; use subagents so exploratory tool noise never fills the parent window.

Paired live product behavior: Claude Code session management and 1M context — https://claude.com/blog/using-claude-code-session-management-and-1m-context — auto-compaction near the limit, proactive `/compact`, subagent isolation.

---

## Open Questions

- Will larger windows retire compaction, or will rot/distraction keep curation mandatory (Anthropic’s bet: curation remains central)?  
- Should memory updates run **on the hot path** (latency, transparency) or **in the background / “dreaming”** (Mukta, AI Native DevCon)?  
- Opaque encrypted compaction items (OpenAI) vs human-auditable summaries (Claude Code) — which wins for enterprise compliance?  
- How much of “context engineering” collapses back into good IR (Week 7–8) vs orchestration (Week 13)?  
- Evaluation: which metrics prove compaction helped — task success, faithfulness to prior decisions, token/$ , or human review of summaries?

---

## Sources

- https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents  
- https://claude.com/blog/using-claude-code-session-management-and-1m-context  
- https://www.langchain.com/blog/context-engineering-for-agents  
- https://docs.langchain.com/oss/python/concepts/memory  
- https://docs.langchain.com/oss/python/langgraph/persistence  
- https://huyenchip.com/2025/01/07/agents.html  
- https://huyenchip.com/2024/07/25/genai-platform.html  
- https://arxiv.org/abs/2307.03172  
- https://www.dbreunig.com/2025/06/22/how-contexts-fail-and-how-to-fix-them.html  
- https://developers.openai.com/api/docs/guides/compaction  
- https://ai.engineer/talks/keynote-why-people-think-agent-is-a-buzzword-but-it-isn-t  
- https://www.youtube.com/watch?v=tTcxVv8HHNw  
