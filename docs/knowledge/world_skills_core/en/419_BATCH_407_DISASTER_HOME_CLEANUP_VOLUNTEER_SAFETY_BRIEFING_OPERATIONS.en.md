# BATCH 407: Disaster Home Cleanup Volunteer Safety Briefing Operations

**KnowledgeUnits:** 44  
**Namespace:** `cleanupbriefops.*`  
**Scope:** hazards, PPE, tools, heat, mold, utilities, stop-work rules and documentation.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| cleanupbriefops.intake.crew_roster | crew roster | RECORD | Roster records volunteers, lead, organization, contact, skills and emergency contact. | Tracks people. |
| cleanupbriefops.intake.site_summary | site summary | RECORD | Summary captures address, damage type, occupancy, access, known hazards and work limits. | Frames briefing. |
| cleanupbriefops.intake.permission | permission check | QUALITY_CHECK | Brief confirms resident permission, scope and access before work starts. | Prevents unauthorized work. |
| cleanupbriefops.intake.briefing_time | briefing time | RECORD | Briefing time records date, location, crew, trainer and materials used. | Creates proof. |
| cleanupbriefops.hazards.structural | structural hazard | SAFETY_RULE | Volunteers are warned about sagging floors, unstable walls, roofs and stairs. | Prevents collapse injuries. |
| cleanupbriefops.hazards.electrical | electrical hazard | SAFETY_RULE | Brief covers downed wires, wet outlets, panels and unknown energized equipment. | Prevents shock. |
| cleanupbriefops.hazards.sharps | sharps hazard | SAFETY_RULE | Broken glass, nails, metal edges and needles require tool handling and disposal rules. | Prevents cuts. |
| cleanupbriefops.hazards.animals | animal hazard | SAFETY_RULE | Brief covers displaced pets, insects, snakes, rodents and bite reporting. | Reduces exposure. |
| cleanupbriefops.ppe.gloves | glove selection | METHOD | Gloves are matched to debris, chemicals, wet work and dexterity needs. | Protects hands. |
| cleanupbriefops.ppe.eye | eye protection | SAFETY_RULE | Eye protection is required for debris, dust, splashing and tool use. | Prevents eye injury. |
| cleanupbriefops.ppe.respiratory | respiratory protection | SAFETY_RULE | Respiratory guidance distinguishes dust, mold, smoke residue and chemical concern. | Reduces inhalation risk. |
| cleanupbriefops.ppe.footwear | footwear rule | SAFETY_RULE | Boots or sturdy closed shoes protect from punctures, mud and debris. | Prevents foot injuries. |
| cleanupbriefops.tools.tool_match | tool match | METHOD | Tools are matched to task, volunteer skill and site conditions. | Reduces misuse. |
| cleanupbriefops.tools.inspection | tool inspection | QUALITY_CHECK | Tools are checked for damage, guards, cords, batteries and safe handles. | Prevents accidents. |
| cleanupbriefops.tools.ladder | ladder boundary | SAFETY_RULE | Ladder use follows height, surface, weather and trained-user limits. | Controls fall risk. |
| cleanupbriefops.tools.power_tool | power tool rule | SAFETY_RULE | Power tools are limited to trained users with PPE and supervisor approval. | Avoids severe injury. |
| cleanupbriefops.heat.hydration | hydration plan | METHOD | Brief sets water, electrolyte, shade and break expectations. | Reduces heat illness. |
| cleanupbriefops.heat.symptoms | heat symptoms | SAFETY_RULE | Volunteers learn heat exhaustion and heat stroke warning signs. | Enables early action. |
| cleanupbriefops.heat.work_rest | work-rest cycle | METHOD | Work-rest timing adapts to temperature, humidity, PPE and volunteer condition. | Controls fatigue. |
| cleanupbriefops.heat.buddy_check | buddy check | METHOD | Volunteers monitor partners for dizziness, confusion, weakness or overexertion. | Improves safety. |
| cleanupbriefops.mold.exposure | mold exposure | SAFETY_RULE | Brief explains when mold cleanup is unsuitable for volunteers or sensitive occupants. | Avoids harm. |
| cleanupbriefops.mold.containment | containment basics | METHOD | Simple containment separates dirty and clean zones where feasible. | Limits spread. |
| cleanupbriefops.mold.discard | discard guidance | METHOD | Porous contaminated materials are handled according to local cleanup guidance. | Supports safe removal. |
| cleanupbriefops.mold.stop_trigger | mold stop trigger | SAFETY_RULE | Large growth, respiratory symptoms or hidden moisture can stop volunteer work. | Prevents overreach. |
| cleanupbriefops.utilities.gas | gas concern | SAFETY_RULE | Smell of gas or damaged gas line triggers evacuation and utility call. | Prevents explosion. |
| cleanupbriefops.utilities.water | water shutoff | METHOD | Brief identifies when water shutoff or leak reporting is needed. | Reduces damage. |
| cleanupbriefops.utilities.power_status | power status | RECORD | Crew records whether power is confirmed off, unknown or restricted. | Guides work. |
| cleanupbriefops.utilities.generator | generator warning | SAFETY_RULE | Generators are kept outdoors and away from openings due to carbon monoxide risk. | Prevents poisoning. |
| cleanupbriefops.stopwork.stop_authority | stop authority | SAFETY_RULE | Any volunteer can stop work for unsafe condition or unclear scope. | Empowers safety. |
| cleanupbriefops.stopwork.escalation | escalation path | METHOD | Stop-work issues route to crew lead, coordinator, resident or professional responder. | Resolves hazards. |
| cleanupbriefops.stopwork.weather | weather stop | SAFETY_RULE | Lightning, high wind, extreme heat, floodwater or smoke can halt work. | Protects crew. |
| cleanupbriefops.stopwork.conflict | conflict stop | SAFETY_RULE | Aggression, weapons, legal dispute or unsafe access triggers withdrawal. | Protects volunteers. |
| cleanupbriefops.documentation.attendance | attendance record | RECORD | Attendance captures volunteers present and acknowledgement of safety briefing. | Proves briefing. |
| cleanupbriefops.documentation.hazard_log | hazard log | RECORD | Hazard log records conditions found, controls used and unresolved risks. | Supports handoff. |
| cleanupbriefops.documentation.incident | incident report | RECORD | Incident records injury, near miss, illness, property damage or safety stop. | Enables follow-up. |
| cleanupbriefops.documentation.photo_policy | photo policy | SAFETY_RULE | Photos follow resident consent, privacy and hazard documentation rules. | Prevents misuse. |
| cleanupbriefops.communication.resident_talk | resident discussion | METHOD | Crew explains scope, safety limits, expected duration and unfinished items to resident. | Sets expectations. |
| cleanupbriefops.communication.team_radio | team communication | METHOD | Brief defines check-in, emergency call, lost member and regroup procedure. | Keeps crew coordinated. |
| cleanupbriefops.communication.language | language support | METHOD | Safety briefing uses interpreter, translated sheet or plain visual checklist when needed. | Improves comprehension. |
| cleanupbriefops.communication.end_brief | end-of-shift brief | METHOD | Crew reviews injuries, hazards, unfinished work, tools and resident follow-up. | Closes shift. |
| cleanupbriefops.qa.supervisor_observe | supervisor observation | QUALITY_CHECK | Supervisor samples crews for PPE, tool control, heat breaks and scope discipline. | Reinforces safety. |
| cleanupbriefops.metrics.briefed_count | briefed count | MEASUREMENT | Count tracks volunteers briefed by site, organization and date. | Shows coverage. |
| cleanupbriefops.metrics.incident_rate | incident rate | MEASUREMENT | Rate tracks incidents or near misses per volunteer shift. | Guides training. |
| cleanupbriefops.review.after_action | after-action review | METHOD | Review captures hazards, PPE gaps, stop-work events, heat controls and documentation lessons. | Improves future briefings. |
