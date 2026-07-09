# BATCH_205 — Pest Control Service Operations Detail
# world_skills_core · source: world_skills_core:batch_205:pest_control_service_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| pestops.intake.service_request | Pest control service request | invariant | Request records pest concern, site, contact, access, urgency, pets, children and prior treatment. | start safely |
| pestops.intake.pest_sighting | Pest sighting record | invariant | Record captures pest type, location, time, quantity, evidence and customer photo if available. | direct inspection |
| pestops.intake.property_profile | Pest property profile | invariant | Profile lists structure type, rooms, exterior zones, sanitation issues and sensitive areas. | know environment |
| pestops.intake.service_agreement | Pest service agreement | invariant | Agreement defines scope, frequency, target pests, exclusions, price and safety responsibilities. | clear service |
| pestops.intake.notification_requirement | Treatment notification requirement | variant | Requirement defines tenant, neighbor, staff or occupant notices before service. | communication duty |
| pestops.inspect.site_inspection | Pest site inspection | invariant | Inspection checks entry points, food, moisture, harborages, droppings, nests and activity. | diagnose conditions |
| pestops.inspect.pest_identification | Pest identification | invariant | Identification distinguishes species or pest group to choose suitable control approach. | wrong ID wastes treatment |
| pestops.inspect.conducive_condition | Conducive condition | invariant | Condition such as moisture, clutter, gaps or food supports pest activity. | fix root cause |
| pestops.inspect.exclusion_gap | Pest exclusion gap | invariant | Gap is opening or defect allowing pest entry or movement. | physical control |
| pestops.inspect.monitoring_device | Monitoring device | variant | Device detects activity using trap, bait station, glue board or sensor. | evidence over guess |
| pestops.plan.treatment_plan | Pest treatment plan | invariant | Plan states target pest, areas, method, product or nonchemical controls and follow-up. | structured response |
| pestops.plan.integrated_pest_management | Integrated pest management | invariant | IPM combines inspection, sanitation, exclusion, monitoring and targeted treatment. | reduce overuse |
| pestops.plan.threshold | Pest action threshold | variant | Threshold defines activity level that triggers treatment or escalation. | proportional response |
| pestops.plan.customer_preparation | Customer preparation instruction | invariant | Instruction tells occupant what to clean, move, protect, remove or avoid before service. | treatment readiness |
| pestops.plan.sensitive_site | Sensitive site flag | variant | Flag marks daycare, food plant, healthcare, water, animals, pollinators or protected area. | extra caution |
| pestops.chemical.product_label | Pesticide label | invariant | Label defines legal use, target pests, dosage, PPE, site, restrictions and warnings. | label is control |
| pestops.chemical.mix_log | Chemical mix log | invariant | Log records product, amount, dilution, applicator, site, time and target. | trace application |
| pestops.chemical.ppe_requirement | Pest control PPE requirement | invariant | Requirement follows label, task, product and exposure risk. | worker safety |
| pestops.chemical.storage_control | Pesticide storage control | invariant | Control separates, secures, labels and contains products according to hazard and rule. | prevent exposure |
| pestops.chemical.spill_response | Pesticide spill response | invariant | Response isolates area, uses kit, protects people, contains product and documents event. | emergency readiness |
| pestops.method.bait_station | Bait station service | variant | Service checks placement, condition, consumption, security, labeling and replenishment. | controlled bait use |
| pestops.method.trap_placement | Trap placement | variant | Placement considers pest travel paths, safety, access, non-target risk and inspection schedule. | catch effectively |
| pestops.method.exclusion_work | Exclusion work | variant | Work seals gaps, screens vents, repairs sweeps or blocks access points. | physical prevention |
| pestops.method.sanitation_recommendation | Sanitation recommendation | invariant | Recommendation targets food, waste, clutter, grease, moisture or storage practices. | customer part |
| pestops.method.heat_treatment | Heat treatment | variant | Treatment uses controlled heat process with monitoring and safety planning where appropriate. | nonchemical option |
| pestops.route.route_schedule | Pest route schedule | invariant | Schedule groups customers by geography, contract frequency, prep readiness and urgency. | efficient service |
| pestops.route.vehicle_inventory | Pest vehicle inventory | invariant | Inventory tracks products, traps, PPE, tools, labels, SDS and spill kit. | ready truck |
| pestops.route.access_issue | Pest access issue | invariant | Issue records locked gate, absent customer, unsafe area, animal, weather or denied entry. | explain missed work |
| pestops.route.weather_limit | Pest weather limit | variant | Limit stops or changes exterior treatment during wind, rain, heat or freezing conditions. | protect environment |
| pestops.route.service_window | Pest service window | invariant | Window communicates expected technician arrival and required occupant action. | customer planning |
| pestops.records.service_report | Pest service report | invariant | Report lists findings, actions, products, locations, recommendations, restrictions and next visit. | service evidence |
| pestops.records.site_map | Pest site map | variant | Map marks stations, traps, hotspots, entry points and restricted zones. | repeatable route |
| pestops.records.sds_access | Safety data sheet access | invariant | Access provides chemical hazard and response information to workers and customers where required. | informed safety |
| pestops.records.regulatory_log | Pest regulatory log | invariant | Log supports required application, product, license, customer and notification records. | compliance |
| pestops.records.photo_evidence | Pest photo evidence | variant | Photos document damage, droppings, devices, conditions or completed exclusion. | visual proof |
| pestops.followup.followup_visit | Pest follow-up visit | invariant | Visit checks activity after treatment, customer actions, device results and next steps. | verify effect |
| pestops.followup.reinfestation | Reinfestation note | variant | Note distinguishes new entry, survival, neighboring source or incomplete control. | choose response |
| pestops.followup.customer_education | Pest customer education | invariant | Education explains prevention, sanitation, storage, moisture and monitoring responsibilities. | long-term control |
| pestops.followup.escalation | Pest escalation | invariant | Escalation involves supervisor, alternative method, structural repair or specialist. | solve persistent issue |
| pestops.followup.closure_criteria | Pest closure criteria | variant | Criteria define when activity is controlled enough to close case or reduce service. | avoid endless work |
| pestops.safety.non_target_risk | Non-target risk | invariant | Risk covers people, pets, wildlife, pollinators, food, water and sensitive surfaces. | avoid collateral harm |
| pestops.safety.license_record | Applicator license record | invariant | Record tracks technician certification, categories, expiration and continuing education. | legal applicator |
| pestops.metrics.pest_kpi | Pest control KPI | variant | KPI tracks callbacks, activity trends, route completion, product use, safety events and retention. | manage service |
| pestops.continuity.outbreak_response | Pest outbreak response | invariant | Response prioritizes severe infestation, communication, staffing, supplies and repeated monitoring. | handle surge |
