# BATCH_155 — Seaport Terminal & Yard Operations Detail
# world_skills_core · source: world_skills_core:batch_155:seaport_terminal_yard_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| portops.berth.berth_plan | Berth plan | invariant | Berth plan assigns vessels to berths by ETA, draft, cargo, crane needs, tidal windows and terminal capacity. | причал как ограниченный ресурс |
| portops.berth.vessel_eta | Vessel ETA update | invariant | ETA update changes labor, berth, pilot, tug, yard and truck planning when vessel arrival shifts. | расписание живое |
| portops.berth.draft_restriction | Draft restriction | invariant | Draft restriction limits vessel movement by water depth, tide, load condition and channel constraints. | глубина решает доступ |
| portops.berth.pilotage_window | Pilotage window | variant | Pilotage window coordinates pilot availability, tides, weather, traffic and port authority clearance. | заход судна по окну |
| portops.berth.mooring_plan | Mooring plan | invariant | Mooring plan defines lines, bollards, fendering, tension risk and safe access between vessel and quay. | судно должно стоять безопасно |
| portops.berth.berth_productivity | Berth productivity | invariant | Berth productivity measures cargo moves or tons handled per berth time under specific operating conditions. | скорость использования причала |
| portops.crane.crane_split | Crane split | variant | Crane split assigns quay cranes across vessel bays to balance speed, interference and stability constraints. | краны не работают хаотично |
| portops.crane.crane_sequence | Crane sequence | invariant | Crane sequence orders container or cargo moves to protect vessel stability, hatch access and operational flow. | порядок грузовых операций |
| portops.crane.twin_lift | Twin lift operation | variant | Twin lift handles two compatible containers at once when equipment, weight and stowage allow it. | быстрее, но не всегда |
| portops.crane.crane_interference | Crane interference | invariant | Crane interference occurs when nearby cranes, booms, vessel structures or unsafe zones constrain simultaneous moves. | productivity has geometry |
| portops.crane.lashing_team | Lashing team | invariant | Lashing team secures or releases containers on vessel using twistlocks, rods and safety procedures. | груз не должен двигаться |
| portops.crane.exception_move | Exception move | variant | Exception move handles damaged, overweight, misdeclared or blocked cargo outside normal sequence. | выброс из стандартного потока |
| portops.yard.yard_block | Yard block | invariant | Yard block organizes container storage by category, destination, vessel, dwell time or equipment strategy. | склад порта в блоках |
| portops.yard.stack_plan | Container stack plan | invariant | Stack plan positions containers to reduce rehandles, respect weight limits and support next moves. | меньше лишних перестановок |
| portops.yard.rehandle | Yard rehandle | invariant | Rehandle is an extra move caused by buried containers, plan changes or poor stack alignment. | скрытая потеря продуктивности |
| portops.yard.dwell_time | Container dwell time | invariant | Dwell time measures how long cargo stays in terminal before pickup, loading or transfer. | congestion signal |
| portops.yard.reefer_monitoring | Reefer monitoring | invariant | Reefer monitoring checks plugged status, temperature setpoint, alarms and power availability for refrigerated containers. | cold chain in yard |
| portops.yard.empty_container_pool | Empty container pool | variant | Empty pool management balances available empties by size, type, shipping line and demand forecast. | equipment imbalance |
| portops.gate.truck_appointment | Truck appointment system | variant | Appointment system schedules truck arrivals to smooth gate demand and reduce queue congestion. | очередь управляется временем |
| portops.gate.gate_in | Gate-in process | invariant | Gate-in records truck, driver, container, booking, seal, damage, weight and customs status. | вход в terminal truth |
| portops.gate.gate_out | Gate-out process | invariant | Gate-out confirms release, container identity, documents, seals, holds and handover to trucker. | cargo leaves with evidence |
| portops.gate.ocr_gate | OCR gate | variant | OCR gate reads container numbers, plates and images automatically but still needs exception handling. | automation with review |
| portops.gate.truck_turn_time | Truck turn time | invariant | Truck turn time measures how long a truck spends from gate entry to exit. | service level for haulers |
| portops.gate.chassis_availability | Chassis availability | variant | Chassis availability constrains container pickup and delivery when transport equipment is scarce. | gate capacity depends on chassis |
| portops.customs.customs_hold | Customs hold | invariant | Customs hold prevents cargo release until authority requirements, inspection or documentation are cleared. | не выпускать без clearance |
| portops.customs.release_order | Release order | invariant | Release order authorizes terminal to deliver cargo to the correct party under required conditions. | legal handover |
| portops.customs.exam_move | Customs exam move | variant | Exam move transfers container to inspection area while preserving chain of custody and terminal records. | досмотр как отдельный поток |
| portops.customs.seal_check | Container seal check | invariant | Seal check compares physical seal with documentation and flags tampering, mismatch or missing seal. | cargo integrity |
| portops.customs.hazardous_manifest | Hazardous cargo manifest | invariant | Hazardous manifest identifies dangerous goods class, segregation, emergency data and handling restrictions. | safety before storage |
| portops.customs.overweight_container | Overweight container | invariant | Overweight container exceeds declared, legal or equipment limits and requires control before movement. | weight can break plans |
| portops.safety.twistlock_hazard | Twistlock hazard | invariant | Twistlocks create pinch, falling-object and mislock risks during vessel and yard operations. | small part, serious risk |
| portops.safety.pedestrian_separation | Yard pedestrian separation | invariant | Pedestrian separation keeps people away from straddles, trucks, reach stackers and crane work zones. | terminal traffic is dangerous |
| portops.safety.wind_stop | Crane wind stop | variant | Wind stop suspends crane operations when wind speed exceeds safe operating limits. | weather overrides productivity |
| portops.safety.dropped_container | Dropped container incident | invariant | Dropped container incident requires area isolation, injury check, equipment inspection and investigation. | high-energy event |
| portops.safety.mooring_snapback | Mooring snapback zone | invariant | Snapback zone marks where parted mooring lines can recoil with lethal force. | invisible danger zone |
| portops.safety.spill_response | Port spill response | invariant | Spill response isolates source, protects drains or water, notifies responders and records environmental impact. | waterway protection |
| portops.planning.vessel_stowage | Vessel stowage plan | invariant | Stowage plan places containers by destination, weight, hazardous segregation, reefer needs and vessel stability. | ship plan drives terminal work |
| portops.planning.cutoff_time | Cargo cutoff time | invariant | Cutoff time defines latest cargo acceptance for a vessel to protect documentation and loading sequence. | deadline for exporters |
| portops.planning.transshipment_connection | Transshipment connection | variant | Transshipment planning connects inbound and outbound vessels while managing dwell, missed connections and yard positions. | port as network node |
| portops.planning.terminal_operating_system | Terminal operating system | invariant | TOS coordinates vessel, yard, gate, equipment, holds, moves and operational reporting. | digital control room |
| portops.planning.equipment_dispatch | Equipment dispatch | invariant | Equipment dispatch assigns cranes, trucks, straddles, handlers or gangs to work queues and priorities. | machines to tasks |
| portops.performance.moves_per_hour | Moves per hour | invariant | Moves per hour measures handling productivity for crane, berth, gang or terminal under defined scope. | comparable only with context |
| portops.performance.yard_density | Yard density | invariant | Yard density indicates how full storage areas are and predicts rehandles, congestion and slowdowns. | too full becomes slow |
| portops.performance.vessel_delay_review | Vessel delay review | variant | Delay review identifies weather, labor, equipment, documentation, berth conflict or yard causes. | learn from port delays |
