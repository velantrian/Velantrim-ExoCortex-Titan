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
import os
import shutil
import sqlite3
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.error
import urllib.request
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

# Обязательные Class-A SQLite в корне тома. notes.db не обязателен:
# пустой деплой может не создать консольные заметки.
REQUIRED_CANONICAL_DBS: tuple[str, ...] = ("velantrim.db",)

# Контракт Titan backup — обычные файлы и каталоги. Симлинки, hardlink,
# fifo/chr/blk в архиве не требуются и отклоняются.
_SAFE_TAR_TYPES = frozenset({tarfile.REGTYPE, tarfile.AREGTYPE, tarfile.DIRTYPE})

# uid/gid образа velantrim-titan (Dockerfile USER). busybox tar идёт от
# root, поэтому после Docker-restore нужна смена владельца.
_PROD_VOLUME_OWNER = "10001:10001"


class RestoreTargetNotEmptyError(RuntimeError):
    """Цель восстановления не пуста — молчаливое смешивание запрещено."""


class BackupVerificationError(RuntimeError):
    """Архив не читается, неполон или SQLite integrity_check не ok."""


class UnsafeArchiveMemberError(BackupVerificationError):
    """Элемент tar выходит за корень restore или не входит в контракт Titan."""


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
    with tarfile.open(archive, "r:*") as tf:
        return sorted(m.name for m in tf.getmembers())


def _posix_member_name(name: str) -> str:
    return (name or "").replace("\\", "/")


def _is_absolute_member(name: str) -> bool:
    posix = _posix_member_name(name)
    if posix.startswith("/") or posix.startswith("//"):
        return True
    if len(posix) >= 3 and posix[1] == ":" and posix[0].isalpha() and posix[2] == "/":
        return True
    return posix.startswith("\\\\") or (len(name) >= 2 and name[1] == ":")


def _posix_escapes_root(name: str) -> bool:
    """True, если логический путь выходит за корень restore (tar-slip)."""
    posix = _posix_member_name(name)
    if _is_absolute_member(posix):
        return True
    depth = 0
    for part in posix.split("/"):
        if part in ("", ".",):
            continue
        if part == "..":
            depth -= 1
            if depth < 0:
                return True
            continue
        depth += 1
    return False


def _link_target_escapes_root(member_name: str, linkname: str) -> bool:
    if _is_absolute_member(linkname) or _posix_escapes_root(linkname):
        return True
    posix = _posix_member_name(member_name).rstrip("/")
    parent = posix.rsplit("/", 1)[0] if "/" in posix else ""
    combined = f"{parent}/{linkname}" if parent else linkname
    return _posix_escapes_root(combined)


def assert_archive_members_safe(archive: Path) -> None:
    """Отклонить абсолютные пути, ..-escape, symlink/hardlink-escape и special."""
    archive = archive.resolve()
    with tarfile.open(archive, "r:*") as tf:
        for info in tf.getmembers():
            name = info.name or ""
            if "\x00" in name:
                raise UnsafeArchiveMemberError(f"REFUSE NUL в имени: {name!r}")
            if _is_absolute_member(name) or _posix_escapes_root(name):
                kind = "absolute path" if _is_absolute_member(name) else "../escape"
                raise UnsafeArchiveMemberError(f"REFUSE {kind}: {name}")
            if info.issym() or info.islnk():
                link = info.linkname or ""
                if _link_target_escapes_root(name, link):
                    raise UnsafeArchiveMemberError(
                        f"REFUSE symlink/hardlink escape: {name} -> {link}"
                    )
                raise UnsafeArchiveMemberError(
                    f"REFUSE symlink/hardlink (не входит в контракт Titan backup): {name}"
                )
            if info.type not in _SAFE_TAR_TYPES:
                raise UnsafeArchiveMemberError(
                    f"REFUSE special entry type {info.type!r}: {name}"
                )


