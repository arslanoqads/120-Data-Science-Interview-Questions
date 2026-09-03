# Chapter 18 — Deployment infrastructure

> **Phase 5 — Production, Cost, and Systems**  
> **Editorial status:** COMPLETE  
> **Source of truth:** `research/phase-5/week-18-deployment-infra/`  
> **Syllabus Build:** You already have **Week 17 traces, judges, and dashboards**. This week you **put the same service on a real delivery path**. (1) **Containerize for production, not only local Compose.** Multi-stage image; non-root; config via env; secrets from a store; `/healthz` (liveness) and `/ready` (can reach vector DB + LLM provider). Do **not** bake frontier weights or API keys into the image. (2) **Read and explain Kubernetes YAML.** A Deployment + ClusterIP Service + HPA. Explain a failed rollout (`kubectl rollout status` / ReplicaSet history). Propose **one** HPA metric that is not CPU if the API is provider-bound. (3) **Staged pipeline.** CI builds **one digest**; promote `dev` → `staging` → `prod`. Staging runs golden-set smoke (Week 16/17 evals). Prod uses rolling updates **or** a canary with abort on error rate / p95 / eval score. Rehearse rollback. (4) **Basic Terraform.** VPC/cluster-or-Cloud-Run, IAM for the workload (static keys deferred to Week 19), remote state with locking, separate state for `staging` vs `prod`. PR runs `plan`; apply from protected main.

---

## Prerequisites Recap

Before this week you should already have from Week 17:

- **Calibrated LLM-as-judge** shadows for residual subjective Week 16 failure modes: binary Pass/Fail + critique; principal domain expert owns the standard; **TPR/TNR** gates on held-out labels.  
- A clear **code vs model** split: objective failures (JSON, schema, citation IDs, tool names) as **code evals in CI**; LLM judges reserved for judgment-heavy modes and run sparingly in CI or on a **sampled schedule**.  
- **Hierarchical tracing** (Langfuse **and/or** Phoenix): generations carry `model`, params, tokens, cost; retrieved context on the observation you will judge; tags for `userId` / `sessionId` / `version` / `env`.  
- **Production dashboards** for volume, errors, p95 latency, cost/day and cost/successful-task, and **1–3 calibrated** quality timeseries; alerts that open **traces**, not bare pages; online judges sampled (~2–10%); guardrails in-request, async evaluators for trends.  
- From Week 16 (still in force): custom failure taxonomy, expert labels, and the production → labels → eval set → regression **flywheel** — staging golden-set smoke this week reuses that suite.

You do **not** need production multi-stage images with digest promotion, walkable Deployment/Service/HPA YAML, staged `dev` → `staging` → `prod` with rehearsed rollback, or Terraform remote state yet as *finished* products — that is what this week ships. You **do** need the Week 17 instrumented service (judges, traces, dashboards); without them, canary abort on eval score and staging golden-set smoke have nothing trustworthy to gate on.

---

## What this week builds

Week 17 **calibrated judges**, chose **code vs model** evals, and made **Langfuse/Phoenix traces and dashboards** usable as a product. Week 18 opens **Phase 5 — Production, Cost, and Systems** as the **shipping** week: put that **same** instrumented service on a real delivery path. This week answers four questions Kubernetes docs, Cloud Run, Terraform, GitHub Actions, and the Google SRE book all treat as the minimum bar for an FDE who can land an LLM service:

1. **Where does a change prove it is safe before customers see it?** (staging environment)  
2. **How do you undo a bad ship in minutes, with bits you already built?** (rollback in CI/CD)  
3. **What is the pipeline if merge-to-prod is too dangerous?** (staged delivery, not push-to-deploy)  
4. **How do environments stay reviewable instead of ClickOps folklore?** (basic infrastructure as code)

A **staging** environment is a **prod-shaped** place that runs the **same container digest** that will go to production—not “whatever we last `docker compose up`’d.” Staging must share the image digest, probe contract (`/healthz`, `/ready`), reachability to some LLM provider + vector/DB (or recorded fakes with contract tests), Week 16/17 golden-set smoke, and IAM-shaped identities. It may fake production PII, full multi-region capacity, rate-limit headroom, and customer tenancy at full scale. **Promotion rule:** CI **builds once**; staging and prod **pull the digest**. Rebuilding for prod is how “rollback” silently ships different Python wheels. Compose remains a **developer** inner loop (Week 3), not staging. Cloud Run maps the same idea to **revisions** and traffic splitting.

**Rollback** is re-deploying a known-good artifact or flipping traffic—not “git revert and hope CI rebuilds the same bits.” Mechanisms include `kubectl rollout undo`, redeploying a previous digest, blue-green / Cloud Run traffic flip to a previous revision, and canary abort (Argo Rollouts / Flagger / Cloud Deploy). **LLM wrinkle:** pods can be Ready while serving a wrong model ID or prompt version; HTTP canaries are necessary but not sufficient—staging golden-set evals (Week 17 judges and code evals) belong on the promote button.

Without SLIs you cannot write canary abort rules. Google’s SRE book maps onto LLM APIs: graceful degradation (weaker model / cache), load shedding, client exponential backoff with jitter, health checking, staged rollouts. Always-on frontier model with no timeout budget amplifies provider incidents into your SEV. Fail-open vs fail-closed is domain-specific (support-draft → fail-open; financial action agent → fail-closed + human escalation; Week 21 for idempotent side effects). Week 17 dashboards (error, latency, cost, calibrated quality) are the **abort criteria surface**; this week wires them to promote/abort.

