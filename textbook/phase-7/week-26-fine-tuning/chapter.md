# Chapter 26 — Fine-tuning when RAG isn't enough

> **Phase 7 — Supplementary Electives**  
> **Compilation status:** COMPLETE  
> **Source of truth:** `research/phase-7/week-26-fine-tuning/`  
> **Syllabus Build:** Write a **decision memo only** — **not** a toy LoRA training run. Argue RAG vs fine-tuning for one concrete product scenario and include: (1) **criteria** — map the product to the Week 26 decision framework (behavior/style/format vs fresh/citeable facts; latency; air-gap; iteration velocity; data availability); (2) **risks** — contamination, catastrophic forgetting, ops burden when base models update, stale knowledge in weights, eval gaps vs Week 10 RAGAS; (3) **kill criteria** — explicit conditions under which you abandon FT (or abandon RAG-only) and switch strategy.

---

## Chapter framing

Week 26 treats **fine-tuning (FT)** as a deliberate escalation after Phase 2 RAG and Week 5 prompting — not as the default “make the model smarter” move. RAG changes **what facts** land in the window at inference. Fine-tuning changes **weights** so the model’s default **behavior**, **format**, **domain phrasing**, or **fixed skill** shifts without stuffing that behavior into every prompt.

OpenAI’s product guidance and Chip Huyen’s production writing converge: fine-tuning is strongest for **style, format, and instruction-following reliability**; retrieval is stronger for **current or proprietary facts** you must cite or update without a training run (*Building LLM applications for production*; OpenAI fine-tuning guide).

| Lever | What moves | Cadence of change | Typical week |
|-------|------------|-------------------|--------------|
| Prompt engineering | Instructions in the request | Git commit | Week 5 |
| RAG / context packing | Evidence tokens at inference | Index update | Weeks 6–10, 25 |
| **Fine-tuning / PEFT** | Adapter or full weights | Training job + eval gate | **Week 26 (this elective)** |

This elective is **supplementary** — it does not replace Weeks 1–24 or Phase 2 RAG. Suggested slot: after Week 10 (RAG eval) so you can prove RAG plateaued, and after Week 20 so you can price FT vs prompt length and retrieval latency — or append after the Week 24 capstone.

The **build** is a written **decision memo** with criteria, risks, and kill criteria — not a Colab that trains once. Flagship systems often fine-tune *after* RAG and prompts plateau; this week forces the **decision** to be written and defensible before GPU spend.

Read the concepts in order. Each section’s **Worked Example** and **Apply It** assume the same flagship service (working title: Deployment Copilot) facing a go/no-go on PEFT for one product surface.

**Default path (synthesis):**

1. Exhaust prompt + RAG (Phase 2) and measure with Week 10 metrics before proposing FT.  
2. Classify the residual failure: **behavior/format** → FT candidate; **missing/stale facts** → stay on RAG; **both** → hybrid (FT for form, RAG for facts).  
3. If FT: prefer PEFT (LoRA/QLoRA); budget labeling for quality over volume; freeze a task golden set + forgetting suite.  
4. Price training + hosting + retrain cadence against Week 20 cost/latency of longer prompts / retrieval.  
5. Ship the **decision memo** with kill criteria; only then consider a later lab for actual adapters.

---

### RAG vs fine-tuning decision framework

