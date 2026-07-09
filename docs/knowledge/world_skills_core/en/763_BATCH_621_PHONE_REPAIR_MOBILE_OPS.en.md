# BATCH 621: Phone Repair — Mobile Device Operations

**KnowledgeUnits:** 50
**Namespace:** `phonerepair.ops.*`
**Scope:** screen, battery, charging_port, diagnostics, microsoldering, water_damage

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| phonerepair.ops.screen_assembly_heat | Screen Replacement — Heat & Adhesive | METHOD | Замена экрана. Инструменты: heat plate (70-80°C 2-3 мин), suction cup, plastic pry tools, isopropyl alcohol 99%. Процесс: power off, heat perimeter, suction cup + pick, обвести по периметру (осторожно — ribbon cables!), откинуть экран. Отсоединить battery всегда первым. Transfer компоненты: Touch ID flex крайне осторожно — обрыв = не работает навсегда. New adhesive (pre-cut strips), новый экран, battery, закрыть. Тест: touch, display, Face ID. | Face ID: повреждение dot projector = Face ID не работает. НЕ ковырять там! |
| phonerepair.ops.battery_replacement_safe | Battery — Safe Removal | METHOD | Замена аккумулятора. Pull tabs: нагреть заднюю крышку 50-60°C. Медленно, равномерно тянуть. Если порвались — isopropyl alcohol под батарею, пластиковый spudger (не металл — прокол = fire!). После замены не-genuine батареи — сообщение "Unable to verify". Решение: перепайка BMS со старой батареи. | Li-ion прокол: дым, fire. Ведро песка (не воды!) на случай возгорания. |
| phonerepair.ops.water_damage_triage | Water Damage — Emergency Triage | METHOD | Спасение утопленного телефона. Сразу ВЫКЛЮЧИТЬ, не заряжать! Промыть изопропиловым спиртом 99%, щётка очистить коррозию, ультразвуковая ванна со спиртом. Сушка 50°C 24 часа. Замена компонентов с видимой коррозией. Солёная вода гораздо агрессивнее. | Категорически НЕ сушить феном в корпусе — загоняет влагу глубже. Рис — миф. |
| phonerepair.ops.microsoldering_connector | Microsoldering — Connector Replacement | METHOD | Пайка микро-компонентов. Оборудование: stereo microscope 10-40x, hot air station, fine-tip soldering iron, flux Amtech NC-559. Замена FPC connector: hot air 350°C airflow 30-40%, удалить старый, очистить pads, solder paste, установить новый. Jump wire: если pad оторван — эмалированная проволока 0.02 мм. | Практика на donor boards. |
