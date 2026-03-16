#!/usr/bin/env python3
"""
parse_schaff.py

Parses Schaff's Dictionary of the Bible from CCEL paragraph JSON.
Source: extracted from jncraton/ccel-paragraphs parquets.

The Schaff dictionary has paragraphs where article entries are identified
by terms in UPPERCASE or with specific patterns at the start of paragraphs.

Output: data/02_sources/schaff/ (a.json ... z.json + _index.json)

Usage:
    python scripts/parse_schaff.py
    python scripts/parse_schaff.py --dry-run
"""

import argparse
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).parent.parent
# Source: extracted JSON from jncraton/ccel-paragraphs parquets.
# This file is not stored in the repo; it must be produced by extracting
# Schaff paragraphs from the CCEL parquet dataset before running this script.
RAW_JSON = REPO_ROOT / "data" / "00_raw" / "ccel" / "json" / "a_dictionary_of_the_bible.json"
OUTPUT_DIR = REPO_ROOT / "data" / "02_sources" / "schaff"
SOURCE_CODE = "SCH"

# Skip paragraphs that are preface/maps/index (by ID pattern)
SKIP_SECTIONS = {"ii", "iii", "xxxii"}  # preface, maps, index


def normalize_ref(ref_str: str) -> Optional[str]:
    """Convert CCEL paragraph ref format to standard reference.
    Input: 'Bible.asv:Rev.1.8' or 'Rev 1:8'
    Output: 'Revelation 1:8'
    """
    if not ref_str:
        return None

    # Strip Bible.xxx: prefix
    if ":" in ref_str and ref_str.startswith("Bible"):
        ref_str = ref_str.split(":", 1)[1]

    # Parse Book.Chapter.Verse format
    parts = ref_str.split(".")
    if len(parts) >= 3:
        book = parts[0]
        chapter = parts[1]
        verse = parts[2]

        book_map = {
            "Gen": "Genesis", "Exod": "Exodus", "Lev": "Leviticus", "Num": "Numbers",
            "Deut": "Deuteronomy", "Josh": "Joshua", "Judg": "Judges", "Ruth": "Ruth",
            "1Sam": "1 Samuel", "2Sam": "2 Samuel", "1Kgs": "1 Kings", "2Kgs": "2 Kings",
            "1Chr": "1 Chronicles", "2Chr": "2 Chronicles", "Ezra": "Ezra", "Neh": "Nehemiah",
            "Esth": "Esther", "Job": "Job", "Ps": "Psalms", "Prov": "Proverbs",
            "Eccl": "Ecclesiastes", "Song": "Song of Solomon", "Isa": "Isaiah", "Jer": "Jeremiah",
            "Lam": "Lamentations", "Ezek": "Ezekiel", "Dan": "Daniel", "Hos": "Hosea",
            "Joel": "Joel", "Amos": "Amos", "Obad": "Obadiah", "Jonah": "Jonah",
            "Mic": "Micah", "Nah": "Nahum", "Hab": "Habakkuk", "Zeph": "Zephaniah",
            "Hag": "Haggai", "Zech": "Zechariah", "Mal": "Malachi",
            "Matt": "Matthew", "Mark": "Mark", "Luke": "Luke", "John": "John",
            "Acts": "Acts", "Rom": "Romans", "1Cor": "1 Corinthians", "2Cor": "2 Corinthians",
            "Gal": "Galatians", "Eph": "Ephesians", "Phil": "Philippians", "Col": "Colossians",
            "1Thess": "1 Thessalonians", "2Thess": "2 Thessalonians", "1Tim": "1 Timothy",
            "2Tim": "2 Timothy", "Titus": "Titus", "Phlm": "Philemon", "Heb": "Hebrews",
            "Jas": "James", "1Pet": "1 Peter", "2Pet": "2 Peter", "1John": "1 John",
            "2John": "2 John", "3John": "3 John", "Jude": "Jude", "Rev": "Revelation",
            "Ex": "Exodus", "Lv": "Leviticus", "Nm": "Numbers", "Dt": "Deuteronomy",
        }
        full_book = book_map.get(book, book)
        return f"{full_book} {chapter}:{verse}"

    return ref_str


def is_article_start(text: str) -> Optional[str]:
    """Detect if a paragraph starts a new dictionary article.
    Returns the term name if it's an article start, None otherwise.

    Pattern: text starts with UPPERCASE term followed by parenthetical or comma.
    Examples:
        "AHIS'AMACH (brother of support), a Danite..."
        "AARON, the first high priest..."
        "A and O, or ALPHA and OMEGA..."
    """
    if not text or len(text) < 5:
        return None

    # Match: UPPERCASE_WORD(S) followed by ( or ,
    match = re.match(
        r"^([A-Z][A-Z'\-\s]{1,40}?)(?:\s*[\(,]|\.\s)",
        text,
    )
    if match:
        term = match.group(1).strip().rstrip(",.")
        # Must be mostly uppercase
        alpha = [c for c in term if c.isalpha()]
        if alpha and sum(1 for c in alpha if c.isupper()) / len(alpha) > 0.6:
            # Clean up
            term = term.replace("'", "").replace("'", "").strip()
            if len(term) >= 2:
                return term

    return None


