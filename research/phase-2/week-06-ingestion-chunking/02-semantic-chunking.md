# 02 — Semantic chunking

> Week 6 concept research (deep). Legal sources only. Chip Huyen via public blog only.

---

## Fundamentals

**Semantic chunking** (Kamradt **Level 4**) does not cut at a global character/token count. It:

1. Splits the document into **sentences** (regex or a sentence tokenizer).
2. Optionally **buffers** each sentence with neighbors (`buffer_size`, default 1 in LlamaIndex / LangChain experimental).
3. **Embeds** those windows with the same family of model you will use at query time (or a cheaper sibling—retune thresholds if you mix).
4. Walks consecutive embeddings and measures **cosine distance**.
5. Places a chunk boundary where distance **spikes**—a topic shift—according to a statistical threshold on that distance series.

LlamaIndex documents this as an adaptation of Kamradt’s video at `https://youtu.be/8OJC21T2SL4?t=1933` into `SemanticSplitterNodeParser`. Official caveats: the sentence regex is **primarily English**; you **must tune** `breakpoint_percentile_threshold`. Defaults in the docs: `buffer_size=1`, `breakpoint_percentile_threshold=95`.

LangChain’s experimental `SemanticChunker` (`langchain_experimental.text_splitter`) exposes `breakpoint_threshold_type`:

| Type | Typical default amount | Idea |
|------|------------------------|------|
| `percentile` (default) | 95 | Split when distance exceeds the Nth percentile of *this document’s* distances |
| `standard_deviation` | ~3 | Split when distance > mean + k·σ |
| `interquartile` | ~1.5 | Split using IQR-scaled outliers (more robust to one huge spike) |
| `gradient` | ~95 | Percentile on the *rate of change* of distances (gradual legal/scientific drift) |

`number_of_chunks` can override the threshold by interpolating a percentile that yields a target count. There is **no `chunk_size`**. Variable-length topics are the point—and the operational risk.

Pinecone describes the same pipeline: sentences → local groups → embed → semantic distance vs predecessor → boundaries at theme shifts. They treat it as experimental tooling, not the first ingest path.

**What semantic chunking is not:**

- Not a substitute for Markdown/HTML header splitters on well-headed wikis (Level 3 already encodes topics).
- Not late chunking (arXiv 2409.04701): late chunking still *needs* span boundaries; it changes *when* pooling happens (after a long-context transformer), not *where* topics break.
- Not Anthropic contextual retrieval: that **prepends** LLM-written situating text to *existing* chunks; it does not choose breakpoints.
- Not “one idea per vector” by magic: two adjacent sentences on the same topic with a rhetorical contrast can spike; two unrelated bullets with similar embedding geometry can fuse.

Huyen (public blog) still frames the job as producing chunks that fit embed/context budgets. Semantic splitting can *violate* those budgets: a “topic” can be 3k tokens. Production implementations **cap** max size and fall back to recursive inside an oversized semantic span.

---

## Alternatives & Tradeoffs

| Choice | Upside | Downside |
|--------|--------|----------|
| Recursive / sentence only | Cheap, stable sizes, reproducible | May join unrelated adjacent sections on unmarked prose |
| Semantic (Kamradt / LlamaIndex / LangChain experimental) | Topic-coherent chunks; community reports of small recall lifts (Firecrawl cites ~few points vs recursive on some sets) | Embed every sentence (or window) at ingest; variable sizes; threshold not portable across embedders |
| Proposition / factoid chunking (LLM or NLP) | Atomic claims for QA | Extra pipeline; fragments procedures that need surrounding steps |
| Hierarchical leaves + parent merge (LlamaIndex auto-merge / LangChain parent-document) | Precision at leaf, restore context at generate | Two-level index; more retriever code |
| Semantic *only on a slice* of the corpus | Pay embed cost where markup is weak | Two splitter IDs in one index; evals must tag corpus subset |

Empirically, recursive is already near semantic on **headed** docs. Semantic shines on long FAQ dumps, legal narrative, academic prose, and transcripts **without** `#` / HTML structure. If your PDF pipeline already emits Markdown with `##` sections, try header split + recursive **before** paying for sentence embeddings.

Distance statistics are **document-local**. A 95th percentile on a homogeneous spec is a different physical distance than 95th on a meandering memoir. Copying `breakpoint_percentile_threshold=95` across embedders (MiniLM vs OpenAI vs E5) is a common silent regression.

ANN / HNSW payload: highly variable chunk lengths change how much “meaning” is compressed per vector (Pinecone: long chunks dilute; short chunks starve context). Semantic does not free you from size/overlap sweeps (concept 04); it changes the *distribution* you sweep over.

---

## Necessity

Without some semantic *or* structural coherence, a chunk mixes two topics so the embedding is a **mushy average**—neither topic retrieves reliably (Weaviate: large chunks mix ideas; subtopics get lost). Semantic chunking is one way to enforce “one idea per vector” when **markup is absent**.

