# Week 19 Research Corpus — Auth, identity, and enterprise AI constraints

> Phase 5 — Production, Cost, and Systems  
> **Status:** COMPLETE (deep pass)  
> Raw research corpus (not textbook). Legal/public sources only (IETF RFCs, OpenID Foundation specs, OASIS SAML, Auth0/Okta docs, AWS/GCP residency and SaaS authorization, YouTube from OktaDev / Auth0 / Google Cloud / AWS). **No pirate PDFs, no libgen/pdfcoffee, no unauthorized course decks.**

This directory is the Week 19 research repository. Read concept files in order, then the source map. **Do not start Week 20 (cost / latency) from this corpus** — this week ships **OIDC login instead of hardcoded API keys**, **SAML for legacy SSO**, **API keys vs service accounts vs federation**, **data residency**, and **multi-tenant RBAC / isolation**. Week 18 already containerized the service; this week decides **who** may call it and **where** tenant data may live.

| # | File | Concept |
|---|------|---------|
| 00 | [00-week-overview.md](00-week-overview.md) | Design doc: OIDC login (not a baked API key) + multi-tenant isolation |
| 01 | [01-oauth2-oidc.md](01-oauth2-oidc.md) | OAuth 2.0 + OIDC: grants, PKCE, JWT validation, token exchange |
| 02 | [02-saml-legacy-sso.md](02-saml-legacy-sso.md) | SAML 2.0 SP/IdP, ACS, Entity ID, certs, IdP-initiated |
| 03 | [03-api-keys-service-accounts-federation.md](03-api-keys-service-accounts-federation.md) | API keys, cloud SAs, workload identity, OBO |
| 04 | [04-data-residency.md](04-data-residency.md) | Region pinning, CMEK, ZDR, embeddings/logs/tools |
| 05 | [05-rbac-multi-tenant.md](05-rbac-multi-tenant.md) | Tenant isolation, RBAC/ABAC, PEP/PDP, pool vs silo |
| — | [99-source-map.md](99-source-map.md) | Master URL / RFC / vendor / YouTube index |

## Completeness checklist (Week 19)

- [x] All syllabus Week 19 concepts covered with **7 required fields**  
- [x] **OIDC login, not a hardcoded API key** as the human-auth design (auth code + PKCE; no `alg=none`; `iss`/`aud`/`exp`)  
- [x] **Multi-tenant isolation design doc** (tenant in JWT; every store keyed; RAG/cache/logs)  
- [x] OAuth 2.0 RFC 6749 roles + grants; bearer RFC 6750; PKCE RFC 7636; BCP RFC 9700  
- [x] OIDC Core + Discovery; ID Token vs access token; JWKS validation  
- [x] Token exchange RFC 8693 / on-behalf-of for agents calling tools  
- [x] Implicit and ROPC called out as **do not use** (RFC 9700)  
- [x] SAML 2.0 OASIS overview; SP- vs IdP-initiated; ACS / Entity ID / AudienceRestriction  
- [x] Auth0 + Okta enterprise connection / SAML SP docs  
- [x] API key vs service account vs federated / workload identity  
- [x] LiteLLM-style **virtual keys** (tenant UX) vs provider keys in a vault  
- [x] GCP Workload Identity Federation; AWS IAM roles / OIDC federation  
- [x] Data residency ≠ GDPR lawful basis; rest vs process vs training vs support access  
- [x] AWS privacy / data residency; GCP Assured Workloads + resource locations  
- [x] Embeddings, vector DB, object store, LLM endpoint, eval logs, observability **all** in-region  
- [x] Multi-tenant RBAC two axes: isolation + in-tenant roles  
- [x] AWS Prescriptive Guidance PDP/PEP; pool vs silo vs bridge  
- [x] Agent **tool** authorization with user+tenant context (not chat-socket-only)  
- [x] YouTube: OktaDev OIDC explainer, Auth0 illustrated OAuth, Google Cloud / AWS identity talks  
- [x] Per-week research **directory** (not a single thin file)  
- [x] `_PRIOR_SINGLE_FILE.md` removed after expansion  

## Syllabus build task (Week 19)

You already have a **containerized, staged LLM service** (Week 18). This week you **stop treating a secret env var as “login.”**

1. **Human login is OIDC.** Browser/SPA/native uses **Authorization Code + PKCE** against an IdP (Auth0/Okta/Entra or customer IdP via enterprise connection). Validate ID tokens (`iss`, `aud`, `exp`, signature via JWKS). Map claims to an app user. **Do not** ship the product with a shared OpenAI/Anthropic key in the client or a single `ADMIN_API_KEY` as the only gate.  
2. **Machines are not humans.** Provider keys live in a secret store. Workloads use **service accounts / workload identity**. Customer-facing APIs use **scoped keys or OAuth client credentials**, not the provider key. Agents that call downstream SaaS use **token exchange / OBO**, not a god-mode SA.  
3. **Enterprise SSO includes SAML.** Document Entity ID, ACS URL, signing cert, SP- and IdP-initiated. Broker (CIAM) is acceptable; refusing SAML is not.  
4. **Residency is a router constraint.** Tenant config pins region; prompts, embeddings, indexes, logs, and tool hops must not silently leave. Disclose provider training/retention.  
5. **Isolation is enforced in every store.** `tenant_id` on DB rows, object prefixes, vector filters, cache keys, and traces. In-tenant RBAC (admin / analyst / viewer / approver) at the **API**, not only the UI.

Interview artifact = **sequence diagram of OIDC login + API call** (no hardcoded key) + **one-page isolation design** (JWT claims → PEP → stores) + **residency surface list** (prompt, embed, log, tool).

## Default path (synthesis)

1. **OAuth delegates; OIDC authenticates.** Access token calls APIs; ID token tells you who ([RFC 6749](https://datatracker.ietf.org/doc/html/rfc6749); [OIDC Core](https://openid.net/specs/openid-connect-core-1_0.html)).  
2. **PKCE is mandatory for public clients; implicit is dead.** ([RFC 7636](https://datatracker.ietf.org/doc/html/rfc7636); [RFC 9700](https://www.rfc-editor.org/rfc/rfc9700.html)).  
3. **SAML still wins RFPs.** Broker it if your app is OIDC-native ([Auth0 SAML IdP](https://auth0.com/docs/authenticate/identity-providers/enterprise-identity-providers/saml)).  
4. **Never put provider keys in browsers; never share one key across tenants.** Virtual keys + vault + workload identity ([GCP WIF](https://cloud.google.com/iam/docs/workload-identity-federation)).  
5. **Residency is the whole pipeline.** One US log vendor voids an EU claim ([Assured Workloads](https://cloud.google.com/assured-workloads/docs/overview); [AWS data privacy](https://aws.amazon.com/compliance/data-privacy/)).  
6. **Missing `tenant_id` on a vector query is a SEV-0 class bug.** PEP/PDP, deny-by-default ([SaaS API authorization](https://docs.aws.amazon.com/prescriptive-guidance/latest/saas-multitenant-api-access-authorization/welcome.html)).
