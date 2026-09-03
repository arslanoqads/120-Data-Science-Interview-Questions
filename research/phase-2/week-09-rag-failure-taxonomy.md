# Week 09 — RAG Failure Taxonomy (Raw Source Material)

> Curriculum research notes for RAG evaluation/debugging. Legal sources only (arXiv, vendor docs, public blogs). Not a finished lesson plan.

---

## Concept 1 — Three Canonical RAG Failure Modes (Recall / Ranking / Generation-Grounding)

### Fundamentals

Production RAG failures cluster into three diagnosable layers that map cleanly onto the Question–Context–Answer (Q–C–A) graph used by Jason Liu and the TruEra/RAGAS “RAG triad”:

| Canonical mode | Pipeline locus | Core question | Barnett et al. FP mapping |
| --- | --- | --- | --- |
| **Recall failure** | Index / retrieval | Was the needed evidence ever eligible to be returned? | FP1 Missing Content; FP2 Missed Top Ranked Documents (when relevant docs fall outside top‑K entirely) |
| **Ranking / context-assembly failure** | Retriever ranking, rerank, consolidation | Did useful evidence land high enough, and survive into the prompt window? | FP2 (near-miss ranking); FP3 Not in Context (consolidation drop) |
| **Generation-grounding failure** | Reader / LLM | Given usable context, did the model extract, stay faithful, and answer completely? | FP4 Not Extracted; FP5 Wrong Format; FP6 Incorrect Specificity; FP7 Incomplete |

**Recall failure** means the answerable evidence is absent from the corpus, wrongly chunked/embedded so similarity never fires, or filtered out by metadata/ACL gates. The system may still answer confidently from parametric memory (hallucination) unless refusal is enforced.

**Ranking failure** means relevant chunks exist in the hit list but sit below the cutoff *K*, get demoted by a weak reranker, or are discarded by a consolidator that must fit a token budget. “Lost in the middle” (Liu et al.) compounds this: even when chunks enter the prompt, mid-context evidence is under-used.

**Generation-grounding failure** means the prompt contains (or nearly contains) the answer, but the LLM invents unsupported claims, ignores instructions, under- or over-specifies, or only partially extracts multi-document answers.

Barnett et al. (arXiv:2401.05856) emphasize two engineering takeaways: (1) **validation is only feasible in operation** because real query distributions emerge at runtime; (2) **robustness evolves** via continuous calibration of chunk size, embedding, retrieval, consolidation, context size, and prompts—not via a one-shot design.

### Alternatives & Tradeoffs

| Diagnostic approach | Pros | Cons |
| --- | --- | --- |
| Collapse all errors into “hallucination” | Simple narrative | Hides whether to fix index, retriever, or prompt |
| Full 7-point Barnett taxonomy | Fine-grained debugging | Overlapping labels; harder to teach and instrument |
| Canonical 3-mode (recall / rank / ground) | Matches component ownership and metric suites | Consolidator bugs can look like either ranking or grounding |
| Jason Liu 6 Q–C–A relationships | Bridges IR metrics and LLM judges | Requires judge calibration; Tier‑3 metrics need more labels |

Tradeoff for ops: raising *K* reduces recall@K misses but increases noise → more FP4 (extraction failure) and cost. Hybrid BM25+dense + cross-encoder rerank improves ranking but adds latency and another model to evaluate.

### Necessity

Without a failure taxonomy, teams optimize the wrong stage (e.g., swapping the generator when the retriever never surfaces the doc). Taxonomy drives: which metric to watch (recall@k vs faithfulness), which owner (search vs prompt), and whether “I don’t know” is a success (FP1) or a bug (FP2).

### Industry Practice