If you skip it *and* skip structure splitters, failures look like:

- Query “refund window for enterprise” retrieves a chunk that also contains the SMB return policy; the generator hedges or picks the wrong tier.
- Consecutive SOP steps that belong together get split by a lucky recursive size cut; consecutive unrelated appendices get glued because they share a page.
- Eval recall looks “fine” on headed wiki queries and collapses on the unmarked FAQ corpus—exactly the slice semantic is for.

If you **always** turn it on:

- Ingest cost scales with sentence count, not document count.
- Oversized topics blow the embedder window (truncation—the thing chunking was invented to avoid).
- Reproducibility dies unless you version embedder + threshold + sentence regex (Week 5 lesson applied to ingest).

---

## Industry Practice

**Common:** skip until recursive + a golden set shows boundary failures. Correct default.

**Strong:**

- Route: `*.md` / HTML / code → structure parsers (concept 06). Unmarked `.txt` / extracted narrative → semantic **or** recursive, decided by eval, not fashion.
- Always `max_chunk_size` (tokens of the embedder) after semantic merge; recursive-split leftovers.
- Tune thresholds **per embedder** on a labeled boundary set (human: “this cut is wrong”). LlamaIndex says this in the module caveats; believe them.
- Prefer `interquartile` or `gradient` when one dramatic topic shift would hide moderate shifts under `standard_deviation` (distance series with a 0.90 outlier inflating σ).
- Log `n_sentences`, distance histogram quantiles, and resulting chunk-size histogram per `doc_id` so you can see “this 10-K became three 8k-token blobs.”
- Do not A/B semantic vs recursive in the same namespace without `splitter_id` metadata (concept 05)—you will not be able to explain a recall delta.

Pinecone: start fixed/recursive; semantic is the next experimental rung. Kamradt Level 4 is “when Level 2/3 still glue unrelated adjacent text.” Huyen pitfalls: do not start here.

---

## Concrete Scenario

Kamradt’s public talk walks Level 4 as an embedding-distance walk, not a new vector database. Timestamp for the semantic section:

https://youtu.be/8OJC21T2SL4?t=1933

Notebook (legal, public GitHub):

https://github.com/FullStackRetrieval-com/RetrievalTutorials/blob/main/5_Levels_Of_Text_Splitting.ipynb

LlamaIndex adapter (cites the same timestamp) and the English-regex / tune-threshold caveats:

https://developers.llamaindex.ai/python/framework/module_guides/loading/node_parsers/modules/

Pinecone overview of the Kamradt-style pipeline:

https://www.pinecone.io/learn/chunking-strategies/

Syllabus chatbot: a 20-query golden set fails on two “policy vs procedure” collisions **inside a long unmarked FAQ**, while headed runbooks are fine. Apply `SemanticSplitterNodeParser` **only** to that FAQ corpus, cap at 512–1024 embedder tokens, keep recursive on wikis. Do not flip the whole index to semantic because a blog claimed a 9% recall lift.

---

## Open Questions

- Is percentile-95 portable across embedding models, or must every embedder swap retune on the same docs?
- How do variable-length semantic chunks interact with ANN indexes and with rerankers that assume roughly uniform passage length (Week 8)?
- Late chunking vs semantic boundaries: complementary (semantic spans + late pooling) or redundant if contextual retrieval already situates chunks?
- Should semantic run on the **same** embedder as retrieval, or is a cheap local MiniLM enough for breakpoints?
- Post-chunking at query time (Weaviate/Elysia): could you embed whole docs and only semantically split retrieved candidates, avoiding ingest-time sentence embeds on cold documents?
- Multilingual: replace `(?<=[.?!])\s+` with a proper sentence segmenter, or semantic chunking is English-only in practice?

---

## Sources

- https://youtu.be/8OJC21T2SL4
- https://youtu.be/8OJC21T2SL4?t=1933
- https://github.com/FullStackRetrieval-com/RetrievalTutorials/blob/main/5_Levels_Of_Text_Splitting.ipynb
- https://developers.llamaindex.ai/python/framework/module_guides/loading/node_parsers/modules/
- https://github.com/run-llama/llama_index/blob/main/llama-index-core/llama_index/core/node_parser/text/semantic_splitter.py
- https://github.com/langchain-ai/langchain-experimental/blob/main/libs/experimental/langchain_experimental/text_splitter.py
- https://www.pinecone.io/learn/chunking-strategies/
- https://weaviate.io/blog/chunking-strategies-for-rag
- https://www.firecrawl.dev/blog/best-chunking-strategies-rag
- https://huyenchip.com/2024/07/25/genai-platform.html
- https://huyenchip.com/2025/01/16/ai-engineering-pitfalls.html
- https://arxiv.org/abs/2409.04701
- https://arxiv.org/abs/2307.03172
