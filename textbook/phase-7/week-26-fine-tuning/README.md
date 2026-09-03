# Week 26 Textbook Chapter — Fine-tuning when RAG isn't enough

> **Compile:** COMPLETE  
> **Edit:** COMPLETE  
> **Source:** `research/phase-7/week-26-fine-tuning/`  
> **Chapter:** [chapter.md](chapter.md)

## Editorial checklist

- [x] Continuity reviewed (Week 25: context engineering — memory, compaction, isolation, failure log)  
- [x] Prerequisites Recap added  
- [x] Framing standardized to **What this week builds**  
- [x] Looking ahead → Week 27 (Phase 7 elective — open-source/self-hosted: Llama/Qwen/Gemma, quantization, Ollama/vLLM, air-gap; self-hosted leg on Week 20 router)  
- [x] Concept structure preserved (6 fields)  
- [x] Language pass for coherence and simplicity  
- [x] Phase 7 noted as supplementary electives (does not replace Weeks 1–24)

## Concepts covered

- [x] RAG vs fine-tuning decision framework
- [x] LoRA / QLoRA / PEFT overview
- [x] Dataset construction for fine-tuning
- [x] Eval for fine-tunes vs RAGAS
- [x] Cost and maintenance of fine-tunes

## Structure check

Each concept includes Fundamentals, The Alternatives, Failure Modes, Average vs. Strong Engineer, Worked Example, and Apply It.

## Syllabus build

Write a **decision memo only** — **not** a toy LoRA training run. Argue RAG vs fine-tuning for one concrete product scenario with: (1) **criteria** mapped to the Week 26 decision framework; (2) **risks** — contamination, catastrophic forgetting, ops/base-model drift, stale knowledge in weights, eval gaps vs Week 10 RAGAS; (3) **kill criteria** — explicit conditions to abandon FT (or abandon RAG-only) and switch strategy.
