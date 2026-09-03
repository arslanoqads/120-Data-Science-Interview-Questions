# Chapter 3 — Git Discipline, Containers, and System Design Literacy

> **Phase 0 — Engineering Foundations**  
> **Editorial status:** COMPLETE  
> **Source of truth:** `research/phase-0/week-03-git-containers-system-design/`  
> **Syllabus Build:** Containerize the FastAPI service with a multi-stage Dockerfile; stand up a compose local stack; write a one-page living system design doc for the chatbot architecture (interview artifact).

---

## Prerequisites Recap

Before this week you should already have from Week 2:

- A **FastAPI** HTTP service for the flagship package (working title: **Deployment Copilot**) with resourceful REST under a versioned path.  
- A documented **OpenAPI** schema (`/docs`, truthful `response_model`s) treated as a contract artifact.  
- **Async** routes that await I/O-bound LLM calls (shared client, no blocking SDK work on the event loop).  
- A **pytest** suite that **mocks** the model provider (`LLMClient` Protocol / fakes / dependency overrides) so CI stays green without live API keys.

You do **not** need trunk-based Git discipline, multi-stage Docker, compose stacks, or system-design SLOs yet. That is what this week teaches.

---

## What this week builds

Week 2 left you with an HTTP FastAPI service, OpenAPI docs, async LLM I/O, and secret-free mocked tests. Week 3 makes that service **shippable and discussable**. Hiring screens for AI Engineer and Forward Deployed Engineer roles ask how incomplete agent tools land on main without breaking prod, why the image is ~180MB instead of 1.4GB, what compose does *not* prove about Cloud Run concurrency, and what your p95 SLO is when the LLM provider is the bottleneck.

The five ideas below are one delivery loop:

- **Trunk-based development** keeps `main` green and reviewable with short PRs and feature flags.  
- **Semantic commits** make history machine-readable for changelogs and interview archaeology.  
- **Multi-stage Docker** produces a promotable artifact sized for cold starts.  
- **Compose** reproduces Postgres/pgvector quirks locally without burning cloud budget.  
- **System design vocabulary** turns a one-page doc into something interviewers and customers can probe.

Skip any one and the rest collapses: a beautiful compose stack with week-long feature branches still produces unmergeable agent rewrites; a tiny image with no latency/throughput/SLO language still fails the “why is p95 8s?” question. Read the concepts in order. Each section’s **Worked Example** and **Apply It** assume the same flagship service (working title: **Deployment Copilot**) being containerized and explained for the first time—OpenAPI, async LLM port, and mocked tests stay; you package and explain them.

---

### Trunk-based development vs feature branches

* **Fundamentals:**  
  **Trunk-based development (TBD)** is a source-control branching model where developers collaborate on a single long-lived branch called the **trunk** (`main` in modern Git naming) and resist pressure to create other **long-lived** development branches. The canonical one-line summary from trunkbaseddevelopment.com: developers collaborate on code in a single branch called ’trunk’ and resist any pressure to create other long-lived development branches by employing documented techniques—so they avoid merge hell, do not break the build, and keep shipping.

  Core rhythm: integrate **small** changes into trunk **at least daily** (often multiple times per day); keep the trunk **green** / always releasable; prefer **short-lived** feature branches (hours to ~1–2 days) for review and CI, or (on very small teams) commit direct to trunk; land incomplete user-visible work behind **feature flags** / toggles, not behind long branches; use **branch by abstraction** and similar techniques for longer structural work—not weeks of isolation.

  TBD is a key enabler of **Continuous Integration** and, by extension, Continuous Delivery. Martin Fowler treats TBD and “true CI” (everyone integrates to mainline at least daily) as essentially synonymous; the “Trunk-Based Development” label resists semantic diffusion where “CI” meant “Jenkins on our feature branches.”

  What TBD is *not*: not “no branches ever”—short-lived branches plus PRs are normal at scale; not “no release branches”—just-in-time release branches cut from trunk (then deleted) are compatible, or you release from trunk with fix-forward; not the opposite of code review—pre-integrate review on short PRs is fine; multi-week isolation is the anti-pattern.

  **Feature branch** (Fowler): open a branch when starting a feature; do all work there; integrate when *done*. Other developers do not see your changes until then. Short-lived (1–2 days) feature branches approximate CI; week/month branches defer integration risk and discourage refactoring.

  **GitFlow** (popularized by Vincent Driessen): multiple long-running branches (`develop`, `release/*`, `hotfix/*`, `main`). Clear release-train narrative on paper; high integration friction; environment/branch sprawl.

  **GitHub Flow** is closer to TBD (short-lived branches, PR to main); trunkbaseddevelopment.com notes people practicing GitHub Flow will feel “quite similar, with a small difference around where to release from.”

  Thoughtworks argues TBD works best when delivery is modeled as a **deployment pipeline**: commit → stages → increasing confidence toward production—not a branch per environment. Each passing stage raises confidence in that revision; failure stops the pipeline (fix forward or revert). Manual gates (QA promote to staging) can still exist as *pipeline stages*, eliminating the need for environment branches. Pull requests plus integration pipelines remain valid when access control requires them—used *with* TBD, not as multi-week private isolation.

  **Feature flags / toggles** (Fowler): **release toggles** allow incomplete codepaths to land on trunk and even ship to production as latent code. Flags **decouple deploy from release**—essential for TBD + Continuous Delivery. Categories include release, experiment, ops, and permission toggles; mismanaged flag debt is a real cost (cleanup, combinatorial testing).

