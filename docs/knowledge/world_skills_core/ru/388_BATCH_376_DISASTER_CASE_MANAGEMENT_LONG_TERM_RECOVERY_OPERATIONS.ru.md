# BATCH 376: Disaster Case Management Long-Term Recovery Operations

**KnowledgeUnits:** 44  
**Namespace:** `recoverycaseops.*`  
**Scope:** unmet needs, recovery plans, referrals, funding, follow-up and closure.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| recoverycaseops.intake.case_id | recovery case ID | RECORD | Case ID links household, disaster, needs, case manager and status. | Tracks long-term recovery work. |
| recoverycaseops.intake.referral_source | referral source | RECORD | Source distinguishes assistance center, hotline, nonprofit, government or self-referral. | Shows entry path. |
| recoverycaseops.intake.household | household record | RECORD | Household record stores members, damage, displacement, income and contacts. | Grounds the recovery plan. |
| recoverycaseops.intake.consent | consent to serve | SAFETY_RULE | Consent defines services and information sharing with partners. | Protects survivor autonomy. |
| recoverycaseops.assessment.unmet_need | unmet need | RECORD | Unmet need records gap after insurance, aid, savings and community resources. | Targets real recovery gaps. |
| recoverycaseops.assessment.damage | damage assessment | RECORD | Damage record includes home, vehicle, medical, job, documents or tools. | Supports recovery priorities. |
| recoverycaseops.assessment.vulnerability | vulnerability score | MODEL | Score considers age, disability, income, housing status, caregiving and trauma. | Prioritizes limited resources. |
| recoverycaseops.assessment.barrier | barrier record | RECORD | Barriers include documents, transport, language, landlord, contractor or health issues. | Makes obstacles explicit. |
| recoverycaseops.plan.recovery_goal | recovery goal | RECORD | Goal defines safe housing, income restoration, repairs, documents or stability milestone. | Gives direction. |
| recoverycaseops.plan.action_plan | action plan | METHOD | Plan assigns tasks, owner, deadline, funding and required documents. | Turns needs into work. |
| recoverycaseops.plan.priority | priority sequence | METHOD | Sequence orders urgent safety, housing, health, income and rebuilding tasks. | Prevents scattered effort. |
| recoverycaseops.plan.revision | plan revision | METHOD | Plan changes when funding, household status or damage facts change. | Keeps plan current. |
| recoverycaseops.documents.document_gap | document gap | RECORD | Missing IDs, deeds, leases, insurance or estimates are tracked. | Enables applications. |
| recoverycaseops.documents.replacement | document replacement | METHOD | Caseworker routes replacement of IDs, vital records, titles or permits. | Restores eligibility. |
| recoverycaseops.documents.estimate | repair estimate | RECORD | Estimates document scope, cost, contractor and funding assumptions. | Supports funding requests. |
| recoverycaseops.documents.file_security | file security | SAFETY_RULE | Documents with personal/financial data are secured. | Protects survivors. |
| recoverycaseops.referral.housing | housing referral | METHOD | Housing referral covers repair, rental, rebuild, relocation or legal help. | Stabilizes home situation. |
| recoverycaseops.referral.financial | financial referral | METHOD | Financial referral connects grants, loans, insurance, benefits or charitable aid. | Fills funding gaps. |
| recoverycaseops.referral.health | health referral | METHOD | Health referral covers medical, behavioral, disability or medication needs. | Supports wellbeing. |
| recoverycaseops.referral.legal | legal referral | METHOD | Legal referral covers landlord, contractor, insurance, title or fraud issues. | Handles complex barriers. |
| recoverycaseops.funding.source_matrix | funding matrix | RECORD | Matrix lists possible public, nonprofit, insurance and private sources. | Shows resource stack. |
| recoverycaseops.funding.duplication | duplication check | QUALITY_CHECK | Funding requests check prior aid and insurance. | Prevents duplicate benefits. |
| recoverycaseops.funding.gap_request | gap request | METHOD | Gap request packages need, proof, estimate and remaining shortfall. | Helps committees decide. |
| recoverycaseops.funding.award_tracking | award tracking | RECORD | Awards record amount, source, purpose, conditions and payment status. | Keeps finances visible. |
| recoverycaseops.contractor.contractor_check | contractor check | SAFETY_RULE | Contractor credentials, insurance and complaint history are reviewed where possible. | Reduces exploitation. |
| recoverycaseops.contractor.scope_review | scope review | QUALITY_CHECK | Scope is checked against damage, estimate and funding rules. | Avoids over/under repair. |
| recoverycaseops.contractor.progress | repair progress | RECORD | Progress records milestones, photos, invoices and issues. | Tracks recovery. |
| recoverycaseops.contractor.dispute | contractor dispute | METHOD | Disputes route to legal aid, consumer protection or funder review. | Protects household. |
| recoverycaseops.followup.checkin | case check-in | METHOD | Check-ins track action items, barriers, wellbeing and changed needs. | Maintains momentum. |
| recoverycaseops.followup.missed | missed contact | FAILURE_MODE | Missed contacts trigger retry, alternate contact or partner check. | Avoids silent loss. |
| recoverycaseops.followup.milestone | milestone review | METHOD | Milestones verify documents, funding, repairs, housing or closure readiness. | Shows progress. |
| recoverycaseops.followup.warm_handoff | warm handoff | METHOD | Open tasks are handed to partner agency when outside case manager scope. | Keeps services connected. |
| recoverycaseops.records.case_note | case note | RECORD | Notes record facts, decisions, referrals, consent and next steps. | Supports continuity. |
| recoverycaseops.records.confidentiality | confidentiality rule | SAFETY_RULE | Sensitive household data is shared only by consent and need. | Protects survivors. |
| recoverycaseops.records.retention | retention rule | CONSTRAINT | Records follow grant, disaster, privacy and nonprofit schedules. | Supports audit. |
| recoverycaseops.records.outcome | outcome record | RECORD | Outcome records housed, repaired, relocated, stabilized, withdrawn or unresolved. | Measures recovery. |
| recoverycaseops.metrics.caseload | caseload metric | MEASUREMENT | Caseload tracks active, pending, high-risk and closed households. | Manages workload. |
| recoverycaseops.metrics.unmet_gap | unmet gap metric | MEASUREMENT | Gap metric sums remaining needs by category and geography. | Guides fundraising. |
| recoverycaseops.metrics.time_to_close | time to close | MEASUREMENT | Time to close measures intake-to-resolution duration. | Shows process speed. |
| recoverycaseops.qa.supervision | case supervision | QUALITY_CHECK | Supervisors review high-risk, high-dollar or stalled cases. | Improves quality. |
| recoverycaseops.qa.equity | equity review | QUALITY_CHECK | Service and funding outcomes are reviewed by geography and vulnerability. | Detects inequity. |
| recoverycaseops.closeout.criteria | closure criteria | CONSTRAINT | Closure requires resolved plan, transfer, client withdrawal or unreachable rule. | Prevents premature ending. |
| recoverycaseops.closeout.final_summary | final summary | RECORD | Summary records needs addressed, referrals, funds, outcomes and remaining risks. | Ends case transparently. |
| recoverycaseops.review.lessons | recovery lessons | METHOD | Review captures unmet resources, policy gaps, partner delays and survivor feedback. | Improves future recovery. |
