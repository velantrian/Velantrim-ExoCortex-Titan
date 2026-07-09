# BATCH_232 — Vehicle Inspection Station Operations Detail
# world_skills_core · source: world_skills_core:batch_232:vehicle_inspection_station_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| inspectops.appointment.booking | Vehicle inspection appointment | invariant | Booking records vehicle, owner, inspection type, time, station and contact. | plan lane load |
| inspectops.appointment.walkin_queue | Inspection walk-in queue | variant | Queue orders unscheduled vehicles by arrival, capacity, priority and cutoff time. | manage demand |
| inspectops.appointment.reminder_notice | Inspection reminder notice | variant | Notice sends time, documents, fees, safety rules and reschedule path. | reduce no-shows |
| inspectops.appointment.no_show | Inspection no-show record | invariant | Record tracks missed slot, communication, fee if any and rebooking. | protect capacity |
| inspectops.intake.vehicle_identity | Vehicle identity check | invariant | Check verifies plate, VIN, registration and inspection category before testing. | right vehicle |
| inspectops.intake.document_review | Vehicle inspection document review | invariant | Review checks ownership, registration, prior failure, exemption or special authorization. | eligibility gate |
| inspectops.intake.fee_collection | Inspection fee collection | invariant | Collection records fee type, payment, receipt, waiver or refund. | financial trail |
| inspectops.intake.customer_disclosure | Inspection customer disclosure | invariant | Disclosure explains scope, pass/fail result, limits and dispute route. | clear expectations |
| inspectops.lane.lane_assignment | Inspection lane assignment | invariant | Assignment directs vehicle to lane by type, equipment, staffing and queue. | efficient flow |
| inspectops.lane.lane_safety_check | Inspection lane safety check | invariant | Check confirms ventilation, lifts, rollers, barriers, signage and pedestrian separation. | safe workspace |
| inspectops.lane.vehicle_positioning | Vehicle inspection positioning | invariant | Positioning places vehicle for brakes, emissions, lights or underbody checks. | test accuracy |
| inspectops.lane.stop_work_signal | Inspection stop-work signal | variant | Signal stops lane for unsafe vehicle condition, equipment fault or person in hazard zone. | prevent harm |
| inspectops.safety.lift_use | Inspection station lift use | variant | Use records lift points, weight limits, locking, spotter and lowering checks. | safe elevation |
| inspectops.safety.exhaust_ventilation | Inspection exhaust ventilation | invariant | Ventilation removes exhaust during idle, dynamometer or indoor running. | air safety |
| inspectops.safety.fire_readiness | Inspection station fire readiness | invariant | Readiness covers extinguishers, fuel leaks, hot surfaces, batteries and evacuation routes. | emergency readiness |
| inspectops.safety.ppe_requirement | Inspection PPE requirement | invariant | Requirement defines eye, hand, hearing, footwear or respiratory protection by task. | reduce injury |
| inspectops.checks.brake_test | Vehicle brake test workflow | variant | Workflow records method, equipment, readings, imbalance and pass/fail outcome. | braking evidence |
| inspectops.checks.light_check | Vehicle light check workflow | invariant | Workflow verifies required lights, signals, reflectors, brightness and mounting. | road visibility |
| inspectops.checks.tire_check | Vehicle tire check workflow | invariant | Workflow checks tread, damage, size, inflation and unsafe wear. | road safety |
| inspectops.checks.steering_suspension | Steering and suspension check | invariant | Check reviews looseness, leaks, mounts, joints and safety-critical damage. | mechanical safety |
| inspectops.checks.glass_mirror | Glass and mirror check | invariant | Check verifies windshield, mirrors, visibility, cracks and required equipment. | driver visibility |
| inspectops.checks.underbody_check | Vehicle underbody check | variant | Check reviews leaks, corrosion, loose components, exhaust mounting and visible damage. | hidden risk |
| inspectops.emissions.test_selection | Emissions test selection | variant | Selection chooses OBD, tailpipe, opacity or exemption path by vehicle rules. | proper test |
| inspectops.emissions.obd_connection | OBD emissions connection | variant | Connection records vehicle readiness, fault codes, communication and result. | electronic evidence |
| inspectops.emissions.analyzer_calibration | Emissions analyzer calibration | invariant | Calibration verifies gas, leak, zero/span or device readiness before testing. | reliable result |
| inspectops.emissions.failed_emissions | Failed emissions result | invariant | Result records pollutant or system failure, retest rule and customer notice. | compliance path |
| inspectops.emissions.exemption_review | Emissions exemption review | variant | Review confirms age, fuel, location, waiver or special status documentation. | correct exception |
| inspectops.result.pass_certificate | Inspection pass certificate | invariant | Certificate links vehicle, date, station, inspector, result and expiration. | proof of compliance |
| inspectops.result.failure_notice | Inspection failure notice | invariant | Notice lists failed items, severity, retest window, repair guidance and dispute path. | actionable result |
| inspectops.result.retest_record | Vehicle retest record | invariant | Record links previous failure, repairs claimed, retest scope, result and fee. | close failure |
| inspectops.result.sticker_control | Inspection sticker control | invariant | Control tracks sticker inventory, issue, voids, damaged stock and reconciliation. | prevent misuse |
| inspectops.result.data_upload | Inspection result data upload | invariant | Upload sends result to registry or authority with confirmation and error handling. | official record |
| inspectops.quality.inspector_credential | Vehicle inspector credential | invariant | Credential records training, authorization, expiration, scope and suspension status. | qualified staff |
| inspectops.quality.audit_sample | Inspection audit sample | variant | Sample reviews selected tests, video, data, certificates and inspector notes. | detect errors |
| inspectops.quality.equipment_maintenance | Inspection equipment maintenance | invariant | Maintenance tracks dyno, lift, analyzer, brake tester, cameras and calibration due dates. | equipment reliability |
| inspectops.quality.tamper_flag | Vehicle tamper flag | variant | Flag documents suspected odometer, emissions, VIN or equipment tampering for escalation. | integrity |
| inspectops.dispute.customer_dispute | Inspection customer dispute | invariant | Dispute records complaint, evidence, reviewer, decision and communication. | fair review |
| inspectops.dispute.second_opinion | Inspection second opinion | variant | Opinion routes vehicle to supervisor, referee station or independent review when allowed. | resolve uncertainty |
| inspectops.dispute.data_correction | Inspection data correction | invariant | Correction fixes plate, VIN, result or clerical error with authorization and audit trail. | accurate record |
| inspectops.close.lane_closeout | Inspection lane closeout | invariant | Closeout secures tools, equipment, stickers, cash, data uploads and waste. | end-day control |
| inspectops.close.waste_handling | Inspection station waste handling | variant | Handling manages fluids, filters, batteries, rags and hazardous waste containers. | environmental care |
| inspectops.close.daily_reconciliation | Inspection daily reconciliation | invariant | Reconciliation compares appointments, tests, fees, stickers, uploads and exceptions. | operational control |
| inspectops.metrics.station_kpi | Vehicle inspection station KPI | variant | KPI tracks throughput, pass rate, retests, equipment downtime, disputes and audit findings. | manage station |
| inspectops.continuity.system_outage | Inspection system outage | invariant | Outage plan records offline tests, paper controls, customer notices and later upload. | keep service safe |
