# BATCH 648: Ambulance — Vehicle Preparation & Operations

**KnowledgeUnits:** 44
**Namespace:** `ambulance.ops.*`
**Scope:** vehicle_check, restocking, stretcher, oxygen, suction, defibrillator, cleaning, driving

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| ambulance.ops.vehicle_daily_check | Vehicle Check — Daily Inspection | METHOD | Ежедневная проверка скорой. Engine: масло, ОЖ, топливо, шины, свет, сирена. Patient compartment: чистота (disinfected), oxygen (main tank + portable — давление >1000 psi), suction unit (работает, canister пуст), defibrillator (self-test, pads срок годности, батарея >50%), монитор (ECG, SpO2, NIBP — калибровка), stretcher (фиксация, ремни), stair chair, backboard, cervical collars, jump bag (airway, trauma, OB kit), medications (контроль срока годности), narcotics count. Оборудование закреплено (не летает при ДТП). Инфекционный контроль: красный мешок (biohazard), острые предметы контейнер. | Без проверки в начале смены: на вызове не работает suction (пациент захлёбывается). |
| ambulance.ops.loading_stretcher_lift | Stretcher — Powered Lift Operation | METHOD | Погрузка пациента на носилках (Stryker Power-PRO, Ferno). Оценка веса: если >150 кг — bariatric stretcher или дополнительный персонал. Safety: ремни (3-5 point — грудь, таз, колени). Подъём: гидравлика (power lift), не ручной (травма спины). Подкат к машине: loading wheel, auto load system (рельсы). Фиксация в ambulance: anti-roll lock. Разгрузка: обратный процесс. Контроль: проверить защёлки. | Ручной подъём пациента — причина №1 травм спины у EMT. |
| ambulance.ops.decontamination_transport | Decon — Vehicle After Contaminated Patient | METHOD | Дезинфекция скорой после инфекционного пациента. PPE: gown, gloves, N95/PAPR, face shield. Уборка: сначала сухая (удаление органических загрязнений), затем дезинфекция (bleach 1:10 или hydrogen peroxide wipes). Все поверхности: stretcher, поручни, монитор, стены, пол. Contact time: 10 мин. Туман (fogger): hydrogen peroxide mist для полной дезинфекции (30-60 мин). Ozone generator (альтернатива). После: проветривание. Terminal clean (после особо опасных инфекций — Ebola, MERS, CJD): специальный протокол. | COVID: N95 mask + face shield минимально. |
| ambulance.ops.ambulance_driving_evasive | Экстренное вождение — безопасность | METHOD | Вождение с сиреной (Code 3). Emergency driving: lights + siren. Intersection: остановиться на red — проверить, проехать. Speed: +15-25 км/ч выше потока. Безопасность: пристёгнуты? Крепление оборудования — при ДТП летает. |
| ambulance.ops.ambulance_lift_wheelchair | Подъёмник для коляски | METHOD | Wheelchair lift: for bariatric patients, folding ramp. |
| ambulance.ops.ambulance_loading_dock | Погрузочная площадка | METHOD | Loading dock: уклон, освещение, защита от дождя. |
| ambulance.ops.ambulance_types_type2 | Типы скорой — Type I, II, III | PRACTICAL | Type I: truck chassis + box (4x4). Type II: van (Mercedes Sprinter — маневренность). Type III: van cutaway + box (наиболее распространён). |
| ambulance.ops.amiodarone_cardiac | Амиодарон — сердечный ритм | METHOD | Амиодарон: 300 mg IV (первая доза), 150 mg (вторая). |
| ambulance.ops.biophone_hospital_notification | Радиопередача в больницу | METHOD | Biophone: передача данных ЭКГ в больницу. Cellphone: предупреждение приёмного отделения. |
| ambulance.ops.blood_glucose_meter | Глюкометр | METHOD | Глюкометр: check strip expiry, calibrate, finger stick. |
| ambulance.ops.carbon_monoxide_detector | Датчик CO | METHOD | CO detector: в салоне (выхлоп проникает). Порог: 10 ppm alarm. |
| ambulance.ops.cervical_spine_immobilization | Иммобилизация шейного отдела | METHOD | Шейный воротник (c-collar). Размеры: от chin to chest (измерить). Установка: осторожно, не сгибать шею. Rigid c-collar. Backboard (жёсткие носилки): фиксация головы, таза, коленей. |
| ambulance.ops.cot_securement_safety | Крепление носилок | METHOD | Крепление носилок в машине. Lock: anti-roll (3-point). Load bars: auto-load system. Проверка: дёрнуть за ручку. |
| ambulance.ops.cpap_ventilator | CPAP — неинвазивная вентиляция | METHOD | CPAP (BiPAP): для отёка лёгких, ХОБЛ. Давление: 5-15 cm H2O. |
| ambulance.ops.ct_scan_ambulance | Скорая с КТ | PRACTICAL | Mobile Stroke Unit: скорая с CT scanner (для диагностики инсульта на месте). |
| ambulance.ops.defibrillator_check | Дефибриллятор — ежедневная проверка | METHOD | Дефибриллятор (Lifepak 15, Zoll X Series, Philips HeartStart). Self-test: проходят при включении (Automatic self-test — AST). Батарея: >50% (Li-ion, заменять каждые 2-3 года). Pads: срок годности (не просрочены — высыхают). ECG cable: не перетёрт. |
| ambulance.ops.ems_injury_log_osha | Травмы на работе — OSHA | METHOD | Needlestick: report immediately, post-exposure prophylaxis (PEP — HIV, Hep B). |
| ambulance.ops.ems_shift_change_over | Смена — передача | METHOD | Handover: equipment check, restock, vehicle clean. Log: incidents, maintenance. |
| ambulance.ops.fentanyl_dosing_safety | Фентанил — дозировка | METHOD | Фентанил: 50-100 mcg IV/IM. Не >3 доз без врача. |
| ambulance.ops.fire_extinguisher_dash | Огнетушитель | METHOD | Огнетушитель ABC (5-10 lb). Проверка: monthly. |
| ambulance.ops.fluid_resuscitation_crystalloid | Жидкостная реанимация | METHOD | Кристаллоиды (LR, NS). Болюс: 500-1000 мл. Для травмы: 1-2 литра (остановить кровотечение). |
| ambulance.ops.hazmat_ambulance_decon | Декон химии | METHOD | Дезактивация: пациент + скорая. PPE Level A. |
| ambulance.ops.iv_catheter_insertion | Катетер — внутривенный доступ | METHOD | IV: 14-24 gauge. 18-20 g — стандарт (травма). 14-16 g — массивная кровопотеря. |
| ambulance.ops.king_lt_combitube | King LT — воздуховод | METHOD | King LT (надгортанный воздуховод). Размер: 3 (средний), 4 (высокий), 5 (очень высокий). |
| ambulance.ops.laryngoscope_blade | Ларингоскоп — клинок | METHOD | Ларингоскоп: Miller (прямой) или Macintosh (изогнутый). Размеры: 1 (ребёнок) — 4 (взрослый). |
| ambulance.ops.mast_trousers_pneumatic | Противошоковые брюки | METHOD | MAST (PASG): pneumatic antishock. Сегодня редко (доказательства сомнительны). |
| ambulance.ops.medication_expiration_check | Проверка срока годности лекарств | METHOD | Каждый месяц: все medications, pads, gloves, IV fluids. Просроченные: замена. |
| ambulance.ops.morgue_transport | Транспорт умершего | METHOD | Транспорт тела (morgue pouch, zippered bag). Без контроля? |
| ambulance.ops.narcotics_count_protocol | Учёт наркотиков | METHOD | Наркотики (морфин, фентанил, мидазолам). Два свидетеля при счёте. Замок (Pediatric lock). Log: кол-во, пациент, остаток. |
| ambulance.ops.nasopharyngeal_airway | Носовой воздуховод | METHOD | NPA (nasopharyngeal airway). Размер: 24-34 Fr (adult). Смазка (lidocaine). |
| ambulance.ops.ob_kit_midwife | Акушерский набор | METHOD | OB kit: cord clamp, scissors, bulb syringe, towel, gloves, placenta bag. |
| ambulance.ops.oxygen_system_management | Кислород — баллоны и регуляторы | METHOD | Кислородная система. Баллоны: M-size (main, 3000 L при 1900 psi), D-size (portable, 350 L). Регулятор: 0-25 L/min. Разные цвета: зелёный (O2), жёлтый (air). Запас: проверять давление при начале смены (M >1000 psi). Nasal cannula: 1-6 L/min (FiO2 24-44%). Non-rebreather mask: 10-15 L/min (FiO2 60-90%). Часы: не превышать — риск кислородного отравления. |
| ambulance.ops.pelvic_immobilization_binder | Таз — связка | METHOD | Pelvic binder: закрытая травма таза (кровотечение). Наложение на уровне trochanters. |
| ambulance.ops.radio_communication_10_codes | Радио — 10-коды | METHOD | 10-коды: 10-8 (в службе/доступен), 10-7 (недоступен), 10-23 (на месте), 10-97 (прибыл на сцену), 10-98 (завершён). |
| ambulance.ops.reflective_vest_night | Светоотражающий жилет | METHOD | ANSI Class 2 или 3 (ночь). Надевать при работе на трассе. |
| ambulance.ops.refueling_procedure | Заправка — процедура | METHOD | Заправка скорой: дизель (или бензин). Не заправлять с пациентом! Оборудование: генератор, кондиционер — выключить. |
| ambulance.ops.saline_locks_hep_lock | Гепариновый замок | METHOD | Saline lock: IV катетер без жидкости (Hep-lock). |
| ambulance.ops.squad_bench_pediatric | Скамья/кресло для ребёнка | METHOD | Детское кресло в скорой. Крепление ремней. Ребёнок на руках — запрещено (crash). |
| ambulance.ops.stair_chair_carry | Кресло-лестница — спуск | METHOD | Stair chair. Вес: до 200 кг. Спуск: два человека (один сверху, один снизу). Track system (гусеницы — Stryker Stair-PRO): один человек спускает по ступенькам. |
| ambulance.ops.suction_unit_check | Отсасыватель — проверка | METHOD | Аспиратор (suction unit). Типы: battery (Laerdal LSU), pneumatic. Проверка: включить, закрыть трубку рукой (должен создать вакуум >300 мм Hg за 5 сек). Canister: пустой, чистый. Трубка: не забита. |
| ambulance.ops.tire_pressure_check | Давление в шинах — проверка | METHOD | Шины: давление по мануалу, проверка протектора. Для скорой — heavy-duty шины (Load Range E). |
| ambulance.ops.traction_splint_long_bone | Шина — вытяжение бедра | METHOD | Traction splint (Thomas, Sager): перелом бедра. Манжета на лодыжку, натяжение. |
| ambulance.ops.warmer_infant_incubator | Инкубатор для новорождённых | METHOD | Транспортировка новорождённых: incubator (терморегуляция, O2, монитор). Питание: батарея. |
| ambulance.ops.winter_driving_safety | Зимнее вождение | METHOD | Зимние шины, цепи противоскольжения. Антифриз, обогрев. |
