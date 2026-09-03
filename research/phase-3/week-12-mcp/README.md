# Week 12 Research Corpus — Model Context Protocol (MCP)

> Phase 3 — Agentic Systems  
> **Status:** COMPLETE (deep pass)  
> Raw research corpus (not textbook). Legal sources only; no pirated books.

This directory is the Week 12 research repository. Read concept files in order, then the source map. **Do not start Week 13 (orchestration / multi-agent) from this corpus** — MCP is a *distribution and discovery* layer for tools/context, not graphs, HITL persistence, or multi-agent handoffs.

| # | File | Concept |
|---|------|---------|
| 00 | [00-week-overview.md](00-week-overview.md) | Wrap **one** capability as an MCP server; attach Claude Desktop + Claude Code |
| 01 | [01-mcp-server-client-architecture.md](01-mcp-server-client-architecture.md) | Host / client / server; JSON-RPC data layer; stdio vs Streamable HTTP; lifecycle |
| 02 | [02-expose-vs-consume-mcp.md](02-expose-vs-consume-mcp.md) | Author a server vs compose third-party servers; A2A complementarity |
| 03 | [03-mcp-primitives.md](03-mcp-primitives.md) | Resource vs tool vs prompt (control: application / model / user) |
| 04 | [04-mcp-for-fde-integration.md](04-mcp-for-fde-integration.md) | Why MCP is the FDE integration surface; handoff artifact vs lock-in |
| — | [99-source-map.md](99-source-map.md) | Master URL / spec / YouTube index |

## Completeness checklist (Week 12)

- [x] All syllabus Week 12 concepts covered with **7 required fields**  
- [x] **MCP server / client architecture** (host creates one client per server; capability negotiation; transports)  
- [x] **Expose vs consume** (you ship a server vs you attach vendor/internal servers)  
- [x] **Resource vs tool vs prompt** primitives (URI context vs `tools/call` vs user-selected templates)  
- [x] **Why MCP matters for FDE** (build once, attach many hosts; security boundary; composable engagement)  
- [x] Overview includes **wrap a capability as MCP** + **connect Claude Desktop and Claude Code** (config paths, `.mcp.json`, stdio vs HTTP)  
- [x] [modelcontextprotocol.io](https://modelcontextprotocol.io/) learn + spec (`2025-11-25`) cited  
- [x] Anthropic MCP overview + Claude Code MCP + Messages API MCP connector cited  
- [x] YouTube / **AI Engineer** MCP talks cited (Mahesh Murag workshop; AI Engineer Europe FastMCP workshop)  
- [x] Per-week research **directory** (not a single thin file)  
- [x] `_PRIOR_SINGLE_FILE.md` removed after expansion  

## Syllabus build task (Week 12)

Ship a **single MCP server wrapping one capability**, then **prove it attaches to two hosts**:

1. Take **one** Week 11 capability (recommended: `docs_search` **or** `structured_query` **or** calendar list — not all three dumped as 40 tools). Implement it as an MCP **server** with advertised `tools` (and optionally a **resource** for schema/docs and a **prompt** for the playbook).  
2. Transport: **stdio** for local Desktop/Code attach. Optionally a second Streamable HTTP listener for remote hosts — do not skip stdio.  
3. Connect **Claude Desktop** via `claude_desktop_config.json` (`mcpServers` + `command`/`args`, absolute paths).  
4. Connect **Claude Code** via `claude mcp add` and/or project `.mcp.json` (`type`: `stdio` vs `http`; `--` separator for stdio; workspace trust / project approval).  
5. Demonstrate: host lists the tool → model calls it → observation returns. Capture a screenshot or `/mcp` status (`✔ Connected`) plus a successful tool trace.  
6. Document the **trust boundary**: which directories/APIs the process can reach; secrets in `env` not committed; user confirmation for writes.

Do **not** skip this week for “we’ll just `bind_tools` in LangGraph.” You cannot debug host catalogs, capability mismatch, or customer handoff if the **connector** is implicit.

## Default path (synthesis)

1. Prefer **official MCP SDKs** (or FastMCP on top of them) over hand-rolled JSON-RPC. Pin a **protocol version** (`2025-11-25` is the spec revision used throughout this corpus; hosts may also negotiate later revisions such as `2026-07-28`).  
2. Prefer **stdio** for laptop/IDE attach; **Streamable HTTP + OAuth 2.1** for shared remote servers. Treat HTTP+SSE (`2024-11-05`) as deprecated compatibility.  
3. Advertise **only** capabilities you implement. If you do not declare `tools`, clients must not call `tools/call`.  
4. Split **read vs write** tools. Resources for schemas and docs; prompts for opinionated workflows; tools for actions.  
5. Allowlist third-party servers. Treat every `tools/call` as a **side effect channel** (Week 11 loop + Week 14 safety).  
6. Interview artifact = **one server + two host configs + a successful tool call**, not a slide that says “we use MCP.”
