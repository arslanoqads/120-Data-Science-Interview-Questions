# Week 18 Research Corpus — Deployment infrastructure

> Phase 5 — Production, Cost, and Systems  
> **Status:** COMPLETE (deep pass)  
> Raw research corpus (not textbook). Legal/public sources only (Kubernetes docs, Docker docs, Cloud Run, Terraform / HashiCorp, Google SRE book + workbook, CNCF / KubeCon YouTube). **No pirate PDFs, no libgen/pdfcoffee, no unauthorized course decks.**

This directory is the Week 18 research repository. Read concept files in order, then the source map. **Do not start Week 19 (auth / identity / enterprise) from this corpus** — this week ships **containerized LLM services**, **Kubernetes fluency (Pod / Service / Deployment / HPA)**, **staged CI/CD with rollback and canary**, and **basic Terraform IaC**. Workload identity, OIDC/SAML, and multi-tenant RBAC are next week.

| # | File | Concept |
|---|------|---------|
| 00 | [00-week-overview.md](00-week-overview.md) | Staging env, rollback CI/CD, basic IaC — FDE bar for shipping |
| 01 | [01-containerized-deployment.md](01-containerized-deployment.md) | Images, probes, Cloud Run vs K8s vs Compose, secrets, GPU split |
| 02 | [02-kubernetes-fluency.md](02-kubernetes-fluency.md) | Pods, Services, Deployments, HPA (`autoscaling/v2`) |
| 03 | [03-cicd-staged-rollback-canary.md](03-cicd-staged-rollback-canary.md) | Digest promotion, rolling / blue-green / canary, eval gates |
| 04 | [04-infrastructure-as-code-terraform.md](04-infrastructure-as-code-terraform.md) | HCL loop, remote state, env split, Terraform vs GitOps |
| — | [99-source-map.md](99-source-map.md) | Master URL / docs / SRE / KubeCon YouTube index |

## Completeness checklist (Week 18)

- [x] All syllabus Week 18 concepts covered with **7 required fields**  
- [x] **Staging environment** as a promotion gate (same image digest; prod-like deps)  
- [x] **Rollback** as a rehearsed CI/CD path (`kubectl rollout undo`, traffic flip, previous digest)  
- [x] **CI/CD beyond push-to-deploy:** lint/test/scan → digest-tagged image → staged promote  
- [x] **Basic IaC** (Terraform `init`/`plan`/`apply`, remote state + lock, per-env state)  
- [x] Containerized LLM APIs: multi-stage images, env/secrets, liveness vs readiness, stateless app tier  
- [x] Cloud Run container contract (`PORT`, listen on `0.0.0.0`), health checks, min instances  
- [x] Docker official multi-stage + Compose as **local** only (Week 3 depth not duplicated)  
- [x] Kubernetes: Pod, Deployment (+ ReplicaSet, rolling update), Service types, Ingress/Gateway API  
- [x] HPA `autoscaling/v2`: formula `desiredReplicas ≈ current × (currentMetric / desiredMetric)`, sync ~15s  
- [x] CPU HPA pitfall for I/O-bound LLM pods; custom metrics / KEDA / queue-depth workers  
- [x] PDB, topology spread, `preStop` + graceful shutdown for in-flight streams  
- [x] Rolling vs blue-green vs canary vs feature flags; LLM eval/smoke gates  
- [x] Google Cloud Deploy canary percentages + analysis; Argo Rollouts / Flagger  
- [x] GitHub Actions environments / protection rules; OIDC to cloud (no long-lived CI keys)  
- [x] Terraform Google provider `google_container_cluster` blue-green node-pool upgrades  
- [x] OpenTofu as Terraform-compatible alternative (licensing debate noted, not resolved)  
- [x] Google SRE: health checking, staged rollouts, overload, retries with jitter, graceful degradation  
- [x] YouTube KubeCon / CNCF: SIG-Autoscaling, Argo Rollouts canary, Monzo rollouts at scale, Terraform K8s demo  
- [x] LLM-specific failure modes (bad prompt/model ID with “healthy” pods; provider rate limits vs replica count)  
- [x] Per-week research **directory** (not a single thin file)  
- [x] `_PRIOR_SINGLE_FILE.md` removed after expansion  

## Syllabus build task (Week 18)

You already have **Week 17 traces, judges, and dashboards**. This week you **put the same service on a real delivery path**.

1. **Containerize for production, not only local Compose.** Multi-stage image; non-root; config via env; secrets from a store; `/healthz` (liveness) and `/ready` (can reach vector DB + LLM provider). Do **not** bake frontier weights or API keys into the image.  
2. **Read and explain Kubernetes YAML.** A Deployment + ClusterIP Service + HPA. Explain a failed rollout (`kubectl rollout status` / ReplicaSet history). Propose **one** HPA metric that is not CPU if the API is provider-bound.  
3. **Staged pipeline.** CI builds **one digest**; promote `dev` → `staging` → `prod`. Staging runs golden-set smoke (Week 16/17 evals). Prod uses rolling updates **or** a canary with abort on error rate / p95 / eval score. Rehearse rollback.  
4. **Basic Terraform.** VPC/cluster-or-Cloud-Run, IAM for the workload (static keys deferred to Week 19), remote state with locking, separate state for `staging` vs `prod`. PR runs `plan`; apply from protected main.

Interview artifact = **a Deployment/Service/HPA YAML you can walk through** + **a one-page pipeline** (digest in, promote, rollback) + **a Terraform sketch** for the platform (not the prompt).

## Default path (synthesis)

1. **Immutable images, mutable config.** Same digest across envs; secrets never in layers ([Docker multi-stage](https://docs.docker.com/build/building/multi-stage/); [Cloud Run contract](https://cloud.google.com/run/docs/container-contract)).  
2. **Readiness is a load-balancer contract.** Unready pods must not get LLM traffic during deploys ([K8s probes](https://kubernetes.io/docs/concepts/configuration/liveness-readiness-startup-probes/)).  
3. **HPA scales replicas, not provider quota.** CPU under-signals I/O-bound LLM APIs ([HPA concept](https://kubernetes.io/docs/concepts/workloads/autoscaling/horizontal-pod-autoscale/)).  
4. **Promote digests; canary quality, not just HTTP 200.** A healthy pod can still ship a bad model ID ([Cloud Deploy canary](https://cloud.google.com/deploy/docs/deployment-strategies/canary); [SRE workbook canarying](https://sre.google/workbook/data-processing/)).  
5. **Terraform owns the platform; GitOps owns the app.** Remote state + lock; per-env blast radius ([Terraform intro](https://developer.hashicorp.com/terraform/intro)).  
6. **SRE habits are the abort criteria.** Timeouts, load shedding, error budgets decide when a canary dies ([SRE service best practices](https://sre.google/sre-book/service-best-practices/)).