* **Fundamentals:**  
  **RAG** retrieves evidence at inference and packs it into context (Phase 2). **Fine-tuning** updates model parameters (often a small adapter) so desired behavior is internalized. They answer different residual failures after prompting:

  | Residual failure after prompting | First lever | Why |
  |----------------------------------|-------------|-----|
  | Model doesn’t *know* / cites wrong / needs fresh docs | **RAG** | Facts stay outside weights; index updates without retrain |
  | Model *knows enough* but format/tone/schema is unreliable | **Fine-tune** | Behavior baked in; shorter prompts; fewer few-shots |
  | Strict latency on a **fixed skill** (classify, extract, rewrite) | **FT (often small model)** | Skip retrieval hop and long instructions |
  | **Air-gap / offline** with stable skill, no live corpus API | **FT (or local RAG with shipped index)** | Weights travel; cloud retrieval may be forbidden |
  | Knowledge changes weekly + must be **citeable** | **RAG** | Weights freeze; citations need passages |

  OpenAI’s fine-tuning guidance and Chip Huyen’s *Building LLM applications for production* both separate **behavior** (finetune / shorter prompts) from **knowledge access** (retrieval / tools). Huyen also warns against insisting on finetuning when prompting still works (*Common pitfalls*, 2025).

  **When FT wins (syllabus):**

  1. **Style / format / domain language** — house voice, ICD coding phrasing, strict JSON/XML schemas that few-shots can’t stabilize at volume.  
  2. **Latency for fixed skills** — high-QPS extraction or routing where retrieval + long context blow p95.  
  3. **Offline / air-gap constraints** — regulated edge boxes that cannot call a vector service every request.

  **When RAG wins:**

  1. **Fresh facts** — prices, policies, tickets, runbooks that churn.  
  2. **Citeable knowledge** — auditors want passage IDs (Week 10 groundedness).  
  3. **Cheaper iteration** — re-index and prompt-diff beat dataset + train + eval + deploy cycles.

  Hybrid is common: LoRA for form, RAG for facts (same product, two levers). Baking docs into weights **looks** like learning but creates silent staleness — the kill criterion for most knowledge-FT proposals.

* **The Alternatives:**  

  | Strategy | Upside | Downside |
  |----------|--------|----------|
  | Prompt-only | Fastest loop | Token cost; brittle long instructions |
  | RAG-only | Fresh + citeable | Latency; packing failures (Week 9); won’t fix style alone |
  | Full FT | Max task fit (sometimes) | Cost, forgetting, hosting, retrain tax |
  | **PEFT (LoRA/QLoRA)** | Small artifact; multi-adapter | Still needs data + eval; merge/serve complexity |
  | Distillation to small specialist | Cheap inference | Narrow; separate model ops |
  | Longer context instead of RAG/FT | Simpler architecture | Cost, rot (Week 25); not a style teacher |

  | Decision input | Prefer RAG if… | Prefer FT if… |
  |----------------|-----------------|---------------|
  | Change rate of “truth” | Daily/weekly | Stable for months |
  | Need citations | Yes | No / rare |
  | Format SLO | Soft | Hard (schema, voice) |
  | Iteration budget | Eng-heavy, ML-light | Labeled set exists |
  | Deployment | Online retrieval OK | Air-gap / no retrieval budget |

  The syllabus selects **exhaust prompt + RAG, then classify residual failure** before PEFT notebooks or GPU spend. Managed paths (OpenAI fine-tuning jobs; Amazon Bedrock `CreateModelCustomizationJob`) and open-weight PEFT are implementation choices *after* the framework says FT is warranted.

* **Failure Modes:**  
  - Customer mandate “fine-tune our Llama on SharePoint” when Week 6–8 ingestion/retrieval would move the needle — knowledge freezes at train time and goes stale.  
  - Cost reviews (Week 20) never compare **$/1k calls with 2k-token exemplars** vs **amortized train + short prompts**.  
  - Security/compliance asks for citations; FT-only answers cannot show passages.  
  - Air-gapped teams over-index on RAG patterns copied from SaaS blogs that assume network.  
  - Binary slogans (“RAG is dead” / “always fine-tune”) driven by vendor demos replace a failure taxonomy.  
  - Interviews cannot explain *why* small tuned models can beat frontier models on **narrow** tasks while losing on open-domain factuality.

* **Average vs. Strong Engineer:**  
  **Average:** jump to full FT first for the “we customized the model” narrative; or refuse FT forever while burning tokens on 4k-token format exemplars every call.  
  **Strong:** failure taxonomy → lever map; A/B prompt+RAG vs FT candidate on the **same golden set**; hybrid when both behavior and knowledge fail; document kill criteria in the design memo. Force the customer to state whether success is measured by **groundedness/citation** (Week 10) or **format accuracy/latency**; refuse FT-as-knowledge-base; cite OpenAI/Bedrock “customize for task” docs and Huyen’s prompting-vs-finetuning cost arithmetic.

