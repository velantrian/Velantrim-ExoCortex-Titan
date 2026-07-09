# BATCH 330: Utility Service Shutoff and Reconnection Operations

**KnowledgeUnits:** 44  
**Namespace:** `servicedisconnectops.*`  
**Scope:** notices, field orders, valves, safety, customer status, reconnection checks and records.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| servicedisconnectops.notice.policy | shutoff policy | CONSTRAINT | Policy defines allowed reasons, notice periods, exemptions, appeals and reconnection terms. | Prevents arbitrary or unlawful disconnection. |
| servicedisconnectops.notice.pre_notice | pre-shutoff notice | METHOD | Customer receives amount/reason, deadline, assistance options and contact route. | Gives opportunity to resolve before field action. |
| servicedisconnectops.notice.medical | medical or hardship flag | DECISION_RULE | Medical, winter, heat or vulnerable-customer rules may pause or modify shutoff. | Protects public welfare and compliance. |
| servicedisconnectops.notice.language_access | language access | METHOD | Shutoff notices include translated payment, appeal and reconnection instructions where needed. | Reduces wrongful loss of service caused by misunderstanding. |
| servicedisconnectops.order.field_order | field order | RECORD | Field order lists account, address, meter, valve, reason, status and safety notes. | Crew knows exactly what action is authorized. |
| servicedisconnectops.order.last_check | last account check | QUALITY_CHECK | Before dispatch, system checks payment, hold, dispute or arrangement status. | Prevents wrongful shutoff. |
| servicedisconnectops.order.priority | order priority | DECISION_RULE | Priorities distinguish nonpayment, leak, emergency, tamper, move-out and safety shutoff. | Dispatch matches urgency. |
| servicedisconnectops.order.cancel_update | cancellation update | METHOD | Paid or held orders are pulled from crew queue promptly. | Avoids field action after resolution. |
| servicedisconnectops.field.identity | address verification | SAFETY_RULE | Crew verifies address, meter ID and service before operating valve. | Prevents disconnecting wrong customer. |
| servicedisconnectops.field.curb_stop | curb stop operation | METHOD | Service is shut at curb stop or meter valve using appropriate key and care. | Physical control point matters. |
| servicedisconnectops.field.meter_lock | meter lock | METHOD | Lock, plug or tag is installed according to utility standard. | Deters unauthorized reconnection. |
| servicedisconnectops.field.photo_proof | photo proof | RECORD | Photos document valve, lock, meter read, property condition and tag. | Supports disputes and audit. |
| servicedisconnectops.field.final_read | final read | RECORD | Meter read at shutoff is captured. | Supports billing and usage cut-off. |
| servicedisconnectops.valves.inoperable | inoperable valve | FAILURE_MODE | Stuck, buried or leaking shutoff valve creates exception order. | Disconnection may require repair or excavation. |
| servicedisconnectops.valves.leak_after | leak after shutoff | FAILURE_MODE | Valve may leak by, causing continued service or property issue. | Needs repair and account note. |
| servicedisconnectops.valves.private_line | private line risk | CONSTRAINT | Customer-side plumbing condition affects safe shutoff/reconnect. | Crew may need caution with old or fragile plumbing. |
| servicedisconnectops.safety.site_hazard | site hazard | SAFETY_RULE | Dogs, traffic, aggressive behavior, weather and unsafe pits are recorded. | Protects field staff. |
| servicedisconnectops.safety.escalation | safety escalation | METHOD | Unsafe situations route to supervisor, paired crew or law enforcement where policy allows. | Maintains safety without improvisation. |
| servicedisconnectops.safety.confined_pit | confined pit | SAFETY_RULE | Meter pits are assessed for confined-space and fall hazards. | Routine service work can still be dangerous. |
| servicedisconnectops.customer.door_tag | door tag | METHOD | Door tag states action taken, reason, contact and reconnection steps. | Customer knows what happened. |
| servicedisconnectops.customer.status_update | customer status update | RECORD | Account is updated as disconnected, attempted, exception, held or reconnected. | Customer service sees current field status. |
| servicedisconnectops.customer.dispute | dispute handling | METHOD | Customer disputes are routed to billing or supervisor with field facts. | Separates crew action from account decision. |
| servicedisconnectops.reconnect.authorization | reconnect authorization | QUALITY_CHECK | Reconnection requires payment, order clearance, safety check or approved arrangement. | Prevents unauthorized or premature restoration. |
| servicedisconnectops.reconnect.field_order | reconnect order | RECORD | Reconnect order includes account, valve, lock removal, read and customer instructions. | Gives crew clear authority. |
| servicedisconnectops.reconnect.slow_open | slow opening | SAFETY_RULE | Valve is opened slowly to reduce pressure surge and plumbing shock. | Protects customer plumbing. |
| servicedisconnectops.reconnect.leak_check | leak check | INSPECTION | Crew checks visible leaks at meter, setter, curb stop and service area. | Prevents immediate property damage. |
| servicedisconnectops.reconnect.customer_present | customer present | DECISION_RULE | Some reconnections require customer present to avoid interior leaks. | Reduces flood risk in vacant or winterized buildings. |
| servicedisconnectops.reconnect.restore_status | restore status | RECORD | Account status, read, time and crew are recorded after reconnection. | Closes service order. |
| servicedisconnectops.tamper.tamper_flag | tamper flag | RECORD | Broken locks, bypasses, cut seals or reversed meters are documented. | Supports enforcement and billing correction. |
| servicedisconnectops.tamper.evidence | tamper evidence | RECORD | Photos, reads, device condition and prior orders are retained. | Makes tamper case defensible. |
| servicedisconnectops.tamper.safe_response | safe tamper response | SAFETY_RULE | Crew avoids confrontation and follows escalation policy. | Tamper cases can become unsafe. |
| servicedisconnectops.emergency.leak_shutoff | emergency leak shutoff | DECISION_RULE | Active leak, main break, frozen pipe or property damage can trigger urgent shutoff. | Protects property and water system. |
| servicedisconnectops.emergency.fire_protection | fire protection check | CONSTRAINT | Shutoff must consider fire lines, sprinklers or shared services. | Avoids disabling life-safety systems unintentionally. |
| servicedisconnectops.emergency.public_health | public health consideration | DECISION_RULE | Occupied premises, sanitation and local rules may affect shutoff decision. | Utility operations intersect public health. |
| servicedisconnectops.records.audit_trail | audit trail | RECORD | Notice, order, field action, photos, reads, payments and reconnection are linked. | Supports complaints, audits and legal review. |
| servicedisconnectops.records.gis_note | GIS/service note | RECORD | Field discoveries update curb stop location, access issues and valve condition. | Improves future orders. |
| servicedisconnectops.records.exception_queue | exception queue | METHOD | Inoperable valves, unsafe access and disputes remain in queue with owner and next step. | Prevents unresolved cases from disappearing. |
| servicedisconnectops.qa.wrong_address | wrong-address prevention | QUALITY_CHECK | QA compares order, meter serial, GIS and field photo. | Reduces high-impact service mistakes. |
| servicedisconnectops.qa.timeliness | timeliness metric | MEASUREMENT | Time from authorization to field action and reconnection is tracked. | Shows operational performance. |
| servicedisconnectops.qa.sample_audit | sample audit | QUALITY_CHECK | Supervisors audit random shutoff/reconnect files for policy compliance. | Maintains fairness and documentation quality. |
| servicedisconnectops.reporting.volume | order volume report | RECORD | Report counts notices, shutoffs, reconnects, exceptions, tamper and cancellations. | Gives management workload view. |
| servicedisconnectops.reporting.assistance | assistance referral trend | RECORD | Reports track referrals, arrangements and avoided shutoffs where policy supports it. | Shows customer-support impact. |
| servicedisconnectops.reporting.risk | operational risk report | MODEL | Risk combines wrong shutoff, safety incidents, delayed reconnection and valve failures. | Focuses improvement on serious harms. |
| servicedisconnectops.review.after_incident | after-incident review | METHOD | Wrong address, injury, dispute or media event triggers review of notice, order and field steps. | Converts mistakes into process improvement. |
