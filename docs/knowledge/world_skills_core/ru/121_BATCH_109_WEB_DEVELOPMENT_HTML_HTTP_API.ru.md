# BATCH_109 — Web Development: HTML/CSS/JS, HTTP, REST, APIs
# world_skills_core · source: world_skills_core:batch_109:web_development
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| webdev.html.role | HTML | invariant | язык разметки структуры веб-страницы | каркас контента |
| webdev.html.tags | Теги и элементы | invariant | `<p>`, `<div>`, `<a>`, заголовки — блоки страницы | структура документа |
| webdev.html.semantic | Семантическая разметка | variant | header/nav/main/footer — смысл, не только вид | доступность, SEO |
| webdev.html.forms | Формы | invariant | сбор пользовательского ввода | взаимодействие |
| webdev.html.accessibility | Доступность (a11y) | variant | alt, ARIA, контраст для всех пользователей | инклюзия |
| webdev.css.role | CSS | invariant | язык оформления (цвет, размер, расположение) | внешний вид |
| webdev.css.selectors | Селекторы | invariant | выбор элементов по тегу/классу/id | применение стилей |
| webdev.css.box_model | Блочная модель | invariant | содержимое + отступ + граница + поле | вёрстка |
| webdev.css.flexbox_grid | Флексбокс и сетка | variant | современная раскладка элементов | адаптивная вёрстка |
| webdev.css.responsive | Адаптивный дизайн | invariant | страница подстраивается под экран | мобильные устройства |
| webdev.js.role | JavaScript | invariant | язык интерактивности в браузере | динамика страницы |
| webdev.js.dom | ДОМ | invariant | дерево объектов страницы для манипуляции | изменение контента |
| webdev.js.events | События | invariant | реакция на клик, ввод, загрузку | интерактивность |
| webdev.js.async | Асинхронность (fetch, promises) | variant | загрузка данных без перезагрузки | динамические приложения |
| webdev.http.protocol | HTTP | invariant | протокол запрос-ответ между клиентом и сервером | основа веба |
| webdev.http.methods | HTTP-методы | invariant | ПОЛУЧИТЬ, ОТПРАВИТЬ, ПОСТАВИТЬ, УДАЛИТЬ, ПАТЧИТЬ | CRUD-операции |
| webdev.http.status | Коды статуса | invariant | 2xx успех, 3xx редирект, 4xx ошибка клиента, 5xx сервера | диагностика |
| webdev.http.headers | Заголовки | variant | метаданные запроса/ответа (тип, авторизация) | управление обменом |
| webdev.http.https | HTTPS/TLS | invariant | шифрование трафика | безопасность |
| webdev.http.cookies | Куки и сессии | variant | хранение состояния между запросами | авторизация, корзина |
| webdev.http.stateless | HTTP без состояния | invariant | каждый запрос независим | нужны куки/токены для состояния |
| webdev.api.rest | ОТДЫХ API | invariant | ресурсы + HTTP-методы + представления | стандарт веб-API |
| webdev.api.json | JSON | invariant | формат обмена данными (ключ-значение) | API, конфиги |
| webdev.api.endpoint | Эндпоинт | invariant | URL-адрес ресурса/операции API | точка обращения |
| webdev.api.auth | Аутентификация API | invariant | API-ключи, токены (JWT), OAuth | контроль доступа |
| webdev.api.rate_limit | Ограничение запросов | variant | защита API от перегрузки | стабильность |
| webdev.api.versioning | Версионирование API | variant | /v1/, /v2/ — обратная совместимость | эволюция без поломок |
| webdev.api.graphql | ГрафQL | variant | клиент запрашивает ровно нужные данные | альтернатива REST |
| webdev.arch.client_server | Клиент-сервер | invariant | браузер ↔ сервер | архитектура веба |
| webdev.arch.frontend_backend | Фронтенд и бэкенд | invariant | интерфейс vs логика и данные | разделение ответственности |
| webdev.arch.spa | SPA (одностраничные приложения) | variant | контент обновляется без перезагрузки | Реагировать/Vue/Угловой |
| webdev.arch.ssr | Серверный рендеринг (SSR) | variant | страница собирается на сервере | скорость, SEO |
| webdev.arch.cdn | CDN | variant | раздача контента с ближних серверов | скорость загрузки |
| webdev.data.database | База данных веб-приложения | invariant | хранение данных (SQL/NoSQL) | персистентность |
| webdev.data.orm | ОРМ | variant | объекты ↔ таблицы БД | работа с данными в коде |
| webdev.sec.xss | XSS | invariant | внедрение скрипта; защита — экранирование | безопасность клиента |
| webdev.sec.csrf | CSRF | invariant | подделка запроса от имени пользователя; токены защищают | безопасность форм |
| webdev.sec.injection | Инъекции | invariant | непроверенный ввод → SQL/команды; параметризация | защита сервера |
| webdev.sec.input_validation | Валидация ввода | invariant | не доверять данным клиента | безопасность |
| webdev.perf.caching | Кэширование | variant | повторное использование ответов | скорость |
| webdev.perf.minification | Минификация и сжатие | variant | уменьшение размера файлов | быстрая загрузка |
| webdev.deploy.hosting | Хостинг и домены | variant | где живёт сайт, DNS-имя | публикация |
| webdev.deploy.ssl_cert | SSL-сертификат | variant | подтверждает HTTPS-шифрование | доверие, безопасность |
| webdev.tools.devtools | Инструменты разработчика | variant | инспектор, консоль, сеть в браузере | отладка |
