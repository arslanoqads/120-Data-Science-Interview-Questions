# Week 18 — Deployment Infrastructure (Containers, K8s Fluency, CI/CD, Terraform)

> Phase 5 · Production, Cost, and Systems  
> Raw source material for FDE gate. Legal/public sources only.

---

## Concept: Containerized deployment patterns for LLM services

### Fundamentals
A container packages an application and its runtime dependencies into an immutable image (typically OCI/Docker). For LLM apps, the container usually holds: the API process (FastAPI/uvicorn, Node, etc.), model-client SDKs, and config injected at runtime via env vars / secrets — **not** frontier model weights (those live at the provider or a separate GPU inference fleet).

Core pattern for a production AI service:

1. **Build** a slim runtime image (multi-stage: compile/deps → runtime).
2. **Config via env**, secrets via secret store / K8s Secrets — never bake keys into the image.
3. **Health endpoints**: liveness (`/healthz`) and readiness (`/ready` — e.g., can reach vector DB + LLM provider).
4. **Stateless app tier** behind a load balancer; durable state in managed DB / object store / queue.
5. **Sidecars or gateways** for auth, rate limits, observability (OpenTelemetry collector, LiteLLM proxy, Envoy).

Compose is fine for local multi-service (app + Redis + Postgres). Production almost always moves to an orchestrator (K8s, ECS, Cloud Run) once you need rolling deploys, autoscaling, and multi-replica HA.

### Alternatives & Tradeoffs
| Pattern | When | Tradeoff |
|---------|------|----------|
| Single VM + Docker Compose | Prototype, internal tool | Manual HA, weak rollback |
| Managed containers (Cloud Run, App Runner, Azure Container Apps) | Stateless APIs, bursty traffic | Less control of networking/sidecars |
| Kubernetes | Multi-service platforms, enterprise networking, custom autoscaling | Operational surface area |
| GPU node pools / dedicated inference | Self-hosted models | Cost, cold starts, driver/CUDA pinning |
| Serverless functions only | Thin glue / webhooks | Timeout, payload, cold-start limits vs long LLM calls |

For LLM gateways specifically: run the gateway (LiteLLM, custom router) as a Deployment with HPA on RPS/latency; keep embeddings/vector DBs as managed services when possible.

### Necessity
Without containerization you get “works on my laptop” drift, unreproducible incidents, and unsafe secret handling. Without readiness probes, load balancers send traffic to pods that cannot reach the model provider → cascading 5xx during deploys. Without immutability, hotfixes on live boxes erase the audit trail and make rollback guesswork.

### Industry Practice
**Common:** Dockerfile + push to registry + deploy to one env.  
**Strong:** multi-stage builds, distroless/alpine bases, SBOM + image scanning in CI, non-root user, resource requests/limits set from load tests, separate images for worker vs API, OpenTelemetry baked in, config via ConfigMap/Secret with checksum-triggered rollouts.

### Concrete Scenario
Kubernetes official concept docs describe Deployments as the declarative way to roll out Pods and manage ReplicaSets — the backbone of containerized LLM API rollouts:  
https://kubernetes.io/docs/concepts/workloads/controllers/deployment/

Docker multi-stage build docs (official):  
https://docs.docker.com/build/building/multi-stage/

### Open Questions
- Should LLM *workers* (long-running agent jobs) share the API Deployment or use a separate queue-consumer Deployment?
- When does self-hosted inference justify GPU K8s vs staying on managed APIs?
- Distroless vs distro images for CVE response speed vs debug-ability in incidents.

### Sources
- https://kubernetes.io/docs/concepts/workloads/controllers/deployment/
- https://docs.docker.com/build/building/multi-stage/
- https://docs.docker.com/compose/
- https://sre.google/sre-book/service-best-practices/

---

## Concept: Kubernetes fluency — Pods, Services, Deployments, HPA

### Fundamentals
Kubernetes objects FDEs must be fluent in (not full SRE depth):

**Pod** — smallest schedulable unit; one or more containers sharing network namespace. Ephemeral. Never treat a Pod IP as durable.

