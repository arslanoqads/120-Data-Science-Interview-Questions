# Chapter 17 — LLM-as-judge & observability

> **Phase 4 — Evals and Observability**  
> **Editorial status:** COMPLETE  
> **Source of truth:** `research/phase-4/week-17-llm-judge-observability/`  
> **Syllabus Build:** You already have **Week 16 labels and a custom taxonomy**. This week you **automate residual subjective failures** and **make traces usable as a product**. (1) **Design judges, not dashboards of 1–5s.** One **binary** judge per high-impact Week 16 failure mode that needs judgment (`should_have_clarified`, faithfulness given retrieved docs). Pass/Fail + written critique. Principal domain expert owns the standard. (2) **Calibrate against Week 16 labels.** Split labeled examples (Hamel: ~10–20% few-shot train, ~40–45% dev, ~40–45% held-out test; aim 30–50 Pass and Fail in dev and test). Gate on **TPR and TNR**. Do not ship a judge that fails the gate. Recalibrate when the app model, judge model, or product criteria change. (3) **Prefer code evals** for objective failures (JSON, schema, citation IDs ⊆ retrieved IDs, tool name). Reserve LLM judges for the rest. Put several code evals in CI; LLM judges sparingly in CI or on a **sampled schedule**. (4) **Tracing dashboard.** Instrument hierarchical traces (Langfuse **and/or** Phoenix). Generations carry `model`, params, tokens, cost. Attach retrieved context on the observation you will judge. Tag `userId` / `sessionId` / `version` / `env`. (5) **Production monitoring.** Dashboards for volume, errors, p95 latency, cost/day and cost/successful-task, and **1–3 calibrated** quality timeseries. Alerts open **traces**, not just pages. Sample online judges (2–10%). Blocking safety stays **in-request**; async evaluators are for trends and triage.

---

## Prerequisites Recap

Before this week you should already have from Week 16:

- An **error-analysis-first** habit: sample ~100 diverse/stratified traces; personally open-code **≥30** (20–50 in ~30 minutes after significant prompt/model/feature changes); one **benevolent dictator** (domain expert) owns Pass/Fail + free-text notes.  
- A **custom failure taxonomy** from open → axial coding: **5–10** binary, named, one-sentence categories grounded in *this* app (`missing_device_lookup`, `should_have_clarified` — not generic `hallucination`). Surface-similar failures with different root causes are split.  
- **Frequency** quantified: boolean relabel of the sample; **failure rate per category**; prioritize **rate × impact**; prompt/tool bugs fixed **before** building judges.  
- **Synthetic edges** only as **inputs** through the live stack when production undersamples a known combo — not synthetic gold answers, not synthetic rates as production rates.  
- A working **data flywheel**: labeled failures promoted into a **regression eval set**; Level-1 assertions and/or monitors on change (CI) plus a **production sample** (Nova Escola ~2% daily as an existence proof); critiques stored on labeled rows for few-shot judge work.  
- From Week 15 (still in force): structured traces, split scores, trajectory vs outcome, C1–C4 fixtures — Week 16 mined them; this week automates the residual judgment-heavy modes.

You do **not** need a calibrated LLM-as-judge, an observability-platform bake-off, or production quality dashboards yet as *finished* products — that is what this week ships. You **do** need the Week 16 taxonomy and expert labels; without them there is nothing trustworthy to shadow.

---

## What this week builds

Week 15 **instrumented** agents. Week 16 **read traces**, built a **custom failure taxonomy** via open coding, quantified **rate × impact**, and closed the **production → labels → eval set → regression** flywheel. Week 17 is the **automation and instrumentation** half of Phase 4. This week does **not** invent new failure modes from a vendor catalog — it uses Week 16’s taxonomy and labels. It answers four questions Hamel Husain, Shreya Shankar, Langfuse, Phoenix, and OpenAI all treat as the *second* half of product evals:

1. **Can an LLM shadow the Week 16 expert** on residual *subjective* failures? (LLM-as-judge design)  
2. **How do we know the shadow is trustworthy?** (alignment / calibration: TPR/TNR on held-out labels)  
3. **When is a `json.loads` enough?** (code-based vs model-based evals)  
4. **Where do scores, tokens, and latency live so a team can act?** (tracing platforms + production dashboards)

**Do not start Week 18 (deployment infrastructure — containers, K8s fluency, CI/CD stages, Terraform) from this chapter** — this week **calibrates LLM judges against Week 16 expert labels**, **chooses code vs model evals**, **instruments tracing (Langfuse / Phoenix)**, and **ships production dashboards** (cost, latency, error, quality, drift). Putting the same service on a real delivery path is next week.

**What you ship this week**

```
Week 16 labels + taxonomy
        │
        ├── objective failures ──► code evals ──► CI (every change)
        └── judgment failures ──► binary judge + few-shot critiques
                                      │
                              TPR/TNR on held-out expert labels
                                      │
                              pass gate? ──no──► iterate prompt / rubric / model
                                      │ yes
                                      ▼
                         offline experiments (datasets)
                                      │
                         sampled observation-level judges (prod)
                                      │
                         dashboards: cost · latency · errors · scores · drift
                                      │
                         disagreements + low scores ──► annotation queues ──► flywheel
```

Interview artifact = **one calibrated binary judge** with TPR/TNR on a held-out Week 16 set + **a screenshot/description of a tracing dashboard** that shows a generation with tokens/cost and a score attached + **one code eval that replaced a would-be judge**.

Read the concepts in order. Each section’s **Worked Example** and **Apply It** assume Deployment Copilot’s Week 16 taxonomy and labels being automated and instrumented for the first time.

---

### LLM-as-judge design (critique shadowing)

