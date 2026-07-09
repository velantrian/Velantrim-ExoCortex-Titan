# BATCH 882: Irrigation Repair

**KnowledgeUnits:** 50
**Namespace:** `irrigation.ops.*`
**Scope:** zone, valve, sprinkler, backflow, winterize, controller

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| irrigation.ops.zone_wiring_ohm_test | Zone Wiring — Ohm Test | METHOD | Сolenoid: 20-60 Ω multimeter at controller. Open circuit — wire break. Short — water in box. Locate with toner. | Replace valve без wire fix — zone still dead. |
| irrigation.ops.valve_diaphragm_rebuild | Valve — Diaphragm Rebuild | METHOD | Клапан течёт: clean debris, replace diaphragm kit same model. Bleed screw open manual test. Flow control adjust. | New valve на dirt in line — leak continues. |
| irrigation.ops.rain_sensor_bypass_check | Rain Sensor — Bypass Check | METHOD | Дождевой датчик: must dry to reset, wire at controller common. Bypass test run zone. Replace if cracked cork. | Dead sensor wet — system never runs, dead lawn. |
| irrigation.ops.head_adjustment_arc | Head — Arc Adjustment | METHOD | Ротатор: arc 40-360°, radius screw. Align не на sidewalk. Match precipitation rate zone. | Spray на driveway — waste и slip hazard. |
| irrigation.ops.pvc_repair_saddle | PVC Repair — Saddle Clamp | METHOD | Прокол: cut section, coupling, primer purple, glue set 15 min pressure. Saddle tee for quick branch. | Dry fit без glue — blowout при включении. |
| irrigation.ops.backflow_test_annual | Backflow — Annual Test | METHOD | RPZ/DCVA: certified tester yearly, tag on device. Shutoff water если fail. Permit some cities. | Expired backflow tag — water company shutoff. |
| irrigation.ops.winterization_blow_out | Winterization — Blow Out | METHOD | Зимовка: compressor CFM per zone size, 50-80 PSI regulated, open zone by zone. Don't exceed pipe rating. | 150 PSI blow — cracked main line spring. |
| irrigation.ops.drip_emitter_clog | Drip — Emitter Clog | METHOD | Капельный: flush line, soak emitters vinegar, replace 2 GPH clogged. Filter at valve 120 mesh. | No filter — все emitters clogged season. |
| irrigation.ops.controller_program_season | Controller — Season Program | METHOD | Программа: cycle soak clay soil, seasonal adjust % summer down spring. Rain delay smart wifi. | Same July schedule October — fungus lawn. |
| irrigation.ops.wire_locator_tone | Wire — Locator Tone | METHOD | Поиск обрыва: tone generator, inductive clamp, walk line. Mark break dig repair splice waterproof. | Dig random — cut 5 good wires. |
| irrigation.ops.rotor_vs_spray_zone | Rotor vs Spray — Zone | VARIANT | Не mix rotors и sprays one zone — different precip rates. Separate valves. | Mixed zone — dry spots и swamp spots. |
| irrigation.ops.main_line_leak_mud | Main Leak — Mud Sign | METHOD | Утечка main: greener grass strip, sinkhole, high water bill. Shut main, isolate section. | Ignore wet spot — main break erodes foundation. |
| irrigation.ops.solenoid_plunger_stuck | Solenoid — Plunger Stuck | METHOD | Вручную twist solenoid — zone on без controller. Stuck open — replace solenoid or debris. | Controller «bad» — просто stuck valve. |
| irrigation.ops.head_height_grade | Head Height — Grade | METHOD | Высота: top flush grade, не sunken — grass blocks. Pop-up 4" shrubs 6". | Sunken head — dry donut around sprinkler. |
| irrigation.ops.tree_root_pipe_lift | Tree Root — Pipe Lift | METHOD | Корни: reroute pipe away, не just cut root large tree. Root guard barrier. | Cut big root — tree fall и pipe crush again. |
| irrigation.ops.pressure_regulation_zone | Pressure — Regulation | METHOD | Давление: 30-50 PSI ideal spray. PRV at valve если municipal high. Fog misting = overpressure. | 80 PSI — heads mist, uneven coverage. |
| irrigation.ops.flow_sensor_leak_detect | Flow Sensor — Leak Detect | VARIANT | Датчик потока: smart controller alert abnormal flow. Catch broken head underground. | Underground leak month — $500 water bill. |
| irrigation.ops.quick_couple_repair | Quick Couple — Repair | METHOD | Быстросъём: replace O-ring, thread tape. Buried quick couple box accessible. | Cross thread — replace entire body. |
| irrigation.ops.lateral_line_depth | Lateral Depth — Code | METHOD | Глубина: 8-12" typical, deeper traffic areas. Mark heads map for future dig. | Shallow lateral — aerator cut flood. |
| irrigation.ops.commercial_clock_battery | Battery — Controller Backup | METHOD | Батарея 9V backup settings power outage. Replace yearly spring. Solar controllers capacitor. | Power blip — lost program desert vacation. |
| irrigation.ops.nozzle_matched_precip | Nozzle — Matched Precipitation | METHOD | MP rotator nozzles: matched precip quarter half full. Even coverage math. | All full circle one corner — flooded corner. |
| irrigation.ops.valve_box_riser | Valve Box — Riser | METHOD | Колодец клапана: level grade, riser if buried deep. Locate map. Don't pave over. | Lost valve box — dig entire lawn find. |
| irrigation.ops.irrigation_tap_meter_size | Tap — Meter Size | METHOD | Отвод: после meter, before PRV house если separate. Dedicated irrigation meter some utilities discount. | Irrigation без meter — sewer charge water. |
| irrigation.ops.dry_well_zone_low | Low Head — Drain Check Valve | METHOD | Низкая зона: check valve prevent drain back, air vacuum relief high points. | Drain out low heads — first cycle air hammer. |
| irrigation.ops.smart_controller_wifi | Smart WiFi — Controller | VARIANT | Rachio/Hydrawise: weather skip, flow monitoring. Customer phone setup included. | Customer can't app — revert dumb timer. |
| irrigation.ops.sod_damage_head_move | Sod — Head Move | METHOD | Новый sod: raise heads, relocate если coverage wrong. Cut sod circle clean. | Head in sod too low — dead ring irrigation. |
| irrigation.ops.chemigation_injection | Chemigation — Injection | VARIANT | Удобрение injector: backflow preventer required, check local ag rules. Residential rare. | Injector без RPZ — fertilizer в drinking water. |
| irrigation.ops.pump_start_relay_well | Pump Start — Relay Well | METHOD | Скважина: pump start relay pressure tank coordination. Irrigation demand drops pressure starts pump. | Wrong relay — pump short cycle burn. |
| irrigation.ops.landscape_lighting_shared | Lighting — Shared Trench | VARIANT | Траншея общая с lighting low voltage separate conduit. Mark irrigation purple wire nut code. | Cut lighting wire — dark yard dispute. |
| irrigation.ops.estimate_zone_count | Estimate — Zone Count | PRACTICAL | Смета: per zone diagnose, per head replace, wire locate hourly. Minimum service call. | Flat repair любой проблемы — 6 часов locate. |
| irrigation.ops.customer_map_update | Map — Update Heads | PROCESS | Карта: laminate for homeowner, mark valves. Update after changes. | No map — next contractor destroys system. |
| irrigation.ops.poly_pipe_fitting | Poly Pipe — Barbed Fitting | METHOD | Полиэтилен: clamp both sides, warm pipe end, worm gear clamp tight. Transition PVC coupling. | No clamp — blow off 80 PSI injury. |
| irrigation.ops.hunter_rain_clik | Rain-Clik — Install Height | METHOD | Датчик на gutter sunny side, wire 18/2 to controller common. Test wet sponge. | Sensor under tree — never dries, brown lawn. |
| irrigation.ops.double_check_install | Double Check — Install | METHOD | DCVA horizontal, test cocks accessible, winter drain if freeze zone. Annual test port. | Frozen DCVA — cracked body spring flood. |
| irrigation.ops.zone_not_covering | Dry Spot — Head Add | METHOD | Сухой участок: head-to-head spacing check, add head same zone если pressure OK. | Raise radius only — neighbor sidewalk soak. |
| irrigation.ops.irrigation_audit_catchcup | Audit — Catch Cups | METHOD | Аудит: catch cups uniformity coefficient >0.7. Adjust or replace nozzles data driven. | Guess adjustment — still brown patches. |
| irrigation.ops.spring_startup_sequence | Spring — Startup Sequence | PROCESS | Весна: main slow open, leak walk, program check, heads clean, backflow test schedule. | Full blast first — water hammer pop fitting. |
| irrigation.ops.dog_chewed_wire | Dog — Chewed Wire | METHOD | Собака: conduit burial wire, splice waterproof DBR. Pet deterrent spray. | Bare splice dirt — zone intermittent. |
| irrigation.ops.licensed_backflow_only | Backflow — Licensed Only | PRACTICAL | Тест backflow: license required, не general irrigator some states. | Illegal test — utility rejects tag. |
| irrigation.ops.night_water_wind | Wind — Night Water | PRACTICAL | Ветер >15 km/h — drift waste. Night water less evaporation wind often calm. | Midday July spray — 40% evaporation loss. |
| irrigation.ops.root_water_ring | Tree — Water Ring | METHOD | Дерево: separate deep watering emitter ring, не lawn spray on trunk. Root zone outward. | Trunk spray — rot bark disease. |
| irrigation.ops.pricing_material_markup | Materials — Markup | PRACTICAL | Наценка parts 20-30%, trip fee, zone minimum. Emergency same day premium. | Time and material no trip — lose on drive. |
| irrigation.ops.warranty_labor_heads | Warranty — Labor Heads | PRACTICAL | Гарантия: new head 1 год, wire locate not if customer dig. Clear terms. | Customer trench — cut wire, expect free fix. |
| irrigation.ops.greywater_irrigation_code | Greywater — Code | VARIANT | Серые воды: permit, subsurface only, no spray edible. Separate system purple pipe. | Laundry to spray tomatoes — health dept stop. |
| irrigation.ops.pivot_irrigation_ag | Pivot — Ag Scale | VARIANT | Центр-пивот: commercial ag, not residential service. Know referral. | Accept pivot repair residential truck — wrong tools. |
| irrigation.ops.clogged_portable_filter | Portable Filter — Flush | METHOD | Промывка screen at valve monthly high sediment wells. Auto self-clean option sandy soil. | Sediment in valve — diaphragm tear. |
| irrigation.ops.manual_drain_valve_low | Manual Drain — Low Point | METHOD | Drain valves at low points freeze zone supplemental to blow out. | Blow out only — water pocket freeze crack. |
| irrigation.ops.customer_controller_training | Training — Controller 15 Min | PRACTICAL | Обучение: run manual zone, adjust schedule, rain delay. Sticker quick guide. | No training — «system broken» user error calls. |
| irrigation.ops.zone_valve_flow_control | Zone Valve — Flow Control | METHOD | Регулятор расхода на клапане: открыть на 2-3 оборота от полного закрытия для баланса зоны. Полностью открыт — водный молот. | Закрытый flow control — сухая зона при «рабочем» клапане. |
| irrigation.ops.sprinkler_head_clean_filter | Head — Clean Filter | METHOD | Спринклер: снять фильтр внутри, промыть, проверить сопло на камни. Заменить cracked nozzle. | Забитый фильтр — donut сухой круг на газоне. |
