# BATCH_263 — Environmental Health Sampling Operations Detail
# world_skills_core · source: world_skills_core:batch_263:environmental_health_sampling_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| envsample.plan.sampling_plan | Environmental sampling plan | invariant | Plan defines site, matrix, analytes, locations, frequency, method and decision use. | guide collection |
| envsample.plan.objective | Sampling objective | invariant | Objective states complaint, compliance, baseline, incident, trend or clearance purpose. | avoid vague sampling |
| envsample.plan.site_map | Sampling site map | invariant | Map marks sample points, access, hazards, landmarks, flow direction and boundaries. | locate samples |
| envsample.plan.background_sample | Background sample | variant | Sample represents unaffected condition for comparison with suspect location. | interpret results |
| envsample.plan.duplicate_sample | Field duplicate sample | variant | Duplicate checks sampling precision by collecting paired sample under same conditions. | quality check |
| envsample.matrix.water_sample | Environmental water sample | invariant | Sample captures source, tap, surface, pool, wastewater or runoff details. | test water |
| envsample.matrix.soil_sample | Environmental soil sample | variant | Sample records depth, grid, composite method, container and site condition. | test soil |
| envsample.matrix.surface_swab | Environmental surface swab | variant | Swab records surface area, template, moisture, tool, location and suspected contaminant. | test surfaces |
| envsample.matrix.air_sample | Environmental air sample | variant | Sample records pump, media, flow, duration, location, weather and activity. | assess exposure |
| envsample.matrix.vector_sample | Environmental vector sample | variant | Sample captures mosquito, tick, rodent, insect or other vector location and trap. | monitor disease |
| envsample.field.field_kit | Environmental sampling field kit | invariant | Kit includes containers, labels, forms, PPE, cooler, blanks, tools and decontamination supplies. | ready fieldwork |
| envsample.field.ppe_selection | Sampling PPE selection | invariant | Selection matches gloves, eye protection, respirator, boots or suit to hazard. | protect collector |
| envsample.field.decontamination | Sampling decontamination | invariant | Decontamination prevents cross-contamination of tools, hands, surfaces and containers. | preserve validity |
| envsample.field.field_blank | Field blank | variant | Blank detects contamination from water, air, handling, containers or transport. | quality assurance |
| envsample.field.field_measure | Field measurement | invariant | Measurement records pH, temperature, chlorine, conductivity, turbidity, moisture or gas reading. | immediate data |
| envsample.collection.grab_sample | Grab sample | invariant | Sample captures condition at one place and time with defined container and preservation. | point evidence |
| envsample.collection.composite_sample | Composite sample | variant | Sample combines increments across time or space under documented rule. | representative average |
| envsample.collection.sample_label | Environmental sample label | invariant | Label records unique ID, matrix, location, date, time, collector and preservative. | identify sample |
| envsample.collection.volume_check | Sample volume check | invariant | Check ensures container has required amount without headspace errors where relevant. | lab acceptability |
| envsample.collection.preservation | Sample preservation | invariant | Preservation applies cooling, chemical preservative, light protection or holding-time rule. | valid result |
| envsample.custody.chain_of_custody | Environmental sample chain of custody | invariant | Custody form tracks sample possession, seals, times, transfers and requested analyses. | defensible custody |
| envsample.custody.cooler_seal | Sample cooler seal | variant | Seal documents cooler integrity, temperature control and transfer condition. | protect shipment |
| envsample.custody.holding_time | Sample holding time | invariant | Time tracks collection-to-analysis window required by method or lab acceptance. | avoid invalid data |
| envsample.custody.lab_receipt | Environmental lab receipt | invariant | Receipt records samples accepted, rejected, temperature, condition and anomalies. | confirm handoff |
| envsample.lab.analysis_request | Environmental analysis request | invariant | Request lists analytes, methods, reporting limits, turnaround and project contact. | direct lab work |
| envsample.lab.result_package | Environmental lab result package | invariant | Package includes results, qualifiers, methods, limits, QA checks and narrative. | interpret data |
| envsample.lab.result_qualifier | Lab result qualifier | invariant | Qualifier explains estimated, nondetect, rejected, diluted, contaminated or holding-time issue. | avoid misreading |
| envsample.lab.data_validation | Environmental data validation | variant | Validation reviews QA, blanks, duplicates, spikes, calibration and method compliance. | trust result |
| envsample.interpret.threshold_compare | Environmental threshold comparison | invariant | Comparison evaluates result against regulatory, advisory, background or project threshold. | decide action |
| envsample.interpret.exceedance_flag | Environmental exceedance flag | invariant | Flag marks result above threshold, uncertain result or urgent follow-up need. | trigger response |
| envsample.interpret.trend_review | Environmental trend review | variant | Review compares results across locations, dates, seasons or interventions. | see pattern |
| envsample.advisory.public_advisory | Environmental public advisory | variant | Advisory communicates affected area, risk, precautions, duration and contact. | inform public |
| envsample.advisory.private_notice | Environmental private notice | variant | Notice tells owner, operator or resident result, meaning and required action. | targeted communication |
| envsample.enforcement.enforcement_referral | Sampling enforcement referral | invariant | Referral sends exceedance, evidence, custody, site facts and legal basis to enforcement. | act on result |
| envsample.enforcement.corrective_order | Environmental sampling corrective order | variant | Order requires cleanup, repair, treatment, resampling, closure or operational change. | compel correction |
| envsample.followup.resample_plan | Environmental resampling plan | invariant | Plan schedules confirmation sample after correction, time interval or disputed result. | verify condition |
| envsample.followup.clearance_sample | Clearance sample | variant | Sample confirms area is acceptable after cleanup, treatment or repair. | reopen safely |
| envsample.records.field_log | Environmental sampling field log | invariant | Log records conditions, observations, deviations, photos, weather and sample IDs. | field memory |
| envsample.records.photo_log | Environmental sampling photo log | invariant | Log links photos to sample points, labels, conditions and timestamps. | visual evidence |
| envsample.records.case_file | Environmental sampling case file | invariant | File stores plan, forms, logs, results, advisories, orders and closure. | complete record |
| envsample.quality.qa_plan | Environmental sampling QA plan | invariant | Plan defines blanks, duplicates, calibration, custody, validation and corrective actions. | quality system |
| envsample.quality.equipment_calibration | Sampling equipment calibration | invariant | Calibration records meter, pump, standard, date, result and user. | reliable readings |
| envsample.metrics.sampling_kpi | Environmental sampling KPI | variant | KPI tracks turnaround, rejected samples, exceedances, resamples, advisories and enforcement referrals. | manage sampling |
| envsample.continuity.emergency_sampling | Emergency environmental sampling | variant | Sampling responds to spill, flood, outbreak, fire, odor or contamination incident. | rapid evidence |
