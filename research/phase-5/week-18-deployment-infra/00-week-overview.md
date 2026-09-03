# 00 — Week overview: staging env, rollback CI/CD, basic IaC

> Week 18 — Deployment infrastructure  
> Research notes (raw). Phase 5 week after LLM-as-judge & observability (Week 17). Next: auth / identity / enterprise (Week 19). Do not start OIDC/SAML/RBAC from this corpus.

---

## Fundamentals

Week 18 is the **shipping** week of Phase 5. Week 17 **instrumented** traces, judges, and dashboards. This week answers four questions Kubernetes docs, Cloud Run, Terraform, GitHub Actions, and the Google SRE book all treat as the minimum bar for an FDE who can land an LLM service:

1. **Where does a change prove it is safe before customers see it?** (staging environment)  
2. **How do you undo a bad ship in minutes, with bits you already built?** (rollback in CI/CD)  
3. **What is the pipeline if merge-to-prod is too dangerous?** (staged delivery, not push-to-deploy)  
4. **How do environments stay reviewable instead of ClickOps folklore?** (basic infrastructure as code)

### Staging environment (promotion, not a second laptop)

A **staging** environment is a **prod-shaped** place that runs the **same container digest** that will go to production. It is not “whatever we last `docker compose up`’d.” Kubernetes Deployments are the declarative unit that makes that promotion real: same Pod template, different namespace/cluster, same image `@sha256:…` ([Deployment concept](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)).

| Staging must have | Staging may fake |
|-------------------|------------------|
| Same image digest as the candidate for prod | Production PII (use anonymized / synthetic / subset) |
| Same probe contract (`/healthz`, `/ready`) | Full multi-region capacity |
| Reachability to **some** LLM provider + vector/DB (or recorded fakes with contract tests) | Production rate-limit headroom |
| Week 16/17 golden-set smoke + a few live traces | 100% traffic volume |
| IAM-shaped identities (even if keys are still static — Week 19 replaces them) | Customer tenancy at full scale |

**Promotion rule:** CI **builds once**. Staging and prod **pull the digest**. Rebuilding for prod is how “rollback” silently ships different Python wheels.

