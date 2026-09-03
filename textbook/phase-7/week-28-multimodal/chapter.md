# Chapter 28 — Multimodal AI as product I/O

> **Phase 7 — Supplementary Electives**  
> **Editorial status:** COMPLETE  
> **Source of truth:** `research/phase-7/week-28-multimodal/`  
> **Syllabus Build:** Add **one real multimodal capability** to an existing stack (Phase 2 RAG chatbot or Phase 3 agent). Keep it small: **one working end-to-end multimodal path** you can demo — not a full “multimodal platform.” Pick **one** of: (1) **Screenshot / error-image path** — upload → vision extract → RAG/tools reason → show image → fields → passages → answer trail; or (2) **Voice-input path** — audio → STT → same text agent/RAG → optional TTS. Document a short design note: modality contract (MIME/size/storage), context assembly (how media enters the Week 25 packer; what is *not* re-sent), and an eval slice of 5–10 golden multimodal cases.

---

## Prerequisites Recap

Before this week you should already have from Week 27 (Phase 7 elective — open-source and self-hosted models):

- **Open-source model landscape** — Llama / Qwen / Gemma shortlist with task eval + license.  
- **Quantization basics** — INT4 / AWQ / GPTQ / GGUF sizing so hardware quotes match reality.  
- **Local inference tooling** — Ollama for spike; graduate to vLLM (or NIM) when concurrency and SLOs matter.  
- **Self-hosted vs API + air-gap** — self-hosted as **one** Week 20 router leg; comparison memo (latency / quality / cost); weight import, offline eval, and `failover=none` when the customer cannot use a hosted API.

You do **not** need a screenshot → vision → RAG path, voice STT pipeline, or requirement-vs-gimmick design note yet as *finished* products — that is what this week ships. You **do** need Week 25’s context packer (images and transcripts are high-cost context), Week 5 prompt discipline around media, and an existing Phase 2 RAG or Phase 3 agent stack to attach **one** multimodal ingress. Week 27’s serving location and comparison memo stay available: air-gap STT via Whisper.cpp and on-prem VLMs are tool-mediated options when vendor vision is unavailable — but **where weights run** and **when non-text I/O is a real requirement** are separate levers.

---

## What this week builds

Week 27 shipped a **self-hosted router leg** and **comparison memo** (latency / quality / cost — not a vague “we support open source” checkbox). Week 28 continues **Phase 7 — Supplementary Electives** — these weeks do **not** replace Weeks 1–24. Suggested slot in research: alongside **Week 14** (prove range of system capabilities / I/O), or append after the Week 24 capstone; **this course appends them** after Week 24 / Week 25 / Week 26 / Week 27. It complements **Week 5** (how you instruct around media) and **Week 25** (images and transcripts are high-cost context).

Week 28 treats **multimodal AI** as product **I/O engineering**, not as “the model can see and hear so we should show that in a demo.” A modality is useful when the user’s ground truth lives outside plain text: a screenshot of a failing UI, a PDF page, a spoken request while driving, a product photo, a waveform of a support call.

Chip Huyen’s *Multimodality and Large Multimodal Models* frames the field: modalities (text, image, audio, video) can be converted or jointly embedded; many “multimodal” products are still **pipelines** (STT → LLM → TTS) rather than a single native model. Her *Agents* essay notes tools can **simulate** multimodality (captioner, OCR, Whisper) when the base model is text-only — an FDE-relevant path when vendor vision is unavailable or too expensive.

| Capability | Job | Typical APIs |
|------------|-----|--------------|
| **Image understanding** | Describe, OCR, classify, reason over pixels | Claude vision; OpenAI image input; Gemini vision |
| **Image generation** | Create / edit pixels from prompts | OpenAI Images / Responses image tool; Gemini image out |
| **STT** | Speech → text | Whisper API / Whisper.cpp; OpenAI transcriptions; Gemini audio |
| **TTS** | Text → speech | OpenAI speech; ElevenLabs |
| **Native multimodal chat** | Multiple content parts in one turn | Messages / Responses / Gemini `contents` with mixed parts |

This week answers four coupled questions that FDE reviews and interview deep-dives treat as the minimum bar once Week 25 packing and (optionally) a Week 27 local route already exist:

1. **Understand vs generate** — default ops/support to understanding; generation is a different surface.  
2. **STT / TTS pipelines** — Capture → STT → Reason → optional TTS with separate SLOs.  
3. **Mixed context** — content blocks in one conversation; extract → compact under Week 25 budget.  
4. **Requirement vs gimmick** — ablation + golden cases before roadmaping modalities.