* **Worked Example:**  
  Deployment Copilot support surface needs (1) answers grounded in **changing** runbooks and help-center articles with URLs in the reply, and (2) a **fixed** apology + escalation JSON schema in the brand voice. OpenAI’s fine-tuning guide frames FT for reliable format/tone after prompting plateaus.

  Decision in the memo: **RAG wins** for article truth and citations (Phase 2 + Week 10 faithfulness). **FT/PEFT wins** only for the schema/voice head if few-shots still fail format accuracy at volume — not for storing the help center. Kill FT if a 500-example style set doesn’t beat prompt+RAG on format@schema while RAGAS faithfulness drops on the factual slice.

* **Apply It:**  
  1. List residual failures after prompt + RAG on a named Deployment Copilot surface.  
  2. Classify each as behavior/format, knowledge/freshness/citeability, latency, or air-gap.  
  3. Fill the decision-input table (change rate, citations, format SLO, iteration budget, deployment).  
  4. State whether hybrid (LoRA for form + RAG for facts) is required.  
  5. Write kill criteria for both “abandon FT” and “abandon RAG-only.”  
  6. Do not open a training notebook until the memo is reviewed.

---

### LoRA / QLoRA / PEFT overview

* **Fundamentals:**  
  **Full fine-tuning** updates (almost) all parameters — storage, optimizer state, and multi-tenant serving cost explode at LLM scale. **PEFT** (Parameter-Efficient Fine-Tuning) trains a **small** set of task parameters while freezing the base.

  **LoRA** (Hu et al., 2021, arXiv:2106.09685): for a frozen weight \(W\), learn low-rank factors \(A, B\) so the effective update is \(\Delta W = BA\) (rank \(r \ll d\)). Only \(A, B\) (and optionally biases) train. At inference, adapters can be **merged** into \(W\) (no extra latency) or kept separate for **multi-adapter** serving.

  Key knobs (Hugging Face PEFT `LoraConfig`):

  | Knob | Meaning |
  |------|---------|
  | `r` (rank) | Capacity of the update; lower → fewer params, less expressivity |
  | `lora_alpha` | Scaling; effective scale often \(\alpha / r\) (or RSLoRA \(\alpha / \sqrt{r}\)) |
  | `target_modules` | Which projections get adapters (e.g. `q_proj`, `v_proj`, MLP gates) |
  | `lora_dropout` / `bias` | Regularization and whether biases train |

  **QLoRA** (Dettmers et al., 2023, arXiv:2305.14314): keep the **base in 4-bit** (NF4 + double quantization + paged optimizers) and still train LoRA adapters in higher precision. Goal: finetune very large models on a **single** high-memory GPU with task quality close to 16-bit LoRA.

  **What you actually change:** not “the whole LLM personality dump,” but a thin **adapter artifact** (MBs–low GBs) conditioned on your dataset. Base capabilities remain mostly those of the frozen model — which is why catastrophic forgetting and eval still matter, and why FT does not replace RAG for fresh facts.

  Tooling stack (legal / official): **PEFT** for adapters; **TRL** (`SFTTrainer`, DPO trainers) for training loops; **Unsloth** for faster / lower-VRAM LoRA–QLoRA compatible with TRL.

  **Mental model for FDEs:** the base model is a shared library; each product skill is a patch. You version the patch (`adapter_config.json` + weights), pin the library (`base_model_revision`), and evaluate the composition. Merging is optional packaging for edge/air-gap — not the same as “we permanently rewrote the foundation model.”

* **The Alternatives:**  

  | Method | Trainable footprint | Pros | Cons |
  |--------|---------------------|------|------|
  | Full FT | ~all weights | Max flexibility | Cost; multi-copy serving; forgetting risk |
  | LoRA (fp16/bf16 base) | Rank-\(r\) mats | Strong quality; mergeable; multi-adapter | Needs VRAM for base in higher precision |
  | **QLoRA** | LoRA + 4-bit base | Consumer / single-GPU large models | Dequant overhead; quant edge cases |
  | Prefix / prompt tuning | Tiny | Very small | Often weaker than LoRA on generative tasks |
  | Vendor managed FT (OpenAI / Bedrock) | Opaque internals | Ops simplicity | Less control; pricing; export limits |

  | Rank / targets | When |
  |----------------|------|
  | Small `r` (4–16), attention only | First pass; style/format |
  | Higher `r`, attention + MLP | Harder domain skills after plateau |
  | Many adapters, one base | Multi-tenant / multi-task serving |

  Tradeoff: merging adapters simplifies latency but loses hot-swap; hot-swap (PEFT) simplifies ops for many tasks but needs careful rank/`target_modules` compatibility. Compared to prompt/prefix tuning, LoRA-merge workflows have fewer moving parts at inference and generally stronger generative quality in modern practice — which is why this elective standardizes on LoRA/QLoRA rather than every PEFT variant.

