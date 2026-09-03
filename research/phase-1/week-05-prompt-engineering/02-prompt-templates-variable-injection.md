# 02 — Prompt templates and variable injection

> Week 5 concept research (deep). Legal sources only.

---

## Fundamentals

A **prompt template** is a parameterized string or message list with placeholders filled at runtime (`{query}`, `{{ context_str }}`). Templates separate **stable instructions** (versioned, cacheable, reviewable — file 01) from **variable inputs** (user text, retrieved chunks, tool results, locale, tenant branding).

OpenAI’s developer-message skeleton is itself a template contract: **Identity → Instructions → Examples → Context** (context last, because it varies per request and should sit after the cache-stable prefix). Anthropic: wrap each content type in XML-ish tags (`<documents>`, `<document>`, `<question>`) so the model can parse mixed prompts; this is **clarity**, not isolation (file 05).

### Mechanics

**Substitution styles**

| Style | Syntax | Typical home | Risk |
|-------|--------|--------------|------|
| f-string / format | `{var}` | LangChain `PromptTemplate`, LlamaIndex `PromptTemplate`, Python format | Brace collisions; easy to interpolate user text into instruction regions |
| Mustache / Jinja | `{{ var }}`, loops, conditionals | LlamaIndex `RichPromptTemplate`; LangSmith mustache; LangChain jinja2 | **SSTI** if the *template string* is attacker-controlled; harder to review |
| Chat message lists | role-tagged parts with per-message vars | `ChatPromptTemplate`, LlamaIndex `ChatPromptTemplate` / `{% chat role= %}` | Safer if system is static and variables live in user messages |
| Programmatic builders | typed functions → `messages[]` | OpenAI 2026 “prompts in code” | More code; must stay consistent across providers |

**LangChain (production patterns, not the old “PromptTemplate is the product” demo).**

- `ChatPromptTemplate.from_messages([...])` — ordered roles: `("system", "…")`, `("user", "{question}")`, `MessagesPlaceholder("history")` or `("placeholder", "{msgs}")`.  
- `prompt.invoke({...})` then `convert_to_openai_messages` (or provider adapters) for the Week 4 client.  
- `FewShotPromptTemplate` / `FewShotChatMessagePromptTemplate` — prefix + example messages + suffix; either a **fixed** `examples` list or an `ExampleSelector` (file 03).  
- LangSmith Prompt Hub stores the `ChatPromptTemplate` as the versioned object: `push_prompt` / `pull_prompt`. Playground supports **f-string** and **mustache**; mustache is required for `{{few_shot_examples}}` injection and nested/conditional content.  
- Partials: bind some variables early (`partial`) so call sites only pass the per-request fields.

**LlamaIndex.**

- `PromptTemplate` — f-string `{context_str}` / `{query_str}`; `.format()` or `.format_messages()`.  
- `ChatPromptTemplate` — list of `ChatMessage` with roles.  
- `RichPromptTemplate` (llama-index-core ≥ 0.12.27) — Jinja: `{{ var }}`, `{% chat role="system" %}…{% endchat %}`, `{% for node in nodes %}`, filters like `| image` / `| audio` for multimodal blocks.  
- Pipeline reality: query engines nest synthesizers. `get_prompts()` returns namespaced keys such as `response_synthesizer:text_qa_template` and `response_synthesizer:refine_template`; `update_prompts({...})` patches them. Common pair: **text QA** (first-pass answer from retrieved nodes) + **refine** (fold additional nodes into `existing_answer`).  
- **function_mappings** — pass callables as template variables (e.g. reformat `context_str` as bullets) instead of string surgery at every call site. This is also the hook for **dynamic few-shot**.  
- **partial_format** and **template_var_mappings** — fill some vars early; remap LlamaIndex’s expected `context_str`/`query_str` onto your own names.

### Variable injection hygiene

