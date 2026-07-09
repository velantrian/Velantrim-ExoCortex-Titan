# BATCH_074 — Restaurants & Institutional Kitchens: Menu Engineering, Food Safety Operations
# world_skills_core · source: world_skills_core:batch_074:foodservice
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| foodservice.kitchen.brigade | Бригадная система кухни (Эскофье) | invariant | иерархия поваров: шеф → су-шеф → шеф-де-парти → коммис | организация работы кухни |
| foodservice.kitchen.stations | Кухонные станции | variant | гриль, соте, гарде-манже, кондитерская | разделение зон приготовления |
| foodservice.kitchen.mise_en_place | Миза на месте | invariant | подготовка всех ингредиентов до начала готовки | скорость и порядок на кухне |
| foodservice.kitchen.flow | Поток на кухне | variant | от приёмки → хранение → обработка → готовка → выдача | эффективность без пересечений |
| foodservice.safety.haccp | HACCP в общепите | invariant | анализ рисков и критические контрольные точки | предотвращение пищевых отравлений |
| foodservice.safety.danger_zone | Температурная опасная зона | invariant | 5–60°C — быстрый рост бактерий | хранить горячее горячим, холодное холодным |
| foodservice.safety.temperature | Контроль температуры | invariant | холодильник ≤5°C, заморозка ≤−18°C, прогрев блюд ≥75°C | безопасность продуктов |
| foodservice.safety.cross_contamination | Перекрёстное загрязнение | invariant | сырое → готовое через руки, доски, ножи | разделение и санитария |
| foodservice.safety.color_boards | Цветные разделочные доски | variant | разные цвета для мяса, рыбы, овощей | предотвращение загрязнения |
| foodservice.safety.handwashing | Гигиена рук персонала | invariant | мытьё до/после операций — ключевой барьер | защита от фекально-оральных инфекций |
| foodservice.safety.allergens | Управление аллергенами | invariant | 14 основных аллергенов; маркировка и изоляция | защита жизни гостей |
| foodservice.safety.fifo | FIFO/ротация продуктов | invariant | первым пришёл — первым использован; даты | свежесть и снижение порчи |
| foodservice.safety.pest | Контроль вредителей на кухне | variant | защита от грызунов и насекомых | санитарные требования |
| foodservice.safety.cleaning | Санитария и дезинфекция | invariant | мойка → ополаскивание → дезинфекция поверхностей | чистая производственная среда |
| foodservice.safety.haccp_records | Журналы контроля | variant | записи температур, уборки, приёмки | доказательство безопасности при проверке |
| foodservice.menu.engineering | Меню-инжиниринг | invariant | анализ блюд по марже и популярности | прибыльность меню |
| foodservice.menu.stars_dogs | Звёзды/лошадки/загадки/собаки | variant | матрица популярность×маржа для решений по меню | оптимизация ассортимента |
| foodservice.menu.food_cost | Фудкост | invariant | доля себестоимости продуктов в цене блюда (цель ~25–35%) | ценообразование и маржа |
| foodservice.menu.portion_control | Контроль порций | invariant | стандартизация веса/объёма порции | стабильность качества и затрат |
| foodservice.menu.recipe_card | Технологическая карта | invariant | рецепт с граммовками, выходом, себестоимостью | воспроизводимость и расчёт |
| foodservice.menu.psychology | Психология меню | variant | расположение, описание, отсутствие знака валюты | влияние на выбор гостя |
| foodservice.ops.par_level | PAR-уровень закупок | variant | целевой запас продуктов до следующей поставки | предотвращение нехватки/порчи |
| foodservice.ops.waste | Управление отходами кухни | variant | контроль перепроизводства, порчи, остатков | снижение food cost |
| foodservice.ops.yield | Выход продукта | variant | доля съедобной части после обработки | точный расчёт закупок |
| foodservice.ops.prep_cook | Заготовка vs готовка под заказ | variant | баланс скорости подачи и свежести | организация сервиса |
| foodservice.service.foh_boh | Фасад дома/Задняя часть дома | invariant | зал (сервис) vs кухня (производство) | координация ресторана |
| foodservice.service.flow | Поток обслуживания | variant | встреча → заказ → подача → расчёт → уборка | опыт гостя |
| foodservice.service.table_turnover | Оборачиваемость столов | invariant | сколько раз стол обслуживается за смену | выручка на посадочное место |
| foodservice.service.upselling | Допродажи | variant | предложение закусок, напитков, десертов | рост среднего чека |
| foodservice.beverage.cost | Себестоимость напитков | variant | бар-кост обычно ниже фудкоста — высокая маржа | прибыльность бара |
| foodservice.beverage.pour_control | Контроль розлива | variant | мерники, системы учёта против потерь | снижение злоупотреблений |
| foodservice.equipment.commercial | Профессиональное оборудование | variant | плиты, пароконвектоматы, холодильные камеры, посудомойки | производительность кухни |
| foodservice.equipment.maintenance | Обслуживание оборудования | invariant | чистка, поверка, ремонт против простоев | непрерывность работы |
| foodservice.institutional.scale | Институциональное питание | variant | школы, больницы, столовые — массовое производство | масштаб и нормы питания |
| foodservice.institutional.nutrition | Нормы питания | variant | сбалансированные рационы по возрасту/потребностям | здоровье питающихся |
| foodservice.institutional.cook_chill | Cook-chill технология | variant | приготовление, быстрое охлаждение, хранение, разогрев | массовое безопасное питание |
| foodservice.cost.labor | Затраты на персонал | invariant | вторая крупная статья после продуктов | управление сменами и нормами |
| foodservice.cost.prime | Прайм-кост | invariant | сумма food cost + labor cost (цель ≤60% выручки) | ключевой показатель ресторана |
| foodservice.staff.training | Обучение персонала | variant | гигиена, сервис, меню, безопасность | качество и стабильность |
| foodservice.staff.turnover | Текучесть кадров | variant | высокая в отрасли → затраты на найм и обучение | удержание персонала |
| foodservice.quality.consistency | Стабильность качества | invariant | одинаковое блюдо каждый раз | доверие и репутация |
| foodservice.delivery.operations | Доставка и навынос | variant | упаковка, температура, время, агрегаторы | сохранение качества при доставке |
| foodservice.hygiene.inspection | Санитарная проверка | invariant | контроль надзорных органов, рейтинги | допуск к работе |
| foodservice.sustainability.local | Локальные продукты и сезонность | variant | свежесть, снижение логистики, поддержка местных | устойчивость и качество |
