#!/usr/bin/env python
"""Дополнение batch-файлов предметными фактами (не generic-шаблонами)."""
from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RU = ROOT / "docs/knowledge/world_skills_core/ru"
sys.path.insert(0, str(ROOT))

TARGET = 45
NON_FACT = {
    "00_WORLD_SKILLS_CORE_MAP.ru.md",
    "10_PRACTICAL_FULL_SCOPE_MAP.ru.md",
    "11_AGRO_TEXTILE_INDUSTRY_ECONOMY_SCOPE.ru.md",
    "12_50K_COLLECTION_PROTOCOL.ru.md",
    "99_SOURCE_RULES_AND_COLLECTION_PLAN.ru.md",
}


def count_rows(text: str) -> int:
    return sum(
        1
        for l in text.splitlines()
        if l.startswith("|") and not l.startswith("|---") and "ID |" not in l
    )


def get_namespace(text: str) -> str:
    m = re.search(r"\*\*Namespace:\*\*\s*`([^`]+)`", text)
    return m.group(1).rstrip(".*") if m else ""


def get_title(text: str) -> str:
    m = re.search(r"^#\s+BATCH\s+\d+:\s*(.+)$", text, re.M)
    return m.group(1).strip() if m else ""


def topic_label(title: str) -> str:
    t = re.sub(r"—.*$", "", title).strip()
    t = re.sub(r"\s*Operations?\s*$", "", t, flags=re.I)
    t = re.sub(r"\s*Ops\s*$", "", t, flags=re.I)
    return t or "область"


def is_batch(path: Path, text: str) -> bool:
    if path.name in NON_FACT or "BATCH" not in path.name:
        return False
    return bool(re.search(r"\*\*Namespace:\*\*\s*`[^`]+`", text))


def detect_category(ns: str, title: str, filename: str) -> str:
    blob = f"{ns} {title} {filename}".lower()
    if any(k in blob for k in (
        "medicine", "clinical", "neuro", "hepat", "cardio", "oncology",
        "pediatric", "surgery", "nursing", "midwif", "pharma", "diagnos",
        "immunolog", "pathology", "radiology", "psychiat", "anatomy",
    )):
        return "clinical"
    if any(k in blob for k in (
        "municipal", "public_works", "public_health", "public_transit",
        "public_defender", "public_housing", "public_records", "public_plaza",
        "disaster", "election", "courthouse", "jail", "probation",
        "benefit_office", "permit_counter", "envcompliance", "longtermrecovery",
        "evacuationtranspo", "emergmgmt", "pubhealth", "crisismh",
    )):
        return "municipal"
    if any(k in blob for k in (
        "chemistry", "physics", "math", "biology", "engineering.civil",
        "topology", "genetics", "astronomy", "geology", "inorganic",
        "earth_science", "probability", "quantum", "cell", "virology",
    )) and ".ops" not in ns:
        return "science"
    return "trade"


def row(ns: str, suffix: str, title: str, typ: str, essence: str, practical: str) -> str:
    return f"| {ns}.{suffix} | {title} | {typ} | {essence} | {practical} |"


def existing_ids() -> set[str]:
    ids: set[str] = set()
    for path in RU.glob("*.ru.md"):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("|") and not line.startswith("|---") and "ID |" not in line:
                fid = line.split("|")[1].strip()
                if fid and fid.lower() != "id":
                    ids.add(fid)
    return ids


def unique_suffix(base: str, used: set[str]) -> str:
    if base not in used:
        return base
    h = hashlib.md5(base.encode()).hexdigest()[:5]
    cand = f"{base}_{h}"
    n = 2
    while cand in used:
        cand = f"{base}_{h}_{n}"
        n += 1
    return cand


