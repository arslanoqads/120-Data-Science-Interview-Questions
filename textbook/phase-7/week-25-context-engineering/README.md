# Week 25 Textbook Chapter — Context Engineering as a discipline

> **Status:** COMPLETE  
> **Source:** `research/phase-7/week-25-context-engineering/`  
> **Chapter:** [chapter.md](chapter.md)

## Concepts covered

- [x] Context vs prompt engineering
- [x] Context sources and layers
- [x] Memory systems (short-term/session vs long-term/persistent)
- [x] Context compaction
- [x] Context isolation
- [x] Multi-agent context sharing
- [x] Context failure modes (stale, poisoning, lost handoffs + Breunig / LITM)

## Structure check

Each concept includes Fundamentals, The Alternatives, Failure Modes, Average vs. Strong Engineer, Worked Example, and Apply It.

## Syllabus build

Add an explicit **context-management layer** to the Phase 3 agentic stack (do not invent a new model API): (1) **session memory** — persist thread/session state; compact when token count crosses a threshold; (2) **isolation** — separate context namespaces per agentic system / sub-agent; (3) **failure-mode log** — stale context, poisoning, lost handoffs (plus distraction / confusion / clash), joinable on `session_id` / `handoff_id`.
