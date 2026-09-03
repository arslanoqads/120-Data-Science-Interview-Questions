# 04 — Self-hosted vs API cost / latency / control tradeoffs

> Week 27 — Open-source and self-hosted models  
> Research notes (raw). Extends **Week 20** cost/latency engineering with an on-prem / VPC OSS option.

---

## Fundamentals

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

---

## Alternatives & Tradeoffs

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

---

## Necessity

Without this tradeoff analysis:

- Finance cannot approve GPU CapEx or API commit discounts with a straight face.  
- FDEs cannot answer “what if customer can’t use hosted API?” except with vibes.  
- Routers send everything local “for privacy” and destroy UX latency.  
- Week 19 residency wins the deal, then Week 20 unit economics lose the renewal.  
- Interviews fail the classic “build vs buy inference” question.

This file is the economic and product bridge between tooling (03) and air-gap constraints (05).

---

## Industry Practice

- **Common:** slide with “80% cheaper with Llama” using peak API list price vs fully loaded GPU at 100% util.  
- **Strong:** measure on a golden set — **latency, quality, cost** — for API route vs Ollama/vLLM route; publish the table; set router thresholds.  
- **FDE bar:** hybrid design with explicit **failover** (local down → approved regional API or graceful degrade); cite Huyen on system costs beyond model fees; reuse Week 20 dashboards for both providers.

NVIDIA NIM blogs/docs often frame TCO for optimized self/managed inference — use as vendor input, still run *your* numbers.

---

## Concrete Scenario

**Chip Huyen — Building LLM applications for production (cost of different levers):**  
https://huyenchip.com/2023/04/11/llm-engineering.html  

**Week 20 routing corpus (this KB):**  
../../phase-5/week-20-cost-latency-engineering/01-model-routing.md  

**Scenario (syllabus build):** Extend the Week 20 router so `tenant.residency == "on_prem"` or `task == "faq_macro"` goes to `ollama/llama3.1:8b-instruct-q4_K_M`. Run 500 golden prompts: record TTFT p50/p95, task accuracy, and $/1k requests (API invoice vs amortized GPU hour / throughput). Deliver a one-pager: “If the customer cannot use a hosted API, route X% locally with quality delta Δ and latency delta Δ; escalate only Y.” That is the FDE answer — not “buy more GPUs” or “refuse the RFP.”

---

## Open Questions

- How should carbon / power enter enterprise TCO sheets next to token $$?  
- Do prompt-cache discounts on APIs permanently shift break-evens against self-host?  
- Spot/preemptible GPUs: acceptable for async eval but not interactive?  
- Should quality-normalized $ (Week 20 cascading) always beat raw $?  
- Who funds the “idle HA GPU” — platform tax or per-tenant chargeback?

---

## Sources

- https://huyenchip.com/2023/04/11/llm-engineering.html  
- https://huyenchip.com/2024/07/25/genai-platform.html  
- https://huyenchip.com/2025/01/16/ai-engineering-pitfalls.html  
- https://docs.vllm.ai/en/latest/  
- https://ollama.com/  
- https://developer.nvidia.com/blog/  
- https://docs.nvidia.com/nim/index.html  
- ../../phase-5/week-20-cost-latency-engineering/README.md  
- ../../phase-5/week-20-cost-latency-engineering/01-model-routing.md  
- ../../phase-5/week-20-cost-latency-engineering/05-cost-attribution-dashboards.md  
- ../../phase-5/week-19-auth-identity-enterprise/04-data-residency.md  
