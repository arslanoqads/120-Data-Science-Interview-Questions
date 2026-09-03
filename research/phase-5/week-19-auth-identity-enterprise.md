# Week 19 — Auth, Identity, and Enterprise AI Constraints

> Phase 5 · Production, Cost, and Systems  
> Raw source material for FDE gate. Legal/public sources only.

---

## Concept: OAuth 2.0 and OpenID Connect (OIDC) fundamentals

### Fundamentals
**OAuth 2.0** (RFC 6749) is a **delegation** framework: a client obtains an **access token** to call APIs on behalf of a resource owner (or itself), without sharing the user’s password with every API.

**OpenID Connect** is an identity layer **on top of OAuth 2.0**. OIDC adds:
- **ID Token** (JWT) asserting who the user is (`sub`, `iss`, `aud`, `exp`, optional profile claims)
- Standard scopes: `openid`, `profile`, `email`
- Discovery (`/.well-known/openid-configuration`) and UserInfo endpoint

Common flows FDEs must recognize:

| Flow | Who | Notes |
|------|-----|-------|
| Authorization Code + PKCE | Browser/SPA/native user login | Default for user SSO; PKCE mandatory for public clients |
| Client Credentials | Service-to-service | No user; app gets token for itself |
| Refresh Token | Long-lived sessions | Rotate; bind to client |
| Device Code | CLI / limited input | Less common in enterprise SaaS web |
| Token Exchange (RFC 8693) | On-behalf-of agents | Critical for multi-tenant agents calling downstream APIs |

Tokens are **bearer** unless sender-constrained (mTLS/DPoP). Treat possession = authority; transmit only over TLS; short TTL for access tokens.

### Alternatives & Tradeoffs
| Approach | Pros | Cons |
|----------|------|------|
| OIDC SSO via enterprise IdP | Centralized MFA, lifecycle, audit | Requires IdP metadata + claim mapping |
| Roll-your-own sessions/passwords | Simple start | No enterprise buy-in; security debt |
| API keys for user auth | Easy | Not SSO; rotation/leak nightmare; no MFA |
| Opaque tokens vs JWT access tokens | Opaque = revocable at introspection | JWT = local validation but harder instant revoke |

**AuthN vs AuthZ:** OIDC tells you *who*; your RBAC/ABAC/policy engine decides *what* (see multi-tenant RBAC below).

### Necessity
Enterprises will not deploy your AI product without SSO. Mis-implemented OAuth (implicit flow, tokens in localStorage without care, skipping `aud`/`iss` validation, accepting `alg=none`) → account takeover. Skipping PKCE on public clients → code interception risk.

### Industry Practice
**Common:** Auth0/Okta/Entra ID; Authorization Code + PKCE; validate JWT with JWKS; map `groups`/`roles` claims into app roles.  
**Strong:** short-lived access tokens; refresh rotation; continuous access evaluation / universal logout; audience-restricted tokens per API; separate IdP applications per environment; never use long-lived user PATs for server-side agent actions — use OBO/token exchange.

### Concrete Scenario
Auth0 enterprise connections overview (OIDC/SAML IdPs for B2B SSO):  
https://auth0.com/docs/authenticate/enterprise-connections  

Okta as OIDC IdP into Auth0 (Workforce connection):  
https://auth0.com/docs/authenticate/identity-providers/okta  

RFC 6749 (OAuth 2.0) and OIDC Core:  
https://datatracker.ietf.org/doc/html/rfc6749  
https://openid.net/specs/openid-connect-core-1_0.html

### Open Questions
- For agentic products, is the “client” the browser, the agent runtime, or both (three-party)?
- How should MCP / tool gateways validate tokens — per-tool audience or one gateway audience?
- Session-bound vs token-bound agent runs when a user logs out mid-task.

### Sources
- https://datatracker.ietf.org/doc/html/rfc6749
- https://datatracker.ietf.org/doc/html/rfc8252 (OAuth for native apps / PKCE practices)
- https://openid.net/specs/openid-connect-core-1_0.html
- https://auth0.com/docs/authenticate/protocols/openid-connect-protocol
- https://developer.okta.com/docs/concepts/oauth-openid/
- https://datatracker.ietf.org/doc/html/rfc8693 (token exchange)

---

## Concept: SAML basics (legacy enterprise SSO)

### Fundamentals
**SAML 2.0** (Security Assertion Markup Language) is an XML-based SSO protocol still dominant in large enterprises (especially older IdPs, government, education). Roles:

