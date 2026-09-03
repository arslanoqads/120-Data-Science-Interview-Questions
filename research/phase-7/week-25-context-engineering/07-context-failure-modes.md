# 07 — Context failure modes (stale, poisoning, lost handoffs)

> Week 25 — Context Engineering as a discipline  
> Research notes (raw).  
> Pair with Week 9 RAG failure taxonomy — same *logging* spirit, different locus.

---

## Fundamentals

Week 9 classifies **RAG** failures (recall / rank / ground). Week 25 classifies **context** failures — anything that makes the assembled window wrong, harmful, or incomplete even when components “ran.”

### Syllabus trio (required)

| Mode | Definition | Typical locus |
|------|------------|---------------|
| **Stale context** | Window or memory reflects outdated world/docs/policy | Memory store; cached RAG; old checkpoint resumed blindly |
| **Context poisoning** | Bad or malicious content enters and is repeatedly trusted | Hallucinated “facts”; indirect prompt injection; tainted memory writes |
| **Lost context across handoffs** | Constraints/evidence fail to cross agent or phase boundaries | Summary omissions; dropped fields; new thread without brief |

### Breunig four (industry taxonomy to map as subtypes)

Drew Breunig, *How Long Contexts Fail* (2025-06-22):

1. **Context Poisoning** — hallucination/error enters context and is reused.  
2. **Context Distraction** — context so long the model over-attends history vs training (agents repeating past actions; Gemini Pokémon anecdote ≳100k).  
3. **Context Confusion** — superfluous tools/docs trigger low-quality choices.  
4. **Context Clash** — contradictory spans derail reasoning.

LangChain’s context-engineering post amplifies these as motivation for write/select/compress/isolate.

### Position / packing failures

**Lost in the Middle** (Liu et al., arXiv:2307.03172, TACL): multi-document QA and KV retrieval show U-shaped performance — mid-context evidence underused; longer contexts can hurt. This is the packing cousin of “lost handoff”: gold was *present* but effectively lost to attention.

Anthropic **context rot**: as tokens grow, recall from context degrades — continuum toward distraction.

### Injection as poisoning

OWASP LLM Prompt Injection Cheat Sheet: **Context Poisoning** — injecting false information into the agent’s working memory; also Thought/Observation forging and tool manipulation. Simon Willison: indirect injection via emails/pages that become context; Dual LLM and context-minimization patterns as defenses. Chip Huyen: prompt injection as social engineering against models; worse when tools can act (*GenAI Platform*; *Agents*).

### Portfolio log schema (mirror Week 9)

```text
incident_id, session_id, handoff_id?,
mode: stale|poison|lost_handoff|distraction|confusion|clash|lost_in_middle,
layer: policy|tools|rag|history|memory|handoff,
evidence: snippet_hash, token_count, position?,
remediation: compact|isolate|re-retrieve|reset_thread|ro_memory|...
```

---

## Alternatives & Tradeoffs

| Taxonomy choice | Pros | Cons |
|-----------------|------|------|
| Syllabus 3 only | Teachable; maps to build tasks | Misses distraction/confusion vocabulary |
| Breunig 4 only | Industry blog resonance | Under-labels staleness & handoff loss |
| **3 primary + Breunig/LITM subtypes** (recommended) | Coverage + portfolio clarity | Slightly heavier labeling |
| Collapse all to “hallucination” | Easy | Wrong owners |

| Remediation style | Risk |
|-------------------|------|
| Always compact | May entrench poison into the summary |
| Always reset thread | Loses good work; user friction |
| Re-retrieve + pin policy | Fixes stale; needs versioned corpus |
| Quarantine + Dual LLM | Security win; product complexity |

---

## Necessity

Without a failure taxonomy:

- Poisoned memory is “fixed” by adding more prompt rules — poison remains in the store.  
- Stale policy chunks score high on faithfulness (faithful to old text) while being wrong vs production — same trap as Week 9 citation drift.  
- Multi-agent demos fail intermittently because briefs omit ACL constraints — labeled as “model dumb.”  
- Million-token windows hide distraction until agents loop.  
- Security incidents are filed as jailbreaks when the path was **indirect context injection**.

Documenting modes like Week 9 is what makes the elective shippable in a portfolio.

---

## Industry Practice

- **Common:** screenshot the bad answer; tweak temperature; clear chat.  
- **Strong:** fault-injection suite — plant mid-context needles; inject conflicting tool results; write a bad memory deliberately; drop `constraints` from a handoff fixture; assert detector labels. Pair with token timelines.  
- **FDE bar:** customer RCA uses the taxonomy; distinguishes stale RAG (data) vs poison (trust) vs lost handoff (orchestration); ties to OWASP when tools + untrusted content exist; refuses to ship shared writeable memory without audit versions.

Remediation cheatsheet:

| Mode | First fix |
|------|-----------|
| Stale | Version pins; re-retrieve; expire memories |
| Poison | Reset/quarantine span; read_only memory; Dual LLM |
| Lost handoff | Handoff schema + summary eval |
| Distraction | Compact earlier; isolate workers |
| Confusion | Shrink tool/doc set; RAG over tools |
| Clash | Reconciliation node; don’t merge raw |
| Lost-in-middle | Reorder; reduce *k*; pointwise cite |

---

## Concrete Scenario

**Drew Breunig — How Long Contexts Fail**  
https://www.dbreunig.com/2025/06/22/how-contexts-fail-and-how-to-fix-them.html  
Follow-up: https://www.dbreunig.com/2025/06/26/how-to-fix-your-context.html  
Talk: https://www.youtube.com/watch?v=-iRQxHxYqak  

Defines poisoning/distraction/confusion/clash with agent examples (including long-context agents repeating history instead of planning). Primary public narrative for “context fails before the window is full.”

**Liu et al. — Lost in the Middle**  
https://arxiv.org/abs/2307.03172  

Controlled evidence that presence ≠ use — foundational for packing/handoff “lostness.”

**OWASP + Willison** — injection → working-memory poison  
https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html  
https://simonwillison.net/2023/Apr/25/dual-llm-pattern/  

---

## Open Questions

- Automatic classifiers for Breunig modes from traces?  
- Does compaction help distraction but risk **summarizing poison into canon**?  
- Metrics: should “constraint survival rate across handoff” be a standard agent eval?  
- How do long-context training improvements shift LITM curves in 2026+ models?  
- Unified taxonomy across Week 9 (RAG) and Week 25 (context) for one error-analysis codebook?

---

## Sources

- https://www.dbreunig.com/2025/06/22/how-contexts-fail-and-how-to-fix-them.html  
- https://www.dbreunig.com/2025/06/26/how-to-fix-your-context.html  
- https://www.youtube.com/watch?v=-iRQxHxYqak  
- https://www.langchain.com/blog/context-engineering-for-agents  
- https://arxiv.org/abs/2307.03172  
- https://doi.org/10.1162/tacl_a_00638  
- https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents  
- https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html  
- https://simonwillison.net/2023/Apr/25/dual-llm-pattern/  
- https://simonwillison.net/2025/Jun/13/prompt-injection-design-patterns/  
- https://huyenchip.com/2024/07/25/genai-platform.html  
- https://huyenchip.com/2023/08/16/llm-research-open-challenges.html  
- https://platform.claude.com/docs/en/managed-agents/memory  
