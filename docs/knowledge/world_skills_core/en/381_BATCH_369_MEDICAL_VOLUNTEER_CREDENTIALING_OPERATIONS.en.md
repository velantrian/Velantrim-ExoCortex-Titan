# BATCH 369: Medical Volunteer Credentialing Operations

**KnowledgeUnits:** 44  
**Namespace:** `medvolcredops.*`  
**Scope:** license checks, scope, assignments, supervision, liability, tracking and demobilization.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| medvolcredops.intake.volunteer_id | volunteer ID | RECORD | Volunteer ID links person, profession, credentials, availability and assignments. | Creates controlled roster. |
| medvolcredops.intake.application | application | RECORD | Application captures identity, contact, license, skills, language and emergency contact. | Starts screening. |
| medvolcredops.intake.affiliation | affiliation | RECORD | Affiliation records employer, reserve corps, NGO, school or unaffiliated status. | Guides trust level. |
| medvolcredops.intake.availability | availability | RECORD | Availability records dates, shift limits, location and remote capability. | Supports deployment planning. |
| medvolcredops.identity.id_check | identity check | SAFETY_RULE | Identity is verified before credential approval. | Prevents impersonation. |
| medvolcredops.identity.background | background screen | CONSTRAINT | Background screening applies by role, site and vulnerable population exposure. | Reduces safeguarding risk. |
| medvolcredops.identity.reference | reference check | METHOD | References or affiliation confirm professional standing where required. | Adds confidence. |
| medvolcredops.identity.duplicate | duplicate profile | FAILURE_MODE | Duplicate profiles split credentials and assignment history. | Requires merge control. |
| medvolcredops.license.primary_source | primary source verification | QUALITY_CHECK | License is verified from official board or approved registry. | Confirms legal authority. |
| medvolcredops.license.status | license status | RECORD | Status records active, expired, suspended, restricted or out-of-state. | Guides eligibility. |
| medvolcredops.license.expiry | license expiry alert | MEASUREMENT | Expiry alerts flag credentials needing renewal before deployment. | Prevents stale rosters. |
| medvolcredops.license.compact | compact or reciprocity | CONSTRAINT | Interstate practice depends on emergency orders, compacts or reciprocity rules. | Keeps practice lawful. |
| medvolcredops.scope.scope_map | scope map | RECORD | Scope maps profession, license, training and permitted tasks. | Prevents unsafe assignment. |
| medvolcredops.scope.restriction | restriction | CONSTRAINT | Restrictions include supervision, procedure limits, prescribing limits or population limits. | Protects patients. |
| medvolcredops.scope.training_gap | training gap | MODEL | Gap identifies tasks needing orientation before assignment. | Targets briefing. |
| medvolcredops.scope.nonclinical | nonclinical option | METHOD | Volunteers outside clinical scope may support logistics, education or admin. | Uses capacity safely. |
| medvolcredops.training.orientation | orientation | METHOD | Orientation covers incident structure, privacy, safety, documentation and site workflow. | Aligns volunteers. |
| medvolcredops.training.justintime | just-in-time training | METHOD | Short training covers site-specific tasks and hazards. | Enables rapid deployment. |
| medvolcredops.training.competency | competency attestation | RECORD | Volunteer attests or demonstrates competence for assigned task. | Supports accountability. |
| medvolcredops.training.ppe | PPE training | SAFETY_RULE | PPE training matches task and infectious or physical hazards. | Protects volunteer and patient. |
| medvolcredops.assignment.request | assignment request | RECORD | Request states role, site, shift, supervisor, scope and number needed. | Defines demand. |
| medvolcredops.assignment.match | match process | METHOD | Matching uses credential, scope, availability, language, distance and risk. | Sends suitable volunteers. |
| medvolcredops.assignment.supervisor | supervisor link | RECORD | Each volunteer has assigned supervisor or clinical lead. | Maintains oversight. |
| medvolcredops.assignment.badge | badge credential | METHOD | Badge shows identity, role, site and dates. | Controls access. |
| medvolcredops.liability.coverage | liability coverage | CONSTRAINT | Coverage depends on agency status, emergency order, employer and role. | Reduces legal ambiguity. |
| medvolcredops.liability.waiver | waiver | RECORD | Waiver or agreement records risks, conduct and data use. | Documents terms. |
| medvolcredops.liability.workers_comp | injury coverage | CONSTRAINT | Injury coverage route is clarified before field work. | Protects volunteers. |
| medvolcredops.liability.privacy_duty | privacy duty | SAFETY_RULE | Volunteers must follow health privacy and confidentiality rules. | Protects patient data. |
| medvolcredops.tracking.checkin | check-in | METHOD | Check-in confirms arrival, badge, assignment and readiness. | Starts accountability. |
| medvolcredops.tracking.checkout | checkout | METHOD | Checkout records hours, incidents, equipment and next availability. | Closes shift. |
| medvolcredops.tracking.hours | hours tracking | MEASUREMENT | Hours are tracked by role, site and funding category. | Supports reporting. |
| medvolcredops.tracking.exposure | exposure tracking | SAFETY_RULE | Occupational exposures are documented and referred for follow-up. | Protects health. |
| medvolcredops.performance.issue | performance issue | RECORD | Issue records unsafe practice, conduct concern, no-show or documentation gap. | Supports corrective action. |
| medvolcredops.performance.removal | removal process | SAFETY_RULE | Unsafe volunteers can be removed from assignment and roster. | Protects operations. |
| medvolcredops.performance.feedback | feedback | METHOD | Supervisors provide performance feedback and future suitability notes. | Improves roster quality. |
| medvolcredops.communication.alert | deployment alert | METHOD | Alert provides role, time, location, supervisor, PPE and response instructions. | Mobilizes clearly. |
| medvolcredops.communication.update | status update | METHOD | Updates communicate shift changes, demobilization, hazards and unmet needs. | Keeps roster aligned. |
| medvolcredops.records.roster | credentialed roster | RECORD | Roster stores approved volunteers, scope, status and availability. | Enables quick activation. |
| medvolcredops.records.audit | audit trail | RECORD | Audit trail logs credential checks, approvals, assignments and removals. | Supports review. |
| medvolcredops.records.retention | retention rule | CONSTRAINT | Records follow volunteer, medical, emergency and privacy retention rules. | Controls lifecycle. |
| medvolcredops.metrics.fill_rate | fill rate | MEASUREMENT | Fill rate measures roles filled by credential type and time. | Shows staffing readiness. |
| medvolcredops.metrics.no_show | no-show rate | MEASUREMENT | No-show rate tracks accepted assignments not worked. | Improves reliability planning. |
| medvolcredops.demob.release | release process | METHOD | Release returns badges/equipment and records final hours/status. | Ends service cleanly. |
| medvolcredops.review.after_action | after-action review | METHOD | Review captures credential bottlenecks, scope issues, liability gaps and training needs. | Improves next activation. |
