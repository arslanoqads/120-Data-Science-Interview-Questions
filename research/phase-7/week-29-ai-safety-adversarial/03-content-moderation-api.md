# 03 — Content moderation API integration — buy vs build

> Week 29 — AI Safety, Ethics, and Adversarial Testing  
> Research notes (raw).

---

## Fundamentals

**Content moderation** for LLM apps means classifying user inputs and/or model outputs for policy-violating categories (hate, sexual, self-harm, violence, etc.) and then **acting**: block, refuse, rewrite, queue for human review, or rate-limit accounts. The architectural choice is rarely “API or nothing” — it is **which layers** you buy, which you customize, and which you own.

Major public options (legal vendor docs):

| Service | Strength | Typical fit |
|---------|----------|-------------|
| **OpenAI Moderation** | Free endpoint; text (+ image via omni); category flags + scores | Default first gate on OpenAI-centric stacks |
| **Azure AI Content Safety** | Severity scales; Prompt Shields; groundedness / protected material | Enterprise Azure; jailbreak + RAG extras |
| **Perspective API** (Jigsaw) | Toxicity / insult / threat attributes for discussion text | Comments, communities, toxicity continuous scores |

OpenAI’s moderation guide: treat scores as **signals for your policy**, not an automatic universal blocklist — tune thresholds on your golden set. Azure adds **Prompt Shields** for jailbreak / indirect injection signals and groundedness checks useful near RAG. Perspective shines when the product problem is conversational toxicity scoring rather than full multimodal trust-and-safety.

**Build-your-own** means: open-weight classifiers, regex/blocklists, LLM-as-moderator with a constitution, or hybrid ensembling. Anthropic’s Constitutional AI / classifiers story is the lab-grade version of “policy as natural language → model judges.”

---

## Alternatives & Tradeoffs

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

---

## Necessity

Wrong moderation architecture causes:

- **False negatives:** harmful completions ship because you trusted model refusals alone.  
- **False positives:** support meltdown; minority dialect over-blocked (ties to fairness, file 02).  
- **Compliance theater:** “we call Moderation API” with default thresholds never evaluated.  
- **Data-path surprises:** sending PHI/PII to a third-party moderator without DPA / residency review (Week 19 enterprise).  
- **Single-layer failure:** attackers bypass one keyword filter that was the only control.

Buy-vs-build is a **risk and ops** decision, not a purity contest.

---

## Industry Practice

- **Common:** OpenAI Moderation on user message only; ignore output; use `flagged` boolean raw.  
- **Strong:** moderate **input and output**; per-category thresholds; shadow mode before enforce; log category_scores for audit; combine Azure Prompt Shields or injection detectors with app allowlists; human review queue for borderline severities.  
- **FDE bar:** present a one-slide decision matrix (latency, cost, residency, category coverage, jailbreak features); show false-positive/negative rates on an internal labeled set; never claim vendor API == full Responsible AI program.

Chip Huyen’s platform framing: moderation is part of the **production system**, alongside evals and feedback — not a bolt-on after the demo works.

---

## Concrete Scenario

**OpenAI — Moderation guide** (official API behavior and categories):  
https://developers.openai.com/api/docs/guides/moderation

The docs describe standalone `/moderations` classification and inline moderation alongside generation, recommend `omni-moderation-latest` for new apps, and emphasize application-level policy on top of `flagged` / `categories` / `category_scores`. A concrete FDE pattern: run omni on user input and assistant output, enforce hard blocks on self-harm/violence thresholds validated on a golden set, and route hate/harassment mid-scores to review — rather than inventing a from-scratch toxicity model on day one. Compare Azure when Prompt Shields / groundedness matter: https://learn.microsoft.com/en-us/azure/ai-services/content-safety/

---

## Open Questions

- Will multimodal moderation stay “free enough” that build-your-own classifiers only win on residency?  
- How should teams grade **refusal quality** when moderation and the chat model both refuse?  
- Can Prompt Shields replace dedicated injection evals (Week 5), or only complement them?  
- What is the right human-review staffing model for mid-severity queues at startup scale?  
- When does on-prem open-weight moderation beat Azure for healthcare data paths?

---

## Sources

- https://developers.openai.com/api/docs/guides/moderation  
- https://developers.openai.com/api/reference/resources/moderations/  
- https://learn.microsoft.com/en-us/azure/ai-services/content-safety/  
- https://learn.microsoft.com/en-us/azure/ai-services/content-safety/concepts/harm-categories  
- https://perspectiveapi.com/  
- https://developers.perspectiveapi.com/s/about-the-api  
- https://www.anthropic.com/research/claudes-constitution  
- https://www.anthropic.com/news/next-generation-constitutional-classifiers  
- https://huyenchip.com/2024/07/25/genai-platform.html  
- https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/  
