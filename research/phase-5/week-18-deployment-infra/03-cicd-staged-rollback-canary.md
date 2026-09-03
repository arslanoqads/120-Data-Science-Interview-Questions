# 03 — CI/CD beyond push-to-deploy: staged envs, rollback, canary / blue-green

> Week 18 — delivery pipeline. Container/K8s objects: files [01](01-containerized-deployment.md)–[02](02-kubernetes-fluency.md). Terraform apply pipeline: file [04](04-infrastructure-as-code-terraform.md). Research notes (raw).

---

## Fundamentals

**Push-to-deploy** (merge → production) is a valid inner loop for toys. Production AI systems need a **delivery pipeline** with **gates**, **immutable artifacts**, and a **rehearsed undo**.

### Pipeline stages

1. **CI**  
   Lint, unit/contract tests, build image, **scan**, push **digest-tagged** image (`sha-abc123`, not only `:latest`). SBOM optional but strong.  
2. **Staged environments**  
   `dev` → `staging` (prod-like deps / fakes) → `prod`. Promote the **same image digest**; never rebuild for prod (file [00](00-week-overview.md)).  
3. **Deploy strategies** (data plane):

| Strategy | Mechanism |
|----------|-----------|
| **Rolling update** | K8s Deployment default: replace Pods with `maxUnavailable` / `maxSurge`. Rollback = previous ReplicaSet. |
| **Blue-green** | Two full environments; flip Service/Ingress/Gateway or Cloud Run traffic; instant undo by flipping back. Needs ~2× capacity during cutover. |
| **Canary** | Small % of traffic (or users) on the new version; advance on **metrics**; else abort. Needs weights (Ingress/Gateway/mesh) **or** replica-ratio hacks (weaker). |

4. **Rollback**  
   Redeploy previous known-good digest; `kubectl rollout undo`; flip traffic; progressive-delivery controller abort. Must be **rehearsed**.  
5. **Release analysis**  
   Error rate, p95 / TTFT, **LLM eval canary scores**, cost-per-request — not just “pods Ready.”

### Cloud Deploy canary (GKE / Cloud Run)

