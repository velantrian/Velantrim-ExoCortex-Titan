# BATCH 310: Farm Equipment Cooperative Operations

**KnowledgeUnits:** 44  
**Namespace:** `farmcoopops.*`  
**Scope:** reservations, maintenance, training, transport, damage, billing, safety and records.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| farmcoopops.membership.member_agreement | member agreement | RECORD | Agreement задает eligibility, fees, equipment access, liability, scheduling rules и penalties. | Делает shared ownership понятным до первого конфликта. |
| farmcoopops.membership.operator_authorization | operator authorization | RECORD | Только authorized operators могут бронировать и использовать specific equipment. | Снижает риск поломок, травм и insurance disputes. |
| farmcoopops.membership.priority_policy | priority policy | DECISION_RULE | Приоритет может зависеть от membership tier, seasonal window, crop urgency или first-come rule. | Предотвращает спор за equipment в короткие агрономические окна. |
| farmcoopops.reservation.calendar | reservation calendar | RECORD | Календарь показывает equipment, user, pickup, return, location, buffer time и status. | Обеспечивает видимость доступности и планирование работ. |
| farmcoopops.reservation.weather_hold | weather hold | DECISION_RULE | Weather hold временно блокирует use при rain, wet soils, wind или unsafe transport. | Защищает soil, operator и machinery. |
| farmcoopops.reservation.buffer_turnaround | turnaround buffer | HEURISTIC | Между bookings оставляют время на cleaning, inspection, transport и small repairs. | Уменьшает cascading delays в busy season. |
| farmcoopops.reservation.no_show | no-show rule | DECISION_RULE | No-show фиксируют и могут штрафовать или снижать priority. | Делает schedule честным для других участников. |
| farmcoopops.reservation.extension_request | extension request | METHOD | Продление booking требует подтверждения coordinator и проверки следующих reservations. | Балансирует реальную полевую задержку и права следующего member. |
| farmcoopops.dispatch.checkout | equipment checkout | METHOD | Checkout фиксирует состояние, hours, attachments, fuel, manuals, safety items и photos. | Создает baseline до передачи оборудования. |
| farmcoopops.dispatch.return_checkin | equipment return check-in | METHOD | Return check сравнивает состояние, hours, cleaning, fuel, damage и missing parts. | Быстро выявляет responsibility и maintenance needs. |
| farmcoopops.dispatch.key_control | key control | RECORD | Keys, fobs и locks выдают по журналу с time, user и equipment ID. | Предотвращает unauthorized use и потерю assets. |
| farmcoopops.dispatch.attachment_match | attachment match | QUALITY_CHECK | Attachments сверяют по model, hitch, PTO, hydraulics, pins и guards. | Несовместимость часто ломает equipment до начала работы. |
| farmcoopops.training.orientation | member orientation | METHOD | Orientation объясняет rules, reservations, safety, cleaning, reporting и billing. | Новые users понимают cooperative process, а не учатся через mistakes. |
| farmcoopops.training.machine_specific | machine-specific training | METHOD | Для каждой машины дают controls, hazards, startup, field settings, shutdown и transport mode. | Generic training недостаточен для specialized implements. |
| farmcoopops.training.refresher | refresher training | DECISION_RULE | Refresher требуют после long gap, incident, new model или repeated misuse. | Возвращает skill level до acceptable risk. |
| farmcoopops.training.signoff | training signoff | RECORD | Signoff хранит trainer, trainee, equipment, date, checklist и restrictions. | Нужен для insurance, accountability и scheduler permissions. |
| farmcoopops.safety.preop_inspection | pre-operation inspection | SAFETY_RULE | Перед use проверяют guards, tires, hydraulics, lights, hitch, PTO, leaks и emergency stop. | Предотвращает работу на equipment с явным дефектом. |
| farmcoopops.safety.pto_guard | PTO guard | SAFETY_RULE | PTO shields должны быть на месте и не заклинивать. | Открытый PTO является high-severity entanglement hazard. |
| farmcoopops.safety.lockout | maintenance lockout | SAFETY_RULE | Maintenance выполняют при выключенной энергии, lowered implements и secured movement. | Снижает риск crush, hydraulic release и unexpected start. |
| farmcoopops.safety.transport_lights | transport lights | SAFETY_RULE | Road transport требует lights, SMV emblem, secure load, width awareness и brakes where needed. | Уменьшает риск road incident при перемещении между farms. |
| farmcoopops.transport.trailer_assignment | trailer assignment | METHOD | Для equipment назначают подходящий trailer по weight, width, tie-down points и tow vehicle. | Неправильный trailer создает legal и safety risk. |
| farmcoopops.transport.load_securement | load securement | SAFETY_RULE | Машину крепят chains/straps по rated points, с учетом movement и legal requirements. | Предотвращает shifting или loss of load on road. |
| farmcoopops.transport.route_check | route check | METHOD | Маршрут проверяют по bridges, low wires, road limits, turns, mud и access gates. | Снижает stuck equipment и дорожные повреждения. |
| farmcoopops.transport.delivery_handoff | delivery handoff | RECORD | Handoff фиксирует location, receiver, condition, time, attachments и photos. | Нужен, когда equipment перемещает не сам borrower. |
| farmcoopops.maintenance.pm_schedule | preventive maintenance schedule | METHOD | PM schedule задает service by hours, calendar, season start/end и manufacturer guidance. | Shared equipment изнашивается предсказуемо только при дисциплине service. |
| farmcoopops.maintenance.grease_log | grease log | RECORD | Grease points и intervals отмечают после use или service. | Простая запись предотвращает bearing failures. |
| farmcoopops.maintenance.wear_parts | wear parts inventory | RECORD | Blades, belts, pins, filters, teeth, bearings и shear bolts держат как critical spares. | Сокращает downtime в peak season. |
| farmcoopops.maintenance.cleaning_standard | cleaning standard | QUALITY_CHECK | Cleaning removes soil, crop residue, manure, seeds и chemical traces per equipment type. | Снижает biosecurity, weed spread и corrosion risks. |
| farmcoopops.maintenance.offseason_storage | offseason storage | METHOD | Storage включает wash, dry, lubrication, battery care, tire support, covers и rodent control. | Увеличивает срок службы и снижает spring startup failures. |
| farmcoopops.damage.damage_report | damage report | RECORD | Damage report фиксирует what happened, operator, time, conditions, photos и immediate action. | Быстрая прозрачность лучше скрытой поломки перед следующим user. |
| farmcoopops.damage.root_cause | root cause review | METHOD | Причину разбирают как misuse, wear, training gap, design issue, maintenance lapse или accident. | Позволяет исправить систему, а не только выставить счет. |
| farmcoopops.damage.repair_authorization | repair authorization | DECISION_RULE | Repairs above threshold require coordinator, board или insurance approval. | Контролирует расходы и предотвращает unauthorized modifications. |
| farmcoopops.damage.downtime_notice | downtime notice | METHOD | При поломке scheduler сразу уведомляет affected reservations и предлагает alternatives. | Снижает cascade losses для участников. |
| farmcoopops.billing.hour_meter | hour meter billing | MEASUREMENT | Billing может основываться на engine hours, acre counter, day rate или use category. | Справедливый метод зависит от equipment и износа. |
| farmcoopops.billing.damage_deposit | damage deposit | RECORD | Deposit или reserve покрывает deductibles, cleaning failures и minor repairs. | Кооператив не теряет cash flow после small incidents. |
| farmcoopops.billing.invoice_cycle | invoice cycle | METHOD | Invoices формируют по completed bookings, rates, fees, penalties, taxes и credits. | Регулярный цикл удерживает финансовую устойчивость. |
| farmcoopops.billing.nonpayment_hold | nonpayment hold | DECISION_RULE | Просроченные balances могут блокировать future reservations после notice. | Защищает cooperative от free-riding. |
| farmcoopops.records.asset_register | asset register | RECORD | Register хранит equipment ID, serial, purchase date, grant restrictions, value, insurance и location. | Это основа для audit, depreciation и replacement planning. |
| farmcoopops.records.usage_history | usage history | RECORD | Usage history связывает operator, field, hours, crop, conditions и issues. | Помогает видеть wear patterns и training needs. |
| farmcoopops.records.insurance_certificate | insurance certificate | RECORD | Insurance documents хранят coverage, exclusions, operator requirements и claim process. | Позволяет быстро реагировать после incident. |
| farmcoopops.records.grant_compliance | grant compliance | CONSTRAINT | Оборудование, купленное на grant, может иметь rules по users, reporting, fees и disposal. | Нарушение условий может привести к repayment. |
| farmcoopops.governance.replacement_plan | replacement plan | MODEL | Replacement планирует срок службы, repair cost trend, utilization и reserve balance. | Кооператив избегает внезапной потери ключевой машины. |
| farmcoopops.governance.conflict_resolution | conflict resolution | METHOD | Споры по schedule, damage, billing и access разбирают через documented process. | Shared assets требуют процедур, иначе доверие быстро падает. |
| farmcoopops.governance.utilization_review | utilization review | QUALITY_CHECK | Board регулярно смотрит hours, cancellations, downtime, waitlists и financial performance. | Помогает решить: купить еще, продать лишнее или изменить rates. |

