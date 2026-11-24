"""Record installed distribution license metadata; missing data is explicit, not approval."""
from __future__ import annotations

import argparse
import json
from importlib.metadata import distributions
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    records = []
    for distribution in distributions():
        meta = distribution.metadata
        classifiers = [item for item in meta.get_all("Classifier", []) if item.startswith("License ::")]
        expression = meta.get("License-Expression")
        declared = meta.get("License")
        records.append({
            "name": meta.get("Name", "UNKNOWN"), "version": distribution.version,
            "license_expression": expression, "declared_license": declared,
            "license_classifiers": classifiers,
            "metadata_status": "DECLARED" if expression or declared or classifiers else "MISSING",
        })
    report = {"scope": "installed-distributions", "legal_compatibility_certified": False,
              "packages": sorted(records, key=lambda item: item["name"].lower())}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
