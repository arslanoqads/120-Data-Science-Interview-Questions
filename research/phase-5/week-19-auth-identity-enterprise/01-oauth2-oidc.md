# 01 — OAuth 2.0 and OpenID Connect (OIDC)

> Week 19 — protocol fundamentals for human SSO and API access tokens.  
> Research notes (raw). SAML is file [02](02-saml-legacy-sso.md); machine identity is [03](03-api-keys-service-accounts-federation.md).

---

## Fundamentals

### OAuth 2.0 is not “login”

**OAuth 2.0** is an **authorization** framework. A **client** obtains an **access token** so it can call a **resource server** with the **resource owner’s** delegated permission — or with its own identity (client credentials). The password stays at the **authorization server** ([RFC 6749](https://datatracker.ietf.org/doc/html/rfc6749)).

Using OAuth **without** an identity layer as “login” (treat access token as proof of who the user is, without `aud`/`iss` discipline) is a long-standing anti-pattern. **OpenID Connect** exists so authentication is explicit.

### Roles (RFC 6749 §1.1)

| Role | In an AI product |
|------|------------------|
| Resource owner | End user (or org admin granting tenant-wide consent) |
| Client | Browser BFF, native app, agent runtime, MCP host |
| Authorization server | Okta, Entra ID, Auth0, Keycloak, customer IdP |
| Resource server | Your FastAPI, LiteLLM gateway, tool API |

### Tokens

| Token | Purpose | Typical format |
|-------|---------|----------------|
| **Authorization code** | One-time; swapped at token endpoint; never a session | Opaque string |
| **Access token** | Call APIs (`Authorization: Bearer`) | Opaque or JWT ([RFC 9068](https://datatracker.ietf.org/doc/html/rfc9068) JWT profile) |
| **Refresh token** | New access tokens without UX | Opaque; store like a secret; rotate ([RFC 9700](https://www.rfc-editor.org/rfc/rfc9700.html)) |
| **ID Token** | Prove who authenticated to **this client** | JWT only (OIDC) |

**ID Token** is for the **client**. **Access token** is for the **API**. Do not send ID Tokens as `Authorization` to your resource server unless you have a documented, audience-correct profile (usually you should not).

Bearer tokens: whoever holds them can use them ([RFC 6750](https://datatracker.ietf.org/doc/html/rfc6750)). Transmit only over TLS. Prefer short TTL. Sender-constrained options: mTLS ([RFC 8705](https://datatracker.ietf.org/doc/html/rfc8705)), DPoP ([RFC 9449](https://datatracker.ietf.org/doc/html/rfc9449)).

### OpenID Connect additions

OIDC Core ([spec](https://openid.net/specs/openid-connect-core-1_0.html)):

- Scope `openid` required for an ID Token.  
- Standard scopes `profile`, `email`, `address`, `phone`.  
- Claims in ID Token and/or UserInfo endpoint.  
- `nonce` in the ID Token binds the token to the authentication request (replay).  
- `at_hash` / `c_hash` when tokens are issued together.

**Discovery** ([OIDC Discovery](https://openid.net/specs/openid-connect-discovery-1_0.html); AS metadata [RFC 8414](https://datatracker.ietf.org/doc/html/rfc8414)): fetch `issuer`, `authorization_endpoint`, `token_endpoint`, `jwks_uri`, `userinfo_endpoint`, `code_challenge_methods_supported`.

**Validation checklist (FDE interview):**

1. Fetch JWKS; verify signature; **reject** `alg=none` and unexpected algs ([RFC 8725](https://datatracker.ietf.org/doc/html/rfc8725)).  
2. `iss` exact match to discovery issuer.  
3. `aud` contains **this** client (or API audience for access tokens).  
4. `exp` / `nbf` / `iat` with small clock skew.  
5. `nonce` if you sent one.  
6. For access tokens: `scope` / `scp` sufficient; tenant claim present.

### Flows FDEs must recognize

| Flow | Who | Notes |
|------|-----|-------|
| **Authorization Code + PKCE** | Browser, SPA, native user login | Default. PKCE `S256`. Public clients MUST; confidential SHOULD ([RFC 7636](https://datatracker.ietf.org/doc/html/rfc7636); RFC 9700). |
| **Client Credentials** | Service-to-service | No user. `grant_type=client_credentials`. Your agent **platform** talking to your own APIs — not “the user clicked send.” |
| **Refresh Token** | Long sessions | Rotate; bind to client; detect reuse (theft). |
| **Device Code** ([RFC 8628](https://datatracker.ietf.org/doc/html/rfc8628)) | CLI / limited input | User codes on a second device. |
| **Token Exchange** ([RFC 8693](https://datatracker.ietf.org/doc/html/rfc8693)) | On-behalf-of, impersonation, downscoping | **Agents calling downstream APIs** as the user. |
| **Implicit** (`response_type=token` / `id_token` in URL) | Legacy SPAs | **Do not use** — RFC 9700. Tokens leak via history/referrer. |
| **ROPC** (password grant) | Legacy | **Do not use** — RFC 9700. Breaks MFA/federation. |

**PKCE (RFC 7636):** client creates `code_verifier`; sends `code_challenge = BASE64URL(SHA256(verifier))`; token request must present the verifier. Stops **authorization code interception** on public clients and **code injection**. Originally for native apps; now BCP for essentially all code flows.

**Pushed Authorization Requests** ([RFC 9126](https://datatracker.ietf.org/doc/html/rfc9126)): PAR moves request parameters to a back-channel POST; front-channel only carries a request URI — reduces leaking `state`/PKCE in logs and referrers. Enterprise IdPs increasingly support it.

**Resource indicators** ([RFC 8707](https://datatracker.ietf.org/doc/html/rfc8707)): `resource` parameter so access tokens are **audience-restricted** to a specific API. Prevents a token minted for “chat API” from being accepted at “admin API.”

### AuthN vs AuthZ

OIDC answers **who**. Your **RBAC/ABAC/ReBAC** (file [05](05-rbac-multi-tenant.md)) answers **what**. Groups in the ID Token are **hints** until the PEP evaluates them.

### Logout

RP-initiated logout, session management, front-channel and back-channel logout are separate OIDC specs. Universal logout / continuous access evaluation (IdP-specific: Okta, Entra) matter when an employee is terminated **during** a long agent run.

Vendor orientation: [Auth0 OIDC protocol](https://auth0.com/docs/authenticate/protocols/openid-connect-protocol); [Okta OAuth/OIDC concepts](https://developer.okta.com/docs/concepts/oauth-openid/).

---

## Alternatives & Tradeoffs

| Approach | Pros | Cons |
|----------|------|------|
| OIDC SSO via enterprise IdP | MFA, lifecycle, audit, SCIM | Claim mapping; IdP quirks |
| CIAM broker (Auth0) + customer IdP | One integration in your app | Extra hop; cost; data processing addendum |
| Roll-your-own sessions/passwords | Fast prototype | No enterprise buy-in |
| API keys as user auth | Scripts | No SSO/MFA; leak blast radius |
| Opaque tokens + introspection ([RFC 7662](https://datatracker.ietf.org/doc/html/rfc7662)) | Central revoke | Latency; AS availability on every call |
| JWT access tokens | Local validate, scale | Revoke ≈ short TTL + denylist |
| BFF + httpOnly cookies | Refresh not in JS | CSRF defense required |
| SPA + tokens in memory | Simple | Refresh handling; XSS still catastrophic |
| DPoP / mTLS | Stolen bearer less useful | Client and gateway complexity |

---

## Necessity

Enterprises will not deploy your AI product without SSO. Mis-implemented OAuth is **account takeover**, not a style issue:

- Implicit flow or tokens in URLs.  
- Skipping `aud`/`iss` (accepting another app’s token).  
- `alg=none` or not pinning allowed algorithms.  
- No PKCE on public clients → code interception.  
- Redirect URI prefix matching (`https://app.com` vs `https://app.com.evil.tld`) — use **exact** registered URIs (RFC 9700).  
- Access token as ID; ID token as API credential.  
- Logging full tokens in LLM traces (Week 17 observability vs this week’s secret hygiene).

Skipping OIDC and shipping a hardcoded API key fails procurement and cannot deprovision.

---

## Industry Practice

**Common:** Auth0/Okta/Entra; Authorization Code + PKCE; validate JWT with JWKS; map `groups`/`roles` into app roles; refresh in a BFF cookie.

**Strong:**

- RFC 9700 as the checklist, not blog folklore.  
- Short-lived access tokens (minutes); rotating refresh.  
- Distinct `aud` per API; gateway rejects wrong audience.  
- PAR + PKCE for high-assurance customers.  
- Token exchange for agents; **downscope** before tools.  
- Continuous access evaluation / back-channel logout hooked to **cancel in-flight agent jobs** (policy choice — document it).  
- Separate IdP apps per environment.  
- Never long-lived user PATs for server-side agent actions.

---

## Concrete Scenario (URL)

**OktaDev — OAuth 2.0 and OpenID Connect (in plain English)** — visual roles, why implicit is wrong, ID vs access token:  
https://www.youtube.com/watch?v=996OiexHze0  

**Auth0 — An Illustrated Guide to OAuth and OpenID Connect:**  
https://www.youtube.com/watch?v=t18YB3xDdHo  

**Auth0 enterprise connections** (customer IdPs for B2B):  
https://auth0.com/docs/authenticate/enterprise-connections  

**Okta Workforce OIDC into Auth0:**  
https://auth0.com/docs/authenticate/identity-providers/okta  

**RFC 6749, RFC 7636, RFC 8252, RFC 8693, RFC 9700, OIDC Core:**  
https://datatracker.ietf.org/doc/html/rfc6749  
https://datatracker.ietf.org/doc/html/rfc7636  
https://datatracker.ietf.org/doc/html/rfc8252  
https://datatracker.ietf.org/doc/html/rfc8693  
https://www.rfc-editor.org/rfc/rfc9700.html  
https://openid.net/specs/openid-connect-core-1_0.html  

**AWS OBO for multi-tenant agents (Bedrock AgentCore Gateway + RFC 8693):**  
https://aws.amazon.com/blogs/machine-learning/implement-on-behalf-of-token-exchange-for-multi-tenant-agents-with-amazon-bedrock-agentcore-gateway/

---

## Open Questions

- Three-party agents: browser client vs agent runtime client — one OAuth client id or two with token exchange between them?  
- MCP servers: OAuth 2.1-style resource servers with PKCE; API keys still allowed for local stdio?  
- JWT access tokens vs opaque at the LLM gateway (introspection vs CPU for JWKS)?  
- Should tool calls require **step-up** authentication (recent MFA) for irreversible actions?  
- GNAP as OAuth successor — interview-relevant yet, or still IETF-niche?

---

## Sources

- https://datatracker.ietf.org/doc/html/rfc6749  
- https://datatracker.ietf.org/doc/html/rfc6750  
- https://datatracker.ietf.org/doc/html/rfc7636  
- https://datatracker.ietf.org/doc/html/rfc8252  
- https://datatracker.ietf.org/doc/html/rfc8414  
- https://datatracker.ietf.org/doc/html/rfc8628  
- https://datatracker.ietf.org/doc/html/rfc8693  
- https://datatracker.ietf.org/doc/html/rfc8707  
- https://datatracker.ietf.org/doc/html/rfc8725  
- https://datatracker.ietf.org/doc/html/rfc9068  
- https://datatracker.ietf.org/doc/html/rfc9126  
- https://www.rfc-editor.org/rfc/rfc9700.html  
- https://openid.net/specs/openid-connect-core-1_0.html  
- https://openid.net/specs/openid-connect-discovery-1_0.html  
- https://auth0.com/docs/authenticate/protocols/openid-connect-protocol  
- https://auth0.com/docs/authenticate/enterprise-connections  
- https://developer.okta.com/docs/concepts/oauth-openid/  
- https://www.youtube.com/watch?v=996OiexHze0  
- https://www.youtube.com/watch?v=t18YB3xDdHo  
