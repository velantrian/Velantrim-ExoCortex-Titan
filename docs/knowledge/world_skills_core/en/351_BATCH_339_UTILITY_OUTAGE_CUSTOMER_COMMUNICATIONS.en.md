# BATCH 339: Utility Outage Customer Communications

**KnowledgeUnits:** 44  
**Namespace:** `outagecommsops.*`  
**Scope:** outage intake, maps, estimated restoration, alerts, sensitive customers, updates and closeout.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| outagecommsops.intake.outage_case | outage case | RECORD | Outage case links calls, SCADA alarms, field tickets, affected area and start time. | Keeps customer reports and operations in one incident record. |
| outagecommsops.intake.first_report | first report | RECORD | First report captures address, symptom, time, customer type and safety concern. | Helps detect outage before full system confirmation. |
| outagecommsops.intake.duplicate_calls | duplicate calls | METHOD | Similar calls are grouped by area, symptom and time window. | Prevents inflated workload and reveals clusters. |
| outagecommsops.intake.safety_screen | safety screen | DECISION_RULE | Downed wires, sewage backup, no water, gas odor or medical dependency trigger priority routing. | Separates routine outage from life-safety response. |
| outagecommsops.map.outage_polygon | outage polygon | RECORD | Map polygon estimates affected customers from assets, valves, circuits or pressure zone. | Shows who should receive alerts. |
| outagecommsops.map.confidence | map confidence | MODEL | Confidence reflects field confirmation, telemetry quality and asset model accuracy. | Prevents overpromising map precision. |
| outagecommsops.map.customer_count | affected customer count | MEASUREMENT | Count is derived from accounts, meters, circuits or parcels inside affected area. | Supports staffing and public messaging. |
| outagecommsops.map.boundary_update | boundary update | METHOD | Boundary changes as crews isolate, restore or discover new failure points. | Keeps notifications aligned with reality. |
| outagecommsops.etr.initial_etr | initial ETR | RECORD | Initial estimated restoration time is based on known cause, crew dispatch and standard repair class. | Gives customers a first expectation. |
| outagecommsops.etr.uncertainty | ETR uncertainty | MODEL | Unknown cause, unsafe access, parts or weather increase uncertainty. | Explains why some ETRs are broad. |
| outagecommsops.etr.revision | ETR revision | METHOD | ETR is updated when field diagnosis, parts, switching or repair progress changes. | Prevents stale promises. |
| outagecommsops.etr.no_etr | no ETR condition | DECISION_RULE | If cause is unknown or site unsafe, message says assessment underway instead of guessing. | Protects trust. |
| outagecommsops.alert.channels | alert channels | METHOD | Alerts use SMS, email, phone, portal, app, website, social and media where appropriate. | Reaches customers through redundant paths. |
| outagecommsops.alert.opt_in | opt-in records | RECORD | Customer notification preferences and language are stored. | Improves delivery and consent compliance. |
| outagecommsops.alert.template | alert template | RECORD | Template includes outage type, area, safety note, ETR and update link. | Keeps messages fast and consistent. |
| outagecommsops.alert.failed_delivery | failed delivery | RECORD | Bounced calls, bad emails or failed SMS are tracked. | Improves contact data quality. |
| outagecommsops.sensitive.medical_flag | medical flag | RECORD | Sensitive customers with medical needs or critical services are flagged under policy. | Supports targeted outreach. |
| outagecommsops.sensitive.facility_list | critical facility list | RECORD | Hospitals, schools, shelters, treatment plants and major employers are listed. | Coordinates high-impact communication. |
| outagecommsops.sensitive.manual_call | manual call | METHOD | High-risk accounts may receive manual confirmation or welfare referral. | Adds care beyond mass alert. |
| outagecommsops.sensitive.privacy | sensitive privacy | SAFETY_RULE | Sensitive status is shared only with authorized staff and responders. | Protects private customer data. |
| outagecommsops.updates.cadence | update cadence | DECISION_RULE | Update frequency depends on incident severity, ETR length and customer impact. | Keeps customers informed without noise. |
| outagecommsops.updates.field_sync | field sync | METHOD | Communications staff sync with incident command or crew lead before updates. | Prevents conflicting messages. |
| outagecommsops.updates.cause_message | cause message | METHOD | Cause is described only when confirmed and useful. | Avoids speculation. |
| outagecommsops.updates.restoration_phase | restoration phase | RECORD | Updates distinguish assessing, isolating, repairing, testing, restoring and closed. | Customers understand progress. |
| outagecommsops.water.boil_notice_link | boil notice link | DECISION_RULE | Water outages with pressure loss may trigger advisory workflow. | Keeps public health messaging integrated. |
| outagecommsops.water.distribution_site | water distribution site | RECORD | If emergency water is provided, site, hours, limits and eligibility are announced. | Turns communication into practical relief. |
| outagecommsops.power.cooling_warming | cooling/warming referral | METHOD | Long outages may refer customers to shelters or community resources. | Supports vulnerable customers. |
| outagecommsops.social.media_post | social media post | METHOD | Public posts use approved facts, area, ETR and safety guidance. | Broadens reach during large events. |
| outagecommsops.social.rumor_control | rumor control | METHOD | Staff correct common rumors with concise verified updates. | Reduces misinformation. |
| outagecommsops.callcenter.script | call center script | RECORD | Agents receive outage script, known area, ETR, safety notes and escalation triggers. | Keeps answers consistent. |
| outagecommsops.callcenter.surge | call surge mode | METHOD | Surge mode routes calls to IVR, callbacks, web updates or extra staff. | Prevents queue collapse. |
| outagecommsops.callcenter.special_case | special case escalation | DECISION_RULE | Medical, trapped, flood or repeated no-service cases escalate beyond script. | Protects outliers. |
| outagecommsops.closeout.restored_notice | restored notice | METHOD | Customers receive restoration notice with any required flushing, reset or safety steps. | Confirms closure and next action. |
| outagecommsops.closeout.confirmation_window | confirmation window | METHOD | Customers can report still-out within defined window after restored notice. | Catches nested or missed outages. |
| outagecommsops.closeout.final_cause | final cause | RECORD | Final cause, duration, affected count and communication timeline are recorded. | Supports after-action review. |
| outagecommsops.closeout.customer_credit | customer credit trigger | DECISION_RULE | Long or regulated outages may trigger credit or claims workflow. | Connects communications with customer relief. |
| outagecommsops.qa.message_review | message review | QUALITY_CHECK | Outage messages are reviewed for accuracy, clarity, language and safety. | Reduces harmful ambiguity. |
| outagecommsops.qa.timestamp_check | timestamp check | QUALITY_CHECK | Public updates show current timestamp and avoid stale ETRs. | Customers know freshness of information. |
| outagecommsops.qa.channel_consistency | channel consistency | QUALITY_CHECK | Website, IVR, social and agent scripts are compared for conflicting details. | Prevents credibility loss. |
| outagecommsops.records.timeline | communication timeline | RECORD | Timeline logs alert sends, updates, scripts, media posts and closeout. | Creates auditable communication record. |
| outagecommsops.reporting.metrics | communication metrics | MEASUREMENT | Metrics include delivery rate, call volume, ETR changes, complaints and closeout lag. | Shows performance under stress. |
| outagecommsops.reporting.after_action | after-action review | METHOD | Review covers speed, accuracy, ETR quality, sensitive outreach and customer feedback. | Improves next outage response. |
| outagecommsops.training.drill | outage communication drill | METHOD | Staff rehearse templates, escalation, map updates and field sync. | Builds readiness before real events. |
| outagecommsops.governance.approval | message approval | CONSTRAINT | High-impact messages require authorized approval path. | Balances speed and accountability. |