**Do not start Week 19 (auth / identity / enterprise — OIDC/SAML, residency, multi-tenant RBAC) from this chapter** — this week ships **containerized LLM services**, **Kubernetes fluency (Pod / Service / Deployment / HPA)**, **staged CI/CD with rollback and canary**, and **basic Terraform IaC**. Workload identity, OIDC/SAML, and multi-tenant RBAC are next week. Cost **signals** on canary abort belong here; routing, semantic cache, and compression are Week 20. Idempotency appears only as a rollback/retry warning; messy ETL / dual-write is Week 21.

**What you ship this week**

```
git merge ──► CI: test + scan + build image
                    │
                    ▼
              registry digest (immutable)
                    │
         ┌──────────┼──────────┐
         ▼          ▼          ▼
        dev      staging      prod
     (namespace) (prod-like   (customers)
                  eval smoke)
                    │
              promote SAME digest
                    │
         rolling / canary / blue-green
                    │
         abort ──► rollback previous digest / revision
```

**Default path (synthesis)**

1. **Immutable images, mutable config.** Same digest across envs; secrets never in layers.  
2. **Readiness is a load-balancer contract.** Unready pods must not get LLM traffic during deploys.  
3. **HPA scales replicas, not provider quota.** CPU under-signals I/O-bound LLM APIs.  
4. **Promote digests; canary quality, not just HTTP 200.** A healthy pod can still ship a bad model ID.  
5. **Terraform owns the platform; GitOps owns the app.** Remote state + lock; per-env blast radius.  
6. **SRE habits are the abort criteria.** Timeouts, load shedding, error budgets decide when a canary dies.

Interview artifact = **a Deployment/Service/HPA YAML you can walk through** + **a one-page pipeline** (digest in, promote, rollback) + **a Terraform sketch** for the platform (not the prompt).

Read the concepts in order. Each section’s **Worked Example** and **Apply It** assume the same flagship service (working title: Deployment Copilot) moving from Week 17 instrumentation onto a real delivery path.

---

### Containerized deployment patterns for LLM services

* **Fundamentals:**  
  A **container** packages an application and its runtime dependencies into an immutable **OCI/Docker image**. A **containerized deployment** is: build that image once, store it in a registry by **digest**, inject **config and secrets at runtime**, and run **N replicas** behind a load balancer that respects **health**.

  For LLM apps the image usually holds the API process (FastAPI/uvicorn, Node, etc.) and model-client SDKs, plus OpenTelemetry instrumentation (Week 17 traces). It does **not** hold frontier model weights (provider or a separate GPU inference fleet) and does **not** hold API keys (secret store / K8s Secret / Cloud Run secret — identity hardening is Week 19).

  **Production loop**

  1. **Build** a slim runtime image (multi-stage: compile/deps → runtime). Official Docker: multiple `FROM`; `COPY --from=` leaves compilers out of the final image.  
  2. **Config via env**, secrets via a secret store. Never bake keys into layers (`.dockerignore` is not enough if `COPY . .` ran before you noticed).  
  3. **Health endpoints:**  
     - **Liveness** (`/healthz`): process is not deadlocked; failure → restart.  
     - **Readiness** (`/ready`): this replica may receive traffic (vector DB + LLM provider reachable, connection pool not exhausted).  
     - **Startup** (K8s/Cloud Run): slow model-client warmup without killing the container.  
     Do not use liveness for “provider down” or you restart the world.  
  4. **Stateless app tier** behind a load balancer; durable state in managed DB / object store / queue.  
  5. **Sidecars or gateways** for auth, rate limits, observability (OTEL collector, LiteLLM proxy, Envoy) — optional; do not require a mesh on week one.

  Compose is the **inner loop** (app + Redis + Postgres). Production almost always moves to an orchestrator (K8s, ECS, Cloud Run) once you need rolling deploys, autoscaling, and multi-replica HA.

  **Cloud Run container contract** (if you skip a cluster): listen on `0.0.0.0`, **not** `127.0.0.1`; honor the injected **`PORT`** (default **8080**); become ready within the platform’s startup window. Injected vars include `PORT`, `K_SERVICE`, `K_REVISION`, `K_CONFIGURATION`. Health checks: startup / liveness / readiness; HTTP `2XX`/`3XX` success; failed liveness → `SIGKILL` and in-flight requests terminate **503**. Docker `HEALTHCHECK` in the image is **not** the Cloud Run control plane. Default min instances is `0` (scale to zero → cold start on first LLM request); set min instances to keep warm replicas. Trap `SIGTERM` (~10s) for graceful drain. Cloud Run multiplexes many requests per instance; LLM streaming + high concurrency can pin memory and provider sockets—tune concurrency **down** for long generations.

  **GPU / self-hosted inference:** treat **API pods** and **GPU inference** as different images and different node pools. The API container stays slim and talks HTTP/gRPC to vLLM/TGI/a vendor.

  **Workers vs API:** long-running agent jobs should **not** share the request-serving Deployment if they need different HPA signals (queue depth vs RPS) or different disruption budgets. Pattern: API Deployment + **queue-consumer** Deployment (SQS/Pub/Sub). Scale workers with KEDA/HPA on queue length.

* **The Alternatives:**  

  | Pattern | When | Tradeoff |
  |---------|------|----------|
  | Single VM + Docker Compose | Prototype, internal tool | Manual HA; weak rollback; “staging” is the VM |
  | Managed containers (Cloud Run, App Runner, Azure Container Apps) | Stateless APIs, bursty traffic | Less control of networking/sidecars; GPU/custom CNI limited |
  | Kubernetes | Multi-service platforms, enterprise networking, custom autoscaling | Operational surface; interview-relevant fluency |
  | GPU node pools / dedicated inference | Self-hosted models | Cost, cold starts, driver/CUDA pinning |
  | Serverless functions only | Thin glue / webhooks | Timeout, payload, cold-start vs long LLM calls |
  | Distroless / alpine / chainguard | Smaller CVE surface | Harder `kubectl exec` debug during incidents |
  | Fat ubuntu image | Easy debug | Pull latency, CVE noise, root habits |

  For LLM **gateways** (LiteLLM, custom router): run as a Deployment (or Cloud Run service) with HPA on RPS/concurrency; keep embeddings/vector DBs as **managed** services when possible. **Sidecar vs in-process instrumentation:** sidecar OTEL collector isolates crash domains; in-process SDK is simpler on Cloud Run (sidecars supported but you must set startup order + probes).

  The syllabus selects **production containerization** (multi-stage, non-root, digest, probes) for Deployment Copilot whether the runtime is Cloud Run or Kubernetes. Compose stays local only.