Cloud Run maps the same idea to **revisions** and traffic splitting (a revision is an immutable snapshot of container + env + resources) ([container contract](https://cloud.google.com/run/docs/container-contract); [canary / traffic](https://cloud.google.com/deploy/docs/deployment-strategies/canary)). Compose remains a **developer** inner loop (Week 3), not staging.

### Rollback as a first-class CI/CD path

Rollback is **re-deploying a known-good artifact** or **flipping traffic**, not “git revert and hope CI rebuilds the same bits.”

| Mechanism | What you undo |
|-----------|----------------|
| `kubectl rollout undo deployment/…` | Pod template to a previous ReplicaSet revision ([rolling back a Deployment](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#rolling-back-a-deployment)) |
| Redeploy previous image digest | The bits, independent of Git history noise |
| Blue-green / Cloud Run traffic 100% → previous revision | Data-plane cut; instant if both stacks are warm |
| Canary abort (Argo Rollouts / Flagger / Cloud Deploy) | Partial traffic; automated analysis failed |

Google SRE: **staged rollouts** and **health checking** exist so you detect overload and bad versions **before** the fleet is homogeneous ([service best practices](https://sre.google/sre-book/service-best-practices/); [handling overload](https://sre.google/sre-book/handling-overload/)). The SRE workbook applies the same progressive-risk idea to **canarying data pipelines** ([data processing](https://sre.google/workbook/data-processing/)).

**LLM wrinkle:** pods can be Ready while serving a **wrong model ID or prompt version**. HTTP canaries are necessary but not sufficient; staging golden-set evals (Week 17) belong on the **promote** button.

### CI/CD beyond push-to-deploy

**Push-to-deploy** (merge → production) is fine for toys. Production AI systems need a **delivery pipeline** with gates:

1. **CI:** lint, unit/contract tests, build image, scan, push **digest-tagged** image (`sha-abc123`, not only `:latest`).  
2. **Staged environments:** `dev` → `staging` → `prod`. Promote the same digest.  
3. **Deploy strategy:** rolling (K8s default), blue-green, or canary (file [03](03-cicd-staged-rollback-canary.md)).  
4. **Release analysis:** error rate, p95 / time-to-first-token, LLM eval canary scores, cost-per-request.  
5. **Rollback rehearsal:** a scheduled undo, not a wiki hope.

GitHub **environments** attach protection rules (required reviewers, wait timers, restricted secrets) to `staging` vs `prod` ([Using environments for deployment](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment)).

### Basic IaC (this week’s Terraform bar)

**Infrastructure as code** means the VPC, cluster or Cloud Run service, IAM skeleton, buckets, and queues are **declared**, **planned**, and **applied** with **remote state** — not assembled in a console. Terraform’s loop is `init` → `plan` → `apply` ([intro](https://developer.hashicorp.com/terraform/intro); [plan](https://developer.hashicorp.com/terraform/cli/commands/plan)).

**FDE-sized Terraform this week:**

- Separate **state** per env (`staging` / `prod`) so an apply cannot recreate prod by accident.  
- Remote backend with **locking** (GCS native lock; S3 `use_lockfile` or legacy DynamoDB) ([GCS backend](https://developer.hashicorp.com/terraform/language/backend/gcs); [S3 backend](https://developer.hashicorp.com/terraform/language/backend/s3)).  
- Pin provider versions.  
- Cluster/node-pool upgrades can themselves be progressive (`BLUE_GREEN` soak on GKE via `google_container_cluster`) ([resource docs](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/container_cluster.html)).

App Deployments often stay in GitOps (Helm/Kustomize/Argo CD) while **platform** stays in Terraform — file [04](04-infrastructure-as-code-terraform.md).

### SRE habits that make staging/canary *mean* something

Without SLIs you cannot write canary abort rules. Google’s SRE book maps directly onto LLM APIs: **graceful degradation** (weaker model / cache), **load shedding**, **client exponential backoff with jitter**, **health checking**, **staged rollouts**. Always-on frontier model with no timeout budget **amplifies provider incidents into your SEV** ([service best practices](https://sre.google/sre-book/service-best-practices/); [handling overload](https://sre.google/sre-book/handling-overload/)).

Fail-open vs fail-closed is domain-specific: support-draft → fail-open; financial action agent → fail-closed + human escalation (Week 21 for idempotent side effects).

### What you ship this week

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

### Mapping to adjacent weeks

| This week | Not this week |
|-----------|----------------|
| Containers, K8s fluency, staged CI/CD, Terraform platform | OIDC/SAML, workload identity, tenant RBAC (Week 19) |
| Cost **signals** on canary abort (spend spike) | Routing, semantic cache, compression (Week 20) |
| Idempotency only as a rollback/retry warning | Messy ETL / dual-write (Week 21) |
| Dockerfile as **production contract** | Week 3 local Compose / multi-stage tutorial depth |

---

## Alternatives & Tradeoffs

| Approach | Pros | Cons |
|----------|------|------|
| **Staging + digest promotion + rehearsed rollback + Terraform for platform** | Blast radius bounded; audit trail; FDE-interview-shaped | More YAML; staging cost; eval suite must exist (Week 16/17) |
| Merge-to-prod rolling update only | Fast | Every bad prompt/model is a customer incident |
| Staging that **rebuilds** images | Feels like a gate | Rollback bits ≠ prod bits |
| Cloud Run only (no K8s) | Less cluster ops; revisions + traffic split | Sidecars/networking/HPA custom metrics harder |
| K8s from day one | Portable fluency; HPA/PDB/mesh | Operational surface; overkill for one stateless API |
| ClickOps cluster + “we’ll Terraform later” | Fast start | Drift; unreproducible staging; no plan review |

---

## Necessity

If you skip **staging as same-digest promotion**:

- “Works in staging” means a different build. Incidents cannot be reproduced.  
- Golden-set evals (Week 17) never see the bits customers run.

If you skip **rollback rehearsal**:

- `kubectl rollout undo` is first used during a SEV. Image `:latest` moved. Git revert rebuilds different deps.  
- Blue-green “instant undo” does not exist because green was never kept warm.

If you skip **CI/CD gates**:

- Scan/SBOM never run; secrets leak into layers; `:latest` is the only tag.  
- Canary never has abort metrics; humans notice after the monthly LLM budget is gone.

If you skip **basic IaC**:

- Staging networking ≠ prod (private LLM endpoints, missing NAT, open security groups).  
- Two engineers `apply` local state and corrupt the cluster.  
- DR is a slide.

If you skip **SRE-shaped health and overload control**:

- Load balancer sends traffic to pods that cannot reach the provider → deploy-shaped 5xx storms.  
- Retries without jitter + no idempotency → thundering herd (Week 21).

---

## Industry Practice

**Common:** GitHub Actions builds `:latest`, deploys to one GKE namespace or Cloud Run service, HPA at 70% CPU, Terraform applied from a laptop, staging is a shared Compose file.

**Strong / senior:**

1. Digest tags + registry immutability; OIDC from CI to cloud (no long-lived JSON keys — identity details Week 19).  
2. Environment protection rules on `prod`.  
3. Staging golden-set + contract tests against provider fakes **and** a live smoke.  
4. Canary 5% → 25% → 100% **or** Cloud Run traffic split, with automated analysis (error, latency, eval, cost).  
5. Separate pipelines: Terraform plan-on-PR / apply-on-main vs app GitOps.  
6. HPA on **in-flight requests / queue depth** for LLM workers; CPU only if the process is actually CPU-bound.  
7. Error budgets gate how fast model experiments ship ([SRE SLOs](https://sre.google/sre-book/table-of-contents/)).  
8. Post-deploy runbooks: rollback command, previous digest pinned in the release UI.

KubeCon talks treat progressive delivery as **metric analysis**, not a percentage slider (Hannah Troisi on Argo Rollouts canary analysis, [`OHU7dGcRZvg`](https://www.youtube.com/watch?v=OHU7dGcRZvg); Monzo automated rollback default, [`Vl5siKnYymY`](https://www.youtube.com/watch?v=Vl5siKnYymY)).

---

## Concrete Scenario (URL)

**Kubernetes Deployment** — declarative rollouts and ReplicaSets; the unit you promote and undo.  
https://kubernetes.io/docs/concepts/workloads/controllers/deployment/

**Rollback a Deployment** — `kubectl rollout undo` / revision history.  
https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#rolling-back-a-deployment

**Google Cloud Deploy canary** — percentage phases + optional automated analysis before advancing.  
https://cloud.google.com/deploy/docs/deployment-strategies/canary

**GitHub Actions environments** — staging vs prod protection.  
https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment

**Terraform plan + GCS state** — reviewable infra; remote state with locking.  
https://developer.hashicorp.com/terraform/cli/commands/plan  
https://developer.hashicorp.com/terraform/language/backend/gcs

**SRE staged rollouts / overload** — why staging and canary exist.  
https://sre.google/sre-book/service-best-practices/  
https://sre.google/sre-book/handling-overload/  
https://sre.google/workbook/data-processing/

**KubeCon / CNCF YouTube** — canary analysis and autoscaling deep dives.  
https://www.youtube.com/watch?v=OHU7dGcRZvg  
https://www.youtube.com/watch?v=odxPyW_rZNQ  
https://www.youtube.com/@cncf

---

## Open Questions

- Should **prompt/model config** changes ride the same canary as the binary, or a faster flag pipeline with the same abort metrics?  
- How “prod-like” must staging LLM spend be to catch tokenizer/cost bugs without burning the eval budget?  
- Error budget for **generative quality** (not HTTP 500s) as a ship/no-ship gate?  
- When is Cloud Run’s revision model enough and K8s fluency still required for the FDE interview?  
- Should cost anomalies page like latency anomalies (Week 20 dashboards share labels you put on Pods this week)?

---

## Sources

- https://kubernetes.io/docs/concepts/workloads/controllers/deployment/  
- https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#rolling-back-a-deployment  
- https://kubernetes.io/docs/concepts/workloads/autoscaling/horizontal-pod-autoscale/  
- https://cloud.google.com/run/docs/container-contract  
- https://cloud.google.com/deploy/docs/deployment-strategies/canary  
- https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment  
- https://developer.hashicorp.com/terraform/intro  
- https://developer.hashicorp.com/terraform/cli/commands/plan  
- https://developer.hashicorp.com/terraform/language/backend/gcs  
- https://sre.google/sre-book/table-of-contents/  
- https://sre.google/sre-book/service-best-practices/  
- https://sre.google/sre-book/handling-overload/  
- https://sre.google/workbook/data-processing/  
- https://www.youtube.com/watch?v=OHU7dGcRZvg  
- https://www.youtube.com/watch?v=odxPyW_rZNQ  
- https://www.youtube.com/@cncf  
