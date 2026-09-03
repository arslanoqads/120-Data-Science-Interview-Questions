# 03 — Building a golden set from real usage

> Week 10 concept research (deep). Legal sources only.

---

## Fundamentals

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

### Hamel / Shreya orthodoxy (hamel.dev)

1. **Error analysis first** — use the product; sample traces; open-code failure modes. FAQ: 60–80% of development time on error analysis; review 20–50 outputs on significant changes; a domain “benevolent dictator” as quality owner.  
2. Do **not** start from “generate 100 diverse queries” with no structure — outputs look diverse but test one behavior repeatedly.  
3. **Structured synthetic data** when needed: define **dimensions** → form **tuples** → LLM realizes natural-language queries. Write **~20 tuples by hand** first. Example dimensions (their recipe app): dietary restriction × cuisine × complexity. Support bot: issue type × mood × prior context.  
4. Tuple generation: **cross product then filter** (coverage, including edges) vs **direct LLM tuples** (more realistic, misses rare combos). Separate prompt to turn `(Vegan, Italian, Multi-step)` into “I need a dairy-free lasagna I can prep the day before.”  
5. Synthetic is a **bootstrap**; compare to **production queries** as soon as they exist. Synthetic **cannot** tell you how common a failure is. Unreliable in high-stakes domains (medicine, law) without heavy human review.  
6. Hand-label a small **anchor** (tens to low hundreds of carefully reviewed items; they cite annotating ≥30 traces yourself in the synthetic workflow, then ~100 diverse traces as a discovery pool).  
7. Re-run error analysis on **100+ fresh traces** on a 2–4 week cadence when the product is live.

Hamel RAG-specific: to evaluate retrieval, create queries paired with relevant documents by **reverse generation** — take corpus documents, extract key facts, generate questions those facts would answer. That yields query–document pairs **without** starting from manual annotation.

### RAGAS / vendor synthetic

RAGAS test-data generation (docs: Testset Generation) typically produces factual, multi-hop, and **unanswerable** queries from chunks. Unanswerables test **refusal** (Barnett FP1) — required Week 9/10 slice.

Databricks: golden / benchmark datasets versioned (Unity Catalog lineage); Agent Bricks can auto-generate **workload-specific** benchmarks from your docs/tools (blog: public OfficeQA/MultiDoc QA are research slices, **not** production gates). `expected_facts` pattern beats a single full-answer string when many phrasings are valid.

LangSmith RAG tutorial: create a dataset of questions + expected answers (Lilian Weng blog bot), run the app, score. That is the **shape**; your golden set must include **IDs and slices** the tutorial’s tiny set does not.

NVIDIA: RAG data formats BEIR / SQuAD / RAGAS; register datasets in Entity Store; retrieval metrics need qrels-style relevance.

### Filter funnel (practitioner pattern)

Synthesize or sample → **MinHash / embedding dedup** → binary judge or heuristic filter → **expert keep/kill** → pin manifest with **content hash** of corpus + dataset SHA. Do not generate synthetic data for bugs you can fix immediately (Hamel: if the prompt never mentions dietary restrictions, fix the prompt).

---

## Alternatives & Tradeoffs

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

---

## Necessity

Without a golden set pinned to **corpus + pipeline versions**, you cannot detect regressions from prompt, embedding, or chunker changes. Week 7 lexical slice and Week 8 rerank deltas are **undefined** if the query set moved.

Without **unanswerable** and **ACL-denied** rows, refusal never gets a metric; systems are rewarded for hallucinating on FP1.

Without joining Week 9 `retrieval_id` / failure tags, you will average metrics across incomparable rows (answerable vs unanswerable; SKU vs FAQ).

Barnett BioASQ: 1000 expert questions + OpenAI Evals + **manual** inspection — automated eval was **more pessimistic** than a non-expert human. Golden sets need a **human calibration subset**, not only LLM judges.

---

## Industry Practice

