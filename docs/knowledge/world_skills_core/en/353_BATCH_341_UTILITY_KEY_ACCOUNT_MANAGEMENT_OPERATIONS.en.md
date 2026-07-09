# BATCH 341: Utility Key Account Management Operations

**KnowledgeUnits:** 44  
**Namespace:** `keyacctops.*`  
**Scope:** account plans, contacts, service reviews, outage coordination, billing issues and records.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| keyacctops.portfolio.key_account_flag | key account flag | RECORD | Account is flagged as key due to load, criticality, revenue, public role or complexity. | Focuses relationship management on high-impact customers. |
| keyacctops.portfolio.segment | segment | RECORD | Segments include hospitals, schools, industry, large irrigation, developers and agencies. | Different segments need different service handling. |
| keyacctops.portfolio.owner | account owner | RECORD | Named utility owner coordinates contacts, issues and follow-up. | Prevents fragmented responses. |
| keyacctops.plan.account_plan | account plan | RECORD | Plan documents contacts, services, risks, meters, sites, communication preferences and goals. | Creates shared context before problems occur. |
| keyacctops.plan.risk_profile | risk profile | MODEL | Risk includes outage sensitivity, billing complexity, water quality needs and public visibility. | Prioritizes proactive work. |
| keyacctops.plan.review_cycle | review cycle | DECISION_RULE | Key accounts receive periodic review based on criticality and issue volume. | Keeps records current. |
| keyacctops.contacts.primary_contact | primary contact | RECORD | Primary contact and backups are recorded with role, phone, email and authority. | Speeds incident communication. |
| keyacctops.contacts.escalation_tree | escalation tree | RECORD | Escalation tree lists utility and customer contacts for urgent issues. | Reduces confusion during outages. |
| keyacctops.contacts.authority_scope | authority scope | CONSTRAINT | Contact authority defines who can approve service changes, billing actions or data release. | Prevents unauthorized decisions. |
| keyacctops.service.service_profile | service profile | RECORD | Profile lists meters, accounts, pressure zone, backflow devices and special infrastructure. | Helps staff understand customer footprint. |
| keyacctops.service.load_pattern | load pattern | MODEL | Demand pattern tracks seasonal, peak, process or emergency use. | Supports capacity and outage planning. |
| keyacctops.service.critical_process | critical process | RECORD | Critical processes such as dialysis, cooling, manufacturing or food safety are documented. | Informs outage and maintenance notices. |
| keyacctops.review.service_review | service review meeting | METHOD | Periodic meeting covers usage, bills, projects, outages, complaints and upcoming work. | Builds trust and prevents surprises. |
| keyacctops.review.action_register | action register | RECORD | Meeting actions have owner, due date, status and closeout evidence. | Keeps relationship work actionable. |
| keyacctops.review.customer_feedback | customer feedback | RECORD | Feedback is captured on responsiveness, reliability and communication quality. | Reveals improvement areas. |
| keyacctops.outage.outage_notice | outage notice | METHOD | Key accounts get targeted planned and emergency outage communications. | Allows customer contingency planning. |
| keyacctops.outage.sensitive_coordination | sensitive coordination | METHOD | Sensitive facilities may coordinate backup water, timing or phased work. | Reduces operational harm. |
| keyacctops.outage.post_outage_review | post-outage review | METHOD | Major outage follow-up reviews impact, communication and mitigation. | Improves future coordination. |
| keyacctops.billing.complex_bill | complex bill review | METHOD | Large or multi-meter bills are reviewed for reads, rates, demand and adjustments. | Prevents high-value billing disputes. |
| keyacctops.billing.billing_contact | billing contact | RECORD | Billing contact differs from operational contact when needed. | Routes issues correctly. |
| keyacctops.billing.exception_tracker | exception tracker | RECORD | Billing disputes, credits, estimates and meter issues are tracked. | Prevents recurring surprises. |
| keyacctops.projects.project_pipeline | project pipeline | RECORD | Customer expansion, construction or process changes are recorded. | Lets utility plan capacity and meters. |
| keyacctops.projects.utility_work | utility work coordination | METHOD | Planned utility work is coordinated with customer operations and shutdown windows. | Reduces business disruption. |
| keyacctops.projects.developer_link | developer link | METHOD | Developer or facility projects connect to engineering, permits and account setup. | Bridges customer service and infrastructure. |
| keyacctops.data.data_request | usage data request | METHOD | Usage or interval data requests verify authority, scope and delivery format. | Gives customer useful data safely. |
| keyacctops.data.benchmarking | benchmarking support | METHOD | Utility may support sustainability or compliance reporting with usage data. | Helps large customers manage resources. |
| keyacctops.data.privacy | data privacy | CONSTRAINT | Multi-tenant or third-party data release follows authorization rules. | Protects customer information. |
| keyacctops.communication.preference | communication preference | RECORD | Customer preference records channels, language, timing and escalation route. | Makes outreach effective. |
| keyacctops.communication.briefing_note | briefing note | RECORD | Briefing note summarizes key facts for executives or incident teams. | Prevents ad hoc leadership messaging. |
| keyacctops.communication.single_voice | single voice | METHOD | Utility coordinates messages through account owner for complex issues. | Reduces conflicting promises. |
| keyacctops.crm.timeline | CRM timeline | RECORD | Contacts, meetings, issues, outages and commitments are stored in timeline. | Staff see relationship history. |
| keyacctops.crm.document_link | document link | RECORD | Agreements, maps, meter lists and correspondence are linked. | Keeps evidence findable. |
| keyacctops.qa.contact_audit | contact audit | QUALITY_CHECK | Contact lists are verified at least periodically. | Avoids stale emergency numbers. |
| keyacctops.qa.commitment_audit | commitment audit | QUALITY_CHECK | Open promises are reviewed for overdue status. | Protects credibility. |
| keyacctops.qa.priority_review | priority review | QUALITY_CHECK | Key account list is reviewed to add/remove accounts by criteria. | Keeps portfolio accurate. |
| keyacctops.reporting.issue_volume | issue volume | MEASUREMENT | Reports track key-account issues by type, age, owner and outcome. | Shows relationship workload. |
| keyacctops.reporting.revenue_risk | revenue risk | MODEL | Billing disputes and large meters can create material revenue risk. | Helps finance prioritize controls. |
| keyacctops.reporting.satisfaction | satisfaction trend | MEASUREMENT | Satisfaction or sentiment is tracked from meetings, complaints and surveys. | Measures relationship health. |
| keyacctops.governance.conflict | conflict management | METHOD | Conflicting requests between customer and policy are escalated with documented decision. | Balances service and fairness. |
| keyacctops.governance.equity | equity boundary | CONSTRAINT | Key accounts can receive coordination but not improper preferential rule-breaking. | Protects public accountability. |
| keyacctops.training.account_brief | account brief training | METHOD | Staff serving key accounts learn account profile, boundaries and escalation path. | Improves continuity. |
| keyacctops.closeout.issue_close | issue closeout | QUALITY_CHECK | Issue closes after customer response, action completion or documented no-response. | Avoids open-loop relationship work. |
| keyacctops.closeout.customer_note | customer closeout note | RECORD | Closure note summarizes action, owner, date and remaining customer responsibilities. | Gives the account a clear final record. |
| keyacctops.review.lessons | lessons learned | METHOD | Major key-account incidents feed process, communication and planning improvements. | Converts high-impact cases into better operations. |
