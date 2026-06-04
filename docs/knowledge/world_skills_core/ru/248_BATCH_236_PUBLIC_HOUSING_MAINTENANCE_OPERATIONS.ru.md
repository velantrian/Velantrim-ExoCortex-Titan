# BATCH_236 — Public Housing Maintenance Operations Detail
# world_skills_core · source: world_skills_core:batch_236:public_housing_maintenance_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| housingops.intake.service_request | Public housing service request | invariant | Request records resident, unit, issue, contact, access permission and urgency. | start maintenance |
| housingops.intake.emergency_triage | Housing emergency triage | invariant | Triage separates life safety, loss of utilities, lockout, leak and routine work. | prioritize risk |
| housingops.intake.duplicate_check | Housing duplicate request check | invariant | Check links repeated calls to existing work order, resident and issue history. | avoid confusion |
| housingops.intake.language_support | Housing maintenance language support | variant | Support ensures resident can report issue, understand access and receive notices. | equitable service |
| housingops.intake.afterhours_call | Housing after-hours maintenance call | variant | Call captures emergency details, dispatch decision, contractor route and follow-up. | 24-hour response |
| housingops.workorder.work_order_create | Housing maintenance work order | invariant | Work order links asset, unit, priority, trade, parts, labor and due date. | control work |
| housingops.workorder.trade_assignment | Housing trade assignment | invariant | Assignment routes plumbing, electrical, HVAC, carpentry, pest, cleaning or grounds work. | right crew |
| housingops.workorder.sla_clock | Housing maintenance SLA clock | invariant | Clock tracks required response time by emergency, urgent or routine priority. | compliance |
| housingops.workorder.status_note | Housing work order status note | invariant | Note records attempted access, parts wait, vendor handoff, completion or deferral. | transparent progress |
| housingops.workorder.resident_confirmation | Housing resident completion confirmation | variant | Confirmation captures resident acceptance, unresolved issue or follow-up need. | close loop |
| housingops.access.entry_notice | Housing unit entry notice | invariant | Notice states date, window, reason, staff or vendor and resident rights. | lawful access |
| housingops.access.key_control | Housing maintenance key control | invariant | Control tracks key checkout, staff, unit, time, return and exception. | protect residents |
| housingops.access.no_access | Housing no-access record | invariant | Record documents missed appointment, notice, door tag, resident contact and reschedule. | evidence |
| housingops.access.occupied_unit_safety | Occupied unit work safety | invariant | Safety covers tools, dust, pets, children, belongings, privacy and cleanup. | respectful work |
| housingops.access.reasonable_accommodation | Housing maintenance accommodation | variant | Accommodation adjusts notice, communication, scheduling or access for resident need. | fair service |
| housingops.trades.plumbing_leak | Housing plumbing leak response | invariant | Response isolates leak, protects property, repairs source and documents damage. | stop damage |
| housingops.trades.electrical_fault | Housing electrical fault response | invariant | Response secures hazard, tests circuit, repairs approved components and documents safety. | prevent shock/fire |
| housingops.trades.hvac_outage | Housing HVAC outage response | invariant | Response records temperature, vulnerable residents, equipment status, repair and temporary measures. | habitability |
| housingops.trades.appliance_repair | Housing appliance repair | variant | Repair tracks appliance, symptom, part, warranty, replacement decision and resident notice. | restore function |
| housingops.trades.pest_workorder | Housing pest work order | invariant | Work order records pest type, prep instructions, treatment, follow-up and education. | control infestation |
| housingops.vendor.vendor_dispatch | Housing vendor dispatch | invariant | Dispatch sends scope, unit, access, insurance, safety rules and completion requirements. | controlled outsourcing |
| housingops.vendor.vendor_checkin | Housing vendor check-in | variant | Check-in verifies arrival, ID, scope, keys, resident contact and building rules. | site control |
| housingops.vendor.invoice_match | Housing vendor invoice match | invariant | Match compares invoice to work order, rates, completion proof and approvals. | payment control |
| housingops.vendor.warranty_callback | Housing warranty callback | variant | Callback routes repeat defect to vendor under warranty or workmanship review. | reduce cost |
| housingops.inspection.unit_inspection | Public housing unit inspection | invariant | Inspection records condition, safety, housekeeping, repairs, photos and notices. | asset oversight |
| housingops.inspection.moveout_inspection | Housing move-out inspection | invariant | Inspection captures damages, wear, cleaning, keys, charges and turnover tasks. | prepare unit |
| housingops.inspection.annual_inspection | Housing annual inspection | variant | Inspection reviews unit condition, health, safety, smoke detectors and resident issues. | compliance |
| housingops.inspection.quality_control | Housing repair quality control | invariant | Control checks completed work against scope, safety, cleanliness and resident impact. | workmanship |
| housingops.turnover.vacant_unit_scope | Vacant unit scope | invariant | Scope lists cleaning, paint, flooring, repairs, appliances, locks and inspection needs. | turn unit |
| housingops.turnover.lock_change | Housing lock change | invariant | Change records lockset, keys, unit status, staff, date and secure handoff. | security |
| housingops.turnover.make_ready_schedule | Housing make-ready schedule | variant | Schedule sequences trades, vendors, inspection and leasing deadline for vacant unit. | reduce vacancy |
| housingops.safety.smoke_detector_check | Housing smoke detector check | invariant | Check records device presence, test, battery, replacement and resident notice. | life safety |
| housingops.safety.mold_moisture | Housing mold and moisture response | invariant | Response investigates source, moisture, ventilation, cleaning, repair and follow-up. | health protection |
| housingops.safety.lead_safe_work | Housing lead-safe work control | invariant | Control applies trained methods, containment, notices and clearance where required. | protect residents |
| housingops.safety.incident_report | Housing maintenance incident report | invariant | Report covers injury, property damage, conflict, exposure, security or emergency. | incident trail |
| housingops.parts.parts_inventory | Housing maintenance parts inventory | invariant | Inventory tracks stock, reorder point, issue to work order and storage location. | faster repairs |
| housingops.parts.appliance_stock | Housing appliance stock | variant | Stock manages refrigerators, stoves, parts, serials, warranties and assignments. | replacement control |
| housingops.parts.tool_checkout | Housing maintenance tool checkout | invariant | Checkout records tool, staff, job, condition, return and damage. | asset control |
| housingops.reporting.backlog_report | Housing maintenance backlog report | invariant | Report summarizes open orders by priority, trade, age, building and cause. | manage workload |
| housingops.reporting.compliance_report | Housing maintenance compliance report | invariant | Report tracks emergency response, inspections, safety checks and overdue work. | oversight |
| housingops.resident.resident_notice | Housing resident maintenance notice | invariant | Notice communicates planned work, outage, entry, delay, preparation or completion. | clear communication |
| housingops.resident.complaint_escalation | Housing maintenance complaint escalation | variant | Escalation routes unresolved issue to supervisor, resident services or quality review. | restore trust |
| housingops.metrics.housing_kpi | Public housing maintenance KPI | variant | KPI tracks response time, backlog age, repeat repairs, no-access, vacancy days and complaints. | manage service |
| housingops.continuity.building_outage | Housing building outage response | invariant | Response coordinates water, heat, elevator, power or sewer outage communication and repair. | protect residents |
