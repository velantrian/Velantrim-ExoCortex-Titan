# BATCH_150 — Environmental Permitting & Compliance Monitoring
# world_skills_core · source: world_skills_core:batch_150:environmental_permitting_compliance_monitoring
# KnowledgeUnits: 44
# ВНИМАНИЕ: общеобразовательные EHS/compliance знания; не заменяет разрешения, нормативы и методики конкретной юрисдикции.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| envperm.permit.permit_register | Реестр экологических разрешений | invariant | Реестр разрешений хранит permit numbers, условия, сроки, ответственных, monitoring duties и reporting deadlines. | увидеть обязательства по соблюдению |
| envperm.permit.permit_condition | Условия разрешения | invariant | Условие разрешения задает конкретное требование к выбросу, сбросу, отходу, мониторингу, работе или отчетности. | обязательство в тексте |
| envperm.permit.emission_limit | Предел выбросов в атмосферу | variant | Лимит выбросов ограничивает концентрацию, массу, rate, operating hour или pollutant для заданного источника. | соблюдение требований к воздуху |
| envperm.permit.discharge_limit | Предел сброса воды | variant | Лимит сброса задает допустимые параметры сточных вод, flow, концентрации или нагрузку по веществам. | соблюдение требований к воде |
| envperm.permit.monitoring_frequency | Частота мониторинга | invariant | Monitoring frequency определяет, как часто нужно измерять, наблюдать, отбирать пробы или проверять параметр. | календарь обязанностей |
| envperm.permit.reporting_deadline | Срок экологической отчетности | invariant | Reporting deadline задает дату или период, к которому данные должны быть отправлены органу или stakeholder. | не пропустить срок |
| envperm.permit.renewal_date | Дата продления разрешения | invariant | Renewal date требует подготовки заявки до истечения разрешения, чтобы деятельность не стала unauthorized. | разрешение не вечно |
| envperm.permit.modification_trigger | Триггер изменения разрешения | variant | Modification trigger возникает при изменении процесса, объема, сырья, emissions, ownership или permit condition. | изменения требуют проверки |
| envperm.permit.compliance_owner | Владелец соответствия | invariant | Compliance owner отвечает за выполнение условия, сбор evidence, escalation и закрытие actions. | обязанность не висит в воздухе |
| envperm.sampling.sampling_plan | План отбора проб окружающей среды | invariant | План отбора проб определяет точки, способы, методы, контейнеры, консерванты, обеспечение/контроль качества и логистику. | проба по правилам |
| envperm.sampling.chain_custody | Экологическая цепочка поставок | invariant | Chain of custody фиксирует путь environmental sample от отбора до лаборатории и отчета. | доказуемость данных |
| envperm.sampling.composite_sample | Составная выборка | variant | Composite sample объединяет несколько подпроб по времени или потоку для представления среднего условия. | не для каждого параметра |
| envperm.sampling.grab_sample | Взять образец | variant | Grab sample фиксирует состояние среды в конкретный момент и месте. | снимок, не среднее |
| envperm.sampling.lab_accreditation | Аккредитация экологической лаборатории | invariant | Аккредитация лаборатории подтверждает компетентность для определенных методов, матриц и analytes. | надежность официальных данных |
| envperm.sampling.detection_limit | Предел обнаружения отчетов | invariant | Detection limit должен быть ниже или соразмерен compliance limit, иначе результат трудно интерпретировать. | метод должен видеть нужное |
| envperm.sampling.field_blank | Поле пустое | variant | Field blank помогает выявить загрязнение от контейнера, транспортировки, среды или процедуры отбора. | QA/QC на площадке |
| envperm.sampling.calibration_log | Журнал калибровки полевого измерителя | invariant | Журнал калибровки полевого прибора подтверждает пригодность pH, conductivity, flow или gas readings. | доверять измерителю |
| envperm.monitoring.stack_monitoring | Мониторинг стека | variant | Мониторинг трубы или источника медицинских исследований измеряет концентрацию загрязняющих веществ, поток, температуру или рабочее состояние. | контроль воздуха |
| envperm.monitoring.wastewater_meter | Расходомер сточных вод | invariant | Flow meter сточных вод нужен для расчета нагрузки, compliance, fees и обнаружения abnormal discharge. | объем меняет значение |
| envperm.monitoring.groundwater_well | Скважина для мониторинга подземных вод | variant | Monitoring well отслеживает состояние groundwater в заданной точке и требует правильного отбора и maintenance. | подземные воды как receptor |
| envperm.monitoring.noise_monitoring | Мониторинг шума окружающей среды | variant | Noise monitoring оценивает уровень шума по времени, месту, источнику и applicable limit. | влияние на сообщество |
| envperm.monitoring.dust_control | Проверка контроля пыли | invariant | Проверка пыли в конечном итоге определяет наличие пыли, уборку помещений, влажность, покрытия, движение транспорта и видимые выбросы. | простая, но важная проверка |
| envperm.monitoring.stormwater_inspection | Проверка ливневых вод | invariant | Проверка ливневых вод позволяет выявить отложения, разливы, засоренные стоки, открытые материалы и средства контроля эрозии. | дождь переносит загрязнения |
| envperm.monitoring.waste_manifest | Манифест отходов | invariant | В манифесте отходов отслеживается тип отхода, производитель, транспортер, получатель, количество и нормативная классификация. | отход не исчезает после вывоза |
| envperm.monitoring.wildlife_observation | Журнал наблюдений за дикой природой | variant | Журнал дикой природы фиксирует наблюдения за видами, гнездованием, смертностью или нарушением среды обитания, если это связано с лицензионными обязательствами. | доказательства биоразнообразия |
| envperm.exceedance.threshold_exceedance | Превышение экологического порога | invariant | Exceedance возникает, когда измеренный или рассчитанный показатель превышает permit limit или action level. | trigger для реакции |
| envperm.exceedance.incident_notification | Уведомление об экологическом происшествии | invariant | Порядок уведомления определяет, кого, когда и чем уведомлять при разливе, превышении, выбросе или рекламации. | часы могут идти сразу |
| envperm.exceedance.corrective_action | Экологические корректирующие действия | invariant | Corrective action устраняет причину exceedance или noncompliance и фиксирует доказательства завершения. | закрыть нарушение |
| envperm.exceedance.root_cause | Экологическая первопричина | invariant | Первопричиной экологического события может быть отказ оборудования, человеческая ошибка, перерыв в техническом обслуживании, погодные условия или изменение процесса. | не лечить симптом |
| envperm.exceedance.agency_correspondence | Агентская переписка | invariant | Переписку с органом необходимо хранить с датами, обязательствами, ответами, одобрениями и последующими действиями. | регуляторная память |
| envperm.exceedance.public_complaint | Экологическая общественная жалоба | variant | Public complaint требует регистрации, расследования, ответа, trend review и связи с operational data. | соседний сигнал |
| envperm.exceedance.enforcement_risk | Правоприменительный риск | variant | Enforcement risk растет при повторных нарушениях, несообщении, плохих records или отсутствии corrective actions. | последствия соблюдения |
| envperm.audit.inspection_readiness | Готовность к проверке | invariant | Готовность к проверке означает, что записи, состояние объекта, ответы персонала и доступ готовы к внешнему виду. | не готовиться в панике |
| envperm.audit.record_retention | Сохранение экологической документации | invariant | Записи о хранении определяют, сколько хранить разрешений, образцов, отчетов, манифестов, документов проверок и учебных документов. | доказательства выживают |
| envperm.audit.internal_audit | Экологический внутренний аудит | variant | Внутренний аудит впоследствии фактически практикуется в отношении условий разрешений, процедур, записей и наблюдений на объекте. | найти проблемы раньше органа |
| envperm.audit.contractor_compliance | Экологическое соблюдение подрядчиком | invariant | Соблюдение требований подрядчика требует инструктажа, осведомленности о разрешениях, контроля отходов, ликвидации разливов и надзора. | подрядчик тоже риск |
| envperm.audit.training_record | Запись экологического обучения | invariant | В протоколе обучения подтверждено, что персонал знает свои экологические обязанности, процедуры и действия в чрезвычайных ситуациях. | обучение как evidence |
| envperm.audit.management_review | Обзор экологического менеджмента | variant | Анализ со стороны руководства оценивает инциденты, ключевые показатели эффективности, аудиты, нормативные изменения, ресурсы и действия по улучшению. | EHS на уровне управления |
| envperm.continuous.permit_change_log | Журнал изменений разрешений | invariant | Журнал изменений фиксирует изменения условий разрешений, интерпретаций, ответственных владельцев и статуса реализации. | не потерять новую обязанность |
| envperm.continuous.environmental_kpi | Экологические КПЭ | variant | KPI может отслеживать выбросы, использование воды, отходы, инциденты, закрытия, жалобы или результаты аудита. | видеть trend |
| envperm.continuous.pollution_prevention | Предотвращение загрязнения | invariant | Prevention ищет способы снизить загрязнение у источника через material substitution, process control или housekeeping. | лучше не создавать риск |
| envperm.continuous.spill_drill | Дрель от разлива | variant | Drill spill response проверяет материалы, роли, уведомления, containment и readiness без реального события. | тренировка реакции |
| envperm.continuous.closure_obligation | Обязательство по закрытию | variant | Closure obligation описывает очистку, демонтаж, monitoring или восстановление площадки после прекращения деятельности. | ответственность после эксплуатации |
| envperm.continuous.community_reporting | Экологическая отчетность сообщества | variant | Community reporting объясняет environmental performance понятным языком без раскрытия защищенных или misleading данных. | доверие к площадке |
