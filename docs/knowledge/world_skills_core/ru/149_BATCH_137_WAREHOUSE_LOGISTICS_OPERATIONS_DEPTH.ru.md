# BATCH_137 — Warehouse Logistics Operations Depth
# world_skills_core · source: world_skills_core:batch_137:warehouse_logistics_depth
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| whops.receiving.asn | Advanced shipping notice | invariant | ASN заранее сообщает складy ожидаемые позиции, количества, упаковки и идентификаторы поставки. | ускоряет приемку |
| whops.receiving.appointment | Dock appointment | variant | Запись на док распределяет прибытие транспорта во времени, чтобы снизить очереди и перегрузку приемки. | управлять воротами |
| whops.receiving.blind_count | Blind count | variant | Blind count скрывает ожидаемое количество от приемщика, чтобы снизить подтверждение ошибки поставщика. | честная приемка |
| whops.receiving.damage_notation | Damage notation | invariant | Повреждения при приемке нужно фиксировать до перемещения товара с фото, описанием, количеством и транспортными документами. | претензии к перевозчику |
| whops.putaway.directed_putaway | Directed putaway | invariant | Directed putaway направляет товар в место хранения по правилам размера, скорости, совместимости и доступности. | меньше хаоса на складе |
| whops.putaway.random_location | Random location storage | variant | Random location storage хранит товар в доступных местах при точном WMS-учете, а не по фиксированному адресу. | гибкость емкости |
| whops.putaway.fixed_location | Fixed location storage | variant | Fixed location storage закрепляет SKU за определенной ячейкой, упрощая поиск, но снижая гибкость пространства. | удобно для fast movers |
| whops.slotting.velocity | Velocity slotting | invariant | Slotting по скорости размещает часто выбираемые SKU ближе к удобным зонам отбора. | меньше ходьбы |
| whops.slotting.cube_movement | Cube movement | invariant | Cube movement учитывает не только число заказов, но и объем или массу, перемещаемые через склад. | тяжелое и объемное ближе |
| whops.slotting.affinity | Product affinity slotting | variant | Affinity slotting размещает товары, часто покупаемые вместе, ближе друг к другу для уменьшения маршрута отбора. | ускорение комплектования |
| whops.slotting.replenishment_trigger | Replenishment trigger | invariant | Триггер пополнения pick face задает момент, когда запас в зоне отбора нужно пополнить из reserve. | избежать пустых ячеек |
| whops.inventory.cycle_count | Cycle count | invariant | Cycle count проверяет часть запасов регулярно, не останавливая весь склад для полной инвентаризации. | постоянная точность |
| whops.inventory.abc_counting | ABC counting | invariant | ABC counting чаще проверяет дорогие, быстрые или рискованные позиции, чем медленные и малозначимые. | фокус контроля |
| whops.inventory.location_accuracy | Location accuracy | invariant | Точность адресации показывает, находится ли товар в указанной WMS ячейке. | товар есть, но потерян |
| whops.inventory.lot_traceability | Lot traceability | invariant | Lot traceability связывает партию товара с приемкой, хранением, отгрузкой и возможным отзывом. | качество и recall |
| whops.inventory.expiration_control | Expiration control | invariant | Контроль срока годности требует FEFO, блокировок и видимости дат, чтобы не отгружать просроченный товар. | пища, фарма, химия |
| whops.picking.discrete_picking | Discrete picking | variant | Discrete picking собирает один заказ за проход и прост в управлении, но может быть медленным при большом объеме. | малые операции |
| whops.picking.batch_picking | Batch picking | variant | Batch picking собирает несколько заказов вместе и затем сортирует позиции по заказам. | меньше маршрутов |
| whops.picking.zone_picking | Zone picking | variant | Zone picking делит склад на зоны, где каждый сборщик отвечает за свою часть заказа. | масштабирование отбора |
| whops.picking.wave_picking | Wave picking | variant | Wave picking выпускает заказы волнами по времени, перевозчику, зоне или приоритету. | синхронизация склада |
| whops.picking.pick_to_light | Pick-to-light | variant | Pick-to-light направляет сборщика световыми индикаторами к нужной ячейке и количеству. | скорость и меньше ошибок |
| whops.picking.voice_picking | Voice picking | variant | Voice picking дает голосовые инструкции и оставляет руки свободными для отбора. | холодные склады и высокая скорость |
| whops.packing.cartonization | Cartonization | invariant | Cartonization выбирает подходящую коробку по размерам, весу, хрупкости и правилам перевозчика. | меньше воздуха и повреждений |
| whops.packing.dunnage | Dunnage selection | invariant | Dunnage заполняет пустоты и защищает товар от ударов, вибрации и сжатия в упаковке. | защита при доставке |
| whops.packing.weight_verification | Pack weight verification | invariant | Проверка веса упаковки сравнивает фактический вес с ожидаемым, чтобы поймать ошибки комплектования. | простой контроль качества |
| whops.shipping.manifest | Shipping manifest | invariant | Shipping manifest перечисляет отправления, перевозчика, сервис, вес, места и документы передачи. | контроль отгрузки |
| whops.shipping.cutoff_time | Carrier cutoff time | invariant | Cutoff time перевозчика задает крайний момент, когда заказ должен быть готов для отправки в тот же цикл. | обещание доставки |
| whops.shipping.trailer_loading | Trailer loading plan | variant | План загрузки трейлера учитывает маршрут, вес, хрупкость, очередность выгрузки и безопасность крепления. | меньше повреждений и переработки |
| whops.returns.rma | Return merchandise authorization | invariant | RMA связывает возврат с причиной, клиентом, товаром, ожидаемым действием и разрешением на прием. | контролируемые возвраты |
| whops.returns.disposition | Return disposition | invariant | Disposition возврата определяет, вернуть товар в продажу, отремонтировать, уценить, списать или отправить поставщику. | стоимость возврата |
| whops.returns.refurbish_flow | Refurbish flow | variant | Поток refurbish требует диагностики, очистки, ремонта, теста, переупаковки и новой маркировки состояния. | вернуть ценность товара |
| whops.returns.fraud_signal | Return fraud signal | variant | Сигналы мошеннического возврата включают несоответствие серийника, состояния, веса, истории покупок или содержимого. | защита маржи |
| whops.safety.pedestrian_separation | Pedestrian separation | invariant | Разделение пешеходов и погрузчиков снижает риск столкновений через разметку, барьеры, маршруты и правила видимости. | безопасность склада |
| whops.safety.rack_load_label | Rack load label | invariant | Табличка грузоподъемности стеллажа указывает допустимые нагрузки и конфигурацию, которую нельзя менять без проверки. | избежать обрушения |
| whops.safety.damaged_rack | Damaged rack control | invariant | Поврежденный стеллаж нужно оценить, разгрузить или оградить по процедуре, потому что локальный удар снижает несущую способность. | риск collapse |
| whops.safety.battery_charging | Forklift battery charging | variant | Зона зарядки батарей требует вентиляции, защиты от кислоты или пожара, порядка кабелей и доступа к emergency equipment. | безопасность энергии |
| whops.layout.cross_dock | Cross-dock flow | variant | Cross-dock минимизирует хранение, переводя входящие товары прямо к исходящей отгрузке при точной синхронизации. | скорость, но мало буфера |
| whops.layout.pick_face | Pick face | invariant | Pick face — фронтальная зона, откуда сборщик берет товар, пополняемая из резервного хранения. | скорость отбора |
| whops.layout.reserve_storage | Reserve storage | invariant | Reserve storage хранит запас сверх pick face и требует пополнения по правилам спроса и емкости. | баланс емкости |
| whops.layout.dock_door_utilization | Dock door utilization | invariant | Использование доковых ворот показывает, насколько ворота заняты приемкой, отгрузкой или ожиданием транспорта. | узкое место на воротах |
| whops.metrics.order_accuracy | Order accuracy | invariant | Order accuracy измеряет долю заказов, отгруженных с правильными SKU, количеством, состоянием и документами. | клиентское качество |
| whops.metrics.on_time_ship | On-time ship rate | invariant | On-time ship rate показывает долю заказов, переданных перевозчику до обещанного cutoff или даты. | выполнение обещания |
| whops.metrics.lines_per_hour | Lines per hour | invariant | Lines per hour измеряет производительность обработки строк заказа, но зависит от профиля SKU и метода отбора. | сравнивать осторожно |
| whops.metrics.inventory_accuracy | Inventory accuracy | invariant | Inventory accuracy сравнивает учетный запас с физическим количеством по SKU, партии и местоположению. | основа доступности |
