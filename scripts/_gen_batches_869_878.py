#!/usr/bin/env python
"""Fail-closed tombstone for the retired 869-878 batch generator.

The historical source is preserved verbatim at:
    docs/history/generators/_gen_batches_869_878.py.txt

Why this path is disabled:
- batch 869 has legitimate provenance in the historical generator;
- the same historical script also writes generic batches 870-878;
- current accepted 870+ assets were produced by the richer successor generator;
- replaying this legacy script could therefore overwrite current knowledge assets.

This compatibility path intentionally performs no writes.  Historical provenance is
preserved, but replay is not authorized by the existence of the old script.
"""

from __future__ import annotations

import sys


ARCHIVE_PATH = "docs/history/generators/_gen_batches_869_878.py.txt"


def main() -> int:
    print(
        "DISABLED: legacy batch generator is provenance-only and unsafe to replay as-is. "
        f"Historical source: {ARCHIVE_PATH}",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
