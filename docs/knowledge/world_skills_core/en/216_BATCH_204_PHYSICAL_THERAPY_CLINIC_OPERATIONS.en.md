# BATCH_204 — Physical Therapy Clinic Operations Detail
# world_skills_core · source: world_skills_core:batch_204:physical_therapy_clinic_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| ptclinic.referral.referral_intake | Physical therapy referral intake | invariant | Intake records diagnosis, provider, body region, precautions, authorization and requested therapy. | start episode |
| ptclinic.referral.script_check | Therapy prescription check | variant | Check verifies frequency, duration, restrictions and payer requirements where prescription is required. | compliant scheduling |
| ptclinic.referral.authorization_visits | Authorized therapy visits | variant | Authorization defines approved visit count, dates, services and documentation rules. | know billing limit |
| ptclinic.referral.red_flag_route | Therapy red-flag routing | invariant | Routing sends concerning symptoms or unsafe presentations to clinical review before routine care. | safety boundary |
| ptclinic.referral.prior_records | Prior record collection | variant | Collection gathers imaging reports, operative notes, precautions and previous therapy notes. | context for evaluation |
| ptclinic.schedule.eval_slot | PT evaluation slot | invariant | Slot reserves therapist time for initial assessment, goals and plan of care. | episode entry |
| ptclinic.schedule.treatment_slot | Treatment visit slot | invariant | Slot reserves therapist, assistant, equipment and treatment space. | therapy capacity |
| ptclinic.schedule.plan_frequency | Plan frequency | invariant | Frequency defines expected visits per week or period in plan of care. | schedule matches plan |
| ptclinic.schedule.cancel_no_show | PT cancel or no-show | invariant | Record notes missed visit, reason, policy, patient contact and effect on plan. | continuity risk |
| ptclinic.schedule.progress_due | Progress note due | invariant | Due date tracks required reassessment or payer progress report interval. | documentation clock |
| ptclinic.intake.patient_goals | Patient therapy goals | invariant | Goals capture patient priorities such as walking, work, sport, pain reduction or function. | meaningful plan |
| ptclinic.intake.outcome_measure | Outcome measure | invariant | Measure quantifies baseline function, pain, balance, mobility or disability. | track change |
| ptclinic.intake.precaution_flag | Therapy precaution flag | invariant | Flag marks weight bearing, post-op limits, fall risk, cardiac, infection or other restrictions. | safe exercise |
| ptclinic.intake.consent_forms | PT consent forms | invariant | Forms document consent to evaluation, treatment, privacy and financial policies. | permission and clarity |
| ptclinic.intake.home_program_baseline | Home program baseline | variant | Baseline records what patient already does and barriers to adherence. | realistic homework |
| ptclinic.eval.initial_evaluation | Initial PT evaluation | invariant | Evaluation documents history, exam, impairments, function, assessment and plan. | clinical foundation |
| ptclinic.eval.range_of_motion | Range of motion record | invariant | Record captures joint movement measurement, side, method and limitation. | mobility datum |
| ptclinic.eval.strength_assessment | Strength assessment | invariant | Assessment records muscle performance or functional strength using defined scale or task. | capacity datum |
| ptclinic.eval.gait_observation | Gait observation | variant | Observation notes walking pattern, device, safety, speed, pain or compensation. | movement insight |
| ptclinic.eval.fall_risk_screen | Fall risk screen | variant | Screen evaluates balance, history, mobility aids and home risk. | prevent injury |
| ptclinic.treatment.exercise_flow | Therapeutic exercise flow | invariant | Flow sequences warm-up, exercises, dosage, cues, rest and response monitoring. | structured session |
| ptclinic.treatment.manual_therapy_note | Manual therapy note | variant | Note records technique region, purpose, patient response and precautions. | document hands-on care |
| ptclinic.treatment.modality_use | Therapy modality use | variant | Use records heat, ice, stimulation, ultrasound or other modality with indication and response. | support treatment |
| ptclinic.treatment.neuromuscular_reeducation | Neuromuscular reeducation | variant | Activity retrains balance, coordination, posture, movement control or proprioception. | movement quality |
| ptclinic.treatment.patient_response | Patient response record | invariant | Record notes pain, fatigue, tolerance, adverse symptoms and progress during visit. | adjust care |
| ptclinic.home.hep_instruction | Home exercise program instruction | invariant | Instruction gives approved exercises, frequency, safety cues and progression limits. | work between visits |
| ptclinic.home.hep_adherence | Home program adherence | variant | Adherence record notes completion, barriers, symptoms and needed adjustment. | real-world progress |
| ptclinic.home.exercise_sheet | Exercise sheet | variant | Sheet provides visual or written exercise instructions tied to patient plan. | memory aid |
| ptclinic.home.equipment_need | Home equipment need | variant | Need identifies bands, cane, brace, ice pack or home setup for program. | practical support |
| ptclinic.home.safety_instruction | Home safety instruction | invariant | Instruction warns about stop signs, fall prevention, pain limits and when to contact clinic. | avoid harm |
| ptclinic.documentation.daily_note | PT daily note | invariant | Note records interventions, time, response, changes, education and plan for next visit. | visit evidence |
| ptclinic.documentation.progress_note | PT progress note | invariant | Note compares baseline, goals, measures, response and need for continued care. | justify ongoing therapy |
| ptclinic.documentation.plan_of_care | Plan of care | invariant | Plan states diagnosis, goals, frequency, interventions, duration and discharge criteria. | treatment roadmap |
| ptclinic.documentation.discharge_summary | PT discharge summary | invariant | Summary records outcome, goals met, remaining limits, home plan and follow-up advice. | close episode |
| ptclinic.documentation.late_note | Late documentation flag | invariant | Flag marks documentation not completed on time and needing review. | billing and quality risk |
| ptclinic.flow.gym_space_assignment | Therapy gym space assignment | variant | Assignment coordinates tables, equipment, privacy and therapist coverage. | avoid bottlenecks |
| ptclinic.flow.equipment_sanitization | Therapy equipment sanitization | invariant | Sanitization cleans tables, bands, weights, mats and shared tools between patients. | infection control |
| ptclinic.flow.assistant_handoff | Therapist assistant handoff | variant | Handoff communicates plan, precautions, exercises and supervision needs. | team treatment |
| ptclinic.flow.patient_late_arrival | PT late arrival handling | invariant | Handling adjusts session, documents lost time and protects next appointments. | schedule discipline |
| ptclinic.flow.incident_report | Therapy incident report | invariant | Report documents fall, symptom event, equipment injury, privacy issue or complaint. | safety learning |
| ptclinic.billing.charge_units | Therapy charge units | invariant | Units reflect documented timed or untimed services according to billing rules. | align note and charge |
| ptclinic.billing.denial_reason | PT denial reason | variant | Reason identifies authorization, medical necessity, documentation, coding or eligibility issue. | fix revenue leak |
| ptclinic.metrics.pt_kpi | PT clinic KPI | variant | KPI tracks visits, cancellations, outcomes, authorization use, documentation lag and discharge rates. | manage clinic |
| ptclinic.continuity.therapist_absence | Therapist absence plan | invariant | Plan reschedules, reassigns or notifies patients while preserving clinical continuity. | keep care moving |
