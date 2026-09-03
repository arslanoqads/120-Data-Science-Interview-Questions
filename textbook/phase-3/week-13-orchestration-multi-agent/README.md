# Week 13 Textbook Chapter — Orchestration / multi-agent

> **Compile:** COMPLETE  
> **Edit:** COMPLETE  
> **Source:** `research/phase-3/week-13-orchestration-multi-agent/`  
> **Chapter:** [chapter.md](chapter.md)

## Editorial checklist

- [x] Continuity reviewed (Week 12: MCP server/client, primitives, FDE integration surface; elicitation ≠ graph `interrupt`)  
- [x] Prerequisites Recap added  
- [x] Framing standardized to **What this week builds**  
- [x] Looking ahead → Week 14 (side-effecting domain agent + safety envelope; A2A)  
- [x] Concept structure preserved (6 fields)  
- [x] Language pass for coherence and simplicity  

## Concepts covered

- [x] Graph-based orchestration vs simple chains
- [x] Single agent with many tools vs multiple specialized agents
- [x] Agent handoff patterns
- [x] Persistence and resumable state
- [x] Human-in-the-loop checkpoints

## Structure check

Each concept includes Fundamentals, The Alternatives, Failure Modes, Average vs. Strong Engineer, Worked Example, and Apply It.

## Syllabus build

Ship a **stateful graph** with a **durable pause** before an irreversible (or expensive) write: model as a **`StateGraph`** (typed state + reducers; cycle and/or conditional edge into approval); put **one high-stakes action** behind `interrupt(payload)` before the side effect; compile with a **checkpointer** and invoke/resume on a stable `thread_id`; drive with `stream_events` v3 (or `invoke` + `__interrupt__`); resume with **`Command(resume=…)`**; prove node replay idempotency and kill-while-paused resume. Interview artifact = **trace of pause → human decision → resume** on a durable thread, plus a **named high-stakes tool that did not run until approved**.
