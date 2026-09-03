# Chapter 29 — AI Safety, Ethics, and Adversarial Testing

> **Phase 7 — Supplementary Electives**  
> **Compilation status:** COMPLETE  
> **Source of truth:** `research/phase-7/week-29-ai-safety-adversarial/`  
> **Syllabus Build:** (1) A **formal adversarial test suite** for the flagship system — malicious and edge-case inputs; **scheduled** runs (CI nightly / weekly deep); explicit **pass/fail criteria** per category (jailbreak, PII leak, tool misuse, bias slices, moderation false-negative traps). (2) A **one-page “Safety & Responsible AI”** doc modeled on fintech / healthcare security reviews: system scope, data classes, threat model, controls, residual risk, escalation owners, evidence links (eval reports, red-team logs). Do not skip this week for “we already refuse bad prompts.”

---

## Chapter framing

Week 29 turns safety from a **feature claim** (“we have a guardrail”) into a **discipline**: scheduled adversarial testing, measurable fairness checks, deliberate moderation architecture, privacy patterns beyond prompt injection, and documentation that survives a regulated-industry security review.

The syllabus why-line is FDE-shaped. Buyers in fintech, healthcare, and government do not ask “did you refuse jailbreaks once?” They ask: who owns the red-team suite, how often it runs, what fails the gate, how bias is measured on production-like slices, which moderation stack you use and why, how PII and tool-call exfiltration are controlled, and where the residual risk is written down.

| Discipline piece | Concept below | Primary question |
|------------------|---------------|------------------|
| Adversarial process | Structured adversarial testing | Is red-teaming on a **schedule** with pass/fail? |
| Fairness | Bias and fairness evaluation | Do we **measure** disparate outcomes on LLM outputs? |
| Moderation architecture | Content moderation API | Buy API vs custom filter — with evidence? |
| Privacy / agency | Security & privacy beyond injection | Beyond injection: PII leak, tool exfil, excessive agency? |
| Audit artifact | Documenting a safety review | Would a bank/hospital security questionnaire accept our one-pager? |

This elective is **supplementary** — it does not replace Weeks 1–24. Suggested slot: after **Week 19** (Auth / identity) so students already know identity, tenancy, and audit logs; alternatively append after the Week 24 capstone. It sits on the **enterprise trust surface** — security + ethics + evidence — not model-lab alignment theory. Cross-links: **Week 5** (prompt injection is necessary but not sufficient), **Week 14** (exfiltration and agency live in tool paths), **Week 15** (adversarial suite is an eval harness with a security posture), **Week 19** (safety docs + identity = regulated-industry trust surface).

Anchors from research: OWASP GenAI LLM Top 10; NIST AI RMF (Govern / Map / Measure / Manage) and Generative AI Profile (NIST AI 600-1); Anthropic red-teaming + Constitutional AI; OpenAI / Azure / Perspective moderation; Garak and Promptfoo for operational suites.

Read the concepts in order. Each section’s **Worked Example** and **Apply It** assume the same flagship service (working title: Deployment Copilot) gaining a **scheduled** adversarial process and a review-grade one-pager — not a one-off guardrail demo.

**Default path (synthesis):**

1. Inventory threats with OWASP LLM Top 10 + your product threat model (tools, RAG, auth).  
2. Stand up **scheduled** red-team / adversarial runs (Promptfoo CI gate + Garak broad scan).  
3. Add **fairness slices** and moderation thresholds with golden sets — measure, don’t assert.  
4. Close privacy gaps: PII in outputs, tool-arg exfiltration, excessive agency (Week 14 side effects).  
5. Ship the **one-pager** + suite evidence; treat it as the enterprise trust surface alongside Week 19 auth.

---

### Structured adversarial testing

