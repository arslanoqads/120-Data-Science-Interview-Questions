# Chapter 6 — Ingestion and Chunking: the RAG Quality Floor

> **Phase 2 — RAG Systems**  
> **Compilation status:** COMPLETE  
> **Source of truth:** `research/phase-2/week-06-ingestion-chunking/`  
> **Syllabus Build:** Ship an ingestion pipeline for the FastAPI RAG chatbot with **≥2 chunking strategies** (recursive + semantic), metadata tagging, and messy real documents—not a single global character cut dumped into a vector DB.

---

## Chapter framing

Weeks 4–5 gave Deployment Copilot a provider-agnostic client and versioned prompts. Week 6 decides **what vectors exist at all**. Retrieval (Week 7), reranking (Week 8), failure taxonomies (Week 9), and evals (Week 10) all operate on the units produced here. A perfect hybrid retriever over half-sentences and headerless table rows still fails.

Chip Huyen’s public platform writing is explicit: RAG exists because naively stuffing whole documents into context is unbounded; documents must be split into **manageable chunks** sized by embedding/context limits and latency. She does **not** prescribe a magic number—she points practitioners at Pinecone, LangChain, LlamaIndex, and Greg Kamradt. Longer generation windows do not retire this step: *how much context a model can use* ≠ *how efficiently it uses it* (lost-in-the-middle, Liu et al. 2023). Pinecone’s embedding constraints make the same point operationally: overflow is truncated before the vector exists, and a chunk that is not independently meaningful will not surface usefully at query time. The human test (Pinecone and Weaviate, independently): **if a chunk makes sense without surrounding context to a human, it will make sense to the model.**

Kamradt’s “5 Levels of Text Splitting” is the industry shared vocabulary this chapter uses:

| Level | Name | Role this week |
|-------|------|----------------|
| 1 | Character / fixed-size | Cheap baseline; mid-sentence cuts |
| 2 | Recursive | Sane generic default under a size cap |
| 3 | Document structure | MIME/type routers (Markdown, HTML, code, JSON) |
| 4 | Semantic | Embedding-distance topic breaks when markup is weak |
| 5 | Agentic | Per-doc strategy selection—expensive escalation |

The six ideas below are one pipeline: **choose a splitter that respects structure** → **size to the embedder and query shape** → **label every chunk** → **route special MIME types**. Escalate to semantic, contextual prefixes, or agentic routing **only** when a labeled query set shows boundary failures. Skipping any step shows up as “the vector DB is bad” when the real bug is ingestion. Huyen’s pitfalls post: start too complex—do not abstract away the details you need to debug.

Read the concepts in order. Each section’s **Worked Example** and **Apply It** assume the same flagship service (working title: Deployment Copilot) ingesting product runbooks, Markdown docs, and a few Python snippets into a FastAPI RAG chatbot—not “just dump PDFs into a vector DB.”

**Default path (synthesis):** format detect → structure-aware split when possible → else recursive **~512 embedding-tokenizer tokens / ~10–20% overlap** → attach rich metadata (exclude ACL/PII from embed text) → eval sweep `{256, 512, 1024} × {0%, 10%, 20%}` before changing strategy → semantic → LLM contextual → agentic only when evals demand it.

---

### Fixed-size vs recursive character splitting

* **Fundamentals:**  
  **Fixed-size chunking** cuts text every N characters or tokens, optionally with a sliding overlap. It does not look at sentences, paragraphs, or headings. The usual target is the embedding model’s context window (Pinecone examples: 1024 tokens for `llama-text-embed-v2`, 8192 for `text-embedding-3-small`). Overflow is truncated *before* the vector exists, so important tokens never enter retrieval.

  **Recursive character splitting** still enforces a size budget, but tries a *hierarchy* of separators first. LangChain’s `RecursiveCharacterTextSplitter` is documented as **the recommended splitter for generic text**. Default separators are `["\n\n", "\n", " ", ""]`: keep paragraphs together; if a piece still exceeds `chunk_size`, split on newlines; then spaces; then characters. That is not “smarter embeddings”—it is cheap string recursion that prefers the strongest remaining semantic unit under a hard cap.

  Parameters that actually matter in production:

  | Parameter | Role |
  |-----------|------|
  | `chunk_size` | Max size as measured by `length_function` |
  | `chunk_overlap` | Repeated suffix/prefix so a cut sentence still appears in a neighbor |
  | `length_function` | Default `len` (characters). Production RAG should pass the **embedding tokenizer** |
  | `is_separator_regex` | Treat separator list as regex (CJK punctuation, Thai ZWSP, etc.) |
  | `from_language` / `get_separators_for_language` | Language-specific separator lists for code and markdown |

  LlamaIndex’s default `SentenceSplitter` is the sibling default: split on sentence boundaries, then pack sentences until a **token** budget. Same idea as recursive—respect structure, then size—measured in tokenizer units rather than `len()`. Recursive is Kamradt **Level 2**: the practical baseline before you spend embed or LLM calls. Pinecone’s 2025 guide is compatible with that claim: fixed-size will be best in many cases—start there and iterate—while recursive is the “great middle ground” that still enforces size limits. Use recursive as the *implementation* of “fixed-size with better boundaries,” then measure.

