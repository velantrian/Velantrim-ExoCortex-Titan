# BATCH 373: Emergency Logistics Staging Area Operations

**KnowledgeUnits:** 44  
**Namespace:** `logstageops.*`  
**Scope:** receiving, staging, inventory, dispatch, safety, traffic flow and demobilization.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| logstageops.activation.trigger | activation trigger | MODEL | Staging area activates when incident resources need central receiving and dispatch. | Creates logistics control. |
| logstageops.activation.site | site selection | METHOD | Site checks access, space, security, surface, utilities, hazards and proximity. | Picks usable area. |
| logstageops.activation.authority | site authority | RECORD | Authority records owner, lead agency, period and access rules. | Clarifies control. |
| logstageops.activation.layout | layout plan | METHOD | Layout separates inbound, inspection, storage, outbound, parking and staff areas. | Reduces congestion. |
| logstageops.receiving.delivery_id | delivery ID | RECORD | Delivery ID links supplier, carrier, load, time, contents and condition. | Tracks inbound goods. |
| logstageops.receiving.checkin | vehicle check-in | METHOD | Drivers check in with manifest, destination, safety and unloading instructions. | Controls arrival flow. |
| logstageops.receiving.inspection | receiving inspection | QUALITY_CHECK | Inspection checks count, damage, temperature, labels and hazards. | Prevents bad stock. |
| logstageops.receiving.exception | receiving exception | RECORD | Exceptions record overage, shortage, damage, wrong item or missing paperwork. | Supports correction. |
| logstageops.inventory.item_record | item record | RECORD | Item record stores type, quantity, unit, lot, location and status. | Makes stock visible. |
| logstageops.inventory.location | location code | RECORD | Location code maps yard, tent, pallet, rack or container. | Speeds finding items. |
| logstageops.inventory.cycle_count | cycle count | QUALITY_CHECK | Counts compare physical goods to system records. | Detects drift. |
| logstageops.inventory.reserved_stock | reserved stock | CONSTRAINT | Reserved stock is held for priority mission or future wave. | Avoids accidental issue. |
| logstageops.staging.zone | staging zone | METHOD | Zones group water, food, medical, shelter, tools, fuel and equipment. | Organizes operations. |
| logstageops.staging.pallet_label | pallet label | RECORD | Label shows item, quantity, destination, priority and handling needs. | Prevents dispatch errors. |
| logstageops.staging.crossdock | cross-dock | METHOD | High-priority goods move from inbound to outbound without storage. | Speeds delivery. |
| logstageops.staging.cold_storage | cold storage | SAFETY_RULE | Temperature-sensitive goods use monitored cold storage or rapid transfer. | Protects supplies. |
| logstageops.request.resource_request | resource request | RECORD | Request records mission, item, quantity, destination, priority and requester. | Controls outbound demand. |
| logstageops.request.validation | request validation | QUALITY_CHECK | Validation checks authorization, need, duplication and availability. | Prevents misuse. |
| logstageops.request.substitution | substitution | METHOD | Substitution offers equivalent items when exact item is unavailable. | Keeps missions moving. |
| logstageops.request.shortage | shortage notice | METHOD | Shortage notice informs requester of partial fill, delay or alternate source. | Sets expectations. |
| logstageops.dispatch.pick_ticket | pick ticket | RECORD | Pick ticket lists item, quantity, location, destination and route. | Guides loaders. |
| logstageops.dispatch.load_plan | load plan | METHOD | Load plan orders goods by weight, priority, route and unloading sequence. | Prevents unsafe loads. |
| logstageops.dispatch.driver_packet | driver packet | RECORD | Packet includes manifest, route, contacts, delivery proof and safety notes. | Supports delivery. |
| logstageops.dispatch.proof | delivery proof | RECORD | Proof captures receiver, time, condition, shortages and signature/photo. | Closes loop. |
| logstageops.traffic.inbound_lane | inbound lane | METHOD | Inbound lanes separate trucks, small vehicles, emergency units and pedestrians. | Reduces collisions. |
| logstageops.traffic.outbound_lane | outbound lane | METHOD | Outbound lanes stage loaded vehicles for dispatch order. | Improves flow. |
| logstageops.traffic.parking | parking control | METHOD | Parking separates staff, volunteers, drivers, equipment and visitors. | Keeps access clear. |
| logstageops.traffic.signage | signage | METHOD | Signs direct check-in, speed, PPE, hazards, loading and exits. | Reduces confusion. |
| logstageops.safety.site_hazards | hazard assessment | SAFETY_RULE | Hazards include forklifts, heat, fuel, unstable loads, night work and traffic. | Protects workers. |
| logstageops.safety.ppe | PPE rule | SAFETY_RULE | PPE requirements match lifting, traffic, weather and material hazards. | Reduces injury. |
| logstageops.safety.forklift | forklift control | SAFETY_RULE | Forklift operators, spotters and pedestrian zones are controlled. | Prevents serious incidents. |
| logstageops.safety.incident | incident report | RECORD | Incidents record injury, near miss, spill, vehicle damage or security issue. | Supports correction. |
| logstageops.security.access | access control | METHOD | Access limits site to authorized staff, drivers, volunteers and officials. | Protects resources. |
| logstageops.security.high_value | high-value storage | SAFETY_RULE | Fuel, medical, electronics or scarce items use locked or guarded storage. | Prevents theft. |
| logstageops.security.seals | seal control | RECORD | Seals track closed trailers, containers and controlled loads. | Maintains integrity. |
| logstageops.staffing.roster | staffing roster | RECORD | Roster tracks logistics, inventory, loaders, safety, traffic and admin roles. | Maintains coverage. |
| logstageops.staffing.briefing | shift briefing | METHOD | Briefing covers missions, hazards, inventory, weather and traffic changes. | Aligns team. |
| logstageops.records.sitrep | logistics sitrep | RECORD | Sitrep reports inbound, outbound, stock, shortages, staffing and issues. | Feeds command. |
| logstageops.records.cost | cost record | RECORD | Costs track labor, rentals, fuel, equipment, supplies and damage. | Supports reimbursement. |
| logstageops.metrics.throughput | throughput | MEASUREMENT | Throughput measures loads received, staged and dispatched per period. | Shows capacity. |
| logstageops.metrics.order_cycle | order cycle time | MEASUREMENT | Cycle time measures request-to-delivery proof. | Reveals bottlenecks. |
| logstageops.demob.site_restore | site restoration | METHOD | Demob removes stock, cleans site, repairs damage and returns keys. | Closes facility. |
| logstageops.demob.final_reconcile | final reconciliation | QUALITY_CHECK | Final reconciliation matches remaining stock, dispatch proofs, losses and transfers. | Prevents unresolved inventory gaps. |
| logstageops.review.after_action | after-action review | METHOD | Review captures layout, inventory accuracy, safety, traffic and dispatch lessons. | Improves next staging area. |
