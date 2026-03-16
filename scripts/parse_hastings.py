#!/usr/bin/env python3
"""
parse_hastings.py

Parses Hastings Dictionary of the Bible from CCEL ThML XML.
Output: data/02_sources/hastings/ (a.json ... z.json + _index.json)

The Hastings XML uses div1 sections per letter (A, B, C...) with articles
delimited by <p> elements whose first child is <strong> containing the term name.

Usage:
    python scripts/parse_hastings.py
    python scripts/parse_hastings.py --dry-run
"""

import argparse
import html
import json
import re
import unicodedata
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).parent.parent
XML_PATH = REPO_ROOT / "data" / "00_raw" / "ccel" / "xml" / "hastings_dict_bible.xml"
OUTPUT_DIR = REPO_ROOT / "data" / "02_sources" / "hastings"
SOURCE_CODE = "HAS"

# Skip these div1 titles (not dictionary letters)
SKIP_TITLES = {"TITLE", "PREFACE", "LIST OF COLORED MAPS.", "INDEX",
               "LIST OF WORKS ON BIBLICAL LEARNING MADE USE OF IN THIS DICTIONARY."}

# Book name mapping (CCEL abbreviations → full names)
BOOK_MAP = {
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
    "Jg": "Judges", "1Sm": "1 Samuel", "2Sm": "2 Samuel",
    "1Ki": "1 Kings", "2Ki": "2 Kings", "1Ch": "1 Chronicles", "2Ch": "2 Chronicles",
    "Ne": "Nehemiah", "Es": "Esther", "Pr": "Proverbs", "So": "Song of Solomon",
    "La": "Lamentations", "Da": "Daniel", "Ho": "Hosea", "Am": "Amos",
    "Ob": "Obadiah", "Mi": "Micah", "Na": "Nahum", "Ha": "Habakkuk",
    "Zp": "Zephaniah", "Hg": "Haggai", "Zc": "Zechariah", "Ml": "Malachi",
    "Mt": "Matthew", "Mk": "Mark", "Lk": "Luke", "Jn": "John", "Ac": "Acts",
    "Ro": "Romans", "Ga": "Galatians", "Ep": "Ephesians", "Pp": "Philippians",
    "Co": "Colossians", "He": "Hebrews", "Jm": "James", "Re": "Revelation",
}


def normalize_ref(parsed: str) -> Optional[str]:
    """Convert CCEL parsed format to standard reference."""
    if not parsed:
        return None

    parts = parsed.strip("|").split("|")

    # Handle format with version prefix: version|book|ch|v|ch|v
    if len(parts) >= 6:
        # Has version prefix
        book, ch1, v1, ch2, v2 = parts[1], parts[2], parts[3], parts[4], parts[5]
    elif len(parts) >= 4:
        book, ch1, v1 = parts[0], parts[1], parts[2]
        ch2 = parts[3] if len(parts) > 3 else "0"
        v2 = parts[4] if len(parts) > 4 else "0"
    else:
        return None

    full_book = BOOK_MAP.get(book, book)

    if ch2 == "0" and v2 == "0":
        if v1 == "0":
            return f"{full_book} {ch1}"
        return f"{full_book} {ch1}:{v1}"

    if ch1 == ch2 or ch2 == "0":
        return f"{full_book} {ch1}:{v1}-{v2}"

    return f"{full_book} {ch1}:{v1}-{ch2}:{v2}"


def clean_text(text: str) -> str:
    """Clean ThML text: unescape HTML, remove tags, fix encoding, normalize whitespace."""
    if not text:
        return ""

    text = html.unescape(text)

    # Fix mojibake
    try:
        if any(ord(c) > 127 for c in text):
            import ftfy
            text = ftfy.fix_text(text)
    except ImportError:
        pass

    # Remove scripRef tags but keep text
    text = re.sub(r"<scripRef[^>]*>([^<]*)</scripRef>", r"\1", text)
    # Remove all other tags
    text = re.sub(r"<[^>]+>", " ", text)
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


def clean_term_name(name: str) -> str:
    """Clean article term name: remove apostrophes used for pronunciation."""
    # Remove pronunciation marks like AA'RON → AARON, AB'ARIM → ABARIM
    name = name.replace("'", "").replace("'", "")
    # Normalize unicode
    name = unicodedata.normalize("NFC", name)
    return name.strip()


def extract_refs_from_element(elem) -> list:
    """Extract all scripRef references from an element tree."""
    refs = []
    seen = set()

    for scripref in elem.iter("scripRef"):
        parsed = scripref.get("parsed", "")
        passage = scripref.get("passage", "")
        original_text = "".join(scripref.itertext()).strip()

        normalized = normalize_ref(parsed)
        if normalized and normalized not in seen:
            refs.append({
                "reference": normalized,
                "original": passage or original_text,
            })
            seen.add(normalized)

    return refs


def get_all_text(elem) -> str:
    """Get all text from element including children."""
    return "".join(elem.itertext())


