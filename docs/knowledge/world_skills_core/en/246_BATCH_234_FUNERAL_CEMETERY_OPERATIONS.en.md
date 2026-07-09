# BATCH_234 — Funeral Cemetery Operations Detail
# world_skills_core · source: world_skills_core:batch_234:funeral_cemetery_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| cemeteryops.plot.plot_inventory | Cemetery plot inventory | invariant | Inventory tracks plot, section, row, grave, crypt, niche, availability and restrictions. | sell accurately |
| cemeteryops.plot.ownership_record | Cemetery ownership record | invariant | Record links owner, rights, transfer, restrictions, documents and contact. | rights evidence |
| cemeteryops.plot.reservation_hold | Cemetery plot reservation hold | variant | Hold reserves plot or niche with deposit, expiry, conditions and release process. | manage demand |
| cemeteryops.plot.deed_issue | Cemetery deed issue | invariant | Issue records right of interment document, signatures, fees and delivery. | formalize rights |
| cemeteryops.plot.map_update | Cemetery map update | invariant | Update synchronizes GIS, paper map, section markers and sales records. | prevent location errors |
| cemeteryops.case.interment_request | Cemetery interment request | invariant | Request records decedent, family contact, plot, service date, disposition type and permits. | start case |
| cemeteryops.case.authorization_check | Interment authorization check | invariant | Check verifies legal authority, ownership rights, funeral director and required permissions. | lawful action |
| cemeteryops.case.permit_record | Cemetery burial permit record | invariant | Record captures burial, cremation, transit or disinterment permit as required. | compliance |
| cemeteryops.case.identity_chain | Cemetery identity chain | invariant | Chain links decedent identity, container, documents, location and staff handoffs. | avoid mismatch |
| cemeteryops.case.family_preferences | Cemetery family preferences | variant | Preferences capture service style, clergy, music, flowers, military honors or cultural needs. | respectful service |
| cemeteryops.schedule.interment_schedule | Cemetery interment schedule | invariant | Schedule coordinates date, grave opening, staff, funeral home, family and weather. | align work |
| cemeteryops.schedule.service_window | Cemetery service window | invariant | Window defines arrival, procession, committal, lowering, departure and closing time. | predictable flow |
| cemeteryops.schedule.conflict_check | Cemetery schedule conflict check | invariant | Check prevents overlapping services, road conflicts, staff shortage or equipment collision. | avoid disruption |
| cemeteryops.schedule.weather_delay | Cemetery weather delay | variant | Delay records unsafe ground, lightning, snow, heat or access issue and family notice. | safe reschedule |
| cemeteryops.grounds.grave_layout | Grave layout marking | invariant | Marking confirms plot corners, orientation, depth constraints and adjacent graves. | accurate opening |
| cemeteryops.grounds.open_close | Grave open and close workflow | invariant | Workflow manages excavation, shoring if needed, lowering, backfill, tamping and restoration. | dignified completion |
| cemeteryops.grounds.crypt_niche_prep | Crypt or niche preparation | variant | Preparation verifies space, nameplate, access, seal, equipment and documentation. | ready placement |
| cemeteryops.grounds.soil_condition | Cemetery soil condition | variant | Condition notes rock, water, collapse risk, frost, roots or equipment limits. | plan safe work |
| cemeteryops.grounds.turf_restoration | Cemetery turf restoration | invariant | Restoration repairs settlement, seed, sod, grading, mats and follow-up checks. | maintain grounds |
| cemeteryops.service.procession_route | Cemetery procession route | invariant | Route directs vehicles from gate to service area while protecting other visitors. | orderly arrival |
| cemeteryops.service.committal_setup | Committal service setup | invariant | Setup includes chairs, tent, lowering device, carpet, signage, flags and sound if used. | service readiness |
| cemeteryops.service.military_honors | Cemetery military honors coordination | variant | Coordination aligns honor guard, flag, timing, shelter and family expectations. | respectful tribute |
| cemeteryops.service.cultural_practice | Cemetery cultural practice accommodation | variant | Accommodation records ritual timing, orientation, participants, materials and site constraints. | respect customs |
| cemeteryops.service.visitor_support | Cemetery visitor support | invariant | Support gives directions, parking help, accessibility assistance and calm communication. | family care |
| cemeteryops.marker.marker_application | Cemetery marker application | invariant | Application records design, inscription, material, plot, rules, fees and approval. | authorize marker |
| cemeteryops.marker.inscription_review | Cemetery inscription review | invariant | Review checks spelling, dates, titles, emblems, language and rule compliance. | prevent costly errors |
| cemeteryops.marker.foundation_order | Marker foundation order | variant | Order schedules base size, location, concrete, curing and installer coordination. | stable marker |
| cemeteryops.marker.installation_check | Cemetery marker installation check | invariant | Check verifies location, level, alignment, inscription and damage after placement. | quality control |
| cemeteryops.marker.marker_repair | Cemetery marker repair | variant | Repair records tilt, breakage, cleaning, reset, owner approval and completion. | preserve memorial |
| cemeteryops.records.interment_register | Cemetery interment register | invariant | Register records decedent, location, date, authority, funeral home and case notes. | permanent record |
| cemeteryops.records.document_scan | Cemetery document scan | invariant | Scan stores permits, authorizations, deeds, contracts and service notes in case file. | retrievable file |
| cemeteryops.records.correction_request | Cemetery record correction request | invariant | Request fixes name, date, plot, ownership or inscription with evidence and approval. | reliable records |
| cemeteryops.records.public_lookup | Cemetery public lookup | variant | Lookup provides permitted grave location or genealogy information while protecting privacy. | visitor service |
| cemeteryops.compliance.disinterment_request | Cemetery disinterment request | variant | Request verifies legal order, authority, health rules, family notice and scheduling. | high-control action |
| cemeteryops.compliance.perpetual_care | Cemetery perpetual care record | invariant | Record tracks care fund, maintenance obligation, restricted funds and reporting. | long-term stewardship |
| cemeteryops.compliance.contract_review | Cemetery contract review | invariant | Review checks plot, service, marker, fees, disclosures, cancellations and signatures. | reduce disputes |
| cemeteryops.finance.fee_schedule | Cemetery fee schedule | invariant | Schedule lists plot, opening, closing, marker, transfer, overtime and admin fees. | consistent billing |
| cemeteryops.finance.payment_plan | Cemetery payment plan | variant | Plan records installments, due dates, rights limits, default and completion. | accessible purchase |
| cemeteryops.finance.refund_transfer | Cemetery refund or transfer | variant | Process handles cancellation, plot transfer, family change, fee offsets and approvals. | clean finance |
| cemeteryops.maintenance.mowing_route | Cemetery mowing route | invariant | Route schedules turf care while avoiding services, fragile markers and wet ground. | dignified grounds |
| cemeteryops.maintenance.road_path | Cemetery road and path maintenance | invariant | Maintenance tracks potholes, snow, ice, drainage, accessibility and signage. | visitor access |
| cemeteryops.maintenance.flower_policy | Cemetery flower policy | variant | Policy governs decorations, removal dates, safety, seasonal items and family notice. | orderly grounds |
| cemeteryops.incident.cemetery_incident | Cemetery incident report | invariant | Report captures injury, damage, vandalism, service disruption, conflict or trespass. | incident trail |
| cemeteryops.metrics.cemetery_kpi | Cemetery operations KPI | variant | KPI tracks interments, plot sales, marker approvals, complaints, maintenance and record corrections. | manage cemetery |
