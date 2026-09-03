# 01 — RAG vs fine-tuning decision framework

> Week 26 — Fine-tuning when RAG isn't enough  
> Research notes (raw).

---

## Fundamentals

**RAG** retrieves evidence at inference and packs it into context (Phase 2). **Fine-tuning** updates model parameters (often a small adapter) so desired behavior is internalized. They answer different failure modes:

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

Hybrid is common: LoRA for form, RAG for facts (same product, two levers).

---

## Alternatives & Tradeoffs

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

Tradeoff inside “FT for knowledge”: baking docs into weights **looks** like learning but creates silent staleness — the kill criterion for most knowledge-FT proposals.

---

## Necessity

Without an explicit framework:

- FDEs inherit a customer mandate “fine-tune our Llama on SharePoint” when Week 6–8 ingestion/retrieval would move the needle.  
- Cost reviews (Week 20) never compare **$/1k calls with 2k-token exemplars** vs **amortized train + short prompts**.  
- Security/compliance asks for citations; FT-only answers cannot show passages.  
- Air-gapped teams over-index on RAG patterns copied from SaaS blogs that assume network.  
- Interviews cannot explain *why* Predibase-style small tuned models beat frontier models on **narrow** tasks while losing on open-domain factuality.

The decision framework is the gate before PEFT notebooks (file 02) and before GPU spend (file 05).

---

## Industry Practice

- **Common:** binary slogan (“RAG is dead” / “always fine-tune”) driven by vendor demos.  
- **Strong:** failure taxonomy → lever map; A/B prompt+RAG vs FT candidate on the **same golden set**; hybrid when both behavior and knowledge fail; document kill criteria in the design memo.  
- **FDE / senior:** force the customer to state whether success is measured by **groundedness/citation** (Week 10) or **format accuracy/latency**; refuse FT-as-knowledge-base; cite OpenAI/Bedrock “customize for task” docs and Huyen’s prompting-vs-finetuning cost arithmetic.

Managed paths: OpenAI fine-tuning jobs; Amazon Bedrock `CreateModelCustomizationJob`; open-weight PEFT when air-gap or unit-cost demands local serving.

---

## Concrete Scenario

**Stripe-style support assistant (hypothetical product memo using real vendor docs as constraints):**

Product needs (1) answers grounded in **changing** help-center articles with URLs in the reply, and (2) a **fixed** apology + escalation JSON schema in the brand voice. OpenAI’s fine-tuning guide frames FT for reliable format/tone after prompting plateaus:  
https://platform.openai.com/docs/guides/fine-tuning  

Decision: **RAG wins** for article truth and citations (Phase 2 + Week 10 faithfulness). **FT/PEFT wins** only for the schema/voice head if few-shots still fail format accuracy at volume — not for storing the help center. Kill FT if a 500-example style set doesn’t beat prompt+RAG on format@schema while RAGAS faithfulness drops on the factual slice.

---

## Open Questions

- Is “domain language” actually FT, or better solved by glossary RAG + constrained decoding?  
- When does continued pretraining on domain corpora beat instruction FT for jargon?  
- Do agent tool policies belong in FT weights or in Week 25 context packs?  
- How to score hybrid systems without double-counting RAGAS and format metrics?  
- Will vendor “preference fine-tunes” blur the RAG-vs-FT line by encoding retrieval-use behavior?

---

## Sources

- https://platform.openai.com/docs/guides/fine-tuning  
- https://docs.aws.amazon.com/bedrock/latest/userguide/custom-model-fine-tuning.html  
- https://huyenchip.com/2023/04/11/llm-engineering.html  
- https://huyenchip.com/2025/01/16/ai-engineering-pitfalls.html  
- https://huyenchip.com/2024/07/25/genai-platform.html  
- https://docs.ragas.io/  
- ../../phase-2/week-10-rag-evaluation/README.md  
- ../../phase-2/week-09-rag-failure-taxonomy/README.md  
- ../../phase-5/week-20-cost-latency-engineering/README.md  
- ../week-25-context-engineering/README.md  