**Do not** drop Week 27’s local route or comparison table — serving location stays; this week adds modality I/O. Do **not** drop Week 25’s packer — media taxes the same attention budget. Do **not** ship five half-wired modality demos or treat generation as proof of multimodality. Do **not** start Week 29 (adversarial / safety review) from this chapter — stay on one honest E2E multimodal path.

The **build** adds **one** real multimodal capability to an existing stack — screenshot/error-image **or** voice-input — plus a short design note (modality contract, Week 25 context assembly, 5–10 golden multimodal cases). Interview artifact = that **one E2E path** with traces and goldens, not an omni agent.

| This week | Not this week |
|-----------|----------------|
| One E2E multimodal path (screenshot **or** voice) | Full multimodal platform / five toggles |
| Understand-first; STT→text stack; content blocks | Generation as “we are multimodal” proof |
| Modality contract + Week 25 extract→compact | Drop Week 27 self-hosted router leg |
| Requirement vs gimmick rubric + kill criterion | Scheduled red-team / safety one-pager (Week 29) |

Read the concepts in order. Each section’s **Worked Example** and **Apply It** assume the same flagship service (working title: Deployment Copilot) gaining **one** honest multimodal ingress on top of the existing RAG / agent stack — after Week 27’s serving comparison is already written.

**Default path (synthesis):**

1. Decide **understand vs generate** per surface; default to understanding for ops/support.  
2. If voice: treat STT/TTS as **pipelines with SLOs**, not “add a mic button.”  
3. Mix modalities in **one conversation** with explicit content blocks and a Week 25 budget.  
4. Apply the **requirement vs gimmick** rubric before roadmaping.  
5. Ship the **single E2E path** + golden cases; cross-check Week 14 “prove range” without inventing a second product.  
6. Keep Week 27’s local/air-gap options available for Whisper.cpp or on-prem VLM legs when vendor APIs are off-limits — without conflating serving choice with modality choice.

---

### Image understanding vs generation

* **Fundamentals:**  
  **Image understanding** (vision) takes pixels as *input* and returns language or structured fields: captions, OCR, UI element descriptions, defect labels, “what changed between these two screenshots.” **Image generation** takes language (and sometimes reference images) as *input* and returns *new* pixels: product mockups, illustrations, edited variants.

  Chip Huyen (*Multimodality and LMMs*): image is a versatile modality — text, tables, and even audio (mel spectrograms) can be rendered as images — but **understanding** and **generation** sit on different training and product surfaces. Agents can also *fake* vision via tools (OCR, captioners) when the planner calls them (*Agents*, 2025).

  | Question | Prefer understanding | Prefer generation |
  |----------|----------------------|-------------------|
  | Does the user’s truth already exist as pixels? | **Yes** — screenshot, photo, scan | No — they want something that does not exist yet |
  | Is the output audited against source evidence? | Yes — diagnose from the image | Rarely — creative / marketing |
  | Failure mode | Misread text / hallucinated objects | Brand-unsafe / wrong layout / IP risk |
  | Cost driver | Input image tokens (resolution, detail) | Output image compute / retries |

  Vendor shapes (from legal docs cited in research):

  - **Anthropic Vision** — `image` content blocks (base64, URL, `file_id`); token estimate ≈ `(width × height) / 750`; resize guidance.  
  - **OpenAI** — image *inputs* via Responses / Chat; image *outputs* via Images API or Responses image-generation tool.  
  - **Gemini** — multimodal `contents` / Files API for vision understanding; separate image-generation modalities when enabled.  
  - **Hugging Face VLMs** (e.g. Qwen2-VL via Inference Providers) — common for cost control or on-prem; still **understanding** unless you wire a separate diffusion stack.

  Syllabus rule of thumb for FDEs: **default to understanding** for ops, support, compliance, and RAG-over-screenshots; add generation only when the user job is *create or edit media*.

