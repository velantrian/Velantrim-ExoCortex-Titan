# BATCH 406: Disaster Repair Volunteer Work Order Coordination

**KnowledgeUnits:** 44  
**Namespace:** `repairvolops.*`  
**Scope:** intake, scope, safety screen, crew assignment, materials, completion and QA.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| repairvolops.intake.request_source | request source | RECORD | Source records hotline, case manager, survivor center, faith group, inspector or outreach. | Shows entry path. |
| repairvolops.intake.property_record | property record | RECORD | Record captures address, owner/tenant status, contact, access, damage type and occupancy. | Defines job. |
| repairvolops.intake.permission | permission to work | RECORD | Permission documents resident consent, property access, limits and liability acknowledgement. | Enables volunteer work. |
| repairvolops.intake.priority | priority model | MODEL | Priority weighs habitability, vulnerable occupants, safety risk, weather exposure and resources. | Orders jobs. |
| repairvolops.scope.scope_summary | scope summary | RECORD | Summary describes requested repair, affected area, photos and known constraints. | Sets expectation. |
| repairvolops.scope.work_category | work category | RECORD | Category distinguishes muck-out, tarping, debris, minor repair, accessibility or cleanup. | Routes skills. |
| repairvolops.scope.out_of_scope | out-of-scope rule | CONSTRAINT | Electrical, structural, hazardous material or licensed work may require professional referral. | Protects residents. |
| repairvolops.scope.estimate_visit | estimate visit | METHOD | Assessment visit verifies scope, materials, crew size, safety and resident readiness. | Plans job. |
| repairvolops.safety.hazard_screen | hazard screen | SAFETY_RULE | Screen checks structure, utilities, mold, asbestos, animals, sharps, heat and security. | Protects crews. |
| repairvolops.safety.stop_work | stop-work rule | SAFETY_RULE | Stop-work triggers include unsafe structure, live utilities, weapons, severe weather or health hazard. | Prevents injury. |
| repairvolops.safety.ppe_need | PPE need | RECORD | PPE need lists gloves, eye protection, respirator, boots, hard hat or fall protection. | Prepares crews. |
| repairvolops.safety.site_brief | site safety brief | METHOD | Brief covers hazards, task limits, tool use, hydration, communication and emergency contact. | Aligns crew. |
| repairvolops.crew.skill_match | skill match | METHOD | Crew assignment matches tasks to skills, tools, language, accessibility and supervision. | Improves quality. |
| repairvolops.crew.crew_roster | crew roster | RECORD | Roster records volunteers, leader, contact, arrival time and organization. | Tracks deployment. |
| repairvolops.crew.background_rule | background rule | CONSTRAINT | Work involving minors, vulnerable residents or private spaces follows screening policy. | Protects households. |
| repairvolops.crew.shift_plan | shift plan | METHOD | Plan defines work hours, breaks, travel, meals, weather and demobilization. | Keeps work controlled. |
| repairvolops.materials.material_list | material list | RECORD | List captures tarps, fasteners, plywood, tools, bags, cleaning supplies and specialty needs. | Supports logistics. |
| repairvolops.materials.procurement | procurement request | METHOD | Request routes unavailable materials to donations, warehouse, purchase or partner source. | Fills gaps. |
| repairvolops.materials.issue_log | issue log | RECORD | Issue log records materials, tools, quantities, crew, job ID and return expectation. | Controls stock. |
| repairvolops.materials.shortage | shortage record | RECORD | Shortage records unavailable items, substitute, delay and escalation. | Explains pending work. |
| repairvolops.schedule.job_assignment | job assignment | RECORD | Assignment names crew, date, address, scope, materials, resident contact and safety notes. | Executes work. |
| repairvolops.schedule.confirmation_call | confirmation call | METHOD | Call confirms resident availability, access, pets, utilities, materials and weather concerns. | Prevents wasted trip. |
| repairvolops.schedule.route_plan | route plan | METHOD | Route groups jobs by geography, crew skill, supplies and priority. | Saves time. |
| repairvolops.schedule.no_access | no-access handling | RECORD | No-access records locked property, no contact, unsafe condition or resident cancellation. | Enables reschedule. |
| repairvolops.work.arrival_check | arrival check | METHOD | Crew verifies address, resident permission, hazards, scope and materials before work starts. | Prevents wrong job. |
| repairvolops.work.progress_note | progress note | RECORD | Note captures tasks completed, materials used, blockers and next steps. | Tracks work. |
| repairvolops.work.change_scope | change of scope | METHOD | Scope changes require resident acknowledgement and coordinator approval. | Controls expectations. |
| repairvolops.work.site_cleanup | site cleanup | METHOD | Crew removes debris, tools, trash and leftover materials from work area. | Leaves site safe. |
| repairvolops.completion.completion_form | completion form | RECORD | Form records work done, unfinished tasks, photos if allowed, resident signature and crew leader. | Closes job. |
| repairvolops.completion.resident_feedback | resident feedback | RECORD | Feedback captures satisfaction, concerns, unmet needs and follow-up requests. | Improves service. |
| repairvolops.completion.followup_referral | follow-up referral | METHOD | Unfinished or professional work routes to case management, contractor or inspection pathway. | Continues recovery. |
| repairvolops.completion.tool_return | tool return | QUALITY_CHECK | Tools and reusable supplies reconcile after crew return. | Protects resources. |
| repairvolops.qa.photo_review | photo review | QUALITY_CHECK | Photo review verifies scope, completion, safety issue or material use when consent allows. | Supports QA. |
| repairvolops.qa.supervisor_check | supervisor check | QUALITY_CHECK | Supervisor samples jobs for quality, safety and resident concerns. | Catches problems. |
| repairvolops.qa.rework_ticket | rework ticket | RECORD | Rework ticket captures defect, cause, assigned crew and due date. | Fixes incomplete work. |
| repairvolops.qa.compliance_check | compliance check | QUALITY_CHECK | Check confirms volunteer work stayed within legal, safety and licensing limits. | Reduces liability. |
| repairvolops.communication.resident_update | resident update | METHOD | Update explains schedule, delays, materials, scope limits and next step. | Reduces uncertainty. |
| repairvolops.communication.partner_update | partner update | METHOD | Partners receive backlog, crew needs, material shortages and completed jobs. | Coordinates response. |
| repairvolops.communication.public_message | public message | METHOD | Public message explains request channels, eligible work, safety limits and wait times. | Manages demand. |
| repairvolops.communication.language | language support | METHOD | Interpreters or translated forms support consent, scope and feedback. | Improves access. |
| repairvolops.records.work_order | work order | RECORD | Work order stores intake, scope, safety, crew, materials, progress, completion and QA. | Creates audit trail. |
| repairvolops.metrics.jobs_completed | jobs completed | MEASUREMENT | Metric tracks completed jobs by category, area, crew and priority. | Shows output. |
| repairvolops.metrics.backlog_age | backlog age | MEASUREMENT | Backlog age measures open work orders by priority and days waiting. | Reveals bottleneck. |
| repairvolops.review.after_action | after-action review | METHOD | Review captures intake accuracy, scope control, crew safety, material gaps and QA lessons. | Improves future repairs. |