- **Microsoft Foundry RAG evaluators** separate *Document Retrieval* (NDCG, fidelity) from *Groundedness* / *Relevance* / *Response Completeness* — explicitly process vs system evaluation.
- **Databricks Agent Evaluation / MLflow GenAI** maps judges to root causes: chunk relevance, context sufficiency, groundedness, relevance-to-query — failing rows get a judge-attributed root cause.
- **NVIDIA NeMo Evaluator** splits retrieval metrics (`recall@k`, `ndcg@k` via pytrec_eval) from generation metrics (`rag_faithfulness`, `rag_answer_relevancy`, NVIDIA groundedness variants).
- Practitioners often start with Hamel Husain’s guidance: evaluate **retrieval with search metrics** and **generation with validated application-specific judges**, then add domain failure modes found via error analysis.

### Concrete Scenario (URL)

Barnett et al. BioASQ experiment: index ~4k biomedical OA PDFs, ask 1,000 expert Q/A pairs, score with OpenAI Evals, then manually inspect false/flagged cases — yielding the seven failure points.

- Paper (HTML): https://arxiv.org/html/2401.05856v1  
- Paper (PDF/abs): https://arxiv.org/abs/2401.05856  
- Supporting materials noted in paper: https://figshare.com/s/fbf7805b5f20d7f7e356  

### Open Questions

- How should “consolidation” (FP3) be attributed—ranking metric, context-window policy, or a separate assembly metric?
- When parametric knowledge is factually correct but *not* in retrieved context, is that a grounding failure, a retrieval failure, or an acceptable hybrid answer policy?
- What taxonomies scale to multi-hop / agentic RAG (tool calls, iterative retrieve)?

### Sources

- Barnett et al., *Seven Failure Points When Engineering a Retrieval Augmented Generation System*: https://arxiv.org/abs/2401.05856  
- Jason Liu, *There Are Only 6 RAG Evals*: https://jxnl.co/writing/2025/05/19/there-are-only-6-rag-evals/  
- Hamel Husain, AI Evals FAQ — RAG approach: https://hamel.dev/blog/posts/evals-faq/index.html  
- Liu et al., *Lost in the Middle*: https://arxiv.org/abs/2307.03172  
- Azure AI Foundry RAG evaluators: https://learn.microsoft.com/en-us/azure/foundry/concepts/evaluation-evaluators/rag-evaluators  
- NVIDIA NeMo RAG evaluation flow: https://docs.nvidia.com/nemo/microservices/latest/evaluate/flows/rag.html  

---

## Concept 2 — Citation / Grounding Techniques

### Fundamentals

**Grounding** = every material claim in the answer is entailed by retrieved evidence (or an explicit refusal). **Citation** = exposing that entailment to the user/auditor via pointers.

Three pipeline moments (industry pattern):

1. **Index time** — attach stable IDs, doc hash, offsets/page/bbox, pipeline_version, embedding_model.
2. **Generation time** — grounding contract: model may only cite retrieved blocks; structured citation objects preferred over free-text “Source: …”.
3. **Verification time** — post-hoc NLI / faithfulness check that cited span actually supports the claim; regenerate or warn on failure.

Citation patterns (from practitioner writeups):

- **Inline anchors** `[1]` into a citation array (UX-friendly; fragile if anchors are positional only).
- **Structured citation block** with stable `chunk_id`, `doc_id`, quote, score.
- **Span-grounded refs** with character offsets / PDF locators / `doc_hash` (audit-grade).

Managed platforms (e.g., Amazon Bedrock Knowledge Bases `RetrieveAndGenerate`) return `retrievedReferences` tying answer spans to source locations — citation as a platform primitive, not just a prompt request.

### Alternatives & Tradeoffs

| Technique | Strength | Weakness |
| --- | --- | --- |
| Prompt-only “please cite sources” | Cheap | Citation hallucination; cites non-retrieved docs |
| Forced cite-from-provided-IDs + schema validation | Enforceable contract | Needs good chunking; brittle UX if IDs leak |
| Post-hoc sentence→chunk attribution | Works on legacy answers | Semantic similarity ≠ derivation; needs NLI |
| Fine-tuned cite models / Cite-style pretraining | Fewer citation-shaped lies | Costly; domain data needed |
| Show sources list without claim-level links | Easy | User cannot verify which sentence used which source |

