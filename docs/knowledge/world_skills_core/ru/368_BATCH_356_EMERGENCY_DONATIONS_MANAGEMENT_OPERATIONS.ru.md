# BATCH 356: Emergency Donations Management Operations

**KnowledgeUnits:** 44  
**Namespace:** `donationops.*`  
**Scope:** offers, acceptance criteria, warehousing, matching, distribution, unsolicited goods and records.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| donationops.intake.offer_id | offer ID | RECORD | Offer ID links donor, item, quantity, location, timing and restrictions. | Creates traceable donation intake. |
| donationops.intake.offer_channel | offer channel | RECORD | Channel records web form, phone, email, partner, corporate offer or walk-in. | Shows donation flow. |
| donationops.intake.donor_contact | donor contact | RECORD | Donor contact stores organization/person, callback, logistics and tax receipt need. | Enables coordination. |
| donationops.intake.item_description | item description | RECORD | Description captures type, condition, quantity, packaging and special handling. | Prevents vague offers. |
| donationops.criteria.accepted_list | accepted item list | CONSTRAINT | Accepted list reflects current incident needs, safety and storage capacity. | Keeps donations useful. |
| donationops.criteria.not_needed | not-needed list | CONSTRAINT | Not-needed list blocks unsuitable goods like dirty clothing, expired food or random bulk. | Avoids waste burden. |
| donationops.criteria.safety_screen | safety screen | SAFETY_RULE | Food, medicine, equipment and hazardous goods require safety review before acceptance. | Protects recipients. |
| donationops.criteria.cash_preferred | cash preference | METHOD | Public messaging may direct donors to cash or vetted partners. | Increases flexibility. |
| donationops.acceptance.accept_decision | acceptance decision | RECORD | Decision records accepted, declined, waitlisted or redirected with reason. | Makes intake defensible. |
| donationops.acceptance.conditions | acceptance conditions | CONSTRAINT | Conditions include delivery time, packaging, labeling, temperature or documentation. | Prevents unusable drop-offs. |
| donationops.acceptance.receipt | donation receipt | RECORD | Receipt records donor, goods, estimated quantity and acknowledgment. | Supports donor records. |
| donationops.acceptance.restriction | restricted donation | CONSTRAINT | Restricted donations are tracked to ensure use matches donor limits. | Avoids compliance issues. |
| donationops.logistics.pickup | pickup coordination | METHOD | Pickup plan covers vehicle, driver, loading, timing and contact. | Moves accepted goods. |
| donationops.logistics.delivery_window | delivery window | METHOD | Delivery windows prevent unmanaged arrivals at response sites. | Reduces congestion. |
| donationops.logistics.transport_limit | transport limit | CONSTRAINT | Bulky, heavy, refrigerated or hazardous goods may exceed available logistics. | Guides accept/decline decisions. |
| donationops.logistics.unloading | unloading plan | METHOD | Unloading plan includes dock, volunteers, equipment and traffic flow. | Prevents bottlenecks. |
| donationops.warehouse.receiving | warehouse receiving | METHOD | Receiving verifies quantity, condition, labels and source. | Starts inventory control. |
| donationops.warehouse.storage_zone | storage zone | METHOD | Zones separate food, hygiene, clothing, medical, bulk, restricted and disposal items. | Makes warehouse usable. |
| donationops.warehouse.cold_chain | cold chain | SAFETY_RULE | Refrigerated donations need temperature logs and release criteria. | Prevents unsafe distribution. |
| donationops.warehouse.inventory_count | inventory count | MEASUREMENT | Counts track SKU/item, quantity, lot, location and status. | Supports matching and reporting. |
| donationops.matching.needs_board | needs board | RECORD | Needs board lists requested items, location, priority, quantity and requester. | Matches supply to demand. |
| donationops.matching.allocation | allocation method | METHOD | Allocation assigns goods by need, urgency, restrictions and transportation. | Gets items to right place. |
| donationops.matching.substitution | substitution rule | METHOD | Substitutions use comparable goods when exact request is unavailable. | Keeps distribution moving. |
| donationops.matching.expiry_priority | expiry priority | MODEL | Perishable or expiring items move first when safe and needed. | Reduces waste. |
| donationops.distribution.release_order | release order | RECORD | Release order records item, quantity, recipient, destination and approver. | Controls outbound goods. |
| donationops.distribution.handoff | handoff proof | RECORD | Handoff proof captures receiver, time, condition and transport. | Closes custody trail. |
| donationops.distribution.last_mile | last mile | METHOD | Last-mile distribution uses shelters, food sites, clinics, field teams or partners. | Reaches affected people. |
| donationops.distribution.equity | equity check | QUALITY_CHECK | Distribution is checked for geographic, access and population fairness. | Avoids favoritism. |
| donationops.unsolicited.dropoff | unsolicited drop-off | FAILURE_MODE | Unsolicited goods arrive without intake and can overwhelm operations. | Requires controlled response. |
| donationops.unsolicited.sorting | sorting process | METHOD | Sorting classifies unsolicited goods into usable, redirect, recycle, disposal or quarantine. | Reduces chaos. |
| donationops.unsolicited.public_message | public message | METHOD | Messaging tells public what is needed, where to give and what not to bring. | Prevents donation surges. |
| donationops.unsolicited.disposal | disposal process | METHOD | Unusable goods are disposed, recycled or transferred under policy. | Clears space safely. |
| donationops.records.chain | chain of custody | RECORD | Chain records source, storage, release and recipient for controlled items. | Supports accountability. |
| donationops.records.value | value record | RECORD | Value may be estimated for accounting, insurance or reporting without inflating claims. | Supports finance. |
| donationops.records.restriction_log | restriction log | RECORD | Restricted gifts track donor limits, use and remaining balance. | Prevents misuse. |
| donationops.records.retention | retention rule | CONSTRAINT | Donation records follow finance, grant, audit and privacy schedules. | Keeps evidence. |
| donationops.finance.cash_donation | cash donation route | METHOD | Cash gifts go through authorized finance or nonprofit channels. | Protects funds. |
| donationops.finance.in_kind | in-kind accounting | METHOD | In-kind donations are recorded separately from purchased inventory. | Improves reporting. |
| donationops.finance.fraud_flag | fraud flag | MODEL | Suspicious offers, inflated values or diversion attempts are flagged. | Protects response resources. |
| donationops.safety.recall | recall process | SAFETY_RULE | Recalled or unsafe goods are isolated and recipients notified if distributed. | Reduces harm. |
| donationops.safety.volunteer_lifting | lifting safety | SAFETY_RULE | Warehouse volunteers receive lifting, PPE and equipment guidance. | Prevents injuries. |
| donationops.metrics.fill_rate | need fill rate | MEASUREMENT | Fill rate measures requested items fulfilled from donations. | Shows usefulness. |
| donationops.metrics.waste_rate | waste rate | MEASUREMENT | Waste rate tracks unusable, expired or disposed donations. | Improves messaging. |
| donationops.closeout.reconcile | reconciliation | QUALITY_CHECK | Closeout reconciles offers, inventory, distributions, disposal and restrictions. | Ends operation cleanly. |
