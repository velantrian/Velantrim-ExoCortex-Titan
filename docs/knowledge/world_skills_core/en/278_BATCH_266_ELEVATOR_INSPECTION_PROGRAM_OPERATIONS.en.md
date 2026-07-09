# BATCH_266 — Elevator Inspection Program Operations Detail
# world_skills_core · source: world_skills_core:batch_266:elevator_inspection_program_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| elevatorops.inventory.unit_record | Elevator unit record | invariant | Record stores device ID, address, type, capacity, speed, owner and contractor. | asset registry |
| elevatorops.inventory.device_type | Elevator device type | invariant | Type identifies passenger, freight, escalator, platform lift, dumbwaiter or moving walk. | apply rules |
| elevatorops.inventory.status | Elevator status | invariant | Status tracks active, inactive, removed, under construction, violation, outage or certified. | program visibility |
| elevatorops.inventory.owner_contact | Elevator owner contact | invariant | Contact stores owner, manager, billing, emergency and contractor information. | communication |
| elevatorops.schedule.periodic_cycle | Elevator periodic inspection cycle | invariant | Cycle sets inspection frequency by device type, age, use, risk and rule. | plan inspections |
| elevatorops.schedule.test_due | Elevator test due date | invariant | Due date tracks annual, periodic, category, load, safety or acceptance tests. | avoid overdue |
| elevatorops.schedule.inspector_assignment | Elevator inspector assignment | invariant | Assignment links inspector, device, test type, route, access and due date. | organize work |
| elevatorops.schedule.contractor_coordination | Elevator contractor coordination | variant | Coordination schedules mechanic, keys, machine room, test weights and shutdown. | inspect safely |
| elevatorops.schedule.no_access | Elevator inspection no-access | invariant | Record captures locked room, no contractor, tenant issue, unsafe access or cancellation. | reschedule evidence |
| elevatorops.field.site_arrival | Elevator inspection site arrival | invariant | Arrival records device, address, contact, access, contractor, time and safety. | start visit |
| elevatorops.field.machine_room | Elevator machine room check | invariant | Check reviews access, lighting, storage, ventilation, labels, disconnects and housekeeping. | safe equipment room |
| elevatorops.field.pit_check | Elevator pit check | invariant | Check reviews ladder, lighting, water, debris, stop switch, clearance and hazards. | pit safety |
| elevatorops.field.car_check | Elevator car check | invariant | Check reviews doors, lighting, communication, capacity plate, controls and ride quality. | passenger safety |
| elevatorops.field.hoistway_check | Elevator hoistway check | invariant | Check reviews doors, locks, clearances, equipment, obstructions and condition. | shaft safety |
| elevatorops.test.safety_test | Elevator safety test | invariant | Test verifies safeties, governor, brake, buffers, limits or other required protections. | prevent failure |
| elevatorops.test.door_reversal | Elevator door reversal test | invariant | Test checks reopening device, force, timing, sensors and door operation. | prevent entrapment |
| elevatorops.test.emergency_phone | Elevator emergency communication test | invariant | Test verifies phone or communication device reaches monitored assistance with location. | trapped passenger aid |
| elevatorops.test.fire_service | Elevator fire service test | variant | Test checks recall, firefighter operation, indicators, keys and smoke control interface. | fire response |
| elevatorops.test.load_test | Elevator load test | variant | Test uses approved weight or method with contractor, safety zones and documentation. | verify capacity |
| elevatorops.violation.violation_code | Elevator violation code | invariant | Code links observed deficiency to rule, severity, deadline and required correction. | consistent enforcement |
| elevatorops.violation.immediate_hazard | Elevator immediate hazard | invariant | Hazard requires shutdown, barricade, lockout, emergency repair or restricted use. | prevent injury |
| elevatorops.violation.repeat_defect | Elevator repeat defect | variant | Defect repeats prior violation and may escalate enforcement or inspection frequency. | address pattern |
| elevatorops.order.shutdown_order | Elevator shutdown order | invariant | Order removes device from service and states conditions for return. | control unsafe device |
| elevatorops.order.correction_notice | Elevator correction notice | invariant | Notice lists defects, rule references, deadlines, owner duty and reinspection process. | guide correction |
| elevatorops.certificate.certificate_issue | Elevator certificate issue | invariant | Certificate records device, inspection, expiration, conditions and posting requirement. | authorize operation |
| elevatorops.certificate.expired_certificate | Expired elevator certificate | invariant | Record flags operation beyond certificate date and triggers notice or enforcement. | compliance |
| elevatorops.certificate.temporary_certificate | Temporary elevator certificate | variant | Certificate allows limited operation with conditions, deadline and pending correction. | controlled use |
| elevatorops.outage.outage_report | Elevator outage report | variant | Report captures device down, reason, trapped passenger, repair ETA and accessibility impact. | service awareness |
| elevatorops.outage.entrapment_response | Elevator entrapment response | invariant | Response coordinates emergency contact, contractor, fire service, documentation and follow-up. | trapped passenger safety |
| elevatorops.outage.accessibility_impact | Elevator accessibility impact | invariant | Impact record notes affected floors, alternative route, notification and duration. | protect access |
| elevatorops.records.inspection_report | Elevator inspection report | invariant | Report documents device, tests, findings, violations, photos, contractor and result. | official record |
| elevatorops.records.test_document | Elevator test document | invariant | Document stores contractor test forms, readings, weights, signatures and deficiencies. | proof |
| elevatorops.records.photo_log | Elevator inspection photo log | variant | Log links images to defect, location, device, date and inspector. | evidence |
| elevatorops.records.case_file | Elevator program case file | invariant | File stores inventory, reports, certificates, violations, orders, correspondence and closure. | device memory |
| elevatorops.billing.fee_assessment | Elevator inspection fee assessment | variant | Assessment records permit, inspection, certificate, reinspection or penalty fee. | program finance |
| elevatorops.billing.invoice_status | Elevator inspection invoice status | variant | Status tracks billed, paid, overdue, waived, disputed or refunded fees. | financial control |
| elevatorops.contractor.contractor_license | Elevator contractor license check | invariant | Check verifies contractor, mechanic credential, insurance and authorization status. | qualified work |
| elevatorops.contractor.repair_confirmation | Elevator repair confirmation | invariant | Confirmation records corrected item, contractor, date, parts, test and proof. | close violation |
| elevatorops.quality.supervisor_review | Elevator inspection supervisor review | invariant | Review checks shutdowns, violations, certificates, tests, fees and contested findings. | consistency |
| elevatorops.reporting.overdue_report | Elevator overdue inspection report | invariant | Report lists overdue inspections, tests, certificates, violations and owners. | manage backlog |
| elevatorops.metrics.elevator_kpi | Elevator inspection KPI | variant | KPI tracks overdue rate, shutdowns, violations, entrapments, certificates and reinspection pass rate. | manage program |
| elevatorops.continuity.inspector_shortage | Elevator inspector shortage plan | variant | Plan prioritizes high-risk devices, overdue certificates, complaints and contractor tests. | keep coverage |
| elevatorops.continuity.system_outage | Elevator program system outage | invariant | Outage uses paper reports, manual certificates, phone scheduling and later entry. | maintain program |
| elevatorops.close.case_closure | Elevator inspection case closure | invariant | Closure records certificate issued, violation corrected, device removed or enforcement complete. | end cycle |