- **IdP** (Identity Provider): Okta, Entra ID, ADFS, Ping — authenticates user, issues assertion
- **SP** (Service Provider): your app — trusts IdP, consumes assertion
- **Assertion:** XML statement with subject, conditions, attributes (email, groups), signed with IdP X.509 cert

Flows:
- **SP-initiated:** user hits your app → redirect to IdP → assertion POST back to ACS URL
- **IdP-initiated:** user clicks app tile in IdP portal → assertion posted to SP (no prior OIDC-style auth request)

OIDC does **not** natively support IdP-initiated the way SAML does; vendors document workarounds (bookmark apps, SAML connection instead). Auth0 notes that Okta Workforce OIDC connections do not support IdP-initiated login the same way SAML does:  
https://support.auth0.com/center/s/article/auth0-users-are-forced-to-re-enter-email-address-when-signing-in-to-an-okta-workforce-connection

### Alternatives & Tradeoffs
| Protocol | Enterprise reality | DX |
|----------|--------------------|-----|
| SAML 2.0 | Ubiquitous legacy; IdP-initiated tiles | XML, cert rotation pain, clock skew |
| OIDC | Modern default; APIs + mobile | Preferred for new builds |
| Both via broker (Auth0/Okta CIAM) | Sell to anyone | Extra hop, mapping complexity |

FDE rule: **support SAML for enterprise SSO even if your app is OIDC-native** — usually by putting a broker in front or using your IdP’s SAML federation.

### Necessity
Refusing SAML loses deals with Fortune/gov accounts. Broken ACS URL / Entity ID mismatches are the #1 onboarding failure. Ignoring assertion signature validation or `AudienceRestriction` → trivial spoofing.

### Industry Practice
**Common:** Auth0/Okta SAML SP; customer uploads IdP metadata XML + signing cert; map `email` → user; JIT provision on first login.  
**Strong:** require signed assertions + encrypted assertions when PII is rich; rotate signing certs with dual-cert windows; SCIM for lifecycle (deprovision); test IdP-initiated and SP-initiated; document exact Entity ID / ACS per environment.

### Concrete Scenario
Auth0: Connect your app to SAML Identity Providers (ACS, Entity ID, X.509 cert):  
https://auth0.com/docs/authenticate/identity-providers/enterprise-identity-providers/saml  

Okta SAML guidance (developer docs):  
https://developer.okta.com/docs/concepts/saml/

### Open Questions
- How long will SAML remain mandatory in RFPs vs “OIDC preferred, SAML accepted”?
- Should AI products expose a SAML SP directly or only via a CIAM broker?
- Attribute bloat: customers stuffing 50 AD groups into assertions — how to map safely?

### Sources
- https://auth0.com/docs/authenticate/identity-providers/enterprise-identity-providers/saml
- https://auth0.com/docs/authenticate/protocols/saml
- https://developer.okta.com/docs/concepts/saml/
- https://docs.oasis-open.org/security/saml/Post2.0/sstc-saml-tech-overview-2.0.html

---

## Concept: API key vs service account vs federated identity

### Fundamentals
Three machine-auth patterns show up in AI systems:

1. **API key** — static secret (often in header). Identifies a *project/tenant/customer app*, not a human. Easy to mint; hard to attribute to a person; leak = full power until rotated.
2. **Service account** — first-class identity for workloads (GCP SA, AWS IAM role, Azure MI). Authenticates via short-lived tokens from metadata/OIDC, or via key files (discouraged). Ideal for “backend calling Vertex/Bedrock/BigQuery.”
3. **Federated identity / workload identity** — CI job or K8s Pod exchanges cloud OIDC token for cloud credentials (**no long-lived JSON keys**). Also: customer’s IdP federates into your app (enterprise SSO). For agents: **on-behalf-of (OBO)** token exchange so tools see the *user*, not a god-mode service account.

LiteLLM / gateways often present **virtual keys** to tenants while holding provider keys server-side — a pattern that combines API-key UX with centralized secret custody.

### Alternatives & Tradeoffs
| Pattern | Attribution | Rotation | Enterprise fit |
|---------|-------------|----------|----------------|
| Shared provider API key in env | Poor | Manual | Demo only |
| Per-tenant virtual key → gateway | Good (tenant) | Manageable | SaaS AI |
| Cloud service account + workload identity | Excellent | Automatic short TTL | Platform internals |
| User OBO to downstream SaaS | Best (user+tenant) | Token TTL | Agents acting in SaaS tools |
| Customer-managed keys in their vault | Strong compliance | Customer-operated | High-trust enterprise |

### Necessity
Static keys in Git → breach class. One global OpenAI key for all tenants → no cost isolation, no kill-switch per customer, cross-tenant abuse if prompt injection exfiltrates key. Agents that call CRM as a service account bypass user ACLs → data exfiltration and compliance failure.