* **Fundamentals:**  
  **Ad hoc red-teaming** is what happens when something breaks, a journalist emails, or an engineer pastes a jailbreak into staging. **Structured adversarial testing** is an owned process: threat categories, a versioned attack corpus, scheduled execution, detectors / graders, pass/fail thresholds, and triage SLAs.

  Anthropic’s *Red Teaming Language Models to Reduce Harms* frames red teaming as simultaneous **discovery, measurement, and reduction** — with documented instructions, statistics, and uncertainty — not vibes. Ganguli et al. treat it as a research and engineering process (instructions, attack collection, comparison across model sizes and safety interventions, transparency about uncertainty). The FDE lesson is not “copy Anthropic’s lab” — it is that adversarial work is **methodical, measured, and iterative**, not a one-off hackathon.

  Operational open-source tools make that posture available to product teams:

  | Tool | Role | Cadence fit |
  |------|------|-------------|
  | **Garak** (NVIDIA) | Broad probe library (jailbreak, injection, leakage, toxicity, …) — “nmap for LLMs” | Nightly / weekly full audit |
  | **Promptfoo** red-team | Declarative, app-specific plugins + strategies; CI-native; OWASP/NIST mappings | Per-PR subset + scheduled deep |

  Syllabus mandate: run **on a schedule**, not only after incidents. A formal suite includes malicious inputs, edge cases (encoding, multi-turn crescendo, tool-abuse prompts), and **explicit pass/fail** per category. Week 15 already taught eval harnesses; this week adds a **security posture** — attack success rate (ASR) and policy-violation rate as first-class metrics.

  Minimum process loop:

  1. **Map** threats (OWASP LLM + product-specific: tools, RAG, tenancy).  
  2. **Generate / curate** attacks (static probes + dynamic strategies).  
  3. **Run** against pinned system versions (model, prompt, tools).  
  4. **Grade** with detectors / LLM-as-judge / regex / policy oracles.  
  5. **Gate** on thresholds; open tickets for fails; re-run after fixes.

* **The Alternatives:**  

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

  Tradeoff: overly strict gates create “safety theater” refusals that tank product metrics; overly loose gates ship silent regressions after a model bump. The syllabus selects the **hybrid schedule** posture: Promptfoo for app-specific CI gates, Garak for broad nightly/weekly scan, plus human campaigns for novel domain attacks.

* **Failure Modes:**  
  - Prompt, RAG chunking, or tool-schema changes reintroduce LLM01 Prompt Injection / LLM03 Excessive Agency without anyone noticing.  
  - Sales claims “we red-teamed” but cannot produce last-run date, commit SHA, or fail list.  
  - Week 5 injection lessons never become regression tests.  
  - Multi-turn attacks (crescendo) bypass single-turn CI that only checks DAN strings.  
  - Incident response starts from zero — no baseline attack success rate to compare.  
  - Guardrail demo only: fast narrative, fails the first enterprise questionnaire.  
  - One-time pen-test before launch: external report artifact, then drift after model/prompt/tool changes.

* **Average vs. Strong Engineer:**  
  **Average:** manual jailbreak spreadsheet; run before big demos; results in Notion, never CI; system-prompt refusals and maybe ad-hoc Slack red-team after an incident.  
  **Strong:** `redteam.yaml` in repo; GitHub Action fails PR on risk score; nightly Garak JSONL archived; dashboard of ASR by OWASP category; pin model IDs in every run; threat model mapped to OWASP LLM categories.  
  **FDE bar:** explain why Promptfoo (app-specific) and Garak (broad) complement; show threshold rationale; map findings to OWASP and NIST Measure; schedule human campaigns for novel domain attacks (fraud, PHI social engineering); walk a CISO through last scheduled red-team report with pass/fail.

* **Worked Example:**  
  For Deployment Copilot, the team commits a Promptfoo red-team config with plugins covering jailbreak, PII, excessive agency, and SSRF-style tool abuse, plus multi-turn strategies. A PR-blocking subset runs on every change to prompts, tools, or model IDs. A fuller plugin set runs weekly; Garak runs nightly against the pinned staging endpoint and archives JSONL. Pass/fail is per category (e.g. jailbreak ASR ≤ threshold; zero tolerance on tool-exfil canaries). When a model bump reopens a crescendo jailbreak, CI fails with a dated report and commit SHA — sales can no longer claim “we red-teamed” without evidence. Findings map to OWASP categories and feed the safety one-pager (concept below).

* **Apply It:**  
  1. Map Deployment Copilot threats to OWASP LLM + product-specific surfaces (tools, RAG, tenancy).  
  2. Add a versioned Promptfoo (or equivalent) config with category-tagged attacks and explicit pass/fail thresholds.  
  3. Wire a PR-blocking subset in CI; schedule a deeper weekly run.  
  4. Add nightly/weekly Garak (or equivalent broad scanner) against a pinned system version; archive results.  
  5. Pin model, prompt, and tool versions in every run; record ASR / policy-violation rate by category.  
  6. Define triage SLAs and owners for fails; re-run after fixes.  
  7. Schedule a quarterly human campaign for novel domain attacks the scanners will miss.