Content-addressed chunk IDs (`sha256(canonical_text)`) survive reindex better than auto-increment IDs. Offset-based citations survive *text* edits poorly unless you version the exact artifact injected into the model.

### Necessity

Citations without grounding verification create **false trust** (confident answer + wrong link). Regulated domains (healthcare, finance, education AI tutors) need reproducible evidence; Barnett’s AI Tutor case made “sources list” a product requirement for student verification.

### Industry Practice

- Require **refusal gate** when retrieval confidence / relevance is below threshold before generating an answer.
- Log the **exact trimmed chunk text** used at answer time; citation UI must render that artifact, not a later re-render of the live corpus.
- Azure `GroundednessEvaluator` (1–5 LLM judge) and `GroundednessPro` (Content Safety binary) treat grounding as a first-class eval, independent of fluency.
- Databricks `RetrievalGroundedness` / `judges.is_grounded()` scorers pull retrieved context from traces.
- RAGAS **Faithfulness**: claim decomposition → support check → score = supported_claims / total_claims.

### Concrete Scenario (URL)

AWS Bedrock Knowledge Bases grounded citation pattern (`RetrieveAndGenerate` → `retrievedReferences`): https://aiarch.dev/patterns/grounded-rag  

(Complementary academic grounding: RAGAS Faithfulness docs — https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/faithfulness/ )

### Open Questions

- What citation granularity (chunk vs sentence vs token span) maximizes user trust without crushing latency?
- How to cite multi-hop answers where no single chunk entails the full claim?
- Should parametric knowledge be marked as “model prior” when allowed?

### Sources

- RAGAS Faithfulness: https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/faithfulness/  
- Azure Groundedness evaluator API: https://learn.microsoft.com/en-us/python/api/azure-ai-evaluation/azure.ai.evaluation.groundednessevaluator  
- Databricks RetrievalGroundedness: https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/concepts/judges/is_grounded  
- Attribution & citation overview: https://mbrenndoerfer.com/writing/attribution-and-citation  
- Grounded RAG pattern: https://aiarch.dev/patterns/grounded-rag  

---

## Concept 3 — Corpus Drift and Reindexing Strategy

### Fundamentals

**Corpus drift** = the indexed knowledge diverges from operational truth: documents added/updated/deleted; extraction/chunking/embedding pipeline changes; ACL and retention policies change; temporal validity of facts expires.

Drift produces silent RAG failures that look like FP1/FP2 (stale or missing content) or FP4 (contradictory versions in context). Citations are especially vulnerable: rechunking or re-embedding can invalidate historical `chunk_id` pointers (“citation drift”).

**Reindexing strategy** is the ops plan for when and how to rebuild vector (and sparse) indices:

| Strategy | Description |
| --- | --- |
| Full rebuild | Re-chunk + re-embed entire corpus (needed on embedding-model change) |
| Incremental upsert | Content-hash change detection; upsert/delete affected docs |
| Blue/green index | Build new index alias; flip traffic after eval gate |
| Dual-write / shadow | Serve old index; score new index offline on golden set |
| Temporal / versioned retrieval | Prefer latest `valid_from`/`valid_to`; keep superseded chunks for audit |

Barnett et al.: changing embedding strategy **requires re-indexing all chunks**; chunk size and embedding choice are coupled design decisions.

### Alternatives & Tradeoffs

| Approach | Pros | Cons |
| --- | --- | --- |
| Always full reindex nightly | Simple consistency | Cost; downtime risk; citation ID churn |
| Hash-based incremental | Cheap; fast freshness | Won’t catch embedding-model upgrade needs |
| Reindex only on embedding change + incremental otherwise | Balanced | Two code paths; must detect pipeline_version |
| Keep immutable evidence store + soft “superseded” | Citation integrity | Storage; retrieval must filter superseded by default |

