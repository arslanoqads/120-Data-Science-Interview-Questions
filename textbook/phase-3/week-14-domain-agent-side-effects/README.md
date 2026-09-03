# Week 14 Textbook Chapter — Domain agents & side-effect safety

> **Compile:** COMPLETE  
> **Edit:** COMPLETE  
> **Source:** `research/phase-3/week-14-domain-agent-side-effects/`  
> **Chapter:** [chapter.md](chapter.md)

## Editorial checklist

- [x] Continuity reviewed (Week 13: graphs, multi-agent, handoffs, persistence, HITL / `interrupt` + `thread_id`)  
- [x] Prerequisites Recap added  
- [x] Framing standardized to **What this week builds**  
- [x] Looking ahead → Week 15 (traces, trajectory vs outcome, failure patterns)  
- [x] Concept structure preserved (6 fields)  
- [x] Language pass for coherence and simplicity  

## Concepts covered

- [x] Agent-to-Agent (A2A) delegation
- [x] Side-effecting agent design
- [x] Idempotency, confirmation gates, and dry-run
- [x] Audit logs for agent actions

## Structure check

Each concept includes Fundamentals, The Alternatives, Failure Modes, Average vs. Strong Engineer, Worked Example, and Apply It.

## Syllabus build

Ship a **second, smaller agentic system** whose job is to **change the world** — not to answer a question: pick **one** domain write (refund against a fake payments table, calendar create, or ticket file); split `lookup_*` / `preview_*` / `propose_*` / `commit_*` so the model cannot reach the write without preview or a confirmation token; wrapper-owned **idempotency keys** (never LLM); gate irreversible commits with Week 13 `interrupt()` or tokenized propose/commit; **read-back** environment state as truth; emit append-only audit before and after the write. Optional A2A: wrap the specialist as an A2A server and propagate `taskId` into keys and audit. Interview artifact = **one successful write + one retry that did not duplicate + one rejected gate + an audit line** — optionally plus an Agent Card URL.
