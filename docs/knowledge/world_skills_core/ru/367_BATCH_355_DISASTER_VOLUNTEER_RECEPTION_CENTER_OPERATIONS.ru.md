# BATCH 355: Disaster Volunteer Reception Center Operations

**KnowledgeUnits:** 44  
**Namespace:** `volreceptionops.*`  
**Scope:** registration, credentialing, assignments, safety briefings, tracking and demobilization.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| volreceptionops.activation.trigger | activation trigger | MODEL | Volunteer center activates when incident needs exceed regular staff or partner capacity. | Opens volunteer intake only when useful. |
| volreceptionops.activation.authority | activation authority | RECORD | Authority records emergency manager, lead agency, site and operating period. | Clarifies command responsibility. |
| volreceptionops.activation.site_setup | site setup | METHOD | Site setup separates reception, registration, credentialing, briefing, assignment and checkout. | Keeps volunteer flow orderly. |
| volreceptionops.activation.partner_roles | partner roles | RECORD | Partner roles identify voluntary organizations, city staff, nonprofits and incident command links. | Prevents duplicate coordination. |
| volreceptionops.registration.volunteer_id | volunteer ID | RECORD | Volunteer ID links person, contact, skills, availability, assignment and history. | Creates traceable deployment record. |
| volreceptionops.registration.contact | contact details | RECORD | Contact details include phone, email, emergency contact and communication preference. | Enables recall and safety checks. |
| volreceptionops.registration.availability | availability window | RECORD | Availability captures dates, hours, transport limits and preferred work type. | Matches people to realistic shifts. |
| volreceptionops.registration.consent | consent and waiver | CONSTRAINT | Waivers and data consent are collected according to program and legal rules. | Controls liability and privacy. |
| volreceptionops.credentialing.identity | identity check | SAFETY_RULE | Identity is checked before assignment where risk or facility access requires it. | Protects survivors and sites. |
| volreceptionops.credentialing.background | background check route | CONSTRAINT | Sensitive roles may require background screening or verified partner credential. | Reduces safeguarding risk. |
| volreceptionops.credentialing.skill_proof | skill proof | RECORD | Licenses, certifications or experience are recorded for specialized roles. | Prevents unsafe tasking. |
| volreceptionops.credentialing.badge | badge issue | METHOD | Badge identifies volunteer, role, date and site access level. | Helps site control. |
| volreceptionops.screening.safety_fit | safety fit screen | METHOD | Screen checks physical limits, stress tolerance, age restrictions and equipment needs. | Avoids harmful assignments. |
| volreceptionops.screening.conflict | conflict screen | METHOD | Conflict screen identifies self-deployment, media intent, political activity or personal dispute risks. | Keeps response focused. |
| volreceptionops.screening.spontaneous | spontaneous volunteer | MODEL | Spontaneous volunteers need structured intake before task assignment. | Turns surge goodwill into safe labor. |
| volreceptionops.assignments.request_board | request board | RECORD | Request board lists task, location, skills, number needed, supervisor and shift. | Matches work demand to volunteers. |
| volreceptionops.assignments.match | assignment match | METHOD | Match uses skills, availability, location, safety limits and credential status. | Sends right person to right task. |
| volreceptionops.assignments.supervisor | supervisor link | RECORD | Each assignment has named supervisor and check-in/out path. | Maintains accountability. |
| volreceptionops.assignments.transport | transport plan | METHOD | Transport plan covers route, vehicle, pickup, fuel, parking and return. | Gets volunteers safely to site. |
| volreceptionops.assignments.remote | remote volunteer work | METHOD | Remote tasks include calls, data entry, translation, mapping or logistics support. | Uses volunteers not suited for field work. |
| volreceptionops.briefing.incident | incident briefing | METHOD | Briefing explains hazard, mission, boundaries, chain of command and communications. | Aligns volunteer behavior. |
| volreceptionops.briefing.safety | safety briefing | SAFETY_RULE | Safety briefing covers PPE, heat/cold, lifting, traffic, infection, conflict and reporting. | Reduces injuries. |
| volreceptionops.briefing.conduct | conduct rules | SAFETY_RULE | Conduct rules cover privacy, survivor dignity, media, photos, harassment and politics. | Protects affected people. |
| volreceptionops.briefing.task_card | task card | RECORD | Task card gives assignment, location, supervisor, start/end time and emergency contact. | Makes deployment clear. |
| volreceptionops.tracking.checkin | check-in | METHOD | Check-in records arrival, assignment readiness and badge status. | Starts accountability clock. |
| volreceptionops.tracking.checkout | checkout | METHOD | Checkout records return, hours, incidents, equipment and next availability. | Closes shift safely. |
| volreceptionops.tracking.hours | volunteer hours | MEASUREMENT | Hours track labor by role, site and funding category. | Supports reimbursement and reporting. |
| volreceptionops.tracking.location | location tracking | RECORD | Location tracking records where volunteers are assigned during operational periods. | Supports safety and coordination. |
| volreceptionops.support.food_water | volunteer support | METHOD | Support includes water, rest, meals, toilets, charging and weather protection. | Sustains volunteer workforce. |
| volreceptionops.support.psychological | psychological support | METHOD | Distressing work may require defusing, peer support or referral. | Reduces burnout and harm. |
| volreceptionops.support.equipment | equipment issue | RECORD | Equipment issue records PPE, tools, radios, keys or vehicles. | Enables return and accountability. |
| volreceptionops.support.injury | injury process | SAFETY_RULE | Injury process records first aid, escalation, report and workers/volunteer insurance route. | Protects volunteers. |
| volreceptionops.communication.update | operational update | METHOD | Updates inform volunteers of shift changes, hazards, closure and demobilization. | Keeps field force aligned. |
| volreceptionops.communication.no_show | no-show handling | METHOD | No-shows are recorded and assignments refilled. | Prevents staffing gaps. |
| volreceptionops.communication.family_contact | emergency contact use | SAFETY_RULE | Emergency contacts are used only for safety or serious incident reasons. | Protects privacy. |
| volreceptionops.records.personnel_file | personnel file | RECORD | File stores registration, credentials, assignment, hours and incident notes. | Supports audit. |
| volreceptionops.records.retention | retention rule | CONSTRAINT | Volunteer records follow privacy, grant and incident retention rules. | Controls data lifecycle. |
| volreceptionops.records.data_security | data security | SAFETY_RULE | Volunteer personal data is stored and shared with need-to-know access. | Prevents misuse. |
| volreceptionops.metrics.fill_rate | fill rate | MEASUREMENT | Fill rate measures requested positions filled by time and skill. | Shows staffing effectiveness. |
| volreceptionops.metrics.turnaway | turnaway reason | MEASUREMENT | Turnaway tracks excess, unsafe, unqualified or unsuitable volunteers. | Improves public messaging. |
| volreceptionops.qa.assignment_audit | assignment audit | QUALITY_CHECK | Audit checks whether volunteers were qualified, briefed and checked out. | Improves control. |
| volreceptionops.demobilization.release | release process | METHOD | Release returns badges/equipment, records hours and thanks volunteers. | Ends service cleanly. |
| volreceptionops.demobilization.standdown | standdown notice | METHOD | Standdown notice explains why intake is ending and where future offers go. | Prevents self-deployment. |
| volreceptionops.review.after_action | after-action review | METHOD | Review captures demand, safety, coordination, data and training improvements. | Strengthens next response. |