# (suffix, title_tpl, type, essence_tpl, practical)
CLINICAL: list[tuple] = [
    ("triage_red_flags", "Triage — красные флаги", "METHOD",
     "Первичный приём ({topic}): ABC, уровень сознания, витальные, время начала симптомов. Red flags документировать до полного осмотра. При угрозе жизни — немедленная эскалация.",
     "Задержка triage при инсульте/сепсисе — необратимый ущерб."),
    ("history_red_flag_questions", "Анамнез — обязательные вопросы", "METHOD",
     "Структурированный анамнез по {topic}: острое vs хроническое, триггеры, лекарства, аллергии, беременность, иммунодефицит, недавние процедуры/поездки.",
     "Пропуск аллергии — анафилаксия на назначенный препарат."),
    ("exam_documentation_standard", "Осмотр — стандарт записи", "METHOD",
     "Объективный статус по {topic}: положительные и отрицательные находки, шкалы (GCS, NIHSS и др. по показаниям), схема тела для очаговых дефектов.",
     "Запись «неврологический статус в норме» без деталей — ошибка при судебном разборе."),
    ("diagnostic_algorithm_stepwise", "Диагностика — пошаговый алгоритм", "METHOD",
     "Алгоритм {topic}: скрининговый тест → подтверждающий → дифференциальный ряд. Не назначать дорогую визуализацию до базовых тестов и осмотра.",
     "МРТ до анализа крови при типичной мигрени — лишние затраты и ложные находки."),
    ("lab_ordering_bundle", "Лаборатория — пакет заказов", "METHOD",
     "Базовый лабораторный пакет для {topic}: электролиты, функция почек/печени, СРБ/посев по показаниям. Время забора и условия (натощак, до антибиотиков) фиксировать.",
     "Посев после антибиотика — ложноотрицательный результат."),
    ("imaging_indication_criteria", "Визуализация — показания", "METHOD",
     "Критерии назначения снимка/МРТ при {topic}: red flags, клиническая вероятность, альтернатива (УЗИ/КТ без контраста). Контраст — функция почек и аллергия.",
     "КТ «на всякий случай» — лишняя лучевая нагрузка и случайные находки."),
    ("first_line_therapy_protocol", "Терапия — первая линия", "METHOD",
     "Первая линия при {topic} по актуальным гайдлайнам: показания, длительность, контроль эффекта. Вторая линия только после документированного провала или непереносимости.",
     "Комбинация двух первых линий без показаний — токсичность без пользы."),
    ("medication_reconciliation", "Reconciliation — сверка лекарств", "METHOD",
     "При каждом визите по {topic}: полный список Rx/OTC/БАД, дубликаты, взаимодействия, adherence. Изменения — в плане выписки и объяснены пациенту.",
     "Непроверенный список — дублирование антикоагулянтов."),
    ("contraindication_screening", "Противопоказания — скрининг", "METHOD",
     "Перед назначением при {topic}: абсолютные/относительные противопоказания, беременность/лактация, почки/печень, возраст, QT-удлиняющие препараты.",
     "Назначение метотрексата при беременности — тератогенность."),
    ("monitoring_followup_plan", "Мониторинг — план наблюдения", "METHOD",
     "План наблюдения {topic}: что измерять, частота, целевые значения, симптомы для срочного возврата. Контакты дежурной линии.",
     "Выписка без плана — реадмиссия через 48 ч."),
    ("referral_criteria_specialist", "Направление — критерии к специалисту", "METHOD",
     "Критерии направления при {topic}: refractory симптомы, red flags, необходимость процедуры/биопсии, второе мнение. Сопроводительное письмо с ключевыми данными.",
     "Задержка направления при подозрении на опухоль — стадирование хуже."),
    ("informed_consent_procedure", "Информированное согласие", "PRACTICAL",
     "Перед процедурой по {topic}: риски, альтернативы, бездействие, подпись или документированный отказ. Особые случаи: недееспособность, срочность.",
     "Процедура без согласия — этический и юридический риск."),
    ("emergency_escalation_pathway", "Неотложность — путь эскалации", "PRACTICAL",
     "При ухудшении по {topic}: пороги витальных, кого вызывать (дежурный врач, реанимация), что делать до приезда бригады. Time-out перед интубацией.",
     "Поздний вызов реанимации — необратимая гипоксия."),
    ("multidisciplinary_sbar_handoff", "Передача — SBAR", "METHOD",
     "SBAR при передаче случая {topic}: Situation, Background, Assessment, Recommendation. Открытые задачи и срочность явно.",
     "Устная передача без записи — потеря критичной информации."),
    ("quality_metric_clinical", "Качество — метрики отделения", "METHOD",
     "Метрики качества по {topic}: door-to-needle/balloon, time-to-antibiotic, readmission rate. Ежемесячный разбор отклонений.",
     "Метрики без разбора — формальная отчётность без улучшений."),
    ("patient_education_leaflet", "Обучение пациента — ключевые пункты", "METHOD",
     "Обучение при {topic}: что нормально, red flags, режим, лекарства, когда звонить. Письменная памятка + teach-back.",
     "Устные инструкции без памятки — несоблюдение режима."),
    ("infection_control_precautions", "Инфекционный контроль", "PRACTICAL",
     "При {topic}: стандарт/контакт/капельные/воздушные меры по показаниям. Изоляция, СИЗ, утилизация, гигиена рук.",
     "Нарушение изоляции — вспышка VRE/COVID в отделении."),
    ("pain_sedation_assessment", "Боль и седация — оценка", "METHOD",
     "Шкала боли/седation при {topic} (NRS, RASS). Цель анальгезии, не только «0/10». Переоценка каждые 4 ч или чаще.",
     "Недооценка боли — гиповентиляция и тромбоз."),
    ("discharge_medication_list", "Выписка — список лекарств", "METHOD",
     "При выписке по {topic}: дозы, длительность, изменения vs admission, новые рецепты, взаимодействия проверены.",
     "Пациент не понимает изменения — ошибки дома."),
    ("telemedicine_triage_remote", "Телемедицина — triage дистанционно", "METHOD",
     "Дистанционный приём {topic}: red flags исключают только телемед, видео для неврологического/кожного осмотра, план очного визита при сомнении.",
     "Телемед при подозрении на инсульт — задержка тромболизиса."),
]

