#!/usr/bin/env python3
"""Validate the reclassification template."""
import argparse
import csv
import sys
from pathlib import Path

VALID_CLOSURE_TYPES = {
    "open",
    "maritime_ban",
    "land_isolation",
    "tech_network_exclusion",
    "bloc",
    "policy_closure",
    "patron_open",
    "uncertain",
    "",
}
VALID_CONFIDENCE = {"high", "medium", "low", ""}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", action="store_true", help="print summary")
    args = parser.parse_args()

    project_dir = Path(__file__).resolve().parent.parent
    template_path = project_dir / "data" / "classification_template.csv"
    if not template_path.exists():
        print(f"Error: {template_path} not found", file=sys.stderr)
        sys.exit(1)

    errors = []
    valid_count = 0
    total = 0
    confidence_counts = {"high": 0, "medium": 0, "low": 0, "": 0}
    closure_counts = {}

    with template_path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=2):
            total += 1
            entity = row.get("entity", "")
            rtype = row.get("rater_closure_type", "").strip()
            conf = row.get("rater_confidence", "").strip().lower()
            url = (row.get("rater_source_url") or "").strip()
            quote = (row.get("rater_source_quote") or "").strip()

            if rtype not in VALID_CLOSURE_TYPES:
                errors.append(f"Row {i} ({entity}): invalid rater_closure_type '{rtype}'")
            if conf not in VALID_CONFIDENCE:
                errors.append(f"Row {i} ({entity}): invalid rater_confidence '{conf}'")

            if rtype and rtype not in {"", "uncertain"}:
                if not conf:
                    errors.append(f"Row {i} ({entity}): rater_closure_type set but confidence missing")
                if not url:
                    errors.append(f"Row {i} ({entity}): rater_closure_type set but source URL missing")
                if not quote:
                    errors.append(f"Row {i} ({entity}): rater_closure_type set but source quote missing")

            if rtype in {"open", "maritime_ban", "land_isolation", "tech_network_exclusion", "bloc", "policy_closure", "patron_open"} and conf and url and quote:
                valid_count += 1

            confidence_counts[conf] = confidence_counts.get(conf, 0) + 1
            closure_counts[rtype] = closure_counts.get(rtype, 0) + 1

    if errors:
        print("Validation errors:")
        for e in errors:
            print(f"  - {e}")
    else:
        print("No validation errors.")

    print(f"\nTotal cases: {total}")
    print(f"Fully coded cases: {valid_count} / {total}")
    if args.summary:
        print("\nConfidence distribution:")
        for k, v in confidence_counts.items():
            label = k if k else "missing"
            print(f"  {label}: {v}")
        print("\nClosure-type distribution:")
        for k, v in closure_counts.items():
            label = k if k else "missing"
            print(f"  {label}: {v}")

    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
