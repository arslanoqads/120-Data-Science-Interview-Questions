# 03 — Dual-track positioning: Applied AI Engineer vs Forward Deployed Engineer

> Week 24 — Portfolio positioning  
> Research notes (raw). Meta-concept: same underlying skills; **different emphasis and proof artifacts**.

---

## Fundamentals

**Applied AI Engineer** and **Forward Deployed Engineer (FDE)** / **Forward Deployed Software Engineer (FDSE)** share RAG, agents, evals, and production engineering. They diverge on **primary customer**, **success metric**, and **story center of gravity**.

Anthropic sometimes labels the function **Applied AI** while the job title is Forward Deployed Engineer — read the posting body ([Greenhouse FDE](https://job-boards.greenhouse.io/anthropic/jobs/5391016008)). Secondary commentary notes Anthropic’s “Applied” branding signals a research↔deployment continuum rather than pure services ([Perspective Anthropic Applied AI writeup](https://getperspective.ai/blog/anthropic-applied-ai-engineers-forward-deployed-claude-enterprise) — secondary; verify against posting).

### Dimension table

| Dimension | Applied AI Engineer | Forward Deployed / Applied AI FDE |
| --- | --- | --- |
| **Primary customer** | Internal product / platform users | External enterprise / gov customer |
| **Success metric** | Product quality, latency, cost, reliability at scale | Time-to-value in customer env; adoption; patterned reuse |
| **Core artifacts** | Eval harness, RAG/agent services, observability, CI | Adapters, MCP/tools in customer VPC, pilot playbooks, stakeholder demos |
| **Interview center of gravity** | System design, deep project, coding, evals | Coding + **customer scenario** + integration judgment + communication |
| **Resume north star** | “I ship and measure AI systems” | “I unblock and productionize AI inside messy orgs” |
| **Origin story employers** | Product AI teams, labs’ app orgs | Palantir FDSE lineage; OpenAI FDE; Anthropic Applied AI FDE |

### Employer-primary language (do not paraphrase away the verbs)

**OpenAI FDE** — own discovery, technical scoping, system design, build, production rollout; measure via production adoption, workflow impact, eval-driven feedback; codify patterns; field signal to Research/Product; travel up to ~50% ([SF](https://openai.com/careers/forward-deployed-engineer-%28fde%29-sf-san-francisco/); [Gov](https://openai.com/careers/forward-deployed-engineer-gov-washington-dc/)).

**Anthropic FDE (Applied AI team)** — production Claude apps inside customer systems; MCP servers, sub-agents, skills; white-glove deploy; evaluation frameworks; codify patterns; travel 25–50%; high agency under ambiguity ([Greenhouse](https://job-boards.greenhouse.io/anthropic/jobs/5391016008)).

**Palantir FDSE** — embed with customer; data integration; access controls; production outages; compose platform; field → product ([Day in the Life](https://blog.palantir.com/a-day-in-the-life-of-a-palantir-forward-deployed-software-engineer-45ef2de257b1); [Who wants to be a Delta](https://blog.palantir.com/who-wants-to-be-a-delta-8d2ea948035)).

### Dual-track positioning = one flagship, two tellings

| Track | Story spine |
|-------|-------------|
| **A — Applied** | Architecture → evals → latency/cost curves → failure taxonomy → CI gate |
| **B — FDE** | Discovery → constraint → thin-slice rollout → adoption metric → what you’d productize next |

Same repo. Different first sentence. Week 23 STAR endings already practice this; Week 24 hardens resume + portfolio + LinkedIn to match the track you apply to **today**.

### Interview loop differences (unofficial aggregations — verify with recruiter)

| Employer flavor | Reported emphasis | Caution |
|-----------------|-------------------|---------|
| Anthropic | Values/safety round common failure for strong coders; evals / production LLM experience | Anecdotal; read current posting |
| OpenAI | Production/systems deep-dives; longer timelines reported anecdotally | Secondary guides ≠ official |
| Palantir-style FDE | Field engineering + customer scenario emphasis | Practice blockers as the job (Week 23 file 03) |

Secondary loop sketches (not official): [Medium six-round FDE](https://medium.com/@shivanathd/the-forward-deployed-engineer-interview-has-six-rounds-365df0544e2c); [FDE Academy OpenAI FDE](https://fde.academy/blog/openai-forward-deployed-engineer); [Paraform OpenAI FDE](https://www.paraform.com/blog/openai-forward-deployed-engineer).

### Comp bands (directional only)

Frontier-lab FDE offers are often equity-heavy; classic Palantir FDSE bands appear on crowdsourced sites. Use as **ranges for negotiation prep**, never as resume content:

- https://www.levels.fyi/companies/palantir/salaries/software-engineer/title/fdse  
- https://getperspective.ai/blog/2026-forward-deployed-engineering-compensation-report-1200-fdes  

OpenAI public posting range example (verify live page): SF FDE lists a cash band + equity on the careers page ([SF posting](https://openai.com/careers/forward-deployed-engineer-%28fde%29-sf-san-francisco/)).

### Chip Huyen role landscape

Huyen’s public interview materials and GenAI writing separate **ML engineering** (train/optimize models) from **AI engineering** (build applications on foundation models with retrieval, tools, evals, guardrails) ([ML interviews book](https://huyenchip.com/ml-interviews-book/); [GenAI platform](https://huyenchip.com/2024/07/25/genai-platform.html); [YouTube `pli1K75PSa8`](https://www.youtube.com/watch?v=pli1K75PSa8)). Both Applied and FDE sit on the AI-engineering side; FDE adds customer-embedded delivery.

---

## Alternatives & Tradeoffs

| Positioning choice | Gain | Risk |
| --- | --- | --- |
| Commit FDE-only | Clear narrative; travel/ambiguity fit | Miss product-only Applied roles |
| Commit Applied-only | Deep systems credibility | Miss lab FDE hiring waves |
| Dual-track | Optionality | Must maintain both proof types; interviews detect fake customer empathy |
| “Solutions architect” blur | Familiar enterprise title | May read non-coding |
| Internal-stakeholder stories as FDE proxy | Available without field title | Weaker than true customer embed — label honestly |
| Open-source “messy domain deploy” | Public proof | May not satisfy enterprise SSO/VPC questions alone |

---

## Necessity

Without conscious positioning, candidates send FDE-sounding resumes without customer stories (reject) or Applied resumes without eval/production depth (reject). Comp bands and travel expectations also differ by tier — know which game you’re in before negotiating or saying yes to 50% travel. Dual-track without dual **proof** is worse than a single honest track.

---

## Industry Practice

| Bar | What it looks like |
|-----|--------------------|
| **Common** | Same resume spray to every AI title |
| **Strong** | Tailored summary + 2–3 bullets per track; portfolio section matches |
| **Senior** | Two talk tracks rehearsed; travel/constraints stated early for FDE; safety/ACL story ready for Anthropic-style loops |

Practical rules:

- Maintain **two talk tracks** for the same repo (table above).  
- Practice customer-scenario questions: incomplete data access, conflicting stakeholders, security review blocking prod keys, success criteria undefined ([Palantir](https://blog.palantir.com/a-day-in-the-life-of-a-palantir-forward-deployed-software-engineer-45ef2de257b1); Week 23 FDE case).  
- For Applied loops, deepen: ranking metrics, judge calibration, cost routing ([Hamel](https://hamel.dev/blog/posts/evals/); [Huyen platform](https://huyenchip.com/2024/07/25/genai-platform.html)).  
- Signal travel willingness early when postings cite ~25–50% (OpenAI / Anthropic).  
- Watch public career talks for vocabulary; prefer official channels ([AI Engineer YouTube](https://www.youtube.com/@aiDotEngineer)).  
- qads.us / portfolio: Applied blurb vs FDE blurb per case ([overview](00-week-overview.md)).

### Candidates without employer-of-record customer work

Substitutes that sometimes pass early screens (still weaker than true field embed):

- Internal platform “customers” (support ops, PMs) with scoped pilots  
- Open-source deployment into a messy public domain dataset with auth + evals  
- Volunteer / nonprofit thin-slice with real stakeholders (anonymize as needed)  
- Capstone framed with integration constraints (SSO stub, undocumented API adapter, residency note)

Label honestly in interviews: “internal stakeholder” ≠ “enterprise embed.”

---

## Concrete Scenario (URL)

**Exercise:** Take one flagship (capstone or qads.us case). Write two 90-second openings:

1. Applied: “I shipped X; measured Y; failed on Z; fixed by …”  
2. FDE: “Stakeholder needed X under constraint C; I scoped thin slice S; unblocked with adapter A; productionized; codified P.”

Then apply to one OpenAI/Anthropic FDE posting and one product Applied AI posting with **different** resume PDFs the same week. Compare callback rate after 20 applications each (personal experiment — not science).

Employer-primary:

- https://openai.com/careers/forward-deployed-engineer-%28fde%29-sf-san-francisco/  
- https://openai.com/careers/forward-deployed-engineer-gov-washington-dc/  
- https://job-boards.greenhouse.io/anthropic/jobs/5391016008  
- https://blog.palantir.com/a-day-in-the-life-of-a-palantir-forward-deployed-software-engineer-45ef2de257b1  

Secondary positioning / loop / comp (caution):

- https://getperspective.ai/blog/anthropic-applied-ai-engineers-forward-deployed-claude-enterprise  
- https://medium.com/@shivanathd/the-forward-deployed-engineer-interview-has-six-rounds-365df0544e2c  
- https://www.levels.fyi/companies/palantir/salaries/software-engineer/title/fdse  
- https://getperspective.ai/blog/2026-forward-deployed-engineering-compensation-report-1200-fdes  
- https://fde.academy/blog/openai-forward-deployed-engineer  

Chip Huyen:

- https://huyenchip.com/ml-interviews-book/  
- https://www.youtube.com/watch?v=pli1K75PSa8  

---

## Open Questions

- Will “Applied AI Engineer” and “FDE” converge into one ladder industry-wide or stay culturally split?  
- How much travel willingness should be signaled in the first recruiter call for OpenAI/Anthropic FDE (postings cite up to ~50%)?  
- For candidates without employer-of-record customer work, can open-source “deployment in a messy domain” substitute in FDE screens?  
- Is Anthropic’s Applied AI branding a meaningful resume keyword outside Anthropic?  
- Do dual-track candidates get dinged for “unclear focus,” or rewarded for optionality, at frontier labs?

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
- https://www.youtube.com/@aiDotEngineer  
- https://www.levels.fyi/companies/palantir/salaries/software-engineer/title/fdse  
- https://getperspective.ai/blog/2026-forward-deployed-engineering-compensation-report-1200-fdes  
- https://getperspective.ai/blog/anthropic-applied-ai-engineers-forward-deployed-claude-enterprise  
- https://medium.com/@shivanathd/the-forward-deployed-engineer-interview-has-six-rounds-365df0544e2c  
- https://fde.academy/blog/openai-forward-deployed-engineer  
- https://qads.us  
