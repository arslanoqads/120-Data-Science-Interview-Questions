# 01 — Context vs prompt engineering (the actual distinction)

> Week 25 — Context Engineering as a discipline  
> Research notes (raw).

---

## Fundamentals

**Prompt engineering** is the craft of writing and organizing *instructions* so a model behaves as intended: system prompts, few-shot exemplars, output schemas, personas, refusal policies. Week 5 already covers versioning, templates, and injection surface. The unit of work is usually a **prompt artifact** — text you author and pin.

**Context engineering** is the craft of deciding **what information the model sees and when**, across the *entire* token set used at inference time. Anthropic (*Effective context engineering for AI agents*, 2025-09-29):

> Prompt engineering refers to methods for writing and organizing LLM instructions for optimal outcomes… Context engineering refers to the set of strategies for curating and maintaining the optimal set of tokens (information) during LLM inference, **including all the other information that may land there outside of the prompts**.

That “other information” is the point: tool schemas, MCP descriptors, retrieved passages, prior messages, tool results, memory mounts, images, and structured state. An agent loop **generates** new candidates for context every turn; curation must be **iterative**, not a one-shot prompt write.

Andrej Karpathy (quoted by LangChain): context engineering is the “delicate art and science of filling the context window with just the right information for the next step.” LangChain treats the LLM as CPU and the context window as RAM — an OS-like scheduler decides what resides in working memory.

Chip Huyen’s public writing uses **context construction** as the umbrella: give the model the information it needs, or tools to fetch it (*Building a Generative AI Platform*; *Agents*). Prompt text is one input; retrieval, tool I/O, and memory are peers.

| Dimension | Prompt engineering | Context engineering |
|-----------|--------------------|---------------------|
| Primary question | How do we *word* instructions? | What *tokens* occupy the window *now*? |
| Cadence | Version when behavior changes | Re-decide every inference turn |
| Artifacts | Prompt files, templates | Packers, retrievers, compactors, isolators, memory writers |
| Failure owner | Prompt author | Retrieval / memory / orchestration / packing |
| Classic week | Week 5 | Week 25 (this elective) |

Anthropic’s design target: the **smallest set of high-signal tokens** that maximize desired outcomes — informative yet tight. System prompts still matter (altitude: not brittle if-else, not vague), but they are one *layer* inside a larger assembly problem.

---

## Alternatives & Tradeoffs

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

Tradeoff inside prompts themselves: stuffing every edge case into the system prompt fights context budget and creates **clash** with later tool results. Anthropic recommends diverse **canonical** examples, not laundry lists.

---

## Necessity

If you only ship prompt engineering:

- A perfect system prompt still fails when **mid-context gold** is ignored (Liu et al., Lost in the Middle).  
- Tool result spam drowns instructions; the model follows a stale JSON blob instead of the policy section.  
- Teams A/B prompt wording while the real delta is **k**, reorder, or compaction aggressiveness.  
- Security reviews miss **indirect injection** sitting in retrieved email or web pages — not in *your* prompt file (Willison; OWASP).  
- Cost dashboards show “prompt tokens” rising when the driver is **unchecked history**, not a longer system string.

Skipping the distinction produces wrong owners in Week 15/16 error analysis: every failure labeled “prompt.”

---

## Industry Practice

- **Common:** one mega system prompt; append chat; hope the model “remembers.” Prompt edits are the only lever.  
- **Strong:** separate **instruction registry** (versioned prompts) from **context assembler** (deterministic merge of static + dynamic sections). Trace each section’s token count. Evaluate prompt changes *and* packing changes independently.  
- **FDE / senior:** can explain Anthropic’s progression narrative in an interview; point at Claude Code (CLAUDE.md always in, files JIT via glob/grep); point at LangGraph state fields that are *not* in `messages` until selected; refuse conflating “we added RAG” with “we engineered context end-to-end.”

Industry vocabulary converging: Anthropic engineering blog; LangChain write/select/compress/isolate; Cognition and others calling context engineering the #1 agent-builder job (as cited by LangChain). Chip Huyen AI Engineer keynote: agents amplify **context** pressure via tool docs + tool outputs + multi-step residue.

---

## Concrete Scenario

**Anthropic Engineering — Effective context engineering for AI agents**  
https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents  

Published 2025-09-29 by Anthropic Applied AI (Prithvi Rajasekaran, Ethan Dixon, Carly Ryan, Jeremy Hadfield et al.). The post explicitly contrasts prompt vs context engineering, introduces **context rot** and the finite **attention budget**, and walks component anatomy (system prompts, tools, examples, history). It is the flagship public definition this week anchors on.

Supporting talk: Chip Huyen, *Why people think “agent” is a buzzword but it isn’t*, AI Engineer — https://ai.engineer/talks/keynote-why-people-think-agent-is-a-buzzword-but-it-isn-t — frames context (tool docs, outputs, reasoning residue) as a first-class agent bottleneck alongside planning and tool use.

---

## Open Questions

- As models get smarter, does Anthropic’s claim hold that they need *less* prescriptive prompting but *still* careful context curation?  
- Is “context engineering” a durable job title or a temporary rebrand of IR + orchestration + prompt ops?  
- Should prompt and context changes share one eval suite or stay separated for attribution?  
- How should teams version **assemblers** (code) vs **prompts** (text) in Git — monorepo contracts?  
- Where does structured output / constrained decoding sit — prompt technique or context contract?

---

## Sources

- https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents  
- https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview (Anthropic prompt engineering docs entry)  
- https://www.langchain.com/blog/context-engineering-for-agents  
- https://huyenchip.com/2024/07/25/genai-platform.html  
- https://huyenchip.com/2025/01/07/agents.html  
- https://huyenchip.com/2023/08/16/llm-research-open-challenges.html  
- https://ai.engineer/talks/keynote-why-people-think-agent-is-a-buzzword-but-it-isn-t  
- https://arxiv.org/abs/2307.03172  
- https://simonwillison.net/2023/Apr/25/dual-llm-pattern/  
- https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html  
