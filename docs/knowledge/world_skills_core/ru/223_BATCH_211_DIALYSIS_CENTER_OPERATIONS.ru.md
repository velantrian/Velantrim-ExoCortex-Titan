# BATCH_211 — Dialysis Center Operations Detail
# world_skills_core · source: world_skills_core:batch_211:dialysis_center_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| dialysis.schedule.chair_schedule | Dialysis chair schedule | invariant | Schedule assigns patient, chair, shift, staff, treatment window and transport notes. | manage scarce chairs |
| dialysis.schedule.shift_wave | Dialysis shift wave | invariant | Wave groups patient arrivals and turnovers to keep treatment area flowing. | avoid crowding |
| dialysis.schedule.missed_treatment | Missed dialysis appointment | invariant | Record flags missed session, patient contact, clinical escalation and rescheduling need. | high-risk absence |
| dialysis.schedule.transport_coordination | Dialysis transport coordination | variant | Coordination tracks pickup, arrival, late vehicle, return ride and mobility needs. | patients depend on rides |
| dialysis.schedule.transient_patient | Transient dialysis patient | variant | Workflow handles visiting patient records, orders, insurance and chair assignment. | temporary service |
| dialysis.intake.identity_check | Dialysis identity check | invariant | Check verifies patient identifiers before chairing, documentation and samples. | right patient |
| dialysis.intake.pre_treatment_weight | Pre-treatment weight capture | invariant | Capture records weight before treatment according to center workflow. | operational baseline |
| dialysis.intake.vital_record | Dialysis vital record | invariant | Record captures required observations at defined points for clinician review. | monitoring evidence |
| dialysis.intake.access_checkin | Vascular access check-in | invariant | Check-in documents access type, condition observations and escalation flags without prescribing care. | protect access workflow |
| dialysis.intake.consent_status | Dialysis consent status | invariant | Status confirms required treatment, privacy and procedure consents are current. | permission evidence |
| dialysis.water.water_system_check | Dialysis water system check | invariant | Check verifies water treatment readiness, alarms, logs and release status before patient use. | water is critical |
| dialysis.water.chlorine_chloramine_test | Chlorine and chloramine test | invariant | Test confirms treated water meets center acceptance before use. | safety gate |
| dialysis.water.conductivity_monitor | Water conductivity monitor | variant | Monitor flags abnormal ionic content or system issue requiring response. | process control |
| dialysis.water.ro_alarm_response | Reverse osmosis alarm response | invariant | Response stops unsafe use, notifies responsible staff and documents recovery. | protect patients |
| dialysis.water.water_log | Dialysis water log | invariant | Log records tests, times, results, staff, alarms, corrective actions and release. | audit trail |
| dialysis.machine.machine_setup | Dialysis machine setup | invariant | Setup verifies machine status, prescription entry source, disposables, alarms and disinfection state. | ready station |
| dialysis.machine.machine_disinfection | Dialysis machine disinfection | invariant | Disinfection follows validated cycle, contact time, test and documentation. | infection control |
| dialysis.machine.machine_alarm | Dialysis machine alarm | invariant | Alarm requires staff response, patient check and event documentation by protocol. | do not ignore |
| dialysis.machine.station_turnover | Dialysis station turnover | invariant | Turnover cleans chair, surfaces, machine exterior, supplies and waste between patients. | safe next patient |
| dialysis.machine.preventive_maintenance | Dialysis equipment PM | invariant | PM tracks service intervals, calibration, parts, alarms, sensors and release to use. | reliable equipment |
| dialysis.supplies.dialyzer_inventory | Dialyzer inventory | variant | Inventory controls compatible dialyzers, lots, expirations, allocation and shortages. | supply fit |
| dialysis.supplies.concentrate_inventory | Dialysis concentrate inventory | invariant | Inventory tracks acid, bicarbonate, containers, lots, expiration and storage. | core consumable |
| dialysis.supplies.single_use_supply | Dialysis single-use supplies | invariant | Supplies include lines, needles, syringes, dressings, PPE and test materials. | chair readiness |
| dialysis.supplies.expiry_round | Dialysis expiry round | invariant | Round removes expired sterile, chemical, testing or medication-related items from use areas. | prevent unsafe stock |
| dialysis.supplies.shortage_plan | Dialysis supply shortage plan | invariant | Plan prioritizes critical inventory, substitutes only by approval and informs operations. | continue safely |
| dialysis.flow.patient_chairing | Patient chairing workflow | invariant | Workflow moves patient from waiting to station with identity, readiness and access checks. | start controlled |
| dialysis.flow.treatment_start_record | Treatment start record | invariant | Record captures start time, machine, station, staff and required setup confirmations. | begin trace |
| dialysis.flow.intratreatment_round | Intratreatment round | invariant | Round records observations, machine status, patient comfort and escalation needs at required intervals. | active monitoring |
| dialysis.flow.treatment_end_record | Treatment end record | invariant | Record captures end time, post-treatment workflow, events and discharge readiness. | close session |
| dialysis.flow.handoff_note | Dialysis handoff note | invariant | Note communicates patient status, machine issue, access concern, incident or pending task. | continuity |
| dialysis.infection.hand_hygiene_station | Dialysis hand hygiene station | invariant | Station supports required hand hygiene at chair, supply and transition points. | behavior control |
| dialysis.infection.ppe_zone | Dialysis PPE zone | invariant | Zone defines gown, glove, eye protection or mask expectations by task and exposure. | staff safety |
| dialysis.infection.blood_spill_response | Dialysis blood spill response | invariant | Response isolates, cleans, disinfects, disposes and documents spill according to protocol. | high-risk cleanup |
| dialysis.infection.isolation_workflow | Dialysis isolation workflow | variant | Workflow separates patient, machine, supplies or room where infection policy requires it. | reduce transmission |
| dialysis.infection.environmental_audit | Dialysis environmental audit | invariant | Audit checks cleaning, hand hygiene, supplies, waste, water logs and station turnover. | verify controls |
| dialysis.records.treatment_record | Dialysis treatment record | invariant | Record compiles session data, staff actions, machine data, events and notes. | legal clinical record |
| dialysis.records.lab_sample_route | Dialysis lab sample route | variant | Route labels, stores, hands off and tracks samples collected in center. | specimen trace |
| dialysis.records.incident_report | Dialysis incident report | invariant | Report documents fall, access issue, machine problem, reaction, spill, missed treatment or transfer. | safety learning |
| dialysis.records.transfer_packet | Dialysis transfer packet | variant | Packet sends patient records, schedule, access notes and orders to another facility. | continuity |
| dialysis.records.privacy_control | Dialysis privacy control | invariant | Control protects charts, screens, conversations and visible treatment information in open clinic. | dignity and compliance |
| dialysis.admin.staff_assignment | Dialysis staff assignment | invariant | Assignment maps nurses, technicians, biomedical support and charge role to shifts and stations. | coverage clarity |
| dialysis.admin.competency_record | Dialysis competency record | invariant | Record tracks staff training, machine, water, infection control and emergency competencies. | qualified work |
| dialysis.metrics.dialysis_kpi | Dialysis center KPI | variant | KPI tracks missed treatments, chair utilization, turnover time, incidents, water issues and documentation lag. | manage center |
| dialysis.continuity.power_water_outage | Dialysis power or water outage | invariant | Outage plan covers patient safety, treatment interruption, alternate sites, transport and communication. | resilience |
