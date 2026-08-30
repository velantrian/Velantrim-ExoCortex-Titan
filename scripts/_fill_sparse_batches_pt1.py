#!/usr/bin/env python
"""Disabled legacy sparse-batch patcher.

The original one-shot writer is preserved verbatim as provenance under
``docs/history/generators/_fill_sparse_batches_pt1.py.txt``.

This active path intentionally fails closed because the historical patcher
blindly appends its stored facts to mutable corpus files without proving that
the original sparse-input preconditions still hold or that IDs are absent.
"""

from __future__ import annotations

import sys


ARCHIVE_PATH = "docs/history/generators/_fill_sparse_batches_pt1.py.txt"


def main() -> int:
    print(
        "DISABLED: legacy sparse-batch patcher is provenance-only and unsafe "
        "to replay as-is. Historical source: " + ARCHIVE_PATH,
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
