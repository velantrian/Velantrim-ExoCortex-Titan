# 🏨 Batch 039 — Retail, Hospitality, Tourism & Service Operations

**Язык:** русский  
**Статус:** 50K batch 039 / seed units / не L3 truth  
**Цель:** добавить практическую базу услуг: магазины, рестораны, отели, туризм, клиентский опыт, очереди, бронирования и service quality.

---

## 📦 Knowledge Units

| ID | Тип | Суть | Условия / границы | Связи |
|---|---|---|---|---|
| `retail.store.layout` | DESIGN_METHOD | План магазина направляет поток людей и видимость товаров. | Не должен мешать безопасности. | retail |
| `retail.shelf_planogram` | TOOL | Планограмма задаёт размещение товаров на полке. | Влияет на продажи и пополнение. | merchandising |
| `retail.sku` | TERM | SKU — уникальная единица учёта товара. | Не всегда равен barcode. | inventory |
| `retail.pos_system` | SYSTEM | POS фиксирует продажу, оплату, товар и чек. | Связан со складом и бухгалтерией. | software |
| `retail.barcode_scanning` | PROCESS | Сканирование штрихкода ускоряет продажу и снижает ошибки цены. | Нужны правильные master data. | retail |
| `retail.price_tag_accuracy` | QUALITY_CHECK | Цена на полке должна соответствовать цене в системе. | Ошибки подрывают доверие и законность. | consumer |
| `retail.stockout` | FAILURE_MODE | Stockout — отсутствие товара при спросе. | Теряется продажа и доверие. | inventory |
| `retail.shrinkage` | METRIC | Shrinkage — потери запасов от краж, ошибок, порчи. | Требует анализа причин. | security |
| `retail.loss_prevention` | SYSTEM | Loss prevention снижает кражи и потери без разрушения клиентского опыта. | Баланс privacy and safety. | security |
| `retail.return_policy` | POLICY | Политика возврата задаёт условия обмена/возврата. | Влияет на продажи и fraud. | consumer |
| `retail.visual_merchandising` | METHOD | Visual merchandising оформляет товар для внимания и понимания. | Должно помогать выбору, не только украшать. | design |
| `retail.omnichannel` | MODEL | Omnichannel связывает магазин, сайт, доставку и возвраты. | Требует единого inventory data. | commerce |
| `hospitality.front_desk` | SERVICE_PROCESS | Reception/front desk встречает гостя, проверяет бронь, документы и оплату. | Первое впечатление критично. | hotel |
| `hospitality.reservation` | SYSTEM | Reservation system управляет номерами, тарифами, датами и каналами. | Overbooking risk needs controls. | hotel |
| `hospitality.housekeeping` | PROCESS | Housekeeping поддерживает чистоту, комплектность и готовность номера. | Требует checklist and timing. | hotel |
| `hospitality.room_turnover` | METRIC | Turnover time показывает, как быстро номер готовят после гостя. | Speed не должен ломать качество. | operations |
| `hospitality.revenue_management` | METHOD | Revenue management меняет цену по спросу, сезону и доступности. | Может раздражать клиентов без прозрачности. | pricing |
| `hospitality.occupancy_rate` | METRIC | Occupancy rate показывает долю занятых номеров. | Высокая загрузка не гарантирует прибыль. | hotel |
| `hospitality.revpar` | METRIC | RevPAR объединяет цену и загрузку номера. | Не учитывает все расходы. | finance |
| `hospitality.guest_recovery` | METHOD | Service recovery исправляет проблему гостя быстро и справедливо. | Поздняя реакция дороже. | service |
| `hospitality.food_service_flow` | PROCESS | Ресторанная услуга соединяет бронирование, заказ, кухню, подачу, оплату. | Узкое место может быть в зале или кухне. | restaurant |
| `hospitality.table_turnover` | METRIC | Table turnover показывает скорость освобождения столов. | Не должен ухудшать опыт гостя. | restaurant |
| `hospitality.menu_engineering` | METHOD | Menu engineering сравнивает популярность и маржинальность блюд. | Данные должны учитывать waste and labor. | food |
| `hospitality.allergen_protocol` | SAFETY_PROCESS | Протокол аллергенов передаёт информацию от гостя к кухне и подаче. | Ошибка может быть опасной. | food_safety |
| `tourism.itinerary` | DOCUMENT | Маршрут поездки связывает места, время, транспорт, брони и риски. | Слишком плотный маршрут ломается. | travel |
| `tourism.seasonality` | MODEL | Сезонность влияет на цены, погоду, толпы и доступность. | Сезон не одинаков для всех регионов. | geography |
| `tourism.carrying_capacity` | CONSTRAINT | Туристическая ёмкость ограничивает нагрузку на место и жителей. | Перегруз разрушает опыт и природу. | sustainability |
| `tourism.local_regulations` | RULE | Путешествия зависят от виз, налогов, правил поведения и ограничений. | Меняются по датам и странам. | law |
| `tourism.travel_insurance` | RISK_TOOL | Travel insurance покрывает часть медицинских, отменных и багажных рисков. | Exclusions критичны. | insurance |
| `tourism.safety_briefing` | COMMUNICATION | Safety briefing объясняет риски маршрута и действия при ЧС. | Должен быть понятным и конкретным. | safety |
| `service.blueprint` | TOOL | Service blueprint показывает visible и backstage действия услуги. | Помогает находить сбои. | operations |
| `service.touchpoint` | TERM | Touchpoint — момент взаимодействия клиента с сервисом. | Каждый touchpoint влияет на доверие. | CX |
| `service.queue_management` | METHOD | Очередями управляют через capacity, priority, appointments and communication. | Неопределённое ожидание ощущается дольше. | operations |
| `service.appointment_scheduling` | SYSTEM | Запись по времени снижает очереди и распределяет нагрузку. | No-shows require policy. | service |
| `service.no_show` | FAILURE_MODE | No-show — клиент не приходит на бронь/запись. | Вредит capacity and revenue. | operations |
| `service.sla_response_time` | METRIC | Response time SLA задаёт ожидание первого ответа. | Решение проблемы может иметь другой SLA. | support |
| `service.customer_journey` | TOOL | Customer journey показывает путь клиента от потребности до результата. | Нужно проверять реальными данными. | design |
| `service.persona` | TOOL | Persona моделирует типичного пользователя для дизайна сервиса. | Может стать стереотипом без research. | UX |
| `service.complaint_handling` | PROCESS | Жалоба — источник улучшения, если её записать и разобрать. | Защитная реакция ухудшает доверие. | quality |
| `service.quality_gap` | MODEL | Service quality gap возникает между ожиданием и фактическим опытом. | Ожидания формирует маркетинг. | quality |
| `service.accessibility` | PRINCIPLE | Услуги должны учитывать людей с разными возможностями и языками. | Доступность лучше встроить в процесс. | inclusion |
| `service.staff_training` | PROCESS | Обучение персонала связывает стандарты, сценарии, безопасность и сервис. | Одного тренинга мало без практики. | HR |
| `service.tipping_culture` | CULTURAL_FACTOR | Чаевые зависят от страны, профессии и нормы. | Может влиять на доходы и поведение. | culture |
| `service.reputation_reviews` | DATA_SOURCE | Отзывы показывают восприятие клиентов, но имеют bias. | Нужен анализ тем, не только рейтинг. | analytics |
| `service.mystery_shopper` | QUALITY_CHECK | Mystery shopper проверяет сервис как клиент. | Даёт выборочную картину. | QA |

---

## 📊 Batch 039 summary

```text
new units: 45
main layers:
  retail operations
  hospitality and restaurants
  tourism and safety
  service design and customer experience
```
