# BATCH 340: Utility Planned Maintenance Notice Operations

**KnowledgeUnits:** 44  
**Namespace:** `maintnoticeops.*`  
**Scope:** work windows, affected customers, templates, channels, reschedules, proof and feedback.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| maintnoticeops.scope.work_id | planned work ID | RECORD | Notice record links work order, project, assets, location and responsible crew. | Connects customer notice to actual maintenance. |
| maintnoticeops.scope.work_type | work type | RECORD | Work type includes flushing, valve work, meter work, main repair, paving coordination or outage. | Determines notice content. |
| maintnoticeops.scope.impact_type | impact type | RECORD | Impact identifies service interruption, pressure change, noise, access, traffic or water quality. | Customers need practical impact, not internal task names. |
| maintnoticeops.scope.affected_area | affected area | MODEL | Area is defined by valves, circuits, parcels, meters, pressure zones or project limits. | Targets notices without over-alerting. |
| maintnoticeops.window.start_end | work window | RECORD | Window includes start date, end date, time range and expected duration. | Sets expectation for disruption. |
| maintnoticeops.window.contingency | contingency window | RECORD | Weather or emergency backup dates are listed when relevant. | Reduces confusion after postponement. |
| maintnoticeops.window.quiet_hours | quiet hours | CONSTRAINT | Work timing respects local noise, traffic, school or business restrictions. | Avoids avoidable complaints. |
| maintnoticeops.window.customer_prep | customer preparation | METHOD | Notice states actions such as store water, move cars, unlock gates or avoid laundry. | Converts notice into useful preparation. |
| maintnoticeops.customers.customer_list | customer list | RECORD | List is generated from accounts, GIS, route or parcel data. | Makes notification auditable. |
| maintnoticeops.customers.sensitive_accounts | sensitive accounts | RECORD | Critical or medical customers are flagged for extra outreach. | Prevents routine notice from missing high-risk users. |
| maintnoticeops.customers.landlord_tenant | landlord tenant handling | METHOD | Notice may go to both billing owner and service occupant where policy allows. | Reaches actual affected people. |
| maintnoticeops.templates.template_id | template ID | RECORD | Templates are stored by work type, language, channel and regulatory requirement. | Speeds consistent messaging. |
| maintnoticeops.templates.required_fields | required fields | QUALITY_CHECK | Template requires area, time, impact, preparation, contact and update source. | Prevents vague notices. |
| maintnoticeops.templates.plain_language | plain language | METHOD | Technical work is translated into customer-understandable effects. | Reduces unnecessary calls. |
| maintnoticeops.templates.language | language variants | METHOD | Notices include translated versions where community needs require. | Improves equitable access. |
| maintnoticeops.channels.mail | mailed notice | METHOD | Mail is used for longer lead times or formal requirements. | Provides durable notice. |
| maintnoticeops.channels.door_hanger | door hanger | METHOD | Door hangers target small affected areas shortly before work. | Reaches occupants when mail is too slow. |
| maintnoticeops.channels.sms_email | SMS/email notice | METHOD | Digital notices support fast updates and reminders. | Useful when work changes quickly. |
| maintnoticeops.channels.website | website post | METHOD | Website or map posts show planned work area and status. | Gives public self-service reference. |
| maintnoticeops.proof.delivery_log | delivery log | RECORD | Proof records channel, recipients, timestamp, staff and content version. | Demonstrates notice was sent. |
| maintnoticeops.proof.door_photo | door-hanger proof | RECORD | Field crews may photo sample placements or route completion. | Supports disputes about notice. |
| maintnoticeops.proof.bounce_handling | bounce handling | METHOD | Failed emails, returned mail or wrong numbers are logged and corrected. | Improves contact database. |
| maintnoticeops.reschedule.postponement | postponement notice | METHOD | Reschedule notice states reason, new window and whether prior prep still applies. | Prevents customers preparing twice unnecessarily. |
| maintnoticeops.reschedule.emergency_override | emergency override | DECISION_RULE | Emergency work may proceed with shortened notice and post-event explanation. | Balances safety and courtesy. |
| maintnoticeops.reschedule.cancel_notice | cancellation notice | RECORD | Cancellation closes planned notice and explains no work occurred. | Stops customers from waiting for disruption. |
| maintnoticeops.field.crew_brief | crew brief | METHOD | Crew receives notice text, customer promises and sensitive accounts. | Field actions match communications. |
| maintnoticeops.field.signage | field signage | METHOD | Signs or cones reinforce planned work notice at site. | Helps passersby and customers. |
| maintnoticeops.field.customer_questions | field question handling | METHOD | Crews know basic answers and referral contact. | Prevents contradictory field explanations. |
| maintnoticeops.feedback.complaint_link | complaint link | RECORD | Complaints after planned work are linked to notice case. | Shows whether notice was adequate. |
| maintnoticeops.feedback.survey | feedback survey | METHOD | Optional feedback asks whether notice was timely and clear. | Improves templates. |
| maintnoticeops.feedback.missed_customer | missed customer analysis | QUALITY_CHECK | Staff investigate customers affected but not notified. | Repairs targeting logic. |
| maintnoticeops.compliance.lead_time | lead time rule | CONSTRAINT | Some work requires minimum notice days by ordinance, permit or policy. | Avoids compliance violations. |
| maintnoticeops.compliance.content_rule | content rule | CONSTRAINT | Required content may include advisory language, rights, contact or restoration. | Keeps notices valid. |
| maintnoticeops.compliance.record_retention | retention | RECORD | Notice lists, content and proof are retained for audit period. | Supports claims and regulators. |
| maintnoticeops.qa.map_check | map check | QUALITY_CHECK | Affected list is compared against field isolation or project map. | Reduces over/under notification. |
| maintnoticeops.qa.date_check | date check | QUALITY_CHECK | Dates and AM/PM are verified before sending. | Prevents high-friction mistakes. |
| maintnoticeops.qa.approval | approval workflow | CONSTRAINT | Notices over threshold or regulatory impact require approval. | Provides accountability. |
| maintnoticeops.reporting.notice_volume | notice volume | MEASUREMENT | Reports count notices by type, area, channel and lead time. | Shows communication workload. |
| maintnoticeops.reporting.effectiveness | notice effectiveness | MODEL | Effectiveness uses complaint rate, missed-customer rate and bounce rate. | Measures notice quality. |
| maintnoticeops.reporting.repeat_area | repeat area report | RECORD | Areas with frequent notices are tracked for customer fatigue. | Helps coordinate work. |
| maintnoticeops.review.template_review | template review | METHOD | Templates are reviewed after complaints, policy changes or major projects. | Keeps messaging current. |
| maintnoticeops.review.project_closeout | project closeout | METHOD | Notice outcomes are reviewed with project closeout. | Communication becomes part of maintenance quality. |
| maintnoticeops.integration.crm_sync | CRM sync | METHOD | Notices sync to CRM account timeline. | Agents can see what customer received. |
| maintnoticeops.integration.work_order_link | work-order link | RECORD | Work order stores notice sent status and proof reference. | Crews know communication status. |

