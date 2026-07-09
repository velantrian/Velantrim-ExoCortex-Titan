# BATCH_100 — Programming Languages & Paradigms: Syntax, Idioms, Ecosystems
# world_skills_core · source: world_skills_core:batch_100:programming
# KnowledgeUnits: 45

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| proglang.concept.variable | Переменная | invariant | именованная ячейка для данных | хранение состояния |
| proglang.concept.types | Типы данных | invariant | число, строка, логический, список, словарь | корректность операций |
| proglang.concept.control_flow | Управление потоком | invariant | условия (if), циклы (for/while) | логика программы |
| proglang.concept.function | Функция | invariant | переиспользуемый блок с входом/выходом | модульность |
| proglang.concept.scope | Область видимости | invariant | где доступна переменная (локальная/глобальная) | избегание ошибок |
| proglang.concept.recursion | Рекурсия | invariant | функция вызывает себя | деревья, делегирование |
| proglang.concept.error_handling | Обработка ошибок | invariant | try/except, коды возврата | устойчивость программ |
| proglang.concept.io | Ввод-вывод | invariant | чтение/запись файлов, консоли, сети | взаимодействие с миром |
| proglang.typing.static_dynamic | Статическая vs динамическая типизация | invariant | типы при компиляции (Java) vs во время выполнения (Python) | надёжность vs гибкость |
| proglang.typing.strong_weak | Сильная vs слабая типизация | variant | строгость неявных преобразований | предсказуемость |
| proglang.paradigm.imperative | Императивное программирование | invariant | последовательность команд, изменяющих состояние | C, Python-стиль |
| proglang.paradigm.oop | ООП | invariant | объекты с данными и методами; инкапсуляция, наследование | моделирование сущностей |
| proglang.paradigm.functional | Функциональное | invariant | чистые функции, неизменяемость, функции высшего порядка | предсказуемость, параллелизм |
| proglang.paradigm.declarative | Декларативное | variant | что нужно, а не как (SQL, HTML) | абстракция от реализации |
| proglang.python.role | Python | variant | читаемый, динамический; ML, скрипты, бэкенд | универсальный язык |
| proglang.python.idioms | Питонические идиомы | variant | list comprehension, контекст-менеджеры, утиная типизация | чистый код |
| proglang.js.role | JavaScript | variant | язык веба (браузер) + Node.js (сервер) | фронтенд и фуллстек |
| proglang.js.async | Асинхронность в JS | variant | колбэки, промисы, async/await | неблокирующий ввод-вывод |
| proglang.java.role | Java | variant | статическая типизация, JVM, «написал раз — запускай везде» | enterprise, Android |
| proglang.c.role | C | variant | низкоуровневый, ручная память, скорость | системы, встраиваемое |
| proglang.cpp.role | C++ | variant | C + ООП + шаблоны; производительность | игры, системы, HPC |
| proglang.rust.role | Rust | variant | безопасность памяти без сборщика мусора (borrow checker) | системы без утечек/гонок |
| proglang.go.role | Go | variant | простота, конкурентность (goroutines), компиляция | серверы, облако |
| proglang.sql.role | SQL | invariant | декларативный язык запросов к реляционным БД | работа с данными |
| proglang.compile.compiler | Компилятор | invariant | переводит код в машинный заранее | скорость исполнения |
| proglang.compile.interpreter | Интерпретатор | invariant | исполняет код построчно | гибкость, отладка |
| proglang.compile.bytecode | Байт-код и виртуальная машина | variant | промежуточный код для VM (JVM, .NET, Python) | переносимость |
| proglang.memory.gc | Сборка мусора | invariant | автоматическое освобождение памяти | удобство (Java, Python, Go) |
| proglang.memory.manual | Ручное управление памятью | variant | malloc/free (C) — мощно, но опасно | утечки, контроль |
| proglang.memory.ownership | Владение и заимствование (Rust) | variant | компилятор гарантирует безопасность памяти | без GC и без гонок |
| proglang.practice.naming | Именование | invariant | понятные имена переменных и функций | читаемость кода |
| proglang.practice.dry | Принцип DRY | invariant | не повторяйся — выноси в функции/модули | поддерживаемость |
| proglang.practice.comments | Комментарии и документация | invariant | объяснять «почему», не «что» | понимание кода |
| proglang.practice.refactoring | Рефакторинг | invariant | улучшение структуры без смены поведения | здоровье кодовой базы |
| proglang.practice.code_review | Код-ревью | variant | проверка коллегами до слияния | качество, обмен знаниями |
| proglang.testing.unit | Модульные тесты | invariant | проверка отдельных функций | защита от регрессий |
| proglang.testing.tdd | Разработка через тесты (TDD) | variant | тест → код → рефакторинг | дизайн и надёжность |
| proglang.version.git | Система контроля версий (Git) | invariant | история изменений, ветки, откат, совместная работа | основа разработки |
| proglang.version.branching | Ветвление и слияние | variant | параллельная работа над фичами | командная разработка |
| proglang.ecosystem.package | Менеджеры пакетов | invariant | pip, npm, cargo — зависимости и версии | переиспользование библиотек |
| proglang.ecosystem.dependency | Управление зависимостями | variant | версии, конфликты, lock-файлы | воспроизводимость сборки |
| proglang.ds.choice | Выбор структуры данных | invariant | список/словарь/множество под задачу | производительность |
| proglang.algo.complexity_practice | Сложность на практике | invariant | избегать O(n²) там, где есть O(n log n) | скорость на больших данных |
| proglang.debug.methods | Отладка | invariant | логи, отладчик, бинарный поиск ошибки | поиск и устранение багов |
| proglang.security.input_validation | Валидация ввода | invariant | не доверять внешним данным | защита от инъекций и сбоев |