* **Failure Modes:**  
  - Teams equate “fine-tune” with full 70B copies per customer — deal dies on cost.  
  - QLoRA without understanding **frozen 4-bit base + small trainable adapters** → confusion when Hub uploads are tiny (adapters only) or why eval still needs the base weights.  
  - Rank treated as magic (`r=256` “to be safe”) → overfitting and wasted VRAM.  
  - Endless LoRA rank sweeps after the product needed better labeling guidelines, not more `r`.  
  - FDEs cannot explain air-gap delivery: ship **base + adapter** (or merged GGUF) vs shipping a RAG service.  
  - Week 20 cost talks ignore that PEFT training ≠ PEFT inference hosting.

* **Average vs. Strong Engineer:**  
  **Average:** copy a Colab; train until loss ↓; merge; no adapter registry; one-off Unsloth run undocumented.  
  **Strong:** PEFT config in Git (`r`, alpha, targets, base revision); TRL/Unsloth job configs versioned; adapters stored as artifacts next to dataset hash; optional merge for edge. Quote LoRA’s frozen-\(W\) + low-rank \(\Delta W\); know QLoRA’s NF4 motivation; compare managed OpenAI/Bedrock FT vs self-host PEFT for the customer’s data-residency story.

* **Worked Example:**  
  An FDE delivering an on-prem Deployment Copilot summarizer for incident-note *formatting* (not living policy facts) freezes Llama-class weights, attaches LoRA to attention projections with `r=16`, trains with TRL `SFTTrainer`, and ships adapter weights plus pinned base revision. If VRAM is tight on the training box, switch to QLoRA without changing the product decision — still PEFT, still not a substitute for retrieving the customer’s living runbook PDFs. Hugging Face PEFT LoRA conceptual guide and TRL ↔ Unsloth integration document this shape.

* **Apply It:**  
  1. In the memo, name PEFT (not full FT) as the default implementation shape if FT is warranted.  
  2. Record intended `r`, `lora_alpha`, `target_modules`, and `base_model_revision` as placeholders to pin later.  
  3. Choose merge vs multi-adapter based on latency vs hot-swap needs (edge/air-gap vs multi-skill serving).  
  4. Note QLoRA only as a training-VRAM tactic — not a different product decision.  
  5. Compare managed vendor FT vs self-host PEFT against data-residency constraints.  
  6. Refuse rank sweeps until dataset and eval gates exist (next two concepts).

---

### Dataset construction for fine-tuning

* **Fundamentals:**  
  Fine-tuning quality is mostly **data quality**. PEFT only decides *how* gradients land; the dataset decides *what* behavior is reinforced.

  **Instruction data (SFT):** triples or chat turns of `{system?, user, assistant}` demonstrating the desired skill — format, tone, tool-call shape, rewrite style. OpenAI and Bedrock fine-tuning flows expect JSONL chat/example records; open-source TRL `SFTTrainer` consumes analogous conversational or text fields.

  **Preference data:** pairs (or ranked lists) of completions for the same prompt — chosen vs rejected — for DPO / RLHF-class trainers in TRL. Higher labeling skill and cost; use when SFT stabilizes format but **relative** quality (helpfulness, safety tone) still drifts.

  **Quality > quantity:** QLoRA’s public results and broader instruction-tuning practice show small, clean sets beating large noisy scrapes. Chip Huyen notes that annotation guidelines used for human eval can later become finetuning data (*Common pitfalls*) — the guideline *is* the product spec.

  | Risk | What it means |
  |------|----------------|
  | **Contamination** | Train examples overlap eval/golden sets or leak benchmark items → fake gains |
  | **Label noise** | Inconsistent schemas/voices teach variance |
  | **Proxy mismatch** | Slack dumps ≠ production prompts |
  | **License / PII** | Training on data you cannot legally or safely encode into weights |
  | **Labeling cost** | Expert hours dominate GPU cost (Week 20 framing) |

  Rule of thumb for FDE memos: budget **curation and review** as a first-class line item; treat “we’ll scrape Confluence” as a smell unless filtered into instruction-shaped gold.

  **Instruction vs preference (quick chooser):** if failures are “wrong shape / wrong house voice,” start with SFT. If failures are “both answers are on-format but humans prefer A,” invest in preference pairs. Mixing both without a guide produces contradictory gradients.

