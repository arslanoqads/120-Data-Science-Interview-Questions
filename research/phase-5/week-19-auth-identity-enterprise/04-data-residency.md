# 04 — Data residency for enterprise AI

> Week 19 — where prompts, embeddings, logs, and tool payloads may live and be processed.  
> Isolation of tenants is [05](05-rbac-multi-tenant.md); identity of callers is [01](01-oauth2-oidc.md)–[03](03-api-keys-service-accounts-federation.md).

---

## Fundamentals

**Data residency** = constraints on **where data is stored at rest** and often **where it is processed in use**. Enterprises (EU, public sector, healthcare, finance) ask more than “which AWS region is the API in?”

Four questions every security questionnaire will rephrase:

1. Where do **prompts, documents, embeddings, and logs** live at rest?  
2. Do **inference** requests leave the region (or country)?  
3. Are prompts used for **provider training** / retained beyond the request (ZDR vs default logs)?  
4. Who can access **ops** data (support, embedding vendors, observability SaaS, eval vendors)?

Residency is **not** the same as:

| Term | Typical meaning |
|------|-----------------|
| **Residency** | Geographic location of storage (and often processing) |
| **Sovereignty** | Legal control / local operator / independent cloud (stronger political bar) |
| **GDPR lawful basis / SCC** | Why you may process personal data and how you transfer it — legal, not a region dropdown |

Buyers **bundle** these. FDEs must unbundle in the design doc, then **enforce** the parts that are technical.

### Cloud building blocks

