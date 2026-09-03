# Chapter 9 — RAG failure taxonomy

> **Phase 2 — RAG Systems**  
> **Compilation status:** COMPLETE  
> **Source of truth:** `research/phase-2/week-09-rag-failure-taxonomy/`  
> **Syllabus Build:** On the Week 7–8 logged RAG stack, **do not add a new retriever**. Instead: (1) **deliberately break** the pipeline at known loci (missing gold in corpus; gold below `k`; consolidator drop; noisy packed window; stale doc version; gold buried mid-prompt); (2) **classify** each broken run with canonical mode (recall / rank / ground), Barnett FP (1–7), and the Jason Liu Q–C–A relationship that failed; (3) keep a **portfolio debugging log** joined on `retrieval_id` from Weeks 7–8. The log is the artifact — Week 10 turns it into a metric cookbook.

---

## Chapter framing

Week 9 is the **diagnosis** week of Phase 2 RAG. Weeks 6–8 produced chunks, a hybrid candidate set, and a reranked packed window. This week answers: **when the answer is wrong, which stage broke?** The syllabus spine is not a new architecture. It is a **fault-injection + classification** protocol plus a **portfolio debugging log**.

Barnett, Kurniawan, Thudumu, Brannelly, Abdelrazek (*Seven Failure Points When Engineering a Retrieval Augmented Generation System*, arXiv:**2401.05856**, CAIN 2024) give the empirical catalogue. Three case studies (Cognitive Reviewer, AI Tutor, BioASQ: ~4k OA PDFs, 1,000 expert Q/A, GPT-4 + OpenAI Evals, then manual inspection) produced **seven failure points** on the Index/Query graph. Two engineering takeaways:

1. **Validation is only feasible during operation** — real query distributions and unknown inputs appear at runtime. Offline G-Eval-style methods need labelled Q/A that often do not exist when you first index unstructured docs.  
2. **Robustness evolves rather than being designed in** — chunk size, embedding, retrieval, consolidation, context size, and prompts are continuously calibrated.

Teaching compression of those seven points into **three canonical modes** that match component ownership:

| Canonical mode | Pipeline locus | Core question | Primary owner |
| --- | --- | --- | --- |
| **Recall failure** | Corpus, chunk/embed, filters, stage-1 | Was the needed evidence ever **eligible** to be returned? | Search / data |
| **Ranking / context-assembly failure** | Rank, rerank, consolidator, pack order | Did useful evidence land **high enough** and **survive** into the prompt? | Search / prompt packing |
| **Generation-grounding failure** | Reader / LLM | Given usable context, did the model **extract, stay faithful, and answer completely**? | Prompt / model / schema |

Jason Liu (*There Are Only 6 RAG Evals*, still public at jxnl.co, 2025-05-19) supplies the **metric graph**: three variables Question (Q), Context (C), Answer (A) and six conditionals. Hamel Husain (hamel.dev evals FAQ) maps that graph onto ops: **Tier 1 IR metrics for retrieval first**, then generation judges **validated against humans**. Azure Foundry and NVIDIA NeMo both split **process (retrieval)** evaluators from **system (groundedness / relevance / completeness)** evaluators — the same cut.

Liu et al. (*Lost in the Middle*, arXiv:**2307.03172**) is the packing failure that sits on the rank/grounding border: gold can be **in the prompt** and still unused. Databricks (Leng et al., arXiv:**2411.03538**) shows long context does not retire RAG; it changes **how much** you retrieve and **how models fail** past an effective window.

**This week’s artifact is a log, not a dashboard.** Join on `retrieval_id` from Weeks 7–8. Label every broken run. Week 10 turns labels into metric recipes.

Do not start Week 9 by swapping Cohere for BGE. If gold is absent from `fetch_k`, that is recall. If gold is in `fetch_k` but not packed, that is ranking/assembly. If gold is packed and the model invents, that is grounding. Do not skip this week for “we’ll just look at end-to-end answer accuracy.” E2E accuracy **confounds** recall, rank, and grounding.

Read the concepts in order. Each section’s **Worked Example** and **Apply It** assume the same flagship service (working title: Deployment Copilot) on the Week 7–8 logged stack — hybrid candidates, rerank ids, packed positions — with taxonomy labels **appended**, not overwritten.

**Default path (synthesis):** keep Week 7 candidate logs and Week 8 `rerank.ids[]` / `packed_position` → run a **fault-injection matrix** (one fault per cell) on a pinned golden set → for each failure: first ask “was gold **eligible**?” then “did it **survive packing**?” then “did the reader **use** it?” → treat “I don’t know” as **success** on FP1 (missing content) and **bug** on FP2 (gold existed, missed top-k) → pin evidence snapshots so citations without a stored snapshot are a separate failure (citation drift) even when the answer is right.

**Classification cheat sheet** — walk **in order**; stop at the first yes:

1. **Gold not in corpus / not visible under ACL / wrong chunker so the span never existed?** → **Recall** (FP1). Success = refusal.  
2. **Gold in corpus, not in `fetch_k`?** → **Recall** (stage-1 miss; still FP2-adjacent if “all docs ranked in theory”).  
3. **Gold in `fetch_k`, not in packed window?** → **Ranking / assembly** (FP2 near-miss or FP3).  
4. **Gold packed, mid-position, model ignores?** → **LITM / FP4** (log `packed_position`).  
5. **Gold packed, model adds unsupported claims?** → **Grounding** (FP4; A\|C).  
6. **Faithful but wrong shape / specificity / missing siblings?** → **Grounding** (FP5–7).  
7. **Was right last week after a corpus or pipeline change?** → **Drift** (re-run 1–6 on both index aliases).