* **Fundamentals:**  
  An **LLM-as-judge** (model-based evaluator) is a model prompted to **score or label another system’s outputs** using explicit criteria. It is not a generic “quality” API. Practitioner consensus (Hamel *Using LLM-as-a-Judge*; YouTube Hamel `DZxaPNYi_k0`): treat the judge as a **classifier** of a **named Week 16 failure mode**, not as a 1–5 personality test. Week 16 already decided *which* modes need judgment (error analysis → open coding → taxonomy → rate × impact); this section designs the shadow for those residual modes.

  Use it when quality is **subjective or semantic**: tone, persona, “should have asked a clarifying question,” faithfulness *given retrieved context*, pedagogical appropriateness. Do **not** use it as the first metric you invent (that was Week 16’s job) and do **not** use it for failures a parser can catch.

  **Human** here = the **principal domain expert** (Hamel: psychologist, lawyer, CS director, lead teacher — or founder in a tiny company). Correlation / agreement is **with that expert’s Pass/Fail**, not with a crowd of random raters and not with ROUGE.

  Hamel’s diagnosis of failed judge programs: (1) **too many metrics** — unmanageable dashboards; (2) **arbitrary 1–5 scales** — nobody can say what a 3 vs 4 is; (3) **ignoring domain experts**; (4) **unvalidated metrics** that don’t reflect users or the business.

  The replacement technique is **critique shadowing**: the judge learns to produce the **same Pass/Fail + critique style** as the expert.

  **Critique shadowing design steps** (Hamel, Oct 2024 guide, updated 2026):

  1. **Find the principal domain expert** — one (maybe two) people whose taste *is* product quality. Developers acting as proxy “because they’re available” is a failure mode.  
  2. **Create a diverse dataset** — production sample **and/or** synthetic **inputs** through the **real** system. Do **not** synthesize gold *answers*.  
  3. **Expert: binary Pass/Fail + detailed critique** — critiques rich enough to become few-shots (a new employee could apply them). Fails must name the **critical** miss.  
  4. **Fix errors first** — if the system is still full of prompt bugs, do not freeze a judge on a moving target. Level 1 assertions should already catch pervasive format bugs.  
  5. **Build the judge from expert examples** — Honeycomb Query Assistant: judge prompt includes domain facts, guidelines, and **XML-ish few-shots** of input + output + `{critique, outcome}`. Ask the model to **write the critique first**, then the label.  
  6. **Iterate until expert and judge converge** — Honeycomb: **three iterations** to **>90%** agreement on a **balanced** set. Then (and only then) apply the judge to unseen data for **error rates**.  
  7. **Specialize later** — after error analysis, add **narrow** judges or **code** assertions. Do not start with a zoo of specialized judges.

  Hamel: **start simple**. Binary forces articulation. You can add complexity later.

  **G-Eval** (Liu et al., EMNLP 2023): GPT-4 + **chain-of-thought** criteria generation + **form-filling** scores; Spearman **0.514** with humans on summarization (SummEval), beating ROUGE/BLEU; caveat **bias toward LLM-generated text**. Use as evidence that *well-prompted* judges can correlate with humans on NLG — **not** as a drop-in product KPI. If you use G-Eval-like CoT, still **calibrate on your expert labels**.

  **Prompt anatomy** that correlates (Hamel + Langfuse):

  | Piece | Why |
  |-------|-----|
  | Role + **one** failure mode | “You judge whether a clarifying question was required,” not “score quality 1–5” |
  | Criteria in the expert’s language | Copied from axial-coded Week 16 notes |
  | Same **context** the expert had | User metadata, retrieved docs, tool results |
  | Few-shot **critiques** (diverse Pass and Fail) | Missing/terse/non-diverse examples are the #1 prompt bug |
  | Structured output | JSON `{critique, outcome}` or boolean + reasoning |
  | Temperature 0 / pinning | Repeatability |

  Langfuse: **System** = stable rubric; **User** = mapped variables; **Assistant** = few-shot of the *judge’s* reply shape. Prefer **observation-level** judges for production — they **do not load sibling spans**. If faithfulness needs retrieved docs, **write context onto the generation**. Trace-level evaluators are **deprecated** (Cloud cutover **2026-11-16**). Typical cost cited **~$0.01–0.10 per assessment** — **sample**.

  **Same model as producer?** Hamel/Shreya FAQ: for **scoped binary** judges, **usually fine** — the judge task ≠ the generation task; **TPR/TNR on held-out humans** decides. Start with the **most capable** judge; cost-optimize later. OpenAI cookbook: often prefer a **different** model when practical — treat as a **bias hedge**, not a religion.

  **Pairwise (A vs B):** OpenAI notes LLMs are stronger at **discrimination** than open generation of a score. Pairwise is excellent for **ranking prompts/models**; weaker as an **absolute CI gate**.

  **RAG-specific design:** claim extraction → binary support per claim → **aggregate in code** (never let the judge do the arithmetic). Forbid outside knowledge; allow paraphrase; don’t penalize “I don’t know” (Langfuse faithfulness). That design is closer to Hamel’s binary philosophy than a holistic 1–5 “faithfulness” slider.

  Langfuse FAQ claim: strong judges can reach **~80–90%** agreement with humans on many dimensions — **comparable to human–human IAA**. That is **marketing-adjacent**; still **calibrate on your labels**. Hamel: if two humans agree worse than chance (Nova Escola), **no judge can save a missing rubric**.

* **The Alternatives:**  

  | Judge design | Pros | Cons | When it fits |
  |--------------|------|------|--------------|
  | **Binary + critique (Hamel)** | Actionable; forces criteria; few-shots from critiques | Less nuance on dashboards; stakeholders want 1–5 | Default product judge for this syllabus |
  | Likert 1–5 multi-dim | Familiar exec slides | Uncalibrated; vanity; Field Guide trap | Avoid as product gate |
  | G-Eval-style CoT + form fill | Better NLG correlation in research | Cost; LLM-text bias; still needs product calibration | Optional research-style metric after calibration |
  | Pairwise preference | Strong for model/prompt ranking | Awkward absolute regression gates | Ranking experiments, not CI Pass/Fail |
  | Reference metrics (BLEU/ROUGE) | Cheap, deterministic | Weak human correlation for open-ended gen (G-Eval paper) | Not product quality |
  | Same model as producer | Ops-simple | Self-preference risk; OK if binary task aligns | Fine if TPR/TNR hold |
  | Stronger/different judge model | Bias hedge; OpenAI default advice | Procurement; latency; still needs labels | When alignment fails or as hedge |
  | Fine-tuned small judge | Cheap at scale | Hamel: rare; prefer PE; needs even more labels | After PE plateaus and labels exist |
  | Vendor hallucination template | Instant | Uncorrelated with Week 16 taxonomy | Exploration signals at most |

  The syllabus selects **binary + critique per failure mode** because Week 17’s build explicitly requires one calibrated binary judge against Week 16 gold — not a kitchen-sink score pack.

