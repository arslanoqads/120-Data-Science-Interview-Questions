# 03 — “Lost in the middle” and why reranking mitigates it

> Week 8 concept research (deep). Legal sources only. Chip Huyen via public blog only.

---

## Fundamentals

**Paper:** Nelson F. Liu, Kevin Lin, John Hewitt, Ashwin Paranjape, Michele Bevilacqua, Fabio Petroni, Percy Liang. *Lost in the Middle: How Language Models Use Long Contexts.* arXiv:**2307.03172**. Published in **TACL** 2024 (ACL Anthology 2024.tacl-1.9; DOI 10.1162/tacl_a_00638). Affiliations: Stanford, UC Berkeley, Samaya AI.

**Claim:** having a long context window is not the same as **using** information in that window. When the authors vary **where** the relevant information sits, performance is often **U-shaped**: best when the needle is at the **beginning** (primacy) or **end** (recency), worst in the **middle** — including for models advertised as long-context.

### Task 1 — Multi-document QA (RAG analogue)

Inputs: a question + **k** Wikipedia passages; **exactly one** contains the answer; **k−1** are distractors. Instantiated from NaturalQuestions-Open (2,655 queries whose long answer is a paragraph). Gold passage from NQ annotations; distractors = Contriever-MSMARCO top chunks that do **not** contain the annotated answers, presented in decreasing relevance. They permute **position** of the gold document and **k** (context length) independently.

Result (paper Figure 1 / §2.3): U-shaped accuracy vs gold position. Extreme finding: when gold is in the **middle**, **GPT-3.5-Turbo** multi-document QA can fall **below closed-book** (paper: closed-book **56.1%**). Extended-context models are **not necessarily** better at using context than their shorter-context counterparts (identical performance in several comparisons).

Architecture probes (§4): encoder-decoder models are more position-robust **within training length**, then show a U-curve when sequences exceed training length. **Query-aware contextualization** (query before *and* after the documents) nearly perfects the synthetic KV task but **minimally** changes multi-document QA trends. Base LMs without instruction tuning still show the U-curve.

### Task 2 — Synthetic key-value retrieval

JSON key-value pairs; return the value for a key. Isolates “can you even copy from the middle?” Some models are perfect; others still U-shaped on middle keys.

### Open-domain case study (§5)

Unlike the controlled task (exactly one gold doc always present), retriever-reader on NQ-Open + Wikipedia: **none or many** of the top-k may contain the answer. **Performance saturates long before retriever recall saturates.** Using **50 documents instead of 20** only marginally improves (~**1.5%** GPT-3.5-Turbo, ~**1%** Claude-1.3) while the retriever is still recovering more gold. Extra retrieved docs are not extra used docs.

**Protocol they want future long-context claims to meet:** show performance is **minimally affected by position** (small best-case vs worst-case gap), not merely that the window is 100K tokens.

### Why reranking mitigates (without rewriting attention)

Reranking does **not** flatten Transformer positional bias. It changes the **input construction**:

1. **Fewer docs** — you leave the long-k regime where the paper shows degradation and open-domain saturation. Pinecone: maximize retriever recall, then minimize what the LLM sees; they cite Liu et al. explicitly. Pinecone Inference blog: more data can reduce accuracy; rerank removes irrelevant docs and can optimize order.  
2. **Better docs in the slots that remain** — less chance the answer lives in a distractor that the model actually attends to.  
3. **Optional edge placement** — put the highest-rerank passage first (primacy) and/or last (recency). LlamaIndex **`LongContextReorder`**: docs cite the same study (“best performance typically arises when crucial data is positioned at the start or conclusion”; performance drops as context lengthens even for long-context models) and reorder retrieved nodes when a large top-k is still required.

Chip Huyen, *Open challenges in LLM research* (2023, public blog): RAG is two phases; **context length ≠ efficient context use**; Lost in the Middle is the example under “prompt construction.” Her later platform post: rank still matters because of lost-in-the-middle, but **inclusion** in the window often dominates search-style nDCG — which is why stage-1 recall and stage-2 packing are both this week’s job.

---

## Alternatives & Tradeoffs

