# BATCH 433: Recovery Household Budget Counseling Intake Operations

**KnowledgeUnits:** 44  
**Namespace:** `budgetcounselops.*`  
**Scope:** income, expenses, debt, benefits, goals, referrals, follow-up and outcomes.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| budgetcounselops.intake.request_source | request source | RECORD | Source records benefits desk, caseworker, shelter, legal clinic, lender or self-referral. | Shows entry path. |
| budgetcounselops.intake.household | household profile | RECORD | Profile captures household size, contact, language, housing status and safe-contact limits. | Defines case. |
| budgetcounselops.intake.financial_goal | financial goal | RECORD | Goal records rent stability, debt plan, benefits access, savings or rebuilding budget. | Frames counseling. |
| budgetcounselops.intake.urgency | urgency model | MODEL | Urgency weighs eviction, shutoff, debt collection, benefit deadline and cash gap. | Prioritizes help. |
| budgetcounselops.income.income_sources | income sources | RECORD | Sources capture wages, benefits, insurance, gifts, self-employment and expected changes. | Builds budget. |
| budgetcounselops.income.income_timing | income timing | RECORD | Timing records pay dates, benefit dates, delays and one-time payments. | Plans cashflow. |
| budgetcounselops.income.income_gap | income gap | MEASUREMENT | Gap compares expected income to basic monthly needs. | Shows shortfall. |
| budgetcounselops.income.verification | income verification | METHOD | Verification uses paystub, benefit notice, bank record or self-attestation where allowed. | Supports referrals. |
| budgetcounselops.expenses.essential | essential expenses | RECORD | Essentials include housing, utilities, food, transport, medical, childcare and communications. | Prioritizes spending. |
| budgetcounselops.expenses.disaster_cost | disaster cost | RECORD | Disaster costs include lodging, repairs, storage, cleanup, replacement and travel. | Shows recovery burden. |
| budgetcounselops.expenses.variable | variable expense | RECORD | Variable expenses are tracked separately from fixed obligations. | Finds flexibility. |
| budgetcounselops.expenses.bill_calendar | bill calendar | METHOD | Calendar maps due dates, grace periods, late fees and shutoff/eviction risk. | Prevents surprises. |
| budgetcounselops.debt.debt_list | debt list | RECORD | List captures creditor, balance, payment, status, secured/unsecured and collection stage. | Organizes obligations. |
| budgetcounselops.debt.priority_debt | priority debt | MODEL | Priority distinguishes housing, utilities, vehicle, court, tax and high-risk debts. | Focuses action. |
| budgetcounselops.debt.collection_notice | collection notice | RECORD | Notice records collector, deadline, dispute rights and legal referral need. | Protects rights. |
| budgetcounselops.debt.payment_plan | payment plan | METHOD | Plan aligns realistic payments with income timing and essential expenses. | Reduces default. |
| budgetcounselops.benefits.benefit_screen | benefit screen | MODEL | Screen checks food, cash, health, unemployment, rent, utility and childcare supports. | Finds resources. |
| budgetcounselops.benefits.document_gap | document gap | RECORD | Gap records missing proof, replacement path and deadline. | Supports applications. |
| budgetcounselops.benefits.referral | benefits referral | METHOD | Referral routes household to appropriate program or navigator. | Expands income. |
| budgetcounselops.benefits.status | benefit status | RECORD | Status tracks applied, pending, approved, denied, appealed or closed. | Monitors progress. |
| budgetcounselops.plan.spending_plan | spending plan | RECORD | Plan allocates income to essentials, debts, recovery costs and reserves. | Guides decisions. |
| budgetcounselops.plan.cashflow_plan | cashflow plan | METHOD | Cashflow sequences payments by due date, income date and risk. | Prevents crises. |
| budgetcounselops.plan.cut_option | cost reduction option | METHOD | Options include bill negotiation, plan change, assistance, substitution or pause. | Finds relief. |
| budgetcounselops.plan.emergency_reserve | emergency reserve | METHOD | Reserve goal sets small realistic buffer where possible. | Builds resilience. |
| budgetcounselops.referrals.legal | legal referral | METHOD | Legal referral handles eviction, garnishment, debt suit, fraud or benefit appeal. | Adds expertise. |
| budgetcounselops.referrals.credit | credit counseling referral | METHOD | Credit referral handles complex debt, credit report and consolidation questions. | Adds support. |
| budgetcounselops.referrals.employment | employment referral | METHOD | Employment referral addresses income gaps and job placement needs. | Improves recovery. |
| budgetcounselops.referrals.behavioral | stress support referral | METHOD | Financial stress routes to peer, counseling or crisis support when needed. | Supports wellbeing. |
| budgetcounselops.followup.next_check | next check | RECORD | Next check records date, task, owner, documents and contact method. | Maintains continuity. |
| budgetcounselops.followup.action_status | action status | RECORD | Status tracks bill call, application, payment plan, document or referral outcome. | Shows progress. |
| budgetcounselops.followup.revision | budget revision | METHOD | Budget updates for new income, denial, repair cost or family change. | Keeps plan real. |
| budgetcounselops.followup.closeout | closeout | RECORD | Closure records stabilized, referred, unreachable, declined or transferred status. | Ends support. |
| budgetcounselops.privacy.consent | consent record | RECORD | Consent explains financial data use, referrals and sharing limits. | Protects household. |
| budgetcounselops.privacy.minimum_data | minimum data | SAFETY_RULE | Records avoid unnecessary account numbers or sensitive details. | Reduces exposure. |
| budgetcounselops.communication.plain_summary | plain summary | METHOD | Household receives simple next steps, dates, calls and documents needed. | Supports action. |
| budgetcounselops.communication.partner_update | partner update | METHOD | Partners receive aggregate barriers, not individual budgets without consent. | Preserves privacy. |
| budgetcounselops.records.case_log | case log | RECORD | Log stores intake, income, expenses, plan, referrals, follow-up and outcome. | Creates continuity. |
| budgetcounselops.records.retention | retention rule | CONSTRAINT | Financial counseling, privacy and referral records follow retention schedules. | Preserves audit. |
| budgetcounselops.metrics.households_served | households served | MEASUREMENT | Count tracks households served by need, referral source and status. | Shows demand. |
| budgetcounselops.metrics.plan_completion | plan completion | MEASUREMENT | Metric tracks households leaving with a documented plan. | Shows output. |
| budgetcounselops.metrics.referral_outcome | referral outcome | MEASUREMENT | Outcome tracks completed referrals to benefits, legal, credit or employment. | Shows linkage. |
| budgetcounselops.qa.case_review | case review | QUALITY_CHECK | Review checks consent, plan realism, referral fit and follow-up completeness. | Improves reliability. |
| budgetcounselops.demob.transfer | transfer plan | METHOD | Ongoing cases transfer to financial counselor, case manager or partner agency. | Maintains support. |
| budgetcounselops.review.after_action | after-action review | METHOD | Review captures income gaps, debt patterns, benefits barriers and counseling workflow lessons. | Improves future intake. |
