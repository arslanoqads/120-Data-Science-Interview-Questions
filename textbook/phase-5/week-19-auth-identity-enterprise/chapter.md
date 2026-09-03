# Chapter 19 — Auth, identity, and enterprise AI constraints

> **Phase 5 — Production, Cost, and Systems**  
> **Compilation status:** COMPLETE  
> **Source of truth:** `research/phase-5/week-19-auth-identity-enterprise/`  
> **Syllabus Build:** You already have a **containerized, staged LLM service** (Week 18). This week you **stop treating a secret env var as “login.”** (1) **Human login is OIDC.** Browser/SPA/native uses **Authorization Code + PKCE** against an IdP (Auth0/Okta/Entra or customer IdP via enterprise connection). Validate ID tokens (`iss`, `aud`, `exp`, signature via JWKS). Map claims to an app user. **Do not** ship the product with a shared OpenAI/Anthropic key in the client or a single `ADMIN_API_KEY` as the only gate. (2) **Machines are not humans.** Provider keys live in a secret store. Workloads use **service accounts / workload identity**. Customer-facing APIs use **scoped keys or OAuth client credentials**, not the provider key. Agents that call downstream SaaS use **token exchange / OBO**, not a god-mode SA. (3) **Enterprise SSO includes SAML.** Document Entity ID, ACS URL, signing cert, SP- and IdP-initiated. Broker (CIAM) is acceptable; refusing SAML is not. (4) **Residency is a router constraint.** Tenant config pins region; prompts, embeddings, indexes, logs, and tool hops must not silently leave. Disclose provider training/retention. (5) **Isolation is enforced in every store.** `tenant_id` on DB rows, object prefixes, vector filters, cache keys, and traces. In-tenant RBAC (admin / analyst / viewer / approver) at the **API**, not only the UI.

---

## Chapter framing

Week 19 is the **who and where** week of Phase 5. Week 18 shipped a **digest-promoted container**. That image still typically starts with `OPENAI_API_KEY=` in a secret store. That key is a **provider credential for the platform**, not a **user session**. Confusing the two is how demos become security questionnaires that fail.

This week answers five questions that procurement, IdP onboarding, and multi-tenant AI incidents all treat as the minimum bar for an FDE who can land an enterprise LLM product:

1. **How does a person log in without a baked secret?** (OIDC on OAuth 2.0 — Authorization Code + PKCE)  
2. **How do enterprises federate when the IdP is still SAML?** (SP/IdP-initiated, ACS, Entity ID, certs)  
3. **How does a machine call your API or a tool without wearing the user’s password or the provider key?** (API keys, service accounts, workload identity, OBO)  
4. **Where may prompts, embeddings, logs, and tool payloads live?** (residency as a control, not a slide)  
5. **How do tenants stay isolated while roles exist inside a tenant?** (two-axis authorization; PEP/PDP)

| Wrong (demo) | Right (enterprise AI product) |
|--------------|-------------------------------|
| SPA sends `sk-…` or `x-api-key: shared-admin` to your backend | SPA redirects to IdP; backend receives **authorization code**; exchanges for tokens **server-side** (or BFF) |
| One env var `API_KEY` authenticates every user | OIDC **ID Token** identifies the user (`sub`, `iss`, `aud`); your session or access token authorizes APIs |
| Provider key in the browser so “chat works” | Provider key only on the **server / gateway**; browser never sees it |
| Long-lived personal access token as the agent identity | Short-lived user access token + **RFC 8693 token exchange** for tools (OBO) |

**Do not start Week 20 (cost / latency) from this chapter** — this week ships **OIDC login instead of hardcoded API keys**, **SAML for legacy SSO**, **API keys vs service accounts vs federation**, **data residency**, and **multi-tenant RBAC / isolation**. Cost **isolation** (per-tenant keys/budgets) belongs here as identity of the key; cascading models, semantic cache as **latency**, and compression are Week 20 — the cache **must** still be tenant-keyed here. Entitlement **shape** in JWT/RBAC is this week; messy SQL entitlements in customer DBs are Week 21. K8s/Terraform/canary remain Week 18.

**Human login sequence (BFF / confidential client)**

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

**Default path (synthesis)**

1. **OAuth delegates; OIDC authenticates.** Access token calls APIs; ID token tells you who (RFC 6749; OIDC Core).  
2. **PKCE is mandatory for public clients; implicit is dead.** (RFC 7636; RFC 9700).  
3. **SAML still wins RFPs.** Broker it if your app is OIDC-native.  
4. **Never put provider keys in browsers; never share one key across tenants.** Virtual keys + vault + workload identity.  
5. **Residency is the whole pipeline.** One US log vendor voids an EU claim.  
6. **Missing `tenant_id` on a vector query is a SEV-0 class bug.** PEP/PDP, deny-by-default.

Interview artifact = **sequence diagram of OIDC login + API call** (no hardcoded key) + **one-page isolation design** (JWT claims → PEP → stores) + **residency surface list** (prompt, embed, log, tool).

Read the concepts in order. Each section’s **Worked Example** and **Apply It** assume the same flagship service (working title: Deployment Copilot) after Week 18 containerization — now deciding **who** may call it and **where** tenant data may live.

---

### OAuth 2.0 and OpenID Connect (OIDC)

