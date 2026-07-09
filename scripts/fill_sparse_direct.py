#!/usr/bin/env python
"""Прямое дополнение неполных batch-файлов до 45 фактов."""
from __future__ import annotations

import glob
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RU = ROOT / "docs/knowledge/world_skills_core/ru"
sys.path.insert(0, str(ROOT))


def count_rows(text: str) -> int:
    return sum(
        1 for l in text.splitlines()
        if l.startswith("|") and not l.startswith("|---") and "ID |" not in l
    )


def get_namespace(text: str) -> str:
    m = re.search(r"\*\*Namespace:\*\*\s*`([^`]+)`", text)
    return m.group(1) if m else "unknown.ops"


def existing_ids() -> set[str]:
    ids: set[str] = set()
    for path in RU.glob("*.ru.md"):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("|") and not line.startswith("|---") and "ID |" not in line:
                fid = line.split("|")[1].strip()
                if fid and fid.lower() != "id":
                    ids.add(fid)
    return ids


def row(ns: str, suffix: str, title: str, typ: str, essence: str, practical: str) -> str:
    return f"| {ns}.{suffix} | {title} | {typ} | {essence} | {practical} |"


def append_facts(filename: str, facts: list[tuple], seen: set[str]) -> int:
    path = RU / filename
    if not path.exists():
        print(f"  SKIP missing {filename}")
        return 0
    text = path.read_text(encoding="utf-8")
    ns = get_namespace(text)
    current = count_rows(text)
    target = 45
    need = max(0, target - current)
    if need == 0:
        print(f"  OK {filename} already {current}")
        return 0

    added_lines: list[str] = []
    for suffix, title, typ, essence, practical in facts:
        if len(added_lines) >= need:
            break
        fid = f"{ns}.{suffix}"
        if fid in seen:
            continue
        added_lines.append(row(ns, suffix, title, typ, essence, practical))
        seen.add(fid)

    if not added_lines:
        print(f"  WARN no new facts for {filename}")
        return 0

    lines = text.splitlines()
    last_row = -1
    for i, line in enumerate(lines):
        if line.startswith("|") and not line.startswith("|---") and "ID |" not in line:
            last_row = i
    if last_row >= 0:
        lines = lines[: last_row + 1] + added_lines + lines[last_row + 1 :]
    else:
        lines.extend(added_lines)

    new_text = "\n".join(lines)
    if not text.endswith("\n"):
        new_text += "\n"
    new_text = re.sub(
        r"(\*\*KnowledgeUnits:\*\*\s*)\d+",
        rf"\g<1>{count_rows(new_text)}",
        new_text,
        count=1,
    )
    path.write_text(new_text, encoding="utf-8")
    print(f"  +{len(added_lines)} {filename} -> {count_rows(new_text)}")
    return len(added_lines)


