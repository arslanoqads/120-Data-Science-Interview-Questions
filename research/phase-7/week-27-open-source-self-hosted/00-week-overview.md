# 00 — Week overview & syllabus mapping

> Week 27 — Open-source and self-hosted models  
> Phase 7 elective (supplementary). Suggested after Week 20; pairs with Week 19 residency.  
> Research notes (raw).

---

## Fundamentals

Week 27 treats **open-weight models + self-hosted inference** as a first-class FDE capability — not a hobbyist side quest. An FDE who can only call hosted APIs is stuck when the customer requires **data residency**, **air-gap**, **unit-cost at high QPS**, or **procurement** that forbids third-party LLM SaaS. The syllabus trio — **Ollama**, **vLLM**, **quantization** — is the practical stack: pull a quantized Llama/Qwen/Gemma, serve it locally, then harden serving for production.

| Lever | What you control | Typical week |
|-------|------------------|--------------|
| Hosted API (OpenAI / Anthropic / Bedrock) | Prompt, tools, routing | Weeks 5, 18–20 |
| **Open weights + self-host** | Weights location, hardware, quant, serving stack | **Week 27 (this elective)** |
| PEFT on open weights | Task behavior on *your* GPU | Week 26 |

Syllabus concepts map to files 01–05: **landscape & task eval** → **quantization** → **Ollama vs vLLM** → **cost/latency/control vs API** → **air-gap**. The **build** (documented only here) adds a self-hosted leg to the **Week 20 router** and forces a measured comparison.

**Suggested placement:** fold into Week 20 model routing, or stand alone immediately after it. Read Week 19 residency first when the driver is compliance. Week 26 fine-tuning is optional follow-on once the base OSS model is chosen and served.

---

## Alternatives & Tradeoffs

| Path | What you optimize | What you sacrifice |
|------|-------------------|-------------------|
| Hosted API only | Time-to-demo; frontier quality | Stuck on residency / air-gap / some unit economics |
| Self-host frontier-class OSS only | Control + residency | Ops burden; may lag closed frontier on hard tasks |
| **Hybrid router** (Week 20 + this week) | Right tool per request | Two serving paths to observe and eval |
| Managed OSS (Bedrock / Vertex / NIM) | Less DIY ops | Still cloud; may not satisfy true air-gap |
| Distilled / small local only | Cheap edge latency | Narrow quality; more routing logic |

| Build scope | Pros | Cons |
|-------------|------|------|
| Ollama demo only | Fast “it runs on my laptop” | No production SLOs; no Week 20 comparison |
| **Self-hosted router leg + comparison memo** (syllabus) | Answers “can’t use hosted API” with numbers | Needs GPU or shared lab box |
| Full multi-node vLLM fleet first | Impressive | Premature before task eval + quant plan |

---

## Necessity

Concrete failure modes if Week 27 is skipped:

- Sales promises “we’ll put Llama in your VPC” with no quantization plan — 70B BF16 does not fit the customer’s single A10.  
- FDEs refuse deals that require on-prem inference because the curriculum never left `api.openai.com`.  
- Teams ship Ollama in production and discover no continuous batching, weak multi-tenant isolation, and opaque metrics.  
- Cost reviews (Week 20) never compare **amortized GPU + power** vs **API tokens** at the customer’s QPS.  
- Air-gap RFPs fail when weight transfer, offline eval, and update cadence were never designed (Week 19 residency incomplete).

Without this week, “open source” stays a slide. With it, self-host is a **routable, measurable** product path.

---

## Industry Practice

- **Common (demo AI):** `ollama run llama3` on a laptop; declare “on-prem ready”; no golden-set parity vs GPT-4-class routes; ignore license Acceptable Use.  
- **Strong:** task-driven model shortlist (Llama / Qwen / Gemma); quantize with AWQ/GPTQ or vendor GGUF; prototype Ollama → serve vLLM/NIM; router sends residency-sensitive traffic local; dashboards for GPU util + quality regression.  
- **FDE bar:** answer the questionnaire *and* the unit-econ sheet; cite model cards and serving docs; keep a kill criterion (“if local quality &lt; X on golden set, escalate to approved regional API or refuse the slice”).

Production references: Meta Llama model cards; Qwen docs; Google Gemma; Ollama docs; vLLM docs; Hugging Face Hub; AWQ/GPTQ papers; NVIDIA NIM; Chip Huyen production blogs.

---

## Concrete Scenario

**vLLM documentation — high-throughput serving:**  
https://docs.vllm.ai/en/latest/  

vLLM positions itself as a production inference engine (PagedAttention, continuous batching, OpenAI-compatible API). Pair with Ollama’s developer-oriented local runner for the prototype phase:  
https://ollama.com/  

The elective’s artifact mirrors strong FDE practice: a **Week 20 router route** to a local OSS model plus a **short latency / quality / cost comparison** — not a vague “we support open source” checkbox.

---

## Open Questions

- Will regional hosted APIs + ZDR retire most “must self-host” asks, or will true air-gap and sovereignty keep DIY serving mandatory?  
- How often must OSS bases be **rebased** when Meta/Qwen/Google ship new families (ops tax vs Week 26 adapters)?  
- When does NIM / managed open-weight hosting beat raw vLLM for enterprise FDEs?  
- Can small on-device Gemma/Llama variants own edge paths while datacenter vLLM owns batch?  
- Who owns GPU capacity planning — customer infra, FDE embedding team, or a shared ML platform?

---

## Sources

- https://docs.vllm.ai/en/latest/  
- https://ollama.com/  
- https://www.llama.com/  
- https://github.com/meta-llama/llama-models  
- https://qwen.readthedocs.io/en/latest/  
- https://ai.google.dev/gemma  
- https://huyenchip.com/2023/04/11/llm-engineering.html  
- https://huyenchip.com/2024/07/25/genai-platform.html  
- ../../phase-5/week-20-cost-latency-engineering/README.md  
- ../../phase-5/week-19-auth-identity-enterprise/04-data-residency.md  
- ../week-26-fine-tuning/README.md  
