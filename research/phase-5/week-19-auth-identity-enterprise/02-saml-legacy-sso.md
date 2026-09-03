# 02 — SAML 2.0 (legacy enterprise SSO)

> Week 19 — XML SSO that still appears in RFPs.  
> Research notes (raw). Prefer OIDC for **new** app protocols ([01](01-oauth2-oidc.md)); still **support** SAML for buyers.

---

## Fundamentals

**SAML 2.0** (Security Assertion Markup Language) is an OASIS standard for exchanging **authentication and attribute assertions** in XML. It remains dominant in large enterprises, government, education, and older IdPs (ADFS, older Ping, some Okta/Entra apps configured years ago). Technical overview: [OASIS SAML 2.0 technical overview](https://docs.oasis-open.org/security/saml/Post2.0/sstc-saml-tech-overview-2.0.html) (public OASIS document).

### Roles

| Role | Who |
|------|-----|
| **IdP** (Identity Provider) | Okta, Microsoft Entra ID, ADFS, Ping, Shibboleth — authenticates the user, issues a signed **assertion** |
| **SP** (Service Provider) | Your app or your CIAM broker — consumes the assertion, creates a session |
| **Principal** | The user |

The **assertion** is XML: subject (NameID), conditions (NotBefore/NotOnOrAfter, **AudienceRestriction**), attribute statements (email, groups, department), optionally authn context (password vs MFA). The IdP **signs** with an X.509 certificate. Optionally the assertion or NameID is **encrypted** to the SP cert.

### Bindings you will see

- **HTTP-Redirect** — typically SP → IdP **AuthnRequest** (deflate + query string).  
- **HTTP-POST** — typically IdP → SP **Response** with assertion to the **Assertion Consumer Service (ACS)** URL.  
- Artifact binding exists; rare in SaaS onboarding.

### SP-initiated vs IdP-initiated

**SP-initiated:** user hits `https://app.example/login` → SP builds AuthnRequest → redirect to IdP SSO URL → user authenticates → POST assertion to ACS. You can relay `RelayState` (return URL / tenant hint). This is the analogue of OIDC’s authorization request.

**IdP-initiated:** user clicks the app tile in the Okta/Entra portal. **No prior AuthnRequest from you.** IdP POSTs a Response to ACS, often with `RelayState` configured in the IdP app. OIDC does **not** natively have the same “unsolicited IdP start” as first-class; brokers document workarounds (SAML connection, bookmark apps). Auth0 notes Okta Workforce **OIDC** connections do not support IdP-initiated the way SAML does:  
https://support.auth0.com/center/s/article/auth0-users-are-forced-to-re-enter-email-address-when-signing-in-to-an-okta-workforce-connection

FDE implication: if the customer’s success criterion is “tile in Okta works with one click,” you likely need **SAML** or a vendor-specific IdP-initiated OIDC hack — do not promise OIDC-only without checking.

### Metadata — the onboarding contract

IdP and SP exchange **metadata XML** (or equivalent form fields):

| Field | Failure mode if wrong |
|-------|------------------------|
| **Entity ID** (SP and IdP unique URIs/URNs) | Audience mismatch; assertion rejected |
| **ACS URL** (SP) | Assertion POSTs to nowhere / 404; #1 ticket |
| SSO / SLO URLs | Redirect loops |
| Signing cert (IdP → SP) | Signature invalid after IdP cert rotation |
| NameID format | Duplicate users (`email` vs persistent opaque) |

Auth0 as SP (typical broker):

- ACS / Post-back: `https://{yourDomain}/login/callback?connection={yourConnectionName}`  
- Entity ID: `urn:auth0:{yourTenant}:{yourConnectionName}` (customizable via Management API `connection.options.entityId`)  

Docs: [Connect your app to SAML IdPs](https://auth0.com/docs/authenticate/identity-providers/enterprise-identity-providers/saml); [SAML IdP configuration settings](https://auth0.com/docs/authenticate/protocols/saml/saml-identity-provider-configuration-settings); protocol overview [Auth0 SAML](https://auth0.com/docs/authenticate/protocols/saml).

Okta developer SAML concept page: [SAML](https://developer.okta.com/docs/concepts/saml/).

### Security checks the SP must perform

1. **Signature valid** over assertion (or response) using **current** IdP cert; do not skip in “dev.”  
2. **AudienceRestriction** includes **your** Entity ID.  
3. **Destination** / recipient matches ACS.  
4. **Time window** with clock skew budget (NTP on both sides; classic “NotOnOrAfter already passed”).  
5. **InResponseTo** matches AuthnRequest ID for SP-initiated (IdP-initiated has none — policy choice).  
6. Decrypt if encrypted; never log raw assertions with PII in LLM traces.

### Clock skew and cert rotation

SAML outages cluster around **expired IdP signing certs** and **clock skew**. Strong practice: dual-cert windows (IdP publishes new cert in metadata before switching). Document who owns rotation (customer IT vs you).

### JIT vs SCIM

**JIT (just-in-time):** first successful assertion creates the user from attributes. Fast; deprovision is weak (user still exists until SSO fails). **SCIM** ([RFC 7643](https://datatracker.ietf.org/doc/html/rfc7643) / [RFC 7644](https://datatracker.ietf.org/doc/html/rfc7644)): IdP pushes create/update/disable. Enterprises will ask for SCIM on the same questionnaire as SAML.

### FDE rule

**Support SAML for enterprise SSO even if the app is OIDC-native** — usually a **broker** (Auth0, Okta CIAM, Entra External ID) or the customer’s IdP federating SAML into an OIDC app you already have. Implementing a SAML SP from scratch is rarely worth it unless you are the IdP vendor.

---

## Alternatives & Tradeoffs

| Protocol | Enterprise reality | DX |
|----------|--------------------|-----|
| SAML 2.0 | Ubiquitous legacy; IdP-initiated tiles; gov/edu | XML, cert rotation, clock skew, attribute mapping |
| OIDC | Modern default; APIs + mobile + PKCE | Preferred for new builds |
| Both via broker | Sell to anyone | Extra hop, claim mapping, data processing |
| WS-Fed | Some Microsoft estates | Even more legacy; treat like SAML for scoping |

**Direct SAML SP in the product** vs **broker:** direct reduces a vendor; you own CVE surface and cert ops. Broker is how most AI startups close the first ten enterprise logos.

---

## Necessity

Refusing SAML loses Fortune / public-sector deals that cannot (or will not) turn on OIDC for a new SaaS this quarter.

Broken **ACS URL** / **Entity ID** mismatches are the #1 onboarding failure — the IdP “test” button succeeds in their console and your app never sees a POST.

Ignoring **signature** or **AudienceRestriction** → trivial assertion spoofing (unsigned XML, wrong audience).

NameID as email without `email_verified`-equivalent process → account takeover when IdP attributes are editable unsafely; prefer persistent NameID + separate email attribute.

---

## Industry Practice

**Common:** Auth0/Okta SAML SP; customer uploads IdP metadata + signing cert; map `email` → user; JIT on first login; SP-initiated for “Log in” button; IdP-initiated for tile.

**Strong:**

- Signed assertions **required**; encrypted assertions when attributes are rich (SSN, student IDs).  
- Dual-cert rotation runbooks; metadata URL if the IdP publishes one (refresh, don’t screenshot certs).  
- Test **both** SP- and IdP-initiated in staging (Week 18 staging digest + this week’s IdP apps).  
- Exact Entity ID / ACS **per environment** (`-dev` vs `-prod` connections).  
- SCIM for disable/delete; JIT only as fallback.  
- Cap / map AD groups (customers stuffing 50 groups into assertions).  
- Document RelayState size limits (some IdPs truncate).

---

## Concrete Scenario (URL)

**Auth0 — Connect your app to SAML Identity Providers** (ACS, Entity ID, X.509):  
https://auth0.com/docs/authenticate/identity-providers/enterprise-identity-providers/saml  

**Auth0 — SAML protocol and IdP settings:**  
https://auth0.com/docs/authenticate/protocols/saml  
https://auth0.com/docs/authenticate/protocols/saml/saml-identity-provider-configuration-settings  

**Okta — SAML concepts (developer):**  
https://developer.okta.com/docs/concepts/saml/  

**OASIS — SAML 2.0 technical overview:**  
https://docs.oasis-open.org/security/saml/Post2.0/sstc-saml-tech-overview-2.0.html  

**IdP-initiated gap on Okta Workforce OIDC (why SAML still matters for tiles):**  
https://support.auth0.com/center/s/article/auth0-users-are-forced-to-re-enter-email-address-when-signing-in-to-an-okta-workforce-connection  

**OktaDev OIDC talk** (contrast with SAML mentally; same SSO goal):  
https://www.youtube.com/watch?v=996OiexHze0  

**Google Cloud / identity conference-style SSO** (Cloud Next sessions on workforce identity; channel):  
https://www.youtube.com/@GoogleCloudTech  

---

## Open Questions

- How long will RFPs say “SAML required” vs “OIDC preferred, SAML accepted”?  
- Should AI products expose a SAML SP **directly** or only via CIAM?  
- Attribute bloat: 50 AD groups in every assertion — map in broker or query Graph/SCIM asynchronously?  
- SLO (single logout): worth the XML pain when agent jobs are mid-flight?  
- Encrypted assertions vs relying on TLS + short-lived sessions for PII?

---

## Sources

- https://docs.oasis-open.org/security/saml/Post2.0/sstc-saml-tech-overview-2.0.html  
- https://auth0.com/docs/authenticate/identity-providers/enterprise-identity-providers/saml  
- https://auth0.com/docs/authenticate/protocols/saml  
- https://auth0.com/docs/authenticate/protocols/saml/saml-identity-provider-configuration-settings  
- https://developer.okta.com/docs/concepts/saml/  
- https://support.auth0.com/center/s/article/auth0-users-are-forced-to-re-enter-email-address-when-signing-in-to-an-okta-workforce-connection  
- https://datatracker.ietf.org/doc/html/rfc7643  
- https://datatracker.ietf.org/doc/html/rfc7644  
- https://www.youtube.com/watch?v=996OiexHze0  
- https://www.youtube.com/@GoogleCloudTech  
