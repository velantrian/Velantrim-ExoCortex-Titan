# BATCH_223 — Appliance Retail Delivery Operations Detail
# world_skills_core · source: world_skills_core:batch_223:appliance_retail_delivery_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| appdeliv.order.delivery_order | Appliance delivery order | invariant | Order records customer, address, appliance, service level, time window, payment and contacts. | start delivery |
| appdeliv.order.sku_match | Appliance SKU match | invariant | Match verifies ordered SKU, color, size, accessories and serial before loadout. | avoid wrong item |
| appdeliv.order.install_scope | Installation scope | invariant | Scope defines delivery only, basic hookup, haul-away, door reversal or accessory install. | know allowed work |
| appdeliv.order.site_notes | Delivery site notes | invariant | Notes cover stairs, elevator, parking, gate, floor, pets, access and customer constraints. | plan route |
| appdeliv.order.customer_confirmation | Delivery customer confirmation | invariant | Confirmation verifies time window, address, readiness, old appliance and required adult presence. | reduce failed stop |
| appdeliv.route.route_manifest | Appliance route manifest | invariant | Manifest lists stops, items, services, sequence, crew, truck and proof requirements. | route plan |
| appdeliv.route.truck_capacity | Appliance truck capacity | invariant | Capacity checks cube, weight, straps, liftgate and appliance protection. | safe load |
| appdeliv.route.stop_sequence | Appliance stop sequence | variant | Sequence balances promised windows, geography, load order and install complexity. | efficient day |
| appdeliv.route.delay_notice | Appliance delivery delay notice | invariant | Notice informs customer about traffic, warehouse, weather, access or installation delay. | expectation control |
| appdeliv.route.failed_stop | Failed delivery stop | invariant | Stop fails due to no access, unsafe path, not home, wrong address or unready site. | explain non-delivery |
| appdeliv.load.warehouse_pick | Appliance warehouse pick | invariant | Pick pulls correct unit, accessories, paperwork and haul-away supplies. | prepare load |
| appdeliv.load.serial_capture | Appliance serial capture | invariant | Capture links physical unit serial to customer order and warranty. | trace exact appliance |
| appdeliv.load.damage_check | Preload damage check | invariant | Check documents dents, scratches, carton damage or missing parts before loading. | baseline evidence |
| appdeliv.load.appliance_padding | Appliance padding | invariant | Padding protects surfaces, doors, handles, glass and floors during transport. | damage prevention |
| appdeliv.load.load_securement | Appliance load securement | invariant | Securement uses straps, blocks, liftgate position and weight balance. | prevent shift |
| appdeliv.site.path_assessment | Delivery path assessment | invariant | Assessment checks doorway, stairs, turns, flooring, overhead clearance and obstacles. | fit before moving |
| appdeliv.site.floor_protection | Appliance delivery floor protection | invariant | Protection uses runners, blankets, sliders or mats to reduce scratches and dirt. | respect home |
| appdeliv.site.door_removal | Door removal need | variant | Need identifies whether appliance or home door removal is required and allowed. | fit issue |
| appdeliv.site.utility_readiness | Appliance utility readiness | invariant | Readiness checks outlet, water, drain, vent, gas shutoff or space requirements. | install boundary |
| appdeliv.site.stop_work_condition | Delivery stop-work condition | invariant | Condition includes unsafe stairs, pests, hazard, missing shutoff, bad electrical or impossible fit. | crew safety |
| appdeliv.install.leveling | Appliance leveling | invariant | Leveling adjusts feet or position to support safe and correct operation. | basic setup |
| appdeliv.install.water_connection | Water connection handoff | variant | Handoff connects approved hose or records why connection was not performed. | controlled hookup |
| appdeliv.install.dryer_vent | Dryer vent check | variant | Check verifies compatible vent path, condition, airflow concern and installation limits. | fire and performance |
| appdeliv.install.range_anti_tip | Range anti-tip check | variant | Check verifies bracket need, presence or install status where service includes it. | tip risk control |
| appdeliv.install.test_cycle | Appliance test cycle | invariant | Test confirms power, obvious leaks, controls or startup according to delivery scope. | prove setup |
| appdeliv.haulaway.old_appliance | Old appliance haul-away | variant | Haul-away removes old unit if disconnected, empty, accessible and included in order. | complete service |
| appdeliv.haulaway.recycling_route | Appliance recycling route | variant | Route sends old appliance to recycler, warehouse, scrap or disposal vendor. | end-of-life |
| appdeliv.haulaway.refrigerant_item | Refrigerant appliance handling | variant | Handling routes refrigerators or freezers through approved recycling or recovery process. | environmental control |
| appdeliv.haulaway.property_left | Property left behind | invariant | Record notes appliance, parts or debris intentionally left with customer or site. | avoid confusion |
| appdeliv.haulaway.debris_removal | Delivery debris removal | variant | Removal collects packaging, straps, cardboard and protective film according to service. | clean finish |
| appdeliv.proof.delivery_signature | Delivery signature | invariant | Signature confirms receipt, condition, services performed and exceptions. | proof |
| appdeliv.proof.photo_proof | Appliance photo proof | variant | Photo documents delivered item, install, damage, path issue or haul-away. | visual evidence |
| appdeliv.proof.exception_note | Delivery exception note | invariant | Note explains damage, refusal, partial service, missing accessory or unsafe condition. | close variance |
| appdeliv.proof.customer_refusal | Customer refusal | invariant | Refusal records reason, item condition, service issue, restock and next action. | controlled return |
| appdeliv.proof.return_to_warehouse | Return to warehouse | invariant | Return logs undelivered appliance, condition, reason, truck, crew and restock status. | inventory control |
| appdeliv.claim.damage_claim | Appliance delivery damage claim | invariant | Claim records product or property damage, photos, timing, crew note and resolution. | service recovery |
| appdeliv.claim.missing_part | Missing accessory or part | invariant | Missing part record triggers warehouse search, reorder, ship-to-customer or return visit. | complete order |
| appdeliv.claim.install_issue | Appliance install issue | invariant | Issue records leak, fit, leveling, connection, venting or startup problem after delivery. | follow-up |
| appdeliv.claim.customer_complaint | Delivery customer complaint | invariant | Complaint records delay, crew conduct, damage, incomplete work or communication issue. | quality loop |
| appdeliv.claim.revisit_order | Appliance delivery revisit | variant | Revisit schedules second trip for missing part, fit correction, inspection or exchange. | close gap |
| appdeliv.admin.crew_assignment | Appliance delivery crew assignment | invariant | Assignment matches driver, helper, skills, truck and route. | staff route |
| appdeliv.admin.safety_briefing | Delivery safety briefing | invariant | Briefing covers lifting, stairs, weather, pets, utilities, driving and stop-work rules. | crew protection |
| appdeliv.metrics.delivery_kpi | Appliance delivery KPI | variant | KPI tracks on-time rate, damage claims, failed stops, haul-away completion and revisits. | manage operation |
| appdeliv.continuity.truck_breakdown | Appliance truck breakdown | invariant | Breakdown plan secures load, updates customers, reassigns route and documents delay. | recover route |
