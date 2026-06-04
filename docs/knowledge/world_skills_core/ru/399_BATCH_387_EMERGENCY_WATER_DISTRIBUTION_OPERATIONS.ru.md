# BATCH 387: Emergency Water Distribution Operations

**KnowledgeUnits:** 44  
**Namespace:** `waterdistops.*`  
**Scope:** requests, source approval, tankers, bottled water, points of distribution, testing and records.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| waterdistops.activation.trigger | activation trigger | MODEL | Trigger includes water outage, contamination, drought, shelter demand or infrastructure damage. | Starts controlled water supply. |
| waterdistops.activation.water_cell | water coordination cell | RECORD | Cell names utility, public health, logistics, finance and distribution leads. | Centralizes decisions. |
| waterdistops.activation.priority_policy | priority policy | CONSTRAINT | Policy ranks hospitals, shelters, dialysis, schools, vulnerable groups and general public. | Allocates limited water fairly. |
| waterdistops.activation.safety_brief | safety briefing | SAFETY_RULE | Brief covers lifting, traffic, heat, sanitation, tanker safety and public crowding. | Protects staff and public. |
| waterdistops.request.request_id | water request ID | RECORD | Request ID links requester, location, population, quantity, urgency and status. | Tracks demand. |
| waterdistops.request.need_type | need type | RECORD | Need type distinguishes drinking, cooking, hygiene, medical, animal or operational water. | Matches source and packaging. |
| waterdistops.request.population | population estimate | MEASUREMENT | Population estimate includes households, shelter residents, workers or facility users. | Sizes deliveries. |
| waterdistops.request.validation | request validation | QUALITY_CHECK | Validation checks need, duplication, current stock, source and distribution method. | Prevents waste. |
| waterdistops.source.approved_source | approved source | SAFETY_RULE | Emergency drinking water comes from public health/utility-approved source. | Protects health. |
| waterdistops.source.bulk_water | bulk water source | RECORD | Bulk source records hydrant, plant, well, supplier, tanker fill point and approval. | Enables traceability. |
| waterdistops.source.bottled_supplier | bottled supplier | RECORD | Supplier record stores vendor, lot, quantity, delivery time and storage needs. | Controls bottled water. |
| waterdistops.source.contamination | contamination concern | FAILURE_MODE | Suspected contamination requires isolation, testing and public health review. | Prevents unsafe distribution. |
| waterdistops.tanker.tanker_id | tanker ID | RECORD | Tanker ID links vehicle, tank, capacity, operator, cleaning and approval status. | Controls bulk deliveries. |
| waterdistops.tanker.sanitation | tanker sanitation | SAFETY_RULE | Tankers for potable water require sanitary history, cleaning and approved fittings. | Prevents contamination. |
| waterdistops.tanker.fill_log | fill log | RECORD | Fill log records source, time, volume, operator and seal if used. | Tracks custody. |
| waterdistops.tanker.delivery_log | delivery log | RECORD | Delivery log records destination, volume, time, receiver and condition. | Closes delivery loop. |
| waterdistops.pod.site_selection | POD site selection | METHOD | Site checks access, traffic, shade, security, storage and population reach. | Makes distribution workable. |
| waterdistops.pod.layout | POD layout | METHOD | Layout separates entry, queue, loading, walk-up, staff, pallets and exit. | Reduces congestion. |
| waterdistops.pod.household_limit | household limit | CONSTRAINT | Limits define units per household or vehicle by supply and need. | Extends scarce stock. |
| waterdistops.pod.accessibility | accessibility support | METHOD | Walk-up, disability, delivery or language support improves access. | Reaches vulnerable users. |
| waterdistops.inventory.stock_count | stock count | MEASUREMENT | Stock count tracks pallets, bottles, gallons, bulk tanks and losses. | Shows available supply. |
| waterdistops.inventory.lot_trace | lot trace | RECORD | Lot trace links bottled water to supplier and distribution sites. | Supports recall. |
| waterdistops.inventory.storage | storage condition | SAFETY_RULE | Water is stored away from heat, chemicals, pests and tampering. | Protects quality. |
| waterdistops.inventory.reorder | reorder trigger | MODEL | Reorder uses burn rate, population, delivery time and reserve level. | Prevents stockout. |
| waterdistops.testing.field_test | field test | QUALITY_CHECK | Chlorine, turbidity or other required checks confirm bulk water acceptability. | Supports safe release. |
| waterdistops.testing.lab_sample | lab sample | METHOD | Samples route to lab when contamination, source change or public health rule requires. | Adds verification. |
| waterdistops.testing.hold_release | hold and release | SAFETY_RULE | Questionable water is held until approved. | Prevents unsafe use. |
| waterdistops.testing.result_record | test result record | RECORD | Result stores source, sample, method, time, result and reviewer. | Creates evidence. |
| waterdistops.communication.public_notice | public notice | METHOD | Notice states sites, hours, limits, containers, delivery options and safety guidance. | Guides residents. |
| waterdistops.communication.boil_link | boil notice link | METHOD | Distribution messaging aligns with boil water or do-not-use notices. | Avoids contradictory advice. |
| waterdistops.communication.partner_update | partner update | METHOD | Partners receive stock, site, delivery, vulnerable needs and closure updates. | Aligns operations. |
| waterdistops.communication.language | language support | METHOD | Core notices are translated for affected communities where possible. | Improves access. |
| waterdistops.security.crowd | crowd control | METHOD | Staff manage queues, vehicle flow, conflict and site safety. | Keeps distribution orderly. |
| waterdistops.security.tamper | tamper control | SAFETY_RULE | Pallets, tanks and valves are monitored for tampering. | Protects water quality. |
| waterdistops.security.theft | theft flag | MODEL | Unexpected losses or unauthorized pickups trigger review. | Protects scarce supply. |
| waterdistops.records.daily_log | daily log | RECORD | Log records sites, deliveries, stock, incidents, staff and issues. | Summarizes operation. |
| waterdistops.records.cost | cost record | RECORD | Costs track purchase, delivery, labor, equipment, storage and security. | Supports reimbursement. |
| waterdistops.records.retention | retention rule | CONSTRAINT | Records follow public health, finance, emergency and grant schedules. | Preserves audit trail. |
| waterdistops.metrics.gallons_served | gallons served | MEASUREMENT | Gallons served by site and population show reach. | Tracks service. |
| waterdistops.metrics.stockout | stockout event | MEASUREMENT | Stockout events record site, time, cause and unmet demand. | Improves planning. |
| waterdistops.qa.reconciliation | reconciliation | QUALITY_CHECK | Stock, deliveries and distribution counts reconcile daily. | Detects loss/error. |
| waterdistops.demob.site_close | site closeout | METHOD | Closeout removes stock, cleans site, returns equipment and notifies public. | Ends operation cleanly. |
| waterdistops.demob.final_inventory | final inventory | QUALITY_CHECK | Final inventory reconciles remaining bottles, bulk water, tanks and losses. | Prevents unresolved stock gaps. |
| waterdistops.review.after_action | after-action review | METHOD | Review captures source, access, testing, stock and communication lessons. | Improves next response. |
