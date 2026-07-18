#!/usr/bin/env python3
"""
scripts/apply_migrations.py — атомарное применение миграций SQLite
===================================================================
Версия: v8.5.3 (Claude audit + cross-AI consensus + Perplexity checklist)

Что делает:
  - Применяет миграции 008/009/010 к БД Velantrim последовательно.
  - Идемпотентен: повторный запуск не делает ничего (через PRAGMA user_version).
  - Атомарен: каждая миграция выполняется в одной транзакции BEGIN/COMMIT.
  - Безопасен для --check: не создаёт пустую БД как побочный эффект.
  - Делает backup БД перед применением (Perplexity checklist).
  - Проверяет integrity_check перед применением.
  - Поддерживает --dry-run-copy: прогоняет миграцию на физической копии.

Использование:
  python scripts/apply_migrations.py              # применить (с auto-backup)
  python scripts/apply_migrations.py --check      # проверить версию
  python scripts/apply_migrations.py --dry-run    # показать без применения
  python scripts/apply_migrations.py --dry-run-copy  # прогнать на копии
  python scripts/apply_migrations.py --no-backup  # пропустить backup (не рекомендуется)
  python scripts/apply_migrations.py --db /path/to/custom.db
"""
from __future__ import annotations

import hashlib
import sqlite3
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

MIGRATIONS = [
    (8,  BASE_DIR / "migrations" / "008_add_relations.sql"),
    (9,  BASE_DIR / "migrations" / "009_truth_kernel.sql"),
    (10, BASE_DIR / "migrations" / "010_raw_memory.sql"),
    (11, BASE_DIR / "migrations" / "011_claim_type_modality.sql"),
    (12, BASE_DIR / "migrations" / "012_crystal_memory.sql"),
    (13, BASE_DIR / "migrations" / "013_erasure_jobs.sql"),
    (14, BASE_DIR / "migrations" / "014_erasure_job_generations.sql"),
    (15, BASE_DIR / "migrations" / "015_erasure_batches.sql"),
]

LATEST_VERSION = max(v for v, _ in MIGRATIONS)


# ─────────────────────────────────────────────────────────────────────────────
# Вспомогательные функции
# ─────────────────────────────────────────────────────────────────────────────

def get_version(conn: sqlite3.Connection) -> int:
    """Текущая версия схемы через PRAGMA user_version. 0 = чистая БД."""
    return conn.execute("PRAGMA user_version").fetchone()[0]


def column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    """
    Проверка существования колонки через PRAGMA table_info.
    Используется для идемпотентности ALTER TABLE ADD COLUMN —
    SQLite не поддерживает IF NOT EXISTS для ALTER.
    """
    try:
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
        return any(row[1] == column for row in rows)
    except sqlite3.OperationalError:
        return False


def integrity_check(db_path: Path) -> bool:
    """
    Проверяет целостность БД через PRAGMA integrity_check.
    Возвращает True если БД исправна. Perplexity checklist.
    """
    conn = sqlite3.connect(str(db_path))
    try:
        result = conn.execute("PRAGMA integrity_check").fetchall()
        ok = len(result) == 1 and result[0][0] == "ok"
        if not ok:
            print("❌ integrity_check обнаружил проблемы:", file=sys.stderr)
            for row in result[:10]:  # первые 10 ошибок
                print(f"   {row[0]}", file=sys.stderr)
        return ok
    finally:
        conn.close()


