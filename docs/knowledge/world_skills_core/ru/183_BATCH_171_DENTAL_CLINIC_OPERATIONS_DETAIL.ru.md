# BATCH_171 — Dental Clinic Operations Detail
# world_skills_core · source: world_skills_core:batch_171:dental_clinic_operations_detail
# KnowledgeUnits: 44
# ВНИМАНИЕ: операционные знания о стоматологической клинике; не диагностика, не лечение и не медицинские назначения.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| dentalops.schedule.appointment_type | Dental appointment type | invariant | Appointment type defines expected duration, room, provider, assistant, equipment and preparation. | capacity starts with visit type |
| dentalops.schedule.recall_schedule | Dental recall schedule | variant | Recall schedule plans follow-up or preventive visits by patient status, clinic policy and provider recommendation. | bring patients back on time |
| dentalops.schedule.broken_appointment | Broken appointment tracking | invariant | Tracking missed or late-cancelled appointments shows capacity loss, communication gaps and patient patterns. | chair time is scarce |
| dentalops.schedule.emergency_slot | Dental emergency slot | variant | Emergency slots reserve capacity for urgent dental issues without collapsing routine schedule. | absorb same-day demand |
| dentalops.schedule.lab_case_due | Lab case due date | invariant | Lab case due date links appointment timing with external or internal dental lab readiness. | do not seat without case |
| dentalops.schedule.provider_column | Provider column | invariant | Provider column organizes dentist, hygienist or specialist time by procedure mix and room availability. | schedule by provider capacity |
| dentalops.intake.medical_history_update | Medical history update | invariant | Update collects relevant patient history changes before treatment and routes concerns to clinician. | patient context changes |
| dentalops.intake.consent_record | Dental consent record | invariant | Consent record documents procedure explanation, patient questions, authorization and version of planned care. | permission with evidence |
| dentalops.intake.financial_estimate | Dental financial estimate | variant | Estimate explains expected patient responsibility, insurance assumptions, exclusions and approval before work. | avoid billing surprise |
| dentalops.intake.insurance_verification | Dental insurance verification | variant | Verification checks eligibility, benefits, waiting periods, frequencies, remaining maximum and claim rules. | coverage is not guarantee |
| dentalops.intake.patient_identifier | Dental patient identifier | invariant | Patient identifier confirms correct chart, imaging, lab case, consent and appointment. | wrong chart prevention |
| dentalops.intake.chief_concern | Dental chief concern | invariant | Chief concern records patient-stated reason for visit before clinician assessment. | why they came |
| dentalops.sterilization.instrument_flow | Dental instrument flow | invariant | Instrument flow moves used instruments through transport, cleaning, packaging, sterilization, storage and chairside use. | dirty-to-clean path |
| dentalops.sterilization.autoclave_cycle | Autoclave cycle record | invariant | Cycle record captures load, parameters, operator, date and result for sterilization traceability. | prove sterilization |
| dentalops.sterilization.biological_indicator | Biological indicator | invariant | Biological indicator verifies sterilizer performance by testing resistant organisms under defined schedule. | sterility assurance |
| dentalops.sterilization.pouch_integrity | Sterilization pouch integrity | invariant | Pouch integrity check confirms seal, dryness, indicator change and no damage before storage or use. | package protects sterile item |
| dentalops.sterilization.sharps_container | Dental sharps container | invariant | Sharps container placement and replacement reduce needle and blade injury risk. | safe disposal |
| dentalops.sterilization.clean_dirty_separation | Clean-dirty separation | invariant | Separation prevents contaminated instruments from crossing into sterile storage or preparation areas. | workflow protects patients |
| dentalops.room.treatment_room_turnover | Treatment room turnover | invariant | Room turnover resets surfaces, barriers, suction lines, instruments, disposables and waste between patients. | fast but controlled reset |
| dentalops.room.barrier_placement | Barrier placement | invariant | Barriers protect high-touch surfaces and equipment from contamination during patient care. | reduce cleaning burden |
| dentalops.room.unit_waterline | Dental unit waterline maintenance | invariant | Waterline maintenance follows clinic protocol for flushing, treatment and monitoring. | water system is equipment |
| dentalops.room.suction_maintenance | Dental suction maintenance | invariant | Suction maintenance preserves evacuation performance and reduces blockage, odor and contamination. | hidden infrastructure |
| dentalops.room.material_setup | Dental material setup | variant | Material setup prepares products, devices and forms needed for planned procedure before patient is seated. | reduce mid-procedure search |
| dentalops.room.room_readiness_check | Dental room readiness check | invariant | Readiness check verifies room, instruments, imaging, materials, PPE and chart before visit starts. | prevent delays |
| dentalops.imaging.image_request | Dental imaging request | invariant | Imaging request links patient, tooth/area, purpose, date and provider authorization. | image has reason |
| dentalops.imaging.image_label | Dental image labeling | invariant | Labeling ties radiograph or scan to patient, date, orientation, region and provider. | avoid image mix-up |
| dentalops.imaging.radiation_log | Dental radiation log | variant | Log records exposure details where required by policy or regulation. | imaging accountability |
| dentalops.imaging.sensor_disinfection | Imaging sensor disinfection | invariant | Sensor disinfection and barrier use protect patients while preserving equipment. | shared device control |
| dentalops.imaging.image_quality_review | Dental image quality review | invariant | Review identifies retakes, positioning errors, artifacts and whether image is diagnostically usable for clinician. | reduce unnecessary retake |
| dentalops.imaging.external_image_import | External image import | variant | Import workflow attaches outside images to correct chart with source, date and consent where needed. | complete record |
| dentalops.lab.lab_case_tracking | Dental lab case tracking | invariant | Tracking follows impression, scan, prescription, shade, due date, receipt and patient appointment link. | case cannot vanish |
| dentalops.lab.shade_record | Dental shade record | invariant | Shade record documents selected shade, method, lighting note or photo reference. | aesthetic communication |
| dentalops.lab.impression_disinfection | Impression disinfection | invariant | Disinfection protects lab and clinic staff before impression transport or processing. | cross-site infection control |
| dentalops.lab.remake_reason | Dental lab remake reason | variant | Remake reason classifies fit, shade, fracture, design, impression or communication issue. | reduce repeat waste |
| dentalops.lab.case_delivery_check | Lab case delivery check | invariant | Delivery check confirms case arrived, matches patient, includes components and is ready before appointment. | prevent chairside surprise |
| dentalops.records.chart_note | Dental chart note | invariant | Chart note records visit facts, clinician findings, procedures, materials, instructions and follow-up. | continuity and evidence |
| dentalops.records.treatment_plan_version | Treatment plan version | invariant | Versioning preserves changes to planned care, estimates, sequencing and patient acceptance. | plan evolves transparently |
| dentalops.records.referral_record | Dental referral record | variant | Referral record includes reason, provider, records sent, urgency and follow-up status. | continuity outside clinic |
| dentalops.records.prescription_log | Dental prescription log | invariant | Prescription log records clinician order, patient, product, date and communication path without replacing clinical judgment. | trace medication orders |
| dentalops.records.incident_report | Dental clinic incident report | invariant | Report captures injury, exposure, equipment failure, complaint or safety event with actions taken. | clinic learning |
| dentalops.inventory.implant_component | Implant component tracking | variant | Component tracking links implant-related parts to patient, lot, expiry and procedure record. | high-traceability item |
| dentalops.inventory.dental_material_expiry | Dental material expiry | invariant | Expiry check removes outdated bonding agents, impression materials, anesthetic cartridges or disposables from use. | product quality |
| dentalops.inventory.bur_block_control | Bur block control | variant | Bur control tracks cleaning, wear, replacement and availability of rotary instruments. | small tool, high use |
| dentalops.inventory.ppe_stock | Dental PPE stock | invariant | PPE stock planning covers masks, gloves, eyewear, gowns and specialty items by procedure volume. | protect staff and patients |
