# BATCH 309: Soil Conservation District Operations

**KnowledgeUnits:** 44  
**Namespace:** `soildistrictops.*`  
**Scope:** landowner requests, site visits, plans, cost-share, practices, inspections, reporting.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| soildistrictops.intake.landowner_request | request landowner | RECORD | Заявка фиксирует parcel, contact, concern, land use, urgency и requested assistance. | Создает официальный старт работы и предотвращает потерю обращений. |
| soildistrictops.intake.issue_triage | triage soil issue | DECISION_RULE | Запросы сортируют по erosion, drainage, nutrient runoff, livestock access, drought, compliance или funding deadlines. | Помогает направить специалиста и не пропустить срочные риски. |
| soildistrictops.intake.eligibility_screen | eligibility screen | QUALITY_CHECK | Проверяют location, land status, program rules, previous funding и required documents. | Экономит время до полевого выезда и снижает rejected applications. |
| soildistrictops.intake.confidentiality | producer confidentiality | SAFETY_RULE | Данные владельца и хозяйства обрабатывают по правилам privacy и program confidentiality. | Повышает доверие и снижает legal risk. |
| soildistrictops.sitevisit.previsit_map | pre-visit map review | METHOD | До выезда смотрят soils, slope, waterways, aerial imagery, parcels, drainage и prior projects. | Field visit становится точнее и короче. |
| soildistrictops.sitevisit.landowner_interview | interview landowner | METHOD | На месте уточняют management history, crop rotation, grazing, drainage, failures и goals. | Техническое решение связывается с реальной практикой владельца. |
| soildistrictops.sitevisit.erosion_observation | erosion observation | OBSERVATION | Фиксируют sheet, rill, gully, bank erosion, sediment deposition и bare soil. | Определяет тип practice: cover, grade, waterway, buffer или structure. |
| soildistrictops.sitevisit.drainage_path | drainage path tracing | METHOD | Полевой обход отслеживает flow paths, outlets, ponding, tile outlets и road ditches. | Помогает не лечить симптом выше или ниже реального источника. |
| soildistrictops.sitevisit.soil_probe | soil probe check | MEASUREMENT | Проба soil profile показывает texture, compaction, moisture, restrictive layers и organic matter signs. | Уточняет feasibility infiltration, planting и equipment access. |
| soildistrictops.sitevisit.photo_evidence | site photo evidence | RECORD | Фотографии привязывают к location, direction, issue и date. | Нужны для plan, cost-share, inspection и before-after comparison. |
| soildistrictops.planning.resource_concern | resource concern | MODEL | Resource concern формулирует проблему почвы, воды, воздуха, растений, животных или энергии. | Держит план на outcome, а не на случайный список работ. |
| soildistrictops.planning.practice_suite | practice suite | METHOD | Несколько practices комбинируют: cover crop, buffer, grassed waterway, terrace, nutrient plan. | Одна мера редко решает всю систему runoff и erosion. |
| soildistrictops.planning.design_standard | design standard | CONSTRAINT | Технические practices проектируют по действующим standards, slope, flow, soils и equipment needs. | Снижает риск failure и funding noncompliance. |
| soildistrictops.planning.owner_objectives | owner objectives | RECORD | План фиксирует production goals, labor limits, equipment, cash flow и tolerance for change. | Увеличивает шанс, что practice будет реально поддерживаться. |
| soildistrictops.planning.alternative_analysis | alternatives analysis | METHOD | В plan сравнивают несколько вариантов по cost, benefit, maintenance, eligibility и risk. | Помогает принять обоснованное решение, а не навязать одну меру. |
| soildistrictops.planning.operation_maintenance | operation maintenance plan | RECORD | O&M описывает inspections, mowing, sediment removal, repairs и prohibited actions. | Conservation practice работает годами только при понятном уходе. |
| soildistrictops.costshare.application_packet | application packet | RECORD | Пакет включает forms, maps, estimates, eligibility, signatures и planned practices. | Ускоряет approval и audit readiness. |
| soildistrictops.costshare.ranking_score | ranking score | MODEL | Заявки ранжируют по environmental benefit, risk, readiness, equity, watershed priority и cost-effectiveness. | Средства идут туда, где ожидаемый результат выше. |
| soildistrictops.costshare.match_requirement | match requirement | CONSTRAINT | Некоторые программы требуют долю владельца деньгами, labor или materials. | Нужно заранее проверять, сможет ли заявитель выполнить условия. |
| soildistrictops.costshare.preapproval_rule | preapproval before work | SAFETY_RULE | Работы нельзя начинать до written approval, если program rules это требуют. | Иначе project может потерять reimbursement. |
| soildistrictops.costshare.change_order | conservation change order | METHOD | Изменения scope, quantity, location или design оформляют до выполнения. | Защищает владельца и district от unpaid или noncompliant work. |
| soildistrictops.practice.cover_crop | cover crop practice | METHOD | Cover crop закрывает почву, удерживает nutrients и улучшает structure между cash crops. | Снижает erosion и runoff в межсезонье. |
| soildistrictops.practice.grassed_waterway | grassed waterway | METHOD | Grassed waterway стабилизирует concentrated flow в ложбинах. | Предотвращает рост gullies и вынос sediment. |
| soildistrictops.practice.riparian_buffer | riparian buffer | METHOD | Riparian buffer фильтрует runoff и защищает streambanks. | Улучшает water quality и habitat вдоль водотока. |
| soildistrictops.practice.terrace | terrace practice | METHOD | Terrace сокращает длину склона и перенаправляет runoff безопасным путем. | Уменьшает скорость воды и sheet/rill erosion. |
| soildistrictops.practice.nutrient_plan | nutrient management plan | METHOD | План nutrients связывает soil tests, crop needs, timing, placement и setbacks. | Снижает потери nitrogen/phosphorus и расходы на fertilizer. |
| soildistrictops.practice.livestock_exclusion | livestock exclusion | METHOD | Fencing и crossings ограничивают доступ скота к stream или wet area. | Уменьшает bank erosion, bacteria и sediment. |
| soildistrictops.practice.conservation_tillage | conservation tillage | METHOD | Минимальная обработка сохраняет residue cover и снижает disturbance. | Помогает удерживать moisture и уменьшить erosion. |
| soildistrictops.inspection.preconstruction | preconstruction meeting | METHOD | До работ contractor, owner и district сверяют layout, specs, utilities, access и weather constraints. | Снижает field changes и construction mistakes. |
| soildistrictops.inspection.during_work | inspection during work | INSPECTION | Во время работ проверяют grades, materials, dimensions, compaction и erosion controls. | Ошибки дешевле исправлять до завершения. |
| soildistrictops.inspection.final_certification | final certification | QUALITY_CHECK | Завершенный practice сравнивают с design, quantities, photos и as-built notes. | Нужно для payment, compliance и будущего maintenance. |
| soildistrictops.inspection.maintenance_check | maintenance check | INSPECTION | После сезонов проверяют vegetation, sediment, erosion, animal damage и structure condition. | Ранний repair сохраняет вложения программы. |
| soildistrictops.inspection.failure_documentation | documentation failure | RECORD | Failure notes включают cause, severity, weather event, owner actions и recommended fix. | Помогает учиться и защищать program integrity. |
| soildistrictops.reporting.project_closeout | project closeout | METHOD | Closeout собирает certification, invoices, maps, photos, payment records и O&M handoff. | Делает project complete для владельца, funder и audit. |
| soildistrictops.reporting.practice_inventory | practice inventory | RECORD | District ведет inventory practices по type, location, installed year, acres, status и funding. | Позволяет видеть portfolio и планировать maintenance outreach. |
| soildistrictops.reporting.outcome_metrics | outcome metrics | MODEL | Метрики включают treated acres, sediment reduction estimates, nutrient savings, habitat acres и participants. | Объясняют общественную ценность программы. |
| soildistrictops.reporting.board_report | board report | RECORD | Board report суммирует requests, approvals, spending, field work, partnerships и risks. | Дает oversight без погружения в каждое дело. |
| soildistrictops.reporting.gis_layer_update | GIS layer update | METHOD | После проекта GIS обновляют as-built geometry, attributes и linked records. | Следующие выезды начинают с актуальной карты. |
| soildistrictops.partner.referral_network | referral network | METHOD | District направляет владельца к extension, engineers, watershed groups, lenders или regulators. | Не все проблемы решаются одной организацией. |
| soildistrictops.partner.contractor_list | contractor list | RECORD | Список contractors поддерживают по practice type, service area, insurance и past performance. | Помогает владельцам найти исполнителя без endorsement риска. |
| soildistrictops.partner.workshop | landowner workshop | METHOD | Workshops объясняют programs, practices, deadlines, maintenance и common failures. | Массовое обучение снижает количество слабых заявок. |
| soildistrictops.admin.file_naming | file naming control | METHOD | Дела именуют по owner, parcel, program year, project ID и practice code. | Ускоряет поиск records и audit trail. |
| soildistrictops.admin.deadline_calendar | deadline calendar | RECORD | Календарь хранит application windows, board approvals, construction seasons, reporting и reimbursement dates. | Предотвращает пропуск funding milestones. |
| soildistrictops.admin.conflict_interest | conflict of interest | SAFETY_RULE | Board и staff раскрывают conflicts при funding decisions, contractor relationships или family parcels. | Защищает доверие к allocation public funds. |

