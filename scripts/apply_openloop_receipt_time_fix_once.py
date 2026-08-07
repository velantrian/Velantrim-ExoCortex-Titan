"""One-shot exact fixture correction for OpenLoop source-binding chronology."""

from pathlib import Path


path = Path("tests/test_continuity_open_loop_source_adapter.py")
text = path.read_text(encoding="utf-8")
old = '        "issued_at": _NOW - timedelta(minutes=1),\n'
new = '        "issued_at": result.as_of,\n'
if text.count(old) != 1:
    raise SystemExit(f"expected one issued_at fixture line, found {text.count(old)}")
path.write_text(text.replace(old, new), encoding="utf-8")
