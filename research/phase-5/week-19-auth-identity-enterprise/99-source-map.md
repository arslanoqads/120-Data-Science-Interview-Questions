# 99 — Week 19 master source map

> Consolidated index of RFCs, OpenID/OASIS specs, Auth0/Okta, AWS/GCP residency and SaaS auth, LiteLLM, YouTube. Legal sources only; no pirate book sites, no unauthorized course PDFs.

**Deep-pass date:** 2026-09-03. Re-fetch before shipping a lecture — Auth0 connection URL shapes, Okta Workforce OIDC vs SAML IdP-initiated behavior, Assured Workloads control-package region lists, provider ZDR vs prompt-cache interactions, and OAuth BCP numbering (RFC 9700) should be confirmed live.

**Not used:** pirate IAM/OAuth books, libgen, pdfcoffee, leaked Udemy/Maven decks. IETF RFC Editor / datatracker, OpenID Foundation, OASIS, vendor **docs** sites, AWS/GCP official docs and blogs, GitHub Docs, Anthropic docs, LiteLLM docs, official YouTube channels only.

---

## IETF — OAuth / JWT / related

| Topic | URL |
|-------|-----|
| RFC 6749 OAuth 2.0 Authorization Framework | https://datatracker.ietf.org/doc/html/rfc6749 |
| RFC 6750 Bearer tokens | https://datatracker.ietf.org/doc/html/rfc6750 |
| RFC 7636 PKCE | https://datatracker.ietf.org/doc/html/rfc7636 |
| RFC 7643 / 7644 SCIM | https://datatracker.ietf.org/doc/html/rfc7643 · https://datatracker.ietf.org/doc/html/rfc7644 |
| RFC 8252 OAuth for native apps | https://datatracker.ietf.org/doc/html/rfc8252 |
| RFC 8414 Authorization Server Metadata | https://datatracker.ietf.org/doc/html/rfc8414 |
| RFC 8628 Device Authorization Grant | https://datatracker.ietf.org/doc/html/rfc8628 |
| RFC 8693 Token Exchange | https://datatracker.ietf.org/doc/html/rfc8693 |
| RFC 8705 OAuth 2.0 Mutual-TLS | https://datatracker.ietf.org/doc/html/rfc8705 |
| RFC 8707 Resource Indicators | https://datatracker.ietf.org/doc/html/rfc8707 |
| RFC 8725 JSON Web Token Best Current Practices | https://datatracker.ietf.org/doc/html/rfc8725 |
| RFC 9068 JWT Profile for OAuth 2.0 Access Tokens | https://datatracker.ietf.org/doc/html/rfc9068 |
| RFC 9126 Pushed Authorization Requests | https://datatracker.ietf.org/doc/html/rfc9126 |
| RFC 9449 DPoP | https://datatracker.ietf.org/doc/html/rfc9449 |
| RFC 9700 OAuth 2.0 Security BCP | https://www.rfc-editor.org/rfc/rfc9700.html |
| RFC 7662 Token Introspection | https://datatracker.ietf.org/doc/html/rfc7662 |

---

## OpenID Foundation / OASIS

| Topic | URL |
|-------|-----|
| OpenID Connect Core 1.0 | https://openid.net/specs/openid-connect-core-1_0.html |
| OpenID Connect Discovery 1.0 | https://openid.net/specs/openid-connect-discovery-1_0.html |
| OASIS SAML 2.0 technical overview | https://docs.oasis-open.org/security/saml/Post2.0/sstc-saml-tech-overview-2.0.html |

---

## Auth0

| Topic | URL |
|-------|-----|
| OIDC protocol | https://auth0.com/docs/authenticate/protocols/openid-connect-protocol |
| Enterprise connections | https://auth0.com/docs/authenticate/enterprise-connections |
| Okta as identity provider | https://auth0.com/docs/authenticate/identity-providers/okta |
| SAML identity providers (ACS, Entity ID) | https://auth0.com/docs/authenticate/identity-providers/enterprise-identity-providers/saml |
| SAML protocol | https://auth0.com/docs/authenticate/protocols/saml |
| SAML IdP configuration settings | https://auth0.com/docs/authenticate/protocols/saml/saml-identity-provider-configuration-settings |
| Organizations (B2B tenants) | https://auth0.com/docs/manage-users/organizations |
| Support: Okta Workforce OIDC vs IdP-initiated | https://support.auth0.com/center/s/article/auth0-users-are-forced-to-re-enter-email-address-when-signing-in-to-an-okta-workforce-connection |

