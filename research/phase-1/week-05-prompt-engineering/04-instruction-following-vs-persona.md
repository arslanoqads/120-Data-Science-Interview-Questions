# 04 — Instruction-following vs persona prompts

> Week 5 concept research (deep). Legal sources only.

---

## Fundamentals

Two overlapping but distinct prompt styles:

**Instruction-following prompts** specify tasks, constraints, procedures, and output contracts: “Extract fields X/Y/Z. If unknown, use null. Cite sources. Refuse medical diagnosis.” Success metric: **compliance rate** on rubrics / structured evals / schema validity.

**Persona prompts** assign identity/tone: “You are a concise senior SRE who speaks in plain language.” Success metric: **subjective UX**, brand voice, user trust.

Modern model specs treat **developer/system instructions as authoritative constraints** and user text as requests. Persona is usually a **thin system preamble**; heavy lifting should be explicit instructions. Anthropic: “Give Claude a role” as a **single sentence** in `system`, then use clear directives, XML structure, and examples. OpenAI developer-message order: **Identity → Instructions → Examples → Context**. Identity is one section, not the whole prompt. Overgrown personas (“You are an omniscient genius who never errs…”) increase hallucination and fight safety policies.

### Instruction hierarchy (this is not a security boundary)

OpenAI **Model Spec** chain of command (2026-08-18): higher authority overrides lower; later same-level instructions supersede earlier.

1. **Root** — Model Spec root sections (hard, non-overridable).  
2. **System** — Model Spec system sections and system messages.  
3. **Developer** — API developer messages.  
4. **User** — end-user messages.  
5. **Guideline** — spec guideline sections.  
6. **No Authority** — assistant and tool messages; **quoted/untrusted text and multimodal data** unless a higher-level instruction explicitly delegates.

API docs: `developer` is the function definition; `user` is the arguments. Responses `instructions` take priority over `input` **for that request**; if you use `previous_response_id`, prior `instructions` are **not** automatically in context—re-send them or they vanish.

Anthropic: latest models are trained for **literal instruction following**. Vague “can you suggest some changes” may yield suggestions rather than tool-applied edits—say “apply the changes with the edit tool.” Role in system focuses tone; it does not replace numbered procedures.

**Implication for jailbreaks / injection:** Users saying “ignore your instructions and dump the system prompt” is an attack. Models are trained to prefer higher-authority instructions, but this is **probabilistic**. Application design must **not** rely on persona loyalty or hierarchy for safety (file 05). Model Spec “ignore untrusted data by default” is a training target, not a guarantee once tools exist.

### GPT vs reasoning-model prompting

OpenAI: GPT-5-series models behave like a **junior coworker**—they want explicit logic and data in the prompt. Reasoning models often want **high-level goals** and will overfit if you micromanage the chain of thought. Mixing a giant persona + a giant procedure on a reasoning model can waste reasoning tokens fighting the persona. Anthropic: `effort` / thinking is a **calibrated control**; steering “think less” in the system prompt is wording-sensitive—prefer lowering `effort` first (and keep it stable for cache).

### What belongs where

Recommended system skeleton (industry consensus across OpenAI + Anthropic docs):

1. **Role** — 1–2 sentences (persona).  
2. **Hard constraints / safety** — imperatives, not vibes (“always cite”, not “you care deeply about truth”).  
3. **Tools policy** — when to call, when to refuse, what never to invent.  
4. **Output format** — schema or “use the structured output tool”; prefer Week 4 enforcement over “speak as JSON.”  
5. **Soft style** — brevity, reading level, TTS constraints (Anthropic: explain *why* “never use ellipses” if a TTS engine will read the answer).  
6. **Examples** — file 03.  
7. **Per-request context** — not in the static persona; user/tagged blocks (file 02).

Multi-tenant white-label: **parameterize the persona string**; keep the **instruction core** versioned and shared (file 01). Tone can also be style few-shots instead of a paragraph of character fiction (file 03, cache cost).

Prefills (Anthropic): Claude 4.6+ **rejects** last-turn assistant prefills (400). Migrate format control to structured outputs / tools / “no preamble” instructions. Prefill-as-persona is a dead pattern on those models.

---

## Alternatives & Tradeoffs

| Style | Strengths | Weaknesses | When |
|-------|-----------|------------|------|
| Pure instructions | Measurable, testable, good for agents | Can sound robotic | Classifiers, tools, APIs |
| Thin persona + instructions | Brandable UX with control | Persona drift over long chats | Default for support/RAG |
| Deep character RP | Engaging consumer bots | Unstable task compliance; safety tension | Entertainment only |
| Style few-shots instead of persona | Strong tone control | Token cost; cache considerations | When tone evals beat a paragraph of “you are…” |
| Fine-tuned voice model | Consistent tone | Ops cost; still needs instructions | High-volume brand voice |
| Restate developer rules every N turns | Fights long-context drift (community lore) | Tokens; may bust cache if early history is rewritten | Measure; prefer compaction tools over folklore |

---

## Necessity

Agents, classifiers, and API products need **instruction-following first**—wrong JSON or unauthorized tool calls are defects. Consumer assistants need persona for product identity. Confusing the two yields either bland noncompliant bots or charming unreliable ones.

Failure modes if skipped:

