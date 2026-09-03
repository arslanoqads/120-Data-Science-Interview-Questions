# 03 — Synthetic data to surface edge cases

> Week 16 — LLM-generated **user inputs**, not fake gold answers  
> Research notes (raw).

---

## Fundamentals

In this week’s vocabulary, **synthetic data** means **LLM-generated user inputs** (queries, tickets, utterances) that you run through the **real application** so you get **real traces**. It does **not** mean generating synthetic “gold” assistant completions and scoring against them. Hamel Field Guide guideline: **generate user inputs, not outputs**, so you do not inherit the generator’s answer biases ([Field Guide §4](https://hamel.dev/blog/posts/field-guide/); also [LLM-as-a-Judge guide](https://hamel.dev/blog/posts/llm-judge/)).

### When to use it

Hamel FAQ [What is the best approach for generating synthetic data?](https://hamel.dev/blog/posts/evals-faq/):

- **Bootstrap error analysis** before enough production traffic.  
- **Force rare edge cases** that random production samples of 100 will miss.  
- After generation: run through the **full system**, capture traces, then open-code as usual (~100 diverse traces as a discovery pool; ≥30 human).

**Cannot** estimate production **failure rates**. Can miss domain-specific realism. **Compare with real traffic ASAP.**

OpenAI public [evaluation best practices](https://developers.openai.com/api/docs/guides/evaluation-best-practices): collect **synthetic, domain-specific, purchased, human-curated, production, and historical** data as **complementary** sources. Include typical, edge, and adversarial cases. Human expert labelers. (Hamel still: synthetic queries must hit **your** tools/DB constraints.)

### Structured dimensions (not “give me 50 test queries”)

Common mistake: one-shot “give me test queries” → generic, repetitive phrasing.

**Dimensions** = categories of variation. Examples from the FAQ:

| Product | Dimensions (illustrative) |
|---------|---------------------------|
| Recipe app | Dietary restriction × cuisine × query complexity |
| Support bot | Issue type × customer mood × prior context |

Field Guide / Rechat **Lucy** (and LLM-as-judge post): think **features × scenarios × personas**:

```
features  = property search, market analysis, scheduling, follow-up
scenarios = exact match, multiple matches, no matches, invalid criteria
personas  = first_time_buyer, investor, luxury_client, relocating_family
```

Start from **failure hypotheses**. If you lack intuition, **use the app** (or friends) first, then choose dimensions that target likely failures.

### Two-step generation

1. Write **~20 tuples by hand** so you understand the space. Example: `(Vegan, Italian, Multi-step)`.  
2. Scale: LLM generates more **tuples**, then a **separate** prompt converts each tuple → natural language (avoids repetitive phrasing). `(Vegan, Italian, Multi-step)` → “I need a dairy-free lasagna recipe that I can prep the day before.”

**Tuple generation modes:**

| Mode | Strength | Weakness |
|------|----------|----------|
| **Cross-product then filter** | Guarantees rare edges | Many combos invalid; need a filter LLM |
| **Direct LLM tuples** | More realistic combos | Generic; **misses long-tail** |

Use cross-product when most combinations are valid; direct generation when many combos are nonsense.

**Fix obvious problems first.** Don’t synthesize tests for a missing dietary-restriction instruction—**add the instruction**. Same as Langfuse “don’t build an evaluator for a prompt gap.”

### Ground in system constraints

Field Guide: dimensions are half the battle. You also need:

1. A **test database** (or anonymized prod copy) with enough variety.  
2. **Verification** that the generated query **actually triggers** the intended scenario (`no matches` must return zero rows).

Rechat: listings chosen so “multiple matches” / “no matches” are true; queries use **real listing IDs, schedules, HOA rules, notice periods**. Pseudo-pattern: sample listings for persona → assert scenario constraints → prompt the LLM to write a query **grounded in those listings**.

If you have **no** production DB: generate **both** queries and underlying records, still constrained (realistic prices, real street-name patterns). Field Guide: generating robust synthetic DBs is a separate engineering problem.

Bryan Bischof (former Head of AI, Hex), quoted by Hamel: LLMs are “surprisingly good at generating excellent—and diverse—examples of user prompts” for **features and evals**; “large language snake eating its tail” but **it works**.

[Your AI Product Needs Evals](https://hamel.dev/blog/posts/evals/) Lucy example: prompt that writes 50 CRM “create contact” instructions **plus** a second instruction to look the contact up; assertion `len(results)==1`; plus generic regex “no exposed UUID.” Synthetic inputs + **code assertions** on **system state**—not BLEU on a fake reply.

### What synthetic is for vs not

Use traces for: open coding, taxonomy, **later** judge calibration, stress of known rare combos, filling eval-set **coverage** of workflows.

Do **not** use synthetic **rates** as production rates. Do not treat generated answers as ground truth for *your* pipeline (the generator is not your tools + RAG + policies).

### When synthetic is unreliable (Hamel FAQ)

1. **Complex domain-specific content** (legal filings, medical records, technical forms)—LLMs miss structure/quirks.  
2. **Low-resource languages/dialects**—unrealistic samples.  
3. **Cannot validate realism** (no expert, no ground truth).  
4. **High-stakes** (medicine, law, emergency)—missing subtlety; errors costly.  
5. **Underrepresented user groups**—can reinforce generator biases.

Those cases still benefit from **real** traces and SME labeling (AnkiHub med-student pattern).

### Interaction with error analysis

FAQ: for apps with wildly different query types, **do not** pre-build a giant eval matrix by query class. Let **error analysis** show which categories share failure patterns (e.g. all temporal-reasoning queries fail similarly). Query type *might* be a good grouping—you don’t know until you look.

After synthetic traces exist, the workflow is identical: sample, open-code ≥30, saturate, count. Langfuse: no prod yet → representative synthetic inputs, capture traces, sample from those.

---

## Alternatives & Tradeoffs

| Data source | Strength | Weakness |
|-------------|----------|----------|
| Production sampling | Real distribution, **rates** | Cold start; privacy; rare edges missing |
| Synthetic **inputs** → real system | Coverage of rare combos; fast | Distribution ≠ production; domain blind spots |
| Purchased / vendor datasets | Scale | Often generic; weak product fit |
| Human-written cases only | High quality | Expensive; incomplete coverage |
| Fully synthetic I/O (fake answers) | Cheap | Useless for product evals of *your* pipeline |
| Adversarial / red-team generators | Stress safety | May not match real user phrasing; still not rates |
| Historical logs (OpenAI list) | Real past traffic | Stale vs current prompt/model |

Cross-product vs direct generation: coverage vs realism (above).

---

## Necessity

Without synthetic (or other **stress**) data:

- Pre-launch products have nothing to open-code.  
- Known rare failures never appear in random samples of 100.  
- Eval sets overfit happy-path traffic and miss edge regressions.

Without validating synthetic against real:

- You optimize for LLM-imagined users and ship into a different distribution (OpenAI anti-pattern: **biased design**—eval datasets that don’t reproduce production).  
- High-stakes domains silently miss the only failures that matter.

Without grounding in DB/tools:

- A “no matches” query that actually matches 40 listings tests nothing you intended (Field Guide).

---

## Industry Practice

**Common:** “Give me 50 test queries” one-shot → repetitive generic queries; or synthetic **dialogues including assistant lines** used as gold.

**Strong:**

- Structured dimensions; two-step generation; **full stack** with logging.  
- Mix synthetic + production; Hex (Hamel) uses synthetic prompts heavily for evals **and** still needs prod.  
- Don’t synthesize tests for bugs you can fix immediately.  
- ~100 diverse traces as discovery pool.  
- Rechat: hundreds of Level-1 assertions; continuously update from observed failures; **pass rate is a product decision**, not 100% ([evals post](https://hamel.dev/blog/posts/evals/)).  
- OpenAI: typical + edge + **adversarial**; expert labelers.  
- Privacy: synthetic as a **safer** stand-in for dumping PII into vendor UIs—still validate later on real (possibly redacted) traffic.

---

## Concrete Scenario (URL)

**Hamel FAQ — recipe/support dimensions, 20 hand tuples, two-step generation, ~100 traces.**  
https://hamel.dev/blog/posts/evals-faq/ (section: generating synthetic data)

**Field Guide — Rechat features/scenarios/personas; queries grounded in listing DB; Hex quote.**  
https://hamel.dev/blog/posts/field-guide/

**LLM-as-a-Judge guide — frustrated-customer invalid order numbers, ambiguous meeting requests, then live app.**  
https://hamel.dev/blog/posts/llm-judge/

**Lucy contact-create synthetic pairs + CRM assertions.**  
https://hamel.dev/blog/posts/evals/

**OpenAI — mix of data sources; log mining.**  
https://developers.openai.com/api/docs/guides/evaluation-best-practices

**Langfuse — no production data: synthetic inputs → traces → sample.**  
https://langfuse.com/guides/cookbook/error-analysis-llm-applications

---

## Open Questions

- How to measure “synthetic realism” quantitatively for specialized domains (medicine, law)?  
- Can adversarial / red-team generators replace **dimension design**, or only supplement?  
- Privacy: when is synthetic a safer substitute for production logs in vendor tools, and when does it hide demographic failure modes?  
- Agentic systems: synthetic **trajectories** (multi-turn user sim) vs single-turn queries? (τ-bench-style user sim is Week 15 literacy; here the bar is still “run through **your** tools.”)  
- Who owns the test DB that makes scenario verification true—eng or PM?

---

## Sources

- https://hamel.dev/blog/posts/llm-judge/  
- https://hamel.dev/blog/posts/evals-faq/  
- https://hamel.dev/blog/posts/field-guide/  
- https://hamel.dev/blog/posts/evals/  
- https://developers.openai.com/api/docs/guides/evaluation-best-practices  
- https://langfuse.com/guides/cookbook/error-analysis-llm-applications  
- https://www.youtube.com/watch?v=BsWxPI9UM4c  
