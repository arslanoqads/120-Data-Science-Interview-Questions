# Week 19 Textbook Chapter — Auth, identity, and enterprise AI constraints

> **Status:** COMPLETE  
> **Source:** `research/phase-5/week-19-auth-identity-enterprise/`  
> **Chapter:** [chapter.md](chapter.md)

## Concepts covered

- [x] OAuth 2.0 and OpenID Connect (OIDC)
- [x] SAML 2.0 (legacy enterprise SSO)
- [x] API keys, service accounts, and federated identity
- [x] Data residency for enterprise AI
- [x] RBAC for multi-tenant AI systems

## Structure check

Each concept includes Fundamentals, The Alternatives, Failure Modes, Average vs. Strong Engineer, Worked Example, and Apply It.

## Syllabus build

You already have a **containerized, staged LLM service** (Week 18). This week you **stop treating a secret env var as “login.”** Human login is OIDC (Authorization Code + PKCE; validate `iss`/`aud`/`exp`/JWKS). Machines use scoped keys, service accounts / workload identity, and OBO — not the provider key in the client. Enterprise SSO includes SAML (Entity ID, ACS, certs, SP- and IdP-initiated). Residency is a router constraint across prompt, embed, index, log, and tool. Isolation is enforced in every store with in-tenant RBAC at the API. Interview artifact = OIDC login + API call sequence (no hardcoded key) + one-page isolation design (JWT → PEP → stores) + residency surface list.
