# 99 — Week 18 master source map

> Consolidated index of official docs, SRE books, talks, YouTube. Legal sources only; no pirate book sites, no unauthorized course PDFs.

**Deep-pass date:** 2026-09-03. Re-fetch before shipping a lecture — Kubernetes HPA defaults, Cloud Deploy schema, Terraform S3 `use_lockfile` deprecation of DynamoDB, Cloud Run probe billing, HashiCorp license / OpenTofu, and GitHub Actions environment UI paths move.

**Not used:** pirate Docker/K8s books, libgen, pdfcoffee, leaked Udemy/Maven decks. Official Kubernetes / Docker / Cloud Run / Terraform docs, Google SRE (free web book), CNCF/KubeCon YouTube, Argo Rollouts docs, GitHub docs only.

---

## Kubernetes

| Topic | URL |
|-------|-----|
| Deployment (rollout, ReplicaSet, strategy) | https://kubernetes.io/docs/concepts/workloads/controllers/deployment/ |
| Rolling back a Deployment | https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#rolling-back-a-deployment |
| Pods | https://kubernetes.io/docs/concepts/workloads/pods/ |
| Service | https://kubernetes.io/docs/concepts/services-networking/service/ |
| Liveness, readiness, startup probes | https://kubernetes.io/docs/concepts/configuration/liveness-readiness-startup-probes/ |
| Horizontal Pod Autoscaling (algorithm, v2, behavior, Metrics Server) | https://kubernetes.io/docs/concepts/workloads/autoscaling/horizontal-pod-autoscale/ |
| HPA walkthrough | https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale-walkthrough/ |
| HorizontalPodAutoscaler v2 API | https://kubernetes.io/docs/reference/kubernetes-api/autoscaling/horizontal-pod-autoscaler-v2/ |
| Gateway API | https://gateway-api.sigs.k8s.io/ |
| prometheus-adapter (custom metrics) | https://github.com/kubernetes-sigs/prometheus-adapter |
| KEDA concepts | https://keda.sh/docs/latest/concepts/ |

---

## Docker

| Topic | URL |
|-------|-----|
| Multi-stage builds | https://docs.docker.com/build/building/multi-stage/ |
| Building best practices | https://docs.docker.com/build/building/best-practices/ |
| Compose | https://docs.docker.com/compose/ |

---

## Cloud Run / Cloud Deploy (Google Cloud)

| Topic | URL |
|-------|-----|
| Container runtime contract (`PORT`, `0.0.0.0`, `K_*`) | https://cloud.google.com/run/docs/container-contract |
| Configure containers | https://cloud.google.com/run/docs/configuring/services/containers |
| Health checks (startup / liveness / readiness) | https://cloud.google.com/run/docs/configuring/healthchecks |
| Min instances | https://cloud.google.com/run/docs/configuring/min-instances |
| Instance autoscaling | https://cloud.google.com/run/docs/about-instance-autoscaling |
| Cloud Deploy canary strategy | https://cloud.google.com/deploy/docs/deployment-strategies/canary |
| Cloud Deploy config schema (canary stanzas) | https://cloud.google.com/deploy/docs/config-files |

---

## Terraform / OpenTofu

| Topic | URL |
|-------|-----|
| Intro | https://developer.hashicorp.com/terraform/intro |
| Language | https://developer.hashicorp.com/terraform/language |
| `terraform plan` | https://developer.hashicorp.com/terraform/cli/commands/plan |
| GCS backend (locking, versioning warning) | https://developer.hashicorp.com/terraform/language/backend/gcs |
| S3 backend (`use_lockfile`, DynamoDB deprecated) | https://developer.hashicorp.com/terraform/language/backend/s3 |
| AWS get-started tutorial | https://developer.hashicorp.com/terraform/tutorials/aws-get-started |
| `google_container_cluster` (BLUE_GREEN upgrades) | https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/container_cluster.html |
| OpenTofu docs | https://opentofu.org/docs/ |
| AWS Prescriptive Guidance — Terraform backends | https://docs.aws.amazon.com/prescriptive-guidance/latest/terraform-aws-provider-best-practices/backend.html |

---

## Google SRE (free web book + workbook)

