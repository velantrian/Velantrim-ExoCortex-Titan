# BATCH_278 — Snow and Ice Control Operations Detail
# world_skills_core · source: world_skills_core:batch_278:snow_ice_control_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| snowiceops.planning.snow_route_priority | Snow route priority | invariant | Priority ranks roads by emergency access, traffic volume, transit, hills, schools and policy. | sequence work |
| snowiceops.planning.route_map | Snow route map | invariant | Map assigns plow routes, salt routes, turnaround points, dead ends, bridges and trouble spots. | guide crews |
| snowiceops.planning.level_of_service | Winter level of service | invariant | Standard defines target response, pass frequency, bare pavement goal and acceptable residual snow. | set expectations |
| snowiceops.planning.storm_forecast_review | Storm forecast review | invariant | Review considers timing, temperature, accumulation, wind, ice risk and pavement temperature. | prepare shift |
| snowiceops.materials.salt_stockpile | Salt stockpile control | invariant | Control tracks tons on hand, moisture, cover, contamination, deliveries and reorder level. | ensure supply |
| snowiceops.materials.brine_production | Brine production | variant | Production mixes salt solution to target concentration for anti-icing or prewetting. | improve treatment |
| snowiceops.materials.abrasive_stock | Winter abrasive stock | variant | Stock includes sand or grit used for traction where salt performance or policy is limited. | traction aid |
| snowiceops.materials.material_application_rate | Material application rate | invariant | Rate sets salt, brine or abrasive amount by temperature, precipitation, road type and condition. | avoid waste |
| snowiceops.equipment.plow_truck_readiness | Plow truck readiness | invariant | Readiness checks blade, hydraulics, spreader, lights, tires, radios, fuel and calibration. | deploy fleet |
| snowiceops.equipment.spreader_calibration | Salt spreader calibration | invariant | Calibration verifies delivered material rate by speed, gate setting, spinner and controller. | accurate dosing |
| snowiceops.equipment.blade_condition | Plow blade condition | invariant | Condition records cutting edge wear, damage, bolts, shoes and replacement need. | effective plowing |
| snowiceops.equipment.loader_readiness | Loader readiness | variant | Readiness checks loader, bucket, fuel, tires, salt dome access and backup equipment. | load material |
| snowiceops.operations.anti_icing | Anti-icing operation | invariant | Operation applies liquid before storm when conditions allow to reduce bonding. | prevent ice |
| snowiceops.operations.deicing | Deicing operation | invariant | Operation applies material after snow or ice starts to break bond and improve traction. | restore grip |
| snowiceops.operations.plowing_pass | Plowing pass | invariant | Pass removes snow from lane using route sequence, blade angle, speed and safe clearance. | clear road |
| snowiceops.operations.curb_to_curb_cleanup | Curb-to-curb cleanup | variant | Cleanup widens roads after initial passes, clears parking lanes, gutters and intersections. | restore capacity |
| snowiceops.operations.bridge_treatment | Bridge treatment | invariant | Treatment prioritizes bridges because decks freeze earlier than adjacent road surfaces. | prevent black ice |
| snowiceops.operations.hill_treatment | Hill treatment | variant | Treatment gives extra material, plowing or sanding to steep grades and known traction trouble spots. | reduce slipping |
| snowiceops.operations.intersection_cleanup | Intersection snow cleanup | variant | Cleanup removes windrows, packed snow and sightline obstructions at junctions and crossings. | improve movement |
| snowiceops.operations.sidewalk_snow_control | Public sidewalk snow control | variant | Control clears municipal sidewalks, curb ramps, crossings, bridges and transit access points. | pedestrian access |
| snowiceops.shift.storm_shift_activation | Storm shift activation | invariant | Activation assigns crews, routes, supervisors, mechanics, dispatch, breaks and reporting channels. | start response |
| snowiceops.shift.crew_rotation | Winter crew rotation | invariant | Rotation manages fatigue, maximum hours, meal breaks, relief drivers and overnight coverage. | safe staffing |
| snowiceops.shift.callout_list | Snow callout list | variant | List identifies staff, contractors, mechanics, loaders and supervisors available for storm work. | mobilize people |
| snowiceops.shift.yard_dispatch | Snow yard dispatch | invariant | Dispatch releases trucks with route, material, fuel, radio, AVL check and first assignment. | coordinate fleet |
| snowiceops.monitoring.pavement_temperature | Pavement temperature monitoring | invariant | Monitoring uses sensors, forecasts or observations to adjust material and plowing strategy. | choose treatment |
| snowiceops.monitoring.avl_tracking | Snow fleet AVL tracking | variant | Tracking shows vehicle location, route progress, plow status, spreader activity and gaps. | manage response |
| snowiceops.monitoring.road_condition_report | Winter road condition report | invariant | Report classifies road as clear, wet, slushy, snow-covered, icy or closed. | inform decisions |
| snowiceops.monitoring.trouble_spot_log | Winter trouble spot log | variant | Log records recurring drifting, icing, drainage, shade, hills, bridges and complaint locations. | target fixes |
| snowiceops.complaints.missed_street | Missed street snow complaint | invariant | Complaint records location, route status, timing, obstruction, response and closure. | handle reports |
| snowiceops.complaints.driveway_windrow | Driveway windrow complaint | variant | Complaint records plow-created snow ridge, local policy and any special access issue. | explain limits |
| snowiceops.complaints.ice_patch | Ice patch complaint | invariant | Complaint reports localized ice from drainage, refreeze, shade, leak or missed treatment. | dispatch treatment |
| snowiceops.complaints.mailbox_damage | Snow operation mailbox damage | variant | Damage record captures location, photos, plow route, impact evidence and repair policy. | resolve claims |
| snowiceops.safety.whiteout_condition | Whiteout operating condition | invariant | Condition reduces visibility and may require convoy, reduced speed, route hold or closure. | protect crew |
| snowiceops.safety.struck_object | Plow struck-object incident | invariant | Incident records impact with parked car, mailbox, sign, curb, utility or roadside object. | manage risk |
| snowiceops.safety.backing_collision_risk | Plow backing collision risk | variant | Risk controls backing through spotters, route design, cameras, alarms and training. | prevent crashes |
| snowiceops.safety.material_handling_safety | Winter material handling safety | invariant | Safety covers salt piles, loaders, conveyors, brine tanks, slips, dust and PPE. | protect yard |
| snowiceops.contractors.contractor_route | Contractor snow route | variant | Route assigned to contractor defines service area, standards, reporting, pay basis and inspection. | expand capacity |
| snowiceops.contractors.contractor_performance | Snow contractor performance | invariant | Performance checks route completion, response time, material use, complaints, safety and documentation. | manage contract |
| snowiceops.reporting.storm_log | Snow storm log | invariant | Log records forecast, activation, routes, materials, incidents, complaints, costs and decisions. | preserve record |
| snowiceops.reporting.material_usage_report | Winter material usage report | invariant | Report totals salt, brine, abrasives by storm, route, truck and application rate. | manage stock |
| snowiceops.reporting.post_storm_review | Post-storm review | invariant | Review compares forecast, response, complaints, crashes, costs, equipment failures and lessons learned. | improve program |
| snowiceops.metrics.route_completion_time | Snow route completion time KPI | invariant | KPI measures time to complete assigned priority route passes after storm trigger. | evaluate response |
| snowiceops.metrics.salt_use_per_lane_mile | Salt use per lane mile KPI | variant | KPI compares material use with weather severity, level of service and environmental targets. | optimize use |
| snowiceops.close.storm_closeout | Snow storm closeout | invariant | Closeout confirms routes complete, trucks cleaned, materials reconciled, complaints triaged and reports filed. | finish event |
