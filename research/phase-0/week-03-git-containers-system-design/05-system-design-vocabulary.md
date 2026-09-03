# 05 — System design vocabulary (latency, scaling, caching, CAP/PACELC, LLM SLOs)

> Week 3 concept research (deep). Legal sources only.

---

## Fundamentals

### Why vocabulary is a Week 3 deliverable
The syllabus asks for a **living system design doc**. Without shared terms, the doc is boxes and arrows. Interviewers (Week 23) and FDE customers probe the same tradeoffs. This file is the glossary that doc must use.

### Latency vs throughput
- **Latency**: time per request (prefer **percentiles**: p50 / p95 / p99—not only averages). Google SRE: request latency is a core SLI for user-facing serving systems.  
- **Throughput**: work per unit time (QPS, tokens/sec, docs ingested/min).  
- Coupling: higher QPS often raises latency; services have **performance cliffs**. Batching can ↑ throughput and ↑ per-item latency simultaneously—state both.

LLM wrinkle: provider latency dominates; your p95 may be “model + retrieval + rerank,” not “FastAPI.” Measure **stages** (retrieve, rerank, generate) separately.

### Vertical vs horizontal scaling
- **Vertical**: bigger machine/CPU/RAM (or larger Cloud Run memory/CPU). Simple; ceilinged; bigger blast radius.  
- **Horizontal**: more replicas behind a **load balancer**. Needs statelessness (or sticky sessions / externalized state). Cloud Run / K8s scale horizontally with concurrency and instance counts.

### Load balancing
Google SRE Book chapters 19–20 (frontend LB, datacenter LB): distribute traffic across instances; health checking; avoid overload. In practice for Week 3:
- Cloud Run / GFE / cloud LB chooses instances.  
- App-level: timeout budgets, retries with jitter, **load shedding** when saturated or when provider returns 429.  
- Don’t retry storms amplify outages (SRE overload / cascading failure chapters).

### Caching layers
Typical web path: client → CDN/edge → app → Redis → DB.  
LLM / RAG additions:
- **Exact prompt / response cache** (identical inputs)  
- **Semantic cache** (near-duplicate embeddings)—Phase 5 depth  
- **Provider prompt caches** (Anthropic/OpenAI-style)—Phase 1  
- **Retrieval caches** keyed by corpus version + query hash  
- **Embedding caches** for repeated chunks  

Every cache needs: **hit-rate**, **TTL**, **invalidation** on corpus/prompt version bump, and a stated consistency story.

### CAP theorem (correct framing)
Informal “pick two of three” (Consistency, Availability, Partition tolerance) is **misleading**. Eric Brewer’s retrospective (*CAP Twelve Years Later*, InfoQ):

- Partitions are the rare case forcing C vs A.  
- Outside partitions you need not forfeit C or A.  
- Choices can be **per operation / per subsystem**, not a permanent database tattoo.  
- Properties are continuous, not binary.

Formal roots: Brewer conjecture (PODC 2000); Gilbert & Lynch proof (2002). CAP **consistency** ≈ linearizability (narrower than ACID “C”). CAP **availability** ≈ every non-failing node eventually responds (not the same as “five 9s marketing”).

Google Cloud Spanner write-up: real systems discuss realistic high availability and partition *mitigation*, not cartoon CA/CP stickers.

### PACELC (Abadi)
Daniel Abadi’s PACELC: **if** Partition → trade Availability vs Consistency; **else** → trade **Latency** vs Consistency. Captures the normal-operation cost of strong consistency (cross-replica coordination).

Examples (textbook classifications—verify per config):
- PA/EL: Dynamo-style / Cassandra-like defaults (favor A and L)  
- PC/EC: Spanner / many strongly consistent NewSQL (favor C, pay L and A under partition)  

For RAG: ACL/entitlement checks often need stronger C; document-popularity caches can be eventually consistent.

### SLIs, SLOs, SLAs (SRE Book Ch. 4)
- **SLI**: quantitative measure (latency, error rate, throughput, availability/yield).  
- **SLO**: target on an SLI (e.g., p95 latency < X).  
- **SLA**: contract with consequences if missed.  

SRE guidance: few representative indicators; user-facing systems care about availability, latency, throughput; publishing SLOs sets expectations. Chubby anecdote: meeting but not vastly exceeding SLO can flush unsafe dependencies.

### LLM-specific SLOs and cost
Emerging practice: treat **cost** (USD/query, tokens/query, GPU-sec) as a first-class objective alongside latency and availability—“CAL” thinking, not classical CAP. Also track:
- Groundedness / eval quality gates (not SRE classical, but product SLI)  
- Provider error/429 rate  
- Cold-start latency for serverless containers  

A design doc that only says “highly available RAG” without p95 and $/query is incomplete for FDE work.

---

## Alternatives & Tradeoffs

| Choice | Example in RAG/agent systems | Cost |
|--------|------------------------------|------|
| Lower latency | Smaller top-k; skip rerank; cascade to small model; tighter timeouts | Quality / recall risk |
| Higher quality | Larger context; cross-encoder; multi-hop agents | p95 and $ explode |
| Higher throughput batch | Offline eval / embed jobs | Worse interactive latency |
| Vertical scale | Bigger Cloud Run instance for peak | Cost floor; single-instance limits |
| Horizontal scale | More replicas | Need statelessness; connection pool multiplication |
| CP-leaning store | Strong consistency for ACL/entitlements | Latency; availability under partition |
| AP / eventual | Analytics caches; some vector replica lags | Stale retrieval / permission bugs if mis-applied |
| Aggressive caching | Prompt/retrieval caches | Stale answers after corpus update; privacy leakage if poorly keyed |