def parse_schaff(raw_path: Path) -> dict:
    """Parse Schaff dictionary from CCEL paragraph JSON."""
    print(f"Loading {raw_path.name}...")

    with open(raw_path, encoding="utf-8") as f:
        paragraphs = json.load(f)

    print(f"  Total paragraphs: {len(paragraphs)}")

    entries = {}
    current_term = None
    current_texts = []
    current_refs = []
    skipped = 0

    for row in paragraphs:
        pid = row.get("id", "")
        text = row.get("text", "").strip()
        refs = row.get("refs", [])

        # Skip preface/maps/index sections
        section = pid.split("-")[0].split(".")[-1] if "-" in pid else ""
        # Extract section from id like "ccel/s/schaff/dictionarybible.xml:ii-p1"
        if ":" in pid:
            section_part = pid.split(":")[1].split("-")[0]
            if section_part in SKIP_SECTIONS:
                skipped += 1
                continue

        if not text:
            continue

        # Check if this starts a new article
        term = is_article_start(text)

        if term:
            # Save previous article
            if current_term and current_texts:
                _save_entry(entries, current_term, current_texts, current_refs)

            current_term = term
            current_texts = [text]
            current_refs = []
            for r in refs:
                norm = normalize_ref(r)
                if norm:
                    current_refs.append(norm)
        else:
            # Continue current article
            if current_term:
                current_texts.append(text)
                for r in refs:
                    norm = normalize_ref(r)
                    if norm:
                        current_refs.append(norm)

    # Save last article
    if current_term and current_texts:
        _save_entry(entries, current_term, current_texts, current_refs)

    print(f"  Skipped (preface/index): {skipped}")
    print(f"  Articles found: {len(entries)}")

    return entries


def _save_entry(entries: dict, term: str, texts: list, refs: list):
    """Save a parsed article."""
    term_key = term.upper()
    full_text = " ".join(texts)

    if len(full_text) < 10:
        return

    slug = re.sub(r"[^a-z0-9]+", "-", term.lower()).strip("-")

    # Deduplicate refs
    unique_refs = []
    seen = set()
    for r in refs:
        if r not in seen:
            unique_refs.append({"reference": r, "original": r})
            seen.add(r)

    entries[term_key] = {
        "name": term.title() if term.isupper() else term,
        "slug": slug,
        "definitions": [{"source": SOURCE_CODE, "text": full_text}],
        "scripture_refs": unique_refs,
        "sources": [SOURCE_CODE],
    }


def save_by_letter(entries: dict, output_dir: Path, dry_run: bool):
    """Save by first letter."""
    by_letter = defaultdict(dict)
    for term, data in entries.items():
        letter = term[0].upper() if term and term[0].isalpha() else "_"
        by_letter[letter][term] = data

    total_entries = 0
    total_refs = 0

    for letter, letter_entries in sorted(by_letter.items()):
        refs_count = sum(len(e["scripture_refs"]) for e in letter_entries.values())
        print(f"  {letter}: {len(letter_entries)} entries, {refs_count} refs")
        total_entries += len(letter_entries)
        total_refs += refs_count

        if not dry_run:
            output_dir.mkdir(parents=True, exist_ok=True)
            with open(output_dir / f"{letter.lower()}.json", "w", encoding="utf-8") as f:
                json.dump(dict(sorted(letter_entries.items())), f, indent=2, ensure_ascii=False)

    index = {
        "total_entries": total_entries,
        "total_refs": total_refs,
        "source": SOURCE_CODE,
        "source_name": "Schaff's Dictionary of the Bible",
        "author": "Philip Schaff",
        "published": "1880",
    }

    if not dry_run:
        with open(output_dir / "_index.json", "w", encoding="utf-8") as f:
            json.dump(index, f, indent=2, ensure_ascii=False)

    return total_entries, total_refs


def main():
    parser = argparse.ArgumentParser(description="Parse Schaff's Dictionary of the Bible")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    print("=" * 60)
    print("SCHAFF DICTIONARY PARSER")
    print("=" * 60)

    entries = parse_schaff(RAW_JSON)

    print(f"\nSaving to {OUTPUT_DIR}/...")
    total_entries, total_refs = save_by_letter(entries, OUTPUT_DIR, args.dry_run)

    print(f"\n{'='*60}")
    print(f"Total: {total_entries} entries, {total_refs} refs")
    if args.dry_run:
        print("(DRY RUN)")

    for term in ["AARON", "MOSES", "JERUSALEM", "FAITH", "SIN"]:
        if term in entries:
            e = entries[term]
            print(f"\n  {term}: {len(e['scripture_refs'])} refs")
            print(f"    {e['definitions'][0]['text'][:120]}...")


if __name__ == "__main__":
    main()
