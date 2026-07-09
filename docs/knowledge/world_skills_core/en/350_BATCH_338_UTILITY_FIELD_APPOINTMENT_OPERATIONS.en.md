# BATCH 338: Utility Field Appointment Operations

**KnowledgeUnits:** 44  
**Namespace:** `fieldapptops.*`  
**Scope:** scheduling, access windows, technician dispatch, customer readiness, missed visits, safety and closeout.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| fieldapptops.intake.appointment_need | appointment need | RECORD | Appointment reason records meter, inspection, leak, service start, repair or customer request. | Defines crew skill and time need. |
| fieldapptops.intake.contact_confirm | contact confirmation | QUALITY_CHECK | Phone, email, address and preferred channel are verified before scheduling. | Reduces missed visits. |
| fieldapptops.intake.access_requirements | access requirements | RECORD | Case captures gate codes, pets, interior access, tenant presence and keys. | Field work depends on access. |
| fieldapptops.scheduling.window | access window | RECORD | Appointment window gives date, time range, location and customer obligations. | Sets shared expectation. |
| fieldapptops.scheduling.capacity | schedule capacity | MODEL | Capacity depends on crew count, geography, job duration and emergency load. | Avoids overbooking. |
| fieldapptops.scheduling.priority | priority rule | DECISION_RULE | Safety, outage, leak and regulatory deadlines can override routine windows. | Keeps urgent work ahead. |
| fieldapptops.scheduling.reschedule | reschedule process | METHOD | Reschedules preserve history, reason, customer notice and new window. | Keeps accountability. |
| fieldapptops.dispatch.technician_match | technician match | METHOD | Job is assigned by skill, tools, certifications, vehicle and route. | Improves first-visit completion. |
| fieldapptops.dispatch.route_optimization | route optimization | METHOD | Route groups appointments by area, priority, time windows and travel. | Reduces windshield time. |
| fieldapptops.dispatch.same_day | same-day add-on | DECISION_RULE | Same-day jobs require capacity, parts and customer readiness check. | Prevents schedule collapse. |
| fieldapptops.dispatch.status_updates | status updates | RECORD | Technician status shows assigned, en route, on site, delayed, complete or exception. | Call center can answer customer questions. |
| fieldapptops.customer.readiness_notice | readiness notice | METHOD | Notice tells customer to clear meter, secure pets, be present or provide access. | Raises completion rate. |
| fieldapptops.customer.arrival_notice | arrival notice | METHOD | Customer receives reminder or en-route notification when supported. | Reduces no-access. |
| fieldapptops.customer.no_show_customer | customer no-show | FAILURE_MODE | No-show is recorded with time, contact attempts and site evidence. | Supports fees or reschedule policy. |
| fieldapptops.customer.special_needs | special needs | RECORD | Accessibility, language or medical needs are captured for field visit. | Makes service safer and fairer. |
| fieldapptops.site.address_verify | address verification | SAFETY_RULE | Technician verifies address, meter and work order before action. | Prevents wrong-property work. |
| fieldapptops.site.hazard_scan | hazard scan | SAFETY_RULE | Site is checked for dogs, traffic, electrical, confined space, weather and unsafe structures. | Protects technician. |
| fieldapptops.site.property_protection | property protection | METHOD | Mats, covers, photos and careful routing reduce property damage. | Prevents claims. |
| fieldapptops.site.permission | permission to enter | CONSTRAINT | Interior or fenced access requires customer permission or legal authority. | Protects privacy and legality. |
| fieldapptops.work.precheck | work precheck | METHOD | Technician reviews task, parts, account notes, history and safety flags before arrival. | Reduces surprises. |
| fieldapptops.work.parts_ready | parts readiness | QUALITY_CHECK | Needed meters, endpoints, tools, seals or forms are confirmed. | Avoids failed visits from missing materials. |
| fieldapptops.work.scope_control | scope control | DECISION_RULE | Technician distinguishes scheduled task from new customer requests. | Prevents uncontrolled work expansion. |
| fieldapptops.work.field_decision | field decision | METHOD | Field staff may complete, defer, escalate, create follow-up or mark no access. | Standardizes outcomes. |
| fieldapptops.missed.no_access | no-access code | RECORD | No-access reasons include locked gate, no adult, unsafe site, dog, buried meter or wrong address. | Makes missed visits analyzable. |
| fieldapptops.missed.trip_fee | trip fee rule | CONSTRAINT | Policy defines when missed appointment fees apply. | Keeps customer charges consistent. |
| fieldapptops.missed.followup | missed-visit follow-up | METHOD | Customer receives reason, evidence, fee if any and reschedule path. | Closes communication gap. |
| fieldapptops.safety.lone_worker | lone worker | SAFETY_RULE | Lone worker procedures define check-ins, panic options and escalation. | Field appointments can be isolated. |
| fieldapptops.safety.aggressive_customer | aggressive customer | SAFETY_RULE | Hostile behavior triggers withdrawal, supervisor notice and safety flag. | Protects employees. |
| fieldapptops.safety.traffic_control | traffic control | METHOD | Street appointments use cones, vests, signs and vehicle positioning. | Prevents roadside injury. |
| fieldapptops.safety.weather | weather delay | DECISION_RULE | Lightning, ice, heat or flooding can postpone appointment. | Safety overrides schedule. |
| fieldapptops.closeout.completion_code | completion code | RECORD | Completion code states completed, partial, no access, unsafe, parts needed or customer canceled. | Makes backlog accurate. |
| fieldapptops.closeout.work_notes | work notes | RECORD | Notes include action taken, readings, parts, photos, customer contact and next steps. | Supports billing and service follow-up. |
| fieldapptops.closeout.customer_signature | customer signature | RECORD | Signature or acknowledgment may confirm interior work, restoration or refusal. | Reduces disputes. |
| fieldapptops.closeout.followup_order | follow-up order | METHOD | Unfinished work creates linked order with reason, priority and requirements. | Prevents dropped tasks. |
| fieldapptops.records.photo_evidence | photo evidence | RECORD | Photos document access, meter, repair, property condition and no-access reason. | Supports QA and claims. |
| fieldapptops.records.time_tracking | time tracking | MEASUREMENT | Travel, onsite and admin time are recorded by job type. | Improves scheduling model. |
| fieldapptops.records.inventory_use | inventory use | RECORD | Parts and seals used are linked to work order. | Supports stock control. |
| fieldapptops.qa.first_visit_completion | first-visit completion | MEASUREMENT | Metric tracks jobs completed without repeat visit. | Shows schedule and readiness quality. |
| fieldapptops.qa.appointment_accuracy | appointment accuracy | MEASUREMENT | Arrival within window is measured by job class and route. | Supports customer-service promises. |
| fieldapptops.qa.audit | field audit | QUALITY_CHECK | Supervisor audits photos, notes, safety and completion codes. | Keeps field records reliable. |
| fieldapptops.reporting.dashboard | appointment dashboard | RECORD | Dashboard shows scheduled, completed, missed, delayed, canceled and aged jobs. | Gives operations visibility. |
| fieldapptops.reporting.no_access_trend | no-access trend | MODEL | Trends identify neighborhoods, job types or communication gaps causing missed visits. | Guides process improvement. |
| fieldapptops.reporting.customer_impact | customer impact | MEASUREMENT | Reports include wait time, reschedule count and complaint links. | Shows service experience. |
| fieldapptops.review.route_review | route review | METHOD | Dispatch reviews travel time, emergency interruptions and appointment density. | Improves future routing. |
