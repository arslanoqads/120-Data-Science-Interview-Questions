# 99 — Week 5 master source map

> Consolidated index of official docs, blogs, talks. Legal sources only.

---

## OpenAI — prompting, hierarchy, caching

| Topic | URL |
|-------|-----|
| Prompt engineering (roles, XML, few-shot, version-in-code) | https://developers.openai.com/api/docs/guides/prompt-engineering |
| Prompting overview (prompts as code; API prompt objects deprecated 2026) | https://developers.openai.com/api/docs/guides/prompting |
| Prompt caching | https://developers.openai.com/api/docs/guides/prompt-caching |
| Cookbook: format inputs / few-shot `name` fields | https://developers.openai.com/cookbook/examples/how_to_format_inputs_to_chatgpt_models |
| Cookbook: Prompt Caching 201 | https://github.com/openai/openai-cookbook/blob/main/examples/Prompt_Caching_201.ipynb |
| GPT-4.1 prompting guide (XML vs JSON long context) | https://developers.openai.com/cookbook/examples/gpt4-1_prompting_guide |
| GPT-5 prompting guide | https://developers.openai.com/cookbook/examples/gpt-5/gpt-5_prompting_guide |
| Model Spec (chain of command, 2026-08-18) | https://model-spec.openai.com/2026-08-18.html |
| Inside the Model Spec | https://openai.com/index/our-approach-to-the-model-spec/ |
| Community: developer vs system | https://community.openai.com/t/how-is-developer-message-better-than-system-prompt/1062784 |
| Community: system vs developer role | https://community.openai.com/t/what-goes-in-the-system-vs-developer-role/1347594 |

---

## Anthropic — prompting, system prompts, caching

| Topic | URL |
|-------|-----|
| Claude prompting best practices | https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices |
| Prompting Claude Opus 5 (verbosity, over-verification) | https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5 |
| Thinking / effort vs cache | https://platform.claude.com/docs/en/build-with-claude/thinking-steering-and-cost |
| Prompt caching | https://platform.claude.com/docs/en/build-with-claude/prompt-caching |
| Prompt caching (docs.anthropic mirror) | https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching |
| Agent SDK: modifying system prompts (preset / append / custom / CLAUDE.md) | https://code.claude.com/docs/en/agent-sdk/modifying-system-prompts |
| Blog: prompt engineering best practices (2026) | https://claude.com/blog/best-practices-for-prompt-engineering |
| Prompt engineering for business performance | https://www.anthropic.com/news/prompt-engineering-for-business-performance |

---

## LangChain / LangSmith / LlamaIndex — templates & registries

| Topic | URL |
|-------|-----|
| LangSmith manage prompts (envs, tags, owners, webhooks, public hub) | https://docs.langchain.com/langsmith/manage-prompts |
| LangSmith prompt engineering quickstart (`ChatPromptTemplate` push/pull) | https://docs.langchain.com/langsmith/prompt-engineering-quickstart |
| LangSmith prompt template formats (f-string vs mustache, few-shot placeholder) | https://docs.langchain.com/langsmith/prompt-template-format |
| LangSmith few-shot evaluators | https://docs.langchain.com/langsmith/create-few-shot-evaluators |
| `FewShotChatMessagePromptTemplate` reference | https://reference.langchain.com/python/langchain-core/prompts/few_shot/FewShotChatMessagePromptTemplate |
| LangChain few_shot.py source | https://github.com/langchain-ai/langchain/blob/master/libs/core/langchain_core/prompts/few_shot.py |
| LlamaIndex prompts overview | https://developers.llamaindex.ai/python/framework/module_guides/models/prompts/ |
| LlamaIndex prompt usage pattern (Rich / f-string / chat / function_mappings) | https://developers.llamaindex.ai/python/framework/module_guides/models/prompts/usage_pattern/ |
| LlamaIndex RichPromptTemplate features | https://developers.llamaindex.ai/python/examples/prompts/rich_prompt_template_features/ |

---

## Langfuse — versions, labels, canary composition

| Topic | URL |
|-------|-----|
| Prompt management overview | https://langfuse.com/docs/prompt-management/overview |
| Data model (versions vs labels) | https://langfuse.com/docs/prompt-management/data-model |
| Prompt version control | https://langfuse.com/docs/prompt-management/features/prompt-version-control |
| Get started | https://langfuse.com/docs/prompt-management/get-started |
| Prompt CI/CD (gates, canary split in app code) | https://langfuse.com/resources/engineering/prompt-cicd |

---

## OWASP / injection / guardrails

