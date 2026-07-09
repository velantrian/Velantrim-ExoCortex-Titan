# BATCH_175 — Museum Exhibition Operations Detail
# world_skills_core · source: world_skills_core:batch_175:museum_exhibition_operations_detail
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| museumops.loan.loan_agreement | Object loan agreement | invariant | Loan agreement defines objects, term, lender, borrower, insurance, transport, display conditions and responsibilities. | правовая основа займа |
| museumops.loan.facility_report | Museum facility report | invariant | Facility report describes security, environment, fire protection, staffing and building conditions for lenders. | prove venue readiness |
| museumops.loan.condition_report | Object condition report | invariant | Condition report records current state, damage, materials, photos and handling notes before transfer or display. | baseline for accountability |
| museumops.loan.courier_requirement | Museum courier requirement | variant | Courier requirement sends lender representative to supervise packing, transport, install or deinstall. | high-value oversight |
| museumops.loan.insurance_certificate | Exhibition insurance certificate | invariant | Insurance certificate proves coverage, values, dates, locations and covered risks for loaned objects. | risk transfer evidence |
| museumops.loan.loan_extension | Loan extension | variant | Extension changes return date and must be documented before original loan term expires. | avoid unauthorized hold |
| museumops.registrar.accession_check | Accession check | invariant | Accession check confirms whether object is owned, loaned, promised, restricted or proposed for acquisition. | know custody status |
| museumops.registrar.object_number | Object number | invariant | Object number uniquely links artifact to catalog, location, images, rights and condition records. | identity for object |
| museumops.registrar.location_control | Object location control | invariant | Location control records exact object movement between storage, gallery, lab, crate and transit. | do not lose artifacts |
| museumops.registrar.rights_clearance | Exhibition rights clearance | invariant | Rights clearance confirms permission for images, text, audio, reproduction or digital display. | display is not always reuse |
| museumops.registrar.restriction_note | Cultural restriction note | variant | Restriction note records access, display, photography or handling limits tied to culture, donor or law. | respect constraints |
| museumops.registrar.deaccession_boundary | Exhibition deaccession boundary | invariant | Exhibition planning must not treat deaccessioned, restricted or disputed objects as ordinary display assets. | governance boundary |
| museumops.design.interpretive_plan | Interpretive plan | invariant | Interpretive plan defines exhibition story, audience, themes, learning goals and object selection logic. | meaning before layout |
| museumops.design.object_list | Exhibition object list | invariant | Object list tracks selected works, alternates, location, dimensions, mounts, media and status. | working inventory |
| museumops.design.gallery_layout | Gallery layout | invariant | Layout maps visitor flow, object placement, accessibility, sightlines, exits and case locations. | room as experience |
| museumops.design.label_copy | Museum label copy | invariant | Label copy gives concise object information, interpretation, credit and accessibility-aware language. | text at point of viewing |
| museumops.design.accessibility_review | Exhibition accessibility review | invariant | Review checks physical access, readable text, audio, captions, tactile elements and sensory considerations. | inclusive exhibition |
| museumops.design.mockup | Exhibition mockup | variant | Mockup tests case, mount, label, lighting or interactive layout before final fabrication. | catch issues early |
| museumops.install.mount_design | Object mount design | invariant | Mount design supports object safely while meeting conservation, visibility and seismic or vibration needs. | support without harm |
| museumops.install.crate_opening | Crate opening procedure | invariant | Crate opening follows acclimatization, documentation, witness and condition check requirements. | unpack carefully |
| museumops.install.art_handling | Art handling protocol | invariant | Handling protocol controls gloves, supports, team size, route, tools and stop conditions. | humans are biggest risk |
| museumops.install.case_sealing | Display case sealing | variant | Case sealing controls dust, pests, humidity buffering and access security for sensitive objects. | microenvironment |
| museumops.install.lighting_focus | Exhibition lighting focus | invariant | Lighting focus balances visibility, glare, heat, UV exposure and object sensitivity. | see without damaging |
| museumops.install.install_punchlist | Exhibition install punchlist | invariant | Punchlist tracks remaining fabrication, labels, cleaning, lighting, security and object issues before opening. | final readiness |
| museumops.environment.temperature_monitor | Gallery temperature monitor | invariant | Temperature monitoring verifies exhibition space remains within agreed object conditions. | climate evidence |
| museumops.environment.humidity_monitor | Gallery humidity monitor | invariant | Humidity monitoring protects objects sensitive to swelling, cracking, corrosion or mold. | moisture control |
| museumops.environment.light_dose | Light dose tracking | variant | Light dose tracks cumulative exposure for light-sensitive materials. | time under light matters |
| museumops.environment.pest_trap | Gallery pest trap | invariant | Pest traps detect insects that can damage organic materials or indicate housekeeping gaps. | early warning |
| museumops.environment.vibration_risk | Exhibition vibration risk | variant | Vibration risk from visitors, construction, transit or equipment can threaten fragile objects. | invisible movement |
| museumops.environment.emergency_cover | Emergency object cover | variant | Emergency covers or supplies protect objects from leaks, dust or urgent facility events. | rapid protection |
| museumops.security.gallery_guard_post | Gallery guard post | invariant | Guard post assigns position, sightline, patrol duty, visitor interaction and escalation path. | human protection layer |
| museumops.security.case_alarm | Display case alarm | invariant | Case alarm detects opening, vibration or tampering and routes alert to security response. | secure enclosure |
| museumops.security.key_control | Exhibition key control | invariant | Key control tracks access to cases, storage, crates and restricted areas. | physical access evidence |
| museumops.security.photography_policy | Photography policy | variant | Policy manages flash, tripods, restricted works, rights and visitor communication. | balance access and protection |
| museumops.security.after_hours_check | Gallery after-hours check | invariant | Check verifies objects, cases, alarms, environment and doors after visitors leave. | overnight confidence |
| museumops.security.incident_report | Museum incident report | invariant | Incident report records damage, theft, visitor issue, alarm, leak or policy breach. | evidence and response |
| museumops.public.opening_check | Exhibition opening check | invariant | Opening check confirms objects, labels, media, lights, interactives, barriers and visitor paths are ready. | daily readiness |
| museumops.public.visitor_flow | Museum visitor flow | invariant | Visitor flow management prevents crowding, blocked exits, object risk and poor experience. | people affect preservation |
| museumops.public.interactive_reset | Interactive exhibit reset | variant | Interactive reset restores screens, controls, supplies or mechanical elements for next visitors. | hands-on needs upkeep |
| museumops.public.docent_brief | Docent briefing | variant | Briefing aligns guides on themes, sensitive content, object restrictions and visitor questions. | interpretation consistency |
| museumops.close.deinstallation_plan | Deinstallation plan | invariant | Plan sequences object removal, condition checks, packing, crates, transport and gallery restoration. | safe ending |
| museumops.close.outgoing_condition | Outgoing condition report | invariant | Outgoing report compares object state after display with incoming condition. | accountability at return |
| museumops.close.exhibition_archive | Exhibition archive | invariant | Archive preserves object list, labels, design files, photos, contracts, reports and lessons. | institutional memory |
| museumops.close.post_exhibition_review | Post-exhibition review | variant | Review analyzes attendance, incidents, costs, conservation issues, feedback and operational lessons. | improve next show |
