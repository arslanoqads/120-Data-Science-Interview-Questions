# 00 — Week overview: LLM-as-judge vs Week 16 labels; tracing dashboard

> Week 17 — LLM-as-judge & observability  
> Research notes (raw). Phase 4 week after error-analysis flywheel (Week 16). Next: deployment / infra (Week 18). Do not start K8s/CI from this corpus.

---

## Fundamentals

Week 17 is the **automation and instrumentation** week of Phase 4. Week 15 **traced** agents. Week 16 **read traces**, built a **custom failure taxonomy**, and produced **expert Pass/Fail + critiques**. This week answers four questions Hamel Husain, Shreya Shankar, Langfuse, Phoenix, and OpenAI all treat as the *second* half of product evals:

1. **Can an LLM shadow the Week 16 expert** on residual *subjective* failures? (LLM-as-judge design)  
2. **How do we know the shadow is trustworthy?** (alignment / calibration: TPR/TNR on held-out labels)  
3. **When is a `json.loads` enough?** (code-based vs model-based evals)  
4. **Where do scores, tokens, and latency live so a team can act?** (tracing platforms + production dashboards)

### LLM-as-judge, validated against Week 16 labels

An **LLM-as-judge** (model-based evaluator) scores another system’s outputs with a prompted LLM. It is not a generic “quality” API. Practitioner consensus ([Hamel *Using LLM-as-a-Judge*](https://hamel.dev/blog/posts/llm-judge/); YouTube [Hamel `DZxaPNYi_k0`](https://www.youtube.com/watch?v=DZxaPNYi_k0)): treat the judge as a **classifier** of a **named Week 16 failure mode**, not as a 1–5 personality test.

**Input from Week 16 (required):**

| Week 16 artifact | Week 17 use |
|------------------|-------------|
| Benevolent-dictator Pass/Fail + critique | Gold labels + few-shots for the judge prompt |
| Custom binary taxonomy | One judge **per** residual judgment-heavy category (`missing_clarifying_question`, not `helpfulness`) |
| Failure **rates** | Decide *whether* a judge is worth 100–200 labels (FAQ: don’t automate trivia) |
| Flywheel eval set | Held-out test for TPR/TNR; CI regression set |

**Hamel “critique shadowing” in one paragraph:** principal domain expert labels Pass/Fail with a critique a new hire could apply → you **fix obvious prompt/tool bugs first** (those do not get judges) → you write a judge that asks for the **same** decision, stuffing expert critiques as few-shots → you iterate until **TPR and TNR** on held-out labels are acceptable → only then run the judge on unseen synthetic/production traffic to **estimate failure rates**. Honeycomb Query Assistant: **three iterations** to **>90%** human–judge agreement on a roughly balanced set ([llm-judge post](https://hamel.dev/blog/posts/llm-judge/); [Field Guide](https://hamel.dev/blog/posts/field-guide/)).

**Research backdrop you must not skip:**

- **G-Eval** (Liu et al., EMNLP 2023): GPT-4 + **chain-of-thought** + **form-filling**; Spearman **0.514** with humans on summarization (SummEval), beating ROUGE/BLEU. Same paper warns of **bias toward LLM-generated text** ([ACL](https://aclanthology.org/2023.emnlp-main.153/), [DOI](https://doi.org/10.18653/v1/2023.emnlp-main.153)). Use as evidence that *well-prompted* judges can correlate with humans on NLG — **not** as a drop-in product KPI.  
- **Who Validates the Validators?** (Shankar et al., 2024): LLM graders inherit LLM problems; humans must validate validators; **criteria drift** — criteria and observed outputs co-evolve ([arXiv:2404.12272](https://arxiv.org/abs/2404.12272)). Week 16 discovered criteria; Week 17 **must keep labeling** or the judge goes stale.  
- OpenAI: model grading works best with strong models and room to reason; **maintain agreement** with human feedback; prefer tasks LLMs are good at (pairwise, classification, criteria scoring) ([best practices](https://developers.openai.com/api/docs/guides/evaluation-best-practices); [cookbook](https://developers.openai.com/cookbook/examples/evaluation/getting_started_with_openai_evals)).

Langfuse product mapping: boolean / categorical / numeric scores; **observation-level** evaluators on live traffic (trace-level judges **deprecated** toward Langfuse v4, Cloud cutover **2026-11-16**); every judge run is itself a **trace** (`environment=langfuse-llm-as-a-judge`) ([LLM-as-a-Judge docs](https://langfuse.com/docs/evaluation/evaluation-methods/llm-as-a-judge)). Typical cost cited **~$0.01–0.10 per assessment** — **sample**.

### The tracing dashboard (substrate, not a vanity UI)

**Observability** = inferring internal state from logged outputs. **Tracing** = the causal tree of one request. Without traces, you cannot (a) attach retrieved docs to a faithfulness judge, (b) attribute p95 latency to retrieval vs model vs tools, (c) feed Week 16’s flywheel.

Core objects you must be able to point at on a dashboard:

| Object | Meaning (cross-vendor, then specifics) |
|--------|----------------------------------------|
| **Trace** | One request / session unit. Hamel FAQ: vendors **define this differently** — don’t assume “trace” means the same I/O everywhere. |
| **Span / observation** | One unit of work (retrieval, tool, LLM, chain). |
| **Generation** (Langfuse) | Observation specialized for LLM calls: `model`, `model_parameters`, `usage_details` (tokens), `cost_details`. |
| **OpenInference span kinds** (Phoenix/Arize) | `LLM`, `CHAIN`, `RETRIEVER`, `RERANKER`, `TOOL`, `AGENT`, `EMBEDDING`, `GUARDRAIL`, `EVALUATOR`, `PROMPT`, … ([spec](https://arize-ai.github.io/openinference/spec/)) |

Both Langfuse and Phoenix ride **OpenTelemetry** (OTLP). SDKs **batch asynchronously** so app latency impact is negligible if flush/batching is correct ([Langfuse observability](https://langfuse.com/docs/observability/overview); [SDK](https://langfuse.com/docs/observability/sdk/overview)).

**What “a tracing dashboard” means this week (minimum viable product view):**

```
Request ──► Trace (userId, sessionId, version, env)
              ├── RETRIEVER  (docs + scores) ──► attached onto generation I/O
              ├── TOOL
              └── GENERATION / LLM  (prompt, completion, tokens, cost, latency)
                        └── Score: faithfulness | should_clarify | json_ok
                              (human / code / calibrated judge)
```

Langfuse: custom dashboards for **cost, latency, volume, quality**; alerts on thresholds; scores unify human, code, and judge ([overview](https://langfuse.com/docs/observability/overview); [evals blog](https://langfuse.com/blog/2025-11-12-evals)). Phoenix: component latency, token breakdown, exceptions, retrieved docs, embeddings, sessions, annotations, LLM-as-judge on traces ([Phoenix tracing](https://arize.com/docs/phoenix/tracing/llm-traces)).

Online judges run **after the response ships**. They are **monitors**. A check that must **block** an unfaithful answer is a **guardrail** in the request path ([Langfuse faithfulness](https://langfuse.com/resources/engineering/rag-faithfulness-evaluation)).

### Mapping: what you ship this week

```
Week 16 labels + taxonomy
        │
        ├── objective failures ──► code evals ──► CI (every change)
        └── judgment failures ──► binary judge + few-shot critiques
                                      │
                              TPR/TNR on held-out expert labels
                                      │
                              pass gate? ──no──► iterate prompt / rubric / model
                                      │ yes
                                      ▼
                         offline experiments (datasets)
                                      │
                         sampled observation-level judges (prod)
                                      │
                         dashboards: cost · latency · errors · scores · drift
                                      │
                         disagreements + low scores ──► annotation queues ──► flywheel
```

### Mapping to adjacent weeks

| This week | Not this week |
|-----------|----------------|
| Calibrated binary judges vs Week 16 gold | Open-coding a new taxonomy from scratch (Week 16) |
| Langfuse vs Phoenix as **tracing + eval** products | K8s, Terraform, GitHub Actions as the main deliverable (Week 18) |
| Cost **on generations** as an observability signal | Full cost-engineering (routing, semantic cache) (Week 20) |
| Sampling 2–10% online judges | Claiming 100% traffic through GPT-4 judges |

---

## Alternatives & Tradeoffs

| Approach | Pros | Cons |
|----------|------|------|
| **Week 16 labels → scoped binary judges + code evals + tracing dashboards** | Metrics match expert taste; CI stays cheap; prod has attribution | Expert time; judge maintenance; OTEL noise if unfiltered |
| Vendor “hallucination + toxicity + helpfulness” pack on day one | Fast UI | Uncorrelated with Week 16 taxonomy; untrusted ([Field Guide](https://hamel.dev/blog/posts/field-guide/)) |
| Likert 1–5 multi-dim only | Familiar exec slides | Uncalibrated; annotator disagreement; Hamel: not actionable |
| G-Eval / ROUGE as *the* product KPI (OpenAI transcript example cites G-Eval) | Literature-backed for summarization research | Weak for *your* failure modes; LLM-text bias |
| Tracing without scores | Debugs latency/cost | Quality can rot while SLO is green |
| Scores without tracing | Pretty charts | Cannot debug RAG vs generation vs tools |

---

## Necessity

If you skip **validating judges on Week 16 labels**:

- You optimize the product for sycophancy, length bias, and self-preference (G-Eval paper; Hamel FAQ on same-model judges).  
- Dashboards nobody trusts → teams ignore evals (Field Guide §5).  
- You “fix” judge noise or miss real regressions.

If you skip **code evals**:

- CI is slow/flaky; you pay a judge to check `json.loads`.  
- Nova Escola: an eval for “two learning goals” that a **prompt fix** deleted ([production notes](https://hamel.dev/notes/llm/ai-product-engineering/evals-production.html)).

If you skip **tracing dashboards**:

- Faithfulness judges have no retrieved context on the observation ([Langfuse: observation-level evaluators do not load siblings](https://langfuse.com/docs/evaluation/evaluation-methods/llm-as-a-judge)).  
- Cost/latency is guesswork; Week 16 flywheel has no production inlet.

---

## Industry Practice

**Common:** Drop a vendor hallucination template; log the final answer only; never compute TPR/TNR.

**Strong / senior:**

1. Error analysis (Week 16) → one failure mode per judge.  
2. Expert labels **100–200** examples per mode when automating a judge (Hamel FAQ sample-size table, cited in Week 16 flywheel). Split train/dev/test.  
3. Iterate **prompt** (prefer PE over fine-tuning per Hamel) using expert critiques. Honeycomb: three loops.  
4. Gate on TPR & TNR; refuse to ship weak alignment.  
5. Recalibrate on app **or** judge model upgrades and on criteria drift.  
6. Code evals in CI; judges sampled online (Nova Escola **~2%** daily; Langfuse faithfulness often **5–10%**).  
7. Log judge calls as traces; filter OTEL noise (`should_export_span` / `shouldExportSpan`).  
8. Anthropic public guidance: combine **rule-based + model-based + targeted human** grading ([Planning to production PDF](https://www-cdn.anthropic.com/2db91550aa050eae0f205b04c908cd32ec1dab4b.pdf)).

Lenny’s Podcast (Hamel & Shreya, [`BsWxPI9UM4c`](https://www.youtube.com/watch?v=BsWxPI9UM4c)): start from actual errors; several **code** evals in CI; LLM evals **sparingly**.

---

## Concrete Scenario (URL)

**Hamel critique shadowing (Honeycomb Query Assistant)** — expert critiques as few-shots; three iterations; agreement vs TPR/TNR warning.  
https://hamel.dev/blog/posts/llm-judge/

**G-Eval** — CoT + form fill; Spearman 0.514; LLM-text bias.  
https://aclanthology.org/2023.emnlp-main.153/

**Nova Escola** — IAA worse than chance until rubric rewrite; then judges; **daily 2%** production suite.  
https://hamel.dev/notes/llm/ai-product-engineering/evals-production.html

**Langfuse** — observation-level judge + generation cost/latency dashboards; faithfulness needs context **on** the observation.  
https://langfuse.com/docs/evaluation/evaluation-methods/llm-as-a-judge  
https://langfuse.com/docs/observability/overview  
https://langfuse.com/resources/engineering/rag-faithfulness-evaluation

**Phoenix** — OTEL traces: latency, tokens, retrieved docs, embeddings, exceptions.  
https://arize.com/docs/phoenix/tracing/llm-traces

**YouTube** — code vs LLM evals + error-analysis-first:  
https://www.youtube.com/watch?v=BsWxPI9UM4c  
Judge as classifier:  
https://www.youtube.com/watch?v=DZxaPNYi_k0

---

## Open Questions

- When do multi-dimensional scores become necessary vs harmful for exec reporting?  
- How much self-enhancement bias remains for modern judges on **scoped binary** product tasks (Hamel: often OK if TPR/TNR hold)?  
- Probabilistic scoring (G-Eval n-sample / token probs) vs single structured label in production?  
- Standardized **trace** semantics across vendors (Hamel FAQ notes definition drift)?  
- Quality SLOs vs classic latency SLOs for nondeterministic systems?  
- OpenAI Evals **platform** shutdown (read-only 2026-10-31, shutdown 2026-11-30) vs portable grader patterns in `openai/evals` and successor Datasets?

---

## Sources

- https://hamel.dev/blog/posts/llm-judge/  
- https://hamel.dev/blog/posts/evals/  
- https://hamel.dev/blog/posts/evals-faq/  
- https://hamel.dev/blog/posts/field-guide/  
- https://hamel.dev/notes/llm/ai-product-engineering/evals-production.html  
- https://arxiv.org/abs/2404.12272  
- https://aclanthology.org/2023.emnlp-main.153/  
- https://langfuse.com/docs/evaluation/evaluation-methods/llm-as-a-judge  
- https://langfuse.com/docs/observability/overview  
- https://langfuse.com/blog/2025-11-12-evals  
- https://arize.com/docs/phoenix/tracing/llm-traces  
- https://arize-ai.github.io/openinference/spec/  
- https://developers.openai.com/api/docs/guides/evaluation-best-practices  
- https://developers.openai.com/api/docs/guides/evals  
- https://www.youtube.com/watch?v=BsWxPI9UM4c  
- https://www.youtube.com/watch?v=DZxaPNYi_k0  
