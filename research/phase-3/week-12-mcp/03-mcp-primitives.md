# 03 — Resource vs tool vs prompt primitives

> Week 12 — Model Context Protocol  
> Research notes (raw).

---

## Fundamentals

MCP servers expose three **server primitives**. The spec’s **control hierarchy** is the whole design ([Server overview](https://modelcontextprotocol.io/specification/2025-11-25/server)):

| Primitive | Control | Role | Typical methods | Example |
|-----------|---------|------|-----------------|---------|
| **Prompts** | **User-controlled** | Templated workflows / slash commands | `prompts/list`, `prompts/get` | `code_review`, `research_workflow` |
| **Resources** | **Application-controlled** | URI-addressed context | `resources/list`, `resources/read`, templates, subscribe | `file:///project/src/main.rs`, DB schema |
| **Tools** | **Model-controlled** | Executable actions | `tools/list`, `tools/call` | API POST, search, file write |

Hosts **may** implement any UX; the protocol does not mandate pickers vs auto-attach vs slash commands. If you collapse all three into tools, you are not “using MCP”; you are using **one** primitive.

Mental model: **resources = context**, **tools = actions**, **prompts = packaged plays**.

Advertise capabilities in `initialize` or clients must not call the methods (file 01).

### Tools (model-controlled)

Spec: [Tools](https://modelcontextprotocol.io/specification/2025-11-25/server/tools). Learn blurb: [Tools docs](https://modelcontextprotocol.io/docs/concepts/tools).

- Unique `name` (SHOULD 1–128 chars; `[A-Za-z0-9_.-]`; case-sensitive; unique **per server**).  
- `inputSchema`: JSON Schema object (default draft **2020-12**). Empty args: `{ "type": "object", "additionalProperties": false }`.  
- Optional `title`, `description`, `icons`, `outputSchema`, `annotations`, `execution.taskSupport`.  
- **Annotations are untrusted** unless the server is trusted.  
- Pagination on `tools/list` (`cursor` / `nextCursor`).  
- `listChanged` → `notifications/tools/list_changed`.  
- Call: `tools/call` with `name` + `arguments`.  
- Result: `content[]` (text, image, audio, `resource_link`, embedded `resource`) + optional `structuredContent` + `isError`.  
- If `outputSchema` is set: server MUST conform; clients SHOULD validate. Also emit serialized JSON as text for compatibility.  
- `structuredContent` is **not** LLM structured-output mode.

**Two error channels** (same split as Anthropic `is_error` in Week 11):

1. **Protocol / JSON-RPC** — unknown tool, malformed `CallToolRequest`, server faults (`-32602` unknown tool, …). Models rarely recover.  
2. **`isError: true` in the result** — business/validation failures. Clients SHOULD feed these to the model for self-repair.

Security (spec): servers MUST validate inputs, access control, rate limit, sanitize outputs. Clients SHOULD confirm sensitive ops, **show arguments before send** (exfil risk), validate results before the LLM, timeouts, audit logs. **HITL SHOULD exist to deny invocations.**

Tool results MAY point at resources (`resource_link`) without those URIs appearing in `resources/list`.

### Resources (application-controlled)

Spec: [Resources](https://modelcontextprotocol.io/specification/2025-11-25/server/resources). Concepts: [Resources docs](https://modelcontextprotocol.io/docs/concepts/resources).

- Identified by **URI**. Optional MIME, `size`, `title`, `description`, `icons`.  
- Hosts may: tree UI, search, **heuristics / auto-include**, or ignore them.  
- Caps: `subscribe`, `listChanged` independently.  
- `resources/read` → `contents[]` as `text` or base64 `blob`.  
- **Templates:** `resources/templates/list` with `uriTemplate` (e.g. `file:///{path}`); completions API may autocomplete args.  
- Subscribe: `resources/subscribe` → `notifications/resources/updated` → client re-reads.  
- Annotations: `audience` (`user` / `assistant`), `priority` 0–1, `lastModified` ISO-8601.  
- URI schemes: `https://` only if the **client** can fetch itself; else custom/file. `file://` need not be a real FS (`inode/directory` XDG type allowed). `git://`. Custom per RFC3986.  
- Errors: not found **`-32002`**; internal `-32603`.  
- Security: **validate URIs**; prevent **path traversal** on `file://`; access control; binary encoding.

Resources are the right default for **schemas, runbooks, config snapshots** — data the **app** should attach without waiting for the model to guess a tool.

### Prompts (user-controlled)

Spec: [Prompts](https://modelcontextprotocol.io/specification/2025-11-25/server/prompts).

- `prompts/list` / `prompts/get` with `arguments`.  
- Result: `messages[]` with `role` `user` | `assistant` and content (text, image, audio, embedded resource).  
- Intended UX: **slash commands / menus**.  
- Errors: invalid name / missing args → `-32602`.  
- Security: validate I/O against injection and unauthorized resource embed.

Workshop servers register prompts like `research_workflow` / `linkedin_post_workflow` so users don’t remember tool choreography ([AI Engineer Europe repo](https://github.com/samtalasila/ai-engineer-europe)).

Prompts are **portable plays**. They are **not** LangGraph. Hosts that never call `prompts/get` leave this primitive dead.

### Client primitives (not substitutes)

Servers may **call into** the host ([Architecture overview](https://modelcontextprotocol.io/docs/learn/architecture), [Sampling](https://modelcontextprotocol.io/specification/2025-11-25/client/sampling)):

- **Sampling** — `sampling/createMessage`; server stays model-agnostic (no API keys in the server). Client SHOULD HITL. Can nest **tool loops** if `sampling.tools` is advertised. User reject → JSON-RPC `-1`.  
- **Elicitation** — ask the user for input/confirmation.  
- **Logging** — structured logs to the client.  
- **Roots** — filesystem/URI boundaries the client provides (`roots/list`; Code documents this).

Do not implement “the server has its own Anthropic key” if sampling would keep policy/keys in the host.

### Database example from official architecture

A DB MCP **should** typically expose ([Architecture overview](https://modelcontextprotocol.io/docs/learn/architecture)):

- **Tool** — constrained query  
- **Resource** — schema  
- **Prompt** — few-shot “how to ask this database”

That triad is the senior default, not tools-only.

---

## Alternatives & Tradeoffs

| Design | Pros | Cons |
|--------|------|------|
| **DB table as resource** | Safer read; host picker; cache/subscribe | Hosts that only wire tools never see it |
| **`run_sql` tool** | Model-flexible | Injection, blast radius, selection noise |
| **Workflow as prompt** | Portable across hosts; user-initiated | Weak control vs a graph + HITL (Week 13) |
| **Workflow as agent graph** | Strong HITL/state | Not an MCP primitive; host-specific |
| **Stuff files into tool results** | Works in tools-only hosts (API connector) | Ephemeral; no subscribe; pollutes observations |
| **Resources + `resource_link` from tools** | Search then attach | Two-step; host must implement resources |
| **Tools-only server** | Matches Anthropic API MCP connector today | Loses application-driven context and slash workflows |

Tradeoff: overusing tools for pure reads pollutes the list and raises accidental writes. Underusing prompts makes every user reinvent the play.

API limitation: Messages **MCP connector supports tools only** ([MCP connector](https://platform.claude.com/docs/en/agents-and-tools/mcp-connector)). If the same server must serve Desktop **and** the API, you may need tools that **mirror** critical resources for the API path — document that as a **host gap**, not as “resources are useless.”

---

## Necessity

Collapsing everything into tools throws away MCP’s split between **model-initiated actions** and **application-controlled context**. Hosts that only implement `tools/call` (API connector, some IDE stubs) leave **half the protocol** on the table for FDE demos and enterprise UX (schema pickers, live `resources/updated`, slash playbooks).

Wrong error channel: JSON-RPC on a bad date format means the model never self-repairs; `isError` on “unknown tool” hides a client bug.

Path traversal on `resources/read` is a classic local-server fail.

---

## Industry Practice

- **Common:** tools-only; no pagination; 200-character descriptions; `isError` never set; resources listed but never read by the host; prompts registered and unused.  
- **Senior:** resources for schemas/docs/config; tools for mutations **and** searches that need arguments; prompts for opinionated multi-step jobs; annotations for audience/priority; cursors on large lists; `-32002` for missing resources; `isError` for recoverable tool failures; validate URIs; don’t trust tool annotations from random consumed servers; contract-test `tools/list` + `resources/list` + `prompts/list`; Inspector round-trip. Claude Code: confirm host actually refreshes on `list_changed` (v2 streams).

---

## Concrete Scenario

Resources spec examples: list/read `file:///project/src/main.rs`, URI templates, subscribe/update ([Resources](https://modelcontextprotocol.io/specification/2025-11-25/server/resources), [concepts](https://modelcontextprotocol.io/docs/concepts/resources)).

**FDE `docs_search` server (syllabus):**

| Primitive | Name | Why |
|-----------|------|-----|
| Resource | `docs://corpus/catalog` | Host can pin “what’s indexed” without a tool call |
| Tool | `docs_search` | Model-controlled retrieval with `query`/`k` |
| Prompt | `handbook_lookup` | User picks `/handbook_lookup` → messages already say “quote + cite, no invented policy” |

Workshop pattern table: Deep Research tools + `research_workflow`; LinkedIn tools + `linkedin_post_workflow` ([repo](https://github.com/samtalasila/ai-engineer-europe)).

Sampling scenario: a research server asks the **host LLM** to summarize a resource via `sampling/createMessage` so the server has no vendor SDK ([Sampling](https://modelcontextprotocol.io/specification/2025-11-25/client/sampling)). Only if the client advertised `sampling` and the user can deny.

---

## Open Questions

- When should a host **auto-attach** resources vs wait for a tool fetch?  
- Are MCP **prompts** competing with IDE **skills** / agent-spec packs?  
- Will API connectors ever grow resources/prompts, or is tools-only permanent?  
- `https://` resources that the client must fetch itself — how do air-gapped enterprises use them?

---

## Sources

- https://modelcontextprotocol.io/specification/2025-11-25/server  
- https://modelcontextprotocol.io/specification/2025-11-25/server/tools  
- https://modelcontextprotocol.io/specification/2025-11-25/server/resources  
- https://modelcontextprotocol.io/specification/2025-11-25/server/prompts  
- https://modelcontextprotocol.io/specification/2025-11-25/client/sampling  
- https://modelcontextprotocol.io/docs/learn/architecture  
- https://modelcontextprotocol.io/docs/concepts/resources  
- https://modelcontextprotocol.io/docs/concepts/tools  
- https://platform.claude.com/docs/en/agents-and-tools/mcp-connector  
- https://github.com/samtalasila/ai-engineer-europe  
