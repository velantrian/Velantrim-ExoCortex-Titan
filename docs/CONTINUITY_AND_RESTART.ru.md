# 🔄 Titan V1 — Continuity / State / Restart

Этот документ описывает только пользовательскую непрерывность Titan V1. Он не добавляет новый runtime, authority, backup service или background recovery subsystem.

## Что должно переживать обычный перезапуск

### 🧠 Основная память

По умолчанию Titan хранит основную локальную память в SQLite:

```text
./data/velantrim.db
```

Путь можно переопределить через `VELANTRIM_DB_PATH`.

Остановка процесса Titan и повторный запуск из той же папки не должны удалять эту базу. Новый runtime instance открывает тот же файл.

### 📝 Заметки Console

Пользовательские заметки хранятся отдельно от epistemic facts:

```text
./data/velantrim_notes.db
```

Это специально отдельный SQLite store: заметка не становится фактом или Canon только потому, что пользователь её сохранил.

### ⚙️ Конфигурация

`bootstrap_titan.py` создаёт `.env` только когда его нет. Повторный запуск сохраняет существующий `.env`, включая серверный ключ, выбранного provider, model и explicit remote-data/network settings.

### 💬 История чатов в браузере

Console chat archive хранится в browser `localStorage` с префиксом:

```text
velantrim_titan_console_*
```

Поэтому перезапуск Python-процесса не должен стирать историю браузера. Однако browser storage — не серверная база Titan и не Canon. Очистка данных сайта, смена browser profile/origin или другой компьютер могут удалить/не перенести эту историю.

## Обычный restart

1. Остановите Titan (`Ctrl+C` в терминале).
2. Не удаляйте `.env` и каталог `data/`.
3. Снова запустите:

```bash
python scripts/bootstrap_titan.py
```

4. Откройте тот же Console URL.
5. Проверяйте отдельно:
   - facts / ingested data — через обычный chat/search path;
   - notes — в Notes UI;
   - browser chat archive — в том же browser profile/origin.

## Что НЕ обещает Stage 6

Stage 6 не является:

- backup/restore системой;
- cloud sync;
- replication;
- crash-consistency redesign;
- migration/update lifecycle;
- disaster recovery;
- production authorization.

Эти вопросы относятся к последующим predefined stages, если они создают реальный P0/P1 для Titan V1.
