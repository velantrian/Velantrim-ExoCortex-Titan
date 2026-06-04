# 🏛️ Batch 019 — Civic Governance, Public Services & Emergency Systems

**Язык:** русский  
**Статус:** 50K batch 019 / seed units / не L3 truth  
**Цель:** добавить знания о том, как работают государства, города, службы, документы, налоги, emergency management и публичные решения.

---

## 📦 Knowledge Units

| ID | Тип | Суть | Условия / границы | Связи |
|---|---|---|---|---|
| `civic.state.institution` | TERM | Государственный институт выполняет публичную функцию по правилам и полномочиям. | Формальные правила могут отличаться от практики. | governance |
| `civic.separation_of_powers` | PRINCIPLE | Разделение властей снижает концентрацию полномочий. | Реальная независимость зависит от институтов. | law |
| `civic.rule_of_law` | PRINCIPLE | Rule of law означает предсказуемость, равенство перед законом и ограничение власти правом. | Может быть нарушен практикой. | law |
| `civic.public_accountability` | PRINCIPLE | Подотчётность требует объяснения решений и возможности проверки. | Без данных и санкций слабеет. | governance |
| `civic.transparency` | PRINCIPLE | Прозрачность открывает информацию о решениях, деньгах и процедурах. | Не вся информация может быть публичной из-за безопасности/приватности. | governance |
| `civic.public_budget` | SYSTEM | Бюджет распределяет публичные доходы на услуги, инфраструктуру и обязательства. | Политический и экономический документ одновременно. | finance |
| `civic.tax.income` | PUBLIC_FINANCE | Подоходный налог взимается с доходов физических или юридических лиц. | Ставки и база зависят от закона. | tax |
| `civic.tax.vat` | PUBLIC_FINANCE | VAT/НДС — налог на добавленную стоимость по цепочке продаж. | Требует учёта входного и выходного налога. | finance |
| `civic.tax.property` | PUBLIC_FINANCE | Налог на имущество связан с владением недвижимостью или активами. | Оценка стоимости важна и спорна. | local_government |
| `civic.tax.customs_duty` | PUBLIC_FINANCE | Таможенные пошлины взимаются при перемещении товаров через границу. | Связаны с HS code, origin, value. | trade |
| `civic.procurement.public_tender` | PROCESS | Публичная закупка выбирает поставщика по правилам конкуренции и прозрачности. | Риск коррупции и формальности. | governance |
| `civic.procurement.specification` | DOCUMENT | Техническое задание закупки описывает нужный результат и критерии. | Слишком узкое ТЗ может ограничивать конкуренцию. | contracts |
| `civic.procurement.conflict_of_interest` | RISK | Конфликт интересов искажает публичное решение в пользу частной выгоды. | Требует раскрытия и управления. | ethics |
| `civic.license.permit` | DOCUMENT | Разрешение даёт право на деятельность при выполнении условий. | Условия зависят от риска и закона. | regulation |
| `civic.registry.civil_status` | SYSTEM | Реестры актов гражданского состояния фиксируют рождение, брак, смерть. | Ошибки влияют на права и документы. | public_records |
| `civic.registry.property` | SYSTEM | Реестр недвижимости связывает объект, владельца, ограничения и историю. | Качество записей важно для рынка. | land |
| `civic.identity.document` | DOCUMENT | Документ личности связывает человека с юридической идентичностью. | Риски: подделка, утрата, privacy. | identity |
| `civic.residency.registration` | PROCESS | Регистрация места проживания помогает услугам, налогам и статистике. | Может ограничивать доступ при плохой политике. | administration |
| `civic.election.voter_roll` | SYSTEM | Список избирателей определяет, кто может голосовать. | Ошибки подрывают доверие. | democracy |
| `civic.election.ballot_secret` | PRINCIPLE | Тайна голосования защищает от давления и покупки голоса. | Требует процедур и дизайна участка. | democracy |
| `civic.election.observation` | QUALITY_CHECK | Наблюдение повышает доверие к выборам через независимую проверку. | Наблюдатели должны иметь доступ и правила. | governance |
| `civic.court.due_process` | PRINCIPLE | Due process требует справедливой процедуры перед лишением прав. | Реализация различается по системам права. | law |
| `civic.court.evidence` | TERM | Доказательства в суде должны быть допустимыми и относимыми. | Стандарты зависят от процесса. | law |
| `civic.court.appeal` | PROCESS | Апелляция проверяет решение нижестоящего органа или суда. | Не всегда пересматривает факты полностью. | law |
| `civic.police.public_order` | PUBLIC_SERVICE | Полиция поддерживает порядок и расследует правонарушения в рамках закона. | Риск abuse требует oversight. | safety |
| `civic.fire_service` | PUBLIC_SERVICE | Пожарная служба тушит пожары, спасает людей и предотвращает риски. | Время реакции зависит от сети станций и доступа. | emergency |
| `civic.ems` | PUBLIC_SERVICE | Emergency medical services оказывают срочную помощь и транспортировку. | Не заменяют профилактическую медицину. | health |
| `civic.dispatch.112_911` | SYSTEM | Единый номер экстренной помощи маршрутизирует вызовы к службам. | Нужны точный адрес и приоритет. | emergency |
| `civic.emergency.incident_command` | SYSTEM | Incident command задаёт роли, командование и координацию при ЧС. | Масштабируется под событие. | disaster |
| `civic.emergency.evacuation_order` | PROCESS | Эвакуация выводит людей из зоны опасности по маршрутам и приоритетам. | Требует транспорта, коммуникации, укрытий. | safety |
| `civic.emergency.shelter` | INFRA | Временные укрытия дают базовую безопасность, воду, санитарные условия и информацию. | Уязвимые группы требуют специальных мер. | disaster |
| `civic.emergency.early_warning` | SYSTEM | Раннее предупреждение сообщает угрозу до воздействия. | Должно быть понятно и доверено. | resilience |
| `civic.emergency.risk_communication` | METHOD | Risk communication объясняет угрозу, действия и неопределённость. | Паника часто растёт от недоверия, а не от честной информации. | communication |
| `civic.disaster.hazard_vulnerability_capacity` | MODEL | Риск ЧС связан с hazard, vulnerability и capacity. | Опасность без уязвимости не равна катастрофе. | resilience |
| `civic.disaster.business_continuity` | METHOD | Continuity planning сохраняет ключевые функции организации при нарушениях. | Требует тестов и резервов. | operations |
| `civic.disaster.mutual_aid` | SYSTEM | Mutual aid позволяет службам помогать друг другу через соглашения. | Нужны совместимые процедуры и связь. | emergency |
| `civic.public_health.health_department` | PUBLIC_SERVICE | Public health agency мониторит, предупреждает и реагирует на угрозы здоровью населения. | Балансирует права, данные и риск. | health |
| `civic.public_health.food_inspection` | PUBLIC_SERVICE | Пищевые инспекции проверяют безопасность процессов и объектов. | Инспекция — выборочная, не абсолютная гарантия. | food_safety |
| `civic.public_health.vector_control` | PUBLIC_SERVICE | Контроль переносчиков снижает риск болезней от комаров, клещей, грызунов. | Требует экологии и общественного участия. | public_health |
| `civic.education.public_school` | PUBLIC_SERVICE | Публичная школа даёт базовое образование и социальную функцию. | Качество зависит от финансирования, кадров, среды. | education |
| `civic.library.public` | PUBLIC_SERVICE | Библиотека обеспечивает доступ к знаниям, цифровым услугам и культуре. | Роль шире хранения книг. | knowledge |
| `civic.transport.public_agency` | PUBLIC_SERVICE | Транспортное агентство планирует маршруты, тарифы, расписание и инфраструктуру. | Должно учитывать доступность и спрос. | transport |
| `civic.water_utility` | PUBLIC_SERVICE | Водоканал управляет водоснабжением и часто канализацией. | Требует тарифов, инвестиций, контроля качества. | water |
| `civic.waste_utility` | PUBLIC_SERVICE | Служба отходов организует сбор, переработку, полигоны и санитарный контроль. | Нужны маршруты и поведение жителей. | waste |
| `civic.urban_planning.master_plan` | DOCUMENT | Генплан задаёт долгосрочное развитие территории. | Реализация зависит от политики и денег. | urban |
| `civic.urban_planning.land_use` | REGULATION | Land use определяет разрешённые функции участка. | Может снижать конфликты или создавать дефицит жилья. | planning |
| `civic.urban_planning.building_code` | REGULATION | Строительные нормы задают минимальные требования безопасности и качества. | Обновляются после опыта аварий и технологий. | construction |
| `civic.urban_planning.permit_review` | PROCESS | Разрешительная экспертиза проверяет проект на соответствие нормам. | Может быть узким местом. | construction |
| `civic.housing.affordability` | POLICY_GOAL | Доступность жилья связана с доходом, ценой, кредитом, землёй и предложением. | Нет одного решения для всех рынков. | economy |
| `civic.social_services.means_test` | METHOD | Means test оценивает нуждаемость по доходам/активам. | Может создавать административные барьеры. | welfare |
| `civic.social_services.case_management` | METHOD | Case management координирует помощь человеку или семье через службы. | Требует privacy и доверия. | care |
| `civic.labor_inspection` | PUBLIC_SERVICE | Трудовая инспекция проверяет безопасность и права работников. | Эффективность зависит от полномочий и ресурсов. | labor |
| `civic.environmental_inspection` | PUBLIC_SERVICE | Экологический контроль проверяет выбросы, отходы, воду и compliance. | Требует измерений и санкций. | environment |
| `civic.statistics.census` | DATA_SYSTEM | Перепись собирает данные о населении для политики и планирования. | Privacy и полнота критичны. | statistics |
| `civic.statistics.administrative_data` | DATA_SYSTEM | Административные данные создаются в процессе работы служб. | Не всегда подходят для анализа без очистки. | data |
| `civic.open_data` | POLICY_TOOL | Open data публикует государственные данные для проверки и инноваций. | Нужно удалять персональные и рискованные данные. | transparency |
| `civic.digital_government` | SYSTEM | Digital government переносит услуги в онлайн-каналы. | Не должен исключать людей без доступа/навыков. | software |
| `civic.digital_identity` | SYSTEM | Digital identity позволяет удалённо подтверждать личность. | Высокие риски privacy и security. | cybersecurity |
| `civic.cyber_public_sector` | RISK | Госуслуги и инфраструктура являются целями кибератак. | Требуются резервирование и incident response. | cyber |
| `civic.public_participation` | PROCESS | Участие жителей помогает учитывать локальное знание и легитимность решений. | Может быть формальным без влияния. | governance |
| `civic.consultation` | PROCESS | Публичная консультация собирает мнения по проекту или норме. | Нужно показывать, что изменилось из-за feedback. | governance |
| `civic.conflict_mediation` | METHOD | Медиация помогает сторонам найти приемлемое решение без суда. | Не подходит при насилии или сильном принуждении. | conflict |
| `civic.anti_corruption.whistleblower` | SAFETY_SYSTEM | Защита информаторов снижает риск мести за сообщение о нарушениях. | Требует независимого канала. | ethics |
| `civic.audit.public` | QUALITY_CHECK | Публичный аудит проверяет расходы, процедуры и результаты. | Должен быть независимым. | accountability |
| `civic.policy.pilot_program` | METHOD | Пилотная программа тестирует решение на малом масштабе перед расширением. | Нужно заранее определить метрики. | policy |
| `civic.policy.sunset_clause` | RULE | Sunset clause автоматически прекращает норму, если её не продлить. | Помогает проверять временные меры. | law |
| `civic.policy.impact_assessment` | METHOD | Impact assessment оценивает последствия политики до внедрения. | Качество зависит от данных и честности. | governance |
| `civic.resilience.community_network` | SYSTEM | Социальные связи района повышают способность переживать кризисы. | Нужны доверие и включённость. | resilience |

---

## 📊 Batch 019 summary

```text
new units: 68
main layers:
  public institutions and law
  taxes, permits, registries, services
  emergency systems and public health
  urban planning, transparency and resilience
```
