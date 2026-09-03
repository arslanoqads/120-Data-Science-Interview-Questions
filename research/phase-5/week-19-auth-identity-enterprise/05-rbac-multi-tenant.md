# 05 — RBAC for multi-tenant AI systems

> Week 19 — tenant walls plus in-tenant roles; PEP/PDP; agents as first-class authorizees.  
> Login tokens: [01](01-oauth2-oidc.md). Keys: [03](03-api-keys-service-accounts-federation.md). Region: [04](04-data-residency.md). Design sketch: [00](00-week-overview.md).

---

## Fundamentals

**Multi-tenancy** = one platform serving many customers (**tenants**) with **isolation**. **RBAC** = permissions via **roles** (Admin, Analyst, Viewer, ConnectorAdmin, AgentApprover) assigned to **principals** (users, groups, service accounts, API keys).

SaaS AI almost always needs **two axes**:

1. **Tenant isolation** — Tenant A must never read Tenant B’s documents, embeddings, prompts, threads, traces, or keys.  
2. **In-tenant RBAC** — inside Tenant A, who can manage connectors, run agents, view logs, approve tool actions?

A user can be Admin in Tenant A and Viewer in Tenant B (consultancies, multi-org IdPs). The token must not collapse that to a global Admin.

### Authorization architecture (PEP / PDP)

