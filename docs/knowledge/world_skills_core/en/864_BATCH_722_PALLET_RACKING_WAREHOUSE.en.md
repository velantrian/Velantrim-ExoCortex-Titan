# BATCH 722: Pallet Racking — Warehouse Storage

**KnowledgeUnits:** 50
**Namespace:** `palletrack.ops.*`
**Scope:** selective_rack, drive_in, push_back, cantilever, beam, upright, anchor, inspection

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| palletrack.ops.upright_anchor_bolting | Upright — Anchor to Floor | METHOD | Крепление стоек стеллажа к полу. Anchor: wedge anchor или epoxy anchor в бетон. Количество: минимум 1 на ногу (оба фланца). Толщина плиты: >15 см для anchor. Шаблон: upright base plate должен быть полностью на бетоне. Затяжка: момент по спецификации. Повреждённый пол: repair before anchor. Сейсмические зоны: дополнительные anchors и bracing. | Незаанкеренный rack: опрокидывается от удара forklift. |
| palletrack.ops.beam_safety_lock_clip | Beam — Safety Lock | METHOD | Фиксатор балки (beam connector). Safety clip: автоматический (spring-loaded) или ручной (pin). Проверка: после установки — beam не должен выдёргиваться без инструмента. Double check: install crew и supervisor проверяют все clips. При ударе: beam может выскочить из upright если clip не защёлкнут. Замена: damaged clip = replace немедленно. | Без safety clip: beam соскальзывает, паллеты падают. |
| palletrack.ops.load_placard_capacity | Load Placard — Capacity Sign | METHOD | Информационная табличка на стеллаже. На каждой bay: максимальная нагрузка (на pair beams, на bay total), manufacturer, date. Размещение: visible (на уровне глаз). Перегрузка: превышение capacity = permanent deformation rack. Изменение: при перемещении beams — обновить placard. | Без placard: forklift driver не знает limits. |
| palletrack.ops.row_spacer_tie_bar | Row Spacer — Flue Space | METHOD | Расстояние между двойными рядами (back-to-back). Flue space: 15-20 см зазор между pallets (противопожарный доступ sprinkler). Row spacer: металлическая труба/швеллер, соединяющая upright задних рядов (stability). Длина spacer: подбирается по distance. Крепление: bolt-on. Wall tie: rack прикреплён к стене для lateral stability. | Sprinkler должен доставать до огня между рядами. |
| palletrack.ops.deflection_collision_guard | Collision Guard — Post Protector | METHOD | Защита стоек от ударов forklift. Guard: стальной профиль, охватывающий upright (съёмный или bolted). Высота: 40-60 см от пола. Энергопоглощающий материал: plastic или steel deflection. Цвет: ярко-жёлтый (visibility). Замена: смятый guard = заменить (он выполнил свою работу). Без защиты: bent upright = reduced capacity, must replace. | Самая частая причина повреждения rack: forklift. |
