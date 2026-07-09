# 💰 Batch 034 — Finance, Accounting, Insurance & Taxes

**Язык:** русский  
**Статус:** 50K batch 034 / seed units / не L3 truth  
**Цель:** расширить финансовую грамотность: учёт, налоги, страхование, кредиты, инвестиции, риск, бюджетирование. Это не финансовая консультация.

---

## 📦 Knowledge Units

| ID | Тип | Суть | Условия / границы | Связи |
|---|---|---|---|---|
| `fincore.bookkeeping.double_entry` | СИСТЕМА | Двойная запись отражает каждую операцию как debit и credit. | Требует плана счетов. | бухгалтерский учет |
| `fincore.account.asset` | СРОК | Актив — ресурс, контролируемый организацией, от которого ожидают выгоду. | Оценка зависит от accounting standard. | бухгалтерский учет |
| `fincore.account.liability` | СРОК | Обязательство — текущая обязанность передать ресурсы. | Сроки важны для liquidity. | бухгалтерский учет |
| `fincore.account.equity` | СРОК | Equity — остаточная доля после активов минус обязательства. | Может отличаться от рыночной стоимости. | бухгалтерский учет |
| `fincore.account.revenue` | СРОК | Revenue — доход от основной деятельности или продажи. | Recognition зависит от правил. | бухгалтерский учет |
| `fincore.account.expense` | СРОК | Expense — затраты, уменьшающие прибыль периода. | Не все выплаты сразу expense. | бухгалтерский учет |
| `fincore.accrual_accounting` | ПРИНЦИП | Accrual accounting признаёт доходы и расходы при возникновении, не только при оплате. | Отличается от cash basis. | бухгалтерский учет |
| `fincore.cash_basis` | МЕТОД | Cash basis учитывает операции при движении денег. | Проще, но хуже показывает обязательства. | бухгалтерский учет |
| `fincore.revenue_recognition` | ПРАВИЛО | Revenue recognition определяет, когда доход считать заработанным. | Особенно сложно для подписок и проектов. | бухгалтерский учет |
| `fincore.matching_principle` | ПРИНЦИП | Matching связывает расходы с доходами, которые они создают. | Требует оценок и периодизации. | бухгалтерский учет |
| `fincore.depreciation.straight_line` | МЕТОД | Straight-line depreciation равномерно распределяет стоимость актива. | Не всегда отражает реальный износ. | бухгалтерский учет |
| `fincore.depreciation.accelerated` | МЕТОД | Accelerated depreciation быстрее списывает стоимость в начале срока. | Влияет на налоги и прибыль. | бухгалтерский учет |
| `fincore.amortization` | МЕТОД | Amortization распределяет стоимость нематериального актива или погашение кредита. | Контекст термина важен. | финансы |
| `fincore.impairment` | КАЧЕСТВО_ПРОВЕРКА | Impairment признаёт снижение recoverable value актива. | Требует тестов и assumptions. | бухгалтерский учет |
| `fincore.inventory.fifo` | МЕТОД | FIFO предполагает продажу старых запасов первыми. | Влияет на COGS and inventory value. | бухгалтерский учет |
| `fincore.inventory.lifo` | МЕТОД | LIFO предполагает продажу новых запасов первыми. | Разрешён не везде. | бухгалтерский учет |
| `fincore.inventory.weighted_average` | МЕТОД | Weighted average сглаживает стоимость запасов. | Полезно при смешанных партиях. | бухгалтерский учет |
| `fincore.receivables.allowance` | МЕТОД | Allowance учитывает ожидаемые неплатежи клиентов. | Требует оценки риска. | кредит |
| `fincore.payroll.gross_net` | РАЗЛИЧИЕ | Gross pay — начислено; net pay — к выплате после удержаний. | Удержания зависят от налогов и льгот. | заработная плата |
| `fincore.payroll.employer_cost` | МЕТРИЧЕСКИЕ | Стоимость работника для работодателя больше gross salary из-за налогов, льгот, overhead. | Важна для бюджета. | HR |
| `fincore.tax.income_tax_base` | СРОК | Tax base — сумма, к которой применяется налог. | Отличается от accounting profit. | налог |
| `fincore.tax.deduction` | СРОК | Deduction уменьшает taxable base при условиях закона. | Нужны документы. | налог |
| `fincore.tax.credit` | СРОК | Tax credit уменьшает сам налог, а не базу. | Правила зависят от страны. | налог |
| `fincore.tax.withholding` | ПРОЦЕСС | Withholding удерживает налог у источника выплаты. | Требует отчётности. | заработная плата |
| `fincore.tax.vat_input_output` | МЕХАНИЗМ | VAT платится с добавленной стоимости через input и output tax. | Cash-flow effect важен. | налог |
| `fincore.tax.transfer_pricing` | РИСК | Transfer pricing регулирует цены между связанными компаниями. | High compliance risk. | международный_налог |
| `fincore.tax.permanent_establishment` | КОНЦЕПЦИЯ | Permanent establishment может создать налоговое присутствие в другой стране. | Зависит от treaty and activity. | международный |
| `fincore.audit.materiality` | ПРИНЦИП | Materiality определяет, какие ошибки значимы для пользователей отчётности. | Не означает допустимость обмана. | аудит |
| `fincore.audit.internal_control` | СИСТЕМА | Internal controls снижают риск ошибок и мошенничества. | Не дают абсолютной гарантии. | управление |
| `fincore.audit.segregation_duties` | КОНТРОЛЬ | Разделение обязанностей снижает риск fraud by one person. | Малому бизнесу сложнее. | аудит |
| `fincore.audit.reconciliation` | МЕТОД | Сверка сравнивает два независимых источника данных. | Например bank statement vs ledger. | бухгалтерский учет |
| `fincore.credit.loan_principal` | СРОК | Principal — основная сумма долга. | От неё обычно считают проценты. | кредит |
| `fincore.credit.interest_compound` | МЕХАНИЗМ | Сложный процент начисляется на principal plus accumulated interest. | Время сильно влияет. | финансы |
| `fincore.credit.amortizing_loan` | МОДЕЛЬ | Amortizing loan погашает проценты и principal регулярными платежами. | В начале доля процентов выше. | кредит |
| `fincore.credit.apr` | МЕТРИЧЕСКИЕ | APR показывает годовую стоимость кредита с учётом некоторых fees. | Сравнение зависит от правил расчёта. | потребитель |
| `fincore.credit.collateral` | СРОК | Collateral — имущество, обеспечивающее долг. | Может быть изъято при default. | банковское дело |
| `fincore.credit.default` | СОБЫТИЕ | Default — невыполнение долговых обязательств. | Последствия: штрафы, суд, залог, рейтинг. | риск |
| `fincore.credit.rating` | МЕТРИЧЕСКИЕ | Credit rating оценивает риск невозврата долга. | Не является гарантией. | финансы |
| `fincore.insurance.risk_pooling` | МЕХАНИЗМ | Страхование объединяет риски многих людей/объектов. | Работает при оценимой вероятности. | страхование |
| `fincore.insurance.premium` | СРОК | Premium — плата за страховое покрытие. | Зависит от риска, лимитов, франшизы. | страхование |
| `fincore.insurance.deductible` | СРОК | Deductible — часть убытка, которую несёт страхователь. | Снижает premium and small claims. | страхование |
| `fincore.insurance.coverage_limit` | СРОК | Coverage limit ограничивает выплату по полису. | Недостаточный лимит оставляет risk gap. | страхование |
| `fincore.insurance.exclusion` | ПУНКТ | Exclusion описывает, что полис не покрывает. | Читать важнее рекламного обещания. | страхование |
| `fincore.insurance.claim` | ПРОЦЕСС | Claim — обращение за выплатой по страховому случаю. | Требует документов и оценки. | страхование |
| `fincore.insurance.underwriting` | ПРОЦЕСС | Underwriting оценивает риск до выдачи полиса или кредита. | Может быть regulated and biased. | риск |
| `fincore.investment.asset_allocation` | МЕТОД | Asset allocation распределяет капитал между классами активов. | Главный driver риска портфеля. | инвестирование |
| `fincore.investment.diversification` | ПРИНЦИП | Diversification снижает специфический риск через разные активы. | Не убирает systemic risk. | инвестирование |
| `fincore.investment.liquidity` | СВОЙСТВО | Liquidity показывает, насколько быстро актив можно продать без сильной потери цены. | Кризис снижает ликвидность. | рынки |
| `fincore.investment.volatility` | МЕТРИЧЕСКИЕ | Volatility измеряет изменчивость цены. | Не равна всем видам риска. | рынки |
| `fincore.investment.real_return` | МЕТРИЧЕСКИЕ | Real return учитывает инфляцию. | Важнее nominal return для покупательной способности. | экономика |
| `fincore.investment.compounding` | МЕХАНИЗМ | Реинвестированная прибыль может расти нелинейно с течением времени. | Fees and taxes reduce. | финансы |
| `fincore.investment.fee_drag` | РИСК | Комиссии уменьшают итоговую доходность. | Малые проценты важны на длинном сроке. | инвестирование |
| `fincore.investment.index_fund` | ПРОДУКТ_ТИП | Index fund пытается следовать индексу, а не выбирать активы вручную. | Tracking error and fees remain. | инвестирование |
| `fincore.investment.bond_duration` | МЕТРИЧЕСКИЕ | Duration показывает чувствительность bond price к процентным ставкам. | Не равна maturity. | фиксированный_доход |
| `fincore.investment.equity_share` | ОБЪЕКТ | Акция даёт долю владения компанией и claim на future profits. | Риск потери капитала. | рынки |
| `fincore.personal.budget_zero_based` | МЕТОД | Zero-based budget распределяет каждый доход по категориям. | Требует дисциплины и пересмотра. | персональные_финансы |
| `fincore.personal.cash_envelope` | МЕТОД | Envelope budgeting ограничивает расходы по категориям. | Может быть физическим или цифровым. | персональные_финансы |
| `fincore.personal.emergency_fund` | РИСК_ИНСТРУМЕНТ | Emergency fund покрывает непредвиденные расходы без дорогого долга. | Размер индивидуален. | семья |
| `fincore.personal.debt_snowball` | МЕТОД | Debt snowball гасит долги от малого к большому для мотивации. | Не всегда минимизирует проценты. | долг |
| `fincore.personal.debt_avalanche` | МЕТОД | Debt avalanche гасит сначала самый дорогой долг. | Математически часто дешевле. | долг |
| `fincore.personal.net_worth` | МЕТРИЧЕСКИЕ | Net worth = активы минус обязательства. | Не показывает cash-flow. | персональные_финансы |
| `fincore.fraud.invoice_fraud` | РИСК | Invoice fraud подменяет реквизиты или создаёт ложный счёт. | Нужны approval and callback controls. | безопасность |
| `fincore.fraud.ponzi` | РИСК | Ponzi scheme платит старым участникам деньгами новых. | Обещания стабильной высокой доходности — red flag. | потребитель |
| `fincore.fraud.identity_theft` | РИСК | Кража идентичности использует чужие данные для финансовых действий. | Нужны monitoring and recovery steps. | кибербезопасность |
| `fincore.reporting.dashboard` | ИНСТРУМЕНТ | Финансовый dashboard показывает ключевые метрики бизнеса. | Опасен без definitions and data quality. | аналитика |
| `fincore.scenario.stress_test` | МЕТОД | Stress test проверяет финансы при плохих сценариях. | Assumptions должны быть реалистично жёсткими. | риск |

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
