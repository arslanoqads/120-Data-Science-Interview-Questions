# 03 — Local inference tooling (Ollama vs vLLM)

> Week 27 — Open-source and self-hosted models  
> Research notes (raw). **Ollama** for prototyping; **vLLM** for production-grade serving.

---

## Fundamentals

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

---

## Alternatives & Tradeoffs

| Path | Pros | Cons |
|------|------|------|
| Ollama only forever | Simple ops story | Weak multi-user scheduling; harder enterprise observability |
| vLLM from day 1 | Prod-shaped | Slower spike; more YAML/CUDA pain in week one |
| **Ollama → vLLM graduate** (recommended) | Fast learning + clear promotion criteria | Two runtimes briefly in flight |
| NIM / managed OSS endpoint | Support + performance recipes | Cost; may not be air-gapped |
| Raw `transformers` generate | Full control | No continuous batching; poor throughput |

| Promotion signal (prototype → vLLM) | |
|-------------------------------------|---|
| Concurrent users &gt; few | Need continuous batching |
| p95 latency SLO written | Need engine metrics + tuning |
| Multi-GPU model | Tensor parallel in server |
| Router must share OpenAI schema | vLLM compatibility layer |

---

## Necessity

Without tooling clarity:

- FDEs demo Ollama and leave customers believing that is the production architecture.  
- Or they start with a multi-node vLLM Helm chart before proving the model wins the task (01).  
- Week 20 routers hard-code OpenAI URLs with no abstraction for `base_url=http://vllm:8000/v1`.  
- Quantized artifacts built for the wrong engine (GGUF vs AWQ) waste calibration time (02).  
- Incidents have no GPU utilization / queue depth dashboards because “it worked on my Mac.”

Tooling choice is how landscape + quantization become a **service**.

---

## Industry Practice

- **Common:** Docker with Ollama on a shared GPU box; no auth; no resource quotas; one model name forever.  
- **Strong:** Ollama (or laptop llama.cpp) for spike; freeze model ID + quant; stand up vLLM with OpenAI-compatible API; put behind the same gateway as hosted providers; scrape Prometheus metrics; canary new weights.  
- **FDE bar:** write promotion criteria in the design doc; cite Ollama docs + vLLM docs; for NVIDIA-centric accounts, evaluate NIM as the supported wrapper around similar open models.

Chip Huyen’s platform writing emphasizes inference as a **platform concern** (batching, caching, routing) — local tooling must graduate into that layer (*Building a Generative AI Platform*).

---

## Concrete Scenario

**Ollama documentation / product:**  
https://ollama.com/  
https://github.com/ollama/ollama  

**vLLM documentation:**  
https://docs.vllm.ai/en/latest/  

**NVIDIA NIM (managed/optimized serving path):**  
https://developer.nvidia.com/nim  
https://docs.nvidia.com/nim/index.html  

**Scenario:** Week 20 router adds `provider=ollama` for PII-tagged tenants during the pilot (`http://127.0.0.1:11434`). After the comparison memo passes, swap the same model family to **vLLM** on the customer’s GPU node (`/v1/chat/completions`) without changing application prompts — only `base_url` and auth. Keep Ollama in CI for smoke tests on CPU/small GPU runners.

---

## Open Questions

- When does Ollama’s evolving server feature set close the gap enough for SMB production?  
- Should FDEs standardize on one OpenAI-compatible gateway (LiteLLM) in front of both Ollama and vLLM?  
- How do structured output / grammar constraints compare across Ollama vs vLLM vs NIM?  
- Multi-LoRA serving (Week 26 adapters) — which engines make “many customer adapters, one base” tractable?  
- Cold-start model load times: how to hide them in k8s with model caches / NIM?

---

## Sources

- https://ollama.com/  
- https://github.com/ollama/ollama  
- https://docs.vllm.ai/en/latest/  
- https://docs.vllm.ai/en/latest/serving/openai_compatible_server.html  
- https://developer.nvidia.com/nim  
- https://docs.nvidia.com/nim/index.html  
- https://huggingface.co/docs/text-generation-inference/index  
- https://huyenchip.com/2024/07/25/genai-platform.html  
- ../../phase-5/week-20-cost-latency-engineering/01-model-routing.md  
- ../../phase-5/week-18-deployment-patterns/README.md  
