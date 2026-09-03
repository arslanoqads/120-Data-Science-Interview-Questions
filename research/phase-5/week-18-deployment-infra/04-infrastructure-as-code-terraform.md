# 04 — Infrastructure as Code with Terraform

> Week 18 — **basic** IaC for the AI platform (network, cluster/Cloud Run, IAM skeleton, state). App Deployments may stay GitOps. Research notes (raw).

---

## Fundamentals

**Terraform** (HashiCorp) declares cloud resources in **HCL**. **State** maps configuration addresses → real object IDs. The core loop is `terraform init` → `plan` → `apply` ([intro](https://developer.hashicorp.com/terraform/intro); [language](https://developer.hashicorp.com/terraform/language); [plan](https://developer.hashicorp.com/terraform/cli/commands/plan)).

For AI platforms, Terraform typically owns:

- Network (VPC, subnets, private endpoints to model APIs)  
- GKE/EKS/AKS **or** Cloud Run / ECS  
- IAM roles for workloads (IRSA / Workload Identity — **wire-up this week**; protocol deep-dive Week 19)  
- Secrets manager **hooks**, KMS keys  
- Object storage for corpora and artifacts  
- Observability sinks, queues, databases (or modules wrapping them)

**Split of record:** Terraform = **platform**. Helm/Kustomize/Argo CD = **app** (Deployments, HPA thresholds, prompt ConfigMaps). Crossing the boundary casually (Terraform `kubernetes_deployment`) creates two sources of truth.

### State is the contract

- **Local state** is for tutorials. Teams use **remote state**.  
- **Locking** prevents two applies from corrupting the mapping.  
- **GCS backend:** state object in a pre-existing bucket; **locking supported**; enable **object versioning** for recovery ([gcs backend](https://developer.hashicorp.com/terraform/language/backend/gcs)).  
- **S3 backend:** state key in a bucket; enable native locking with `use_lockfile = true` (DynamoDB locking **deprecated**, both can coexist during migration) ([s3 backend](https://developer.hashicorp.com/terraform/language/backend/s3)).  
- State contains **secrets** (sometimes). Restrict read IAM; encrypt; do not commit `terraform.tfstate`.

**Workspaces vs directories:** named workspaces share code with different state keys. Stronger blast-radius control: **separate root modules / separate state** per env (`staging`, `prod`) — a prod apply cannot see staging resources. HashiCorp tutorials still show workspaces; production FDE practice usually **folders + separate backends**.

### Plan is the review artifact

CI on PR: `fmt` + `init` + `validate` + `plan`. Humans review the plan (especially IAM, buckets, security groups). Apply **only** from protected `main` with OIDC (or a tightly gated runner). Natalie Godec’s public talk (HashiConf/community; widely cited IaC pipeline): **GitHub flow**; matrix or **detect-changed-roots** so you do not apply every stack every time ([`hc7sTnYKCkU`](https://www.youtube.com/watch?v=hc7sTnYKCkU)).

### Modules and pinning

Thin wrappers around **official providers**; pin **provider** and **module** versions. Do not “latest” the Google provider on Friday.

### GKE upgrades as infra-level progressive delivery

Terraform Google provider `google_container_cluster` documents node-pool upgrade strategies including **`BLUE_GREEN`** with soak duration — the cluster itself can roll like an app ([container_cluster](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/container_cluster.html)). Pair with **PDBs** (file 02) so soak does not evict the last LLM replica.

### OpenTofu

[OpenTofu](https://opentofu.org/docs/) is a Terraform-compatible fork after HashiCorp license changes. Same HCL mental model; org policy/licensing is an **open question**, not a syllabus pick-one.

### ClickOps and import

Existing console resources can be `terraform import`ed **deliberately**. Accidental import of half a VPC is how state lies. Drift detection (plan in CI on a schedule) finds ClickOps.

KubeCon NA 2021 HashiCorp demo: multi-cloud Kubernetes from Terraform (version data sources vs pinning) ([`EQasvKfQLy4`](https://www.youtube.com/watch?v=EQasvKfQLy4)).

---

## Alternatives & Tradeoffs

| Tool | Strength | Tradeoff |
|------|----------|----------|
| Terraform / OpenTofu | Multi-cloud; huge provider ecosystem | State drift; blast radius of apply; license fork politics |
| Pulumi | General-purpose languages | Same state class of problems; different DX |
| CloudFormation / CDK | AWS-native | AWS lock-in |
| Crossplane / Config Connector | K8s-native infra | Requires a cluster **first** (chicken/egg) |
| ClickOps | Fast start | No review; no drift detection; unreproducible staging |
| Terraform `kubernetes_*` for apps | One tool | Fights GitOps; slow apply; state owns Pods |
| Terragrunt / wrappers | DRY roots | Extra abstraction interviews may not assume |

**Env isolation patterns:**

| Pattern | Blast radius | Footgun |
|---------|--------------|---------|
| Separate accounts/projects + separate state | Smallest | More boilerplate |
| One project, folders `envs/staging|prod` | Small if backends differ | Wrong `-chdir` |
| One state, `count`/`for_each` both envs | Huge | One apply touches prod |
| Workspaces `default`/`prod` | Easy | Easy to apply the wrong workspace |

---

## Necessity

Without IaC, environments **diverge** (“staging isn’t prod”), security groups rot, and disaster recovery is folklore.

Without **plan review**, a one-line IAM change can expose buckets (Week 19 will make this worse if identity is also ClickOps).

Without **remote state locking**, two engineers corrupt infra simultaneously.

Without **per-env state**, a “quick staging fix” recreates the prod cluster.

Without Terraform (or equivalent) for **private control plane / private endpoints**, LLM API keys and corpora traverse the public internet by accident.

Without **version pins**, a provider upgrade rewrites GKE in a Monday plan you did not intend.

---

## Industry Practice

**Common:** one monorepo `infra/` with workspaces; `terraform apply` from a laptop; app Deployments also in Terraform; state in the same bucket without versioning; no policy-as-code.

**Strong / senior:**

- CI `plan` on PR; apply from protected main + OIDC  
- Policy-as-code (OPA/Sentinel) for public buckets / open SG  
- Drift detection job  
- Import existing resources **on purpose**  
- GKE/EKS modules with **private** control plane  
- Blue-green **node pool** upgrades via provider settings  
- Separate pipelines from app images (file 03)  
- Bootstrap problem: state bucket created once (script or tiny stack), then everything else uses it  
- GitOps (Argo CD) **installed by Terraform** (Helm provider) then left to reconcile apps — Terraform does not own the LLM Deployment thereafter  

AWS prescriptive guidance (legal, vendor): remote S3 state + locking; prefer native S3 lock over DynamoDB going forward ([backend best practices](https://docs.aws.amazon.com/prescriptive-guidance/latest/terraform-aws-provider-best-practices/backend.html)).

---

## Concrete Scenario (URL)

**Terraform intro + language + plan:**  
https://developer.hashicorp.com/terraform/intro  
https://developer.hashicorp.com/terraform/language  
https://developer.hashicorp.com/terraform/cli/commands/plan

**GCS / S3 backends (lock + versioning warning):**  
https://developer.hashicorp.com/terraform/language/backend/gcs  
https://developer.hashicorp.com/terraform/language/backend/s3

**GKE `google_container_cluster` — BLUE_GREEN node upgrades / soak:**  
https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/container_cluster.html

**Get started tutorial (workflow muscle memory):**  
https://developer.hashicorp.com/terraform/tutorials/aws-get-started

**OpenTofu docs:**  
https://opentofu.org/docs/

**KubeCon NA 2021 — Multi-cloud Kubernetes with Terraform (HashiCorp):**  
https://www.youtube.com/watch?v=EQasvKfQLy4

**IaC pipeline / GitHub flow for Terraform (public talk):**  
https://www.youtube.com/watch?v=hc7sTnYKCkU

**Teaching sketch (not copy-paste prod):** remote GCS backend + two env prefixes; `google_cloud_run_v2_service` or GKE module in `envs/prod`; app image digest **not** hardcoded in Terraform (CI writes to GitOps repo instead).

---

## Open Questions

- Where is the boundary between **Terraform and Helm** for LLM app config (model names, HPA thresholds)?  
- OpenTofu vs Terraform for org policy/licensing in 2026?  
- How aggressively to terraform **data** resources (vector DB indexes) vs treat them as app migrations?  
- Should Cloud Run services be Terraform or `gcloud`/`skaffold` like GKE apps?  
- Policy-as-code in CI vs HCP Terraform Sentinel — enough for an FDE interview?  
- Week 19: does Workload Identity **belong** in this week’s Terraform module or wait for the identity week?

---

## Sources

- https://developer.hashicorp.com/terraform/intro  
- https://developer.hashicorp.com/terraform/language  
- https://developer.hashicorp.com/terraform/cli/commands/plan  
- https://developer.hashicorp.com/terraform/language/backend/gcs  
- https://developer.hashicorp.com/terraform/language/backend/s3  
- https://developer.hashicorp.com/terraform/tutorials/aws-get-started  
- https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/container_cluster.html  
- https://opentofu.org/docs/  
- https://docs.aws.amazon.com/prescriptive-guidance/latest/terraform-aws-provider-best-practices/backend.html  
- https://www.youtube.com/watch?v=EQasvKfQLy4  
- https://www.youtube.com/watch?v=hc7sTnYKCkU  
- https://www.youtube.com/@cncf  
