# 01 — Trunk-based development vs feature branches

> Week 3 concept research (deep). Legal sources only.

---

## Fundamentals

### What trunk-based development is
**Trunk-based development (TBD)** is a source-control branching model where developers collaborate on a single long-lived branch called the **trunk** (`main` in modern Git naming) and resist pressure to create other **long-lived** development branches. The one-line summary from trunkbaseddevelopment.com:

> Developers collaborate on code in a single branch called ’trunk’ and resist any pressure to create other long-lived development branches by employing documented techniques. They therefore avoid merge hell, do not break the build, and live happily ever after.

Core rhythm:
- Integrate **small** changes into trunk **at least daily** (often multiple times per day).  
- Keep the trunk **green** / always releasable.  
- Prefer **short-lived** feature branches (hours to ~1–2 days) for review/CI, or (very small teams) commit direct to trunk.  
- Incomplete user-visible work lands behind **feature flags** / toggles, not behind long branches.  
- Longer structural work uses **branch by abstraction** and similar techniques—not weeks of isolation.

TBD is a key enabler of **Continuous Integration** and, by extension, Continuous Delivery. Fowler treats TBD and “true CI” (everyone integrates to mainline at least daily) as essentially synonymous; the “Trunk-Based Development” label resists semantic diffusion where “CI” meant “Jenkins on our feature branches.”

### What it is *not*
- Not “no branches ever.” Short-lived branches + PRs are normal at scale.  
- Not “no release branches.” Just-in-time release branches cut from trunk (then deleted) are compatible; alternatively release from trunk with fix-forward.  
- Not the opposite of code review. Pre-integrate review on short PRs is fine; multi-week isolation is the anti-pattern.

### Contrast: feature branches and GitFlow

**Feature branch** (Fowler): open a branch when starting a feature; do all work there; integrate when *done*. Other developers do not see your changes until then. Short-lived (1–2 days) feature branches approximate CI; week/month branches defer integration risk and discourage refactoring.

**GitFlow** (popularized by Vincent Driessen; widely contrasted on trunkbaseddevelopment.com and Fowler’s branching patterns): multiple long-running branches (`develop`, `release/*`, `hotfix/*`, `main`). Clear release-train narrative; high integration friction; environment/branch sprawl.

**GitHub Flow**: closer to TBD (short-lived branches, PR to main) but release-from semantics can differ; trunkbaseddevelopment.com notes people practicing GitHub Flow will feel “quite similar, with a small difference around where to release from.”

### Deployment pipelines (Thoughtworks)
Thoughtworks argues TBD works best when delivery is modeled as a **deployment pipeline**: commit → stages → increasing confidence toward production—not a branch per environment. Each passing stage raises confidence in that revision; failure stops the pipeline (fix forward or revert). Manual gates (QA promote to staging) can still exist as *pipeline stages*, eliminating the need for environment branches. Pull requests + integration pipelines remain valid when access control requires them (OSS, core-team review)—used *with* TBD, not as multi-week private isolation.

### Feature flags / toggles
Martin Fowler’s Feature Toggles article: **release toggles** allow incomplete codepaths to land on trunk and even ship to production as latent code. Flags **decouple deploy from release**—essential for TBD + Continuous Delivery. Categories include release, experiment, ops, and permission toggles; mismanaged flag debt is a real cost (cleanup, combinatorial testing).

---

## Alternatives & Tradeoffs

| Model | Strength | Cost | When |
|-------|----------|------|------|
| **TBD + short PRs + flags** | Fast feedback; less merge hell; always-deployable main | Requires CI discipline, small batches, flag hygiene | Default for product/FDE delivery teams |
| **GitFlow** | Familiar release/hotfix vocabulary | Slow integration; “integration branch” debt; environment-branch temptation | Rare; regulated release trains sometimes *simulate* this with pipeline stages instead |
| **Long feature branches (weeks)** | Quiet parallel work; big bang demos | Painful merges; hidden breakage; unreviewable PRs; eval baseline drift | Avoid for AI/RAG features |
| **Fork + PR (OSS)** | Access control for untrusted contributors | Not the same as multi-week *internal* private branches | Open source; can still keep contributor PRs small |
| **Scaled TBD (merge queues)** | Serializes integration under high commit rate | Queue latency; tooling cost | Large monorepos (Google-scale patterns) |

