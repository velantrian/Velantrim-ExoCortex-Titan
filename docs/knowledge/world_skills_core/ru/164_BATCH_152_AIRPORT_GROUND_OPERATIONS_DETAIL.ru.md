# BATCH_152 — Airport Ground Operations Detail
# world_skills_core · source: world_skills_core:batch_152:airport_ground_operations_detail
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| airportops.turnaround.turnaround_plan | Aircraft turnaround plan | invariant | Turnaround plan связывает arrival, blocks-on, unloading, servicing, boarding, pushback и departure target. | минуты складываются |
| airportops.turnaround.ground_time | Ground time | invariant | Ground time измеряет период между прибытием самолета на стоянку и готовностью к отправлению. | capacity gate |
| airportops.turnaround.stand_allocation | Stand allocation | variant | Назначение стоянки учитывает aircraft size, terminal, passenger flow, connections, towing, restrictions и disruption risk. | самолету нужно место |
| airportops.turnaround.turnaround_coordinator | Turnaround coordinator | invariant | Coordinator синхронизирует ramp, cabin, fuel, catering, baggage, gate и crew during turnaround. | один operational view |
| airportops.turnaround.off_block_time | Off-block time | invariant | Off-block time фиксирует момент начала движения от stand и влияет на punctuality metrics. | точка отправления |
| airportops.ramp.ramp_safety_zone | Ramp safety zone | invariant | Ramp safety zone ограничивает движение людей, техники и equipment near aircraft engines, wings and service points. | безопасность около самолета |
| airportops.ramp.fod_walk | FOD walk | invariant | FOD walk ищет foreign object debris на стоянке или рулежной зоне до повреждения aircraft или equipment. | мелочь может стоить дорого |
| airportops.ramp.marshalling | Aircraft marshalling | invariant | Marshalling использует стандартизированные сигналы или guidance system для безопасного позиционирования aircraft. | точная парковка |
| airportops.ramp.chocks_cones | Chocks and safety cones | invariant | Chocks и cones обозначают protected zones, предотвращают движение aircraft и направляют ground equipment. | базовый ramp barrier |
| airportops.ramp.gse_positioning | Ground support equipment positioning | invariant | GSE positioning должен учитывать clearance, aircraft doors, service panels, jet blast и emergency access. | техника не должна мешать |
| airportops.ramp.jet_blast | Jet blast hazard | invariant | Jet blast может опрокинуть equipment, повредить объекты и травмировать персонал behind aircraft. | уважать engine zones |
| airportops.ramp.pushback_clearance | Pushback clearance | invariant | Pushback clearance подтверждает, что aircraft, tug, headset, route and ATC/ground permissions are ready. | уход со стоянки без конфликта |
| airportops.baggage.baggage_makeup | Baggage makeup | invariant | Baggage makeup сортирует багаж по рейсу, destination, priority и loading sequence. | мешки идут к правильному aircraft |
| airportops.baggage.baggage_reconciliation | Baggage reconciliation | invariant | Reconciliation багажа сопоставляет loaded bags with boarded passengers и handling records. | safety and tracking |
| airportops.baggage.mishandled_bag | Mishandled baggage | invariant | Mishandled bag возникает при задержке, неправильной загрузке, потере, повреждении или неверной маркировке. | customer impact |
| airportops.baggage.oversized_baggage | Oversized baggage handling | variant | Oversized baggage требует отдельного приема, screening, transport, loading and damage controls. | не проходит обычной лентой |
| airportops.baggage.unit_load_device | Unit load device | invariant | ULD объединяет багаж или cargo в контейнер или pallet, совместимый с aircraft loading. | ускорить обработку |
| airportops.baggage.load_sheet | Load sheet | invariant | Load sheet отражает weight, balance, cargo, baggage, fuel и passenger distribution for aircraft dispatch. | aircraft balance matters |
| airportops.passenger.gate_readiness | Gate readiness | invariant | Gate readiness означает готовность gate system, staff, boarding zones, documents, announcements and aircraft status. | посадка без задержки |
| airportops.passenger.boarding_sequence | Boarding sequence | variant | Boarding sequence управляет priority, groups, accessibility, cabin flow and departure time pressure. | посадка как поток |
| airportops.passenger.connection_protection | Connection protection | variant | Connection protection оценивает delayed inbound passengers against departure delay, baggage and network impact. | спасать стыковки разумно |
| airportops.passenger.prm_assistance | PRM assistance | invariant | Помощь пассажирам с reduced mobility требует booking, equipment, trained staff, timing and dignity. | доступность аэропорта |
| airportops.passenger.denied_boarding | Denied boarding process | variant | Denied boarding process управляет overbooking, volunteers, compensation rules, rebooking and communication. | конфликтный момент |
| airportops.passenger.disruption_queue | Passenger disruption queue | invariant | Disruption queue сортирует affected passengers by destination, urgency, status and available reaccommodation options. | recovery after delay |
| airportops.services.fueling_coordination | Aircraft fueling coordination | invariant | Fueling coordination связывает fuel order, truck, safety zone, bonding, paperwork and departure timing. | топливо без риска |
| airportops.services.catering_exchange | Catering exchange | invariant | Catering exchange заменяет carts, supplies and waste with seal checks, timing and aircraft access control. | cabin readiness |
| airportops.services.cabin_cleaning | Cabin cleaning turnaround | variant | Cabin cleaning balances speed, hygiene, lost-item checks, seat pockets, lavatories and crew handover. | качество при дефиците времени |
| airportops.services.potable_water_service | Potable water service | invariant | Potable water servicing requires approved water source, hose hygiene, aircraft connection and record discipline. | вода на борту |
| airportops.services.lavatory_service | Lavatory service | invariant | Lavatory service removes waste and refills fluids under hygiene, spill control and aircraft safety rules. | неприятно, но критично |
| airportops.services.deicing_request | Deicing request | variant | Deicing request depends on weather, aircraft contamination, holdover time, fluid type and departure sequence. | winter operations |
| airportops.weather.holdover_time | Holdover time | invariant | Holdover time estimates protection duration after deicing/anti-icing under specified precipitation and temperature conditions. | окно после обработки |
| airportops.weather.lightning_alert | Lightning alert | invariant | Lightning alert can stop ramp activity to protect personnel from strike risk. | safety overrides schedule |
| airportops.weather.low_visibility | Low visibility procedure | variant | Low visibility procedure changes movement rules, spacing, guidance and equipment use on the airfield. | operations slow down |
| airportops.weather.snow_plan | Airport snow plan | variant | Snow plan prioritizes runways, taxiways, stands, equipment, chemicals and staffing during winter disruption. | keep airport usable |
| airportops.control.airport_slot | Airport slot | variant | Slot allocates planned arrival or departure time at capacity-constrained airports. | schedule as scarce resource |
| airportops.control.ground_stop | Ground stop | variant | Ground stop temporarily prevents departures to a destination or airspace due to capacity, weather or disruption. | delay before takeoff |
| airportops.control.aodb_update | AODB update | invariant | Airport operational database update keeps flight status, stand, gate, belt, times and resources synchronized. | shared operational truth |
| airportops.control.turnaround_milestone | Turnaround milestone | invariant | Milestones track doors open, bags off, fuel start, boarding start, doors closed and ready-to-go. | manage delay causes |
| airportops.control.delay_code | Delay code | invariant | Delay code classifies the primary cause of delay for performance review and accountability. | learn from lateness |
| airportops.security.airside_pass | Airside pass control | invariant | Airside pass control restricts access to secure zones by identity, training, authorization and validity. | secure perimeter |
| airportops.security.secure_supply_chain | Secure supply chain | variant | Secure supply chain controls goods entering aircraft or airside areas through screening, seals and known suppliers. | prevent tampering |
| airportops.security.unattended_bag | Unattended bag procedure | invariant | Unattended bag procedure protects passengers and operations through reporting, isolation, assessment and coordinated response. | simple object, serious protocol |
| airportops.irregular.irrops_bridge | IROPS coordination bridge | variant | Irregular operations bridge coordinates airline, airport, handlers, ATC, security and passenger service during disruption. | crisis rhythm |
| airportops.irregular.post_operation_review | Post-operation review | invariant | Review after disruption analyzes timeline, decisions, resource constraints, communications and improvement actions. | better next event |
