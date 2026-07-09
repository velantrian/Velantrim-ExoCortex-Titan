# 🔗 Batch 029 — Systems, Models & Causal Thinking

**Язык:** русский  
**Статус:** 50K batch 029 / seed units / не L3 truth  
**Цель:** добавить слой "как думать о сложных системах": причинность, модели, обратные связи, неопределённость, сценарии, ограничения и failure modes.

---

## 📦 Knowledge Units

| ID | Тип | Суть | Условия / границы | Связи |
|---|---|---|---|---|
| `systems.boundary` | MODEL | Граница системы определяет, что включено в анализ, а что считается средой. | Неверная граница меняет вывод. | modeling |
| `systems.input_output` | MODEL | Система преобразует входы в выходы через процессы и состояния. | Слишком простая схема скрывает feedback. | systems |
| `systems.state` | TERM | Состояние системы описывает важные переменные в данный момент. | Не все переменные наблюдаемы. | modeling |
| `systems.stock_flow` | MODEL | Stock — накопление, flow — скорость изменения накопления. | Важно для воды, денег, запасов, населения. | dynamics |
| `systems.feedback_positive` | MECHANISM | Positive feedback усиливает изменение. | Может вести к росту или runaway. | dynamics |
| `systems.feedback_negative` | MECHANISM | Negative feedback стабилизирует систему через коррекцию отклонений. | Задержки могут вызвать колебания. | control |
| `systems.delay` | MECHANISM | Задержка между причиной и эффектом усложняет управление. | Часто вызывает overshoot. | dynamics |
| `systems.nonlinearity` | PROPERTY | Нелинейность означает, что эффект не пропорционален причине. | Малые изменения могут иметь большой эффект. | math |
| `systems.threshold` | PROPERTY | Threshold — уровень, после которого поведение системы меняется. | До порога риск может быть незаметен. | risk |
| `systems.tipping_point` | MODEL | Tipping point — критический переход системы в другой режим. | Точное предсказание часто трудно. | climate |
| `systems.resilience` | PROPERTY | Resilience — способность системы сохранять или восстанавливать функцию после удара. | Не равно неизменности. | safety |
| `systems.robustness` | PROPERTY | Robustness — устойчивость к вариациям без отказа. | Может снижать гибкость. | engineering |
| `systems.redundancy` | DESIGN_PRINCIPLE | Redundancy добавляет запасные элементы для отказоустойчивости. | Увеличивает стоимость и сложность. | reliability |
| `systems.diversity` | DESIGN_PRINCIPLE | Разнообразие путей и компонентов снижает общий риск одинакового отказа. | Может снижать стандартизацию. | resilience |
| `systems.modularity` | DESIGN_PRINCIPLE | Модульность ограничивает распространение ошибок и упрощает замену. | Слишком много интерфейсов увеличивает complexity. | architecture |
| `systems.coupling.tight` | PROPERTY | Tight coupling означает сильную и быструю зависимость компонентов. | Ошибки быстро распространяются. | safety |
| `systems.coupling.loose` | PROPERTY | Loose coupling даёт буфер между частями системы. | Может снижать эффективность. | design |
| `systems.complexity.essential_accidental` | DISTINCTION | Essential complexity исходит из задачи; accidental — из плохой реализации. | Важно для software и организаций. | engineering |
| `systems.emergence` | PHENOMENON | Emergence — свойства целого, не очевидные из отдельных частей. | Не магия, а результат взаимодействий. | complexity |
| `systems.path_dependence` | MODEL | Path dependence означает, что история выбора ограничивает будущее. | Часто в технологиях и институтах. | history |
| `systems.lock_in` | FAILURE_MODE | Lock-in удерживает систему в неидеальном стандарте из-за costs switching. | Может быть рыночным или техническим. | economics |
| `systems.leverage_point` | MODEL | Leverage point — место, где малое изменение даёт большой эффект. | Трудно определить без модели. | strategy |
| `systems.local_global_optimum` | DISTINCTION | Локальная оптимизация может ухудшить глобальный результат. | Часто в supply chains и бюрократии. | optimization |
| `systems.constraint_theory` | MODEL | Theory of constraints ищет узкое место, ограничивающее throughput. | После устранения ограничение перемещается. | operations |
| `systems.tradeoff` | PRINCIPLE | Tradeoff означает, что улучшение одного свойства часто ухудшает другое. | Не все компромиссы неизбежны. | design |
| `systems.second_order_effect` | MODEL | Вторичные эффекты появляются после прямого результата решения. | Часто недооцениваются. | policy |
| `systems.unintended_consequence` | FAILURE_MODE | Непреднамеренные последствия возникают из-за сложных связей и стимулов. | Требуют monitoring. | policy |
| `systems.incentive_alignment` | PRINCIPLE | Система работает лучше, когда стимулы участников совпадают с целью. | Люди оптимизируют то, что измеряется. | governance |
| `systems.metric_gaming` | FAILURE_MODE | Metric gaming возникает, когда метрика становится целью и искажает поведение. | Goodhart's law. | management |
| `systems.goodharts_law` | PRINCIPLE | Когда показатель становится целью, он теряет качество показателя. | Нужно использовать multiple signals. | measurement |
| `systems.risk.hazard_exposure_vulnerability` | MODEL | Риск зависит от опасности, воздействия и уязвимости. | Уменьшать можно любой компонент. | disaster |
| `systems.risk.expected_value` | MODEL | Expected value умножает вероятность на последствия. | Плохо описывает tail risks. | statistics |
| `systems.risk.tail` | RISK_MODEL | Tail risk — редкое событие с большим ущербом. | Средние значения скрывают. | finance |
| `systems.risk.precautionary` | PRINCIPLE | Precautionary principle осторожен при серьёзном риске и неопределённости. | Может конфликтовать с инновациями. | ethics |
| `systems.risk.fail_safe` | DESIGN_PRINCIPLE | Fail-safe переводит систему в безопасное состояние при отказе. | Требует понимания safe state. | safety |
| `systems.risk.fail_operational` | DESIGN_PRINCIPLE | Fail-operational сохраняет работу после отказа. | Нужно в авиации, медицине, инфраструктуре. | reliability |
| `systems.causality.correlation` | DISTINCTION | Корреляция показывает совместное изменение, но не причину. | Может быть confounding. | statistics |
| `systems.causality.confounder` | TERM | Confounder влияет и на предполагаемую причину, и на результат. | Искажает наблюдательные выводы. | causal |
| `systems.causality.mediator` | TERM | Mediator передаёт часть причинного эффекта от X к Y. | Не путать с confounder. | causal |
| `systems.causality.collider` | TERM | Collider — переменная, на которую влияют две причины; условие на ней создаёт ложную связь. | Частая ошибка анализа. | causal |
| `systems.causality.dag` | MODEL | DAG показывает направленные причинные связи без циклов. | Упрощает реальность. | causal_graph |
| `systems.causality.intervention` | METHOD | Интервенция спрашивает, что будет, если изменить X принудительно. | Отличается от наблюдения. | causal |
| `systems.causality.counterfactual` | METHOD | Контрфакт спрашивает, что было бы при другом условии. | Требует causal model. | reasoning |
| `systems.model.abstraction` | PRINCIPLE | Абстракция оставляет важное и убирает детали. | Можно убрать слишком много. | modeling |
| `systems.model.assumption` | TERM | Assumption — принятое условие модели. | Должно быть явно указано. | epistemology |
| `systems.model.sensitivity` | METHOD | Sensitivity analysis проверяет, как результат меняется от assumptions. | Выявляет fragile conclusions. | modeling |
| `systems.model.scenario` | METHOD | Scenario planning сравнивает несколько возможных будущих. | Не является предсказанием. | strategy |
| `systems.model.monte_carlo` | METHOD | Monte Carlo моделирует неопределённость через множество случайных прогонов. | Зависит от распределений входов. | statistics |
| `systems.model.agent_based` | METHOD | Agent-based model строит поведение системы из действий агентов. | Требует правил агентов и валидации. | simulation |
| `systems.model.system_dynamics` | METHOD | System dynamics моделирует stocks, flows, feedback and delays. | Полезно для policy и operations. | simulation |
| `systems.model.digital_twin` | SYSTEM | Digital twin связывает модель объекта с данными реального состояния. | Нужны sensors, calibration, governance. | industry |
| `systems.optimization.objective_function` | TERM | Objective function задаёт, что оптимизируется. | Неправильная цель портит решение. | math |
| `systems.optimization.constraint` | TERM | Constraint ограничивает допустимые решения. | Игнорирование constraints делает решение нереальным. | math |
| `systems.optimization.pareto_front` | MODEL | Pareto front показывает решения, где нельзя улучшить одно без ухудшения другого. | Помогает tradeoff analysis. | decision |
| `systems.decision.criteria_matrix` | TOOL | Матрица критериев сравнивает варианты по нескольким признакам. | Веса критериев субъективны. | decision |
| `systems.decision.pre_mortem` | METHOD | Pre-mortem заранее спрашивает, почему проект мог провалиться. | Помогает найти риски до старта. | project |
| `systems.decision.reversibility` | PRINCIPLE | Обратимые решения можно принимать быстрее, необратимые требуют проверки. | Степень обратимости надо оценивать честно. | strategy |
| `systems.learning.feedback_loop` | SYSTEM | Система учится, если собирает feedback и меняет поведение. | Feedback может быть шумным или запаздывать. | learning |
| `systems.learning.double_loop` | METHOD | Double-loop learning пересматривает не только действия, но и правила/цели. | Требует психологической безопасности. | organization |
| `systems.knowledge.unknown_unknowns` | RISK | Unknown unknowns — неизвестные неизвестные, не включённые в модель. | Нужны разведка, эксперименты, резервы. | epistemology |
| `systems.knowledge.map_territory` | PRINCIPLE | Модель или карта не равна реальности. | Полезная модель всё равно неполна. | epistemology |
| `systems.explanation.mechanism` | PRINCIPLE | Хорошее объяснение показывает механизм, а не только совпадение. | Механизм должен иметь evidence. | science |

---

## 📊 Batch 029 summary

```text
new units: 62
main layers:
  systems and feedback
  risk, causality and modeling
  optimization, decisions and learning
```
