# 🧮 Batch 040 — Applied Math, Decisions & Quantitative Life

**Язык:** русский  
**Статус:** 50K batch 040 / seed units / не L3 truth  
**Цель:** добавить прикладную математику повседневного и инженерного мышления: оценки, проценты, модели, вероятность, таблицы, риски и решения.

---

## 📦 Knowledge Units

| ID | Тип | Суть | Условия / границы | Связи |
|---|---|---|---|---|
| `appmath.unit_conversion` | METHOD | Перевод единиц сохраняет физическую величину при смене масштаба. | Ошибки единиц приводят к авариям и неверным покупкам. | measurement |
| `appmath.dimensional_analysis` | METHOD | Анализ размерностей проверяет, совместимы ли формулы по единицам. | Не доказывает физическую истинность формулы. | physics |
| `appmath.estimation` | METHOD | Оценка даёт полезный порядок величины без точного расчёта. | Нужно знать допустимую погрешность. | reasoning |
| `appmath.fermi_estimate` | METHOD | Fermi estimate разбивает неизвестное число на грубые множители. | Хорош для sanity check. | estimation |
| `appmath.percentage_change` | METHOD | Процентное изменение показывает относительную разницу между значениями. | База сравнения критична. | finance |
| `appmath.compound_growth` | MODEL | Сложный рост умножает результат на результат предыдущего периода. | Малые проценты важны на длинном времени. | finance |
| `appmath.linear_model` | MODEL | Линейная модель предполагает постоянный прирост на единицу входа. | Часто ломается за пределами диапазона. | modeling |
| `appmath.exponential_model` | MODEL | Экспоненциальная модель описывает рост/убывание пропорционально текущему значению. | Не может продолжаться бесконечно в реальном мире. | systems |
| `appmath.log_scale` | MODEL | Логарифмическая шкала показывает кратные изменения как равные шаги. | Полезна для звука, землетрясений, pH, графиков. | math |
| `appmath.ratio_proportion` | METHOD | Пропорция связывает две величины постоянным отношением. | Работает только при линейной зависимости. | math |
| `appmath.weighted_average` | METHOD | Взвешенное среднее учитывает разную важность или массу элементов. | Весы должны суммироваться и иметь смысл. | statistics |
| `appmath.moving_average` | METHOD | Скользящее среднее сглаживает шум временного ряда. | Запаздывает за резкими изменениями. | data |
| `appmath.interpolation` | METHOD | Интерполяция оценивает значение между известными точками. | Безопаснее экстраполяции. | data |
| `appmath.extrapolation_risk` | RISK | Экстраполяция продолжает тренд за пределы данных. | Высокий риск ошибки при смене режима. | modeling |
| `appmath.constraint_optimization` | METHOD | Оптимизация с ограничениями ищет лучшее решение среди допустимых. | Неверная objective function портит результат. | decision |
| `appmath.break_even_graph` | MODEL | Break-even graph показывает точку, где доходы равны затратам. | Зависит от предположений о цене и объёме. | finance |
| `appmath.sensitivity_table` | METHOD | Таблица чувствительности показывает, как итог меняется от входов. | Помогает найти ключевые факторы. | modeling |
| `appmath.error_propagation` | METHOD | Ошибки измерений распространяются через расчёты. | Нелинейные формулы сложнее. | measurement |
| `appmath.measurement_uncertainty` | MODEL | Неопределённость измерения даёт диапазон доверия к результату. | Нужно не прятать её в отчёте. | metrology |
| `appmath.probability_base_rate` | PRINCIPLE | Base rate задаёт исходную вероятность события до новой информации. | Игнорирование base rate искажает вывод. | probability |
| `appmath.conditional_probability` | METHOD | Условная вероятность оценивает событие при известном условии. | P(A|B) не равно P(B|A). | probability |
| `appmath.bayes_update` | METHOD | Bayes update обновляет вероятность при новом evidence. | Нужны prior и likelihood. | reasoning |
| `appmath.expected_value` | MODEL | Expected value умножает outcomes на их probabilities. | Не учитывает риск-аверсию и tail risk. | decision |
| `appmath.variance` | METRIC | Variance показывает разброс вокруг среднего. | Единицы квадратичные, часто используют standard deviation. | statistics |
| `appmath.normal_distribution` | MODEL | Normal distribution описывает многие шумовые величины вокруг среднего. | Не подходит для всех данных. | statistics |
| `appmath.percentile` | METRIC | Percentile показывает позицию значения в распределении. | Лучше среднего для skewed data. | statistics |
| `appmath.correlation_regression` | METHOD | Регрессия оценивает связь между переменными. | Не доказывает причинность. | statistics |
| `appmath.sampling_bias` | FAILURE_MODE | Смещённая выборка не представляет целевую группу. | Большой размер не исправляет bias. | statistics |
| `appmath.confidence_interval_reading` | METHOD | Интервал доверия лучше читать как диапазон совместимых значений модели. | Не как точную вероятность для уже посчитанного интервала. | statistics |
| `appmath.decision_tree` | TOOL | Decision tree раскладывает варианты, вероятности и outcomes. | Быстро растёт в сложных задачах. | decision |
| `appmath.utility_score` | MODEL | Utility score переводит разные критерии в сравнимую оценку. | Веса субъективны. | decision |
| `appmath.monte_carlo_simple` | METHOD | Monte Carlo прогоняет много случайных сценариев для распределения результатов. | Зависит от входных distributions. | simulation |
| `appmath.littles_law` | MODEL | Little's law связывает средний WIP, throughput и lead time. | Работает в стабильной системе. | queue |
| `appmath.geometry_area` | METHOD | Площадь измеряет двумерный размер поверхности. | Единицы должны быть квадратными. | geometry |
| `appmath.geometry_volume` | METHOD | Объём измеряет трёхмерную вместимость. | Важен для воды, бетона, склада. | geometry |
| `appmath.trig_slope_angle` | METHOD | Тригонометрия связывает угол, высоту и расстояние. | Полезна для крыш, дорог, карт. | trigonometry |
| `appmath.map_scale_distance` | METHOD | Масштаб карты переводит расстояние на карте в реальную длину. | Проекция может искажать расстояния. | geography |
| `appmath.vector_components` | METHOD | Вектор можно разложить на компоненты по осям. | Полезно для сил, скорости, навигации. | physics |
| `appmath.spreadsheet_formula` | TOOL | Формула таблицы автоматизирует повторный расчёт. | Ошибки ячеек трудно заметить. | spreadsheets |
| `appmath.spreadsheet_pivot` | TOOL | Pivot table группирует и агрегирует данные. | Результат зависит от чистоты данных. | data |
| `appmath.chart_axis_misleading` | FAILURE_MODE | Обрезанная или нелинейная ось может визуально преувеличить эффект. | Нужно читать шкалы. | data_literacy |
| `appmath.data_cleaning_missing` | METHOD | Missing values нужно обрабатывать явно: удалить, заполнить, пометить. | Выбор влияет на вывод. | data |
| `appmath.scenario_budget` | METHOD | Сценарный бюджет считает optimistic, base и pessimistic варианты. | Уменьшает ложную точность. | finance |
| `appmath.quant_risk_matrix` | TOOL | Количественная risk matrix переводит риски в сопоставимые категории. | Категории должны быть определены. | risk |
| `appmath.back_of_envelope` | METHOD | Back-of-envelope calculation быстро проверяет правдоподобность идеи. | Не заменяет финальный расчёт. | reasoning |

---

## 📊 Batch 040 summary

```text
new units: 45
main layers:
  estimation, models and uncertainty
  probability, statistics and decisions
  geometry, spreadsheets and risk
```
