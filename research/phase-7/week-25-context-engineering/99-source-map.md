# 99 — Week 25 master source map

> Consolidated index of official docs, engineering blogs, papers, talks. Legal sources only.  
> Phase 7 elective — Context Engineering as a discipline.

Fetched / verified via WebSearch & WebFetch during corpus authoring (2026-09-03).

---

## Anthropic — context engineering, agents, memory

| Topic | URL |
|-------|-----|
| **Effective context engineering for AI agents** (2025-09-29) | https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents |
| Building effective AI agents (related) | https://www.anthropic.com/engineering/building-effective-agents |
| Multi-agent research system | https://www.anthropic.com/engineering/multi-agent-research-system |
| When / how to use multi-agent | https://claude.com/blog/building-multi-agent-systems-when-and-how-to-use-them |
| Claude Code session management & 1M context | https://claude.com/blog/using-claude-code-session-management-and-1m-context |
| Managed Agents — Using agent memory | https://platform.claude.com/docs/en/managed-agents/memory |
| Cookbook — remember user preferences | https://platform.claude.com/cookbook/managed-agents-cma-remember-user-preferences |
| Prompt engineering overview (contrast) | https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview |

---

## LangGraph / LangChain — memory & context patterns

| Topic | URL |
|-------|-----|
| Context engineering for agents (write/select/compress/isolate) | https://www.langchain.com/blog/context-engineering-for-agents |
| Memory overview (short vs long-term) | https://docs.langchain.com/oss/python/concepts/memory |
| Persistence (checkpointers vs stores) | https://docs.langchain.com/oss/python/langgraph/persistence |
| Add memory guide | https://docs.langchain.com/oss/python/langgraph/add-memory |
| Checkpointers | https://docs.langchain.com/oss/python/langgraph/checkpointers |

---

## OpenAI — threads / Responses / compaction

| Topic | URL |
|-------|-----|
| Compaction guide (Responses) | https://developers.openai.com/api/docs/guides/compaction |
| Compact API reference | https://developers.openai.com/api/reference/resources/responses/methods/compact |
| Assistants → Responses / Conversations migration | https://developers.openai.com/api/docs/assistants/migration |

---

## Chip Huyen — public blogs / talks

| Topic | URL |
|-------|-----|
| Agents (context construction, tools, memory note) | https://huyenchip.com/2025/01/07/agents.html |
| Building a Generative AI Platform (context construction) | https://huyenchip.com/2024/07/25/genai-platform.html |
| Open challenges in LLM research (cites Lost in the Middle) | https://huyenchip.com/2023/08/16/llm-research-open-challenges.html |
| Building LLM applications for production | https://huyenchip.com/2023/04/11/llm-engineering.html |
| AI Engineer keynote — agents not just a buzzword | https://ai.engineer/talks/keynote-why-people-think-agent-is-a-buzzword-but-it-isn-t |

---

## Papers — long context / position

| Topic | URL |
|-------|-----|
| Liu et al. **Lost in the Middle** arXiv:2307.03172 | https://arxiv.org/abs/2307.03172 |
| PDF | https://arxiv.org/pdf/2307.03172 |
| HTML | https://arxiv.org/html/2307.03172v1 |
| TACL DOI | https://doi.org/10.1162/tacl_a_00638 |
| ACL Anthology | https://aclanthology.org/2024.tacl-1.9/ |

---

## Failure modes — Breunig, injection, OWASP

| Topic | URL |
|-------|-----|
| Drew Breunig — How Long Contexts Fail | https://www.dbreunig.com/2025/06/22/how-contexts-fail-and-how-to-fix-them.html |
| Drew Breunig — How to Fix Your Context | https://www.dbreunig.com/2025/06/26/how-to-fix-your-context.html |
| O’Reilly Radar reprint / working with contexts | https://www.oreilly.com/radar/working-with-contexts/ |
| Simon Willison — Dual LLM pattern | https://simonwillison.net/2023/Apr/25/dual-llm-pattern/ |
| Simon Willison — Design patterns for securing LLM agents | https://simonwillison.net/2025/Jun/13/prompt-injection-design-patterns/ |
| Simon Willison — CaMeL commentary | https://simonwillison.net/2025/Apr/11/camel/ |
| OWASP — LLM Prompt Injection Prevention Cheat Sheet | https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html |

---

## YouTube / conference talks

| Topic | URL |
|-------|-----|
| Lamis Mukta (Anthropic) — Learning while you sleep / dreaming (AI Native DevCon) | https://www.youtube.com/watch?v=tTcxVv8HHNw |
| Drew Breunig — How Long Contexts Fail (and How to Fix Them) | https://www.youtube.com/watch?v=-iRQxHxYqak |
| Chip Huyen AI Engineer keynote page (talk entry) | https://ai.engineer/talks/keynote-why-people-think-agent-is-a-buzzword-but-it-isn-t |

---

## Cross-links inside this KB

| Related week | Why |
|--------------|-----|
| Week 5 — prompt engineering | Instruction crafting; injection intro |
| Weeks 6–9 — RAG | Evidence layer; Lost in the Middle; failure taxonomy sibling |
| Weeks 11–15 — agents | Loops, tools, multi-agent, HITL, evals |
| Week 16–17 — evals / observability | Trace the context assembler |
| Week 20 — cost/latency | Token budgets, caching, compression |

---

## Source policy reminder

Allowed: official docs, reputable engineering blogs, open talks, arXiv, public YouTube.  
Not used: pirate book/PDF sites or unauthorized copyrighted book text.
