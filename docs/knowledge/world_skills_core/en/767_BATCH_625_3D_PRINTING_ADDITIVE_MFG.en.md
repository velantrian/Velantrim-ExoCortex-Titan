# BATCH 625: 3D Printing — Additive Manufacturing Operations

**KnowledgeUnits:** 50
**Namespace:** `print3d.ops.*`
**Scope:** FDM, SLA, slicing, filament, resin, bed_leveling, post_processing

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| print3d.ops.fdm_bed_leveling | FDM — Bed Leveling & First Layer | METHOD | Manual paper method (0.1 мм зазор). Mesh bed leveling (BLTouch, probe). Z-offset micro-stepping. First layer test: ровное прилегание без щелей и гребешков. Bed adhesion: clean isopropyl, PEI sheet, glue stick для PLA на стекле. | Первый слой — 90% отказов начинаются здесь. |
| print3d.ops.filament_drying | Filament — Drying & Storage | METHOD | PLA гигроскопичен. Признаки влажного: popping звук, stringing, poor adhesion. Сушка: dryer 45-50°C PLA, 65-75°C PETG, 70-80°C Nylon 4-6 часов. Хранение: airtight box + desiccant. Nylon/PVA — печатать из dry box. | Мокрый PLA становится хрупким. |
| print3d.ops.sla_resin_safety | SLA — Resin Handling & Safety | METHOD | Фотополимер токсичен. PPE: нитриловые перчатки всегда, очки, маска. Вентиляция enclosure + exhaust. Wash: isopropyl 99% 2-5 мин. Post-cure: UV chamber 2-5 мин. Support removal. Disposal: НЕ сливать uncured в раковину — отвердить на солнце, затем в мусор. | Resin spill: немедленно вытереть. |
| print3d.ops.slicing_support | Slicing — Support & Orientation | METHOD | Orientation: минимизация supports (>45° = нужны). Z distance 0.1-0.2 мм FDM, 0.05-0.1 SLA. Infill: 15-20% decorative, 50-100% functional. Gyroid — равномерная прочность. Layer height: 0.12 quality, 0.20 standard, 0.28 draft. Brim/Raft. | Orientation: нагрузку направлять поперёк слоёв. |
| print3d.ops.abs_enclosure | ABS — Enclosure & Warp Prevention | METHOD | Высокая усадка → warping. Решения: enclosure 40-50°C, bed 100-110°C, nozzle 240-260°C, PEI sheet + ABS slurry, brim 8-10 мм, без сквозняков. Cooling fan OFF. Vapour smoothing: ацетоновый пар для глянца. | ABS fumes (styrene) — carbon/HEPA фильтр, vent наружу. |
