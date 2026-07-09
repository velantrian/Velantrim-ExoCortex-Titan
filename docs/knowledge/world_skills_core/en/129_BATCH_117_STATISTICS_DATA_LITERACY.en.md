# BATCH_117 — Statistics & Data Literacy: Charts, Averages, Misleading Data
# world_skills_core · source: world_skills_core:batch_117:data_literacy
# KnowledgeUnits: 42

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| stats.data.types | Типы данных | invariant | числовые (количественные) и категориальные | выбор анализа |
| stats.data.population_sample | Генеральная совокупность и выборка | invariant | целое vs изучаемая часть | основа статистики |
| stats.data.sampling | Репрезентативная выборка | invariant | должна отражать совокупность | достоверность выводов |
| stats.center.mean | Среднее арифметическое | invariant | сумма / количество | мера центра, чувствительна к выбросам |
| stats.center.median | Медиана | invariant | серединное значение; устойчива к выбросам | лучше для зарплат, цен |
| stats.center.mode | Мода | invariant | самое частое значение | категориальные данные |
| stats.center.mean_vs_median | Среднее vs медиана | invariant | при перекосе они расходятся | манипуляция «средним» |
| stats.spread.range | Размах | variant | макс − мин | грубая мера разброса |
| stats.spread.variance_sd | Дисперсия и СКО | invariant | мера разброса вокруг среднего | изменчивость |
| stats.spread.iqr | Межквартильный размах | variant | разброс средних 50% данных | устойчив к выбросам |
| stats.spread.outlier | Выбросы | invariant | аномальные значения искажают среднее | проверять, не игнорировать слепо |
| stats.dist.normal | Нормальное распределение | invariant | колокол; правило 68-95-99.7 | естественная изменчивость |
| stats.dist.skew | Асимметрия (перекос) | variant | хвост влево/вправо смещает среднее | интерпретация |
| stats.percent.basics | Проценты | invariant | доля от целого ×100 | повсеместно |
| stats.percent.change | Процентное изменение | invariant | (нов−стар)/стар; рост на 50% ≠ падение на 50% | манипуляция |
| stats.percent.points | Процентные пункты vs проценты | invariant | с 10% до 12% = +2 п.п. = +20% относительно | частая путаница |
| stats.prob.basics | Вероятность | invariant | шанс события 0–1 | оценка риска |
| stats.prob.gambler | Ошибка игрока | invariant | прошлые независимые исходы не влияют на будущие | защита от заблуждения |
| stats.prob.base_rate | Базовая частота | invariant | игнор базовой вероятности → ошибки (тесты) | медицина, оценка |
| stats.corr.correlation | Корреляция | invariant | связь величин (−1…+1) | анализ зависимостей |
| stats.corr.not_causation | Корреляция ≠ причинность | invariant | связь не доказывает причину | критическое мышление |
| stats.corr.confounder | Скрытая переменная | invariant | третий фактор объясняет «связь» | ложные выводы |
| stats.infer.significance | Статистическая значимость | invariant | вероятность случайности (p-value) | научный вывод |
| stats.infer.pvalue_trap | Ловушка p-value | variant | значимость ≠ важность; p-hacking | критика исследований |
| stats.infer.confidence_interval | Доверительный интервал | invariant | диапазон вероятного значения | оценка неопределённости |
| stats.infer.sample_size | Размер выборки | invariant | малая выборка → ненадёжно | доверие к результату |
| stats.chart.bar | Столбчатая диаграмма | invariant | сравнение категорий | чтение данных |
| stats.chart.line | Линейный график | invariant | тренд во времени | динамика |
| stats.chart.pie | Круговая диаграмма | variant | доли целого; плохо при многих категориях | ограничения |
| stats.chart.scatter | Диаграмма рассеяния | invariant | связь двух величин | корреляция визуально |
| stats.chart.histogram | Гистограмма | variant | распределение числовых данных | форма данных |
| stats.mislead.truncated_axis | Обрезанная ось | invariant | ось не с нуля преувеличивает различия | манипуляция графиком |
| stats.mislead.cherry_pick | Выборочные данные | invariant | показ только удобного периода/группы | искажение |
| stats.mislead.scale | Манипуляция масштабом | variant | растяжение/сжатие осей искажает тренд | критическое чтение |
| stats.mislead.average_abuse | Злоупотребление «средним» | invariant | среднее при перекосе вводит в заблуждение | требовать медиану/разброс |
| stats.mislead.small_n | Малые числа в процентах | variant | «рост на 100%» при 1→2 случая | контекст абсолютных чисел |
| stats.mislead.survivorship | Ошибка выжившего | invariant | данные только об «уцелевших» | неполная картина |
| stats.mislead.simpson | Парадокс Симпсона | variant | тренд в группах исчезает/меняется при объединении | осторожность с агрегацией |
| stats.read.context | Контекст данных | invariant | кто собрал, как, когда, зачем | оценка достоверности |
| stats.read.absolute_relative | Абсолютные vs относительные числа | invariant | «вдвое больше» без базы бессмысленно | полная картина |
| stats.read.source | Источник статистики | invariant | конфликт интересов искажает | критическая оценка |
| stats.literacy.value | Статистическая грамотность | invariant | защита от манипуляций числами | решения на данных |
