# BATCH 411: Disaster Tenant Habitability Documentation Support Operations

**KnowledgeUnits:** 44  
**Namespace:** `tenanthabitops.*`  
**Scope:** photos, notices, code referrals, repair requests, landlord contact and timelines.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| tenanthabitops.intake.request_source | request source | RECORD | Source records shelter, legal clinic, hotline, tenant, caseworker or inspector referral. | Shows entry path. |
| tenanthabitops.intake.tenant_profile | tenant profile | RECORD | Profile captures tenant contact, unit address, lease status, language and safe-contact limits. | Defines case. |
| tenanthabitops.intake.damage_summary | damage summary | RECORD | Summary lists water, mold, heat, power, smoke, structural, pest or access issues. | Frames habitability. |
| tenanthabitops.intake.urgency | urgency model | MODEL | Urgency weighs unsafe occupancy, children, medical risk, shutoff, eviction threat and deadline. | Prioritizes support. |
| tenanthabitops.photos.photo_plan | photo plan | METHOD | Plan identifies rooms, defects, date markers, wide views and close-ups. | Builds evidence. |
| tenanthabitops.photos.consent | photo consent | SAFETY_RULE | Photos avoid people, private papers and sensitive belongings unless consent and purpose allow. | Protects privacy. |
| tenanthabitops.photos.metadata | photo metadata | RECORD | Metadata records date, unit, issue, photographer and storage location. | Preserves context. |
| tenanthabitops.photos.before_after | before-after set | RECORD | Before-after photos document repair progress or continuing hazard. | Shows timeline. |
| tenanthabitops.notices.landlord_notice | landlord notice | RECORD | Notice records issue, date sent, method, requested repair and deadline if applicable. | Creates paper trail. |
| tenanthabitops.notices.delivery_proof | delivery proof | RECORD | Proof captures certified mail, email, text, portal, hand delivery or witness. | Verifies notice. |
| tenanthabitops.notices.response_log | response log | RECORD | Log records landlord replies, promises, denials, visits and repair dates. | Tracks conduct. |
| tenanthabitops.notices.followup_notice | follow-up notice | METHOD | Follow-up restates unresolved issues, new damage and prior communication. | Maintains pressure. |
| tenanthabitops.code.code_referral | code referral | METHOD | Referral routes habitability issue to housing, building, fire, health or code office. | Gets inspection path. |
| tenanthabitops.code.jurisdiction | jurisdiction check | QUALITY_CHECK | Check identifies correct city, county, housing authority or campus office. | Avoids misrouting. |
| tenanthabitops.code.case_number | case number | RECORD | Case number records agency, inspector, date, complaint ID and next step. | Tracks referral. |
| tenanthabitops.code.inspection_prep | inspection prep | METHOD | Prep helps tenant organize photos, access, notice history and hazard list. | Improves inspection. |
| tenanthabitops.repairs.repair_request | repair request | RECORD | Request lists issue, location, severity, date discovered and requested action. | Defines ask. |
| tenanthabitops.repairs.priority | repair priority | MODEL | Priority separates life safety, essential services, habitability, nuisance and cosmetic issues. | Focuses effort. |
| tenanthabitops.repairs.access_window | access window | RECORD | Window records when landlord or contractor may enter and tenant constraints. | Enables repair. |
| tenanthabitops.repairs.incomplete_repair | incomplete repair | RECORD | Incomplete repair records work done, remaining issue, photos and tenant concern. | Supports follow-up. |
| tenanthabitops.landlord.contact_record | landlord contact | RECORD | Contact stores owner, manager, phone, email, portal, address and preferred method. | Enables communication. |
| tenanthabitops.landlord.communication_script | communication script | METHOD | Script keeps tenant messages factual, dated, specific and non-escalatory. | Improves clarity. |
| tenanthabitops.landlord.retaliation_flag | retaliation flag | SAFETY_RULE | Retaliation concerns route to legal aid or tenant protection pathway. | Protects tenant. |
| tenanthabitops.landlord.access_dispute | access dispute | RECORD | Dispute records missed entry, denied access, unclear notice or safety concern. | Clarifies delay. |
| tenanthabitops.timeline.event_log | event log | RECORD | Timeline records damage, notice, responses, inspection, repairs, expenses and displacement. | Organizes facts. |
| tenanthabitops.timeline.deadline | deadline capture | SAFETY_RULE | Deadlines for court, inspection, insurance or assistance are flagged. | Prevents missed rights. |
| tenanthabitops.timeline.expense_log | expense log | RECORD | Expenses record temporary lodging, cleaning, storage, lost food or repair supplies. | Supports claims. |
| tenanthabitops.timeline.displacement | displacement record | RECORD | Displacement records dates away, shelter use, reason and return status. | Shows impact. |
| tenanthabitops.documents.lease_copy | lease copy | RECORD | Lease copy or tenancy proof is linked to case file. | Supports eligibility. |
| tenanthabitops.documents.utility_bills | utility bills | RECORD | Bills document service address, shutoffs, abnormal use or account issues. | Supports claims. |
| tenanthabitops.documents.notice_packet | notice packet | RECORD | Packet groups notices, delivery proof, photos, inspection notes and timeline. | Prepares referral. |
| tenanthabitops.documents.secure_storage | secure storage | SAFETY_RULE | Documents are stored with privacy controls and limited access. | Protects tenant. |
| tenanthabitops.referral.legal_aid | legal aid referral | METHOD | Legal aid handles eviction, retaliation, repair enforcement or deposit dispute. | Adds expertise. |
| tenanthabitops.referral.housing_assist | housing assistance referral | METHOD | Housing referral handles relocation, rent aid, hotel, shelter or case management. | Supports safety. |
| tenanthabitops.referral.health | health referral | METHOD | Health referral handles mold symptoms, injury, sanitation or vulnerable occupant risk. | Protects residents. |
| tenanthabitops.referral.mediation | mediation referral | METHOD | Mediation offers structured landlord-tenant communication where appropriate. | Reduces conflict. |
| tenanthabitops.followup.status_check | status check | METHOD | Staff check repair progress, inspection result, legal referral and tenant safety. | Keeps case moving. |
| tenanthabitops.followup.unreachable | unreachable process | METHOD | Attempts, backup contact and closure reason are documented. | Maintains audit. |
| tenanthabitops.followup.closeout | closeout | RECORD | Closeout records resolved, referred, moved, unresolved or no-contact status. | Ends support. |
| tenanthabitops.metrics.case_volume | case volume | MEASUREMENT | Volume tracks habitability cases by issue, area and referral source. | Shows demand. |
| tenanthabitops.metrics.repair_time | repair time | MEASUREMENT | Repair time measures notice to documented repair or referral outcome. | Reveals delays. |
| tenanthabitops.metrics.referral_rate | referral rate | MEASUREMENT | Referral rate shows legal, code, housing and health pathways used. | Plans partners. |
| tenanthabitops.qa.packet_review | packet review | QUALITY_CHECK | Review checks that photos, notices, timeline and referrals are coherent. | Improves evidence. |
| tenanthabitops.review.after_action | after-action review | METHOD | Review captures documentation barriers, landlord response, code routing and privacy lessons. | Improves future support. |