* **Failure Modes:**  
  - Optimize the product for the judge’s quirks (sycophancy, length, self-preference, G-Eval LLM-text bias).  
  - Create dashboards nobody trusts (Field Guide §5).  
  - Fail to catch the **taxonomy** failures you actually care about.  
  - Reward-hack (agent writes what the judge likes) — especially if the judge is in the training/improvement loop without humans.  
  - Build a judge **before** reading traces (Week 16) — rubric that never appears in production (Nova Escola mistake).  
  - Developers as proxy experts because they’re available.  
  - Terse critiques that cannot become few-shots.  
  - Observation-level faithfulness judge without retrieved docs **on** the generation (siblings invisible).  
  - Starting with eight specialized judges before one converges.

* **Average vs. Strong Engineer:**  
  **Average:** enable Langfuse/Phoenix “helpfulness” template; never sit with the expert; never few-shot critiques; ship a 1–5 multi-dim pack.  
  **Strong:** error analysis → **one** failure mode; expert labels (balanced Pass/Fail where possible); split few-shot / dev / held-out; iterate **prompt** with expert critiques (Honeycomb three loops); prefer PE over fine-tuning (Hamel has not had much luck with DSPy-style optimizers for this); gate TPR/TNR; log judge executions as traces (`langfuse-llm-as-a-judge`); version evaluator definitions; recalibrate on model or product change. Prefer boolean for Week 17 product judges unless aggregating claim-level binaries into a rate.

* **Worked Example:**  
  Deployment Copilot’s Week 16 taxonomy reserved `missing_runbook_lookup` and `should_have_clarified` for judgment. The principal domain expert (ops lead) already labeled Pass/Fail + critiques on those modes. You do **not** enable a vendor “hallucination + helpfulness” pack. You write one binary judge for `should_have_clarified`: system rubric in the expert’s language, few-shots from train-split critiques in XML-ish `{critique, outcome}` form, temperature 0, critique-first then label. Honeycomb-style spreadsheet compares judge vs expert; after three prompt iterations on the balanced set you move to held-out TPR/TNR (next section). For RAG faithfulness on runbook answers, you extract claims, binary-support each claim against docs attached **on the generation**, and aggregate the rate in code — never a holistic 1–5 faithfulness slider.

* **Apply It:**  
  1. From Week 16, pick **one** residual judgment-heavy failure mode (not a format bug).  
  2. Confirm the principal domain expert owns Pass/Fail + critique; fix obvious prompt/tool bugs first.  
  3. Draft a binary judge prompt: one failure mode, expert-language criteria, same context the expert had, diverse Pass/Fail few-shots, structured `{critique, outcome}`, temperature 0.  
  4. Prefer observation-level judges; attach retrieved context onto the generation being judged.  
  5. Iterate on disagreements until the expert and judge converge on the balanced set; do not ship uncalibrated.  
  6. Treat G-Eval / ROUGE as optional research evidence, not your product KPI.

---

### Judge alignment / calibration (TPR/TNR vs Week 16 labels)

* **Fundamentals:**  
  **Alignment** (product sense) = the judge’s labels match the **domain expert’s** labels on **held-out** data. **Calibration** (ops sense) = ongoing checks so that trust remains as data, prompts, models, and **criteria** drift. The held-out set is the Week 16 gold you already collected (and keep refilling via the flywheel) — not a fresh invented rubric.

  This is not “the model outputs a well-calibrated probability 0.73.” You may later use token probs (G-Eval-style); Week 17’s bar is **classifier performance vs humans**. Hamel (YouTube `DZxaPNYi_k0`): if you do not measure the judge against humans, **evals lose trust**.

  **Critique-shadowing measurement loop:**

  1. Expert labels Pass/Fail + critique (Week 16 gold).  
  2. Judge prompt asks for the **same** decision (+ rationale). Few-shots from **train** split only.  
  3. Iterate on **dev** where judge ≠ expert (read both critiques; fix rubric or examples).  
  4. Report **True Positive Rate** and **True Negative Rate** on **held-out test**.  
  5. Only then run the judge on unseen synthetic/production traffic to estimate **failure rates**.

  **Agreement is a trap** (Aakash masterclass / Hamel warning on Honeycomb): if failures are 10% prevalent, a judge that **always predicts Pass** is **90% accurate**. Honeycomb used raw agreement only because the set was **~50/50**. Default reporting:

  | Metric | Meaning for a **Fail = positive** (catching bad outputs) |
  |--------|----------------------------------------------------------|
  | **TPR** (recall / sensitivity) | Share of expert-Fails the judge also Fails — **catches real failures** |
  | **TNR** (specificity) | Share of expert-Passes the judge also Passes — **doesn’t flag goods** |
  | Precision | Of judge-Fails, how many are real — useful when paging humans |
  | Accuracy / % agreement | **Do not gate on this** under imbalance |
  | Cohen’s κ | Better than raw agreement; still **hides asymmetric errors** if used alone |

  Define the positive class explicitly (Fail vs Pass) in the alignment report next to the prompt version.

  **Splits and sample size** (Hamel):

  | Stage | Guidance |
  |-------|----------|
  | Discover failure modes / write rubric | ~30+ until no new modes (Week 16) |
  | **Validate a judge** | **~100–200 labeled examples per failure mode**; **<60** often has CIs too wide to conclude anything |
  | Split | **~10–20% train** (few-shot), **~40–45% dev**, **~40–45% final test** |
  | Balance | Aim **~30–50 Pass and 30–50 Fail** in **both** dev and test when possible |

  Leakage: few-shots must not include test items. Production online scores are **not** the alignment set — they estimate **prevalence**, biased by TPR/TNR.

  Langfuse: calibrate on a **small human-annotated sample** before trusting trend lines; typical judge **$0.01–0.10** per call — sample production. Faithfulness write-up: calibrate **20–50** answers vs a person **once for rubric wording**, then still keep a proper held-out set for gates.

  **Criteria drift** (Shankar et al., *Who Validates the Validators?*, UIST 2024 / arXiv:2404.12272): **EvalGen** generates candidate assertions/prompts; humans grade a subset; the system selects implementations that maximize alignment. Qualitative finding: **grading outputs changes the criteria** — **criteria drift**. Implication: you cannot fully specify the rubric a priori; Week 16 discovered criteria; Week 17 **must re-label** when the expert’s taste or the product moves. Hamel quotes the paper: people need outputs to define criteria and criteria to grade outputs.

  Nova Escola: two annotators initially agreed **less often than chance** → rewrite rubric **with pedagogical experts** → relabel → **then** automate judges. If IAA is broken, **alignment to “humans” is undefined**.

  OpenAI: **maintain agreement** between automated scoring and human feedback; continuous evaluation; anti-pattern = ignoring human feedback.

  **Tooling for the alignment conversation:** spreadsheets (Honeycomb); **AlignEval** (Eugene Yan, recommended by Hamel); Langfuse **annotation queues** + human vs judge scores on the same observation; Phoenix **annotations** on traces. Version **judge prompts**; store the **alignment report** next to the version.

  **Recalibration triggers:** human review at **regular intervals** and whenever something **material** changes (model upgrade, major prompt, new cohort). After early iterations, bias sampling toward **errors** but **keep some random**. Langfuse: updating the **project default judge model** changes **every** evaluator using it — that is a **recalibration event**, not a silent upgrade. Anthropic (*Planning to production*): combine rule-based, model-based, and **targeted human** grading.

  **G-Eval’s Spearman 0.514** is **not** your gate. Your gate is **your** expert’s held-out TPR/TNR.

