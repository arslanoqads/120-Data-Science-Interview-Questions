# Week 3 — Git Workflows, Containers, System Design Vocabulary
> Phase 0 — Engineering Foundations
> Raw research notes (not textbook prose). Sources cited inline and in Sources sections.

## Concept: trunk-based development vs feature branches

### Fundamentals
**Trunk-based development (TBD):** developers integrate into a single shared branch (`main`/trunk) at high frequency—often daily—using very short-lived branches (hours/days) or direct commits with review. Long-lived feature branches are avoided; incomplete work hides behind feature flags or branch-by-abstraction. Contrasts with GitFlow-style long `develop`/`feature/*` branches that merge infrequently.

### Alternatives & Tradeoffs
| Style | Pros | Cons |
|-------|------|------|
| TBD + short PR branches | Early integration, fewer merge hells, CD-friendly | Needs fast tests, flags for unfinished work, discipline |
| Long feature branches | Isolation for large risky work | Merge conflicts, stale branches, delayed feedback |
| GitFlow | Clear release trains | Heavyweight; fights continuous delivery |

trunkbaseddevelopment.com documents styles: commit-to-trunk vs short-lived feature branches scaled with code review bots. Trade-offs hinge on team size, build speed, and commit rate.

### Necessity
Long-lived branches produce painful merges, “integration week,” and hidden breakage. CI that only runs on rare merges discovers conflicts late. Without TBD (or equivalent frequent integration), continuous delivery stalls.

### Industry Practice
**Common:** feature branches lasting weeks; occasional rebase chaos. **Strong:** small PRs merged in <1–2 days; trunk always releasable; feature flags; branch-by-abstraction for multi-day refactors (ThoughtWorks Go ORM migration example on trunkbaseddevelopment.com); CI required green before merge; prefer rebase/squash policies that keep trunk history legible.

### Concrete Scenario
trunkbaseddevelopment.com’s CI page ties TBD to continuous integration practice popularized by Fowler/ThoughtWorks (CruiseControl era) and notes Docker-sized prod-like build environments as enablers: https://trunkbaseddevelopment.com/continuous-integration/. Styles/trade-offs: https://trunkbaseddevelopment.com/styles/. Branch by abstraction narrative: https://trunkbaseddevelopment.com/branch-by-abstraction/.

### Open Questions
How TBD coexists with required GitHub CODEOWNERS reviews at large orgs. Monorepo TBD vs polyrepo. Are stacked PRs a healthy scaling pattern or feature-branch creep? Flag technical debt from permanent toggles.

### Sources
- https://trunkbaseddevelopment.com/
- https://trunkbaseddevelopment.com/continuous-integration/
- https://trunkbaseddevelopment.com/styles/
- https://trunkbaseddevelopment.com/branch-by-abstraction/
- https://trunkbaseddevelopment.com/committing-straight-to-the-trunk/

---

## Concept: semantic commits (Conventional Commits)

### Fundamentals
Conventional Commits is a lightweight spec for commit messages: `<type>[optional scope][!]: <description>` with optional body/footers. `feat` → SemVer MINOR, `fix` → PATCH, `BREAKING CHANGE` / `!` → MAJOR. Enables automated changelogs, semantic-release version bumps, and clearer history for humans and machines.

### Alternatives & Tradeoffs
- **Free-form commits**: fast locally; poor automation; noisy history.
- **Conventional Commits**: machine-readable; needs linting (`commitlint`) or squash-time editing so casual contributors aren’t blocked.
- **Angular-style types** (`build`, `ci`, `perf`, …): richer taxonomy; bikeshedding risk.
- **PR title conventions vs every commit**: squash workflows let maintainers enforce the spec at merge only (explicitly endorsed by the spec FAQ).

### Necessity
Without semantic structure, release tooling can’t infer version bumps; changelogs become manual archaeology; teammates can’t scan history for breaking API changes. Mistyped types (`feet` instead of `feat`) silently skip automation—spec warns of this failure mode.

### Industry Practice
**Common:** inconsistent messages; manual tags. **Strong:** Conventional Commits + `semantic-release` or similar; CI checks PR titles; `feat!`/`BREAKING CHANGE` reviewed carefully; scopes per package in monorepos; docs/test-only commits use `docs:`/`test:` to avoid spurious minors.

