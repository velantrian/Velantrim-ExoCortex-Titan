# 📦 Production Database — GitHub Release

**Статус:** SQLite/Ladybug-артефакты не хранятся в git (`.gitignore`).  
Полный production bundle должен публиковаться отдельно как GitHub Release asset.

> Важно: наличие инструкции в репозитории не означает, что Release уже опубликован.
> Перед установкой проверьте страницу Releases и SHA-256 sidecar конкретного архива.

## Контракт архива

| Файл | Назначение |
|---|---|
| `data/velantrim_kb_clean_20260710_graph.db` | SQLite KB graph |
| `data/exocortex_graph.db` | L3 topology (SQLite sidecar) |
| `data/exocortex.lbug` | L3 Ladybug graph |
| `data/ngram_house.db` | NGram/FTS pre-filter |
| `kb_graph.json` | Portable JSON export |
| `MANIFEST.json` | Версия контракта, размеры и SHA-256 каждого asset |
| `README.txt` | Runtime paths и команда проверки |

Архив публикуется вместе с внешним файлом `<archive>.sha256`. Внешний checksum
проверяет сам ZIP; `MANIFEST.json` проверяет содержимое после распаковки.

## Собрать bundle локально

```powershell
powershell -File scripts/package_production_release.ps1
```

С другим каталогом вывода:

```powershell
powershell -File scripts/package_production_release.ps1 -OutDir dist
```

Скрипт выполняет fail-closed preflight:

1. требует все обязательные production assets;
2. формирует `MANIFEST.json` schema v1;
3. запускает `scripts/verify_release_bundle.py` до сжатия;
4. создаёт `dist/velantrim_production_db_YYYYMMDD.zip`;
5. создаёт внешний `dist/velantrim_production_db_YYYYMMDD.zip.sha256`.

## Проверить после скачивания

Сначала проверьте внешний checksum архива.

Linux/macOS:

```bash
sha256sum -c velantrim_production_db_YYYYMMDD.zip.sha256
```

PowerShell:

```powershell
Get-FileHash .\velantrim_production_db_YYYYMMDD.zip -Algorithm SHA256
Get-Content .\velantrim_production_db_YYYYMMDD.zip.sha256
```

После распаковки проверьте все внутренние файлы:

```bash
python scripts/verify_release_bundle.py /path/to/extracted/bundle
```

Успешная проверка должна завершиться кодом `0`. Любой отсутствующий файл,
изменение размера, несовпадение SHA-256, дубликат или небезопасный путь в
manifest завершает проверку кодом `1`.

## Установка

1. Проверить внешний SHA-256 ZIP.
2. Распаковать bundle во временный каталог.
3. Выполнить `python scripts/verify_release_bundle.py <каталог>`.
4. Только после успешной проверки скопировать `data/`, `kb_graph.json`,
   `MANIFEST.json` и `README.txt` в корень репозитория.
5. Настроить `.env` на paths из `README.txt`.
6. Запустить сервер:

```bash
python -m uvicorn server:app --host 127.0.0.1 --port 8000
```

## Что реально можно восстановить из исходников

Штатный source rebuild создаёт SQLite KB и portable JSON:

```bash
python scripts/build_kb_graph.py \
  --db data/velantrim_kb_clean_20260710_graph.db \
  --wipe-all-edges \
  --export kb_graph.json
```

Эта команда **не** создаёт автоматически:

- `data/exocortex_graph.db`;
- `data/exocortex.lbug`;
- `data/ngram_house.db`.

Для этих sidecar-артефактов в текущем репозитории нет единого воспроизводимого
sync-командного пути. Поэтому документация больше не ссылается на отсутствующий
`scripts/sync_l3_ladybug.py` и не передаёт неподдерживаемые параметры
`--db/--sync-l3` в `scripts/export_kb_graph.py`.

## Удалённые из git артефакты

Из рабочего дерева удалены промежуточные `velantrim_kb_v2…v11.db`,
`velantrim_kb_full.db` и demo-заглушки L3/NGram. Старые blob могут оставаться в
истории Git до отдельной подтверждённой history-rewrite операции.
