# Bible Dictionary Dataset

Biblical dictionary entries from Easton's Bible Dictionary (1897) and Smith's Bible Dictionary (1863), extracted from the CCEL (Christian Classics Ethereal Library) ThML XML sources.

Part of the [NEUU](https://github.com/neuu-org) biblical scholarship ecosystem.

## Overview

| Metric | Value |
|--------|-------|
| Total entries (parsed) | 5,998 |
| Easton entries | 3,962 |
| Smith entries | 4,561 |
| Entries in both | 2,525 |
| Total scripture references | 35,089 |
| Raw XML sources | 12 biblical dictionaries |

## Pipeline

```
00_raw/ccel/xml/                          ← Original ThML XML from CCEL
  ├── easton_ebd2.xml (7.2 MB)
  ├── smith_bibledict.xml (6.5 MB)
  └── 10 additional biblical dictionaries
              ↓ parse_easton_smith.py
01_parsed/   (5,998 merged entries, a-z)  ← Easton + Smith merged by term
              ↓ split_sources.py
02_sources/  (separated by dictionary)    ← Each dictionary standalone
  ├── easton/ (3,962 entries)
  └── smith/  (4,561 entries)
```

## Structure

```
bible-dictionary-dataset/
├── data/
│   ├── 00_raw/
│   │   └── ccel/xml/                    # Original ThML XML sources
│   │       ├── easton_ebd2.xml          # Easton's Bible Dictionary
│   │       ├── smith_bibledict.xml      # Smith's Bible Dictionary
│   │       ├── hastings_dict_bible.xml  # Hastings Dictionary of the Bible
│   │       ├── hastings_dictv1-v4.xml   # Hastings (4 volumes)
│   │       ├── hastings_christ_gospels_v1-v2.xml
│   │       ├── hitchcock_bible_names.xml
│   │       ├── grimm_greek_lexicon.xml  # Greek-English Lexicon NT
│   │       └── wigram_greek_concordance.xml
│   │
│   ├── 01_parsed/                       # Merged Easton + Smith (by term)
│   │   ├── a.json ... z.json           # 26 alphabetical files
│   │   └── _index.json                 # Stats and file listing
│   │
│   └── 02_sources/                      # Separated by dictionary
│       ├── easton/                      # 3,962 entries (Easton only)
│       │   ├── a.json ... z.json
│       │   └── _index.json
│       └── smith/                       # 4,561 entries (Smith only)
│           ├── a.json ... z.json
│           └── _index.json
│
├── scripts/
│   ├── parse_easton_smith.py            # XML → 01_parsed (merge both dictionaries)
│   └── split_sources.py                 # 01_parsed → 02_sources (separate by dictionary)
```

## Data Layers

### 00_raw — Original ThML XML

XML files from the [CCEL](https://www.ccel.org/) via [jncraton/ccel-paragraphs](https://huggingface.co/datasets/jncraton/ccel-paragraphs). ThML (Theological Markup Language) with `<term>`, `<def>`, and `<scripRef>` tags.

12 biblical dictionaries available as raw XML. Currently only Easton and Smith are parsed.

### 01_parsed — Merged by Term

Result of `parse_easton_smith.py`: both dictionaries merged by uppercase term name. When the same term exists in both, definitions from both sources are combined.

```json
{
  "AARON": {
    "name": "Aaron",
    "slug": "aaron",
    "definitions": [
      {"source": "EAS", "text": "The first high priest..."},
      {"source": "SMI", "text": "The son of Amram and Jochebed..."}
    ],
    "scripture_refs": [
      {"reference": "Exodus 4:14", "original": "Ex 4:14"}
    ],
    "sources": ["EAS", "SMI"]
  }
}
```

### 02_sources — Separated by Dictionary

Result of `split_sources.py`: each dictionary as standalone entries, containing only its own definitions.

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

## Raw XML Sources

| File | Dictionary | Size | Parsed? |
|------|-----------|------|:-------:|
| `easton_ebd2.xml` | Easton's Bible Dictionary (1897) | 7.2 MB | Yes |
| `smith_bibledict.xml` | Smith's Bible Dictionary (1863) | 6.5 MB | Yes |
| `hastings_dict_bible.xml` | Hastings Dictionary of the Bible | 9.3 MB | Not yet |
| `hastings_dictv1-v4.xml` | Hastings (4 volumes) | 1.0 MB | Not yet |
| `hastings_christ_gospels_v1-v2.xml` | Dictionary of Christ and the Gospels | 0.5 MB | Not yet |
| `hitchcock_bible_names.xml` | Hitchcock's Bible Names | 0.2 MB | Not yet |
| `grimm_greek_lexicon.xml` | Greek-English Lexicon of the NT | 0.2 MB | Not yet |
| `wigram_greek_concordance.xml` | Greek Concordance of the NT | 0.3 MB | Not yet |

## Scripts

```bash
# Parse Easton + Smith XML → merged JSON
python scripts/parse_easton_smith.py

# Split merged → separate sources
python scripts/split_sources.py
```

## License

All source dictionaries are **public domain** (1863-1897). Dataset and scripts: **CC BY 4.0**.

## Citation

```bibtex
@misc{neuu_bible_dictionary_2026,
  title={Bible Dictionary Dataset: Biblical Dictionaries from CCEL},
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
