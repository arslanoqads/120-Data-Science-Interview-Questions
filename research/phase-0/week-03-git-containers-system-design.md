# Week 3 — Git discipline, containers, and system design literacy

> Phase 0 — Engineering Foundations  
> Raw research notes (not textbook prose). Legal sources only.

---

## Concept: Trunk-based development vs feature branches

### Fundamentals
**Trunk-based development (TBD)** means developers integrate small changes into a single mainline (`main`/`trunk`) at least daily, keeping branches short-lived. Long-lived **feature branches** / GitFlow isolate work for days–weeks, then merge with higher conflict risk. TBD pairs with CI that must stay green and with feature flags for incomplete work.

### Alternatives & Tradeoffs
| Model | Strength | Cost |
|-------|----------|------|
| TBD + short PRs | Fast feedback, less merge hell | Requires CI discipline, flags, small batches |
| GitFlow (develop/release/hotfix) | Clear release trains | Slow integration; “integration branch” debt |
| Long feature branches | Quiet parallel work | Painful merges; hidden breakage |
| Fork + PR (OSS) | Access control | Not the same as multi-week private branches |

Thoughtworks notes TBD works best with visible **deployment pipelines** (commit → stages → prod confidence) rather than environment branches.

### Necessity
Long AI-feature branches (RAG rewrite + agent rewrite together) produce unreviewable PRs and “works on my branch” eval baselines that cannot merge. FDE customer work needs frequent integration with their staging systems.

### Industry Practice
- **Common:** feature branches lasting 1–2 weeks; rare CI on main.
- **Senior:** PRs <1–2 days of work; main always deployable; feature flags for risky agent tools; release = promote artifact, not merge epic branch.

### Concrete Scenario
Thoughtworks: enabling TBD with deployment pipelines: https://www.thoughtworks.com/en-us/insights/blog/enabling-trunk-based-development-deployment-pipelines  
trunkbaseddevelopment.com patterns: https://trunkbaseddevelopment.com/

### Open Questions
- How do regulated enterprises reconcile TBD with mandatory long-lived release approval branches?
- AI-generated PRs: does TBD batch size need to shrink further for reviewability?

### Sources
- https://trunkbaseddevelopment.com/
- https://www.thoughtworks.com/en-us/insights/blog/enabling-trunk-based-development-deployment-pipelines
- https://martinfowler.com/bliki/FeatureBranch.html

---

## Concept: Semantic commits

### Fundamentals
**Conventional Commits** / semantic commits structure messages as `type(scope): summary` (e.g. `fix(retrieval): correct RRF weight`). Types (`feat`, `fix`, `docs`, `refactor`, `test`, `chore`) enable automated changelogs and semver bumps. They are a communication protocol for humans and release tooling—not magic.

### Alternatives & Tradeoffs
- **Conventional Commits**: machine-parseable; noisy if over-scoped.
- **Free-form prose**: expressive; weak automation.
- **Ticket-ID prefixes only** (`PROJ-123: …`): good traceability; weaker change taxonomy.
Tradeoff: enforce via commitlint vs social norms; squash-merge can destroy granular history (decide deliberately).

### Necessity
Without semantics, “update stuff” commits make Week 23 STAR stories and prompt changelogs hard to reconstruct. Interview narratives need commit archaeology of failures.

### Industry Practice
- **Common:** inconsistent messages; giant squash commits.
- **Senior:** conventional commits + PR templates; separate `feat(prompts)` from `feat(retrieval)`; link eval metric deltas in body; protect main with required checks.

### Concrete Scenario
Conventional Commits spec: https://www.conventionalcommits.org/en/v1.0.0/  
YouTube: GitHub Universe / conventional commits tooling talks — https://www.youtube.com/results?search_query=conventional+commits+github

### Open Questions
- Should prompt-template edits be `feat` or a dedicated `prompt` type for AI systems?
- AI commit-message generators: useful or a source of confident nonsense?

### Sources
- https://www.conventionalcommits.org/en/v1.0.0/
- https://semver.org/

---

## Concept: Docker fundamentals (multi-stage builds, image size optimization)

### Fundamentals
Docker packages app + runtime into an **image** run as a **container**. **Multi-stage builds** use multiple `FROM` stages: build/test in a fat stage, `COPY --from=builder` only artifacts into a slim runtime stage—smaller images, smaller attack surface (no compilers, fewer CVEs). Optimize further with `.dockerignore`, pinned base digests, non-root `USER`, and BuildKit cache mounts.

### Alternatives & Tradeoffs
- **Single-stage fat image**: simple; slow pulls, large CVE surface.
- **Multi-stage + slim/distroless**: production default; slightly harder debug (add debug stage/`--target`).
- **Buildpacks / Chainguard / unikernels**: less Dockerfile craft; less control.
Tradeoff: minimal images vs need for shell in incident response (distroless trade).

### Necessity
Syllabus Cloud Run path: oversized images slow cold starts/autoscaling pulls and ship unused build tools. Postmortems regularly cite GB-sized images delaying deploys.

### Industry Practice
- **Common:** `FROM python:3.12`, `pip install -r requirements.txt`, copy everything, run as root.
- **Senior:** builder stage with uv; runtime `python:slim` or distroless; `uv sync --frozen --no-dev`; non-root; healthcheck; SBOM/scan in CI; layer caching ordered for deps-first.

