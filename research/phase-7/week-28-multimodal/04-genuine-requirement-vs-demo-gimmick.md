# 04 — Genuine product requirement vs demo gimmick

> Week 28 — Multimodal AI  
> Research notes (raw).

---

## Fundamentals

**Genuine multimodal requirement:** removing the modality makes the product fail its primary user job or exclude a required class of users/data. **Demo gimmick:** the modality is additive spectacle; the same outcome is available faster via text, and the team cannot name an eval that moves when the modality is ablated.

Chip Huyen (*Open challenges in LLM research*; *Multimodality*): multimodality is powerful for domains that **naturally** mix signals — healthcare (notes + imaging), e-commerce (photo + attributes), accessibility (describe the world). That is different from bolting a mic icon onto a text chatbot to impress a stakeholder.

| Signal | Genuine requirement | Likely gimmick |
|--------|---------------------|----------------|
| User’s evidence is non-text | Screenshot of error; X-ray; shelf photo | “Describe this stock photo” Easter egg |
| Hands/eyes busy | Driver / warehouse / surgeon voice | Voice that only works at a desk with a mouse |
| Accessibility mandate | Alt-text generation; screen-reader-friendly TTS | Autoplay TTS that fights assistive tech |
| Throughput | Visual defect inspection at line rate | One-off generated hero image on marketing site |
| Ablation test | Task success drops when image/audio removed | Metrics unchanged |

Week 14 “prove range” is honest when you show **one** modality that changes outcomes — not five toggles. Week 5 still applies: instructions around media must be clear; Week 25 applies: media taxes the budget.

Decision rubric (use in the build design note):

1. What user artifact exists **before** our app (screenshot, voicemail, SKU photo)?  
2. Can they reasonably **transcribe / describe** it themselves without losing fidelity?  
3. Does a text-only baseline hit the SLO?  
4. Do we have **golden multimodal cases** and an owner for them?  
5. What is the kill criterion (e.g., “if vision extract accuracy < 90% on 20 screenshots, ship OCR-assisted text upload instead”)?

---

## Alternatives & Tradeoffs

| Investment | Upside | Downside |
|------------|--------|----------|
| Text-only + better UX copy | Ships; clear evals | Misses true non-text evidence |
| **One E2E multimodal path** (syllabus) | Credible range; learn ops | Narrow |
| Full omni agent (vision+voice+video+gen) | Keynote energy | Ops cliff; no golden set |
| Tool-composed multimodal only | Cheaper; swap tools | May fail when joint reasoning needed |
| Generation-first roadmap | Viral assets | Does not help support/ops truth |

| Stakeholder ask | FDE response pattern |
|-----------------|----------------------|
| “Add voice for the demo” | Offer STT→same RAG path with 5 audio goldens — or refuse |
| “Make it draw pictures” | Ask who consumes the pixels and what brand review exists |
| “We need GPT-4o vision” | Ask for the screenshot corpus and failure of text paste |

Tradeoff: accessibility features can look like “gimmicks” in a sales demo but are **requirements** under policy — classify by user exclusion, not by wow factor.

---

## Necessity

If you skip the requirement filter:

- Roadmaps fill with modality theater while the text RAG still hallucinates (Week 9).  
- Security scope expands (biometrics-adjacent voice, face images) without legal review.  
- On-call pages on Whisper outages for a feature nobody uses in production traffic.  
- Week 14 portfolio claims “multimodal” and diligence finds only a playground GIF.  
- Context costs (Week 25) blow up from vanity image turns with zero retrieval gain.

Gimmicks are not morally wrong in a lab — they are wrong when they displace the one E2E path that would have closed a real user loop.

---

## Industry Practice

- **Common:** launch blog with generated images + voiceover; production traffic 99% text; no ablation study.  
- **Strong:** PRD checkbox “modality justifies itself under ablation”; shadow-mode vision on support tickets measuring deflection; voice limited to locales with STT WER gates; generation behind a creative workflow with human brand review.  
- **FDE bar:** bring the rubric to the customer workshop; propose screenshot-error **or** voice-input — not both in week one; cite Huyen’s industry examples (health, retail, accessibility) as positive cases; cite OpenAI image-understanding RAG cookbook as the pattern for genuine support multimodal.

Refuse vanity metrics (“% sessions with an image attached”) unless tied to task success.

---

## Concrete Scenario

**Chip Huyen — Multimodality and Large Multimodal Models**  
https://huyenchip.com/2023/10/10/multimodal.html  

Public essay surveying why modalities matter, how LMMs are built (encoders, aligned spaces, Flamingo-style conditioning), and where speech is still mostly STT/TTS. Read alongside *Open challenges* multimodality section — https://huyenchip.com/2023/08/16/llm-research-open-challenges.html — for product domains (medical imaging + notes; product photos + metadata; accessibility) that pass the “genuine requirement” test.

Product counterpart: OpenAI’s image-understanding RAG cookbook shows a **support/feedback** job where photos change analysis quality — not a caption toy:  
https://developers.openai.com/cookbook/examples/multimodal/image_understanding_with_rag/

---

## Open Questions

- Who in the org owns the ablation study — product, applied science, or FDE?  
- How do we price “accessibility multimodal” when usage is low but exclusion risk is high?  
- Will regulators force provenance labels that make gimmick generation more expensive than understanding?  
- Can one Week 15 trajectory eval harness cover text and multimodal without forked tooling?  
- When customers demand “omni,” how do you contractually stage modalities behind kill criteria?

---

## Sources

- https://huyenchip.com/2023/10/10/multimodal.html  
- https://huyenchip.com/2023/08/16/llm-research-open-challenges.html  
- https://huyenchip.com/2025/01/07/agents.html  
- https://huyenchip.com/2024/07/25/genai-platform.html  
- https://developers.openai.com/cookbook/examples/multimodal/image_understanding_with_rag/  
- https://platform.claude.com/docs/en/build-with-claude/vision  
- https://developers.openai.com/api/docs/guides/speech-to-text  
- ../week-25-context-engineering/README.md  
