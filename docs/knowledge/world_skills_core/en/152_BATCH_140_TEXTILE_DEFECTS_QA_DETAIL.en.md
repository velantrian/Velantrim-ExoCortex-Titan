# BATCH_140 — Textile Defects & Quality Assurance Detail
# world_skills_core · source: world_skills_core:batch_140:textile_defects_qa
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| textqa.fiber.fineness | Fiber fineness | invariant | Тонкость волокна влияет на мягкость, пряжу, прочность, покрытие и ощущение ткани. | сырье задаёт качество |
| textqa.fiber.length_uniformity | Fiber length uniformity | invariant | Равномерность длины волокон влияет на обрывность пряжи, ворсистость и стабильность процесса прядения. | контроль партии волокна |
| textqa.fiber.moisture_regain | Moisture regain | variant | Влагосодержание волокна влияет на массу, электризацию, переработку и ощущение материала. | важна кондиционировка |
| textqa.spinning.yarn_count | Yarn count | invariant | Номер пряжи описывает толщину нити и должен соответствовать конструкции ткани или трикотажа. | спецификация материала |
| textqa.spinning.twist_level | Yarn twist level | invariant | Крутка пряжи влияет на прочность, мягкость, ворсистость, усадку и внешний вид ткани. | баланс прочности и hand feel |
| textqa.spinning.thick_thin_places | Thick and thin places | invariant | Утолщения и утонения пряжи создают визуальные дефекты, слабые места и неравномерность ткани. | контроль Uster |
| textqa.spinning.neps | Neps | invariant | Neps — мелкие узелки волокон или загрязнений, которые ухудшают внешний вид и окрашивание ткани. | дефект сырья или процесса |
| textqa.spinning.yarn_hairiness | Yarn hairiness | variant | Ворсистость пряжи влияет на пилинг, мягкость, пыль, окрашивание и поведение при ткачестве. | процесс и финиш |
| textqa.weaving.broken_end | Broken end | invariant | Broken end в ткачестве создает продольный дефект из-за обрыва нити основы. | обнаружение на станке |
| textqa.weaving.broken_pick | Broken pick | invariant | Broken pick создает поперечный дефект из-за обрыва уточной нити. | видимый дефект ткани |
| textqa.weaving.mispick | Mispick | variant | Mispick возникает, когда уточная нить проложена неправильно или пропущена. | дефект структуры |
| textqa.weaving.float | Yarn float | invariant | Float появляется, когда нить проходит поверх слишком многих пересечений из-за ошибки переплетения. | зацепы и слабое место |
| textqa.weaving.reed_mark | Reed mark | variant | Reed mark выглядит как полосы по основе из-за проблем берда, заправки или неравномерного распределения нитей. | наладка ткацкого станка |
| textqa.knitting.dropped_stitch | Dropped stitch | invariant | Dropped stitch в трикотаже возникает, когда петля не удержана и распускается вниз по полотну. | критичный дефект |
| textqa.knitting.laddering | Laddering | invariant | Laddering — дорожка распускания петель, которая часто начинается с dropped stitch или повреждения нити. | прочность трикотажа |
| textqa.knitting.barre | Barre | variant | Barre проявляется полосами в трикотаже из-за различий пряжи, натяжения, окрашивания или машинных настроек. | визуальная неоднородность |
| textqa.knitting.spirality | Spirality | variant | Spirality — перекос трикотажа после стирки или отделки из-за крутки пряжи и структуры вязания. | швы уходят в сторону |
| textqa.dyeing.shade_variation | Shade variation | invariant | Разнотоновость возникает, когда партии или участки ткани отличаются по цвету из-за рецепта, температуры, времени или подготовки. | контроль цвета |
| textqa.dyeing.listing | Listing defect | variant | Listing — разница оттенка между краями и центром ткани при окрашивании или отделке. | контроль ширины процесса |
| textqa.dyeing.crocking | Crocking | invariant | Crocking — перенос красителя с ткани на другую поверхность при сухом или влажном трении. | стойкость окраски |
| textqa.dyeing.colorfastness_wash | Wash colorfastness | invariant | Стойкость окраски к стирке показывает, насколько ткань сохраняет цвет и не окрашивает соседние материалы. | требования ухода |
| textqa.dyeing.metamerism | Metamerism | variant | Metamerism возникает, когда два цвета совпадают при одном освещении, но отличаются при другом. | проверять под разным светом |
| textqa.finishing.shrinkage | Fabric shrinkage | invariant | Усадка ткани после стирки или отделки меняет размеры изделия и должна учитываться в лекалах и спецификации. | размерная стабильность |
| textqa.finishing.skew | Fabric skew | invariant | Skew — диагональное смещение нитей или петель относительно края ткани. | перекос изделия |
| textqa.finishing.bowing | Fabric bowing | variant | Bowing — дугообразное искривление уточных нитей или рисунка по ширине ткани. | проблемы раскроя |
| textqa.finishing.pilling | Pilling | invariant | Pilling образует катышки из-за истирания, миграции волокон и недостаточного удержания волокон в структуре. | долговечность внешнего вида |
| textqa.finishing.handfeel | Hand feel | variant | Hand feel описывает тактильное восприятие ткани и зависит от волокна, пряжи, переплетения, отделки и химии. | субъективное, но управляемое |
| textqa.garment.seam_slippage | Seam slippage | invariant | Seam slippage возникает, когда нити ткани расходятся у шва под нагрузкой. | прочность одежды |
| textqa.garment.seam_puckering | Seam puckering | variant | Seam puckering — морщины вдоль шва из-за натяжения нитей, усадки, иглы, подачи или конструкции. | внешний вид изделия |
| textqa.garment.stitch_density | Stitch density | invariant | Плотность стежков влияет на прочность шва, эластичность, внешний вид и риск повреждения ткани. | настройка швейной операции |
| textqa.garment.needle_damage | Needle damage | invariant | Повреждение иглой создает отверстия, затяжки или разрывы волокон при неправильной игле, скорости или ткани. | подбор иглы |
| textqa.garment.fit_spec | Garment fit specification | variant | Спецификация посадки связывает мерки изделия, допуски, модель тела и ожидаемую свободу облегания. | размерная сетка |
| textqa.inspection.aql | AQL inspection | variant | AQL определяет выборочный план приемки партии с допустимым уровнем дефектов, но не гарантирует отсутствие дефектов. | риск выборочного контроля |
| textqa.inspection.four_point_system | Four-point fabric inspection | invariant | Four-point system оценивает дефекты ткани баллами по размеру и рассчитывает качество на единицу площади. | приемка рулонов |
| textqa.inspection.defect_map | Fabric defect map | invariant | Карта дефектов рулона показывает тип, место и частоту дефектов для раскроя, претензий и анализа процесса. | меньше отходов |
| textqa.inspection.gold_sample | Textile gold sample | variant | Gold sample фиксирует согласованный цвет, руку, внешний вид или конструкцию как эталон для сравнения. | избежать споров |
| textqa.testing.tensile_strength | Textile tensile strength | invariant | Разрывная прочность ткани или пряжи измеряет сопротивление растяжению до разрушения. | базовая механика |
| textqa.testing.tear_strength | Tear strength | invariant | Прочность на раздирание показывает сопротивление распространению разрыва после начального повреждения. | рабочая одежда и ткани |
| textqa.testing.abrasion_resistance | Abrasion resistance | invariant | Стойкость к истиранию показывает способность ткани сохранять структуру и внешний вид при трении. | мебель, одежда, сумки |
| textqa.testing.dimensional_stability | Dimensional stability | invariant | Размерная стабильность оценивает изменение размеров после стирки, сушки, пара или эксплуатации. | посадка после ухода |
| textqa.testing.seam_strength | Seam strength test | invariant | Испытание прочности шва оценивает разрушение ниток, ткани или раскрытие шва под нагрузкой. | качество пошива |
| textqa.traceability.roll_id | Fabric roll ID | invariant | Идентификатор рулона связывает ткань с партией, поставщиком, результатами инспекции и раскроем. | traceability в производстве |
| textqa.traceability.bundle_tracking | Bundle tracking | variant | Bundle tracking отслеживает пачки кроя через швейные операции, контроль и упаковку. | не терять детали |
| textqa.corrective.root_cause | Textile defect root cause | invariant | Корневая причина текстильного дефекта может быть в сырье, машине, настройке, операторе, химии, среде или хранении. | исправлять источник |
