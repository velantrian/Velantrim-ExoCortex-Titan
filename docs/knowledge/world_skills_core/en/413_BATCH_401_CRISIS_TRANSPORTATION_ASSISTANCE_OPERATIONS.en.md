# BATCH 401: Crisis Transportation Assistance Operations

**KnowledgeUnits:** 44  
**Namespace:** `crisistransportops.*`  
**Scope:** requests, eligibility, routing, vouchers, accessible vehicles, safety and reconciliation.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| crisistransportops.intake.request_source | request source | RECORD | Source records shelter, hotline, clinic, caseworker, school, outreach or public desk. | Shows origin. |
| crisistransportops.intake.trip_purpose | trip purpose | RECORD | Purpose distinguishes shelter, medical, benefits, food, reunification, work or evacuation trip. | Routes service. |
| crisistransportops.intake.origin_destination | origin destination | RECORD | Record captures pickup, destination, time window, contact and access constraints. | Defines trip. |
| crisistransportops.intake.passenger_count | passenger count | MEASUREMENT | Count includes adults, children, caregivers, pets, luggage and equipment. | Selects vehicle. |
| crisistransportops.eligibility.criteria | eligibility criteria | CONSTRAINT | Criteria define disaster impact, income, referral source, trip purpose and service area. | Preserves fairness. |
| crisistransportops.eligibility.priority | priority model | MODEL | Priority weighs life safety, medical appointment, shelter access, disability and time sensitivity. | Orders requests. |
| crisistransportops.eligibility.exception | exception record | RECORD | Exception records unusual need, approval, reason and limits. | Allows flexibility. |
| crisistransportops.eligibility.duplicate_check | duplicate check | QUALITY_CHECK | Duplicate check links repeated trip requests and prevents double voucher issue. | Protects resources. |
| crisistransportops.routing.mode_match | mode match | METHOD | Mode match selects bus, paratransit, rideshare, taxi, shuttle, nonprofit van or fuel card. | Fits need. |
| crisistransportops.routing.route_plan | route plan | METHOD | Plan groups trips by geography, urgency, capacity and road conditions. | Improves throughput. |
| crisistransportops.routing.pickup_window | pickup window | RECORD | Window records earliest/latest pickup, driver instructions and contact backup. | Reduces misses. |
| crisistransportops.routing.road_status | road status | CONSTRAINT | Road status checks closures, flood, debris, security and weather. | Keeps trips feasible. |
| crisistransportops.accessible.vehicle_need | accessible vehicle need | RECORD | Need records wheelchair, lift, stretcher, low-step, service animal or caregiver support. | Selects accessible transport. |
| crisistransportops.accessible.device_space | device space | SAFETY_RULE | Vehicle must fit mobility devices, oxygen, luggage and securement needs. | Prevents unsafe loading. |
| crisistransportops.accessible.driver_brief | driver brief | METHOD | Brief explains assistance level, communication need and safe boarding procedure. | Improves service. |
| crisistransportops.accessible.no_accessible_vehicle | no accessible vehicle | RECORD | Gap record captures wait time, alternative, escalation and resident update. | Exposes unmet need. |
| crisistransportops.voucher.voucher_issue | voucher issue | RECORD | Voucher records amount, vendor, trip purpose, rider, expiration and restrictions. | Controls subsidy. |
| crisistransportops.voucher.fuel_card | fuel card | RECORD | Fuel card issue records vehicle, amount, eligibility, purpose and receipt expectation. | Supports self-transport. |
| crisistransportops.voucher.ride_code | ride code | RECORD | Ride code tracks platform, limit, origin/destination rule and activation time. | Enables digital rides. |
| crisistransportops.voucher.cancellation | cancellation rule | METHOD | Cancellations reclaim unused voucher or record reason for no-show. | Prevents waste. |
| crisistransportops.safety.driver_check | driver check | QUALITY_CHECK | Provider checks driver credential, vehicle status, insurance and dispatch contact. | Protects riders. |
| crisistransportops.safety.child_transport | child transport | SAFETY_RULE | Child transport follows guardian, seat, school or reunification rules. | Prevents unsafe release. |
| crisistransportops.safety.medical_trip | medical trip safety | SAFETY_RULE | Medical trips define when EMS, non-emergency medical transport or regular ride is appropriate. | Avoids under-response. |
| crisistransportops.safety.incident_report | incident report | RECORD | Incident records crash, no-show, threat, medical event, lost rider or complaint. | Supports review. |
| crisistransportops.dispatch.assignment | dispatch assignment | RECORD | Assignment names provider, driver/vehicle if known, pickup time and trip ID. | Executes trip. |
| crisistransportops.dispatch.rider_notify | rider notification | METHOD | Rider receives pickup window, vehicle info, contact, cost and cancellation rule. | Sets expectations. |
| crisistransportops.dispatch.provider_update | provider update | METHOD | Provider receives changes, delays, accessibility notes and route hazards. | Keeps trip aligned. |
| crisistransportops.dispatch.failed_pickup | failed pickup | RECORD | Failed pickup records cause, attempts, driver note and next action. | Enables reschedule. |
| crisistransportops.records.trip_log | trip log | RECORD | Trip log stores intake, eligibility, assignment, completion, cost and incident notes. | Creates audit trail. |
| crisistransportops.records.receipt | receipt record | RECORD | Receipt captures vendor charge, voucher use, fuel proof or reimbursement support. | Supports finance. |
| crisistransportops.records.privacy | privacy rule | SAFETY_RULE | Trip data hides sensitive destinations where safety or medical privacy requires. | Protects riders. |
| crisistransportops.records.retention | retention rule | CONSTRAINT | Records follow emergency, finance, grant and privacy schedules. | Preserves audit. |
| crisistransportops.reconcile.vendor_invoice | vendor invoice | QUALITY_CHECK | Invoice reconciles trip IDs, fares, cancellations, wait fees and authorized limits. | Prevents overpayment. |
| crisistransportops.reconcile.voucher_balance | voucher balance | MEASUREMENT | Balance tracks issued, used, expired, canceled and remaining voucher funds. | Shows funds. |
| crisistransportops.reconcile.exception_review | exception review | QUALITY_CHECK | Review checks trips outside limits, duplicate riders and unusual costs. | Controls misuse. |
| crisistransportops.reconcile.grant_code | grant code | RECORD | Grant code links trips to eligible funding source and documentation. | Supports reimbursement. |
| crisistransportops.communication.public_info | public information | METHOD | Public info explains who can request rides, purposes, hours and limits. | Guides residents. |
| crisistransportops.communication.partner_referral | partner referral | METHOD | Partners use referral form with eligibility, destination and accessibility fields. | Standardizes requests. |
| crisistransportops.communication.language | language support | METHOD | Calls and notices use interpreter or translated scripts when needed. | Improves access. |
| crisistransportops.communication.shortage | shortage message | METHOD | Shortage notice explains delays, alternatives, priority rules and callback timing. | Reduces frustration. |
| crisistransportops.metrics.completed_trips | completed trips | MEASUREMENT | Completed trips count rides delivered by purpose, mode, area and provider. | Shows output. |
| crisistransportops.metrics.wait_time | wait time | MEASUREMENT | Wait time measures request to assignment and pickup. | Reveals bottleneck. |
| crisistransportops.metrics.no_show_rate | no-show rate | MEASUREMENT | No-show rate tracks rider, driver or provider failures. | Improves dispatch. |
| crisistransportops.review.after_action | after-action review | METHOD | Review captures eligibility, routing, accessible vehicle gaps, voucher controls and safety lessons. | Improves future transport. |
