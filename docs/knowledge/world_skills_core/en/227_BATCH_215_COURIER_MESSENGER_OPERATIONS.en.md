# BATCH_215 — Courier Messenger Operations Detail
# world_skills_core · source: world_skills_core:batch_215:courier_messenger_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| courier.dispatch.job_intake | Courier job intake | invariant | Intake records sender, recipient, address, item type, deadline, service level and contact. | open delivery task |
| courier.dispatch.service_level | Courier service level | invariant | Level defines standard, rush, same-day, scheduled, legal, medical or fragile handling. | priority logic |
| courier.dispatch.zone_assignment | Courier zone assignment | variant | Assignment maps jobs to rider, driver, walking messenger or depot zone. | efficient dispatch |
| courier.dispatch.route_priority | Route priority | invariant | Priority orders pickups and drops by deadline, distance, custody risk and promised service. | deliver on time |
| courier.dispatch.capacity_check | Courier capacity check | invariant | Check verifies vehicle, bag, weight, size, temperature or security capacity. | accept only feasible work |
| courier.pickup.pickup_proof | Pickup proof | invariant | Proof records time, location, sender, signature, photo, barcode or scan. | custody starts |
| courier.pickup.item_count | Pickup item count | invariant | Count verifies envelopes, parcels, bags or totes accepted from sender. | prevent shortage |
| courier.pickup.package_condition | Package condition note | invariant | Note records damage, seal status, wetness, missing label or fragile state at pickup. | baseline evidence |
| courier.pickup.label_scan | Courier label scan | variant | Scan connects physical item to dispatch record and tracking timeline. | item identity |
| courier.pickup.failed_pickup | Failed pickup | invariant | Failure records no item, closed office, wrong address, access denial or cancellation. | explain non-collection |
| courier.custody.chain_of_custody | Courier chain of custody | invariant | Custody log tracks possession, transfer, time, person and condition. | accountable movement |
| courier.custody.sealed_bag | Sealed courier bag | variant | Bag uses tamper-evident seal and recorded seal number for sensitive contents. | protect integrity |
| courier.custody.high_value_item | High-value courier item | variant | Item requires extra authorization, secure handling, proof and exception escalation. | reduce loss risk |
| courier.custody.medical_specimen | Medical specimen courier item | variant | Specimen uses required packaging, temperature, labels and handoff workflow. | special custody |
| courier.custody.legal_document | Legal document courier item | variant | Document delivery may require named recipient, filing deadline, stamp or affidavit. | deadline proof |
| courier.route.route_manifest | Courier route manifest | invariant | Manifest lists stops, sequence, items, contacts, notes and required proofs. | route plan |
| courier.route.dynamic_resequence | Dynamic route resequence | variant | Resequence adjusts route after rush job, traffic, failed stop or deadline change. | stay responsive |
| courier.route.traffic_delay | Courier traffic delay | invariant | Delay records cause, affected jobs, ETA change and customer notice. | manage promise |
| courier.route.secure_parking | Secure parking decision | variant | Decision balances proximity, theft risk, loading rules, vehicle safety and time. | protect items |
| courier.route.multi_stop_batch | Multi-stop batch | invariant | Batch groups pickups or deliveries for efficiency while preserving priority and custody. | route density |
| courier.delivery.delivery_proof | Delivery proof | invariant | Proof records recipient, time, signature, photo, GPS, stamp or scan. | close delivery |
| courier.delivery.named_recipient | Named recipient delivery | variant | Delivery must be handed only to specified person or authorized substitute. | controlled handoff |
| courier.delivery.safe_drop | Safe drop rule | variant | Rule permits unattended delivery only under sender, recipient or service policy. | avoid risky drop |
| courier.delivery.failed_delivery | Failed delivery | invariant | Failure records no access, refused item, wrong address, closed office or recipient unavailable. | next action needed |
| courier.delivery.return_to_sender | Return-to-sender courier flow | invariant | Flow routes undeliverable or refused item back with proof and status update. | close failed job |
| courier.exception.address_issue | Courier address issue | invariant | Issue records missing suite, bad address, inaccessible location or conflicting directions. | solve navigation |
| courier.exception.damaged_item | Courier damaged item | invariant | Damage record captures condition, photos, custody stage, notification and claim path. | incident evidence |
| courier.exception.lost_item | Courier lost item | invariant | Lost item process searches custody, route, vehicle, depot and scans before claim. | structured recovery |
| courier.exception.customer_change | Courier customer change | variant | Change updates address, deadline, recipient, service level or cancellation with approval. | control scope |
| courier.exception.security_incident | Courier security incident | invariant | Incident records theft, threat, assault, vehicle break-in or suspicious item. | protect staff and cargo |
| courier.comms.customer_eta | Courier customer ETA | variant | ETA message updates sender or recipient about pickup or delivery timing. | transparency |
| courier.comms.dispatch_radio | Courier dispatch communication | invariant | Communication gives concise stop, status, exception and safety updates. | live coordination |
| courier.comms.proof_request | Proof request response | invariant | Response sends delivery proof, chain detail or exception notes to customer. | answer evidence need |
| courier.comms.escalation_contact | Courier escalation contact | invariant | Contact defines who decides on failed, high-value, legal, medical or unsafe delivery. | fast decision |
| courier.comms.recipient_call | Recipient call | variant | Call confirms access, location, delivery window or special instruction. | reduce failed stop |
| courier.billing.price_quote | Courier price quote | invariant | Quote uses distance, urgency, item, wait time, vehicle, route and special handling. | price before dispatch |
| courier.billing.wait_time | Courier wait time charge | variant | Charge applies when courier waits beyond included pickup or delivery window. | recover delay cost |
| courier.billing.proof_billing | Proof-linked billing | invariant | Billing connects completed job, proofs, exceptions, surcharges and customer account. | invoice defensibly |
| courier.billing.account_terms | Courier account terms | variant | Terms define credit limit, invoicing cycle, service levels and dispute process. | repeat customer control |
| courier.billing.dispute_case | Courier billing dispute | invariant | Case records charge issue, proof, communication, correction or denial. | resolve cleanly |
| courier.admin.courier_equipment | Courier equipment checklist | invariant | Checklist covers bag, scanner, phone, charger, lock, PPE, forms and vehicle items. | ready to work |
| courier.admin.license_insurance | Courier license and insurance | variant | Record confirms driver, vehicle, insurance and permits where required. | compliance |
| courier.metrics.courier_kpi | Courier operations KPI | variant | KPI tracks on-time delivery, failed stops, claims, route density, wait time and customer issues. | manage dispatch |
| courier.continuity.vehicle_breakdown | Courier vehicle breakdown plan | invariant | Plan reassigns items, secures cargo, updates customers and documents delay. | recover route |