* **Fundamentals:**  
  **OAuth 2.0** is an **authorization** framework, not “login.” A **client** obtains an **access token** so it can call a **resource server** with the **resource owner’s** delegated permission — or with its own identity (client credentials). The password stays at the **authorization server** (RFC 6749). Using OAuth **without** an identity layer as “login” (treat access token as proof of who the user is, without `aud`/`iss` discipline) is a long-standing anti-pattern. **OpenID Connect (OIDC)** is an **identity layer on OAuth 2.0** so authentication is explicit.

  **Roles (RFC 6749 §1.1)** in an AI product: **resource owner** = end user (or org admin granting tenant-wide consent); **client** = browser BFF, native app, agent runtime, MCP host; **authorization server** = Okta, Entra ID, Auth0, Keycloak, customer IdP; **resource server** = your FastAPI, LiteLLM gateway, tool API.

  | Token | Purpose | Typical format |
  |-------|---------|----------------|
  | **Authorization code** | One-time; swapped at token endpoint; never a session | Opaque string |
  | **Access token** | Call APIs (`Authorization: Bearer`) | Opaque or JWT (RFC 9068 JWT profile) |
  | **Refresh token** | New access tokens without UX | Opaque; store like a secret; rotate (RFC 9700) |
  | **ID Token** | Prove who authenticated to **this client** | JWT only (OIDC) |

  **ID Token** is for the **client**. **Access token** is for the **API**. Do not send ID Tokens as `Authorization` to your resource server unless you have a documented, audience-correct profile (usually you should not). Bearer tokens (RFC 6750): whoever holds them can use them. Transmit only over TLS. Prefer short TTL. Sender-constrained options: mTLS (RFC 8705), DPoP (RFC 9449).

  OIDC Core: scope `openid` required for an ID Token; standard scopes `profile`, `email`, `address`, `phone`; claims in ID Token and/or UserInfo; `nonce` binds the token to the authentication request; `at_hash` / `c_hash` when tokens are issued together. Discovery (`/.well-known/openid-configuration`; AS metadata RFC 8414): fetch `issuer`, `authorization_endpoint`, `token_endpoint`, `jwks_uri`, `userinfo_endpoint`, `code_challenge_methods_supported`.

  **Validation checklist (FDE interview):** (1) Fetch JWKS; verify signature; **reject** `alg=none` and unexpected algs (RFC 8725). (2) `iss` exact match to discovery issuer. (3) `aud` contains **this** client (or API audience for access tokens). (4) `exp` / `nbf` / `iat` with small clock skew. (5) `nonce` if you sent one. (6) For access tokens: `scope` / `scp` sufficient; tenant claim present.

  | Flow | Who | Notes |
  |------|-----|-------|
  | **Authorization Code + PKCE** | Browser, SPA, native user login | Default. PKCE `S256`. Public clients MUST; confidential SHOULD (RFC 7636; RFC 9700). |
  | **Client Credentials** | Service-to-service | No user. Your agent **platform** talking to your own APIs — not “the user clicked send.” |
  | **Refresh Token** | Long sessions | Rotate; bind to client; detect reuse (theft). |
  | **Device Code** (RFC 8628) | CLI / limited input | User codes on a second device. |
  | **Token Exchange** (RFC 8693) | On-behalf-of, impersonation, downscoping | **Agents calling downstream APIs** as the user. |
  | **Implicit** (`response_type=token` / `id_token` in URL) | Legacy SPAs | **Do not use** — RFC 9700. Tokens leak via history/referrer. |
  | **ROPC** (password grant) | Legacy | **Do not use** — RFC 9700. Breaks MFA/federation. |

  **PKCE (RFC 7636):** client creates `code_verifier`; sends `code_challenge = BASE64URL(SHA256(verifier))`; token request must present the verifier. Stops **authorization code interception** on public clients and **code injection**. Originally for native apps; now BCP for essentially all code flows. Public SPA/native: same authorization code + PKCE; no client secret; prefer a **backend-for-frontend** so refresh tokens never sit in `localStorage`.

  **Pushed Authorization Requests** (RFC 9126): PAR moves request parameters to a back-channel POST; front-channel only carries a request URI — reduces leaking `state`/PKCE in logs and referrers. **Resource indicators** (RFC 8707): `resource` parameter so access tokens are **audience-restricted** to a specific API — prevents a token minted for “chat API” from being accepted at “admin API.”

  OIDC answers **who**. Your **RBAC/ABAC/ReBAC** (later in this chapter) answers **what**. Groups in the ID Token are **hints** until the PEP evaluates them. Logout: RP-initiated logout, session management, front-channel and back-channel logout are separate OIDC specs. Universal logout / continuous access evaluation (IdP-specific: Okta, Entra) matter when an employee is terminated **during** a long agent run.

* **The Alternatives:**  

  | Approach | Pros | Cons |
  |----------|------|------|
  | OIDC SSO via enterprise IdP | MFA, lifecycle, audit, SCIM | Claim mapping; IdP quirks |
  | CIAM broker (Auth0) + customer IdP | One integration in your app | Extra hop; cost; data processing addendum |
  | Roll-your-own sessions/passwords | Fast prototype | No enterprise buy-in |
  | API keys as user auth | Scripts | No SSO/MFA; leak blast radius |
  | Opaque tokens + introspection (RFC 7662) | Central revoke | Latency; AS availability on every call |
  | JWT access tokens | Local validate, scale | Revoke ≈ short TTL + denylist |
  | BFF + httpOnly cookies | Refresh not in JS | CSRF defense required |
  | SPA + tokens in memory | Simple | Refresh handling; XSS still catastrophic |
  | DPoP / mTLS | Stolen bearer less useful | Client and gateway complexity |

  The syllabus selects **OIDC (Authorization Code + PKCE)** as human login for Deployment Copilot — not a hardcoded shared API key. Prefer: IdP authenticates → validate ID token → session or audience-correct access token → provider key only on server/gateway.

* **Failure Modes:**  
  - Implicit flow or tokens in URLs → history/referrer leak.  
  - Skipping `aud`/`iss` (accepting another app’s token) → account takeover.  
  - `alg=none` or not pinning allowed algorithms → forged JWTs.  
  - No PKCE on public clients → authorization code interception.  
  - Redirect URI prefix matching (`https://app.com` vs `https://app.com.evil.tld`) — use **exact** registered URIs (RFC 9700).  
  - Access token used as ID; ID token used as API credential.  
  - Logging full tokens in LLM traces (Week 17 observability vs this week’s secret hygiene).  
  - Hardcoded API key as “login” → no SSO/MFA/SCIM; employee leaves and key still works; cannot attribute agent actions to a person.

