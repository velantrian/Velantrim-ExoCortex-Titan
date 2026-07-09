# BATCH 368: Epidemiology Data Quality Operations

**KnowledgeUnits:** 44  
**Namespace:** `epidataops.*`  
**Scope:** deduplication, missing fields, case definitions, data linkage, dashboards and audit.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| epidataops.intake.feed_registry | feed registry | RECORD | Registry lists labs, hospitals, clinics, schools and manual entry sources. | Shows data origins. |
| epidataops.intake.file_receipt | file receipt | RECORD | Receipt records file, timestamp, sender, schema and row count. | Creates ingest audit. |
| epidataops.intake.schema_check | schema check | QUALITY_CHECK | Incoming fields are checked against expected names, types and code sets. | Prevents broken imports. |
| epidataops.intake.error_queue | error queue | METHOD | Invalid records route to repair queue with reason. | Keeps failures visible. |
| epidataops.identity.person_key | person key | MODEL | Person key combines name, date, contact, address and identifiers. | Supports matching. |
| epidataops.identity.case_key | case key | MODEL | Case key combines person, disease, event and date logic. | Prevents duplicate cases. |
| epidataops.identity.merge_rule | merge rule | METHOD | Merge rule decides when records combine, remain separate or need review. | Controls deduplication. |
| epidataops.identity.unmerge | unmerge process | METHOD | Incorrect merges can be reversed with audit history. | Repairs false matches. |
| epidataops.missing.required_fields | required fields | CONSTRAINT | Required fields vary by condition, report type and surveillance purpose. | Defines completeness. |
| epidataops.missing.completeness | completeness metric | MEASUREMENT | Completeness tracks missing onset, lab, demographics, location and outcome. | Shows data quality. |
| epidataops.missing.followup_task | follow-up task | METHOD | Missing critical fields trigger investigator, provider or lab query. | Improves records. |
| epidataops.missing.unknown_code | unknown code | RECORD | Unknown is distinct from blank or not asked. | Prevents false precision. |
| epidataops.definition.case_definition | case definition | CONSTRAINT | Case definition maps lab, symptoms, exposure and epidemiologic criteria. | Standardizes classification. |
| epidataops.definition.version | definition version | RECORD | Version records which definition applied at classification time. | Supports trend interpretation. |
| epidataops.definition.probable | probable case | MODEL | Probable case meets partial clinical/epidemiologic criteria. | Preserves uncertainty. |
| epidataops.definition.reclassification | reclassification | METHOD | Cases can change status when new lab or exposure data arrives. | Keeps dataset current. |
| epidataops.codes.code_set | code set | RECORD | Code sets define disease, lab, location, race/ethnicity, setting and outcome values. | Enables analysis. |
| epidataops.codes.mapping | code mapping | METHOD | Mapping converts local codes to standard codes. | Integrates sources. |
| epidataops.codes.invalid_code | invalid code | FAILURE_MODE | Invalid code breaks dashboards or misclassifies cases. | Requires validation. |
| epidataops.codes.retired_code | retired code | CONSTRAINT | Retired codes are preserved historically but blocked for new records. | Maintains continuity. |
| epidataops.linkage.lab_link | lab linkage | METHOD | Lab results link to cases by person, specimen and accession. | Connects evidence. |
| epidataops.linkage.hospital_link | hospital linkage | METHOD | Hospital data links admissions, ICU, discharge and deaths. | Tracks severity. |
| epidataops.linkage.outbreak_link | outbreak linkage | METHOD | Cases link to outbreak, facility, event or exposure cluster. | Supports response. |
| epidataops.linkage.privacy | linkage privacy | SAFETY_RULE | Linkage uses minimum necessary access and logs. | Protects sensitive data. |
| epidataops.temporal.event_date | event date hierarchy | MODEL | Date hierarchy prioritizes onset, specimen, diagnosis, report and entry dates by use. | Prevents trend distortion. |
| epidataops.temporal.lag | reporting lag | MEASUREMENT | Lag measures event-to-report and report-to-entry delay. | Explains delayed trends. |
| epidataops.temporal.backfill | backfill handling | METHOD | Backfilled records update historical counts with versioned refresh. | Keeps dashboards honest. |
| epidataops.temporal.timezone | timezone standard | CONSTRAINT | Timestamps use consistent timezone or UTC conversion. | Avoids daily count errors. |
| epidataops.dashboard.metric_definition | metric definition | RECORD | Each dashboard metric has numerator, denominator, filters and refresh cadence. | Prevents ambiguous charts. |
| epidataops.dashboard.suppression | small cell suppression | SAFETY_RULE | Small counts are suppressed or aggregated when privacy risk exists. | Protects identity. |
| epidataops.dashboard.refresh_log | refresh log | RECORD | Refresh log records data time, run status and anomalies. | Supports trust. |
| epidataops.dashboard.annotation | annotation | METHOD | Public charts note definition changes, outages, backlogs and reporting shifts. | Reduces misinterpretation. |
| epidataops.audit.change_log | change log | RECORD | Changes to records capture old value, new value, user, time and reason. | Makes edits accountable. |
| epidataops.audit.access_log | access log | RECORD | Access logs show who viewed or exported sensitive data. | Detects misuse. |
| epidataops.audit.sample_review | sample review | QUALITY_CHECK | Sampled cases are reviewed for classification, completeness and linkage. | Improves reliability. |
| epidataops.audit.export_review | export review | QUALITY_CHECK | Exports are checked for privacy, fields, filters and recipient authorization. | Prevents disclosure mistakes. |
| epidataops.governance.data_owner | data owner | RECORD | Data owner defines standards, approvals and quality thresholds. | Keeps accountability. |
| epidataops.governance.dictionary | data dictionary | RECORD | Dictionary explains fields, values, sources and caveats. | Supports reuse. |
| epidataops.governance.issue_log | issue log | RECORD | Issue log tracks defects, owner, priority, fix and validation. | Turns quality into work. |
| epidataops.governance.release_rule | release rule | CONSTRAINT | Public release requires privacy, accuracy and communications review. | Protects public trust. |
| epidataops.metrics.duplicate_rate | duplicate rate | MEASUREMENT | Duplicate rate tracks likely duplicates per feed and condition. | Targets cleanup. |
| epidataops.metrics.timeliness | timeliness metric | MEASUREMENT | Timeliness measures report-to-action-ready record time. | Shows operational speed. |
| epidataops.closeout.archive | archive snapshot | RECORD | Dataset snapshots preserve definitions, extracts and dashboards. | Enables later analysis. |
| epidataops.review.lessons | data lessons | METHOD | Review identifies source problems, training needs and automation improvements. | Strengthens surveillance. |
