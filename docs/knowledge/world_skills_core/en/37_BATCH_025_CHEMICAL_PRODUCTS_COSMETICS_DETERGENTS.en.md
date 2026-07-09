# 🧪 Batch 025 — Chemical Products, Cosmetics, Detergents & Household Materials

**Язык:** русский  
**Статус:** 50K batch 025 / seed units / не L3 truth  
**Цель:** добавить практическую химию продуктов: моющие средства, косметика, клеи, краски, растворители, удобрения, бытовые материалы и safety.

---

## ⚠️ Safety note

Этот batch не является рецептурником опасной химии. Он описывает классы веществ, функции, риски и ограничения.

---

## 📦 Knowledge Units

| ID | Тип | Суть | Условия / границы | Связи |
|---|---|---|---|---|
| `chemprod.surfactant.anionic` | MATERIAL_CLASS | Анионные ПАВ хорошо удаляют жир и пенятся. | Могут раздражать кожу и чувствительны к жёсткой воде. | detergents |
| `chemprod.surfactant.nonionic` | MATERIAL_CLASS | Неионогенные ПАВ часто работают при разных pH и низкой пене. | Используются в стирке, посуде, промышленности. | detergents |
| `chemprod.surfactant.cationic` | MATERIAL_CLASS | Катионные ПАВ могут работать как кондиционеры и антимикробные компоненты. | Несовместимы со многими анионными ПАВ. | chemistry |
| `chemprod.surfactant.amphoteric` | MATERIAL_CLASS | Амфотерные ПАВ мягче и часто используются в шампунях. | Свойства зависят от pH. | cosmetics |
| `chemprod.detergent.builder` | COMPONENT_ROLE | Builders связывают жёсткость воды и усиливают моющее действие. | Некоторые builder ограничены экологически. | detergents |
| `chemprod.detergent.enzyme` | COMPONENT_ROLE | Энзимы расщепляют белковые, крахмальные или жировые загрязнения. | Чувствительны к температуре и pH. | laundry |
| `chemprod.detergent.bleach_oxygen` | COMPONENT_ROLE | Кислородные отбеливатели окисляют пятна и запахи. | Безопаснее хлорных для многих тканей, но не универсальны. | laundry |
| `chemprod.detergent.optical_brightener` | COMPONENT_ROLE | Оптические отбеливатели поглощают UV и излучают синеватый свет. | Не очищают, а меняют восприятие белизны. | textiles |
| `chemprod.cleaner.acid_descaler` | PRODUCT_TYPE | Кислотные средства удаляют известковый налёт и ржавчину. | Опасны для мрамора, бетона и кожи. | cleaning |
| `chemprod.cleaner.alkaline_degreaser` | PRODUCT_TYPE | Щёлочные обезжириватели разрушают жиры и масла. | Могут быть едкими. | cleaning |
| `chemprod.cleaner.solvent_degreaser` | PRODUCT_TYPE | Растворители растворяют неполярные загрязнения. | Риски: пары, пожар, токсичность. | safety |
| `chemprod.cleaner.abrasive` | PRODUCT_TYPE | Абразивы механически снимают загрязнения и слой поверхности. | Могут царапать. | materials |
| `chemprod.disinfectant.alcohol` | PRODUCT_TYPE | Спиртовые дезинфектанты быстро снижают микробную нагрузку на чистых поверхностях. | Летучи и горючи. | hygiene |
| `chemprod.disinfectant.quat` | PRODUCT_TYPE | QAC/quat применяются как дезинфицирующие компоненты. | Остатки и устойчивость требуют контроля. | hygiene |
| `chemprod.disinfectant.chlorine` | PRODUCT_TYPE | Хлорные средства сильные окислители для дезинфекции и отбеливания. | Нельзя смешивать с кислотами/аммиаком. | safety |
| `chemprod.cosmetic.emulsion_oil_in_water` | FORM | Oil-in-water emulsion даёт лёгкие кремы и лосьоны. | Требует эмульгатора и консервации. | cosmetics |
| `chemprod.cosmetic.emulsion_water_in_oil` | FORM | Water-in-oil emulsion более жирная и барьерная. | Может ощущаться тяжёлой. | cosmetics |
| `chemprod.cosmetic.humectant` | COMPONENT_ROLE | Humectants притягивают и удерживают воду. | Эффект зависит от влажности и формулы. | skincare |
| `chemprod.cosmetic.emollient` | COMPONENT_ROLE | Emollients смягчают кожу и улучшают ощущение поверхности. | Не всегда увлажняют сами по себе. | skincare |
| `chemprod.cosmetic.occlusive` | COMPONENT_ROLE | Occlusives снижают потерю воды через кожу. | Могут быть тяжёлыми или комедогенными для некоторых. | skincare |
| `chemprod.cosmetic.preservative` | COMPONENT_ROLE | Консерванты ограничивают рост микробов в продукте. | Требуют challenge testing. | cosmetics |
| `chemprod.cosmetic.fragrance_allergen` | RISK | Ароматические компоненты могут вызывать раздражение или аллергию. | Риск индивидуален. | health |
| `chemprod.cosmetic.sunscreen_filter` | COMPONENT_ROLE | UV-фильтры поглощают или рассеивают ультрафиолет. | Эффективность зависит от нанесения и SPF testing. | skincare |
| `chemprod.cosmetic.ph` | PARAMETER | pH продукта влияет на кожу, волосы, консервацию и стабильность. | Измерять нужно в готовой формуле. | formulation |
| `chemprod.hair.shampoo` | PRODUCT_TYPE | Шампунь очищает кожу головы и волосы с ПАВ и добавками. | Слишком сильное очищение сушит. | cosmetics |
| `chemprod.hair.conditioner` | PRODUCT_TYPE | Кондиционер снижает трение волос и улучшает расчёсывание. | Часто использует катионные компоненты. | cosmetics |
| `chemprod.hair.dye_oxidative` | PRODUCT_TYPE | Окислительное окрашивание меняет пигменты волос химически. | Риски раздражения и аллергии. | hair |
| `chemprod.soap.saponification` | PROCESS | Омыление превращает жиры и щёлочь в мыло и глицерин. | Щёлочь опасна, нужен контроль избытка. | chemistry |
| `chemprod.soap.superfat` | PARAMETER | Superfat оставляет часть жиров неомылёнными в мыле. | Снижает очищающую силу и меняет стабильность. | soap |
| `chemprod.adhesive.pva` | PRODUCT_TYPE | PVA-клей используется для бумаги, дерева и пористых материалов. | Не всегда водостойкий. | adhesives |
| `chemprod.adhesive.epoxy` | PRODUCT_TYPE | Эпоксидные клеи отверждаются реакцией смолы и отвердителя. | Прочны, но требуют точного смешивания и PPE. | materials |
| `chemprod.adhesive.cyanoacrylate` | PRODUCT_TYPE | Цианоакрилат быстро полимеризуется от влаги на поверхности. | Склеивает кожу, плохо заполняет большие зазоры. | repair |
| `chemprod.adhesive.hot_melt` | PRODUCT_TYPE | Hot-melt клей наносится расплавом и твердеет при охлаждении. | Чувствителен к температуре эксплуатации. | packaging |
| `chemprod.sealant.silicone` | PRODUCT_TYPE | Силиконовые герметики остаются эластичными и влагостойкими. | Не все окрашиваются и не все подходят для аквариумов/еды. | construction |
| `chemprod.sealant.polyurethane` | PRODUCT_TYPE | Полиуретановые герметики прочны и эластичны. | Влага и подготовка поверхности важны. | construction |
| `chemprod.paint.binder` | COMPONENT_ROLE | Binder удерживает пигмент и формирует плёнку краски. | Определяет адгезию и стойкость. | paint |
| `chemprod.paint.pigment` | COMPONENT_ROLE | Пигмент даёт цвет, укрывистость и иногда защитные свойства. | Некоторые пигменты токсичны. | paint |
| `chemprod.paint.solvent` | COMPONENT_ROLE | Растворитель регулирует вязкость и испаряется при высыхании. | VOC и пожарные риски. | safety |
| `chemprod.paint.waterborne` | PRODUCT_TYPE | Водоразбавляемые краски используют воду как основной носитель. | Не всегда без VOC. | paint |
| `chemprod.paint.alkyd` | PRODUCT_TYPE | Алкидные краски дают прочную плёнку через окислительное высыхание. | Могут желтеть и выделять растворители. | paint |
| `chemprod.coating.powder` | PROCESS | Порошковое покрытие наносит сухой порошок и запекает плёнку. | Требует электростатики и печи. | manufacturing |
| `chemprod.fertilizer.nitrogen` | PRODUCT_TYPE | Азотные удобрения поддерживают рост листьев и белков. | Избыток загрязняет воду и ослабляет растения. | agriculture |
| `chemprod.fertilizer.phosphorus` | PRODUCT_TYPE | Фосфор важен для энергии клеток и корней. | В почве может связываться и быть недоступным. | agriculture |
| `chemprod.fertilizer.potassium` | PRODUCT_TYPE | Калий важен для водного баланса и устойчивости растений. | Дефицит и избыток влияют на урожай. | agriculture |
| `chemprod.fertilizer.slow_release` | PRODUCT_TYPE | Медленное высвобождение снижает потери и пики концентрации. | Стоит дороже и зависит от условий. | agriculture |
| `chemprod.pesticide.herbicide` | PRODUCT_TYPE | Гербициды подавляют сорные растения. | Риск резистентности и drift. | agriculture |
| `chemprod.pesticide.insecticide` | PRODUCT_TYPE | Инсектициды контролируют насекомых-вредителей. | Могут вредить опылителям и людям. | agriculture |
| `chemprod.pesticide.fungicide` | PRODUCT_TYPE | Фунгициды снижают болезни растений от грибов/оомицетов. | Timing и resistance management важны. | agriculture |
| `chemprod.material.plasticizer` | COMPONENT_ROLE | Пластификаторы делают полимеры мягче и гибче. | Миграция и toxicity зависят от вещества. | polymers |
| `chemprod.material.flame_retardant` | COMPONENT_ROLE | Огнезащитные добавки замедляют воспламенение или горение. | Некоторые имеют экологические риски. | safety |
| `chemprod.material.uv_stabilizer` | COMPONENT_ROLE | UV stabilizers замедляют разрушение материалов светом. | Не делают материал вечным. | polymers |
| `chemprod.rubber.vulcanization` | PROCESS | Вулканизация сшивает каучук, повышая упругость и прочность. | Температура и сера/пероксиды важны. | rubber |
| `chemprod.plastic.recycling_code` | INFORMATION | Recycling code указывает тип пластика, но не гарантирует переработку. | Местная инфраструктура решает. | waste |
| `chemprod.aerosol.propellant` | COMPONENT_ROLE | Пропеллент выталкивает продукт из аэрозольной упаковки. | Риски давления и горючести. | packaging |
| `chemprod.battery.electrolyte` | COMPONENT_ROLE | Электролит переносит ионы между электродами батареи. | Может быть едким, горючим или токсичным. | battery |
| `chemprod.desiccant.silica_gel` | PRODUCT_TYPE | Силикагель поглощает влагу в упаковке. | Имеет ограниченную ёмкость. | packaging |
| `chemprod.absorbent.activated_carbon` | MATERIAL | Активированный уголь адсорбирует многие органические молекулы. | Не универсален для всех газов/ионов. | filtration |
| `chemprod.safety.sds` | DOCUMENT | SDS описывает опасности, хранение, PPE и первую помощь для химиката. | Должен соответствовать конкретному продукту. | safety |
| `chemprod.safety.ghs_pictogram` | STANDARD | GHS pictograms показывают классы химической опасности. | Нужно читать весь label/SDS. | safety |
| `chemprod.safety.compatible_storage` | SAFETY_RULE | Несовместимые химикаты хранят раздельно. | Особенно кислоты, bases, oxidizers, flammables. | lab |
| `chemprod.safety.ventilation` | SAFETY_RULE | Вентиляция снижает концентрацию паров, аэрозолей и пыли. | Не заменяет PPE при high risk. | safety |
| `chemprod.safety.skin_patch_test` | CAUTION | Patch test иногда используют для оценки реакции кожи на продукт. | Не гарантирует отсутствие аллергии. | cosmetics |
| `chemprod.quality.viscosity` | QUALITY_METRIC | Вязкость влияет на нанесение, дозирование и стабильность продукта. | Зависит от температуры. | formulation |
| `chemprod.quality.shelf_stability` | QUALITY_CHECK | Shelf stability проверяет, сохраняет ли продукт свойства во времени. | Условия ускоренного теста не всегда точны. | QA |
| `chemprod.quality.phase_separation` | FAILURE_MODE | Расслоение показывает нестабильность эмульсии или смеси. | Может быть от температуры, pH, несовместимости. | formulation |
| `chemprod.quality.packaging_compatibility` | QUALITY_CHECK | Упаковка не должна разрушаться или загрязнять продукт. | Растворители и масла могут мигрировать. | packaging |

---

## 📊 Batch 025 summary

```text
new units: 66
main layers:
  detergents and cleaners
  cosmetics and formulation
  adhesives, paints, fertilizers and pesticides
  chemical product safety and quality
```