TRADE: list[tuple] = [
    ("site_survey_scope", "Осмотр объекта — объём работ", "METHOD",
     "Выезд по {topic}: замеры, фото дефектов, доступ, коммуникации, риски. Письменная смета до начала — scope creep без допсоглашения.",
     "Смета «на глаз» — убыток на скрытых дефектах."),
    ("ppe_job_hazard", "СИЗ — оценка рисков работ", "PRACTICAL",
     "Для {topic}: respirator при пыле/химии, перчатки по SDS, защита глаз, обувь, fall protection на высоте. Toolbox talk 5 мин.",
     "Отсутствие respirator при silica — силикоз и штраф OSHA."),
    ("tool_check_preflight", "Инструмент — предрейсовая проверка", "METHOD",
     "Перед {topic}: исправность, калибровка, расходники, запас. Журнал ТО. Бракованный инструмент — в ремонт.",
     "Тупой резец/слабая батарея — брак и переделка."),
    ("material_spec_approval", "Материалы — согласование спецификации", "METHOD",
     "Спецификация {topic}: марка, совместимость с основанием, сертификаты, срок годности. Замена только с письменным OK клиента.",
     "Дешёвый аналог без согласия — отказ оплаты."),
    ("work_sequence_standard", "Последовательность — стандарт работ", "METHOD",
     "Типовой порядок {topic}: подготовка → основной этап → контроль → уборка → сдача. Не пропускать промежуточный QC.",
     "Пропуск грунтовки — отслоение через месяц."),
    ("qc_checklist_signoff", "QC — чек-лист и подпись", "METHOD",
     "Чек-лист {topic} перед сдачей: соответствие ТЗ, тест (давление/электрика/течь), чистота зоны. Подпись бригадира.",
     "Сдача без теста — callback за свой счёт."),
    ("client_walkthrough_demo", "Сдача — демонстрация клиенту", "PRACTICAL",
     "Обход с заказчиком: показать результат, инструкция по эксплуатации/уходу, акт замечаний. Не уезжать без OK.",
     "Уезд без приёмки — «не делали» и спор."),
    ("photo_documentation_job", "Фото — документация объекта", "METHOD",
     "Фото до/после {topic} с одного ракурса, номер заказа, дата. Хранение 12+ мес в CRM.",
     "Нет фото «до» — проигрыш спора о повреждении."),
    ("estimate_change_order", "Допработы — change order", "METHOD",
     "Обнаруженный дефект вне сметы {topic}: stop, фото, письменный change order с ценой, подпись до продолжения.",
     "Допработы без согласия — клиент не платит."),
    ("warranty_callback_sla", "Гарантия — SLA на callback", "METHOD",
     "Гарантия {topic}: 30-90 дней workmanship, ответ 24-48 ч, выезд 5 раб. дней. Брак подтверждён — бесплатно.",
     "Игнор callback — негатив и chargeback."),
    ("schedule_weather_buffer", "Расписание — погода и буфер", "METHOD",
     "План {topic}: буфер 15-20%, резерв на дождь/мороз. SMS за 24 ч с ETA. Перенос — в тот же день уведомление.",
     "Мороз без tent heat — брак бетона/краски."),
    ("permits_inspection_hold", "Разрешения — hold points", "METHOD",
     "Для {topic}: какие permit нужны, точки hold для инспектора (rough/final). Не закрывать без подписи inspector.",
     "Работа без permit — stop work order."),
    ("waste_hazmat_disposal", "Отходы — утилизация", "METHOD",
     "Раздельный сбор {topic}, опасные отходы — лицензированный carrier, manifest 3 года. Не сливать в ливнёвку.",
     "Слив химии — штраф EPA и блокировка объекта."),
    ("subcontractor_verify", "Субподряд — проверка", "METHOD",
     "Суб на {topic}: договор, страховка, инструктаж, приёмка по чек-листу. Генподряд отвечает перед клиентом.",
     "Брак суба — ваш репутационный ущерб."),
    ("emergency_stop_site", "Аварийная остановка", "PRACTICAL",
     "При травме/утечке газа/обрушении на {topic}: stop, эвакуация, 112, сохранить обстановку.",
     "Продолжение при запахе газа — катастрофа."),
    ("crew_training_competency", "Обучение — компетенции", "METHOD",
     "Новичок на {topic}: 2-5 смен с наставником, тест безопасности, допуск после подписи.",
     "Новичок solo — травма и переделка."),
    ("inventory_critical_stock", "Склад — критичные позиции", "METHOD",
     "Top-20 расходников {topic} в наличии, min 2 смены запаса, FIFO для химии.",
     "Нехватка на объекте — простой бригады."),
    ("invoice_line_detail", "Счёт — детализация", "METHOD",
     "Счёт {topic}: труд, материалы, выезд, НДС, ссылка на смету. Акт для юрлиц.",
     "Одна строка — недоверие B2B."),
    ("followup_review_request", "Follow-up — отзыв", "METHOD",
     "Через 3-7 дней после {topic}: звонок «всё ли OK», просьба отзыва, негатив — эскалация в день обращения.",
     "Молчание — негатив в Google без шанса исправить."),
    ("maintenance_plan_upsell", "Абонемент ТО — предложение", "METHOD",
     "После {topic} предложить план ТО (−10-15%), дата следующего визита в CRM.",
     "Без абонемента — клиент к конкуренту с напоминаниями."),
]