* **The Alternatives:**  

  | Approach | What you gain | What it costs | When it fits |
  |----------|---------------|---------------|--------------|
  | Skip chunking / dump PDFs | Demo speed; “long context will save us” | Truncation; lost-in-middle; unusable citations | Never for retrieval indexes |
  | Fixed-size (chars or tokens) | Predictable lengths; cheapest | Mid-sentence cuts; orphaned pronouns | Pinecone’s “start here then iterate” |
  | Single-separator `CharacterTextSplitter` | Slightly structure-aware | One separator is brittle across corpora | Narrow, uniform prose |
  | Recursive character (LangChain recommended) | Structure-first, O(text), no model calls | Weak on unmarked prose / minified JSON | Syllabus default for unmarked prose |
  | LlamaIndex `SentenceSplitter` | Token-aware packing of sentences | English-biased regex; huge sentences need fallback | Org default when tokens are the contract |
  | Document-specific (Markdown/HTML/code/JSON) | Aligns with real structure | Needs a MIME/type router | Prefer before recursive when format is known |
  | Semantic / LLM / agentic first | Topic coherence / format routing | Ingest $ and latency | Only after recursive evals fail |

  CJK / Thai: default `["\n\n", "\n", " ", ""]` will bisect words with no spaces. Override separators with ASCII/fullwidth/ideographic stops and zero-width space. Recursive is still the algorithm; the separator list is the localization.

* **Failure Modes:**  
  - Broken-span embeddings: half a definition + half the next section averages into a mushy vector; hybrid search may still hit a keyword while the generator answers from incomplete evidence.  
  - Silent truncation: a 1000-*character* chunk can be 400 or 900 tokens depending on code vs English; the embedder drops the tail.  
  - Citation theater: offsets do not line up with sentences humans can quote—“the bot cited page 4 but the sentence is cut.”  
  - False “vector DB is bad” incidents: Weaviate notes that poor RAG is often chunk quality, not the retriever. Week 7 hybrid/RRF cannot restore a mid-word cut.  
  - Over-investment later: picking a fancy vectordb before a recursive baseline (Huyen: start too complex).

* **Average vs. Strong Engineer:**  
  **Average:** copies `RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)` with `length_function=len`; metadata is `{source}` only; works on blog posts; fails on runbooks, 10-Ks, and Python.  
  **Strong:** `length_function` = embedding tokenizer (`tiktoken` / model tokenizer; LangChain `from_tiktoken_encoder()` so `chunk_size` is in tokens the embedder sees); format router first, recursive or `SentenceSplitter` as **fallback**; pin `splitter_id`, separator list, tokenizer name, size, and overlap next to the index (re-ingest is a deploy); golden query set before changing strategy; documents Kamradt Level 2 as default and Level 3+ as explicit escalations. FDE bar: explain why Pinecone still says start with fixed-size *then* iterate; why LangChain documents recursive as the generic recommended splitter; why character `len` in the official demo is a teaching default, not a production contract.

* **Worked Example:**  
  LangChain’s recursive guide splits a State of the Union transcript with `chunk_size=100`, `chunk_overlap=20`, default separators, and `length_function=len`. Chunks break at paragraph/sentence boundaries rather than arbitrary character offsets. That tiny size is **illustrative**—the same code with **512 embedding tokens** is Deployment Copilot’s unmarked-prose default.

  After the MIME router, leftover `.txt` / extracted PDF prose goes through recursive **512 embedding-tokenizer tokens / ~10% overlap**. A 20-query golden set that fails on mid-sentence policy definitions is a splitter bug, not a Weaviate vs Pinecone bake-off. Pin `splitter_id=recursive_v1` with tokenizer name and separator list in chunk metadata so a later re-ingest is attributable.

* **Apply It:**  
  1. Wire `RecursiveCharacterTextSplitter` (or LlamaIndex `SentenceSplitter`) as the unmarked-prose fallback—not as the only path.  
  2. Pass the **embedding tokenizer** as `length_function` (or use `from_tiktoken_encoder`); ban character `len` for production size contracts.  
  3. Start at ~512 tokens / ~10% overlap for prose; do not treat tutorial `1000/200` characters as the contract.  
  4. Record `splitter_id`, separators, tokenizer, size, and overlap on every chunk.  
  5. Run a golden query set before arguing about vector DB choice.  
  6. Localize separators for CJK/Thai corpora if present.

---

### Semantic chunking

* **Fundamentals:**  
  **Semantic chunking** (Kamradt **Level 4**) does not cut at a global character/token count. It:

  1. Splits the document into **sentences** (regex or a sentence tokenizer).  
  2. Optionally **buffers** each sentence with neighbors (`buffer_size`, default 1 in LlamaIndex / LangChain experimental).  
  3. **Embeds** those windows with the same family of model you will use at query time (or a cheaper sibling—retune thresholds if you mix).  
  4. Walks consecutive embeddings and measures **cosine distance**.  
  5. Places a chunk boundary where distance **spikes**—a topic shift—according to a statistical threshold on that distance series.

  LlamaIndex documents this as an adaptation of Kamradt’s video (semantic section ~`t=1933`) into `SemanticSplitterNodeParser`. Official caveats: the sentence regex is **primarily English**; you **must tune** `breakpoint_percentile_threshold`. Defaults in the docs: `buffer_size=1`, `breakpoint_percentile_threshold=95`.

  LangChain’s experimental `SemanticChunker` exposes `breakpoint_threshold_type`:

  | Type | Typical default amount | Idea |
  |------|------------------------|------|
  | `percentile` (default) | 95 | Split when distance exceeds the Nth percentile of *this document’s* distances |
  | `standard_deviation` | ~3 | Split when distance > mean + k·σ |
  | `interquartile` | ~1.5 | IQR-scaled outliers (more robust to one huge spike) |
  | `gradient` | ~95 | Percentile on the *rate of change* of distances (gradual legal/scientific drift) |

  `number_of_chunks` can override the threshold by interpolating a percentile that yields a target count. There is **no `chunk_size`**. Variable-length topics are the point—and the operational risk. Pinecone treats the same pipeline as experimental tooling, not the first ingest path.

  **What semantic chunking is not:** not a substitute for Markdown/HTML header splitters on well-headed wikis (Level 3 already encodes topics); not late chunking (arXiv 2409.04701—changes *when* pooling happens, not *where* topics break); not Anthropic contextual retrieval (prepends situating text to *existing* chunks). Two adjacent sentences on the same topic with a rhetorical contrast can spike; two unrelated bullets with similar embedding geometry can fuse. Huyen still frames the job as producing chunks that fit embed/context budgets—semantic splitting can *violate* those budgets (a “topic” can be 3k tokens). Production implementations **cap** max size and fall back to recursive inside an oversized semantic span.

