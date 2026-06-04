# BATCH_207 — Urgent Care Clinic Operations Detail
# world_skills_core · source: world_skills_core:batch_207:urgent_care_clinic_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| urgentops.intake.walk_in_registration | Walk-in registration | invariant | Registration captures identity, contact, reason for visit, payer, consent and arrival time. | start visit fast |
| urgentops.intake.online_checkin | Urgent care online check-in | variant | Online check-in gathers demographics, symptoms, forms and estimated arrival before patient reaches clinic. | reduce front desk load |
| urgentops.intake.arrival_priority | Arrival priority flag | invariant | Flag identifies patient needing immediate clinical triage before normal queue. | do not wait blindly |
| urgentops.intake.identity_band | Urgent care identity band | variant | Band links patient to chart, orders, samples and discharge paperwork when used. | reduce mix-ups |
| urgentops.intake.consent_capture | Urgent care consent capture | invariant | Consent confirms treatment, privacy, financial responsibility and release rules before services. | permission baseline |
| urgentops.triage.triage_route | Triage routing | invariant | Routing sends patient to room, waiting, emergency transfer, test path or provider review based on clinic protocol. | right next step |
| urgentops.triage.vital_signs_capture | Vital signs capture | invariant | Capture records basic measurements, time, staff and abnormal flags for clinician review. | visit baseline |
| urgentops.triage.red_flag_escalation | Red flag escalation | invariant | Escalation alerts clinical lead or emergency services for dangerous presentation under protocol. | safety gate |
| urgentops.triage.chief_complaint | Chief complaint record | invariant | Record summarizes main reason for visit in patient words or structured category. | focus encounter |
| urgentops.triage.isolation_flag | Infection isolation flag | variant | Flag prompts mask, rooming, cleaning or workflow changes for possible contagious illness. | protect clinic |
| urgentops.flow.room_assignment | Urgent care room assignment | invariant | Assignment matches patient need, room availability, equipment, isolation and provider flow. | keep clinic moving |
| urgentops.flow.queue_status | Urgent care queue status | invariant | Status tracks waiting, triage, roomed, testing, provider, procedure, discharge or transfer. | visible flow |
| urgentops.flow.provider_handoff | Provider handoff | invariant | Handoff gives clinician triage notes, tests pending, risk flags and patient location. | no lost context |
| urgentops.flow.procedure_room_turnover | Procedure room turnover | invariant | Turnover cleans, restocks and resets procedure area after wound care, splinting or other task. | ready and safe |
| urgentops.flow.delayed_visit_notice | Delayed visit notice | variant | Notice updates patients about wait, reason and options when clinic flow slows. | reduce frustration |
| urgentops.testing.point_of_care_test | Point-of-care testing flow | variant | Flow orders, collects, runs, records and communicates rapid test results through approved process. | fast diagnostic support |
| urgentops.testing.specimen_label | Urgent care specimen label | invariant | Label links sample to patient, test, time and collector before sending or running. | sample identity |
| urgentops.testing.lab_sendout | Urgent care lab sendout | variant | Sendout packages specimen, requisition, courier pickup and result routing to external lab. | tests beyond clinic |
| urgentops.testing.xray_order_flow | Urgent care x-ray flow | variant | Flow coordinates order, positioning, image transfer, interpretation and safety checks. | imaging support |
| urgentops.testing.result_callback_queue | Result callback queue | invariant | Queue tracks pending results needing patient notification or clinician action. | close test loop |
| urgentops.supplies.room_stock | Urgent care room stock | invariant | Stock includes common disposables, PPE, forms, diagnostic supplies and procedure materials. | avoid delays |
| urgentops.supplies.crash_cart_check | Emergency cart check | variant | Check verifies seal, supplies, oxygen, device readiness and expiration dates per protocol. | rare but critical |
| urgentops.supplies.medication_storage | Clinic medication storage | variant | Storage controls access, temperature, expiration and logs for clinic-held medications. | safe inventory |
| urgentops.supplies.vaccine_cold_chain | Vaccine cold chain | variant | Cold chain logs temperature, excursions and inventory where urgent care administers vaccines. | potency control |
| urgentops.supplies.expiration_round | Supply expiration round | invariant | Round removes expired tests, medications, sterile packs and consumables. | prevent unsafe use |
| urgentops.records.visit_note | Urgent care visit note | invariant | Note documents history, exam, tests, assessment, plan, instructions and disposition by authorized clinician. | encounter evidence |
| urgentops.records.work_school_note | Work or school note | variant | Note records attendance restriction or return guidance from clinician-approved template. | common admin output |
| urgentops.records.referral_order | Urgent care referral order | variant | Order directs patient to specialist, imaging, primary care or emergency department follow-up. | continuity |
| urgentops.records.transfer_record | Emergency transfer record | invariant | Record documents reason, receiving facility, transport, handoff and accompanying documents. | high-risk handoff |
| urgentops.records.privacy_control | Urgent care privacy control | invariant | Control protects conversations, charts, screens and discharge papers in high-flow clinic. | trust and compliance |
| urgentops.discharge.discharge_instruction | Discharge instruction | invariant | Instruction gives approved care steps, warning signs, prescriptions if any, follow-up and contact path. | patient leaves informed |
| urgentops.discharge.followup_call | Urgent care follow-up call | variant | Call checks status, pending results, referral completion or service issue by protocol. | close loop |
| urgentops.discharge.patient_portal_release | Portal release workflow | variant | Workflow publishes results or visit documents according to policy and timing. | digital access |
| urgentops.discharge.unreachable_patient | Unreachable patient process | invariant | Process documents attempts, alternate contacts if permitted, letters and escalation for important result. | do not drop risk |
| urgentops.discharge.prescription_handoff | Prescription handoff record | variant | Record verifies pharmacy, electronic transmission, printed order or issue needing correction. | medication workflow evidence |
| urgentops.billing.charge_review | Urgent care charge review | invariant | Review checks visit level, procedures, tests, supplies and payer rules before claim. | accurate billing |
| urgentops.billing.eligibility_exception | Eligibility exception | variant | Exception flags inactive coverage, wrong plan, referral need, self-pay or payer mismatch. | front-end fix |
| urgentops.billing.patient_balance | Patient balance workflow | variant | Workflow explains copay, deductible, estimate, payment, refund or later billing. | financial clarity |
| urgentops.quality.patient_complaint | Urgent care complaint | invariant | Complaint records wait, communication, billing, quality, privacy or staff concern and response. | service recovery |
| urgentops.quality.incident_report | Urgent care incident report | invariant | Report documents fall, adverse event, wrong patient risk, specimen error, equipment issue or aggression. | safety learning |
| urgentops.quality.chart_audit | Urgent care chart audit | variant | Audit checks documentation, orders, results, discharge, coding and follow-up completion. | quality control |
| urgentops.admin.staffing_board | Urgent care staffing board | invariant | Board shows provider, nurse, technician, front desk and imaging or lab coverage by shift. | know available capacity |
| urgentops.metrics.uc_kpi | Urgent care KPI | variant | KPI tracks door-to-provider time, length of stay, callbacks, transfers, complaints and abandoned visits. | manage throughput |
| urgentops.continuity.surge_plan | Urgent care surge plan | invariant | Plan adjusts staffing, triage, rooms, supplies and communication during volume spike. | handle demand waves |
