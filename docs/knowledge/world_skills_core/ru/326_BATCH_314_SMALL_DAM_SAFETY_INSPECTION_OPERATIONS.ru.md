# BATCH 314: Small Dam Safety Inspection Operations

**KnowledgeUnits:** 44  
**Namespace:** `smalldamops.*`  
**Scope:** embankment, spillway, outlet works, seepage, instrumentation, emergency action and records.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| smalldamops.inventory.dam_id | dam ID | RECORD | Small dam inventory хранит dam name, ID, owner, location, height, storage, hazard class и regulator. | Без inventory невозможно управлять inspection cycle. |
| smalldamops.inventory.hazard_class | hazard classification | MODEL | Hazard class отражает consequence of failure, not current condition. | Малый dam с домами ниже по течению требует больше внимания. |
| smalldamops.inventory.design_docs | design document file | RECORD | Plans, calculations, permits, as-builts и prior inspections хранят вместе. | История помогает понять нормальное и abnormal состояние. |
| smalldamops.inventory.downstream_map | downstream impact map | RECORD | Карта показывает roads, homes, utilities, bridges и flood path below dam. | Нужна для emergency action planning. |
| smalldamops.embankment.crest | crest condition | INSPECTION | Crest проверяют на settlement, cracking, rutting, depressions и unauthorized traffic. | Crest часто показывает deformation до явной аварии. |
| smalldamops.embankment.upstream_slope | upstream slope | INSPECTION | Upstream slope проверяют на wave erosion, riprap loss, slides, animal damage и vegetation. | Защищает dam от reservoir action. |
| smalldamops.embankment.downstream_slope | downstream slope | INSPECTION | Downstream slope проверяют на wet spots, slides, bulging, erosion и woody growth. | Это ключевая зона для seepage and stability signs. |
| smalldamops.embankment.freeboard | freeboard check | MEASUREMENT | Freeboard сравнивает water surface with dam crest and design requirements. | Недостаточный freeboard повышает overtopping risk. |
| smalldamops.embankment.animal_burrows | animal burrows | FAILURE_MODE | Burrows create preferential seepage paths and local voids. | Требуют repair and animal control, not only surface fill. |
| smalldamops.embankment.woody_vegetation | woody vegetation | FAILURE_MODE | Trees can hide defects, create root paths and leave voids after death. | Vegetation management является dam safety task. |
| smalldamops.spillway.principal_spillway | principal spillway | INSPECTION | Principal spillway проверяют на debris, corrosion, cracks, inlet condition и capacity signs. | Основной outlet должен safely pass routine flows. |
| smalldamops.spillway.emergency_spillway | emergency spillway | INSPECTION | Emergency spillway проверяют на vegetation, erosion, obstructions, settlement и control section. | Это backup против overtopping при больших flows. |
| smalldamops.spillway.debris_control | debris control | METHOD | Debris racks and approach areas чистят до storm season. | Blocked spillway может поднять reservoir выше safe level. |
| smalldamops.spillway.erosion_headcut | spillway headcut | FAILURE_MODE | Headcut in earth spillway can migrate upstream and breach control. | Требует срочной оценки и stabilization. |
| smalldamops.spillway.concrete_crack | concrete crack | INSPECTION | Cracks, spalls, joint offsets and undermining фиксируют по location and severity. | Concrete defects могут привести к leakage and structural loss. |
| smalldamops.outlet.low_level | low-level outlet | INSPECTION | Low-level outlet проверяют на operability, corrosion, leaks, controls и blockage. | Позволяет drawdown during emergency or maintenance. |
| smalldamops.outlet.valve_exercise | valve exercise | METHOD | Valves periodically operate through controlled range when safe. | Неиспользуемый valve может не открыться в emergency. |
| smalldamops.outlet.conduit_joint | conduit joint | FAILURE_MODE | Joint leaks can carry soil and trigger internal erosion. | Outlet conduits are common dam failure paths. |
| smalldamops.outlet.trashrack | trashrack inspection | INSPECTION | Trashrack проверяют на clogging, corrosion, attachment и safe access. | Засор снижает outlet capacity. |
| smalldamops.outlet.energy_dissipator | energy dissipator | INSPECTION | Stilling basin, riprap or plunge pool проверяют на scour and displacement. | Outlet flow не должен разрушать downstream toe. |
| smalldamops.seepage.clear_flow | clear seepage | OBSERVATION | Clear seepage is documented by location, flow and trend. | Stable seepage может быть monitored but still tracked. |
| smalldamops.seepage.muddy_flow | muddy seepage | FAILURE_MODE | Muddy or increasing seepage indicates possible internal erosion. | Требует emergency evaluation. |
| smalldamops.seepage.wet_area | wet area mapping | METHOD | Wet zones on downstream slope/toe are mapped with reservoir level and rainfall context. | Отличает rainfall wetness от reservoir-driven seepage. |
| smalldamops.seepage.drain_outlet | drain outlet | INSPECTION | Toe drains and relief drains проверяют на flow, clarity, blockage and animal entry. | Drains work only if outlets remain open. |
| smalldamops.instrument.piezometer | piezometer reading | MEASUREMENT | Piezometer measures internal water pressure at specific locations. | Shows seepage pressure changes not visible on surface. |
| smalldamops.instrument.staff_gauge | reservoir gauge | MEASUREMENT | Staff gauge records reservoir level and storm response. | Connects inspection observations to water load. |
| smalldamops.instrument.survey_monument | settlement monument | MEASUREMENT | Survey monuments track crest or embankment movement over time. | Detects settlement before freeboard is lost. |
| smalldamops.instrument.reading_schedule | instrument schedule | METHOD | Readings increase during high water, unusual seepage or after earthquakes/storms. | Monitoring intensity follows risk. |
| smalldamops.instrument.data_plot | data plot review | QUALITY_CHECK | Instrument data are plotted against reservoir level and time. | Trends matter more than isolated readings. |
| smalldamops.emergency.eap | emergency action plan | RECORD | EAP lists contacts, triggers, inundation maps, warning steps and responsibilities. | Converts dam distress into organized public warning. |
| smalldamops.emergency.trigger_levels | emergency trigger levels | DECISION_RULE | Triggers cover overtopping, muddy seepage, slides, spillway failure and rapid reservoir rise. | Staff know when to notify, inspect or evacuate. |
| smalldamops.emergency.drawdown | emergency drawdown | METHOD | Drawdown uses safe outlet capacity and downstream warning. | Lowering reservoir can reduce risk but may create downstream hazards. |
| smalldamops.emergency.communication_test | communication test | QUALITY_CHECK | EAP contacts and phone trees are tested periodically. | A plan with dead contacts fails during emergency. |
| smalldamops.emergency.after_storm | post-storm inspection | METHOD | After major rainfall, inspect reservoir level, spillways, slopes, seepage and downstream damage. | Storms reveal defects not visible in dry conditions. |
| smalldamops.maintenance.mowing | mowing for visibility | METHOD | Grass cover is maintained low enough for inspection without exposing soil. | Balances erosion protection and defect visibility. |
| smalldamops.maintenance.rodent_control | rodent control | METHOD | Rodent management combines inspection, repair, habitat control and authorized control measures. | Reduces recurring burrow defects. |
| smalldamops.maintenance.riprap_repair | riprap repair | METHOD | Displaced riprap is replaced with proper size, bedding and slope coverage. | Protects upstream slope from wave erosion. |
| smalldamops.maintenance.access | access maintenance | METHOD | Roads, gates and paths must allow inspection and emergency equipment access. | Dam safety depends on reaching the site during bad weather. |
| smalldamops.records.inspection_form | inspection form | RECORD | Forms standardize observations for embankment, spillways, outlet, seepage, instruments and actions. | Prevents missing key components. |
| smalldamops.records.photo_station | photo stations | RECORD | Repeat photos from fixed stations show changes in slopes, structures and vegetation. | Visual trends support maintenance decisions. |
| smalldamops.records.deficiency_log | deficiency log | RECORD | Each deficiency has severity, owner, due date, action and closeout evidence. | Inspection findings become managed repairs. |
| smalldamops.records.regulatory_report | regulatory report | RECORD | Reports include condition, deficiencies, hazard class, EAP status and recommended actions. | Supports compliance and owner accountability. |
| smalldamops.records.owner_brief | owner brief | METHOD | Owner brief translates technical findings into risks, deadlines, costs and required decisions. | Small dam owners often need clear priorities to act. |
| smalldamops.review.periodic_engineer | periodic engineer review | DECISION_RULE | Higher hazard or deteriorating dams require professional engineering review. | Routine checklist cannot replace specialist judgment for serious defects. |