* **The Alternatives:**  

  | Choice | Upside | Downside | When it fits |
  |--------|--------|----------|--------------|
  | Recursive / sentence only | Cheap, stable sizes, reproducible | May join unrelated adjacent sections on unmarked prose | Headed docs; first path |
  | Semantic (Kamradt / LlamaIndex / LangChain experimental) | Topic-coherent chunks; small recall lifts reported on some sets | Embed every sentence at ingest; variable sizes; threshold not portable across embedders | Long FAQ dumps, legal narrative, transcripts without `#` / HTML |
  | Proposition / factoid chunking | Atomic claims for QA | Extra pipeline; fragments procedures | Factoid-heavy contracts |
  | Hierarchical leaves + parent merge | Precision at leaf, restore context at generate | Two-level index; more retriever code | When leaves must be small |
  | Semantic *only on a slice* of the corpus | Pay embed cost where markup is weak | Two splitter IDs in one index | Syllabus pattern for FAQ vs wiki |

  Empirically, recursive is already near semantic on **headed** docs. Distance statistics are **document-local**—copying `breakpoint_percentile_threshold=95` across MiniLM vs OpenAI vs E5 is a common silent regression. Semantic does not free you from size/overlap sweeps; it changes the *distribution* you sweep over.

* **Failure Modes:**  
  - Two topics in one vector → mushy average; neither topic retrieves (Weaviate: large chunks mix ideas; subtopics get lost).  
  - Query “refund window for enterprise” retrieves a chunk that also contains the SMB return policy; the generator hedges or picks the wrong tier.  
  - Always-on semantic: ingest cost scales with sentence count; oversized topics blow the embedder window; reproducibility dies unless you version embedder + threshold + sentence regex.  
  - Eval recall looks fine on headed wiki queries and collapses on the unmarked FAQ—exactly the slice semantic is for—while you wasted sentence embeds on `.md` that already had `##` structure.  
  - A/B semantic vs recursive in the same namespace without `splitter_id` → you cannot explain a recall delta.

* **Average vs. Strong Engineer:**  
  **Average:** flips the whole index to semantic because a blog claimed a recall lift; uses default 95th percentile across embedders; no max-size cap.  
  **Strong:** skips until recursive + a golden set shows boundary failures; routes `*.md` / HTML / code to structure parsers; applies semantic **or** recursive to unmarked narrative by eval, not fashion; always `max_chunk_size` (embedder tokens) after semantic merge with recursive-split leftovers; tunes thresholds **per embedder** on a labeled boundary set; prefers `interquartile` or `gradient` when one dramatic spike would hide moderate shifts; logs `n_sentences`, distance histogram quantiles, and chunk-size histogram per `doc_id`. Pinecone: start fixed/recursive; semantic is the next experimental rung. Huyen pitfalls: do not start here.

* **Worked Example:**  
  Deployment Copilot’s 20-query golden set fails on two “policy vs procedure” collisions **inside a long unmarked FAQ**, while headed runbooks are fine. You apply `SemanticSplitterNodeParser` **only** to that FAQ corpus, cap at 512–1024 embedder tokens, keep recursive on wikis, and tag chunks with `splitter_id=semantic_faq_v1` plus `breakpoint_percentile_threshold=95` and embedder id. You do not flip the whole index because a secondary roundup cited a few-point lift.

* **Apply It:**  
  1. Confirm headed corpora already use header/structure splitters before paying for sentence embeddings.  
  2. Add semantic only where a golden set shows topic-boundary failures on unmarked prose.  
  3. Cap semantic spans at embedder-token max; recursive-split leftovers.  
  4. Tune `breakpoint_*` per embedder on human-labeled “this cut is wrong” examples.  
  5. Tag every node with `splitter_id` and threshold/embedder versions.  
  6. Log distance and chunk-size histograms so 8k-token blobs are visible.

---

### Agentic / LLM-based chunking, contextual retrieval, and late chunking

