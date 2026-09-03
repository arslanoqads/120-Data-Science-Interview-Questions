# 01 — Fixed-size vs recursive character splitting

> Week 6 concept research (deep). Legal sources only. Chip Huyen via public blog only.

---

## Fundamentals

**Fixed-size chunking** (Pinecone: “the most common and straightforward approach”) cuts text every N characters or tokens, optionally with a sliding overlap. It does not look at sentences, paragraphs, or headings. The usual target is the embedding model’s context window (Pinecone examples: 1024 tokens for `llama-text-embed-v2`, 8192 for `text-embedding-3-small`). Overflow is truncated *before* the vector exists, so important tokens never enter retrieval.

**Recursive character splitting** still enforces a size budget, but tries a *hierarchy* of separators first. LangChain’s `RecursiveCharacterTextSplitter` is documented as **the recommended splitter for generic text**. Default separators are `["\n\n", "\n", " ", ""]`: keep paragraphs together; if a piece still exceeds `chunk_size`, split on newlines; then spaces; then characters. That is not “smarter embeddings”—it is cheap string recursion that prefers the strongest remaining semantic unit under a hard cap.

LangChain parameters that actually matter in production:

| Parameter | Role |
|-----------|------|
| `chunk_size` | Max size as measured by `length_function` |
| `chunk_overlap` | Repeated suffix/prefix so a cut sentence still appears in a neighbor |
| `length_function` | Default `len` (characters). Production RAG should pass the **embedding tokenizer** |
| `is_separator_regex` | Treat separator list as regex (CJK punctuation, Thai ZWSP, etc.) |
| `from_language(Language.PYTHON)` / `get_separators_for_language` | Language-specific separator lists for code and markdown |

LlamaIndex’s default `SentenceSplitter` is the sibling default: split on sentence boundaries, then pack sentences until a **token** budget. Same idea as recursive—respect structure, then size—measured in tokenizer units rather than `len()`.

Greg Kamradt’s “5 Levels of Text Splitting” (YouTube + notebook) is the shared vocabulary: **Level 1** character/fixed → **Level 2** recursive → **Level 3** document structure → **Level 4** semantic → **Level 5** agentic. Recursive is the practical baseline before you spend embed/LLM calls.

Chip Huyen’s public platform post does **not** pick a magic splitter. She states the constraint: documents can be 10 tokens or 1M tokens; naively stuffing whole docs makes context unbounded; RAG **requires** splitting into manageable chunks sized by model context and latency. She points practitioners at Pinecone, LangChain, LlamaIndex, and Kamradt. Her 2023 open-challenges post names **chunking (indexing)** as RAG phase 1: gather → divide into chunks → embed → store. Longer generation windows do not retire this step: *how much context a model can use* ≠ *how efficiently it uses it* (Liu et al., lost-in-the-middle, arXiv 2307.03172). Pinecone restates the same for o-class / Claude 200k windows: un-chunked docs may *fit*; latency, cost, and lost-in-middle remain.

Human test (Pinecone and Weaviate, independently): **if a chunk makes sense without surrounding context to a human, it will make sense to the model.** Fixed-size frequently fails that test at mid-sentence cuts. Recursive fails less often on prose that has newlines.

---

## Alternatives & Tradeoffs

| Approach | What you optimize | What you sacrifice |
|----------|-------------------|-------------------|
| Skip chunking / dump PDFs | Demo speed; “long context will save us” | Truncation at embed time; lost-in-middle at generate; unusable citations |
| Fixed-size (chars or tokens) | Predictable lengths; cheapest to implement; Pinecone’s **start here then iterate** | Mid-sentence cuts; orphaned pronouns; headerless table fragments |
| Single-separator `CharacterTextSplitter` (`\n\n` only) | Slightly structure-aware | One separator is brittle across corpora (logs, legal, CJK) |
| Recursive character (LangChain recommended generic) | Structure-first, O(text), no model calls, still size-capped | Weak on unmarked prose / minified JSON; still size-driven |
| LlamaIndex `SentenceSplitter` | Token-aware packing of sentences | Sentence regex is English-biased; huge sentences still need a fallback |
| Document-specific (Markdown/HTML/code/JSON) | Aligns with real structure | Needs a MIME/type router (concept 06) |
| Semantic / LLM / agentic first | Topic coherence / format routing | Ingest $ and latency; skip until recursive evals fail (concepts 02–03) |

Pinecone’s 2025 guide is explicit: **fixed-size will be the best path in most cases; start there and iterate only after it is insufficient.** Recursive is their “great middle ground” between naive character cuts and semantic splitters **while still enforcing size limits**. Those two claims are compatible: use recursive as the *implementation* of “fixed-size with better boundaries,” then measure.

LangChain JS splitter overview: for most use cases start with recursive; only fine-tune if evals demand it. Weaviate: recursive is the usual default for articles/blog posts/papers because it respects natural organization instead of splitting randomly.

CJK / Thai: default `["\n\n", "\n", " ", ""]` will bisect words with no spaces. LangChain documents overriding separators with ASCII/fullwidth/ideographic stops and zero-width space. Recursive is still the algorithm; the separator list is the localization.

