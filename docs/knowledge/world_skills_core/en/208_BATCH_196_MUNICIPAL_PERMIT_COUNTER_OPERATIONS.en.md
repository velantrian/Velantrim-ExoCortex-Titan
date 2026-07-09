# BATCH_196 — Municipal Permit Counter Operations Detail
# world_skills_core · source: world_skills_core:batch_196:municipal_permit_counter_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| permitctr.intake.application_intake | Permit application intake | invariant | Intake records applicant, parcel, work type, valuation, documents, fees and contact details. | open permit file |
| permitctr.intake.parcel_lookup | Parcel lookup | invariant | Lookup connects application to property, zoning, owner, address and prior permit history. | site identity |
| permitctr.intake.work_description | Work description | invariant | Description states proposed scope clearly enough for routing and review. | know what is requested |
| permitctr.intake.completeness_check | Permit completeness check | invariant | Check verifies required forms, plans, signatures, contractor data, fees and supporting documents. | avoid review delay |
| permitctr.intake.application_deficiency | Application deficiency | invariant | Deficiency records missing, inconsistent or unacceptable item needing correction. | return actionable list |
| permitctr.fees.fee_schedule | Permit fee schedule | invariant | Schedule defines fees by permit type, valuation, area, inspection or surcharge. | price consistently |
| permitctr.fees.valuation_basis | Project valuation basis | variant | Basis estimates construction value for fee and reporting rules. | fee input |
| permitctr.fees.payment_receipt | Permit payment receipt | invariant | Receipt records amount, method, payer, permit number and date. | money evidence |
| permitctr.fees.refund_request | Permit refund request | variant | Request documents unused permit, overpayment, withdrawal or policy-based refund. | controlled money return |
| permitctr.fees.fee_waiver | Permit fee waiver | variant | Waiver applies authorized exemption, public project rule or hardship program. | exception control |
| permitctr.routing.review_route | Plan review routing | invariant | Routing sends application to building, zoning, fire, health, engineering or planning reviewers. | right desks |
| permitctr.routing.discipline_review | Discipline review | invariant | Review evaluates application against rules for one technical discipline. | specialized check |
| permitctr.routing.parallel_review | Parallel review | variant | Parallel review lets multiple disciplines evaluate at the same time. | shorten turnaround |
| permitctr.routing.resubmittal_cycle | Resubmittal cycle | invariant | Cycle tracks applicant response to comments and renewed review. | manage corrections |
| permitctr.routing.external_agency | External agency referral | variant | Referral sends item to utility, heritage, environmental, state or road authority when required. | outside dependency |
| permitctr.review.comment_letter | Permit comment letter | invariant | Letter lists review deficiencies, code references, requested changes and next steps. | clear correction path |
| permitctr.review.condition_of_approval | Condition of approval | invariant | Condition imposes requirement that must be met before issuance, inspection or final closure. | approval with obligations |
| permitctr.review.code_reference | Code reference | invariant | Reference cites adopted rule, standard, zoning section or ordinance. | trace decision |
| permitctr.review.expired_review | Expired review | variant | Review can expire after inactivity or code cycle change under policy. | time matters |
| permitctr.review.approval_stamp | Permit approval stamp | invariant | Stamp marks approved plans, revision, date and reviewing authority. | field uses approved set |
| permitctr.issuance.permit_number | Permit number | invariant | Number uniquely identifies permit, type, site, status and history. | tracking anchor |
| permitctr.issuance.issue_packet | Permit issue packet | invariant | Packet provides permit card, approved plans, conditions, inspection list and contact instructions. | applicant can proceed |
| permitctr.issuance.contractor_license | Contractor license check | variant | Check confirms license, insurance or registration meets permit requirements. | qualified party |
| permitctr.issuance.owner_builder | Owner-builder declaration | variant | Declaration records owner responsibility when work is not by licensed contractor. | accountability |
| permitctr.issuance.revision_submittal | Permit revision submittal | invariant | Revision updates approved scope, plans, valuation or conditions before or during work. | control changes |
| permitctr.inspection.inspection_request | Inspection request | invariant | Request schedules type, permit, address, contact, access notes and preferred date. | field visit trigger |
| permitctr.inspection.inspection_window | Inspection window | variant | Window communicates expected date or time range for inspector arrival. | coordinate access |
| permitctr.inspection.result_code | Inspection result code | invariant | Code records pass, fail, partial, cancel, no access or correction required. | status clarity |
| permitctr.inspection.correction_notice | Inspection correction notice | invariant | Notice lists failed items, references, photos if used and reinspection requirement. | fix field issues |
| permitctr.inspection.final_inspection | Final inspection | invariant | Final confirms required inspections, conditions and documentation are complete for closure. | legal closeout |
| permitctr.notices.public_notice | Permit public notice | variant | Notice informs neighbors or public about application, hearing, variance or work. | transparency |
| permitctr.notices.stop_work_order | Stop-work order | invariant | Order halts work due to unsafe, unpermitted or noncompliant activity. | enforcement |
| permitctr.notices.expiration_notice | Permit expiration notice | invariant | Notice warns permit will expire without action, inspection or extension. | prevent surprise closure |
| permitctr.notices.appeal_window | Appeal window | variant | Window defines deadline and path for challenging decision. | procedural fairness |
| permitctr.notices.certificate_issue | Certificate issuance | variant | Certificate confirms occupancy, completion, compliance or use permission where required. | official outcome |
| permitctr.records.permit_file | Permit file | invariant | File stores application, plans, comments, fees, inspections, notices and final documents. | full permit history |
| permitctr.records.plan_version | Permit plan version | invariant | Version controls submitted, reviewed, approved and superseded plan sets. | avoid wrong drawings |
| permitctr.records.public_record | Permit public record | invariant | Public record exposes allowed permit information while protecting restricted data. | civic transparency |
| permitctr.records.retention_rule | Permit retention rule | invariant | Rule defines how long applications, plans and inspection records are kept. | archive lifecycle |
| permitctr.records.audit_trail | Permit audit trail | invariant | Trail records status changes, reviewers, approvals, payments, comments and issuance. | explain decisions |
| permitctr.counter.customer_queue | Permit counter queue | invariant | Queue organizes walk-ins, calls, online submissions, appointments and technical questions. | service flow |
| permitctr.counter.preapplication_meeting | Pre-application meeting | variant | Meeting clarifies requirements, constraints, route and likely issues before formal submittal. | reduce rework |
| permitctr.metrics.permit_kpi | Permit counter KPI | variant | KPI tracks intake volume, review time, resubmittals, inspection pass rate and backlog. | manage service |
| permitctr.continuity.system_outage | Permit system outage process | invariant | Process defines manual receipts, temporary numbers, later data entry and applicant communication. | keep counter operating |