Tradeoff: freshness SLA vs eval gate. Shipping a new chunker without re-running retrieval metrics on a pinned golden set routinely regresses recall@k.

### Necessity

Without drift control, groundedness metrics can stay high while **answer correctness vs world** collapses (faithful to stale docs). Enterprise RAG ownership explicitly includes corpus freshness; otherwise citations lend false authority to outdated policy/pricing/docs.

### Industry Practice

- Pin **`pipeline_version` + `embedding_model` + `chunker_config`** on every stored chunk.
- Use **content-addressed IDs**; on text change, new ID + `supersedes` link.
- Gate production index flips on: retrieval metrics (recall@k / NDCG), sample faithfulness, and spot-check of high-traffic queries.
- Monitor online signals: rising “I don’t know”, rising user thumbs-down, rising contradiction rate in retrieved sets.
- For time-sensitive corpora, add metadata filters (as_of date) rather than hoping embeddings encode recency.

### Concrete Scenario (URL)

Databricks long-context RAG study shows retrieval depth and context packing interact with model effective context — relevant when reindex/rerank changes how many chunks you pack: https://www.databricks.com/blog/long-context-rag-performance-llms  

Citation drift failure mode writeup (immutable evidence / content-addressed IDs): https://medium.com/@npavfan2facts/rag-citations-backfire-when-chunks-keep-changing-850f4336d882  

### Open Questions

- What automated canaries detect embedding-space drift without labeled queries?
- How often should golden sets be refreshed when the corpus itself is the moving target?
- Best practice for legally retaining cited snapshots after source deletion (right-to-be-forgotten vs audit)?

### Sources

- Barnett et al. (embedding change ⇒ full reindex): https://arxiv.org/abs/2401.05856  
- Databricks Long Context RAG Performance: https://www.databricks.com/blog/long-context-rag-performance-llms  
- Cohere (industry stance that large context doesn’t replace RAG freshness/control): commonly cited in Databricks blog discussion thread / related posts  
- Grounded RAG on index ownership: https://aiarch.dev/patterns/grounded-rag  

---

## Concept 4 — RAG vs Long-Context Tradeoffs

### Fundamentals

Two strategies for external knowledge:

1. **RAG** — retrieve a small relevant subset; generate conditioned on that subset.  
2. **Long-context (LC)** — stuff large portions (or all) of a corpus/document into an extended window.

They are **not mutually exclusive**. Databricks (Leng et al., arXiv:2411.03538 / blog) argues long context and RAG are **synergistic**: longer effective windows let RAG include more candidates—but many models still degrade as packed context grows (instruction-following failures, repetition). RULER-style results: **advertised context ≫ effective context**.

Classic failure of naïve LC: **Lost in the Middle** (Liu et al., arXiv:2307.03172) — multi-document QA accuracy U-shaped in evidence position; mid-context evidence under-used. That is exactly the RAG packing problem when *K* is large.

Xu et al. (arXiv:2501.01880) revisit LC vs RAG: LC often wins on Wikipedia-style QA when the corpus fits; summarization-based retrieval can approach LC; chunk RAG lags; RAG retains advantages on dialogue/general queries and when full-corpus stuffing is infeasible.

### Alternatives & Tradeoffs

| Dimension | Prefer RAG | Prefer Long-Context | Prefer Hybrid |
| --- | --- | --- | --- |
| Corpus size | Millions of docs | Single long doc / small corpus that fits | Large corpus + long effective window for top‑N |
| Freshness / ACL | Per-doc access control, incremental update | Harder (must rebuild packed prompts) | Retrieve then pack under policy |
| Cost / latency | Lower tokens per query | High tokens; quadratic attention cost historically | Retrieve broader, pack until quality plateaus |
| Evidence localization | Natural citations | Harder attribution across huge prompts | Retrieve with IDs, pack ranked list |
| Failure mode | Missed retrieval | Lost-in-middle / effective-length collapse | Need joint tuning of *K* and model |

