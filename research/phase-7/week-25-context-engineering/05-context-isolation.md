# 05 — Context isolation (why one agent's context shouldn't leak into another's)

> Week 25 — Context Engineering as a discipline  
> Research notes (raw).

---

## Fundamentals

**Context isolation** means each agent (or agent role, or tenant session) operates with a **bounded window and memory namespace** so tokens from one lineage do not silently become instructions or evidence for another.

Why it matters:

1. **Correctness** — Agent B should not “remember” Agent A’s abandoned hypotheses (context clash / poisoning).  
2. **Security** — Untrusted content processed by a worker must not reach a privileged tool-caller (prompt injection).  
3. **Budget** — Exploratory search can burn tens of thousands of tokens; parents should see **summaries**, not raw haystacks (Anthropic multi-agent research + effective context posts).  
4. **Tenancy** — Customer 1’s thread/memory must never mount into Customer 2’s session.

### Isolation mechanisms

| Mechanism | What is isolated | Pattern |
|-----------|------------------|---------|
| **Separate threads / checkpointers** | Session histories | Distinct `thread_id` per conversation |
| **Store namespaces** | Long-term facts | `(tenant, user, agent)` keys |
| **Sub-agents / workers** | Full exploratory context | Fresh window; return 1–2k summary |
| **State schema fields** | Non-message blobs | Keep images/SQL tables off `messages` until needed |
| **Sandboxes / CodeAgents** | Heavy artifacts in env vars | HuggingFace-style; LangGraph+E2B examples |
| **Dual LLM** | Trust domains | Privileged planner never reads raw untrusted text (Willison) |
| **Memory access modes** | Write rights | Claude `read_only` mounts for shared org knowledge |

Anthropic Claude Code: spawning a subagent via the Agent tool gives a **fresh context window**; intermediate tool noise stays in the child; only the final report returns. Multi-agent research system: parallel subagents with own windows beat a single crowded agent on broad research — at ~15× token cost vs chat.

Simon Willison **Dual LLM**: Privileged LLM holds tools; Quarantined LLM reads untrusted content without tools; never forward quarantined raw text back as privileged context — only structured/safe interfaces. OWASP LLM Prompt Injection Cheat Sheet lists **context poisoning** (false info into working memory) and cites Dual LLM as architectural mitigation.

Context-minimization pattern (design-patterns paper via Willison): strip user prompt from context after translating to a safe query so injection cannot continue into later turns.

---

## Alternatives & Tradeoffs

| Approach | Pros | Cons |
|----------|------|------|
| One shared mega-context for all roles | Simple wiring | Leak, clash, distraction |
| Soft isolation (roles in one prompt) | Cheap | Model may ignore role boundaries |
| **Hard isolation (separate windows)** | Clear blast radius | Summary loss; coordination tokens |
| Dual LLM | Strong injection story | UX/latency; interface design hard |
| CaMeL / capability systems (DeepMind; Willison commentary) | Dataflow enforcement | Research/early production |
| Tenant DB row-level security only | Good for stores | Does not stop in-prompt leak if assembler merges wrong |

| Subagent granularity | |
|----------------------|--|
| Too coarse | Still polluted windows |
| Too fine | Summary telephone game; 15× spend |

Week 13 reminder: split by **context boundaries** (pollution, parallelism, specialization), not vanity role names.

---

## Necessity

If isolation is skipped:

- Support bot for Tenant A cites Tenant B’s invoice numbers from a shared Redis chat key.  
- Research worker’s hallucinated “fact” is pasted into the lead agent’s plan and becomes **poison** for all downstream tools.  
- Injected instructions in a fetched webpage reach the privileged agent that can `send_email` / `refund`.  
- Parent coding agent’s window fills with grep dumps; task focus collapses (rot) — solvable by subagent isolation *or* compaction, but isolation prevents the fill-in in the first place.  
- HITL reviewers see the wrong thread’s PII.

Breunig’s **context clash** is often an isolation bug: contradictory tool results from parallel workers merged without reconciliation.

---

## Industry Practice

- **Common:** single `messages` array; “multi-agent” is prompt cosplay; one memory table.  
- **Strong:** thread_id and memory namespace mandatory in every invoke; subagents as tools returning summaries; red-team tests that attempt cross-tenant reads; Dual LLM or gated tools for untrusted channels; read_only shared memories.  
- **FDE bar:** threat model diagram with trust boundaries on the context assembler; demo that Agent tools cannot read another tenant’s store ID; document handoff schema (allowed fields); cite OWASP + Willison in security review.

LangGraph: subgraphs can use checkpoint namespaces; avoid compiling nested graphs with separate checkpointers that accidentally orphan state — inherit outer checkpointer when appropriate. Swarm/supervisor libraries motivate separation of concerns via per-agent instructions/tools/windows.

---

## Concrete Scenario

**Anthropic — subagent isolation in Claude Code / research**  
https://claude.com/blog/using-claude-code-session-management-and-1m-context  
https://www.anthropic.com/engineering/multi-agent-research-system  
https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents  

Subagents explore with tens of thousands of tokens; lead receives condensed summaries (~1–2k). Parallel isolated windows improved research quality vs single-agent crowding.

**Simon Willison — Dual LLM pattern**  
https://simonwillison.net/2023/Apr/25/dual-llm-pattern/  

Architectural isolation of tool privilege from untrusted content — foundational for “context shouldn’t leak” as a *security* property, not only UX.

**OWASP — LLM Prompt Injection Prevention Cheat Sheet** (context poisoning section)  
https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html  

---

## Open Questions

- Is summary-at-boundary enough, or do we need cryptographic capability labels on every context span (CaMeL-style)?  
- How to isolate within one agent across **phases** without full multi-agent?  
- Should evaluators run in an isolated context so judge rubrics cannot be injected by the candidate answer?  
- Multi-agent A2A across vendors: how to express isolation contracts on the wire?  
- Performance: when does isolation’s token multiplier dominate its quality win?

---

## Sources

- https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents  
- https://www.anthropic.com/engineering/multi-agent-research-system  
- https://claude.com/blog/using-claude-code-session-management-and-1m-context  
- https://www.langchain.com/blog/context-engineering-for-agents  
- https://docs.langchain.com/oss/python/langgraph/persistence  
- https://simonwillison.net/2023/Apr/25/dual-llm-pattern/  
- https://simonwillison.net/2025/Jun/13/prompt-injection-design-patterns/  
- https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html  
- https://platform.claude.com/docs/en/managed-agents/memory  
- https://www.dbreunig.com/2025/06/22/how-contexts-fail-and-how-to-fix-them.html  