---

## Okta

| Topic | URL |
|-------|-----|
| OAuth / OpenID Connect concepts | https://developer.okta.com/docs/concepts/oauth-openid/ |
| SAML concepts | https://developer.okta.com/docs/concepts/saml/ |

---

## AWS — identity, tenancy, residency

| Topic | URL |
|-------|-----|
| Data privacy / residency building blocks | https://aws.amazon.com/compliance/data-privacy/ |
| AWS privacy | https://aws.amazon.com/privacy/ |
| SaaS multi-tenant API authorization (PEP/PDP) | https://docs.aws.amazon.com/prescriptive-guidance/latest/saas-multitenant-api-access-authorization/welcome.html |
| GenAI Lens — multi-tenant platform scenario | https://docs.aws.amazon.com/wellarchitected/latest/generative-ai-lens/multi-tenant-generative-ai-platform-scenario.html |
| OBO token exchange — Bedrock AgentCore Gateway | https://aws.amazon.com/blogs/machine-learning/implement-on-behalf-of-token-exchange-for-multi-tenant-agents-with-amazon-bedrock-agentcore-gateway/ |
| Pool-model multi-tenancy — AgentCore | https://aws.amazon.com/blogs/machine-learning/shared-infrastructure-isolated-tenants-pool-model-multi-tenancy-with-amazon-bedrock-agentcore/ |

---

## GCP — federation, residency, privacy

| Topic | URL |
|-------|-----|
| Workload Identity Federation | https://cloud.google.com/iam/docs/workload-identity-federation |
| Assured Workloads overview | https://cloud.google.com/assured-workloads/docs/overview |
| Assured Workloads data residency | https://cloud.google.com/assured-workloads/docs/data-residency |
| EU Data Boundary control package | https://cloud.google.com/assured-workloads/docs/control-packages/eu-data-boundary |
| Google Cloud privacy | https://cloud.google.com/privacy |

---

## GitHub / gateways / model providers

| Topic | URL |
|-------|-----|
| GitHub Actions OIDC to cloud | https://docs.github.com/en/actions/deployment/security/use-oidc |
| LiteLLM virtual keys | https://docs.litellm.ai/docs/proxy/virtual_keys |
| Anthropic prompt caching (ZDR interaction) | https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching |
| Open Policy Agent docs | https://www.openpolicyagent.org/docs/latest/ |

---

## YouTube (official / vendor engineering channels)

| Topic | URL |
|-------|-----|
| OktaDev — OAuth 2.0 and OpenID Connect (in plain English) | https://www.youtube.com/watch?v=996OiexHze0 |
| Auth0 — An Illustrated Guide to OAuth and OpenID Connect | https://www.youtube.com/watch?v=t18YB3xDdHo |
| OktaDev channel | https://www.youtube.com/@oktadev |
| Auth0 channel | https://www.youtube.com/@auth0 |
| Google Cloud Tech (WIF, Assured Workloads, IAM) | https://www.youtube.com/@GoogleCloudTech |
| AWS Cloud (IAM, Identity Center, multi-tenant SaaS) | https://www.youtube.com/@awscloud |

---

## Concept file map

| File | Primary sources |
|------|-----------------|
| [00](00-week-overview.md) | RFC 6749, OIDC Core, RFC 9700, Auth0 enterprise connections, AWS SaaS auth, GenAI Lens, OktaDev + Auth0 YouTube |
| [01](01-oauth2-oidc.md) | RFC 6749/6750/7636/8252/8693/8707/8725/9068/9126/9700, OIDC Core+Discovery, Auth0/Okta OIDC |
| [02](02-saml-legacy-sso.md) | OASIS SAML overview, Auth0 SAML IdP + settings, Okta SAML, SCIM RFCs |
| [03](03-api-keys-service-accounts-federation.md) | RFC 8693, GCP WIF, AWS OBO + GenAI Lens, LiteLLM virtual keys, GitHub OIDC |
| [04](04-data-residency.md) | AWS privacy, GCP Assured Workloads + EU boundary, Anthropic caching/ZDR |
| [05](05-rbac-multi-tenant.md) | AWS PEP/PDP, AgentCore pool model, OPA, Auth0 Organizations |