* **Failure Modes:**  
  - “Works on my laptop” drift; unreproducible incidents; unsafe secret handling when images are not the ship artifact.  
  - Without **readiness** probes, load balancers send traffic to pods that cannot reach the model provider → cascading 5xx during deploys (the most common “we deployed and the world died” LLM outage).  
  - Without **immutability**, hotfixes on live boxes erase the audit trail and make rollback guesswork.  
  - Without honoring Cloud Run **`PORT` / `0.0.0.0`**, the revision never becomes ready; “service unavailable” for hours.  
  - Without **min instances** (or K8s `minReplicas`) on a latency-sensitive chat API, the first token after scale-to-zero includes image pull + Python import + TLS to the provider.  
  - Without a **separate worker** image/Deployment, a backlog of agent jobs starves HTTP readiness (shared thread pool / event loop).  
  - Keys baked into layers despite `.dockerignore` theater after an earlier `COPY . .`.

* **Average vs. Strong Engineer:**  
  **Average:** one Dockerfile, `docker push …:latest`, deploy to Cloud Run or a single Deployment, `/health` that returns 200 if the process started, env vars pasted in the console, root user.  
  **Strong:** multi-stage; distroless or pinned distro; **non-root** `USER`; SBOM + image scanning in CI; resource **requests/limits** from load tests (HPA needs CPU **requests**); separate images for **worker vs API**; OpenTelemetry baked in; config via ConfigMap/Secret with **checksum-triggered** rollouts; readiness checks **provider + DB**, not only `return {"ok": true}`; `preStop` sleep + graceful shutdown so **in-flight LLM streams** finish (`terminationGracePeriodSeconds` sized to max stream); registry **digest** in the manifest, tag only for humans; Cloud Run: explicit concurrency, min instances for chat, secrets from Secret Manager, startup probe if imports are slow.

* **Worked Example:**  
  Deployment Copilot leaves Compose-only shipping. CI builds a multi-stage image: builder installs deps with the lockfile; runtime copies the installed package, runs as non-root, and exposes `/healthz` (process alive) and `/ready` (vector DB ping + provider client can open a connection). Secrets come from Secret Manager / K8s Secret at runtime—never `ENV OPENAI_API_KEY=…` in the Dockerfile. The registry receives `registry.example.com/deployment-copilot@sha256:…`; humans may also see a `sha-abc123` tag. Cloud Run path: listen on `0.0.0.0:$PORT`, min instances ≥ 1 for the chat surface, concurrency tuned down for SSE streams. K8s path: same digest in the Deployment Pod template. Agent backlog work moves to a separate worker Deployment consuming a queue so HTTP readiness is not starved. Week 17 OTEL instrumentation stays in the image so staging and prod keep emitting the same traces and scores.

* **Apply It:**  
  1. Write a multi-stage Dockerfile; final stage non-root; no frontier weights or API keys in layers.  
  2. Add `/healthz` (liveness) and `/ready` (vector DB + LLM provider reachability).  
  3. Push by **digest**; ban `:latest` as the only promotion tag.  
  4. If Cloud Run: honor `PORT` / `0.0.0.0`; set min instances for chat; tune concurrency for streams; secrets from Secret Manager.  
  5. Split API vs queue-consumer images/Deployments when HPA signals differ.  
  6. Size graceful shutdown (`preStop` / `SIGTERM` / grace period) to max in-flight generation time.

---

### Kubernetes fluency (Pods, Services, Deployments, HPA)

