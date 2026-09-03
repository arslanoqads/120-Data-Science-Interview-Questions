# Chapter 25 — Context Engineering as a discipline

> **Phase 7 — Supplementary Electives**  
> **Compilation status:** COMPLETE  
> **Source of truth:** `research/phase-7/week-25-context-engineering/`  
> **Syllabus Build:** Add an explicit **context-management layer** to the Phase 3 agentic stack (do not invent a new model API): (1) **session memory** — persist thread/session state (messages + scratchpad fields); compact (summarize / trim / clear tool results) when token count crosses a configured threshold; (2) **isolation** — separate context namespaces per agentic system (or per sub-agent); no accidental shared message lists across tenants or sibling agents; (3) **failure-mode log** — document incidents the way Week 9 documents RAG failures: stale context, context poisoning, lost context across handoffs (plus distraction / confusion / clash as subtypes); join on `session_id` / `handoff_id`.

---

## Chapter framing

Week 25 makes **context engineering** an explicit curriculum discipline. Flagship agent stacks already do it implicitly: RAG packs evidence, agents accumulate tool results, checkpointers resume threads, memory stores persist preferences. This elective forces those mechanisms into one vocabulary and one build surface. It is **supplementary** — it does not replace Weeks 1–24. Suggested slot: after Phase 3 (Week 15), before or alongside Phase 4 evals — or append after the Week 24 capstone.

**Prompt engineering** (Week 5) is how you write and version *instructions*. **Context engineering** is how you curate *everything* that consumes the model's finite attention budget on each inference turn — system instructions, tool schemas, MCP metadata, retrieved documents, message history, scratchpads, and long-term memories (Anthropic, *Effective context engineering for AI agents*, 2025-09-29). Karpathy (via LangChain): fill the window with **just the right information for the next step**. Anthropic’s guiding principle: the **smallest set of high-signal tokens** that maximizes the likelihood of the desired outcome. Chip Huyen frames the same problem as **context construction** — gathering what a model needs via RAG, tools, or memory.

Why it is distinct from “just longer windows”:

| Observation | Implication |
|-------------|-------------|
| **Context rot** (Anthropic) — recall accuracy degrades as token count rises | Treat context as a scarce resource, not free storage |
| **Lost in the Middle** (Liu et al., arXiv:2307.03172) — U-shaped position sensitivity | Order and packing matter as much as inclusion |
| **Distraction ceilings** (Breunig; Gemini Pokémon agent anecdote ~100k) | Agents can fail *before* the hard window limit |
| **Attention is n²** (transformer pairwise) | Every token taxes every other token |

Do not skip this week for “we already have RAG and a system prompt.” Flagship systems do context work **implicitly**; this week makes the discipline **explicit** and measurable.

Read the concepts in order. Each section’s **Worked Example** and **Apply It** assume the same flagship service (working title: Deployment Copilot) gaining a named context-management layer on top of the Phase 3 agentic stack.

**Default path (synthesis):**

1. Inventory every token source that lands in the window (system, tools, retrieved docs, history, memory mounts).  
2. Implement **write / select / compress / isolate** (LangChain framing) as named modules with traces.  
3. Set a **compaction threshold** (token or % of window) and evaluate fidelity before/after on long traces.  
4. Give each agent its own `thread_id` / memory namespace; pass only **summaries** across boundaries.  
5. Keep a portfolio **context failure log** paired with Week 9 RAG taxonomy and Week 15 agent evals.

---

### Context vs prompt engineering

* **Fundamentals:**  
  **Prompt engineering** is the craft of writing and organizing *instructions* so a model behaves as intended: system prompts, few-shot exemplars, output schemas, personas, refusal policies. Week 5 already covers versioning, templates, and injection surface. The unit of work is usually a **prompt artifact** — text you author and pin.

  **Context engineering** is the craft of deciding **what information the model sees and when**, across the *entire* token set used at inference time. Anthropic (*Effective context engineering for AI agents*, 2025-09-29): prompt engineering is methods for writing and organizing LLM instructions; context engineering is strategies for curating and maintaining the optimal set of tokens during inference, **including all the other information that may land there outside of the prompts** — tool schemas, MCP descriptors, retrieved passages, prior messages, tool results, memory mounts, images, and structured state. An agent loop **generates** new candidates for context every turn; curation must be **iterative**, not a one-shot prompt write.

  Andrej Karpathy (quoted by LangChain): context engineering is the “delicate art and science of filling the context window with just the right information for the next step.” LangChain treats the LLM as CPU and the context window as RAM — an OS-like scheduler decides what resides in working memory. Chip Huyen’s public writing uses **context construction** as the umbrella: prompt text is one input; retrieval, tool I/O, and memory are peers (*Building a Generative AI Platform*; *Agents*).

  | Dimension | Prompt engineering | Context engineering |
  |-----------|--------------------|---------------------|
  | Primary question | How do we *word* instructions? | What *tokens* occupy the window *now*? |
  | Cadence | Version when behavior changes | Re-decide every inference turn |
  | Artifacts | Prompt files, templates | Packers, retrievers, compactors, isolators, memory writers |
  | Failure owner | Prompt author | Retrieval / memory / orchestration / packing |
  | Classic week | Week 5 | Week 25 (this elective) |

  Anthropic’s design target: the **smallest set of high-signal tokens** that maximize desired outcomes — informative yet tight. System prompts still matter (altitude: not brittle if-else, not vague), but they are one *layer* inside a larger assembly problem.

