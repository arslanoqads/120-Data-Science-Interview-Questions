# 00 — Week overview & syllabus mapping

> Week 9 — RAG failure taxonomy  
> Research notes (raw).

---

## Fundamentals

Week 9 is the **diagnosis** week of Phase 2 RAG. Weeks 6–8 produced chunks, a hybrid candidate set, and a reranked packed window. This week answers: **when the answer is wrong, which stage broke?** The syllabus spine is not a new architecture. It is a **fault-injection + classification** protocol plus a **portfolio debugging log**.

Barnett, Kurniawan, Thudumu, Brannelly, Abdelrazek (*Seven Failure Points When Engineering a Retrieval Augmented Generation System*, arXiv:**2401.05856**, CAIN 2024) give the empirical catalogue. Three case studies (Cognitive Reviewer, AI Tutor, BioASQ: ~4k OA PDFs, 1,000 expert Q/A, GPT-4 + OpenAI Evals, then manual inspection) produced **seven failure points** on the Index/Query graph. Two engineering takeaways:

1. **Validation is only feasible during operation** — real query distributions and unknown inputs appear at runtime. Offline G-Eval-style methods need labelled Q/A that often do not exist when you first index unstructured docs.  
2. **Robustness evolves rather than being designed in** — chunk size, embedding, retrieval, consolidation, context size, and prompts are continuously calibrated.

Teaching compression of those seven points into **three canonical modes** that match component ownership:

| Canonical mode | Pipeline locus | Core question | Primary owner |
| --- | --- | --- | --- |
| **Recall failure** | Corpus, chunk/embed, filters, stage-1 | Was the needed evidence ever **eligible** to be returned? | Search / data |
| **Ranking / context-assembly failure** | Rank, rerank, consolidator, pack order | Did useful evidence land **high enough** and **survive** into the prompt? | Search / prompt packing |
| **Generation-grounding failure** | Reader / LLM | Given usable context, did the model **extract, stay faithful, and answer completely**? | Prompt / model / schema |

Jason Liu (*There Are Only 6 RAG Evals*, still public at jxnl.co, 2025-05-19) supplies the **metric graph**: three variables Question (Q), Context (C), Answer (A) and six conditionals. Hamel Husain (hamel.dev evals FAQ) maps that graph onto ops: **Tier 1 IR metrics for retrieval first**, then generation judges **validated against humans**. Azure Foundry and NVIDIA NeMo both split **process (retrieval)** evaluators from **system (groundedness / relevance / completeness)** evaluators — the same cut.

Liu et al. (*Lost in the Middle*, arXiv:**2307.03172**) is the packing failure that sits on the rank/grounding border: gold can be **in the prompt** and still unused. Databricks (Leng et al., arXiv:**2411.03538**) shows long context does not retire RAG; it changes **how much** you retrieve and **how models fail** past an effective window.

**This week’s artifact is a log, not a dashboard.** Join on `retrieval_id` from Weeks 7–8. Label every broken run. Week 10 turns labels into metric recipes.

---

## Alternatives & Tradeoffs

| Path | What you optimize | What you sacrifice |
|------|-------------------|-------------------|
| Collapse all errors into “hallucination” | Simple narrative | Wrong owner; swap generator when gold never retrieved |
| Full 7-point Barnett only | Fine-grained debugging | Overlapping labels (FP2 vs FP3; FP4 vs FP7); harder to instrument |
| **Canonical 3-mode + Barnett FP as subtype** (syllabus default) | Component ownership + paper vocabulary | Consolidator bugs can look like rank *or* ground |
| Jason Liu 6 Q–C–A only | Completeness of pairwise relations | Does not name index/ACL/drift; Hamel: add domain modes from error analysis |
| E2E answer accuracy only | One number for slides | Confounds recall, rank, and grounding (Week 10 trap) |
| Vendor default metrics (fluency, coherence) | Easy tooling | Hamel: platform defaults ≠ product failures |

| Fault-injection style | Pros | Cons |
|-----------------------|------|------|
| **One fault per cell** (syllabus) | Causal attribution; portfolio-ready | Slow; needs pinned golden set |
| Production error analysis only | Real distribution (Barnett: validation in operation) | Confounded; no counterfactual |
| Synthetic Q from chunks only | Cheap qrels (Hamel reverse generation) | Misses user wording / unanswerable queries (FP1) |

Do not start Week 9 by swapping Cohere for BGE. If gold is absent from `fetch_k`, that is recall. If gold is in `fetch_k` but not packed, that is ranking/assembly. If gold is packed and the model invents, that is grounding.

---

## Necessity

Concrete failure modes if Week 9 is skipped:

