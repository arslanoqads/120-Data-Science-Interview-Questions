# 04 — Narrating tradeoffs aloud

> Week 23 — System design interview  
> Research notes (raw). Meta-concept: naming axes, picking for constraints, and stating what you monitor — in one breath each.

---

## Fundamentals

Interview signal is rarely the choice itself; it is **naming the axes, picking for stated constraints, and saying what you monitor**. Silent diagrams without tradeoffs read as memorized. Aloud tradeoffs read as design ownership—and match how FDE conversations with customer architects actually go.

### Core AI axes (memorize the monitor column)

| Axis | If you optimize… | You often pay… | Monitor |
| --- | --- | --- | --- |
| **Recall vs precision** (retrieval) | Higher recall@k / more chunks | Noise, lost-in-middle, cost, grounding errors | recall@k, precision@k, faithfulness |
| **Latency vs quality** | Rerank + bigger model + agent loops | p95, $ | stage timings, abandonment |
| **Build vs buy** | Custom index/agents/evals | Ops burden | time-to-value, vendor lock, margins |
| **Freshness vs stability** | Aggressive re-index | Flickering answers, cost | time-to-searchable, churn |
| **Autonomy vs control** | More tools/agent steps | Irreproducibility, safety surface | trajectory evals, human gates |
| **Long context vs RAG** | Stuff / cache large KB | $ and attention limits | Anthropic guidance on when RAG still wins |

