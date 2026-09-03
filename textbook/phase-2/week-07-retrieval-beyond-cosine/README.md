# Week 7 Textbook Chapter — Retrieval beyond cosine

> **Compile:** COMPLETE  
> **Edit:** COMPLETE  
> **Source:** `research/phase-2/week-07-retrieval-beyond-cosine/`  
> **Chapter:** [chapter.md](chapter.md)

## Editorial checklist

- [x] Continuity reviewed (Week 6 recursive+semantic chunking, metadata, messy docs, stable `chunk_id`s)  
- [x] Prerequisites Recap added  
- [x] Framing standardized to **What this week builds**  
- [x] Looking ahead → Week 8  
- [x] Concept structure preserved (6 fields)  
- [x] Language pass for coherence and simplicity  

## Concepts covered

- [x] Bi-encoder vs cross-encoder
- [x] Hybrid search (dense + BM25)
- [x] Reciprocal Rank Fusion (RRF)
- [x] Lexical precision failures (why pure cosine fails)
- [x] Vector database selection (pgvector vs dedicated vs hybrid-native)

## Syllabus build

Hybrid retrieval (dense ANN + BM25) fused with RRF (`k=60` default); instrument candidate logging on every query.