---

### Three canonical failure modes (recall / ranking / generation-grounding)

* **Fundamentals:**  
  Production RAG failures cluster into **three diagnosable layers**. They map onto Barnett et al.’s Index/Query graph (arXiv:2401.05856), Jason Liu’s Q–C–A triangle, and the TruEra/RAGAS “RAG triad” (context relevance, groundedness, answer relevance).

  **Recall failure — “Was the evidence ever eligible?”**  
  The answerable span is **not in the candidate set** the retriever can return. Causes:

  - **FP1 Missing Content** (Barnett): the question cannot be answered from available documents. Happy path: “Sorry, I don’t know.” Failure: the system is **fooled** into answering from parametric memory or near-topic chunks when the question is *related* but unanswerable.  
  - Chunking/embedding so similarity never fires (Barnett §3.1: chunks too small → some questions unanswerable; too long → noise). Changing embedding **requires re-indexing all chunks**.  
  - Metadata / ACL / tenant filters emptying the pool (looks like “RAG missed it”; Week 7 pgvector under-scan is the same shape).  
  - Gold outside `fetch_k` entirely — Barnett **FP2** when K is a performance cutoff: “in theory all documents are ranked; in practice top-K.” If gold never enters the retrieved list, Jason Liu **C|Q** is already dead. Hamel: **absence blindness** — teams obsess over generation while retrieval never found the passage.

  Recall is **not** “the user didn’t like the answer.” It is a **set-membership** question against the corpus and the retrieval cutoff.

  **Ranking / context-assembly failure — “Did evidence survive into the window?”**  
  Relevant chunks exist in the hit list but sit **below the cutoff**, get demoted by a weak reranker, or are discarded by a **consolidator** that must fit a token/rate budget.

  - **FP2 Missed Top Ranked Documents:** answer is in the document; rank was not high enough to return. K chosen for latency/cost.  
  - **FP3 Not in Context — consolidation strategy limitations:** documents **were retrieved** from the DB but **did not make it into the prompt**. Barnett: token limits and rate limits force a reduction/chaining strategy. This is the stage Week 8 packing owns.  
  - **Lost in the Middle** (Liu et al., arXiv:2307.03172) compounds assembly: even when chunks **enter** the prompt, **mid-context** evidence is under-used. That can present as FP4 (not extracted) even though the engineering bug was **order / k**, not the reader weights.

  Jason Liu **C|Q** (context relevance) fails when packed C is off-need; **Q|C** (answerability) fails when packed C cannot support a satisfactory answer even if some retrieved-but-dropped chunk could.

  **Generation-grounding failure — “Given usable C, did the reader behave?”**  
  The prompt contains (or nearly contains) the answer, but the LLM:

  - **FP4 Not Extracted** — answer present in context; model fails to extract. Typical cause: **too much noise or contradicting information** (Barnett). LITM is a special case of “present but unused.”  
  - **FP5 Wrong Format** — asked for table/list; model ignored the instruction.  
  - **FP6 Incorrect Specificity** — too vague or too specific vs designer/user need (AI Tutor: teachers want **educational content with** the answer, not just the fact). Also: users ask too generally.  
  - **FP7 Incomplete** — not incorrect, but missing information that **was in context**. Example: “key points in documents A, B, and C” — better asked separately (Barnett).

  Jason Liu **A|C** = faithfulness/groundedness (answer restricts itself to C). **A|Q** = answer relevance. **C|A** = context support coverage (does C support every claim in A — complementary to faithfulness). **Q|A** = self-containment (can you infer the question from the answer).

  Hamel maps this to ops: **debug retrieval with IR metrics first**; then generation via error analysis and **validated** judges. Domain modes (adult vs pediatric dose; jurisdiction) are **extra** metrics found only by reading traces — not a reason to skip the 3-mode cut.

  **Barnett → 3-mode map (teaching table):**

  | Barnett FP | 3-mode | Jason Liu primary | Azure analogue | NVIDIA analogue |
  | --- | --- | --- | --- | --- |
  | FP1 Missing Content | Recall | Q\|C (unanswerable); C\|Q | Retrieval fail + refusal policy | recall@k = 0; do not punish faithfulness |
  | FP2 Missed top ranked | Recall if outside all retrieved; else Ranking | C\|Q at production k | Document Retrieval NDCG / fidelity / holes | `retriever_recall_k`, `retriever_ndcg_cut_k` |
  | FP3 Not in context | Ranking / assembly | C packed ≠ C retrieved | Process vs system split | Compare retriever metrics vs faithfulness on **packed** C |
  | FP4 Not extracted | Grounding (or LITM) | A\|C | Groundedness 1–5; Groundedness Pro binary | `rag_faithfulness`, `response_groundedness` |
  | FP5 Wrong format | Grounding | A\|Q + schema | often code assertion, not LLM judge | format tests |
  | FP6 Incorrect specificity | Grounding | A\|Q | Relevance | `rag_answer_relevancy` |
  | FP7 Incomplete | Grounding | C\|A; completeness | Response Completeness (recall of answer vs gold) | completeness / context_recall |

  Azure’s own wording: **Groundedness = precision** of the response (no content outside grounding context); **Response Completeness = recall** of the response vs expected information. That is FP4 vs FP7 in metric clothing.

  BioASQ scenario (Barnett §4.3): indexed **4017** open-access BioASQ PDFs; **1000** expert questions; OpenAI Evals plus manual inspection. Automated evaluation was **more pessimistic** than a non-expert human rater. AI Tutor lessons: larger context helped extraction (8K vs 4K) **contrary** to some GPT-3.5 LITM reports; filename + chunk number in context helped the reader; continuous calibration because inputs are unknown at runtime.

