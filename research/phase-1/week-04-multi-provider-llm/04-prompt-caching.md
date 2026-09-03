# 04 — Prompt caching mechanics

> Week 4 concept research (deep). Legal sources only.

---

## Fundamentals

Prompt caching stores **KV / prefix computation** for a reusable prompt prefix so later requests with a **byte-identical prefix** avoid recomputing it—lowering input cost and TTFT. Caches are typically **organization-scoped**, machine-local, and TTL-bound. Matching is exact-prefix: any change at position N invalidates everything after N.

### What is cacheable (both providers, in spirit)
Stable system/developer instructions, tool definitions, structured-output schemas, static few-shot blocks, large reference documents, and prior conversation turns that remain unchanged. Dynamic timestamps, per-user PII at the front, reordered tools, reshuffled few-shots, and compaction that rewrites history are **not** cache-friendly.

### Anthropic
- Enable via top-level `cache_control: { type: "ephemeral" }` (**automatic** breakpoint on last cacheable block, advances as history grows) or per-block `cache_control` for **explicit** breakpoints.  
- Prompt order for prefixes: **`tools` → `system` → `messages`** up to and including the breakpoint.  
- Default TTL ~**5 minutes**, refreshed on use at no extra write cost; **1-hour** TTL available (`ttl: "1h"`) at higher write multipliers (~2× base input).  
- Usage fields: `cache_creation_input_tokens`, `cache_read_input_tokens`, regular `input_tokens`.  
- Economics (published): cache write ≈ **1.25×** base input (5-min TTL); cache read ≈ **0.1×** (some newer models advertise even lower, e.g. 0.025×). Break-even often ~2 reads for 5-min writes. Announced latency cuts up to ~85% and cost cuts up to ~90% on long reused prompts.  
- Minimum token thresholds are **model-dependent** (commonly 1,024–4,096; some newer families 512). Below minimum → silently no cache (both creation and read usage stay 0).  
- Explicit breakpoints: writes happen **only at** your breakpoint; reads look backward (Claude API lookback window ~20 blocks). Place breakpoint on the **last shared stable block**, not on a per-request timestamp/user message. Max ~4 breakpoints.  
- Automatic caching traps: if the last block changes every request, automatic mode writes useless unique prefixes—use explicit breakpoint on the static prefix instead.

### OpenAI
- Enabled by default for supported models; monitor via Prompt Caching Dashboard.  
- Cache stores **KV tensors**, not raw tokens. Full rendered context includes OpenAI-provided instructions, developer messages, tools, history, images/docs/audio where supported.  
- Minimum cacheable length: **1,024** tokens for GPT-5.6+, **2,048** for many earlier models (hidden platform system tokens do **not** count toward minimum). Older reporting often rounds `cached_tokens` down to multiples of **128**.  
- **GPT-5.6+:** optional **explicit** mode via `prompt_cache_options.mode` and per-block `prompt_cache_breakpoint`; writes **1.25×**, reads **0.1×**; TTL via `prompt_cache_options.ttl` (e.g. `30m`). Implicit mode places an end-of-latest-message breakpoint. Multiple explicit breakpoints (up to four writes) isolate stable vs volatile sections.  
- Earlier models: implicit only; often no separate write surcharge; `cached_tokens` in usage; retention `in_memory` (~5–10 min idle) or extended `24h` where supported.  
- Routing: caches live on machines; traffic >~**15 RPM** risks overflow. `prompt_cache_key` improves stickiness—keys influence routing, they do not pin or guarantee hits.

### Few-shot placement effects
Exact prefix matching means:

| Placement | Cache effect | Quality effect |
|-----------|--------------|----------------|
| Static few-shots early (after tools/system) | High shared hit rate | Stable style/examples |
| Dynamic per-request examples **after** breakpoint | Preserve hits on system+tools; pay for examples each time | Better task fit |
| Dynamic examples **before** breakpoint | Destroy shared cache for everyone | Quality may rise; cost spikes |

Week 5 deepens selection policy; Week 4 owns the **layout constraint**: never insert volatile examples into the shared prefix without accepting a cold cache.

### What’s NOT cache-friendly
Dynamic timestamps, per-user PII at the front of the prompt, reordered tools, reshuffled few-shots, compaction that rewrites history, changing `reasoning.effort` / structured schema / `parallel_tool_calls` / `tool_choice` settings that alter rendered instructions.

---

