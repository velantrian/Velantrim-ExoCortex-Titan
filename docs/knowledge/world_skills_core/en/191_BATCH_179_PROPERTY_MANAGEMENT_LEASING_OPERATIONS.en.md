# BATCH_179 — Property Management & Leasing Operations Detail
# world_skills_core · source: world_skills_core:batch_179:property_management_leasing_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| propops.listing.unit_listing | Unit listing | invariant | Listing records unit features, rent, availability, photos, restrictions, amenities and showing instructions. | объект готов к рынку |
| propops.listing.rent_comparison | Rent comparison | variant | Comparison reviews similar units, vacancy, seasonality and concessions before pricing. | price with context |
| propops.listing.photo_standard | Listing photo standard | invariant | Photo standard keeps images accurate, current, well-lit and not misleading. | trust before showing |
| propops.listing.vacancy_status | Vacancy status | invariant | Status tracks occupied, notice-given, vacant, make-ready, listed, application pending or leased. | pipeline visibility |
| propops.listing.showing_schedule | Showing schedule | variant | Schedule coordinates prospect access, occupied-unit notice, staff availability and key control. | tours without chaos |
| propops.listing.concession_record | Leasing concession record | variant | Concession record documents discount, free rent, waived fee, condition and approval. | discount with audit trail |
| propops.application.application_intake | Rental application intake | invariant | Intake collects applicant identity, household, income, rental history, consent and required documents. | start screening |
| propops.application.application_fee | Application fee record | variant | Fee record tracks charge, waiver, refund rule and payment status for application processing. | money tied to application |
| propops.application.document_checklist | Applicant document checklist | invariant | Checklist tracks missing or received ID, income proof, references and required forms. | complete file |
| propops.application.screening_criteria | Screening criteria | invariant | Criteria define objective factors for approval, denial or conditional approval. | consistent decisions |
| propops.application.adverse_action | Adverse action notice | invariant | Notice explains denial or conditional terms when screening result requires disclosure. | fairness and compliance |
| propops.application.waitlist | Rental waitlist | variant | Waitlist orders applicants by priority, date, unit type and eligibility. | manage scarce units |
| propops.lease.lease_draft | Lease draft | invariant | Draft prepares rent, term, parties, unit, deposits, rules, utilities and addenda for review. | contract package |
| propops.lease.addendum_tracking | Lease addendum tracking | invariant | Tracking ensures pet, parking, storage, lead, rules or local addenda are included when needed. | avoid missing terms |
| propops.lease.signature_status | Lease signature status | invariant | Status shows who has signed, pending, declined or needs correction. | execution control |
| propops.lease.movein_funds | Move-in funds | invariant | Funds include rent, deposit, fees or credits required before possession under policy. | keys after money |
| propops.lease.key_release | Key release control | invariant | Key release confirms lease, funds, ID, insurance and move-in condition before handover. | possession gate |
| propops.lease.lease_renewal | Lease renewal workflow | variant | Renewal workflow sets offer, rent change, deadline, negotiation, signature and nonrenewal path. | keep tenancy current |
| propops.movein.condition_report | Move-in condition report | invariant | Report records unit state, photos, meters, keys, appliances and existing damage at possession. | deposit baseline |
| propops.movein.utility_transfer | Utility transfer tracking | variant | Tracking confirms required utilities are placed in tenant or owner name by move-in date. | avoid service gaps |
| propops.movein.welcome_packet | Resident welcome packet | variant | Packet explains rules, contacts, portals, trash, maintenance requests, emergency and payment methods. | reduce first-week confusion |
| propops.movein.parking_assignment | Parking assignment | variant | Assignment links space, permit, vehicle, fee and restrictions to tenant record. | manage parking asset |
| propops.movein.access_device | Access device inventory | invariant | Inventory tracks keys, fobs, remotes, mailbox keys and returns. | control physical access |
| propops.movein.pet_registration | Pet registration | variant | Registration records pet approval, fees, restrictions, vaccination proof if required and rules. | animal policy control |
| propops.maintenance.work_order | Property work order | invariant | Work order records issue, location, tenant, priority, vendor, status and completion. | maintenance memory |
| propops.maintenance.emergency_repair | Emergency repair workflow | invariant | Workflow triages urgent leaks, no heat, lockouts, electrical hazards or safety issues for rapid response. | protect habitability |
| propops.maintenance.vendor_dispatch | Vendor dispatch | variant | Dispatch sends approved vendor with scope, access, limit, photos and tenant contact rules. | contractor control |
| propops.maintenance.preventive_schedule | Preventive maintenance schedule | invariant | Schedule covers HVAC, gutters, alarms, pest, roofs, plumbing and inspections. | prevent expensive failure |
| propops.maintenance.tenant_chargeback | Tenant chargeback | variant | Chargeback records repair cost attributed to tenant-caused damage with evidence and approval. | fair cost recovery |
| propops.maintenance.completion_verification | Maintenance completion verification | invariant | Verification confirms work done, tenant satisfaction, photos, invoice and closeout code. | close correctly |
| propops.inspection.periodic_inspection | Periodic property inspection | invariant | Inspection checks condition, safety, lease compliance, deferred maintenance and unauthorized changes. | know asset state |
| propops.inspection.moveout_inspection | Move-out inspection | invariant | Inspection compares unit condition with baseline and documents cleaning, damage, keys and meter readings. | deposit decision evidence |
| propops.inspection.notice_to_enter | Notice to enter | invariant | Notice informs tenant of planned entry according to rules, purpose and time window. | access with respect |
| propops.inspection.violation_notice | Lease violation notice | invariant | Notice records observed issue, lease basis, correction required, deadline and consequences. | formal compliance path |
| propops.financial.rent_roll | Rent roll | invariant | Rent roll lists units, tenants, rents, deposits, balances, lease dates and status. | property financial snapshot |
| propops.financial.ledger | Tenant ledger | invariant | Ledger records charges, payments, credits, fees, adjustments and balance. | account truth |
| propops.financial.deposit_accounting | Security deposit accounting | invariant | Accounting tracks deposit receipt, allowable deductions, interest if applicable and return deadline. | money held in trust |
| propops.financial.delinquency_workflow | Rent delinquency workflow | invariant | Workflow tracks late notices, promises, payment plans, fees, legal handoff and communication. | structured arrears handling |
| propops.financial.owner_statement | Owner statement | variant | Statement reports income, expenses, reserves, fees, distributions and property notes to owner. | investor visibility |
| propops.closeout.nonrenewal | Nonrenewal workflow | variant | Nonrenewal records decision, notice, dates, tenant communication and make-ready planning. | end tenancy intentionally |
| propops.closeout.eviction_handoff | Eviction handoff | variant | Handoff sends case file, ledger, notices, lease and communication history to authorized legal process. | organized escalation |
| propops.closeout.unit_turn | Unit turn | invariant | Turn coordinates cleaning, repairs, paint, inspection, pricing and listing after vacancy. | vacant to rentable |
| propops.closeout.records_retention | Property records retention | invariant | Retention covers leases, ledgers, notices, inspections, applications, invoices and communications. | records after tenancy |
| propops.closeout.kpi_vacancy_loss | Vacancy loss KPI | invariant | Vacancy loss measures rent not earned while unit is unrented or not ready. | empty unit cost |
| propops.financial.tenant_ledger | Книга арендаторов | invariant | В книге регистрируются расходы, платежи, кредиты, сборы, корректировки и баланс. | правда аккаунта |
