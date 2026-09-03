# 05 — Metadata attachment per chunk

> Week 6 concept research (deep). Legal sources only. Chip Huyen via public blog only.

---

## Fundamentals

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

**Inheritance.** LlamaIndex: child nodes inherit parent document attributes. `MarkdownNodeParser` / LangChain `MarkdownHeaderTextSplitter` write header hierarchy onto each chunk (`Header 1`, `Header 2`, …). LangChain character/recursive `create_documents` / `split_documents` **propagate** parent metadata onto splits—use `split_documents` after header split so overlap stays *inside* a section and headers are preserved (official markdown troubleshooting).

**LLM extractors (LlamaIndex ingestion pipeline).** Official chain examples:

- `SentenceSplitter` or `TokenTextSplitter` (e.g. 512 / 128)
- `TitleExtractor(nodes=5)`
- `QuestionsAnsweredExtractor(questions=3)` — hypothetical questions the node can answer (query-aligned facets)
- `SummaryExtractor(summaries=["prev", "self"])`
- `KeywordExtractor(keywords=10)` → `excerpt_keywords`
- `EntityExtractor` (places, people, orgs)

These are **extra LLM calls at ingest**. They enable hybrid filters and question-style retrieval; they are not required for v1.

**Embed vs LLM visibility.** LlamaIndex is explicit: **by default metadata is concatenated into the text** the embedding model *and* the LLM see. That is a footgun.

- `excluded_llm_metadata_keys` — hide `file_name`, ACL, PII from the generator while still filtering on them.
- `excluded_embed_metadata_keys` — hide keys you do **not** want to bias the bi-encoder (or the inverse: leave `title` in embed, hide from LLM).
- `metadata_template` / `text_template` — control the serialization (`Metadata: … \n-----\nContent: …`).

`SentenceSplitter` **subtracts metadata token length from `chunk_size`** so the *serialized* payload fits. If metadata is longer than `chunk_size`, ingest throws (“Metadata length (130) is longer than chunk size (128)”). Exclude keys from embed/LLM if they should not occupy the window—or stop stuffing JSON blobs into metadata.

**Vector DB filters.** Metadata only works if the index is configured for it (Pinecone metadata filters, Weaviate properties, pgvector JSONB). ACL must be a **pre-filter** (cannot retrieve then drop—timing and cache leaks). Missing `version=2024-Q3` looks like “bad embeddings.”

Huyen (pitfalls): retrieval/caching systems have **security and privacy** compliance issues. Metadata is where tenant and PII live. Do not embed raw email lists “for better retrieval.”

---

## Alternatives & Tradeoffs

| Approach | Benefit | Cost |
|----------|---------|------|
| `{source}` only | Demo citations | Cannot filter version/tenant; weak debug |
| Path + page from PDF loader | Cheap, essential | Weak on HTML/Markdown; no section name |
| Header path / breadcrumbs | Grounding + filters (`section == Refunds`) | Needs structure parse (concept 06) |
| prev/next / parent relationships | Expansion, auto-merge, hierarchical RAG | Schema complexity; store must support refs |
| LLM extractors | Rich facets, hypothetical questions | $ / latency; prompt-version the extractors |
| Embed all metadata into text | Bi-encoder “sees” titles | Pollutes vector; ACL leakage into nearest neighbors |
| Filter-only metadata (exclude embed+LLM) | Safe ACL, timestamps | Embedder cannot use title signal |
| Dual: title in embed, ACL excluded everywhere | Common strong pattern | Must test `get_content(MetadataMode.EMBED)` vs `.LLM` |

Google Cloud + LlamaIndex writeup on hierarchical nodes / auto-merging: structure lives in **relationships and metadata**, not only in the blob. That is how small leaves stay filterable while parents restore context (concept 04).

Weaviate agentic chunking may **tag** chunks with extra metadata for advanced retrieval—same idea, more expensive producer.

---

## Necessity

Without per-chunk metadata you cannot:

1. **Cite** page/section (enterprise non-negotiable; hallucinations look ungrounded even when the vector was right).
2. **Scope** search to product version, locale, or doc set (Q3 vs Q4; “only runbooks”).
3. **Enforce tenant isolation** at retrieve time.
4. **Debug** which PDF produced a bad answer (`doc_id`, `splitter_id`, `ingested_at`).
5. **Re-ingest partially** without orphaning old vectors (stable `doc_id` + delete-by-filter).
6. **Compare** recursive vs semantic in one index (`splitter_id` on each node).

Classic misdiagnosis: “we need a better embedder” when the query should have been `filter: version=2024-Q3` and both versions sit in the same namespace.

