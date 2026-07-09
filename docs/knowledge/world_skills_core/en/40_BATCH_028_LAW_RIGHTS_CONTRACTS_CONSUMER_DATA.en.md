# ⚖️ Batch 028 — Law, Rights, Contracts, Consumer & Data Protection

**Язык:** русский  
**Статус:** 50K batch 028 / seed units / не L3 truth  
**Цель:** добавить практическое правовое мышление: права, договоры, потребители, данные, ответственность, доказательства и compliance. Это не юридическая консультация.

---

## 📦 Knowledge Units

| ID | Тип | Суть | Условия / границы | Связи |
|---|---|---|---|---|
| `lawcore.source.statute` | LAW_SOURCE | Закон/статут — письменный акт компетентного органа. | Иерархия актов зависит от страны. | law |
| `lawcore.source.regulation` | LAW_SOURCE | Regulation уточняет применение закона через правила органа власти. | Может быть оспорено или изменено. | governance |
| `lawcore.source.case_law` | LAW_SOURCE | Case law формируется судебными решениями. | Сила прецедента зависит от правовой системы. | courts |
| `lawcore.source.contract` | LAW_SOURCE | Договор создаёт обязательства между сторонами. | Не может законно отменять все mandatory rules. | contracts |
| `lawcore.jurisdiction.subject_matter` | CONSTRAINT | Предметная юрисдикция определяет, какой орган рассматривает тип дела. | Ошибка форума задерживает спор. | courts |
| `lawcore.jurisdiction.personal` | CONSTRAINT | Персональная юрисдикция связывает суд с участником спора. | Важна в cross-border делах. | law |
| `lawcore.rights.human_dignity` | PRINCIPLE | Достоинство человека часто лежит в основе правовых систем прав человека. | Конкретное содержание зависит от права. | rights |
| `lawcore.rights.due_process` | PRINCIPLE | Справедливая процедура требует уведомления, возможности защиты и независимого решения. | Формы различаются. | justice |
| `lawcore.rights.privacy` | RIGHT | Право на приватность защищает личную жизнь и данные. | Балансируется с безопасностью и законом. | data |
| `lawcore.rights.free_expression` | RIGHT | Свобода выражения защищает мнение и информацию. | Имеет ограничения: клевета, угрозы, incitement. | society |
| `lawcore.rights.property` | RIGHT | Право собственности регулирует владение, пользование и распоряжение вещью. | Ограничивается zoning, налогами, public interest. | property |
| `lawcore.rights.access_to_remedy` | PRINCIPLE | Право на средство защиты позволяет оспаривать нарушение. | Без доступной процедуры право слабеет. | courts |
| `lawcore.contract.offer` | ELEMENT | Offer — определённое предложение заключить договор. | Не вся реклама является offer. | contracts |
| `lawcore.contract.acceptance` | ELEMENT | Acceptance — согласие на условия offer. | Изменённый ответ может быть counteroffer. | contracts |
| `lawcore.contract.consideration` | ELEMENT | Consideration в common law — обмен ценностями между сторонами. | Не во всех системах требуется так же. | contracts |
| `lawcore.contract.capacity` | ELEMENT | Capacity означает способность стороны заключать договор. | Возраст и состояние могут ограничивать. | contracts |
| `lawcore.contract.legality` | ELEMENT | Договорная цель должна быть законной. | Незаконный предмет может сделать договор недействительным. | contracts |
| `lawcore.contract.material_terms` | DOCUMENT | Существенные условия определяют предмет, цену, сроки, стороны и обязанности. | Зависят от типа договора. | contracts |
| `lawcore.contract.breach` | EVENT | Breach — нарушение договорного обязательства. | Последствия зависят от materiality и условий. | disputes |
| `lawcore.contract.remedy.damages` | REMEDY | Damages компенсируют убытки от нарушения. | Нужно доказать causation и размер. | contracts |
| `lawcore.contract.remedy.specific_performance` | REMEDY | Specific performance требует исполнить обязанность, а не платить деньги. | Доступно не всегда. | courts |
| `lawcore.contract.limitation_liability` | CLAUSE | Ограничение ответственности заранее задаёт предел убытков. | Может быть недействительным при грубой вине/законе. | contracts |
| `lawcore.contract.indemnity` | CLAUSE | Indemnity переносит определённые потери одной стороны на другую. | Текст должен быть точным. | contracts |
| `lawcore.contract.warranty` | CLAUSE | Warranty обещает качество, состояние или соответствие. | Нарушение даёт remedies. | consumer |
| `lawcore.contract.termination` | CLAUSE | Termination clause задаёт условия прекращения договора. | Нужно соблюдать notice и procedure. | contracts |
| `lawcore.contract.notice` | CLAUSE | Notice clause определяет, как юридически сообщать важные уведомления. | Неверный канал может быть спорным. | contracts |
| `lawcore.consumer.warranty` | RIGHT | Потребительские гарантии защищают от дефектного товара или услуги. | Права зависят от юрисдикции. | consumer |
| `lawcore.consumer.cooling_off` | RIGHT | Cooling-off period позволяет отказаться от некоторых дистанционных/домашних сделок. | Не применяется ко всему. | consumer |
| `lawcore.consumer.unfair_terms` | RISK | Несправедливые условия могут быть недействительными против потребителя. | Оценка зависит от закона. | consumer |
| `lawcore.consumer.product_safety` | REGULATION | Product safety требует, чтобы товары не создавали неприемлемый риск. | Требует стандартов, recall, маркировки. | safety |
| `lawcore.consumer.recall` | PROCESS | Recall убирает опасный или дефектный товар с рынка. | Нужна traceability и коммуникация. | product |
| `lawcore.liability.negligence` | TORT | Negligence — вред от нарушения duty of care. | Нужно доказать duty, breach, causation, damage. | tort |
| `lawcore.liability.strict` | TORT | Strict liability может наступать без доказательства вины. | Обычно для опасных продуктов/деятельности. | tort |
| `lawcore.liability.vicarious` | TORT | Vicarious liability переносит ответственность за действия другого в определённой связи. | Часто работодатель/работник. | labor |
| `lawcore.evidence.burden_of_proof` | PRINCIPLE | Burden of proof показывает, кто должен доказать claim. | Стандарт различается по делу. | courts |
| `lawcore.evidence.standard_civil` | STANDARD | В гражданских делах часто нужен баланс вероятностей/преобладание доказательств. | Формулировки различаются. | evidence |
| `lawcore.evidence.standard_criminal` | STANDARD | В уголовных делах стандарт обычно выше, например beyond reasonable doubt. | Защищает от ошибочного наказания. | justice |
| `lawcore.evidence.document_authenticity` | QUALITY_CHECK | Подлинность документа требует проверки источника, подписи, метаданных, цепочки хранения. | Цифровые документы требуют forensic. | evidence |
| `lawcore.evidence.hearsay` | ISSUE | Hearsay — сообщение о чужих словах, используемое как доказательство. | Допустимость зависит от правил и исключений. | courts |
| `lawcore.data.personal_data` | TERM | Personal data — информация, относящаяся к идентифицируемому человеку. | Определение зависит от закона. | privacy |
| `lawcore.data.special_category` | RISK | Sensitive/special data требует повышенной защиты. | Здоровье, биометрия, убеждения часто входят. | privacy |
| `lawcore.data.consent` | LEGAL_BASIS | Consent должен быть информированным, свободным и конкретным. | Не всегда лучший legal basis. | privacy |
| `lawcore.data.purpose_limitation` | PRINCIPLE | Данные используют только для заявленных совместимых целей. | Новая цель требует проверки. | privacy |
| `lawcore.data.storage_limitation` | PRINCIPLE | Данные не хранят дольше необходимого. | Нужна retention policy. | governance |
| `lawcore.data.access_request` | RIGHT | Человек может иметь право получить копию своих данных. | Есть исключения и сроки. | privacy |
| `lawcore.data.deletion_request` | RIGHT | Право на удаление позволяет требовать стирания при условиях закона. | Не всегда применимо к архивам/обязательствам. | privacy |
| `lawcore.data.breach_notification` | PROCESS | Утечки данных могут требовать уведомления регулятора и людей. | Сроки и критерии зависят от закона. | cybersecurity |
| `lawcore.data.dpia` | METHOD | DPIA оценивает высокий риск обработки данных до запуска. | Особенно важно для AI и sensitive data. | privacy |
| `lawcore.ai.accountability` | PRINCIPLE | AI accountability требует объяснимых ролей, логов, контроля и ответственности. | Не решается одной моделью. | AI |
| `lawcore.ai.human_oversight` | SAFETY_RULE | Human oversight снижает риск автоматических решений без контроля. | Человек должен иметь реальную власть и информацию. | AI_governance |
| `lawcore.ai.bias_audit` | QUALITY_CHECK | Bias audit проверяет различия воздействия системы на группы. | Нужны данные и метрики fairness. | AI_ethics |
| `lawcore.ip.license` | DOCUMENT | Лицензия разрешает использовать IP на условиях. | Объём прав должен быть явно указан. | IP |
| `lawcore.ip.assignment` | DOCUMENT | Assignment передаёт право собственности на IP. | Часто требует письменной формы. | IP |
| `lawcore.ip.open_source_license` | LICENSE | Open-source license разрешает использование кода с условиями. | Copyleft и permissive лицензии отличаются. | software |
| `lawcore.ip.moral_rights` | RIGHT | Moral rights защищают связь автора с произведением и целостность. | В разных странах действуют по-разному. | copyright |
| `lawcore.labor.employment_contract` | DOCUMENT | Трудовой договор задаёт роль, оплату, время, обязанности и права. | Закон может иметь обязательные условия. | labor |
| `lawcore.labor.worker_classification` | RISK | Классификация worker/contractor влияет на налоги, права, ответственность. | Ошибки ведут к штрафам. | business |
| `lawcore.labor.work_time` | REGULATION | Рабочее время и отдых регулируются для здоровья и справедливости. | Исключения зависят от отрасли. | labor |
| `lawcore.labor.health_safety` | REGULATION | Работодатель обязан управлять рисками безопасности труда. | Требует assessments и training. | safety |
| `lawcore.labor.discrimination` | RISK | Дискриминация — неблагоприятное обращение по защищённому признаку. | Может быть прямой или косвенной. | rights |
| `lawcore.environment.polluter_pays` | PRINCIPLE | Polluter pays возлагает стоимость загрязнения на источник. | Реализация требует измерений и enforcement. | environment |
| `lawcore.environment.permit` | REGULATION | Экологическое разрешение задаёт лимиты выбросов, отходов или водопользования. | Нарушение может остановить производство. | industry |
| `lawcore.environment.eia_public_participation` | PROCESS | ОВОС часто включает общественное участие и раскрытие информации. | Качество зависит от реального доступа. | environment |
| `lawcore.dispute.mediation` | METHOD | Медиация помогает сторонам договориться через нейтрального посредника. | Не подходит при дисбалансе безопасности. | conflict |
| `lawcore.dispute.arbitration_clause` | CLAUSE | Arbitration clause заранее выбирает арбитраж вместо суда. | Может ограничить доступ к суду. | contracts |
| `lawcore.dispute.choice_forum` | CLAUSE | Forum clause выбирает место/орган спора. | В cross-border делах критично. | contracts |

---

## 📊 Batch 028 summary

```text
new units: 66
main layers:
  legal sources and rights
  contracts and remedies
  consumer, product, data and AI law
  labor, environment and disputes
```
