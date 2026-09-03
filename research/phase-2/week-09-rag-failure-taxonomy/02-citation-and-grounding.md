# 02 — Citation and grounding techniques

> Week 9 concept research (deep). Legal sources only.

---

## Fundamentals

**Grounding** = every **material claim** in the answer is entailed by retrieved evidence, **or** the system emits an explicit refusal. **Citation** = exposing that entailment to a user or auditor via pointers. Citation without grounding verification is **false trust** (confident prose + a link that does not support the sentence).

Jason Liu **A|C** (faithfulness/groundedness) is the claim-level property. Azure names the same split: Groundedness = **precision** (nothing outside C); Response Completeness = **recall** (nothing critical missing vs gold). RAGAS **Faithfulness** operationalizes A|C as:

\[
\text{Faithfulness} = \frac{\#\text{ claims in the response supported by retrieved context}}{\#\text{ claims in the response}}
\]

Pipeline: decompose answer into claims → NLI/support check vs C → ratio. Example from RAGAS docs: “Einstein born in Germany” supported; “born 20 March 1879” not supported when C says 14 March → 0.5.

Three **moments** (industry pattern):

1. **Index time** — stable identity for whatever you will later cite: `doc_id`, content-addressed `chunk_id` (e.g. `sha256(canonical_text)`), character offsets / page / bbox, `doc_hash`, `pipeline_version`, `embedding_model`, `ingested_at`. Barnett AI Tutor: students **verify** via a sources list — product requirement, not a prompt flourish. Adding **filename + chunk number into retrieved context** improved extraction (lesson table: FP2, FP4).  
2. **Generation time** — a **grounding contract**: the model may only cite IDs that appear in this prompt; prefer **structured citation objects** (`chunk_id`, `doc_id`, quote, score) over free-text “Source: Wikipedia.” Schema validation (Week 4 structured outputs) turns “please cite” into an enforceable constraint. Managed platforms (Amazon Bedrock Knowledge Bases `RetrieveAndGenerate`) return `retrievedReferences` tying answer spans to source locations — citation as a **platform primitive**.  
3. **Verification time** — post-hoc support check (RAGAS-style claim decomposition, Azure `GroundednessEvaluator` 1–5 LLM judge, Azure **Groundedness Pro** Content Safety **binary**, Databricks `RetrievalGroundedness` / `retrieval_groundedness(trace)`). On failure: regenerate, strip the unsupported sentence, or warn. Databricks judge returns `value` yes/no plus rationale with **quotes from context**; it requires a trace span `span_type=RETRIEVER` so C is the **retrieved** payload, not a later corpus fetch.

Citation UX patterns:

| Pattern | What the user sees | Failure mode |
|---------|--------------------|--------------|
| Inline anchors `[1]` + bibliography | Familiar | Anchors are positional; reordering C silently retargets `[1]` |
| Structured citation block | Auditor-friendly | Ugly unless UI maps IDs to titles |
| Span-grounded refs (offsets, PDF locators, `doc_hash`) | Audit-grade | Breaks if you re-render from live corpus instead of **snapshot** |
| Source list, no claim-level links | Easy | Cannot tell which sentence used which source (Barnett still wanted the list for tutors) |

NVIDIA NeMo `rag_faithfulness` (RAGAS type) needs `question, answer, contexts` and a `judge_llm`. `response_groundedness` in newer metric tables evaluates response vs retrieved contexts without always requiring the question. Vectara HHEM (wired in RAGAS `FaithfulnesswithHHEM`) is a small T5 hallucination classifier for the support step — cheaper than a second GPT.

Refusal gate: if retrieval confidence / C|Q is below threshold, **do not generate a grounded-looking answer**. That is how FP1 stays a success instead of a fluent lie. Jason Liu **Q|C** (question answerability given C) is the metric for that gate.

---

## Alternatives & Tradeoffs

| Technique | Strength | Weakness |
| --- | --- | --- |
| Prompt-only “please cite sources” | Cheap | Citation hallucination; cites docs never retrieved |
| Forced cite-from-provided-IDs + JSON schema | Enforceable contract | Needs good chunking; IDs leak into UX if not mapped |
| Post-hoc sentence→chunk similarity | Works on legacy answers | Cosine ≠ entailment; needs NLI/judge |
| Fine-tuned citation models / cite-pretraining | Fewer citation-shaped lies | Cost; domain data |
| Show sources list only | Easy; AI Tutor-shaped | No claim-level audit |
| Groundedness Pro (Azure Content Safety) | Strict binary, hosted | Different definition than 1–5 GPT judge — scores will disagree |
| RAGAS faithfulness | Claim decomposition documented | Judge cost; claim splitter errors; faithful-to-stale-C still “1.0” |
| Databricks trace-groundedness | Uses actual RETRIEVER span | Useless if you never tagged spans |

Content-addressed chunk IDs survive **reindex of the same bytes**. Auto-increment IDs churn. Offset-based citations survive **text** edits poorly unless you version the **exact artifact** injected into the model (`packed_text_hash` / evidence snapshot). That is the bridge to concept 03 (citation drift).

Granularity tradeoff: token-span citations maximize audit and crush latency; chunk-level is the usual product default; sentence-level is the RAGAS claim unit.

---

## Necessity

Regulated and education surfaces (Barnett AI Tutor; Hamel’s medical RAG dose example) need **reproducible evidence**. A correct answer with a wrong citation is a **grounding UX failure** even if A|Q looks fine. A wrong answer with a pretty citation is worse: it teaches the user to trust the pointer.

Service-specific failures:

- **Citation hallucination:** `[12]` not in retrieved ID set — catch with a **code** assertion (Hamel: not everything needs a judge).  
- **Stale render:** UI opens current docs.corp/policy.html; model saw `policy.html@hash_a`. After legal edits, the quote is gone → **citation drift** (concept 03).  
- **Faithfulness 1.0, completeness 0:** FP7 — all claims supported, gold treatments missing. Azure completeness evaluator needs `ground_truth`.  
- **Groundedness vs Groundedness Pro disagreement:** 1–5 judge passes “reasonable paraphrase”; Pro fails strict consistency. Pick one definition per product policy.  
- **Judge context ≠ packed context:** concatenated `\n\n` Azure `context` string must be the **same** string the generator saw (Foundry docs: concatenate chunks with a separator).  
- **Parametric true fact not in C:** A|C fails if policy is “context-only”; passes if hybrid-allowed. Label the policy on the log.

---

## Industry Practice

**Common:** “Answer using the context. Cite sources.” No ID allowlist. Sources panel lists cosine top-4 titles.

**Strong:**

- Allowlist citation IDs = packed IDs.  
- Store **evidence snapshots** (raw chunk text at answer time) for the citation UI.  
- Refusal when C|Q / retrieval metrics fail.  
- Independent evals: Azure Groundedness (`response`, `context`, optional `query` for better scoring; agent mode can pull tool-call context) + Relevance (`query`, `response`) + Completeness (`ground_truth`, `response`).  
- Databricks: `mlflow.trace(span_type="RETRIEVER")` returning `Document(id, page_content, metadata)` then `RetrievalGroundedness` scorer.  
- RAGAS Faithfulness on the same snapshot; do not re-retrieve at eval time.  
- Hamel: if citation format is the failure, a **targeted** judge or a schema test; calibrate against humans before trusting dashboards.

**FDE bar:** distinguish grounding (entailment) from citation (pointer); demo a **false-trust** example (unsupported claim + real URL); quote Azure precision/recall split; show a code check that every `citation.chunk_id ∈ packed.ids`.

---

## Concrete Scenario

AWS / architecture writeups of Bedrock Knowledge Bases: `RetrieveAndGenerate` returns `retrievedReferences` (location in the KB). Curriculum analogue: generator JSON

```json
{
  "answer": "...",
  "citations": [
    {"chunk_id": "sha256:…", "quote": "…", "start": 120, "end": 188}
  ],
  "refused": false
}
```

Verifier: (1) IDs ⊆ packed set; (2) `quote` is a substring of snapshot; (3) RAGAS/Azure groundedness on claims vs snapshots; (4) if `gold_chunk_ids` not subset of packed → do not blame the generator.

Azure sample jsonl uses `query`, `context`, `response` on store-hours / return-policy — the **process** Retrieval evaluator uses `query`+`context`; Groundedness uses `response`+`context`.

URL: https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/faithfulness/  
Companions: https://learn.microsoft.com/en-us/python/api/azure-ai-evaluation/azure.ai.evaluation.groundednessevaluator · https://learn.microsoft.com/en-us/azure/foundry/concepts/evaluation-evaluators/rag-evaluators · https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/concepts/judges/is_grounded · https://aiarch.dev/patterns/grounded-rag

---

## Open Questions

- Optimal citation granularity (chunk vs sentence vs token span) vs latency and user trust?  
- How to cite **multi-hop** answers where no single chunk entails the full claim (need a reasoning trace + multiple quotes)?  
- Should allowed parametric knowledge be tagged `"origin": "model_prior"` when product policy permits hybrid answers?  
- Can Groundedness Pro replace RAGAS faithfulness in high-stakes oracles, or only as a second vote?  
- Agent traces: Azure says `context` optional if tool-call results exist — does that hide FP3 (retrieved but not passed to the reader)?

---

## Sources

- RAGAS Faithfulness: https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/faithfulness/  
- Azure Groundedness evaluator API: https://learn.microsoft.com/en-us/python/api/azure-ai-evaluation/azure.ai.evaluation.groundednessevaluator  
- Azure RAG evaluators (Groundedness vs Completeness vs Pro): https://learn.microsoft.com/en-us/azure/foundry/concepts/evaluation-evaluators/rag-evaluators  
- Databricks RetrievalGroundedness: https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/concepts/judges/is_grounded  
- NVIDIA `rag_faithfulness` / groundedness metrics: https://docs.nvidia.com/nemo/microservices/26.3.0/evaluator/metrics/rag.html  
- Barnett et al. (AI Tutor sources list; metadata in context): https://arxiv.org/abs/2401.05856  
- Jason Liu A\|C: https://jxnl.co/writing/2025/05/19/there-are-only-6-rag-evals/  
- Hamel judges + citation-shaped targeted evals: https://hamel.dev/blog/posts/evals-faq/index.html  
- Grounded RAG pattern (retrievedReferences): https://aiarch.dev/patterns/grounded-rag  
- Attribution overview: https://mbrenndoerfer.com/writing/attribution-and-citation  
- YouTube: Hamel & Shreya “How to Automate AI Evals (Correctly)” https://www.youtube.com/watch?v=tqUDjc1HzO4  
