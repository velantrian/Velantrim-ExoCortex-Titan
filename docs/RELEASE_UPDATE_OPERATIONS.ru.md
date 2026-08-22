# 📦 Titan V1 — Release / Update / Operations

Этот документ фиксирует bounded lifecycle для текущего Titan V1. Он не объявляет production authorization и не создаёт новый канал runtime authority.

## 🧭 Текущий канал поставки V1

Для текущего V1 authoritative source distribution — GitHub checkout репозитория `velantrian/Velantrim-ExoCortex-Titan`.

`pyproject.toml` содержит package identity/version, а CI отдельно проверяет воспроизводимую сборку wheel. Наличие wheel evidence не означает, что PyPI или иной публичный package registry является авторизованным production-каналом.

## 🔎 Проверить обновление

Из чистой ветки `main`:

```bash
python scripts/update_titan.py
```

Команда:

- проверяет, что это Git checkout Titan;
- требует ветку `main`;
- отказывается работать при локальных изменениях;
- делает `git fetch --prune origin main`;
- сравнивает точный текущий SHA с `origin/main`;
- проверяет, что обновление является только fast-forward;
- без `--apply` ничего не изменяет.

## ⬆️ Применить обновление

```bash
python scripts/update_titan.py --apply
```

Updater выполняет только:

```text
git merge --ff-only origin/main
```

Force/reset/rebase автоматически не используются.

Если существующая `.venv` найдена, updater повторно устанавливает bounded runtime extras:

```text
[server,parsers]
```

Это необходимо, потому что простая проверка importability не доказывает, что после обновления установлены новые/изменённые dependency constraints.

Если `.venv` отсутствует, updater не создаёт скрытый второй bootstrap path, а предлагает обычную canonical команду:

```bash
python scripts/bootstrap_titan.py
```

## 🔐 Локальные данные

`.env` исключён из Git tracking. SQLite runtime state (`*.db`, WAL/SHM/journal и соответствующие data-пути) также исключён `.gitignore`.

Updater сам не открывает, не мигрирует и не удаляет `.env` или пользовательские SQLite-файлы. Git fast-forward изменяет только tracked repository content.

Перед важными обновлениями пользователь всё равно может сделать собственную резервную копию локального состояния. Stage 8 не превращает Titan в отдельную backup/disaster-recovery систему.

## 🧯 Отказ обновления

Updater fail-closed в следующих случаях:

- нет Git;
- каталог не является Git checkout;
- неполный checkout;
- активна не `main`;
- есть локальные изменения;
- локальная история и `origin/main` разошлись;
- fetch/merge завершился ошибкой.

В этих случаях автоматический force-update запрещён.

Если code fast-forward уже применён, но dependency refresh не прошёл, updater сообщает об этом явно. После восстановления доступа к package index достаточно повторно выполнить updater либо canonical bootstrap.

## ↩️ Точный rollback reference

Перед применением updater печатает текущий commit SHA и после обновления повторяет его как rollback reference.

Это evidence/reference, а не автоматическая команда destructive rollback. Stage 8 намеренно не выполняет `git reset --hard` автоматически.

## 🏗️ Packaging evidence

Titan V1 имеет:

- package metadata в `pyproject.toml`;
- Python >= 3.11 contract;
- bounded `server` и `parsers` extras;
- reproducible wheel CI gate;
- deterministic SBOM CI gate;
- dependency vulnerability audit;
- Docker build/test workflow.

Эти поверхности доказывают build/operations engineering quality, но сами по себе не дают production authorization.

## 🧩 Release discipline

Перед V1 closure конкретный release candidate должен быть привязан к точному Git SHA и пройти существующие exact-head CI/CodeQL/aggregate gates. Stage 9 проверяет ordinary-user E2E, Stage 10 — bounded pilot, Stage 11 — final V1 closure decision.

Поэтому Stage 8 закрывает lifecycle доставки/обновления, но **не создаёт преждевременный Final Release/production GO**.

## ✅ Stage 8 exit contract

Stage 8 считается закрытым только если:

- безопасная check-only update команда существует;
- apply path разрешает только clean-main fast-forward;
- локальная изменённая/divergent история fail-closed;
- runtime dependencies обновляются или пользователь явно направляется в canonical bootstrap;
- local `.env`/SQLite state не становятся update payload;
- packaging evidence остаётся зелёным;
- P1-04 закрыт;
- P0=0 и других V1 P1 не осталось;
- CI/CodeQL/aggregate exact-head зелёные.
