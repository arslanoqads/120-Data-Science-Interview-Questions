# 01 — Resume language that mirrors AI Engineer / FDE postings

> Week 24 — Portfolio positioning  
> Research notes (raw). Meta-concept: ATS-and-human screeners scan for **production AI system verbs** backed by metrics — not course certificates.

---

## Fundamentals

Resume language for Applied AI Engineer and Forward Deployed Engineer roles must **mirror primary postings** while remaining defensibly true in a deep-dive. Invented keywords fail the first technical screen; generic SWE bullets get filtered out of AI/FDE piles.

### Phrase clusters → resume shape

| Phrase cluster | Where it shows up | Resume translation (shape — invent your facts from STAR) |
| --- | --- | --- |
| **RAG / retrieval** | Nearly all Applied AI postings; Huyen / Anthropic public tech writing | “Shipped hybrid BM25+dense retrieval with rerank; measured recall@k / faithfulness on a golden set” |
| **Eval harness / evaluation frameworks** | Anthropic FDE; Hamel-aligned product culture | “Built offline golden-set + trace triage taxonomy; CI gate on prompt/retrieval changes” |
| **Agent orchestration** | Anthropic (agents, MCP, skills); OpenAI deployment language | “Orchestrated tool-calling agent with retries/stop conditions; logged trajectories” |
| **MCP / tools in customer env** | Anthropic FDE responsibilities | “Delivered MCP server / tool adapter over customer system X; contract tests before prod” |
| **Cost / latency** | Platform + FDE delivery reality | “Cut p95 from Xs→Ys via cache/routing; tracked $/1k queries” |
| **Production deployment** | OpenAI FDE end-to-end rollout; Palantir field engineering | “Deployed to [env]; auth, monitoring, rollback; on-call style ownership” |
| **Customer-facing / ambiguity** | All FDE postings | “Scoped pilot with stakeholders; delivered thin slice under changing constraints” |
| **Codify patterns back to product** | Palantir + OpenAI + Anthropic FDE | “Turned engagement-specific adapter into reusable template/playbook” |

### Primary posting verbs to steal (legally — paraphrase with your evidence)

