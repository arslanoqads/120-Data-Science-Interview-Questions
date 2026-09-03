# 99 — Week 14 master source map

> Consolidated index of official docs, talks, YouTube. Legal sources only; no pirate book sites.

**Deep-pass date:** 2026-09-03. A2A spec URLs under `https://a2a-protocol.org/latest/...` track the **latest** release (1.0.0 at gather time). Pin `https://a2a-protocol.org/v1.0.0/specification/` when reproducing a lesson. Re-fetch before shipping.

---

## A2A protocol (primary)

| Topic | URL |
|-------|-----|
| Protocol home (MCP complementarity, “what A2A is not”, governance, video + course links) | https://a2a-protocol.org/latest/ |
| Key concepts (actors, Card, Task, Message, Part, Artifact, streaming, push) | https://a2a-protocol.org/latest/topics/key-concepts/ |
| A2A and MCP (auto repair shop; tools vs peer agents) | https://a2a-protocol.org/latest/topics/a2a-and-mcp/ |
| Agent discovery (`.well-known/agent-card.json`, registries, card security, caching) | https://a2a-protocol.org/latest/topics/agent-discovery/ |
| Specification (layers, operations, bindings; proto is normative) | https://a2a-protocol.org/latest/specification/ |
| Pinned 1.0.0 spec | https://a2a-protocol.org/v1.0.0/specification/ |
| Python tutorial — start server / well-known card routes | https://a2a-protocol.org/latest/tutorials/python/5-start-server/ |
| GitHub (protocol + SDKs) | https://github.com/a2aproject/A2A |
| Historical Google mirror | https://github.com/google/A2A |

---

## Google / Linux Foundation (announcement & ecosystem)

| Topic | URL |
|-------|-----|
| Announcing A2A (2025-04-09; complements MCP; 50+ partners) | https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/ |
| Vertex AI multi-system agents + A2A (Cloud blog) | https://cloud.google.com/blog/products/ai-machine-learning/build-and-manage-multi-system-agents-with-vertex-ai |
| Cross-language ADK + A2A (`RemoteA2aAgent`) | https://developers.googleblog.com/en/build-cross-language-multi-agent-team-with-google-agent-development-kit-and-a2a/ |
| Linux Foundation project launch (2025-06-23) | https://www.linuxfoundation.org/press/linux-foundation-launches-the-agent2agent-protocol-project-to-enable-secure-intelligent-communication-between-ai-agents |
| Community: Card / Task / push | https://discuss.google.dev/t/understanding-a2a-the-protocol-for-agent-collaboration/189103 |
| Community: Vertex eval + Cloud Run A2A agents | https://discuss.google.dev/t/end-to-end-evaluation-of-multi-agent-systems-on-vertex-ai-with-cloud-run-deployment-for-a2a-agents/250552 |
| Vertex agent evaluation service (trajectory metrics; Week 15 adjacent) | https://cloud.google.com/blog/products/ai-machine-learning/introducing-agent-evaluation-in-vertex-ai-gen-ai-evaluation-service |
| IBM BeeAI + A2A tutorial (ACP merge note) | https://www.ibm.com/think/tutorials/use-a2a-protocol-for-ai-agent-communication |
| DeepLearning.AI course intro | https://learn.deeplearning.ai/courses/a2a-the-agent2agent-protocol/lesson/vtf72ap4/introduction |
| Course short link | https://goo.gle/dlai-a2a |

---

## Anthropic — agents, support actions, eval vocabulary

| Topic | URL |
|-------|-----|
| Building effective agents (workflows vs agents; ACI; support refunds; pause at checkpoints; sandbox writes) | https://www.anthropic.com/engineering/building-effective-agents |
| Demystifying evals (transcript vs **outcome**; harness; τ²-bench mention) | https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents |

---

## Stripe — idempotency (industry template)