* **The Alternatives:**  

  | Model | Strength | Cost | When |
  |-------|----------|------|------|
  | TBD + short PRs + flags | Fast feedback; less merge hell; always-deployable main | Requires CI discipline, small batches, flag hygiene | Default for product/FDE delivery teams |
  | GitFlow | Familiar release/hotfix vocabulary | Slow integration; “integration branch” debt; environment-branch temptation | Rare; regulated release trains sometimes *simulate* this with pipeline stages instead |
  | Long feature branches (weeks) | Quiet parallel work; big bang demos | Painful merges; hidden breakage; unreviewable PRs; eval baseline drift | Avoid for AI/RAG features |
  | Fork + PR (OSS) | Access control for untrusted contributors | Not the same as multi-week *internal* private branches | Open source; can still keep contributor PRs small |
  | Scaled TBD (merge queues) | Serializes integration under high commit rate | Queue latency; tooling cost | Large monorepos (Google-scale patterns) |

  DORA / delivery research (cited via Fowler’s branching patterns): very short branch lifetimes (<1 day) and daily merges to trunk correlate with higher performance continuous delivery. Tradeoff: TBD without solid tests/CI is just shared breakage; feature flags without lifecycle management become permanent conditional debt.

  The syllabus selects **TBD + short PRs + multi-stage + compose** as the default. For regulated enterprises that mandate long-lived release *approval* branches, the Thoughtworks-style answer is: keep **development** trunk-based; express approvals as **pipeline stages / artifact promotion**, not as parallel development lines.

* **Failure Modes:**  
  - Unreviewable “epic” PRs: RAG rewrite + agent rewrite + prompt overhaul in one branch; reviewers cannot reason about eval deltas.  
  - “Works on my branch” eval baselines: golden sets and metric numbers that cannot merge cleanly to main.  
  - Customer staging drift: FDE work needs frequent integration with the customer’s staging systems; week-long isolation means painful reconciliation against their main.  
  - Refactor fear: long branches discourage shared cleanup (embedding schema, chunk metadata); codebase health decays.  
  - False CI: green builds on feature branches that never co-exist until the final merge war.  
  - Environment branches (`dev`, `staging`, `prod`) as long-lived lines of code instead of pipeline stages.

* **Average vs. Strong Engineer:**  
  **Average:** feature branches lasting 1–2 weeks (or more); rare CI on `main`; “CI” only on PR branches; incomplete agent tools gated by “don’t merge yet” instead of flags; environment branches as long-lived code lines.  
  **Strong:** PRs represent **<1–2 days** of work; main always deployable; feature flags for risky agent tools, new retrieval paths, and prompt experiments; release = **promote immutable artifact** through pipeline stages, not merge an epic branch; short-lived branches for code review + build checking; artifact creation from trunk commits; branch-by-abstraction for large renames (for example swapping vector store clients); visible pipeline (Thoughtworks): commit → test → staging → prod confidence. At FDE / platform bar: can explain TBD vs GitFlow with Thoughtworks / trunkbaseddevelopment.com language; feature flags for incomplete agent tools.

* **Worked Example:**  
  While shipping Deployment Copilot’s hybrid retrieval, you do **not** open `feature/agent-v2-complete-rewrite` for three weeks. Instead you land:

  ```text
  feat(retrieval): add hybrid RRF behind flag
  ```

  The RRF path ships with `hybrid_rrf_enabled` defaulted off. Prompt and eval harness changes merge daily so baselines stay comparable. Incomplete agent tools land behind release toggles so main stays deployable. A large vector-store client swap uses branch-by-abstraction: introduce the new port, dual-write or dual-read behind a flag, then remove the old path—never a three-week private branch. Customer staging receives trunk commits through a deployment pipeline (test → staging → prod confidence), not an environment branch merge.

* **Apply It:**  
  1. Adopt short-lived branches (hours to ~1–2 days) that PR into `main`; ban week-long feature isolation for RAG/agent work.  
  2. Keep `main` always deployable; require CI green before merge.  
  3. Put incomplete agent tools, new retrieval paths, and prompt experiments behind feature flags (release toggles).  
  4. Model delivery as a deployment pipeline (commit → stages → production), not a branch per environment.  
  5. Prefer branch-by-abstraction for structural renames; keep prompt/eval harness changes merging daily.  
  6. Document flag lifecycle (owner, cleanup date) so toggles do not become permanent debt.

---

### Semantic commits (Conventional Commits)

