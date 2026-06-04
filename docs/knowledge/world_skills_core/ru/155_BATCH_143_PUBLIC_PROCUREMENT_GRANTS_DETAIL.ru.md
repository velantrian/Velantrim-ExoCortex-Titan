# BATCH_143 — Public Procurement & Grant Administration Detail
# world_skills_core · source: world_skills_core:batch_143:public_procurement_grants_detail
# KnowledgeUnits: 44
# ВНИМАНИЕ: общеобразовательная административная грамотность; не заменяет локальные законы, регламенты и условия конкретного конкурса.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| procgrant.planning.needs_assessment | Needs assessment | invariant | Оценка потребности объясняет, зачем закупка или грант нужны, какую проблему решают и какой результат должен быть получен. | не начинать с поставщика |
| procgrant.planning.market_analysis | Market analysis | invariant | Анализ рынка показывает доступные решения, поставщиков, цены, риски, сроки и ограничения конкуренции. | реалистичные требования |
| procgrant.planning.procurement_plan | Procurement plan | variant | План закупок связывает потребности, бюджет, метод закупки, сроки, ответственных и контрольные точки. | управление календарем |
| procgrant.planning.budget_availability | Budget availability | invariant | Проверка доступности бюджета подтверждает, что обязательства не создаются без финансового источника и лимита. | предотвратить unfunded purchase |
| procgrant.planning.procurement_method | Procurement method selection | variant | Выбор метода закупки зависит от стоимости, срочности, конкуренции, сложности предмета и нормативных порогов. | не применять один режим ко всему |
| procgrant.specification.functional_requirement | Functional requirement | invariant | Функциональное требование описывает, что результат должен делать, а не только каким товаром он должен быть. | меньше vendor lock-in |
| procgrant.specification.performance_requirement | Performance requirement | invariant | Performance requirement задает измеримый уровень качества, мощности, срока, доступности или результата. | проверяемая спецификация |
| procgrant.specification.brand_neutrality | Brand neutrality | invariant | Бренд-нейтральная спецификация избегает необоснованной привязки к марке, если эквиваленты могут удовлетворить потребность. | честная конкуренция |
| procgrant.specification.lot_strategy | Lot strategy | variant | Деление на лоты может расширить конкуренцию, но слишком мелкие или связанные лоты повышают координационные риски. | баланс доступа и управления |
| procgrant.tender.notice | Tender notice | invariant | Извещение о закупке сообщает предмет, сроки, требования, критерии и способ подачи предложений. | прозрачный старт процедуры |
| procgrant.tender.bidder_questions | Bidder questions | invariant | Вопросы участников фиксируют неясности документации и должны получать одинаково доступные ответы. | равная информация |
| procgrant.tender.addendum | Tender addendum | variant | Addendum официально меняет документацию, сроки или ответы и должен быть доступен всем участникам. | единая версия условий |
| procgrant.tender.submission_deadline | Submission deadline | invariant | Срок подачи заявок определяет момент, после которого новые предложения обычно не принимаются. | защита процедурной честности |
| procgrant.tender.bid_security | Bid security | variant | Обеспечение заявки снижает риск несерьезных предложений, но может ограничить участие малых поставщиков. | пропорциональность требования |
| procgrant.tender.responsiveness_check | Responsiveness check | invariant | Проверка соответствия заявки отделяет формально приемлемые предложения от тех, что не отвечают обязательным условиям. | не смешивать с scoring |
| procgrant.evaluation.criteria_matrix | Evaluation criteria matrix | invariant | Матрица критериев заранее связывает баллы, веса, доказательства и метод оценки. | меньше произвола |
| procgrant.evaluation.technical_score | Technical score | variant | Техническая оценка сравнивает качество предложения по установленным критериям, а не по личному вкусу комиссии. | обоснованное ранжирование |
| procgrant.evaluation.price_evaluation | Price evaluation | invariant | Ценовая оценка должна учитывать заданную формулу, валюту, налоги, скидки и сопоставимость предложений. | сравнивать одинаково |
| procgrant.evaluation.abnormally_low_bid | Abnormally low bid | variant | Аномально низкая цена требует объяснения, потому что может указывать на ошибку, демпинг или невыполнимый объем. | риск будущего срыва |
| procgrant.evaluation.conflict_of_interest | Conflict of interest declaration | invariant | Декларация конфликта интересов фиксирует связи оценщиков, заявителей и поставщиков, которые могут повлиять на решение. | доверие к процедуре |
| procgrant.evaluation.committee_minutes | Evaluation committee minutes | invariant | Протокол комиссии сохраняет ход оценки, решения, основания, голоса и особые мнения. | audit trail процедуры |
| procgrant.award.standstill_period | Standstill period | variant | Standstill period дает участникам время ознакомиться с решением до заключения договора. | окно для возражений |
| procgrant.award.debriefing | Bidder debriefing | variant | Debriefing объясняет участнику сильные и слабые стороны заявки без раскрытия защищенной информации конкурентов. | обучение рынка |
| procgrant.award.protest_window | Protest window | invariant | Окно обжалования ограничивает срок, когда участник может оспорить процедуру или решение. | процедурная определенность |
| procgrant.contract.kickoff | Contract kickoff | invariant | Kickoff договора согласует роли, календарь, deliverables, каналы связи, риски и правила приемки. | запуск без хаоса |
| procgrant.contract.performance_bond | Performance bond | variant | Обеспечение исполнения защищает заказчика от невыполнения обязательств, но увеличивает стоимость участия. | финансовый барьер и защита |
| procgrant.contract.change_order | Change order | invariant | Change order документирует изменение объема, цены, срока или условий до выполнения измененной работы. | контролировать scope creep |
| procgrant.contract.acceptance_certificate | Acceptance certificate | invariant | Акт приемки подтверждает, что поставка, услуга или этап проверены по согласованным критериям. | основание для оплаты |
| procgrant.contract.liquidated_damages | Liquidated damages | variant | Заранее определенные штрафы за задержку или невыполнение должны быть связаны с реальным риском и условиями договора. | стимул соблюдать сроки |
| procgrant.contract.final_payment | Final payment control | invariant | Финальный платеж обычно требует закрытия поставки, документов, гарантий, удержаний и нерешенных претензий. | не платить до закрытия |
| procgrant.grant.call_for_proposals | Call for proposals | invariant | Конкурс грантов описывает цели, допустимых заявителей, расходы, сроки, критерии и формат заявки. | правила для applicants |
| procgrant.grant.eligibility_criteria | Eligibility criteria | invariant | Eligibility criteria определяют, кто может получить грант и какие проекты допустимы. | отсечь неподходящие заявки |
| procgrant.grant.matching_funds | Matching funds | variant | Софинансирование требует, чтобы получатель внес часть ресурсов деньгами или допустимым вкладом. | разделение ответственности |
| procgrant.grant.workplan | Grant workplan | invariant | Workplan связывает задачи, сроки, ответственных, deliverables и показатели результата. | проект становится управляемым |
| procgrant.grant.output_indicator | Output indicator | invariant | Output indicator измеряет конкретный продукт или услугу проекта, а не общую красивую цель. | проверяемый результат |
| procgrant.grant.budget_line | Grant budget line | invariant | Бюджетная строка показывает категорию расхода, сумму, основание расчета и связь с активностью. | traceability расходов |
| procgrant.grant.allowable_cost | Allowable cost | invariant | Допустимый расход соответствует правилам гранта, периоду проекта, бюджету и цели финансирования. | не все полезное оплачиваемо |
| procgrant.grant.advance_payment | Advance payment | variant | Аванс ускоряет запуск проекта, но требует контроля остатков, отчетности и условий возврата. | cashflow получателя |
| procgrant.grant.reporting_period | Reporting period | invariant | Отчетный период задает интервал, за который получатель показывает расходы, прогресс и подтверждающие документы. | регулярный контроль |
| procgrant.grant.audit_trail | Grant audit trail | invariant | Audit trail гранта связывает заявку, договор, бюджет, платеж, счет, deliverable и отчет. | доказуемость использования средств |
| procgrant.compliance.debarment_check | Debarment check | invariant | Проверка исключенных поставщиков или получателей снижает риск работы с запрещенными или недобросовестными участниками. | compliance до award |
| procgrant.compliance.procurement_file | Procurement file | invariant | Закупочное дело хранит ключевые документы процедуры от планирования до закрытия договора. | один источник правды |
| procgrant.compliance.open_contracting_data | Open contracting data | variant | Открытые данные о закупках повышают прозрачность, если публикуются в понятной структуре и без защищенных секретов. | public accountability |
| procgrant.compliance.value_for_money | Value for money | invariant | Value for money оценивает не только минимальную цену, но и качество, риски, жизненный цикл и достижение цели. | экономность без слепоты |