def _extract_archive(archive: Path, dest: Path) -> None:
    assert_archive_members_safe(archive)
    tar_bin = shutil.which("tar")
    if tar_bin:
        _run_tar(["xzf", str(archive), "-C", str(dest)])
        return
    with tarfile.open(archive, "r:*") as tf:
        kwargs: dict[str, Any] = {}
        if sys.version_info >= (3, 12):
            kwargs["filter"] = "data"
        tf.extractall(dest, **kwargs)


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


def sqlite_user_version(db_path: Path) -> int:
    conn = sqlite3.connect(str(db_path), timeout=30.0)
    try:
        row = conn.execute("PRAGMA user_version").fetchone()
        return int(row[0]) if row else 0
    finally:
        conn.close()


def _collect_sqlite_user_versions(data_dir: Path) -> dict[str, int]:
    versions: dict[str, int] = {}
    for db_path in _iter_live_sqlite_files(data_dir):
        rel = str(db_path.relative_to(data_dir)).replace("\\", "/")
        versions[rel] = sqlite_user_version(db_path)
    return versions


def _strip_leading_dot_slash(name: str) -> str:
    posix = _posix_member_name(name)
    while posix.startswith("./"):
        posix = posix[2:]
    return posix


def _member_is_required_canonical_db(name: str) -> bool:
    return _strip_leading_dot_slash(name) == "velantrim.db"


def _missing_required_canonical_dbs(root: Path) -> list[str]:
    missing: list[str] = []
    for name in REQUIRED_CANONICAL_DBS:
        if not (root / name).is_file():
            missing.append(name)
    return missing


