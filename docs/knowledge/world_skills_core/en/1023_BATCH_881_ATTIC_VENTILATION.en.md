# BATCH 881: Attic Ventilation

**KnowledgeUnits:** 50
**Namespace:** `atticvent.ops.*`
**Scope:** soffit, ridge, baffle, insulation, ice dam, fan

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| atticvent.ops.soffit_intake_balance | Soffit Intake — Balance Ratio | METHOD | Баланс вентиляции: intake soffit = exhaust CFM min 50%. 1 sq ft NFA на 150 sq ft attic IRC. Не блокировать soffit insulation baffle. | Blocked soffit — exhaust тянет из conditioned space, $$$ HVAC. |
| atticvent.ops.ridge_vent_continuous | Ridge Vent — Continuous | METHOD | Конёк: continuous ridge vent 1" slot both sides, cap over. Cut 3" from peak each side. No dead spots between rafters. | End-only roof vents — hot pocket middle attic 150°F. |
| atticvent.ops.baffle_maintain_airgap | Baffle — Maintain Air Gap | METHOD | Wind baffle 2" air channel над insulation до soffit. Cardboard or foam. Insulation не заходит в soffit. | Insulation в soffit — zero intake, ridge useless. |
| atticvent.ops.power_fan_thermostat | Power Fan — Thermostat | METHOD | Мощный вентилятор: 105-110°F on, humidistat combo humid climate. 1500+ CFM. Needs adequate intake. | Power vent no soffit — pulls AC air through ceiling. |
| atticvent.ops.static_vent_count_formula | Static Vent — Count Formula | METHOD | Box vents: NFA rating суммировать до 1/150 rule. Равномерно по roof. Не mix power и ridge без calc. | Two small boxes 2000 sq ft — insufficient, ice dams. |
| atticvent.ops.ice_dam_ventilation_link | Ice Dam — Ventilation Link | METHOD | Ледяные дамбы: cold roof через vent + air seal ceiling. Insulation R49+. Vent alone не fix air leak. | Only add vents — warm roof still melts snow. |
| atticvent.ops.mold_attic_humidity | Mold — Attic Humidity | METHOD | Плесень: bathroom fan vent INTO attic forbidden — duct outside. 60% RH max winter. Black on sheathing — source fix first. | Bath vent in attic — mold и rot sheathing $15k. |
| atticvent.ops.radiant_barrier_debate | Radiant Barrier — Application | VARIANT | Радиобарьер: staple under rafters или on sheathing. 10-20°F reduction peak. Dust reduces effect over years. | Promise 40% bill cut — unrealistic, angry customer. |
| atticvent.ops.cathedral_ceiling_vent | Cathedral — Vent Channel | METHOD | Скатный потолок: baffle каждый bay rafter 1" min, ridge vent mandatory. Dense pack cellulose risky без channel. | No channel cathedral — sheathing rot invisible 5 years. |
| atticvent.ops.solar_fan_wind_turbine | Solar Fan — vs Turbine | VARIANT | Солнечный вентилятор: no wiring, stops at night when still hot. Turbine wind dependent. Ridge preferred modern. | Solar fan dead battery — zero exhaust August. |
| atticvent.ops.knee_wall_venting | Knee Wall — Venting | METHOD | Короткие стены: vented knee wall behind, insulation between studs, air from soffit below. | Insulated knee no vent — oven behind upstairs room. |
| atticvent.ops.gable_fan_one_side | Gable Fan — One Side | VARIANT | Фронтонный вентилятор: one-way exhaust, other gable intake screen. Less ideal than soffit-ridge path. | Both gables exhaust — negative pressure attic. |
| atticvent.ops.insulation_depth_mark | Insulation — Depth Mark | METHOD | R-value: measure depth, uniform. Marker stakes depth target. Don't cover can lights non-IC. | IC can buried — fire и house burn. |
| atticvent.ops.air_seal_before_insulate | Air Seal — Before Insulate | METHOD | Порядок: foam seal penetrations, then insulate, then vent path clear. Top plate gaps foam. | Insulate first — can't reach leaks under blown. |
| atticvent.ops.hip_roof_venting | Hip Roof — Venting | METHOD | Вальмовая: ridge shorter — supplement static vents lower roof. Calc total NFA. | Hip large no ridge — stagnant corners mold. |
| atticvent.ops.pest_screen_vent | Pest Screen — Vent | METHOD | Сетка на exhaust: 1/4" hardware cloth, не block NFA >50%. Wasps in ridge cap common. | No screen — hornets nest in attic vent. |
| atticvent.ops.walk_boards_attic | Walk Boards — Attic | METHOD | Доски на joists для service — не step on drywall. Mark path to HVAC. Safety и less damage. | Fall through ceiling — injury и drywall $800. |
| atticvent.ops.spray_foam_vented_conflict | Spray Foam — Vented Conflict | VARIANT | Closed cell foam roof deck — unvented assembly engineered. Не mix with soffit vents. | Foam + open soffit — moisture trap sheathing. |
| atticvent.ops.whirlybird_noise | Whirlybird — Noise | PRACTICAL | Турбина: bearing squeak age. Grease или replace. Customer complaint night wind. | Squeaky turbine — 2 AM call, remove request. |
| atticvent.ops.attic_access_seal | Attic Access — Seal | METHOD | Люк: insulated cover box, weatherstrip, latch. Major air leak if unsealed. | Unsealed hatch — all vent work wasted on stack effect. |
| atticvent.ops.frost_attic_sheathing | Frost — Sheathing Winter | METHOD | Иней нанутри sheathing: warm moist air leak. Infrared scan ceiling. Not «need more vent» only. | More vents on leaky ceiling — bigger heating bill. |
| atticvent.ops.combination_vent_calc | Combination — Vent Calc | METHOD | Mixed systems: sum NFA all exhaust, verify intake. Power vent counts high CFM — enlarge soffit. | Ridge + power both on — over negative, pull conditioned air. |
| atticvent.ops.overhang_soffit_vinyl | Vinyl Soffit — Perforated | METHOD | Винил soffit: perforated panels, not solid. J-channel clear. Paint aluminum ok if vents existing. | Solid vinyl soffit — beautiful attic rot. |
| atticvent.ops.roof_deck_nail_pattern | Roof Deck — Nail Pattern | METHOD | При re-roof: don't block planned ridge slot. Coordinate roofer and vent installer. | New shingles over planned ridge — recut $$$. |
| atticvent.ops.attic_temp_monitor | Temp Monitor — Data | METHOD | Logger: attic vs outdoor delta <30°F ideal sunny day. Proof vent improvement. | No data — customer doubts work helped. |
| atticvent.ops.fire_blocking_rafter | Fire Blocking — Rafter Bay | METHOD | Fire stop at soffit line some codes. Don't block vent channel — use listed baffle fire rated. | Drywall fire block — blocked soffit airflow. |
| atticvent.ops.hvac_in_attic_insulate | HVAC in Attic — Duct Insulate | METHOD | Кондиционер на чердаке: R-8 duct min, second zone heat extreme attic. Vent helps equipment life. | R-4 duct 140°F attic — cold air delivery. |
| atticvent.ops.pricing_per_sqft_attic | Pricing — Per Sq Ft | PRACTICAL | Смета: baffles per bay, ridge lf, fan unit. Steep roof surcharge. Insulation separate trade clarify. | Ridge only quote — soffit blocked, failure. |
| atticvent.ops.osb_wet_replace | Wet OSB — Replace | METHOD | Разбухший OSB: mold source, replace section, fix vent AND leak. Cosmetic mold spray insufficient. | Bleach wet OSB — structural failure continues. |
| atticvent.ops.turbine_count_wind | Turbine Count — Wind Zone | METHOD | Турбины: high wind area — secure extra screws. Hurricane strap vents coastal. | Turbine blown off — hole in roof rain. |
| atticvent.ops.static_vent_color_match | Static Vent — Color Match | PRACTICAL | Цвет вентиля: match shingle, customer aesthetic. Powder coat option. | Silver vent on black roof — HOA fine. |
| atticvent.ops.attic_moisture_source_hvac | HVAC Leak — Moisture Source | METHOD | Конденсат drain pan overflow — attic moisture misdiagnosed as vent. Inspect coil pan. | New vents on HVAC leak — mold continues. |
| atticvent.ops.ridge_vent_shingle_over | Ridge Cap — Shingle Over | METHOD | Установка: ridge cap shingles over vent, nail pattern manufacturer. No exposed nail heads. | Exposed nails ridge — leak in 2 years. |
| atticvent.ops.winter_cover_fan_wrong | Winter Cover Fan — Wrong | PRACTICAL | Не cover power vent winter — moisture buildup. Fans designed year round. | Covered vent winter — mold spring surprise. |
| atticvent.ops.blown_insulation_settle | Blown Insulation — Settle | METHOD | Cellulose settle 20% — top up year one. Depth markers. Vent baffles before blow. | Settled insulation — bare spots at eave cold. |
| atticvent.ops.truss_bracing_vent | Truss — Bracing Vent | METHOD | Не remove truss bracing for vent. Engineer if conflict. Alternate vent location. | Cut brace — roof sag и code violation. |
| atticvent.ops.solar_attic_fan_wiring | Solar Attic Fan — Wiring | VARIANT | Hybrid solar+electric: runs night. Wiring permit. Better than solar only hot nights. | Solar only — attic still 120°F sunset. |
| atticvent.ops.pest_entry_fascia | Fascia Gap — Pest Entry | METHOD | Зазор fascia-soffit: seal metal, squirrels common. Vent function after seal. | Squirrels in attic — chewed wires fire. |
| atticvent.ops.condensation_metal_roof | Metal Roof — Condensation | METHOD | Металл: vented channel below or spray foam unvented design. Dripping underside winter. | Unvented metal — rain inside attic frost melt. |
| atticvent.ops.customer_education_balance | Education — Balance Concept | PRACTICAL | Объяснить: chimney needs air in and out. Diagram soffit-ridge. Why baffles matter. | Customer blocks soffit after — your fault perception. |
| atticvent.ops.inspection_photo_before | Photo — Before After | PROCESS | Фото: sheathing mold before, baffle install, NFA calc sheet. Liability and marketing. | Dispute mold pre-existing — no photos lose. |
| atticvent.ops.multi_attic_separate | Multi Attic — Separate | METHOD | Несколько чердаков: каждый isolated vent path. Don't assume connected. | Vent one section — other still 160°F. |
| atticvent.ops.low_slope_vent_challenge | Low Slope — Vent Challenge | METHOD | Малый уклон <3:12: limited ridge — use low profile vents, code exception consult. | Standard ridge low slope — leak wind driven rain. |
| atticvent.ops.asbestos_vermiculite_check | Vermiculite — Asbestos Check | PRACTICAL | Vermiculite insulation: test asbestos before disturb. EPA protocol if positive. | Disturb asbestos — federal violation $25k. |
| atticvent.ops.warranty_vent_install | Warranty — Install Leak | PRACTICAL | Гарантия: leak-free install 5 лет, not mold if bath vent wrong. Document exclusions. | Mold warranty claim — bath vent not your work. |
| atticvent.ops.off_ridge_vent_use | Off Ridge — Vent Use | VARIANT | Off-ridge vents: when ridge not possible hip. Place high, near ridge line. | Low roof vent — doesn't exhaust hot layer. |
| atticvent.ops.attic_stair_insulated_tent | Stair Tent — Insulated | VARIANT | Tent over pull stairs R-10+. Combo with vent project upsell. | Stair leak — 15% home heat loss. |
| atticvent.ops.ventilation_roi_energy | ROI — Energy Savings | PRACTICAL | Ожидания: 5-15% cooling savings realistic, ice dam prevention major. Honest numbers. | Promise half bill — BBB complaint. |
| atticvent.ops.soffit_vents_blocked_insulation | Soffit Blocked — Insulation | METHOD | Забитый соффит: убрать утеплитель из вентиляционного канала, установить дефлекторы. Без притока вытяжка не работает. | Утеплитель в соффите — отрицательное давление и плесень. |
| atticvent.ops.attic_mold_source_bath_fan | Mold Source — Bath Fan | METHOD | Плесень на обрешётке: проверить вывод вентилятора ванной — должен наружу, не в чердак. Герметизировать фланец. | Вентилятор в чердак — плесень несмотря на ridge vent. |
