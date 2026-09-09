"""Самоочищающееся доказательство cold tar → restore в свежий каталог.

Покрывает контракт docs/operations/hardened-production-profile.md §9:
остановка писателей, tar каталога данных, проверка архива, распаковка
ТОЛЬКО в пустую цель, загрузка из restored state, паритет Canon.

Docker-демон не требуется: именованный том — это тот же каталог /app/data.
Временные БД, архивы и restore-каталоги живут в tmp_path и удаляются pytest.
"""
from __future__ import annotations

import importlib.util
import io
import sqlite3
import sys
import tarfile
import time
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "prod_volume_backup_restore.py"
PROD_COMPOSE = REPO_ROOT / "docker-compose.prod.yml"
OPS_DOC = REPO_ROOT / "docs" / "operations" / "hardened-production-profile.md"
APP_DATA_PREFIX = "/app/data"

DRILL_API_KEY = "ph2a-synthetic-backup-key-not-a-secret"

# Пины, влияющие на дюрабилити Canon. Тест сверяет их с compose, чтобы не
# появился второй источник правды по флагам.
DURABILITY_PINS = (
    "STORAGE_BACKEND",
    "VELANTRIM_SQLITE_SYNCHRONOUS",
    "VELANTRIM_VERSION_SNAPSHOTS",
    "ENABLE_WRITE_GATE",
    "ENABLE_TRUTH_GATE",
    "ENABLE_TRUTH_POLICY",
    "ENABLE_RESPONSE_AUDIT",
    "SLEEP_WORKER_ENABLED",
    "ENABLE_EVENT_BUS",
    "ENABLE_CAUSAL_GRAPH",
    "CAUSAL_PERSIST",
)


