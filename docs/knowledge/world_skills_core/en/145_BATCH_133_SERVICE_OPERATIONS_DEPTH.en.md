# BATCH_133 — Service Operations Depth
# world_skills_core · source: world_skills_core:batch_133:service_operations_depth
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| svcopsd.queue.arrival_rate | Queue arrival rate | invariant | Arrival rate показывает, как часто клиенты, заявки или работы поступают в систему обслуживания. | основа расчета очереди |
| svcopsd.queue.service_rate | Queue service rate | invariant | Service rate показывает, как быстро один канал обслуживания завершает работу при заданных условиях. | сравнение спроса и мощности |
| svcopsd.queue.utilization | Service utilization | invariant | Utilization равна отношению нагрузки к доступной мощности, и при приближении к 100% ожидание резко растет. | нельзя планировать на полный максимум |
| svcopsd.queue.variability | Queue variability | invariant | Вариативность прихода и длительности обслуживания увеличивает ожидание даже при той же средней нагрузке. | средние значения обманывают |
| svcopsd.queue.priority_rule | Priority rule | variant | Правило приоритета определяет, кого обслуживать раньше: по срочности, SLA, риску, стоимости или очередности. | справедливость и эффективность |
| svcopsd.queue.triage_service | Service triage | invariant | Triage в сервисе сортирует обращения по срочности, влиянию и требуемому уровню компетенции. | быстрее решать критичное |
| svcopsd.scheduling.appointment_slot | Appointment slot | invariant | Слот записи связывает клиента, ресурс, длительность, место и ограничения календаря. | управляемая загрузка |
| svcopsd.scheduling.no_show_rate | No-show rate | variant | No-show rate показывает долю записей, где клиент не пришел и не отменил вовремя. | влияет на overbooking |
| svcopsd.scheduling.overbooking | Service overbooking | variant | Overbooking может компенсировать no-show, но увеличивает риск перегруза и ухудшения опыта при высокой явке. | баланс дохода и качества |
| svcopsd.scheduling.buffer_time | Buffer time | invariant | Buffer time между задачами покрывает вариативность, подготовку, переходы и короткие сбои. | расписание становится реалистичным |
| svcopsd.scheduling.skill_based_routing | Skill-based routing | invariant | Skill-based routing направляет заявку к человеку или команде с подходящей компетенцией. | меньше переадресаций |
| svcopsd.dispatch.field_service | Field service dispatch | invariant | Dispatch field service связывает задачу, технику, маршрут, запасные части, SLA и доступ клиента. | выездное обслуживание |
| svcopsd.dispatch.route_density | Route density | variant | Плотность маршрута показывает, сколько работ можно выполнить на территории с учетом переездов и окон доступа. | экономия времени дороги |
| svcopsd.dispatch.first_time_fix | First-time fix rate | invariant | First-time fix rate измеряет долю выездов, завершенных без повторного визита по той же проблеме. | качество диагностики и запасов |
| svcopsd.dispatch.parts_availability | Parts availability | invariant | Наличие нужной запчасти в момент обслуживания часто определяет, будет ли проблема решена с первого раза. | связать склад и расписание |
| svcopsd.sla.response_time | SLA response time | invariant | Response time SLA измеряет время до первого принятого действия или ответа, а не обязательно до полного решения. | правильно читать SLA |
| svcopsd.sla.resolution_time | SLA resolution time | invariant | Resolution time SLA измеряет время до восстановления услуги или закрытия заявки по согласованным критериям. | клиенту важен результат |
| svcopsd.sla.service_credit | Service credit | variant | Service credit компенсирует нарушение SLA по заранее заданной формуле, но не всегда покрывает реальные потери клиента. | управлять ожиданиями |
| svcopsd.sla.exclusion_window | SLA exclusion window | variant | Исключение из SLA может покрывать плановые работы, форс-мажор, действия клиента или внешние зависимости. | читать мелкий текст |
| svcopsd.sla.error_budget_service | Service error budget | variant | Error budget переводит допустимый уровень недоступности или дефектов в управляемый лимит риска. | баланс скорости и надежности |
| svcopsd.complaint.intake | Complaint intake | invariant | Прием жалобы должен фиксировать клиента, проблему, время, канал, ожидание и доказательства. | не потерять контекст |
| svcopsd.complaint.classification | Complaint classification | invariant | Классификация жалоб группирует причины по продукту, процессу, поведению, задержке, цене или коммуникации. | видеть повторяющиеся проблемы |
| svcopsd.complaint.service_recovery | Service recovery | variant | Service recovery пытается восстановить доверие после сбоя через признание проблемы, исправление и разумную компенсацию. | удержание клиента |
| svcopsd.complaint.closed_loop | Closed-loop complaint | invariant | Closed-loop complaint process проверяет, что клиент получил ответ и причина проблемы передана владельцу процесса. | жалоба становится улучшением |
| svcopsd.customer.journey_map | Customer journey map | variant | Journey map показывает шаги клиента, точки контакта, ожидания, эмоции и сбои в процессе услуги. | улучшать опыт системно |
| svcopsd.customer.touchpoint | Service touchpoint | invariant | Touchpoint — момент взаимодействия клиента с услугой, каналом, сотрудником, системой или физической средой. | качество складывается по точкам |
| svcopsd.customer.moment_of_truth | Moment of truth | variant | Moment of truth — критический контакт, где клиент быстро формирует доверие или недоверие к услуге. | фокусировать обучение |
| svcopsd.customer.expectation_gap | Expectation gap | invariant | Разрыв ожиданий возникает, когда обещание, восприятие или фактическая услуга не совпадают. | маркетинг влияет на операцию |
| svcopsd.capacity.demand_forecast | Service demand forecast | invariant | Прогноз спроса на услугу должен учитывать сезонность, акции, погоду, события, базу клиентов и прошлые отклонения. | планирование смен |
| svcopsd.capacity.cross_training | Cross-training | variant | Cross-training повышает гибкость команды, позволяя людям закрывать несколько типов задач при пиках или отсутствиях. | устойчивость расписания |
| svcopsd.capacity.bottleneck_step | Service bottleneck | invariant | Узкое место сервиса — шаг, ресурс или решение, ограничивающее поток всего процесса. | улучшать не все сразу |
| svcopsd.capacity.work_in_progress | Service WIP | invariant | Work in progress в услугах — открытые, но незавершенные заявки, дела или клиенты в процессе. | скрытая очередь |
| svcopsd.quality.service_standard | Service standard | invariant | Service standard переводит желаемое качество в наблюдаемые требования: срок, тон, точность, полноту или чистоту. | обучаемый стандарт |
| svcopsd.quality.mystery_shopping | Mystery shopping | variant | Mystery shopping проверяет фактический сервис через имитацию клиента, но должен быть этичным и репрезентативным. | наблюдение опыта |
| svcopsd.quality.call_calibration | Call calibration | variant | Calibration review выравнивает оценки качества между супервайзерами через общие примеры и критерии. | меньше субъективности |
| svcopsd.quality.knowledge_base_article | Service knowledge base article | invariant | Статья базы знаний должна описывать симптом, применимость, шаги, ограничения, эскалацию и дату обновления. | единые ответы |
| svcopsd.quality.script_flexibility | Script flexibility | variant | Скрипт обслуживания задаёт структуру разговора, но должен оставлять место для контекста и реальной проблемы клиента. | не звучать механически |
| svcopsd.metrics.nps_limit | NPS limit | variant | NPS измеряет готовность рекомендовать, но не объясняет сам по себе причину оценки. | нужен анализ комментариев |
| svcopsd.metrics.csat | CSAT | invariant | CSAT измеряет удовлетворенность конкретным взаимодействием, продуктом или периодом через прямой вопрос клиенту. | локальная обратная связь |
| svcopsd.metrics.ces | Customer effort score | invariant | Customer effort score оценивает, насколько трудно клиенту было получить решение. | снижать трение |
| svcopsd.metrics.abandonment_rate | Abandonment rate | invariant | Abandonment rate показывает долю клиентов, покинувших очередь до обслуживания. | сигнал перегруза |
| svcopsd.metrics.reopen_rate | Reopen rate | invariant | Reopen rate измеряет долю заявок, вновь открытых после закрытия из-за неполного или неправильного решения. | качество закрытия |
| svcopsd.metrics.backlog_age | Backlog age | invariant | Возраст backlog показывает, как долго незавершенные задачи ждут обработки, а не только их количество. | старые задачи требуют внимания |
| svcopsd.improvement.root_cause_feedback | Service root-cause feedback | invariant | Сервисное улучшение требует передавать повторяющиеся причины жалоб владельцам продукта, процесса или политики. | не лечить только симптомы |
