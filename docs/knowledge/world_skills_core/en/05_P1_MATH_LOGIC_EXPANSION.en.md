# 🧮 P1 Math & Logic Expansion — расширение формального ядра

**Язык:** русский  
**Статус:** seed pack v0.2 / не L3 truth  
**Назначение:** расширить формальную базу: алгебра, геометрия, тригонометрия, анализ, вероятность, дискретная математика, логика и вычисления.

---

## 📦 Knowledge Units

| ID | Тип | Суть | Условия / границы | Связи |
|---|---|---|---|---|
| `math.algebra.group` | STRUCTURE | Группа — множество с ассоциативной операцией, нейтральным элементом и обратными. | Операция должна быть замкнута. | symmetry |
| `math.algebra.ring` | STRUCTURE | Кольцо имеет сложение, умножение и distributive laws. | Умножение не обязано быть коммутативным. | algebra |
| `math.algebra.field` | STRUCTURE | Поле позволяет сложение, вычитание, умножение и деление на ненулевые элементы. | Деление на ноль запрещено. | equations |
| `math.algebra.polynomial` | TERM | Полином — сумма степеней переменной с коэффициентами. | Область коэффициентов важна. | equations |
| `math.algebra.factorization` | METHOD | Факторизация раскладывает выражение на множители. | Не всегда проста или единственна вне специальных областей. | simplification |
| `math.algebra.logarithm` | TERM | Логарифм отвечает, в какую степень нужно возвести основание. | Основание положительно и не равно 1; аргумент положителен. | exponential |
| `math.algebra.exponential_growth` | MODEL | Экспоненциальный рост пропорционален текущему значению. | В реальности ограничивается ресурсами. | biology, finance |
| `math.algebra.linear_function` | MODEL | Линейная функция имеет вид `y=ax+b`. | Описывает постоянную скорость изменения. | modeling |
| `math.algebra.system_equations` | METHOD | Система уравнений описывает несколько ограничений одновременно. | Решения зависят от совместности и независимости уравнений. | engineering |
| `math.geometry.point_line_plane` | TERM | Точка, прямая и плоскость — базовые объекты евклидовой геометрии. | Идеализации, не физические объекты. | geometry |
| `math.geometry.parallel_lines` | TERM | Параллельные прямые в евклидовой плоскости не пересекаются. | В неевклидовой геометрии иначе. | maps |
| `math.geometry.triangle_sum` | THEOREM | Сумма углов треугольника в евклидовой геометрии равна 180°. | На сфере сумма больше 180°. | geography |
| `math.geometry.similar_triangles` | THEOREM | Подобные треугольники имеют равные углы и пропорциональные стороны. | Основа измерения недоступных расстояний. | survey |
| `math.geometry.circle_circumference` | FORMULA | Длина окружности `C=2πr`. | Евклидова геометрия. | mechanics |
| `math.geometry.sphere_area` | FORMULA | Площадь сферы `A=4πr²`. | Идеальная сфера. | earth |
| `math.geometry.sphere_volume` | FORMULA | Объём сферы `V=4/3πr³`. | Идеальная сфера. | tanks |
| `math.trig.unit_circle` | MODEL | Единичная окружность расширяет sin/cos на любые углы. | Угол измеряется в радианах или градусах. | waves |
| `math.trig.radian` | TERM | Радиан — угол, при котором длина дуги равна радиусу. | `2π` радиан = 360°. | calculus |
| `math.trig.identity_pythagorean` | LAW | `sin²x + cos²x = 1`. | Из единичной окружности. | waves |
| `math.trig.law_of_sines` | THEOREM | `a/sin A = b/sin B = c/sin C`. | Для любого плоского треугольника. | navigation |
| `math.trig.law_of_cosines` | THEOREM | `c²=a²+b²-2ab cos C`. | Обобщает Пифагора. | survey |
| `math.trig.bearing` | METHOD | Направление на карте можно задавать углом относительно севера. | Требует системы координат и магнитной/истинной поправки. | geography |
| `math.calculus.limit` | TERM | Предел описывает значение, к которому стремится функция. | Может не существовать. | derivative |
| `math.calculus.continuity` | TERM | Непрерывность означает отсутствие разрыва в точке. | Формально через предел. | modeling |
| `math.calculus.chain_rule` | RULE | Производная композиции: `(f(g(x)))'=f'(g(x))g'(x)`. | Для дифференцируемых функций. | physics |
| `math.calculus.product_rule` | RULE | `(fg)'=f'g+fg'`. | Для дифференцируемых функций. | optimization |
| `math.calculus.fundamental_theorem` | THEOREM | Производная и интеграл связаны как обратные операции при условиях гладкости. | Требует корректных условий. | physics |
| `math.calculus.gradient` | TERM | Градиент указывает направление наибольшего роста функции. | Для скалярного поля. | optimization |
| `math.calculus.differential_equation` | MODEL | Дифференциальное уравнение связывает функцию и её производные. | Требует начальных/граничных условий. | dynamics |
| `math.probability.sample_space` | TERM | Пространство исходов содержит возможные результаты эксперимента. | Должно быть определено до вероятностей. | probability |
| `math.probability.independence` | TERM | События независимы, если `P(A∩B)=P(A)P(B)`. | Не путать с несовместимостью. | stats |
| `math.probability.bayes` | THEOREM | `P(H|E)=P(E|H)P(H)/P(E)`. | Требует ненулевого `P(E)`. | diagnosis |
| `math.probability.expected_value` | FORMULA | Матожидание — взвешенное среднее значений по вероятностям. | Может не существовать для некоторых распределений. | risk |
| `math.stats.confidence_interval` | METHOD | Доверительный интервал оценивает диапазон параметра по выборке. | Не означает вероятность нахождения уже фиксированного параметра в частотной трактовке. | uncertainty |
| `math.stats.p_value` | METHOD | p-value — вероятность получить такие или более экстремальные данные при нулевой гипотезе. | Не является вероятностью истинности гипотезы. | science |
| `math.stats.regression` | METHOD | Регрессия оценивает зависимость переменной от факторов. | Корреляция и подгонка не доказывают причинность. | causal |
| `math.discrete.graph` | STRUCTURE | Граф состоит из вершин и рёбер. | Рёбра могут быть направленными/взвешенными. | knowledge_graph |
| `math.discrete.tree` | STRUCTURE | Дерево — связный граф без циклов. | В rooted tree есть корень и иерархия. | memory_tree |
| `math.discrete.shortest_path` | METHOD | Кратчайший путь ищет минимальную стоимость между узлами. | Стоимость зависит от веса рёбер. | routing |
| `math.discrete.topological_sort` | METHOD | Топологическая сортировка упорядочивает DAG по зависимостям. | Невозможна при цикле. | tasks |
| `math.discrete.boolean_algebra` | STRUCTURE | Булева алгебра формализует операции AND, OR, NOT. | Основа цифровой логики. | circuits |
| `logic.formal_fallacy.affirming_consequent` | FALLACY | Из `A→B` и `B` нельзя выводить `A`. | Формальная ошибка. | reasoning |
| `logic.formal_fallacy.denying_antecedent` | FALLACY | Из `A→B` и `¬A` нельзя выводить `¬B`. | Формальная ошибка. | reasoning |
| `logic.informal_fallacy.strawman` | FALLACY | Соломенное чучело искажает позицию оппонента. | Ошибка аргументации. | debate |
| `logic.informal_fallacy.false_dilemma` | FALLACY | Ложная дилемма сводит выбор к двум вариантам без основания. | Нужно искать скрытые альтернативы. | decision |
| `logic.informal_fallacy.post_hoc` | FALLACY | "После этого" не значит "по причине этого". | Требуется причинная проверка. | causal |
| `logic.informal_fallacy.ad_hominem` | FALLACY | Атака на человека не опровергает аргумент. | Личность может быть релевантна только для credibility, не логической истинности. | argument |
| `logic.fuzzy` | LOGIC_TYPE | Нечёткая логика работает со степенями истинности. | Не равна вероятности. | control |
| `logic.default_reasoning` | METHOD | Вывод по умолчанию действует, пока нет исключений. | Немонотонный: новое знание может отменить вывод. | common_sense |
| `logic.non_monotonic` | LOGIC_TYPE | В немонотонной логике добавление фактов может отменять старые выводы. | Полезно для реального мира с исключениями. | AI |
| `cs.turing_machine` | MODEL | Машина Тьюринга — абстрактная модель вычисления. | Не модель реального железа, а формальная мощность. | computability |
| `cs.halting_problem` | THEOREM | Нет общего алгоритма, решающего остановку любой программы. | Классический результат неразрешимости. | limits |
| `cs.recursion` | METHOD | Рекурсия решает задачу через вызов самой себя на меньшем случае. | Нужна база остановки. | algorithms |
| `cs.sorting` | METHOD | Сортировка упорядочивает элементы по критерию. | Алгоритмы имеют разные сложности и устойчивость. | data |
| `cs.search.binary` | METHOD | Бинарный поиск работает за `O(log n)` по отсортированному массиву. | Требуется сортировка и random access. | algorithms |
| `cs.cache` | MECHANISM | Кэш ускоряет повторный доступ к данным, храня копии ближе к вычислению. | Требует invalidation strategy. | performance |
| `cs.concurrency.race_condition` | FAILURE_MODE | Race condition возникает, когда результат зависит от порядка одновременных операций. | Нужны блокировки, транзакции или атомарность. | reliability |
| `cs.transaction.acid` | PRINCIPLE | ACID: atomicity, consistency, isolation, durability. | Реальные БД выбирают компромиссы. | databases |