- Teams “fix the prompt” when the doc was never indexed (FP1) or never ranked into top-K (FP2).  
- “I don’t know” is treated as always-bad — it is **correct** on missing content and **wrong** when gold existed.  
- Citations lend **false trust** (right-looking `[1]` pointing at a live URL that no longer contains the quoted span).  
- After a doc update, groundedness stays high (faithful to **stale** chunks) while correctness vs world collapses — drift mislabelled as hallucination.  
- Raising `k` into a long window looks like using the model card; Liu et al. show extra docs stop helping and mid-context gold can beat **closed-book** in the wrong direction (GPT-3.5-Turbo multi-doc QA **below** 56.1% closed-book when gold is mid-prompt).  
- Week 10 metrics get attached to the wrong stage (faithfulness on a recall miss is a **false** generator bug).

Without a taxonomy, error analysis in Week 16 has no starter codebook for RAG traces.

---

## Industry Practice

- **Common (demo AI):** read the chat, say “hallucination,” change temperature or the system prompt. No candidate log. No gold IDs.  
- **Strong:** log stage-1, rerank, packed text, `packed_position`, citations, `pipeline_version`. Maintain a **fault-injection matrix** on a pinned golden set. Use Azure **process** evaluators (Document Retrieval NDCG/fidelity/holes, or Retrieval LLM-judge) separately from **system** Groundedness / Relevance / Response Completeness. NVIDIA: `retriever_recall_k` / `retriever_ndcg_cut_k` (`pytrec_eval`) vs `rag_faithfulness` / `rag_answer_relevancy` (`ragas`). Databricks `RetrievalGroundedness` requires a RETRIEVER span — the judge reads **trace context**, not a later re-fetch.  
- **FDE bar:** quote Barnett FP1–FP7 in order; map each to 3-mode + Q–C–A; treat “I don’t know” as a labelled outcome; pin evidence snapshots; refuse to report a single E2E % as the Week 9 deliverable.

Hamel: retrieval is a **search problem** (Recall@k, Precision@k, MRR). Generation uses **error analysis → human labels → targeted judges → TPR/TNR calibration**. Jason Liu’s six evals are the relationship graph, not a license to skip IR metrics (his own Tier 1).

---

## Concrete Scenario

Same product as Weeks 6–8. Pin a golden set of ~30–50 queries with **supporting `chunk_id`s** (and an **unanswerable** slice for FP1).

**Deliberate-break matrix** (one change per row; restore after each):

| Cell | Injection | Expected canonical | Expected Barnett | Expected Q–C–A break |
|------|-----------|--------------------|------------------|----------------------|
| A | Delete gold doc from index (or ACL-deny the tenant) | Recall | FP1 | C\|Q weak; Q\|C unanswerable — refusal should pass |
| B | Keep gold; set packed `k` below gold’s fused/rerank rank | Ranking | FP2 | C\|Q fails at production k; recall@fetch_k still high |
| C | Retrieve gold at rank 2; consolidator/token budget drops it | Ranking / assembly | FP3 | C exists in retriever span, absent from prompt C |
| D | Pack gold + contradicting/noisy neighbors; gold mid-list | Grounding (± LITM) | FP4 | A\|C fails; gold present |
| E | Ask for a JSON list; prompt allows prose | Grounding | FP5 | A\|Q / format contract |
| F | Teacher wants unit-week citation; model returns generic fact | Grounding | FP6 | A\|Q specificity |
| G | Multi-doc “key points in A,B,C”; model answers A only | Grounding | FP7 | C\|A coverage; completeness |
| H | Update source PDF; do **not** reindex | Recall (stale) | FP1/FP2-like | Drift; citations point at new URL, old hash |
| I | Pack 20 docs, gold at position 10 | Rank/ground border | FP4 + LITM | Position ablation |

**Portfolio debugging log** (append-only JSONL, join key `retrieval_id`):

| Field | Why |
|-------|-----|
| `retrieval_id` | Week 7–8 join — **do not overwrite** candidate arrays |
| `query`, `query_slice` | factoid / multi-hop / unanswerable / vocab-gap |
| `gold_chunk_ids[]`, `gold_in_corpus` | FP1 vs FP2 gate |
| `stage1.ranks{}`, `fetch_k` | recall eligibility |
| `rerank.ids[]`, `rerank.ranks{}` | FP2 |
| `packed.ids[]`, `packed_position`, `packed_text_hash` | FP3 + LITM |
| `answer`, `citations[]`, `evidence_snapshot_hash` | grounding + citation drift |
| `canonical_mode`, `barnett_fp`, `qca_failed[]` | taxonomy labels |
| `pipeline_version`, `embedding_model`, `chunker_config`, `index_alias` | drift |
| `injection_cell` | A–I or `prod` |
| `notes` | one-sentence human rationale (Hamel journaling) |

