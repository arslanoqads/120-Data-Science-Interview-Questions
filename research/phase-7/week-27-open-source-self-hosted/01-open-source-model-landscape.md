# 01 — Open-source model landscape (Llama, Qwen, Gemma)

> Week 27 — Open-source and self-hosted models  
> Research notes (raw). How to evaluate an open-weight model for a **task**, not a leaderboard screenshot.

---

## Fundamentals

“Open-source model” in enterprise practice usually means **open weights** (downloadable checkpoints + license) — not necessarily OSI-approved source for training data or full training code. The FDE shortlist for 2024–2026 self-host work centers on three families:

| Family | Typical strengths | Watch-outs |
|--------|-------------------|------------|
| **Meta Llama** | Broad ecosystem, recipes, sizes from edge (1B/3B) to 70B+ / MoE; strong English + coding baseline | Community License + Acceptable Use; gated download; not “do anything” public domain |
| **Qwen (Alibaba)** | Multilingual breadth, long-context / reasoning variants, dense + MoE options; good HF + vLLM support | Check exact license per checkpoint; Chinese + EN eval balance on *your* task |
| **Google Gemma** | Permissive Gemma license (verify version); strong small/mid sizes for on-device and edge; multimodal variants | Size ladder differs from Llama; confirm commercial terms for the exact gemma-* card |

**How to evaluate for a task (syllabus):**

1. **Task golden set** — same slices as Week 10 / Week 20: format accuracy, groundedness if RAG, tool-call validity, language mix. Leaderboard Elo is a prior, not a go/no-go.  
2. **Size vs hardware** — parameter count × dtype (file 02) must fit GPU RAM + KV cache at target context.  
3. **Context length** — claimed 128k is not free; measure prefill latency and quality at *your* pack sizes (Week 25).  
4. **License & AUP** — Llama Community License, Qwen license text, Gemma terms; prohibited uses; redistribution of derivatives.  
5. **Serving maturity** — day-0 vLLM/Ollama/llama.cpp/HF Transformers support; tokenizer quirks; chat template.  
6. **Tool / JSON / agent fit** — if the product is agentic (Phase 3), test tool schemas before loving MMLU.  
7. **Safety & refusal** — on-policy for the customer vertical; open weights still need product guardrails.

Chip Huyen’s production framing still applies: pick models by **application requirements and cost**, not novelty (*Building LLM applications for production*).

---

## Alternatives & Tradeoffs

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

Tradeoff: **instruct-tuned** checkpoints for chat/tools vs **base** for continued pretrain / FT (Week 26). Wrong variant wastes a week.

---

## Necessity

Without a landscape + task-eval discipline:

- FDEs default to whatever Ollama’s homepage lists first; customer German legal Q&A never measured.  
- Procurement gets a Llama license surprise mid-pilot.  
- Hardware quotes assume BF16 70B when the winning model was Qwen-14B-AWQ.  
- Week 26 FT starts on a base that cannot serve tool calls even before adapters.  
- Interviews cannot explain *why* three open families coexist (license, language, size ladder, ecosystem).

The landscape file is the gate before quantization math (02) and serving choice (03).

---

## Industry Practice

- **Common:** screenshot Arena; pick top open model; ignore license; ship.  
- **Strong:** 2–3 candidate cards; fixed golden set; score latency + quality + license pass/fail; document runner-up.  
- **FDE / senior:** map candidates to **routes** (edge FAQ → Gemma/Llama-3B; complex reasoning → Qwen/Llama-70B-quant; PII tenants → local only); cite official model cards in the design doc; re-run eval when weights revise.

References: Meta `llama-models` cards; Qwen docs + HF model pages; Google AI Gemma docs; Hugging Face Hub model cards; Huyen genai platform post for architecture context.

---

## Concrete Scenario

**Meta Llama model cards (official repo):**  
https://github.com/meta-llama/llama-models  

Example card for Llama 3.1 (sizes, context, languages, license pointers):  
https://github.com/meta-llama/llama-models/blob/main/models/llama3_1/MODEL_CARD.md  

**Product memo pattern:** An EU support bot needs German + English ticket triage (classification + short reply draft), 8k context of retrieved macros, and **no** US-hosted API. Shortlist Llama-3.1-8B-Instruct and Qwen2.5-7B-Instruct (or current peers); run the Week 20 golden set offline; pick the winner that fits one L4 with AWQ and passes license review. Escalate only the hard 5% to an approved regional endpoint if policy allows — else accept local quality ceiling and design UX accordingly.

---

## Open Questions

- Do MoE open models (Llama 4-class, Qwen-MoE) change the “one GPU” story more than dense 70B + INT4?  
- Will Apache-licensed families displace Community License models in regulated procurement?  
- How should FDEs version “the model” when HF revisions move silently under the same repo name?  
- Is multilingual quality better bought via Qwen weights or via translation microservice + EN Llama?  
- When does Week 26 FT on a mid-size open model beat routing to a larger untuned peer?

---

## Sources

- https://www.llama.com/  
- https://github.com/meta-llama/llama-models  
- https://github.com/meta-llama/llama-models/blob/main/models/llama3_1/MODEL_CARD.md  
- https://qwen.readthedocs.io/en/latest/  
- https://qwenlm.github.io/blog/qwen3/  
- https://huggingface.co/docs/transformers/main/model_doc/qwen3  
- https://ai.google.dev/gemma  
- https://ai.google.dev/gemma/docs  
- https://huggingface.co/blog/gemma  
- https://huyenchip.com/2023/04/11/llm-engineering.html  
- https://huyenchip.com/2024/07/25/genai-platform.html  
- ../../phase-5/week-20-cost-latency-engineering/01-model-routing.md  
- ../week-26-fine-tuning/01-rag-vs-fine-tuning-decision.md  