* **Average vs. Strong Engineer:**  
  **Average:** Auth0/Okta/Entra wired for Authorization Code + PKCE; validate JWT with JWKS; map `groups`/`roles` into app roles; refresh in a BFF cookie — but one IdP app across envs, long-lived tokens, and no audience split.  
  **Strong:** RFC 9700 as the checklist, not blog folklore; short-lived access tokens (minutes) with rotating refresh; distinct `aud` per API so the gateway rejects wrong audience; PAR + PKCE for high-assurance customers; token exchange for agents with **downscope** before tools; continuous access evaluation / back-channel logout hooked to **cancel in-flight agent jobs** (policy choice — document it); separate IdP applications per environment (`dev`/`staging`/`prod` — Week 18 digest promotion meets Week 19 app ids); never long-lived user PATs for server-side agent actions.

* **Worked Example:**  
  Deployment Copilot’s UI no longer ships with `ADMIN_API_KEY` or a provider `sk-` in the browser. Users click “Sign in with company SSO.” Auth0 (or Okta) is the broker; customer Okta/Entra is an OIDC enterprise connection. The BFF runs Authorization Code + PKCE, validates the ID token (`iss`, `aud` = Deployment Copilot client id, `exp`, JWKS signature, reject `alg=none`), and creates an httpOnly session cookie. API calls carry the session or a short-lived access token whose `aud` is the chat API — not the admin API. When an agent must create a Jira ticket, the runtime performs RFC 8693 token exchange so Jira sees the **user**, not a platform god-mode identity. Provider keys stay in the vault / gateway only.

* **Apply It:**  
  1. Replace any shared `ADMIN_API_KEY` / client-side provider key with Authorization Code + PKCE against an IdP (or CIAM broker).  
  2. Validate ID tokens: JWKS signature, reject `alg=none`, exact `iss`, `aud` = your client, `exp`/`nbf`/`iat` with clock skew, `nonce` if sent.  
  3. Prefer a BFF so refresh tokens are not in `localStorage`; defend CSRF on cookie sessions.  
  4. Register **exact** redirect URIs; separate IdP apps for `dev` / `staging` / `prod`.  
  5. Ban Implicit and ROPC; use client credentials only for service-to-service without a user.  
  6. For agents calling downstream SaaS, plan RFC 8693 / OBO with downscoping — not a user PAT.  
  7. `[NEEDS MORE RESEARCH]`: for agentic products, whether the OAuth client is the browser, the agent runtime, or both (three-party + token exchange); MCP / tool gateways — per-tool audience vs one gateway `aud`; session-bound vs token-bound agent runs when the user logs out mid-task.

---

### SAML 2.0 (legacy enterprise SSO)

* **Fundamentals:**  
  **SAML 2.0** (Security Assertion Markup Language) is an OASIS standard for exchanging **authentication and attribute assertions** in XML. It remains dominant in large enterprises, government, education, and older IdPs (ADFS, older Ping, some Okta/Entra apps configured years ago). Prefer OIDC for **new** app protocols; still **support** SAML for buyers.

  | Role | Who |
  |------|-----|
  | **IdP** (Identity Provider) | Okta, Microsoft Entra ID, ADFS, Ping, Shibboleth — authenticates the user, issues a signed **assertion** |
  | **SP** (Service Provider) | Your app or your CIAM broker — consumes the assertion, creates a session |
  | **Principal** | The user |

  The **assertion** is XML: subject (NameID), conditions (NotBefore/NotOnOrAfter, **AudienceRestriction**), attribute statements (email, groups, department), optionally authn context (password vs MFA). The IdP **signs** with an X.509 certificate. Optionally the assertion or NameID is **encrypted** to the SP cert.

  **Bindings you will see:** **HTTP-Redirect** — typically SP → IdP **AuthnRequest** (deflate + query string); **HTTP-POST** — typically IdP → SP **Response** with assertion to the **Assertion Consumer Service (ACS)** URL. Artifact binding exists; rare in SaaS onboarding.

  **SP-initiated:** user hits `https://app.example/login` → SP builds AuthnRequest → redirect to IdP SSO URL → user authenticates → POST assertion to ACS. You can relay `RelayState` (return URL / tenant hint). This is the analogue of OIDC’s authorization request.

  **IdP-initiated:** user clicks the app tile in the Okta/Entra portal. **No prior AuthnRequest from you.** IdP POSTs a Response to ACS, often with `RelayState` configured in the IdP app. OIDC does **not** natively have the same “unsolicited IdP start” as first-class; brokers document workarounds. Auth0 notes Okta Workforce **OIDC** connections do not support IdP-initiated the way SAML does. FDE implication: if the customer’s success criterion is “tile in Okta works with one click,” you likely need **SAML** or a vendor-specific IdP-initiated OIDC hack — do not promise OIDC-only without checking.

  **Metadata — the onboarding contract** (IdP and SP exchange metadata XML or form fields):

  | Field | Failure mode if wrong |
  |-------|------------------------|
  | **Entity ID** (SP and IdP unique URIs/URNs) | Audience mismatch; assertion rejected |
  | **ACS URL** (SP) | Assertion POSTs to nowhere / 404; #1 ticket |
  | SSO / SLO URLs | Redirect loops |
  | Signing cert (IdP → SP) | Signature invalid after IdP cert rotation |
  | NameID format | Duplicate users (`email` vs persistent opaque) |

  Auth0 as SP (typical broker): ACS / Post-back `https://{yourDomain}/login/callback?connection={yourConnectionName}`; Entity ID `urn:auth0:{yourTenant}:{yourConnectionName}` (customizable via Management API `connection.options.entityId`).

  **Security checks the SP must perform:** (1) Signature valid over assertion (or response) using **current** IdP cert — do not skip in “dev.” (2) AudienceRestriction includes **your** Entity ID. (3) Destination / recipient matches ACS. (4) Time window with clock skew budget (NTP on both sides; classic “NotOnOrAfter already passed”). (5) InResponseTo matches AuthnRequest ID for SP-initiated (IdP-initiated has none — policy choice). (6) Decrypt if encrypted; never log raw assertions with PII in LLM traces.

  SAML outages cluster around **expired IdP signing certs** and **clock skew**. Strong practice: dual-cert windows (IdP publishes new cert in metadata before switching). **JIT (just-in-time):** first successful assertion creates the user from attributes — fast; deprovision is weak. **SCIM** (RFC 7643 / RFC 7644): IdP pushes create/update/disable — enterprises will ask for SCIM on the same questionnaire as SAML.

  **FDE rule:** Support SAML for enterprise SSO even if the app is OIDC-native — usually a **broker** (Auth0, Okta CIAM, Entra External ID) or the customer’s IdP federating SAML into an OIDC app you already have. Implementing a SAML SP from scratch is rarely worth it unless you are the IdP vendor.

