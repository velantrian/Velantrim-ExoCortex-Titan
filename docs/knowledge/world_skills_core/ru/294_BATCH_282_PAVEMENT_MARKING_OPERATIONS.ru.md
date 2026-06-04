# BATCH_282 — Pavement Marking Operations Detail
# world_skills_core · source: world_skills_core:batch_282:pavement_marking_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| markops.inventory.marking_record | Pavement marking record | invariant | Record stores marking type, location, material, color, date, condition and responsible owner. | manage markings |
| markops.inventory.centerline_inventory | Centerline marking inventory | invariant | Inventory tracks yellow lines, passing zones, no-passing zones, double lines and gaps. | guide traffic |
| markops.inventory.crosswalk_inventory | Crosswalk marking inventory | invariant | Inventory stores crosswalk type, school status, signal relation, width, material and condition. | pedestrian safety |
| markops.inventory.legend_symbol_inventory | Pavement legend and symbol inventory | variant | Inventory covers arrows, bike symbols, words, lane-use markings and bus markings. | plan refresh |
| markops.layout.marking_layout_plan | Pavement marking layout plan | invariant | Plan defines geometry, offsets, line widths, tapers, symbols, stationing and references. | install correctly |
| markops.layout.field_layout | Field marking layout | invariant | Layout uses measurements, control points, chalk, string, templates or GPS guidance before application. | avoid errors |
| markops.layout.as_built_marking_update | Marking as-built update | variant | Update records final location, deviations, quantities and field changes after installation. | keep records |
| markops.materials.traffic_paint | Traffic paint | invariant | Paint is lower-cost marking material used where durability requirements are moderate. | choose material |
| markops.materials.thermoplastic_marking | Thermoplastic pavement marking | invariant | Thermoplastic is heated material with beads that provides durable retroreflective markings. | durable lines |
| markops.materials.epoxy_marking | Epoxy pavement marking | variant | Epoxy provides durable adhesion and retroreflectivity for high-volume or harsh conditions. | long life |
| markops.materials.preformed_tape | Preformed marking tape | variant | Tape offers precise symbols, temporary markings or durable inlaid markings on suitable surfaces. | quick install |
| markops.materials.glass_beads | Pavement marking glass beads | invariant | Beads embedded in material return headlight light and create nighttime visibility. | retroreflectivity |
| markops.condition.faded_line | Faded pavement line | invariant | Fade reduces contrast and driver guidance because of wear, weather, plowing or age. | refresh needed |
| markops.condition.missing_marking | Missing pavement marking | invariant | Missing marking removes lane guidance, stop control, crosswalk visibility or symbol information. | safety risk |
| markops.condition.worn_crosswalk | Worn crosswalk marking | invariant | Wear reduces pedestrian crossing visibility and may require priority refresh. | protect pedestrians |
| markops.condition.snowplow_damage | Snowplow marking damage | variant | Damage scrapes or removes markings, raised markers and tapes during winter maintenance. | seasonal repair |
| markops.retroreflectivity.retro_test | Pavement marking retroreflectivity test | invariant | Test measures nighttime visibility using calibrated instrument, location and marking type. | verify visibility |
| markops.retroreflectivity.minimum_threshold | Marking retroreflectivity threshold | invariant | Threshold defines minimum reading or management method before replacement or refresh. | decide work |
| markops.retroreflectivity.night_review | Pavement marking night review | variant | Review checks line visibility, bead performance, contrast, wet visibility and confusing gaps. | improve guidance |
| markops.workzones.traffic_control_plan | Marking work traffic control plan | invariant | Plan protects striping crew with shadow vehicles, cones, signs, lane closures and buffers. | worker safety |
| markops.workzones.mobile_operation | Mobile striping operation | invariant | Operation moves along road with striping truck, attenuator, warning signs and support vehicles. | efficient marking |
| markops.workzones.dry_time_protection | Marking dry-time protection | variant | Protection keeps traffic off fresh paint or material until tracking risk is acceptable. | prevent smears |
| markops.workzones.night_marking_work | Night pavement marking work | variant | Work uses lighting, visibility controls and traffic management to reduce daytime disruption. | safer scheduling |
| markops.refresh.annual_refresh_program | Annual marking refresh program | invariant | Program prioritizes markings by condition, road class, safety, schools, bike lanes and budget. | plan repainting |
| markops.refresh.crosswalk_priority | Crosswalk refresh priority | variant | Priority ranks crossings near schools, transit, crashes, high pedestrian demand or faded markings. | focus safety |
| markops.refresh.bike_marking_refresh | Bike lane marking refresh | variant | Refresh restores bike symbols, buffers, green areas and conflict markings. | support cyclists |
| markops.refresh.post_paving_marking | Post-paving marking restoration | invariant | Restoration replaces lines and symbols after resurfacing, milling, patching or utility work. | reopen safely |
| markops.quality.line_width_check | Pavement marking line width check | invariant | Check confirms installed line width matches standard and plan. | quality control |
| markops.quality.alignment_check | Pavement marking alignment check | invariant | Check verifies line straightness, curves, tapers, offsets and relation to lane geometry. | avoid confusion |
| markops.quality.bead_drop_check | Glass bead drop check | variant | Check verifies bead application rate, embedment and distribution for visibility. | ensure reflectivity |
| markops.quality.material_thickness_check | Marking material thickness check | variant | Check measures wet film, dry film, thermoplastic thickness or tape placement. | durability |
| markops.equipment.striper_calibration | Striping truck calibration | invariant | Calibration verifies paint flow, bead rate, line width, skip pattern and control timing. | accurate install |
| markops.equipment.template_condition | Pavement symbol template condition | variant | Condition affects symbol clarity, dimensions, overspray and repeatability. | clean symbols |
| markops.equipment.material_heater | Thermoplastic material heater | variant | Heater maintains safe application temperature and material consistency. | proper bonding |
| markops.safety.crew_exposure | Pavement marking crew exposure | invariant | Exposure arises from moving traffic, night work, chemicals, heat, noise and visibility limits. | protect crew |
| markops.safety.chemical_handling | Marking material chemical handling | invariant | Handling covers solvents, paints, epoxies, thermoplastic heat, ventilation, PPE and spills. | worker safety |
| markops.safety.shadow_vehicle | Striping shadow vehicle | invariant | Vehicle shields mobile crew and may carry attenuator, warning board and communication equipment. | crash protection |
| markops.reporting.quantity_report | Pavement marking quantity report | invariant | Report totals linear feet, symbols, crosswalks, material used, crew hours and locations. | track production |
| markops.reporting.defect_report | Pavement marking defect report | variant | Report records smears, wrong layout, poor adhesion, missing beads, early wear or complaints. | correct quality |
| markops.metrics.marking_backlog | Pavement marking backlog KPI | invariant | KPI counts markings needing refresh or installation by safety priority and age. | manage workload |
| markops.metrics.retro_pass_rate | Pavement marking retroreflectivity pass rate KPI | variant | KPI measures share of tested markings meeting visibility threshold. | evaluate program |
| markops.coordination.signal_project_link | Marking coordination with signal project | variant | Coordination aligns stop bars, crosswalks, lane arrows and detectors with signal changes. | avoid mismatch |
| markops.coordination.permit_restoration | Permit pavement marking restoration | variant | Coordination ensures permit holders restore markings removed by utility or construction work. | protect network |
| markops.close.marking_work_closeout | Pavement marking work closeout | invariant | Closeout confirms quantities, photos, QA checks, map updates, complaints and material records. | finish job |
