# 🧠 Batch 015 — Education, Knowledge Work & Communication

**Язык:** русский  
**Статус:** 50K batch 015 / seed units / не L3 truth  
**Цель:** добавить практические знания о том, как люди учатся, объясняют, документируют, принимают решения, работают с информацией и передают смысл.

---

## 📦 Knowledge Units

| ID | Тип | Суть | Условия / границы | Связи |
|---|---|---|---|---|
| `education.learning.prior_knowledge` | PRINCIPLE | Новое знание легче усваивается, когда связано с уже известными структурами. | Ошибочные прежние модели могут мешать. | cognition |
| `education.learning.spaced_repetition` | METHOD | Повторение с интервалами помогает удерживать информацию дольше. | Эффективность зависит от качества карточек и обратной связи. | memory |
| `education.learning.active_recall` | METHOD | Активное извлечение из памяти укрепляет знание лучше пассивного чтения. | Требует проверки ответа. | memory |
| `education.learning.interleaving` | METHOD | Чередование похожих типов задач помогает различать методы. | Может казаться труднее в момент обучения. | practice |
| `education.learning.feedback_loop` | SYSTEM | Обратная связь показывает разницу между попыткой и целью. | Поздняя или неточная обратная связь слабее. | learning |
| `education.learning.scaffolding` | METHOD | Scaffolding даёт временную поддержку, которую убирают по мере освоения. | Слишком много поддержки снижает самостоятельность. | teaching |
| `education.learning.cognitive_load` | CONSTRAINT | Рабочая память ограничена, поэтому сложность надо дозировать. | Эксперты выдерживают больше схем за счёт chunking. | cognition |
| `education.learning.chunking` | METHOD | Chunking объединяет элементы в смысловые блоки. | Работает при понятной структуре материала. | memory |
| `education.learning.transfer` | PRINCIPLE | Transfer — перенос знания в новую ситуацию. | Требует понимания принципа, а не только примера. | reasoning |
| `education.learning.mastery` | MODEL | Mastery learning требует достигнуть базового уровня перед следующим шагом. | Может замедлять поток, но снижает пробелы. | education |
| `education.curriculum.spiral` | MODEL | Spiral curriculum возвращает темы на новом уровне сложности. | Требует хорошей последовательности. | curriculum |
| `education.curriculum.prerequisite_graph` | MODEL | Prerequisite graph показывает, какие знания нужны перед новым знанием. | Ошибка в графе создаёт ложную простоту. | knowledge_graph |
| `education.assessment.formative` | METHOD | Formative assessment помогает учиться во время процесса. | Не должно быть только оценкой наказания. | feedback |
| `education.assessment.summative` | METHOD | Summative assessment измеряет итоговый уровень после блока обучения. | Может плохо отражать процесс и контекст. | assessment |
| `education.assessment.rubric` | TOOL | Rubric описывает критерии качества работы. | Слишком расплывчатые критерии не помогают. | evaluation |
| `education.assessment.validity` | QUALITY | Валидность означает, что оценивание измеряет то, что должно измерять. | Тест может быть надёжным, но невалидным. | measurement |
| `education.assessment.reliability` | QUALITY | Надёжность означает стабильность результата при повторении/экспертах. | Не гарантирует смысловую правильность. | measurement |
| `education.instruction.example_worked` | METHOD | Worked example показывает полный путь решения. | Полезен новичкам, но эксперту может мешать. | teaching |
| `education.instruction.socratic_questioning` | METHOD | Сократические вопросы ведут к выявлению предпосылок и противоречий. | Требует уважительного темпа. | philosophy |
| `education.instruction.concept_map` | TOOL | Concept map показывает понятия и связи между ними. | Качество зависит от правильных отношений. | knowledge_graph |
| `education.instruction.analogy` | METHOD | Аналогия помогает понять новое через знакомую структуру. | Нужно явно указать, где аналогия ломается. | reasoning |
| `education.instruction.demonstration` | METHOD | Демонстрация показывает процесс в действии. | Без объяснения причин может стать зрелищем. | practical |
| `education.instruction.simulation` | METHOD | Симуляция позволяет безопасно изучать процесс и последствия. | Модель упрощает реальность. | modeling |
| `education.instruction.project_based` | METHOD | Project-based learning связывает знание с реальным продуктом. | Нужны критерии и этапы, иначе хаос. | practice |
| `education.instruction.apprenticeship` | MODEL | Ученичество передаёт навыки через наблюдение, практику и коррекцию мастера. | Зависит от качества мастера. | craft |
| `education.instruction.peer_teaching` | METHOD | Объяснение другим укрепляет собственное понимание. | Нужно контролировать распространение ошибок. | learning |
| `education.literacy.reading_comprehension` | SKILL | Понимание текста требует словаря, структуры, контекста и вывода. | Быстрое чтение не равно пониманию. | language |
| `education.literacy.numeracy` | SKILL | Numeracy — умение применять числа, доли, оценки и графики в жизни. | Важно для денег, медицины, техники. | math |
| `education.literacy.scientific_literacy` | SKILL | Scientific literacy помогает понимать evidence, uncertainty и claims. | Не требует быть учёным. | science |
| `education.literacy.media_literacy` | SKILL | Media literacy оценивает источник, цель, framing и доказательства сообщения. | Не равно тотальному недоверию. | information |
| `education.literacy.data_literacy` | SKILL | Data literacy помогает читать таблицы, графики, статистику и ограничения данных. | Ошибки визуализации могут вводить в заблуждение. | data |
| `knowledgework.note.atomic` | METHOD | Atomic note хранит одну идею, чтобы её легко связывать. | Без связей превращается в карточный хаос. | notes |
| `knowledgework.note.source_link` | RULE | Заметка должна хранить источник и контекст происхождения. | Иначе невозможно проверить. | trace |
| `knowledgework.note.progressive_summary` | METHOD | Progressive summary выделяет уровни важности в заметке. | Может исказить смысл при плохом отборе. | summarization |
| `knowledgework.zettelkasten` | SYSTEM | Zettelkasten строит сеть маленьких связанных заметок. | Требует дисциплины ссылок и формулировок. | memory |
| `knowledgework.decision_log` | TOOL | Decision log фиксирует решение, причины, альтернативы и дату. | Помогает не переписывать историю. | governance |
| `knowledgework.meeting_minutes` | DOCUMENT | Minutes фиксируют решения, задачи, ответственных и сроки. | Не должны быть стенограммой без структуры. | management |
| `knowledgework.requirements` | DOCUMENT | Requirements описывают, что система должна делать и какие ограничения есть. | Нечёткие требования ведут к переделкам. | engineering |
| `knowledgework.specification` | DOCUMENT | Specification переводит потребность в проверяемое описание решения. | Требует границ и тестов. | engineering |
| `knowledgework.checklist` | TOOL | Checklist снижает риск пропуска известных шагов. | Не заменяет понимание ситуации. | safety |
| `knowledgework.standard_operating_procedure` | DOCUMENT | SOP задаёт повторяемый способ выполнения процесса. | Должен обновляться после изменений. | operations |
| `knowledgework.postmortem` | METHOD | Postmortem анализирует инцидент без поиска козла отпущения. | Сильнее, когда ищет системные причины. | reliability |
| `knowledgework.root_cause_analysis` | METHOD | RCA ищет глубинные причины отказа, а не только симптом. | Может уйти в бесконечность без границ. | quality |
| `knowledgework.five_whys` | METHOD | Five whys повторно спрашивает "почему", углубляя причину. | Уязвим к предвзятости одной версии. | RCA |
| `knowledgework.fishbone_diagram` | TOOL | Диаграмма Исикавы группирует причины по категориям. | Полезна для командного анализа. | quality |
| `knowledgework.kanban` | METHOD | Kanban визуализирует поток работы и WIP limits. | Не решает приоритеты сам по себе. | operations |
| `knowledgework.gantt` | TOOL | Gantt показывает задачи, сроки и зависимости на временной шкале. | Плохо отражает неопределённость. | project |
| `knowledgework.risk_register` | TOOL | Risk register хранит риски, вероятность, impact, владельца и меры. | Бесполезен без обновления. | management |
| `knowledgework.stakeholder_map` | TOOL | Stakeholder map показывает заинтересованных людей и их влияние/интерес. | Не должен становиться манипуляцией. | governance |
| `communication.sender_receiver` | MODEL | Коммуникация включает отправителя, сообщение, канал, получателя и шум. | Смысл не передаётся идеально. | communication |
| `communication.common_ground` | PRINCIPLE | Common ground — общая база знаний, нужная для понимания. | Её надо проверять, а не предполагать. | language |
| `communication.feedback` | METHOD | Обратная связь подтверждает, что сообщение понято правильно. | Может быть невербальной или явной. | communication |
| `communication.active_listening` | SKILL | Active listening проверяет смысл, эмоцию и запрос собеседника. | Не означает автоматическое согласие. | psychology |
| `communication.nonviolent` | METHOD | Ненасильственная коммуникация разделяет наблюдение, чувство, потребность и просьбу. | Может звучать искусственно без искренности. | conflict |
| `communication.plain_language` | METHOD | Plain language делает текст понятным целевой аудитории. | Не значит упрощать до потери точности. | writing |
| `communication.technical_writing` | SKILL | Technical writing объясняет сложную систему через структуру, определения и шаги. | Требует знания пользователя. | documentation |
| `communication.visual_hierarchy` | DESIGN_PRINCIPLE | Визуальная иерархия показывает, что важнее читать сначала. | Цвет и размер должны помогать, а не шуметь. | design |
| `communication.argument_claim_evidence` | MODEL | Хороший аргумент связывает claim, evidence и reasoning. | Evidence может быть слабым или нерелевантным. | logic |
| `communication.fallacy_strawman` | FALLACY | Strawman искажает позицию оппонента, чтобы легче её опровергнуть. | Нужно возвращаться к сильной версии аргумента. | logic |
| `communication.fallacy_false_dilemma` | FALLACY | False dilemma сводит выбор к двум вариантам, когда есть больше. | Часто используется в споре и политике. | logic |
| `communication.fallacy_post_hoc` | FALLACY | Post hoc ошибочно принимает последовательность за причинность. | Требует causal evidence. | logic |
| `communication.negotiation.batna` | METHOD | BATNA — лучшая альтернатива соглашению. | Сильная BATNA повышает переговорную позицию. | negotiation |
| `communication.negotiation.interests` | PRINCIPLE | Переговоры по интересам ищут потребности за позициями. | Не всегда возможно при недобросовестности. | conflict |
| `communication.crisis_message` | METHOD | Кризисное сообщение должно быть быстрым, честным, конкретным и обновляемым. | Сокрытие разрушает доверие. | public_safety |
| `communication.translation.context` | CONSTRAINT | Перевод требует контекста, регистра и области, а не только словаря. | Термины меняют смысл по доменам. | language |
| `communication.localization` | METHOD | Localization адаптирует текст, формат, культуру и нормы к аудитории. | Не равно буквальному переводу. | product |
| `communication.accessibility` | PRINCIPLE | Доступная коммуникация учитывает зрение, слух, язык, когнитивную нагрузку. | Полезна не только людям с инвалидностью. | design |
| `communication.signage_wayfinding` | DESIGN_SYSTEM | Навигационные знаки помогают людям находить путь в пространстве. | Должны быть видимыми, последовательными, понятными. | urban |

---

## 📊 Batch 015 summary

```text
new units: 68
main layers:
  learning science
  teaching and assessment
  note systems and documentation
  communication, argumentation and negotiation
```
