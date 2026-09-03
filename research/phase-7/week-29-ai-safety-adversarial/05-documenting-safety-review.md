# 05 — Documenting a safety review for regulated-industry customers

> Week 29 — AI Safety, Ethics, and Adversarial Testing  
> Research notes (raw).

---

## Fundamentals

A **safety review document** is the artifact a fintech, healthcare, or similarly regulated buyer expects when they ask “how do you handle Responsible AI / model risk?” It is not a manifesto and not a 40-page policy binder for the first meeting. The syllabus build asks for a **one-page “Safety & Responsible AI”** note that still sounds like it would survive a security questionnaire.

Map the page to NIST AI RMF functions so reviewers recognize the shape:

| Section on the one-pager | NIST-ish intent | Evidence to link |
|--------------------------|-----------------|------------------|
| System scope & use case | Map | Architecture diagram; data classes |
| Roles & owners | Govern | RACI: eng, security, legal, on-call |
| Threats & harms in scope | Map | OWASP LLM subset + domain harms |
| Controls | Manage | Moderation, authZ, tool policy, DLP |
| Measurement | Measure | Last adversarial suite; fairness slices |
| Residual risk & limits | Manage | Explicit out-of-scope; known fails |
| Incident / escalation | Govern | SEV definitions; customer notify path |

Tone: factual, dated, versioned (doc `v1.4`, system release `2026.09.01`). Avoid unverifiable claims (“fully aligned,” “unbiasable”). Prefer “we measure X weekly; threshold Y; last fail on DATE; owner Z.”

Audience overlap with Week 19 enterprise reviews: identity, tenancy, audit logs, subprocessors — safety docs should **cross-link** auth and data-processing addenda rather than duplicate them.

---

## Alternatives & Tradeoffs

| Artifact | Pros | Cons |
|----------|------|------|
| Marketing blog only | Pretty | Rejected by InfoSec |
| Full model risk management pack day one | Impressive | Slow; often fiction |
| Oral answers on a sales call | Fast | No audit trail |
| **One-pager + evidence links** | Right density for early review | Must stay truthful as system changes |
| Vendor safety PDFs only | Borrowed authority | Doesn’t cover *your* tools/RAG |

| Honesty level | Outcome |
|---------------|---------|
| Hide residual risk | Later breach of trust in procurement |
| Dump every research caveat | Buyer panic without context |
| **State residual risk + compensating controls** | Credible FDE posture |

---

## Necessity

Without a review-grade document:

- Security questionnaires stall for weeks while engineers invent answers per RFP.  
- Customers assume you have no process; deal requires expensive third-party audit prematurely.  
- Internal teams disagree on what was promised (sales vs eng).  
- After an incident, no baseline description of intended controls exists.  
- Adversarial suite results (file 01) never connect to a human-readable control narrative.

Documentation is part of the **control system** — Govern in NIST language — not paperwork afterthought.

---

## Industry Practice

- **Common:** paste OpenAI / Anthropic trust center links; claim inheritance of provider safety.  
- **Strong:** one-pager owned by the FDE/tech lead; quarterly refresh; links to CI red-team reports, moderation threshold doc, data-flow diagram, subprocessors list; alignment to OWASP categories in scope.  
- **FDE bar:** walk a bank CISO through the page in ten minutes; answer “what happens when Measure fails?”; distinguish foundation-model provider controls from **application** controls you own.

Anthropic’s public constitution / red-team transparency is a *reference style* for clarity — your one-pager should be similarly explicit about principles **and** limits, without copying lab claims you cannot defend.

---

## Concrete Scenario

**NIST AI RMF** landing + AI 100-1 publication (voluntary framework used in enterprise questionnaires):  
https://www.nist.gov/itl/ai-risk-management-framework  
https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-ai-rmf-10

Procurement and InfoSec teams frequently phrase Responsible AI asks in RMF vocabulary (or map ISO / internal policies to it). An FDE who can produce a one-pager structured as Map → Measure → Manage → Govern, with URLs to the last Promptfoo/Garak run and moderation policy, matches how regulated buyers already review vendors — especially when paired with Week 19 auth and logging evidence.

---

## Open Questions

- Is a single page enough for HIPAA-adjacent copilots, or must clinical safety cases always expand?  
- How do you version the doc when the model provider changes safety behavior underneath you?  
- Should residual risk be customer-visible or under NDA only?  
- Where does EU AI Act / sector guidance force more than NIST-shaped narrative?  
- Who signs the page — CTO, CISO, or product GM — for legal weight?

---

## Sources

- https://www.nist.gov/itl/ai-risk-management-framework  
- https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-ai-rmf-10  
- https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf  
- https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/  
- https://www.anthropic.com/research/claudes-constitution  
- https://www.anthropic.com/research/red-teaming-language-models-to-reduce-harms-methods-scaling-behaviors-and-lessons-learned  
- https://developers.openai.com/api/docs/guides/moderation  
- https://www.promptfoo.dev/docs/red-team/  
- https://huyenchip.com/2024/07/25/genai-platform.html  
- https://huyenchip.com/2023/04/11/llm-engineering.html  
