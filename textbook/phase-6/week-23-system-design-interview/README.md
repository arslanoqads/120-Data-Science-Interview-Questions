# Week 23 Textbook Chapter — System design interview

> **Compile:** COMPLETE  
> **Edit:** COMPLETE  
> **Source:** `research/phase-6/week-23-system-design-interview/`  
> **Chapter:** [chapter.md](chapter.md)

## Editorial checklist

- [x] Continuity reviewed (Week 22: scope freeze, eval-driven fixes, 5-min demo narrative)  
- [x] Prerequisites Recap added  
- [x] Framing standardized to **What this week builds**  
- [x] Looking ahead → Week 24 (portfolio positioning: resume language, portfolio under 5 min, dual-track AI Engineer vs FDE)  
- [x] Concept structure preserved (6 fields)  
- [x] Language pass for coherence and simplicity  

## Concepts covered

- [x] Retrieval system design (~10M docs, mixed query types)
- [x] Prompt debugging under time pressure
- [x] FDE integration case study
- [x] Narrating tradeoffs aloud
- [x] STAR technical case studies

## Structure check

Each concept includes Fundamentals, The Alternatives, Failure Modes, Average vs. Strong Engineer, Worked Example, and Apply It.

## Syllabus build

Syllabus treats Week 23 as **interview meta-work**: you already shipped Weeks 6–22 systems. This week you **rehearse packaging** under time pressure.

1. **Whiteboard a 10M-doc assistant.** Pin N, QPS, p95, freshness, ACL, wrong-answer cost. Split offline vs online. Force hybrid + ACL pre-filter + incremental deletes + rerank budget + abstain + eval gate.  
2. **Run the prompt-debug ladder live.** Reproduce → localize layer → minimize → one hypothesis → golden lock. Never jump to “bigger model” first.  
3. **Rehearse one FDE integration case.** Customer won’t give prod data / SSO blocked / undocumented API — what do you ship Monday?  
4. **Bank 8–10 STAR stories** from *your* build (chunk fix, hybrid exact-ID, ACL filter-before-rank, eval taxonomy, tool schema, messy SQL, cost/cache, scope freeze). Quantify; reject an alternative aloud; survive follow-ups.

Interview artifact = **annotated 10M whiteboard** + **one timed prompt-debug transcript** + **one FDE unblock case** + **STAR index (title / metric / systems / 3 follow-ups)** + **tradeoff one-liners**.
