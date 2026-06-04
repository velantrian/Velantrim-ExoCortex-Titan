# BATCH 323: Water Tower Inspection Operations

**KnowledgeUnits:** 44  
**Namespace:** `watertowerops.*`  
**Scope:** tank levels, coatings, hatches, vents, ladders, cathodic protection, sampling and security.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| watertowerops.inventory.tank_id | tank ID | RECORD | Tower record includes ID, location, volume, height, material, owner and pressure zone. | Links inspection, water quality and capital planning. |
| watertowerops.inventory.design_file | design file | RECORD | Plans, coating history, repairs, mixing equipment and appurtenances are kept together. | Inspectors compare field condition to known structure. |
| watertowerops.inventory.access_route | access route | RECORD | Access notes cover gate, road, easement, weather limits and contractor staging. | Prevents failed inspections due to unreachable site. |
| watertowerops.level.normal_range | normal level range | MEASUREMENT | Operators track high, low and normal operating levels for the tank. | Abnormal levels reveal controls or demand problems. |
| watertowerops.level.altitude_valve | altitude valve check | INSPECTION | Altitude valves are checked for correct fill/close behavior and leakage. | Prevents overflow or underfilled storage. |
| watertowerops.level.overflow_pipe | overflow pipe | INSPECTION | Overflow pipe is checked for screening, discharge path, staining and freeze damage. | Shows past overflows and protects from entry. |
| watertowerops.level.mixer | tank mixer | INSPECTION | Mixer operation is checked through status, vibration, power and water-quality effect. | Reduces stratification and disinfectant decay. |
| watertowerops.coating.exterior | exterior coating | INSPECTION | Exterior coating is checked for chalking, peeling, rust, cracks and UV damage. | Coating protects steel and extends service life. |
| watertowerops.coating.interior | interior coating | INSPECTION | Interior coating is checked for blistering, holidays, delamination, rust and sediment. | Interior failure can affect water quality and corrosion. |
| watertowerops.coating.holiday_test | holiday testing | QUALITY_CHECK | Coating holiday tests detect pinholes or missed spots after coating work. | Finds defects before tank returns to service. |
| watertowerops.coating.lead_paint | legacy lead paint | CONSTRAINT | Older exterior coatings may require lead handling, containment and worker protection. | Painting becomes environmental and safety work. |
| watertowerops.coating.recoat_priority | recoat priority | DECISION_RULE | Recoating priority uses corrosion, coating age, water quality risk, access and budget. | Prevents waiting until structural damage. |
| watertowerops.hatches.roof_hatch | roof hatch | INSPECTION | Hatches are checked for locks, seals, curbs, hinges and water intrusion. | Protects potable water from contamination. |
| watertowerops.hatches.access_hatch | access hatch | INSPECTION | Access hatches need secure closure, safe opening and sanitary seal. | Enables inspection without compromising water quality. |
| watertowerops.vents.vent_screen | vent screen | INSPECTION | Vents are checked for intact screen, weather hood, corrosion and blockage. | Allows breathing while excluding birds, insects and debris. |
| watertowerops.vents.overflow_airgap | overflow air gap | SAFETY_RULE | Overflow and drain arrangements avoid cross-connection to unsafe drains. | Protects against backflow contamination. |
| watertowerops.ladders.fixed_ladder | fixed ladder | INSPECTION | Ladders are checked for rungs, corrosion, anchorage, cages or fall-arrest rail. | Climb safety is part of tank inspection. |
| watertowerops.ladders.fall_arrest | fall arrest | SAFETY_RULE | Fall protection equipment and anchor points must be rated and inspected. | Prevents fatal falls during tower work. |
| watertowerops.ladders.platform | platform condition | INSPECTION | Platforms, guardrails and toe boards are checked for corrosion and stability. | Keeps operators safe at height. |
| watertowerops.ladders.lockout_access | locked access | SECURITY | Ladder guards and locked gates restrict unauthorized climbing. | Reduces vandalism and injury risk. |
| watertowerops.cathodic.anode | sacrificial anode | INSPECTION | Anodes are checked for consumption, connection and coverage. | Slows corrosion inside submerged steel. |
| watertowerops.cathodic.impressed_current | impressed current | INSPECTION | Rectifier output, wiring and reference readings are reviewed. | Cathodic system must be powered and tuned. |
| watertowerops.cathodic.reading_log | cathodic readings | RECORD | Voltage/current readings are logged with date and water level. | Trends show protection loss before corrosion appears. |
| watertowerops.structure.shell | shell condition | INSPECTION | Shell is checked for corrosion, deformation, leaks, weld cracks and staining. | Detects structural and coating failures. |
| watertowerops.structure.roof | roof condition | INSPECTION | Roof plates, seams, drainage, penetrations and bird activity are checked. | Roof defects can admit contamination. |
| watertowerops.structure.foundation | foundation | INSPECTION | Foundation, anchor bolts, grout and settlement are inspected. | Structural support problems can progress slowly. |
| watertowerops.structure.leak | leak tracking | RECORD | Leaks are recorded by location, flow, staining and operating level. | Helps distinguish condensation, overflow and shell leak. |
| watertowerops.sampling.sample_tap | sample tap | INSPECTION | Sample taps are checked for sanitary design, accessibility and flushing. | Bad taps create misleading water-quality samples. |
| watertowerops.sampling.chlorine | chlorine residual | MEASUREMENT | Residual is checked at tank or downstream points. | Low residual signals age, mixing or nitrification issues. |
| watertowerops.sampling.bacti | bacteriological sampling | QUALITY_CHECK | Bacti samples follow sterile technique after tank entry or repairs. | Confirms safe return to service. |
| watertowerops.sampling.sediment | sediment observation | OBSERVATION | Sediment depth, color and deposits are noted during interior inspection. | Indicates cleaning need and source issues. |
| watertowerops.security.fence | fence and gate | INSPECTION | Fence, gate, locks and signage are checked for breaches. | Protects critical drinking-water asset. |
| watertowerops.security.intrusion | intrusion evidence | SECURITY | Graffiti, cut locks, footprints, open hatches or tampering are documented. | Triggers security and water-quality response. |
| watertowerops.security.camera | camera or alarm | INSPECTION | Cameras, door alarms and telemetry are checked where installed. | Security tools need maintenance too. |
| watertowerops.operations.drain_down | drain-down plan | METHOD | Interior inspection needs drawdown, isolation, pressure review and customer impact plan. | Prevents pressure loss while tank is offline. |
| watertowerops.operations.disinfection | disinfection after entry | METHOD | Tank is cleaned, disinfected and sampled before return to service. | Protects potable water after workers enter. |
| watertowerops.operations.confined_space | confined space | SAFETY_RULE | Tank entry requires confined-space review, ventilation, rescue and atmospheric checks. | Interior work has oxygen and chemical hazards. |
| watertowerops.operations.coordination | operations coordination | METHOD | Operators coordinate SCADA levels, valves, pumps, crews and notifications. | Inspection must fit system hydraulics. |
| watertowerops.records.inspection_report | inspection report | RECORD | Report includes photos, deficiencies, severity, recommendations and repair priorities. | Turns field observations into action. |
| watertowerops.records.deficiency_log | deficiency log | RECORD | Each issue has owner, status, due date, cost and closeout evidence. | Prevents inspection findings from being forgotten. |
| watertowerops.records.paint_history | paint history | RECORD | Coating type, contractor, surface prep, date and warranty are stored. | Supports lifecycle planning and claims. |
| watertowerops.reporting.capital_plan | capital plan | MODEL | Capital plan prioritizes recoating, mixing, safety retrofits, structural repairs and replacement. | Converts tower condition into budget decisions. |
| watertowerops.reporting.regulatory | regulatory report | RECORD | Reports may document sanitary defects, inspection date, disinfection and corrective actions. | Supports drinking-water compliance. |
| watertowerops.review.risk_score | tank risk score | MODEL | Risk combines condition, water quality, security, redundancy, age and pressure-zone importance. | Helps rank towers across a utility. |

