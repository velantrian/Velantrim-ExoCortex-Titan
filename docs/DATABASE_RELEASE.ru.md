# 📦 Production Database — GitHub Release

**Статус:** SQLite/Ladybug артефакты **не хранятся в git** (`.gitignore`).  
Полная production-БД публикуется как **GitHub Release asset**.

## Что внутри zip

| Файл | Назначение |
|---|---|
| `data/velantrim_kb_clean_20260710_graph.db` | KB graph (32 302 facts, bilingual metadata) |
| `data/exocortex_graph.db` | L3 topology (SQLite sidecar) |
| `data/exocortex.lbug` | L3 Ladybug (Etir / MHI graph_coverage) |
| `data/ngram_house.db` | FTS5 trigram pre-filter |
| `kb_graph.json` | Portable JSON export |
| `MANIFEST.json` | SHA256 для проверки целостности |

## Собрать zip локально

```powershell
powershell -File scripts/package_production_release.ps1
```

Архив: `dist/velantrim_production_db_YYYYMMDD.zip` (~500 MB).

## Установка после скачивания Release

1. Распаковать в корень репозитория (перезаписать `data/` и `kb_graph.json`).
2. Проверить хэши из `MANIFEST.json`.
3. Убедиться, что `.env` указывает на production paths (см. `.env.example`).
4. Запустить сервер: `python -m uvicorn server:app --host 127.0.0.1 --port 8000`.

## Восстановление без zip (из исходников)

```bash
python scripts/build_kb_graph.py --db data/velantrim_kb_clean_20260710_graph.db
python scripts/export_kb_graph.py --db data/velantrim_kb_clean_20260710_graph.db --sync-l3 data/exocortex_graph.db --out kb_graph.json
python scripts/sync_l3_ladybug.py
```

## Удалённые из git (устаревшие)

С репозитория сняты промежуточные `velantrim_kb_v2…v11.db`, `velantrim_kb_full.db`, демо-заглушки L3/NGram.  
История git может содержать старые blob — для slim clone используйте свежий Release.
