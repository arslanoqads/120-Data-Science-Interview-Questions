# 02 — Semantic commits (Conventional Commits, changelogs, semver)

> Week 3 concept research (deep). Legal sources only.

---

## Fundamentals

### What Conventional Commits are
**Conventional Commits** (spec v1.0.0) is a lightweight convention on top of commit messages that adds human- and machine-readable meaning. Structure:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

SemVer mapping (from the spec):
- `fix` → **PATCH**  
- `feat` → **MINOR**  
- `BREAKING CHANGE` footer or `!` after type/scope → **MAJOR** (any type can be breaking)

Other types (`build`, `chore`, `ci`, `docs`, `style`, `refactor`, `perf`, `test`, …) are allowed (Angular / `@commitlint/config-conventional` conventions) and have **no implicit SemVer effect** unless they include a breaking change.

Example with scope (AI service shaped):

```
feat(retrieval): add RRF fusion for hybrid search

Wire BM25 + dense scores through Reciprocal Rank Fusion.
Behind flag `hybrid_rrf_enabled` (default off).

Eval: nDCG@10 +0.04 on golden_v3
```

Breaking change forms:
```
feat(api)!: rename /query to /v2/retrieve

BREAKING CHANGE: clients must call /v2/retrieve; /query removed.
```

### Why it exists
Per the spec, benefits include:
- Automatically generating **CHANGELOGs**  
- Automatically determining **semantic version** bumps  
- Communicating change nature to teammates/stakeholders  
- Triggering build/publish processes  
- Making structured history easier to explore for contributors

It is a **communication protocol** for humans and release tooling—not magic quality.

### SemVer reminder
**Semantic Versioning** (semver.org): `MAJOR.MINOR.PATCH`. Public API breakage → major; backward-compatible feature → minor; backward-compatible bugfix → patch. Conventional Commits dovetail by encoding intent in the commit stream so tools (`semantic-release`, `release-please`, `conventional-changelog`) can automate bumps and notes.

### Changelog automation
Tools parse commits since the last tag, group by type, emit `CHANGELOG.md` / GitHub Release notes. Workflow choices:
- **Every commit conventional** + merge commits kept  
- **Squash-merge** with a single conventional subject written at merge time (spec FAQ: lead maintainers can clean up for casual committers)  
Decide deliberately—squash destroys granular archaeology unless PR bodies preserve it.

---

## Alternatives & Tradeoffs

| Approach | Strengths | Weaknesses | When |
|----------|-----------|------------|------|
| **Conventional Commits + commitlint** | Machine-parseable; changelog/semver automation | Noisy if over-scoped; learning curve; bikeshedding types | Libraries, services with releases, interview portfolios |
| **Free-form prose** | Expressive; low friction | Weak automation; inconsistent archaeology | Tiny personal scripts |
| **Ticket-ID prefixes only** (`PROJ-123: …`) | Traceability to tracker | Weak change taxonomy; poor changelog grouping | Enterprise ticket culture—often *combine* with conventional (`fix(auth): … Refs: PROJ-123`) |
| **PR-title-as-squash-message** | One clean history line per PR | Loses intra-PR commits; needs discipline on PR title | Common GitHub team default compatible with Conventional Commits |
| **AI-generated commit messages** | Speed | Confident nonsense; wrong type/scope; hallucinated “why” | Use as draft only; human owns SemVer intent |

**Enforcement tradeoff:** commitlint + husky/lefthook vs social norms. Over-strict lint on WIP commits can annoy; many teams lint on PR title / squash message instead.

**Scope tradeoff:** scopes like `retrieval`, `prompts`, `evals`, `api` make changelogs useful; inventing 40 scopes creates thrash.

---

## Necessity

### Failure modes if skipped
1. **“update stuff” history** — cannot reconstruct which commit broke nDCG or raised cost/query.  
2. **Week 23 STAR stories suffer** — interview narratives need commit archaeology of failures and fixes.  
3. **Prompt/changelog opacity** — product asks “what changed in the assistant this week?” and the answer is a git blame scavenger hunt.  
4. **Accidental major bumps** or silent breaking OpenAPI changes without `!` / BREAKING CHANGE.  
5. **Release tooling theater** — `semantic-release` configured but commits are free-form → empty or wrong releases.

### Spec guidance worth internalizing
- Prefer **multiple commits** when a change spans types (don’t stuff `feat`+`fix`+`docs` into one).  
- Proceed as if already released even in 0.x—someone is consuming the software.  
- Reverts: use `revert` type + `Refs:` footers; tooling authors define SemVer impact.

---

## Industry Practice

### Common (weak)
- Inconsistent messages; giant squash commits titled “address comments.”  
- No link between commits and eval metric deltas.  
- Mixing unrelated prompt, retrieval, and infra changes in one commit.

### Strong / senior
- Conventional Commits + PR templates.  
- Separate `feat(prompts)` from `feat(retrieval)` from `chore(deps)`.  
- Link **eval metric deltas** and flag names in the body.  
- Protect main with required checks; optionally commitlint on PR title.  
- `CHANGELOG.md` or GitHub Releases generated from commits.  
- Deliberate squash vs merge-commit policy documented in CONTRIBUTING.

### AI / prompt commit-type debate
Open question in AI systems: should prompt-template edits be:
- `feat(prompts): …` — user-visible behavior change (often correct for product impact)  
- `fix(prompts): …` — correcting regressions  
- dedicated custom type `prompt:` — highlights prompt ops in changelog but **won’t** auto-bump SemVer unless configured  
- `chore(prompts):` — understates user impact  

**Senior practice:** treat user-visible prompt/behavior changes as `feat`/`fix` with scope `prompts`; reserve custom types only if release tooling is taught to map them. Document the team rule in CONTRIBUTING so AI commit generators do not invent types.

### RAG chatbot Week 3 application
Good:
```
fix(retrieval): correct RRF weight for sparse channel
feat(prompts): add citation instruction block to system template
test(evals): add golden cases for empty-retrieval path
chore(docker): shrink runtime stage to python:3.12-slim
```
Bad:
```
updates
WIP
fix stuff
AI: improved the system
```

---

## Concrete Scenario

**Conventional Commits specification v1.0.0**  
https://www.conventionalcommits.org/en/v1.0.0/  

Canonical rules, SemVer mapping, FAQ on squash workflows, reverts, and multiple types.

**Semantic Versioning**  
https://semver.org/  

**Tooling examples (legal OSS docs):**
- commitlint conventional config: https://github.com/conventional-changelog/commitlint  
- conventional-changelog / guides: https://conventional-changelog.js.org/  

**YouTube search seed (GitHub Universe / tooling talks):**  
https://www.youtube.com/results?search_query=conventional+commits+github+universe  

---

## Open Questions

- Should prompt-template edits be `feat` or a dedicated `prompt` type for AI systems?  
- AI commit-message generators: net useful or a source of confident nonsense that pollutes SemVer?  
- For internal services without public SemVer consumers, is Conventional Commits still worth it (changelog + archaeology) or overkill?  
- How should eval-harness-only changes version relative to the API (`feat(evals)` never bumps service API version—monorepo release rules)?

---

## Sources

- https://www.conventionalcommits.org/en/v1.0.0/  
- https://semver.org/  
- https://conventional-changelog.js.org/  
- https://github.com/conventional-changelog/commitlint  
- https://www.youtube.com/results?search_query=conventional+commits+github+universe  
