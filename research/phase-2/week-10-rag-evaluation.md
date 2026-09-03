# Week 10 — RAG Evaluation (Raw Source Material)

> Curriculum research notes for RAG evaluation/debugging. Legal sources only (official docs, arXiv, public blogs, YouTube). Not a finished lesson plan.

---

## Concept 1 — Retrieval Metrics (Precision@k, Recall@k, MRR, NDCG)

### Fundamentals

Treat the retriever as a classical IR system: for each query *q*, the system returns an ordered list *D₁…Dₖ*. Labels are binary or graded relevance of documents/chunks to *q* (or to a gold answer’s supporting passages).

| Metric | Definition (operational) | Sensitive to | Typical RAG use |
| --- | --- | --- | --- |
| **Precision@k** | (# relevant in top *k*) / *k* | Noise in the packed window | “Are we feeding junk to the LLM?” |
| **Recall@k** | (# relevant in top *k*) / (# relevant in corpus qrels) | Misses outside *k* | “Can generation possibly succeed?” — primary recall-failure detector |
| **MRR** (Mean Reciprocal Rank) | mean over queries of 1/rank of *first* relevant hit | Single-answer lookup | FAQ / factoid RAG where one chunk suffices |
| **NDCG@k** | Discounted cumulative gain normalized by ideal ordering | Graded relevance + rank position | Tuning hybrid search & rerankers |

**Formulas (binary relevance):**

- \(\mathrm{P@k} = \frac{|\{d \in \mathrm{top\text{-}k} : \mathrm{rel}(d)=1\}|}{k}\)
- \(\mathrm{R@k} = \frac{|\{d \in \mathrm{top\text{-}k} : \mathrm{rel}(d)=1\}|}{|\{d : \mathrm{rel}(d)=1\}|}\)
- \(\mathrm{RR} = 1/\min\{i : \mathrm{rel}(D_i)=1\}\) (0 if none); MRR = mean RR
- \(\mathrm{DCG@k} = \sum_{i=1}^{k} \frac{2^{rel_i}-1}{\log_2(i+1)}\); NDCG = DCG / IDCG

**RAGAS Context Precision** is a rank-aware cousin: average of precision@k only at ranks where the chunk is relevant (\(v_k=1\)), rewarding relevant chunks appearing early — documented at docs.ragas.io.

**Azure Document Retrieval evaluator** exposes composite search metrics including **NDCG**, **XDCG**, **Fidelity** (good docs returned / known good), **Max Relevance**, **Holes** (missing judgments).

**NVIDIA NeMo** retrieval eval uses **pytrec_eval** for `recall@k` and `ndcg@k` alongside generation metrics.

### Alternatives & Tradeoffs

| Choice | Tradeoff |
| --- | --- |
| Binary vs graded labels | Graded NDCG needs expensive rubrics; binary understates “partially useful” chunks |
| Doc-level vs chunk-level qrels | Chunk labels match the actual prompt unit; doc labels are cheaper but coarse |
| Fixed *k* vs *k* sweeps | Production *k* must be measured; sweeps reveal recall–noise frontier |
| Exact match IDs vs LLM-judged relevance | ID precision is cheap/reproducible; LLM relevance scales when qrels missing (but needs calibration) |
| MRR vs Recall@k | MRR ignores extra supporting chunks needed for multi-hop |

Proxy trap: optimizing embedding cosine to a synthetic query set can raise P@k while harming real-user recall.

### Necessity

End-to-end answer accuracy **confounds** retrieval and generation. Without retrieval metrics you cannot tell FP2 (missed ranking) from FP4 (not extracted). Recall@k is the gate: if recall@k = 0, groundedness of the answer is irrelevant to debugging retrieval.

### Industry Practice

- Maintain a **qrels** file (TREC-style) or ID lists of supporting chunk IDs per golden question.
- Report metrics at the **same *k*** used in production packing (and ± neighbors).
- Use hybrid retrieval ablations (BM25 / dense / both / +rerank) scored by NDCG@k + Recall@k.
- LangSmith RAG tutorial includes a **retrieval relevance** LLM-as-judge when labeled docs are unavailable: https://docs.langchain.com/langsmith/evaluate-rag-tutorial  
- Hamel FAQ: use **traditional search metrics for retrieval**; don’t replace them entirely with LLM judges.

### Concrete Scenario (URL)

LangSmith “Evaluate a RAG application” tutorial — dataset → run → retrieval relevance + groundedness + answer relevance + correctness:  
https://docs.langchain.com/langsmith/evaluate-rag-tutorial  

Azure Document Retrieval metrics (NDCG, fidelity, holes):  
https://learn.microsoft.com/en-us/azure/foundry/concepts/evaluation-evaluators/rag-evaluators  

### Open Questions

- How to define chunk relevance for questions requiring synthesis across *n* chunks (credit partial sets)?
- Should ACL-filtered docs count as relevant-but-inaccessible in recall denominators?
- Best labeling UX for graded chunk relevance at startup scale (<100 queries)?

### Sources

- RAGAS Context Precision: https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_precision/  
- Azure RAG evaluators: https://learn.microsoft.com/en-us/azure/foundry/concepts/evaluation-evaluators/rag-evaluators  
- NVIDIA NeMo RAG metrics: https://docs.nvidia.com/nemo/microservices/latest/evaluate/flows/rag.html  
- LangSmith RAG eval tutorial: https://docs.langchain.com/langsmith/evaluate-rag-tutorial  
- Hamel Husain evals FAQ (RAG section): https://hamel.dev/blog/posts/evals-faq/index.html  
- Jason Liu six evals (Tier‑1 IR): https://jxnl.co/writing/2025/05/19/there-are-only-6-rag-evals/  

---

## Concept 2 — Generation Metrics (Groundedness, Answer Relevance, Context Precision — RAGAS Triad)

### Fundamentals

The **RAG triad** (also called TruEra triad / Jason Liu Tier‑2) evaluates the three edges of Q–C–A:

| Edge | Metric family | Question answered |
| --- | --- | --- |
| **C \| Q** | Context relevance / Context precision | Are retrieved chunks pertinent—and ranked well? |
| **A \| C** | Groundedness / Faithfulness | Are answer claims supported by retrieved context? |
| **A \| Q** | Answer / Response relevancy | Does the answer address the user question? |

**RAGAS implementations (canonical formulas from docs):**

1. **Faithfulness (groundedness)**  
   - Decompose answer into claims.  
   - Check each claim against `retrieved_contexts`.  
   - \(\text{Faithfulness} = \frac{\#\text{ supported claims}}{\#\text{ claims}}\).  
   - Reference-free (needs contexts + response). Optional HHEM classifier for the support step.

2. **Answer Relevancy (Response Relevancy)**  
   - LLM generates *N* artificial questions from the response (default 3).  
   - Embed those questions and the original user input; average cosine similarity.  
   - Penalizes incomplete or padded answers; **does not** check factual accuracy.

3. **Context Precision**  
   - Rank-aware score over retrieved list: rewards relevant chunks appearing early.  
   - Variants: with reference answer, without reference (vs generated response = Context Utilization), non-LLM / ID-based.

**Related but distinct:**

- **Context Recall** (RAGAS): fraction of reference-answer statements attributable to retrieved contexts — **needs ground-truth answer**; detects retrieval misses.
- **Azure Groundedness** (1–5 LLM judge) + **Relevance** + **Response Completeness** (recall vs expected answer).
- **Databricks** judges: `RetrievalGroundedness`, `RelevanceToQuery`, `RetrievalRelevance` (chunk precision), `RetrievalSufficiency` / context sufficiency.
- **NVIDIA** metrics: `rag_faithfulness`, `rag_answer_relevancy`, `rag_response_groundedness`, `rag_context_relevance`, etc.

Jason Liu’s Tier‑3 adds: context support coverage (C|A), question answerability (Q|C), self-containment (Q|A).

### Alternatives & Tradeoffs

| Approach | Pros | Cons |
| --- | --- | --- |
| Reference-free triad (faithfulness + relevancy + context util.) | Runs on production logs | Can score a “faithful wrong answer” highly if retrieval was wrong but model stuck to it |
| Reference-based (correctness, context recall) | Ties to business truth | Label cost; answers go stale as corpus drifts |
| Single LLM rubric “overall quality” | Fast | Confounds failure modes; weak debugging |
| Vendor judges (Azure/Databricks) | Integrated tracing, pass/fail UX | Less portable; still need human calibration |
| Lexical overlap (BLEU/ROUGE) | Cheap | Poor for paraphrase; discouraged as sole RAG metric |

**Critical tradeoff:** Faithfulness ≠ Correctness. An answer can be fully grounded in a wrong/outdated chunk.

Hamel’s rule: **validate LLM judges against human labels** (estimate TPR/TNR; correct base rates). Off-the-shelf judge prompts are a starting point, not truth.

### Necessity

Generation metrics are required because:

- High Recall@k can still yield hallucinations (FP4).  
- Low answer relevancy catches evasive or off-topic generations even when context is fine.  
- Context precision explains “lost in the middle / noise” regressions when *k* increases.

Together they localize failures to retrieval vs generation ownership.

### Industry Practice

- Ship a **minimum dashboard**: Faithfulness, Answer Relevancy, Context Precision/Recall (or vendor equivalents).  
- Use **binary pass/fail with rationale** (Databricks style) for triage; keep continuous scores for offline tuning.  
- Separate **online monitoring** (sample traffic, reference-free) from **offline golden** (reference-based correctness).  
- LangSmith tutorial wires correctness, groundedness, relevance, retrieval_relevance as parallel evaluators.  
- Prefer **code-based checks** when possible (schema, citation ID ∈ retrieved set, JSON validity) before LLM judges (Hamel/Shreya talks).

### Concrete Scenario (URL)

RAGAS Answer Relevancy calculation docs:  
https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/answer_relevance/  

RAGAS Faithfulness:  
https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/faithfulness/  

RAGAS Context Precision:  
https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_precision/  

Databricks blog — what agent evaluation is (component + E2E, judges):  
https://www.databricks.com/blog/what-is-agent-evaluation  

### Open Questions

- How much judge–human agreement is “enough” before gating releases?  
- Can smaller specialized NLI models replace LLM faithfulness judges in CI for cost?  
- Should triad scores be aggregated, or always reported disaggregated for debugging?

### Sources

- RAGAS metrics docs (above URLs)  
- Jason Liu: https://jxnl.co/writing/2025/05/19/there-are-only-6-rag-evals/  
- Azure RAG evaluators: https://learn.microsoft.com/en-us/azure/foundry/concepts/evaluation-evaluators/rag-evaluators  
- Databricks Agent Evaluation API (judges): https://api-docs.databricks.com/python/databricks-agents/latest/databricks_agent_eval.html  
- MLflow GenAI evaluation: https://mlflow.org/docs/latest/genai/eval-monitor/  
- Hamel FAQ: https://hamel.dev/blog/posts/evals-faq/index.html  

---

## Concept 3 — Building a Golden Set from Real Usage

### Fundamentals

A **golden set** (eval dataset) is a versioned collection of:

- `user_input` / query  
- optional `retrieved_contexts` snapshots or reproducible retrieval traces  
- `response` (system under test) and/or `reference` / `expected_facts`  
- labels for retrieval qrels and failure-mode tags  
- metadata: persona, time, locale, product surface, corpus version  

**Hamel Husain / Shreya Shankar orthodoxy:**

1. **Error analysis first** — use the product; sample traces; open-code failure modes.  
2. Don’t start from “generate 100 diverse queries” unstructured — outputs look diverse but test one behavior repeatedly.  
3. **Structured synthetic data** (when needed): define **dimensions** (persona, complexity, answerability, multi-hop, …) → form **tuples** → LLM realizes natural-language queries from tuples.  
4. Synthetic is a **bootstrap**; replace/augment with **production queries** as they accumulate.  
5. Hand-label a small anchor (often cited: on the order of tens to low hundreds of carefully reviewed items) before scaling judges.

**RAGAS / synthetic pipelines** often generate factual, multi-hop, and **unanswerable** queries from chunks — unanswerables are essential to test refusal (Barnett FP1).

**Databricks** provides synthetic eval generation from documents (`expected_facts`) and dataset management in MLflow GenAI; Agent Evaluation combines per-row judge rationales with aggregate pass rates.

### Alternatives & Tradeoffs

| Source | Pros | Cons |
| --- | --- | --- |
| Production logs + human labels | Real distribution | Privacy; sparse failures; labeling lag |
| Dimension-tuple synthetic | Coverage of rare failures | May invent unreachable combinations |
| Chunk-conditioned synthetic (RAGAS-style) | Grounded in corpus | Skews to single-chunk lookup if unfiltered |
| Expert-authored exams | High quality | Expensive; may miss slang/typos |
| LLM-as-user simulators | Scale | Mode collapse; needs filters/dedup |

Filter funnel pattern (practitioner cookbooks): synthesize → MinHash dedup → binary judge filter → expert keep/kill → pin manifest with content hash.

### Necessity

Without a golden set pinned to **corpus + pipeline versions**, you cannot detect regressions from prompt, embedding, or chunker changes. Barnett: offline eval assumes labeled Q/A that often **don’t exist** at build time — so golden-set construction *is* the enabling SE practice for RAG.

### Industry Practice

- Store datasets in LangSmith / MLflow evaluation datasets / plain versioned JSONL with SHA of corpus snapshot.  
- Include **explicit unanswerable** and **ACL-denied** cases.  
- Tag each row with hypothesized failure mode for stratified metrics.  
- Refresh policy: continuous sample of production + periodic expert review; retire items when docs are deleted (or mark superseded).  
- For judges: collect human pass/fail on the same rows; measure judge agreement before CI gating (Hamel).  
- YouTube: Hamel Husain & Shreya Shankar — *Why AI evals are the hottest new skill for product builders*: https://www.youtube.com/watch?v=BsWxPI9UM4c  

### Concrete Scenario (URL)

Hamel — best approach for generating synthetic data (dimensions → tuples → queries):  
https://hamel.dev/blog/posts/evals-faq/what-is-the-best-approach-for-generating-synthetic-data.html  

Hamel AI Evals FAQ hub (includes “How should I approach evaluating my RAG system?”):  
https://hamel.dev/blog/posts/evals-faq/index.html  

LangSmith dataset creation within RAG eval tutorial:  
https://docs.langchain.com/langsmith/evaluate-rag-tutorial  

### Open Questions

- Optimal mix: % production vs synthetic vs expert for regulated domains?  
- How to golden-set **multi-turn** RAG (anaphora, follow-ups) without exponential labeling cost?  
- When should expected output be full answer vs `expected_facts` list (Databricks pattern)?

### Sources

- https://hamel.dev/blog/posts/evals-faq/index.html  
- https://hamel.dev/blog/posts/evals-faq/what-is-the-best-approach-for-generating-synthetic-data.html  
- https://www.youtube.com/watch?v=BsWxPI9UM4c  
- https://docs.langchain.com/langsmith/evaluate-rag-tutorial  
- https://www.databricks.com/blog/what-is-agent-evaluation  
- https://mlflow.org/docs/latest/genai/eval-monitor/  
- Barnett et al. on test data scarcity: https://arxiv.org/abs/2401.05856  

---

## Concept 4 — Component-Level vs End-to-End Eval

### Fundamentals

| Level | What is measured | Example metrics | Primary use |
| --- | --- | --- | --- |
| **Component — retrieval** | Quality of candidate sets independent of wording of final answer | P@k, R@k, MRR, NDCG, context precision/recall, chunk relevance | Tune embeddings, *k*, hybrid weights, rerankers |
| **Component — generation** | Reader behavior given **fixed** contexts | Faithfulness, format adherence, citation validity, completeness on frozen contexts | Tune prompts, models, decoding; A/B generators fairly |
| **End-to-end (system)** | User-visible outcome of full pipeline | Correctness vs reference, task success, groundedness on live retrieval, latency/cost | Release gates, product KPIs |
| **Trace / agent-level** | Multi-step tool/retrieve paths | Databricks/MLflow trace scorers, tool-call correctness | Debug agents, not single-shot RAG |

**Isolation technique:** cache retrieval outputs (`cached_outputs` in NVIDIA NeMo; stored traces in MLflow) so generation metrics can iterate **without** re-retrieving — and conversely, swap retrievers while keeping a frozen judge harness.

Databricks explicitly recommends hybrid evaluation: component checks (retrieval relevance, parameter formatting) **plus** end-to-end success; failing rows get a **root-cause judge**.

RAGAS positions faithfulness/answer relevancy/context precision-recall as **component-wise** metrics that still roll up to system quality.

Barnett lesson: many performance characteristics are only visible **at runtime** with live users — E2E online eval complements offline components.

### Alternatives & Tradeoffs

| Strategy | Pros | Cons |
| --- | --- | --- |
| E2E-only | Matches user experience | Confounded; slow attribution; expensive labels |
| Component-only | Fast debugging loops | Can over-optimize a stage that doesn’t move E2E |
| Frozen-context generation harness | Fair LLM comparisons | Misses retrieval–generation interactions (noise sensitivity) |
| Online shadow eval | Real traffic | Risk, privacy, judge cost |
| Single “quality” score | Exec-friendly | Hides regressions |

Noise-sensitivity metrics (RAGAS / NVIDIA) specifically measure generation robustness when retrieval is imperfect — a bridge between component and E2E.

### Necessity

Curriculum and production both need **both** levels:

- Component metrics answer “what to fix.”  
- E2E metrics answer “did the fix matter?”  

Release processes that gate only on faithfulness can ship a retriever regression; gating only on answer correctness can hide rising hallucination rates masked by parametric knowledge.

### Industry Practice

- **CI:** retrieval unit tests on pinned qrels + prompt regression on frozen contexts.  
- **Pre-release:** full golden E2E with reference correctness + triad.  
- **Production:** sampled online triad + user feedback; periodic human review sessions (Hamel error analysis).  
- **Tooling matrix:** LangSmith experiments, MLflow/`mlflow.genai.evaluate`, Azure AI Evaluation `evaluate()`, RAGAS `evaluate()`, NeMo Evaluator flows.  
- Databricks: migrate Agent Evaluation judges into MLflow 3 scorers (`RetrievalGroundedness`, `Correctness`, guidelines, custom `@scorer`).  
- Prefer deterministic scorers for citations-present, JSON schema, refusals; LLM judges for fuzzy quality.

### Concrete Scenario (URL)

NVIDIA NeMo — evaluate retrieval alone vs retrieval+generation vs answer-only on cached outputs:  
https://docs.nvidia.com/nemo/microservices/latest/evaluate/flows/rag.html  

Databricks — Agent Evaluation overview (offline + online, root-cause judges):  
https://www.databricks.com/blog/what-is-agent-evaluation  

LangSmith RAG tutorial running multiple evaluators in one experiment:  
https://docs.langchain.com/langsmith/evaluate-rag-tutorial  

YouTube talk operationalizing eval loops:  
https://www.youtube.com/watch?v=BsWxPI9UM4c  

### Open Questions

- How to budget eval spend across component CI vs weekly E2E vs online sampling?  
- When an agent has multiple retrieve calls, which span is “the context” for groundedness?  
- Can automated root-cause classifiers reliably map E2E fails → Barnett FPs?

### Sources

- https://docs.ragas.io/en/v0.1.21/concepts/metrics/ (component-wise framing)  
- https://docs.langchain.com/langsmith/evaluate-rag-tutorial  
- https://www.databricks.com/blog/what-is-agent-evaluation  
- https://docs.databricks.com/aws/en/mlflow3/genai/agent-eval-migration  
- https://docs.nvidia.com/nemo/microservices/latest/evaluate/flows/rag.html  
- https://learn.microsoft.com/en-us/azure/foundry/concepts/evaluation-evaluators/rag-evaluators  
- https://hamel.dev/blog/posts/evals-faq/index.html  
- https://jxnl.co/writing/2025/05/19/there-are-only-6-rag-evals/  

---

## Practical Metric Wiring Map (Debugging Curriculum)

| Failure mode (Week 09) | Component metric | E2E metric |
| --- | --- | --- |
| Recall failure | Recall@k, Context Recall, Retrieval Sufficiency | Correctness ↓, often Faithfulness ambiguous |
| Ranking / assembly failure | NDCG, MRR, Context Precision, chunk relevance | Correctness ↓ with Faithfulness ↓ or noise sensitivity ↑ |
| Generation-grounding failure | Faithfulness / Groundedness on **frozen** good contexts | Faithfulness ↓, Completeness ↓, Citation verification fail |
| Corpus drift | Freshness SLOs + Recall@k on time-sensitive slice | Correctness vs world ↓ while Faithfulness stays high |

---

## Master Source List (Week 10)

1. https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/faithfulness/  
2. https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/answer_relevance/  
3. https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_precision/  
4. https://docs.langchain.com/langsmith/evaluate-rag-tutorial  
5. https://learn.microsoft.com/en-us/azure/foundry/concepts/evaluation-evaluators/rag-evaluators  
6. https://www.databricks.com/blog/what-is-agent-evaluation  
7. https://www.databricks.com/blog/building-custom-llm-judges-ai-agent-accuracy  
8. https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/concepts/judges/is_grounded  
9. https://api-docs.databricks.com/python/databricks-agents/latest/databricks_agent_eval.html  
10. https://mlflow.org/docs/latest/genai/eval-monitor/  
11. https://docs.nvidia.com/nemo/microservices/latest/evaluate/flows/rag.html  
12. https://hamel.dev/blog/posts/evals-faq/index.html  
13. https://hamel.dev/blog/posts/evals-faq/what-is-the-best-approach-for-generating-synthetic-data.html  
14. https://jxnl.co/writing/2025/05/19/there-are-only-6-rag-evals/  
15. https://www.youtube.com/watch?v=BsWxPI9UM4c — Hamel Husain & Shreya Shankar evals talk  
16. https://arxiv.org/abs/2401.05856 — Seven Failure Points (eval implications)  
