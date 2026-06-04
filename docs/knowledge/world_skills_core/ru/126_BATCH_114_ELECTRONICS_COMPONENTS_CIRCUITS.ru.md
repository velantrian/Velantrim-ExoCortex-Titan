# BATCH_114 — Electronics Components & Circuits Practical
# world_skills_core · source: world_skills_core:batch_114:electronics_components
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| ecomp.basic.voltage_current_resistance | Напряжение, ток, сопротивление | invariant | U=IR (закон Ома) | основа расчёта схем |
| ecomp.basic.power | Мощность P=UI | invariant | тепловыделение, нагрузка | выбор компонентов |
| ecomp.basic.series_parallel | Последовательно/параллельно | invariant | складываются R (посл.) или проводимости (парал.) | расчёт цепей |
| ecomp.basic.ac_dc | Переменный и постоянный ток | invariant | AC меняет направление, DC нет | питание |
| ecomp.basic.ground | Земля (общий провод) | invariant | опорный потенциал схемы | разводка |
| ecomp.resistor.function | Резистор | invariant | ограничивает ток, делит напряжение | базовый компонент |
| ecomp.resistor.color_code | Цветовая маркировка резисторов | variant | полосы = номинал и допуск | чтение номинала |
| ecomp.resistor.divider | Делитель напряжения | invariant | два резистора делят напряжение | датчики, опорные уровни |
| ecomp.capacitor.function | Конденсатор | invariant | накапливает заряд, блокирует DC, пропускает AC | фильтры, сглаживание |
| ecomp.capacitor.filter | Сглаживающий конденсатор | variant | убирает пульсации питания | блоки питания |
| ecomp.inductor.function | Катушка индуктивности | invariant | запасает энергию в магнитном поле | фильтры, дроссели |
| ecomp.diode.function | Диод | invariant | пропускает ток в одну сторону | выпрямление, защита |
| ecomp.diode.led | Светодиод (LED) | invariant | светится при прямом токе; нужен резистор | индикация, освещение |
| ecomp.diode.zener | Стабилитрон | variant | стабилизирует напряжение | опорное напряжение |
| ecomp.diode.rectifier | Выпрямитель (мост) | invariant | AC → DC через диоды | блоки питания |
| ecomp.transistor.function | Транзистор | invariant | усилитель и ключ | основа электроники |
| ecomp.transistor.bjt_mosfet | BJT и MOSFET | variant | биполярный (ток) vs полевой (напряжение) | выбор по задаче |
| ecomp.transistor.switch | Транзистор как ключ | invariant | включает нагрузку малым сигналом | управление |
| ecomp.ic.opamp | Операционный усилитель | variant | усиление, сравнение, фильтрация | аналоговые схемы |
| ecomp.ic.555 | Таймер 555 | variant | генерация импульсов и задержек | мигалки, генераторы |
| ecomp.ic.logic | Логические микросхемы | invariant | AND/OR/NOT в кремнии | цифровая логика |
| ecomp.ic.microcontroller | Микроконтроллер (MCU) | invariant | мини-компьютер на чипе (Arduino, ESP32) | управление устройствами |
| ecomp.ic.adc_dac | АЦП и ЦАП | invariant | аналог ↔ цифра | датчики, звук |
| ecomp.power.regulator | Стабилизатор напряжения | invariant | стабильное питание (7805, LDO) | питание схем |
| ecomp.power.battery | Батареи и аккумуляторы | variant | источники DC; ёмкость в мА·ч | питание устройств |
| ecomp.power.smps | Импульсный блок питания (SMPS) | variant | высокий КПД, компактность | зарядки, БП |
| ecomp.signal.digital_analog | Цифровой и аналоговый сигнал | invariant | дискретный vs непрерывный | обработка |
| ecomp.signal.pwm | ШИМ (PWM) | variant | управление мощностью шириной импульса | моторы, яркость, звук |
| ecomp.bus.uart | UART | variant | последовательный обмен двумя проводами | связь МК |
| ecomp.bus.i2c | I²C | variant | шина с адресами, два провода | датчики, дисплеи |
| ecomp.bus.spi | SPI | variant | быстрый последовательный обмен | память, дисплеи |
| ecomp.sensor.types | Датчики | invariant | температура, свет, движение, влажность | вход данных |
| ecomp.actuator.types | Исполнительные элементы | invariant | моторы, реле, сервоприводы | вывод действия |
| ecomp.relay.function | Реле | invariant | маломощный сигнал управляет сильной нагрузкой | развязка, коммутация |
| ecomp.pcb.basics | Печатная плата (PCB) | invariant | дорожки соединяют компоненты | основа устройств |
| ecomp.pcb.smd_tht | SMD и THT монтаж | variant | поверхностный vs выводной | сборка |
| ecomp.tool.multimeter | Мультиметр | invariant | измеряет U, I, R, прозвонку | диагностика схем |
| ecomp.tool.soldering | Пайка | invariant | соединение компонентов припоем | сборка, ремонт |
| ecomp.tool.oscilloscope | Осциллограф | variant | показывает форму сигнала во времени | отладка |
| ecomp.tool.breadboard | Макетная плата | variant | прототип без пайки | эксперименты |
| ecomp.safety.esd | Статика (ESD) | invariant | разряд губит чипы; заземление, браслет | защита компонентов |
| ecomp.safety.polarity | Соблюдение полярности | invariant | конденсаторы/диоды/питание чувствительны | защита от поломки |
| ecomp.safety.short | Короткое замыкание | invariant | прямой путь тока → перегрев | предохранители |
| ecomp.debug.method | Отладка схемы | invariant | проверка питания, земли, сигналов мультиметром | поиск неисправности |
