# 03 — Docker multi-stage builds (image size, BuildKit, Python/uv)

> Week 3 concept research (deep). Legal sources only.

---

## Fundamentals

### Images vs containers
Docker packages application + runtime into an **image** (immutable filesystem layers + metadata). A **container** is a running instance. Production deploys (Cloud Run, Kubernetes, ECS) pull images; image size and layer structure directly affect pull latency, cold start, and CVE surface.

### What multi-stage builds are
Official Docker docs: use multiple `FROM` statements in one Dockerfile. Each `FROM` starts a new stage (optionally `AS name`). Copy only needed artifacts with `COPY --from=stage` into a slim runtime stage—leaving compilers, SDKs, caches, and test tooling behind.

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

### Why size and attack surface matter
Docker best practices: choose minimal trusted bases; use a fat builder image and a slimmer production image so final output lacks build tools. Smaller images → faster downloads/portability, fewer dependency CVEs. Rebuild often (`--pull`) because tags move under you as publishers patch.

### BuildKit cache mounts
`RUN --mount=type=cache,target=...` persists package-manager caches across builds without baking them into image layers. Critical for CI speed when dependency layers invalidate.

### `.dockerignore`
Excludes junk from the build context (`.git`, `.venv`, `tests`, local `.env`, notebooks, `node_modules`). Smaller context = faster uploads to the daemon and less accidental `COPY` of secrets/source you meant to leave out.

### Non-root
Runtime stage should `USER` a non-root account. Running as root in production widens blast radius of RCE. Pair with read-only root filesystem where the platform allows.

### Python / uv idiomatic pattern
Astral uv Docker guide + community “optimal Dockerfile” patterns:

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

Key ideas:
- Lockfile-first layer so code edits don’t bust dependency install.  
- `--frozen` / `--locked` for deterministic CI installs.  
- `--no-dev` so pytest/ruff never ship.  
- `UV_LINK_MODE=copy` with cache mounts (cross-filesystem hardlink warning).  
- Optional separate `debug` stage with a shell for incident response while prod stays slim/distroless.

---

## Alternatives & Tradeoffs

| Approach | Strengths | Weaknesses | When |
|----------|-----------|------------|------|
| **Single-stage fat image** | Simple Dockerfile | Slow pulls; large CVE surface; ships compilers | Throwaway demos only |
| **Multi-stage + slim** | Production default; readable | Slightly harder debug | Syllabus / Cloud Run default |
| **Multi-stage + distroless / Chainguard / Wolfi** | Minimal attack surface | No shell for `exec`; native wheel friction | Hardened prod once debug stage exists |
| **Buildpacks** | Less Dockerfile craft | Less control; harder custom native deps | Teams standardizing on buildpacks |
| **Scratch / static binary** | Tiny | Mostly Go/Rust; not typical CPython | Non-Python sidecars |

**Debug tradeoff:** distroless prod + `docker build --target debug` (or ephemeral debug container) beats keeping bash in every prod image “just in case.”

**Cache tradeoff:** cache mounts speed rebuilds; `--no-cache` for clean dependency refresh is occasional, not default.

**Pinning tradeoff:** floating `python:3.12` vs digest-pinned bases—digests for prod reproducibility; rebuild cadence for patches.

---

## Necessity

### Failure modes if skipped
1. **GB-sized images** delay Cloud Run / Kubernetes node pulls; autoscaling feels “broken.”  
2. **Build tools in prod** (gcc, rustc for wheels, leftover `.git`) expand CVE scans and incident blast radius.  
3. **Root runtime** — container escape / misconfig impact worse.  
4. **Context bloat** — copying `.venv` and secrets because no `.dockerignore`.  
5. **CI thrash** — every code change reinstalls all deps (wrong layer order; no cache mount).

### Cloud Run / syllabus path
Syllabus deploys toward Cloud Run-style container hosting: oversized images slow cold starts and ship unused build tools. Postmortems regularly cite multi-GB images delaying deploys. Multi-stage is the standard fix (Docker 17.05+; BuildKit now default).

---

## Industry Practice

### Common (weak)
```dockerfile
FROM python:3.12
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["uvicorn", "main:app", "--host", "0.0.0.0"]
```
Runs as root; no pin; no ignore file; includes tests/dev deps; no health semantics.

### Strong / senior
- `# syntax=docker/dockerfile:1`  
- Builder stage with uv; runtime `python:*-slim` or distroless  
- `uv sync --frozen --no-dev`; deps-first layer ordering  
- BuildKit cache mounts for `/root/.cache/uv`  
- Non-root `USER`; optional read-only root  
- `.dockerignore` audited  
- SBOM + image scan in CI (Trivy/Grype class tools)  
- `--target` for test/lint stages that never ship  
- Base images rebuilt on a schedule with `--pull`  
- Healthcheck at orchestrator/compose layer (and/or `HEALTHCHECK` in image)

### Docker official talk signal
DockerCon / Docker Official “Dockerfile Best Practices” (Tibor Vass, Sebastiaan van Stijn): **use multi-stage Dockerfiles and enable BuildKit**; parallelize independent stages; cache mounts matter.  
https://www.youtube.com/watch?v=JofsaZ3H1qM

### RAG service specifics
- Don’t bake large embedding model weights into the API image unless required—prefer volume/sidecar/model service.  
- Native wheels (tokenizers, numpy) may block pure distroless until glibc/musl needs are understood—slim is a pragmatic Phase 0 default.  
- Keep prompt templates as versioned files in the image *or* config service—but not untracked notebooks.

---

## Concrete Scenario

**Docker official — Multi-stage builds**  
https://docs.docker.com/build/building/multi-stage/  

Documents named stages, `--target`, `COPY --from`, BuildKit vs legacy unused-stage behavior.

**Docker official — Building best practices**  
https://docs.docker.com/build/building/best-practices/  

Multi-stage, base image choice, rebuild cadence, layer hygiene.

**Get-started concept page**  
https://docs.docker.com/get-started/docker-concepts/building-images/multi-stage-builds/  

**uv in Docker (Astral)**  
https://docs.astral.sh/uv/guides/integration/docker/  

Cache mounts, `UV_LINK_MODE=copy`, lockfile-driven sync patterns.

**YouTube — Dockerfile Best Practices (Docker)**  
https://www.youtube.com/watch?v=JofsaZ3H1qM  

---

## Open Questions

- Distroless vs Wolfi/Chainguard as default for Python LLM services with native wheels?  
- How much does image size still dominate Cloud Run cold start vs runtime initialization (model clients, DB pools)?  
- Should Week 3 mandate digest pinning + Cosign signing, or defer signing to Week 18?  
- Multi-platform (`buildx --platform`) for Apple Silicon dev vs linux/amd64 Cloud Run—when to pay the emulation cost?

---

## Sources

- https://docs.docker.com/build/building/multi-stage/  
- https://docs.docker.com/build/building/best-practices/  
- https://docs.docker.com/get-started/docker-concepts/building-images/multi-stage-builds/  
- https://docs.docker.com/build/guide/mounts/  
- https://docs.astral.sh/uv/guides/integration/docker/  
- https://depot.dev/docs/container-builds/optimal-dockerfiles/python-uv-dockerfile  
- https://www.youtube.com/watch?v=JofsaZ3H1qM  
- https://www.youtube.com/results?search_query=docker+multi-stage+builds+official  
