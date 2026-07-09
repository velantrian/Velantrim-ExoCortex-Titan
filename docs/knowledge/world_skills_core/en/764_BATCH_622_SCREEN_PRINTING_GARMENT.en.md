# BATCH 622: Screen Printing — Garment Decoration

**KnowledgeUnits:** 44
**Namespace:** `screenprint.ops.*`
**Scope:** screen_prep, emulsion, exposure, ink, squeegee, curing, multi_color, registration

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| screenprint.ops.screen_mesh_coating | Screen — Mesh & Emulsion Coating | METHOD | Подготовка трафаретной сетки. Mesh count: 110-160 для пластовых красок, 200-280 для детальной, 305+ для CMYK. Натяжение: 20-25 Н/см. Emulsion (dual-cure). Coating: scoop coater — тонкий ровный слой на обе стороны. Сушка: в темноте, 30-60 мин при 25-30°C. EOM (Emulsion Over Mesh): 10-20%. | Обезжиривание сетки перед coating'ом. |
| screenprint.ops.exposure_calculation | Exposure — Step Test & Calculation | METHOD | Засветка трафарета. UV fluorescent/LED UV 395-405 нм. Step Wedge Test (Stouffer 21-Step). Under-exposed: pinholes, sawtooth edges. Over-exposed: тонкие линии не вымываются. Позитив: inkjet film, laser vellum. Вакуумный стол для контакта. | Полутона: dot 45-65 lpi, угол 22.5° для одного цвета. |
| screenprint.ops.squeegee_technique | Squeegee — Angle, Pressure & Speed | METHOD | Нанесение ракелем. Угол 75-80°, давление достаточное для проталкивания, flood stroke (pre-distribute), print stroke. Off-contact 1-3 мм (сетка касается ткани только в момент прохода). Для бумаги — on-contact. | Пластизолевые краски: требуют curing 160°C. Водные: air-dry но забивают сетку. |
| screenprint.ops.conveyor_curing | Curing — Conveyor Dryer | PROCESS | Фиксация пластизолевых красок при 150-165°C через туннельную сушилку. Under-cured: трескается при стирке. Flash между цветами для wet-on-wet. Curing test: stretch test. | Водные краски требуют испарения воды + catalyst. |
| screenprint.ops.registration_multi | Multi-Color — Registration System | METHOD | Совмещение цветов. Карусельный пресс. Registration marks (crosshairs), micro registration (винты X/Y/угол). Порядок цветов: light → dark. Underbase (белая подложка) для тёмных тканей. Trap 0.25-0.5 мм. | Карусель: каждая head — один цвет. |
