# 🛡️ Batch 035 — Security, Defense, Risk & Safety Systems

**Язык:** русский  
**Статус:** 50K batch 035 / seed units / не L3 truth  
**Цель:** добавить практическое понимание безопасности: физическая безопасность, threat modeling, emergency planning, industrial safety, information security and resilience. Не является инструкцией для вреда.

---

## 📦 Knowledge Units

| ID | Тип | Суть | Условия / границы | Связи |
|---|---|---|---|---|
| `security.threat` | СРОК | Threat — потенциальный источник вреда или нарушения. | Не вся threat становится incident. | риск |
| `security.vulnerability` | СРОК | Vulnerability — слабость, которую threat может использовать. | Может быть технической, физической, человеческой. | риск |
| `security.asset` | СРОК | Asset — то, что нужно защитить: люди, данные, имущество, функция. | Без asset inventory риск неясен. | риск |
| `security.impact` | МЕТРИЧЕСКИЕ | Impact — последствия события для людей, денег, операций, репутации. | Нужно оценивать в контексте. | риск |
| `security.likelihood` | МЕТРИЧЕСКИЕ | Likelihood — вероятность или правдоподобность события. | Трудно оценить для редких событий. | риск |
| `security.risk_matrix` | ИНСТРУМЕНТ | Risk matrix связывает likelihood и impact для приоритизации. | Может давать ложную точность. | риск |
| `security.risk_treatment` | МЕТОД | Риск можно снизить, принять, передать или избежать. | Выбор зависит от cost and values. | управление |
| `security.defense_in_depth` | ПРИНЦИП | Defense in depth использует несколько независимых уровней защиты. | Один слой может отказать. | безопасность |
| `security.least_privilege` | ПРИНЦИП | Минимальные права снижают ущерб от ошибки или компрометации. | Требует пересмотра доступов. | кибер |
| `security.separation_of_duties` | КОНТРОЛЬ | Разделение обязанностей мешает одному человеку выполнить fraud end-to-end. | Малые команды компенсируют мониторингом. | управление |
| `security.access_control.physical` | КОНТРОЛЬ | Физический доступ ограничивают замками, картами, зонами и журналами. | Tailgating остаётся риском. | средство |
| `security.perimeter` | КОНТРОЛЬ | Периметр задерживает, направляет и обнаруживает доступ. | Не должен создавать опасность эвакуации. | физический |
| `security.lighting` | КОНТРОЛЬ | Освещение повышает видимость и снижает часть рисков. | Слепящие зоны ухудшают безопасность. | средство |
| `security.cctv` | КОНТРОЛЬ | CCTV помогает наблюдать, расследовать и сдерживать. | Требует privacy rules and retention. | наблюдение |
| `security.alarm` | КОНТРОЛЬ | Сигнализация обнаруживает вторжение, пожар, газ или другие события. | False alarms reduce trust. | средство |
| `security.guard_force` | КОНТРОЛЬ | Охрана реагирует, наблюдает и управляет доступом. | Нужны правила, training, accountability. | физический |
| `security.visitor_management` | ПРОЦЕСС | Visitor management регистрирует гостей и ограничивает их доступ. | Важно для офисов, заводов, школ. | средство |
| `security.badge_policy` | КОНТРОЛЬ | Пропуск идентифицирует человека и его права доступа. | Потерянные badges нужно быстро отзывать. | доступ |
| `security.key_control` | ПРОЦЕСС | Key control учитывает выдачу, копии, возврат и замену ключей. | Потерянный мастер-ключ — высокий риск. | физический |
| `security.lock.grade` | КАЧЕСТВО | Замки различаются по стойкости, назначению и сертификации. | Дверь и рама тоже важны. | средство |
| `security.safe` | КОНТРОЛЬ | Сейф защищает ценности от кражи, пожара или доступа. | Класс и крепление важны. | физический |
| `security.document_classification` | СИСТЕМА | Классификация документов задаёт уровень доступа и обработки. | Слишком много секретности мешает работе. | информация |
| `security.clean_desk` | ПОЛИТИКА | Clean desk снижает риск утечки документов и устройств. | Работает только с удобным хранением. | офис |
| `security.shredding` | КОНТРОЛЬ | Уничтожение документов снижает риск восстановления информации. | Метод зависит от чувствительности. | информация |
| `security.social_engineering` | АТАКА | Social engineering использует доверие, срочность и авторитет. | Обучение и verification помогают. | кибер |
| `security.pretexting` | АТАКА | Pretexting создаёт ложный сценарий для получения доступа или данных. | Проверка личности критична. | безопасность |
| `security.insider_threat` | РИСК | Insider threat исходит от человека с легитимным доступом. | Может быть malicious or negligent. | управление |
| `security.background_check` | КОНТРОЛЬ | Проверка биографии снижает часть кадровых рисков. | Должна быть законной и пропорциональной. | HR |
| `security.workplace_violence_prevention` | БЕЗОПАСНОСТЬ_СИСТЕМА | Профилактика включает в себя отчетность, деэскалацию, окружающую среду и политику. | Требует деликатности и безопасности. | рабочее место |
| `security.event_crowd_management` | МЕТОД | Crowd management планирует потоки, выходы, барьеры и коммуникацию. | Плотность толпы критична. | события |
| `security.fire_life_safety` | СИСТЕМА | Безопасность жизнедеятельности определяют, эвакуацию, отсекание, подавление. | Требует обслуживания. | огонь |
| `security.hazmat.response` | ПРОЦЕСС | Hazmat response изолирует, идентифицирует и контролирует опасные вещества. | Требует trained responders. | чрезвычайная ситуация |
| `security.emergency.operations_center` | СИСТЕМА | EOC координирует информацию, решения и ресурсы в кризисе. | Не должен мешать полевому командованию. | катастрофа |
| `security.continuity.critical_functions` | МЕТОД | Continuity planning выделяет функции, которые нельзя потерять. | Не всё одинаково критично. | устойчивость |
| `security.continuity.rto_rpo` | МЕТРИЧЕСКИЕ | RTO — время восстановления; RPO — допустимая потеря данных. | Нужны для IT and operations. | устойчивость |
| `security.crisis.communication_tree` | ИНСТРУМЕНТ | Communication tree задаёт, кто кого уведомляет в crisis. | Должен тестироваться. | коммуникация |
| `security.drill` | МЕТОД | Учения проверяют планы до реальной аварии. | После drill нужен after-action review. | готовность |
| `security.after_action_review` | МЕТОД | AAR фиксирует, что ожидалось, что произошло, почему, что изменить. | Не должен быть поиском виноватых. | обучение |
| `security.supply_chain_risk` | РИСК | Поставщики могут приносить риск качества, санкций, кибератак, forced labor. | Нужна due diligence. | цепочка поставок |
| `security.counterfeit_parts` | РИСК | Поддельные компоненты могут отказать или быть небезопасными. | Traceability and testing reduce risk. | производство |
| `security.product_tamper_evidence` | КОНТРОЛЬ | Tamper-evident packaging показывает признаки вскрытия. | Не препятствует всем атакам. | продукт |
| `security.food_defense` | БЕЗОПАСНОСТЬ_СИСТЕМА | Food defense защищает пищевую цепочку от намеренного загрязнения. | Отличается от food safety. | еда |
| `security.infrastructure.critical` | ASSET_CLASS | Critical infrastructure включает системы, отказ которых сильно вредит обществу. | Списки зависят от страны. | устойчивость |
| `security.infrastructure.single_point_failure` | FAILURE_MODE | Single point of failure может остановить всю систему. | Нужно redundancy or mitigation. | системы |
| `security.infrastructure.interdependency` | МОДЕЛЬ | Инфраструктуры зависят друг от друга: power, water, telecom, transport. | Cascading failure risk. | системы |
| `security.infrastructure.cascading_failure` | FAILURE_MODE | Каскадный отказ распространяется через связи систем. | Малый старт может дать большой ущерб. | устойчивость |
| `security.cyber.zero_trust` | ПРИНЦИП | Zero trust не доверяет автоматически сети или устройству. | Требует identity, segmentation, monitoring. | кибер |
| `security.cyber.network_segmentation` | КОНТРОЛЬ | Сегментация ограничивает распространение атаки. | Нужны правила и monitoring. | кибер |
| `security.cyber.backup_immutable` | КОНТРОЛЬ | Immutable backup защищает копии от изменения ransomware. | Нужно проверять restore. | кибер |
| `security.cyber.security_logging` | КОНТРОЛЬ | Security logs помогают обнаруживать и расследовать события. | Без анализа logs мертвы. | кибер |
| `security.cyber.siem` | СИСТЕМА | SIEM собирает и коррелирует security events. | Качество зависит от sources and rules. | кибер |
| `security.cyber.vulnerability_management` | ПРОЦЕСС | Управление уязвимостями ищет, оценивает и закрывает weaknesses. | Patch priority зависит от exploitability. | кибер |
| `security.cyber.penetration_test` | КАЧЕСТВО_ПРОВЕРКА | Пентест на последнем этапе защиты через симуляцию контролируемой атаки. | Не заменяет continuous security. | кибер |
| `security.cyber.red_team` | МЕТОД | Red team проверяет организацию как реальный adversary. | Требует rules of engagement. | кибер |
| `security.cyber.blue_team` | ФУНКЦИЯ | Blue team защищает, обнаруживает и реагирует. | Нужны процессы и tooling. | кибер |
| `security.cyber.purple_team` | МЕТОД | Фиолетовая команда занимается обучением атаке и защите. | Цель — улучшение, не соревнование. | кибер |
| `security.intelligence.cycle` | МОДЕЛЬ | Цикл разведки включает направление, сбор, обработку, анализ, распространение. | Риск bias на каждом шаге. | анализ |
| `security.intelligence.osint` | МЕТОД | OSINT использует открытые источники для анализа. | Требует verification and ethics. | информация |
| `security.intelligence.source_reliability` | КАЧЕСТВО | Источник оценивают по надёжности и доступу к информации. | Даже надёжный источник ошибается. | доказательство |
| `security.intelligence.analytical_confidence` | МЕТРИЧЕСКИЕ | Analytical confidence показывает уверенность вывода. | Должна быть отделена от вероятности события. | анализ |
| `security.intelligence.competing_hypotheses` | МЕТОД | ACH сравнивает гипотезы по evidence for/against. | Помогает против confirmation bias. | рассуждение |
| `security.defense.deterrence` | МОДЕЛЬ | Deterrence снижает действие угрозы через риск наказания или отказа. | Требует credibility. | стратегия |
| `security.defense.resilience` | СТРАТЕГИЯ | Resilience снижает выгоду атаки через восстановление и устойчивость. | Дополняет prevention. | стратегия |
| `security.defense.escalation` | РИСК_МОДЕЛЬ | Escalation — рост конфликта по интенсивности или масштабу. | Misperception усиливает риск. | геополитика |
| `security.humanitarian.proportionality` | ПРИНЦИП | Proportionality требует соразмерности вреда и цели в high-risk contexts. | Юридически сложно и контекстно. | закон |

---

## 📊 Batch 035 summary

```text
new units: 65
main layers:
  physical and organizational security
  emergency, continuity and infrastructure resilience
  cyber defense and intelligence analysis
  defense concepts and safety governance
```