# --- ФАКТЫ ПО ФАЙЛАМ ---
RETAIL = [
    ("goods_receiving_dock", "Приёмка товара — док и сверка", "METHOD",
     "Приёмка на рампе: сверка накладной поставщика с заказом PO, подсчёт коробов и паллет, проверка целостности упаковки и сроков годности. Сканирование штрих-кодов в WMS, фиксация расхождений (over/short/damage) в акте приёмки до подписания.",
     "Подпись без сверки — спор с поставщиком и ошибки остатков в системе."),
    ("shelf_replenishment_task", "Пополнение полок — задание из WMS", "METHOD",
     "Пополнение с полочного запаса (backstock): система генерирует pick-list по минимальным остаткам на полке. Сотрудник сканирует ячейку склада, переносит товар на торговый зал, сканирует полочную метку, выставляет facing по планограмме.",
     "Пополнение без сканирования — расхождение полка/книга и ложные out-of-stock."),
    ("price_change_labeling", "Смена цен — переоценка и этикетки", "METHOD",
     "Переоценка: загрузка файла цен из HQ, печать shelf labels (ESL или бумажные), снятие старых ценников, проверка 10% SKU выборочно. Акционные цены: дата начала/окончания, автоматический откат в POS.",
     "Старая цена на полке при новой в кассе — жалобы и штрафы контроля."),
    ("returns_policy_processing", "Возвраты — проверка и оформление", "METHOD",
     "Возврат без чека: поиск транзакции по карте/дате/сумме. Проверка состояния товара (неоткрытая упаковка, комплектность). Возврат на тот же способ оплаты по PCI. Товар defect — в карантинную зону, не на полку.",
     "Возврат испорченного товара на полку — повторная продажа и репутационный риск."),
    ("shrink_audit_monthly", "Аудит потерь — ежемесячный разбор", "METHOD",
     "Ежемесячный shrink review: сравнение продаж, приёмок, списаний и инвентаризации. Топ-20 SKU с расхождениями, видео по подозрительным транзакциям, корректирующие действия (обучение, EAS, камеры).",
     "Shrink >2% оборота — убыток магазина без анализа причин."),
    ("staff_scheduling_peak", "Расписание персонала — пиковые часы", "METHOD",
     "Планирование смен по трафику: пик 17:00-20:00 — максимум кассиров и зала. Labor cost % цель 8-12% для grocery. Break compliance: перерывы по трудовому закону, не закрывать все кассы одновременно.",
     "Одна касса в пик — очередь и потеря покупателей."),
    ("vendor_compliance_chargeback", "Штрафы поставщику — chargeback", "METHOD",
     "Chargeback за нарушение поставки: поздняя доставка, неполный заказ, неправильная маркировка, повреждение. Документировать фото и акт, удержание из следующего платежа по договору.",
     "Без chargeback поставщик повторяет сбои без последствий."),
    ("click_collect_picking", "Click & Collect — сбор заказа", "METHOD",
     "Сбор онлайн-заказа: pick по маршруту зала (минимизация пробега), замена отсутствующего SKU по правилам (аналог, отмена позиции). Упаковка с чеком, холодовая цепь для заморозки, выдача по коду/QR.",
     "Перепутанный заказ — возврат и негативный отзыв."),
    ("fresh_department_rotation", "Свежие отделы — ротация FIFO", "METHOD",
     "Ротация скоропорта: FIFO на полке и в холодильнике, снятие просрочки 2 раза в день, температурный журнал холодильников 2-8°C. Markdown просрочки за 1-2 дня до даты — снижение списаний.",
     "Просрочка на полке — штраф Роспотребнадзора и отравления."),
    ("cash_handling_till_float", "Касса — разменный фонд и инкассация", "METHOD",
     "Разменный фонд (float): фиксированная сумма в начале смены, сверка в конце. Инкассация: двое лиц, сейф, лимит наличных в кассе. Подозрительные купюры — отложить, не выдавать сдачу.",
     "Превышение лимита наличных — риск ограбления."),
    ("mystery_shopper_program", "Тайный покупатель — программа", "METHOD",
     "Mystery shopper: чек-лист приветствие, знание товара, чистота, очередь. Результаты — обучение смены, не наказание без разбора. Частота 1-2 раза в месяц на магазин.",
     "Игнорирование отчётов — формальная программа без эффекта."),
    ("promotional_display_setup", "Промо-стойка — монтаж и демонтаж", "METHOD",
     "Промо end-cap: сборка по инструкции бренда, ценник акции, дата окончания, запас на backstock. После акции — возврат планограммы, списание остатков по политике.",
     "Забытая акционная цена — продажа ниже себестоимости."),
    ("basket_analysis_conversion", "Конверсия и средний чек — анализ", "METHOD",
     "KPI: conversion rate (покупатели/посетители), ATV (средний чек), UPT (единиц на чек). Heatmap зала, A/B тест выкладки. Upsell на кассе — лимит 15 секунд чтобы не замедлять очередь.",
     "Только выручка без UPT — рост за счёт инфляции, не эффективности."),
    ("store_opening_checklist", "Открытие магазина — чек-лист", "PRACTICAL",
     "Утро: разблокировка, включение света и HVAC, проверка холодильников, выкат тележек, кассы self-test, вывеска «открыто», безопасность (замки, сигнализация).",
     "Пропуск теста кассы — сбои в первый час пика."),
    ("store_closing_checklist", "Закрытие магазина — чек-лист", "PRACTICAL",
     "Вечер: выгон посетителей, подсчёт касс, Z-report, уборка зала, блокировка входов, постановка на сигнализацию, сейф, ключи по регламенту.",
     "Забытый Z-report — расхождение выручки наутро."),
    ("food_sampling_hygiene", "Дегустации — гигиена и разрешения", "METHOD",
     "Дегустация: одноразовые шпажки/стаканчики, перчатки, накрытие, срок открытой упаковки, журнал. Разрешение местной санэпидслужбы где требуется.",
     "Повторное использование шпажек — нарушение СанПиН."),
    ("gift_card_activation", "Подарочные карты — активация и учёт", "METHOD",
     "Активация gift card в POS, проверка баланса, запрет обналичивания где запрещено законом. Учёт неактивированных карт на складе — инвентаризация как ценности.",
     "Кража неактивированных карт — прямой убыток."),
    ("loyalty_program_enrollment", "Программа лояльности — регистрация", "METHOD",
     "Регистрация карты лояльности: минимум полей (телефон/email), согласие на рассылку отдельным чекбоксом. Начисление баллов в реальном времени, возврат — списание баллов.",
     "Начисление без согласия на ПДн — нарушение 152-ФЗ."),
    ("seasonal_reset_planogram", "Сезонный reset — смена планограммы", "METHOD",
     "Сезонная перестановка: демонтаж старой коллекции, markdown, новая планограмма из HQ, обучение сотрудников за 1 неделю до старта, контроль OSA в первые 3 дня.",
     "Смешение сезонов на полке — путаница покупателя и списания."),
    ("damaged_goods_markdown", "Брак и уценка — политика", "METHOD",
     "Повреждённая упаковка: уценка 10-30% по матрице, стикер «уценка», отдельная зона. Не продавать вскрытые пищевые без разрешения. Списание в систему с причиной code.",
     "Уценка без стикера — спор на кассе и обвинение в обмане."),
    ("queue_management_belt", "Управление очередью — лента и host", "METHOD",
     "Кассовая зона: лента ограждения, host направляет в короткую очередь, express lane до 10 позиций, открытие дополнительной кассы при ожидании >3 мин.",
     "Длинная очередь без реакции — уход покупателя без покупки."),
    ("alcohol_tobacco_compliance", "Алкоголь и табак — комплаенс", "METHOD",
     "Продажа 18+: сканирование паспорта/2D-кода, отказ при сомнении, журнал отказов, отдельная касса где требуется. Хранение алкоголя в locked cabinet после 22:00 в некоторых форматах.",
     "Продажа несовершеннолетнему — лишение лицензии."),
    ("ecommerce_bopis_handoff", "BOPIS — выдача интернет-заказа", "METHOD",
     "Buy Online Pick Up In Store: заказ в staging zone, проверка ID, подпись клиента, возврат незабранного через 7 дней — возврат на полку или списание.",
     "Выдача без проверки — кража чужого заказа."),
    ("supplier_fill_rate_kpi", "Fill rate поставщика — KPI", "METHOD",
     "Fill rate = поставлено/заказано × 100%. Цель >95% для A-поставщиков. Еженедельный отчёт, эскалация при <90% три недели подряд, резервный поставщик для критичных SKU.",
     "Низкий fill rate — пустые полки при наличии на центральном складе."),
    ("training_pos_new_hire", "Обучение кассира — новый сотрудник", "METHOD",
     "Онбординг кассира: 4-8 часов shadowing, возвраты, возрастные ограничения, безопасность, PCI (не записывать карту), тестовая транзакция под надзором.",
     "Кассир без обучения возвратам — финансовые потери и конфликты."),
    ("cleaning_schedule_retail", "График уборки торгового зала", "METHOD",
     "Уборка: подметание каждые 2 часа в пик, ночная влажная уборка, дезинфекция тележек и корзин ежедневно, журнал уборки туалетов каждые 2 часа в ТЦ.",
     "Грязный зал — снижение NPS и жалобы."),
    ("energy_retail_hvac_light", "Энергия — HVAC и освещение", "METHOD",
     "Экономия: LED, датчики движения в подсобках, HVAC setpoint 22°C летом, ночной setback, закрытие холодильных крышек ночью в некоторых форматах.",
     "Открытые кейсы ночью — +15% электроэнергии отдела."),
    ("incident_report_slip_fall", "Инцидент — падение покупателя", "PRACTICAL",
     "При падении: оказать помощь, не признавать вину, фото места, свидетели, инцидент-репорт, страховой контакт, сохранить записи CCTV 30 дней.",
     "Извинение с признанием вины — юридический риск в суде."),
    ("rfid_inventory_pilot", "RFID — пилот инвентаризации", "METHOD",
     "RFID: метки на apparel, считывание порталом или ручным reader, инвентаризация за минуты vs дни. Интеграция с EAS. Пилот на 1 отделе перед rollout.",
     "RFID на металле — помехи, нужна правильная метка."),
    ("self_checkout_assist", "КСО — помощь и антифрод", "METHOD",
     "Самокасса: attendant наблюдает, intervention при алерте (несканированный товар, вес), обучение пожилых, отключение при повторных алертах одного клиента.",
     "КСО без attendant — shrink выше на 30-50%."),
    ("bakery_production_label", "Выпечка — маркировка и срок", "METHOD",
     "Собственная выпечка: этикетка состав, аллергены, дата изготовления, срок 24-72 ч, markdown вечером, списание в конце дня.",
     "Без аллергенов на этикетке — ответственность при анафилаксии."),
    ("butcher_food_safety", "Мясной отдел — безопасность", "METHOD",
     "Разделка: отдельные доски и ножи для сырого/готового, температура витрины 0-4°C, смена перчаток между видами мяса, санитарная обработка в конце смены.",
     "Кросс-контаминация — сальмонелла и отзыв партии."),
    ("produce_misting_quality", "Овощи — увлажнение и качество", "METHOD",
     "Misting овощей: не переувлажнять (гниение), убрать гнилые единицы 3 раза в день, FIFO, температура 10-15°C для большинства овощей.",
     "Гниль рядом — распространение на соседние единицы."),
    ("security_grace_period", "Охрана — взаимодействие с LP", "METHOD",
     "Взаимодействие охраны и LP: детеншн только по политике и закону, наблюдение, radio code, не физическое противодействие без обучения.",
     "Незаконный детеншн — иск и увольнение."),
    ("signage_compliance_pricing", "Ценники — соответствие закону", "METHOD",
     "Цена на полке = цена на кассе (закон о защите прав потребителей). Штрих-код читается, единица измерения (кг/шт), акция — старая и новая цена.",
     "Расхождение цен — штраф и компенсация покупателю."),
    ("waste_compactor_safety", "Компактор отходов — безопасность", "PRACTICAL",
     "Компактор: обучение, ключ только у уполномоченных, не руки внутрь, блокировка LOTO при обслуживании, отходы без острых предметов в пакетах.",
     "Травма в компакторе — тяжёлый инцидент и остановка объекта."),
    ("central_warehouse_crossdock", "Кросс-докинг — распределение", "METHOD",
     "Кросс-док: товар с центрального склада не хранится в магазине, а сразу на полку в день поставки. Окно приёмки 2-4 часа, приоритет скоропорт.",
     "Задержка кросс-дока — out-of-stock в тот же день."),
    ("customer_complaint_escalation", "Жалоба клиента — эскалация", "METHOD",
     "Жалоба: выслушать, извиниться за неудобство без признания вины, решение в рамках политики (замена, voucher), запись в CRM, эскалация менеджеру при угрозе суда/СМИ.",
     "Спор с клиентом у кассы — эскалация и viral video."),
    ("inventory_shrink_pos_void", "Void и refund — контроль мошенничества", "METHOD",
     "Мониторинг: excessive voids, post-void, refund без товара, same-card refunds. Лимиты без менеджера, отчёт exception daily.",
     "Сотрудник post-void на свою карту — классическое мошенничество."),
    ("planogram_reset_audit", "Аудит планограммы — фото и score", "METHOD",
     "Еженедельный фото-аудит полок, score compliance %, обратная связь команде зала, приоритет top 50 SKU revenue.",
     "Планограмма только на бумаге — нет роста продаж."),
    ("store_kpi_dashboard", "Дашборд KPI магазина", "METHOD",
     "Ежедневный dashboard: sales vs LY, traffic, conversion, shrink MTD, labor %, OSA top SKUs. Утренний huddle 10 минут с командой.",
     "KPI без huddle — цифры не превращаются в действия."),
]

