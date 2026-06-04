# BATCH 414: Disaster Small Business Recovery Intake Operations

**KnowledgeUnits:** 44  
**Namespace:** `smbrecoveryops.*`  
**Scope:** damage, revenue loss, insurance, loans, grants, documents, referrals and tracking.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| smbrecoveryops.intake.request_source | request source | RECORD | Source records business owner, chamber, hotline, lender, agency, nonprofit or outreach. | Shows entry path. |
| smbrecoveryops.intake.business_profile | business profile | RECORD | Profile captures business name, owner, location, sector, employees and contact. | Defines applicant. |
| smbrecoveryops.intake.operating_status | operating status | RECORD | Status distinguishes open, limited, closed, displaced, online-only or relocating. | Shows disruption. |
| smbrecoveryops.intake.urgency | urgency model | MODEL | Urgency weighs payroll, rent, inventory loss, closure length, debt and community service role. | Prioritizes help. |
| smbrecoveryops.damage.physical_damage | physical damage | RECORD | Damage record captures building, equipment, inventory, vehicles, utilities and access. | Documents loss. |
| smbrecoveryops.damage.photo_evidence | photo evidence | RECORD | Photos document damaged areas, equipment, inventory and exterior context when allowed. | Supports claims. |
| smbrecoveryops.damage.estimate | repair estimate | RECORD | Estimate records vendor, scope, cost, assumptions and date. | Supports funding. |
| smbrecoveryops.damage.access_issue | access issue | CONSTRAINT | Access issue records road closure, unsafe building, landlord restriction or utility outage. | Explains closure. |
| smbrecoveryops.revenue.revenue_loss | revenue loss | RECORD | Loss compares pre-disaster and post-disaster sales, bookings or contracts. | Shows economic impact. |
| smbrecoveryops.revenue.cashflow | cashflow need | MODEL | Cashflow need weighs expenses, payroll, rent, inventory and expected reopening date. | Targets support. |
| smbrecoveryops.revenue.payroll | payroll pressure | RECORD | Payroll record captures employees, missed payroll, reduced hours or layoffs. | Guides workforce aid. |
| smbrecoveryops.revenue.records_gap | records gap | RECORD | Gap notes missing POS, bank, tax, invoice or bookkeeping records. | Directs document help. |
| smbrecoveryops.insurance.policy_info | policy information | RECORD | Policy captures carrier, number, coverage type, deductible and claim contact. | Starts claim coordination. |
| smbrecoveryops.insurance.claim_status | claim status | RECORD | Status records filed, adjuster assigned, paid, denied, delayed or not covered. | Shows funding path. |
| smbrecoveryops.insurance.denial_reason | denial reason | RECORD | Denial records exclusion, deductible, documentation gap or coverage limit. | Guides appeal/referral. |
| smbrecoveryops.insurance.duplication | duplication check | QUALITY_CHECK | Assistance review checks insurance, grants, loans and donations overlap. | Prevents duplicate benefits. |
| smbrecoveryops.loans.loan_screen | loan screen | MODEL | Screen checks interest tolerance, debt capacity, collateral, credit and eligibility. | Routes loan options. |
| smbrecoveryops.loans.sba_referral | SBA referral | METHOD | Referral captures disaster loan interest, required documents and application status. | Connects federal path. |
| smbrecoveryops.loans.local_lender | local lender referral | METHOD | Local lender path captures bank, CDFI, credit union or emergency fund option. | Expands financing. |
| smbrecoveryops.loans.loan_status | loan status | RECORD | Status records inquiry, application, approved, denied, withdrawn or funded. | Tracks progress. |
| smbrecoveryops.grants.grant_match | grant match | METHOD | Matching finds grants by sector, geography, ownership, damage and use of funds. | Builds options. |
| smbrecoveryops.grants.eligibility | grant eligibility | QUALITY_CHECK | Eligibility checks business size, location, disaster impact, registration and expenses. | Avoids wasted filing. |
| smbrecoveryops.grants.application_status | application status | RECORD | Status records draft, submitted, deficient, approved, denied or paid. | Tracks aid. |
| smbrecoveryops.grants.use_restriction | use restriction | CONSTRAINT | Restrictions identify eligible payroll, rent, equipment, inventory or working capital uses. | Prevents misuse. |
| smbrecoveryops.documents.document_list | document list | RECORD | List includes tax, bank, lease, payroll, insurance, licenses, photos and estimates. | Organizes packet. |
| smbrecoveryops.documents.missing_doc | missing document | RECORD | Missing documents record owner, source, deadline and workaround. | Drives completion. |
| smbrecoveryops.documents.license_check | license check | QUALITY_CHECK | Business registration, permit, tax ID or professional license is verified where needed. | Supports eligibility. |
| smbrecoveryops.documents.secure_storage | secure storage | SAFETY_RULE | Financial and identity documents are stored with restricted access. | Protects business. |
| smbrecoveryops.referral.technical_assist | technical assistance | METHOD | Referral connects business to SBDC, accountant, chamber or recovery advisor. | Adds expertise. |
| smbrecoveryops.referral.workforce | workforce referral | METHOD | Workforce referral handles layoffs, hiring, wage support or employee benefits. | Supports employees. |
| smbrecoveryops.referral.real_estate | site relocation referral | METHOD | Relocation referral handles temporary site, permits, lease and utilities. | Restores operations. |
| smbrecoveryops.referral.legal | legal referral | METHOD | Legal path handles lease dispute, insurance denial, contract issue or debt pressure. | Reduces risk. |
| smbrecoveryops.tracking.case_status | case status | RECORD | Status distinguishes intake, document gathering, referred, application pending, funded or closed. | Shows progress. |
| smbrecoveryops.tracking.followup_queue | follow-up queue | RECORD | Queue tracks next contact, deadline, owner and unresolved barrier. | Maintains continuity. |
| smbrecoveryops.tracking.outcome | outcome record | RECORD | Outcome records reopened, funded, referred, denied, closed, relocated or unreachable. | Closes loop. |
| smbrecoveryops.tracking.reopen | reopen rule | METHOD | Case reopens for new denial, damage, funding source or document. | Handles change. |
| smbrecoveryops.communication.owner_update | owner update | METHOD | Update explains options, documents, deadlines, risks and next steps. | Reduces uncertainty. |
| smbrecoveryops.communication.partner_update | partner update | METHOD | Partners receive aggregate demand, sector needs, funding gaps and referral barriers. | Coordinates ecosystem. |
| smbrecoveryops.communication.language | language support | METHOD | Interpretation or translated forms support owner intake and applications. | Improves access. |
| smbrecoveryops.reporting.daily_summary | daily summary | MEASUREMENT | Summary reports businesses assisted, sectors, closures, applications and urgent needs. | Informs recovery. |
| smbrecoveryops.metrics.businesses_served | businesses served | MEASUREMENT | Count tracks businesses served by sector, size, geography and status. | Shows reach. |
| smbrecoveryops.metrics.funding_pipeline | funding pipeline | MEASUREMENT | Pipeline tracks requested, approved, denied and disbursed funds. | Shows finance gap. |
| smbrecoveryops.metrics.reopen_rate | reopen rate | MEASUREMENT | Rate tracks businesses reopened or stabilized after support. | Measures outcome. |
| smbrecoveryops.review.after_action | after-action review | METHOD | Review captures sector needs, documentation barriers, insurance gaps and funding lessons. | Improves future intake. |