* **The Alternatives:**  

  | Calibration practice | Pros | Cons | When it fits |
  |----------------------|------|------|--------------|
  | **Held-out TPR/TNR gates** | Honest; imbalance-aware | Needs enough Fail examples | Default ship gate for this syllabus |
  | Cohen’s κ / Spearman only | Single number; G-Eval uses Spearman vs humans | Hides asymmetric errors; research ≠ product gate | Complement, not sole gate |
  | Periodic human audits (weekly sample) | Catches drift | Ongoing cost | Always after shipping |
  | AlignEval / annotation-queue loops | Fast iteration | Tooling investment | Ongoing conversation |
  | Langfuse “small sample then trust trends” | Practical | Underpowered if you skip a real test split | Rubric wording only — still need held-out |
  | No calibration (“vendor template”) | Zero effort | Untrusted metrics | Never for product quality |
  | Bayesian-adjust online scores by known TPR/TNR | Statistically nicer prevalence | Rarely implemented; still need labels | [NEEDS MORE RESEARCH] for Deployment Copilot defaults |

  The syllabus selects **held-out TPR/TNR** because Week 17’s build explicitly refuses to ship a judge that fails that gate.

* **Failure Modes:**  
  - Online “quality” charts are fiction.  
  - You “fix” regressions that are judge noise — or miss real ones.  
  - Multi-annotator chaos: if two humans disagree worse than chance, the judge cannot align to a nonexistent standard — **fix the rubric first** (Nova Escola).  
  - Criteria drift happens **anyway** (EvalGen); unmeasured drift is silent policy change.  
  - Spot-check 10 examples once; ship; never re-check after a model bump.  
  - Few-shot leakage into the test set.  
  - Gating on raw agreement under class imbalance.  
  - Treating production online scores as the alignment set.

* **Average vs. Strong Engineer:**  
  **Average:** spot-check 10 examples once; ship; never re-check after a model bump; report “90% agreement.”  
  **Strong:** version judge prompts; store TPR/TNR (with class definition) next to prompt version and dataset version; recalibrate on **app or judge** model upgrades and on product/taxonomy changes; use **disagreements** as gold for taxonomy/rubric updates (criteria drift as a **feature**); separate **offline experiment** alignment from **online sampled** monitoring; Field Guide: binary + critiques + regular human–judge calibration + **strategic sampling** (don’t remove humans from hard cases). Note: OpenAI **Evals platform** read-only **2026-10-31**, shutdown **2026-11-30** — the *practice* of human–auto agreement remains; don’t couple the course to that UI.

* **Worked Example:**  
  Deployment Copilot collects ~150 expert-labeled examples for `should_have_clarified` (~75 Pass / ~75 Fail). Split: ~15% train few-shots, ~42% dev, ~43% held-out test (aiming 30–50 of each class in both). Fail = positive. After three prompt iterations on dev disagreements, held-out report shows TPR and TNR next to prompt version `clarify-judge-v3` and dataset version `w16-clarify-2026-09`. You refuse to ship until both rates clear the team’s gate. Online 5% sampling later estimates prevalence — it does **not** replace this report. When the app model upgrades, you treat that as a recalibration event; when Langfuse’s project-default judge model changes, every evaluator using it is a recalibration event too.

* **Apply It:**  
  1. Gather ~100–200 Week 16 labels per failure mode you will automate; refuse gates on <60.  
  2. Split ~10–20% train / ~40–45% dev / ~40–45% test; keep few-shots out of test.  
  3. Define Fail = positive; report TPR and TNR (not raw accuracy) on held-out.  
  4. Iterate on dev disagreements (read both critiques); store alignment report next to prompt + dataset versions.  
  5. Fix broken IAA / rubric before blaming the judge (Nova Escola).  
  6. Recalibrate on app or judge model upgrades, product/taxonomy changes, and criteria drift; keep some random traces in human batches.

---

### Code-based vs model-based evals