**Deployment** — desired replica count + Pod template. Owns ReplicaSets; implements rolling updates and rollbacks via revision history.

**Service** — stable virtual IP / DNS name in front of Pods selected by labels. Types: ClusterIP (internal), NodePort, LoadBalancer, ExternalName. For HTTP APIs, often Service → Ingress / Gateway API.

**HorizontalPodAutoscaler (HPA)** — controller that adjusts Deployment/StatefulSet `replicas` based on metrics (CPU, memory, custom, external). Uses `autoscaling/v2`. Formula conceptually: desiredReplicas ≈ currentReplicas × (currentMetric / desiredMetric). Stabilization windows prevent flapping.

Mental model for an LLM API:

```
Ingress/Gateway → Service → Deployment (API pods)
                              ↑
                             HPA (CPU or custom RPS/queue depth)
Workers: Deployment consuming from SQS/PubSub (scale on queue depth)
```

### Alternatives & Tradeoffs
| Scaling lever | Pros | Cons |
|---------------|------|------|
| HPA on CPU | Simple, built-in | LLM pods are often I/O-bound waiting on provider; CPU under-signals load |
| HPA on custom RPS / concurrency | Matches real demand | Needs metrics-server + adapter (e.g. prometheus-adapter) |
| HPA on queue depth (workers) | Correct for async agents | Lag between enqueue and scale-up |
| Vertical Pod Autoscaler | Right-sizes CPU/mem | Disruptive restarts; less common for latency-sensitive APIs |
| KEDA | Event-driven scale to zero | Extra CRDs/operators |

Replica count ≠ capacity for LLM apps: provider rate limits and connection pools often saturate before CPU.

### Necessity
Without Services, clients break whenever Pods reschedule. Without Deployments, you hand-edit Pods and lose rolling updates/rollback. Without HPA (or equivalent), traffic spikes → timeout storms and retry amplification; valleys → wasted spend. Mis-set readiness probes cause half the fleet to be removed during a dependency blip → worse outage.

### Industry Practice
**Common:** Deployment + ClusterIP Service + Ingress; HPA on 70% CPU.  
**Strong:** requests/limits from profiling; PDBs (PodDisruptionBudgets) for voluntary evictions; separate HPAs for API vs workers; custom metrics (inflight requests, p95 latency, queue depth); `behavior.scaleDown` stabilization 3–5 min; topology spread across AZs; `preStop` sleep + graceful shutdown so in-flight LLM streams finish.

### Concrete Scenario
Official HPA concept page and walkthrough — scale a Deployment between min/max replicas targeting average CPU (or custom metrics):  
https://kubernetes.io/docs/concepts/workloads/autoscaling/horizontal-pod-autoscale/  
https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale-walkthrough/

KubeCon talks regularly cover production HPA pitfalls (metrics lag, CPU for I/O-bound services). Example channel: CNCF YouTube — search “KubeCon Horizontal Pod Autoscaler”:  
https://www.youtube.com/@cncf

### Open Questions
- For streaming LLM responses, should readiness consider “connection budget” rather than CPU?
- Scale-to-zero for agent workers: worth the cold-start vs always-on minReplicas=1?
- When to prefer Gateway API over Ingress for canary weight splitting.

### Sources
- https://kubernetes.io/docs/concepts/workloads/pods/
- https://kubernetes.io/docs/concepts/services-networking/service/
- https://kubernetes.io/docs/concepts/workloads/controllers/deployment/
- https://kubernetes.io/docs/concepts/workloads/autoscaling/horizontal-pod-autoscale/
- https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale-walkthrough/
- https://github.com/kubernetes-sigs/prometheus-adapter
- https://www.youtube.com/@cncf

---

## Concept: CI/CD beyond push-to-deploy — staged envs, rollback, canary / blue-green

### Fundamentals
**Push-to-deploy** (merge → production) is fine for toys; production AI systems need a **delivery pipeline** with gates:

