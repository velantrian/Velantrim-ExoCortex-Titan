# BATCH_199 — Security Guard Operations Detail
# world_skills_core · source: world_skills_core:batch_199:security_guard_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| guardops.post.post_order | Security post order | invariant | Post order defines duties, authority, patrols, contacts, alarms, access rules and reporting. | guard playbook |
| guardops.post.shift_briefing | Security shift briefing | invariant | Briefing shares risks, events, banned persons, maintenance issues and special instructions. | start informed |
| guardops.post.uniform_check | Guard uniform check | variant | Check confirms identification, equipment, radio, keys, PPE and professional appearance. | visible authority |
| guardops.post.key_control | Security key control | invariant | Control records issue, return, holder, time, purpose and missing-key escalation. | protect access |
| guardops.post.post_relief | Guard post relief | invariant | Relief transfers responsibility, logs, keys, radio and active incidents between guards. | no gap in coverage |
| guardops.patrol.patrol_route | Security patrol route | invariant | Route defines checkpoints, timing, areas, hazards and observation points. | systematic coverage |
| guardops.patrol.checkpoint_scan | Patrol checkpoint scan | variant | Scan proves guard visited location at time and may capture exception notes. | patrol evidence |
| guardops.patrol.randomization | Patrol randomization | variant | Randomization varies timing or route to reduce predictability. | deterrence |
| guardops.patrol.observation_note | Security observation note | invariant | Note records unusual condition, person, vehicle, door, leak, fire risk or safety issue. | eyes on site |
| guardops.patrol.patrol_exception | Patrol exception | invariant | Exception explains missed checkpoint, unsafe area, emergency diversion or access barrier. | transparent variance |
| guardops.access.visitor_checkin | Security visitor check-in | invariant | Check-in verifies identity, purpose, host, badge, time and access area. | controlled entry |
| guardops.access.badge_issue | Temporary badge issue | invariant | Issue records badge number, visitor, host, valid area and return. | temporary identity |
| guardops.access.delivery_access | Delivery access control | variant | Control verifies carrier, manifest, dock assignment, vehicle and recipient. | manage logistics entry |
| guardops.access.tailgating | Tailgating prevention | invariant | Prevention stops unauthorized person following authorized entry through controlled door. | access integrity |
| guardops.access.deny_entry | Entry denial | invariant | Denial records reason, person, supervisor contact and escalation when entry is refused. | lawful boundary |
| guardops.alarm.alarm_response | Alarm response | invariant | Response follows procedure for fire, intrusion, duress, equipment or environmental alarm. | act on signal |
| guardops.alarm.false_alarm | False alarm record | invariant | Record notes cause, system, area, response time and corrective action. | reduce noise |
| guardops.alarm.cctv_review | CCTV review request | variant | Request defines camera, time window, reason, authorization and evidence handling. | controlled video use |
| guardops.alarm.door_forced | Forced-door alarm | invariant | Alarm indicates door opened without valid credential or request-to-exit sequence. | investigate access breach |
| guardops.alarm.dispatch_escalation | Security dispatch escalation | invariant | Escalation contacts supervisor, facilities, police, fire, medical or client contact per protocol. | right help fast |
| guardops.incident.incident_report | Security incident report | invariant | Report documents who, what, where, when, actions, witnesses, evidence and notifications. | formal record |
| guardops.incident.use_of_force_report | Use-of-force report | variant | Report records force type, reason, injuries, witnesses, policy basis and review path. | high-risk accountability |
| guardops.incident.trespass_case | Trespass case | variant | Case documents unauthorized presence, warning, removal, law enforcement contact and future restriction. | repeat prevention |
| guardops.incident.medical_assist | Security medical assist | variant | Assist records observed emergency, first aid limits, EMS call and handoff. | support without clinical overreach |
| guardops.incident.property_damage | Property damage incident | invariant | Incident records location, photos, asset, suspected cause, immediate controls and notification. | preserve evidence |
| guardops.emergency.evacuation_support | Evacuation support | invariant | Support helps direct occupants, keep routes clear, report hazards and account for assigned area. | emergency role |
| guardops.emergency.lockdown_support | Lockdown support | variant | Support follows site procedure for access control, communication and safe positioning. | threat response |
| guardops.emergency.fire_watch | Fire watch | variant | Watch monitors area when fire system impairment or hot work requires human surveillance. | temporary protection |
| guardops.emergency.severe_weather | Severe weather procedure | variant | Procedure guides shelter, access restriction, patrol suspension and communication during weather threat. | protect people |
| guardops.emergency.emergency_drill | Security emergency drill | invariant | Drill tests guard role, communications, timing, reporting and corrective actions. | practice before crisis |
| guardops.communication.radio_protocol | Security radio protocol | invariant | Protocol uses clear calls, location, priority, acknowledgments and concise updates. | shared awareness |
| guardops.communication.daily_activity_report | Daily activity report | invariant | Report summarizes patrols, visitors, incidents, alarms, issues and handovers. | client visibility |
| guardops.communication.escalation_tree | Security escalation tree | invariant | Tree lists who to notify by event type, time, severity and site. | no guessing |
| guardops.communication.confidential_info | Security confidential information | invariant | Sensitive names, investigations, camera footage and access data are shared only by need. | privacy and trust |
| guardops.communication.client_update | Client security update | variant | Update informs client contact about incidents, risks, service issue or corrective action. | align expectations |
| guardops.safety.personal_safety | Guard personal safety | invariant | Safety covers distance, lighting, backup, communication, PPE and avoiding unnecessary confrontation. | guard comes home |
| guardops.safety.deescalation | De-escalation | invariant | De-escalation uses calm communication, space, listening and options to reduce conflict. | lower risk |
| guardops.safety.prohibited_action | Prohibited guard action | invariant | Prohibition limits searches, detention, pursuit, force or advice outside law and policy. | boundaries matter |
| guardops.safety.lone_post_check | Lone post welfare check | variant | Check confirms guard safety and alertness during isolated or overnight work. | protect lone worker |
| guardops.safety.hazard_report | Security hazard report | invariant | Report flags unsafe conditions found during patrol or post duty. | safety feedback |
| guardops.admin.training_record | Guard training record | invariant | Record tracks licensing, site orientation, emergency procedures, de-escalation and equipment training. | qualified coverage |
| guardops.admin.license_expiry | Guard license expiry | invariant | Expiry tracking prevents assignment of unlicensed or unauthorized guard. | compliance |
| guardops.metrics.security_kpi | Security operations KPI | variant | KPI tracks incidents, response time, patrol completion, alarm rate, access exceptions and client issues. | manage service |
| guardops.continuity.staffing_gap | Security staffing gap | invariant | Gap procedure covers replacement, overtime, post prioritization and client notification. | maintain coverage |
