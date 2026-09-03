# Chapter 27 — Open-source and self-hosted models

> **Phase 7 — Supplementary Electives**  
> **Editorial status:** COMPLETE  
> **Source of truth:** `research/phase-7/week-27-open-source-self-hosted/`  
> **Syllabus Build:** Add a **self-hosted model as one leg of the Week 20 router** — do **not** replace the hosted API stack. Document (and later implement in the Week 20 lab) only: (1) **route subset** — rules or classifier send a defined slice of queries (e.g. PII-tagged tenants, “must stay on-prem,” cheap FAQ) to a **local Ollama-served OSS model**; (2) **short comparison** — same golden set for **latency** (TTFT / p95), **quality** (task metric), and **cost** ($/1k calls amortized GPU vs API tokens) vs existing hosted routes; (3) **direct answer** — what if the customer **cannot use a hosted API** (residency, air-gap, procurement)? Show the self-hosted path is a first-class route, not an afterthought.

---

## Prerequisites Recap

Before this week you should already have from Week 26 (Phase 7 elective — fine-tuning when RAG isn't enough):

- **RAG vs FT decision** — residual-failure taxonomy (behavior/format vs fresh/citeable facts vs packing); hybrid when both fail.  
- **LoRA / QLoRA / PEFT overview** — small adapters, not full-weight cosplay; knobs and base-revision pinning as placeholders.  
- **Decision memo** — criteria, risks (contamination, forgetting, ops/rebase, stale knowledge in weights, eval gaps vs Week 10 RAGAS), and kill criteria — **not** a toy LoRA training run.

You do **not** need a self-hosted router leg, Ollama/vLLM comparison memo, or air-gap weight-import runbook yet as *finished* products — that is what this week ships. You **do** need Week 20 cost/latency routing as the surface this elective extends, and Week 19 residency language when the driver is compliance. Week 26’s memo stays upstream: PEFT on open weights is optional follow-on once a base OSS model is chosen and served; residency and air-gap often force the serving question *before* adapters.

---

## What this week builds

Week 26 shipped a written **decision memo** (criteria, risks, kill criteria — not a toy LoRA). Week 27 continues **Phase 7 — Supplementary Electives** — these weeks do **not** replace Weeks 1–24. Suggested slot in research: fold into **Week 20** model routing, or stand alone immediately after it; read Week 19 residency first when the driver is compliance — or append after the Week 24 capstone; **this course appends them** after Week 24 / Week 25 / Week 26.

Week 27 treats **open-weight models + self-hosted inference** as a first-class FDE capability — not a hobbyist side quest. An FDE who can only call hosted APIs is stuck when the customer requires **data residency**, **air-gap**, **unit-cost at high QPS**, or **procurement** that forbids third-party LLM SaaS. The syllabus trio — **Ollama**, **vLLM**, **quantization** — is the practical stack: pull a quantized Llama/Qwen/Gemma, serve it locally, then harden serving for production.

| Lever | What you control | Typical week |
|-------|------------------|--------------|
| Hosted API (OpenAI / Anthropic / Bedrock) | Prompt, tools, routing | Weeks 5, 18–20 |
| **Open weights + self-host** | Weights location, hardware, quant, serving stack | **Week 27 (this elective)** |
| PEFT on open weights | Task behavior on *your* GPU | Week 26 |

This week answers five coupled questions that FDE reviews and interview deep-dives treat as the minimum bar once Week 20 routing and (optionally) a Week 26 FT go/no-go already exist:

1. **Landscape** — shortlist Llama / Qwen / Gemma with task eval + license.  
2. **Quantization** — size hardware with INT4/AWQ/GPTQ or GGUF reality.  
3. **Tooling** — Ollama for spike; graduate to vLLM (or NIM) for SLOs.  
4. **Self-host vs API** — measured latency / quality / cost on the same golden set.  
5. **Air-gap** — weight import, offline eval, update windows, failover policy.

**Do not** replace the hosted API stack — add self-hosted as **one** Week 20 route. Do **not** drop Week 26’s decision memo or bake FT into every on-prem story — PEFT follows serving choice. Do **not** implement the router or Ollama integration inside the research corpus; ship the **comparison memo**. Do **not** start Week 28 (multimodal I/O) from this chapter — stay on where weights run and how you measure the local leg.

The **build** adds a self-hosted leg to the **Week 20 router** and forces a measured latency / quality / cost comparison — not a vague “we support open source” checkbox. Interview artifact = **comparison memo** that answers “customer can’t use hosted API” with numbers: route subset, golden-set deltas, and explicit failover.

| This week | Not this week |
|-----------|----------------|
| Self-hosted as one Week 20 router leg | Rip out hosted APIs |
| Landscape + quant + Ollama→vLLM path | Toy LoRA / adapter training (Week 26 memo holds) |
| Latency / quality / cost comparison memo | Vague “we support open source” slide |
| Air-gap import + offline eval (if required) | Multimodal vision/STT/TTS path (Week 28) |

Read the concepts in order. Each section’s **Worked Example** and **Apply It** assume the same flagship service (working title: Deployment Copilot) gaining an on-prem / local OSS route beside existing hosted providers — after Week 26’s FT decision memo is already written.

**Default path (synthesis):**

1. Pick candidates from Llama / Qwen / Gemma with an explicit **task eval** + license check.  
2. Size hardware with **quantization** reality — do not assume BF16 70B on one consumer GPU.  
3. Prototype on **Ollama**; graduate serving to **vLLM** (or NIM) when concurrency and SLOs matter.  
4. Price self-host vs API with Week 20 math; keep both routes behind one router.  
5. If air-gapped: plan weight import, offline eval, and update windows before promising the deal.  
6. Ship the **comparison memo** that answers “customer can’t use hosted API” with measured numbers.

---

### Open-source model landscape (Llama / Qwen / Gemma)

* **Fundamentals:**  
  “Open-source model” in enterprise practice usually means **open weights** (downloadable checkpoints + license) — not necessarily OSI-approved source for training data or full training code. The FDE shortlist for 2024–2026 self-host work centers on three families:

  | Family | Typical strengths | Watch-outs |
  |--------|-------------------|------------|
  | **Meta Llama** | Broad ecosystem, recipes, sizes from edge (1B/3B) to 70B+ / MoE; strong English + coding baseline | Community License + Acceptable Use; gated download; not “do anything” public domain |
  | **Qwen (Alibaba)** | Multilingual breadth, long-context / reasoning variants, dense + MoE options; good HF + vLLM support | Check exact license per checkpoint; Chinese + EN eval balance on *your* task |
  | **Google Gemma** | Permissive Gemma license (verify version); strong small/mid sizes for on-device and edge; multimodal variants | Size ladder differs from Llama; confirm commercial terms for the exact gemma-* card |

  **How to evaluate for a task (syllabus):**

  1. **Task golden set** — same slices as Week 10 / Week 20: format accuracy, groundedness if RAG, tool-call validity, language mix. Leaderboard Elo is a prior, not a go/no-go.  
  2. **Size vs hardware** — parameter count × dtype (next section) must fit GPU RAM + KV cache at target context.  
  3. **Context length** — claimed 128k is not free; measure prefill latency and quality at *your* pack sizes (Week 25).  
  4. **License & AUP** — Llama Community License, Qwen license text, Gemma terms; prohibited uses; redistribution of derivatives.  
  5. **Serving maturity** — day-0 vLLM/Ollama/llama.cpp/HF Transformers support; tokenizer quirks; chat template.  
  6. **Tool / JSON / agent fit** — if the product is agentic (Phase 3), test tool schemas before loving MMLU.  
  7. **Safety & refusal** — on-policy for the customer vertical; open weights still need product guardrails.

  Chip Huyen’s production framing still applies: pick models by **application requirements and cost**, not novelty (*Building LLM applications for production*). Instruct-tuned checkpoints fit chat/tools; **base** fits continued pretrain / FT (Week 26). Wrong variant wastes a week.

* **The Alternatives:**  

  | Choice | Upside | Downside |
  |--------|--------|----------|
  | Always newest Llama | Ecosystem + docs | May need requant + re-eval every release |
  | Always Qwen for multilingual | Strong non-EN | Team familiarity / safety eval gaps |
  | Always small Gemma on-device | Latency + privacy | Harder reasoning / coding ceiling |
  | Closed API only | Peak quality, zero GPU | Week 19 residency / air-gap fail |
  | Mix via Week 20 router | Best of each | Eval matrix grows with N models |

  | Eval shortcut | Risk |
  |---------------|------|
  | Trust LMSYS / Open LLM Leaderboard alone | Distribution shift vs customer tickets |
  | “70B always beats 8B” | Latency/$ may favor 8B + RAG + tools |
  | Ignore chat template | Silent quality drop (“base” vs “Instruct”) |

  The syllabus selects **task-driven shortlisting across Llama / Qwen / Gemma** before quantization math and serving choice. Map candidates to **routes** (edge FAQ → Gemma/Llama-3B; complex reasoning → Qwen/Llama-70B-quant; PII tenants → local only) rather than one forever-model.

* **Failure Modes:**  
  - FDEs default to whatever Ollama’s homepage lists first; customer German legal Q&A never measured.  
  - Procurement gets a Llama license surprise mid-pilot.  
  - Hardware quotes assume BF16 70B when the winning model was Qwen-14B-AWQ.  
  - Week 26 FT starts on a base that cannot serve tool calls even before adapters.  
  - Interviews cannot explain *why* three open families coexist (license, language, size ladder, ecosystem).  
  - Silent quality drop from loading a **base** checkpoint where **Instruct** was required.

* **Average vs. Strong Engineer:**  
  **Average:** screenshot Arena; pick top open model; ignore license; ship.  
  **Strong:** 2–3 candidate cards; fixed golden set; score latency + quality + license pass/fail; document runner-up; map candidates to router legs; cite official model cards in the design doc; re-run eval when weights revise. Industry practice at Meta `llama-models` cards, Qwen docs + HF pages, and Google AI Gemma docs is the citation bar — not a forum thread.

* **Worked Example:**  
  Deployment Copilot must support an EU support surface: German + English ticket triage (classification + short reply draft), 8k context of retrieved macros, and **no** US-hosted API for that tenant class. Shortlist Llama-3.1-8B-Instruct and Qwen2.5-7B-Instruct (or current peers from the same families); run the Week 20 golden set offline; pick the winner that fits one L4 with AWQ and passes license review. Escalate only the hard 5% to an approved regional endpoint if policy allows — else accept the local quality ceiling and design UX accordingly. Model-card pointers live in Meta’s official `llama-models` repo (e.g. Llama 3.1 card for sizes, context, languages, license).

* **Apply It:**  
  1. Write a one-page shortlist of 2–3 Llama / Qwen / Gemma candidates for one Deployment Copilot route.  
  2. Attach license/AUP pass-fail and serving maturity (Ollama/vLLM day-0) for each card.  
  3. Freeze a task golden set (format, groundedness if RAG, tool-call validity, language mix) — not a leaderboard screenshot.  
  4. Score each candidate on that set before buying GPUs or promising “Llama in your VPC.”  
  5. Document the runner-up and a kill criterion (“if local quality &lt; X, escalate or refuse the slice”).  
  6. Prefer Instruct (or chat-tuned) variants for the router leg unless Week 26 FT explicitly needs a base.

---

### Quantization basics

* **Fundamentals:**  
  **Quantization** stores (and sometimes computes) weights — and optionally activations — at lower numeric precision than the training dtype (typically FP16/BF16). Memory for parameters scales roughly with bits per weight:

  | Format | Bits / weight (approx) | 70B weight memory (order of magnitude) |
  |--------|------------------------|----------------------------------------|
  | FP16 / BF16 | 16 | ~140 GB |
  | INT8 / FP8 | 8 | ~70 GB |
  | INT4 (GPTQ/AWQ/GGUF Q4) | ~4 (+ scales/zeros overhead) | ~35 GB + overhead |

  A single **80 GB** datacenter GPU (e.g. A100/H100 80GB) cannot hold 70B in BF16 weights alone, and **KV cache** for long context still needs headroom. **4-bit weight-only** quantization brings weights into a range where **one 40–80 GB GPU** can load a 70B-class model and still serve modest batch/context — the syllabus answer to “why 70B fits on one GPU after quantization.”

  Two widely cited post-training methods:

  - **GPTQ** — layer-wise post-training quantization minimizing output error (Hessian / OBQ-style); arXiv:2210.17323.  
  - **AWQ** — activation-aware weight quantization; protects salient weights using activation magnitude; arXiv:2306.00978.

  **GGUF / llama.cpp / Ollama** use related low-bit schemes (Q4_K_M, Q5_K_M, etc.) optimized for local CPU/GPU runtimes. **vLLM** documents AWQ, GPTQ, FP8, and other formats for server deployment.

  **What you lose (always measure):**

  1. **Quality** — perplexity / task accuracy; sensitive tasks (math, precise JSON, rare languages) degrade first.  
  2. **Calibration dependence** — bad calibration set → silent regressions.  
  3. **Kernel / hardware lock-in** — not every GPU supports every path equally (see vLLM quantization hardware tables).  
  4. **Training story** — inference quant ≠ QLoRA training quant (Week 26); don’t conflate.

* **The Alternatives:**  

  | Strategy | Fit | Tradeoff |
  |----------|-----|----------|
  | BF16 / FP16 full precision | Max fidelity; multi-GPU | Cost; may be impossible on customer SKU |
  | FP8 / INT8 | Milder quality hit; good throughput on new GPUs | Still heavy for 70B on one mid GPU |
  | **INT4 AWQ/GPTQ** | Single-GPU 70B serving | Eval required; vendor kernel maturity |
  | GGUF Q4 on Ollama | Laptop / workstation prototype | Not a substitute for vLLM SLOs |
  | Smaller dense model (8B/14B) BF16 | Simpler; often better quality/$ | May need stronger RAG/tools |
  | Speculative decoding / MoE | Speed / capacity tricks | Extra complexity vs “just quantize” |

  | You might think… | Reality |
  |-------------------|---------|
  | “INT4 is free quality” | Task-dependent; always A/B vs BF16 on golden set |
  | “Fits in VRAM = production-ready” | KV cache + concurrency dominate at load |
  | “One quant file for all runtimes” | GGUF ≠ AWQ safetensors; pick for the engine |

  The syllabus expects **quantize for the target engine** (AWQ/GPTQ for vLLM; GGUF for Ollama/llama.cpp), calibrate on domain text, and compare BF16 (or official FP8) vs INT4 on **task** metrics. NVIDIA NIM and Hub cards often publish pre-quantized variants — still verify on *your* eval harness.

* **Failure Modes:**  
  - Capacity plans quote 4× A100s for a workload that fits one GPU at INT4 — deal dies on CapEx.  
  - Or the opposite: ship Q3 ultra-aggressive quants, miss SLO quality, blame “open source is bad.”  
  - Ollama prototypes use Q4; production mistakenly loads BF16 and OOMs at first load test.  
  - Week 20 cost models ignore that **quant enables batching headroom**, changing $/query.  
  - Week 26 QLoRA discussions confuse training adapters with serving quants.  
  - Garbled Unicode / broken tool JSON after a bad calibration set — silent until agents fail.

* **Average vs. Strong Engineer:**  
  **Average:** download the smallest GGUF; skip eval; call it “the 70B.”  
  **Strong:** choose method for target engine; calibrate on domain text; compare BF16 (or official FP8) vs INT4 on task metrics; monitor for garbled Unicode / broken tool JSON; put a VRAM spreadsheet in the design doc (weights + KV + overhead); cite GPTQ/AWQ papers and vLLM quant docs; set a kill criterion (“if format@schema drops &gt; N points vs BF16, use 8-bit or smaller model”).

* **Worked Example:**  
  A customer offers Deployment Copilot a single **48 GB** GPU for an internal Llama-3.1-70B assistant. BF16 weights alone are impossible. Plan: serve an **AWQ 4-bit** checkpoint via vLLM; reserve memory budget for 8k context and batch 4; run the Week 20 golden set vs the hosted GPT-class route. If legal-clause extraction F1 drops below threshold, fall back to **32B/34B BF16** or **70B INT8** on a larger SKU — don’t silently ship broken INT4. Papers and docs to cite in the design memo: AWQ (arXiv:2306.00978), GPTQ (arXiv:2210.17323), and vLLM’s quantization feature docs.

* **Apply It:**  
  1. For the chosen candidate, write a VRAM budget: weights + KV cache at target context + overhead.  
  2. Pick the quant format that matches the intended runtime (GGUF for Ollama spike; AWQ/GPTQ for vLLM).  
  3. A/B the quantized checkpoint against BF16 (or official FP8) on the same golden set.  
  4. Record kill criteria for quality drop (schema accuracy, tool JSON, rare-language tasks).  
  5. Do not conflate serving INT4 with Week 26 QLoRA training quant in the design doc.  
  6. Re-check VRAM under expected concurrency — “fits at load” ≠ “fits at batch N.”

---

### Local inference tooling (Ollama vs vLLM)

* **Fundamentals:**  
  Self-hosting needs a **runtime**, not just weights. Two syllabus tools occupy different niches:

  | | **Ollama** | **vLLM** |
  |--|------------|----------|
  | **Job** | Developer-local / small-team runner | High-throughput inference **server** |
  | **UX** | `ollama pull` / `ollama run`; Modelfile; simple HTTP API | OpenAI-compatible server; Python `LLM` API; rich engine flags |
  | **Strengths** | Minutes to first token on a laptop; model library; GGUF ergonomics | PagedAttention, continuous batching, tensor parallel, quant backends, metrics |
  | **Weak when** | Multi-tenant prod SLOs, max GPU util, complex routing farms | Overkill for a single engineer’s spike |

  **Ollama for prototyping:** validate chat templates, prompt packs, and “does this OSS model even solve the task?” before buying multi-GPU serving complexity. Ideal for the Week 27 build’s **local leg** during development.

  **vLLM for production-grade serving:** when QPS, p95 TTFT/TPOT, and GPU utilization matter. Docs cover quantization (AWQ/GPTQ/FP8), distributed serving, and OpenAI-compatible endpoints so the Week 20 router can treat `local-llama` like any other provider base URL.

  **Adjacent (not syllabus-primary but industry-real):**

  - **llama.cpp / LM Studio** — local/edge cousins of Ollama’s stack.  
  - **NVIDIA NIM** — packaged, supported microservices for optimized inference on NVIDIA GPUs; path when the customer wants OSS weights with vendor support.  
  - **HF Text Generation Inference (TGI)** — alternate production server; compare when customer standardizes on HF.

  Chip Huyen’s platform writing emphasizes inference as a **platform concern** (batching, caching, routing) — local tooling must graduate into that layer (*Building a Generative AI Platform*).

* **The Alternatives:**  

  | Path | Pros | Cons |
  |------|------|------|
  | Ollama only forever | Simple ops story | Weak multi-user scheduling; harder enterprise observability |
  | vLLM from day 1 | Prod-shaped | Slower spike; more YAML/CUDA pain in week one |
  | **Ollama → vLLM graduate** (recommended) | Fast learning + clear promotion criteria | Two runtimes briefly in flight |
  | NIM / managed OSS endpoint | Support + performance recipes | Cost; may not be air-gapped |
  | Raw `transformers` generate | Full control | No continuous batching; poor throughput |

  | Promotion signal (prototype → vLLM) | Why |
  |-------------------------------------|-----|
  | Concurrent users &gt; few | Need continuous batching |
  | p95 latency SLO written | Need engine metrics + tuning |
  | Multi-GPU model | Tensor parallel in server |
  | Router must share OpenAI schema | vLLM compatibility layer |

  The syllabus selects **Ollama for the spike and Week 27 local leg, then graduate to vLLM (or NIM on NVIDIA-centric accounts)** when concurrency and SLOs matter. Freeze model ID + quant before promoting.

* **Failure Modes:**  
  - FDEs demo Ollama and leave customers believing that is the production architecture.  
  - Or they start with a multi-node vLLM Helm chart before proving the model wins the task.  
  - Week 20 routers hard-code OpenAI URLs with no abstraction for `base_url=http://vllm:8000/v1`.  
  - Quantized artifacts built for the wrong engine (GGUF vs AWQ) waste calibration time.  
  - Incidents have no GPU utilization / queue depth dashboards because “it worked on my Mac.”  
  - Shared GPU box with no auth and no resource quotas becomes the “production” path.

* **Average vs. Strong Engineer:**  
  **Average:** Docker with Ollama on a shared GPU box; no auth; no resource quotas; one model name forever.  
  **Strong:** Ollama (or laptop llama.cpp) for spike; freeze model ID + quant; stand up vLLM with OpenAI-compatible API; put behind the same gateway as hosted providers; scrape Prometheus metrics; canary new weights; write promotion criteria in the design doc; for NVIDIA-centric accounts, evaluate NIM as the supported wrapper around similar open models.

* **Worked Example:**  
  Deployment Copilot’s Week 20 router adds `provider=ollama` for PII-tagged tenants during the pilot (`http://127.0.0.1:11434`). After the comparison memo passes, swap the same model family to **vLLM** on the customer’s GPU node (`/v1/chat/completions`) without changing application prompts — only `base_url` and auth. Keep Ollama in CI for smoke tests on CPU/small GPU runners. Cite Ollama docs/product, vLLM docs (including the OpenAI-compatible server), and NVIDIA NIM docs when the account standardizes on NVIDIA stacks.

* **Apply It:**  
  1. Spike the shortlisted Instruct model on Ollama; confirm chat template and golden-set smoke pass.  
  2. Freeze model ID + quant tag used in the Week 27 router leg.  
  3. Abstract the Week 20 router behind a provider `base_url` so local and hosted share one client shape.  
  4. Write promotion criteria (concurrency, p95 SLO, multi-GPU, metrics) before claiming “production self-host.”  
  5. When promoting, serve via vLLM (or NIM) with OpenAI-compatible `/v1/chat/completions`.  
  6. Keep Ollama (or small-GPU smoke) in CI; put GPU util / queue depth on the same dashboards as hosted routes.

---

### Self-hosted vs API tradeoffs

* **Fundamentals:**  
  Hosted APIs price **tokens + premium for frontier capability**. Self-hosting prices **CapEx/OpEx for GPUs**, power, people, and idle capacity. Neither wins universally — the Week 20 router exists so you can **mix**.

  | Dimension | Hosted API | Self-hosted OSS |
  |-----------|------------|-----------------|
  | **Marginal cost** | ~$/1M tokens | Near-zero per token once GPU is paid; idle still costs |
  | **Latency** | Cross-internet RTT + provider queue | LAN/VPC; can win TTFT if GPU warm and close to app |
  | **Control** | Limited (rate limits, model deprecations) | Full: weights, logs stay local, pin revisions |
  | **Quality ceiling** | Often highest frontier | Strong open weights; may lag hardest tasks |
  | **Compliance** | Region + ZDR contracts (Week 19) | Strongest story for air-gap / residency |
  | **Ops** | Vendor pager | Your on-call for CUDA, capacity, patching |

  **Break-even intuition (teach the method, not a fake number):**

  1. Estimate monthly token volume and API $ (Week 20 attribution).  
  2. Estimate GPU instance $/month × utilization (incl. HA spare).  
  3. Add eng hours for serving + eval regression.  
  4. Compare **at the slice** the router would send local — not at 100% of traffic unless forced.

  **Latency:** self-host wins when (a) GPU is co-located, (b) batching is healthy, (c) model size/quant match the SLO. Self-host **loses** when a single underpowered GPU serializes a queue while the API fans out globally.

  **Control:** model pin, log retention, custom decoding, offline operation — the reasons regulated buyers ask.

* **The Alternatives:**  

  | Strategy | When it wins | When it fails |
  |----------|--------------|---------------|
  | 100% API | Low volume; need frontier; residency OK | Air-gap RFP; huge steady QPS |
  | 100% self-host | Strict residency; stable high QPS; mid models OK | Spiky load; need GPT-class reasoning always |
  | **Hybrid router** | Most enterprise | Requires dual eval + failover policy |
  | Managed OSS in cloud (Bedrock/Vertex/NIM) | Want open weights without DIY | True air-gap; data still in cloud |
  | Batch API / async | Throughput jobs | Interactive UX |

  | Cost fallacy | Correction |
  |--------------|------------|
  | “GPUs are free, we already own them” | Opportunity cost + power + HA + people |
  | “API is always more expensive” | Idle A100s can dwarf token bills at low QPS |
  | “Local is always lower latency” | Cold load + queue beats a warm API |

  The syllabus selects the **hybrid Week 20 router** with a measured comparison memo: latency, quality, and cost on the same golden set for API vs Ollama/vLLM routes. NVIDIA NIM blogs/docs often frame TCO for optimized self/managed inference — use as vendor input, still run *your* numbers. Chip Huyen’s production writing frames system costs beyond model fees (*Building LLM applications for production*).

* **Failure Modes:**  
  - Finance cannot approve GPU CapEx or API commit discounts with a straight face.  
  - FDEs cannot answer “what if customer can’t use hosted API?” except with vibes.  
  - Routers send everything local “for privacy” and destroy UX latency.  
  - Week 19 residency wins the deal, then Week 20 unit economics lose the renewal.  
  - Interviews fail the classic “build vs buy inference” question.  
  - Slides claim “80% cheaper with Llama” using peak API list price vs fully loaded GPU at 100% util.

* **Average vs. Strong Engineer:**  
  **Average:** marketing slide with peak list price vs fantasy 100% GPU util; or refuse every residency deal.  
  **Strong:** measure on a golden set — **latency, quality, cost** — for API route vs Ollama/vLLM route; publish the table; set router thresholds; hybrid design with explicit **failover** (local down → approved regional API or graceful degrade); reuse Week 20 dashboards for both providers; cite Huyen on system costs beyond model fees.

* **Worked Example:**  
  Extend Deployment Copilot’s Week 20 router so `tenant.residency == "on_prem"` or `task == "faq_macro"` goes to `ollama/llama3.1:8b-instruct-q4_K_M`. Run 500 golden prompts: record TTFT p50/p95, task accuracy, and $/1k requests (API invoice vs amortized GPU hour / throughput). Deliver a one-pager: “If the customer cannot use a hosted API, route X% locally with quality delta Δ and latency delta Δ; escalate only Y.” That is the FDE answer — not “buy more GPUs” or “refuse the RFP.”

* **Apply It:**  
  1. Define the router slice that will go local (residency tag, PII tenant, cheap FAQ — not “everything”).  
  2. Estimate API $ and fully loaded GPU $ **for that slice only**, including idle/HA and eng hours.  
  3. Run the same golden set on hosted vs local; record TTFT p50/p95, task metric, $/1k calls.  
  4. Publish the comparison table and router thresholds in the design memo.  
  5. Write failover policy (local down → approved regional API, or `failover=none` with graceful degrade).  
  6. Answer explicitly: “customer cannot use hosted API” → which % stays local, at what quality/latency delta.

---

### Air-gapped deployment

* **Fundamentals:**  
  **Air-gapped** (or “highly isolated”) deployment means inference hosts **cannot** reach public model hubs, hosted LLM APIs, or often general internet. This is stricter than “VPC with private endpoints” (Week 19 residency). Self-hosted OSS is frequently the **only** viable generative path.

  Checklist an FDE must design explicitly:

  | Concern | Air-gap implication |
  |---------|---------------------|
  | **Weight import** | Download/verify on a connected bastion; transfer via approved media / data diode; checksum (SHA256) + signature policy |
  | **License acceptance** | Llama/Qwen/Gemma terms accepted by legal **before** transfer; keep license text offline |
  | **Tokenizer / templates** | Ship chat templates + tokenizer files with weights; no runtime Hub fetch |
  | **Runtime images** | Mirror container images (vLLM, CUDA, drivers) to private registry |
  | **Quant artifacts** | Produce AWQ/GPTQ/GGUF **outside**, promote immutable artifacts in |
  | **Eval** | Golden sets and judge models must run offline (or use non-LLM metrics) |
  | **Telemetry** | No phone-home; local logs only; redaction still applies |
  | **Updates** | Scheduled “update windows” with re-eval; no silent `pull latest` |
  | **RAG / tools** | Indexes and tools also air-gapped; no web search dependency |
  | **Time sync / certs** | Offline PKI; NTP policy — broken clocks break TLS to internal gateways |

  Week 19 residency asks *where* data lives; air-gap asks whether **any path** to the public model provider exists. Answer carefully on questionnaires. Air-gap is where Week 27 stops being optional for FDEs in defense, critical infrastructure, and some public sector.

* **The Alternatives:**  

  | Pattern | Pros | Cons |
  |---------|------|------|
  | True air-gap + local vLLM | Max isolation | Highest ops; slow model refresh |
  | Private VPC + Hub allowlist | Easier updates | Not air-gap; may fail audit |
  | Connected bastion → diode → serve | Controlled promotion | Process-heavy; needs staffing |
  | Managed confidential / sovereign cloud | Less DIY | Contractual; may still not be “air-gap” |
  | Refuse GenAI in air-gap | Honest | Product gap; competitor with OSS wins |

  | Temptation | Risk |
  |------------|------|
  | USB stick of random GGUF from forum | Supply chain / malware / license |
  | “We’ll use API just for eval” | Policy violation; train bad habits |
  | Skip golden-set re-run after weight bump | Silent regressions in production |

  The syllabus selects **explicit artifact promotion** (connected lab → verified transfer → internal serve) with offline eval gates and documented rollback. NVIDIA NIM enterprise deployment guidance is useful when the customer standardizes on NVIDIA stacks **inside** the boundary — still plan artifact import.

* **Failure Modes:**  
  - Pilots depend on `ollama pull` and die on the customer’s disconnected VLAN.  
  - Security rejects the design for undeclared egress to Hugging Face or Docker Hub.  
  - Model updates become heroics; nobody owns the promotion checklist.  
  - Week 26 FT datasets cannot be refreshed; adapters drift from frozen bases.  
  - Incident response cannot fetch mitigations; playbooks assume GitHub access.  
  - Hosted API left as “failover” on a network that forbids it — policy and UX lie.

* **Average vs. Strong Engineer:**  
  **Average:** copy a laptop Ollama models directory; hope drivers match; no SBOM.  
  **Strong:** private mirror of approved weights + containers; SBOM; checksum verification; staged promote (lab → pre-prod → air-gap); offline eval gate; documented rollback to previous weight hash; map questionnaire language (air-gap vs private network vs residency); propose diode workflow; cite model cards for license; pair with Week 19 auth so only service accounts hit internal vLLM; never promise “same day” model upgrades.

* **Worked Example:**  
  A national lab forbids egress for Deployment Copilot. FDE builds on a connected lab cluster: quantize Llama-3.1-8B-Instruct AWQ, bake a vLLM container pinned by digest, run golden-set eval, sign the bundle. Transfer via approved media; verify checksums; deploy to internal k8s with no `ImagePull` from the public internet. Quarterly update window: repeat eval; if quality regresses, keep previous digest. Hosted API is **not** a failover — UX must degrade gracefully with local-only models (Week 20 router policy `failover=none`). License acceptance and Gemma/Llama download flows happen on the connected side before transfer; residency questionnaires distinguish air-gap from mere private-network residency.

* **Apply It:**  
  1. Classify the customer ask: air-gap vs private network vs residency-only (Week 19 language).  
  2. Design weight + container import: bastion download, checksum/signature, approved media or diode.  
  3. Ship tokenizer, chat templates, and quant artifacts with the weights — no runtime Hub fetch.  
  4. Mirror runtime images to a private registry; pin by digest.  
  5. Gate every weight bump with offline golden-set eval and a documented rollback hash.  
  6. Set router failover explicitly (`failover=none` when no approved egress path exists).

---

## Week 27 build checklist (end-to-end)

Use this as the chapter’s capstone sequence; every concept above maps here.

1. **Landscape:** Shortlist 2–3 Llama / Qwen / Gemma candidates; license + task golden set before hardware quotes.  
2. **Quantization:** Size VRAM with INT4/AWQ/GPTQ or GGUF reality; A/B vs higher precision on the golden set.  
3. **Tooling:** Prototype the local leg on Ollama; write promotion criteria to vLLM (or NIM).  
4. **Router slice:** Add self-hosted as **one** Week 20 route — do not rip out hosted APIs.  
5. **Comparison memo:** Same golden set → latency (TTFT / p95), quality, cost ($/1k amortized GPU vs API).  
6. **Air-gap (if required):** Weight import, offline eval, update windows, `failover=none` before promising the deal.  
7. **Direct answer:** Document what happens when the customer cannot use a hosted API — first-class local route with measured deltas, not an afterthought.

When those steps are true, Week 27 is done in the syllabus sense: self-host is a **routable, measurable** product path beside Week 20 hosted routes.

---

## Looking ahead

Week 28 continues **Phase 7 — Supplementary Electives** with **multimodal AI as product I/O**. After this week’s self-hosted router leg and comparison memo (latency / quality / cost — not a vague “we support open source” checkbox), the next elective treats **vision, STT/TTS, and mixed context** as product surfaces — not demo gimmicks. The build adds **one real multimodal capability** to an existing stack (Phase 2 RAG or Phase 3 agent): **one** E2E path — screenshot/error-image → vision extract → RAG/tools, **or** voice → STT → same text path (optional TTS) — plus a short design note (modality contract, Week 25 context assembly, 5–10 golden multimodal cases). Do **not** start Week 28 by dropping this week’s local route or comparison table — serving location and modality I/O are separate levers. Week 26’s FT memo and Week 25’s context layer stay available; the deep work shifts from “where do weights run?” to “when is non-text I/O a real requirement vs a gimmick?”

---

## Compilation notes

- All concept sections above are grounded in `research/phase-7/week-27-open-source-self-hosted/` (`00`–`05` + README).  
- No section required `[NEEDS MORE RESEARCH]` for the five syllabus concepts covered in research files `01`–`05`.  
- Research **Open Questions** (regional APIs vs true air-gap longevity; OSS rebase cadence vs Week 26 adapters; NIM vs raw vLLM for enterprise FDEs; edge Gemma/Llama vs datacenter vLLM; GPU capacity ownership; MoE vs dense INT4; Apache vs Community License procurement; HF silent revisions; FP4/MXFP vs GPTQ/AWQ; KV-cache quant composition; confidential GPUs replacing air-gap; offline LLM-as-judge VRAM; SBOM/attestation minimums; carbon in TCO; prompt-cache break-evens) remain unresolved in the corpus — not answered here.  
- Outside URLs from research are not required reading to understand this chapter; operational detail was inlined from the notes.  
- Elective placement and “does not replace Weeks 1–24” follow research `00` / README.  
- Build is self-hosted Week 20 router leg + comparison memo only (not a full multi-node fleet), per syllabus.  
- Editorial pass: Prerequisites Recap bridges Week 26 (RAG vs FT decision, LoRA/QLoRA overview, decision memo — not a toy LoRA); Looking ahead bridges Week 28 (multimodal AI — vision, STT/TTS, mixed context, real vs gimmick; one E2E path); Phase 7 framed as supplementary electives; no new technical claims beyond research.  
- Week 28 multimodal depth is explicitly deferred — ship the OSS serving comparison here; multimodal I/O comes next.
