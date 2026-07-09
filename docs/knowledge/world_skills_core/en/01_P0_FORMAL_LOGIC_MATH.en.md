# 🧮 P0 Formal Core — математика, логика, статистика, вычисления

**Язык:** русский  
**Статус:** seed pack v0.1 / не L3 truth  
**Цель:** собрать компактные единицы знания, которые дают Velantrim формальный скелет мышления: считать, выводить, проверять, различать строгий вывод и вероятностное рассуждение.

---

## Правило слоя

Математика и классическая логика могут быть почти `ImmutableCore`, но только после нормализации терминов и проверки формализации.

```text
строгие правила → Validated / ImmutableCore
вероятностные правила → Supported / Validated
эвристики → Supported
философские трактовки логики → Hypothesized / Supported
```

---

## 📦 Knowledge Units

| ID | Тип | Утверждение / суть | Условия и границы | Связи |
|---|---|---|---|---|
| `math.set.element` | TERM | Множество задаётся элементами; принадлежность записывается как `x ∈ A`. | Требуется выбранная теория множеств. | logic.predicate |
| `math.function.mapping` | TERM | Функция сопоставляет каждому элементу области определения ровно одно значение. | Многозначные соответствия не являются функциями без уточнения. | math.relation |
| `math.equality.substitution` | RULE | Если `a = b`, то `a` можно заменить на `b` в корректном выражении. | В пределах одной формальной системы. | logic.identity |
| `math.order.transitive` | RULE | Транзитивность порядка: из `a ≤ b` и `b ≤ c` следует `a ≤ c`. | Для транзитивных отношений порядка. | logic.transitivity |
| `math.arithmetic.associative_add` | LAW | `(a + b) + c = a + (b + c)`. | Для стандартных числовых структур, где сложение ассоциативно. | algebra |
| `math.arithmetic.distributive` | LAW | `a(b + c) = ab + ac`. | В кольцах, полях и стандартной арифметике. | algebra |
| `math.number.prime` | TERM | Простое число имеет ровно два положительных делителя: 1 и само себя. | Обычно для натуральных чисел больше 1. | divisibility |
| `math.divisibility.gcd` | TERM | НОД двух чисел — наибольшее число, делящее оба без остатка. | Для целых чисел. | euclid_algorithm |
| `math.linear_equation` | METHOD | Уравнение `ax + b = 0` при `a ≠ 0` имеет решение `x = -b/a`. | Не работает при `a = 0` без разбора случая. | algebra |
| `math.quadratic_formula` | METHOD | Для `ax²+bx+c=0`, `a≠0`, корни: `x=(-b±√(b²-4ac))/(2a)`. | Над вещественными числами число корней зависит от дискриминанта. | algebra |
| `math.pythagorean_theorem` | THEOREM | В прямоугольном треугольнике `a² + b² = c²`. | Только евклидова геометрия, прямой угол. | geometry, engineering.survey |
| `math.trigonometry.sine` | TERM | `sin(θ)` в прямоугольном треугольнике = противолежащий катет / гипотенуза. | Базовое определение для прямоугольного треугольника; расширяется через окружность. | geography.navigation |
| `math.trigonometry.cosine` | TERM | `cos(θ)` = прилежащий катет / гипотенуза. | См. ограничения синуса. | navigation, physics.vector |
| `math.trigonometry.tangent` | TERM | `tan(θ)=sin(θ)/cos(θ)`. | Не определена при `cos(θ)=0`. | slope, road_design |
| `math.geometry.area_circle` | FORMULA | Площадь круга `A = πr²`. | Евклидова геометрия. | engineering.pipe |
| `math.geometry.volume_cylinder` | FORMULA | Объём цилиндра `V = πr²h`. | Идеализированная форма. | tanks, pipes |
| `math.calculus.derivative` | TERM | Производная показывает мгновенную скорость изменения функции. | Требуется предел; не все функции дифференцируемы. | physics.velocity |
| `math.calculus.integral` | TERM | Интеграл может представлять накопленную величину или площадь под графиком. | Требуется выбранный тип интеграла и условия интегрируемости. | work, probability |
| `math.vector.dot_product` | FORMULA | Скалярное произведение `a·b = |a||b|cosθ`. | В евклидовом пространстве. | physics.work |
| `math.matrix.linear_system` | METHOD | Линейные системы можно записывать как `Ax=b`. | Решение зависит от ранга и обратимости матрицы. | engineering.simulation |
| `logic.identity` | LAW | Закон тождества: `A` есть `A`. | Классическая логика. | math.equality |
| `logic.non_contradiction` | LAW | `A` и `¬A` не могут быть истинны одновременно в одном смысле и контексте. | Классическая логика; параконсистентные логики допускают иное обращение с противоречиями. | truth_gate |
| `logic.excluded_middle` | LAW | `A ∨ ¬A`. | Классическая логика; в интуиционистской логике ограничено. | proof |
| `logic.modus_ponens` | INFERENCE_RULE | Modus ponens (прямой вывод): из `A → B` и `A` следует `B`. | Дедуктивный вывод. | reasoning.deductive |
| `logic.modus_tollens` | INFERENCE_RULE | Если `A → B` и `¬B`, то `¬A`. | Дедуктивный вывод. | falsification |
| `logic.hypothetical_syllogism` | INFERENCE_RULE | Гипотетический силлогизм: из `A→B` и `B→C` следует `A→C`. | Цепочка импликаций. | causal_chain |
| `logic.disjunctive_syllogism` | INFERENCE_RULE | Дизъюнктивный силлогизм: из `A∨B` и `¬A` следует `B`. | Классическая логика. | decision |
| `logic.de_morgan.1` | LAW | Закон де Моргана (отрицание конъюнкции): `¬(A ∧ B) = ¬A ∨ ¬B`. | Булева логика. | circuits |
| `logic.de_morgan.2` | LAW | Закон де Моргана (отрицание дизъюнкции): `¬(A ∨ B) = ¬A ∧ ¬B`. | Булева логика. | circuits |
| `logic.contraposition` | INFERENCE_RULE | `A→B` эквивалентно `¬B→¬A` в классической логике. | Не все логики принимают без ограничений. | proof |
| `logic.universal_instantiation` | INFERENCE_RULE | Из `∀x P(x)` следует `P(a)` для конкретного `a`. | При корректной области дискурса. | predicate_logic |
| `logic.existential_introduction` | INFERENCE_RULE | Из `P(a)` следует `∃x P(x)`. | При наличии объекта `a` в области. | predicate_logic |
| `logic.proof_by_contradiction` | METHOD | Чтобы доказать `A`, допускают `¬A` и выводят противоречие. | Классическая логика; осторожно в конструктивных системах. | math.proof |
| `logic.induction_math` | METHOD | Если база верна и шаг `n→n+1` верен, утверждение верно для всех натуральных `n`. | Для утверждений над натуральными числами. | math.natural |
| `logic.induction_empirical` | METHOD | Обобщение из наблюдений даёт вероятный, но не строгий вывод. | Может быть опровергнуто новым наблюдением. | science |
| `logic.abduction` | METHOD | Абдукция выбирает лучшее объяснение наблюдения. | Не гарантирует истинность; требует проверки. | diagnosis |
| `logic.bayesian_update` | METHOD | Новые данные обновляют вероятность гипотезы через prior, likelihood и posterior. | Требуются вероятностная модель и допущения. | statistics |
| `logic.causal_intervention` | METHOD | Причинный вопрос спрашивает не только "связано ли", а "что будет, если вмешаться". | Требуется causal model; корреляции недостаточно. | world_model |
| `logic.modal.necessity` | LOGIC_TYPE | Модальная логика различает необходимость и возможность. | Значение зависит от типа модальности. | philosophy |
| `logic.temporal` | LOGIC_TYPE | Временная логика описывает, что было, есть, будет или всегда/иногда истинно. | Важна для систем, событий и верификации программ. | bi_temporal |
| `logic.deontic` | LOGIC_TYPE | Деонтическая логика описывает обязанное, разрешённое и запрещённое. | Нормативная логика; не равна фактической истинности. | ethics, safety |
| `logic.epistemic` | LOGIC_TYPE | Эпистемическая логика описывает знание и убеждения агентов. | Не заменяет проверку источников. | trace, agent |
| `logic.paraconsistent` | LOGIC_TYPE | Параконсистентная логика позволяет работать с противоречиями без полного логического взрыва. | Полезна для конфликтующих баз знаний; требует маркировки противоречий. | inconsistency_hunter |
| `stats.mean` | FORMULA | Среднее арифметическое = сумма значений / число значений. | Чувствительно к выбросам. | data_analysis |
| `stats.median` | METHOD | Медиана делит упорядоченный набор пополам. | Устойчива к выбросам. | robust_stats |
| `stats.variance` | FORMULA | Дисперсия измеряет средний квадрат отклонения от среднего. | Единицы измерения возводятся в квадрат. | uncertainty |
| `stats.correlation_not_causation` | CONSTRAINT | Корреляция не доказывает причинность. | Возможны скрытые переменные и обратная причинность. | causal_model |
| `stats.conditional_probability` | FORMULA | Условная вероятность: `P(A|B)=P(A∧B)/P(B)` при `P(B)>0`. | Требуется корректная вероятность события B. | bayes |
| `info.entropy` | FORMULA | Энтропия Шеннона измеряет неопределённость распределения. | Не равна физической энтропии без уточнения. | compression |
| `cs.algorithm` | TERM | Алгоритм — конечная процедура решения класса задач. | Должны быть определены вход, шаги и завершение. | computation |
| `cs.complexity.big_o` | METHOD | Big-O описывает асимптотический рост затрат алгоритма. | Скрывает константы и реальные аппаратные эффекты. | performance |
| `cs.database.index` | MECHANISM | Индекс ускоряет поиск ценой дополнительной памяти и стоимости обновления. | Неподходящий индекс может не помочь запросу. | retrieval |
| `cs.hash.sha256` | METHOD | SHA-256 даёт криптографический дайджест фиксированной длины. | Хэш не шифрует данные и не доказывает истинность содержимого. | audit_chain |