* **Fundamentals:**  
  Two automated evaluator families (Hamel/Shreya teaching, Langfuse, OpenAI graders) plus humans. Week 16’s taxonomy already split **objective** failures (fix or code) from **judgment-heavy** residuals; this section operationalizes that split into CI vs sampled judges.

  | Type | Mechanism | Best for |
  |------|-----------|----------|
  | **Code-based / deterministic** | Assertions, regex, JSON schema, exact match, tool-arg checks, length, allowlists, citation-ID subset | Objective, unambiguous failures |
  | **Model-based / LLM judge** | Prompted LLM (or classifier) scores output | Subjective, semantic, domain judgment |
  | **Human** | Expert review | Ground truth, calibration, high-stakes, rubric discovery |

  Langfuse also lists **user feedback** (sparse, clear) and **implicit feedback** (retries, abandonment — noisy) as production signals that are neither code nor judge.

  **Decision rule** (repeat until muscle memory) — Hamel FAQ, Langfuse error-analysis cookbook, Lenny’s Podcast (`BsWxPI9UM4c`), Aakash Gupta write-up:

  1. Can you **just fix** the bug in prompt/tools/code? **Do that first.**  
  2. Else, if a **deterministic rule** catches it → **code eval** (cheap, CI-friendly).  
  3. Else, if it needs **judgment** → **LLM judge**, then calibrate.  
  4. **Safety/compliance** may need an evaluator **as guardrail** even after fixing (in-request), not only as a monitor.

  Langfuse cookbook after taxonomy: **fix / evaluator / monitor**. Low-rate categories may only need monitoring. Do not build a judge for a 5% incomplete-resolution tail if nobody will iterate on it weekly.

  Hamel FAQ: **Should I build automated evaluators for every failure mode?** **No.** Cost hierarchy: assertions **cheap**; LLM-as-judge needs **100+ labels**, **weekly maintenance**, PM/eng/expert coordination. Automate failures you will **iterate on repeatedly**.

  Nova Escola lesson: they built an eval for “emit exactly one learning goal” when a **prompt change** deleted the double-goal bug — wasted meta-eval.

  **What code-based looks like:**

  - **Langfuse code evaluators:** Python or TypeScript `evaluate(ctx) -> scores`; run on live observations or experiments; **no network**; **stdlib only**; **≤2 seconds**. Examples: exact match, PII regex, numeric tolerance.  
  - **OpenAI Evals API:** `testing_criteria` lists graders; workhorse **`string_check`** (exact match / `contains`). Platform **deprecation**: read-only **2026-10-31**, shutdown **2026-11-30**; concepts of deterministic vs model graders **port**. OpenAI also points new users at **Datasets**. GitHub `openai/evals` remains a public registry.  
  - **Hamel Level 1:** pytest-like assertions; Rechat **hundreds** of checks (listing counts, no UUID leakage). Run on **every code change**.  
  - **Agent tool-call evals:** name, arguments, schema, policy order — **code**; semantic appropriateness of *which* tool — often **judge**.  
  - **RAG:** citation IDs ⊆ retrieved IDs, JSON shape, “must not claim X” substring — **code**; faithfulness / clarifying-question — **judge** (deterministic overlap is a **pre-filter**, not faithfulness).

  **What model-based looks like:** OpenAI **model graders** for style/content criteria strings cannot capture; give the grader room to reason; validate vs humans. Best practices: LLMs are better at **pairwise, classification, criteria scoring** than open-ended generation of a quality number. Langfuse: managed catalog **or** custom `{{variables}}`; stack a **cheap code pre-screen** in front of a judge to cut cost. Anthropic: robust production evals **combine** rule-based + LLM-powered + targeted human.

  **CI vs online:** **several code evals in CI**; **one or two** LLM evals in CI **maybe**; more often **weekly sampled online** judges (Lenny/Shreya). Flaky LLM judges in CI (nondeterminism, rate limits) are a real ops tax — Langfuse production judges are **async** with retry/`Delayed` on rate limits; that is **monitoring**, not a blocking unit test. Hybrid: **code prefilter → judge**.

* **The Alternatives:**  

  | Choice | Cost | Latency | Brittleness | Human correlation effort |
  |--------|------|---------|-------------|---------------------------|
  | **Code assert** | ≈0 | ms | High if format varies | Low (examples for edges) |
  | **LLM judge** | $$ (~$0.01–0.10/call, Langfuse) | seconds | Prompt-sensitive | High (100–200 labels) |
  | **Human** | $$$ | hours/days | Rater variance | N/A (is the reference) |
  | **Hybrid: code prefilter → judge** | Medium | Medium | Manageable | Medium |
  | **Fine-tuned classifier** | Cheap at serve | ms | Needs labels; drifts | High upfront |
  | **Ragas / library metrics** | Low–medium | seconds | Generic dimensions | Still calibrate if used as gates |

  | CI pattern | Pros | Cons | When it fits |
  |------------|------|------|--------------|
  | Code-only CI | Stable, fast | Blind to persona/faithfulness | Objective failures |
  | LLM judges on every PR | Dense | Cost, flake, rate limits | Rare; high-stakes only |
  | Code in CI + sampled online judges | Practical (Lenny/Shreya) | Online lag; statistical noise | Default for this syllabus |

  The syllabus selects **code first, judge second, human as truth** — several code evals in CI; LLM judges sparingly or sampled.

* **Failure Modes:**  
  - **Code-only** → blind to persona, tone, partial helpfulness, faithfulness nuance.  
  - **Judge-only** → expensive, flaky CI, meta-eval debt for failures `json.loads` would catch.  
  - **Neither** → flying blind.  
  - **Humans-only in production** → cannot scale (Nova Escola needed sampled automation *after* the rubric existed).  
  - Building an eval for a bug a prompt fix already deleted (Nova Escola double learning-goal).  
  - Automating every taxonomy cell including one-offs nobody will iterate weekly.

* **Average vs. Strong Engineer:**  
  **Average:** every failure mode gets an LLM judge; CI runs flaky model graders on every PR; or only JSON asserts and hope.  
  **Strong:** Level 1 assertions **every change**; Level 2 human/model on a cadence; Level 3 A/B rarely (Hamel). Code examples: valid JSON; required sections; tool name/args schema; PII regex; citation IDs ⊆ retrieved IDs; exact category labels (`string_check`). Judge examples: clarifying question; grounded in retrieved context; persona. Langfuse: observation-level targeting (evaluate only `GENERATION` named `final-response`); sampling rules; scores unify all methods in one dashboard. OpenAI: mix grader types; cookbook walks model grading + human validation.

* **Worked Example:**  
  Deployment Copilot Week 16 rates: `policy_order_skipped` and `markdown_in_sms` are objective enough for **code**. You add CI asserts: tool order (verify/preview before `commit_refund`); SMS channel output has no markdown markers; citation IDs ⊆ retrieved IDs; response parses as JSON when the API contract requires it. You do **not** build an LLM judge for “exactly one learning-goal–style” format bug you can prompt-fix. `should_have_clarified` stays a calibrated LLM judge. Online: several code evals in CI; the clarifying judge runs on a sampled schedule (async), not as a blocking unit test on every PR. A cheap citation-ID prefilter runs before any faithfulness judge to cut cost.

* **Apply It:**  
  1. For each Week 16 category, walk **fix → code eval → LLM judge → monitor-only**.  
  2. Put several deterministic asserts in CI on every change (JSON, schema, tool order, citation ⊆ retrieved).  
  3. Reserve LLM judges for residual judgment; calibrate before shipping.  
  4. Prefer sampled online judges over flaky LLM-in-CI on every PR.  
  5. Stack code prefilters in front of judges where possible.  
  6. Do not automate failure modes you will not iterate on weekly; do not meta-eval bugs a prompt already killed.

---

### Observability platforms (Langfuse, Arize Phoenix)

