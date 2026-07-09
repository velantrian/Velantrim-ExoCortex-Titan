# BATCH_150 — Environmental Permitting & Compliance Monitoring
# world_skills_core · source: world_skills_core:batch_150:environmental_permitting_compliance_monitoring
# KnowledgeUnits: 44
# ВНИМАНИЕ: общеобразовательные EHS/compliance знания; не заменяет разрешения, нормативы и методики конкретной юрисдикции.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| envperm.permit.permit_register | Environmental permit register | invariant | Реестр разрешений хранит permit numbers, условия, сроки, ответственных, monitoring duties и reporting deadlines. | видеть compliance obligations |
| envperm.permit.permit_condition | Permit condition | invariant | Условие разрешения задает конкретное требование к выбросу, сбросу, отходу, мониторингу, работе или отчетности. | обязательство в тексте |
| envperm.permit.emission_limit | Air emission limit | variant | Лимит выбросов ограничивает концентрацию, массу, rate, operating hour или pollutant для заданного источника. | air compliance |
| envperm.permit.discharge_limit | Water discharge limit | variant | Лимит сброса задает допустимые параметры сточных вод, flow, концентрации или нагрузку по веществам. | water compliance |
| envperm.permit.monitoring_frequency | Monitoring frequency | invariant | Monitoring frequency определяет, как часто нужно измерять, наблюдать, отбирать пробы или проверять параметр. | календарь обязанностей |
| envperm.permit.reporting_deadline | Environmental reporting deadline | invariant | Reporting deadline задает дату или период, к которому данные должны быть отправлены органу или stakeholder. | не пропустить срок |
| envperm.permit.renewal_date | Permit renewal date | invariant | Renewal date требует подготовки заявки до истечения разрешения, чтобы деятельность не стала unauthorized. | разрешение не вечно |
| envperm.permit.modification_trigger | Permit modification trigger | variant | Modification trigger возникает при изменении процесса, объема, сырья, emissions, ownership или permit condition. | изменения требуют проверки |
| envperm.permit.compliance_owner | Compliance owner | invariant | Compliance owner отвечает за выполнение условия, сбор evidence, escalation и закрытие actions. | обязанность не висит в воздухе |
| envperm.sampling.sampling_plan | Environmental sampling plan | invariant | Sampling plan задает точки, частоту, метод, containers, preservatives, QA/QC и logistics. | проба по правилам |
| envperm.sampling.chain_custody | Environmental chain of custody | invariant | Chain of custody фиксирует путь environmental sample от отбора до лаборатории и отчета. | доказуемость данных |
| envperm.sampling.composite_sample | Composite sample | variant | Composite sample объединяет несколько подпроб по времени или потоку для представления среднего условия. | не для каждого параметра |
| envperm.sampling.grab_sample | Grab sample | variant | Grab sample фиксирует состояние среды в конкретный момент и месте. | снимок, не среднее |
| envperm.sampling.lab_accreditation | Environmental lab accreditation | invariant | Аккредитация лаборатории подтверждает компетентность для определенных методов, матриц и analytes. | надежность официальных данных |
| envperm.sampling.detection_limit | Reporting detection limit | invariant | Detection limit должен быть ниже или соразмерен compliance limit, иначе результат трудно интерпретировать. | метод должен видеть нужное |
| envperm.sampling.field_blank | Field blank | variant | Field blank помогает выявить загрязнение от контейнера, транспортировки, среды или процедуры отбора. | QA/QC на площадке |
| envperm.sampling.calibration_log | Field meter calibration log | invariant | Журнал калибровки полевого прибора подтверждает пригодность pH, conductivity, flow или gas readings. | доверять измерителю |
| envperm.monitoring.stack_monitoring | Stack monitoring | variant | Monitoring трубы или источника выбросов измеряет pollutant concentration, flow, temperature или operating condition. | контроль воздуха |
| envperm.monitoring.wastewater_meter | Wastewater flow meter | invariant | Flow meter сточных вод нужен для расчета нагрузки, compliance, fees и обнаружения abnormal discharge. | объем меняет значение |
| envperm.monitoring.groundwater_well | Groundwater monitoring well | variant | Monitoring well отслеживает состояние groundwater в заданной точке и требует правильного отбора и maintenance. | подземные воды как receptor |
| envperm.monitoring.noise_monitoring | Environmental noise monitoring | variant | Noise monitoring оценивает уровень шума по времени, месту, источнику и applicable limit. | community impact |
| envperm.monitoring.dust_control | Dust control inspection | invariant | Dust inspection проверяет источники пыли, housekeeping, moisture, covers, traffic и visible emissions. | простая, но важная проверка |
| envperm.monitoring.stormwater_inspection | Stormwater inspection | invariant | Stormwater inspection ищет sediment, spills, blocked drains, exposed materials и erosion controls. | дождь переносит загрязнения |
| envperm.monitoring.waste_manifest | Waste manifest | invariant | Waste manifest отслеживает тип отхода, generator, transporter, receiver, quantity и regulatory classification. | отход не исчезает после вывоза |
| envperm.monitoring.wildlife_observation | Wildlife observation log | variant | Wildlife log фиксирует наблюдения видов, nesting, mortality или habitat disturbance, если это связано с permit obligations. | biodiversity evidence |
| envperm.exceedance.threshold_exceedance | Environmental threshold exceedance | invariant | Exceedance возникает, когда измеренный или рассчитанный показатель превышает permit limit или action level. | trigger для реакции |
| envperm.exceedance.incident_notification | Environmental incident notification | invariant | Notification procedure определяет, кого, когда и чем уведомлять при spill, exceedance, release или complaint. | часы могут идти сразу |
| envperm.exceedance.corrective_action | Environmental corrective action | invariant | Corrective action устраняет причину exceedance или noncompliance и фиксирует доказательства завершения. | закрыть нарушение |
| envperm.exceedance.root_cause | Environmental root cause | invariant | Root cause environmental event может быть equipment failure, human error, maintenance gap, weather или process change. | не лечить симптом |
| envperm.exceedance.agency_correspondence | Agency correspondence | invariant | Correspondence с органом нужно хранить с датами, commitments, responses, approvals и follow-up actions. | регуляторная память |
| envperm.exceedance.public_complaint | Environmental public complaint | variant | Public complaint требует регистрации, расследования, ответа, trend review и связи с operational data. | соседний сигнал |
| envperm.exceedance.enforcement_risk | Enforcement risk | variant | Enforcement risk растет при повторных нарушениях, несообщении, плохих records или отсутствии corrective actions. | compliance consequences |
| envperm.audit.inspection_readiness | Inspection readiness | invariant | Inspection readiness означает, что records, site conditions, staff answers и access готовы к проверке. | не готовиться в панике |
| envperm.audit.record_retention | Environmental record retention | invariant | Retention records определяет, сколько хранить permits, samples, reports, manifests, inspections и training documents. | evidence survives |
| envperm.audit.internal_audit | Environmental internal audit | variant | Internal audit проверяет фактическую практику против permit conditions, procedures, records и site observations. | найти проблемы раньше органа |
| envperm.audit.contractor_compliance | Contractor environmental compliance | invariant | Contractor compliance требует инструктажа, permit awareness, waste control, spill response и supervision. | подрядчик тоже риск |
| envperm.audit.training_record | Environmental training record | invariant | Training record подтверждает, что персонал знает свои environmental duties, procedures и emergency steps. | обучение как evidence |
| envperm.audit.management_review | Environmental management review | variant | Management review оценивает incidents, KPIs, audits, regulatory changes, resources и improvement actions. | EHS на уровне управления |
| envperm.continuous.permit_change_log | Permit change log | invariant | Change log фиксирует изменения permit conditions, interpretations, responsible owners и implementation status. | не потерять новую обязанность |
| envperm.continuous.environmental_kpi | Environmental KPI | variant | KPI может отслеживать emissions, water use, waste, incidents, closures, complaints или audit findings. | видеть trend |
| envperm.continuous.pollution_prevention | Pollution prevention | invariant | Prevention ищет способы снизить загрязнение у источника через material substitution, process control или housekeeping. | лучше не создавать риск |
| envperm.continuous.spill_drill | Spill drill | variant | Drill spill response проверяет материалы, роли, уведомления, containment и readiness без реального события. | тренировка реакции |
| envperm.continuous.closure_obligation | Closure obligation | variant | Closure obligation описывает очистку, демонтаж, monitoring или восстановление площадки после прекращения деятельности. | ответственность после эксплуатации |
| envperm.continuous.community_reporting | Community environmental reporting | variant | Community reporting объясняет environmental performance понятным языком без раскрытия защищенных или misleading данных. | доверие к площадке |
