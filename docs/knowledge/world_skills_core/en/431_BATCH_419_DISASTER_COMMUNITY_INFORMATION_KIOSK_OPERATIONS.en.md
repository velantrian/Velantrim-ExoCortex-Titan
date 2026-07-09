# BATCH 419: Disaster Community Information Kiosk Operations

**KnowledgeUnits:** 44  
**Namespace:** `infokioskops.*`  
**Scope:** staffing, scripts, maps, referrals, printed materials, updates and feedback.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| infokioskops.activation.site_selection | kiosk site selection | METHOD | Site selection checks foot traffic, shelter proximity, accessibility, shade, security and power. | Places help where useful. |
| infokioskops.activation.service_scope | service scope | CONSTRAINT | Scope defines information, referrals, maps, forms and excluded advice topics. | Prevents overpromising. |
| infokioskops.activation.operating_hours | operating hours | RECORD | Hours record open times, peak periods, closures and backup coverage. | Sets public expectation. |
| infokioskops.activation.command_link | command link | RECORD | Kiosk links to public information, operations, logistics and partner liaisons. | Keeps messages aligned. |
| infokioskops.staffing.roster | staffing roster | RECORD | Roster lists greeters, referral staff, interpreter support, runners and supervisor. | Maintains coverage. |
| infokioskops.staffing.role_brief | role brief | METHOD | Brief defines greeting, triage, referral, rumor logging and escalation duties. | Aligns staff. |
| infokioskops.staffing.volunteer_boundary | volunteer boundary | CONSTRAINT | Volunteers give approved information and route complex cases to qualified staff. | Controls risk. |
| infokioskops.staffing.shift_handoff | shift handoff | METHOD | Handoff covers updates, shortages, rumors, difficult cases and material status. | Preserves continuity. |
| infokioskops.scripts.core_script | core script | RECORD | Script covers greeting, needs triage, available services, privacy and next steps. | Standardizes service. |
| infokioskops.scripts.rumor_response | rumor response | METHOD | Rumor script uses verified facts, uncertainty language and source referral. | Reduces misinformation. |
| infokioskops.scripts.sensitive_topic | sensitive topic routing | SAFETY_RULE | Medical, legal, immigration, benefits and safety topics route to qualified channels. | Protects residents. |
| infokioskops.scripts.language_plain | plain language | METHOD | Scripts use short sentences, local terms and nontechnical service names. | Improves comprehension. |
| infokioskops.maps.service_map | service map | RECORD | Map shows shelters, food, water, charging, clinics, transport and assistance centers. | Guides movement. |
| infokioskops.maps.route_update | route update | METHOD | Routes update for closures, hazards, transit changes and access restrictions. | Prevents bad directions. |
| infokioskops.maps.accessibility_layer | accessibility layer | RECORD | Map notes wheelchair access, quiet space, interpreters, restrooms and transport options. | Supports equity. |
| infokioskops.maps.print_version | printed map version | RECORD | Printed maps carry version date, source and update warning. | Avoids stale maps. |
| infokioskops.referrals.directory | referral directory | RECORD | Directory lists providers, hours, eligibility, contacts, capacity and language access. | Supports accurate referral. |
| infokioskops.referrals.warm_referral | warm referral | METHOD | Warm referral confirms receiving service, needed documents and next contact. | Reduces drop-off. |
| infokioskops.referrals.closed_loop | closed-loop referral | QUALITY_CHECK | Closed-loop check verifies urgent residents reached the referred service where feasible. | Confirms help. |
| infokioskops.referrals.unavailable | unavailable service | RECORD | Unavailable services record reason, alternative, update time and requester impact. | Maintains honesty. |
| infokioskops.materials.flyer_master | flyer master | RECORD | Master tracks approved flyers, versions, languages, source and expiration. | Controls printed info. |
| infokioskops.materials.form_packet | form packet | RECORD | Packets group applications, checklists, maps and instruction sheets by need. | Speeds handout. |
| infokioskops.materials.restock | restock trigger | METHOD | Restock uses daily counts, peak use and minimum stock thresholds. | Prevents shortages. |
| infokioskops.materials.removal | stale material removal | QUALITY_CHECK | Old flyers and superseded maps are pulled from display. | Prevents misinformation. |
| infokioskops.updates.update_source | update source | RECORD | Updates record source agency, timestamp, approver and affected materials. | Creates traceability. |
| infokioskops.updates.bulletin_cycle | bulletin cycle | METHOD | Bulletin cycle schedules checks for service status, closures and new resources. | Keeps current. |
| infokioskops.updates.emergency_notice | emergency notice | SAFETY_RULE | Urgent warnings supersede routine materials and require command confirmation. | Protects public. |
| infokioskops.updates.version_board | version board | RECORD | Board shows last update time and high-change items. | Signals freshness. |
| infokioskops.feedback.feedback_card | feedback card | RECORD | Card captures unanswered questions, bad referrals, access barriers and suggestions. | Finds gaps. |
| infokioskops.feedback.rumor_log | rumor log | RECORD | Rumor log records claim, source area, frequency and response given. | Guides public information. |
| infokioskops.feedback.unmet_need | unmet need | RECORD | Unmet need log captures request, barrier, location and possible partner. | Informs planning. |
| infokioskops.feedback.complaint_route | complaint route | METHOD | Complaints route to supervisor, partner agency or formal process. | Handles issues. |
| infokioskops.privacy.minimum_data | minimum data | SAFETY_RULE | Kiosk avoids collecting personal data unless needed for referral or follow-up. | Reduces exposure. |
| infokioskops.privacy.private_issue | private issue handling | METHOD | Sensitive conversations move away from public line or to qualified desk. | Preserves dignity. |
| infokioskops.safety.site_safety | site safety | SAFETY_RULE | Site safety covers heat, crowding, trip hazards, lighting, security and weather. | Protects staff/public. |
| infokioskops.safety.conflict_deescalation | conflict de-escalation | METHOD | Staff use calm scripts, supervisor handoff and security route for conflict. | Reduces escalation. |
| infokioskops.reporting.daily_summary | daily summary | MEASUREMENT | Summary reports visitors, referrals, materials used, rumors, gaps and incidents. | Informs command. |
| infokioskops.reporting.partner_gap | partner gap report | RECORD | Gap report shows services missing, unavailable or repeatedly requested. | Drives resource action. |
| infokioskops.metrics.visitor_count | visitor count | MEASUREMENT | Count tracks visitors by time, need category and language when feasible. | Shows demand. |
| infokioskops.metrics.referral_count | referral count | MEASUREMENT | Count tracks referrals by provider, topic and completion status. | Shows output. |
| infokioskops.metrics.material_usage | material usage | MEASUREMENT | Usage tracks flyers, maps and packets distributed by type. | Guides printing. |
| infokioskops.qa.mystery_check | mystery check | QUALITY_CHECK | Supervisor samples kiosk accuracy, courtesy, referral quality and material freshness. | Improves service. |
| infokioskops.demob.closeout | kiosk closeout | METHOD | Closeout removes materials, archives logs, transfers open issues and restores site. | Ends cleanly. |
| infokioskops.review.after_action | after-action review | METHOD | Review captures staffing, scripts, maps, referral gaps, rumors and feedback lessons. | Improves future kiosks. |