| Mitigation | Idea | Limit |
|------------|------|--------|
| **Rerank → fewer docs (5–10)** | Primary production fix; syllabus default | Cannot help if gold never retrieved |
| Best-first packing | Exploit primacy | Recency unused; still a U if k is huge |
| Best-first + best-last / `LongContextReorder` | Exploit both lobes of the U | Middle still weak if you keep many docs |
| Query-aware contextualization | Query before and after docs | Paper: helps KV copy more than multi-doc QA |
| Smaller chunks + citations | Less hay per needle | Chunking is Week 6; citations ≠ attention |
| Long-context models alone | Marketing | Paper: extended context ≠ robust middle use |
| Encoder-decoder generators | More robust in-train-length | Rare as the RAG *generator* in 2026 stacks |
| Raise k until recall saturates | Feels scientific | Open-domain: reader saturates first |

Rerank **then** reorder is complementary: CE chooses *who* enters; reorder chooses *where* they sit.

---

## Necessity

Naïvely stuffing top-20 cosine (or even top-20 RRF) hits invites middle-context failures that look like “the model is dumb” or “hallucination.” Liu et al. show the failure can be **worse than giving no documents**. Without **position-aware eval**, you may increase `k` and watch quality drop.

Service-specific failures:

- **“We have 128K context so k=40 is free.”** Token $ is not free; middle use is not free.  
- **Gold at rank 1 of CE but packed as document #6 of 12** — you paid for ranking then buried it.  
- **Evaluating only average accuracy** without slicing by gold position — U-curve hidden in the mean.  
- **Blaming the LLM** when Week 7 logs show gold was never retrieved — different bug (Week 9 taxonomy).

---

## Industry Practice

**Common:** `k=5` folklore without position testing; or `k=20` because the model card says 128K.

**Strong:** measure answer accuracy vs **gold-doc position** on a controlled permutation set (even a 50-query mini protocol); keep prompt packs short; put highest-rerank doc first (or first+last); treat “more context” as a hypothesis to **falsify**. Pinecone rerankers chapter + refine-with-rerank page cite Liu et al. as motivation. LlamaIndex ships `LongContextReorder` as a named postprocessor for this paper. Huyen: invest in retrieval/chunking/querying, not only window size.

**FDE bar:** reproduce the paper’s two experimental knobs (position, k) in language; quote the closed-book-vs-middle GPT-3.5 number as a warning, not as a 2026 SOTA; distinguish *controlled* one-gold-doc vs *open-domain* saturation; log `packed_position` of gold on every eval query.

---

## Concrete Scenario

Paper landing + PDF + TACL:

https://arxiv.org/abs/2307.03172  
https://arxiv.org/pdf/2307.03172  
https://aclanthology.org/2024.tacl-1.9/  
https://doi.org/10.1162/tacl_a_00638  
Code/data pointer in paper: nelsonliu.me/papers/lost-in-the-middle  

Huyen public discussion (RAG + Lost in the Middle):

https://huyenchip.com/2023/08/16/llm-research-open-challenges.html  

Pinecone citations:

https://www.pinecone.io/learn/series/rag/rerankers/  
https://www.pinecone.io/learn/refine-with-rerank/  
https://www.pinecone.io/blog/introducing-reranking-to-pinecone-inference/  

LlamaIndex reorder (explicit LITM copy):

https://docs.llamaindex.ai/en/stable/module_guides/querying/node_postprocessors/node_postprocessors/  

**Curriculum lab:** take 30 NQ-style questions where gold chunk is known. For each, build a 10-doc prompt with gold at indices 0, 4, 9. Measure exact-match. Then rerank the same 10 and pack top 5 (gold should move to index 0 if CE works). The delta **is** this week’s point.

---

## Open Questions

- Have post-2024 models flattened the U-curve enough to change `k` defaults, or only reduced the depth of the valley?  
- Is edge-ordering still helpful **after** strong reranking to 5 docs?  
- Does RAG-with-citations / quote-first decoding change how models attend vs plain concatenation?  
- How much of the U-curve is architecture (causal + residual) vs training data (later papers argue both)?  
- Should eval harnesses require a position-robustness gap metric before claiming “long context RAG”?

---

## Sources

- https://arxiv.org/abs/2307.03172  
- https://arxiv.org/pdf/2307.03172  
- https://aclanthology.org/2024.tacl-1.9/  
- https://doi.org/10.1162/tacl_a_00638  
- https://huyenchip.com/2023/08/16/llm-research-open-challenges.html  
- https://huyenchip.com/2024/07/25/genai-platform.html  
- https://www.pinecone.io/learn/series/rag/rerankers/  
- https://www.pinecone.io/learn/refine-with-rerank/  
- https://www.pinecone.io/blog/introducing-reranking-to-pinecone-inference/  
- https://docs.llamaindex.ai/en/stable/module_guides/querying/node_postprocessors/node_postprocessors/  