- Store in LangSmith datasets / MLflow evaluation datasets / **plain versioned JSONL** with SHA of corpus snapshot. Databricks Unity Catalog for lineage.  
- Include **explicit unanswerable** and **ACL-denied** cases; tag hypothesized failure mode for stratified metrics.  
- For judges: collect human pass/fail on the **same** rows; measure agreement before CI gating (Hamel).  
- Mix: start synthetic + reverse-from-chunk; **replace weight** with production over time. High-stakes: production + expert, synthetic only for rare safety cases after review.  
- Multi-turn RAG: start with **single-turn** pins; add follow-ups as a separate slice (anaphora) rather than exploding the Cartesian product on day one.  
- YouTube: Hamel Husain & Shreya Shankar — *Why AI evals are the hottest new skill for product builders*: https://www.youtube.com/watch?v=BsWxPI9UM4c  
- YouTube: Hamel *How To Approach Your AI Evals*: https://www.youtube.com/watch?v=DZxaPNYi_k0  

**Common:** 15 FAQ questions in a spreadsheet, no IDs, no hash.  
**Strong:** JSONL + qrels + slices + 30-human calibration.  
**FDE:** can explain why reverse-generated questions overstate retrieval (they share the chunk’s vocabulary) and why production logs under-sample rare SKUs (so you **keep** a synthetic lexical slice).

---

## Concrete Scenario

**Build sequence for the Weeks 6–9 runbook bot:**

1. Dump Week 9 debugging log; keep every query with `gold_chunk_ids` and `injection_cell`.  
2. Add reverse-generated questions from 20 runbook chunks (Hamel RAG method) — mark `source=synthetic_reverse`.  
3. Hand-write 20 dimension tuples: `{issue: auth|search|ingest, complexity: lookup|multi-hop, answerable: Y|N, lexical: sku|error|none}`. Realize as queries.  
4. Expert keep/kill to **n=60**. Add 8 unanswerable + 4 ACL-denied.  
5. Pin `golden_v1.jsonl` + `corpus_hash`. LangSmith dataset create as in https://docs.langchain.com/langsmith/evaluate-rag-tutorial  
6. Human-label 30 rows for faithfulness + correctness; do **not** gate CI on judges until TPR/TNR known.

Hamel synthetic FAQ: https://hamel.dev/blog/posts/evals-faq/what-is-the-best-approach-for-generating-synthetic-data.html  
Hamel RAG: https://hamel.dev/blog/posts/evals-faq/how-should-i-approach-evaluating-my-rag-system.html  
Databricks golden/benchmarks: https://www.databricks.com/blog/what-is-agent-evaluation  

---

## Open Questions

- Optimal mix: % production vs synthetic vs expert for regulated domains?  
- How to golden-set **multi-turn** RAG (anaphora, follow-ups) without exponential labeling cost?  
- When should expected output be a full answer vs `expected_facts` vs gold chunks only?  
- How often to drop items after corpus delete vs keep as “should refuse / not cite”?  
- Privacy: can production queries enter the set after redaction, or only after expert rewrite?

---

## Sources

- https://hamel.dev/blog/posts/evals-faq/index.html  
- https://hamel.dev/blog/posts/evals-faq/what-is-the-best-approach-for-generating-synthetic-data.html  
- https://hamel.dev/blog/posts/evals-faq/how-should-i-approach-evaluating-my-rag-system.html  
- https://www.youtube.com/watch?v=BsWxPI9UM4c  
- https://www.youtube.com/watch?v=DZxaPNYi_k0  
- https://docs.langchain.com/langsmith/evaluate-rag-tutorial  
- https://www.databricks.com/blog/what-is-agent-evaluation  
- https://mlflow.org/docs/latest/genai/eval-monitor/  
- Barnett et al. (test data scarcity / operational validation): https://arxiv.org/abs/2401.05856  
- RAGAS testset generation (entry): https://docs.ragas.io/en/stable/concepts/test_data_generation/  
