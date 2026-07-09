# BATCH_201 — Landscaping Service Operations Detail
# world_skills_core · source: world_skills_core:batch_201:landscaping_service_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| landscape.sales.site_visit | Landscaping site visit | invariant | Visit records property size, access, slopes, plantings, irrigation, hazards and client goals. | understand site |
| landscape.sales.scope_estimate | Landscaping scope estimate | invariant | Estimate defines tasks, frequency, materials, labor, equipment, disposal and exclusions. | price the work |
| landscape.sales.service_contract | Landscape service contract | invariant | Contract sets schedule, scope, price, weather rules, change orders and client responsibilities. | stable agreement |
| landscape.sales.seasonal_plan | Seasonal landscape plan | variant | Plan adapts services for spring cleanup, growing season, leaf fall, winter or drought. | work follows season |
| landscape.sales.property_map | Landscape property map | variant | Map marks turf, beds, trees, irrigation zones, utilities, gates and no-service areas. | crew orientation |
| landscape.crew.route_schedule | Landscape route schedule | invariant | Schedule orders sites by geography, service window, crew, equipment and priority. | efficient day |
| landscape.crew.crew_briefing | Landscape crew briefing | invariant | Briefing covers tasks, hazards, weather, customer notes, equipment and expected hours. | start aligned |
| landscape.crew.time_capture | Landscaping time capture | invariant | Capture records crew arrival, departure, travel, task time and exceptions. | labor control |
| landscape.crew.client_access | Client access instruction | invariant | Instruction covers gates, pets, parking, water access, noise limits and restricted areas. | avoid friction |
| landscape.crew.service_photo | Landscape service photo | variant | Photo documents completed work, issue, damage, plant condition or before-after state. | remote evidence |
| landscape.mow.mowing_height | Mowing height | invariant | Height is set by turf type, season, weather and client preference. | avoid turf stress |
| landscape.mow.edging | Lawn edging | invariant | Edging defines clean boundary along walks, beds, curbs and drives. | finished look |
| landscape.mow.trimming | String trimming | invariant | Trimming cuts areas mowers cannot reach without damaging plants, bark or structures. | detail work |
| landscape.mow.clipping_management | Clipping management | variant | Clippings may be mulched, bagged or removed based on turf health and appearance. | manage residue |
| landscape.mow.turf_damage | Turf damage note | invariant | Note documents scalping, ruts, disease, drought, pests or equipment damage. | fix or prevent |
| landscape.plant.pruning_plan | Pruning plan | invariant | Plan defines plant, timing, objective, cut limits and debris handling. | prune with purpose |
| landscape.plant.shrub_shaping | Shrub shaping | variant | Shaping maintains appearance while avoiding excessive cutback or plant stress. | aesthetics and health |
| landscape.plant.tree_clearance | Tree clearance note | variant | Note flags branches near buildings, signs, wires, walkways or sightlines for proper service. | manage conflicts |
| landscape.plant.mulch_depth | Mulch depth | invariant | Depth affects moisture, weeds, roots and trunk rot risk. | not too much |
| landscape.plant.plant_replacement | Plant replacement | variant | Replacement records dead plant, warranty status, species, size, location and reason. | maintain design |
| landscape.irrigation.zone_check | Irrigation zone check | invariant | Check confirms heads, coverage, leaks, pressure, valves and controller schedule. | water where needed |
| landscape.irrigation.controller_schedule | Irrigation controller schedule | invariant | Schedule sets start times, duration, days and seasonal adjustment. | water control |
| landscape.irrigation.leak_report | Irrigation leak report | invariant | Report documents broken head, pipe leak, valve issue, wet area or water waste. | stop loss |
| landscape.irrigation.winterization | Irrigation winterization | variant | Winterization removes or protects water from system before freezing season. | prevent burst damage |
| landscape.irrigation.backflow_check | Backflow device check | variant | Check verifies required irrigation backflow protection status and inspection need. | protect water supply |
| landscape.safety.equipment_inspection | Landscape equipment inspection | invariant | Inspection checks blades, guards, fuel, leaks, tires, belts and safety controls. | safe equipment |
| landscape.safety.ppe_check | Landscape PPE check | invariant | Check verifies eye, hearing, gloves, footwear, sun and respiratory protection as needed. | worker protection |
| landscape.safety.utility_marking | Utility marking awareness | invariant | Awareness avoids digging or staking without utility location process. | prevent strikes |
| landscape.safety.chemical_handling | Landscape chemical handling | variant | Handling follows label, storage, PPE, mixing, application and notification requirements. | avoid exposure |
| landscape.safety.heat_stress | Heat stress procedure | invariant | Procedure covers hydration, breaks, shade, symptoms and escalation during hot work. | outdoor risk |
| landscape.materials.debris_disposal | Landscape debris disposal | invariant | Disposal manages grass, leaves, branches, soil, stone and waste by allowed route. | clean finish |
| landscape.materials.material_delivery | Landscape material delivery | variant | Delivery coordinates mulch, soil, plants, stone or sod quantity, placement and access. | material logistics |
| landscape.materials.tool_inventory | Landscape tool inventory | invariant | Inventory tracks mowers, trimmers, blowers, hand tools, fuel and spare parts. | avoid lost gear |
| landscape.materials.fuel_control | Landscape fuel control | invariant | Control manages fuel type, containers, storage, spill response and usage. | fire and cost risk |
| landscape.materials.equipment_maintenance | Landscape equipment maintenance | invariant | Maintenance covers blade sharpening, oil, filters, belts, batteries, tires and cleaning. | uptime |
| landscape.quality.service_checklist | Landscape service checklist | invariant | Checklist confirms tasks completed, gates closed, debris cleared and issues noted. | consistent service |
| landscape.quality.client_issue | Landscape client issue | invariant | Issue records complaint, missed task, damage, billing concern or special request. | service recovery |
| landscape.quality.property_damage | Landscape property damage | invariant | Damage record captures object, location, photos, cause, client notice and repair route. | accountability |
| landscape.quality.rework_order | Landscape rework order | variant | Order sends crew back to correct incomplete or defective service. | close quality gap |
| landscape.quality.season_review | Landscape season review | variant | Review evaluates contract fit, plant health, irrigation, client satisfaction and next-season needs. | improve account |
| landscape.billing.service_invoice | Landscape service invoice | invariant | Invoice links completed visits, contract items, extras, materials and taxes. | bill work done |
| landscape.billing.change_order | Landscape change order | invariant | Change order approves extra pruning, cleanup, planting, repair or material beyond contract. | control extras |
| landscape.metrics.landscape_kpi | Landscaping operations KPI | variant | KPI tracks route efficiency, rework, equipment downtime, complaints, margins and safety incidents. | manage crew business |
| landscape.continuity.weather_delay | Landscaping weather delay | invariant | Delay procedure reschedules work, informs clients and prioritizes weather-sensitive tasks. | weather drives work |
