# Week 3 Research Corpus — Git discipline, containers, and system design literacy

> Phase 0 — Engineering Foundations  
> **Status:** COMPLETE (deep pass)  
> Raw research corpus (not textbook). Legal sources only; no pirated books.

This directory is the Week 3 research repository. Read concept files in order, then the source map.

| # | File | Concept |
|---|------|---------|
| 00 | [00-week-overview.md](00-week-overview.md) | Syllabus mapping: Docker multi-stage, compose, living system design doc |
| 01 | [01-trunk-based-development.md](01-trunk-based-development.md) | TBD vs GitFlow/feature branches, Thoughtworks, feature flags |
| 02 | [02-semantic-commits.md](02-semantic-commits.md) | Conventional Commits, changelogs, semver, AI/prompt commit types |
| 03 | [03-docker-multistage.md](03-docker-multistage.md) | Multi-stage builds, image size, BuildKit cache mounts, non-root, uv |
| 04 | [04-docker-compose-local-dev.md](04-docker-compose-local-dev.md) | Compose for API+DB+vector, profiles, healthchecks, Cloud Run parity |
| 05 | [05-system-design-vocabulary.md](05-system-design-vocabulary.md) | Latency/throughput, scaling, LB, caching, CAP+PACELC, LLM SLOs |
| — | [99-source-map.md](99-source-map.md) | Master URL / YouTube / SRE / CAP index |

## Completeness checklist (Week 3)

- [x] All syllabus Week 3 concepts covered with 7 required fields  
- [x] Trunk-based development vs GitFlow / long feature branches documented  
- [x] Thoughtworks deployment-pipeline TBD article + trunkbaseddevelopment.com  
- [x] Martin Fowler Feature Branch / Feature Toggles / branching patterns cited  
- [x] Feature flags as incomplete-work / release decoupling mechanism covered  
- [x] Conventional Commits v1.0.0 + SemVer mapping covered  
- [x] Changelog automation + commitlint / squash-merge tradeoffs covered  
- [x] AI / prompt commit-type debate (`feat` vs dedicated `prompt`) covered  
- [x] Docker official multi-stage builds + building best practices covered  
- [x] BuildKit cache mounts, `.dockerignore`, non-root USER, Python/uv patterns  
- [x] Docker Compose profiles + healthchecks + `depends_on: service_healthy`  
- [x] Local stack for API + DB + vector; parity limits vs Cloud Run documented  
- [x] Latency vs throughput, horizontal/vertical scaling, load balancing, caching layers  
- [x] CAP misconceptions + Brewer “Twelve Years Later” + PACELC (Abadi) covered  
- [x] Google SRE Book (free) SLOs / load chapters cited  
- [x] LLM-specific SLOs and cost-as-first-class objective noted  
- [x] YouTube / conference talk citations (Docker Best Practices, KubeCon CAP, etc.)  
- [x] AI/RAG-service-specific failure modes noted per concept  
- [x] Per-week research **directory** (not a single thin file)  
- [x] `_PRIOR_SINGLE_FILE.md` removed after expansion  

## Syllabus build task (Week 3)

Ship a **production-shaped container** (multi-stage Dockerfile) + **local compose stack** (API + DB/vector) and start a **living system design doc** that uses the vocabulary in `05-system-design-vocabulary.md`. Git discipline (TBD + semantic commits) is how changes land and how the changelog/interview archaeology stays readable.