* **The Alternatives:**  

  | Data strategy | Upside | Downside |
  |---------------|--------|----------|
  | Scrape everything | Volume | Noise, PII, contamination, weak skill signal |
  | **Hand-authored gold (100s–low 1000s)** | High signal | Slow; needs SMEs |
  | Synthetic from frontier model | Scale | Homogenization; teacher biases; still needs human audit |
  | Production logs → filtered | Real distribution | Consent, PII, sparse “good” labels |
  | Preference pairs | Better ranking behavior | 2–5× labeling cost vs SFT |
  | Mix SFT + prefs | Strong stacks | Two pipelines to maintain |

  | Contamination control | Practice |
  |----------------------|----------|
  | Hash / near-dup vs golden set | Block train∩eval |
  | Hold out by time or account | Avoid leakage from prod traces |
  | Document source tiers | SME gold vs synthetic vs logs |

  Tradeoff: synthetic expansion without a **style guide** amplifies the teacher’s generic voice — defeating “domain language” FT goals from the decision framework.

* **Failure Modes:**  
  - Beautiful LoRA loss curves that fail the product golden set.  
  - “FT improved MMLU” via contamination while customer schema accuracy flatlines.  
  - Legal holds when customer PII is baked into adapters shared across environments.  
  - Preference training on uncalibrated pairwise labels → reward hacking / sycophancy.  
  - Endless GPU sweeps that were actually **labeling** problems (Huyen: start too complex / insist on finetuning when prompting works — often because data wasn’t ready either).  
  - Hybrid FT examples that memorize citeable facts that should stay in RAG.

* **Average vs. Strong Engineer:**  
  **Average:** JSONL of random good/bad tickets; no guidelines; eval = “ask the model in chat.”  
  **Strong:** written annotation guide; inter-annotator agreement spot checks; train/val/golden splits with contamination scans; separate slices for format, safety, and (if hybrid) RAG-grounded answers that must **not** be memorized as facts. Estimate labeling hours in the decision memo; refuse FT until N reviewed examples exist; cite vendor data prep docs (Bedrock prepare data; OpenAI training format); plan preference data only if SFT plateaus.

* **Worked Example:**  
  A bank wants Deployment Copilot “regulator-ready” letter rewrites in a fixed template. The FDE rejects dumping 50k CRM emails. Instead: 800 SME-reviewed instruction examples following a one-page style guide, 200 validation, 150 sealed golden (never trained on), plus a contamination check against the golden strings. Preference pairs (tone too aggressive vs approved) added only after SFT format@template exceeds the kill threshold. Facts about rate changes stay in RAG — not in the JSONL — so letters don’t memorize yesterday’s APR. Bedrock custom-model fine-tuning docs treat data prep as the gate before `CreateModelCustomizationJob`; OpenAI expects chat-format training files with a clear validation split.

* **Apply It:**  
  1. Write a one-page annotation / style guide before collecting examples.  
  2. Budget SME review hours as a memo line item (often > GPU).  
  3. Plan train / val / sealed golden splits; schedule a contamination scan.  
  4. Start with SFT; add preference pairs only if relative quality still drifts.  
  5. Keep citeable / churning facts out of the JSONL — route them to RAG.  
  6. Refuse FT until a minimum reviewed N exists; cite vendor JSONL format requirements.

---

### Eval for fine-tunes vs RAGAS