---

### Bias and fairness evaluation

* **Fundamentals:**  
  **Bias / fairness evaluation** for LLMs asks whether outputs systematically disadvantage or stereotype groups — or produce unequal quality / refusal / toxicity rates — across slices that matter for the product. It is **not** “we prompted the model to be fair.” It is measurement: defined populations or proxies, metrics, thresholds, and remediation owners.

  NIST AI RMF treats fairness-related risks under trustworthy AI characteristics and pushes organizations to **Map** where harms arise, **Measure** them with appropriate metrics, and **Manage** residual risk — not assert benevolence. For generative systems, NIST’s Generative AI Profile (NIST AI 600-1) highlights risks such as harmful bias and homogenization that classical classification fairness toolkits only partially cover.

  Practical metric families for LLM products:

  | Metric family | Example question | Typical method |
  |---------------|------------------|----------------|
  | Quality parity | Does summarization / answer quality drop for dialect X? | Blind human or judge scores by slice |
  | Toxicity / stereotyping | Are completions more hostile toward group Y? | Perspective / toxicity classifiers + human audit |
  | Allocation / advice parity | Different loan-ish or medical-ish advice by persona? | Counterfactual persona prompts (careful ethics) |
  | Refusal parity | Over-refuse identity topics for some groups? | Refusal rate by template slice |
  | Representation | Who appears in generated examples? | Entity tagging on corpora |

  Chip Huyen’s production LLM writing emphasizes evaluation and system design over slogans: fairness work inherits the same need for **golden sets, regression, and ownership** as accuracy evals (*Building LLM applications for production*; *Building a Generative AI Platform*). Never treat “bias score from one vendor API” as a complete fairness program.

* **The Alternatives:**  

  | Stance | Upside | Downside |
  |--------|--------|----------|
  | Ignore slices; optimize average win rate | Simple dashboards | Hidden disparate failures; enterprise deal risk |
  | Only detox classifiers | Cheap continuous signal | Misses quality / advice disparity |
  | Only human review panels | Nuance | Not continuous; sampling bias |
  | Counterfactual personas everywhere | Stresses model | Ethical landmines; synthetic ≠ real users |
  | **Slice metrics + targeted human audit** | Measurable + contextual | Needs PII-aware data design |

  | Proxy strategy | Tradeoff |
  |----------------|----------|
  | Geo / language / dialect | Available in logs; coarse |
  | Self-identified demographics | Accurate; rare / sensitive |
  | Synthetic demographic prompts | Controllable experiments; validity gaps |

  The syllabus selects **slice metrics + targeted human audit**: continuous signals where cheap, human rubrics where advice products demand nuance, and residual gaps documented on the safety one-pager.

* **Failure Modes:**  
  - Marketing claims “responsible AI” while support tickets show dialect or accent ASR failures cascading into bad LLM answers.  
  - Hiring- or lending-adjacent copilots emit stereotyped career or credit language — legal and reputational blast radius.  
  - Safety filters over-block minority dialects (toxicity false positives), creating unequal access.  
  - Model swaps change stereotype rates with no regression alert.  
  - Week 15 evals celebrate task success on a majority-English golden set and miss slice collapse.  
  - Fairness debates stay anecdotal; no slice metrics for loan, triage, or hiring-adjacent language.

* **Average vs. Strong Engineer:**  
  **Average:** one-time bias brainstorm; screenshot a polite refusal; no slices in CI; ignore slices and optimize average win rate.  
  **Strong:** maintain slice taxonomies per product surface; track toxicity / quality / refusal by slice; calibrate moderation thresholds for disparate false-positive rates; document known residual gaps in the safety one-pager; reuse Perspective for continuous toxicity signals, human rubrics for advice products, Promptfoo plugins for biased/toxic generation.  
  **FDE bar:** map fairness work to NIST Measure; refuse demographic inference from names without policy; show before/after on a stereotype suite after prompt or model change; distinguish **representational** harm from **allocative** harm in customer language.