## Alternatives & Tradeoffs

| Strategy | When it wins | When it loses |
| --- | --- | --- |
| Automatic / implicit caching | Multi-turn chat; low ops burden | Uncontrolled writes of volatile tails (esp. if writes cost extra) |
| Explicit breakpoints | Stable prefix + volatile suffix; cost control | More instrumentation; easy to misplace breakpoints |
| No caching | Tiny prompts; highly unique inputs | Leaves money/latency on table for long shared prefixes |
| Prompt shortening instead | Below min cache size; rare reuse | May hurt quality more than caching would save |
| Extended TTL / 24h retention | Bursty traffic with long gaps | Higher write cost or retention policy constraints (ZDR) |

---

## Necessity

Long system prompts, RAG corpora in-context, tool catalogs, and multi-turn agents make uncached input the dominant bill. Caching is often the highest-ROI infra change after choosing the right model size—**if** prefixes are designed for stability.

Failure modes if skipped:

1. “Caching enabled” but breakpoint after unique user message → pay write premium every time, zero shared hits.  
2. One-character system-prompt deploy → org-wide cold start and cost spike.  
3. Per-tenant PII in system → no cross-tenant reuse; privacy OK but economics wrong for shared policy.  
4. Summarization rewriting early history every N turns → perpetual misses.  
5. Too many `prompt_cache_key` values → fragmented routing / overflow misses.

---

## Industry Practice

### Common (weak)
- Flip caching on; leave prompt order random.  
- Put `Date.now()` in the system prompt for “freshness.”  
- Never look at `cache_read_*` / `cached_tokens` in dashboards.

### Strong / senior
- Structure prompts **stable → semi-stable → dynamic** (system + tools + static few-shots + docs, then user-specific, then latest user turn).  
- Put cache breakpoints **after** the last stable block; never after a unique user message if writes are billed.  
- Monitor hit rate dashboards; alert on miss spikes after prompt deploys.  
- Use `prompt_cache_key` (OpenAI) per product surface carefully—too many keys fragment routing; too few cause overflow contention.  
- Coordinate prompt versioning with caching: treat system-prompt edits as intentional cold-cache events (document expected cost spike).  
- Few-shots: keep static and early for hits; dynamic selection after breakpoint when quality needs it (see Week 5).

### RAG chatbot application
Cache: system policy + tool schemas + static style examples. Do **not** cache per-query retrieved chunks in the shared prefix—fetch via tools or place after the breakpoint. Keep tenant IDs out of the shared prefix hash unless isolation is required.

---

## Concrete Scenario

Anthropic’s prompt-caching docs describe caching large system/context blocks: first request pays cache write; subsequent questions within TTL pay cache read (~10% input rate) with large latency drops. OpenAI’s prompt-caching guide emphasizes exact prefix match, 1024+/2048+ minima, preserving history, stable tools, and `prompt_cache_key` for routing—plus GPT-5.6 explicit breakpoints so volatile tool outputs don’t force expensive writes. Cookbook “Prompt Caching 201” walks operational patterns.

URL: https://platform.claude.com/docs/en/build-with-claude/prompt-caching  
Companions: https://developers.openai.com/api/docs/guides/prompt-caching · https://www.anthropic.com/news/prompt-caching · https://openai.com/index/api-prompt-caching/ · https://github.com/openai/openai-cookbook/blob/main/examples/Prompt_Caching_201.ipynb

---

## Open Questions

1. How should multi-tenant SaaS choose `prompt_cache_key` granularity without fragmenting hit rates?  
2. Best pattern for “keep-alive” refreshes vs paying longer TTL write premiums?  
3. Can explicit breakpoints fully isolate per-user RAG chunks without sacrificing shared system+tool cache?  
4. How do providers’ ZDR / data-residency policies interact with extended cache retention in regulated industries?  
5. Should CI fail a prompt PR if it changes bytes before the declared cache breakpoint without a version bump?

---

## Sources

- https://platform.claude.com/docs/en/build-with-claude/prompt-caching  
- https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching  
- https://www.anthropic.com/news/prompt-caching  
- https://developers.openai.com/api/docs/guides/prompt-caching  
- https://openai.com/index/api-prompt-caching/  
- https://github.com/openai/openai-cookbook/blob/main/examples/Prompt_Caching_201.ipynb  
- https://github.com/anthropics/skills/blob/main/skills/claude-api/shared/prompt-caching.md  