* **Fundamentals:**  
  **Week 10 RAGAS-style metrics** (faithfulness / groundedness, answer relevance, context precision/recall) evaluate whether a **retrieval+generation** stack uses evidence well. They are the wrong primary scoreboard for a fine-tune whose job is **behavior**: schema validity, tone, classification F1, tool-call shape, or latency-bound rewrite quality.

  **Fine-tune eval** centers on:

  1. **Task-specific golden sets** — sealed examples with expected structures or labels. Score format compliance, exact/soft match, constrained JSON validity, rubric grades (Week 17 LLM-judge only if calibrated).  
  2. **Regression vs base** — same prompts on base instruct model vs adapter; require non-regression on general skills you still need.  
  3. **Catastrophic forgetting checks** — holdout suites for safety refusals, core reasoning, or other product skills that must survive PEFT.  
  4. **Hybrid split** — if RAG remains for facts, keep **RAGAS on the RAG path** and **task metrics on the FT path**; don’t average them into one vanity number.

  | Question | Metric family |
  |----------|---------------|
  | Did retrieval get the right docs? | P@k, R@k, MRR, NDCG (Week 10) |
  | Did the answer stick to context? | RAGAS faithfulness / groundedness |
  | Did FT learn the template/voice? | Schema pass rate, rubric, pairwise win rate |
  | Did FT break the base model? | Forgetting suite delta vs base checkpoint |
  | Is the system shippable? | Gate: task metric ↑ AND forgetting within budget AND (if RAG) faithfulness ≥ floor |

  Training loss and vendor “validation loss” are **not** product acceptance.

  **Attribution rule (ties to Week 16):** when a hybrid system fails, slice first — retrieval miss (Week 9/10) vs generator format miss (FT/prompt) vs packing/context failure (Week 25). Only then decide whether to collect more instruction data, raise LoRA rank, or fix the index.

* **The Alternatives:**  

  | Eval approach | Pros | Cons |
  |---------------|------|------|
  | Vibes / chat demo | Fast | Non-reproducible; ships regressions |
  | RAGAS only | Great for Phase 2 | Misses format FT gains; punishes non-RAG answers |
  | **Task golden + forgetting suite** | Matches FT intent | Needs SME labels; maintenance |
  | LLM-as-judge only | Scales | Judge bias (Huyen pitfalls; Week 17) |
  | Online A/B | Real utility | Slow; needs guardrails first |
  | Benchmarks (MMLU etc.) | Comparable | Contamination risk; weak product link |

  | Gate design | Tradeoff |
  |-------------|----------|
  | Strict schema 99% | May reject useful paraphrases |
  | Soft rubric | Needs IAA / judge calibration |
  | Combined hybrid gates | More honest; more CI cost |

  Tradeoff: optimizing only task golden sets can destroy helpful base behaviors — hence forgetting checks as a **first-class** gate, not a nice-to-have. Practical CI shape: one workflow for **adapter candidates** (task + forgetting), one for **index/prompt candidates** (RAGAS + IR@k). Sharing a single flaky notebook for both is how regressions slip.

* **Failure Modes:**  
  - Teams declare victory because RAGAS faithfulness rose after they stuffed more docs into prompts — while the LoRA never helped.  
  - Or they ship an adapter that nails JSON but starts leaking PII / weakening refusals.  
  - Week 16 error analysis attributes failures to “model quality” without slicing **retrieval vs behavior**.  
  - Decision memos lack kill criteria (“kill FT if format@golden < X or forgetting delta > Y”).  
  - Vendor FT jobs look “green” on loss while product schema tests fail.  
  - Evals stay RAGAS-only (Week 10) while FT regressions and catastrophic forgetting go unmeasured.

* **Average vs. Strong Engineer:**  
  **Average:** one Excel of 20 prompts; before/after screenshots; no base regression.  
  **Strong:** versioned golden JSONL; CI job runs base vs adapter; separate RAGAS job for retrieval builds; forgetting suite tagged by capability; contamination audit when adding train data. Present two dashboards in the memo — **Behavior** and **Grounding** — and state which one FT is allowed to move; cite RAGAS docs for the grounding board and task metrics for the behavior board.