* **The Alternatives:**  

  | Approach | Upside | Downside |
  |----------|--------|----------|
  | Native vision LLM | Joint reasoning with text in one call | Token cost; vendor pixel limits; harder eval |
  | OCR → text LLM | Cheap, auditable text | Loses layout/icons/color cues |
  | Captioner → text LLM | Simple tool composition (Huyen) | Caption may drop the error string that mattered |
  | Classic CV classifiers | Stable for fixed defect classes | Brittle to new UI themes |
  | Generation + human edit | Fast creative drafts | Not a substitute for reading customer images |
  | “Vision” that only generates | Pretty demos | Fails Week 14 honesty test |

  | Detail / resolution | When it wins |
  |---------------------|--------------|
  | Low / downscaled | Routing, “is this a receipt?”, coarse UI type |
  | High / full detail | Tiny stack-trace fonts, tables, dense IDE screenshots |
  | Always max detail | Burns budget; Week 25 context rot accelerates |

  Inside generation: Images API (single shot) vs Responses tool (multi-turn edit in conversation). Prefer the former for batch creative; the latter when the agent must decide generate-vs-edit mid-dialog (OpenAI image-generation guide). The syllabus selects **understanding-first** for the Deployment Copilot support/ops surface.

* **Failure Modes:**  
  - Roadmaps fund DALL·E-style features while support still cannot paste a **red error dialog**.  
  - Security reviews treat all “images” the same — missing that **user-upload understanding** is an injection and PII surface (screenshots of customer PII), while **generation** is a brand/IP surface.  
  - Eval suites score caption BLEU while the real KPI is “extracted error code matches ground truth.”  
  - Cost attribution is wrong: generation retries look like “multimodal spend” when understanding at `detail: high` was the actual line item.  
  - Wrong owners: creative designers own “vision” while platform eng owns none of the screenshot path.  
  - One “Add image” button that captions or generates with the same prompt template; no resize; re-send full PNG every turn.

* **Average vs. Strong Engineer:**  
  **Average:** one “Add image” that either captions or generates; no resize; no structured extraction; generation sold as proof of “we are multimodal.”  
  **Strong:** product PRDs label surfaces **Understand** vs **Generate**; preprocess (max dimension, JPEG quality, strip EXIF); structured extraction schemas for screenshots; store `file_id` / URI and reference instead of rebasing64; separate allowlists for user uploads vs model outputs; can walk OpenAI’s Image Understanding with RAG cookbook end-to-end; quote Anthropic token formula; explain when OCR pipeline beats native vision; refuse generation as proof of multimodality.

* **Worked Example:**  
  Deployment Copilot support tickets often include a screenshot of a red error banner or stack-trace UI. Following the OpenAI Image Understanding with RAG cookbook pattern: vision interprets the image; file search / RAG grounds analysis in runbooks — not caption-only. The product surface is labeled **Understand**. You extract structured fields (error code, service name, UI region), then retrieve docs. Generation is *not* on this path: pixels are *evidence*, not the *deliverable*. Contrast: a marketing mockup flow would use the Images API / Responses image tool where new pixels are the output.

* **Apply It:**  
  1. Label every image surface in the PRD **Understand** or **Generate**; default ops/support to Understand.  
  2. Add preprocess: max dimension, JPEG quality, strip EXIF before vision.  
  3. Define a structured extraction schema for screenshots (error code, service, banner text).  
  4. Prefer `file_id` / URI storage over rebasing64 on every turn.  
  5. Separate eval KPI: extraction accuracy vs caption BLEU; kill generation from the “multimodal proof” narrative.  
  6. Document when OCR → text LLM beats native vision for dense UI screenshots.

---

### Audio processing pipeline (STT, TTS)

* **Fundamentals:**  
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

  Syllabus voice-input build = prove steps 1–3 end-to-end; TTS is optional sugar with its own latency and brand constraints. Hugging Face Whisper (`openai/whisper-large-v3`) and Whisper.cpp are the common open/local legs; ElevenLabs is the frequent branded-voice TTS choice beside OpenAI speech.

* **The Alternatives:**  

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

  The syllabus selects **pipeline literacy** for the voice build: prove Capture → STT → Reason; optional TTS behind preference.

* **Failure Modes:**  
  - “Voice feature” launches with **no transcript store** — support cannot dispute what was said; Week 16 observability is blind.  
  - p95 latency is blamed on the LLM while **STT upload + TTS synthesis** dominate.  
  - PII in audio is retained forever because eng only redacted **text** logs.  
  - Whisper.cpp is proposed for “privacy” without a model-update and eval story.  
  - Teams confuse **translation** endpoints with transcription and silently English-force users (OpenAI translations vs transcriptions).  
  - Block on full Whisper → full LLM → full TTS; no streaming; no language hint; replay last TTS on every page refresh.  
  - TTS that reads secrets or raw tool JSON aloud.

