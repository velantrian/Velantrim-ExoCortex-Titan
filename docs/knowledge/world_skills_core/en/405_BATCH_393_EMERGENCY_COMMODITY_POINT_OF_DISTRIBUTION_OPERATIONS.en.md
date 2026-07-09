# BATCH 393: Emergency Commodity Point-of-Distribution Operations

**KnowledgeUnits:** 44  
**Namespace:** `commoditypodops.*`  
**Scope:** site layout, traffic, registration, loading, inventory, safety and reporting.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| commoditypodops.activation.trigger | POD trigger | MODEL | Trigger includes broad need for water, food, tarps, kits, ice or other commodities. | Starts public distribution. |
| commoditypodops.activation.pod_type | POD type | RECORD | Type distinguishes drive-through, walk-up, mobile, neighborhood or bulk partner model. | Defines operations. |
| commoditypodops.activation.site_selection | site selection | METHOD | Site checks access, traffic capacity, storage, safety, shade and population reach. | Chooses workable location. |
| commoditypodops.activation.command_link | command link | RECORD | POD reports to logistics, operations, public information and safety. | Keeps command aligned. |
| commoditypodops.layout.entry | entry lane | METHOD | Entry lane separates public vehicles, deliveries, staff and emergency access. | Prevents congestion. |
| commoditypodops.layout.registration | registration point | METHOD | Registration or count point captures household, vehicle or anonymous tally as policy requires. | Supports fair issue. |
| commoditypodops.layout.loading | loading zone | METHOD | Loading zone positions pallets, staff and vehicles for safe handoff. | Speeds distribution. |
| commoditypodops.layout.exit | exit route | METHOD | Exit route prevents cross-traffic with incoming vehicles or pedestrians. | Reduces crashes. |
| commoditypodops.traffic.queue_plan | queue plan | METHOD | Queue plan defines lanes, cones, signs, overflow and law enforcement needs. | Manages demand. |
| commoditypodops.traffic.pedestrian | pedestrian flow | SAFETY_RULE | Walk-up users have safe route away from vehicles. | Protects people without cars. |
| commoditypodops.traffic.accessibility | accessibility lane | METHOD | Accessibility support handles disability, elders, language or no-vehicle needs. | Improves equity. |
| commoditypodops.traffic.cutoff | queue cutoff | METHOD | Cutoff rules stop new entries when stock, daylight or safety limit is reached. | Prevents conflict. |
| commoditypodops.inventory.item_master | item master | RECORD | Item master lists commodity, unit, package, source and handling rules. | Standardizes stock. |
| commoditypodops.inventory.receiving | receiving | QUALITY_CHECK | Receiving checks quantity, condition, lot, delivery time and source. | Protects inventory. |
| commoditypodops.inventory.stock_count | stock count | MEASUREMENT | Count tracks starting stock, deliveries, issued units and remaining stock. | Shows availability. |
| commoditypodops.inventory.pallet_control | pallet control | METHOD | Pallets are labeled by item, count, lot and lane. | Speeds loading. |
| commoditypodops.issue.issue_rule | issue rule | CONSTRAINT | Rule defines units per household, vehicle, person or referral. | Extends supply fairly. |
| commoditypodops.issue.standard_load | standard load | METHOD | Standard load packages common set of commodities for quick handoff. | Improves throughput. |
| commoditypodops.issue.exception | exception issue | RECORD | Exceptions record extra need, disability, large household or agency pickup. | Keeps fairness visible. |
| commoditypodops.issue.proof | issue proof | RECORD | Proof captures count, lane, time, staff and optional household/vehicle data. | Supports reporting. |
| commoditypodops.staffing.roster | staffing roster | RECORD | Roster covers site lead, inventory, traffic, loaders, safety, registration and runners. | Maintains coverage. |
| commoditypodops.staffing.briefing | shift briefing | METHOD | Briefing covers stock, issue rules, safety, communication and expected demand. | Aligns staff. |
| commoditypodops.staffing.loader_safety | loader safety | SAFETY_RULE | Loaders use safe lifting, hydration, PPE and vehicle awareness. | Reduces injury. |
| commoditypodops.staffing.volunteer | volunteer role | CONSTRAINT | Volunteers work within assigned roles and supervision. | Keeps operation controlled. |
| commoditypodops.safety.heat | heat safety | SAFETY_RULE | Heat plan includes water, shade, breaks and medical escalation. | Protects staff/public. |
| commoditypodops.safety.conflict | conflict management | METHOD | Conflict over shortages or limits routes to supervisor and security. | Reduces escalation. |
| commoditypodops.safety.incident | incident report | RECORD | Incidents record injury, crash, threat, lost child, theft or medical event. | Supports review. |
| commoditypodops.safety.weather | weather action | METHOD | Weather action covers lightning, wind, smoke, flood or closure thresholds. | Keeps site safe. |
| commoditypodops.communication.public_notice | public notice | METHOD | Notice states location, hours, items, limits, access, documents and transport. | Guides residents. |
| commoditypodops.communication.site_update | site update | METHOD | Updates announce stockouts, wait times, closure or relocation. | Reduces frustration. |
| commoditypodops.communication.language | language support | METHOD | Signs and scripts use common local languages and icons. | Improves access. |
| commoditypodops.communication.partner | partner coordination | METHOD | Partners receive stock, demand, access and special population needs. | Aligns distribution. |
| commoditypodops.records.daily_log | daily log | RECORD | Log stores staff, weather, stock, counts, incidents and issues. | Summarizes operation. |
| commoditypodops.records.sitrep | POD situation report | RECORD | Situation report summarizes hours, households served, stock status, safety issues and needs. | Informs command. |
| commoditypodops.records.cost | cost record | RECORD | Costs track commodities, transport, labor, equipment and security. | Supports finance. |
| commoditypodops.records.retention | retention rule | CONSTRAINT | Records follow emergency, grant, finance and privacy schedules. | Preserves audit. |
| commoditypodops.qa.reconciliation | reconciliation | QUALITY_CHECK | Inventory reconciles deliveries, issues, losses and remaining stock. | Detects errors. |
| commoditypodops.qa.lane_observation | lane observation | QUALITY_CHECK | Supervisors observe lanes for rule compliance and safety. | Improves consistency. |
| commoditypodops.metrics.throughput | throughput | MEASUREMENT | Throughput tracks households/vehicles served per hour. | Shows capacity. |
| commoditypodops.metrics.unmet_demand | unmet demand | MEASUREMENT | Unmet demand captures turnaways, stockouts and requests not filled. | Guides resupply. |
| commoditypodops.demob.site_close | site closeout | METHOD | Closeout removes stock, cones, trash and signs; restores site. | Ends operation cleanly. |
| commoditypodops.demob.stock_transfer | stock transfer | METHOD | Remaining commodities transfer to another POD, shelter, cache or partner. | Avoids waste. |
| commoditypodops.review.after_action | after-action review | METHOD | Review captures site layout, demand, traffic, shortages and public messaging lessons. | Improves next POD. |
| commoditypodops.governance.site_owner | site owner | RECORD | Site owner coordinates logistics, safety, public information and partners. | Keeps accountability clear. |
