# BATCH 382: Post-Disaster Building Safety Placarding Operations

**KnowledgeUnits:** 44  
**Namespace:** `placardops.*`  
**Scope:** inspection teams, placards, occupancy restrictions, appeals, data and public notices.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| placardops.activation.trigger | placarding trigger | MODEL | Trigger includes earthquake, flood, fire, storm or structural hazard affecting buildings. | Starts safety posting. |
| placardops.activation.authority | placarding authority | RECORD | Authority records building official, emergency order, jurisdiction and inspection period. | Clarifies legal basis. |
| placardops.activation.team_roster | team roster | RECORD | Roster lists inspectors, engineers, admin, GIS and safety support. | Assigns capacity. |
| placardops.activation.priority_area | priority area | METHOD | Priority areas include collapse risk, dense occupancy, critical facilities and public reports. | Sends teams where risk is high. |
| placardops.inspection.structure_id | structure ID | RECORD | Structure ID links address, parcel, owner, occupancy and inspection history. | Grounds placard decisions. |
| placardops.inspection.rapid_eval | rapid evaluation | METHOD | Rapid evaluation checks visible hazards, occupancy risk and need for detailed review. | Quickly protects public. |
| placardops.inspection.detailed_eval | detailed evaluation | METHOD | Detailed evaluation uses qualified specialist for complex damage. | Improves decision confidence. |
| placardops.inspection.access_limit | access limit | CONSTRAINT | Inspectors may be blocked by utilities, flooding, fire, unsafe entry or owner access. | Explains pending status. |
| placardops.placard.green | green placard | RECORD | Green placard indicates no restriction from rapid assessment, with caveats. | Allows use while noting limits. |
| placardops.placard.yellow | yellow placard | RECORD | Yellow placard restricts occupancy or areas until repairs/review. | Communicates limited use. |
| placardops.placard.red | red placard | SAFETY_RULE | Red placard prohibits entry or occupancy except authorized access. | Protects life safety. |
| placardops.placard.custom | custom condition | METHOD | Custom condition states specific room, floor, utility or time restriction. | Avoids over/under restriction. |
| placardops.criteria.structural | structural criteria | MODEL | Criteria consider foundation, walls, roof, connections, settlement and collapse signs. | Supports consistent placards. |
| placardops.criteria.fire | fire damage criteria | MODEL | Fire criteria include charring, smoke, utilities, roof, stairs and hazardous materials. | Guides safe reentry. |
| placardops.criteria.flood | flood damage criteria | MODEL | Flood criteria include undermining, contamination, electrical and mold risk. | Handles water damage. |
| placardops.criteria.utility | utility hazard | SAFETY_RULE | Gas, electrical, water or elevator hazards can drive occupancy restriction. | Prevents secondary injury. |
| placardops.posting.placement | placard placement | METHOD | Placard is posted visibly at main entrance or safe access point. | Makes status clear. |
| placardops.posting.photo | posting photo | RECORD | Photo documents placard, building, date and inspector. | Supports enforcement. |
| placardops.posting.tamper | tamper rule | SAFETY_RULE | Removing or altering placard is prohibited and enforceable. | Maintains control. |
| placardops.posting.expiry | review date | RECORD | Placard may include review, expiration or reinspection date. | Shows next step. |
| placardops.owner.notice | owner notice | METHOD | Owner receives placard reason, restrictions, appeal and repair path. | Supports due process. |
| placardops.owner.tenant | tenant communication | METHOD | Tenants receive safe-entry, belongings, relocation and contact information. | Protects occupants. |
| placardops.owner.language | language support | METHOD | Notices use plain language and translation where feasible. | Improves compliance. |
| placardops.owner.entry | limited entry permit | CONSTRAINT | Limited entry may allow retrieval, repairs or inspection under conditions. | Balances safety and needs. |
| placardops.data.field_form | field form | RECORD | Form records damage, placard, photos, inspector, time and notes. | Standardizes records. |
| placardops.data.gis_update | GIS update | METHOD | Placard status updates map and dashboard layers. | Gives command visibility. |
| placardops.data.duplicate | duplicate check | QUALITY_CHECK | Duplicate checks merge repeated inspections for same structure. | Keeps status accurate. |
| placardops.data.privacy | privacy boundary | CONSTRAINT | Public maps avoid unnecessary personal owner/tenant data. | Protects residents. |
| placardops.enforcement.restriction | restriction enforcement | SAFETY_RULE | Unsafe occupancy can trigger enforcement, police/fire support or utility action. | Protects public. |
| placardops.enforcement.contractor_access | contractor access | METHOD | Contractors need permits, safety plan or official permission for restricted buildings. | Controls repair work. |
| placardops.enforcement.reopen | reopening condition | CONSTRAINT | Reopening requires repair, engineer letter, permit signoff or reinspection. | Prevents premature use. |
| placardops.enforcement.violation | violation record | RECORD | Violations record illegal entry, placard removal or unsafe occupancy. | Supports action. |
| placardops.appeal.request | appeal request | RECORD | Appeal records owner/occupant challenge, evidence and desired change. | Starts review. |
| placardops.appeal.review_panel | review panel | METHOD | Qualified official or panel reviews contested placard. | Provides due process. |
| placardops.appeal.outcome | appeal outcome | RECORD | Outcome records upheld, modified, removed or pending further inspection. | Closes appeal. |
| placardops.appeal.timeline | appeal timeline | CONSTRAINT | Timelines define response and reinspection expectations. | Reduces uncertainty. |
| placardops.repair.permit_link | permit link | RECORD | Placard case links to repair permits and inspections. | Connects safety to repair process. |
| placardops.repair.engineer_letter | engineer letter | RECORD | Engineer letter may document repair adequacy or temporary shoring. | Supports reclassification. |
| placardops.repair.reinspection | reinspection | QUALITY_CHECK | Reinspection verifies repairs or changed conditions before placard change. | Maintains safety. |
| placardops.public.status_map | public status map | METHOD | Public map shows placard category and general location where policy allows. | Informs community. |
| placardops.public.faq | public FAQ | METHOD | FAQ explains placard colors, entry rules, appeals and resources. | Reduces confusion. |
| placardops.records.retention | retention rule | CONSTRAINT | Inspection, photos, appeals and permits follow building/legal retention rules. | Preserves evidence. |
| placardops.metrics.counts | placard counts | MEASUREMENT | Counts track green, yellow, red, pending and cleared structures. | Shows recovery status. |
| placardops.closeout.clearance | clearance closeout | METHOD | Case closes when placard is removed, replaced by normal permit case, or demolition completed. | Ends emergency status. |