* **Fundamentals:**  
  Kubernetes fluency for this curriculum is **four objects** plus how they fail together. You do **not** need custom controllers, cluster federation, or CNI packet debugging.

  **Pod** — smallest schedulable unit: one or more containers sharing network namespace (localhost) and volumes. **Ephemeral.** Never treat a Pod IP as durable. Multi-container Pods are for sidecars (OTEL, service mesh) that must die/live with the app — not for “API + Redis in one Pod” in production.

  **Deployment** — desired replica count + Pod **template**. Owns **ReplicaSets**; implements **rolling updates** and **rollbacks** via revision history. Changing the template (image digest, env checksum) creates a new ReplicaSet; the Deployment controller ramps new Pods and drains old ones per `strategy.rollingUpdate` (`maxUnavailable`, `maxSurge`). **GitOps note:** if you set `spec.replicas` in Git **and** attach an HPA, the two fight. Strong practice: let HPA own replicas; omit or ignore `replicas` in the GitOps app of record.

  **Service** — stable virtual IP / DNS name in front of Pods selected by **labels**. Types: **ClusterIP** (default; in-cluster LLM API / gateway), **NodePort** (rare in cloud; debugging), **LoadBalancer** (cloud LB → nodes → Pods), **ExternalName** (DNS alias). HTTP APIs usually: **Service → Ingress or Gateway API**. Canary **percentage splits** need Ingress weights, Gateway API `HTTPRoute` weights, or a mesh — a ClusterIP Service alone is **equal-cost** across Ready endpoints. Traffic goes to Pods that pass **readiness**; mis-set probes empty the Endpoints list → 5xx at the LB.

  **HorizontalPodAutoscaler (HPA)** — controller that adjusts a workload’s `replicas` (Deployment, StatefulSet, anything with a **scale subresource**) from metrics. **Not** for DaemonSets. API: **`autoscaling/v2`** (CPU, memory, custom, external, multiple metrics). Control loop: kube-controller-manager `--horizontal-pod-autoscaler-sync-period` default **~15s**. Formula (docs):

  `desiredReplicas = ceil(currentReplicas × currentMetricValue / desiredMetricValue)`

  Skip if ratio is within tolerance (default **0.1**). Multiple metrics: take the **max** proposed replica count (capped by `maxReplicas`). CPU utilization is **percent of requests**. **If any container lacks a CPU request, CPU utilization is undefined and HPA will not act on that metric.** Metrics path: `metrics.k8s.io` (usually Metrics Server), `custom.metrics.k8s.io` (e.g. prometheus-adapter), `external.metrics.k8s.io`. **Behavior (`v2`):** `scaleUp` / `scaleDown` policies + `stabilizationWindowSeconds`. Defaults: scale-up aggressive (0s stabilization), scale-down **300s** lookback — pick the safest (highest) recommendation in the window for down (stops **flapping**). `minReplicas` defaults to 1; 0 requires scale-to-zero feature gates and object/external metrics. Production LLM APIs almost never want `minReplicas: 0` without an explicit cold-start budget.

  **Mental model for an LLM API**

  ```
  Ingress / Gateway API  →  Service  →  Deployment (API pods)
                                           ↑
                                          HPA (CPU *or* custom RPS / inflight / latency)
  Workers: Deployment consuming SQS/PubSub
           HPA or KEDA on queue depth
  ```

  **Replica count ≠ capacity:** provider rate limits, connection pools, and GPU inference queues saturate **before** CPU.

  **Related objects you must recognize (not master):** **PodDisruptionBudget (PDB)** — voluntary evictions leave `minAvailable` Pods; **topology spread** — schedule across AZs; **`preStop` + `terminationGracePeriodSeconds`** — finish SSE/WebSocket generations; **VPA** — resizes requests/limits; disruptive; do not dual-wield VPA+HPA on the **same** CPU metric casually; **KEDA** — ScaledObject that **manages an HPA** for event sources (queue, cron); scale-to-zero for workers. Cluster Autoscaler **node** scale-down vs HPA **pod** scale are different loops.

* **The Alternatives:**  

  | Scaling lever | Pros | Cons |
  |---------------|------|------|
  | HPA on CPU | Built-in; Metrics Server | LLM pods often **I/O-bound** waiting on provider; CPU under-signals load |
  | HPA on memory | Easy to set | Lagging; OOM loops get **multiplied**; caches look like “need more pods” |
  | HPA on custom RPS / concurrency / inflight | Matches real demand | prometheus-adapter (or equivalent) ops |
  | HPA on queue depth (workers) | Correct for async agents | Scale-up lag; need `maxReplicas` ≤ downstream quota |
  | VPA | Right-sizes CPU/mem | Restarts; fights HPA if both on CPU |
  | KEDA | Event-driven; scale to zero | Extra CRDs/operators |
  | Cluster Autoscaler / Karpenter | Nodes appear when pods Pending | Minutes of scheduling delay; not a substitute for `minReplicas` headroom |

  | Traffic object | Pros | Cons |
  |----------------|------|------|
  | ClusterIP only | Simple | No L7 canary |
  | Ingress | Ubiquitous | Annotation soup; vendor-specific canary |
  | Gateway API | Portable canary weights (Cloud Deploy path) | Newer; implementation-dependent |

  The syllabus requires you to **read and explain** Deployment + ClusterIP Service + HPA, and to propose **one non-CPU metric** when the API is provider-bound.

* **Failure Modes:**  
  - Without **Services**, clients break whenever Pods reschedule.  
  - Without **Deployments**, you hand-edit Pods and lose rolling updates/rollback.  
  - Without **HPA** (or Cloud Run autoscaling), spikes → timeout storms and retry amplification; valleys → wasted spend.  
  - Without CPU **requests**, “HPA on 70% CPU” is a no-op—and you learn this during a launch.  
  - Without **readiness**, a rolling update sends traffic to pods still establishing TLS to OpenAI/Anthropic.  
  - Without PDB + topology spread, a node upgrade or AZ blip takes the **only** Ready replica of a `minReplicas: 1` chat API.  
  - Without graceful shutdown, rolling updates **cut streams**; users see truncated answers and retry → more load.  
  - Git `replicas` fighting HPA; CPU HPA under-signaling I/O-bound LLM pods while provider 429s explode.

* **Average vs. Strong Engineer:**  
  **Average:** Deployment + ClusterIP + Ingress; HPA `averageUtilization: 70` CPU; `minReplicas: 1`; no PDB; `replicas` also set in Helm.  
  **Strong:** requests/limits from profiling; watch `container_cpu_cfs_throttled_seconds_total` if limits are tight; PDBs for voluntary evictions; separate HPAs for **API vs workers**; custom metrics: inflight requests, p95, queue depth; **`maxReplicas` capped by provider RPM**; `behavior.scaleDown.stabilizationWindowSeconds` 180–300s; scale-up may want a **short** window if pods start slowly; topology spread across AZs; `preStop` + grace ≥ max generation time; `kubectl describe hpa` / events as the first debug (metrics-server missing, targets unknown); labels that Week 17 dashboards and Week 20 cost views will use (`app`, `version`, `env`). Enough analysis data points matter for HPA the same way they matter for canary (do not expect a single 15s CPU scrape to save a 2-minute prompt).