* **The Alternatives:**  

  | Stance | Upside | Downside |
  |--------|--------|----------|
  | “Prompt engineering subsumes everything” | Simple org chart | Hides packing/memory bugs under “bad prompt” |
  | “Context engineering replaces prompts” | Fashionable | Still need clear instructions; tools still need schemas |
  | **Progression model (Anthropic)** — prompts → full context curation | Matches agent reality | Requires new modules and evals |
  | Bigger windows only | Less summarizer code | Rot, cost, Lost-in-the-Middle, distraction |
  | Pure RAG as “the” context strategy | Strong for docs | Ignores history, tools, cross-session memory |

  | Prompt investment vs context investment | When it wins |
  |-----------------------------------------|--------------|
  | Polish system prompt + few-shots | Single-turn classification / generation |
  | Packer + compaction + isolation | Multi-turn agents, tool loops, multi-tenant |
  | Hybrid: pinned CLAUDE.md / rules + JIT retrieval | Coding agents (Anthropic hybrid example) |

  The syllabus selects the **progression model**: keep Week 5 prompt discipline, then add an explicit assembler. Stuffing every edge case into the system prompt fights context budget and creates **clash** with later tool results; Anthropic recommends diverse **canonical** examples, not laundry lists.

* **Failure Modes:**  
  - A perfect system prompt still fails when **mid-context gold** is ignored (Liu et al., Lost in the Middle).  
  - Tool result spam drowns instructions; the model follows a stale JSON blob instead of the policy section.  
  - Teams A/B prompt wording while the real delta is **k**, reorder, or compaction aggressiveness.  
  - Security reviews miss **indirect injection** sitting in retrieved email or web pages — not in *your* prompt file (Willison; OWASP).  
  - Cost dashboards show “prompt tokens” rising when the driver is **unchecked history**, not a longer system string.  
  - Week 15/16 error analysis labels every failure “prompt” — wrong owner.

* **Average vs. Strong Engineer:**  
  **Average:** one mega system prompt; append chat; hope the model “remembers”; prompt edits are the only lever.  
  **Strong:** separate **instruction registry** (versioned prompts) from **context assembler** (deterministic merge of static + dynamic sections); trace each section’s token count; evaluate prompt changes *and* packing changes independently; can explain Anthropic’s progression narrative; point at Claude Code (CLAUDE.md always in, files JIT via glob/grep); point at LangGraph state fields that are *not* in `messages` until selected; refuse conflating “we added RAG” with “we engineered context end-to-end.”

* **Worked Example:**  
  Deployment Copilot’s support agent keeps failing “respect the change-freeze calendar” tickets. The team rewrites the system prompt three times. Traces show the freeze rule is present in turn 1, then buried under 40k tokens of kubectl logs and RAG snippets mid-session. After Week 25, the **assembler** pins the freeze rule in the static policy layer every turn, clears old tool payloads after use, and meters section token counts. Prompt wording stays pinned; the packing change is the A/B that moves task success — attributed separately from prompt registry versions.

* **Apply It:**  
  1. Write a one-page distinction: what lives in the prompt registry vs what the assembler decides per turn.  
  2. Instrument traces with per-section token counts (policy / tools / RAG / history / memory).  
  3. For the next “prompt regression,” require a hypothesis that names a *context* lever (k, order, compact, isolate) before editing system text.  
  4. Keep CLAUDE.md / org rules as always-on policy; load repo files JIT via tools, not pre-stuff.  
  5. Evaluate prompt changes and packing changes on separate axes in the Week 15 harness.

---

### Context sources and layers