AWS Prescriptive Guidance for multi-tenant SaaS APIs ([welcome](https://docs.aws.amazon.com/prescriptive-guidance/latest/saas-multitenant-api-access-authorization/welcome.html)):

| Component | Job |
|-----------|-----|
| **PEP** (Policy Enforcement Point) | Gateway or service middleware: extract token, call PDP, **allow/deny**, never “UI only” |
| **PDP** (Policy Decision Point) | Evaluates RBAC/ABAC (OPA/Rego, Cedar / Amazon Verified Permissions, custom) |
| **PIP** (optional) | Extra attributes (sensitivity of doc, region, spend tier) |

**Deny by default.** Unknown tenant claim → 401/403, not “empty results that leak existence” unless that is an explicit anti-enumeration choice.

OPA docs (legal, official): [openpolicyagent.org](https://www.openpolicyagent.org/docs/latest/).

### Isolation patterns

| Pattern | Infra | Isolation | Cost |
|---------|-------|-----------|------|
| **Pool** | Shared cluster/DB; `tenant_id` everywhere | Software (RLS, IAM prefix, vector filter) | Lowest |
| **Silo** | Per-tenant account/cluster/DB | Stronger; easier residency | Highest |
| **Bridge** | Mix by tier | “Enterprise” silo, SMB pool | Medium complexity |

Pool is the default FDE prototype; silo appears when residency, noisy neighbor, or “bring your own cloud” shows up. AWS: [pool-model multi-tenancy with Bedrock AgentCore](https://aws.amazon.com/blogs/machine-learning/shared-infrastructure-isolated-tenants-pool-model-multi-tenancy-with-amazon-bedrock-agentcore/) (tier → tenant → user claims in JWT). Platform: [GenAI Lens multi-tenant scenario](https://docs.aws.amazon.com/wellarchitected/latest/generative-ai-lens/multi-tenant-generative-ai-platform-scenario.html).

### Claims and every store

After OIDC/SAML, the **session or access token** should carry:

- `tenant_id` (stable internal id, not display name)  
- `sub` (user)  
- `roles` or mapped groups  
- optional `region` / `tier`

**Every** DB query, cache key, vector filter, object prefix, and trace attribute must be tenant-scoped. Object IDs are not a security boundary (`/docs/uuid` without tenant check is IDOR).

### RBAC vs ABAC vs ReBAC

| Model | Flexibility | Complexity |
|-------|-------------|------------|
| Pure RBAC | Simple | Role explosion (`EU_Finance_Read_PII_AgentApprove_…`) |
| **ABAC** (dept, region, sensitivity, residency) | Fine-grained | Harder to reason; need PIP |
| RBAC + ABAC hybrid | Practical enterprise | Need a real PDP |
| **ReBAC** (Zanzibar-style relations) | Sharing graphs (“this folder”) | Ops + modeling cost |

For **agents:** authorize **each tool invocation** with **user + tenant + action + resource**, not merely “they opened the WebSocket.” The LLM proposing SQL or a REST body does not grant permission — the **PEP** does.

### Customer-admin trap

Tenant admins may invite users, mint **virtual API keys**, and map SSO groups. They must **not** be able to:

- Set `tenant_id` on writes to another tenant  
- Disable isolation filters  
- Read platform provider keys  
- Expand their token `aud` to internal admin APIs  

Platform operators use a **separate** IdP app / break-glass role with audit.

### Testing isolation

The FDE-quality bar is **automated** tests: Token A + query designed for B’s namespace → **always deny**. Include RAG, cache get, trace export, and tool gateway. This is more important than a pretty roles UI.

---

## Alternatives & Tradeoffs

| Approach | Pros | Cons |
|----------|------|------|
| `tenant_id` column + role enum in app `if` | Ships | Scattered; missed path = leak |
| Central PDP (OPA/Cedar) | One policy language; testable | Extra latency; policy ops |
| DB RLS as backstop | Defense in depth | App still must pass tenant; migrations painful |
| Silo per tenant | Easy questionnaires | Cost; slow features |
| Pool + strict prefixing + tests | SaaS default | Discipline; one bug is existential |
| UI-only RBAC | Pretty | Trivial privilege escalation via API |

---

## Necessity

Missing `tenant_id` on a **vector query** → **cross-tenant RAG leakage** (career-ending class of bug).

**UI-only RBAC** (hiding buttons) without API enforcement → privilege escalation with curl.

**Shared semantic cache** without tenant (and sometimes user) in the key → answer leakage; Week 20 will want that cache for latency — **this week forbids unkeyed cache**.

**Agent with platform SA** → authorization theater; CRM ACLs never run.

**IDOR** on thread IDs → prompt history of another customer.

---

## Industry Practice

**Common:** `tenant_id` column + role enum; JWT `org_id` from Auth0 Organizations / Okta orgs; gateway checks membership.

**Strong:**

- Central PDP; deny-by-default; **integration tests** for cross-tenant access on every store.  
- Optional per-tenant encryption keys for high tiers.  
- Rate limits and **budgets per tenant** (identity of the key — file [03](03-api-keys-service-accounts-federation.md)).  
- Audit log: tenant, user, action, resource, tool name, decision.  
- Pool model with prefixing as in Bedrock AgentCore guidance.  
- Generated SQL / tool args: allowlist of tables; PEP still applies **row** filters.  
- Approvals for high-risk tools: role-based **or** ReBAC owners — pick one and document.

Okta/Auth0 org features are vendor implementations of tenant = organization; still **your** PEP must enforce.

---

## Concrete Scenario (URL)

**AWS Prescriptive Guidance — Multi-tenant SaaS authorization and API access control** (PDP/PEP, RBAC/ABAC, OPA, Verified Permissions):  
https://docs.aws.amazon.com/prescriptive-guidance/latest/saas-multitenant-api-access-authorization/welcome.html  

**Pool-model multi-tenancy with Bedrock AgentCore** (tier → tenant → user in JWT):  
https://aws.amazon.com/blogs/machine-learning/shared-infrastructure-isolated-tenants-pool-model-multi-tenancy-with-amazon-bedrock-agentcore/  

**GenAI Lens — multi-tenant generative AI platform:**  
https://docs.aws.amazon.com/wellarchitected/latest/generative-ai-lens/multi-tenant-generative-ai-platform-scenario.html  

**OPA documentation:**  
https://www.openpolicyagent.org/docs/latest/  

**Auth0 Organizations** (B2B tenant as org — still enforce in your API):  
https://auth0.com/docs/manage-users/organizations  

**Okta — OAuth/OIDC** (groups/claims into your RBAC):  
https://developer.okta.com/docs/concepts/oauth-openid/  

**YouTube — OktaDev OIDC** (claims you will map into roles):  
https://www.youtube.com/watch?v=996OiexHze0  

---

## Open Questions

- Who approves high-risk agent actions — role-based approvers, or per-resource owners (ReBAC)?  
- How to expose “customer admin” RBAC without allowing them to break isolation?  
- Authorization for **generated** SQL/tool args (LLM proposes; PEP must still enforce).  
- Should traces used for eval (Week 16–17) be a separate sensitivity class inside the tenant (admins vs model trainers)?  
- Multi-tenant **MCP**: is the MCP session tenant-bound, or can one host multiplex tenants safely?

---

## Sources

- https://docs.aws.amazon.com/prescriptive-guidance/latest/saas-multitenant-api-access-authorization/welcome.html  
- https://aws.amazon.com/blogs/machine-learning/shared-infrastructure-isolated-tenants-pool-model-multi-tenancy-with-amazon-bedrock-agentcore/  
- https://docs.aws.amazon.com/wellarchitected/latest/generative-ai-lens/multi-tenant-generative-ai-platform-scenario.html  
- https://www.openpolicyagent.org/docs/latest/  
- https://auth0.com/docs/manage-users/organizations  
- https://developer.okta.com/docs/concepts/oauth-openid/  
- https://datatracker.ietf.org/doc/html/rfc8693  
- https://www.youtube.com/watch?v=996OiexHze0  
