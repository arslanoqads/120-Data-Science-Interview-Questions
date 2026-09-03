# 99 — Week 15 master source map

> Consolidated index of official docs, papers, talks, YouTube. Legal sources only; no pirate book sites.

**Deep-pass date:** 2026-09-03. Re-fetch before shipping a lecture — OpenAI Evals **platform** deprecation dates, Langfuse observation-level judges, and τ2-bench domain lists move.

---

## Anthropic

| Topic | URL |
|-------|-----|
| Demystifying evals for AI agents (transcript vs outcome, graders, pass@k / pass^k, roadmap, τ² loophole, CORE-Bench/METR grader bugs, appendix frameworks) | https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents |
| Building effective agents (ACI, workflows vs agents, support refunds, stopping conditions) | https://www.anthropic.com/engineering/building-effective-agents |

---

## LangSmith / LangChain AgentEvals

| Topic | URL |
|-------|-----|
| Trajectory evaluations (`strict` / `unordered` / `subset` / `superset`; LLM judge prompts) | https://docs.langchain.com/langsmith/trajectory-evals |
| Docs index (discover adjacent pages) | https://docs.langchain.com/llms.txt |

---

## Langfuse

| Topic | URL |
|-------|-----|
| AI agent evaluation (four dimensions; structured tool calls; offline/online; CI action; RAG-agent; session scores) | https://langfuse.com/resources/engineering/ai-agent-evaluation |
| Markdown twin | https://langfuse.com/resources/engineering/ai-agent-evaluation.md |
| Docs search API (as documented on that page) | https://langfuse.com/api/search-docs |
| Docs index | https://langfuse.com/llms.txt |

---

## OpenAI

| Topic | URL |
|-------|-----|
| Evaluate agent workflows (trace grading → datasets) | https://developers.openai.com/api/docs/guides/agent-evals |
| Evals guide | https://developers.openai.com/api/docs/guides/evals |
| Deprecations (Evals platform: read-only 2026-10-31, shutdown 2026-11-30) | https://developers.openai.com/api/docs/deprecations |
| Cookbook: OpenAI Evals → Promptfoo | https://developers.openai.com/cookbook/examples/evaluation/moving-from-openai-evals-to-promptfoo |

---

## Hamel Husain / Shreya Shankar

| Topic | URL |
|-------|-----|
| How do I evaluate agentic workflows? (E2E then steps; four tool checks; transition matrices; Bischof) | https://hamel.dev/blog/posts/evals-faq/how-do-i-evaluate-agentic-workflows.html |
| How do I evaluate complex multi-step workflows? (outcome + process; stages; cascade) | https://hamel.dev/blog/posts/evals-faq/how-do-i-evaluate-complex-multi-step-workflows.html |
| Evals FAQ hub | https://hamel.dev/blog/posts/evals-faq/ |

---

## τ-bench / τ²-bench (Sierra)

| Topic | URL |
|-------|-----|
| τ-bench code/data | https://github.com/sierra-research/tau-bench |
| τ-bench paper (DB state, user sim, pass^k, retail/airline) | https://arxiv.org/abs/2406.12045 |
| τ²-bench code | https://github.com/sierra-research/tau2-bench |
| τ²-bench paper (dual-control, telecom) | https://arxiv.org/abs/2506.07982 |

---

## WebArena

| Topic | URL |
|-------|-----|
| Project hub | https://webarena.dev/ |
| Paper (812 tasks, functional/backend eval, 14.41% vs 78.24%) | https://arxiv.org/abs/2307.13854 |
| Canonical implementation | https://github.com/web-arena-x/webarena |
| Paper PDF (site) | https://webarena.dev/static/paper.pdf |

---

## AgentBench (THUDM, ICLR’24)

| Topic | URL |
|-------|-----|
| GitHub (8 environments) | https://github.com/THUDM/AgentBench |
| arXiv | https://arxiv.org/abs/2308.03688 |
| ICLR abstract | https://proceedings.iclr.cc/paper_files/paper/2024/hash/e9df36b21ff4ee211a8b71ee8b7e9f57-Abstract-Conference.html |
| English intro (env write-ups) | https://github.com/THUDM/AgentBench/blob/main/docs/Introduction_en.md |

---

## Google / Vertex (trajectory metrics; A2A-adjacent)

| Topic | URL |
|-------|-----|
| Vertex Gen AI evaluation — agent trajectory metrics | https://cloud.google.com/blog/products/ai-machine-learning/introducing-agent-evaluation-in-vertex-ai-gen-ai-evaluation-service |
| Community: Vertex eval + Cloud Run A2A | https://discuss.google.dev/t/end-to-end-evaluation-of-multi-agent-systems-on-vertex-ai-with-cloud-run-deployment-for-a2a-agents/250552 |

---

## YouTube / courses / talks (legal public)

| Topic | URL |
|-------|-----|
| Hamel — How To Approach Your AI Evals (judge = classifier; calibrate) | https://www.youtube.com/watch?v=DZxaPNYi_k0 |
| Hamel — How to Automate AI Evals (Correctly) (analyze / measure / improve) | https://www.youtube.com/watch?v=tqUDjc1HzO4 |
| Hamel & Shreya — Why AI evals are the hottest new skill | https://www.youtube.com/watch?v=BsWxPI9UM4c |
| Hamel/Shreya — Intro to error analysis (annotation before taxonomy) | https://www.youtube.com/watch?v=qH1dZ8JLLdU |
| Harrison Chase — 3 ingredients for reliable enterprise agents (AI Engineer) | https://www.youtube.com/watch?v=kTnfJszFxCg |
| Talk page | https://ai.engineer/talks/3-ingredients-for-building-reliable-enterprise-agents |
| DeepLearning.AI A2A course trailer (handoff/context) | https://www.youtube.com/watch?v=4gYm0Rp7VHc |
| Course short link | https://goo.gle/dlai-a2a |
| Course intro lesson | https://learn.deeplearning.ai/courses/a2a-the-agent2agent-protocol/lesson/vtf72ap4/introduction |
| Hamel + Bischof — Stop Managing AI Projects Like Traditional Software (capability/failure funnel) | https://maven.com/p/9b1bab/stop-managing-ai-projects-like-traditional-software |
| Lessons From A Year Building With LLMs (Bischof on stage with LLM-app authors) | https://www.youtube.com/watch?v=qBHfQT3YtyY |

Bischof *Failure is a Funnel* (Data Council 2025) is cited with figures in Hamel’s agentic-workflow FAQ. Prefer that write-up plus the Maven lesson when a standalone conference VOD is not on YouTube.

---

## Cross-links from adjacent weeks (do not duplicate those corpora)

| Topic | URL |
|-------|-----|
| Week 14 A2A / writes (instrument these traces) | ../week-14-domain-agent-side-effects/ |
| LangGraph interrupts (confirmation appears in traces) | https://docs.langchain.com/oss/python/langgraph/interrupts |

---

## Source policy reminder

Allowed: official docs, reputable engineering blogs, conference talks, arXiv, public YouTube/courses.  
Not used: pirate book/PDF mirrors (pdfcoffee, libgen, etc.).
