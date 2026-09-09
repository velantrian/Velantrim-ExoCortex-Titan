#!/usr/bin/env python3
"""Холодный tar-бэкап каталога данных hardened production-профиля.

Это не новый recovery-фреймворк. Скрипт воспроизводит задокументированную
процедуру из docs/operations/hardened-production-profile.md §9:

    tar czf ARCHIVE -C <data-dir> .

и явное восстановление ТОЛЬКО в новый пустой каталог/том:

    tar xzf ARCHIVE -C <fresh-empty-dir>

Docker-обёртки вызывают тот же busybox tar по именованному тому.
Демон Docker не требуется для файлового пути (его покрывает pytest).

Не обещает RTO/RPO, live/hot backup, DR-оркестрацию или production authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sqlite3
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
from typing import Any, Iterable

# Канонические таблицы в velantrim.db. NGram/metrics — пересобираемые виды
# (server.py при старте перестраивает NGramIndex из Validated-фактов).
CANONICAL_TABLES: tuple[tuple[str, str], ...] = (
    ("facts", "fact_id"),
    ("fact_versions", "version_id"),
    ("provenance_chains", "fact_id, seq"),
    ("memory_events", "event_id"),
    ("l0_raw_memory", "raw_id"),
    ("l0_fact_provenance", "id"),
)

NOTES_TABLES: tuple[tuple[str, str], ...] = (
    ("console_notes", "note_id"),
)

# Каталоги, которые tar включает, но которые не являются Canon.
DERIVED_DIR_NAMES = frozenset({"backups"})


class RestoreTargetNotEmptyError(RuntimeError):
    """Цель восстановления не пуста — молчаливое смешивание запрещено."""


class BackupVerificationError(RuntimeError):
    """Архив не читается или SQLite integrity_check не ok."""


class StateMismatchError(RuntimeError):
    """Каноническое состояние после restore не совпало с baseline."""


def _run_tar(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["tar", *args],
        check=True,
        capture_output=True,
        text=True,
    )


def create_cold_tar(data_dir: Path, archive: Path) -> dict[str, Any]:
    """Создать gzip-tar содержимого data_dir (эквивалент `tar czf -C data .`)."""
    data_dir = data_dir.resolve()
    if not data_dir.is_dir():
        raise FileNotFoundError(f"каталог данных не найден: {data_dir}")
    archive = archive.resolve()
    archive.parent.mkdir(parents=True, exist_ok=True)
    if archive.exists():
        archive.unlink()
    tar_bin = shutil.which("tar")
    if tar_bin:
        _run_tar(["czf", str(archive), "-C", str(data_dir), "."])
    else:
        with tarfile.open(archive, "w:gz") as tf:
            tf.add(data_dir, arcname=".")
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    listing = archive_member_names(archive)
    return {
        "archive": str(archive),
        "size_bytes": archive.stat().st_size,
        "sha256": digest,
        "member_count": len(listing),
        "members": listing,
    }


def archive_member_names(archive: Path) -> list[str]:
    tar_bin = shutil.which("tar")
    if tar_bin:
        proc = _run_tar(["tzf", str(archive)])
        names = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
        return sorted(names)
    with tarfile.open(archive, "r:gz") as tf:
        return sorted(m.name for m in tf.getmembers())


def _extract_archive(archive: Path, dest: Path) -> None:
    tar_bin = shutil.which("tar")
    if tar_bin:
        _run_tar(["xzf", str(archive), "-C", str(dest)])
        return
    with tarfile.open(archive, "r:gz") as tf:
        tf.extractall(dest)


def _dir_is_empty(path: Path) -> bool:
    if not path.exists():
        return True
    if not path.is_dir():
        return False
    return next(path.iterdir(), None) is None


def restore_to_fresh_dir(archive: Path, dest: Path) -> None:
    """Распаковать архив только в новый пустой каталог. Иначе — громкий отказ."""
    archive = archive.resolve()
    if not archive.is_file():
        raise FileNotFoundError(f"архив не найден: {archive}")
    dest = dest.resolve()
    if dest.exists() and not _dir_is_empty(dest):
        raise RestoreTargetNotEmptyError(
            f"цель восстановления не пуста: {dest} — restore только в fresh target"
        )
    dest.mkdir(parents=True, exist_ok=True)
    _extract_archive(archive, dest)


def checkpoint_sqlite_dir(data_dir: Path) -> None:
    """Best-effort WAL checkpoint после остановки писателей (аналог clean stop)."""
    for db_path in sorted(_iter_live_sqlite_files(data_dir)):
        conn = sqlite3.connect(str(db_path), timeout=30.0)
        try:
            conn.execute("PRAGMA busy_timeout=5000")
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            conn.commit()
        except sqlite3.Error:
            continue
        finally:
            conn.close()


def _iter_live_sqlite_files(data_dir: Path) -> Iterable[Path]:
    for path in sorted(data_dir.rglob("*")):
        if not path.is_file():
            continue
        if any(part in DERIVED_DIR_NAMES for part in path.relative_to(data_dir).parts):
            continue
        if path.suffix == ".db" or path.suffix == ".sqlite":
            yield path


def _db_fingerprint_kind(rel: str) -> str | None:
    name = Path(rel).name
    if name.endswith("notes.db") or "notes" in name:
        return "notes"
    if "ngram" in name or "graph" in name or "response_audit" in name:
        return None
    if name.endswith(".db") and "velantrim" in name:
        return "canon"
    return None


def sqlite_integrity_ok(db_path: Path) -> str:
    conn = sqlite3.connect(str(db_path), timeout=30.0)
    try:
        row = conn.execute("PRAGMA integrity_check").fetchone()
        return str(row[0]) if row else "missing"
    finally:
        conn.close()


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (name,),
    ).fetchone()
    return row is not None


def _fingerprint_table(conn: sqlite3.Connection, table: str, order_sql: str) -> dict[str, Any]:
    if not _table_exists(conn, table):
        return {"present": False, "count": 0, "sha256": None}
    cur = conn.execute(f"SELECT * FROM {table} ORDER BY {order_sql}")
    rows = cur.fetchall()
    cols = [d[0] for d in (cur.description or [])]
    payload = json.dumps(
        [dict(zip(cols, [row[i] for i in range(len(cols))])) for row in rows],
        ensure_ascii=False,
        sort_keys=True,
        default=str,
    )
    return {
        "present": True,
        "count": len(rows),
        "sha256": hashlib.sha256(payload.encode("utf-8")).hexdigest(),
    }


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def snapshot_data_dir(data_dir: Path) -> dict[str, Any]:
    """Снимок канонического состояния без секретов (только счётчики и хэши)."""
    data_dir = data_dir.resolve()
    files: dict[str, dict[str, Any]] = {}
    for path in sorted(data_dir.rglob("*")):
        if not path.is_file():
            continue
        rel = str(path.relative_to(data_dir)).replace("\\", "/")
        files[rel] = {
            "size_bytes": path.stat().st_size,
            "sha256": _file_sha256(path),
        }

    db_states: dict[str, Any] = {}
    integrity: dict[str, str] = {}
    for db_path in _iter_live_sqlite_files(data_dir):
        rel = str(db_path.relative_to(data_dir)).replace("\\", "/")
        integrity[rel] = sqlite_integrity_ok(db_path)
        conn = sqlite3.connect(str(db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        try:
            kind = _db_fingerprint_kind(rel)
            if kind is None:
                continue
            wanted = NOTES_TABLES if kind == "notes" else CANONICAL_TABLES
            table_map = {
                name: _fingerprint_table(conn, name, order_sql)
                for name, order_sql in wanted
            }
            db_states[rel] = table_map
        finally:
            conn.close()

    audit_present = False
    audit_count = 0
    for table_map in db_states.values():
        events = table_map.get("memory_events") or {}
        if events.get("present") and int(events.get("count") or 0) > 0:
            audit_present = True
            audit_count += int(events["count"])

    return {
        "files": files,
        "sqlite_integrity": integrity,
        "tables": db_states,
        "audit_chain_durable": audit_present,
        "audit_chain_event_count": audit_count,
        "response_audit_claimed": False,
    }


def compare_snapshots(
    baseline: dict[str, Any],
    restored: dict[str, Any],
    *,
    compare_files: bool = False,
) -> None:
    """Сравнить канонические таблицы. Расхождение — громкий отказ, не частичный PASS."""
    mismatches: list[str] = []
    base_tables: dict[str, Any] = baseline.get("tables") or {}
    rest_tables: dict[str, Any] = restored.get("tables") or {}
    keys = sorted(set(base_tables) | set(rest_tables))
    if not keys:
        mismatches.append("нет sqlite-снимков ни в baseline, ни в restored")
    for db_key in keys:
        if db_key not in rest_tables:
            mismatches.append(f"отсутствует БД после restore: {db_key}")
            continue
        if db_key not in base_tables:
            mismatches.append(f"лишняя БД после restore: {db_key}")
            continue
        for table, base_fp in (base_tables[db_key] or {}).items():
            rest_fp = (rest_tables[db_key] or {}).get(table) or {}
            if bool(base_fp.get("present")) != bool(rest_fp.get("present")):
                mismatches.append(
                    f"{db_key}:{table} present baseline={base_fp.get('present')} "
                    f"restored={rest_fp.get('present')}"
                )
                continue
            if not base_fp.get("present"):
                continue
            if base_fp.get("count") != rest_fp.get("count"):
                mismatches.append(
                    f"{db_key}:{table} count {base_fp.get('count')} != {rest_fp.get('count')}"
                )
            if base_fp.get("sha256") != rest_fp.get("sha256"):
                mismatches.append(f"{db_key}:{table} sha256 mismatch")
    for db_key, status in (baseline.get("sqlite_integrity") or {}).items():
        rest_status = (restored.get("sqlite_integrity") or {}).get(db_key)
        if status != "ok":
            mismatches.append(f"baseline integrity {db_key}={status}")
        if rest_status != "ok":
            mismatches.append(f"restored integrity {db_key}={rest_status}")
    if compare_files:
        base_files = baseline.get("files") or {}
        rest_files = restored.get("files") or {}
        canon_base = {
            name: meta
            for name, meta in base_files.items()
            if not any(part in DERIVED_DIR_NAMES for part in Path(name).parts)
            and not name.endswith(("-wal", "-shm", "-journal"))
        }
        canon_rest = {
            name: meta
            for name, meta in rest_files.items()
            if not any(part in DERIVED_DIR_NAMES for part in Path(name).parts)
            and not name.endswith(("-wal", "-shm", "-journal"))
        }
        if set(canon_base) != set(canon_rest):
            missing = sorted(set(canon_base) - set(canon_rest))
            extra = sorted(set(canon_rest) - set(canon_base))
            mismatches.append(f"file set mismatch missing={missing} extra={extra}")
        else:
            for name, meta in canon_base.items():
                if meta.get("sha256") != (canon_rest.get(name) or {}).get("sha256"):
                    mismatches.append(f"file sha256 mismatch: {name}")
    if mismatches:
        raise StateMismatchError(
            "NO_SILENT_PARTIAL_RECOVERY: " + "; ".join(mismatches)
        )


def verify_archive(archive: Path, extract_dir: Path | None = None) -> dict[str, Any]:
    """Прочитать tar, распаковать во временный/указанный каталог, проверить SQLite."""
    archive = archive.resolve()
    if not archive.is_file():
        raise FileNotFoundError(f"архив не найден: {archive}")
    listing = archive_member_names(archive)
    if not listing:
        raise BackupVerificationError("архив пуст")
    cleanup = False
    dest = extract_dir
    if dest is None:
        dest = Path(tempfile.mkdtemp(prefix="velantrim-backup-verify-"))
        cleanup = True
    try:
        if not _dir_is_empty(dest):
            raise RestoreTargetNotEmptyError(f"каталог проверки не пуст: {dest}")
        dest.mkdir(parents=True, exist_ok=True)
        _extract_archive(archive, dest)
        integrity: dict[str, str] = {}
        for db_path in _iter_live_sqlite_files(dest):
            rel = str(db_path.relative_to(dest)).replace("\\", "/")
            status = sqlite_integrity_ok(db_path)
            integrity[rel] = status
            if status != "ok":
                raise BackupVerificationError(
                    f"PRAGMA integrity_check {rel} = {status}"
                )
        return {
            "archive": str(archive),
            "size_bytes": archive.stat().st_size,
            "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
            "members": listing,
            "sqlite_integrity": integrity,
        }
    finally:
        if cleanup:
            shutil.rmtree(dest, ignore_errors=True)


def docker_volume_backup(volume: str, archive: Path) -> dict[str, Any]:
    """Документированный cold backup именованного тома через busybox tar."""
    if shutil.which("docker") is None:
        raise RuntimeError("docker CLI недоступен")
    archive = archive.resolve()
    archive.parent.mkdir(parents=True, exist_ok=True)
    host_dir = archive.parent
    name = archive.name
    subprocess.run(
        [
            "docker", "run", "--rm",
            "-v", f"{volume}:/data:ro",
            "-v", f"{host_dir}:/backup",
            "busybox",
            "tar", "czf", f"/backup/{name}", "-C", "/data", ".",
        ],
        check=True,
    )
    return {
        "archive": str(archive),
        "size_bytes": archive.stat().st_size,
        "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "members": archive_member_names(archive),
        "volume": volume,
    }


def docker_volume_restore_fresh(archive: Path, new_volume: str) -> None:
    """Восстановить архив только в НОВЫЙ пустой Docker-том."""
    if shutil.which("docker") is None:
        raise RuntimeError("docker CLI недоступен")
    archive = archive.resolve()
    inspect = subprocess.run(
        ["docker", "volume", "inspect", new_volume],
        capture_output=True,
        text=True,
    )
    if inspect.returncode != 0:
        subprocess.run(["docker", "volume", "create", new_volume], check=True)
    listing = subprocess.run(
        [
            "docker", "run", "--rm",
            "-v", f"{new_volume}:/data",
            "busybox", "sh", "-c", "ls -A /data",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    if listing.stdout.strip():
        raise RestoreTargetNotEmptyError(
            f"том {new_volume} не пуст — restore только в fresh volume"
        )
    host_dir = archive.parent
    subprocess.run(
        [
            "docker", "run", "--rm",
            "-v", f"{new_volume}:/data",
            "-v", f"{host_dir}:/backup",
            "busybox",
            "tar", "xzf", f"/backup/{archive.name}", "-C", "/data",
        ],
        check=True,
    )


def _cmd_backup(args: argparse.Namespace) -> int:
    meta = create_cold_tar(Path(args.data_dir), Path(args.archive))
    print(json.dumps(meta, ensure_ascii=False, indent=2))
    return 0


def _cmd_verify(args: argparse.Namespace) -> int:
    extract = Path(args.extract_dir) if args.extract_dir else None
    try:
        meta = verify_archive(Path(args.archive), extract)
    except (BackupVerificationError, RestoreTargetNotEmptyError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(meta, ensure_ascii=False, indent=2))
    return 0


def _cmd_restore(args: argparse.Namespace) -> int:
    try:
        restore_to_fresh_dir(Path(args.archive), Path(args.target))
    except RestoreTargetNotEmptyError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps({"restored_to": str(Path(args.target).resolve())}, indent=2))
    return 0


def _cmd_snapshot(args: argparse.Namespace) -> int:
    snap = snapshot_data_dir(Path(args.data_dir))
    print(json.dumps(snap, ensure_ascii=False, indent=2))
    return 0


def _cmd_compare(args: argparse.Namespace) -> int:
    baseline = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
    restored = json.loads(Path(args.restored).read_text(encoding="utf-8"))
    try:
        compare_snapshots(baseline, restored, compare_files=args.files)
    except StateMismatchError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print("STATE_PARITY_OK")
    return 0


def _cmd_docker_backup(args: argparse.Namespace) -> int:
    meta = docker_volume_backup(args.volume, Path(args.archive))
    print(json.dumps(meta, ensure_ascii=False, indent=2))
    return 0


def _cmd_docker_restore(args: argparse.Namespace) -> int:
    try:
        docker_volume_restore_fresh(Path(args.archive), args.new_volume)
    except RestoreTargetNotEmptyError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps({"volume": args.new_volume, "fresh": True}, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Cold tar backup/verify/restore-to-fresh для каталога данных Titan",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    backup = sub.add_parser("backup", help="tar czf каталога данных")
    backup.add_argument("--data-dir", required=True)
    backup.add_argument("--archive", required=True)
    backup.set_defaults(func=_cmd_backup)

    verify = sub.add_parser("verify", help="проверить архив и SQLite integrity")
    verify.add_argument("--archive", required=True)
    verify.add_argument("--extract-dir", default=None)
    verify.set_defaults(func=_cmd_verify)

    restore = sub.add_parser("restore", help="распаковать только в пустой каталог")
    restore.add_argument("--archive", required=True)
    restore.add_argument("--target", required=True)
    restore.set_defaults(func=_cmd_restore)

    snap = sub.add_parser("snapshot", help="канонический снимок без секретов")
    snap.add_argument("--data-dir", required=True)
    snap.set_defaults(func=_cmd_snapshot)

    compare = sub.add_parser("compare", help="сравнить два снимка, fail-loud")
    compare.add_argument("--baseline", required=True)
    compare.add_argument("--restored", required=True)
    compare.add_argument("--files", action="store_true")
    compare.set_defaults(func=_cmd_compare)

    dbackup = sub.add_parser("docker-backup", help="документированный volume tar")
    dbackup.add_argument("--volume", required=True)
    dbackup.add_argument("--archive", required=True)
    dbackup.set_defaults(func=_cmd_docker_backup)

    drestore = sub.add_parser("docker-restore-fresh", help="restore в новый пустой том")
    drestore.add_argument("--archive", required=True)
    drestore.add_argument("--new-volume", required=True)
    drestore.set_defaults(func=_cmd_docker_restore)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