Public bar: Barnett HTML + abs; Jason Liu six evals page (confirm still 200); Hamel RAG FAQ; Azure RAG evaluators; NVIDIA RAG flow; Liu et al. 2307.03172.

URL: https://arxiv.org/abs/2401.05856  
Companions: https://jxnl.co/writing/2025/05/19/there-are-only-6-rag-evals/ · https://hamel.dev/blog/posts/evals-faq/index.html · https://learn.microsoft.com/en-us/azure/foundry/concepts/evaluation-evaluators/rag-evaluators · https://docs.nvidia.com/nemo/microservices/latest/evaluate/flows/rag.html · https://arxiv.org/abs/2307.03172

---

## Open Questions

- Attribute FP3 (consolidation) to ranking metrics, a separate **assembly** metric, or prompt-token accounting?  
- Parametric knowledge that is **true** but **not** in C: grounding failure, retrieval failure, or allowed hybrid policy with a “model prior” tag?  
- Taxonomies for **agentic / multi-hop** RAG (tool hops, query rewrite, retry) — Barnett’s pipeline is single-shot; later papers (CHARM, AgenticRAG-FP) treat cascade. Week 9 stays single-shot; flag the gap.  
- How many fault cells are enough for a portfolio vs a production canary set?  
- Should unanswerable queries be a first-class golden-set slice from day one (Azure completeness vs groundedness precision/recall split)?

---

## Classification cheat sheet (syllabus instrument)

Walk **in order**. Stop at the first yes.

1. **Gold not in corpus / not visible under ACL / wrong chunker so the span never existed?** → **Recall** (FP1). Success = refusal.  
2. **Gold in corpus, not in `fetch_k`?** → **Recall** (stage-1 miss; still FP2-adjacent if “all docs ranked in theory”).  
3. **Gold in `fetch_k`, not in packed window?** → **Ranking / assembly** (FP2 near-miss or FP3).  
4. **Gold packed, mid-position, model ignores?** → **LITM / FP4** (log `packed_position`).  
5. **Gold packed, model adds unsupported claims?** → **Grounding** (FP4; A\|C).  
6. **Faithful but wrong shape / specificity / missing siblings?** → **Grounding** (FP5–7).  
7. **Was right last week after a corpus or pipeline change?** → **Drift** (re-run 1–6 on both index aliases).

Observed-symptom table:

| Observed symptom | Likely mode | First measurements |
| --- | --- | --- |
| Invents facts; sources empty/irrelevant | Recall or ranking | recall@k, retrieval relevance judge (C\|Q) |
| Right doc in corpus, wrong answer | Ranking or grounding | MRR/NDCG; inspect top-k vs packed |
| Right chunk in prompt, wrong/partial answer | Generation-grounding | Faithfulness, completeness, position ablation |
| Correct yesterday, wrong after doc update | Corpus drift | `content_hash`, `pipeline_version`, dual-index eval |
| Quality drops as *K* increases | Lost-in-middle / noise | Context precision, faithfulness vs *K* sweep |

---

## Sources

- Barnett et al., Seven Failure Points: https://arxiv.org/abs/2401.05856 · HTML https://arxiv.org/html/2401.05856v1 · figshare https://figshare.com/s/fbf7805b5f20d7f7e356  
- Jason Liu, There Are Only 6 RAG Evals (public 2025-05-19): https://jxnl.co/writing/2025/05/19/there-are-only-6-rag-evals/  
- Hamel Husain, evals FAQ (RAG): https://hamel.dev/blog/posts/evals-faq/index.html · dedicated page https://hamel.dev/blog/posts/evals-faq/how-should-i-approach-evaluating-my-rag-system.html  
- Liu et al., Lost in the Middle: https://arxiv.org/abs/2307.03172  
- Azure AI Foundry RAG evaluators: https://learn.microsoft.com/en-us/azure/foundry/concepts/evaluation-evaluators/rag-evaluators  
- NVIDIA NeMo RAG evaluation flow: https://docs.nvidia.com/nemo/microservices/latest/evaluate/flows/rag.html  
- NVIDIA RAG metrics (RAGAS family): https://docs.nvidia.com/nemo/microservices/26.3.0/evaluator/metrics/rag.html  
- Databricks long-context RAG: https://www.databricks.com/blog/long-context-rag-performance-llms  
- Chip Huyen (public): context length ≠ context use https://huyenchip.com/2023/08/16/llm-research-open-challenges.html  
- YouTube: Hamel “How To Approach Your AI Evals” https://www.youtube.com/watch?v=DZxaPNYi_k0  
- TWIML: Why Your RAG System Is Broken (Jason Liu) https://twimlai.com/podcast/twimlai/why-your-rag-system-is-broken-and-how-to-fix-it  