1. **CI:** lint, unit/contract tests, build image, scan, push digest-tagged image (`sha-abc123`, not only `:latest`).
2. **Staged environments:** `dev` → `staging` (prod-like data/fakes) → `prod`. Promote the **same image digest**; never rebuild for prod.
3. **Deploy strategies:**
   - **Rolling update** (K8s default): gradually replace Pods.
   - **Blue-green:** two full environments; flip Service/Ingress traffic; instant rollback by flipping back.
   - **Canary:** send a small % of traffic (or users) to the new version; advance on metrics; else abort.
4. **Rollback:** redeploy previous known-good digest / Deployment revision (`kubectl rollout undo`) or flip traffic back. Rollback must be rehearsed.
5. **Release analysis:** error rate, p95 latency, LLM eval canary scores, cost-per-request — not just “pods healthy.”

Google Cloud Deploy documents canary as progressive traffic splitting with optional automated analysis before advancing phases:  
https://cloud.google.com/deploy/docs/deployment-strategies/canary

### Alternatives & Tradeoffs
| Strategy | Blast radius | Cost / complexity | Best for |
|----------|--------------|-------------------|----------|
| Rolling | Medium | Low | Backward-compatible APIs |
| Blue-green | Low (flip) | 2× capacity during cutover | Schema-compatible releases needing fast undo |
| Canary (% traffic) | Lowest | Needs mesh/Ingress weights + metrics | High-risk model/prompt/gateway changes |
| Feature flags | Decouples deploy from release | Flag debt | Prompt/model routing toggles |

LLM-specific risk: a “healthy” pod can still ship a bad prompt or model ID. Include **eval gates** (golden set smoke) in staging and a **shadow/canary eval** in prod.

### Necessity
Without staged promotion, every bad merge is a customer incident. Without digest immutability, “rollback” rebuilds different bits. Without canary/blue-green for high-blast changes, one bad tokenizer/prompt/version burns the monthly LLM budget or serves wrong tenant data. Without automated abort criteria, humans notice too late.

### Industry Practice
**Common:** GitHub Actions → build → deploy staging → manual approve → prod rolling update.  
**Strong:** OIDC to cloud (no long-lived CI keys); environment protection rules; canary 5%→25%→100% with automated metric gates; separate pipelines for infra (Terraform) vs app; progressive delivery (Argo Rollouts / Flagger / Cloud Deploy); post-deploy runbooks; LLM regression suite on staging with production-like prompts.

### Concrete Scenario
GCP Cloud Deploy canary strategy for GKE — configure `strategy.canary` with percentage phases and optional deploy analysis:  
https://cloud.google.com/deploy/docs/deployment-strategies/canary  

Google SRE workbook on canarying data pipelines (same progressive-risk idea applied to batch):  
https://sre.google/workbook/data-processing/

KubeCon / progressive delivery talks (CNCF):  
https://www.youtube.com/@cncf

### Open Questions
- Should model/prompt config changes go through the same canary path as binary deploys?
- How to canary streaming endpoints where error rates are delayed until first token?
- Eval-based canary: what’s the minimum golden-set size for a statistically useful abort signal?

### Sources
- https://cloud.google.com/deploy/docs/deployment-strategies/canary
- https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#rolling-back-a-deployment
- https://sre.google/workbook/data-processing/
- https://sre.google/sre-book/service-best-practices/
- https://argo-rollouts.readthedocs.io/en/stable/
- https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment

---

## Concept: Infrastructure as Code with Terraform

### Fundamentals
Terraform (HashiCorp) declares cloud resources in HCL; state maps config → real objects. Core loop: `init` → `plan` → `apply`. For AI platforms, Terraform typically owns:

- Network (VPC, subnets, private endpoints to model APIs)
- K8s cluster / Cloud Run / ECS
- IAM roles for workloads (IRSA / Workload Identity)
- Secrets manager hooks, KMS keys
- Object storage for corpora, artifacts
- Observability sinks, queues, databases (or modules wrapping them)

App Deployments may stay in GitOps (Helm/Kustomize/Argo CD) while **platform** stays in Terraform — a common split.