* **Fundamentals:**  
  **Conventional Commits** (spec v1.0.0) is a lightweight convention on top of commit messages that adds human- and machine-readable meaning. Structure:

  ```text
  <type>[optional scope]: <description>

  [optional body]

  [optional footer(s)]
  ```

  SemVer mapping from the spec: `fix` → **PATCH**; `feat` → **MINOR**; `BREAKING CHANGE` footer or `!` after type/scope → **MAJOR** (any type can be breaking). Other types (`build`, `chore`, `ci`, `docs`, `style`, `refactor`, `perf`, `test`, …) are allowed (Angular / `@commitlint/config-conventional` conventions) and have **no implicit SemVer effect** unless they include a breaking change.

  Example with scope (AI service shaped):

  ```text
  feat(retrieval): add RRF fusion for hybrid search

  Wire BM25 + dense scores through Reciprocal Rank Fusion.
  Behind flag `hybrid_rrf_enabled` (default off).

  Eval: nDCG@10 +0.04 on golden_v3
  ```

  Breaking change forms:

  ```text
  feat(api)!: rename /query to /v2/retrieve

  BREAKING CHANGE: clients must call /v2/retrieve; /query removed.
  ```

  Per the spec, benefits include: automatically generating **CHANGELOGs**; automatically determining **semantic version** bumps; communicating change nature to teammates/stakeholders; triggering build/publish processes; making structured history easier to explore. It is a **communication protocol** for humans and release tooling—not magic quality.

  **Semantic Versioning** (semver.org): `MAJOR.MINOR.PATCH`. Public API breakage → major; backward-compatible feature → minor; backward-compatible bugfix → patch. Conventional Commits dovetail by encoding intent in the commit stream so tools (`semantic-release`, `release-please`, `conventional-changelog`) can automate bumps and notes.

  Changelog automation: tools parse commits since the last tag, group by type, emit `CHANGELOG.md` / GitHub Release notes. Workflow choices: **every commit conventional** + merge commits kept, or **squash-merge** with a single conventional subject written at merge time (spec FAQ: lead maintainers can clean up for casual committers). Decide deliberately—squash destroys granular archaeology unless PR bodies preserve it.

  Spec guidance worth internalizing: prefer **multiple commits** when a change spans types (don’t stuff `feat`+`fix`+`docs` into one); proceed as if already released even in 0.x—someone is consuming the software; reverts use `revert` type + `Refs:` footers (tooling authors define SemVer impact).

* **The Alternatives:**  

  | Approach | Strengths | Weaknesses | When |
  |----------|-----------|------------|------|
  | Conventional Commits + commitlint | Machine-parseable; changelog/semver automation | Noisy if over-scoped; learning curve; bikeshedding types | Libraries, services with releases, interview portfolios |
  | Free-form prose | Expressive; low friction | Weak automation; inconsistent archaeology | Tiny personal scripts |
  | Ticket-ID prefixes only (`PROJ-123: …`) | Traceability to tracker | Weak change taxonomy; poor changelog grouping | Enterprise ticket culture—often *combine* with conventional (`fix(auth): … Refs: PROJ-123`) |
  | PR-title-as-squash-message | One clean history line per PR | Loses intra-PR commits; needs discipline on PR title | Common GitHub team default compatible with Conventional Commits |
  | AI-generated commit messages | Speed | Confident nonsense; wrong type/scope; hallucinated “why” | Use as draft only; human owns SemVer intent |

  Enforcement tradeoff: commitlint + husky/lefthook vs social norms. Over-strict lint on WIP commits can annoy; many teams lint on PR title / squash message instead. Scope tradeoff: scopes like `retrieval`, `prompts`, `evals`, `api` make changelogs useful; inventing 40 scopes creates thrash.

  **AI / prompt commit-type debate:** should prompt-template edits be `feat(prompts): …` (user-visible behavior—often correct for product impact), `fix(prompts): …` (correcting regressions), a dedicated custom type `prompt:` (highlights prompt ops but **won’t** auto-bump SemVer unless configured), or `chore(prompts):` (understates user impact)? **Senior practice:** treat user-visible prompt/behavior changes as `feat`/`fix` with scope `prompts`; reserve custom types only if release tooling is taught to map them. Document the team rule in CONTRIBUTING so AI commit generators do not invent types.

* **Failure Modes:**  
  - “update stuff” history: cannot reconstruct which commit broke nDCG or raised cost/query.  
  - Week 23 STAR stories suffer: interview narratives need commit archaeology of failures and fixes.  
  - Prompt/changelog opacity: product asks “what changed in the assistant this week?” and the answer is a git blame scavenger hunt.  
  - Accidental major bumps or silent breaking OpenAPI changes without `!` / BREAKING CHANGE.  
  - Release tooling theater: `semantic-release` configured but commits are free-form → empty or wrong releases.  
  - Mixing unrelated prompt, retrieval, and infra changes in one commit.

* **Average vs. Strong Engineer:**  
  **Average:** inconsistent messages; giant squash commits titled “address comments”; no link between commits and eval metric deltas; mixing unrelated prompt, retrieval, and infra changes in one commit.  
  **Strong:** Conventional Commits + PR templates; separate `feat(prompts)` from `feat(retrieval)` from `chore(deps)`; link **eval metric deltas** and flag names in the body; protect main with required checks; optionally commitlint on PR title; `CHANGELOG.md` or GitHub Releases generated from commits; deliberate squash vs merge-commit policy documented in CONTRIBUTING.

