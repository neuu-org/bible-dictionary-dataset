#!/usr/bin/env python3
"""
Parse Easton's Bible Dictionary and Smith's Bible Dictionary from CCEL XML.
Creates a unified dictionary dataset.

Output: data/dataset/dictionary/*.json
"""

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict
from typing import Optional
import html

# Paths
REPO_ROOT = Path(__file__).parent.parent
CCEL_DIR = REPO_ROOT / "data" / "00_raw" / "ccel" / "xml"
OUTPUT_DIR = REPO_ROOT / "data" / "01_parsed"

EASTON_XML = CCEL_DIR / "easton_ebd2.xml"
SMITH_XML = CCEL_DIR / "smith_bibledict.xml"


def normalize_ref(parsed: str) -> Optional[str]:
    """
    Convert CCEL parsed format to standard reference.
    Example: "|Gen|4|1|4|16" -> "Gen 4:1-16"
             "|Rev|1|8|0|0" -> "Rev 1:8"
    """
    if not parsed:
        return None
    
    parts = parsed.strip("|").split("|")
    if len(parts) < 5:
        return None
    
    book = parts[0]
    chapter1 = parts[1]
    verse1 = parts[2]
    chapter2 = parts[3]
    verse2 = parts[4]
    
    # Book name mapping (CCEL uses abbreviations)
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
        "2John": "2 John", "3John": "3 John", "Jude": "Jude", "Rev": "Revelation"
    }
    
    full_book = book_map.get(book, book)
    
    # Single verse or chapter
    if chapter2 == "0" and verse2 == "0":
        if verse1 == "0":
            return f"{full_book} {chapter1}"  # Whole chapter
        return f"{full_book} {chapter1}:{verse1}"
    
    # Range within same chapter
    if chapter1 == chapter2 or chapter2 == "0":
        return f"{full_book} {chapter1}:{verse1}-{verse2}"
    
    # Range across chapters
    return f"{full_book} {chapter1}:{verse1}-{chapter2}:{verse2}"