PHONEREPAIR = [
    ("charging_port_clean", "Разъём зарядки — очистка контактов", "METHOD",
     "Засорённый порт Lightning/USB-C: выключить телефон, зубочистка/пластиковый зуб, сжатый воздух, изопропиловый спирт 99% на ватной палочке. Не металлические иглы — короткое замыкание.",
     "Металл в порту — повреждение контактов и платы."),
    ("charging_port_replacement", "Замена разъёма зарядки", "METHOD",
     "Пайка разъёма: снять плата, flux, паяльник 350°C тонким жалом, демонтаж старого, очистка падов, установка OEM-разъёма, тест зарядки и данных.",
     "Дешёвый разъём — отвал через месяц и повторный ремонт."),
    ("diagnostic_board_level", "Диагностика — плата и питание", "METHOD",
     "Проверка: мультиметр на линии VBUS, батарея (напряжение, циклы), потребление в standby. Короткое на линии — искать микротрещину под микроскопом.",
     "Замена батареи при КЗ на плате — повторный отказ."),
    ("back_glass_removal", "Заднее стекло — снятие", "METHOD",
     "Снятие заднего стекла: нагрев 80°C, лазер для разрушения клея (для iPhone), пластиковые лопатки, не повредить беспроводную зарядку и flash flex.",
     "Скол у катушки NFC — беспроводная зарядка не работает."),
    ("face_id_calibration", "Face ID — калифровка после ремонта", "METHOD",
     "После замены экрана/камеры: перенос dot projector и IR с донорского модуля (микропайка) или программатор для привязки. Без калибровки Face ID отключён системой.",
     "Новый экран без переноса Face ID — функция потеряна навсегда."),
    ("touch_ic_repair", "Touch IC — восстановление сенсора", "METHOD",
     "Типичная болезнь iPhone 6/6 Plus: отвал Meson/>Cumulus IC. Reboll под микроскопом, jumpers при оторванных падах, тест multi-touch и 3D Touch.",
     "Пропуск reboll — touch отваливается снова через неделю."),
    ("audio_codec_speaker", "Динамик и аудиокодек — диагностика", "METHOD",
     "Нет звука: тест в настройках, замена динамика, проверка audio IC и линий. Замена нижнего шлейфа на моделях где динамик на flex.",
     "Замена динамика при мёртвом codec — звука нет."),
    ("camera_module_swap", "Модуль камеры — замена", "METHOD",
     "Замена камеры: OEM vs aftermarket (ошибка «неоригинальная деталь»). Программирование серийника на некоторых моделях. Проверка фокуса, вспышки, OIS.",
     "Aftermarket камера — пятна на фото и отказ Portrait mode."),
    ("sim_tray_repair", "Лоток SIM — ремонт", "METHOD",
     "Погнутый лоток — выпрямить или заменить. Застрявшая SIM — извлечь тонким инструментом, не ломать лоток. Проверить контакты SIM reader на плате.",
     "Сломанный лоток — SIM не фиксируется и теряется."),
    ("software_restore_dfu", "Программное восстановление — DFU", "METHOD",
     "DFU/Recovery: резервная копия если возможно, DFU mode, iTunes/Finder restore, настройка как нового или из backup. Проверка iCloud lock перед работой.",
     "Ремонт заблокированного iCloud — нельзя активировать для клиента."),
    ("icloud_lock_check", "Проверка iCloud lock — приём", "PRACTICAL",
     "При приёме: Settings → Apple ID, Find My выключен или учётные данные клиента. IMEI check на stolen status. Не принимать устройство с блокировкой.",
     "Ремонт краденого — уголовный риск и потеря деталей."),
    ("esd_workstation_setup", "ESD — антистатическая зона", "PRACTICAL",
     "ESD коврик, браслет на землю, ионизатор воздуха, хранение плат в антистатических пакетах. Работа без ESD — скрытые отказы через дни.",
     "Прикосновение к плате без браслета — ESD повреждение CPU."),
    ("data_backup_before_repair", "Резервная копия — до ремонта", "METHOD",
     "Перед разборкой: предложить backup (iCloud, local, Android Smart Switch). Подпись waiver если отказ. Документировать состояние экрана фото.",
     "Потеря данных без waiver — иск на мастерскую."),
    ("warranty_repair_rma", "Гарантийный ремонт — RMA", "METHOD",
     "RMA производителя: серийник, proof of purchase, ticket в портале, отправка, ожидание 5-15 дней. Временный loaner по политике сервиса.",
     "Ремонт вне RMA при гарантии — потеря гарантии клиента."),
    ("quote_transparency_parts", "Смета — прозрачность запчастей", "METHOD",
     "Смета: OEM/aftermarket/refurbished, срок, гарантия 30-90 дней. Озвучить риск aftermarket. Депозит 50% на дорогие платы.",
     "Сюрприз на выдаче — отказ платить и конфликт."),
    ("tablet_digitizer_bond", "Планшет — приклеивание дигитайзера", "METHOD",
     "OCA приклеивание: чистая комната, пылеудалитель, выравнивание, вакуумный ламинатор, дегазация пузырей. Не воздух в OCA — пятна под стеклом.",
     "Пузыри OCA — переделка и потеря стекла."),
    ("laptop_dc_jack", "Ноутбук — разъём питания DC jack", "METHOD",
     "DC jack: часто на шлейфе, замена шлейфа проще пайки. Пайка jack — закрепление на корпусе, strain relief. Тест wiggle при подключении.",
     "Слабая пайка — интермиттирующая зарядка и жалобы."),
    ("laptop_keyboard_liquid", "Ноутбук — залитие клавиатуры", "METHOD",
     "Залитие: отключить питание и батарею, перевернуть, промыть дистиллированной водой после сладких жидкостей, сушка 48 ч, замена клавиатуры если залипает.",
     "Включение мокрого — коррозия на плате за часы."),
    ("motherboard_reflow_risk", "Реболл BGA — риски", "METHOD",
     "BGA reflow — временное решение на старых GPU/чипах. Предупредить клиента о сроке 1-6 месяцев. Лучше замена платы или устройства.",
     "Обещание permanent fix после reflow — возврат и репутация."),
    ("parts_inventory_sku", "Склад запчастей — SKU и совместимость", "METHOD",
     "Учёт экранов по модели и ревизии (A1660 vs A1784). Cross-reference chart на стене. Минимум 2 экрана top 10 моделей в наличии.",
     "Неверная ревизия экрана — не подходит кнопка Home/Touch ID."),
    ("customer_device_waiver", "Акт приёма — повреждения и waiver", "PRACTICAL",
     "Акт: царапины, трещины, IMEI, пароль снят, Find My off, согласие на потерю данных, согласие на замену не-OEM.",
     "Без акта — спор «было целое» при выдаче."),
    ("ultrasonic_cleaning_board", "Ультразвуковая ванна — платы", "METHOD",
     "Ультразвук: спирт или специальный раствор, 3-5 мин, не долго — отвал мелких компонентов. Сушка 24 ч. После воды — обязательно.",
     "Ультразвук на слабом клее — отвал чипов."),
    ("frame_bent_straighten", "Погнутый корпус — риск экрана", "METHOD",
     "Погнутый frame: оценить, можно ли выправить. Новый экран на погнутом — трещина от напряжения. Рекомендовать замену housing.",
     "Экран на кривом frame — трещина через 2-3 дня."),
    ("wireless_charging_coil", "Катушка беспроводной зарядки", "METHOD",
     "Замена coil + NFC antenna на некоторых моделях в одном модуле. Выравнивание под стеклом. Тест Qi charger 5W/15W.",
     "Смещённая coil — нагрев и медленная зарядка."),
    ("fingerprint_sensor_swap", "Сканер отпечатка — перенос", "METHOD",
     "Android in-display FPS: привязка к плате, калибровка. iPhone Touch ID home button — привязан к плата, только перенос оригинала.",
     "Новая кнопка Touch ID без переноса — Touch ID мёртв."),
    ("test_matrix_post_repair", "Матрица тестов — после ремонта", "METHOD",
     "Post-repair: touch все углы, камеры, микрофоны, динамики, Wi-Fi, Bluetooth, GPS, сенсоры, заряд AC и wireless, кнопки громкости.",
     "Выдача без теста — возврат «не работает микрофон»."),
    ("pricing_labor_parts", "Ценообразование — работа и запчасти", "METHOD",
     "Цена = запчасть + labor (фикс или по времени) + markup 20-40%. Диагностика fee при отказе от ремонта. Прозрачность в SMS/email.",
     "Бесплатная диагностика без fee — злоупотребления."),
    ("rma_vendor_warranty", "RMA поставщику — брак запчасти", "METHOD",
     "Брак экрана из коробки: RMA vendor в 7 дней, фото дефекта, не выбрасывать до одобрения. Credit на следующий заказ.",
     "Выброс брака без RMA — потеря стоимости детали."),
    ("customer_communication_delay", "Коммуникация — задержка запчасти", "PRACTICAL",
     "Задержка: SMS/email в день задержки, новая ETA, опция отмены и возврат депозита. Не ghosting.",
     "Молчание 2 недели — негативный отзыв и chargeback."),
    ("tool_calibration_microscope", "Микроскоп — калибровка и освещение", "PRACTICAL",
     "Стереомикроскоп 10-40x, кольцевая LED, фиксация платы в держателе. Чистка линз ежемесячно.",
     "Плохой свет — пропуск микротрещин при пайке."),
    ("ipad_battery_adhesive", "iPad — снятие проклеенной батареи", "METHOD",
     "iPad battery: растворитель клея (небольшое количество), пластиковые карты, не гнуть батарею. Много адгезива на новой — прекаты.",
     "Прокол iPad battery — пожар в мастерской."),
    ("corrosion_ultrasound_protocol", "Коррозия — протокол после воды", "METHOD",
     "После воды: разборка, щётка + IPA, ультразвук, замена подозрительных компонентов (фильтры, контроллеры заряда), сушка, тест 48 ч soak.",
     "Только сушка без чистки — коррозия прогрессирует."),
    ("logic_board_schematic", "Схема платы — чтение для ремонта", "METHOD",
     "Использовать ZXW/PDF schematics: поиск линии питания, измерение на тест-поинтах, сравнение с donor board. Не угадывать компоненты.",
     "Замена случайного чипа — убитая плата."),
    ("shop_insurance_liability", "Страхование мастерской", "PRACTICAL",
     "Страхование: ущерб клиентскому устройству, пожар, ESD. Лимит покрытия выше стоимости top repair.",
     "Пожар от батареи без страховки — закрытие бизнеса."),
    ("recycling_e_waste", "Утилизация — e-waste", "METHOD",
     "Неисправимые устройства: wipe data, сертифицированный e-waste recycler, журнал утилизации. Батареи — отдельный контейнер.",
     "Выброс батарей в мусор — пожар на свалке и штраф."),
    ("loaner_phone_policy", "Подменный телефон — политика", "METHOD",
     "Loaner: депозит, договор, ограниченный функционал, wipe при возврате, проверка damage.",
     "Loaner без депозита — не возвращают."),
    ("board_swap_data_migration", "Замена платы — перенос данных", "METHOD",
     "Swap платы: перенос NAND/CPU невозможен без Apple factory. Данные только если старая плата жива — backup до swap.",
     "Обещание данных при мёртвой плате — невозможно без chip-off."),
    ("quality_oem_vs_aftermarket", "Качество экрана — OEM vs копия", "METHOD",
     "Объяснить клиенту: OEM (True Tone, яркость), aftermarket (дешевле, нет True Tone, возможен отказ сообщения). Запись выбора в акте.",
     "Aftermarket без согласия — спор о качестве."),
    ("repair_turnaround_sla", "SLA срока ремонта", "METHOD",
     "SLA: экран 1-2 ч, сложный board 3-5 дней, заказ запчасти 5-14 дней. Письменное подтверждение при приёме.",
     "Нереалистичный SLA — срыв ожиданий."),
    ("static_bag_shipping", "Отправка платы — антистатика", "METHOD",
     "Отправка в другой сервис: антистатический пакет, пена, IMEI на коробке, страховка отправления.",
     "Плата без ESD bag — отказ по пути."),
]

