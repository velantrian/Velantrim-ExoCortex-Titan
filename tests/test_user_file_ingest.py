from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parents[1] / "scripts" / "ingest_file.py"
spec = importlib.util.spec_from_file_location("ingest_file", SCRIPT)
assert spec and spec.loader
ingest = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ingest)


class FakeParsed:
    file_type = "text"
    extraction_method = "test-parser"
    extracted_text = "alpha beta gamma"


class FakeResponse:
    def __init__(self, payload: dict):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def test_read_env_skips_comments_and_reads_server_key(tmp_path):
    path = tmp_path / ".env"
    path.write_text(
        "# comment\nVELANTRIM_API_KEY=test-secret\nOTHER='value'\n",
        encoding="utf-8",
    )
    assert ingest.read_env(path) == {
        "VELANTRIM_API_KEY": "test-secret",
        "OTHER": "value",
    }


def test_split_text_is_bounded_and_lossless():
    text = "abcdefghij"
    assert ingest.split_text(text, limit=4) == ["abcd", "efgh", "ij"]
    assert "".join(ingest.split_text(text, limit=4)) == text


def test_safe_source_name_removes_control_characters(tmp_path):
    path = tmp_path / "report ] ignore\nthis.pdf"
    source = ingest.safe_source_name(path)
    assert source.startswith("file:")
    assert "\n" not in source
    assert "]" not in source


def test_ingest_file_reuses_canonical_local_ingest_api(tmp_path, monkeypatch):
    path = tmp_path / "notes.txt"
    path.write_text("placeholder", encoding="utf-8")
    monkeypatch.setattr(ingest, "parse_file", lambda _: FakeParsed())

    captured = []

    def opener(request, timeout):
        captured.append((request, timeout))
        return FakeResponse({"stored": 1})

    result = ingest.ingest_file(
        path,
        base_url="http://127.0.0.1:8755",
        api_key="server-key",
        opener=opener,
    )

    assert result["requests"] == 1
    assert result["file_type"] == "text"
    request, timeout = captured[0]
    assert request.full_url == "http://127.0.0.1:8755/ingest/text"
    assert request.get_header("X-api-key") == "server-key"
    payload = json.loads(request.data.decode("utf-8"))
    assert payload["text"] == FakeParsed.extracted_text
    assert payload["source"] == "file:notes.txt"
    assert timeout == 30


def test_ingest_file_requires_server_key(tmp_path, monkeypatch):
    path = tmp_path / "notes.txt"
    path.write_text("placeholder", encoding="utf-8")
    monkeypatch.setattr(ingest, "parse_file", lambda _: FakeParsed())
    with pytest.raises(ingest.FileIngestError, match="VELANTRIM_API_KEY"):
        ingest.ingest_file(path, base_url="http://127.0.0.1:8755", api_key="")


def test_ingest_file_splits_large_parser_output(tmp_path, monkeypatch):
    path = tmp_path / "large.txt"
    path.write_text("placeholder", encoding="utf-8")

    parsed = FakeParsed()
    parsed.extracted_text = "x" * (ingest.REQUEST_CHUNK_CHARS + 5)
    monkeypatch.setattr(ingest, "parse_file", lambda _: parsed)

    sources = []

    def opener(request, timeout):
        payload = json.loads(request.data.decode("utf-8"))
        sources.append(payload["source"])
        return FakeResponse({"stored": 1})

    result = ingest.ingest_file(
        path,
        base_url="http://127.0.0.1:8755",
        api_key="server-key",
        opener=opener,
    )
    assert result["requests"] == 2
    assert sources == ["file:large.txt:part-1-of-2", "file:large.txt:part-2-of-2"]


def test_bootstrap_runtime_installs_existing_parser_extra():
    bootstrap_path = Path(__file__).parents[1] / "scripts" / "bootstrap_titan.py"
    bootstrap_spec = importlib.util.spec_from_file_location("bootstrap_stage5", bootstrap_path)
    assert bootstrap_spec and bootstrap_spec.loader
    bootstrap = importlib.util.module_from_spec(bootstrap_spec)
    bootstrap_spec.loader.exec_module(bootstrap)

    calls = []

    def runner(command, **kwargs):
        calls.append((command, kwargs))

        class Result:
            returncode = 0

        return Result()

    bootstrap.install_server_dependencies(Path("/tmp/titan"), Path("/tmp/python"), runner=runner)
    assert calls
    command = calls[0][0]
    assert command[-1].endswith("[server,parsers]")
