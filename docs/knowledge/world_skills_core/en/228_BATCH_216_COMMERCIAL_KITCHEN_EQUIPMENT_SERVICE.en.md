# BATCH_216 — Commercial Kitchen Equipment Service Detail
# world_skills_core · source: world_skills_core:batch_216:commercial_kitchen_equipment_service
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| kitchsvc.intake.service_call | Kitchen equipment service call | invariant | Call records equipment, symptom, location, urgency, warranty, access and foodservice impact. | open service job |
| kitchsvc.intake.asset_tag | Kitchen equipment asset tag | invariant | Tag links unit to model, serial, owner, location, warranty and service history. | identify exact unit |
| kitchsvc.intake.symptom_category | Equipment symptom category | invariant | Category groups no heat, no power, leak, poor temperature, noise, ignition or control fault. | dispatch skill |
| kitchsvc.intake.priority_level | Kitchen service priority | variant | Priority reflects safety, refrigeration loss, production outage, health risk or SLA. | triage work |
| kitchsvc.intake.previsit_instruction | Previsit instruction | invariant | Instruction asks customer to clear access, stop unsafe use or preserve error conditions. | technician readiness |
| kitchsvc.dispatch.technician_assignment | Kitchen service technician assignment | invariant | Assignment matches gas, refrigeration, electrical, steam or warewash skill to call. | right expertise |
| kitchsvc.dispatch.parts_preload | Parts preload | variant | Preload sends likely igniters, probes, gaskets, pumps or controls based on symptom. | improve first fix |
| kitchsvc.dispatch.site_access | Kitchen site access | invariant | Access notes delivery dock, kitchen hours, contact, security, parking and after-hours rules. | reach equipment |
| kitchsvc.dispatch.foodservice_window | Foodservice work window | variant | Window avoids peak meal production when possible. | reduce disruption |
| kitchsvc.dispatch.no_service_condition | No-service condition | invariant | Condition records unsafe site, inaccessible unit, missing authorization or unavailable contact. | explain stop |
| kitchsvc.safety.gas_safety_check | Gas equipment safety check | variant | Check covers shutoff, odor, ventilation, combustion area and qualified scope. | gas risk control |
| kitchsvc.safety.electrical_lockout | Kitchen electrical lockout | invariant | Lockout isolates power before exposure to hazardous components. | technician safety |
| kitchsvc.safety.hot_surface | Hot surface control | invariant | Control manages burns from ovens, fryers, grills, steamers or hot liquids. | avoid injury |
| kitchsvc.safety.refrigerant_boundary | Refrigerant handling boundary | variant | Boundary limits sealed-system work to qualified staff and approved recovery process. | compliance |
| kitchsvc.safety.food_contact_safety | Food-contact safety | invariant | Safety prevents tools, chemicals, debris or lubricants from contaminating food-contact surfaces. | protect food |
| kitchsvc.diagnostic.visual_inspection | Kitchen equipment visual inspection | invariant | Inspection checks installation, damage, cleanliness, airflow, water, power, gas and controls. | first evidence |
| kitchsvc.diagnostic.error_code | Kitchen equipment error code | variant | Code points to possible fault but must be verified by test and context. | diagnostic clue |
| kitchsvc.diagnostic.temperature_test | Equipment temperature test | invariant | Test measures actual heating, cooling or holding performance against expected operation. | verify symptom |
| kitchsvc.diagnostic.leak_check | Kitchen equipment leak check | invariant | Check looks for water, gas, steam, oil or refrigerant-related leak signs within scope. | containment |
| kitchsvc.diagnostic.cycle_observation | Equipment cycle observation | variant | Observation watches ignition, compressor, pump, fan, timer, drain or control sequence. | see failure happen |
| kitchsvc.repair.repair_estimate | Commercial kitchen repair estimate | invariant | Estimate lists diagnosis, parts, labor, downtime, risk and customer approval. | informed choice |
| kitchsvc.repair.part_replacement | Kitchen equipment part replacement | invariant | Replacement follows manufacturer procedure and verifies compatibility. | restore function |
| kitchsvc.repair.gasket_repair | Door gasket repair | variant | Repair fixes seal, alignment and cleaning issue on refrigeration, oven or warmer doors. | efficiency and temperature |
| kitchsvc.repair.burner_service | Burner service | variant | Service cleans, adjusts or repairs burner components within qualified gas procedure. | reliable heat |
| kitchsvc.repair.pump_service | Pump service | variant | Service addresses warewasher, ice machine, drain or circulation pump issue. | water movement |
| kitchsvc.test.post_repair_test | Kitchen post-repair test | invariant | Test confirms unit starts, cycles, reaches performance target and no obvious leaks remain. | prove repair |
| kitchsvc.test.safety_device_test | Kitchen safety device test | invariant | Test verifies interlocks, limits, flame safeguard, guards or shutoffs as applicable. | safe release |
| kitchsvc.test.sanitation_return | Sanitation return check | invariant | Check leaves food-contact and work areas clean after service. | kitchen can resume |
| kitchsvc.test.customer_demo | Kitchen equipment customer demo | variant | Demo shows repaired function, basic care and warning signs to staff. | reduce callbacks |
| kitchsvc.test.return_to_service | Return-to-service release | invariant | Release records unit condition, test result, restrictions and customer acceptance. | operational handoff |
| kitchsvc.pm.pm_schedule | Kitchen equipment PM schedule | invariant | Schedule sets cleaning, inspection, calibration, lubrication, filters and safety checks. | prevent outage |
| kitchsvc.pm.filter_cleaning | Filter cleaning task | variant | Task covers hood, fryer, ice, refrigeration or water filter condition where applicable. | performance depends on flow |
| kitchsvc.pm.scale_control | Scale control | variant | Control manages mineral buildup in steamers, dish machines, coffee and ice equipment. | water chemistry |
| kitchsvc.pm.belt_fan_check | Belt and fan check | variant | Check verifies airflow components, tension, noise and bearing condition. | heat transfer |
| kitchsvc.pm.pm_report | Kitchen PM report | invariant | Report lists findings, work done, parts used, risks and recommendations. | maintenance evidence |
| kitchsvc.parts.part_identification | Kitchen service part identification | invariant | Identification matches model, serial, revision, voltage, gas type and manufacturer part. | avoid wrong part |
| kitchsvc.parts.emergency_part | Emergency part sourcing | variant | Sourcing finds critical part for production-down equipment through approved channel. | reduce downtime |
| kitchsvc.parts.warranty_part | Warranty part claim | variant | Claim documents failed part, install date, diagnosis and manufacturer return requirement. | recover cost |
| kitchsvc.parts.van_stock | Kitchen service van stock | variant | Stock includes common gaskets, igniters, probes, switches, hoses, fittings and hardware. | faster repair |
| kitchsvc.parts.obsolete_part | Obsolete part path | invariant | Path documents no-longer-available part, substitute, rebuild or replacement recommendation. | honest next step |
| kitchsvc.records.service_note | Kitchen service note | invariant | Note captures diagnosis, safety checks, repair, tests, parts, photos and restrictions. | job memory |
| kitchsvc.records.maintenance_contract | Maintenance contract record | variant | Record defines covered equipment, PM frequency, response terms, exclusions and price. | recurring service |
| kitchsvc.metrics.kitchen_service_kpi | Kitchen service KPI | variant | KPI tracks response time, first-fix rate, callbacks, downtime, parts delay and contract compliance. | manage service |
| kitchsvc.continuity.critical_equipment_outage | Critical kitchen equipment outage | invariant | Outage plan communicates downtime, workaround, parts ETA and foodservice risk. | keep kitchen informed |
