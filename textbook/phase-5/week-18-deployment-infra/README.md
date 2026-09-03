# Week 18 Textbook Chapter — Deployment infrastructure

> **Status:** COMPLETE  
> **Source:** `research/phase-5/week-18-deployment-infra/`  
> **Chapter:** [chapter.md](chapter.md)

## Concepts covered

- [x] Containerized deployment patterns for LLM services
- [x] Kubernetes fluency (Pods, Services, Deployments, HPA)
- [x] CI/CD beyond push-to-deploy (staged envs, rollback, canary / blue-green)
- [x] Infrastructure as Code with Terraform

## Structure check

Each concept includes Fundamentals, The Alternatives, Failure Modes, Average vs. Strong Engineer, Worked Example, and Apply It.

## Syllabus build

You already have **Week 17 traces, judges, and dashboards**. This week you **put the same service on a real delivery path**: containerize for production (multi-stage, non-root, env/secrets, `/healthz` + `/ready`); read and explain Deployment + ClusterIP Service + HPA YAML and propose one non-CPU HPA metric if the API is provider-bound; stage CI so one digest promotes `dev` → `staging` → `prod` with golden-set smoke and rehearsed rollback (rolling or canary with abort); sketch basic Terraform for VPC/cluster-or-Cloud-Run, IAM skeleton, remote state with locking, separate state for staging vs prod. Interview artifact = Deployment/Service/HPA YAML you can walk through + one-page pipeline (digest in, promote, rollback) + Terraform sketch for the platform (not the prompt).
