# 01 — Image understanding vs generation (when to use which)

> Week 28 — Multimodal AI  
> Research notes (raw).

---

## Fundamentals

**Image understanding** (vision) takes pixels as *input* and returns language or structured fields: captions, OCR, UI element descriptions, defect labels, “what changed between these two screenshots.” **Image generation** takes language (and sometimes reference images) as *input* and returns *new* pixels: product mockups, illustrations, edited variants.

Chip Huyen (*Multimodality and LMMs*): image is a versatile modality — text, tables, and even audio (mel spectrograms) can be rendered as images — but **understanding** and **generation** sit on different training and product surfaces. Agents can also *fake* vision via tools (OCR, captioners) when the planner calls them (*Agents*, 2025).

| Question | Prefer understanding | Prefer generation |
|----------|----------------------|-------------------|
| Does the user’s truth already exist as pixels? | **Yes** — screenshot, photo, scan | No — they want something that does not exist yet |
| Is the output audited against source evidence? | Yes — diagnose from the image | Rarely — creative / marketing |
| Failure mode | Misread text / hallucinated objects | Brand-unsafe / wrong layout / IP risk |
| Cost driver | Input image tokens (resolution, detail) | Output image compute / retries |

Vendor shapes (legal docs):

- **Anthropic Vision** — `image` content blocks (base64, URL, `file_id`); token estimate ≈ `(width × height) / 750`; resize guidance.  
  https://platform.claude.com/docs/en/build-with-claude/vision  
- **OpenAI** — image *inputs* via Responses / Chat; image *outputs* via Images API or Responses image-generation tool.  
  https://developers.openai.com/api/docs/guides/images  
  https://developers.openai.com/api/docs/guides/image-generation  
- **Gemini** — multimodal `contents` / Files API for vision understanding; separate image-generation modalities when enabled.  
  https://ai.google.dev/gemini-api/docs/image-understanding  

Syllabus rule of thumb for FDEs: **default to understanding** for ops, support, compliance, and RAG-over-screenshots; add generation only when the user job is *create or edit media*.

---

## Alternatives & Tradeoffs

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

Tradeoff inside generation: Images API (single shot) vs Responses tool (multi-turn edit in conversation). Prefer the former for batch creative; the latter when the agent must decide generate-vs-edit mid-dialog (OpenAI image-generation guide).

---

## Necessity

If you blur understanding and generation:

- Roadmaps fund DALL·E-style features while support still cannot paste a **red error dialog**.  
- Security reviews treat all “images” the same — missing that **user-upload understanding** is an injection and PII surface (screenshots of customer PII), while **generation** is a brand/IP surface.  
- Eval suites score caption BLEU while the real KPI is “extracted error code matches ground truth.”  
- Cost attribution is wrong: generation retries look like “multimodal spend” when understanding at `detail: high` was the actual line item.

Skipping the distinction produces wrong owners: creative designers own “vision” while platform eng owns none of the screenshot path.

---

## Industry Practice

- **Common:** one “Add image” button that either captions or generates with the same prompt template; no resize; re-send full PNG every turn.  
- **Strong:** product PRDs label surfaces **Understand** vs **Generate**; preprocess (max dimension, JPEG quality, strip EXIF); structured extraction schemas for screenshots; store `file_id` / URI and reference instead of rebasing64; separate allowlists for user uploads vs model outputs.  
- **FDE / senior:** can walk OpenAI’s Image Understanding with RAG cookbook end-to-end; quote Anthropic token formula; explain when OCR pipeline beats native vision; refuse generation as proof of “we are multimodal.”

Hugging Face VLMs (e.g. Qwen2-VL via Inference Providers Responses) are common for cost control or on-prem: https://huggingface.co/docs/inference-providers — still **understanding** unless you wire a separate diffusion stack.

---

## Concrete Scenario

**OpenAI — Image Understanding with RAG (Cookbook)**  
https://developers.openai.com/cookbook/examples/multimodal/image_understanding_with_rag/

Customer feedback mixes photos and text. The notebook uses vision to interpret images, then **file search** to ground analysis in stored context — measuring whether image understanding changes outcomes versus text-only. That is the canonical **understanding** product pattern for this elective (and the screenshot-error build variant).

Contrast generation: OpenAI Image generation guide — https://developers.openai.com/api/docs/guides/image-generation — for create/edit flows where pixels are the *deliverable*, not the *evidence*.

---

## Open Questions

- Will OCR quality from VLMs fully retire dedicated OCR for UI screenshots in 1–2 model generations?  
- How should teams version **extraction schemas** for screenshots alongside Week 5 prompt versions?  
- Is watermarking / C2PA enough to separate generated assets from customer evidence in the same bucket?  
- Multi-image reasoning (before/after) — vendor limits vs stitching into one collage?  
- When does open VLM + self-host beat Claude/GPT vision on p95 cost for high-QPS moderation?

---

## Sources

- https://platform.claude.com/docs/en/build-with-claude/vision  
- https://developers.openai.com/api/docs/guides/images  
- https://developers.openai.com/api/docs/guides/image-generation  
- https://developers.openai.com/cookbook/examples/multimodal/image_understanding_with_rag/  
- https://developers.openai.com/cookbook/examples/multimodal/image-gen-models-prompting-guide  
- https://ai.google.dev/gemini-api/docs/image-understanding  
- https://huyenchip.com/2023/10/10/multimodal.html  
- https://huyenchip.com/2025/01/07/agents.html  
- https://huggingface.co/docs/transformers/tasks/image_text_to_text  
- ../week-25-context-engineering/01-context-vs-prompt-engineering.md  
