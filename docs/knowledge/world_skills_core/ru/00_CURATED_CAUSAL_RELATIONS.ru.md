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