* **Worked Example:**  
  You walk an interviewer through Deployment Copilot’s teaching YAML (not a blind cluster apply):

  ```yaml
  apiVersion: apps/v1
  kind: Deployment
  metadata:
    name: llm-api
  spec:
    selector:
      matchLabels: { app: llm-api }
    template:
      metadata:
        labels: { app: llm-api }
      spec:
        terminationGracePeriodSeconds: 120
        containers:
          - name: api
            image: registry.example.com/llm-api@sha256:abc…
            ports: [{ containerPort: 8080 }]
            resources:
              requests: { cpu: "500m", memory: "1Gi" }
              limits: { memory: "1Gi" }
            readinessProbe:
              httpGet: { path: /ready, port: 8080 }
              periodSeconds: 5
            livenessProbe:
              httpGet: { path: /healthz, port: 8080 }
              periodSeconds: 15
            lifecycle:
              preStop:
                exec: { command: ["sleep", "10"] }
  ---
  apiVersion: v1
  kind: Service
  metadata: { name: llm-api }
  spec:
    selector: { app: llm-api }
    ports: [{ port: 80, targetPort: 8080 }]
  ---
  apiVersion: autoscaling/v2
  kind: HorizontalPodAutoscaler
  metadata: { name: llm-api }
  spec:
    scaleTargetRef:
      apiVersion: apps/v1
      kind: Deployment
      name: llm-api
    minReplicas: 3
    maxReplicas: 20
    metrics:
      - type: Resource
        resource:
          name: cpu
          target: { type: Utilization, averageUtilization: 70 }
    behavior:
      scaleDown:
        stabilizationWindowSeconds: 300
  ```

  Because the API is provider-bound, you replace (or add) a custom/external metric for **inflight requests or RPS**, and set `maxReplicas` from provider RPM—not from a CPU guess. A failed rollout: `kubectl rollout status` stuck; `kubectl get rs` shows the new ReplicaSet at 0 Ready while old Pods remain; `kubectl describe` / events show ImagePullBackOff or readiness failing on provider TLS. Rollback: `kubectl rollout undo deployment/llm-api` (or re-apply the previous digest). Workers get a separate Deployment + HPA/KEDA on queue depth.

* **Apply It:**  
  1. Author Deployment + ClusterIP Service + `autoscaling/v2` HPA for the API; walk a failed rollout and ReplicaSet history.  
  2. Set CPU **requests** before trusting any CPU utilization target.  
  3. If the API is provider-bound, propose **one** non-CPU metric (inflight / RPS / queue depth for workers).  
  4. Cap `maxReplicas` by provider quota; separate API vs worker HPAs.  
  5. Add PDB, topology spread, and `preStop` + grace sized to max stream.  
  6. Let HPA own replicas in GitOps; do not fight it with a pinned `spec.replicas`.

---

### CI/CD beyond push-to-deploy (staged envs, rollback, canary / blue-green)

* **Fundamentals:**  
  **Push-to-deploy** (merge → production) is a valid inner loop for toys. Production AI systems need a **delivery pipeline** with **gates**, **immutable artifacts**, and a **rehearsed undo**.

  **Pipeline stages**

  1. **CI** — lint, unit/contract tests, build image, **scan**, push **digest-tagged** image (`sha-abc123`, not only `:latest`). SBOM optional but strong.  
  2. **Staged environments** — `dev` → `staging` (prod-like deps / fakes) → `prod`. Promote the **same image digest**; never rebuild for prod.  
  3. **Deploy strategies** (data plane):

  | Strategy | Mechanism |
  |----------|-----------|
  | **Rolling update** | K8s Deployment default: replace Pods with `maxUnavailable` / `maxSurge`. Rollback = previous ReplicaSet. |
  | **Blue-green** | Two full environments; flip Service/Ingress/Gateway or Cloud Run traffic; instant undo by flipping back. Needs ~2× capacity during cutover. |
  | **Canary** | Small % of traffic (or users) on the new version; advance on **metrics**; else abort. Needs weights (Ingress/Gateway/mesh) **or** replica-ratio hacks (weaker). |

  4. **Rollback** — redeploy previous known-good digest; `kubectl rollout undo`; flip traffic; progressive-delivery controller abort. Must be **rehearsed**.  
  5. **Release analysis** — error rate, p95 / TTFT, **LLM eval canary scores**, cost-per-request — not just “pods Ready.”

  **Cloud Deploy canary** (GKE / Cloud Run): progressive traffic splitting with optional **automated analysis** before advancing phases. GKE can use **service networking** (pod counts ≈ traffic) or **Gateway API** (true percentage weights). Configure `strategy.canary` with percentage phases (e.g. 10 / 50 / 80 then full). Cloud Run canaries shift **revision traffic** without you managing ReplicaSets.

  **Argo Rollouts vs Flagger** (K8s progressive delivery): Argo Rollouts replaces Deployment with a `Rollout` CR and uses `AnalysisTemplate` (Prometheus, jobs, web metrics, …); Flagger watches a normal **Deployment**, uses interval/threshold/metric providers, and creates primary+canary services. Hannah Troisi (CNCF/KubeCon): canary is **art plus analysis** — how much traffic, which metrics, how long. Adobe: scrape interval vs canary duration — enough points for analysis. Monzo (KubeCon): **2100+** services; invested in Rollouts so **automated rollback is the default**, not heroic canarying.

  **Feature flags vs deploys:** flags **decouple deploy from release**. For LLM: route **model ID / prompt version** with a flag **and** still canary the **binary**. Flag-only changes still need abort metrics (quality + cost). Flag debt is real.

  **GitHub environments:** `staging` / `prod` as GitHub **environments** — required reviewers, wait timers, environment secrets, deployment branches. **OIDC** to cloud so CI has no long-lived keys (Week 19 deep-dive; strong practice here).

  **LLM-specific gates:** a Ready pod can still ship a **bad prompt or model ID**. Include eval gates on staging (Week 16/17 golden-set smoke — code evals in CI, judges sampled); shadow / canary eval in prod (sample traces, not 100% GPT-4 judges); cost-per-request abort (Week 20 will deepen routing/cache on the same labels); streaming-aware SLIs — error rate may stay green until **first token**; abort on TTFT / timeout rate, not only HTTP 500. Google SRE workbook canarying of data pipelines is the same progressive-risk idea as traffic canaries. The Week 17 dashboard tiles (errors, p95, cost, calibrated quality) are what the canary controller should read.

