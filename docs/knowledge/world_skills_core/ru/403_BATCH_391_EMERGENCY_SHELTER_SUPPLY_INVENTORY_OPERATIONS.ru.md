# BATCH 391: Emergency Shelter Supply Inventory Operations

**KnowledgeUnits:** 44  
**Namespace:** `sheltersupplyops.*`  
**Scope:** cots, blankets, hygiene kits, PPE, ordering, issue logs, shortages and reconciliation.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| sheltersupplyops.activation.supply_plan | supply plan | RECORD | Plan lists expected population, operating days, supply categories and owners. | Sets inventory baseline. |
| sheltersupplyops.activation.cache_link | cache link | RECORD | Shelter inventory links to local cache, donations, vendors and logistics staging. | Shows supply sources. |
| sheltersupplyops.activation.role_roster | role roster | RECORD | Roster names inventory lead, receiving, issue desk, runners and finance support. | Clarifies responsibility. |
| sheltersupplyops.activation.initial_count | initial count | MEASUREMENT | Opening count records supplies on hand before shelter operation begins. | Establishes audit baseline. |
| sheltersupplyops.items.cots | cot inventory | RECORD | Cot inventory tracks type, quantity, condition, location and setup status. | Manages sleeping capacity. |
| sheltersupplyops.items.blankets | blanket inventory | RECORD | Blanket inventory tracks clean, issued, soiled and reserve blankets. | Prevents night shortages. |
| sheltersupplyops.items.hygiene_kits | hygiene kits | RECORD | Kits include soap, toothbrush, menstrual products, wipes or local standard contents. | Supports dignity. |
| sheltersupplyops.items.ppe | PPE inventory | RECORD | PPE tracks masks, gloves, gowns, eye protection and sanitizer. | Protects health operations. |
| sheltersupplyops.receiving.delivery_id | delivery ID | RECORD | Delivery ID links supplier, driver, items, count, time and receiver. | Tracks inbound supplies. |
| sheltersupplyops.receiving.condition_check | condition check | QUALITY_CHECK | Received goods are checked for damage, contamination, expiration and count. | Prevents bad stock. |
| sheltersupplyops.receiving.shortage | receiving shortage | RECORD | Shortage records expected, received, missing and follow-up owner. | Keeps supplier issues visible. |
| sheltersupplyops.receiving.storage_route | storage route | METHOD | Supplies route to sleeping, medical, food, PPE, cleaning or secure storage. | Prevents pileups. |
| sheltersupplyops.storage.zone | storage zone | METHOD | Zones separate clean, soiled, medical, restricted, bulk and daily-use goods. | Makes stock findable. |
| sheltersupplyops.storage.security | secure storage | SAFETY_RULE | Scarce, medical or high-value supplies use controlled access. | Reduces loss. |
| sheltersupplyops.storage.environment | storage condition | CONSTRAINT | Supplies are protected from moisture, pests, heat, chemicals and traffic. | Preserves usability. |
| sheltersupplyops.storage.labeling | bin labeling | METHOD | Bins and pallets show item, quantity, date and reorder threshold. | Speeds work. |
| sheltersupplyops.issue.issue_log | issue log | RECORD | Issue log records item, quantity, destination, requester and time. | Tracks outbound use. |
| sheltersupplyops.issue.resident_issue | resident issue | METHOD | Resident-issued items may be logged by household, dorm area or anonymous count. | Balances privacy and stock control. |
| sheltersupplyops.issue.department_issue | department issue | METHOD | Functional areas receive supplies through approved request path. | Prevents uncontrolled grabbing. |
| sheltersupplyops.issue.return | return process | METHOD | Unused clean supplies can return to inventory after inspection. | Reduces waste. |
| sheltersupplyops.reorder.burn_rate | burn rate | MEASUREMENT | Burn rate estimates daily use by population and activity. | Predicts shortages. |
| sheltersupplyops.reorder.threshold | reorder threshold | MODEL | Threshold uses lead time, criticality, reserve and burn rate. | Triggers timely ordering. |
| sheltersupplyops.reorder.request | reorder request | RECORD | Request records item, quantity, justification, priority and funding source. | Starts resupply. |
| sheltersupplyops.reorder.substitution | substitution | METHOD | Equivalent supplies are approved when exact item is unavailable. | Keeps service operating. |
| sheltersupplyops.shortage.shortage_id | shortage ID | RECORD | Shortage ID tracks item, site impact, priority, workaround and owner. | Makes gaps actionable. |
| sheltersupplyops.shortage.rationing | rationing rule | CONSTRAINT | Rationing prioritizes life safety, health, accessibility and minimum dignity. | Allocates fairly. |
| sheltersupplyops.shortage.escalation | shortage escalation | METHOD | Critical shortages escalate to logistics, donations, procurement or mutual aid. | Finds supply fast. |
| sheltersupplyops.shortage.public_message | public message | METHOD | Public messages request only needed donations and avoid unwanted items. | Reduces clutter. |
| sheltersupplyops.sanitation.soiled_goods | soiled goods | METHOD | Soiled blankets, towels and clothing are separated and bagged. | Prevents contamination. |
| sheltersupplyops.sanitation.laundry_route | laundry route | METHOD | Laundry routes send reusable textiles to approved cleaning or disposal. | Restores stock. |
| sheltersupplyops.sanitation.waste | waste handling | SAFETY_RULE | Damaged, contaminated or single-use supplies are disposed by policy. | Protects health. |
| sheltersupplyops.sanitation.pest | pest prevention | METHOD | Food-like or textile storage is checked for pests. | Protects inventory. |
| sheltersupplyops.records.daily_count | daily count | MEASUREMENT | Daily count checks high-use and scarce supplies. | Keeps inventory current. |
| sheltersupplyops.records.adjustment | inventory adjustment | RECORD | Adjustments record loss, damage, correction, donation or transfer reason. | Preserves audit trail. |
| sheltersupplyops.records.cost | cost record | RECORD | Costs track purchases, rentals, donations, losses and transfers. | Supports finance. |
| sheltersupplyops.records.retention | retention rule | CONSTRAINT | Inventory records follow emergency, finance and grant schedules. | Keeps evidence. |
| sheltersupplyops.qa.cycle_count | cycle count | QUALITY_CHECK | Cycle counts compare physical stock to logs. | Detects errors. |
| sheltersupplyops.qa.loss_review | loss review | QUALITY_CHECK | Losses are reviewed for theft, damage, spoilage or documentation gap. | Improves control. |
| sheltersupplyops.metrics.stockout | stockout metric | MEASUREMENT | Stockouts record item, duration, cause and impact. | Guides improvement. |
| sheltersupplyops.metrics.per_resident | per-resident use | MEASUREMENT | Use per resident helps forecast future shelter supply needs. | Improves planning. |
| sheltersupplyops.demob.final_reconcile | final reconciliation | QUALITY_CHECK | Final reconciliation matches opening, receipts, issues, returns and remaining stock. | Closes inventory. |
| sheltersupplyops.demob.transfer | supply transfer | METHOD | Remaining supplies transfer to cache, shelters, donations or disposal. | Avoids waste. |
| sheltersupplyops.review.after_action | after-action review | METHOD | Review captures shortages, reorder delays, storage and issue-control lessons. | Improves next shelter. |
| sheltersupplyops.governance.inventory_owner | inventory owner | RECORD | Owner coordinates shelter, logistics, finance and donations for supplies. | Keeps accountability clear. |