* **Worked Example:**  
  Deployment Copilot’s support summarizer is evaluated on a majority-English golden set and looks fine. After Week 29, the team adds slice tags (dialect / language templates) and tracks quality score, refusal rate, and Perspective toxicity attributes per slice. A model bump improves average win rate but drops dialect-X quality and raises false-positive toxicity blocks — CI alerts on the slice regression. The safety one-pager states the measured gap, the threshold, the owner, and the compensating control (human review queue for that slice) rather than claiming the product is “unbiased.”

* **Apply It:**  
  1. Define which product surfaces can create representational or allocative harm for Deployment Copilot.  
  2. Choose slice taxonomy and proxy strategy with a PII-aware / ethics review (no casual demographic inference from names).  
  3. Build a small golden set per slice; measure quality, toxicity/stereotype, and refusal parity.  
  4. Add slice metrics to the eval / adversarial dashboard; gate on regressions after model or prompt changes.  
  5. Calibrate moderation thresholds for disparate false-positive rates across slices.  
  6. Document residual fairness gaps and owners on the safety one-pager.

---

### Content moderation API

* **Fundamentals:**  
  **Content moderation** for LLM apps means classifying user inputs and/or model outputs for policy-violating categories (hate, sexual, self-harm, violence, etc.) and then **acting**: block, refuse, rewrite, queue for human review, or rate-limit accounts. The architectural choice is rarely “API or nothing” — it is **which layers** you buy, which you customize, and which you own.

  Major public options (from legal vendor docs in research):

  | Service | Strength | Typical fit |
  |---------|----------|-------------|
  | **OpenAI Moderation** | Free endpoint; text (+ image via omni); category flags + scores | Default first gate on OpenAI-centric stacks |
  | **Azure AI Content Safety** | Severity scales; Prompt Shields; groundedness / protected material | Enterprise Azure; jailbreak + RAG extras |
  | **Perspective API** (Jigsaw) | Toxicity / insult / threat attributes for discussion text | Comments, communities, toxicity continuous scores |

  OpenAI’s moderation guide: treat scores as **signals for your policy**, not an automatic universal blocklist — tune thresholds on your golden set. Docs describe standalone `/moderations` classification and inline moderation alongside generation; recommend `omni-moderation-latest` for new apps; emphasize application-level policy on top of `flagged` / `categories` / `category_scores`. Azure adds **Prompt Shields** for jailbreak / indirect injection signals and groundedness checks useful near RAG. Perspective shines when the product problem is conversational toxicity scoring rather than full multimodal trust-and-safety.

  **Build-your-own** means: open-weight classifiers, regex/blocklists, LLM-as-moderator with a constitution, or hybrid ensembling. Anthropic’s Constitutional AI / classifiers story is the lab-grade version of “policy as natural language → model judges.” Chip Huyen’s platform framing: moderation is part of the **production system**, alongside evals and feedback — not a bolt-on after the demo works.

* **The Alternatives:**  

  | Option | Pros | Cons |
  |--------|------|------|
  | Vendor API only | Fast, maintained categories, low ops | Generic thresholds; data leaves boundary; category mismatch |
  | Custom classifier only | Domain vocabulary; data residency | Training / drift / recall gaps on rare harms |
  | LLM-as-moderator only | Flexible policy text | Cost, latency, self-preferencing, jailbreak of the judge |
  | Blocklist / regex only | Deterministic | Trivial bypass; high false positives |
  | **Ensemble** — vendor API + domain rules + selective LLM judge | Defense in depth | Complexity; need attribution in logs |

  | Decision driver | Prefer buy | Prefer build / hybrid |
  |-----------------|------------|------------------------|
  | Time-to-first-gate | ✓ | |
  | Regulated data residency | | ✓ or Azure private networking |
  | Niche policy (pharma, weapons edge cases) | | ✓ policy layer |
  | UGC comments toxicity | Perspective | |
  | Jailbreak-aware input filter | Azure Prompt Shields / dedicated | |

  Buy-vs-build is a **risk and ops** decision, not a purity contest. The syllabus expects a deliberate matrix (latency, cost, residency, category coverage, jailbreak features) with thresholds validated on a labeled set — not “we call Moderation API” as theater.

* **Failure Modes:**  
  - **False negatives:** harmful completions ship because you trusted model refusals alone.  
  - **False positives:** support meltdown; minority dialect over-blocked (ties to fairness).  
  - **Compliance theater:** “we call Moderation API” with default thresholds never evaluated.  
  - **Data-path surprises:** sending PHI/PII to a third-party moderator without DPA / residency review (Week 19 enterprise).  
  - **Single-layer failure:** attackers bypass one keyword filter that was the only control.  
  - Moderation API with no adversarial suite: low eng cost, blind to app-specific jailbreaks / tool misuse.  
  - Custom filter only: domain vocabulary, but misses broad harm categories and carries a maintenance tax.

