# BATCH_148 — Insurance Claims & Underwriting Operations
# world_skills_core · source: world_skills_core:batch_148:insurance_claims_underwriting_ops
# KnowledgeUnits: 44
# ВНИМАНИЕ: общеобразовательные операционные знания; не страховая, юридическая или финансовая консультация.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| insops.underwriting.application_intake | Прием заявок на страхование | invariant | Intake заявки собирает данные заявителя, объекта риска, желаемого покрытия, истории и подтверждающих документов. | начать андеррайтинг |
| insops.underwriting.risk_class | Класс риска | invariant | Risk class группирует похожие риски по характеристикам, влияющим на вероятность и размер убытков. | тариф не одинаков для всех |
| insops.underwriting.exposure_basis | Базис риска | invariant | Exposure basis определяет измеритель риска, например выручку, payroll, стоимость имущества, количество единиц или пробег. | база расчета премии |
| insops.underwriting.loss_history | История потерь | invariant | Loss history показывает прошлые claims, частоту, severity, причины и trend риска. | прошлое как сигнал |
| insops.underwriting.guidelines | Рекомендации по андеррайтингу | invariant | Руководящие принципы предусматривают приемлемые риски, ограничения, направления, необходимые документы и уровни полномочий. | согласованность решений |
| insops.underwriting.pricing_factor | Ценовой фактор | variant | Pricing factor корректирует премию по характеристикам риска, deductible, limits, geography или controls. | цена отражает профиль |
| insops.underwriting.policy_limit | Лимит политики | invariant | Policy limit ограничивает максимальную выплату по coverage или событию согласно условиям договора. | граница ответственности |
| insops.underwriting.deductible | Франшиза | invariant | Deductible оставляет часть убытка на страхователе и влияет на premium, behavior и claims frequency. | разделение риска |
| insops.underwriting.exclusions | Исключения из политики | invariant | Exclusions описывают события, причины или условия, которые не покрываются полисом. | читать не только coverage |
| insops.underwriting.reinsurance_referral | Направление в перестрахование | variant | Referral в перестрахование нужен, когда риск, limit или aggregation превышают обычную underwriting authority. | capacity и риск концентрации |
| insops.claims.first_notice_loss | Первое уведомление об утрате | invariant | FNOL фиксирует первое сообщение об убытке, дату, участника, событие, объект и первичные документы. | открыть claim правильно |
| insops.claims.claim_number | Номер претензии | invariant | Номер претензии связывает все документы, платежи, заметки, обзор покрытия и сообщения по делу. | единая папка убытка |
| insops.claims.coverage_check | Проверка покрытия | invariant | Проверка покрытия включает событие с полисом, сроком, исключениями, лимитами, франшизой и одобрениями. | покрытие до выплаты |
| insops.claims.reserve_setting | Претензионный резерв | invariant | Reserve estimate отражает ожидаемую стоимость claim и обновляется при появлении новой информации. | финансовая дисциплина |
| insops.claims.adjuster_assignment | Назначение наладчика | variant | Назначение adjuster зависит от сложности, линии страхования, geography, authority и conflict checks. | правильный обработчик |
| insops.claims.claimant_contact | Контактное лицо истца | invariant | Контакт с claimant устанавливает ожидания, документы, сроки, next steps и канал коммуникации. | меньше недоверия |
| insops.claims.fraud_indicator | Индикатор мошенничества | variant | Fraud indicator — сигнал несоответствия или необычности, требующий проверки, но не доказывающий мошенничество. | осторожный triage |
| insops.claims.subrogation_flag | Флаг суброгации | variant | Subrogation flag отмечает возможность взыскать часть выплаты с ответственной третьей стороны. | recovery после выплаты |
| insops.investigation.evidence_collection | Претензионный сбор доказательств | invariant | Сбор доказательств собирает фотографии, счета, контракты, заявления, отчеты и доказательства убытков. | решение на фактах |
| insops.investigation.damage_assessment | Оценка ущерба | invariant | Damage assessment оценивает характер, размер, причину и repair scope заявленного убытка. | сколько и почему |
| insops.investigation.invoice_review | Проверка счета | invariant | Invoice review проверяет связь счета с covered loss, разумность суммы, duplication и подтверждение работы. | не оплачивать лишнее |
| insops.investigation.liability_analysis | Анализ ответственности | variant | Liability analysis оценивает ответственность сторон, duty, breach, causation и применимые факты. | кто за что отвечает |
| insops.investigation.causation_review | Обзор причинно-следственной связи | invariant | Анализ причинно-следственной связи отделяет покрываемую причину от исключенного, ранее существовавшего или несвязанного ущерба. | причина решает coverage |
| insops.investigation.expert_report | Экспертный отчет | variant | Expert report нужен, когда причина, стоимость или технические обстоятельства требуют специализированного анализа. | внешняя экспертиза |
| insops.investigation.recorded_statement | Записанное заявление | variant | Recorded statement фиксирует слова участника claim при соблюдении правил consent, fairness и relevance. | точная версия событий |
| insops.investigation.field_inspection | Полевая проверка | variant | Field inspection дает прямое наблюдение объекта, повреждения, условий и несоответствий документам. | видеть своими глазами |
| insops.settlement.settlement_authority | Расчетный орган | invariant | Settlement authority определяет, кто может одобрить выплату или соглашение в пределах суммы и условий. | контроль решений |
| insops.settlement.payment_approval | Запросить одобрение платежа | invariant | Утверждение платежа после покрытия, резерв, получатель платежа, банковские реквизиты, налоговые флаги и полномочия до выплаты. | деньги под контролем |
| insops.settlement.salvage_recovery | Аварийное восстановление | variant | Salvage recovery возвращает стоимость остатков имущества после выплаты, если это применимо к claim. | уменьшить net loss |
| insops.settlement.denial_letter | Письмо об отказе в претензии | invariant | Denial letter объясняет основание отказа, факты, условия полиса и доступные options for review. | прозрачный отказ |
| insops.settlement.partial_payment | Частичная оплата | variant | Partial payment закрывает подтвержденную часть claim, пока спорные элементы продолжают проверяться. | не задерживать все |
| insops.settlement.claim_closure | Закрытие претензии | invariant | Closure claim подтверждает завершение выплат, документов, recoveries, notes и final status. | закрыть дело чисто |
| insops.settlement.recovery_reserve | Резерв восстановления | variant | Резерв восстановления оценивает вероятное возвращение за счет суброгации, спасения или других источников восстановления. | представление чистых претензий |
| insops.settlement.complaint_escalation | Эскалация жалоб | invariant | Escalation жалобы передает спор на уровень с authority, сроками и независимым review path. | управлять конфликтом |
| insops.operations.bordereau | Страхование бордеро | variant | Bordereau — структурированный отчет о полисах, premium, claims или exposures для партнера или перестраховщика. | пакетная отчетность |
| insops.operations.claim_triage_queue | Заявить очередь на сортировку | invariant | Очередная сортировка претензий сортирует по срочности, серьезности, проблеме покрытия, влиянию на клиента и сложности. | не обрабатывать хаотично |
| insops.operations.catastrophe_event_code | Код события катастрофы | variant | Код события CAT связывает множество претензий с одним событием для отчетности, резервов и увеличения производительности. | массовые убытки |
| insops.operations.leakage_review | Рассмотрение утечки претензий | invariant | При проверке утечек выявляются переплаты, задержки, пропущенные восстановления, плохая документация и дефекты процесса. | улучшать loss cost |
| insops.operations.litigation_hold | Судебное разбирательство | invariant | Litigation hold сохраняет документы и communications, если claim может перейти в судебный спор. | не уничтожить evidence |
| insops.operations.regulatory_reporting | Регулирующая отчетность по страхованию | invariant | Нормативная отчетность требует точных данных по срокам, рассмотрению жалоб, платежеспособности, претензиям или поведению на рынке. | часы соответствия |
| insops.operations.renewal_signal | Сигнал о продлении андеррайтинга | variant | Характер претензий может стать сигналом для продления андеррайтинга, улучшения рисков или изменения условий. | претензии учат андеррайтинг |
| insops.operations.broker_communication | Брокерское общение | variant | Коммуникация с брокером должна отделять позицию покрытия, запрос информации, статус расчета и конфиденциальные данные. | посредник без шума |
| insops.operations.audit_sampling | Выборочная проверка претензий | invariant | Аудиторская выборка выбирает дела для проверки по риску, сумме, возрасту, обработчику, линии или случайному выбору. | контроль качества |
| insops.operations.data_quality_check | Проверка качества страховых данных | invariant | Проверка качества данных ловит пустые поля, неверные коды, повторяющиеся заявки, несогласованные даты и нестандартные суммы. | аналитика начинается с данных |