### Industry Practice
**Common:** provider key in Secrets Manager; app service account; customer API keys for your public API.  
**Strong:** workload identity everywhere; per-tenant keyed gateway; OBO/RFC 8693 into tools; key scoping (models allowed, RPM, budget); automatic rotation; anomaly detection on key use; never ship provider keys to browsers.

### Concrete Scenario
AWS on-behalf-of token exchange for multi-tenant agents (Bedrock AgentCore Gateway + RFC 8693):  
https://aws.amazon.com/blogs/machine-learning/implement-on-behalf-of-token-exchange-for-multi-tenant-agents-with-amazon-bedrock-agentcore-gateway/

AWS Well-Architected GenAI Lens — multi-tenant platform scenario (virtual keys, OAuth, Secrets Manager):  
https://docs.aws.amazon.com/wellarchitected/latest/generative-ai-lens/multi-tenant-generative-ai-platform-scenario.html

GCP Workload Identity Federation (conceptual parallel for keyless CI/workloads):  
https://cloud.google.com/iam/docs/workload-identity-federation

### Open Questions
- Virtual keys vs full customer OIDC for every API call — when is each worth the friction?
- Should MCP servers accept API keys at all, or only OAuth?
- Break-glass access patterns that still leave an audit trail.

### Sources
- https://datatracker.ietf.org/doc/html/rfc8693
- https://aws.amazon.com/blogs/machine-learning/implement-on-behalf-of-token-exchange-for-multi-tenant-agents-with-amazon-bedrock-agentcore-gateway/
- https://docs.aws.amazon.com/wellarchitected/latest/generative-ai-lens/multi-tenant-generative-ai-platform-scenario.html
- https://cloud.google.com/iam/docs/workload-identity-federation
- https://docs.litellm.ai/docs/proxy/virtual_keys

---

## Concept: Data residency for enterprise AI

### Fundamentals
**Data residency** = constraints on *where* data is stored and often *where it is processed*. Enterprises (especially EU, public sector, healthcare/finance) ask:

1. Where do prompts, documents, embeddings, and logs live at rest?
2. Do inference requests leave the region (or country)?
3. Are prompts used for **training** / retention by the model provider?
4. Who can access ops data (support, embeddings vendors, observability SaaS)?

Cloud controls: region selection, customer-managed encryption keys (CMEK), VPC endpoints / Private Link to AI APIs, contractual Zero Data Retention (ZDR), regional model endpoints.

Residency is **not** the same as sovereignty or GDPR lawful basis — but buyers often bundle them in security questionnaires.

### Alternatives & Tradeoffs
| Strategy | Pros | Cons |
|----------|------|------|
| Single-region deploy (e.g., `eu-west-1` only) | Clear story | Latency for global users; model availability gaps |
| Per-tenant regional pinning | Wins regulated deals | Multiplies infra cost; routing complexity |
| Process in-region, log globally | Easy ops | Often fails customer questionnaires |
| On-prem / VPC self-hosted models | Max control | Ops burden, weaker models, patching |
| Provider ZDR + regional endpoints | Pragmatic SaaS | Must verify subprocessors & support access |

Embeddings + vector DB + object storage + LLM endpoint + eval logs must **all** align — one US-only observability vendor can void an “EU residency” claim.

### Necessity
Shipping EU customer PDFs to a US-only embedding pipeline loses the deal or triggers contractual breach. “We use a US model API” without disclosure fails security review. Accidentally enabling provider training on customer prompts is a company-level incident.

### Industry Practice
**Common:** pick one primary region; document provider subprocessors; offer DPA.  
**Strong:** tenant residency config enforced in code (router refuses cross-region providers); separate regional stacks; CMEK; Private Link; ZDR addenda; residency-aware RAG (corpus + vector index co-located); deny-by-default egress policies; audit that *agent tool calls* also stay in-region.

### Concrete Scenario
AWS privacy / data residency building blocks and regional services (enterprise questionnaires map here):  
https://aws.amazon.com/compliance/data-privacy/  
https://aws.amazon.com/privacy/  

GCP data residency / Assured Workloads orientation:  
https://cloud.google.com/assured-workloads/docs/overview  
https://cloud.google.com/privacy  

Anthropic / OpenAI publish data usage and retention docs — treat as contractual inputs alongside cloud residency (check current ZDR offerings in provider trust centers). Anthropic prompt caching docs note ZDR interaction:  
https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching

