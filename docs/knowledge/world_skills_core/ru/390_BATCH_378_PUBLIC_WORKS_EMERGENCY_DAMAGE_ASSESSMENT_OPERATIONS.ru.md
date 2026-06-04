# BATCH 378: Public Works Emergency Damage Assessment Operations

**KnowledgeUnits:** 44  
**Namespace:** `pwdamageops.*`  
**Scope:** rapid assessments, asset tagging, estimates, safety, documentation and reporting.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| pwdamageops.activation.trigger | assessment trigger | MODEL | Trigger includes storm, flood, earthquake, fire, crash, outage or infrastructure failure. | Starts organized inspection. |
| pwdamageops.activation.team_roster | team roster | RECORD | Roster lists inspectors, engineers, GIS, safety and admin roles. | Assigns work. |
| pwdamageops.activation.priority_map | priority map | METHOD | Map ranks critical routes, utilities, bridges, public buildings and hazards. | Sends teams first where risk is high. |
| pwdamageops.activation.safety_brief | safety briefing | SAFETY_RULE | Brief covers downed wires, unstable structures, floodwater, traffic, PPE and communications. | Protects assessors. |
| pwdamageops.intake.asset_id | asset ID | RECORD | Asset ID links road, bridge, culvert, building, pump, sign, light or facility. | Grounds damage in inventory. |
| pwdamageops.intake.location | location capture | METHOD | Location records address, GPS, milepost, intersection or GIS feature. | Enables repair dispatch. |
| pwdamageops.intake.report_source | report source | RECORD | Source distinguishes field crew, 311, police, resident, sensor or partner agency. | Shows discovery path. |
| pwdamageops.intake.initial_condition | initial condition | RECORD | Initial condition describes visible damage, hazard and service impact. | Starts assessment trail. |
| pwdamageops.rapid.windshield | windshield survey | METHOD | Windshield survey quickly scans routes or neighborhoods for obvious damage. | Gives early situational picture. |
| pwdamageops.rapid.safety_tag | safety tag | RECORD | Tag marks asset as open, restricted, closed, unsafe or needs specialist review. | Communicates immediate use status. |
| pwdamageops.rapid.photo | photo documentation | RECORD | Photos capture damage, context, scale and access constraints. | Supports estimates and claims. |
| pwdamageops.rapid.access_limit | access limit | CONSTRAINT | Some sites wait for water recession, utility clearance or security. | Prevents unsafe inspection. |
| pwdamageops.detail.damage_category | damage category | RECORD | Category distinguishes pavement, structure, drainage, electrical, mechanical, debris or erosion. | Routes expertise. |
| pwdamageops.detail.severity | severity rating | MODEL | Severity considers safety, service loss, structural risk and repair complexity. | Prioritizes repair. |
| pwdamageops.detail.cause | cause note | RECORD | Cause notes flood, wind, impact, overload, fire, earth movement or preexisting condition. | Supports reimbursement logic. |
| pwdamageops.detail.temporary_measure | temporary measure | METHOD | Barricade, shoring, pump, patch, detour or signage may stabilize site. | Reduces immediate risk. |
| pwdamageops.estimates.quantity | quantity estimate | MEASUREMENT | Quantities measure debris, asphalt, pipe, guardrail, signs, labor or equipment. | Supports cost estimate. |
| pwdamageops.estimates.cost | cost estimate | MEASUREMENT | Estimate uses unit prices, labor, equipment, materials and contractor assumptions. | Plans funding. |
| pwdamageops.estimates.confidence | confidence level | MODEL | Confidence notes rapid, preliminary, engineer-reviewed or final estimate. | Prevents false precision. |
| pwdamageops.estimates.update | estimate update | METHOD | Estimates update after detailed inspection, bids, hidden damage or scope change. | Keeps finance realistic. |
| pwdamageops.safety.closure | closure decision | SAFETY_RULE | Closure is based on unsafe condition, structural doubt, flooding, wires or traffic hazard. | Protects public. |
| pwdamageops.safety.detour | detour setup | METHOD | Detour identifies route, signs, accessibility, emergency access and duration. | Maintains mobility. |
| pwdamageops.safety.utility_clearance | utility clearance | SAFETY_RULE | Work waits for gas, electric, water or telecom clearance when needed. | Prevents secondary harm. |
| pwdamageops.safety.reentry | reentry rule | CONSTRAINT | Reentry to damaged facility follows structural, environmental and safety clearance. | Protects staff. |
| pwdamageops.documentation.field_form | field form | RECORD | Form captures asset, damage, photos, quantities, safety status and assessor. | Standardizes data. |
| pwdamageops.documentation.gis_update | GIS update | METHOD | Damage points update map layers for command and repair teams. | Makes status visible. |
| pwdamageops.documentation.time_log | time log | RECORD | Staff and equipment time are recorded by incident and asset. | Supports reimbursement. |
| pwdamageops.documentation.evidence_pack | evidence package | RECORD | Package includes before/after photos, maps, costs, work orders and approvals. | Supports claims. |
| pwdamageops.reporting.sitrep | situation report | RECORD | Sitrep summarizes damaged assets, closures, priorities, costs and unmet needs. | Feeds emergency management. |
| pwdamageops.reporting.public_status | public status | METHOD | Public status communicates closures, detours, hazards and repair estimates. | Keeps residents informed. |
| pwdamageops.reporting.state_federal | state/federal report | METHOD | Reports meet assistance program fields and deadlines. | Enables funding. |
| pwdamageops.reporting.dashboard | damage dashboard | MEASUREMENT | Dashboard tracks open assessments, severity, costs and repair status. | Supports management. |
| pwdamageops.repair.work_order | repair work order | RECORD | Work order links assessment, scope, crew/contractor, priority and status. | Moves from assessment to action. |
| pwdamageops.repair.temporary_repair | temporary repair | METHOD | Temporary repair restores minimal safe service until permanent fix. | Speeds recovery. |
| pwdamageops.repair.permanent_repair | permanent repair scope | METHOD | Permanent scope addresses full repair, standards, permits and resilience. | Restores asset properly. |
| pwdamageops.repair.close_verification | close verification | QUALITY_CHECK | Completed repair is checked against assessment and safety status. | Confirms closure. |
| pwdamageops.qa.duplicate_asset | duplicate asset check | QUALITY_CHECK | Duplicate checks prevent multiple records for same damage. | Keeps counts accurate. |
| pwdamageops.qa.field_review | field review | QUALITY_CHECK | Supervisors review high-cost, closed or unclear assessments. | Improves reliability. |
| pwdamageops.qa.eligibility_review | eligibility review | QUALITY_CHECK | Damage is reviewed for incident relation and reimbursement eligibility. | Protects claims. |
| pwdamageops.records.retention | retention rule | CONSTRAINT | Records follow disaster, asset, finance and grant schedules. | Keeps audit trail. |
| pwdamageops.metrics.assessment_rate | assessment rate | MEASUREMENT | Rate tracks assets assessed per day/team. | Shows progress. |
| pwdamageops.metrics.cost_total | cost total | MEASUREMENT | Total estimated damage by asset class and area supports planning. | Guides funding requests. |
| pwdamageops.demob.transition | transition to recovery | METHOD | Open items transfer from emergency assessment to capital, maintenance or claims teams. | Prevents dropped repairs. |
| pwdamageops.review.after_action | after-action review | METHOD | Review captures map gaps, forms, safety issues, estimate accuracy and repair handoff. | Improves next event. |
