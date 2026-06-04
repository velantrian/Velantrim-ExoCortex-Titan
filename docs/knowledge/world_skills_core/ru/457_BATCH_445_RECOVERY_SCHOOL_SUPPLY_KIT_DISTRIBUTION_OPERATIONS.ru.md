# BATCH 445: Recovery School Supply Kit Distribution Operations

**KnowledgeUnits:** 44  
**Namespace:** `schoolsupplykitops.*`  
**Scope:** student intake, grade bands, inventory, pickup, delivery, accessibility and reporting.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| schoolsupplykitops.intake.request_source | request source | RECORD | Source records school liaison, shelter desk, caseworker, family center, teacher, hotline or self-referral. | Shows entry path. |
| schoolsupplykitops.intake.student_profile | student profile | RECORD | Profile captures grade band, school, language, caregiver contact, displacement status and access needs. | Defines kit need. |
| schoolsupplykitops.intake.household_count | household count | RECORD | Count records number of students, grade levels and duplicate household requests. | Prevents gaps and duplication. |
| schoolsupplykitops.intake.urgency_score | urgency score | MODEL | Score weighs school start date, lost supplies, transportation barrier, special need and caregiver availability. | Prioritizes distribution. |
| schoolsupplykitops.eligibility.recovery_link | recovery link | CONTROL | Link verifies supplies are needed because of displacement, damage, lost backpack or school disruption. | Targets aid. |
| schoolsupplykitops.eligibility.school_confirmation | school confirmation | CONTROL | Confirmation checks enrollment, temporary enrollment, McKinney-style displacement support or school liaison note. | Validates need. |
| schoolsupplykitops.eligibility.duplicate_check | duplicate check | CONTROL | Check compares student, caregiver, school, grade band, pickup site and prior kit issue. | Avoids double issue. |
| schoolsupplykitops.grade.kit_band | kit band | MODEL | Band separates early elementary, upper elementary, middle, high school and special program supply needs. | Fits age. |
| schoolsupplykitops.grade.teacher_addon | teacher addon | RECORD | Addon captures calculators, binders, art tools, lab notebooks or course-specific items. | Handles exceptions. |
| schoolsupplykitops.grade.accessibility_item | accessibility item | RECORD | Item records adaptive grips, large-print notebooks, headphones, visual supports or sensory tools. | Supports inclusion. |
| schoolsupplykitops.grade.language_insert | language insert | PROCESS | Insert includes multilingual school contacts, schedule basics, bus help and family support notes. | Helps caregivers. |
| schoolsupplykitops.inventory.item_master | item master | RECORD | Master lists notebooks, pencils, pens, folders, backpack, hygiene items, calculator and grade-specific items. | Defines stock. |
| schoolsupplykitops.inventory.stock_count | stock count | RECORD | Count tracks on-hand, reserved, packed, issued, damaged, expired or donated items. | Maintains control. |
| schoolsupplykitops.inventory.substitution_rule | substitution rule | CONTROL | Rule permits equivalent items when exact brand, size or color is unavailable. | Keeps distribution moving. |
| schoolsupplykitops.inventory.donation_sort | donation sorting | PROCESS | Sorting separates usable, unsafe, damaged, age-inappropriate, duplicate and surplus supplies. | Protects students. |
| schoolsupplykitops.packing.pack_list | pack list | RECORD | List defines required items by grade band, optional add-ons and language inserts. | Standardizes kits. |
| schoolsupplykitops.packing.quality_check | quality check | PROCESS | Check verifies full contents, correct band, safe items, backpack condition and label. | Prevents bad kits. |
| schoolsupplykitops.packing.family_bundle | family bundle | PROCESS | Bundle groups multiple student kits by caregiver, pickup site and delivery need. | Speeds handoff. |
| schoolsupplykitops.packing.label_code | label code | CONTROL | Code uses non-stigmatizing identifiers and avoids public display of displacement status. | Protects dignity. |
| schoolsupplykitops.pickup.site_schedule | site schedule | RECORD | Schedule records school, shelter, community center, mobile stop, hours and staff contact. | Organizes pickup. |
| schoolsupplykitops.pickup.identity_check | identity check | CONTROL | Check confirms caregiver, student, liaison or authorized pickup without excessive documentation. | Balances access. |
| schoolsupplykitops.pickup.queue_plan | queue plan | PROCESS | Plan handles lines, shade, seating, language help, privacy and traffic. | Improves experience. |
| schoolsupplykitops.pickup.handoff_proof | handoff proof | RECORD | Proof records kit band, count, recipient role, date and exception notes. | Supports audit. |
| schoolsupplykitops.delivery.delivery_route | delivery route | PROCESS | Route delivers to shelters, temporary housing, schools or homebound families when pickup is impossible. | Reaches barriers. |
| schoolsupplykitops.delivery.failed_delivery | failed delivery | STATE | Failed delivery logs no contact, moved household, school mismatch, unsafe access or returned kit. | Triggers follow-up. |
| schoolsupplykitops.delivery.accessible_handoff | accessible handoff | PROCESS | Handoff supports mobility barriers, caregiver limits, sensory needs and safe contact instructions. | Includes vulnerable families. |
| schoolsupplykitops.communication.family_notice | family notice | PROCESS | Notice explains pickup time, kit contents, documents if any, delivery option and school contacts. | Reduces confusion. |
| schoolsupplykitops.communication.school_update | school update | PROCESS | Update informs liaisons about kit availability, unmet grade bands, special requests and distribution counts. | Aligns partners. |
| schoolsupplykitops.communication.referral_note | referral note | RECORD | Note routes uniforms, devices, transportation, meals, counseling or enrollment needs to proper support. | Extends help. |
| schoolsupplykitops.records.case_file | case file | RECORD | File links intake, eligibility, kit band, pickup or delivery, proof and follow-up. | Supports audit. |
| schoolsupplykitops.records.inventory_log | inventory log | RECORD | Log records donations, purchases, packing, transfers, issues, damage and remaining stock. | Controls supplies. |
| schoolsupplykitops.records.exception_log | exception log | RECORD | Log captures stockout, duplicate request, wrong grade, failed pickup, privacy issue or damaged kit. | Enables review. |
| schoolsupplykitops.records.consent_note | consent note | RECORD | Note records caregiver permission for pickup, delivery, school liaison coordination and follow-up. | Documents consent. |
| schoolsupplykitops.accessibility.language_support | language support | PROCESS | Support provides translated notices, interpreters, bilingual staff or pictorial instructions. | Improves access. |
| schoolsupplykitops.accessibility.stigma_control | stigma control | CONTROL | Control avoids visible labels or separate lines that identify disaster-affected students. | Protects dignity. |
| schoolsupplykitops.accessibility.special_request | special request | PROCESS | Request handles adaptive supplies, sensory items, uniforms, assistive tech referral or extra materials. | Meets real needs. |
| schoolsupplykitops.reporting.daily_summary | daily summary | RECORD | Summary reports kits issued, grade bands, sites, unmet demand, stockouts and referrals. | Briefs partners. |
| schoolsupplykitops.reporting.donor_report | donor report | RECORD | Report summarizes aggregate distribution, needs and acknowledgments without exposing student data. | Supports funding. |
| schoolsupplykitops.metrics.fill_rate | fill rate | METRIC | Rate compares eligible requests with complete kits issued. | Measures service. |
| schoolsupplykitops.metrics.grade_stock_gap | grade stock gap | METRIC | Gap tracks shortages by grade band and item type. | Guides procurement. |
| schoolsupplykitops.metrics.pickup_completion | pickup completion | METRIC | Completion compares scheduled pickups, completed pickups, no-shows and deliveries. | Improves operations. |
| schoolsupplykitops.closeout.family_confirmation | family confirmation | PROCESS | Confirmation checks kit received, correct grade, missing items and remaining school barriers. | Closes loop. |
| schoolsupplykitops.closeout.stock_reconciliation | stock reconciliation | PROCESS | Reconciliation compares purchased, donated, packed, issued, damaged and remaining supplies. | Finds errors. |
| schoolsupplykitops.closeout.after_action | after-action note | RECORD | Note captures grade demand, access barriers, partner issues, privacy concerns and procurement lessons. | Improves next cycle. |
