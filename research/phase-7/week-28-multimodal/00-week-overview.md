# 00 — Week overview & syllabus mapping

> Week 28 — Multimodal AI  
> Phase 7 elective (supplementary). Suggested alongside Week 14 (prove range).  
> Research notes (raw).

---

## Fundamentals

Week 28 treats **multimodal AI** as product **I/O engineering**, not as “the model can see and hear so we should show that in a demo.” A modality is useful when the user’s ground truth lives outside plain text: a screenshot of a failing UI, a PDF page, a spoken request while driving, a product photo, a waveform of a support call.

Chip Huyen’s *Multimodality and Large Multimodal Models* frames the field: modalities (text, image, audio, video) can be converted or jointly embedded; many “multimodal” products are still **pipelines** (STT → LLM → TTS) rather than a single native model. Her *Agents* essay notes tools can **simulate** multimodality (captioner, OCR, Whisper) when the base model is text-only — an FDE-relevant path when vendor vision is unavailable or too expensive.

| Capability | Job | Typical APIs |
|------------|-----|--------------|
| **Image understanding** | Describe, OCR, classify, reason over pixels | Claude vision; OpenAI image input; Gemini vision |
| **Image generation** | Create / edit pixels from prompts | OpenAI Images / Responses image tool; Gemini image out |
| **STT** | Speech → text | Whisper API / Whisper.cpp; OpenAI transcriptions; Gemini audio |
| **TTS** | Text → speech | OpenAI speech; ElevenLabs |
| **Native multimodal chat** | Multiple content parts in one turn | Messages / Responses / Gemini `contents` with mixed parts |

Syllabus concepts map to files 01–04. The **build** is one small **E2E multimodal path** (screenshot reasoning **or** voice input) documented as design — not a full multimodal suite.

**Suggested placement:** alongside **Week 14** (prove range of system capabilities / I/O). Complements **Week 5** (how you instruct around media) and **Week 25** (images and transcripts are high-cost context). Alternatively append after Week 24. It does **not** replace Weeks 1–24.

---

## Alternatives & Tradeoffs

| Path | What you optimize | What you sacrifice |
|------|-------------------|-------------------|
| Text-only forever | Simple evals, cheap tokens | Blind to screenshots, spoken UX, visual defects |
| Tool-mediated multimodal (OCR/caption/STT → LLM) | Swap models; air-gap STT via Whisper.cpp | Latency hops; lost nuance (intonation, layout) |
| **Native vision / audio models** (this week’s center) | Joint reasoning in one call | Token cost; vendor limits; harder golden sets |
| Generate images in every UI | Demo sparkle | Wrong tool when user needed diagnosis |
| Full voice agent day one | Hands-free narrative | Realtime, barge-in, PII in audio — ops cliff |

| Build scope | Pros | Cons |
|-------------|------|------|
| Five modality buttons | Looks complete | None work under load |
| **One E2E path** (syllabus) | Honest demo; evalable | Narrow surface |
| Understanding + generation both | Portfolio range | Split owners and budgets |

---

## Necessity

Concrete failure modes if Week 28 is skipped:

- Support RAG cannot ingest the **screenshot** the customer already has; agents ask users to retype error codes.  
- “Voice AI” demos call TTS on every reply with no STT latency budget, no transcript audit log, and no PII policy.  
- Image **generation** is sold as “multimodal” while the product never **reads** user images — Week 14 range claim collapses in diligence.  
- Mixed image+text turns blow the Week 25 **attention budget** because every follow-up re-sends full-resolution PNGs.  
- Teams cannot articulate Huyen’s distinction between **native LMMs** and **tool-composed** multimodality in an FDE interview.

Without this week, multimodal stays a slide. With it, modalities are contracts: MIME types, token math, eval slices, and a single shippable path.

---

## Industry Practice

- **Common (demo AI):** upload cat photo → witty caption; mic button that sometimes works on Chrome; DALL·E splash on landing. No golden multimodal set.  
- **Strong:** separate **understand** vs **generate** product surfaces; resize/compress before vision; log STT transcripts as first-class messages; optional TTS behind a toggle; Gemini/Claude/OpenAI content-block patterns; Whisper.cpp or managed STT for edge/air-gap.  
- **FDE bar:** one E2E path with traces (image bytes → vision extract → RAG → answer, or audio → STT → agent); cite Anthropic vision limits, OpenAI STT/TTS guides, Gemini audio token rates; refuse gimmick modalities that do not change user outcomes.

Production references: Anthropic Vision; OpenAI Images / speech-to-text / TTS / image generation; Gemini Files + audio; Whisper.cpp; ElevenLabs; Hugging Face Whisper & VLMs; Chip Huyen multimodality + agents posts.

---

## Concrete Scenario

**OpenAI Cookbook — Image Understanding with RAG**  
https://developers.openai.com/cookbook/examples/multimodal/image_understanding_with_rag/

The cookbook joins **vision** (image understanding via Responses) with **file search** so customer feedback that includes photos can be analyzed with retrieved context — not caption-only. That pattern matches the syllabus build: screenshot/error image → understand → RAG reason. Pair with Anthropic’s vision guide for content-block shape and token estimates:  
https://platform.claude.com/docs/en/build-with-claude/vision  

---

## Open Questions

- Will native audio-in / audio-out models retire STT→LLM→TTS pipelines for most products, or will pipelines remain for auditability?  
- How should Week 10 / 15 eval harnesses score **vision** faithfulness without expensive human raters?  
- When is tool-OCR better than end-to-end vision for dense UI screenshots?  
- Should generated images ever enter the **same** RAG index as customer uploads (poisoning risk)?  
- How do GDPR / retention policies treat raw audio vs transcripts?

---

## Sources

- https://platform.claude.com/docs/en/build-with-claude/vision  
- https://developers.openai.com/cookbook/examples/multimodal/image_understanding_with_rag/  
- https://developers.openai.com/api/docs/guides/images  
- https://developers.openai.com/api/docs/guides/image-generation  
- https://developers.openai.com/api/docs/guides/speech-to-text  
- https://developers.openai.com/api/docs/guides/text-to-speech  
- https://ai.google.dev/gemini-api/docs/audio  
- https://ai.google.dev/gemini-api/docs/image-understanding  
- https://github.com/ggml-org/whisper.cpp  
- https://huyenchip.com/2023/10/10/multimodal.html  
- https://huyenchip.com/2025/01/07/agents.html  
- ../week-25-context-engineering/README.md  