* **Worked Example:**  
  While containerizing Deployment Copilot and landing retrieval/prompt work, good commits look like:

  ```text
  fix(retrieval): correct RRF weight for sparse channel
  feat(prompts): add citation instruction block to system template
  test(evals): add golden cases for empty-retrieval path
  chore(docker): shrink runtime stage to python:3.12-slim
  ```

  Bad:

  ```text
  updates
  WIP
  fix stuff
  AI: improved the system
  ```

  The RRF fix body links the eval delta (`Eval: nDCG@10 …`) and the flag name so a Week 23 STAR story can reconstruct “what broke quality, what we changed, how we measured.” Squash-merge policy is documented: PR titles must be conventional so the changelog stays machine-parseable even when intra-PR commits are collapsed.

* **Apply It:**  
  1. Adopt Conventional Commits for the flagship repo; document allowed types and scopes in CONTRIBUTING.  
  2. Prefer scopes such as `retrieval`, `prompts`, `evals`, `api`, `docker`—keep the set small.  
  3. Put eval metric deltas and feature-flag names in commit bodies when behavior changes.  
  4. Decide squash vs merge-commit policy deliberately; if squashing, require conventional PR titles.  
  5. Optionally enforce with commitlint on PR title; keep main protected by required checks.  
  6. Treat user-visible prompt edits as `feat(prompts)` / `fix(prompts)`; do not invent unconfigured custom types.

---

### Docker multi-stage builds (image size)

* **Fundamentals:**  
  Docker packages application + runtime into an **image** (immutable filesystem layers + metadata). A **container** is a running instance. Production deploys (Cloud Run, Kubernetes, ECS) pull images; image size and layer structure directly affect pull latency, cold start, and CVE surface.

  **Multi-stage builds** (official Docker docs): use multiple `FROM` statements in one Dockerfile. Each `FROM` starts a new stage (optionally `AS name`). Copy only needed artifacts with `COPY --from=stage` into a slim runtime stage—leaving compilers, SDKs, caches, and test tooling behind.

  Classic shape (Go example from Docker docs → same pattern for Python):

  ```dockerfile
  # syntax=docker/dockerfile:1
  FROM golang:1.26 AS build
  WORKDIR /src
  # ... build binary ...
  RUN go build -o /bin/hello ./main.go

  FROM scratch
  COPY --from=build /bin/hello /bin/hello
  CMD ["/bin/hello"]
  ```

  Named stages keep `COPY --from=` stable if stages reorder. `--target <stage>` stops at a stage (debug/test vs production). BuildKit only builds stages the target **depends on**; the legacy builder may build unused intermediate stages.

  Why size and attack surface matter: choose minimal trusted bases; use a fat builder image and a slimmer production image so final output lacks build tools. Smaller images → faster downloads/portability, fewer dependency CVEs. Rebuild often (`--pull`) because tags move under you as publishers patch.

  **BuildKit cache mounts:** `RUN --mount=type=cache,target=...` persists package-manager caches across builds without baking them into image layers—critical for CI speed when dependency layers invalidate.

  **`.dockerignore`:** excludes junk from the build context (`.git`, `.venv`, `tests`, local `.env`, notebooks, `node_modules`). Smaller context = faster uploads to the daemon and less accidental `COPY` of secrets/source you meant to leave out.

  **Non-root:** runtime stage should `USER` a non-root account. Running as root in production widens blast radius of RCE. Pair with read-only root filesystem where the platform allows.

  **Python / uv idiomatic pattern** (Astral uv Docker guide + community optimal Dockerfile patterns):

  ```dockerfile
  # syntax=docker/dockerfile:1
  FROM python:3.12-slim AS builder
  COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
  WORKDIR /app
  ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never

  COPY pyproject.toml uv.lock ./
  RUN --mount=type=cache,target=/root/.cache/uv \
      uv sync --frozen --no-install-project --no-dev

  COPY . .
  RUN --mount=type=cache,target=/root/.cache/uv \
      uv sync --frozen --no-dev

  FROM python:3.12-slim AS runtime
  WORKDIR /app
  RUN useradd -r -u 10001 appuser
  COPY --from=builder --chown=appuser:appuser /app /app
  ENV PATH="/app/.venv/bin:$PATH"
  USER appuser
  CMD ["python", "-m", "myapp"]
  ```

  Key ideas: lockfile-first layer so code edits don’t bust dependency install; `--frozen` / `--locked` for deterministic CI installs; `--no-dev` so pytest/ruff never ship; `UV_LINK_MODE=copy` with cache mounts (cross-filesystem hardlink warning); optional separate `debug` stage with a shell for incident response while prod stays slim/distroless.

  Syllabus path toward Cloud Run-style hosting: oversized images slow cold starts and ship unused build tools. Multi-stage is the standard fix (Docker 17.05+; BuildKit now default). DockerCon / Docker Official “Dockerfile Best Practices” (Tibor Vass, Sebastiaan van Stijn): **use multi-stage Dockerfiles and enable BuildKit**; parallelize independent stages; cache mounts matter.