* **Fundamentals:**  
  A model never sees “the world.” It sees an **assembled context**: a finite sequence of tokens. Context engineering starts by inventorying **sources** (where tokens come from) and **layers** (how they are ordered, scoped, and updated).

  Sources (Anthropic anatomy + LangChain types):

  | Source | Role | Typical volatility |
  |--------|------|--------------------|
  | **System / developer instructions** | Behavioral policy, output contracts | Low (versioned) |
  | **Tool schemas / MCP metadata** | Action & information surface | Medium (tool catalog changes) |
  | **Retrieved external data (RAG)** | Grounding for this query | High (per turn) |
  | **Message / reasoning history** | Session continuity | High (grows every turn) |
  | **Examples (few-shot)** | Behavioral pictures | Low–medium |
  | **Memory stores / notes** | Cross-session or scratch facts | Medium |
  | **Tool results** | Observations from the environment | Very high |

  LangChain groups similar material as **instructions**, **knowledge**, and **tools** (feedback from tool calls). Chip Huyen’s platform post calls the gathering step **context construction** — RAG, SQL, web search, people/inventory APIs are all sources that feed the window.

  Layers an assembler merges deterministically:

  1. **Static policy layer** — system prompt sections, org rules (`CLAUDE.md`, Cursor rules), safety.  
  2. **Capability layer** — tool / MCP definitions currently enabled (minimal viable set — Anthropic).  
  3. **Episodic session layer** — messages, prior tool I/O still retained.  
  4. **Retrieved evidence layer** — packed RAG / search hits for *this* step (Week 6–8 discipline).  
  5. **Memory injection layer** — selected long-term facts / preferences (namespaced).  
  6. **Working scratch layer** — plan, TODO, NOTES.md excerpts the agent wrote.

  Claude Code’s hybrid pattern (Anthropic): naively drop `CLAUDE.md` up front; use glob/grep for **just-in-time** file loads so the full repo never sits in the evidence layer. Progressive disclosure: each exploration step adds only what is needed. LangGraph encodes layers as **state schema fields**: only some fields (e.g. `messages`) are rendered into the LLM call each node; others stay isolated until selected.

  JIT vs pre-retrieval:

  | Strategy | Mechanism | Risk |
  |----------|-----------|------|
  | **Pre-inference RAG** | Embed/search before the call | Stale index; over-stuff |
  | **Just-in-time** | Agent holds pointers (paths, queries) and loads via tools | Extra turns; tool misuse |
  | **Hybrid** | Small always-on layer + agentic fetch | Needs good tool heuristics |

* **The Alternatives:**  

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

  Positioning inside the evidence layer still matters: Lost in the Middle — gold in the *middle* of long packed contexts underperforms edges (Liu et al.). The syllabus expects a **named bill of materials** in traces, not a flat concat.

* **Failure Modes:**  
  - Token budgets are argued as “the prompt is too long” when **tool results** dominate.  
  - Security reviews miss that **retrieved email** is a source with the same trust level as user text (indirect injection).  
  - Memory mounts (Claude Managed Agents `/mnt/memory/...`) silently inject system-prompt notes — operators forget they are context.  
  - Multi-agent systems duplicate entire capability layers into every worker (15× token blowups — Anthropic research system).  
  - Compaction deletes the wrong layer (drops policy; keeps noisy search HTML).  
  - Week 9 RAG failures live mostly in the **retrieved evidence** layer; Week 25 failures can originate in *any* layer — inventory first.

* **Average vs. Strong Engineer:**  
  **Average:** one ChatML transcript; tools always on; top-k=20 forever.  
  **Strong:** context bill of materials in traces (tokens per section); enable tools per task phase; reorder evidence (recent/high-score at edges); separate org-read-only memory from per-user read-write memory (Anthropic memory cookbook pattern); draw the layer diagram in the first architecture workshop; assign owners (prompt team vs search vs platform memory); set SLOs on **tokens per successful task**, not only latency. OpenAI Responses conversation items generalize beyond messages — layers become first-class item types.

* **Worked Example:**  
  Deployment Copilot’s deploy agent always enables 30 MCP tools. Traces show the capability layer alone is ~8k tokens; history + tool results push the window toward rot before the user finishes describing the outage. You split layers in the assembler: static policy + a **phase-gated** tool subset (read-only diagnostics first; write tools only after a plan node); RAG evidence packed with high-score hits at edges; scratch NOTES.md selected only when the agent wrote it this session. Section counters in the failure log prove tool schemas were the budget killer — not the system prompt.

* **Apply It:**  
  1. Inventory every source that can emit tokens into Deployment Copilot’s window.  
  2. Implement a deterministic assembler with named layers and per-section token traces.  
  3. Default to hybrid: always-on policy + JIT file/doc loads via tools.  
  4. Enable tools per phase; avoid “all tools always on.”  
  5. When packing RAG, account for Lost-in-the-Middle (edges vs middle).  
  6. Label trust tiers per source (user / retrieved / memory / system) for later Dual-LLM routing.

---

### Memory systems (short-term vs long-term)