* **The Alternatives:**  

  | Protocol | Enterprise reality | DX |
  |----------|--------------------|-----|
  | SAML 2.0 | Ubiquitous legacy; IdP-initiated tiles; gov/edu | XML, cert rotation, clock skew, attribute mapping |
  | OIDC | Modern default; APIs + mobile + PKCE | Preferred for new builds |
  | Both via broker | Sell to anyone | Extra hop, claim mapping, data processing |
  | WS-Fed | Some Microsoft estates | Even more legacy; treat like SAML for scoping |

  | SP placement | Upside | Downside |
  |--------------|--------|----------|
  | Direct SAML SP in the product | One less vendor hop | You own CVE surface and cert ops |
  | CIAM broker as SP | How most AI startups close the first ten enterprise logos | Extra mapping; DPA with broker |

  The syllabus selects **support SAML via broker (or equivalent)** for Deployment Copilot — refusing SAML is not acceptable even when the app is OIDC-native.

* **Failure Modes:**  
  - Refusing SAML → Fortune / public-sector deals stall that cannot turn on OIDC this quarter.  
  - Broken **ACS URL** / **Entity ID** mismatches — #1 onboarding failure; IdP “test” button succeeds and your app never sees a POST.  
  - Ignoring **signature** or **AudienceRestriction** → trivial assertion spoofing (unsigned XML, wrong audience).  
  - NameID as email without an `email_verified`-equivalent process → account takeover when IdP attributes are editable unsafely; prefer persistent NameID + separate email attribute.  
  - Cert rotation without dual-cert window → sudden SSO outage.  
  - Clock skew → “NotOnOrAfter already passed” on every assertion.

* **Average vs. Strong Engineer:**  
  **Average:** Auth0/Okta SAML SP; customer uploads IdP metadata + signing cert; map `email` → user; JIT on first login; SP-initiated for “Log in” button; IdP-initiated for tile.  
  **Strong:** Signed assertions **required**; encrypted assertions when attributes are rich (SSN, student IDs); dual-cert rotation runbooks; metadata URL if the IdP publishes one (refresh, don’t screenshot certs); test **both** SP- and IdP-initiated in staging (Week 18 staging digest + this week’s IdP apps); exact Entity ID / ACS **per environment** (`-dev` vs `-prod` connections); SCIM for disable/delete with JIT only as fallback; cap / map AD groups (customers stuffing 50 groups into assertions); document RelayState size limits (some IdPs truncate).

* **Worked Example:**  
  A regulated customer’s success criterion is “one click from the Okta tile.” Deployment Copilot’s app is OIDC-native, so Auth0 is configured as SAML SP: customer IT uploads IdP metadata; ACS is `https://{domain}/login/callback?connection=acme-saml`; Entity ID is `urn:auth0:{tenant}:acme-saml`. Staging and prod use **separate** connections so ACS/Entity ID never collide. On first login JIT creates the user from mapped attributes; SCIM is on the roadmap for disable when the employee leaves. SP-initiated covers the in-app “Log in” button; IdP-initiated covers the Okta tile — both are tested in staging before go-live.

* **Apply It:**  
  1. Document Entity ID, ACS URL, signing cert, SP-initiated, and IdP-initiated for your product (or broker connection).  
  2. Prefer a CIAM broker as SAML SP unless you have a reason to own XML/certs yourself.  
  3. Enforce signature + AudienceRestriction + Destination + time window; never skip signature in “dev.”  
  4. Separate SAML connections / Entity ID / ACS per environment.  
  5. Plan dual-cert rotation and NTP; add SCIM for deprovision (JIT alone is weak).  
  6. Do not promise OIDC-only if the customer needs IdP-initiated tiles without checking broker/IdP support.  
  7. `[NEEDS MORE RESEARCH]`: how long RFPs will say “SAML required” vs “OIDC preferred, SAML accepted”; whether AI products should expose a SAML SP directly or only via CIAM; attribute bloat (50 AD groups) — map in broker vs query Graph/SCIM asynchronously; SLO worth when agent jobs are mid-flight.

---

### API keys, service accounts, and federated identity

