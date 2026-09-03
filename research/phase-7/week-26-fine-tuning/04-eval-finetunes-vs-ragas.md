# 04 — Eval for fine-tunes vs RAGAS

> Week 26 — Fine-tuning when RAG isn't enough  
> Research notes (raw).

---

## Fundamentals

**Week 10 RAGAS-style metrics** (faithfulness / groundedness, answer relevance, context precision/recall) evaluate whether a **retrieval+generation** stack uses evidence well. They are the wrong primary scoreboard for a fine-tune whose job is **behavior**: schema validity, tone, classification F1, tool-call shape, or latency-bound rewrite quality.

**Fine-tune eval** centers on:

1. **Task-specific golden sets** — sealed examples with expected structures or labels (from file 03). Score format compliance, exact/soft match, constrained JSON validity, rubric grades (Week 17 LLM-judge only if calibrated).  
2. **Regression vs base** — same prompts on base instruct model vs adapter; require non-regression on general skills you still need.  
3. **Catastrophic forgetting checks** — holdout suites for safety refusals, core reasoning, or other product skills that must survive PEFT.  
4. **Hybrid split** — if RAG remains for facts, keep **RAGAS on the RAG path** and **task metrics on the FT path**; don’t average them into one vanity number.

| Question | Metric family |
|----------|---------------|
| Did retrieval get the right docs? | P@k, R@k, MRR, NDCG (Week 10) |
| Did the answer stick to context? | RAGAS faithfulness / groundedness |
| Did FT learn the template/voice? | Schema pass rate, rubric, pairwise win rate |
| Did FT break the base model? | Forgetting suite delta vs base checkpoint |
| Is the system shippable? | Gate: task metric ↑ AND forgetting within budget AND (if RAG) faithfulness ≥ floor |

Training loss and vendor “validation loss” are **not** product acceptance.

**Attribution rule (ties to Week 16):** when a hybrid system fails, slice first — retrieval miss (Week 9/10) vs generator format miss (FT/prompt) vs packing/context failure (Week 25). Only then decide whether to collect more instruction data, raise LoRA rank, or fix the index.

---

## Alternatives & Tradeoffs

| Eval approach | Pros | Cons |
|---------------|------|------|
| Vibes / chat demo | Fast | Non-reproducible; ships regressions |
| RAGAS only | Great for Phase 2 | Misses format FT gains; punishes non-RAG answers |
| **Task golden + forgetting suite** | Matches FT intent | Needs SME labels; maintenance |
| LLM-as-judge only | Scales | Judge bias (Huyen pitfalls; Week 17) |
| Online A/B | Real utility | Slow; needs guardrails first |
| Benchmarks (MMLU etc.) | Comparable | Contamination risk; weak product link |

| Gate design | Tradeoff |
|-------------|----------|
| Strict schema 99% | May reject useful paraphrases |
| Soft rubric | Needs IAA / judge calibration |
| Combined hybrid gates | More honest; more CI cost |

Tradeoff: optimizing only task golden sets can destroy helpful base behaviors — hence forgetting checks as a **first-class** gate, not a nice-to-have.

Practical CI shape: one workflow for **adapter candidates** (task + forgetting), one for **index/prompt candidates** (RAGAS + IR@k). Sharing a single flaky notebook for both is how regressions slip.

---

## Necessity

Without FT-aware eval:

- Teams declare victory because RAGAS faithfulness rose after they stuffed more docs into prompts — while the LoRA never helped.  
- Or they ship an adapter that nails JSON but starts leaking PII / weakening refusals.  
- Week 16 error analysis attributes failures to “model quality” without slicing **retrieval vs behavior**.  
- Decision memos lack kill criteria (“kill FT if format@golden < X or forgetting delta > Y”).  
- Vendor FT jobs look “green” on loss while product schema tests fail.

Eval is how Week 26 connects to Week 10 without confusing the two scoreboards.

---

## Industry Practice

- **Common:** one Excel of 20 prompts; before/after screenshots; no base regression.  
- **Strong:** versioned golden JSONL; CI job runs base vs adapter; separate RAGAS job for retrieval builds; forgetting suite tagged by capability; contamination audit when adding train data.  
- **FDE bar:** present two dashboards in the memo — **Behavior** and **Grounding** — and state which one FT is allowed to move; cite RAGAS docs for the grounding board and task metrics for the behavior board.

RAGAS docs: https://docs.ragas.io/  
Week 10 corpus in this KB for retrieval metric detail.

---

## Concrete Scenario

**RAGAS documentation (generation metrics for RAG stacks):**  
https://docs.ragas.io/  

A claims-ops copilot uses RAG over policy PDFs (Phase 2) and a LoRA for **fixed denial-letter structure**. Eval plan: (a) Week 10 RAGAS faithfulness/context precision on policy answers with retrieval on; (b) letter **schema pass rate** + SME rubric on 150 golden letters with retrieval off or with frozen distractor contexts; (c) forgetting suite of 50 general support prompts + safety items comparing base vs adapter. Ship only if (b) clears kill threshold without (a) or (c) regressing beyond agreed floors. OpenAI’s fine-tuning guide’s emphasis on evaluation after jobs aligns with treating loss as insufficient:  
https://platform.openai.com/docs/guides/fine-tuning  

---

## Open Questions

- Best standard forgetting suites for enterprise PEFT (safety + general instruction)?  
- Can one LLM judge reliably score both groundedness and brand voice?  
- How to eval merged quantized GGUF vs fp16 adapter fairly?  
- Should RAFT-trained models use modified RAGAS that expects distractor resistance?  
- Continuous eval from prod — when to promote traces into golden without contamination?

---

## Sources

- https://docs.ragas.io/  
- https://docs.ragas.io/en/latest/concepts/metrics/available_metrics/  
- https://platform.openai.com/docs/guides/fine-tuning  
- https://huyenchip.com/2025/01/16/ai-engineering-pitfalls.html  
- https://huyenchip.com/2023/04/11/llm-engineering.html  
- ../../phase-2/week-10-rag-evaluation/README.md  
- ../../phase-4/week-16-error-analysis-flywheel/README.md  
- ../../phase-4/week-17-llm-judge-observability/README.md  
- https://arxiv.org/abs/2305.14314  
- https://huggingface.co/docs/trl/en/sft_trainer  