ByteByteGo on Agentic RAG: loops are not free—latency, cost, debuggability, evaluator paradox ([Agentic RAG](https://blog.bytebytego.com/p/how-agentic-rag-works)). Anthropic on rerank: better retrieval vs added latency/cost—tune candidate counts ([Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval)). Huyen: start simple; add components when failure modes demand ([GenAI platform](https://huyenchip.com/2024/07/25/genai-platform.html)).

### One-breath templates (fill constraints live)

Practice until these are automatic:

1. **Hybrid + rerank:** “I’d take hybrid+rerank because exact IDs matter; I’ll spend ~150–300ms of a 1.5–2s budget on rerank and cut model size / context to compensate.”  
2. **Build vs buy:** “For FAQ traffic I’d buy managed search + API model; for data-plane actions inside the VPC I’d build the tool/MCP layer ourselves.”  
3. **Precision-first pilot:** “Pilot metric is precision-oriented with abstain; after trust, we raise recall targets.”  
4. **Agentic branch:** “One-shot RAG for FAQ; agentic loop only for multi-hop policy — accept 3–10× latency on that slice ([ByteByteGo](https://blog.bytebytego.com/p/how-agentic-rag-works)).”  
5. **Long context:** “If the working set fits ~200k with caching and changes slowly, skip RAG; past that, retrieval is the product ([Anthropic](https://www.anthropic.com/news/contextual-retrieval)).”  
6. **Eval harness:** “Buy Langfuse/Phoenix for traces early; own golden-set assertions and taxonomy — judges only for subjective residuals ([Hamel](https://hamel.dev/blog/posts/evals/)).”

### Budget tables beat vibes

Strong RAG interview answers allocate a **latency budget** across embed/retrieve/rerank/TTFT and a **cost budget** dominated by context tokens. Weak answers only say “we’ll use Pinecone and GPT-4.” Public rubrics explicitly score naming cost + latency ([technoscripts](https://technoscripts.com/python-rag-system-design/); enterprise rerank-budget notes: [hld.handbook](https://hld.handbook.academy/curriculum/case-studies/enterprise-rag/)).

Mock videos that model tradeoff talk under scale constraints: [semantic search Ep. 45](https://www.youtube.com/watch?v=MUs3JFkevak); Chip Huyen systems design principles [`c_AUuTuPA5k`](https://www.youtube.com/watch?v=c_AUuTuPA5k).

---

## Alternatives & Tradeoffs

| Narration style | Strength | Weakness |
| --- | --- | --- |
| **Axes + pick + monitor** | Hire signal; FDE-shaped | Needs constraints pinned first |
| **Vendor name-drop only** | Fast | No judgment shown |
| **Endless option lists** | Looks broad | Never commits; burns clock |
| **Fake precision numbers** | Sounds senior until drilled | Credibility collapse on follow-up |
| **Approximate but labeled** (“order-of”) | Honest; usually enough | Say assumptions aloud |

Practice templates (fill constraints live) — same as Fundamentals templates; rotate recall/precision vs latency/quality each mock.

---

## Necessity

Without aloud tradeoffs:

- Interviewers assume you memorized a blog diagram.  
- FDE stakeholders cannot trust you in architecture reviews.  
- You cannot defend Week 22 scope cuts (“why no second agent?”).

With empty numbers: tradeoff talk sounds theatrical. Prefer approximate, labeled assumptions over silence or fiction.

---

## Industry Practice

| Bar | What it looks like |
|-----|--------------------|
| **Common** | “We’ll optimize later”; single metric vanity |
| **Strong** | Stage latency table; $/1k; abstain policy; rejected alternative |
| **Senior** | Ties tradeoff to wrong-answer cost and tenant risk; schedules revisit when metrics flip |

Perplexity-style public architecture posts (ByteByteGo) emphasize hybrid retrieval + **model routing** as an explicit quality/cost control — good interview language for “not every query needs the biggest model” ([Perplexity writeup](https://blog.bytebytego.com/p/how-perplexity-built-an-ai-google)).

---

## Concrete Scenario (URL)

**Interviewer:** “Why not agentic RAG for everything?”

**Answer shape:** “Default one-shot hybrid because 80% of traffic is FAQ/ID. Agentic loop for multi-doc policy only — ByteByteGo notes loops multiply latency/cost and hurt debuggability. I’ll route on a classifier, cap iterations, and eval the agent slice separately.”

**Interviewer:** “Why rerank?”

**Answer shape:** “Anthropic measured large failure reductions stacking hybrid contextual retrieval with rerank. I’ll limit candidates so rerank fits ~200ms of a 2s p95 and watch faithfulness vs p95 on a dashboard.”

URLs:

- https://www.anthropic.com/news/contextual-retrieval  
- https://blog.bytebytego.com/p/how-agentic-rag-works  
- https://blog.bytebytego.com/p/how-perplexity-built-an-ai-google  
- https://huyenchip.com/2024/07/25/genai-platform.html  
- https://hld.handbook.academy/curriculum/case-studies/enterprise-rag/  
- https://technoscripts.com/python-rag-system-design/  

---

## Open Questions

- Should candidates lead with cost numbers even when approximate?  
- When is “abstain” the correct precision move vs a product failure?  
- Build-vs-buy for eval harnesses: Langfuse/Phoenix vs in-house?  
- How explicit should vendor lock arguments be in lab interviews?

---

## Sources

- Anthropic Contextual Retrieval: https://www.anthropic.com/news/contextual-retrieval  
- ByteByteGo Agentic RAG: https://blog.bytebytego.com/p/how-agentic-rag-works  
- ByteByteGo Perplexity: https://blog.bytebytego.com/p/how-perplexity-built-an-ai-google  
- ByteByteGo RAG: https://blog.bytebytego.com/p/how-rag-enables-ai-for-your-data  
- Chip Huyen GenAI platform: https://huyenchip.com/2024/07/25/genai-platform.html  
- Hamel evals: https://hamel.dev/blog/posts/evals/  
- Enterprise RAG rerank budget notes: https://hld.handbook.academy/curriculum/case-studies/enterprise-rag/  
- RAG interview layers: https://technoscripts.com/python-rag-system-design/  
- Semantic search mock (YouTube): https://www.youtube.com/watch?v=MUs3JFkevak  
- Chip Huyen MLSys (YouTube): https://www.youtube.com/watch?v=c_AUuTuPA5k  
