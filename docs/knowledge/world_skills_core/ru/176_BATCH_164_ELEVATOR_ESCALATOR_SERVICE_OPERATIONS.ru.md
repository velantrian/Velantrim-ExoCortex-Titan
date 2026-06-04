# BATCH_164 — Elevator & Escalator Service Operations Detail
# world_skills_core · source: world_skills_core:batch_164:elevator_escalator_service_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| elevops.service.unit_register | Lift unit register | invariant | Unit register links elevator or escalator identity, location, type, controller, duty and service contract. | знать обслуживаемый актив |
| elevops.service.maintenance_route | Maintenance route | variant | Route groups units by geography, criticality, service interval, access and technician capacity. | technician day planning |
| elevops.service.pm_interval | Preventive maintenance interval | invariant | PM interval defines planned service frequency based on equipment, usage, risk and contract. | prevent failure |
| elevops.service.service_log | Elevator service log | invariant | Service log records visit date, checks, findings, adjustments, parts, safety issues and technician. | asset memory |
| elevops.service.callback | Callback | invariant | Callback is an unplanned service request after fault, complaint, shutdown or malfunction. | reactive workload |
| elevops.service.repeat_callback | Repeat callback | invariant | Repeat callback indicates unresolved root cause, poor repair, misuse, environment or aging component. | signal of deeper issue |
| elevops.safety.lockout | Lift lockout | invariant | Lockout controls hazardous energy and movement before maintenance or inspection work. | protect technician |
| elevops.safety.barricade | Public barricade | invariant | Barricade keeps passengers away from open shafts, stopped escalators or service work areas. | separate public from hazard |
| elevops.safety.pit_access | Elevator pit access | invariant | Pit access requires controlled entry, stop switch, lighting, communication and hazard awareness. | bottom of shaft risk |
| elevops.safety.machine_room_access | Machine room access | invariant | Machine room access must be controlled because equipment contains electrical, mechanical and rescue-critical systems. | restricted technical room |
| elevops.safety.escalator_combplate | Escalator combplate hazard | invariant | Combplate area can trap objects or footwear and must be inspected for damage, alignment and debris. | passenger injury point |
| elevops.safety.overspeed_governor | Overspeed governor | invariant | Overspeed governor is safety device that detects excessive elevator speed and triggers protective action. | critical safety layer |
| elevops.inspection.door_operation | Door operation check | invariant | Door checks verify reopening, force, sensors, timing, alignment and obstruction response. | doors cause many incidents |
| elevops.inspection.leveling_accuracy | Leveling accuracy | invariant | Leveling accuracy measures how well elevator floor aligns with landing to reduce trip risk. | small height matters |
| elevops.inspection.brake_test | Elevator brake test | invariant | Brake testing confirms ability to hold or stop car according to required conditions. | controlled stopping |
| elevops.inspection.ride_quality | Ride quality | variant | Ride quality reflects vibration, noise, acceleration, stopping and passenger comfort. | experience plus diagnostics |
| elevops.inspection.emergency_phone | Emergency phone check | invariant | Emergency communication must connect trapped passengers with response service or building staff. | voice during entrapment |
| elevops.inspection.fire_service | Fire service operation | invariant | Fire service mode changes elevator behavior for recall and firefighter use according to local requirements. | life safety interface |
| elevops.entrapment.entrapment_call | Entrapment call | invariant | Entrapment call reports passengers trapped and requires priority response, communication and safe release. | people inside first |
| elevops.entrapment.passenger_communication | Passenger communication | invariant | Communication reassures trapped passengers, gathers condition, prevents unsafe self-rescue and updates ETA. | reduce panic |
| elevops.entrapment.rescue_authorization | Rescue authorization | invariant | Rescue must be performed by authorized trained personnel using approved procedure for equipment state. | no improvisation |
| elevops.entrapment.post_entrapment_check | Post-entrapment check | invariant | After entrapment, unit needs inspection before return to service to identify cause and safety status. | do not restart blindly |
| elevops.entrapment.incident_report | Entrapment incident report | invariant | Report records timeline, passengers, fault, rescue actions, injuries, communications and corrective actions. | evidence and learning |
| elevops.parts.spare_part_identification | Spare part identification | invariant | Correct part identification uses model, serial, controller, revision, dimensions and supplier compatibility. | wrong part delays repair |
| elevops.parts.obsolete_part | Obsolete part | variant | Obsolete part requires substitution, refurbishment, modernization or longer lead time planning. | aging equipment risk |
| elevops.parts.critical_spares | Critical spares | variant | Critical spares reduce downtime for high-use or critical units when failure probability and lead time justify stock. | resilience inventory |
| elevops.parts.parts_traceability | Lift parts traceability | invariant | Traceability links installed part to unit, date, technician, batch or supplier. | service evidence |
| elevops.parts.returned_part_analysis | Returned part analysis | variant | Analysis of replaced parts can reveal root cause, wear pattern, misuse or supplier issue. | learn from failures |
| elevops.escalator.step_chain | Escalator step chain | invariant | Step chain moves escalator steps and requires inspection for wear, tension, lubrication and alignment. | core moving system |
| elevops.escalator.handrail_speed | Handrail speed check | invariant | Handrail speed should match step speed within allowed tolerance to reduce passenger imbalance. | hands and feet align |
| elevops.escalator.skirt_gap | Escalator skirt gap | invariant | Skirt gap and brushes reduce entrapment risk between step and side panel. | side hazard |
| elevops.escalator.step_demarcation | Step demarcation | invariant | Demarcation lines help passengers see step edges and transition zones. | visual safety cue |
| elevops.escalator.shutdown_reset | Escalator shutdown reset | variant | Reset after stop requires checking cause, area, passengers, faults and safety devices before restart. | restart with awareness |
| elevops.modernization.modernization_trigger | Modernization trigger | variant | Modernization may be triggered by reliability, code, energy, parts obsolescence, capacity or tenant expectations. | replace before crisis |
| elevops.modernization.controller_upgrade | Controller upgrade | variant | Controller upgrade changes dispatch, diagnostics, safety interfaces and service practices. | brain of lift |
| elevops.modernization.door_operator_upgrade | Door operator upgrade | variant | Door operator modernization can reduce faults, improve safety sensing and speed passenger flow. | doors are bottleneck |
| elevops.modernization.energy_recovery | Elevator energy recovery | variant | Energy recovery systems can return braking energy where usage pattern and electrical design support it. | efficiency option |
| elevops.contract.response_time | Service response time | invariant | Response time defines how quickly service provider must attend breakdown, entrapment or callback. | SLA for mobility |
| elevops.contract.uptime_metric | Elevator uptime metric | invariant | Uptime measures availability but should be interpreted with shutdown reasons, planned maintenance and usage. | availability context |
| elevops.contract.third_party_inspection | Third-party inspection | invariant | Independent inspection verifies safety, code compliance and condition outside routine maintenance. | external assurance |
| elevops.contract.deficiency_notice | Deficiency notice | invariant | Deficiency notice records safety or compliance issue requiring correction by responsible party. | formal gap |
| elevops.contract.shutdown_decision | Unit shutdown decision | invariant | Shutdown decision removes equipment from service when safety, code, fault or risk requires it. | stop unsafe unit |
| elevops.records.certificate_status | Lift certificate status | invariant | Certificate status tracks whether unit has required approvals, inspections and expiry dates. | legal operation |
| elevops.records.callback_analysis | Callback analysis | invariant | Callback analysis groups faults by unit, component, time, technician and root cause. | reliability improvement |
