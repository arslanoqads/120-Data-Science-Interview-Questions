# 04 — Agent benchmarks (τ-bench, WebArena, AgentBench)

> Week 15 — Research-level literacy; not a product ship gate  
> Research notes (raw).

---

## Fundamentals

Public agent benchmarks exist so teams can **compare models/harnesses** and **steal grader patterns**. They are **not** a substitute for private product evals (cost, safety, maintainability, your SOPs). Anthropic: use them as inspiration (state checks, user sims, isolation); **read transcripts** before taking a leaderboard at face value.

This file goes deeper than names. Primary three for the syllabus: **τ-bench / τ²-bench**, **WebArena**, **AgentBench**. Adjacent (Anthropic post): SWE-bench Verified, Terminal-Bench, OSWorld, BrowseComp.

### τ-bench (Tool-Agent-User) — Sierra, 2024

**Paper:** Shunyu Yao, Noah Shinn, Pedram Razavi, Karthik Narasimhan — *τ-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains* ([arXiv:2406.12045](https://arxiv.org/abs/2406.12045)). **Code:** [sierra-research/tau-bench](https://github.com/sierra-research/tau-bench).

**Problem it attacks.** Prior agent/tool benchmarks often give the agent **all information in one shot** and have **no human in the loop** and **no domain policy**. Real support agents must (1) talk to users **and** APIs over a long horizon, (2) follow **complex written policies**, (3) stay **consistent** across millions of interactions.

**Formulation.** Each task is a POMDP. State = **DB ⊗ user**. Actions = DB APIs ∪ natural-language to the user. The agent **cannot see** raw DB rows — only API observations. The user **cannot see** tool traces. A **markdown policy** partially describes the world model (some rules enforced in APIs, some only in the document — e.g. baggage allowances the agent must compute).

**Construction.** Modular: JSON databases, Python API tools, policy markdown, JSON tasks. Three stages: manual schema/API design, LM-assisted data entries, **manual** scenario generation/verification for the user simulator.

**User simulation.** An LM (paper: gpt-4-0613) plays the user from a scenario instruction + chat history. Stochastic wording; same **goal**. Episode ends when the user emits `###STOP###`.

**Grading (outcome-centric).** Compare **database state at end** to an **annotated goal state**. The **transcript is not graded**, so conversations may vary if the DB matches. This is the support-domain analogue of WebArena functional correctness.

**pass^k.** Probability that **all k i.i.d. trials** succeed — reliability under user-sim stochasticity. Distinct from HumanEval-style **pass@k** (at least one success).

**Headline results (paper era).** Function-calling gpt-4o-class agents: **&lt;50%** task success; retail **~61% pass^1** vs airline **~35%**; **pass^8 &lt; ~25%** retail. Failures: complex DB reasoning, **policy following**, **compound (multi-intent) requests**.

**Domains (original):** τ-retail, τ-airline (customer service).

### τ²-bench — Sierra et al., 2025

**Paper:** Barres, Dong, Ray, Si, Narasimhan — *τ²-Bench: Evaluating Conversational Agents in a Dual-Control Environment* ([arXiv:2506.07982](https://arxiv.org/abs/2506.07982)). **Code:** [sierra-research/tau2-bench](https://github.com/sierra-research/tau2-bench).

**Gap:** original τ-bench is **single-control** — only the agent has tools; the user is a passive information source. Real tech support is **dual-control**: the user also acts on a shared world (reboot the modem, toggle a setting).

**What’s new (paper claims):** (1) **Telecom** domain as a Dec-POMDP where **both** agent and user have tools; (2) compositional task generator from atomic components; (3) user-sim constrained by tools and observables; (4) ablations separating reasoning vs **communication/coordination**.

**pass^k culture continues.** Reported pass^1 drops from retail/airline to telecom (e.g. gpt-4.1 ~74% / ~56% vs ~34% telecom in secondary summaries of the paper’s Figure 3 — **re-read the PDF** before quoting in a lecture). pass^k decays faster on telecom → **inconsistency** under dual control.

Anthropic cites τ²: Opus 4.5 found a **policy loophole** on a flight task — failed the written eval, better for the user. Literacy point: **outcome + policy graders can fight user value**.

Repo (2026): domains include `mock`, `airline`, `retail`, `telecom`, `banking_knowledge`; half-duplex and **full-duplex voice** paths; `tau2 run --num-trials`.

### WebArena — CMU, NeurIPS 2024 Oral

**Paper:** Zhou, Xu, Zhu, et al. — *WebArena: A Realistic Web Environment for Building Autonomous Agents* ([arXiv:2307.13854](https://arxiv.org/abs/2307.13854)). **Site:** [webarena.dev](https://webarena.dev/). **Code:** [web-arena-x/webarena](https://github.com/web-arena-x/webarena).

**Problem it attacks.** Agents were tested in **oversimplified** or **static cached** sites; evals compared **action strings** to a reference path, ignoring **functional correctness** and **valid alternatives**.

**Environment.** Self-hosted, reproducible Docker (not live Amazon — CAPTCHA, drift). Four site categories from authors’ real browsing: **e-commerce**, **social forum**, **collaborative software (GitLab)**, **CMS**, plus **map / calculator / scratchpad**, Wikipedia, manuals. Data imported from real counterparts. **Gym-style** API. **Reset** to a deterministic initial state between evals (required for isolation — same lesson as Anthropic harness hygiene).

**Observations.** URL, tabs, page as **screenshot**, **DOM**, or **accessibility tree** (compact structured). Optional viewport crop. **Multi-tab** tasks (first web env to emphasize this).

**Actions.** Click/type/hover/keys; tab open/close/switch; URL nav. Element reference by **coordinates** or **element ID** (n-way classification).

**Benchmark.** **812** long-horizon tasks; high-level NL intents (not “click science subreddit”).

**Grading.** `r(actions, states)` via **programmatic validators** — e.g. **repository contents**, **whether an order was placed** (backend), URL/page predicates. Authors: more reliable than surface-form action match; allows **many valid paths**. `evaluator_router(config_file)` in the official `minimal_example.py`.

**Headline results.** Best **GPT-4** agent **14.41%** end-to-end success vs **human 78.24%**. Authors: weak **active exploration** and **failure recovery**.

**Family (site):** VisualWebArena (ACL 2024, multimodal), WebArena-Infinity, TheAgentCompany (ICML 2025). Canonical repo recommends **BrowserGym / AgentLab** for newer experiments while keeping this tree for **paper reproduction**.

Anthropic computer-use section: WebArena uses URL/page checks **plus backend** for mutations (“confirmation page appeared” is not enough).

### AgentBench — THUDM, ICLR 2024

**Paper:** *AgentBench: Evaluating LLMs as Agents* ([arXiv:2308.03688](https://arxiv.org/abs/2308.03688); [ICLR hash](https://proceedings.iclr.cc/paper_files/paper/2024/hash/e9df36b21ff4ee211a8b71ee8b7e9f57-Abstract-Conference.html)). **Code:** [THUDM/AgentBench](https://github.com/THUDM/AgentBench).

**Problem it attacks.** Need a **multi-dimensional** eval of LLM-as-agent in **interactive, multi-turn** environments — not a single web or single game.

**Eight environments**

| Env | Origin | What it tests (docs/paper) | Typical metric |
|-----|--------|----------------------------|----------------|
| **OS** | New | Ubuntu Docker bash; questions with deterministic answers or operation sequences | Success rate (SR) |
| **DB** | New | Real SQL interfaces, multi-table | SR |
| **KG** | New | Knowledge-graph tooling | SR / task-specific |
| **DCG** | New | Digital card game | Reward / win |
| **LTP** | New | Lateral thinking puzzles | SR |
| **HH** | ALFWorld / TextWorld | Household text games | SR |
| **WS** | WebShop | Web shopping | Reward / SR |
| **WB** | Mind2Web (adapted for prompted LLMs) | Browse/click/type across sites | SR / F1-style |

Five **fresh** domains + three **recompiled**. Docker images for several tasks (`longinyu/agentbench-*`).

**Findings.** Large gap: top **API** models vs many **OSS ≤70B**. Failure reasons: **long-term reasoning**, **decision-making**, **instruction following**. High-quality **multi-round alignment** data helps; **code training** has **ambivalent** (not uniformly positive) effects across tasks — contrary to a naive “train on code → better agent” story.

**How to use it in an FDE curriculum.** It is a **breadth** probe (can the model act in OS vs DB vs web?), not a customer-support policy test (that’s τ-bench) and not a realistic multi-site web product test (that’s WebArena). Map AgentBench OS/DB failures onto Week 11 tool loops; map ALFWorld/WebShop onto long-horizon C4.

### Adjacent benchmarks (Anthropic map)

| Name | Role in eval design |
|------|---------------------|
| **SWE-bench Verified** | Outcome via **fail-to-pass tests without regressions**; saturation warning (&gt;80%) |
| **Terminal-Bench** | End-to-end technical tasks; Harbor registry; **ambiguous filepath** grader bugs |
| **OSWorld** | Full OS; scripts inspect files, configs, DB, UI properties |
| **BrowseComp** | Hard web needles; easy to verify, hard to solve |

---

## Alternatives & Tradeoffs

| Choice | Pros | Cons |
|--------|------|------|
| **Public benchmarks** | Comparable, citable, steal graders | Saturating, contaminable, missing cost/safety/your SOP |
| **Private domain evals** | Predictive for users | Expensive; not comparable externally |
| **Hybrid** (syllabus) | Literacy + ship gate | Two harnesses to maintain |
| τ-bench-style **user sim** | Tests information gathering | Sim ≠ real users; sim LLM cost; dual-control still young |
| WebArena **self-host** | Reproducible, backend truth | Heavy Docker; 812-task runtime |
| Action-sequence match (Mind2Web original style) | Easy | Punishes valid paths (WebArena critique) |
| Leaderboard chasing | Hiring signal | Gaming; pass^k still rare outside τ-family |

Use benchmarks to compare **models/harnesses**. Use **private product evals** for deployment. Review literature (and Anthropic) stress the disconnect.

---

## Necessity

Without shared benchmark **literacy**, teams reinvent **text-match** evals and then discover τ-bench/WebArena already solved “grade the DB/backend.” Without **private** evals, teams overfit public sets and fail in production (your refund SOP is not GitLab issue #812).

pass^k literacy prevents reporting **pass@8** as if the write agent got more reliable.

---

## Industry Practice

- **Common:** paste a WebArena or SWE-bench number on a slide; never run isolation/reset; never read a failing transcript.  
- **Strong:** borrow **grader patterns** (state check, functional validator, user sim, pass^k, isolated trials); run a **tiny** public slice to test the harness; invest in **20–50 private** tasks (Anthropic). Harbor for containerized tasks; Braintrust/LangSmith/Langfuse as product harnesses (Anthropic appendix).  
- **FDE bar:** explain **why** τ-bench grades DB not chat; **why** WebArena refuses action-string match; **why** AgentBench is eight-env breadth; name **pass^k** vs **pass@k**; refuse to ship on a public leaderboard alone.

Google Vertex (Jan 2025): trajectory exact / in-order / any-order / precision / recall / single-tool — industrial cousin of LangSmith match modes, not a replacement for τ-bench policy+DB.

---

## Concrete Scenario

**τ-bench airline (paper Figure 1):** user wants to change a basic-economy flight; **policy** may require reject + cancel/rebook instead of a naive change. Agent must use reservation APIs **and** talk. Success = **DB** matches gold, not a particular utterance.  
https://arxiv.org/abs/2406.12045 · https://github.com/sierra-research/tau-bench  

**WebArena Figure 2-style:** find Pittsburgh art museums (Wikipedia), plan a route (map), update a **GitLab README**. Grader checks **repo contents**, not the click path. GPT-4 14.41% vs human 78.24%.  
https://webarena.dev/ · https://arxiv.org/abs/2307.13854 · https://github.com/web-arena-x/webarena  

**AgentBench OS:** “count files matching X outside `/home`” in Ubuntu Docker — SR. Failure often **instruction following** over many turns.  
https://github.com/THUDM/AgentBench · https://arxiv.org/abs/2308.03688  

**Anthropic** discussion of these families: https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents  

**YouTube (eval process, not the papers):** Hamel https://www.youtube.com/watch?v=DZxaPNYi_k0 · https://www.youtube.com/watch?v=BsWxPI9UM4c  

---

## Open Questions

- Leaderboard gaming vs real reliability (**pass^k** still rare outside τ-family).  
- Multimodal / computer-use eval **cost** (screenshots vs DOM — Anthropic Chrome: pick the cheaper observation).  
- Multi-agent **A2A** benchmarks still immature vs single-agent.  
- τ³ knowledge/voice extensions — how much of Week 15 should wait for voice? (Don’t block this week.)  
- When WebArena-Infinity / VisualWebArena supersede the 812-task canonical split for teaching?

---

## Sources

- https://github.com/sierra-research/tau-bench  
- https://arxiv.org/abs/2406.12045  
- https://github.com/sierra-research/tau2-bench  
- https://arxiv.org/abs/2506.07982  
- https://webarena.dev/  
- https://arxiv.org/abs/2307.13854  
- https://github.com/web-arena-x/webarena  
- https://github.com/THUDM/AgentBench  
- https://arxiv.org/abs/2308.03688  
- https://proceedings.iclr.cc/paper_files/paper/2024/hash/e9df36b21ff4ee211a8b71ee8b7e9f57-Abstract-Conference.html  
- https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents  
- https://cloud.google.com/blog/products/ai-machine-learning/introducing-agent-evaluation-in-vertex-ai-gen-ai-evaluation-service  
- https://docs.langchain.com/langsmith/trajectory-evals  
- https://langfuse.com/resources/engineering/ai-agent-evaluation  
