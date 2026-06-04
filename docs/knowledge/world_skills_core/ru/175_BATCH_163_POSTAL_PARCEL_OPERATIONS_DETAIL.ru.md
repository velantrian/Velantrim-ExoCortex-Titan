# BATCH_163 — Postal & Parcel Operations Detail
# world_skills_core · source: world_skills_core:batch_163:postal_parcel_operations_detail
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| parcelops.induction.parcel_induction | Parcel induction | invariant | Parcel induction вводит отправление в сеть через прием, сканирование, маркировку и первичную проверку. | старт tracking |
| parcelops.induction.acceptance_scan | Acceptance scan | invariant | Acceptance scan подтверждает, что оператор получил отправление в определенном месте и времени. | доказать прием |
| parcelops.induction.label_readability | Label readability | invariant | Читаемая этикетка нужна для автоматической сортировки, route planning и customer visibility. | label drives movement |
| parcelops.induction.dimension_capture | Dimension capture | invariant | Dimension capture фиксирует размер и вес посылки для тарифа, capacity и handling rules. | объем тоже стоимость |
| parcelops.induction.dangerous_goods_check | Dangerous goods check | invariant | Проверка dangerous goods выявляет запрещенные или ограниченные вложения до входа в сеть. | безопасность сети |
| parcelops.induction.address_quality | Address quality | invariant | Address quality проверяет полноту, postcode, locality, apartment, recipient и deliverability. | плохой адрес задерживает |
| parcelops.sorting.primary_sort | Primary sort | invariant | Primary sort разделяет отправления по крупным направлениям, hubs, regions или transport lanes. | first network split |
| parcelops.sorting.secondary_sort | Secondary sort | invariant | Secondary sort уточняет направление до depot, route, delivery zone или carrier partner. | ближе к последней миле |
| parcelops.sorting.missort | Missort | invariant | Missort отправляет parcel в неверный поток и вызывает задержку, rework или customer complaint. | ошибка сортировки |
| parcelops.sorting.chute_overflow | Chute overflow | variant | Chute overflow возникает, когда сортировочный выход переполнен и начинает тормозить line flow. | capacity bottleneck |
| parcelops.sorting.manual_sort | Manual sort | variant | Manual sort нужен для нестандартных, поврежденных, unreadable или exception parcels. | automation cannot handle all |
| parcelops.sorting.sort_plan | Sort plan | invariant | Sort plan задает destinations, cutoffs, equipment settings, staffing и contingency routing. | сортировка по плану |
| parcelops.routing.route_sequence | Route sequencing | invariant | Route sequencing упорядочивает доставки по geography, service commitments, traffic и vehicle constraints. | водитель едет логично |
| parcelops.routing.delivery_zone | Delivery zone | invariant | Delivery zone группирует адреса для устойчивого распределения объема между routes. | territory design |
| parcelops.routing.cutoff_time | Parcel cutoff time | invariant | Cutoff time определяет последний момент, когда отправление может попасть в конкретный transport или delivery cycle. | deadline network |
| parcelops.routing.linehaul_dispatch | Linehaul dispatch | invariant | Linehaul dispatch отправляет trailers или containers между hubs по расписанию, capacity и priority. | магистральная сеть |
| parcelops.routing.load_plan | Parcel load plan | invariant | Load plan определяет, какие containers, bags или parcels идут в vehicle and in what order. | loading supports delivery |
| parcelops.routing.route_rebalance | Route rebalance | variant | Rebalance перераспределяет stops или parcels при перегрузе, absence, vehicle issue или weather disruption. | keep routes feasible |
| parcelops.tracking.event_scan | Tracking event scan | invariant | Event scan updates parcel status, location and time in customer and operational systems. | visibility through network |
| parcelops.tracking.out_for_delivery | Out-for-delivery event | invariant | Out-for-delivery event означает, что parcel assigned to courier route for delivery attempt. | customer expectation |
| parcelops.tracking.delivery_attempt | Delivery attempt | invariant | Delivery attempt records whether courier reached address, delivered, failed, redirected or left notice. | last-mile truth |
| parcelops.tracking.proof_of_delivery | Proof of delivery | invariant | Proof of delivery may include signature, photo, PIN, geolocation or recipient confirmation. | доказать завершение |
| parcelops.tracking.exception_event | Parcel exception event | invariant | Exception event records abnormal condition such as damage, delay, address issue, hold or failed delivery. | signal to intervene |
| parcelops.tracking.scan_compliance | Scan compliance | invariant | Scan compliance measures whether required scans occur at expected handoff points. | network data quality |
| parcelops.delivery.safe_place | Safe-place delivery | variant | Safe-place delivery leaves parcel at approved location when policy, risk and customer preference allow it. | convenience with risk |
| parcelops.delivery.recipient_not_home | Recipient not home | invariant | Recipient-not-home outcome triggers notice, retry, pickup point, locker or return workflow. | failed attempt path |
| parcelops.delivery.locker_delivery | Parcel locker delivery | variant | Locker delivery uses authenticated compartment access and changes delivery, pickup and exception processes. | unattended handover |
| parcelops.delivery.age_check | Age-check delivery | variant | Age-check delivery verifies recipient eligibility for restricted goods according to policy and law. | not every parcel can drop |
| parcelops.delivery.cod_collection | Cash-on-delivery collection | variant | COD collection links parcel handover to payment capture, receipt and reconciliation. | delivery plus money |
| parcelops.delivery.route_closeout | Route closeout | invariant | Route closeout reconciles delivered, failed, returned, cash, devices and undelivered parcels. | finish driver day |
| parcelops.returns.return_label | Return label | invariant | Return label identifies reverse shipment, merchant, customer, service and routing. | reverse logistics starts |
| parcelops.returns.return_authorization | Return authorization | variant | Authorization confirms that merchant or carrier allows return under specific conditions. | control reverse flow |
| parcelops.returns.undeliverable_return | Undeliverable return | invariant | Undeliverable return sends parcel back when delivery cannot be completed after defined attempts or holds. | close failed delivery |
| parcelops.returns.damage_claim | Parcel damage claim | invariant | Damage claim records item condition, packaging, evidence, liability review and compensation path. | structured dispute |
| parcelops.returns.lost_parcel_investigation | Lost parcel investigation | invariant | Investigation checks scans, containers, depot records, route notes and exception logs to locate parcel. | find before compensate |
| parcelops.returns.customer_refund_signal | Refund signal | variant | Refund signal informs merchant or service team that parcel status may justify customer refund or replacement. | commerce depends on tracking |
| parcelops.capacity.peak_plan | Peak parcel plan | variant | Peak plan prepares staffing, linehaul, sort capacity, lockers, vehicles and customer messaging for high volume. | seasonality hits network |
| parcelops.capacity.trailer_utilization | Trailer utilization | invariant | Trailer utilization measures how well transport capacity is used by volume, weight or container count. | moving air is expensive |
| parcelops.capacity.depot_backlog | Depot backlog | invariant | Backlog shows parcels waiting beyond planned processing, dispatch or delivery cycle. | visible congestion |
| parcelops.capacity.route_density | Route density | invariant | Route density reflects stops or parcels per area and affects cost, speed and service design. | geography shapes economics |
| parcelops.quality.service_level | Parcel service level | invariant | Service level compares actual delivery time with promised product or SLA. | promise versus reality |
| parcelops.quality.damage_rate | Parcel damage rate | invariant | Damage rate tracks damaged parcels by lane, packaging, handler, product type or facility. | find weak points |
| parcelops.quality.complaint_code | Parcel complaint code | invariant | Complaint codes classify customer issues for trends, root cause and process improvement. | complaints become data |
| parcelops.quality.network_root_cause | Network root cause | invariant | Root cause analysis connects delay or failure to scan gap, capacity, address, transport, sort or delivery issue. | fix network, not symptom |
