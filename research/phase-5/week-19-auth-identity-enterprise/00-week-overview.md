# 00 — Week overview: OIDC login (not a hardcoded API key) and multi-tenant isolation

> Week 19 — Auth, identity, and enterprise AI constraints  
> Research notes (raw). Phase 5 week after deployment infra (Week 18). Next: cost / latency (Week 20). Do not start routing/caching from this corpus.

This file is the **design document** for the two FDE interview artifacts: (1) how a human reaches the product **without** a baked secret, (2) how Tenant A never reads Tenant B.

---

## Fundamentals

Week 18 shipped a **digest-promoted container**. That image still typically starts with `OPENAI_API_KEY=` in a secret store. That key is a **provider credential for the platform**, not a **user session**. Confusing the two is how demos become security questionnaires that fail.

This week answers:

1. **How does a person log in?** OpenID Connect (OIDC) on OAuth 2.0 — Authorization Code + PKCE — against an IdP.  
2. **How does a machine call your API?** Scoped API keys, client credentials, or federated workload identity — never the user’s password and never the provider’s key in the client.  
3. **How do enterprises federate?** SAML 2.0 still, plus OIDC enterprise connections.  
4. **Where may data live?** Residency as a **control**, not a slide.  
5. **How do tenants stay isolated while roles exist inside a tenant?** Two-axis authorization.

### Design: OIDC login, not a hardcoded API key

| Wrong (demo) | Right (enterprise AI product) |
|--------------|-------------------------------|
| SPA sends `sk-…` or `x-api-key: shared-admin` to your backend | SPA redirects to IdP; backend receives **authorization code**; exchanges for tokens **server-side** (or BFF) |
| One env var `API_KEY` authenticates every user | OIDC **ID Token** identifies the user (`sub`, `iss`, `aud`); your session or access token authorizes APIs |
| Provider key in the browser so “chat works” | Provider key only on the **server / gateway**; browser never sees it |
| Long-lived personal access token as the agent identity | Short-lived user access token + **RFC 8693 token exchange** for tools (OBO) |

