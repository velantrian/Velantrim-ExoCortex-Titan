# BATCH 374: Disaster Survivor Assistance Center Operations

**KnowledgeUnits:** 44  
**Namespace:** `survivorcenterops.*`  
**Scope:** multi-agency intake, referrals, benefits, documentation, language support and closeout.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| survivorcenterops.activation.trigger | activation trigger | MODEL | Center activates when survivors need centralized multi-agency support. | Creates one-stop recovery access. |
| survivorcenterops.activation.site | site selection | METHOD | Site checks accessibility, privacy, parking, transit, safety and partner space. | Makes center usable. |
| survivorcenterops.activation.partner_plan | partner plan | RECORD | Plan lists agencies, programs, roles, hours and referral paths. | Coordinates services. |
| survivorcenterops.activation.layout | layout | METHOD | Layout separates reception, triage, agency desks, private rooms and waiting. | Improves flow. |
| survivorcenterops.intake.case_id | survivor case ID | RECORD | Case ID links person/household, disaster, needs, documents and referrals. | Tracks assistance. |
| survivorcenterops.intake.household | household record | RECORD | Household record captures members, address, displacement and contact. | Guides eligibility. |
| survivorcenterops.intake.damage | damage summary | RECORD | Damage summary records home, vehicle, business, medical, documents or income loss. | Routes needs. |
| survivorcenterops.intake.priority | priority level | MODEL | Priority considers homelessness, injury, disability, income loss and safety. | Sends urgent cases forward. |
| survivorcenterops.triage.needs_screen | needs screen | METHOD | Screen identifies shelter, food, benefits, insurance, legal, health and cleanup needs. | Builds service plan. |
| survivorcenterops.triage.program_match | program match | METHOD | Program match maps needs to public, nonprofit and private resources. | Reduces wrong queues. |
| survivorcenterops.triage.duplicate | duplicate check | QUALITY_CHECK | Duplicate check compares household, address, application and prior visits. | Prevents fragmented service. |
| survivorcenterops.triage.warm_handoff | warm handoff | METHOD | Staff walk survivor to agency or connect by phone/portal. | Reduces dropout. |
| survivorcenterops.documents.document_list | document checklist | RECORD | Checklist lists ID, proof of residence, ownership, insurance, income or damage evidence. | Helps survivors prepare. |
| survivorcenterops.documents.lost_docs | lost documents | METHOD | Lost document process routes to ID, vital records or property record replacement. | Restores access to aid. |
| survivorcenterops.documents.scan | document scanning | METHOD | Scanning stores copies with consent and privacy controls. | Reduces repeated paperwork. |
| survivorcenterops.documents.privacy | document privacy | SAFETY_RULE | Sensitive documents are shielded from public view and unauthorized partners. | Protects survivors. |
| survivorcenterops.benefits.application_help | application help | METHOD | Staff support forms without promising eligibility. | Helps completion. |
| survivorcenterops.benefits.status_check | status check | METHOD | Status check explains pending, missing documents, approved, denied or appeal stage. | Reduces uncertainty. |
| survivorcenterops.benefits.appeal_referral | appeal referral | METHOD | Denials or disputes route to legal aid, agency appeal or case review. | Protects rights. |
| survivorcenterops.benefits.fraud_warning | fraud warning | SAFETY_RULE | Survivors receive warning about scams, fees and impersonation. | Reduces exploitation. |
| survivorcenterops.referral.housing | housing referral | METHOD | Housing referral covers shelter, rental aid, repairs, hotels or relocation. | Stabilizes households. |
| survivorcenterops.referral.health | health referral | METHOD | Health referral connects to clinic, medication, mental health or disability support. | Supports recovery. |
| survivorcenterops.referral.legal | legal referral | METHOD | Legal referral covers landlord, insurance, documents, employment or benefits. | Addresses complex barriers. |
| survivorcenterops.referral.cleanup | cleanup referral | METHOD | Cleanup referral connects debris, muck-out, mold, chainsaw or repair support. | Restores homes. |
| survivorcenterops.language.language_screen | language screen | METHOD | Preferred language is identified during reception. | Routes interpretation. |
| survivorcenterops.language.interpreter | interpreter support | METHOD | Interpreters support intake, agency desks and private rooms. | Improves access. |
| survivorcenterops.language.translated_material | translated material | RECORD | Core materials are translated and version-controlled. | Keeps instructions consistent. |
| survivorcenterops.language.accessibility | accessibility support | METHOD | Center supports disability, TTY, mobility, sensory and plain-language needs. | Keeps service inclusive. |
| survivorcenterops.communication.appointment | appointment scheduling | METHOD | Follow-up appointments spread demand and reduce waiting. | Improves service quality. |
| survivorcenterops.communication.case_update | case update | METHOD | Survivors receive next steps, deadlines, contacts and documents needed. | Keeps recovery moving. |
| survivorcenterops.communication.public_notice | public notice | METHOD | Notice states location, hours, services, documents, language and transport. | Helps survivors reach center. |
| survivorcenterops.communication.partner_update | partner update | METHOD | Partners receive demand, gaps, hours changes and urgent needs. | Aligns service network. |
| survivorcenterops.records.case_note | case note | RECORD | Note records needs, referrals, documents, consent and next action. | Supports continuity. |
| survivorcenterops.records.consent | consent record | RECORD | Consent controls information sharing between agencies. | Protects privacy. |
| survivorcenterops.records.retention | retention rule | CONSTRAINT | Records follow disaster, benefits, privacy and grant schedules. | Preserves audit trail. |
| survivorcenterops.records.data_sharing | data sharing rule | CONSTRAINT | Partners share only authorized fields for defined purposes. | Limits misuse. |
| survivorcenterops.safety.site_security | site security | METHOD | Security handles entry, crowding, threats, scams and staff safety. | Keeps center calm. |
| survivorcenterops.safety.behavioral_support | behavioral support | METHOD | Distress, grief or crisis routes to trained support. | Helps survivors cope. |
| survivorcenterops.safety.incident | incident report | RECORD | Incidents record safety, privacy, conflict or medical events. | Supports review. |
| survivorcenterops.metrics.households_served | households served | MEASUREMENT | Count tracks households, visits, agencies used and needs. | Shows reach. |
| survivorcenterops.metrics.unmet_need | unmet need | MEASUREMENT | Unmet need records resources unavailable or waitlisted. | Guides escalation. |
| survivorcenterops.qa.case_audit | case audit | QUALITY_CHECK | Audit checks consent, referrals, documents and closure. | Improves service integrity. |
| survivorcenterops.closeout.transition | transition plan | METHOD | Open cases transfer to long-term recovery groups or agencies. | Prevents abandonment. |
| survivorcenterops.closeout.site_close | site closeout | METHOD | Closeout secures records, returns site and informs public of next service route. | Ends center responsibly. |
