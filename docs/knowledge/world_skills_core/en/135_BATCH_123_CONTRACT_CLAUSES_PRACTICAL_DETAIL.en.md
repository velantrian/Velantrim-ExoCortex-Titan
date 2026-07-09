# BATCH_123 — Contract Clauses Practical Detail
# world_skills_core · source: world_skills_core:batch_123:contract_clauses_detail
# KnowledgeUnits: 44
# ВНИМАНИЕ: общеобразовательная правовая грамотность; не юридическая консультация и не замена локального права.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| lawdet.contract.definitions_clause | Definitions clause | invariant | Раздел определений в договоре задаёт точный смысл ключевых терминов, чтобы одинаковые слова читались одинаково во всех разделах. | снижает спорность текста |
| lawdet.contract.interpretation_rule | Interpretation clause | invariant | Оговорка о толковании указывает, как читать заголовки, единственное и множественное число, ссылки на законы и приложения. | уменьшает двусмысленность |
| lawdet.contract.precedence_order | Precedence order | invariant | Порядок приоритета документов определяет, какой текст главнее при конфликте договора, приложений, спецификаций и заказа. | предотвращает конфликт версий |
| lawdet.contract.scope_statement | Scope statement | invariant | Раздел scope описывает, какие товары, услуги, результаты и исключения входят в предмет договора. | фиксирует границы обязательств |
| lawdet.contract.deliverables_list | Deliverables list | invariant | Перечень deliverables связывает каждый результат с форматом, сроком, критерием приемки и ответственным лицом. | делает исполнение проверяемым |
| lawdet.contract.acceptance_criteria | Acceptance criteria | invariant | Критерии приемки описывают объективные условия, при которых результат считается принятым заказчиком. | снижает спор о качестве |
| lawdet.contract.deemed_acceptance | Deemed acceptance | variant | Оговорка о молчаливой приемке может считать результат принятым, если замечания не направлены в согласованный срок. | защищает от зависшей приемки |
| lawdet.contract.change_order | Change order | invariant | Change order фиксирует изменение объема, цены, срока или требований как отдельное согласованное изменение договора. | контролирует scope creep |
| lawdet.contract.variation_procedure | Variation procedure | invariant | Процедура изменений задаёт, кто вправе согласовывать поправки и в какой форме они становятся обязательными. | предотвращает неформальные изменения |
| lawdet.contract.notice_clause | Notice clause | invariant | Оговорка об уведомлениях указывает допустимые каналы, адреса, момент доставки и требования к форме сообщения. | делает сроки доказуемыми |
| lawdet.contract.time_is_of_essence | Time is of the essence | variant | Условие time is of the essence делает срок существенным условием, нарушение которого может давать усиленные последствия. | повышает важность сроков |
| lawdet.contract.extension_of_time | Extension of time | variant | Оговорка о продлении срока описывает события, доказательства и процедуру, позволяющие сдвинуть дату исполнения. | управляет задержками |
| lawdet.contract.liquidated_damages | Liquidated damages | variant | Liquidated damages заранее устанавливают сумму за конкретное нарушение, если такая сумма допустима применимым правом. | делает риск нарушения прогнозируемым |
| lawdet.contract.penalty_clause_limit | Penalty clause limit | variant | Штрафная оговорка может быть ограничена законом или судом, если она несоразмерна нарушению или запрещена юрисдикцией. | не путать штраф с компенсацией |
| lawdet.contract.liability_cap | Liability cap | variant | Limitation of liability ограничивает общий размер ответственности, но обычно имеет исключения для умысла, конфиденциальности или закона. | ограничивает финансовый риск |
| lawdet.contract.exclusion_indirect_loss | Indirect loss exclusion | variant | Исключение косвенных убытков пытается убрать ответственность за удаленные коммерческие потери вроде lost profit. | уточняет покрываемые потери |
| lawdet.contract.indemnity_clause | Indemnity clause | variant | Indemnity переносит на одну сторону обязанность защитить другую от определенных требований, потерь или расходов третьих лиц. | распределяет внешний риск |
| lawdet.contract.warranty_clause | Warranty clause | invariant | Гарантийная оговорка формулирует обещание о свойствах товара, услуги, полномочиях или соответствии требованиям. | задает основу претензий |
| lawdet.contract.disclaimer_clause | Disclaimer clause | variant | Disclaimer исключает или ограничивает подразумеваемые гарантии, если такое исключение допустимо применимым правом. | снижает ожидания сверх текста |
| lawdet.contract.representation_clause | Representation clause | invariant | Representation подтверждает факт на момент заключения договора и может повлечь последствия при ложности. | важна для due diligence |
| lawdet.contract.covenant_clause | Covenant clause | invariant | Covenant устанавливает обещание действовать или воздерживаться от действия в течение срока договора. | фиксирует поведение после подписания |
| lawdet.contract.condition_precedent | Condition precedent | invariant | Condition precedent делает возникновение обязанности зависимым от наступления заранее указанного события. | связывает обязательство с условием |
| lawdet.contract.condition_subsequent | Condition subsequent | variant | Condition subsequent прекращает или изменяет обязанность после наступления указанного события. | управляет выходом из обязательства |
| lawdet.contract.confidentiality_scope | Confidentiality scope | invariant | Оговорка о конфиденциальности должна описывать защищаемую информацию, исключения, срок и разрешенное раскрытие. | защищает коммерческие сведения |
| lawdet.contract.data_processing_clause | Data processing clause | variant | Оговорка обработки данных распределяет роли, цели, меры защиты, инструкции и ответственность за персональные данные. | поддерживает compliance |
| lawdet.contract.audit_rights | Audit rights | variant | Audit rights дают стороне право проверять записи, процессы или соответствие договорным требованиям в заданных границах. | делает контроль возможным |
| lawdet.contract.recordkeeping_clause | Recordkeeping clause | invariant | Оговорка о хранении записей задаёт, какие документы, сколько времени и в каком виде нужно сохранять. | поддерживает доказуемость |
| lawdet.contract.subcontracting_clause | Subcontracting clause | variant | Оговорка о субподряде определяет, можно ли привлекать третьих лиц и сохраняет ли основной исполнитель ответственность. | контролирует цепочку исполнения |
| lawdet.contract.assignment_clause | Assignment clause | variant | Assignment clause регулирует передачу прав или обязанностей по договору другому лицу. | предотвращает нежелательную замену стороны |
| lawdet.contract.third_party_beneficiary | Third-party beneficiary | variant | Оговорка о третьих лицах указывает, могут ли неучаствующие стороны получать права по договору. | ограничивает неожиданные требования |
| lawdet.contract.ip_ownership | IP ownership clause | invariant | Оговорка об интеллектуальной собственности определяет, кому принадлежат исходные материалы, новые результаты и производные работы. | предотвращает спор о правах |
| lawdet.contract.license_grant | License grant | invariant | Лицензионная оговорка задаёт объем использования, территорию, срок, исключительность, передачу и ограничения. | делает использование прав законным |
| lawdet.contract.open_source_compliance | Open-source compliance | variant | Оговорка open-source compliance требует соблюдать лицензии стороннего кода и раскрывать компоненты при необходимости. | снижает риск нарушения лицензий |
| lawdet.contract.non_solicitation | Non-solicitation clause | variant | Non-solicitation ограничивает переманивание сотрудников или клиентов, но допустимость зависит от юрисдикции и объема ограничения. | защищает отношения |
| lawdet.contract.non_compete_limit | Non-compete clause | variant | Non-compete ограничивает конкуренцию после договора, но часто требует узкого срока, территории и законного интереса. | высокий риск недействительности |
| lawdet.contract.force_majeure_notice | Force majeure notice | variant | Force majeure обычно требует своевременного уведомления, доказательства события и мер по снижению последствий. | не освобождает автоматически |
| lawdet.contract.hardship_clause | Hardship clause | variant | Hardship clause запускает пересмотр условий, когда исполнение стало чрезмерно обременительным, но не невозможным. | отличается от форс-мажора |
| lawdet.contract.termination_for_cause | Termination for cause | invariant | Termination for cause позволяет прекратить договор из-за существенного нарушения или другого указанного основания. | защищает от плохого исполнения |
| lawdet.contract.termination_for_convenience | Termination for convenience | variant | Termination for convenience позволяет выйти без нарушения, если соблюдены срок уведомления и компенсации. | дает управляемую гибкость |
| lawdet.contract.cure_period | Cure period | variant | Cure period даёт нарушившей стороне срок исправить нарушение до расторжения или санкций. | снижает резкость конфликта |
| lawdet.contract.survival_clause | Survival clause | invariant | Survival clause перечисляет положения, которые продолжают действовать после прекращения договора. | сохраняет важные обязанности |
| lawdet.contract.governing_law | Governing law | invariant | Governing law указывает право, по которому толкуется договор, но не всегда отменяет императивные нормы. | снижает неопределенность |
| lawdet.contract.dispute_resolution_tier | Dispute resolution tier | variant | Многоступенчатая оговорка споров может требовать переговоры, медиацию, арбитраж или суд в заданной последовательности. | структурирует конфликт |
| lawdet.contract.entire_agreement | Entire agreement | invariant | Entire agreement подтверждает, что письменный договор заменяет прежние переговоры и сторонние обещания по тому же предмету. | защищает от устных ожиданий |
