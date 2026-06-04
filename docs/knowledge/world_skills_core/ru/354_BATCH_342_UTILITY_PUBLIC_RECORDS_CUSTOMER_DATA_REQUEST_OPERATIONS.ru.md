# BATCH 342: Utility Public Records and Customer Data Request Operations

**KnowledgeUnits:** 44  
**Namespace:** `datarequestops.*`  
**Scope:** intake, identity, scope, exemptions, redaction, delivery, fees and audit.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| datarequestops.intake.request_id | request ID | RECORD | Request ID links requester, date, scope, channel, deadline and owner. | Creates controlled tracking. |
| datarequestops.intake.request_type | request type | RECORD | Type distinguishes public records, customer data, legal subpoena, media or internal request. | Different rules apply. |
| datarequestops.intake.scope_text | scope text | RECORD | Request wording is preserved exactly and clarified if needed. | Prevents later disputes about scope. |
| datarequestops.intake.deadline | statutory deadline | CONSTRAINT | Public records deadlines are calculated by jurisdiction and request type. | Keeps compliance visible. |
| datarequestops.identity.customer_auth | customer authorization | SAFETY_RULE | Customer-specific data requires verified identity or valid authorization. | Protects private utility records. |
| datarequestops.identity.third_party | third-party release | CONSTRAINT | Third parties need written consent, legal authority or approved disclosure route. | Prevents improper data sharing. |
| datarequestops.identity.business_request | business request | METHOD | Business data requests verify officer, agent or account authority. | Protects commercial accounts. |
| datarequestops.scope.clarification | clarification | METHOD | Staff clarify broad, ambiguous or impossible requests before search. | Reduces wasted search and disputes. |
| datarequestops.scope.narrowing | narrowing offer | METHOD | Requester may be offered date, topic or record-type narrowing. | Helps deliver useful records faster. |
| datarequestops.scope.search_plan | search plan | RECORD | Plan lists systems, custodians, keywords, dates and likely record types. | Makes search reproducible. |
| datarequestops.search.systems | system search | METHOD | Billing, CRM, GIS, work orders, email, SCADA reports and archives may be searched. | Utility data is spread across systems. |
| datarequestops.search.custodian | custodian search | METHOD | Staff custodians search local files, email and project folders. | Captures records outside central databases. |
| datarequestops.search.search_log | search log | RECORD | Log records where searched, by whom, when and results. | Defends adequacy of search. |
| datarequestops.exemptions.privacy | privacy exemption | CONSTRAINT | Personal identifiers, contact details, medical flags or payment data may be exempt. | Protects customers. |
| datarequestops.exemptions.security | security exemption | CONSTRAINT | Critical infrastructure details, vulnerabilities or security procedures may be withheld. | Protects utility assets. |
| datarequestops.exemptions.privilege | legal privilege | CONSTRAINT | Attorney-client, litigation or deliberative materials may require legal review. | Avoids privileged disclosure. |
| datarequestops.exemptions.trade_secret | trade secret | CONSTRAINT | Vendor or customer confidential business data may be protected. | Balances openness with commercial harm. |
| datarequestops.redaction.redaction_review | redaction review | METHOD | Records are reviewed and redacted before release. | Allows partial disclosure safely. |
| datarequestops.redaction.redaction_log | redaction log | RECORD | Log identifies withheld portions and legal basis. | Supports appeal and audit. |
| datarequestops.redaction.quality_check | redaction QA | QUALITY_CHECK | Redacted files are checked for hidden text, metadata and missed fields. | Prevents accidental release. |
| datarequestops.fees.fee_estimate | fee estimate | METHOD | Staff estimate search, copy, redaction or delivery fees where allowed. | Sets expectations before large work. |
| datarequestops.fees.deposit | deposit | DECISION_RULE | Large requests may require deposit before processing. | Controls unfunded workload. |
| datarequestops.fees.waiver | fee waiver | DECISION_RULE | Fee waiver may apply for public interest, small cost or policy. | Supports access. |
| datarequestops.delivery.format | delivery format | RECORD | Delivery format includes portal, email, paper, export, spreadsheet or inspection. | Matches requester need and security. |
| datarequestops.delivery.secure_link | secure link | METHOD | Sensitive customer data is delivered through secure channel with expiry. | Reduces privacy risk. |
| datarequestops.delivery.partial_release | partial release | METHOD | Rolling releases provide available records while complex review continues. | Improves timeliness. |
| datarequestops.delivery.no_records | no-records response | RECORD | Response documents search performed and no responsive records found. | Closes request defensibly. |
| datarequestops.appeal.appeal_path | appeal path | RECORD | Denial or redaction response includes appeal or review process. | Supports due process. |
| datarequestops.appeal.reconsideration | reconsideration | METHOD | Staff may re-review scope, search or exemptions after challenge. | Corrects mistakes without litigation. |
| datarequestops.legal.subpoena | subpoena handling | METHOD | Subpoenas route to legal with deadline, scope and service validity. | Separates legal compulsion from ordinary request. |
| datarequestops.legal.litigation_hold | litigation hold | CONSTRAINT | Related records may be preserved under legal hold. | Prevents deletion during dispute. |
| datarequestops.customer.usage_data | usage data request | METHOD | Customers can request usage history, reads, bills or interval data under policy. | Supports customer analysis. |
| datarequestops.customer.landlord_tenant | landlord tenant data | CONSTRAINT | Tenant and landlord access to usage/billing data follows privacy law and account authority. | Prevents improper disclosure. |
| datarequestops.customer.data_correction | data correction request | METHOD | Customer may request correction of contact, account or meter data. | Keeps records accurate. |
| datarequestops.records.case_file | case file | RECORD | File stores request, search log, records, redactions, delivery and correspondence. | Single audit trail. |
| datarequestops.records.retention | retention | CONSTRAINT | Request files are retained under records schedule. | Supports later appeals. |
| datarequestops.records.version_control | version control | QUALITY_CHECK | Released file versions are labeled and preserved. | Shows exactly what was disclosed. |
| datarequestops.qa.deadline_monitor | deadline monitor | QUALITY_CHECK | Dashboard flags requests near deadline or waiting on custodian/legal. | Prevents missed deadlines. |
| datarequestops.qa.scope_creep | scope creep check | QUALITY_CHECK | Staff distinguish new requests from clarifications. | Keeps workload controlled. |
| datarequestops.qa.training | staff training | METHOD | Custodians learn search duties, exemptions, privacy and preservation. | Improves compliance. |
| datarequestops.reporting.volume | request volume | MEASUREMENT | Reports track count, type, age, fees, pages and outcomes. | Shows public-record workload. |
| datarequestops.reporting.exemption_trend | exemption trend | MODEL | Frequent exemptions reveal data-design or policy issues. | Helps improve transparency. |
| datarequestops.review.after_issue | after-issue review | METHOD | Controversial or late requests trigger process review. | Prevents repeat failures. |
| datarequestops.governance.owner | program owner | RECORD | Public records owner coordinates legal, IT, departments and customer service. | Avoids fragmented responsibility. |
