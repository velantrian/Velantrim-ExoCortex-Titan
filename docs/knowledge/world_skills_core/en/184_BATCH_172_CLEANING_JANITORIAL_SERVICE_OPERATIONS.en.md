# BATCH_172 — Cleaning & Janitorial Service Operations Detail
# world_skills_core · source: world_skills_core:batch_172:cleaning_janitorial_service_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| cleanops.plan.area_schedule | Cleaning area schedule | invariant | Area schedule assigns spaces, tasks, frequency, time window and responsible team. | clean by plan |
| cleanops.plan.scope_of_work | Janitorial scope of work | invariant | Scope defines surfaces, rooms, tasks, exclusions, quality expectations and reporting duties. | avoid unclear cleaning |
| cleanops.plan.zone_map | Cleaning zone map | variant | Zone map divides facility into manageable routes based on risk, traffic, floor type and access. | route the work |
| cleanops.plan.high_touch_list | High-touch surface list | invariant | List identifies handles, switches, rails, counters, buttons and shared devices needing frequent attention. | focus on contact points |
| cleanops.plan.frequency_matrix | Cleaning frequency matrix | invariant | Matrix links task frequency to space type, traffic, risk and client requirement. | not every room daily deep clean |
| cleanops.plan.after_hours_access | After-hours access | variant | Access plan controls keys, alarms, escort rules, restricted rooms and sign-in for cleaning staff. | clean safely after close |
| cleanops.chemicals.sds_access | Safety data sheet access | invariant | SDS access ensures workers can review hazards, PPE, dilution and emergency actions for chemicals. | know the chemical |
| cleanops.chemicals.dilution_control | Chemical dilution control | invariant | Dilution control prevents too-weak, too-strong or incompatible cleaning solution. | chemistry must be measured |
| cleanops.chemicals.labeling | Secondary container labeling | invariant | Labeling identifies product, hazard and use when chemical is transferred from original container. | no mystery bottles |
| cleanops.chemicals.compatibility | Chemical compatibility | invariant | Compatibility rules prevent dangerous mixing such as acids with bleach or ammonia-containing products. | avoid toxic reactions |
| cleanops.chemicals.storage | Janitorial chemical storage | invariant | Storage separates incompatible chemicals, restricts access and prevents leaks or food-area contamination. | closet as safety zone |
| cleanops.chemicals.spill_response | Cleaning chemical spill response | invariant | Spill response isolates area, uses appropriate PPE, contains material and escalates if beyond staff capability. | small spill can harm |
| cleanops.tasks.restroom_clean | Restroom cleaning cycle | invariant | Cycle covers fixtures, floors, mirrors, consumables, odor, trash and touchpoints. | high-risk service area |
| cleanops.tasks.floor_mopping | Wet mopping | invariant | Mopping removes soil while controlling slip risk, water quality, mop condition and wet-floor signage. | clean without creating hazard |
| cleanops.tasks.vacuuming | Vacuuming task | invariant | Vacuuming removes dry soil from carpets with attention to edges, traffic lanes and cord safety. | carpet maintenance |
| cleanops.tasks.trash_removal | Trash removal | invariant | Trash workflow handles liners, segregation, leakage, weight, route and disposal location. | waste leaves safely |
| cleanops.tasks.dusting | Dusting task | variant | Dusting removes settled particles from surfaces without spreading contamination or damaging finishes. | visible quality |
| cleanops.tasks.glass_cleaning | Glass cleaning | variant | Glass cleaning controls streaks, fingerprints, product residue and ladder or edge safety. | transparent surfaces show defects |
| cleanops.equipment.cart_setup | Janitorial cart setup | invariant | Cart setup stocks tools, chemicals, PPE, liners, cloths and forms for route completion. | mobile workstation |
| cleanops.equipment.color_coding | Cleaning color coding | variant | Color coding separates cloths, mops or tools by area or contamination risk. | prevent cross-use |
| cleanops.equipment.autoscrubber | Autoscrubber operation | variant | Autoscrubber work requires correct pad, solution, squeegee, battery, route and recovery tank handling. | machine cleaning |
| cleanops.equipment.vacuum_filter | Vacuum filter maintenance | invariant | Filter maintenance preserves suction, dust control and machine life. | equipment quality |
| cleanops.equipment.mop_laundering | Mop and cloth laundering | invariant | Laundering or replacement prevents tools from spreading odor, soil or microbes. | dirty tools cannot clean |
| cleanops.equipment.locked_storage | Equipment locked storage | invariant | Locked storage prevents misuse, theft, chemical access and obstruction of public areas. | control assets |
| cleanops.quality.inspection_checklist | Cleaning inspection checklist | invariant | Checklist verifies task completion, visible quality, supplies, odors, damage and safety issues. | inspect against standard |
| cleanops.quality.deficiency_tag | Cleaning deficiency tag | invariant | Deficiency tag records missed task, location, severity, photo, owner and correction status. | issue becomes action |
| cleanops.quality.complaint_log | Janitorial complaint log | invariant | Complaint log captures client or occupant issue, time, location, response and trend. | feedback loop |
| cleanops.quality.atp_swab | ATP swab | variant | ATP swab gives rapid indicator of organic residue on selected surfaces but does not identify pathogens. | verification tool |
| cleanops.quality.before_after_photo | Before-after photo | variant | Photo evidence can document special cleans, damage, access issues or complaint closure. | visual proof |
| cleanops.quality.service_level_review | Cleaning service level review | invariant | Review compares performance, complaints, inspections, staffing and scope against contract. | manage service |
| cleanops.safety.slip_trip | Slip and trip control | invariant | Control includes signs, dry routes, cord management, prompt spill response and clutter reduction. | do not create accidents |
| cleanops.safety.ppe_selection | Janitorial PPE selection | invariant | PPE matches task hazards such as chemicals, sharps, dust, bodily fluids or noise. | not one glove for all |
| cleanops.safety.sharps_found | Sharps found procedure | invariant | Procedure avoids hand pickup, uses tools or approved container and reports location. | protect cleaners |
| cleanops.safety.blood_bodily_fluid | Bodily fluid cleanup | invariant | Cleanup uses trained staff, correct PPE, containment, disinfectant and disposal path. | high-risk task |
| cleanops.safety.ladder_use | Cleaning ladder use | variant | Ladder use requires correct height, condition, surface, positioning and no overreach. | avoid fall |
| cleanops.safety.lone_worker | Janitorial lone worker check | variant | Lone worker process provides check-ins, emergency contact and access control for isolated shifts. | night work safety |
| cleanops.staffing.route_time | Cleaning route time | invariant | Route time estimates labor needed for tasks, travel, setup, restocking and interruptions. | realistic staffing |
| cleanops.staffing.task_training | Task training record | invariant | Training record confirms worker understands methods, chemicals, equipment and safety requirements. | competence evidence |
| cleanops.staffing.substitution_plan | Cleaner substitution plan | variant | Substitution plan covers absence without losing critical tasks or access knowledge. | continuity of service |
| cleanops.staffing.productivity_rate | Cleaning productivity rate | variant | Rate estimates area or fixtures cleaned per hour but must account for soil, traffic and scope. | compare with context |
| cleanops.special.deep_clean | Deep cleaning project | variant | Deep clean addresses accumulated soil, vents, carpets, high surfaces, grout or periodic detail tasks. | beyond routine |
| cleanops.special.post_construction_clean | Post-construction clean | variant | Post-construction cleaning removes dust, debris, labels, residues and fine particles before occupancy. | handover readiness |
| cleanops.special.event_clean | Event cleaning | variant | Event clean handles pre-event, during-event and post-event waste, restrooms, spills and high traffic. | cleaning follows crowd |
| cleanops.records.cleaning_log | Cleaning log | invariant | Log records task completion, time, worker, area, exceptions and corrective notes. | proof of service |
