# BATCH 1041: Storm Shelter — Safe Room Construction

**KnowledgeUnits:** 5
**Namespace:** `storm.ops.*`
**Scope:** ICC500, concrete, steel_door, anchor, ventilation, underground, above_ground

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| storm.ops.door_impact_test_15lb | Дверь — испытание на удар (ракета весом 15 фунтов) | METHOD | Противоторнадная дверь (ICC 500). Тест: 15-фунтовый (6.8 кг) 2×4 деревянный снаряд выстреливается в дверь со скоростью 160 км/ч (100 mph) — дверь не должна быть пробита. Дверь: стальная 14 ga min, 3-point locking (вверх-вниз-центр), hinges внутрь (не наружу — не срезать). Outward opening: door не может быть заблокирована debris. Inward opening: стандарт для жилых. | Обычная exterior door: торнадо пробивает мгновенно. |
| storm.ops.concrete_wall_reinforcement | Бетонная стена — деталь арматуры | METHOD | Армирование стен убежища. Wall: 15-20 см толщина, reinforced. Rebar: #4 (12 мм) горизонтально и вертикально через 30-40 см. Connection: dowels в фундамент. Roof: reinforced slab 15-20 см, connected к стенам (monolithic pour предпочтительнее). Для ICC 500: walls должны выдержать давление ветра EF5 (400+ км/ч) и debris impact. | Блочные стены без армирования: разрушаются. |
| storm.ops.ventilation_impact_protection | Вентиляция — противоударная решетка | METHOD | Вентиляция убежища. Vents: через стену или потолок с impact-protected grille (стальная решётка). Отверстие: не менее 2% площади пола. Natural ventilation: cross-ventilation с двумя openings. Без вентиляции: задохнутся за часы. Protection: debris guard на внешней стороне. Fan (опционально): на battery backup. Связь: NOAA weather radio (crank/rechargeable). | Вентиляция не должна ослаблять структурную прочность. |
| storm.ops.underground_entry_hatch | Подземелье — Входной люк | METHOD | Вход в подземное убежище (гаражный пол или двор). Hatch: стальная sliding или hinged door (flush с полом). Ladder/stairs. Drainage: sump pump (грунтовые воды!). Вентиляция: свежий воздух intake труба (выше уровня земли). Emergency egress: второй выход (обязателен!). Waterproofing: membrane снаружи (грунтовые воды). | Без sump pump: затопление при дождях. |
| storm.ops.anchoring_foundation_bolts | Анкеровка — фундаментные болты | METHOD | Крепление надземного убежища к фундаменту. Anchor bolts: 16 мм диаметр, L-образные, замоноличены в фундамент (глубина 15-20 см). Шаг: 80-120 см. Washer + nut. Steel frame убежища приваривается к anchor bolts. Инспекция: torque test. | Сорванный anchor = убежище сносит ветром. |