* **The Alternatives:**  

  | Approach | Strengths | Weaknesses | When |
  |----------|-----------|------------|------|
  | Single-stage fat image | Simple Dockerfile | Slow pulls; large CVE surface; ships compilers | Throwaway demos only |
  | Multi-stage + slim | Production default; readable | Slightly harder debug | Syllabus / Cloud Run default |
  | Multi-stage + distroless / Chainguard / Wolfi | Minimal attack surface | No shell for `exec`; native wheel friction | Hardened prod once debug stage exists |
  | Buildpacks | Less Dockerfile craft | Less control; harder custom native deps | Teams standardizing on buildpacks |
  | Scratch / static binary | Tiny | Mostly Go/Rust; not typical CPython | Non-Python sidecars |

  Debug tradeoff: distroless prod + `docker build --target debug` (or ephemeral debug container) beats keeping bash in every prod image “just in case.” Cache tradeoff: cache mounts speed rebuilds; `--no-cache` for clean dependency refresh is occasional, not default. Pinning tradeoff: floating `python:3.12` vs digest-pinned bases—digests for prod reproducibility; rebuild cadence for patches.

  RAG service specifics from research: don’t bake large embedding model weights into the API image unless required—prefer volume/sidecar/model service; native wheels (tokenizers, numpy) may block pure distroless until glibc/musl needs are understood—**slim is a pragmatic Phase 0 default**; keep prompt templates as versioned files in the image *or* config service—but not untracked notebooks.

* **Failure Modes:**  
  - GB-sized images delay Cloud Run / Kubernetes node pulls; autoscaling feels “broken.”  
  - Build tools in prod (gcc, rustc for wheels, leftover `.git`) expand CVE scans and incident blast radius.  
  - Root runtime: container escape / misconfig impact worse.  
  - Context bloat: copying `.venv` and secrets because no `.dockerignore`.  
  - CI thrash: every code change reinstalls all deps (wrong layer order; no cache mount).  
  - Weak single-stage pattern: `FROM python:3.12` + `COPY . .` + `pip install -r requirements.txt` as root—includes tests/dev deps, no pin, no health semantics.

* **Average vs. Strong Engineer:**  
  **Average:** fat single-stage image; runs as root; no pin; no ignore file; includes tests/dev deps; no health semantics.  
  **Strong:** `# syntax=docker/dockerfile:1`; builder stage with uv; runtime `python:*-slim` or distroless; `uv sync --frozen --no-dev`; deps-first layer ordering; BuildKit cache mounts for `/root/.cache/uv`; non-root `USER`; optional read-only root; `.dockerignore` audited; SBOM + image scan in CI (Trivy/Grype class tools); `--target` for test/lint stages that never ship; base images rebuilt on a schedule with `--pull`; healthcheck at orchestrator/compose layer (and/or `HEALTHCHECK` in image). FDE / platform bar: image size tied to cold-start budget.

* **Worked Example:**  
  You replace Deployment Copilot’s fat Dockerfile with the multi-stage uv pattern above. The builder stage installs from `uv.lock` with `--frozen --no-dev`; the runtime stage copies only `/app` (including the venv) onto `python:3.12-slim`, runs as `appuser` (uid 10001), and starts the FastAPI process via the venv `PATH`. `.dockerignore` excludes `.git`, `.venv`, notebooks, local `.env`, and tests from the build context. A `debug` stage (optional) keeps a shell for incident response while production stays slim. Interview question—“Why is the image 180MB not 1.4GB?”—answers with: no compilers/dev deps in runtime, slim base, lockfile-first layers, BuildKit cache mounts that never bake into the final image.

* **Apply It:**  
  1. Write a multi-stage Dockerfile with a builder stage and a slim runtime stage for the FastAPI package.  
  2. Install with uv (`uv sync --frozen --no-dev`); copy lockfile before source so dependency layers stay stable.  
  3. Add BuildKit cache mounts for `/root/.cache/uv`; set `UV_LINK_MODE=copy` when using them.  
  4. Run the runtime stage as a non-root `USER`; audit `.dockerignore`.  
  5. Use `--target` for debug/test stages that never ship to Cloud Run.  
  6. Do not bake large embedding weights into the API image unless required; keep prompt templates versioned in the image or a config service.

---

### Docker Compose for local development

* **Fundamentals:**  
  **Docker Compose** declares multi-container applications in YAML (`compose.yaml` / `docker-compose.yml`) so `docker compose up` starts the whole dependency graph. For Week 3 / FDE work, the canonical local stack is:

  - **API** — FastAPI RAG/agent service (build from multi-stage Dockerfile, often `--target` suitable for hot reload or bind mounts)  
  - **DB** — Postgres (often with **pgvector**)  
  - Optional: **Redis**, workers, OpenTelemetry collector, Adminer/pgAdmin  

  Compose is primarily a **dev / integration** tool. Production orchestration is Cloud Run, Kubernetes, ECS, etc. Treat compose as the reproducible laptop/CI-integration substrate—not as full prod.

  **Profiles** (official Compose docs): assign services to named profiles; services **without** profiles always start; profiled services start only when activated via `--profile` or `COMPOSE_PROFILES`. Core services should **not** be profile-gated so they always come up.

  ```yaml
  services:
    api:
      build: .
      depends_on:
        db:
          condition: service_healthy
    db:
      image: pgvector/pgvector:pg16
      healthcheck:
        test: ["CMD-SHELL", "pg_isready -U postgres"]
        interval: 5s
        timeout: 5s
        retries: 10
        start_period: 10s
    redis:
      image: redis:7-alpine
      profiles: ["cache"]
    otel-collector:
      image: otel/opentelemetry-collector:latest
      profiles: ["obs"]
    seed:
      build: .
      command: ["python", "-m", "myapp.seed"]
      profiles: ["tools"]
      depends_on:
        db:
          condition: service_healthy
  ```

  ```bash
  docker compose up                         # api + db
  docker compose --profile obs --profile cache up
  COMPOSE_PROFILES=tools docker compose run seed
  ```

  **Healthchecks and startup order:** Compose starts dependency order from `depends_on`, but **short-form `depends_on` only waits until the dependency container has started**—not until it is ready. Official startup-order docs: use long-form `depends_on` with `condition: service_healthy` (also `service_started` | `service_completed_successfully`). `healthcheck` mirrors Dockerfile `HEALTHCHECK` semantics (`test`, `interval`, `timeout`, `retries`, `start_period`). Escape Compose interpolation with `$$` when the variable must expand *inside* the container (`pg_isready -U $${POSTGRES_USER}`).

  **Volumes, networks, seed data:** named volumes for Postgres data so `down` without `-v` keeps state; bind mounts for API source during active development (with clear warning: not identical to prod image path); seed / fixture scripts under a `tools` profile for “messy” enterprise-like data (partial NULLs, duplicate titles, ACL columns).

  What Compose is for in an AI stack: local parity for **retrieval/DB quirks** (pgvector operators, migrations, connection pool behavior) that mocks erase; optional local Redis for cache-layer experiments; observability profile for tracing without requiring cloud backends every morning.

