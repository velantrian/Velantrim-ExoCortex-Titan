# BATCH_239 — Street Maintenance Operations Detail
# world_skills_core · source: world_skills_core:batch_239:street_maintenance_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| streetops.request.citizen_report | Street maintenance citizen report | invariant | Report records location, defect type, photos, reporter, hazard and callback need. | start response |
| streetops.request.duplicate_merge | Street request duplicate merge | invariant | Merge links repeated reports for the same pothole, sign, signal or drainage issue. | reduce noise |
| streetops.request.priority_score | Street maintenance priority score | invariant | Score ranks safety risk, road class, traffic volume, school route and service impact. | triage work |
| streetops.request.service_area | Street maintenance service area | variant | Area groups requests by district, crew yard, contractor zone or council boundary. | route work |
| streetops.request.status_notice | Street request status notice | variant | Notice updates reporter on received, scheduled, completed, deferred or referred status. | public transparency |
| streetops.pothole.pothole_inspection | Pothole inspection | invariant | Inspection records location, size, depth, lane, hazard level and repair method. | choose repair |
| streetops.pothole.cold_patch | Cold patch pothole repair | variant | Repair fills defect temporarily with material, compaction, traffic control and photo proof. | quick stabilization |
| streetops.pothole.permanent_patch | Permanent pavement patch | variant | Patch cuts, cleans, tacks, fills, compacts and seals pavement defect. | durable repair |
| streetops.pothole.utility_cut | Utility cut restoration | invariant | Restoration verifies trench backfill, surface repair, settlement and responsible party. | protect roadway |
| streetops.pothole.repair_failure | Pavement repair failure | invariant | Failure record captures recurrence, material issue, drainage cause or contractor defect. | learn and recover |
| streetops.sign.sign_inventory | Street sign inventory | invariant | Inventory tracks sign type, location, post, condition, reflectivity and installation date. | asset control |
| streetops.sign.missing_sign | Missing street sign response | invariant | Response prioritizes stop, warning, street-name or regulatory sign replacement. | restore safety |
| streetops.sign.sign_knockdown | Sign knockdown work order | invariant | Work order records crash, vandalism, weather, temporary control and permanent repair. | fix hazard |
| streetops.sign.reflectivity_check | Sign reflectivity check | variant | Check evaluates nighttime visibility, fading, damage and replacement need. | safe navigation |
| streetops.sign.work_zone_signage | Street work zone signage | invariant | Signage sets advance warning, cones, flagging, detour and pedestrian guidance. | protect crews |
| streetops.signal.signal_outage | Traffic signal outage response | invariant | Response records intersection, mode, police need, contractor, timing and restoration. | control traffic |
| streetops.signal.conflict_monitor | Traffic signal conflict monitor | variant | Monitor flags conflicting indications, controller fault or detector failure for urgent repair. | prevent crashes |
| streetops.signal.detector_loop | Signal detector loop repair | variant | Repair tracks loop, camera, radar or button failure and verification. | restore detection |
| streetops.signal.ped_button | Pedestrian button repair | invariant | Repair verifies push button, audible cue, crossing call and accessibility. | safer crossings |
| streetops.signal.timing_request | Signal timing request | variant | Request evaluates congestion, pedestrian delay, transit priority or school timing. | improve flow |
| streetops.striping.lane_marking | Street lane marking | invariant | Marking defines lanes, arrows, stop bars, crosswalks and bike symbols. | guide movement |
| streetops.striping.crosswalk_refresh | Crosswalk refresh | variant | Refresh schedules worn crosswalk repainting by school, transit, crash or wear priority. | pedestrian visibility |
| streetops.striping.material_choice | Pavement marking material choice | variant | Choice selects paint, thermoplastic, tape or raised markers by durability and road type. | fit conditions |
| streetops.striping.no_parking_zone | No-parking curb marking | invariant | Marking implements fire lane, bus stop, loading, ADA or sight-distance restriction. | curb clarity |
| streetops.striping.quality_check | Street striping quality check | invariant | Check verifies alignment, thickness, retroreflectivity, curing and traffic reopening. | good markings |
| streetops.drainage.catch_basin_clean | Catch basin cleaning | invariant | Cleaning removes sediment, debris, leaves, trash and blockage from drainage structure. | prevent flooding |
| streetops.drainage.inlet_blockage | Storm inlet blockage response | invariant | Response clears blockage, checks upstream flooding and documents cause. | restore flow |
| streetops.drainage.culvert_inspection | Street culvert inspection | variant | Inspection checks debris, erosion, collapse, outfall, animal blockage and capacity. | drainage reliability |
| streetops.drainage.flood_call | Street flood call | invariant | Call records water depth, road closure need, pump need, weather and notifications. | protect drivers |
| streetops.drainage.sinkhole_flag | Street sinkhole flag | invariant | Flag secures area, assesses utility/drainage cause, closes lane and escalates repair. | prevent collapse |
| streetops.closure.lane_closure_plan | Street lane closure plan | invariant | Plan defines limits, signs, cones, flaggers, hours, detour and emergency access. | safe work |
| streetops.closure.detour_route | Street detour route | variant | Route avoids weight, height, school, transit and emergency conflicts during closure. | move traffic |
| streetops.closure.permit_coordination | Street closure permit coordination | invariant | Coordination aligns public works, police, transit, businesses, events and notifications. | reduce disruption |
| streetops.crew.daily_assignment | Street crew daily assignment | invariant | Assignment lists crew, truck, tools, material, work orders, route and safety briefing. | organize field work |
| streetops.crew.material_loadout | Street maintenance material loadout | invariant | Loadout records asphalt, signs, cones, paint, tools, fuel and PPE. | ready crew |
| streetops.crew.field_note | Street crew field note | invariant | Note captures site condition, work performed, quantities, photos and unresolved issues. | field evidence |
| streetops.crew.returned_material | Street maintenance returned material | variant | Record tracks unused asphalt, signs, cones, paint or tools back to inventory. | stock control |
| streetops.safety.traffic_control_audit | Traffic control audit | invariant | Audit checks taper, buffer, signs, cones, visibility, flagger position and pedestrian route. | crew safety |
| streetops.safety.near_miss | Street crew near miss | invariant | Report captures vehicle intrusion, equipment incident, trip, struck-by or public conflict. | safety learning |
| streetops.safety.night_work | Street night work setup | variant | Setup covers lighting, reflective gear, noise limits, lane control and fatigue. | safe off-hours |
| streetops.reporting.asset_update | Street asset update | invariant | Update changes pavement, sign, signal, drainage or curb asset status after work. | current map |
| streetops.reporting.cost_capture | Street maintenance cost capture | variant | Capture records labor, equipment, material, contractor and disposal cost by job. | budget insight |
| streetops.metrics.street_kpi | Street maintenance KPI | variant | KPI tracks response time, backlog, potholes repaired, closures, repeat defects and safety incidents. | manage streets |
| streetops.continuity.storm_response | Street storm response | invariant | Response stages crews, clears roads, manages flooding, downed signs, debris and closures. | restore mobility |