* **Fundamentals:**  
  Three different “use an LLM / long model at ingest” ideas get collapsed in Slack. Separate them.

  **1. LLM-based chunking (breakpoints or propositions).** A model reads (a window of) the document and **proposes cuts**, or rewrites text into **propositions** (atomic claims) that become chunks. Weaviate: the LLM identifies propositions, summarizes sections, or highlights key points so chunks preserve meaning better than punctuation rules. Cost: at least one strong-model call per document or per window. Output length is stochastic unless you constrain schema (Week 4 structured outputs).

  **2. Agentic chunking (strategy selection).** Kamradt **Level 5** and Weaviate’s agentic section: an agent inspects **type, structure, density**, then **selects or mixes** strategies—Markdown-by-header vs propositional vs page-level—and may attach metadata tags. It is a **router with tools** (MIME sniff, header count, table density, language), not “one prompt that splits every file the same way.” Token-cost trends made this thinkable; it is still the most expensive ingest path. In practice, ~90% of the value is a **deterministic MIME router** plus a few heuristics (`heading_density`, `code_fence_ratio`). The agent is justified when the corpus is heterogeneous *and* heuristics mis-route (scanned PDF that is actually a table pack; `.md` that is really a CSV dump).

  **3. Contextual retrieval (Anthropic, 2024) — text augmentation, not a splitter.** Documents are still split by an ordinary chunker. For each chunk, Claude sees **the whole document + the chunk** and writes ~**50–100 tokens** of situating context (“this chunk is from the Q3 enterprise refund policy, not SMB”). That prefix is prepended **before embedding and before BM25**. Prompt caching holds the document while you iterate chunks. Anthropic’s published reductions on their internal mix (codebases, papers, fiction), top-20-chunk retrieval **failure rate**:

  | Stack | Failure rate | Relative reduction vs baseline 5.7% |
  |-------|--------------|-------------------------------------|
  | Contextual embeddings only | 3.7% | ~35% |
  | Contextual embeddings + contextual BM25 | 2.9% | ~49% |
  | Above + rerank | 1.9% | ~67% |

  This fixes **anaphora and local ambiguity** (“the policy”, “its”). It does **not** choose recursive vs semantic. Pinecone’s 2025 guide describes the same pattern under “Contextual Chunking with LLMs.”

  **4. Late chunking (Günther et al., arXiv 2409.04701; Jina + Weaviate coauthors).** Architectural change to **embedding**, not an LLM editor. Naive path: split → embed each chunk in isolation → pronouns lose the antecedent. Late path: run a **long-context** embedding transformer over the whole document (or max window); take **token states**; **mean-pool** those states inside each chunk span. Chunk vectors are conditioned on document context. Requires a mean-pooling long-context embedder (e.g. Jina v2 8k). Berlin toy example: naive embeddings of “Its” / “the city” barely match “Berlin”; late-chunked embeddings do, because attention already saw the city name.

  **Complementarity:** recursive/semantic/agentic decide *spans*. Contextual retrieval *rewrites/prefixes* chunk text. Late chunking *pools token states* over those spans. You can combine them; you should not treat them as one checkbox named “agentic.” Huyen will not prescribe Level 5; pitfalls: **start too complex**—agentic ingest before a recursive baseline is exactly that. Weaviate also contrasts **pre-chunking** (async, fast query) vs **post-chunking** (embed whole docs, chunk at query time on retrieved docs—Elysia): another way to avoid a global ingest strategy, not free (first-access latency).

* **The Alternatives:**  

  | Method | Cost at ingest | Best for | Failure mode |
  |--------|----------------|----------|--------------|
  | Recursive / Markdown / Code splitters | Low, deterministic | Known formats, high volume | Wrong MIME → silent quality drop |
  | MIME + heuristics router | Low | ~90% of enterprise packs | Weird files misclassified |
  | Single-prompt LLM breakpoints | Medium, variable sizes | Messy narrative PDFs | Unreproducible cuts; JSON parse fails |
  | Propositional LLM rewrite | High | Factoid QA over contracts | Destroys procedure order |
  | Agentic per-doc routing | High (many tool/LLM calls) | Extreme heterogeneity | Cannot replay ingest without traces |
  | Contextual prefixes (Anthropic) | High but **cacheable** (~$1.02 / M doc tokens in their writeup with caching) | Long docs, pronouns, “this section of that policy” | Prefix drift if prompt unversioned; PII in prefixes |
  | Late chunking | Embed-time compute on long context; no extra LLM | Models with long-context + mean pool; cross-chunk references | Docs longer than embedder window; APIs that do not expose token states |

* **Failure Modes:**  
  - One recursive rule on mixed 10-Ks, SOPs, tables, and Python: sentence splits on modules, character cuts on 10-column tables—“retrieval looks busy,” generation is wrong.  
  - Skipping all routing *and* MIME detection → Week 7 still retrieves headerless rows and half-functions.  
  - Full agent loop per file before a recursive baseline → unreproducible cuts, no eval replay, Huyen-style over-abstraction.  
  - Shipping contextual prefixes alone without BM25 + rerank and calling it done (Anthropic’s ladder shows the stack compounds).  
  - Assuming OpenAI `text-embedding-3-*` as a black-box per-string API can late-chunk without vendor support for token-state pooling.  
  - Stuffing the whole 10-K into the generator instead of situating chunks → lost-in-middle (arXiv 2307.03172).

* **Average vs. Strong Engineer:**  
  **Average:** starts the FastAPI ingest job with an agent; or never routes MIME types at all.  
  **Strong:** deterministic router with fixture tests per MIME; versions `router_id`, `chunker_id`, contextual-prompt hash, and embedder id on every chunk; adds Anthropic-style prefixes **after** a measured recursive/structure baseline, with prompt caching, combined with BM25 + rerank; uses an agent only as a **classifier** that writes a structured `strategy_id`, then runs **deterministic** splitters; late chunking only when controlling a long-context mean-pool embedder; cost dashboard ($ / million ingested tokens, cache hit rate, p95 ingest latency per MIME). Prefer agents that **label structure**, not agents that emit chunk text if you need eval replay.

* **Worked Example:**  
  Deployment Copilot ships MIME routing + recursive—not Level 5. Golden queries fail on “which policy does ‘it’ refer to?” You add Anthropic-style prefixes on that doc class, version the situating prompt next to Week 5 templates, cache the document while iterating chunks, and keep `strategy_id=contextual_prefix_v1` on nodes. You consider late chunking only if the embedding stack supports token pooling. You do **not** let an agent rewrite chunk boundaries on every file in the corpus.

* **Apply It:**  
  1. Implement a deterministic MIME/heuristic router with unit-tested fixtures before any agent.  
  2. Escalate to contextual prefixes only when anaphora/local-ambiguity queries fail on the golden set; version the prefix prompt.  
  3. If using an agent, restrict it to emitting a structured `strategy_id`; run deterministic splitters afterward.  
  4. Combine contextual embeddings with BM25 (+ rerank when available)—do not ship prefixes alone.  
  5. Treat late chunking as an embedder-architecture choice, not a LangChain checkbox.  
  6. Log ingest $/token and p95 latency per MIME; refuse unreproducible agent-emitted chunk text for eval corpora.

