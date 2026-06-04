# BATCH_138 — Data Governance Detail
# world_skills_core · source: world_skills_core:batch_138:data_governance_detail
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| datagov.catalog.data_catalog | Data catalog | invariant | Data catalog описывает наборы данных, владельцев, определения, источники, качество, доступ и использование. | найти и понять данные |
| datagov.catalog.business_glossary | Business glossary | invariant | Business glossary задаёт согласованные бизнес-термины и связывает их с полями данных и правилами расчета. | один язык для метрик |
| datagov.catalog.data_domain | Data domain | invariant | Data domain группирует данные по предметной области, владельцам и правилам управления. | распределить ответственность |
| datagov.catalog.dataset_owner | Dataset owner | invariant | Dataset owner отвечает за смысл, доступ, качество и жизненный цикл конкретного набора данных. | данные имеют владельца |
| datagov.catalog.data_steward | Data steward | invariant | Data steward ведёт определения, качество, правила и координацию изменений данных в своей области. | ежедневная дисциплина данных |
| datagov.lineage.source_to_target | Source-to-target lineage | invariant | Lineage source-to-target показывает, как данные проходят от источника через трансформации к отчету или продукту. | расследовать ошибки |
| datagov.lineage.transformation_rule | Transformation rule | invariant | Правило трансформации описывает, как поле очищается, объединяется, агрегируется или вычисляется. | воспроизводимость метрик |
| datagov.lineage.impact_analysis | Data impact analysis | invariant | Impact analysis показывает, какие отчеты, модели или процессы изменятся при правке источника или поля. | не ломать downstream |
| datagov.lineage.manual_extract_risk | Manual extract risk | variant | Ручная выгрузка данных разрывает lineage и повышает риск устаревшей, измененной или неполной копии. | контролировать spreadsheets |
| datagov.quality.completeness | Data completeness | invariant | Completeness измеряет, заполнены ли необходимые поля для заданного процесса или решения. | пустое поле может ломать процесс |
| datagov.quality.validity | Data validity | invariant | Validity проверяет, соответствует ли значение разрешенному формату, диапазону, справочнику или правилу. | машинная проверка |
| datagov.quality.consistency | Data consistency | invariant | Consistency проверяет, не противоречат ли значения друг другу между системами, таблицами или полями. | одна реальность в разных системах |
| datagov.quality.uniqueness | Data uniqueness | invariant | Uniqueness проверяет, нет ли нежелательных дублей сущности, записи или ключа. | дедуп клиентов и товаров |
| datagov.quality.timeliness | Data timeliness | invariant | Timeliness показывает, доступны ли данные достаточно быстро и свежо для решения. | устаревшие данные вредят |
| datagov.quality.accuracy | Data accuracy | invariant | Accuracy оценивает близость данных к реальному состоянию или надежному источнику истины. | верность факта |
| datagov.quality.rule_owner | Data quality rule owner | invariant | У правила качества данных должен быть владелец, который определяет смысл, порог, исключения и действия при нарушении. | правило не живет само |
| datagov.quality.issue_workflow | Data quality issue workflow | invariant | Workflow проблемы качества данных фиксирует дефект, владельца, приоритет, причину, исправление и проверку результата. | не только dashboard |
| datagov.master.golden_record | Golden record | invariant | Golden record объединяет лучшие атрибуты сущности из нескольких источников по заданным правилам доверия. | единый клиент или продукт |
| datagov.master.match_merge | Match and merge | variant | Match and merge ищет записи одной сущности и объединяет их, сохраняя правила выживания атрибутов. | MDM dedup |
| datagov.master.survivorship_rule | Survivorship rule | invariant | Survivorship rule определяет, какой источник или значение выигрывает при конфликте атрибутов мастер-данных. | предсказуемое объединение |
| datagov.master.reference_data | Reference data | invariant | Reference data задаёт контролируемые списки кодов, категорий, стран, статусов или типов для согласованного использования. | меньше разнобоя |
| datagov.master.hierarchy_management | Hierarchy management | variant | Управление иерархиями задаёт связи parent-child между продуктами, организациями, территориями или счетами. | агрегирование и права |
| datagov.access.least_privilege | Least privilege data access | invariant | Доступ к данным должен даваться по минимально необходимым правам для роли и задачи. | снизить риск утечки |
| datagov.access.role_based | Role-based access | invariant | Role-based access назначает права через роли, а не индивидуальные исключения для каждого пользователя. | проще audit |
| datagov.access.attribute_based | Attribute-based access | variant | Attribute-based access учитывает атрибуты пользователя, данных, контекста и действия при принятии решения доступа. | гибкий контроль |
| datagov.access.break_glass | Break-glass access | variant | Break-glass access дает аварийный доступ с усиленным логированием, ограничением срока и последующей проверкой. | помощь при инциденте |
| datagov.privacy.data_minimization | Data minimization | invariant | Data minimization требует собирать и хранить только данные, необходимые для определенной цели. | меньше риск и стоимость |
| datagov.privacy.purpose_limitation | Purpose limitation | invariant | Purpose limitation ограничивает использование данных теми целями, для которых они были собраны или разрешены. | не растягивать согласие |
| datagov.privacy.pseudonymization | Pseudonymization | invariant | Pseudonymization заменяет прямые идентификаторы, но остается обратимой или связываемой при наличии дополнительных данных. | не равно анонимизация |
| datagov.privacy.anonymization_limit | Anonymization limit | variant | Анонимизация требует снижения риска повторной идентификации, а не простого удаления имени. | учитывать квазиидентификаторы |
| datagov.retention.retention_policy | Data retention policy | invariant | Политика хранения данных задаёт сроки, основания, исключения, архивирование и уничтожение по типам данных. | управляемый lifecycle |
| datagov.retention.defensible_deletion | Defensible deletion | invariant | Defensible deletion удаляет данные по утвержденным правилам и журналам так, чтобы решение можно было объяснить. | меньше лишних данных |
| datagov.retention.archive_tier | Archive tier | variant | Archive tier хранит редко используемые данные дешевле, но должен сохранять поиск, целостность и правила доступа. | баланс цена/доступность |
| datagov.retention.restore_test | Restore test | invariant | Проверка восстановления подтверждает, что архив или backup можно реально прочитать и использовать после сбоя. | backup без restore не доказан |
| datagov.metrics.metric_definition | Metric definition | invariant | Определение метрики должно описывать формулу, зерно, фильтры, источник, время обновления и владельца. | избежать спорных dashboards |
| datagov.metrics.grain | Data grain | invariant | Grain определяет, что представляет одна строка или запись набора данных. | ошибка grain ломает агрегацию |
| datagov.metrics.slowly_changing_dimension | Slowly changing dimension | variant | Slowly changing dimension управляет историей атрибутов, которые меняются со временем, например адресом или сегментом клиента. | историческая аналитика |
| datagov.metrics.reconciliation | Data reconciliation | invariant | Reconciliation сравнивает итоги между системами или этапами обработки и объясняет расхождения. | доверие к отчетам |
| datagov.change.schema_change | Schema change control | invariant | Изменение схемы данных требует оценки downstream влияния, версии, миграции и коммуникации пользователям. | не ломать потребителей |
| datagov.change.deprecation_notice | Data deprecation notice | variant | Deprecation notice заранее сообщает, что поле, таблица или API будут отключены или заменены. | время на миграцию |
| datagov.change.contract_testing | Data contract testing | variant | Data contract testing проверяет, что производитель данных сохраняет ожидаемую схему, типы, обязательность и смысловые правила. | защита pipelines |
| datagov.ai.training_data_rights | Training data rights | variant | Данные для обучения модели требуют проверки прав использования, чувствительности, происхождения и ограничений повторного применения. | governance для AI |
| datagov.ai.feature_store | Feature store governance | variant | Feature store governance управляет определениями признаков, lineage, свежестью, доступом и training-serving consistency. | надежные ML признаки |
| datagov.ai.model_input_drift | Model input drift data | invariant | Дрейф входных данных модели показывает изменение распределений или качества признаков относительно периода обучения. | мониторинг ML систем |
