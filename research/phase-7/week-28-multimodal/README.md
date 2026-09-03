# Week 28 Research Corpus — Multimodal AI

> Phase 7 — Supplementary Electives (Weeks 25–29)  
> **Status:** COMPLETE (deep pass)  
> Raw research corpus (not textbook). Legal sources only.

This directory is the **Phase 7 elective Week 28** research repository. It is **not** a replacement for Weeks 1–24. Suggested slot: **alongside Week 14** (prove range of modalities / I/O) — or append after the Week 24 capstone. Read concept files in order, then the source map.

| # | File | Concept |
|---|------|---------|
| 00 | [00-week-overview.md](00-week-overview.md) | Syllabus mapping: multimodal as product I/O; one E2E path build |
| 01 | [01-image-understanding-vs-generation.md](01-image-understanding-vs-generation.md) | Vision (understand) vs image gen — when to use which |
| 02 | [02-audio-stt-tts-pipeline.md](02-audio-stt-tts-pipeline.md) | Audio processing pipeline basics — STT, TTS |
| 03 | [03-multimodal-input-single-conversation.md](03-multimodal-input-single-conversation.md) | Mixing image + text (and audio) in one conversation / context |
| 04 | [04-genuine-requirement-vs-demo-gimmick.md](04-genuine-requirement-vs-demo-gimmick.md) | When multimodal is a real product requirement vs a demo gimmick |
| — | [99-source-map.md](99-source-map.md) | Master URL / paper / blog / docs index |

## Completeness checklist (Week 28)

- [x] All syllabus Week 28 concepts covered with **7 required fields**  
- [x] **Image understanding vs generation** — OpenAI vision / Images API; Anthropic Claude vision; Gemini image; Hugging Face VLMs  
- [x] **Audio pipeline STT / TTS** — Whisper / Whisper.cpp; OpenAI speech-to-text + TTS; ElevenLabs; Gemini audio  
- [x] **Multimodal input in a single conversation** — mixed image + text content blocks; context/token cost; Week 25 packing  
- [x] **Genuine requirement vs demo gimmick** — decision rubric; accessibility / ops / UX cases that force modalities  
- [x] OpenAI vision + audio + image-generation docs cited  
- [x] Anthropic Claude vision docs cited  
- [x] Google Gemini multimodal / audio docs cited  
- [x] Whisper, Whisper.cpp, ElevenLabs / OpenAI TTS cited  
- [x] Hugging Face (Whisper / VLM / Transformers) cited  
- [x] Chip Huyen public blogs cited (multimodality LMMs; agents tools-as-modalities; genai platform)  
- [x] Cross-links: Week 14 (range); Week 5 (prompts); Week 25 (context engineering)  
- [x] Build task documented: **one small E2E multimodal path** (screenshot→reason **or** voice-input) — design only, no app code in this corpus  
- [x] Per-week research **directory** (not a single thin file)  
- [x] Phase 7 elective note: supplementary; not a replacement for 1–24  

## Syllabus build task (Week 28)

Add **one real multimodal capability** to an existing stack (Phase 2 RAG chatbot or Phase 3 agent). Keep it small: **one working end-to-end multimodal path** you can demo — not a full “multimodal platform.”

Pick **one** of:

1. **Screenshot / error-image path** — user uploads a screenshot (stack trace UI, red error banner, config dialog). Vision model extracts structured error signals; RAG / tools reason with that extraction + docs. Show the image → extracted fields → retrieved passages → answer trail.  
2. **Voice-input path** — mic/audio file → STT (Whisper API or Whisper.cpp) → same text agent/RAG path → (optional) TTS reply. Prove the audio boundary is production-shaped (format limits, latency, transcript logging).

Document in a short design note (this week’s artifact):

1. **Modality contract** — accepted MIME types, size/resolution limits, what is stored vs discarded.  
2. **Context assembly** — how image/audio tokens or transcripts enter the Week 25-style packer (and what is *not* re-sent every turn).  
3. **Eval slice** — 5–10 golden multimodal cases (screenshot + expected diagnosis; or audio + expected transcript intent) with pass/fail.

Do **not** implement application code in this research corpus. Do not ship generation for its own sake if the product need is **understanding**. Flagship FDEs prove **one** honest E2E path rather than five half-wired modality demos.

## Default path (synthesis)

1. Decide **understand vs generate** per surface (01); default to understanding for ops/support.  
2. If voice: treat STT/TTS as **pipelines with SLOs**, not “add a mic button” (02).  
3. Mix modalities in **one conversation** with explicit content blocks and budget (03; Week 25).  
4. Apply the **requirement vs gimmick** rubric before roadmaping (04).  
5. Ship the **single E2E path** + golden cases; cross-check Week 14 “prove range” narrative without inventing a second product.
