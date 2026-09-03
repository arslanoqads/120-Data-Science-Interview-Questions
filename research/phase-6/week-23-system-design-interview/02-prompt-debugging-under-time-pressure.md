# 02 — Prompt debugging under time pressure

> Week 23 — System design interview  
> Research notes (raw). Meta-concept: structured localization for broken RAG/agents and AI-assisted coding rounds.

---

## Fundamentals

Two interview settings share the same skill:

1. **Prompt/system debug round:** broken RAG/agent; find why outputs fail.  
2. **AI-assisted coding round:** you must prompt a model to ship code while narrating.

Under time pressure, strong candidates run a **diagnostic ladder**, not vibes:

1. **Reproduce** with a fixed failing input; write expected vs actual.  
2. **Localize layer**: retrieval miss vs ranking vs grounding vs tool schema vs prompt contradiction vs evaluator bug (reuse Week 9 RAG failure taxonomy).  
3. **Minimize**: strip tools/context until behavior flips.  
4. **Hypothesize aloud** one change; apply; re-run same case.  
5. **Lock regression**: add unit/golden case before moving on.

Chip Huyen’s production LLM theme: prefer **control flow / evals** over prompt magic ([Building LLM Applications for Production](https://huyenchip.com/2023/04/11/llm-engineering.html)). Hamel: ground yourself in **actual errors** before writing more tests or swapping models ([evals](https://hamel.dev/blog/posts/evals/); Lenny’s [`BsWxPI9UM4c`](https://www.youtube.com/watch?v=BsWxPI9UM4c)).

### Layer checklist (say aloud)

| Layer | Symptom | First probe |
|-------|---------|-------------|
| Retrieval miss | Empty / wrong chunks | Inspect retrieved set vs gold doc IDs |
| Ranking / lost-in-middle | Right doc low; model ignores mid context | Rerank; reorder; shrink k |
| Grounding | Fluent lie; bad citations | Faithfulness assert; force quotes |
| Tool schema | Wrong args / retries | Validate JSON schema; check descriptions |
| Prompt contradiction | Refuse + answer; conflicting rules | Diff system prompt sections |
| Evaluator bug | “Fail” on good output | Check judge rubric / reference |

### AI-paired coding tactics (public convergence)

Public Meta-style / AI-coding round writeups converge on:

- Small verified prompts &gt; mega-prompt.  
- Specify stack, files, constraints, tests.  
- Never paste unread diffs — verify every AI edit.  
- Reset context when drift accumulates.  
- Timebox: Understand → Strategy → Code → Verify.

Sources: [Meta AI-round prompting](https://dsa.handbook.academy/curriculum/interview-framework/meta-ai-round-prompting/); [techinterview.org prompting](https://www.techinterview.org/post/3233474912/prompt-engineering-during-coding-interview/); [InterviewEra](https://interviewera.com/blog/ai-prompt-engineering-interview).

### 20-minute planted-failure drill

| Minute | Action |
|--------|--------|
| 0–3 | Reproduce; write expected vs actual on the board |
| 3–8 | Localize layer with evidence (retrieval dump / prompt excerpt / tool trace) |
| 8–14 | One hypothesis; minimal change; re-run |
| 14–18 | Add golden / unit; narrate what you will *not* chase |
| 18–20 | State residual risk + next offline experiment |

---

## Alternatives & Tradeoffs

| Move | When good | When bad |
| --- | --- | --- |
| Jump to bigger model | After confirming retrieval/context OK | Hides root cause; burns time/cost |
| Add few-shot | Format/style failures | Masks missing evidence |
| Raise top-k | Suspected recall miss | Adds noise; may worsen extraction |
| Rewrite prompt | Instruction conflict / refusal policy | Won’t fix absent chunks |
| One-shot “fix everything” AI prompt | Never in interview | Unreviewable; signals loss of control |
| Swap vector DB | Proven infra limit | Premature in 20-minute debug |
| Silence while thrashing | Never | Interviewers score process visibility |

---

## Necessity

Interviewers score **process visibility**. Silent thrashing or blind model swaps read as junior. Structured localization reads as production ownership—especially for FDE, where debugging customer systems under ambiguity is the job ([Palantir FDSE](https://blog.palantir.com/a-day-in-the-life-of-a-palantir-forward-deployed-software-engineer-45ef2de257b1); [Anthropic FDE](https://job-boards.greenhouse.io/anthropic/jobs/5391016008) lists eval frameworks as production LLM experience).

Without a golden lock, “fixed” demos regress before the next round.

---

## Industry Practice

| Bar | What it looks like |
|-----|--------------------|
| **Common** | Rewrite system prompt twice; change temperature; claim fixed |
| **Strong** | Layer hypothesis with evidence; one change; regression case |
| **Senior / FDE** | Separates data bugs from prompt bugs; names severity; schedules offline soak |

- Capstone/product: Hamel-style error analysis on a handful of traces beats prompt roulette.  
- Debugging interviews generally: narrate priorities; state what you will *not* investigate ([interviewnode real-time debugging](https://interviewnode.com/post/real-time-debugging-interviews-what-companies-expect-and-how-to-practice)).  
- Check each company’s **candidate AI-tool policy** before using assistants in-loop (Anthropic values perception varies by posting/year).

---

## Concrete Scenario (URL)

**Planted bug:** Assistant invents a refund policy. Candidate dumps retrieval: top chunks are shipping FAQs; refund PDF never ingested after a path filter bug. Fix = ingest path + golden query — **not** “be more careful” in the prompt.

**Planted bug (tool):** Agent doubles charges. Trace shows timeout retry without idempotency key. Fix = key + status lookup (Week 21), not a longer prompt.

Prompting tactics under timed AI-assisted rounds:

- https://dsa.handbook.academy/curriculum/interview-framework/meta-ai-round-prompting/  
- https://www.techinterview.org/post/3233474912/prompt-engineering-during-coding-interview/  
- https://interviewera.com/blog/ai-prompt-engineering-interview  

Huyen production control: https://huyenchip.com/2023/04/11/llm-engineering.html  
Hamel evals: https://hamel.dev/blog/posts/evals/  

---

## Open Questions

- Will frontier-lab loops standardize “prompt debug” as a named round or keep it inside project deep-dives?  
- How much LLM-as-judge debugging is expected live vs offline?  
- Does using AI tools in the interview help or hurt Anthropic values perception? (Check each company’s candidate AI policy.)  
- Ideal artifact: handwritten ladder vs IDE live share?

---

## Sources

- Chip Huyen LLM engineering essay: https://huyenchip.com/2023/04/11/llm-engineering.html  
- Chip Huyen GenAI platform: https://huyenchip.com/2024/07/25/genai-platform.html  
- Hamel Husain evals: https://hamel.dev/blog/posts/evals/  
- Hamel & Shreya Lenny’s (YouTube): https://www.youtube.com/watch?v=BsWxPI9UM4c  
- Meta AI-round prompting tactics: https://dsa.handbook.academy/curriculum/interview-framework/meta-ai-round-prompting/  
- Prompt engineering during coding interviews: https://www.techinterview.org/post/3233474912/prompt-engineering-during-coding-interview/  
- InterviewEra prompt engineering interview: https://interviewera.com/blog/ai-prompt-engineering-interview  
- Real-time debugging interview expectations: https://interviewnode.com/post/real-time-debugging-interviews-what-companies-expect-and-how-to-practice  
- Anthropic FDE posting: https://job-boards.greenhouse.io/anthropic/jobs/5391016008  
- Palantir FDSE blog: https://blog.palantir.com/a-day-in-the-life-of-a-palantir-forward-deployed-software-engineer-45ef2de257b1  
