# Week 11 Textbook Chapter — Agent fundamentals

> **Compile:** COMPLETE  
> **Edit:** COMPLETE  
> **Source:** `research/phase-3/week-11-agent-fundamentals/`  
> **Chapter:** [chapter.md](chapter.md)

## Editorial checklist

- [x] Continuity reviewed (Week 10: RAGAS harness, golden set, component vs E2E; runbook corpus → `docs_search`)  
- [x] Prerequisites Recap added  
- [x] Framing standardized to **What this week builds**  
- [x] Looking ahead → Week 12  
- [x] Concept structure preserved (6 fields)  
- [x] Language pass for coherence and simplicity  

## Concepts covered

- [x] Agent loop vs naive `while True`
- [x] Tool / function calling schemas (OpenAI + Anthropic)
- [x] Tool selection and disambiguation
- [x] Tool error handling and retry
- [x] Stopping conditions and loop-limit guardrails

## Structure check

Each concept includes Fundamentals, The Alternatives, Failure Modes, Average vs. Strong Engineer, Worked Example, and Apply It.

## Syllabus build

Ship a **single-agent tool loop** (not MCP, not multi-agent): define three client tools with strict JSON Schema (`docs_search`, `structured_query`, `calendar_list_events` / `calendar_create_event`); implement a bounded OpenAI Responses or Anthropic Messages loop with pairing, iteration cap, per-tool timeout, and a typed stop reason; convert tool exceptions into error observations; log a turn trace (stop reason, tool names, latency, error class, remaining budget). Interview artifact = multi-step trajectory with a **named stop reason**.