Treat **all** runtime variables as **untrusted data**, not instructions—even “our” retrieved chunks (OWASP LLM01 scenario #4: poisoned RAG documents).

1. **Role separation over concatenation.** Keep instructions in `system`/`developer`; put documents and questions in `user` (or clearly tagged blocks). Do not assemble `"System: …\nUser: …"` into one completion string if you have a chat API.  
2. **Delimit for parseability.** Anthropic: `<document><source>…</source><document_content>…</document_content></document>`. OpenAI: Markdown headers + XML with attributes (`<product_review id="example-1">`). GPT-4.1 prompting guide: XML and “ID | TITLE | CONTENT” beat JSON blobs for long context; **if retrieved docs already contain XML, XML delimiters are weaker.**  
3. **Delimiters are not a security boundary.** Willison (file 05): stripping/randomizing delimiters still loses to “task already done, now do X.”  
4. **Validate before fill.** Max chars/tokens per chunk (Week 4 counting); allowlisted enums for `{locale}`, `{tier}`; schema for structured tool traces. Refuse to render if context exceeds budget.  
5. **SSTI / template-logic RCE.** If you `Template(user_supplied_string).render(...)`, the user writes Jinja (`{{ self.__init__.__globals__ }}`). **Never let untrusted text become the template**; only let it become **values**. Sandbox or disable Jinja features if templates are loaded from a registry that non-engineers edit.  
6. **Escape only for your delimiter scheme.** Escaping `<` in user text helps your XML parser; it does not stop prompt injection.  
7. **Snapshot rendered prompts in traces** with PII redaction (file 01 version IDs + Week 17 observability later).

OpenAI cookbook historical pattern: few-shot as extra `system` messages with `name: example_user` / `example_assistant` so the model does not treat them as live dialogue—still templates, still versioned.

---

## Alternatives & Tradeoffs

| Style | Pros | Cons | When |
|-------|------|------|------|
| Hardcoded prompts | Fast to ship | Copy drift; untestable fill | Never in the RAG service |
| Simple `{var}` templates | Clear, unit-testable `format(vars)` | Weak logic; easy misuse | Default for QA/RAG |
| Jinja / Rich / mustache | Loops over nodes, conditionals, multimodal filters | Review difficulty; SSTI; logic bugs in templates | Many chunks, chat-role blocks in one file |
| Programmatic message builders | Full control, typed, OpenAI-aligned | More code; provider mapping still needed | Multi-provider client (Week 4) |
| Example selectors (dynamic few-shot) | Better relevance | Cache misses; retrieval complexity | After a cache breakpoint (file 03) |
| LlamaIndex default QA/refine prompts | Fast RAG | Hidden nested prompts; Shakespeare-style overrides surprise you | Always `get_prompts()` before shipping |

**Provider mapping:** one template across OpenAI `developer` vs Anthropic `system` vs Responses `instructions` is a **renderer** problem (Week 4 adapter), not three copy-pasted strings.

---

## Necessity

Production apps rarely have a single static prompt. RAG, multi-tenant branding, localization, and tool traces all require **safe, testable injection**. Without templates:

1. **Copy drift** — support, RAG, and agent paths each invent a slightly different contract.  
2. **Unbounded fill** — retrieved chunks blow the context window (Week 4 400s) or drown the question.  
3. **Instruction/data mix-up** — user text lands in the system region → direct injection.  
4. **Untestable renders** — you cannot assert `format(vars)` in CI.  
5. **Jinja as an attack surface** — registry-editable templates execute attacker expressions.  
6. **Hidden LlamaIndex prompts** — `refine_template` still ships the library default you never reviewed.

RAG-specific: concatenating `{context_str}` above the question without tags + without a token cap is how “lost in the middle” and indirect injection share a root cause (unstructured, unbounded untrusted text).

---

## Industry Practice

### Common (weak)
- `f"You are a helpful assistant. Context: {docs}. Question: {q}"` in the system prompt.  
- No max length on `{context_str}`.  
- Jinja templates loaded from user-editable CMS.  
- Never call `get_prompts()` on a LlamaIndex query engine.

### Strong / senior
- Instructions in system; variable documents/questions in user; XML/Markdown structure for humans *and* models.  
- Centralize templates next to prompt versions (file 01); snapshot rendered prompts in traces (redacted).  
- Cap injected context via Week 4 token counting **inside the template pipeline**, not after the API 400.  
- Prefer `format_messages` / chat APIs over stuffing a completion string.  
- LlamaIndex/LangChain: `function_mappings` / partials for derived fields (bulleted contexts) rather than ad-hoc surgery at call sites.  
- Type-check template variables (Pydantic/JSON Schema for prompt inputs)—the OpenAI 2026 “typed function arguments” recommendation.  
- LangSmith: mustache when you need loops or `{{few_shot_examples}}`; f-string when substitution is enough.  
- If retrieved documents contain your delimiter language, switch delimiter family (GPT-4.1 guide).

### RAG chatbot Week 5 application
Load `prompts/answer_v4.chat.yaml` (or Hub pull). System: policy + output contract (static). User: `{% for node in nodes %}{{ node.text }}{% endfor %}` or explicit `<context>` list + `<question>`. `function_mapping` strips HTML comments from chunks (soft mitigation, not a boundary). Refuse render if `count_tokens(messages) > budget`. Week 4 client sends Anthropic `system` vs OpenAI `developer` from the same template AST.

---

## Concrete Scenario

LlamaIndex prompt docs show a QA template with `{context_str}` / `{query_str}` (or Jinja `{{ }}` in `RichPromptTemplate`), then `format_messages(...)` for chat models. Nested engines expose `response_synthesizer:text_qa_template` + `refine_template` via `get_prompts()`. LangSmith quickstart pushes a `ChatPromptTemplate` with `("{system}", …), ("{user}", "{question}")` and pulls it by name for OpenAI Chat Completions.

A support RAG service: versioned chat template → inject top-k chunks into `<context>` → inject the user question into `<question>` → refuse if context tokens exceed budget → log `prompt_version` + redacted render.

URL: https://developers.llamaindex.ai/python/framework/module_guides/models/prompts/  
Companions: https://developers.llamaindex.ai/python/framework/module_guides/models/prompts/usage_pattern/ · https://developers.llamaindex.ai/python/examples/prompts/rich_prompt_template_features/ · https://docs.langchain.com/langsmith/prompt-engineering-quickstart · https://docs.langchain.com/langsmith/prompt-template-format · https://developers.openai.com/api/docs/guides/prompt-engineering · https://developers.openai.com/cookbook/examples/gpt4-1_prompting_guide · https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

---

## Open Questions

1. Standard way to type-check template variables across teams (JSON Schema / Pydantic for prompt inputs)? OpenAI is pushing typed builders; Hub prompts are still loosely typed strings.  
2. Should rendering happen in a sandbox to prevent template-logic RCE (Jinja) when PMs edit mustache in a UI?  
3. How to share one template AST across OpenAI developer-role vs Anthropic `system` vs Responses `instructions` cleanly in the Week 4 adapter?  
4. Best redaction policy when logging fully rendered prompts containing PII?  
5. When retrieved HTML/PDF text contains `</document>` or `{question}`, is escaping enough for quality, or must we switch delimiter alphabets per corpus?  
6. LlamaIndex `refine_template`: is sequential refine still justified vs stuffing + Week 4 long-context models?

---

## Sources

- https://developers.llamaindex.ai/python/framework/module_guides/models/prompts/  
- https://developers.llamaindex.ai/python/framework/module_guides/models/prompts/usage_pattern/  
- https://developers.llamaindex.ai/python/examples/prompts/rich_prompt_template_features/  
- https://docs.langchain.com/langsmith/prompt-engineering-quickstart  
- https://docs.langchain.com/langsmith/prompt-template-format  
- https://reference.langchain.com/python/langchain-core/prompts/few_shot/FewShotChatMessagePromptTemplate  
- https://github.com/langchain-ai/langchain/blob/master/libs/core/langchain_core/prompts/few_shot.py  
- https://developers.openai.com/api/docs/guides/prompt-engineering  
- https://developers.openai.com/api/docs/guides/prompting  
- https://developers.openai.com/cookbook/examples/how_to_format_inputs_to_chatgpt_models  
- https://developers.openai.com/cookbook/examples/gpt4-1_prompting_guide  
- https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices  
- https://claude.com/blog/best-practices-for-prompt-engineering  
- https://simonwillison.net/2023/May/11/delimiters-wont-save-you/  