**OpenAI FDE** ([SF](https://openai.com/careers/forward-deployed-engineer-%28fde%29-sf-san-francisco/); [NYC](https://openai.com/careers/forward-deployed-engineer-%28fde%29-nyc-new-york-city/); [Gov](https://openai.com/careers/forward-deployed-engineer-gov-washington-dc/)):

- Own discovery → technical scoping → system design → build → **production rollout**  
- Production adoption, measurable workflow impact, **eval-driven feedback**  
- Embed with customer teams; guide adoption  
- Trade-offs among scope, speed, quality  
- **Codify** working patterns into tools / playbooks / building blocks  
- Share field feedback to Research / Product  
- Travel up to ~50% (SF posting); hybrid office model  

**Anthropic FDE / Applied AI** ([Greenhouse](https://job-boards.greenhouse.io/anthropic/jobs/5391016008)):

- Build **production applications with Claude** inside customer systems  
- Deliver **MCP servers, sub-agents, agent skills**  
- White-glove enterprise deploy  
- **Evaluation frameworks**; prompt engineering; agent development at scale  
- Codify repeatable deployment patterns back to Product / Engineering  
- Travel **25–50%**; thrive under ambiguity  

**Palantir FDSE** ([Day in the Life](https://blog.palantir.com/a-day-in-the-life-of-a-palantir-forward-deployed-software-engineer-45ef2de257b1); [Who wants to be a Delta](https://blog.palantir.com/who-wants-to-be-a-delta-8d2ea948035)):

- Embed with customer; integrate data; access controls  
- Production rigor / outages; compose platform capabilities  
- Field learnings → product  

### Bullet formula

```
Verb + system component + constraint + metric + failure/learning hook
```

**Example shape:** “Hardened RAG ingest for ACL-aware hybrid retrieval; raised golden-set pass rate 62%→84% by fixing chunk-boundary misses found in error analysis.”

**Weak:** “Worked on RAG chatbot using LangChain and OpenAI.”  
**Stronger:** “Shipped hybrid retrieval + citation aligner for internal KB; faithfulness 58%→81% after open-coding 40 traces; p95 held under 2s.”

### Resume structure that survives AI Eng / FDE screens

1. **Header** — name, email, LinkedIn, GitHub, portfolio ([qads.us](https://qads.us) case URL).  
2. **Summary (2–3 lines)** — track noun + one system claim + one customer/production claim if FDE.  
3. **Skills** — clustered (retrieval/evals/agents; languages; cloud; identity) — not a dump.  
4. **Experience** — reverse chrono; 3–5 AI system bullets lead.  
5. **Projects** — flagship with metrics if day job is not yet AI-titled.  
6. **Education** — short; coursework does not lead.

Chip Huyen’s framing: AI engineering is **adapting foundation models into systems** (integration, evals, guardrails), not training models from scratch — resume language should reflect shipped systems ([GenAI platform](https://huyenchip.com/2024/07/25/genai-platform.html); [ML interviews](https://huyenchip.com/ml-interviews-book/)).

---

## Alternatives & Tradeoffs

| Resume strategy | Pros | Cons |
| --- | --- | --- |
| Mirror keywords densely | Passes screens | Sounds fake if bullets lack metrics |
| Pure generic SWE bullets | Safe for classic SWE piles | Filtered out of AI/FDE piles |
| Research-paper heavy | Helps research tracks | Weak for Applied/FDE unless tied to shipped systems |
| Dual header (“Applied AI / FDE”) | Dual apply | Dilutes if no evidence for both |
| Two tailored resumes | Higher match per posting | Maintenance cost |
| “Prompt Engineer” title lead | Rarely helpful in 2026 | Can read as non-systems / fad title |

**Title nouns that usually help:** Applied AI Engineer, AI Engineer, Forward Deployed Engineer, Field Engineer (AI), ML Platform / LLM Application Engineer.  
**Title nouns to use carefully:** Prompt Engineer (prefer as a *skill inside* a systems bullet), Solutions Architect (may read non-coding unless coding evidence is loud).

---

## Necessity

Without mirrored language, strong projects get miscategorized as hobby chatbots. Without evidence behind keywords, mirrored language fails the first technical screen and destroys trust in onsite loops. Without at least one **stakeholder + integration + production** bullet, FDE piles reject strong Applied-only resumes.

---

## Industry Practice

| Bar | What it looks like |
|-----|--------------------|
| **Common** | “Familiar with LLMs”; certificate row; tool laundry list |
| **Strong** | 3–5 system bullets with metrics; stack explained as decisions; personal “I” ownership |
| **Senior / FDE** | Ambiguity + scoping + rollout + codify; eval frameworks named; travel willingness when relevant |

Practical rules:

- Put **tech stack in context of decisions** (why hybrid, why judge type), not laundry lists.  
- Lead with AI system bullets; bury coursework and bootcamp names.  
- For FDE, one bullet must show **stakeholder + integration + production**.  
- For Anthropic-targeted apps, MCP / eval frameworks as first-class bullets when true.  
- Comp research ([Levels.fyi FDSE](https://www.levels.fyi/companies/palantir/salaries/software-engineer/title/fdse); [Perspective secondary synthesis](https://getperspective.ai/blog/2026-forward-deployed-engineering-compensation-report-1200-fdes)) is for negotiation context later — **not resume content**. Treat crowdsourced TC as directional only.  
- Secondary FDE resume guides (Exponent, FDE Academy, roadmaps) are useful for *structure*; prefer primary posting verbs over blog templates ([Exponent FDE resume](https://www.tryexponent.com/blog/forward-deployed-engineer-resume); [FDE Academy guide](https://fde.academy/blog/forward-deployed-engineer-resume-portfolio-interview-guide)).

### Keyword mirror checklist (paste against a live posting)

- [ ] RAG / hybrid retrieval / rerank  
- [ ] Eval harness / golden set / error analysis / evaluation frameworks  
- [ ] Agent orchestration / tools / MCP (if posting mentions)  
- [ ] Latency p95 + cost metric  
- [ ] Production deploy / monitoring / rollback  
- [ ] Security/ACL or enterprise constraint  
- [ ] Customer or stakeholder language (FDE)  
- [ ] Codify / playbook / reusable pattern (FDE)  
- [ ] Quantified result + personal ownership (“I”)  
- [ ] Portfolio / GitHub / qads.us link in header  

---

## Concrete Scenario (URL)

**Exercise:** Open the Anthropic FDE posting and OpenAI FDE SF posting side by side. Highlight every production verb. For each highlight, either (a) write a bullet from your Week 23 STAR bank or (b) mark “no evidence — do not claim.” Then rewrite your summary line for Applied-only vs FDE-only applications.

Primary postings:

- https://openai.com/careers/forward-deployed-engineer-%28fde%29-sf-san-francisco/  
- https://openai.com/careers/forward-deployed-engineer-%28fde%29-nyc-new-york-city/  
- https://openai.com/careers/forward-deployed-engineer-gov-washington-dc/  
- https://job-boards.greenhouse.io/anthropic/jobs/5391016008  
- https://blog.palantir.com/a-day-in-the-life-of-a-palantir-forward-deployed-software-engineer-45ef2de257b1  

Chip Huyen role / interview expectations:

- https://huyenchip.com/ml-interviews-book/  
- https://www.youtube.com/watch?v=pli1K75PSa8  

Eval culture language:

- https://hamel.dev/blog/posts/evals/  

---

## Open Questions

- Is “Prompt Engineer” still harmful as a headline on a 2026 Applied AI / FDE resume?  
- Should MCP appear as a first-class bullet for all Anthropic-targeted apps, or only when the posting lists it?  
- One resume vs two tailored resumes when spraying both tracks the same week?  
- How much internal “customer” (PM, support ops) language counts as FDE stakeholder signal without employer-of-record field work?  
- Do frontier-lab FDE postings overweight years-of-experience vs portfolio depth in practice?

---

## Sources

- https://openai.com/careers/forward-deployed-engineer-%28fde%29-sf-san-francisco/  
- https://openai.com/careers/forward-deployed-engineer-%28fde%29-nyc-new-york-city/  
- https://openai.com/careers/forward-deployed-engineer-gov-washington-dc/  
- https://job-boards.greenhouse.io/anthropic/jobs/5391016008  
- https://blog.palantir.com/a-day-in-the-life-of-a-palantir-forward-deployed-software-engineer-45ef2de257b1  
- https://blog.palantir.com/who-wants-to-be-a-delta-8d2ea948035  
- https://huyenchip.com/ml-interviews-book/  
- https://huyenchip.com/2024/07/25/genai-platform.html  
- https://hamel.dev/blog/posts/evals/  
- https://www.youtube.com/watch?v=pli1K75PSa8  
- https://www.levels.fyi/companies/palantir/salaries/software-engineer/title/fdse  
- https://getperspective.ai/blog/2026-forward-deployed-engineering-compensation-report-1200-fdes  
- https://www.tryexponent.com/blog/forward-deployed-engineer-resume  
- https://fde.academy/blog/forward-deployed-engineer-resume-portfolio-interview-guide  