* **Fundamentals:**  
  **Observability** for LLM apps = understanding internal behavior from logged outputs (metrics, logs, **traces**). Langfuse FAQ: observability is the broader capability; **tracing** is the technique that records the **flow of a request** and preserves **causal** relationships. For LLM apps, tracing is the most important tool because it captures prompts, responses, tool calls, and their relationships. Week 15/16 assumed *some* structured traces existed for error analysis; this week turns that into a **product** dashboard the team can act on (and that judges can attach scores to).

  **Why LLM-specific platforms exist:** general APM (Datadog-only) has weak prompt/token/eval semantics. OpenTelemetry is generic by design; **OpenInference** adds AI span kinds and attributes on top of valid OTLP.

  **Core objects — learn both vocabularies:**

  | OTel / Phoenix | Langfuse |
  |----------------|----------|
  | Trace (root span; shares ID) | Langfuse **trace** = observations sharing `trace_id` + `session_id` / `user_id` |
  | Span | **Observation** (span, **generation**, event, tool, retrieval, …) |
  | — | **Generation**: specialized span for LLM calls: `model`, `model_parameters`, `usage_details` (tokens), `cost_details` |

  Hamel FAQ: vendors **define “trace” differently** — don’t assume the same I/O everywhere.

  Langfuse v4: overall input/output belong on the **root observation**; **trace-level I/O is deprecated**. Attribute propagation: `userId`, `sessionId`, `metadata`, `version`, `tags` via `propagate_attributes()`.

  **Phoenix / OpenInference span kinds:** `LLM`, `AGENT`, `CHAIN`, `TOOL`, `RETRIEVER`, `RERANKER`, `EMBEDDING`, `GUARDRAIL`, `EVALUATOR`, `PROMPT`. Span fields: name, start/end, `openinference.span.kind`, attributes, status `OK`/`ERROR`/`UNSET`. Spec motivation: structured multi-turn messages, token economics, agentic control flow, privacy masking, nondeterminism (enough context to explain a run), **quality feedback** (human / LLM / code scores).

  **Minimum viable tracing dashboard view:**

  ```
  Request ──► Trace (userId, sessionId, version, env)
                ├── RETRIEVER  (docs + scores) ──► attached onto generation I/O
                ├── TOOL
                └── GENERATION / LLM  (prompt, completion, tokens, cost, latency)
                          └── Score: faithfulness | should_clarify | json_ok
                                (human / code / calibrated judge)
  ```

  **Langfuse** (OSS, self-hostable): purpose-built loop **traces → scores (human/code/judge) → datasets/experiments → prompt management → custom dashboards & alerts**. Python SDK v4 / JS SDK v5 on **OpenTelemetry**; **async** export; errors caught so SDK “cannot break your application.” `start_as_current_observation(as_type="span"| "generation", ...)`. Customize with **`should_export_span` / `shouldExportSpan`** (filter OTEL noise). Judges: observation-level; compositional; evaluator executions are traces in env `langfuse-llm-as-a-judge`. Latency: SDK queues/batches; **does not add request latency** if used as documented.

  **Arize Phoenix** (OSS): traces via **OTEL**; first-class LlamaIndex, LangChain, OpenAI, DSPy, Bedrock, etc. Insights: application **latency** (slow LLM / retriever / other), **token usage** breakdown, **runtime exceptions**, **retrieved documents**, **embeddings**, **LLM parameters**, **prompt templates**, **tool descriptions** and **function calls**. Features: projects, sessions, annotations, metrics, **run evaluations** (LLM-as-judge on traces), embedding views. OpenInference best practices: hierarchy **sessions → traces → spans**; three capture modes — **auto-instrumentation**, **manual**, **hybrid** (wrap logical units, keep LLM child spans). Local `phoenix serve` UI `:6006` for the cookbook.

  **Instrumentation principles (both):** hierarchical traces with **inputs/outputs on each span**; tag `userId`, `sessionId`, `version`, `env`, feature flags; record **token usage and model name** on every generation/LLM span; **attach retrieved context** onto the generation being judged; sample or filter non-LLM OTEL spans; privacy/masking (OpenInference per-field masking). Annotation queues: **label the GENERATION** when trace I/O is null under OTEL (Week 16 Langfuse anti-pattern).

  Hamel FAQ: you do **not** need a dedicated AI observability product to *start* error analysis (JSON/CSV) — you **do** need structured traces before judges and cost dashboards scale.

* **The Alternatives:**  

  | Platform / approach | Pros | Cons | When it fits |
  |---------------------|------|------|--------------|
  | **Langfuse** | Strong eval+prompt+dataset loop; generations/cost native; OSS self-host | Must filter OTEL noise; v4 observation-first migration | Bottleneck is eval/experiment/prompt versioning |
  | **Phoenix** | OpenInference richness; embedding drift UX; OTEL-native; OSS | Drift automation vs exploration (community discussion 10442); less “prompt CMS” | Bottleneck is OpenInference traces, embeddings, retrieval inspection |
  | General APM (Datadog-only) | Already deployed | Weak prompt/token/eval semantics | Infra SLOs — not LLM quality |
  | Homegrown logs | Full control | No trace UI; reinvent scoring/datasets | Early error analysis only |
  | Closed SaaS-only | Managed | Data residency / lock-in | Regulated teams may prefer self-host OSS |
  | Auto vs manual vs hybrid instrumentation | Hybrid often best (OpenInference) | Auto alone may miss logical units | Prefer hybrid |

  The syllabus requires **literacy in both** Langfuse and Phoenix; pick **one primary** for the product and map concepts — don’t run three incomplete instrumentations.

* **Failure Modes:**  
  - Without tracing: cannot do error analysis on real **cascades** (RAG vs model vs tool); cost/latency is guesswork; judges lack context; flywheel has no production inlet; cannot debug **the judge**.  
  - Without LLM-specific semantics: spans named `HTTP POST` and no token/cost/model; cannot split “slow retriever” vs “slow 32k prompt.”  
  - Log final answer only; never set `sessionId`.  
  - Annotating empty OTel **traces** instead of **GENERATION** observations.  
  - Unfiltered OTEL noise explodes observation volume.  
  - Faithfulness judge without retrieved docs on the same observation.

* **Average vs. Strong Engineer:**  
  **Average:** log final answer only; maybe wrap OpenAI SDK once; never set `sessionId`; three half-wired vendors.  
  **Strong:** hierarchical traces; I/O on spans; propagate user/session/version; generations with usage + cost; retrieved context on the judged observation; `should_export_span` to drop framework spam; annotation queues on **GENERATION** when OTEL trace I/O is null; dual-write or pick **one primary**; self-host for regulated industries (both OSS); Langfuse HIPAA cloud exists as a managed option; instrument **judge** and **app** the same way. Choose Langfuse if the bottleneck is **eval/experiment/prompt versioning**; choose Phoenix if the bottleneck is **OpenInference-shaped traces, embeddings, and retrieval inspection**.

