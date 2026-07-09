# BATCH_174 — Laboratory Animal Facility Operations Detail
# world_skills_core · source: world_skills_core:batch_174:lab_animal_facility_operations
# KnowledgeUnits: 44
# ВНИМАНИЕ: операционные и welfare-процессы; не протокол эксперимента и не ветеринарное назначение.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| lafacility.records.cage_card | Cage card | invariant | Cage card identifies animals, strain or group, protocol, investigator, dates and special notes. | cage-side identity |
| lafacility.records.animal_id | Animal identification | invariant | Animal ID links individual or group to records, observations, procedures and location. | avoid animal mix-up |
| lafacility.records.room_log | Animal room log | invariant | Room log records daily checks, environmental readings, issues, entries and staff initials. | room-level evidence |
| lafacility.records.protocol_number | Animal protocol number | invariant | Protocol number links activity to approved study scope, species, numbers and conditions. | compliance trace |
| lafacility.records.census_count | Animal census count | invariant | Census count reconciles animals present with records, billing, transfers and protocol limits. | know population |
| lafacility.records.transfer_record | Animal transfer record | invariant | Transfer record documents movement between rooms, studies or facilities with date, IDs and approvals. | location history |
| lafacility.husbandry.feed_check | Feed check | invariant | Feed check confirms correct diet, availability, freshness and special dietary instructions. | daily welfare basic |
| lafacility.husbandry.water_check | Water check | invariant | Water check confirms access, function, bottle condition or automated watering status. | water is critical |
| lafacility.husbandry.bedding_change | Bedding change | invariant | Bedding change maintains hygiene, comfort and environmental control according to species and room schedule. | cage environment |
| lafacility.husbandry.cage_change | Cage change | invariant | Cage change moves animals to clean housing while preserving ID, group integrity and welfare observations. | clean housing without mix-up |
| lafacility.husbandry.sentinel_program | Sentinel program | variant | Sentinel program monitors colony health status through selected animals or environmental samples. | early disease detection |
| lafacility.husbandry.enrichment | Animal enrichment | invariant | Enrichment provides species-appropriate environmental or social stimulation consistent with welfare and study constraints. | welfare beyond food |
| lafacility.health.daily_observation | Daily health observation | invariant | Observation checks appearance, behavior, posture, food/water use, wounds and abnormal signs. | see welfare issues early |
| lafacility.health.health_flag | Health flag | invariant | Health flag marks animals needing veterinary, investigator or supervisor review. | escalation signal |
| lafacility.health.body_condition_score | Body condition score | variant | Score records body condition trend using facility-approved scale when relevant. | welfare trend |
| lafacility.health.humane_endpoint_alert | Humane endpoint alert | invariant | Endpoint alert prompts review when observed condition approaches approved welfare limit. | protect animal welfare |
| lafacility.health.treatment_record | Animal treatment record | invariant | Treatment record documents clinician-authorized care, date, animal, staff and follow-up. | care traceability |
| lafacility.health.mortality_record | Mortality record | invariant | Mortality record documents unexpected death, ID, location, time found and notification path. | serious event record |
| lafacility.environment.temperature_range | Room temperature range | invariant | Temperature range must be monitored because it affects animal welfare, physiology and study consistency. | environment as variable |
| lafacility.environment.humidity_range | Room humidity range | invariant | Humidity control affects comfort, respiratory conditions, static, bedding and equipment performance. | stable room conditions |
| lafacility.environment.light_cycle | Light cycle | invariant | Light cycle controls day/night timing and must be documented to avoid welfare and study disruption. | time signal |
| lafacility.environment.air_changes | Air changes | variant | Air changes affect odor, ammonia, allergens, temperature and pathogen control. | ventilation matters |
| lafacility.environment.alarm_response | Facility alarm response | invariant | Alarm response covers temperature, water, ventilation, power or access alarms with escalation and documentation. | respond before harm |
| lafacility.environment.noise_control | Animal facility noise control | variant | Noise control reduces stress from equipment, construction, alarms or handling. | quiet supports welfare |
| lafacility.biosecurity.quarantine | Animal quarantine | invariant | Quarantine separates incoming or suspect animals until health status and facility requirements are satisfied. | protect colony |
| lafacility.biosecurity.ppe_entry | Animal room PPE entry | invariant | PPE entry requirements reduce contamination between rooms, colonies, staff and visitors. | barrier discipline |
| lafacility.biosecurity.traffic_flow | Facility traffic flow | invariant | Traffic flow orders movement from clean to higher-risk areas and controls cross-contamination. | route matters |
| lafacility.biosecurity.cage_sanitization | Cage sanitization | invariant | Sanitization process controls wash, temperature, chemical, contact time and storage of clean cages. | clean equipment |
| lafacility.biosecurity.waste_stream | Animal facility waste stream | invariant | Waste stream separates bedding, carcasses, sharps, chemical, biohazard and ordinary waste. | disposal compliance |
| lafacility.biosecurity.pest_control | Facility pest control | invariant | Pest control prevents insects or rodents from entering animal rooms, feed storage or waste areas. | protect colony |
| lafacility.operations.work_order | Facility work order | invariant | Work order records equipment, room, repair need, priority, access and completion evidence. | maintenance trace |
| lafacility.operations.equipment_sanitization | Shared equipment sanitization | invariant | Shared equipment must be cleaned between rooms or uses according to contamination risk. | avoid transfer |
| lafacility.operations.feed_storage | Feed storage | invariant | Feed storage controls expiry, pests, humidity, lot identity and separation of special diets. | diet quality |
| lafacility.operations.bedding_storage | Bedding storage | invariant | Bedding storage protects material from moisture, contamination, pests and mix-up. | housing material quality |
| lafacility.operations.cage_wash_log | Cage wash log | invariant | Wash log records machine cycle, load, parameters, issues and release of clean equipment. | sanitation evidence |
| lafacility.operations.power_backup | Animal facility backup power | invariant | Backup power protects ventilation, temperature, watering, alarms and critical equipment. | continuity for welfare |
| lafacility.compliance.training_record | Animal facility training record | invariant | Training record confirms staff competence for husbandry, handling, PPE, records and emergency actions. | people quality system |
| lafacility.compliance.iacuc_approval | Animal care approval status | invariant | Approval status verifies work is covered by active authorized protocol before activities proceed. | authorized work only |
| lafacility.compliance.deviation_report | Animal protocol deviation | invariant | Deviation report documents activity outside approved process, impact, notification and corrective action. | transparency |
| lafacility.compliance.audit_readiness | Animal facility audit readiness | invariant | Readiness means records, rooms, cage cards, training and environmental logs are current and retrievable. | inspection without panic |
| lafacility.compliance.sop_version | Facility SOP version | invariant | SOP version control prevents staff from following obsolete husbandry, sanitation or emergency procedures. | current instructions |
| lafacility.emergency.evacuate_shelter | Animal facility emergency shelter | variant | Emergency plan decides shelter-in-place, relocation or evacuation based on species, building and hazard. | protect animals during crisis |
| lafacility.emergency.water_failure | Automated watering failure | invariant | Water failure response provides alternate water, checks affected racks and documents duration. | immediate welfare risk |
| lafacility.emergency.disease_outbreak | Colony disease outbreak response | variant | Outbreak response controls movement, diagnostics coordination, communication, quarantine and sanitation escalation. | contain health event |
