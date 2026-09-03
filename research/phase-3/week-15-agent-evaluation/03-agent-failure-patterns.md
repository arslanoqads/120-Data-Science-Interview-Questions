# 03 — Common agent failure patterns

> Week 15 — Tool misuse, infinite loops, premature stop, context loss  
> Research notes (raw).

---

## Fundamentals

These patterns are the **named bugs** that trace + outcome evals exist to catch. They recur across Anthropic, Langfuse, Hamel, τ-bench analyses, WebArena error discussion, and AgentBench’s “typical reasons of failures.” Teach them as **labels you attach to traces**, then (Week 16) count them. This week: **recognize, instrument, write a regression case**.

### C1. Tool misuse

**What it looks like**

- Wrong tool selected (search vs update; `cancel_order` vs `refund`).  
- Right tool, **wrong arguments** (IDs, dates, amounts, filters, city aliases that map to the wrong entity).  
- Skipping **precondition** tools (`verify_identity`, preview, policy fetch).  
- Calling **write** tools when a read would suffice (or vice versa — answering from parametric memory when retrieval was required).  
- Ignoring tool **errors / empty results** and hallucinating success (Hamel: error handling as its own check).  
- **Over-trigger / under-trigger** (Anthropic web-search evals: search when you should vs answer from knowledge).  
- RAG-agent special case (Langfuse): skip retrieval, rewrite the query into something the index cannot serve, or loop retrieve without converging.

**Why it happens:** overlapping tool descriptions (bad ACI — Anthropic Appendix 2 / *Building effective agents*); schema too loose; no poka-yoke; policy only in the prompt.

**Eval hooks**

- Tool **name** assertions; JSON schema validation; semantic arg checks (ID in allowlist; amount ≤ policy).  
- Hamel: **name / arguments / result / resulting state** + authorization.  
- LangSmith `strict` or explicit order for verify-then-refund; `subset` to ban extra payment tools.  
- Langfuse boolean `used_search_tool` on structured `tool_calls`.  
- State read-back: tool JSON said cancelled; **status still open**.  
- Anthropic support YAML: required `verify_identity`, `process_refund` with `amount <= 100`, `send_confirmation`.

### C2. Infinite loops / retry storms

**What it looks like**

- Repeated **identical** failing tool calls.  
- Oscillation between two tools without progress (`search` ↔ `refine_query`).  
- Re-entering propose/commit after `already_consumed` (Week 14 token) or after idempotent “same key” without noticing.  
- No **max-turn / max-tool** budget (Week 11 stopping conditions).  
- Langfuse aggregated graph: cycle edges; `retrieve_docs (12/12)`.

**Why it happens:** empty tool result not treated as a branch; missing circuit breaker; model “tries again” instead of clarifying; harness does not surface errors as observations.

**Eval hooks**

- Langfuse quantitative trajectory: step count, **loop detection**, `within_step_budget`.  
- Transcript metrics `n_turns`, `n_toolcalls`, tokens (Anthropic tracked_metrics).  
- Harness **hard stops** (Anthropic stopping conditions in *Building effective agents*).  
- Code: hash `(tool_name, canonical_args)` and fail if identical failure repeats ≥ N.  
- Distinguish **legitimate exploration** (different queries) from **storms** (same payload).

### C3. Premature stopping

**What it looks like**

- Agent ends the turn before the goal is complete (“I’ve started the process…”).  
- Partial multi-step workflow (identified the issue, **did not refund**).  
- Exits on **ambiguous** tool output instead of clarifying or retrying with a different tool.  
- Conversational: five locally reasonable turns that never **resolve the session** (Langfuse multi-turn).  
- Coding: stops before tests are run (Anthropic coding example requires `run_tests` in tool_calls).

**Why it happens:** stop condition is “model emitted a final message,” not “environment matches goal”; no min-required-actions; user-sim or UI accepts a polite close.

**Eval hooks**

- **Outcome** state checks (ticket `resolved`, refund `processed`).  
- Goal checkpoints / partial credit (Anthropic; Hamel).  
- `superset` trajectory: required tools must appear.  
- Session scores: `resolved` / `escalated` / `abandoned` (Langfuse categorical).  
- `max_turns` **and** min-required-actions — budget alone can encourage **early exit**.  
- τ-bench: episode ends on user `###STOP###` then **DB compare** — if the agent stopped chatting without writing, reward is 0.

