# 02 — Bias and fairness evaluation for LLM outputs

> Week 29 — AI Safety, Ethics, and Adversarial Testing  
> Research notes (raw).

---

## Fundamentals

**Bias / fairness evaluation** for LLMs asks whether outputs systematically disadvantage or stereotype groups — or produce unequal quality / refusal / toxicity rates — across slices that matter for the product. It is **not** “we prompted the model to be fair.” It is measurement: defined populations or proxies, metrics, thresholds, and remediation owners.

NIST AI RMF treats fairness-related risks under trustworthy AI characteristics and pushes organizations to **Map** where harms arise, **Measure** them with appropriate metrics, and **Manage** residual risk — not assert benevolence. For generative systems, NIST’s Generative AI Profile (NIST AI 600-1) highlights risks such as harmful bias and homogenization that classical classification fairness toolkits only partially cover.

Practical metric families for LLM products:

| Metric family | Example question | Typical method |
|---------------|------------------|----------------|
| Quality parity | Does summarization / answer quality drop for dialect X? | Blind human or judge scores by slice |
| Toxicity / stereotyping | Are completions more hostile toward group Y? | Perspective / toxicity classifiers + human audit |
| Allocation / advice parity | Different loan-ish or medical-ish advice by persona? | Counterfactual persona prompts (careful ethics) |
| Refusal parity | Over-refuse identity topics for some groups? | Refusal rate by template slice |
| Representation | Who appears in generated examples? | Entity tagging on corpora |

Chip Huyen’s production LLM writing emphasizes evaluation and system design over slogans: fairness work inherits the same need for **golden sets, regression, and ownership** as accuracy evals (*Building LLM applications for production*; *Building a Generative AI Platform*).

---

## Alternatives & Tradeoffs

| Stance | Upside | Downside |
|--------|--------|----------|
| Ignore slices; optimize average win rate | Simple dashboards | Hidden disparate failures; enterprise deal risk |
| Only detox classifiers | Cheap continuous signal | Misses quality / advice disparity |
| Only human review panels | Nuance | Not continuous; sampling bias |
| Counterfactual personas everywhere | Stresses model | Ethical landmines; synthetic ≠ real users |
| **Slice metrics + targeted human audit** | Measurable + contextual | Needs PII-aware data design |

| Proxy strategy | Tradeoff |
|----------------|----------|
| Geo / language / dialect | Available in logs; coarse |
| Self-identified demographics | Accurate; rare / sensitive |
| Synthetic demographic prompts | Controllable experiments; validity gaps |

Never treat “bias score from one vendor API” as a complete fairness program.

---

## Necessity

Without fairness evaluation:

- Marketing claims “responsible AI” while support tickets show dialect or accent ASR failures cascading into bad LLM answers.  
- Hiring- or lending-adjacent copilots emit stereotyped career or credit language — legal and reputational blast radius.  
- Safety filters over-block minority dialects (toxicity false positives), creating unequal access.  
- Model swaps change stereotype rates with no regression alert.  
- Week 15 evals celebrate task success on a majority-English golden set and miss slice collapse.

Fairness eval is how ethics becomes **engineering**, not a values slide.

---

## Industry Practice

- **Common:** one-time bias brainstorm; screenshot a polite refusal; no slices in CI.  
- **Strong:** maintain slice taxonomies per product surface; track toxicity / quality / refusal by slice; calibrate moderation thresholds for disparate false-positive rates; document known residual gaps in the safety one-pager (file 05).  
- **FDE bar:** map fairness work to NIST Measure; refuse demographic inference from names without policy; show before/after on a stereotype suite after prompt or model change; distinguish **representational** harm from **allocative** harm in customer language.

Tools often reused: Perspective toxicity attributes for continuous signals; human rubrics for advice products; Promptfoo plugins for biased/toxic generation; domain legal review for regulated verticals.

---

## Concrete Scenario

**NIST — AI Risk Management Framework** (Govern / Map / Measure / Manage):  
https://www.nist.gov/itl/ai-risk-management-framework

The AI RMF (NIST AI 100-1) and companion materials give enterprises a vocabulary for fairness-related risk without prescribing a single metric. FDEs use it to structure customer conversations: which harms are in scope (Map), what is measured on which slices (Measure), what controls and residual risk remain (Manage), who is accountable (Govern). Generative-specific amplification is addressed in the Generative AI Profile: https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf

---

## Open Questions

- Which generative fairness metrics will courts and regulators actually recognize in 2026+?  
- How should multilingual products weight dialect fairness vs majority-language quality under fixed eval budgets?  
- When does measuring stereotypes via generated personas itself create policy or ethics violations?  
- Can LLM-as-judge fairness grading be calibrated across demographic slices without circular bias?  
- How do RAG corpora (Week 7–9) dominate output bias relative to the base model?

---

## Sources

- https://www.nist.gov/itl/ai-risk-management-framework  
- https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-ai-rmf-10  
- https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf  
- https://perspectiveapi.com/  
- https://developers.perspectiveapi.com/s/about-the-api-attributes-and-languages  
- https://www.anthropic.com/research/claudes-constitution  
- https://huyenchip.com/2023/04/11/llm-engineering.html  
- https://huyenchip.com/2024/07/25/genai-platform.html  
- https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/  
- https://www.promptfoo.dev/docs/red-team/  
