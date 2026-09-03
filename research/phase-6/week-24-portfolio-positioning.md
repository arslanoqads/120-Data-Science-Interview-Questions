# Week 24 — Portfolio Positioning (Raw Source Material)

> Meta-concepts: resume language mirroring live AI Engineer / FDE postings; portfolio pages that communicate system + metrics + failure in &lt;5 minutes; dual-track positioning (Applied AI Engineer vs Forward Deployed Engineer). Legal public sources only. Comp figures treated cautiously.

---

## Concept 1 — Resume Language that Mirrors AI Engineer / FDE Postings

### Fundamentals

ATS-and-human screeners for these roles scan for **production AI system verbs**, not course certificates. Mirror phrasing from primary postings:

| Phrase cluster | Where it shows up | Resume translation (examples of *shape*, invent your facts) |
| --- | --- | --- |
| **RAG / retrieval** | Nearly all Applied AI postings; Huyen/Anthropic public tech writing | “Shipped hybrid BM25+dense retrieval with rerank; measured recall@k / faithfulness on a golden set” |
| **Eval harness / evaluation frameworks** | Anthropic FDE; Hamel-aligned product culture | “Built offline golden-set + trace triage taxonomy; CI gate on prompt/retrieval changes” |
| **Agent orchestration** | Anthropic (agents, MCP, skills); OpenAI deployment language | “Orchestrated tool-calling agent with retries/stop conditions; logged trajectories” |
| **Cost / latency** | Platform + FDE delivery reality | “Cut p95 from Xs→Ys via cache/routing; tracked $/1k queries” |
| **Production deployment** | OpenAI FDE end-to-end rollout; Palantir field engineering | “Deployed to [env]; auth, monitoring, rollback; on-call style ownership” |
| **Customer-facing / ambiguity** | All FDE postings | “Scoped pilot with stakeholders; delivered thin slice under changing constraints” |
| **Codify patterns back to product** | Palantir + Anthropic FDE | “Turned engagement-specific adapter into reusable template/playbook” |

OpenAI FDE: own discovery → scoping → system design → build → production rollout.  
Anthropic FDE: production Claude apps; MCP servers; agents; **evaluation frameworks**; white-glove enterprise deploy; travel 25–50%.  
Palantir FDSE: embed with customer; integrate data; production rigor; field → product feedback.

### Alternatives & Tradeoffs

| Resume strategy | Pros | Cons |
| --- | --- | --- |
| Mirror keywords densely | Passes screens | Sounds fake if bullets lack metrics |
| Pure generic SWE bullets | Safe | Filtered out of AI/FDE piles |
| Research-paper heavy | Helps research tracks | Weak for Applied/FDE unless tied to shipped systems |
| Dual header (“Applied AI / FDE”) | Dual apply | Dilutes if no evidence for both |

**Bullet formula:** `Verb + system component + constraint + metric + failure/learning hook`  
Example shape: “Hardened RAG ingest for ACL-aware hybrid retrieval; raised golden-set pass rate 62%→84% by fixing chunk-boundary misses found in error analysis.”

### Necessity

Without mirrored language, strong projects get miscategorized as “chatbot hobby.” Without evidence behind keywords, mirrored language fails first technical screen.

### Industry Practice

- Put **tech stack in context of decisions** (why hybrid, why judge type), not laundry lists.
- Lead with 3–5 AI system bullets; bury coursework.
- For FDE, one bullet must show **stakeholder + integration + production**.
- Comp research (Levels.fyi / secondary aggregators) is for negotiation context later—not resume content. Treat crowdsourced TC as directional only.

### Concrete Scenario (URL)

Primary postings to mine verbs from:

- https://openai.com/careers/forward-deployed-engineer-%28fde%29-sf-san-francisco/  
- https://openai.com/careers/forward-deployed-engineer-%28fde%29-nyc-new-york-city/  
- https://openai.com/careers/forward-deployed-engineer-gov-washington-dc/  
- https://job-boards.greenhouse.io/anthropic/jobs/5391016008  
- https://blog.palantir.com/a-day-in-the-life-of-a-palantir-forward-deployed-software-engineer-45ef2de257b1  

Cautious comp anchors (crowdsourced / secondary; verify against offer docs):

- Levels.fyi Palantir FDSE: https://www.levels.fyi/companies/palantir/salaries/software-engineer/title/fdse  
- Secondary FDE comp synthesis citing Levels.fyi + postings: https://getperspective.ai/blog/2026-forward-deployed-engineering-compensation-report-1200-fdes  

Chip Huyen on role types / interview expectations:

- https://huyenchip.com/ml-interviews-book/  

### Open Questions

- Is “Prompt Engineer” still harmful on a 2026 resume for these tracks?
- Should MCP appear as a first-class bullet for Anthropic-targeted apps?
- One resume vs two tailored resumes for Applied vs FDE?

