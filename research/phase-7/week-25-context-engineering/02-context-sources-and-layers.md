# 02 — Context sources and context layers

> Week 25 — Context Engineering as a discipline  
> Research notes (raw).

---

## Fundamentals

A model never sees “the world.” It sees a **assembled context**: a finite sequence of tokens. Context engineering starts by inventorying **sources** (where tokens come from) and **layers** (how they are ordered, scoped, and updated).

### Sources (Anthropic anatomy + LangChain types)

Anthropic’s effective-context post lists the working world of an agent:

| Source | Role | Typical volatility |
|--------|------|--------------------|
| **System / developer instructions** | Behavioral policy, output contracts | Low (versioned) |
| **Tool schemas / MCP metadata** | Action & information surface | Medium (tool catalog changes) |
| **Retrieved external data (RAG)** | Grounding for this query | High (per turn) |
| **Message / reasoning history** | Session continuity | High (grows every turn) |
| **Examples (few-shot)** | Behavioral pictures | Low–medium |
| **Memory stores / notes** | Cross-session or scratch facts | Medium |
| **Tool results** | Observations from the environment | Very high |

LangChain groups similar material as **instructions**, **knowledge**, and **tools** (feedback from tool calls). Chip Huyen’s platform post calls the gathering step **context construction** — RAG, SQL, web search, people/inventory APIs are all sources that feed the window (*Building a Generative AI Platform*).

### Layers (assembly order)

Think in **layers** that an assembler merges deterministically:

1. **Static policy layer** — system prompt sections, org rules (`CLAUDE.md`, Cursor rules), safety.  
2. **Capability layer** — tool / MCP definitions currently enabled (minimal viable set — Anthropic).  
3. **Episodic session layer** — messages, prior tool I/O still retained.  
4. **Retrieved evidence layer** — packed RAG / search hits for *this* step (Week 6–8 discipline).  
5. **Memory injection layer** — selected long-term facts / preferences (namespaced).  
6. **Working scratch layer** — plan, TODO, NOTES.md excerpts the agent wrote.

Claude Code’s hybrid pattern (Anthropic): naively drop `CLAUDE.md` up front; use glob/grep for **just-in-time** file loads so the full repo never sits in layer 4. Progressive disclosure: each exploration step adds only what is needed.

LangGraph encodes layers as **state schema fields**: only some fields (e.g. `messages`) are rendered into the LLM call each node; others stay isolated until selected (see file 05).

### JIT vs pre-retrieval

| Strategy | Mechanism | Risk |
|----------|-----------|------|
| **Pre-inference RAG** | Embed/search before the call | Stale index; over-stuff |
| **Just-in-time** | Agent holds pointers (paths, queries) and loads via tools | Extra turns; tool misuse |
| **Hybrid** | Small always-on layer + agentic fetch | Needs good tool heuristics |

Anthropic: as models improve, designs trend toward more autonomy — but “do the simplest thing that works” remains advice.

---

## Alternatives & Tradeoffs

| Layering choice | Pros | Cons |
|-----------------|------|------|
| Single flat string concat | Easy | Undebuggable; no section token metrics |
| XML/Markdown sections (Anthropic) | Clear boundaries; easier audits | Still competes for attention |
| Structured item arrays (Responses / Chat APIs) | Typed roles; compaction items | Vendor-specific item types |
| Everything in `messages` | Simple checkpoint | Cannot hide tool blobs from attention |
| Split state fields + selective render | Fine-grained control | Custom assembler code |

| Source inclusion policy | Tradeoff |
|-------------------------|----------|
| Always include all tools | Confusion when schemas overlap |
| RAG over tool descriptions (LangGraph Bigtool pattern) | Better selection; retrieval miss → missing capability |
| Always include full history | Continuity until rot/distraction |
| Pointers + JIT only | Lean window; higher latency |

Positioning inside the evidence layer still matters: Lost in the Middle — gold in the *middle* of long packed contexts underperforms edges (Liu et al.).

---

## Necessity

Without an explicit source/layer map:

- Token budgets are argued as “the prompt is too long” when **tool results** dominate.  
- Security reviews miss that **retrieved email** is a source with the same trust level as user text (indirect injection).  
- Memory mounts (Claude Managed Agents `/mnt/memory/...`) silently inject system-prompt notes — operators forget they are context.  
- Multi-agent systems duplicate entire capability layers into every worker (15× token blowups — Anthropic research system).  
- Compaction deletes the wrong layer (drops policy; keeps noisy search HTML).

Week 9 RAG failures live mostly in the **retrieved evidence** layer. Week 25 failures can originate in *any* layer — inventory first.

---

## Industry Practice

- **Common:** one ChatML transcript; tools always on; top-k=20 forever.  
- **Strong:** context bill of materials in traces (tokens per section); enable tools per task phase; reorder evidence (recent/high-score at edges); separate org-read-only memory from per-user read-write memory (Anthropic memory cookbook pattern).  
- **FDE bar:** draw the layer diagram for the customer’s stack in the first architecture workshop; assign owners (prompt team vs search vs platform memory); set SLOs on **tokens per successful task**, not only latency.

OpenAI Responses: conversation items generalize beyond messages (tool calls, outputs, compaction items) — layers become first-class item types. Assistants Threads → Conversations migration makes durable session history an explicit product object.

---

## Concrete Scenario

**Claude Code hybrid context layers** — Anthropic engineering post + session blog:  
https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents  
https://claude.com/blog/using-claude-code-session-management-and-1m-context  

`CLAUDE.md` / project rules form the always-on procedural layer. File reads and bash outputs enter as episodic tool observations. Near the million-token ceiling, auto-compaction summarizes the trajectory while aiming to preserve architectural decisions and recent files. Subagents get a **fresh** window for exploratory search; only a distilled report returns to the parent — evidence that layers can be **forked** rather than endlessly appended.

Chip Huyen platform architecture (context construction block):  
https://huyenchip.com/2024/07/25/genai-platform.html  

---

## Open Questions

- Should MCP tool descriptors be retrieved dynamically or always pinned for safety-critical tools?  
- Ideal default order: policy → tools → memory → evidence → history, or history near the end for recency bias?  
- How to label trust tiers per source in the assembler (user / retrieved / memory / system) for Dual-LLM routing?  
- Do multimodal items (screenshots, PDFs) need separate layer budgets?  
- Can section-level caching (provider prompt cache) dictate layer stability ordering?

---

## Sources

- https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents  
- https://claude.com/blog/using-claude-code-session-management-and-1m-context  
- https://www.langchain.com/blog/context-engineering-for-agents  
- https://huyenchip.com/2024/07/25/genai-platform.html  
- https://huyenchip.com/2025/01/07/agents.html  
- https://platform.claude.com/docs/en/managed-agents/memory  
- https://developers.openai.com/api/docs/guides/compaction  
- https://developers.openai.com/api/docs/assistants/migration  
- https://arxiv.org/abs/2307.03172  
- https://docs.langchain.com/oss/python/langgraph/add-memory  
