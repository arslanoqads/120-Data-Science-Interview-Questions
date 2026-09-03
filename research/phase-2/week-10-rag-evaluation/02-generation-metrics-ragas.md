# 02 — Generation metrics (RAGAS triad: groundedness, answer relevance, context precision)

> Week 10 concept research (deep). Legal sources only.

---

## Fundamentals

The **RAG triad** (TruEra triad / Jason Liu **Tier 2**) evaluates the three edges of Question–Context–Answer:

| Edge | Metric family | Question answered |
| --- | --- | --- |
| **C \| Q** | Context relevance / Context precision | Are retrieved chunks pertinent — and ranked well? |
| **A \| C** | Groundedness / Faithfulness | Are answer claims supported by retrieved context? |
| **A \| Q** | Answer / Response relevancy | Does the answer address the user question? |

Jason Liu Tier 3 adds: **C\|A** (context support coverage), **Q\|C** (question answerability from C), **Q\|A** (self-containment). Hamel: implement Tier 2/3 with **validated** judges, not off-the-shelf prompts; plus **domain** metrics found only in error analysis (adult vs pediatric dose; jurisdiction).

Azure maps the triad onto **system** evaluators: Groundedness (precision of response vs context), Relevance (addresses the query), Response Completeness (recall vs expected answer). Their wording: **Groundedness = precision** (no content outside grounding context); **Completeness = recall** vs ground truth — Week 9 FP4 vs FP7 in metric clothing.

### RAGAS Faithfulness (groundedness)

Docs: measures how factually consistent `response` is with `retrieved_contexts` (0–1). A response is faithful if **all claims** can be supported by retrieved context.

