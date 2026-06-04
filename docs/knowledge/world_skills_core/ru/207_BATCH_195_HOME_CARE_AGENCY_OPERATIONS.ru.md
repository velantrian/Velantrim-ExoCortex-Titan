# BATCH_195 — Home Care Agency Operations Detail
# world_skills_core · source: world_skills_core:batch_195:home_care_agency_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| homecare.intake.referral_intake | Home care referral intake | invariant | Intake records client, referrer, requested service, urgency, payer, location and contact permissions. | start service safely |
| homecare.intake.eligibility_check | Home care eligibility check | invariant | Check confirms service type, payer rules, authorization, geography and agency capability. | know if agency can serve |
| homecare.intake.initial_assessment | Initial home care assessment | invariant | Assessment documents needs, risks, environment, supports, schedule preference and care goals. | build care plan |
| homecare.intake.service_boundary | Home care service boundary | invariant | Boundary defines tasks caregivers may and may not perform under policy and regulation. | prevent unsafe scope |
| homecare.intake.consent_packet | Home care consent packet | variant | Packet includes service agreement, privacy notices, emergency contacts and client rights. | informed start |
| homecare.plan.care_plan | Home care plan | invariant | Plan lists authorized tasks, frequency, preferences, risks, reporting rules and escalation points. | guide each visit |
| homecare.plan.task_list | Visit task list | invariant | Task list tells caregiver what support to provide and what to document. | clear daily work |
| homecare.plan.risk_flag | Client risk flag | invariant | Flag marks fall risk, wandering, infection control, aggression, allergies or special precautions. | prepare caregiver |
| homecare.plan.medication_assist_boundary | Medication assistance boundary | variant | Boundary separates reminders or assistance from prohibited clinical medication decisions. | safety and compliance |
| homecare.plan.care_plan_review | Care plan review | invariant | Review updates tasks, schedule, risks and goals after change, incident or periodic check. | plan stays current |
| homecare.schedule.shift_assignment | Home care shift assignment | invariant | Assignment links client, caregiver, date, time, tasks, location and required skills. | schedule the visit |
| homecare.schedule.caregiver_match | Caregiver matching | variant | Matching considers skills, language, location, continuity, availability and client preference. | better fit |
| homecare.schedule.open_shift | Open shift | invariant | Open shift lacks assigned caregiver and needs staffing action before service time. | avoid missed care |
| homecare.schedule.callout_handling | Caregiver callout handling | invariant | Handling finds replacement, informs client, updates schedule and records reason. | continuity under disruption |
| homecare.schedule.overtime_control | Home care overtime control | variant | Control tracks hours, authorization, fatigue and cost before approving extra shifts. | manage labor |
| homecare.visit.evv_checkin | Electronic visit verification check-in | variant | EVV check-in records caregiver, client, time, location or approved exception. | prove visit start |
| homecare.visit.evv_checkout | Electronic visit verification check-out | variant | Checkout records end time, completed tasks, notes and exceptions. | close visit evidence |
| homecare.visit.missed_visit | Missed visit | invariant | Missed visit records no-service cause, client notification, supervisor action and payer reporting need. | high-risk exception |
| homecare.visit.late_arrival | Late caregiver arrival | invariant | Late arrival triggers client notice, schedule update and impact review. | protect trust |
| homecare.visit.task_exception | Care task exception | invariant | Exception records task refused, impossible, unsafe, unavailable or not needed. | explain variance |
| homecare.client.emergency_contact | Client emergency contact | invariant | Contact list defines who to call for urgent health, safety or access issues. | escalation path |
| homecare.client.home_access | Home access instructions | invariant | Instructions cover keys, lockbox, door codes, pets, alarms and entry restrictions. | enter safely |
| homecare.client.preference_profile | Client preference profile | variant | Profile records routines, communication style, food preferences, mobility aids and household norms. | person-centered care |
| homecare.client.change_in_condition | Change in condition report | invariant | Report flags new weakness, confusion, fall, pain, wound, behavior change or environment concern. | early warning |
| homecare.client.service_suspension | Service suspension | variant | Suspension pauses care due to hospitalization, safety issue, travel, payer hold or client request. | status control |
| homecare.caregiver.credential_record | Caregiver credential record | invariant | Record tracks background check, training, license if required, skills and expiration dates. | qualified staff |
| homecare.caregiver.orientation | Caregiver orientation | invariant | Orientation covers policies, documentation, boundaries, infection control, lifting and incident reporting. | consistent practice |
| homecare.caregiver.skill_match | Caregiver skill match | variant | Match verifies caregiver can perform assigned tasks such as transfer support or dementia care. | avoid mismatch |
| homecare.caregiver.performance_note | Caregiver performance note | invariant | Note records attendance, documentation quality, client feedback, incidents and coaching. | manage workforce |
| homecare.caregiver.availability_update | Caregiver availability update | invariant | Update records working hours, territories, days off and restrictions. | schedule accuracy |
| homecare.safety.home_hazard | Home hazard note | invariant | Note identifies clutter, pets, smoke, weapons, unsafe neighborhood, poor lighting or fall hazards. | field safety |
| homecare.safety.infection_precaution | Home care infection precaution | variant | Precaution defines PPE, hand hygiene, symptom screening and cleaning expectations. | protect client and worker |
| homecare.safety.lone_worker_check | Lone worker check | variant | Check confirms caregiver safety during high-risk visits or late hours. | worker protection |
| homecare.safety.manual_handling | Manual handling boundary | invariant | Boundary prevents unsafe lifting, transfer or movement without equipment and training. | avoid injury |
| homecare.safety.abuse_neglect_alert | Abuse or neglect alert | invariant | Alert routes suspected abuse, neglect, exploitation or unsafe living condition to mandated process. | safeguarding |
| homecare.incident.incident_report | Home care incident report | invariant | Report documents fall, injury, medication concern, property damage, aggression or emergency response. | formal event record |
| homecare.incident.client_complaint | Home care complaint | invariant | Complaint captures issue, impact, investigation, response and corrective action. | service recovery |
| homecare.incident.hospitalization_notice | Hospitalization notice | variant | Notice updates client status, schedule, payer and care plan after hospital admission. | pause or adapt service |
| homecare.incident.root_cause_review | Home care root cause review | variant | Review analyzes repeated missed visits, incidents, complaints or documentation failures. | improve system |
| homecare.billing.authorization_units | Authorized service units | invariant | Units define payer-approved hours, visits, tasks or period limits. | billable boundary |
| homecare.billing.timesheet_reconciliation | Timesheet reconciliation | invariant | Reconciliation compares schedule, EVV, caregiver notes and payroll hours. | pay and bill correctly |
| homecare.billing.claim_exception | Home care billing exception | invariant | Exception flags missing authorization, late note, EVV mismatch, duplicate visit or payer denial. | fix before claim |
| homecare.metrics.homecare_kpi | Home care agency KPI | variant | KPI tracks missed visits, fill rate, continuity, incidents, complaints, overtime and authorization use. | manage agency health |
| homecare.continuity.emergency_staffing | Emergency staffing plan | invariant | Plan covers backup caregivers, supervisor coverage, weather disruption and priority clients. | keep critical care running |