* **The Alternatives:**  

  | Diagnostic grain | Pros | Cons |
  | --- | --- | --- |
  | “Hallucination” umbrella | Communicates to execs | Hides index vs retriever vs prompt |
  | 7 FPs only | Matches the paper | Overlap; consolidator vs rank |
  | **3-mode + FP subtype** (syllabus default) | Matches owners and vendor evaluator split | Need logging at each hop; consolidator bugs can look like rank *or* ground |
  | 6 Q–C–A only | Exhaustive pairwise | Weak on corpus/ACL/drift/index version |
  | RAGChecker / ARES / 20-metric suites | Fine dashboards | Jason Liu: ask which of the 6 relations they measure |
  | E2E answer accuracy only | One number for slides | Confounds recall, rank, and grounding |

  | Fault-injection style | Pros | Cons |
  |-----------------------|------|------|
  | **One fault per cell** (syllabus) | Causal attribution; portfolio-ready | Slow; needs pinned golden set |
  | Production error analysis only | Real distribution (Barnett: validation in operation) | Confounded; no counterfactual |
  | Synthetic Q from chunks only | Cheap qrels (Hamel reverse generation) | Misses user wording / unanswerable queries (FP1) |

  **k tradeoff (ops):** raising *K* reduces FP2 misses and can raise Databricks-style “more docs help **until** they don’t”; it increases noise → more FP4, token cost, and LITM. Hybrid + CE rerank improves ranking (Week 8) but adds a model to evaluate. Refusal gates reduce FP1-shaped hallucinations but raise false refusals on FP2.

  The syllabus selects **canonical 3-mode + Barnett FP as subtype** because it matches component ownership and the Azure/NVIDIA process-vs-system evaluator split.

* **Failure Modes:**  
  - Teams “fix the prompt” when the doc was never indexed (FP1) or never ranked into top-K (FP2).  
  - “I don’t know” is treated as always-bad — it is **correct** on missing content and **wrong** when gold existed.  
  - **Faithfulness 0.9 on a recall miss:** the model faithfully recited irrelevant C — **not** a generator win.  
  - **E2E accuracy dip after raising k:** ranking/LITM, not “the new embedding is worse,” unless recall@k also moved.  
  - **OpenAI Evals red, human green (BioASQ):** do not auto-close FP4 from a pessimistic judge (Hamel: calibrate TPR/TNR).  
  - **Judge uses live corpus instead of packed snapshot:** you evaluate a different C than the model saw.  
  - Week 10 metrics get attached to the wrong stage (faithfulness on a recall miss is a **false** generator bug).

* **Average vs. Strong Engineer:**  
  **Average:** screenshot the wrong answer; blame the LLM; collapse all errors into “hallucination”; change temperature or the system prompt. No candidate log. No gold IDs.  
  **Strong:** Hamel sequence — (1) qrels / synthetic reverse-generated query–doc pairs; Recall@k / Precision@k / MRR on **production k** and **fetch_k**; (2) only then LLM judges for C|Q, A|C, A|Q. Azure: Document Retrieval when you have graded `retrieval_ground_truth` (fidelity, NDCG, XDCG, max relevance, **holes** = unlabeled docs); Retrieval evaluator (1–5) when you lack qrels. NVIDIA RAG flow: `retriever_recall_5/10` + `retriever_ndcg_cut_5/10` type `pytrec_eval`; `rag_faithfulness` / `rag_answer_relevancy` type `ragas` with `judge_llm`. Databricks Agent Evaluation attributes failing rows to chunk relevance / context sufficiency / groundedness / relevance-to-query.  
  **FDE bar:** walk a trace through the ordered decision list; name FP1–FP7 without notes; distinguish packed C from retrieved C (FP3); cite Jason Liu page as **still public**; add one **domain** failure mode from error analysis rather than inventing 20 generic metrics; refuse to report a single E2E % as the Week 9 deliverable.

