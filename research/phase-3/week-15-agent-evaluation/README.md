# Week 15 Research Corpus — Agent evaluation (traces, trajectory vs outcome, failure patterns)

> Phase 3 — Agentic Systems  
> **Status:** COMPLETE (deep pass)  
> Raw research corpus (not textbook). Legal sources only; no pirated books.

This directory is the Week 15 research repository. Read concept files in order, then the source map. **Do not start Week 16 (error-analysis flywheel) from this corpus** — this week **instruments both existing agentic systems** and scores **tool-call correctness**, trajectory vs outcome, and named failure patterns. The flywheel that *mines* those failures into a taxonomy and synthetic data is next week.

| # | File | Concept |
|---|------|---------|
| 00 | [00-week-overview.md](00-week-overview.md) | Instrument **both** agentic systems; tool-call correctness as the first eval layer |
| 01 | [01-evaluating-agentic-traces.md](01-evaluating-agentic-traces.md) | Traces / transcripts; structured tool-call graders; match modes vs LLM-as-judge |
| 02 | [02-trajectory-vs-outcome-eval.md](02-trajectory-vs-outcome-eval.md) | Path vs environment state; pass@k vs pass^k; hybrid scoring |
| 03 | [03-agent-failure-patterns.md](03-agent-failure-patterns.md) | Tool misuse, infinite loops, premature stop, context loss |
| 04 | [04-agent-benchmarks.md](04-agent-benchmarks.md) | τ-bench / τ²-bench, WebArena, AgentBench (research, not name-drops) |
| — | [99-source-map.md](99-source-map.md) | Master URL / paper / blog / YouTube index |

## Completeness checklist (Week 15)

- [x] All syllabus Week 15 concepts covered with **7 required fields**  
- [x] **Instrument both agentic systems** (Week 11 loop agent + Week 14 side-effecting agent) with structured traces  
- [x] **Tool-call correctness evals** (name, arguments, result, resulting state; order / policy invariants)  
- [x] **Trace grading** (OpenAI traces; LangSmith `agentevals`; Langfuse tool-call fields + four dimensions)  
- [x] **Trajectory vs outcome** (Anthropic transcript vs SQL/environment; Hamel E2E-then-steps)  
- [x] **Failure patterns:** tool misuse, infinite loops / retry storms, premature stopping, context loss  
- [x] **Benchmarks researched:** τ-bench / τ²-bench (DB state, user sim, pass^k), WebArena (functional / backend checks), AgentBench (8 envs, ICLR’24)  
- [x] LangSmith trajectory evals (`strict` / `unordered` / `subset` / `superset`) cited  
- [x] Langfuse agent evaluation (trajectory, tool use, task completion, multi-turn) cited  
- [x] Anthropic *Demystifying evals for AI agents* + *Building effective agents* cited  
- [x] OpenAI agent-evals / traces workflow cited  
- [x] Hamel / Shankar agentic-workflow + multi-step FAQ cited  
- [x] YouTube: Hamel evals talks; Chase AI Engineer; DLAI A2A; Bischof/Hamel experiment-roadmap lesson cited  
- [x] Per-week research **directory** (not a single thin file)  
- [x] `_PRIOR_SINGLE_FILE.md` removed after expansion  

## Syllabus build task (Week 15)

Do **not** ship a third agent. **Instrument and score the two you already have.**

1. **Wire traces** on the Week 11 loop agent **and** the Week 14 write agent (LangSmith **or** Langfuse **or** OpenAI traces — one primary, map the other). Tool calls must be **structured fields** (`name`, `arguments`, …), not parsed chat text. Session IDs on the conversational agent.  
2. Define **split scores**, never one “quality” number: `task_success` (outcome / read-back), `tool_name`, `tool_args`, `policy_order` (e.g. `verify_identity` before `commit_refund`), `within_step_budget`, cost/turns.  
3. Add **tool-call correctness** tests: Hamel’s four checks (name, arguments, result, resulting state) plus authorization/preconditions. Use **code graders** for decidable checks; LLM-as-judge only for semantic appropriateness.  
4. On the **same** refund (or ticket/calendar) task, show **one strict trajectory assertion** and **one environment outcome assertion** side by side — Anthropic: path can be too rigid; outcome without path misses unsafe intermediates.  
5. Codify the **four failure patterns** as regression cases (loop detector, premature-stop outcome fail, missing tool, dropped early constraint). Promote at least one **real** failing prod/dev trace into the dataset.  
6. **Literacy assignment (not a product gate):** read τ-bench (state + pass^k), WebArena (functional / backend), AgentBench (cross-env). Do **not** claim you “beat WebArena” as a shipping criterion.

Do **not** skip this week for “we’ll look at LangSmith later.” Week 16 error analysis has nothing to annotate if traces are unstructured.

## Default path (synthesis)

1. **Instrument first.** If tools are not structured on the observation, you cannot grade them ([Langfuse tool-call eval](https://langfuse.com/resources/engineering/ai-agent-evaluation); [OpenAI trace grading](https://developers.openai.com/api/docs/guides/agent-evals)).  
2. **Outcome is the store** (Week 14 read-back). Trajectory is the **path and policy** ([Anthropic](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)). Score both independently ([Langfuse four dimensions](https://langfuse.com/resources/engineering/ai-agent-evaluation)).  
3. Hamel order: **E2E task success first**, then step diagnostics and **transition failure matrices** ([agentic workflows FAQ](https://hamel.dev/blog/posts/evals-faq/how-do-i-evaluate-agentic-workflows.html)).  
4. Prefer **code** graders for tool name/schema/budget; **LLM judge** for reasonableness — then calibrate judges against humans ([Hamel YouTube](https://www.youtube.com/watch?v=DZxaPNYi_k0); Anthropic grader triad).  
5. Use LangSmith match modes with intent: `strict` for policy order, `unordered` for independent reads, `subset` for no extras, `superset` for required actions ([trajectory evals](https://docs.langchain.com/langsmith/trajectory-evals)). Anthropic: do not over-use strict sequences.  
6. Interview artifact = **a table of split scores on both agents** + one refund task that **fails trajectory / passes outcome** (or vice versa) + a named failure (loop or skipped `verify_identity`).
