# 00 — Week overview & syllabus mapping

> Week 26 — Fine-tuning when RAG isn't enough  
> Phase 7 elective (supplementary). Suggested after Phase 2 + Week 20.  
> Research notes (raw).

---

## Fundamentals

Week 26 treats **fine-tuning (FT)** as a deliberate escalation after Phase 2 RAG and Week 5 prompting — not as the default “make the model smarter” move. RAG changes **what facts** land in the window at inference. Fine-tuning changes **weights** so the model’s default **behavior**, **format**, **domain phrasing**, or **fixed skill** shifts without stuffing that behavior into every prompt.

OpenAI’s product guidance and Chip Huyen’s production writing converge: fine-tuning is strongest for **style, format, and instruction-following reliability**; retrieval is stronger for **current or proprietary facts** you must cite or update without a training run (*Building LLM applications for production*; OpenAI fine-tuning guide).

| Lever | What moves | Cadence of change | Typical week |
|-------|------------|-------------------|--------------|
| Prompt engineering | Instructions in the request | Git commit | Week 5 |
| RAG / context packing | Evidence tokens at inference | Index update | Weeks 6–10, 25 |
| **Fine-tuning / PEFT** | Adapter or full weights | Training job + eval gate | **Week 26 (this elective)** |

Syllabus concepts map to files 01–05: **decision framework** → **LoRA/QLoRA/PEFT mechanics** → **datasets** → **eval vs RAGAS** → **cost/maintenance**. The **build** is a written **decision memo** with criteria, risks, and kill criteria — not a toy LoRA.

**Suggested placement:** after Week 10 (RAG eval) so students can prove RAG plateaued; after Week 20 so they can price FT vs prompt length and retrieval latency. Alternatively append after Week 24. It does **not** replace Weeks 1–24 or Phase 2 RAG.

---

## Alternatives & Tradeoffs

| Path | What you optimize | What you sacrifice |
|------|-------------------|-------------------|
| Stay on prompt + RAG forever | Fast iteration, citeable answers | May never hit strict format/latency/air-gap SLOs |
| Jump to full FT first | “We customized the model” narrative | Wasted GPU; stale facts; wrong owner for retrieval bugs |
| **PEFT after measured plateau** (this week) | Behavior gains with small adapters | Need data + eval harness + hosting story |
| Distill / smaller specialist model | Cheap high-QPS fixed skills | Narrower capability; more ML ops |
| Hybrid: LoRA for form + RAG for facts | Best of both when both fail | Two systems to version and eval |

| Build scope | Pros | Cons |
|-------------|------|------|
| Toy LoRA notebook | Hands-on PEFT | Skips the decision; encourages FT cosplay |
| **Decision memo only** (syllabus) | Forces criteria + kill criteria | No GPU artifact this week |
| Memo + later PEFT lab | Complete FDE story | Needs Week 26 memo first |

---

## Necessity

Concrete failure modes if Week 26 is skipped:

- Teams fine-tune to “add the PDF corpus” when Week 7–9 retrieval was the real gap — knowledge freezes at train time and goes stale.  
- Or the opposite: they refuse FT forever while burning tokens on 4k-token format exemplars every call (Week 20 cost story ignored).  
- Air-gapped / offline products get stuck with cloud RAG architectures that cannot run.  
- Evals stay RAGAS-only (Week 10) while FT regressions and **catastrophic forgetting** go unmeasured.  
- No kill criteria: endless LoRA rank sweeps after the product needed better labeling guidelines, not more `r`.

Without this week, “fine-tune” remains a prestige word. With it, FT is a **gated** investment with dataset, eval, and ops owners.

---

## Industry Practice

- **Common (demo AI):** fine-tune on scraped Slack + random PDFs; declare victory on a vibes demo; no holdout; no forgetting suite; host one mega merged checkpoint forever.  
- **Strong:** prompt → RAG → measure (Week 10); residual failures classified as behavior vs knowledge; PEFT (LoRA/QLoRA via PEFT/TRL/Unsloth or vendor FT APIs); small high-quality instruction/preference sets; golden task set + base-model regression; adapter versioning.  
- **FDE bar:** write the memo before the job; cite OpenAI/Bedrock docs for *when* FT helps; name LoRA rank / what freezes; price retrain when the base model upgrades; refuse “FT to replace RAG” for citeable, changing facts.

Production references: OpenAI fine-tuning; Amazon Bedrock model customization; Hugging Face PEFT + TRL; Unsloth; LoRA / QLoRA papers; Chip Huyen public blogs on prompting vs finetuning and complexity pitfalls.

---

## Concrete Scenario

**OpenAI — Fine-tuning guide (platform docs):**  
https://platform.openai.com/docs/guides/fine-tuning  

OpenAI positions fine-tuning for improving performance on specific tasks after prompting (and often retrieval) are insufficient — especially consistent format, tone, and reliable instruction following — while retrieval remains the better tool for supplying up-to-date or large proprietary knowledgebases. Pair with Amazon Bedrock custom fine-tuning for managed enterprise jobs:  
https://docs.aws.amazon.com/bedrock/latest/userguide/custom-model-fine-tuning.html  

The elective’s artifact mirrors how strong FDEs work: a **written go/no-go** for FT on a named product surface, not a Colab that trains once.

---

## Open Questions

- Will long-context + better RAG retire most “domain language” FT, or will format/latency SLOs keep PEFT alive?  
- Preference tuning (DPO/RLHF-class) vs SFT-only — when does the labeling cost justify preference pairs?  
- How often must adapters be **rebased** when vendors ship new base models?  
- Can RAFT / retrieval-aware FT collapse the hybrid stack into one training recipe without losing citeability?  
- Who owns FT in the org — platform ML, product eng, or the FDE embedding with the customer?

---

## Sources

- https://platform.openai.com/docs/guides/fine-tuning  
- https://docs.aws.amazon.com/bedrock/latest/userguide/custom-model-fine-tuning.html  
- https://huyenchip.com/2023/04/11/llm-engineering.html  
- https://huyenchip.com/2024/07/25/genai-platform.html  
- https://huyenchip.com/2025/01/16/ai-engineering-pitfalls.html  
- https://huggingface.co/docs/peft/index  
- https://arxiv.org/abs/2106.09685  
- https://arxiv.org/abs/2305.14314  
- https://docs.ragas.io/  
- ../week-25-context-engineering/README.md  
- ../../phase-2/week-10-rag-evaluation/README.md  
- ../../phase-5/week-20-cost-latency-engineering/README.md  