* **Worked Example:**  
  Pin a golden set of ~30–50 queries with **supporting `chunk_id`s** (and an **unanswerable** slice for FP1). Run injection cells A–G on Deployment Copilot (one change per row; restore after each):

  | Cell | Injection | Expected canonical | Expected Barnett | Expected Q–C–A break |
  |------|-----------|--------------------|------------------|----------------------|
  | A | Delete gold doc from index (or ACL-deny the tenant) | Recall | FP1 | C\|Q weak; Q\|C unanswerable — refusal should pass |
  | B | Keep gold; set packed `k` below gold’s fused/rerank rank | Ranking | FP2 | C\|Q fails at production k; recall@fetch_k still high |
  | C | Retrieve gold at rank 2; consolidator/token budget drops it | Ranking / assembly | FP3 | C exists in retriever span, absent from prompt C |
  | D | Pack gold + contradicting/noisy neighbors; gold mid-list | Grounding (± LITM) | FP4 | A\|C fails; gold present |
  | E | Ask for a JSON list; prompt allows prose | Grounding | FP5 | A\|Q / format contract |
  | F | Teacher wants unit-week citation; model returns generic fact | Grounding | FP6 | A\|Q specificity |
  | G | Multi-doc “key points in A,B,C”; model answers A only | Grounding | FP7 | C\|A coverage; completeness |

  Paper-shaped walkthrough — query: “Define pseudotumor cerebri. How is it treated?” (Barnett sample):

  - If the OA PDF was never ingested → FP1 / recall; refusal is correct.  
  - If ingested but cosine put it at rank 40 and `k=8` → FP2 / ranking; recall@40 high, recall@8 zero.  
  - If retrieved then consolidator dropped it for token budget → FP3; retriever span has gold, prompt does not.  
  - If packed with contradictory review papers → FP4 / A\|C.  
  - If the gold list of treatments is in C but the model returns one drug → FP7.

  Append-only portfolio debugging log (join key `retrieval_id` — **do not overwrite** candidate arrays):

  | Field | Why |
  |-------|-----|
  | `retrieval_id` | Week 7–8 join |
  | `query`, `query_slice` | factoid / multi-hop / unanswerable / vocab-gap |
  | `gold_chunk_ids[]`, `gold_in_corpus` | FP1 vs FP2 gate |
  | `stage1.ranks{}`, `fetch_k` | recall eligibility |
  | `rerank.ids[]`, `rerank.ranks{}` | FP2 |
  | `packed.ids[]`, `packed_position`, `packed_text_hash` | FP3 + LITM |
  | `answer`, `citations[]`, `evidence_snapshot_hash` | grounding + citation drift |
  | `canonical_mode`, `barnett_fp`, `qca_failed[]` | taxonomy labels |
  | `pipeline_version`, `embedding_model`, `chunker_config`, `index_alias` | drift |
  | `injection_cell` | A–I or `prod` |
  | `notes` | one-sentence human rationale (Hamel journaling) |

* **Apply It:**  
  1. Keep Week 7–8 candidate / rerank / packed logs; **append** taxonomy fields — never overwrite stage-1 arrays.  
  2. Pin a golden set (~30–50) with supporting `chunk_id`s plus an unanswerable slice.  
  3. Run the fault-injection matrix (cells A–G at minimum), one fault per cell, restore after each.  
  4. For every broken run, label `canonical_mode`, `barnett_fp`, and `qca_failed[]` using the ordered cheat sheet.  
  5. Treat “I don’t know” as success on FP1 and as a bug on FP2.  
  6. Instrument IR metrics (recall@k / NDCG / MRR) on `fetch_k` and production packed k **before** faithfulness judges.  
  7. Do not ship a single E2E accuracy number as the Week 9 deliverable — the classified log is the artifact.

---

### Citation and grounding techniques

