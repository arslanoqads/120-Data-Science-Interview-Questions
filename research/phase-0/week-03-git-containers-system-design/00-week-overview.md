# 00 — Week overview & syllabus mapping

> Week 3 — Git discipline, containers, and system design literacy  
> Research notes (raw).

---

## Fundamentals

Week 3 closes Phase 0 by making the Week 1–2 service **shippable and discussable**. The syllabus spine is:

1. Keep Git integration **trunk-shaped** (short-lived branches, green main, feature flags for incomplete work).  
2. Make commit history **machine-readable** (Conventional Commits → changelog/semver).  
3. Package the FastAPI/RAG service in a **multi-stage Docker image** small enough for Cloud Run cold starts.  
4. Reproduce dependencies locally with **Compose** (API + Postgres/pgvector + optional Redis/obs).  
5. Start a **living system design doc** that uses real vocabulary (latency, throughput, scaling, caching, CAP/PACELC, SLOs)—the same language Week 23 interviews probe.

The five concepts form one delivery loop:

| Concept | What it unlocks |
|---------|-----------------|
| TBD | Frequent integration with customer staging; reviewable PRs |
| Semantic commits | Changelog, release notes, STAR archaeology |
| Multi-stage Docker | Artifact you can promote (not “works on my laptop”) |
| Compose | Local parity for DB/vector quirks without burning cloud $ |
| System design vocab | Design doc + interview fluency for RAG/agent tradeoffs |

Skipping any one collapses the rest: a beautiful Compose stack with GitFlow-week-long branches still produces unmergeable agent rewrites; a tiny image with no design-doc vocabulary still fails the “why is p95 8s?” interview question.

Week 3 is the bridge from “HTTP service with mocked tests” (Week 2) to Phase 1+ work that runs in containers against real stores and is explained in a living design document.

---

## Alternatives & Tradeoffs

| Path | What you optimize | What you sacrifice |
|------|-------------------|-------------------|
| Long feature branches + fat single-stage image + “use prod Redis” | Quiet parallel work, minimal Docker craft | Merge hell, slow pulls, hidden DB bugs, weak take-home signal |
| GitFlow (develop/release/hotfix) | Clear release trains on paper | Integration debt; environment branches instead of pipeline stages |
| TBD + short PRs + multi-stage + compose (syllabus default) | Fast feedback, reviewable diffs, local realism | Requires CI discipline, flags, healthchecks, documenting parity limits |
| Full K8s local (kind/Tilt) from day one | Closer to eventual prod orchestrator | Heavy for Phase 0; delays learning Docker fundamentals |
| Cloud-only staging for everything | True prod parity | Slow loop, cost, blocks offline/offline-ish FDE work |

For the flagship Deployment Copilot / RAG chatbot backend, Week 3 should prefer **TBD + conventional commits + multi-stage uv image + compose profiles for API+DB+vector**, plus a living design doc that states SLOs (including cost) and CAP/PACELC choices per *operation*.

---

## Necessity

Concrete failure modes if Week 3 is skipped:

- Multi-week “RAG rewrite + agent rewrite” branch: unreviewable PR, eval baselines that cannot merge, “works on my branch.”  
- `FROM python:3.12` + `pip install` as root → GB image, slow Cloud Run pulls, CVE surface includes compilers.  
- No local Postgres/pgvector → retrieval bugs mocked away until customer staging.  
- Design doc is a slide deck of boxes with no latency/throughput/SLO language → Week 23 interview collapse.  
- Commit history is “update stuff” → cannot reconstruct prompt/eval deltas for STAR stories.

---

## Industry Practice

- **Common (self-taught AI):** feature branch lasting 1–2 weeks; fat Dockerfile; `docker run` one container; CAP recited as “pick two of three”; no design doc.  
- **Strong:** PRs <1–2 days; main always deployable; multi-stage + non-root; compose with healthchecks and documented Cloud Run parity limits; design doc with p95 latency + $/query SLOs.  
- **FDE / platform bar:** can explain TBD vs GitFlow with Thoughtworks/trunkbaseddevelopment.com language; feature flags for incomplete agent tools; CAP/PACELC stated per operation (ACL check vs popularity cache); image size tied to cold-start budget.

---

## Concrete Scenario

Syllabus build task (verbatim intent): multi-stage Docker image + compose local stack + living system design doc. Interviewers ask: how do incomplete agent tools land on main without breaking prod? Why is the image 180MB not 1.4GB? What does compose *not* prove about Cloud Run concurrency? What is your p95 SLO when the LLM provider is the bottleneck?

Public anchors for the same skills:

- Thoughtworks — enabling TBD with deployment pipelines: https://www.thoughtworks.com/insights/blog/enabling-trunk-based-development-deployment-pipelines  
- Docker multi-stage builds: https://docs.docker.com/build/building/multi-stage/  
- Docker Compose: https://docs.docker.com/compose/  
- Google SRE Book — Service Level Objectives: https://sre.google/sre-book/service-level-objectives/

---

## Open Questions

- How early should the living system design doc live in-repo (`docs/system-design.md`) vs Notion/Confluence for customer FDE work?  
- Compose vs Dev Containers vs `gcloud run` local emulator as the default teaching path?  
- Should Week 3 mandate SBOM/image scanning in CI, or defer to Week 18 deployment infra?

---

## Sources

- Syllabus PDF (uploaded): AQ AI Engineer FDE Syllabus  
- https://trunkbaseddevelopment.com/  
- https://www.thoughtworks.com/insights/blog/enabling-trunk-based-development-deployment-pipelines  
- https://www.conventionalcommits.org/en/v1.0.0/  
- https://docs.docker.com/build/building/multi-stage/  
- https://docs.docker.com/compose/  
- https://sre.google/sre-book/table-of-contents/  