def _assert_required_canonical_dbs(root: Path, listing: list[str]) -> None:
    if not any(_member_is_required_canonical_db(name) for name in listing):
        raise BackupVerificationError(
            "нет обязательной канонической БД velantrim.db в архиве "
            "(непустой tar без required Class-A DB не является успешной проверкой)"
        )
    missing = _missing_required_canonical_dbs(root)
    if missing:
        raise BackupVerificationError(
            "нет обязательной канонической БД в корне restore: "
            + ", ".join(missing)
        )


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
        "sqlite_user_versions": _collect_sqlite_user_versions(data_dir),
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
    base_uv: dict[str, Any] = baseline.get("sqlite_user_versions") or {}
    rest_uv: dict[str, Any] = restored.get("sqlite_user_versions") or {}
    uv_keys = sorted(set(base_uv) | set(rest_uv))
    for db_key in uv_keys:
        kind = _db_fingerprint_kind(db_key)
        required = (
            Path(db_key).name in REQUIRED_CANONICAL_DBS
            and Path(db_key).parent.as_posix() in (".", "")
        )
        if kind != "canon" and not required:
            continue
        if base_uv.get(db_key) != rest_uv.get(db_key):
            mismatches.append(
                f"user_version {db_key}: baseline={base_uv.get(db_key)} "
                f"restored={rest_uv.get(db_key)}"
            )
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
    assert_archive_members_safe(archive)
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
        _assert_required_canonical_dbs(dest, listing)
        integrity: dict[str, str] = {}
        for db_path in _iter_live_sqlite_files(dest):
            rel = str(db_path.relative_to(dest)).replace("\\", "/")
            status = sqlite_integrity_ok(db_path)
            integrity[rel] = status
            if status != "ok":
                raise BackupVerificationError(
                    f"PRAGMA integrity_check {rel} = {status}"
                )
        user_versions = _collect_sqlite_user_versions(dest)
        if "velantrim.db" not in user_versions:
            raise BackupVerificationError(
                "нет PRAGMA user_version для обязательной канонической БД velantrim.db"
            )
        return {
            "archive": str(archive),
            "size_bytes": archive.stat().st_size,
            "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
            "members": listing,
            "sqlite_integrity": integrity,
            "sqlite_user_versions": user_versions,
            "required_canonical_dbs": list(REQUIRED_CANONICAL_DBS),
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
    assert_archive_members_safe(archive)
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
    subprocess.run(
        [
            "docker", "run", "--rm",
            "-v", f"{new_volume}:/data",
            "busybox",
            "chown", "-R", _PROD_VOLUME_OWNER, "/data",
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
    except (RestoreTargetNotEmptyError, BackupVerificationError) as exc:
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
    except (RestoreTargetNotEmptyError, BackupVerificationError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps({"volume": args.new_volume, "fresh": True}, indent=2))
    return 0


def _require_docker_daemon() -> None:
    if shutil.which("docker") is None:
        raise RuntimeError("BLOCKED_BY_ENVIRONMENT: docker CLI недоступен")
    probe = subprocess.run(["docker", "info"], capture_output=True, text=True)
    if probe.returncode != 0:
        raise RuntimeError("BLOCKED_BY_ENVIRONMENT: docker daemon недоступен")


def _compose_argv(
    compose_file: Path,
    env_file: Path,
    project: str,
    extra_files: Iterable[Path] | None = None,
) -> list[str]:
    cmd = [
        "docker", "compose",
        "-p", project,
        "--env-file", str(env_file),
        "-f", str(compose_file),
    ]
    for extra in extra_files or ():
        cmd.extend(["-f", str(extra)])
    return cmd


def _compose_run(
    compose_file: Path,
    env_file: Path,
    project: str,
    args: list[str],
    extra_files: Iterable[Path] | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        [*_compose_argv(compose_file, env_file, project, extra_files), *args],
        check=False,
        capture_output=True,
        text=True,
        env=os.environ.copy(),
    )
    if check and proc.returncode != 0:
        raise RuntimeError(
            f"docker compose {' '.join(args)} failed ({proc.returncode}):\n"
            f"{proc.stdout}\n{proc.stderr}"
        )
    return proc


def _http_json(
    method: str,
    url: str,
    api_key: str | None = None,
    body: dict[str, Any] | None = None,
    timeout: float = 30.0,
) -> tuple[int, Any]:
    data = None
    headers = {"Accept": "application/json"}
    if api_key:
        headers["X-Api-Key"] = api_key
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
            payload: Any = json.loads(raw.decode("utf-8")) if raw else {}
            return int(response.status), payload
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        text = raw.decode("utf-8", errors="replace") if raw else ""
        raise RuntimeError(f"{method} {url} -> {exc.code}: {text}") from exc


def _wait_health(base_url: str, timeout_s: float = 120.0) -> dict[str, Any]:
    deadline = time.time() + timeout_s
    last = "нет ответа"
    while time.time() < deadline:
        try:
            status, payload = _http_json("GET", f"{base_url}/health")
            if status == 200:
                return payload if isinstance(payload, dict) else {"raw": payload}
        except Exception as exc:  # noqa: BLE001 — диагностика ожидания boot
            last = str(exc)
        time.sleep(1)
    raise RuntimeError(f"/health не стал 200 за {timeout_s:.0f}с: {last}")


def _container_named_volume(container: str, dest: str = "/app/data") -> str:
    proc = subprocess.run(
        [
            "docker", "inspect",
            "-f",
            "{{range .Mounts}}{{if eq .Destination \"" + dest + "\"}}{{.Name}}{{end}}{{end}}",
            container,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    name = proc.stdout.strip()
    if not name:
        raise RuntimeError(f"именованный том для {container}:{dest} не найден")
    return name


def _assert_post_restore_mount_identity(
    original_volume: str,
    requested_restore_volume: str,
    mounted_restore_volume: str,
) -> None:
    """ORIGINAL_STATE_ISOLATED только если /app/data — запрошенный restore-том."""
    if mounted_restore_volume == original_volume:
        raise StateMismatchError(
            "ORIGINAL_STATE_ISOLATED FAIL: после restore-boot /app/data "
            f"смонтирован с original_volume {original_volume}"
        )
    if mounted_restore_volume != requested_restore_volume:
        raise StateMismatchError(
            "ORIGINAL_STATE_ISOLATED FAIL: mounted "
            f"{mounted_restore_volume} != requested {requested_restore_volume}"
        )


def _docker_exec_user_version(container: str = "velantrim-titan-prod") -> int:
    proc = subprocess.run(
        [
            "docker", "exec", container,
            "python", "-c",
            "import sqlite3; print(sqlite3.connect('/app/data/velantrim.db')"
            ".execute('PRAGMA user_version').fetchone()[0])",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return int(proc.stdout.strip())


def _docker_drill_seed(base_url: str, api_key: str, nonce: str) -> dict[str, Any]:
    observed_id = f"ph2a_observed_{nonce}"
    supported_id = f"ph2a_supported_{nonce}"
    validated_id = f"ph2a_validated_{nonce}"
    invalidated_id = f"ph2a_invalidated_{nonce}"
    for fact_id, claim, confidence, evidence in (
        (observed_id, f"PH-2A observed claim {nonce}", 0.4, None),
        (supported_id, f"PH-2A supported claim {nonce}", 0.6, None),
        (validated_id, f"PH-2A validated claim {nonce}", 0.9, ["ev-a", "ev-b"]),
        (invalidated_id, f"PH-2A invalidated claim {nonce}", 0.55, None),
    ):
        payload: dict[str, Any] = {
            "fact_id": fact_id,
            "claim": claim,
            "source": "ph2a-backup-drill",
            "confidence": confidence,
            "metadata": {"memory_category": "personal", "drill": nonce},
        }
        if evidence is not None:
            payload["metadata"]["evidence_refs"] = evidence
        status, _ = _http_json("POST", f"{base_url}/facts", api_key, payload)
        if status not in (200, 201):
            raise RuntimeError(f"POST /facts {fact_id} -> {status}")
    for fact_id in (supported_id, validated_id, invalidated_id):
        for state in ("Hypothesized", "Supported"):
            _http_json(
                "PATCH",
                f"{base_url}/facts/{fact_id}/transition",
                api_key,
                {"new_state": state, "by": "ph2a-backup-drill"},
            )
    _http_json(
        "PATCH",
        f"{base_url}/facts/{validated_id}/transition",
        api_key,
        {"new_state": "Validated", "by": "ph2a-backup-drill"},
    )
    _http_json("PATCH", f"{base_url}/facts/{invalidated_id}/invalidate", api_key, {})
    _status, note = _http_json(
        "POST",
        f"{base_url}/console/notes",
        api_key,
        {
            "title": f"PH-2A note {nonce}",
            "content": f"Deterministic console note for backup drill {nonce}",
            "tags": ["ph2a", "backup"],
        },
    )
    note_id = note["note_id"]
    _http_json(
        "POST",
        f"{base_url}/ingest/text",
        api_key,
        {
            "text": f"PH-2A ingest fragment {nonce} stays Observed.",
            "source": "ph2a-backup-drill-ingest",
            "chunk_size": 200,
        },
    )
    return {
        "fact_ids": {
            "observed": observed_id,
            "supported": supported_id,
            "validated": validated_id,
            "invalidated": invalidated_id,
        },
        "note_id": note_id,
    }


def _docker_drill_selected_state(
    base_url: str, api_key: str, seed: dict[str, Any]
) -> dict[str, Any]:
    _status, facts = _http_json("GET", f"{base_url}/facts?limit=100", api_key)
    listed = facts["facts"]
    by_id = {
        item["fact_id"]: {
            "claim": item["claim"],
            "epistemic_state": item["epistemic_state"],
            "confidence": item["confidence"],
            "source": item["source"],
        }
        for item in listed
    }
    note_id = str(seed["note_id"])
    _status, note = _http_json("GET", f"{base_url}/console/notes/{note_id}", api_key)
    validated_id = str(seed["fact_ids"]["validated"])
    _status, validated = _http_json("GET", f"{base_url}/facts/{validated_id}", api_key)
    return {
        "facts_total": facts["total"],
        "facts_by_id": by_id,
        "note": {
            "note_id": note["note_id"],
            "title": note["title"],
            "content": note["content"],
            "tags": note["tags"],
        },
        "validated_state": validated["epistemic_state"],
    }


def _write_synthetic_prod_env(path: Path, port: int) -> None:
    """Синтетический .env без секретов: порт/bind/provider. Ключ — только в env процесса."""
    path.write_text(
        "\n".join(
            [
                f"VELANTRIM_PUBLIC_PORT={port}",
                "VELANTRIM_BIND_ADDR=127.0.0.1",
                "LLM_PROVIDER=none",
                "LOG_LEVEL=INFO",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_restore_override(path: Path, restore_volume: str) -> None:
    """Сбросить driver: local из prod-файла, затем указать external-том restore."""
    path.write_text(
        "\n".join(
            [
                "volumes:",
                "  velantrim_prod_data:",
                "    driver: !reset null",
                "    external: true",
                f"    name: {restore_volume}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _cleanup_docker_drill(
    compose_file: Path,
    env_file: Path | None,
    project: str,
    extra_files: list[Path],
    volumes: list[str],
    work_dir: Path | None,
    remove_work_dir: bool,
) -> None:
    if env_file is not None and env_file.is_file():
        _compose_run(
            compose_file,
            env_file,
            project,
            ["down", "-v", "--remove-orphans"],
            extra_files=extra_files,
            check=False,
        )
        _compose_run(
            compose_file,
            env_file,
            project,
            ["down", "-v", "--remove-orphans"],
            check=False,
        )
    subprocess.run(["docker", "rm", "-f", "velantrim-titan-prod"], capture_output=True)
    for volume in volumes:
        subprocess.run(["docker", "volume", "rm", "-f", volume], capture_output=True)
    if work_dir is not None and remove_work_dir:
        shutil.rmtree(work_dir, ignore_errors=True)
    elif work_dir is not None:
        for leftover in work_dir.glob("*"):
            if leftover.is_file():
                leftover.unlink(missing_ok=True)


def run_docker_production_drill(
    compose_file: Path,
    *,
    project: str,
    port: int,
    image: str,
    api_key: str,
    work_dir: Path | None = None,
) -> dict[str, Any]:
    """Один bounded proof: compose.prod → named volume tar → fresh restore → /health."""
    _require_docker_daemon()
    inspect = subprocess.run(
        ["docker", "image", "inspect", image],
        capture_output=True,
        text=True,
    )
    if inspect.returncode != 0:
        raise RuntimeError(f"BLOCKED_BY_ENVIRONMENT: образ {image} отсутствует")
    compose_file = compose_file.resolve()
    if not compose_file.is_file():
        raise FileNotFoundError(f"compose не найден: {compose_file}")
    owned_work = work_dir is None
    work = work_dir.resolve() if work_dir is not None else Path(
        tempfile.mkdtemp(prefix="ph2a-docker-drill-")
    )
    work.mkdir(parents=True, exist_ok=True)
    env_file = work / "ph2a.env"
    archive = work / "velantrim-prod-ph2a.tar.gz"
    override = work / "docker-compose.restore.yml"
    original_volume = f"{project}_velantrim_prod_data"
    restore_volume = f"{project}_velantrim_prod_restore"
    extra_files: list[Path] = []
    nonce = f"d{int(time.time())}"
    base_url = f"http://127.0.0.1:{port}"
    subprocess.run(["docker", "rm", "-f", "velantrim-titan-prod"], capture_output=True)
    try:
        os.environ["VELANTRIM_API_KEY"] = api_key
        _write_synthetic_prod_env(env_file, port)
        _compose_run(
            compose_file, env_file, project,
            ["up", "-d", "--no-build"],
        )
        health = _wait_health(base_url)
        original_volume = _container_named_volume("velantrim-titan-prod")
        seed = _docker_drill_seed(base_url, api_key, nonce)
        selected_before = _docker_drill_selected_state(base_url, api_key, seed)
        baseline_user_version = _docker_exec_user_version()
        _compose_run(compose_file, env_file, project, ["stop"])
        docker_volume_backup(original_volume, archive)
        verify_meta = verify_archive(archive)
        backup_verified_user_version = verify_meta["sqlite_user_versions"]["velantrim.db"]
        _compose_run(compose_file, env_file, project, ["down"])
        subprocess.run(["docker", "rm", "-f", "velantrim-titan-prod"], capture_output=True)
        subprocess.run(["docker", "volume", "create", restore_volume], check=True)
        extra_files = [override]
        _write_restore_override(override, restore_volume)
        docker_volume_restore_fresh(archive, restore_volume)
        _compose_run(
            compose_file, env_file, project,
            ["up", "-d", "--no-build"],
            extra_files=extra_files,
        )
        health_after = _wait_health(base_url)
        mounted_restore_volume = _container_named_volume("velantrim-titan-prod")
        _assert_post_restore_mount_identity(
            original_volume, restore_volume, mounted_restore_volume
        )
        selected_after = _docker_drill_selected_state(base_url, api_key, seed)
        restored_user_version = _docker_exec_user_version()
        if selected_before != selected_after:
            raise StateMismatchError(
                "NO_SILENT_PARTIAL_RECOVERY: recovered API state mismatch"
            )
        if not (
            baseline_user_version
            == backup_verified_user_version
            == restored_user_version
        ):
            raise StateMismatchError(
                "NO_SILENT_PARTIAL_RECOVERY: user_version "
                f"baseline={baseline_user_version} "
                f"backup={backup_verified_user_version} "
                f"restored={restored_user_version}"
            )
        return {
            "observation": "OBSERVED",
            "project": project,
            "original_volume": original_volume,
            "restore_volume": restore_volume,
            "requested_restore_volume": restore_volume,
            "mounted_restore_volume": mounted_restore_volume,
            "original_state_isolated": True,
            "ORIGINAL_STATE_ISOLATED": "PASS",
            "archive_sha256": verify_meta["sha256"],
            "health_before": health,
            "health_after": health_after,
            "selected_state": selected_after,
            "sqlite_user_versions": {
                "BASELINE_USER_VERSION": baseline_user_version,
                "BACKUP_VERIFIED_USER_VERSION": backup_verified_user_version,
                "RESTORED_USER_VERSION": restored_user_version,
            },
            "required_canonical_dbs": list(REQUIRED_CANONICAL_DBS),
        }
    finally:
        _cleanup_docker_drill(
            compose_file,
            env_file if env_file.exists() else None,
            project,
            extra_files,
            [original_volume, restore_volume],
            work,
            owned_work,
        )


def _cmd_docker_drill(args: argparse.Namespace) -> int:
    try:
        work = Path(args.work_dir) if args.work_dir else None
        result = run_docker_production_drill(
            Path(args.compose_file),
            project=args.project,
            port=int(args.port),
            image=args.image,
            api_key=args.api_key,
            work_dir=work,
        )
    except RuntimeError as exc:
        message = str(exc)
        print(message, file=sys.stderr)
        if message.startswith("BLOCKED_BY_ENVIRONMENT"):
            return 2
        return 1
    except (BackupVerificationError, RestoreTargetNotEmptyError, StateMismatchError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as exc:
        print(exc.stdout or "", file=sys.stderr)
        print(exc.stderr or "", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
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

    ddrill = sub.add_parser(
        "docker-drill",
        help="bounded proof: compose.prod named volume → backup → fresh restore → /health",
    )
    ddrill.add_argument("--compose-file", default="docker-compose.prod.yml")
    ddrill.add_argument("--project", default="ph2a455")
    ddrill.add_argument("--port", type=int, default=18082)
    ddrill.add_argument("--image", default="velantrim-titan:prod")
    ddrill.add_argument(
        "--api-key",
        default="ph2a-synthetic-backup-key-not-a-secret",
    )
    ddrill.add_argument("--work-dir", default=None)
    ddrill.set_defaults(func=_cmd_docker_drill)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