### Sources

- OpenAI / Anthropic / Palantir URLs above  
- https://huyenchip.com/ml-interviews-book/  
- https://hamel.dev/blog/posts/evals/  
- https://www.levels.fyi/companies/palantir/salaries/software-engineer/title/fdse  

---

## Concept 2 — Portfolio Pages that Show System + Metrics + Failure Narrative in &lt;5 Minutes

### Fundamentals

Hiring managers and FDEs skim. A portfolio page that cannot communicate in **&lt;5 minutes** fails. Minimum viable portfolio artifact for one flagship project:

1. **One-liner job-to-be-done** (user + stakes).  
2. **Architecture diagram** matching real code (online vs offline paths).  
3. **3 metrics**: quality (eval), latency (p95), cost proxy.  
4. **Failure narrative**: top failure mode from error analysis → fix → delta.  
5. **Run / repro**: demo link or `make eval` / video backup.  
6. **Non-goals** (scope freeze honesty).

This maps directly to Week 22 demo narrative and Week 23 STAR extraction. Public “AI portfolio” repos that read as senior tend to emphasize ADRs, tests, reproducible evals—not UI chrome alone.

### Alternatives & Tradeoffs

| Portfolio format | Pros | Cons |
| --- | --- | --- |
| Live demo + short case study | Highest trust | Uptime/cost; can flake in interview |
| Case study + recorded walkthrough | Reliable | Weaker “ops” signal |
| GitHub README only | Easy | Easy to ignore; weak narrative |
| Blog post novel | SEO | Too long for screeners |
| Multi-project grid without depth | Looks busy | No drillable system |

**5-minute script:** 60s problem → 60s architecture → 90s metrics/eval → 60s failure→fix → 30s what’s next / hire me for.

### Necessity

Interviewers increasingly ask for project deep-dives. Without a failure narrative, portfolios look like tutorial clones. Without metrics, claims are non-auditable.

### Industry Practice

- Pin golden-set size, model IDs, date of last eval run.
- Show **refusal / grounding** behavior, not only happy-path GIF.
- Link traces or redacted screenshots of triage (Hamel-aligned).
- For FDE flavor: include an “integration constraints” subsection (auth, data access, legacy tool).

### Concrete Scenario (URL)

Examples of public portfolio *shapes* (study structure, don’t copy claims):

- https://github.com/rubsj/ai-portfolio (eval/tests/ADR emphasis in README positioning)  
- Applied AI career framing (ships foundation-model apps): https://rockstardeveloperuniversity.com/career-path/applied-ai-engineer-career-path/  

Technical narrative ingredients from public engineering posts:

- https://hamel.dev/blog/posts/evals/  
- https://huyenchip.com/2024/07/25/genai-platform.html  
- https://technoscripts.com/python-rag-system-design/  

AI Engineer community talks / career sessions (YouTube — search current year’s AI Engineer World’s Fair / summit career panels; use as listening practice for how practitioners describe shipped systems):

- AI Engineer YouTube org / talk corpus: https://www.youtube.com/@aiDotEngineer  
- Example discovery search: “AI Engineer World’s Fair career” on YouTube (verify uploaders; prefer official event channels)

### Open Questions

- Is a chat UI mandatory, or is a CLI + eval report enough for Applied AI screens?
- How much customer anonymization is needed for FDE-style case studies from work?
- Should portfolios include cost dashboards even at hobby scale?

### Sources

- https://hamel.dev/blog/posts/evals/  
- https://huyenchip.com/2024/07/25/genai-platform.html  
- https://github.com/rubsj/ai-portfolio  
- https://www.youtube.com/@aiDotEngineer  
- https://technoscripts.com/python-rag-system-design/  

---

## Concept 3 — Positioning for Both Applied AI Engineer and Forward Deployed Engineer Tracks

### Fundamentals

Same underlying skills; **different emphasis and proof artifacts**.

| Dimension | Applied AI Engineer | Forward Deployed / Applied AI FDE |
| --- | --- | --- |
| **Primary customer** | Internal product / platform users | External enterprise / gov customer |
| **Success metric** | Product quality, latency, cost, reliability at scale | Time-to-value in customer env; adoption; patterned reuse |
| **Core artifacts** | Eval harness, RAG/agent services, observability, CI | Adapters, MCP/tools in customer VPC, pilot playbooks, stakeholder demos |
| **Interview center of gravity** | System design, deep project, coding, evals | Coding + **customer scenario** + integration judgment + communication |
| **Resume north star** | “I ship and measure AI systems” | “I unblock and productionize AI inside messy orgs” |
| **Origin story employers** | Product AI teams, labs’ app orgs | Palantir FDSE lineage; OpenAI FDE; Anthropic Applied AI FDE |

