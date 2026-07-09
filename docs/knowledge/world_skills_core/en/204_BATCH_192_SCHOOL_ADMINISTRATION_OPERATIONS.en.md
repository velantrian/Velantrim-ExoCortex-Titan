# BATCH_192 — School Administration Operations Detail
# world_skills_core · source: world_skills_core:batch_192:school_administration_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| schooladmin.enroll.application | Student enrollment application | invariant | Application collects student identity, guardians, address, grade, prior school and required documents. | start student record |
| schooladmin.enroll.residency_check | Residency check | variant | Check verifies eligibility for school, district, transport or funding rules. | place correctly |
| schooladmin.enroll.document_verification | Enrollment document verification | invariant | Verification checks birth record, guardianship, immunization evidence where required and transfer records. | valid admission file |
| schooladmin.enroll.grade_placement | Grade placement | invariant | Placement assigns student to year or grade using age, records, assessment and policy. | right cohort |
| schooladmin.enroll.withdrawal | Student withdrawal | invariant | Withdrawal records exit date, destination, records transfer and device or book returns. | close enrollment |
| schooladmin.attendance.daily_register | Daily attendance register | invariant | Register records present, absent, late, excused, remote or partial-day status. | legal attendance record |
| schooladmin.attendance.late_arrival | Late arrival process | invariant | Process records arrival time, reason, pass and guardian notification where needed. | controlled entry |
| schooladmin.attendance.early_release | Early release process | invariant | Release verifies authorized adult, reason, time and destination. | student safety |
| schooladmin.attendance.absence_followup | Absence follow-up | invariant | Follow-up contacts guardian and documents reason when absence is unexplained. | safeguarding signal |
| schooladmin.attendance.truancy_flag | Truancy flag | variant | Flag identifies repeated unexcused absence for intervention workflow. | prevent disengagement |
| schooladmin.timetable.master_schedule | Master timetable | invariant | Timetable assigns periods, rooms, teachers, groups and constraints. | school rhythm |
| schooladmin.timetable.room_assignment | Room assignment | invariant | Assignment matches class needs, capacity, accessibility, equipment and safety limits. | space fit |
| schooladmin.timetable.coverage_plan | Teacher coverage plan | invariant | Plan assigns substitute, merged class, supervision or remote work when staff absent. | continuity |
| schooladmin.timetable.exam_schedule | Exam schedule | variant | Schedule sets rooms, invigilators, accommodations, timing and materials. | fair assessment logistics |
| schooladmin.timetable.clash_resolution | Timetable clash resolution | invariant | Resolution fixes conflicts between student, teacher, room, resource or transport constraints. | make schedule possible |
| schooladmin.records.student_record | Student cumulative record | invariant | Record stores enrollment, attendance, grades, services, discipline, contacts and transfers. | institutional memory |
| schooladmin.records.guardian_contact | Guardian contact record | invariant | Record lists authorized guardians, pickup rights, communication preferences and emergency contacts. | contact right person |
| schooladmin.records.permission_form | Permission form | variant | Form authorizes trip, photo, medication handling, activity or service participation. | documented consent |
| schooladmin.records.record_request | Student record request | invariant | Request controls transfer, access, identity verification and disclosure scope. | privacy and mobility |
| schooladmin.records.data_correction | Student data correction | variant | Correction updates inaccurate demographic, contact or academic data with evidence and audit trail. | accurate systems |
| schooladmin.safeguard.visitor_checkin | School visitor check-in | invariant | Check-in verifies identity, purpose, host, badge, access area and departure. | site security |
| schooladmin.safeguard.incident_log | Student incident log | invariant | Log records injury, behavior, safeguarding concern, witness, action and notification. | accountable response |
| schooladmin.safeguard.pickup_authorization | Pickup authorization | invariant | Authorization confirms who may collect student and under what restrictions. | prevent unsafe release |
| schooladmin.safeguard.emergency_contact | Emergency contact procedure | invariant | Procedure defines contact order, escalation and documentation during urgent student issue. | reach help |
| schooladmin.safeguard.confidential_flag | Confidential student flag | variant | Flag restricts access to sensitive custody, protection, health or safety information. | need-to-know |
| schooladmin.communication.family_notice | Family notice | invariant | Notice communicates schedule, policy, event, absence, emergency or required action. | clear home link |
| schooladmin.communication.translation_need | Translation need | variant | Need identifies communication that must be translated or interpreted. | equitable access |
| schooladmin.communication.newsletter | School newsletter | variant | Newsletter summarizes events, deadlines, achievements and reminders. | routine communication |
| schooladmin.communication.emergency_alert | School emergency alert | invariant | Alert sends urgent instructions through approved channels with timing and confirmation. | fast mass message |
| schooladmin.communication.meeting_record | Family meeting record | invariant | Record captures attendees, topic, action items, follow-up and confidential notes. | continuity of support |
| schooladmin.operations.front_office_queue | School front office queue | invariant | Queue handles visitors, calls, attendance, deliveries, forms, student requests and staff needs. | hub of school |
| schooladmin.operations.daily_bulletin | Daily bulletin | variant | Bulletin coordinates announcements, cover, events, visitors, trips and operational changes. | shared situational awareness |
| schooladmin.operations.key_inventory | School key inventory | invariant | Inventory controls issued keys, cards, rooms, holders, dates and returns. | access control |
| schooladmin.operations.supply_request | School supply request | variant | Request captures need, quantity, budget code, approval and delivery. | keep classes supplied |
| schooladmin.operations.transport_change | Student transport change | variant | Change records bus, pickup, walking, caregiver or special arrangement update. | avoid wrong route |
| schooladmin.finance.fee_record | School fee record | variant | Record tracks charges, waivers, payments, refunds and outstanding balances. | transparent billing |
| schooladmin.finance.meal_account | Meal account administration | variant | Administration tracks eligibility, balances, payments, restrictions and alerts. | lunch access |
| schooladmin.finance.trip_collection | Trip payment collection | variant | Collection links consent, payment, subsidy and participant list. | event readiness |
| schooladmin.finance.cash_handoff | School cash handoff | invariant | Handoff records payer, purpose, amount, receipt, secure storage and deposit transfer. | reduce loss |
| schooladmin.reporting.enrollment_report | Enrollment report | invariant | Report summarizes active students by grade, program, demographic, funding or attendance status. | planning data |
| schooladmin.reporting.attendance_report | Attendance report | invariant | Report identifies attendance rates, chronic absence, late patterns and intervention lists. | monitor engagement |
| schooladmin.reporting.compliance_calendar | School compliance calendar | invariant | Calendar tracks required reporting, audits, drills, records and policy deadlines. | no missed obligations |
| schooladmin.training.office_procedure | School office procedure training | invariant | Training covers privacy, safeguarding, attendance, visitors, communication and emergency scripts. | consistent front office |
| schooladmin.metrics.admin_kpi | School administration KPI | variant | KPI tracks enrollment turnaround, attendance follow-up, call response, records requests and incident closure. | manage office health |