---

### Chunk size and overlap tradeoffs

* **Fundamentals:**  
  **Chunk size** trades **granularity** (small → precise match, less self-contained context) against **completeness** (large → more local context, noisier embedding). Pinecone: too small or too large both produce imprecise search or missed content. Weaviate: oversized chunks mix topics into an averaged vector; undersized chunks fail the “makes sense alone” test and starve the generator.

  **Overlap** is a sliding window so an idea that straddles a cut appears in both neighbors. Weaviate’s fixed-size section treats **10–20%** overlap as the typical starting band. Industry summaries (Firecrawl and others) repeat **~400–512 tokens with 10–20% overlap** as the usual first setting. That is a **heuristic**, not a law.

  Chip Huyen (public platform post): chunk size should reflect **model context limits and application latency**; she refuses a magic number. Open-challenges (2023): RAG phase 1 is chunking/indexing; longer windows let you *squeeze more chunks into generation*, which is not the same as using them well. Liu et al. (arXiv 2307.03172) **lost-in-the-middle**: models use beginnings and ends of long contexts better than the middle. Pinecone 2025: even when o-class / Claude 200k can *fit* un-chunked docs, large blobs raise latency/cost and still suffer lost-in-middle. The fix is passing an **optimal amount** of information downstream—not the whole PDF.

  **Units.** LangChain recursive docs: `chunk_size` is whatever `length_function` returns. Canonical demo uses `len` (characters). Embedders think in **tokens**. A 1000-character English paragraph ≈ 200–300 tokens; the same length of Python or CJK is a different count. Production size/overlap **must** be in **embedding-tokenizer tokens**. Overlap of 200 *characters* on a 1000-character tutorial copy is not 20% of what the embedder saw. Embedder windows are a hard ceiling—overflow truncates silently. **Query shape** matters: short error-code queries want small lexical units; “summarize the refund procedure” wants a complete section.

* **The Alternatives:**  

  | Setting | Argue for | Argue against |
  |---------|-----------|---------------|
  | 128–256 tokens | High precision FAQ; sentence-oriented embedders; error codes | Fragments multi-step procedures; more vectors = storage + ANN + $ |
  | **400–512 tokens** | Fits many embedders; ~few prose paragraphs; common starting band | Still splits tables/code; not sacred |
  | 1024+ tokens | Richer local context; fewer vectors | Diluted embeddings; more lost-in-middle *inside* retrieved context if k is large |
  | 0% overlap | Smaller index; no duplicate bias | Boundary information loss on size-driven splitters |
  | **10–20% overlap** | Cheap insurance when cuts ignore semantics | Duplicate vectors; overlapped phrases rank twice |
  | >30% overlap | Rare pathological boundaries | Index bloat; rerank sees clones; some benches show worse precision |
  | Huge overlap instead of **expansion** | All context in the index | Pays storage forever for a query-time problem |

  **Argue against the 512/15% default:** highly lexical queries often want smaller chunks + hybrid/BM25 (Week 7); parent-document / auto-merging lets **leaf** chunks be 128–256 because **parents** restore context at generate; **chunk expansion** (Pinecone) retrieves neighbors at query time—couple moderate ingest size with expansion instead of 40% overlap; contextual prefixes can replace overlap that existed only to carry the section title; structure-aware splitters: if every chunk is already a full `##` section under the size cap, overlap **does not cross sections** (LangChain markdown docs)—setting `chunk_overlap=200` and seeing no overlap is expected.

  Pinecone’s recommended **sweep**, not a constant: smaller 128/256 for granularity **and** 512/1024 for context, evaluated with **representative queries**, using multiple indices or namespaces.

* **Failure Modes:**  
  - Too small → incomplete answers, “the bot stopped mid-procedure.”  
  - Too large → vaguely related walls of text crowd the prompt; attention dilutes; lost-in-middle.  
  - Character/token mismatch → you think you are at 512 and you are at 900 (truncation), or you think you overlap 20% and you overlap 5% of tokens.  
  - Copy-paste `chunk_size=1000, chunk_overlap=200` from LangChain’s **character** demo onto a **token** embedder without reading `length_function`.  
  - Skipping a sweep → Week 10 evals attribute gains to “hybrid search” that were actually “we accidentally used 256-token chunks.”  
  - Skipping overlap *and* expansion *and* using fixed-size cuts → boundary straddles disappear from every vector.

* **Average vs. Strong Engineer:**  
  **Average:** 512/50 tokens *or* 1000/200 characters from the nearest tutorial; one global constant for code, tables, and prose.  
  **Strong:** sweeps `{256, 512, 1024} × {0%, 10%, 20%}` on a **labeled** query set; records hit@k, MRR, and a human “is the evidence complete?” flag; separate budgets for prose vs code vs tables; sizes in **embedder tokens** with `token_count` / `tokenizer_name` in metadata; prefers **expansion / parent merge** over >20% overlap once the index is large; watches duplicate retrieval (top-5 are three near-clones → lower overlap or diversity/MMR later); re-runs the sweep when the **embedder** changes; for agents, remembers oversized chunks waste session context / tool-calling budget.

* **Worked Example:**  
  Deployment Copilot’s prose fallback is recursive **512 embedding tokens / ~10% overlap**. Before touching Week 7, you embed the same golden 20 queries into namespaces for `{256, 512, 1024} × {0%, 10%, 20%}`. Procedure questions fail completeness at 256 → try 1024 or parent expansion, **not** 40% overlap. Code and tables use separate size policies (next concept). Store `token_count` and `tokenizer_name` on each chunk so a later embedder swap triggers a known re-sweep.

