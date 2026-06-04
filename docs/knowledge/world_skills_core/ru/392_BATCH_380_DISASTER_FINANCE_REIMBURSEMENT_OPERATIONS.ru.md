# BATCH 380: Disaster Finance Reimbursement Operations

**KnowledgeUnits:** 44  
**Namespace:** `disasterfinanceops.*`  
**Scope:** project worksheets, eligibility, documentation, cost tracking, drawdowns, closeout and audit.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| disasterfinanceops.intake.project_id | project ID | RECORD | Project ID links incident, applicant, damage, scope, costs and funding source. | Tracks reimbursement package. |
| disasterfinanceops.intake.damage_link | damage link | RECORD | Project links to damage assessment, photos, maps and work orders. | Connects cost to event. |
| disasterfinanceops.intake.applicant | applicant record | RECORD | Applicant record stores legal entity, contacts, identifiers and authority. | Establishes who claims funds. |
| disasterfinanceops.intake.program | program type | RECORD | Program distinguishes public assistance, hazard mitigation, insurance, grant or donor fund. | Different rules apply. |
| disasterfinanceops.eligibility.incident_period | incident period | CONSTRAINT | Eligible work must connect to declared incident and approved dates. | Protects claim validity. |
| disasterfinanceops.eligibility.work_category | work category | CONSTRAINT | Work category separates emergency protective measures, debris, repair or mitigation. | Routes documentation. |
| disasterfinanceops.eligibility.ownership | ownership check | QUALITY_CHECK | Ownership or legal responsibility is confirmed before claiming repair costs. | Prevents ineligible claims. |
| disasterfinanceops.eligibility.duplication | duplication of benefits | QUALITY_CHECK | Insurance, other grants and donations are checked against claimed costs. | Avoids duplicate reimbursement. |
| disasterfinanceops.scope.scope_statement | scope statement | RECORD | Scope describes work performed or planned, location and standard. | Defines reimbursable work. |
| disasterfinanceops.scope.version | scope version | RECORD | Scope versions track changes, approvals and cost impact. | Controls amendments. |
| disasterfinanceops.scope.improved_project | improved project | CONSTRAINT | Improved or alternate work requires approval and cost limits. | Keeps funding compliant. |
| disasterfinanceops.scope.mitigation | mitigation add-on | METHOD | Mitigation measures are documented separately with benefit and eligibility. | Supports resilient repair. |
| disasterfinanceops.cost.labor | labor cost | RECORD | Labor records employee, hours, rate, fringe, work performed and location. | Supports payroll claim. |
| disasterfinanceops.cost.equipment | equipment cost | RECORD | Equipment records asset, hours, rate, operator and task. | Supports force account cost. |
| disasterfinanceops.cost.materials | material cost | RECORD | Materials record item, quantity, price, vendor and use. | Links purchases to project. |
| disasterfinanceops.cost.contract | contract cost | RECORD | Contract costs include procurement file, invoice, proof and scope. | Supports external work. |
| disasterfinanceops.documentation.photo | photo evidence | RECORD | Photos show damage, work progress and completion. | Proves necessity and result. |
| disasterfinanceops.documentation.invoice | invoice package | RECORD | Invoice package includes PO/contract, receipt, approval and payment proof. | Supports reimbursement. |
| disasterfinanceops.documentation.timesheet | timesheet support | QUALITY_CHECK | Timesheets match incident codes, work dates and supervisor approvals. | Reduces labor audit risk. |
| disasterfinanceops.documentation.map | map documentation | RECORD | Maps identify project sites, routes, facilities or debris zones. | Clarifies geography. |
| disasterfinanceops.tracking.cost_code | cost code | RECORD | Cost codes separate incident, project, funding source and category. | Enables clean accounting. |
| disasterfinanceops.tracking.budget | project budget | MEASUREMENT | Budget tracks estimate, obligations, expenditures and remaining balance. | Controls spend. |
| disasterfinanceops.tracking.match | local match | RECORD | Match records cost share, source and eligible amount. | Supports funding plan. |
| disasterfinanceops.tracking.unresolved | unresolved item | RECORD | Unresolved items include missing docs, eligibility questions or disputed costs. | Keeps blockers visible. |
| disasterfinanceops.drawdown.request | drawdown request | METHOD | Request packages eligible costs, certification and supporting records. | Converts costs to cash. |
| disasterfinanceops.drawdown.certification | certification | SAFETY_RULE | Authorized official certifies costs are true, eligible and not duplicated. | Protects public funds. |
| disasterfinanceops.drawdown.cash_timing | cash timing | MODEL | Drawdown timing balances reimbursement, cash flow and documentation readiness. | Improves liquidity. |
| disasterfinanceops.drawdown.receipt | reimbursement receipt | RECORD | Receipt records amount, date, fund and project allocation. | Closes finance loop. |
| disasterfinanceops.audit.file_complete | file completeness | QUALITY_CHECK | File contains eligibility, scope, costs, procurement, proof and approvals. | Prepares audit. |
| disasterfinanceops.audit.procurement | procurement audit | QUALITY_CHECK | Procurement is checked for competition, emergency justification and vendor responsibility. | Protects grant eligibility. |
| disasterfinanceops.audit.site_visit | site visit | METHOD | Site visit verifies work location, completion and documentation. | Supports claim confidence. |
| disasterfinanceops.audit.finding | audit finding | RECORD | Finding records issue, questioned cost, response and corrective action. | Manages audit risk. |
| disasterfinanceops.insurance.claim | insurance claim | RECORD | Insurance claim records coverage, deductible, proceeds and denial. | Supports duplication analysis. |
| disasterfinanceops.insurance.proceeds | proceeds offset | METHOD | Insurance proceeds offset eligible reimbursement where required. | Avoids overpayment. |
| disasterfinanceops.insurance.appeal | insurance appeal | METHOD | Denials or underpayments may be appealed before final funding position. | Maximizes proper recovery. |
| disasterfinanceops.reporting.status_report | status report | RECORD | Report summarizes projects, costs, reimbursements, issues and deadlines. | Informs leadership. |
| disasterfinanceops.reporting.deadline | deadline tracking | MEASUREMENT | Deadlines track application, documentation, appeals, closeout and retention. | Prevents lost funding. |
| disasterfinanceops.reporting.dashboard | finance dashboard | MEASUREMENT | Dashboard shows obligation, expenditure, reimbursement and match by project. | Guides decisions. |
| disasterfinanceops.records.retention | retention rule | CONSTRAINT | Records are retained for grant, audit and legal periods after closeout. | Preserves evidence. |
| disasterfinanceops.security.access | access control | SAFETY_RULE | Finance records with payroll, vendor and survivor data use restricted access. | Protects sensitive data. |
| disasterfinanceops.closeout.final_report | final report | METHOD | Closeout submits final costs, scope, insurance, payments and certifications. | Ends grant process. |
| disasterfinanceops.closeout.deobligation | deobligation | METHOD | Unused or ineligible funds are returned or reduced. | Keeps accounts accurate. |
| disasterfinanceops.closeout.lessons | lessons learned | METHOD | Review captures documentation gaps, cost coding, procurement and cash-flow issues. | Improves future recovery. |
| disasterfinanceops.governance.finance_owner | finance owner | RECORD | Finance owner coordinates departments, grants, procurement and auditors. | Keeps reimbursement disciplined. |
