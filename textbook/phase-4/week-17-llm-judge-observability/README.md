# Week 17 Textbook Chapter — LLM-as-judge & observability

> **Compile:** COMPLETE  
> **Edit:** COMPLETE  
> **Source:** `research/phase-4/week-17-llm-judge-observability/`  
> **Chapter:** [chapter.md](chapter.md)

## Editorial checklist

- [x] Continuity reviewed (Week 16: error-analysis-first, open coding / custom taxonomy, frequency × impact, synthetic edges, flywheel)  
- [x] Prerequisites Recap added  
- [x] Framing standardized to **What this week builds**  
- [x] Looking ahead → Week 18 (deployment infra: containers, K8s fluency, CI/CD stages, Terraform)  
- [x] Concept structure preserved (6 fields)  
- [x] Language pass for coherence and simplicity  

## Concepts covered

- [x] LLM-as-judge design (critique shadowing)
- [x] Judge alignment / calibration (TPR/TNR vs Week 16 labels)
- [x] Code-based vs model-based evals
- [x] Observability platforms (Langfuse, Arize Phoenix)
- [x] Production monitoring dashboards (cost, latency, errors, quality, drift)

## Structure check

Each concept includes Fundamentals, The Alternatives, Failure Modes, Average vs. Strong Engineer, Worked Example, and Apply It.

## Syllabus build

You already have **Week 16 labels and a custom taxonomy**. This week you **automate residual subjective failures** and **make traces usable as a product**: design binary judges (Pass/Fail + critique) per judgment-heavy failure mode; calibrate against Week 16 labels with **TPR/TNR** gates on held-out splits; prefer **code evals** for objective failures in CI and reserve LLM judges for the rest; instrument hierarchical tracing (Langfuse and/or Phoenix) with generations carrying tokens/cost and retrieved context on the judged observation; ship production dashboards for cost, latency, errors, 1–3 calibrated quality timeseries, and drift — sample online judges (2–10%), keep guardrails in-request, and make alerts open traces. Interview artifact = one calibrated binary judge with TPR/TNR + tracing dashboard screenshot/description (generation with tokens/cost + score) + one code eval that replaced a would-be judge.
