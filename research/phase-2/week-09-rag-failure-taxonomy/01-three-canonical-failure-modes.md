# 01 — Three canonical failure modes (recall / ranking / generation-grounding)

> Week 9 concept research (deep). Legal sources only.

---

## Fundamentals

Production RAG failures cluster into **three diagnosable layers**. They map onto Barnett et al.’s Index/Query graph (arXiv:2401.05856), Jason Liu’s Q–C–A triangle, and the TruEra/RAGAS “RAG triad” (context relevance, groundedness, answer relevance).

### Recall failure — “Was the evidence ever eligible?”

The answerable span is **not in the candidate set** the retriever can return. Causes:

- **FP1 Missing Content** (Barnett): the question cannot be answered from available documents. Happy path: “Sorry, I don’t know.” Failure: the system is **fooled** into answering from parametric memory or near-topic chunks when the question is *related* but unanswerable.  
- Chunking/embedding so similarity never fires (Barnett §3.1: chunks too small → some questions unanswerable; too long → noise). Changing embedding **requires re-indexing all chunks**.  
- Metadata / ACL / tenant filters emptying the pool (looks like “RAG missed it”; Week 7 pgvector under-scan is the same shape).  
- Gold outside `fetch_k` entirely — Barnett **FP2** when K is a performance cutoff: “in theory all documents are ranked; in practice top-K.” If gold never enters the retrieved list, Jason Liu **C|Q** is already dead. Hamel: **absence blindness** — teams obsess over generation while retrieval never found the passage.

Recall is **not** “the user didn’t like the answer.” It is a **set-membership** question against the corpus and the retrieval cutoff.

### Ranking / context-assembly failure — “Did evidence survive into the window?”

Relevant chunks exist in the hit list but sit **below the cutoff**, get demoted by a weak reranker, or are discarded by a **consolidator** that must fit a token/rate budget.

- **FP2 Missed Top Ranked Documents:** answer is in the document; rank was not high enough to return. K chosen for latency/cost.  
- **FP3 Not in Context — consolidation strategy limitations:** documents **were retrieved** from the DB but **did not make it into the prompt**. Barnett: token limits and rate limits force a reduction/chaining strategy. This is the stage Week 8 packing owns.  
- **Lost in the Middle** (Liu et al., arXiv:2307.03172) compounds assembly: even when chunks **enter** the prompt, **mid-context** evidence is under-used. That can present as FP4 (not extracted) even though the engineering bug was **order / k**, not the reader weights.

Jason Liu **C|Q** (context relevance) fails when packed C is off-need; **Q|C** (answerability) fails when packed C cannot support a satisfactory answer even if some retrieved-but-dropped chunk could.

### Generation-grounding failure — “Given usable C, did the reader behave?”

The prompt contains (or nearly contains) the answer, but the LLM:

- **FP4 Not Extracted** — answer present in context; model fails to extract. Typical cause: **too much noise or contradicting information** (Barnett). LITM is a special case of “present but unused.”  
- **FP5 Wrong Format** — asked for table/list; model ignored the instruction.  
- **FP6 Incorrect Specificity** — too vague or too specific vs designer/user need (AI Tutor: teachers want **educational content with** the answer, not just the fact). Also: users ask too generally.  
- **FP7 Incomplete** — not incorrect, but missing information that **was in context**. Example: “key points in documents A, B, and C” — better asked separately (Barnett).

Jason Liu **A|C** = faithfulness/groundedness (answer restricts itself to C). **A|Q** = answer relevance. **C|A** = context support coverage (does C support every claim in A — complementary to faithfulness). **Q|A** = self-containment (can you infer the question from the answer).

Hamel maps this to ops: **debug retrieval with IR metrics first**; then generation via error analysis and **validated** judges. Domain modes (adult vs pediatric dose; jurisdiction) are **extra** metrics found only by reading traces — not a reason to skip the 3-mode cut.

### Barnett → 3-mode map (teaching table)

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

### BioASQ scenario (Barnett §4.3)

Indexed **4017** open-access BioASQ PDFs; **1000** expert questions (yes/no, summarisation, factoid, list). Generated answers evaluated with **OpenAI Evals**. Manual inspection of ~40 issues plus **all** Evals-flagged inaccuracies. Finding: automated evaluation was **more pessimistic** than a non-expert human rater (validity threat: LLM may know more than the rater in-domain). Scripts/data/examples of each FP: figshare `fbf7805b5f20d7f7e356`.

AI Tutor lessons that feed the taxonomy: larger context helped extraction (8K vs 4K) **contrary** to some GPT-3.5 LITM reports; filename + chunk number in context helped the reader (FP2/FP4); semantic cache for FAQs (FP1 cost); jailbreaks bypass RAG into safety training (FP5–7); **continuous calibration** because inputs are unknown at runtime.

---

## Alternatives & Tradeoffs

| Diagnostic grain | Pros | Cons |
| --- | --- | --- |
| “Hallucination” umbrella | Communicates to execs | Hides index vs retriever vs prompt |
| 7 FPs only | Matches the paper | Overlap; consolidator vs rank |
| **3-mode + FP subtype** | Matches owners and vendor evaluator split | Need logging at each hop |
| 6 Q–C–A only | Exhaustive pairwise | Weak on corpus/ACL/drift/index version |
| RAGChecker / ARES / 20-metric suites | Fine dashboards | Jason Liu: ask which of the 6 relations they measure |

**k tradeoff (ops):** raising *K* reduces FP2 misses and can raise Databricks-style “more docs help **until** they don’t”; it increases noise → more FP4, token cost, and LITM. Hybrid + CE rerank improves ranking (Week 8) but adds a model to evaluate. Refusal gates reduce FP1-shaped hallucinations but raise false refusals on FP2.

