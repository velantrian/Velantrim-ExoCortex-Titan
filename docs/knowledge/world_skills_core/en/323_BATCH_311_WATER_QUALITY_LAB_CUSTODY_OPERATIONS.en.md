# BATCH 311: Water Quality Laboratory Chain-of-Custody Operations

**KnowledgeUnits:** 44  
**Namespace:** `wqlabcustody.*`  
**Scope:** bottle prep, field custody, preservation, receiving, login, storage, transfer and reporting.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| wqlabcustody.bottle.container_matrix | container by matrix | METHOD | Бутылки выбирают по matrix, analyte, volume, material compatibility и method requirement. | Неверный контейнер может сделать результат непригодным. |
| wqlabcustody.bottle.preservative_match | preservative match | CONSTRAINT | Acid, base, dechlorinating agent или no preservative задаются аналитическим методом. | Сохраняет analyte до анализа и снижает rejection. |
| wqlabcustody.bottle.precleaned_cert | precleaned certificate | RECORD | Для trace metals и organics используют precleaned bottles с lot certificate. | Доказывает, что тара не внесла загрязнение. |
| wqlabcustody.bottle.lot_tracking | bottle lot tracking | RECORD | Lot number связывает бутылку, preservative, supplier и expiration. | Позволяет расследовать batch contamination. |
| wqlabcustody.bottle.kit_assembly | field kit assembly | METHOD | Kit собирают по site list, parameters, blanks, duplicates, labels, coolers и forms. | Уменьшает риск забытых бутылок в поле. |
| wqlabcustody.bottle.expiration_check | expiration check | QUALITY_CHECK | Проверяют срок preservatives, sterile containers и reagent packs. | Предотвращает invalid microbiology или chemistry samples. |
| wqlabcustody.field.sample_id | unique sample ID | RECORD | Sample ID должен быть уникальным и одинаковым на bottle, form и electronic record. | Это главный ключ всей custody chain. |
| wqlabcustody.field.label_durability | durable label | METHOD | Этикетка должна выдерживать воду, лед, abrasion и охлаждение. | Сохраняет идентичность пробы до login. |
| wqlabcustody.field.time_record | collection time record | RECORD | Время отбора фиксируют с timezone и preferably 24-hour format. | Нужно для holding time и storm-event interpretation. |
| wqlabcustody.field.collector_initials | collector initials | RECORD | Инициалы отборщика связывают sample с trained person. | Упрощает clarification при field anomalies. |
| wqlabcustody.field.cooler_seal | cooler seal | SAFETY_RULE | Cooler seal показывает, вскрывался ли контейнер после field custody. | Полезно для regulatory или disputed samples. |
| wqlabcustody.field.field_coc_form | field COC form | RECORD | Chain-of-custody form фиксирует samples, preservatives, requested analyses, relinquish и receive. | Делает передачу проб проверяемой. |
| wqlabcustody.preservation.cooling | cooling preservation | METHOD | Многие пробы держат охлажденными, но не замороженными, если method не требует freeze. | Сохраняет chemistry и microbiology в допустимом режиме. |
| wqlabcustody.preservation.ph_check | preservation pH check | QUALITY_CHECK | Для acid/base preserved samples pH проверяют по method или lab policy. | Подтверждает, что preservation реально сработала. |
| wqlabcustody.preservation.headspace | headspace control | CONSTRAINT | VOC bottles обычно требуют zero headspace and intact septa. | Headspace может привести к потере volatile analytes. |
| wqlabcustody.preservation.holding_time | holding time | CONSTRAINT | Holding time отсчитывается от collection до extraction или analysis. | Нарушение срока должно быть flagged или rejected. |
| wqlabcustody.preservation.light_protect | light protection | METHOD | Photosensitive analytes защищают amber glass, foil или dark storage. | Свет может разрушить analyte до анализа. |
| wqlabcustody.transport.cooler_temp | cooler temperature | MEASUREMENT | Температуру cooler измеряют при receiving и иногда с trip blank/logger. | Подтверждает, что транспорт не испортил sample. |
| wqlabcustody.transport.trip_blank | trip blank | QUALITY_CHECK | Trip blank путешествует с bottles и выявляет contamination during transport. | Особенно важен для VOC и low-level analyses. |
| wqlabcustody.transport.delivery_window | delivery window | DECISION_RULE | Доставка планируется backward от shortest holding time. | Логистика подчиняется самому чувствительному analyte. |
| wqlabcustody.transport.exception_note | transport exception note | RECORD | Delays, broken ice, leaking bottles или missing seals записывают сразу. | Позволяет lab корректно flag results. |
| wqlabcustody.receiving.sample_receipt | sample receipt | METHOD | Receiving сверяет cooler, forms, bottle count, labels, temperature, preservation и condition. | Это gatekeeper качества до лабораторной работы. |
| wqlabcustody.receiving.nonconformance | receipt nonconformance | RECORD | Nonconformance фиксирует missing info, wrong bottle, broken container или exceeded holding time. | Делает проблему видимой клиенту и data reviewer. |
| wqlabcustody.receiving.client_notification | client notification | METHOD | Клиента уведомляют о критических отклонениях до анализа, если решение влияет на usability. | Предотвращает бессмысленные расходы и споры. |
| wqlabcustody.receiving.accept_reject | accept/reject decision | DECISION_RULE | Lab принимает, flags или rejects sample по method, permit и QA plan. | Сохраняет научную и юридическую пригодность данных. |
| wqlabcustody.login.lims_accession | LIMS accession | METHOD | Samples регистрируют в LIMS с project, sample IDs, tests, due dates и custody status. | Переводит физическую пробу в управляемую digital workflow. |
| wqlabcustody.login.test_code_map | test code mapping | QUALITY_CHECK | Requested analysis сопоставляют с правильными method codes и reporting limits. | Ошибка test code дает неправильный результат даже при хорошей пробе. |
| wqlabcustody.login.barcode | barcode label | METHOD | Lab barcode связывает бутылку, aliquot, extraction и instrument runs. | Снижает ручной ввод и sample mix-up. |
| wqlabcustody.login.project_qap | project QAP link | RECORD | Проект связывают с QAP, permit, detection limits, qualifiers и deliverable format. | Аналитика выполняется под нужные правила, а не generic template. |
| wqlabcustody.storage.location_control | storage location control | RECORD | Холодильник, shelf, bin и custody status фиксируются в LIMS или log. | Sample можно быстро найти без потери custody. |
| wqlabcustody.storage.temperature_log | storage temperature log | MEASUREMENT | Refrigerators и freezers имеют continuous или routine temperature logs. | Доказывает соблюдение preservation после receipt. |
| wqlabcustody.storage.hold_segmentation | hold segmentation | METHOD | Samples разделяют по microbiology, organics, metals, hazardous или legal hold. | Снижает contamination и access risk. |
| wqlabcustody.storage.expiry_queue | holding-time queue | METHOD | LIMS сортирует work by earliest holding-time deadline. | Предотвращает просрочку анализов. |
| wqlabcustody.transfer.internal_transfer | internal transfer | RECORD | Передача между receiving, prep, analyst и storage фиксирует person, time и item. | Custody сохраняется внутри лаборатории. |
| wqlabcustody.transfer.subcontract_lab | subcontract transfer | METHOD | External lab получает documented COC, sample condition, required methods и deliverable terms. | Сохраняет traceability за пределами основной lab. |
| wqlabcustody.transfer.aliquot_trace | aliquot traceability | RECORD | Aliquots наследуют parent sample ID, prep batch и container notes. | Позволяет связать result с исходной бутылкой. |
| wqlabcustody.transfer.disposal_release | disposal release | DECISION_RULE | Disposal разрешают после reporting, hold period, legal hold review и hazardous classification. | Избегает преждевременного уничтожения evidence. |
| wqlabcustody.qa.coc_audit | COC audit | QUALITY_CHECK | Audit проверяет completeness signatures, dates, sample IDs, conditions и LIMS match. | Находит weak links до внешней проверки. |
| wqlabcustody.qa.blank_review | blank review | QUALITY_CHECK | Field, trip, method и equipment blanks сравнивают с associated samples. | Выявляет contamination source. |
| wqlabcustody.qa.qualifier_codes | result qualifier codes | RECORD | Qualifiers отмечают estimated, rejected, detected below RL, holding-time issue или matrix interference. | Пользователь понимает ограничение результата. |
| wqlabcustody.qa.corrective_action | corrective action | METHOD | Повторяющиеся COC failures ведут к retraining, form redesign, courier changes или kit controls. | QA становится улучшением процесса, а не только замечанием. |
| wqlabcustody.reporting.edeliverable | electronic deliverable | RECORD | EDD должен совпадать с report, LIMS IDs, units, qualifiers и detection limits. | Упрощает upload в regulatory databases. |
| wqlabcustody.reporting.narrative | case narrative | RECORD | Narrative объясняет exceptions, QC results, nonconformances и data usability. | Делает отчет интерпретируемым, а не просто таблицей чисел. |
| wqlabcustody.reporting.coc_archive | COC archive | RECORD | Final report хранит копию COC, receipt records, qualifiers и approvals. | Поддерживает audit trail после закрытия проекта. |