---

## Necessity

If Week 6 ships a global `CharacterTextSplitter(chunk_size=1000)` (or worse, concatenated PDF text with no splitter):

1. **Broken-span embeddings.** Half a definition + half the next section averages into a mushy vector. Hybrid search may still hit a keyword; the generator answers from incomplete evidence.
2. **Silent truncation.** Embedder windows drop the tail of “fixed” chunks that were measured in characters, not tokens. A 1000-*character* chunk can be 400 or 900 tokens depending on code vs English.
3. **Citation theater.** Offsets do not line up with sentences humans can quote. Support tickets look like “the bot cited page 4 but the sentence is cut.”
4. **False “vector DB is bad” incidents.** Weaviate: when RAG performs poorly, the issue is often not the retriever—it is the chunks. Week 7 hybrid/RRF cannot restore a mid-word cut.
5. **Over-investment later.** Huyen’s pitfalls post: start too complex (pick a fancy vectordb, skip ingestion quality). Recursive is the cheap control you should have before arguing Pinecone vs Weaviate vs pgvector.

---

## Industry Practice

**Common (demo AI):** copy `RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)` from a tutorial with `length_function=len`. Metadata is `{source}` only. Works on blog posts; fails on runbooks, 10-Ks, and Python.

**Strong:**

- `length_function` = embedding tokenizer (`tiktoken` / model tokenizer). LangChain `from_tiktoken_encoder()` exists so `chunk_size` is in **tokens the embedder sees**.
- Format router first (concept 06); recursive or `SentenceSplitter` as **fallback**, not as the only path.
- Pin `splitter_id`, separator list, tokenizer name, `chunk_size`, `chunk_overlap` next to the index (same versioning debate as Week 5 prompts). Re-ingest is a deploy.
- Golden query set before changing strategy (Pinecone: multiple indices or namespaces; iterative query review).
- Kamradt Level 2 as the documented default in the design doc; Level 3+ as explicit escalations.

**FDE bar:** explain why Pinecone still says start with fixed-size *then* iterate; why LangChain documents recursive as the generic recommended splitter; why character `len` in the official demo is a teaching default, not a production contract.

---

## Concrete Scenario

LangChain’s recursive splitter guide splits a State of the Union transcript with `chunk_size=100`, `chunk_overlap=20`, default separators, `length_function=len`. Chunks break at paragraph/sentence boundaries rather than arbitrary character offsets. That tiny size is **illustrative**—the same code with 512 **embedding tokens** is the syllabus default for unmarked prose.

URL: https://docs.langchain.com/oss/python/integrations/splitters/recursive_text_splitter

Pinecone walks the progression fixed-size → recursive → structure-based → semantic → contextual, and states the two embedding constraints (window truncation; independently meaningful chunks):

https://www.pinecone.io/learn/chunking-strategies/

Weaviate’s recursive section: prioritized separators, keep structurally related units, recommended for unstructured articles:

https://weaviate.io/blog/chunking-strategies-for-rag

Syllabus build: product runbooks + Markdown + Python. After the MIME router, leftover `.txt` / extracted PDF prose goes through recursive **512 embedding-tokenizer tokens / ~10% overlap**. A 20-query golden set that fails on mid-sentence policy definitions is a splitter bug, not a Weaviate vs Pinecone bake-off.

---

## Open Questions

- Should “sane default” **always** be tokens of the embedding tokenizer? LangChain’s canonical demo still uses `length_function=len`. Character size is ~4× noisier across code vs English.
- When is **page-level PDF** chunking (industry writeups citing NVIDIA 2024 paginated-document numbers) better than recursive on OCR dumps that have no reliable `\n\n`?
- Does late chunking (arXiv 2409.04701) or Anthropic contextual prefixes reduce the need for careful recursive separators, or only paper over them at embed time while citations still look like half-sentences?
- Git vs object-store as source of truth for `splitter_id` + separator list (Week 5 prompt-versioning analog).
- Recursive vs LlamaIndex `SentenceSplitter` as the org default—character hierarchy vs sentence packing—on mixed EN/CJK corpora.

---

## Sources

- https://docs.langchain.com/oss/python/integrations/splitters/recursive_text_splitter
- https://docs.langchain.com/oss/python/integrations/splitters/character_text_splitter
- https://docs.langchain.com/oss/javascript/integrations/splitters
- https://www.pinecone.io/learn/chunking-strategies/
- https://weaviate.io/blog/chunking-strategies-for-rag
- https://docs.weaviate.io/academy/py/standalone/chunking
- https://developers.llamaindex.ai/python/framework/module_guides/loading/node_parsers/modules/
- https://github.com/FullStackRetrieval-com/RetrievalTutorials/blob/main/5_Levels_Of_Text_Splitting.ipynb
- https://youtu.be/8OJC21T2SL4
- https://huyenchip.com/2024/07/25/genai-platform.html
- https://huyenchip.com/2023/08/16/llm-research-open-challenges.html
- https://huyenchip.com/2025/01/16/ai-engineering-pitfalls.html
- https://arxiv.org/abs/2307.03172
