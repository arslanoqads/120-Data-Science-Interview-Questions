# 02 — Audio processing pipeline basics (STT, TTS)

> Week 28 — Multimodal AI  
> Research notes (raw).

---

## Fundamentals

Most production “voice AI” is still a **pipeline**, not a single mystical ear–brain–mouth model:

1. **Capture** — mic stream or uploaded file (WAV/MP3/OGG, sample rate, channels).  
2. **STT (speech-to-text)** — acoustic model → transcript (+ optional timestamps, language, diarization).  
3. **Reason** — your Week 5–15 text stack (prompt, RAG, tools, agents).  
4. **TTS (text-to-speech)** — transcript of the *assistant* → audio bytes for playback.  
5. **Log / redact** — store transcript (and maybe audio) under retention policy.

Chip Huyen (*Multimodality*): speech is often treated as a voice-based alternative to text; STT/TTS remain the common production forms, while non-speech audio is niche. Converting speech to text **loses** volume, intonation, and pauses — know what you discard.

| Stage | Job | Example stacks |
|-------|-----|----------------|
| **STT** | Audio → text | OpenAI `/v1/audio/transcriptions` (`whisper-1`, `gpt-transcribe`); Whisper.cpp local; Gemini audio understanding / transcript prompts |
| **TTS** | Text → audio | OpenAI `/v1/audio/speech` (`tts-1`, `tts-1-hd`, `gpt-4o-mini-tts`); ElevenLabs TTS API |
| **Native audio LLM** | Audio in (± out) without explicit STT | Gemini audio; emerging realtime APIs — still need audit strategy |

Canonical docs:

- OpenAI speech-to-text: https://developers.openai.com/api/docs/guides/speech-to-text  
- OpenAI TTS: https://developers.openai.com/api/docs/guides/text-to-speech  
- Whisper.cpp (C/C++ port for edge/air-gap): https://github.com/ggml-org/whisper.cpp  
- Hugging Face Whisper: https://huggingface.co/openai/whisper-large-v3  
- Gemini audio: https://ai.google.dev/gemini-api/docs/audio  
- ElevenLabs (creative / branded voices): https://elevenlabs.io/docs  

Syllabus voice-input build = prove steps 1–3 end-to-end; TTS is optional sugar with its own latency and brand constraints.

---

## Alternatives & Tradeoffs

| STT choice | Upside | Downside |
|------------|--------|----------|
| Managed Whisper / OpenAI transcriptions | Fast to ship; good accuracy | Data leaves boundary; per-minute cost |
| **Whisper.cpp / Faster-Whisper on-box** | Air-gap; predictable unit cost | GPU/CPU sizing; model update ops |
| Gemini native audio understanding | Richer than pure transcript (non-speech cues) | Tokenization ~32 tokens/sec audio; different eval |
| Streaming / realtime STT | Low perceived latency | Harder partial-hypothesis UX; barge-in |

| TTS choice | Upside | Downside |
|------------|--------|----------|
| OpenAI speech | Simple API; streaming chunk transfer | Fewer “character” voices than specialists |
| **ElevenLabs** | High realism; voice library | Vendor lock; safety / impersonation policy |
| Browser `speechSynthesis` | Free | Quality/brand inconsistency |
| Skip TTS (text only) | Simplest; accessible via screen readers | Not hands-free |

| Pipeline vs native | When it wins |
|--------------------|--------------|
| Classic STT→LLM→TTS | Need **searchable transcripts**, compliance, reuse of text RAG |
| Native audio models | Emotion / non-speech; fewer hops — if you accept opaque audio memory |

---

## Necessity

If you skip pipeline literacy:

- “Voice feature” launches with **no transcript store** — support cannot dispute what was said; Week 16 observability is blind.  
- p95 latency is blamed on the LLM while **STT upload + TTS synthesis** dominate.  
- PII in audio is retained forever because eng only redacted **text** logs.  
- Whisper.cpp is proposed for “privacy” without a model-update and eval story (Week 26-adjacent ops).  
- Teams confuse **translation** endpoints with transcription and silently English-force users (OpenAI translations vs transcriptions).

Without STT/TTS as named stages, voice remains a demo mic button.

---

## Industry Practice

- **Common:** record full utterance → block on Whisper → full LLM → full TTS; no streaming; no language hint; replay last TTS on every page refresh.  
- **Strong:** enforce MIME/size limits; pass `language` / `languages` when known; stream STT and TTS where APIs allow; treat transcript as the **canonical message** in the conversation store; optional TTS behind user preference; measure STT WER on a domain clip set (product names, SKUs).  
- **FDE bar:** diagram the five stages with owners; cite OpenAI STT/TTS guides and Whisper.cpp for offline; know Gemini’s audio token heuristic; refuse shipping TTS that reads secrets or raw tool JSON aloud.

ElevenLabs + Whisper is a frequent teaching stack for voice RAG demos; production still needs the same RAG evals on the **transcript text** as Week 10 — audio is just another ingress.

---

## Concrete Scenario

**OpenAI — File transcription (Speech to text guide)**  
https://developers.openai.com/api/docs/guides/speech-to-text  

Official guidance for bounded recordings: upload audio to `/v1/audio/transcriptions`, choose `gpt-transcribe` (recommended) or `whisper-1` (timestamps / legacy), optionally stream events. Pair with TTS guide for the outbound leg:  
https://developers.openai.com/api/docs/guides/text-to-speech  

For air-gapped labs, mirror the same contract with Whisper.cpp using ggml models from the project’s model docs — same transcript-in / agent / optional-TTS-out shape, different trust boundary.

---

## Open Questions

- When do realtime multimodal models make batch file transcription obsolete for product UX?  
- Should WER or **task success after RAG** be the north-star metric for STT in agents?  
- How aggressive should voice activity detection (VAD) be before cutting utterances mid-SKU?  
- Is synthetic TTS voice cloning ever acceptable for enterprise brand agents under pending regulation?  
- Can one golden audio set serve both STT regression and full agent trajectory evals?

---

## Sources

- https://developers.openai.com/api/docs/guides/speech-to-text  
- https://developers.openai.com/api/docs/guides/text-to-speech  
- https://github.com/ggml-org/whisper.cpp  
- https://github.com/openai/whisper  
- https://huggingface.co/openai/whisper-large-v3  
- https://huggingface.co/docs/transformers/model_doc/whisper  
- https://ai.google.dev/gemini-api/docs/audio  
- https://elevenlabs.io/docs  
- https://huyenchip.com/2023/10/10/multimodal.html  
- https://huyenchip.com/2024/07/25/genai-platform.html  
