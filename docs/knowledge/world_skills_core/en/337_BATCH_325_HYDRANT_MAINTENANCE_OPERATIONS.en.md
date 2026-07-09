# BATCH 325: Hydrant Maintenance Operations

**KnowledgeUnits:** 44  
**Namespace:** `hydrantops.*`  
**Scope:** inspections, flow tests, lubrication, drainage, caps, painting, repairs and fire coordination.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| hydrantops.inventory.hydrant_id | hydrant ID | RECORD | Hydrant record includes ID, location, make, model, size, year, valve and pressure zone. | Links inspections, fire use and repairs. |
| hydrantops.inventory.barrel_type | barrel type | RECORD | Dry-barrel and wet-barrel hydrants have different freeze and drainage behavior. | Maintenance method depends on climate and design. |
| hydrantops.inventory.fire_district | fire district link | RECORD | Hydrant is linked to fire response area, station and dispatch map. | Fire crews need accurate hydrant data. |
| hydrantops.inspection.visibility | visibility check | INSPECTION | Hydrant must be visible from road and clear of vegetation, snow, signs or parked obstruction. | Hidden hydrants delay fire response. |
| hydrantops.inspection.clearance | clearance | INSPECTION | Clearance around hydrant is checked for hose connection and wrench access. | Firefighters need working space. |
| hydrantops.inspection.damage | physical damage | INSPECTION | Crews check for traffic damage, tilted barrel, cracked bonnet and broken flanges. | Damage can make hydrant unusable or leaking. |
| hydrantops.inspection.leak | leak check | INSPECTION | Leakage at nozzles, bonnet, stem or base is recorded. | Leaks waste water and can undermine pavement. |
| hydrantops.inspection.nozzle_threads | nozzle threads | INSPECTION | Threads and seats are checked for damage, debris and compatibility. | Hose connections must work under pressure. |
| hydrantops.caps.cap_condition | cap condition | INSPECTION | Caps, gaskets and chains are checked for corrosion, fit and missing parts. | Missing caps allow debris and thread damage. |
| hydrantops.caps.outlet_size | outlet size | RECORD | Steamer and side outlet sizes are recorded and compared with fire department needs. | Ensures equipment compatibility. |
| hydrantops.operation.slow_open | slow opening | SAFETY_RULE | Hydrants are opened slowly and fully where design requires. | Prevents water hammer and drain-port leakage. |
| hydrantops.operation.slow_close | slow closing | SAFETY_RULE | Hydrants are closed slowly to avoid pressure surge. | Protects mains, services and valves. |
| hydrantops.operation.main_valve | main valve condition | INSPECTION | Operating nut turns, stiffness and full closure are checked. | Shows whether hydrant can be controlled. |
| hydrantops.operation.aux_valve | auxiliary valve | RECORD | Hydrant isolation valve location and operability are tracked. | Allows repair without large shutdown. |
| hydrantops.flow.static_pressure | static pressure | MEASUREMENT | Static pressure is measured before flow test. | Establishes baseline system pressure. |
| hydrantops.flow.residual_pressure | residual pressure | MEASUREMENT | Residual pressure during flow shows system capacity under demand. | Supports fire-flow evaluation. |
| hydrantops.flow.pitot | pitot reading | MEASUREMENT | Pitot reading estimates discharge from nozzle flow. | Converts field flow into usable fire-flow data. |
| hydrantops.flow.diffuser | diffuser | SAFETY_RULE | Diffuser controls discharge direction, velocity and erosion. | Protects traffic, property and workers. |
| hydrantops.flow.dechlorination | dechlorination | CONSTRAINT | Flow water may need dechlorination before entering storm drains or streams. | Prevents environmental harm. |
| hydrantops.drainage.drain_check | drain check | INSPECTION | Dry-barrel hydrants are checked for proper barrel drainage after closure. | Prevents freezing and barrel damage. |
| hydrantops.drainage.plugged_drain | plugged drain | FAILURE_MODE | Water standing in barrel indicates plugged drains or groundwater intrusion. | Requires repair before freeze season. |
| hydrantops.drainage.pump_out | pump-out | METHOD | Standing water may be pumped out during winter maintenance. | Temporary mitigation until repair. |
| hydrantops.lubrication.stem | stem lubrication | METHOD | Stem and operating nut are lubricated per manufacturer guidance. | Reduces stiffness and breakage. |
| hydrantops.lubrication.nozzle | nozzle lubrication | METHOD | Nozzle caps and threads receive appropriate anti-seize or lubricant. | Keeps caps removable by fire crews. |
| hydrantops.paint.color_code | color coding | RECORD | Paint color may indicate flow class, ownership or status under local standard. | Fire crews can quickly interpret hydrant capacity. |
| hydrantops.paint.surface_prep | surface preparation | METHOD | Painting requires rust removal, cleaning and compatible coating. | Paint protects asset and improves visibility. |
| hydrantops.paint.reflective_marker | reflective marker | METHOD | Markers or flags help locate hydrants at night or in snow. | Speeds emergency access. |
| hydrantops.repairs.breakaway | breakaway flange | INSPECTION | Traffic-hit hydrants are checked at breakaway flange and barrel alignment. | Ensures impact protection worked correctly. |
| hydrantops.repairs.seat_repair | seat repair | METHOD | Leaking main seats may need disassembly, parts and isolation. | Stops hidden water loss. |
| hydrantops.repairs.rebuild | rebuild | METHOD | Rebuild replaces gaskets, seals, stems, nozzles or internal parts. | Extends hydrant life without full replacement. |
| hydrantops.repairs.replace | replacement trigger | DECISION_RULE | Replacement is considered for age, unavailable parts, severe corrosion, repeated leaks or poor location. | Prevents endless repair on obsolete hydrants. |
| hydrantops.firecoord.map_update | fire map update | METHOD | Hydrant status changes are sent to fire department and dispatch maps. | Fire crews avoid out-of-service hydrants. |
| hydrantops.firecoord.out_of_service | out-of-service tag | RECORD | OOS hydrants are tagged, logged and communicated with expected repair date. | Prevents reliance during fire response. |
| hydrantops.firecoord.training_use | training use | METHOD | Fire training use is coordinated with utility to avoid pressure and water-quality problems. | Balances emergency readiness and system operation. |
| hydrantops.firecoord.private_hydrant | private hydrant | CONSTRAINT | Private hydrants may have owner maintenance duties and utility/fire inspection coordination. | Clarifies responsibility. |
| hydrantops.safety.traffic | traffic safety | SAFETY_RULE | Cones, signs, vests and safe truck positioning protect hydrant crews. | Hydrants often sit in roadside zones. |
| hydrantops.safety.ice | ice hazard | FAILURE_MODE | Winter flushing or leaks can create road and sidewalk ice. | Maintenance must control runoff in freezing weather. |
| hydrantops.safety.pressure | pressure hazard | SAFETY_RULE | Caps are not removed from pressurized or damaged outlets without care. | Prevents injury from sudden release. |
| hydrantops.records.inspection | inspection record | RECORD | Record includes condition, turns, leaks, drainage, caps, paint, flow and photos. | Standardizes maintenance history. |
| hydrantops.records.work_order | work order | RECORD | Repairs use work orders with defect, parts, labor, isolation and closeout. | Tracks backlog and cost. |
| hydrantops.records.flow_history | flow history | RECORD | Flow test values are stored by date and conditions. | Shows capacity trends and system changes. |
| hydrantops.reporting.program_summary | program summary | RECORD | Summary reports inspected, flowed, repaired, OOS and replaced hydrants. | Gives managers and fire partners system view. |
| hydrantops.reporting.priority | repair priority | MODEL | Priority uses fire criticality, defect severity, flow capacity and location risk. | Directs crews to most important hydrants. |
| hydrantops.review.post_fire | post-fire review | METHOD | After major fire, hydrant performance and water system impacts are reviewed. | Improves maps, maintenance and coordination. |