* **Worked Example:**  
  Deployment Copilot instruments hierarchical traces in Langfuse (primary) with OpenInference-aware literacy for Phoenix comparison. Each request is a trace tagged `userId`, `sessionId`, `version`, `env`. A `RETRIEVER` span records docs + scores; those docs are **copied onto** the final `GENERATION` observation so an observation-level faithfulness / `missing_runbook_lookup` judge can see them. Generations carry `model`, params, `usage_details`, `cost_details`. `should_export_span` drops noisy framework HTTP spans. Judge runs appear as traces filtered by `environment=langfuse-llm-as-a-judge` (Completed / Error / Delayed / Pending). Annotation queues target the GENERATION when OTEL root I/O is null. The interview artifact screenshot shows one generation with tokens/cost and a boolean score attached.

* **Apply It:**  
  1. Instrument hierarchical traces (Langfuse and/or Phoenix) with I/O on each span.  
  2. Ensure every generation/LLM span records model, tokens, and cost.  
  3. Attach retrieved context onto the observation you will judge.  
  4. Propagate `userId` / `sessionId` / `version` / `env`; filter OTEL noise with `should_export_span`.  
  5. Annotate GENERATION observations when trace-level I/O is null.  
  6. Pick one primary platform; keep literacy in both; instrument judge executions the same way as the app.

---

### Production monitoring dashboards (cost, latency, errors, quality, drift)

* **Fundamentals:**  
  Production monitoring for LLM apps sits **on top of traces**. Infra-green (HTTP 200, CPU OK) is **not** product-healthy. Langfuse Academy framing: use traces to monitor; custom dashboards for **cost, latency, volume, quality**; **alerts** when metrics cross thresholds. The Week 16 flywheel’s production sample is the inlet; this week’s calibrated scores and dashboards are how the team *sees* and *triages* what that sample finds.

  **Signals that belong on the first dashboard:**

  | Signal | What it catches | Notes |
  |--------|-----------------|-------|
  | **Latency** (p50/p95/p99, **per-span**) | Slow tools, model, retrieval | Phoenix: component-level latency; Langfuse dashboards |
  | **Cost / tokens** | Prompt bloat, wrong model, agent loops | Needs pricing table + usage on **generations** |
  | **Error rate** | API failures, tool exceptions, rate limits | Span status `ERROR`; Phoenix runtime exceptions |
  | **Quality scores** | Judge/human/code scores over time | **Sampled** online evals; alert on threshold **after** calibration |
  | **Volume** | Traffic spikes, abuse | Per user/session/feature/version |
  | **Drift** | Input/embedding/behavior shift while accuracy looks flat | Phoenix embedding drift / clustering; quality-score drift; **taxonomy rate** shifts (Week 16 flywheel) |

  Online judges run **after the response ships**. They are **monitors**. A check that must **block** an unfaithful answer is a **guardrail** in the request path (Langfuse faithfulness).

  | | **Guardrail** | **Monitor / online eval** |
  |--|---------------|---------------------------|
  | When | In the request path, **before** the user sees output | **After** response ships (async) |
  | Purpose | Block policy/safety/unfaithful answers | Trends, triage, dataset refill |
  | Failure mode if confused | User-facing latency + judge flake as outages | Thinking a dashboard “blocks” bad answers |

  **Sampling** (you will not judge 100% of tokens):

  | Source | Practice |
  |--------|----------|
  | **Nova Escola** | Daily eval suite on **~2%** of production traffic |
  | **Langfuse faithfulness** | **5–10%** of matching observations often enough for a trend |
  | **Langfuse cost FAQ** | ~$0.01–0.10 per judge call; sampling + observation targeting + cheaper models |
  | **Hamel review sampling** | Keep **random** traces in every human batch; target outliers (long, retries) |

  Need enough volume for the quality timeseries to be more than noise; rare failures need **targeted** sampling (known input patterns), not only 2% random.

  **Dashboards to ship early:**

  1. **Requests, error %, p95 latency** by route / **version** / env.  
  2. **Cost** per day / per successful task / **by model** (generation `cost_details`).  
  3. **Score timeseries** for top **1–3 calibrated** failure modes (sampled boolean Pass rate).  
  4. **Annotation queue depth** / human review SLA.  
  5. Optional RAG: **embedding distance** to corpus centroid / cluster view (Phoenix).  
  6. **Judge health:** judge error/Delayed rate, judge token cost (Langfuse judge traces).

  **Alerting:** budget burn, p95 latency, error spikes, **sudden drop in Pass rate or faithfulness** — then **open traces**, don’t just page on the number. Version tags prevent mixing v1 and v2 quality on one line.

  **Drift kinds:**

  | Kind | Example | Tooling |
  |------|---------|---------|
  | **Quality-score drift** | Calibrated faithfulness mean drops | Langfuse score dashboards + alerts |
  | **Taxonomy-rate drift** | Week 16 `missing_device_lookup` rate up | Relabel sample; don’t trust judge until recalibrated |
  | **Embedding / retrieval drift** | Corpus moved; latency/accuracy look fine | Phoenix embedding views; discussion 10442 |
  | **Criteria drift** | Expert would now Fail yesterday’s Pass | Shankar et al.; human audits |
  | **Traffic mix drift** | New user cohort, new doc types | Stratify dashboards by tag |

  OpenAI: continuous evaluation on every change; monitor **nondeterminism**; **grow the set**. Offline experiments catch known regressions; online catches **unknowns** that refill Week 16 flywheel.

  Hamel ops: **weekly sample of traces** + periodic judge runs; don’t rely on generic scores alone — pair with **error-analysis revisits** when distributions shift. Between full cycles: **10–20 weekly** outlier traces; full **100+** every **2–4 weeks**.

* **The Alternatives:**  

  | Monitoring style | Pros | Cons | When it fits |
  |------------------|------|------|--------------|
  | Infra-only (CPU/5xx) | Familiar SRE | Misses silent quality failure | Never alone for LLM products |
  | Cost+latency only | Controls spend/SLO | Quality can rot unnoticed | Incomplete |
  | 100% online LLM judges | Dense quality signal | Expensive; needs calibration; still not a guardrail | Avoid |
  | Sampled judges (2–10%) + human queues | Practical | Statistical noise; need volume | Default for this syllabus |
  | Embedding drift dashboards | Early RAG warning | May miss behavioral collapse with stable embeddings | Complement quality scores |
  | Business KPIs only | Executive-friendly | Slow/ambiguous attribution | After product-level changes |
  | Quality SLOs (Pass rate) | Product-honest | Nondeterministic; needs calibrated judge + sample size | After TPR/TNR gate |

  The syllabus selects **cost + latency + errors + 1–3 calibrated quality timeseries + drift awareness**, with **sampled** online judges and alerts that deep-link to traces.

