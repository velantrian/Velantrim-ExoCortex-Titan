# 🧠 Batch 027 — Psychology, Cognition & Social Behavior

**Язык:** русский  
**Статус:** 50K batch 027 / seed units / не L3 truth  
**Цель:** добавить осторожную базу о внимании, памяти, эмоциях, мотивации, группах, привычках и ошибках мышления. Это не диагностика и не терапия.

---

## 📦 Knowledge Units

| ID | Тип | Суть | Условия / границы | Связи |
|---|---|---|---|---|
| `psych.attention.selective` | MODEL | Избирательное внимание усиливает часть сигналов и подавляет другие. | Можно пропустить важное вне фокуса. | cognition |
| `psych.attention.divided` | CONSTRAINT | Разделённое внимание ограничено и ухудшается при сложных задачах. | Multitasking часто является быстрым переключением. | cognition |
| `psych.attention.inattentional_blindness` | FAILURE_MODE | Человек может не заметить видимый объект, если занят другой задачей. | Важно для безопасности и интерфейсов. | perception |
| `psych.memory.working` | MODEL | Рабочая память удерживает и обрабатывает ограниченное количество информации. | Перегружается сложностью и стрессом. | learning |
| `psych.memory.long_term` | MODEL | Долговременная память хранит знания, навыки и эпизоды. | Воспоминания реконструируются, а не воспроизводятся идеально. | memory |
| `psych.memory.episodic` | MODEL | Эпизодическая память хранит события с контекстом времени и места. | Уязвима к искажению. | cognition |
| `psych.memory.semantic` | MODEL | Семантическая память хранит понятия и факты без конкретного эпизода. | Может терять источник знания. | knowledge |
| `psych.memory.procedural` | MODEL | Процедурная память хранит навыки и привычные действия. | Часто трудно объясняется словами. | skill |
| `psych.memory.false_memory` | FAILURE_MODE | Ложные воспоминания могут возникать от внушения, реконструкции и ожиданий. | Не означает намеренную ложь. | evidence |
| `psych.memory.source_monitoring` | FAILURE_MODE | Source monitoring error — забывание, откуда пришла информация. | Важно для слухов и AI outputs. | trace |
| `psych.learning.reinforcement` | MODEL | Поведение усиливается или ослабляется последствиями. | Человеческое поведение сложнее простой награды. | behavior |
| `psych.learning.observational` | MODEL | Люди учатся, наблюдая действия и последствия у других. | Модели поведения важны. | social |
| `psych.motivation.intrinsic` | MODEL | Внутренняя мотивация связана с интересом и смыслом самой деятельности. | Может снижаться при плохих внешних стимулах. | education |
| `psych.motivation.extrinsic` | MODEL | Внешняя мотивация связана с наградами, наказаниями, статусом. | Может работать краткосрочно. | behavior |
| `psych.motivation.goal_gradient` | MODEL | Усилие часто растёт, когда цель кажется близкой. | Восприятие прогресса важно. | habits |
| `psych.habit.cue_routine_reward` | MODEL | Привычка часто связывает сигнал, действие и результат. | Не все привычки объясняются одной петлёй. | behavior |
| `psych.habit.environment_design` | METHOD | Изменение среды может облегчить желаемое поведение. | Сильнее одной силы воли. | design |
| `psych.emotion.appraisal` | MODEL | Эмоции зависят от оценки ситуации относительно целей и угроз. | Разные люди оценивают одно событие иначе. | affect |
| `psych.emotion.regulation` | METHOD | Регуляция эмоций меняет интенсивность, выражение или интерпретацию. | Не равно подавлению. | wellbeing |
| `psych.stress.acute` | MODEL | Острый стресс мобилизует ресурсы для краткосрочной угрозы. | Может помогать или мешать. | physiology |
| `psych.stress.chronic` | RISK | Хронический стресс связан с длительной нагрузкой без восстановления. | Требует контекстной оценки. | health |
| `psych.decision.dual_process` | MODEL | Быстрые эвристики и медленное аналитическое мышление взаимодействуют. | Упрощённая модель, но полезная. | reasoning |
| `psych.bias.confirmation` | BIAS | Confirmation bias — поиск и оценка информации в пользу уже имеющегося убеждения. | Снижается через adversarial questions. | logic |
| `psych.bias.availability` | BIAS | Availability bias переоценивает то, что легко вспомнить. | Медиа и личный опыт усиливают. | judgment |
| `psych.bias.anchoring` | BIAS | Anchoring тянет оценку к первому числу или идее. | Даже случайный якорь может влиять. | decision |
| `psych.bias.fundamental_attribution` | BIAS | Люди часто переоценивают личность и недооценивают ситуацию в поведении других. | Культурно и контекстно вариативно. | social |
| `psych.bias.hindsight` | BIAS | Hindsight bias делает прошлый исход кажущимся очевидным. | Вредит postmortem и обучению. | decision |
| `psych.bias.sunk_cost` | BIAS | Sunk cost bias удерживает в плохом решении из-за уже потраченных ресурсов. | Рационально смотреть на будущие costs/benefits. | economics |
| `psych.risk.perception` | MODEL | Восприятие риска зависит от контроля, новизны, страха и доверия. | Не совпадает с статистическим риском. | safety |
| `psych.trust.calibration` | PRINCIPLE | Доверие должно соответствовать реальной надёжности системы или человека. | Overtrust и undertrust оба вредят. | AI |
| `psych.communication.empathy` | SKILL | Эмпатия помогает понять состояние другого без обязательного согласия. | Не является доказательством правоты. | communication |
| `psych.communication.boundaries` | SKILL | Границы задают допустимое поведение и ответственность сторон. | Нужны ясность и уважение. | relationships |
| `psych.conflict.escalation` | PROCESS | Конфликт растёт через угрозы, унижение, недоверие и ответные шаги. | Деэскалация требует безопасности. | social |
| `psych.conflict.repair` | METHOD | Repair after conflict включает признание, объяснение, изменение и восстановление доверия. | Извинение без изменения слабо. | communication |
| `psych.group.conformity` | MODEL | Люди могут менять поведение под давлением группы. | Сила зависит от нормы, статуса, неопределённости. | social |
| `psych.group.groupthink` | FAILURE_MODE | Groupthink подавляет сомнения ради согласия. | Помогают dissent roles и внешняя проверка. | governance |
| `psych.group.social_loafing` | FAILURE_MODE | В группе часть людей может снижать усилие при размытом вкладе. | Чёткая ответственность снижает риск. | teamwork |
| `psych.group.psychological_safety` | TEAM_PROPERTY | Psychological safety позволяет говорить о проблемах без страха наказания. | Не означает отсутствие стандартов. | management |
| `psych.leadership.power` | MODEL | Власть может быть формальной, экспертной, ресурсной, харизматической. | Тип власти влияет на поведение. | organization |
| `psych.leadership.feedback` | METHOD | Хорошая обратная связь конкретна, своевременна и ориентирована на поведение. | Личностная критика хуже. | management |
| `psych.identity.self_concept` | MODEL | Self-concept — представление человека о себе. | Меняется через опыт и окружение. | psychology |
| `psych.identity.role_conflict` | FAILURE_MODE | Role conflict возникает, когда ожидания разных ролей несовместимы. | Часто в семье, работе, культуре. | sociology |
| `psych.development.attachment` | MODEL | Attachment описывает устойчивые паттерны близости и безопасности в отношениях. | Не надо использовать как ярлык без специалиста. | development |
| `psych.development.play` | MECHANISM | Игра помогает детям развивать правила, воображение, тело и социальность. | Тип игры меняется с возрастом. | education |
| `psych.aging.cognitive_change` | MODEL | С возрастом некоторые когнитивные функции меняются неравномерно. | Индивидуальные различия велики. | health |
| `psych.behavior.nudge` | METHOD | Nudge меняет архитектуру выбора без прямого запрета. | Этический риск манипуляции. | policy |
| `psych.behavior.default_effect` | BIAS | Default option часто выбирается, потому что требует меньше усилий. | Сильно влияет на формы и сервисы. | design |
| `psych.behavior.friction` | DESIGN_FACTOR | Friction усложняет или замедляет действие. | Может защищать от ошибки или мешать нужному. | UX |
| `psych.behavior.reward_schedule` | MODEL | Расписание подкрепления влияет на устойчивость поведения. | Переменные награды могут быть addictive. | design_ethics |
| `psych.wellbeing.autonomy` | NEED | Автономия связана с ощущением выбора и контроля. | Не равна полной независимости. | motivation |
| `psych.wellbeing.competence` | NEED | Компетентность связана с ощущением способности действовать. | Требует подходящих вызовов и feedback. | learning |
| `psych.wellbeing.relatedness` | NEED | Relatedness — чувство связи с другими. | Социальное качество важнее количества контактов. | social |
| `psych.trauma.informed_care` | PRINCIPLE | Trauma-informed подход учитывает безопасность, выбор, доверие и избегание повторной травматизации. | Не является диагнозом. | care |
| `psych.addiction.reinforcement_loop` | MODEL | Зависимое поведение может поддерживаться наградой, облегчением и withdrawal. | Требует профессиональной помощи при серьёзности. | health |
| `psych.design.cognitive_affordance` | DESIGN_PRINCIPLE | Интерфейс должен подсказывать, что с ним можно сделать. | Плохой affordance вызывает ошибки. | UX |
| `psych.design.error_prevention` | DESIGN_PRINCIPLE | Хороший дизайн предотвращает ошибку до её совершения. | Лучше, чем только сообщение после. | safety |
| `psych.design.recovery` | DESIGN_PRINCIPLE | Система должна позволять безопасно исправить ошибку. | Undo и confirmation важны. | UX |
| `psych.ai.user_overtrust` | RISK | Пользователь может переоценить уверенный AI-ответ. | Нужны uncertainty и trace. | AI_safety |
| `psych.ai.anthropomorphism` | RISK | Люди склонны приписывать системе человеческие чувства и намерения. | Интерфейс должен быть честным. | AI_ethics |

---

## 📊 Batch 027 summary

```text
new units: 59
main layers:
  attention, memory and learning
  motivation, emotion and stress
  bias, groups, conflict and design
  AI trust and anthropomorphism
```
