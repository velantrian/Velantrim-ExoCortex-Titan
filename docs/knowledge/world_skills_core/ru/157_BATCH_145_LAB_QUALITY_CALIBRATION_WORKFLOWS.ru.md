# BATCH_145 — Laboratory Quality & Calibration Workflows
# world_skills_core · source: world_skills_core:batch_145:lab_quality_calibration_workflows
# KnowledgeUnits: 44
# ВНИМАНИЕ: общеобразовательные принципы лабораторного качества; конкретные методы требуют аккредитованных SOP и локальных правил безопасности.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| labqual.sample.sample_id | Laboratory sample ID | invariant | Уникальный sample ID связывает образец, заявку, контейнер, метод, результаты и архивные записи. | не спутать образцы |
| labqual.sample.chain_of_custody | Sample chain of custody | invariant | Chain of custody фиксирует передачу образца между людьми, зонами и этапами анализа. | доказуемость владения |
| labqual.sample.receipt_condition | Sample receipt condition | invariant | Условие приема образца описывает целостность, температуру, маркировку, объем и пригодность к анализу. | принять или отклонить |
| labqual.sample.hold_time | Sample hold time | invariant | Hold time ограничивает период между отбором и анализом, чтобы результат оставался интерпретируемым. | время влияет на достоверность |
| labqual.sample.storage_condition | Sample storage condition | invariant | Условия хранения задают температуру, свет, контейнер, консервацию и разделение несовместимых образцов. | сохранить состояние |
| labqual.sample.aliquot | Sample aliquot | variant | Aliquot — часть образца, выделенная для анализа, ретеста или параллельной проверки без загрязнения исходника. | экономить и защищать пробу |
| labqual.sample.retention | Sample retention | variant | Retention образца задает, сколько и как хранить остаток после анализа для проверки или спора. | возможность повторной проверки |
| labqual.method.validation_scope | Method validation scope | invariant | Scope validation указывает матрицы, диапазоны, analytes, оборудование и условия, где метод доказан. | не применять метод вне рамки |
| labqual.method.accuracy | Method accuracy | invariant | Accuracy показывает близость результата метода к принятому референсному значению. | правильность измерения |
| labqual.method.precision | Method precision | invariant | Precision показывает повторяемость результатов при заданных условиях, операторах и приборах. | стабильность метода |
| labqual.method.detection_limit | Detection limit | invariant | Detection limit описывает минимальный уровень сигнала или analyte, который метод способен надежно обнаружить. | не обещать невозможное |
| labqual.method.selectivity | Method selectivity | invariant | Selectivity показывает способность метода измерять нужный analyte при наличии мешающих компонентов. | матрица может обманывать |
| labqual.method.uncertainty | Measurement uncertainty | invariant | Неопределенность измерения описывает диапазон, в котором результат разумно интерпретировать с заданной уверенностью. | число без ложной точности |
| labqual.qc.blank_sample | Blank sample | invariant | Blank sample показывает вклад реагентов, контейнеров, среды или процедуры в сигнал без analyte. | найти загрязнение |
| labqual.qc.control_sample | Control sample | invariant | Control sample с известным уровнем проверяет, что метод работает в серии анализов. | ежедневная уверенность |
| labqual.qc.spike_recovery | Spike recovery | invariant | Spike recovery показывает, насколько метод возвращает добавленное количество analyte в конкретной матрице. | проверить matrix effect |
| labqual.qc.duplicate_sample | Duplicate sample | invariant | Duplicate sample оценивает вариабельность подготовки, измерения или неоднородности образца. | видеть разброс |
| labqual.qc.control_chart | Control chart | invariant | Control chart отслеживает результаты QC во времени и выявляет смещение, тренд или внезапный выход из контроля. | статистический сторож |
| labqual.qc.proficiency_test | Proficiency test | variant | Proficiency testing сравнивает лабораторию с внешними участниками или референсным провайдером. | независимая проверка компетентности |
| labqual.instrument.calibration_interval | Calibration interval | variant | Интервал калибровки зависит от стабильности прибора, критичности измерения, истории отклонений и требований системы качества. | не калибровать наугад |
| labqual.instrument.calibration_certificate | Calibration certificate | invariant | Сертификат калибровки должен указывать прибор, метод, дату, результаты, неопределенность и traceability. | документ доверия |
| labqual.instrument.reference_standard | Reference standard | invariant | Reference standard должен иметь известную прослеживаемость, состояние, срок годности и подходящий диапазон. | эталон задает основу |
| labqual.instrument.as_found_as_left | As found and as left | invariant | As found показывает состояние прибора до регулировки, а as left — после обслуживания или калибровки. | понять риск прошлых результатов |
| labqual.instrument.maintenance_log | Instrument maintenance log | invariant | Maintenance log хранит очистку, ремонт, замену частей, сбои, сервис и возврат прибора в работу. | история оборудования |
| labqual.instrument.out_of_tolerance | Out-of-tolerance event | invariant | Out-of-tolerance event требует оценки влияния на прошлые результаты, текущую работу и корректирующие действия. | прибор мог уже ошибаться |
| labqual.data.raw_data | Raw data | invariant | Raw data — исходная запись измерения или наблюдения, из которой выводится результат. | нельзя подменять итогом |
| labqual.data.result_review | Result review | invariant | Review результата проверяет расчеты, QC, единицы, метод, flags, подписи и соответствие спецификации. | второй взгляд |
| labqual.data.transcription_check | Transcription check | invariant | Проверка переноса данных снижает ошибки при ручном вводе между прибором, журналом, LIMS и отчетом. | ловить человеческие ошибки |
| labqual.data.electronic_signature | Electronic signature | variant | Электронная подпись в лаборатории должна связывать пользователя, действие, время и неизменяемость записи. | accountability в LIMS |
| labqual.data.audit_trail | Laboratory audit trail | invariant | Audit trail показывает изменения данных, кто их сделал, когда и с каким основанием. | прозрачность изменений |
| labqual.deviation.nonconformance | Laboratory nonconformance | invariant | Nonconformance фиксирует отклонение от метода, спецификации, SOP, QC или условий приемки. | не скрывать сбой |
| labqual.deviation.capa | CAPA in laboratory | invariant | CAPA связывает correction, root cause, corrective action, preventive action и проверку эффективности. | закрыть причину |
| labqual.deviation.root_cause | Lab root cause analysis | invariant | Root cause analysis отделяет поверхностную ошибку от системной причины в методе, обучении, оборудовании или среде. | лечить процесс |
| labqual.deviation.impact_assessment | Result impact assessment | invariant | Impact assessment определяет, какие результаты, партии, отчеты или клиенты могли быть затронуты отклонением. | границы риска |
| labqual.deviation.retest_rule | Retest rule | variant | Retest должен быть заранее регулируемым, чтобы повторный анализ не использовался для выбора удобного результата. | честность данных |
| labqual.biosafety.ppe | Laboratory PPE | invariant | PPE подбирается по химическому, биологическому, физическому и процедурному риску работы. | защита не универсальна |
| labqual.biosafety.waste_segregation | Lab waste segregation | invariant | Разделение отходов предотвращает смешение химических, биологических, острых, радиоактивных или обычных материалов. | безопасная утилизация |
| labqual.biosafety.chemical_label | Chemical label | invariant | Маркировка химиката должна показывать идентичность, концентрацию, дату, hazards и ответственного владельца. | не работать с неизвестным |
| labqual.biosafety.emergency_shower | Emergency shower and eyewash | invariant | Душ и eyewash должны быть доступны, проверены и не заблокированы для быстрого реагирования на exposure. | секунды важны |
| labqual.biosafety.sample_disposal | Sample disposal | invariant | Утилизация образцов учитывает hazardous status, retention, стерилизацию, контейнер и документирование. | закрыть lifecycle пробы |
| labqual.training.competency | Analyst competency | invariant | Компетентность аналитика подтверждается обучением, наблюдением, практикой, успешными проверками и периодическим пересмотром. | метод делает человек |
| labqual.document.sop_control | SOP control | invariant | SOP control управляет версиями, утверждением, распространением и изъятием устаревших процедур. | работать по актуальному методу |
| labqual.environment.temperature_log | Laboratory temperature log | variant | Журнал температуры подтверждает, что помещения, холодильники или инкубаторы оставались в заданном диапазоне. | условия влияют на результат |
| labqual.environment.contamination_control | Contamination control | invariant | Контроль загрязнения требует разделения зон, чистых расходников, blanks, уборки и поведения персонала. | результат не должен прийти из среды |
