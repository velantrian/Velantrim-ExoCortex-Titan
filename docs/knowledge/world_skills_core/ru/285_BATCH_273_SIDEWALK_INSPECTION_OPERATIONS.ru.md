# BATCH_273 — Sidewalk Inspection Operations Detail
# world_skills_core · source: world_skills_core:batch_273:sidewalk_inspection_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| sidewalkops.inventory.sidewalk_segment | Sidewalk segment record | invariant | Record stores block face, material, width, grade, curb ramps, ownership and inspection history. | manage network |
| sidewalkops.inventory.parcel_frontage_link | Sidewalk parcel frontage link | variant | Link connects sidewalk responsibility to adjacent parcel, public asset or special district. | assign responsibility |
| sidewalkops.inventory.ramp_inventory | Curb ramp inventory | invariant | Inventory records ramp type, landing, detectable warning, slope, crosswalk relation and condition. | accessibility |
| sidewalkops.inventory.tree_well_record | Tree well record | variant | Record captures tree location, species if known, grate, roots, soil and sidewalk interaction. | coordinate trees |
| sidewalkops.inspection.routine_sidewalk_inspection | Routine sidewalk inspection | invariant | Inspection checks panels, joints, slopes, obstructions, ramps, drainage and trip hazards. | find defects |
| sidewalkops.inspection.complaint_inspection | Sidewalk complaint inspection | invariant | Inspection responds to public reports with location, hazard type, photos, measurements and priority. | respond fairly |
| sidewalkops.inspection.post_storm_inspection | Post-storm sidewalk inspection | variant | Inspection looks for fallen branches, uplift, ice, washout, debris and access blockage. | restore passage |
| sidewalkops.inspection.school_route_review | School route sidewalk review | variant | Review prioritizes sidewalks near schools, crossings, bus stops and child walking routes. | protect children |
| sidewalkops.hazard.vertical_displacement | Sidewalk vertical displacement | invariant | Hazard records height difference between slabs, utility covers, ramps or patch edges. | prevent trips |
| sidewalkops.hazard.cracked_panel | Sidewalk cracked panel | invariant | Hazard captures cracks, broken concrete, spalling, missing pieces and panel instability. | schedule repair |
| sidewalkops.hazard.surface_spalling | Sidewalk surface spalling | variant | Spalling records flaking, scaling, aggregate exposure or freeze-thaw surface loss. | assess severity |
| sidewalkops.hazard.settlement_depression | Sidewalk settlement depression | invariant | Depression causes ponding, uneven walking surface or drainage problems from base settlement. | fix drainage |
| sidewalkops.hazard.excessive_cross_slope | Excessive sidewalk cross slope | invariant | Cross slope may make travel difficult for wheelchairs, strollers or people with mobility limits. | accessibility |
| sidewalkops.hazard.narrow_clear_width | Narrow sidewalk clear width | invariant | Narrow width results from poles, signs, vegetation, outdoor dining, snow or construction. | maintain access |
| sidewalkops.hazard.slippery_surface | Slippery sidewalk surface | variant | Hazard comes from algae, ice, polished surface, debris, mud or drainage. | reduce falls |
| sidewalkops.access.detectable_warning_issue | Detectable warning issue | invariant | Issue includes missing, worn, misaligned or wrong-color truncated domes at curb ramps. | accessible crossing |
| sidewalkops.access.ramp_landing_defect | Curb ramp landing defect | invariant | Defect includes steep landing, insufficient space, obstruction or poor alignment with crossing. | wheelchair usability |
| sidewalkops.access.driveway_crossing_barrier | Driveway crossing barrier | variant | Barrier occurs when driveway slope, lip or surface interrupts accessible sidewalk path. | continuous route |
| sidewalkops.trees.root_uplift | Tree root sidewalk uplift | invariant | Uplift occurs when roots raise panels, creating slope change, cracks or trip hazards. | coordinate repair |
| sidewalkops.trees.root_pruning_review | Tree root pruning review | variant | Review weighs sidewalk repair against tree stability, health, arborist guidance and permits. | avoid damage |
| sidewalkops.trees.flexible_surface_option | Flexible sidewalk surface option | variant | Option uses asphalt, rubber, porous material or bridging around roots where allowed. | preserve tree |
| sidewalkops.workorders.temporary_make_safe | Sidewalk temporary make-safe | invariant | Action uses asphalt wedge, grinding, barricade or plate until permanent repair. | reduce immediate risk |
| sidewalkops.workorders.panel_replacement_order | Sidewalk panel replacement order | invariant | Order specifies panels, limits, concrete, base, joints, ramps, traffic control and restoration. | permanent fix |
| sidewalkops.workorders.sidewalk_grinding_order | Sidewalk grinding order | variant | Order removes minor vertical offsets within limits without full panel replacement. | quick repair |
| sidewalkops.workorders.utility_cover_adjustment | Utility cover adjustment | variant | Order coordinates raised or sunken covers with utility owner and sidewalk repair crew. | remove hazard |
| sidewalkops.notices.owner_notice | Sidewalk owner notice | invariant | Notice informs responsible owner of defect, deadline, standards, permit path and appeal. | legal process |
| sidewalkops.notices.repair_deadline | Sidewalk repair deadline | invariant | Deadline sets required action period based on hazard severity, local code and notice date. | enforce timeline |
| sidewalkops.notices.failure_to_repair | Failure-to-repair escalation | variant | Escalation may trigger city repair, billing, lien process or enforcement hearing. | close defects |
| sidewalkops.closure.pedestrian_detour | Pedestrian detour | invariant | Detour provides accessible route, signs, barriers, ramps and protection from traffic. | maintain passage |
| sidewalkops.closure.hazard_barricade | Sidewalk hazard barricade | invariant | Barricade isolates unsafe slab, hole, work area or collapse risk until repair. | protect public |
| sidewalkops.closure.accessibility_exception | Accessibility closure exception | variant | Exception records why full accessibility cannot be maintained and what mitigation is provided. | document limits |
| sidewalkops.data.photo_evidence | Sidewalk photo evidence | invariant | Photos show defect, measurement, context, address, repair completion and closeout condition. | support record |
| sidewalkops.data.measurement_standard | Sidewalk measurement standard | invariant | Standard defines how to measure displacement, slope, width, defect size and location. | consistent ratings |
| sidewalkops.data.map_update | Sidewalk map update | variant | Update changes segment status, repair history, hazard layer or closure zone. | spatial tracking |
| sidewalkops.prioritization.risk_rank | Sidewalk risk rank | invariant | Rank combines severity, pedestrian volume, vulnerable users, complaints, route importance and exposure. | choose work |
| sidewalkops.prioritization.ada_priority_route | ADA priority route | variant | Route prioritizes accessible paths to transit, schools, government buildings and medical services. | equity access |
| sidewalkops.prioritization.bundle_repairs | Sidewalk repair bundling | variant | Bundling groups nearby panels, ramps, tree work or utility fixes for efficient contracting. | reduce cost |
| sidewalkops.reporting.defect_backlog_report | Sidewalk defect backlog report | invariant | Report summarizes open defects by severity, age, location, cause and responsibility. | manage program |
| sidewalkops.reporting.notice_status_report | Sidewalk notice status report | variant | Report tracks issued notices, deadlines, owner repairs, appeals, city repairs and collections. | monitor enforcement |
| sidewalkops.metrics.repair_cycle_time | Sidewalk repair cycle time KPI | invariant | KPI measures time from inspection or complaint to make-safe and permanent repair. | improve response |
| sidewalkops.metrics.accessible_route_gap | Accessible route gap KPI | variant | KPI tracks missing, blocked or noncompliant links on priority pedestrian routes. | target investment |
| sidewalkops.safety.inspector_field_safety | Sidewalk inspector field safety | invariant | Safety covers traffic exposure, uneven ground, dogs, weather, visibility and lone-worker protocol. | protect inspectors |
| sidewalkops.continuity.snow_ice_blockage | Sidewalk snow and ice blockage | variant | Blockage records uncleared snow, refreeze, plow windrows, icy ramps and enforcement response. | winter access |
| sidewalkops.close.repair_closeout | Sidewalk repair closeout | invariant | Closeout confirms defect corrected, photos stored, map updated, notice resolved and billing handled. | finish case |