* **The Alternatives:**  

  | Approach | Strengths | Weaknesses | When |
  |----------|-----------|------------|------|
  | Compose | Low friction; one YAML; great for API+DB+vector | Drift from prod manifests; not a prod orchestrator | Phase 0 default; FDE laptop |
  | Dev Containers | Editor-integrated onboarding | Heavier IDE coupling | Team onboarding standardization |
  | Tilt / Skaffold + kind | Closer to K8s | Cognitive + resource cost | When prod is K8s and team already fluent |
  | Cloud-only staging | True parity | Slow loop; cost; offline failure | Supplement, not sole loop |
  | `gcloud run` local / Cloud Code emulator | Closer Cloud Run env semantics | Still not full multi-service DB realism alone | Pair with compose for data plane |
  | `gcloud run compose up` | Deploy compose-shaped stacks to Cloud Run | Subset of fields; defaults like max instances=1; not full IaC | Prototypes; not Week 3 teaching default |

  **Parity tradeoff:** compose that *claims* “identical to prod” lies. Document **parity limits** explicitly in README.

  | Local Compose | Cloud Run production |
  |---------------|----------------------|
  | Long-running containers | Scale-to-zero; **cold starts** |
  | One machine network | Request-driven instances; concurrency settings (default max concurrency often 80) |
  | Local volumes | Ephemeral disk (unless mounted Cloud Storage etc.) |
  | No IAM / VPC connectors | Service identity, Secret Manager, VPC egress |
  | Compose healthcheck | Platform health/readiness + your app’s `/healthz` |
  | Unlimited local “instances” | `min`/`max` instances; CPU allocation; request timeout |
  | `docker compose` multi-service network | Sidecars / multi-container services are a different model; `gcloud run compose` is a **subset** translator, not full prod IaC |

  Google’s local testing guidance: run the container locally (Docker / Cloud Code / `gcloud` local) **before** deploy; still expect behavioral differences. Compose remains best for the **data plane** (Postgres/pgvector) beside that.

* **Failure Modes:**  
  - Mock-only retrieval: bugs that only appear against real Postgres/pgvector (type casts, `NULL` metadata, index build time) escape to customer staging.  
  - “Just use prod Redis”: shared state corruption; cost; can’t work on a plane.  
  - Racey boots: API starts before DB accepts connections; flaky onboarding (`depends_on` without health).  
  - Laptop RAM death: every optional obs/tooling service always-on without profiles.  
  - False confidence: compose green assumed to prove Cloud Run concurrency, IAM, and cold-start behavior.  
  - Secrets in compose plaintext committed to git.

* **Average vs. Strong Engineer:**  
  **Average:** single service Dockerfile only; no compose—or compose without healthchecks and `sleep 10` scripts; no documented differences vs Cloud Run; secrets in compose plaintext.  
  **Strong:** `compose.yaml` with **profiles**: default API+DB; `cache`, `obs`, `tools`; `depends_on` + `service_healthy` for Postgres/pgvector; named volumes; seed scripts; `.env.example` (not real secrets); document **parity limits** vs Cloud Run in README; same multi-stage Dockerfile with compose overrides command for reload in dev only; CI job: `docker compose up -d --wait` + integration tests against the stack; optional mental-model alignment with later Terraform/K8s—don’t duplicate forever.

* **Worked Example:**  
  For Deployment Copilot you add `compose.yaml` with always-on `api` + `db` (`pgvector/pgvector:pg16`), Redis under profile `cache`, OpenTelemetry collector under `obs`, and a `seed` service under `tools`. The API `depends_on` the DB with `condition: service_healthy`. Day-to-day you run `docker compose up` (API + DB only). When experimenting with retrieval caches: `docker compose --profile cache up`. Seed messy fixtures with `COMPOSE_PROFILES=tools docker compose run seed`. The README lists parity limits: compose does **not** prove Cloud Run cold starts, concurrency (often default max ~80), IAM, Secret Manager, or VPC egress. Interview question—“What does compose *not* prove about Cloud Run concurrency?”—answers from that table.