* **Fundamentals:**  
  **Memory** is how an agent retains information beyond a single model call. Context engineering cares because memory decides what *may* be selected into the window later. Two scopes dominate industry docs:

  | Scope | Also called | Typical mechanism | Lifetime |
  |-------|-------------|-------------------|----------|
  | **Short-term / session** | Thread memory, working memory | Message list + checkpointed graph state | One conversation / thread |
  | **Long-term / persistent** | Cross-session memory | Store / memory files / profiles / collections | Across threads & days |

  LangGraph persistence (official docs):

  - **Checkpointers** — persist a thread’s **graph state** as checkpoints. Short-term, **thread-scoped**. Enables conversation continuity, human-in-the-loop, time travel, fault tolerance. Access via `thread_id` in config.  
  - **Stores** — persist application-defined key-value / JSON documents **outside** graph state. Long-term, **cross-thread**. Namespaces (e.g. `(user_id, context)`) + keys. Supports semantic search over memories when indexed.

  Compile with both: `graph.compile(checkpointer=..., store=...)`. Short-term updates on each invoke/step; long-term is read/written from nodes when application logic decides. Docs warn: long conversations exceed windows and degrade quality even when they fit — manage messages (trim, summarize, filter).

  Memory types (LangGraph / CoALA-inspired):

  | Type | Stores | Agent example |
  |------|--------|---------------|
  | **Semantic** | Facts | User preferences, account attributes |
  | **Episodic** | Experiences | Few-shot trajectories of successful tool use |
  | **Procedural** | Instructions | Evolving system prompt / rules files |

  Write timing: **hot path** (agent saves during the user turn — transparent; adds latency) vs **background** / “dreaming” (async job reviews transcripts and proposes updates — Mukta, Anthropic AI Native DevCon).

  Claude Managed Agents: sessions start fresh by default; **memory stores** are workspace-scoped text document collections mounted at `/mnt/memory/{slug}/`; attach at session create via `resources[]`. Patterns: one store per end user; org standards as **read_only** + per-user **read_write**; injection risk when untrusted input + `read_write` can poison future sessions; version history for audit/rollback. Anthropic also describes **structured note-taking** inside a session (NOTES.md / TODO) as agentic memory that survives compaction better than raw transcripts.

  OpenAI patterns (public): legacy Assistants + Threads (sunset path → Responses + Conversations); Responses API chains with `previous_response_id` or durable Conversations items; application-owned DB still common for true cross-product memory. Chip Huyen (*Agents*): agents often exceed context limits; a memory system that supplements the window is essential.

* **The Alternatives:**  

  | Design | Pros | Cons |
  |--------|------|------|
  | Checkpointer only | Simple resume; HITL | No cross-thread personalization |
  | Store only | Durable facts | No automatic turn transcript |
  | **Both** (LangGraph default advice) | Full coverage | Two systems to operate |
  | Single profile JSON | Coherent user model | Patch errors as profile grows |
  | Memory collection / files | High recall; easy append | Selection harder; over-insert |
  | Provider-managed memory (ChatGPT-like) | UX magic | Opaque; surprise retrieval |
  | Markdown files as memory (Claude) | Auditable; agent-native | Concurrent writers need versioning |

  | Hot path vs background writes | |
  |-------------------------------|--|
  | Hot path | Immediate availability; user-visible “saved” |
  | Background / dreaming | No latency tax; needs trigger policy & review |

  The syllabus build requires **session memory** (checkpointer-class persistence of messages + scratchpad). Long-term stores are the cross-session companion; both must be namespaced for isolation.

* **Failure Modes:**  
  - Restarting a worker process **wipes** “memory” that was only RAM messages — users see amnesia.  
  - Putting all users in one store namespace → **cross-tenant leak**.  
  - Writing every tool trace into long-term memory → **poisoning** and distraction forever.  
  - Relying on the raw checkpoint message list as long-term truth → unbounded cost and Lost-in-the-Middle.  
  - Prompt injection that says “remember the admin API key” persists if the write path is unguarded (OWASP context poisoning; Anthropic `read_only` guidance).

* **Average vs. Strong Engineer:**  
  **Average:** client sends full history each call; “memory” is the chat sidebar; no namespaces; `InMemorySaver` in anything resembling prod.  
  **Strong:** Postgres/SQLite checkpointer in prod; store namespaces include `tenant_id` + `user_id`; memory write tools require allowlists; evaluate memory *selection* precision/recall; whiteboard checkpointer vs store in customer language (“this week’s ticket thread” vs “evergreen preference”); demonstrate read_only org memory; document retention & redact via version APIs. Procedural memory in rules files always loaded; semantic memories selective. LangMem-like libraries are helpers, not substitutes for namespace design.

* **Worked Example:**  
  Deployment Copilot’s graph compiles with a Postgres checkpointer keyed by `thread_id=incident-{id}` and a store namespace `(tenant_id, user_id, "prefs")`. Session scratch fields (`plan`, `NOTES`) live in checkpointed state; evergreen facts (“prefer blue/green for payments-api”) live in the store and are **selected** into the memory layer only when the incident touches that service. Org runbooks mount read_only. A background job proposes new preferences from resolved incidents; hot-path writes are limited to explicit “remember this” tool calls behind an allowlist.

* **Apply It:**  
  1. Persist session state (messages + scratchpad) via a checkpointer with stable `thread_id`.  
  2. Add a long-term store with `(tenant, user, …)` namespaces — never a global blob.  
  3. Prefer `read_only` for shared org memory; gate `read_write` against untrusted content.  
  4. Decide hot-path vs background write policy; document it.  
  5. Do not treat the raw message list as long-term truth — trim/summarize/select.  
  6. Use structured notes (NOTES/TODO) that survive compaction better than full transcripts.