* **Fundamentals:**  
  Three **machine** patterns show up in every production LLM system. Mixing them is how keys leak into browsers and how agents bypass user ACLs. Humans use OIDC/SAML (previous sections); this section is machine authentication.

  **1. API key** — a **static secret** (header `x-api-key`, `Authorization: Bearer sk-…`; query params are a mistake). Identifies a **project, tenant, or customer integration**, not a human. Easy to mint; hard to attribute to a person; leak = full power until rotated or gated. Where they belong: customer calling **your** public API; **virtual keys** in a gateway; never as the only “login” for a UI. LiteLLM / AI gateways often give tenants **virtual keys** while the gateway holds **provider** keys in a vault — API-key UX + centralized custody. Scope virtual keys: models allowed, RPM, budget, tenant id.

  **2. Service account (workload identity object)** — a **first-class identity for software**: GCP service account, AWS IAM role (instance/task/pod identity), Azure managed identity / workload identity. Authenticates with **short-lived tokens** from the metadata service, STS, or projected SA tokens — not a password. Key files (GCP JSON keys, long-lived IAM users) exist and are **discouraged**: they leak via Git, Docker layers, and chat logs. Ideal for: backend calling Vertex / Bedrock / BigQuery / S3; CI deployers (with federation).

  **3. Federated identity / workload identity federation** — a workload that **already has** an OIDC token (GitHub Actions, GitLab, GKE, EKS IRSA, Kubernetes projected SA) **exchanges** it for cloud credentials. **No long-lived JSON keys.** GCP: Workload Identity Federation — attribute mapping from external `sub`/`aud` to a Google SA. AWS: IAM OIDC identity providers + `AssumeRoleWithWebIdentity` (EKS IRSA, GitHub OIDC). Azure: federated credentials on Entra apps. Same idea in **product** space: customer’s IdP federates **users** into your app (SSO). For **agents**, **on-behalf-of (OBO)** / token exchange (RFC 8693) so tools see the **user**, not a god-mode service account.

  | Caller | Present | Must not present |
  |--------|---------|------------------|
  | Browser user | OIDC session / user access token | Provider `sk-`, cloud JSON key |
  | Customer backend | Your API key or client-credentials token | Your **provider** key |
  | Your API pod | Workload identity / SA | User passwords |
  | CI pipeline | OIDC federation to cloud | Static cloud keys in GitHub secrets extras |
  | Agent tool hop | Exchanged OBO token (user+tenant+scope) | Unconstrained platform SA into CRM |

  **Client credentials:** the **app** is the subject. Correct for “embedder service reads **its** GCS bucket.” Wrong for “summarize **this user’s** mailbox.” **OBO / token exchange:** incoming user token + your client identity → new token with **audience = tool API**, **subject = user**, maybe downscoped. Correct for agents. If the tool only supports API keys, you still **authorize in your PEP** before using a tenant-scoped key.

* **The Alternatives:**  

  | Pattern | Attribution | Rotation | Enterprise fit |
  |---------|-------------|----------|----------------|
  | Shared provider API key in env | Poor | Manual | Demo only |
  | Per-tenant virtual key → gateway | Good (tenant) | Manageable | SaaS AI |
  | Per-user API keys to **your** API | Good (user) | Painful at scale | Scripts, not SSO |
  | Cloud SA + workload identity | Excellent (workload) | Automatic TTL | Platform internals |
  | User OBO to downstream SaaS | Best (user+tenant) | Token TTL | Agents in SaaS tools |
  | Customer-managed keys in their vault | Strong compliance | Customer-operated | High-trust / VPC |
  | Long-lived GCP JSON / AWS IAM user | Terrible | Forgotten | Incident waiting |

  The syllabus selects **vaulted provider keys + per-tenant virtual keys + workload identity for runtime/CI + OBO for agent tool hops** — never one global provider key as user auth, never provider keys in browsers.

* **Failure Modes:**  
  - Static keys in Git → class of breach (history rewrite does not save you; assume leaked).  
  - **One global OpenAI key for all tenants:** no cost isolation, no kill-switch per customer, prompt injection that exfiltrates env → **cross-tenant spend and data**.  
  - **Agents that call CRM as a service account:** bypass **user** ACLs → data exfiltration and compliance failure.  
  - **Provider keys in the browser or mobile app:** trivially extracted; bill and quota die; ToS violations.  
  - **CI JSON keys:** stolen GitHub secret = production cloud admin (Week 18 already said OIDC to cloud; this week is why).

* **Average vs. Strong Engineer:**  
  **Average:** provider key in AWS Secrets Manager / GCP Secret Manager / Vault; one app SA; customer API keys for your public API; GitHub OIDC to deploy.  
  **Strong:** workload identity **everywhere** (runtime + CI); per-tenant keyed gateway with budgets and model allowlists; OBO / RFC 8693 into tools — never “platform admin” into customer SaaS; key scoping + automatic rotation + anomaly detection (impossible travel / new model / spend spike — Week 20 metrics, this week’s identity labels); break-glass: short-lived, ticketed, audited impersonation — not a shared `root` key in 1Password forever; MCP: prefer OAuth on remote servers; treat static keys as local-dev only.

* **Worked Example:**  
  Deployment Copilot’s LiteLLM (or equivalent) gateway holds the real OpenAI/Anthropic key in Secret Manager. Each tenant gets a **virtual key** scoped to models, RPM, budget, and `tenant_id`. The API pod authenticates to cloud APIs via workload identity — no JSON key in the image or env. CI uses GitHub OIDC → cloud STS / WIF to deploy the Week 18 digest. When an agent tool must write to Salesforce, the gateway exchanges the user’s token (RFC 8693) so Salesforce ACLs see the user; a platform SA is never used as a CRM god-mode identity.

