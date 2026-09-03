# 06 — Multi-agent context sharing patterns

> Week 25 — Context Engineering as a discipline  
> Research notes (raw).

---

## Fundamentals

Multi-agent systems need **controlled sharing**: enough context for coordination, not enough to reintroduce isolation failures. Sharing is a first-class context-engineering decision — what crosses the boundary, in what form, with what trust label.

### Pattern catalog

| Pattern | What is shared | When it fits |
|---------|----------------|--------------|
| **Summary handoff** | Distilled report (goals, findings, open questions, citations) | Default Anthropic worker → lead |
| **Shared scratchpad / plan file** | Mutable plan outside windows | LeadResearcher Memory plan (Anthropic research) survives truncation |
| **Shared long-term store** | Namespaced facts both may read | Org standards read_only; user profile |
| **Message relay (full dump)** | Entire child transcript | Rarely; explodes tokens; prefer summary |
| **Tool-as-subagent** | Only tool return string | LangGraph `create_agent` subagents-as-tools |
| **Blackboard / state bus** | Typed fields on shared graph state | Single process; selective render to each node |
| **Artifact pointers** | URIs / doc IDs, not bodies | JIT load by recipient |
| **Critique channel** | Reviewer comments only | Eval / red-team agents |

Anthropic *How we built our multi-agent research system*: orchestrator–worker; subagents parallelize with **own contexts**; token use ~**15×** chat; **detailed task briefs** mandatory — vague assignments caused duplicate work and gaps. Effective context post: each subagent may use tens of thousands of tokens; returns ~1–2k condensed summary.

LangChain: Cognition emphasizes summarization at **agent–agent boundaries**. LangGraph supervisor/swarm: separate instructions/tools/windows; control history in wrappers (`last_message` vs summary vs full).

Chip Huyen (*Agents*): more tools → more documentation in context; tool outputs accumulate across steps — multi-agent can partition that load if sharing is disciplined.

### Handoff contract (recommended fields)

```text
handoff_id, from_agent, to_agent,
objective, constraints[],
findings[], evidence_refs[],
open_questions[],
token_budget_used,
trust_tier (user|retrieved|inferred)
```

Missing `constraints[]` is the classic **lost context across handoffs** failure (file 07).

---

## Alternatives & Tradeoffs

| Sharing style | Pros | Cons |
|---------------|------|------|
| Full transcript share | Max fidelity | Token blowup; injection spread |
| **Summary only** | Lean; isolates noise | Omits nuance; telephone errors |
| Pointers + JIT | Fresh reads | Extra latency; link rot |
| Shared mutable blackboard | Tight coordination | Race conditions; clash |
| Dual read paths (raw for quarantine, summary for privilege) | Security | Complexity |

| Topology | Sharing implication |
|----------|---------------------|
| Sequential pipeline | Handoff summaries between stages |
| Supervisor–workers | Fan-out briefs; fan-in merges |
| Peer swarm | High clash risk without locks |
| Human-in-the-loop gate | Human edits become shared context — version them |

Tradeoff from Week 13: multi-agent often **3–10×** tokens in testing; Anthropic research up to **15×**. Share less, not more, unless breadth requires it.

---

## Necessity

Without explicit sharing patterns:

- Workers duplicate the same web searches (wasted spend).  
- Lead agent never sees a constraint that lived only in worker turn 3.  
- Two workers write conflicting facts into a shared store without merge rules → clash.  
- “Share everything” re-creates a single polluted context — isolation theater.  
- Security: one compromised worker transcript injected into all peers.

Sharing policy is how you encode **isolation exceptions**. Unwritten exceptions become bugs.

---

## Industry Practice

- **Common:** concatenate worker outputs into the next prompt; no schema; no token accounting.  
- **Strong:** typed handoff objects; summarize nodes; shared plan file with ownership; merge strategies for store writes (Trustcall-like); evaluate end-to-end *and* per-boundary faithfulness.  
- **FDE bar:** customer-facing diagram of who sees what; SLAs on summary latency; refuse architectures that pipe raw PII between agents without need; align with Dual LLM when tools are involved.

OpenAI migration guidance: Conversations store mixed item types — design multi-agent shares as **items**, not free text blobs, when on Responses.

Claude Managed Agents: multiple memory stores per session (org + user) is a **controlled** share — not a full transcript mesh.

---

## Concrete Scenario

**Anthropic multi-agent research system**  
https://www.anthropic.com/engineering/multi-agent-research-system  

Lead agent plans and delegates; workers explore in parallel isolated windows; results synthesized centrally. Public write-up stresses token cost, briefing quality, and context separation — the canonical industry scenario for **sharing via summaries + plan memory**, not full context merge.

Supporting: LangChain context engineering post (write/select/compress/isolate; boundary summarization)  
https://www.langchain.com/blog/context-engineering-for-agents  

---

## Open Questions

- Can learned routers decide share granularity per task?  
- Standard handoff schema across vendors (A2A)?  
- How to cite evidence across agents without shipping full passages?  
- Should shared stores be CRDTs / versioned files only (Mukta concurrency hashing)?  
- When does a human-readable brief outperform an opaque shared embedding space?

---

## Sources

- https://www.anthropic.com/engineering/multi-agent-research-system  
- https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents  
- https://claude.com/blog/building-multi-agent-systems-when-and-how-to-use-them  
- https://www.langchain.com/blog/context-engineering-for-agents  
- https://docs.langchain.com/oss/python/langgraph/add-memory  
- https://huyenchip.com/2025/01/07/agents.html  
- https://platform.claude.com/docs/en/managed-agents/memory  
- https://developers.openai.com/api/docs/assistants/migration  
- https://simonwillison.net/2023/Apr/25/dual-llm-pattern/  
