# 🔬 Batch 021 — Research, Laboratories, Standards & Evidence

**Язык:** русский  
**Статус:** 50K batch 021 / seed units / не L3 truth  
**Цель:** добавить слой научной проверки: как строят эксперименты, измеряют, публикуют, воспроизводят, стандартизируют и оценивают доказательства.

---

## 📦 Knowledge Units

| ID | Тип | Суть | Условия / границы | Связи |
|---|---|---|---|---|
| `research.question` | METHOD | Исследовательский вопрос задаёт, что именно нужно узнать. | Слишком широкий вопрос не проверяется. | science |
| `research.hypothesis` | METHOD | Гипотеза — проверяемое предположение о связи или механизме. | Должна допускать опровержение. | logic |
| `research.null_hypothesis` | MODEL | Нулевая гипотеза задаёт отсутствие эффекта или различия. | Не доказывается простым p-value. | statistics |
| `research.operational_definition` | METHOD | Операциональное определение переводит абстрактное понятие в измеряемую процедуру. | Может сузить смысл понятия. | measurement |
| `research.variable_independent` | TERM | Независимая переменная — фактор, которым управляют или который сравнивают. | В наблюдательных данных контроль ограничен. | experiment |
| `research.variable_dependent` | TERM | Зависимая переменная — измеряемый результат. | Должна быть связана с вопросом. | experiment |
| `research.control_group` | METHOD | Контрольная группа задаёт базу сравнения. | Плохой контроль искажает вывод. | experiment |
| `research.randomization` | METHOD | Рандомизация распределяет скрытые факторы между группами. | Не гарантирует баланс в малой выборке. | statistics |
| `research.blinding` | METHOD | Ослепление снижает влияние ожиданий участника или исследователя. | Не всегда возможно технически. | bias |
| `research.placebo` | METHOD | Placebo помогает отделить эффект вмешательства от ожиданий и контекста. | Не для всех исследований этично. | clinical |
| `research.sample_size` | DESIGN_CONSTRAINT | Размер выборки влияет на способность обнаружить эффект. | Большая выборка не спасает плохой дизайн. | statistics |
| `research.power_analysis` | METHOD | Power analysis оценивает шанс обнаружить эффект заданного размера. | Требует предположений об эффекте и вариации. | statistics |
| `research.effect_size` | METRIC | Effect size показывает величину эффекта, а не только его статистическую заметность. | Практическая значимость зависит от контекста. | statistics |
| `research.confidence_interval` | METRIC | Confidence interval показывает диапазон совместимый с данными и моделью. | Не равен вероятности, что параметр внутри для конкретного интервала. | statistics |
| `research.p_value` | METRIC | p-value оценивает данные при условии нулевой гипотезы. | Не измеряет вероятность истинности гипотезы. | statistics |
| `research.multiple_testing` | RISK | Много проверок повышают шанс ложноположительных находок. | Нужны коррекции или preregistration. | statistics |
| `research.preregistration` | METHOD | Preregistration фиксирует план анализа до данных. | Не запрещает exploratory analysis, но отделяет его. | open_science |
| `research.replication` | QUALITY_CHECK | Репликация проверяет, повторяется ли результат в новых условиях. | Неудача репликации требует анализа причин. | evidence |
| `research.reproducibility` | QUALITY_CHECK | Reproducibility позволяет получить тот же результат из тех же данных/кода. | Требует доступных материалов и среды. | data |
| `research.peer_review` | QUALITY_PROCESS | Peer review оценивает работу до публикации экспертами. | Не гарантирует истинность. | publishing |
| `research.preprint` | PUBLICATION_STAGE | Preprint быстро распространяет работу до формального рецензирования. | Требует осторожности в claims. | science |
| `research.systematic_review` | EVIDENCE_METHOD | Systematic review ищет и оценивает исследования по заранее заданному протоколу. | Качество зависит от включённых работ. | evidence |
| `research.meta_analysis` | EVIDENCE_METHOD | Meta-analysis количественно объединяет результаты исследований. | Heterogeneity может ограничить вывод. | statistics |
| `research.case_study` | METHOD | Case study глубоко описывает один случай или объект. | Ограниченная обобщаемость. | research |
| `research.cohort_study` | METHOD | Cohort study наблюдает группу во времени по экспозициям и исходам. | Уязвимо к confounding. | epidemiology |
| `research.cross_sectional` | METHOD | Cross-sectional study измеряет состояние в один момент. | Плохо устанавливает причинность. | survey |
| `research.qualitative_interview` | METHOD | Интервью раскрывает опыт, смысл и контекст участников. | Не предназначено для простой статистической обобщаемости. | social_science |
| `research.ethics.irb` | GOVERNANCE | Ethics board/IRB оценивает риск для участников исследования. | Требования зависят от страны и области. | ethics |
| `research.consent` | ETHICS_RULE | Участник должен понимать цель, риски и право отказаться. | Уязвимые группы требуют особой защиты. | ethics |
| `research.data_anonymization` | PRIVACY_METHOD | Анонимизация снижает риск идентификации участников. | Полная анонимность сложна при богатых данных. | privacy |
| `research.data_management_plan` | DOCUMENT | DMP описывает сбор, хранение, доступ, backup и публикацию данных. | Нужен до старта проекта. | data |
| `research.lab_notebook` | RECORD | Лабораторный журнал фиксирует действия, условия, результаты и отклонения. | Должен быть датирован и проверяем. | trace |
| `research.protocol` | DOCUMENT | Протокол описывает процедуру исследования или эксперимента. | Изменения надо документировать. | QA |
| `research.deviation_log` | RECORD | Deviation log фиксирует отклонения от протокола и их влияние. | Скрытые отклонения портят trust. | quality |
| `research.reagent_lot` | TRACE | Партия реагента влияет на воспроизводимость и должна отслеживаться. | Особенно важно для биологии и химии. | lab |
| `research.sample_chain_of_custody` | TRACE | Chain of custody показывает, кто и когда держал образец. | Важно для судов, медицины, экологии. | audit |
| `research.positive_control` | QUALITY_CHECK | Positive control должен дать ожидаемый положительный результат. | Показывает, что система способна обнаружить эффект. | lab |
| `research.negative_control` | QUALITY_CHECK | Negative control показывает фон и загрязнение. | Если он положительный, эксперимент под вопросом. | lab |
| `research.blank_control` | QUALITY_CHECK | Blank control проверяет реактивы и среду без образца. | Помогает найти contamination. | chemistry |
| `research.standard_curve` | METHOD | Standard curve связывает сигнал прибора с известными концентрациями. | Нужен рабочий диапазон и quality points. | lab |
| `research.limit_of_detection` | METRIC | LOD — минимальный уровень, который метод может обнаружить. | Обнаружить не значит точно измерить. | metrology |
| `research.limit_of_quantification` | METRIC | LOQ — минимальный уровень, который метод может измерить с приемлемой точностью. | Выше LOD. | metrology |
| `research.assay_validation` | QUALITY_CHECK | Validation assay оценивает specificity, sensitivity, precision, accuracy, range. | Критично для диагностики и QC. | lab |
| `research.interlaboratory_comparison` | QUALITY_CHECK | Межлабораторное сравнение проверяет согласованность результатов разных лабораторий. | Требует одинаковых образцов и правил. | standards |
| `research.reference_material` | STANDARD | Reference material имеет известные свойства для проверки метода. | Нужна прослеживаемость и сертификат. | metrology |
| `research.standard_operating_procedure` | DOCUMENT | SOP делает лабораторный процесс повторяемым. | Нужны обучение и version control. | quality |
| `research.good_laboratory_practice` | QUALITY_SYSTEM | GLP управляет качеством доклинических и лабораторных данных. | Не равно GMP. | regulation |
| `research.biosafety_level` | SAFETY_SYSTEM | Biosafety levels задают containment для биологических рисков. | Зависят от агента и процедуры. | biosafety |
| `research.chemical_hygiene_plan` | SAFETY_SYSTEM | Chemical hygiene plan описывает безопасную работу с химическими веществами. | Должен быть локальным и актуальным. | lab_safety |
| `research.fume_hood` | SAFETY_EQUIPMENT | Вытяжной шкаф защищает от паров и аэрозолей при правильной работе. | Не склад и не универсальная защита. | safety |
| `research.autoclave` | EQUIPMENT | Автоклав использует пар под давлением для стерилизации. | Требует валидации цикла и safety. | lab |
| `research.centrifuge_balance` | SAFETY_RULE | Центрифуга требует балансировки ротора и совместимых пробирок. | Дисбаланс опасен. | lab_safety |
| `research.cold_storage` | EQUIPMENT | Морозильники и холодильники хранят образцы при заданной температуре. | Нужны alarms и backup plan. | lab |
| `research.instrument_qualification` | QUALITY_CHECK | IQ/OQ/PQ подтверждают установку, работу и пригодность прибора. | Термины зависят от системы качества. | validation |
| `research.audit_trail` | TRACE | Audit trail фиксирует изменения данных, пользователя и время. | Защищает от скрытой правки. | data_integrity |
| `research.alcoa_plus` | PRINCIPLE | ALCOA+ описывает целостность данных: attributable, legible, contemporaneous, original, accurate и др. | Важно в regulated science. | quality |
| `research.publication.bias` | BIAS | Publication bias возникает, когда положительные результаты публикуются чаще. | Искажает reviews и meta-analysis. | evidence |
| `research.conflict_of_interest` | RISK | Финансовые или личные интересы могут влиять на дизайн, анализ или вывод. | Нужно раскрывать и управлять. | ethics |
| `research.retraction` | EVENT | Retraction отзывает публикацию из-за ошибок, misconduct или недостоверности. | Не всегда означает намеренный обман. | publishing |
| `research.citation_graph` | MODEL | Citation graph показывает связи работ через ссылки. | Цитирование не равно качество. | science |
| `research.consensus` | MODEL | Scientific consensus — устойчивое согласие экспертов по совокупности доказательств. | Может меняться с новыми данными. | epistemology |
| `research.uncertainty_disclosure` | COMMUNICATION_RULE | Научный вывод должен показывать неопределённость и ограничения. | Слишком уверенный язык искажает trust. | communication |
| `research.open_data` | PRACTICE | Open data позволяет проверку, reuse и meta-analysis. | Ограничивается privacy, safety, IP. | open_science |
| `research.open_source_code` | PRACTICE | Открытый код облегчает проверку анализа. | Нужны версии, зависимости и лицензия. | software |
| `research.protocol_registry` | SYSTEM | Регистры протоколов уменьшают selective reporting. | Запись должна быть до результата. | evidence |
| `research.evidence_grade` | MODEL | Evidence grade оценивает качество доказательств по дизайну, bias, consistency и directness. | Не заменяет экспертизу домена. | quality_layer |

---

## 📊 Batch 021 summary

```text
new units: 66
main layers:
  research design and statistics
  evidence quality and publication
  laboratory quality systems
  safety, traceability and standards
```