**OAuth 2.0** (RFC 6749) is **delegation**: a **client** obtains an **access token** to call a **resource server** without the **resource owner** sharing a password with that API. Roles: resource owner, client, authorization server, resource server ([RFC 6749](https://datatracker.ietf.org/doc/html/rfc6749)). Bearer usage is RFC 6750: possession of the token is authority unless you add sender constraints (mTLS RFC 8705, DPoP RFC 9449).

**OIDC** is an **identity layer on OAuth 2.0**. Request scope `openid` (plus `profile` / `email` as needed). The authorization server (OpenID Provider) returns an **ID Token** (JWT) with at least `iss`, `sub`, `aud`, `exp`, `iat` ([OIDC Core](https://openid.net/specs/openid-connect-core-1_0.html)). Discovery: `/.well-known/openid-configuration` ([OIDC Discovery](https://openid.net/specs/openid-connect-discovery-1_0.html)). Validate signature against JWKS (`jwks_uri`); reject `alg=none`; check `aud` is **your client id**; check `iss` matches the OP.

**Human login sequence (BFF / confidential client):**

```
User → App → 302 /authorize?response_type=code&scope=openid+profile
                &code_challenge=S256(...)&state=...&nonce=...
         → IdP (MFA, enterprise SSO)
         → 302 redirect_uri?code=...&state=...
User → App → POST /token (code + code_verifier + client_secret)
         ← access_token, id_token, refresh_token
App validates id_token, creates server session (httpOnly cookie)
App APIs: session or sender-constrained access token
LLM provider: server-side key / workload identity — never in the cookie
```

Public SPA/native: same **authorization code + PKCE**; no client secret; PKCE `S256` required ([RFC 7636](https://datatracker.ietf.org/doc/html/rfc7636); [RFC 8252](https://datatracker.ietf.org/doc/html/rfc8252); [RFC 9700](https://www.rfc-editor.org/rfc/rfc9700.html)). Prefer a **backend-for-frontend** so refresh tokens never sit in `localStorage`.

**What the hardcoded key was doing (and how to replace it):**

| Demo secret | Replacement |
|-------------|-------------|
| Shared `ADMIN_API_KEY` for the UI | OIDC session + RBAC roles in claims or your user store |
| Provider `sk-` in frontend | Gateway holds provider key; UI holds only IdP tokens / session |
| “Login” = knowing the Slack webhook secret | SSO + SCIM deprovision (when they leave, access ends) |
| CI `gcloud` JSON key in GitHub secrets | GitHub OIDC → cloud STS / WIF (Week 18 mentioned; this week specifies) |

Auth0 enterprise connections (OIDC/SAML IdPs for B2B) are the usual **broker** so your app speaks one protocol and customers bring Okta/Entra/Ping ([enterprise connections](https://auth0.com/docs/authenticate/enterprise-connections)). Okta’s OAuth/OIDC concept page is the workforce-IdP counterpart ([Okta OAuth/OIDC](https://developer.okta.com/docs/concepts/oauth-openid/)).

### Design: multi-tenant isolation

**Tenant** = a customer organization (company, agency, workspace). **Multi-tenancy** = one control plane serving many tenants. Isolation is **not** “we have a `customers` table.” It is: **every read/write path** that can hold prompts, documents, embeddings, traces, keys, or tool results is **scoped by tenant**, and a token from Tenant A **cannot** name Tenant B’s resources.

**Two axes (always both):**

1. **Cross-tenant isolation** — hard wall. Failure = data leak / career-ending bug.  
2. **In-tenant RBAC** — Admin vs Analyst vs Viewer vs Agent-approver inside one tenant.

**JWT / session must carry tenant context** after SSO:

- `tid` / `org_id` / custom `https://yourapp.com/tenant_id`  
- `roles` or `groups` (mapped from IdP; do not trust raw AD group explosion without mapping)  
- Optional `tier` (pool vs silo routing, residency region)

**Enforcement architecture** (AWS SaaS auth guidance): **PEP** (API gateway / middleware) asks **PDP** (Cedar / Verified Permissions / OPA / custom) ([multi-tenant API authorization](https://docs.aws.amazon.com/prescriptive-guidance/latest/saas-multitenant-api-access-authorization/welcome.html)). Deny by default. UI hiding buttons is not a PEP.

**Stores that must be tenant-keyed:**

| Surface | Isolation mechanism |
|---------|---------------------|
| Postgres / SQL | `tenant_id` on every row; RLS or mandatory WHERE; no raw `id` lookups without tenant |
| Object storage | Prefix `s3://bucket/{tenant_id}/…` + IAM/policy that cannot list sibling prefixes |
| Vector index | Namespace / filter `tenant_id == token.tenant`; never “global” semantic cache |
| Redis / prompt cache | Key includes tenant (and user if answers are private) |
| LLM gateway virtual keys | Per-tenant key → budget, models, RPM ([LiteLLM virtual keys](https://docs.litellm.ai/docs/proxy/virtual_keys)) |
| Traces / eval logs | Tenant attribute on every span; backends that cannot filter = residency + isolation fail |
| Agent tool calls | Authorize **each** invocation with user+tenant; OBO token so CRM sees the user ([RFC 8693](https://datatracker.ietf.org/doc/html/rfc8693); [Bedrock AgentCore OBO](https://aws.amazon.com/blogs/machine-learning/implement-on-behalf-of-token-exchange-for-multi-tenant-agents-with-amazon-bedrock-agentcore-gateway/)) |

**Pool vs silo vs bridge:** shared cluster + row-level tenant (cheap, isolation bugs easier); per-tenant accounts/clusters (residency, noisy-neighbor); mix by tier ([pool-model AgentCore](https://aws.amazon.com/blogs/machine-learning/shared-infrastructure-isolated-tenants-pool-model-multi-tenancy-with-amazon-bedrock-agentcore/); [GenAI Lens multi-tenant scenario](https://docs.aws.amazon.com/wellarchitected/latest/generative-ai-lens/multi-tenant-generative-ai-platform-scenario.html)).

### Mapping to adjacent weeks

| This week | Not this week |
|-----------|----------------|
| OIDC/SAML, keys vs SA vs WIF, residency, tenant RBAC | K8s/Terraform/canary (Week 18) |
| Cost **isolation** (per-tenant keys/budgets) | Cascading models, semantic cache as **latency** (Week 20) — cache **must** still be tenant-keyed here |
| Entitlement **shape** in JWT/RBAC | Messy SQL entitlements in customer DBs (Week 21) |

---

## Alternatives & Tradeoffs

| Approach | Pros | Cons |
|----------|------|------|
| **OIDC (code+PKCE) + CIAM broker + tenant PEP + vaulted provider keys** | Sellable; MFA/lifecycle; isolation testable | IdP mapping work; more moving parts |
| Hardcoded shared API key as “auth” | Ships Friday | No SSO, no MFA, no deprovision, no tenant kill-switch |
| Roll-your-own passwords | Simple | Enterprises refuse; credential stuffing |
| API keys for **humans** | Easy scripts | Rotation/leak; not SSO; no device trust |
| Opaque access tokens vs JWT | Opaque: central revoke | JWT: local validate, harder instant revoke (keep TTL short + denylist) |
| SAML SP in-app vs broker | Direct: one less hop | You own XML/certs; broker: extra mapping |
| Pool tenancy | Cost | One missed filter = all customers |
| Silo tenancy | Isolation/residency story | Cost, ops, slower features |

---

## Necessity

If login is a **hardcoded API key**:

- Security questionnaire: “SSO? MFA? SCIM?” → No. Deal dies.  
- Key in a screenshot / HAR / LLM prompt injection → **all tenants** or **all users**.  
- Employee leaves; key still works.  
- You cannot attribute an agent action to a person for audit.

If you skip **OIDC validation** (`aud`/`iss`/JWKS/`alg`):

- Token confusion / `alg=none` / stolen token from another app → account takeover ([RFC 8725 JWT BCP](https://datatracker.ietf.org/doc/html/rfc8725); RFC 9700).

If you skip **tenant isolation**:

- Vector search without `tenant_id` → **cross-tenant RAG** (classic multi-tenant AI failure).  
- Shared semantic cache → Tenant B sees Tenant A’s answer.  
- Agent with a platform SA calling Salesforce → bypasses user ACLs.

If you skip **SAML**:

- Fortune / gov / education IdPs never complete SSO; implementation stalls on ACS mismatches.

If you skip **residency as code**:

- EU PDFs embed in US; contract breach; one observability SaaS voids the claim.

---

## Industry Practice

**Common:** Auth0/Okta/Entra; code+PKCE; JWT access tokens; `tenant_id` column; provider key in Secrets Manager; SAML via broker; one primary cloud region; DPA on file.

**Strong / senior:**

1. Short-lived access tokens; refresh rotation; RP-initiated logout; CAE/universal logout where the IdP supports it.  
2. Audience-restricted tokens **per API** (RFC 8707 resource indicators / distinct `aud`).  
3. Separate IdP applications per environment (`dev`/`staging`/`prod`) — Week 18 digest promotion meets Week 19 app ids.  
4. Workload identity for CI and runtime; no long-lived cloud JSON keys.  
5. Per-tenant virtual keys + budgets; OBO into tools.  
6. Central PDP; integration tests that **must fail** if Tenant A’s token reads Tenant B’s vector namespace.  
7. Tenant residency in the **router**: refuse cross-region providers; CMEK/Private Link for high tiers.  
8. SCIM deprovision; dual-cert SAML rotation windows.

OktaDev’s public talk remains the fastest visual of OAuth vs OIDC ([OAuth 2.0 and OpenID Connect in plain English](https://www.youtube.com/watch?v=996OiexHze0)). Auth0’s illustrated talk is the companion ([Illustrated Guide to OAuth and OpenID Connect](https://www.youtube.com/watch?v=t18YB3xDdHo)).

---

## Concrete Scenario (URL)

**This week’s design, instantiated:** a B2B AI copilot. Users click “Sign in with company SSO.” Auth0 (or Okta) is the broker. Customer Okta is an OIDC or SAML enterprise connection. After login, JWT includes `org_id`. API PEP rejects missing/mismatched tenant. RAG query always filters `tenant_id`. LiteLLM virtual key per tenant holds the OpenAI key in the vault. Agent “create Jira ticket” uses RFC 8693 exchange so Jira sees the user, not `svc-copilot@`. EU tenant’s embedding + Pinecone/pgvector + Cloud Logging stay in `europe-west1` / `eu-central-1`.

Auth0 enterprise connections:  
https://auth0.com/docs/authenticate/enterprise-connections  

Okta as IdP into Auth0:  
https://auth0.com/docs/authenticate/identity-providers/okta  

RFC 6749 + OIDC Core:  
https://datatracker.ietf.org/doc/html/rfc6749  
https://openid.net/specs/openid-connect-core-1_0.html  

RFC 9700 (do not use implicit / ROPC):  
https://www.rfc-editor.org/rfc/rfc9700.html  

AWS SaaS authorization (PEP/PDP):  
https://docs.aws.amazon.com/prescriptive-guidance/latest/saas-multitenant-api-access-authorization/welcome.html  

GenAI Lens multi-tenant platform:  
https://docs.aws.amazon.com/wellarchitected/latest/generative-ai-lens/multi-tenant-generative-ai-platform-scenario.html  

YouTube (OktaDev + Auth0):  
https://www.youtube.com/watch?v=996OiexHze0  
https://www.youtube.com/watch?v=t18YB3xDdHo  

---

## Open Questions

- For agentic products, is the **OAuth client** the browser, the agent runtime, or both (three-party + token exchange)?  
- MCP / tool gateways: **per-tool audience** vs one gateway `aud`?  
- Session-bound vs token-bound agent runs when the user logs out mid-task (back-channel logout vs job continues with a snapshot of consent).  
- Should “customer admin” be able to mint keys that outlive SSO sessions?  
- Pool + RLS vs silo for a 50-tenant FDE deployment vs a 5,000-tenant SaaS.

---

## Sources

- https://datatracker.ietf.org/doc/html/rfc6749  
- https://datatracker.ietf.org/doc/html/rfc6750  
- https://datatracker.ietf.org/doc/html/rfc7636  
- https://datatracker.ietf.org/doc/html/rfc8252  
- https://www.rfc-editor.org/rfc/rfc9700.html  
- https://datatracker.ietf.org/doc/html/rfc8693  
- https://openid.net/specs/openid-connect-core-1_0.html  
- https://openid.net/specs/openid-connect-discovery-1_0.html  
- https://auth0.com/docs/authenticate/enterprise-connections  
- https://auth0.com/docs/authenticate/protocols/openid-connect-protocol  
- https://developer.okta.com/docs/concepts/oauth-openid/  
- https://docs.aws.amazon.com/prescriptive-guidance/latest/saas-multitenant-api-access-authorization/welcome.html  
- https://docs.aws.amazon.com/wellarchitected/latest/generative-ai-lens/multi-tenant-generative-ai-platform-scenario.html  
- https://docs.litellm.ai/docs/proxy/virtual_keys  
- https://www.youtube.com/watch?v=996OiexHze0  
- https://www.youtube.com/watch?v=t18YB3xDdHo  
