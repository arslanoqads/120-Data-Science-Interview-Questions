# 04 — Security & privacy patterns beyond prompt injection

> Week 29 — AI Safety, Ethics, and Adversarial Testing  
> Research notes (raw).

---

## Fundamentals

Week 5 taught **prompt injection** (OWASP LLM01). Production incidents and the broader OWASP GenAI LLM Top 10 show that injection is necessary but **not sufficient**. Two FDE-critical siblings:

1. **Sensitive Information Disclosure (LLM02)** — PII, secrets, system prompts, hidden context, or training/retrieval data appear in outputs (or reasoning channels).  
2. **Excessive Agency (LLM03 in 2026 ranking)** — tools do too much: exfiltrate data via outbound calls, modify state, or chain actions without adequate authorization.

Privacy / security patterns beyond “sanitize the prompt”:

| Pattern | Failure mode | Control sketch |
|---------|--------------|----------------|
| **Output PII leakage** | Model echoes SSRN / MRN / email from context | DLP on outputs; minimize context; redaction |
| **Retrieval exfiltration** | Indirect injection in docs → “send secrets to URL” | Context isolation; link allowlists; Dual LLM |
| **Tool-call exfiltration** | `email.send` / `http.post` args carry secrets | Tool allowlists; arg schemas; egress proxies |
| **Hidden context exposure** | System prompt / tool schemas leaked | Least-privilege prompts; canary tokens in suite |
| **Cross-tenant bleed** | Wrong `thread_id` / memory namespace | Week 19 authZ + Week 25 isolation |
| **Logging side channels** | Traces store raw prompts with secrets | Redacted telemetry; retention policy |

Chip Huyen’s agents / platform writing stresses tool outputs and side effects as first-class design — privacy engineering must sit on the **tool boundary**, not only the chat box (*Agents*; *GenAI Platform*).

---

## Alternatives & Tradeoffs

| Control stack | Upside | Downside |
|---------------|--------|----------|
| Prompt-only “never reveal PII” | Cheap | Unreliable under injection |
| Output regex DLP | Catches common patterns | Misses novel encodings; false positives |
| Tokenization / vault before LLM | Strong for known PII fields | Breaks UX if overused |
| Dual LLM / privileged planner | Limits untrusted content power | Latency, complexity (Willison pattern) |
| No tools / human-only side effects | Small blast radius | Weak product |
| **Capability-scoped tools + egress policy + output DLP** | Defense in depth | Needs Week 14 + 19 discipline |

| Exfil path | Prefer |
|------------|--------|
| User-visible answer | Output DLP + context minimization |
| Tool HTTP body | Egress allowlist + arg validation |
| Retrieval store write | Separate write roles; no secret fields |

---

## Necessity

If you only harden against direct jailbreaks:

- Attacker pastes “ignore previous” into a shared Confluence page (indirect injection) and the agent posts customer PII to an external webhook.  
- Support bot includes prior-ticket PHI in a summary emailed externally.  
- Debug traces in an observability vendor contain API keys from tool results.  
- Model politely refuses bomb recipes but happily dumps `.env` contents present in RAG.  
- Excessive agency: “cancel all orders” succeeds because the tool trusted the LLM’s intent string.

Regulated customers treat these as **data breaches and change-control failures**, not “model quirks.”

---

## Industry Practice

- **Common:** system prompt “don’t leak PII”; tools wrapped with raw HTTP; logs full fidelity forever.  
- **Strong:** classify data (public / internal / PII / secrets); strip or vault before prompt pack; schema-validate tool args; deny-by-default egress; canary secrets in adversarial suite (Promptfoo PII / SSRF plugins; Garak leakage probes); map findings to OWASP LLM02/LLM03.  
- **FDE bar:** threat-model **each tool**; show authZ checks independent of the LLM (Week 19); demo a failed exfil attempt in the scheduled suite; document residual risk when browsing tools exist.

Simon Willison’s design patterns for securing LLM agents and Dual LLM remain practical references alongside OWASP cheat sheets.

---

## Concrete Scenario

**OWASP GenAI — LLM Top 10 2026** (official project resource):  
https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/

The 2026 list keeps **Prompt Injection** and **Sensitive Information Disclosure** at the top and elevates **Excessive Agency**, reflecting incident-weighted reality for tool-using systems. An FDE reading for flagship agents: budget adversarial tests for (a) direct/indirect injection, (b) PII/secret disclosure in answers and traces, and (c) tool misuse / exfiltration — not injection alone. Pair with Promptfoo agent/tool plugins and Week 14 side-effect discipline.

---

## Open Questions

- Should tool arguments be signed by a privileged planner so the LLM cannot forge egress?  
- How much of PII leakage is solved by better RAG chunk hygiene vs model behavior?  
- Are canary tokens in system prompts still useful once models detect them?  
- Where should DLP live — gateway, app, or vendor safety API?  
- How do multi-agent handoffs (Week 25 isolation) create new exfil paths?

---

## Sources

- https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/  
- https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html  
- https://simonwillison.net/2023/Apr/25/dual-llm-pattern/  
- https://simonwillison.net/2025/Jun/13/prompt-injection-design-patterns/  
- https://www.promptfoo.dev/docs/red-team/  
- https://github.com/NVIDIA/garak  
- https://huyenchip.com/2025/01/07/agents.html  
- https://huyenchip.com/2024/07/25/genai-platform.html  
- https://www.nist.gov/itl/ai-risk-management-framework  
- https://developers.openai.com/api/docs/guides/moderation  