* **Average vs. Strong Engineer:**  
  **Average:** OpenAI Moderation on user message only; ignore output; use `flagged` boolean raw; claim vendor API == full Responsible AI program.  
  **Strong:** moderate **input and output**; per-category thresholds; shadow mode before enforce; log `category_scores` for audit; combine Azure Prompt Shields or injection detectors with app allowlists; human review queue for borderline severities.  
  **FDE bar:** present a one-slide decision matrix (latency, cost, residency, category coverage, jailbreak features); show false-positive/negative rates on an internal labeled set; never claim vendor API equals a full Responsible AI program.

* **Worked Example:**  
  Deployment Copilot initially refuses bad prompts in the system message and calls OpenAI Moderation on user input with the default `flagged` gate. Under Week 29, the team runs `omni-moderation-latest` on **user input and assistant output**, tunes hard blocks on self-harm/violence thresholds against a golden set, routes mid-score hate/harassment to a human review queue, and logs `category_scores` for audit. Where RAG and jailbreak-aware input filtering matter, they compare Azure Prompt Shields / groundedness. False-negative traps for the moderation layer are added as categories in the scheduled adversarial suite. The buy-vs-build slide for the CISO shows why they bought the vendor gate first and where a domain policy layer still owns niche refusals.

* **Apply It:**  
  1. Write a one-slide moderation decision matrix (latency, cost, residency, categories, jailbreak features).  
  2. Choose vendor / hybrid layers; document data residency and DPA implications.  
  3. Moderate both input and output; do not rely on model refusals alone.  
  4. Build a labeled golden set; tune per-category thresholds; shadow-mode before enforce.  
  5. Log category scores and actions for audit; attribute which layer fired.  
  6. Add moderation false-negative traps to the adversarial suite.  
  7. Staff or stub a human-review path for mid-severity scores.

---

### Security and privacy beyond injection

* **Fundamentals:**  
  Week 5 taught **prompt injection** (OWASP LLM01). Production incidents and the broader OWASP GenAI LLM Top 10 show that injection is necessary but **not sufficient**. Two FDE-critical siblings:

  1. **Sensitive Information Disclosure (LLM02)** — PII, secrets, system prompts, hidden context, or training/retrieval data appear in outputs (or reasoning channels).  
  2. **Excessive Agency (LLM03 in 2026 ranking)** — tools do too much: exfiltrate data via outbound calls, modify state, or chain actions without adequate authorization.

  The 2026 OWASP list keeps Prompt Injection and Sensitive Information Disclosure at the top and elevates Excessive Agency, reflecting incident-weighted reality for tool-using systems. Privacy / security patterns beyond “sanitize the prompt”:

  | Pattern | Failure mode | Control sketch |
  |---------|--------------|----------------|
  | **Output PII leakage** | Model echoes SSRN / MRN / email from context | DLP on outputs; minimize context; redaction |
  | **Retrieval exfiltration** | Indirect injection in docs → “send secrets to URL” | Context isolation; link allowlists; Dual LLM |
  | **Tool-call exfiltration** | `email.send` / `http.post` args carry secrets | Tool allowlists; arg schemas; egress proxies |
  | **Hidden context exposure** | System prompt / tool schemas leaked | Least-privilege prompts; canary tokens in suite |
  | **Cross-tenant bleed** | Wrong `thread_id` / memory namespace | Week 19 authZ + Week 25 isolation |
  | **Logging side channels** | Traces store raw prompts with secrets | Redacted telemetry; retention policy |

  Chip Huyen’s agents / platform writing stresses tool outputs and side effects as first-class design — privacy engineering must sit on the **tool boundary**, not only the chat box. Simon Willison’s Dual LLM and agent design patterns remain practical references alongside OWASP cheat sheets.

