# BATCH_197 — Equipment Calibration Service Operations Detail
# world_skills_core · source: world_skills_core:batch_197:equipment_calibration_service_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| calibsvc.intake.equipment_intake | Calibration equipment intake | invariant | Intake records asset ID, owner, model, serial, condition, accessories and requested service. | identify item |
| calibsvc.intake.service_request | Calibration service request | invariant | Request defines measurement ranges, points, tolerances, standard, due date and certificate needs. | scope the job |
| calibsvc.intake.as_found_condition | As-found condition | invariant | Condition documents instrument state before adjustment or repair. | evidence before work |
| calibsvc.intake.damage_observation | Calibration intake damage | invariant | Observation records broken seals, missing parts, contamination, impact damage or unsafe condition. | protect lab and customer |
| calibsvc.intake.priority_queue | Calibration priority queue | variant | Queue orders work by due date, production need, contract, turnaround or risk. | schedule lab capacity |
| calibsvc.standards.reference_standard | Reference standard | invariant | Standard is calibrated equipment used to compare or adjust customer item. | traceable basis |
| calibsvc.standards.traceability_chain | Calibration traceability chain | invariant | Chain links measurement results to recognized references through documented calibrations. | trust measurement |
| calibsvc.standards.standard_due_date | Standard due date | invariant | Due date controls whether reference equipment is valid for use. | avoid expired standard |
| calibsvc.standards.environment_condition | Calibration environment condition | invariant | Condition records temperature, humidity, vibration or other variables affecting measurement. | context for accuracy |
| calibsvc.standards.intermediate_check | Intermediate check | variant | Check verifies standard performance between formal calibrations. | catch drift |
| calibsvc.procedure.calibration_method | Calibration method | invariant | Method defines setup, points, sequence, calculations, acceptance and reporting. | repeatable work |
| calibsvc.procedure.measurement_range | Measurement range | invariant | Range defines the span over which instrument is tested or adjusted. | know coverage |
| calibsvc.procedure.test_point | Calibration test point | invariant | Point is specific value where indication, error and uncertainty are assessed. | sample performance |
| calibsvc.procedure.tolerance_limit | Tolerance limit | invariant | Limit defines maximum permitted error for customer use or specification. | pass/fail boundary |
| calibsvc.procedure.adjustment_rule | Calibration adjustment rule | invariant | Rule defines when technician may adjust instrument and how as-left data is recorded. | controlled correction |
| calibsvc.measure.as_found_data | As-found calibration data | invariant | Data records instrument performance before adjustment. | impact prior use |
| calibsvc.measure.as_left_data | As-left calibration data | invariant | Data records final performance after adjustment, repair or confirmation. | release evidence |
| calibsvc.measure.error_calculation | Calibration error calculation | invariant | Calculation compares instrument indication with reference value. | quantify deviation |
| calibsvc.measure.repeatability_check | Repeatability check | variant | Check repeats measurements to see short-term consistency. | measurement stability |
| calibsvc.measure.resolution_effect | Resolution effect | invariant | Instrument resolution limits how finely value can be read or reported. | display matters |
| calibsvc.uncertainty.uncertainty_budget | Uncertainty budget | invariant | Budget combines sources such as reference, repeatability, resolution and environment. | know confidence |
| calibsvc.uncertainty.coverage_factor | Coverage factor | variant | Factor expands standard uncertainty for stated confidence convention. | report interval |
| calibsvc.uncertainty.cmc_limit | Calibration capability limit | variant | Capability describes what lab can measure with stated uncertainty. | lab scope boundary |
| calibsvc.uncertainty.guard_band | Guard band | variant | Guard band reduces false accept or false reject risk near tolerance boundary. | decision risk |
| calibsvc.uncertainty.decision_rule | Calibration decision rule | invariant | Rule states how uncertainty is considered when declaring pass, fail or indeterminate. | transparent judgment |
| calibsvc.certificate.calibration_certificate | Calibration certificate | invariant | Certificate reports item, method, standards, results, uncertainty, date and authorization. | official output |
| calibsvc.certificate.accreditation_scope | Accreditation scope | variant | Scope states which measurements and uncertainties are covered by accreditation. | certificate limits |
| calibsvc.certificate.result_table | Calibration result table | invariant | Table lists points, reference values, readings, error, uncertainty and tolerance. | readable evidence |
| calibsvc.certificate.statement_of_conformity | Statement of conformity | variant | Statement declares whether item meets specified tolerance under decision rule. | pass/fail summary |
| calibsvc.certificate.certificate_revision | Certificate revision | invariant | Revision corrects or supersedes certificate with reason and authorization. | controlled correction |
| calibsvc.oot.out_of_tolerance | Out-of-tolerance result | invariant | OOT result means instrument error exceeded acceptance rule. | potential product impact |
| calibsvc.oot.impact_notice | OOT impact notice | invariant | Notice informs customer so they can evaluate prior measurements or affected work. | backward risk |
| calibsvc.oot.recall_list | Calibration recall list | invariant | List identifies instruments due, overdue, failed or needing removal from use. | control instruments |
| calibsvc.oot.repair_route | Calibration repair route | variant | Route sends instrument for repair, adjustment, replacement or return unrepaired. | restore usefulness |
| calibsvc.oot.recalibration_interval | Recalibration interval | invariant | Interval sets time or use cycle before next calibration is due. | schedule confidence |
| calibsvc.lab.workstation_setup | Calibration workstation setup | invariant | Setup verifies standards, fixtures, software, environment, cleanliness and safety. | ready to measure |
| calibsvc.lab.software_validation | Calibration software validation | variant | Validation confirms calculations, data capture and report generation behave correctly. | avoid hidden errors |
| calibsvc.lab.data_integrity | Calibration data integrity | invariant | Integrity protects raw data, edits, approvals, audit trail and backups. | trust records |
| calibsvc.lab.technician_authorization | Technician authorization | invariant | Authorization confirms technician is trained and approved for method or equipment type. | competence control |
| calibsvc.lab.cross_check | Calibration cross-check | variant | Cross-check compares result with another standard, method or technician when risk is high. | independent confidence |
| calibsvc.customer.customer_requirement | Customer calibration requirement | invariant | Requirement may specify tolerance, points, format, accreditation or labeling. | meet use case |
| calibsvc.customer.due_label | Calibration due label | invariant | Label shows status, date, next due, asset ID and restrictions if any. | field visibility |
| calibsvc.metrics.turnaround_metric | Calibration turnaround metric | variant | Metric tracks intake-to-completion, backlog, rework, OOT rate and on-time delivery. | manage lab service |
| calibsvc.continuity.standard_failure | Reference standard failure process | invariant | Process quarantines affected standard, reviews work since last valid check and informs customers if needed. | protect traceability |
