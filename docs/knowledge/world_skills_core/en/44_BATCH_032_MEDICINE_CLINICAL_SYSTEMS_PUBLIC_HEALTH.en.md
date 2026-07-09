# 🏥 Batch 032 — Medicine, Clinical Systems & Public Health Operations

**Язык:** русский  
**Статус:** 50K batch 032 / seed units / не L3 truth  
**Цель:** добавить осторожный системный слой о клинической работе, диагностике, больницах, общественном здоровье и безопасности пациента. Это не медицинская консультация.

---

## ⚠️ Safety note

Здесь хранятся общие знания о системах, рисках и процессах. Никаких диагнозов, дозировок, назначений или персональных лечебных инструкций.

---

## 📦 Knowledge Units

| ID | Тип | Суть | Условия / границы | Связи |
|---|---|---|---|---|
| `clinical.vital_signs` | MEASUREMENT_SET | Vital signs обычно включают температуру, пульс, дыхание, давление и oxygen saturation. | Интерпретация зависит от человека и контекста. | health |
| `clinical.blood_pressure` | MEASUREMENT | Артериальное давление отражает давление крови на стенки артерий. | Одно измерение не всегда диагноз. | physiology |
| `clinical.pulse_oximetry` | MEASUREMENT | Pulse oximetry оценивает насыщение крови кислородом через свет. | Ошибается при плохой перфузии, лаке, движении, CO. | devices |
| `clinical.temperature_measurement` | MEASUREMENT | Температура тела зависит от места и метода измерения. | Нормы и погрешности различаются. | devices |
| `clinical.triage.acuity` | PROCESS | Triage оценивает срочность помощи по риску ухудшения. | Не окончательный диагноз. | emergency |
| `clinical.history_taking` | METHOD | Анамнез собирает симптомы, время, контекст, лекарства, аллергии и историю. | Качество зависит от коммуникации. | medicine |
| `clinical.physical_exam` | METHOD | Осмотр и обследование ищут признаки через наблюдение, пальпацию, перкуссию, аускультацию. | Требует обучения. | medicine |
| `clinical.differential_diagnosis` | REASONING | Differential diagnosis перечисляет возможные причины симптома. | Вероятности меняются с данными. | reasoning |
| `clinical.red_flag` | SAFETY_RULE | Red flags — признаки, требующие срочной оценки. | Списки зависят от симптома. | safety |
| `clinical.laboratory.cbc` | TEST | Общий анализ крови оценивает клетки крови. | Интерпретация зависит от референсов и клиники. | lab |
| `clinical.laboratory.electrolytes` | TEST | Электролиты крови отражают баланс натрия, калия и других ионов. | Ошибки забора и состояния влияют. | lab |
| `clinical.laboratory.crp` | TEST | CRP — маркер воспаления, не специфичный к причине. | Не диагностирует сам по себе. | lab |
| `clinical.laboratory.culture` | TEST | Посев пытается вырастить микроорганизм для идентификации и чувствительности. | Контаминация и антибиотики влияют. | microbiology |
| `clinical.imaging.xray` | TEST | Рентген использует ионизирующее излучение для изображения плотных структур. | Доза и показания важны. | imaging |
| `clinical.imaging.ultrasound` | TEST | УЗИ использует звуковые волны для визуализации тканей. | Зависит от оператора и окна. | imaging |
| `clinical.imaging.ct` | TEST | CT строит послойное изображение с рентгеновским излучением. | Доза выше обычного рентгена. | imaging |
| `clinical.imaging.mri` | TEST | MRI использует магнитное поле и радиочастоты для изображения тканей. | Металлы и импланты требуют проверки. | imaging |
| `clinical.ecg` | TEST | ECG записывает электрическую активность сердца. | Требует правильного расположения электродов и интерпретации. | cardiology |
| `clinical.medication.allergy_record` | SAFETY_RECORD | Запись аллергий снижает риск опасного назначения. | Нужно отличать allergy от side effect. | medication_safety |
| `clinical.medication.reconciliation` | PROCESS | Medication reconciliation сверяет лекарства при переходах care. | Снижает дубли и пропуски. | care |
| `clinical.medication.five_rights` | SAFETY_HEURISTIC | Five rights проверяют patient, drug, dose, route, time. | Не покрывают все риски. | medication_safety |
| `clinical.medication.look_alike_sound_alike` | RISK | Похожие названия/упаковки лекарств создают риск ошибки. | Требует label design и checks. | safety |
| `clinical.infection.hand_hygiene_moments` | SAFETY_RULE | Гигиена рук в care зависит от моментов контакта и риска. | Перчатки не заменяют hygiene. | infection_control |
| `clinical.infection.isolation_precautions` | SAFETY_SYSTEM | Isolation precautions ограничивают передачу инфекций по путям распространения. | Требуют signage и compliance. | hospital |
| `clinical.infection.sterile_field` | SAFETY_METHOD | Sterile field защищает процедуру от загрязнения. | Нарушение поля требует реакции. | aseptic |
| `clinical.surgery.timeout` | SAFETY_PROCESS | Surgical timeout проверяет пациента, процедуру, сторону и готовность команды. | Работает только при реальном участии. | patient_safety |
| `clinical.surgery.checklist` | SAFETY_TOOL | Surgical checklist снижает пропуски критичных шагов. | Не должна быть формальностью. | safety |
| `clinical.anesthesia.monitoring` | SAFETY_SYSTEM | Анестезия требует постоянного мониторинга жизненных функций. | High-risk domain. | surgery |
| `clinical.blood.transfusion_match` | SAFETY_CHECK | Переливание требует совместимости и проверки личности. | Ошибка может быть тяжёлой. | lab |
| `clinical.falls.risk_assessment` | SAFETY_METHOD | Оценка риска падений учитывает состояние, лекарства, среду и мобильность. | Не заменяет профилактический план. | care |
| `clinical.pressure_injury_prevention` | SAFETY_METHOD | Профилактика пролежней использует смену положения, кожу, питание и поверхности. | Риск выше у неподвижных пациентов. | nursing |
| `clinical.nutrition.screening` | PROCESS | Nutrition screening выявляет риск недостаточного питания. | Требует дальнейшей оценки. | care |
| `clinical.discharge_planning` | PROCESS | План выписки готовит лекарства, follow-up, уход и предупреждения. | Плохая выписка ведёт к повторным госпитализациям. | care_transition |
| `clinical.referral` | PROCESS | Направление передаёт пациента к другому специалисту/службе. | Нужна причина, данные и срочность. | healthcare |
| `clinical.ehr` | SYSTEM | Electronic health record хранит медицинские данные пациента. | Риски privacy, usability, interoperability. | data |
| `clinical.ehr.problem_list` | RECORD | Problem list summarises active and past clinical issues. | Устаревший список опасен. | EHR |
| `clinical.ehr.order_entry` | SYSTEM | CPOE вводит назначения в электронную систему. | Decision support может помочь или перегрузить alerts. | EHR |
| `clinical.decision_support` | SYSTEM | Clinical decision support напоминает о рисках, дозах, взаимодействиях, guidelines. | Alert fatigue снижает пользу. | AI |
| `clinical.telemedicine` | CARE_MODEL | Telemedicine даёт care через удалённую связь. | Не подходит для всех состояний. | digital_health |
| `clinical.remote_monitoring` | SYSTEM | Remote monitoring собирает показатели пациента вне клиники. | Нужны data quality и response workflow. | devices |
| `clinical.patient_consent` | ETHICS_RULE | Пациент должен понимать процедуру, риски, альтернативы и право отказа. | Emergency exceptions возможны по закону. | ethics |
| `clinical.shared_decision_making` | METHOD | Shared decision-making соединяет evidence и предпочтения пациента. | Требует понятной коммуникации. | care |
| `clinical.health_literacy` | FACTOR | Health literacy влияет на понимание рекомендаций и навигацию в системе. | Система должна адаптировать язык. | communication |
| `clinical.interpreter_services` | SAFETY_SERVICE | Медицинский перевод снижает ошибки при языковом барьере. | Родственники не всегда безопасная замена. | equity |
| `clinical.quality.readmission_rate` | METRIC | Readmission rate показывает повторные госпитализации после выписки. | Может отражать case mix и социальные факторы. | quality |
| `clinical.quality.hai_rate` | METRIC | HAI rate отслеживает внутрибольничные инфекции. | Требует определения и surveillance. | infection |
| `clinical.quality.mortality_review` | PROCESS | Mortality review анализирует смерти для learning and improvement. | Нужна культура без сокрытия. | quality |
| `clinical.incident_reporting` | SAFETY_SYSTEM | Reporting near misses and incidents помогает учиться до повторения вреда. | Страх наказания снижает reporting. | patient_safety |
| `clinical.root_cause_analysis` | METHOD | RCA в медицине ищет системные причины adverse events. | Не должен завершаться "human error" без анализа. | safety |
| `clinical.human_factors` | PRINCIPLE | Human factors учитывает реальные ограничения людей, интерфейсов и среды. | Уменьшает blame и улучшает system design. | ergonomics |
| `clinical.public_health.screening` | METHOD | Screening ищет риск или раннее заболевание у людей без симптомов. | Требует balance benefit/harm. | public_health |
| `clinical.public_health.contact_tracing` | PROCESS | Contact tracing находит контакты инфекционного случая. | Зависит от доверия, privacy, скорости. | epidemiology |
| `clinical.public_health.vaccine_cold_chain` | LOGISTICS | Вакцины требуют контроля температуры до использования. | Разрыв цепи снижает качество. | logistics |
| `clinical.public_health.herd_immunity` | MODEL | Коллективная защита зависит от доли иммунных и передачи инфекции. | Порог зависит от pathogen. | epidemiology |
| `clinical.public_health.health_equity` | PRINCIPLE | Health equity учитывает несправедливые различия в доступе и outcomes. | Требует социальных данных. | society |
| `clinical.public_health.social_determinants` | MODEL | Здоровье зависит от жилья, дохода, среды, образования, работы и дискриминации. | Не сводить всё к личному выбору. | policy |
| `clinical.emergency.mass_casualty` | PROCESS | Mass casualty triage распределяет ограниченные ресурсы при множестве пострадавших. | Этический high-risk domain. | disaster |
| `clinical.emergency.decontamination` | PROCESS | Деконтаминация снижает перенос опасных веществ с пациента на людей и объект. | Требует PPE and zoning. | hazmat |
| `clinical.supply.critical_stock` | LOGISTICS | Больницы хранят critical stock для лекарств, PPE, кислорода и расходников. | Expiry и shortage risk важны. | supply_chain |
| `clinical.oxygen_system` | INFRA | Медицинский кислород требует источника, трубопроводов, регуляторов и безопасности. | Fire risk и pressure risk. | hospital |
| `clinical.waste.sharps` | WASTE_STREAM | Острые медицинские отходы собирают отдельно для предотвращения травм. | Контейнеры не переполнять. | waste |
| `clinical.waste.infectious` | WASTE_STREAM | Инфекционные отходы требуют маркировки, containment и обработки. | Нормы зависят от юрисдикции. | waste |
| `clinical.research.trial_phase` | MODEL | Клинические испытания проходят фазы для безопасности, дозы, эффективности и мониторинга. | Не все продукты идут одинаковым путём. | research |

---

## 📊 Batch 032 summary

```text
new units: 63
main layers:
  clinical workflow and diagnostics
  medication and patient safety
  hospital systems and EHR
  public health operations
```
