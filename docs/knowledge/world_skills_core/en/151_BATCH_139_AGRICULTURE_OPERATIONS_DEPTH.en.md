# BATCH_139 — Agriculture Operations Depth
# world_skills_core · source: world_skills_core:batch_139:agriculture_operations_depth
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| agopsd.soil.soil_test | Soil test | invariant | Анализ почвы измеряет pH, питательные элементы, органическое вещество и другие параметры для управляемого внесения удобрений. | не удобрять вслепую |
| agopsd.soil.ph_adjustment | Soil pH adjustment | variant | Коррекция pH почвы требует времени, дозы, буферной способности почвы и совместимости с культурой. | известкование не мгновенно |
| agopsd.soil.organic_matter | Soil organic matter | invariant | Органическое вещество почвы улучшает структуру, влагоудержание, биологическую активность и запас питательных элементов. | основа здоровья почвы |
| agopsd.soil.compaction | Soil compaction | invariant | Уплотнение почвы снижает пористость, инфильтрацию и рост корней, особенно после движения техники по влажному полю. | управлять трафиком техники |
| agopsd.soil.cover_crop | Cover crop | variant | Покровная культура защищает почву, снижает эрозию, добавляет биомассу или управляет сорняками между основными культурами. | межсезонная польза |
| agopsd.soil.crop_rotation | Crop rotation planning | invariant | Севооборот меняет культуры во времени, чтобы управлять вредителями, болезнями, питанием и структурой почвы. | не истощать поле |
| agopsd.nutrient.nitrogen_timing | Nitrogen timing | variant | Внесение азота должно учитывать фазу роста культуры, потери, погоду, почву и ожидаемую урожайность. | снизить потери и дефицит |
| agopsd.nutrient.phosphorus_runoff | Phosphorus runoff risk | invariant | Фосфорный сток усиливается при эрозии, насыщенной почве, неправильном времени внесения и близости водоемов. | защита воды |
| agopsd.nutrient.potassium_balance | Potassium balance | variant | Калийный баланс зависит от выноса урожаем, почвенного запаса, фиксации глинами и уровня урожайности. | не смотреть только N |
| agopsd.nutrient.manure_analysis | Manure nutrient analysis | invariant | Анализ навоза помогает оценить фактическое содержание питательных веществ и избежать недо- или перевнесения. | органическое удобрение тоже переменно |
| agopsd.irrigation.evapotranspiration | Evapotranspiration scheduling | invariant | Планирование полива по evapotranspiration оценивает потерю воды культурой и почвой между поливами. | поливать по потребности |
| agopsd.irrigation.soil_moisture_sensor | Soil moisture sensor | variant | Датчик влажности почвы помогает видеть доступную воду в корневой зоне, если установлен и интерпретирован правильно. | меньше стресс и перерасход |
| agopsd.irrigation.deficit_irrigation | Deficit irrigation | variant | Дефицитный полив сознательно допускает умеренный водный стресс в менее чувствительные фазы роста ради экономии воды. | требует знания культуры |
| agopsd.irrigation.uniformity | Irrigation uniformity | invariant | Равномерность полива показывает, насколько одинаково вода распределяется по полю или теплице. | часть растений не должна страдать |
| agopsd.irrigation.salt_leaching | Salt leaching | variant | Промывка солей требует достаточной воды и дренажа, иначе соли накапливаются в корневой зоне. | засоленные почвы |
| agopsd.pest.scouting_plan | Pest scouting plan | invariant | План обследования вредителей задаёт частоту, маршрут, пороги, метод подсчета и запись наблюдений. | видеть проблему до ущерба |
| agopsd.pest.economic_threshold | Economic threshold | invariant | Экономический порог вредителя показывает уровень, при котором ущерб вероятно превысит стоимость контроля. | не обрабатывать без причины |
| agopsd.pest.beneficial_insects | Beneficial insects | variant | Полезные насекомые могут снижать вредителей, поэтому контроль должен учитывать их сохранение. | IPM вместо тотального уничтожения |
| agopsd.pest.resistance_management | Pesticide resistance management | invariant | Управление устойчивостью вредителей требует ротации механизмов действия, правильных доз и неконтрольных методов. | сохранить эффективность средств |
| agopsd.pest.disease_triangle | Disease triangle | invariant | Болезнь растения развивается при сочетании восприимчивого хозяина, патогена и благоприятной среды. | искать разрыв треугольника |
| agopsd.weed.seed_bank | Weed seed bank | invariant | Банк семян сорняков в почве поддерживает будущие волны всходов даже после успешной обработки текущего сезона. | стратегия на годы |
| agopsd.weed.cover_canopy | Crop canopy weed suppression | variant | Быстрое закрытие рядов культурой снижает свет для сорняков и уменьшает их конкурентоспособность. | агротехника как контроль |
| agopsd.weed.herbicide_mode | Herbicide mode of action | invariant | Механизм действия гербицида должен учитываться при ротации, чтобы снизить риск устойчивости сорняков. | не повторять один механизм |
| agopsd.planting.seed_rate | Seed rate | variant | Норма высева зависит от культуры, всхожести, цели густоты, условий почвы и ожидаемых потерь. | не только кг на гектар |
| agopsd.planting.row_spacing | Row spacing | variant | Междурядье влияет на конкуренцию с сорняками, доступ техники, свет, вентиляцию и урожайность. | проектирование посева |
| agopsd.planting.seed_depth | Seed depth | invariant | Глубина заделки семян влияет на влагу, температуру, энергию проростка и равномерность всходов. | частая ошибка посева |
| agopsd.planting.germination_test | Germination test | invariant | Тест всхожести показывает долю семян, способных дать нормальный проросток при заданных условиях. | корректировать норму высева |
| agopsd.harvest.moisture_target | Harvest moisture target | variant | Целевая влажность при уборке зависит от культуры, способа хранения, риска потерь и возможностей сушки. | качество после уборки |
| agopsd.harvest.header_loss | Combine header loss | invariant | Потери жатки возникают до обмолота и зависят от высоты среза, скорости, состояния культуры и настройки оборудования. | найти место потерь |
| agopsd.harvest.threshing_damage | Threshing damage | invariant | Повреждение зерна при обмолоте растет при неправильной скорости, зазоре, влажности или агрессивной настройке. | качество и хранение |
| agopsd.harvest.field_loss_check | Field loss check | variant | Проверка потерь в поле сравнивает зерно до и после комбайна, чтобы отделить естественное осыпание от машинных потерь. | настройка уборки |
| agopsd.storage.grain_drying | Grain drying | invariant | Сушка зерна снижает влажность до уровня, при котором уменьшается риск плесени, нагрева и порчи. | хранение без потерь |
| agopsd.storage.aeration | Grain aeration | invariant | Аэрация зерна выравнивает температуру и влажность массы, снижая риск конденсации и горячих зон. | силосы и бункеры |
| agopsd.storage.hotspot_monitoring | Grain hotspot monitoring | variant | Горячая зона в зерне может указывать на влажность, насекомых, плесень или дыхание зерна. | раннее вмешательство |
| agopsd.storage.fumigation_safety | Storage fumigation safety | variant | Фумигация хранилища требует обученного персонала, герметизации, экспозиции, вентиляции и строгого контроля доступа. | опасная операция |
| agopsd.quality.grade_standard | Crop grade standard | invariant | Класс качества урожая определяется показателями вроде влажности, примесей, повреждений, массы и специфических дефектов культуры. | цена зависит от качества |
| agopsd.quality.foreign_material | Foreign material control | invariant | Контроль примесей снижает риск порчи, штрафов, повреждения оборудования и отказа покупателя. | чистка после уборки |
| agopsd.quality.mycotoxin_risk | Mycotoxin risk | variant | Риск микотоксинов зависит от культуры, погоды, повреждений, патогенов, влажности и условий хранения. | проверка безопасности |
| agopsd.quality.traceability_lot | Farm lot traceability | invariant | Партийная прослеживаемость связывает поле, дату, обработки, уборку, хранение и продажу урожая. | recall и premium markets |
| agopsd.equipment.calibration_sprayer | Sprayer calibration | invariant | Калибровка опрыскивателя связывает расход форсунок, скорость, давление и ширину захвата с фактической нормой внесения. | точная обработка |
| agopsd.equipment.nozzle_selection | Nozzle selection | variant | Выбор форсунки влияет на размер капли, покрытие, drift, давление и совместимость с препаратом. | качество опрыскивания |
| agopsd.equipment.drift_management | Spray drift management | invariant | Drift уменьшают через погоду, буферные зоны, высоту штанги, размер капли, скорость и правильную технику. | защита соседей и природы |
| agopsd.equipment.maintenance_log | Farm equipment maintenance log | invariant | Журнал обслуживания техники фиксирует часы, работы, детали, неисправности и ответственного. | меньше простоев в сезон |
| agopsd.decision.field_record | Field record | invariant | Полевой журнал связывает поле, культуру, операции, материалы, погоду, наблюдения и результаты сезона. | память хозяйства |
