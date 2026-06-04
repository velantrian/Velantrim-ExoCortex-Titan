# 📦 Batch 038 — Packaging, Printing & Consumer Goods

**Язык:** русский  
**Статус:** 50K batch 038 / seed units / не L3 truth  
**Цель:** добавить знания о товарах повседневного потребления: упаковка, печать, маркировка, производство, контроль качества и shelf life.

---

## 📦 Knowledge Units

| ID | Тип | Суть | Условия / границы | Связи |
|---|---|---|---|---|
| `packaging.primary` | TERM | Первичная упаковка контактирует с продуктом напрямую. | Требует совместимости с продуктом. | packaging |
| `packaging.secondary` | TERM | Вторичная упаковка группирует первичные единицы. | Часто используется для полки и логистики. | packaging |
| `packaging.tertiary` | TERM | Третичная упаковка нужна для транспорта и складирования. | Паллеты, стрейч, коробки. | logistics |
| `packaging.paperboard` | MATERIAL | Картон используется для коробок, этикеток и потребительской упаковки. | Влага снижает прочность. | paper |
| `packaging.corrugated_board` | MATERIAL | Гофрокартон имеет волнистый слой между лайнерами для жёсткости. | Профиль flute влияет на прочность. | logistics |
| `packaging.glass_bottle` | MATERIAL | Стеклянная тара барьерна и химически стойка. | Тяжёлая и хрупкая. | materials |
| `packaging.aluminum_can` | MATERIAL | Алюминиевые банки лёгкие и перерабатываемые. | Требуют внутреннего покрытия для некоторых продуктов. | metals |
| `packaging.plastic_pet` | MATERIAL | PET часто используется для бутылок и пищевой упаковки. | Барьер к кислороду ограничен. | polymers |
| `packaging.plastic_hdpe` | MATERIAL | HDPE прочен и устойчив к многим химикатам. | Используется для канистр, флаконов, крышек. | polymers |
| `packaging.flexible_film` | MATERIAL | Гибкие плёнки экономят массу и место. | Переработка сложна при многослойности. | packaging |
| `packaging.laminate` | MATERIAL | Ламинат объединяет слои для барьера, печати и прочности. | Разделение слоёв сложно. | materials |
| `packaging.barrier_oxygen` | PROPERTY | Кислородный барьер замедляет окисление продукта. | Важен для кофе, мяса, масел. | food |
| `packaging.barrier_moisture` | PROPERTY | Влагобарьер защищает продукт от высыхания или увлажнения. | Критично для порошков и снеков. | food |
| `packaging.seal_integrity` | QUALITY_CHECK | Целостность шва защищает продукт от утечек и загрязнения. | Проверяется давлением, вакуумом, красителем. | QA |
| `packaging.tamper_evident` | SAFETY_FEATURE | Tamper evidence показывает признаки вскрытия. | Не предотвращает все вмешательства. | security |
| `packaging.child_resistant` | SAFETY_FEATURE | Child-resistant packaging снижает риск доступа детей к опасным продуктам. | Не является child-proof. | safety |
| `packaging.label.claim` | INFORMATION | Claims на упаковке должны быть точными и доказуемыми. | Регулируются по категории продукта. | law |
| `packaging.label.ingredient_list` | INFORMATION | Состав перечисляет ингредиенты по правилам категории. | Аллергены требуют отдельного контроля. | consumer |
| `packaging.label.lot_code` | TRACE | Lot code связывает товар с партией производства. | Критично для recall. | traceability |
| `packaging.label.expiry` | INFORMATION | Срок годности связывает качество/безопасность со временем хранения. | Нужны stability data. | QA |
| `printing.offset` | PROCESS | Офсетная печать переносит краску через промежуточный цилиндр. | Эффективна для больших тиражей. | printing |
| `printing.flexography` | PROCESS | Флексография печатает гибкими формами по упаковочным материалам. | Часто для плёнок и этикеток. | packaging |
| `printing.gravure` | PROCESS | Глубокая печать использует углубления цилиндра для краски. | Дорога, но стабильна на больших тиражах. | printing |
| `printing.digital` | PROCESS | Цифровая печать печатает без печатных форм. | Хороша для малых тиражей и personalization. | printing |
| `printing.color_cmyk` | MODEL | CMYK смешивает cyan, magenta, yellow и black в печати. | Цвет зависит от профиля и материала. | design |
| `printing.pantone` | STANDARD | Spot colors стандартизируют специальные цвета. | Не всегда воспроизводимы в CMYK. | branding |
| `printing.registration` | QUALITY_CHECK | Registration проверяет совпадение цветов и слоёв печати. | Смещение даёт размытые контуры. | QA |
| `printing.bleed` | DESIGN_RULE | Bleed добавляет запас изображения за линию реза. | Нужен для аккуратной обрезки. | design |
| `printing.die_cutting` | PROCESS | Высечка вырезает форму упаковки или этикетки. | Tooling влияет на точность. | packaging |
| `printing.varnish_coating` | FINISH | Лак защищает печать и меняет блеск/ощущение. | Может влиять на переработку. | finishing |
| `consumer.goods.bom` | DOCUMENT | BOM товара перечисляет материалы, компоненты и количества. | Основа закупок и себестоимости. | manufacturing |
| `consumer.goods.qc_sampling` | METHOD | Выборочный контроль проверяет часть партии по плану. | Риск пропустить дефект остаётся. | quality |
| `consumer.goods.aql` | METRIC | AQL задаёт допустимый уровень дефектов в выборочном контроле. | Не означает ноль дефектов. | QA |
| `consumer.goods.defect_critical_major_minor` | CLASSIFICATION | Дефекты делят на critical, major, minor по риску и влиянию. | Критерии должны быть заранее. | QA |
| `consumer.goods.drop_test` | QUALITY_CHECK | Drop test проверяет устойчивость товара/упаковки к падению. | Высота и ориентации задают сценарий. | packaging |
| `consumer.goods.shelf_test` | QUALITY_CHECK | Shelf test проверяет внешний вид и стабильность товара при хранении. | Условия должны соответствовать рынку. | QA |
| `consumer.goods.user_manual` | DOCUMENT | Инструкция объясняет безопасное использование, сборку, уход и ограничения. | Плохой manual создаёт риск. | documentation |
| `consumer.goods.warning_label` | SAFETY_INFO | Предупреждение сообщает о конкретном риске и способе избежать вреда. | Слишком много предупреждений снижает внимание. | safety |
| `consumer.goods.warranty_card` | DOCUMENT | Гарантийный документ задаёт срок, условия и исключения. | Права потребителя могут шире гарантии. | law |
| `consumer.goods.spare_parts_policy` | POLICY | Доступность запчастей влияет на ремонтопригодность товара. | Важна для sustainability. | repair |
| `consumer.goods.repairability_score` | METRIC | Repairability оценивает лёгкость ремонта, документацию и запчасти. | Методики различаются. | circular |
| `consumer.goods.product_lifecycle` | MODEL | Жизненный цикл товара: разработка, производство, продажа, использование, конец жизни. | Нужно считать весь cycle. | sustainability |
| `consumer.goods.end_of_life` | PROCESS | End-of-life решает, что делать после использования: reuse, repair, recycle, dispose. | Зависит от инфраструктуры. | waste |
| `consumer.goods.counterfeit_detection` | METHOD | Проверка подделок использует упаковку, коды, качество и цепочку поставок. | Подделки могут быть очень похожими. | security |
| `consumer.goods.recall_notice` | COMMUNICATION | Recall notice должен ясно объяснить товар, риск и действие пользователя. | Нужна многоканальная доставка. | safety |

---

## 📊 Batch 038 summary

```text
new units: 45
main layers:
  packaging materials and barriers
  labels and traceability
  printing processes
  consumer goods quality and repairability
```
