# 03 — Few-shot placement and cache-hit effects

> Week 5 concept research (deep). Legal sources only.  
> Cross-link: [Week 4 — Prompt caching](../week-04-multi-provider-llm/04-prompt-caching.md)

---

## Fundamentals

**Few-shot / multishot prompting** supplies input→output exemplars to steer format, tone, and decision boundaries. Placement changes both **model behavior** and **prompt-cache economics**. Week 4 owns the **layout constraint** (exact-prefix matching; never put volatile examples in the shared prefix without accepting a cold cache). This file owns **selection policy**: how many shots, where they live, static vs retrieved, and how that maps onto OpenAI/Anthropic cache mechanics.

### Why shots work (and when they do not)

OpenAI: few-shot steers a model toward a new task **without fine-tuning**; show a **diverse** range of inputs with desired outputs; typically place examples in the **developer** message. Anthropic: examples are one of the most reliable steers for format/tone/structure; make them **relevant, diverse, structured** (wrap in tags); **3–5 examples** for best results; ask the model to critique your examples. Claude 4.x+ **overfits accidental patterns** in examples—bad shots teach bad behavior. Karina Nguyen (AI Engineer workshop / YouTube): diverse edge-case exemplars beat adjective piles; huge few-shot prefixes are a valid long-context strategy; for long-document QA, **question after documents** outperformed question-first (~30% in Anthropic’s tests). Diminishing returns: more shots are not monotonically better; irrelevant random shots can fail to help.

Structured outputs / enum tools (Week 4) often **remove the need for format few-shots**. Keep shots for **decision boundaries** (what counts as “escalate”, how to refuse) rather than “please emit JSON.”

### Placement options

1. **Inside system / developer / `instructions`**  
   Examples treated as part of durable instructions; high authority; excellent for stable style guides and classifiers. Counts toward the **cached static prefix** if unchanged. OpenAI’s official few-shot snippet is exactly this: `# Examples` plus `<product_review>` / `<assistant_response>` pairs in the developer message.

2. **As prior user/assistant turns**  
   Mimics real dialogue; often strong for format imitation; assistant “golden answers” teach structure. Cacheable if the whole transcript prefix is reused (multi-turn cache). Risk: analytics mix synthetic turns with real history; some models refer back to them as if they happened. OpenAI cookbook: extra `system` messages with `name: example_user` / `example_assistant` to mark them as non-live.

3. **In the current user message**  
   Tagged `<examples>…</examples>` beside the live query. Flexible per request. Shared-cache-friendly **only if** the example block is **byte-identical** across users **and** a cache breakpoint sits between that block and the unique query (Week 4 explicit breakpoints). Otherwise the unique query (or unique examples) sit in the prefix and you miss.

4. **Dynamic retrieval (example selectors)**  
   Embed the query, pull k nearest exemplars. LangChain: `FewShotChatMessagePromptTemplate` + `SemanticSimilarityExampleSelector` (vector store over example dicts). LlamaIndex: `function_mappings` that retrieve examples. LangSmith: `{{few_shot_examples}}` mustache placeholder filled from a dataset (evaluators: default k=5, random if more exist). Best **task fit per token** for diverse tasks; **worst** for caching and for prefix stability.

5. **Zero-shot + schema**  
   Often enough for extraction if Week 4 structured outputs are on.

### Cache interaction (Week 4 mechanics, Week 5 policy)

Exact prefix matching (both providers): a change at position N invalidates everything after N. Anthropic prefix order: **`tools` → `system` → `messages`**. OpenAI: put stable developer instructions and shared reference material **first**; GPT-5.6+ explicit `prompt_cache_breakpoint` isolates stable vs volatile sections.

| Placement | Cache effect | Quality effect | Policy |
|-----------|--------------|----------------|--------|
| Static few-shots early (after tools/system) | High shared hit rate; helps clear min token thresholds (OpenAI 1,024 / 2,048; Anthropic model-dependent 512–4,096) | Stable style/policy | Default when cache $ matters |
| Static synthetic dialogue turns, identical every request | Excellent if identical | High for format | Don’t mix with real turns in logs |
| User-tagged block **before** unique query, **after** breakpoint | Preserve hits on system+tools; pay for examples each time | Medium–high | Use when examples are shared but you already broke cache after system |
| Dynamic kNN few-shots **after** breakpoint | Preserve system+tool hits; examples uncached | Highest task fit | Pay the quality tax honestly |
| Dynamic examples **before** breakpoint / reshuffled in system | **Destroy shared cache for everyone** | Quality may rise | Forbidden unless you accept org-wide cold cache |
| Zero-shot + structured outputs | Best cache, shortest prefix | Weaker for nuanced style | Prefer for JSON/enum |

