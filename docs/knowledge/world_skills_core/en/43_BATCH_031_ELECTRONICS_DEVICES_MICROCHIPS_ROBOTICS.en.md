# 🤖 Batch 031 — Electronics, Devices, Microchips & Robotics

**Язык:** русский  
**Статус:** 50K batch 031 / seed units / не L3 truth  
**Цель:** расширить практическую электронику: устройства, микросхемы, sensors, actuators, embedded systems, robotics и производство.

---

## 📦 Knowledge Units

| ID | Тип | Суть | Условия / границы | Связи |
|---|---|---|---|---|
| `electronics.device.resistor` | COMPONENT | Резистор ограничивает ток и задаёт падение напряжения. | Мощность и допуск важны. | circuits |
| `electronics.device.capacitor` | COMPONENT | Конденсатор хранит заряд и фильтрует изменения напряжения. | ESR, напряжение и полярность важны. | circuits |
| `electronics.device.inductor` | COMPONENT | Индуктивность хранит энергию в магнитном поле. | Насыщение сердечника ограничивает ток. | power |
| `electronics.device.diode` | COMPONENT | Диод проводит ток преимущественно в одном направлении. | Имеет падение напряжения и пределы. | circuits |
| `electronics.device.led` | COMPONENT | LED излучает свет при прямом токе. | Требует ограничения тока. | lighting |
| `electronics.device.bjt` | COMPONENT | BJT управляет током через ток базы. | Используется в усилении и переключении. | semiconductors |
| `electronics.device.mosfet` | COMPONENT | MOSFET управляет током через напряжение затвора. | Gate charge и heating важны. | power |
| `electronics.device.opamp` | COMPONENT | Операционный усилитель усиливает разность входов. | Реальные op-amp имеют offset, bandwidth, rails. | analog |
| `electronics.device.regulator_linear` | COMPONENT | Электроника: Линейный регулятор снижает напряжение, рассеивая лишнюю энергию теплом. | Неэффективен при большом падении напряжения. | power |
| `electronics.device.buck_converter` | POWER_TOPOLOGY | Buck converter понижает напряжение импульсным способом. | Требует индуктивности, диода/ключа, feedback. | power |
| `electronics.device.boost_converter` | POWER_TOPOLOGY | Boost converter повышает напряжение через накопление энергии в индуктивности. | Токи и ripple важны. | power |
| `electronics.device.hbridge` | CIRCUIT | H-bridge меняет направление тока через мотор. | Shoot-through опасен. | robotics |
| `electronics.sensor.thermistor` | SENSOR | Термистор меняет сопротивление с температурой. | Нелинейность требует калибровки. | sensing |
| `electronics.sensor.rtd` | SENSOR | RTD измеряет температуру через сопротивление металла. | Точнее, но дороже термистора. | measurement |
| `electronics.sensor.photodiode` | SENSOR | Электроника: Фотодиод преобразует свет в ток. | Нужна схема усиления. | optics |
| `electronics.sensor.imu` | SENSOR | IMU измеряет ускорение и угловую скорость. | Drift требует фильтрации. | robotics |
| `electronics.sensor.encoder` | SENSOR | Энкодер измеряет положение или скорость вращения. | Абсолютный и инкрементальный отличаются. | motors |
| `electronics.sensor.ultrasonic` | SENSOR | Ультразвуковой датчик измеряет расстояние по времени эха. | Плохо работает с мягкими/наклонными поверхностями. | robotics |
| `electronics.sensor.lidar` | SENSOR | LiDAR измеряет расстояние лазером. | Дороже, чувствителен к среде. | robotics |
| `electronics.sensor.camera` | SENSOR | Камера даёт 2D/видео данные для наблюдения и vision. | Требует света, optics, processing. | computer_vision |
| `electronics.actuator.dc_motor` | ACTUATOR | DC motor создаёт вращение от постоянного тока. | Скорость зависит от напряжения и нагрузки. | motors |
| `electronics.actuator.stepper` | ACTUATOR | Шаговый мотор двигается дискретными шагами. | Может терять шаги без feedback. | robotics |
| `electronics.actuator.servo` | ACTUATOR | Серво содержит мотор, редуктор и feedback для положения. | Диапазон и момент ограничены. | robotics |
| `electronics.actuator.solenoid` | ACTUATOR | Соленоид создаёт линейное движение электромагнитом. | Потребляет ток и нагревается. | automation |
| `electronics.actuator.piezo` | ACTUATOR | Piezo меняет форму под напряжением или генерирует заряд при деформации. | Малый ход, высокая точность. | devices |
| `embedded.microcontroller` | SYSTEM | Микроконтроллер объединяет CPU, память и периферию на одном чипе. | Подходит для управления устройствами. | embedded |
| `embedded.gpio` | INTERFACE | GPIO — цифровые входы/выходы общего назначения. | Ток и напряжение ограничены. | embedded |
| `embedded.adc` | COMPONENT | ADC переводит аналоговый сигнал в цифровое число. | Разрешение и шум важны. | sensing |
| `embedded.pwm` | METHOD | PWM управляет средней мощностью через ширину импульса. | Частота влияет на шум и нагрев. | control |
| `embedded.interrupt` | MECHANISM | Interrupt прерывает основной код для срочного события. | Плохая ISR ломает timing. | firmware |
| `embedded.watchdog` | SAFETY_SYSTEM | Watchdog перезапускает систему при зависании. | Нужно правильно обслуживать. | reliability |
| `embedded.bootloader` | SYSTEM | Bootloader запускает прошивку и может обновлять её. | Ошибка обновления может brick устройство. | firmware |
| `embedded.rtos` | SYSTEM | RTOS управляет задачами с предсказуемым временем. | Требует дисциплины приоритетов. | embedded |
| `embedded.i2c` | BUS | I2C соединяет микросхемы двумя линиями с адресами. | Ограничен скоростью и длиной. | electronics |
| `embedded.spi` | BUS | SPI быстро соединяет master и peripherals несколькими линиями. | Требует chip select. | electronics |
| `embedded.uart` | BUS | Встраиваемые системы: UART передаёт последовательные данные без общего clock. | Нужно согласовать baud rate. | electronics |
| `embedded.can_bus` | BUS | CAN используется в автомобилях и промышленности для устойчивой связи. | Имеет arbitration и termination. | automotive |
| `embedded.firmware_ota` | PROCESS | OTA обновляет прошивку удалённо. | Нужны подпись, rollback и питание. | security |
| `pcb.stackup` | DESIGN | PCB stackup задаёт слои меди, диэлектрика, земли и питания. | Важен для EMI и impedance. | PCB |
| `pcb.ground_plane` | DESIGN_PRINCIPLE | Сплошная земля снижает шум и возвращает токи. | Разрывы создают проблемы EMI. | electronics |
| `pcb.decoupling` | DESIGN_METHOD | Decoupling capacitors сглаживают питание возле микросхем. | Размещение важнее только номинала. | PCB |
| `pcb.trace_width` | DESIGN_CONSTRAINT | Ширина дорожки зависит от тока, нагрева и производства. | High-current требует расчёта. | PCB |
| `pcb.impedance_control` | DESIGN_CONSTRAINT | Контроль impedance нужен для быстрых сигналов. | Требует stackup и правил трассировки. | high_speed |
| `pcb.dfm` | METHOD | DFM делает плату пригодной для производства. | Минимальные зазоры зависят от фабрики. | manufacturing |
| `pcb.soldermask` | COMPONENT | Паяльная маска защищает медь и ограничивает припой. | Повреждения могут создавать коррозию/short. | PCB |
| `pcb.reflow_soldering` | PROCESS | Reflow плавит пасту для пайки SMD компонентов. | Профиль температуры критичен. | assembly |
| `pcb.hand_soldering` | PROCESS | Ручная пайка соединяет компоненты припоем и флюсом. | Перегрев повреждает pad/component. | repair |
| `pcb.esd_control` | SAFETY_RULE | PCB: ESD control защищает чувствительные компоненты от статического разряда. | Требует браслетов, ковриков, packaging. | QA |
| `semiconductor.wafer` | MATERIAL | Wafer — пластина полупроводника для изготовления микросхем. | Чистота и дефекты критичны. | microchips |
| `semiconductor.photolithography` | PROCESS | Фотолитография переносит рисунок на wafer через свет и resist. | Resolution зависит от wavelength, optics, resist. | microchips |
| `semiconductor.doping` | PROCESS | Легирование вводит примеси для изменения проводимости. | Профиль dopant задаёт свойства транзистора. | microchips |
| `semiconductor.etching` | PROCESS | Травление удаляет материал по рисунку. | Бывает wet/dry, isotropic/anisotropic. | microfabrication |
| `semiconductor.deposition` | PROCESS | Осаждение наносит тонкие слои материала. | Толщина и uniformity критичны. | microchips |
| `semiconductor.cleanroom` | INFRA | Cleanroom снижает частицы, загрязнения и дефекты. | Класс чистоты зависит от процесса. | manufacturing |
| `semiconductor.yield` | METRIC | Yield — доля годных чипов на wafer. | Дефекты и дизайн влияют на стоимость. | manufacturing |
| `semiconductor.packaging` | PROCESS | Packaging защищает die и соединяет его с внешней платой. | Тепло и signal integrity важны. | electronics |
| `robotics.kinematics` | MODEL | Кинематика описывает положение и движение без сил. | Нужна для манипуляторов и мобильных роботов. | robotics |
| `robotics.dynamics` | MODEL | Динамика учитывает силы, массы и ускорения. | Важна для контроля и безопасности. | robotics |
| `robotics.forward_kinematics` | METHOD | Forward kinematics вычисляет положение end-effector из суставов. | Зависит от модели робота. | robotics |
| `robotics.inverse_kinematics` | METHOD | Inverse kinematics ищет суставы для нужной позиции. | Может иметь много решений или ни одного. | robotics |
| `robotics.pid_control` | CONTROL | PID управляет ошибкой через proportional, integral, derivative компоненты. | Нужна настройка и anti-windup. | control |
| `robotics.slam` | METHOD | SLAM строит карту и оценивает положение одновременно. | Ошибки датчиков накапливаются. | autonomy |
| `robotics.path_planning` | METHOD | Path planning ищет безопасный маршрут через ограничения. | Динамические препятствия усложняют. | autonomy |
| `robotics.gripper` | END_EFFECTOR | Захват удерживает объект через форму, трение, вакуум или магнит. | Объекты разные по хрупкости и форме. | automation |
| `robotics.safety_e_stop` | SAFETY_SYSTEM | Emergency stop быстро переводит робота в безопасное состояние. | Должен быть доступен и проверен. | safety |
| `robotics.cobot_force_limit` | SAFETY_METHOD | Cobot ограничивает силу/скорость для работы рядом с людьми. | Не делает любую задачу безопасной. | safety |

---

## 📊 Batch 031 summary

```text
new units: 66
main layers:
  electronic components and sensors
  embedded systems and PCB
  semiconductor manufacturing
  robotics and safety
```
