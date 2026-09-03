# Chapter 10 — RAG evaluation

> **Phase 2 — RAG Systems**  
> **Editorial status:** COMPLETE  
> **Source of truth:** `research/phase-2/week-10-rag-evaluation/`  
> **Syllabus Build:** On the **same** Week 7–9 logged stack (do **not** swap retrievers this week): (1) pin a **golden set** (queries + gold `chunk_id`s / `expected_facts` + unanswerable slice) to `corpus_hash` + `pipeline_version`; (2) stand up a **RAGAS-style harness** (or LangSmith / Azure `evaluate()` / NeMo RAG flow / MLflow scorers — one primary, others as mapping tables); (3) score **retrieval** at production packed *k* and at `fetch_k` (Recall@k, P@k, MRR, NDCG); (4) score **generation** (faithfulness / answer relevancy / context precision; plus reference correctness on the golden slice); (5) produce a **before/after table** vs Weeks 7–9 ablations (cosine-only → hybrid → +rerank → taxonomy-informed packing). That table is the interview artifact.

---

## Prerequisites Recap

Before this week you should already have from Week 9:

- **Three canonical failure modes** — recall / ranking-assembly / generation-grounding — with Barnett FP1–7 as subtypes and the Jason Liu Q–C–A relationship that failed.  
- A **portfolio debugging log** joined on `retrieval_id` from Weeks 7–8, with taxonomy labels, evidence snapshots, and injection-cell notes so stage-1 miss, packing miss, and generate-ignore stay separable.  
- A **classification habit**: ask eligibility → packing survival → reader use **in order**; treat “I don’t know” as success on FP1 and a bug when gold existed but was missed.  
- Fault-injection cells exercised on the same Week 7–8 stack (missing gold; gold below *k*; consolidator drop; noisy packed window; stale version; mid-prompt gold) — labels, not a new retriever.

You do **not** need a pinned golden set, RAGAS/LangSmith harness, or a numbered before/after metric table yet. That is what this week teaches.

---

## What this week builds

Week 9 **named** failures (recall / ranking / generation-grounding; Barnett FP1–7; Jason Liu Q–C–A) and shipped a classified debugging log. Week 10 is the **measurement** week of Phase 2 RAG: **quantify** those names so a change to embeddings, *k*, reranker, or prompt has a before/after that can be repeated in CI and told in an interview. Weeks 6–8 already built chunks, hybrid candidates, and a reranked packed window — do not swap them.

The syllabus spine is a **RAGAS-style harness**, not a new retriever:

| Layer | Question | Default instruments |
| --- | --- | --- |
| **Retrieval (component)** | Did the right chunks enter the packed window, in a useful order? | P@k, R@k, MRR, NDCG@k; RAGAS Context Precision / Recall; Azure Document Retrieval; NeMo `pytrec_eval` |
| **Generation (component)** | Given those chunks, did the reader stay faithful and on-question? | RAGAS Faithfulness + Answer Relevancy; Azure Groundedness / Relevance / Completeness; Databricks `RetrievalGroundedness` |
| **System (E2E)** | Did the user-visible answer match business truth? | Reference correctness (LangSmith); task success; latency/cost |
| **Dataset** | Can we re-run this next week on the same world? | Versioned golden set + corpus hash + pipeline version |

**RAGAS** (docs.ragas.io) is the open vocabulary: Faithfulness = supported claims / claims; Answer Relevancy = mean cosine of reverse-engineered questions vs the user input; Context Precision = rank-aware mean of Precision@k at relevant ranks. NVIDIA NeMo’s RAG flow **embeds the same split**: `retriever_recall_k` / `retriever_ndcg_cut_k` via **pytrec_eval**, and `rag_faithfulness` / `rag_answer_relevancy` via **ragas**. Azure Foundry splits **process** (Document Retrieval, Retrieval LLM-judge) from **system** (Groundedness, Relevance, Response Completeness). LangSmith’s RAG tutorial runs **correctness, groundedness, relevance, retrieval_relevance** as parallel evaluators on one dataset.

Hamel Husain & Shreya Shankar (hamel.dev evals FAQ): retrieval is a **search problem** — use IR metrics. Generation uses **error analysis → human labels → targeted judges → TPR/TNR**. Jason Liu (*There Are Only 6 RAG Evals*, 2025-05-19) is the relationship graph (Q, C, A); Hamel’s RAG FAQ maps it onto ops: **Tier 1 IR first**.

Barnett et al. (arXiv:2401.05856): **validation is only feasible in operation** because labelled Q/A often do not exist at index time. Week 10’s golden set is therefore an **engineering artifact you build**, not a download. Week 9’s debugging log is the labelling bootstrap.

**This week’s artifact is a numbered before/after table**, joined on the same queries and `pipeline_version`s as Weeks 7–9 — not a screenshot of a vendor dashboard.

Do not start Week 10 by regenerating the index. If gold is absent from `fetch_k`, that is **Recall@k = 0** — faithfulness of the answer is not a retriever score. Do not skip this week for “we’ll just look at chat.” E2E accuracy **confounds** recall, rank, and grounding. Hamel: **debug retrieval with IR metrics first**, then generation with **judges validated against humans**.

Read the concepts in order. Each section’s **Worked Example** and **Apply It** assume the same flagship service (working title: Deployment Copilot) on the Weeks 6–9 runbook/FAQ stack — hybrid candidates, rerank ids, packed positions, Week 9 failure tags — with metrics **appended**, not swapped in for a new architecture.

**Default path (synthesis):**

1. Join Week 9 debugging log on `retrieval_id`. Convert labels into **stratified slices** (recall / rank / ground / unanswerable / lexical-precision).  
2. Prefer **ID-based** retrieval metrics when qrels exist; use LLM retrieval-relevance only when labels are missing — then calibrate.  
3. Freeze packed contexts for generator A/B; freeze generator for retriever A/B.  
4. Report metrics **disaggregated** (never a single “quality” number as the deliverable).  
5. Interview story = **numbers + owner + next lever**, not “we added RAGAS.”

**Week 9 failure → Week 10 metric map:**

