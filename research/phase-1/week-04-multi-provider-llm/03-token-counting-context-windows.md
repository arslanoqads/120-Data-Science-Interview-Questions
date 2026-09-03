# 03 — Token counting and context window management

> Week 4 concept research (deep). Legal sources only.

---

## Fundamentals

Models consume **tokens**, not characters. Context windows are hard caps on (input + output) tokens; exceeding them fails the request or truncates. Pricing and rate limits are also token-based. Accurate **pre-flight counting** is required for budgeting, truncation, and `max_tokens` / `max_completion_tokens` planning.

### OpenAI / tiktoken
OpenAI’s open-source **tiktoken** mirrors BPE used by GPT models. Use `tiktoken.encoding_for_model(name)`:

| Encoding | Typical models |
|----------|----------------|
| `o200k_base` | gpt-4o / gpt-4o-mini family |
| `cl100k_base` | gpt-4, gpt-3.5-turbo, text-embedding-3-* |
| `p50k_base` / `r50k_base` | Legacy Codex / GPT-3 |

Raw `len(encode(text))` **undercounts** chat calls: message framing adds overhead (`tokens_per_message`, name tokens, priming tokens). The OpenAI Cookbook’s `num_tokens_from_messages` estimates Chat Completions usage; tool definitions add further overhead (`num_tokens_for_tools`). Cookbook notes counts are **estimates** and may drift by snapshot—verify against live `usage.prompt_tokens` when calibrating.

### Anthropic token counting
Prefer the official `POST /v1/messages/count_tokens` endpoint with the same payload shape as Messages (system, tools, images, PDFs, thinking config). Returns `input_tokens` without running inference; separate rate limits; generally free of message-creation charges. Tokenizer differs by model family—**re-count when migrating**. Claude 4.7+ / newer families: Anthropic documents ~**30% more tokens** for the same text vs earlier tokenizers on some workloads. Tool use adds system-side tokens for tool instructions; server tool counts apply specially on first sampling call.

### Context management strategies (combined in production)
1. **Priority ordering** — system/policy first; then high-value reference; then history; then current user turn.  
2. **Sliding window** — keep last N turns or last K tokens of dialogue.  
3. **Summarization / compaction** — compress older turns into a summary (trades fidelity for space; can bust prompt caches).  
4. **Truncation** — hard drop from the middle or oldest non-critical content as backstop.  
5. **Retrieval** — keep a thin prompt; pull docs on demand outside the permanent window (agent tools).

Reserve output budget:

```text
available_output ≈ context_limit − input_tokens − safety_margin
```

Set `max_tokens` / `max_completion_tokens` from that remainder—not a fixed 4096 on every call.

### Long-context tradeoffs
Huge windows (100K–1M+) reduce engineering pressure but raise cost, latency, and **lost-in-the-middle** risk. Retrieval + small window often beats stuffing a 200K context on both quality and cost for RAG. Multimodal tokens (images, PDFs, audio) dominate budgets—always count with provider-native tools, not character heuristics.

---

## Alternatives & Tradeoffs

| Method | Accuracy | Offline? | Notes |
| --- | --- | --- | --- |
| Character/word heuristics | Poor | Yes | Overflows easily |
| tiktoken local | High for OpenAI text | Yes | Chat/tool overhead still estimated |
| Anthropic `count_tokens` | Highest for Claude payloads | Network | Includes tools/images/PDFs |
| Post-hoc `usage` from response | Exact billed | After call | Too late to prevent overflow |
| Aggressive summarization | Saves tokens | — | Loses detail; cache invalidation |
| Huge context models only | Simple | — | Cost/latency; lost-in-the-middle |

---

## Necessity

Without counting: surprise 400s, truncated answers, runaway cost, and broken agent loops when tool transcripts grow unbounded. Multi-turn agents and RAG pipelines are especially sensitive.

Failure modes if skipped:

1. Agent succeeds for 8 turns then dies when tool JSON history exceeds the window.  
2. `max_tokens` set too high → provider rejects or silently truncates mid-JSON (breaks structured outs).  
3. Switching Claude generations without recount → ~30% budget error.  
4. Image/PDF turns counted as “one message” → massive undercount.  
5. Summarization that rewrites the prompt prefix → destroys cache hit rates (concept 04) while “saving” tokens.

---

## Industry Practice

### Common (weak)
- Trust UI “context %” or `len(prompt)//4`.  
- Never reserve output budget; structured JSON truncates at the closing brace.  
- Drop system instructions first when over budget.

### Strong / senior
- Pre-flight count every request that can approach the window; fail soft with “context too large” UX.  
- Allocate budgets explicitly (e.g. system 10–20%, tools+schema fixed, retrieved docs capped, history residual, output reserved).  
- Prefer **drop or summarize tool results** before dropping system instructions.  
- Monitor p95 prompt tokens and cache hit rates together.  
- When switching models, re-benchmark token counts.  
- Keep a provider-agnostic `count_tokens(request) -> int` on the LLM port (OpenAI: tiktoken + overhead tables; Anthropic: `count_tokens` API).

### RAG chatbot application
Cap retrieved chunk tokens separately from chat history. Prefer tool-based retrieval over stuffing top-k forever. Log `prompt_tokens`, `completion_tokens`, and (when present) cache fields on every span.

---

## Concrete Scenario

OpenAI Cookbook “How to count tokens with Tiktoken” verifies `num_tokens_from_messages` against live `usage.prompt_tokens` for chat messages (and a second recipe for tools). Anthropic’s token-counting guide shows `count_tokens` with system + messages (+ tools/images) returning `input_tokens` before `messages.create`. A chat backend can: count → if over budget, summarize oldest turns → recount → stream completion with `max_tokens = window − input − margin`.

URL: https://developers.openai.com/cookbook/examples/how_to_count_tokens_with_tiktoken  
Companion: https://platform.claude.com/docs/en/build-with-claude/token-counting  
tiktoken: https://github.com/openai/tiktoken

---

## Open Questions

1. What is the durable public formula for Responses API / GPT-5-family message framing overhead?  
2. How should compaction APIs expose “cache-safe” summaries that preserve prefix hashes?  
3. Best practice for counting multimodal tokens across providers in one gateway?  
4. When does retrieval+small-window outperform stuffing a 200K context on quality and cost?  
5. Should soft limits (warn at 70%) and hard limits (reject at 95%) be product UX or infra only?

---

## Sources

- https://developers.openai.com/cookbook/examples/how_to_count_tokens_with_tiktoken  
- https://platform.claude.com/docs/en/build-with-claude/token-counting  
- https://docs.anthropic.com/en/docs/build-with-claude/token-counting  
- https://github.com/openai/tiktoken  
- https://developers.openai.com/api/docs/guides/function-calling (tools consume context)  
