# 02 — Exposing tools as an MCP server vs consuming third-party MCP servers

> Week 12 — Model Context Protocol  
> Research notes (raw).

---

## Fundamentals

Two FDE postures. They use the **same protocol** and **opposite ownership**. Mixing them in one engagement without naming which is which is how “we use MCP” becomes un-debuggable.

### A. You are the server author (**expose**)

Wrap **your** product APIs, warehouses, or workflows so **any MCP host** can use them. You implement lifecycle + primitives (at least `tools/list` + `tools/call`). You choose transport:

- **stdio** — customer laptops, Desktop, Code, Cursor local attach.  
- **Streamable HTTP** — shared service, many clients, OAuth.

You own: schemas, versioning, auth to **downstream** systems, rate limits, `isError` vs JSON-RPC errors, SLA, blast radius.

Anthropic’s pitch: MCP **reduces development time** when building or integrating with AI apps ([What is MCP?](https://docs.anthropic.com/en/docs/agents-and-tools/mcp)). That is true **only if** hosts already speak MCP; you still write the domain semantics.

Claude Code can **scaffold** a server (`mcp-server-dev` plugin / `/mcp-server-dev:build-mcp-server`) — still **your** security review ([Claude Code MCP](https://docs.anthropic.com/en/docs/claude-code/mcp)).

### B. You are the host integrator (**consume**)

Point Claude Code / Desktop / Cursor / Agents SDK / Anthropic API at **someone else’s** server (GitHub, Slack, Notion, internal platform team).

Discovery paths that are real in 2026 docs:

- Desktop `claude_desktop_config.json`  
- Code: `claude mcp add`, project `.mcp.json`, user/local scopes, plugins, **Anthropic Directory** remote connectors (`claude mcp add` on a Directory URL)  
- `claude mcp add-from-claude-desktop`  
- Anthropic Messages **MCP connector**: `mcp_servers` + `mcp_toolset` (remote HTTPS only) ([MCP connector](https://platform.claude.com/docs/en/agents-and-tools/mcp-connector))  
- OpenAI Agents SDK documents MCP as a **tool source** alongside function tools (tool search + `defer_loading`) ([OpenAI Agents SDK tools](https://openai.github.io/openai-agents-python/tools/))

After the host bridges MCP → model tools, your Week 11 loop sees **ordinary callable functions**. You do **not** automatically get the vendor’s SLAs or a safe allowlist.

Claude Code: **verify you trust each server**; servers that fetch external content are a **prompt-injection** channel ([Claude Code MCP](https://docs.anthropic.com/en/docs/claude-code/mcp)).

### Complementary protocol: A2A (not a substitute)

Linux Foundation **A2A** (Google-originated): **agent-to-agent**. Official framing ([A2A Protocol](https://a2a-protocol.org/latest/)):

- **MCP** = equip **one** agent with tools/data.  
- **A2A** = opaque agents **discover, delegate, share results** across frameworks **without** sharing internal memory/tools.

A2A explicitly is **not** a tool-call protocol and **not** a replacement for MCP. If the customer wants “our LangGraph agent talks to their Crew agent,” that is A2A (Week 14 adjacent). If they want “Claude Code can `docs_search`,” that is MCP.

### Thin MCP over REST vs curated surface

A mechanical wrapper that 1:1 maps every REST endpoint to a tool **will** explode the palette (Week 11 selection). Consume-side, attaching **five** vendor servers can dump **hundreds** of tools into one Code session. Code’s **tool search** is the host mitigation; your job is still **allowlists** (`mcp_toolset` allow/deny on the API connector; Code `/mcp` disable; don’t commit random Directory servers).

---

## Alternatives & Tradeoffs

| Choice | When | Risk |
|--------|------|------|
| **Build MCP for your SaaS** | Customers live in many AI hosts | You own server security, versioning, SLA |
| **Consume vendor MCP** | Fast enablement (Notion, GitHub, Stripe URLs in Code docs) | Supply chain; injection; schema drift |
| **Thin MCP over existing REST** | Reuse API surface quickly | Leaky tools; oversized lists; auth passthrough |
| **Skip MCP; proprietary plugin** | One strategic host | Lock-in; rewrite at the next RFP |
| **One fat server** | Simple deploy | Blast radius; mixed trust (files + prod writes) |
| **Many small servers** | Trust boundaries | Config sprawl; host connection limits |
| **API MCP connector only** | No desktop fleet | Tools-only; public HTTPS; beta headers |
| **A2A instead of MCP** | Multi-vendor **agents** | Does not attach Claude Desktop to your DB |

Tradeoff: **exposing everything as tools** creates selection problems; **resources + prompts** are often the safer read-heavy API (file 03). **Consuming** everything from a marketplace is an un-reviewed plugin folder.

| Engagement deliverable | Expose | Consume |
|------------------------|--------|---------|
| Customer keeps it after you leave | **Your** server repo + config | Their vendor contracts + your allowlist doc |
| Who patches CVEs | You / customer platform | Vendor |
| Auth | Your OAuth/resource server | Vendor OAuth in `/mcp` |

---

## Necessity

FDEs embedding into customer environments need a **stable integration surface**. Rebuilding “Jira tool” per IDE wastes the engagement.

Consuming **unvetted** MCP servers without allowlists is a **security incident waiting to happen**: `tools/call` is arbitrary side effects with the user’s (or a service account’s) credentials. Claude Code’s own docs put prompt injection next to “fetch external content.”

Exposing a server **without** a versioning story means the first `inputSchema` change breaks every pinned host.

If you only consume: you have **no** artifact when vendors deprecate SSE. If you only expose and never attach Desktop/Code: you have a process nobody runs.

---

## Industry Practice

- **Common:** one demo stdio server in the repo; `.env` committed; `npx -y` whatever GitHub README; no review for added `.mcp.json` servers; production agent still uses hardcoded tools; “MCP” on the slide.  
- **Senior:** name the posture in the SOW (**ship a server** vs **compose existing servers** vs **both**). Allowlist per environment. Least-privilege credentials (read vs write tools split). Version server releases; contract tests for `tools/list`. Separate servers by trust domain. For consume: Directory/official vendor URLs, OAuth via host UI, disable unused servers in `/mcp`. For expose: official SDK, Inspector, both hosts in CI as far as feasible. Document SSE vs Streamable HTTP. API path: `mcp_toolset` **allowlist**, not “enable all.” Code: project `.mcp.json` uses `${API_KEY}` expansion, not literals ([Claude Code MCP](https://docs.anthropic.com/en/docs/claude-code/mcp)).

Workshop pattern (consume **and** expose in one talk): two **authored** FastMCP servers + attach to Code/Cursor ([AI Engineer Europe](https://www.youtube.com/watch?v=mYSRn6PC1mc), [repo](https://github.com/samtalasila/ai-engineer-europe)). That is **expose twice**, then **consume locally** — still not “install the internet.”

---

## Concrete Scenario

**Engagement split.**

1. **Expose:** wrap the customer’s `structured_query` allowlisted warehouse as `acme-metrics` MCP (stdio for the pilot, HTTP later).  
2. **Consume:** attach official GitHub MCP (remote HTTP) so Code can open PRs.  
3. **Do not** wrap GitHub yourself unless the official server is blocked.  
4. **Do not** put prod DB credentials in the GitHub server’s env.  
5. Anthropic API bot for Slack: use **MCP connector** to the **HTTP** `acme-metrics` URL with `authorization_token` you minted; allowlist `structured_query` only ([MCP connector](https://platform.claude.com/docs/en/agents-and-tools/mcp-connector)).

A2A vs MCP: if later “metrics agent” must delegate to a vendor “compliance agent” without sharing tools, add A2A — do not pretend MCP servers should call each other ([A2A](https://a2a-protocol.org/latest/)).

Code examples of consume-by-URL from Anthropic’s own page: Notion `https://mcp.notion.com/mcp`, Asana SSE, Stripe `https://mcp.stripe.com` ([Claude Code MCP](https://docs.anthropic.com/en/docs/claude-code/mcp)).

---

## Open Questions

- Who **certifies** enterprise MCP servers (vendor? host store? customer security)?  
- One fat server vs many small servers for blast radius — any host-imposed connection caps?  
- Should product companies publish **stdio + HTTP** or HTTP-only now that API connectors cannot see stdio?  
- Dynamic Client Registration (optional in MCP OAuth) — too dangerous for enterprise IdPs?

---

## Sources

- https://docs.anthropic.com/en/docs/agents-and-tools/mcp  
- https://docs.anthropic.com/en/docs/claude-code/mcp  
- https://platform.claude.com/docs/en/agents-and-tools/mcp-connector  
- https://modelcontextprotocol.io/docs/learn/architecture  
- https://modelcontextprotocol.io/docs/getting-started/intro  
- https://a2a-protocol.org/latest/  
- https://openai.github.io/openai-agents-python/tools/  
- https://www.youtube.com/watch?v=mYSRn6PC1mc  
- https://github.com/samtalasila/ai-engineer-europe  
- https://youtu.be/kQmXtrmQ5Zg  
