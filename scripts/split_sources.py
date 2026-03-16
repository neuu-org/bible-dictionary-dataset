#!/usr/bin/env python3
"""
split_sources.py

Splits the unified dictionary (02_unified) into separate source files
for Easton's Bible Dictionary and Smith's Bible Dictionary.

Reads from data/01_parsed/, writes to data/02_sources/easton/ and data/02_sources/smith/.

Each source gets only its own definitions, organized by letter (a.json ... z.json).

Usage:
    python scripts/split_sources.py
    python scripts/split_sources.py --dry-run
"""

import argparse
import json
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
UNIFIED_DIR = REPO_ROOT / "data" / "01_parsed"
SOURCES_DIR = REPO_ROOT / "data" / "02_sources"


def split():
    parser = argparse.ArgumentParser(description="Split unified dictionary by source")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    easton = defaultdict(dict)
    smith = defaultdict(dict)

    total_eas = 0
    total_smi = 0
    total_refs_eas = 0
    total_refs_smi = 0

    # Read all unified files
    for f in sorted(UNIFIED_DIR.glob("*.json")):
        if f.name == "_index.json":
            continue

        with open(f, encoding="utf-8") as fh:
            data = json.load(fh)

        letter = f.stem  # a, b, c, ...

        for term, entry in data.items():
            sources = entry.get("sources", [])
            definitions = entry.get("definitions", [])
            refs = entry.get("scripture_refs", [])

            if "EAS" in sources:
                eas_defs = [d for d in definitions if d.get("source") == "EAS"]
                easton[letter][term] = {
                    "name": entry.get("name", term),
                    "slug": entry.get("slug", ""),
                    "definitions": eas_defs,
                    "scripture_refs": refs,
                }
                total_eas += 1
                total_refs_eas += len(refs)

            if "SMI" in sources:
                smi_defs = [d for d in definitions if d.get("source") == "SMI"]
                smith[letter][term] = {
                    "name": entry.get("name", term),
                    "slug": entry.get("slug", ""),
                    "definitions": smi_defs,
                    "scripture_refs": refs,
                }
                total_smi += 1
                total_refs_smi += len(refs)

    print(f"Easton: {total_eas} entries, {total_refs_eas} refs")
    print(f"Smith:  {total_smi} entries, {total_refs_smi} refs")

    if args.dry_run:
        print("(DRY RUN — nothing saved)")
        return

    # Save Easton
    eas_dir = SOURCES_DIR / "easton"
    eas_dir.mkdir(parents=True, exist_ok=True)
    for letter, entries in sorted(easton.items()):
        with open(eas_dir / f"{letter}.json", "w", encoding="utf-8") as fh:
            json.dump(entries, fh, ensure_ascii=False, indent=2)

    eas_index = {"total_entries": total_eas, "total_refs": total_refs_eas, "source": "EAS", "source_name": "Easton's Bible Dictionary", "published": "1897"}
    with open(eas_dir / "_index.json", "w", encoding="utf-8") as fh:
        json.dump(eas_index, fh, ensure_ascii=False, indent=2)

    # Save Smith
    smi_dir = SOURCES_DIR / "smith"
    smi_dir.mkdir(parents=True, exist_ok=True)
    for letter, entries in sorted(smith.items()):
        with open(smi_dir / f"{letter}.json", "w", encoding="utf-8") as fh:
            json.dump(entries, fh, ensure_ascii=False, indent=2)

    smi_index = {"total_entries": total_smi, "total_refs": total_refs_smi, "source": "SMI", "source_name": "Smith's Bible Dictionary", "published": "1863"}
    with open(smi_dir / "_index.json", "w", encoding="utf-8") as fh:
        json.dump(smi_index, fh, ensure_ascii=False, indent=2)

    print(f"\nSaved to {SOURCES_DIR}/")


if __name__ == "__main__":
    split()
