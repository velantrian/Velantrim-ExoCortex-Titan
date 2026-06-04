# BATCH_149 — HR Workforce Planning & Payroll Controls
# world_skills_core · source: world_skills_core:batch_149:hr_workforce_payroll_controls
# KnowledgeUnits: 44
# ВНИМАНИЕ: общеобразовательные HR/payroll процессы; не заменяет трудовое, налоговое и privacy-регулирование конкретной страны.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| hrpay.workforce.headcount_plan | Headcount plan | invariant | Headcount plan связывает бизнес-потребности, роли, бюджет, сроки найма и организационную структуру. | люди как capacity |
| hrpay.workforce.vacancy_requisition | Vacancy requisition | invariant | Requisition вакансии формально открывает позицию с причиной, budget approval, manager, location и job profile. | не нанимать без основания |
| hrpay.workforce.skills_matrix | Workforce skills matrix | variant | Skills matrix показывает навыки команды, gaps, резерв замещения и потребности обучения. | видеть capability |
| hrpay.workforce.succession_plan | Succession plan | variant | Succession plan готовит возможную замену для критичных ролей и снижает риск зависимости от одного человека. | continuity людей |
| hrpay.workforce.capacity_model | Workforce capacity model | variant | Capacity model оценивает объем работы, productivity, shifts, absence и staffing level. | расчет потребности |
| hrpay.workforce.contractor_mix | Contractor mix | variant | Баланс сотрудников и contractors влияет на гибкость, knowledge retention, compliance и cost structure. | не все роли одинаковы |
| hrpay.workforce.overtime_forecast | Overtime forecast | variant | Прогноз overtime помогает увидеть перегрузку, cost spike, staffing gap или seasonality. | усталость и бюджет |
| hrpay.workforce.attrition_rate | Attrition rate | invariant | Attrition rate показывает долю ухода сотрудников за период и требует сегментации по ролям, причинам и tenure. | текучесть как сигнал |
| hrpay.time.timesheet_approval | Timesheet approval | invariant | Approval табеля подтверждает отработанное время, проект, shift, overtime и exceptions до payroll run. | зарплата по подтвержденным данным |
| hrpay.time.clock_exception | Clock-in exception | variant | Clock exception фиксирует пропущенную отметку, ручную правку, поздний приход или технический сбой. | не скрывать ручные изменения |
| hrpay.time.shift_differential | Shift differential | variant | Shift differential добавляет оплату за ночные, выходные, опасные или специальные смены согласно правилам. | pay rules по сменам |
| hrpay.time.leave_balance | Leave balance | invariant | Leave balance показывает накопленные, использованные, одобренные и доступные дни отпуска или absence entitlement. | не платить и не планировать вслепую |
| hrpay.time.absence_code | Absence code | invariant | Код отсутствия классифицирует отпуск, болезнь, unpaid leave, training, family leave или другую категорию. | корректная аналитика и payroll |
| hrpay.time.scheduling_rule | Scheduling rule | variant | Scheduling rule ограничивает смены по availability, rest time, skills, location и трудовым правилам. | график без нарушений |
| hrpay.time.overtime_authorization | Overtime authorization | invariant | Overtime authorization требует предварительного или последующего подтверждения сверхурочного времени уполномоченным лицом. | контролировать extra cost |
| hrpay.time.attendance_audit | Attendance audit | invariant | Attendance audit ищет patterns ручных правок, missing approvals, unusual overtime и inconsistent records. | контроль табеля |
| hrpay.payroll.payroll_calendar | Payroll calendar | invariant | Payroll calendar задает cut-off, processing date, pay date, bank deadlines и reporting milestones. | ритм выплат |
| hrpay.payroll.gross_pay | Gross pay | invariant | Gross pay рассчитывается до удержаний из оклада, часов, overtime, премий, allowances и adjustments. | база payroll |
| hrpay.payroll.tax_withholding | Tax withholding | variant | Tax withholding зависит от юрисдикции, статуса сотрудника, дохода, льгот и правил отчетности. | не универсальная формула |
| hrpay.payroll.benefit_deduction | Benefit deduction | variant | Benefit deduction удерживает взносы за benefits согласно enrollment, eligibility, rates и employee share. | связать HR и payroll |
| hrpay.payroll.garnishment_order | Garnishment order | variant | Garnishment order требует удержаний по официальному документу с лимитами, приоритетом и сроком действия. | legal deduction |
| hrpay.payroll.bonus_payment | Bonus payment | variant | Bonus payment должен иметь approved amount, eligibility, performance basis, tax treatment и pay period. | разовая выплата под контролем |
| hrpay.payroll.retro_pay | Retroactive pay | variant | Retro pay корректирует прошлые периоды из-за изменения ставки, ошибки, promotion или late approval. | исправить прошлый расчет |
| hrpay.payroll.final_pay | Final pay | invariant | Final pay учитывает зарплату, отпуск, deductions, advances, assets и сроки выплаты при увольнении. | закрыть employment |
| hrpay.payroll.payroll_register | Payroll register | invariant | Payroll register показывает детальный расчет выплат и удержаний по сотрудникам за payroll run. | основной контрольный отчет |
| hrpay.payroll.direct_deposit | Direct deposit file | variant | Direct deposit file отправляет банковские выплаты и требует контроля счета, суммы, authorization и cutoff. | платежный файл |
| hrpay.payroll.payslip | Payslip | invariant | Payslip объясняет сотруднику gross pay, deductions, net pay, period, employer и year-to-date данные. | прозрачность оплаты |
| hrpay.payroll.reconciliation | Payroll reconciliation | invariant | Reconciliation payroll сравнивает register, bank file, GL postings, headcount и prior period changes. | найти ошибки до/после выплаты |
| hrpay.controls.segregation_duties | Payroll segregation of duties | invariant | Segregation of duties разделяет создание сотрудника, изменение pay data, approval и payment release. | меньше fraud risk |
| hrpay.controls.master_data_change | Employee master data change | invariant | Master data change фиксирует изменения имени, bank account, tax status, rate, manager или employment status. | контроль критичных полей |
| hrpay.controls.approval_workflow | Payroll approval workflow | invariant | Approval workflow определяет, кто проверяет exceptions, totals, variances и final release. | не выпускать без review |
| hrpay.controls.bank_file_control | Bank file control | invariant | Bank file control сравнивает approved payroll с фактическим payment file до отправки и после подтверждения банка. | защита денег |
| hrpay.controls.duplicate_employee_check | Duplicate employee check | invariant | Duplicate employee check ищет повторяющиеся identifiers, bank accounts, addresses или suspicious similarities. | риск двойной выплаты |
| hrpay.controls.ghost_employee_risk | Ghost employee risk | invariant | Ghost employee risk возникает, когда фиктивная или неактивная запись получает payroll payment. | проверять active workforce |
| hrpay.controls.access_review | Payroll access review | invariant | Access review проверяет, кто может видеть, менять, утверждать и выгружать payroll data. | privacy и fraud control |
| hrpay.controls.audit_trail | Payroll audit trail | invariant | Audit trail payroll показывает изменения данных, approvals, recalculations, overrides и payment release. | доказуемость расчета |
| hrpay.lifecycle.onboarding_checklist | Onboarding checklist | invariant | Onboarding checklist подтверждает документы, system access, payroll setup, benefits, training и equipment. | первый день без провалов |
| hrpay.lifecycle.contract_terms | Employment contract terms | invariant | Contract terms задают роль, оплату, hours, location, start date, probation и key obligations. | payroll и HR source |
| hrpay.lifecycle.probation_review | Probation review | variant | Probation review фиксирует performance, fit, extension, confirmation или termination decision в установленный срок. | контроль early tenure |
| hrpay.lifecycle.promotion_effective_date | Promotion effective date | invariant | Effective date promotion определяет, когда меняются title, pay, manager, grade или permissions. | дата решает payroll |
| hrpay.lifecycle.termination_reason | Termination reason code | invariant | Reason code увольнения помогает reporting, eligibility, rehire decision, benefits и compliance. | корректная классификация |
| hrpay.lifecycle.exit_clearance | Exit clearance | invariant | Exit clearance закрывает access, equipment, final pay inputs, confidentiality reminders и records. | уход без хвостов |
| hrpay.lifecycle.records_retention | HR records retention | invariant | Retention HR records задает сроки хранения контрактов, payroll, benefits, performance и termination documents. | хранить достаточно, не бесконечно |
| hrpay.lifecycle.privacy_minimization | HR privacy minimization | invariant | Минимизация privacy требует собирать и хранить только нужные employee data с контролем доступа. | меньше data risk |
