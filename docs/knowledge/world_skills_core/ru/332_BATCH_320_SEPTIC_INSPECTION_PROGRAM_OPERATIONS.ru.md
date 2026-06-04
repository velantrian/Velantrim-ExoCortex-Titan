# BATCH 320: Septic Inspection Program Operations

**KnowledgeUnits:** 44  
**Namespace:** `septicops.*`  
**Scope:** permits, site records, tank checks, drainfields, failures, notices, repairs and public health reporting.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| septicops.records.parcel_file | parcel septic file | RECORD | File links parcel, owner, system type, permit, as-built, tank size and drainfield location. | Prevents guesswork during inspection and sale. |
| septicops.records.asbuilt | as-built drawing | RECORD | As-built shows tank, distribution box, drainfield, reserve area and setbacks. | Inspectors can find components without damaging property. |
| septicops.records.permit_history | permit history | RECORD | Permit history tracks installation, repairs, variances, pump-outs and complaints. | Reveals chronic failure patterns. |
| septicops.intake.inspection_request | inspection request | RECORD | Request records reason: sale, complaint, routine cycle, repair, expansion or permit. | Sets legal authority and scope. |
| septicops.intake.owner_notice | owner notice | METHOD | Owner receives date, access needs, documents, pets and safety instructions. | Improves cooperation and inspection completeness. |
| septicops.intake.weather_screen | weather screen | DECISION_RULE | Inspection timing considers snow, frozen soil, flooding, drought or high groundwater. | Conditions affect whether failures are visible. |
| septicops.site.setback_check | setback check | CONSTRAINT | System distance is checked from wells, water bodies, buildings, property lines and slopes. | Protects drinking water and surface water. |
| septicops.site.surface_signs | surface signs | OBSERVATION | Wet spots, odor, lush grass, surfacing sewage or erosion indicate possible failure. | Fast field cues guide deeper checks. |
| septicops.site.water_use_context | water use context | RECORD | Occupancy, fixtures, laundry, business use and seasonal use are recorded. | Hydraulic load explains system stress. |
| septicops.tank.access_lids | tank access lids | INSPECTION | Lids and risers are checked for access, cracks, safety and watertightness. | Unsafe or buried lids hinder maintenance. |
| septicops.tank.sludge_scum | sludge and scum | MEASUREMENT | Sludge and scum levels are measured against tank capacity and outlet clearance. | Determines pump-out need and risk to drainfield. |
| septicops.tank.baffles | baffles and tees | INSPECTION | Inlet/outlet baffles are checked for damage, blockage and corrosion. | Failed baffles let solids enter drainfield. |
| septicops.tank.leakage | tank leakage | FAILURE_MODE | Cracks, root intrusion or high liquid level may indicate infiltration or exfiltration. | Leaks can overload system or contaminate soil. |
| septicops.tank.pumpout_record | pump-out record | RECORD | Pump-out date, hauler, volume and observations are recorded. | Supports maintenance compliance. |
| septicops.drainfield.location | drainfield location | RECORD | Drainfield boundaries and reserve area are mapped or field-marked. | Prevents paving, building or driving over absorption area. |
| septicops.drainfield.saturation | saturation signs | OBSERVATION | Ponding, biomat overload, odor or surfacing effluent indicate poor absorption. | Signals failure or hydraulic overload. |
| septicops.drainfield.vegetation | vegetation condition | OBSERVATION | Trees, deep roots or unusual growth are noted near drainfield. | Roots and moisture clues affect repair decisions. |
| septicops.drainfield.compaction | compaction risk | FAILURE_MODE | Vehicles, livestock or construction over drainfield reduce soil pores. | Compaction can ruin treatment capacity. |
| septicops.drainfield.distribution | distribution box | INSPECTION | D-box is checked for level, blockage, solids, broken outlets and flow balance. | Uneven distribution overloads one trench. |
| septicops.failure.imminent_hazard | imminent health hazard | DECISION_RULE | Surfacing sewage, sewage backing into home or contamination risk triggers urgent action. | Protects residents and neighbors. |
| septicops.failure.hydraulic_overload | hydraulic overload | MODEL | Too much water can exceed soil absorption even if hardware is intact. | Repair may include water-use reduction or system expansion. |
| septicops.failure.soil_limitation | soil limitation | CONSTRAINT | Shallow bedrock, clay, high groundwater or steep slope limits onsite treatment. | Determines feasible repair options. |
| septicops.failure.illegal_connection | illegal connection | FAILURE_MODE | Roof drains, sump pumps or stormwater connected to septic overload system. | Removing connection may solve repeated failure. |
| septicops.notice.deficiency_notice | deficiency notice | RECORD | Notice lists findings, required action, deadline, appeal route and contact. | Creates due process and compliance path. |
| septicops.notice.pumpout_order | pump-out order | METHOD | Pump-out is ordered when solids level or maintenance violation requires it. | Simple intervention may prevent drainfield damage. |
| septicops.notice.repair_order | repair order | METHOD | Repair order specifies permit requirement, licensed contractor and completion proof. | Moves failed systems toward correction. |
| septicops.notice.noncompliance | noncompliance escalation | DECISION_RULE | Missed deadlines escalate to penalties, liens, court or service restrictions where legal. | Protects public health when voluntary action fails. |
| septicops.repair.repair_permit | repair permit | RECORD | Repair permit documents design, site constraints, contractor and approval conditions. | Controls work before excavation. |
| septicops.repair.alternative_system | alternative system | MODEL | Mound, aerobic, sand filter or advanced treatment may be needed on constrained sites. | Not every lot can use conventional trenches. |
| septicops.repair.final_inspection | final inspection | QUALITY_CHECK | Final checks installation, elevations, materials, setbacks and as-built update. | Confirms repair matches permit. |
| septicops.repair.maintenance_contract | maintenance contract | CONSTRAINT | Advanced systems may require ongoing service contract and reports. | Treatment depends on active maintenance. |
| septicops.publichealth.well_sampling | well sampling trigger | DECISION_RULE | Nearby wells may be sampled when sewage failure threatens groundwater. | Detects exposure beyond property. |
| septicops.publichealth.disease_risk | disease risk | MODEL | Failing systems can spread pathogens through surface water, groundwater or direct contact. | Explains why enforcement is health-based. |
| septicops.publichealth.cluster_review | cluster review | METHOD | Multiple failures in area may indicate high groundwater, old systems or subdivision issue. | Program can shift from parcel response to area planning. |
| septicops.publichealth.reporting | public health reporting | RECORD | Reports summarize complaints, failures, repairs, hazards and unresolved cases. | Supports oversight and grants. |
| septicops.qa.inspector_training | inspector training | METHOD | Inspectors learn system types, safety, soil clues, records, notices and evidence handling. | Consistent inspections reduce disputes. |
| septicops.qa.photo_evidence | photo evidence | RECORD | Photos document lids, tank condition, field signs, failures and repairs. | Supports notices and contractor handoff. |
| septicops.qa.data_consistency | data consistency | QUALITY_CHECK | Parcel, permit, owner and coordinates are checked across systems. | Prevents action against wrong property. |
| septicops.safety.h2s | hydrogen sulfide risk | SAFETY_RULE | Tanks can contain toxic gases; inspectors avoid entry and use safe opening procedures. | Prevents fatal confined-space exposure. |
| septicops.safety.open_tank | open tank safety | SAFETY_RULE | Open tanks are guarded and never left unattended. | Protects people and animals from falls. |
| septicops.program.routine_cycle | routine cycle | DECISION_RULE | Inspection interval depends on system age, risk, water body proximity and local rules. | Focuses effort where failures matter most. |
| septicops.program.sale_transfer | sale transfer inspection | METHOD | Property transfer inspection verifies system condition before ownership changes. | Prevents hidden health liabilities. |
| septicops.program.database | program database | RECORD | Database tracks permits, inspections, failures, notices, repairs and maintenance. | Enables population-level septic management. |
| septicops.program.education | owner education | METHOD | Owners receive guidance on pumping, water use, grease, additives and drainfield protection. | Prevention is cheaper than repair. |