* **Average vs. Strong Engineer:**  
  **Average:** mic button; block on Whisper; full TTS every reply; no language hint; no WER set; audio PII ignored.  
  **Strong:** enforce MIME/size limits; pass `language` / `languages` when known; stream STT and TTS where APIs allow; treat transcript as the **canonical message** in the conversation store; optional TTS behind user preference; measure STT WER on a domain clip set (product names, SKUs); diagram five stages with owners; cite OpenAI STT/TTS and Whisper.cpp for offline; know Gemini’s ~32 tokens/sec audio heuristic; refuse shipping TTS that speaks secrets.

* **Worked Example:**  
  Deployment Copilot adds a **voice-input path**: support engineer uploads a short WAV of a spoken incident report. Audio hits OpenAI `/v1/audio/transcriptions` (`gpt-transcribe` recommended, or `whisper-1` when timestamps matter). The transcript becomes the canonical user message in the conversation store and enters the same RAG/agent path as typed text. Optional TTS (OpenAI speech or ElevenLabs) plays the assistant reply only when the user toggles voice-out. For an air-gapped lab tenant, the same contract runs on Whisper.cpp with ggml models — transcript-in / agent / optional-TTS-out, different trust boundary. Latency budgets list STT and TTS as separate SLO stages, not “the LLM was slow.”

* **Apply It:**  
  1. Diagram Capture → STT → Reason → TTS → Log/redact with an owner per stage.  
  2. Enforce MIME types, size limits, and language hints on ingress.  
  3. Persist the transcript as the canonical message; apply retention to raw audio separately.  
  4. Measure STT WER on a domain clip set (product names, SKUs, error codes).  
  5. Put TTS behind a user preference; never speak secrets or raw tool JSON.  
  6. For air-gap: document Whisper.cpp model-update and eval story before promising privacy.

---

### Multimodal input in a single conversation

* **Fundamentals:**  
  A **single conversation** is multimodal when one turn (or the thread) mixes content types the model consumes jointly: e.g. a PNG screenshot **and** “why is checkout failing for order 1842?” in the same user message. Vendors expose this as **content parts / blocks**, not as two unrelated API calls you mentally concatenate.

  | Vendor pattern | Shape |
  |----------------|-------|
  | Anthropic Messages | `content: [{type: image, source…}, {type: text, text…}]` |
  | OpenAI Responses | `input_text` + `input_image` (URL / data URL / file id) |
  | Gemini | interleaved `contents` parts; Files API for large media |

  This is **Week 25 context engineering** with heavier tokens: images burn input budget by resolution; audio (if inlined) burns by duration (Gemini documents ~32 tokens per second of audio). Mixing modalities without a packer means **context rot** arrives sooner.

  Chip Huyen (*Building a Generative AI Platform*; *Agents*): context construction must gather whatever the model needs — including tools that fetch or transform media. Multimodal chat is the case where the “retrieved” evidence is often **user-supplied pixels** sitting beside RAG passages.

  Design rules of thumb:

  1. Put the **instruction text** that binds the image (“Extract the red error string; then search runbooks”) in the same turn as the image.  
  2. Prefer **file ids / URIs** over rebasing64 every follow-up (Anthropic Files API; OpenAI files; Gemini Files).  
  3. After extraction, consider **promoting structured fields to text** and dropping raw pixels from later turns (compaction).  
  4. Never assume the model “remembers” an image that you omitted from the serialized history.

* **The Alternatives:**  

  | Strategy | Upside | Downside |
  |----------|--------|----------|
  | Every turn resends full image | Model always “sees” it | Cost explosion; hits multi-image limits |
  | **Extract once → text thereafter** | Cheap follow-ups; searchable | Extraction errors freeze into the thread |
  | Caption-only then RAG | Simple | Loses fine UI detail |
  | Separate vision call, then text agent | Clear module boundary | Two models; sync bugs; double latency |
  | Collage multiple screenshots | One image slot | Unreadable text; weird aspect ratios |
  | Parallel tools (OCR + vision) | Redundancy | Clash / contradiction (Week 25 clash mode) |

  | Ordering | Note |
  |----------|------|
  | Image then text | Gemini docs often recommend image-first for single-image prompts |
  | Text then image | Fine for “here is policy; apply to image below” |
  | Interleaved many pairs | Needed for document + figure walkthroughs; watch per-request image caps |

  Tradeoff with Week 5 prompting: few-shot **multimodal** exemplars are expensive; prefer one canonical example or tool schemas over five huge screenshots in the system preamble. The syllabus selects **content-block-first messages + extract-then-compact** for the screenshot path.