* **Apply It:**  
  1. Add `compose.yaml` with API (build from multi-stage Dockerfile) + Postgres/pgvector as always-on services.  
  2. Put Redis, observability, and seed/tools behind named profiles.  
  3. Use long-form `depends_on` with `condition: service_healthy` for the database.  
  4. Use named volumes for DB data; `.env.example` instead of committed secrets.  
  5. Document Cloud Run parity limits in the README (cold start, concurrency, IAM, ephemeral disk).  
  6. Optionally add a CI job: `docker compose up -d --wait` plus integration tests against the stack.

---

### System design vocabulary (latency, scaling, caching, CAP)

* **Fundamentals:**  
  The syllabus asks for a **living system design doc**. Without shared terms, the doc is boxes and arrows. Interviewers (Week 23) and FDE customers probe the same tradeoffs. This section is the glossary that doc must use.

  **Latency vs throughput:**  
  - **Latency**: time per request (prefer **percentiles**: p50 / p95 / p99—not only averages). Google SRE: request latency is a core SLI for user-facing serving systems.  
  - **Throughput**: work per unit time (QPS, tokens/sec, docs ingested/min).  
  - Coupling: higher QPS often raises latency; services have **performance cliffs**. Batching can ↑ throughput and ↑ per-item latency simultaneously—state both.  
  LLM wrinkle: provider latency dominates; your p95 may be “model + retrieval + rerank,” not “FastAPI.” Measure **stages** (retrieve, rerank, generate) separately.

  **Vertical vs horizontal scaling:**  
  - **Vertical**: bigger machine/CPU/RAM (or larger Cloud Run memory/CPU). Simple; ceilinged; bigger blast radius.  
  - **Horizontal**: more replicas behind a **load balancer**. Needs statelessness (or sticky sessions / externalized state). Cloud Run / K8s scale horizontally with concurrency and instance counts.

  **Load balancing:** Google SRE Book chapters 19–20 (frontend LB, datacenter LB): distribute traffic across instances; health checking; avoid overload. In practice for Week 3: Cloud Run / GFE / cloud LB chooses instances; app-level: timeout budgets, retries with jitter, **load shedding** when saturated or when provider returns 429; don’t let retry storms amplify outages (SRE overload / cascading failure chapters).

  **Caching layers:** typical web path: client → CDN/edge → app → Redis → DB. LLM / RAG additions: **exact prompt / response cache** (identical inputs); **semantic cache** (near-duplicate embeddings)—Phase 5 depth; **provider prompt caches** (Anthropic/OpenAI-style)—Phase 1; **retrieval caches** keyed by corpus version + query hash; **embedding caches** for repeated chunks. Every cache needs: **hit-rate**, **TTL**, **invalidation** on corpus/prompt version bump, and a stated consistency story.

  **CAP theorem (correct framing):** informal “pick two of three” (Consistency, Availability, Partition tolerance) is **misleading**. Eric Brewer’s retrospective (*CAP Twelve Years Later*, InfoQ): partitions are the rare case forcing C vs A; outside partitions you need not forfeit C or A; choices can be **per operation / per subsystem**, not a permanent database tattoo; properties are continuous, not binary. Formal roots: Brewer conjecture (PODC 2000); Gilbert & Lynch proof (2002). CAP **consistency** ≈ linearizability (narrower than ACID “C”). CAP **availability** ≈ every non-failing node eventually responds (not the same as “five 9s marketing”). Google Cloud Spanner write-up: real systems discuss realistic high availability and partition *mitigation*, not cartoon CA/CP stickers.

  **PACELC (Abadi):** **if** Partition → trade Availability vs Consistency; **else** → trade **Latency** vs Consistency. Captures the normal-operation cost of strong consistency (cross-replica coordination). Textbook classifications (verify per config): PA/EL — Dynamo-style / Cassandra-like defaults (favor A and L); PC/EC — Spanner / many strongly consistent NewSQL (favor C, pay L and A under partition). For RAG: ACL/entitlement checks often need stronger C; document-popularity caches can be eventually consistent.

  **SLIs, SLOs, SLAs** (SRE Book Ch. 4):  
  - **SLI**: quantitative measure (latency, error rate, throughput, availability/yield).  
  - **SLO**: target on an SLI (e.g., p95 latency < X).  
  - **SLA**: contract with consequences if missed.  
  SRE guidance: few representative indicators; user-facing systems care about availability, latency, throughput; publishing SLOs sets expectations.

  **LLM-specific SLOs and cost:** emerging practice: treat **cost** (USD/query, tokens/query, GPU-sec) as a first-class objective alongside latency and availability—“CAL” thinking, not classical CAP. Also track groundedness / eval quality gates (not SRE classical, but product SLI); provider error/429 rate; cold-start latency for serverless containers. A design doc that only says “highly available RAG” without p95 and $/query is incomplete for FDE work.