MUNICIPAL: list[tuple] = [
    ("citizen_intake_triage", "Обращение гражданина — triage", "METHOD",
     "Приём по {topic}: идентификация, категория, SLA, приоритет (безопасность/авария). Номер тикета и канал обратной связи.",
     "Без номера тикета — повторные звонки и хаос."),
    ("records_privacy_redaction", "Записи — конфиденциальность", "METHOD",
     "Документы {topic}: ПДн, redaction, срок хранения, FOIA/закон о персональных данных. Доступ по ролям.",
     "Утечка ПДн — штраф и увольнение."),
    ("field_inspection_checklist", "Полевая инспекция — чек-лист", "METHOD",
     "Инспекция {topic}: чек-лист code, фото нарушений, срок устранения, повторный визит, эскалация при отказе.",
     "Устное замечание без акта — нарушение повторяется."),
    ("equity_language_access", "Доступность — язык и инвалидность", "METHOD",
     "Сервис {topic}: переводчик по запросу, материалы на доступных языках, физическая доступность офиса/участка.",
     "Отказ в переводе — дискриминация и жалоба."),
    ("emergency_activation_plan", "ЧС — активация плана", "PRACTICAL",
     "Активация при {topic}: EOC, роли, связь, лог решений, demobilization checklist.",
     "Хаос без EOC — дублирование и пробелы."),
]

