# BATCH_286 — Traffic Calming Operations Detail
# world_skills_core · source: world_skills_core:batch_286:traffic_calming_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| calmingops.request.traffic_calming_request | Traffic calming request | invariant | Request records speeding, cut-through traffic, pedestrian concern, school route or neighborhood safety issue. | start review |
| calmingops.request.petition_requirement | Traffic calming petition requirement | variant | Requirement asks for resident support, affected area definition and verified signatures before study. | confirm demand |
| calmingops.request.eligibility_screen | Traffic calming eligibility screen | invariant | Screen checks street classification, speed limit, emergency route, traffic volume and policy thresholds. | decide review |
| calmingops.request.problem_statement | Traffic calming problem statement | invariant | Statement defines observed issue, location, users, time period, evidence and desired outcome. | focus study |
| calmingops.study.speed_study | Traffic calming speed study | invariant | Study measures vehicle speeds, percentiles, sample size, time and location conditions. | quantify speeding |
| calmingops.study.volume_study | Traffic volume study | invariant | Study measures daily traffic, peak hours, directional split and cut-through indicators. | quantify use |
| calmingops.study.crash_review | Traffic calming crash review | invariant | Review checks crash history, severity, patterns, vulnerable users and roadway context. | assess risk |
| calmingops.study.walk_audit | Traffic calming walk audit | variant | Audit observes crossings, sidewalks, sightlines, driver behavior, school activity and comfort. | ground truth |
| calmingops.study.before_after_data | Traffic calming before-after data | variant | Data compares speeds, volumes, crashes and complaints before and after installation. | evaluate effect |
| calmingops.devices.speed_hump | Speed hump | invariant | Device is raised roadway feature that slows vehicles on suitable low-speed streets. | reduce speed |
| calmingops.devices.speed_cushion | Speed cushion | variant | Device has wheel gaps intended to slow cars while allowing some emergency vehicles to straddle. | balance response |
| calmingops.devices.raised_crosswalk | Raised crosswalk | invariant | Crosswalk is elevated to slow vehicles and improve pedestrian visibility. | safer crossing |
| calmingops.devices.curb_extension | Curb extension | invariant | Extension narrows crossing distance and visually narrows roadway at intersection or midblock. | calm turns |
| calmingops.devices.chicane | Chicane | variant | Chicane creates horizontal deflection through alternating curb extensions, islands or parking layout. | slow path |
| calmingops.devices.mini_roundabout | Mini roundabout | variant | Roundabout slows intersection traffic and changes conflict angles in constrained space. | calm junction |
| calmingops.devices.neighborhood_gateway | Neighborhood gateway | variant | Gateway uses signs, markings, islands or streetscape cues to mark traffic-calmed area. | signal context |
| calmingops.design.device_spacing | Traffic calming device spacing | invariant | Spacing affects speed reduction consistency, driver comfort, drainage and emergency access. | design corridor |
| calmingops.design.drainage_check | Traffic calming drainage check | invariant | Check ensures devices do not trap water, block gutters or create icing. | avoid flooding |
| calmingops.design.bicycle_accommodation | Traffic calming bicycle accommodation | variant | Accommodation considers bike lanes, bypasses, gaps, approach angle and surface comfort. | protect cyclists |
| calmingops.design.emergency_access_review | Traffic calming emergency access review | invariant | Review checks fire, EMS and police routes, delay, turning and device choice. | maintain response |
| calmingops.engagement.public_meeting | Traffic calming public meeting | variant | Meeting presents data, options, tradeoffs, costs, timeline and resident feedback. | build consent |
| calmingops.engagement.ballot_process | Traffic calming resident ballot | variant | Ballot records support threshold, eligible addresses, returned votes and decision rule. | decide installation |
| calmingops.engagement.school_coordination | Traffic calming school coordination | variant | Coordination includes school access, arrival patterns, crossing guards, buses and family travel. | align safety |
| calmingops.approval.project_approval | Traffic calming project approval | invariant | Approval confirms device, location, funding, policy compliance, design and implementation authority. | authorize work |
| calmingops.approval.funding_source | Traffic calming funding source | variant | Source may be capital budget, grant, district fund, school program or developer contribution. | pay project |
| calmingops.install.temporary_trial | Temporary traffic calming trial | variant | Trial uses modular devices, paint, cones or planters before permanent construction. | test design |
| calmingops.install.permanent_installation | Permanent traffic calming installation | invariant | Installation builds approved device with layout, materials, traffic control and inspection. | deliver project |
| calmingops.install.signs_markings | Traffic calming signs and markings | invariant | Signs and markings warn drivers, define device, guide users and support enforceability. | communicate device |
| calmingops.install.construction_inspection | Traffic calming construction inspection | invariant | Inspection verifies dimensions, location, drainage, visibility, accessibility and material quality. | quality control |
| calmingops.maintenance.device_condition | Traffic calming device condition | invariant | Condition checks cracking, settlement, missing signs, worn markings, loose modules and drainage. | keep functional |
| calmingops.maintenance.modular_device_repair | Modular traffic calming repair | variant | Repair replaces damaged posts, rubber humps, curbs, bolts, reflectors or planters. | restore device |
| calmingops.maintenance.snow_plow_compatibility | Traffic calming snow plow compatibility | variant | Compatibility considers device profile, markings, plow damage, winter visibility and route operations. | maintain winter |
| calmingops.monitoring.speed_reduction_result | Speed reduction result | invariant | Result compares target and measured speed change after traffic calming installation. | judge success |
| calmingops.monitoring.volume_diversion | Traffic volume diversion | variant | Diversion analysis checks whether calming shifted traffic to parallel streets. | avoid side effects |
| calmingops.monitoring.complaint_followup | Traffic calming complaint follow-up | invariant | Follow-up reviews concerns about noise, delay, access, drainage, parking or device placement. | adjust program |
| calmingops.safety.device_visibility | Traffic calming device visibility | invariant | Visibility ensures device is seen in daylight, night, rain and snow through markings or signs. | prevent surprise |
| calmingops.safety.motorcycle_safety | Traffic calming motorcycle safety | variant | Safety considers skid risk, approach angle, surface texture and warning for two-wheel users. | reduce risk |
| calmingops.safety.accessibility_effect | Traffic calming accessibility effect | variant | Effect reviews crossings, curb ramps, tactile cues, slopes and pedestrian route continuity. | inclusive design |
| calmingops.records.project_file | Traffic calming project file | invariant | File stores request, data, engagement, design, approval, construction, monitoring and closeout. | trace decision |
| calmingops.records.device_inventory_update | Traffic calming device inventory update | invariant | Update records installed device, dimensions, location, materials, signs, markings and maintenance schedule. | manage asset |
| calmingops.reporting.program_report | Traffic calming program report | variant | Report summarizes requests, studies, approvals, installations, costs, outcomes and backlog. | manage program |
| calmingops.metrics.study_cycle_time | Traffic calming study cycle time KPI | invariant | KPI measures time from eligible request to completed study and decision. | improve process |
| calmingops.metrics.installation_success_rate | Traffic calming success rate KPI | variant | KPI tracks projects meeting speed, volume, safety or satisfaction targets after installation. | evaluate policy |
| calmingops.close.project_closeout | Traffic calming project closeout | invariant | Closeout confirms installation, inventory, resident notice, monitoring plan and maintenance handoff. | finish project |
