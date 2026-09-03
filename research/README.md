# AI Engineer / FDE Curriculum — Research Knowledge Base

Raw source material for the 24-week syllabus (TPM → AI Engineer / Forward Deployed Engineer). **Not a textbook** — research dumps with citations for later synthesis.

## Source policy

- **Allowed:** official documentation, reputable engineering blogs, open conference talks/transcripts, arXiv papers, public YouTube courses/talks.
- **Not used:** pirate book/PDF sites (pdfcoffee, pdfdrive, libgen, etc.) or unauthorized copyrighted book text.

## Layout note

Deep-pass weeks are **directories** (e.g. `phase-0/week-01-python-production/`) with one file per concept plus a source map. Earlier single-file weeks are upgraded to this layout when their deep pass runs.

## Entry format (per concept)

Each concept includes:

1. **Fundamentals** — plain-terms explanation  
2. **Alternatives & Tradeoffs** — real engineering design space  
3. **Necessity** — concrete failure modes if skipped  
4. **Industry Practice** — common vs strong/senior implementation  
5. **Concrete Scenario** — real example/benchmark/failure with URL  
6. **Open Questions** — debate / shifting paradigms  
7. **Sources** — URLs consulted  

## Index by phase

### Phase 0 — Engineering Foundations (Weeks 1–3)

| Week | File | Focus |
|------|------|--------|
| 1 | [week-01-python-production/](phase-0/week-01-python-production/) | **Research corpus** — typing, packaging, deps, venv, testable code, logging |
| 2 | [week-02-apis-async-testing/](phase-0/week-02-apis-async-testing/) | **Research corpus** — REST, FastAPI/Pydantic, async, test pyramid, mocks, contracts |
| 3 | [week-03-git-containers-system-design/](phase-0/week-03-git-containers-system-design/) | **Research corpus** — trunk-based, commits, Docker, compose, system design vocab |

### Phase 1 — LLM Application Engineering Core (Weeks 4–5)

| Week | File | Focus |
|------|------|--------|
| 4 | [week-04-multi-provider-llm/](phase-1/week-04-multi-provider-llm/) | **Research corpus** — multi-provider APIs, structured outputs, tokens, prompt caching, provider-agnostic client |
| 5 | [week-05-prompt-engineering/](phase-1/week-05-prompt-engineering/) | **Research corpus** — versioned prompts, templates, few-shot/cache, personas, injection |

### Phase 2 — RAG Systems (Weeks 6–10)

| Week | File | Focus |
|------|------|--------|
| 6 | [week-06-ingestion-chunking/](phase-2/week-06-ingestion-chunking/) | **Research corpus** — chunking strategies, overlap, metadata, structured content |
| 7 | [week-07-retrieval-beyond-cosine/](phase-2/week-07-retrieval-beyond-cosine/) | **Research corpus** — bi/cross-encoders, hybrid, RRF, lexical precision, vector DB tradeoffs |
| 8 | [week-08-reranking-query-understanding/](phase-2/week-08-reranking-query-understanding/) | **Research corpus** — two-stage retrieval, rerankers, lost-in-middle, HyDE/decomposition |
| 9 | [week-09-rag-failure-taxonomy/](phase-2/week-09-rag-failure-taxonomy/) | **Research corpus** — recall/rank/ground failures, citations, drift, long-context |
| 10 | [week-10-rag-evaluation/](phase-2/week-10-rag-evaluation/) | **Research corpus** — retrieval/generation metrics, golden sets, component vs E2E |

### Phase 3 — Agentic Systems (Weeks 11–15)

| Week | File | Focus |
|------|------|--------|
| 11 | [week-11-agent-fundamentals/](phase-3/week-11-agent-fundamentals/) | **Research corpus** — agent loop, tools, selection, retries, stop conditions |
| 12 | [week-12-mcp/](phase-3/week-12-mcp/) | **Research corpus** — MCP architecture, primitives, FDE integration surface |
| 13 | [week-13-orchestration-multi-agent/](phase-3/week-13-orchestration-multi-agent/) | **Research corpus** — graphs, multi-agent, handoffs, persistence, HITL |
| 14 | [week-14-domain-agent-side-effects/](phase-3/week-14-domain-agent-side-effects/) | **Research corpus** — A2A, side-effecting actions, safety controls |
| 15 | [week-15-agent-evaluation/](phase-3/week-15-agent-evaluation/) | **Research corpus** — trace eval, trajectory vs outcome, failure patterns |

### Phase 4 — Evals and Observability (Weeks 16–17)

| Week | File | Focus |
|------|------|--------|
| 16 | [week-16-error-analysis-flywheel/](phase-4/week-16-error-analysis-flywheel/) | **Research corpus** — manual error analysis, taxonomies, synthetic data, flywheel |
| 17 | [week-17-llm-judge-observability/](phase-4/week-17-llm-judge-observability/) | **Research corpus** — LLM-as-judge, calibration, code vs model evals, tracing |

### Phase 5 — Production, Cost, and Systems (Weeks 18–21)

| Week | File | Focus |
|------|------|--------|
| 18 | [week-18-deployment-infra/](phase-5/week-18-deployment-infra/) | **Research corpus** — containers, K8s fluency, CI/CD, Terraform |
| 19 | [week-19-auth-identity-enterprise/](phase-5/week-19-auth-identity-enterprise/) | **Research corpus** — OIDC/SAML, identity patterns, residency, multi-tenant RBAC |
| 20 | [week-20-cost-latency-engineering/](phase-5/week-20-cost-latency-engineering/) | **Research corpus** — routing, cascading, semantic cache, compression, cost dashboards |
| 21 | [week-21-legacy-messy-integration/](phase-5/week-21-legacy-messy-integration/) | **Research corpus** — messy SQL/ETL, partial failure, idempotent side effects |

### Phase 6 — Capstone and Interview Readiness (Weeks 22–24)

| Week | File | Focus |
|------|------|--------|
| 22 | [week-22-capstone-integration/](phase-6/week-22-capstone-integration/) | **Research corpus** — integration polish, eval-driven fixes, demo narrative |
| 23 | [week-23-system-design-interview/](phase-6/week-23-system-design-interview/) | **Research corpus** — system design, prompt debug, FDE cases, STAR write-ups |
| 24 | [week-24-portfolio-positioning.md](phase-6/week-24-portfolio-positioning.md) | Resume language, portfolio, dual-track positioning |

## Syllabus map (primary content shopping)

Per syllabus source map — use when deepening a week:

| Phase | Primary sources |
|-------|-----------------|
| 0 | Backend Python/FastAPI courses; Docker official docs |
| 1 | Anthropic + OpenAI official API docs/cookbooks |
| 2 | Chip Huyen public writing/talks; LangChain/LlamaIndex RAG tutorials |
| 3 | Anthropic MCP + Claude Agent SDK; LangGraph docs |
| 4 | Hamel Husain (hamel.dev); Langfuse / Arize Phoenix docs |
| 5 | Inference/cost docs; LiteLLM / RouteLLM; observability platforms |
| 6 | Live AI Engineer / FDE job postings (Palantir, Anthropic, OpenAI, Scale, Databricks) |