---

### Context compaction

* **Fundamentals:**  
  **Compaction** shrinks a growing session context into a smaller representation so the agent can continue past token budgets **without** naively truncating the only copy of critical decisions.

  Anthropic definition (*Effective context engineering…*): take a conversation nearing the limit, **summarize**, reinitiate a window with the summary (plus carefully chosen residue such as recent files). Goal: high-fidelity continuity with minimal performance degradation.

  Why not only truncate?

  | Naive trim | Compaction |
  |------------|------------|
  | Drops oldest messages blindly | Distills decisions, bugs, constraints |
  | May delete the policy user stated turn 1 | Prompted to preserve architectural choices |
  | Cheap | Costs a summarization call; can lose subtlety |

  Related operations (LangChain compress bucket):

  - **Summarization** — LLM distill of trajectory or tool output.  
  - **Trimming / pruning** — heuristic drop (e.g. remove messages before last N; clear old tool payloads).  
  - **Tool-result clearing** — lightest compaction: keep that a tool was called; drop bulky raw output once consumed (Anthropic notes this as a platform feature).

  Thresholds and timing:

  - Claude Code: auto-compact near capacity (~95% default in operator docs; override via env). Proactive `/compact` with optional focus instructions — better because **context rot** means the model is weakest when the window is fullest.  
  - OpenAI Responses: `context_management` with `compact_threshold` for **server-side** compaction mid-stream; or standalone `POST /responses/compact` returning a new window including an **encrypted compaction item** (opaque, ZDR-friendly with `store=false`).  
  - LangGraph: utilities to summarize/trim message lists; or custom summarize nodes between phases / at agent boundaries.

  Compaction quality loop (Anthropic): (1) maximize **recall** — summarizer must not omit critical constraints; (2) then improve **precision** — strip superfluous tool HTML, duplicate searches; (3) evaluate on **complex agent traces**, not toy chats. Structured note-taking complements compaction: durable NOTES outside the window are re-read after reset.

* **The Alternatives:**  

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

  Tradeoff: compaction frequency vs fidelity. Too rare → distraction/rot. Too often → thrashing and lost detail. The syllabus requires a **configured threshold**, not “compact when the API errors.”

* **Failure Modes:**  
  - Long coding/research agents **die** at the window ceiling mid-migration.  
  - Cost/latency grow linearly with transcript length even when 90% is obsolete tool JSON.  
  - Models enter **context distraction** (Breunig): repeat past actions instead of planning.  
  - Teams “fix” by switching to a larger model when they needed **summary + tool clearing**.  
  - Overly aggressive compaction deletes a constraint whose importance appears only later → silent policy break.  
  - Compacting a **poisoned** thread can entrench poison into the summary canon.  
  - Compaction fires too late (at hard limit) when the model is already at peak context rot — Anthropic: model is least intelligent when forced to compact.

* **Average vs. Strong Engineer:**  
  **Average:** catch context-length exceptions; retry with clipped history; user starts a new chat.  
  **Strong:** meter tokens every turn; compact at threshold; clear tool results after use; keep last user goals + decision log verbatim when possible; unit-test summarizer prompts on golden traces; log before/after token counts and a hash of preserved constraint list; choose auditable vs opaque compaction per compliance regime; never compact away **authorization** decisions without re-injecting them as system pins. Claude: steer `/compact` with instructions; put durable rules in `CLAUDE.md` so they survive summary. OpenAI: after server compaction, drop items before the latest compaction item when using input-array chaining; do not manually prune when using `previous_response_id`.

* **Worked Example:**  
  Deployment Copilot’s incident thread hits ~180k tokens of kubectl and log dumps. At **70% of the model window** (threshold config), a summarize node runs: preserve freeze-calendar constraint, approved rollback decision, and last three file paths; clear raw tool payloads older than the previous phase. Traces log `tokens_before`, `tokens_after`, and `constraint_hash`. A golden long-session eval asserts the freeze rule still appears in the post-compact policy pin. NOTES.md still holds the migration checklist so a second compact cannot erase it.

* **Apply It:**  
  1. Meter tokens (or % of window) every turn in the session path.  
  2. Configure a compaction threshold below the hard limit; prefer proactive compact over error-driven clip.  
  3. Implement summarize + tool-result clearing; keep decision/constraint pins.  
  4. Log before/after token counts and preserved-constraint hashes on `session_id`.  
  5. Evaluate summarizer fidelity on complex agent traces, not toy chats.  
  6. Pair with structured notes that re-enter after reset; do not compact away auth decisions without re-inject.

---

### Context isolation