* **Fundamentals:**  
  **Grounding** = every **material claim** in the answer is entailed by retrieved evidence, **or** the system emits an explicit refusal. **Citation** = exposing that entailment to a user or auditor via pointers. Citation without grounding verification is **false trust** (confident prose + a link that does not support the sentence).

  Jason Liu **A|C** (faithfulness/groundedness) is the claim-level property. Azure names the same split: Groundedness = **precision** (nothing outside C); Response Completeness = **recall** (nothing critical missing vs gold). RAGAS **Faithfulness** operationalizes A|C as:

  \[
  \text{Faithfulness} = \frac{\#\text{ claims in the response supported by retrieved context}}{\#\text{ claims in the response}}
  \]

  Pipeline: decompose answer into claims → NLI/support check vs C → ratio. RAGAS docs example: “Einstein born in Germany” supported; “born 20 March 1879” not supported when C says 14 March → 0.5.

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

* **The Alternatives:**  

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

  Content-addressed chunk IDs survive **reindex of the same bytes**. Auto-increment IDs churn. Offset-based citations survive **text** edits poorly unless you version the **exact artifact** injected into the model (`packed_text_hash` / evidence snapshot). That is the bridge to corpus drift.

  Granularity tradeoff: token-span citations maximize audit and crush latency; chunk-level is the usual product default; sentence-level is the RAGAS claim unit.

* **Failure Modes:**  
  - **Citation hallucination:** `[12]` not in retrieved ID set — catch with a **code** assertion (Hamel: not everything needs a judge).  
  - **Stale render:** UI opens current docs.corp/policy.html; model saw `policy.html@hash_a`. After legal edits, the quote is gone → **citation drift**.  
  - **Faithfulness 1.0, completeness 0:** FP7 — all claims supported, gold treatments missing. Azure completeness evaluator needs `ground_truth`.  
  - **Groundedness vs Groundedness Pro disagreement:** 1–5 judge passes “reasonable paraphrase”; Pro fails strict consistency. Pick one definition per product policy.  
  - **Judge context ≠ packed context:** concatenated `\n\n` Azure `context` string must be the **same** string the generator saw (Foundry docs: concatenate chunks with a separator).  
  - **Parametric true fact not in C:** A|C fails if policy is “context-only”; passes if hybrid-allowed. Label the policy on the log.  
  - A correct answer with a wrong citation is a **grounding UX failure** even if A|Q looks fine; a wrong answer with a pretty citation teaches the user to trust the pointer.

* **Average vs. Strong Engineer:**  
  **Average:** “Answer using the context. Cite sources.” No ID allowlist. Sources panel lists cosine top-4 titles.  
  **Strong:** Allowlist citation IDs = packed IDs. Store **evidence snapshots** (raw chunk text at answer time) for the citation UI. Refusal when C|Q / retrieval metrics fail. Independent evals: Azure Groundedness (`response`, `context`, optional `query`) + Relevance (`query`, `response`) + Completeness (`ground_truth`, `response`). Databricks: `mlflow.trace(span_type="RETRIEVER")` returning `Document(id, page_content, metadata)` then `RetrievalGroundedness` scorer. RAGAS Faithfulness on the same snapshot; do not re-retrieve at eval time. Hamel: if citation format is the failure, a **targeted** judge or a schema test; calibrate against humans before trusting dashboards.  
  **FDE bar:** distinguish grounding (entailment) from citation (pointer); demo a **false-trust** example (unsupported claim + real URL); quote Azure precision/recall split; show a code check that every `citation.chunk_id ∈ packed.ids`.

* **Worked Example:**  
  Curriculum analogue of Bedrock Knowledge Bases `RetrieveAndGenerate` / `retrievedReferences`. Deployment Copilot generator returns JSON:

  ```json
  {
    "answer": "...",
    "citations": [
      {"chunk_id": "sha256:…", "quote": "…", "start": 120, "end": 188}
    ],
    "refused": false
  }
  ```

  Verifier pipeline: (1) IDs ⊆ packed set; (2) `quote` is a substring of snapshot; (3) RAGAS/Azure groundedness on claims vs snapshots; (4) if `gold_chunk_ids` not subset of packed → do not blame the generator. Azure sample jsonl uses `query`, `context`, `response` — the **process** Retrieval evaluator uses `query`+`context`; Groundedness uses `response`+`context`.

* **Apply It:**  
  1. Emit structured citation objects (`chunk_id`, quote, offsets) — not free-text “Source: …”.  
  2. Enforce allowlist: every `citation.chunk_id ∈ packed.ids` with a code assertion.  
  3. Persist an evidence snapshot (`packed_text_hash` / raw chunk text) at answer time; render citations from the snapshot, not a live corpus fetch.  
  4. Gate generation on C|Q / retrieval confidence — refuse rather than invent on FP1.  
  5. Run groundedness (A|C) and completeness separately; do not treat faithfulness 1.0 as “done” when FP7 is open.  
  6. Evaluate judges on the **same** packed C the model saw; never re-retrieve at eval time.

---

### Corpus drift and reindexing strategy

* **Fundamentals:**  
  **Corpus drift** = indexed knowledge diverges from **operational truth**. It is not one bug. It is several clocks running at different rates:

  | Clock | What moves | How it shows up |
  |-------|------------|-----------------|
  | Document clock | Adds / updates / deletes in the CMS or object store | FP1/FP2-shaped misses; contradictory versions in C (FP4) |
  | Pipeline clock | Chunker, overlap, embedding model, metadata extractors | Recall collapse after “we upgraded embeddings”; **citation ID churn** |
  | Policy clock | ACL, retention, residency, tenant partitions | Gold exists globally, invisible to this user (false FP1) |
  | Fact clock | Prices, policies, on-call rotas expire | Faithful answers to **superseded** chunks (A\|C high, world-correctness low) |

  Barnett §3.1: **changing the embedding strategy requires re-indexing all chunks**; chunk size and embedding choice are coupled. Lesson table: implement a **RAG pipeline for configuration** — calibrate chunk size, embedding, chunking, retrieval, consolidation, context size, and prompts together. Second lesson: **testing performance characteristics are only possible at runtime**; labelled Q/A often arrive after indexing.

  **Citation drift** is the user-visible form: historical `chunk_id` / offsets no longer point at the bytes the model quoted. Rechunking or re-embedding without an **immutable evidence store** invalidates the sources panel even when answers remain plausible.

  **Reindexing strategy** is the ops plan for when and how to rebuild dense (and sparse) indices:

  | Strategy | Description | When |
  |----------|-------------|------|
  | **Full rebuild** | Re-chunk + re-embed entire corpus | Embedding-model change; chunker change; corruption |
  | **Incremental upsert** | Content-hash change detection; upsert/delete affected docs | Normal CMS edits |
  | **Blue/green index** | Build new index; flip alias after eval gate | Any risky pipeline_version |
  | **Dual-write / shadow** | Serve old; score new offline on golden set | Embedding A/B |
  | **Temporal / versioned retrieval** | `valid_from` / `valid_to`; keep superseded chunks for audit | Policies, prices, legal |
  | **as_of filter** | Query-time metadata, not “hope embeddings encode recency” | Time-travel Q&A |

  Databricks long-context RAG study (Leng et al., blog + arXiv:2411.03538) is relevant even though it is not a drift paper: **retrieval depth and context packing interact with the generator**. A reindex that changes chunk size or overlap changes how many chunks you pack for a token budget — you must **re-sweep k** and LITM position, not only recall@k.

  Hamel on “RAG is dead”: retrieval is not dead; **naive single-vector** may be. Drift control still applies to hybrid, ColBERT, and agentic search — the **evidence store** and **index alias** remain the source of truth.

* **The Alternatives:**  

  | Approach | Pros | Cons |
  | --- | --- | --- |
  | Full reindex nightly | Simple consistency | Cost; downtime; citation ID churn if IDs are positional |
  | Hash-based incremental only | Cheap freshness | Misses embedding-model upgrades; won’t catch silent chunker bugs if hash is on **source file** not **chunk text** |
  | Incremental + full on `pipeline_version` bump | Balanced | Two code paths; must thread version through logs |
  | Immutable evidence store + `supersedes` links | Citation integrity; audit | Storage; default retrieval must **filter superseded** |
  | Always serve latest blob, citations are URLs | Simple UX | False trust after edits |
  | Skip eval gate on index flip | Fast SLA | Recall@k regressions ship (Barnett: continuous calibration) |

  **Freshness SLA vs eval gate:** shipping a new chunker without re-running retrieval metrics on a **pinned** golden set routinely regresses recall@k. Conversely, freezing the index while the CMS moves produces silent FP1.

  Golden-set drift is the sibling problem: if the **corpus is the moving target**, last month’s qrels point at deleted chunks. Refresh labels on a cadence; keep a **frozen eval snapshot** of corpus+index for regression (separate from production freshness).

* **Failure Modes:**  
  - Without drift control, **groundedness metrics stay high** while **answer correctness vs the world** collapses — the system is faithful to yesterday’s policy PDF.  
  - **Embedding upgrade, partial reembed:** mixed vector spaces; cosine is meaningless; looks like a sudden recall crater.  
  - **Delete in CMS, tombstone missing in vector DB:** retriever cites a ghost; generation may still quote snapshot or hallucinate around a stub.  
  - **Right-to-be-forgotten vs audit:** legally drop source but keep cited snapshots — product/legal design, not an embedding trick.  
  - **ACL change without re-filter:** tenant B sees tenant A chunks (not a quality metric; still a Week 9 log field).  
  - **Blue/green flip without alias atomicity:** mixed k from two chunkers in one request.  
  - **Canary only on E2E accuracy:** misses retrieval holes Azure would call `holes` (unlabeled) or fidelity drop.  
  - Citations lend **false trust** to outdated pricing, medical doses, or course weeks (Barnett AI Tutor: “topics in week 6” is a time-indexed question).

* **Average vs. Strong Engineer:**  
  **Average:** cron “reindex all” Sunday night; IDs = filename + integer; no `pipeline_version`; citations are live URLs.  
  **Strong:** Pin `pipeline_version` + `embedding_model` + `chunker_config` on every stored chunk (Week 6 metadata). Content-addressed IDs; on text change, **new ID** + `supersedes` link; retrieval filter `superseded=false` by default. Gate production alias flips on: recall@k / NDCG (same k as prod), sample faithfulness on snapshots, spot-check **high-traffic queries**. Online signals: rising “I don’t know,” thumbs-down, contradiction rate in retrieved sets, Azure Document Retrieval **fidelity** drop. Time-sensitive corpora: metadata `as_of` / `valid_to` filters. Dual-index eval: old vs new alias on the **same** golden queries (Week 8 delta protocol reused). Log `index_alias` on every `retrieval_id` so Week 9 taxonomy can split “model change” from “index change.”  
  **FDE bar:** explain why embedding change ⇒ **full** reembed (Barnett); draw blue/green; refuse to debug “quality drop Monday” without `pipeline_version` and content hashes; distinguish **faithful-stale** from **hallucination**.

* **Worked Example:**  
  Injection **cell H**: update a policy PDF in object storage; **do not** reindex. A Deployment Copilot query that was correct last week now returns the old hash. Labels: canonical **recall** (stale content = missing *current* content), Barnett **FP1-like**, Jason C|Q measured against **new** truth. Groundedness vs **packed old C** may still be 1.0 — that is the teaching point.

  Databricks DocsQA in the long-context study uses **real user questions** against **public Databricks documentation** — a corpus that itself drifts as docs ship. Their experimental chunking (512 tokens, stride 256, `text-embedding-3-large`, FAISS IndexFlatL2) is a **pinned pipeline**; changing any knob is a new index.

* **Apply It:**  
  1. Stamp every chunk with `pipeline_version`, `embedding_model`, `chunker_config`, and content hash.  
  2. Use content-addressed `chunk_id`s; on text change emit a new ID + `supersedes` link; default retrieval filters `superseded=false`.  
  3. Prefer incremental upsert for CMS edits; **full** reembed on embedding-model or chunker change (Barnett).  
  4. Flip production via blue/green alias only after dual-index eval on the pinned golden set (recall@k / NDCG + sample faithfulness).  
  5. Log `index_alias` on every `retrieval_id`; run cell H (update source, skip reindex) and label faithful-stale separately from hallucination.  
  6. Keep a frozen eval corpus+index snapshot for regression while production stays fresh.

---

### RAG vs long-context tradeoffs

* **Fundamentals:**  
  Two strategies for external knowledge:

  1. **RAG** — retrieve a small relevant subset; generate conditioned on that subset (Lewis et al. 2020 lineage; Barnett: embeddings → top-k → consolidator → reader).  
  2. **Long-context (LC)** — stuff large portions (or all) of a corpus/document into an extended window.

  They are **not mutually exclusive**. Databricks (Quinn Leng, Jacob Portes, Sam Havens, Matei Zaharia, Michael Carbin; blog 2024-08-12; paper arXiv:**2411.03538**) argues long context and RAG are **synergistic**: longer **effective** windows let RAG include more candidates — but **most models degrade after a context size**. Their headline findings from **>2,000 experiments** on 13 models × four datasets (Databricks DocsQA, FinanceBench, HotPotQA, Natural Questions):

  - Retrieving **more** documents can help: higher chance the right information is in the prompt; modern LC models can use that — **until they don’t**.  
  - Longer context is **not always optimal**: Llama-3.1-405B performance started to decrease after **32k** tokens; GPT-4-0125-preview after **64k**; only a few models stayed consistent across all datasets.  
  - Models **fail differently** at long context: copyright refusals, “always summarize the context,” instruction-following collapse — often a lack of long-context post-training, not a single U-curve.

  **Advertised context ≫ effective context** (they cite **RULER**). Chip Huyen (public 2023 open-challenges post): **context length ≠ efficient context use**; Lost in the Middle is the prompt-construction example.

  **Lost in the Middle** (Liu et al., arXiv:2307.03172, TACL 2024): controlled **multi-document QA** (RAG analogue) — question + *k* Wikipedia passages, **exactly one** gold, *k−1* distractors from Contriever; permute **gold position** and *k*. Accuracy often **U-shaped** (primacy + recency). Extreme: **GPT-3.5-Turbo** with gold in the **middle** can fall **below closed-book 56.1%**. Extended-context models are **not necessarily** better at *using* context than shorter siblings.

  Open-domain case study: retriever-reader on NQ-Open; **performance saturates long before retriever recall saturates**. **50 docs instead of 20** only marginally improved (~**1.5%** GPT-3.5-Turbo, ~**1%** Claude-1.3) while the retriever was still recovering more gold. Extra retrieved docs ≠ extra **used** docs.

  Taxonomy placement: LITM is a **ranking/assembly + grounding border** failure. Gold **is** in C (not FP2/FP3) but the reader behaves like **FP4 Not Extracted**. Log `packed_position`. Week 8 mitigation: rerank to **5–10**, optionally `LongContextReorder` (edges). Week 9: **injection cell I** (gold at mid packed position).

  Barnett AI Tutor lesson **conflicts on GPT-4-class 8K vs 4K** (“larger context got better results… contrary to prior work with GPT-3.5 (Liu et al.)”). Teaching point: **do not** treat 2023 GPT-3.5 U-curves as 2026 SOTA; **do** treat position as an **eval slice**. Databricks shows the modern restatement: more context helps **then** hurts, model-specifically.

  **LC vs RAG revisit** (Xu et al., arXiv:2501.01880): LC often wins on Wikipedia-style QA when the **corpus fits**; summarization-based retrieval can approach LC; naive chunk RAG lags; RAG retains advantages on **dialogue / general queries** and when full-corpus stuffing is **infeasible**. Use as a counterweight to “always RAG” and to “LC replaces RAG.”

  Hamel FAQ (document processing vs RAG): even if a document **fits**, splitting can still help; models are sensitive to distraction; **middle under-attended**; if cost/latency hurts, **filter** before stuffing. “RAG is dead” discourse targets **naive vector DBs for coding agents**, not retrieval-as-such — Claude Code still retrieves, via **agentic search**.

* **The Alternatives:**  

  | Dimension | Prefer RAG | Prefer Long-Context | Prefer Hybrid |
  | --- | --- | --- | --- |
  | Corpus size | Millions of docs | Single long doc / small KB that fits | Large corpus + long effective window for top-N |
  | Freshness / ACL | Per-doc ACL, incremental update | Rebuild packed prompts; hard to un-see a doc | Retrieve then pack under policy |
  | Cost / latency | Fewer tokens per query | High tokens; historically quadratic attention | Retrieve broader, pack until quality plateaus (Databricks sweep) |
  | Evidence localization | Natural citations | Attribution across huge prompts | Retrieve with IDs, pack ranked list |
  | Failure mode | Missed retrieval (FP1–3) | LITM / effective-length collapse / weird refusals | Joint tune of *K* and model |
  | Citations | Snapshot-friendly | Easy to lose span grounding | IDs in packed subset |

  Open vs closed (Databricks): some open models peaked ~**16k** packed tokens; some closed models kept gaining toward ~**100k** — **re-evaluate packing whenever the generator changes**.

  | Anti-pattern | Why it fails the taxonomy |
  |-------------|---------------------------|
  | “128k so k=40 is free” | Token $ + LITM + Databricks decrease-after-N |
  | Dump top-50 cosine hits | Week 8: maximize retriever recall then **minimize** what the LLM sees (Pinecone restatement of Liu) |
  | LC-only on a million-doc corpus | Infeasible; ACL; drift |
  | RAG-only on a 20-page contract the model can hold | Extra retrieval miss risk; Hamel: still consider distraction |

  Curriculum and production design must kill the false dichotomy **“long context replaces RAG.”** Cost, ACL, citation, freshness, and **effective**-context limits keep retrieval relevant. LC changes **how much** you retrieve and **how you order it**, not whether you need a failure taxonomy.

* **Failure Modes:**  
  - **Quality drop as k increases:** cell I / Databricks decrease region — not necessarily a worse embedding.  
  - **Copyright refusal / summarize-only** (Databricks deep dives): looks like FP5/FP6 (wrong format / specificity) caused by **long-context post-training**, not your chunker.  
  - **Gold packed at position 10 of 20, model quotes distractor #1:** FP4 + LITM; CE already ranked gold #1 and you **buried** it (Week 8 packing bug).  
  - **Evaluating only mean accuracy:** U-curve hidden; Liu et al. ask future LC claims to show **small best-vs-worst position gap**.  
  - **FinanceBench / 10-K stuffing:** long docs (Databricks: pages from SEC filings) — RAG still needed at corpus scale (53k docs in their FinanceBench setup).  
  - Raising `k` into a long window looks like using the model card; Liu et al. show extra docs stop helping and mid-context gold can beat **closed-book** in the wrong direction.

* **Average vs. Strong Engineer:**  
  **Average:** pick k from the model card (8 or 32); or paste the whole PDF into Gemini because the deck said 2M tokens; use “we have long context” as a reason to skip Week 9 logs.  
  **Strong:** Tune **recall curve vs packed-token quality** **per model** (Databricks methodology: embed `text-embedding-3-large`, chunk 512 / stride 256, cap prompt for output+buffer). Put highest-relevance chunks at **beginning and/or end** (Liu U-curve; LlamaIndex `LongContextReorder`). Use LC for **within-doc** reasoning (contracts, transcripts) and RAG for **corpus-scale** search. Re-evaluate packing on generator change — effective context is model-specific. Cohere and others argue large windows don’t replace RAG for freshness, cost, modularity (referenced in Databricks survey of the debate).  
  **FDE bar:** quote Liu U-curve + open-domain saturation numbers as **warnings**, not 2026 SOTA; quote Databricks 32k/64k decrease examples as **model-specific**; classify a long-k miss as FP4/LITM only after confirming gold was packed; never use “we have long context” as a reason to skip Week 9 logs.

* **Worked Example:**  
  Injection **cell I** on Deployment Copilot: take Week 8 packed top-8, insert 12 distractors so gold sits at **index 10**, keep query and gold text fixed (Liu’s position knob). Label: ranking/assembly + grounding; Barnett FP4; Jason A|C. Compare to best-first packing (same 8 gold+neighbors). Log `packed_position`.

  Observed-symptom table for the Week 9 log:

  | Observed symptom | Likely mode | First measurements |
  | --- | --- | --- |
  | Invents facts; sources empty/irrelevant | Recall or ranking | recall@k, retrieval relevance judge (C\|Q) |
  | Right doc in corpus, wrong answer | Ranking or grounding | MRR/NDCG; inspect top-k vs packed |
  | Right chunk in prompt, wrong/partial answer | Generation-grounding | Faithfulness, completeness, position ablation |
  | Correct yesterday, wrong after doc update | Corpus drift | `content_hash`, `pipeline_version`, dual-index eval |
  | Quality drops as *K* increases | Lost-in-middle / noise | Context precision, faithfulness vs *K* sweep |

* **Apply It:**  
  1. Do not treat advertised context length as a license to raise packed `k` without a quality sweep.  
  2. Log `packed_position` on every run; run cell I (gold mid-list) as a position ablation.  
  3. Pack highest-rerank hits at beginning and/or end; keep Week 8 `top_n` in the 5–10 band unless your model-specific sweep says otherwise.  
  4. When quality drops as *K* rises, classify FP4/LITM / noise — not “embedding regressed” — unless recall@k also moved.  
  5. Re-sweep packing whenever the generator changes (Databricks: effective window is model-specific).  
  6. Prefer RAG for corpus-scale / ACL / freshness; prefer LC (or hybrid) when a single long doc fits and distraction is controlled.

---

## Week 9 build checklist (end-to-end)

Use this as the chapter’s capstone sequence; every concept above maps here.

1. **Preserve logs:** Keep Week 7 stage-1 candidates and Week 8 `rerank.ids[]` / `packed_position`; append taxonomy fields only.  
2. **Golden set:** Pin ~30–50 queries with supporting `chunk_id`s plus an unanswerable slice.  
3. **Fault matrix:** Run injection cells A–I (one fault per cell; restore after each).  
4. **Classify:** For each broken run, set `canonical_mode`, `barnett_fp`, `qca_failed[]` via the ordered cheat sheet.  
5. **Grounding contract:** Structured citations ⊆ packed IDs; evidence snapshots; code assert on citation allowlist.  
6. **Drift control:** Stamp `pipeline_version` / hashes / `index_alias`; run cell H (stale index); gate alias flips on dual-index eval.  
7. **LITM slice:** Run cell I; log `packed_position`; do not raise packed `k` from model-card folklore alone.  
8. **Artifact:** Ship the classified portfolio debugging log — not a single E2E accuracy slide. Week 10 turns labels into metric recipes.

When those steps are true, Week 9 is done in the syllabus sense: wrong answers have owners (search / packing / reader / drift), Barnett FP1–FP7 and Jason Liu Q–C–A are on the log, and “I don’t know” is a labelled outcome.

---

## Compilation notes

- All concept sections above are grounded in `research/phase-2/week-09-rag-failure-taxonomy/` (`00`–`04`, README).  
- No section required `[NEEDS MORE RESEARCH]` for the four syllabus concepts compiled from research files `01`–`04` plus the fault-injection / debugging-log protocol in `00`.  
- Open questions left in research (agentic multi-hop cascade attribution; FP3 as first-class assembly mode; parametric-prior policy tags; Groundedness Pro vs RAGAS as sole oracle; optimal citation granularity; golden-set refresh cadence) are out of scope for this chapter’s six fields and remain research-side.  
- Outside URLs from research are not required reading to understand this chapter; operational detail was inlined from the notes.
