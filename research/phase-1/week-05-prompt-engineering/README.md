# Week 5 Research Corpus — Prompt Engineering

> Phase 1 — LLM Application Engineering Core  
> **Status:** COMPLETE (deep pass)  
> Raw research corpus (not textbook). Legal sources only; no pirated books.

This directory is the Week 5 research repository. Read concept files in order, then the source map.

| # | File | Concept |
|---|------|---------|
| 00 | [00-week-overview.md](00-week-overview.md) | Syllabus mapping: versioned prompts as product behavior after Week 4 wire protocol |
| 01 | [01-system-prompts-version-control.md](01-system-prompts-version-control.md) | VCS, changelogs, prompt registries, canary / rollback |
| 02 | [02-prompt-templates-variable-injection.md](02-prompt-templates-variable-injection.md) | Templates, injection safety, LangChain / LlamaIndex patterns |
| 03 | [03-few-shot-placement-and-cache.md](03-few-shot-placement-and-cache.md) | User vs system placement; cache-hit effects (cross-link Week 4 caching) |
| 04 | [04-instruction-following-vs-persona.md](04-instruction-following-vs-persona.md) | Instruction hierarchy vs persona; Model Spec chain of command |
| 05 | [05-prompt-injection-and-guardrails.md](05-prompt-injection-and-guardrails.md) | OWASP LLM01, Willison, dual LLM, allowlists, how guardrails actually work |
| — | [99-source-map.md](99-source-map.md) | Master URL / cookbook / YouTube index |

## Completeness checklist (Week 5)

- [x] All syllabus Week 5 concepts covered with 7 required fields  
- [x] System prompts in version control with changelogs  
- [x] Prompt registries (LangSmith Hub, Langfuse labels) + git-as-source vs registry-as-source  
- [x] Canary / weighted rollout + rollback of prompt versions  
- [x] Prompt templates and variable injection (hygiene, SSTI, typed fill)  
- [x] LangChain ChatPromptTemplate / FewShot* + LlamaIndex PromptTemplate / RichPromptTemplate  
- [x] Few-shot placement: system vs dialogue turns vs current user vs dynamic selectors  
- [x] Cache-hit effects of few-shot placement — cross-linked to [Week 4 prompt caching](../week-04-multi-provider-llm/04-prompt-caching.md)  
- [x] Instruction-following vs persona; OpenAI Model Spec chain of command; Anthropic “give Claude a role”  
- [x] Prompt injection vs jailbreak (Willison); OWASP LLM01:2025 + GenAI Top 10 2026  
- [x] Dual LLM / quarantine, lethal trifecta, CaMeL, allowlists; how NeMo-style guardrails actually work  
- [x] Anthropic + OpenAI official prompting docs cited  
- [x] Simon Willison series + OWASP GenAI LLM Top 10 cited  
- [x] YouTube / AI Engineer talk citations  
- [x] AI/RAG-service-specific failure modes noted per concept  
- [x] Per-week research **directory** (not a single thin file)  
- [x] `_PRIOR_SINGLE_FILE.md` removed after expansion  

## Syllabus build task (Week 5)

Ship **versioned, templated prompts** for the FastAPI RAG chatbot from Weeks 1–4: store system text as reviewable artifacts; inject retrieved chunks and the user question as **data**, not instructions; keep static few-shots in the cache-stable prefix (Week 4); canary prompt changes behind a version ID; treat retrieved docs as untrusted (Week 5 injection model). This corpus makes every design choice (git vs registry, XML delimiters vs real isolation, persona vs contract, classifier-as-guardrail vs architecture) explainable with citations.
