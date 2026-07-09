# BATCH_142 — Treasury, Cash & Liquidity Detail
# world_skills_core · source: world_skills_core:batch_142:treasury_cash_liquidity_detail
# KnowledgeUnits: 44
# ВНИМАНИЕ: общеобразовательные финансово-операционные знания; не инвестиционная рекомендация.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| treas.cash.cash_position | Daily cash position | invariant | Daily cash position показывает доступные деньги по счетам, валютам, ограничениям и ожидаемым движениям. | видеть ликвидность сегодня |
| treas.cash.bank_balance_vs_book | Bank balance versus book balance | invariant | Банковский остаток и учетный остаток могут отличаться из-за незавершенных платежей, комиссий, курсов и ошибок. | нужна сверка |
| treas.cash.bank_reconciliation | Bank reconciliation | invariant | Bank reconciliation объясняет различия между банковской выпиской и учетными записями. | контроль денег |
| treas.cash.cash_pooling | Cash pooling | variant | Cash pooling концентрирует остатки группы компаний физически или виртуально, чтобы снизить дефициты и лишние займы. | управление групповой ликвидностью |
| treas.cash.sweeping | Cash sweeping | variant | Sweeping автоматически переводит остатки между счетами по заданным правилам и порогам. | меньше ручных переводов |
| treas.cash.lockbox | Lockbox | variant | Lockbox ускоряет обработку входящих платежей через банк или сервис, который собирает и передает данные оплат. | ускорение cash application |
| treas.forecast.direct_cash_forecast | Direct cash forecast | invariant | Direct cash forecast строится из ожидаемых поступлений и выплат по дням или неделям. | краткосрочная ликвидность |
| treas.forecast.indirect_cash_forecast | Indirect cash forecast | variant | Indirect cash forecast выводит денежный поток из прибыли, оборотного капитала и корректировок. | среднесрочное планирование |
| treas.forecast.rolling_forecast | Rolling cash forecast | invariant | Rolling forecast регулярно продлевает горизонт прогноза и обновляет фактические отклонения. | не ждать конца месяца |
| treas.forecast.variance_analysis | Cash forecast variance | invariant | Анализ отклонений прогноза сравнивает ожидаемые и фактические потоки по причине, сумме и владельцу. | улучшать прогноз |
| treas.liquidity.minimum_cash_buffer | Minimum cash buffer | variant | Минимальный cash buffer задает запас денег под операционные сбои, задержки поступлений и неожиданные выплаты. | защита от кассового разрыва |
| treas.liquidity.liquidity_runway | Liquidity runway | invariant | Liquidity runway показывает, на сколько времени хватит денежных ресурсов при заданном burn rate или сценарии. | выживаемость организации |
| treas.liquidity.stress_scenario | Liquidity stress scenario | variant | Stress scenario проверяет ликвидность при задержке клиентов, росте ставок, валютном шоке, падении продаж или закрытии кредитной линии. | план до кризиса |
| treas.liquidity.committed_facility | Committed credit facility | invariant | Committed facility дает право заемщику получить финансирование в пределах условий, если соблюдены ковенанты и документы. | резервная ликвидность |
| treas.liquidity.uncommitted_facility | Uncommitted facility | variant | Uncommitted facility может быть отозвана или не предоставлена банком, поэтому слабее как резерв ликвидности. | не считать гарантией |
| treas.workingcapital.dso | Days sales outstanding | invariant | DSO показывает среднее время взыскания дебиторской задолженности в днях. | скорость превращения продаж в cash |
| treas.workingcapital.dpo | Days payable outstanding | invariant | DPO показывает среднее время оплаты поставщиков в днях. | управлять исходящим cash |
| treas.workingcapital.dio | Days inventory outstanding | invariant | DIO показывает среднее время, на которое деньги связаны в запасах. | inventory как cash |
| treas.workingcapital.cash_conversion_cycle | Cash conversion cycle | invariant | Cash conversion cycle связывает DIO, DSO и DPO, показывая время от вложения денег до возврата cash. | оборотный капитал |
| treas.receivables.aging_report | AR aging report | invariant | Aging дебиторки группирует неоплаченные счета по просрочке и помогает приоритизировать взыскание. | фокус collection |
| treas.receivables.credit_limit | Customer credit limit | variant | Кредитный лимит клиента ограничивает открытый риск по продажам с отсрочкой с учетом платежной истории и надежности. | не продавать без меры |
| treas.receivables.cash_application | Cash application | invariant | Cash application сопоставляет входящий платеж с клиентом, счетом, скидкой, спором или переплатой. | чистая дебиторка |
| treas.receivables.dispute_deduction | Customer deduction | variant | Deduction возникает, когда клиент платит меньше счета из-за скидки, претензии, возврата или ошибки. | отделить спор от неоплаты |
| treas.payables.payment_run | Payment run | invariant | Payment run группирует утвержденные счета к оплате по срокам, валюте, банку, приоритету и cash availability. | управляемые выплаты |
| treas.payables.early_payment_discount | Early payment discount | variant | Скидка за раннюю оплату имеет смысл, если экономия выше альтернативной стоимости денег и не вредит ликвидности. | сравнить с cash cost |
| treas.payables.payment_hold | Payment hold | variant | Payment hold временно блокирует оплату из-за спора, отсутствия документов, санкционного риска или cash constraint. | контроль исходящих денег |
| treas.payments.dual_approval | Dual approval payment | invariant | Двойное утверждение платежа снижает риск ошибки или мошенничества, разделяя создание и авторизацию платежа. | контроль платежей |
| treas.payments.beneficiary_validation | Beneficiary validation | invariant | Проверка получателя платежа подтверждает банковские реквизиты, владельца, изменение данных и риск подмены. | защита от fraud |
| treas.payments.payment_cutoff | Bank payment cutoff | invariant | Bank cutoff определяет, будет ли платеж обработан текущим банковским днем или перенесен. | планировать срочные платежи |
| treas.payments.sanctions_screening | Payment sanctions screening | variant | Sanctions screening проверяет контрагентов, банки и страны перед платежом, но требует настройки совпадений и эскалации. | compliance платежей |
| treas.fx.transaction_exposure | FX transaction exposure | invariant | Transaction exposure возникает, когда денежный поток в иностранной валюте изменяет стоимость из-за курса. | риск счетов и закупок |
| treas.fx.natural_hedge | Natural hedge | variant | Natural hedge снижает валютный риск, сопоставляя поступления и выплаты в одной валюте. | меньше деривативов |
| treas.fx.forward_contract | FX forward contract | variant | Валютный forward фиксирует курс будущей покупки или продажи валюты по договоренному сроку и сумме. | предсказуемость cash flow |
| treas.fx.hedge_ratio | Hedge ratio | variant | Hedge ratio показывает долю валютной позиции, покрытую хеджем, и должен соответствовать политике риска. | не хеджировать наугад |
| treas.debt.covenant | Debt covenant | invariant | Ковенант займа задает финансовое или операционное условие, нарушение которого может вызвать последствия по договору. | контроль обязательств |
| treas.debt.interest_rate_risk | Interest rate risk | invariant | Риск процентной ставки влияет на стоимость долга или доходность размещений при изменении рыночных ставок. | фиксированная или плавающая ставка |
| treas.debt.maturity_ladder | Debt maturity ladder | invariant | Maturity ladder показывает график погашений долга и помогает увидеть концентрацию рефинансирования. | не попасть в стену долга |
| treas.investment.short_term_policy | Short-term investment policy | variant | Политика краткосрочных размещений обычно задает безопасность, ликвидность, доходность, лимиты и допустимые инструменты. | cash не должен исчезнуть |
| treas.investment.counterparty_limit | Counterparty limit | invariant | Лимит контрагента ограничивает сумму риска на один банк, брокера или эмитента. | не зависеть от одного |
| treas.risk.fraud_red_flag | Treasury fraud red flag | variant | Red flags платежного fraud включают срочность, смену реквизитов, необычного получателя, обход процедур и давление на сотрудника. | остановить до перевода |
| treas.risk.seg_duties | Treasury segregation duties | invariant | Разделение обязанностей в treasury отделяет создание платежа, утверждение, сверку и администрирование банковских прав. | защита от злоупотреблений |
| treas.reporting.treasury_dashboard | Treasury dashboard | invariant | Treasury dashboard показывает cash, forecast, debt, FX, ковенанты, лимиты и ключевые исключения. | управление одним экраном |
| treas.reporting.bank_fee_analysis | Bank fee analysis | variant | Анализ банковских комиссий сравнивает тарифы, объемы операций, ошибки начислений и возможности оптимизации. | снизить расходы |
| treas.policy.treasury_policy | Treasury policy | invariant | Treasury policy задает полномочия, лимиты, инструменты, отчетность, контроль и эскалацию финансовых рисков. | правила до кризиса |