ACL failure mode is worse than quality: **cross-tenant retrieval**. Filters that are “best effort” after `top_k` are a data-leak. Put `tenant_id` in the query planner **before** ANN.

PII in metadata: indexes get snapshotted, logged, and sent to embed APIs. If you extract names/SSNs into `EntityExtractor` output, you expanded the blast radius. Huyen’s compliance bullet is this file.

---

## Industry Practice

**Common:** `{source, page}` from `PyPDFLoader`. ACL ignored until the first enterprise demo. Extractors off.

**Strong:**

- Schema doc for metadata keys (types, filterable, embed/LLM visibility) reviewed like an API.
- Header path on Markdown/HTML; `symbol_name` + `start_line` on code; `table_id` on tables (concept 06).
- `excluded_embed_metadata_keys` includes ACL, emails, `ingested_at`; `excluded_llm_metadata_keys` includes ACL and raw file paths if they distract the model; leave `header_path` / title in **both** or at least in embed.
- Vector store **filterable indexes** created up front (unindexed JSON you cannot filter is a trap).
- Ingestion pipeline: splitter → extractors (optional) → embed. Extractor prompts versioned (Week 5).
- Re-chunk: delete by `doc_id`, write new chunks with new `chunk_id`, keep `doc_id` stable.
- LangChain: `split_documents` after header split so metadata is not dropped when applying size/overlap.

LlamaIndex document customization guide is the canonical explanation of default inclusion and the two exclude lists.

---

## Concrete Scenario

LlamaIndex metadata extraction guide chains `SentenceSplitter` with title / keyword / summary / QA / entity extractors and shows enriched node dicts (`excerpt_keywords`, document title) used downstream:

https://developers.llamaindex.ai/python/framework/module_guides/indexing/metadata_extraction/

Usage pattern (`TokenTextSplitter` 512/128 + `TitleExtractor` + `QuestionsAnsweredExtractor` in `IngestionPipeline`):

https://developers.llamaindex.ai/python/framework/module_guides/loading/documents_and_nodes/usage_metadata_extractor/

Document/node metadata modes (`excluded_*`, templates, `get_content`):

https://developers.llamaindex.ai/python/framework/module_guides/loading/documents_and_nodes/usage_documents/

LangChain header metadata + `split_documents` overlap troubleshooting:

https://docs.langchain.com/oss/python/integrations/splitters/markdown_header_metadata_splitter

Hierarchical / auto-merge context (structure in metadata/relationships):

https://cloud.google.com/blog/products/ai-machine-learning/llamaindex-for-rag-on-google-cloud

Syllabus: every `Document`/`Node` carries `source`, `header_path` or `symbol_name`, `doc_id`, `ingested_at`, `tenant_id`. Exclude `tenant_id` from embed and LLM. Filter `tenant_id` on every query. If `SentenceSplitter` throws metadata-length errors, you stuffed too much JSON—exclude it.

---

## Open Questions

- What metadata should be embedded vs filter-only vs LLM-only? (Title/header: usually embed; ACL: never embed/LLM; hypothetical questions: embed-only is a known trick.)
- How to keep metadata consistent under re-chunk / partial re-ingest (content-hash of source bytes + `splitter_id`)?
- PII in extractors—redact before persist, or skip `EntityExtractor` in regulated corpora?
- Should `splitter_id` live in git with Week 5 prompts, or in the object store next to the index snapshot?
- Multi-tenant: one index + filter vs index-per-tenant (isolation vs ops cost)?
- Does Anthropic contextual prefix duplicate `header_path` in the text, and should you then exclude headers from embed to avoid double-counting?

---

## Sources

- https://developers.llamaindex.ai/python/framework/module_guides/indexing/metadata_extraction/
- https://developers.llamaindex.ai/python/framework/module_guides/loading/documents_and_nodes/usage_metadata_extractor/
- https://developers.llamaindex.ai/python/framework/module_guides/loading/documents_and_nodes/usage_documents/
- https://developers.llamaindex.ai/python/framework/module_guides/loading/node_parsers/modules/
- https://developers.llamaindex.ai/python/framework-api-reference/node_parsers/
- https://cloud.google.com/blog/products/ai-machine-learning/llamaindex-for-rag-on-google-cloud
- https://docs.langchain.com/oss/python/integrations/splitters/character_text_splitter
- https://docs.langchain.com/oss/python/integrations/splitters/markdown_header_metadata_splitter
- https://weaviate.io/blog/chunking-strategies-for-rag
- https://www.pinecone.io/learn/chunking-strategies/
- https://huyenchip.com/2025/01/16/ai-engineering-pitfalls.html
- https://huyenchip.com/2024/07/25/genai-platform.html