* **Apply It:**  
  1. Define size and overlap in **embedder tokens**, never characters, for the dense index.  
  2. Start prose at ~400–512 / 10–20% as a heuristic only.  
  3. Sweep `{256, 512, 1024} × {0%, 10%, 20%}` on a labeled set before changing strategy.  
  4. Prefer neighbor/parent expansion over >20% overlap for index bloat control.  
  5. Expect zero cross-section overlap after Markdown header split—that is correct.  
  6. Re-sweep when the embedder or tokenizer changes.

---

### Metadata attachment per chunk

* **Fundamentals:**  
  A chunk without metadata is an anonymous vector. LangChain `Document.metadata` and LlamaIndex `Node.metadata` are how you **cite**, **filter**, **ACL**, **debug**, and **replay ingest**. They are not log decoration.

  **Minimum viable fields** for the syllabus RAG chatbot:

  | Key | Why |
  |-----|-----|
  | `source` | Human citation; URL or repo path |
  | `doc_id` | Stable document identity across re-chunk |
  | `chunk_id` / node id | Dedup, expansion, traces |
  | `page` or `header_path` | Grounding (“§3.2 Refunds” / PDF page 4) |
  | `content_type` / MIME | Route evals; hybrid field boosts later |
  | `splitter_id` + versions | Reproducibility (Week 5 analog) |
  | `ingested_at` / `doc_version` | Q3 vs Q4 policy; corpus drift (Week 9) |
  | `tenant_id` / `acl` | Pre-filter so vectors never leak across tenants |

  **Inheritance.** LlamaIndex: child nodes inherit parent document attributes. `MarkdownNodeParser` / LangChain `MarkdownHeaderTextSplitter` write header hierarchy onto each chunk. LangChain character/recursive `create_documents` / `split_documents` **propagate** parent metadata onto splits—use `split_documents` after header split so overlap stays *inside* a section and headers are preserved.

  **LLM extractors (LlamaIndex ingestion pipeline)**—optional for v1: `TitleExtractor`, `QuestionsAnsweredExtractor` (hypothetical questions the node can answer), `SummaryExtractor`, `KeywordExtractor` → `excerpt_keywords`, `EntityExtractor`. These are **extra LLM calls at ingest**.

  **Embed vs LLM visibility.** LlamaIndex is explicit: **by default metadata is concatenated into the text** the embedding model *and* the LLM see. That is a footgun.

  - `excluded_llm_metadata_keys` — hide `file_name`, ACL, PII from the generator while still filtering on them.  
  - `excluded_embed_metadata_keys` — hide keys you do **not** want to bias the bi-encoder (or the inverse: leave `title` in embed, hide from LLM).  
  - `metadata_template` / `text_template` — control serialization (`Metadata: … \n-----\nContent: …`).

  `SentenceSplitter` **subtracts metadata token length from `chunk_size`** so the *serialized* payload fits. If metadata is longer than `chunk_size`, ingest throws (“Metadata length (130) is longer than chunk size (128)”). Vector DB filters only work if the index is configured for them (Pinecone metadata filters, Weaviate properties, pgvector JSONB). ACL must be a **pre-filter**—cannot retrieve then drop (timing and cache leaks). Huyen (pitfalls): retrieval/caching systems have **security and privacy** compliance issues; metadata is where tenant and PII live. Do not embed raw email lists “for better retrieval.”

* **The Alternatives:**  

  | Approach | Benefit | Cost | When it fits |
  |----------|---------|------|--------------|
  | `{source}` only | Demo citations | Cannot filter version/tenant; weak debug | Throwaway demos |
  | Path + page from PDF loader | Cheap, essential | Weak on HTML/Markdown; no section name | PDF-heavy corpora |
  | Header path / breadcrumbs | Grounding + filters (`section == Refunds`) | Needs structure parse | Markdown/HTML wikis |
  | prev/next / parent relationships | Expansion, auto-merge, hierarchical RAG | Schema complexity | Hierarchical indexes |
  | LLM extractors | Rich facets, hypothetical questions | $ / latency; version extractor prompts | After baseline metadata works |
  | Embed all metadata into text | Bi-encoder “sees” titles | Pollutes vector; ACL leakage into neighbors | Avoid for ACL/PII |
  | Filter-only metadata (exclude embed+LLM) | Safe ACL, timestamps | Embedder cannot use title signal | ACL, emails, timestamps |
  | Dual: title in embed, ACL excluded everywhere | Common strong pattern | Must test EMBED vs LLM content modes | Default strong pattern |

* **Failure Modes:**  
  - Cannot cite page/section → enterprise non-negotiable; hallucinations look ungrounded even when the vector was right.  
  - Cannot scope to product version, locale, or doc set (Q3 vs Q4).  
  - Cross-tenant retrieval: filters that are “best effort” after `top_k` are a data leak.  
  - Cannot debug which PDF produced a bad answer (`doc_id`, `splitter_id`, `ingested_at`).  
  - Cannot re-ingest partially without orphaning old vectors.  
  - Cannot compare recursive vs semantic in one index without `splitter_id`.  
  - Classic misdiagnosis: “we need a better embedder” when the query should have been `filter: version=2024-Q3`.  
  - PII in extractors (`EntityExtractor` names/SSNs) expands blast radius into snapshots, logs, and embed APIs.