1. Identify claims in the response.  
2. Check each claim against retrieved context.  
3. \(\text{Faithfulness} = \frac{\#\text{ supported claims}}{\#\text{ claims}}\).

Worked example (docs): Q “Where and when was Einstein born?” Context: born 14 March 1879, German-born. Low-faithfulness answer adds **20 March**. Claims: (1) born in Germany — yes; (2) 20 March — no → **0.5**.

**Reference-free** (needs contexts + response, not a gold answer). Optional **FaithfulnesswithHHEM**: Vectara HHEM-2.1-Open (T5 classifier) for the support step — small, open, CPU-default batch 10; useful in CI cost/latency.

NVIDIA: `faithfulness` / `rag_faithfulness` (user_input, response, retrieved_contexts) and `response_groundedness` (response, retrieved_contexts). Separate `noise_sensitivity` measures robustness to noisy context (needs reference too).

**Critical:** Faithfulness ≠ Correctness. An answer can be fully grounded in a **wrong or stale** chunk (Week 9 drift). High faithfulness + Recall@k = 0 is a **retrieval** bug.

### RAGAS Answer Relevancy (Response Relevancy)

Docs title both **Answer Relevancy** and **Response Relevancy**. Measures how relevant `response` is to `user_input` (typically ~0–1; **not guaranteed** because cosine ∈ [−1, 1]). Focus: intent match; **does not** check factual accuracy. Penalizes incomplete or padded answers.

1. Generate *N* artificial questions from the response (default **3**, `strictness`).  
2. Embed those questions and the original user input.  
3. Average cosine similarity:

\[
\text{Answer Relevancy} = \frac{1}{N} \sum_{i=1}^{N} \frac{E_{g_i} \cdot E_o}{\|E_{g_i}\| \|E_o\|}
\]

Worked idea (docs): Q “Where is France and what is its capital?” Low relevance: “France is in western Europe” (reconstructed questions omit capital). High relevance includes Paris. Intuition: if the answer addresses the question, you can **reconstruct** the question from the answer (related to Jason Liu **Q\|A**).

Requires **judge LLM + embeddings** (NeMo: `response_relevancy` needs `embeddings_model`). LangSmith tutorial **relevance** evaluator is a sibling: LLM binary “does the answer address the question,” not reverse-question cosine.

### RAGAS Context Precision

See also file 01. Rank-aware retrieval metric living in the triad because **packed order** is a generation input. Variants: with reference, without (Context Utilization vs generated response), non-LLM, ID-based.

**Do not** treat Context Precision as groundedness. It can be high while the answer fabricates (A\|C fails) or low while the one gold chunk at rank 1 still supports a faithful short answer.

### Related generation / system metrics

| Instrument | What it adds |
| --- | --- |
| **RAGAS Context Recall** | Reference claims covered by C — retrieval miss detector; **needs gold answer** |
| **Azure Groundedness** | 1–5 LLM judge; Pass/Fail vs threshold (default 3); optional query for better scoring; agent mode can pull context from tool results |
| **Azure Groundedness Pro** | Azure AI Content Safety; strict True/False consistency |
| **Azure Relevance** | 1–5 accuracy/completeness/directness vs query; no ground truth required |
| **Azure Response Completeness** | 1–5 vs `ground_truth` — recall of expected information |
| **Databricks / MLflow** | `RetrievalGroundedness` (trace RETRIEVER span — **not** a later re-fetch), `RelevanceToQuery`, `RetrievalRelevance`, sufficiency judges; binary pass/fail + rationale |
| **LangSmith tutorial** | `correctness` (vs ground truth), `groundedness`, `relevance`, `retrieval_relevance` — four parallel evaluators |
| **NeMo** | `context_relevance`, `context_entity_recall`, `noise_sensitivity` in addition to faithfulness / relevancy |

LangSmith correctness instructions (tutorial): teacher grading quiz — QUESTION + GROUND TRUTH + STUDENT ANSWER → boolean. That is **E2E truth**, not A\|C.

---

## Alternatives & Tradeoffs

| Approach | Pros | Cons |
| --- | --- | --- |
| Reference-free triad (faithfulness + relevancy + context utilization) | Runs on production logs | “Faithful wrong answer” scores high if retrieval was wrong but the model stuck to it |
| Reference-based (correctness, context recall, completeness) | Ties to business truth | Label cost; answers go stale as corpus drifts |
| Single LLM rubric “overall quality” | Fast | Confounds failure modes; weak debugging (Hamel: don’t start from platform defaults) |
| Vendor judges (Azure / Databricks) | Tracing, pass/fail UX, span-grounded context | Less portable; still need human calibration |
| HHEM / NLI instead of LLM faithfulness | Cheap, stable CI | May miss nuanced support; still not correctness |
| Lexical overlap (BLEU/ROUGE) | Deterministic | Poor for paraphrase; discouraged as sole RAG metric |
| Continuous scores vs binary pass/fail | Tuning vs triage | Databricks-style binary is better for on-call; keep floats offline |

**Aggregation trap:** averaging triad into one “RAGAS score” hides opposing moves (k↑ → context recall↑, faithfulness↓). **Always report disaggregated.**

Hamel’s rule: **validate LLM judges against human labels** (estimate TPR/TNR; correct base rates). Off-the-shelf RAGAS/LangSmith/Azure prompts are a **starting point**, not truth. Once you know TPR/TNR you can invert observed fail rates to estimate true fail rates.

---

## Necessity

Generation metrics are required because:

- High Recall@k can still yield **hallucinations** (Barnett FP4) — IR metrics stay green.  
- Low answer relevancy catches **evasive or off-topic** generations when context is fine (FP6 specificity; “France is in Europe” when asked for the capital).  
- Context precision explains **lost-in-the-middle / noise** regressions when *k* increases (Week 8–9).  
- Completeness / context recall vs gold catches **FP7** (partial lists) that faithfulness may pass (every said claim is supported; claims are missing).  
- Code assertions (JSON schema, citation ID ∈ retrieved set) catch **FP5** cheaper than any LLM judge.

Together they localize ownership: retrieval vs prompt/model vs policy (refusal).

If skipped: teams ship a prompt tweak that raises faithfulness on frozen bad context, or an embedding tweak that raises recall while the reader ignores mid-prompt gold.

---

## Industry Practice

- Ship a **minimum dashboard**: Faithfulness, Answer Relevancy, Context Precision **and** Context Recall or ID Recall@k; plus reference correctness on the golden slice.  
- Use **binary pass/fail with rationale** (Databricks / Azure `passed` + `reason`) for triage; keep continuous scores for offline tuning and *k* sweeps.  
- Separate **online monitoring** (sample traffic, reference-free triad) from **offline golden** (reference-based correctness + completeness).  
- LangSmith: wire four evaluators in **one** experiment so a row shows which edge failed.  
- Prefer **code-based checks** first (schema, citation ∈ retrieved IDs, refusal regex, JSON validity) — Hamel/Shreya talks — then LLM judges for fuzzy quality.  
- Databricks: migrate Agent Evaluation judges into MLflow 3 scorers (`RetrievalGroundedness`, `Correctness`, guidelines, custom `@scorer`). Groundedness must read the **trace’s retrieved context**.  
- Azure: for best Groundedness, provide **query + response + context**; concatenate multi-chunk context with `\n\n`.  
- NeMo: offline jobs use pre-generated `response`; online jobs generate via `prompt_template` then score RAGAS metrics.  
- RAGAS collections API (`Faithfulness`, `AnswerRelevancy`, `ContextPrecision`) is recommended; legacy `SingleTurnSample` API deprecated toward 0.4 / removed 1.0.

**Common:** one 1–5 “quality” score.  
**Strong:** triad + correctness, disaggregated, with judge rationales in the row.  
**FDE:** state faithfulness formula; distinguish Azure precision/recall (groundedness vs completeness) from IR P@k/R@k; never gate release on faithfulness alone.

---

## Concrete Scenario

**Same Einstein-shaped bug in a runbook bot.** Retrieved context: “Restart the **search** daemon after changing `http.port`.” Answer: “Restart the **ingest** daemon after changing `http.port`.”

| Metric | Score shape | Debug |
| --- | --- | --- |
| Faithfulness | ~0.5 (one claim unsupported) | FP4 / A\|C — if gold was packed |
| Answer relevancy | High (reconstructed Q still about restart/port) | Does **not** catch the wrong daemon |
| Context precision | High if the search-daemon chunk is rank 1 | Retrieval looks fine |
| Correctness vs gold | Fail | E2E catch |
| Completeness | May pass if gold answer was only one sentence | Don’t use completeness as faithfulness |

**LangSmith tutorial bot** (Lilian Weng posts, RecursiveCharacterTextSplitter chunk 250, retriever k=6): correctness vs authored gold; groundedness vs retrieved docs; relevance vs question; retrieval_relevance vs docs. URL: https://docs.langchain.com/langsmith/evaluate-rag-tutorial

RAGAS calculation docs:

- Faithfulness: https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/faithfulness/  
- Answer Relevancy: https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/answer_relevance/  
- Context Precision: https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_precision/  

Databricks component + E2E + root cause: https://www.databricks.com/blog/what-is-agent-evaluation  

---

## Open Questions

- How much judge–human agreement is “enough” before **gating** releases (TPR/TNR thresholds)?  
- Can HHEM / smaller NLI replace LLM faithfulness judges in CI for cost, with LLM judges only on disagreements?  
- Should triad scores ever be aggregated for exec dashboards, or always a small multiples chart?  
- Claim granularity: who splits “Einstein was born in Germany on 20 March” into two claims — the metric implementation. Different RAGAS versions / prompts change scores. Pin **metric version**.  
- Agent traces: Azure notes context can be extracted from tool calls — which span is C for A\|C when there were three retrieves?

---

## Sources

- RAGAS Faithfulness: https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/faithfulness/  
- RAGAS Answer Relevancy: https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/answer_relevance/  
- RAGAS Context Precision: https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_precision/  
- RAGAS Context Recall: https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_recall/  
- Jason Liu: https://jxnl.co/writing/2025/05/19/there-are-only-6-rag-evals/  
- Azure RAG evaluators: https://learn.microsoft.com/en-us/azure/foundry/concepts/evaluation-evaluators/rag-evaluators  
- Databricks Agent Evaluation: https://www.databricks.com/blog/what-is-agent-evaluation  
- Databricks `is_grounded` / RetrievalGroundedness: https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/concepts/judges/is_grounded  
- Databricks agents Python API: https://api-docs.databricks.com/python/databricks-agents/latest/databricks_agent_eval.html  
- MLflow GenAI eval-monitor: https://mlflow.org/docs/latest/genai/eval-monitor/  
- NVIDIA RAG metrics: https://docs.nvidia.com/nemo/microservices/26.3.0/evaluator/metrics/rag.html  
- LangSmith RAG tutorial: https://docs.langchain.com/langsmith/evaluate-rag-tutorial  
- Hamel FAQ: https://hamel.dev/blog/posts/evals-faq/index.html  
- Hamel RAG: https://hamel.dev/blog/posts/evals-faq/how-should-i-approach-evaluating-my-rag-system.html  