* **The Alternatives:**  

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

  Interview anti-pattern: “We’ll add Redis” with no hit-rate, TTL, or invalidation plan. CAP anti-pattern: “Mongo is AP, Postgres is CA” as absolute identity.

  RAG design examples (tradeoff table for the living doc):

  | Operation | Lean | Rationale |
  |-----------|------|-----------|
  | Entitlement check before retrieve | Stronger C | Wrong doc = compliance incident |
  | Dense ANN query | Latency; approximate | Approximate neighbor OK; freshness SLO separate |
  | Prompt response cache | EL (favor L) | Invalidate on prompt/corpus version |
  | Billing token counters | Stronger C | Money |

* **Failure Modes:**  
  - Design docs cannot explain why hybrid search + rerank blows p95.  
  - Multi-region RAG with residency constraints sold as “just CA.”  
  - Autoscaling without concurrency/load-shedding plan → 429 storms + DB connection exhaustion.  
  - Cache without corpus versioning → “wrong answer from yesterday’s policy PDF.”  
  - Week 23 interviews: candidate draws boxes, cannot discuss percentiles, PACELC, or cost SLOs.  
  - Averages instead of percentiles; CAP recited as pick-two menu; no cost objective—surprised by bill after demo traffic; design doc written once for interview, never updated.

* **Average vs. Strong Engineer:**  
  **Average:** averages instead of percentiles; CAP recited as pick-two menu; “Redis cache” with no metrics; no cost objective; design doc written once for interview, never updated.  
  **Strong:** SLOs on **p95 latency** and **cost/query**; error budget thinking from SRE; cache TTLs tied to **corpus version** / prompt version; CAP/PACELC stated per *operation* (authZ check vs popularity cache vs ANN search freshness); load shedding / graceful degradation when provider 429s (smaller model; cached answer; “degraded” UX); explicit cold-start and concurrency assumptions for Cloud Run; vector DB freshness guarantees documented honestly (ANN ≠ linearizable read of source of truth). FDE / platform bar: CAP/PACELC stated per operation (ACL check vs popularity cache).

* **Worked Example:**  
  You write `docs/system-design.md` (living one-pager) for Deployment Copilot with at least these sections, using this vocabulary:

  1. Goals / non-goals  
  2. Request path + sequence (retrieve → rerank → generate)  
  3. SLIs/SLOs (latency percentiles, availability, **$/query**)  
  4. Scaling model (horizontal; concurrency assumptions)  
  5. Caching layers + invalidation  
  6. Data stores + CAP/PACELC **per operation**  
  7. Failure modes (provider down, partition, overload)  
  8. Open questions  

  Example SLO sketch grounded in research practice: p95 end-to-end chat latency broken into retrieve / rerank / generate stages; availability/error-rate SLI; **$/query** (tokens × price + infra). Entitlement checks lean stronger consistency; ANN search favors latency with a separate freshness SLO; prompt response cache favors latency (PACELC “EL”) and invalidates on prompt/corpus version. When the provider returns 429, the doc states load shedding / graceful degradation (smaller model, cached answer, degraded UX)—not “retry forever.” Keep the doc living: update when architecture changes land on trunk (TBD).

* **Apply It:**  
  1. Create a living one-page system design doc (`docs/system-design.md` or equivalent) for the chatbot.  
  2. State SLIs/SLOs with **p95 latency** (stage-broken) and **$/query**—not averages alone.  
  3. Describe horizontal scaling and Cloud Run concurrency / cold-start assumptions.  
  4. List caching layers with hit-rate intent, TTL, and invalidation on corpus/prompt version.  
  5. State CAP/PACELC choices **per operation** (ACL vs ANN vs cache vs billing)—never a single database sticker.  
  6. Document failure modes (provider 429, partition, overload) and update the doc when trunk architecture changes.

---

## Week 3 build checklist (end-to-end)

Use this as the chapter’s capstone sequence; every concept above maps here.

1. **Git rhythm:** Short-lived PRs into `main`; incomplete features behind flags; no week-long epic branches.  
2. **Commits:** Conventional Commits with useful scopes; eval deltas and flag names in bodies when behavior changes.  
3. **Dockerfile:** Multi-stage builder + slim runtime; uv frozen sync `--no-dev`; non-root USER; `.dockerignore`.  
4. **Compose:** API + Postgres/pgvector always on; profiles for cache/obs/tools; `service_healthy` depends_on; parity limits documented.  
5. **Design doc:** One-page living system design using latency/throughput, scaling, load balancing, caching, CAP/PACELC-per-operation, and cost SLOs.  
6. **Interview readiness:** Be able to answer why the image is small, what compose does not prove about Cloud Run, and what your p95 and $/query targets are when the LLM is the bottleneck.

When those six steps are true, Week 3 is done in the syllabus sense: Deployment Copilot is a containerized FastAPI service with local data-plane realism and a design document that speaks the same language Week 23 interviews probe. Phase 0 engineering foundations close here; later weeks run in containers against real stores and stay explainable in a living design document.

---

## Looking ahead

Week 4 opens **Multi-provider LLM engineering**: a **provider-agnostic client** that swaps OpenAI, Anthropic, and optional gateway backends behind one interface, plus **structured outputs**, **token counting** / context windows, and **prompt caching**. Keep the containerized FastAPI service, compose data plane, short-lived Git rhythm, and living system design doc—you will call real providers correctly through them, not replace the shippable shell.
