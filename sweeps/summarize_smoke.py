"""Print per-config smoke accuracy and the aggregate degeneracy gate from a run dir."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir")
    parser.add_argument("--chance", type=float, default=0.5)
    args = parser.parse_args()
    rows = []
    for path in sorted(Path(args.run_dir).glob("activities*.jsonl")):
        rows.extend(json.loads(line) for line in path.read_text().splitlines() if line.strip())
    ok = [r for r in rows if r["status"] != "failed"]
    degenerate = [r for r in ok if r["status"] == "degenerate"]
    print(f"activities={len(rows)} usable={len(ok)} degenerate={len(degenerate)}/{len(ok)} "
          f"({len(degenerate) / len(ok) if ok else 1:.1%})")
    for row in rows:
        recipe = row["recipe"]
        print(f"{row['activity_id']} status={row['status']} accuracy={row['accuracy']} "
              f"family={recipe.get('family')} task={recipe.get('task')} model={recipe.get('model')}")
    passed = bool(ok) and len(degenerate) / len(ok) < 0.5 and any((r["accuracy"] or 0) > args.chance for r in ok)
    print(f"gate={'PASS' if passed else 'FAIL'} (<50% degenerate and accuracy > {args.chance:g})")


if __name__ == "__main__":
    main()
