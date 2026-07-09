# BATCH 880: Sump Pump Install

**KnowledgeUnits:** 50
**Namespace:** `sumppump.ops.*`
**Scope:** basin, float, discharge, backup, check valve, GFCI

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| sumppump.ops.basin_size_18_inch | Basin Size — 18 Inch Min | METHOD | Колодец: 18" диаметр min для dual float, глубина ниже inlet tile 6". Perforated basin в gravel bed. Solid lid sealed. | 14" basin — pump cycles every minute, burn out за год. |
| sumppump.ops.check_valve_orientation | Check Valve — Orientation | METHOD | Обратный клапан: стрелка от насоса, 3 ft above pump. Vertical install. Silent check valve reduces hammer. | Reverse valve — вода обратно в basin, double run. |
| sumppump.ops.discharge_freeze_gutter | Discharge — Freeze Protection | METHOD | Вывод: 10 ft от foundation, не в septic. Freeze guard или grade drain below frost. Ice check winter. | Discharge у foundation — recycle water в basement. |
| sumppump.ops.float_switch_adjust | Float Switch — Adjust | METHOD | Поплавок: on 6" below rim, off 2" above pump intake. Tether clear. Test pour water bucket. | Too high float — overflow rim перед start. |
| sumppump.ops.backup_battery_ups | Backup — Battery UPS | VARIANT | Аварийный: battery backup pump или UPS inverter для primary. Separate discharge или Y fitting. Test monthly. | Power out в storm — flooded basement без backup. |
| sumppump.ops.pedestal_vs_submersible | Pedestal vs Submersible | VARIANT | Погружной: тише, basin covered. Pedestal: service in dry, дешевле. Submersible standard residential. | Pedestal open basin — humidity и odor в basement. |
| sumppump.ops.gfci_dedicated_circuit | GFCI — Dedicated Circuit | METHOD | Электрика: dedicated 15-20A, GFCI protection, не extension cord. Disconnect above basin. | Extension cord в water — electrocution risk. |
| sumppump.ops.weep_hole_drilled | Weep Hole — Drilled | METHOD | Weep hole в discharge 1/4" below check valve — drain chamber, prevent air lock. Some pumps pre-drilled. | No weep — air lock, pump runs dry humming. |
| sumppump.ops.radon_sealed_lid | Radon — Sealed Lid | METHOD | Радон: airtight lid, vent pipe to exterior, gasket bolts. Permeation через sump pit common. | Open sump — radon highway в basement. |
| sumppump.ops.tile_inlet_bedding | Tile Inlet — Bedding | METHOD | Drain tile inlet: hole saw basin, gasket, below water line. Gravel surround exterior weeping tile. | Gap around inlet — sediment fills basin. |
| sumppump.ops.pump_sizing_gpm_head | Pump Sizing — GPM Head | METHOD | Размер: 35-60 GPM residential, head height to discharge + friction. Chart manufacturer. Undersize — can't keep up. | 1/4 HP на 2000 sq ft wet yard — constant flood. |
| sumppump.ops.alarm_high_water | Alarm — High Water | METHOD | Сигнал: второй float выше primary, audible + WiFi optional. Test quarterly. Battery backup alarm. | No alarm — flood discovered когда carpet wet upstairs. |
| sumppump.ops.basin_clean_sediment | Basin Clean — Sediment | METHOD | Обслуживание: annual pull pump, vacuum sediment, inspect impeller. Mud kills float. | 5 years sediment — float stuck on, overflow. |
| sumppump.ops.dual_pump_primary_backup | Dual Pump — Primary Backup | VARIANT | Два насоса: primary + higher float backup. Commercial and high-value basement. Alternating cycle option. | Single pump failure 2 AM — $50k finished basement loss. |
| sumppump.ops.discharge_check_local_code | Discharge — Local Code | PRACTICAL | Код: куда можно сбрасывать — storm, daylight, не street illegal. Permit inspect. | Illegal street discharge — fine и forced reroute. |
| sumppump.ops.vent_hole_basin | Vent Hole — Basin | METHOD | Вентиляция pit: 1" vent to exterior если sealed lid radon. Balance air for pump cycle. | Sealed no vent — vacuum collapse cheap basin. |
| sumppump.ops.impeller_replace_clog | Impeller — Replace Clog | METHOD | Засор: pull pump, clear impeller, check screen. Cloth и debris common. Reset thermal if tripped. | Run clogged — motor burn $400 new pump. |
| sumppump.ops.freeze_discharge_heat | Freeze — Heat Cable | METHOD | Heat cable on discharge pipe exposed section. Insulate wrap. GFCI protected. | Frozen discharge — pump runs continuously deadhead. |
| sumppump.ops.sump_pit_odor_trap | Odor — Trap Water | METHOD | Запах: dried trap in floor drain nearby, not sump if sealed. Water seal in unused pit. | Open pit summer — sewer gas basement. |
| sumppump.ops.install_permit_electrical | Permit — Electrical | PRACTICAL | Permit: new circuit often requires electrician license. DIY illegal some jurisdictions. | Unpermitted work — home sale blocker. |
| sumppump.ops.gravel_base_basin | Gravel Base — Basin | METHOD | Основание: 6" pea gravel level, basin twist slightly settle. Prevents tilt float stick. | Tilted basin — float hangs on wall. |
| sumppump.ops.high_water_table_basin | High Water Table — Basin | METHOD | Высокий ГВУ: basin may fill groundwater — differentiate from tile water. Seal exterior if needed. | Misdiagnose groundwater — wrong drainage solution $10k. |
| sumppump.ops.wifi_monitoring_iot | WiFi — IoT Monitoring | VARIANT | Smart plug + water sensor: alert phone on run time anomaly. Flood sensor beside basin. | Vacation flood — no IoT, insurance deductible $10k. |
| sumppump.ops.pedestal_motor_oil | Pedestal — Motor Oil | METHOD | Pedestal pump: oil level check annual, sleeve bearing. Submersible oil-filled — replace if leak. | Dry pedestal bearing — seize mid-storm. |
| sumppump.ops.discharge_pipe_pvc_cement | PVC — Cement Joint | METHOD | Труба: schedule 40, primer + cement, support straps. No sharp 90° — two 45°. | Sharp 90 — friction loss и check valve slam. |
| sumppump.ops.liberty_little_giant_sizing | Brand — Sizing Chart | PRACTICAL | Производители: Zoeller, Liberty charts по basin diameter и head. Stock common models on truck. | Wrong model overnight — basement floods waiting part. |
| sumppump.ops.ejector_sewage_separate | Ejector — Sewage Separate | VARIANT | Санитарный ejector: sealed basin, grinder pump, не mix storm sump. Vent stack required. | Sewage в storm sump — health violation. |
| sumppump.ops.backup_generator_tie | Generator — Tie In | METHOD | Генератор: transfer switch для sump circuit priority. Storm season test monthly. | Generator no sump circuit — useless during flood. |
| sumppump.ops.insurance_sump_rider | Insurance — Sump Rider | PRACTICAL | Страховка: sewer backup rider separate, document maintenance. Photos install date. | No rider — denied claim после loss. |
| sumppump.ops.basin_cover_child_safe | Child Safe — Cover | METHOD | Крышка: bolt down, load rated if traffic area. Child drowning rare но liability. | Loose cover — kid falls in pit. |
| sumppump.ops.install_quiet_check_valve | Quiet — Check Valve | VARIANT | Тихий клапан: spring soft close, reduce water hammer noise bedroom above. | Standard valve bang — 3 AM complaints. |
| sumppump.ops.sump_test_rain_event | Test — Rain Event | METHOD | Тест: hose perimeter foundation или wait rain, observe cycles. Adjust float after real load. | Bucket test only — misadjusted в real storm. |
| sumppump.ops.foundation_crack_water | Foundation Crack — Source | METHOD | Вода в pit не только tile — wall cracks contribute. Refer waterproofing если constant high water. | New pump на leaking walls — still wet basement. |
| sumppump.ops.pricing_pump_tiers | Pricing — Pump Tiers | PRACTICAL | Смета: pump tier, basin new vs existing, discharge length, backup option, electrical. | Quote pump only — 4 hours electrical extra unpaid. |
| sumppump.ops.warranty_labor_pump | Warranty — Labor Pump | PRACTICAL | Гарантия: pump 3-5 лет manufacturer, labor 1 год. Defect vs install error. | Install error blamed manufacturer — dispute. |
| sumppump.ops.mineral_oil_submersible | Mineral Oil — Submersible | PRACTICAL | Утечка oil submersible — replace, не repair. Environmental dispose. | Oil in basin — pump failure imminent. |
| sumppump.ops.check_valve_freeze_location | Check Valve — Freeze Location | METHOD | Клапан в heated space если possible — frozen valve blocks discharge winter. | Valve in attic crawl — ice jam flood. |
| sumppump.ops.sump_basin_liner | Basin Liner — Optional | VARIANT | Лайнер: preformed polyethylene basin vs brick old retrofit. Lid adapter kit. | Brick pit no lid — debris и frogs. |
| sumppump.ops.discharge_pop_up_emitter | Pop-Up Emitter — Yard | VARIANT | Pop-up: lawn level discharge, closes when dry. Clean grass debris spring. | Buried pop-up clogged — water backs to sump. |
| sumppump.ops.maintenance_contract_annual | Maintenance — Annual Contract | PRACTICAL | Контракт: annual clean, test, report для insurance. Recurring revenue. | One install no service — pump dead 5 years, blame installer. |
| sumppump.ops.laundry_sink_pump | Laundry Sink — Utility Pump | VARIANT | Малый насос: laundry sink drain когда below sewer. Not same as foundation sump. | Wrong pump type — soap clog daily. |
| sumppump.ops.iron_ochre_clog | Iron Ochre — Clog | METHOD | Железобактерия: orange slime clogs pump yearly. Special treatment или different basin design. | Standard pump iron water — float slime stuck monthly. |
| sumppump.ops.customer_battery_test | Customer — Battery Test Remind | PRACTICAL | Инструкция: test backup monthly, replace battery 3-5 лет. Sticker on lid. | Dead backup battery — false security flood. |
| sumppump.ops.sump_install_timeline | Timeline — Same Day | PROCESS | Установка: 4-8 ч typical, concrete break if needed extra day. Dry basement before finish trim. | Promise 2 hours — incomplete electrical, angry client. |
| sumppump.ops.pit_radon_fan_combo | Radon Fan — Combo System | VARIANT | Комбо: sealed sump + radon fan pipe dual use routing. Radon mitigator coordinate. | Two holes lid — leak radon at gaskets. |
| sumppump.ops.overflow_secondary_drain | Overflow — Secondary | METHOD | Overflow drain to daylight если rim exceeded — rare backup path. Alarm still primary. | No overflow — rim spill finished carpet. |
| sumppump.ops.zoeller_m53_standard | Standard — M53 Class | PRACTICAL | Zoeller M53 industry standard residential — stock on truck, customer recognize name. | No-name pump — warranty fight и callback. |
| sumppump.ops.discharge_freeze_protection | Discharge — Freeze Guard | METHOD | Защита от замерзания: утеплённый участок трубы у выхода, обогрев кабель на открытом участке. Наклон от насоса к выходу. | Замёрзший выход — насос работает вхолостую и перегрев. |
| sumppump.ops.basin_perforation_gravel | Basin — Perforation Gravel | METHOD | Перфорированная установка: гравийная подушка 15 см, отверстия в колодце для дренажа плиточных линий. Геотекстиль против ила. | Колодец в глине без гравия — плавает и не принимает воду. |
| sumppump.ops.high_water_alarm_test | High Water — Alarm Test | METHOD | Тест сигнализации: поднять поплавок вручную, проверить сирену и WiFi-уведомление. Ежеквартально для клиента. | Мёртвая сигнализация — затопление без предупреждения. |