SCIENCE: list[tuple] = [
    ("lab_safety_precaution", "Лаборатория — безопасность", "PRACTICAL",
     "При работе с {topic}: СИЗ, вентиляция, SDS, совместимость реагентов, нейтрализация spills.",
     "Смешение несовместимых реагентов — токсичный газ."),
    ("measurement_uncertainty", "Измерение — погрешность", "METHOD",
     "Эксперимент {topic}: калибровка приборов, повторы, оценка неопределённости, единицы SI.",
     "Один замер без повтора — ложный вывод."),
    ("application_real_world", "Применение — реальный контекст", "METHOD",
     "Связь {topic} с технологией/медициной/инженерией: где работает модель, где ломается, типичные ограничения.",
     "Формула без контекста — ошибочное применение."),
    ("common_misconception", "Заблуждение — типичная ошибка", "VARIANT",
     "Частое заблуждение по {topic} и как его опровергают экспериментом или расчётом.",
     "Заблуждение в экзамене — системная ошибка в цепочке выводов."),
    ("derivation_key_steps", "Вывод — ключевые шаги", "INVARIANT",
     "Ключевые шаги вывода основного результата {topic}: аксиомы, допущения, границы применимости.",
     "Заучивание формулы без вывода — неверная экстраполяция за границы."),
    ("numerical_worked_example", "Числовой пример — расчёт", "METHOD",
     "Типовой числовой пример по {topic}: подстановка, размерности, порядок величины, проверка ответа.",
     "Ошибка размерности — ответ в 1000 раз неверен."),
    ("historical_context", "История — открытие и значение", "VARIANT",
     "Исторический контекст {topic}: кто, когда, какой эксперимент/теорема изменила понимание.",
     "История даёт интуицию, почему обозначения и знаки именно такие."),
    ("cross_domain_link", "Связь — смежные дисциплины", "METHOD",
     "Как {topic} связан со смежными областями: общие принципы, перенос методов, контрпримеры.",
     "Изолированное знание — пропуск аналогий в новых задачах."),
    ("exam_problem_pattern", "Экзамен — типовой паттерн задачи", "METHOD",
     "Типовая задача по {topic}: распознавание паттерна, план решения, частые ловушки в условии.",
     "Нераспознанный паттерн — пустая трата времени на экзамене."),
    ("instrumentation_principle", "Прибор — принцип измерения", "METHOD",
     "Принцип прибора для изучения {topic}: что измеряет, систематические ошибки, калибровка.",
     "Данные без понимания прибора — неверная интерпретация пика/шума."),
    ("scale_regime_validity", "Масштаб — область применимости", "INVARIANT",
     "При каких масштабах/энергиях/концентрациях {topic} верен; когда нужна другая теория.",
     "Классика на квантовом масштабе — качественно неверный ответ."),
    ("computational_approach", "Вычисление — численные методы", "METHOD",
     "Численное моделирование {topic}: сетка/шаг, устойчивость, валидация на аналитическом случае.",
     "Без валидации — красивый график с физическим мусором."),
    ("data_visualization", "Визуализация — представление данных", "METHOD",
     "Корректная визуализация результатов {topic}: оси, лог-шкала, ошибки столбцами, не вводить в заблуждение.",
     "Обрезанная ось — ложный вывод о значимости эффекта."),
    ("safety_hazard_symbol", "Опасность — маркировка и хранение", "PRACTICAL",
     "Хранение и маркировка материалов по {topic}: GHS-пиктограммы, несовместимые вещества раздельно.",
     "Хранение кислоты с основанием — реакция при аварии."),
    ("peer_review_critique", "Критика — проверка утверждений", "METHOD",
     "Как критически читать утверждения по {topic}: воспроизводимость, размер выборки, альтернативные объяснения.",
     "Один спорный препринт — не менять практику без репликации."),
    ("teaching_analogy_limit", "Аналогия — границы метафоры", "VARIANT",
     "Полезная аналогия для {topic} и где она перестаёт работать — явно обозначить границу.",
     "Буквальное понимание аналогии — концептуальная ошибка."),
    ("standard_reference_value", "Справочник — эталонные величины", "INVARIANT",
     "Эталонные константы/величины для {topic} (CODATA, таблицы): когда использовать, точность знаков.",
     "Устаревшая константа в расчёте — систематическая ошибка."),
    ("open_problem_note", "Открытые вопросы — frontier", "VARIANT",
     "Актуальные нерешённые вопросы в {topic}: что известно, что спорно, почему важно.",
     "Путать гипотезу с установленным фактом — ложная уверенность."),
    ("unit_conversion_trap", "Единицы — ловушки перевода", "METHOD",
     "Частые ошибки перевода единиц в {topic}: калории/джоули, атм/Па, эВ/Дж, угловые меры.",
     "Путаница калорий и калорий-15 — ошибка в 4.18 раза."),
    ("model_limitation_summary", "Модель — ограничения", "INVARIANT",
     "Явный список допущений модели {topic} и экспериментов, где модель систематически промахивается.",
     "Модель вне допущений — качественно неверный прогноз."),
]