* **Failure Modes:**  
  - Cost regressions (agent loops) burn budget silently.  
  - Latency SLOs break without **span attribution**.  
  - Quality drifts after prompt/model/corpus changes with **green CI**.  
  - No queue of bad traces to feed the Week 16 flywheel.  
  - Uncalibrated quality alerts page the team into ignoring evals (Field Guide trust collapse).  
  - Collapsing guardrails and monitors — judge flake becomes user-facing outages, or dashboards are mistaken for blockers.  
  - Mixing v1 and v2 quality on one untagged timeseries.  
  - Judging 100% of traffic through GPT-4 judges.

* **Average vs. Strong Engineer:**  
  **Average:** Cloudwatch 5xx + a single “helpfulness” sparkline.  
  **Strong:** ship the dashboard tiles above in week one of production; alerts **deep-link to traces** filtered by version; sampled calibrated scores; human queues for disagreements and tails; recalibrate judges when the timeseries jumps after a **model** change (could be judge or app); separate **experiment** comparison (offline dataset run) from **online** monitoring; Nova Escola: daily 2% as a **product** habit; Langfuse: scores on observations; Phoenix: inspect exceptions and retrieved docs when quality drops; Hamel: 10–20 weekly outliers between full error-analysis cycles. **Cost attribution:** tag traces by feature/tenant; sum `cost_details` — Week 20 goes deeper on routing/cache; this week you **must at least see** spend.

* **Worked Example:**  
  Deployment Copilot’s first production dashboard has six tiles: requests/error%/p95 by version; cost/day and cost/successful-task by model from generation `cost_details`; sampled Pass-rate timeseries for calibrated `should_have_clarified` and claim-aggregated faithfulness (5–10% of matching observations; Nova Escola–style ~2% daily suite as the habit); annotation queue depth; judge health (Delayed/Error rate and judge token cost); optional Phoenix embedding distance for runbook corpus drift. An alert on faithfulness Pass-rate drop opens traces filtered by `version=copilot-v2`, not a bare page. Blocking policy checks (unsafe tool order) stay **in-request** guardrails; async judges never block the user. Disagreements and low scores refill the Week 16 flywheel annotation queue.

* **Apply It:**  
  1. Ship dashboards for volume, errors, p95 latency, cost, and **1–3 calibrated** quality timeseries.  
  2. Sample online judges (start from Nova Escola ~2% / Langfuse faithfulness 5–10%); keep random + outlier human review.  
  3. Separate **guardrails** (in-request) from **monitors** (async after response).  
  4. Alerts deep-link to version-filtered traces; include judge-health and annotation-queue depth.  
  5. Watch quality-score, taxonomy-rate, embedding, criteria, and traffic-mix drift; recalibrate when models or criteria move.  
  6. Tag cost by feature/tenant; do not claim Week 20 routing/cache work — just **see** spend.

---

## Week 17 build checklist (end-to-end)

Use this as the chapter’s capstone sequence; every concept above maps here.

1. **Design judges:** One binary judge per high-impact Week 16 judgment-heavy failure mode; Pass/Fail + critique; principal domain expert owns the standard.  
2. **Calibrate:** Split labels (~10–20% / ~40–45% / ~40–45%); gate on **TPR and TNR**; do not ship a weak judge; recalibrate on model/criteria change.  
3. **Code vs model:** Prefer code evals for objective failures in CI; reserve LLM judges for residual judgment; sample online.  
4. **Tracing dashboard:** Hierarchical traces (Langfuse and/or Phoenix); generations with tokens/cost; retrieved context on the judged observation; tag user/session/version/env.  
5. **Production monitoring:** Cost, latency, errors, 1–3 calibrated quality timeseries, drift; alerts open traces; sample 2–10%; guardrails ≠ monitors.  
6. **Interview artifact:** One calibrated binary judge with TPR/TNR on held-out Week 16 set + tracing dashboard showing generation tokens/cost + score + one code eval that replaced a would-be judge.

When those steps are true, Week 17 is done in the syllabus sense: residual subjective failures have a trustworthy shadow, objective failures stay cheap in CI, and traces are a product the team can act on — not a vanity UI. The Week 16 flywheel does not stop: disagreements and low scores keep refilling annotation queues.

---

## Looking ahead

Week 18 opens **Phase 5 — Production Engineering** with **deployment infrastructure**: containerize the service for production (multi-stage builds, non-root, env/secrets, health/ready endpoints); build **Kubernetes fluency** (Pods, Services, Deployments, HPA — including when CPU is the wrong autoscaling signal); take **CI/CD beyond push-to-deploy** (staged `dev` → `staging` → `prod`, golden-set smoke, rehearsed rollback / canary); sketch **Infrastructure as Code with Terraform** (VPC/cluster-or-Cloud-Run, IAM skeleton, remote state with locking, separate state for staging vs prod). Do **not** start Week 18 by throwing away this week’s judges and dashboards — you put the **same** instrumented service on a real delivery path. Week 20 goes deeper on cost routing and semantic cache; this week you only need to **see** spend on generations.

---

## Compilation notes

- All concept sections above are grounded in `research/phase-4/week-17-llm-judge-observability/` (`00`–`05`, README).  
- One `[NEEDS MORE RESEARCH]` appears under calibration alternatives (Bayesian prevalence adjustment defaults for Deployment Copilot) — research notes flag the technique as rarely implemented without prescribing product defaults.  
- Research Open Questions (multi-dimensional scores for exec reporting, residual self-enhancement bias on scoped binary tasks, G-Eval n-sample vs single structured label in production, standardized trace semantics across vendors, quality SLOs vs latency SLOs, OpenAI Evals platform shutdown vs portable grader homes, sample size for statistically real Pass-rate drops at 2% traffic sampling, judge cost as a first-class budget line) remain open and were **not** resolved with invented answers.  
- Outside URLs from research are cited inline; operational detail was inlined from the notes.  
- Week 18 deployment / infra (containers, K8s, CI/CD, Terraform) is explicitly deferred. Week 20 full cost-engineering (routing, semantic cache) is explicitly deferred beyond “see spend on generations.”
