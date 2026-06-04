# 🧠 P1 Human & Society Expansion — человек, общество, смысл

**Язык:** русский  
**Статус:** seed pack v0.2 / не L3 truth  
**Назначение:** расширить знания о мышлении, обучении, коммуникации, рисках, экономике, праве, этике и философии так, чтобы система лучше понимала человеческий контекст.

---

## 📦 Knowledge Units

| ID | Тип | Суть | Условия / границы | Связи |
|---|---|---|---|---|
| `human.perception.top_down` | MECHANISM | Восприятие зависит не только от сигнала, но и от ожиданий и контекста. | Может улучшать распознавание или создавать ошибки. | cognition |
| `human.perception.bottom_up` | MECHANISM | Bottom-up обработка идёт от сенсорных данных к интерпретации. | Никогда полностью не изолирована от контекста. | perception |
| `human.attention.inattentional_blindness` | EFFECT | При фокусе на задаче человек может не заметить очевидный стимул. | Зависит от нагрузки и ожиданий. | safety |
| `human.memory.reconstructive` | PRINCIPLE | Человеческая память реконструирует, а не воспроизводит идеально. | Свидетельские воспоминания могут искажаться. | epistemology |
| `human.memory.spaced_repetition` | METHOD | Интервальное повторение улучшает долговременное запоминание. | Интервалы зависят от сложности и человека. | learning |
| `human.learning.chunking` | METHOD | Chunking объединяет элементы в смысловые блоки, снижая нагрузку. | Требует знакомых паттернов. | education |
| `human.learning.feedback` | METHOD | Быстрая обратная связь ускоряет коррекцию ошибок. | Плохой feedback может вредить. | training |
| `human.learning.transfer` | EFFECT | Перенос обучения происходит, когда навык применим в новом контексте. | Поверхностное сходство не гарантирует перенос. | analogy |
| `human.skill.deliberate_practice` | METHOD | Осознанная практика работает через целевые упражнения и feedback. | Требует усилия, времени, наставления или измерения. | mastery |
| `human.emotion.salience` | MECHANISM | Эмоции повышают значимость сигналов и влияют на внимание/память. | Не являются надёжным индикатором истины. | salience |
| `human.stress.yerkes_dodson` | MODEL | Умеренное возбуждение может улучшать выполнение, чрезмерное ухудшает. | Зависит от задачи и человека. | performance |
| `human.sleep.cognition` | MECHANISM | Сон влияет на внимание, память, регуляцию эмоций и восстановление. | Медицинские claims требуют источников. | health |
| `human.communication.context` | PRINCIPLE | Значение сообщения зависит от контекста, отношений, цели и культуры. | Буквальный текст не всегда полное значение. | language |
| `human.communication.grice` | MODEL | Максимы Грайса описывают кооперативность: количество, качество, отношение, способ. | Описание, не закон. | pragmatics |
| `human.communication.framing` | EFFECT | Фрейм подачи меняет восприятие решения. | Может быть манипулятивным. | decision |
| `human.conflict.interests_positions` | DISTINCTION | Позиция — что человек требует; интерес — зачем ему это нужно. | Переговоры часто улучшаются через интересы. | negotiation |
| `human.negotiation.batna` | METHOD | Переговоры: BATNA — лучшая альтернатива соглашению. | Сильная BATNA повышает переговорную позицию. | economics |
| `human.trust.repair` | METHOD | Доверие восстанавливают признанием, исправлением, последовательностью и временем. | Не всегда возможно. | social |
| `human.group.groupthink` | FAILURE_MODE | Groupthink подавляет сомнения ради согласия группы. | Риск выше при изоляции и сильном лидере. | governance |
| `human.group.diffusion_responsibility` | EFFECT | В группе ответственность может размываться. | Снижается назначением явных ролей. | safety |
| `human.decision.satisficing` | METHOD | Satisficing выбирает достаточно хороший вариант вместо оптимального. | Полезно при ограниченном времени/данных. | bounded_rationality |
| `human.decision.bounded_rationality` | MODEL | Люди принимают решения с ограниченной информацией, временем и вычислениями. | Не означает иррациональность всегда. | economics |
| `human.risk.base_rate_neglect` | BIAS | Люди часто игнорируют базовые частоты при оценке вероятности. | Улучшается явным подсчётом. | bayes |
| `human.risk.normalcy_bias` | BIAS | Люди могут недооценивать угрозу, ожидая нормального продолжения. | Опасно при авариях. | safety |
| `human.risk.overconfidence` | BIAS | Люди часто переоценивают точность своих знаний или прогнозов. | Требуется calibration. | uncertainty |
| `human.calibration` | METHOD | Калибровка уверенности сравнивает заявленную уверенность с фактической точностью. | Нужны исторические данные. | epistemology |
| `soc.economics.inflation` | TERM | Инфляция — рост общего уровня цен. | Причины различны; не всякий рост цены = инфляция. | economy |
| `soc.economics.productivity` | TERM | Производительность измеряет output на единицу input. | Метрики зависят от отрасли. | industry |
| `soc.economics.comparative_advantage` | PRINCIPLE | Выгода торговли может возникать из относительных, а не абсолютных преимуществ. | Модель имеет допущения. | trade |
| `soc.economics.moral_hazard` | FAILURE_MODE | Moral hazard возникает, когда защита от последствий меняет поведение к большему риску. | Важен дизайн стимулов. | insurance |
| `soc.economics.adverse_selection` | FAILURE_MODE | Adverse selection возникает при асимметрии информации до сделки. | Типично для страхования/рынков. | information |
| `soc.organization.principal_agent` | MODEL | Агент может действовать не в интересах принципала при разных целях/информации. | Решается контрактами, мониторингом, стимулами. | governance |
| `soc.organization.bureaucracy` | MODEL | Бюрократия формализует правила и роли для устойчивости управления. | Может снижать гибкость. | institutions |
| `soc.organization.resilience` | PROPERTY | Устойчивость системы — способность сохранять функции при сбоях. | Требует redundancy, adaptation, learning. | reliability |
| `soc.law.contract` | TERM | Контракт фиксирует обязательства сторон. | Конкретная сила зависит от правовой системы. | law |
| `soc.law.property` | TERM | Право собственности регулирует контроль над ресурсом. | Есть ограничения общественными интересами. | economics |
| `soc.law.due_process` | PRINCIPLE | Due process требует процедурной справедливости перед санкциями. | Реализация зависит от системы. | rule_of_law |
| `soc.law.privacy` | PRINCIPLE | Приватность защищает контроль над личной информацией. | Балансируется с безопасностью, законом, согласием. | AI_ethics |
| `soc.law.consent` | PRINCIPLE | Согласие должно быть информированным и добровольным, чтобы иметь силу. | Есть контексты с ограниченной способностью согласия. | ethics |
| `soc.city.zoning` | METHOD | Зонирование регулирует виды использования территории. | Может улучшать порядок или создавать неэффективность. | urban |
| `soc.city.public_transport` | SYSTEM | Общественный транспорт повышает мобильность при высокой плотности спроса. | Требует сети, расписания, финансирования. | infrastructure |
| `soc.city.walkability` | PROPERTY | Walkability зависит от плотности, безопасности, расстояний, тротуаров и смешанности функций. | Субъективная и объективная метрики различаются. | urban_design |
| `soc.supply_chain.inventory` | METHOD | Запасы снижают риск дефицита, но увеличивают стоимость хранения. | Trade-off с just-in-time. | logistics |
| `soc.supply_chain.just_in_time` | METHOD | JIT снижает запасы, полагаясь на надёжные поставки. | Уязвим к disruptions. | logistics |
| `soc.supply_chain.bullwhip` | FAILURE_MODE | Bullwhip effect усиливает колебания спроса вверх по цепочке поставок. | Снижается информацией и координацией. | logistics |
| `phil.science.paradigm` | MODEL | Научные парадигмы задают рамки вопросов, методов и интерпретации. | Не означает, что истина чисто относительна. | history_science |
| `phil.science.underdetermination` | PROBLEM | Данные могут быть совместимы с несколькими теориями. | Нужны дополнительные критерии: простота, плодотворность, coherence. | epistemology |
| `phil.science.reproducibility` | PRINCIPLE | Воспроизводимость повышает доверие к результату. | В сложных системах точное повторение трудно. | quality |
| `phil.science.peer_review_limit` | CONSTRAINT | Peer review снижает риск ошибок, но не гарантирует истинность. | Ошибочные работы могут проходить review. | source_tier |
| `phil.truth.correspondence` | POSITION | Корреспондентская теория связывает истину с соответствием реальности. | Философская позиция. | epistemology |
| `phil.truth.coherence` | POSITION | Когерентная теория связывает истину с согласованностью системы убеждений. | Согласованная система может быть оторвана от реальности. | epistemology |
| `phil.truth.pragmatic` | POSITION | Прагматическая теория оценивает истину через практические последствия. | Не равна простому "полезно значит истинно". | philosophy |
| `phil.ethics.harm_principle` | PRINCIPLE | Ограничение свободы часто обосновывают предотвращением вреда другим. | Концепт вреда спорен. | governance |
| `phil.ethics.double_effect` | PRINCIPLE | Эффект действия может быть намеренным или побочным, что влияет на оценку. | Спорный принцип. | medical_ethics |
| `phil.ai.transparency` | PRINCIPLE | AI-система должна показывать основания важных решений. | Глубина объяснения зависит от риска. | trace |
| `phil.ai.accountability` | PRINCIPLE | Должно быть понятно, кто отвечает за последствия системы. | Особенно важно при автоматизации. | governance |
| `phil.ai.human_oversight` | PRINCIPLE | В высокорисковых задачах человек должен иметь возможность контроля. | Не формальность: нужен реальный механизм вмешательства. | safety |
| `phil.meaning.context_dependence` | PRINCIPLE | Смысл часто зависит от цели, ситуации и уровня абстракции. | Нельзя всегда извлечь смысл из словаря терминов. | essence |
| `phil.analogy.structure` | PRINCIPLE | Сильная аналогия переносит структуру отношений, а не поверхностное сходство. | Нужно указывать disanalogies. | cross_domain |
| `phil.uncertainty.honesty` | PRINCIPLE | Честная система должна различать знание, вывод, гипотезу и неизвестность. | Основа Truth Gate. | velantrim |