### Concrete Scenario
Official spec examples and SemVer mapping: https://www.conventionalcommits.org/en/v1.0.0/. FAQ notes squash-merge workflows where maintainers rewrite the final message—useful for open-source contribution UX. Many CD pipelines bump versions and build Docker tags from these commits.

### Open Questions
Should `refactor:` ever trigger releases? How to encode AI-generated change risk in commit metadata? Commit message LLM assistants vs intentional human typing. Revert semantics remain underspecified by design.

### Sources
- https://www.conventionalcommits.org/en/v1.0.0/
- https://semver.org/

---

## Concept: Docker fundamentals (multi-stage builds, image size optimization)

### Fundamentals
A Docker image is layered filesystem + metadata; a container is a running instance. A Dockerfile defines build steps. **Multi-stage builds** use multiple `FROM` lines: compile/install in a fat builder stage, then `COPY --from=build` only artifacts into a slim runtime stage—leaving compilers, caches, and source out of production. Smaller images pull faster and expose less attack surface.

### Alternatives & Tradeoffs
- **Single-stage fat image**: simple; huge CVE surface (toolchains in prod).
- **multi-stage + distroless/slim/alpine/scratch**: minimal runtime; debugging harder (no shell).
- **Alpine vs Debian slim**: Alpine’s musl can break manylinux wheels; Debian slim often safer for Python.
- **Pin by digest vs floating tags**: digests reproducible; tags drift under you.
- **BuildKit cache mounts**: faster rebuilds; need CI cache configuration.

### Necessity
Naive `FROM python:3.9` app images balloon to ~GB scale with hundreds of CVEs. Shipping build tools in prod increases post-compromise capability. Slow pulls delay deploys and autoscaling.

### Industry Practice
**Common:** single-stage Dockerfile copying the whole repo. **Strong:** multi-stage; `.dockerignore`; non-root `USER`; pin base digests; copy only needed paths (never `COPY --from=build /`); separate `--target` for test vs prod; scan images in CI (Trivy etc.). Docker docs show Go builder → `scratch` final binary as the canonical pattern.

### Concrete Scenario
Docker official multi-stage docs: builder compiles, final `FROM scratch` copies only `/bin/hello`—no SDK in the result: https://docs.docker.com/build/building/multi-stage/. Community DevSecOps demos report cutting a naive Python/Flask image from ~1.6 GB / 1200+ HIGH+CRITICAL findings toward ~100 MB distroless with far fewer CVEs via staged hardening: https://github.com/MetaMaaz/docker-security-pipeline.

### Open Questions
Distroless Python ergonomics vs operational need for `exec` debugging. Reproduceable SBOM requirements in enterprise FDEs. WASM/container alternatives for cold-start LLM sidecars.

### Sources
- https://docs.docker.com/build/building/multi-stage/
- https://docs.docker.com/build/building/best-practices/
- https://github.com/MetaMaaz/docker-security-pipeline
- https://docs.docker.com/engine/reference/builder/

---

## Concept: docker-compose for local dev

### Fundamentals
Docker Compose defines multi-container apps in YAML (`services`, `networks`, `volumes`). One command starts the stack—API + Postgres + Redis + vector DB—mirroring production topology on a laptop or in CI. Compose manages lifecycle: up/down, logs, one-off `compose run` commands.

### Alternatives & Tradeoffs
- **Compose vs local installs**: Compose onboards faster and matches prod deps; heavier resource use; Docker-required.
- **Compose vs full K8s (minikube/kind/skaffold)**: K8s fidelity higher; Compose far simpler for day-1 service wiring.
- **Compose for prod**: possible but controversial; many teams use Compose for dev/test and K8s/ECS for prod.
- **bind mounts vs image rebuilds**: mounts speed iteration; diverge from prod image path—test both.

### Necessity
Without Compose (or equivalent), engineers hand-run five services with drift (“forgot to migrate DB”), and bugs appear only in shared staging. Onboarding time explodes.

### Industry Practice
**Common:** a `docker-compose.yml` that’s stale vs prod. **Strong:** compose for local + CI integration tests; pinned images; healthchecks; separate `compose.override.yml` for dev mounts; secrets via env files not committed; document `compose up` as the golden path; keep parity for ports/protocols even if scale differs.

