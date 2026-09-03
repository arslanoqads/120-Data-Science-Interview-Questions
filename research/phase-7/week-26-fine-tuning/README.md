# Week 26 Research Corpus — Fine-tuning when RAG isn't enough

> Phase 7 — Supplementary Electives (Weeks 25–29)  
> **Status:** COMPLETE (deep pass)  
> Raw research corpus (not textbook). Legal sources only.

This directory is the **Phase 7 elective Week 26** research repository. It is **not** a replacement for Weeks 1–24. Suggested slot: after Phase 2 RAG (Weeks 6–10) and Week 20 cost/latency — or append after the Week 24 capstone. Read concept files in order, then the source map.

| # | File | Concept |
|---|------|---------|
| 00 | [00-week-overview.md](00-week-overview.md) | Syllabus mapping: when FT wins vs RAG; decision memo build |
| 01 | [01-rag-vs-fine-tuning-decision.md](01-rag-vs-fine-tuning-decision.md) | Decision framework — style/format/domain language, latency, air-gap vs fresh facts, citations, cheaper iteration |
| 02 | [02-lora-qlora-peft.md](02-lora-qlora-peft.md) | LoRA / QLoRA / PEFT — adapters, rank, what you actually change |
| 03 | [03-dataset-construction-for-ft.md](03-dataset-construction-for-ft.md) | Instruction & preference data; quality > quantity; contamination; labeling cost |
| 04 | [04-eval-finetunes-vs-ragas.md](04-eval-finetunes-vs-ragas.md) | Task golden sets; regression vs RAGAS retrieval metrics; catastrophic forgetting |
| 05 | [05-cost-maintenance-finetunes.md](05-cost-maintenance-finetunes.md) | Training, hosting, versioning, base-model drift, ops burden vs prompt/RAG |
| — | [99-source-map.md](99-source-map.md) | Master URL / paper / blog / YouTube index |

## Completeness checklist (Week 26)

- [x] All syllabus Week 26 concepts covered with **7 required fields**  
- [x] **RAG vs fine-tuning decision framework** — FT wins (style/format/domain language, fixed-skill latency, offline/air-gap) vs RAG wins (fresh facts, citeable knowledge, cheaper iteration)  
- [x] **LoRA / QLoRA / PEFT overview** — Hu et al. LoRA; Dettmers et al. QLoRA; Hugging Face PEFT / TRL; Unsloth  
- [x] **Dataset construction for FT** — instruction data, preference data, quality > quantity, contamination, labeling cost  
- [x] **Eval for fine-tunes vs RAGAS** — task-specific golden sets; regression vs retrieval metrics; catastrophic forgetting checks  
- [x] **Cost and maintenance of fine-tunes** — training, hosting, versioning, base-model updates, ops vs prompt/RAG  
- [x] OpenAI fine-tuning docs + AWS Bedrock custom model FT cited  
- [x] Chip Huyen public blogs cited (LLM engineering, genai platform, pitfalls — no pirate PDFs)  
- [x] arXiv: LoRA (2106.09685), QLoRA (2305.14314)  
- [x] Cross-links: Week 10 RAG eval / RAGAS; Week 20 cost/latency; Phase 2 RAG (Weeks 6–9)  
- [x] Build task documented: **decision memo only** (not a toy LoRA)  
- [x] Per-week research **directory** (not a single thin file)  
- [x] Phase 7 elective note: supplementary; not a replacement for 1–24  

## Syllabus build task (Week 26)

Write a **decision memo only** — **not** a toy LoRA training run. The memo must argue RAG vs fine-tuning for one concrete product scenario and include:

1. **Criteria** — map the product to the Week 26 decision framework (behavior/style/format vs fresh/citeable facts; latency; air-gap; iteration velocity; data availability).  
2. **Risks** — contamination, catastrophic forgetting, ops burden when base models update, stale knowledge in weights, eval gaps vs Week 10 RAGAS.  
3. **Kill criteria** — explicit conditions under which you abandon FT (or abandon RAG-only) and switch strategy (e.g., “if golden-set format accuracy < X after N high-quality examples and prompt+RAG still wins on latency/$ , kill FT”).

Do not implement training code this week. Flagship systems often fine-tune *after* RAG and prompts plateau; this elective forces the **decision** to be written and defensible before GPU spend.

## Default path (synthesis)

1. Exhaust prompt + RAG (Phase 2) and measure with Week 10 metrics before proposing FT.  
2. Classify the residual failure: **behavior/format** → FT candidate; **missing/stale facts** → stay on RAG; **both** → hybrid (FT for form, RAG for facts).  
3. If FT: prefer PEFT (LoRA/QLoRA); budget labeling for quality over volume; freeze a task golden set + forgetting suite.  
4. Price training + hosting + retrain cadence against Week 20 cost/latency of longer prompts / retrieval.  
5. Ship the **decision memo** with kill criteria; only then consider a later lab for actual adapters.
