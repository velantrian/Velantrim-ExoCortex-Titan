# BATCH_222 — Crematory Operations Detail
# world_skills_core · source: world_skills_core:batch_222:crematory_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| crematory.case.case_intake | Crematory case intake | invariant | Intake records decedent, funeral home, authorization, permit, container and requested service. | open case |
| crematory.case.case_number | Crematory case number | invariant | Number uniquely links identity, documents, custody, retort cycle, processing and release. | trace everything |
| crematory.case.authorization_check | Cremation authorization check | invariant | Check verifies legal authorization, signatures, identification and required waiting or permit rules. | cannot proceed blindly |
| crematory.case.permit_check | Cremation permit check | invariant | Check confirms permit or medical examiner clearance where required before scheduling. | legal gate |
| crematory.case.special_instruction | Crematory special instruction | variant | Instruction may cover witness cremation, jewelry, container, return method or religious request. | honor wishes |
| crematory.custody.receipt_log | Crematory receipt log | invariant | Log records arrival, sender, staff, time, container, seals and condition. | custody starts |
| crematory.custody.identity_tag | Crematory identity tag | invariant | Tag links decedent and container to case number throughout facility movement. | prevent mix-up |
| crematory.custody.personal_effects | Personal effects handling | invariant | Handling records items removed, retained, cremated by authorization or returned. | protect property |
| crematory.custody.refrigeration_location | Refrigeration location | invariant | Location record tracks storage unit, shelf, time and case status before cremation. | controlled holding |
| crematory.custody.chain_transfer | Crematory chain transfer | invariant | Transfer records movement between receiving, holding, retort, processing and release. | continuous trace |
| crematory.schedule.retort_schedule | Retort schedule | invariant | Schedule assigns case, retort, date, operator, witness request and readiness status. | plan equipment |
| crematory.schedule.capacity_check | Crematory capacity check | invariant | Check compares case load, refrigeration, retort availability, staffing and permits. | avoid backlog |
| crematory.schedule.witness_appointment | Witness cremation appointment | variant | Appointment coordinates family, funeral home, timing, privacy, safety and viewing limits. | sensitive access |
| crematory.schedule.hold_status | Crematory hold status | invariant | Hold stops cremation due to missing document, dispute, permit, identification or instruction. | safe pause |
| crematory.schedule.priority_case | Priority cremation case | variant | Priority may apply to service date, shipment, family need or operational backlog. | schedule judgment |
| crematory.prep.container_check | Cremation container check | invariant | Check verifies container condition, identification, combustible compatibility and authorization. | retort readiness |
| crematory.prep.implant_device_check | Implant and device check | invariant | Check identifies devices or materials needing special handling before cremation. | safety and compliance |
| crematory.prep.jewelry_decision | Jewelry decision | variant | Decision records whether item is removed, returned or remains by authorization. | avoid dispute |
| crematory.prep.paperwork_match | Crematory paperwork match | invariant | Match confirms case tag, permit, authorization and schedule all refer to same decedent. | final gate |
| crematory.prep.operator_timeout | Crematory operator timeout | invariant | Timeout confirms identity, documents, retort, container and special instructions before start. | irreversible step |
| crematory.retort.start_record | Cremation start record | invariant | Record captures retort, operator, case, time, cycle and authorization readiness. | cycle evidence |
| crematory.retort.operating_parameter | Retort operating parameter | invariant | Parameter includes temperature, time, airflow or program settings within equipment procedure. | process control |
| crematory.retort.active_monitoring | Retort active monitoring | invariant | Monitoring observes equipment status, alarms, emissions controls and cycle progress. | do not walk away |
| crematory.retort.alarm_response | Retort alarm response | invariant | Response follows equipment procedure, safety controls, documentation and supervisor notice. | manage abnormal event |
| crematory.retort.cooldown | Cremation cooldown | invariant | Cooldown allows safe handling and protects equipment after cycle completion. | heat risk |
| crematory.processing.recovery | Cremated remains recovery | invariant | Recovery collects remains from retort with case identity maintained. | preserve identity |
| crematory.processing.metal_separation | Metal separation | variant | Separation removes noncombustible metal according to policy and authorization. | clean processing |
| crematory.processing.processor_use | Cremated remains processor use | invariant | Processor reduces remains to consistent form while maintaining case control. | final preparation |
| crematory.processing.container_fill | Temporary container fill | invariant | Fill places processed remains into labeled container with case and identity checks. | ready release |
| crematory.processing.processing_log | Crematory processing log | invariant | Log records recovery, processing, container, operator, time and exceptions. | audit trail |
| crematory.release.release_authorization | Cremated remains release authorization | invariant | Authorization defines who may receive remains and required identity proof. | controlled handoff |
| crematory.release.release_receipt | Cremated remains release receipt | invariant | Receipt records recipient, date, container, signatures and identification. | close custody |
| crematory.release.shipment | Cremated remains shipment | variant | Shipment follows packaging, carrier, tracking, permits and recipient confirmation. | remote return |
| crematory.release.hold_for_pickup | Hold for pickup | variant | Hold stores remains securely until authorized recipient arrives. | secure waiting |
| crematory.release.unclaimed_remains | Unclaimed remains process | invariant | Process tracks notices, storage, legal timeline and final disposition options. | respectful closure |
| crematory.maintenance.retort_maintenance | Retort maintenance | invariant | Maintenance covers refractory, burners, controls, seals, fans, sensors and service logs. | reliable equipment |
| crematory.maintenance.emissions_control | Emissions control check | invariant | Check verifies required filtration, monitoring, stack, opacity or permit-related controls. | environmental compliance |
| crematory.maintenance.housekeeping | Crematory housekeeping | invariant | Housekeeping removes dust, residue, packaging, tools and trip hazards in controlled areas. | safe facility |
| crematory.maintenance.instrument_calibration | Crematory instrument calibration | variant | Calibration tracks thermocouples, scales, monitors or other measurement devices. | trusted readings |
| crematory.maintenance.preventive_schedule | Crematory preventive schedule | invariant | Schedule sets inspection, cleaning, service, spare parts and downtime windows. | avoid failure |
| crematory.compliance.operator_training | Crematory operator training | invariant | Training covers identity, documents, retort operation, safety, emissions, dignity and emergency response. | competent operators |
| crematory.compliance.case_file_audit | Crematory case file audit | invariant | Audit checks authorization, permits, identity, logs, processing and release records. | compliance proof |
| crematory.metrics.crematory_kpi | Crematory KPI | variant | KPI tracks turnaround, holds, retort uptime, documentation errors, incidents and releases. | manage operation |
| crematory.continuity.retort_outage | Retort outage plan | invariant | Plan manages backlog, refrigeration, alternate facility, family communication and repair. | service continuity |
