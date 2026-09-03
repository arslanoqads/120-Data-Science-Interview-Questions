# 00 — Week overview & syllabus mapping

> Week 29 — AI Safety, Ethics, and Adversarial Testing as a formal discipline  
> Phase 7 elective (supplementary). Suggested after Week 19 (Auth/identity).  
> Research notes (raw).

---

## Fundamentals

Week 29 turns safety from a **feature claim** (“we have a guardrail”) into a **discipline**: scheduled adversarial testing, measurable fairness checks, deliberate moderation architecture, privacy patterns beyond prompt injection, and documentation that survives a regulated-industry security review.

The syllabus why-line is FDE-shaped. Buyers in fintech, healthcare, and government do not ask “did you refuse jailbreaks once?” They ask: who owns the red-team suite, how often it runs, what fails the gate, how bias is measured on production-like slices, which moderation stack you use and why, how PII and tool-call exfiltration are controlled, and where the residual risk is written down.

| Discipline piece | Curriculum file | Primary question |
|------------------|-----------------|------------------|
| Adversarial process | 01 | Is red-teaming on a **schedule** with pass/fail? |
| Fairness | 02 | Do we **measure** disparate outcomes on LLM outputs? |
| Moderation architecture | 03 | Buy API vs custom filter — with evidence? |
| Privacy / agency | 04 | Beyond injection: PII leak, tool exfil, excessive agency? |
| Audit artifact | 05 | Would a bank/hospital security questionnaire accept our one-pager? |

**Cross-links:** Week 5 (prompt injection intro), Week 14 (tool side effects), Week 15 (agent eval harness), Week 19 (auth / enterprise identity). This elective sits on the **enterprise trust surface** — security + ethics + evidence — not model-lab alignment theory.

Anchors: OWASP GenAI LLM Top 10; NIST AI RMF (Govern / Map / Measure / Manage) and Generative AI Profile; Anthropic red-teaming + Constitutional AI; OpenAI / Azure / Perspective moderation; Garak and Promptfoo for operational suites.

**Suggested placement:** after Week 19 so students already know identity, tenancy, and audit logs. Alternatively append after Week 24. It does **not** replace Weeks 1–24.

---

## Alternatives & Tradeoffs

| Path | What you optimize | What you sacrifice |
|------|-------------------|-------------------|
| Guardrail demo only | Fast demo narrative | Fails first enterprise questionnaire |
| One-time pen-test before launch | External report artifact | Drift after model/prompt/tool changes |
| Moderation API with no suite | Low eng cost | Blind to app-specific jailbreaks / tool misuse |
| Custom filter only | Domain vocabulary | Misses broad harm categories; maintenance tax |
| **Scheduled suite + one-pager** (this week) | Auditable process | Needs owners, golden sets, CI time |

| Build scope | Pros | Cons |
|-------------|------|------|
| Suite only | Catches regressions | Reviewers still ask for written policy |
| One-pager only | Looks mature in sales | Lies without evidence links |
| **Suite + one-pager** (syllabus) | Process + artifact | Requires honesty about residual risk |

---

## Necessity

Concrete failure modes if Week 29 is skipped:

- Team ships “we block DAN prompts” while OWASP **Sensitive Information Disclosure** and **Excessive Agency** remain untested.  
- Model or prompt update silently reopens jailbreaks; no nightly gate notices.  
- Fairness debates stay anecdotal; no slice metrics for loan, triage, or hiring-adjacent language.  
- PII appears in completions or tool arguments; Week 5 injection hardening never checked output egress.  
- Enterprise RFP asks for Responsible AI documentation; engineers paste a blog post. Deal stalls.  
- Week 15 evals measure task success only — never **attack success rate** or **policy violation rate**.

Without this week, safety is a checkbox. With it, safety is a scheduled, measured, documented control system.

---

## Industry Practice

- **Common (demo AI):** system-prompt refusals; maybe OpenAI Moderation on inputs; ad-hoc red-team in a Slack thread after an incident.  
- **Strong:** threat model mapped to OWASP LLM categories; Promptfoo red-team in CI; Garak nightly; fairness slices in eval dashboards; moderation thresholds tuned on golden sets; tool allowlists + egress filters; written safety review with owners.  
- **FDE bar:** walk a CISO through NIST Map → Measure → Manage; show last scheduled red-team report with pass/fail; name residual risks; refuse “the model is aligned so we’re fine.”

Production references: Anthropic red-team research and Constitutional Classifiers; OpenAI Moderation guide; Azure Content Safety (Prompt Shields); NIST AI RMF Playbook; NVIDIA garak; Promptfoo red-team docs.

---

## Concrete Scenario

**Anthropic — Red Teaming Language Models to Reduce Harms** (methods, scaling, lessons; dataset release):  
https://www.anthropic.com/research/red-teaming-language-models-to-reduce-harms-methods-scaling-behaviors-and-lessons-learned

Ganguli et al. treat red teaming as a **research and engineering process**: instructions, attack collection (~39k attacks), comparison across model sizes and safety interventions, and transparency about uncertainty. The lesson for FDEs is not “copy Anthropic’s lab” — it is that adversarial work is **methodical, measured, and iterative**, not a one-off hackathon. Pair with operational tooling (Garak / Promptfoo) so the flagship app inherits that process posture.

---

## Open Questions

- How much red-team budget belongs in **CI** (fast plugins) vs **quarterly human** campaigns?  
- Should fairness metrics for generative chat use demographic **proxies**, self-ID, or synthetic personas — and when is each unethical?  
- Will vendor moderation + model refusals converge enough that custom filters die, or will domain policy always need a layer?  
- How do agent tool graphs change the safety review (Week 14) relative to single-turn chatbots?  
- What evidence density satisfies a bank vs a hospital vs a consumer SaaS — same one-pager template?

---

## Sources

- https://www.anthropic.com/research/red-teaming-language-models-to-reduce-harms-methods-scaling-behaviors-and-lessons-learned  
- https://www.anthropic.com/research/claudes-constitution  
- https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/  
- https://www.nist.gov/itl/ai-risk-management-framework  
- https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf  
- https://developers.openai.com/api/docs/guides/moderation  
- https://learn.microsoft.com/en-us/azure/ai-services/content-safety/  
- https://perspectiveapi.com/  
- https://github.com/NVIDIA/garak  
- https://www.promptfoo.dev/docs/red-team/  
- https://huyenchip.com/2024/07/25/genai-platform.html  
