# BATCH 321: Stormwater Pond Maintenance Operations

**KnowledgeUnits:** 44  
**Namespace:** `swpondops.*`  
**Scope:** forebays, embankments, outlets, vegetation, sediment, inspections, repairs and owner compliance.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| swpondops.inventory.pond_id | pond ID | RECORD | Pond file stores ID, watershed, owner, design type, drainage area, outlet and easements. | Links inspections, complaints and maintenance obligations. |
| swpondops.inventory.design_plan | design plan | RECORD | Design plan shows permanent pool, storage, forebay, outlet, spillway and access. | Maintenance checks compare field condition to intended function. |
| swpondops.inventory.owner_duty | owner duty | CONSTRAINT | Private or HOA ponds often have maintenance duties in agreements or permits. | Clarifies who must act and pay. |
| swpondops.inventory.access_easement | access easement | RECORD | Access routes and easements are mapped for equipment and inspectors. | Sediment removal fails if heavy equipment cannot reach pond. |
| swpondops.forebay.function | forebay function | MODEL | Forebay traps coarse sediment before main pond cell. | Easier cleanout protects main storage and habitat. |
| swpondops.forebay.sediment_marker | sediment marker | MEASUREMENT | Staff plates or survey points track sediment accumulation. | Creates objective cleanout trigger. |
| swpondops.forebay.cleanout | forebay cleanout | METHOD | Cleanout removes sediment, stabilizes disturbed area and prevents downstream release. | Restores pretreatment capacity. |
| swpondops.forebay.access | forebay access | INSPECTION | Inspectors check whether access pad, ramp or gate remains usable. | Maintenance planning depends on actual equipment access. |
| swpondops.embankment.slope | embankment slope | INSPECTION | Embankment is checked for settlement, cracks, slides, erosion and animal holes. | Pond embankment failure can release stored water. |
| swpondops.embankment.crest | crest condition | INSPECTION | Crest is checked for low spots, rutting, trees, unauthorized paths and vehicle damage. | Maintains freeboard and structural integrity. |
| swpondops.embankment.seepage | seepage signs | OBSERVATION | Wet spots, boils or cloudy flow at downstream toe are recorded. | Can signal internal erosion risk. |
| swpondops.embankment.spillway | emergency spillway | INSPECTION | Spillway is checked for blockage, erosion, settlement and vegetation. | Protects pond from overtopping. |
| swpondops.outlet.riser | outlet riser | INSPECTION | Riser is checked for clogging, corrosion, cracks, trash rack and structural stability. | Outlet controls water level and detention time. |
| swpondops.outlet.orifice | orifice opening | INSPECTION | Orifices are checked for trash, sediment, algae and missing plates. | Small openings clog easily and change discharge. |
| swpondops.outlet.barrel | outlet barrel | INSPECTION | Barrel is checked for joint separation, blockage, sinkholes and downstream erosion. | Hidden outlet failure can undermine embankment. |
| swpondops.outlet.trash_rack | trash rack | METHOD | Trash rack is maintained clear while preserving safety and wildlife considerations. | Prevents flooding from blocked outlet. |
| swpondops.outlet.low_flow | low-flow channel | INSPECTION | Low-flow path is checked for blockage, sediment and erosion. | Maintains dry-weather conveyance. |
| swpondops.vegetation.buffer | vegetated buffer | METHOD | Buffer around pond filters runoff and discourages mowing to water edge. | Improves pollutant removal and bank stability. |
| swpondops.vegetation.invasive | invasive vegetation | FAILURE_MODE | Invasive reeds, woody plants or nuisance species can reduce access and function. | Requires planned control, not random cutting. |
| swpondops.vegetation.trees_on_dam | trees on embankment | FAILURE_MODE | Trees on embankment can create root paths and inspection obstruction. | Often prohibited by dam/pond maintenance standards. |
| swpondops.vegetation.mowing | mowing plan | METHOD | Mowing frequency balances visibility, erosion protection, habitat and access. | Over-mowing and neglect both create problems. |
| swpondops.vegetation.aquatic_plants | aquatic plant balance | MODEL | Some aquatic vegetation supports treatment, but dense mats block flow. | Maintenance aims for function, not bare pond. |
| swpondops.sediment.bathymetry | bathymetry survey | MEASUREMENT | Survey estimates sediment volume and lost storage. | Determines dredging need and budget. |
| swpondops.sediment.cleanout_trigger | sediment cleanout trigger | DECISION_RULE | Trigger may be percent storage loss, forebay marker, water quality failure or flooding. | Makes dredging defensible. |
| swpondops.sediment.disposal | sediment disposal | METHOD | Sediment is tested or handled according to contamination risk and local rules. | Prevents moving pollutants to a new site. |
| swpondops.sediment.upstream_source | upstream source | METHOD | Sediment source is traced to construction, erosion, roads, banks or failing controls. | Cleanout without source control repeats quickly. |
| swpondops.inspection.routine | routine inspection | METHOD | Inspection covers water level, inlets, outlet, embankment, vegetation, sediment and access. | Creates complete maintenance picture. |
| swpondops.inspection.post_storm | post-storm inspection | METHOD | After large storms, check debris, erosion, outlet blockage, high-water marks and damage. | Storms reveal capacity and blockage issues. |
| swpondops.inspection.photo_points | photo points | RECORD | Fixed photos document inlets, outlet, forebay, slopes and access. | Shows change over time. |
| swpondops.inspection.condition_score | condition score | MODEL | Score combines structural, hydraulic, sediment, vegetation and access issues. | Ranks ponds across a portfolio. |
| swpondops.repairs.bank_stabilization | bank stabilization | METHOD | Banks may need grading, vegetation, coir, riprap or toe protection. | Reduces erosion and sediment feedback. |
| swpondops.repairs.outlet_repair | outlet repair | METHOD | Outlet repairs address cracks, clogged orifices, corrosion, joints and trash racks. | Restores designed water release. |
| swpondops.repairs.access_repair | access repair | METHOD | Gates, paths, pads and ramps are repaired for inspection and equipment. | Keeps future maintenance possible. |
| swpondops.repairs.animal_damage | animal damage repair | METHOD | Burrows or dams are assessed for embankment risk and flow impacts. | Wildlife activity can become structural issue. |
| swpondops.compliance.notice_owner | owner notice | METHOD | Owner receives inspection findings, required correction, deadline and evidence needs. | Moves private pond defects toward action. |
| swpondops.compliance.escalation | escalation | DECISION_RULE | Missed deadlines may lead to penalties, municipal work, liens or permit enforcement. | Protects public drainage when owner fails. |
| swpondops.compliance.recorded_agreement | recorded agreement | RECORD | Maintenance agreement is stored with parcel or HOA records. | Future owners inherit obligations. |
| swpondops.compliance.reinspection | reinspection | QUALITY_CHECK | Completed repairs are verified with field check, photos and invoices where needed. | Prevents paper-only compliance. |
| swpondops.safety.public_access | public access safety | SAFETY_RULE | Steep slopes, deep water, thin ice and outlet structures need signage or barriers. | Ponds are infrastructure, not just landscape. |
| swpondops.safety.mosquito | mosquito complaint | METHOD | Mosquito complaints trigger checks for stagnant pockets, blocked flow and vegetation mats. | Fixes habitat conditions rather than only spraying. |
| swpondops.records.work_order | work order | RECORD | Work orders include location, defect, crew, contractor, photos, materials and closeout. | Maintains maintenance history. |
| swpondops.records.cost_history | cost history | RECORD | Dredging, mowing, repairs and inspections are tracked by pond ID. | Supports lifecycle budgeting. |
| swpondops.reporting.portfolio | portfolio report | RECORD | Report lists inspected ponds, condition scores, urgent defects, costs and compliance cases. | Gives managers a system-level view. |
| swpondops.reporting.capital_plan | capital plan | MODEL | Capital plan prioritizes dredging, outlet rebuilds, access and retrofits by risk and benefit. | Turns inspections into budget decisions. |

