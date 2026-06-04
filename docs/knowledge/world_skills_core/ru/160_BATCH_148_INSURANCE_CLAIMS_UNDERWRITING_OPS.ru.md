# BATCH_148 — Insurance Claims & Underwriting Operations
# world_skills_core · source: world_skills_core:batch_148:insurance_claims_underwriting_ops
# KnowledgeUnits: 44
# ВНИМАНИЕ: общеобразовательные операционные знания; не страховая, юридическая или финансовая консультация.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| insops.underwriting.application_intake | Insurance application intake | invariant | Intake заявки собирает данные заявителя, объекта риска, желаемого покрытия, истории и подтверждающих документов. | старт underwriting |
| insops.underwriting.risk_class | Risk class | invariant | Risk class группирует похожие риски по характеристикам, влияющим на вероятность и размер убытков. | тариф не одинаков для всех |
| insops.underwriting.exposure_basis | Exposure basis | invariant | Exposure basis определяет измеритель риска, например выручку, payroll, стоимость имущества, количество единиц или пробег. | база расчета премии |
| insops.underwriting.loss_history | Loss history | invariant | Loss history показывает прошлые claims, частоту, severity, причины и trend риска. | прошлое как сигнал |
| insops.underwriting.guidelines | Underwriting guidelines | invariant | Guidelines задают приемлемые риски, ограничения, referrals, required documents и authority levels. | согласованность решений |
| insops.underwriting.pricing_factor | Pricing factor | variant | Pricing factor корректирует премию по характеристикам риска, deductible, limits, geography или controls. | цена отражает профиль |
| insops.underwriting.policy_limit | Policy limit | invariant | Policy limit ограничивает максимальную выплату по coverage или событию согласно условиям договора. | граница ответственности |
| insops.underwriting.deductible | Deductible | invariant | Deductible оставляет часть убытка на страхователе и влияет на premium, behavior и claims frequency. | разделение риска |
| insops.underwriting.exclusions | Policy exclusions | invariant | Exclusions описывают события, причины или условия, которые не покрываются полисом. | читать не только coverage |
| insops.underwriting.reinsurance_referral | Reinsurance referral | variant | Referral в перестрахование нужен, когда риск, limit или aggregation превышают обычную underwriting authority. | capacity и риск концентрации |
| insops.claims.first_notice_loss | First notice of loss | invariant | FNOL фиксирует первое сообщение об убытке, дату, участника, событие, объект и первичные документы. | открыть claim правильно |
| insops.claims.claim_number | Claim number | invariant | Claim number связывает все документы, payments, notes, coverage review и communications по делу. | единая папка убытка |
| insops.claims.coverage_check | Coverage check | invariant | Coverage check сопоставляет событие с полисом, сроком, exclusions, limits, deductible и endorsements. | покрытие до выплаты |
| insops.claims.reserve_setting | Claim reserve | invariant | Reserve estimate отражает ожидаемую стоимость claim и обновляется при появлении новой информации. | финансовая дисциплина |
| insops.claims.adjuster_assignment | Adjuster assignment | variant | Назначение adjuster зависит от сложности, линии страхования, geography, authority и conflict checks. | правильный обработчик |
| insops.claims.claimant_contact | Claimant contact | invariant | Контакт с claimant устанавливает ожидания, документы, сроки, next steps и канал коммуникации. | меньше недоверия |
| insops.claims.fraud_indicator | Fraud indicator | variant | Fraud indicator — сигнал несоответствия или необычности, требующий проверки, но не доказывающий мошенничество. | осторожный triage |
| insops.claims.subrogation_flag | Subrogation flag | variant | Subrogation flag отмечает возможность взыскать часть выплаты с ответственной третьей стороны. | recovery после выплаты |
| insops.investigation.evidence_collection | Claim evidence collection | invariant | Evidence collection собирает фотографии, счета, контракты, statements, reports и proof of loss. | решение на фактах |
| insops.investigation.damage_assessment | Damage assessment | invariant | Damage assessment оценивает характер, размер, причину и repair scope заявленного убытка. | сколько и почему |
| insops.investigation.invoice_review | Invoice review | invariant | Invoice review проверяет связь счета с covered loss, разумность суммы, duplication и подтверждение работы. | не оплачивать лишнее |
| insops.investigation.liability_analysis | Liability analysis | variant | Liability analysis оценивает ответственность сторон, duty, breach, causation и применимые факты. | кто за что отвечает |
| insops.investigation.causation_review | Causation review | invariant | Causation review отделяет covered cause от excluded, pre-existing или unrelated damage. | причина решает coverage |
| insops.investigation.expert_report | Expert report | variant | Expert report нужен, когда причина, стоимость или технические обстоятельства требуют специализированного анализа. | внешний expertise |
| insops.investigation.recorded_statement | Recorded statement | variant | Recorded statement фиксирует слова участника claim при соблюдении правил consent, fairness и relevance. | точная версия событий |
| insops.investigation.field_inspection | Field inspection | variant | Field inspection дает прямое наблюдение объекта, повреждения, условий и несоответствий документам. | видеть своими глазами |
| insops.settlement.settlement_authority | Settlement authority | invariant | Settlement authority определяет, кто может одобрить выплату или соглашение в пределах суммы и условий. | контроль решений |
| insops.settlement.payment_approval | Claim payment approval | invariant | Payment approval проверяет coverage, reserve, payee, bank details, tax flags и authority до выплаты. | деньги под контролем |
| insops.settlement.salvage_recovery | Salvage recovery | variant | Salvage recovery возвращает стоимость остатков имущества после выплаты, если это применимо к claim. | уменьшить net loss |
| insops.settlement.denial_letter | Claim denial letter | invariant | Denial letter объясняет основание отказа, факты, условия полиса и доступные options for review. | прозрачный отказ |
| insops.settlement.partial_payment | Partial payment | variant | Partial payment закрывает подтвержденную часть claim, пока спорные элементы продолжают проверяться. | не задерживать все |
| insops.settlement.claim_closure | Claim closure | invariant | Closure claim подтверждает завершение выплат, документов, recoveries, notes и final status. | закрыть дело чисто |
| insops.settlement.recovery_reserve | Recovery reserve | variant | Recovery reserve оценивает вероятное поступление от subrogation, salvage или other recovery sources. | net claim view |
| insops.settlement.complaint_escalation | Complaint escalation | invariant | Escalation жалобы передает спор на уровень с authority, сроками и независимым review path. | управлять конфликтом |
| insops.operations.bordereau | Insurance bordereau | variant | Bordereau — структурированный отчет о полисах, premium, claims или exposures для партнера или перестраховщика. | пакетная отчетность |
| insops.operations.claim_triage_queue | Claim triage queue | invariant | Очередь triage сортирует claims по urgency, severity, coverage issue, customer impact и complexity. | не обрабатывать хаотично |
| insops.operations.catastrophe_event_code | Catastrophe event code | variant | CAT event code связывает множество claims с одним событием для reporting, reserves и operational surge. | массовые убытки |
| insops.operations.leakage_review | Claim leakage review | invariant | Leakage review ищет переплаты, задержки, missed recoveries, poor documentation и process defects. | улучшать loss cost |
| insops.operations.litigation_hold | Litigation hold | invariant | Litigation hold сохраняет документы и communications, если claim может перейти в судебный спор. | не уничтожить evidence |
| insops.operations.regulatory_reporting | Insurance regulatory reporting | invariant | Regulatory reporting требует точных данных по срокам, complaint handling, solvency, claims или market conduct. | compliance clock |
| insops.operations.renewal_signal | Renewal underwriting signal | variant | Claim patterns могут стать сигналом для renewal underwriting, risk improvement или изменения terms. | claims учат underwriting |
| insops.operations.broker_communication | Broker communication | variant | Коммуникация с брокером должна отделять coverage position, information request, settlement status и confidential details. | посредник без шума |
| insops.operations.audit_sampling | Claim audit sampling | invariant | Audit sampling выбирает дела для проверки по risk, amount, age, handler, line или random selection. | контроль качества |
| insops.operations.data_quality_check | Insurance data quality check | invariant | Data quality check ловит пустые поля, неверные codes, duplicate claims, inconsistent dates и outlier amounts. | аналитика начинается с данных |