def _load_helper():
    spec = importlib.util.spec_from_file_location("prod_volume_backup_restore", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


helper = _load_helper()


def _compose_env() -> dict[str, str]:
    raw = yaml.safe_load(PROD_COMPOSE.read_text(encoding="utf-8"))
    out: dict[str, str] = {}
    for item in raw["services"]["velantrim"].get("environment") or []:
        key, _, value = str(item).partition("=")
        out[key.strip()] = value
    return out


def _resolve_compose_value(raw: str) -> str | None:
    if "${" not in raw:
        return raw
    if ":?" in raw:
        return None
    if raw.startswith("${") and ":-" in raw and raw.endswith("}"):
        return raw.split(":-", 1)[1][:-1]
    return None


def _prod_runtime_env(data_dir: Path) -> dict[str, str]:
    compose = _compose_env()
    env: dict[str, str] = {
        "VELANTRIM_API_KEY": DRILL_API_KEY,
        "VELANTRIM_ALLOW_OPEN": "false",
        "LLM_PROVIDER": "none",
        "ENABLE_API_DOCS": "false",
    }
    data = str(data_dir)
    for key, raw in compose.items():
        value = _resolve_compose_value(raw)
        if value is None:
            continue
        if value.startswith(APP_DATA_PREFIX):
            env[key] = data + value[len(APP_DATA_PREFIX):]
        else:
            env[key] = value
    env["SQLITE_AUDIT_PATH"] = str(data_dir / "response_audit.db")
    env["CORE_BLOCKS_DB"] = str(data_dir / "core_blocks.db")
    env["NOTEBOOK_DB"] = str(data_dir / "notebook.db")
    return env


def _unload_runtime() -> None:
    for name in list(sys.modules):
        if name == "server" or name.startswith(("server.", "core.", "api.", "scripts.apply_migrations")):
            del sys.modules[name]


def _apply_env(monkeypatch, env: dict[str, str]) -> None:
    for key, value in env.items():
        monkeypatch.setenv(key, value)


def _boot_client(monkeypatch, data_dir: Path):
    data_dir.mkdir(parents=True, exist_ok=True)
    env = _prod_runtime_env(data_dir)
    _apply_env(monkeypatch, env)
    _unload_runtime()
    from fastapi.testclient import TestClient

    import server as srv
    from core.feature_config import clear_config_cache

    clear_config_cache()
    client = TestClient(srv.app)
    client.headers.update({"X-Api-Key": DRILL_API_KEY})
    return client, srv


def _close_writers(_srv) -> None:
    mem = sys.modules.get("core.memory")
    store = getattr(mem, "_GLOBAL_STORE", None) if mem is not None else None
    closer = getattr(store, "close", None)
    if callable(closer):
        closer()


def _seed_diverse_state(client, nonce: str) -> dict[str, object]:
    observed_id = f"ph2a_observed_{nonce}"
    supported_id = f"ph2a_supported_{nonce}"
    validated_id = f"ph2a_validated_{nonce}"
    invalidated_id = f"ph2a_invalidated_{nonce}"

    created = []
    for fact_id, claim, confidence, evidence in (
        (observed_id, f"PH-2A observed claim {nonce}", 0.4, None),
        (supported_id, f"PH-2A supported claim {nonce}", 0.6, None),
        (validated_id, f"PH-2A validated claim {nonce}", 0.9, ["ev-a", "ev-b"]),
        (invalidated_id, f"PH-2A invalidated claim {nonce}", 0.55, None),
    ):
        payload = {
            "fact_id": fact_id,
            "claim": claim,
            "source": "ph2a-backup-drill",
            "confidence": confidence,
            "metadata": {"memory_category": "personal", "drill": nonce},
        }
        if evidence is not None:
            payload["metadata"]["evidence_refs"] = evidence
        response = client.post("/facts", json=payload)
        assert response.status_code in (200, 201), response.text
        created.append(fact_id)

    for fact_id in (supported_id, validated_id, invalidated_id):
        for state in ("Hypothesized", "Supported"):
            patched = client.patch(
                f"/facts/{fact_id}/transition",
                json={"new_state": state, "by": "ph2a-backup-drill"},
            )
            assert patched.status_code == 200, patched.text

    validated = client.patch(
        f"/facts/{validated_id}/transition",
        json={"new_state": "Validated", "by": "ph2a-backup-drill"},
    )
    assert validated.status_code == 200, validated.text
    assert validated.json()["epistemic_state"] == "Validated"

    invalidated = client.patch(f"/facts/{invalidated_id}/invalidate", json={})
    assert invalidated.status_code == 200, invalidated.text

    note = client.post(
        "/console/notes",
        json={
            "title": f"PH-2A note {nonce}",
            "content": f"Deterministic console note for backup drill {nonce}",
            "tags": ["ph2a", "backup"],
        },
    )
    assert note.status_code == 201, note.text
    note_id = note.json()["note_id"]

    ingest = client.post(
        "/ingest/text",
        json={
            "text": f"PH-2A ingest fragment {nonce} stays Observed.",
            "source": "ph2a-backup-drill-ingest",
            "chunk_size": 200,
        },
    )
    assert ingest.status_code in (200, 201), ingest.text

    facts = client.get("/facts", params={"limit": 100})
    assert facts.status_code == 200, facts.text
    listed = facts.json()["facts"]
    by_id = {item["fact_id"]: item for item in listed}
    assert by_id[observed_id]["epistemic_state"] == "Observed"
    assert by_id[supported_id]["epistemic_state"] == "Supported"
    assert by_id[validated_id]["epistemic_state"] == "Validated"

    restored_note = client.get(f"/console/notes/{note_id}")
    assert restored_note.status_code == 200

    return {
        "fact_ids": {
            "observed": observed_id,
            "supported": supported_id,
            "validated": validated_id,
            "invalidated": invalidated_id,
        },
        "note_id": note_id,
        "facts_by_id": {
            fid: {
                "claim": item["claim"],
                "epistemic_state": item["epistemic_state"],
                "confidence": item["confidence"],
                "source": item["source"],
            }
            for fid, item in by_id.items()
        },
        "note": {
            "note_id": note_id,
            "title": restored_note.json()["title"],
            "content": restored_note.json()["content"],
            "tags": restored_note.json()["tags"],
        },
        "facts_total": facts.json()["total"],
    }


def _api_state(client, seed: dict[str, object]) -> dict[str, object]:
    facts = client.get("/facts", params={"limit": 100})
    assert facts.status_code == 200, facts.text
    listed = facts.json()["facts"]
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
    note = client.get(f"/console/notes/{note_id}")
    assert note.status_code == 200, note.text
    validated_id = str(seed["fact_ids"]["validated"])  # type: ignore[index]
    got = client.get(f"/facts/{validated_id}")
    assert got.status_code == 200
    return {
        "facts_total": facts.json()["total"],
        "facts_by_id": by_id,
        "note": {
            "note_id": note.json()["note_id"],
            "title": note.json()["title"],
            "content": note.json()["content"],
            "tags": note.json()["tags"],
        },
        "validated_state": got.json()["epistemic_state"],
    }


def _run_drill(tmp_path: Path, monkeypatch, nonce: str) -> dict[str, object]:
    live = tmp_path / f"live-{nonce}"
    archive = tmp_path / f"velantrim-prod-{nonce}.tar.gz"
    verify_dir = tmp_path / f"verify-{nonce}"
    restored = tmp_path / f"restored-{nonce}"
    started = time.monotonic()

    client, srv = _boot_client(monkeypatch, live)
    try:
        with client:
            seed = _seed_diverse_state(client, nonce)
            api_baseline = _api_state(client, seed)
    finally:
        _close_writers(srv)
    helper.checkpoint_sqlite_dir(live)
    _unload_runtime()

    found_files = sorted(
        str(p.relative_to(live)) for p in live.rglob("*") if p.is_file()
    )
    baseline = helper.snapshot_data_dir(live)

    def _present(table: str) -> bool:
        return any(
            int((tables.get(table) or {}).get("count") or 0) > 0
            for tables in baseline["tables"].values()
        )

    assert _present("facts"), found_files
    assert _present("fact_versions"), baseline["tables"]
    assert _present("l0_fact_provenance"), baseline["tables"]
    assert _present("memory_events"), baseline["tables"]
    backup_meta = helper.create_cold_tar(live, archive)
    assert archive.is_file()
    assert backup_meta["size_bytes"] > 0
    verify_meta = helper.verify_archive(archive, verify_dir)
    assert verify_meta["sqlite_integrity"]
    assert all(status == "ok" for status in verify_meta["sqlite_integrity"].values())

    # Живой каталог изолирован от цели restore: распаковка только в пустой path.
    helper.restore_to_fresh_dir(archive, restored)
    pre_boot = helper.snapshot_data_dir(restored)
    helper.compare_snapshots(baseline, pre_boot)

    client2, srv2 = _boot_client(monkeypatch, restored)
    try:
        with client2:
            health = client2.get("/health")
            assert health.status_code == 200, health.text
            api_restored = _api_state(client2, seed)
    finally:
        _close_writers(srv2)
    helper.checkpoint_sqlite_dir(restored)
    _unload_runtime()

    after = helper.snapshot_data_dir(restored)
    helper.compare_snapshots(baseline, after)
    if api_baseline != api_restored:
        raise helper.StateMismatchError(
            "NO_SILENT_PARTIAL_RECOVERY: API state mismatch after restore"
        )

    base_uv = baseline["sqlite_user_versions"]["velantrim.db"]
    verify_uv = verify_meta["sqlite_user_versions"]["velantrim.db"]
    restored_uv = after["sqlite_user_versions"]["velantrim.db"]
    if not (base_uv == verify_uv == restored_uv):
        raise helper.StateMismatchError(
            "NO_SILENT_PARTIAL_RECOVERY: user_version "
            f"baseline={base_uv} backup={verify_uv} restored={restored_uv}"
        )

    duration_s = round(time.monotonic() - started, 3)
    return {
        "backup_meta": backup_meta,
        "verify_meta": {
            "sha256": verify_meta["sha256"],
            "size_bytes": verify_meta["size_bytes"],
            "sqlite_integrity": verify_meta["sqlite_integrity"],
            "sqlite_user_versions": verify_meta["sqlite_user_versions"],
            "member_count": len(verify_meta["members"]),
        },
        "baseline_tables": baseline["tables"],
        "restored_tables": after["tables"],
        "audit_chain_durable": baseline["audit_chain_durable"],
        "provenance_l0_durable": True,
        "provenance_chains_present": any(
            bool((tables.get("provenance_chains") or {}).get("present"))
            for tables in baseline["tables"].values()
        ),
        "api_facts_total": api_restored["facts_total"],
        "validated_state": api_restored["validated_state"],
        "sqlite_user_versions": {
            "BASELINE_USER_VERSION": base_uv,
            "BACKUP_VERIFIED_USER_VERSION": verify_uv,
            "RESTORED_USER_VERSION": restored_uv,
        },
        "observed_recovery_duration_s": duration_s,
        "seed": seed,
    }


def test_durability_pins_match_compose_profile():
    compose = _compose_env()
    env = _prod_runtime_env(Path("/tmp/ph2a-unused"))
    for key in DURABILITY_PINS:
        expected = _resolve_compose_value(compose[key])
        assert expected is not None, key
        assert env[key] == expected, f"{key}: {env[key]!r} != {expected!r}"
    assert env["ENABLE_RESPONSE_AUDIT"] == "0"
    assert env["ENABLE_TRUTH_POLICY"] == "0"
    assert env["VELANTRIM_SQLITE_SYNCHRONOUS"] == "FULL"
    assert env["VELANTRIM_VERSION_SNAPSHOTS"] == "true"


def test_ops_doc_documents_fresh_target_restore():
    text = OPS_DOC.read_text(encoding="utf-8")
    assert "tar czf" in text
    assert "tar xzf" in text
    assert "new empty" in text.lower() or "fresh" in text.lower()
    assert "scripts/prod_volume_backup_restore.py" in text
    assert "down -v" in text
    assert "velantrim.db" in text
    assert "user_version" in text
    assert "REFUSE" in text
    assert "driver: !reset" in text
    assert "ORIGINAL_STATE_ISOLATED" in text


def test_restore_to_non_empty_target_fails_loud(tmp_path: Path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "marker.txt").write_text("x", encoding="utf-8")
    archive = tmp_path / "b.tar.gz"
    helper.create_cold_tar(src, archive)
    occupied = tmp_path / "occupied"
    occupied.mkdir()
    (occupied / "keep.txt").write_text("no-clobber", encoding="utf-8")
    with pytest.raises(helper.RestoreTargetNotEmptyError):
        helper.restore_to_fresh_dir(archive, occupied)
    assert (occupied / "keep.txt").read_text(encoding="utf-8") == "no-clobber"


def test_partial_canonical_loss_is_not_silent(tmp_path: Path):
    src = tmp_path / "src"
    src.mkdir()
    db = src / "velantrim.db"
    conn = sqlite3.connect(str(db))
    conn.execute("CREATE TABLE facts (fact_id TEXT PRIMARY KEY, claim TEXT)")
    conn.execute("INSERT INTO facts VALUES ('a', 'one')")
    conn.execute("INSERT INTO facts VALUES ('b', 'two')")
    conn.commit()
    conn.close()
    baseline = helper.snapshot_data_dir(src)
    archive = tmp_path / "p.tar.gz"
    helper.create_cold_tar(src, archive)
    dest = tmp_path / "dest"
    helper.restore_to_fresh_dir(archive, dest)
    damaged = sqlite3.connect(str(dest / "velantrim.db"))
    damaged.execute("DELETE FROM facts WHERE fact_id = 'b'")
    damaged.commit()
    damaged.close()
    restored = helper.snapshot_data_dir(dest)
    with pytest.raises(helper.StateMismatchError, match="NO_SILENT_PARTIAL_RECOVERY"):
        helper.compare_snapshots(baseline, restored)


def test_cold_tar_restore_to_fresh_recovers_canonical_state(tmp_path: Path, monkeypatch):
    first = _run_drill(tmp_path, monkeypatch, "r1")
    second = _run_drill(tmp_path, monkeypatch, "r2")

    assert first["validated_state"] == "Validated"
    assert second["validated_state"] == "Validated"
    assert first["api_facts_total"] == second["api_facts_total"]
    assert first["audit_chain_durable"] is True
    assert second["audit_chain_durable"] is True

    # Response audit в prod-профиле выключен и не заявляется.
    compose = _compose_env()
    assert _resolve_compose_value(compose["ENABLE_RESPONSE_AUDIT"]) == "0"

    leftover_archives = list(REPO_ROOT.glob("velantrim-prod-*.tar.gz"))
    assert leftover_archives == []
    assert first["observed_recovery_duration_s"] >= 0
    assert second["observed_recovery_duration_s"] >= 0
    assert first.get("provenance_l0_durable") is True
    assert first["sqlite_user_versions"]["BASELINE_USER_VERSION"] == (
        first["sqlite_user_versions"]["BACKUP_VERIFIED_USER_VERSION"]
    )
    assert first["sqlite_user_versions"]["BACKUP_VERIFIED_USER_VERSION"] == (
        first["sqlite_user_versions"]["RESTORED_USER_VERSION"]
    )
    assert second["sqlite_user_versions"]["BASELINE_USER_VERSION"] == (
        second["sqlite_user_versions"]["RESTORED_USER_VERSION"]
    )


def _write_member_archive(path: Path, name: str, payload: bytes, *, tar_type: bytes | None = None, linkname: str | None = None) -> None:
    with tarfile.open(path, "w:gz") as tf:
        info = tarfile.TarInfo(name=name)
        if tar_type is not None:
            info.type = tar_type
        if linkname is not None:
            info.linkname = linkname
            info.size = 0
            tf.addfile(info)
            return
        info.size = len(payload)
        tf.addfile(info, io.BytesIO(payload))


def test_archive_without_required_canonical_db_fails_loud(tmp_path: Path):
    src = tmp_path / "src"
    src.mkdir()
    extra = sqlite3.connect(str(src / "ngram.db"))
    extra.execute("CREATE TABLE t (x INTEGER)")
    extra.execute("INSERT INTO t VALUES (1)")
    extra.commit()
    extra.close()
    (src / "readme.txt").write_text("not canon", encoding="utf-8")
    archive = tmp_path / "archive_without_required_canonical_db.tar.gz"
    helper.create_cold_tar(src, archive)
    with pytest.raises(helper.BackupVerificationError, match="velantrim.db"):
        helper.verify_archive(archive)
    rc = helper.main(["verify", "--archive", str(archive)])
    assert rc != 0


def test_tar_member_parent_escape_is_refused(tmp_path: Path):
    archive = tmp_path / "escape.tar.gz"
    _write_member_archive(archive, "../escape.txt", b"nope")
    dest = tmp_path / "dest"
    dest.mkdir()
    with pytest.raises(helper.UnsafeArchiveMemberError, match="REFUSE"):
        helper.restore_to_fresh_dir(archive, dest)
    assert list(dest.iterdir()) == []


def test_tar_member_absolute_path_is_refused(tmp_path: Path):
    archive = tmp_path / "absolute.tar.gz"
    _write_member_archive(archive, "/tmp/ph2a-absolute.txt", b"nope")
    dest = tmp_path / "dest"
    dest.mkdir()
    with pytest.raises(helper.UnsafeArchiveMemberError, match="REFUSE"):
        helper.restore_to_fresh_dir(archive, dest)
    assert list(dest.iterdir()) == []


def test_tar_symlink_escape_is_refused(tmp_path: Path):
    archive = tmp_path / "symlink.tar.gz"
    _write_member_archive(
        archive,
        "escape_link",
        b"",
        tar_type=tarfile.SYMTYPE,
        linkname="../outside",
    )
    dest = tmp_path / "dest"
    dest.mkdir()
    with pytest.raises(helper.UnsafeArchiveMemberError, match="REFUSE"):
        helper.restore_to_fresh_dir(archive, dest)
    assert list(dest.iterdir()) == []


def test_docker_drill_command_is_registered():
    parser = helper.build_parser()
    args = parser.parse_args(
        ["docker-drill", "--compose-file", "docker-compose.prod.yml"]
    )
    assert args.command == "docker-drill"


def test_synthetic_prod_env_does_not_persist_api_key(tmp_path: Path):
    path = tmp_path / "ph2a.env"
    helper._write_synthetic_prod_env(path, 18082)
    text = path.read_text(encoding="utf-8")
    assert "VELANTRIM_API_KEY" not in text
    assert "VELANTRIM_PUBLIC_PORT=18082" in text


def test_restore_override_resets_volume_driver(tmp_path: Path):
    path = tmp_path / "docker-compose.restore.yml"
    helper._write_restore_override(path, "ph2a_restore_vol")
    text = path.read_text(encoding="utf-8")
    assert "driver: !reset null" in text
    assert "external: true" in text
    assert "name: ph2a_restore_vol" in text
    assert "driver: local" not in text


def test_post_restore_mount_identity_is_fail_loud():
    helper._assert_post_restore_mount_identity("orig_vol", "restore_vol", "restore_vol")
    with pytest.raises(helper.StateMismatchError, match="ORIGINAL_STATE_ISOLATED"):
        helper._assert_post_restore_mount_identity("orig_vol", "restore_vol", "orig_vol")
    with pytest.raises(helper.StateMismatchError, match="ORIGINAL_STATE_ISOLATED"):
        helper._assert_post_restore_mount_identity("orig_vol", "restore_vol", "other_vol")
