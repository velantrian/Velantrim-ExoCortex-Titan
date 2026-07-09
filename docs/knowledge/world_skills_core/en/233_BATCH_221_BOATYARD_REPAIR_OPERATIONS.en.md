# BATCH_221 — Boatyard Repair Operations Detail
# world_skills_core · source: world_skills_core:batch_221:boatyard_repair_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| boatyard.intake.work_request | Boatyard work request | invariant | Request records vessel, owner, service, haul date, symptoms, access and authorization. | open job |
| boatyard.intake.vessel_profile | Boatyard vessel profile | invariant | Profile stores length, beam, draft, weight, hull type, engines, insurance and contacts. | plan work |
| boatyard.intake.scope_estimate | Boatyard scope estimate | invariant | Estimate lists labor, parts, materials, haul, storage, environmental fees and assumptions. | price repair |
| boatyard.intake.owner_authorization | Boatyard owner authorization | invariant | Authorization permits haul-out, inspection, repair, storage, subcontract or change order. | permission |
| boatyard.intake.prehaul_condition | Pre-haul condition note | invariant | Note records hull, fittings, rigging, engines, electronics, gear and visible damage before lift. | baseline |
| boatyard.haul.haulout_schedule | Haul-out schedule | invariant | Schedule coordinates tide, lift, staff, slings, blocking area and owner contact. | move vessel safely |
| boatyard.haul.sling_plan | Boat sling plan | invariant | Plan identifies safe lifting points, appendages, weight and hull restrictions. | avoid crush damage |
| boatyard.haul.travel_lift_check | Travel lift check | invariant | Check verifies lift capacity, slings, tires, hydraulics, alarms and operator readiness. | heavy lift safety |
| boatyard.haul.pressure_wash | Hull pressure wash | variant | Wash removes marine growth while controlling runoff, debris and coating damage. | prepare inspection |
| boatyard.haul.launch_check | Vessel launch check | invariant | Check confirms plugs, seacocks, shaft, hull penetrations, bilge and leak watch before release. | safe return to water |
| boatyard.block.blocking_plan | Vessel blocking plan | invariant | Plan places stands, blocks, chains and pads to support hull shape and wind load. | stable storage |
| boatyard.block.stand_inspection | Boat stand inspection | invariant | Inspection checks threads, pads, chains, load, ground and corrosion. | prevent falls |
| boatyard.block.yard_location | Yard location assignment | invariant | Assignment places vessel by job type, utilities, access, crane needs and safety. | yard flow |
| boatyard.block.storm_tie_down | Storm tie-down | variant | Tie-down adds anchors, straps, stands and inspections before severe weather. | reduce storm loss |
| boatyard.block.access_ladder | Vessel access ladder | invariant | Ladder must be secured, appropriate height and safe for workers and owners. | fall prevention |
| boatyard.repair.hull_inspection | Hull inspection | invariant | Inspection checks blisters, cracks, delamination, impact, corrosion, through-hulls and coating. | find defects |
| boatyard.repair.fiberglass_repair | Fiberglass repair | variant | Repair prepares, laminates, cures, fairings and protects composite hull damage. | restore structure |
| boatyard.repair.gelcoat_repair | Gelcoat repair | variant | Repair matches color, fills, sands, buffs and seals cosmetic surface damage. | finish quality |
| boatyard.repair.metal_hull_repair | Metal hull repair | variant | Repair controls corrosion, welding, plating, coatings and isolation on metal vessels. | material-specific work |
| boatyard.repair.through_hull_service | Through-hull service | invariant | Service inspects, replaces, seals or tests fittings and valves below waterline. | critical leak path |
| boatyard.paint.bottom_paint_plan | Bottom paint plan | invariant | Plan selects coating, prep, compatibility, number of coats and environmental controls. | antifouling workflow |
| boatyard.paint.surface_prep | Boatyard surface prep | invariant | Prep removes growth, loose coating, contaminants and roughness before coating. | adhesion |
| boatyard.paint.masking | Hull masking | variant | Masking protects waterline, hardware, zincs, transducers, shafts and labels. | clean edges |
| boatyard.paint.cure_window | Marine coating cure window | invariant | Window defines time and conditions before launch or next coat. | coating performance |
| boatyard.paint.paint_log | Boatyard paint log | invariant | Log records product, batch, area, coats, weather, applicator and cure timing. | trace finish |
| boatyard.systems.engine_service | Boatyard engine service | variant | Service coordinates mechanical inspection, fluids, filters, belts, cooling or alignment work. | propulsion reliability |
| boatyard.systems.electrical_repair | Marine electrical repair | variant | Repair addresses batteries, shore power, wiring, panels, corrosion and circuit protection. | electrical reliability |
| boatyard.systems.plumbing_repair | Marine plumbing repair | variant | Repair handles bilge, freshwater, blackwater, pumps, hoses and valves. | onboard systems |
| boatyard.systems.rigging_check | Rigging check | variant | Check inspects standing or running rigging, terminals, lines, winches and mast fittings. | sailing safety |
| boatyard.systems.sea_trial | Sea trial | variant | Trial verifies repair under operating conditions with owner or technician notes. | prove function |
| boatyard.safety.hot_work_permit | Boatyard hot work permit | invariant | Permit controls welding, grinding or heat near fuel, paint, dust or confined areas. | fire control |
| boatyard.safety.confined_space | Vessel confined space | invariant | Space work needs ventilation, atmosphere awareness, communication and rescue planning. | high-risk work |
| boatyard.safety.environmental_containment | Boatyard environmental containment | invariant | Containment controls paint chips, dust, solvents, wash water and fuel spills. | protect water |
| boatyard.safety.ladder_scaffold | Yard ladder and scaffold safety | invariant | Safety checks setup, tie-off, surface, weather and access around vessels. | fall prevention |
| boatyard.safety.owner_yard_rules | Owner yard rules | invariant | Rules define PPE, access, DIY limits, pets, children, ladders and hazardous work. | shared yard safety |
| boatyard.parts.marine_parts_order | Marine parts order | invariant | Order records part, vessel, supplier, ETA, compatibility and approval. | supply repair |
| boatyard.parts.special_order_delay | Special order delay | variant | Delay affects schedule and requires owner update or alternate plan. | manage expectation |
| boatyard.parts.material_storage | Boatyard material storage | invariant | Storage controls paints, resins, solvents, batteries, hardware and flammables. | safe inventory |
| boatyard.admin.subcontractor_coordination | Boatyard subcontractor coordination | variant | Coordination controls outside riggers, mechanics, electricians, painters or surveyors working in yard. | align external work |
| boatyard.quality.work_order_closeout | Boatyard work order closeout | invariant | Closeout confirms tasks, tests, photos, cleanup, invoice and owner notes. | finish job |
| boatyard.quality.final_walkaround | Vessel final walkaround | invariant | Walkaround checks hull, systems, cleanliness, plugs, tools, paint and owner items. | release gate |
| boatyard.quality.callback | Boatyard callback | invariant | Callback records post-delivery issue, repair link, responsibility and corrective action. | quality loop |
| boatyard.metrics.boatyard_kpi | Boatyard KPI | variant | KPI tracks haul-outs, days on hard, rework, safety events, material margin and launch delays. | manage yard |
| boatyard.continuity.lift_outage | Travel lift outage plan | invariant | Plan resequences jobs, communicates delays and arranges repair or alternate lift. | recover capacity |
