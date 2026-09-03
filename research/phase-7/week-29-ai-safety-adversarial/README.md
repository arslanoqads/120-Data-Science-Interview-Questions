# Week 29 Research Corpus — AI Safety, Ethics, and Adversarial Testing

> Phase 7 — Supplementary Electives (Weeks 25–29)  
> **Status:** COMPLETE (deep pass)  
> Raw research corpus (not textbook). Legal sources only.

This directory is the **Phase 7 elective Week 29** research repository. It is **not** a replacement for Weeks 1–24. Suggested slot: after Week 19 (Auth / identity) — enterprise trust surface — or append after the Week 24 capstone. Read concept files in order, then the source map.

| # | File | Concept |
|---|------|---------|
| 00 | [00-week-overview.md](00-week-overview.md) | Syllabus mapping: turn “I built a guardrail” into scheduled adversarial process |
| 01 | [01-structured-adversarial-testing.md](01-structured-adversarial-testing.md) | Structured adversarial testing / red-teaming on a schedule |
| 02 | [02-bias-fairness-evaluation.md](02-bias-fairness-evaluation.md) | Bias and fairness evaluation for LLM outputs |
| 03 | [03-content-moderation-api.md](03-content-moderation-api.md) | Content moderation API vs build-your-own filter |
| 04 | [04-security-privacy-beyond-injection.md](04-security-privacy-beyond-injection.md) | PII leakage, tool-call exfiltration, patterns beyond prompt injection |
| 05 | [05-documenting-safety-review.md](05-documenting-safety-review.md) | Safety review docs regulated customers expect |
| — | [99-source-map.md](99-source-map.md) | Master URL / framework / tool index |

## Completeness checklist (Week 29)

- [x] All syllabus Week 29 concepts covered with **7 required fields**  
- [x] **Structured adversarial testing** — schedule, suite ownership, pass/fail; Garak + Promptfoo; Anthropic red-team research  
- [x] **Bias / fairness evaluation** — slice metrics, demographic proxies, NIST AI RMF Measure; not vibe checks  
- [x] **Content moderation APIs** — OpenAI Moderation, Azure Content Safety, Perspective; buy vs build decision matrix  
- [x] **Security / privacy beyond injection** — OWASP LLM Sensitive Information Disclosure, Excessive Agency, tool exfiltration  
- [x] **Safety review documentation** — one-pager modeled on fintech/healthcare asks; NIST Govern/Map/Measure/Manage  
- [x] OWASP LLM Top 10 cited (official GenAI project)  
- [x] NIST AI RMF + Generative AI Profile cited  
- [x] Anthropic constitution / red-team blogs cited  
- [x] OpenAI Moderation, Azure Content Safety, Perspective cited  
- [x] Garak + Promptfoo cited  
- [x] Chip Huyen public blogs cited where relevant  
- [x] Build task documented (suite + one-pager); **no code implemented in this corpus**  
- [x] Per-week research **directory** (not a single thin file)  
- [x] Phase 7 elective note: supplementary; cross-links Weeks 5, 14, 15, 19  

## Syllabus build task (Week 29)

Document only in this README — **do not implement code** in the research corpus:

1. **Formal adversarial test suite** for the flagship system — malicious and edge-case inputs; **scheduled** runs (CI nightly / weekly deep); explicit **pass/fail criteria** per category (jailbreak, PII leak, tool misuse, bias slices, moderation false-negative traps).  
2. **One-page “Safety & Responsible AI” doc** modeled on what fintech / healthcare security reviews ask: system scope, data classes, threat model, controls, residual risk, escalation owners, evidence links (eval reports, red-team logs).

Do not skip this week for “we already refuse bad prompts.” Flagship systems in regulated industries need a **process** with owners, cadence, and audit artifacts — not a one-off guardrail demo.

## Default path (synthesis)

1. Inventory threats with OWASP LLM Top 10 + your product threat model (tools, RAG, auth).  
2. Stand up **scheduled** red-team / adversarial runs (Promptfoo CI gate + Garak broad scan).  
3. Add **fairness slices** and moderation thresholds with golden sets — measure, don’t assert.  
4. Close privacy gaps: PII in outputs, tool-arg exfiltration, excessive agency (Week 14 side effects).  
5. Ship the **one-pager** + suite evidence; treat it as the enterprise trust surface alongside Week 19 auth.

## Cross-links

| Week | Why |
|------|-----|
| Week 5 — prompt injection | Injection is necessary but not sufficient |
| Week 14 — side effects / tools | Exfiltration and agency live in tool paths |
| Week 15 — agent eval | Adversarial suite is an eval harness with a security posture |
| Week 19 — auth / enterprise | Safety docs + identity = regulated-industry trust surface |
