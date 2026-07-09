# 💰 Batch 034 — Finance, Accounting, Insurance & Taxes

**Язык:** русский  
**Статус:** 50K batch 034 / seed units / не L3 truth  
**Цель:** расширить финансовую грамотность: учёт, налоги, страхование, кредиты, инвестиции, риск, бюджетирование. Это не финансовая консультация.

---

## 📦 Knowledge Units

| ID | Тип | Суть | Условия / границы | Связи |
|---|---|---|---|---|
| `fincore.bookkeeping.double_entry` | SYSTEM | Двойная запись отражает каждую операцию как debit и credit. | Требует плана счетов. | accounting |
| `fincore.account.asset` | TERM | Актив — ресурс, контролируемый организацией, от которого ожидают выгоду. | Оценка зависит от accounting standard. | accounting |
| `fincore.account.liability` | TERM | Обязательство — текущая обязанность передать ресурсы. | Сроки важны для liquidity. | accounting |
| `fincore.account.equity` | TERM | Equity — остаточная доля после активов минус обязательства. | Может отличаться от рыночной стоимости. | accounting |
| `fincore.account.revenue` | TERM | Revenue — доход от основной деятельности или продажи. | Recognition зависит от правил. | accounting |
| `fincore.account.expense` | TERM | Expense — затраты, уменьшающие прибыль периода. | Не все выплаты сразу expense. | accounting |
| `fincore.accrual_accounting` | PRINCIPLE | Accrual accounting признаёт доходы и расходы при возникновении, не только при оплате. | Отличается от cash basis. | accounting |
| `fincore.cash_basis` | METHOD | Cash basis учитывает операции при движении денег. | Проще, но хуже показывает обязательства. | accounting |
| `fincore.revenue_recognition` | RULE | Revenue recognition определяет, когда доход считать заработанным. | Особенно сложно для подписок и проектов. | accounting |
| `fincore.matching_principle` | PRINCIPLE | Matching связывает расходы с доходами, которые они создают. | Требует оценок и периодизации. | accounting |
| `fincore.depreciation.straight_line` | METHOD | Straight-line depreciation равномерно распределяет стоимость актива. | Не всегда отражает реальный износ. | accounting |
| `fincore.depreciation.accelerated` | METHOD | Accelerated depreciation быстрее списывает стоимость в начале срока. | Влияет на налоги и прибыль. | accounting |
| `fincore.amortization` | METHOD | Amortization распределяет стоимость нематериального актива или погашение кредита. | Контекст термина важен. | finance |
| `fincore.impairment` | QUALITY_CHECK | Impairment признаёт снижение recoverable value актива. | Требует тестов и assumptions. | accounting |
| `fincore.inventory.fifo` | METHOD | FIFO предполагает продажу старых запасов первыми. | Влияет на COGS and inventory value. | accounting |
| `fincore.inventory.lifo` | METHOD | LIFO предполагает продажу новых запасов первыми. | Разрешён не везде. | accounting |
| `fincore.inventory.weighted_average` | METHOD | Weighted average сглаживает стоимость запасов. | Полезно при смешанных партиях. | accounting |
| `fincore.receivables.allowance` | METHOD | Allowance учитывает ожидаемые неплатежи клиентов. | Требует оценки риска. | credit |
| `fincore.payroll.gross_net` | DISTINCTION | Gross pay — начислено; net pay — к выплате после удержаний. | Удержания зависят от налогов и льгот. | payroll |
| `fincore.payroll.employer_cost` | METRIC | Стоимость работника для работодателя больше gross salary из-за налогов, льгот, overhead. | Важна для бюджета. | HR |
| `fincore.tax.income_tax_base` | TERM | Tax base — сумма, к которой применяется налог. | Отличается от accounting profit. | tax |
| `fincore.tax.deduction` | TERM | Deduction уменьшает taxable base при условиях закона. | Нужны документы. | tax |
| `fincore.tax.credit` | TERM | Tax credit уменьшает сам налог, а не базу. | Правила зависят от страны. | tax |
| `fincore.tax.withholding` | PROCESS | Withholding удерживает налог у источника выплаты. | Требует отчётности. | payroll |
| `fincore.tax.vat_input_output` | MECHANISM | VAT платится с добавленной стоимости через input и output tax. | Cash-flow effect важен. | tax |
| `fincore.tax.transfer_pricing` | RISK | Transfer pricing регулирует цены между связанными компаниями. | High compliance risk. | international_tax |
| `fincore.tax.permanent_establishment` | CONCEPT | Permanent establishment может создать налоговое присутствие в другой стране. | Зависит от treaty and activity. | international |
| `fincore.audit.materiality` | PRINCIPLE | Materiality определяет, какие ошибки значимы для пользователей отчётности. | Не означает допустимость обмана. | audit |
| `fincore.audit.internal_control` | SYSTEM | Internal controls снижают риск ошибок и мошенничества. | Не дают абсолютной гарантии. | governance |
| `fincore.audit.segregation_duties` | CONTROL | Разделение обязанностей снижает риск fraud by one person. | Малому бизнесу сложнее. | audit |
| `fincore.audit.reconciliation` | METHOD | Сверка сравнивает два независимых источника данных. | Например bank statement vs ledger. | accounting |
| `fincore.credit.loan_principal` | TERM | Principal — основная сумма долга. | От неё обычно считают проценты. | credit |
| `fincore.credit.interest_compound` | MECHANISM | Сложный процент начисляется на principal plus accumulated interest. | Время сильно влияет. | finance |
| `fincore.credit.amortizing_loan` | MODEL | Amortizing loan погашает проценты и principal регулярными платежами. | В начале доля процентов выше. | credit |
| `fincore.credit.apr` | METRIC | APR показывает годовую стоимость кредита с учётом некоторых fees. | Сравнение зависит от правил расчёта. | consumer |
| `fincore.credit.collateral` | TERM | Collateral — имущество, обеспечивающее долг. | Может быть изъято при default. | banking |
| `fincore.credit.default` | EVENT | Default — невыполнение долговых обязательств. | Последствия: штрафы, суд, залог, рейтинг. | risk |
| `fincore.credit.rating` | METRIC | Credit rating оценивает риск невозврата долга. | Не является гарантией. | finance |
| `fincore.insurance.risk_pooling` | MECHANISM | Страхование объединяет риски многих людей/объектов. | Работает при оценимой вероятности. | insurance |
| `fincore.insurance.premium` | TERM | Premium — плата за страховое покрытие. | Зависит от риска, лимитов, франшизы. | insurance |
| `fincore.insurance.deductible` | TERM | Deductible — часть убытка, которую несёт страхователь. | Снижает premium and small claims. | insurance |
| `fincore.insurance.coverage_limit` | TERM | Coverage limit ограничивает выплату по полису. | Недостаточный лимит оставляет risk gap. | insurance |
| `fincore.insurance.exclusion` | CLAUSE | Exclusion описывает, что полис не покрывает. | Читать важнее рекламного обещания. | insurance |
| `fincore.insurance.claim` | PROCESS | Claim — обращение за выплатой по страховому случаю. | Требует документов и оценки. | insurance |
| `fincore.insurance.underwriting` | PROCESS | Underwriting оценивает риск до выдачи полиса или кредита. | Может быть regulated and biased. | risk |
| `fincore.investment.asset_allocation` | METHOD | Asset allocation распределяет капитал между классами активов. | Главный driver риска портфеля. | investing |
| `fincore.investment.diversification` | PRINCIPLE | Diversification снижает специфический риск через разные активы. | Не убирает systemic risk. | investing |
| `fincore.investment.liquidity` | PROPERTY | Liquidity показывает, насколько быстро актив можно продать без сильной потери цены. | Кризис снижает ликвидность. | markets |
| `fincore.investment.volatility` | METRIC | Volatility измеряет изменчивость цены. | Не равна всем видам риска. | markets |
| `fincore.investment.real_return` | METRIC | Real return учитывает инфляцию. | Важнее nominal return для покупательной способности. | economics |
| `fincore.investment.compounding` | MECHANISM | Reinvested returns can grow nonlinearly over time. | Fees and taxes reduce. | finance |
| `fincore.investment.fee_drag` | RISK | Комиссии уменьшают итоговую доходность. | Малые проценты важны на длинном сроке. | investing |
| `fincore.investment.index_fund` | PRODUCT_TYPE | Index fund пытается следовать индексу, а не выбирать активы вручную. | Tracking error and fees remain. | investing |
| `fincore.investment.bond_duration` | METRIC | Duration показывает чувствительность bond price к процентным ставкам. | Не равна maturity. | fixed_income |
| `fincore.investment.equity_share` | ASSET | Акция даёт долю владения компанией и claim на future profits. | Риск потери капитала. | markets |
| `fincore.personal.budget_zero_based` | METHOD | Zero-based budget распределяет каждый доход по категориям. | Требует дисциплины и пересмотра. | personal_finance |
| `fincore.personal.cash_envelope` | METHOD | Envelope budgeting ограничивает расходы по категориям. | Может быть физическим или цифровым. | personal_finance |
| `fincore.personal.emergency_fund` | RISK_TOOL | Emergency fund покрывает непредвиденные расходы без дорогого долга. | Размер индивидуален. | household |
| `fincore.personal.debt_snowball` | METHOD | Debt snowball гасит долги от малого к большому для мотивации. | Не всегда минимизирует проценты. | debt |
| `fincore.personal.debt_avalanche` | METHOD | Debt avalanche гасит сначала самый дорогой долг. | Математически часто дешевле. | debt |
| `fincore.personal.net_worth` | METRIC | Net worth = активы минус обязательства. | Не показывает cash-flow. | personal_finance |
| `fincore.fraud.invoice_fraud` | RISK | Invoice fraud подменяет реквизиты или создаёт ложный счёт. | Нужны approval and callback controls. | security |
| `fincore.fraud.ponzi` | RISK | Ponzi scheme платит старым участникам деньгами новых. | Обещания стабильной высокой доходности — red flag. | consumer |
| `fincore.fraud.identity_theft` | RISK | Кража идентичности использует чужие данные для финансовых действий. | Нужны monitoring and recovery steps. | cybersecurity |
| `fincore.reporting.dashboard` | TOOL | Финансовый dashboard показывает ключевые метрики бизнеса. | Опасен без definitions and data quality. | analytics |
| `fincore.scenario.stress_test` | METHOD | Stress test проверяет финансы при плохих сценариях. | Assumptions должны быть реалистично жёсткими. | risk |

---

## 📊 Batch 034 summary

```text
new units: 66
main layers:
  accounting and audit
  taxes, credit and insurance
  investing and personal finance
  fraud and financial risk
```