### C4. Context loss across long horizons

**What it looks like**

- Drops earlier constraints (budget, user preferences, prior confirmations, “don’t email the customer”).  
- Forgets entities already created → **duplicates** (Week 14 idempotency is the infra mitigation; eval still needs a case).  
- Multi-turn **goal drift**: answers each turn locally, never session-resolves.  
- Summarization / memory truncation removes **critical IDs**.  
- Handoffs (Week 13 / A2A): peer does not receive constraints — DLAI A2A course surface.

**Why it happens:** context windows; naive summarization; session not the eval unit; AgentBench authors: **poor long-term reasoning** is a main obstacle ([ICLR’24](https://arxiv.org/abs/2308.03688)). WebArena: long-horizon multi-site tasks; GPT-4 14.41% vs human 78% — authors hypothesize weak **exploration and failure recovery**.

**Eval hooks**

- Session-level scores (Langfuse `session_id`).  
- Tasks that inject a constraint in turn 1 and **require it in turn 8** (Hamel **context retention** diagnostic).  
- AgentBench OS/DB/web long interactive tasks; WebArena multi-step (Wikipedia → map → GitLab README).  
- τ-bench long conversations + policy doc in context — failures include **not following ad-hoc policies** and **compound requests**.  
- Trace: did the commit args still match the **preview** payload from earlier (Week 14 parity)?

### C5. Related patterns (teach, don’t collapse into C1–C4)

| Pattern | Signal | Notes |
|---------|--------|-------|
| **Eval hacking / loopholes** | Pass graders without real solve | Anthropic: make graders resistant to bypasses; τ² policy loophole |
| **Harness/environment flakiness** | Correlated failures across “independent” trials | Shared state, leftover files, CPU; Claude reading prior-trial git history |
| **Brittle graders** | Valid format / path punished | CORE-Bench float; METR threshold wording |
| **Unsafe but successful paths** | Outcome green, trajectory red | The Week 15 teaching contrast |
| **Over-refusal** | Balanced evals needed | Anthropic should/should-not sets |
| **Instruction-following collapse** | AgentBench: OSS models vs GPT-4 gap | Multi-turn alignment data helps (paper) |

### Mitigations (not a substitute for evals)

| Failure | Mitigation | Tradeoff |
|---------|------------|----------|
| Tool misuse | Better ACI/docs; fewer overlapping tools; schema strictness; poka-yoke args | Upfront tool-design cost |
| Loops | Max iterations; repeated-call detector; circuit breakers | May stop recoverable retries early |
| Premature stop | Explicit completion criteria; outcome graders; required tool supersets | Longer average trajectories / cost |
| Context loss | External state store; periodic goal restatement; session evals | Memory noise |
| Duplicates | Idempotency + audit (Week 14) | Infra dependency |

---

## Alternatives & Tradeoffs

| Debugging style | Pros | Cons |
|-----------------|------|------|
| One viral prompt fix | Fast | Same pattern returns next week |
| **Taxonomy + regression cases** (syllabus) | Compounds | Needs traces and labels |
| Only outcome SLOs | Ships “works” | Misses C1 unsafe paths, C2 cost, C4 drift |
| Only loop/budget metrics | Cheap | Green loops that still fail the user |
| Transition matrices (Hamel/Bischof) | Shows **where** the funnel drops | Needs agreed states |
| Agent graph visual (Langfuse) | Fast loop spotting | Not a score |

Hamel/Shankar **error analysis** (YouTube): look at traces, free-form notes, **then** categories — do not start with a universal “accuracy” bar ([Intro to error analysis](https://www.youtube.com/watch?v=qH1dZ8JLLdU); full flywheel is Week 16).

---

## Necessity

These patterns dominate production incidents for **side-effecting** agents. Benchmarks that only score final text **under-detect** them — hence WebArena **backend** checks, τ-bench **DB state**, trajectory tooling in LangSmith/Langfuse/Vertex, and Anthropic’s required `verify_identity` even when money moved.

Without names, teams file “agent was weird” tickets. With names, you can say: **12/20 failures are C2 on `commit_refund`** and write a `within_step_budget` gate.

AgentBench (Liu et al.): poor **long-term reasoning, decision-making, and instruction following** are the main obstacles — that maps onto C4 + C1 + C3.

---

## Industry Practice

- **Common:** fix one-off prompt after a viral failure.  
- **Strong (Anthropic roadmap + Hamel):**  
  1. Start with **20–50** tasks from **real failures**.  
  2. Record **first upstream failure**.  
  3. Build **transition failure matrices**.  
  4. Codify as regression tests (capability → regression graduation).  
  5. Code graders + calibrated LLM judges + periodic human review.  
  6. **Always read transcripts** when scores move (fair failures).  
- **FDE bar:** one fixture per C1–C4 on **both** agents (loop on the Week 11 search agent; skipped verify on the Week 14 write agent; premature close on a ticket; dropped budget constraint on a multi-turn shopper).

Langfuse: when you find a bad trajectory, add the input to a dataset and write the violated property (“must not call the payment tool twice”).

---

## Concrete Scenario

**C1 policy skip** — Anthropic support agent: missing `verify_identity` is a trajectory fail even if money moves.  
https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents  

**C2 budgets** — Langfuse `within_step_budget`, loop detection, aggregated graph cycle edges.  
https://langfuse.com/resources/engineering/ai-agent-evaluation  

**C3 / C4 long horizon** — WebArena multi-step site tasks (e.g. Wikipedia + map + GitLab README); AgentBench OS/DB/web.  
https://webarena.dev/ · https://github.com/THUDM/AgentBench · https://arxiv.org/abs/2307.13854 · https://arxiv.org/abs/2308.03688  

**τ-bench failures** (paper): complex DB reasoning, **ad-hoc policy**, **compound requests** — mix of C1 and C4.  
https://arxiv.org/abs/2406.12045  

**Transition matrices** — https://hamel.dev/blog/posts/evals-faq/how-do-i-evaluate-agentic-workflows.html — Bischof *Failure is a Funnel*, Data Council 2025 (cited there; lesson with Hamel: [Maven](https://maven.com/p/9b1bab/stop-managing-ai-projects-like-traditional-software)).

**YouTube / course:** DeepLearning.AI A2A trailer (handoffs drop context) — https://www.youtube.com/watch?v=4gYm0Rp7VHc · https://goo.gle/dlai-a2a  
Hamel error analysis — https://www.youtube.com/watch?v=qH1dZ8JLLdU  
Chase cost-if-wrong (unsafe tools) — https://www.youtube.com/watch?v=kTnfJszFxCg  

---

## Open Questions

- Automatic loop classifiers that don’t flag **legitimate** exploratory search?  
- How to eval **memory systems** separately from the policy model?  
- Standardized **incident → dataset** labels across vendors (shared C1–C4)?  
- Multi-agent: is context loss at the **handoff boundary** a different class than intra-agent truncation?  
- Dual-control τ²: user-tool mistakes vs agent C1 — attribution?

---

## Sources

- https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents  
- https://www.anthropic.com/engineering/building-effective-agents  
- https://langfuse.com/resources/engineering/ai-agent-evaluation  
- https://docs.langchain.com/langsmith/trajectory-evals  
- https://hamel.dev/blog/posts/evals-faq/how-do-i-evaluate-agentic-workflows.html  
- https://hamel.dev/blog/posts/evals-faq/how-do-i-evaluate-complex-multi-step-workflows.html  
- https://webarena.dev/  
- https://arxiv.org/abs/2307.13854  
- https://github.com/THUDM/AgentBench  
- https://arxiv.org/abs/2308.03688  
- https://github.com/sierra-research/tau-bench  
- https://arxiv.org/abs/2406.12045  
- https://developers.openai.com/api/docs/guides/agent-evals  
- https://www.youtube.com/watch?v=4gYm0Rp7VHc  
- https://www.youtube.com/watch?v=qH1dZ8JLLdU  
- https://www.youtube.com/watch?v=kTnfJszFxCg  
- https://maven.com/p/9b1bab/stop-managing-ai-projects-like-traditional-software  
