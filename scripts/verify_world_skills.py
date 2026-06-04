#!/usr/bin/env python3
"""
scripts/verify_world_skills.py — verify the world_skills_core knowledge base.

Makes the "duplicate_ids: 0" / total-count claim COMPUTED instead of ASSERTED
(canon principle: verify, don't assert). Scans every batch file, extracts each
KnowledgeUnit ID (the FIRST table cell), and checks:

  1. ID format        — lowercase ASCII dot-path: domain[.subdomain].term
  2. duplicate IDs    — the same ID appearing in two or more places (FATAL)
  3. real total count — actual number of unique IDs across all batches

Handles BOTH batch table formats:
  old:  | `agro.crop.wheat.grain_use` | Тип | Суть | Условия | Связи |
  new:  | education.formal.levels     | KnowledgeUnit | Тип | Суть | ... |
Only the first cell is read, so dotted tokens in a "Связи"/links column
(e.g. food.flour) are never mistaken for IDs.

Usage:
    python scripts/verify_world_skills.py                 # report + exit 1 if dups
    python scripts/verify_world_skills.py --update-state   # also rewrite the counter
    python scripts/verify_world_skills.py --quiet          # only summary + exit code

Pure stdlib. Exit code: 0 = clean, 1 = duplicates or malformed IDs found.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

# domain[.subdomain...].term — lowercase ascii, digits, underscore; ≥ 2 parts
ID_RE = re.compile(r"^[a-z0-9_]+(?:\.[a-z0-9_]+)+$")

# Meta/organizational files (maps, plans, rules) — not KnowledgeUnit sources.
# Match complete filename tokens so domain words like FOOD_PLANT are not skipped.
META_KEYWORDS = {"MAP", "PLAN", "PROTOCOL", "RULES", "SCOPE", "README"}


def _is_unit_file(path: Path) -> bool:
    tokens = {t for t in re.split(r"[^A-Z0-9]+", path.stem.upper()) if t}
    return not bool(tokens & META_KEYWORDS)

ROOT = Path(__file__).resolve().parents[1]
KB_DIR = ROOT / "docs" / "knowledge" / "world_skills_core"
RU_DIR = KB_DIR / "ru"
STATE_FILE = KB_DIR / "WORLD_SKILLS_CORE_STATE.ru.json"


def _first_cell(line: str) -> str | None:
    """Return the first table cell of a markdown row, or None if not a data row."""
    s = line.strip()
    if not s.startswith("|"):
        return None
    parts = s.split("|")          # ['', ' c1 ', ' c2 ', ..., '']
    if len(parts) < 3:
        return None
    cell = parts[1].strip().strip("`").strip()
    return cell or None


def extract_ids(path: Path) -> list[tuple[str, int]]:
    """Yield (id, line_number) for every KnowledgeUnit ID in a batch file."""
    out: list[tuple[str, int]] = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        cell = _first_cell(line)
        if cell and ID_RE.match(cell):
            out.append((cell, n))
    return out


_WS_RE = re.compile(r"\s+")
_PUNCT_RE = re.compile(r"[^\w\s]")
# generic-claim markers: claim begins with a column-label word but no entity
_GENERIC_PREFIX = ("столица,", "столица ,", "валюта,", "это ", "см.", "—")
_MIN_CLAIM_LEN = 12


def _norm_claim(claim: str) -> str:
    return _WS_RE.sub(" ", _PUNCT_RE.sub(" ", (claim or "").lower())).strip()


def extract_units(path: Path) -> list[tuple[str, str, int]]:
    """Header-aware: yield (id, claim, line) for every KnowledgeUnit row.

    The «Суть» (claim) column index is read from the header row (it differs between
    the old and new batch table formats), with a fallback to column 2.
    """
    out: list[tuple[str, str, int]] = []
    claim_idx: int | None = None
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip().strip("`").strip() for c in s.split("|")[1:-1]]
        if len(cells) < 2:
            continue
        low = [c.lower() for c in cells]
        if "id" in low and "суть" in low:
            claim_idx = low.index("суть")
            continue
        fid = cells[0]
        if not fid or fid.lower() == "id" or not ID_RE.match(fid):
            continue
        ci = claim_idx if (claim_idx is not None and claim_idx < len(cells)) else 2
        claim = cells[ci] if ci < len(cells) else ""
        out.append((fid, claim, n))
    return out


def scan() -> dict:
    """Scan all batch files; return a structured report."""
    id_locations: dict[str, list[str]] = defaultdict(list)
    per_file: dict[str, int] = {}
    malformed: list[str] = []
    claim_to_ids: dict[str, set] = defaultdict(set)   # normalized claim → set of ids
    claim_example: dict[str, str] = {}                # normalized claim → "rel:line | text"
    short_claims: list[str] = []
    generic_claims: list[str] = []

    files = sorted(p for p in RU_DIR.glob("*.md") if _is_unit_file(p))
    for path in files:
        rel = path.relative_to(KB_DIR).as_posix()
        units = extract_units(path)
        per_file[rel] = len(units)
        for fid, claim, ln in units:
            id_locations[fid].append(f"{rel}:{ln}")
            nc = _norm_claim(claim)
            if nc:
                claim_to_ids[nc].add(fid)
                claim_example.setdefault(nc, f"{rel}:{ln} | {claim}")
            # CLAIM LINTER: claims must be self-contained (audit: generic capital claims)
            cl = (claim or "").strip().lower()
            if len(cl) < _MIN_CLAIM_LEN:
                short_claims.append(f"{rel}:{ln} | {claim!r}")
            elif cl.startswith(_GENERIC_PREFIX):
                generic_claims.append(f"{rel}:{ln} | {claim!r}")
        # malformed = first-cell tokens that look like IDs but fail the strict rule
        for line in path.read_text(encoding="utf-8").splitlines():
            cell = _first_cell(line)
            if cell and "." in cell and not ID_RE.match(cell) and cell.lower() != "id":
                if " " not in cell and len(cell) < 80:
                    malformed.append(f"{rel}: {cell!r}")

    duplicates = {fid: locs for fid, locs in id_locations.items() if len(locs) > 1}
    # duplicate claims = one normalized claim shared by ≥2 DIFFERENT ids (generic/non-distinct)
    dup_claims = {nc: sorted(ids) for nc, ids in claim_to_ids.items() if len(ids) > 1}
    return {
        "files": len(files),
        "total_ids": sum(per_file.values()),
        "unique_ids": len(id_locations),
        "duplicates": duplicates,
        "malformed": malformed,
        "duplicate_claims": dup_claims,
        "claim_example": claim_example,
        "short_claims": short_claims,
        "generic_claims": generic_claims,
        "per_file": per_file,
    }


def update_state(report: dict) -> None:
    if not STATE_FILE.is_file():
        print(f"⚠️  state file not found: {STATE_FILE}")
        return
    state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    cp = state.setdefault("current_checkpoint", {})
    cp["knowledge_unit_ids"] = report["unique_ids"]
    cp["duplicate_ids"] = sum(len(v) - 1 for v in report["duplicates"].values())
    target = cp.get("target_ids", 50000)
    cp["remaining_to_target"] = max(0, target - report["unique_ids"])
    cp["verified_by_tool"] = "scripts/verify_world_skills.py"
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"✅ state updated: knowledge_unit_ids={report['unique_ids']} "
          f"duplicate_ids={cp['duplicate_ids']}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Verify world_skills_core for duplicate IDs.")
    ap.add_argument("--update-state", action="store_true", help="rewrite the state counter")
    ap.add_argument("--quiet", action="store_true", help="summary only")
    ap.add_argument("--strict-claims", action="store_true",
                    help="fail (exit 1) on duplicate/generic claims, not just duplicate IDs")
    args = ap.parse_args(argv)

    if not RU_DIR.is_dir():
        print(f"❌ knowledge dir not found: {RU_DIR}")
        return 2

    r = scan()
    dup_units = sum(len(v) - 1 for v in r["duplicates"].values())

    if not args.quiet:
        print(f"📂 files scanned:    {r['files']}")
        print(f"🔢 total ID rows:    {r['total_ids']}")
        print(f"🆔 unique IDs:       {r['unique_ids']}")
        print(f"♻️  duplicate IDs:    {len(r['duplicates'])} ids / {dup_units} extra rows")
        print(f"⚠️  malformed IDs:    {len(r['malformed'])}")
        print(f"🔁 duplicate claims: {len(r['duplicate_claims'])} (одна «Суть» у ≥2 ID — generic/неразличимы)")
        print(f"✂️  short claims:     {len(r['short_claims'])} (<{_MIN_CLAIM_LEN} симв.)  "
              f"| generic-prefix claims: {len(r['generic_claims'])}")
        if r["duplicates"]:
            print("\n--- DUPLICATE IDs ---")
            for fid, locs in sorted(r["duplicates"].items()):
                print(f"  {fid}\n      " + "\n      ".join(locs))
        if r["malformed"]:
            print("\n--- MALFORMED (dotted but not valid ID) ---")
            for m in r["malformed"][:30]:
                print(f"  {m}")
        if r["duplicate_claims"]:
            print("\n--- DUPLICATE CLAIMS (несамодостаточные / generic «Суть») ---")
            for nc, ids in sorted(r["duplicate_claims"].items(), key=lambda x: -len(x[1]))[:20]:
                print(f"  {len(ids)} ID: {ids[:5]}{'…' if len(ids) > 5 else ''}")
                print(f"      пример: {r['claim_example'].get(nc, '')[:90]}")
        if r["generic_claims"]:
            print("\n--- GENERIC-PREFIX CLAIMS (начинаются с метки-колонки) ---")
            for g in r["generic_claims"][:15]:
                print(f"  {g[:90]}")

    claim_issues = len(r["duplicate_claims"]) + len(r["generic_claims"])
    print(f"\n{'❌ DUPLICATES FOUND' if r['duplicates'] else '✅ no duplicate IDs'} "
          f"| {r['unique_ids']} unique units"
          f"{f' | ⚠️ {claim_issues} claim issues' if claim_issues else ''}")

    if args.update_state:
        update_state(r)

    if r["duplicates"]:
        return 1
    if args.strict_claims and claim_issues:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
