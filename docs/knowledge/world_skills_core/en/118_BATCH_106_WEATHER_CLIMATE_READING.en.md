# BATCH_106 — Weather & Climate Reading: Forecasts, Instruments, Local Signs
# world_skills_core · source: world_skills_core:batch_106:weather_reading
# KnowledgeUnits: 42

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| wxread.basic.weather_climate | Погода vs климат | invariant | погода — сейчас; климат — статистика за годы | разные горизонты |
| wxread.basic.atmosphere | Атмосфера и тропосфера | invariant | погода формируется в нижнем слое | где «живёт» погода |
| wxread.pressure.high_low | Высокое и низкое давление | invariant | высокое → ясно/сухо; низкое → облака/осадки | прогноз по барометру |
| wxread.pressure.barometer | Барометр | invariant | измеряет атмосферное давление | падает → ухудшение погоды |
| wxread.pressure.trend | Тенденция давления | invariant | важна динамика, не абсолют | рост → улучшение |
| wxread.temp.thermometer | Термометр | invariant | измеряет температуру воздуха | базовый параметр |
| wxread.temp.feels_like | Ощущаемая температура | variant | ветер/влажность меняют ощущение | одежда по погоде |
| wxread.temp.windchill | Ветро-холодовой индекс | variant | ветер усиливает ощущение холода | риск обморожения |
| wxread.temp.heat_index | Индекс жары | variant | влажность усиливает ощущение жары | риск теплового удара |
| wxread.humidity.relative | Относительная влажность | invariant | % насыщения воздуха паром | комфорт, осадки |
| wxread.humidity.dewpoint | Точка росы | invariant | температура конденсации; высокая → душно | туман, роса |
| wxread.humidity.hygrometer | Гигрометр | variant | измеряет влажность | микроклимат |
| wxread.wind.direction | Направление ветра | invariant | откуда дует; смена → смена погоды | прогноз фронтов |
| wxread.wind.speed | Скорость ветра | invariant | измеряется анемометром; шкала Бофорта | безопасность, осадки |
| wxread.wind.beaufort | Шкала Бофорта | variant | оценка ветра по видимым признакам | без приборов |
| wxread.clouds.cumulus | Кучевые облака | variant | «вата»; хорошая погода или развитие грозы | индикатор |
| wxread.clouds.stratus | Слоистые облака | variant | сплошная серая пелена → морось | пасмурно |
| wxread.clouds.cirrus | Перистые облака | variant | высокие «перья» → приближение фронта | погода изменится через ~сутки |
| wxread.clouds.cumulonimbus | Кучево-дождевые (гроза) | invariant | мощная вертикальная облачность → ливень, гроза, град | укрытие |
| wxread.fronts.cold | Холодный фронт | invariant | резкая смена, ливни, прояснение после | быстрые изменения |
| wxread.fronts.warm | Тёплый фронт | invariant | постепенное потепление, затяжные осадки | долгий дождь |
| wxread.precip.types | Виды осадков | invariant | дождь, снег, град, морось, ледяной дождь | подготовка |
| wxread.precip.formation | Как образуются осадки | invariant | конденсация → рост капель → выпадение | понимание прогноза |
| wxread.storm.thunder | Гроза и молния | invariant | электрический разряд; гром — звук | правила безопасности |
| wxread.storm.lightning_safety | Безопасность при молнии | invariant | в помещение/машину; не под одиноким деревом | спасение жизни |
| wxread.storm.distance | Расстояние до грозы | variant | задержка грома: ~3 сек = 1 км | оценка приближения |
| wxread.storm.hail | Град | variant | замёрзшие осадки из грозовых облаков | укрытие техники |
| wxread.storm.tornado | Смерч/торнадо | variant | вращающийся столб; укрытие в низком прочном месте | выживание |
| wxread.fog.formation | Туман | variant | конденсация у земли; снижает видимость | осторожность на дороге |
| wxread.forecast.reading | Чтение прогноза | invariant | вероятность осадков, температура, ветер | планирование дня |
| wxread.forecast.probability | Вероятность осадков (%) | variant | шанс осадков в районе/времени | интерпретация |
| wxread.forecast.radar | Метеорадар | variant | показывает осадки в реальном времени | краткосрочный прогноз |
| wxread.forecast.satellite | Спутниковые снимки | variant | облачность и фронты сверху | крупная картина |
| wxread.forecast.sources | Источники прогноза | invariant | метеослужбы, приложения, модели | надёжность данных |
| wxread.signs.red_sky | Народные приметы | variant | «красное небо вечером» и т.п. — частично основаны на физике | грубый ориентир |
| wxread.signs.animals | Поведение животных и погода | variant | низкий полёт птиц, активность — связаны с давлением | вспомогательный признак |
| wxread.season.cycle | Времена года | invariant | наклон оси Земли, не расстояние до Солнца | сезонная погода |
| wxread.climate.zones | Климатические зоны | invariant | тропики, умеренные, полярные | ожидаемая погода региона |
| wxread.hazard.heatwave | Аномальная жара | variant | гидратация, прохлада, риск для уязвимых | защита здоровья |
| wxread.hazard.coldwave | Аномальный холод | variant | обморожение, отопление, одежда слоями | безопасность |
| wxread.hazard.flood_warning | Предупреждения о наводнении | invariant | реагировать на штормовые предупреждения | эвакуация |
| wxread.measure.station | Домашняя метеостанция | variant | датчики давления, температуры, влажности | локальный прогноз |
