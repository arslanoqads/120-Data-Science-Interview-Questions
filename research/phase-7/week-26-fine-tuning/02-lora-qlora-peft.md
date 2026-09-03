# 02 — LoRA / QLoRA / PEFT overview

> Week 26 — Fine-tuning when RAG isn't enough  
> Research notes (raw).

---

## Fundamentals

**Full fine-tuning** updates (almost) all parameters — storage, optimizer state, and multi-tenant serving cost explode at LLM scale. **PEFT** (Parameter-Efficient Fine-Tuning) trains a **small** set of task parameters while freezing the base.

**LoRA** (Hu et al., 2021, arXiv:2106.09685): for a frozen weight \(W\), learn low-rank factors \(A, B\) so the effective update is \(\Delta W = BA\) (rank \(r \ll d\)). Only \(A, B\) (and optionally biases) train. At inference, adapters can be **merged** into \(W\) (no extra latency) or kept separate for **multi-adapter** serving.

Key knobs (Hugging Face PEFT `LoraConfig`):

| Knob | Meaning |
|------|---------|
| `r` (rank) | Capacity of the update; lower → fewer params, less expressivity |
| `lora_alpha` | Scaling; effective scale often \(\alpha / r\) (or RSLoRA \(\alpha / \sqrt{r}\)) |
| `target_modules` | Which projections get adapters (e.g. `q_proj`, `v_proj`, MLP gates) |
| `lora_dropout` / `bias` | Regularization and whether biases train |

**QLoRA** (Dettmers et al., 2023, arXiv:2305.14314): keep the **base in 4-bit** (NF4 + double quantization + paged optimizers) and still train LoRA adapters in higher precision. Goal: finetune very large models on a **single** high-memory GPU with task quality close to 16-bit LoRA.

**What you actually change:** not “the whole LLM personality dump,” but a thin **adapter artifact** (MBs–low GBs) conditioned on your dataset. Base capabilities remain mostly those of the frozen model — which is why **catastrophic forgetting** and eval (file 04) still matter, and why FT does not replace RAG for fresh facts (file 01).

Tooling stack (legal / official): **PEFT** for adapters; **TRL** (`SFTTrainer`, DPO trainers) for training loops; **Unsloth** for faster / lower-VRAM LoRA–QLoRA compatible with TRL.

**Mental model for FDEs:** the base model is a shared library; each product skill is a patch. You version the patch (`adapter_config.json` + weights), pin the library (`base_model_revision`), and evaluate the composition. Merging is optional packaging for edge/air-gap — not the same as “we permanently rewrote the foundation model.”

---

## Alternatives & Tradeoffs

| Method | Trainable footprint | Pros | Cons |
|--------|---------------------|------|------|
| Full FT | ~all weights | Max flexibility | Cost; multi-copy serving; forgetting risk |
| LoRA (fp16/bf16 base) | Rank-\(r\) mats | Strong quality; mergeable; multi-adapter | Needs VRAM for base in higher precision |
| **QLoRA** | LoRA + 4-bit base | Consumer / single-GPU large models | Dequant overhead; quant edge cases |
| Prefix / prompt tuning | Tiny | Very small | Often weaker than LoRA on generative tasks |
| Vendor managed FT (OpenAI / Bedrock) | Opaque internals | Ops simplicity | Less control; pricing; export limits |

| Rank / targets | When |
|----------------|------|
| Small `r` (4–16), attention only | First pass; style/format |
| Higher `r`, attention + MLP | Harder domain skills after plateau |
| Many adapters, one base | Multi-tenant / multi-task serving |

Tradeoff: merging adapters simplifies latency but loses hot-swap; hot-swap (PEFT) simplifies ops for many tasks but needs careful rank/`target_modules` compatibility.

Compared to **prompt tuning / prefix tuning**: fewer moving parts at inference for LoRA-merge workflows, and generally stronger generative quality in modern practice — which is why this elective standardizes on LoRA/QLoRA rather than every PEFT variant.

---

## Necessity

If you skip PEFT literacy:

- Teams equate “fine-tune” with full 70B copies per customer — deal dies on cost.  
- Or they QLoRA without understanding **frozen 4-bit base + small trainable adapters**, then wonder why Hub uploads are tiny (adapters only) or why eval still needs the base weights.  
- Rank is treated as magic (`r=256` “to be safe”) → overfitting and wasted VRAM.  
- FDEs cannot explain air-gap delivery: ship **base + adapter** (or merged GGUF) vs shipping a RAG service.  
- Week 20 cost talks ignore that PEFT training ≠ PEFT inference hosting.

PEFT is the default **implementation shape** once the decision memo (file 01) says FT is warranted.

---

## Industry Practice

- **Common:** copy a Colab; train until loss ↓; merge; no adapter registry; one-off Unsloth run undocumented.  
- **Strong:** PEFT config in Git (`r`, alpha, targets, base revision); TRL/Unsloth job configs versioned; adapters stored as artifacts next to dataset hash; optional merge for edge.  
- **FDE bar:** quote LoRA’s frozen-\(W\) + low-rank \(\Delta W\); know QLoRA’s NF4 motivation; compare managed OpenAI/Bedrock FT vs self-host PEFT for the customer’s data-residency story.

References: PEFT LoRA conceptual guide; TRL Unsloth integration; LoRA & QLoRA papers; Bedrock/OpenAI when the customer refuses DIY GPU.

---

## Concrete Scenario

**Hugging Face PEFT — LoRA conceptual guide:**  
https://huggingface.co/docs/peft/main/en/conceptual_guides/lora  

An FDE delivering an on-prem summarizer for clinical note *formatting* (not diagnosis facts) freezes Llama-class weights, attaches LoRA to attention projections with `r=16`, trains with TRL `SFTTrainer`, and ships adapter weights plus pinned base revision. If VRAM is tight on the training box, switch to QLoRA (arXiv:2305.14314) without changing the product decision — still PEFT, still not a substitute for retrieving the hospital’s living policy PDFs.

Unsloth + TRL path for faster iteration:  
https://huggingface.co/docs/trl/en/unsloth_integration  

---

## Open Questions

- Optimal default `target_modules` per architecture family — still folklore-heavy?  
- DoRA / RSLoRA / newer PEFT variants — when do they beat vanilla LoRA enough to standardize?  
- Adapter composition (stacking multiple LoRAs) — eval and conflict rules?  
- Quantization at **inference** after QLoRA train — double-quant traps?  
- Will inference engines standardize adapter hot-swap APIs across vLLM / TensorRT-LLM?

---

## Sources

- https://arxiv.org/abs/2106.09685  
- https://arxiv.org/pdf/2106.09685  
- https://arxiv.org/abs/2305.14314  
- https://arxiv.org/pdf/2305.14314  
- https://huggingface.co/docs/peft/index  
- https://huggingface.co/docs/peft/main/en/conceptual_guides/lora  
- https://huggingface.co/docs/trl/en/sft_trainer  
- https://huggingface.co/docs/trl/en/unsloth_integration  
- https://docs.unsloth.ai/  
- https://platform.openai.com/docs/guides/fine-tuning  
- https://docs.aws.amazon.com/bedrock/latest/userguide/custom-model-fine-tuning.html  