* **Fundamentals:**  
  **Context isolation** means each agent (or agent role, or tenant session) operates with a **bounded window and memory namespace** so tokens from one lineage do not silently become instructions or evidence for another.

  Why it matters:

  1. **Correctness** — Agent B should not “remember” Agent A’s abandoned hypotheses (context clash / poisoning).  
  2. **Security** — Untrusted content processed by a worker must not reach a privileged tool-caller (prompt injection).  
  3. **Budget** — Exploratory search can burn tens of thousands of tokens; parents should see **summaries**, not raw haystacks (Anthropic multi-agent research + effective context posts).  
  4. **Tenancy** — Customer 1’s thread/memory must never mount into Customer 2’s session.

  Isolation mechanisms:

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

  Simon Willison **Dual LLM**: Privileged LLM holds tools; Quarantined LLM reads untrusted content without tools; never forward quarantined raw text back as privileged context — only structured/safe interfaces. OWASP LLM Prompt Injection Cheat Sheet lists **context poisoning** and cites Dual LLM as architectural mitigation. Context-minimization pattern (via Willison): strip user prompt from context after translating to a safe query so injection cannot continue into later turns.

* **The Alternatives:**  

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

  Week 13 reminder: split by **context boundaries** (pollution, parallelism, specialization), not vanity role names. The syllabus requires **hard isolation** of namespaces — not prompt cosplay.

* **Failure Modes:**  
  - Support bot for Tenant A cites Tenant B’s invoice numbers from a shared Redis chat key.  
  - Research worker’s hallucinated “fact” is pasted into the lead agent’s plan and becomes **poison** for all downstream tools.  
  - Injected instructions in a fetched webpage reach the privileged agent that can `send_email` / `refund`.  
  - Parent coding agent’s window fills with grep dumps; task focus collapses (rot).  
  - HITL reviewers see the wrong thread’s PII.  
  - Breunig’s **context clash** is often an isolation bug: contradictory tool results from parallel workers merged without reconciliation.

* **Average vs. Strong Engineer:**  
  **Average:** single `messages` array; “multi-agent” is prompt cosplay; one memory table.  
  **Strong:** `thread_id` and memory namespace mandatory in every invoke; subagents as tools returning summaries; red-team tests that attempt cross-tenant reads; Dual LLM or gated tools for untrusted channels; read_only shared memories; threat model diagram with trust boundaries on the context assembler; document handoff schema (allowed fields); cite OWASP + Willison in security review. LangGraph: subgraphs can use checkpoint namespaces; avoid compiling nested graphs with separate checkpointers that accidentally orphan state — inherit outer checkpointer when appropriate.

* **Worked Example:**  
  Deployment Copilot’s research worker scrapes docs and tickets for an outage. It runs in a **fresh** subagent window with no refund/email tools. Only a ~1–2k summary returns to the lead agent (findings + evidence refs + open questions). Tenant store access is namespaced `(acme, user_42, …)`; red-team tests assert Agent tools cannot read `(globex, …)`. Untrusted webpage text is processed by a quarantined path (Dual LLM); the privileged lead never sees raw HTML — only structured fields.

* **Apply It:**  
  1. Require distinct `thread_id` / memory namespace per tenant and per agent role.  
  2. Spawn exploratory work in subagents with fresh windows; return summaries only.  
  3. Keep bulky artifacts off `messages` until selectively rendered.  
  4. Mount shared org memory `read_only`; red-team cross-tenant reads.  
  5. Apply Dual LLM (or equivalent gated tools) when untrusted content meets privileged actions.  
  6. Document isolation boundaries on the assembler threat model.

---

### Multi-agent context sharing

* **Fundamentals:**  
  Multi-agent systems need **controlled sharing**: enough context for coordination, not enough to reintroduce isolation failures. Sharing is a first-class context-engineering decision — what crosses the boundary, in what form, with what trust label.

  Pattern catalog:

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

  Anthropic *How we built our multi-agent research system*: orchestrator–worker; subagents parallelize with **own contexts**; token use ~**15×** chat; **detailed task briefs** mandatory — vague assignments caused duplicate work and gaps. Effective context post: each subagent may use tens of thousands of tokens; returns ~1–2k condensed summary. LangChain: Cognition emphasizes summarization at **agent–agent boundaries**. LangGraph supervisor/swarm: separate instructions/tools/windows; control history in wrappers (`last_message` vs summary vs full). Chip Huyen (*Agents*): more tools → more documentation in context; tool outputs accumulate — multi-agent can partition that load if sharing is disciplined.

  Recommended handoff contract fields:

  ```text
  handoff_id, from_agent, to_agent,
  objective, constraints[],
  findings[], evidence_refs[],
  open_questions[],
  token_budget_used,
  trust_tier (user|retrieved|inferred)
  ```

  Missing `constraints[]` is the classic **lost context across handoffs** failure.

* **The Alternatives:**  

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

  Tradeoff from Week 13: multi-agent often **3–10×** tokens in testing; Anthropic research up to **15×**. Share less, not more, unless breadth requires it. Sharing policy is how you encode **isolation exceptions** — unwritten exceptions become bugs.

* **Failure Modes:**  
  - Workers duplicate the same web searches (wasted spend).  
  - Lead agent never sees a constraint that lived only in worker turn 3.  
  - Two workers write conflicting facts into a shared store without merge rules → clash.  
  - “Share everything” re-creates a single polluted context — isolation theater.  
  - Security: one compromised worker transcript injected into all peers.  
  - Vague briefs → duplicate work and coverage gaps (Anthropic research system lesson).

