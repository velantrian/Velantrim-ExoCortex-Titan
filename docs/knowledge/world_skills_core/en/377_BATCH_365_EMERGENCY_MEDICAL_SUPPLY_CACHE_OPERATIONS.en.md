# BATCH 365: Emergency Medical Supply Cache Operations

**KnowledgeUnits:** 44  
**Namespace:** `medcacheops.*`  
**Scope:** inventory, rotation, requests, allocation, deployment, return and audit.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| medcacheops.inventory.item_id | item ID | RECORD | Item ID links product, lot, quantity, location, expiration and status. | Creates controlled inventory. |
| medcacheops.inventory.category | item category | RECORD | Category distinguishes PPE, medications, devices, testing, sanitation or field supplies. | Supports allocation. |
| medcacheops.inventory.lot | lot tracking | RECORD | Lot and serial data are recorded for recalls and expiry. | Enables traceability. |
| medcacheops.inventory.condition | condition status | QUALITY_CHECK | Condition records sealed, damaged, expired, quarantined or deployable. | Prevents unsafe issue. |
| medcacheops.storage.zone | storage zone | METHOD | Zones separate temperature, security, sterile, hazardous and fast-pick items. | Makes warehouse usable. |
| medcacheops.storage.temperature | temperature control | SAFETY_RULE | Temperature-sensitive supplies use monitored storage and excursion logs. | Preserves usability. |
| medcacheops.storage.security | security control | SAFETY_RULE | Controlled or high-value items require access control and logs. | Prevents diversion. |
| medcacheops.storage.shelf_map | shelf map | RECORD | Shelf map identifies aisle, rack, bin and pallet. | Speeds picking. |
| medcacheops.rotation.fefo | FEFO rotation | METHOD | First-expire-first-out is used for dated supplies. | Reduces waste. |
| medcacheops.rotation.expiry_alert | expiry alert | MEASUREMENT | Alerts flag items nearing expiration for use, transfer or disposal. | Protects readiness. |
| medcacheops.rotation.exercising | stock exercise | METHOD | Supplies may be rotated through routine programs before expiry. | Maintains value. |
| medcacheops.rotation.disposal | disposal process | SAFETY_RULE | Expired or damaged medical supplies are disposed by regulation. | Prevents unsafe reuse. |
| medcacheops.request.request_id | request ID | RECORD | Request ID links requester, incident, item, quantity, justification and priority. | Controls demand. |
| medcacheops.request.authorized_requester | authorized requester | CONSTRAINT | Only approved agencies or roles can request cache release. | Protects stock. |
| medcacheops.request.need_validation | need validation | QUALITY_CHECK | Need is checked against incident data, burn rate and local stock. | Prevents over-allocation. |
| medcacheops.request.substitution | substitution rule | METHOD | Equivalent supplies may be offered when exact item is unavailable. | Keeps response moving. |
| medcacheops.allocation.priority | allocation priority | MODEL | Priority considers life safety, healthcare capacity, vulnerable settings and scarcity. | Allocates fairly. |
| medcacheops.allocation.formula | allocation formula | METHOD | Formula uses population, caseload, beds, staff or mission size. | Makes distribution transparent. |
| medcacheops.allocation.reserve | reserve level | CONSTRAINT | Minimum reserve protects future surge and critical missions. | Avoids empty cache. |
| medcacheops.allocation.approval | approval record | RECORD | Approval records decision, approver, quantity, restrictions and rationale. | Supports audit. |
| medcacheops.deployment.pick_list | pick list | RECORD | Pick list specifies item, lot, quantity, bin and handling requirement. | Reduces fulfillment error. |
| medcacheops.deployment.pack | packing process | METHOD | Packing checks count, lot, label, chain of custody and transport condition. | Ships correct supplies. |
| medcacheops.deployment.courier | courier handoff | RECORD | Handoff records driver, vehicle, seal, time and destination. | Maintains custody. |
| medcacheops.deployment.receipt | receiving confirmation | RECORD | Recipient confirms quantity, condition, time and discrepancies. | Closes delivery loop. |
| medcacheops.transport.cold_chain | cold-chain transport | SAFETY_RULE | Cold-chain transport uses validated containers and temperature logs. | Protects sensitive supplies. |
| medcacheops.transport.route | route plan | METHOD | Route plan considers urgency, security, weather, access and fuel. | Improves delivery reliability. |
| medcacheops.transport.security | transport security | SAFETY_RULE | High-value or controlled items may need escorts, seals or restricted routes. | Reduces theft. |
| medcacheops.transport.delay | delay handling | METHOD | Delay triggers recipient notice, temperature check and reroute decision. | Manages risk. |
| medcacheops.return.return_id | return ID | RECORD | Return ID links deployed items, unused stock, condition and source. | Tracks reverse logistics. |
| medcacheops.return.inspection | return inspection | QUALITY_CHECK | Returned supplies are inspected for seal, temperature, damage and contamination. | Decides redeployability. |
| medcacheops.return.quarantine | quarantine status | METHOD | Questionable items are isolated until safety decision. | Prevents bad stock mixing. |
| medcacheops.return.restock | restock process | METHOD | Deployable returns are counted, relabeled and placed back into inventory. | Restores readiness. |
| medcacheops.records.chain | chain of custody | RECORD | Chain records each transfer, handler and condition. | Supports accountability. |
| medcacheops.records.recall | recall record | METHOD | Recall process finds lots by location and recipient. | Enables rapid removal. |
| medcacheops.records.retention | retention rule | CONSTRAINT | Cache records follow medical, finance, grant and emergency retention schedules. | Keeps audit trail. |
| medcacheops.finance.valuation | valuation | RECORD | Stock value is tracked for insurance, grant and replacement planning. | Supports finance. |
| medcacheops.finance.replenishment | replenishment trigger | MODEL | Replenishment triggers after deployment, expiry, loss or minimum stock breach. | Maintains readiness. |
| medcacheops.qa.cycle_count | cycle count | QUALITY_CHECK | Cycle counts compare physical stock to system records. | Detects errors. |
| medcacheops.qa.drill | deployment drill | METHOD | Drills test request, pick, pack, delivery and documentation speed. | Proves readiness. |
| medcacheops.metrics.fill_rate | fill rate | MEASUREMENT | Fill rate measures requested quantity fulfilled on time. | Shows cache usefulness. |
| medcacheops.metrics.expiry_loss | expiry loss | MEASUREMENT | Expiry loss tracks stock discarded due to age. | Improves rotation. |
| medcacheops.governance.cache_owner | cache owner | RECORD | Cache owner defines policy, access, inventory standards and reporting. | Keeps accountability clear. |
| medcacheops.governance.mutual_aid | mutual aid agreement | RECORD | Agreements define borrowing, replacement, liability and documentation between agencies. | Expands cache capacity safely. |
| medcacheops.closeout.after_action | after-action review | METHOD | Review captures request quality, allocation fairness, delivery issues and replenishment needs. | Improves next deployment. |
