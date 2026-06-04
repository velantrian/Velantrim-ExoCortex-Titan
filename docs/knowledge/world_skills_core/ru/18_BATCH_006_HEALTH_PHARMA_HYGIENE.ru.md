# 💊 Batch 006 — Health, Pharma, Hygiene & Care Safety

**Язык:** русский  
**Статус:** 50K batch 006 / seed units / не L3 truth  
**Цель:** добавить осторожный practical-слой по гигиене, фармацевтическому производству, лекарственной безопасности, медизделиям, лабораториям и care-процессам. Это не медицинская инструкция для самолечения.

---

## ⚠️ Safety note

Здоровье и лекарства — high-risk domain. Эти units должны храниться как осторожные knowledge records:

```text
не диагноз
не назначение лечения
не дозировка
не замена врача
```

Основной фокус: безопасность, производство, качество, общие процессы, ограничения.

---

## 📦 Knowledge Units

| ID | Тип | Суть | Условия / границы | Связи |
|---|---|---|---|---|
| `health.hygiene.handwashing` | METHOD | Мытьё рук снижает перенос загрязнений и микроорганизмов. | Эффективность зависит от техники, времени и ситуации. | public_health |
| `health.hygiene.soap_mechanism` | MECHANISM | Мыло помогает отделять жир и загрязнения от кожи через ПАВ. | Не равно стерилизации. | chemistry.surfactant |
| `health.hygiene.clean_disinfect_distinction` | DISTINCTION | Очистка удаляет грязь; дезинфекция снижает микробную нагрузку. | Дезинфекция хуже работает на грязной поверхности. | hygiene |
| `health.hygiene.sterilization_distinction` | DISTINCTION | Стерилизация направлена на уничтожение всех жизнеспособных микроорганизмов. | Требует валидированного процесса. | meddevice |
| `health.hygiene.ppe_gloves` | SAFETY_RULE | Перчатки защищают руки и снижают перенос загрязнений. | Неправильное снятие переносит загрязнение. | care |
| `health.water.boiling_pathogen_reduction` | METHOD | Кипячение снижает риск многих водных патогенов. | Не удаляет химические загрязнители. | water_safety |
| `health.water.filtration` | METHOD | Фильтрация удаляет частицы и некоторые загрязнители. | Эффект зависит от типа фильтра. | water |
| `health.water.chlorination` | METHOD | Хлорирование обеззараживает воду при правильной дозе и контакте. | Органика и мутность снижают эффективность. | sanitation |
| `health.food.allergen_cross_contact` | FAILURE_MODE | Перекрёстный контакт аллергенов делает продукт опасным для чувствительных людей. | Требует маркировки и санитарного разделения. | food_safety |
| `health.food.temperature_control` | SAFETY_RULE | Контроль температуры снижает рост микроорганизмов в пище. | Конкретные диапазоны зависят от продукта и норм. | cold_chain |
| `health.firstaid.bleeding_pressure` | METHOD | Прямое давление часто используется для остановки наружного кровотечения. | Тяжёлые случаи требуют экстренной помощи. | emergency |
| `health.firstaid.burn_cooling` | METHOD | Охлаждение ожога прохладной водой может снизить повреждение в ранний период. | Не использовать лёд; серьёзные ожоги требуют помощи. | emergency |
| `health.firstaid.choking_emergency` | EMERGENCY_RULE | Удушье от инородного тела требует быстрого распознавания и экстренного алгоритма. | Обучение и возраст пациента критичны. | emergency |
| `health.pharma.active_ingredient` | TERM | Active ingredient — вещество, обеспечивающее основной фармакологический эффект. | Эффект зависит от дозы, формы, пациента. | pharma |
| `health.pharma.excipient` | TERM | Вспомогательное вещество формирует таблетку/раствор и влияет на стабильность/доставку. | Не всегда биологически "нейтрально" для всех пациентов. | formulation |
| `health.pharma.dosage_form_tablet` | DOSAGE_FORM | Таблетка — твёрдая дозированная форма, часто получаемая прессованием. | Высвобождение зависит от состава и покрытия. | tablet |
| `health.pharma.capsule` | DOSAGE_FORM | Капсула содержит порошок, гранулы или жидкость в оболочке. | Оболочка и наполнение влияют на высвобождение. | pharma |
| `health.pharma.solution` | DOSAGE_FORM | Раствор содержит растворённое вещество в жидкой среде. | Стабильность и микробная чистота важны. | formulation |
| `health.pharma.suspension` | DOSAGE_FORM | Суспензия содержит твёрдые частицы в жидкости. | Требует равномерного распределения перед применением. | formulation |
| `health.pharma.ointment` | DOSAGE_FORM | Мазь — полутвёрдая форма для кожи/слизистых. | Основа влияет на проникновение и ощущение. | topical |
| `health.pharma.sterile_injection` | DOSAGE_FORM | Инъекционные формы требуют стерильности и контроля частиц. | High-risk manufacturing. | aseptic |
| `health.pharma.api_synthesis` | PROCESS | Синтез API создаёт активное вещество через химические/биотехнологические стадии. | Требует purity, impurity control, validation. | pharma_manufacturing |
| `health.pharma.extraction` | PROCESS | Некоторые вещества получают извлечением из природного сырья. | Состав сырья вариативен; нужна стандартизация. | medicinal_plants |
| `health.pharma.formulation` | PROCESS | Формуляция превращает API и excipients в стабильную дозированную форму. | Требует совместимости и контроля высвобождения. | pharma |
| `health.pharma.tablet_compression` | PROCESS | Прессование формирует таблетки из порошка/гранулята. | Важны flow, hardness, friability, weight uniformity. | manufacturing |
| `health.pharma.granulation` | PROCESS | Грануляция улучшает текучесть и сжимаемость порошков. | Бывает wet/dry; влажность критична. | tablet |
| `health.pharma.coating` | PROCESS | Покрытие таблеток защищает, маскирует вкус или управляет высвобождением. | Нужна равномерность и стабильность. | pharma |
| `health.pharma.aseptic_processing` | PROCESS | Aseptic processing предотвращает микробное загрязнение стерильного продукта. | Требует cleanroom, validated procedures, trained staff. | sterile |
| `health.pharma.cgmp_quality_system` | QUALITY_SYSTEM | CGMP требует системы контроля, предотвращающей загрязнения, mix-ups, deviations, failures. | Нормы зависят от юрисдикции. | FDA, quality |
| `health.pharma.batch_record` | QUALITY_RECORD | Batch record документирует производство конкретной партии. | Критично для traceability и расследований. | quality |
| `health.pharma.validation` | METHOD | Validation доказывает, что процесс стабильно даёт ожидаемый результат. | Нужны критерии и данные. | quality |
| `health.pharma.stability_testing` | QUALITY_CHECK | Stability testing оценивает сохранение качества во времени. | Условия хранения и упаковка важны. | shelf_life |
| `health.pharma.storage_conditions` | CONSTRAINT | Лекарства требуют определённых условий хранения. | Свет, температура, влажность могут разрушать продукт. | pharma |
| `health.pharma.cold_chain` | PROCESS | Холодовая цепь поддерживает температуру чувствительных препаратов. | Разрыв цепи может снизить качество. | logistics |
| `health.pharma.adverse_event_reporting` | PROCESS | Сообщения о нежелательных реакциях помогают мониторить безопасность лекарств. | Требует надёжной информации и анализа. | pharmacovigilance |
| `health.pharma.high_alert_medications` | SAFETY_RULE | High-alert medicines требуют особого внимания из-за риска серьёзного вреда при ошибке. | Нужны SOP, double checks, training. | medication_safety |
| `health.pharma.drug_interaction_risk` | RISK | Лекарственные взаимодействия могут изменить эффект или токсичность препаратов. | Требует профессиональной проверки. | medication_safety |
| `health.pharma.antibiotic_stewardship` | PRINCIPLE | Рациональное использование антибиотиков снижает риск устойчивости. | Не заменяет клиническое решение. | public_health |
| `health.meddevice.sterilization` | PROCESS | Медизделия могут требовать стерилизации паром, газом, радиацией или другими методами. | Метод зависит от материала и конструкции. | meddevice |
| `health.meddevice.biocompatibility` | QUALITY_CHECK | Биосовместимость оценивает безопасность контакта материала с телом. | Зависит от типа и длительности контакта. | materials |
| `health.meddevice.single_use` | SAFETY_RULE | Одноразовые медизделия рассчитаны на один цикл использования. | Повторное использование может быть опасно. | infection_control |
| `health.lab.sample_labeling` | SAFETY_RULE | Неправильная маркировка образца может привести к неверным решениям. | Требуются ID, время, источник, цепочка custody. | lab |
| `health.lab.contamination_control` | METHOD | Контроль загрязнения защищает образцы, персонал и результат анализа. | Нужны процедуры и среда. | lab |
| `health.lab.calibration` | QUALITY_CHECK | Лабораторное оборудование калибруют для доверия к измерениям. | Дрейф приборов требует периодичности. | measurement |
| `health.hospital.triage` | METHOD | Triage сортирует пациентов по срочности помощи. | Правила зависят от системы и ситуации. | emergency |
| `health.hospital.infection_control` | SYSTEM | Infection control снижает передачу инфекций в медучреждениях. | Требует hand hygiene, PPE, isolation, cleaning. | public_health |
| `health.public_health.vaccination` | METHOD | Вакцинация снижает риск заболевания или тяжёлого течения для многих инфекций. | Эффективность и показания зависят от вакцины и группы. | immunology |
| `health.public_health.surveillance` | SYSTEM | Эпиднадзор отслеживает случаи, тренды и вспышки. | Качество зависит от данных и reporting. | epidemiology |
| `health.public_health.outbreak` | EVENT | Вспышка — рост случаев выше ожидаемого уровня. | Требует расследования источника и мер контроля. | epidemiology |
| `health.nutrition.macronutrients` | TERM | Белки, жиры и углеводы дают энергию и строительные компоненты. | Потребности зависят от человека и состояния. | nutrition |
| `health.nutrition.micronutrients` | TERM | Витамины и минералы нужны в малых количествах для функций организма. | Дефицит и избыток могут быть вредны. | nutrition |
| `health.nutrition.energy_balance` | MODEL | Масса тела связана с балансом поступления и расхода энергии. | Биология и поведение сложнее простой арифметики. | health |
| `health.nutrition.food_fortification` | METHOD | Обогащение пищи добавляет micronutrients для снижения дефицитов. | Требует контроля доз и населения. | public_health |
| `health.care.elder_fall_prevention` | SAFETY_RULE | Профилактика падений включает освещение, убрать препятствия, обувь, поручни. | Индивидуальный риск требует оценки. | care |
| `health.care.medication_reconciliation` | METHOD | Medication reconciliation сверяет список лекарств при переходах care. | Снижает ошибки и дубли. | medication_safety |
| `health.safety.sharps` | SAFETY_RULE | Иглы и острые предметы требуют безопасных контейнеров и процедур. | Риск травм и инфекций. | clinical_safety |
| `health.safety.biohazard_waste` | SAFETY_RULE | Биологические отходы требуют маркировки, разделения и безопасной утилизации. | Нормы зависят от юрисдикции. | waste |
| `health.safety.oxygen_fire` | SAFETY_RULE | Кислород усиливает горение и требует контроля источников огня. | Особенно важно в медсреде. | fire_safety |
| `health.safety.pressurized_gas` | SAFETY_RULE | Баллоны с газом опасны давлением и должны быть закреплены. | Повреждение вентиля может превратить баллон в снаряд. | safety |
| `health.ethics.informed_consent` | PRINCIPLE | Информированное согласие требует понимания, добровольности и информации. | Есть исключения и особые случаи. | ethics |

---

## 📊 Batch 006 summary

```text
new units: 60
main layers:
  hygiene and water safety
  food safety
  first aid boundaries
  pharmaceutical forms and manufacturing
  CGMP / quality / validation
  medication safety
  medical devices and labs
  public health and care safety
```

