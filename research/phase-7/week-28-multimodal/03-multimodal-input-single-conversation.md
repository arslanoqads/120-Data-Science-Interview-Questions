# 03 — Multimodal input in a single conversation (image + text context)

> Week 28 — Multimodal AI  
> Research notes (raw).

---

## Fundamentals

A **single conversation** is multimodal when one turn (or the thread) mixes content types the model consumes jointly: e.g. a PNG screenshot **and** “why is checkout failing for order 1842?” in the same user message. Vendors expose this as **content parts / blocks**, not as two unrelated API calls you mentally concatenate.

| Vendor pattern | Shape | Doc |
|----------------|-------|-----|
| Anthropic Messages | `content: [{type: image, source…}, {type: text, text…}]` | https://platform.claude.com/docs/en/build-with-claude/vision |
| OpenAI Responses | `input_text` + `input_image` (URL / data URL / file id) | https://developers.openai.com/api/docs/guides/images |
| Gemini | interleaved `contents` parts; Files API for large media | https://ai.google.dev/gemini-api/docs/image-understanding |

This is **Week 25 context engineering** with heavier tokens: images burn input budget by resolution; audio (if inlined) burns by duration (Gemini documents ~32 tokens per second of audio). Mixing modalities without a packer means **context rot** arrives sooner.

Chip Huyen (*Building a Generative AI Platform*; *Agents*): context construction must gather whatever the model needs — including tools that fetch or transform media. Multimodal chat is the case where the “retrieved” evidence is often **user-supplied pixels** sitting beside RAG passages.

Design rules of thumb:

1. Put the **instruction text** that binds the image (“Extract the red error string; then search runbooks”) in the same turn as the image.  
2. Prefer **file ids / URIs** over rebasing64 every follow-up (Anthropic Files API; OpenAI files; Gemini Files).  
3. After extraction, consider **promoting structured fields to text** and dropping raw pixels from later turns (compaction).  
4. Never assume the model “remembers” an image that you omitted from the serialized history.

---

## Alternatives & Tradeoffs

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

Tradeoff with Week 5 prompting: few-shot **multimodal** exemplars are expensive; prefer one canonical example or tool schemas over five huge screenshots in the system preamble.

---

## Necessity

If you treat multimodal chat as “just another attachment”:

- Follow-up “what about the second error?” fails because the image was stripped from history serialization.  
- Token dashboards spike after a single support session with three 4K Retina captures at `detail: high`.  
- Indirect **prompt injection** via screenshot text (meme overlays, malicious OCR) bypasses text-only filters (pair with Week 5 / Willison-class thinking).  
- Multi-agent handoffs pass text summaries that **drop** visual constraints (“approve only if the red banner says X”).  
- Eval harnesses score the text reply while ignoring whether the model used the image at all.

Skipping joint-context design makes Week 14 “we support images” a UI lie.

---

## Industry Practice

- **Common:** chat UI shows a thumbnail; backend only stores the URL in a side channel the model never sees on turn 2.  
- **Strong:** content-block first-class in the message schema; trace `vision_tokens` vs `text_tokens`; compact by replacing images with extraction JSON after N turns or on threshold; enforce max images per request (Anthropic many-image limits; OpenAI payload caps).  
- **FDE bar:** can redraw a turn as Anthropic/OpenAI/Gemini blocks; cite OpenAI multimodal Responses cookbook examples; link to Week 25 compaction for media; show a failure where omitting the image changed the answer.

OpenAI Responses multimodal + tools example (image + web_search in one call):  
https://developers.openai.com/cookbook/examples/responses_api/responses_example  

---

## Concrete Scenario

**Anthropic — Vision (Messages API, multiple content blocks)**  
https://platform.claude.com/docs/en/build-with-claude/vision  

Docs show user messages that combine `image` + `text` blocks, multiple images per request, and Files API `file_id` reuse — the production pattern for “screenshot + question” support bots. Token/cost section forces FDEs to budget pixels the same way Week 25 budgets history.

Paired OpenAI path: Image Understanding with RAG — https://developers.openai.com/cookbook/examples/multimodal/image_understanding_with_rag/ — image parts plus retrieved text evidence in one reasoning loop.

---

## Open Questions

- Should compaction **always** discard raw images after extraction, or keep a low-res thumbnail for audit?  
- How do we evaluate “did the model actually use the image?” without eye-tracking or forced ablation?  
- Cross-provider history portability when one vendor uses `file_id` and another needs re-upload?  
- Where do PDFs sit — document blocks vs rasterized page images (Claude/Gemini differ)?  
- Multi-user threads: whose images enter the shared Week 25 isolation boundary?

---

## Sources

- https://platform.claude.com/docs/en/build-with-claude/vision  
- https://developers.openai.com/api/docs/guides/images  
- https://developers.openai.com/cookbook/examples/multimodal/image_understanding_with_rag/  
- https://developers.openai.com/cookbook/examples/responses_api/responses_example  
- https://ai.google.dev/gemini-api/docs/image-understanding  
- https://ai.google.dev/gemini-api/docs/interactions/files  
- https://huyenchip.com/2024/07/25/genai-platform.html  
- https://huyenchip.com/2025/01/07/agents.html  
- ../week-25-context-engineering/02-context-sources-and-layers.md  
- ../week-25-context-engineering/04-context-compaction.md  
