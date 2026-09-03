# 03 — Tool selection and disambiguation

> Week 11 — Agent fundamentals  
> Research notes (raw).

---

## Fundamentals

**Tool selection** is the model’s choice of **which named capability** to invoke given the user goal and the tool list in context. Failures:

- **Wrong twin** — `docs_search` vs `structured_query` vs `calendar_list_events` when names/descriptions overlap (“search”, “get”, “lookup”).  
- **None when one is needed** — model answers from parametric memory about a policy that lives in the corpus.  
- **Shotgun parallel** — calls search *and* SQL *and* calendar for “what’s the PTO rule?”  
- **Write instead of read** — `calendar_create_event` when the user asked “am I free?”  
- **Deferred-search miss** — tool search loads the wrong subset; the right tool was never in context.

This is not “the model is dumb.” It is **attention over a menu**. Every extra tool is a competing description.

### Vendor techniques

1. **Better descriptions (first lever)**  
   Anthropic’s handle-tool-calls guidance when Claude picks wrong tools: improve **`description` specificity**; point to “Define tools” ([Handle tool calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls)). Encode **when not to use**. Week 11 starter tools (overview) are a worked example: docs vs structured vs calendar.

2. **Fewer tools in context**  
   Large catalogs dilute attention and burn tokens (schemas are prompt). Merge duplicates. Split agents (Week 13) so each sees a **small palette**. Harrison Chase: reliability via **narrower, more workflow-like** autonomy — not 80 peer tools on one brain ([AI Engineer talk](https://ai.engineer/talks/3-ingredients-for-building-reliable-enterprise-agents)).

3. **`tool_choice` constraints**  
   - OpenAI / Agents SDK: `auto` | `required` | `none` | named tool. Named force is for **forms / known workflows**. `required` breaks chitchat and “I don’t know.” Agents SDK: **reset `tool_choice` to `auto` after a call** or you loop forever ([Agents](https://openai.github.io/openai-agents-python/agents/)). With tool search, named `tool_choice` **cannot** target bare namespaces, deferred-only tools, or `tool_search` itself — prefer `auto`/`required` ([Agents SDK tools](https://openai.github.io/openai-agents-python/tools/)).  
   - Anthropic: `tool_choice` type auto/any/tool; `disable_parallel_tool_use: true` reduces shotgun calling ([Tool use overview](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview)).

4. **Disable parallel when order matters**  
   Docs → SQL → calendar is **sequential** (later calls need earlier observations). Parallel is for independent reads (`docs_search` + `calendar_list_events` only if truly independent). Wrong parallel = wasted calls + confused synthesis.

5. **Tool search / deferred loading (“RAG for tools”)**  
   OpenAI `tool_search` (gpt-5.4+): mark functions/MCP `defer_loading: true`; model searches and loads only needed tools; hosted or client-executed search ([Tool search](https://developers.openai.com/api/docs/guides/tools-tool-search)). Agents SDK: exactly one `ToolSearchTool()`; searchable surfaces include `@function_tool(defer_loading=True)`, `tool_namespace(...)`, `HostedMCPTool(..., defer_loading)` ([Tools](https://openai.github.io/openai-agents-python/tools/)). Anthropic exposes server-side `tool_search` analogously (overview).  
   **Wrong search query still loads an irrelevant subset** — selection quality is now **index + descriptions**.

6. **Namespaces / grouping**  
   OpenAI Agents SDK `tool_namespace(name="crm", description="...", tools=[...])` — load a **group** instead of 15 near-duplicates. Mix immediate (always loaded) and deferred tools in one namespace. Prefer namespaces or MCP servers over dozens of individually deferred functions.

7. **Router / multi-agent (boundary of this week)**  
   Billing vs search vs calendar as **separate agents** (Week 13). Week 11 should **feel** the pain of a 3-tool palette done well before adding a router.

8. **Embeddings over tool docs (custom)**  
   Enterprise catalogs sometimes retrieve tool definitions with the same hybrid stack as docs. Not first-party; you own eval of retrieval@k for **tools**.

### Disambiguation recipe for the syllabus triad

| User language | Tool | Why the others lose |
|---------------|------|---------------------|
| “What does the handbook say about X?” | `docs_search` | Not a row in a DB; not a meeting |
| “How many open tickets does Alice have?” | `structured_query` | Not in PDFs; not calendar |
| “Am I free Thursday 3pm?” | `calendar_list_events` | Don’t SQL the calendar replica; don’t search Confluence |
| “Book 30 minutes with Alice” | `calendar_create_event` | Only after list/confirm; not search |

Put those **negative** sentences in the `description` fields. Names should be **verb_noun** and non-overlapping (`search` appearing in two names is a smell — `docs_search` vs `structured_query` is intentional).

---

## Alternatives & Tradeoffs

| Strategy | When it helps | Cost |
|----------|---------------|------|
| Rewrite descriptions + when-not-to | Near-duplicate names; Week 11 triad | Human curation; eval set |
| Fewer tools / merge | Any catalog | Product negotiation |
| `disable_parallel` / `parallel_tool_calls: false` | Sequential tasks; shotgun | Extra latency on independent reads |
| `tool_choice: required` / named | Forms, “always look it up” | Breaks refusal, small talk, already-in-context answers |
| Deferred tool search | **~20–100+** tools | Extra latency; model/version (gpt-5.4+); search quality |
| Namespaces | Related families (crm, billing) | Named `tool_choice` limitations |
| Multi-agent split | Distinct domains | Orchestration (Week 13) |
| Embedding router over tool docs | Dynamic enterprise catalogs | Custom infra; another RAG problem |

Tradeoff: one mega-agent is simpler to ship; **selection quality collapses as tools grow**. Industry response is **retrieval over tools**, not infinite prompt stuffing — but retrieval can load the **wrong** 10 tools.

Do **not** start Week 11 with `defer_loading` on three tools. You cannot tell description bugs from search bugs.

---

## Necessity

Ambiguous tools cause:

- **Wrong side effects** — refund vs cancel; create vs list.  
- **Wasted API calls** and user-visible thrashing.  
- **Authz holes** — model picks a high-privilege twin because the description was shorter.  
- **Eval noise** — Week 15 “trajectory fail” that is really a menu design fail.  
- With deferred loading: **silent unavailability** of the correct tool.

If you skip disambiguation work, you will “fix it in the system prompt” (`always use docs_search for policies`) which **rots** the moment a fourth tool is added.

---

## Industry Practice

- **Common:** dump all CRM/Jira/Slack/MCP tools into one agent; debug with “please use X”; enable parallel because it looks faster.  
- **Senior:**  
  - Inventory tools; merge duplicates; **mutual exclusion in descriptions**.  
  - Golden prompts for **tool-choice accuracy** (Phase 3 Week 15): N user utterances → expected tool (or none).  
  - Adopt tool_search past **~20–30** tools (heuristic from prior notes + OpenAI’s “many functions or large schemas” guidance).  
  - Route by intent to specialized agents when domains diverge.  
  - Log `chosen_tool` vs `expected_tool` in traces.  
  - Keep a **hot set** (always loaded: search + query + list) and defer rare writes/admin tools.  
- **FDE bar:** explain why `docs_search` vs `structured_query` is the **same** problem as `search_tickets` vs `search_kb` at 10× catalog size; cite tool_search docs and namespace rules; mention Murag’s MCP talk as **distribution**, not selection magic.

---

## Concrete Scenario

**OpenAI Tool search:** add `tool_search`, set `defer_loading: true` on rarely used functions/MCP so definitions are not all loaded up front — fewer tokens, better selection among large inventories: https://developers.openai.com/api/docs/guides/tools-tool-search  

**Agents SDK:** `tool_namespace` + `ToolSearchTool()` + defer_loading constraints: https://openai.github.io/openai-agents-python/tools/  

**Week 11 lab (small palette, no search yet):** 20 paraphrases:

- 5 should call **only** `docs_search`  
- 5 **only** `structured_query`  
- 5 **only** `calendar_list_events`  
- 3 chitchat → **no tool**  
- 2 sequential (docs then SQL) → **not** parallel both on turn 1  

Score **tool-choice accuracy**. Then **deliberately** rename `structured_query` to `search_records` and watch accuracy drop — that is the disambiguation lesson.

**Talks:** Mahesh Murag, *Building Agents with MCP* (AI Engineer Summit) — MCP + agents, ecosystem tool surfaces (selection still depends on names/descriptions): https://youtu.be/kQmXtrmQ5Zg — Harrison Chase — narrower control flow vs unbounded tool menus: https://www.youtube.com/watch?v=kTnfJszFxCg  

---

## Open Questions

- Is tool search enough, or do enterprises need **typed capability registries** with auth scopes (tool not even visible unless the token allows it)?  
- Should disambiguation be **model-side** (better LLMs) or **system-side** (routers, allowlists per tenant)? Chase’s talk argues control flow; tool search argues retrieval.  
- Who evaluates the **tool retriever** (nDCG over tools) vs the **agent**?  
- Parallel-by-default: should descriptions include “independent of X” annotations for the model, or should the executor **serialize** writes always?

---

## Sources

- https://developers.openai.com/api/docs/guides/tools-tool-search  
- https://developers.openai.com/api/docs/guides/function-calling  
- https://openai.github.io/openai-agents-python/tools/  
- https://openai.github.io/openai-agents-python/agents/  
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview  
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls  
- https://ai.engineer/talks/3-ingredients-for-building-reliable-enterprise-agents  
- https://youtu.be/kQmXtrmQ5Zg  
- https://www.youtube.com/watch?v=kTnfJszFxCg  
- https://www.youtube.com/@aidotengineer  
