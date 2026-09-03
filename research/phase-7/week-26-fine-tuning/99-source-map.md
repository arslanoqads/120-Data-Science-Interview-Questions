# 99 — Week 26 master source map

> Consolidated index of official docs, engineering blogs, papers, talks. Legal sources only.  
> Phase 7 elective — Fine-tuning when RAG isn't enough.

Fetched / verified via WebSearch & WebFetch during corpus authoring (2026-09-03).

---

## OpenAI — fine-tuning

| Topic | URL |
|-------|-----|
| Fine-tuning guide | https://platform.openai.com/docs/guides/fine-tuning |
| API pricing (cost memos) | https://openai.com/api/pricing/ |

---

## AWS Bedrock — custom models / fine-tuning

| Topic | URL |
|-------|-----|
| Customize a model with fine-tuning | https://docs.aws.amazon.com/bedrock/latest/userguide/custom-model-fine-tuning.html |
| Prepare data for fine-tuning | https://docs.aws.amazon.com/bedrock/latest/userguide/model-customization-prepare.html |
| Submit customization job | https://docs.aws.amazon.com/bedrock/latest/userguide/model-customization-submit.html |
| Provisioned throughput (hosting) | https://docs.aws.amazon.com/bedrock/latest/userguide/prov-thru.html |

---

## Hugging Face — PEFT / TRL / Unsloth

| Topic | URL |
|-------|-----|
| PEFT index | https://huggingface.co/docs/peft/index |
| LoRA conceptual guide | https://huggingface.co/docs/peft/main/en/conceptual_guides/lora |
| TRL SFTTrainer | https://huggingface.co/docs/trl/en/sft_trainer |
| TRL DPO trainer | https://huggingface.co/docs/trl/en/dpo_trainer |
| TRL ↔ Unsloth integration | https://huggingface.co/docs/trl/en/unsloth_integration |
| Unsloth docs | https://docs.unsloth.ai/ |
| Unsloth GitHub | https://github.com/unslothai/unsloth |

---

## Papers — LoRA / QLoRA

| Topic | URL |
|-------|-----|
| Hu et al. **LoRA** arXiv:2106.09685 | https://arxiv.org/abs/2106.09685 |
| LoRA PDF | https://arxiv.org/pdf/2106.09685 |
| Dettmers et al. **QLoRA** arXiv:2305.14314 | https://arxiv.org/abs/2305.14314 |
| QLoRA PDF | https://arxiv.org/pdf/2305.14314 |

---

## Chip Huyen — public blogs (no pirate PDFs)

| Topic | URL |
|-------|-----|
| Building LLM applications for production (prompting vs finetuning, cost) | https://huyenchip.com/2023/04/11/llm-engineering.html |
| Building a Generative AI Platform (context / RAG architecture) | https://huyenchip.com/2024/07/25/genai-platform.html |
| Common pitfalls (don’t insist on finetuning when prompting works) | https://huyenchip.com/2025/01/16/ai-engineering-pitfalls.html |
| Agents | https://huyenchip.com/2025/01/07/agents.html |
| Open challenges (RAG context) | https://huyenchip.com/2023/08/16/llm-research-open-challenges.html |

---

## RAG eval — RAGAS & related (contrast with FT eval)

| Topic | URL |
|-------|-----|
| RAGAS docs | https://docs.ragas.io/ |
| RAGAS available metrics | https://docs.ragas.io/en/latest/concepts/metrics/available_metrics/ |
| Week 10 corpus (this KB) | ../../phase-2/week-10-rag-evaluation/README.md |

---

## Anthropic — agents / context (boundary with FT)

| Topic | URL |
|-------|-----|
| Effective context engineering for AI agents | https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents |
| Building effective agents | https://www.anthropic.com/engineering/building-effective-agents |

*Note:* Prefer Anthropic engineering posts for **context and prompting** boundaries with FT. Managed FT availability varies: e.g. Bedrock lists Anthropic Claude 3 Haiku among customizable models — always verify current regional/model tables before promising Claude FT in a customer memo. Open-weight PEFT remains the portable teaching path.

---

## Talks / YouTube (PEFT / fine-tuning education)

| Topic | URL |
|-------|-----|
| Hugging Face — PEFT / fine-tuning sessions (HF YouTube org) | https://www.youtube.com/@HuggingFace |
| LoRA paper page (abs) for reading groups | https://arxiv.org/abs/2106.09685 |

---

## Cross-links inside this KB

| Related week | Why |
|--------------|-----|
| Phase 2 Weeks 6–9 — RAG | Ingestion, retrieval, failure taxonomy — exhaust before FT |
| Week 10 — RAG evaluation | RAGAS / IR metrics vs FT task golden sets |
| Week 5 — prompt engineering | Prefer prompts before FT (Huyen pitfalls) |
| Week 20 — cost / latency | Token savings vs train/host; payback math |
| Week 16–17 — error analysis / judges | Slices for behavior vs grounding; calibrated judges |
| Week 25 — context engineering | Packing vs weight updates; don’t confuse levers |
| Week 18 — deployment | Serving adapters / custom models |

---

## Source policy reminder

Allowed: official docs (HF PEFT/TRL, Unsloth, OpenAI, Anthropic, AWS Bedrock FT), Chip Huyen **public blogs only**, arXiv (LoRA, QLoRA), conference talks/YouTube.  
Not used: pirate book/PDF sites or unauthorized copyrighted book text.
