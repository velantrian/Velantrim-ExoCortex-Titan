# BATCH_275 — Transit Stop Maintenance Operations Detail
# world_skills_core · source: world_skills_core:batch_275:transit_stop_maintenance_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| transitstopops.inventory.stop_record | Transit stop record | invariant | Record stores stop ID, name, route service, location, direction, owner and status. | manage stop |
| transitstopops.inventory.stop_zone | Transit stop zone | invariant | Zone defines curb length, boarding area, waiting area, signage and passenger access path. | define footprint |
| transitstopops.inventory.amenity_inventory | Transit stop amenity inventory | invariant | Inventory tracks shelter, bench, trash bin, lighting, timetable case, bike rack and real-time display. | know equipment |
| transitstopops.inventory.accessibility_status | Transit stop accessibility status | invariant | Status records pad size, slope, curb height, ramp access, obstructions and accessible route. | support boarding |
| transitstopops.inventory.shelter_asset | Transit shelter asset record | variant | Record captures shelter model, glass panels, roof, frame, anchors, lighting and advertising panels. | maintain shelter |
| transitstopops.inspection.routine_stop_check | Routine transit stop check | invariant | Check reviews signs, shelter, cleanliness, accessibility, damage, lighting and passenger information. | find issues |
| transitstopops.inspection.high_ridership_review | High-ridership stop review | variant | Review gives extra attention to crowding, trash, wear, lighting and boarding reliability. | protect busiest stops |
| transitstopops.inspection.accessibility_walkthrough | Stop accessibility walkthrough | invariant | Walkthrough tests clear path, boarding pad, curb ramp, slopes, tactile cues and obstructions. | reduce barriers |
| transitstopops.inspection.weather_damage_check | Weather damage stop check | variant | Check looks for wind damage, flooding, snow blockage, heat damage or loose panels. | restore service |
| transitstopops.shelter.glass_panel_damage | Shelter glass panel damage | invariant | Damage includes cracked, shattered, missing, loose or unsafe transparent panels. | protect riders |
| transitstopops.shelter.roof_leak | Transit shelter roof leak | variant | Leak records roof holes, clogged drains, seal failure or dripping over waiting area. | keep dry |
| transitstopops.shelter.anchor_failure | Shelter anchor failure | invariant | Failure means loose bolts, corroded anchors, shifted base or unstable shelter frame. | prevent collapse |
| transitstopops.shelter.bench_condition | Transit stop bench condition | invariant | Condition notes broken slats, loose bolts, graffiti, sharp edges, corrosion and cleanliness. | seating safety |
| transitstopops.signs.stop_sign_missing | Transit stop sign missing | invariant | Missing sign reduces driver recognition, rider wayfinding and stop legitimacy. | restore identification |
| transitstopops.signs.route_panel_update | Route panel update | invariant | Update changes routes, destinations, stop ID, service hours, maps or fare information. | accurate info |
| transitstopops.signs.timetable_case | Timetable case maintenance | variant | Maintenance checks weather seal, readability, lock, poster currency and vandalism. | passenger information |
| transitstopops.signs.real_time_display_fault | Real-time display fault | variant | Fault may involve power, communications, software, screen damage or stale predictions. | restore information |
| transitstopops.cleaning.litter_removal | Transit stop litter removal | invariant | Removal clears trash, needles, broken glass, bulky items and overflowing bins. | clean waiting area |
| transitstopops.cleaning.graffiti_removal | Transit stop graffiti removal | invariant | Removal cleans shelter, signs, benches and nearby panels using approved methods. | reduce disorder |
| transitstopops.cleaning.pressure_washing | Transit stop pressure washing | variant | Washing removes grime, spills, residue and odor while protecting signs and electronics. | deep clean |
| transitstopops.cleaning.bin_service | Transit stop trash bin service | invariant | Service empties, replaces liners, checks damage and records overflow or contamination. | manage waste |
| transitstopops.access.boarding_pad_defect | Boarding pad defect | invariant | Defect includes cracked concrete, settlement, ponding, missing pad or poor bus alignment. | accessible boarding |
| transitstopops.access.obstructed_stop | Obstructed transit stop | invariant | Obstruction includes parked vehicles, construction, snow, vegetation, vendors or street furniture. | keep usable |
| transitstopops.access.curb_height_issue | Transit stop curb height issue | variant | Issue affects boarding when curb height, settlement or resurfacing changes bus-floor relation. | improve access |
| transitstopops.access.temporary_stop_access | Temporary transit stop access | variant | Access ensures relocated stops have signs, safe waiting space, lighting and accessible path. | maintain service |
| transitstopops.repairs.work_order_intake | Transit stop work order intake | invariant | Intake records defect, stop ID, photos, priority, responsible party and required trade. | start repair |
| transitstopops.repairs.shelter_repair_order | Shelter repair order | invariant | Order covers panels, frame, roof, lights, benches, anchors, cleaning and parts. | fix shelter |
| transitstopops.repairs.sign_replacement_order | Transit stop sign replacement order | invariant | Order specifies sign type, post, route panels, location, height and installation proof. | restore stop |
| transitstopops.repairs.electrical_repair | Transit stop electrical repair | variant | Repair handles shelter lighting, displays, solar kits, wiring, batteries and power feed. | restore power |
| transitstopops.safety.stop_hazard | Transit stop hazard | invariant | Hazard records sharp edges, unstable shelter, trip hazards, exposed wiring or unsafe debris. | reduce injury |
| transitstopops.safety.traffic_exposure | Transit stop traffic exposure | invariant | Exposure checks crew work near lanes, bus pull-ins, cones, vehicle placement and visibility. | worker safety |
| transitstopops.safety.security_incident | Transit stop security incident | variant | Incident records assault, vandalism, threatening behavior, repeated damage or emergency response. | coordinate safety |
| transitstopops.coordination.bus_operations_notice | Bus operations notice | invariant | Notice informs dispatch and operators about stop closure, relocation, obstruction or repair. | avoid confusion |
| transitstopops.coordination.advertising_contractor | Shelter advertising contractor coordination | variant | Coordination assigns responsibility for ad panels, lighting, cleaning windows and damage reporting. | clarify owner |
| transitstopops.coordination.property_owner_issue | Adjacent property owner issue | variant | Issue handles private encroachment, snow clearing, vegetation, drainage or access conflicts. | resolve boundary |
| transitstopops.rider_reports.rider_complaint | Transit stop rider complaint | invariant | Complaint records dirty, unsafe, missing sign, late update, blocked access or damaged shelter. | rider feedback |
| transitstopops.rider_reports.repeat_complaint | Repeat stop complaint | variant | Repeat complaint flags chronic conditions requiring root-cause review or service change. | target fixes |
| transitstopops.reporting.stop_condition_report | Transit stop condition report | invariant | Report summarizes defects by stop, route, district, amenity, severity and age. | manage backlog |
| transitstopops.reporting.accessibility_report | Stop accessibility report | variant | Report lists access barriers, priority routes, repairs, temporary exceptions and compliance progress. | plan upgrades |
| transitstopops.metrics.repair_response_time | Transit stop repair response time KPI | invariant | KPI measures time from report or inspection to make-safe and permanent repair. | improve service |
| transitstopops.metrics.cleanliness_score | Transit stop cleanliness score | variant | Score combines litter, graffiti, odor, bin overflow, washing need and inspection outcome. | manage cleaning |
| transitstopops.stock.stop_parts_inventory | Transit stop parts inventory | invariant | Inventory tracks signs, posts, glass panels, benches, lights, locks and hardware. | repair readiness |
| transitstopops.continuity.snow_clearance_priority | Transit stop snow clearance priority | variant | Priority ranks stops for snow removal by ridership, accessibility, transfers and critical routes. | winter access |
| transitstopops.close.stop_work_closeout | Transit stop work closeout | invariant | Closeout confirms repair, photos, asset update, rider notice, invoice and backlog status. | finish work |