### Concrete Scenario
Docker Compose product docs: single YAML controls services/networks/volumes; one command creates and starts the stack; works across dev/test/CI: https://docs.docker.com/compose/. Typical FDE RAG stack: `api`, `postgres`, `redis`, `otel-collector` services with dependency `healthcheck` gates.

### Open Questions
Compose vs Dev Containers vs Tilt for inner loop. How much prod parity is enough before diminishing returns? Compose Watch vs native hot reload.

### Sources
- https://docs.docker.com/compose/
- https://docs.docker.com/compose/compose-file/
- https://docs.docker.com/compose/how-tos/startup-order/

---

## Concept: system design vocabulary — latency vs throughput, horizontal vs vertical scaling, load balancing, caching layers, CAP theorem (working level)

### Fundamentals
- **Latency**: time for one request (e.g., p50/p99). **Throughput**: work per unit time (QPS, tokens/sec). Optimizing one can hurt the other (batching raises throughput, adds latency).
- **Vertical scaling**: bigger machine. **Horizontal scaling**: more machines/replicas; needs statelessness or shared state design.
- **Load balancing**: distribute traffic across instances (DNS → VIP/L4 → L7). Google SRE: search cares about latency (nearest DC); uploads may prefer throughput paths.
- **Caching layers**: client, CDN, edge, app memory, Redis, DB buffer pools—each trades freshness for speed; distinguish **latency caches** (system survives cold) vs **capacity caches** (cold cache can’t hold load—SRE cascading-failure chapter).
- **CAP (working level)**: under network **P**artition, a system cannot simultaneously provide full **C**onsistency and **A**vailability. Useful as intuition; easy to misuse as “Mongo=AP” labels.

### Alternatives & Tradeoffs
- Scale up until cost/limits force scale out; horizontal needs load balancing + session/data strategy.
- Strong consistency (quorum/Paxos-style) increases delay sensitivity; eventual consistency lowers user-visible wait but complicates correctness.
- Cache-aside vs read-through vs write-through; TTLs vs explicit invalidation.
- Kleppmann argues CAP is too coarse—latency matters more than binary availability; prefers delay-sensitivity reasoning (arXiv:1509.05393).

### Necessity
Confusing latency with throughput leads to wrong SLOs (optimizing average QPS while p99 burns). Skipping load balancing creates single points of failure. Treating a capacity cache as optional causes outages on restart (thundering herds). Naïve “we’re CP” slogans hide real client-visible timeouts.

### Industry Practice
**Common:** one box + Redis “for speed”; no p99 tracking. **Strong:** SLIs for latency *and* availability; horizontal pods behind LB; cache layered with explicit cold-cache plan; load-test failover; discuss consistency per data type (billing vs recommendation); read SRE load-balancing and cascading-failure chapters before inventing new cache tiers.

### Concrete Scenario
Google SRE frontend load balancing: search routed for low RTT latency; video upload may take a different path to maximize throughput—same platform, different optimization targets: https://sre.google/sre-book/load-balancing-frontend/. Cascading failures chapter: empty caches making previously cheap requests expensive, and capacity vs latency caches: https://sre.google/sre-book/addressing-cascading-failures/. CAP at consensus systems: https://sre.google/sre-book/managing-critical-state/. Kleppmann’s critique—“please stop calling databases CP or AP”: https://martin.kleppmann.com/2015/05/11/please-stop-calling-databases-cp-or-ap.html and https://arxiv.org/abs/1509.05393.

### Open Questions
PACELC as teaching replacement for CAP? How LLM inference changes classic vocab (batching tokens, TTFT vs TPOT latency). Edge caching of personalized AI responses—privacy vs hit rate. When global consistency is worth cross-region RTT for agent memory stores.

### Sources
- https://sre.google/sre-book/load-balancing-frontend/
- https://sre.google/sre-book/load-balancing-datacenter/
- https://sre.google/sre-book/addressing-cascading-failures/
- https://sre.google/sre-book/managing-critical-state/
- https://martin.kleppmann.com/2015/05/11/please-stop-calling-databases-cp-or-ap.html
- https://arxiv.org/abs/1509.05393
- https://martin.kleppmann.com/2015/09/17/critique-of-the-cap-theorem.html