| Topic | URL |
|-------|-----|
| Table of contents | https://sre.google/sre-book/table-of-contents/ |
| Production services best practices (health, retries, degradation, staged rollouts) | https://sre.google/sre-book/service-best-practices/ |
| Handling overload | https://sre.google/sre-book/handling-overload/ |
| Workbook — data processing / canarying pipelines | https://sre.google/workbook/data-processing/ |

---

## CI/CD / progressive delivery docs

| Topic | URL |
|-------|-----|
| GitHub Actions environments | https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment |
| Argo Rollouts | https://argo-rollouts.readthedocs.io/en/stable/ |

---

## YouTube (KubeCon / CNCF and adjacent official talks)

| Topic | URL |
|-------|-----|
| CNCF YouTube channel (KubeCon archive; search HPA, canary, Terraform) | https://www.youtube.com/@cncf |
| SIG-Autoscaling Deep Dive and Q+A — Maciek Pytel & Marcin Wielgus (HPA/VPA/CA) | https://www.youtube.com/watch?v=odxPyW_rZNQ |
| Lightning: Open Source Canary Deployments with Application Metric Analysis — Hannah Troisi (Argo Rollouts) | https://www.youtube.com/watch?v=OHU7dGcRZvg |
| Argo Rollouts at Scale / automated rollback — Joseph Pallamidessi, Monzo | https://www.youtube.com/watch?v=Vl5siKnYymY |
| Tailored Deployment Strategies: Argo Rollouts — Larisa Danaila, Adobe | https://www.youtube.com/watch?v=aWP6ZUdPXak |
| Real Time Argo Rollouts Analytics — Intuit (Agrawal & Blixt) | https://www.youtube.com/watch?v=EbEWJP1HDt0 |
| KubeCon NA 2021 demo: Multi-Cloud Kubernetes with HashiCorp Terraform | https://www.youtube.com/watch?v=EQasvKfQLy4 |
| HPA + KEDA + node autoscaling pedagogy (EKS; complementary to SIG-Autoscaling) | https://www.youtube.com/watch?v=H2REI7uE_yc |
| Terraform CI/GitHub flow (Natalie Godec; pipeline design, not KubeCon) | https://www.youtube.com/watch?v=hc7sTnYKCkU |

---

## Mapping: source → Week 18 file

| File | Primary sources |
|------|-----------------|
| [00-week-overview.md](00-week-overview.md) | K8s Deployment + rollback; Cloud Deploy canary; GitHub environments; Terraform plan + GCS backend; SRE best practices / overload / workbook; YouTube OHU7dGcRZvg + odxPyW_rZNQ |
| [01-containerized-deployment.md](01-containerized-deployment.md) | Docker multi-stage + Compose; K8s probes + Deployment; Cloud Run contract, healthchecks, min instances; SRE health checking |
| [02-kubernetes-fluency.md](02-kubernetes-fluency.md) | Pods, Service, Deployment, HPA concept + walkthrough + v2 API; prometheus-adapter; KEDA; Gateway API; YouTube odxPyW_rZNQ, H2REI7uE_yc |
| [03-cicd-staged-rollback-canary.md](03-cicd-staged-rollback-canary.md) | Cloud Deploy canary + config schema; K8s rollback; GitHub environments; Argo Rollouts docs; SRE workbook + best practices; YouTube OHU7dGcRZvg, Vl5siKnYymY, aWP6ZUdPXak, EbEWJP1HDt0 |
| [04-infrastructure-as-code-terraform.md](04-infrastructure-as-code-terraform.md) | Terraform intro/language/plan/backends; google_container_cluster; OpenTofu; AWS backend guidance; YouTube EQasvKfQLy4, hc7sTnYKCkU |

---

## Explicitly out of scope (Week 19+)

OIDC/SAML, workload identity protocols, tenant RBAC, data residency **as the main deliverable** (Week 19). LiteLLM/RouteLLM **cost routing** and semantic cache (Week 20). Idempotent dual-write / messy ETL (Week 21). Week 3 Compose/multi-stage tutorials are **prerequisite**, not duplicated as the focus. Week 17 tracing is assumed so canary abort can use quality/cost signals.