Anthropic thinking/`effort`: resolved effort is rendered into the prompt; **changing effort between requests invalidates cache**. Keep thinking config stable per conversation; steer thinking with **per-message** wording so earlier breakpoints survive (Week 4 + Anthropic steering docs).

OpenAI: few-shots in the prefix contribute to the cacheable minimum—sometimes **intentionally** keeping a stable 3-shot block is economically rational even if quality plateaued at 2 shots.

### Diminishing returns and selection

Measure shots on a **held-out set**, not vibes. Nguyen: diversity > count. Anthropic blog: modern Claude pays close attention to example details—audit shots for leaked policies, PII, and accidental biases. LangSmith few-shot evaluators: if examples are long, **lower k** to save tokens.

Do **not** put real user PII into exemplars; synthesize anonymized goldens and version them with the system prompt (file 01).

---

## Alternatives & Tradeoffs

| Placement | Quality leverage | Cache friendliness | Risk |
|-----------|------------------|--------------------|------|
| Static in system/developer | High for style/policy | Excellent | Bloats every request; slow to personalize |
| Static synthetic dialogue turns | High for format | Excellent if identical | Confuses analytics/history if mixed with real turns |
| User-tagged block before question | Medium–high | Good if identical block + breakpoint before unique query | User may “override” examples rhetorically |
| Dynamic kNN few-shots | Highest task fit | Poor if in prefix; OK after breakpoint | Latency + cost; selection bugs; cache miss on examples |
| Learned router (classifier → exemplar pack) | Packs stay cacheable | Good if pack count is small | Training/ops cost |
| Zero-shot + structured outputs | Often enough | Best | Weaker for nuanced style / policy edge cases |
| Fine-tune on goldens | Strong default | Best at inference | Slow iteration; still version the remaining prompt |

---

## Necessity

For classification, extraction style, and tool-calling etiquette, a few carefully chosen shots often beat paragraphs of instructions. Misplacement either **wastes cache budget** or **teaches the wrong authority** (e.g. burying critical rules only inside an example the model treats as optional).

Failure modes if skipped or done naively:

1. Dynamic selectors in the system prompt → org-wide cache miss after every unique query (Week 4).  
2. Too many similar shots → model copies a spurious correlation (Claude 4.x sensitivity).  
3. Format shots instead of structured outputs → brittle JSON, extra tokens.  
4. PII in goldens → privacy incident plus un-shareable cache prefix.  
5. Question buried *before* a 50k-token document dump → long-context QA regression (Anthropic: question at end).  
6. Reshuffling example order per request “for diversity” → identical to a cache-busting edit.

RAG-specific: retrieved **documents** are not few-shots. Do not store kNN docs in the shared prefix. Few-shots teach *how to answer*; RAG chunks are *what to answer from* and belong after the breakpoint (and in tagged user blocks—file 02).

---

## Industry Practice

### Common (weak)
- Paste six tweets into the system prompt; reorder them every call.  
- Semantic example selector with no cache breakpoint.  
- Zero measurement of 0 vs 2 vs 5 shots.  
- Live customer tickets as exemplars.

