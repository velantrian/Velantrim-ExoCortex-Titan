# BATCH 405: Emergency Childcare Support Operations

**KnowledgeUnits:** 44  
**Namespace:** `emchildcareops.*`  
**Scope:** intake, eligibility, provider checks, safe spaces, staffing, sign-in/out and incident reporting.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| emchildcareops.activation.trigger | support trigger | MODEL | Trigger includes sheltering, school closure, recovery appointments, work need or caregiver disruption. | Starts childcare support. |
| emchildcareops.activation.service_model | service model | RECORD | Model distinguishes supervised child area, voucher, referral, respite or mobile support. | Defines operation. |
| emchildcareops.activation.command_link | command link | RECORD | Operation links sheltering, family services, public health, safety and legal compliance. | Clarifies oversight. |
| emchildcareops.activation.age_scope | age scope | CONSTRAINT | Age scope defines eligible child ages, ratios and exclusion limits. | Sets boundaries. |
| emchildcareops.intake.child_profile | child profile | RECORD | Profile captures name, age, caregiver, allergies, medical notes, language and special needs. | Enables safe care. |
| emchildcareops.intake.caregiver_identity | caregiver identity | RECORD | Caregiver record captures authorized adults, contact and pickup permissions. | Protects release. |
| emchildcareops.intake.emergency_contact | emergency contact | RECORD | Contact records backup adult, phone, relationship and safe-contact limits. | Supports incidents. |
| emchildcareops.intake.consent | consent record | RECORD | Consent documents participation, pickup rules, emergency care permission and data sharing. | Establishes authorization. |
| emchildcareops.eligibility.criteria | eligibility criteria | CONSTRAINT | Criteria define disaster impact, caregiver need, location, age and service availability. | Preserves fairness. |
| emchildcareops.eligibility.priority | priority model | MODEL | Priority weighs caregiver work, appointments, sheltering, disability, single caregiver and safety risk. | Orders slots. |
| emchildcareops.eligibility.duration_limit | duration limit | CONSTRAINT | Limit defines hours, days, breaks and repeat use policy. | Manages capacity. |
| emchildcareops.eligibility.waitlist | waitlist | RECORD | Waitlist records child, caregiver, priority, requested time and contact method. | Tracks unmet demand. |
| emchildcareops.provider.provider_roster | provider roster | RECORD | Roster lists licensed providers, nonprofits, school partners and vetted volunteers. | Builds capacity. |
| emchildcareops.provider.background_check | background check | SAFETY_RULE | Providers and staff meet required screening before unsupervised access. | Protects children. |
| emchildcareops.provider.license_status | license status | QUALITY_CHECK | License or emergency approval status is verified and recorded. | Maintains compliance. |
| emchildcareops.provider.scope_match | scope match | METHOD | Provider is matched to age, hours, accessibility, language and special care needs. | Improves fit. |
| emchildcareops.safe_space.site_check | site check | QUALITY_CHECK | Site checks exits, hazards, sanitation, restrooms, lighting, noise and supervision visibility. | Creates safe area. |
| emchildcareops.safe_space.childproofing | childproofing | SAFETY_RULE | Hazards, cords, chemicals, sharp objects and unsafe furniture are removed or controlled. | Reduces injury. |
| emchildcareops.safe_space.supplies | supplies list | RECORD | Supplies include mats, toys, hygiene, water, snacks, diapers, first aid and sign-in tools. | Supports care. |
| emchildcareops.safe_space.separation | separation rule | SAFETY_RULE | Child area separates from traffic, adult sleeping areas, vehicles and unsafe work zones. | Protects children. |
| emchildcareops.staffing.ratio | staffing ratio | CONSTRAINT | Ratio defines minimum adults per child by age and need. | Maintains supervision. |
| emchildcareops.staffing.role_assignment | role assignment | RECORD | Roles include lead, sign-in, activity, hygiene, runner, safety and floater. | Organizes staff. |
| emchildcareops.staffing.shift_brief | shift brief | METHOD | Brief covers roster, allergies, pickup rules, incidents, hazards and escalation. | Aligns staff. |
| emchildcareops.staffing.fatigue | fatigue control | SAFETY_RULE | Breaks, shift length and backup staffing prevent supervision lapses. | Keeps care reliable. |
| emchildcareops.signin.child_signin | child sign-in | RECORD | Sign-in records child, caregiver, time, staff, authorized pickup and condition notes. | Establishes custody. |
| emchildcareops.signin.pickup_check | pickup check | SAFETY_RULE | Pickup verifies authorized adult before release. | Prevents wrongful release. |
| emchildcareops.signin.late_pickup | late pickup | METHOD | Late pickup process contacts caregiver, backup, supervisor and protective pathway if needed. | Handles risk. |
| emchildcareops.signin.headcount | headcount | MEASUREMENT | Headcount checks children present against sign-in roster at set intervals. | Prevents missing child. |
| emchildcareops.health.allergy_flag | allergy flag | SAFETY_RULE | Allergy information controls snacks, medications, activities and emergency response. | Prevents reactions. |
| emchildcareops.health.illness_screen | illness screen | QUALITY_CHECK | Screen identifies fever, symptoms, exposure concerns or need for medical referral. | Protects group. |
| emchildcareops.health.medication_boundary | medication boundary | CONSTRAINT | Staff do not administer medication unless policy, authorization and trained role allow. | Prevents unsafe care. |
| emchildcareops.health.hygiene_routine | hygiene routine | METHOD | Routine covers handwashing, diapering, surfaces, toys and waste. | Reduces infection. |
| emchildcareops.activities.age_activity | age-appropriate activity | METHOD | Activities match age, stress level, culture, language and available space. | Supports wellbeing. |
| emchildcareops.activities.trauma_aware | trauma-aware approach | METHOD | Staff use calm routines, choices, reassurance and escalation for distress. | Reduces stress. |
| emchildcareops.activities.quiet_option | quiet option | METHOD | Quiet option supports sensory needs, fatigue or distress. | Improves inclusion. |
| emchildcareops.activities.family_reunification | reunification support | METHOD | Childcare coordinates with family reunification when caregiver location changes. | Maintains safety. |
| emchildcareops.incident.incident_report | incident report | RECORD | Report captures injury, illness, missing child, behavioral event, release issue or hazard. | Creates response trail. |
| emchildcareops.incident.notification | caregiver notification | METHOD | Caregiver and supervisor are notified based on severity and policy. | Ensures transparency. |
| emchildcareops.incident.escalation | escalation path | SAFETY_RULE | Serious incidents escalate to medical, security, child protection or command. | Protects child. |
| emchildcareops.incident.corrective_action | corrective action | RECORD | Corrective action records hazard fix, staffing change, retraining or closure. | Prevents recurrence. |
| emchildcareops.records.daily_log | daily log | RECORD | Log stores attendance, staff, incidents, supplies, waitlist and unmet needs. | Summarizes operation. |
| emchildcareops.metrics.slot_utilization | slot utilization | MEASUREMENT | Utilization tracks available slots, used slots, waitlist and no-shows. | Shows capacity. |
| emchildcareops.metrics.incident_rate | incident rate | MEASUREMENT | Incident rate tracks events by type, age group and shift. | Guides improvement. |
| emchildcareops.review.after_action | after-action review | METHOD | Review captures safety, staffing, provider checks, sign-out controls and family feedback. | Improves future care. |
