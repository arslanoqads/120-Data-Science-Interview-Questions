# 01 — Messy SQL integration (schemas, docs, text-to-SQL)

> Week 21 — Connecting LLM systems to non-trivial existing data.  
> Research notes (raw). ETL/DLQ is file [02](02-tolerant-etl-ingestion.md). Timeouts to the warehouse are file [03](03-partial-failure-design.md).

---

## Fundamentals

Enterprise data is rarely warehouse-clean. FDE work means connecting agents/RAG to **production schemas** with:

- Cryptic names (`CUST_XREF_V3`, `stat_cd`)  
- Overloaded columns (status `1/2/3` meaning different things **per division**)  
- Soft deletes (`deleted_at`, `is_active=0`) applied inconsistently  
- Multiple sources of truth (CRM vs billing vs spreadsheet exports)  
- Sparse documentation; tribal knowledge in Slack  
- PII mixed into free-text notes  
- Timezone-naive timestamps; currency in cents vs dollars  
- Polymorphic FKs / EAV tables  

**Messy docs are part of the same surface.** A data dictionary that is three years stale is more dangerous than no dictionary: the model will cite it. Treat docs as **versioned artifacts** ingested with the same bronze/silver discipline as CSV (file 02): source, `as_of`, owner, checksum.

LLM integration patterns that work:

