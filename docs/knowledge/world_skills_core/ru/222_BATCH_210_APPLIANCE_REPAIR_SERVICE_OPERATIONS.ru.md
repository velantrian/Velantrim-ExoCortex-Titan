# BATCH_210 — Appliance Repair Service Operations Detail
# world_skills_core · source: world_skills_core:batch_210:appliance_repair_service_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| applrepair.intake.service_request | Appliance repair service request | invariant | Request records appliance, model, symptom, location, access, warranty and customer contact. | open job |
| applrepair.intake.model_serial | Model and serial capture | invariant | Capture identifies exact appliance version for parts, manuals and warranty checks. | right information |
| applrepair.intake.symptom_notes | Appliance symptom notes | invariant | Notes describe failure, noises, leaks, codes, timing and customer observations. | guide diagnosis |
| applrepair.intake.warranty_status | Appliance warranty status | variant | Status checks manufacturer, extended plan, labor, parts and authorization requirements. | billing path |
| applrepair.intake.safety_warning | Previsit safety warning | variant | Warning tells customer to stop using appliance when leak, smoke, shock, gas smell or overheating is reported. | reduce risk |
| applrepair.schedule.dispatch_slot | Appliance repair dispatch slot | invariant | Slot assigns technician, route, time window, skills, appliance type and parts. | schedule visit |
| applrepair.schedule.route_optimization | Repair route optimization | variant | Optimization groups calls by geography, parts availability, priority and appointment window. | reduce travel |
| applrepair.schedule.customer_confirmation | Appointment confirmation | invariant | Confirmation verifies address, availability, parking, appliance access and preparation. | avoid failed trip |
| applrepair.schedule.no_access | No-access visit | invariant | Record documents missed appointment, locked door, unsafe site or unavailable adult. | explain trip failure |
| applrepair.schedule.priority_repair | Priority repair | variant | Priority applies to safety, refrigeration failure, repeat call or contract SLA. | triage service |
| applrepair.diagnostic.visual_inspection | Appliance visual inspection | invariant | Inspection checks condition, installation, leaks, damage, power, ventilation and user controls. | first look |
| applrepair.diagnostic.error_code | Appliance error code | variant | Code provides manufacturer diagnostic clue but needs confirmation by testing. | clue, not proof |
| applrepair.diagnostic.power_check | Appliance power check | invariant | Check verifies outlet, breaker, cord, voltage suitability and control response where safe. | basic input |
| applrepair.diagnostic.water_leak_check | Appliance leak check | variant | Check examines hoses, valves, pumps, seals, drains, trays and installation. | contain water risk |
| applrepair.diagnostic.functional_test | Appliance functional test | invariant | Test runs appliance mode to observe symptom, cycle, sound, temperature or fault. | reproduce issue |
| applrepair.safety.lockout | Appliance service lockout | invariant | Lockout removes power, gas or water exposure before hazardous service work. | protect technician |
| applrepair.safety.gas_appliance_precaution | Gas appliance precaution | variant | Precaution checks shutoff, odor, ventilation, ignition risk and qualified scope. | high-risk system |
| applrepair.safety.refrigerant_boundary | Refrigerant service boundary | variant | Boundary limits sealed-system work to qualified technician and approved process. | compliance and safety |
| applrepair.safety.sharp_edge_ppe | Appliance sharp-edge PPE | invariant | PPE protects from sheet metal, glass, springs, motors and cramped spaces. | common injury risk |
| applrepair.safety.floor_protection | Customer floor protection | invariant | Protection uses mats, sliders or covers to avoid scratches, water and dirt. | respect home |
| applrepair.parts.part_identification | Appliance part identification | invariant | Identification matches part number, revision, compatibility and substitution rules. | avoid wrong part |
| applrepair.parts.truck_stock | Appliance truck stock | variant | Stock covers common parts, tools and consumables by appliance category. | first-visit fix |
| applrepair.parts.special_order | Special order part | invariant | Order records supplier, ETA, price, approval, deposit and return rule. | plan second visit |
| applrepair.parts.core_return | Core or defective part return | variant | Return sends replaced board, motor or compressor to supplier under warranty or rebuild process. | recover value |
| applrepair.parts.part_warranty | Part warranty record | invariant | Record tracks installed part, date, warranty period and claim evidence. | future coverage |
| applrepair.repair.repair_estimate | Appliance repair estimate | invariant | Estimate states diagnosis, parts, labor, taxes, risks and customer approval. | informed decision |
| applrepair.repair.customer_approval | Repair approval | invariant | Approval records customer consent to price, scope and parts before work proceeds. | avoid dispute |
| applrepair.repair.repair_note | Appliance repair note | invariant | Note documents diagnosis, replaced parts, tests, settings, observations and remaining issues. | service history |
| applrepair.repair.installation_correction | Installation correction | variant | Correction fixes leveling, venting, drain height, hose routing or clearance within scope. | many failures are setup |
| applrepair.repair.unrepairable_decision | Unrepairable decision | variant | Decision explains cost, part unavailability, unsafe condition or age making repair impractical. | honest closure |
| applrepair.test.post_repair_test | Post-repair test | invariant | Test confirms appliance operates, fault cleared, leaks absent and controls respond. | prove fix |
| applrepair.test.leak_recheck | Leak recheck | variant | Recheck observes water, gas or refrigerant risk after repair according to scope. | verify safety |
| applrepair.test.temperature_check | Appliance temperature check | variant | Check verifies cooling, heating or drying performance where relevant. | function evidence |
| applrepair.test.customer_demo | Customer demonstration | variant | Demo shows repaired function, maintenance advice and warning signs. | customer confidence |
| applrepair.test.repeat_call_flag | Repeat call flag | invariant | Flag identifies same symptom or related issue after recent service. | quality focus |
| applrepair.billing.invoice | Appliance repair invoice | invariant | Invoice lists trip, labor, parts, tax, discount, warranty coverage and payment. | close money |
| applrepair.billing.diagnostic_fee | Diagnostic fee | variant | Fee covers technician diagnosis and may apply to repair under policy. | price visit |
| applrepair.billing.warranty_claim | Appliance warranty claim | variant | Claim sends authorization, diagnosis, part, labor and proof to warranty payer. | recover cost |
| applrepair.billing.refund_adjustment | Repair refund or adjustment | variant | Adjustment corrects overcharge, failed repair, goodwill or warranty reversal. | service recovery |
| applrepair.customer.damage_claim | In-home damage claim | invariant | Claim records alleged property damage, photos, technician notes and resolution. | protect customer and firm |
| applrepair.customer.followup_call | Repair follow-up call | variant | Call checks performance, satisfaction and repeat symptoms after service. | quality loop |
| applrepair.admin.technician_training | Appliance technician training | invariant | Training covers electrical, gas, water, manufacturer procedures, documentation and customer conduct. | competent field work |
| applrepair.metrics.first_visit_completion | First-visit completion KPI | variant | KPI tracks jobs completed without return visit, missing part or repeat failure. | service effectiveness |
| applrepair.continuity.parts_shortage | Parts shortage procedure | invariant | Procedure communicates delay, alternatives, temporary safety advice and job status updates. | keep customer informed |
