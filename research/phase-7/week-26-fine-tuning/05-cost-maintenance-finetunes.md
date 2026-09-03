# 05 — Cost and maintenance of fine-tunes

> Week 26 — Fine-tuning when RAG isn't enough  
> Research notes (raw).

---

## Fundamentals

Fine-tuning shifts spend from **per-request prompt tokens** to **upfront training + ongoing hosting + retrain ops**. Chip Huyen’s production essay frames the prompting-vs-finetuning cost trade: baking instructions into weights can remove thousands of prompt tokens per call — material at high QPS — but only after you pay for data, training, and evaluation (*Building LLM applications for production*).

**Cost stack:**

| Layer | Examples |
|-------|----------|
| **Training** | GPU hours (LoRA/QLoRA), or OpenAI/Bedrock job fees; engineer time for configs |
| **Labeling** | Often dominates (file 03) |
| **Hosting** | Dedicated endpoint, provisioned throughput (Bedrock), GPU replica for merged model, or adapter+base memory |
| **Versioning** | Artifact registry: `base_revision + adapter_id + dataset_hash + eval_report` |
| **Drift / rebase** | When the **base model** updates, adapters may need retrain; prompts/RAG indexes usually port cheaper |
| **Eval CI** | Golden + forgetting suites on every candidate (file 04) |

**Ops burden vs prompt/RAG changes:** changing a system prompt or re-indexing is typically a deploy measured in minutes–hours. Shipping a new FT is a **model release**: train, eval gates, canary, rollback. That burden is justified when file 01’s FT-win conditions hold at scale; otherwise Week 20 cost engineering should prefer caching, shorter prompts, better retrieval, or smaller models without FT.

**Payback sketch for the decision memo:**  
`monthly_savings ≈ calls/month × tokens_removed_per_call × $/token`  
`payback_months ≈ (labeling + train + eval_eng + host_delta) / monthly_savings`  
If payback exceeds the expected life of the base model revision (or voice churn cycle), kill FT.

---

## Alternatives & Tradeoffs

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

---

## Necessity

Ignoring maintenance produces:

- Shadow IT LoRAs with no owner after the hackathon.  
- Production pinned to an old base because rebase risk is unknown — security patches delayed.  
- Cost dashboards that show “LLM $ down” while hidden GPU serving $ and labeling retainers soar.  
- Customers surprised that “we fine-tuned once” does not track their weekly policy corpus (RAG still required).  
- FDEs unable to write kill criteria tied to **payback period** (Week 20): train_cost / (token_savings_per_call × calls).

Maintenance is why the syllabus build is a **memo**, not a toy train — the memo must price the life cycle.

---

## Industry Practice

- **Common:** one successful job → forever endpoint; no adapter inventory; base upgrades ignored.  
- **Strong:** model card per adapter; scheduled eval against golden; rebase policy (“within N weeks of base release”); cost alarms on training accounts; compare to prompt+RAG baseline monthly.  
- **FDE bar:** put train + host + rebase + labeling in the decision memo; cite Bedrock throughput / OpenAI usage pricing pages as inputs; recommend RAG for churning facts to avoid retrain tax.

Bedrock fine-tuning + provisioned throughput for custom models is a typical enterprise ops shape:  
https://docs.aws.amazon.com/bedrock/latest/userguide/custom-model-fine-tuning.html  

---

## Concrete Scenario

**OpenAI fine-tuning guide (productized training jobs + ongoing use):**  
https://platform.openai.com/docs/guides/fine-tuning  

An e-commerce company burns ~1.5k tokens/call on style exemplars for product-description rewrites at 20M calls/month. Memo math (Week 20 style): if FT removes ~1k tokens/call at published token prices, monthly savings dwarf a managed fine-tune job — **but** only if (a) descriptions don’t require citeable inventory facts (those stay RAG), (b) labeling 1k gold examples is funded, and (c) kill criteria fire when a new base model ships and rebase + eval exceed one quarter of savings. Chip Huyen’s cost framing:  
https://huyenchip.com/2023/04/11/llm-engineering.html  

If traffic is low or voice changes weekly, the memo should **kill FT** and keep prompts.

---

## Open Questions

- Standardized adapter rebase SLAs when closed vendors deprecate base models?  
- Multi-tenant adapter routing — cost of hot-swap vs merged replicas?  
- Carbon / energy reporting for FT vs long-context RAG at equal quality?  
- When does batch distillation beat keeping a large base + LoRA?  
- How to charge customers for FT in services businesses — T&M labeling vs outcome-based?

---

## Sources

- https://platform.openai.com/docs/guides/fine-tuning  
- https://openai.com/api/pricing/  
- https://docs.aws.amazon.com/bedrock/latest/userguide/custom-model-fine-tuning.html  
- https://docs.aws.amazon.com/bedrock/latest/userguide/prov-thru.html  
- https://huyenchip.com/2023/04/11/llm-engineering.html  
- https://huyenchip.com/2024/07/25/genai-platform.html  
- https://huyenchip.com/2025/01/16/ai-engineering-pitfalls.html  
- https://huggingface.co/docs/peft/index  
- ../../phase-5/week-20-cost-latency-engineering/README.md  
- ../../phase-2/week-10-rag-evaluation/README.md  
- 01-rag-vs-fine-tuning-decision.md  
- 04-eval-finetunes-vs-ragas.md  
