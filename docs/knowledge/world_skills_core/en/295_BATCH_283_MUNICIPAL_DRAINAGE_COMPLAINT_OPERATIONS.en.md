# BATCH_283 — Municipal Drainage Complaint Operations Detail
# world_skills_core · source: world_skills_core:batch_283:municipal_drainage_complaint_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| drainageops.intake.drainage_complaint | Municipal drainage complaint | invariant | Complaint records flooding, ponding, erosion, blocked pipe, yard water or structure concern. | start case |
| drainageops.intake.location_precision | Drainage complaint location precision | invariant | Location captures address, parcel, road segment, inlet, ditch, outfall or map point. | find issue |
| drainageops.intake.storm_context | Drainage complaint storm context | variant | Context records rainfall timing, intensity, duration, snowmelt, tide or upstream condition. | interpret cause |
| drainageops.intake.property_damage_claim | Drainage property damage claim | variant | Claim records alleged damage, photos, dates, cause, ownership review and insurance routing. | document risk |
| drainageops.triage.public_safety_priority | Drainage public safety priority | invariant | Priority flags road flooding, sinkhole, washout, structure threat, school route or emergency access. | dispatch fast |
| drainageops.triage.private_property_screen | Private property drainage screen | invariant | Screen distinguishes public drainage responsibility from private grading, roof leaders or yard issues. | clarify scope |
| drainageops.triage.repeat_location | Repeat drainage complaint location | variant | Repeat location indicates unresolved capacity, grading, blockage or ownership problem. | target investigation |
| drainageops.field.initial_site_check | Drainage initial site check | invariant | Check observes water path, inlets, ditches, pipes, grading, debris, erosion and photos. | verify complaint |
| drainageops.field.high_water_mark | Drainage high-water mark | variant | Mark estimates flood extent from debris line, staining, sediment, resident photo or field evidence. | reconstruct event |
| drainageops.field.upstream_downstream_check | Upstream downstream drainage check | invariant | Check compares flow path before and after complaint point to locate restriction or source. | find cause |
| drainageops.field.dry_weather_flow | Dry-weather drainage flow | variant | Flow outside storms may indicate groundwater, sump discharge, leak, illicit discharge or irrigation. | classify source |
| drainageops.assets.inlet_capacity | Drainage inlet capacity issue | invariant | Issue occurs when inlet size, placement, clogging or gutter spread cannot capture runoff. | plan fix |
| drainageops.assets.pipe_obstruction | Drainage pipe obstruction | invariant | Obstruction includes sediment, roots, collapse, debris, utility conflict or displaced joint. | restore flow |
| drainageops.assets.ditch_condition | Drainage ditch condition | invariant | Condition reviews vegetation, sediment, erosion, slope, blockages, culverts and maintenance access. | maintain channel |
| drainageops.assets.culvert_condition | Culvert condition | invariant | Condition checks inlet, outlet, barrel, headwalls, sediment, deformation and hydraulic capacity. | prevent flooding |
| drainageops.grading.negative_slope | Negative drainage slope | invariant | Negative slope directs water toward structure, sidewalk, road or low area instead of outlet. | identify grading |
| drainageops.grading.low_point | Drainage low point | invariant | Low point accumulates water where outlet, inlet or positive grade is insufficient. | diagnose ponding |
| drainageops.grading.swale_function | Drainage swale function | variant | Swale conveys runoff through shallow graded channel that can fail from fill, vegetation or obstruction. | preserve flow |
| drainageops.ownership.public_private_boundary | Drainage public-private boundary | invariant | Boundary determines if city, county, utility, HOA, owner or developer is responsible. | assign action |
| drainageops.ownership.easement_check | Drainage easement check | invariant | Check reviews recorded easement, access rights, maintenance responsibility and legal limits. | enter lawfully |
| drainageops.ownership.encroachment_issue | Drainage easement encroachment | variant | Encroachment includes fences, sheds, landscaping or fill blocking access or flow. | resolve obstruction |
| drainageops.workorders.cleaning_order | Drainage cleaning work order | invariant | Order clears inlet, ditch, pipe, culvert or outfall using crew, equipment and disposal steps. | restore capacity |
| drainageops.workorders.repair_order | Drainage repair work order | invariant | Order fixes pipe, structure, ditch, erosion, grading, inlet frame or outlet protection. | correct defect |
| drainageops.workorders.investigation_order | Drainage investigation order | variant | Order sends engineering review when complaint requires survey, modeling, ownership or design decision. | escalate analysis |
| drainageops.solutions.minor_grading | Minor drainage grading | variant | Grading reshapes shallow flow path, shoulder, ditch or swale within maintenance authority. | improve flow |
| drainageops.solutions.inlet_adjustment | Drainage inlet adjustment | variant | Adjustment changes inlet elevation, grate type, throat opening or approach flow path. | improve capture |
| drainageops.solutions.pipe_repair | Drainage pipe repair | invariant | Repair addresses broken, collapsed, separated, clogged or undersized pipe within scope. | restore conveyance |
| drainageops.solutions.outlet_stabilization | Drainage outlet stabilization | variant | Stabilization uses riprap, apron, vegetation or energy dissipation to reduce erosion. | protect outlet |
| drainageops.communication.resident_update | Drainage resident update | invariant | Update explains findings, responsibility, planned work, limits, schedule and next contact. | manage expectations |
| drainageops.communication.no_city_action | No city drainage action notice | variant | Notice explains why issue is private, outside authority, below threshold or needs owner work. | close fairly |
| drainageops.communication.interagency_referral | Drainage interagency referral | variant | Referral sends issue to county, state DOT, utility, flood district or environmental agency. | route ownership |
| drainageops.records.photo_log | Drainage complaint photo log | invariant | Log stores before, during and after photos with location, date, direction and notes. | evidence |
| drainageops.records.rainfall_reference | Drainage rainfall reference | variant | Reference links complaint to gauge data, radar estimate or storm recurrence context. | support analysis |
| drainageops.records.case_history | Drainage case history | invariant | History records complaints, inspections, work orders, calls, decisions and closeout evidence. | avoid repeat |
| drainageops.safety.flooded_road_control | Flooded road control | invariant | Control blocks unsafe travel through barricades, signs, cones and emergency coordination. | protect public |
| drainageops.safety.manhole_inlet_hazard | Drainage structure hazard | invariant | Hazard includes open grate, missing lid, sinkhole, undermined pavement or confined-space risk. | urgent action |
| drainageops.safety.field_water_hazard | Drainage field water hazard | variant | Hazard covers swift water, contaminated water, hidden holes, unstable banks and wildlife. | protect crew |
| drainageops.reporting.complaint_backlog | Drainage complaint backlog report | invariant | Report summarizes open cases by age, severity, cause, district and assigned owner. | manage workload |
| drainageops.reporting.repeat_flood_report | Repeat drainage flood report | variant | Report identifies chronic locations, storm triggers, maintenance history and capital needs. | plan investment |
| drainageops.metrics.response_time | Drainage complaint response time KPI | invariant | KPI measures time from intake to field check, action, referral or closure. | improve service |
| drainageops.metrics.corrective_action_rate | Drainage corrective action rate KPI | variant | KPI tracks complaints resulting in cleaning, repair, capital project, referral or no action. | understand demand |
| drainageops.coordination.capital_project_link | Drainage capital project link | variant | Link transfers chronic or undersized system issues from maintenance to design program. | solve root cause |
| drainageops.coordination.development_review_link | Development drainage review link | variant | Link flags complaints tied to new construction, grading changes or permit compliance. | enforce design |
| drainageops.close.complaint_closeout | Drainage complaint closeout | invariant | Closeout confirms findings, work completion or referral, resident notification and record update. | finish case |
