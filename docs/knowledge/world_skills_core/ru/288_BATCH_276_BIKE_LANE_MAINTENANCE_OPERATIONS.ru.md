# BATCH_276 — Bike Lane Maintenance Operations Detail
# world_skills_core · source: world_skills_core:batch_276:bike_lane_maintenance_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| bikelaneops.inventory.bike_lane_segment | Bike lane segment record | invariant | Record stores segment limits, facility type, width, direction, protection, surface and status. | manage network |
| bikelaneops.inventory.facility_type | Bike facility type | invariant | Type distinguishes conventional lane, buffered lane, protected lane, shared lane or trail connection. | classify asset |
| bikelaneops.inventory.protection_asset | Bike lane protection asset | variant | Asset includes posts, curbs, planters, barriers, parking buffer or concrete separators. | maintain protection |
| bikelaneops.inventory.conflict_zone | Bike lane conflict zone | invariant | Zone marks intersections, driveways, bus stops, loading areas, turn lanes and parking edges. | manage risk |
| bikelaneops.inspection.routine_bike_lane_inspection | Routine bike lane inspection | invariant | Inspection checks pavement, markings, debris, drainage, protection, signs and obstructions. | find defects |
| bikelaneops.inspection.corridor_safety_ride | Corridor safety ride | variant | Ride-through observes comfort, visibility, conflicts, surface hazards and continuity from rider view. | rider perspective |
| bikelaneops.inspection.post_construction_check | Post-construction bike lane check | variant | Check confirms reopened lane has markings, surface, signs and barriers restored. | prevent gaps |
| bikelaneops.inspection.winter_condition_check | Winter bike lane condition check | variant | Check records snow storage, ice, plow damage, blocked buffers and narrowed lanes. | winter safety |
| bikelaneops.pavement.surface_crack | Bike lane surface crack | invariant | Crack records longitudinal, transverse, utility cut or edge cracking affecting bicycle travel. | plan repair |
| bikelaneops.pavement.pothole_hazard | Bike lane pothole hazard | invariant | Hazard records hole size, depth, location in wheel path and urgency. | prevent crashes |
| bikelaneops.pavement.edge_drop | Bike lane edge drop | invariant | Drop occurs at gutter, curb, utility patch, shoulder edge or pavement transition. | avoid loss control |
| bikelaneops.pavement.drain_grate_issue | Bike lane drain grate issue | variant | Issue includes wheel-trapping slots, sunken grate, raised grate or blocked inlet. | improve safety |
| bikelaneops.markings.line_wear | Bike lane line wear | invariant | Wear reduces visibility of lane lines, buffers, symbols, green treatment or conflict markings. | refresh markings |
| bikelaneops.markings.symbol_refresh | Bike symbol refresh | variant | Refresh restores bicycle symbols, arrows, buffers, conflict boxes and lane legends. | guide riders |
| bikelaneops.markings.green_conflict_area | Green conflict area maintenance | variant | Maintenance checks color wear, skid resistance, edge failure and driver visibility. | highlight conflict |
| bikelaneops.markings.buffer_marking | Bike lane buffer marking | invariant | Marking defines separation from traffic or parking with painted buffer, hatching or channelization. | clarify space |
| bikelaneops.debris.sweeping_need | Bike lane sweeping need | invariant | Need records glass, gravel, leaves, sand, trash or crash debris in travel path. | keep usable |
| bikelaneops.debris.leaf_accumulation | Leaf accumulation hazard | variant | Leaves hide defects, reduce traction and block drains in bike lanes. | seasonal cleaning |
| bikelaneops.debris.construction_debris | Construction debris in bike lane | variant | Debris includes dirt, stones, nails, equipment, signs or loose materials from adjacent work. | enforce cleanup |
| bikelaneops.obstruction.parked_vehicle_blockage | Parked vehicle bike lane blockage | invariant | Blockage records parked, standing, delivery or ride-hail vehicles occupying bike lane. | enforce access |
| bikelaneops.obstruction.work_zone_blockage | Work zone bike lane blockage | invariant | Blockage occurs when construction closes bike route without safe detour or warning. | maintain route |
| bikelaneops.obstruction.vegetation_encroachment | Bike lane vegetation encroachment | variant | Encroachment includes branches, weeds or shrubs narrowing lane or obscuring signs. | clear path |
| bikelaneops.protection.delineator_damage | Bike lane delineator damage | invariant | Damage includes missing, bent, loose, dirty or low-visibility posts. | restore buffer |
| bikelaneops.protection.barrier_shift | Bike lane barrier shift | invariant | Shifted barrier narrows lane, enters traffic, blocks drainage or creates impact hazard. | realign asset |
| bikelaneops.protection.planter_maintenance | Protected lane planter maintenance | variant | Maintenance covers soil, plants, drainage, visibility, placement and winter storage. | keep separator |
| bikelaneops.signs.bike_route_sign | Bike route sign maintenance | invariant | Maintenance checks route signs, regulatory signs, wayfinding, mounts, visibility and accuracy. | guide users |
| bikelaneops.signs.no_parking_signage | Bike lane no-parking signage | variant | Signage supports enforcement with clear times, curb limits, loading rules and tow authority. | prevent blockage |
| bikelaneops.signs.detour_signage | Bike detour signage | variant | Signage directs riders around closures using safe, continuous and understandable routes. | reduce confusion |
| bikelaneops.repairs.surface_patch_order | Bike lane surface patch order | invariant | Order repairs potholes, utility cuts, edge failures or rutting in bicycle wheel path. | fix hazard |
| bikelaneops.repairs.protection_replacement_order | Bike protection replacement order | invariant | Order replaces posts, curbs, barriers, bases or anchors and records quantities. | restore separation |
| bikelaneops.repairs.marking_work_order | Bike lane marking work order | invariant | Order specifies lines, symbols, green zones, materials, limits, timing and traffic control. | repaint asset |
| bikelaneops.complaints.safety_complaint | Bike lane safety complaint | invariant | Complaint records hazard, blockage, near miss, poor design, missing protection or surface defect. | user feedback |
| bikelaneops.complaints.repeat_hotspot | Bike lane repeat complaint hotspot | variant | Hotspot identifies locations with recurring complaints, crashes, obstructions or maintenance defects. | prioritize action |
| bikelaneops.coordination.parking_enforcement | Bike lane parking enforcement coordination | invariant | Coordination sends blockage patterns, signs, curb rules and evidence to enforcement staff. | clear lanes |
| bikelaneops.coordination.street_sweeping_schedule | Bike lane sweeping schedule coordination | variant | Coordination aligns bike lane debris removal with street sweeping routes and seasonal needs. | clean lanes |
| bikelaneops.coordination.transit_stop_overlap | Bike lane transit stop overlap | variant | Overlap manages bus boarding, floating stops, markings and passenger crossing movements. | reduce conflict |
| bikelaneops.data.map_layer_update | Bike lane map layer update | invariant | Update records facility status, closures, protection, defects, completed work and detours. | shared awareness |
| bikelaneops.data.before_after_photos | Bike lane before-after photos | variant | Photos document defect, repair, markings, barriers and safety condition after work. | evidence |
| bikelaneops.reporting.condition_report | Bike lane condition report | invariant | Report summarizes pavement, markings, protection, debris, obstructions and complaint trends. | manage network |
| bikelaneops.reporting.closure_report | Bike lane closure report | variant | Report lists active closures, detours, expected reopen dates and responsible permit holders. | inform riders |
| bikelaneops.metrics.usable_lane_rate | Bike lane usable lane rate KPI | invariant | KPI measures share of bike lane network free of critical obstruction or hazard. | service quality |
| bikelaneops.metrics.protection_uptime | Bike lane protection uptime KPI | variant | KPI tracks percentage of protective devices present, aligned and functional. | maintain safety |
| bikelaneops.safety.crew_lane_work | Bike lane crew work safety | invariant | Safety covers traffic exposure, cones, buffer use, work vehicles, visibility and spotters. | protect crews |
| bikelaneops.close.maintenance_closeout | Bike lane maintenance closeout | invariant | Closeout confirms hazard fixed, map updated, complaint resolved, photos stored and schedule adjusted. | finish work |
