# BATCH_154 — Utilities Outage Management & Restoration Detail
# world_skills_core · source: world_skills_core:batch_154:utilities_outage_restoration_detail
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| outageops.intake.trouble_call | Trouble call | invariant | Trouble call records customer-reported outage, hazard, location, time, symptoms and contact details. | первый сигнал аварии |
| outageops.intake.outage_ticket | Outage ticket | invariant | Outage ticket groups calls, device alarms, crews, switching steps, estimated restoration and status history. | единая аварийная запись |
| outageops.intake.customer_clustering | Customer call clustering | invariant | Clustering calls by feeder, transformer, pressure zone or circuit helps infer the likely affected asset. | many calls reveal location |
| outageops.intake.hazard_report | Hazard report | invariant | Hazard report flags downed wire, gas odor, flooding, traffic exposure or other immediate public safety risk. | safety before restoration |
| outageops.intake.priority_customer | Priority customer flag | variant | Priority flags identify hospitals, critical facilities, life-support customers or essential infrastructure for response planning. | not all loads equal |
| outageops.intake.estimated_time_restore | Estimated time of restoration | variant | ETR communicates expected restoration time and must be updated when field facts change. | customer expectations |
| outageops.dispatch.crew_dispatch | Crew dispatch | invariant | Crew dispatch assigns qualified personnel, location, task, safety notes, materials and communication channel. | send the right crew |
| outageops.dispatch.crew_staging | Crew staging area | variant | Staging area organizes crews, materials, food, rest, briefings and assignments during large events. | scale response |
| outageops.dispatch.mutual_aid | Mutual aid request | variant | Mutual aid brings external crews or resources under agreed roles, safety rules, logistics and cost tracking. | surge capacity |
| outageops.dispatch.damage_assessment | Utility damage assessment | invariant | Damage assessment identifies failed assets, access limits, hazards, materials needed and expected repair duration. | field truth |
| outageops.dispatch.patrol_route | Patrol route | variant | Patrol route sequences inspection of lines, valves, stations or assets based on risk, access and reports. | inspect efficiently |
| outageops.dispatch.materials_request | Emergency materials request | invariant | Materials request links repair task to required poles, cable, valves, transformers, fittings, fuel or tools. | crews cannot fix without parts |
| outageops.safety.tailboard_brief | Tailboard safety brief | invariant | Tailboard brief covers hazards, job steps, roles, PPE, switching state, traffic control and emergency plan. | safety before work |
| outageops.safety.lockout_tagout | Utility lockout tagout | invariant | Lockout/tagout prevents unexpected energization, pressure, flow or movement during repair. | control hazardous energy |
| outageops.safety.public_barrier | Public barrier | invariant | Barriers and signs keep public away from energized, pressurized, flooded or unstable work zones. | protect bystanders |
| outageops.safety.backfeed_risk | Backfeed risk | invariant | Backfeed can energize equipment unexpectedly from generators, alternate feeds or customer sources. | assume dangerous until verified |
| outageops.safety.gas_make_safe | Gas make-safe | variant | Make-safe actions reduce immediate gas hazard through isolation, ventilation, monitoring and controlled access. | stabilize before repair |
| outageops.safety.confined_space | Confined space utility work | variant | Confined space work requires atmosphere checks, entry controls, rescue plan and trained workers. | hidden fatal risk |
| outageops.operations.switching_order | Switching order | invariant | Switching order documents the planned sequence of operations to isolate, transfer or restore utility sections. | no improvising with networks |
| outageops.operations.clearance_hold | Clearance hold | invariant | Clearance hold confirms equipment is isolated and reserved for worker protection until released. | protect crews |
| outageops.operations.sectionalizing | Sectionalizing | invariant | Sectionalizing isolates smaller network parts to reduce affected customers and locate the fault. | narrow the outage |
| outageops.operations.load_transfer | Load transfer | variant | Load transfer moves demand to alternate feeders, pumps, mains or sources within safe capacity. | restore some before repair |
| outageops.operations.pressure_zone | Pressure zone management | variant | Pressure zone management maintains acceptable water or gas pressure while isolating damaged sections. | service continuity |
| outageops.operations.generator_connection | Temporary generator connection | variant | Temporary generation supports critical load when grid restoration is delayed and safety interfaces are controlled. | temporary resilience |
| outageops.repair.fault_location | Fault location | invariant | Fault location uses reports, protection operation, testing, patrol and asset knowledge to find the failed point. | repair starts with location |
| outageops.repair.pole_replacement | Pole replacement coordination | variant | Pole replacement coordinates access, excavation, lifting, wires, attachments, traffic and utility conflicts. | many crews, one asset |
| outageops.repair.cable_splice | Cable splice repair | variant | Cable splice repair requires correct material, preparation, testing, environmental control and documentation. | hidden joint quality |
| outageops.repair.valve_isolation | Valve isolation | invariant | Valve isolation controls flow around a damaged water or gas asset before repair. | stop the source |
| outageops.repair.water_main_flush | Water main flush | invariant | Flushing after repair removes sediment, air, disinfectant imbalance or contamination risk before normal service. | restore quality, not just flow |
| outageops.repair.transformer_swap | Transformer replacement | variant | Transformer replacement requires capacity match, connections, lifting safety, testing and customer restoration sequence. | critical distribution asset |
| outageops.communication.customer_update | Customer outage update | invariant | Customer update should state known status, safety advice, affected area, ETR and next update time. | reduce uncertainty |
| outageops.communication.critical_customer_contact | Critical customer contact | invariant | Critical customer contact gives tailored status to hospitals, emergency services, water plants or key facilities. | coordinate essential services |
| outageops.communication.media_brief | Utility media brief | variant | Media brief summarizes impact, safety, restoration progress and what customers should or should not do. | public trust |
| outageops.communication.call_center_script | Call center script | variant | Script aligns customer service messages with current operations and safety instructions. | one voice |
| outageops.communication.outage_map | Public outage map | variant | Outage map displays affected areas, customer counts and ETR with uncertainty and refresh limits. | transparency with caveats |
| outageops.recovery.restoration_verification | Restoration verification | invariant | Verification confirms service returned, hazards are cleared, equipment is stable and tickets can close. | do not close on assumption |
| outageops.recovery.nested_outage | Nested outage | invariant | Nested outage is a smaller remaining failure hidden inside a larger outage until upstream restoration occurs. | not everyone comes back |
| outageops.recovery.customer_callback | Customer callback | variant | Callback checks whether service is restored for customers whose status remains uncertain. | close the last gaps |
| outageops.recovery.asset_record_update | Asset record update | invariant | Asset records must reflect replaced equipment, temporary repairs, test results and follow-up work. | system memory |
| outageops.recovery.after_action_review | After-action review | invariant | AAR reviews timeline, safety, decisions, resources, communications and improvement actions after outage. | improve next response |
| outageops.metrics.saidi | SAIDI metric | invariant | SAIDI measures average outage duration experienced by customers over a period. | reliability duration |
| outageops.metrics.saifi | SAIFI metric | invariant | SAIFI measures average outage frequency experienced by customers over a period. | reliability frequency |
| outageops.metrics.caidi | CAIDI metric | invariant | CAIDI relates restoration duration to interrupted customers and helps evaluate repair performance. | repair time lens |
| outageops.metrics.repeat_outage | Repeat outage analysis | invariant | Repeat outage analysis identifies assets or areas with recurring interruptions and unresolved root causes. | reliability improvement |
