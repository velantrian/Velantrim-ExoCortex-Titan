from __future__ import annotations

import sqlite3

import core.provenance_chain as provenance_module
from core.provenance_chain import ProvenanceChain


def test_verify_accepts_a_successfully_read_empty_chain(tmp_path) -> None:
    chain = ProvenanceChain(str(tmp_path / "provenance.db"))

    assert chain.verify("missing-fact") == (True, "empty_chain")


def test_verify_fails_closed_when_database_read_fails(tmp_path, monkeypatch) -> None:
    chain = ProvenanceChain(str(tmp_path / "provenance.db"))

    def fail_connect(*_args, **_kwargs):
        raise sqlite3.OperationalError("disk I/O error")

    monkeypatch.setattr(provenance_module.sqlite3, "connect", fail_connect)

    assert chain.verify("fact-1") == (False, "read_error")


def test_verify_fails_closed_when_event_payload_cannot_be_decoded(tmp_path) -> None:
    db_path = tmp_path / "provenance.db"
    chain = ProvenanceChain(str(db_path))
    appended, _ = chain.append("fact-1", event_type="fact_created")
    assert appended

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "UPDATE provenance_chains SET payload_json = ? WHERE fact_id = ?",
            ("{malformed", "fact-1"),
        )

    # Keep the legacy list API's historical fallback, but never use it to verify.
    assert chain.get_chain("fact-1") == []
    assert chain.verify("fact-1") == (False, "read_error")


def test_verify_fails_closed_when_text_column_contains_blob(tmp_path) -> None:
    db_path = tmp_path / "provenance.db"
    chain = ProvenanceChain(str(db_path))
    appended, _ = chain.append("fact-1", event_type="fact_created")
    assert appended

    with sqlite3.connect(db_path) as conn:
        schema = {
            row[1]: row[2]
            for row in conn.execute("PRAGMA table_info(provenance_chains)")
        }
        assert schema["event_type"] == "TEXT"
        conn.execute(
            "UPDATE provenance_chains SET event_type = CAST(event_type AS BLOB) "
            "WHERE fact_id = ?",
            ("fact-1",),
        )
        stored_type = conn.execute(
            "SELECT typeof(event_type) FROM provenance_chains WHERE fact_id = ?",
            ("fact-1",),
        ).fetchone()[0]

    assert stored_type == "blob"
    assert chain.verify("fact-1") == (False, "read_error")
