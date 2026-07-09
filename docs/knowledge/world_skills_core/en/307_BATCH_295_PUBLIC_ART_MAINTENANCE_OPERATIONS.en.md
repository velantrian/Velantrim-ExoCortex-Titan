# BATCH_295 — Public Art Maintenance Operations Detail
# world_skills_core · source: world_skills_core:batch_295:public_art_maintenance_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| publicartops.inventory.artwork_record | Public art artwork record | invariant | Record stores title, artist, location, material, owner, date, dimensions and maintenance history. | manage artwork |
| publicartops.inventory.artist_agreement | Public art artist agreement record | invariant | Agreement defines rights, maintenance duties, reproduction limits, relocation rules and contact path. | respect rights |
| publicartops.inventory.material_profile | Public art material profile | invariant | Profile describes metal, stone, ceramic, glass, paint, wood, digital or mixed materials. | choose care |
| publicartops.inventory.site_context | Public art site context | variant | Context records exposure, landscaping, lighting, traffic, drainage, public access and security. | understand risk |
| publicartops.inventory.plaque_record | Public art plaque record | variant | Record captures title plaque, donor text, artist credit, material, condition and readability. | maintain context |
| publicartops.condition.condition_assessment | Public art condition assessment | invariant | Assessment reviews surface, structure, coating, attachment, corrosion, cracks, biological growth and vandalism. | find needs |
| publicartops.condition.surface_soiling | Public art surface soiling | invariant | Soiling includes dust, soot, bird droppings, minerals, pollution film and biological deposits. | plan cleaning |
| publicartops.condition.coating_failure | Public art coating failure | variant | Failure includes peeling, chalking, blistering, fading, cracking or loss of protective layer. | restore protection |
| publicartops.condition.structural_movement | Public art structural movement | invariant | Movement includes leaning, loose base, shifted anchor, crack growth or unstable component. | protect public |
| publicartops.condition.water_damage | Public art water damage | variant | Damage comes from ponding, leaks, irrigation overspray, freeze-thaw or poor drainage. | prevent decay |
| publicartops.cleaning.routine_cleaning | Public art routine cleaning | invariant | Cleaning removes light soil with approved tools, water, detergent and surface limits. | preserve artwork |
| publicartops.cleaning.graffiti_removal | Public art graffiti removal | invariant | Removal uses compatible methods to clear paint, marker or adhesive without damaging original surface. | recover appearance |
| publicartops.cleaning.bird_deterrent | Public art bird deterrent | variant | Deterrent reduces droppings through humane design, spikes, wires or site management. | reduce soiling |
| publicartops.cleaning.biogrowth_removal | Public art biological growth removal | variant | Removal treats algae, moss, lichen or mold using conservation-safe methods. | slow deterioration |
| publicartops.conservation.conservation_review | Public art conservation review | invariant | Review determines whether work requires conservator, artist input, engineer or routine maintenance. | choose expertise |
| publicartops.conservation.treatment_plan | Public art treatment plan | invariant | Plan specifies methods, materials, tests, sequence, risks, approvals and documentation. | guide work |
| publicartops.conservation.mockup_test | Public art cleaning mockup test | variant | Test applies proposed method in small area to verify effect before full treatment. | avoid damage |
| publicartops.conservation.patina_preservation | Public art patina preservation | variant | Preservation distinguishes intended aging from harmful corrosion or staining. | protect intent |
| publicartops.vandalism.vandalism_report | Public art vandalism report | invariant | Report captures damage type, photos, police referral, artist notice and repair decision. | document incident |
| publicartops.vandalism.tagging_hotspot | Public art tagging hotspot | variant | Hotspot indicates repeated graffiti requiring lighting, patrol, coating or site intervention. | prevent recurrence |
| publicartops.vandalism.physical_damage | Public art physical damage | invariant | Damage includes dents, scratches, broken parts, missing pieces, burns or impact marks. | prioritize repair |
| publicartops.lighting.artwork_lighting | Public art lighting record | invariant | Record tracks fixtures, aiming, timers, power, condition, glare and lighting intent. | maintain display |
| publicartops.lighting.lighting_fault | Public art lighting fault | invariant | Fault includes dark fixture, flicker, water ingress, wiring issue, timer error or vandalism. | repair lights |
| publicartops.lighting.glare_shadow_review | Public art glare and shadow review | variant | Review checks visual quality, safety, nearby windows, driver distraction and nighttime legibility. | tune lighting |
| publicartops.safety.public_contact_risk | Public art public contact risk | invariant | Risk covers climbing, sharp edges, pinch points, heat, electrical exposure or unstable parts. | protect visitors |
| publicartops.safety.temporary_barrier | Public art temporary barrier | variant | Barrier isolates damaged artwork during repair, investigation or unsafe condition. | control hazard |
| publicartops.safety.engineering_review | Public art engineering review | variant | Review checks foundation, anchors, wind, load, corrosion or structural safety. | verify stability |
| publicartops.records.condition_photo | Public art condition photo | invariant | Photo documents each side, detail damage, site context, repair stages and final condition. | evidence |
| publicartops.records.treatment_record | Public art treatment record | invariant | Record stores methods, products, staff, tests, approvals, dates, cost and observed results. | preserve history |
| publicartops.records.artist_contact_log | Public art artist contact log | variant | Log records artist consultation, approvals, concerns, unavailable contacts or estate communication. | respect intent |
| publicartops.coordination.artist_coordination | Public art artist coordination | invariant | Coordination seeks artist input for repair, repainting, relocation, interpretation or alteration. | protect meaning |
| publicartops.coordination.conservator_contract | Public art conservator contract | variant | Contract defines scope, qualifications, treatment limits, documentation and deliverables. | expert care |
| publicartops.coordination.public_works_link | Public art public works coordination | variant | Coordination avoids damage during paving, utility work, cleaning, landscaping or events. | prevent conflicts |
| publicartops.repairs.minor_repair | Public art minor repair | invariant | Repair fixes small scratches, loose fasteners, sealant, paint touchups or component alignment. | keep stable |
| publicartops.repairs.major_repair | Public art major repair | variant | Repair involves structural, material, conservation or artist-approved intervention beyond routine care. | restore artwork |
| publicartops.repairs.relocation_support | Public art relocation support | variant | Support handles removal, packing, transport, foundation, artist rights and reinstallation. | move safely |
| publicartops.reporting.collection_condition_report | Public art collection condition report | invariant | Report summarizes condition, risks, maintenance needs, conservation priorities and budget. | plan program |
| publicartops.reporting.vandalism_summary | Public art vandalism summary | variant | Summary tracks incidents, hotspots, costs, cleaning time and prevention measures. | reduce damage |
| publicartops.metrics.maintenance_cycle | Public art maintenance cycle KPI | invariant | KPI measures interval between inspections, cleanings and priority treatments by artwork. | schedule care |
| publicartops.metrics.condition_score | Public art condition score KPI | variant | Score rates artwork condition, safety, appearance, conservation need and site risk. | prioritize funding |
| publicartops.access.public_notice | Public art maintenance public notice | variant | Notice explains temporary closure, conservation work, relocation or cleaning activity. | inform visitors |
| publicartops.continuity.emergency_stabilization | Public art emergency stabilization | invariant | Stabilization secures unstable, damaged, vandalized or weather-threatened artwork until treatment. | prevent loss |
| publicartops.close.work_closeout | Public art work closeout | invariant | Closeout confirms treatment, photos, records, artist notice, invoice and updated condition. | finish work |
| publicartops.audit.inventory_reconciliation | Public art inventory reconciliation | variant | Reconciliation compares field artwork, records, artist files, plaques and GIS locations. | clean database |
