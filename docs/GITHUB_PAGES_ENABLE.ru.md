# Включить GitHub Pages (один раз)

Сайт собирается в ветку **`gh-pages`**. Пока Pages не включён в настройках репозитория, ссылка показывает:

> There isn't a GitHub Pages site here.

## Шаги (2 минуты)

1. Откройте: **https://github.com/velantrian/Velantrim-ExoCortex-Titan/settings/pages**
2. **Build and deployment → Source:** выберите **Deploy from a branch**
3. **Branch:** `gh-pages` → папка **`/ (root)`** → **Save**
4. Подождите 1–3 минуты. Статус: зелёная галочка «Your site is live at…»

## Адреса после включения

| Назначение | URL |
|------------|-----|
| Портал | https://velantrian.github.io/Velantrim-ExoCortex-Titan/ |
| Research PWA (телефон/ПК, без сервера) | https://velantrian.github.io/Velantrim-ExoCortex-Titan/console/research-app.html |
| UI полной консоли (нужен API-сервер) | https://velantrian.github.io/Velantrim-ExoCortex-Titan/console/ |

## Полный сервер (LLM + SQLite)

GitHub Pages **не запускает Python**. Для чата и `/query`:

```powershell
.\scripts\start_console.ps1
```

Или на VPS/Docker: `docker-compose up -d` → порт **8000**.

Статическая консоль на GitHub может подключаться к вашему серверу по URL (ПК или VPS).