| Failure mode (Week 9) | Component metric | E2E metric |
| --- | --- | --- |
| Recall failure (FP1/FP2 miss) | Recall@k, Context Recall, Azure Fidelity, Retrieval Sufficiency | Correctness ↓; Faithfulness **do not use** as retriever debug |
| Ranking / assembly (FP2 near-miss, FP3, LITM) | NDCG, MRR, Context Precision, P@k | Correctness ↓; noise sensitivity / faithfulness may move |
| Generation-grounding (FP4–7) | Faithfulness on **frozen good C**; completeness; citation ∈ retrieved IDs | Faithfulness ↓, Completeness ↓, format assertions fail |
| Corpus drift | Recall@k on time-sensitive slice; `content_hash` mismatch | Correctness vs world ↓ while Faithfulness stays high |

---

### Retrieval metrics (P@k, R@k, MRR, NDCG)

* **Fundamentals:**  
  Treat the retriever as a classical IR system. For each query *q*, the pipeline returns an **ordered** list *D₁ … Dₖ*. Labels (**qrels**) are binary or graded relevance of documents/chunks to *q* (or to a gold answer’s supporting passages). Hamel Husain (evals FAQ): the retrieval component is a **search problem**; evaluate it with traditional IR metrics — Recall@k, Precision@k, MRR — **before** LLM judges on generation. Jason Liu’s **Tier 1** is the same cut.

  NVIDIA NeMo’s RAG evaluation flow scores retrieval with **pytrec_eval** (`retriever_recall_k`, `retriever_ndcg_cut_k`, `retriever_P_k`, `retriever_map_cut_k`) and generation separately with **ragas**. Retriever metrics are only computed when a retriever pipeline is actually specified. Azure Foundry **Document Retrieval** is the labelled-qrels process evaluator: composite **Fidelity, NDCG, XDCG, Max Relevance, Holes**.

  Always name **which list** you scored: stage-1 `fetch_k`, fused list, reranked list, or **packed prompt k**. Comparing Recall@40 (Week 7 pool) to Recall@5 (packed) without saying so is a reporting bug.

  | Metric | Definition (operational) | Sensitive to | Typical RAG use |
  | --- | --- | --- | --- |
  | **Precision@k** | (# relevant in top *k*) / *k* | Noise in the packed window | “Are we feeding junk to the LLM?” |
  | **Recall@k** | (# relevant in top *k*) / (# relevant in qrels for *q*) | Misses outside *k* | “Can generation possibly succeed?” — primary recall-failure detector |
  | **MRR** | mean over queries of 1/rank of *first* relevant hit (0 if none) | Single-hit lookup | FAQ / factoid RAG where one chunk suffices |
  | **NDCG@k** | DCG normalized by ideal DCG | Graded relevance + rank | Tuning hybrid weights and rerankers |

  **Formulas (binary relevance unless noted):**

  - \(\mathrm{P@k} = \frac{|\{d \in \mathrm{top\text{-}k} : \mathrm{rel}(d)=1\}|}{k}\)
  - \(\mathrm{R@k} = \frac{|\{d \in \mathrm{top\text{-}k} : \mathrm{rel}(d)=1\}|}{|\{d : \mathrm{rel}(d)=1\}|}\)
  - \(\mathrm{RR} = 1/\min\{i : \mathrm{rel}(D_i)=1\}\) (0 if none); \(\mathrm{MRR} = \mathrm{mean}_q \mathrm{RR}(q)\)
  - \(\mathrm{DCG@k} = \sum_{i=1}^{k} \frac{2^{\mathrm{rel}_i}-1}{\log_2(i+1)}\); \(\mathrm{NDCG@k} = \mathrm{DCG@k}/\mathrm{IDCG@k}\)

  NeMo documents `retriever_recall_k` as “fraction of relevant documents retrieved in the top k”; `retriever_ndcg_cut_k` as NDCG at cutoff k (range 0–1). Cutoffs in their catalog include k ∈ {5, 10, 20, 100} — **your** production *k* may not be in that set; still compute it.

  **RAGAS Context Precision** (rank-aware cousin): assesses whether **relevant chunks are placed at the top**. It is the mean of Precision@k **only at ranks where the chunk is relevant** (\(v_k \in \{0,1\}\)):

  \[
  \mathrm{Context\ Precision@K} = \frac{\sum_{k=1}^{K} (\mathrm{Precision@k} \times v_k)}{\text{number of relevant items in the top } K}
  \]

  Worked shape from RAGAS docs: relevant then irrelevant → score ≈ 1.0; **irrelevant first**, relevant second → score ≈ 0.5. Same set, different order — NDCG/Context Precision move; set-Recall@2 does not.

  Variants: **ContextPrecision** (LLM vs reference answer); **ContextUtilization** (same rank-aware score vs generated response); **NonLLMContextPrecisionWithReference** (RapidFuzz / Levenshtein vs `reference_contexts`); **IDBasedContextPrecision** = |retrieved IDs ∩ reference IDs| / |retrieved IDs| (example: retrieved `{doc_1..4}`, gold `{doc_1, doc_4, doc_5, doc_6}` → **0.5**).

  **Context Recall** (needs a reference): fraction of **reference-answer claims** attributable to retrieved contexts (LLM), or ID-based |gold IDs ∩ retrieved| / |gold IDs|. ID example: retrieved 3 IDs, gold 4, one overlap → **0.25**. Claim-level cousin of Recall@k when you lack chunk qrels but have a gold answer.

  **Azure Document Retrieval composite** requires `retrieval_ground_truth` (human `query_relevance_label` per `document_id`) and `retrieved_documents` (system `relevance_score`):

  | Metric | Azure description |
  | --- | --- |
  | **Fidelity** | Good documents returned / known good in the dataset |
  | **NDCG** | Ranking vs ideal order of relevant items |
  | **XDCG** | Quality of top-k **regardless of scoring of other index documents** |
  | **Max Relevance** | Maximum relevance in the top-k (`top1_relevance`, `top3_max_relevance`) |
  | **Holes** / **holes_ratio** | Documents **missing** query relevance judgments — label sanity, not IR quality |

  Sample output in Microsoft Learn: `ndcg@3` score **0.646** (pass), `fidelity` **0.019** (fail). Teaching point: NDCG can look “ok” while fidelity says you are not covering known-good docs. Azure **Retrieval** (LLM-judge, no qrels): 1–5 relevance of concatenated context; use when labels do not exist — do not replace NDCG once qrels exist (Hamel).

* **The Alternatives:**  

  | Choice | What you gain | What it costs | When it fits |
  |----------|---------------|---------------|--------------|
  | Binary vs graded labels | Simple qrels; cheap labelling | Graded NDCG needs rubrics (Azure 0–4 / 1–5); binary understates “partially useful” | Binary for CI; graded when tuning rerankers |
  | Doc-level vs chunk-level qrels | Doc labels cheaper | Coarse — relevant doc can pack wrong chunk | Prefer chunk labels (prompt unit) |
  | Fixed *k* vs *k* sweeps | Production *k* is honest | Sweeps show recall–noise frontier | Always report production *k*; sweep offline |
  | Exact ID match vs LLM-judged relevance | IDs cheap, reproducible | LLM relevance needs calibration | IDs in CI; LLM when qrels missing |
  | MRR vs Recall@k | MRR for single-hit FAQ | MRR ignores extra supporting chunks (multi-hop / FP7) | MRR secondary for multi-evidence RAG |
  | Set metrics vs rank-aware | Recall@k = 1.0 with gold at rank *k* | NDCG/Context Precision still punish bad order | Always pair Recall with NDCG or Context Precision |
  | Micro vs macro average | Micro weights busy queries | Macro treats each query equally | **Say which** |
  | Azure Fidelity vs Recall@k | Same coverage spirit | Fidelity defined on Azure labelled set + top n | Map in interviews; compute both if on Azure |

  **Proxy trap:** optimizing embedding cosine on a synthetic query set can raise P@k on that set while harming real-user recall (distribution shift). Hamel reverse-generation is a bootstrap, not a substitute for production queries.

  **k trap:** raising *k* monotonically improves Recall@k and usually hurts P@k / context precision. Week 8 rerank exists so you can keep a **small packed k** with high NDCG.

  The syllabus selects **ID-based IR at production packed k and fetch_k** as the default retrieval gate because NeMo, Azure Document Retrieval, and Hamel Tier 1 all treat retrieval as search first.

* **Failure Modes:**  
  - E2E answer accuracy **confounds** retrieval and generation — you cannot tell Week 9 recall failure (gold never eligible) from ranking/assembly (gold below packed k) from grounding (gold packed, unused).  
  - Averaging faithfulness across Recall@k_prod = 0 rows blames the generator (Hamel **absence blindness**).  
  - Without NDCG/MRR/Context Precision you miss Week 8 rerank **working**: gold already in fetch_k, order improved; Recall@fetch_k stays flat — that is ranking success, not a “no-op eval.”  
  - Azure **Holes**: you think you have NDCG but half the retrieved IDs have no labels — metric not comparable across weeks.  
  - Reporting Recall@40 vs Recall@5 as if they were the same metric.  
  - One “retrieval quality” LLM score with *k* unspecified.

* **Average vs. Strong Engineer:**  
  **Average:** one “retrieval quality” LLM score; *k* unspecified; no qrels; gates on a single fluency-adjacent number.  
  **Strong:** TREC-style qrels or gold `chunk_id` lists; pytrec / sklearn / RAGAS ID metrics at **production packed k** and **fetch_k**; lexical vs semantic slices (Week 7); ablate BM25 / dense / hybrid / +rerank with **NDCG@k + Recall@k** on the **same** query set; log `holes` / unlabeled retrieved IDs; prefer ID-based precision/recall in CI, LLM Context Precision for error analysis.  
  **FDE bar:** explain Fidelity vs Recall; XDCG vs NDCG; why MRR is the wrong primary metric for multi-hop; quote NeMo’s split of pytrec vs ragas; always name *k*.

* **Worked Example:**  
  Deployment Copilot query: `ERR_OS_4092` after OpenSearch upgrade (Week 7 lexical slice). Gold chunks: `runbook#os-4092`, `compat-matrix#2.19`.

  | System | Ranked IDs (packed k=5) | P@5 | R@5 | RR | Notes |
  | --- | --- | --- | --- | --- | --- |
  | Cosine-only | 5 semantically “search error” FAQs, neither gold | 0 | 0 | 0 | Recall failure; do not tune prompt |
  | Hybrid RRF | gold at ranks 7 and 12, packed 1–5 miss | 0 | 0 at k=5; R@40=1.0 | 1/7 | Ranking/assembly; Week 8 rerank |
  | + CE rerank | gold at 1 and 3 | 0.4 | 1.0 | 1.0 | NDCG jumps; generation now eligible |

  Azure-shaped labels: gold docs `query_relevance_label` 4–5, near-miss 2. After rerank, `ndcg@3` rises; if you never labelled the near-misses, **holes** stay high and NDCG is noisy. LangSmith tutorial equivalent: dataset → run → `retrieval_relevance` alongside groundedness when labelled docs are unavailable — starting point only.

* **Apply It:**  
  1. Maintain qrels or per-query gold `chunk_id` lists in the golden set (see golden-set section).  
  2. Report Recall@k, P@k, MRR, NDCG@k at **production packed k** and at **fetch_k**.  
  3. Prefer ID-based RAGAS / pytrec metrics in CI; keep LLM retrieval-relevance for bootstrap when labels are missing — then calibrate.  
  4. Ablate cosine / hybrid / +rerank on the **same** query set; never compare Recall@5 to Recall@40 without naming both.  
  5. Log holes / unlabeled retrieved IDs; do not gate on NDCG when `holes_ratio` is high.  
  6. If Recall@k_prod = 0, stop using faithfulness as a retriever debug signal.

---

### Generation metrics / RAGAS triad

* **Fundamentals:**  
  The **RAG triad** (TruEra triad / Jason Liu **Tier 2**) evaluates the three edges of Question–Context–Answer:

  | Edge | Metric family | Question answered |
  | --- | --- | --- |
  | **C \| Q** | Context relevance / Context precision | Are retrieved chunks pertinent — and ranked well? |
  | **A \| C** | Groundedness / Faithfulness | Are answer claims supported by retrieved context? |
  | **A \| Q** | Answer / Response relevancy | Does the answer address the user question? |

  Jason Liu Tier 3 adds: **C\|A** (context support coverage), **Q\|C** (question answerability from C), **Q\|A** (self-containment). Hamel: implement Tier 2/3 with **validated** judges, not off-the-shelf prompts; plus **domain** metrics found only in error analysis (adult vs pediatric dose; jurisdiction).

  Azure maps the triad onto **system** evaluators: Groundedness (precision of response vs context), Relevance (addresses the query), Response Completeness (recall vs expected answer). Their wording: **Groundedness = precision** (no content outside grounding context); **Completeness = recall** vs ground truth — Week 9 FP4 vs FP7 in metric clothing.

  **RAGAS Faithfulness (groundedness):** measures how factually consistent `response` is with `retrieved_contexts` (0–1). A response is faithful if **all claims** can be supported by retrieved context.

  1. Identify claims in the response.  
  2. Check each claim against retrieved context.  
  3. \(\text{Faithfulness} = \frac{\#\text{ supported claims}}{\#\text{ claims}}\).

  Worked example (RAGAS docs): Q “Where and when was Einstein born?” Context: born 14 March 1879, German-born. Low-faithfulness answer adds **20 March**. Claims: (1) born in Germany — yes; (2) 20 March — no → **0.5**.

  **Reference-free** (needs contexts + response, not a gold answer). Optional **FaithfulnesswithHHEM**: Vectara HHEM-2.1-Open (T5 classifier) for the support step — useful in CI cost/latency. NVIDIA: `faithfulness` / `rag_faithfulness` and `response_groundedness`; separate `noise_sensitivity` measures robustness to noisy context (needs reference too).

  **Critical:** Faithfulness ≠ Correctness. An answer can be fully grounded in a **wrong or stale** chunk (Week 9 drift). High faithfulness + Recall@k = 0 is a **retrieval** bug.

  **RAGAS Answer Relevancy (Response Relevancy):** measures how relevant `response` is to `user_input` (typically ~0–1; **not guaranteed** because cosine ∈ [−1, 1]). Focus: intent match; **does not** check factual accuracy. Penalizes incomplete or padded answers.

  1. Generate *N* artificial questions from the response (default **3**, `strictness`).  
  2. Embed those questions and the original user input.  
  3. Average cosine similarity:

  \[
  \text{Answer Relevancy} = \frac{1}{N} \sum_{i=1}^{N} \frac{E_{g_i} \cdot E_o}{\|E_{g_i}\| \|E_o\|}
  \]

  Intuition: if the answer addresses the question, you can **reconstruct** the question from the answer (related to Jason Liu **Q\|A**). Requires **judge LLM + embeddings**. LangSmith tutorial **relevance** is a sibling: LLM binary “does the answer address the question,” not reverse-question cosine.

  **Context Precision** lives in the triad because **packed order** is a generation input — but it is **not** groundedness. It can be high while the answer fabricates (A\|C fails) or low while the one gold chunk at rank 1 still supports a faithful short answer.

  **Related instruments:**

  | Instrument | What it adds |
  | --- | --- |
  | **RAGAS Context Recall** | Reference claims covered by C — retrieval miss detector; **needs gold answer** |
  | **Azure Groundedness** | 1–5 LLM judge; Pass/Fail vs threshold (default 3) |
  | **Azure Groundedness Pro** | Azure AI Content Safety; strict True/False consistency |
  | **Azure Relevance** | 1–5 vs query; no ground truth required |
  | **Azure Response Completeness** | 1–5 vs `ground_truth` — recall of expected information |
  | **Databricks / MLflow** | `RetrievalGroundedness` (trace RETRIEVER span — **not** a later re-fetch), `RelevanceToQuery`, `RetrievalRelevance`; binary pass/fail + rationale |
  | **LangSmith tutorial** | `correctness` (vs ground truth), `groundedness`, `relevance`, `retrieval_relevance` — four parallel evaluators |
  | **NeMo** | `context_relevance`, `context_entity_recall`, `noise_sensitivity` in addition to faithfulness / relevancy |

  LangSmith correctness (tutorial): teacher grading quiz — QUESTION + GROUND TRUTH + STUDENT ANSWER → boolean. That is **E2E truth**, not A\|C.

* **The Alternatives:**  

  | Approach | Pros | Cons |
  | --- | --- | --- |
  | Reference-free triad (faithfulness + relevancy + context utilization) | Runs on production logs | “Faithful wrong answer” scores high if retrieval was wrong but the model stuck to it |
  | Reference-based (correctness, context recall, completeness) | Ties to business truth | Label cost; answers go stale as corpus drifts |
  | Single LLM rubric “overall quality” | Fast | Confounds failure modes; weak debugging (Hamel: don’t start from platform defaults) |
  | Vendor judges (Azure / Databricks) | Tracing, pass/fail UX, span-grounded context | Less portable; still need human calibration |
  | HHEM / NLI instead of LLM faithfulness | Cheap, stable CI | May miss nuanced support; still not correctness |
  | Lexical overlap (BLEU/ROUGE) | Deterministic | Poor for paraphrase; discouraged as sole RAG metric |
  | Continuous scores vs binary pass/fail | Tuning vs triage | Databricks-style binary better for on-call; keep floats offline |

  **Aggregation trap:** averaging triad into one “RAGAS score” hides opposing moves (k↑ → context recall↑, faithfulness↓). **Always report disaggregated.**

  Hamel’s rule: **validate LLM judges against human labels** (estimate TPR/TNR; correct base rates). Off-the-shelf RAGAS/LangSmith/Azure prompts are a **starting point**, not truth. Once you know TPR/TNR you can invert observed fail rates to estimate true fail rates.

  The syllabus selects **disaggregated triad + reference correctness on the golden slice** as the default generation dashboard, with code assertions (schema, citation ∈ retrieved IDs, refusal) before LLM judges.

* **Failure Modes:**  
  - High Recall@k still yields **hallucinations** (Barnett FP4) — IR metrics stay green.  
  - Low answer relevancy catches **evasive or off-topic** generations when context is fine (FP6; “France is in Europe” when asked for the capital) — faithfulness alone misses this.  
  - Completeness / context recall vs gold catches **FP7** (partial lists) that faithfulness may pass (every said claim is supported; claims are missing).  
  - Teams ship a prompt tweak that raises faithfulness on frozen **bad** context, or an embedding tweak that raises recall while the reader ignores mid-prompt gold.  
  - Gating release on faithfulness alone ships a retriever regression (faithful to the wrong C).  
  - Claim-granularity drift across RAGAS versions / prompts — pin **metric version**.

* **Average vs. Strong Engineer:**  
  **Average:** one 1–5 “quality” score; gates on platform-default judges; aggregates triad into a single “RAGAS score.”  
  **Strong:** Faithfulness, Answer Relevancy, Context Precision **and** Context Recall or ID Recall@k; plus reference correctness on the golden slice; binary pass/fail with rationale for triage; continuous scores for offline tuning; code-based checks first (schema, citation ∈ retrieved IDs, refusal regex); LangSmith-style four evaluators on **one** experiment so a row shows which edge failed; Databricks groundedness reads the **trace’s** retrieved context.  
  **FDE bar:** state faithfulness formula; distinguish Azure precision/recall (groundedness vs completeness) from IR P@k/R@k; never gate release on faithfulness alone; state judge–human agreement or that judges are **not** yet gating.

* **Worked Example:**  
  Deployment Copilot Einstein-shaped bug. Retrieved context: “Restart the **search** daemon after changing `http.port`.” Answer: “Restart the **ingest** daemon after changing `http.port`.”

  | Metric | Score shape | Debug |
  | --- | --- | --- |
  | Faithfulness | ~0.5 (one claim unsupported) | FP4 / A\|C — if gold was packed |
  | Answer relevancy | High (reconstructed Q still about restart/port) | Does **not** catch the wrong daemon |
  | Context precision | High if the search-daemon chunk is rank 1 | Retrieval looks fine |
  | Correctness vs gold | Fail | E2E catch |
  | Completeness | May pass if gold answer was only one sentence | Don’t use completeness as faithfulness |

  LangSmith tutorial shape (Lilian Weng posts bot): correctness vs authored gold; groundedness vs retrieved docs; relevance vs question; retrieval_relevance vs docs — four parallel evaluators on one experiment.

* **Apply It:**  
  1. Ship a minimum dashboard: Faithfulness, Answer Relevancy, Context Precision, plus Context Recall or ID Recall@k, plus reference correctness on the golden slice.  
  2. Prefer code assertions first (JSON schema, citation ID ∈ retrieved set, refusal regex) — then LLM judges for fuzzy quality.  
  3. Separate online monitoring (sample traffic, reference-free triad) from offline golden (reference-based correctness + completeness).  
  4. Validate judges against ≥30 human labels before CI gating; report TPR/TNR.  
  5. Never average faithfulness across Recall@k = 0 / FP1 rows into the generator score.  
  6. Pin metric / judge prompt versions; report triad **disaggregated**.

---

### Golden set from usage

* **Fundamentals:**  
  A **golden set** (eval dataset) is a **versioned** collection of rows that let you re-run Week 10 metrics after a chunker, embedding, *k*, reranker, or prompt change. Minimum fields:

  | Field | Role |
  | --- | --- |
  | `user_input` / query | What the system saw (preserve typos, locale, shorthand) |
  | `reference` / `expected_facts` | E2E correctness / Azure completeness / Databricks facts |
  | `gold_chunk_ids[]` / `reference_context_ids` | ID-based P/R, qrels |
  | `retrieved_contexts` snapshot **or** reproducible `retrieval_id` | Frozen-context generation eval; citation checks |
  | `response` (optional, SUT output) | Offline RAGAS without re-generation (NeMo pre-generated answers) |
  | Failure-mode tags | Stratified metrics (Week 9 canonical mode + Barnett FP) |
  | Metadata | persona, time, locale, surface, `corpus_hash`, `pipeline_version`, ACL/tenant |

  Barnett et al. (arXiv:2401.05856): offline methods need labelled Q/A that **often do not exist** when you first index unstructured docs; **validation is feasible in operation**. Golden-set construction is therefore the enabling software-engineering practice for RAG, not a research nicety.

  **Hamel / Shreya orthodoxy:**

  1. **Error analysis first** — use the product; sample traces; open-code failure modes. FAQ: 60–80% of development time on error analysis; review 20–50 outputs on significant changes; a domain “benevolent dictator” as quality owner.  
  2. Do **not** start from “generate 100 diverse queries” with no structure — outputs look diverse but test one behavior repeatedly.  
  3. **Structured synthetic data** when needed: define **dimensions** → form **tuples** → LLM realizes natural-language queries. Write **~20 tuples by hand** first. Example: support bot issue type × mood × prior context.  
  4. Tuple generation: **cross product then filter** (coverage, including edges) vs **direct LLM tuples** (more realistic, misses rare combos).  
  5. Synthetic is a **bootstrap**; compare to **production queries** as soon as they exist. Synthetic **cannot** tell you how common a failure is. Unreliable in high-stakes domains without heavy human review.  
  6. Hand-label a small **anchor** (tens to low hundreds; cite annotating ≥30 traces yourself, then ~100 diverse traces as a discovery pool).  
  7. Re-run error analysis on **100+ fresh traces** on a 2–4 week cadence when the product is live.

  Hamel RAG-specific: evaluate retrieval by **reverse generation** — take corpus documents, extract key facts, generate questions those facts would answer. That yields query–document pairs **without** starting from manual annotation.

  **RAGAS / vendor synthetic:** RAGAS test-data generation typically produces factual, multi-hop, and **unanswerable** queries from chunks. Unanswerables test **refusal** (Barnett FP1) — required Week 9/10 slice. Databricks: golden / benchmark datasets versioned (Unity Catalog lineage); `expected_facts` pattern beats a single full-answer string when many phrasings are valid. Public OfficeQA/MultiDoc QA are research slices, **not** production gates. LangSmith tutorial: questions + expected answers is the **shape**; your set must include **IDs and slices**. NVIDIA: BEIR / SQuAD / RAGAS formats; retrieval metrics need qrels-style relevance.

  **Filter funnel:** synthesize or sample → MinHash / embedding dedup → binary judge or heuristic filter → **expert keep/kill** → pin manifest with **content hash** of corpus + dataset SHA. Do not generate synthetic data for bugs you can fix immediately (Hamel: if the prompt never mentions dietary restrictions, fix the prompt).

* **The Alternatives:**  

  | Source | Pros | Cons |
  | --- | --- | --- |
  | Production logs + human labels | Real distribution (Barnett: operation) | Privacy; sparse failures; labeling lag; PII |
  | Dimension-tuple synthetic | Coverage of rare failures | May invent unreachable combinations |
  | Chunk-conditioned synthetic (RAGAS / reverse facts) | Grounded in corpus; cheap qrels | Skews to single-chunk lookup if unfiltered; misses user slang |
  | Expert-authored exams | High quality | Expensive; may miss typos/SKUs |
  | LLM-as-user simulators | Scale | Mode collapse; needs filters/dedup |
  | Public IR/RAG benchmarks (BEIR nfcorpus, etc.) | Comparable; NeMo examples | Not your schema, ACL, or jargon |

  **Reference shape:** full gold answer (LangSmith correctness) vs `expected_facts` list (Databricks) vs gold `chunk_id`s only (IR CI). Strong sets store **all three** where possible.

  **Refresh:** continuous sample of production + periodic expert review; **retire** rows when docs are deleted or mark `superseded_by`. Stale gold is how faithfulness stays high while correctness vs world dies (Week 9 drift).

  The syllabus selects **Week 9 log + reverse-from-chunk + dimension tuples → expert keep/kill → pin with corpus_hash**, with unanswerable and ACL-denied slices mandatory.

* **Failure Modes:**  
  - Without a golden set pinned to **corpus + pipeline versions**, regressions from prompt, embedding, or chunker changes are undetectable; Week 7 lexical and Week 8 rerank deltas are **undefined** if the query set moved.  
  - Without **unanswerable** and **ACL-denied** rows, refusal never gets a metric; systems are rewarded for hallucinating on FP1.  
  - Averaging metrics across incomparable rows (answerable vs unanswerable; SKU vs FAQ) without Week 9 failure tags.  
  - Barnett BioASQ lesson: automated eval can be **more pessimistic** than a non-expert human — golden sets need a **human calibration subset**, not only LLM judges.  
  - Reverse-generated questions overstate retrieval (they share the chunk’s vocabulary); production logs under-sample rare SKUs — keep a synthetic lexical slice.

* **Average vs. Strong Engineer:**  
  **Average:** 15 FAQ questions in a spreadsheet, no IDs, no hash, no unanswerable slice.  
  **Strong:** JSONL + qrels + slices + 30-human calibration; LangSmith / MLflow / Unity Catalog or plain versioned JSONL with SHA of corpus snapshot; mix synthetic + reverse-from-chunk, **replace weight** with production over time; multi-turn as a separate slice rather than exploding Cartesian product on day one.  
  **FDE bar:** explain why reverse-generated questions overstate retrieval and why production logs under-sample rare SKUs (so you **keep** a synthetic lexical slice); can walk the filter funnel and pin story.

* **Worked Example:**  
  Build sequence for Deployment Copilot (Weeks 6–9 runbook bot):

  1. Dump Week 9 debugging log; keep every query with `gold_chunk_ids` and `injection_cell`.  
  2. Add reverse-generated questions from 20 runbook chunks (Hamel RAG method) — mark `source=synthetic_reverse`.  
  3. Hand-write 20 dimension tuples: `{issue: auth|search|ingest, complexity: lookup|multi-hop, answerable: Y|N, lexical: sku|error|none}`. Realize as queries.  
  4. Expert keep/kill to **n=60**. Add 8 unanswerable + 4 ACL-denied.  
  5. Pin `golden_v1.jsonl` + `corpus_hash`. Create LangSmith dataset (or equivalent) in the tutorial shape.  
  6. Human-label 30 rows for faithfulness + correctness; do **not** gate CI on judges until TPR/TNR known.

  Target product shape from overview: **N ≈ 40–80** queries — semantic FAQ, lexical-precision (SKU / error code / version), multi-hop, **unanswerable**, ACL-denied. Gold = supporting `chunk_id`s (and `expected_facts` where the answer is a list).

* **Apply It:**  
  1. Convert Week 9 debugging log into stratified golden rows joined on `retrieval_id`.  
  2. Store gold `chunk_id`s, `expected_facts` / reference, failure tags, `corpus_hash`, `pipeline_version`.  
  3. Add explicit unanswerable and ACL-denied slices; measure refusal precision / pass rate.  
  4. Bootstrap with reverse generation and ~20 hand-written dimension tuples; expert keep/kill; dedup.  
  5. Human-label ≥30 rows for judge calibration before any CI gate on LLM scores.  
  6. Retire or supersede rows when docs delete; refresh with production samples on a 2–4 week cadence when live.

---

### Component-level vs end-to-end evaluation

* **Fundamentals:**  
  RAG evaluation has **levels**. Mixing them produces numbers that cannot be actioned. Databricks (What is Agent Evaluation): use **component-level tests** (retrieval relevance, parameter formatting) **plus** **end-to-end** success; failing rows get **root-cause** analysis. MLflow tracing makes both possible on the same run. Azure’s docs use the same cut under different names: **process evaluation** (retrieval) vs **system evaluation** (final response). NVIDIA NeMo’s RAG flow literally offers different jobs: retrieval + generation + eval together; **answer evaluation on pre-generated answers**; generation+eval with **cached retrieved docs**.

  | Level | What is measured | Example metrics | Primary use |
  | --- | --- | --- | --- |
  | **Component — retrieval** | Quality of candidate sets independent of final wording | P@k, R@k, MRR, NDCG, context precision/recall, Azure Document Retrieval, NeMo `pytrec_eval` | Tune embeddings, *k*, hybrid, rerankers |
  | **Component — generation** | Reader behavior given **fixed** contexts | Faithfulness, format, citation ∈ C, completeness on frozen C | Tune prompts, models, decoding; fair A/B of generators |
  | **End-to-end (system)** | User-visible outcome of the **full** pipeline | Correctness vs reference, task success, live groundedness, latency/cost | Release gates, product KPIs |
  | **Trace / agent-level** | Multi-step tool/retrieve paths | Databricks/MLflow span scorers, tool-call correctness, trajectory | Debug agents (Phase 3); still relevant if RAG is a tool |

  **Isolation techniques:**

  - **Freeze retrieval:** store packed `ids[]` / `packed_text_hash` / NeMo cached retriever outputs / MLflow spans. Iterate the generator **without** re-retrieving.  
  - **Freeze generation:** swap retrievers (Week 7–8 ablations) while keeping the **same** judge harness and gold answers.  
  - **NeMo (docs):** (1) Retrieval + Answer Generation + Answer Evaluation (live pipeline); (2) Answer Evaluation on **pre-generated** answers; (3) cached retriever outputs + generate + eval. Older target schema named this `cached_outputs` (later versions prefer **dataset** targets holding those fields).  
  - **RAGAS:** component-wise metrics that still **roll up** to system quality if you refuse to average away slices.  
  - **Noise sensitivity** (RAGAS / NeMo): generation robustness when retrieval is imperfect — a **bridge** metric between component and E2E.

  Barnett: many characteristics are only visible **at runtime** with live users — E2E **online** eval complements offline components. Databricks: **offline** curated datasets vs **online** scoring of production traces; production traces feed the next golden set. Hamel: debug **retrieval first** with IR metrics; then generation with error analysis and validated judges. Jason Liu Tier 1 vs Tiers 2–3 is the same isolation.

* **The Alternatives:**  

  | Strategy | Pros | Cons |
  | --- | --- | --- |
  | E2E-only | Matches user experience | Confounded; slow attribution; expensive labels |
  | Component-only | Fast debugging loops | Can over-optimize a stage that doesn’t move E2E (rerank NDCG↑, users still fail completeness) |
  | Frozen-context generation harness | Fair LLM / prompt comparisons | Misses retrieval–generation **interactions** (noise sensitivity, LITM) |
  | Online shadow eval | Real traffic | Privacy, judge cost, risk if writes |
  | Single “quality” score | Exec-friendly | Hides regressions |
  | Public agent benchmarks (OfficeQA, MiniWoB++, HLE) | Architecture sanity | Databricks: **not** production readiness |

  **CI vs pre-release vs prod (budget):**

  | Cadence | What runs | Spend |
  | --- | --- | --- |
  | **CI** (every PR) | ID Recall@k + P@k on pinned qrels; schema/citation **code** scorers; faithfulness on **frozen** good contexts (HHEM or small judge) | Cheap, deterministic preferred |
  | **Pre-release** | Full golden E2E: correctness + triad + slices | Judge cost accepted |
  | **Production** | Sampled reference-free triad + user feedback; periodic human review (Hamel 100+ traces / 2–4 weeks) | Sample rate is the knob |

  Release processes that gate **only** on faithfulness can ship a retriever regression (faithful to the wrong C). Gating **only** on answer correctness can hide rising hallucination **masked by parametric knowledge** (correct but ungrounded).

  The syllabus selects **two-level eval**: CI on ID retrieval + frozen-context generation; pre-release on full golden E2E; production on sampled triad — with LangSmith/RAGAS/Azure/NeMo/MLflow as interchangeable harnesses mapped to the same levels.

* **Failure Modes:**  
  - Week 7 hybrid raises Recall@40 without moving E2E if packed k still misses gold — **only the two-level table shows that**.  
  - A prompt change raises frozen-context faithfulness but **drops** E2E on live retrieval — noise-sensitivity / LITM, not a “prompt win.”  
  - NeMo `retriever_*` metrics only when a retriever pipeline is in the target — if you only pass cached answers, you are not measuring retrieval this run.  
  - MLflow groundedness scored against a later re-fetch instead of the RETRIEVER span — wrong C for A\|C.  
  - E2E success hides inefficient or unsafe agent trajectories (Databricks failure taxonomy for agents) — single-shot RAG still needs the retrieval vs generation split.

* **Average vs. Strong Engineer:**  
  **Average:** one E2E % on 12 questions; no frozen harness; “we used RAGAS” with no denominator, no *k*, no slice.  
  **Strong:** two-level dashboard + frozen harness; CI / pre-release / prod budget table; LangSmith one `evaluate()` with four evaluators so component vs E2E appear on the **same** rows; Azure Document Retrieval for **parameter sweep** of search, system evaluators for the answer; deterministic scorers for citations-present, JSON schema, refusals.  
  **FDE bar:** name which NVIDIA job type they ran; why Azure process ≠ system; why MLflow groundedness must use the RETRIEVER span; tell a quantified before/after with owner of each delta.

* **Worked Example:**  
  Change: swap `gpt-4.1-mini` for a cheaper reader on Deployment Copilot.

  | Harness | Result | Interpretation |
  | --- | --- | --- |
  | E2E-only on live hybrid | Correctness 0.68 → 0.61 | “Worse model” — maybe |
  | Frozen C from Week 8 packed gold | Faithfulness 0.84 → 0.70, completeness ↓ | Generator regression (real) |
  | Same cheap model, **oracle** gold chunks packed | Correctness back to 0.74 | Model is OK **if** C is clean; live drop is noise sensitivity |
  | Retrieval metrics unchanged | Recall@8 = 0.74 both | Don’t retune RRF |

  **Quantified interview story (before / after Weeks 7–9)** — fill the **your numbers** column from actual Week 7–9 logs. The **illustrative** column is a teaching shape (order of magnitude and **which way** metrics move), not a published benchmark. Never cite the illustrative column as a paper result.

  | Stage | What changed | Retrieval (illustrative) | Generation / E2E (illustrative) | Owner of the delta |
  | --- | --- | --- | --- | --- |
  | **W6 baseline** | Recursive chunks; dense cosine `k=5`; no BM25; no candidate log | Recall@5 **~0.41** overall; lexical slice Recall@5 **~0.18**; MRR **~0.33** | E2E correctness **~0.48**; faithfulness **~0.71** (faithful to junk); answer relevancy **~0.80** | — |
  | **After W7** | Dense+BM25 → RRF `fetch_k≈40`; identifier analyzer; candidate logs | Recall@40 **~0.78** / lexical Recall@40 **~0.71**; Recall@5 still **~0.50** (gold in pool, not packed) | Correctness **~0.55** (more evidence, still noisy window); faithfulness **may dip** (more FP4 noise) | Search: recall; packing still Week 8 |
  | **After W8** | CE rerank → pack 8; LITM-aware order; one query transform on hard slice | NDCG@8 **~0.62 → ~0.79**; MRR **~0.52 → ~0.70**; Recall@8 **~0.74** | Correctness **~0.68**; context precision **up**; faithfulness **up** if noise dropped | Ranking / packing |
  | **After W9** | Fault matrix; refuse on FP1; citation snapshot; don’t punish faithfulness when Recall@k=0 | Same IR on answerable slice; **new** slice metrics: refusal precision on unanswerable | Correctness on answerable **~0.72**; unanswerable “I don’t know” **pass rate ~0.90**; groundedness **not** averaged with FP1 | Taxonomy + policy |
  | **W10 harness** | Pin golden set; report **disaggregated** + CI; judge calibration n≥30 | Publish Recall@k at **k_prod and fetch_k**; holes/fidelity if using Azure labels | Triad + correctness; TPR/TNR of faithfulness judge vs human | Eval engineering |

  **How to say it in an interview (STAR-shaped):**

  > “On 60 labelled queries pinned to corpus `abc123`, cosine-only `k=5` had Recall@5 = 0.41 (0.18 on SKU/error-code). Hybrid RRF at 40 lifted Recall@40 to 0.78 but packed-window Recall@5 only to 0.50 — so generation was still starved. Cross-encoder packing to 8 moved NDCG@8 from 0.62 to 0.79 and E2E correctness from 0.55 to 0.68. Faithfulness stayed high on a retrieval miss until we **stopped averaging** FP1 rows into the generator score and added an unanswerable slice (refusal pass 0.90). We gate CI on Recall@8 + faithfulness on **frozen good contexts**, and gate release on E2E correctness + triad.”

  That paragraph is the Week 10 deliverable. Swap in **your** logged numbers.

* **Apply It:**  
  1. Stand up one primary harness (RAGAS collections / LangSmith experiment / Azure `evaluate()` / NeMo RAG flow / MLflow scorers); keep a mapping table to the others.  
  2. Freeze packed contexts for generator A/B; freeze generator for retriever A/B.  
  3. CI: ID Recall@k + P@k + schema/citation code scorers + faithfulness on frozen good contexts.  
  4. Pre-release: full golden E2E (correctness + triad + slices). Production: sampled reference-free triad + periodic human review.  
  5. Produce the before/after table vs Weeks 7–9 on the **same** pinned queries; name *k*, owner, and next lever.  
  6. Never gate release on faithfulness alone or on a single aggregated “RAG score.”

---

## Week 10 build checklist (end-to-end)

Use this as the chapter’s capstone sequence; every concept above maps here.

1. **Pin golden set:** Queries + gold `chunk_id`s / `expected_facts` + unanswerable (+ ACL-denied) slice; stamp `corpus_hash` + `pipeline_version`.  
2. **Harness:** RAGAS-style evaluate (or LangSmith / Azure / NeMo / MLflow — one primary).  
3. **Retrieval scores:** Recall@k, P@k, MRR, NDCG at **k_prod** and **fetch_k**; ID-based preferred.  
4. **Generation scores:** Faithfulness, answer relevancy, context precision; reference correctness on golden slice; refusal_ok on unanswerable.  
5. **Isolation:** Frozen packed C for generator A/B; frozen generator for retriever ablations.  
6. **Before/after table:** Cosine → hybrid → +rerank → taxonomy-informed policy on the same queries — the interview artifact.  
7. **Gates:** CI on ID IR + frozen faithfulness; release on E2E correctness + triad; judges gated only after human TPR/TNR.  
8. **Disaggregate:** Never ship a single “quality” number; report slices (lexical / multi-hop / unanswerable / FP1 vs answerable).

Minimum loop shape:

```text
for each row in golden.jsonl  # pinned: corpus_hash, pipeline_version
  run retriever @ fetch_k, rerank, pack @ k_prod
  log retrieval_id, ids[], ranks, packed_text_hash
  generate answer
  score:
    ID Recall@k_prod, Recall@fetch_k, P@k, MRR, NDCG@k   # component retrieval
    RAGAS faithfulness, answer_relevancy, context_precision
    reference correctness (if reference exists)
    refusal_ok on unanswerable slice
```

When those steps are true, Week 10 is done in the syllabus sense: Weeks 7–9 changes have **numbers**, retrieval and generation have **separate owners**, and the interview story is a quantified before/after — not “we used RAGAS.”

---

## Looking ahead

Week 11 opens **Phase 3 — Agentic Systems** with **agent fundamentals**: a **bounded tool-using agent loop** (not MCP, not multi-agent) and a small palette of **2–3 tools** (e.g. docs search, structured query, calendar read/write split). The loop contract — pairing tool calls to results, iteration caps, typed stop reasons, error observations — is the artifact. Keep this week’s eval harness and golden-set discipline; Phase 3 later scores **trajectories**, which do not exist if the loop is a hidden `while True`. Deployment Copilot’s runbook corpus from Weeks 6–10 becomes a natural `docs_search` surface when tools arrive.