* **The Alternatives:**  

  | Strategy | Blast radius | Cost / complexity | Best for |
  |----------|--------------|-------------------|----------|
  | Rolling | Medium (mixed versions) | Low | Backward-compatible APIs |
  | Blue-green | Low (flip) | 2× capacity during cutover | Schema-compatible releases needing fast undo |
  | Canary (% traffic) | Lowest | Mesh/Ingress/Gateway + metrics | High-risk model/prompt/gateway changes |
  | Canary (% pods only) | Misleading | Easy | **Avoid** if clients are sticky or load is uneven |
  | Feature flags | Decouples release | Flag debt; still need analysis | Prompt/model routing toggles |
  | Push-to-prod | 100% immediately | Lowest | Demos, internal tools with two users |

  | Analysis | Pros | Cons |
  |----------|------|------|
  | HTTP success + p95 only | Cheap | Misses quality/cost disasters |
  | + golden eval smoke | Catches prompt/model ID | Staging traffic ≠ prod mix |
  | + sampled prod judges | Real distribution | Lag; judge cost (Week 17) |
  | Automated Cloud Deploy / Rollouts analysis | Hands off | Bad SLIs → false abort or false promote |

  Framing alternatives from the week overview: **staging + digest promotion + rehearsed rollback + Terraform for platform** bounds blast radius and is FDE-interview-shaped (more YAML; staging cost; needs Week 16/17 eval suite). Merge-to-prod rolling only is fast and makes every bad prompt/model a customer incident. Staging that **rebuilds** images feels like a gate but rollback bits ≠ prod bits.

* **Failure Modes:**  
  - Without **staged promotion**, every bad merge is a customer incident.  
  - Without **digest immutability**, “rollback” rebuilds different bits (`:latest` moved; lockfile changed).  
  - Without canary/blue-green for **high-blast** changes, one bad tokenizer/prompt/version burns the monthly LLM budget or serves **wrong tenant data**.  
  - Without **automated abort criteria**, humans notice too late (Monzo: do not rely on “engineers will watch the dashboard” at 100 deploys/day).  
  - Without **streaming-aware** SLIs, canaries promote a version that hangs on first token.  
  - Without **rehearsed rollback**, the undo path is a Slack thread; `kubectl rollout undo` is first used during a SEV; blue-green “instant undo” fails because green was never kept warm.  
  - Scan/SBOM never run; secrets leak into layers; canary never has abort metrics until the monthly LLM budget is gone.

* **Average vs. Strong Engineer:**  
  **Average:** GitHub Actions → build → deploy staging → manual approve → prod **rolling** update; `:latest`; no eval gate; rollback undocumented.  
  **Strong:** OIDC to cloud; environment protection rules on `prod`; canary **5% → 25% → 100%** (or Cloud Deploy percentages) with **automated** metric gates (error, latency, eval, cost); separate pipelines: **infra** (Terraform plan/apply) vs **app** (image + GitOps); progressive delivery (Argo Rollouts / Flagger / Cloud Deploy); post-deploy runbooks; LLM regression suite on staging with production-like prompts; Monzo-style **automated rollback defaults** even when canary is “light”; Adobe-style analysis duration matched to scrape interval and traffic; SRE error budgets decide whether you **slow the pipeline** after a quality burn. Cloud Run teams: traffic tags / revisions instead of Rollouts CRDs — same **percentage + analysis** idea. Digest tags + registry immutability; staging golden-set + contract tests against provider fakes **and** a live smoke.

* **Worked Example:**  
  Deployment Copilot’s one-page pipeline: CI lint/test/scan → build once → push `deployment-copilot@sha256:…`. Promote that digest to `dev`, then `staging` (GitHub environment with reviewers). Staging runs Week 16/17 golden-set smoke (code evals plus sampled calibrated judges) plus a few live traces; only then promote the **same** digest to `prod`. Prod uses Cloud Deploy (or Argo Rollouts) canary 5% → 25% → 100% with automated abort on error rate, p95/TTFT, sampled eval score, and cost-per-request spike. A bad model ID that still returns HTTP 200 fails the eval gate before full traffic. Rollback rehearsal (scheduled): `kubectl rollout undo` **or** flip Cloud Run traffic to the previous revision **or** redeploy the pinned previous digest from the release UI—bits already in the registry, no rebuild.

* **Apply It:**  
  1. Build one digest-tagged image in CI; promote `dev` → `staging` → `prod` without rebuild.  
  2. Attach GitHub environment protection rules to `staging` / `prod`; prefer OIDC over long-lived CI keys.  
  3. Gate staging promote on golden-set smoke (Week 16/17); gate prod advance on error / latency / eval / cost.  
  4. Choose rolling, blue-green, or canary; for high-blast model/prompt changes prefer weighted canary (not pod-count-only hacks).  
  5. Rehearse rollback (undo / traffic flip / previous digest) on a schedule; document the runbook.  
  6. Keep feature flags for model/prompt routing, but still canary the binary and attach abort metrics to flag flips.

---

### Infrastructure as Code with Terraform