* **Average vs. Strong Engineer:**  
  **Average:** `{source, page}` from `PyPDFLoader`; ACL ignored until the first enterprise demo; extractors off; metadata stuffed into embed text by default.  
  **Strong:** schema doc for metadata keys (types, filterable, embed/LLM visibility) reviewed like an API; header path on Markdown/HTML; `symbol_name` + `start_line` on code; `table_id` on tables; `excluded_embed_metadata_keys` includes ACL, emails, `ingested_at`; leave `header_path` / title in embed (and usually LLM); filterable indexes created up front; re-chunk = delete by `doc_id`, write new `chunk_id`s, keep `doc_id` stable; LangChain `split_documents` after header split so metadata is not dropped. FDE bar: explain why ACL is pre-filter, not post-filter.

* **Worked Example:**  
  Every Deployment Copilot `Document`/`Node` carries `source`, `header_path` or `symbol_name`, `doc_id`, `ingested_at`, `tenant_id`, `splitter_id`, and `content_type`. `tenant_id` is in `excluded_embed_metadata_keys` and `excluded_llm_metadata_keys`; every query pre-filters `tenant_id`. Header-split Markdown then recursive `split_documents` keeps `Header 1` / `Header 2` on leaves. If `SentenceSplitter` throws metadata-length errors, you stuffed too much JSON—exclude it from serialization rather than raising `chunk_size`.

* **Apply It:**  
  1. Define the MVP metadata schema (table above) before the first bulk ingest.  
  2. Configure embed vs LLM exclusion lists; never embed or prompt ACL/PII.  
  3. Ensure the vector store indexes filterable fields up front.  
  4. Propagate parent metadata through header → size splits (`split_documents`).  
  5. Implement delete-by-`doc_id` re-ingest; keep `doc_id` stable across re-chunks.  
  6. Filter `tenant_id` in the query planner **before** ANN—never as a post-hoc drop.

---

### Tables, code, and structured content vs prose

* **Fundamentals:**  
  Prose splitters (`RecursiveCharacterTextSplitter` defaults, `SentenceSplitter`) assume a **linear narrative** with paragraphs and sentences. **Tables** lose meaning when rows separate from headers. **Code** breaks when a function is cut mid-body. **HTML/Markdown** store hierarchy in tags and ATX headers. **JSON** is a tree, not a novel.

  Pinecone “document structure-based chunking” and Weaviate “document-based chunking” say the same thing: for PDF/HTML/Markdown/LaTeX/code, **parse format-specific elements** (headings, tags, fences, environments, functions) instead of blind character cuts. LangChain groups these under **document structure-based** integrations: Markdown, HTML, JSON, code. LlamaIndex node parsers: `MarkdownNodeParser`, `HTMLNodeParser`, `JSONNodeParser`, `CodeSplitter` (AST via tree-sitter; SweepAI lineage). The **MIME/type router** is the production object. Kamradt Level 3 is this layer. Level 5 (agentic) is an expensive way to choose Level 3 tools. Huyen pitfalls: start with the boring router, not an agent.

  **Markdown / HTML.** `MarkdownHeaderTextSplitter`: split on `#` / `##` / …; attach header path as metadata; default **strips** header lines from body (`strip_headers=False` to keep them). Oversized sections → recursive `split_documents` **inside** the section; overlap does **not** cross H1→H2 boundaries. `HTMLHeaderTextSplitter` is the HTML analog. `HTMLSemanticPreservingSplitter` exists so **tables and lists are not torn across chunks**. Weaviate: convert PDFs to **clean Markdown** (OCR if needed) *before* any of these strategies—naive `pdftotext` + recursive is a trap on columns and scanned pages.

  **Code.** LangChain `RecursiveCharacterTextSplitter.from_language(Language.PYTHON)` uses language-aware separator lists (`class`, `def`, etc.)—still recursive, not a full AST. LlamaIndex `CodeSplitter`: parse AST; `chunk_lines`, `chunk_lines_overlap`, `max_chars` / `count_mode` `"char"|"token"`, `max_tokens`. Metadata should include `symbol_name`, `language`, `start_line` for BM25 on identifiers (Week 7 hybrid). Do not run English sentence regex on source.

  **Tables.** Options, in order of integrity: (1) keep the table intact if it fits the embedder window; (2) **row + replayed column headers** (each row is a mini-record); (3) embed a textual/LLM summary and store raw HTML/CSV in metadata or object storage for the generator to fetch by `table_id`; (4) table-as-image multimodal embeddings when grid lines beat HTML (scanned 10-K exhibits). Never: recursive character split **mid-row**.

  **JSON / APIs.** LangChain `RecursiveJsonSplitter` splits by object/array structure with a size cap. For agent tool schemas, split by **path + method** as the unit, metadata `operation_id`—pretty-print then `chunk_size=1000` loses method identity.

  **Notebooks.** Cell-level chunks (code cells vs markdown cells). Concatenating all cells then fixed-size mixes stdout dumps with functions.

  The Pinecone/Weaviate human test still applies: a headerless row or half-function does **not** make sense alone, so it will not make sense to the model—even if BM25 found the token.

* **The Alternatives:**  

  | Content | Prefer | Avoid |
  |---------|--------|-------|
  | Markdown docs / wikis | Header splitter → recursive fallback; keep `header_path` | Fixed 500-char cuts across `#` sections |
  | HTML product pages | Header or semantic-preserving HTML splitter | `get_text()` then recursive |
  | Code | AST `CodeSplitter` or `from_language`; symbol metadata | Sentence tokenizers; semantic Level 4 |
  | Tables | Whole table / row+headers / summary+raw sidecar | Mid-row character splits |
  | PDFs with layout | Layout/OCR → Markdown or page/layout chunks | Plain dump + recursive only |
  | LaTeX | Environment/section-aware | Treating `$` math as separators |
  | Nested JSON / OpenAPI | Recursive JSON or per-operation nodes | Pretty-print then character chunk |
  | Mixed notebooks | Per-cell, typed metadata | Concatenate then fixed-size |
  | One recursive splitter for everything | Demo speed | Every structured failure mode in this table |

  **Page-level PDF** (industry summaries of NVIDIA 2024 paginated benchmarks) can beat recursive on *true* paginated reports. It is the wrong unit for a 2-page poster or a 1-token running header. Measure. Dual indexes for code: dense on docstrings/comments; sparse/BM25 on identifiers—structure chunking supplies the `symbol_name` hook for Week 7.

