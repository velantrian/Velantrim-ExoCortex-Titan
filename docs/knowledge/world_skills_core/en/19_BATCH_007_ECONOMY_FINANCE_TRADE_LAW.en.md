# 💰 Batch 007 — Economy, Finance, International Trade & Law

**Язык:** русский  
**Статус:** 50K batch 007 / seed units / не L3 truth  
**Цель:** расширить practical-базу по экономике, финансам, учёту, международной торговле, праву, интеллектуальной собственности и compliance.

---

## 📦 Knowledge Units

| ID | Тип | Суть | Условия / границы | Связи |
|---|---|---|---|---|
| `econ.supply_demand_equilibrium` | MODEL | Рыночное равновесие возникает там, где спрос и предложение совпадают по цене/количеству. | Реальные рынки имеют задержки, регулирование, власть участников. | economics |
| `econ.price_elasticity_demand` | METRIC | Ценовая эластичность спроса показывает реакцию спроса на изменение цены. | Зависит от заменителей, времени, необходимости товара. | pricing |
| `econ.income_elasticity` | METRIC | Эластичность по доходу показывает реакцию спроса на изменение дохода. | Товары могут быть normal или inferior. | demand |
| `econ.market_equilibrium_shift` | MECHANISM | Изменение факторов спроса/предложения сдвигает равновесную цену и количество. | Нужно различать движение по кривой и сдвиг кривой. | economics |
| `econ.inflation_cpi` | METRIC | CPI-инфляция измеряет изменение стоимости корзины потребительских товаров. | Корзина и методика влияют на результат. | finance |
| `econ.interest_rate_time_value` | PRINCIPLE | Процентная ставка отражает стоимость денег во времени, риск и альтернативы. | Реальные ставки зависят от инфляции и риска. | finance |
| `econ.central_bank_policy_rate` | TOOL | Ключевая ставка влияет на кредитование, спрос, инфляцию и валюту. | Передача в экономику не мгновенная. | macro |
| `econ.exchange_rate` | PRICE | Валютный курс — цена одной валюты в другой. | Зависит от ставок, торговли, ожиданий, политики. | trade |
| `econ.productivity_labor` | METRIC | Производительность труда = output на работника или час. | Не учитывает качество и капитал без уточнения. | industry |
| `econ.economies_scale` | MECHANISM | Экономия на масштабе снижает средние издержки при росте выпуска. | Может перейти в diseconomies при сложности. | factory |
| `econ.marginal_cost` | METRIC | Предельная стоимость — затраты на выпуск ещё одной единицы. | Важна для pricing и production planning. | finance |
| `econ.fixed_variable_cost` | DISTINCTION | Fixed costs не меняются напрямую с выпуском; variable costs растут с выпуском. | На длинном горизонте многие fixed costs становятся изменяемыми. | accounting |
| `econ.break_even_quantity` | FORMULA | Точка безубыточности по количеству = fixed costs / contribution margin per unit. | Требует корректной маржи и стабильных допущений. | finance |
| `finance.accounting.balance_sheet` | REPORT | Баланс показывает активы, обязательства и капитал на дату. | Это snapshot, не поток. | accounting |
| `finance.accounting.income_statement` | REPORT | Отчёт о прибылях и убытках показывает доходы и расходы за период. | Бухгалтерская прибыль не равна cash flow. | accounting |
| `finance.accounting.cash_flow_statement` | REPORT | Cash flow statement показывает движение денег по операционной, инвестиционной, финансовой деятельности. | Критичен для выживания бизнеса. | finance |
| `finance.inventory_turnover` | METRIC | Оборачиваемость запасов показывает, как быстро запасы превращаются в продажи. | Слишком высокая может означать риск дефицита. | operations |
| `finance.accounts_receivable` | TERM | Дебиторская задолженность — деньги, которые должны компании клиенты. | Риск неплатежей влияет на cash. | finance |
| `finance.accounts_payable` | TERM | Кредиторская задолженность — деньги, которые компания должна поставщикам. | Может быть источником краткосрочного финансирования. | working_capital |
| `finance.gross_margin_ratio` | METRIC | Gross margin ratio = gross profit / revenue. | Сравнивать лучше внутри отрасли. | profitability |
| `finance.contribution_margin` | METRIC | Contribution margin = price - variable cost. | Используется для break-even и product economics. | unit_economics |
| `finance.npv` | METHOD | NPV дисконтирует будущие cash flows к текущей стоимости. | Зависит от discount rate и прогнозов. | investment |
| `finance.irr` | METHOD | IRR — ставка, при которой NPV проекта равна нулю. | Может вводить в заблуждение при нестандартных потоках. | investment |
| `finance.payback_period` | METHOD | Payback period показывает срок возврата вложений. | Игнорирует cash flows после окупаемости. | investment |
| `finance.debt_equity` | METRIC | Debt/equity показывает соотношение долга и капитала. | Нормы зависят от отрасли. | risk |
| `finance.liquidity_current_ratio` | METRIC | Current ratio = current assets / current liabilities. | Высокий показатель не всегда означает эффективность. | liquidity |
| `finance.tax.vat` | TAX | VAT/НДС взимается на добавленную стоимость по цепочке. | Ставки и правила зависят от страны. | tax |
| `finance.tax.customs_duty` | TAX | Таможенная пошлина начисляется при импорте/экспорте по правилам тарифа. | Зависит от HS code, происхождения, соглашений. | trade |
| `trade.import_export` | PROCESS | Импорт и экспорт перемещают товары через границы. | Требуют документов, customs, compliance. | trade |
| `trade.tariff` | POLICY | Тариф — налог на товар при пересечении границы. | Может защищать отрасль или повышать цены. | customs |
| `trade.quota` | POLICY | Квота ограничивает количество товара. | Может создавать дефицит и rent. | trade_policy |
| `trade.incoterms.exw` | RULE | EXW переносит много обязанностей на покупателя от точки продавца. | Нужно понимать местное экспортное оформление. | incoterms |
| `trade.incoterms.fob` | RULE | FOB обычно связывает риск с погрузкой на судно в порту отправления. | Применяется для морских перевозок. | incoterms |
| `trade.incoterms.cif` | RULE | CIF включает стоимость, страхование и фрахт до порта назначения. | Риск и расходы распределяются по правилам Incoterms. | trade |
| `trade.incoterms.dap` | RULE | DAP означает доставку до указанного места без импортной очистки. | Налоги/пошлины обычно на покупателе. | trade |
| `trade.customs_valuation` | METHOD | Таможенная стоимость определяет базу для пошлин и налогов. | Регулируется правилами и документами. | WTO |
| `trade.rules_origin` | RULE | Правила происхождения определяют страну происхождения товара. | Влияют на тарифы и преференции. | customs |
| `trade.hs_code` | CLASSIFICATION | HS code классифицирует товары для таможни и статистики. | Ошибка кода ведёт к штрафам/задержкам. | customs |
| `trade.bill_of_lading` | DOCUMENT | Коносамент подтверждает принятие груза к морской перевозке и условия. | Может быть документом title. | shipping |
| `trade.letter_of_credit` | FINANCE_TOOL | Аккредитив снижает риск оплаты/поставки через банк и документы. | Документы должны строго соответствовать условиям. | trade_finance |
| `trade.trade_credit_insurance` | RISK_TOOL | Страхование торгового кредита снижает риск неоплаты покупателем. | Не покрывает все риски. | finance |
| `trade.sanctions_screening` | COMPLIANCE | Санкционный screening проверяет контрагентов, товары, страны, банки. | Требует актуальных списков. | law |
| `trade.export_control` | COMPLIANCE | Экспортный контроль ограничивает товары/технологии двойного назначения. | Нарушения могут быть серьёзными. | international_law |
| `trade.currency_hedging` | RISK_TOOL | Валютное хеджирование снижает риск изменения курса. | Имеет стоимость и basis risk. | finance |
| `law.international.treaty` | LAW_SOURCE | Договор создаёт обязательства для государств-участников. | Применимость зависит от ратификации и оговорок. | international_law |
| `law.international.customary_law` | LAW_SOURCE | Обычное международное право возникает из практики государств и opinio juris. | Доказательство может быть сложным. | international_law |
| `law.international.sovereignty` | PRINCIPLE | Суверенитет означает верховную власть государства в пределах территории. | Ограничивается международными обязательствами. | law |
| `law.international.jurisdiction` | TERM | Юрисдикция определяет, кто имеет право применять закон или рассматривать спор. | Может быть территориальной, персональной, предметной. | law |
| `law.international.arbitration` | METHOD | Международный арбитраж решает споры вне национального суда по соглашению сторон. | Требует арбитражной оговорки/согласия. | trade |
| `law.contract.choice_of_law` | CLAUSE | Choice of law определяет применимое право к договору. | Не всегда отменяет mandatory rules. | contract |
| `law.dispute_settlement` | METHOD | Dispute settlement задаёт форум и процедуру разрешения спора. | Может быть суд, арбитраж, медиация. | law |
| `law.trade.wto_mfn` | PRINCIPLE | MFN требует не дискриминировать торговых партнёров сверх правил соглашений. | Есть исключения и преференциальные соглашения. | WTO |
| `law.trade.national_treatment` | PRINCIPLE | National treatment требует не ухудшать режим импортных товаров после ввоза по сравнению с местными. | Детали зависят от соглашения. | WTO |
| `law.trade.anti_dumping` | TOOL | Anti-dumping меры применяются против товара, продаваемого ниже нормальной стоимости при ущербе отрасли. | Требует расследования. | trade_law |
| `law.ip.patent` | IP_RIGHT | Патент защищает техническое изобретение на ограниченный срок. | Требуются новизна, inventive step, применимость. | WIPO |
| `law.ip.trademark` | IP_RIGHT | Товарный знак отличает товары/услуги одного предприятия от других. | Защита зависит от регистрации/использования. | WIPO |
| `law.ip.copyright` | IP_RIGHT | Copyright защищает форму выражения произведения. | Не защищает саму идею как таковую. | IP |
| `law.ip.trade_secret` | IP_RIGHT | Коммерческая тайна защищает ценную секретную информацию при мерах сохранения тайны. | Утечка может разрушить защиту. | business |
| `law.ip.geographic_indication` | IP_RIGHT | Географическое указание связывает продукт с местом и качеством/репутацией. | Правила различаются по юрисдикции. | trade |
| `law.labor.standard` | REGULATION | Трудовые стандарты регулируют условия труда, безопасность, оплату, часы. | Нормы зависят от страны и отрасли. | factory |
| `law.environmental_compliance` | REGULATION | Экологическое compliance требует соблюдения норм выбросов, отходов, воды и воздействия. | Нарушения ведут к штрафам и остановкам. | factory |
| `law.contract.force_majeure` | CLAUSE | Force majeure регулирует последствия непредотвратимых событий для исполнения договора. | Применимость зависит от текста договора и права. | contract |
| `law.contract.incoterms_risk_transfer` | RULE | Incoterms распределяют расходы и риск, но не заменяют договор купли-продажи полностью. | Нужна правильная версия Incoterms. | trade |
| `econ.externality_internalization` | POLICY | Internalization заставляет учитывать external costs/benefits в решении. | Методы: налоги, нормы, cap-and-trade. | policy |
| `econ.public_goods_free_rider` | FAILURE_MODE | Free-rider problem возникает, когда люди пользуются благом без оплаты. | Типично для public goods. | economics |

---

## 📊 Batch 007 summary

```text
new units: 65
main layers:
  economics
  accounting and finance
  investment metrics
  international trade
  customs / Incoterms / documents
  sanctions and export control
  international law
  intellectual property
```
