# BATCH_274 — Road Closure Permit Operations Detail
# world_skills_core · source: world_skills_core:batch_274:road_closure_permit_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| closureops.application.closure_application | Road closure permit application | invariant | Application records applicant, location, dates, purpose, affected lanes, sidewalk and detour needs. | start review |
| closureops.application.work_type | Closure work type | variant | Type classifies utility work, construction, event, filming, crane lift, emergency or maintenance. | route review |
| closureops.application.impact_area | Closure impact area | invariant | Area defines street limits, intersections, driveways, transit stops, sidewalks and parking affected. | understand footprint |
| closureops.application.schedule_window | Closure schedule window | invariant | Window states start, end, work hours, night work, weekend work and restoration time. | coordinate timing |
| closureops.application.applicant_responsibility | Applicant responsibility | invariant | Responsibility covers traffic control, notifications, insurance, restoration, cleanup and compliance. | set obligations |
| closureops.review.completeness_check | Closure application completeness check | invariant | Check verifies plans, dates, contact, insurance, fees, drawings, detours and approvals. | avoid delays |
| closureops.review.conflict_check | Road closure conflict check | invariant | Check compares proposed closure with other permits, events, paving, transit, schools and emergencies. | prevent overlap |
| closureops.review.emergency_access_review | Emergency access review | invariant | Review confirms fire, ambulance and police access through detours, staging and lane widths. | protect response |
| closureops.review.transit_review | Transit impact review | variant | Review checks bus stops, routes, headways, temporary stops, passenger notices and operator access. | keep transit |
| closureops.review.business_access_review | Business access review | variant | Review checks deliveries, customer access, loading, signage and stakeholder contact. | reduce disruption |
| closureops.traffic_control.traffic_control_plan | Traffic control plan | invariant | Plan shows signs, cones, barriers, tapers, flaggers, detours, phases and pedestrian routes. | safe closure |
| closureops.traffic_control.detour_route | Detour route | invariant | Route guides vehicles around closure using suitable streets, signs, turns and capacity. | maintain movement |
| closureops.traffic_control.pedestrian_control | Pedestrian closure control | invariant | Control maintains accessible walkway or detour with barriers, ramps, signs and separation. | pedestrian safety |
| closureops.traffic_control.bicycle_control | Bicycle closure control | variant | Control manages bike lanes, shared detours, merge points and warning signs. | protect cyclists |
| closureops.traffic_control.flagger_plan | Flagger plan | variant | Plan assigns flagger positions, communication, visibility, breaks, emergency steps and authority. | manage flow |
| closureops.traffic_control.temporary_signal | Temporary signal control | variant | Temporary signal manages alternating traffic, pedestrian phases, power, timing and monitoring. | control traffic |
| closureops.conditions.permit_condition | Road closure permit condition | invariant | Condition states limits, work hours, traffic control, inspections, notifications and restoration. | enforce rules |
| closureops.conditions.no_parking_posting | No-parking posting condition | variant | Condition requires signs with dates, times, limits, towing rules and posting verification. | clear curb |
| closureops.conditions.noise_condition | Closure noise condition | variant | Condition limits night work, equipment noise, backup alarms or mitigation near sensitive uses. | reduce nuisance |
| closureops.conditions.restoration_condition | Roadway restoration condition | invariant | Condition requires pavement, markings, sidewalk, curb and utility restoration after closure. | close properly |
| closureops.notifications.public_notice | Public closure notice | invariant | Notice informs residents, businesses and road users of dates, limits, detours and contacts. | prepare public |
| closureops.notifications.agency_notice | Agency closure notice | invariant | Notice goes to police, fire, EMS, transit, schools, sanitation and traffic operations. | coordinate services |
| closureops.notifications.variable_message_sign | Variable message sign notice | variant | Sign warns drivers before closure with dates, route impact and detour guidance. | reduce surprise |
| closureops.notifications.stakeholder_log | Closure stakeholder log | invariant | Log records who was notified, when, method, concerns and follow-up commitments. | prove outreach |
| closureops.inspection.pre_closure_inspection | Pre-closure inspection | invariant | Inspection verifies posted signs, barricades, detour setup, access, permits and site readiness. | start safely |
| closureops.inspection.active_closure_inspection | Active closure inspection | invariant | Inspection checks compliance, barrier placement, traffic queues, pedestrian route and work limits. | monitor closure |
| closureops.inspection.after_hours_check | After-hours closure check | variant | Check verifies unattended closures remain safe, lit, signed, secured and passable. | overnight safety |
| closureops.inspection.noncompliance_notice | Closure noncompliance notice | invariant | Notice documents missing signs, unsafe setup, wrong hours, blocked access or expired permit. | correct issue |
| closureops.extensions.extension_request | Road closure extension request | invariant | Request explains reason, added dates, revised impacts, updated notices and traffic plan changes. | extend lawfully |
| closureops.extensions.extension_review | Extension review | invariant | Review checks conflicts, performance history, public impact, safety and revised conditions. | control duration |
| closureops.extensions.emergency_extension | Emergency closure extension | variant | Extension covers unexpected utility failure, collapse, weather, crash or safety condition. | manage urgent need |
| closureops.enforcement.stop_work_order | Closure stop-work order | invariant | Order halts activity when permit, safety, access or traffic control conditions are violated. | enforce safety |
| closureops.enforcement.fee_penalty | Closure fee or penalty | variant | Fee covers permit charge, late extension, inspection cost, lane rental or violation penalty. | recover cost |
| closureops.enforcement.permit_revocation | Closure permit revocation | variant | Revocation cancels authorization for serious unsafe, unauthorized or repeated violations. | protect network |
| closureops.operations.emergency_closure | Emergency road closure | invariant | Closure blocks unsafe road after crash, fire, flood, sinkhole, utility break or structural hazard. | immediate safety |
| closureops.operations.special_event_closure | Special event road closure | variant | Closure supports parades, races, markets or festivals with crowd control and access planning. | event operations |
| closureops.operations.utility_work_closure | Utility work road closure | variant | Closure supports excavation, service connection, pole work, trenching or emergency repair. | utility access |
| closureops.data.permit_map_layer | Road closure permit map layer | invariant | Layer displays active, planned and expired closures with limits, dates, detours and contacts. | shared awareness |
| closureops.data.closure_history | Road closure history | invariant | History records approved closures, durations, violations, complaints, extensions and restoration. | learn patterns |
| closureops.reporting.weekly_closure_report | Weekly closure report | variant | Report summarizes upcoming closures, conflicts, major impacts, extensions and special conditions. | coordinate city |
| closureops.reporting.closeout_report | Road closure closeout report | invariant | Report confirms removal of control devices, restoration, inspection, complaints and final status. | finish permit |
| closureops.metrics.closure_compliance_rate | Closure compliance rate KPI | invariant | KPI measures inspections passed versus violations by contractor, work type and location. | improve compliance |
| closureops.metrics.network_impact_hours | Network impact hours KPI | variant | KPI counts lane or road closure hours weighted by road importance and traffic impact. | manage disruption |
| closureops.close.permit_closeout | Road closure permit closeout | invariant | Closeout verifies work complete, site restored, fees settled, records updated and permit closed. | administrative closure |