* **The Alternatives:**  

  | Control stack | Upside | Downside |
  |---------------|--------|----------|
  | Prompt-only “never reveal PII” | Cheap | Unreliable under injection |
  | Output regex DLP | Catches common patterns | Misses novel encodings; false positives |
  | Tokenization / vault before LLM | Strong for known PII fields | Breaks UX if overused |
  | Dual LLM / privileged planner | Limits untrusted content power | Latency, complexity (Willison pattern) |
  | No tools / human-only side effects | Small blast radius | Weak product |
  | **Capability-scoped tools + egress policy + output DLP** | Defense in depth | Needs Week 14 + 19 discipline |

  | Exfil path | Prefer |
  |------------|--------|
  | User-visible answer | Output DLP + context minimization |
  | Tool HTTP body | Egress allowlist + arg validation |
  | Retrieval store write | Separate write roles; no secret fields |

  The syllabus selects **capability-scoped tools + egress policy + output DLP**, with canaries in the adversarial suite — not prompt-only “don’t leak PII.”

* **Failure Modes:**  
  - Attacker pastes “ignore previous” into a shared Confluence page (indirect injection) and the agent posts customer PII to an external webhook.  
  - Support bot includes prior-ticket PHI in a summary emailed externally.  
  - Debug traces in an observability vendor contain API keys from tool results.  
  - Model politely refuses bomb recipes but happily dumps `.env` contents present in RAG.  
  - Excessive agency: “cancel all orders” succeeds because the tool trusted the LLM’s intent string.  
  - Team ships “we block DAN prompts” while OWASP Sensitive Information Disclosure and Excessive Agency remain untested.  
  - PII appears in completions or tool arguments; Week 5 injection hardening never checked output egress.

* **Average vs. Strong Engineer:**  
  **Average:** system prompt “don’t leak PII”; tools wrapped with raw HTTP; logs full fidelity forever; only harden against direct jailbreaks.  
  **Strong:** classify data (public / internal / PII / secrets); strip or vault before prompt pack; schema-validate tool args; deny-by-default egress; canary secrets in adversarial suite (Promptfoo PII / SSRF plugins; Garak leakage probes); map findings to OWASP LLM02/LLM03.  
  **FDE bar:** threat-model **each tool**; show authZ checks independent of the LLM (Week 19); demo a failed exfil attempt in the scheduled suite; document residual risk when browsing tools exist; refuse “the model is aligned so we’re fine.”

* **Worked Example:**  
  Deployment Copilot’s agent can `email.send` and `http.post` for ticketing integrations. Week 5 injection tests pass on chat turns, but a poisoned RAG doc instructs the model to POST customer emails to an external URL. After Week 29, tool args are schema-validated, egress is deny-by-default allowlisted, output DLP scans answers for MRN/email patterns, and the adversarial suite includes canary secrets plus Promptfoo PII/SSRF-style tool-abuse plugins. AuthZ on the email tool checks the caller’s tenant independently of the LLM’s intent string (Week 19). The failed exfil attempt appears in the nightly report and is linked from the safety one-pager under residual risk for any remaining browse-capable tools.

* **Apply It:**  
  1. Extend the threat model beyond LLM01 to LLM02 (sensitive disclosure) and LLM03 (excessive agency) for every tool.  
  2. Classify data classes in context packs; minimize or vault PII before the LLM.  
  3. Schema-validate tool arguments; deny-by-default egress; separate write roles for retrieval stores.  
  4. Add output DLP and redacted telemetry (no raw secrets in traces).  
  5. Plant canary secrets / PII patterns in the scheduled suite; include tool-misuse plugins.  
  6. Keep authZ checks independent of the LLM (Week 19); document residual risk for high-agency tools.

---

### Documenting a safety review

* **Fundamentals:**  
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

  Tone: factual, dated, versioned (doc `v1.4`, system release `2026.09.01`). Avoid unverifiable claims (“fully aligned,” “unbiasable”). Prefer “we measure X weekly; threshold Y; last fail on DATE; owner Z.” Audience overlap with Week 19 enterprise reviews: identity, tenancy, audit logs, subprocessors — safety docs should **cross-link** auth and data-processing addenda rather than duplicate them. Anthropic’s public constitution / red-team transparency is a *reference style* for clarity — explicit about principles **and** limits — without copying lab claims you cannot defend.

* **The Alternatives:**  

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

  | Build scope | Pros | Cons |
  |-------------|------|------|
  | Suite only | Catches regressions | Reviewers still ask for written policy |
  | One-pager only | Looks mature in sales | Lies without evidence links |
  | **Suite + one-pager** (syllabus) | Process + artifact | Requires honesty about residual risk |

  The syllabus requires **suite + one-pager**: process evidence and a human-readable control narrative together.

