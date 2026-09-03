# 04 — Context compaction (summarizing history to stay under budget)

> Week 25 — Context Engineering as a discipline  
> Research notes (raw).

---

## Fundamentals

**Compaction** shrinks a growing session context into a smaller representation so the agent can continue past token budgets **without** naively truncating the only copy of critical decisions.

Anthropic definition (*Effective context engineering…*): take a conversation nearing the limit, **summarize**, reinitiate a window with the summary (plus carefully chosen residue such as recent files). Goal: high-fidelity continuity with minimal performance degradation.

### Why not only truncate?

| Naive trim | Compaction |
|------------|------------|
| Drops oldest messages blindly | Distills decisions, bugs, constraints |
| May delete the policy user stated turn 1 | Prompted to preserve architectural choices |
| Cheap | Costs a summarization call; can lose subtlety |

Related operations (LangChain compress bucket):

- **Summarization** — LLM distill of trajectory or tool output.  
- **Trimming / pruning** — heuristic drop (e.g. remove messages before last N; clear old tool payloads).  
- **Tool-result clearing** — lightest compaction: keep that a tool was called; drop bulky raw output once consumed (Anthropic notes this as a platform feature).

### Thresholds and timing

- Claude Code: auto-compact near capacity (~95% default in operator docs; override via env). Proactive `/compact` with optional focus instructions — better because **context rot** means the model is weakest when the window is fullest (Claude session blog).  
- OpenAI Responses: `context_management` with `compact_threshold` for **server-side** compaction mid-stream; or standalone `POST /responses/compact` returning a new window including an **encrypted compaction item** (opaque, ZDR-friendly with `store=false`).  
- LangGraph: utilities to summarize/trim message lists; or custom summarize nodes between phases / at agent boundaries.

### Compaction quality loop (Anthropic)

1. Maximize **recall** — summarizer must not omit critical constraints.  
2. Then improve **precision** — strip superfluous tool HTML, duplicate searches.  
3. Evaluate on **complex agent traces**, not toy chats.

Loss mode: overly aggressive compaction deletes a constraint whose importance appears only later → silent policy break.

Structured note-taking complements compaction: durable NOTES outside the window are re-read after reset (Pokémon agent example in Anthropic post).

---

## Alternatives & Tradeoffs

| Strategy | Pros | Cons |
|----------|------|------|
| Wait for hard context error | Zero engineering | Run aborts mid-task |
| Sliding window (last K turns) | Simple | Loses early constraints |
| **LLM summary compaction** | Semantic continuity | Summary errors; cost |
| Provider opaque compaction (OpenAI) | Token-efficient latent state | Not human auditable |
| Hierarchical / recursive summaries | Scales to huge traces | Complexity; drift |
| Subagent instead of compacting parent | Isolates noise | Coordination overhead |
| Fine-tuned summarizer (Cognition, cited by LangChain) | Better handoff fidelity | ML ops burden |

| Threshold policy | |
|----------------|--|
| % of model window | Portable across tasks |
| Absolute token count | Predictable cost |
| Event-based (after research phase) | Aligns with workflow; may forget mid-phase |

Tradeoff: compaction frequency vs fidelity. Too rare → distraction/rot. Too often → thrashing and lost detail.

---

## Necessity

Without compaction:

- Long coding/research agents **die** at the window ceiling mid-migration.  
- Cost/latency grow linearly with transcript length even when 90% is obsolete tool JSON.  
- Models enter **context distraction** (Breunig): repeat past actions instead of planning (Gemini Pokémon agent anecdote beyond ~100k).  
- Teams “fix” by switching to a larger model when they needed **summary + tool clearing**.  
- Handoffs pass megabytes; receiving agent immediately needs its own compaction.

OpenAI docs position compaction as balancing **quality, cost, and latency** for long-running interactions — not an optional nicety.

---

## Industry Practice

- **Common:** catch context-length exceptions; retry with clipped history; user starts a new chat.  
- **Strong:** meter tokens every turn; compact at threshold; clear tool results after use; keep last user goals + decision log verbatim when possible; unit-test summarizer prompts on golden traces; log before/after token counts and a hash of preserved constraint list.  
- **FDE bar:** choose auditable vs opaque compaction per compliance regime; for regulated clients prefer summary text in object storage with retention; for ZDR stacks use provider encrypted compaction with `store=false`; never compact away **authorization** decisions without re-injecting them as system pins.

Claude session blog: steer `/compact` with instructions; put durable rules in `CLAUDE.md` so they survive summary. OpenAI: after server compaction, drop items before the latest compaction item when using input-array chaining; do not manually prune when using `previous_response_id`.

---

## Concrete Scenario

**OpenAI — Compaction guide (Responses API)**  
https://developers.openai.com/api/docs/guides/compaction  

Server-side: set `context_management: [{ type: "compaction", compact_threshold: 200_000 }]`. Stream may emit encrypted compaction items; continue via input-array append or `previous_response_id`. Standalone: `client.responses.compact({ model, input })` → pass `compacted.output` as next input. Explicitly supports long-running coding/agent loops under token pressure.

**Anthropic — Claude Code compaction**  
https://claude.com/blog/using-claude-code-session-management-and-1m-context  
https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents  

Auto-compact + `/compact`; preserve decisions; pair with notes and subagents.

---

## Open Questions

- Can we verify compaction fidelity automatically (constraint checklist NLI)?  
- Should user messages always remain verbatim (OpenAI compact behavior) while assistant/tool sides compress?  
- Ideal threshold as % of window across model families?  
- Interaction with prompt caching: does compaction destroy cache hits?  
- When is **starting a new thread with a brief** better than compacting a poisoned thread?

---

## Sources

- https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents  
- https://claude.com/blog/using-claude-code-session-management-and-1m-context  
- https://developers.openai.com/api/docs/guides/compaction  
- https://developers.openai.com/api/reference/resources/responses/methods/compact  
- https://www.langchain.com/blog/context-engineering-for-agents  
- https://docs.langchain.com/oss/python/langgraph/add-memory  
- https://www.dbreunig.com/2025/06/22/how-contexts-fail-and-how-to-fix-them.html  
- https://www.dbreunig.com/2025/06/26/how-to-fix-your-context.html  
- https://arxiv.org/abs/2307.03172  
