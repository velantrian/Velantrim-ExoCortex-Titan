# BATCH_291 — Street Furniture Maintenance Operations Detail
# world_skills_core · source: world_skills_core:batch_291:street_furniture_maintenance_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| streetfurnops.inventory.asset_record | Street furniture asset record | invariant | Record stores asset ID, type, location, owner, condition, install date and maintenance history. | manage asset |
| streetfurnops.inventory.bench_record | Public bench record | invariant | Record captures bench material, mounting, accessibility, nearby stop or plaza and condition. | maintain seating |
| streetfurnops.inventory.bin_record | Public litter bin record | invariant | Record stores bin type, capacity, liner, service frequency, condition and location. | manage waste |
| streetfurnops.inventory.bollard_record | Bollard record | variant | Record captures fixed, removable, flexible or decorative bollard location, purpose and condition. | protect space |
| streetfurnops.inventory.bike_rack_record | Bike rack record | variant | Record stores rack type, capacity, mounting, spacing, condition and demand context. | support parking |
| streetfurnops.inventory.shelter_record | Street furniture shelter record | variant | Record captures small shelter, canopy, frame, panels, seating relation, lighting and condition. | maintain shelter |
| streetfurnops.inspection.routine_check | Street furniture routine check | invariant | Check reviews damage, cleanliness, stability, placement, accessibility and safety hazards. | find defects |
| streetfurnops.inspection.post_event_check | Post-event furniture check | variant | Check looks for moved barriers, damaged bins, broken benches, litter and missing assets. | restore area |
| streetfurnops.inspection.post_storm_check | Post-storm furniture check | variant | Check reviews fallen branches, flooding, wind damage, loose fixtures and blocked paths. | recover safety |
| streetfurnops.damage.vandalism | Street furniture vandalism | invariant | Vandalism includes graffiti, broken parts, fire damage, removed bolts or deliberate misuse. | repair damage |
| streetfurnops.damage.vehicle_strike | Vehicle strike damage | invariant | Damage occurs when vehicle hits bench, bollard, bin, rack, planter or shelter element. | protect public |
| streetfurnops.damage.corrosion | Street furniture corrosion | variant | Corrosion weakens metal frames, fasteners, mounts and exposed surfaces. | plan renewal |
| streetfurnops.damage.loose_mount | Loose furniture mount | invariant | Loose mount creates wobble, trip hazard, theft risk or impact hazard. | secure asset |
| streetfurnops.cleaning.graffiti_removal | Street furniture graffiti removal | invariant | Removal cleans paint, marker, stickers or etching using approved method and surface protection. | restore appearance |
| streetfurnops.cleaning.pressure_washing | Street furniture pressure washing | variant | Washing removes grime, spills, stains and odor while avoiding damage to finishes. | deep clean |
| streetfurnops.cleaning.sticker_removal | Sticker removal | variant | Removal clears unauthorized posters, stickers and adhesive residue from public assets. | keep legible |
| streetfurnops.cleaning.bin_sanitation | Public bin sanitation | invariant | Sanitation cleans bin interior, exterior, odor sources, leaks and pest attractants. | improve hygiene |
| streetfurnops.repairs.bench_repair | Public bench repair | invariant | Repair fixes slats, frame, anchors, armrests, finish, sharp edges and stability. | restore seating |
| streetfurnops.repairs.bin_repair | Public bin repair | invariant | Repair fixes lid, liner, door, mount, corrosion, fire damage or capacity issue. | restore waste point |
| streetfurnops.repairs.bollard_replacement | Bollard replacement | invariant | Replacement restores protection, spacing, visibility, foundation and removable hardware if needed. | restore barrier |
| streetfurnops.repairs.bike_rack_repair | Bike rack repair | variant | Repair addresses bent rack, loose bolts, corrosion, spacing conflict or missing part. | secure bikes |
| streetfurnops.stock.spare_parts | Street furniture spare parts | invariant | Stock includes slats, bolts, locks, liners, lids, reflectors, brackets and finish materials. | repair readiness |
| streetfurnops.stock.standard_models | Street furniture standard models | variant | Standards define approved bench, bin, rack, bollard, planter and replacement parts. | maintain consistency |
| streetfurnops.placement.access_clearance | Street furniture access clearance | invariant | Clearance preserves sidewalk width, curb ramps, doors, tactile paths and emergency access. | avoid obstruction |
| streetfurnops.placement.sightline_conflict | Street furniture sightline conflict | variant | Conflict occurs when asset blocks crossings, signs, driveways or intersection visibility. | protect users |
| streetfurnops.placement.anchoring_requirement | Street furniture anchoring requirement | invariant | Anchoring prevents tipping, theft, movement, wind displacement and vehicle impact movement. | secure asset |
| streetfurnops.complaints.damaged_asset_report | Damaged furniture report | invariant | Report records asset type, location, damage, safety risk, photo and priority. | start work |
| streetfurnops.complaints.cleanliness_complaint | Furniture cleanliness complaint | variant | Complaint covers dirty bench, overflowing bin, odor, spills, sticky surfaces or pests. | dispatch service |
| streetfurnops.complaints.access_obstruction | Furniture access obstruction complaint | variant | Complaint notes asset blocking sidewalk, wheelchair route, curb ramp, door or bike lane. | restore access |
| streetfurnops.safety.sharp_edge | Street furniture sharp edge | invariant | Sharp edge can come from broken metal, splintered wood, cracked plastic or vandalism. | make safe |
| streetfurnops.safety.trip_hazard | Street furniture trip hazard | invariant | Hazard includes loose base, protruding bolt, displaced rack, raised plate or broken paving. | prevent falls |
| streetfurnops.safety.fire_damage | Street furniture fire damage | variant | Fire damage affects bins, benches, shelters, planters and nearby surfaces. | assess safety |
| streetfurnops.contracts.adopted_asset | Adopted street furniture asset | variant | Adopted asset has partner, sponsor or business maintenance responsibilities and reporting rules. | clarify owner |
| streetfurnops.contracts.cleaning_vendor | Street furniture cleaning vendor | variant | Vendor scope defines routes, frequency, standards, supplies, documentation and issue escalation. | manage service |
| streetfurnops.data.gis_update | Street furniture GIS update | invariant | Update corrects asset location, type, status, ownership, condition or removal. | keep map |
| streetfurnops.data.photo_evidence | Street furniture photo evidence | invariant | Photos document damage, location, repair, cleaning and final condition. | support records |
| streetfurnops.reporting.condition_report | Street furniture condition report | invariant | Report summarizes assets by type, condition, defects, repairs, removals and backlog. | plan renewal |
| streetfurnops.reporting.service_frequency_report | Street furniture service frequency report | variant | Report compares cleaning or waste service frequency with demand, complaints and overflow. | adjust service |
| streetfurnops.metrics.repair_cycle_time | Street furniture repair cycle time KPI | invariant | KPI measures time from report to make-safe and permanent repair. | improve response |
| streetfurnops.metrics.asset_uptime | Street furniture asset uptime KPI | variant | KPI tracks share of assets usable, clean, stable and not closed for repair. | monitor quality |
| streetfurnops.coordination.sanitation_link | Street furniture sanitation coordination | variant | Coordination aligns bins, sweeping, litter crews and event cleanup needs. | reduce litter |
| streetfurnops.coordination.transport_link | Street furniture transport coordination | variant | Coordination handles furniture near stops, curb zones, bike lanes and traffic control. | avoid conflict |
| streetfurnops.continuity.temporary_removal | Temporary street furniture removal | variant | Removal supports construction, events, security, repair or seasonal operations with tracking. | protect assets |
| streetfurnops.close.work_closeout | Street furniture work closeout | invariant | Closeout confirms repair or cleaning, photos, inventory update, complaint response and cost. | finish work |
