# Week 27 Textbook Chapter — Open-source and self-hosted models

> **Status:** COMPLETE  
> **Source:** `research/phase-7/week-27-open-source-self-hosted/`  
> **Chapter:** [chapter.md](chapter.md)

## Concepts covered

- [x] Open-source model landscape (Llama / Qwen / Gemma)
- [x] Quantization basics
- [x] Local inference tooling (Ollama vs vLLM)
- [x] Self-hosted vs API tradeoffs
- [x] Air-gapped deployment

## Structure check

Each concept includes Fundamentals, The Alternatives, Failure Modes, Average vs. Strong Engineer, Worked Example, and Apply It.

## Syllabus build

Add a **self-hosted model as one leg of the Week 20 router** — do **not** replace the hosted API stack. Document (and later implement in the Week 20 lab) only: (1) **route subset** — rules or classifier send a defined slice (e.g. PII-tagged tenants, “must stay on-prem,” cheap FAQ) to a **local Ollama-served OSS model**; (2) **short comparison** — same golden set for **latency** (TTFT / p95), **quality** (task metric), and **cost** ($/1k calls amortized GPU vs API tokens) vs existing hosted routes; (3) **direct answer** — what if the customer **cannot use a hosted API** (residency, air-gap, procurement)? Show the self-hosted path is a first-class route, not an afterthought.
