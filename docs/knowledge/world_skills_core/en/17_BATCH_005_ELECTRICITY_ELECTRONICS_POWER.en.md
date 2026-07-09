# ⚡ Batch 005 — Electricity, Electronics, Power & Computing

**Язык:** русский  
**Статус:** 50K batch 005 / seed units / не L3 truth  
**Цель:** расширить practical-базу по электричеству, электронике, датчикам, питанию, батареям, сетям, микросхемам, вычислениям и безопасности.

---

## 📦 Knowledge Units

| ID | Тип | Суть | Условия / границы | Связи |
|---|---|---|---|---|
| `elec.safety.voltage_current` | DISTINCTION | Напряжение создаёт возможность тока, а ток через тело опасен. | Опасность зависит от пути, длительности, условий кожи, энергии. | electrical_safety |
| `elec.cable.copper_aluminum` | MATERIAL | Медь проводит лучше алюминия, но дороже и тяжелее. | Соединение Cu/Al требует правильных клемм из-за коррозии/тепла. | wiring |
| `elec.cable.insulation_rating` | CONSTRAINT | Изоляция кабеля имеет допустимое напряжение, температуру и среду. | Неверный кабель создаёт пожарный риск. | construction.electrical |
| `elec.connector.contact_resistance` | FAILURE_MODE | Плохой контакт повышает сопротивление и нагрев. | Может привести к пожару или отказу. | maintenance |
| `elec.resistor.color_code` | METHOD | Цветовые полосы резистора кодируют номинал и допуск. | SMD-компоненты используют другую маркировку. | electronics |
| `elec.capacitor.polarity` | SAFETY_RULE | Полярные конденсаторы нельзя включать с обратной полярностью. | Возможен нагрев, утечка, взрыв. | electronics |
| `elec.inductor.core_saturation` | FAILURE_MODE | Сердечник индуктивности насыщается при слишком большом токе. | Индуктивность падает, ток растёт. | power |
| `elec.diode.rectifier` | COMPONENT | Диодный выпрямитель превращает AC в пульсирующий DC. | Нужны фильтрация и учёт падения напряжения. | power_supply |
| `elec.led.current_limit` | SAFETY_RULE | LED требует ограничения тока. | Прямое подключение к источнику напряжения может сжечь LED. | electronics |
| `elec.zener_regulation` | COMPONENT | Стабилитрон поддерживает приблизительное напряжение в обратном пробое. | Нужен ограничивающий ток резистор/схема. | regulation |
| `elec.bjt.current_gain` | COMPONENT | BJT управляет большим током через меньший базовый ток. | Зависит от режима и температуры. | transistor |
| `elec.mosfet.gate` | COMPONENT | MOSFET управляется напряжением на затворе и имеет высокое входное сопротивление. | Затвор чувствителен к ESD и перенапряжению. | power |
| `elec.opamp.feedback` | PRINCIPLE | Операционный усилитель с обратной связью реализует усиление, фильтры, сравнение. | Реальный op-amp имеет ограничения по скорости, питанию, шуму. | analog |
| `elec.adc_sampling` | PROCESS | ADC преобразует аналоговый сигнал в цифровые отсчёты. | Частота дискретизации и разрядность ограничивают точность. | sensors |
| `elec.dac_output` | PROCESS | DAC преобразует цифровое значение в аналоговый сигнал. | Нужны фильтрация и учёт разрешения. | control |
| `elec.sensor.temperature_rtd` | SENSOR | RTD измеряет температуру по изменению сопротивления. | Требует калибровки и компенсации проводов. | measurement |
| `elec.sensor.thermocouple` | SENSOR | Термопара создаёт напряжение из-за разности температур спаев. | Требует cold-junction compensation. | temperature |
| `elec.sensor.photodiode` | SENSOR | Фотодиод преобразует свет в ток. | Зависит от спектра и схемы. | optics |
| `elec.sensor.strain_gauge` | SENSOR | Тензодатчик меняет сопротивление при деформации. | Требует мостовой схемы и калибровки. | mechanics |
| `elec.pcb.ground_plane` | METHOD | Земляной слой снижает импеданс возвратных токов и шум. | Плохие разрывы ухудшают EMI. | pcb |
| `elec.pcb.trace_width` | CONSTRAINT | Ширина дорожки выбирается по току, нагреву и допустимому падению напряжения. | Зависит от меди, слоя, охлаждения. | pcb |
| `elec.pcb.decoupling_capacitor` | METHOD | Развязывающий конденсатор рядом с микросхемой снижает просадки питания. | Расположение критично. | digital |
| `elec.pcb.emi` | FAILURE_MODE | Электромагнитные помехи возникают из-за быстрых фронтов, токовых петель и плохой разводки. | Нужны layout, shielding, filtering. | compliance |
| `elec.power.linear_regulator` | COMPONENT | Линейный регулятор снижает напряжение, рассеивая лишнюю энергию теплом. | Неэффективен при большом падении и токе. | power |
| `elec.power.switching_regulator` | COMPONENT | Импульсный регулятор преобразует напряжение с высокой эффективностью. | Создаёт шум и требует правильной разводки. | power |
| `elec.power.rectifier_bridge` | COMPONENT | Мостовой выпрямитель использует четыре диода для двухполупериодного выпрямления. | Есть падение напряжения и нагрев. | ac_dc |
| `elec.power.inverter` | SYSTEM | Инвертор превращает DC в AC. | Форма сигнала и защита важны. | solar |
| `elec.power.ups` | SYSTEM | UPS питает нагрузку при пропадании сети. | Время работы зависит от батареи и нагрузки. | reliability |
| `elec.battery.lead_acid` | BATTERY | Свинцово-кислотные батареи дешевы и мощны, но тяжелы. | Опасны кислота, газовыделение, свинец. | energy_storage |
| `elec.battery.li_ion_bms` | SAFETY_RULE | Li-ion батареям нужен BMS для контроля напряжения, тока, температуры и баланса. | Ошибка может вызвать thermal runaway. | battery |
| `elec.battery.nimh` | BATTERY | NiMH аккумуляторы применяются в бытовой технике и гибридных системах. | Имеют саморазряд и особенности зарядки. | batteries |
| `elec.grid.transformer_substation` | SYSTEM | Подстанция преобразует напряжение и распределяет энергию. | Требует защиты, охлаждения, изоляции. | grid |
| `elec.grid.protection_relay` | SAFETY | Релейная защита отключает повреждённые участки сети. | Настройка должна избегать ложных и пропущенных срабатываний. | power_grid |
| `elec.grid.load_balancing` | PROCESS | Балансировка сети требует соответствия генерации и потребления. | Нарушение влияет на частоту и стабильность. | grid |
| `elec.solar.mppt` | METHOD | MPPT ищет рабочую точку солнечной панели с максимальной мощностью. | Зависит от освещённости и температуры. | solar_pv |
| `elec.wind.pitch_control` | METHOD | Pitch control меняет угол лопастей для управления мощностью и нагрузками. | Важен при сильном ветре. | wind |
| `elec.motor.vfd` | SYSTEM | Частотный привод управляет скоростью AC-двигателя через изменение частоты/напряжения. | Может создавать EMI и требования к мотору. | motors |
| `elec.digital.binary` | PRINCIPLE | Цифровая логика представляет состояния как 0/1 в допустимых уровнях напряжения. | Реальные сигналы аналоговые и шумные. | computing |
| `elec.digital.clock` | COMPONENT | Тактовый сигнал синхронизирует цифровые схемы. | Clock skew и jitter ограничивают скорость. | CPU |
| `elec.digital.flip_flop` | COMPONENT | Триггер хранит один бит состояния. | Требует timing constraints. | digital |
| `elec.digital.register` | COMPONENT | Регистр хранит группу битов. | Основа процессорного состояния. | CPU |
| `elec.digital.alu` | COMPONENT | ALU выполняет арифметические и логические операции. | Работает внутри CPU/микроконтроллера. | computing |
| `elec.memory.sram` | COMPONENT | SRAM хранит бит на транзисторной ячейке без refresh. | Быстрая, но дорогая по площади. | cache |
| `elec.memory.flash` | COMPONENT | Flash хранит заряд в ячейках для энергонезависимой памяти. | Ограничена числом циклов записи/стирания. | storage |
| `elec.cpu.pipeline` | MECHANISM | Конвейер CPU разделяет выполнение инструкций на стадии для повышения throughput. | Branches и hazards требуют управления. | computing |
| `elec.cpu.branch_prediction` | METHOD | Предсказание ветвлений уменьшает простой pipeline. | Ошибка предсказания стоит сброса/штрафа. | CPU |
| `elec.bus.i2c` | PROTOCOL | I2C — двухпроводная шина для связи микросхем на плате. | Ограничена скоростью, ёмкостью линии, адресами. | embedded |
| `elec.bus.spi` | PROTOCOL | SPI — синхронная шина с отдельными линиями данных и clock. | Быстрее I2C, но требует больше проводов. | embedded |
| `elec.bus.uart` | PROTOCOL | UART передаёт последовательные данные без общего clock. | Стороны должны согласовать baud rate. | embedded |
| `elec.network.ethernet` | PROTOCOL | Ethernet передаёт сетевые кадры в локальных сетях. | Физические среды и скорости различаются. | networks |
| `elec.network.wifi` | PROTOCOL | Wi-Fi передаёт данные по радиоканалу. | Помехи, расстояние и стены влияют на качество. | networks |
| `elec.security.tls` | PROTOCOL | TLS защищает соединение шифрованием и аутентификацией. | Требует корректных сертификатов и настроек. | security |
| `elec.security.password_hashing` | METHOD | Пароли хранят как медленные salted hashes, а не plaintext. | Нужны современные параметры и защита от утечек. | security |
| `elec.data.backup_restore_test` | METHOD | Backup считается полезным только после проверки восстановления. | Непроверенный backup может быть бесполезен. | data_safety |
| `elec.software.api` | TERM | API задаёт контракт взаимодействия программ. | Смена API ломает клиентов без совместимости. | software |
| `elec.software.logging` | METHOD | Логи записывают события для диагностики и аудита. | Нельзя логировать секреты. | observability |
| `elec.failure.short_circuit` | FAILURE_MODE | Короткое замыкание создаёт чрезмерный ток и нагрев. | Нужны предохранители/автоматы. | electrical_safety |
| `elec.failure.thermal_overload` | FAILURE_MODE | Перегрев компонентов возникает при превышении мощности, плохом охлаждении или контакте. | Ускоряет деградацию и пожарный риск. | reliability |
| `elec.safety.esd_control` | SAFETY_RULE | ESD-control защищает чувствительные компоненты от статического разряда. | Нужны браслеты, коврики, упаковка, влажность. | electronics |
| `elec.safety.arc_flash` | SAFETY_RULE | Arc flash — опасный электрический разряд с теплом, светом и давлением. | Требует процедур, PPE и расчёта риска. | industrial_safety |

---

## 📊 Batch 005 summary

```text
new units: 60
main layers:
  wiring and electrical safety
  passive and active components
  sensors and PCB design
  power conversion and batteries
  grid and renewable energy
  digital logic and CPU basics
  embedded buses and networks
  software/security operational basics
```