* **Failure Modes:**  
  - Follow-up “what about the second error?” fails because the image was stripped from history serialization.  
  - Token dashboards spike after a single support session with three 4K Retina captures at `detail: high`.  
  - Indirect **prompt injection** via screenshot text (meme overlays, malicious OCR) bypasses text-only filters (pair with Week 5 / Willison-class thinking).  
  - Multi-agent handoffs pass text summaries that **drop** visual constraints (“approve only if the red banner says X”).  
  - Eval harnesses score the text reply while ignoring whether the model used the image at all.  
  - Chat UI shows a thumbnail; backend only stores the URL in a side channel the model never sees on turn 2.  
  - Skipping joint-context design makes Week 14 “we support images” a UI lie.

* **Average vs. Strong Engineer:**  
  **Average:** attachment thumbnail in UI; model sees the image only on turn 1; rebases64 every follow-up; no `vision_tokens` vs `text_tokens` split.  
  **Strong:** content-block first-class in the message schema; trace `vision_tokens` vs `text_tokens`; compact by replacing images with extraction JSON after N turns or on threshold; enforce max images per request (Anthropic many-image limits; OpenAI payload caps); can redraw a turn as Anthropic/OpenAI/Gemini blocks; link to Week 25 compaction for media; show a failure where omitting the image changed the answer.

* **Worked Example:**  
  Deployment Copilot support bot: user message is Anthropic-style blocks — `image` (screenshot `file_id`) + `text` (“Extract the red error string; then search runbooks for order checkout failures”). Vision extracts `{error_code, service, banner_text}`. The Week 25 packer keeps the image on turn 1; on later turns it promotes the extraction JSON to text and drops raw pixels (compaction), so “what about the second error?” still has searchable fields without re-sending a 4K PNG. Traces show `vision_tokens` vs `text_tokens`. OpenAI path mirrors the cookbook: image parts plus retrieved text evidence in one reasoning loop (Responses multimodal + tools when web_search or file search joins the same call).

* **Apply It:**  
  1. Make content blocks first-class in the message schema (image + text in one turn).  
  2. Bind the image with instruction text in the same message (“extract X; then search Y”).  
  3. Store `file_id` / URI; do not rebase64 every follow-up.  
  4. Compact: after extraction, promote structured fields to text; drop or thumbnail raw pixels under a token threshold.  
  5. Trace `vision_tokens` vs `text_tokens`; enforce max images / resolution per request.  
  6. Add an ablation eval: same question with and without the image — does the answer change?

---

### Genuine requirement vs demo gimmick

* **Fundamentals:**  
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

* **The Alternatives:**  

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

  Accessibility features can look like “gimmicks” in a sales demo but are **requirements** under policy — classify by user exclusion, not by wow factor. The syllabus selects **one E2E path** gated by the rubric, not an omni agent in week one.

* **Failure Modes:**  
  - Roadmaps fill with modality theater while the text RAG still hallucinates (Week 9).  
  - Security scope expands (biometrics-adjacent voice, face images) without legal review.  
  - On-call pages on Whisper outages for a feature nobody uses in production traffic.  
  - Week 14 portfolio claims “multimodal” and diligence finds only a playground GIF.  
  - Context costs (Week 25) blow up from vanity image turns with zero retrieval gain.  
  - Launch blog with generated images + voiceover; production traffic 99% text; no ablation study.  
  - Vanity metrics (“% sessions with an image attached”) untied to task success.

* **Average vs. Strong Engineer:**  
  **Average:** five modality toggles for the keynote; no ablation; generation splash as “multimodal”; vanity attach-rate metrics.  
  **Strong:** PRD checkbox “modality justifies itself under ablation”; shadow-mode vision on support tickets measuring deflection; voice limited to locales with STT WER gates; generation behind a creative workflow with human brand review; bring the rubric to the customer workshop; propose screenshot-error **or** voice-input — not both in week one; cite Huyen’s industry examples (health, retail, accessibility) as positive cases; cite OpenAI image-understanding RAG cookbook as the pattern for genuine support multimodal; refuse vanity attach-rate metrics unless tied to task success.

* **Worked Example:**  
  Stakeholder asks Deployment Copilot to “add voice and DALL·E for the demo.” You run the rubric: the artifact that exists *before* the app is a **screenshot of a failing deploy UI**; users lose fidelity when forced to retype error codes; text-only baseline misses the banner; you already have a corpus of support screenshots. Kill criterion: if vision extract accuracy < 90% on 20 goldens, ship OCR-assisted text upload instead. You refuse generation and dual voice+vision in week one. Ship the screenshot → extract → RAG path with 5–10 golden cases (screenshot + expected diagnosis). Voice is deferred until STT WER gates exist for the locales you support. Week 14 “prove range” shows this one path with traces — not five half-wired buttons.

