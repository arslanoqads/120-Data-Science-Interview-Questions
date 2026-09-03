# Week 9 Textbook Chapter — RAG failure taxonomy

> **Compile:** COMPLETE  
> **Edit:** COMPLETE  
> **Source:** `research/phase-2/week-09-rag-failure-taxonomy/`  
> **Chapter:** [chapter.md](chapter.md)

## Editorial checklist

- [x] Continuity reviewed (Week 8 two-stage rerank, one query transform, measured delta, append-only `rerank.*` / `packed_position` logs)  
- [x] Prerequisites Recap added  
- [x] Framing standardized to **What this week builds**  
- [x] Looking ahead → Week 10  
- [x] Concept structure preserved (6 fields)  
- [x] Language pass for coherence and simplicity  

## Concepts covered

- [x] Three canonical failure modes (recall / ranking / generation-grounding)
- [x] Citation and grounding techniques
- [x] Corpus drift and reindexing strategy
- [x] RAG vs long-context tradeoffs (incl. Lost in the Middle)

## Structure check

Each concept includes Fundamentals, The Alternatives, Failure Modes, Average vs. Strong Engineer, Worked Example, and Apply It.

## Syllabus build

On the Week 7–8 logged RAG stack, do **not** add a new retriever. Deliberately break the pipeline at known loci; classify each broken run with canonical mode (recall / rank / ground), Barnett FP (1–7), and the Jason Liu Q–C–A relationship that failed; keep a portfolio debugging log joined on `retrieval_id`. The log is the artifact — Week 10 turns it into a metric cookbook.