* **Fundamentals:**  
  **Terraform** (HashiCorp) declares cloud resources in **HCL**. **State** maps configuration addresses → real object IDs. The core loop is `terraform init` → `plan` → `apply`.

  For AI platforms, Terraform typically owns: network (VPC, subnets, private endpoints to model APIs); GKE/EKS/AKS **or** Cloud Run / ECS; IAM roles for workloads (IRSA / Workload Identity — **wire-up this week**; protocol deep-dive Week 19); secrets manager **hooks**, KMS keys; object storage for corpora and artifacts; observability sinks, queues, databases (or modules wrapping them).

  **Split of record:** Terraform = **platform**. Helm/Kustomize/Argo CD = **app** (Deployments, HPA thresholds, prompt ConfigMaps). Crossing the boundary casually (Terraform `kubernetes_deployment`) creates two sources of truth.

  **State is the contract:** local state is for tutorials; teams use **remote state**. **Locking** prevents two applies from corrupting the mapping. **GCS backend:** state object in a pre-existing bucket; locking supported; enable **object versioning** for recovery. **S3 backend:** state key in a bucket; enable native locking with `use_lockfile = true` (DynamoDB locking **deprecated**, both can coexist during migration). State contains **secrets** (sometimes)—restrict read IAM; encrypt; do not commit `terraform.tfstate`.

  **Workspaces vs directories:** named workspaces share code with different state keys. Stronger blast-radius control: **separate root modules / separate state** per env (`staging`, `prod`) — a prod apply cannot see staging resources. HashiCorp tutorials still show workspaces; production FDE practice usually **folders + separate backends**.

  **Plan is the review artifact:** CI on PR: `fmt` + `init` + `validate` + `plan`. Humans review the plan (especially IAM, buckets, security groups). Apply **only** from protected `main` with OIDC (or a tightly gated runner). Detect-changed-roots so you do not apply every stack every time.

  **Modules and pinning:** thin wrappers around **official providers**; pin **provider** and **module** versions. Do not “latest” the Google provider on Friday.

  **GKE upgrades as infra-level progressive delivery:** Terraform Google provider `google_container_cluster` documents node-pool upgrade strategies including **`BLUE_GREEN`** with soak duration — the cluster itself can roll like an app. Pair with **PDBs** so soak does not evict the last LLM replica.

  **OpenTofu** is a Terraform-compatible fork after HashiCorp license changes. Same HCL mental model; org policy/licensing is an **open question**, not a syllabus pick-one.

  **ClickOps and import:** existing console resources can be `terraform import`ed **deliberately**. Accidental import of half a VPC is how state lies. Drift detection (plan in CI on a schedule) finds ClickOps.

* **The Alternatives:**  

  | Tool | Strength | Tradeoff |
  |------|----------|----------|
  | Terraform / OpenTofu | Multi-cloud; huge provider ecosystem | State drift; blast radius of apply; license fork politics |
  | Pulumi | General-purpose languages | Same state class of problems; different DX |
  | CloudFormation / CDK | AWS-native | AWS lock-in |
  | Crossplane / Config Connector | K8s-native infra | Requires a cluster **first** (chicken/egg) |
  | ClickOps | Fast start | No review; no drift detection; unreproducible staging |
  | Terraform `kubernetes_*` for apps | One tool | Fights GitOps; slow apply; state owns Pods |
  | Terragrunt / wrappers | DRY roots | Extra abstraction interviews may not assume |

  | Env isolation pattern | Blast radius | Footgun |
  |-----------------------|--------------|---------|
  | Separate accounts/projects + separate state | Smallest | More boilerplate |
  | One project, folders `envs/staging\|prod` | Small if backends differ | Wrong `-chdir` |
  | One state, `count`/`for_each` both envs | Huge | One apply touches prod |
  | Workspaces `default`/`prod` | Easy | Easy to apply the wrong workspace |

  The syllabus selects **basic Terraform** for the platform (VPC/cluster-or-Cloud-Run, IAM skeleton, remote state + lock, per-env state) with plan-on-PR / apply-on-main. App Deployments stay GitOps.

* **Failure Modes:**  
  - Without IaC, environments **diverge** (“staging isn’t prod”), security groups rot, and disaster recovery is folklore.  
  - Without **plan review**, a one-line IAM change can expose buckets (Week 19 makes this worse if identity is also ClickOps).  
  - Without **remote state locking**, two engineers corrupt infra simultaneously.  
  - Without **per-env state**, a “quick staging fix” recreates the prod cluster.  
  - Without Terraform (or equivalent) for **private control plane / private endpoints**, LLM API keys and corpora traverse the public internet by accident.  
  - Without **version pins**, a provider upgrade rewrites GKE in a Monday plan you did not intend.  
  - ClickOps cluster + “we’ll Terraform later” → drift; unreproducible staging; no plan review.

* **Average vs. Strong Engineer:**  
  **Average:** one monorepo `infra/` with workspaces; `terraform apply` from a laptop; app Deployments also in Terraform; state in the same bucket without versioning; no policy-as-code; Terraform applied from a laptop while staging is a shared Compose file.  
  **Strong:** CI `plan` on PR; apply from protected main + OIDC; policy-as-code (OPA/Sentinel) for public buckets / open SG; drift detection job; import existing resources **on purpose**; GKE/EKS modules with **private** control plane; blue-green **node pool** upgrades via provider settings; separate pipelines from app images; bootstrap problem: state bucket created once (script or tiny stack), then everything else uses it; GitOps (Argo CD) **installed by Terraform** (Helm provider) then left to reconcile apps — Terraform does not own the LLM Deployment thereafter. AWS guidance: remote S3 state + locking; prefer native S3 lock over DynamoDB going forward.

