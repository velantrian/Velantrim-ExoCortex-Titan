# 🎛️ Batch 041 — Audio, Music, Stage & Event Production

**Язык:** русский  
**Статус:** 50K batch 041 / seed units / не L3 truth  
**Цель:** добавить практическую базу сценического, аудио- и event-производства: звук, свет, сцена, репетиции, безопасность, авторские права и работа с публикой.

---

## 📦 Knowledge Units

| ID | Тип | Суть | Условия / границы | Связи |
|---|---|---|---|---|
| `audioprod.acoustics.frequency` | TERM | Частота звука связана с высотой тона и измеряется в Hz. | Человеческий слух имеет ограниченный диапазон. | physics |
| `audioprod.acoustics.amplitude` | TERM | Амплитуда связана с уровнем звукового давления. | Восприятие громкости нелинейно. | audio |
| `audioprod.acoustics.decibel` | UNIT | Decibel — логарифмическая единица отношения уровней. | dB SPL, dBu, dBFS различаются. | measurement |
| `audioprod.room.modes` | PHENOMENON | Комнатные моды усиливают или ослабляют басовые частоты. | Сильнее в малых помещениях. | acoustics |
| `audioprod.room.reverberation_time` | METRIC | RT60 оценивает время затухания звука в помещении. | Оптимум зависит от речи/музыки. | acoustics |
| `audioprod.room.absorption` | METHOD | Поглощение снижает отражения и реверберацию. | Материалы работают по-разному по частотам. | acoustics |
| `audioprod.room.diffusion` | METHOD | Диффузия рассеивает отражения, не просто поглощая энергию. | Требует размеров относительно длины волны. | acoustics |
| `audioprod.room.isolation` | METHOD | Звукоизоляция снижает передачу звука между помещениями. | Требует массы, герметичности и развязки. | building |
| `audioprod.microphone.dynamic` | DEVICE | Динамический микрофон прочен и часто выдерживает высокий SPL. | Обычно менее чувствителен к деталям. | audio |
| `audioprod.microphone.condenser` | DEVICE | Конденсаторный микрофон чувствителен и требует питания. | Уязвим к влаге и перегрузке. | audio |
| `audioprod.microphone.polar_pattern` | PROPERTY | Диаграмма направленности показывает, откуда микрофон принимает звук. | Влияет на feedback and bleed. | audio |
| `audioprod.signal.gain_staging` | METHOD | Gain staging держит сигнал достаточно высоким без перегруза. | Важно на каждом участке цепи. | mixing |
| `audioprod.signal.clipping` | FAILURE_MODE | Clipping возникает, когда сигнал превышает допустимый уровень. | Цифровой clipping часто звучит жёстко. | audio |
| `audioprod.signal.noise_floor` | METRIC | Noise floor — уровень шума системы без полезного сигнала. | Gain and equipment affect it. | audio |
| `audioprod.processing.equalizer` | TOOL | EQ усиливает или ослабляет частотные диапазоны. | Может исправлять или портить баланс. | mixing |
| `audioprod.processing.compressor` | TOOL | Compressor снижает динамический диапазон выше порога. | Attack/release меняют ощущение. | mixing |
| `audioprod.processing.limiter` | TOOL | Limiter ограничивает пики сигнала. | Чрезмерность разрушает динамику. | mastering |
| `audioprod.processing.reverb` | EFFECT | Reverb добавляет ощущение пространства. | Может ухудшать разборчивость речи. | mixing |
| `audioprod.processing.delay` | EFFECT | Delay повторяет сигнал с задержкой. | Timing должен соответствовать музыке/речи. | mixing |
| `audioprod.mixer.channel_strip` | SYSTEM | Channel strip объединяет gain, EQ, routing and dynamics. | Разные пульты имеют разную логику. | mixing |
| `audioprod.mixer.aux_send` | ROUTING | Aux send отправляет часть сигнала на монитор или эффект. | Pre/post fader различаются. | audio |
| `audioprod.monitor_mix` | PROCESS | Monitor mix помогает исполнителю слышать себя и других. | Слишком громкий монитор вызывает feedback. | stage |
| `audioprod.feedback_howl` | FAILURE_MODE | Feedback возникает, когда микрофон снова ловит усиленный звук колонок. | Лечат позиционированием, gain, EQ. | safety |
| `audioprod.pa.coverage` | DESIGN_METHOD | PA-система должна равномерно покрывать аудиторию звуком. | Комната и crowd меняют звук. | live |
| `audioprod.speaker.crossover` | COMPONENT | Crossover разделяет частоты между динамиками. | Неверная настройка даёт провалы/перегруз. | audio |
| `stage.stage_plot` | DOCUMENT | Stage plot показывает расположение исполнителей и оборудования. | Нужен техникам до события. | event |
| `stage.input_list` | DOCUMENT | Input list перечисляет источники звука и каналы. | Снижает хаос soundcheck. | event |
| `stage.cable.balanced` | PRINCIPLE | Балансный кабель снижает наведённый шум. | Требует совместимого входа/выхода. | audio |
| `stage.connector.xlr` | COMPONENT | XLR часто используется для микрофонов и balanced audio. | Не все XLR несут одинаковый сигнал. | audio |
| `stage.phantom_power` | POWER | Phantom power питает condenser microphones and DI boxes. | Может навредить некоторым устройствам при ошибке. | audio |
| `stage.di_box` | DEVICE | DI box согласует инструментальный сигнал с микшерным входом. | Бывает passive/active. | audio |
| `recording.sample_rate` | PARAMETER | Sample rate задаёт, сколько раз в секунду измеряется сигнал. | Выше не всегда слышимо лучше. | digital_audio |
| `recording.bit_depth` | PARAMETER | Bit depth задаёт динамический диапазон цифрового аудио. | 24-bit полезен при записи. | digital_audio |
| `musicprod.midi` | PROTOCOL | MIDI передаёт музыкальные события, а не сам звук. | Ноты, velocity, controllers. | music |
| `musicprod.synth_oscillator` | COMPONENT | Осциллятор синтезатора создаёт базовую волну. | Фильтры и envelopes формируют тембр. | synthesis |
| `musicprod.sequencer` | TOOL | Sequencer упорядочивает музыкальные события во времени. | Может управлять MIDI and audio. | production |
| `lighting.dmx` | PROTOCOL | DMX управляет световыми приборами по каналам. | Адресация и termination важны. | stage |
| `stage.power_distribution` | SAFETY_SYSTEM | Сценическое питание распределяет нагрузку по линиям и защите. | Перегруз и плохое заземление опасны. | electrical |
| `stage.rigging.load` | SAFETY_RULE | Подвес света/звука требует расчёта нагрузки и сертифицированного rigging. | High-risk, только квалифицированные специалисты. | safety |
| `event.permit` | DOCUMENT | Ивент может требовать разрешений по шуму, безопасности, продаже, толпе. | Зависит от места и масштаба. | law |
| `event.crowd_flow` | SAFETY_METHOD | Потоки публики планируют через входы, выходы, барьеры и signage. | Узкие места опасны. | safety |
| `event.ticketing` | SYSTEM | Ticketing управляет продажей, доступом, вместимостью и отчётностью. | Fraud and privacy risks. | operations |
| `event.rehearsal_schedule` | DOCUMENT | Расписание репетиций координирует людей, сцену, звук, свет и время. | Буферы снижают риск срыва. | project |
| `event.copyright_performance` | LEGAL_RISK | Публичное исполнение музыки может требовать лицензий. | Правила зависят от страны и репертуара. | IP |
| `event.hearing_protection` | SAFETY_RULE | Длительный громкий звук требует защиты слуха для персонала и публики. | Damage can be irreversible. | health |

---

## 📊 Batch 041 summary

```text
new units: 45
main layers:
  acoustics and audio signal flow
  live sound and recording
  stage, lighting, events and safety
```
