# Week 27 Research Corpus — Open-source and self-hosted models

> Phase 7 — Supplementary Electives (Weeks 25–29)  
> **Status:** COMPLETE (deep pass)  
> Raw research corpus (not textbook). Legal sources only.

This directory is the **Phase 7 elective Week 27** research repository. It is **not** a replacement for Weeks 1–24. Suggested slot: folds into **Week 20** (cost/latency + routing) as a self-hosted route, or stands alone after Week 20 — and after Week 19 residency when the customer cannot leave their network. Read concept files in order, then the source map.

| # | File | Concept |
|---|------|---------|
| 00 | [00-week-overview.md](00-week-overview.md) | Syllabus mapping: why OSS/self-host; Ollama→vLLM path; Week 20 router build |
| 01 | [01-open-source-model-landscape.md](01-open-source-model-landscape.md) | Llama / Qwen / Gemma landscape — how to evaluate for a task |
| 02 | [02-quantization-basics.md](02-quantization-basics.md) | Why 70B fits on one GPU after quantization; what you lose |
| 03 | [03-local-inference-tooling.md](03-local-inference-tooling.md) | Ollama for prototyping; vLLM for production-grade serving |
| 04 | [04-self-hosted-vs-api-tradeoffs.md](04-self-hosted-vs-api-tradeoffs.md) | Cost / latency / control: self-hosted vs hosted API |
| 05 | [05-air-gapped-deployment.md](05-air-gapped-deployment.md) | Air-gapped deployment considerations (weights, updates, eval) |
| — | [99-source-map.md](99-source-map.md) | Master URL / paper / blog / docs index |

## Completeness checklist (Week 27)

- [x] All syllabus Week 27 concepts covered with **7 required fields**  
- [x] **Open-source model landscape** — Llama, Qwen, Gemma; task evaluation criteria (license, size, context, evals, tool use)  
- [x] **Quantization basics** — FP16/BF16 → INT8/INT4; why ~70B fits one GPU; quality/latency tradeoffs; AWQ/GPTQ  
- [x] **Local inference tooling** — Ollama (prototype) vs vLLM (production serving); NVIDIA NIM as managed OSS path  
- [x] **Self-hosted vs API tradeoffs** — cost, latency, control, ops burden vs Week 20 hosted routes  
- [x] **Air-gapped deployment** — weight transfer, update cadence, offline eval, residency (Week 19)  
- [x] Meta Llama docs/model cards, Qwen docs, Google Gemma, Ollama docs, vLLM docs cited  
- [x] Hugging Face + AWQ (arXiv:2306.00978) + GPTQ (arXiv:2210.17323) cited  
- [x] NVIDIA NIM blogs/docs + Chip Huyen public blogs cited (no pirate PDFs)  
- [x] Cross-links: Week 20 cost/latency/routing; Week 19 residency; Week 26 fine-tuning  
- [x] Build task documented: **self-hosted leg on Week 20 router** (do NOT implement in this corpus)  
- [x] Per-week research **directory** (not a single thin file)  
- [x] Phase 7 elective note: supplementary; not a replacement for 1–24  

## Syllabus build task (Week 27)

Add a **self-hosted model as one leg of the Week 20 router** — do **not** replace the hosted API stack. Document (and later implement in the Week 20 lab) only:

1. **Route subset** — rules or classifier send a defined slice of queries (e.g., PII-tagged tenants, “must stay on-prem,” cheap FAQ) to a **local Ollama-served OSS model**.  
2. **Short comparison** — same golden set: **latency** (TTFT / p95), **quality** (task metric), **cost** ($/1k calls amortized GPU vs API tokens) vs existing hosted routes.  
3. **Direct answer** — what if the customer **cannot use a hosted API** (residency, air-gap, procurement)? Show the self-hosted path is a first-class route, not an afterthought.

Do not implement the router or Ollama integration inside this research directory. Suggested slot: folds into Week 20 or stands alone immediately after it. Pair with Week 19 data-residency questionnaires and Week 26 if the OSS model will later take PEFT adapters.

## Default path (synthesis)

1. Pick candidates from Llama / Qwen / Gemma with an explicit **task eval** + license check (file 01).  
2. Size hardware with **quantization** reality (file 02) — do not assume BF16 70B on one consumer GPU.  
3. Prototype on **Ollama**; graduate serving to **vLLM** (or NIM) when concurrency and SLOs matter (file 03).  
4. Price self-host vs API with Week 20 math; keep both routes behind one router (file 04).  
5. If air-gapped: plan weight import, offline eval, and update windows before promising the deal (file 05).  
6. Ship the **comparison memo** that answers “customer can’t use hosted API” with measured numbers.
