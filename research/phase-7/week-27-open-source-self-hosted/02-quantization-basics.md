# 02 — Quantization basics

> Week 27 — Open-source and self-hosted models  
> Research notes (raw). Why a **70B** model can fit on **one GPU** after quantization — and what you lose.

---

## Fundamentals

**Quantization** stores (and sometimes computes) weights — and optionally activations — at lower numeric precision than the training dtype (typically FP16/BF16). Memory for parameters scales roughly with bits per weight:

| Format | Bits / weight (approx) | 70B weight memory (order of magnitude) |
|--------|------------------------|----------------------------------------|
| FP16 / BF16 | 16 | ~140 GB |
| INT8 / FP8 | 8 | ~70 GB |
| INT4 (GPTQ/AWQ/GGUF Q4) | ~4 (+ scales/zeros overhead) | ~35 GB + overhead |

A single **80 GB** datacenter GPU (e.g. A100/H100 80GB) cannot hold 70B in BF16 weights alone, and **KV cache** for long context still needs headroom. **4-bit weight-only** quantization brings weights into a range where **one 40–80 GB GPU** can load a 70B-class model and still serve modest batch/context — the syllabus “why 70B fits on one GPU after quantization.”

Two widely cited post-training methods:

- **GPTQ** — layer-wise post-training quantization minimizing output error (Hessian / OBQ-style); arXiv:2210.17323.  
- **AWQ** — activation-aware weight quantization; protects salient weights using activation magnitude; arXiv:2306.00978.

**GGUF / llama.cpp / Ollama** use related low-bit schemes (Q4_K_M, Q5_K_M, etc.) optimized for local CPU/GPU runtimes. **vLLM** documents AWQ, GPTQ, FP8, and other formats for server deployment.

**What you lose (always measure):**

1. **Quality** — perplexity / task accuracy; sensitive tasks (math, precise JSON, rare languages) degrade first.  
2. **Calibration dependence** — bad calibration set → silent regressions.  
3. **Kernel / hardware lock-in** — not every GPU supports every path equally (see vLLM quantization hardware tables).  
4. **Training story** — inference quant ≠ QLoRA training quant (Week 26); don’t conflate.

---

## Alternatives & Tradeoffs

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

---

## Necessity

Without quantization literacy:

- Capacity plans quote 4× A100s for a workload that fits one GPU at INT4 — deal dies on CapEx.  
- Or the opposite: ship Q3 ultra-aggressive quants, miss SLO quality, blame “open source is bad.”  
- Ollama prototypes use Q4; production mistakenly loads BF16 and OOMs at first load test.  
- Week 20 cost models ignore that **quant enables batching headroom**, changing $/query.  
- Week 26 QLoRA discussions confuse training adapters with serving quants.

Quantization is the bridge between model cards (01) and serving tooling (03).

---

## Industry Practice

- **Common:** download the smallest GGUF; skip eval; call it “the 70B.”  
- **Strong:** choose method for target engine (AWQ/GPTQ for vLLM; GGUF for Ollama/llama.cpp); calibrate on domain text; compare BF16 (or official FP8) vs INT4 on **task** metrics; monitor for garbled Unicode / broken tool JSON.  
- **FDE bar:** put VRAM spreadsheet in the design doc (weights + KV + overhead); cite GPTQ/AWQ papers and vLLM quant docs; set a kill criterion (“if format@schema drops &gt; N points vs BF16, use 8-bit or smaller model”).

NVIDIA NIM and Hub cards often publish pre-quantized variants — still verify on *your* eval harness.

---

## Concrete Scenario

**AWQ paper (Activation-aware Weight Quantization):**  
https://arxiv.org/abs/2306.00978  

**GPTQ paper:**  
https://arxiv.org/abs/2210.17323  

**vLLM quantization feature docs:**  
https://docs.vllm.ai/en/stable/features/quantization/  

**Scenario:** Customer offers a single **48 GB** GPU for an internal Llama-3.1-70B assistant. BF16 weights alone are impossible. Plan: serve an **AWQ 4-bit** checkpoint via vLLM; reserve memory budget for 8k context and batch 4; run the Week 20 golden set vs hosted GPT-class route. If legal-clause extraction F1 drops below threshold, fall back to **32B/34B BF16** or **70B INT8** on a larger SKU — don’t silently ship broken INT4.

---

## Open Questions

- Will native FP4 / MXFP hardware make INT4 GPTQ/AWQ obsolete for new clusters?  
- How should KV-cache quantization compose with weight-only AWQ for long-context RAG (Week 25)?  
- Is per-layer mixed precision worth the ops complexity for FDE-led pilots?  
- Do MoE models quantize “for free” on inactive experts, or do serving stacks still materialize too much?  
- When does quality loss from quant exceed loss from switching to a smaller BF16 model?

---

## Sources

- https://arxiv.org/abs/2306.00978  
- https://arxiv.org/pdf/2306.00978  
- https://arxiv.org/abs/2210.17323  
- https://arxiv.org/pdf/2210.17323  
- https://docs.vllm.ai/en/stable/features/quantization/  
- https://huggingface.co/docs/transformers/main/en/quantization/overview  
- https://ollama.com/  
- https://huyenchip.com/2023/04/11/llm-engineering.html  
- ../week-26-fine-tuning/02-lora-qlora-peft.md  
- ../../phase-5/week-20-cost-latency-engineering/README.md  
