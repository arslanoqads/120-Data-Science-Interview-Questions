# 99 — Week 20 master source map

> Consolidated index of RouteLLM, LiteLLM, Anthropic/OpenAI prompt caching, vLLM, FrugalGPT, LLMLingua, AWS, OpenTelemetry, YouTube. Legal sources only; no pirate book sites, no unauthorized course PDFs.

**Deep-pass date:** 2026-09-03. Re-fetch before shipping a lecture — provider cache prices/TTLs, OpenAI `prompt_cache_key` / GPT-5.6 breakpoint fields, Anthropic min-token tables, LiteLLM Auto Router names, and model list prices move.

**Not used:** pirate “LLMOps” books, libgen, pdfcoffee, leaked Udemy/Maven decks. arXiv, LMSYS blog, GitHub **lm-sys/RouteLLM**, vendor **docs**, Microsoft Research LLMLingua pages, ACM/SOSP talks on YouTube, official cookbooks only.

---

## RouteLLM / LMSYS

| Topic | URL |
|-------|-----|
| LMSYS blog (14% GPT-4 @ 95% MT Bench; MMLU/GSM8K; vs Martian/Unify) | https://www.lmsys.org/blog/2024-07-01-routellm/ |
| Paper: RouteLLM: Learning to Route LLMs with Preference Data | https://arxiv.org/abs/2406.18665 |
| HTML paper (v4) | https://arxiv.org/html/2406.18665v4 |
| GitHub serving + eval | https://github.com/lm-sys/RouteLLM |
| Hugging Face routers/datasets | https://huggingface.co/routellm |
| Chatbot Arena paper (preference source) | https://arxiv.org/abs/2403.04132 |

---

## Related routing / cascade research

| Topic | URL |
|-------|-----|
| FrugalGPT (sequential LLM cascade; up to 98% $ on their tasks) | https://arxiv.org/abs/2305.05176 |
| Hybrid-LLM (BERT router; cited in RouteLLM related work) | https://arxiv.org/abs/2404.14618 |

---

## LiteLLM

| Topic | URL |
|-------|-----|
| Router / load balancing (`simple-shuffle`, least-busy, latency, cost) | https://docs.litellm.ai/docs/routing |
| Proxy response caching (exact + semantic; agentic warning; 5 s embed timeout) | https://docs.litellm.ai/docs/proxy/caching |
| All cache backends | https://docs.litellm.ai/docs/caching/all_caches |
| Provider prompt caching (normalized usage, GPT-5.6 breakpoints) | https://docs.litellm.ai/docs/completion/prompt_caching |
| Auto-inject `cache_control` | https://docs.litellm.ai/docs/tutorials/prompt_caching |
| Claude Code prompt-cache **deployment** pinning | https://docs.litellm.ai/docs/tutorials/claude_code_prompt_cache_routing |
| Auto router + prompt cache (session affinity notes) | https://docs.litellm.ai/docs/auto_router/prompt_caching |
| Claude Code cost-cut bundle | https://docs.litellm.ai/docs/tutorials/claude_code_cut_costs |
| Spend tracking | https://docs.litellm.ai/docs/proxy/cost_tracking |
| Virtual keys | https://docs.litellm.ai/docs/proxy/virtual_keys |
| Users / teams | https://docs.litellm.ai/docs/proxy/users |
| Life of a request (auth cache vs spend async) | https://docs.litellm.ai/docs/proxy/architecture |

---

## Anthropic prompt caching

| Topic | URL |
|-------|-----|
| Prompt caching docs | https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching |
| Claude platform docs (automatic vs explicit) | https://platform.claude.com/docs/en/build-with-claude/prompt-caching |
| Cookbook notebook | https://github.com/anthropics/anthropic-cookbook/blob/main/misc/prompt-caching.ipynb |

---

## OpenAI prompt caching / batch

| Topic | URL |
|-------|-----|
| Prompt caching guide | https://platform.openai.com/docs/guides/prompt-caching |
| Launch post (1024 tokens, `cached_tokens`) | https://openai.com/index/api-prompt-caching/ |
| Cookbook 101 | https://developers.openai.com/cookbook/examples/prompt_caching101 |
| Cookbook 201 (`prompt_cache_key`) | https://developers.openai.com/cookbook/examples/prompt_caching_201 |
| Batch API | https://platform.openai.com/docs/guides/batch |

---

## Compression / self-hosted serving

| Topic | URL |
|-------|-----|
| LLMLingua paper | https://arxiv.org/abs/2310.05736 |
| Microsoft Research LLMLingua | https://www.microsoft.com/en-us/research/project/llmlingua/llmlingua/ |
| LLMLingua GitHub | https://github.com/microsoft/LLMLingua |
| vLLM PagedAttention paper | https://arxiv.org/abs/2309.06180 |
| vLLM blog (2023-06-20) | https://blog.vllm.ai/2023/06/20/vllm.html |
| vLLM docs | https://docs.vllm.ai/en/latest/ |
| vLLM GitHub | https://github.com/vllm-project/vllm |

---

## Cost / multi-tenant / telemetry

| Topic | URL |
|-------|-----|
| AWS GenAI Lens — multi-tenant platform scenario | https://docs.aws.amazon.com/wellarchitected/latest/generative-ai-lens/multi-tenant-generative-ai-platform-scenario.html |
| OpenTelemetry docs | https://opentelemetry.io/docs/ |

---

## YouTube (public talks / walkthroughs)

| Topic | URL |
|-------|-----|
| SOSP ’23 — PagedAttention / vLLM (Kwon, Stoica, et al.) | https://www.youtube.com/watch?v=UdNocRPQS3Y |
| RouteLLM tutorial (OpenAI-client drop-in routing demo) | https://www.youtube.com/watch?v=mcZKQe2pUA0 |
| Anthropic prompt caching walkthrough (cache_control placement) | https://www.youtube.com/watch?v=jQw3_6meUF8 |
| LiteLLM same-schema multi-provider intro | https://www.youtube.com/watch?v=MeTJVfdj3JM |

---

## Citation snippet (curriculum later)

```
Ong et al., 2024. RouteLLM: Learning to Route LLMs with Preference Data. arXiv:2406.18665.
LMSYS blog, 2024-07-01. RouteLLM: An Open-Source Framework for Cost-Effective LLM Routing.
Chen et al., 2023. FrugalGPT. arXiv:2305.05176.
Kwon et al., 2023. Efficient Memory Management for LLM Serving with PagedAttention. SOSP / arXiv:2309.06180.
Jiang et al., 2023. LLMLingua. arXiv:2310.05736.
```