* **Apply It:**  
  1. Fill the five-question rubric in the Week 28 design note before writing code.  
  2. Pick **one** E2E path (screenshot-error **or** voice-input); refuse omni in week one.  
  3. Write 5–10 golden multimodal cases with pass/fail and an named owner.  
  4. Define a kill criterion (e.g. extract accuracy threshold → OCR fallback).  
  5. Run an ablation: task success with modality removed — if unchanged, do not ship.  
  6. Classify accessibility asks by user exclusion, not wow factor; refuse vanity attach-rate KPIs.

---

## Week 28 build checklist (end-to-end)

Use this as the chapter’s capstone sequence; every concept above maps here.

1. **Understand vs generate:** Label the chosen surface Understand (default for ops/support); do not ship generation as multimodal proof.  
2. **Pick one path:** Screenshot/error-image **or** voice-input — not both in the first ship.  
3. **Modality contract:** Accepted MIME types, size/resolution limits, what is stored vs discarded.  
4. **Pipeline or blocks:** Voice → name STT (and optional TTS) stages with SLOs; images → content-block message schema.  
5. **Context assembly:** How image/audio tokens or transcripts enter the Week 25 packer; what is *not* re-sent every turn (extract → compact).  
6. **Eval slice:** 5–10 golden multimodal cases (screenshot + expected diagnosis, or audio + expected transcript intent) with pass/fail.  
7. **Rubric + kill criterion:** Requirement vs gimmick answers in the design note; abort path if goldens fail the threshold.

When those steps are true, Week 28 is done in the syllabus sense: one honest E2E multimodal path with contracts, token math, and goldens — not five half-wired modality demos.

---

## Looking ahead

Week 29 continues **Phase 7 — Supplementary Electives** with **AI safety, ethics, and adversarial testing**. After this week’s one E2E multimodal path (modality contract, Week 25 context assembly, 5–10 golden multimodal cases — not five half-wired demos), the next elective turns safety from a feature claim into a **discipline**: scheduled red-team / adversarial runs, bias and fairness slices, content moderation architecture, PII and tool-exfil controls beyond prompt injection, and a one-page safety review that survives fintech/healthcare-style questionnaires. The build is (1) a **formal adversarial test suite** with CI nightly / weekly deep cadence and explicit pass/fail per category, and (2) a **Safety & Responsible AI** one-pager (scope, data classes, threat model, controls, residual risk, escalation owners, evidence links). Do **not** start Week 29 by dropping this week’s multimodal path or goldens — screenshots and audio expand the attack and PII surface the suite must cover. Week 27’s self-hosted route and Week 25’s packer stay available; the deep work shifts from “when is non-text I/O real?” to “who owns the red-team schedule, and where is residual risk written down?”

---

## Compilation notes

- All concept sections above are grounded in `research/phase-7/week-28-multimodal/` (`00`–`04` + README; `99` for source index).  
- No section required `[NEEDS MORE RESEARCH]` for the four syllabus concepts covered in research files `01`–`04`.  
- Research **Open Questions** (native audio retiring pipelines; vision faithfulness eval without human raters; OCR vs VLM for dense UI; generated assets in RAG indexes; GDPR raw audio vs transcripts; ablation ownership; accessibility pricing; C2PA/provenance; omni contractual staging) remain open in the corpus and are **not** answered here.  
- Outside URLs from research are not required reading to understand this chapter; operational detail was inlined from the notes.  
- Elective placement and “does not replace Weeks 1–24” follow research `00` / README.  
- Build is one E2E multimodal path + design note only (not a full multimodal platform), per syllabus.  
- Editorial pass: Prerequisites Recap bridges Week 27 (OSS/self-hosted — Llama/Qwen/Gemma, quantization, Ollama/vLLM, air-gap; Week 20 router leg + comparison memo); Looking ahead bridges Week 29 (AI safety / adversarial testing — red-team schedule, bias, moderation, PII/exfil, safety review one-pager); Phase 7 framed as supplementary electives; no new technical claims beyond research.  
- Week 29 safety / adversarial depth is explicitly deferred — ship the one multimodal path here; scheduled red-team and the safety one-pager come next.
