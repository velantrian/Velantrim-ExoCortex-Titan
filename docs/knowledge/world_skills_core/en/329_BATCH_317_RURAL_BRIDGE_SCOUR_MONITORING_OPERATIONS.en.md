# BATCH 317: Rural Bridge Scour Monitoring Operations

**KnowledgeUnits:** 44  
**Namespace:** `bridgescourops.*`  
**Scope:** inventory, channel checks, debris, foundations, flood patrol, countermeasures and closure triggers.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| bridgescourops.inventory.bridge_id | bridge ID | RECORD | Bridge scour file uses bridge ID, route, stream, owner, span, foundation type and inspection class. | Links hydraulic risk to asset management. |
| bridgescourops.inventory.scour_category | scour category | MODEL | Bridges are categorized as low risk, scour susceptible, unknown foundation or critical. | Determines monitoring intensity. |
| bridgescourops.inventory.foundation_type | foundation type | RECORD | Spread footing, pile, drilled shaft or unknown foundations are recorded. | Foundation type changes failure vulnerability. |
| bridgescourops.inventory.stream_context | stream context | RECORD | File notes watershed, channel slope, bed material, bends, floodplain and past migration. | Scour risk depends on river behavior, not bridge alone. |
| bridgescourops.inventory.plan_of_action | scour plan of action | RECORD | POA defines flood thresholds, inspection steps, closure triggers and contacts. | Gives staff a preplanned response during floods. |
| bridgescourops.channel.cross_section | channel cross-section | MEASUREMENT | Repeated cross-sections show bed lowering, aggradation and bank movement. | Detects change before foundations are exposed. |
| bridgescourops.channel.thalweg | thalweg location | OBSERVATION | Deepest channel line is tracked relative to piers and abutments. | Shifting thalweg can move scour attack point. |
| bridgescourops.channel.bank_erosion | bank erosion | INSPECTION | Banks are checked for undercutting, slumps, exposed roots and approach road threat. | Bank loss can undermine abutments and approaches. |
| bridgescourops.channel.bed_material | bed material | OBSERVATION | Bed is described as clay, silt, sand, gravel, cobble, rock or armoring. | Erodibility sets how quickly scour can deepen. |
| bridgescourops.channel.aggradation | aggradation | FAILURE_MODE | Sediment buildup can redirect flow and increase local scour elsewhere. | More sediment is not automatically safer. |
| bridgescourops.debris.debris_jam | debris jam | INSPECTION | Logs, trash and vegetation trapped on piers or railings are documented. | Debris increases hydraulic force and local scour. |
| bridgescourops.debris.removal_priority | debris removal priority | DECISION_RULE | Removal priority considers flood forecast, access, bridge criticality and worker safety. | Avoids risky work when benefit is low. |
| bridgescourops.debris.upstream_source | upstream debris source | METHOD | Crews note eroding banks, fallen trees, beaver activity or land clearing upstream. | Source control can reduce recurring jams. |
| bridgescourops.debris.safe_removal | safe debris removal | SAFETY_RULE | Removal near water requires traffic control, equipment plan and flood awareness. | Protects crews from water and road hazards. |
| bridgescourops.foundation.exposed_footing | exposed footing | FAILURE_MODE | Exposed footing or pile caps indicate loss of supporting bed material. | May require immediate engineering review. |
| bridgescourops.foundation.undermining | undermining | FAILURE_MODE | Voids beneath abutments, wingwalls or footings are critical defects. | Hidden undermining can precede sudden failure. |
| bridgescourops.foundation.pier_nose | pier nose scour | INSPECTION | Scour holes form around pier noses under high velocity. | Local scour can be deeper than visible low-flow water suggests. |
| bridgescourops.foundation.unknown_foundation | unknown foundation | CONSTRAINT | Unknown foundation bridges need conservative monitoring and documentation. | Lack of plans increases uncertainty. |
| bridgescourops.flood.stage_threshold | flood stage threshold | DECISION_RULE | Patrol starts at stream gauges, rainfall forecasts or local trigger levels. | Crews mobilize before peak risk. |
| bridgescourops.flood.highwater_mark | high-water mark | RECORD | High-water marks are recorded after events with location and elevation if possible. | Supports calibration of flood risk. |
| bridgescourops.flood.patrol_check | flood patrol check | METHOD | Patrol checks water level, debris, overtopping, approach settlement and visible foundation exposure. | Fast field screen decides whether to keep route open. |
| bridgescourops.flood.night_limit | night inspection limit | SAFETY_RULE | Night or high-flow inspections avoid unsafe approaches and use remote observations where possible. | Inspector safety limits direct observation. |
| bridgescourops.flood.post_event | post-event inspection | METHOD | After water recedes, crews inspect channel, foundations, approaches, debris and countermeasures. | Damage often appears after peak flow. |
| bridgescourops.counter.riprap | riprap countermeasure | METHOD | Properly sized riprap with filter protects banks, abutments or piers. | Undersized rock washes away and gives false security. |
| bridgescourops.counter.guide_bank | guide bank | METHOD | Guide banks align flow through bridge opening and reduce abutment attack. | Hydraulics can be managed upstream of the bridge. |
| bridgescourops.counter.grade_control | grade control | METHOD | Grade control stabilizes bed elevation where channel incision threatens foundations. | Stops progressive lowering that exposes supports. |
| bridgescourops.counter.monitoring | countermeasure monitoring | INSPECTION | Countermeasures are checked for displacement, burial, undermining and vegetation. | Installed protection can fail silently. |
| bridgescourops.closure.trigger | closure trigger | DECISION_RULE | Closure is triggered by overtopping, exposed foundations, approach washout, severe debris or engineer order. | Protects public when uncertainty is too high. |
| bridgescourops.closure.detour | detour plan | RECORD | Detour routes, signs, emergency services and school routes are preplanned. | Rural closures can isolate residents. |
| bridgescourops.closure.reopen | reopen criteria | QUALITY_CHECK | Reopening requires inspection, defect resolution or engineering approval. | Prevents unsafe reopening after water drops. |
| bridgescourops.closure.public_notice | public notice | METHOD | Notices give bridge ID, road, closure reason, detour and expected review time. | Reduces confusion and risky bypass attempts. |
| bridgescourops.records.photo_points | fixed photo points | RECORD | Photos are repeated from upstream, downstream, deck, abutments and channel bed. | Visual history reveals gradual channel change. |
| bridgescourops.records.soundings | sounding records | MEASUREMENT | Soundings measure bed elevation around piers and abutments during safe conditions. | Quantifies scour hole depth. |
| bridgescourops.records.inspection_flag | inspection flag | RECORD | Flags mark urgent scour, debris, approach damage or monitoring needs in asset system. | Keeps findings visible to bridge managers. |
| bridgescourops.records.rainfall_link | rainfall link | RECORD | Inspection records include rainfall, gauge height or flood estimate. | Connects damage to event magnitude. |
| bridgescourops.qa.data_consistency | data consistency | QUALITY_CHECK | Bridge ID, stationing, photos and measurements are checked for consistency. | Prevents mixing observations from nearby crossings. |
| bridgescourops.qa.training | scour training | METHOD | Inspectors learn scour signs, water safety, POA use and closure authority. | Rural crews often make first safety call. |
| bridgescourops.qa.instrument_check | instrument check | QUALITY_CHECK | Staff gauges, sonar, drones or cameras are checked before storm season. | Monitoring tools fail if not maintained. |
| bridgescourops.reporting.priority_list | priority list | RECORD | Priority list ranks bridges by scour risk, criticality, unknown foundations and past events. | Directs limited funds to highest risk. |
| bridgescourops.reporting.event_report | event report | RECORD | Event report summarizes inspected bridges, closures, damages, debris and repairs. | Supports reimbursement and planning. |
| bridgescourops.reporting.capital_need | capital need | MODEL | Capital need includes replacement, countermeasure, study, instrumentation or channel work. | Converts inspection risk into budget action. |
| bridgescourops.reporting.owner_coordination | owner coordination | METHOD | County, state, railroad or private owners coordinate where responsibilities overlap. | Water does not respect ownership boundaries. |
| bridgescourops.reporting.lessons | lessons learned | METHOD | After floods, teams review triggers, closures, detours, communication and repairs. | Refines the POA for the next event. |
| bridgescourops.public.local_reports | local report intake | METHOD | Residents can report debris, flooding, noise, settlement or washed approaches. | Local observations extend monitoring coverage. |

