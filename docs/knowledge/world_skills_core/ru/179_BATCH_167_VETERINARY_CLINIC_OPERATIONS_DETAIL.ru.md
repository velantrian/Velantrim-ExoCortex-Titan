# BATCH_167 — Veterinary Clinic Operations Detail
# world_skills_core · source: world_skills_core:batch_167:veterinary_clinic_operations_detail
# KnowledgeUnits: 44
# ВНИМАНИЕ: операционные знания о клинике; не ветеринарная диагностика и не схема лечения.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| vetops.schedule.appointment_slot | Veterinary appointment slot | invariant | Appointment slot links patient, owner, reason, clinician, room, duration and urgency. | clinic day capacity |
| vetops.schedule.walkin_policy | Walk-in policy | variant | Walk-in policy defines how unscheduled patients are triaged, queued, redirected or stabilized. | not all arrivals fit |
| vetops.schedule.no_show_tracking | Veterinary no-show tracking | invariant | No-show tracking records missed appointments and patterns by owner, service, time or reminder effectiveness. | protect clinic capacity |
| vetops.schedule.reminder_protocol | Appointment reminder protocol | variant | Reminder protocol uses calls, texts or emails to confirm visits, preparation and cancellation rules. | reduce missed slots |
| vetops.schedule.surgery_board | Surgery board | invariant | Surgery board lists procedures, patient identifiers, consent, fasting status, clinician and room sequence. | surgical day control |
| vetops.schedule.discharge_slot | Discharge slot | variant | Discharge slot reserves time to return patient, explain care plan, collect payment and answer owner questions. | end of visit matters |
| vetops.intake.patient_signalment | Patient signalment | invariant | Signalment records species, breed, age, sex, reproductive status and identifying details. | basic patient identity |
| vetops.intake.owner_contact | Owner contact verification | invariant | Contact verification confirms phone, address, email, emergency contact and authorized decision-maker. | decisions need reachable owner |
| vetops.intake.presenting_complaint | Presenting complaint record | invariant | Presenting complaint captures owner-described reason for visit without replacing clinical assessment. | why the patient came |
| vetops.intake.weight_record | Animal weight record | invariant | Weight record supports workflow, dosing calculations by clinician, monitoring and equipment choices. | current weight is critical data |
| vetops.intake.consent_form | Veterinary consent form | invariant | Consent form documents owner authorization, procedure scope, risks discussed and financial acknowledgment. | permission before action |
| vetops.intake.estimate_approval | Treatment estimate approval | variant | Estimate approval records expected charges, owner acceptance, limits and update requirements. | avoid surprise billing |
| vetops.triage.triage_category | Veterinary triage category | invariant | Triage category ranks urgency based on observed condition and clinic protocol. | prioritize safely |
| vetops.triage.red_flag_observation | Red-flag observation | invariant | Red-flag observation flags breathing distress, collapse, severe bleeding, seizure or other urgent signs for clinician review. | fast escalation |
| vetops.triage.isolation_flag | Infectious isolation flag | variant | Isolation flag separates patients with possible contagious risk before they expose waiting room or wards. | infection control |
| vetops.triage.pain_score_record | Pain score record | variant | Pain score documents observed discomfort using clinic-approved scale for clinician assessment and follow-up. | visible welfare data |
| vetops.triage.waiting_room_monitor | Waiting room monitoring | invariant | Monitoring checks patients waiting for worsening signs, stress, aggression or owner concerns. | queue is not passive |
| vetops.triage.emergency_transfer | Emergency transfer workflow | variant | Transfer workflow coordinates referral hospital, records, owner communication and safe handoff. | right care setting |
| vetops.diagnostics.sample_label | Veterinary sample label | invariant | Sample label links patient, owner, date, sample type, collector and requested test. | avoid sample mix-up |
| vetops.diagnostics.lab_request | Lab request form | invariant | Lab request specifies test, patient details, sample, history notes and reporting destination. | lab needs context |
| vetops.diagnostics.sample_storage | Sample storage condition | invariant | Storage condition preserves sample integrity until pickup, analysis or shipping. | data quality before lab |
| vetops.diagnostics.imaging_schedule | Imaging schedule | variant | Imaging schedule coordinates room, equipment, patient preparation, staff and clinician request. | shared diagnostic resource |
| vetops.diagnostics.result_routing | Diagnostic result routing | invariant | Result routing ensures findings reach responsible clinician and are filed in patient record. | no orphan results |
| vetops.diagnostics.external_lab_tracking | External lab tracking | variant | Tracking monitors courier pickup, accession, pending status, result arrival and delays. | lab workflow visibility |
| vetops.surgery.preop_checklist | Veterinary pre-op checklist | invariant | Checklist verifies identity, procedure, consent, fasting status, diagnostics, equipment and team readiness. | wrong-patient prevention |
| vetops.surgery.anesthesia_record | Anesthesia monitoring record | invariant | Monitoring record captures time-based observations and equipment readings under clinician supervision. | continuous evidence |
| vetops.surgery.instrument_pack | Instrument pack control | invariant | Pack control tracks sterilization, contents, expiry, integrity and opening for procedure. | sterile tools managed |
| vetops.surgery.surgical_count | Surgical count | invariant | Count tracks sponges, sharps and instruments before closure according to clinic procedure. | retained item prevention |
| vetops.surgery.recovery_monitoring | Recovery monitoring | invariant | Recovery monitoring observes patient until safe transfer, discharge or ward placement under protocol. | anesthesia does not end at stop |
| vetops.surgery.postop_instruction | Post-op instruction | invariant | Instruction explains owner responsibilities, warning signs, restrictions and follow-up without replacing clinician judgment. | home care handoff |
| vetops.pharmacy.prescription_record | Veterinary prescription record | invariant | Prescription record stores clinician order, patient, owner, medication identity, quantity and counseling notes. | medication traceability |
| vetops.pharmacy.dispensing_check | Veterinary dispensing check | invariant | Dispensing check verifies label, patient, product, strength, quantity and clinician authorization. | reduce medication errors |
| vetops.pharmacy.controlled_log | Controlled substance log | invariant | Controlled log records receipt, use, dispensing, waste and reconciliation where required. | high-control inventory |
| vetops.pharmacy.expiry_check | Veterinary inventory expiry check | invariant | Expiry check removes outdated medications, vaccines, reagents or supplies before use. | prevent expired use |
| vetops.pharmacy.cold_storage | Veterinary cold storage | invariant | Cold storage maintains vaccines, samples or medicines within required temperature range and logs exceptions. | temperature-sensitive stock |
| vetops.pharmacy.recall_notice | Veterinary product recall | invariant | Recall workflow identifies affected stock, patients, owners and actions required by notice. | respond to defective product |
| vetops.records.medical_record_entry | Veterinary medical record entry | invariant | Entry documents encounter facts, clinician assessment, owner communication, orders and follow-up. | legal and care continuity |
| vetops.records.record_amendment | Record amendment | invariant | Amendment changes record transparently with date, author, reason and preserved original context. | no silent edits |
| vetops.records.discharge_summary | Veterinary discharge summary | invariant | Summary gives owner diagnosis wording from clinician, performed services, next steps and contact path. | owner leaves with clarity |
| vetops.records.referral_packet | Referral packet | variant | Packet includes history, diagnostics, treatments, images and reason for referral to another facility. | continuity across clinics |
| vetops.facility.kennel_card | Kennel card | invariant | Kennel card identifies patient, restrictions, feeding, alerts and responsible team while hospitalized. | cage-side identity |
| vetops.facility.cleaning_between_patients | Cleaning between patients | invariant | Cleaning rooms, tables and equipment between patients reduces cross-contamination and odor. | hygiene rhythm |
| vetops.facility.sharps_disposal | Veterinary sharps disposal | invariant | Sharps disposal uses approved containers and handling to prevent puncture injuries and contamination. | staff safety |
| vetops.facility.bite_incident_log | Bite or scratch incident log | invariant | Incident log records animal-related injury, context, first aid, reporting and follow-up. | occupational safety |