* **Apply It:**  
  1. Move provider keys out of browsers/clients into a secret store; never share one provider key across tenants as the only control.  
  2. Issue per-tenant **virtual keys** (or equivalent) with model allowlist, RPM, budget, and tenant binding.  
  3. Use workload identity / short-lived SA tokens for API pods and CI; remove long-lived cloud JSON keys.  
  4. Customer-facing machine access: scoped API keys or client credentials to **your** API — not the provider key.  
  5. Agent tool hops: OBO / RFC 8693 with user+tenant+scope; authorize in PEP before any tenant-scoped fallback key.  
  6. Document break-glass as short-lived, ticketed, audited — not a standing shared root key.  
  7. `[NEEDS MORE RESEARCH]`: virtual keys vs full customer OIDC on every API call (partners vs interactive users); whether remote MCP servers should accept API keys at all or only OAuth; CMEK vs customer-bring-your-own-**provider** key (BYOK) as two different questionnaires; how to surface RFC 8693 `act` (“agent runtime X acting for user Y”) in traces.

---

### Data residency for enterprise AI

* **Fundamentals:**  
  **Data residency** = constraints on **where data is stored at rest** and often **where it is processed in use**. Enterprises (EU, public sector, healthcare, finance) ask more than “which AWS region is the API in?”

  Four questions every security questionnaire will rephrase: (1) Where do **prompts, documents, embeddings, and logs** live at rest? (2) Do **inference** requests leave the region (or country)? (3) Are prompts used for **provider training** / retained beyond the request (ZDR vs default logs)? (4) Who can access **ops** data (support, embedding vendors, observability SaaS, eval vendors)?

  Residency is **not** the same as:

  | Term | Typical meaning |
  |------|-----------------|
  | **Residency** | Geographic location of storage (and often processing) |
  | **Sovereignty** | Legal control / local operator / independent cloud (stronger political bar) |
  | **GDPR lawful basis / SCC** | Why you may process personal data and how you transfer it — legal, not a region dropdown |

  Buyers **bundle** these. FDEs must unbundle in the design doc, then **enforce** the parts that are technical.

  **Cloud building blocks:** region selection (`eu-west-1`, `europe-west4`, `me-central1`, etc.); organization policy / SCP deny creating resources outside an allow-list (GCP `gcp.resourceLocations`; AWS SCPs / RCPs); Assured Workloads / control packages (residency + personnel access — GCP Assured Workloads, EU Data Boundary); CMEK / CloudHSM — customer-managed encryption keys **in-region** (keys leaving the region can void the story); VPC endpoints / Private Link / PSC — API calls to Bedrock/Vertex stay on private backbone, still **check the service’s processing region**; contractual ZDR — provider zero-data-retention addenda. Technical features (prompt caching) may **conflict** with ZDR — always re-read the current trust center; offerings move.

  A single “we deploy in Frankfurt” claim fails if any hop is elsewhere:

  | Surface | Residency failure |
  |---------|-------------------|
  | Object store for PDFs | US bucket “for cost” |
  | Embedding API | US-only model endpoint |
  | Vector DB | Managed service with US replica / US control plane storing payloads |
  | LLM inference | Global router picks `us-east-1` at 3am |
  | Prompt cache | Provider cache in another region; ZDR off |
  | Eval / golden sets | Nightly job copies prompts to a US notebook |
  | Traces (Week 17) | US SaaS APM with full prompt bodies |
  | Support | Engineer pulls EU tenant HAR to a US laptop |
  | Agent tools | US Salesforce / Jira while claiming EU-only processing |

  **FDE rule:** embeddings + vector DB + object storage + LLM endpoint + eval logs + **tool destinations** must **align**, or you **disclose** the exception in the DPA — not in a footnote after signature. Customers often ask whether model weights were trained on EU data / in the EU — usually a **political/contract** question, not something your router can fix. **Inference in-region** with a US-trained model is often acceptable contractually and sometimes unacceptable politically. Document both.

* **The Alternatives:**  

  | Strategy | Pros | Cons |
  |----------|------|------|
  | Single-region deploy (`eu-west-1` only) | Clear story | Latency for global users; model SKU gaps |
  | Per-tenant regional pinning | Wins regulated deals | Multiplies infra; routing bugs = breaches |
  | Process in-region, log globally | Easy SRE | Often fails questionnaires |
  | On-prem / VPC self-hosted models | Max control | Ops, patching, weaker or delayed models |
  | Provider ZDR + regional endpoints | Pragmatic SaaS | Subprocessors, support access, cache features |
  | Assured Workloads / EU Data Boundary | Enforce create-time location | Not all products in-scope; personnel controls extra |

  The syllabus selects **residency as a router constraint** for Deployment Copilot: tenant config pins region; prompts, embeddings, indexes, logs, and tool hops must not silently leave; disclose training/retention.

* **Failure Modes:**  
  - Shipping EU customer PDFs to a US-only embedding pipeline → lose the deal or breach the DPA.  
  - “We use a US model API” without disclosure → fails security review; with disclosure may still fail customer policy.  
  - Accidentally enabling **provider training** on customer prompts → company-level incident.  
  - A **US-only observability vendor** with raw prompts voids an “EU residency” marketing claim even if object storage is in `europe-west1`.  
  - Agent graphs that call **US SaaS tools** while the LLM stays in-region → still a cross-border disclosure or a block.  
  - Prompt caching / features that conflict with claimed ZDR without feature flags per tenant.

* **Average vs. Strong Engineer:**  
  **Average:** one primary region; subprocessors list; DPA; “we don’t train on your data” screenshot from the vendor.  
  **Strong:** tenant `residency_region` in config; **router refuses** non-compliant providers (code, not wiki); separate regional stacks for high tiers (silo — next section); CMEK; Private Link; ZDR addenda **and** feature flags that disable conflicting caches; residency-aware RAG (corpus, index, and query path co-located); deny-by-default **egress** policies (Week 18 network + this week’s data); audit **agent tool calls** for region; support: in-region break-glass with just-in-time access; tests: tenant tagged `eu` cannot successfully call a US embedding stub.