* **Average vs. Strong Engineer:**  
  **Average:** concatenate worker outputs into the next prompt; no schema; no token accounting.  
  **Strong:** typed handoff objects; summarize nodes; shared plan file with ownership; merge strategies for store writes; evaluate end-to-end *and* per-boundary faithfulness; customer-facing diagram of who sees what; refuse architectures that pipe raw PII between agents without need; align with Dual LLM when tools are involved. OpenAI: design multi-agent shares as **items**, not free text blobs, when on Responses. Claude Managed Agents: multiple memory stores per session (org + user) is a **controlled** share — not a full transcript mesh.

* **Worked Example:**  
  Deployment Copilot’s lead agent fans out two workers: “timeline of deploy events” and “blast radius for payments-api.” Each gets a typed brief with `constraints[]` (change freeze, no prod writes). Workers return summary handoffs with `handoff_id`, findings, and evidence refs — not full kubectl transcripts. A shared plan file outside both windows tracks open questions. Fan-in merges summaries; conflicting severity claims go to a reconciliation node instead of raw concat. Token accounting shows ~12× single-chat spend — accepted for breadth, with summary-only boundaries preventing a mega-context merge.

* **Apply It:**  
  1. Default to summary handoffs; ban full transcript relay unless justified.  
  2. Implement a typed handoff schema including `constraints[]` and `handoff_id`.  
  3. Use shared scratch/plan outside windows for durable coordination.  
  4. Pass artifact pointers for large bodies; JIT-load in the recipient.  
  5. Evaluate per-boundary faithfulness (constraint survival) as well as E2E success.  
  6. Brief workers with detailed objectives — vague assignments cause duplicate work.

---

### Context failure modes

* **Fundamentals:**  
  Week 9 classifies **RAG** failures (recall / rank / ground). Week 25 classifies **context** failures — anything that makes the assembled window wrong, harmful, or incomplete even when components “ran.”

  Syllabus trio (required):

  | Mode | Definition | Typical locus |
  |------|------------|---------------|
  | **Stale context** | Window or memory reflects outdated world/docs/policy | Memory store; cached RAG; old checkpoint resumed blindly |
  | **Context poisoning** | Bad or malicious content enters and is repeatedly trusted | Hallucinated “facts”; indirect prompt injection; tainted memory writes |
  | **Lost context across handoffs** | Constraints/evidence fail to cross agent or phase boundaries | Summary omissions; dropped fields; new thread without brief |

  Breunig four (industry taxonomy to map as subtypes) — Drew Breunig, *How Long Contexts Fail* (2025-06-22):

  1. **Context Poisoning** — hallucination/error enters context and is reused.  
  2. **Context Distraction** — context so long the model over-attends history vs training (agents repeating past actions; Gemini Pokémon anecdote ≳100k).  
  3. **Context Confusion** — superfluous tools/docs trigger low-quality choices.  
  4. **Context Clash** — contradictory spans derail reasoning.

  LangChain’s context-engineering post amplifies these as motivation for write/select/compress/isolate.

  **Lost in the Middle** (Liu et al., arXiv:2307.03172, TACL): multi-document QA and KV retrieval show U-shaped performance — mid-context evidence underused; longer contexts can hurt. This is the packing cousin of “lost handoff”: gold was *present* but effectively lost to attention. Anthropic **context rot**: as tokens grow, recall from context degrades — continuum toward distraction.

  Injection as poisoning: OWASP lists **Context Poisoning** — injecting false information into the agent’s working memory; also Thought/Observation forging and tool manipulation. Simon Willison: indirect injection via emails/pages that become context; Dual LLM and context-minimization as defenses. Chip Huyen: prompt injection as social engineering against models; worse when tools can act.

  Portfolio log schema (mirror Week 9):

  ```text
  incident_id, session_id, handoff_id?,
  mode: stale|poison|lost_handoff|distraction|confusion|clash|lost_in_middle,
  layer: policy|tools|rag|history|memory|handoff,
  evidence: snippet_hash, token_count, position?,
  remediation: compact|isolate|re-retrieve|reset_thread|ro_memory|...
  ```

