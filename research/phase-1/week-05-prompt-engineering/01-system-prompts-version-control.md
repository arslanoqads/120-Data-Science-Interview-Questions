# 01 — System prompts in version control, registries, and canary

> Week 5 concept research (deep). Legal sources only.

---

## Fundamentals

A **system prompt** (OpenAI `developer` message / Responses `instructions`; Anthropic top-level `system`) is durable product behavior: role, safety boundaries, tool policy, output contracts, and domain rules. Treating it as ephemeral copy-paste in application code causes silent regressions, unreproducible evals, and cache thrash (Week 4: any byte change at position N invalidates the prefix after N).

OpenAI’s 2026 prompting guide states the operational rule: **store production prompts in application code**, with typed inputs, code review, tests, and the normal deployment process. Reusable API prompt objects (`v1/prompts`) are being deprecated (creation de-emphasized June 3, 2026; shutdown scheduled November 30, 2026). Anthropic’s Agent SDK makes the same product-surface claim from the other direction: you choose a **preset** (`claude_code`), **append** to that preset, or send a **fully custom string**—and CLAUDE.md is injected as conversation context, *not* silently merged into an unversioned blob.

### What “version control” means for prompts

Prompts need the same archaeology as code:

| Artifact | Role |
|----------|------|
| **Immutable snapshot** | Exact bytes the model saw (or the template + fill schema that produced them) |
| **Identity** | `prompt_id` + `prompt_version` (semver, date stamp, or commit hash) logged on every trace |
| **Changelog** | Why it changed, expected behavioral delta, linked eval run IDs, rollback pointer |
| **Promotion pointer** | `dev` / `staging` / `production` / `canary` labels that move without rewriting history |
| **Review gate** | PR or owners-only tag move; eval diffs, not just prose |

Keep-a-Changelog style entries work: date, author, intent, eval IDs, expected deltas, rollback hash. Conventional Commits can carry a `prompt:` type or `feat(prompt):` scope (Week 3 commit debate)—the important part is **searchable history**, not the token.

### Git vs prompt registries

**Git (markdown/YAML/JSON next to the feature).** Diffable in PRs. Local repro is trivial. OpenAI’s 2026 recommendation for new work: `prompts/supportReply.ts` (or `.md` + typed builder), fixtures, eval checks in CI, feature flags for staged releases.

**Prompt registry / hub.** LangSmith: every `push_prompt` is an immutable **commit hash**; reserved `staging` / `production` **commit tags** are environment pointers; `client.pull_prompt("joke-generator:production")` resolves the pointer without a code change. Owners-only mode restricts who can promote tags. Webhooks fire on commit (CI, git mirror). Public Hub prompts are **unverified user content**—treat as untrusted templates.

Langfuse: every save is an immutable **version** (`1, 2, 3…`); **labels** (`production`, `latest`, custom `canary` / tenant) point at exactly one version. Default fetch serves `production`. Rollback = move the label. Protected labels stop members from moving `production`. Langfuse is explicit that **weighted canary is not a built-in router**—you compose it in application code (two labels, random split, `langfuse_prompt` attribution on traces).

**Hybrid.** Registry for hot-reload + UI; webhook mirrors every version into git for review/backup. Langfuse’s own CI/CD writeup: registry remains deploy source of truth; git is the review/backup plane. Inverse hybrid (git source, registry cache) matches OpenAI’s deprecation direction and regulated audit stories.

### Canary, A/B, rollback

A prompt edit has the **blast radius of a deploy** and historically skipped every safeguard (Langfuse: no review, no tests, no staged rollout). A complete pipeline:

1. **Version** — immutable snapshot + diff + author.  
2. **Validate** — golden dataset + scores (LLM-as-judge and/or code).  
3. **Gate** — CI fails on regression; human approves production pointer.  
4. **Roll out** — serve candidate to a fraction of live traffic (`canary` label or feature flag).  
5. **Observe** — quality, cost, latency, **cache hit rate** per version (Week 4).  
6. **Roll back** — repoint label / flip flag; no model-weight redeploy.

Canary is **application-level**: `if hash(user_id) % 100 < 5: pull("support:canary") else pull("support:production")`. Attribute every generation to the exact version. A 100% cutover of a long system prompt is an **intentional cold-cache event**—budget the write premium and TTFT spike.

Agent SDK nuance: swapping from `claude_code` preset to a custom string is not a small changelog line—it **drops** tool guidance and safety instructions the preset included. Treat preset↔custom as a major version.

### Separate static system text from runtime context

Version the **template and static instructions**, not the fully rendered string that includes today’s date, user tier, and retrieved docs. Runtime fill belongs in user/tagged blocks so (a) the versioned artifact stays reviewable, (b) the cache prefix stays stable (Week 4).

---

## Alternatives & Tradeoffs

| Approach | Pros | Cons | When |
|----------|------|------|------|
| Inline strings in code | Simple | No review trail; hard A/B; merge conflicts with logic | Throwaway only |
| Markdown/YAML in git + changelog | Diffable, reviewable, cheap, OpenAI-aligned | Manual promotion; PM bottleneck | Default for FDE / take-homes |
| LangSmith Hub / Langfuse labels | UI, analytics, env pointers, webhooks | Vendor lock-in; pull latency unless cached; public hub is untrusted | Multi-editor teams; hot reload |
| DB-only remote prompts | Instant edit | Weak review; local repro fails; audit gaps | Avoid as sole source |
| OpenAI API prompt objects | Historical convenience | **Deprecated 2026** — migrate to code | Legacy only |
| Fine-tune instead of system prompt | Strong default behavior | Costly; slower iteration; still needs some system text | Stable voice at scale after prompt plateau |
| Feature-flag canary in-app | Works with git *or* registry | You own split math and attribution | Required for high-blast-radius prompts |

