# BATCH_202 — Ophthalmology Clinic Operations Detail
# world_skills_core · source: world_skills_core:batch_202:ophthalmology_clinic_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| eyeclinic.schedule.visit_type | Ophthalmology visit type | invariant | Visit type defines exam, imaging, procedure, post-op, contact lens or urgent slot. | schedule correctly |
| eyeclinic.schedule.provider_template | Eye clinic provider template | invariant | Template allocates physician, optometrist, technician, imaging and procedure capacity. | match flow to resources |
| eyeclinic.schedule.dilation_buffer | Dilation buffer | variant | Buffer accounts for waiting time after drops before exam or imaging. | eye visits take time |
| eyeclinic.schedule.recall_list | Eye clinic recall list | invariant | Recall list tracks patients due for follow-up, monitoring, imaging or post-op visit. | prevent lost follow-up |
| eyeclinic.schedule.urgent_eye_route | Urgent eye routing | variant | Routing escalates red-flag symptoms to clinical triage rather than routine scheduling. | front desk boundary |
| eyeclinic.intake.ocular_history | Ocular history intake | invariant | Intake records prior eye disease, surgery, injury, lenses, medications and symptoms. | exam context |
| eyeclinic.intake.visual_acuity | Visual acuity capture | invariant | Capture records measured vision using clinic method, correction status and eye laterality. | baseline function |
| eyeclinic.intake.laterality_check | Eye laterality check | invariant | Check confirms right, left or both eyes for testing, procedure and documentation. | prevent wrong-eye errors |
| eyeclinic.intake.medication_allergy | Eye clinic medication allergy | invariant | Record flags allergy or sensitivity relevant to drops, contrast or procedure supplies. | safety screen |
| eyeclinic.intake.consent_status | Ophthalmology consent status | invariant | Status confirms required consent for imaging, procedure, dilation or surgery-related care. | permission evidence |
| eyeclinic.testing.refraction_workup | Refraction workup handoff | variant | Handoff sends measurement results, patient goals and lens history to clinician. | optical workflow |
| eyeclinic.testing.iop_measurement | Intraocular pressure measurement | invariant | Measurement records pressure result, method, time and eye. | monitoring datum |
| eyeclinic.testing.visual_field | Visual field test | variant | Test maps patient response across field of vision using defined protocol. | functional map |
| eyeclinic.testing.color_vision | Color vision test | variant | Test screens color discrimination using standardized plates or device. | specific function |
| eyeclinic.testing.pachymetry | Corneal thickness measurement | variant | Measurement records corneal thickness when needed for diagnosis or planning context. | structural datum |
| eyeclinic.imaging.oct_scan | OCT scan workflow | variant | Workflow captures optical coherence images with eye, scan type, quality and storage. | retinal or nerve image |
| eyeclinic.imaging.fundus_photo | Fundus photo workflow | variant | Photo captures retina images with laterality, field, quality and comparison tags. | document appearance |
| eyeclinic.imaging.topography | Corneal topography workflow | variant | Workflow maps corneal shape and stores quality-controlled image for clinician review. | shape data |
| eyeclinic.imaging.image_quality | Eye image quality check | invariant | Check flags blur, artifact, wrong eye, poor fixation or incomplete scan. | usable images |
| eyeclinic.imaging.image_handoff | Imaging handoff | invariant | Handoff ensures clinician can find images, timestamps, eye labels and technician notes. | no lost tests |
| eyeclinic.flow.technician_rooming | Ophthalmic technician rooming | invariant | Rooming prepares history, acuity, preliminary tests, drops and equipment before clinician. | efficient exam |
| eyeclinic.flow.drop_administration_log | Eye drop administration log | invariant | Log records drop type, eye, time, staff and patient reaction if relevant. | timing and safety |
| eyeclinic.flow.room_turnover | Eye exam room turnover | invariant | Turnover cleans surfaces, resets equipment, disposes supplies and protects instruments. | infection control |
| eyeclinic.flow.patient_education_packet | Patient education packet | variant | Packet gives approved instructions, procedure info or lens guidance from clinic materials. | consistent communication |
| eyeclinic.flow.checkout_orders | Eye clinic checkout orders | invariant | Checkout schedules follow-up, testing, prescriptions, referrals or procedure dates from clinician plan. | close loop |
| eyeclinic.procedure.laser_room_setup | Ophthalmology laser room setup | variant | Setup verifies equipment, lens, consent, eye, staff, safety signs and documentation. | procedure readiness |
| eyeclinic.procedure.injection_flow | Intravitreal injection flow | variant | Flow coordinates consent, medication handling, sterile setup, timeout, documentation and follow-up. | controlled procedure |
| eyeclinic.procedure.timeout | Ophthalmology procedure timeout | invariant | Timeout confirms patient, procedure, eye, consent, medication or device and allergies. | wrong-site prevention |
| eyeclinic.procedure.instrument_trace | Ophthalmology instrument trace | invariant | Trace links reusable instruments to sterilization cycle, procedure and patient where required. | infection traceability |
| eyeclinic.procedure.postprocedure_note | Post-procedure note | invariant | Note records procedure completion, tolerance, instructions, lot numbers if needed and follow-up. | close procedure |
| eyeclinic.optical.frame_selection | Optical frame selection | variant | Selection records frame, size, fit, price, insurance and patient preference. | optical retail |
| eyeclinic.optical.lens_order | Lens order | variant | Order captures prescription, lens type, coating, measurements, frame and lab route. | make glasses |
| eyeclinic.optical.pupillary_distance | Pupillary distance measurement | variant | Measurement supports accurate lens fabrication and fitting. | align optics |
| eyeclinic.optical.order_verification | Optical order verification | invariant | Verification checks prescription, lens, frame, measurements, price and patient approval before lab order. | avoid remake |
| eyeclinic.optical.dispensing_adjustment | Glasses dispensing adjustment | variant | Adjustment fits frame, confirms vision, comfort and patient instructions at pickup. | usable eyewear |
| eyeclinic.records.eye_diagram | Eye diagram documentation | variant | Diagram marks lesion, finding, procedure site or observation with laterality. | visual record |
| eyeclinic.records.referral_letter | Ophthalmology referral letter | invariant | Letter communicates reason, findings, tests, urgency and requested action to another provider. | care handoff |
| eyeclinic.records.surgery_packet | Eye surgery packet | variant | Packet compiles clearance, measurements, consent, lens choice, medications and scheduling details. | surgery readiness |
| eyeclinic.records.device_lot | Ophthalmology device lot record | variant | Record tracks lens, implant, medication or supply lot when procedure traceability is required. | recall support |
| eyeclinic.records.privacy_screen | Eye clinic privacy screen | invariant | Screen limits visible images, charts and conversations in high-flow testing areas. | protect patient data |
| eyeclinic.quality.no_show_recall | Eye clinic no-show recall | invariant | Recall workflow follows up missed high-risk monitoring, post-op or procedure appointments. | avoid care gaps |
| eyeclinic.quality.equipment_qc | Ophthalmic equipment QC | invariant | QC checks calibration, cleaning, software, image quality and service status. | reliable testing |
| eyeclinic.quality.incident_report | Eye clinic incident report | invariant | Report documents fall, wrong-eye risk, drop reaction, equipment issue, privacy event or complaint. | safety learning |
| eyeclinic.metrics.eyeclinic_kpi | Ophthalmology clinic KPI | variant | KPI tracks wait time, imaging defects, recall completion, room utilization, no-shows and procedure flow. | manage clinic |