* **Worked Example:**  
  An EU tenant of Deployment Copilot has `residency_region = europe-west1` / `eu-central-1` in tenant config. The router refuses US-only embedding and LLM SKUs for that tenant. PDFs land in an EU object prefix; embeddings and the vector index stay in-region; Cloud Logging / traces keep prompt bodies in-region (or redact if the APM cannot). ZDR addenda are on file; prompt-caching features that conflict with ZDR are disabled for that tenant via flag. Agent tool hops to US Salesforce are either blocked or explicitly disclosed in the DPA — not discovered after signature. A CI test asserts: token for EU tenant + US embedding stub → deny.

* **Apply It:**  
  1. List every residency surface: prompt, document store, embedding API, vector DB, LLM endpoint, prompt cache, eval logs, traces, support access, agent tool destinations.  
  2. Put `residency_region` (or equivalent) on tenant config; enforce in the **router** in code.  
  3. Align embeddings + vector DB + object storage + LLM + eval logs + tools, or disclose exceptions in the DPA.  
  4. Unbundle residency vs sovereignty vs GDPR lawful basis in the design doc — then enforce the technical parts.  
  5. Re-read provider ZDR vs prompt-caching docs before claiming both; gate conflicting features per tenant.  
  6. Add a test that an `eu`-tagged tenant cannot call a US-only embedding/LLM stub.  
  7. `[NEEDS MORE RESEARCH]`: whether in-region inference satisfies customers if weights were trained elsewhere (often contractually yes; sometimes politically no); cross-border support debug without moving payloads; multi-hop agents calling US SaaS while claiming EU residency — disclose, tokenize, or block; vector DB “serverless” global control planes with US metadata as deal-breaker or not.

---

### RBAC for multi-tenant AI systems

* **Fundamentals:**  
  **Multi-tenancy** = one platform serving many customers (**tenants**) with **isolation**. **RBAC** = permissions via **roles** (Admin, Analyst, Viewer, ConnectorAdmin, AgentApprover) assigned to **principals** (users, groups, service accounts, API keys).

  SaaS AI almost always needs **two axes**:

  1. **Tenant isolation** — Tenant A must never read Tenant B’s documents, embeddings, prompts, threads, traces, or keys. Failure = data leak / career-ending bug.  
  2. **In-tenant RBAC** — inside Tenant A, who can manage connectors, run agents, view logs, approve tool actions?

  A user can be Admin in Tenant A and Viewer in Tenant B (consultancies, multi-org IdPs). The token must not collapse that to a global Admin.

  **Authorization architecture (PEP / PDP)** — AWS Prescriptive Guidance for multi-tenant SaaS APIs:

  | Component | Job |
  |-----------|-----|
  | **PEP** (Policy Enforcement Point) | Gateway or service middleware: extract token, call PDP, **allow/deny**, never “UI only” |
  | **PDP** (Policy Decision Point) | Evaluates RBAC/ABAC (OPA/Rego, Cedar / Amazon Verified Permissions, custom) |
  | **PIP** (optional) | Extra attributes (sensitivity of doc, region, spend tier) |

  **Deny by default.** Unknown tenant claim → 401/403, not “empty results that leak existence” unless that is an explicit anti-enumeration choice. UI hiding buttons is not a PEP.

  | Pattern | Infra | Isolation | Cost |
  |---------|-------|-----------|------|
  | **Pool** | Shared cluster/DB; `tenant_id` everywhere | Software (RLS, IAM prefix, vector filter) | Lowest |
  | **Silo** | Per-tenant account/cluster/DB | Stronger; easier residency | Highest |
  | **Bridge** | Mix by tier | “Enterprise” silo, SMB pool | Medium complexity |

  Pool is the default FDE prototype; silo appears when residency, noisy neighbor, or “bring your own cloud” shows up.

  After OIDC/SAML, the **session or access token** should carry: `tenant_id` (stable internal id, not display name); `sub` (user); `roles` or mapped groups; optional `region` / `tier`. **Every** DB query, cache key, vector filter, object prefix, and trace attribute must be tenant-scoped. Object IDs are not a security boundary (`/docs/uuid` without tenant check is IDOR).

  | Surface | Isolation mechanism |
  |---------|---------------------|
  | Postgres / SQL | `tenant_id` on every row; RLS or mandatory WHERE; no raw `id` lookups without tenant |
  | Object storage | Prefix `s3://bucket/{tenant_id}/…` + IAM/policy that cannot list sibling prefixes |
  | Vector index | Namespace / filter `tenant_id == token.tenant`; never “global” semantic cache |
  | Redis / prompt cache | Key includes tenant (and user if answers are private) |
  | LLM gateway virtual keys | Per-tenant key → budget, models, RPM |
  | Traces / eval logs | Tenant attribute on every span; backends that cannot filter = residency + isolation fail |
  | Agent tool calls | Authorize **each** invocation with user+tenant; OBO token so CRM sees the user |

  | Model | Flexibility | Complexity |
  |-------|-------------|------------|
  | Pure RBAC | Simple | Role explosion (`EU_Finance_Read_PII_AgentApprove_…`) |
  | **ABAC** (dept, region, sensitivity, residency) | Fine-grained | Harder to reason; need PIP |
  | RBAC + ABAC hybrid | Practical enterprise | Need a real PDP |
  | **ReBAC** (Zanzibar-style relations) | Sharing graphs (“this folder”) | Ops + modeling cost |

  For **agents:** authorize **each tool invocation** with **user + tenant + action + resource**, not merely “they opened the WebSocket.” The LLM proposing SQL or a REST body does not grant permission — the **PEP** does.

  **Customer-admin trap:** tenant admins may invite users, mint **virtual API keys**, and map SSO groups. They must **not** set `tenant_id` on writes to another tenant, disable isolation filters, read platform provider keys, or expand their token `aud` to internal admin APIs. Platform operators use a **separate** IdP app / break-glass role with audit.

  The FDE-quality bar is **automated** tests: Token A + query designed for B’s namespace → **always deny**. Include RAG, cache get, trace export, and tool gateway — more important than a pretty roles UI.