**Cache coupling:** bumping the system prompt is an org-wide miss until TTL. Pair changelog entries with expected `cache_creation_*` / `cached_tokens` impact.

---

## Necessity

System prompts encode **policy and UX**. Without versioning:

1. **Incident archaeology fails** — “who changed the refund policy?” has no answer.  
2. **Eval baselines drift** — yesterday’s golden set is scoring a different contract.  
3. **Cache thrash** — unchecked edits invalidate prefixes (Week 4 failure mode 2).  
4. **Regulated audit gap** — instruction changes are as material as config/code in many industries.  
5. **Unsafe hot-reload** — a PM edits production copy; agents gain a new tool policy with no review.  
6. **Preset footgun** — custom Agent SDK prompt silently drops Claude Code safety text.

Failure mode specific to RAG/agents: a one-line “be more helpful” edit that authorizes extra tools or loosens citation rules ships to 100% of sessions that can retrieve untrusted docs.

---

## Industry Practice

### Common (weak)
- System prompt in a FastAPI handler f-string.  
- “Latest” pulled from a hub with no pin.  
- Changelog = git commit message “tweak prompt.”  
- No `prompt_version` on traces.  
- 100% cutover on Friday afternoon.

### Strong / senior
- One prompt file (or Hub prompt) per product surface; IDs like `support.system.2026-03-12` or commit hashes.  
- CI: forbidden-pattern lint (unescaped user content in system files), golden evals on PR, required changelog entry.  
- Promote through environments with the same gates as config (LangSmith Promote UI; Langfuse protected `production` label).  
- Log `prompt_version` (and registry commit/label) on every inference trace.  
- Cache pulled registry prompts in-process (TTL); LangSmith `pull_prompt()` is an HTTP call.  
- Canary 5–10% with per-version quality **and** cache-hit dashboards; rollback is a pointer move.  
- OpenAI: typed builders, not string soup; feature flags for staged releases.  
- Anthropic Agent SDK: prefer `preset + append` over rewriting the whole system string when you still want coding-agent safety.

### RAG chatbot Week 5 application
Version: system policy + tool policy + static style examples as `prompts/rag_answer_vN`. Do **not** version-control per-query retrieved chunks. Pin `prompt_version` in the Week 4 client’s trace metadata. Treat a production pointer move as a deploy: eval gate + canary + cache-cost note in the changelog.

---

## Concrete Scenario

**Prompt learning loop (AI Engineer).** SallyAnn DeLucia & Fuad Ali frame production prompt work as an evaluation-driven loop: scorers / LLM-as-judge produce feedback that updates the system prompt iteratively. That workflow only works if each candidate is **addressable, comparable, and recorded**—i.e., versioned with changelog linkage to eval metrics.

URL: https://ai.engineer/talks/build-a-prompt-learning-loop

**LangSmith promotion.** Commits are immutable; `staging` and `production` are reserved tags moved through a promotion modal that shows which commit will be replaced. Rollback walks environment history. Code pulls `name:production` so the binary does not change.

URL: https://docs.langchain.com/langsmith/manage-prompts

**Langfuse canary composition.** Two labels (`production`, `canary`); application serves 90/10; every generation linked via `langfuse_prompt`; promotion is moving `production` onto the winner. Weighted split is **your** code (as of their July 2026 CI/CD guide).

URL: https://langfuse.com/resources/engineering/prompt-cicd

**OpenAI code-managed prompts.** Official prompting page: keep production prompts in versioned helpers, typed parameters, tests/evals on publish, git + PR + flags for rollout—because API prompt objects are going away.

URL: https://developers.openai.com/api/docs/guides/prompt-engineering

Companions: https://code.claude.com/docs/en/agent-sdk/modifying-system-prompts · https://claude.com/blog/best-practices-for-prompt-engineering · https://docs.langchain.com/langsmith/prompt-engineering-quickstart · https://langfuse.com/docs/prompt-management/features/prompt-version-control

---

## Open Questions

1. Should prompt registries be the source of truth with git as export, or git as source with registry as cache? OpenAI’s 2026 deprecation pushes git/code; PM-led orgs still want UI source.  
2. How to changelog multilingual / multi-brand variants without combinatorial explosion (matrix of locale × brand × surface)?  
3. Minimum eval suite that must pass before a system-prompt merge (instruction suite vs tone vs cache-hit SLO)?  
4. How to version mid-conversation Anthropic system messages separately from the top-level `system` field?  
5. Canary % vs cache: does a 5% canary of a long prefix fragment `prompt_cache_key` routing enough to hide the true cost of the candidate?  
6. Agent SDK: should `append` snippets be versioned as their own artifacts, or always snapshotted with the preset’s published hash?

---

## Sources

- https://developers.openai.com/api/docs/guides/prompt-engineering  
- https://developers.openai.com/api/docs/guides/prompting  
- https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices  
- https://code.claude.com/docs/en/agent-sdk/modifying-system-prompts  
- https://claude.com/blog/best-practices-for-prompt-engineering  
- https://www.anthropic.com/news/prompt-engineering-for-business-performance  
- https://docs.langchain.com/langsmith/manage-prompts  
- https://docs.langchain.com/langsmith/prompt-engineering-quickstart  
- https://langfuse.com/docs/prompt-management/overview  
- https://langfuse.com/docs/prompt-management/features/prompt-version-control  
- https://langfuse.com/docs/prompt-management/data-model  
- https://langfuse.com/resources/engineering/prompt-cicd  
- https://ai.engineer/talks/build-a-prompt-learning-loop  
- https://ai.engineer/talks/how-claude-code-works  
- https://keepachangelog.com/en/1.1.0/  
