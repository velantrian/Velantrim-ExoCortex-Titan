# BATCH_226 — Blood Donation Center Operations Detail
# world_skills_core · source: world_skills_core:batch_226:blood_donation_center_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| bloodops.schedule.donor_appointment | Blood donor appointment | invariant | Appointment records donor, donation type, time, site, eligibility reminders and contact. | plan donor flow |
| bloodops.schedule.walkin_flow | Blood donation walk-in flow | variant | Flow handles unscheduled donors by capacity, staffing and inventory need. | flexible intake |
| bloodops.schedule.donation_type | Donation type schedule | invariant | Type allocates whole blood, platelet, plasma or other collection slot where offered. | match equipment |
| bloodops.schedule.no_show | Donor no-show record | invariant | Record tracks missed appointment, communication and rescheduling. | protect capacity |
| bloodops.schedule.mobile_drive | Mobile blood drive schedule | variant | Schedule coordinates host site, staff, equipment, donor slots, transport and setup. | offsite collection |
| bloodops.registration.donor_identity | Donor identity check | invariant | Check verifies donor identity against record before screening and labeling. | right donor |
| bloodops.registration.consent_capture | Blood donation consent capture | invariant | Consent confirms donor understands process, testing, privacy and release rules. | permission evidence |
| bloodops.registration.questionnaire | Donor questionnaire | invariant | Questionnaire captures health, travel, medication and risk information for trained review. | screening input |
| bloodops.registration.record_update | Donor record update | invariant | Update captures contact, demographics, deferral status and communication preference. | current donor file |
| bloodops.registration.language_support | Donor language support | variant | Support ensures donor can understand forms, questions and instructions. | informed process |
| bloodops.screening.screening_queue | Donor screening queue | invariant | Queue manages private interview, checks, deferral review and collection readiness. | orderly flow |
| bloodops.screening.deferral_status | Donor deferral status | invariant | Status records temporary, permanent or resolved deferral according to trained decision process. | eligibility control |
| bloodops.screening.vital_check_record | Donor vital check record | invariant | Record captures required pre-donation measurements for staff review. | safety gate |
| bloodops.screening.hemoglobin_check | Hemoglobin check workflow | variant | Workflow records sample, result, staff, device and eligibility outcome under protocol. | donation safety |
| bloodops.screening.private_interview | Donor private interview | invariant | Interview protects confidentiality while reviewing questionnaire and eligibility. | privacy and safety |
| bloodops.collection.bed_assignment | Donor bed assignment | invariant | Assignment links donor, donation type, collection staff, equipment and unit labels. | collection setup |
| bloodops.collection.collection_kit | Blood collection kit | invariant | Kit includes bag, tubing, labels, needle, samples and required supplies. | ready collection |
| bloodops.collection.unit_label | Blood unit label | invariant | Label uniquely identifies collected unit, donor, samples and processing path. | traceability |
| bloodops.collection.collection_start | Collection start record | invariant | Record captures start time, staff, unit ID, equipment and donor readiness. | begin chain |
| bloodops.collection.collection_end | Collection end record | invariant | Record captures end time, volume/status, samples, reaction notes and disposition. | close collection |
| bloodops.donorcare.reaction_response | Donor reaction response | invariant | Response documents faintness, bruising, nausea or other event and staff action under protocol. | donor safety |
| bloodops.donorcare.post_donation_care | Post-donation care | invariant | Care provides rest, refreshments, instructions and observation as required. | recovery |
| bloodops.donorcare.adverse_event_report | Donor adverse event report | invariant | Report captures event, severity, actions, follow-up and quality review. | safety learning |
| bloodops.donorcare.aftercare_instruction | Donor aftercare instruction | invariant | Instruction gives approved post-donation guidance and contact path. | donor leaves informed |
| bloodops.donorcare.followup_contact | Donor follow-up contact | variant | Contact checks recovery, reports issue or requests additional information. | close loop |
| bloodops.specimen.sample_tube_label | Sample tube label | invariant | Label links test samples to unit and donor before lab handoff. | specimen identity |
| bloodops.specimen.sample_packout | Blood sample packout | invariant | Packout protects tubes, requisitions, temperature and transport route. | lab readiness |
| bloodops.specimen.courier_handoff | Blood sample courier handoff | invariant | Handoff records time, courier, container, condition and destination. | custody |
| bloodops.specimen.missing_sample | Missing sample exception | invariant | Exception records absent, unlabeled, broken or mismatched sample and escalation. | testing risk |
| bloodops.specimen.test_result_route | Donor test result route | variant | Route sends lab result, quarantine, release or donor notification tasks through approved process. | controlled output |
| bloodops.component.unit_quarantine | Blood unit quarantine | invariant | Quarantine holds unit until testing, review or investigation clears disposition. | protect supply |
| bloodops.component.component_handoff | Component processing handoff | variant | Handoff transfers unit to processing with temperature, time and identity controls. | next stage |
| bloodops.component.temperature_log | Blood product temperature log | invariant | Log tracks required storage or transport temperature for units and components. | quality |
| bloodops.component.discard_record | Blood unit discard record | invariant | Record documents reason, unit, authorization and disposal route. | trace loss |
| bloodops.component.inventory_status | Blood inventory status | variant | Status tracks collected, quarantined, released, shipped, expired or discarded units. | supply visibility |
| bloodops.quality.equipment_qc | Donation equipment QC | invariant | QC checks scales, sealers, refrigerators, agitators, beds and screening devices. | reliable operation |
| bloodops.quality.lot_trace | Blood collection lot trace | invariant | Trace links bags, tubes, reagents, labels and supplies to donation events. | recall support |
| bloodops.quality.deviation_report | Blood center deviation report | invariant | Report documents process departure, impact assessment, containment and corrective action. | quality system |
| bloodops.quality.staff_competency | Blood center staff competency | invariant | Competency tracks registration, screening, phlebotomy, donor care, labeling and emergency response. | qualified work |
| bloodops.quality.audit_trail | Blood donation audit trail | invariant | Trail records donor flow, labels, units, samples, staff actions, exceptions and dispositions. | full trace |
| bloodops.mobile.mobile_setup | Mobile blood drive setup | variant | Setup places beds, screening, privacy, supplies, power, refrigeration and donor flow. | temporary center |
| bloodops.mobile.mobile_teardown | Mobile blood drive teardown | variant | Teardown secures units, samples, waste, equipment, records and site cleanup. | safe departure |
| bloodops.metrics.blood_center_kpi | Blood donation center KPI | variant | KPI tracks donor throughput, deferrals, reactions, collection failures, discards and appointment fill. | manage center |
| bloodops.continuity.refrigeration_alarm | Blood refrigeration alarm response | invariant | Response protects units, documents excursion, escalates quality review and restores storage. | product safety |
