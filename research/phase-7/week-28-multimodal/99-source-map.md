# 99 — Week 28 master source map

> Consolidated index of official docs, engineering blogs, model repos. Legal sources only.  
> Phase 7 elective — Multimodal AI.

Fetched / verified via WebSearch & WebFetch during corpus authoring (2026-09-03).

---

## OpenAI — vision, images, audio

| Topic | URL |
|-------|-----|
| Images / vision inputs guide | https://developers.openai.com/api/docs/guides/images |
| Image generation guide | https://developers.openai.com/api/docs/guides/image-generation |
| Speech to text (file transcription) | https://developers.openai.com/api/docs/guides/speech-to-text |
| Text to speech | https://developers.openai.com/api/docs/guides/text-to-speech |
| Image Understanding with RAG (cookbook) | https://developers.openai.com/cookbook/examples/multimodal/image_understanding_with_rag/ |
| GPT image generation prompting guide | https://developers.openai.com/cookbook/examples/multimodal/image-gen-models-prompting-guide |
| Responses API multimodal + tools example | https://developers.openai.com/cookbook/examples/responses_api/responses_example |
| Migrate to Responses (native multimodal note) | https://developers.openai.com/api/docs/guides/migrate-to-responses |

---

## Anthropic — Claude vision

| Topic | URL |
|-------|-----|
| **Vision** (image blocks, limits, token estimate) | https://platform.claude.com/docs/en/build-with-claude/vision |
| API usage primer (text + images) | https://platform.claude.com/docs/en/claude_api_primer |
| Prompt engineering overview (contrast / instructions) | https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview |

---

## Google Gemini — multimodal / audio / files

| Topic | URL |
|-------|-----|
| Image understanding | https://ai.google.dev/gemini-api/docs/image-understanding |
| Audio understanding | https://ai.google.dev/gemini-api/docs/audio |
| Files API / multimodal files | https://ai.google.dev/gemini-api/docs/interactions/files |
| Google Cloud multimodal AI overview | https://cloud.google.com/use-cases/multimodal-ai |

---

## Whisper / Whisper.cpp / Hugging Face

| Topic | URL |
|-------|-----|
| OpenAI Whisper (original repo) | https://github.com/openai/whisper |
| **whisper.cpp** (ggml-org) | https://github.com/ggml-org/whisper.cpp |
| whisper.cpp models README | https://github.com/ggml-org/whisper.cpp/blob/master/models/README.md |
| HF `openai/whisper-large-v3` | https://huggingface.co/openai/whisper-large-v3 |
| Transformers Whisper docs | https://huggingface.co/docs/transformers/model_doc/whisper |
| HF image-text-to-text / VLM task | https://huggingface.co/docs/transformers/tasks/image_text_to_text |
| HF Inference Providers Responses (multimodal example) | https://huggingface.co/docs/inference-providers/en/guides/responses-api |

---

## TTS — OpenAI & ElevenLabs

| Topic | URL |
|-------|-----|
| OpenAI text to speech | https://developers.openai.com/api/docs/guides/text-to-speech |
| ElevenLabs docs hub | https://elevenlabs.io/docs |
| ElevenLabs API reference (TTS) | https://elevenlabs.io/docs/api-reference/text-to-speech |

---

## Chip Huyen — public blogs

| Topic | URL |
|-------|-----|
| **Multimodality and Large Multimodal Models (LMMs)** | https://huyenchip.com/2023/10/10/multimodal.html |
| Open challenges — multimodality section | https://huyenchip.com/2023/08/16/llm-research-open-challenges.html |
| Agents (tools as modality bridges) | https://huyenchip.com/2025/01/07/agents.html |
| Building a Generative AI Platform (context construction) | https://huyenchip.com/2024/07/25/genai-platform.html |
| Building LLM applications for production | https://huyenchip.com/2023/04/11/llm-engineering.html |

---

## Cross-links inside this KB

| Related week | Why |
|--------------|-----|
| **Week 14** — prove range | Suggested slot; multimodal as honest I/O range, not slideware |
| **Week 5** — prompt engineering | Instructions that bind media; injection via image/OCR text |
| **Week 25** — context engineering | Image/audio tokens; compaction after extraction; isolation |
| Weeks 6–10 — RAG | Screenshot → extract → retrieve (cookbook pattern) |
| Weeks 11–15 — agents | Tool-mediated caption/OCR/STT vs native LMM |
| Week 16–17 — evals / observability | Trace vision_tokens; transcript logs; golden multimodal sets |
| Week 20 — cost/latency | STT+TTS hops; `detail` / resolution knobs |

---

## Source policy reminder

Allowed: official docs, reputable engineering blogs, open model repos, arXiv (when cited), public cookbooks.  
Not used: pirate book/PDF sites or unauthorized copyrighted book text.
