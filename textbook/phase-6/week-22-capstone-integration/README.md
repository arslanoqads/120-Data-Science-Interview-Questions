# Week 22 Textbook Chapter — Capstone integration

> **Status:** COMPLETE  
> **Source:** `research/phase-6/week-22-capstone-integration/`  
> **Chapter:** [chapter.md](chapter.md)

## Concepts covered

- [x] Systems integration / freezing scope for demoable AI products
- [x] Eval-log-driven bug fixes (taxonomy → frequency × severity × leverage)
- [x] Technical demo narrative (claim → architecture → evidence → failure → next bet)

## Structure check

Each concept includes Fundamentals, The Alternatives, Failure Modes, Average vs. Strong Engineer, Worked Example, and Apply It.

## Syllabus build

Syllabus says “concepts: none new.” Treat that as **meta-work**: you already have Weeks 6–21 systems. This week you **stop building sideways** and make one vertical slice demo-safe.

1. **Freeze scope in writing.** One primary user job, one corpus + tool set, success metrics, and an explicit non-goals list. Walk Chip Huyen’s GenAI platform stack end-to-end for that slice: model API → guardrails → context (RAG/tools) → cache/route → logging/evals.  
2. **Triage eval logs into a bug queue.** Sample 20–50 (then ~100) traces; open-code; axial-code a taxonomy with counts; rank **frequency × severity × leverage**; fix top classes; promote fixed failures into regression evals.  
3. **Script a 5-minute walkthrough.** User stakes → requirements freeze → request + offline paths → live success with citations → intentional refusal/tool failure → metrics/tradeoffs → roadmap as non-goals. Record a backup; keep the live path primary.  
4. **Ship the polish gates.** Happy path on a clean machine / deploy URL; golden-set command in README; architecture diagram that matches code; one STAR story from a real taxonomy fix.

Interview artifact = **written demo contract** + **taxonomy table with top-5 fixes** + **5-min script (success + failure)** + **metrics line** (quality / p95 / $/1k).