Anthropic sometimes labels the function **Applied AI** while the job title is Forward Deployed Engineer—read the posting body. Secondary commentary notes Anthropic’s “Applied” branding signals research↔deployment continuum rather than pure services.

**Dual-track positioning** = one flagship system that can be *told two ways*:

- Track A story: architecture, evals, latency/cost curves, failure taxonomy.  
- Track B story: discovery, constraint, thin-slice rollout, what you’d productize next.

### Alternatives & Tradeoffs

| Positioning choice | Gain | Risk |
| --- | --- | --- |
| Commit FDE-only | Clear narrative; travel/ambiguity fit | Miss product-only Applied roles |
| Commit Applied-only | Deep systems credibility | Miss lab FDE hiring waves |
| Dual-track | Optionality | Must maintain both proof types; interviews detect fake customer empathy |
| “Solutions architect” blur | Familiar enterprise title | May read non-coding |

### Necessity

Without conscious positioning, candidates send FDE-sounding resumes without customer stories (reject) or Applied resumes without eval/production depth (reject). Comp bands also differ by tier (frontier lab FDE equity-heavy vs classic Palantir FDSE)—know which game you’re in before negotiating; use Levels.fyi/postings as **ranges**, not promises.

### Industry Practice

- Maintain **two talk tracks** for the same repo (see above).  
- Practice customer-scenario questions: incomplete data access, conflicting stakeholders, security review blocking prod keys, success criteria undefined.  
- For Applied loops, deepen: ranking metrics, judge calibration, cost routing.  
- Watch public career talks from AI Engineer events for vocabulary; prefer official channels.

Reported loop differences (unofficial aggregations—verify with recruiter):

- Anthropic: values/safety round common failure mode for strong coders.  
- OpenAI: production/systems deep-dives; longer timelines reported anecdotally.  
- Palantir-style FDE: field engineering + customer scenario emphasis.

### Concrete Scenario (URL)

Employer-primary:

- https://openai.com/careers/forward-deployed-engineer-%28fde%29-sf-san-francisco/  
- https://job-boards.greenhouse.io/anthropic/jobs/5391016008  
- https://blog.palantir.com/a-day-in-the-life-of-a-palantir-forward-deployed-software-engineer-45ef2de257b1  

Secondary positioning / loop / comp context (caution: not official):

- https://getperspective.ai/blog/anthropic-applied-ai-engineers-forward-deployed-claude-enterprise  
- https://medium.com/@shivanathd/the-forward-deployed-engineer-interview-has-six-rounds-365df0544e2c  
- https://www.levels.fyi/companies/palantir/salaries/software-engineer/title/fdse  
- https://getperspective.ai/blog/2026-forward-deployed-engineering-compensation-report-1200-fdes  
- https://fde.academy/blog/openai-forward-deployed-engineer  

Chip Huyen role/interview landscape:

- https://huyenchip.com/ml-interviews-book/  

### Open Questions

- Will “Applied AI Engineer” and “FDE” converge into one ladder industry-wide or stay culturally split?
- How much travel willingness should be signaled early for OpenAI/Anthropic FDE (postings cite up to ~50%)?
- For candidates without employer-of-record customer work, can open-source “deployment in a messy domain” substitute in FDE screens?

### Sources

- OpenAI FDE postings (SF/NYC/Gov)  
- Anthropic FDE Greenhouse posting  
- Palantir FDSE blog  
- https://huyenchip.com/ml-interviews-book/  
- https://www.levels.fyi/companies/palantir/salaries/software-engineer/title/fdse  
- https://getperspective.ai/blog/2026-forward-deployed-engineering-compensation-report-1200-fdes  
- https://www.youtube.com/@aiDotEngineer  

---

## Dual-Track One-Pager (Fill from Capstone)

| Slot | Applied AI Engineer version | FDE version |
| --- | --- | --- |
| Headline | System + metrics | Customer problem + time-to-value |
| Proof #1 | Eval harness / golden set | Integration unblock story |
| Proof #2 | Latency/cost engineering | Stakeholder scoping / freeze |
| Proof #3 | Architecture depth (hybrid RAG/agents) | Production rollout + pattern codified |
| Failure | Taxonomy → fix delta | Ambiguity → clarified success metric |
| Ask | Product/platform AI role | Embedded delivery + feedback to product |

---

## Keyword Mirror Checklist (paste against a live posting)

- [ ] RAG / hybrid retrieval / rerank  
- [ ] Eval harness / golden set / error analysis  
- [ ] Agent orchestration / tools / MCP (if posting mentions)  
- [ ] Latency p95 + cost metric  
- [ ] Production deploy / monitoring / rollback  
- [ ] Security/ACL or enterprise constraint  
- [ ] Customer or stakeholder language (FDE)  
- [ ] Quantified result + personal ownership (“I”)  
