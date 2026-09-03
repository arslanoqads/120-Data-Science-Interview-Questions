# Week 20 Textbook Chapter — Cost and latency engineering

> **Compile:** COMPLETE  
> **Edit:** COMPLETE  
> **Source:** `research/phase-5/week-20-cost-latency-engineering/`  
> **Chapter:** [chapter.md](chapter.md)

## Editorial checklist

- [x] Continuity reviewed (Week 19: OIDC/SAML, API keys/federation, residency, multi-tenant RBAC)  
- [x] Prerequisites Recap added  
- [x] Framing standardized to **What this week builds**  
- [x] Looking ahead → Week 21 (legacy/messy integration: SQL, tolerant ETL, partial failure, idempotency)  
- [x] Concept structure preserved (6 fields)  
- [x] Language pass for coherence and simplicity  

## Concepts covered

- [x] Model routing (rule / embedding / ML classifier)
- [x] Model cascading and RouteLLM (~15% expensive / ~95% quality)
- [x] Semantic caching (exact vs semantic; threshold; tenant keys)
- [x] Prompt caching, compression, and batching
- [x] Cost-attribution dashboards (tenant × feature × model cube)

## Structure check

Each concept includes Fundamentals, The Alternatives, Failure Modes, Average vs. Strong Engineer, Worked Example, and Apply It.

## Syllabus build

You already have a **containerized, OIDC-gated, tenant-isolated LLM service** (Weeks 18–19). This week you **stop sending every request to the frontier model**. (1) **Route before you generate.** Rules first (&lt;1 ms): path, tier, `task_type`, tools, length. Uncertain traffic → embedding (~5 ms) or a trained classifier (50–100 ms). Never put an LLM-as-router on the hot path unless you measured that it still saves money. (2) **Calibrate a cascade, do not guess a percentage.** Plot quality vs % strong-model calls on *your* golden set. The RouteLLM public headline is **~95% of GPT-4 quality at ~14% GPT-4 calls on MT Bench** (matrix factorization + LLM-judge augmentation). Your production mix will differ; the *shape* of the curve is the deliverable. (3) **Cache in two layers.** Exact-match (hash) for deterministic FAQ; semantic (embedding + threshold) for paraphrases — **tenant in the key**, **off for agentic multi-turn**. Provider **prompt caching** for long static prefixes (system + tools + corpus). (4) **Structure prompts for prefix hits.** Static first, user query last. Monitor `cache_read` vs `cache_write`. Compression and Batch APIs are for the paths that cannot be prefix-cached or are offline. (5) **Attribute every dollar.** Gateway tags: tenant, feature, model, prompt version, router decision, cache class. Cost per **successful task**, not only cost per call. Hard budgets per tenant (Week 19 virtual keys).

Interview artifact = **router decision tree with latency budgets** + **quality-vs-%-strong curve** (or RouteLLM-cited operating point plus “we would re-benchmark”) + **cost cube sketch** (tenant × model × feature) + **before/after $/request**.
