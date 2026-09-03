# 99 — Week 4 master source map

> Consolidated index of official docs, cookbooks, blogs, talks. Legal sources only.

---

## OpenAI — platform / developers

| Topic | URL |
|-------|-----|
| Function / tool calling | https://developers.openai.com/api/docs/guides/function-calling |
| Structured Outputs | https://developers.openai.com/api/docs/guides/structured-outputs |
| Prompt caching | https://developers.openai.com/api/docs/guides/prompt-caching |
| API prompt caching announcement | https://openai.com/index/api-prompt-caching/ |
| Cookbook: count tokens with tiktoken | https://developers.openai.com/cookbook/examples/how_to_count_tokens_with_tiktoken |
| Cookbook: Prompt Caching 201 | https://github.com/openai/openai-cookbook/blob/main/examples/Prompt_Caching_201.ipynb |
| openai-python helpers (`.parse`) | https://github.com/openai/openai-python/blob/main/helpers.md |
| openai-node tool stream example | https://github.com/openai/openai-node/blob/master/examples/tool-calls-stream.ts |
| Community: developer vs system role | https://community.openai.com/t/how-is-developer-message-better-than-system-prompt/1062784 |
| platform.openai.com (canonical host) | https://platform.openai.com/docs |

---

## Anthropic — docs / Claude platform

| Topic | URL |
|-------|-----|
| Messages streaming | https://docs.anthropic.com/en/api/messages-streaming |
| Tool use (implement) | https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/implement-tool-use |
| Fine-grained tool streaming | https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/fine-grained-tool-streaming |
| Prompt caching | https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching |
| Prompt caching (Claude platform mirror) | https://platform.claude.com/docs/en/build-with-claude/prompt-caching |
| Prompt caching launch post | https://www.anthropic.com/news/prompt-caching |
| Token counting | https://docs.anthropic.com/en/docs/build-with-claude/token-counting |
| Token counting (platform mirror) | https://platform.claude.com/docs/en/build-with-claude/token-counting |
| Structured outputs | https://platform.claude.com/docs/en/build-with-claude/structured-outputs |
| Working with messages | https://platform.claude.com/docs/en/build-with-claude/working-with-messages |
| How tool use works | https://platform.claude.com/docs/en/agents-and-tools/tool-use/how-tool-use-works.md |
| Skills: prompt-caching notes | https://github.com/anthropics/skills/blob/main/skills/claude-api/shared/prompt-caching.md |

---

## Tokenizers & schema libraries

| Resource | URL |
|----------|-----|
| tiktoken (GitHub) | https://github.com/openai/tiktoken |
| Pydantic | https://docs.pydantic.dev/latest/ |

---

## LiteLLM / multi-provider gateways

| Topic | URL |
|-------|-----|
| Getting started | https://docs.litellm.ai/docs/ |
| Function calling | https://docs.litellm.ai/docs/completion/function_call |
| Input params | https://docs.litellm.ai/docs/completion/input |
| Router / load balancing | https://docs.litellm.ai/docs/routing |
| Proxy fallbacks / reliability | https://docs.litellm.ai/docs/proxy/reliability |
| GitHub | https://github.com/BerriAI/litellm |

---

## YouTube / AI Engineer talks

| Talk | Link |
|------|------|
| Patrick Dougherty — How to Build AI Agents that Actually Work (AI Engineer Summit) | https://www.youtube.com/watch?v=7MiFIhlkBoE |
| Same talk (ai.engineer page) | https://ai.engineer/talks/how-to-build-ai-agents-that-actually-work |
| Build Production AI Agents in 2025 [With LiteLLM] | https://www.youtube.com/watch?v=_BuWC220CzA |

---

## Concept → primary sources

| Concept file | Primary citations |
|--------------|-------------------|
| 01 API mechanics | OpenAI function-calling; Anthropic messages-streaming; fine-grained tool streaming; Dougherty talk |
| 02 Structured outputs | OpenAI Structured Outputs; Claude structured outputs; Pydantic; openai-python helpers |
| 03 Token counting | tiktoken cookbook; Anthropic token-counting; tiktoken GitHub |
| 04 Prompt caching | Anthropic prompt-caching docs + news; OpenAI prompt-caching guide + cookbook 201 |
| 05 Provider-agnostic client | LiteLLM docs; OpenAI + Anthropic tool guides; LiteLLM + Dougherty YouTube |

---

## Syllabus build reminder

Ship a **provider-agnostic LLM client** (Protocol + OpenAI/Anthropic adapters, optionally LiteLLM for gateway/failover) that normalizes roles, tools, streaming, structured outputs, token counts, and cache usage. This corpus exists to make every choice in that client **explainable with citations**.