* **Worked Example:**  
  A claims-ops Deployment Copilot uses RAG over policy PDFs (Phase 2) and a LoRA for **fixed denial-letter structure**. Eval plan: (a) Week 10 RAGAS faithfulness/context precision on policy answers with retrieval on; (b) letter **schema pass rate** + SME rubric on 150 golden letters with retrieval off or with frozen distractor contexts; (c) forgetting suite of 50 general support prompts + safety items comparing base vs adapter. Ship only if (b) clears kill threshold without (a) or (c) regressing beyond agreed floors. OpenAI’s fine-tuning guide’s emphasis on evaluation after jobs aligns with treating loss as insufficient.

* **Apply It:**  
  1. Define a sealed task golden set and scoring (schema / rubric / match).  
  2. Define a forgetting suite (safety + general skills you must keep).  
  3. Keep RAGAS on the RAG path; never average Behavior + Grounding into one vanity score.  
  4. Write kill criteria: format@golden < X or forgetting delta > Y → abandon FT.  
  5. Plan separate CI workflows for adapter candidates vs index/prompt candidates.  
  6. Attribute hybrid failures with Week 16 slicing before collecting more data or raising `r`.

---

### Cost and maintenance of fine-tunes

* **Fundamentals:**  
  Fine-tuning shifts spend from **per-request prompt tokens** to **upfront training + ongoing hosting + retrain ops**. Chip Huyen’s production essay frames the prompting-vs-finetuning cost trade: baking instructions into weights can remove thousands of prompt tokens per call — material at high QPS — but only after you pay for data, training, and evaluation (*Building LLM applications for production*).

  **Cost stack:**

  | Layer | Examples |
  |-------|----------|
  | **Training** | GPU hours (LoRA/QLoRA), or OpenAI/Bedrock job fees; engineer time for configs |
  | **Labeling** | Often dominates (dataset construction) |
  | **Hosting** | Dedicated endpoint, provisioned throughput (Bedrock), GPU replica for merged model, or adapter+base memory |
  | **Versioning** | Artifact registry: `base_revision + adapter_id + dataset_hash + eval_report` |
  | **Drift / rebase** | When the **base model** updates, adapters may need retrain; prompts/RAG indexes usually port cheaper |
  | **Eval CI** | Golden + forgetting suites on every candidate |

  **Ops burden vs prompt/RAG changes:** changing a system prompt or re-indexing is typically a deploy measured in minutes–hours. Shipping a new FT is a **model release**: train, eval gates, canary, rollback. That burden is justified when the decision framework’s FT-win conditions hold at scale; otherwise Week 20 cost engineering should prefer caching, shorter prompts, better retrieval, or smaller models without FT.

  **Payback sketch for the decision memo:**  
  `monthly_savings ≈ calls/month × tokens_removed_per_call × $/token`  
  `payback_months ≈ (labeling + train + eval_eng + host_delta) / monthly_savings`  
  If payback exceeds the expected life of the base model revision (or voice churn cycle), kill FT.

* **The Alternatives:**  

  | Approach | CapEx / train | OpEx / call | Change velocity |
  |----------|---------------|-------------|-----------------|
  | Long prompts + few-shots | Low | High tokens | Fast |
  | RAG | Index infra | Retrieval + context tokens | Fast for facts |
  | Managed FT (OpenAI/Bedrock) | Job fees | Custom-model pricing / provisioned | Medium |
  | Self-host LoRA | GPU train | GPU serve or merge-to-edge | Slow–medium |
  | Distilled small model | Train/distill | Cheap QPS | Medium |

  | Maintenance event | Prompt/RAG | Fine-tune |
  |-------------------|------------|-----------|
  | Policy doc update | Re-index | Retrain if facts were in weights (anti-pattern) |
  | Brand voice tweak | Prompt edit | Relabel + retrain |
  | Vendor base model upgrade | Smoke test | **Rebase adapters**, full eval |
  | Traffic spike | Scale retrieval/LLM | Scale FT endpoint; watch GPU $ |

  Tradeoff: PEFT adapters are cheap to **store** but not free to **operate** if every tenant needs isolation, telemetry, and eval.