| Topic | URL |
|-------|-----|
| Idempotent requests (`Idempotency-Key`, 24h prune, param mismatch, POST-only, no PII in keys, 500 caching) | https://docs.stripe.com/api/idempotent_requests |

---

## LangGraph / LangChain — HITL harness (confirmation)

| Topic | URL |
|-------|-----|
| Interrupts (`interrupt`, `Command(resume=…)`, node replay, $500 transfer) | https://docs.langchain.com/oss/python/langgraph/interrupts |
| Persistence (checkpointer required for durable gate) | https://docs.langchain.com/oss/python/langgraph/persistence |
| HITL DX blog | https://www.langchain.com/blog/making-it-easier-to-build-human-in-the-loop-agents-with-interrupt |
| LangSmith trajectory evals (Week 15) | https://docs.langchain.com/langsmith/trajectory-evals |

---

## Outcome grading / support benchmarks

| Topic | URL |
|-------|-----|
| τ-bench (Sierra) — policy + DB state | https://github.com/sierra-research/tau-bench |
| Langfuse — production traces → datasets | https://langfuse.com/resources/engineering/ai-agent-evaluation |

---

## OpenTelemetry (audit-adjacent traces)

| Topic | URL |
|-------|-----|
| GenAI spans landing (moved; follow redirects) | https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-spans/ |
| GenAI semantic conventions repo | https://github.com/open-telemetry/semantic-conventions-genai |

---

## YouTube / conference

| Topic | URL |
|-------|-----|
| **Google** — Introduction to Agent2Agent (A2A) Protocol (~8 min; Card, JSON-RPC, MCP vs A2A) | https://www.youtube.com/watch?v=Fbr_Solax1w |
| **DeepLearning.AI / Google Cloud / IBM** — Use A2A to connect agents across frameworks (course trailer; healthcare multi-agent) | https://www.youtube.com/watch?v=4gYm0Rp7VHc |
| **Harrison Chase (LangChain)** — 3 ingredients; reversible actions + human inbox (cost if wrong) | https://www.youtube.com/watch?v=kTnfJszFxCg |
| Same talk, AI Engineer page | https://ai.engineer/talks/3-ingredients-for-building-reliable-enterprise-agents |
| AI Engineer channel | https://www.youtube.com/@aidotengineer |

---

## Mapping: concept file → sources

| File | Must-cite |
|------|-----------|
| 00 overview + side-effecting second system | A2A home + MCP page; Anthropic both essays; Stripe idempotency; LangGraph interrupts; Chase YouTube; DLAI/Google YouTube |
| 01 A2A delegation | Spec + key concepts + discovery + a2a-and-mcp; Google announce + LF press; GitHub; Fbr_Solax1w; 4gYm0Rp7VHc; DLAI course |
| 02 side-effecting design | Anthropic building-effective-agents + demystifying-evals; τ-bench; Stripe; Chase |
| 03 idempotency + gates + dry-run | Stripe idempotent requests; LangGraph interrupts + HITL blog; Anthropic pause/checkpoints; A2A async/HITL in spec |
| 04 audit logs | Stripe keys/PII; Anthropic transcript vs outcome; OTel GenAI; Langfuse; A2A taskId; LangGraph checkpointers (not a substitute) |

---

## Out of scope (do not pull into Week 14)

| Topic | Week |
|-------|------|
| Agent loop, pairing IDs, retries, stop reasons | 11 |
| MCP protocol, Desktop/Code attach | 12 |
| Graph API, checkpointers, `interrupt` **as the whole lesson** | 13 (reuse as harness only) |
| Trajectory metrics, judges, failure taxonomies | 15 |
| Idempotent **legacy** ETL / messy SQL at scale | 21 |

Week 14 **uses** Week 13 `interrupt` and Week 12 MCP; it does **not** re-teach them. A2A **implementation** and the **write envelope** are this week.

---

## Prior single-file week

Expanded from `phase-3/week-14-domain-agent-side-effects.md` (removed after this deep pass). Do not resurrect a thin single file for Week 14.
