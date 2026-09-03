# Week 15 Textbook Chapter — Agent evaluation

> **Status:** COMPLETE  
> **Source:** `research/phase-3/week-15-agent-evaluation/`  
> **Chapter:** [chapter.md](chapter.md)

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
