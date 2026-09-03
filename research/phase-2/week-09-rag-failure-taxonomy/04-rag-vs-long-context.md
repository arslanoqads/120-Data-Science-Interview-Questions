# 04 — RAG vs long-context tradeoffs

> Week 9 concept research (deep). Legal sources only. Lost-in-the-middle detail also lives in Week 8 `03-lost-in-the-middle.md`; this file is the **architecture choice** (retrieve vs stuff) plus taxonomy labels.

---

## Fundamentals

Two strategies for external knowledge:

1. **RAG** — retrieve a small relevant subset; generate conditioned on that subset (Lewis et al. 2020 lineage; Barnett: embeddings → top-k → consolidator → reader).  
2. **Long-context (LC)** — stuff large portions (or all) of a corpus/document into an extended window.

They are **not mutually exclusive**. Databricks (Quinn Leng, Jacob Portes, Sam Havens, Matei Zaharia, Michael Carbin; blog 2024-08-12; paper arXiv:**2411.03538**) argues long context and RAG are **synergistic**: longer **effective** windows let RAG include more candidates — but **most models degrade after a context size**. Their headline findings from **>2,000 experiments** on 13 models × four datasets (Databricks DocsQA, FinanceBench, HotPotQA, Natural Questions):

- Retrieving **more** documents can help: higher chance the right information is in the prompt; modern LC models can use that — **until they don’t**.  
- Longer context is **not always optimal**: Llama-3.1-405B performance started to decrease after **32k** tokens; GPT-4-0125-preview after **64k**; only a few models stayed consistent across all datasets.  
- Models **fail differently** at long context: copyright refusals, “always summarize the context,” instruction-following collapse — often a lack of long-context post-training, not a single U-curve.

**Advertised context ≫ effective context** (they cite **RULER**). Chip Huyen (public 2023 open-challenges post): **context length ≠ efficient context use**; Lost in the Middle is the prompt-construction example.

### Lost in the Middle (Liu et al., arXiv:2307.03172, TACL 2024)

Controlled **multi-document QA** (RAG analogue): question + *k* Wikipedia passages, **exactly one** gold, *k−1* distractors from Contriever; permute **gold position** and *k*. Accuracy often **U-shaped** (primacy + recency). Extreme: **GPT-3.5-Turbo** with gold in the **middle** can fall **below closed-book 56.1%**. Extended-context models are **not necessarily** better at *using* context than shorter siblings.

Open-domain case study: retriever-reader on NQ-Open; **performance saturates long before retriever recall saturates**. **50 docs instead of 20** only marginally improved (~**1.5%** GPT-3.5-Turbo, ~**1%** Claude-1.3) while the retriever was still recovering more gold. Extra retrieved docs ≠ extra **used** docs.

Taxonomy placement: LITM is a **ranking/assembly + grounding border** failure. Gold **is** in C (not FP2/FP3) but the reader behaves like **FP4 Not Extracted**. Log `packed_position`. Week 8 mitigation: rerank to **5–10**, optionally `LongContextReorder` (edges). Week 9: **injection cell I** (gold at mid packed position).

Barnett AI Tutor lesson **conflicts on GPT-4-class 8K vs 4K** (“larger context got better results… contrary to prior work with GPT-3.5 (Liu et al.)”). Teaching point: **do not** treat 2023 GPT-3.5 U-curves as 2026 SOTA; **do** treat position as an **eval slice**. Databricks shows the modern restatement: more context helps **then** hurts, model-specifically.

### LC vs RAG revisit (Xu et al., arXiv:2501.01880)

Revisit: LC often wins on Wikipedia-style QA when the **corpus fits**; summarization-based retrieval can approach LC; naive chunk RAG lags; RAG retains advantages on **dialogue / general queries** and when full-corpus stuffing is **infeasible**. Use as a counterweight to “always RAG” and to “LC replaces RAG.”

Hamel FAQ (document processing vs RAG): even if a document **fits**, splitting can still help; models are sensitive to distraction; **middle under-attended**; if cost/latency hurts, **filter** before stuffing. “RAG is dead” discourse targets **naive vector DBs for coding agents**, not retrieval-as-such — Claude Code still retrieves, via **agentic search**.

---

## Alternatives & Tradeoffs

| Dimension | Prefer RAG | Prefer Long-Context | Prefer Hybrid |
| --- | --- | --- | --- |
| Corpus size | Millions of docs | Single long doc / small KB that fits | Large corpus + long effective window for top-N |
| Freshness / ACL | Per-doc ACL, incremental update (concept 03) | Rebuild packed prompts; hard to un-see a doc | Retrieve then pack under policy |
| Cost / latency | Fewer tokens per query | High tokens; historically quadratic attention | Retrieve broader, pack until quality plateaus (Databricks sweep) |
| Evidence localization | Natural citations (concept 02) | Attribution across huge prompts | Retrieve with IDs, pack ranked list |
| Failure mode | Missed retrieval (FP1–3) | LITM / effective-length collapse / weird refusals | Joint tune of *K* and model |
| Citations | Snapshot-friendly | Easy to lose span grounding | IDs in packed subset |

Open vs closed (Databricks): some open models peaked ~**16k** packed tokens; some closed models kept gaining toward ~**100k** — **re-evaluate packing whenever the generator changes**.

