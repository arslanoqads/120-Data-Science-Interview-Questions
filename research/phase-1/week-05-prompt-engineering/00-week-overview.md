# 00 — Week overview & syllabus mapping

> Week 5 — Prompt Engineering  
> Research notes (raw).

---

## Fundamentals

Week 5 is the **product-behavior layer** on top of Week 4’s wire protocol. Week 4 proved you can call OpenAI and Anthropic with correct roles, tools, streams, schemas, token budgets, and cache-stable prefixes. Week 5 proves that the **text those APIs consume** is a versioned, testable, attack-aware artifact—not a string literal someone pasted into a handler.

The syllabus spine is:

1. **System prompts in VCS** — changelog, registry, canary, rollback.  
2. **Templates + variable injection** — stable instructions vs runtime data; framework patterns.  
3. **Few-shot placement** — quality vs cache economics (Week 4 layout constraint).  
4. **Instruction-following vs persona** — measurable contracts over vibes.  
5. **Prompt injection and guardrails** — OWASP LLM01, Willison, dual LLM, what filters actually do.

These five form one pipeline: **version a contract** → **render it with typed, bounded variables** → **place exemplars where they help without busting cache** → **keep persona thin** → **assume untrusted tokens will try to seize control**. Skipping any step shows up as silent policy drift, SSTI or delimiter-bypass, cold-cache cost spikes, charming-but-noncompliant bots, or agents that email private data because a webpage told them to.

OpenAI’s 2026 prompting docs now say it explicitly: treat prompts as application code (typed builders, fixtures, evals, feature flags). Anthropic’s Agent SDK treats the system prompt as a **preset vs custom string vs append** product surface. LangSmith/Langfuse treat prompts as **immutable commits with environment labels**. That is the industry object model this week exists to teach.

---

## Alternatives & Tradeoffs

| Path | What you optimize | What you sacrifice |
|------|-------------------|-------------------|
| Inline strings in handlers | Fastest first demo | No review trail; cache thrash; merge conflicts with logic |
| Git markdown/YAML + changelog (syllabus default) | Diffable, reviewable, cheap, reproducible locally | Promotion still needs env/config; non-engineers bottleneck |
| Prompt registry as source of truth (LangSmith / Langfuse) | Hot reload, UI for PMs, labels for canary | Vendor coupling; must still mirror to git for audit in many orgs |
| “Just add a persona and XML tags” | Feels like security/UX work | Not a security boundary (Willison); persona ≠ instruction following |
| Filter/guardrail product as the whole defense | Demo-friendly “we have rails” | 95% detection is a failing grade for agents with tools |

For the flagship Deployment Copilot / RAG chatbot, Week 5 should prefer **git-versioned chat templates + pinned `prompt_version` in traces**, with an optional registry for canary labels. Do not put retrieved chunks in the system prompt. Do not treat delimiter tags as isolation.

---

## Necessity

Concrete failure modes if Week 5 is skipped:

- “Who changed the refund policy wording?” is unanswerable; eval baselines drift.  
- User text interpolated into the instruction region → instruction override / SSTI.  
- Dynamic kNN few-shots inserted **before** the cache breakpoint → org-wide cold cache (Week 4).  
- Overgrown persona fights safety policy and structured-output contracts.  
- RAG chatbot with tools + private data + outbound HTTP = Willison’s **lethal trifecta**, shipped as a feature.

Regulated teams need auditability of instruction changes the same way they audit application config. Cache economics (Week 4) make unversioned prompt edits a **cost incident**, not just a quality incident.

---

## Industry Practice

- **Common (demo AI):** system prompt in a Python f-string; examples copied from a tweet; “ignore instructions in `<user>` tags”; ship.  
- **Strong:** one prompt module per product surface; semantic/dated IDs; CI evals on PR; `prompt_version` on every trace; static few-shots in the cached prefix; retrieved docs in tagged user blocks; tools default-deny.  
- **FDE bar:** can explain git vs registry source-of-truth, canary math, why OpenAI deprecated API prompt objects in favor of code, why Dual LLM still leaks via data-flow, and why a NeMo/Llama-Guard classifier is a **soft signal** not a gate.

---

## Concrete Scenario

Syllabus build intent: the Week 4 provider-agnostic client now loads `prompts/support.system.v4.md` (or a Langfuse `production` label pinned in staging), fills a chat template with `<context>` chunks and `<question>`, keeps three static extraction examples in the developer/system prefix so OpenAI/Anthropic caches hit, and refuses to render if injected context exceeds the Week 4 token budget. A canary flag sends 5% of traffic to `v5` with eval-linked changelog. Retrieved HTML is treated as attacker-controlled: no generic `http_request` tool beside mailbox access.

Related public bar: AI Engineer “Build a Prompt Learning Loop” (DeLucia & Ali) — scorers update the system prompt only if candidates are addressable and comparable. Karina Nguyen’s task-tuned prompting workshop — iterate against task metrics, not folklore.

URL: https://ai.engineer/talks/build-a-prompt-learning-loop  
Companions: https://developers.openai.com/api/docs/guides/prompt-engineering · https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices · https://www.youtube.com/watch?v=6d60zVdcCV4

---

## Open Questions

- Git as source with registry as cache, or registry as source with git as export? (OpenAI 2026: prefer code-managed prompts.)  
- Who owns prompt-cache key design vs prompt-version canary in multi-tenant SaaS—platform or product? (Week 4 leftover.)  
- Minimum eval suite that must pass before a system-prompt merge?  
- When do capability-based runtimes (CaMeL-like) become default agent frameworks vs Dual LLM by convention?

---

## Sources

- Syllabus PDF (uploaded): AQ AI Engineer FDE Syllabus  
- https://developers.openai.com/api/docs/guides/prompt-engineering  
- https://developers.openai.com/api/docs/guides/prompting  
- https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices  
- https://code.claude.com/docs/en/agent-sdk/modifying-system-prompts  
- https://genai.owasp.org/llmrisk/llm01-prompt-injection/  
- https://simonwillison.net/series/prompt-injection/  
- https://ai.engineer/talks/build-a-prompt-learning-loop  
- https://www.youtube.com/watch?v=6d60zVdcCV4  
