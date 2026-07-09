# BATCH 448: Emergency Communication Board Distribution

**KnowledgeUnits:** 44  
**Namespace:** `commboardops.*`  
**Scope:** intake, symbol boards, language needs, training, inventory, delivery and follow-up.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| commboardops.intake.request_source | request source | RECORD | Source records shelter desk, disability advocate, clinic, school, caregiver, interpreter team or outreach worker. | Shows entry path. |
| commboardops.intake.user_profile | user profile | RECORD | Profile captures age group, communication method, language, disability need, caregiver and current site. | Defines support. |
| commboardops.intake.communication_barrier | communication barrier | RECORD | Barrier notes speech loss, hearing barrier, language gap, cognitive access, stress response or device loss. | Frames need. |
| commboardops.intake.urgency_score | urgency score | MODEL | Score weighs medical triage, shelter navigation, food needs, safety, caregiver absence and language isolation. | Prioritizes distribution. |
| commboardops.eligibility.emergency_link | emergency link | CONTROL | Link verifies communication board need is tied to emergency access, displacement or service disruption. | Targets supplies. |
| commboardops.eligibility.use_context | use context | RECORD | Context records shelter, clinic, feeding site, field outreach, school, family reunification or transport. | Selects board type. |
| commboardops.eligibility.duplicate_check | duplicate check | CONTROL | Check compares user, site, board type, language, caregiver and prior issue records. | Avoids duplication. |
| commboardops.board.board_type | board type | MODEL | Type separates picture board, alphabet board, pain scale, needs board, translation board or low-vision board. | Matches barrier. |
| commboardops.board.symbol_set | symbol set | RECORD | Set lists symbols for food, water, pain, restroom, medicine, family, danger, transport and help. | Supports quick expression. |
| commboardops.board.language_set | language set | RECORD | Set records printed languages, pictograms, plain language, braille add-on or interpreter note. | Improves access. |
| commboardops.board.low_vision_format | low-vision format | CONTROL | Format uses high contrast, large print, tactile cues or glare control where needed. | Supports visibility. |
| commboardops.board.durable_format | durable format | CONTROL | Format uses lamination, wipeable surface, tether, pocket size or wall mount. | Survives field use. |
| commboardops.inventory.asset_record | asset record | RECORD | Record captures board type, language, quantity, site, condition and issue status. | Tracks inventory. |
| commboardops.inventory.stock_threshold | stock threshold | CONTROL | Threshold flags low supply by language, board type, site and user group. | Prevents stockouts. |
| commboardops.inventory.print_batch | print batch | RECORD | Batch records version, date, printer, paper, lamination and quality check. | Supports consistency. |
| commboardops.inventory.version_control | version control | CONTROL | Control avoids mixing outdated symbols, wrong translations or unapproved layouts. | Prevents confusion. |
| commboardops.training.staff_orientation | staff orientation | PROCESS | Orientation shows how to offer choices, wait for response, confirm meaning and avoid rushing. | Makes boards useful. |
| commboardops.training.caregiver_brief | caregiver brief | PROCESS | Brief explains board layout, yes/no method, pointing support and cleaning. | Extends use. |
| commboardops.training.user_demo | user demo | PROCESS | Demo lets user practice needs, pain, location, family, refusal and emergency messages. | Confirms usability. |
| commboardops.training.misuse_warning | misuse warning | CONTROL | Warning prevents staff from assuming answers, forcing choices or replacing interpreters when needed. | Protects autonomy. |
| commboardops.delivery.site_distribution | site distribution | PROCESS | Distribution places boards at intake, medical desk, feeding line, dorm area, transport and information desk. | Makes access visible. |
| commboardops.delivery.individual_issue | individual issue | RECORD | Issue records user, board type, language, caregiver, date and follow-up need. | Personalizes support. |
| commboardops.delivery.mobile_delivery | mobile delivery | PROCESS | Delivery routes boards to homebound clients, field teams, clinics, schools or temporary housing. | Reaches barriers. |
| commboardops.delivery.handoff_proof | handoff proof | RECORD | Proof records recipient, quantity, location, board version and instruction given. | Closes custody. |
| commboardops.cleaning.cleaning_rule | cleaning rule | CONTROL | Rule defines wipeable surfaces, cleaning frequency, shared-use handling and damaged-board removal. | Reduces infection risk. |
| commboardops.cleaning.damage_check | damage check | PROCESS | Check removes torn, unreadable, contaminated, outdated or missing boards from use. | Maintains quality. |
| commboardops.accessibility.interpreter_link | interpreter link | PROCESS | Link routes complex, legal, medical or emotional communication to interpreter or specialist support. | Avoids overreliance. |
| commboardops.accessibility.cultural_check | cultural check | CONTROL | Check reviews symbols, gestures, translations and sensitive images for local appropriateness. | Reduces misunderstanding. |
| commboardops.accessibility.literacy_support | literacy support | PROCESS | Support uses pictograms, plain wording, pointing, color cues and staff facilitation. | Helps low-literacy users. |
| commboardops.records.case_file | case file | RECORD | File links intake, board selection, issue, training, follow-up and closure. | Supports audit. |
| commboardops.records.site_log | site log | RECORD | Log tracks board counts, locations, staff trained, missing boards and restock needs. | Manages sites. |
| commboardops.records.exception_log | exception log | RECORD | Log captures wrong language, lost board, misunderstanding, interpreter need, damage or refusal. | Enables review. |
| commboardops.records.version_note | version note | RECORD | Note records board edition, symbol source, language review and approved use setting. | Prevents wrong versions. |
| commboardops.privacy.minimum_data | minimum data | CONTROL | Minimum data limits disability, language and medical details to support need. | Protects users. |
| commboardops.privacy.public_display | public display privacy | CONTROL | Display avoids exposing names, diagnoses, immigration status or sensitive needs. | Preserves dignity. |
| commboardops.communication.site_notice | site notice | PROCESS | Notice tells staff where boards are available and how to request more. | Promotes use. |
| commboardops.communication.user_update | user update | PROCESS | Update explains board purpose, return or keep rule, cleaning and where to get help. | Clarifies expectations. |
| commboardops.communication.partner_request | partner request | PROCESS | Request asks disability groups, translators, printers or clinics for board versions and advice. | Expands capacity. |
| commboardops.metrics.distribution_count | distribution count | METRIC | Count tracks boards issued by type, language, site and user group. | Measures reach. |
| commboardops.metrics.training_coverage | training coverage | METRIC | Coverage tracks staff or caregiver orientation sessions and sites covered. | Shows readiness. |
| commboardops.metrics.followup_success | follow-up success | METRIC | Success records whether board helped communication or needed replacement or referral. | Measures usefulness. |
| commboardops.metrics.replacement_rate | replacement rate | METRIC | Rate tracks damaged, lost, outdated or wrong-language boards needing replacement. | Guides stock planning. |
| commboardops.closeout.user_confirmation | user confirmation | PROCESS | Confirmation checks board usability, language fit, damage and remaining communication barriers. | Closes loop. |
| commboardops.closeout.after_action | after-action note | RECORD | Note captures language gaps, symbol issues, training needs and stock lessons. | Improves next activation. |