### Strong / senior
- Prefer **2–5 gold examples**; measure diminishing returns on a held-out set.  
- Keep production few-shots **static and versioned** with the system prompt when cache hit rate matters (file 01 changelog includes “added shot #4 for refund-or-replace”).  
- Put a **cache breakpoint after** static examples; only then add retrieved docs / user question ([Week 4](../week-04-multi-provider-llm/04-prompt-caching.md)).  
- Don’t mix real user PII into exemplars; synthesize anonymized goldens.  
- For OpenAI, remember few-shots in the prefix contribute to the 1,024+ token caching threshold—stable examples can be economically rational padding.  
- Evaluate whether structured outputs reduce the need for format few-shots.  
- LangChain: fixed `examples=` in production; `example_selector=` only behind a flag, and then **after** breakpoint.  
- LangSmith: manage example datasets independently from the template via `{{few_shot_examples}}` so shots can version without rewriting instructions—**still** freeze the production dataset if you care about cache.  
- Anthropic long context: documents (and large shot banks) **above** the query; quote-then-answer for faithfulness.

### RAG chatbot Week 5 application
Cache: system policy + tool schemas + **three static JSON-extraction examples**. User message: `<context>` chunks + `<question>`. If rare-class F1 is weak, retrieve extra shots **after** the breakpoint (or a second explicit OpenAI breakpoint) and accept uncached example tokens. Never insert per-query shots into `system`.

---

## Concrete Scenario

OpenAI Prompt Caching docs/Cookbook: tool definitions, developer messages, and conversation prefixes are cacheable—so a product that embeds three static JSON-extraction examples in the developer message clears the minimum token threshold and hits cache on subsequent extractions. Moving to per-query semantic example selection improves F1 on rare classes but collapses `cached_tokens` unless examples are moved after an explicit breakpoint and accepted as uncached.

Anthropic prompting best practices: 3–5 tagged, diverse examples; long documents at the top; question last. Nguyen’s workshop: huge few-shot prefixes as a long-context technique; diversity of edge cases; XML more reliable than markdown for some structured tasks in their Claude Instant-era tests (re-validate on current models).

URL: https://developers.openai.com/api/docs/guides/prompt-caching  
Companions: https://developers.openai.com/api/docs/guides/prompt-engineering · https://platform.claude.com/docs/en/build-with-claude/prompt-caching · https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices · https://ai.engineer/talks/writing-principles-for-task-tuned-prompt-engineering · https://www.youtube.com/watch?v=6d60zVdcCV4 · https://www.youtube.com/watch?v=T9aRN5JkmL8 · https://github.com/openai/openai-cookbook/blob/main/examples/Prompt_Caching_201.ipynb · [Week 4 caching notes](../week-04-multi-provider-llm/04-prompt-caching.md)

---

## Open Questions

1. Optimal split: how many shots in system vs as dialogue turns for tool-calling agents?  
2. Do mid-conversation Anthropic system messages that add examples preserve cache as cleanly as docs imply under load?  
3. When do learned routers (small classifiers choosing exemplar **packs**) beat embedding selectors—because packs stay prefix-stable?  
4. Interaction between few-shots and reasoning/thinking modes—do exemplars shorten or lengthen hidden chains? Changing `effort` already busts cache.  
5. LangSmith random k-of-N few-shot injection: can production ever use it without a deterministic seed keyed on `prompt_version`?  
6. Should Week 5’s few-shot selection policy live in the prompt layer or the cache-layout layer? (Week 4 open question—answer in practice: **policy here, breakpoint placement there**.)

---

## Sources

- https://developers.openai.com/api/docs/guides/prompt-engineering  
- https://developers.openai.com/api/docs/guides/prompt-caching  
- https://developers.openai.com/cookbook/examples/how_to_format_inputs_to_chatgpt_models  
- https://github.com/openai/openai-cookbook/blob/main/examples/Prompt_Caching_201.ipynb  
- https://platform.claude.com/docs/en/build-with-claude/prompt-caching  
- https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices  
- https://platform.claude.com/docs/en/build-with-claude/thinking-steering-and-cost  
- https://claude.com/blog/best-practices-for-prompt-engineering  
- https://www.anthropic.com/news/prompt-engineering-for-business-performance  
- https://docs.langchain.com/langsmith/prompt-template-format  
- https://docs.langchain.com/langsmith/create-few-shot-evaluators  
- https://reference.langchain.com/python/langchain-core/prompts/few_shot/FewShotChatMessagePromptTemplate  
- https://developers.llamaindex.ai/python/framework/module_guides/models/prompts/usage_pattern/  
- https://ai.engineer/talks/writing-principles-for-task-tuned-prompt-engineering  
- https://ai.engineer/talks/6d60zVdcCV4-writing-principles-task-tuned-prompt-engineering  
- https://www.youtube.com/watch?v=6d60zVdcCV4  
- https://www.youtube.com/watch?v=T9aRN5JkmL8  
- ../week-04-multi-provider-llm/04-prompt-caching.md  
