# 🧭 Профили Velantrim — выбери «режим сервера»

Velantrim можно запускать **по-разному**: для дома, для компании, для науки.  
Не нужно помнить десятки флагов `ENABLE_*` — выбери **профиль**.

---

## 🚦 Три способа выбрать профиль

| Способ | Когда | Пример |
|--------|-------|--------|
| **1. При старте сервера** | Один режим на весь сервер | `VELANTRIM_PROFILE=personal` |
| **2. В каждом запросе** | Разные клиенты — один сервер | `"profile": "citizen"` в `POST /query` |
| **3. Справочник API** | Посмотреть ориентиры | `GET /profiles` |

---

## 🗺️ Витрина профилей

| Профиль | Кому | Сложность | Одной фразой |
|---------|------|-----------|--------------|
| 🏠 **citizen** | Обычные люди | ⭐ | Спросил — ответили просто |
| 🧑 **personal** | Личный бот | ⭐ | Цели, заметки, «помни меня» |
| 🏢 **company** | Компания | ⭐⭐ | Факты + аудит + лимиты |
| 🔬 **science** | Наука, R&D | ⭐⭐ | Источники, связи, домен science |
| 🎒 **education** | Учёба, курсы | ⭐ | Конспекты, цели, объяснения |
| 🧪 **research** | Продвинутые исследования | ⭐⭐⭐ | Cross-domain, cognitive runtime |
| ⚙️ **developer** | Разработчик Velantrim | ⭐⭐⭐ | Весь ExoCortex (dev) |

---

## 🖥️ Веб-консоль (удобнее сырого API)

После запуска сервера откройте в браузере:

**http://127.0.0.1:8755/console/**

Там: переключатель профилей, чат, сохранение фактов, статус LLM.

## 🤖 Подключение LLM

1. Скопируйте `config/llm.example.env` → допишите в `.env`
2. Задайте `LLM_PROVIDER=anthropic` и `ANTHROPIC_API_KEY=...` (или OpenAI)
3. Перезапустите сервер
4. Проверьте: `GET /setup/llm` или индикатор в `/console`

## 🚀 Быстрый старт (PowerShell)

```powershell
# Личный бот + консоль
.\scripts\start_profile.ps1 -Profile personal

# В браузере: http://127.0.0.1:8755/console/
# API ключ — из VELANTRIM_API_KEY в .env
```

---

## 📁 Файлы конфигурации

| Профиль | Файл |
|---------|------|
| citizen | `config/profiles/citizen.env` |
| personal | `config/profiles/personal.env` |
| company | `config/profiles/company.env` |
| science | `config/profiles/science.env` |
| research | `config/profiles/research.env` |
| developer | `config/exocortex-dev.env` |

Скопируй нужный файл в `.env` или используй `start_profile.ps1`.

---

## 🧩 Что меняет профиль

1. **При старте** — включает нужные слои (`ENABLE_*` в `.env`).
2. **В `/query`** — подставляет `mode`, `response_lens`, `domain`, `top_k`, `use_llm`.
3. **В ответе** — блок `profile_landmark` с шагами-ориентирами.

Явные поля в запросе (если отличаются от заводских) **перебивают** профиль.

---

## ❓ Какой профиль выбрать

- **Дом, семья, хобби** → `citizen` или `personal`
- **Стартап / отдел / support** → `company`
- **Лаборатория, статьи, гипотезы** → `science`
- **Эксперименты с графом и агентами** → `research`
- **Отладка всего репозитория** → `developer`

---

См. также: [AUDIT_V8_6.ru.md](AUDIT_V8_6.ru.md) · [README.md](../README.md)
