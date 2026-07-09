# BATCH 347: Municipal 311 Service Request Operations

**KnowledgeUnits:** 44  
**Namespace:** `muni311ops.*`  
**Scope:** intake, categorization, routing, SLAs, field updates, resident communications and closure.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| muni311ops.intake.request_id | request ID | RECORD | Request ID links resident, channel, location, category, time and status. | Creates traceable service work. |
| muni311ops.intake.channel | intake channel | RECORD | Channel distinguishes phone, web, app, email, walk-in, council referral or social media. | Helps manage demand by source. |
| muni311ops.intake.location | location capture | METHOD | Location captures address, parcel, intersection, asset ID or map point. | Routes work to the right crew. |
| muni311ops.intake.description | issue description | RECORD | Description preserves resident wording and key observable facts. | Prevents loss of field detail. |
| muni311ops.intake.photo | photo evidence | RECORD | Photo attachments show condition, context and urgency. | Improves triage and reduces revisits. |
| muni311ops.category.taxonomy | service taxonomy | MODEL | Taxonomy maps request types to responsible departments and workflows. | Keeps routing consistent. |
| muni311ops.category.duplicate_check | duplicate check | QUALITY_CHECK | Duplicate check matches nearby location, category and open case. | Prevents repeated work orders. |
| muni311ops.category.emergency_filter | emergency filter | SAFETY_RULE | Life safety, active hazards or crimes route outside routine 311. | Protects urgent response. |
| muni311ops.category.private_property | private property boundary | CONSTRAINT | Some issues are private property, utility, county, state or contractor responsibility. | Avoids false city commitments. |
| muni311ops.routing.department | department routing | METHOD | Requests route to sanitation, streets, parks, code, traffic, utilities or police non-emergency. | Sends work to accountable owner. |
| muni311ops.routing.queue | queue assignment | METHOD | Queue assignment uses category, geography, priority and crew availability. | Improves workload control. |
| muni311ops.routing.escalation | escalation path | METHOD | Escalation sends stuck or high-risk cases to supervisors or interdepartmental review. | Prevents unattended issues. |
| muni311ops.routing.external | external referral | METHOD | External referral forwards issue to utility, transit, county, state or private owner. | Closes responsibility gaps. |
| muni311ops.sla.priority | priority level | MODEL | Priority level reflects hazard, legal deadline, service impact and visibility. | Drives response time. |
| muni311ops.sla.target_date | target date | RECORD | Target date is calculated from SLA calendar, priority and department rules. | Sets measurable expectation. |
| muni311ops.sla.pause_reason | pause reason | RECORD | Case may pause for weather, access, parts, owner contact or external dependency. | Explains SLA exceptions. |
| muni311ops.sla.breach | SLA breach | FAILURE_MODE | Breach occurs when target passes without accepted status reason. | Signals management attention. |
| muni311ops.field.work_order | work order link | RECORD | Service request links to field work order, inspection or enforcement case. | Connects resident report to action. |
| muni311ops.field.dispatch_note | dispatch note | RECORD | Dispatch note includes access, hazards, asset details and resident contact limits. | Helps crews act safely. |
| muni311ops.field.status_update | field status update | METHOD | Crews update status as assigned, inspected, completed, referred or no issue found. | Keeps back office informed. |
| muni311ops.field.no_issue_found | no issue found | METHOD | No-issue closure records inspection evidence and reason. | Prevents unexplained denial. |
| muni311ops.field.revisit | revisit trigger | METHOD | Revisit triggers when work fails, resident disputes, weather changes or hazard remains. | Improves closure quality. |
| muni311ops.communication.acknowledgment | acknowledgment | METHOD | Acknowledgment gives case number, category and expected response path. | Confirms receipt to resident. |
| muni311ops.communication.status_message | status message | METHOD | Status message translates internal workflow into public wording. | Reduces confusion. |
| muni311ops.communication.delay_notice | delay notice | METHOD | Delay notice explains cause, new target or external dependency. | Maintains trust when work slips. |
| muni311ops.communication.closure_notice | closure notice | METHOD | Closure notice states outcome, date, evidence and follow-up route. | Completes resident loop. |
| muni311ops.communication.language | language support | METHOD | Communications use preferred language when available. | Improves equitable service. |
| muni311ops.records.case_file | case file | RECORD | Case file stores intake, routing, notes, photos, field updates and communications. | Enables audit and public record response. |
| muni311ops.records.privacy | privacy filter | CONSTRAINT | Personal data is hidden from public maps and open data where required. | Protects residents. |
| muni311ops.records.retention | retention rule | CONSTRAINT | 311 records are retained by case type and legal schedule. | Supports transparency and cleanup. |
| muni311ops.analytics.hotspot | hotspot analysis | MEASUREMENT | Repeated cases by location reveal asset, enforcement or service design problems. | Turns complaints into planning data. |
| muni311ops.analytics.demand_trend | demand trend | MEASUREMENT | Volume by category, season and channel shows service demand. | Supports staffing and budget decisions. |
| muni311ops.analytics.first_close | first-close quality | MEASUREMENT | First-close quality measures cases completed without reopen or duplicate. | Shows resolution accuracy. |
| muni311ops.analytics.equity | equity review | QUALITY_CHECK | Response time and closure rates are reviewed by neighborhood and request type. | Detects service inequity. |
| muni311ops.qa.category_audit | category audit | QUALITY_CHECK | Sampled cases check whether category and routing were correct. | Improves intake accuracy. |
| muni311ops.qa.closure_audit | closure audit | QUALITY_CHECK | Closure audit checks evidence, wording and actual completion. | Prevents cosmetic closure. |
| muni311ops.qa.script_update | script update | METHOD | Intake scripts update after recurring misroutes or resident confusion. | Makes front office smarter. |
| muni311ops.integration.asset_system | asset system integration | METHOD | 311 links to asset inventory for signs, trees, hydrants, lights or roads. | Grounds requests in real assets. |
| muni311ops.integration.gis_layer | GIS layer | METHOD | GIS layers show jurisdiction, wards, districts and service boundaries. | Reduces routing mistakes. |
| muni311ops.integration.open_data | open data feed | METHOD | Nonprivate 311 data may publish category, status, geography and date. | Supports public transparency. |
| muni311ops.governance.owner | service owner | RECORD | Each category has owner, SLA rule, closure rule and escalation contact. | Avoids orphan queues. |
| muni311ops.governance.change_control | taxonomy change control | METHOD | Category and SLA changes are reviewed before deployment. | Prevents breaking reports and routing. |
| muni311ops.closeout.reopen | reopen process | METHOD | Reopen process accepts disputes, failed work or changed conditions. | Keeps closure honest. |
| muni311ops.closeout.lessons | service lesson | METHOD | Patterns from 311 feed maintenance planning, code strategy or communication improvements. | Converts resident reports into better services. |