**DORA / delivery research** (cited via Fowler branching patterns): very short branch lifetimes (<1 day) and daily merges to trunk correlate with higher performance continuous delivery.

**Tradeoff:** TBD without solid tests/CI is just shared breakage. Feature flags without lifecycle management become permanent conditional debt.

---

## Necessity

### Failure modes if skipped (AI/FDE specific)
1. **Unreviewable “epic” PRs** — RAG rewrite + agent rewrite + prompt overhaul in one branch; reviewers cannot reason about eval deltas.  
2. **“Works on my branch” eval baselines** — golden sets and metric numbers that cannot merge cleanly to main.  
3. **Customer staging drift** — FDE work needs frequent integration with the customer’s staging systems; week-long isolation means painful reconcilation against their main.  
4. **Refactor fear** — long branches discourage shared cleanup (embedding schema, chunk metadata); codebase health decays.  
5. **False CI** — green builds on feature branches that never co-exist until the final merge war.

### Regulated / enterprise tension
Some enterprises mandate long-lived release approval branches. Thoughtworks-style answer: keep **development** trunk-based; express approvals as **pipeline stages / artifact promotion**, not as parallel development lines. Release branches cut JIT from trunk remain compatible with TBD.

---

## Industry Practice

### Common (weak)
- Feature branches lasting 1–2 weeks (or more).  
- Rare CI on `main`; “CI” only on PR branches.  
- Incomplete agent tools gated by “don’t merge yet” instead of flags.  
- Environment branches (`dev`, `staging`, `prod`) as long-lived lines of code.

### Strong / senior
- PRs represent **<1–2 days** of work; main always deployable.  
- Feature flags for risky agent tools, new retrieval paths, and prompt experiments.  
- Release = **promote immutable artifact** through pipeline stages, not merge an epic branch.  
- Short-lived branches for code review + build checking; artifact creation from trunk commits.  
- Branch-by-abstraction for large renames (e.g., swapping vector store clients).  
- Visible pipeline (Thoughtworks): commit → test → staging → prod confidence.

### Scaled practice (awareness)
trunkbaseddevelopment.com notes Google-scale monorepo TBD with tens of thousands of developers—proof that trunk scales with the right tooling (not that every startup needs that tooling).

### RAG / Deployment Copilot application
- Land `feat(retrieval): add hybrid RRF behind flag` before the flag defaults on.  
- Never open `feature/agent-v2-complete-rewrite` for three weeks.  
- Keep prompt/eval harness changes merging daily so baselines stay comparable.

---

## Concrete Scenario

**Thoughtworks — Enabling Trunk Based Development with Deployment Pipelines**  
https://www.thoughtworks.com/insights/blog/enabling-trunk-based-development-deployment-pipelines  

Models delivery as stages from trunk to production; each stage increases confidence; QA can manually promote without an environment branch. Pull requests remain valid for access control alongside TBD.

**Canonical pattern site:** https://trunkbaseddevelopment.com/ — definitions, scaled TBD, release branches, feature flags, branch by abstraction, GitFlow contrast.

**Fowler Feature Branch bliki** (cost of delayed integration / refactor discouragement):  
https://martinfowler.com/bliki/FeatureBranch.html  

**Feature Toggles** (release toggles enabling TBD):  
https://martinfowler.com/articles/feature-toggles.html  

**Atlassian TBD overview** (CI/CD framing for teams):  
https://www.atlassian.com/continuous-delivery/continuous-integration/trunk-based-development  

---

## Open Questions

- How do regulated enterprises reconcile TBD with mandatory long-lived release *approval* branches—promote-artifact vs code-branch?  
- AI-generated PRs: does TBD batch size need to shrink further for human reviewability?  
- When are merge queues mandatory vs overkill for a 3–8 person FDE pod?  
- Feature-flag platforms (LaunchDarkly, Unleash, OpenFeature) vs simple env/config flags for agent tools—when does the platform pay for itself?

---

## Sources

- https://trunkbaseddevelopment.com/  
- https://www.thoughtworks.com/insights/blog/enabling-trunk-based-development-deployment-pipelines  
- https://martinfowler.com/bliki/FeatureBranch.html  
- https://martinfowler.com/articles/feature-toggles.html  
- https://martinfowler.com/articles/branching-patterns.html  
- https://martinfowler.com/articles/continuousIntegration.html  
- https://www.atlassian.com/continuous-delivery/continuous-integration/trunk-based-development  
