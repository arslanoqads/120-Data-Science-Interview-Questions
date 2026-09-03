# 99 — Week 3 master source map

> Consolidated index of docs, blogs, papers, talks. Legal sources only.

---

## Trunk-based development / branching

| Source | Topic | URL |
|--------|-------|-----|
| trunkbaseddevelopment.com | Canonical TBD patterns, GitFlow contrast, flags, release branches | https://trunkbaseddevelopment.com/ |
| Thoughtworks | Enabling TBD with deployment pipelines | https://www.thoughtworks.com/insights/blog/enabling-trunk-based-development-deployment-pipelines |
| Martin Fowler — Feature Branch | Delayed integration costs | https://martinfowler.com/bliki/FeatureBranch.html |
| Martin Fowler — Feature Toggles | Release toggles enabling TBD | https://martinfowler.com/articles/feature-toggles.html |
| Martin Fowler — Branching patterns | Feature branching vs CI/TBD, GitFlow, GitHub Flow | https://martinfowler.com/articles/branching-patterns.html |
| Martin Fowler — Continuous Integration | CI ≈ TBD; semantic diffusion warning | https://martinfowler.com/articles/continuousIntegration.html |
| Martin Fowler — Pull Request | PRs + short-lived branches under CI | https://martinfowler.com/bliki/PullRequest.html |
| Atlassian | TBD overview for CI/CD teams | https://www.atlassian.com/continuous-delivery/continuous-integration/trunk-based-development |

---

## Conventional Commits / SemVer / changelogs

| Source | Topic | URL |
|--------|-------|-----|
| Conventional Commits v1.0.0 | Spec, SemVer mapping, FAQ | https://www.conventionalcommits.org/en/v1.0.0/ |
| Semantic Versioning | MAJOR.MINOR.PATCH rules | https://semver.org/ |
| conventional-changelog | Tooling / guides | https://conventional-changelog.js.org/ |
| commitlint | Enforce conventional messages | https://github.com/conventional-changelog/commitlint |
| YouTube seed | Conventional Commits / GitHub Universe | https://www.youtube.com/results?search_query=conventional+commits+github+universe |

---

## Docker multi-stage / BuildKit / best practices

| Source | Topic | URL |
|--------|-------|-----|
| Docker docs — Multi-stage builds | Named stages, `--target`, BuildKit vs legacy | https://docs.docker.com/build/building/multi-stage/ |
| Docker docs — Building best practices | Bases, rebuilds, multi-stage, layer hygiene | https://docs.docker.com/build/building/best-practices/ |
| Docker get-started — Multi-stage concept | Introductory concept page | https://docs.docker.com/get-started/docker-concepts/building-images/multi-stage-builds/ |
| Docker docs — Build mounts | Cache mounts / secret mounts | https://docs.docker.com/build/guide/mounts/ |
| Docker get-started hub | Orientation | https://docs.docker.com/get-started/ |
| YouTube — Dockerfile Best Practices | Tibor Vass & Sebastiaan van Stijn (Docker); multi-stage + BuildKit | https://www.youtube.com/watch?v=JofsaZ3H1qM |
| YouTube seed | Official multi-stage talks | https://www.youtube.com/results?search_query=docker+multi-stage+builds+official |

---

## Python / uv in Docker

| Source | Topic | URL |
|--------|-------|-----|
| Astral — Using uv in Docker | Cache mounts, lockfile sync, `UV_LINK_MODE` | https://docs.astral.sh/uv/guides/integration/docker/ |
| Depot — Optimal Dockerfile for Python with uv | Layer ordering + cache mounts pattern | https://depot.dev/docs/container-builds/optimal-dockerfiles/python-uv-dockerfile |

---

## Docker Compose / local stacks

| Source | Topic | URL |
|--------|-------|-----|
| Docker Compose docs | Hub | https://docs.docker.com/compose/ |
| Compose file reference | Spec / file overview | https://docs.docker.com/compose/compose-file/ |
| Compose services reference | `healthcheck`, `profiles`, `depends_on` | https://docs.docker.com/reference/compose-file/services/ |
| Profiles how-to | Selective service activation | https://docs.docker.com/compose/how-tos/profiles/ |
| Startup order how-to | `service_healthy` readiness | https://docs.docker.com/compose/how-tos/startup-order/ |
| YouTube seed | Compose official tutorial | https://www.youtube.com/results?search_query=docker+compose+official+tutorial |