### Concrete Scenario
Docker official multi-stage docs: https://docs.docker.com/build/building/multi-stage/  
Get-started concept page: https://docs.docker.com/get-started/docker-concepts/building-images/multi-stage-builds/  
YouTube: Docker’s official channel multi-stage / Best Practices — https://www.youtube.com/results?search_query=docker+multi-stage+builds+official

### Open Questions
- Distroless vs wolfi/chainguard as default for Python LLM services with native wheels?
- How much image size still matters on Cloud Run vs Kubernetes node pull latency?

### Sources
- https://docs.docker.com/build/building/multi-stage/
- https://docs.docker.com/build/building/best-practices/
- https://docs.docker.com/get-started/

---

## Concept: docker-compose for local dev

### Fundamentals
**Compose** declares multi-container local stacks (API + Postgres/pgvector + Redis + observability) in YAML so `docker compose up` reproduces dependencies without cloud. It is a **dev/integration** tool—not a full production orchestrator (K8s/ECS/Cloud Run handle prod).

### Alternatives & Tradeoffs
- **Compose**: low friction local parity for DBs/vector stores.
- **Devcontainers**: editor-integrated; good onboarding.
- **Tilt/Skaffold + kind**: closer to K8s; heavier.
- **Cloud-only staging**: true parity; slow loop, cost.
Tradeoff: compose drift from prod manifests unless generated from same IaC mental model.

### Necessity
Without local dependencies, engineers mock away retrieval/DB bugs that only appear against real Postgres quirks—exactly the FDE “messy systems” gap.

### Industry Practice
- **Common:** one service Dockerfile only; “just use prod Redis.”
- **Senior:** compose profiles (`--profile obs`); named volumes; healthchecks; seed scripts for messy fixtures; document parity limits vs Cloud Run.

### Concrete Scenario
Compose specification / Docker docs: https://docs.docker.com/compose/  
YouTube: Docker Compose overview (Docker Official): https://www.youtube.com/results?search_query=docker+compose+official+tutorial

### Open Questions
- Compose vs Podman/Kubernetes local as the teaching default for FDE candidates?
- How to share compose “customer simulator” packs for enterprise SSO/DB fixtures?

### Sources
- https://docs.docker.com/compose/
- https://docs.docker.com/compose/compose-file/

---

## Concept: System design vocabulary (latency vs throughput, scaling, load balancing, caching, CAP)

### Fundamentals
Working vocabulary for interview and design docs:
- **Latency**: time per request (p50/p95/p99). **Throughput**: requests/work per unit time. Optimizing one can hurt the other (batching ↑ throughput, ↑ latency).
- **Vertical scaling**: bigger machine. **Horizontal scaling**: more replicas behind a **load balancer**.
- **Caching layers**: client → CDN/edge → app → Redis → DB; for LLM apps also **exact/semantic prompt caches** and provider prompt caches (Phase 1/5).
- **CAP**: under network **Partition**, a distributed datastore chooses **Consistency** vs **Availability** (partition tolerance is assumed). **PACELC** adds: else (no partition), trade latency vs consistency.

### Alternatives & Tradeoffs
| Choice | Example in RAG/agent systems |
|--------|------------------------------|
| Lower latency | Smaller top-k, skip rerank, cascade to small model |
| Higher quality / throughput batch | Larger context, cross-encoder, offline eval jobs |
| CP store | Strong consistency for ACL/entitlements |
| AP / eventual | Analytics caches, some vector index replicas |

### Necessity
Without this vocabulary, design docs cannot explain why hybrid search + rerank blows p95, or why multi-region RAG with residency constraints cannot be “just CA.” Interviewers probe these tradeoffs explicitly (syllabus Week 23).

### Industry Practice
- **Common:** “we’ll add Redis” without hit-rate/invalidation plan; CAP recited as “pick two of three” incorrectly.
- **Senior:** SLOs on p95 latency and cost/query; cache TTLs tied to corpus version; CAP/PACELC stated per *operation* (authZ check vs document popularity cache); load shedding when provider 429s.

### Concrete Scenario
Google SRE Book (free) — latency-related chapters / managing load: https://sre.google/sre-book/table-of-contents/  
Gilbert & Lynch CAP formalization (free ACM/HTML discussions widely cited); practitioner CAP/PACELC explainers: https://www.alekseialeinikov.com/en/blog/topics/architecture/cap-theorem-2026-what-it-really-means-for-choosing-a-database  
YouTube: infoQ/Strange Loop talks on CAP misconceptions — https://www.youtube.com/results?search_query=CAP+theorem+partition+InfoQ

### Open Questions
- Are vector DBs meaningfully CP or AP for ANN indexes, and how should RAG cite freshness guarantees?
- For LLM apps, is **cost** a first-class SLO alongside latency/availability (emerging “CAL” thinking)?

### Sources
- https://sre.google/sre-book/table-of-contents/
- https://docs.docker.com/get-started/
- https://trunkbaseddevelopment.com/
- Brewer CAP history / distributed systems primers (search ACM “Brewer’s conjecture”)
