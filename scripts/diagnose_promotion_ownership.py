from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEST_PATH = ROOT / "tests" / "test_promotion_ownership_guard.py"
OUTPUT = ROOT / "diagnostics" / "promotion-ownership-actual.txt"

spec = importlib.util.spec_from_file_location("promotion_ownership_guard", TEST_PATH)
if spec is None or spec.loader is None:
    raise SystemExit("cannot load promotion ownership guard")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

authority_sites, literal_validated_steps = module._scan()

lines = ["AUTHORITY_SITES"]
lines.extend(
    f"{site.path} :: {site.scope} :: {site.callee}"
    for site in sorted(authority_sites)
)
lines.append("")
lines.append("LITERAL_VALIDATED_STEPS")
lines.extend(
    f"{site.path} :: {site.scope} :: {site.callee}"
    for site in sorted(literal_validated_steps)
)
lines.append("")

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text("\n".join(lines), encoding="utf-8")
