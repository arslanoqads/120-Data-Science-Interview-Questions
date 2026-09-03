# Week 7 Textbook Chapter — Retrieval beyond cosine

> **Status:** COMPLETE  
> **Source:** `research/phase-2/week-07-retrieval-beyond-cosine/`  
> **Chapter:** [chapter.md](chapter.md)

## Concepts covered

- [x] Bi-encoder vs cross-encoder
- [x] Hybrid search (dense + BM25)
- [x] Reciprocal Rank Fusion (RRF)
- [x] Lexical precision failures (why pure cosine fails)
- [x] Vector database selection (pgvector vs dedicated vs hybrid-native)

## Structure check

Each concept includes Fundamentals, The Alternatives, Failure Modes, Average vs. Strong Engineer, Worked Example, and Apply It.

## Syllabus build

Hybrid retrieval (dense ANN + BM25) fused with RRF (`k=60` default); instrument candidate logging on every query.
