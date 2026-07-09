# 🛡️ Batch 035 — Security, Defense, Risk & Safety Systems

**Язык:** русский  
**Статус:** 50K batch 035 / seed units / не L3 truth  
**Цель:** добавить практическое понимание безопасности: физическая безопасность, threat modeling, emergency planning, industrial safety, information security and resilience. Не является инструкцией для вреда.

---

## 📦 Knowledge Units

| ID | Тип | Суть | Условия / границы | Связи |
|---|---|---|---|---|
| `security.threat` | TERM | Threat — потенциальный источник вреда или нарушения. | Не вся threat становится incident. | risk |
| `security.vulnerability` | TERM | Vulnerability — слабость, которую threat может использовать. | Может быть технической, физической, человеческой. | risk |
| `security.asset` | TERM | Asset — то, что нужно защитить: люди, данные, имущество, функция. | Без asset inventory риск неясен. | risk |
| `security.impact` | METRIC | Impact — последствия события для людей, денег, операций, репутации. | Нужно оценивать в контексте. | risk |
| `security.likelihood` | METRIC | Likelihood — вероятность или правдоподобность события. | Трудно оценить для редких событий. | risk |
| `security.risk_matrix` | TOOL | Risk matrix связывает likelihood и impact для приоритизации. | Может давать ложную точность. | risk |
| `security.risk_treatment` | METHOD | Риск можно снизить, принять, передать или избежать. | Выбор зависит от cost and values. | governance |
| `security.defense_in_depth` | PRINCIPLE | Defense in depth использует несколько независимых уровней защиты. | Один слой может отказать. | safety |
| `security.least_privilege` | PRINCIPLE | Минимальные права снижают ущерб от ошибки или компрометации. | Требует пересмотра доступов. | cyber |
| `security.separation_of_duties` | CONTROL | Разделение обязанностей мешает одному человеку выполнить fraud end-to-end. | Малые команды компенсируют мониторингом. | governance |
| `security.access_control.physical` | CONTROL | Физический доступ ограничивают замками, картами, зонами и журналами. | Tailgating остаётся риском. | facility |
| `security.perimeter` | CONTROL | Периметр задерживает, направляет и обнаруживает доступ. | Не должен создавать опасность эвакуации. | physical |
| `security.lighting` | CONTROL | Освещение повышает видимость и снижает часть рисков. | Слепящие зоны ухудшают безопасность. | facility |
| `security.cctv` | CONTROL | CCTV помогает наблюдать, расследовать и сдерживать. | Требует privacy rules and retention. | surveillance |
| `security.alarm` | CONTROL | Alarm detects intrusion, fire, gas or other events. | False alarms reduce trust. | facility |
| `security.guard_force` | CONTROL | Охрана реагирует, наблюдает и управляет доступом. | Нужны правила, training, accountability. | physical |
| `security.visitor_management` | PROCESS | Visitor management регистрирует гостей и ограничивает их доступ. | Важно для офисов, заводов, школ. | facility |
| `security.badge_policy` | CONTROL | Пропуск идентифицирует человека и его права доступа. | Потерянные badges нужно быстро отзывать. | access |
| `security.key_control` | PROCESS | Key control учитывает выдачу, копии, возврат и замену ключей. | Потерянный мастер-ключ — высокий риск. | physical |
| `security.lock.grade` | QUALITY | Замки различаются по стойкости, назначению и сертификации. | Дверь и рама тоже важны. | facility |
| `security.safe` | CONTROL | Сейф защищает ценности от кражи, пожара или доступа. | Класс и крепление важны. | physical |
| `security.document_classification` | SYSTEM | Классификация документов задаёт уровень доступа и обработки. | Слишком много секретности мешает работе. | information |
| `security.clean_desk` | POLICY | Clean desk снижает риск утечки документов и устройств. | Работает только с удобным хранением. | office |
| `security.shredding` | CONTROL | Уничтожение документов снижает риск восстановления информации. | Метод зависит от чувствительности. | information |
| `security.social_engineering` | ATTACK | Social engineering использует доверие, срочность и авторитет. | Обучение и verification помогают. | cyber |
| `security.pretexting` | ATTACK | Pretexting создаёт ложный сценарий для получения доступа или данных. | Проверка личности критична. | security |
| `security.insider_threat` | RISK | Insider threat исходит от человека с легитимным доступом. | Может быть malicious or negligent. | governance |
| `security.background_check` | CONTROL | Проверка биографии снижает часть кадровых рисков. | Должна быть законной и пропорциональной. | HR |
| `security.workplace_violence_prevention` | SAFETY_SYSTEM | Prevention включает reporting, de-escalation, environment and policy. | Требует деликатности и безопасности. | workplace |
| `security.event_crowd_management` | METHOD | Crowd management планирует потоки, выходы, барьеры и коммуникацию. | Плотность толпы критична. | events |
| `security.fire_life_safety` | SYSTEM | Life safety объединяет обнаружение, эвакуацию, compartmentation, suppression. | Требует обслуживания. | fire |
| `security.hazmat.response` | PROCESS | Hazmat response изолирует, идентифицирует и контролирует опасные вещества. | Требует trained responders. | emergency |
| `security.emergency.operations_center` | SYSTEM | EOC координирует информацию, решения и ресурсы в кризисе. | Не должен мешать полевому командованию. | disaster |
| `security.continuity.critical_functions` | METHOD | Continuity planning выделяет функции, которые нельзя потерять. | Не всё одинаково критично. | resilience |
| `security.continuity.rto_rpo` | METRIC | RTO — время восстановления; RPO — допустимая потеря данных. | Нужны для IT and operations. | resilience |
| `security.crisis.communication_tree` | TOOL | Communication tree задаёт, кто кого уведомляет в crisis. | Должен тестироваться. | communication |
| `security.drill` | METHOD | Учения проверяют планы до реальной аварии. | После drill нужен after-action review. | preparedness |
| `security.after_action_review` | METHOD | AAR фиксирует, что ожидалось, что произошло, почему, что изменить. | Не должен быть поиском виноватых. | learning |
| `security.supply_chain_risk` | RISK | Поставщики могут приносить риск качества, санкций, кибератак, forced labor. | Нужна due diligence. | supply_chain |
| `security.counterfeit_parts` | RISK | Поддельные компоненты могут отказать или быть небезопасными. | Traceability and testing reduce risk. | manufacturing |
| `security.product_tamper_evidence` | CONTROL | Tamper-evident packaging показывает признаки вскрытия. | Не препятствует всем атакам. | product |
| `security.food_defense` | SAFETY_SYSTEM | Food defense защищает пищевую цепочку от намеренного загрязнения. | Отличается от food safety. | food |
| `security.infrastructure.critical` | ASSET_CLASS | Critical infrastructure включает системы, отказ которых сильно вредит обществу. | Списки зависят от страны. | resilience |
| `security.infrastructure.single_point_failure` | FAILURE_MODE | Single point of failure может остановить всю систему. | Нужно redundancy or mitigation. | systems |
| `security.infrastructure.interdependency` | MODEL | Инфраструктуры зависят друг от друга: power, water, telecom, transport. | Cascading failure risk. | systems |
| `security.infrastructure.cascading_failure` | FAILURE_MODE | Каскадный отказ распространяется через связи систем. | Малый старт может дать большой ущерб. | resilience |
| `security.cyber.zero_trust` | PRINCIPLE | Zero trust не доверяет автоматически сети или устройству. | Требует identity, segmentation, monitoring. | cyber |
| `security.cyber.network_segmentation` | CONTROL | Сегментация ограничивает распространение атаки. | Нужны правила и monitoring. | cyber |
| `security.cyber.backup_immutable` | CONTROL | Immutable backup защищает копии от изменения ransomware. | Нужно проверять restore. | cyber |
| `security.cyber.security_logging` | CONTROL | Security logs помогают обнаруживать и расследовать события. | Без анализа logs мертвы. | cyber |
| `security.cyber.siem` | SYSTEM | SIEM собирает и коррелирует security events. | Качество зависит от sources and rules. | cyber |
| `security.cyber.vulnerability_management` | PROCESS | Управление уязвимостями ищет, оценивает и закрывает weaknesses. | Patch priority зависит от exploitability. | cyber |
| `security.cyber.penetration_test` | QUALITY_CHECK | Pentest проверяет защиту через controlled attack simulation. | Не заменяет continuous security. | cyber |
| `security.cyber.red_team` | METHOD | Red team проверяет организацию как реальный adversary. | Требует rules of engagement. | cyber |
| `security.cyber.blue_team` | FUNCTION | Blue team защищает, обнаруживает и реагирует. | Нужны процессы и tooling. | cyber |
| `security.cyber.purple_team` | METHOD | Purple team объединяет attack and defense learning. | Цель — улучшение, не соревнование. | cyber |
| `security.intelligence.cycle` | MODEL | Intelligence cycle включает direction, collection, processing, analysis, dissemination. | Риск bias на каждом шаге. | analysis |
| `security.intelligence.osint` | METHOD | OSINT использует открытые источники для анализа. | Требует verification and ethics. | information |
| `security.intelligence.source_reliability` | QUALITY | Источник оценивают по надёжности и доступу к информации. | Даже надёжный источник ошибается. | evidence |
| `security.intelligence.analytical_confidence` | METRIC | Analytical confidence показывает уверенность вывода. | Должна быть отделена от вероятности события. | analysis |
| `security.intelligence.competing_hypotheses` | METHOD | ACH сравнивает гипотезы по evidence for/against. | Помогает против confirmation bias. | reasoning |
| `security.defense.deterrence` | MODEL | Deterrence снижает действие угрозы через риск наказания или отказа. | Требует credibility. | strategy |
| `security.defense.resilience` | STRATEGY | Resilience снижает выгоду атаки через восстановление и устойчивость. | Дополняет prevention. | strategy |
| `security.defense.escalation` | RISK_MODEL | Escalation — рост конфликта по интенсивности или масштабу. | Misperception усиливает риск. | geopolitics |
| `security.humanitarian.proportionality` | PRINCIPLE | Proportionality требует соразмерности вреда и цели в high-risk contexts. | Юридически сложно и контекстно. | law |

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
