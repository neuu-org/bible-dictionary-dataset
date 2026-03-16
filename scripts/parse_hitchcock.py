#!/usr/bin/env python3
"""
parse_hitchcock.py

Parses Hitchcock's Bible Names Dictionary from CCEL ThML XML.
Uses proper ThML <glossary>/<term>/<def> structure.

Output: data/02_sources/hitchcock/ (a.json ... z.json + _index.json)

Usage:
    python scripts/parse_hitchcock.py
    python scripts/parse_hitchcock.py --dry-run
"""

import argparse
import json
import re
import unicodedata
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
XML_PATH = REPO_ROOT / "data" / "00_raw" / "ccel" / "xml" / "hitchcock_bible_names.xml"
OUTPUT_DIR = REPO_ROOT / "data" / "02_sources" / "hitchcock"
SOURCE_CODE = "HIT"


def parse_hitchcock(xml_path: Path) -> dict:
    """Parse Hitchcock Bible Names from ThML glossary format."""
    print(f"Parsing {xml_path.name} ({xml_path.stat().st_size / 1024:.0f} KB)...")

    with open(xml_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    root = ET.fromstring(content)
    entries = {}

    # Find all glossary sections
    glossaries = list(root.iter("glossary"))
    print(f"  Glossary sections: {len(glossaries)}")

    for glossary in glossaries:
        # Iterate term/def pairs
        terms = list(glossary.iter("term"))
        defs = list(glossary.iter("def"))

        for term_elem, def_elem in zip(terms, defs):
            name = "".join(term_elem.itertext()).strip()
            meaning = "".join(def_elem.itertext()).strip()

            if not name or not meaning:
                continue

            term_key = name.upper()
            slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")

            entries[term_key] = {
                "name": name,
                "slug": slug,
                "definitions": [{"source": SOURCE_CODE, "text": meaning}],
                "scripture_refs": [],
                "sources": [SOURCE_CODE],
            }

    print(f"  Entries parsed: {len(entries)}")
    return entries


def save_by_letter(entries: dict, output_dir: Path, dry_run: bool):
    """Save entries by first letter."""
    by_letter = defaultdict(dict)
    for term, data in entries.items():
        letter = term[0].upper() if term and term[0].isalpha() else "_"
        by_letter[letter][term] = data

    total_entries = 0
    for letter, letter_entries in sorted(by_letter.items()):
        print(f"  {letter}: {len(letter_entries)} entries")
        total_entries += len(letter_entries)

        if not dry_run:
            output_dir.mkdir(parents=True, exist_ok=True)
            with open(output_dir / f"{letter.lower()}.json", "w", encoding="utf-8") as f:
                json.dump(dict(sorted(letter_entries.items())), f, indent=2, ensure_ascii=False)

    index = {
        "total_entries": total_entries,
        "total_refs": 0,
        "source": SOURCE_CODE,
        "source_name": "Hitchcock's Bible Names Dictionary",
        "author": "Roswell D. Hitchcock",
        "published": "1869",
    }

    if not dry_run:
        with open(output_dir / "_index.json", "w", encoding="utf-8") as f:
            json.dump(index, f, indent=2, ensure_ascii=False)

    return total_entries


def main():
    parser = argparse.ArgumentParser(description="Parse Hitchcock's Bible Names Dictionary")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    print("=" * 60)
    print("HITCHCOCK BIBLE NAMES PARSER")
    print("=" * 60)

    entries = parse_hitchcock(XML_PATH)

    print(f"\nSaving to {OUTPUT_DIR}/...")
    total = save_by_letter(entries, OUTPUT_DIR, args.dry_run)

    print(f"\n{'='*60}")
    print(f"Total: {total} entries")
    if args.dry_run:
        print("(DRY RUN)")

    # Samples
    for term in ["AARON", "MOSES", "JERUSALEM", "ADAM", "EVE"]:
        if term in entries:
            print(f"\n  {term}: {entries[term]['definitions'][0]['text']}")


if __name__ == "__main__":
    main()
