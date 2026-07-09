# 💻 Batch 017 — Computing, Data, AI & Communications

**Язык:** русский  
**Статус:** 50K batch 017 / seed units / не L3 truth  
**Цель:** добавить практическую основу цифрового мира: компьютеры, данные, сети, software, AI, безопасность, хранение и коммуникационные системы.

---

## 📦 Knowledge Units

| ID | Тип | Суть | Условия / границы | Связи |
|---|---|---|---|---|
| `computing.bit` | TERM | Бит хранит одно из двух состояний: 0 или 1. | Физическая реализация может быть разной. | information |
| `computing.byte` | TERM | Байт обычно содержит 8 бит и часто хранит символ или малое число. | Кодировка определяет смысл байтов. | data |
| `computing.binary_integer` | MODEL | Двоичное представление кодирует числа степенями двойки. | Signed formats имеют разные правила. | math |
| `computing.floating_point` | MODEL | Floating point приближённо хранит вещественные числа через мантиссу и экспоненту. | Ошибки округления неизбежны. | numerical |
| `computing.character_encoding` | SYSTEM | Кодировка связывает числа с символами. | Несовпадение кодировок ломает текст. | text |
| `computing.unicode` | STANDARD | Unicode задаёт универсальное пространство символов разных письменностей. | UTF-8, UTF-16 — способы кодирования. | text |
| `computing.cpu.fetch_decode_execute` | MECHANISM | CPU выполняет цикл выборки, декодирования и исполнения инструкций. | Современные CPU усложняют это конвейерами и кэшами. | hardware |
| `computing.cpu.cache` | COMPONENT | Кэш CPU хранит часто используемые данные ближе к ядру. | Ошибки locality снижают скорость. | performance |
| `computing.memory.ram` | COMPONENT | RAM хранит данные для текущей работы программы. | Теряется при выключении питания. | hardware |
| `computing.storage.ssd` | COMPONENT | SSD хранит данные во флеш-памяти без движущихся частей. | Имеет износ записи. | storage |
| `computing.storage.hdd` | COMPONENT | HDD хранит данные магнитно на вращающихся пластинах. | Чувствителен к ударам и механике. | storage |
| `computing.filesystem` | SYSTEM | Файловая система организует данные в файлы, каталоги и метаданные. | Повреждение метаданных может потерять доступ. | OS |
| `computing.operating_system` | SYSTEM | OS управляет процессами, памятью, файлами, устройствами и правами. | Разные OS имеют разные модели безопасности. | software |
| `computing.process_thread` | DISTINCTION | Процесс имеет своё пространство ресурсов; поток делит ресурсы процесса. | Ошибки синхронизации сложны. | programming |
| `computing.virtual_memory` | SYSTEM | Virtual memory даёт процессам иллюзию собственного адресного пространства. | Page faults влияют на скорость. | OS |
| `computing.container` | SYSTEM | Container изолирует приложение через OS-level механизмы. | Не равен виртуальной машине по уровню изоляции. | deployment |
| `computing.virtual_machine` | SYSTEM | VM эмулирует целую машину поверх гипервизора. | Больше накладных расходов, сильнее изоляция. | infrastructure |
| `software.algorithm` | TERM | Алгоритм — конечное описание шагов решения задачи. | Качество зависит от сложности и корректности. | logic |
| `software.data_structure` | TERM | Структура данных организует хранение и доступ к информации. | Выбор меняет скорость и сложность. | programming |
| `software.big_o` | MODEL | Big-O описывает рост затрат алгоритма при увеличении входа. | Игнорирует константы и реальные машины. | math |
| `software.recursion` | METHOD | ПО: Рекурсия решает задачу через вызов самой себя на меньшем случае. | Нужен базовый случай. | programming |
| `software.api` | INTERFACE | API задаёт способ взаимодействия программ. | Контракт важнее внутренней реализации. | software |
| `software.sdk` | TOOLSET | SDK даёт библиотеки, инструменты и примеры для разработки. | Может привязывать к платформе. | development |
| `software.version_control` | SYSTEM | Version control хранит историю изменений файлов. | Полезен для кода, документов и конфигураций. | git |
| `software.branching` | METHOD | Branching позволяет вести параллельные линии разработки. | Требует merge discipline. | git |
| `software.testing.unit` | QUALITY_CHECK | Unit tests проверяют малые части программы. | Не доказывают работу всей системы. | QA |
| `software.testing.integration` | QUALITY_CHECK | Integration tests проверяют взаимодействие компонентов. | Часто сложнее и медленнее unit tests. | QA |
| `software.testing.regression` | QUALITY_CHECK | Regression tests ловят повторное появление старых ошибок. | Нужны после исправлений. | QA |
| `software.ci_cd` | SYSTEM | CI/CD автоматизирует сборку, тесты и доставку изменений. | Плохой pipeline быстро распространяет ошибки. | devops |
| `software.logging` | METHOD | Логи фиксируют события системы для диагностики. | Логи не должны раскрывать секреты. | observability |
| `software.metrics` | METHOD | Метрики измеряют состояние и поведение системы во времени. | Нужны пороги и контекст. | observability |
| `software.tracing` | METHOD | Tracing показывает путь запроса через сервисы. | Важно для distributed systems. | observability |
| `software.backup` | SAFETY_SYSTEM | Backup хранит копии данных для восстановления. | Непроверенный backup может быть бесполезен. | resilience |
| `software.restore_test` | QUALITY_CHECK | Restore test проверяет, что backup реально восстанавливается. | Нужно делать регулярно. | resilience |
| `data.table` | STRUCTURE | Таблица хранит данные в строках и столбцах. | Типы и ключи задают смысл. | databases |
| `data.primary_key` | CONSTRAINT | Primary key уникально идентифицирует запись. | Изменение ключа может ломать ссылки. | databases |
| `data.foreign_key` | CONSTRAINT | Foreign key связывает запись с другой таблицей. | Поддерживает целостность данных. | databases |
| `data.index` | STRUCTURE | Индекс ускоряет поиск за счёт дополнительного хранения. | Замедляет запись и требует памяти. | databases |
| `data.transaction` | MECHANISM | Транзакция объединяет операции в атомарное изменение. | Нужна для денег, заказов, учёта. | databases |
| `data.acid` | PRINCIPLE | ACID описывает атомарность, согласованность, изоляцию и долговечность. | Реализация зависит от БД. | databases |
| `data.normalization` | METHOD | Нормализация снижает дубли и аномалии в таблицах. | Иногда денормализация нужна для скорости. | databases |
| `data.etl` | PROCESS | ETL извлекает, преобразует и загружает данные. | Ошибки transformation портят аналитику. | data_engineering |
| `data.data_quality` | QUALITY | Качество данных включает полноту, точность, актуальность и согласованность. | Garbage in, garbage out. | analytics |
| `data.lineage` | TRACE | Data lineage показывает происхождение и преобразования данных. | Критично для аудита и доверия. | governance |
| `data.privacy_minimization` | PRINCIPLE | Data minimization собирает только нужные данные. | Снижает риск утечек. | privacy |
| `network.packet` | TERM | Пакет — единица передачи данных в сети. | Может теряться, дублироваться, приходить не по порядку. | networking |
| `network.ip_address` | TERM | IP-адрес идентифицирует узел или интерфейс в сети. | IPv4 и IPv6 отличаются. | networking |
| `network.dns` | SYSTEM | DNS переводит имена доменов в адреса. | Компрометация DNS опасна. | internet |
| `network.tcp` | PROTOCOL | TCP обеспечивает надёжную последовательную передачу байтов. | Имеет задержки подтверждения и congestion control. | internet |
| `network.udp` | PROTOCOL | UDP передаёт датаграммы без гарантии доставки. | Полезен для real-time и простых протоколов. | internet |
| `network.http` | PROTOCOL | HTTP задаёт обмен запросами и ответами в web. | HTTPS добавляет шифрование через TLS. | web |
| `network.tls` | SECURITY_PROTOCOL | TLS шифрует и аутентифицирует сетевое соединение. | Сертификаты и настройки критичны. | security |
| `network.wifi` | SYSTEM | Wi-Fi передаёт данные радиосигналом в локальной сети. | Помехи и стены влияют на скорость. | communications |
| `network.cellular` | SYSTEM | Сотовая связь делит территорию на соты с базовыми станциями. | Скорость зависит от спектра, нагрузки и сигнала. | telecom |
| `network.satellite` | SYSTEM | Спутниковая связь передаёт данные через орбитальные аппараты. | Задержка зависит от орбиты. | telecom |
| `cyber.authentication` | SECURITY_CONTROL | Authentication проверяет, кто пользователь или система. | Пароль — только один возможный фактор. | security |
| `cyber.authorization` | SECURITY_CONTROL | Authorization определяет, что разрешено после проверки личности. | Ошибки ведут к privilege escalation. | security |
| `cyber.mfa` | SECURITY_CONTROL | MFA требует больше одного фактора входа. | Не все факторы одинаково устойчивы. | security |
| `cyber.password_hashing` | SECURITY_CONTROL | Пароли хранят как устойчивые хэши с salt, а не открытым текстом. | Нужны медленные функции для паролей. | security |
| `cyber.phishing` | ATTACK | Phishing обманывает пользователя, чтобы получить секреты или действие. | Техническая защита и обучение нужны вместе. | security |
| `cyber.malware` | ATTACK | Malware выполняет вредные действия на устройстве. | Каналы: файлы, ссылки, supply chain. | security |
| `cyber.ransomware` | ATTACK | Ransomware шифрует или блокирует данные ради выкупа. | Backup и сегментация критичны. | resilience |
| `cyber.patch_management` | SECURITY_PROCESS | Patch management закрывает известные уязвимости. | Нужно тестировать критичные системы. | operations |
| `cyber.least_privilege` | PRINCIPLE | Least privilege выдаёт минимальные нужные права. | Требует пересмотра доступов. | security |
| `cyber.incident_response` | PROCESS | Incident response включает обнаружение, containment, eradication, recovery и lessons learned. | План должен быть заранее. | security |
| `ai.model.training` | PROCESS | Training подбирает параметры модели на данных и objective. | Данные и loss определяют поведение. | AI |
| `ai.inference` | PROCESS | Inference использует обученную модель для ответа или предсказания. | Может ошибаться за пределами данных. | AI |
| `ai.embedding` | REPRESENTATION | Embedding кодирует объект как числовой вектор для сходства и моделей. | Близость не всегда равна истинной связи. | retrieval |
| `ai.retrieval_augmented_generation` | METHOD | RAG добавляет найденные внешние факты в контекст генерации. | Качество зависит от retrieval и grounding. | AI |
| `ai.hallucination` | FAILURE_MODE | Hallucination — уверенно звучащее, но неподтверждённое или ложное утверждение. | Требует evidence, trace и проверки. | truth_gate |
| `ai.evaluation` | QUALITY_CHECK | Evaluation проверяет модель на задачах, ошибках и рисках. | Нужны репрезентативные данные. | AI |
| `ai.bias` | RISK | Bias модели может отражать данные, метрики и системные решения. | Нужен аудит по контексту. | ethics |
| `ai.prompt_context` | INPUT | Prompt и контекст направляют поведение модели на inference. | Не гарантируют истинность. | LLM |
| `ai.tool_use` | CAPABILITY | Tool use позволяет AI вызывать внешние функции и данные. | Требует прав, валидации и логирования. | agents |
| `ai.memory_external` | SYSTEM | Внешняя память хранит факты и предпочтения вне весов модели. | Требует consent, correction, deletion. | exocortex |
| `ai.guardrail` | SAFETY_SYSTEM | Guardrail ограничивает вредные, недостоверные или запрещённые outputs. | Может ошибаться и требует прозрачности. | safety |
| `ai.traceability` | PRINCIPLE | Traceability показывает, какие данные и шаги привели к ответу. | Не равно доказательству без quality checks. | TRACE |

---

## 📊 Batch 017 summary

```text
new units: 77
main layers:
  hardware / OS / software engineering
  data systems and databases
  networking and cybersecurity
  AI, RAG, memory and traceability
```
