# BATCH_141 — Food Plant Sanitation & Allergen Detail
# world_skills_core · source: world_skills_core:batch_141:food_sanitation_allergen_detail
# KnowledgeUnits: 44
# ВНИМАНИЕ: общеобразовательная food safety грамотность; не заменяет локальные регламенты и HACCP-план предприятия.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| foodsan.zoning.hygienic_zone | Hygienic zoning | invariant | Гигиеническое зонирование разделяет участки по риску загрязнения, продукту, персоналу, воздуху, воде и инвентарю. | не переносить риск между зонами |
| foodsan.zoning.raw_ready_separation | Raw and ready-to-eat separation | invariant | Разделение сырого и готового к употреблению продукта снижает риск перекрестного микробного загрязнения. | один из ключевых барьеров |
| foodsan.zoning.traffic_flow | Personnel traffic flow | variant | Потоки персонала должны идти от чистых зон к менее чистым или проходить контролируемую смену одежды и санитарные барьеры. | движение людей несет риск |
| foodsan.zoning.tool_color_code | Tool color coding | variant | Цветовое кодирование инвентаря помогает закрепить инструменты за зонами, аллергенами или типами продукта. | визуальный контроль |
| foodsan.cleaning.dry_cleaning | Dry cleaning in food plant | variant | Сухая уборка удаляет остатки без воды и полезна там, где влага повышает микробный риск или портит продукт. | низковлажные производства |
| foodsan.cleaning.wet_cleaning | Wet cleaning | invariant | Влажная мойка требует контроля воды, химии, механического воздействия, времени, температуры и последующей сушки. | моющий цикл как система |
| foodsan.cleaning.cip | Clean-in-place | invariant | CIP очищает внутренние поверхности оборудования циркуляцией растворов без полной разборки. | трубы, танки, пастеризаторы |
| foodsan.cleaning.cop | Clean-out-of-place | invariant | COP очищает снятые детали в отдельной мойке или ванне с контролем времени, химии и температуры. | разборные компоненты |
| foodsan.cleaning.soil_type | Soil type in sanitation | invariant | Тип загрязнения — жир, белок, сахар, минералы или крахмал — определяет выбор химии и режима мойки. | не вся грязь одинаковая |
| foodsan.cleaning.detergent_rinse | Detergent rinse | invariant | После моющего средства требуется достаточное ополаскивание, чтобы удалить остатки химии и загрязнений перед санитарной обработкой. | избежать химических остатков |
| foodsan.sanitizing.clean_before_sanitize | Clean before sanitize | invariant | Санитарная обработка эффективна только после удаления органических загрязнений, которые защищают микробы и расходуют санитайзер. | сначала мойка, потом sanitize |
| foodsan.sanitizing.contact_time | Sanitizer contact time | invariant | Санитайзер должен контактировать с поверхностью достаточно долго в правильной концентрации и условиях. | не просто распылить |
| foodsan.sanitizing.concentration_check | Sanitizer concentration check | invariant | Концентрацию санитайзера нужно проверять, потому что слишком слабый раствор неэффективен, а слишком сильный может быть опасен или оставлять остатки. | тест-полоски и журналы |
| foodsan.sanitizing.no_rinse_rule | No-rinse sanitizer rule | variant | No-rinse санитайзер допустим только при правильной концентрации и применении согласно назначению. | не все химикаты no-rinse |
| foodsan.validation.cleaning_validation | Cleaning validation | invariant | Validation подтверждает, что процедура очистки способна стабильно достигать заданного уровня чистоты. | доказать метод |
| foodsan.validation.verification_swab | Sanitation verification swab | invariant | Swab verification проверяет конкретные поверхности после очистки на остатки, индикаторы или микробные признаки. | подтвердить выполнение |
| foodsan.validation.atp_limit | ATP test limit | variant | ATP-тест быстро показывает органический остаток, но не является прямым подсчетом патогенов. | быстрый индикатор, не абсолют |
| foodsan.environmental.listeria_zone | Environmental monitoring zone | invariant | Зоны environmental monitoring различают поверхности контакта с продуктом, близкие зоны и удаленную среду по риску переноса. | план отбора проб |
| foodsan.environmental.trend_analysis | Environmental trend analysis | invariant | Тренд environmental monitoring важнее одного результата, потому что повторяемость указывает на нишу или слабый барьер. | найти источник |
| foodsan.environmental.harborages | Microbial harborage | invariant | Harborage — место, где влага, остатки и конструкция позволяют микробам сохраняться и возвращаться после уборки. | искать ниши |
| foodsan.environmental.floor_drain_risk | Floor drain risk | invariant | Трапы и стоки часто являются высокорисковыми зонами, потому что собирают влагу, остатки и биоfilm. | отделять от product zone |
| foodsan.design.hygienic_design | Hygienic equipment design | invariant | Гигиеничный дизайн оборудования избегает щелей, мертвых зон, полостей, сложной разборки и плохо дренируемых поверхностей. | легче мыть правильно |
| foodsan.design.drainability | Equipment drainability | invariant | Оборудование должно дренироваться без стоячей воды, потому что остаточная влага поддерживает микробный рост. | наклоны и слив |
| foodsan.design.material_compatibility | Food equipment material compatibility | invariant | Материалы оборудования должны выдерживать пищу, мойку, санитайзеры, температуру и механическую нагрузку без деградации. | не только stainless |
| foodsan.design.foreign_material | Foreign material control | invariant | Контроль посторонних предметов включает стекло, металл, пластик, дерево, инструменты, упаковку и личные предметы. | физическая безопасность |
| foodsan.allergen.allergen_map | Allergen map | invariant | Карта аллергенов показывает, где каждый аллерген хранится, перемещается, обрабатывается, очищается и упаковывается. | видеть пути риска |
| foodsan.allergen.dedicated_equipment | Dedicated allergen equipment | variant | Выделенное оборудование для аллергена снижает риск cross-contact, но требует места, маркировки и дисциплины. | когда очистки недостаточно |
| foodsan.allergen.changeover | Allergen changeover | invariant | Переналадка между аллергенами требует порядка производства, очистки, проверки и контроля маркировки. | защита потребителя |
| foodsan.allergen.label_control | Allergen label control | invariant | Контроль этикетки должен убедиться, что упаковка соответствует фактическому продукту и аллергенам внутри. | ошибка этикетки опасна |
| foodsan.allergen.rework_control | Allergen rework control | variant | Rework с аллергеном должен использоваться только в совместимых продуктах с правильной маркировкой и traceability. | скрытый источник allergen |
| foodsan.allergen.cleaning_verification | Allergen cleaning verification | invariant | Проверка очистки аллергенов подтверждает, что остаток целевого аллергена снижен до установленного критерия. | не полагаться на видимую чистоту |
| foodsan.trace.lot_coding | Food lot coding | invariant | Lot code связывает продукт с сырьем, линией, датой, сменой и условиями производства. | recall и расследования |
| foodsan.trace.mass_balance | Traceability mass balance | invariant | Mass balance сравнивает входы, выходы, отходы и остатки, чтобы проверить полноту прослеживаемости. | найти потерянные партии |
| foodsan.trace.mock_recall | Mock recall | invariant | Mock recall тестирует, можно ли быстро найти затронутые партии, клиентов и сырье без реального кризиса. | тренировка recall |
| foodsan.storage.temperature_log | Food temperature log | invariant | Температурный журнал хранения показывает, сохранялся ли продукт в установленном диапазоне по времени. | холодовая цепь |
| foodsan.storage.fifo_fefo | FIFO and FEFO | invariant | FIFO использует первым старейший товар, а FEFO использует первым товар с ближайшим сроком годности. | срок и качество |
| foodsan.storage.condensation_risk | Condensation risk | variant | Конденсат в пищевом производстве может переносить загрязнения и указывает на проблему температуры, влажности или вентиляции. | капли над продуктом опасны |
| foodsan.people.handwashing_station | Handwashing station | invariant | Станция мытья рук должна быть доступной, снабженной, понятной и расположенной там, где реально нужна. | поведение зависит от условий |
| foodsan.people.illness_reporting | Illness reporting | invariant | Политика сообщения о болезни должна позволять сотруднику не работать с продуктом при симптомах риска без наказания за честность. | культура безопасности |
| foodsan.people.clothing_control | Protective clothing control | variant | Спецодежда снижает перенос загрязнений только при правильном хранении, смене, стирке и движении между зонами. | одежда тоже процесс |
| foodsan.documentation.sanitation_ssop | Sanitation SSOP | invariant | SSOP описывает что чистить, чем, как, кто, когда, какие параметры и как подтверждать результат. | повторяемость уборки |
| foodsan.documentation.deviation_record | Sanitation deviation record | invariant | Запись отклонения фиксирует, что пошло не так, продуктовый риск, коррекцию, удержание продукта и предотвращение повтора. | не скрывать сбой |
| foodsan.documentation.preop_inspection | Pre-op inspection | invariant | Pre-op inspection проверяет готовность линии после санитарии до запуска продукта. | последний барьер перед производством |
| foodsan.culture.food_safety_culture | Food safety culture | invariant | Культура food safety проявляется в том, сообщают ли люди о рисках, соблюдают ли процедуры и исправляет ли руководство причины. | безопасность не только документы |