Google Cloud Deploy documents **canary** as progressive traffic splitting with optional **automated analysis** before advancing phases. GKE can use **service networking** (pod counts ≈ traffic) or **Gateway API** (true percentage weights). Configure `strategy.canary` with percentage phases (e.g. 10 / 50 / 80 then full) ([canary overview](https://cloud.google.com/deploy/docs/deployment-strategies/canary); GKE service networking and Gateway API guides linked from that page; [config schema](https://cloud.google.com/deploy/docs/config-files)).

Cloud Run canaries shift **revision traffic** without you managing ReplicaSets.

### Argo Rollouts vs Flagger (K8s progressive delivery)

Both are CNCF-adjacent progressive delivery:

| | **Argo Rollouts** | **Flagger** |
|--|-------------------|-------------|
| Workload | Replaces Deployment with `Rollout` CR | Watches a normal **Deployment** |
| GitOps home | Argo CD | Flux (works elsewhere with care) |
| Analysis | `AnalysisTemplate` (Prometheus, jobs, web metrics, …) | Interval / threshold / metric providers |
| Traffic | Mesh, Ingress, Gateway, ALB, … | Mesh / Ingress; creates primary+canary services |

Hannah Troisi (CNCF/KubeCon lightning): canary is **art plus analysis** — how much traffic, which metrics, how long ([`OHU7dGcRZvg`](https://www.youtube.com/watch?v=OHU7dGcRZvg)). Adobe: scrape interval vs canary duration — enough points for analysis ([`aWP6ZUdPXak`](https://www.youtube.com/watch?v=aWP6ZUdPXak)). Monzo (KubeCon): **2100+** services; invested in Rollouts so **automated rollback is the default**, not heroic canarying ([`Vl5siKnYymY`](https://www.youtube.com/watch?v=Vl5siKnYymY)). Intuit: thousands of Rollout objects; insights from notification engine ([`EbEWJP1HDt0`](https://www.youtube.com/watch?v=EbEWJP1HDt0)). Docs: [Argo Rollouts](https://argo-rollouts.readthedocs.io/en/stable/).

### Feature flags vs deploys

Flags **decouple deploy from release** (Week 3 TBD). For LLM: route **model ID / prompt version** with a flag **and** still canary the **binary**. Flag-only changes still need abort metrics (quality + cost). Flag debt is real.

### GitHub environments

`staging` / `prod` as GitHub **environments**: required reviewers, wait timers, environment secrets, deployment branches ([docs](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment)). **OIDC** to cloud so CI has no long-lived keys (Week 19 deep-dive; mention as strong practice here).

### LLM-specific gates

A Ready pod can still ship a **bad prompt or model ID**. Include:

- **Eval gates** on staging (Week 16/17 golden set smoke — code evals in CI, judges sampled)  
- **Shadow / canary eval** in prod (sample traces, not 100% GPT-4 judges)  
- **Cost-per-request** abort (Week 20 will dashboard the same labels)  
- **Streaming:** error rate may stay green until **first token**; abort on TTFT / timeout rate, not only HTTP 500

Google SRE workbook: canary **data pipelines** with progressive risk — same idea as traffic canaries ([workbook](https://sre.google/workbook/data-processing/)). SRE book: staged rollouts, health checking ([service best practices](https://sre.google/sre-book/service-best-practices/)).

---

## Alternatives & Tradeoffs

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

---

## Necessity

Without **staged promotion**, every bad merge is a customer incident.

Without **digest immutability**, “rollback” rebuilds different bits (`:latest` moved; lockfile changed).

Without canary/blue-green for **high-blast** changes, one bad tokenizer/prompt/version burns the monthly LLM budget or serves **wrong tenant data**.

Without **automated abort criteria**, humans notice too late. Monzo’s KubeCon lesson: do not rely on “engineers will watch the dashboard” at 100 deploys/day.

Without **streaming-aware** SLIs, canaries promote a version that hangs on first token.

Without **rehearsed rollback**, the undo path is a Slack thread.

---

## Industry Practice

**Common:** GitHub Actions → build → deploy staging → manual approve → prod **rolling** update; `:latest`; no eval gate; rollback undocumented.

**Strong / senior:**

- OIDC to cloud; environment protection rules  
- Canary **5% → 25% → 100%** (or Cloud Deploy percentages) with **automated** metric gates  
- Separate pipelines: **infra** (Terraform plan/apply) vs **app** (image + GitOps)  
- Progressive delivery (Argo Rollouts / Flagger / Cloud Deploy)  
- Post-deploy runbooks; LLM regression suite on staging with production-like prompts  
- Monzo-style: **automated rollback defaults** even when canary is “light”  
- Adobe-style: analysis duration matched to scrape interval and traffic  
- SRE: error budgets decide whether you **slow the pipeline** after a quality burn

Cloud Run teams: traffic tags / revisions instead of Rollouts CRDs — same **percentage + analysis** idea.

---

## Concrete Scenario (URL)

**GCP Cloud Deploy canary** — `strategy.canary`, percentage phases, analysis, GKE + Cloud Run:  
https://cloud.google.com/deploy/docs/deployment-strategies/canary  
https://cloud.google.com/deploy/docs/config-files

**Kubernetes Deployment rollback:**  
https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#rolling-back-a-deployment

**GitHub environments:**  
https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment

**Argo Rollouts docs:**  
https://argo-rollouts.readthedocs.io/en/stable/

**SRE workbook canarying data pipelines** (progressive risk):  
https://sre.google/workbook/data-processing/

**SRE service best practices** (staged rollouts, health):  
https://sre.google/sre-book/service-best-practices/

**KubeCon / CNCF YouTube:**

- Open source canary + metric analysis (Argo Rollouts) — Hannah Troisi: https://www.youtube.com/watch?v=OHU7dGcRZvg  
- Argo Rollouts at scale / automated rollback default — Monzo: https://www.youtube.com/watch?v=Vl5siKnYymY  
- Tailored Rollouts analysis (Adobe): https://www.youtube.com/watch?v=aWP6ZUdPXak  
- Rollouts analytics at Intuit: https://www.youtube.com/watch?v=EbEWJP1HDt0  
- CNCF channel: https://www.youtube.com/@cncf

---

## Open Questions

- Should **model/prompt config** changes go through the same canary path as binary deploys?  
- How to canary **streaming** endpoints where error rates are delayed until first token?  
- Eval-based canary: minimum golden-set size for a statistically useful abort (Week 16/17 sample-size tension)?  
- Header-based canary (employees / beta tenants) vs % traffic for multi-tenant RAG (wrong-tenant risk)?  
- When is blue-green cheaper than canary (GPU inference pools that cannot run two versions)?  
- Feature-flag + canary: who owns abort — platform or app team?

---

## Sources

- https://cloud.google.com/deploy/docs/deployment-strategies/canary  
- https://cloud.google.com/deploy/docs/config-files  
- https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#rolling-back-a-deployment  
- https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment  
- https://argo-rollouts.readthedocs.io/en/stable/  
- https://sre.google/workbook/data-processing/  
- https://sre.google/sre-book/service-best-practices/  
- https://sre.google/sre-book/handling-overload/  
- https://www.youtube.com/watch?v=OHU7dGcRZvg  
- https://www.youtube.com/watch?v=Vl5siKnYymY  
- https://www.youtube.com/watch?v=aWP6ZUdPXak  
- https://www.youtube.com/watch?v=EbEWJP1HDt0  
- https://www.youtube.com/@cncf  