* **Failure Modes:**  
  - Support bot cites a pricing table but the chunk is three cells without column names → invents units.  
  - Code copilot RAG returns the middle of a `try` without the `except` → hallucinated APIs.  
  - Runbook bot splits a Markdown numbered procedure across chunks without `header_path` → skips a warning step.  
  - Agent tool-use retrieves a fragment of JSON schema → invalid tool calls (Pinecone: bad chunks → wrong tools, wasted tokens).  
  - Eval dashboards blame the vector DB or the Week 7 retriever.  
  - Skipping the router also poisons semantic/agentic spend: embed-distance-walk a Python file instead of using `CodeSplitter`.

* **Average vs. Strong Engineer:**  
  **Average:** one `RecursiveCharacterTextSplitter` on Unstructured / PyPDF text; tables become whitespace; code is English.  
  **Strong:** router by MIME / extension / `content_type` with unit tests (fixtures: `.md`, `.py`, `.html` table, `.json`, scanned PDF); LangChain/LlamaIndex specialized parsers; fallback recursive **only** for unmarked prose; store table HTML/CSV in metadata or blob store; embed summary or row records; code chunked by symbol with `symbol_name` for BM25; PDF → Markdown first (Docling and similar layout exporters are options—eval on *your* PDFs); metadata `content_type`, `header_path`, `symbol_name`, `table_id`; do not apply 400–512 / 10–20% blindly to AST chunks—function size is the unit until `max_chars` forces a split.

* **Worked Example:**  
  Deployment Copilot ingest routes: `*.md` → `MarkdownHeaderTextSplitter` then recursive fallback inside oversized sections; `*.py` → `from_language(Language.PYTHON)` or LlamaIndex `CodeSplitter` with `symbol_name` / `start_line`; HTML tables → semantic-preserving HTML splitter or row+header records with `table_id`; remaining prose → recursive 512 tokens / ~10% overlap. Golden queries that fail on a pricing table mean **fix the table serializer**, not the cosine metric. A Python module is never fed to `SemanticChunker`.

* **Apply It:**  
  1. Build a MIME/type router with fixtures for Markdown, Python, HTML tables, JSON, and at least one messy PDF extract.  
  2. Wire header splitters before recursive size caps; preserve `header_path`.  
  3. Chunk code by language separators or AST; attach `symbol_name` / `start_line`.  
  4. Never mid-row-split tables; choose intact / row+headers / summary+sidecar.  
  5. Split OpenAPI-like JSON by operation, not by character windows.  
  6. Keep recursive 512/10% as **prose fallback only**—not the policy for structured MIME types.

---

## Week 6 build checklist (end-to-end)

Use this as the chapter’s capstone sequence; every concept above maps here.

1. **Format detect:** Route by MIME / extension / `content_type` with fixture tests (`.md`, `.py`, HTML table, `.json`, messy PDF/text).  
2. **Structure-aware split:** Markdown/HTML headers; code language or AST; JSON by object/operation; tables intact or row+headers.  
3. **Prose fallback:** Recursive (or `SentenceSplitter`) at **~512 embedding-tokenizer tokens / ~10–20% overlap**—not character `len` from a tutorial.  
4. **Second strategy:** Add semantic chunking on the unmarked FAQ/narrative slice only when the golden set shows topic-boundary failures; cap max size; tag `splitter_id`.  
5. **Metadata:** Attach `source`, `page`/`header_path`, `doc_id`, `chunk_id`, `content_type`, `splitter_id`, `ingested_at`/`doc_version`, `tenant_id`/ACL; exclude ACL/PII from embed and LLM text; pre-filter tenants.  
6. **Size sweep:** Evaluate `{256, 512, 1024} × {0%, 10%, 20%}` on a labeled query set before changing strategy or blaming Week 7.  
7. **Escalate carefully:** Contextual prefixes (versioned, cached) or agentic *routing labels* only when evals demand it—do not start at Level 5.  
8. **Persist:** Stable IDs; delete-by-`doc_id` re-ingest; pin splitter/tokenizer/prompt versions next to the index.

When those steps are true, Week 6 is done in the syllabus sense: Deployment Copilot has an ingestion pipeline with at least recursive + semantic paths, rich metadata, and structure-aware handling of messy real docs. Week 7 retrieval cannot rescue mushy or headerless chunks—so do not skip this week for “just dump PDFs into a vector DB.”

---

## Compilation notes

- All concept sections above are grounded in `research/phase-2/week-06-ingestion-chunking/` (`00`–`06`, README synthesis).  
- Covered syllabus concepts: fixed vs recursive, semantic, agentic/LLM chunking (including contextual retrieval and late chunking), size/overlap, metadata per chunk, tables/code/structured content.  
- Open questions left open in research (e.g. whether character `length_function` should ever remain a production default; page-level PDF vs recursive on OCR dumps; post-chunking at query time vs pre-chunked indexes; multimodal table-as-image sizing) are not answered here—see research open-question blocks rather than inventing guidance.  
- No section required `[NEEDS MORE RESEARCH]` for the six syllabus concepts; Chip Huyen material is from public blog posts only, as required by the research corpus.  
- Outside URLs from research are not required reading to understand this chapter; operational detail was inlined from the notes.
