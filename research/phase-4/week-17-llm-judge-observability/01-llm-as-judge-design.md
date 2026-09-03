# 01 — Designing LLM-as-judge that correlates with human judgment

> Week 17 — Judge *design* (what you ask the model to do)  
> Research notes (raw). Calibration metrics and splits: file [02](02-judge-alignment-calibration.md). Code vs judge: file [03](03-code-based-vs-model-based-evals.md).

---

## Fundamentals

An **LLM-as-judge** is a model prompted to **score or label another system’s outputs** using explicit criteria. Use it when quality is **subjective or semantic**: tone, persona, “should have asked a clarifying question,” faithfulness *given retrieved context*, pedagogical appropriateness. Do **not** use it as the first metric you invent (Week 16) and do **not** use it for failures a parser can catch (file 03).

### What “correlates with human judgment” means here

Product evals are not SummEval leaderboards. **Human** = the **principal domain expert** (Hamel: psychologist, lawyer, CS director, lead teacher — or founder in a tiny company). Correlation / agreement is **with that expert’s Pass/Fail**, not with a crowd of random raters and not with ROUGE.

Hamel’s diagnosis of failed judge programs ([llm-judge](https://hamel.dev/blog/posts/llm-judge/)):

1. **Too many metrics** — unmanageable dashboards.  
2. **Arbitrary 1–5 scales** — nobody can say what a 3 vs 4 is; evaluators disagree.  
3. **Ignoring domain experts.**  
4. **Unvalidated metrics** that don’t reflect users or the business.

The replacement technique is **critique shadowing**: the judge learns to produce the **same Pass/Fail + critique style** as the expert.

### Critique shadowing (design steps that are *not* just “write a rubric”)

From Hamel (Oct 2024 guide, updated 2026):

1. **Find the principal domain expert** — one (maybe two) people whose taste *is* product quality. Developers acting as proxy “because they’re available” is a failure mode. Involvement does not have to be full-time; frictionless review UI matters.  
2. **Create a diverse dataset** — production sample **and/or** synthetic **inputs** through the **real** system (features × scenarios × personas). Do **not** synthesize gold *answers*. Hex (Bryan Bischof, quoted by Hamel): LLMs are surprisingly good at diverse *user prompts* for evals.  
3. **Expert: binary Pass/Fail + detailed critique** — “Did the AI achieve the desired outcome?” Critiques must be rich enough to become few-shots (a new employee could apply them). Terse critiques are a listed failure mode. Passes can still mention improvements; fails must name the **critical** miss.  
4. **Fix errors first** — if the system is still full of prompt bugs, do not freeze a judge on a moving target. Level 1 assertions (Hamel evals post) should already catch pervasive format bugs.  
5. **Build the judge from expert examples** — Honeycomb Query Assistant: judge prompt includes query-language facts, guidelines, and **XML-ish few-shots** of NLQ + generated query + `{critique, outcome}`. Ask the model to **write the critique first**, then the label (same order as G-Eval’s “reason then score,” different product framing).  
6. **Iterate the prompt until the expert and judge converge** — Honeycomb: spreadsheet of NLQ / query / judge critique / judge outcome vs Phillip’s labels; **three iterations** to **>90%** agreement on a **balanced** set. Then (and only then) apply the judge to unseen data for **error rates by dimension**.  
7. **Specialize later** — after error analysis, add **narrow** judges (citations, etc.) or **code** assertions. Do not start with a zoo of specialized judges.

Hamel: **start simple**. If stakeholders demand “8 dimensions on 1–5,” they usually do not know what they want yet. Binary forces articulation. You can add complexity later.

### G-Eval (research design, not a product template)

**G-Eval** (Liu, Iter, Xu, Wang, Xu, Zhu — EMNLP 2023, [Anthology](https://aclanthology.org/2023.emnlp-main.153/)):

- Problem: BLEU/ROUGE correlate poorly with humans on creative/diverse NLG.  
- Method: LLM (GPT-4) with **chain-of-thought** criteria generation + **form-filling** scores.  
- Result: Spearman **0.514** with humans on **summarization**; large margin over prior automatic metrics. Also evaluated on dialogue.  
- Caveat: **bias toward LLM-generated texts** — LLM judges may prefer LLM style. That is a **product risk** if your users are humans writing unlike the judge model.

OpenAI’s evaluation-best-practices **example** for transcript summarization even pairs ROUGE-L ≥ 0.40 with a G-Eval-style coherence target. Hamel/Shreya: treat those as **optional research-style metrics**, not default product scores. If you use G-Eval-like CoT, still **calibrate on your expert labels** (file 02).

### Prompt anatomy that actually correlates

A working product judge prompt (Hamel + Langfuse docs) typically includes:

| Piece | Why |
|-------|-----|
| Role + **one** failure mode | “You judge whether a clarifying question was required,” not “score quality 1–5” |
| Criteria in the expert’s language | Copied from axial-coded Week 16 notes |
| Same **context** the expert had | User metadata, inventory, retrieved docs, tool results — Langfuse: map `{{input}}`, `{{output}}`, metadata, tool calls |
| Few-shot **critiques** (diverse Pass and Fail) | Hamel: missing/terse/non-diverse examples are the #1 prompt bug |
| Structured output | JSON `{critique, outcome}` or boolean score + reasoning; Langfuse numeric/categorical/boolean |
| Temperature 0 / pinning | Repeatability (Langfuse faithfulness guide) |

Langfuse message roles: **System** = stable rubric; **User** = mapped variables; **Assistant** = few-shot of the *judge’s* reply shape ([docs](https://langfuse.com/docs/evaluation/evaluation-methods/llm-as-a-judge)).

**Observation vs whole-trace:** Langfuse **recommends observation-level** judges for production. They **do not load sibling spans**. If faithfulness needs retrieved docs, **write context onto the generation** (or judge a logical root that already holds overall I/O). Trace-level evaluators are **deprecated** (Cloud: keep working until **2026-11-16**).

**Same model as producer?** Hamel/Shreya FAQ: for **scoped binary** judges, **usually fine** — the judge task ≠ the generation task. Literature on self-preference exists; **TPR/TNR on held-out humans** decides. Start with the **most capable** judge; cost-optimize later. Switch models only if alignment fails ([FAQ](https://hamel.dev/blog/posts/evals-faq/can-i-use-the-same-model-for-both-the-main-task-and-evaluation.html)). OpenAI cookbook: often prefer a **different** model when practical — treat as a **bias hedge**, not a religion.

**Pairwise (A vs B):** OpenAI notes LLMs are stronger at **discrimination** than open generation of a score. Pairwise is excellent for **ranking prompts/models**; weaker as an **absolute CI gate** (“is this request a Fail?”).

**RAG-specific design:** claim extraction → binary support per claim → **aggregate in code** (never let the judge do the arithmetic). Forbid outside knowledge; allow paraphrase; don’t penalize “I don’t know” ([Langfuse faithfulness](https://langfuse.com/resources/engineering/rag-faithfulness-evaluation)). That design is closer to Hamel’s binary philosophy than a holistic 1–5 “faithfulness” slider.

Langfuse FAQ claim: strong judges can reach **~80–90%** agreement with humans on many dimensions — **comparable to human–human IAA**. That is **marketing-adjacent**; still **calibrate on your labels**. Hamel: if two humans agree worse than chance (Nova Escola), **no judge can save a missing rubric**.

---

## Alternatives & Tradeoffs

| Judge design | Pros | Cons |
|--------------|------|------|
| **Binary + critique (Hamel)** | Actionable; forces criteria; few-shots from critiques | Less nuance on dashboards; stakeholders want 1–5 |
| Likert 1–5 multi-dim | Familiar | Uncalibrated; vanity; Field Guide trap |
| G-Eval-style CoT + form fill | Better NLG correlation in research | Cost; LLM-text bias; still needs product calibration |
| Pairwise preference | Strong for model/prompt ranking | Awkward absolute regression gates |
| Reference metrics (BLEU/ROUGE) | Cheap, deterministic | Weak human correlation for open-ended gen (G-Eval paper) |
| Same model as producer | Ops-simple | Self-preference risk; OK if binary task aligns |
| Stronger/different judge model | Bias hedge; OpenAI default advice | Procurement; latency; still needs labels |
| Fine-tuned small judge | Cheap at scale | Hamel: rare; prefer PE; needs even more labels |
| Vendor hallucination template | Instant | Uncorrelated with Week 16 taxonomy |

Hamel FAQ: same model is **often fine** for scoped binary if TPR/TNR hold.

---

## Necessity

Uncalibrated / badly designed judges:

- Optimize the product for the judge’s quirks (sycophancy, length, self-preference, G-Eval LLM-text bias).  
- Create dashboards nobody trusts.  
- Fail to catch the **taxonomy** failures you actually care about.  
- Reward-hack (agent writes what the judge likes) — especially if the judge is in the training/improvement loop without humans.

Skipping judges entirely for **subjective** residual failures leaves only slow human review at production scale (Nova Escola needed daily sampled automation *after* IAA was fixed).

Building a judge **before** reading traces (Week 16) produces a rubric that never appears in production (Nova Escola mistake).

---

## Industry Practice

**Common:** Enable Langfuse/Phoenix “helpfulness” template; never sit with the expert; never few-shot critiques.

**Strong:**

1. Error analysis → **one** failure mode.  
2. Expert labels (balanced Pass/Fail where possible).  
3. Split few-shot / dev / held-out (file 02).  
4. Iterate **prompt** with expert critiques (Honeycomb three loops). Prefer PE; AlignEval (Eugene Yan) for UI loops; Hamel has not had much luck with DSPy-style prompt optimizers for this.  
5. Gate TPR/TNR; do not ship.  
6. Log judge executions as traces (Langfuse environment filter `langfuse-llm-as-a-judge`: Completed / Error / Delayed / Pending).  
7. Recalibrate on model or product change.  
8. Version evaluator definitions (Langfuse: evaluators version; rules sample + filter).

**Langfuse score types:** numeric (e.g. 0–1 helpfulness — Hamel would still push binary product gates), categorical (`correct` / `partial`), boolean (policy, out-of-scope). Prefer boolean for Week 17 product judges unless you aggregate claim-level binaries into a rate.

**Multi-modal:** Langfuse can map media into judge prompts if the judge model supports the type.

---

## Concrete Scenario (URL)

**Hamel — complete critique-shadowing guide (Honeycomb few-shots, three iterations, prompt mistakes).**  
https://hamel.dev/blog/posts/llm-judge/

**G-Eval paper (ACL Anthology + DOI).**  
https://aclanthology.org/2023.emnlp-main.153/  
https://doi.org/10.18653/v1/2023.emnlp-main.153

**Shankar et al. — you cannot freeze criteria before grading (EvalGen / criteria drift).**  
https://arxiv.org/abs/2404.12272

**Langfuse — how a judge prompt is wired (variables, observation-level, debug traces).**  
https://langfuse.com/docs/evaluation/evaluation-methods/llm-as-a-judge

**Langfuse — claim-level faithfulness judge (binary claims, score in code).**  
https://langfuse.com/resources/engineering/rag-faithfulness-evaluation

**OpenAI cookbook — getting started with evals (model grading, human validation).**  
https://developers.openai.com/cookbook/examples/evaluation/getting_started_with_openai_evals

**YouTube — treat LLM-as-judge as a classifier.**  
https://www.youtube.com/watch?v=DZxaPNYi_k0  

**YouTube — Lenny: don’t jump to writing evals; actual errors first; code vs LLM.**  
https://www.youtube.com/watch?v=BsWxPI9UM4c

---

## Open Questions

- When do multi-dimensional scores become necessary vs harmful?  
- How much self-enhancement bias remains for modern judges on binary **product** tasks?  
- G-Eval n-sample / token-probability scoring vs single structured label in production?  
- Can smaller/cheaper judges match large ones after distillation on expert labels?  
- Dynamic few-shot / continual ICL (Hamel points to a follow-up) vs static Honeycomb-style examples?  
- Should pairwise tournaments replace binary gates for prompt selection only?

---

## Sources

- https://hamel.dev/blog/posts/llm-judge/  
- https://hamel.dev/blog/posts/evals/  
- https://hamel.dev/blog/posts/evals-faq/can-i-use-the-same-model-for-both-the-main-task-and-evaluation.html  
- https://arxiv.org/abs/2404.12272  
- https://aclanthology.org/2023.emnlp-main.153/  
- https://developers.openai.com/cookbook/examples/evaluation/getting_started_with_openai_evals  
- https://developers.openai.com/api/docs/guides/evaluation-best-practices  
- https://langfuse.com/docs/evaluation/evaluation-methods/llm-as-a-judge  
- https://langfuse.com/resources/engineering/rag-faithfulness-evaluation  
- https://www.youtube.com/watch?v=DZxaPNYi_k0  
- https://www.youtube.com/watch?v=BsWxPI9UM4c  
