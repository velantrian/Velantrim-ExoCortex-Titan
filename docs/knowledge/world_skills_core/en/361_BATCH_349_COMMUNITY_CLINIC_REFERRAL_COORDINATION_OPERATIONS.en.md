# BATCH 349: Community Clinic Referral Coordination Operations

**KnowledgeUnits:** 44  
**Namespace:** `clinicrefops.*`  
**Scope:** referral intake, eligibility, records, scheduling, follow-up, no-shows and closed-loop tracking.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| clinicrefops.intake.referral_id | referral ID | RECORD | Referral ID links patient, source, service requested, date and coordinator. | Creates traceable handoff. |
| clinicrefops.intake.source | referral source | RECORD | Source distinguishes primary care, ED, school, social service, outreach or self-referral. | Helps prioritize and communicate. |
| clinicrefops.intake.reason | referral reason | RECORD | Reason summarizes need without replacing clinical assessment. | Preserves why the referral exists. |
| clinicrefops.intake.urgency | urgency level | MODEL | Urgency reflects risk, symptoms, time sensitivity and service capacity. | Guides scheduling priority. |
| clinicrefops.intake.consent | information consent | SAFETY_RULE | Sharing records requires patient consent or lawful basis. | Protects privacy. |
| clinicrefops.eligibility.coverage | coverage check | METHOD | Coverage check reviews insurance, program eligibility, sliding fee or charity care. | Reduces surprise costs. |
| clinicrefops.eligibility.service_fit | service fit | METHOD | Service fit checks whether clinic can provide requested specialty or support. | Avoids wrong referrals. |
| clinicrefops.eligibility.catchment | catchment rule | CONSTRAINT | Catchment rules may limit geography, population or program category. | Uses resources as intended. |
| clinicrefops.eligibility.barrier_screen | barrier screen | METHOD | Screen identifies transport, language, housing, phone, disability or technology barriers. | Supports successful attendance. |
| clinicrefops.records.minimum_packet | minimum packet | RECORD | Packet includes demographics, referral reason, relevant records and contact details. | Lets receiving clinic act. |
| clinicrefops.records.missing_info | missing information | FAILURE_MODE | Missing records, consent or contact details delay referral. | Creates clear follow-up task. |
| clinicrefops.records.secure_transfer | secure transfer | SAFETY_RULE | Records move through approved secure channel. | Prevents privacy breach. |
| clinicrefops.records.update_log | update log | RECORD | Log records contacts, attempts, status and next action. | Keeps coordination continuous. |
| clinicrefops.scheduling.appointment_match | appointment match | METHOD | Appointment match considers urgency, service type, location, language and patient availability. | Increases completed visits. |
| clinicrefops.scheduling.waitlist | waitlist | METHOD | Waitlist records priority, earliest acceptable date and contact rules. | Manages limited slots. |
| clinicrefops.scheduling.transport | transport support | METHOD | Transport support may arrange ride resources or directions. | Reduces no-shows. |
| clinicrefops.scheduling.reminder | reminder | METHOD | Reminder confirms appointment, location, prep and cancellation path. | Improves attendance. |
| clinicrefops.scheduling.reschedule | reschedule workflow | METHOD | Reschedule keeps referral active while updating urgency and barrier notes. | Prevents silent dropout. |
| clinicrefops.no_show.no_show_record | no-show record | RECORD | No-show records missed appointment, outreach attempts and reason if known. | Enables follow-up. |
| clinicrefops.no_show.risk_review | no-show risk review | MODEL | Risk review distinguishes routine miss from medically or socially high-risk loss to follow-up. | Prioritizes outreach. |
| clinicrefops.no_show.outreach | outreach attempt | METHOD | Outreach uses approved channels and privacy-safe messages. | Reconnects patient. |
| clinicrefops.no_show.close_rule | no-show closure rule | CONSTRAINT | Referral closes only after defined attempts, time or source notification. | Avoids premature closure. |
| clinicrefops.followup.visit_confirm | visit confirmation | RECORD | Visit confirmation records whether patient attended, declined, rescheduled or redirected. | Closes the loop. |
| clinicrefops.followup.result_summary | result summary | RECORD | Result summary sends necessary outcome back to referring provider under consent. | Supports continuity of care. |
| clinicrefops.followup.next_step | next step | METHOD | Next step may be additional service, community resource, return visit or case closure. | Keeps care pathway moving. |
| clinicrefops.followup.patient_feedback | patient feedback | METHOD | Feedback captures access barriers, clarity and satisfaction. | Improves referral system. |
| clinicrefops.communication.patient_message | patient message | METHOD | Message uses plain language and avoids sensitive details when channel is uncertain. | Protects privacy and comprehension. |
| clinicrefops.communication.referrer_update | referrer update | METHOD | Referrer receives status such as accepted, scheduled, completed, delayed or declined. | Prevents duplicate referrals. |
| clinicrefops.communication.language | language services | METHOD | Interpretation and translated instructions are arranged when needed. | Supports equitable access. |
| clinicrefops.communication.warm_handoff | warm handoff | METHOD | Warm handoff connects patient directly to receiving service or navigator. | Reduces drop-off. |
| clinicrefops.capacity.slot_inventory | slot inventory | RECORD | Slot inventory tracks service availability, provider, location and eligibility constraints. | Makes scheduling realistic. |
| clinicrefops.capacity.backlog | referral backlog | MEASUREMENT | Backlog tracks open referrals by age, urgency and service type. | Shows access pressure. |
| clinicrefops.capacity.diversion | diversion route | METHOD | Diversion sends referral to alternate clinic, telehealth or community partner when capacity is insufficient. | Prevents stalled care. |
| clinicrefops.capacity.priority_review | priority review | QUALITY_CHECK | High-urgency referrals are reviewed for scheduling delays. | Reduces harm from waitlists. |
| clinicrefops.quality.closed_loop | closed-loop rate | MEASUREMENT | Closed-loop rate measures referrals with confirmed outcome. | Shows coordination reliability. |
| clinicrefops.quality.leakage | referral leakage | FAILURE_MODE | Leakage occurs when referral never reaches appointment or outcome confirmation. | Identifies system breaks. |
| clinicrefops.quality.data_accuracy | data accuracy check | QUALITY_CHECK | Contact, eligibility, appointment and status fields are sampled for accuracy. | Prevents operational drift. |
| clinicrefops.integration.ehr_link | EHR link | METHOD | Referral is linked to EHR task, order or external referral module where possible. | Reduces double entry. |
| clinicrefops.integration.community_resource | community resource link | METHOD | Nonclinical needs can link to food, housing, transport or benefits resources. | Addresses access barriers. |
| clinicrefops.integration.hie | health information exchange | CONSTRAINT | HIE use follows consent, minimum necessary and access rules. | Keeps exchange lawful. |
| clinicrefops.governance.owner | referral owner | RECORD | Each referral has active owner until completed, transferred or closed. | Avoids abandoned referrals. |
| clinicrefops.governance.protocol | referral protocol | METHOD | Protocol defines acceptance criteria, urgency, records and escalation. | Standardizes coordination. |
| clinicrefops.governance.safety_net | safety net rule | SAFETY_RULE | High-risk unresolved referrals require escalation or documented clinical review. | Protects vulnerable patients. |
| clinicrefops.closeout.closure_reason | closure reason | RECORD | Closure reason states completed, declined, unreachable, ineligible, duplicate or transferred. | Makes outcomes measurable. |
