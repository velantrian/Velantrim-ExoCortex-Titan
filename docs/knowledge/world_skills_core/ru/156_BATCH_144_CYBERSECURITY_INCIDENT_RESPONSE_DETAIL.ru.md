# BATCH_144 — Cybersecurity Incident Response Operations Detail
# world_skills_core · source: world_skills_core:batch_144:cybersecurity_incident_response_detail
# KnowledgeUnits: 44
# ВНИМАНИЕ: защитные operational знания; без инструкций по атаке, обходу защиты или эксплуатации уязвимостей.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| cyir.prepare.ir_policy | Incident response policy | invariant | IR policy задает полномочия, область, роли, эскалацию и правила работы с инцидентами безопасности. | кто имеет право действовать |
| cyir.prepare.roles | Incident response roles | invariant | Роли IR разделяют triage, containment, evidence, communications, legal, IT operations и business ownership. | меньше путаницы в кризис |
| cyir.prepare.contact_tree | Incident contact tree | variant | Contact tree хранит актуальные контакты людей, команд, поставщиков и внешних служб для срочной связи. | не искать телефоны ночью |
| cyir.prepare.asset_inventory | Security asset inventory | invariant | Инвентаризация активов помогает понять, какие системы, учетные записи, данные и владельцы затронуты сигналом. | scope начинается с asset map |
| cyir.prepare.log_sources | Critical log sources | invariant | Критичные источники логов включают identity, endpoints, network, cloud, applications и security tools. | без логов расследование слепое |
| cyir.prepare.playbook | Incident playbook | variant | Playbook описывает типовой порядок действий для класса инцидентов, но должен адаптироваться к фактическому риску. | шаблон, не автопилот |
| cyir.prepare.tabletop_exercise | Tabletop exercise | variant | Tabletop exercise тренирует decision-making, коммуникации и эскалацию без реального отключения систем. | проверить готовность заранее |
| cyir.detect.alert_tuning | Alert tuning | variant | Настройка alerting снижает шум и повышает вероятность, что важный сигнал не потеряется среди ложных срабатываний. | качество detection |
| cyir.detect.siem_correlation | SIEM correlation | invariant | Корреляция событий связывает разные источники логов в единый подозрительный паттерн. | видеть цепочку, не точку |
| cyir.detect.endpoint_signal | Endpoint signal | invariant | Endpoint signal показывает подозрительное поведение устройства, процесса, учетной записи или файла в управляемой среде. | источник первичного triage |
| cyir.detect.network_indicator | Network indicator | invariant | Network indicator описывает необычные соединения, объемы, направления или протоколы, требующие проверки. | сетевой слой расследования |
| cyir.detect.user_report | User security report | invariant | Сообщение пользователя может быть первым признаком phishing, account compromise, data exposure или system misuse. | люди как sensor network |
| cyir.detect.severity_classification | Severity classification | invariant | Severity classification учитывает затронутые данные, критичность системы, распространение, законные сроки и business impact. | правильная эскалация |
| cyir.triage.event_vs_incident | Event versus incident | invariant | Не каждое событие безопасности является инцидентом; инцидент требует подтвержденного или вероятного ущерба правилам безопасности. | не перегружать IR |
| cyir.triage.scope_estimate | Incident scope estimate | invariant | Первичная оценка scope определяет затронутые активы, учетные записи, временной период и возможный путь распространения. | размер проблемы |
| cyir.triage.affected_accounts | Affected accounts | invariant | Список затронутых учетных записей помогает оценить доступ, привилегии, владельцев и возможные действия от их имени. | identity-first triage |
| cyir.triage.initial_timeline | Initial incident timeline | invariant | Первичная timeline фиксирует известные события по времени, источнику и степени уверенности. | не потерять последовательность |
| cyir.triage.business_impact | Business impact triage | variant | Business impact triage оценивает влияние инцидента на клиентов, операции, обязательства, репутацию и восстановление. | безопасность плюс бизнес |
| cyir.triage.false_positive | False positive handling | invariant | Ложное срабатывание должно закрываться с объяснением, доказательствами и возможной корректировкой правила detection. | учиться на шуме |
| cyir.containment.account_disable | Account disable containment | variant | Временное отключение учетной записи ограничивает риск, если есть признаки компрометации или злоупотребления. | быстрый identity barrier |
| cyir.containment.network_segmentation | Network segmentation containment | variant | Сегментация сети ограничивает движение между зонами, когда инцидент может распространяться по инфраструктуре. | локализовать ущерб |
| cyir.containment.host_isolation | Host isolation | variant | Изоляция хоста сохраняет устройство для анализа и ограничивает связи без немедленного уничтожения evidence. | containment с сохранением следов |
| cyir.containment.block_indicator | Indicator blocking | variant | Блокировка indicator of compromise снижает повторные обращения, но не доказывает устранение корневой причины. | временный барьер |
| cyir.containment.privileged_access_review | Privileged access review | invariant | Пересмотр привилегированного доступа выявляет чрезмерные права, активные сессии и учетные записи высокого риска. | закрыть самый опасный доступ |
| cyir.evidence.chain_of_custody | Digital chain of custody | invariant | Chain of custody фиксирует, кто, когда, где и как получил или передал цифровые доказательства. | доказательная дисциплина |
| cyir.evidence.log_retention | Incident log retention | invariant | Retention логов должен покрывать период расследования и регуляторные требования, иначе факты исчезают раньше анализа. | сохранить историю |
| cyir.evidence.disk_image_decision | Disk image decision | variant | Решение о создании образа диска зависит от критичности evidence, времени, доступных инструментов и влияния на сервис. | не всегда полный image |
| cyir.evidence.volatile_data | Volatile data capture | variant | Volatile data может исчезнуть при перезагрузке, поэтому решение о сборе принимают до разрушительных действий. | память и активные сессии |
| cyir.evidence.evidence_notes | Evidence notes | invariant | Заметки расследования должны отделять наблюдения, выводы, гипотезы, действия и источники. | меньше путаницы позже |
| cyir.communication.incident_bridge | Incident bridge | variant | Incident bridge создает управляемый канал координации с владельцем, фасилитатором, журналом решений и правилами доступа. | единая комната кризиса |
| cyir.communication.legal_notification | Legal notification check | invariant | Legal notification check определяет, нужны ли уведомления юристам, регуляторам, клиентам или страховщику. | сроки могут быть короткими |
| cyir.communication.customer_message | Customer incident message | variant | Сообщение клиентам должно быть точным, своевременным, не раскрывать лишнего и отделять подтвержденные факты от анализа. | доверие без спекуляций |
| cyir.communication.regulator_timer | Regulator timer | invariant | Регуляторные часы начинают считаться от конкретного события или обнаружения, заданного применимыми правилами. | контролировать deadlines |
| cyir.communication.executive_update | Executive incident update | invariant | Executive update переводит technical status в риск, impact, решения, нужные ресурсы и следующий checkpoint. | руководство принимает решения |
| cyir.recovery.clean_restore | Clean restore | invariant | Clean restore восстанавливает систему из доверенного источника после устранения причины, а не просто возвращает ее online. | не восстановить проблему |
| cyir.recovery.password_reset | Credential reset campaign | variant | Массовый reset credentials нужен, когда scope компрометации учетных данных не ограничен надежно. | identity recovery |
| cyir.recovery.patch_validation | Patch validation | invariant | Валидация патча подтверждает, что закрытая уязвимость действительно устранена в affected environment. | fix должен работать |
| cyir.recovery.monitoring_window | Post-incident monitoring window | invariant | Период усиленного мониторинга после recovery помогает увидеть повторные признаки и недоочищенные системы. | trust but verify |
| cyir.recovery.backup_integrity | Backup integrity check | invariant | Проверка backup integrity подтверждает, что резервные копии доступны, корректны и не содержат очевидного повреждения. | recovery зависит от backups |
| cyir.lessons.root_cause | Incident root cause | invariant | Root cause analysis ищет управляемую причину инцидента, а не только ближайший симптом. | исправить систему |
| cyir.lessons.corrective_actions | Corrective actions | invariant | Corrective actions должны иметь владельца, срок, критерий завершения и связь с найденным control gap. | урок превращается в работу |
| cyir.lessons.control_gap | Security control gap | invariant | Control gap показывает, какой барьер отсутствовал, не сработал или был неправильно настроен. | улучшение защиты |
| cyir.lessons.lessons_report | Lessons learned report | invariant | Lessons learned report фиксирует timeline, impact, решения, evidence limits, control gaps и agreed actions. | память организации |
| cyir.lessons.metrics_mttd_mttr | MTTD and MTTR metrics | variant | MTTD и MTTR измеряют скорость обнаружения и восстановления, но требуют контекста severity и качества данных. | метрики без самообмана |