* **The Alternatives:**  

  | Taxonomy choice | Pros | Cons |
  |-----------------|------|------|
  | Syllabus 3 only | Teachable; maps to build tasks | Misses distraction/confusion vocabulary |
  | Breunig 4 only | Industry blog resonance | Under-labels staleness & handoff loss |
  | **3 primary + Breunig/LITM subtypes** (recommended) | Coverage + portfolio clarity | Slightly heavier labeling |
  | Collapse all to “hallucination” | Easy | Wrong owners |

  | Remediation style | Risk |
  |-------------------|------|
  | Always compact | May entrench poison into the summary |
  | Always reset thread | Loses good work; user friction |
  | Re-retrieve + pin policy | Fixes stale; needs versioned corpus |
  | Quarantine + Dual LLM | Security win; product complexity |

  Remediation cheatsheet:

  | Mode | First fix |
  |------|-----------|
  | Stale | Version pins; re-retrieve; expire memories |
  | Poison | Reset/quarantine span; read_only memory; Dual LLM |
  | Lost handoff | Handoff schema + summary eval |
  | Distraction | Compact earlier; isolate workers |
  | Confusion | Shrink tool/doc set; RAG over tools |
  | Clash | Reconciliation node; don’t merge raw |
  | Lost-in-middle | Reorder; reduce *k*; pointwise cite |

  The syllabus selects **3 primary + Breunig/LITM subtypes** and a joinable failure log as the elective artifact.

* **Failure Modes:**  
  - Poisoned memory is “fixed” by adding more prompt rules — poison remains in the store.  
  - Stale policy chunks score high on faithfulness (faithful to old text) while being wrong vs production — same trap as Week 9 citation drift.  
  - Multi-agent demos fail intermittently because briefs omit ACL constraints — labeled as “model dumb.”  
  - Million-token windows hide distraction until agents loop.  
  - Security incidents are filed as jailbreaks when the path was **indirect context injection**.  
  - Compaction “helps” distraction but summarizes poison into canon.

* **Average vs. Strong Engineer:**  
  **Average:** screenshot the bad answer; tweak temperature; clear chat.  
  **Strong:** fault-injection suite — plant mid-context needles; inject conflicting tool results; write a bad memory deliberately; drop `constraints` from a handoff fixture; assert detector labels; pair with token timelines; customer RCA uses the taxonomy; distinguishes stale RAG (data) vs poison (trust) vs lost handoff (orchestration); ties to OWASP when tools + untrusted content exist; refuses to ship shared writeable memory without audit versions.

* **Worked Example:**  
  Three Deployment Copilot incidents, one log:

  1. **Stale** — resumed a week-old checkpoint after a policy change; freeze calendar in memory was outdated. Remediation: expire memories + re-retrieve; `mode=stale`, `layer=memory`.  
  2. **Poison** — a scraped runbook said “always force-push to main”; worker summary carried it into the lead plan. Remediation: quarantine span, `read_only` org memory, Dual LLM for web; `mode=poison`, `layer=handoff`.  
  3. **Lost handoff** — worker found an ACL constraint in turn 3; summary omitted `constraints[]`. Lead attempted a prod write. Remediation: schema-required field + boundary eval; `mode=lost_handoff`, join on `handoff_id`.

  A fourth trace shows the model repeating prior kubectl commands past ~100k tokens without new planning — labeled `distraction`, remediated by earlier compaction + subagent isolation. A packed gold chunk at mid-position ignored by the reader is labeled `lost_in_middle` with `position` recorded.

* **Apply It:**  
  1. Create a context failure log schema joinable on `session_id` / `handoff_id`.  
  2. Label with syllabus 3 + Breunig/LITM subtypes; record `layer` and token evidence.  
  3. Build a small fault-injection suite (stale memory, poison write, dropped constraints, mid-context needle, conflicting tools).  
  4. Pair each incident with a first-fix from the remediation cheatsheet.  
  5. Keep the log beside Week 9 RAG taxonomy — same portfolio spirit, different locus.  
  6. Refuse to close “prompt tweak” tickets when the mode is poison-in-store or lost-handoff.

---

## Week 25 build checklist (end-to-end)

Use this as the chapter’s capstone sequence; every concept above maps here.

1. **Inventory:** List every token source/layer in the Phase 3 agent stack; add per-section traces.  
2. **Session memory:** Persist messages + scratchpad via checkpointer / durable session; namespace by `thread_id`.  
3. **Compaction:** Configure a token (or % window) threshold; summarize / trim / clear tool results; log before/after counts.  
4. **Isolation:** Separate namespaces per tenant and per sub-agent; fresh windows for exploratory workers; summaries only upward.  
5. **Sharing contracts:** Typed handoffs with `constraints[]` and `handoff_id`; no full-transcript mesh by default.  
6. **Failure-mode log:** Record stale / poison / lost_handoff (+ distraction / confusion / clash / LITM); join on `session_id` / `handoff_id`.  
7. **Eval hook:** Pair long-session compaction fidelity and handoff constraint survival with Week 15 agent evals.

When those steps are true, Week 25 is done in the syllabus sense: context is an engineered budget with owners, thresholds, and failure codes — not a vibes word.

---

## Compilation notes

- All concept sections above are grounded in `research/phase-7/week-25-context-engineering/` (`00`–`07` + README).  
- No section required `[NEEDS MORE RESEARCH]` for the seven syllabus concepts covered in research files `01`–`07`.  
- Outside URLs from research are not required reading to understand this chapter; operational detail was inlined from the notes.  
- Elective placement and “does not replace Weeks 1–24” follow research `00` / README.
