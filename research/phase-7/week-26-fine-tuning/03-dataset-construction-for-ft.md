# 03 — Dataset construction for fine-tuning

> Week 26 — Fine-tuning when RAG isn't enough  
> Research notes (raw).

---

## Fundamentals

Fine-tuning quality is mostly **data quality**. PEFT (file 02) only decides *how* gradients land; the dataset decides *what* behavior is reinforced.

**Instruction data (SFT):** triples or chat turns of `{system?, user, assistant}` demonstrating the desired skill — format, tone, tool-call shape, rewrite style. OpenAI and Bedrock fine-tuning flows expect JSONL chat/example records; open-source TRL `SFTTrainer` consumes analogous conversational or text fields.

**Preference data:** pairs (or ranked lists) of completions for the same prompt — chosen vs rejected — for DPO / RLHF-class trainers in TRL. Higher labeling skill and cost; use when SFT stabilizes format but **relative** quality (helpfulness, safety tone) still drifts.

**Quality > quantity:** QLoRA’s public results and broader instruction-tuning practice show small, clean sets beating large noisy scrapes. Chip Huyen notes that annotation guidelines used for human eval can later become finetuning data (*Common pitfalls*) — the guideline *is* the product spec.

| Risk | What it means |
|------|----------------|
| **Contamination** | Train examples overlap eval/golden sets or leak benchmark items → fake gains |
| **Label noise** | Inconsistent schemas/voices teach variance |
| **Proxy mismatch** | Slack dumps ≠ production prompts |
| **License / PII** | Training on data you cannot legally or safely encode into weights |
| **Labeling cost** | Expert hours dominate GPU cost (Week 20 framing) |

Rule of thumb for FDE memos: budget **curation and review** as a first-class line item; treat “we’ll scrape Confluence” as a smell unless filtered into instruction-shaped gold.

**Instruction vs preference (quick chooser):** if failures are “wrong shape / wrong house voice,” start with SFT. If failures are “both answers are on-format but humans prefer A,” invest in preference pairs. Mixing both without a guide produces contradictory gradients.

---

## Alternatives & Tradeoffs

| Data strategy | Upside | Downside |
|---------------|--------|----------|
| Scrape everything | Volume | Noise, PII, contamination, weak skill signal |
| **Hand-authored gold (100s–low 1000s)** | High signal | Slow; needs SMEs |
| Synthetic from frontier model | Scale | Homogenization; teacher biases; still needs human audit |
| Production logs → filtered | Real distribution | Consent, PII, sparse “good” labels |
| Preference pairs | Better ranking behavior | 2–5× labeling cost vs SFT |
| Mix SFT + prefs | Strong stacks | Two pipelines to maintain |

| Contaminaton control | Practice |
|----------------------|----------|
| Hash / near-dup vs golden set | Block train∩eval |
| Hold out by time or account | Avoid leakage from prod traces |
| Document source tiers | SME gold vs synthetic vs logs |

Tradeoff: synthetic expansion without a **style guide** amplifies the teacher’s generic voice — defeating “domain language” FT goals from file 01.

---

## Necessity

Skip dataset discipline and you get:

- Beautiful LoRA loss curves that fail the product golden set.  
- “FT improved MMLU” via contamination while customer schema accuracy flatlines.  
- Legal holds when customer PII is baked into adapters shared across environments.  
- Preference training on uncalibrated pairwise labels → reward hacking / sycophancy.  
- Endless GPU sweeps that were actually **labeling** problems (Huyen: start too complex / insist on finetuning when prompting works — often because data wasn’t ready either).

Dataset construction is where most FT projects should spend calendar attention — not rank search.

---

## Industry Practice

- **Common:** JSONL of random good/bad tickets; no guidelines; eval = “ask the model in chat.”  
- **Strong:** written annotation guide; inter-annotator agreement spot checks; train/val/golden splits with contamination scans; separate slices for format, safety, and (if hybrid) RAG-grounded answers that must **not** be memorized as facts.  
- **FDE bar:** estimate labeling hours in the decision memo; refuse FT until N reviewed examples exist; cite vendor data prep docs (Bedrock prepare data; OpenAI training format); plan preference data only if SFT plateaus.

Bedrock: prepare fine-tuning datasets in the required JSONL shapes before `CreateModelCustomizationJob`. OpenAI: chat-format training files with clear validation split.

---

## Concrete Scenario

**Amazon Bedrock — Customize a model with fine-tuning (data prep is the gate):**  
https://docs.aws.amazon.com/bedrock/latest/userguide/custom-model-fine-tuning.html  

A bank wants “regulator-ready” letter rewrites in a fixed template. The FDE rejects dumping 50k CRM emails. Instead: 800 SME-reviewed instruction examples following a one-page style guide, 200 validation, 150 sealed golden (never trained on), plus a contamination check against the golden strings. Preference pairs (tone too aggressive vs approved) added only after SFT format@template exceeds the kill threshold. Facts about rate changes stay in RAG — not in the JSONL — so letters don’t memorize yesterday’s APR.

Related OpenAI training format expectations:  
https://platform.openai.com/docs/guides/fine-tuning  

---

## Open Questions

- Minimum viable N for PEFT on modern instruct models — task-dependent folklore vs measured curves?  
- How much synthetic data is safe before voice collapse?  
- Should hybrid FT examples include retrieved contexts (RAFT-style) in the train set by default?  
- Automated contamination detection beyond string match (paraphrase leakage)?  
- Who signs off labeling guides in regulated enterprises — compliance or product?

---

## Sources

- https://platform.openai.com/docs/guides/fine-tuning  
- https://docs.aws.amazon.com/bedrock/latest/userguide/custom-model-fine-tuning.html  
- https://docs.aws.amazon.com/bedrock/latest/userguide/model-customization-prepare.html  
- https://huggingface.co/docs/trl/en/sft_trainer  
- https://huggingface.co/docs/trl/en/dpo_trainer  
- https://arxiv.org/abs/2305.14314  
- https://huyenchip.com/2025/01/16/ai-engineering-pitfalls.html  
- https://huyenchip.com/2023/04/11/llm-engineering.html  
- ../../phase-2/week-10-rag-evaluation/README.md  
- ../../phase-4/week-16-error-analysis-flywheel/README.md  
