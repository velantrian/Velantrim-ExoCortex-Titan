# BATCH_287 — School Crossing Guard Operations Detail
# world_skills_core · source: world_skills_core:batch_287:school_crossing_guard_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| crossingguardops.posts.crossing_post | School crossing guard post | invariant | Post defines assigned crossing, approaches, school, times, visibility needs and safety context. | manage post |
| crossingguardops.posts.post_risk_rating | Crossing post risk rating | variant | Rating combines traffic speed, volume, turning movements, sight distance, age group and crash history. | prioritize staffing |
| crossingguardops.posts.sightline_check | Crossing post sightline check | invariant | Check confirms guard, children and drivers can see each other before crossing movements. | improve visibility |
| crossingguardops.posts.weather_exposure | Crossing post weather exposure | variant | Exposure records rain, snow, heat, darkness, glare or wind affecting guard and children. | prepare equipment |
| crossingguardops.schedule.guard_schedule | Crossing guard schedule | invariant | Schedule assigns guard, post, arrival, dismissal, early release and special school times. | staff coverage |
| crossingguardops.schedule.school_calendar_sync | School calendar sync | invariant | Sync aligns guard shifts with holidays, closures, late starts, exams and events. | avoid gaps |
| crossingguardops.schedule.split_shift | Crossing guard split shift | variant | Split shift covers morning and afternoon peaks with separate reporting and relief rules. | match demand |
| crossingguardops.schedule.substitution_plan | Guard substitution plan | invariant | Plan identifies backup guards, contact order, travel time and approval for uncovered posts. | maintain coverage |
| crossingguardops.training.basic_guard_training | Basic crossing guard training | invariant | Training covers positioning, gap selection, hand signals, whistle, vest, stop paddle and communication. | standard practice |
| crossingguardops.training.traffic_gap_judgment | Traffic gap judgment | invariant | Judgment estimates safe crossing gaps considering speed, distance, driver behavior and child group size. | safer crossings |
| crossingguardops.training.child_behavior_awareness | Child behavior awareness | variant | Awareness covers impulsive movement, group distraction, visibility, bicycles and younger children. | anticipate risk |
| crossingguardops.training.incident_protocol | Crossing incident protocol training | invariant | Protocol covers crash, near miss, aggressive driver, medical event, threat or missing child. | respond correctly |
| crossingguardops.equipment.high_visibility_vest | Crossing guard high-visibility vest | invariant | Vest makes guard conspicuous and must be clean, reflective, fitted and seasonally appropriate. | be seen |
| crossingguardops.equipment.stop_paddle | Crossing guard stop paddle | invariant | Paddle signals drivers to stop and must be visible, reflective, readable and undamaged. | control traffic |
| crossingguardops.equipment.whistle_use | Crossing guard whistle use | variant | Whistle supplements hand signals where noise, attention or distance requires alerting users. | signal clearly |
| crossingguardops.equipment.radio_phone | Guard radio or phone | variant | Device enables contact with supervisor, school, police or dispatch during incidents. | coordinate help |
| crossingguardops.field.arrival_check | Crossing guard arrival check | invariant | Check confirms guard arrives early, observes traffic, wears gear and prepares crossing. | ready post |
| crossingguardops.field.positioning | Crossing guard positioning | invariant | Positioning places guard where drivers see signals and children wait safely before crossing. | control movement |
| crossingguardops.field.crossing_sequence | School crossing sequence | invariant | Sequence stops traffic, enters roadway if policy allows, signals children, clears crossing and releases traffic. | safe process |
| crossingguardops.field.group_crossing | Student group crossing | variant | Group crossing manages multiple children, late arrivals, bikes, strollers and mixed pedestrian flow. | orderly movement |
| crossingguardops.field.turning_vehicle_watch | Turning vehicle watch | invariant | Guard monitors turning drivers who may not yield during school crossing movements. | prevent conflict |
| crossingguardops.incidents.near_miss_report | Crossing near-miss report | invariant | Report captures driver action, location, time, child exposure, witness and corrective action. | learn from risk |
| crossingguardops.incidents.driver_noncompliance | Driver noncompliance incident | invariant | Incident includes failure to stop, speeding, distraction, illegal turn or passing stopped vehicles. | enforce safety |
| crossingguardops.incidents.student_injury | Student injury at crossing | invariant | Injury record triggers emergency response, school notification, supervisor review and documentation. | protect students |
| crossingguardops.incidents.guard_injury | Crossing guard injury | variant | Injury record covers traffic, fall, weather, assault, strain or equipment-related harm. | worker safety |
| crossingguardops.incidents.aggressive_person | Aggressive person incident | variant | Incident involves threatening driver, pedestrian, parent or public behavior toward guard or students. | escalate safely |
| crossingguardops.coordination.school_contact | School crossing school contact | invariant | Contact links guard program to principal, attendance office, dismissal staff and emergency contacts. | coordinate site |
| crossingguardops.coordination.police_referral | Crossing police referral | variant | Referral sends repeat violations, dangerous driving or enforcement needs to police unit. | support enforcement |
| crossingguardops.coordination.traffic_engineering_referral | Crossing traffic engineering referral | variant | Referral requests signs, markings, signal timing, sightline changes or crossing redesign review. | fix conditions |
| crossingguardops.coordination.parent_communication | Parent crossing communication | variant | Communication explains safe routes, guard hours, behavior expectations and temporary changes. | align families |
| crossingguardops.supervision.field_observation | Crossing guard field observation | invariant | Supervisor observes guard performance, post conditions, equipment and adherence to procedure. | quality control |
| crossingguardops.supervision.performance_feedback | Crossing guard performance feedback | variant | Feedback addresses timing, signals, positioning, communication, attendance and safety behavior. | improve practice |
| crossingguardops.supervision.post_coverage_audit | Guard post coverage audit | invariant | Audit compares scheduled versus actually covered posts and documents gaps. | manage reliability |
| crossingguardops.records.daily_log | Crossing guard daily log | invariant | Log records attendance, weather, incidents, unusual traffic, equipment issues and school changes. | trace shift |
| crossingguardops.records.equipment_issue_record | Crossing guard equipment issue record | variant | Record captures missing, damaged, dirty, expired or unsuitable vest, paddle, whistle or radio. | replace gear |
| crossingguardops.records.training_record | Crossing guard training record | invariant | Record stores completed training, refresher dates, certifications, policies and acknowledgments. | prove readiness |
| crossingguardops.safety.darkness_visibility | School crossing darkness visibility | invariant | Visibility controls include reflective gear, lighting, signs and adjusted awareness during low light. | reduce risk |
| crossingguardops.safety.winter_crossing | Winter school crossing condition | variant | Condition includes snowbanks, ice, narrowed crossings, plow windrows and reduced sightlines. | adapt post |
| crossingguardops.safety.heat_stress | Crossing guard heat stress | variant | Heat stress risk requires water, shade, breaks, clothing and supervisor monitoring. | protect guards |
| crossingguardops.reporting.incident_summary | Crossing guard incident summary | invariant | Summary aggregates near misses, violations, injuries, post issues and referrals. | manage program |
| crossingguardops.metrics.post_coverage_rate | Crossing guard post coverage rate KPI | invariant | KPI measures scheduled guard posts covered during required school crossing periods. | track reliability |
| crossingguardops.metrics.incident_rate | School crossing incident rate KPI | variant | KPI tracks incidents by post, school, time period, driver behavior and season. | target interventions |
| crossingguardops.continuity.emergency_uncovered_post | Emergency uncovered crossing post | invariant | Procedure addresses absent guard through substitute, police support, school notice or temporary closure. | avoid unsafe gap |
| crossingguardops.close.shift_closeout | Crossing guard shift closeout | invariant | Closeout confirms children cleared, incidents reported, gear stored and supervisor notified. | finish shift |