- **Region selection** — `eu-west-1`, `europe-west4`, `me-central1`, etc.  
- **Organization policy / SCP** — deny creating resources outside an allow-list (GCP `gcp.resourceLocations`; AWS SCPs / RCPs).  
- **Assured Workloads / control packages** — folders that apply residency + personnel access controls ([GCP Assured Workloads overview](https://cloud.google.com/assured-workloads/docs/overview); [data residency](https://cloud.google.com/assured-workloads/docs/data-residency); [EU Data Boundary](https://cloud.google.com/assured-workloads/docs/control-packages/eu-data-boundary)).  
- **CMEK / CloudHSM** — customer-managed encryption keys **in-region** (keys leaving the region can void the story).  
- **VPC endpoints / Private Link / PSC** — API calls to Bedrock/Vertex stay on private backbone; still **check the service’s processing region**.  
- **Contractual ZDR** — provider zero-data-retention addenda. Technical features (prompt caching) may **conflict** with ZDR — Anthropic documents ZDR interaction with prompt caching ([prompt caching](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching)). Always re-read the current trust center; offerings move.

AWS orientation for questionnaires: [AWS data privacy](https://aws.amazon.com/compliance/data-privacy/), [AWS privacy](https://aws.amazon.com/privacy/). Multi-tenant AI platform scenario (keys, tenancy, isolation — residency is a neighbor concern): [GenAI Lens](https://docs.aws.amazon.com/wellarchitected/latest/generative-ai-lens/multi-tenant-generative-ai-platform-scenario.html). GCP privacy hub: [cloud.google.com/privacy](https://cloud.google.com/privacy).

### The AI pipeline is many stores

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

**FDE rule:** embeddings + vector DB + object storage + LLM endpoint + eval logs + **tool destinations** must **align**, or you **disclose** the exception in the DPA — not in a footnote after signature.

### Inference vs training vs weights

Customers often ask: “Were the model weights trained on EU data / in the EU?” That is **usually a political/contract** question, not something your router can fix. **Inference in-region** with a US-trained model is often acceptable contractually and sometimes unacceptable politically. Document both.

---

## Alternatives & Tradeoffs

| Strategy | Pros | Cons |
|----------|------|------|
| Single-region deploy (`eu-west-1` only) | Clear story | Latency for global users; model SKU gaps |
| Per-tenant regional pinning | Wins regulated deals | Multiplies infra; routing bugs = breaches |
| Process in-region, log globally | Easy SRE | Often fails questionnaires |
| On-prem / VPC self-hosted models | Max control | Ops, patching, weaker or delayed models |
| Provider ZDR + regional endpoints | Pragmatic SaaS | Subprocessors, support access, cache features |
| Assured Workloads / EU Data Boundary | Enforce create-time location | Not all products in-scope; personnel controls extra |

---

## Necessity

Shipping EU customer PDFs to a US-only embedding pipeline **loses the deal** or **breaches** the DPA.

“We use a US model API” without disclosure fails security review; with disclosure it may still fail the customer’s policy.

Accidentally enabling **provider training** on customer prompts is a **company-level incident**.

A **US-only observability vendor** with raw prompts voids an “EU residency” marketing claim even if GCS is in `europe-west1`.

Agent graphs that call **US SaaS tools** while the LLM stays in-region: still a **cross-border disclosure** or a **block**.

---

## Industry Practice

**Common:** one primary region; subprocessors list; DPA; “we don’t train on your data” screenshot from the vendor.

**Strong:**

- Tenant `residency_region` in config; **router refuses** non-compliant providers (code, not wiki).  
- Separate regional stacks for high tiers (silo — file [05](05-rbac-multi-tenant.md)).  
- CMEK; Private Link; ZDR addenda **and** feature flags that disable conflicting caches.  
- Residency-aware RAG: corpus, index, and query path co-located.  
- Deny-by-default **egress** policies (Week 18 network + this week’s data).  
- Audit **agent tool calls** for region.  
- Support: in-region break-glass with just-in-time access (Assured Workloads access justifications analogue on GCP).  
- Tests: tenant tagged `eu` cannot successfully call a US embedding stub.

Google Cloud Tech and AWS Cloud YouTube channels periodically cover sovereignty / Assured Workloads / AWS European Sovereign Cloud — cite the **current** official session rather than a stale third-party recap ([Google Cloud Tech](https://www.youtube.com/@GoogleCloudTech); [AWS Cloud](https://www.youtube.com/@awscloud)).

---

## Concrete Scenario (URL)

**AWS — data privacy / residency building blocks:**  
https://aws.amazon.com/compliance/data-privacy/  
https://aws.amazon.com/privacy/  

**AWS — GenAI Lens multi-tenant platform** (where keys and tenant data live):  
https://docs.aws.amazon.com/wellarchitected/latest/generative-ai-lens/multi-tenant-generative-ai-platform-scenario.html  

**GCP — Assured Workloads overview, data residency, EU Data Boundary:**  
https://cloud.google.com/assured-workloads/docs/overview  
https://cloud.google.com/assured-workloads/docs/data-residency  
https://cloud.google.com/assured-workloads/docs/control-packages/eu-data-boundary  
https://cloud.google.com/privacy  

**Anthropic prompt caching — ZDR interaction** (re-read before claiming ZDR + cache):  
https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching  

**YouTube — official cloud identity/residency talks (channel indexes):**  
https://www.youtube.com/@GoogleCloudTech  
https://www.youtube.com/@awscloud  

---

## Open Questions

- Does in-region **inference** satisfy customers if weights were trained elsewhere? (Often contractually yes; sometimes politically no.)  
- Cross-border **support**: debug EU tenants without moving payloads — session recording vs on-shore only SRE?  
- Multi-hop agents calling US SaaS while claiming EU residency — disclose, tokenize, or block?  
- Prompt caching / batch APIs that persist prompts — compatible with ZDR or a hard fork of features per tenant?  
- Vector DB “serverless” global control planes: is metadata in the US a deal-breaker?

---

## Sources

- https://aws.amazon.com/compliance/data-privacy/  
- https://aws.amazon.com/privacy/  
- https://docs.aws.amazon.com/wellarchitected/latest/generative-ai-lens/multi-tenant-generative-ai-platform-scenario.html  
- https://cloud.google.com/assured-workloads/docs/overview  
- https://cloud.google.com/assured-workloads/docs/data-residency  
- https://cloud.google.com/assured-workloads/docs/control-packages/eu-data-boundary  
- https://cloud.google.com/privacy  
- https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching  
- https://www.youtube.com/@GoogleCloudTech  
- https://www.youtube.com/@awscloud  
