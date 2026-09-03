# 04 — Docker Compose for local development

> Week 3 concept research (deep). Legal sources only.

---

## Fundamentals

### What Compose is
**Docker Compose** declares multi-container applications in YAML (`compose.yaml` / `docker-compose.yml`) so `docker compose up` starts the whole dependency graph. For Week 3 / FDE work, the canonical local stack is:

- **API** — FastAPI RAG/agent service (build from multi-stage Dockerfile, often `--target` suitable for hot reload or bind mounts)  
- **DB** — Postgres (often with **pgvector**)  
- Optional: **Redis**, workers, OpenTelemetry collector, Adminer/pgAdmin  

Compose is primarily a **dev / integration** tool. Production orchestration is Cloud Run, Kubernetes, ECS, etc. Treat compose as the reproducible laptop/CI-integration substrate—not as full prod.

### Profiles
Official Compose profiles docs: assign services to named profiles; services **without** profiles always start; profiled services start only when activated via `--profile` or `COMPOSE_PROFILES`.

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

Docs tip: core services should **not** be profile-gated so they always come up.

### Healthchecks and startup order
Compose starts dependency order from `depends_on`, but **short-form `depends_on` only waits until the dependency container has started**—not until it is ready. Official startup-order docs: use long-form:

```yaml
depends_on:
  db:
    condition: service_healthy
```

Conditions: `service_started` | `service_healthy` | `service_completed_successfully`.

`healthcheck` mirrors Dockerfile `HEALTHCHECK` semantics (`test`, `interval`, `timeout`, `retries`, `start_period`). Escape Compose interpolation with `$$` when the variable must expand *inside* the container (`pg_isready -U $${POSTGRES_USER}`).

### Volumes, networks, seed data
- Named volumes for Postgres data so `down` without `-v` keeps state.  
- Bind mounts for API source during active development (with clear warning: not identical to prod image path).  
- Seed / fixture scripts under a `tools` profile for “messy” enterprise-like data (partial NULLs, duplicate titles, ACL columns).

### What Compose is for in an AI stack
Local parity for **retrieval/DB quirks** (pgvector operators, migrations, connection pool behavior) that mocks erase. Optional local Redis for cache-layer experiments. Observability profile for tracing without requiring cloud backends every morning.

---

## Alternatives & Tradeoffs

| Approach | Strengths | Weaknesses | When |
|----------|-----------|------------|------|
| **Compose** | Low friction; one YAML; great for API+DB+vector | Drift from prod manifests; not a prod orchestrator | Phase 0 default; FDE laptop |
| **Dev Containers** | Editor-integrated onboarding | Heavier IDE coupling | Team onboarding standardization |
| **Tilt / Skaffold + kind** | Closer to K8s | Cognitive + resource cost | When prod is K8s and team already fluent |
| **Cloud-only staging** | True parity | Slow loop; cost; offline failure | Supplement, not sole loop |
| **`gcloud run` local / Cloud Code emulator** | Closer Cloud Run env semantics | Still not full multi-service DB realism alone | Pair with compose for data plane |
| **`gcloud run compose up`** | Deploy compose-shaped stacks to Cloud Run | Subset of fields; defaults like max instances=1; not full IaC | Prototypes; not Week 3 teaching default |

**Parity tradeoff:** compose that *claims* “identical to prod” lies. Document **parity limits** explicitly in README (see below).

---

## Necessity

### Failure modes if skipped
1. **Mock-only retrieval** — bugs that only appear against real Postgres/pgvector (type casts, `NULL` metadata, index build time) escape to customer staging.  
2. **“Just use prod Redis”** — shared state corruption; cost; can’t work on a plane.  
3. **Racey boots** — API starts before DB accepts connections; flaky onboarding (`depends_on` without health).  
4. **Laptop RAM death** — every optional obs/tooling service always-on without profiles.  
5. **False confidence** — compose green assumed to prove Cloud Run concurrency, IAM, and cold-start behavior.

### FDE “messy systems” gap
Without local dependencies, engineers mock away the messy integration surface that FDE roles are hired to navigate. Compose + seed fixtures are the Phase 0 antidote.

---

## Industry Practice

### Common (weak)
- Single service Dockerfile only; no compose.  
- Or compose without healthchecks; `sleep 10` scripts.  
- No documented differences vs Cloud Run.  
- Secrets in compose plaintext committed to git.

### Strong / senior
- `compose.yaml` with **profiles**: default API+DB; `cache`, `obs`, `tools`.  
- `depends_on` + `service_healthy` for Postgres/pgvector.  
- Named volumes; seed scripts; `.env.example` (not real secrets).  
- Document **parity limits** vs Cloud Run in README.  
- Same multi-stage Dockerfile; compose overrides command for reload in dev only.  
- CI job: `docker compose up -d --wait` + integration tests against the stack.  
- Optional: generate mental model alignment with later Terraform/K8s—don’t duplicate forever.

### Parity limits vs Cloud Run (document these)
From Google Cloud Run docs and operational reality:

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

---

## Concrete Scenario

**Compose documentation hub**  
https://docs.docker.com/compose/  

**Profiles how-to**  
https://docs.docker.com/compose/how-tos/profiles/  

**Startup order + healthchecks**  
https://docs.docker.com/compose/how-tos/startup-order/  

**Compose file services reference (`healthcheck`, `profiles`, `depends_on`)**  
https://docs.docker.com/reference/compose-file/services/  

**Cloud Run — test locally**  
https://cloud.google.com/run/docs/testing/local  

**Cloud Run — general tips (concurrency, min instances)**  
https://cloud.google.com/run/docs/tips/general  

**Cloud Run — deploy using Compose (subset / caveats)**  
https://docs.cloud.google.com/run/docs/deploy-run-compose  

**YouTube seed — Docker Compose official tutorial**  
https://www.youtube.com/results?search_query=docker+compose+official+tutorial  

---

## Open Questions

- Compose vs Podman Compose vs Kubernetes-local as the teaching default for FDE candidates?  
- How to share compose “customer simulator” packs (SSO stubs, messy SQL fixtures) across engagements without leaking customer data?  
- Should integration tests in CI use compose or Testcontainers—and is that a Week 3 or Week 2 residual decision?  
- When does `gcloud run compose up` help vs confuse Phase 0 learners about prod IaC?

---

## Sources

- https://docs.docker.com/compose/  
- https://docs.docker.com/compose/compose-file/  
- https://docs.docker.com/compose/how-tos/profiles/  
- https://docs.docker.com/compose/how-tos/startup-order/  
- https://docs.docker.com/reference/compose-file/services/  
- https://cloud.google.com/run/docs/testing/local  
- https://cloud.google.com/run/docs/tips/general  
- https://docs.cloud.google.com/run/docs/deploy-run-compose  
- https://www.youtube.com/results?search_query=docker+compose+official+tutorial  
