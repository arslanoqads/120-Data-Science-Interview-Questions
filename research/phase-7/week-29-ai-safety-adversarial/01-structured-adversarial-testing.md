# 01 — Structured adversarial testing / red-teaming on a schedule

> Week 29 — AI Safety, Ethics, and Adversarial Testing  
> Research notes (raw).

---

## Fundamentals

**Ad hoc red-teaming** is what happens when something breaks, a journalist emails, or an engineer pastes a jailbreak into staging. **Structured adversarial testing** is a owned process: threat categories, a versioned attack corpus, scheduled execution, detectors / graders, pass/fail thresholds, and triage SLAs.

Anthropic’s *Red Teaming Language Models to Reduce Harms* frames red teaming as simultaneous **discovery, measurement, and reduction** — with documented instructions, statistics, and uncertainty — not vibes. Operational open-source tools make that posture available to product teams:

| Tool | Role | Cadence fit |
|------|------|-------------|
| **Garak** (NVIDIA) | Broad probe library (jailbreak, injection, leakage, toxicity, …) — “nmap for LLMs” | Nightly / weekly full audit |
| **Promptfoo** red-team | Declarative, app-specific plugins + strategies; CI-native; OWASP/NIST mappings | Per-PR subset + scheduled deep |

Syllabus mandate: run **on a schedule**, not only after incidents. A formal suite includes malicious inputs, edge cases (encoding, multi-turn crescendo, tool-abuse prompts), and **explicit pass/fail** per category. Week 15 already taught eval harnesses; this week adds a **security posture** — attack success rate and policy-violation rate as first-class metrics.

Minimum process loop:

1. **Map** threats (OWASP LLM + product-specific: tools, RAG, tenancy).  
2. **Generate / curate** attacks (static probes + dynamic strategies).  
3. **Run** against pinned system versions (model, prompt, tools).  
4. **Grade** with detectors / LLM-as-judge / regex / policy oracles.  
5. **Gate** on thresholds; open tickets for fails; re-run after fixes.

---

## Alternatives & Tradeoffs

| Approach | Upside | Downside |
|----------|--------|----------|
| Human red-team only | High-quality novel attacks | Expensive; not continuous |
| Scanner only (Garak) | Broad known coverage | Weak on app-specific business logic |
| Promptfoo only | CI + custom policy | Narrower “known exploit museum” than Garak |
| Bug bounty | External creativity | Needs triage maturity; late findings |
| **Hybrid schedule** — CI Promptfoo + nightly Garak + quarterly human | Coverage + novelty | Multiple owners / reports to reconcile |

| Pass/fail design | When it wins |
|------------------|--------------|
| Zero-tolerance any jailbreak | High-risk regulated assistants |
| Per-category budgets (e.g. ≤2% ASR) | Consumer chat with known long-tail |
| Severity-weighted risk score | Mixed product surfaces |

Tradeoff: overly strict gates create “safety theater” refusals that tank product metrics; overly loose gates ship silent regressions after a model bump.

---

## Necessity

If adversarial testing is only reactive:

- Prompt, RAG chunking, or tool-schema changes reintroduce LLM01 Prompt Injection / LLM03 Excessive Agency without anyone noticing.  
- Sales claims “we red-teamed” but cannot produce last-run date, commit SHA, or fail list.  
- Week 5 injection lessons never become regression tests.  
- Multi-turn attacks (crescendo) bypass single-turn CI that only checks DAN strings.  
- Incident response starts from zero — no baseline attack success rate to compare.

Scheduled suites turn safety into **change control**: every deploy is compared to yesterday’s ASR.

---

## Industry Practice

- **Common:** manual jailbreak spreadsheet; run before big demos; results in Notion, never CI.  
- **Strong:** `redteam.yaml` in repo; GitHub Action fails PR on risk score; nightly Garak JSONL archived; dashboard of ASR by OWASP category; pin model IDs in every run.  
- **FDE bar:** explain why Promptfoo (app-specific) and Garak (broad) complement; show threshold rationale; map findings to OWASP and NIST Measure; schedule human campaigns for novel domain attacks (fraud, PHI social engineering).

Anthropic’s later Constitutional Classifiers work shows lab-scale continuous red-team hours; product teams approximate with automation + smaller expert bursts.

---

## Concrete Scenario

**Promptfoo — Red teaming documentation** (CI-oriented adversarial testing):  
https://www.promptfoo.dev/docs/red-team/

Promptfoo documents plugins (jailbreak, PII, excessive agency, SSRF-style tool abuse, etc.), multi-turn strategies, and compliance-oriented reporting (OWASP / NIST / MITRE mappings). A shipping team commits a config, runs a PR-blocking subset, and schedules a fuller plugin set weekly — exactly the “process not heroics” shape this week demands. Pair with Garak for model-layer probe breadth: https://github.com/NVIDIA/garak

---

## Open Questions

- Who owns the suite — SecEng, ML platform, or the FDE pod embedding the app?  
- How do you version attacks when the threat landscape moves faster than the product?  
- Should multi-agent systems (Week 13–15) get **per-agent** adversarial suites or one end-to-end graph suite?  
- When is LLM-as-judge grading for harm **too gameable** by the same model family?  
- What ASR is “good enough” for a SOC2 narrative vs a FDA-adjacent narrative?

---

## Sources

- https://www.anthropic.com/research/red-teaming-language-models-to-reduce-harms-methods-scaling-behaviors-and-lessons-learned  
- https://www.anthropic.com/news/next-generation-constitutional-classifiers  
- https://www.promptfoo.dev/docs/red-team/  
- https://www.promptfoo.dev/blog/promptfoo-vs-garak/  
- https://github.com/NVIDIA/garak  
- https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/  
- https://www.nist.gov/itl/ai-risk-management-framework  
- https://huyenchip.com/2023/04/11/llm-engineering.html  
