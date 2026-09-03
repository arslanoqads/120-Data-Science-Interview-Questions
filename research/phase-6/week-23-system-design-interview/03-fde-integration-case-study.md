# 03 — FDE integration case study: blockers become the job

> Week 23 — System design interview  
> Research notes (raw). Meta-concept: interview cases where integration constraints — not greenfield architecture — are the primary signal.

---

## Fundamentals

Forward Deployed / Applied AI Engineer work, per primary employers’ own words:

- **Palantir FDSE:** embed with customer; configure platforms; data integration; access controls; production outages; feed field learnings back to product. Not slide consulting ([Day in the Life](https://blog.palantir.com/a-day-in-the-life-of-a-palantir-forward-deployed-software-engineer-45ef2de257b1); [Who wants to be a Delta](https://blog.palantir.com/who-wants-to-be-a-delta-8d2ea948035)).  
- **OpenAI FDE:** discovery, technical scoping, system design, build, production rollout with strategic customers; hybrid of delivery + platform feedback; significant travel ([SF posting](https://openai.com/careers/forward-deployed-engineer-%28fde%29-sf-san-francisco/); [Gov posting](https://openai.com/careers/forward-deployed-engineer-gov-washington-dc/)).  
- **Anthropic FDE (Applied AI):** build production apps on Claude inside customer systems; deliver MCP servers, sub-agents, skills; white-glove deploy; **evaluation frameworks**; codify repeatable patterns back to Product/Engineering; thrive in ambiguity ([Greenhouse FDE](https://job-boards.greenhouse.io/anthropic/jobs/5391016008); [FDE Manager](https://job-boards.greenhouse.io/anthropic/jobs/5385634008)).

**Integration blockers** (SSO, VPC, messy schemas, undocumented APIs, data residency, change control, “who owns the gold dataset?”) are not interruptions—they **are** the engagement. Interview case studies should center unblocking a path to a **thin production slice**, not inventing a novel architecture in a vacuum.

### Case skeleton (use every time)

| Beat | What you say |
|------|----------------|
| **Clarify stakes** | Who user, cost of wrong answer, deadline, compliance |
| **Inventory constraints** | Data access, identity, network, owners, SLAs |
| **Thin slice** | One job / one corpus or tool / one KPI |
| **Unblock plan** | Adapter, synthetic/redacted data, contract test, escalation |
| **Risk + monitor** | What fails open/closed; how you know Monday |
| **Codify** | What becomes playbook / MCP / product feedback |

### Classic blockers → FDE-shaped moves

| Blocker | Monday move | Anti-pattern |
|---------|-------------|--------------|
| No prod data for 2 weeks | Redacted sample + synthetic goldens; contract on schema | Idle wait |
| SSO / IdP delay | Dev IdP + documented prod cutover checklist | Shadow deploy without auth |
| Undocumented API | Adapter over export/view + contract tests; escalate owner | Boil-the-ocean rewrite |
| Dirty SQL / ERD | Semantic layer + allowlisted tools (Week 21) | Open text-to-SQL on raw warehouse |
| Security review | Threat model + least privilege path + logging | “We’ll harden later” |
| Model quality complaints | Error analysis on *their* traces | Blind model swap |
| Scope creep | Written freeze + measurable pilot KPI | Infinite PoC |
| Data residency | Region-pinned deploy; no exfil embeddings if required | “API in us-east is fine” |

Palantir narratives emphasize rapid cycle with users and engineering rigor in the field — COVID-era examples stress pipelines, access controls, workflow UX, production outage investigation ([FDSE blog](https://blog.palantir.com/a-day-in-the-life-of-a-palantir-forward-deployed-software-engineer-45ef2de257b1)). Visual metaphor for composed workflows: Foundry deskside demos ([YouTube `bPGnvfyMuxE`](https://www.youtube.com/watch?v=bPGnvfyMuxE)).

Secondary synthesis of multi-round FDE loops exists (anecdotal; not official) — use only as practice structure, not employer gospel ([Medium six-round sketch](https://medium.com/@shivanathd/the-forward-deployed-engineer-interview-has-six-rounds-365df0544e2c)).

---

## Alternatives & Tradeoffs

| Response to blocker | FDE-shaped | Anti-pattern |
| --- | --- | --- |
| Missing API | Adapter + contract test; escalate owner | Wait for perfect platform |
| Dirty SQL | Bounded views/ETL with idempotent jobs | Boil-the-ocean warehouse rewrite |
| Security review | Threat model + least privilege path | Shadow IT deploy |
| Model quality complaints | Error analysis on *their* traces | “Try GPT-whatever” |
| Scope creep | Written freeze + measurable pilot KPI | Infinite PoC |
| Push back hard | When safety / residency / ACL at risk | Performative disagreement on taste |
| Absorb chaos | Short-term to ship slice | Permanent heroics without codifying |

---

## Necessity

Candidates who only talk greenfield RAG demos fail FDE scenarios that ask: “Customer won’t give prod data for two weeks—what do you do Monday?”

Frontier postings explicitly reward production deployment in **customer environments**, MCP/agent packages, and eval frameworks — i.e., institutionalizing integration patterns ([Anthropic](https://job-boards.greenhouse.io/anthropic/jobs/5391016008); [OpenAI](https://openai.com/careers/forward-deployed-engineer-%28fde%29-sf-san-francisco/)).

---

## Industry Practice

| Bar | What it looks like |
|-----|--------------------|
| **Common** | Ideal architecture diagram; ignore identity/network |
| **Strong** | Constraint inventory; thin slice; written KPI; escalation path |
| **Senior FDE** | Codifies adapter → reusable MCP/playbook; feeds product; handles outage |

Reported FDE loops (secondary; cautious) often include a **customer scenario** round testing composure, clarifying questions, and prioritization. Anthropic manager/Head of FDE postings stress playbooks, MCP/agent packages, measurable time-to-value.

---

## Concrete Scenario (URL)

**Interview prompt:** Healthcare customer wants a policy assistant. Prod PHI corpus blocked 3 weeks. Okta SSO in security queue. They have a CSV export of de-identified FAQs and a legacy SOAP “getClaimStatus” used by one internal app.

**Strong Monday plan:**

1. Freeze pilot: FAQ assistant only; no PHI; citation required; abstain on miss.  
2. Ingest CSV → hybrid index; golden set from 30 labeled FAQs.  
3. SOAP adapter behind one read-only tool with timeout + circuit breaker; no writes.  
4. Dev auth stub; SSO cutover checklist owned with security.  
5. Eval harness + weekly taxonomy review with champion user.  
6. Write engagement note: what becomes MCP server template for next hospital.

Primary role definitions:

- https://blog.palantir.com/a-day-in-the-life-of-a-palantir-forward-deployed-software-engineer-45ef2de257b1  
- https://blog.palantir.com/who-wants-to-be-a-delta-8d2ea948035  
- https://openai.com/careers/forward-deployed-engineer-%28fde%29-sf-san-francisco/  
- https://openai.com/careers/forward-deployed-engineer-gov-washington-dc/  
- https://job-boards.greenhouse.io/anthropic/jobs/5391016008  
- https://job-boards.greenhouse.io/anthropic/jobs/5385634008  
- Deskside compose demo: https://www.youtube.com/watch?v=bPGnvfyMuxE  

---

## Open Questions

- How much “push back on customer” vs “absorb chaos” do labs want in 2026?  
- Are MCP servers now a default artifact expectation in Anthropic-style loops?  
- How to discuss classified/gov constraints without leaking or fabricating?  
- Travel expectations: how to answer honestly from public postings (25–50% ranges)?

---

## Sources

- Palantir FDSE day-in-life: https://blog.palantir.com/a-day-in-the-life-of-a-palantir-forward-deployed-software-engineer-45ef2de257b1  
- Palantir Delta reflection: https://blog.palantir.com/who-wants-to-be-a-delta-8d2ea948035  
- OpenAI FDE SF: https://openai.com/careers/forward-deployed-engineer-%28fde%29-sf-san-francisco/  
- OpenAI FDE Gov: https://openai.com/careers/forward-deployed-engineer-gov-washington-dc/  
- Anthropic FDE: https://job-boards.greenhouse.io/anthropic/jobs/5391016008  
- Anthropic FDE Manager: https://job-boards.greenhouse.io/anthropic/jobs/5385634008  
- Palantir deskside demo (YouTube): https://www.youtube.com/watch?v=bPGnvfyMuxE  
- Secondary FDE loop sketch (anecdotal): https://medium.com/@shivanathd/the-forward-deployed-engineer-interview-has-six-rounds-365df0544e2c  
- Chip Huyen GenAI platform (compose progressive stack): https://huyenchip.com/2024/07/25/genai-platform.html  
