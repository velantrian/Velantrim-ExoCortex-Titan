# BATCH_214 — Moving Company Operations Detail
# world_skills_core · source: world_skills_core:batch_214:moving_company_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| moveops.sales.move_inquiry | Moving inquiry | invariant | Inquiry records origin, destination, date, volume, stairs, access, services and constraints. | start estimate |
| moveops.sales.survey | Moving survey | invariant | Survey estimates inventory, weight or volume, packing needs, risks and access limits. | price realistically |
| moveops.sales.estimate_type | Moving estimate type | invariant | Type defines binding, nonbinding, hourly, flat-rate or not-to-exceed pricing. | customer expectation |
| moveops.sales.service_scope | Move service scope | invariant | Scope covers packing, loading, transport, storage, unpacking, disposal and exclusions. | define job |
| moveops.sales.date_hold | Move date hold | variant | Hold reserves crew, truck and slot pending deposit or confirmation. | capacity promise |
| moveops.planning.move_plan | Move plan | invariant | Plan maps crew, truck, timing, access, inventory, packing, route and special items. | operational blueprint |
| moveops.planning.crew_assignment | Moving crew assignment | invariant | Assignment matches crew size, skill, hours, driver, helper and supervisor to move. | staff the job |
| moveops.planning.truck_assignment | Moving truck assignment | invariant | Assignment chooses truck size, liftgate, equipment and route suitability. | fit load |
| moveops.planning.access_check | Move access check | invariant | Check confirms parking, elevators, loading docks, stairs, permits and time windows. | avoid day-of blockers |
| moveops.planning.weather_plan | Moving weather plan | variant | Plan adapts protection, timing and safety for rain, snow, heat or wind. | weather-proof move |
| moveops.pack.packing_order | Packing order | invariant | Order lists rooms, materials, fragile items, owner-packed items and labeling rules. | pack systematically |
| moveops.pack.carton_label | Carton label | invariant | Label identifies room, contents, handling, destination and priority. | find items later |
| moveops.pack.fragile_pack | Fragile packing | invariant | Packing protects glass, dishes, art, electronics or delicate items with suitable materials. | reduce breakage |
| moveops.pack.wardrobe_box | Wardrobe box | variant | Box transports hanging garments with less folding and handling. | clothing care |
| moveops.pack.owner_packed | Owner-packed box note | variant | Note identifies boxes packed by customer and condition limitations. | claim clarity |
| moveops.inventory.inventory_list | Moving inventory list | invariant | List records items, condition, tag, room and handling notes. | custody record |
| moveops.inventory.condition_code | Item condition code | invariant | Code documents scratches, dents, wear, cracks or prior damage before move. | baseline |
| moveops.inventory.high_value_item | High-value item declaration | variant | Declaration identifies valuable, fragile or special-liability property needing extra controls. | risk focus |
| moveops.inventory.photo_record | Move photo record | variant | Photos document condition, packing, loading, damage risk or access issues. | visual evidence |
| moveops.inventory.exception_item | Moving exception item | invariant | Exception covers prohibited, hazardous, oversized, unprepared or disputed item. | decide before loading |
| moveops.load.floor_protection | Move floor protection | invariant | Protection uses runners, pads, corner guards or door jamb protectors. | protect property |
| moveops.load.furniture_pad | Furniture padding | invariant | Padding protects surfaces, corners, glass and upholstery during handling and transport. | prevent damage |
| moveops.load.load_sequence | Truck load sequence | invariant | Sequence balances weight, protects fragile items and supports unload order. | stable load |
| moveops.load.strapping | Load strapping | invariant | Strapping secures tiers, heavy items and shifting risks inside truck. | transport safety |
| moveops.load.lift_team | Heavy item lift team | variant | Team handles pianos, safes, appliances or oversized furniture with planning and equipment. | avoid injury |
| moveops.transport.route_plan | Moving route plan | invariant | Plan chooses route, tolls, restrictions, parking, fuel and timing. | move between sites |
| moveops.transport.driver_log | Moving driver log | invariant | Log records vehicle, driver, mileage, hours, fuel, inspections and incidents. | transport accountability |
| moveops.transport.vehicle_inspection | Moving truck inspection | invariant | Inspection checks tires, lights, liftgate, straps, pads, fluids and damage. | road readiness |
| moveops.transport.delay_notice | Move delay notice | invariant | Notice informs customer about traffic, weather, breakdown, access or crew delay. | reduce uncertainty |
| moveops.transport.storage_in_transit | Storage-in-transit | variant | Storage holds goods temporarily with inventory, location, access and billing records. | pause move safely |
| moveops.unload.delivery_check | Delivery check | invariant | Check verifies address, access, inventory, room labels and customer instructions. | unload right place |
| moveops.unload.room_placement | Room placement | invariant | Placement puts items in requested rooms or zones according to labels and customer direction. | useful delivery |
| moveops.unload.reassembly | Furniture reassembly | variant | Reassembly restores beds, tables, desks or fixtures within agreed scope. | finish service |
| moveops.unload.debris_removal | Packing debris removal | variant | Removal collects cartons, wrap and pads where service includes cleanup. | leave cleaner |
| moveops.unload.final_walkthrough | Move final walkthrough | invariant | Walkthrough checks inventory, rooms, damages, missing items and remaining tasks with customer. | close job |
| moveops.claim.damage_claim | Moving damage claim | invariant | Claim records damaged item, evidence, inventory tag, valuation, review and resolution. | handle loss fairly |
| moveops.claim.missing_item | Missing item claim | invariant | Claim investigates inventory, load, unload, truck, storage and customer report. | find or compensate |
| moveops.claim.valuation_option | Moving valuation option | variant | Option defines carrier liability level or customer-selected protection plan. | claim basis |
| moveops.claim.claim_deadline | Moving claim deadline | invariant | Deadline sets time window and submission requirements for loss or damage claim. | procedural control |
| moveops.claim.customer_dispute | Moving customer dispute | invariant | Dispute records estimate, charges, service issue, claim and communication trail. | structured resolution |
| moveops.safety.safe_lifting | Moving safe lifting | invariant | Safe lifting uses team coordination, equipment, path clearing and body mechanics. | reduce injury |
| moveops.safety.prohibited_items | Moving prohibited items | invariant | Prohibition covers hazardous, illegal, perishable, live, valuable or restricted items by policy. | avoid liability |
| moveops.metrics.move_kpi | Moving company KPI | variant | KPI tracks on-time arrival, claims, estimate accuracy, crew hours, damage rate and reviews. | manage operation |
| moveops.continuity.truck_breakdown | Moving truck breakdown plan | invariant | Plan covers roadside safety, alternate truck, customer update, crew time and cargo security. | recover move |
