# Week 22 Research Corpus — Capstone integration

> Phase 6 — Capstone and Interview Readiness  
> **Status:** COMPLETE (deep pass)  
> Raw research corpus (not textbook). Legal/public sources only (Hamel Husain evals posts + FAQ, Chip Huyen GenAI / ML systems / interview public posts, Palantir FDSE day-in-life, OpenAI/Anthropic FDE public postings, Anthropic Contextual Retrieval, public YouTube demo & career talks). **No pirate PDFs, no libgen/pdfcoffee, no unauthorized Maven course decks.**

This directory is the Week 22 research repository. Read concept files in order, then the source map. **Do not start Week 23 (system-design interview drills) from this corpus** — this week **freezes scope**, turns **eval logs into a prioritized bug queue**, and ships a **demo narrative** interviewers trust. New model capabilities are not the goal; integration polish is.

| # | File | Concept |
|---|------|---------|
| 00 | [00-week-overview.md](00-week-overview.md) | Freeze scope; **top 5 eval bugs**; **5-min walkthrough** demo |
| 01 | [01-systems-integration-scope-freeze.md](01-systems-integration-scope-freeze.md) | Vertical-slice freeze; GenAI platform checklist; FDSE composition |
| 02 | [02-eval-log-driven-bug-fixes.md](02-eval-log-driven-bug-fixes.md) | Error analysis → taxonomy → frequency × severity → fix queue |
| 03 | [03-technical-demo-narrative.md](03-technical-demo-narrative.md) | Claim → architecture → evidence → failure → next bet |
| — | [99-source-map.md](99-source-map.md) | Master URL / Hamel / Chip Huyen / FDE / YouTube index |

## Completeness checklist (Week 22)

- [x] All syllabus Week 22 meta-concepts covered with **7 required fields**  
- [x] **Scope freeze** written: user job, corpus/tools, success metrics, non-goals  
- [x] Chip Huyen GenAI platform progressive stack as **integration checklist** (not feature wishlist)  
- [x] Palantir FDSE metaphor: compose existing platform for one customer / one vertical slice  
- [x] **Top 5 eval-driven bugs** named with fix leverage and demo impact (overview + file 02)  
- [x] Hamel error-analysis loop: sample → open coding → axial taxonomy → targeted evals → fix  
- [x] Prioritization = **frequency × user severity × fix leverage** (not vanity score deltas)  
- [x] Binary pass/fail + critique preferred over Likert for iteration speed  
- [x] Regression: golden set / scripted eval command; CI or README gate  
- [x] **5-minute walkthrough** script: stakes → architecture → success → refusal → metrics  
- [x] Demo shows **control under failure** (abstain, bad retrieval, tool error)  
- [x] Architecture diagram matches actual code paths (no vapor boxes)  
- [x] Metrics: quality + latency + cost proxy (even approximate)  
- [x] Interview bridge: one STAR-ready story from a real fix  
- [x] YouTube: Hamel/Shreya Lenny’s (`BsWxPI9UM4c`); error-analysis annotation (`qH1dZ8JLLdU`); Chip Huyen ML interviews (`pli1K75PSa8`); Chip Huyen MLSys (`c_AUuTuPA5k`); Palantir Foundry deskside demo (`bPGnvfyMuxE`)  
- [x] OpenAI / Anthropic public FDE postings cited for role-shaped scope (evals, production, customer env)  
- [x] Per-week research **directory** (not a single thin file)  
- [x] `_PRIOR_SINGLE_FILE.md` removed after expansion  

## Syllabus build task (Week 22)

Syllabus says “concepts: none new.” Treat that as **meta-work**: you already have Weeks 6–21 systems. This week you **stop building sideways** and make one vertical slice demo-safe.

1. **Freeze scope in writing.** One primary user job, one corpus + tool set, success metrics, and an explicit non-goals list (multi-tenant stub, second agent loop, billing UI — unless they *are* the job). Chip Huyen’s GenAI platform post is the stack you walk end-to-end for that slice: model API → guardrails → context (RAG/tools) → cache/route → logging/evals ([Building a Generative AI Platform](https://huyenchip.com/2024/07/25/genai-platform.html)).  
2. **Triage eval logs into a bug queue.** Sample 20–50 (then ~100) traces; open-code; axial-code a taxonomy with counts; rank **frequency × severity × leverage**; fix top classes; promote fixed failures into regression evals ([Hamel evals](https://hamel.dev/blog/posts/evals/); [error-analysis FAQ](https://hamel.dev/blog/posts/evals-faq/why-is-error-analysis-so-important-in-llm-evals-and-how-is-it-performed.html)).  
3. **Script a 5-minute walkthrough.** User stakes → requirements freeze → request + offline paths → live success with citations → intentional refusal/tool failure → metrics/tradeoffs → roadmap as non-goals. Record a backup; keep the live path primary.  
4. **Ship the polish gates.** Happy path on a clean machine / deploy URL; golden-set command in README; architecture diagram that matches code; one STAR story from a real taxonomy fix.

Interview artifact = **written demo contract** + **taxonomy table with top-5 fixes** + **5-min script (success + failure)** + **metrics line** (quality / p95 / $/1k).

## Default path (synthesis)

1. **Freeze before you polish.** Unbounded surface area kills demos ([Huyen GenAI platform](https://huyenchip.com/2024/07/25/genai-platform.html); [Palantir FDSE](https://blog.palantir.com/a-day-in-the-life-of-a-palantir-forward-deployed-software-engineer-45ef2de257b1)).  
2. **Compose what you built** (RAG + eval harness + one agent path); refuse greenfield side quests in the last stretch (FDSE: many capabilities for one customer by composing the platform).  
3. **Eval logs are a work queue**, not a vanity dashboard ([Hamel](https://hamel.dev/blog/posts/evals/); [Field Guide](https://hamel.dev/blog/posts/field-guide/)).  
4. **Fix ordinary bugs immediately** (chunk metadata, tool schema, prompt contradiction); reserve judges for subjective residuals (Weeks 16–17).  
5. **Demo narrative = claim → architecture → evidence → failure → next bet** ([Huyen ML systems / interviews](https://huyenchip.com/machine-learning-systems-design/toc.html); [YouTube ML interviews](https://www.youtube.com/watch?v=pli1K75PSa8)).  
6. **Control under failure beats peak vibes.** Interviewers trust abstain + tool-error demos more than another model swap.
