# BATCH_293 — Public Plaza Operations Detail
# world_skills_core · source: world_skills_core:batch_293:public_plaza_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| plazaops.inventory.plaza_record | Public plaza record | invariant | Record stores boundaries, owner, surfaces, utilities, furniture, landscaping and operating rules. | manage place |
| plazaops.inventory.zone_map | Public plaza zone map | invariant | Map divides seating, circulation, event, vendor, landscape, service and emergency access zones. | organize space |
| plazaops.inventory.utility_point | Plaza utility point | variant | Point includes electrical outlet, water connection, drain, lighting controller or service cabinet. | support operations |
| plazaops.daily.opening_check | Plaza opening check | invariant | Check reviews cleanliness, hazards, seating, lighting, restrooms, vendors, access and overnight issues. | start day |
| plazaops.daily.midday_check | Plaza midday check | variant | Check addresses litter, crowding, spills, furniture movement, complaints and emerging maintenance. | maintain quality |
| plazaops.daily.closing_check | Plaza closing check | invariant | Check secures equipment, removes trash, records damage and confirms overnight status. | end day |
| plazaops.cleaning.litter_pickup | Plaza litter pickup | invariant | Pickup removes trash, glass, food waste, flyers and windblown debris. | keep clean |
| plazaops.cleaning.surface_washing | Plaza surface washing | invariant | Washing removes spills, stains, residue, dirt and odor from hardscape. | reset surface |
| plazaops.cleaning.graffiti_response | Plaza graffiti response | invariant | Response cleans walls, furniture, paving, signs and public art using approved methods. | restore appearance |
| plazaops.cleaning.special_cleaning | Plaza special cleaning | variant | Cleaning handles biohazards, grease, gum, confetti, wax, paint or event residue. | handle exceptions |
| plazaops.seating.moveable_chair_control | Moveable plaza chair control | variant | Control tracks deployment, arrangement, stacking, missing chairs and storage. | manage seating |
| plazaops.seating.fixed_seating_condition | Fixed plaza seating condition | invariant | Condition reviews benches, seat walls, anchors, cracks, splinters and accessibility. | maintain seating |
| plazaops.events.event_permit_check | Plaza event permit check | invariant | Check verifies permitted area, dates, insurance, layout, utilities, noise and cleanup plan. | govern events |
| plazaops.events.load_in_plan | Plaza event load-in plan | variant | Plan controls vendor arrival, vehicle access, staging, surface protection and timing. | prevent conflict |
| plazaops.events.load_out_check | Plaza event load-out check | variant | Check confirms equipment removal, cleaning, damage review and utility shutoff after event. | restore plaza |
| plazaops.vendors.vendor_location | Plaza vendor location | invariant | Location assigns vending space, queue area, power, waste, access and pedestrian clearance. | manage vendors |
| plazaops.vendors.vendor_compliance | Plaza vendor compliance | variant | Compliance checks permit, hours, footprint, waste, noise, fire safety and cleanup. | enforce rules |
| plazaops.access.accessible_route | Plaza accessible route | invariant | Route preserves clear path through plaza to seating, crossings, transit, restrooms and destinations. | inclusive access |
| plazaops.access.emergency_access | Plaza emergency access | invariant | Access keeps fire, EMS, police and maintenance routes clear through events and daily use. | emergency readiness |
| plazaops.access.crowd_flow | Plaza crowd flow | variant | Flow manages queues, pinch points, entrances, exits, vendors and event barriers. | reduce congestion |
| plazaops.safety.trip_hazard | Plaza trip hazard | invariant | Hazard includes lifted pavers, broken edges, mats, cords, planters or settlement. | prevent falls |
| plazaops.safety.slip_hazard | Plaza slip hazard | invariant | Hazard comes from water, algae, ice, spills, leaves, grease or polished surface. | reduce injuries |
| plazaops.safety.lighting_issue | Plaza lighting issue | invariant | Issue affects visibility, security, event safety or wayfinding after dark. | repair lights |
| plazaops.safety.behavior_incident | Plaza behavior incident | variant | Incident includes conflict, intoxication, harassment, unsafe activity or security call. | coordinate response |
| plazaops.repairs.paver_repair | Plaza paver repair | invariant | Repair resets pavers, fills joints, corrects settlement and restores smooth surface. | fix hardscape |
| plazaops.repairs.furniture_repair | Plaza furniture repair | invariant | Repair fixes tables, chairs, benches, bollards, bins, umbrellas or planters. | restore amenities |
| plazaops.repairs.drainage_repair | Plaza drainage repair | variant | Repair addresses ponding, clogged trench drain, settlement, broken grate or poor slope. | keep dry |
| plazaops.landscape.planter_maintenance | Plaza planter maintenance | variant | Maintenance covers watering, pruning, weeds, mulch, soil, irrigation and seasonal plants. | keep landscape |
| plazaops.landscape.tree_care_link | Plaza tree care coordination | variant | Coordination handles tree wells, pruning, roots, lighting, seating conflicts and irrigation. | protect trees |
| plazaops.publicrealm.signage_condition | Plaza signage condition | invariant | Condition checks rules signs, maps, event signs, directional signs and readability. | inform users |
| plazaops.publicrealm.public_art_link | Plaza public art coordination | variant | Coordination covers cleaning, protection, lighting, events, repairs and artist requirements. | preserve art |
| plazaops.complaints.noise_complaint | Plaza noise complaint | variant | Complaint concerns music, events, vendors, maintenance, crowds or equipment. | manage impact |
| plazaops.complaints.cleanliness_complaint | Plaza cleanliness complaint | invariant | Complaint reports litter, odor, spills, overflowing bins, pests or dirty seating. | dispatch cleaning |
| plazaops.complaints.access_complaint | Plaza access complaint | variant | Complaint reports blocked route, vendor encroachment, inaccessible seating or unsafe crossing. | restore access |
| plazaops.records.daily_log | Plaza daily log | invariant | Log records checks, cleaning, incidents, repairs, vendor issues, events and weather. | trace operations |
| plazaops.records.damage_photo | Plaza damage photo | invariant | Photo documents broken surface, furniture, landscape, utility, public art or event damage. | evidence |
| plazaops.reporting.operations_report | Plaza operations report | invariant | Report summarizes visits, events, cleaning, incidents, repairs, complaints and closures. | manage place |
| plazaops.reporting.event_impact_report | Plaza event impact report | variant | Report compares event attendance, damage, cleanup, complaints, revenue and staffing. | evaluate event |
| plazaops.metrics.cleanliness_score | Plaza cleanliness score KPI | variant | Score rates litter, stains, bins, surfaces, furniture and complaint pattern. | monitor quality |
| plazaops.metrics.repair_backlog | Plaza repair backlog KPI | invariant | KPI tracks open defects by severity, age, trade, cost and location. | prioritize work |
| plazaops.coordination.police_security | Plaza police or security coordination | variant | Coordination handles patrols, incidents, events, closures and behavior concerns. | keep safe |
| plazaops.coordination.business_stakeholders | Plaza business stakeholder coordination | variant | Coordination aligns operations with adjacent businesses, deliveries, patios and complaints. | reduce friction |
| plazaops.continuity.weather_closure | Plaza weather closure | variant | Closure may occur for ice, wind, flooding, heat, lightning, smoke or severe storm. | protect users |
| plazaops.close.daily_closeout | Plaza daily closeout | invariant | Closeout confirms logs, unresolved issues, locked assets, waste removal and next-day needs. | finish day |
