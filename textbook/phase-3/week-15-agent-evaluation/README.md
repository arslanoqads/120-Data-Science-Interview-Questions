# Week 15 Textbook Chapter — Agent evaluation

> **Compile:** COMPLETE  
> **Edit:** COMPLETE  
> **Source:** `research/phase-3/week-15-agent-evaluation/`  
> **Chapter:** [chapter.md](chapter.md)

## Editorial checklist

- [x] Continuity reviewed (Week 14: side-effecting write agent, idempotency, confirmation/dry-run, audit logs, optional A2A)  
- [x] Prerequisites Recap added  
- [x] Framing standardized to **What this week builds**  
- [x] Looking ahead → Week 16 (error-analysis flywheel: read outputs, open coding, taxonomy, synthetic edges)  
- [x] Concept structure preserved (6 fields)  
- [x] Language pass for coherence and simplicity  

## Concepts covered

- [x] Instrumenting both agentic systems (tool-call correctness as first eval layer)
- [x] Evaluating agentic traces (structured tool-call graders)
- [x] Trajectory evaluation vs outcome evaluation
- [x] Common agent failure patterns
- [x] Agent benchmarks (τ-bench, WebArena, AgentBench)

## Structure check

Each concept includes Fundamentals, The Alternatives, Failure Modes, Average vs. Strong Engineer, Worked Example, and Apply It.

## Syllabus build

Do **not** ship a third agent. **Instrument and score the two you already have** (Week 11 loop agent + Week 14 write agent): wire structured traces (LangSmith **or** Langfuse **or** OpenAI traces — one primary); define **split scores** (`task_success`, `tool_name`, `tool_args`, `policy_order`, `within_step_budget`, cost/turns); add **tool-call correctness** tests (Hamel’s four checks + authorization); on the same refund/ticket task show one **strict trajectory** assertion and one **environment outcome** assertion side by side; codify the four failure patterns as regression cases; literacy on τ-bench / WebArena / AgentBench without shipping on a public leaderboard. Interview artifact = **split scorecard on both agents** + one trajectory/outcome disagreement + a named failure.
