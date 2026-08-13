from pathlib import Path


def test_docker_base_is_digest_pinned() -> None:
    text = Path("Dockerfile").read_text(encoding="utf-8")
    from_lines = [line for line in text.splitlines() if line.startswith("FROM python:")]
    assert len(from_lines) == 2
    assert all("@sha256:" in line for line in from_lines)
    assert from_lines[0].split(" AS ")[0] == from_lines[1].split(" AS ")[0]