* **Worked Example:**  
  Deployment Copilot’s Terraform sketch (teaching, not copy-paste prod): remote GCS backend with locking and object versioning; separate roots `envs/staging` and `envs/prod` (separate state prefixes) so an apply cannot recreate prod by accident. Platform resources: VPC, private endpoints toward the model API path, either `google_cloud_run_v2_service` **or** a GKE module, IAM skeleton for the workload (static keys deferred to Week 19), Secret Manager hooks, artifact/corpus buckets. Provider and module versions pinned. PR CI runs `fmt` / `validate` / `plan`; humans review IAM and networking diffs; apply only from protected `main`. The app image digest is **not** hardcoded in Terraform—CI writes the digest into the GitOps repo (Helm/Kustomize/Argo CD). Node-pool upgrades use `BLUE_GREEN` soak on `google_container_cluster`, paired with PDBs so soak does not evict the last chat replica. Argo CD itself may be installed once via Terraform’s Helm provider, then left alone.

* **Apply It:**  
  1. Declare platform (VPC, cluster or Cloud Run, IAM skeleton, buckets/queues) in HCL; pin provider/module versions.  
  2. Use remote state with locking (GCS or S3 `use_lockfile`); enable versioning on the state bucket.  
  3. Separate state (and preferably roots) for `staging` vs `prod`.  
  4. PR: `fmt` + `validate` + `plan`; apply only from protected main (OIDC).  
  5. Keep app Deployments/HPA/prompt ConfigMaps in GitOps; do not make Terraform the second owner of Pods.  
  6. Prefer deliberate `import` + scheduled drift plans over ClickOps; consider `BLUE_GREEN` node-pool upgrades with PDBs.

---

## Week 18 build checklist (end-to-end)

Use this as the chapter’s capstone sequence; every concept above maps here.

1. **Containerize:** Multi-stage, non-root image; env/secrets at runtime; `/healthz` + `/ready` (provider + DB); digest tags; no weights/keys in layers; Cloud Run contract if applicable.  
2. **Kubernetes fluency:** Deployment + ClusterIP Service + HPA YAML you can explain; failed rollout / ReplicaSet history; one non-CPU HPA metric if provider-bound; PDB / `preStop` / grace for streams.  
3. **Staged pipeline:** CI builds one digest; promote `dev` → `staging` → `prod`; staging golden-set smoke; prod rolling **or** canary with abort on error / p95 / eval / cost; rehearse rollback.  
4. **Basic Terraform:** VPC/cluster-or-Cloud-Run + IAM skeleton; remote state + lock; separate staging/prod state; plan on PR; apply from protected main; platform ≠ app.  
5. **Interview artifact:** Walkable Deployment/Service/HPA YAML + one-page pipeline (digest → promote → rollback) + Terraform sketch for the platform (not the prompt).

When those steps are true, Week 18 is done in the syllabus sense: the Week 17–instrumented service rides an immutable digest through staging and a rehearsed undo path, on platform declared in Terraform—not ClickOps folklore.

---

## Looking ahead

Week 19 is **auth, identity, and enterprise AI constraints**. The containerized, digest-promoted service from this week still typically starts with `OPENAI_API_KEY=` in a secret store — that key is a **provider credential for the platform**, not a **user session**. Next week you stop treating a secret env var as “login”: **OIDC** for human login (Authorization Code + PKCE; validate `iss`/`aud`/`exp`/JWKS); **SAML** for legacy enterprise SSO; machines via scoped API keys, service accounts / workload identity, and OBO — not the provider key in the client; **data residency** as a router constraint across prompt, embed, index, log, and tool; **multi-tenant RBAC / isolation** enforced in every store. Do **not** start Week 19 by throwing away this week’s digests, probes, or staged pipeline — you harden **who** may call the same delivery path and **where** payloads may live. Cost routing and semantic cache deepen in Week 20; this week only needs cost as a canary abort signal.

---

## Compilation notes

- All concept sections above are grounded in `research/phase-5/week-18-deployment-infra/` (`00`–`04`, README).  
- No section required inventing answers beyond the research corpus; overview staging/rollback/SRE framing is folded into chapter framing and the CI/CD concept.  
- Research Open Questions remain open and were **not** resolved with invented answers: prompt/model config on the same canary vs faster flag pipeline; how prod-like staging LLM spend must be; generative-quality error budgets as ship/no-ship; when Cloud Run revisions suffice vs K8s interview fluency; cost anomalies paging like latency; distroless vs distro for 3am debug; self-hosted GPU vs managed APIs; always-separate worker Deployments; Cloud Run concurrency vs one-generation-per-instance for SSE; LiteLLM gateway as library vs sidecar for key rotation (Week 19); readiness on connection budget / inflight; worker scale-to-zero vs `minReplicas: 1`; Gateway API vs Ingress for canary weights; HPA on p95 death-spiral risk; `maxReplicas` as platform policy (OPA) tied to spend; Terraform vs Helm boundary for model names / HPA thresholds; OpenTofu vs Terraform licensing in 2026; terraforming vector DB indexes vs app migrations; Cloud Run in Terraform vs `gcloud`/skaffold; policy-as-code depth for FDE interviews; whether Workload Identity belongs in this week’s module vs Week 19.  
- Where research does not prescribe Deployment Copilot–specific defaults for those open questions, treat them as deferred—not as silent product decisions. `[NEEDS MORE RESEARCH]` is not required for any of the four syllabus concepts’ six fields as compiled; open questions are listed rather than filled.  
- Outside URLs from research are cited by concept in the notes; operational detail was inlined from the notes.  
- Week 19 auth/identity/enterprise (OIDC/SAML, residency, multi-tenant RBAC), Week 20 full cost-engineering (routing/cache), and Week 21 idempotent side effects are explicitly deferred.  
- Editorial pass: Prerequisites Recap bridges Week 17 (judges, calibration, Langfuse/Phoenix, dashboards); Looking ahead bridges Week 19; no new technical claims beyond research.
