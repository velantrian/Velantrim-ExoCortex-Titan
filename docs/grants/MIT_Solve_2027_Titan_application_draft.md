# MIT Solve 2027 — Titan application draft

**Status:** DRAFT ONLY — not submitted. Parent agent will type answers into https://solve.mit.edu/  
**Prepared:** 2026-11-06 (Europe/Berlin)  
**Challenge:** 2027 Global Economic Prosperity Challenge  
**Challenge URL:** https://solve.mit.edu/challenges/2027-global-economic-prosperity-challenge  
**Eligibility:** Does your solution address an economic opportunity or financial inclusion problem? → **Yes**  
**Dimension:** Create pathways to quality employment and economic opportunity, particularly for young people and workers excluded from formal labor markets as AI and other technologies reshape entry-level work  

**Sources used (evidence only):** Titan README / PROJECT_STATUS / REVIEWER_README; Titan LICENSE (MIT); Crystal README / STATUS (related line; AGPL-3.0); GitHub repo metadata; Notion MIT Solve note, grants hub, funding hub, NLnet original application + decision; MIT Solve challenge page; ILO GET for Youth 2024 news page for NEET statistic.

---

## Page 1 — Solution Profile

### 1. Organization name
Velantrim

### 2. Solution name (≤30 characters)
Titan  
*(5 characters)*

### 3. One-line summary / tagline (≤150 characters, 10–20 words)
Local-first verifiable memory for AI agents—inspectable writes, not black-box assistants.  
*(89 characters; 10 words)*

### 4. HQ city/region
Hamburg

### 5. HQ country
Germany

### 6. Organization type
**Other**

**Other explanation (≤100 words):**  
Velantrim is not registered as a legal entity. Titan is developed by founder Ruslan Gagiev as an independent open-source project under the Velantrim name. Prior grant forms (including NLnet) left the organization field blank and treated the applicant as an individual.  
*(41 words)*

### 7. Video pitch
Skip / leave blank — none.

