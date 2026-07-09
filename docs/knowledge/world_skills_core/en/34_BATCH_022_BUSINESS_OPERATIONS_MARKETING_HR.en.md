# 🏢 Batch 022 — Business, Operations, Marketing & HR

**Язык:** русский  
**Статус:** 50K batch 022 / seed units / не L3 truth  
**Цель:** добавить практическое знание о том, как создают, продают, обслуживают и управляют продуктами, компаниями, командами и клиентским опытом.

---

## 📦 Knowledge Units

| ID | Тип | Суть | Условия / границы | Связи |
|---|---|---|---|---|
| `business.value_proposition` | MODEL | Value proposition объясняет, какую проблему решает продукт и почему он ценен. | Не равен slogan. | product |
| `business.customer_segment` | MODEL | Customer segment группирует людей по потребности, поведению или контексту. | Сегмент должен быть достижимым. | marketing |
| `business.problem_solution_fit` | MODEL | Problem-solution fit показывает, что решение реально закрывает важную боль. | Не доказывает масштабируемый бизнес. | startup |
| `business.product_market_fit` | MODEL | Product-market fit означает устойчивый спрос на продукт в выбранном рынке. | Не имеет одной универсальной метрики. | startup |
| `business.minimum_viable_product` | METHOD | MVP проверяет ключевую гипотезу минимальным продуктом. | Не означает плохое качество. | product |
| `business.unit_economics` | MODEL | Unit economics оценивает доходы и затраты на единицу клиента/заказа/продукта. | Средние могут скрыть сегменты. | finance |
| `business.customer_acquisition_cost` | METRIC | CAC — стоимость привлечения клиента. | Должен сравниваться с LTV и margin. | marketing |
| `business.lifetime_value` | METRIC | LTV оценивает будущую ценность клиента. | Зависит от retention и assumptions. | finance |
| `business.churn_rate` | METRIC | Churn измеряет уход клиентов за период. | Нужно различать logo churn и revenue churn. | SaaS |
| `business.retention_cohort` | METRIC | Cohort retention показывает, как группы клиентов остаются со временем. | Сильнее средней retention. | analytics |
| `business.sales_funnel` | MODEL | Sales funnel описывает путь от lead до покупки. | Может быть нелинейным. | sales |
| `business.lead_qualification` | METHOD | Qualification оценивает, подходит ли потенциальный клиент. | Экономит время sales team. | sales |
| `business.crm` | SYSTEM | CRM хранит контакты, сделки, историю и задачи по клиентам. | Данные должны быть актуальными. | software |
| `business.pipeline_forecast` | METHOD | Forecast оценивает будущие продажи по стадиям и вероятностям. | Оптимизм и sandbagging искажают. | sales |
| `business.pricing.cost_plus` | METHOD | Cost-plus добавляет маржу к себестоимости. | Может игнорировать ценность для клиента. | pricing |
| `business.pricing.value_based` | METHOD | Value-based pricing опирается на ценность результата для клиента. | Требует понимания клиента и альтернатив. | pricing |
| `business.pricing.subscription` | MODEL | Subscription распределяет оплату во времени за доступ или сервис. | Требует retention и поддержки. | SaaS |
| `business.pricing.freight_landed_cost` | METHOD | Landed cost включает товар, доставку, пошлины, страховку, обработку. | Нужен для импортного pricing. | trade |
| `business.marketing.positioning` | METHOD | Positioning задаёт место продукта в голове клиента относительно альтернатив. | Должно соответствовать реальности. | marketing |
| `business.marketing.brand` | ASSET | Brand — устойчивые ассоциации, доверие и обещание продукта. | Не только логотип. | marketing |
| `business.marketing.channel` | SYSTEM | Marketing channel доставляет сообщение или продукт аудитории. | Канал должен соответствовать поведению сегмента. | marketing |
| `business.marketing.content` | METHOD | Content marketing создаёт полезный материал для привлечения и доверия. | Без полезности превращается в шум. | communication |
| `business.marketing.seo` | METHOD | SEO повышает видимость в поисковых системах через структуру, контент и authority. | Алгоритмы меняются. | web |
| `business.marketing.email` | CHANNEL | Email marketing работает через разрешённые рассылки и сегментацию. | Спам разрушает доверие. | marketing |
| `business.marketing.conversion_rate` | METRIC | Conversion rate показывает долю людей, совершивших целевое действие. | Нужен denominator и контекст. | analytics |
| `business.marketing.ab_test` | METHOD | A/B test сравнивает варианты на реальной аудитории. | Требует достаточного объёма и корректной метрики. | statistics |
| `business.customer_support.ticket` | SYSTEM | Ticket system отслеживает обращение клиента от регистрации до решения. | Категории и SLA важны. | support |
| `business.customer_support.sla` | CONTRACT | SLA задаёт ожидаемый уровень сервиса или времени реакции. | Нужны измеримые критерии. | operations |
| `business.customer_support.knowledge_base` | TOOL | Knowledge base помогает клиентам и поддержке находить ответы. | Должна обновляться после новых проблем. | documentation |
| `business.customer_success` | FUNCTION | Customer success помогает клиенту получить результат, чтобы снизить churn. | Не равен обычной техподдержке. | SaaS |
| `business.operations.process_map` | TOOL | Process map показывает шаги, роли, входы, выходы и узкие места. | Нужна реальная практика, не только идеальная схема. | operations |
| `business.operations.sop` | DOCUMENT | SOP стандартизирует повторяемую операцию. | Перегруженный SOP никто не читает. | quality |
| `business.operations.kpi` | METRIC | KPI измеряет важный результат или поведение процесса. | Плохой KPI искажает действия. | management |
| `business.operations.okr` | METHOD | OKR связывает цели и измеримые ключевые результаты. | Не должен быть списком всех задач. | management |
| `business.operations.capacity_planning` | METHOD | Capacity planning оценивает ресурсы под спрос. | Ошибки ведут к очередям или простоям. | operations |
| `business.operations.queue` | MODEL | Очередь возникает, когда спрос временно превышает обслуживание. | Вариативность важна так же, как средняя скорость. | systems |
| `business.operations.service_blueprint` | TOOL | Service blueprint показывает frontstage, backstage и support processes. | Полезен для услуг. | design |
| `business.operations.inventory_policy` | METHOD | Политика запасов задаёт уровень, пополнение и риск дефицита. | Зависит от спроса и lead time. | logistics |
| `business.operations.quality_cost` | MODEL | Cost of quality включает prevention, appraisal, internal и external failure. | Дешевле предотвращать, чем исправлять после клиента. | quality |
| `business.hr.job_description` | DOCUMENT | Job description описывает роль, задачи, требования и критерии. | Нечёткая роль создаёт конфликт. | HR |
| `business.hr.recruiting_funnel` | PROCESS | Recruiting funnel ведёт кандидата от sourcing до offer. | Bias может возникать на каждом шаге. | HR |
| `business.hr.structured_interview` | METHOD | Structured interview задаёт одинаковые вопросы и критерии. | Снижает субъективность. | HR |
| `business.hr.onboarding` | PROCESS | Onboarding вводит человека в роль, процессы, культуру и ожидания. | Первые недели критичны. | management |
| `business.hr.performance_review` | PROCESS | Performance review оценивает вклад и развитие. | Может быть вредным без ясных критериев. | HR |
| `business.hr.compensation_band` | SYSTEM | Compensation bands задают диапазоны оплаты по роли/уровню. | Помогают справедливости и бюджету. | finance |
| `business.hr.training_matrix` | TOOL | Training matrix показывает, кто обучен каким навыкам. | Важно для безопасности и замещения. | operations |
| `business.hr.shift_scheduling` | METHOD | Графики смен балансируют спрос, закон, отдых и навыки. | Ошибки ведут к усталости и дефициту персонала. | labor |
| `business.hr.workplace_safety` | SYSTEM | Безопасность труда управляет рисками места, процесса и поведения. | Требует reporting без страха. | safety |
| `business.hr.conflict_resolution` | METHOD | Разрешение конфликтов ищет факты, интересы и безопасный процесс. | Не все конфликты симметричны. | communication |
| `business.legal.entity` | STRUCTURE | Юридическое лицо отделяет бизнес от владельцев в правовом смысле. | Ответственность зависит от формы и закона. | law |
| `business.legal.contract_basics` | DOCUMENT | Контракт фиксирует стороны, предмет, цену, сроки, ответственность и споры. | Шаблон без контекста опасен. | law |
| `business.legal.nda` | DOCUMENT | NDA ограничивает раскрытие конфиденциальной информации. | Не защищает уже публичное. | IP |
| `business.legal.terms_of_service` | DOCUMENT | Terms of service задают правила использования продукта или сервиса. | Должны соответствовать закону и UX. | product |
| `business.legal.privacy_policy` | DOCUMENT | Privacy policy объясняет сбор, использование, хранение и права по данным. | Требует фактического соответствия процессам. | privacy |
| `business.compliance.kyc` | PROCESS | KYC проверяет клиента для снижения финансовых и правовых рисков. | Балансирует privacy и regulation. | finance |
| `business.compliance.aml` | SYSTEM | AML снижает риск отмывания денег через мониторинг и reporting. | Требует правил и анализа транзакций. | finance |
| `business.compliance.supplier_audit` | PROCESS | Supplier audit проверяет поставщика по качеству, правам, безопасности, экологии. | Аудит без corrective actions слаб. | supply_chain |
| `business.supply.vendor_selection` | METHOD | Выбор поставщика сравнивает цену, качество, сроки, риск и поддержку. | Самая низкая цена не всегда выгодна. | procurement |
| `business.supply.dual_sourcing` | RISK_TOOL | Dual sourcing снижает зависимость от одного поставщика. | Может снижать объёмные скидки. | resilience |
| `business.supply.contract_manufacturing` | MODEL | Contract manufacturing отдаёт производство внешней фабрике. | Требует контроля качества и IP. | manufacturing |
| `business.supply.quality_agreement` | DOCUMENT | Quality agreement распределяет обязанности по качеству между сторонами. | Особенно важно в regulated industries. | quality |
| `business.finance.burn_rate` | METRIC | Burn rate показывает скорость расходования денежных средств. | Важен для стартапов и runway. | finance |
| `business.finance.runway` | METRIC | Runway показывает, на сколько времени хватит денег при текущем burn. | Меняется с доходом и расходами. | startup |
| `business.finance.margin_stack` | MODEL | Margin stack показывает, как цена распадается на себестоимость, логистику, комиссии, налоги и прибыль. | Полезен для retail и marketplace. | finance |
| `business.strategy.swot` | TOOL | SWOT группирует strengths, weaknesses, opportunities и threats. | Часто поверхностен без данных. | strategy |
| `business.strategy.moat` | MODEL | Moat — устойчивое преимущество, защищающее бизнес. | Может исчезнуть с технологией или рынком. | strategy |
| `business.exit.sunset_product` | METHOD | Sunset product — планированное закрытие продукта с миграцией клиентов. | Требует коммуникации и поддержки. | product |

---

## 📊 Batch 022 summary

```text
new units: 67
main layers:
  product, marketing, sales and support
  operations, HR and compliance
  procurement, finance and strategy
```
