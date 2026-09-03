# Week 9 Textbook Chapter — RAG failure taxonomy

> **Status:** COMPLETE  
> **Source:** `research/phase-2/week-09-rag-failure-taxonomy/`  
> **Chapter:** [chapter.md](chapter.md)

## Concepts covered

- [x] Three canonical failure modes (recall / ranking / generation-grounding)
- [x] Citation and grounding techniques
- [x] Corpus drift and reindexing strategy
- [x] RAG vs long-context tradeoffs (incl. Lost in the Middle)

## Structure check

Each concept includes Fundamentals, The Alternatives, Failure Modes, Average vs. Strong Engineer, Worked Example, and Apply It.

## Syllabus build

On the Week 7–8 logged RAG stack, do **not** add a new retriever. Deliberately break the pipeline at known loci; classify each broken run with canonical mode (recall / rank / ground), Barnett FP (1–7), and the Jason Liu Q–C–A relationship that failed; keep a portfolio debugging log joined on `retrieval_id`. The log is the artifact — Week 10 turns it into a metric cookbook.