* **The Alternatives:**  

  | Approach | Pros | Cons |
  |----------|------|------|
  | `tenant_id` column + role enum in app `if` | Ships | Scattered; missed path = leak |
  | Central PDP (OPA/Cedar) | One policy language; testable | Extra latency; policy ops |
  | DB RLS as backstop | Defense in depth | App still must pass tenant; migrations painful |
  | Silo per tenant | Easy questionnaires | Cost; slow features |
  | Pool + strict prefixing + tests | SaaS default | Discipline; one bug is existential |
  | UI-only RBAC | Pretty | Trivial privilege escalation via API |

  The syllabus selects **two-axis authorization** (hard cross-tenant wall + in-tenant roles) with PEP/PDP deny-by-default and tenant-keyed stores for Deployment Copilot. Pool is the default prototype; bridge/silo when residency or tier demands it.

* **Failure Modes:**  
  - Missing `tenant_id` on a **vector query** → **cross-tenant RAG leakage** (career-ending class of bug).  
  - **UI-only RBAC** (hiding buttons) without API enforcement → privilege escalation with curl.  
  - **Shared semantic cache** without tenant (and sometimes user) in the key → answer leakage; Week 20 will want that cache for latency — **this week forbids unkeyed cache**.  
  - **Agent with platform SA** → authorization theater; CRM ACLs never run.  
  - **IDOR** on thread IDs → prompt history of another customer.  
  - Customer admin able to disable isolation filters or read platform provider keys.

* **Average vs. Strong Engineer:**  
  **Average:** `tenant_id` column + role enum; JWT `org_id` from Auth0 Organizations / Okta orgs; gateway checks membership.  
  **Strong:** central PDP; deny-by-default; **integration tests** for cross-tenant access on every store; optional per-tenant encryption keys for high tiers; rate limits and **budgets per tenant** (identity of the key — previous section); audit log: tenant, user, action, resource, tool name, decision; pool model with prefixing as in Bedrock AgentCore guidance; generated SQL / tool args: allowlist of tables; PEP still applies **row** filters; approvals for high-risk tools: role-based **or** ReBAC owners — pick one and document. Okta/Auth0 org features are vendor implementations of tenant = organization; still **your** PEP must enforce.

* **Worked Example:**  
  After SSO, Deployment Copilot JWTs carry `org_id` / `tenant_id`, `sub`, mapped `roles`, and optional `tier` / `residency_region`. API middleware (PEP) calls a PDP (OPA/Cedar/custom); missing or mismatched tenant → 403. Every Postgres query includes `tenant_id`; object keys are `s3://…/{tenant_id}/…`; vector search always filters `tenant_id == token.tenant`; Redis cache keys include tenant (and user when answers are private); traces carry tenant attributes. In-tenant roles: Admin, Analyst, Viewer, AgentApprover — enforced at the API, not only by hiding UI buttons. Integration tests: Tenant A’s token querying Tenant B’s vector namespace, cache key, trace export, and tool gateway → must deny. High-tier EU customers may route to a silo stack; SMB stays on the pool.

* **Apply It:**  
  1. Put stable `tenant_id` (plus `sub`, roles, optional region/tier) in the session/access token after SSO.  
  2. Enforce isolation in **every** store: SQL, object prefix, vector filter, cache key, virtual key, traces, tool gateway.  
  3. Implement PEP at the API (gateway/middleware); deny by default; never rely on UI-only RBAC.  
  4. Separate cross-tenant isolation from in-tenant roles; do not collapse multi-org membership into a global Admin.  
  5. Constrain customer admins so they cannot set foreign `tenant_id`, disable filters, or read platform provider keys.  
  6. Add automated cross-tenant deny tests for RAG, cache, traces, and tools — ship these before a pretty roles UI.  
  7. `[NEEDS MORE RESEARCH]`: who approves high-risk agent actions — role-based approvers or per-resource owners (ReBAC); how to expose customer-admin RBAC without allowing isolation break; authorization for generated SQL/tool args beyond allowlist + row filters; whether eval traces are a separate sensitivity class inside the tenant; multi-tenant MCP — session tenant-bound vs host multiplexing; pool + RLS vs silo for a 50-tenant FDE deployment vs a 5,000-tenant SaaS; whether “customer admin” may mint keys that outlive SSO sessions.

---

## Chapter synthesis

Week 19 turns a Week 18 container into something an enterprise can **log into**, **federate**, **attribute**, **locate**, and **isolate**:

1. Humans authenticate with **OIDC (code + PKCE)**; validate `iss` / `aud` / `exp` / JWKS; never a hardcoded shared key.  
2. Enterprises still need **SAML** (ACS, Entity ID, certs, SP- and IdP-initiated) — broker it if the app is OIDC-native.  
3. Machines use **API keys / virtual keys / workload identity / OBO** — provider keys stay in the vault; agents do not wear a god-mode SA into CRM.  
4. **Residency** is the whole pipeline (prompt, embed, index, log, tool), enforced in the router and disclosed when it is not.  
5. **Two-axis RBAC**: hard tenant wall + in-tenant roles at the PEP; missing `tenant_id` on a vector query is SEV-0.

Interview artifact: **OIDC login + API call sequence** (no hardcoded key) + **one-page isolation design** (JWT → PEP → stores) + **residency surface list**.

Where research leaves open questions (three-party OAuth clients for agents, MCP audience design, logout mid-agent-run, SAML-vs-OIDC RFP trajectory, CMEK vs BYOK questionnaires, ReBAC vs role approvers, pool vs silo scale breakpoints), they are marked `[NEEDS MORE RESEARCH]` in Apply It rather than filled with invented defaults.