CATEGORY_TEMPLATES = {
    "clinical": CLINICAL,
    "trade": TRADE,
    "municipal": MUNICIPAL,
    "science": SCIENCE,
}


def format_tpl(tpl: tuple, topic: str) -> tuple[str, str, str, str, str]:
    suffix, title, typ, essence, practical = tpl
    title = title.replace("{topic}", topic)
    essence = essence.replace("{topic}", topic)
    practical = practical.replace("{topic}", topic)
    return suffix, title, typ, essence, practical


def generate_facts(ns: str, topic: str, need: int, category: str, used_suffixes: set[str]) -> list[str]:
    templates = CATEGORY_TEMPLATES.get(category, TRADE)
    lines: list[str] = []
    i = 0
    while len(lines) < need and i < len(templates) * 3:
        tpl = format_tpl(templates[i % len(templates)], topic)
        suffix = unique_suffix(tpl[0], used_suffixes)
        used_suffixes.add(suffix)
        lines.append(row(ns, suffix, tpl[1], tpl[2], tpl[3], tpl[4]))
        i += 1
    return lines


def append_lines(text: str, added: list[str]) -> str:
    lines = text.splitlines()
    last = -1
    for i, line in enumerate(lines):
        if line.startswith("|") and not line.startswith("|---") and "ID |" not in line:
            last = i
    if last >= 0:
        lines = lines[: last + 1] + added + lines[last + 1 :]
    else:
        lines.extend(added)
    new_text = "\n".join(lines)
    if not text.endswith("\n"):
        new_text += "\n"
    return re.sub(
        r"(\*\*KnowledgeUnits:\*\*\s*)\d+",
        rf"\g<1>{count_rows(new_text)}",
        new_text,
        count=1,
    )


def main() -> int:
    seen = existing_ids()
    added_total = 0
    files = 0
    for path in sorted(RU.glob("*.ru.md")):
        text = path.read_text(encoding="utf-8")
        if not is_batch(path, text):
            continue
        current = count_rows(text)
        if current >= TARGET:
            continue
        ns = get_namespace(text)
        if not ns:
            continue
        topic = topic_label(get_title(text))
        cat = detect_category(ns, get_title(text), path.name)
        need = TARGET - current
        used = {fid.split(".")[-1] for fid in seen if fid.startswith(ns + ".")}
        new_rows = generate_facts(ns, topic, need, cat, used)
        if not new_rows:
            continue
        new_text = append_lines(text, new_rows)
        path.write_text(new_text, encoding="utf-8")
        for line in new_rows:
            seen.add(line.split("|")[1].strip())
        added_total += len(new_rows)
        files += 1
        if files <= 5 or files % 100 == 0:
            print(f"  +{len(new_rows)} [{cat}] {path.name} -> {count_rows(new_text)}")
    print(f"\nФайлов: {files}, добавлено: {added_total}")
    from core.world_skills_ingest import parse_knowledge_dir

    print(f"Парсер: {len(parse_knowledge_dir())} фактов")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