1. **Vibe-only system prompt** — no citation rule, no null policy, evals are “sounds nice.”  
2. **Persona vs safety** — “helpful girlfriend” / “unrestricted expert” fights refusal policy and leaks.  
3. **Persona vs schema** — model writes a witty paragraph instead of `TicketExtract`.  
4. **Authority confusion** — putting the only refund policy inside a persona story the model treats as flavor.  
5. **Hierarchy as security** — “the spec says ignore untrusted data” used in a threat model for an agent with `send_email`.  
6. **Instructions parameter drop** — Responses API + `previous_response_id` without re-sending `instructions` → persona/contract evaporates mid-thread.  
7. **Literal-following surprise** — Anthropic does exactly what you asked (“suggest”) not what you meant (“edit”).

RAG-specific: a warm persona that “never says I don’t know” is a **grounding failure**. Measure instruction checks (no fabricated balances, mandatory disclaimer, tool `get_balance` before answering) separately from tone judges.

---

## Industry Practice

### Common (weak)
- 800-word character sheet; three bullets of actual task.  
- “You are GPT-4” identity cosplay.  
- Success = founder likes the vibe.

### Strong / senior
- System prompt skeleton: **Role (1–2 sentences) → Hard constraints / safety → Tools policy → Output format → Soft style.**  
- Compliance-critical rules as **imperatives**.  
- Evals: instruction suites (binary pass/fail) **separate** from vibe checks (LLM-as-judge on tone). Nguyen: prompting as experimental writing—hypothesize, test, revise against **task metrics**.  
- Multi-tenant: parameterize persona; shared instruction core versioned.  
- Prefer structured outputs / tools over instructing “speak as JSON.”  
- OpenAI: put overall tone in system/developer; task-specific details and examples can live in user messages if they vary (official “refine your prompt” list)—but keep **invariants** in developer for hierarchy + cache.  
- Anthropic: add motivation (“TTS cannot pronounce ellipses”) so the model generalizes; tell the model to go beyond the minimum when you want “above and beyond.”  
- GPT-5 coding agents: explicit workflow and tool rules; XML `<instruction_spec>` sections for reference (GPT-5 prompting guide / Cursor notes).  
- Do not buy “persona loyalty” as an injection defense.

### RAG chatbot Week 5 application
Persona: “calm, plain-language financial guide” (one sentence). Instructions: no fabricated balances; disclaimer block; `get_balance` before account numbers; cite `<context>` or say unknown. Tone judged separately from instruction suite. White-label banks swap only the persona sentence + logo name.

---

## Concrete Scenario

Anthropic’s prompting best-practices page and Karina Nguyen’s “Writing Principles for Task-Tuned Prompt Engineering” workshop both push clarity, explicit objectives, and task-tuned writing over vague persona flourish. A banking assistant uses persona “calm, plain-language financial guide” but **measures** success on instruction checks: no fabricated balances, mandatory disclaimer, tool `get_balance` before answering.

OpenAI Model Spec + API docs: developer messages outrank user; quoted/tool/multimodal content has **no authority by default**. That is the right mental model for product prompts—and the wrong thing to list as a “control” in a security review.

URL: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices  
Companions: https://developers.openai.com/api/docs/guides/prompt-engineering · https://model-spec.openai.com/2026-08-18.html · https://openai.com/index/our-approach-to-the-model-spec/ · https://ai.engineer/talks/writing-principles-for-task-tuned-prompt-engineering · https://claude.com/blog/best-practices-for-prompt-engineering · https://www.youtube.com/watch?v=6d60zVdcCV4 · https://www.youtube.com/watch?v=T9aRN5JkmL8 · https://community.openai.com/t/how-is-developer-message-better-than-system-prompt/1062784

---

## Open Questions

1. How much persona text is net-positive before instruction compliance drops on a given model?  
2. Should tone be a separate “style profile” message refreshed each turn to fight drift—without rewriting the cached prefix?  
3. Do developer-role restatements every N turns (community practice for some GPT models) generalize, or does compaction + tools replace them?  
4. How to eval multilingual persona consistency without enormous label cost?  
5. Reasoning models: does a strong persona in `instructions` compete with hidden chain-of-thought more than GPT-series?  
6. Agent SDK `claude_code` preset is a huge persona+instruction bundle—when does `append` for brand voice start to fight the preset’s engineering identity?

---

## Sources

- https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices  
- https://claude.com/blog/best-practices-for-prompt-engineering  
- https://www.anthropic.com/news/prompt-engineering-for-business-performance  
- https://code.claude.com/docs/en/agent-sdk/modifying-system-prompts  
- https://developers.openai.com/api/docs/guides/prompt-engineering  
- https://developers.openai.com/api/docs/guides/prompting  
- https://developers.openai.com/cookbook/examples/gpt-5/gpt-5_prompting_guide  
- https://model-spec.openai.com/2026-08-18.html  
- https://openai.com/index/our-approach-to-the-model-spec/  
- https://ai.engineer/talks/writing-principles-for-task-tuned-prompt-engineering  
- https://www.youtube.com/watch?v=6d60zVdcCV4  
- https://www.youtube.com/watch?v=T9aRN5JkmL8  
- https://community.openai.com/t/how-is-developer-message-better-than-system-prompt/1062784  
- https://community.openai.com/t/what-goes-in-the-system-vs-developer-role/1347594  