State is the source of truth for what Terraform manages; remote state (S3/GCS + locking) is mandatory for teams.

### Alternatives & Tradeoffs
| Tool | Strength | Tradeoff |
|------|----------|----------|
| Terraform / OpenTofu | Multi-cloud, huge provider ecosystem | State drift, blast radius of apply |
| Pulumi | General-purpose languages | Same state problems; different DX |
| CloudFormation / CDK | AWS-native | AWS lock-in |
| Crossplane / Config Connector | K8s-native infra | Requires cluster first |
| ClickOps | Fast start | No review, no drift detection |

Module design: thin wrappers around official providers; pin provider and module versions; separate state per env (`dev`/`staging`/`prod`) to limit blast radius.

### Necessity
Without IaC, environments diverge (“staging isn’t prod”), security groups rot, and disaster recovery is folklore. Without plan review, a one-line IAM change can expose buckets. Without remote state locking, two engineers corrupt infra simultaneously.

### Industry Practice
**Common:** one monorepo `infra/` with workspaces or folders per env; manual `apply` from laptop.  
**Strong:** CI runs `plan` on PR; apply only from protected main with OIDC; policy-as-code (OPA/Sentinel) for public buckets / open SG; drift detection; import existing resources deliberately; GKE/EKS modules with private control plane; blue-green node pool upgrades via provider settings.

### Concrete Scenario
Terraform Google provider `google_container_cluster` documents node pool upgrade strategies including `BLUE_GREEN` with soak duration — infra-level progressive delivery for the cluster itself:  
https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/container_cluster.html  

Terraform language / workflow docs:  
https://developer.hashicorp.com/terraform/intro  
https://developer.hashicorp.com/terraform/cli/commands/plan

### Open Questions
- Where is the boundary between Terraform and Helm for LLM app config (model names, HPA thresholds)?
- OpenTofu vs Terraform for org policy/licensing in 2026?
- How aggressively to terraform “data” resources (vector DB indexes) vs treat them as app migrations?

### Sources
- https://developer.hashicorp.com/terraform/intro
- https://developer.hashicorp.com/terraform/language
- https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/container_cluster.html
- https://developer.hashicorp.com/terraform/tutorials/aws-get-started
- https://opentofu.org/docs/

---

## Concept: Production reliability habits FDEs inherit from SRE (deployment-relevant)

### Fundamentals
Google’s free SRE book emphasizes practices that map directly to shipping AI services: graceful degradation, load shedding, client exponential backoff with jitter, health checking, and staged rollouts. An LLM feature that always calls the strongest model with no timeout/retry budget will amplify provider incidents into your SEV.

### Alternatives & Tradeoffs
Fail-open (serve cached / weaker model) vs fail-closed (error) depends on domain: customer support draft → fail-open; financial action agent → fail-closed with human escalation.

### Necessity
Retry without jitter + no idempotency → thundering herd and duplicate side effects (see Week 21). No SLOs → you cannot decide canary abort thresholds.

### Industry Practice
Define SLIs: availability, latency to first token, answer quality proxy, cost per successful task. Error budgets gate how fast you ship model experiments.

### Concrete Scenario
SRE book — production services best practices (overload, retries, degradation):  
https://sre.google/sre-book/service-best-practices/

### Open Questions
- What is an appropriate error budget for generative quality (not just HTTP 500s)?
- Should cost anomalies page like latency anomalies?

### Sources
- https://sre.google/sre-book/table-of-contents/
- https://sre.google/sre-book/service-best-practices/
- https://sre.google/sre-book/handling-overload/

---

## Week 18 synthesis notes (for later curriculum writing)

- FDE bar: read a Deployment/Service/HPA YAML, explain a failed rollout, propose a canary metric, sketch Terraform for a private GKE/EKS + IAM for the app.
- Do **not** need: writing custom controllers, cluster federation, deep networking CNI debugging.
- Pair this week with Week 20 (cost dashboards need the same labels you put on Pods) and Week 19 (workload identity instead of static API keys in Secrets).
