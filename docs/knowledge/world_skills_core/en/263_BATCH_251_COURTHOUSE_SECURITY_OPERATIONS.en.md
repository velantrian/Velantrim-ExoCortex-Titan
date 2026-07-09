# BATCH_251 — Courthouse Security Operations Detail
# world_skills_core · source: world_skills_core:batch_251:courthouse_security_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| courtsec.screening.entry_queue | Courthouse entry queue | invariant | Queue separates visitors, staff, attorneys, jurors and deliveries by screening lane. | manage entry |
| courtsec.screening.magnetometer_check | Courthouse magnetometer check | invariant | Check routes person through detector, secondary search and clearance decision. | detect hazards |
| courtsec.screening.xray_bag | Courthouse bag x-ray | invariant | X-ray screens bags, packages, folders and electronics for prohibited items. | inspect property |
| courtsec.screening.secondary_search | Courthouse secondary search | invariant | Search resolves alarm, unclear image or suspicious item with documented staff action. | clear exception |
| courtsec.screening.accessibility_screen | Accessible courthouse screening | variant | Screening adapts process for mobility devices, medical devices, interpreters or support persons. | inclusive entry |
| courtsec.access.staff_credential | Courthouse staff credential | invariant | Credential verifies employee, judge, contractor or authorized worker access level. | control staff access |
| courtsec.access.attorney_access | Courthouse attorney access | variant | Access recognizes attorney credentials, client materials, courtroom limits and security rules. | professional flow |
| courtsec.access.juror_checkin | Courthouse juror security check-in | variant | Check-in directs jurors through screening, waiting area, badges and reporting room. | jury flow |
| courtsec.access.restricted_area | Courthouse restricted area control | invariant | Control protects chambers, clerk back office, holding cells, evidence rooms and secure corridors. | protect zones |
| courtsec.access.afterhours_access | Courthouse after-hours access | variant | Access records authorized person, time, reason, escort, alarm and exit. | secure building |
| courtsec.prohibited.item_policy | Courthouse prohibited item policy | invariant | Policy defines weapons, tools, sprays, cameras, food or other restricted articles. | consistent rules |
| courtsec.prohibited.item_disposition | Prohibited item disposition | invariant | Disposition records return-to-car, surrender, locker, seizure or law enforcement referral. | resolve item |
| courtsec.prohibited.weapon_find | Courthouse weapon finding | invariant | Finding secures weapon, separates person, notifies supervisor and records incident. | prevent harm |
| courtsec.prohibited.evidence_exception | Courthouse evidence item exception | variant | Exception permits controlled entry of case evidence through authorization and custody. | support proceedings |
| courtsec.courtroom.courtroom_post | Courtroom security post | invariant | Post assignment lists courtroom, officer, judge, case risk, entrances and relief. | cover hearings |
| courtsec.courtroom.high_profile_case | High-profile case security | variant | Plan covers crowds, media, parties, threats, seating, escorts and overflow rooms. | reduce disruption |
| courtsec.courtroom.disruption_response | Courtroom disruption response | invariant | Response manages shouting, threats, refusal, filming, protest or medical issue. | restore order |
| courtsec.courtroom.no_contact_seating | Courtroom no-contact seating | variant | Seating separates protected persons, witnesses, defendants and families under court order. | reduce intimidation |
| courtsec.courtroom.judge_escort | Judge escort | variant | Escort moves judge between chambers, bench, parking or secure area when risk requires. | protect judiciary |
| courtsec.prisoner.sally_port | Courthouse sally port | invariant | Sally port controls prisoner vehicle entry, doors, search, handoff and logs. | secure transfer |
| courtsec.prisoner.holding_cell | Courthouse holding cell | invariant | Cell operation tracks occupancy, checks, separation, property and movement. | safe custody |
| courtsec.prisoner.prisoner_movement | Courthouse prisoner movement | invariant | Movement records route, restraints, escort staff, time, destination and return. | custody control |
| courtsec.prisoner.medical_alert | Prisoner medical alert at court | variant | Alert communicates known medical, mobility or medication concern to custody staff. | safe handling |
| courtsec.prisoner.escape_alarm | Courthouse escape alarm | invariant | Alarm locks routes, alerts agencies, preserves scene and starts search protocol. | emergency response |
| courtsec.incident.threat_report | Courthouse threat report | invariant | Report records threat source, target, words, evidence, risk review and notification. | risk management |
| courtsec.incident.assault_response | Courthouse assault response | invariant | Response secures scene, separates parties, requests medical care and documents witnesses. | protect people |
| courtsec.incident.medical_call | Courthouse medical call | invariant | Call records symptoms, location, aid, EMS, witnesses and room status. | care trail |
| courtsec.incident.public_disturbance | Courthouse public disturbance | variant | Disturbance handling manages protest, crowding, shouting or refusal outside courtroom. | maintain order |
| courtsec.incident.lost_child | Courthouse lost child response | variant | Response secures exits, broadcasts description, checks rooms and reunites guardian. | rapid resolution |
| courtsec.emergency.evacuation_plan | Courthouse evacuation plan | invariant | Plan defines exits, assembly, prisoner handling, judges, staff and public guidance. | emergency readiness |
| courtsec.emergency.lockdown | Courthouse lockdown | invariant | Lockdown secures entrances, courtrooms, chambers, holding areas and communication. | contain threat |
| courtsec.emergency.fire_alarm | Courthouse fire alarm response | invariant | Response evacuates or shelters per plan, secures custody and reports all-clear. | life safety |
| courtsec.emergency.suspicious_package | Courthouse suspicious package response | invariant | Response isolates package, clears area, notifies specialists and documents timeline. | reduce risk |
| courtsec.records.daily_log | Courthouse security daily log | invariant | Log records posts, staffing, incidents, screening volumes, alarms and unusual activity. | shift record |
| courtsec.records.visitor_count | Courthouse visitor count | variant | Count tracks public flow by entrance, time, hearing load and security staffing. | capacity planning |
| courtsec.records.camera_review | Courthouse camera review | variant | Review retrieves video for incident, request, investigation or quality check. | evidence support |
| courtsec.records.key_control | Courthouse security key control | invariant | Control tracks keys, cards, radios, panic devices, checkout and return. | asset custody |
| courtsec.staff.post_orders | Courthouse post orders | invariant | Orders describe duties, routes, alarms, contacts, escalation and local rules. | consistent work |
| courtsec.staff.shift_briefing | Courthouse security shift briefing | invariant | Briefing covers cases, risks, closures, equipment, staffing and incidents from prior shift. | align team |
| courtsec.staff.training_record | Courthouse security training record | invariant | Record tracks screening, de-escalation, custody, emergency, legal limits and equipment. | qualified staff |
| courtsec.quality.screening_audit | Courthouse screening audit | variant | Audit reviews lane operation, item handling, alarms, courtesy and documentation. | improve screening |
| courtsec.reporting.security_summary | Courthouse security summary | invariant | Summary reports incidents, threats, weapons, disruptions, staffing gaps and trends. | leadership awareness |
| courtsec.metrics.courtsec_kpi | Courthouse security KPI | variant | KPI tracks screening volume, wait time, incidents, contraband, response time and audits. | manage security |
| courtsec.continuity.system_outage | Courthouse security system outage | invariant | Outage plan covers magnetometer, camera, access control, radio or alarm failure. | maintain security |
