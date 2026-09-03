# 01 — Containerized deployment patterns for LLM services

> Week 18 — production images and runtime contracts (Cloud Run / K8s / Compose).  
> Local Compose and multi-stage *mechanics* were Week 3; this file is **how those images get shipped**. Research notes (raw).

---

## Fundamentals

A **container** packages an application and its runtime dependencies into an immutable **OCI/Docker image**. A **containerized deployment** is: build that image once, store it in a registry by **digest**, inject **config and secrets at runtime**, and run **N replicas** behind a load balancer that respects **health**.

For LLM apps the image usually holds:

- The API process (FastAPI/uvicorn, Node, etc.) and model-client SDKs  
- OpenTelemetry instrumentation (Week 17 traces)  
- **Not** frontier model weights (provider or a separate GPU inference fleet)  
- **Not** API keys (secret store / K8s Secret / Cloud Run secret — identity hardening is Week 19)

### Production loop

1. **Build** a slim runtime image (multi-stage: compile/deps → runtime). Official Docker: multiple `FROM`; `COPY --from=` leaves compilers out of the final image ([multi-stage builds](https://docs.docker.com/build/building/multi-stage/); [building best practices](https://docs.docker.com/build/building/best-practices/)).  
2. **Config via env**, secrets via a secret store. Never bake keys into layers (`.dockerignore` is not enough if `COPY . .` ran before you noticed).  
3. **Health endpoints:**  
   - **Liveness** (`/healthz`): process is not deadlocked; failure → restart.  
   - **Readiness** (`/ready`): this replica may receive traffic (vector DB + LLM provider reachable, connection pool not exhausted).  
   - **Startup** (K8s/Cloud Run): slow model-client warmup without killing the container.  
   Kubernetes probe semantics: [liveness/readiness/startup](https://kubernetes.io/docs/concepts/configuration/liveness-readiness-startup-probes/).  
4. **Stateless app tier** behind a load balancer; durable state in managed DB / object store / queue.  
5. **Sidecars or gateways** for auth, rate limits, observability (OTEL collector, LiteLLM proxy, Envoy) — optional; do not require a mesh on week one.

Compose is the **inner loop** (app + Redis + Postgres) ([Compose](https://docs.docker.com/compose/)). Production almost always moves to an orchestrator (K8s, ECS, Cloud Run) once you need rolling deploys, autoscaling, and multi-replica HA.

### Cloud Run container contract (if you skip a cluster)

Cloud Run **services** must:

- Listen on `0.0.0.0`, **not** `127.0.0.1`  
- Honor the injected **`PORT`** (default **8080**)  
- Become ready to serve within the platform’s startup window (CPU allocated during startup; optional CPU boost)  

Injected vars include `PORT`, `K_SERVICE`, `K_REVISION`, `K_CONFIGURATION` ([container runtime contract](https://cloud.google.com/run/docs/container-contract)).

**Health checks:** startup / liveness / readiness; HTTP `2XX`/`3XX` success; failed liveness → `SIGKILL` and in-flight requests terminate **503** ([Cloud Run health checks](https://cloud.google.com/run/docs/configuring/healthchecks)). Docker `HEALTHCHECK` in the image is **not** the Cloud Run control plane.

**Min instances:** default `0` (scale to zero → cold start on first LLM request). Set min instances to keep warm replicas; idle instances can still be rebalanced. Combine with instance-based billing if you need CPU outside requests ([min instances](https://cloud.google.com/run/docs/configuring/min-instances); [autoscaling](https://cloud.google.com/run/docs/about-instance-autoscaling)). Trap `SIGTERM` (~10s) for graceful drain.

**Concurrency:** Cloud Run multiplexes many requests per instance; LLM streaming + high concurrency can pin memory and provider sockets. Tune concurrency **down** for long generations.

### GPU / self-hosted inference

Treat **API pods** and **GPU inference** as different images and different node pools. CUDA/driver pinning, cold starts, and cost live on the inference fleet. The API container stays slim and talks HTTP/gRPC to vLLM/TGI/a vendor.

### Workers vs API

Long-running agent jobs should **not** share the request-serving Deployment if they need different HPA signals (queue depth vs RPS) or different disruption budgets. Pattern: API Deployment + **queue-consumer** Deployment (SQS/Pub/Sub). Scale workers with KEDA/HPA on queue length (file [02](02-kubernetes-fluency.md)).

---

## Alternatives & Tradeoffs

| Pattern | When | Tradeoff |
|---------|------|----------|
| Single VM + Docker Compose | Prototype, internal tool | Manual HA; weak rollback; “staging” is the VM |
| Managed containers (Cloud Run, App Runner, Azure Container Apps) | Stateless APIs, bursty traffic | Less control of networking/sidecars; GPU/custom CNI limited |
| Kubernetes | Multi-service platforms, enterprise networking, custom autoscaling | Operational surface; interview-relevant fluency |
| GPU node pools / dedicated inference | Self-hosted models | Cost, cold starts, driver/CUDA pinning |
| Serverless functions only | Thin glue / webhooks | Timeout, payload, cold-start vs long LLM calls |
| Distroless / alpine / chainguard | Smaller CVE surface | Harder `kubectl exec` debug during incidents |
| Fat ubuntu image | Easy debug | Pull latency, CVE noise, root habits |

For LLM **gateways** (LiteLLM, custom router): run as a Deployment (or Cloud Run service) with HPA on RPS/concurrency; keep embeddings/vector DBs as **managed** services when possible.

**Sidecar vs in-process instrumentation:** sidecar OTEL collector isolates crash domains; in-process SDK is simpler on Cloud Run (sidecars supported but you must set startup order + probes).

---

## Necessity

Without containerization you get “works on my laptop” drift, unreproducible incidents, and unsafe secret handling.

Without **readiness** probes, load balancers send traffic to pods that cannot reach the model provider → **cascading 5xx during deploys** (the most common “we deployed and the world died” LLM outage).

Without **immutability**, hotfixes on live boxes erase the audit trail and make rollback guesswork.

Without honoring Cloud Run **`PORT` / 0.0.0.0`**, the revision never becomes ready; you debug “service unavailable” for hours.

Without **min instances** (or K8s `minReplicas`) on a latency-sensitive chat API, the first token after scale-to-zero includes **image pull + Python import + TLS to the provider**.

Without a **separate worker image/Deployment**, a backlog of agent jobs starves HTTP readiness (thread pool / event loop shared).

---

## Industry Practice

**Common:** one Dockerfile, `docker push …:latest`, deploy to Cloud Run or a single Deployment, `/health` that returns 200 if the process started, env vars pasted in the console, root user.

**Strong / senior:**

- Multi-stage; distroless or pinned distro; **non-root** `USER`; SBOM + image scanning in CI  
- Resource **requests/limits** from load tests (HPA needs CPU **requests** — file 02)  
- Separate images for **worker vs API**  
- OpenTelemetry baked in; config via ConfigMap/Secret with **checksum-triggered** rollouts  
- Readiness checks **provider + DB**, not only `return {"ok": true}`  
- `preStop` sleep + graceful shutdown so **in-flight LLM streams** finish (K8s `terminationGracePeriodSeconds` sized to max stream)  
- Registry **digest** in the manifest, tag only for humans  
- Cloud Run: explicit concurrency, min instances for chat, secrets from Secret Manager, startup probe if imports are slow  

Docker docs + Cloud Run samples remain the legal how-to; KubeCon talks assume this baseline and then talk about **rollout analysis** (file 03).

---

## Concrete Scenario (URL)

**Kubernetes Deployment** as the declarative rollout primitive for containerized LLM APIs:  
https://kubernetes.io/docs/concepts/workloads/controllers/deployment/

**Probes** — liveness vs readiness vs startup (do not use liveness for “provider down” or you restart the world):  
https://kubernetes.io/docs/concepts/configuration/liveness-readiness-startup-probes/

**Docker multi-stage** — official:  
https://docs.docker.com/build/building/multi-stage/

**Compose** — local multi-service only:  
https://docs.docker.com/compose/

**Cloud Run container contract** — `PORT`, `0.0.0.0`, injected `K_*` vars:  
https://cloud.google.com/run/docs/container-contract

**Cloud Run health checks** — HTTP success codes; liveness → SIGKILL / 503 in-flight:  
https://cloud.google.com/run/docs/configuring/healthchecks

**Cloud Run min instances / autoscaling** — warm vs scale-to-zero:  
https://cloud.google.com/run/docs/configuring/min-instances  
https://cloud.google.com/run/docs/about-instance-autoscaling

**SRE health checking / degradation** — why probes exist:  
https://sre.google/sre-book/service-best-practices/

---

## Open Questions

- Distroless vs distro images: CVE response speed vs debug-ability in a 3am streaming-stuck incident?  
- When does self-hosted GPU K8s beat staying on managed APIs (utilization, data residency — Week 19 — vs driver toil)?  
- Should LLM **workers** share the API Deployment or always use a queue-consumer Deployment?  
- Cloud Run concurrency vs one-generation-per-instance for SSE streams?  
- Is a **gateway container** (LiteLLM) in-process library or sidecar the right isolation for key rotation (Week 19)?

---

## Sources

- https://docs.docker.com/build/building/multi-stage/  
- https://docs.docker.com/build/building/best-practices/  
- https://docs.docker.com/compose/  
- https://kubernetes.io/docs/concepts/workloads/controllers/deployment/  
- https://kubernetes.io/docs/concepts/configuration/liveness-readiness-startup-probes/  
- https://cloud.google.com/run/docs/container-contract  
- https://cloud.google.com/run/docs/configuring/healthchecks  
- https://cloud.google.com/run/docs/configuring/min-instances  
- https://cloud.google.com/run/docs/about-instance-autoscaling  
- https://cloud.google.com/run/docs/configuring/services/containers  
- https://sre.google/sre-book/service-best-practices/  
- https://www.youtube.com/@cncf  
