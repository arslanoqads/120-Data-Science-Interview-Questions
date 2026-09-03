# 05 — Air-gapped deployment considerations

> Week 27 — Open-source and self-hosted models  
> Research notes (raw). When the model, eval harness, and updates must survive **without internet**.

---

## Fundamentals

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

Week 19 residency asks *where* data lives; air-gap asks whether **any path** to the public model provider exists. Answer carefully on questionnaires.

---

## Alternatives & Tradeoffs

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

---

## Necessity

Without air-gap design:

- Pilots depend on `ollama pull` and die on the customer’s disconnected VLAN.  
- Security rejects the design for undeclared egress to Hugging Face or Docker Hub.  
- Model updates become heroics; nobody owns the promotion checklist.  
- Week 26 FT datasets cannot be refreshed; adapters drift from frozen bases.  
- Incident response cannot fetch mitigations; playbooks assume GitHub access.

Air-gap is where Week 27 stops being optional for FDEs in defense, critical infrastructure, and some public sector.

---

## Industry Practice

- **Common:** copy a laptop Ollama models directory; hope drivers match; no SBOM.  
- **Strong:** private mirror of approved weights + containers; SBOM; checksum verification; staged promote (lab → pre-prod → air-gap); offline eval gate; documented rollback to previous weight hash.  
- **FDE / senior:** map questionnaire language (air-gap vs private network vs residency); propose diode workflow; cite model cards for license; pair with Week 19 auth so only service accounts hit internal vLLM; never promise “same day” model upgrades.

NVIDIA NIM documentation includes enterprise deployment guidance — useful when the customer standardizes on NVIDIA stacks **inside** the boundary; still plan artifact import.

---

## Concrete Scenario

**Google Gemma docs (open weights for on-device / controlled deploy):**  
https://ai.google.dev/gemma/docs  

**Meta Llama downloads / license flow (connected side):**  
https://www.llama.com/  

**Data residency neighbor (this KB):**  
../../phase-5/week-19-auth-identity-enterprise/04-data-residency.md  

**Scenario:** A national lab forbids egress. FDE builds on a connected lab cluster: quantize Llama-3.1-8B-Instruct AWQ, bake a vLLM container pinned by digest, run golden-set eval, sign the bundle. Transfer via approved media; verify checksums; deploy to internal k8s with no `ImagePull` from the public internet. Quarterly update window: repeat eval; if quality regresses, keep previous digest. Hosted API is **not** a failover — UX must degrade gracefully with local-only models (tie to Week 20 router policy `failover=none`).

---

## Open Questions

- Can confidential GPUs + attested serving replace classic air-gap for some auditors?  
- How do you run LLM-as-judge eval offline without a second large model’s VRAM?  
- What’s the minimum SBOM + attestation story buyers will accept for GGUF/AWQ artifacts?  
- Do sovereign clouds reduce true air-gap demand over the next product cycles?  
- How should CVE response work when CUDA/vLLM patches cannot `apt update` freely?

---

## Sources

- https://ai.google.dev/gemma/docs  
- https://www.llama.com/  
- https://github.com/meta-llama/llama-models  
- https://qwen.readthedocs.io/en/latest/  
- https://docs.vllm.ai/en/latest/  
- https://ollama.com/  
- https://docs.nvidia.com/nim/index.html  
- https://huyenchip.com/2024/07/25/genai-platform.html  
- ../../phase-5/week-19-auth-identity-enterprise/04-data-residency.md  
- ../../phase-5/week-19-auth-identity-enterprise/README.md  
- ../../phase-5/week-20-cost-latency-engineering/01-model-routing.md  
- ../week-26-fine-tuning/05-cost-maintenance-finetunes.md  