### 8. What specific problem are you solving? (≤200 words)
As AI assistants and agents enter everyday work, entry-level and knowledge work is being reshaped. MIT Solve's 2027 Global Economic Prosperity Challenge notes that one in five young people (ages 15–24) are not in employment, education, or training, while AI and other technologies reshape entry-level work. ILO Global Employment Trends for Youth 2024 reported that 20.4% of young people globally were NEET in 2023. The problem I am solving is narrower and practical: when small organizations, agencies, and non-engineer workers start relying on AI agents for real tasks, those agents write into memory and change state without an inspectable audit trail. Finding an old note that "the purchase was approved" is not proof of current approval. Opaque memory turns AI from a productivity tool into an unaccountable black box—especially for people who cannot read model internals or hire a security team. Without local-first, verifiable memory controls, workers and small teams excluded from formal AI engineering roles cannot safely use agents for paid work, and organizations cannot trust what an agent recorded or changed later.  
*(174 words)*  
Sources: MIT Solve challenge page; ILO news on GET for Youth 2024 (https://www.ilo.org/resource/news/number-youth-not-employment-education-or-training-neet-cause-concern).

### 9. What is your solution? (≤200 words)
Titan is a research-grade, local-first AI memory and orchestration prototype. It separates recall, provenance, review, and authorized changes so that retrieving information is not treated as permission to trust or act on it. Core pieces that exist in the public GitHub main branch include: an epistemic state machine for facts; controlled write and promotion boundaries (TruthGate / WriteGate / PromotionGateway); provenance and hash-linked audit surfaces; hybrid retrieval with a lexical baseline and optional denser signals; an authenticated FastAPI server and console; and a replaceable LLM/provider layer. The public pitch I have already used is deliberately limited: Titan is a small open prototype of inspectable, hash-linked memory logging, with clear limits—no users yet, no external audit, and an unsigned chain. Related research/implementation work lives in the Crystal repository (local-first auditable memory); Crystal is a related line, not a second product claim for this application. Titan is meant so non-engineers and small organizations can direct AI coding assistants and agents with inspectable memory instead of opaque black-box tools.  
*(166 words)*

### 10. Who does your solution serve, and how will it impact their lives? (≤200 words)
Intended beneficiaries are small organizations and teams that want to use AI agents for real work but cannot afford opaque systems: agencies and similar knowledge-work groups, banks and other regulated teams evaluating agent memory before deployment, and non-engineer operators (including young people and workers outside formal AI engineering roles) who direct AI coding assistants. Today Titan serves 0 beneficiaries/customers. If the prototype matures into trusted local tooling, the impact would be practical agency: people can inspect what an agent wrote into memory, what changed later, and whether a recalled fact was ever admitted as trusted state. That is a pathway into quality AI-assisted work without requiring users to become model engineers. I do not claim current livelihood impact; impact depends on pilots, partners, and honest evaluation that do not yet exist.  
*(131 words)*

---

## Page 2 — Eligibility

### 11. Is technology core to your solution?
**Yes**

### 12. Does your solution address an economic opportunity or financial inclusion problem?
**Yes**

### 13. Stage of development
**Prototype**

### 14. Why that stage (≤200 words)
I select Prototype because a functioning research-grade software system already exists on GitHub main, not only a concept. Titan includes runnable local install paths (venv/uvicorn and a hardened Docker Compose profile), a FastAPI surface with /health-style checks, core memory/ESM and write-boundary modules, provenance/audit chain code, retrieval, authenticated MCP/tool wiring, and a documented verification baseline (ruff, mypy, pytest smoke/invariant/truth-gate/write-gate tests). Documentation explicitly labels the project research-grade and not production-authorized multi-user SaaS. There are 0 users. Concept-stage ideas are not reviewed for Global Challenges; Prototype matches Solve's definition of an initial working version that may still be getting feedback (often 0 users).  
*(100 words)*

---

## Page 3

### 15. How many beneficiaries / customers currently served?
**0**

### 16. Website
**Yes**

- Primary: https://github.com/velantrian/Velantrim-ExoCortex-Titan  
- Related research/implementation line (not a second product): https://github.com/velantrian/velantrim-exocortex-crystal

### 17. Which dimension of the challenge?
Create pathways to quality employment and economic opportunity, particularly for young people and workers excluded from formal labor markets as AI and other technologies reshape entry-level work.

### 18. How are you and your team well-positioned? (≤300 words)
I am a non-engineer founder based in Hamburg, Germany. I direct AI coding assistants to build and review open-source infrastructure rather than claiming a large engineering staff. That position is the point of Titan: if someone who is not a professional software engineer can build and operate an inspectable agent-memory stack, then small organizations and workers outside formal AI engineering markets can too. Evidence of the approach is public: the Titan repository (created 2026-07-09) and the related Crystal research/implementation line (created 2026-04-08), with status docs, reviewer maps, and test/CI baselines that refuse overclaim. I have already practiced grant-safe honesty across submissions—NLnet (not selected, 2026-10-09), Prototype Fund Crystal Evidence Core (submitted 7 Oct 2026, awaiting), EA Funds and BlueDot Titan Audit Kit requests (submitted 31 Oct 2026, awaiting), Emergent Ventures (submitted 2 July 2026, under review), and Hub71 (rejected). Those are applications, not awards or network memberships. I have no fabricated community-engagement numbers. My advantage is disciplined product boundaries: local-first, verifiable memory, replaceable models, and public limits (no users, unsigned chain, no external audit).  
*(173 words)*

### 19. Countries
- **Currently operate:** Germany (Hamburg-based)  
- **Additional countries next year:** none confirmed  
*(Do not claim Cambodia/SEA operations — that framing was a media pitch only.)*

### 20. How many people on the team (≤100 words)
Team size today is 1 person: founder Ruslan Gagiev. 0 full-time staff, 0 part-time staff, and 0 contractors are documented. Development is founder-directed with AI coding assistants; no co-founder or paid team is claimed.  
*(34 words)*

### 21. How long have you been working (≤100 words)
The Titan GitHub repository was created on 2026-07-09. The related Crystal repository was created on 2026-04-08. Broader Velantrim ExoCortex work has been underway since at least 2025. I do not inflate this into multi-year company tenure or a hired team.  
*(40 words)*

### 22. Why are you applying to Solve? (≤200 words)
I am applying to Solve for partners, scrutiny, and implementation support—not only prize money. Titan is stuck at an honest prototype gap: working local software exists, but there are no users, no external security audit, and an unsigned hash-linked audit chain. I need partners for carefully scoped pilots with agencies or small teams that already feel pressure to adopt AI agents; help on business model and evaluation so "inspectable memory" becomes a measurable service rather than only open code; and technical/legal guidance on what GDPR-relevant controls can and cannot claim. Solve's network, workshops, and Solver community are a fit for turning a research-grade audit surface into a human-centered pathway into AI-assisted work for people excluded from opaque enterprise AI stacks.  
*(120 words)*

### 23. Team Lead
- **Name:** Ruslan Gagiev  
- **Email:** velantrim@gmail.com  
- **Phone:** [PHONE — ask user]  
  *(Note for parent: NLnet application 2026-06-2ea listed +4917612656081; confirm before typing into Solve form. Not taken from vault.)*  
- **Backup contacts:** blank (none documented for this application)

### 24. US resident
**No**

### 25. Gender / transgender / race
**Prefer not to answer**

### 26. Previously selected as MIT Solve Solver
**No**

### 27. Other entrepreneurship network (incubator / accelerator / VC / fellowship joined)
**No**  
Hub71 was rejected (does not count as joining). Grant applications (NLnet, Prototype Fund, EA Funds, BlueDot, Emergent Ventures) are submissions, not networks joined.

### 28. MITx course
**No** (no evidence found)

### 29. Heard about Solve through a mailing list
**No**  
Program was tracked in Notion from STARTUP_FUNDING-15 research (MIT Solve note source field).

---

## Page 4

### 30. What makes your solution innovative? (≤300 words)
Most AI "memory" products optimize for convenience: retrieve something relevant and let the model speak. Titan inverts the default. Innovation is architectural separation, not a flashy demo. Retrieval is not evidence. Admission is not verification. Model output is not Canon. TRACE membership is not proof that a model semantically used a fact or that the fact supported the answer. The system keeps an epistemic state machine, controlled promotion into trusted state, provenance/audit surfaces, and a replaceable LLM layer so language generation never silently becomes authority to mutate memory. That matters for economic opportunity because the workers and small organizations being pushed into AI tools are exactly the people least able to reverse-engineer a black box. A local-first, inspectable exocortex lets non-engineers direct agents while still answering "what did the agent write, and what changed later?" Related Crystal work explores evidence admission even more strictly; this application is about Titan's orchestration/memory prototype, not a claim that every Crystal evaluation feature is already Titan runtime.  
*(163 words)*

### 31. Theory of change / why you expect impact (≤300 words)
Theory of change, stated without fake traction: If AI-assisted work requires inspectable memory, then building a research-grade local-first audit surface is a necessary step before agencies, banks, and small teams can safely assign economic tasks to agents. Activities now: keep Titan honest on GitHub (tests, status docs, explicit non-claims), seek partners for bounded pilots, and harden the audit kit (receipts/signing) through pending grant scopes where applicable. Outputs: runnable prototype, public documentation, and eventually signed/auditable memory transitions if funded hardening lands. Outcomes: pilot users can review agent memory writes instead of trusting opaque assistants; non-engineer operators gain a practical skill path—directing agents with accountability. Impact: broader pathways into quality AI-era work for people excluded from formal ML engineering roles. Evidence today is only technical (code, tests, docs). There are 0 beneficiaries. I expect impact only after partners, evaluation, and external review close the gap between prototype and trusted use.  
*(148 words)*

### 32. Tech stack and how you know it works (≤300 words)
Titan is primarily Python software. Documented stack and proof points from the public repo: core memory/ESM (`core/memory.py`); truth/write/promotion gates; hybrid retriever with lexical/BM25-style baseline and optional dense/graph signals; provenance and audit chain modules; FastAPI server (`server.py`) with authenticated API and MCP/tool gateway; browser console under `static/console/`; SQLite-backed local persistence; Docker Compose hardened profile for local deployment experiments; replaceable LLM/provider layer. How I know it works as a prototype: the README and Reviewer README publish a verification baseline—install editable extras, import `core` version, `ruff check core/`, `mypy core/`, and focused `pytest` suites (smoke, invariants, truth gate, write gate). Project Status and Reviewer docs state what is implemented vs gated vs research and refuse production authorization. I do not claim an independent third-party security audit or production-scale multi-user operation.  
*(127 words)*

### 33. Technologies used (select on form)
Select only what the code supports:
- **Software and Mobile Applications** — Yes (local software, FastAPI, console UI)
- **Generative AI** — Yes (replaceable LLM/provider layer)
- **Machine Learning** — Optional/Yes with restraint (hybrid retrieval supports optional dense embeddings; not every install runs dense signals)
- **Blockchain** — **Do NOT select** (hash-linked unsigned audit log is not a blockchain)

### 34. Business model (≤300 words)
There is no registered company and no documented revenue. Titan is open source under the MIT License (Copyright 2026 Velantrian / VELANTRIM contributors). The related Crystal line is AGPL-3.0. Current "business model" is public-interest open infrastructure plus possible later services around audit hardening, deployment help, and evaluation—not a claim of paying customers. Near-term financing is grant-seeking by an individual applicant. I am not presenting requested grant amounts as income.  
*(69 words)*

### 35. Primarily serve
**Organizations (B2B)** — agencies, banks, and small teams evaluating or using AI agents.  
Not government unless separately documented (none found).

### 36. Plan for financial sustainability + evidence (≤300 words)
Financial sustainability plan is staged and honest. Stage 0 (now): keep the prototype public and testable while living costs and development are self-directed; no revenue. Stage 1: complete pending grant reviews and, if awarded, use them only for scoped hardening (for example audit-kit receipts/signing work), not for inventing users. Documented submissions and outcomes: NLnet Commons Fund application 2026-06-2ea — NOT SELECTED / NOT AWARDED (decision 2026-10-09); Prototype Fund Jahrgang 03 Crystal Evidence Core #ptfj03i899 — submitted 7 Oct 2026, awaiting decision; EA Funds Transformative AI Fund Titan Audit Kit — submitted 31 Oct 2026, requested USD 50,175, awaiting; BlueDot Rapid Grants Titan Audit Kit — submitted 31 Oct 2026, requested USD 15,600, awaiting; Emergent Ventures — submitted 2 July 2026, under review; Hub71 — rejected. Stage 2 (needs partners): bounded pilots with organizations that need agent-memory audit trails, then decide whether sustainability is grants + services, open-core support, or another model. Solve support would help test that path without pretending a market already exists.  
*(164 words)*

---

## Required checkbox acknowledgements (parent ticks on site)

1. **Terms of Service / media / privacy** — acknowledge Solve terms, media release, and privacy policy as shown on the form.  
2. **AI-enabled review** — acknowledge that Solve may use AI-enabled tools in review as disclosed on the form.  
3. **No fabricated/exaggerated information; GenAI-assisted text checked against current status** — this draft was prepared with AI assistance; every factual claim was checked against GitHub main status docs, LICENSE files, Notion grant records, and the MIT Solve challenge page. Do not submit if any field still says `[PHONE — ask user]` or otherwise unresolved.

---

## Claims deliberately NOT made
- No users, revenue, partners, or pilots  
- No Cambodia / SEA operations (media pitch only)  
- No NLnet funding / award  
- No production-ready, GDPR-certified, zero-hallucination, AGI, consciousness, or “only project in the world” claims  
- No Blockchain checkbox  
- Crystal features not claimed as Titan runtime unless Titan main supports them  
- Research Mode / Notion research concepts not claimed as current runtime  
- Hub71 not claimed as joined network  
- Requested grant USD/EUR amounts not claimed as awarded money  
- No external security audit claimed  

## Prototype evidence summary
Titan LICENSE = **MIT**. Functioning prototype evidence: public repo created 2026-07-09; README quick start (venv + uvicorn / Docker Compose); `/health`; core memory/ESM + truth/write gates + provenance/audit + retrieval + authenticated MCP wiring; verification commands in REVIEWER_README (`pip install -e ".[server,dev]"`, `ruff`, `mypy`, focused `pytest`). Explicitly research-grade, 0 users, not production-authorized.