1. **Semantic layer first** — curated views / metrics (dbt models, LookML, Cube) so the LLM never sees a raw 400-table ERD. dbt public docs: models are SELECT statements materialized as tables/views and composed via `ref()` ([dbt models](https://docs.getdbt.com/docs/build/models)). That composition **is** the join graph you allowlist.  
2. **Text-to-SQL with allowlists** — approved views only; row-level security; read-only roles; `LIMIT`; **statement timeouts**; no multiple statements; no `INTO OUTFILE`. Middleware injects `tenant_id` / RLS; the model does not.  
3. **RAG over data docs** — ingest dictionaries, example queries, join paths, “do not join X to Y” notes; retrieve **before** generating SQL; require a citation or refuse the table.  
4. **Hybrid tools** — vetted parameterized tools (`get_invoice(id)`, `list_open_ar(account_id)`) for high-risk domains; open SQL only for analyst-grade questions on views.  
5. **Schema grounding** — filtered `information_schema` + redacted sample rows in the **tool result**, versioned with the schema snapshot id. Do **not** paste entire schemas into the system prompt (tokens, confusion, leakage).

EIP **Canonical Data Model**: each application has its own format; minimize N×N translators by agreeing on a common model ([pattern](https://www.enterpriseintegrationpatterns.com/patterns/messaging/CanonicalDataModel.html)). At 2 apps, CDM can be *more* translators; at 6 apps it wins (30 pairwise vs 12). Agents are another consumer: they should speak **Customer / Invoice / Ticket**, not `CUST_XREF_V3`.

Companion pattern: **Message Translator** between the producer’s format and the canonical one ([Message Translator](https://www.enterpriseintegrationpatterns.com/patterns/messaging/MessageTranslator.html)). FDE: dbt models and tool adapters *are* translators.

Google SRE on pipelines: real processing accumulates **operational** complexity — worker sizing, hanging chunks, preemptions, monitoring that only reports **on job completion** (so a hung periodic job is silent) ([Ch. 25](https://sre.google/sre-book/data-processing-pipelines/)). Pointing an agent at OLTP without a replica/warehouse strategy inherits **lock contention**, statement timeouts, and “thundering herd” if every user session issues a full scan.

**OLTP vs replica vs warehouse (default tool target):**

| Target | Use | Risk |
|--------|-----|------|
| Prod OLTP | Never for open SQL | Locks, PII, writes |
| Read replica | Narrow parameterized lookups | Replica lag; still RLS |
| Warehouse / semantic views | Analytics, text-to-SQL | Freshness SLO; still tenant filters |

SRE workbook: measure **end-to-end** freshness/correctness, not per-stage “job succeeded” ([Define SLOs](https://sre.google/workbook/data-processing/)). The user cares that AR in the answer matches billing within Y minutes, not that dbt ran.

**Multi-tenancy compounds schema mess.** Pool vs silo isolation still needs predicates the model cannot strip ([AWS Bedrock AgentCore pool model](https://aws.amazon.com/blogs/machine-learning/shared-infrastructure-isolated-tenants-pool-model-multi-tenancy-with-amazon-bedrock-agentcore/)). Week 19 RBAC applies **inside** SQL tools.

**Eval:** gold set of (question, allowed views, expected rows or equivalent SQL). Score **execution accuracy**, not string-match SQL. Shadow: generate, do not run, until the allowlist compiler is trusted.

---

## Alternatives & Tradeoffs

| Approach | Accuracy | Safety | Effort |
|----------|----------|--------|--------|
| Open text-to-SQL on raw OLTP | Fragile | Dangerous | Low upfront |
| Semantic views + text-to-SQL | Higher | Better | Medium |
| Hand-built tools only | Highest | Highest | High |
| Copy to warehouse then AI | Cleaner | Lag | ETL cost |
| Fine-tuned schema linker | Strong | Still needs RLS | ML cost |
| Dump full schema in prompt | Looks grounded | Leakage + confusion | Cheap until context fills |
| Docs RAG only, no SQL | Safe | Cannot compute | Low |

**Compiler vs model:** a SQL allowlist/parser that rejects unknown tables is cheaper than hoping the 70B model “knows” the policy. Put the join graph in code.

---

## Necessity

Raw prod DB without RLS → data breach or accidental `UPDATE`. FDE pilots die when the first SQL hallucination touches a write-capable role.

Ignoring soft deletes → answers about “customers that don’t exist.” Dual currency/timezone → wrong financial summaries and lost trust.

Ignoring **docs** → the model invents column semantics. Trusting **stale** docs without `as_of` → systematic bias by division.

Unbounded `SELECT` without timeout → warehouse slot exhaustion (your agent as denial-of-service). SRE hanging-chunk lesson: wait-for-all-before-next-stage plus kill-and-restart **without checkpoints** wastes the whole cycle ([Ch. 25](https://sre.google/sre-book/data-processing-pipelines/)). Agent analog: don’t kill the whole conversation because one GROUP BY is slow — cancel **that** statement, return `SQL_TIMEOUT`, continue with other tools.

---

## Industry Practice

**Common:** `information_schema` dump in the system prompt; shared DBA login; `SELECT *` examples in few-shots; wiki page last edited in 2019.

**Strong:**

1. Semantic layer owned by analytics eng; agent consumes **only** that.  
2. Approved join graph; SQL compiler; read-only role per tenant.  
3. NL→SQL eval with execution accuracy; regression on every schema snapshot bump.  
4. Shadow mode then human approve for any write path.  
5. Column-level masking / tokenization for PII **before** rows enter the model context.  
6. Tenant predicates injected by middleware.  
7. Schema snapshot **version** in traces (Week 17) so you can debug “it worked last Tuesday.”  
8. Statement timeout + max rows + max bytes returned to the model.  
9. Catalog freshness SLO: dictionary PRs when dbt models change (CI check).

---

## Concrete Scenario

**Interview walkthrough:** “Explain last month’s churn for Division B.”

1. Retrieve dictionary chunks: `stat_cd` for Division B; `churn` metric defined in dbt as `fct_subscription_churn`.  
2. Compiler allows `fct_subscription_churn` + `dim_account`; rejects `stg_salesforce_raw`.  
3. Generated SQL runs on warehouse with 8s timeout, `LIMIT 5000`.  
4. Result truncated flag if hit limit.  
5. Cite metric definition URL/path in the answer.

Strange Loop / industry talks on legacy data and production systems: [Strange Loop channel](https://www.youtube.com/@StrangeLoopConf).

SRE pipeline complexity (why you don’t `SELECT * AND SHIP`): [Data processing pipelines](https://sre.google/sre-book/data-processing-pipelines/).

EIP CDM: [Canonical Data Model](https://www.enterpriseintegrationpatterns.com/patterns/messaging/CanonicalDataModel.html).

AWS pool vs silo (schema mess × tenancy): [AgentCore multi-tenancy](https://aws.amazon.com/blogs/machine-learning/shared-infrastructure-isolated-tenants-pool-model-multi-tenancy-with-amazon-bedrock-agentcore/).

dbt models as the semantic building block: [Build models](https://docs.getdbt.com/docs/build/models).

---

## Open Questions

- When is it cheaper to fix the semantic layer than to push harder on agent reasoning?  
- Can LLMs maintain a living data catalog from query logs **safely** (PII in predicates, poisoning via malicious comments)?  
- OLTP vs replica vs warehouse: which is the **default** tool target for agents in 2026 products?  
- Who pages when the dictionary drifts from dbt — analytics or the FDE?

---

## Sources

- https://sre.google/sre-book/data-processing-pipelines/  
- https://sre.google/workbook/data-processing/  
- https://www.enterpriseintegrationpatterns.com/patterns/messaging/CanonicalDataModel.html  
- https://www.enterpriseintegrationpatterns.com/patterns/messaging/MessageTranslator.html  
- https://docs.getdbt.com/docs/build/models  
- https://aws.amazon.com/blogs/machine-learning/shared-infrastructure-isolated-tenants-pool-model-multi-tenancy-with-amazon-bedrock-agentcore/  
- https://www.youtube.com/@StrangeLoopConf  
