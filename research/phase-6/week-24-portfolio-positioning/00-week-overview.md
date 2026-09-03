# 00 — Week overview: resume spine, qads.us write-up, dual-track positioning

> Week 24 — Portfolio positioning  
> Research notes (raw). Phase 6 final week after system-design interview drills (Week 23). Do not invent new RAG/agent theory here — **package** Weeks 6–23 evidence into hire-readable surfaces.

This file is the **design document** for positioning week: a resume rewrite spine that mirrors live JDs, a concrete **[qads.us](https://qads.us)** portfolio write-up dual-track case pages can follow, and a one-pager that tells the same flagship system two ways. Concept files 01–03 are depth; this file is the stitched path plus the public-site brief.

---

## Fundamentals

Weeks 22–23 produced a frozen demo, a failure narrative, and a STAR bank. Week 24 answers: can a screener (ATS + human) and a hiring manager **find that signal in under five minutes** on a resume and a portfolio page?

Three coupled deliverables:

1. **Resume language** — mirror OpenAI / Anthropic / Palantir verbs with evidence (file [01](01-resume-language-mirroring-jds.md)).  
2. **Portfolio &lt;5 minutes** — system + metrics + failure + repro (file [02](02-portfolio-under-five-minutes.md)).  
3. **Dual-track positioning** — Applied AI Engineer vs FDE talk tracks (file [03](03-dual-track-ai-engineer-vs-fde.md)).

### Resume spine (say before you edit bullets)

| Step | Action | Source of truth |
|------|--------|-----------------|
| 1 | Pick **one** target posting this week | Live OpenAI / Anthropic / product-AI JD |
| 2 | Extract verb clusters into checklist | File 01 phrase table |
| 3 | Map each cluster → STAR row | Week 23 STAR bank |
| 4 | Rewrite bullets: Verb + system + constraint + metric + learning | File 01 formula |
| 5 | Header: role nouns matching track | “Applied AI Engineer” *or* “Forward Deployed / Field AI” |
| 6 | Link: GitHub pin + **qads.us** case URL | Public repro surface |

Chip Huyen’s interview materials treat portfolio and systems explanation as stronger signal than credential lists ([ML interviews book](https://huyenchip.com/ml-interviews-book/); [YouTube `pli1K75PSa8`](https://www.youtube.com/watch?v=pli1K75PSa8)). OpenAI FDE language to mirror: discovery → scoping → system design → build → production rollout; codify patterns; field feedback ([SF posting](https://openai.com/careers/forward-deployed-engineer-%28fde%29-sf-san-francisco/)). Anthropic Applied AI / FDE: production Claude apps, MCP servers, agents, **evaluation frameworks**, white-glove deploy, travel 25–50% ([Greenhouse](https://job-boards.greenhouse.io/anthropic/jobs/5391016008)). Palantir FDSE: embed, integrate data, production rigor, field → product ([Day in the Life](https://blog.palantir.com/a-day-in-the-life-of-a-palantir-forward-deployed-software-engineer-45ef2de257b1)).

### End-to-end packaging path

```
Week 23 STAR bank (metrics locked)
        │
        ▼
pick live JD → keyword checklist
        │
        ▼
rewrite 5–7 bullets (evidence-backed)
        │
        ▼
harden qads.us / portfolio case (6 MVP fields)
        │
        ▼
dual talk tracks for same flagship
        │
        ▼
tailored PDF + LinkedIn headline + send link
```

### Mapping to adjacent weeks

| This week | Not this week |
|-----------|----------------|
| Resume / portfolio copy | New features or retrieval theory (Weeks 6–10) |
| qads.us case-page hardening | Capstone scope changes (Week 22 freeze holds) |
| Dual-track talk tracks | Whiteboard practice (Week 23) — **reuse** STAR |
| Comp range research for later negotiation | Putting TC numbers on the resume |

---

## Resume + qads.us write-up

[qads.us](https://qads.us) is the public brand surface (Arslan Qadri — AI Product Manager / builder). For this curriculum’s dual-track goal, treat the site as an **Applied AI + FDE portfolio hub**, not only a PM bio. Screeners who open the link must hit **system + metrics + failure** in under five minutes on at least one showcase item.

### Current showcase inventory (structure to harden)

| Showcase | What it already signals | Harden for AI Eng / FDE |
|----------|-------------------------|-------------------------|
| **Today in AI** | Shipping cadence; multi-source ingest; auto-publish | Offline vs online path; eval of summary faithfulness; failure when source is wrong |
| **Voice Mirror** | On-device LLM; agentic flow; privacy-first | Latency/cost on-device; refusal/privacy constraints; metric cards (nine vocal metrics → which gates ship?) |
| **MarketSignal Agent** | Domain agent for wireless strategy | Tool schema; data freshness; stakeholder “what decision does this unblock?” |
| **Portfolio graph** | GraphRAG / career knowledge graph | Hybrid retrieve; citation/grounding; architecture diagram matching code |

### Per-project case page template (paste under each showcase)

Use the six MVP fields from file [02](02-portfolio-under-five-minutes.md):

1. **One-liner job-to-be-done** — user + stakes (one sentence).  
2. **Architecture** — online request path + offline ingest; boxes must match repo.  
3. **Three metrics** — quality (eval), latency (p95), cost proxy ($/1k or device budget).  
4. **Failure narrative** — top mode from error analysis → fix → delta.  
5. **Run / repro** — live demo, video backup, or `make eval`.  
6. **Non-goals** — honest scope freeze.

### Dual-track blurb pairs (write both; link the matching one from applications)

**Today in AI — Applied track**  
“Shipped a daily multi-source briefing pipeline with retrieval + summarization; gated publish on faithfulness checks against a golden set of newsletter claims; tracked p95 pipeline time and $/day model spend.”

**Today in AI — FDE track**  
“Scoped a thin ‘morning brief’ slice under shifting source APIs; quarantined malformed feeds; codified ingest adapters so the next source is a config + contract test, not a rewrite.”

**Voice Mirror — Applied track**  
“On-device agent loop with structured vocal metrics; measured end-to-end latency vs cloud baseline; documented privacy constraint as a hard non-goal for server-side audio.”

**Voice Mirror — FDE track**  
“Navigated on-device vs cloud tradeoff with a stakeholder constraint (PII never leaves device); shipped thin coaching slice first; wrote playbook for metric gates before feature expansion.”

**MarketSignal Agent — Applied track**  
“Tool-calling competitive-intel agent with allowlisted data tools; logged trajectories; eval slice for wrong-tool and stale-data failures.”

**MarketSignal Agent — FDE track**  
“Discovery with domain stakeholders on which wireless decisions matter; froze pilot KPI; integrated messy carrier-strategy inputs behind adapters; fed pattern back as reusable agent skill.”

**Portfolio graph — Applied track**  
“GraphRAG over career/skills corpus; hybrid retrieve + cite; golden-set recall@k and citation aligner in CI.”

**Portfolio graph — FDE track**  
“Embedded ‘tell my story’ assistant in a real site constraint (public surface, anonymize where needed); productionized retrieval under content-update freshness; playbook for adding a new hub node safely.”

### Homepage positioning line (choose per application week)

| Track | Suggested hero subtitle (shape — edit facts) |
|-------|-----------------------------------------------|
| Applied AI Engineer | “I ship and measure production LLM systems — RAG, agents, eval harnesses, cost/latency.” |
| FDE / Applied AI FDE | “I unblock and productionize AI inside messy orgs — discovery, thin-slice rollout, patterns back to product.” |
| Dual (site default) | “Production AI systems + field-style delivery. Case studies below open in &lt;5 minutes.” |

Link the resume header to the **deepest** case page (usually Portfolio graph or MarketSignal), not only the homepage. Chip Huyen: thoughtful public work beats credential theater ([`pli1K75PSa8`](https://www.youtube.com/watch?v=pli1K75PSa8)).

### Site QA before sending links to recruiters

- [ ] Each linked case has the six MVP fields above the fold or one click away  
- [ ] Architecture diagram matches current code / GraphRAG path  
- [ ] At least one **failure** demo or written failure→fix (not only happy path)  
- [ ] Metrics dated (last eval run / model IDs)  
- [ ] Mobile load: first viewport = brand + one project CTA, not a dashboard dump  
- [ ] Chat / portfolio assistant (if present): graceful abstain + link to case study (control under failure)

---

## Dual-track one-pager (fill from capstone / qads.us)

| Slot | Applied AI Engineer version | FDE version |
| --- | --- | --- |
| Headline | System + metrics | Customer / stakeholder problem + time-to-value |
| Proof #1 | Eval harness / golden set | Integration unblock story |
| Proof #2 | Latency/cost engineering | Stakeholder scoping / freeze |
| Proof #3 | Architecture depth (hybrid RAG/agents) | Production rollout + pattern codified |
| Failure | Taxonomy → fix delta | Ambiguity → clarified success metric |
| Ask | Product/platform AI role | Embedded delivery + feedback to product |
| Public link | qads.us case (Applied blurb) | qads.us case (FDE blurb) |

---

## Alternatives & Tradeoffs

| Packaging choice | Gain | Risk |
| --- | --- | --- |
| One resume, dual header | Speed | Dilutes if evidence thin for one track |
| Two tailored PDFs | Higher pass rate per pile | Must keep both current |
| Homepage-only portfolio | Easy share | Screeners bounce without drill-down |
| Deep case + weak homepage | Trust on click-through | Lost if link never opened |
| Comp numbers on resume | None useful | Looks naive; use Levels.fyi offline only |

---

## Necessity

Without mirrored language, strong projects read as “chatbot hobby.” Without evidence behind keywords, mirrored language fails the first technical screen. Without a &lt;5-minute portfolio (qads.us or otherwise), Week 22 demos stay private. Without dual-track consciousness, candidates send FDE resumes without customer stories—or Applied resumes without eval/production depth.

---

## Industry Practice

| Bar | What it looks like |
|-----|--------------------|
| **Common** | Tool laundry list; course certificates lead; portfolio is UI screenshots |
| **Strong** | 3–5 AI system bullets with metrics; one failure story; live or recorded repro |
| **Senior / FDE** | Stakeholder + integration + production in one bullet; codify-back-to-product; dual talk tracks; travel willingness stated when applying FDE |

- Lead with production AI verbs from primary postings; bury coursework.  
- Put stack in **decision context** (why hybrid, why judge type).  
- Comp research ([Levels.fyi Palantir FDSE](https://www.levels.fyi/companies/palantir/salaries/software-engineer/title/fdse); secondary [Perspective 2026 FDE report](https://getperspective.ai/blog/2026-forward-deployed-engineering-compensation-report-1200-fdes)) is for **negotiation prep**, not resume body.  
- Watch public career vocabulary on [AI Engineer YouTube](https://www.youtube.com/@aiDotEngineer); prefer official uploaders.

---

## Concrete Scenario (URL)

**This week’s exercise:** Take the OpenAI FDE SF posting and the Anthropic FDE Greenhouse posting. Build one keyword checklist. Rewrite five bullets from your STAR bank. Publish or update **one** qads.us case page with the six MVP fields and both track blurbs. Time-box a stranger skim: can they explain your system in five minutes?

- https://openai.com/careers/forward-deployed-engineer-%28fde%29-sf-san-francisco/  
- https://job-boards.greenhouse.io/anthropic/jobs/5391016008  
- https://blog.palantir.com/a-day-in-the-life-of-a-palantir-forward-deployed-software-engineer-45ef2de257b1  
- https://qads.us  
- https://huyenchip.com/ml-interviews-book/  
- https://www.youtube.com/watch?v=pli1K75PSa8  

---

## Open Questions

- Is “Prompt Engineer” still harmful on a 2026 resume for Applied / FDE tracks?  
- Should MCP appear as a first-class bullet for Anthropic-targeted apps only, or generally?  
- One resume vs two tailored resumes when applying both tracks the same week?  
- How much employer anonymization is required when FDE-style stories come from day-job work?  
- Will Applied AI Engineer and FDE ladders converge industry-wide or stay culturally split?

---

## Sources

- https://qads.us  
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
