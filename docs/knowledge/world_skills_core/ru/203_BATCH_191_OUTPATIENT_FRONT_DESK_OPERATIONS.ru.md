# BATCH_191 — Outpatient Front Desk Operations Detail
# world_skills_core · source: world_skills_core:batch_191:outpatient_front_desk_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| clinicdesk.schedule.appointment_slot | Appointment slot | invariant | Slot defines provider, service type, duration, location, time and booking rules. | schedule capacity |
| clinicdesk.schedule.template | Provider schedule template | invariant | Template sets normal clinic sessions, breaks, visit types and allowable overbooks. | repeatable calendar |
| clinicdesk.schedule.waitlist | Appointment waitlist | variant | Waitlist tracks patients who can accept earlier or alternative appointment times. | fill cancellations |
| clinicdesk.schedule.no_show | No-show record | invariant | Record notes missed appointment, policy action, reason if known and follow-up need. | protect capacity |
| clinicdesk.schedule.reschedule_rule | Reschedule rule | invariant | Rule controls how changes are made, documented and communicated to patient and provider. | reduce confusion |
| clinicdesk.registration.patient_identity | Patient identity check | invariant | Check verifies name, date of birth, contact and identifiers before service. | avoid wrong record |
| clinicdesk.registration.demographic_update | Demographic update | invariant | Update captures address, phone, emergency contact, language and communication preference. | current records |
| clinicdesk.registration.consent_status | Consent status | invariant | Status shows required consents, notices or authorizations are present before visit. | paperwork readiness |
| clinicdesk.registration.new_patient_packet | New patient packet | variant | Packet gathers history forms, privacy notices, payment information and clinic policies. | first visit setup |
| clinicdesk.registration.portal_activation | Patient portal activation | variant | Activation enables secure messages, forms, results access and appointment management. | digital access |
| clinicdesk.eligibility.coverage_check | Coverage eligibility check | invariant | Check verifies payer, plan, active coverage, network and basic visit eligibility. | reduce billing surprises |
| clinicdesk.eligibility.copay_collection | Copay collection | variant | Collection records expected patient payment, receipt, waiver reason or later billing route. | front-end revenue |
| clinicdesk.eligibility.self_pay_flag | Self-pay flag | invariant | Flag identifies patient without billable coverage or choosing direct payment. | different workflow |
| clinicdesk.eligibility.prior_authorization | Prior authorization status | variant | Status tracks approval, denial, pending request, expiration and service match. | service may depend on approval |
| clinicdesk.eligibility.referral_status | Referral status | variant | Status verifies referral source, validity, visit limit and required documentation. | route compliant care |
| clinicdesk.checkin.arrival_timestamp | Arrival timestamp | invariant | Timestamp records when patient arrives or begins check-in. | measure flow |
| clinicdesk.checkin.visit_reason | Visit reason confirmation | invariant | Confirmation matches appointment purpose, forms and provider expectations. | prepare visit |
| clinicdesk.checkin.forms_completion | Forms completion | invariant | Completion checks required questionnaires, updates, consents and signatures. | ready for rooming |
| clinicdesk.checkin.late_arrival | Late arrival handling | invariant | Handling follows policy for grace period, provider decision, reschedule or wait. | protect schedule |
| clinicdesk.checkin.interpreter_need | Interpreter need flag | variant | Flag identifies language or communication support required for visit. | accessible service |
| clinicdesk.flow.waiting_room_status | Waiting room status | invariant | Status tracks checked-in, waiting, roomed, provider-ready, completed or left. | visible patient flow |
| clinicdesk.flow.provider_delay | Provider delay communication | invariant | Communication updates patients and staff when clinic is running late. | reduce frustration |
| clinicdesk.flow.walk_in_triage_route | Walk-in routing | variant | Routing sends unscheduled patients to approved desk, nurse, urgent slot or referral path. | front desk does not diagnose |
| clinicdesk.flow.queue_priority | Desk queue priority | invariant | Priority separates check-in, checkout, phone, urgent admin issue and documentation tasks. | manage workload |
| clinicdesk.flow.service_recovery | Patient service recovery | variant | Recovery responds to delay, error, access problem or complaint with escalation and documentation. | preserve trust |
| clinicdesk.messages.phone_queue | Clinic phone queue | invariant | Queue handles appointment, refill, result, billing and urgent routing calls by script. | calls become work |
| clinicdesk.messages.secure_message | Secure patient message | invariant | Message is routed to appropriate clinical, scheduling or billing queue with timestamp. | protect privacy |
| clinicdesk.messages.callback_task | Callback task | invariant | Task records caller, issue, owner, due time and closure note. | no lost calls |
| clinicdesk.messages.result_inquiry | Result inquiry routing | variant | Inquiry is routed through authorized clinical workflow rather than front desk interpretation. | avoid unsafe advice |
| clinicdesk.messages.escalation_rule | Front desk escalation rule | invariant | Rule defines when staff contact supervisor, nurse, provider, billing or emergency channel. | know limits |
| clinicdesk.checkout.followup_booking | Follow-up booking | invariant | Booking schedules next visit, test, referral or procedure per provider instruction. | continuity |
| clinicdesk.checkout.after_visit_paperwork | After-visit paperwork | variant | Paperwork gives visit summary, orders, school/work forms or instructions from approved record. | close visit |
| clinicdesk.checkout.balance_notice | Balance notice | variant | Notice explains outstanding patient balance without delaying clinically necessary workflow. | financial clarity |
| clinicdesk.checkout.referral_packet | Referral packet | variant | Packet sends required demographics, notes, order, authorization and contact details. | handoff to outside care |
| clinicdesk.checkout.departure_status | Departure status | invariant | Status closes visit in scheduling and billing workflow when patient leaves. | end of front-desk loop |
| clinicdesk.records.document_scan | Clinic document scan | invariant | Scan attaches external forms, IDs, authorizations or correspondence to correct patient record. | evidence in chart |
| clinicdesk.records.release_request | Records release request | invariant | Request records patient authorization, recipient, scope, dates and delivery method. | privacy controlled sharing |
| clinicdesk.records.correction_request | Record correction request | variant | Request captures patient-reported error and routes to authorized record amendment process. | controlled correction |
| clinicdesk.records.duplicate_chart | Duplicate chart alert | invariant | Alert flags possible duplicate patient record for merge review. | prevent split history |
| clinicdesk.records.privacy_incident | Front desk privacy incident | invariant | Incident records misdirected communication, exposure, wrong chart or unauthorized disclosure. | respond to breach risk |
| clinicdesk.controls.cash_drawer | Clinic cash drawer control | variant | Control reconciles payments, refunds, receipts, drawer access and deposit handoff. | payment accountability |
| clinicdesk.controls.daily_close | Front desk daily close | invariant | Close verifies schedules, no-shows, messages, payments, scans, referrals and open tasks. | reset for tomorrow |
| clinicdesk.metrics.front_desk_kpi | Front desk KPI | variant | KPI tracks wait time, call abandonment, no-show rate, check-in errors and task aging. | manage service |
| clinicdesk.training.role_boundary | Front desk role boundary | invariant | Boundary separates administrative help from clinical advice, diagnosis or treatment decisions. | safety and compliance |
