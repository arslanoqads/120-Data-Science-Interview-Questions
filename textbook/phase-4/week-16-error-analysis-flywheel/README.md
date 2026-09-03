# Week 16 Textbook Chapter — Error analysis & the data flywheel

> **Compile:** COMPLETE  
> **Edit:** COMPLETE  
> **Source:** `research/phase-4/week-16-error-analysis-flywheel/`  
> **Chapter:** [chapter.md](chapter.md)

## Editorial checklist

- [x] Continuity reviewed (Week 15: structured agent traces, split scores, trajectory vs outcome, C1–C4 failure patterns)  
- [x] Prerequisites Recap added  
- [x] Framing standardized to **What this week builds**  
- [x] Looking ahead → Week 17 (LLM-as-judge, calibration / TPR/TNR, observability platforms, production dashboards)  
- [x] Concept structure preserved (6 fields)  
- [x] Language pass for coherence and simplicity  

## Concepts covered

- [x] Error-analysis-first workflow (read 20–50 outputs before metrics)
- [x] Open coding and custom failure taxonomy
- [x] Frequency (rate × impact)
- [x] Synthetic data for edge cases
- [x] Data flywheel (production → labels → eval set → regression)

## Structure check

Each concept includes Fundamentals, The Alternatives, Failure Modes, Average vs. Strong Engineer, Worked Example, and Apply It.

## Syllabus build

Do **not** skip to LLM-as-judge dashboards. You already have **structured traces** from Week 15. This week you **read them**: error-analysis pass (≥30 human open-coded; 20–50 after significant changes; ~100 working pool); custom taxonomy (5–10 binary categories); quantify **rate × impact**; synthetic **inputs** through the real stack for undersampled edges; promote labeled failures into a regression eval set (CI + sampled production). Week 17 calibrates residual judges. Interview artifact = taxonomy table with rates + one prompt fix that killed a high-rate category + one failure reserved for a judge + how production sampling refills the set.
