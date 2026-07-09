# BATCH_151 — Nonprofit & Public Program Monitoring Detail
# world_skills_core · source: world_skills_core:batch_151:nonprofit_program_monitoring_detail
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| progmon.design.logic_model | Program logic model | invariant | Logic model связывает inputs, activities, outputs, outcomes и assumptions в проверяемую структуру программы. | видеть цепочку результата |
| progmon.design.theory_change | Theory of change | invariant | Theory of change объясняет, почему действия программы должны привести к желаемым изменениям в конкретном контексте. | не путать активность и эффект |
| progmon.design.beneficiary_criteria | Beneficiary eligibility criteria | invariant | Eligibility criteria определяют, кто может получать услугу, помощь или участие в программе. | честный доступ |
| progmon.design.indicator_definition | Indicator definition | invariant | Indicator definition задает формулу, источник, период, единицу, disaggregation и владельца данных. | один показатель, одно значение |
| progmon.design.baseline | Program baseline | invariant | Baseline фиксирует исходное состояние до вмешательства или до нового периода мониторинга. | сравнивать с началом |
| progmon.design.target | Program target | variant | Target задает ожидаемый уровень показателя с учетом ресурсов, времени, контекста и риска. | цель без фантазии |
| progmon.design.data_collection_plan | Data collection plan | invariant | План сбора данных описывает источники, инструменты, frequency, ответственных и проверку качества. | данные не появляются сами |
| progmon.ethics.informed_consent | Beneficiary informed consent | invariant | Consent объясняет участнику цель сбора данных, использование, риски, добровольность и privacy safeguards. | уважение к человеку |
| progmon.ethics.safeguarding_pathway | Safeguarding referral pathway | invariant | Safeguarding pathway показывает, куда и как передавать concern о насилии, эксплуатации или риске для участника. | безопасность важнее отчета |
| progmon.field.site_visit_checklist | Site visit checklist | invariant | Site visit checklist стандартизирует наблюдение activities, records, staff, materials, risks и beneficiary feedback. | визит не прогулка |
| progmon.field.attendance_record | Attendance record | invariant | Attendance record фиксирует участие людей в activity с датой, сессией, ролью и допустимым подтверждением. | не завышать охват |
| progmon.field.duplicate_beneficiary | Duplicate beneficiary check | invariant | Проверка дублей ищет повторную регистрацию одного участника через identifiers, contact, household или case matching. | считать людей, не строки |
| progmon.field.case_file | Beneficiary case file | variant | Case file собирает eligibility, services, referrals, follow-up и key notes по участнику или домохозяйству. | история поддержки |
| progmon.field.indicator_verification | Indicator verification | invariant | Verification показателя сопоставляет отчетную цифру с первичными документами, наблюдением или независимым источником. | trust but verify |
| progmon.field.outcome_survey | Outcome survey | variant | Outcome survey измеряет изменения у участников через вопросы, sample, timing и bias controls. | результат глазами данных |
| progmon.feedback.feedback_mechanism | Feedback mechanism | invariant | Feedback mechanism дает участникам безопасный канал предложений, жалоб, вопросов и оценки услуги. | программа слышит людей |
| progmon.feedback.grievance_log | Grievance log | invariant | Grievance log хранит жалобы, даты, severity, ответственного, действия и статус закрытия. | жалоба как управляемый процесс |
| progmon.feedback.referral_tracking | Referral tracking | variant | Tracking referrals показывает, дошел ли участник до другой услуги и был ли follow-up завершен. | не просто дать адрес |
| progmon.delivery.distribution_list | Distribution list | invariant | Distribution list подтверждает выдачу товаров или услуг участникам с датой, item, quantity и proof. | контроль помощи |
| progmon.delivery.cash_transfer_reconciliation | Cash transfer reconciliation | invariant | Reconciliation cash transfers сравнивает approved list, payment file, provider report, failed payments и complaints. | деньги дошли правильно |
| progmon.delivery.monitoring_visit_report | Monitoring visit report | invariant | Monitoring report фиксирует observed facts, evidence, issues, agreed actions и responsible owners. | визит оставляет след |
| progmon.delivery.photo_evidence_rule | Photo evidence rule | variant | Правило photo evidence ограничивает, когда фото допустимы, как защищать достоинство, consent и location privacy. | картинка не всегда безопасна |
| progmon.data.data_quality_assessment | Data quality assessment | invariant | DQA проверяет accuracy, completeness, timeliness, consistency, validity и integrity program data. | качество до dashboard |
| progmon.data.sampling_frame | Sampling frame | invariant | Sampling frame определяет совокупность, из которой выбирают cases for survey, verification или evaluation. | sample начинается со списка |
| progmon.data.enumerator_training | Enumerator training | invariant | Training enumerators выравнивает понимание вопросов, ethics, probing, recording и escalation rules. | меньше interviewer bias |
| progmon.data.confidentiality_control | Program confidentiality control | invariant | Confidentiality control ограничивает доступ к sensitive beneficiary data и связывает sharing с purpose. | защита участников |
| progmon.data.inclusion_disaggregation | Inclusion disaggregation | variant | Disaggregation по полу, возрасту, disability, location или group помогает увидеть unequal reach. | справедливость в данных |
| progmon.risk.do_no_harm | Do-no-harm review | invariant | Do-no-harm review ищет, может ли программа усилить конфликт, stigma, dependency, exclusion или safety risks. | помощь без вреда |
| progmon.risk.partner_report_review | Partner report review | invariant | Review partner report проверяет numbers, narrative, evidence, exceptions и alignment with grant terms. | партнерские данные тоже проверять |
| progmon.risk.budget_activity_link | Budget to activity link | invariant | Связь бюджета и activities показывает, какие расходы поддерживают какие outputs и outcomes. | деньги связаны с работой |
| progmon.results.output_verification | Output verification | invariant | Output verification подтверждает, что заявленные trainings, deliveries, visits или services реально состоялись. | факт выполнения |
| progmon.results.outcome_contribution | Outcome contribution | variant | Contribution analysis оценивает, насколько программа могла повлиять на outcome среди других факторов. | не присваивать весь эффект |
| progmon.eval.evaluation_questions | Evaluation questions | invariant | Evaluation questions формулируют, что именно нужно узнать о relevance, effectiveness, efficiency, impact или sustainability. | оценка начинается с вопроса |
| progmon.eval.midline_review | Midline review | variant | Midline review показывает прогресс и проблемы до окончания программы, когда еще можно менять course. | учиться посередине |
| progmon.eval.endline_measurement | Endline measurement | invariant | Endline measurement фиксирует состояние в конце периода и сравнивается с baseline или target. | закрыть цикл измерения |
| progmon.learning.learning_agenda | Learning agenda | variant | Learning agenda задает вопросы для улучшения программы, а не только donor reporting. | знание для решений |
| progmon.learning.corrective_action | Program corrective action | invariant | Corrective action имеет issue, root cause, owner, deadline, verification и closure evidence. | замечание становится работой |
| progmon.learning.risk_register | Program risk register | invariant | Risk register отслеживает operational, safeguarding, financial, political и delivery risks с mitigations. | риск виден заранее |
| progmon.safety.safeguarding_incident | Safeguarding incident record | invariant | Safeguarding incident record фиксирует concern, immediate action, referral, confidentiality и follow-up без лишнего раскрытия. | серьезный сигнал |
| progmon.safety.community_validation | Community validation | variant | Community validation сверяет program facts with local stakeholders без раскрытия sensitive details. | reality check на месте |
| progmon.reporting.program_dashboard | Program dashboard | variant | Dashboard показывает key indicators, status, alerts и trends, но должен сохранять контекст и data caveats. | обзор без самообмана |
| progmon.reporting.adaptive_management | Adaptive management | invariant | Adaptive management использует evidence, feedback и context changes для корректировки delivery. | программа не застывает |
| progmon.closeout.closure_report | Program closure report | invariant | Closure report собирает results, lessons, remaining obligations, asset disposition и record handover. | завершить аккуратно |
| progmon.closeout.record_retention | Program record retention | invariant | Retention records задает, какие program documents хранить, где, сколько и с каким доступом. | доказательства после проекта |