| Topic | URL |
|-------|-----|
| LLM01:2025 Prompt Injection | https://genai.owasp.org/llmrisk/llm01-prompt-injection/ |
| OWASP LLM Top 10 project (legacy + 2026 pointer) | https://owasp.org/www-project-top-10-for-large-language-model-applications/ |
| GenAI LLM Top 10 canonical repo | https://github.com/GenAI-Security-Project/GenAI-LLM-Top10 |
| Dual LLM pattern | https://simonwillison.net/2023/Apr/25/dual-llm-pattern/ |
| Delimiters won’t save you | https://simonwillison.net/2023/May/11/delimiters-wont-save-you/ |
| Indirect injection via YouTube transcripts | https://simonwillison.net/2023/May/15/indirect-prompt-injection-via-youtube-transcripts/ |
| Injection ≠ jailbreaking | https://simonwillison.net/2024/Mar/5/prompt-injection-jailbreaking/ |
| CaMeL commentary | https://simonwillison.net/2025/Apr/11/camel/ |
| Design patterns for securing agents | https://simonwillison.net/2025/Jun/13/prompt-injection-design-patterns/ |
| Lethal trifecta | https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/ |
| Prompt injection series index | https://simonwillison.net/series/prompt-injection/ |
| DeepMind CaMeL paper | https://arxiv.org/abs/2503.18813 |
| NeMo Guardrails paper | https://arxiv.org/abs/2310.10501 |
| NeMo architecture (how rails run) | https://docs.nvidia.com/nemo/guardrails/about-nemo-guardrails-library/how-it-works |
| Colang event loop | https://docs.nvidia.com/nemo/guardrails/v0.23.0/reference/colang-architecture-guide |
| NeMo Guardrails GitHub | https://github.com/NVIDIA/NeMo-Guardrails |

---

## YouTube / AI Engineer talks

| Talk | Link |
|------|------|
| Karina Nguyen — Principles for Prompt Engineering (YouTube) | https://www.youtube.com/watch?v=6d60zVdcCV4 |
| Same workshop (ai.engineer) | https://ai.engineer/talks/writing-principles-for-task-tuned-prompt-engineering |
| Alternate ai.engineer id | https://ai.engineer/talks/6d60zVdcCV4-writing-principles-task-tuned-prompt-engineering |
| Related Nguyen talk (YouTube) | https://www.youtube.com/watch?v=T9aRN5JkmL8 |
| DeLucia & Ali — Build a Prompt Learning Loop | https://ai.engineer/talks/build-a-prompt-learning-loop |
| How Claude Code works | https://ai.engineer/talks/how-claude-code-works |

---

## Changelog / versioning adjacent

| Resource | URL |
|----------|-----|
| Keep a Changelog | https://keepachangelog.com/en/1.1.0/ |

---

## Week 4 cross-link (cache layout)

| Resource | Path / URL |
|----------|------------|
| Week 4 prompt caching corpus | [../week-04-multi-provider-llm/04-prompt-caching.md](../week-04-multi-provider-llm/04-prompt-caching.md) |
| Week 4 source map | [../week-04-multi-provider-llm/99-source-map.md](../week-04-multi-provider-llm/99-source-map.md) |

---

## Concept → primary sources

| Concept file | Primary citations |
|--------------|-------------------|
| 01 System prompts / VCS / canary | OpenAI version-prompts-in-code; LangSmith manage-prompts; Langfuse version control + CI/CD; Agent SDK system prompts; Prompt learning loop talk |
| 02 Templates / injection hygiene | LlamaIndex prompts + usage_pattern; LangSmith template format + quickstart; OpenAI XML/Markdown; Anthropic XML tags; Willison delimiters |
| 03 Few-shot + cache | OpenAI few-shot + prompt-caching; Anthropic examples + long-context order; Week 4 caching; Nguyen YouTube; LangChain FewShot* / LangSmith `{{few_shot_examples}}` |
| 04 Instruction vs persona | Anthropic “give Claude a role”; OpenAI Model Spec chain of command; GPT-5 prompting guide; Nguyen workshop |
| 05 Injection / guardrails | OWASP LLM01; Willison series (dual LLM, delimiters, jailbreak distinction, trifecta, CaMeL); NeMo architecture docs; arXiv 2503.18813 |

---

## Syllabus build reminder

Ship **versioned, templated prompts** for the FastAPI RAG chatbot: reviewable system artifacts; retrieved chunks as **data**; static few-shots in the Week 4 cache-stable prefix; canary via `prompt_version`; treat corpus/tools as LLM01. This corpus exists to make every choice **explainable with citations**.
