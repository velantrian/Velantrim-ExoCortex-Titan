# BATCH_134 — Educational Assessment Design
# world_skills_core · source: world_skills_core:batch_134:educational_assessment_design
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| edassess.learning_objective | Learning objective | invariant | Учебная цель описывает, что учащийся сможет сделать наблюдаемо после обучения. | оценивать действие, а не тему |
| edassess.alignment | Assessment alignment | invariant | Оценивание должно соответствовать учебным целям, уровню сложности и реально изучавшимся заданиям. | честная проверка |
| edassess.construct_validity | Construct validity | invariant | Construct validity показывает, измеряет ли задание именно целевое умение, а не посторонние навыки. | тест не должен мерить шум |
| edassess.content_validity | Content validity | invariant | Content validity требует, чтобы оценивание покрывало важные части содержания, а не случайный узкий фрагмент. | репрезентативность |
| edassess.formative_assessment | Formative assessment | invariant | Формирующее оценивание дает обратную связь во время обучения, чтобы изменить дальнейшие действия ученика и преподавателя. | учить до итоговой оценки |
| edassess.summative_assessment | Summative assessment | invariant | Итоговое оценивание фиксирует достигнутый уровень после периода обучения или модуля. | сертификация результата |
| edassess.diagnostic_assessment | Diagnostic assessment | invariant | Диагностическое оценивание ищет стартовые пробелы, неверные представления и готовность к новой теме. | подобрать маршрут обучения |
| edassess.rubric_analytic | Analytic rubric | invariant | Аналитическая рубрика оценивает работу по нескольким критериям отдельно, а не одной общей оценкой. | понятная обратная связь |
| edassess.rubric_holistic | Holistic rubric | variant | Холистическая рубрика дает общую оценку качества работы по целостному впечатлению и описанию уровней. | быстрее, но менее диагностично |
| edassess.criteria_level | Rubric performance level | invariant | Уровень рубрики должен описывать наблюдаемое качество работы, а не просто слова вроде хорошо или плохо. | снижает субъективность |
| edassess.item_stem_clarity | Item stem clarity | invariant | Формулировка вопроса должна ясно задавать задачу без лишней двусмысленности и скрытых ловушек. | честный вопрос |
| edassess.distractor_quality | Distractor quality | invariant | Хороший distractor в тесте правдоподобен для типичной ошибки, но не является спорно правильным. | выявлять заблуждения |
| edassess.answer_key_rationale | Answer key rationale | invariant | Ключ ответа должен иметь объяснение, почему вариант верен и почему альтернативы неверны. | проверка качества задания |
| edassess.item_difficulty | Item difficulty | invariant | Сложность задания оценивают по доле учащихся, ответивших правильно, с учетом уровня группы. | калибровка теста |
| edassess.item_discrimination | Item discrimination | invariant | Дискриминативность задания показывает, насколько оно различает учащихся с разным уровнем владения материалом. | убрать плохие вопросы |
| edassess.guessing_risk | Guessing risk | variant | Риск угадывания зависит от формата задания, числа вариантов и возможности исключить неверные ответы. | интерпретация теста |
| edassess.open_response | Open response assessment | invariant | Открытый ответ проверяет генерацию рассуждения или решения, но требует критериев и согласованности проверяющих. | глубже multiple choice |
| edassess.performance_task | Performance task | invariant | Performance task просит выполнить реалистичное действие или продукт, связанный с целевым умением. | проверка применения |
| edassess.portfolio_assessment | Portfolio assessment | variant | Портфолио оценивает набор работ во времени и показывает развитие, процесс и разнообразие доказательств. | прогресс, а не один тест |
| edassess.peer_assessment | Peer assessment | variant | Взаимооценивание развивает критерии качества, если ученики обучены рубрике и получают модерацию. | учиться через оценку |
| edassess.self_assessment | Self assessment | variant | Самооценивание помогает метакогниции, но требует конкретных критериев и примеров качества. | ученик видит свой процесс |
| edassess.feedback_timing | Feedback timing | invariant | Обратная связь полезнее, когда приходит достаточно быстро, чтобы ученик мог применить ее к следующей попытке. | закрыть цикл обучения |
| edassess.feedback_specificity | Feedback specificity | invariant | Конкретная обратная связь указывает, что сделано, что улучшить и какой следующий шаг выполнить. | не просто похвала |
| edassess.feedback_load | Feedback load | variant | Слишком много замечаний за раз может перегрузить ученика и снизить вероятность действия. | выбирать главное |
| edassess.mastery_threshold | Mastery threshold | variant | Порог mastery должен отражать минимально надежное владение навыком, а не произвольную красивую цифру. | честное продвижение |
| edassess.retake_policy | Retake policy | variant | Политика пересдачи должна различать обучение через повторную попытку и простое улучшение оценки без нового освоения. | мотивация и справедливость |
| edassess.late_work_policy | Late work policy | variant | Политика поздней сдачи должна отделять оценку знания от оценки сроков, если обе цели важны. | прозрачные последствия |
| edassess.accommodations | Assessment accommodations | invariant | Адаптации оценивания уменьшают барьеры доступа, не меняя целевой construct, если это возможно. | справедливость для разных учащихся |
| edassess.bias_review | Assessment bias review | invariant | Проверка bias ищет культурные, языковые, гендерные или контекстные элементы, которые мешают измерять целевое умение. | равные условия |
| edassess.language_load | Language load | variant | Языковая сложность задания может исказить оценку предметного знания у учащихся, для которых язык теста труден. | отделить язык от предмета |
| edassess.cheating_resistance | Cheating resistance | variant | Устойчивость к списыванию повышают вариативные задания, устная защита, процессные артефакты и проверка рассуждения. | академическая честность |
| edassess.authenticity_check | Authenticity check | variant | Проверка авторства работы сравнивает процесс, черновики, стиль, устную защиту и историю изменений. | не только детектор |
| edassess.proctoring_limit | Proctoring limit | variant | Прокторинг снижает некоторые риски списывания, но не доказывает понимание и может создавать privacy и access проблемы. | не универсальное решение |
| edassess.grade_norm_referenced | Norm-referenced grading | invariant | Norm-referenced оценка сравнивает учащегося с группой, а не с фиксированным критерием владения. | рейтинг, а не mastery |
| edassess.grade_criterion_referenced | Criterion-referenced grading | invariant | Criterion-referenced оценка сравнивает работу с заранее заданными критериями качества. | прозрачное mastery |
| edassess.standard_setting | Standard setting | variant | Standard setting определяет пороги уровней через экспертное суждение, данные заданий и последствия решений. | проходной балл не случайность |
| edassess.inter_rater_reliability | Inter-rater reliability | invariant | Межэкспертная надежность показывает, насколько разные проверяющие дают согласованные оценки одной работы. | качество рубрик |
| edassess.anchor_papers | Anchor papers | variant | Anchor papers являются примерами работ на разных уровнях рубрики и помогают выровнять оценивание. | обучение проверяющих |
| edassess.moderation_session | Moderation session | variant | Сессия модерации обсуждает спорные работы и уточняет применение критериев между проверяющими. | согласованность оценок |
| edassess.learning_analytics | Learning analytics assessment | variant | Learning analytics использует данные активности и результатов, но требует осторожности с контекстом и privacy. | не превращать клики в знание |
| edassess.progress_tracking | Progress tracking | invariant | Отслеживание прогресса должно показывать изменение конкретных навыков во времени, а не только среднюю оценку. | видеть рост |
| edassess.misconception_mapping | Misconception mapping | invariant | Карта заблуждений связывает типичные ошибки с концептами и заданиями, где они проявляются. | целевая помощь |
| edassess.spaced_retrieval_check | Spaced retrieval check | variant | Повторная проверка через интервалы показывает удержание знания лучше, чем немедленный тест после объяснения. | долговременное обучение |
| edassess.assessment_blueprint | Assessment blueprint | invariant | Blueprint оценивания связывает темы, навыки, уровни сложности, число заданий и вес критериев. | проектировать тест заранее |
