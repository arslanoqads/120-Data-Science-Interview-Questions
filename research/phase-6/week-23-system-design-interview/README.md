# Week 23 Research Corpus — System design interview

> Phase 6 — Capstone and Interview Readiness  
> **Status:** COMPLETE (deep pass)  
> Raw research corpus (not textbook). Legal/public sources only (Chip Huyen GenAI / ML systems / interviews, ByteByteGo public RAG / Perplexity / Agentic RAG posts, Anthropic Contextual Retrieval, Palantir FDSE blogs, OpenAI/Anthropic FDE public postings, Amazon interviewing guidance, public YouTube mocks & career talks). **No pirate PDFs, no libgen/pdfcoffee, no unauthorized Maven/Udemy decks.**

This directory is the Week 23 research repository. Read concept files in order, then the source map. **Do not start Week 24 (portfolio / resume language) from this corpus** — this week drills **RAG-at-scale whiteboards**, **prompt debugging under the clock**, **FDE integration cases**, **aloud tradeoffs**, and a **STAR bank** extracted from your own Weeks 6–22 builds. Capstone polish (Week 22) is assumed done; packaging for interview loops is the work.

| # | File | Concept |
|---|------|---------|
| 00 | [00-week-overview.md](00-week-overview.md) | Interview week spine; **8–10 STAR case studies** from own build |
| 01 | [01-retrieval-system-design-10m.md](01-retrieval-system-design-10m.md) | 10M-doc / mixed-query RAG design framework |
| 02 | [02-prompt-debugging-under-time-pressure.md](02-prompt-debugging-under-time-pressure.md) | Diagnostic ladder for prompt / RAG / AI-coding rounds |
| 03 | [03-fde-integration-case-study.md](03-fde-integration-case-study.md) | Integration blockers *are* the engagement |
| 04 | [04-narrating-tradeoffs-aloud.md](04-narrating-tradeoffs-aloud.md) | Recall↔precision, latency↔quality, build↔buy templates |
| 05 | [05-star-technical-case-studies.md](05-star-technical-case-studies.md) | STAR packaging, drillability, dual-track endings |
| — | [99-source-map.md](99-source-map.md) | Master URL / Huyen / ByteByteGo / FDE / YouTube mocks index |

## Completeness checklist (Week 23)

- [x] All syllabus Week 23 meta-concepts covered with **7 required fields**  
- [x] **Retrieval system design (~10M docs, mixed query types)** whiteboard spine (file 01)  
- [x] Clarify numbers → offline/online → ingest → route → hybrid retrieve → generate → wrap  
- [x] ACL **pre-filter**, deletes/tombstones, incremental index, hybrid + RRF, rerank budget, abstain, evals  
- [x] Anthropic Contextual Retrieval hybrid/rerank failure reductions cited  
- [x] ByteByteGo RAG / Perplexity / Agentic RAG public posts cited for stack + loops  
- [x] Chip Huyen GenAI platform + ML systems design + interview public materials cited  
- [x] **Prompt debugging under time pressure** diagnostic ladder (file 02)  
- [x] Localize layer before model swap; minimize; golden lock; AI-paired coding tactics  
- [x] **FDE integration case study** from Palantir / OpenAI / Anthropic primary language (file 03)  
- [x] Blockers (SSO, VPC, messy schema, undocumented API, residency, gold-set ownership) as the job  
- [x] **Narrating tradeoffs aloud** templates with latency/cost budgets (file 04)  
- [x] **8–10 STAR technical case studies** from curriculum own-build path (overview + file 05)  
- [x] STAR Action majority; “I” language; metrics; alternatives rejected; 2–3 follow-up depths  
- [x] Dual endings: Applied AI Engineer vs FDE emphasis  
- [x] 45-minute RAG design drill card preserved and expanded  
- [x] YouTube: Chip Huyen ML interviews (`pli1K75PSa8`); MLSys design (`c_AUuTuPA5k`); semantic search at scale mock (`MUs3JFkevak`); RAG 500M-docs interview Qs (`BY5hk_tMgyA`); Isaac Chung RAG production (`K-KhenQ3Scw`); Palantir deskside (`bPGnvfyMuxE`); Hamel/Shreya Lenny’s (`BsWxPI9UM4c`)  
- [x] OpenAI / Anthropic public FDE postings + Palantir FDSE blogs cited  
- [x] Per-week research **directory** (not a single thin file)  
- [x] `_PRIOR_SINGLE_FILE.md` removed after expansion  

## Syllabus build task (Week 23)

Syllabus treats Week 23 as **interview meta-work**: you already shipped Weeks 6–22 systems. This week you **rehearse packaging** under time pressure.

1. **Whiteboard a 10M-doc assistant.** Pin N, QPS, p95, freshness, ACL, wrong-answer cost. Split offline vs online. Force hybrid + ACL pre-filter + incremental deletes + rerank budget + abstain + eval gate ([Huyen GenAI platform](https://huyenchip.com/2024/07/25/genai-platform.html); [Anthropic Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval); [ByteByteGo RAG](https://blog.bytebytego.com/p/how-rag-enables-ai-for-your-data)).  
2. **Run the prompt-debug ladder live.** Reproduce → localize layer → minimize → one hypothesis → golden lock. Never jump to “bigger model” first ([Huyen LLM engineering](https://huyenchip.com/2023/04/11/llm-engineering.html); [Hamel evals](https://hamel.dev/blog/posts/evals/)).  
3. **Rehearse one FDE integration case.** Customer won’t give prod data / SSO blocked / undocumented API — what do you ship Monday? ([Palantir FDSE](https://blog.palantir.com/a-day-in-the-life-of-a-palantir-forward-deployed-software-engineer-45ef2de257b1); [OpenAI FDE](https://openai.com/careers/forward-deployed-engineer-%28fde%29-sf-san-francisco/); [Anthropic FDE](https://job-boards.greenhouse.io/anthropic/jobs/5391016008)).  
4. **Bank 8–10 STAR stories** from *your* build (chunk fix, hybrid exact-ID, ACL filter-before-rank, eval taxonomy, tool schema, messy SQL, cost/cache, scope freeze). Quantify; reject an alternative aloud; survive follow-ups.

Interview artifact = **annotated 10M whiteboard** + **one timed prompt-debug transcript** + **one FDE unblock case** + **STAR index (title / metric / systems / 3 follow-ups)** + **tradeoff one-liners**.

## Default path (synthesis)

1. **Pin requirements before boxes** ([technoscripts RAG layers](https://technoscripts.com/python-rag-system-design/); [Huyen ML interviews](https://www.youtube.com/watch?v=pli1K75PSa8)).  
2. **Hybrid + contextualize + rerank** beats dense-only vibes ([Anthropic](https://www.anthropic.com/news/contextual-retrieval)).  
3. **Agentic RAG is a branch**, not the default — cost/latency 3–10× ([ByteByteGo Agentic RAG](https://blog.bytebytego.com/p/how-agentic-rag-works)).  
4. **Debug the layer**, not the model ([Huyen](https://huyenchip.com/2023/04/11/llm-engineering.html); [Hamel](https://hamel.dev/blog/posts/evals/)).  
5. **Integration blockers are the FDE job** ([Palantir](https://blog.palantir.com/a-day-in-the-life-of-a-palantir-forward-deployed-software-engineer-45ef2de257b1)).  
6. **Aloud tradeoffs + STAR metrics** turn Week 22 polish into hire signal.
