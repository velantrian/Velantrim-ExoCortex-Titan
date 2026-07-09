# BATCH 318: Water Supply Backflow Prevention Operations

**KnowledgeUnits:** 44  
**Namespace:** `backflowops.*`  
**Scope:** hazard surveys, device inventory, testing, repairs, records, notices and enforcement.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| backflowops.program.cross_connection | cross-connection | MODEL | Cross-connection is a physical link between potable water and potential contamination source. | Identifies where backflow prevention is needed. |
| backflowops.program.backpressure | backpressure | MECHANISM | Backpressure occurs when downstream pressure exceeds water system pressure. | Can push contaminated liquid into potable supply. |
| backflowops.program.backsiphonage | backsiphonage | MECHANISM | Backsiphonage occurs when negative pressure pulls fluid backward. | Main breaks or firefighting can create this risk. |
| backflowops.program.authority | program authority | CONSTRAINT | Utility authority comes from plumbing code, water rules, service agreement or ordinance. | Defines inspection, notice and enforcement power. |
| backflowops.survey.hazard_survey | hazard survey | METHOD | Survey identifies processes, chemicals, irrigation, boilers, medical systems and auxiliary water. | Determines device requirement by risk. |
| backflowops.survey.premise_isolation | premise isolation | DECISION_RULE | High-risk sites may require protection at service connection. | Protects public system even if internal plumbing changes. |
| backflowops.survey.internal_protection | internal protection | METHOD | Internal devices protect specific fixtures or process connections. | Reduces hazard at source inside facility. |
| backflowops.survey.site_category | site category | RECORD | Site is classified as residential, irrigation, commercial, industrial, medical or fire system. | Category drives survey frequency and notices. |
| backflowops.survey.auxiliary_water | auxiliary water | INSPECTION | Wells, reclaimed water, rainwater or process water are checked for separation. | Auxiliary sources are common contamination pathways. |
| backflowops.device.rp | reduced pressure assembly | METHOD | RP assembly protects against high hazards with relief valve discharge. | Suitable where contamination risk is severe. |
| backflowops.device.dcva | double check valve assembly | METHOD | DCVA protects against lower hazard backpressure/backsiphonage. | Used where pollutant risk is lower than contaminant risk. |
| backflowops.device.pvb | pressure vacuum breaker | METHOD | PVB protects against backsiphonage where installed above downstream piping. | Common in irrigation if elevation rules are met. |
| backflowops.device.air_gap | air gap | SAFETY_RULE | Air gap is physical separation between outlet and flood level rim. | Most robust protection but space and design dependent. |
| backflowops.device.fire_system | fire system device | CONSTRAINT | Fire sprinkler systems may need backflow devices compatible with fire code and hydraulics. | Protects water quality without disabling fire protection. |
| backflowops.inventory.device_id | device ID | RECORD | Each device gets ID, location, type, manufacturer, serial, size and hazard served. | Enables testing, repair and compliance tracking. |
| backflowops.inventory.location_note | location note | RECORD | Records include room, wall, meter, pit, GPS or photo for device access. | Testers can find devices without owner guesswork. |
| backflowops.inventory.status | device status | RECORD | Status shows active, removed, replaced, exempt, failed, overdue or inaccessible. | Supports accurate compliance dashboards. |
| backflowops.inventory.install_date | install date | RECORD | Install and replacement dates support lifecycle and warranty. | Older devices may need rebuild or replacement. |
| backflowops.testing.annual_test | annual test | METHOD | Testers verify check valves, relief valve and shutoff functions per device type. | Confirms the device actually protects the system. |
| backflowops.testing.certified_tester | certified tester | CONSTRAINT | Testing is performed by certified testers using accepted procedures. | Maintains technical reliability and legal acceptance. |
| backflowops.testing.gauge_calibration | gauge calibration | QUALITY_CHECK | Test gauges require calibration records within allowed interval. | Bad gauges produce false pass/fail results. |
| backflowops.testing.test_report | test report | RECORD | Report includes device ID, readings, pass/fail, repairs, tester, gauge and date. | Creates audit trail for compliance. |
| backflowops.testing.failed_test | failed test | FAILURE_MODE | A failed device must be repaired, replaced or isolated within required timeframe. | Failed protection leaves active contamination risk. |
| backflowops.repairs.rebuild | rebuild kit | METHOD | Rebuild replaces checks, springs, seals or relief components per manufacturer. | Restores function without full replacement. |
| backflowops.repairs.retest | retest after repair | QUALITY_CHECK | Device is retested after repair before compliance status is restored. | Repair claim alone is not proof of protection. |
| backflowops.repairs.freeze_damage | freeze damage | FAILURE_MODE | Outdoor devices can crack or fail after freezing if not protected. | Seasonalization prevents recurring failures. |
| backflowops.repairs.access_clearance | access clearance | CONSTRAINT | Devices need clearance, drainage, lighting and safe access for testing. | Inaccessible devices become chronic overdue items. |
| backflowops.notices.initial_notice | initial notice | METHOD | Customer receives test due date, device list, accepted testers and submission method. | Gives clear path to compliance. |
| backflowops.notices.reminder | reminder notice | METHOD | Reminders are sent before due date and after missed deadline. | Reduces enforcement workload. |
| backflowops.notices.violation | violation notice | RECORD | Violation notice documents overdue test, failed repair, refusal or unauthorized removal. | Creates due process record. |
| backflowops.notices.language_access | language access | METHOD | Notices may need plain language, translated text or direct outreach for complex sites. | Improves compliance across customer groups. |
| backflowops.enforcement.water_shutoff | water shutoff | DECISION_RULE | Severe noncompliance may lead to service termination after required notice. | Protects public health when voluntary compliance fails. |
| backflowops.enforcement.penalty | penalty | DECISION_RULE | Fines or fees may apply for missed tests, repeat notices or utility-performed actions. | Encourages timely compliance. |
| backflowops.enforcement.emergency_order | emergency order | DECISION_RULE | Immediate isolation may be required when active contamination threat is found. | Rapid action prevents system contamination. |
| backflowops.records.customer_account | customer account link | RECORD | Device records link to service account, meter, parcel and owner. | Notices reach the responsible party. |
| backflowops.records.document_retention | document retention | RECORD | Surveys, tests, repairs, notices and enforcement records are retained by policy. | Supports audits and incident investigation. |
| backflowops.records.data_import | tester data import | METHOD | Electronic submissions are validated for IDs, dates, readings and tester credentials. | Reduces manual entry errors. |
| backflowops.qa.survey_cycle | survey cycle | DECISION_RULE | Higher hazard customers are surveyed more often than low-risk sites. | Program effort matches public health risk. |
| backflowops.qa.audit_tests | test audit | QUALITY_CHECK | Utility audits a sample of tests for procedure, gauge, readings and device match. | Detects unreliable tester behavior. |
| backflowops.qa.incident_review | incident review | METHOD | Backflow incidents are reviewed for cause, exposure, corrective action and notifications. | Turns contamination events into prevention improvements. |
| backflowops.reporting.compliance_rate | compliance rate | MEASUREMENT | Rate tracks current, overdue, failed, repaired and unknown devices. | Shows program health to managers. |
| backflowops.reporting.high_hazard_list | high hazard list | RECORD | High-hazard sites are tracked separately for priority follow-up. | Focuses enforcement where consequences are largest. |
| backflowops.reporting.board_summary | board summary | RECORD | Summary reports surveys, tests, failures, enforcement and incidents. | Gives governance oversight of water safety. |
| backflowops.integration.plumbing_permit | plumbing permit link | METHOD | New permits feed possible device installs or hazard changes into program records. | Keeps inventory current as buildings change. |
