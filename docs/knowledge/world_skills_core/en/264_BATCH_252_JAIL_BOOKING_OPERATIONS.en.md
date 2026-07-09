# BATCH_252 — Jail Booking Operations Detail
# world_skills_core · source: world_skills_core:batch_252:jail_booking_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| jailbook.intake.arrival_record | Jail booking arrival record | invariant | Record captures person, agency, time, location, charges, warrants and transport officer. | start custody |
| jailbook.intake.custody_handoff | Jail custody handoff | invariant | Handoff records restraints, property, documents, medical concerns and officer signatures. | custody continuity |
| jailbook.intake.booking_number | Jail booking number | invariant | Number links arrest, person, charges, property, housing, court and release records. | case control |
| jailbook.intake.arrest_document | Arrest document intake | invariant | Intake verifies arrest report, warrant, court order, citation or commitment paperwork. | legal basis |
| jailbook.identity.identity_check | Jail identity check | invariant | Check compares name, birthdate, identifiers, fingerprints, photo and prior records. | avoid misidentification |
| jailbook.identity.fingerprint_capture | Jail fingerprint capture | invariant | Capture records prints, device, operator, quality, submission and response. | identity evidence |
| jailbook.identity.mugshot_capture | Jail booking photo | invariant | Photo captures face, profile if required, booking ID, date and quality. | visual identification |
| jailbook.identity.alias_record | Jail alias record | variant | Record links aliases, prior names, spelling variants and identifiers. | search history |
| jailbook.property.property_inventory | Jail property inventory | invariant | Inventory lists clothing, cash, cards, phone, jewelry, medication and personal items. | protect property |
| jailbook.property.cash_count | Jail cash count | invariant | Count records currency, coins, cards, receipt, witness and deposit route. | financial custody |
| jailbook.property.contraband_find | Jail booking contraband finding | invariant | Finding records prohibited item, location, officer, evidence route and incident. | facility safety |
| jailbook.property.property_release | Jail property release | variant | Release records authorized recipient, items, ID, signature and retained exceptions. | return property |
| jailbook.medical.medical_screen | Jail medical screen | invariant | Screen identifies urgent symptoms, medications, injuries, intoxication and care referral. | health triage |
| jailbook.medical.mental_health_screen | Jail mental health screen | invariant | Screen flags self-harm risk, crisis, history, behavior and mental health referral. | suicide prevention |
| jailbook.medical.medication_record | Jail medication record | invariant | Record captures reported medication, verification status, storage and clinician review. | care continuity |
| jailbook.medical.injury_documentation | Jail injury documentation | invariant | Documentation records visible injury, statement, photos, care and notifications. | protect person |
| jailbook.medical.detox_watch | Jail detox watch flag | variant | Flag routes intoxication or withdrawal concern to observation and medical protocol. | reduce harm |
| jailbook.classification.risk_screen | Jail classification risk screen | invariant | Screen evaluates charges, behavior, history, separation needs and vulnerability. | housing decision |
| jailbook.classification.separation_alert | Jail separation alert | invariant | Alert separates enemies, codefendants, victims, juveniles, protective custody or special status. | prevent conflict |
| jailbook.classification.housing_assignment | Jail housing assignment | invariant | Assignment links classification, bed, unit, restrictions, gender policy and availability. | place safely |
| jailbook.classification.special_watch | Jail special watch | variant | Watch records suicide, medical, detox, assault, escape or protective observation level. | monitor risk |
| jailbook.housing.bed_move | Jail bed move | invariant | Move records old bed, new bed, reason, time, officer and restrictions. | location accuracy |
| jailbook.housing.orientation | Jail intake orientation | invariant | Orientation explains rules, rights, requests, grievances, phones, mail and safety. | inform detainee |
| jailbook.housing.clothing_issue | Jail clothing issue | variant | Issue records uniform, bedding, hygiene kit, sizes and replacement needs. | basic supplies |
| jailbook.court.court_date_entry | Jail court date entry | invariant | Entry records court, date, time, judge, transport need and notice. | ensure appearance |
| jailbook.court.bail_bond_record | Jail bail or bond record | variant | Record captures amount, conditions, authority, payer, receipt and release eligibility. | release control |
| jailbook.court.hold_record | Jail hold record | invariant | Hold records warrant, agency, detainer, sentence, probation or immigration notice. | custody constraints |
| jailbook.court.transport_list | Jail court transport list | variant | List groups detainees by court, time, custody level, restraints and medical needs. | transport planning |
| jailbook.records.case_file | Jail booking case file | invariant | File stores booking sheet, charges, property, screens, classification and release documents. | official record |
| jailbook.records.data_correction | Jail booking data correction | invariant | Correction fixes name, charge, date, property or housing error with audit reason. | accurate records |
| jailbook.records.notification_log | Jail booking notification log | variant | Log records attorney, consulate, guardian, victim, agency or court notice when required. | compliance |
| jailbook.release.release_eligibility | Jail release eligibility check | invariant | Check reviews holds, court order, bail, sentence, fees, identity and property. | lawful release |
| jailbook.release.release_packet | Jail release packet | invariant | Packet includes property, instructions, court dates, conditions, referrals and receipts. | complete exit |
| jailbook.release.time_served | Jail time-served release | variant | Release calculates sentence credit, order, holds, approval and discharge time. | close custody |
| jailbook.release.transfer_release | Jail transfer release | variant | Release transfers person to another agency, court, hospital or facility with custody logs. | custody handoff |
| jailbook.safety.use_of_force_note | Jail booking force note | invariant | Note documents force, restraints, injuries, witnesses, review and reporting. | accountability |
| jailbook.safety.booking_area_check | Jail booking area check | invariant | Check reviews cameras, panic alarms, cells, benches, restraints, sanitation and hazards. | safe intake |
| jailbook.safety.language_access | Jail booking language access | invariant | Access provides interpreter, translated rights, forms and communication support. | understand process |
| jailbook.quality.audit | Jail booking audit | invariant | Audit checks legal basis, identity, property, medical screen, classification and release. | reduce errors |
| jailbook.reporting.daily_booking_report | Daily jail booking report | invariant | Report summarizes bookings, releases, holds, medical flags, incidents and population impact. | operational awareness |
| jailbook.reporting.population_update | Jail population update | variant | Update tracks booked, housed, released, transfers, capacity and classification mix. | capacity control |
| jailbook.metrics.booking_kpi | Jail booking KPI | variant | KPI tracks booking time, release time, property variances, medical flags, incidents and errors. | manage booking |
| jailbook.continuity.system_outage | Jail booking system outage | invariant | Outage plan uses paper logs, manual numbering, later entry and custody safeguards. | keep custody legal |
| jailbook.continuity.surge_intake | Jail booking surge intake | variant | Surge plan adds staff, triage, holding space, medical screening and court coordination. | handle volume |
