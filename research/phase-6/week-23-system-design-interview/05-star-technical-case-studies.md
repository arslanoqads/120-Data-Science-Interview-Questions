# 05 — STAR-format technical case studies from production builds

> Week 23 — System design interview  
> Research notes (raw). Meta-concept: packaging Weeks 6–22 work into drillable behavioral/technical stories. Full story bank lives in [00-week-overview.md](00-week-overview.md).

---

## Fundamentals

STAR = **Situation, Task, Action, Result** (+ **Learning** for senior). For AI Engineer / FDE, stories must be **technically drillable**: metrics, alternatives rejected, your personal actions, failure modes.

Amazon-oriented public coaching (useful beyond Amazon) stresses:

- Action ≈ majority of airtime; say **“I”** not “we.”  
- Quantify: latency, error rate, cost, time-to-value, eval pass rate.  
- Survive 2–3 follow-up depths (logs, queries, tradeoffs).  
- Keep a bank of ~8–10 stories mapped to themes: incident, ambiguity, stakeholder conflict, tech debt, customer unblock, quality flywheel.

Amazon’s own interviewing guidance hub frames behavioral / LP-style storytelling ([Interviewing at Amazon](https://www.amazon.jobs/content/en/how-we-hire/interviewing-at-amazon)). Engineering-oriented STAR explainers: [PracHub](https://prachub.com/resources/what-is-the-star-method-for-behavioral-interviews-with-faang-examples-2); [Leonstaff LP examples](https://leonstaff.com/blogs/amazon-leadership-principles-star-examples-engineers/).

### Capstone → STAR extraction recipe

1. Pick one **eval-driven fix** from Week 22 (or earlier week).  
2. Write STAR with **before/after metric**.  
3. Name the alternative you did **not** take (e.g., “didn’t fine-tune; fixed chunk boundaries”).  
4. List **3 follow-up bullets** (how measured, what still fails, ops cost).  
5. Dual-end: one Applied AI punchline (harness/latency/architecture) + one FDE punchline (discovery/constraint/rollout/codify).

### Own-build bank (index)

Nine primary + one optional stories are fully tabulated in the overview — titles only here for rehearsal order:

| # | Title | Theme | Primary metric shape |
|---|-------|-------|----------------------|
| 1 | Chunk boundaries beat fine-tuning | Quality flywheel | Faithfulness % |
| 2 | Hybrid BM25 for exact error codes | Retrieval | recall@k on ID slice |
| 3 | Rerank inside a 2s budget | Latency/cost | p95, $/1k |
| 4 | Filter ACL before rank | Security / tenancy | Leak suite pass |
| 5 | Citation off-by-one from taxonomy | Evals | Fake-citation count |
| 6 | Idempotent ticket create | Side effects | Duplicate rate |
| 7 | MCP adapter on undocumented API | Customer unblock | Time-to-pilot |
| 8 | Semantic layer before text-to-SQL | Messy integration | SQL error rate |
| 9 | Scope freeze over feature sprawl | Ambiguity / focus | Demo stability |
| 10 | Semantic cache + routing (optional) | Cost | $/1k, hit rate |

Map stories to employer language:

- Palantir FDSE: https://blog.palantir.com/a-day-in-the-life-of-a-palantir-forward-deployed-software-engineer-45ef2de257b1  
- Anthropic FDE: https://job-boards.greenhouse.io/anthropic/jobs/5391016008  
- OpenAI FDE: https://openai.com/careers/forward-deployed-engineer-%28fde%29-sf-san-francisco/  

### One-page story index fields

Keep a card per story:

- Title  
- Metric (before → after)  
- Systems touched  
- Failure mode  
- Alternative rejected  
- 3 follow-up bullets  
- Applied ending / FDE ending  

Chip Huyen interview materials emphasize systems thinking and portfolio signal over trivia ([ML interviews book site](https://huyenchip.com/ml-interviews-book/); [YouTube `pli1K75PSa8`](https://www.youtube.com/watch?v=pli1K75PSa8)).

### Timing

Aim **2–3 minutes** before pause for questions. If uninterrupted past 4 minutes, you are over-narrating Situation. Cut setup; expand Action + Result.

---

## Alternatives & Tradeoffs

| Story type | Good for | Risk |
| --- | --- | --- |
| Outage / rollback | Ownership, incident muscle | Don’t blame teammates |
| Eval taxonomy → fix | Applied AI Engineer signal | Need real numbers |
| Customer integration unblock | FDE signal | Don’t violate NDAs; anonymize |
| Build vs buy decision | Judgment | Avoid fanboy vendor tales |
| Failed experiment | Learning / humility | Must show updated process |
| Pure interpersonal conflict | Classic LP rounds | Weak in AI labs if no technical consequence |

Anthropic values rounds (public candidate reports) may punish pure STAR “team conflict” theater if it ignores model failure modes / safety—**pair technical consequence** with interpersonal stories.

| Packaging choice | Pros | Cons |
|------------------|------|------|
| Own-build only | Drillable | Thin if metrics never recorded |
| Invented metrics | Smooth | Ethical + credibility risk — don’t |
| Anonymized customer | FDE-safe | Still need technical depth |
| Dual-track endings | Apply broadly | Rehearse both or stumble |

---

## Necessity

Without STAR packaging, strong builds stay invisible. With empty STAR (no metrics/tradeoffs), packaging backfires under follow-up. Week 24 resume language depends on this bank — extract evidence **here**, polish wording later.

---

## Industry Practice

| Bar | What it looks like |
|-----|--------------------|
| **Common** | “We built a chatbot with LangChain”; no numbers |
| **Strong** | 8–10 cards; I-language; metric; rejected alternative; follow-ups |
| **Senior / FDE** | Dual endings; safety/ACL story; codify-back-to-product story; incident with rollback |

Prepare dual endings:

- **Applied AI:** harnesses, latency/cost, architecture decisions.  
- **FDE:** discovery, constraint navigation, production rollout, pattern codification.

Hamel-style error analysis is itself a story engine: taxonomy count → fix → regression ([evals](https://hamel.dev/blog/posts/evals/); Field Guide patterns).

---

## Concrete Scenario (URL)

**Before packaging:** Capstone README says “improved retrieval.”  
**After STAR 2:** “Dense-only miss on error codes; I added BM25+RRF and an ID eval slice; recall@5 41%→93%; rejected sparse-only because FAQ NDCG would fall; follow-up-ready on fusion weights.”

STAR method explainers:

- https://prachub.com/resources/what-is-the-star-method-for-behavioral-interviews-with-faang-examples-2  
- https://leonstaff.com/blogs/amazon-leadership-principles-star-examples-engineers/  
- https://www.amazon.jobs/content/en/how-we-hire/interviewing-at-amazon  

Interview / systems framing:

- https://huyenchip.com/ml-interviews-book/  
- https://www.youtube.com/watch?v=pli1K75PSa8  
- https://hamel.dev/blog/posts/evals/  

---

## Open Questions

- How “production” must a personal project be to count in frontier-lab loops?  
- Should safety/values stories be separate from technical STAR bank?  
- Optimal story length before interviewer interrupts (often ~2–3 minutes)?  
- How many stories is too many to maintain (staleness of metrics)?

---

## Sources

- PracHub STAR / FAANG examples: https://prachub.com/resources/what-is-the-star-method-for-behavioral-interviews-with-faang-examples-2  
- Leonstaff Amazon LP STAR for engineers: https://leonstaff.com/blogs/amazon-leadership-principles-star-examples-engineers/  
- Amazon interviewing guidance: https://www.amazon.jobs/content/en/how-we-hire/interviewing-at-amazon  
- Chip Huyen ML interviews book: https://huyenchip.com/ml-interviews-book/  
- Chip Huyen ML interviews (YouTube): https://www.youtube.com/watch?v=pli1K75PSa8  
- Hamel evals: https://hamel.dev/blog/posts/evals/  
- Palantir FDSE: https://blog.palantir.com/a-day-in-the-life-of-a-palantir-forward-deployed-software-engineer-45ef2de257b1  
- Anthropic FDE: https://job-boards.greenhouse.io/anthropic/jobs/5391016008  
- OpenAI FDE SF: https://openai.com/careers/forward-deployed-engineer-%28fde%29-sf-san-francisco/  
- Generative AI system design question bank (practice): https://prachub.com/resources/generative-ai-system-design-interview-questions-rag-agents-evals-and-guardrails  
