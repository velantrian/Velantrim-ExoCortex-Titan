# BATCH_250 — Probation Office Operations Detail
# world_skills_core · source: world_skills_core:batch_250:probation_office_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| probationops.intake.case_intake | Probation case intake | invariant | Intake records person, court order, offense, conditions, sentence and supervision start. | open supervision |
| probationops.intake.order_review | Probation order review | invariant | Review identifies reporting, treatment, restitution, testing, travel and no-contact conditions. | know duties |
| probationops.intake.risk_assessment | Probation risk assessment | variant | Assessment estimates supervision level, criminogenic needs, protective factors and responsivity. | tailor supervision |
| probationops.intake.orientation | Probation orientation | invariant | Orientation explains conditions, appointments, violations, rights, fees and contact rules. | set expectations |
| probationops.intake.contact_info | Probation contact information | invariant | Information records residence, phone, email, employer, emergency contact and approved contacts. | maintain reach |
| probationops.plan.supervision_plan | Probation supervision plan | invariant | Plan links risks, needs, goals, conditions, appointments, referrals and monitoring level. | guide casework |
| probationops.plan.goal_step | Probation goal step | variant | Step breaks employment, housing, treatment, education or restitution goal into actions. | support compliance |
| probationops.plan.case_note | Probation case note | invariant | Note records contact, progress, concerns, instructions, referrals and officer observations. | supervision record |
| probationops.plan.review_cycle | Probation plan review cycle | invariant | Cycle updates plan after assessment, violation, progress, court order or life change. | adapt supervision |
| probationops.appointment.office_visit | Probation office visit | invariant | Visit records attendance, identity, condition review, updates, documents and next date. | routine supervision |
| probationops.appointment.missed_visit | Missed probation visit | invariant | Record captures absence, reason, attempted contact, officer response and escalation. | monitor compliance |
| probationops.appointment.home_visit | Probation home visit | variant | Visit documents residence verification, household concerns, safety, contacts and observations. | field supervision |
| probationops.appointment.virtual_checkin | Probation virtual check-in | variant | Check-in verifies identity, location, privacy, updates and documentation. | remote contact |
| probationops.compliance.condition_check | Probation condition check | invariant | Check reviews court conditions against reported behavior, records and officer observations. | assess compliance |
| probationops.compliance.employment_verify | Probation employment verification | variant | Verification confirms employer, schedule, pay, attendance and job change. | stability check |
| probationops.compliance.residence_verify | Probation residence verification | invariant | Verification confirms address, move request, household limits and contact. | locate person |
| probationops.compliance.travel_request | Probation travel request | variant | Request records destination, purpose, dates, contacts, restrictions and approval. | manage movement |
| probationops.compliance.no_contact_monitor | No-contact condition monitor | invariant | Monitor tracks protected parties, addresses, calls, messages, social media and alleged contact. | protect victims |
| probationops.testing.drug_test_order | Probation drug test order | variant | Order records required test, schedule, collection site, result route and missed-test rules. | monitor substance use |
| probationops.testing.test_result | Probation test result | invariant | Result records negative, positive, diluted, missed, refused or pending status. | compliance evidence |
| probationops.testing.confirmation_review | Probation test confirmation review | variant | Review handles disputed, lab-confirmed, prescription or chain-of-custody issues. | fair response |
| probationops.referral.treatment_referral | Probation treatment referral | invariant | Referral links condition, provider, appointment, releases, attendance and progress reports. | support change |
| probationops.referral.education_program | Probation education program | variant | Program referral covers classes, certificates, attendance, completion and fees. | meet condition |
| probationops.referral.employment_service | Probation employment service referral | variant | Referral connects person to job search, training, documents, transportation or placement. | improve stability |
| probationops.referral.housing_support | Probation housing support referral | variant | Referral addresses shelter, lease, transitional housing, restrictions and safety. | reduce risk |
| probationops.violation.violation_report | Probation violation report | invariant | Report documents alleged violation, evidence, history, response, recommendation and court notice. | escalate formally |
| probationops.violation.technical_violation | Technical violation response | variant | Response handles missed meeting, fee, travel, testing, curfew or paperwork issue. | proportional action |
| probationops.violation.new_arrest | Probation new arrest alert | invariant | Alert records arrest, charges, custody, court date, conditions and officer response. | update risk |
| probationops.violation.graduated_sanction | Graduated sanction | variant | Sanction records warning, increased reporting, program, service hours or court referral. | respond proportionally |
| probationops.violation.incentive_record | Probation incentive record | variant | Record notes reduced reporting, praise, certificate, fee waiver or early review. | reinforce progress |
| probationops.court.status_report | Probation court status report | invariant | Report summarizes compliance, violations, payments, treatment, risk and recommendation. | inform judge |
| probationops.court.hearing_preparation | Probation hearing preparation | invariant | Preparation gathers reports, notices, evidence, witnesses, recommendations and client status. | ready court |
| probationops.court.order_update | Probation court order update | invariant | Update changes conditions, term, fees, supervision level or termination date. | keep current |
| probationops.victim.victim_notification | Probation victim notification | variant | Notification follows allowed rules for hearings, violations, release, no-contact or restitution. | victim rights |
| probationops.victim.restitution_tracking | Probation restitution tracking | invariant | Tracking records amount, payments, arrears, distribution, court changes and completion. | financial accountability |
| probationops.fees.fee_schedule | Probation fee schedule | variant | Schedule records supervision, testing, program, restitution or court-ordered payment obligations. | payment clarity |
| probationops.fees.payment_record | Probation payment record | invariant | Record links payment, obligation, date, receipt, allocation and balance. | financial trail |
| probationops.quality.case_audit | Probation case audit | invariant | Audit checks order, contacts, notes, assessments, violations, referrals and court reports. | supervision quality |
| probationops.quality.safety_plan | Probation officer safety plan | invariant | Plan covers field visit risk, partner officer, check-in, location and emergency path. | protect staff |
| probationops.reporting.caseload_report | Probation caseload report | invariant | Report summarizes active cases, risk levels, contacts due, violations and closures. | manage workload |
| probationops.reporting.outcome_report | Probation outcome report | variant | Report tracks completions, revocations, new arrests, treatment completion and restitution. | program insight |
| probationops.metrics.probation_kpi | Probation office KPI | variant | KPI tracks contact timeliness, violations, completions, revocations, referrals and caseload balance. | manage office |
| probationops.close.case_closure | Probation case closure | invariant | Closure records term completion, early discharge, revocation, transfer or death. | end supervision |
| probationops.continuity.office_closure | Probation office closure response | variant | Response shifts reporting, testing, court notices, field safety and emergency contact. | maintain supervision |