def clean_text(text: str) -> str:
    """Clean definition text, removing XML tags but keeping content."""
    if not text:
        return ""
    
    # Unescape HTML entities
    text = html.unescape(text)
    
    # Fix common encoding issues (UTF-8 interpreted as latin-1)
    replacements = {
        'â€œ': '"',  # Left double quote
        'â€\x9d': '"',  # Right double quote  
        'â€™': "'",  # Right single quote / apostrophe
        'â€˜': "'",  # Left single quote
        'â€"': "—",  # Em dash
        'â€"': "–",  # En dash
        'Ã©': 'é',
        'Ã¨': 'è',
        'Ã ': 'à',
        '\x93': '"',
        '\x94': '"',
        '\x92': "'",
        '\x97': '—',
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    
    # Remove scripRef tags but keep text content
    text = re.sub(r'<scripRef[^>]*>([^<]*)</scripRef>', r'\1', text)
    
    # Remove other tags
    text = re.sub(r'<[^>]+>', ' ', text)
    
    # Clean whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def extract_scripture_refs(element) -> list[dict]:
    """Extract all scripture references from an element and its children."""
    refs = []
    
    # Find all scripRef elements
    for scripref in element.iter():
        if scripref.tag == 'scripRef':
            parsed = scripref.get('parsed', '')
            passage = scripref.get('passage', '')
            
            normalized = normalize_ref(parsed)
            if normalized:
                refs.append({
                    "reference": normalized,
                    "original": passage
                })
    
    # Deduplicate
    seen = set()
    unique_refs = []
    for ref in refs:
        if ref["reference"] not in seen:
            seen.add(ref["reference"])
            unique_refs.append(ref)
    
    return unique_refs


def get_element_text(element) -> str:
    """Get all text content from element including children."""
    return ''.join(element.itertext())


def parse_dictionary(xml_path: Path, source_code: str) -> dict:
    """
    Parse a dictionary XML file.
    Returns dict: {term_name: {definition, refs, ...}}
    """
    print(f"\nParsing {xml_path.name}...")
    
    entries = {}
    
    # Read file with proper encoding handling
    with open(xml_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    
    # Fix encoding issues in content
    content = content.replace('â€œ', '"').replace('â€\x9d', '"').replace('â€™', "'")
    content = content.replace('â€˜', "'").replace('â€"', '—')
    
    # Parse XML from string
    root = ET.fromstring(content)
    
    # Find all term/def pairs
    current_term = None
    current_term_id = None
    
    for elem in root.iter():
        if elem.tag == 'term':
            current_term = elem.text.strip() if elem.text else ""
            current_term_id = elem.get('id', '')
            
        elif elem.tag == 'def' and current_term:
            # Extract full definition text
            full_text = []
            for p in elem.findall('.//p'):
                p_text = get_element_text(p)
                if p_text.strip():
                    full_text.append(p_text.strip())
            
            definition = ' '.join(full_text)
            definition_clean = clean_text(definition)
            
            # Extract scripture references
            refs = extract_scripture_refs(elem)
            
            # Create entry
            term_key = current_term.upper()
            
            if term_key not in entries:
                entries[term_key] = {
                    "name": current_term,
                    "slug": re.sub(r'[^a-z0-9]+', '-', current_term.lower()).strip('-'),
                    "definitions": [],
                    "scripture_refs": [],
                    "sources": []
                }
            
            # Add this source's definition
            if definition_clean:
                entries[term_key]["definitions"].append({
                    "source": source_code,
                    "text": definition_clean[:5000]  # Limit length
                })
            
            # Add refs (deduplicated)
            existing_refs = {r["reference"] for r in entries[term_key]["scripture_refs"]}
            for ref in refs:
                if ref["reference"] not in existing_refs:
                    entries[term_key]["scripture_refs"].append(ref)
                    existing_refs.add(ref["reference"])
            
            if source_code not in entries[term_key]["sources"]:
                entries[term_key]["sources"].append(source_code)
            
            current_term = None
    
    print(f"  Found {len(entries)} entries")
    return entries


def merge_dictionaries(easton: dict, smith: dict) -> dict:
    """Merge Easton and Smith dictionaries."""
    merged = {}
    
    # Start with Easton
    for term, data in easton.items():
        merged[term] = data.copy()
    
    # Merge Smith
    for term, data in smith.items():
        if term in merged:
            # Merge definitions
            for defn in data["definitions"]:
                merged[term]["definitions"].append(defn)
            
            # Merge refs
            existing_refs = {r["reference"] for r in merged[term]["scripture_refs"]}
            for ref in data["scripture_refs"]:
                if ref["reference"] not in existing_refs:
                    merged[term]["scripture_refs"].append(ref)
            
            # Merge sources
            for src in data["sources"]:
                if src not in merged[term]["sources"]:
                    merged[term]["sources"].append(src)
        else:
            merged[term] = data.copy()
    
    return merged


def save_dictionary(entries: dict, output_dir: Path):
    """Save dictionary entries to JSON files by first letter."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Group by first letter
    by_letter = defaultdict(dict)
    for term, data in entries.items():
        first_letter = term[0].upper() if term else '_'
        if not first_letter.isalpha():
            first_letter = '_'
        by_letter[first_letter][term] = data
    
    # Save each letter file
    total_entries = 0
    total_refs = 0
    
    for letter, letter_entries in sorted(by_letter.items()):
        output_file = output_dir / f"{letter.lower()}.json"
        
        # Sort entries alphabetically
        sorted_entries = dict(sorted(letter_entries.items()))
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(sorted_entries, f, indent=2, ensure_ascii=False)
        
        letter_refs = sum(len(e["scripture_refs"]) for e in letter_entries.values())
        print(f"  {letter}: {len(letter_entries)} entries, {letter_refs} refs")
        
        total_entries += len(letter_entries)
        total_refs += letter_refs
    
    # Save index
    index = {
        "total_entries": total_entries,
        "total_refs": total_refs,
        "sources": ["EAS", "SMI"],
        "source_names": {
            "EAS": "Easton's Bible Dictionary",
            "SMI": "Smith's Bible Dictionary"
        },
        "files": [f"{l.lower()}.json" for l in sorted(by_letter.keys())]
    }
    
    with open(output_dir / "_index.json", 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2, ensure_ascii=False)
    
    return total_entries, total_refs


def main():
    print("=" * 60)
    print("DICTIONARY PARSER - Easton + Smith")
    print("=" * 60)
    
    # Parse both dictionaries
    easton_entries = parse_dictionary(EASTON_XML, "EAS")
    smith_entries = parse_dictionary(SMITH_XML, "SMI")
    
    # Merge
    print("\nMerging dictionaries...")
    merged = merge_dictionaries(easton_entries, smith_entries)
    
    # Stats
    easton_only = sum(1 for t, d in merged.items() if d["sources"] == ["EAS"])
    smith_only = sum(1 for t, d in merged.items() if d["sources"] == ["SMI"])
    both = sum(1 for t, d in merged.items() if "EAS" in d["sources"] and "SMI" in d["sources"])
    
    print(f"\n  Easton only: {easton_only}")
    print(f"  Smith only: {smith_only}")
    print(f"  Both: {both}")
    print(f"  Total unique terms: {len(merged)}")
    
    # Save
    print(f"\nSaving to {OUTPUT_DIR}...")
    total_entries, total_refs = save_dictionary(merged, OUTPUT_DIR)
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total entries: {total_entries}")
    print(f"Total scripture refs: {total_refs}")
    print(f"Output: {OUTPUT_DIR}")
    
    # Show some examples
    print("\n" + "=" * 60)
    print("EXAMPLES")
    print("=" * 60)
    
    examples = ["SIN", "PAUL", "JERUSALEM", "FAITH", "LOVE"]
    for term in examples:
        if term in merged:
            entry = merged[term]
            print(f"\n{term}:")
            print(f"  Sources: {entry['sources']}")
            print(f"  Refs: {len(entry['scripture_refs'])}")
            if entry['definitions']:
                preview = entry['definitions'][0]['text'][:150]
                print(f"  Definition: {preview}...")


if __name__ == "__main__":
    main()