Open-source vs closed models differ: Databricks finds some open models peak ~16k packed tokens while some closed models keep gaining toward ~100k.

### Necessity

Curriculum and production design must kill the false dichotomy “long context replaces RAG.” Cost, ACL, citation, and effective-context limits keep retrieval relevant; LC changes *how much* you retrieve and *how* you order it.

### Industry Practice

- Tune **recall curve vs packed-token quality** per model (Databricks methodology).  
- Put highest-relevance chunks at **beginning and/or end**; avoid burying the answer mid-prompt (Lost-in-the-Middle mitigation).  
- Use LC for **within-doc** reasoning (contracts, transcripts) and RAG for **corpus-scale** search.  
- Re-evaluate packing whenever the generator model changes — effective context is model-specific.  
- Cohere and others publicly argue large windows don’t replace RAG for freshness, cost, and modularity (referenced in Databricks survey of the debate).

### Concrete Scenario (URL)

Databricks engineering blog with empirical curves across ~20 models: https://www.databricks.com/blog/long-context-rag-performance-llms  

Companion paper: https://arxiv.org/abs/2411.03538  

Lost in the Middle (controlled multi-doc QA mimicking RAG): https://arxiv.org/abs/2307.03172  

### Open Questions

- Optimal routing policy: when to retrieve vs stuff-full-doc vs summarize-then-retrieve?
- Does reranking matter less as effective context grows, or more (noise sensitivity)?
- How do agentic multi-step retrieve loops interact with million-token models?

### Sources

- Databricks Long Context RAG Performance: https://www.databricks.com/blog/long-context-rag-performance-llms  
- Leng et al. arXiv:2411.03538: https://arxiv.org/abs/2411.03538  
- Liu et al. Lost in the Middle: https://arxiv.org/abs/2307.03172  
- Long Context vs RAG revisit: https://arxiv.org/abs/2501.01880  
- Barnett et al. (context size lesson in AI Tutor): https://arxiv.org/abs/2401.05856  

---

## Cross-Cutting Debugging Cheat Sheet

| Observed symptom | Likely mode | First measurements |
| --- | --- | --- |
| Answer invents facts; sources empty/irrelevant | Recall or ranking | recall@k, retrieval relevance judge |
| Right doc in corpus, wrong answer | Ranking or grounding | MRR/NDCG; manual top‑k inspection |
| Right chunk in prompt, wrong/partial answer | Generation-grounding | Faithfulness, completeness, position ablation |
| Correct yesterday, wrong after doc update | Corpus drift | Index freshness, version skew, dual-index eval |
| Quality drops as *K* increases | Lost-in-middle / noise | Context precision, faithfulness vs *K* sweep |

---

## Master Source List (Week 09)

1. https://arxiv.org/abs/2401.05856 — Seven Failure Points of RAG  
2. https://arxiv.org/html/2401.05856v1 — HTML full text  
3. https://arxiv.org/abs/2307.03172 — Lost in the Middle  
4. https://www.databricks.com/blog/long-context-rag-performance-llms — Long context × RAG  
5. https://arxiv.org/abs/2411.03538 — Long Context RAG Performance of LLMs  
6. https://arxiv.org/abs/2501.01880 — Long Context vs RAG evaluation revisit  
7. https://jxnl.co/writing/2025/05/19/there-are-only-6-rag-evals/ — Six RAG evals  
8. https://hamel.dev/blog/posts/evals-faq/index.html — Hamel evals FAQ  
9. https://learn.microsoft.com/en-us/azure/foundry/concepts/evaluation-evaluators/rag-evaluators — Azure RAG evaluators  
10. https://docs.nvidia.com/nemo/microservices/latest/evaluate/flows/rag.html — NVIDIA NeMo RAG eval  
11. https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/faithfulness/ — Faithfulness  
12. https://aiarch.dev/patterns/grounded-rag — Grounded citations pattern  