### Open Questions
- Does “inference in-region” satisfy customers if the foundation model weights were trained elsewhere? (Often yes contractually; sometimes no politically.)
- Cross-border **support** access: how to debug EU tenants without moving payloads?
- Multi-hop agents calling US SaaS tools while claiming EU residency — disclose or block?

### Sources
- https://aws.amazon.com/compliance/data-privacy/
- https://docs.aws.amazon.com/wellarchitected/latest/generative-ai-lens/multi-tenant-generative-ai-platform-scenario.html
- https://cloud.google.com/assured-workloads/docs/overview
- https://cloud.google.com/privacy
- https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching

---

## Concept: RBAC for multi-tenant AI systems

### Fundamentals
**Multi-tenancy** = one platform serving many customers (tenants) with isolation. **RBAC** = permissions via roles (Admin, Analyst, Viewer…) assigned to principals. In SaaS AI you almost always need **two axes**:

1. **Tenant isolation** — Tenant A must never read Tenant B’s documents, embeddings, prompts, threads, or keys.
2. **In-tenant RBAC** — within Tenant A, who can manage connectors, run agents, view logs, approve tool actions?

Authorization architectures (AWS Prescriptive Guidance):

- **PEP** (Policy Enforcement Point): API gateway / service middleware that asks “allowed?”
- **PDP** (Policy Decision Point): engine evaluating RBAC/ABAC (OPA/Rego, Cedar / Amazon Verified Permissions, custom)

Patterns: **pool** (shared infra, row-level `tenant_id`), **silo** (per-tenant resources), **bridge** (mix). Pool is cheaper; silo is easier for residency/compliance.

JWT claims should carry `tenant_id` (+ role/tier). Every DB query, cache key, vector filter, and S3 prefix must be tenant-scoped.

### Alternatives & Tradeoffs
| Model | Flexibility | Complexity |
|-------|-------------|------------|
| Pure RBAC | Simple | Role explosion |
| ABAC (attributes: dept, region, sensitivity) | Fine-grained | Harder to reason about |
| RBAC + ABAC hybrid | Practical enterprise | Need good PDP |
| ReBAC (relationship-based, Zanzibar-style) | Great for sharing graphs | Ops + modeling cost |

For agents: authorize **each tool invocation** with user+tenant context, not just the chat WebSocket.

### Necessity
Missing `tenant_id` on a vector query → cross-tenant RAG leakage (career-ending class of bug). UI-only RBAC (hiding buttons) without API enforcement → trivial privilege escalation. Shared semantic cache without tenant key → answer leakage across customers.

### Industry Practice
**Common:** `tenant_id` column + role enum in app code.  
**Strong:** centralized PDP; deny-by-default; integration tests for cross-tenant access; per-tenant encryption keys optional for high tiers; rate limits and budgets per tenant; audit log with tenant/user/action; pool model with strict prefixing as in Bedrock AgentCore multi-tenant guidance.

### Concrete Scenario
AWS Prescriptive Guidance — Multi-tenant SaaS authorization and API access control (PDP/PEP, RBAC/ABAC, OPA, Verified Permissions):  
https://docs.aws.amazon.com/prescriptive-guidance/latest/saas-multitenant-api-access-authorization/welcome.html  

Pool-model multi-tenancy with Bedrock AgentCore (tier → tenant → user claims in JWT):  
https://aws.amazon.com/blogs/machine-learning/shared-infrastructure-isolated-tenants-pool-model-multi-tenancy-with-amazon-bedrock-agentcore/

### Open Questions
- Who approves high-risk agent actions — role-based approvers, or per-resource owners (ReBAC)?
- How to expose “customer admin” RBAC without allowing them to break isolation?
- Evaluating authorization for *generated* SQL/tool args (LLM proposes; PEP must still enforce).

### Sources
- https://docs.aws.amazon.com/prescriptive-guidance/latest/saas-multitenant-api-access-authorization/welcome.html
- https://aws.amazon.com/blogs/machine-learning/shared-infrastructure-isolated-tenants-pool-model-multi-tenancy-with-amazon-bedrock-agentcore/
- https://docs.aws.amazon.com/wellarchitected/latest/generative-ai-lens/multi-tenant-generative-ai-platform-scenario.html
- https://www.openpolicyagent.org/docs/latest/

---

## Week 19 synthesis notes (for later curriculum writing)

- FDE interview fluency: draw SP-initiated SAML vs OIDC auth code; explain when to use client credentials vs OBO; list residency surfaces (prompt, embed, log, tool); sketch tenant-scoped RAG filter.
- Pair with Week 18 (Workload Identity on K8s) and Week 21 (customer IdP + messy entitlement schemas in legacy SQL).