def parse_hastings(xml_path: Path, dry_run: bool = False) -> dict:
    """Parse Hastings Dictionary XML into structured entries."""
    print(f"Parsing {xml_path.name} ({xml_path.stat().st_size / 1024 / 1024:.1f} MB)...")

    with open(xml_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    root = ET.fromstring(content)
    entries = {}
    stats = {"div1_processed": 0, "paragraphs_scanned": 0, "articles_found": 0}

    for div1 in root.iter("div1"):
        title = div1.get("title", "")

        # Skip non-dictionary sections
        if title in SKIP_TITLES or not title:
            continue

        letter = title.strip(".").strip().upper()
        if len(letter) > 2:
            continue

        stats["div1_processed"] += 1

        # Collect all paragraphs and identify article boundaries
        current_term = None
        current_paragraphs = []
        current_refs = []

        for elem in div1:
            if elem.tag == "p":
                stats["paragraphs_scanned"] += 1

                # Check if this paragraph starts a new article
                children = list(elem)
                first_text = get_all_text(elem).strip()

                is_new_article = False
                new_term = None

                if children and children[0].tag == "strong":
                    candidate = "".join(children[0].itertext()).strip()
                    if candidate and len(candidate) < 60:
                        is_new_article = True
                        new_term = candidate

                if is_new_article and new_term:
                    # Save previous article
                    if current_term and current_paragraphs:
                        _save_article(entries, current_term, current_paragraphs, current_refs)
                        stats["articles_found"] += 1

                    # Start new article
                    current_term = new_term
                    current_paragraphs = [clean_text(first_text)]
                    current_refs = extract_refs_from_element(elem)
                else:
                    # Continue current article
                    if current_term:
                        text = clean_text(first_text)
                        if text:
                            current_paragraphs.append(text)
                        current_refs.extend(extract_refs_from_element(elem))

            elif elem.tag == "ol":
                # Ordered lists inside articles
                if current_term:
                    for li in elem.iter("li"):
                        text = clean_text(get_all_text(li))
                        if text:
                            current_paragraphs.append(text)
                        current_refs.extend(extract_refs_from_element(li))

        # Save last article of this letter
        if current_term and current_paragraphs:
            _save_article(entries, current_term, current_paragraphs, current_refs)
            stats["articles_found"] += 1

    print(f"  Sections: {stats['div1_processed']}")
    print(f"  Paragraphs scanned: {stats['paragraphs_scanned']}")
    print(f"  Articles found: {stats['articles_found']}")

    return entries


def _save_article(entries: dict, term: str, paragraphs: list, refs: list):
    """Save an article to the entries dict."""
    clean_name = clean_term_name(term)
    term_key = clean_name.upper()

    # Skip very short entries (likely cross-references like "See X")
    full_text = " ".join(paragraphs)
    if len(full_text) < 10:
        return

    slug = re.sub(r"[^a-z0-9]+", "-", clean_name.lower()).strip("-")

    if term_key not in entries:
        entries[term_key] = {
            "name": clean_name,
            "slug": slug,
            "definitions": [],
            "scripture_refs": [],
            "sources": [SOURCE_CODE],
        }

    entries[term_key]["definitions"].append({
        "source": SOURCE_CODE,
        "text": full_text,
    })

    # Merge refs (deduplicated)
    existing = {r["reference"] for r in entries[term_key]["scripture_refs"]}
    for ref in refs:
        if ref["reference"] not in existing:
            entries[term_key]["scripture_refs"].append(ref)
            existing.add(ref["reference"])


def save_by_letter(entries: dict, output_dir: Path, dry_run: bool):
    """Save entries organized by first letter."""
    by_letter = defaultdict(dict)
    for term, data in entries.items():
        letter = term[0].upper() if term and term[0].isalpha() else "_"
        by_letter[letter][term] = data

    total_entries = 0
    total_refs = 0

    for letter, letter_entries in sorted(by_letter.items()):
        sorted_entries = dict(sorted(letter_entries.items()))
        refs_count = sum(len(e["scripture_refs"]) for e in letter_entries.values())
        print(f"  {letter}: {len(letter_entries)} entries, {refs_count} refs")

        total_entries += len(letter_entries)
        total_refs += refs_count

        if not dry_run:
            output_dir.mkdir(parents=True, exist_ok=True)
            with open(output_dir / f"{letter.lower()}.json", "w", encoding="utf-8") as f:
                json.dump(sorted_entries, f, indent=2, ensure_ascii=False)

    # Index
    index = {
        "total_entries": total_entries,
        "total_refs": total_refs,
        "source": SOURCE_CODE,
        "source_name": "Hastings Dictionary of the Bible",
        "author": "Philip Schaff",
        "published": "1880",
    }

    if not dry_run:
        with open(output_dir / "_index.json", "w", encoding="utf-8") as f:
            json.dump(index, f, indent=2, ensure_ascii=False)

    return total_entries, total_refs


def main():
    parser = argparse.ArgumentParser(description="Parse Hastings Dictionary of the Bible")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    print("=" * 60)
    print("HASTINGS DICTIONARY PARSER")
    print("=" * 60)

    entries = parse_hastings(XML_PATH, args.dry_run)

    print(f"\nTotal unique terms: {len(entries)}")

    print(f"\nSaving to {OUTPUT_DIR}/...")
    total_entries, total_refs = save_by_letter(entries, OUTPUT_DIR, args.dry_run)

    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"Total entries: {total_entries}")
    print(f"Total refs: {total_refs}")

    if args.dry_run:
        print("(DRY RUN — nothing saved)")

    # Show sample entries
    print(f"\n{'='*60}")
    print("SAMPLE ENTRIES")
    print(f"{'='*60}")
    for term in ["AARON", "MOSES", "JERUSALEM", "FAITH", "SIN"]:
        if term in entries:
            e = entries[term]
            text_preview = e["definitions"][0]["text"][:150] if e["definitions"] else ""
            print(f"\n  {term}: {len(e['scripture_refs'])} refs")
            print(f"    {text_preview}...")


if __name__ == "__main__":
    main()
