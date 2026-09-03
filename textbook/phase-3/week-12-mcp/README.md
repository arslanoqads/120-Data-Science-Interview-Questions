# Week 12 Textbook Chapter — Model Context Protocol (MCP)

> **Status:** COMPLETE  
> **Source:** `research/phase-3/week-12-mcp/`  
> **Chapter:** [chapter.md](chapter.md)

## Concepts covered

- [x] MCP server / client architecture
- [x] Expose vs consume MCP servers
- [x] Resource vs tool vs prompt primitives
- [x] Why MCP matters for FDE (standardized integration surface)

## Structure check

Each concept includes Fundamentals, The Alternatives, Failure Modes, Average vs. Strong Engineer, Worked Example, and Apply It.

## Syllabus build

Ship a **single MCP server wrapping one capability**, then **prove it attaches to two hosts**: wrap one Week 11 tool (recommended `docs_search`) as an MCP server with advertised `tools` (optional resource + prompt); use **stdio** for local attach; connect **Claude Desktop** via `claude_desktop_config.json` and **Claude Code** via `claude mcp add` / project `.mcp.json`; demonstrate list → call → observation; document trust boundary (reachable dirs/APIs, secrets in `env`, confirmation for writes). Interview artifact = **one server + two host configs + a successful tool call**.
