from __future__ import annotations

from pathlib import Path


PATH = Path("core/memory.py")


def _replace_once(source: str, old: str, new: str, *, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one exact match, found {count}")
    return source.replace(old, new, 1)


source = PATH.read_text(encoding="utf-8")

source = _replace_once(
    source,
    'SQLITE_PATH = os.getenv("VELANTRIM_DB_PATH", "./data/velantrim.db")\n\n'
    '# GDPR Art. 17 batch erasure',
    'SQLITE_PATH = os.getenv("VELANTRIM_DB_PATH", "./data/velantrim.db")\n'
    '_SQLITE_BUSY_TIMEOUT_DEFAULT_MS = 30_000\n'
    '_SQLITE_BUSY_TIMEOUT_MAX_MS = 120_000\n\n\n'
    'def _sqlite_busy_timeout_ms() -> int:\n'
    '    """Resolve one bounded SQLite lock-wait budget per store instance.\n\n'
    '    Invalid/operator-hostile values retain the historical 30-second\n'
    '    default. The returned integer is safe for both sqlite3.connect() and\n'
    '    PRAGMA busy_timeout interpolation.\n'
    '    """\n'
    '    raw = os.getenv(\n'
    '        "VELANTRIM_SQLITE_BUSY_TIMEOUT_MS",\n'
    '        str(_SQLITE_BUSY_TIMEOUT_DEFAULT_MS),\n'
    '    )\n'
    '    try:\n'
    '        value = int(raw.strip())\n'
    '    except (AttributeError, ValueError):\n'
    '        return _SQLITE_BUSY_TIMEOUT_DEFAULT_MS\n'
    '    if not 1 <= value <= _SQLITE_BUSY_TIMEOUT_MAX_MS:\n'
    '        return _SQLITE_BUSY_TIMEOUT_DEFAULT_MS\n'
    '    return value\n\n\n'
    '# GDPR Art. 17 batch erasure',
    label="busy-timeout resolver",
)

source = _replace_once(
    source,
    '        self._closed = False\n'
    '        # Одно WAL-соединение + RLock: исключает deadlock пула из 3 conn.\n',
    '        self._closed = False\n'
    '        self._busy_timeout_ms = _sqlite_busy_timeout_ms()\n'
    '        # Одно WAL-соединение + RLock: исключает deadlock пула из 3 conn.\n',
    label="store timeout binding",
)

connect_old = (
    '                    self.db_path, timeout=30.0, check_same_thread=False\n'
)
connect_new = (
    '                    self.db_path,\n'
    '                    timeout=self._busy_timeout_ms / 1000.0,\n'
    '                    check_same_thread=False,\n'
)
if source.count(connect_old) != 2:
    raise SystemExit(
        f"sqlite connect timeout: expected two exact matches, found {source.count(connect_old)}"
    )
source = source.replace(connect_old, connect_new)

source = _replace_once(
    source,
    '            conn.execute("PRAGMA busy_timeout = 30000")\n',
    '            conn.execute(f"PRAGMA busy_timeout = {self._busy_timeout_ms}")\n',
    label="busy_timeout pragma",
)

PATH.write_text(source, encoding="utf-8")
