# CURATED CAUSAL RELATIONS — явные причинные связи (World Skills Core)

**Статус:** production curated layer
**Формат:** `| source_id | relation | target_id | evidence | confidence |`
**Правило:** только стабильные `fact_id`; связь не выводится, если её нет в таблице.

| source_id | relation | target_id | evidence | confidence |
|---|---|---|---|---|
| plumb.system.shutoff_main | enables | emergplumb.ops.water_main_shutoff | theory→emergency SOP bridge | 0.92 |
| plumb.system.local_shutoff | enables | plumbing.ops.toilet_flush_mechanism | local valve before fixture repair | 0.9 |
| foodservice.safety.haccp | requires | foodservice.safety.temperature | HACCP CCP temperature monitoring | 0.93 |
| foodservice.safety.handwashing | prevents | foodservice.safety.cross_contamination | WHO hand hygiene barrier | 0.94 |
| infcontrol.ops.five_moments_hand_hygiene | requires | infcontrol.ops.contact_precautions | WHO 5 moments before contact precautions | 0.95 |
| electric.ops.grounding_earthing_system | requires | electric.ops.electrical_panel_wiring | NEC grounding before panel energization | 0.91 |
| electric.ops.gfci_afci_operation_test | requires | electric.ops.outlet_installation_receptacle | test protective devices before receptacle use | 0.9 |
| gutter.ops.slope_hanger_spacing | precedes | gutter.ops.downspout_outlet_routing | gutter install SOP: slope before downspout | 0.88 |
| gutter.ops.downspout_outlet_routing | precedes | gutter.ops.leaf_guard_types | downspout routing before leaf guard retrofit | 0.87 |
| construction.safety.confined_space | requires | construction.safety.asbestos | confined space protocol before asbestos work | 0.92 |
| construction.safety.lead_paint | requires | construction.safety.respirator_fit | lead paint work requires respirator fit test | 0.91 |
| infcontrol.ops.hand_hygiene | prevents | infcontrol.ops.hai_transmission | hand hygiene prevents healthcare-associated infection | 0.94 |
| foodservice.safety.cold_holding | prevents | foodservice.safety.foodborne_illness | cold holding prevents pathogen growth | 0.93 |
| electric.ops.panel_dead_front | requires | electric.ops.circuit_breaker_install | de-energized panel before breaker install | 0.9 |
| plumb.ops.drain_vent_sizing | enables | plumb.ops.toilet_rough_in | vent sizing enables toilet rough-in | 0.88 |
| safety.ops.lockout_tagout | requires | electric.ops.panel_work | LOTO before electrical panel work | 0.95 |
| safety.ops.confined_space_entry | requires | construction.safety.confined_space | entry permit requires confined space assessment | 0.9 |
| chemistry.lab.fume_hood | prevents | chemistry.lab.toxic_exposure | fume hood prevents toxic inhalation | 0.92 |
| medicine.clinical.informed_consent | requires | medicine.clinical.procedure | consent required before clinical procedure | 0.96 |
| streetlightops.electrical.photocell_fault | causes | streetlightops.outage.dayburner | photocell fault causes dayburner | 0.91 |
| compostops.moisture.excess_moisture | causes | compostops.aeration.odor_from_anaerobic | excess moisture causes anaerobic odor | 0.9 |
| fountainops.lighting.led_driver_fault | causes | fountainops.lighting.night_scene_review | LED driver fault degrades night scene quality | 0.87 |
| sidewalkops.hazard.settlement_depression | causes | sidewalkops.hazard.slippery_surface | settlement ponding can create slippery surface | 0.86 |