---

## Cloud Run parity (local vs prod)

| Source | Topic | URL |
|--------|-------|-----|
| Cloud Run — Test locally | Docker / Cloud Code / gcloud local | https://cloud.google.com/run/docs/testing/local |
| Cloud Run — General tips | Concurrency, min instances, cold start | https://cloud.google.com/run/docs/tips/general |
| Cloud Run — Deploy using Compose | Subset mapping + caveats | https://docs.cloud.google.com/run/docs/deploy-run-compose |

---

## SRE / SLOs / load

| Source | Topic | URL |
|--------|-------|-----|
| Google SRE Book — ToC | Free online book | https://sre.google/sre-book/table-of-contents/ |
| SRE Book — Ch. 4 SLOs | SLI / SLO / SLA; latency & throughput | https://sre.google/sre-book/service-level-objectives/ |
| SRE Book — Ch. 19 Frontend LB | Load balancing | https://sre.google/sre-book/load-balancing-frontend/ |
| SRE Book — Ch. 20 Datacenter LB | Load balancing | https://sre.google/sre-book/load-balancing-datacenter/ |
| SRE Book — Ch. 21 Overload | Handling overload | https://sre.google/sre-book/handling-overload/ |
| SRE Book — Ch. 22 Cascading failures | Failure amplification | https://sre.google/sre-book/addressing-cascading-failures/ |

---

## CAP / PACELC

| Source | Topic | URL |
|--------|-------|-----|
| Brewer — CAP Twelve Years Later (InfoQ) | “2 of 3” misconceptions; partitions | https://www.infoq.com/articles/cap-twelve-years-later-how-the-rules-have-changed/ |
| Abadi — PACELC paper (PDF) | Partition + else latency/consistency | https://www.cs.umd.edu/~abadi/papers/abadi-pacelc.pdf |
| Gilbert/Lynch — Perspectives on CAP (PDF) | Formal context / practical implications | https://groups.csail.mit.edu/tds/papers/Gilbert/Brewer2.pdf |
| Google Cloud — Spanner and CAP | Practitioner CAP nuance | https://cloud.google.com/blog/products/databases/inside-cloud-spanner-and-the-cap-theorem |
| ScyllaDB — PACELC glossary | PA/EL vs PC/EC examples | https://www.scylladb.com/glossary/pacelc-theorem/ |
| Formation — CAP misconceptions | Availability ≠ uptime marketing | https://formation.dev/blog/cap-theorem-misconceptions |

---

## YouTube / conference talks

| Talk | Focus | URL |
|------|-------|-----|
| Dockerfile Best Practices (Docker) | Multi-stage, BuildKit, parallel stages | https://www.youtube.com/watch?v=JofsaZ3H1qM |
| KubeCon NA 2021 — Junod & Burt | CAP, Raft, HA intuition for K8s | https://kccncna2021.sched.com/event/lV4H |
| YouTube seed — KubeCon CAP | Find recording | https://www.youtube.com/results?search_query=KubeCon+CAP+theorem+Raft+Junod+Burt |
| YouTube seed — InfoQ CAP | CAP partition talks | https://www.youtube.com/results?search_query=CAP+theorem+partition+InfoQ |
| YouTube seed — Compose | Official Compose tutorials | https://www.youtube.com/results?search_query=docker+compose+official+tutorial |
| YouTube seed — Conventional Commits | Tooling / Universe | https://www.youtube.com/results?search_query=conventional+commits+github+universe |

---

## Syllabus / internal

- Syllabus PDF (uploaded): AQ AI Engineer FDE Syllabus — Week 3: Git discipline, containers, system design literacy; build multi-stage image + compose stack + living system design doc.

---

## Coverage matrix (concept → primary sources)

| Concept file | Must-cite primaries |
|--------------|---------------------|
| 01 TBD | trunkbaseddevelopment.com, Thoughtworks pipeline article, Fowler Feature Branch + Toggles |
| 02 Semantic commits | conventionalcommits.org v1.0.0, semver.org |
| 03 Multi-stage | docs.docker.com multi-stage + best practices, Astral uv Docker, Docker Best Practices YouTube |
| 04 Compose | Compose profiles + startup-order docs, Cloud Run local/tips |
| 05 System design vocab | SRE Book SLO + LB/overload chapters, Brewer InfoQ, Abadi PACELC, Spanner CAP blog |
