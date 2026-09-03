# Chapter 24 — Portfolio positioning

> **Phase 6 — Capstone and Interview Readiness**  
> **Editorial status:** COMPLETE  
> **Source of truth:** `research/phase-6/week-24-portfolio-positioning/`  
> **Syllabus Build:** Syllabus treats Week 24 as **packaging meta-work**: you already have a demo (Week 22) and STAR bank (Week 23). This week you make them **hire-readable**. (1) **Mirror one live posting.** Paste OpenAI / Anthropic / Palantir-language verbs into a keyword checklist; rewrite 5–7 bullets with evidence from STAR ([OpenAI FDE SF](https://openai.com/careers/forward-deployed-engineer-%28fde%29-sf-san-francisco/); [Anthropic FDE](https://job-boards.greenhouse.io/anthropic/jobs/5391016008); [Palantir FDSE](https://blog.palantir.com/a-day-in-the-life-of-a-palantir-forward-deployed-software-engineer-45ef2de257b1)). (2) **Ship a &lt;5-minute portfolio page** for the flagship (or harden [qads.us](https://qads.us) project pages): architecture matching code, three metrics, one failure→fix, repro link ([Huyen GenAI platform](https://huyenchip.com/2024/07/25/genai-platform.html); [Hamel evals](https://hamel.dev/blog/posts/evals/); Week 22 narrative). (3) **Write dual talk tracks** for the same repo: Applied (evals/latency/architecture) vs FDE (discovery/constraint/rollout/codify). (4) **Freeze resume header + LinkedIn headline** for the track you apply to this week; keep the other track’s bullets ready as a second tailored PDF.

---

## Prerequisites Recap

Before this week you should already have from Week 23:

- **System design interview drills:** annotated ~10M-doc retrieval whiteboard; timed prompt-debug ladder (reproduce → localize → minimize → one hypothesis → golden lock); one FDE integration unblock case; aloud tradeoff one-liners with latency + $ budgets.  
- **STAR bank:** 8–10 cards from *your* Weeks 6–22 builds (title / metric / systems / 3 follow-ups), with dual-track endings and quantified results you can defend.

You do **not** need a tailored resume PDF, a hire-readable portfolio/qads.us case page, dual-track one-pager, or keyword checklist marked against a live JD yet as *finished* products — that is what this week ships. You **do** need Week 22’s frozen demo narrative and Week 23’s locked STAR metrics as raw material; without them, resume bullets and portfolio metrics invent numbers you cannot defend.

---

## What this week builds

Week 23 drilled whiteboards, timed prompt-debug, FDE unblock cases, aloud tradeoffs, and a STAR bank. Week 24 is the **hire-readable packaging** week of Phase 6. Weeks 6–23 already shipped the systems and interview drills; this week adds **no new product surface**. Capstone freeze (Week 22) and STAR metrics (Week 23) hold; this week only rewrites and surfaces them.

This week answers three coupled questions that screeners and hiring managers treat as the minimum bar for finding your signal in under five minutes:

1. **Resume language** — mirror OpenAI / Anthropic / Palantir verbs with evidence from STAR.  
2. **Portfolio &lt;5 minutes** — system + metrics + failure + repro (architecture matching code).  
3. **Dual-track positioning** — Applied AI Engineer vs FDE talk tracks for the same flagship.

**Do not invent new RAG/agent theory here** — package Weeks 6–23 evidence into hire-readable surfaces. Do **not** start Phase 7 electives from this chapter — this week freezes resume header + LinkedIn headline, hardens the portfolio case, and writes dual talk tracks. Do **not** reopen the Week 22 freeze or invent STAR metrics to “fill bullets.”

**End-to-end packaging path**

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

**Default path (synthesis)**

1. **Evidence before keywords** — STAR metrics from Week 23 feed bullets; never invent ([Huyen ML interviews](https://huyenchip.com/ml-interviews-book/)).  
2. **Mirror posting verbs** that you can defend in a deep-dive ([OpenAI](https://openai.com/careers/forward-deployed-engineer-%28fde%29-sf-san-francisco/); [Anthropic](https://job-boards.greenhouse.io/anthropic/jobs/5391016008)).  
3. **Portfolio = system + metrics + failure**, not UI chrome ([Hamel](https://hamel.dev/blog/posts/evals/); Week 22).  
4. **Dual-track = two stories, one system** — Applied ships/measures; FDE unblocks/productionizes ([Palantir](https://blog.palantir.com/a-day-in-the-life-of-a-palantir-forward-deployed-software-engineer-45ef2de257b1)).  
5. **Comp is negotiation context later**, not resume content ([Levels.fyi FDSE](https://www.levels.fyi/companies/palantir/salaries/software-engineer/title/fdse)).  
6. **qads.us is the public surface** — each showcase item needs the six MVP fields before you send the link.

Interview artifact = **tailored resume (1–2 pages)** + **portfolio/qads.us case that survives 5 minutes** + **dual-track one-pager** + **keyword checklist marked against a live JD**.

| This week | Not this week |
|-----------|----------------|
| Resume / portfolio copy | New features or retrieval theory (Weeks 6–10) |
| qads.us case-page hardening | Capstone scope changes (Week 22 freeze holds) |
| Dual-track talk tracks | Whiteboard practice (Week 23) — **reuse** STAR |
| Comp range research for later negotiation | Putting TC numbers on the resume |

Read the concepts in order. Each section’s **Worked Example** and **Apply It** assume the same flagship service (working title: Deployment Copilot) after Week 22–23 freeze — now packaged for resume, portfolio, and dual-track applications. Public-site hardening follows the [qads.us](https://qads.us) case template from research.

---

### Resume language that mirrors AI Engineer / FDE postings

* **Fundamentals:**  
  Resume language for Applied AI Engineer and Forward Deployed Engineer roles must **mirror primary postings** while remaining defensibly true in a deep-dive. Invented keywords fail the first technical screen; generic SWE bullets get filtered out of AI/FDE piles. Chip Huyen’s framing: AI engineering is **adapting foundation models into systems** (integration, evals, guardrails), not training models from scratch — resume language should reflect shipped systems ([GenAI platform](https://huyenchip.com/2024/07/25/genai-platform.html); [ML interviews](https://huyenchip.com/ml-interviews-book/)).

  **Phrase clusters → resume shape**

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

  **Primary posting verbs to steal (paraphrase with your evidence)**

  **OpenAI FDE** ([SF](https://openai.com/careers/forward-deployed-engineer-%28fde%29-sf-san-francisco/); [NYC](https://openai.com/careers/forward-deployed-engineer-%28fde%29-nyc-new-york-city/); [Gov](https://openai.com/careers/forward-deployed-engineer-gov-washington-dc/)): own discovery → technical scoping → system design → build → **production rollout**; production adoption, measurable workflow impact, **eval-driven feedback**; embed with customer teams; trade-offs among scope, speed, quality; **codify** working patterns into tools / playbooks / building blocks; share field feedback to Research / Product; travel up to ~50% (SF posting).

  **Anthropic FDE / Applied AI** ([Greenhouse](https://job-boards.greenhouse.io/anthropic/jobs/5391016008)): build **production applications with Claude** inside customer systems; deliver **MCP servers, sub-agents, agent skills**; white-glove enterprise deploy; **evaluation frameworks**; prompt engineering; agent development at scale; codify repeatable deployment patterns back to Product / Engineering; travel **25–50%**; thrive under ambiguity.

  **Palantir FDSE** ([Day in the Life](https://blog.palantir.com/a-day-in-the-life-of-a-palantir-forward-deployed-software-engineer-45ef2de257b1); [Who wants to be a Delta](https://blog.palantir.com/who-wants-to-be-a-delta-8d2ea948035)): embed with customer; integrate data; access controls; production rigor / outages; compose platform capabilities; field learnings → product.

  **Bullet formula**

  ```
  Verb + system component + constraint + metric + failure/learning hook
  ```

  **Example shape:** “Hardened RAG ingest for ACL-aware hybrid retrieval; raised golden-set pass rate 62%→84% by fixing chunk-boundary misses found in error analysis.”  
  **Weak:** “Worked on RAG chatbot using LangChain and OpenAI.”  
  **Stronger:** “Shipped hybrid retrieval + citation aligner for internal KB; faithfulness 58%→81% after open-coding 40 traces; p95 held under 2s.”

  **Resume structure that survives AI Eng / FDE screens**

  1. **Header** — name, email, LinkedIn, GitHub, portfolio ([qads.us](https://qads.us) case URL).  
  2. **Summary (2–3 lines)** — track noun + one system claim + one customer/production claim if FDE.  
  3. **Skills** — clustered (retrieval/evals/agents; languages; cloud; identity) — not a dump.  
  4. **Experience** — reverse chrono; 3–5 AI system bullets lead.  
  5. **Projects** — flagship with metrics if day job is not yet AI-titled.  
  6. **Education** — short; coursework does not lead.

  **Resume spine (say before you edit bullets)**

  | Step | Action | Source of truth |
  |------|--------|-----------------|
  | 1 | Pick **one** target posting this week | Live OpenAI / Anthropic / product-AI JD |
  | 2 | Extract verb clusters into checklist | Phrase table above |
  | 3 | Map each cluster → STAR row | Week 23 STAR bank |
  | 4 | Rewrite bullets: Verb + system + constraint + metric + learning | Bullet formula |
  | 5 | Header: role nouns matching track | “Applied AI Engineer” *or* “Forward Deployed / Field AI” |
  | 6 | Link: GitHub pin + **qads.us** case URL | Public repro surface |

  **Keyword mirror checklist (paste against a live posting)**

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

* **The Alternatives:**  

  | Resume strategy | What you gain | What it costs | When it fits |
  |-----------------|---------------|---------------|--------------|
  | Mirror keywords densely | Passes screens | Sounds fake if bullets lack metrics | Default when STAR evidence exists |
  | Pure generic SWE bullets | Safe for classic SWE piles | Filtered out of AI/FDE piles | Classic SWE-only targets |
  | Research-paper heavy | Helps research tracks | Weak for Applied/FDE unless tied to shipped systems | Research-heavy postings |
  | Dual header (“Applied AI / FDE”) | Dual apply | Dilutes if no evidence for both | Thin evidence for one track — avoid |
  | Two tailored resumes | Higher match per posting | Maintenance cost | Applying both tracks same week |
  | “Prompt Engineer” title lead | Rarely helpful in 2026 | Can read as non-systems / fad title | Prefer as *skill inside* a systems bullet |

  **Title nouns that usually help:** Applied AI Engineer, AI Engineer, Forward Deployed Engineer, Field Engineer (AI), ML Platform / LLM Application Engineer.  
  **Title nouns to use carefully:** Prompt Engineer (prefer as a skill inside a systems bullet); Solutions Architect (may read non-coding unless coding evidence is loud).

  Comp research ([Levels.fyi FDSE](https://www.levels.fyi/companies/palantir/salaries/software-engineer/title/fdse); [Perspective secondary synthesis](https://getperspective.ai/blog/2026-forward-deployed-engineering-compensation-report-1200-fdes)) is for **negotiation context later** — **not resume content**. Treat crowdsourced TC as directional only. Secondary FDE resume guides (Exponent, FDE Academy) are useful for *structure*; prefer primary posting verbs over blog templates.

  `[NEEDS MORE RESEARCH]`: whether “Prompt Engineer” is still harmful as a 2026 headline for Applied / FDE tracks; whether MCP should be a first-class bullet for all Anthropic-targeted apps or only when the posting lists it; one resume vs two tailored resumes when spraying both tracks the same week (research leaves these as open questions).

* **Failure Modes:**  
  - Strong projects miscategorized as “chatbot hobby” without mirrored production verbs.  
  - Mirrored keywords without STAR metrics → fails first technical screen and destroys onsite trust.  
  - No **stakeholder + integration + production** bullet → FDE piles reject strong Applied-only resumes.  
  - Tool laundry list / certificate row leads; coursework ahead of systems.  
  - Comp / TC numbers on the resume (looks naive).  
  - Dual header with thin evidence for one track dilutes both.  
  - Claiming posting verbs you cannot defend in a deep-dive.

* **Average vs. Strong Engineer:**  
  **Average / Common:** “Familiar with LLMs”; certificate row; tool laundry list; generic SWE bullets.  
  **Strong:** 3–5 AI system bullets with metrics; stack explained as decisions (why hybrid, why judge type); personal “I” ownership; lead with production AI verbs; bury coursework.  
  **Senior / FDE:** Ambiguity + scoping + rollout + codify in one bullet; eval frameworks named; travel willingness when relevant; dual talk tracks ready.

* **Worked Example:**  
  You open the Anthropic FDE Greenhouse posting and OpenAI FDE SF posting side by side. From the Week 23 STAR bank for Deployment Copilot you rewrite five bullets (shape — replace with your locked metrics):

  1. **RAG / eval:** “Shipped hybrid BM25+dense retrieval + citation aligner for Deployment Copilot KB; faithfulness 58%→81% after open-coding 40 traces; p95 held under 2s.”  
  2. **Eval harness:** “Built offline golden-set + trace triage taxonomy; CI gate on prompt/retrieval changes for the capstone slice.”  
  3. **Cost / latency:** “Cut p95 2.8s→1.7s via rerank-candidate budget + cache routing; tracked $/1k queries (−18%).”  
  4. **FDE constraint:** “Scoped pilot under ACL / tenant filter-before-rank; red-team goldens; empty-retrieve abstain when context missing.”  
  5. **Codify:** “Turned undocumented API adapter into contract-tested MCP/tool template so the next source is config + tests, not a rewrite.”

  Summary line for **Applied-only:** “Applied AI Engineer — I ship and measure production LLM systems (RAG, agents, eval harnesses, cost/latency).”  
  Summary line for **FDE-only:** “Forward Deployed Engineer — I unblock and productionize AI inside messy constraints — discovery, thin-slice rollout, patterns back to product.”  
  Header links GitHub pin + deepest qads.us / portfolio case URL, not only the homepage.

* **Apply It:**  
  1. Pick **one** live OpenAI / Anthropic / product-AI posting this week.  
  2. Extract verb clusters into the keyword mirror checklist; mark each as evidenced or “no evidence — do not claim.”  
  3. Map each evidenced cluster to a Week 23 STAR row.  
  4. Rewrite 5–7 bullets with Verb + system + constraint + metric + learning; use I-language.  
  5. Freeze header role noun for the track you apply to this week; keep the other track’s bullets as a second tailored PDF if needed.  
  6. Put portfolio / GitHub / qads.us case link in the header.  
  7. Do **not** put TC / Levels.fyi numbers on the resume.

---

### Portfolio pages that show system + metrics + failure in under five minutes

* **Fundamentals:**  
  A portfolio for Applied AI Engineer / FDE loops is not a gallery of UIs. It is a **drillable system narrative**: architecture that matches code, auditable metrics, and a failure→fix story. This maps directly to Week 22’s demo narrative and Week 23’s STAR extraction. Hiring managers and FDEs skim — a portfolio that cannot communicate in **&lt;5 minutes** fails. Chip Huyen’s interview materials treat portfolio and systems explanation as stronger signal than credential lists ([ML interviews book](https://huyenchip.com/ml-interviews-book/); [YouTube `pli1K75PSa8`](https://www.youtube.com/watch?v=pli1K75PSa8)).

  **Minimum viable portfolio artifact (one flagship)**

  1. **One-liner job-to-be-done** — user + stakes.  
  2. **Architecture diagram** — online vs offline paths; boxes match real code.  
  3. **Three metrics** — quality (eval), latency (p95), cost proxy.  
  4. **Failure narrative** — top failure mode from error analysis → fix → delta.  
  5. **Run / repro** — demo link, `make eval`, or video backup.  
  6. **Non-goals** — scope freeze honesty.

  Public “AI portfolio” repos that read as senior tend to emphasize ADRs, tests, reproducible evals — not UI chrome alone (study structure, don’t copy claims: e.g. [rubsj/ai-portfolio](https://github.com/rubsj/ai-portfolio)).

  **Five-minute script (default)**

  | Clock | Beat | Anti-pattern |
  |-------|------|--------------|
  | 0:00–1:00 | Problem / user / stakes | Starting in model names |
  | 1:00–2:00 | Architecture (online + offline) | Vapor boxes not in repo |
  | 2:00–3:30 | Metrics + eval evidence | Vibes-only screenshots |
  | 3:30–4:30 | Failure → fix → delta | Hiding failure; tutorial clone |
  | 4:30–5:00 | What’s next / hire me for | Feature roadmap dump |

  Align with Week 22’s longer demo spine when you have a live walkthrough: user → freeze → architecture → success → controlled failure → metrics.

  **What “opening the hood” means on a page** — above the fold or one click away, show at least one of: retrieved chunks / scores / ACL filters; citation highlights aligned to answer spans; tool-call JSON (success + structured error); eval command output or golden-set row; trace / triage screenshot (redacted). Hamel’s product-eval ethos: you should be able to debug quickly because traces, assertions, and navigation exist ([Your AI Product Needs Evals](https://hamel.dev/blog/posts/evals/)). A portfolio that cannot show where a citation came from fails the trust test the same way a demo does.

  **Progressive complexity (Huyen):** model API → guardrails → context (RAG/tools) → cache/route → logging/evals — add components when failure modes demand them ([Building a Generative AI Platform](https://huyenchip.com/2024/07/25/genai-platform.html)). Portfolio pages should show **which layer you added and why**, not every buzzword.

  **FDE flavor subsection (when targeting field roles)** — add an **integration constraints** block: Auth / SSO / VPC / residency; data access reality (export vs API); legacy tool / messy schema; stakeholder success metric freeze; what you would **codify** next as a playbook / MCP / template. Palantir FDSE narratives emphasize composing platform capabilities under customer constraints, not inventing a new platform per engagement ([Day in the Life](https://blog.palantir.com/a-day-in-the-life-of-a-palantir-forward-deployed-software-engineer-45ef2de257b1)).

  **qads.us as the default public surface:** For this curriculum, [qads.us](https://qads.us) is the public brand surface. Treat it as an **Applied AI + FDE portfolio hub**. Screeners who open the link must hit **system + metrics + failure** in under five minutes on at least one showcase item. Prefer linking recruiters to a **single deep case** over the homepage alone.

  | Showcase | What it already signals | Harden for AI Eng / FDE |
  |----------|-------------------------|-------------------------|
  | **Today in AI** | Shipping cadence; multi-source ingest; auto-publish | Offline vs online path; eval of summary faithfulness; failure when source is wrong |
  | **Voice Mirror** | On-device LLM; agentic flow; privacy-first | Latency/cost on-device; refusal/privacy constraints; metric cards (nine vocal metrics → which gates ship?) |
  | **MarketSignal Agent** | Domain agent for wireless strategy | Tool schema; data freshness; stakeholder “what decision does this unblock?” |
  | **Portfolio graph** | GraphRAG / career knowledge graph | Hybrid retrieve; citation/grounding; architecture diagram matching code |

  **Homepage positioning line (choose per application week)**

  | Track | Suggested hero subtitle (shape — edit facts) |
  |-------|-----------------------------------------------|
  | Applied AI Engineer | “I ship and measure production LLM systems — RAG, agents, eval harnesses, cost/latency.” |
  | FDE / Applied AI FDE | “I unblock and productionize AI inside messy orgs — discovery, thin-slice rollout, patterns back to product.” |
  | Dual (site default) | “Production AI systems + field-style delivery. Case studies below open in &lt;5 minutes.” |

  **Site QA before sending links to recruiters**

  - [ ] Each linked case has the six MVP fields above the fold or one click away  
  - [ ] Architecture diagram matches current code / GraphRAG path  
  - [ ] At least one **failure** demo or written failure→fix (not only happy path)  
  - [ ] Metrics dated (last eval run / model IDs)  
  - [ ] Mobile load: first viewport = brand + one project CTA, not a dashboard dump  
  - [ ] Chat / portfolio assistant (if present): graceful abstain + link to case study (control under failure)

* **The Alternatives:**  

  | Portfolio format | What you gain | What it costs | When it fits |
  |------------------|---------------|---------------|--------------|
  | Live demo + short case study | Highest trust | Uptime/cost; can flake in interview | Primary when ops confidence + rollback story exist |
  | Case study + recorded walkthrough | Reliable | Weaker “ops” signal unless traces shown | Backup / default reliability path |
  | GitHub README only | Easy | Easy to ignore; weak narrative | Insufficient alone for screeners |
  | Blog post novel | SEO | Too long for screeners | Secondary deep-dive, not skim path |
  | Multi-project grid without depth | Looks busy | No drillable system | Avoid as sole surface |
  | Chat UI on portfolio | Engagement | Must abstain gracefully; else toy signal | Only with refusal control |
  | Cost dashboard at hobby scale | Shows ops taste | Numbers must be honest / dated | Optional; honesty required |
  | Homepage-only share | Easy share | Screeners bounce without drill-down | Prefer deep case URL |
  | Deep case + weak homepage | Trust on click-through | Lost if link never opened | Pair with clear homepage CTA |

  **Practical default:** recorded walkthrough + live primary + `make eval` backup. Live-only signals ops confidence but needs a rollback story when the demo dies mid-loop.

  `[NEEDS MORE RESEARCH]`: whether a chat UI is mandatory vs CLI + eval report for Applied screens; how much customer anonymization FDE-style paid-work cases need; whether hobby-scale cost dashboards help; whether a portfolio assistant helps or hurts when abstain is weak; one flagship deep case vs three medium cases for dual-track applicants (research leaves these open).

* **Failure Modes:**  
  - Without a failure narrative, portfolios look like tutorial clones.  
  - Without metrics, claims are non-auditable.  
  - Architecture diagrams that don’t match code read as slideware.  
  - No five-minute path → busy FDE/hiring managers bounce.  
  - Hero GIF of chat UI; “built with LangChain”; no evals.  
  - Week 22 demos stay private — never linked from resume.  
  - Undated golden-set / model IDs; happy-path only.  
  - Portfolio chat that cannot abstain → toy signal.

* **Average vs. Strong Engineer:**  
  **Average / Common:** Hero GIF of chat UI; “built with LangChain”; no evals; homepage-only share.  
  **Strong:** Architecture + 3 metrics + failure→fix + repro command; pin golden-set size, model IDs, date of last eval run; show refusal / grounding, not only happy-path GIF; link traces or redacted triage screenshots (Hamel-aligned).  
  **Senior / FDE:** Integration constraints block; refusal/grounding demo; dated golden-set; codify note; discovery → thin slice → production → pattern.

* **Worked Example:**  
  Deployment Copilot (or one qads.us showcase) case page — six MVP fields filled from Week 22–23 artifacts:

  1. **One-liner:** “Help a deployment engineer answer ACL-aware runbook questions with citations under 2s p95.”  
  2. **Architecture:** Online path (retrieve → rerank → generate → cite/abstain) + offline ingest (chunk → embed → index); diagram boxes match `src/` modules.  
  3. **Three metrics:** faithfulness / golden-set pass rate; p95 latency; $/1k queries (dated + model IDs).  
  4. **Failure → fix:** chunk-boundary misses from error analysis → retune chunk/overlap + section-aware split → faithfulness delta (STAR 1 shape from Week 23).  
  5. **Repro:** live demo URL + recorded backup + `make eval` / golden-set command in README.  
  6. **Non-goals:** second agent, admin UI sprawl — Week 22 freeze holds.

  **Dual-track blurbs** (write both; link the matching one from applications) — curriculum showcase shapes from research:

  | Case | Applied track | FDE track |
  |------|---------------|-----------|
  | Today in AI | Daily multi-source briefing; faithfulness gate; p95 + $/day | Thin ‘morning brief’ under shifting APIs; quarantine feeds; ingest adapters as config + contract tests |
  | Voice Mirror | On-device agent loop; latency vs cloud; privacy as hard non-goal | Stakeholder PII-never-leaves-device; thin coaching slice; metric gates before expansion |
  | MarketSignal Agent | Tool-calling agent; trajectories; wrong-tool / stale-data eval | Discovery on which decisions matter; pilot KPI freeze; messy inputs behind adapters → reusable skill |
  | Portfolio graph | GraphRAG; hybrid retrieve + cite; recall@k + citation aligner in CI | Public-surface constraints; freshness under content updates; playbook for new hub nodes |

  **Stranger skim test:** give a colleague five minutes, close the tab, ask them to restate (1) user job, (2) one architecture choice, (3) one metric, (4) one failure fix. If any answer is missing, the page failed.

* **Apply It:**  
  1. Pick one flagship (Deployment Copilot or one qads.us showcase).  
  2. Write a one-page case with all six MVP fields above the fold or one click away.  
  3. Align architecture diagram to current code; pin dated metrics + model IDs.  
  4. Add failure→fix (demo or written) and a repro path (live + video + `make eval`).  
  5. For FDE targets, add the integration-constraints block and a codify-next note.  
  6. Write both Applied and FDE blurbs; link the matching one from applications.  
  7. Run site QA + stranger 5-minute skim before sending recruiter links.  
  8. Prefer the deepest case URL in the resume header, not homepage-only.

---

### Dual-track positioning: Applied AI Engineer vs Forward Deployed Engineer

* **Fundamentals:**  
  **Applied AI Engineer** and **Forward Deployed Engineer (FDE)** / **Forward Deployed Software Engineer (FDSE)** share RAG, agents, evals, and production engineering. They diverge on **primary customer**, **success metric**, and **story center of gravity**. Anthropic sometimes labels the function **Applied AI** while the job title is Forward Deployed Engineer — read the posting body ([Greenhouse FDE](https://job-boards.greenhouse.io/anthropic/jobs/5391016008)). Secondary commentary notes Anthropic’s “Applied” branding signals a research↔deployment continuum rather than pure services — verify against the live posting.

  **Dimension table**

  | Dimension | Applied AI Engineer | Forward Deployed / Applied AI FDE |
  | --- | --- | --- |
  | **Primary customer** | Internal product / platform users | External enterprise / gov customer |
  | **Success metric** | Product quality, latency, cost, reliability at scale | Time-to-value in customer env; adoption; patterned reuse |
  | **Core artifacts** | Eval harness, RAG/agent services, observability, CI | Adapters, MCP/tools in customer VPC, pilot playbooks, stakeholder demos |
  | **Interview center of gravity** | System design, deep project, coding, evals | Coding + **customer scenario** + integration judgment + communication |
  | **Resume north star** | “I ship and measure AI systems” | “I unblock and productionize AI inside messy orgs” |
  | **Origin story employers** | Product AI teams, labs’ app orgs | Palantir FDSE lineage; OpenAI FDE; Anthropic Applied AI FDE |

  **Employer-primary language (do not paraphrase away the verbs)**

  - **OpenAI FDE** — discovery, technical scoping, system design, build, production rollout; measure via production adoption, workflow impact, eval-driven feedback; codify patterns; field signal to Research/Product; travel up to ~50% ([SF](https://openai.com/careers/forward-deployed-engineer-%28fde%29-sf-san-francisco/); [Gov](https://openai.com/careers/forward-deployed-engineer-gov-washington-dc/)).  
  - **Anthropic FDE (Applied AI team)** — production Claude apps inside customer systems; MCP servers, sub-agents, skills; white-glove deploy; evaluation frameworks; codify patterns; travel 25–50%; high agency under ambiguity ([Greenhouse](https://job-boards.greenhouse.io/anthropic/jobs/5391016008)).  
  - **Palantir FDSE** — embed with customer; data integration; access controls; production outages; compose platform; field → product ([Day in the Life](https://blog.palantir.com/a-day-in-the-life-of-a-palantir-forward-deployed-software-engineer-45ef2de257b1); [Who wants to be a Delta](https://blog.palantir.com/who-wants-to-be-a-delta-8d2ea948035)).

  **Dual-track positioning = one flagship, two tellings**

  | Track | Story spine |
  |-------|-------------|
  | **A — Applied** | Architecture → evals → latency/cost curves → failure taxonomy → CI gate |
  | **B — FDE** | Discovery → constraint → thin-slice rollout → adoption metric → what you’d productize next |

  Same repo. Different first sentence. Week 23 STAR endings already practice this; Week 24 hardens resume + portfolio + LinkedIn to match the track you apply to **today**.

  **Dual-track one-pager (fill from capstone / qads.us)**

  | Slot | Applied AI Engineer version | FDE version |
  | --- | --- | --- |
  | Headline | System + metrics | Customer / stakeholder problem + time-to-value |
  | Proof #1 | Eval harness / golden set | Integration unblock story |
  | Proof #2 | Latency/cost engineering | Stakeholder scoping / freeze |
  | Proof #3 | Architecture depth (hybrid RAG/agents) | Production rollout + pattern codified |
  | Failure | Taxonomy → fix delta | Ambiguity → clarified success metric |
  | Ask | Product/platform AI role | Embedded delivery + feedback to product |
  | Public link | qads.us case (Applied blurb) | qads.us case (FDE blurb) |

  **Interview loop differences (unofficial aggregations — verify with recruiter)**

  | Employer flavor | Reported emphasis | Caution |
  |-----------------|-------------------|---------|
  | Anthropic | Values/safety round common failure for strong coders; evals / production LLM experience | Anecdotal; read current posting |
  | OpenAI | Production/systems deep-dives; longer timelines reported anecdotally | Secondary guides ≠ official |
  | Palantir-style FDE | Field engineering + customer scenario emphasis | Practice blockers as the job (Week 23) |

  **Comp bands (directional only):** Frontier-lab FDE offers are often equity-heavy; classic Palantir FDSE bands appear on crowdsourced sites. Use as **ranges for negotiation prep**, never as resume content ([Levels.fyi](https://www.levels.fyi/companies/palantir/salaries/software-engineer/title/fdse); [Perspective 2026 FDE report](https://getperspective.ai/blog/2026-forward-deployed-engineering-compensation-report-1200-fdes)). OpenAI public posting range example: SF FDE lists a cash band + equity on the careers page — verify live page.

  **Chip Huyen role landscape:** public interview materials and GenAI writing separate **ML engineering** (train/optimize models) from **AI engineering** (build applications on foundation models with retrieval, tools, evals, guardrails). Both Applied and FDE sit on the AI-engineering side; FDE adds customer-embedded delivery ([ML interviews](https://huyenchip.com/ml-interviews-book/); [GenAI platform](https://huyenchip.com/2024/07/25/genai-platform.html); [`pli1K75PSa8`](https://www.youtube.com/watch?v=pli1K75PSa8)).

  **Candidates without employer-of-record customer work** — substitutes that sometimes pass early screens (still weaker than true field embed): internal platform “customers” (support ops, PMs) with scoped pilots; open-source deployment into a messy public domain dataset with auth + evals; volunteer / nonprofit thin-slice with real stakeholders (anonymize as needed); capstone framed with integration constraints (SSO stub, undocumented API adapter, residency note). Label honestly: “internal stakeholder” ≠ “enterprise embed.”

* **The Alternatives:**  

  | Positioning choice | What you gain | What it costs | When it fits |
  |--------------------|---------------|---------------|--------------|
  | Commit FDE-only | Clear narrative; travel/ambiguity fit | Miss product-only Applied roles | Strong customer stories + travel OK |
  | Commit Applied-only | Deep systems credibility | Miss lab FDE hiring waves | Strong eval/prod depth; weak field proof |
  | Dual-track | Optionality | Must maintain both proof types; interviews detect fake customer empathy | Real evidence for both tracks |
  | “Solutions architect” blur | Familiar enterprise title | May read non-coding | Only with loud coding evidence |
  | Internal-stakeholder stories as FDE proxy | Available without field title | Weaker than true customer embed — label honestly | Capstone / internal pilots |
  | Open-source “messy domain deploy” | Public proof | May not satisfy enterprise SSO/VPC questions alone | Early-screen supplement |
  | One resume, dual header | Speed | Dilutes if evidence thin for one track | Usually weaker than two PDFs |
  | Two tailored PDFs | Higher pass rate per pile | Must keep both current | Applying both tracks same week |

  `[NEEDS MORE RESEARCH]`: whether Applied AI Engineer and FDE ladders will converge industry-wide; how much travel willingness to signal in the first recruiter call for OpenAI/Anthropic FDE (~25–50% in postings); whether open-source “messy domain” deploy can substitute in FDE screens without EOR customer work; whether Anthropic’s Applied AI branding is a meaningful resume keyword outside Anthropic; whether dual-track candidates get dinged for “unclear focus” or rewarded for optionality at frontier labs. How much employer anonymization is required when FDE-style stories come from day-job work is also unresolved in research.

* **Failure Modes:**  
  - FDE-sounding resumes without customer stories → reject.  
  - Applied resumes without eval/production depth → reject.  
  - Dual-track without dual **proof** is worse than a single honest track.  
  - Same resume spray to every AI title.  
  - Fake customer empathy detected in interview.  
  - Comp/travel surprises after verbal yes — didn’t know which game you were in.  
  - Calling internal stakeholders “enterprise embed” without labeling honesty.

* **Average vs. Strong Engineer:**  
  **Average / Common:** Same resume spray to every AI title; no track-specific summary.  
  **Strong:** Tailored summary + 2–3 bullets per track; portfolio section matches; two talk tracks for the same repo; practice customer-scenario questions (incomplete data access, conflicting stakeholders, security review blocking prod keys, success criteria undefined).  
  **Senior:** Two talk tracks rehearsed; travel/constraints stated early for FDE; safety/ACL story ready for Anthropic-style loops; Applied loops deepen ranking metrics, judge calibration, cost routing ([Hamel](https://hamel.dev/blog/posts/evals/); [Huyen platform](https://huyenchip.com/2024/07/25/genai-platform.html)).

* **Worked Example:**  
  Same Deployment Copilot repo, two 90-second openings:

  1. **Applied:** “I shipped hybrid retrieval + citation aligner for Deployment Copilot; measured faithfulness 58%→81% and p95 under 2s; failed on chunk-boundary misses found in open-coding; fixed by section-aware split + golden promotion; CI gates prompt/retrieval changes.”  
  2. **FDE:** “Stakeholder needed ACL-safe runbook answers under tenant isolation; I scoped a thin cite-or-abstain slice; unblocked with filter-before-rank + undocumented-API adapter; productionized with contract tests; codified the adapter as a reusable MCP/tool template.”

  Fill the dual-track one-pager: Applied proofs = eval harness, latency/cost, hybrid architecture; FDE proofs = integration unblock, stakeholder freeze, rollout + pattern. Public links point to the matching qads.us / case blurb. Apply to one OpenAI/Anthropic FDE posting and one product Applied AI posting with **different** resume PDFs the same week when both tracks are real.

* **Apply It:**  
  1. Decide which track you apply to **this week**; freeze LinkedIn headline + resume header to that north star.  
  2. Write two 90-second openings for the same flagship (Applied spine vs FDE spine).  
  3. Fill the dual-track one-pager from capstone / qads.us evidence.  
  4. Maintain tailored summary + 2–3 bullets per track; keep the other track’s PDF ready.  
  5. Rehearse customer-scenario blockers for FDE; deepen eval/cost/architecture for Applied.  
  6. Signal travel willingness early when postings cite ~25–50%.  
  7. If you lack EOR customer work, use honest substitutes (internal stakeholders, messy OSS deploy, nonprofit thin-slice, capstone integration constraints) — never inflate to “enterprise embed.”  
  8. Use Levels.fyi / secondary TC only for later negotiation prep — never resume body.

---

## Week 24 build checklist (end-to-end)

Use this as the chapter’s capstone sequence; every concept above maps here.

1. **Mirror one live posting:** Keyword checklist against OpenAI / Anthropic / Palantir verbs; mark evidenced vs do-not-claim.  
2. **Rewrite 5–7 bullets** from Week 23 STAR with Verb + system + constraint + metric + learning.  
3. **Ship / harden a &lt;5-minute portfolio case** (Deployment Copilot or qads.us): six MVP fields, architecture matches code, three metrics, failure→fix, repro.  
4. **Write dual talk tracks** + fill the dual-track one-pager for the same flagship.  
5. **Freeze resume header + LinkedIn headline** for this week’s track; keep the other track’s tailored PDF ready.  
6. **Site QA + stranger skim** before sending links.  
7. **Interview artifact:** tailored resume (1–2 pages) + portfolio/qads.us case that survives 5 minutes + dual-track one-pager + keyword checklist marked against a live JD.

When those steps are true, Week 24 is done in the syllabus sense: Week 22–23 evidence is hire-readable on resume, portfolio, and dual-track surfaces.

---

## Looking ahead

Week 25 opens **Phase 7 — Supplementary Electives** with **context engineering** as an explicit discipline: memory (session vs persistent), compaction, isolation, and failure modes (stale context, poisoning, lost handoffs — plus distraction / confusion / clash). Electives can append after the Week 24 capstone packaging or interleave earlier (for example after Phase 3); **this course appends them** after Week 24. Next week you add a named **context-management layer** to the Phase 3 agentic stack — session memory with a compaction threshold, per-agent isolation namespaces, and a joinable context failure log — without inventing a new model API and without reopening the Week 22 freeze or inventing resume metrics. Resume / portfolio maintenance stays available; the deep work shifts to curating the token set the model sees each turn.

---

## Compilation notes

- All concept sections above are grounded in `research/phase-6/week-24-portfolio-positioning/` (`00`–`03`, README; source map consulted for URL provenance only).  
- `[NEEDS MORE RESEARCH]` markers appear where research Open Questions leave a claim ungrounded: Prompt Engineer headline harm in 2026; MCP first-class bullet scope for Anthropic apps; one vs two resumes when dual-applying; Applied/FDE ladder convergence; travel-signal timing; OSS messy-domain as FDE substitute; Anthropic “Applied AI” keyword outside Anthropic; dual-track focus ding vs optionality reward; employer anonymization for day-job FDE stories; chat-UI vs CLI+eval sufficiency; hobby cost dashboards; portfolio-assistant abstain risk; one deep vs three medium cases. Those open questions were **not** resolved with invented answers.  
- Outside URLs from research are cited inline where the notes already named them; operational detail was inlined from the notes.  
- Comp figures from Levels.fyi / secondary reports are treated as **directional ranges for negotiation**, never resume content — matching research policy.  
- Editorial pass: Prerequisites Recap bridges Week 23 (system design interview drills, STAR bank); Looking ahead bridges Week 25 / Phase 7 elective (context engineering: memory, compaction, isolation, failure modes; electives append after capstone in this course); no new technical claims beyond research.  
- Phase 7 elective depth is explicitly deferred — freeze hire-readable packaging here; context-management layer comes next.