* **Failure Modes:**  
  - Shadow IT LoRAs with no owner after the hackathon.  
  - Production pinned to an old base because rebase risk is unknown — security patches delayed.  
  - Cost dashboards that show “LLM $ down” while hidden GPU serving $ and labeling retainers soar.  
  - Customers surprised that “we fine-tuned once” does not track their weekly policy corpus (RAG still required).  
  - FDEs unable to write kill criteria tied to **payback period** (Week 20): train_cost / (token_savings_per_call × calls).  
  - One successful job → forever endpoint; no adapter inventory; base upgrades ignored.

* **Average vs. Strong Engineer:**  
  **Average:** train once; host forever; ignore base upgrades; omit labeling from the budget.  
  **Strong:** model card per adapter; scheduled eval against golden; rebase policy (“within N weeks of base release”); cost alarms on training accounts; compare to prompt+RAG baseline monthly. Put train + host + rebase + labeling in the decision memo; cite Bedrock throughput / OpenAI usage pricing pages as inputs; recommend RAG for churning facts to avoid retrain tax.

* **Worked Example:**  
  An e-commerce Deployment Copilot burns ~1.5k tokens/call on style exemplars for product-description rewrites at 20M calls/month. Memo math (Week 20 style): if FT removes ~1k tokens/call at published token prices, monthly savings dwarf a managed fine-tune job — **but** only if (a) descriptions don’t require citeable inventory facts (those stay RAG), (b) labeling 1k gold examples is funded, and (c) kill criteria fire when a new base model ships and rebase + eval exceed one quarter of savings. If traffic is low or voice changes weekly, the memo should **kill FT** and keep prompts. Chip Huyen’s cost framing and OpenAI/Bedrock pricing pages are the inputs — not vibes.

* **Apply It:**  
  1. Line-item labeling, train, host delta, eval eng, and rebase in the memo.  
  2. Compute payback months with the savings sketch above.  
  3. State a rebase policy when vendors ship new base models.  
  4. Compare change velocity: prompt/RAG minutes–hours vs FT model-release cadence.  
  5. Kill FT if payback exceeds base-revision life or voice-churn cycle.  
  6. Keep churning facts on RAG so policy updates never force a retrain.

---

## Week 26 build checklist (end-to-end)

Use this as the chapter’s capstone sequence; every concept above maps here. **Decision memo only — no toy LoRA.**

1. **Plateau proof:** Show prompt + RAG measured with Week 10 metrics on the named Deployment Copilot surface; classify residual failures.  
2. **Criteria:** Map the product to the decision framework (behavior/style/format vs fresh/citeable facts; latency; air-gap; iteration velocity; data availability).  
3. **PEFT shape (if FT):** Name LoRA/QLoRA (or managed vendor FT) as the implementation shape; record knobs and base-revision pinning as placeholders — do not train this week.  
4. **Data plan:** Annotation guide; quality > quantity; train/val/golden; contamination controls; labeling hours; SFT first, preferences only if needed.  
5. **Eval plan:** Task golden + forgetting suite; separate Behavior vs Grounding dashboards; RAGAS stays on the RAG path.  
6. **Risks:** Contamination, catastrophic forgetting, ops burden on base-model updates, stale knowledge in weights, eval gaps vs Week 10 RAGAS.  
7. **Cost / maintenance:** Payback sketch; hosting; versioning (`base_revision + adapter_id + dataset_hash + eval_report`); rebase policy.  
8. **Kill criteria:** Explicit conditions to abandon FT (e.g., format@golden < X after N high-quality examples while prompt+RAG still wins on latency/$) or abandon RAG-only (e.g., format SLO unmet and air-gap forbids retrieval).

When those steps are true, Week 26 is done in the syllabus sense: fine-tuning is a **gated** investment with dataset, eval, and ops owners — not a prestige word or a Colab demo.

---

## Compilation notes

- All concept sections above are grounded in `research/phase-7/week-26-fine-tuning/` (`00`–`05` + README).  
- No section required `[NEEDS MORE RESEARCH]` for the five syllabus concepts covered in research files `01`–`05`.  
- Outside URLs from research are not required reading to understand this chapter; operational detail was inlined from the notes.  
- Elective placement and “does not replace Weeks 1–24” follow research `00` / README.  
- Build is decision memo only (not a toy LoRA), per syllabus.