* **Failure Modes:**  
  - Security questionnaires stall for weeks while engineers invent answers per RFP.  
  - Customers assume you have no process; deal requires expensive third-party audit prematurely.  
  - Internal teams disagree on what was promised (sales vs eng).  
  - After an incident, no baseline description of intended controls exists.  
  - Adversarial suite results never connect to a human-readable control narrative.  
  - Enterprise RFP asks for Responsible AI documentation; engineers paste a blog post. Deal stalls.  
  - One-pager only without suite links: looks mature in sales, lies without evidence.

* **Average vs. Strong Engineer:**  
  **Average:** paste OpenAI / Anthropic trust center links; claim inheritance of provider safety; oral answers on a sales call; marketing blog as the “safety doc.”  
  **Strong:** one-pager owned by the FDE/tech lead; quarterly refresh; links to CI red-team reports, moderation threshold doc, data-flow diagram, subprocessors list; alignment to OWASP categories in scope.  
  **FDE bar:** walk a bank CISO through the page in ten minutes; answer “what happens when Measure fails?”; distinguish foundation-model provider controls from **application** controls you own; structure Map → Measure → Manage → Govern with URLs to the last Promptfoo/Garak run and moderation policy.

* **Worked Example:**  
  Deployment Copilot’s sales team is in a fintech RFP. Instead of pasting a provider trust-center URL, the FDE ships `Safety & Responsible AI v1.4` (dated, pinned to release `2026.09.01`): scope (support summarization + ticket tools), data classes, OWASP LLM01–03 in scope, controls (moderation ensemble, tool allowlists, output DLP, Week 19 authZ), Measure links to last weekly Promptfoo report and nightly Garak archive, fairness slice dashboard, residual risk (“browse tool not enabled; residual indirect-injection risk in RAG docs mitigated by egress deny-by-default”), and escalation owners. In a ten-minute CISO walkthrough, every claim has an evidence URL — and sales cannot invent promises that eng never made.

* **Apply It:**  
  1. Draft the one-pager with the seven sections mapped to NIST Govern / Map / Measure / Manage.  
  2. Version and date it; pin to a system release.  
  3. Link live evidence: last adversarial suite, fairness slices, moderation thresholds, data-flow / auth addenda (Week 19).  
  4. State residual risk and compensating controls honestly — no “fully aligned.”  
  5. Name RACI owners and incident / customer-notify paths.  
  6. Schedule a quarterly refresh; treat doc drift after model/provider changes as a Govern failure.  
  7. Practice the ten-minute CISO walkthrough before the next regulated RFP.

---

## Week 29 build checklist (end-to-end)

Use this as the chapter’s capstone sequence; every concept above maps here.

1. **Threat inventory:** OWASP LLM Top 10 + product-specific tools / RAG / auth surfaces.  
2. **Scheduled suite:** Promptfoo (or equivalent) CI subset + deeper weekly run; Garak (or equivalent) nightly/weekly; pin versions; per-category pass/fail.  
3. **Fairness slices:** golden sets + quality / toxicity / refusal metrics; document residual gaps.  
4. **Moderation architecture:** buy/hybrid decision matrix; input+output gates; thresholds on a labeled set; false-negative traps in the suite.  
5. **Privacy beyond injection:** output DLP, tool arg validation, egress policy, canaries for LLM02/LLM03.  
6. **One-pager:** Safety & Responsible AI doc with NIST-shaped sections, owners, residual risk, and evidence links.  
7. **Trust surface:** cross-link Week 19 auth / tenancy / audit logs; refuse “the model is aligned so we’re fine.”

When those steps are true, Week 29 is done in the syllabus sense: safety is a **scheduled, measured, documented control system** — not a checkbox guardrail demo.

---

## Compilation notes

- All concept sections above are grounded in `research/phase-7/week-29-ai-safety-adversarial/` (`00`–`05`, README).  
- No section required `[NEEDS MORE RESEARCH]` for the five syllabus concepts covered in research files `01`–`05`.  
- Outside URLs from research are not required reading to understand this chapter; operational detail was inlined from the notes.  
- Research open questions (CI vs quarterly human budget; proxy ethics; EU AI Act density; tool-arg signing; etc.) remain open and were not answered inventively here.