**Interview anti-pattern:** “We’ll add Redis” with no hit-rate, TTL, or invalidation plan.  
**CAP anti-pattern:** “Mongo is AP, Postgres is CA” as absolute identity.

---

## Necessity

### Failure modes if vocabulary is missing
1. Design docs cannot explain why hybrid search + rerank blows p95.  
2. Multi-region RAG with residency constraints sold as “just CA.”  
3. Autoscaling without concurrency/load-shedding plan → 429 storms + DB connection exhaustion.  
4. Cache without corpus versioning → “wrong answer from yesterday’s policy PDF.”  
5. Week 23 interviews: candidate draws boxes, cannot discuss percentiles, PACELC, or cost SLOs.

### Living system design doc (Week 3 artifact)
Minimum sections that use this vocabulary:
1. Goals / non-goals  
2. Request path + sequence (retrieve → rerank → generate)  
3. SLIs/SLOs (latency percentiles, availability, **$/query**)  
4. Scaling model (horizontal; concurrency assumptions)  
5. Caching layers + invalidation  
6. Data stores + CAP/PACELC **per operation**  
7. Failure modes (provider down, partition, overload)  
8. Open questions  

Keep it living: update when architecture changes land on trunk (TBD).

---

## Industry Practice

### Common (weak)
- Averages instead of percentiles.  
- CAP recited as pick-two menu.  
- “Redis cache” with no metrics.  
- No cost objective; surprised by bill after demo traffic.  
- Design doc written once for interview, never updated.

### Strong / senior
- SLOs on **p95 latency** and **cost/query**; error budget thinking from SRE.  
- Cache TTLs tied to **corpus version** / prompt version.  
- CAP/PACELC stated per *operation* (authZ check vs popularity cache vs ANN search freshness).  
- Load shedding / graceful degradation when provider 429s (smaller model; cached answer; “degraded” UX).  
- Explicit cold-start and concurrency assumptions for Cloud Run.  
- Vector DB freshness guarantees documented honestly (ANN ≠ linearizable read of source of truth).

### RAG design examples (tradeoff table for the living doc)

| Operation | Lean | Rationale |
|-----------|------|-----------|
| Entitlement check before retrieve | Stronger C | Wrong doc = compliance incident |
| Dense ANN query | Latency; approximate | Approximate neighbor OK; freshness SLO separate |
| Prompt response cache | EL (favor L) | Invalidate on prompt/corpus version |
| Billing token counters | Stronger C | Money |

---

## Concrete Scenario

**Google SRE Book (free) — ToC**  
https://sre.google/sre-book/table-of-contents/  

Especially: Ch. 4 Service Level Objectives; Ch. 19–21 load balancing / overload; monitoring chapters for SLI collection.

**SRE — Service Level Objectives**  
https://sre.google/sre-book/service-level-objectives/  

**Brewer — CAP Twelve Years Later (InfoQ)**  
https://www.infoq.com/articles/cap-twelve-years-later-how-the-rules-have-changed/  

**Abadi PACELC paper (PDF)**  
https://www.cs.umd.edu/~abadi/papers/abadi-pacelc.pdf  

**Gilbert & Lynch perspectives PDF**  
https://groups.csail.mit.edu/tds/papers/Gilbert/Brewer2.pdf  

**Google Cloud — Spanner and CAP**  
https://cloud.google.com/blog/products/databases/inside-cloud-spanner-and-the-cap-theorem  

**ScyllaDB PACELC glossary**  
https://www.scylladb.com/glossary/pacelc-theorem/  

**KubeCon NA 2021 — CAP / Raft intuition talk** (Betty Junod, Paul Burt)  
Sched: https://kccncna2021.sched.com/event/lV4H  
YouTube search: https://www.youtube.com/results?search_query=KubeCon+CAP+theorem+Raft+Junod+Burt  

**InfoQ / CAP misconceptions search seed**  
https://www.youtube.com/results?search_query=CAP+theorem+partition+InfoQ  

---

## Open Questions

- Are vector DBs meaningfully CP or AP for ANN indexes, and how should RAG cite freshness guarantees?  
- For LLM apps, is **cost** a first-class SLO alongside latency/availability (emerging “CAL” thinking)?  
- Should groundedness / eval pass-rate be an SLO owned by product vs platform SRE?  
- Multi-region RAG with data residency: how to explain PACELC when partition *and* legal constraints co-exist?

---

## Sources

- https://sre.google/sre-book/table-of-contents/  
- https://sre.google/sre-book/service-level-objectives/  
- https://www.infoq.com/articles/cap-twelve-years-later-how-the-rules-have-changed/  
- https://www.cs.umd.edu/~abadi/papers/abadi-pacelc.pdf  
- https://groups.csail.mit.edu/tds/papers/Gilbert/Brewer2.pdf  
- https://cloud.google.com/blog/products/databases/inside-cloud-spanner-and-the-cap-theorem  
- https://www.scylladb.com/glossary/pacelc-theorem/  
- https://kccncna2021.sched.com/event/lV4H  
- https://www.youtube.com/results?search_query=CAP+theorem+partition+InfoQ  
