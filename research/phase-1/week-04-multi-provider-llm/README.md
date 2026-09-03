# Week 4 Research Corpus — Multi-Provider LLM APIs

> Phase 1 — LLM Application Engineering Core  
> **Status:** COMPLETE (deep pass)  
> Raw research corpus (not textbook). Legal sources only; no pirated books.

This directory is the Week 4 research repository. Read concept files in order, then the source map.

| # | File | Concept |
|---|------|---------|
| 00 | [00-week-overview.md](00-week-overview.md) | Syllabus mapping, build task, Phase 1 entry point |
| 01 | [01-api-mechanics-streaming-tools-roles.md](01-api-mechanics-streaming-tools-roles.md) | OpenAI + Anthropic: streaming, tool/function calling, system/user/assistant/developer roles |
| 02 | [02-structured-output-enforcement.md](02-structured-output-enforcement.md) | JSON Schema, Pydantic validation, retry-on-malformed, provider structured outputs |
| 03 | [03-token-counting-context-windows.md](03-token-counting-context-windows.md) | Tokenizers, budgeting, truncation strategies, long-context tradeoffs |
| 04 | [04-prompt-caching.md](04-prompt-caching.md) | Cacheable prefixes, Anthropic/OpenAI mechanics, hit economics, few-shot placement |
| 05 | [05-provider-agnostic-client.md](05-provider-agnostic-client.md) | Wrapper interface, LiteLLM vs hand-rolled ports (syllabus build) |
| — | [99-source-map.md](99-source-map.md) | Master URL / cookbook / YouTube index |

## Completeness checklist (Week 4)

- [x] All syllabus Week 4 concepts covered with 7 required fields  
- [x] OpenAI + Anthropic API mechanics: streaming, tools, roles (system/user/assistant/developer)  
- [x] Structured output enforcement: JSON Schema, Pydantic, retry-on-malformed, provider strict modes  
- [x] Token counting & context windows: tiktoken, Anthropic `count_tokens`, truncation/budgeting  
- [x] Prompt caching: cacheable content, Anthropic/OpenAI mechanics, economics, few-shot placement  
- [x] Provider-agnostic client / wrapper interface (LiteLLM vs hand-rolled) — syllabus build augment  
- [x] OpenAI Cookbook + platform.openai.com / developers.openai.com citations  
- [x] docs.anthropic.com / platform.claude.com prompt-caching + Messages streaming citations  
- [x] tiktoken / Anthropic token-counting citations  
- [x] YouTube / AI Engineer talk citations  
- [x] AI/RAG-service-specific failure modes noted per concept  
- [x] Per-week research **directory** (not a single thin file)  
- [x] `_PRIOR_SINGLE_FILE.md` removed after expansion  

## Syllabus build task (Week 4)

Ship a **provider-agnostic LLM client** that wraps OpenAI and Anthropic behind one interface: normalize roles, tools, streaming events, and usage fields; prefer structured outputs + validated tool args; pre-flight token budgets; design prompts for cache-stable prefixes. This corpus makes every design choice (Chat Completions vs Responses, Anthropic `system` vs OpenAI `developer`, LiteLLM vs ports) explainable with citations.
