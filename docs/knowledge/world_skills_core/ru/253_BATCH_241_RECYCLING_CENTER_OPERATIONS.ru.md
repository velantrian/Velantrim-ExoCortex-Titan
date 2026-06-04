# BATCH_241 — Recycling Center Operations Detail
# world_skills_core · source: world_skills_core:batch_241:recycling_center_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| recycleops.dropoff.site_layout | Recycling center site layout | invariant | Layout separates entry, scales, drop-off bays, traffic lanes, staff zones and exits. | safe flow |
| recycleops.dropoff.material_bay | Recycling material drop-off bay | invariant | Bay identifies accepted material, container, contamination limits and signage. | correct sorting |
| recycleops.dropoff.customer_greeting | Recycling customer greeting | variant | Greeting directs visitor to materials, rules, fees, hazards and unloading method. | reduce confusion |
| recycleops.dropoff.vehicle_queue | Recycling vehicle queue | variant | Queue manages peak arrivals, trailers, pedestrians, commercial vehicles and overflow. | prevent congestion |
| recycleops.dropoff.unacceptable_item | Recycling unacceptable item handling | invariant | Handling rejects trash, hazardous, wet, contaminated or unsupported items with guidance. | protect process |
| recycleops.sorting.presort_line | Recycling presort line | invariant | Line removes bags, tanglers, hazardous items, bulky objects and obvious contamination. | protect equipment |
| recycleops.sorting.paper_sort | Recycling paper sort | variant | Sort separates cardboard, mixed paper, office paper, cartons and wet material. | improve value |
| recycleops.sorting.plastic_sort | Recycling plastic sort | variant | Sort separates containers by resin, color, film, contamination and market rules. | marketable bales |
| recycleops.sorting.metal_sort | Recycling metal sort | variant | Sort separates aluminum, steel cans, scrap metal and nonconforming items. | recover metals |
| recycleops.sorting.glass_sort | Recycling glass sort | variant | Sort handles color, breakage, ceramics, mirrors, bulbs and grit contamination. | safer glass stream |
| recycleops.contamination.contamination_audit | Recycling contamination audit | invariant | Audit samples load, identifies contaminants, estimates rate and routes education. | improve quality |
| recycleops.contamination.load_reject | Recycling load rejection | invariant | Rejection documents source, reason, photos, weight, notice and disposal path. | prevent bad stock |
| recycleops.contamination.battery_find | Battery contamination finding | invariant | Finding isolates battery, records source if known and prevents fire risk. | facility safety |
| recycleops.contamination.tangler_control | Recycling tangler control | invariant | Control removes hoses, cords, film, chains and straps before equipment jams. | reduce downtime |
| recycleops.baling.baler_setup | Recycling baler setup | invariant | Setup checks material type, wire, pressure, guards, emergency stops and operator readiness. | safe baling |
| recycleops.baling.bale_spec | Recycling bale specification | invariant | Specification defines weight, size, density, contamination limit, wire count and label. | sell bales |
| recycleops.baling.bale_label | Recycling bale label | invariant | Label records material, date, weight, grade, operator and lot. | trace inventory |
| recycleops.baling.bale_storage | Recycling bale storage | variant | Storage organizes bales by grade, buyer, age, fire lane and weather protection. | ship efficiently |
| recycleops.baling.baler_jam | Recycling baler jam response | invariant | Response locks out equipment, clears jam by trained staff and records downtime. | protect workers |
| recycleops.equipment.conveyor_check | Recycling conveyor check | invariant | Check verifies belts, guards, pull cords, bearings, debris and emergency stops. | equipment safety |
| recycleops.equipment.forklift_use | Recycling forklift use | invariant | Use records inspection, operator, bale movement, pedestrian zones and charging. | safe handling |
| recycleops.equipment.loader_operation | Recycling loader operation | variant | Operation manages piles, bucket loads, visibility, spotters and traffic separation. | safe material movement |
| recycleops.equipment.dust_control | Recycling dust control | variant | Control uses cleaning, ventilation, masks, misting or housekeeping where needed. | worker health |
| recycleops.equipment.fire_watch | Recycling center fire watch | invariant | Watch checks batteries, hot work, piles, smoking, alarms and extinguishers. | prevent fires |
| recycleops.markets.buyer_contract | Recycling buyer contract | variant | Contract defines material grade, price, volume, contamination tolerance and pickup terms. | revenue clarity |
| recycleops.markets.market_price | Recyclable market price | variant | Price record tracks commodity value, buyer quote, grade and effective date. | selling decision |
| recycleops.markets.load_tender | Recycling load tender | invariant | Tender offers bale lot, weights, photos, grade and pickup window to buyer. | arrange sale |
| recycleops.markets.claim_response | Recycling buyer claim response | variant | Response reviews contamination, weight variance, moisture or grade dispute evidence. | protect revenue |
| recycleops.reporting.weight_ticket | Recycling weight ticket | invariant | Ticket records inbound or outbound material, scale weight, source, destination and time. | mass balance |
| recycleops.reporting.diversion_report | Recycling diversion report | invariant | Report summarizes materials received, shipped, rejected, disposed and stored. | sustainability data |
| recycleops.reporting.source_report | Recycling source report | variant | Report compares municipal routes, drop-off users, schools, businesses or events. | target education |
| recycleops.reporting.inventory_report | Recycling inventory report | invariant | Report lists loose stock, bales, rejected material, aging and buyer commitments. | warehouse visibility |
| recycleops.safety.ppe_zone | Recycling PPE zone | invariant | Zone requires high visibility, gloves, eye protection, hearing or respiratory PPE. | reduce injury |
| recycleops.safety.public_separation | Recycling public separation | invariant | Separation keeps visitors away from loaders, balers, conveyors, pits and truck lanes. | public safety |
| recycleops.safety.sharps_response | Recycling sharps response | invariant | Response isolates needles or blades with trained pickup and incident reporting. | prevent exposure |
| recycleops.safety.chemical_find | Recycling chemical finding | invariant | Finding isolates unknown liquids, aerosols, fuels or corrosives and escalates disposal. | hazard control |
| recycleops.education.signage_update | Recycling signage update | variant | Update revises accepted items, photos, languages, placement and seasonal messages. | improve sorting |
| recycleops.education.load_feedback | Recycling load feedback | variant | Feedback tells hauler or source what contaminants were found and how to improve. | reduce contamination |
| recycleops.education.tour_control | Recycling center tour control | variant | Control manages visitors, PPE, routes, photos, questions and safety boundaries. | education safely |
| recycleops.close.daily_cleanup | Recycling center daily cleanup | invariant | Cleanup clears floors, bays, drains, equipment, litter, glass and fire hazards. | reset site |
| recycleops.close.endofday_lockout | Recycling end-of-day lockout | invariant | Lockout secures gates, equipment, scales, offices, hazardous holds and alarms. | secure facility |
| recycleops.metrics.recycling_kpi | Recycling center KPI | variant | KPI tracks tons received, contamination, bale quality, downtime, revenue and safety incidents. | manage center |
| recycleops.continuity.market_disruption | Recycling market disruption response | variant | Response adjusts storage, sorting, buyer search, public messaging and disposal fallback. | handle shocks |
| recycleops.continuity.equipment_outage | Recycling equipment outage | invariant | Outage plan reroutes material, pauses intake, schedules repair and records lost capacity. | continuity |
