# 03 — API keys, service accounts, and federated identity

> Week 19 — machine authentication for AI platforms (not human SSO).  
> Humans: [01](01-oauth2-oidc.md) / [02](02-saml-legacy-sso.md). Tenancy of keys: [05](05-rbac-multi-tenant.md).

---

## Fundamentals

Three **machine** patterns show up in every production LLM system. Mixing them is how keys leak into browsers and how agents bypass user ACLs.

### 1. API key

A **static secret** (header `x-api-key`, `Authorization: Bearer sk-…`, query param — query params are a mistake). Identifies a **project, tenant, or customer integration**, not a human. Easy to mint; hard to attribute to a person; leak = full power until rotated or gated.

**Where they belong:** customer calling **your** public API; **virtual keys** in a gateway; never as the only “login” for a UI (overview [00](00-week-overview.md)).

**LiteLLM / AI gateways** often give tenants **virtual keys** while the gateway holds **provider** keys in a vault. That is API-key UX + centralized custody ([LiteLLM virtual keys](https://docs.litellm.ai/docs/proxy/virtual_keys)). Scope virtual keys: models allowed, RPM, budget, tenant id.

### 2. Service account (workload identity object)

A **first-class identity for software**: GCP service account, AWS IAM role (instance/task/pod identity), Azure managed identity / workload identity. Authenticates with **short-lived tokens** from the metadata service, STS, or projected SA tokens — not a password.

**Key files** (GCP JSON keys, long-lived IAM users) exist and are **discouraged**: they leak via Git, Docker layers, and chat logs.

Ideal for: backend calling Vertex / Bedrock / BigQuery / S3; CI deployers (with federation, below).

### 3. Federated identity / workload identity federation

A workload that **already has** an OIDC token (GitHub Actions, GitLab, GKE, EKS IRSA, Kubernetes projected SA) **exchanges** it for cloud credentials. **No long-lived JSON keys.**

GCP: [Workload Identity Federation](https://cloud.google.com/iam/docs/workload-identity-federation) — attribute mapping from external `sub`/`aud` to a Google SA.  
AWS: IAM OIDC identity providers + `AssumeRoleWithWebIdentity` (EKS IRSA, GitHub OIDC).  
Azure: federated credentials on Entra apps.

Same idea in **product** space: customer’s IdP federates **users** into your app (SSO). For **agents**, **on-behalf-of (OBO)** / token exchange ([RFC 8693](https://datatracker.ietf.org/doc/html/rfc8693)) so tools see the **user**, not a god-mode service account.

AWS write-up: [OBO token exchange for multi-tenant agents (Bedrock AgentCore Gateway)](https://aws.amazon.com/blogs/machine-learning/implement-on-behalf-of-token-exchange-for-multi-tenant-agents-with-amazon-bedrock-agentcore-gateway/). Platform-level: [Well-Architected GenAI Lens — multi-tenant platform](https://docs.aws.amazon.com/wellarchitected/latest/generative-ai-lens/multi-tenant-generative-ai-platform-scenario.html) (virtual keys, OAuth, Secrets Manager).

### Decision table (who presents what)

| Caller | Present | Must not present |
|--------|---------|------------------|
| Browser user | OIDC session / user access token | Provider `sk-`, cloud JSON key |
| Customer backend | Your API key or client-credentials token | Your **provider** key |
| Your API pod | Workload identity / SA | User passwords |
| CI pipeline | OIDC federation to cloud | Static cloud keys in `secrets.GITHUB_TOKEN` extras |
| Agent tool hop | Exchanged OBO token (user+tenant+scope) | Unconstrained platform SA into CRM |

### Client credentials vs OBO

**Client credentials:** the **app** is the subject. Correct for “embedder service reads **its** GCS bucket.” Wrong for “summarize **this user’s** mailbox.”

**OBO / token exchange:** incoming user token + your client identity → new token with **audience = tool API**, **subject = user**, maybe downscoped. Correct for agents. If the tool only supports API keys, you still **authorize in your PEP** before using a tenant-scoped key.

---

## Alternatives & Tradeoffs

| Pattern | Attribution | Rotation | Enterprise fit |
|---------|-------------|----------|----------------|
| Shared provider API key in env | Poor | Manual | Demo only |
| Per-tenant virtual key → gateway | Good (tenant) | Manageable | SaaS AI |
| Per-user API keys to **your** API | Good (user) | Painful at scale | Scripts, not SSO |
| Cloud SA + workload identity | Excellent (workload) | Automatic TTL | Platform internals |
| User OBO to downstream SaaS | Best (user+tenant) | Token TTL | Agents in SaaS tools |
| Customer-managed keys in their vault | Strong compliance | Customer-operated | High-trust / VPC |
| Long-lived GCP JSON / AWS IAM user | Terrible | Forgotten | Incident waiting |

---

## Necessity

Static keys in Git → class of breach (history rewrite does not save you; assume leaked).

**One global OpenAI key for all tenants:** no cost isolation, no kill-switch per customer, prompt injection that exfiltrates env → **cross-tenant spend and data**.

**Agents that call CRM as a service account:** bypass **user** ACLs → data exfiltration and compliance failure (the SA can see all Salesforce records).

**Provider keys in the browser or mobile app:** trivially extracted; your bill and quota die; ToS violations.

**CI JSON keys:** Week 18 already said OIDC to cloud; this week is why — stolen GitHub secret = production cloud admin.

---

## Industry Practice

**Common:** provider key in AWS Secrets Manager / GCP Secret Manager / Vault; one app SA; customer API keys for your public API; GitHub OIDC to deploy.

**Strong:**

- Workload identity **everywhere** (runtime + CI).  
- Per-tenant keyed gateway; budgets and model allowlists.  
- OBO / RFC 8693 into tools; never “platform admin” into customer SaaS.  
- Key scoping + automatic rotation + anomaly detection (impossible travel / new model / spend spike — Week 20 metrics, this week’s identity labels).  
- Break-glass: short-lived, ticketed, audited impersonation — not a shared `root` key in 1Password forever.  
- MCP: prefer OAuth on remote servers; treat static keys as local-dev only.

Google Cloud Tech publishes WIF explainers on YouTube (search current “Workload Identity Federation” on [Google Cloud Tech](https://www.youtube.com/@GoogleCloudTech)). AWS IAM Identity Center / IAM roles sessions: [AWS Cloud](https://www.youtube.com/@awscloud).

---

## Concrete Scenario (URL)

**RFC 8693 — Token Exchange** (OBO / downscope / actor token):  
https://datatracker.ietf.org/doc/html/rfc8693  

**AWS — OBO for multi-tenant agents (Bedrock AgentCore Gateway):**  
https://aws.amazon.com/blogs/machine-learning/implement-on-behalf-of-token-exchange-for-multi-tenant-agents-with-amazon-bedrock-agentcore-gateway/  

**AWS Well-Architected GenAI Lens — multi-tenant platform** (virtual keys, OAuth, Secrets Manager):  
https://docs.aws.amazon.com/wellarchitected/latest/generative-ai-lens/multi-tenant-generative-ai-platform-scenario.html  

**GCP Workload Identity Federation:**  
https://cloud.google.com/iam/docs/workload-identity-federation  

**LiteLLM virtual keys:**  
https://docs.litellm.ai/docs/proxy/virtual_keys  

**GitHub Actions OIDC** (no long-lived cloud keys in CI — pairs with Week 18):  
https://docs.github.com/en/actions/deployment/security/use-oidc  

**YouTube — Google Cloud Tech channel** (WIF / IAM talks; re-fetch title for the current flagship WIF session):  
https://www.youtube.com/@GoogleCloudTech  

**YouTube — AWS Cloud** (IAM / Identity Center):  
https://www.youtube.com/@awscloud  

---

## Open Questions

- Virtual keys vs full customer OIDC on **every** API call — when is the friction worth it (partners vs interactive users)?  
- Should remote MCP servers accept API keys at all, or only OAuth?  
- Break-glass that still leaves an audit trail without becoming a standing god key.  
- Customer-bring-your-own-key (CMEK) vs customer-bring-your-own-**provider** key (BYOK to OpenAI) — two different questionnaires.  
- Actor tokens in RFC 8693 (`act` claim): how to show “agent runtime X acting for user Y” in traces.

---

## Sources

- https://datatracker.ietf.org/doc/html/rfc8693  
- https://datatracker.ietf.org/doc/html/rfc6749  
- https://aws.amazon.com/blogs/machine-learning/implement-on-behalf-of-token-exchange-for-multi-tenant-agents-with-amazon-bedrock-agentcore-gateway/  
- https://docs.aws.amazon.com/wellarchitected/latest/generative-ai-lens/multi-tenant-generative-ai-platform-scenario.html  
- https://cloud.google.com/iam/docs/workload-identity-federation  
- https://docs.litellm.ai/docs/proxy/virtual_keys  
- https://docs.github.com/en/actions/deployment/security/use-oidc  
- https://www.youtube.com/@GoogleCloudTech  
- https://www.youtube.com/@awscloud  
