# BATCH_203 — Radiology Imaging Center Operations Detail
# world_skills_core · source: world_skills_core:batch_203:radiology_imaging_center_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| radops.schedule.imaging_order | Imaging order | invariant | Order states patient, modality, body part, indication, priority and ordering provider. | exam authority |
| radops.schedule.modality_slot | Modality slot | invariant | Slot allocates scanner, protocol time, room, technologist and preparation window. | schedule scarce equipment |
| radops.schedule.prep_instruction | Imaging prep instruction | invariant | Instruction tells patient fasting, clothing, arrival, medication or document requirements. | reduce failed exams |
| radops.schedule.authorization_status | Imaging authorization status | variant | Status tracks payer approval, denial, pending review, expiration and exam match. | prevent billing denial |
| radops.schedule.no_show_recovery | Imaging no-show recovery | invariant | Recovery contacts patient, updates order status, releases slot and reschedules if needed. | protect capacity |
| radops.protocol.protocoling | Radiology protocoling | invariant | Protocoling selects exam parameters, contrast, sequences or views based on order and history. | right exam setup |
| radops.protocol.laterality_check | Imaging laterality check | invariant | Check confirms right, left or bilateral body side before exam. | avoid wrong-side imaging |
| radops.protocol.contrast_screen | Contrast screening | variant | Screening checks allergy, kidney risk, pregnancy status where relevant and prior reactions. | contrast safety gate |
| radops.protocol.implant_screen | MRI implant screening | variant | Screening identifies implants, devices, metal fragments and documentation required for MRI safety. | magnetic risk control |
| radops.protocol.prior_image_review | Prior image review | variant | Review compares earlier studies to choose protocol and support interpretation. | context matters |
| radops.intake.patient_identity | Imaging patient identity check | invariant | Check verifies patient identifiers against order before exam. | correct patient |
| radops.intake.consent_form | Imaging consent form | variant | Consent documents patient agreement for contrast, invasive component or special procedure. | permission evidence |
| radops.intake.clinical_history | Imaging clinical history | invariant | History captures symptoms, surgery, trauma, labs or question to answer. | help interpretation |
| radops.intake.gowning_locker | Gowning and locker process | variant | Process removes metal or clothing items and secures belongings before exam. | readiness and safety |
| radops.intake.pregnancy_screen | Pregnancy screening | variant | Screening follows policy before radiation or contrast exposure. | risk review |
| radops.flow.patient_call | Patient call to scanner | invariant | Call moves patient from waiting area to modality with identity and readiness check. | flow control |
| radops.flow.exam_timeout | Imaging exam timeout | invariant | Timeout confirms patient, exam, side, contrast, allergies and protocol before acquisition. | prevent major errors |
| radops.flow.positioning | Imaging positioning | invariant | Positioning aligns patient, body part, coil, detector or table for diagnostic acquisition. | image starts with setup |
| radops.flow.motion_management | Motion management | variant | Management uses instruction, supports, timing or repeat policy to reduce motion artifact. | sharper images |
| radops.flow.exam_completion | Exam completion status | invariant | Status records completed, partial, canceled, refused or failed exam with reason. | close workflow |
| radops.modality.xray_flow | X-ray workflow | variant | Workflow covers order check, positioning, exposure, image review and radiation safety. | common modality |
| radops.modality.ct_flow | CT workflow | variant | Workflow covers protocol, positioning, scout, acquisition, contrast timing and reconstruction. | cross-sectional flow |
| radops.modality.mri_flow | MRI workflow | variant | Workflow covers safety screen, coils, sequences, monitoring, communication and image transfer. | controlled magnetic environment |
| radops.modality.ultrasound_flow | Ultrasound workflow | variant | Workflow covers patient prep, probe selection, images, measurements and sonographer notes. | operator-dependent imaging |
| radops.modality.mammography_flow | Mammography workflow | variant | Workflow covers positioning, compression, image quality, prior comparison and patient communication. | specialized screening |
| radops.qa.image_quality_check | Radiology image quality check | invariant | Check reviews coverage, positioning, exposure, artifacts, labels and completeness before release. | avoid nondiagnostic study |
| radops.qa.repeat_image | Repeat image record | invariant | Record explains repeated acquisition due to motion, positioning, exposure or artifact. | dose and quality tracking |
| radops.qa.dicom_metadata | DICOM metadata check | invariant | Check verifies patient, study, series, laterality, timestamps and accession. | digital identity |
| radops.qa.critical_finding_route | Critical finding route | invariant | Route ensures urgent radiologist findings reach responsible clinical contact. | safety communication |
| radops.qa.discrepancy_review | Imaging discrepancy review | variant | Review examines interpretation, prior comparisons, technical limitations and communication issues. | learn from misses |
| radops.records.accession_number | Radiology accession number | invariant | Accession uniquely links order, exam, images, report and billing. | study anchor |
| radops.records.pacs_transfer | PACS transfer | invariant | Transfer sends images to archive with complete metadata and confirmation. | images available |
| radops.records.report_status | Radiology report status | invariant | Status tracks draft, preliminary, final, amended or addendum report. | know interpretation state |
| radops.records.result_delivery | Imaging result delivery | invariant | Delivery routes final report to ordering provider, patient portal or referral system. | complete loop |
| radops.records.image_release | Image release request | variant | Request provides images to patient or external provider with authorization and format. | portability |
| radops.safety.radiation_dose_record | Radiation dose record | variant | Record captures exposure metrics for applicable modalities and quality monitoring. | dose awareness |
| radops.safety.mri_zone_control | MRI zone control | variant | Control restricts access by safety zone, screening status and trained supervision. | magnetic safety |
| radops.safety.contrast_reaction | Contrast reaction response | variant | Response documents symptoms, actions, clinician involvement, lot and follow-up. | adverse event control |
| radops.safety.fall_risk | Imaging fall risk | invariant | Risk flag prompts transfer help, wheelchair, escort or monitoring during visit. | patient safety |
| radops.safety.equipment_qc | Imaging equipment QC | invariant | QC checks scanner performance, calibration, artifacts, safety systems and service status. | reliable modality |
| radops.billing.charge_capture | Imaging charge capture | invariant | Capture links completed exam, contrast, supplies and modifiers to billing workflow. | bill what happened |
| radops.metrics.turnaround_time | Radiology turnaround time | variant | Metric measures order-to-schedule, exam-to-report and critical-result communication time. | manage delays |
| radops.metrics.modality_utilization | Modality utilization KPI | variant | KPI tracks scanner occupancy, cancellations, repeats, downtime and backlog. | manage capacity |
| radops.continuity.scanner_downtime | Scanner downtime procedure | invariant | Procedure reroutes patients, reschedules exams, informs staff and tracks service recovery. | recover capacity |