| Anti-pattern | Why it fails the taxonomy |
|-------------|---------------------------|
| “128k so k=40 is free” | Token $ + LITM + Databricks decrease-after-N | 
| Dump top-50 cosine hits | Week 8: maximize retriever recall then **minimize** what the LLM sees (Pinecone restatement of Liu) |
| LC-only on a million-doc corpus | Infeasible; ACL; drift |
| RAG-only on a 20-page contract the model can hold | Extra retrieval miss risk; Hamel: still consider distraction |

---

## Necessity

Curriculum and production design must kill the false dichotomy **“long context replaces RAG.”** Cost, ACL, citation, freshness, and **effective**-context limits keep retrieval relevant. LC changes **how much** you retrieve and **how you order it**, not whether you need a failure taxonomy.

Service-specific failures:

- **Quality drop as k increases:** cell I / Databricks decrease region — not necessarily a worse embedding.  
- **Copyright refusal / summarize-only** (Databricks deep dives): looks like FP5/FP6 (wrong format / specificity) caused by **long-context post-training**, not your chunker.  
- **Gold packed at position 10 of 20, model quotes distractor #1:** FP4 + LITM; CE already ranked gold #1 and you **buried** it (Week 8 packing bug).  
- **Evaluating only mean accuracy:** U-curve hidden; Liu et al. ask future LC claims to show **small best-vs-worst position gap**.  
- **FinanceBench / 10-K stuffing:** long docs (Databricks table: pages from SEC filings) — RAG still needed at corpus scale (53k docs in their FinanceBench setup).

---

## Industry Practice

**Common:** pick k from the model card (8 or 32); or paste the whole PDF into Gemini because the deck said 2M tokens.

**Strong:**

- Tune **recall curve vs packed-token quality** **per model** (Databricks methodology: embed `text-embedding-3-large`, chunk 512 / stride 256, cap prompt for output+buffer).  
- Put highest-relevance chunks at **beginning and/or end** (Liu U-curve; LlamaIndex `LongContextReorder`).  
- Use LC for **within-doc** reasoning (contracts, transcripts) and RAG for **corpus-scale** search.  
- Re-evaluate packing on generator change — effective context is model-specific.  
- Cohere and others argue large windows don’t replace RAG for freshness, cost, modularity (referenced in Databricks survey of the debate).  
- Anthropic public guidance (elsewhere in this KB): small KBs that fit + prompt cache can skip RAG; beyond that, retrieval is the product.

**FDE bar:** quote Liu U-curve + open-domain saturation numbers as **warnings**, not 2026 SOTA; quote Databricks 32k/64k decrease examples as **model-specific**; classify a long-k miss as FP4/LITM only after confirming gold was packed; never use “we have long context” as a reason to skip Week 9 logs.

---

## Concrete Scenario

Databricks engineering blog with empirical curves across GPT, Claude, Llama, Mistral, DBRX: https://www.databricks.com/blog/long-context-rag-performance-llms  

Companion paper: https://arxiv.org/abs/2411.03538  

Lost in the Middle (controlled multi-doc QA mimicking RAG): https://arxiv.org/abs/2307.03172  

Curriculum injection **cell I:** take Week 8 packed top-8, insert 12 distractors so gold sits at **index 10**, keep query and gold text fixed (Liu’s position knob). Label: ranking/assembly + grounding; Barnett FP4; Jason A|C. Compare to best-first packing (same 8 gold+neighbors).

Xu et al. revisit: https://arxiv.org/abs/2501.01880  

YouTube explainer (U-curve, RAG stuffing, edges vs middle): https://www.youtube.com/watch?v=jt_PAZ5zLq4  

---

## Open Questions

- Optimal routing: retrieve vs stuff-full-doc vs summarize-then-retrieve (Xu: summarization retrieval can approach LC)?  
- Does reranking matter **less** as effective context grows, or **more** (noise sensitivity / Databricks decrease region)?  
- How do agentic multi-step retrieve loops interact with million-token models (Hamel: coding agents already chose agentic search over naive vectors)?  
- Have post-2024 models flattened the U-curve enough to change Week 8 `k=5–10`, or only changed the **shape**? (Week 8 open question; Week 9 still logs `packed_position`.)  
- Barnett 8K>4K on AI Tutor vs Liu GPT-3.5: when is “more context” the FP4 fix vs the FP4 cause?

---

## Sources

- Databricks Long Context RAG Performance: https://www.databricks.com/blog/long-context-rag-performance-llms  
- Leng et al. arXiv:2411.03538: https://arxiv.org/abs/2411.03538  
- Liu et al. Lost in the Middle arXiv:2307.03172 · TACL: https://arxiv.org/abs/2307.03172 · https://aclanthology.org/2024.tacl-1.9/  
- Xu et al. Long Context vs RAG arXiv:2501.01880: https://arxiv.org/abs/2501.01880  
- Barnett et al. (context size lesson; LITM citation): https://arxiv.org/abs/2401.05856  
- Chip Huyen, open challenges (public): https://huyenchip.com/2023/08/16/llm-research-open-challenges.html  
- Chip Huyen, GenAI platform (rank vs inclusion / LITM): https://huyenchip.com/2024/07/25/genai-platform.html  
- Hamel FAQ (RAG not dead; middle distraction): https://hamel.dev/blog/posts/evals-faq/index.html  
- Pinecone rerankers (Week 8 pairing): https://www.pinecone.io/learn/series/rag/rerankers/  
- YouTube: Lost in the Middle explainer https://www.youtube.com/watch?v=jt_PAZ5zLq4  
- YouTube: Hamel How To Approach Your AI Evals https://www.youtube.com/watch?v=DZxaPNYi_k0  
