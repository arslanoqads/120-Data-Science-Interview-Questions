# Week 9 Research Corpus — RAG failure taxonomy

> Phase 2 — RAG Systems  
> **Status:** COMPLETE (deep pass)  
> Raw research corpus (not textbook). Legal sources only.

This directory is the Week 9 research repository. Read concept files in order, then the source map.

| # | File | Concept |
|---|------|---------|
| 00 | [00-week-overview.md](00-week-overview.md) | Syllabus mapping: deliberately break the pipeline; classify failures; keep a portfolio debugging log |
| 01 | [01-three-canonical-failure-modes.md](01-three-canonical-failure-modes.md) | Recall vs ranking vs generation-grounding; Barnett 7 FPs mapped onto the 3 modes; Jason Liu Q–C–A |
| 02 | [02-citation-and-grounding.md](02-citation-and-grounding.md) | Grounding contract, citation objects, post-hoc NLI/faithfulness, vendor groundedness evaluators |
| 03 | [03-corpus-drift-reindexing.md](03-corpus-drift-reindexing.md) | Corpus / citation / embedding drift; incremental vs full vs blue/green reindex |
| 04 | [04-rag-vs-long-context.md](04-rag-vs-long-context.md) | RAG vs stuffing; Lost in the Middle; Databricks long-context RAG; effective vs advertised window |
| — | [99-source-map.md](99-source-map.md) | Master URL / paper / blog / YouTube index |

## Completeness checklist (Week 9)

- [x] All syllabus Week 9 concepts covered with 7 required fields  
- [x] Three canonical modes: **recall / ranking / generation-grounding**  
- [x] Barnett et al. **Seven Failure Points** **arXiv:2401.05856** mapped onto the 3 modes (FP1–FP7)  
- [x] Liu et al. **Lost in the Middle** **arXiv:2307.03172** / TACL (position U-curve + open-domain saturation)  
- [x] Jason Liu **There Are Only 6 RAG Evals** still public (`jxnl.co`, 2025-05-19); Q–C–A + Tier 1–3  
- [x] Hamel Husain **hamel.dev** evals FAQ — RAG: IR metrics for retrieval, validated judges for generation  
- [x] Azure AI Foundry **RAG evaluators** (process vs system; Document Retrieval vs Groundedness / Relevance / Completeness)  
- [x] NVIDIA NeMo **RAG evaluation flow** (`retriever_recall@k` / `ndcg@k` via pytrec_eval vs `rag_faithfulness` / `rag_answer_relevancy`)  
- [x] Citation / grounding techniques (index-time IDs, generation-time contract, verification-time NLI)  
- [x] Corpus drift + reindexing strategies (full / incremental / blue-green / versioned)  
- [x] RAG vs long-context tradeoffs (Databricks Leng et al. arXiv:2411.03538; Xu et al. arXiv:2501.01880)  
- [x] YouTube / talks cited (Hamel evals, Jason Liu TWIML, Lost-in-the-Middle explainers)  
- [x] AI/RAG-service-specific failure modes noted per concept  
- [x] Per-week research **directory** (not a single thin file)  
- [x] `_PRIOR_SINGLE_FILE.md` removed after expansion  

## Syllabus build task (Week 9)

On the Week 7–8 logged RAG stack, **do not add a new retriever**. Instead:

1. **Deliberately break** the pipeline at known loci (missing gold in corpus; gold below `k`; consolidator drop; noisy packed window; stale doc version; gold buried mid-prompt).  
2. **Classify** each broken run with: canonical mode (recall / rank / ground) **and** Barnett FP (1–7) **and** the Jason Liu Q–C–A relationship that failed.  
3. Keep a **portfolio debugging log** joined on `retrieval_id` from Weeks 7–8. The log is the artifact — Week 10 turns it into a metric cookbook.

Do not skip this week for “we’ll just look at end-to-end answer accuracy.” E2E accuracy **confounds** recall, rank, and grounding. Barnett’s two takeaways: **validation is only feasible in operation**, and **robustness evolves** via continuous calibration — not a one-shot design.

## Default path (synthesis)

1. Keep Week 7 candidate logs and Week 8 `rerank.ids[]` / `packed_position`. **Append** taxonomy labels; do not overwrite.  
2. Run a **fault-injection matrix** (one fault per cell) on a pinned golden set.  
3. For each failure: first ask “was gold **eligible**?” then “did it **survive packing**?” then “did the reader **use** it?”  
4. Treat “I don’t know” as **success** on FP1 (missing content) and **bug** on FP2 (gold existed, missed top-k).  
5. Citations without a stored **evidence snapshot** are a separate failure (citation drift) even when the answer is right.