AIRDUCT = [
    ("blower_motor_clean", "Вентилятор — очистка колеса", "METHOD",
     "Очистка blower wheel: снятие панели furnace/AHU, вакуум + щётка, баланс после очистки. Грязное колесо снижает airflow на 30-50%.",
     "Неочищенный blower — перегрев heat exchanger."),
    ("coil_evaporator_clean", "Испаритель — очистка змеевика", "METHOD",
     "Evaporator coil: no-rinse coil cleaner, распыление, смыв при сильной грязи, не повредить fins. Ежегодно в humid climate.",
     "Забитый coil — лёд зимой и высокий счёт за электричество."),
    ("coil_condenser_outdoor", "Конденсатор наружный — мойка", "METHOD",
     "Outdoor condenser: выключить питание, мойка снизу вверх 1500 PSI мягким соплом, straighten bent fins comb.",
     "Мойка внутрь unit — погнуть fan blade."),
    ("register_sealing_boot", "Регистр — герметизация boot", "METHOD",
     "Утечка boot к register: mastic sealant, metal tape (не duct tape — сохнет), проверка airflow после.",
     "Duct tape на воздуховоде — отвал через год."),
    ("mold_remediation_duct", "Плесень в воздуховоде — ремедиация", "METHOD",
     "При видимой плесени: EPA-зарегистрированный biocide для HVAC, механическая очистка, устранение источника влаги. Пост-тест спор.",
     "Только дезодорант без удаления — плесень возвращается."),
    ("iaq_particulate_pm25", "Качество воздуха — PM2.5", "METHOD",
     "Измерение PM2.5 до/после чистки, цель снижение >50% при загрязнённых duct. Рекомендация MERV upgrade.",
     "Без измерения — нет доказательства пользы клиенту."),
    ("duct_insulation_repair", "Изоляция воздуховода — ремонт", "METHOD",
     "Повреждённая изоляция в unconditioned space: замена wrap, seal seams, R-value по климатической зоне.",
     "Потеря изоляции — конденсат и рост плесени."),
    ("flex_duct_replacement", "Гибкий воздуховод — замена", "METHOD",
     "Смятый flex duct: замена участка, правильный радиус изгиба, не сжатие >10%. Поддержка каждые 1.2 м.",
     "Сжатый flex — как закрытый клапан, нет airflow."),
    ("plenum_cleaning_access", "Пленум — доступ и очистка", "METHOD",
     "Plenum: снять access panel, HEPA vacuum, agitation, seal panel обратно с gasket.",
     "Пыль в plenum без negative air — выброс в дом."),
    ("dryer_vent_cleaning", "Сушилка — чистка вентканала", "METHOD",
     "Dryer vent: rotary brush от выхода наружу, удаление lint, проверка backdraft damper, max длина по code.",
     "Забитый dryer vent — пожар #1 причина бытовых пожаров США."),
    ("kitchen_grease_duct", "Кухонный жир — воздуховод ресторана", "METHOD",
     "Commercial kitchen hood duct: NFPA 96 schedule, steam/pressure wash, access doors каждые 3.6 m, сертификат чистки.",
     "Жир в duct — пожар вытяжки ресторана."),
    ("uvc_sanitizer_install", "UVC — установка обеззараживания", "METHOD",
     "UVC lamp в plenum: только при airflow (interlock), замена лампы 9000 ч, защита глаз при обслуживании.",
     "UVC без interlock — ожог сетчатки при открытии панели."),
    ("odor_source_elimination", "Запах — поиск источника", "METHOD",
     "Запах из vent: мёртвая грызунь, плесень, VOC от краски — не маскировать spray. Найти и удалить источник.",
     "Освежитель без чистки — запах возвращается."),
    ("zoning_damper_check", "Зонирование — проверка заслонок", "METHOD",
     "Motorized dampers: проверка открытия каждой зоны, калибровка thermostat, баланс static pressure.",
     "Закрытая damper — передавление и шум в других зонах."),
    ("static_pressure_test", "Статическое давление — измерение", "METHOD",
     "Manometer на supply/return: total external static pressure, сравнение с nameplate max. Выше max — undersized duct или dirty coil.",
     "Высокий static — сокращение срока службы blower motor."),
    ("customer_education_nadca", "Образование клиента — когда чистить", "METHOD",
     "Чистка нужна при видимой пыли, ремонте, плесени, аллергии, новом доме. Не каждые 3 года routine scam.",
     "Ненужная чистка — трата денег без IAQ выгоды."),
    ("before_after_photo_report", "Отчёт — фото до и после", "METHOD",
     "Фото interior duct до/после, video scope, включить в invoice. Маркетинг и доверие.",
     "Нет доказательств — клиент сомневается в необходимости."),
    ("hepa_filter_nam_maintenance", "HEPA на NAM — замена", "METHOD",
     "HEPA на negative air machine: проверка pressure drop, замена по manufacturer, не переполнять.",
     "Пробитый HEPA — пыль в комнату во время работы."),
    ("commercial_bid_duct_clean", "Коммерческая смета — воздуховоды", "METHOD",
     "Смета: $/linear foot по размеру duct, access difficulty, количество registers, night work premium.",
     "Фикс цена без осмотра — убыток на большом объекте."),
    ("asbestos_verification", "Асбест — проверка перед работами", "METHOD",
     "Здания до 1980: sample duct wrap на asbestos перед disturbance. Licensed abatement если positive.",
     "Пробив асбестового wrap — штраф и health hazard."),
    ("return_air_grille_clean", "Решётка return — очистка", "METHOD",
     "Снять grille, мыть, vacuum behind, проверить filter slot seal.",
     "Забитый return — шум и starved furnace."),
    ("supply_boot_insulation", "Supply boot — изоляция и seal", "METHOD",
     "Boot в unconditioned attic: изолировать boot, seal to drywall с mastic.",
     "Негерметичный boot — кондиционированный воздух в чердак."),
    ("robot_duct_cleaning", "Робот — чистка магистрали", "METHOD",
     "Crawler robot с щёткой и камерой для main trunk >30 cm. Operator контролирует video.",
     "Робот без negative air — пыль в branch lines."),
    ("fire_damper_inspection", "Противопожарная заслонка — инспекция", "METHOD",
     "Fire/smoke dampers в commercial: ежегодная проверка по code, документация для fire marshal.",
     "Заклинившая fire damper — не закроется при пожаре."),
    ("new_construction_debris", "Новостройка — строительный мусор в duct", "METHOD",
     "Post-construction: drywall dust, обрезки в duct — полная очистка до occupancy. Защита duct при стройке — лучшая практика.",
     "Пыль гипса в coil — блокировка и ремонт HVAC."),
    ("pet_hair_return_clog", "Шерсть животных — засор return", "METHOD",
     "Дома с питомцами: частая смена filter MERV 11, vacuum return grille weekly, чистка duct 3-5 лет.",
     "Шерсть на filter — bypass в coil как felt layer."),
    ("humidifier_pad_service", "Увлажнитель — смена падов", "METHOD",
     "Whole-house humidifier: смена evaporator pad сезонно, очистка tray от scale, проверка solenoid.",
     "Забитый pad — рост бактерий в water tray."),
    ("electrostatic_filter_wash", "Электростатический фильтр — мойка", "METHOD",
     "Washable electrostatic: только мыло и вода, полная сушка перед установкой, не повреждать grid.",
     "Влажный grid в furnace — короткое замыкание."),
    ("duct_size_verification", "Размер воздуховода — проверка", "METHOD",
     "Undersized duct: noise, low airflow at far registers. Расчёт Manual D при замене furnace.",
     "Большой furnace на малых duct — высокий static и поломки."),
    ("sanitizer_fogging_limit", "Туман дезинфекция — ограничения", "METHOD",
     "Fogging biocide: только после mechanical cleaning, evacuate home, follow label dwell, ventilate.",
     "Fog без удаления пыли — biocide на грязи бесполезен."),
    ("warranty_cleaning_service", "Гарантия на чистку", "PRACTICAL",
     "Гарантия 30-90 дней на workmanship, не на IAQ если источник пыли остаётся (carpet, pets).",
     "Гарантия «никогда не запылится» — невыполнимое обещание."),
    ("crew_safety_ppe", "СИЗ бригады — воздуховоды", "PRACTICAL",
     "PPE: respirator N95/P100, очки, перчатки, coveralls в contaminated duct.",
     "Без respirator — legionella и histoplasmosis риск."),
    ("access_door_installation", "Дверца доступа — установка", "METHOD",
     "Установка access doors в trunk для будущего обслуживания: по code каждые 7.6 m commercial.",
     "Без access — невозможна чистка середины trunk."),
    ("vinyl_duct_banned", "Виниловый воздуховод — не использовать", "PRACTICAL",
     "Plastic/vinyl flex не rated для high temp — заменить на UL-listed flex или metal.",
     "Винил плавится у furnace — токсичные газы."),
    ("balancing_report", "Балансировка — отчёт airflow", "METHOD",
     "После чистки: capture hood на каждый supply, CFM vs design, adjust dampers, записать в report.",
     "Без баланса — горячие/холодные комнаты остаются."),
    ("carbon_monoxide_combustion", "CO — проверка при furnace service", "METHOD",
     "При работе у furnace: CO monitor, проверка flue, heat exchanger crack (camera scope).",
     "Трещина heat exchanger — CO в supply air и отравление."),
    ("invoice_line_items", "Счёт — детализация услуг", "METHOD",
     "Invoice: количество registers, main line length, extras (sanitizer, access door), до/после фото ID.",
     "Одна строка «duct cleaning $999» — недоверие commercial клиента."),
    ("followup_filter_reminder", "Напоминание — смена фильтра", "METHOD",
     "После визита: email напоминание сменить filter через 30 дней, подписка на filter delivery.",
     "Клиент не меняет filter — быстрое повторное загрязнение."),
    ("negative_air_setup_steps", "Negative air — пошаговая установка", "METHOD",
     "1) Seal all registers except one. 2) Connect NAM to working register. 3) Agitate from far end. 4) Run NAM until visually clean.",
     "Два открытых register — negative pressure не держится."),
    ("commercial_kitchen_hood_link", "Связь с кухонной вытяжкой", "METHOD",
     "При чистке restaurant: coordinate hood cleaning same night, lockout tagout exhaust fan.",
     "Включённый fan во время чистки — травма и пыль по кухне."),
    ("residential_price_transparency", "Цена для частного дома — прозрачность", "METHOD",
     "Типичный дом: whole house $400-800 по количеству vents, не «$49 special» с доплатами на месте.",
     "Bait price — репутационный ущерб индустрии."),
]

BATCH_DATA = {
    "619_BATCH_477_RETAIL_STORE_OPERATIONS.ru.md": RETAIL,
    "763_BATCH_621_PHONE_REPAIR_MOBILE_OPS.ru.md": PHONEREPAIR,
    "791_BATCH_649_AIR_DUCT_CLEANING_OPS.ru.md": AIRDUCT,
}


def main() -> int:
    seen = existing_ids()
    total = 0
    for fname, facts in BATCH_DATA.items():
        total += append_facts(fname, facts, seen)
    print(f"\nДобавлено фактов: {total}")
    from core.world_skills_ingest import parse_knowledge_dir
    print(f"Парсер: {len(parse_knowledge_dir())} фактов")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
