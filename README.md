# Bible Dictionary Dataset

Biblical dictionary entries from Easton's Bible Dictionary (1897) and Smith's Bible Dictionary (1863), extracted from the CCEL (Christian Classics Ethereal Library) corpus.

Part of the [NEUU](https://github.com/neuu-org) biblical scholarship ecosystem.

## Overview

| Metric | Value |
|--------|-------|
| Total entries (unified) | 5,998 |
| Easton entries | 3,962 |
| Smith entries | 4,561 |
| Entries in both | 2,525 |
| Total scripture references | 35,089 |

## Pipeline

```
CCEL ThML XML (HuggingFace jncraton/ccel-paragraphs)
  ├── ebd2.xml (Easton, 7.2 MB)
  └── bibledict.xml (Smith, 6.5 MB)
        ↓ parse_easton_smith.py
00_raw/ccel/  (7,433 + 4,639 paragraphs)
        ↓ parse_easton_smith.py
02_unified/   (5,998 merged entries, a-z)
        ↓ split_sources.py
01_sources/easton/  (3,962 entries)
01_sources/smith/   (4,561 entries)
```

## Structure

```
bible-dictionary-dataset/
├── data/
│   ├── 00_raw/
│   │   └── ccel/
│   │       ├── xml/
│   │       │   ├── ebd2.xml             # Easton original ThML (7.2 MB)
│   │       │   └── bibledict.xml        # Smith original ThML (6.5 MB)
│   │       ├── easton_ccel_raw.json     # 7,433 paragraphs from CCEL
│   │       └── smith_ccel_raw.json      # 4,639 paragraphs from CCEL
│   ├── 01_sources/
│   │   ├── easton/                      # 3,962 entries (Easton only)
│   │   │   ├── a.json ... z.json
│   │   │   └── _index.json
│   │   └── smith/                       # 4,561 entries (Smith only)
│   │       ├── a.json ... z.json
│   │       └── _index.json
│   └── 02_unified/                      # 5,998 entries (merged)
│       ├── a.json ... z.json
│       └── _index.json
├── scripts/
│   ├── parse_easton_smith.py            # CCEL XML → unified JSON
│   └── split_sources.py                 # Unified → separate sources
```

## Data Layers

### 00_raw — CCEL Paragraphs

Raw paragraphs extracted from the [jncraton/ccel-paragraphs](https://huggingface.co/datasets/jncraton/ccel-paragraphs) HuggingFace dataset. Each paragraph has:

```json
{
  "id": "ccel/e/easton/ebd2.xml:a-p4",
  "text": "Afterwards, when encamped before Sinai...",
  "refs": ["Ex. 19:24", "Ex. 24:9"],
  "author": "easton",
  "title": "Easton's Bible Dictionary"
}
```

### 01_sources — Separated by Dictionary

Each dictionary as standalone entries, organized alphabetically:

```json
{
  "AARON": {
    "name": "Aaron",
    "slug": "aaron",
    "definitions": [{"source": "EAS", "text": "The first high priest..."}],
    "scripture_refs": [{"reference": "Exodus 4:14", "original": "Ex 4:14"}]
  }
}
```

### 02_unified — Merged

Both dictionaries merged by term. Entries with the same name get definitions from both sources:

```json
{
  "AARON": {
    "name": "Aaron",
    "slug": "aaron",
    "definitions": [
      {"source": "EAS", "text": "The first high priest..."},
      {"source": "SMI", "text": "The son of Amram and Jochebed..."}
    ],
    "scripture_refs": [...],
    "sources": ["EAS", "SMI"]
  }
}
```

## Sources

| Source | Author | Published | Entries | License |
|--------|--------|-----------|---------|---------|
| Easton's Bible Dictionary | Matthew George Easton | 1897 | 3,962 | Public domain |
| Smith's Bible Dictionary | William Smith | 1863 | 4,561 | Public domain |

Both extracted from [CCEL](https://www.ccel.org/) (Christian Classics Ethereal Library).

## Scripts

```bash
# Split unified into separate sources
python scripts/split_sources.py

# Parse from CCEL XML (requires XML source files)
python scripts/parse_easton_smith.py
```

## License

Source dictionaries are **public domain** (1863, 1897). Dataset and scripts: **CC BY 4.0**.

## Citation

```bibtex
@misc{neuu_bible_dictionary_2026,
  title={Bible Dictionary Dataset: Easton and Smith Bible Dictionaries},
  author={NEUU},
  year={2026},
  publisher={GitHub},
  url={https://github.com/neuu-org/bible-dictionary-dataset}
}
```

## Related Datasets

- [bible-topics-dataset](https://github.com/neuu-org/bible-topics-dataset) — Consumes dictionary for V3 definitions
- [bible-gazetteers-dataset](https://github.com/neuu-org/bible-gazetteers-dataset) — Entities and symbols
- [bible-commentaries-dataset](https://github.com/neuu-org/bible-commentaries-dataset) — 31,218 commentaries
- [bible-crossrefs-dataset](https://github.com/neuu-org/bible-crossrefs-dataset) — 1.1M+ cross-references
- [bible-text-dataset](https://github.com/neuu-org/bible-text-dataset) — 17 Bible translations
- [bible-hybrid-search](https://github.com/neuu-org/bible-hybrid-search) — Hybrid retrieval research
