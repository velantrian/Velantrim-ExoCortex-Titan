# BATCH_294 — Pedestrian Wayfinding Operations Detail
# world_skills_core · source: world_skills_core:batch_294:pedestrian_wayfinding_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| wayfindops.inventory.sign_record | Pedestrian wayfinding sign record | invariant | Record stores sign ID, type, location, destinations, arrows, maps, owner and condition. | manage signs |
| wayfindops.inventory.destination_list | Wayfinding destination list | invariant | List defines approved landmarks, districts, transit nodes, parks, civic buildings and routes. | standardize content |
| wayfindops.inventory.map_panel | Pedestrian map panel | variant | Panel displays area map, walking times, landmarks, north arrow and accessible routes. | orient users |
| wayfindops.inventory.kiosk_record | Wayfinding kiosk record | variant | Record captures kiosk structure, lighting, digital screen, power, network and content version. | maintain kiosk |
| wayfindops.placement.decision_point | Pedestrian wayfinding decision point | invariant | Point is location where users choose direction, route, crossing or destination. | place signs |
| wayfindops.placement.sightline | Wayfinding sightline | invariant | Sightline ensures sign is visible from approach without obstruction or visual clutter. | improve legibility |
| wayfindops.placement.walking_distance | Wayfinding walking distance | variant | Distance text estimates pedestrian travel based on route, barriers, slopes and crossings. | set expectation |
| wayfindops.placement.accessible_route_indicator | Accessible route indicator | variant | Indicator directs users toward step-free, ramped or barrier-free pedestrian paths. | inclusive navigation |
| wayfindops.content.destination_hierarchy | Wayfinding destination hierarchy | invariant | Hierarchy ranks destinations by civic importance, distance, visitor need and sign capacity. | choose content |
| wayfindops.content.arrow_consistency | Wayfinding arrow consistency | invariant | Consistency keeps arrows, directions and destinations coherent across consecutive signs. | avoid confusion |
| wayfindops.content.naming_standard | Wayfinding naming standard | invariant | Standard controls official names, abbreviations, translations, icons and district labels. | clear messages |
| wayfindops.content.multilingual_panel | Multilingual wayfinding panel | variant | Panel includes additional languages where visitor, community or transit needs justify it. | improve access |
| wayfindops.maps.base_map_update | Wayfinding base map update | invariant | Update revises streets, paths, landmarks, transit stops, closures and public spaces. | keep current |
| wayfindops.maps.you_are_here | You-are-here marker | invariant | Marker shows exact map position and orientation relative to the viewer. | orient quickly |
| wayfindops.maps.walk_time_ring | Walking-time ring | variant | Ring shows destinations reachable within approximate walking time from panel location. | plan route |
| wayfindops.maps.landmark_icon | Wayfinding landmark icon | variant | Icon represents transit, toilets, parks, civic sites, hospitals or attractions. | scan map |
| wayfindops.maintenance.cleaning | Wayfinding sign cleaning | invariant | Cleaning removes dirt, stickers, graffiti, bird droppings and residues from panels. | keep readable |
| wayfindops.maintenance.panel_replacement | Wayfinding panel replacement | invariant | Replacement updates damaged, faded, outdated or incorrect sign face or map panel. | restore content |
| wayfindops.maintenance.post_repair | Wayfinding post repair | invariant | Repair fixes leaning, corroded, loose, damaged or unsafe sign supports. | stabilize sign |
| wayfindops.maintenance.digital_screen_reboot | Digital wayfinding screen reboot | variant | Reboot addresses frozen display, stale content, network fault or software issue. | restore display |
| wayfindops.condition.faded_panel | Faded wayfinding panel | invariant | Fading reduces map contrast, text legibility, color coding and professional appearance. | schedule replacement |
| wayfindops.condition.graffiti_damage | Wayfinding graffiti damage | invariant | Damage obscures text, maps, icons or arrows and may require cleaning or panel replacement. | restore readability |
| wayfindops.condition.outdated_destination | Outdated wayfinding destination | invariant | Destination becomes wrong after facility move, route closure, name change or redevelopment. | update content |
| wayfindops.condition.obstructed_sign | Obstructed wayfinding sign | variant | Obstruction includes trees, banners, vendors, construction, parked vehicles or other signs. | clear view |
| wayfindops.accessibility.text_legibility | Wayfinding text legibility | invariant | Legibility depends on font, size, contrast, height, lighting, spacing and viewing distance. | readable signs |
| wayfindops.accessibility.tactile_element | Tactile wayfinding element | variant | Element may include raised text, braille, tactile map or accessible route marker. | assist users |
| wayfindops.accessibility.mounting_height | Wayfinding mounting height | invariant | Height must balance readability, obstruction clearance, accessibility and vandalism resistance. | install correctly |
| wayfindops.audit.route_walkthrough | Wayfinding route walkthrough | invariant | Walkthrough follows destinations to check sign continuity, arrows, missing decisions and user confusion. | validate system |
| wayfindops.audit.content_audit | Wayfinding content audit | invariant | Audit reviews maps, names, distances, icons, translations, dates and destination hierarchy. | maintain accuracy |
| wayfindops.audit.inventory_reconciliation | Wayfinding inventory reconciliation | variant | Reconciliation compares field signs, GIS records, vendor files and maintenance tickets. | clean data |
| wayfindops.complaints.confusing_direction | Confusing wayfinding direction complaint | invariant | Complaint reports unclear arrow, missing sign, wrong destination, map mismatch or route ambiguity. | improve system |
| wayfindops.complaints.missing_destination | Missing wayfinding destination request | variant | Request asks to add civic, cultural, transit, park or district destination. | review content |
| wayfindops.complaints.damaged_sign | Damaged wayfinding sign complaint | invariant | Complaint records broken panel, leaning post, graffiti, lighting fault or missing sign. | dispatch repair |
| wayfindops.records.content_version | Wayfinding content version record | invariant | Record identifies map files, destination lists, approval date, vendor proof and install batch. | trace changes |
| wayfindops.records.install_photo | Wayfinding install photo | invariant | Photo documents placement, orientation, context, panel content and final condition. | verify install |
| wayfindops.records.approval_log | Wayfinding approval log | variant | Log stores stakeholder review, traffic approval, accessibility check and brand approval. | govern edits |
| wayfindops.reporting.condition_report | Wayfinding condition report | invariant | Report summarizes sign condition, cleaning needs, outdated content, damage and missing assets. | plan work |
| wayfindops.reporting.update_program_report | Wayfinding update program report | variant | Report tracks map refreshes, new destinations, panel replacements, costs and schedule. | manage program |
| wayfindops.metrics.legibility_pass_rate | Wayfinding legibility pass rate KPI | invariant | KPI measures share of signs passing readability, condition and obstruction checks. | monitor quality |
| wayfindops.metrics.complaint_resolution_time | Wayfinding complaint resolution time KPI | variant | KPI measures time from report to repair, content correction or explanation. | improve service |
| wayfindops.coordination.tourism_link | Wayfinding tourism coordination | variant | Coordination aligns destinations, maps, events, visitor routes and branding with tourism office. | serve visitors |
| wayfindops.coordination.transit_link | Wayfinding transit coordination | variant | Coordination aligns walking routes with stations, stops, fares, exits and service changes. | connect modes |
| wayfindops.continuity.temporary_wayfinding | Temporary pedestrian wayfinding | variant | Temporary signs guide users around construction, events, closures or station changes. | maintain navigation |
| wayfindops.close.work_closeout | Wayfinding work closeout | invariant | Closeout confirms installation, cleaning or update, photos, GIS, content record and complaint status. | finish work |