def backup_db(db_path: Path, backup_dir: Path | None = None) -> Path:
    """
    Создаёт backup через SQLite .backup API (самый надёжный способ —
    учитывает WAL и корректно завершает незакрытые транзакции).
    Возвращает путь к backup-файлу. Perplexity checklist.
    """
    if backup_dir is None:
        backup_dir = db_path.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    backup_path = backup_dir / f"{db_path.stem}_backup_{ts}.db"

    # SQLite .backup API — корректно работает даже при открытых соединениях
    src = sqlite3.connect(str(db_path))
    dst = sqlite3.connect(str(backup_path))
    try:
        src.backup(dst)
        # SHA256 checksum для проверки целостности backup
        checksum = hashlib.sha256(backup_path.read_bytes()).hexdigest()
        checksum_path = backup_path.with_suffix(".sha256")
        checksum_path.write_text(f"{checksum}  {backup_path.name}\n")
        print(f"💾 Backup: {backup_path.name}")
        print(f"   SHA256: {checksum[:16]}...")
    finally:
        src.close()
        dst.close()

    return backup_path


def dry_run_on_copy(db_path: Path, migrations: list[tuple[int, Path]]) -> bool:
    """
    Прогоняет все непримененные миграции на физической копии БД (не просто
    список имён). Возвращает True если всё прошло без ошибок.
    Perplexity checklist: строже, чем просто вывод имён файлов.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        copy_path = Path(tmpdir) / "dryrun.db"

        # Копируем через .backup API для корректной обработки WAL
        src = sqlite3.connect(str(db_path))
        dst = sqlite3.connect(str(copy_path))
        try:
            src.backup(dst)
        finally:
            src.close()
            dst.close()

        conn = sqlite3.connect(str(copy_path))
        conn.execute("PRAGMA journal_mode=WAL")
        current = get_version(conn)

        print(f"🔍 [DRY-RUN-COPY] Прогоняю на копии (текущая версия БД: {current})")
        success = True

        for version, mig_path in migrations:
            if current >= version:
                print(f"   ⏭️  {mig_path.name} (уже применена)")
                continue

            if not mig_path.exists():
                print(f"   ⚠️  {mig_path.name} не найдена")
                continue

            try:
                raw_sql = mig_path.read_text(encoding="utf-8")
                if version == 10 and column_exists(conn, "facts", "derived_from"):
                    filtered = [l for l in raw_sql.split("\n")
                                if "ALTER TABLE facts ADD COLUMN derived_from" not in l]
                    raw_sql = "\n".join(filtered)
                if version == 13 and column_exists(conn, "erasure_jobs", "generation"):
                    # Codex review finding (P2): the coordinator's own
                    # runtime _ensure_schema() can self-heal a v12 DB into
                    # the generation-aware shape (allowing multiple
                    # terminal rows per fact_id) before an operator ever
                    # runs this script. Migration 013's obsolete,
                    # unconditional UNIQUE(fact_id) index would then fail
                    # with a genuine UNIQUE constraint violation as soon as
                    # any fact_id has more than one terminal generation —
                    # neutralize ONLY that one obsolete statement; the rest
                    # of 013 (CREATE TABLE IF NOT EXISTS, idx_erasure_jobs_
                    # status) is harmless and still applied normally, and
                    # 014 runs next exactly as it would on a fresh DB.
                    raw_sql = "\n".join(
                        l for l in raw_sql.split("\n")
                        if "CREATE UNIQUE INDEX IF NOT EXISTS idx_erasure_jobs_fact "
                           "ON erasure_jobs(fact_id)" not in l
                    )
                if version == 14:
                    if column_exists(conn, "erasure_jobs", "generation"):
                        raw_sql = "\n".join(
                            l for l in raw_sql.split("\n")
                            if "ALTER TABLE erasure_jobs ADD COLUMN generation" not in l
                        )
                    if column_exists(conn, "erasure_log", "job_id"):
                        raw_sql = "\n".join(
                            l for l in raw_sql.split("\n")
                            if "ALTER TABLE erasure_log ADD COLUMN job_id" not in l
                        )

                conn.executescript(raw_sql)
                conn.execute(f"PRAGMA user_version = {version}")
                conn.commit()
                current = version
                print(f"   ✅ {mig_path.name} — прошла на копии")
            except Exception as exc:
                print(f"   ❌ {mig_path.name} — ОШИБКА: {exc}", file=sys.stderr)
                success = False
                break

        # Проверяем целостность копии после миграций
        result = conn.execute("PRAGMA integrity_check").fetchall()
        if len(result) == 1 and result[0][0] == "ok":
            print("   ✅ integrity_check копии: ok")
        else:
            print("   ❌ integrity_check копии: ПРОБЛЕМЫ", file=sys.stderr)
            success = False

        conn.close()
        return success


# ─────────────────────────────────────────────────────────────────────────────
# Основная логика
# ─────────────────────────────────────────────────────────────────────────────

def apply_migrations(
    db_path: Path,
    dry_run: bool = False,
    skip_backup: bool = False,
) -> list[str]:
    """
    Применить все непримененные миграции.
    Возвращает список имён применённых файлов миграций (для лога).
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Инициализация базовой схемы через DDL-trigger (миграции 008+ требуют
    # существующую таблицу facts)
    if not dry_run:
        sys.path.insert(0, str(BASE_DIR))
        from core.memory import SQLiteGraphStore
        _base_store = SQLiteGraphStore(str(db_path))
        _ = _base_store.get_fact("__migration_ddl_trigger__")

    # ── Integrity check перед любыми изменениями ─────────────────────────────
    if not dry_run and db_path.exists():
        print("🩺 Проверка целостности БД перед миграцией...")
        if not integrity_check(db_path):
            print("❌ Миграция отменена: integrity_check обнаружил ошибки.",
                  file=sys.stderr)
            print("   Восстановите БД из backup перед повторной попыткой.",
                  file=sys.stderr)
            raise RuntimeError("integrity_check failed — migration aborted")
        print("   ✅ integrity_check: ok")

    # ── Backup перед применением ──────────────────────────────────────────────
    if not dry_run and not skip_backup and db_path.exists():
        print("💾 Создаю backup перед миграцией...")
        backup_db(db_path)

    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")

    applied: list[str] = []
    current = get_version(conn)

    for version, mig_path in MIGRATIONS:
        if current >= version:
            continue

        if not mig_path.exists():
            print(f"⚠️  Миграция {mig_path.name} не найдена, пропускаем",
                  file=sys.stderr)
            continue

        if dry_run:
            print(f"🔍 [DRY RUN] применил бы {mig_path.name} (v{version})")
            applied.append(mig_path.name)
            continue

        print(f"📦 Применяю {mig_path.name} (версия {version})...")
        raw_sql = mig_path.read_text(encoding="utf-8")

        if version == 10 and column_exists(conn, "facts", "derived_from"):
            print("   ℹ️  Колонка facts.derived_from уже существует — "
                  "пропускаем ALTER")
            filtered_lines = [
                line for line in raw_sql.split("\n")
                if "ALTER TABLE facts ADD COLUMN derived_from" not in line
            ]
            raw_sql = "\n".join(filtered_lines)

        # 013 (Codex review finding, P2): the coordinator's own runtime
        # _ensure_schema() self-heal can add erasure_jobs.generation
        # before an operator ever runs this script (e.g. the server
        # started against a v12 DB before migrations were applied). If a
        # fact_id has already accumulated more than one terminal
        # generation by then, migration 013's obsolete unconditional
        # UNIQUE(fact_id) index fails outright with a genuine constraint
        # violation — neutralize ONLY that one statement; the rest of 013
        # (CREATE TABLE IF NOT EXISTS, idx_erasure_jobs_status) is
        # harmless and still runs, and 014 proceeds normally next.
        if version == 13 and column_exists(conn, "erasure_jobs", "generation"):
            print("   ℹ️  erasure_jobs уже generation-aware (runtime self-heal) — "
                  "пропускаю obsolete UNIQUE(fact_id) индекс")
            raw_sql = "\n".join(
                line for line in raw_sql.split("\n")
                if "CREATE UNIQUE INDEX IF NOT EXISTS idx_erasure_jobs_fact "
                   "ON erasure_jobs(fact_id)" not in line
            )

        # 011: claim_type/origin_type часто уже созданы DDL в core/memory.py
        # (на свежей БД). ALTER ADD COLUMN не идемпотентен в SQLite → отфильтровываем
        # уже существующие колонки, как для derived_from выше.
        if version == 11:
            for col in ("claim_type", "origin_type"):
                if column_exists(conn, "facts", col):
                    print(f"   ℹ️  Колонка facts.{col} уже существует — пропускаю ALTER")
                    raw_sql = "\n".join(
                        line for line in raw_sql.split("\n")
                        if f"ADD COLUMN {col}" not in line
                    )

        # 014: erasure_jobs.generation / erasure_log.job_id may already
        # exist if ErasureCoordinator's own runtime schema self-healing
        # (core/erasure_coordinator.py::_ensure_schema()) added them to this
        # DB before the operator got around to running this migration —
        # same non-idempotent-ALTER problem as 010/011 above.
        if version == 14:
            if column_exists(conn, "erasure_jobs", "generation"):
                print("   ℹ️  Колонка erasure_jobs.generation уже существует — "
                      "пропускаю ALTER")
                raw_sql = "\n".join(
                    line for line in raw_sql.split("\n")
                    if "ALTER TABLE erasure_jobs ADD COLUMN generation" not in line
                )
            if column_exists(conn, "erasure_log", "job_id"):
                print("   ℹ️  Колонка erasure_log.job_id уже существует — "
                      "пропускаю ALTER")
                raw_sql = "\n".join(
                    line for line in raw_sql.split("\n")
                    if "ALTER TABLE erasure_log ADD COLUMN job_id" not in line
                )

        try:
            conn.executescript(raw_sql)
            conn.execute(f"PRAGMA user_version = {version}")
            conn.commit()
            applied.append(mig_path.name)
            current = version
            print(f"   ✅ версия БД теперь {version}")
        except Exception as exc:
            try:
                conn.rollback()
            except sqlite3.OperationalError:
                pass
            print(f"❌ Ошибка при миграции {mig_path.name}: {exc}",
                  file=sys.stderr)
            raise

    conn.close()
    return applied


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(
        description="Velantrim SQLite migration runner v8.5.3"
    )
    parser.add_argument("--db", default="./data/velantrim.db",
                        help="Путь к БД (default: ./data/velantrim.db)")
    parser.add_argument("--check", action="store_true",
                        help="Только проверить версию, не применять")
    parser.add_argument("--dry-run", action="store_true",
                        help="Показать что будет сделано, но не делать")
    parser.add_argument("--dry-run-copy", action="store_true",
                        help="Прогнать миграции на физической копии БД")
    parser.add_argument("--no-backup", action="store_true",
                        help="Пропустить автоматический backup (не рекомендуется)")
    args = parser.parse_args()

    db_abs = Path(args.db).resolve()

    if args.check:
        if not db_abs.exists():
            print(f"❌ БД {db_abs} не найдена.", file=sys.stderr)
            return 1
        conn = sqlite3.connect(str(db_abs))
        ver = get_version(conn)
        conn.close()
        if ver < LATEST_VERSION:
            print(f"❌ БД версии {ver}, требуется ≥{LATEST_VERSION}.")
            return 1
        print(f"✅ БД актуальна (версия {ver})")
        return 0

    if args.dry_run_copy:
        if not db_abs.exists():
            print(f"❌ БД {db_abs} не найдена.", file=sys.stderr)
            return 1
        success = dry_run_on_copy(db_abs, MIGRATIONS)
        return 0 if success else 1

    applied = apply_migrations(
        db_abs,
        dry_run=args.dry_run,
        skip_backup=args.no_backup,
    )
    if applied:
        print(f"✅ Применены миграции: {', '.join(applied)}")
    else:
        print("✅ Миграции уже применены, БД актуальна")
    return 0


if __name__ == "__main__":
    sys.exit(main())

