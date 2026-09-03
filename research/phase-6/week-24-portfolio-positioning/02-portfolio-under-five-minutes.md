# 02 — Portfolio pages that show system + metrics + failure in &lt;5 minutes

> Week 24 — Portfolio positioning  
> Research notes (raw). Meta-concept: hiring managers and FDEs skim — a portfolio that cannot communicate in **&lt;5 minutes** fails.

---

## Fundamentals

A portfolio for Applied AI Engineer / FDE loops is not a gallery of UIs. It is a **drillable system narrative**: architecture that matches code, auditable metrics, and a failure→fix story. This maps directly to Week 22’s demo narrative and Week 23’s STAR extraction.

### Minimum viable portfolio artifact (one flagship)

1. **One-liner job-to-be-done** — user + stakes.  
2. **Architecture diagram** — online vs offline paths; boxes match real code.  
3. **Three metrics** — quality (eval), latency (p95), cost proxy.  
4. **Failure narrative** — top failure mode from error analysis → fix → delta.  
5. **Run / repro** — demo link, `make eval`, or video backup.  
6. **Non-goals** — scope freeze honesty.

Public “AI portfolio” repos that read as senior tend to emphasize ADRs, tests, reproducible evals — not UI chrome alone (study structure, don’t copy claims: e.g. [rubsj/ai-portfolio](https://github.com/rubsj/ai-portfolio)).

### Five-minute script (default)

| Clock | Beat | Anti-pattern |
|-------|------|--------------|
| 0:00–1:00 | Problem / user / stakes | Starting in model names |
| 1:00–2:00 | Architecture (online + offline) | Vapor boxes not in repo |
| 2:00–3:30 | Metrics + eval evidence | Vibes-only screenshots |
| 3:30–4:30 | Failure → fix → delta | Hiding failure; tutorial clone |
| 4:30–5:00 | What’s next / hire me for | Feature roadmap dump |

Align with Week 22’s longer demo spine when you have a live walkthrough: user → freeze → architecture → success → controlled failure → metrics ([Week 22 narrative](../week-22-capstone-integration/03-technical-demo-narrative.md) in the curriculum corpus).

### What “opening the hood” means on a page

Above the fold or one click away, show at least one of:

- Retrieved chunks / scores / ACL filters  
- Citation highlights aligned to answer spans  
- Tool-call JSON (success + structured error)  
- Eval command output or golden-set row  
- Trace / triage screenshot (redacted)

Hamel’s product-eval ethos: you should be able to debug quickly because traces, assertions, and navigation exist ([Your AI Product Needs Evals](https://hamel.dev/blog/posts/evals/)). A portfolio that cannot show where a citation came from fails the trust test the same way a demo does.

### Progressive complexity (Huyen)

Chip Huyen’s GenAI platform essay is a checklist, not a feature wishlist: model API → guardrails → context (RAG/tools) → cache/route → logging/evals — add components when failure modes demand them ([Building a Generative AI Platform](https://huyenchip.com/2024/07/25/genai-platform.html)). Portfolio pages should show **which layer you added and why**, not every buzzword.

### FDE flavor subsection (when targeting field roles)

Add an **integration constraints** block:

- Auth / SSO / VPC / residency  
- Data access reality (export vs API)  
- Legacy tool / messy schema  
- Stakeholder success metric freeze  
- What you would **codify** next as a playbook / MCP / template  

Palantir FDSE narratives emphasize composing platform capabilities under customer constraints, not inventing a new platform per engagement ([Day in the Life](https://blog.palantir.com/a-day-in-the-life-of-a-palantir-forward-deployed-software-engineer-45ef2de257b1)). Visual metaphor: composed workflow demos ([YouTube `bPGnvfyMuxE`](https://www.youtube.com/watch?v=bPGnvfyMuxE)).

### qads.us as the default public surface

For this curriculum owner, [qads.us](https://qads.us) showcase items (Today in AI, Voice Mirror, MarketSignal Agent, Portfolio graph) should each eventually satisfy the six MVP fields. Prefer linking recruiters to a **single deep case** over the homepage alone. Dual-track blurbs live in the week overview ([00](00-week-overview.md)).

---

## Alternatives & Tradeoffs

| Portfolio format | Pros | Cons |
| --- | --- | --- |
| Live demo + short case study | Highest trust | Uptime/cost; can flake in interview |
| Case study + recorded walkthrough | Reliable | Weaker “ops” signal unless traces shown |
| GitHub README only | Easy | Easy to ignore; weak narrative |
| Blog post novel | SEO | Too long for screeners |
| Multi-project grid without depth | Looks busy | No drillable system |
| Chat UI on portfolio | Engagement | Must abstain gracefully; else toy signal |
| Cost dashboard at hobby scale | Shows ops taste | Numbers must be honest / dated |

**Practical default:** recorded walkthrough + live primary + `make eval` backup. Live-only signals ops confidence but needs a rollback story when the demo dies mid-loop (public reports of OpenAI-style FDE loops emphasize defending decisions under recorded or live scrutiny).

---

## Necessity

Interviewers increasingly ask for project deep-dives. Without a failure narrative, portfolios look like tutorial clones. Without metrics, claims are non-auditable. Without architecture matching code, diagrams read as slideware. Without a five-minute path, busy FDE/hiring managers bounce.

---

## Industry Practice

| Bar | What it looks like |
|-----|--------------------|
| **Common** | Hero GIF of chat UI; “built with LangChain”; no evals |
| **Strong** | Architecture + 3 metrics + failure→fix + repro command |
| **Senior / FDE** | Integration constraints; refusal/grounding demo; dated golden-set; codify note |

Practical rules:

- Pin golden-set size, model IDs, date of last eval run.  
- Show **refusal / grounding** behavior, not only happy-path GIF.  
- Link traces or redacted triage screenshots (Hamel-aligned).  
- For Applied loops: ranking metrics, judge calibration notes, cost routing.  
- For FDE loops: discovery → thin slice → production → pattern.  
- Career vocabulary / how practitioners narrate shipped systems: [AI Engineer YouTube](https://www.youtube.com/@aiDotEngineer); Chip Huyen FSDL interviews [`pli1K75PSa8`](https://www.youtube.com/watch?v=pli1K75PSa8); Hamel/Shreya on Lenny’s [`BsWxPI9UM4c`](https://www.youtube.com/watch?v=BsWxPI9UM4c).

Applied AI career framing (ships foundation-model apps): secondary path writeups exist (e.g. [Rockstar Applied AI path](https://rockstardeveloperuniversity.com/career-path/applied-ai-engineer-career-path/)) — use as framing, not as citation of your results.

---

## Concrete Scenario (URL)

**Exercise:** Pick one qads.us showcase or the Week 22 capstone. Write a one-page case (README or site section) with the six MVP fields. Time a colleague: give them five minutes, close the tab, ask them to restate (1) user job, (2) one architecture choice, (3) one metric, (4) one failure fix. If any answer is missing, the page failed.

Structural references:

- https://hamel.dev/blog/posts/evals/  
- https://huyenchip.com/2024/07/25/genai-platform.html  
- https://technoscripts.com/python-rag-system-design/  
- https://github.com/rubsj/ai-portfolio  
- https://qads.us  
- https://www.youtube.com/@aiDotEngineer  
- https://www.youtube.com/watch?v=pli1K75PSa8  
- https://blog.palantir.com/a-day-in-the-life-of-a-palantir-forward-deployed-software-engineer-45ef2de257b1  
- https://www.youtube.com/watch?v=bPGnvfyMuxE  

---

## Open Questions

- Is a chat UI mandatory, or is a CLI + eval report enough for Applied AI screens?  
- How much customer anonymization is needed for FDE-style case studies from paid work?  
- Should portfolios include cost dashboards even at hobby scale?  
- Does a portfolio assistant / chatbot help or hurt trust if abstain behavior is weak?  
- One flagship deep case vs three medium cases for dual-track applicants?

---

## Sources

- https://hamel.dev/blog/posts/evals/  
- https://huyenchip.com/2024/07/25/genai-platform.html  
- https://huyenchip.com/ml-interviews-book/  
- https://github.com/rubsj/ai-portfolio  
- https://technoscripts.com/python-rag-system-design/  
- https://qads.us  
- https://www.youtube.com/@aiDotEngineer  
- https://www.youtube.com/watch?v=pli1K75PSa8  
- https://www.youtube.com/watch?v=BsWxPI9UM4c  
- https://www.youtube.com/watch?v=bPGnvfyMuxE  
- https://blog.palantir.com/a-day-in-the-life-of-a-palantir-forward-deployed-software-engineer-45ef2de257b1  
- https://rockstardeveloperuniversity.com/career-path/applied-ai-engineer-career-path/  
