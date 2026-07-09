# BATCH_299 — Community Garden Operations Detail
# world_skills_core · source: world_skills_core:batch_299:community_garden_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| gardenops.inventory.garden_record | Community garden record | invariant | Record stores site, plots, water, tools, compost, members, rules and maintenance history. | manage garden |
| gardenops.inventory.plot_map | Community garden plot map | invariant | Map identifies plot numbers, paths, accessible beds, common areas, water points and boundaries. | assign plots |
| gardenops.inventory.accessible_bed | Accessible garden bed | variant | Bed supports reachable height, path width, surface stability and nearby water access. | inclusive gardening |
| gardenops.membership.member_record | Community garden member record | invariant | Record stores gardener contact, plot assignment, agreement, fees, orientation and status. | manage membership |
| gardenops.membership.waitlist | Garden plot waitlist | invariant | Waitlist orders applicants by policy, date, priority, residency or special program. | fair assignment |
| gardenops.membership.orientation | Community garden orientation | invariant | Orientation explains rules, tools, water, compost, safety, harvest, communication and conflict process. | onboard members |
| gardenops.membership.plot_abandonment | Garden plot abandonment | variant | Abandonment occurs when plot is unused, weedy, unpaid or unresponsive after notice. | reassign space |
| gardenops.rules.garden_rules | Community garden rules | invariant | Rules define plot care, allowed plants, structures, chemicals, watering, guests and quiet hours. | reduce conflict |
| gardenops.rules.organic_policy | Garden organic practice policy | variant | Policy limits synthetic pesticides, herbicides, fertilizers or treated materials where required. | protect users |
| gardenops.rules.harvest_boundary | Garden harvest boundary | invariant | Boundary clarifies personal plots, communal crops, donation beds and unauthorized picking. | prevent disputes |
| gardenops.water.water_point | Garden water point | invariant | Point includes hose bib, hydrant, rain tank, meter, backflow control and access rules. | supply water |
| gardenops.water.hose_management | Garden hose management | variant | Management prevents leaks, trip hazards, cross-plot conflicts, broken fittings and wasted water. | keep safe |
| gardenops.water.irrigation_schedule | Community garden irrigation schedule | variant | Schedule balances water availability, drought rules, plot needs and shared infrastructure. | conserve water |
| gardenops.water.leak_response | Garden water leak response | invariant | Response shuts valve, reports fault, protects path and repairs hose, pipe or fitting. | stop waste |
| gardenops.tools.tool_inventory | Community garden tool inventory | invariant | Inventory tracks shovels, rakes, wheelbarrows, hoses, keys, locks and shared supplies. | manage tools |
| gardenops.tools.tool_checkout | Garden tool checkout | variant | Checkout records borrowed tools, member, date, return condition and missing items. | prevent loss |
| gardenops.tools.tool_safety | Garden tool safety | invariant | Safety covers storage, sharp edges, gloves, safe lifting, cleaning and damaged tools. | reduce injury |
| gardenops.compost.compost_area | Community garden compost area | invariant | Area receives allowed plant waste with rules for piles, bins, turning and contamination. | recycle organics |
| gardenops.compost.contamination | Garden compost contamination | invariant | Contamination includes plastic, meat, pet waste, diseased plants, invasive seeds or chemicals. | protect compost |
| gardenops.compost.finished_compost_distribution | Finished compost distribution | variant | Distribution shares cured compost by plots, communal beds, season or member rules. | use resource |
| gardenops.maintenance.path_maintenance | Garden path maintenance | invariant | Maintenance keeps paths level, drained, weeded, wide, accessible and free of trip hazards. | safe movement |
| gardenops.maintenance.fence_gate | Garden fence and gate maintenance | invariant | Maintenance checks locks, hinges, holes, posts, access codes, signage and security. | protect site |
| gardenops.maintenance.common_area | Garden common-area maintenance | variant | Maintenance covers shared beds, sheds, gathering areas, notice boards and compost zones. | shared care |
| gardenops.maintenance.seasonal_cleanup | Community garden seasonal cleanup | invariant | Cleanup removes debris, dead crops, abandoned materials, trash, weeds and unsafe structures. | reset season |
| gardenops.repairs.raised_bed_repair | Garden raised bed repair | invariant | Repair fixes rotted boards, loose corners, soil loss, sharp edges or unstable bed walls. | keep plots usable |
| gardenops.repairs.shed_repair | Garden shed repair | variant | Repair addresses roof leaks, locks, shelves, pests, tools, doors and weather damage. | protect supplies |
| gardenops.repairs.path_surface_repair | Garden path surface repair | variant | Repair adds mulch, gravel, pavers or grading to reduce mud, holes and accessibility barriers. | improve access |
| gardenops.events.workday | Community garden workday | invariant | Workday organizes member labor, tasks, tools, safety briefing and completion tracking. | maintain site |
| gardenops.events.education_event | Garden education event | variant | Event covers growing skills, compost, water conservation, seed saving or food preparation. | build skills |
| gardenops.events.seed_swap | Community garden seed swap | variant | Event exchanges seeds with labels, crop notes, local adaptation guidance and sharing rules. | share varieties |
| gardenops.events.harvest_donation | Garden harvest donation | variant | Donation manages communal harvest, food safety, weighing, recipients and records. | share food |
| gardenops.conflict.plot_boundary_dispute | Garden plot boundary dispute | invariant | Dispute involves encroachment, shade, harvest, paths, water, structures or member conduct. | resolve fairly |
| gardenops.conflict.rule_violation | Garden rule violation | invariant | Violation records behavior, evidence, notice, correction period and possible plot loss. | enforce rules |
| gardenops.conflict.mediation_process | Garden mediation process | variant | Process brings gardeners and coordinator together to clarify facts, rules and next actions. | reduce escalation |
| gardenops.safety.chemical_risk | Garden chemical risk | invariant | Risk includes unapproved pesticide, contaminated soil, fertilizer misuse or unsafe storage. | protect users |
| gardenops.safety.heat_work | Garden heat work safety | variant | Safety encourages water, shade, breaks and task timing during hot weather. | protect volunteers |
| gardenops.safety.soil_contamination_notice | Garden soil contamination notice | variant | Notice informs users about known soil limits, testing, raised beds or crop restrictions. | manage exposure |
| gardenops.records.plot_inspection | Garden plot inspection record | invariant | Record captures plot condition, weeds, structures, compliance, notices and photos. | track upkeep |
| gardenops.records.water_meter_log | Garden water meter log | variant | Log tracks water use, leaks, seasonal patterns, billing and conservation results. | manage costs |
| gardenops.reporting.membership_report | Community garden membership report | invariant | Report summarizes plots assigned, waitlist, vacancies, rule issues and participation. | manage program |
| gardenops.metrics.plot_utilization | Garden plot utilization KPI | invariant | KPI measures active plots versus total available plots by season. | improve access |
| gardenops.metrics.workday_participation | Garden workday participation KPI | variant | KPI tracks member participation in shared maintenance and events. | balance labor |
| gardenops.coordination.parks_department | Garden parks department coordination | variant | Coordination handles mowing, trash, water, repairs, capital work and site rules. | align support |
| gardenops.close.season_closeout | Community garden season closeout | invariant | Closeout confirms plots cleared, water winterized, tools stored, records updated and notices sent. | finish season |
