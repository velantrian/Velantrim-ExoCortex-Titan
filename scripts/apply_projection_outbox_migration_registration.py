from __future__ import annotations

from pathlib import Path

PATH = Path("scripts/apply_migrations.py")
OLD = '''    (19, BASE_DIR / "migrations" / "019_suggested_edges.sql"),
]'''
NEW = '''    (19, BASE_DIR / "migrations" / "019_suggested_edges.sql"),
    (20, BASE_DIR / "migrations" / "020_projection_outbox.sql"),
]'''

text = PATH.read_text(encoding="utf-8")
if text.count(OLD) != 1:
    raise SystemExit("expected exactly one migration-list anchor")
PATH.write_text(text.replace(OLD, NEW, 1), encoding="utf-8")
