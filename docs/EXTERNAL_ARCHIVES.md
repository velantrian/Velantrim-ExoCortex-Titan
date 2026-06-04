# External Archives Policy

Этот файл фиксирует внешние архивные копии и правила их использования.

## 1) `VELANTRIM_v8_5_1_WITH_PHILOSOPHY`

Путь:
- `C:\Users\VELAN\Documents\velantrim\VELANTRIM_v8_5_1_WITH_PHILOSOPHY`

Назначение:
- Архивный снимок v8.5.1 (reference/backup), не рабочая основа.

Краткий итог сравнения с `VELANTRIM_v8_5_1_KB_v3`:
- Уникально в архиве: `0` файлов.
- В `KB_v3` есть дополнительные слои/документы и более новые изменения.
- Отличаются ключевые файлы: `core/pipeline.py`, `core/memory.py`, `server.py`, `tests/test_pipeline.py`, `Velantrim_Project_Map.md`, `WORK_LOG.md`.

Правило:
1. Архив использовать только для точечного diff/восстановления.
2. Не делать массовый merge архивной папки в `KB_v3`.
3. Перед переносом любого файла из архива — обоснование и проверка регрессий.