---

## Necessity

Without this cut, teams optimize the **wrong stage** (swap GPT when BM25 never saw the SKU; or tune embeddings when the model ignored a packed gold chunk). Taxonomy decides:

- **Metric:** recall@k vs NDCG vs faithfulness vs completeness.  
- **Owner:** data/search vs packing vs prompt.  
- **Whether “I don’t know” is a win (FP1) or a bug (FP2).**

Service-specific failures:

- **Faithfulness 0.9 on a recall miss:** the model faithfully recited irrelevant C — **not** a generator win.  
- **E2E accuracy dip after raising k:** ranking/LITM, not “the new embedding is worse,” unless recall@k also moved.  
- **OpenAI Evals red, human green (BioASQ):** do not auto-close FP4 from a pessimistic judge (Hamel: calibrate TPR/TNR).  
- **Judge uses live corpus instead of packed snapshot:** you evaluate a different C than the model saw.

---

## Industry Practice

**Common:** screenshot the wrong answer; blame the LLM.

**Strong:** Hamel sequence — (1) qrels / synthetic reverse-generated query–doc pairs; Recall@k / Precision@k / MRR on **production k** and **fetch_k**; (2) only then LLM judges for C|Q, A|C, A|Q. Azure: Document Retrieval when you have graded `retrieval_ground_truth` (fidelity, NDCG, XDCG, max relevance, **holes** = unlabeled docs); Retrieval evaluator (1–5) when you lack qrels. NVIDIA RAG flow example config: `retriever_recall_5/10` + `retriever_ndcg_cut_5/10` type `pytrec_eval`; `rag_faithfulness` / `rag_answer_relevancy` type `ragas` with `judge_llm` (+ embeddings for relevancy). Databricks Agent Evaluation attributes failing rows to chunk relevance / context sufficiency / groundedness / relevance-to-query.

**FDE bar:** walk a trace through the ordered decision list in `00-week-overview.md`; name FP1–FP7 without notes; distinguish packed C from retrieved C (FP3); cite Jason Liu page as **still public**; add one **domain** failure mode from error analysis (Hamel medical/legal examples) rather than inventing 20 generic metrics.

---

## Concrete Scenario

Barnett BioASQ + AI Tutor + Cognitive Reviewer are the paper’s three worlds. For the curriculum product, run **injection cells A–G** from the overview on the same 50-query golden set used in Week 8 deltas.

Worked example (synthetic but in the paper’s shape):

- Query: “Define pseudotumor cerebri. How is it treated?” (Barnett sample).  
- If the OA PDF was never ingested → FP1 / recall; refusal is correct.  
- If ingested but cosine put it at rank 40 and `k=8` → FP2 / ranking; recall@40 high, recall@8 zero.  
- If retrieved then consolidator dropped it for token budget → FP3; retriever span has gold, prompt does not.  
- If packed with contradictory review papers → FP4 / A|C.  
- If the gold list of treatments is in C but the model returns one drug → FP7.

URL: https://arxiv.org/html/2401.05856v1  
Companions: https://arxiv.org/abs/2401.05856 · https://jxnl.co/writing/2025/05/19/there-are-only-6-rag-evals/ · https://hamel.dev/blog/posts/evals-faq/how-should-i-approach-evaluating-my-rag-system.html · https://learn.microsoft.com/en-us/azure/foundry/concepts/evaluation-evaluators/rag-evaluators · https://docs.nvidia.com/nemo/microservices/latest/evaluate/flows/rag.html

---

## Open Questions

- Multi-hop / agentic RAG: is a failed hop-1 retrieve still “recall” when hop-3 looks like grounding? (Later literature: cascade / causal attribution — out of Week 9 scope but interviewers ask.)  
- Should FP3 be a first-class **assembly** mode so 3-mode does not overload “ranking”?  
- When C is relevant but **insufficient** (Jason C|A / Q|C), is that recall (need more docs) or ranking (wrong mix) or generation (should refuse)? Product policy, not a metric.  
- Graded vs binary qrels for FP2 (Azure Document Retrieval wants `query_relevance_label`).

---

## Sources

- Barnett et al. arXiv:2401.05856: https://arxiv.org/abs/2401.05856 · https://arxiv.org/html/2401.05856v1 · ACM CAIN https://doi.org/10.1145/3644815.3644945 · figshare https://figshare.com/s/fbf7805b5f20d7f7e356  
- Jason Liu, There Are Only 6 RAG Evals: https://jxnl.co/writing/2025/05/19/there-are-only-6-rag-evals/  
- Hamel RAG FAQ: https://hamel.dev/blog/posts/evals-faq/index.html · https://hamel.dev/blog/posts/evals-faq/how-should-i-approach-evaluating-my-rag-system.html  
- Liu et al. Lost in the Middle: https://arxiv.org/abs/2307.03172  
- Azure RAG evaluators: https://learn.microsoft.com/en-us/azure/foundry/concepts/evaluation-evaluators/rag-evaluators  
- NVIDIA RAG flow: https://docs.nvidia.com/nemo/microservices/latest/evaluate/flows/rag.html  
- NVIDIA RAG metrics: https://docs.nvidia.com/nemo/microservices/26.3.0/evaluator/metrics/rag.html  
- YouTube: Hamel How To Approach Your AI Evals https://www.youtube.com/watch?v=DZxaPNYi_k0  
- TWIML / Jason Liu: Why Your RAG System Is Broken https://twimlai.com/podcast/twimlai/why-your-rag-system-is-broken-and-how-to-fix-it  
