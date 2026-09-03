# 04 — Why MCP matters for FDE work (standardized integration surface)

> Week 12 — Model Context Protocol  
> Research notes (raw).

---

## Fundamentals

**Forward Deployed / AI Engineer** work is usually: land in a messy customer environment, connect models to **their** systems, leave something **operable**. MCP matters because it turns “integration” into a **repeatable product surface**, not a one-off `bind_tools` in last week’s notebook.

Five reasons, grounded in official docs rather than vendor keynotes:

1. **Build once, attach many hosts.** Same server in Claude Code, Claude Desktop, VS Code, Cursor, ChatGPT, custom hosts ([What is MCP?](https://modelcontextprotocol.io/docs/getting-started/intro), [Anthropic MCP](https://docs.anthropic.com/en/docs/agents-and-tools/mcp)). Ecosystem list is explicit: assistants **and** IDEs.

2. **Clear security boundary per server.** Isolated process/service; negotiated capabilities; host-enforced consent. Spec principle: servers do not see the full conversation or sibling servers ([Architecture](https://modelcontextprotocol.io/specification/2025-11-25/architecture/index)). Blast radius = **that** server’s credentials and tools — if you did not build a god-server.

3. **Composable engagements.** Stack **vendor** MCP (consume) + **one custom** server for the proprietary API (expose) instead of a monolith agent (file 02).

4. **Handoff artifact.** The customer keeps **server + host config** (Desktop JSON, Code `.mcp.json`, runbooks for `/mcp` and logs). That outlives the FDE laptop and a “Claude Project” full of stale instructions.

5. **Ecosystem leverage.** Inspector, official SDKs, Directory connectors, conference workshops ([Murag](https://youtu.be/kQmXtrmQ5Zg), [AI Engineer Europe](https://www.youtube.com/watch?v=mYSRn6PC1mc)). Official AI Engineer org treats MCP as a first-class conference surface ([ai.engineer llms.md](https://www.ai.engineer/llms.md)).

MCP does **not** replace: Week 11 loop, Week 13 graphs/HITL, Week 14 side-effect policy, Week 15 evals, or **auth design**. Authorization for remote MCP is OAuth 2.1 + protected resource metadata — you still implement it ([Authorization](https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization), [Understanding Authorization](https://modelcontextprotocol.io/docs/tutorials/security/authorization)).

Pair with **A2A** when multiple **opaque agents** must collaborate across vendors ([A2A](https://a2a-protocol.org/latest/)).

Anthropic product stories you can cite without inventing case studies: Calendar/Notion agents, Claude Code + Figma, enterprise multi-DB chat, Blender → 3D print ([MCP overview](https://docs.anthropic.com/en/docs/agents-and-tools/mcp)). Those are **host capabilities enabled by connectors**, not proof your customer’s SAP instance is easy.

### What “standardized surface” actually standardizes

| Standardized | Still your problem |
|--------------|--------------------|
| JSON-RPC methods, lifecycle, primitive shapes | Domain tool semantics |
| How Desktop/Code **spawn or HTTP-connect** | Which tools exist; descriptions (Week 11) |
| Capability flags | Honest advertising |
| OAuth discovery (remote) | IdP, scopes, token vault |
| Isolation **idea** | OS sandbox, secret injection, allowlists |

If you MCP-wash a nightly ETL, you added a chat UI to a batch job. Don’t.

### FDE delivery shapes

| Artifact | Portability | Maintenance |
|----------|-------------|-------------|
| **MCP server(s) + host config** | High across MCP hosts | Spec/SDK/host quirks |
| LangGraph app with bespoke tools | High **inside that repo** | Weak Desktop UX |
| Claude project instructions only | Low | Drifts immediately |
| Customer-only IDE plugin | Low | Rewrite cost |
| Anthropic API `mcp_toolset` only | High for **API** bots | Tools-only; no stdio |
| Notebook `while True` + functions | Demo | Dies at handoff |

---

## Alternatives & Tradeoffs

| Strategy | Wins | Loses |
|----------|------|-------|
| **MCP as the integration SKU** | Host swap; customer-operable | You track protocol revisions (`2025-11-25` vs host `2026-07-28`) |
| **Deep one-host plugin** | Best UX on that host | Next RFP uses a different IDE |
| **Only consume marketplace servers** | Speed | No proprietary API; supply chain |
| **Only expose, never consume** | Control | Reimplement GitHub/Slack badly |
| **Standardize later “when we know the host”** | Feels agile | Engagement ends with nothing reusable |

Tradeoff: shaping APIs as **chat tools** can be dishonest when the real interface is a pipeline. MCP is for **interactive agent context**, not a replacement for job schedulers.

Harrison Chase (Week 11 talk): reliability lives in **control flow**. MCP does not give you that. It gives you **where tools come from**. `P(success)` still depends on the loop, palettes, and HITL.

---

## Necessity

Without a standardized surface, each engagement **reinvents connectors** and dies when the preferred chat UI changes. The expensive part (domain semantics, auth, guardrails) should concentrate in the **server**; the host is swappable.

Without MCP-as-handoff, the customer inherits a Python script that imports your unpublished package. Without allowlists, “we connected MCP” is an **unreviewed RCE-shaped plugin** (stdio = your user account; HTTP = whatever token you pasted).

Without treating servers as **versioned products**, the first schema change breaks Desktop while Code still works (or the reverse).

---

## Industry Practice

- **Common:** slideware “we use MCP”; actually hardcoded tools in one LangGraph; or 12 unreviewed `npx -y` servers; credentials in git; no `tools/list` tests; no Desktop log path in the runbook.  
- **Senior:** MCP servers as **versioned products** (semver, changelog of tool schemas). CI contract tests. Secrets via customer vault / Code `${VAR}` / Desktop `env`. Document **both** host setups (file 00). Measure tool success rates (Week 15 traces). Combine with loop guardrails (Week 11) and do **not** pretend Week 13 is done. Separate read/write; confirm writes in the host. For remote: OAuth 2.1, resource indicators, no token passthrough (auth tutorial: validate audience; least-privilege scopes; official libraries). Anthropic API bots: allowlisted `mcp_toolset`. Code: workspace trust story for committed `.mcp.json`. Registry/Directory as they mature — still **allowlist**.

Managed Agents / vaults (Anthropic): credentials matched by MCP URL, agent never sees the token ([Managed agents MCP connector](https://platform.claude.com/docs/en/managed-agents/mcp-connector)) — pattern to copy even if you are not on that product: **session-time credential injection**, not tokens in tool descriptions.

---

## Concrete Scenario

**90-day FDE, customer using Claude Code today and “maybe Desktop for execs.”**

1. Week 11 loop proven with three **in-process** tools.  
2. Week 12: lift `docs_search` to MCP; attach Code **and** Desktop; exec demo uses Desktop filesystem-style approval UX.  
3. Consume official GitHub MCP for PRs; do not wrap GitHub.  
4. Handoff: repo `servers/docs-search`, `.mcp.json` with `${DOCS_API_KEY}`, Desktop snippet in README, `/mcp` approval instructions, `mcp.log` paths, protocol version pin, **which tools are writes**.  
5. Explicit non-goals: multi-agent graph (Week 13), A2A (later), wrapping SAP in one weekend.

Murag workshop: philosophy → build → agents → roadmap ([YouTube](https://youtu.be/kQmXtrmQ5Zg)). Use it for **framing**; implement against **spec URLs** in this corpus.

Europe workshop: two servers, one harness file ([YouTube](https://www.youtube.com/watch?v=mYSRn6PC1mc)) — that is the **compose** endgame after one capability works.

---

## Open Questions

- Will enterprise procurement treat MCP servers like **browser extensions** (scary) or like **APIs** (manageable)?  
- How do FDEs version **breaking** `inputSchema` changes for customers pinned to an older host/protocol?  
- Who is on the hook when a Directory server is compromised — host store, vendor, or the FDE who added `.mcp.json`?  
- Does tools-only API MCP push the industry to starve resources/prompts in “enterprise” servers?

---

## Sources

- https://docs.anthropic.com/en/docs/agents-and-tools/mcp  
- https://docs.anthropic.com/en/docs/claude-code/mcp  
- https://platform.claude.com/docs/en/agents-and-tools/mcp-connector  
- https://platform.claude.com/docs/en/managed-agents/mcp-connector  
- https://modelcontextprotocol.io/docs/getting-started/intro  
- https://modelcontextprotocol.io/docs/learn/architecture  
- https://modelcontextprotocol.io/specification/2025-11-25/architecture/index  
- https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization  
- https://modelcontextprotocol.io/docs/tutorials/security/authorization  
- https://a2a-protocol.org/latest/  
- https://youtu.be/kQmXtrmQ5Zg  
- https://www.youtube.com/watch?v=mYSRn6PC1mc  
- https://www.ai.engineer/llms.md  
