# BATCH_130 — Evidence, Records & Procedure Detail
# world_skills_core · source: world_skills_core:batch_130:evidence_records_procedure_detail
# KnowledgeUnits: 44
# ВНИМАНИЕ: общая грамотность по доказуемости и записям; не юридическая консультация.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| evidrec.record.authenticity | Record authenticity | invariant | Аутентичность записи означает, что запись действительно происходит из заявленного источника и не была подменена. | доверие к документу |
| evidrec.record.integrity | Record integrity | invariant | Целостность записи означает, что содержание осталось полным и неизмененным с контролируемого момента. | защита от незаметной правки |
| evidrec.record.provenance | Record provenance | invariant | Provenance описывает происхождение записи, историю владения, изменения и контекст создания. | понять откуда данные |
| evidrec.record.metadata | Record metadata | invariant | Метаданные записи описывают автора, время, формат, устройство, версию или контекст, не являясь основным содержанием. | часто важны для проверки |
| evidrec.record.version_history | Version history | invariant | История версий показывает последовательность изменений документа и помогает восстановить, какая редакция действовала в момент события. | контроль договоров и процедур |
| evidrec.record.retention_schedule | Retention schedule | invariant | График хранения записей задаёт тип записи, срок хранения, основание и способ уничтожения или архивации. | не хранить хаотично |
| evidrec.record.legal_hold | Legal hold | variant | Legal hold приостанавливает обычное уничтожение потенциально релевантных записей из-за спора, проверки или расследования. | сохранить доказательства |
| evidrec.record.disposition_log | Disposition log | invariant | Журнал уничтожения записей фиксирует, что именно уничтожено, когда, кем и по какому правилу хранения. | доказуемое удаление |
| evidrec.record.access_log | Access log | invariant | Журнал доступа показывает, кто, когда и к какому ресурсу обращался или пытался обратиться. | расследование действий |
| evidrec.record.audit_trail | Audit trail | invariant | Audit trail связывает события системы в последовательность, позволяющую проверить действия пользователей и изменения данных. | трассируемость процесса |
| evidrec.evidence.chain_of_custody | Chain of custody | invariant | Chain of custody документирует передачу объекта или записи между хранителями с временем, состоянием и ответственным лицом. | защита от спора о подмене |
| evidrec.evidence.tamper_evident | Tamper-evident control | variant | Tamper-evident контроль не предотвращает доступ полностью, но делает попытку вскрытия или изменения заметной. | пломбы и контроль целостности |
| evidrec.evidence.hash_value | Cryptographic hash value | invariant | Криптографический hash фиксирует цифровой отпечаток файла, который меняется при изменении содержимого. | проверка цифровой целостности |
| evidrec.evidence.timestamping | Trusted timestamping | variant | Доверенная метка времени связывает данные с моментом существования через независимый или защищенный механизм. | доказать существование на дату |
| evidrec.evidence.digital_signature | Digital signature | invariant | Цифровая подпись подтверждает связь подписанта с данными и выявляет последующее изменение подписанного содержимого. | электронное подтверждение |
| evidrec.evidence.original_vs_copy | Original and copy distinction | invariant | Различение оригинала и копии важно, потому что копия может потерять контекст, метаданные или признаки подлинности. | качество доказательства |
| evidrec.evidence.contemporaneous_note | Contemporaneous note | invariant | Запись, созданная близко ко времени события, обычно лучше сохраняет детали и меньше зависит от поздней памяти. | ценность быстрых заметок |
| evidrec.evidence.hearsay_risk | Hearsay risk | variant | Пересказ чужих слов несёт риск ошибки источника, памяти и контекста даже до вопроса о его допустимости. | отделять прямое наблюдение |
| evidrec.evidence.corroboration | Evidence corroboration | invariant | Corroboration усиливает утверждение через независимое подтверждение другим источником, методом или записью. | не опираться на один сигнал |
| evidrec.evidence.contradiction_log | Contradiction log | invariant | Журнал противоречий фиксирует несовместимые сведения, источники, дату обнаружения и статус разрешения. | не прятать конфликт фактов |
| evidrec.procedure.standard_form | Standard form | variant | Стандартная форма уменьшает пропуски данных, если поля соответствуют реальному процессу и понятны пользователю. | качество ввода |
| evidrec.procedure.required_field | Required field | variant | Обязательное поле полезно только тогда, когда пользователь реально может предоставить достоверное значение в момент заполнения. | избегать мусорных ответов |
| evidrec.procedure.approval_matrix | Approval matrix | invariant | Матрица согласования связывает тип решения, сумму, риск или область с нужным уровнем утверждения. | прозрачная ответственность |
| evidrec.procedure.delegation_authority | Delegation of authority | invariant | Делегирование полномочий определяет, кто может подписывать, утверждать или принимать решения вместо основного ответственного. | предотвращает недействительные действия |
| evidrec.procedure.segregation_duties | Segregation of duties | invariant | Разделение обязанностей не дает одному человеку одновременно инициировать, утверждать и скрыто контролировать критическую операцию. | защита от ошибок и злоупотреблений |
| evidrec.procedure.exception_register | Exception register | invariant | Реестр исключений фиксирует отклонения от правил, причину, утверждение, срок и последующее закрытие. | исключение не становится нормой |
| evidrec.procedure.corrective_action | Corrective action | invariant | Corrective action устраняет причину обнаруженного несоответствия, а не только исправляет отдельный симптом. | предотвращение повторов |
| evidrec.procedure.preventive_action | Preventive action | invariant | Preventive action снижает риск потенциальной проблемы до ее фактического возникновения. | работа до отказа |
| evidrec.procedure.escalation_path | Escalation path | invariant | Путь эскалации задаёт, кому передавать вопрос, если уровень риска, срок или полномочия превышают обычные рамки. | не застревать на исполнителе |
| evidrec.procedure.deadline_rule | Deadline rule | variant | Правило сроков должно указывать момент начала отсчета, календарные или рабочие дни, часовой пояс и последствия пропуска. | снижает спор о дедлайне |
| evidrec.procedure.notice_receipt | Notice receipt proof | invariant | Доказательство получения уведомления связывает содержание, адресата, канал, дату отправки и дату доставки. | сроки становятся проверяемыми |
| evidrec.procedure.meeting_minutes | Meeting minutes evidence | invariant | Протокол встречи должен отделять решения, обсуждения, поручения, сроки и открытые вопросы. | не смешивать разговор и решение |
| evidrec.procedure.action_owner | Action owner | invariant | У каждого действия должен быть один ответственный владелец, даже если исполнителей несколько. | убрать размытую ответственность |
| evidrec.procedure.raci_matrix | RACI matrix | variant | RACI различает ответственного исполнителя, утверждающего, консультируемых и информируемых участников процесса. | ясность ролей |
| evidrec.procedure.sop_revision | SOP revision control | invariant | Контроль редакций SOP показывает действующую версию, дату вступления, автора изменения и причину пересмотра. | не работать по старой процедуре |
| evidrec.procedure.training_record | Training record | invariant | Запись об обучении связывает сотрудника, процедуру, дату, формат проверки и подтверждение компетентности. | доказать готовность выполнять работу |
| evidrec.procedure.competency_check | Competency check | variant | Проверка компетентности подтверждает не только факт обучения, но и способность выполнить задачу с нужным качеством. | не путать attendance и skill |
| evidrec.procedure.nonconformity_report | Nonconformity report | invariant | Отчет о несоответствии описывает требование, фактическое отклонение, доказательство, масштаб и временное сдерживание. | структурировать проблему |
| evidrec.procedure.containment_action | Containment action | invariant | Containment action временно ограничивает ущерб от несоответствия до нахождения и устранения коренной причины. | защита клиентов и процесса |
| evidrec.procedure.effectiveness_check | Effectiveness check | invariant | Проверка эффективности подтверждает, что corrective action действительно снизил или устранил повторение проблемы. | закрывать CAPA по результату |
| evidrec.procedure.document_control | Document control | invariant | Document control управляет созданием, пересмотром, утверждением, распространением и изъятием контролируемых документов. | единая версия правды |
| evidrec.procedure.form_obsolescence | Obsolete form control | variant | Устаревшие формы должны быть изъяты или явно помечены, чтобы пользователи не создавали записи по старым правилам. | защита от старых шаблонов |
| evidrec.procedure.data_quality_rule | Data quality rule | invariant | Правило качества данных описывает допустимые значения, формат, источник, владельца и проверку поля. | машинная проверяемость |
| evidrec.procedure.master_data_owner | Master data owner | invariant | Владелец мастер-данных отвечает за определение, качество, изменение и разрешение конфликтов ключевого справочника. | управляемые справочники |
