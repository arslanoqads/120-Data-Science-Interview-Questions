# 00 — Week overview & syllabus mapping

> Week 11 — Agent fundamentals: loop, tools, selection, retries, stop conditions  
> Research notes (raw). Phase 3 starts here.

---

## Fundamentals

Week 11 is the **loop contract** week of Phase 3. Weeks 4–5 taught you how to call models with tools as a *single round trip*. This week makes that round trip **repeat until done**, under budgets, with typed observations and typed stops. MCP (Week 12) is how tools are *discovered and transported*. Graphs, multi-agent, and HITL (Week 13) are how loops *branch and persist*. Side-effect safety (Week 14) assumes you already know when a tool ran and whether it will run again. Evaluation (Week 15) scores **trajectories** — which do not exist if the loop is a hidden `while True`.

**What an agent is this week (vendor, not slogan):** a multi-turn conversation in which the model may request tools, *your application* executes them, results are fed back, and the model continues until it produces a final answer **or a guardrail stops it**.

OpenAI names a **five-step flow** and says the application “can continue this flow for as many tool calls as the task requires” ([Function calling](https://developers.openai.com/api/docs/guides/function-calling)):

1. Request with tools.  
2. Receive tool call(s).  
3. Execute application-side code.  
4. Send tool output (`function_call_output`, correlated by `call_id`).  
5. Receive a final response **or more tool calls**.

Anthropic’s equivalent: Claude returns `stop_reason: "tool_use"` with `tool_use` blocks (`id`, `name`, `input`); the app replies with a **user** message whose content is `tool_result` blocks (`tool_use_id`, `content`, optional `is_error`); repeat until Claude stops calling tools ([Tool use overview](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview), [Handle tool calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls)). The SDK **tool runner** automates that cycle and stops when Claude returns without tool use, or when `max_iterations` is hit ([Tool runner](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-runner)).

LangGraph makes the same cycle a **graph**: `START → llm_call → (conditional: tools?) → tool_node → llm_call → … → END`. Official quickstarts show both a `StateGraph` with `should_continue` and a Functional API `while True` that **breaks when there are no `tool_calls`** ([LangGraph quickstart](https://docs.langchain.com/oss/python/langgraph/quickstart), [Workflows and agents](https://docs.langchain.com/oss/javascript/langgraph/workflows-agents)). The graph API docs explicitly compare a two-node loop to a **ReAct agent** (model node + tools node) and require a **termination condition** plus `recursion_limit` ([Use the graph API](https://docs.langchain.com/oss/python/langgraph/use-graph-api), [Graph API overview](https://docs.langchain.com/oss/python/langgraph/graph-api)).

The slogan **plan → act → observe → repeat** is Yao et al., *ReAct: Synergizing Reasoning and Acting in Language Models* (arXiv:**2210.03629**). In 2026 APIs, “plan” is the model’s reasoning + tool choice, “act” is *your* executor, “observe” is injecting `tool_result` / `function_call_output` / `ToolMessage`. Do not implement ReAct as unbounded thought–action traces in free text; use native tool calling.

Harrison Chase (AI Engineer World’s Fair, *3 ingredients for building reliable enterprise agents*): enterprise adoption is **value if right × P(success) − cost if wrong**. LangGraph exists to put **required behavior in control flow** (not only in the prompt) so P(success) rises and failure cost drops via reversible actions and review ([talk page](https://ai.engineer/talks/3-ingredients-for-building-reliable-enterprise-agents), YouTube `kTnfJszFxCg`). Week 11’s contribution to that formula is **P(success) of a single ReAct cycle** and **cost if the loop never stops**.

**This week’s artifact is a bounded loop + three tools + a stop taxonomy**, not a framework logo.

### Starter tool palette (syllabus: calendar, doc search, structured query)

Use **three mutually exclusive capabilities** so Week 11 practices *selection* without a 40-tool CRM dump. Names below are examples; keep them next to executors in code.

| Tool | Side effects | When to use | When **not** to use |
|------|----------------|-------------|---------------------|
| **`docs_search`** | Read-only | User asks about policies, runbooks, product docs, “what does the handbook say” | Exact row/metric from a warehouse; “put it on my calendar” |
| **`structured_query`** | Read-only (default); writes are a *different* tool next week | Filters, counts, joins against a typed store (tickets, orders, employees) with a constrained query object | Keyword search over PDFs; creating meetings |
| **`calendar_list_events`** | Read-only | “Am I free Tuesday?”, “what’s on the team calendar” | Searching the knowledge base |
| **`calendar_create_event`** | **Write** | User explicitly asked to schedule; you have title, start, end, timezone | Model “helpfully” booking after a search; never auto-retry without `idempotency_key` |

**`docs_search` (OpenAI-shaped sketch)** — hybrid/keyword over an indexed corpus (Week 7–10 stack). Return *evidence*, not an answer:

```json
{
  "type": "function",
  "name": "docs_search",
  "description": "Keyword/semantic search over the internal document corpus (policies, runbooks, product docs). Use when the user needs quoted or cited handbook text. Do not use for warehouse metrics, ticket IDs, or calendar availability.",
  "strict": true,
  "parameters": {
    "type": "object",
    "properties": {
      "query": { "type": "string", "description": "User intent in search terms, not a full chat transcript." },
      "k": { "type": "integer", "description": "Max chunks to return (1–8). Default 5 if omitted is not allowed in strict schemas — always pass k." }
    },
    "required": ["query", "k"],
    "additionalProperties": false
  }
}
```

**`structured_query` (Anthropic-shaped sketch)** — *not* free-form SQL from the model. Pass a constrained object the executor compiles (allowlisted tables, parameterized filters). This is the FDE “don’t let the model write SQL” pattern for Week 11; Week 21 covers messy SQL.

```json
{
  "name": "structured_query",
  "description": "Read-only query against the operational store (tickets, orders, employees). Use for counts, filters, and lookups by id/status/date. Do not use for prose documents or calendar. Never invent table names; only use tables listed in the enum.",
  "strict": true,
  "input_schema": {
    "type": "object",
    "properties": {
      "entity": { "type": "string", "enum": ["ticket", "order", "employee"] },
      "filters": {
        "type": "object",
        "properties": {
          "id": { "type": "string" },
          "status": { "type": "string" },
          "updated_after": { "type": "string", "description": "ISO-8601 date" }
        },
        "additionalProperties": false
      },
      "limit": { "type": "integer" }
    },
    "required": ["entity", "filters", "limit"],
    "additionalProperties": false
  }
}
```

**`calendar_list_events` / `calendar_create_event`:** split **read vs write**. List takes `time_min`, `time_max`, `calendar_id`, `timezone`. Create takes `title`, `start`, `end`, `timezone`, `attendees[]`, **`idempotency_key`** (client-generated UUID for the user intent). Description of create must say: *only after the user confirmed time and attendees; do not use to search docs or tickets*.

**Canonical multi-step task for traces:** “Find the PTO policy snippet, check how many PTO tickets Alice has open, and propose (do not silently create) a 30-minute calendar block to review them.” Expected trajectory: `docs_search` → `structured_query` → `calendar_list_events` → **final text proposal** (create is HITL / Week 13 unless the user said “book it”).

---

## Alternatives & Tradeoffs

| Path | What you optimize | What you sacrifice |
|------|-------------------|-------------------|
| **Manual message loop** (OpenAI/Anthropic raw) | Full control: HITL, custom streaming, mixed server+client tools | Easy to get pairing/ordering wrong; you own retries and caps |
| **Anthropic tool runner / OpenAI Agents SDK** | Loop, validation, `max_iterations` / `max_turns`, hooks | Less transparent; beta surfaces change; still need *your* stop taxonomy in logs |
| **LangGraph `llm_call` ↔ `tool_node`** | Explicit edges, `recursion_limit`, checkpoints, path to Week 13 | Heavier than a single ReAct loop for three tools |
| **LangGraph Functional API `while True`** | Looks like application code | Same footguns as naive while unless you add caps |
| **Always one tool then stop** | Predictable cost | Cannot solve the PTO+calendar task |
| **Unbounded ReAct demo** | Looks smart on stage | Cost explosions, duplicate writes, 400s on unpaired results |

| Palette design | Pros | Cons |
|----------------|------|------|
| **Three tools (syllabus)** | Disambiguation is teachable; traces are short | Not a realistic CRM catalog (that is tool search, file 03) |
| One mega `do_anything` tool | Tiny schema | Model dumps unstructured args; no selection practice |
| 80 MCP tools on day one | Feels “platform” | Selection collapse; Week 12 before Week 11 |

Harrison Chase: put **reliability in the graph**, not only in the prompt. For Week 11 that means caps, pairing, and error-as-observation — even if the graph is two nodes.

---

## Necessity

If Week 11 is skipped or is a toy `while True`:

- Agents **hang** (iteration/token/$/wall-clock unbounded) or **crash** (Anthropic HTTP 400: `tool_use` ids without matching `tool_result` immediately after).  
- `max_tokens` truncates a tool-call JSON blob; the next turn is illegal or hallucinated.  
- Write tools **double-fire** on retries (two calendar events, two refunds).  
- Week 12 MCP looks like “magic tools” instead of the same JSON-schema surface over a different transport.  
- Week 13 graphs have no **semantic** stop vs **recursion** stop distinction.  
- Week 15 trajectory eval has no consistent turn schema.  
- Interview answer collapses to “we used LangChain agents” with **no stop reason, no pairing rule, no idempotency**.

LangGraph’s thinking-in-langgraph doc classifies tool failures as **LLM-recoverable**: store the error in state and loop back so the model can adapt — not raise out of the node ([Thinking in LangGraph](https://docs.langchain.com/oss/python/langgraph/thinking-in-langgraph)). That is the same contract as Anthropic `is_error: true`.

---

## Industry Practice

- **Common (demo AI):** `while True` until no `tool_calls`; `get_weather` schema; hope; no metrics; crash on exception; one calendar tool that both lists and creates.  
- **Strong:** max iterations (often **5–25** depending on domain); per-tool timeouts; structured stop taxonomy; trace each turn; `strict` schemas; read/write split; tool runner / Agents SDK when custom control is unused.  
- **FDE bar:** name OpenAI’s five steps and Anthropic’s pairing rules; show a **three-tool** trace; distinguish **executor retry** vs **model retry**; cite LangGraph `recursion_limit` (default **1000** super-steps as of Graph API 1.0.6 — **set it yourself**, do not inherit a demo 25 vs 1000 surprise) and Anthropic `max_iterations`; treat tool results as **untrusted** (indirect prompt injection).

Anthropic documents preferring the **tool runner** for custom-tool agents and dropping to a manual loop only for transport/custom shapes ([Tool runner](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-runner)). OpenAI points the same loop at the **Agents SDK** if you want packaged orchestration ([Function calling](https://developers.openai.com/api/docs/guides/function-calling)).

---

## Concrete Scenario

**Product:** internal ops copilot (FDE-shaped). User: “What’s the PTO carryover rule, how many open PTO tickets does Alice have, and book 30 minutes with her tomorrow afternoon if I’m free.”

**Legal, documented loops to copy mechanics from (not the business domain):**

- OpenAI `get_horoscope` end-to-end: define function + `strict: true` → execute locally → `function_call_output` with matching `call_id` → final NL answer: https://developers.openai.com/api/docs/guides/function-calling  
- Anthropic `get_weather` client-tool round trip: `input_schema` + `tool_result`: https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview  
- Anthropic multimodal **zoom** cookbook: `client.beta.messages.toolRunner(..., max_iterations=20)` **and** a manual loop with dispatch-by-name + `is_error` recovery: https://platform.claude.com/cookbook/multimodal-crop-tool  
- LangGraph quickstart: `llm_call` / `tool_node` / `should_continue`; Functional API `while True` **with a break**: https://docs.langchain.com/oss/python/langgraph/quickstart  
- LangGraph thinking-in-langgraph: `execute_tool` catches exceptions, writes `"Tool error: …"` into state, `goto="agent"`: https://docs.langchain.com/oss/python/langgraph/thinking-in-langgraph  

**Expected Week 11 run (pass):** `docs_search(query="PTO carryover", k=5)` → `structured_query(entity="ticket", filters={status:open, …}, limit=20)` → `calendar_list_events(...)` → if user said “book it” **and** slot is free: `calendar_create_event(..., idempotency_key=…)` **once** → `stop_reason=end_turn`. **Fail (teachable):** naive while retries create on HTTP 500 → two events; or unpaired `tool_use` → 400.

**Talks:** Mahesh Murag, Anthropic — *Building Agents with MCP*, AI Engineer Summit (tools as a product surface; Week 12 deepens MCP, Week 11 needs the “tool menu + loop” mental model): https://youtu.be/kQmXtrmQ5Zg — Harrison Chase, LangChain/LangGraph — *3 ingredients…*: https://www.youtube.com/watch?v=kTnfJszFxCg — channel: https://www.youtube.com/@aidotengineer

---

## Open Questions

- When should “plan” be a **separate** LLM call (planner–executor) vs implicit in one ReAct model? (Chase: put *required* steps in the graph; optional reasoning can stay in the model.)  
- Is `max_iterations` enough, or do production systems need budgeted **tool-call trees** with per-branch caps?  
- How do **hosted server tools** (OpenAI built-ins, Anthropic `web_search` / `code_execution`) change the loop when the provider owns part of act/observe?  
- Should the model **see remaining budget** as an observation so it wraps up, or is that a prompt injection of ops concerns?  
- Three tools are pedagogically clean; when does an FDE engagement *have* to jump to tool search in Week 11 vs wait for a 30-tool catalog?

---

## Sources

- https://developers.openai.com/api/docs/guides/function-calling  
- https://developers.openai.com/api/docs/guides/tools-tool-search  
- https://openai.github.io/openai-agents-python/tools/  
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview  
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls  
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-runner  
- https://platform.claude.com/cookbook/multimodal-crop-tool  
- https://docs.langchain.com/oss/python/langgraph/quickstart  
- https://docs.langchain.com/oss/python/langgraph/graph-api  
- https://docs.langchain.com/oss/python/langgraph/use-graph-api  
- https://docs.langchain.com/oss/python/langgraph/thinking-in-langgraph  
- https://docs.langchain.com/oss/javascript/langgraph/workflows-agents  
- https://arxiv.org/abs/2210.03629  
- https://ai.engineer/talks/3-ingredients-for-building-reliable-enterprise-agents  
- https://www.youtube.com/watch?v=kTnfJszFxCg  
- https://youtu.be/kQmXtrmQ5Zg  
- https://www.youtube.com/@aidotengineer  
