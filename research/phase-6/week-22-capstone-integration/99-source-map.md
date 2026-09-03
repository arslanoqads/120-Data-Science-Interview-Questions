# 99 — Week 22 master source map

> Consolidated index of Hamel Husain evals posts, Chip Huyen public posts/talks, Palantir FDSE / Foundry demos, OpenAI/Anthropic FDE public postings, Anthropic Contextual Retrieval, RAG interview rubrics, YouTube demo & career talks. Legal sources only; no pirate book sites, no unauthorized Maven/Udemy decks.

**Deep-pass date:** 2026-09-03. Re-fetch before shipping a lecture — job postings move, Greenhouse IDs change, and YouTube URLs are stable but titles drift.

**Not used:** pirate PDFs, libgen, pdfcoffee, leaked course recordings, unauthorized copies of *AI Engineering* / *Designing Machine Learning Systems* book text. Public **huyenchip.com** posts, free ML interviews book site, **hamel.dev**, vendor/career pages, public **YouTube** only.

---

## Hamel Husain — evals & error analysis

| Topic | URL |
|-------|-----|
| Your AI Product Needs Evals | https://hamel.dev/blog/posts/evals/ |
| AI Evals FAQ hub | https://hamel.dev/blog/posts/evals-faq/ |
| Why error analysis matters / how performed | https://hamel.dev/blog/posts/evals-faq/why-is-error-analysis-so-important-in-llm-evals-and-how-is-it-performed.html |
| Field Guide to rapidly improving AI products | https://hamel.dev/blog/posts/field-guide/ |
| Office hours — error analysis notes | https://hamel.dev/notes/llm/officehours/erroranalysis.html |
| Lenny’s Podcast w/ Hamel & Shreya (YouTube) | https://www.youtube.com/watch?v=BsWxPI9UM4c |
| Intro to error analysis / annotation apps (YouTube) | https://www.youtube.com/watch?v=qH1dZ8JLLdU |
| Aakash Gupta masterclass write-up (public notes on Hamel/Shreya) | https://www.aakashg.com/hamel-shreya-ai-evals-step-by-step/ |
| Lenny newsletter companion (evals / error analysis) | https://www.lennysnewsletter.com/p/why-ai-evals-are-the-hottest-new-skill |

---

## Chip Huyen — GenAI platform, production, systems, interviews

| Topic | URL |
|-------|-----|
| Building a Generative AI Platform (2024-07-25) | https://huyenchip.com/2024/07/25/genai-platform.html |
| Building LLM applications for production (2023-04-11) | https://huyenchip.com/2023/04/11/llm-engineering.html |
| ML Systems Design TOC | https://huyenchip.com/machine-learning-systems-design/toc.html |
| ML Systems Design GitHub | https://github.com/chiphuyen/machine-learning-systems-design |
| ML Interviews book (free site) | https://huyenchip.com/ml-interviews-book/ |
| ML Interviews book GitHub | https://github.com/chiphuyen/ml-interviews-book |
| FSDL — Machine Learning Interviews (YouTube) | https://www.youtube.com/watch?v=pli1K75PSa8 |
| Stanford MLSys Ep. 5 — Principles of Good ML Systems Design (YouTube) | https://www.youtube.com/watch?v=c_AUuTuPA5k |
| Databricks — Principles of Good ML Systems Design (YouTube) | https://www.youtube.com/watch?v=g08qBcdk3Ss |

---

## FDE / career postings & day-in-life

| Topic | URL |
|-------|-----|
| Palantir — Day in the Life of an FDSE | https://blog.palantir.com/a-day-in-the-life-of-a-palantir-forward-deployed-software-engineer-45ef2de257b1 |
| Palantir Developer Deskside — Workshop map workflow (YouTube demo) | https://www.youtube.com/watch?v=bPGnvfyMuxE |
| OpenAI Forward Deployed Engineer (SF) | https://openai.com/careers/forward-deployed-engineer-%28fde%29-sf-san-francisco/ |
| Anthropic Forward Deployed Engineer (Greenhouse) | https://job-boards.greenhouse.io/anthropic/jobs/5391016008 |

---

## Retrieval / architecture scope decisions

| Topic | URL |
|-------|-----|
| Anthropic Contextual Retrieval (when RAG vs long context) | https://www.anthropic.com/news/contextual-retrieval |
| ByteByteGo — How Agentic RAG Works | https://blog.bytebytego.com/p/how-agentic-rag-works |

---

## Demo / interview rubrics (RAG walkthrough)

| Topic | URL |
|-------|-----|
| Python RAG system design interview layers | https://technoscripts.com/python-rag-system-design/ |
| SDE→AI RAG practice rubric | https://sde2ai.com/practice/rag |

---

## YouTube index (demo & career talks)

| Talk | ID / URL | Use in Week 22 |
|------|----------|----------------|
| Hamel & Shreya — Why AI evals are the hottest new skill (Lenny’s) | `BsWxPI9UM4c` | Error analysis before metrics; demo “how we know” |
| Error analysis annotation / custom viewers | `qH1dZ8JLLdU` | Low-friction triage UX for polish week |
| Chip Huyen — ML Interviews (FSDL) | `pli1K75PSa8` | Career/interview narrative; portfolio signal |
| Chip Huyen — Stanford MLSys systems design | `c_AUuTuPA5k` | Iterative production framing for architecture walkthrough |
| Chip Huyen — Databricks ML systems design | `g08qBcdk3Ss` | Shorter systems-design principles cut |
| Palantir Foundry Developer Deskside | `bPGnvfyMuxE` | Composed product demo metaphor (ingest → workflow) |

---

## Concept → primary sources

| Concept file | Primary citations |
|--------------|-------------------|
| [00-week-overview.md](00-week-overview.md) | Huyen GenAI platform; Hamel evals + Lenny’s YT; Palantir FDSE; top-5 bug table; 5-min script |
| [01-systems-integration-scope-freeze.md](01-systems-integration-scope-freeze.md) | Huyen GenAI + production posts; Palantir FDSE + deskside YT; OpenAI/Anthropic FDE; Contextual Retrieval |
| [02-eval-log-driven-bug-fixes.md](02-eval-log-driven-bug-fixes.md) | Hamel evals + FAQ + Field Guide; YT `BsWxPI9UM4c` / `qH1dZ8JLLdU`; Anthropic FDE evals line |
| [03-technical-demo-narrative.md](03-technical-demo-narrative.md) | Huyen ML systems + interviews (+ YT); RAG rubrics; Palantir demo YT; Hamel “debug via evals” |

---

## Week 22 meta-checklist (research-derived punch list)

| Gate | Pass criterion |
| --- | --- |
| Scope freeze | One primary user job + written non-goals |
| Integration | Happy path works on clean machine / deploy URL |
| Eval triage | Taxonomy with counts; top bugs fixed or explicitly deferred with reason |
| Regression | Golden set in CI or scripted eval command in README |
| Demo script | Success + refusal + one integration failure narrated |
| Architecture | Diagram matching actual code paths (no vapor boxes) |
| Metrics | At least quality + latency + cost proxy |
| Interview bridge | One STAR-ready story extracted from a real fix |
