# Bible Dictionary Dataset

Biblical dictionary entries parsed from 4 CCEL ThML XML sources into 5 structured dictionary datasets.

Part of the [NEUU](https://github.com/neuu-org) biblical scholarship ecosystem.

## Overview

| Metric | Value |
|--------|-------|
| Raw XML sources | 4 (Easton, Smith, Hastings, Hitchcock) |
| Parsed dictionaries | 5 (Easton, Smith, Hastings, Hitchcock, Schaff) |
| Easton entries | 3,962 |
| Smith entries | 4,561 |
| Hastings entries | 5,033 |
| Hitchcock entries | 2,619 |
| Schaff entries | 4,725 |
| **Total entries** | **20,900** |

## Pipeline

```
00_raw/ccel/xml/                          <- Original ThML XML from CCEL
  ├── easton_ebd2.xml
  ├── smith_bibledict.xml
  ├── hastings_dict_bible.xml
  └── hitchcock_bible_names.xml
              |
              | parse_easton_smith.py
              v
01_parsed/   (Easton + Smith merged by term, a-z + _index.json)
              |
              | split_sources.py
              v
02_sources/  (each dictionary standalone)
  ├── easton/    (3,962 entries)
  ├── smith/     (4,561 entries)
  ├── hastings/  (5,033 entries)  <- parse_hastings.py
  ├── hitchcock/ (2,619 entries)  <- parse_hitchcock.py
  └── schaff/    (4,725 entries)  <- parse_schaff.py
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
│   │       └── hitchcock_bible_names.xml # Hitchcock's Bible Names
│   │
│   ├── 01_parsed/                       # Merged Easton + Smith (by term)
│   │   ├── a.json ... z.json           # 26 alphabetical files
│   │   └── _index.json                 # Stats and file listing
│   │
│   └── 02_sources/                      # Separated by dictionary
│       ├── easton/    (3,962 entries)
│       ├── smith/     (4,561 entries)
│       ├── hastings/  (5,033 entries)
│       ├── hitchcock/ (2,619 entries)
│       └── schaff/    (4,725 entries)
│
├── scripts/
│   ├── parse_easton_smith.py            # XML -> 01_parsed (merge both dictionaries)
│   ├── split_sources.py                 # 01_parsed -> 02_sources (separate Easton/Smith)
│   ├── parse_hastings.py                # XML -> 02_sources/hastings
│   ├── parse_hitchcock.py               # XML -> 02_sources/hitchcock
│   └── parse_schaff.py                  # CCEL parquet JSON -> 02_sources/schaff
```

## Data Layers

### 00_raw -- Original ThML XML

XML files from the [CCEL](https://www.ccel.org/) via [jncraton/ccel-paragraphs](https://huggingface.co/datasets/jncraton/ccel-paragraphs). ThML (Theological Markup Language) with `<term>`, `<def>`, and `<scripRef>` tags.

4 XML sources are stored in `data/00_raw/ccel/xml/`.

### 01_parsed -- Merged by Term

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

### 02_sources -- Separated by Dictionary

Each dictionary as standalone entries, containing only its own definitions.

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

| File | Dictionary | Parsed? |
|------|-----------|:-------:|
| `easton_ebd2.xml` | Easton's Bible Dictionary (1897) | Yes (3,962 entries) |
| `smith_bibledict.xml` | Smith's Bible Dictionary (1863) | Yes (4,561 entries) |
| `hastings_dict_bible.xml` | Hastings Dictionary of the Bible (1898) | Yes (5,033 entries) |
| `hitchcock_bible_names.xml` | Hitchcock's Bible Names (1869) | Yes (2,619 entries) |

Schaff's Dictionary of the Bible (4,725 entries) was parsed from CCEL parquet JSON via `parse_schaff.py`.

## Scripts

```bash
# Parse Easton + Smith XML -> merged JSON
python scripts/parse_easton_smith.py

# Split merged -> separate sources
python scripts/split_sources.py

# Parse individual dictionaries -> 02_sources
python scripts/parse_hastings.py
python scripts/parse_hitchcock.py
python scripts/parse_schaff.py
```

## License

All source dictionaries are **public domain** (1863-1898). Dataset and scripts: **CC BY 4.0**.

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

- [bible-topics-dataset](https://github.com/neuu-org/bible-topics-dataset) -- Consumes dictionary for V3 definitions
- [bible-gazetteers-dataset](https://github.com/neuu-org/bible-gazetteers-dataset) -- Entities and symbols
- [bible-commentaries-dataset](https://github.com/neuu-org/bible-commentaries-dataset) -- 31,218 commentaries
- [bible-crossrefs-dataset](https://github.com/neuu-org/bible-crossrefs-dataset) -- 1.1M+ cross-references
- [bible-text-dataset](https://github.com/neuu-org/bible-text-dataset) -- 17 Bible translations
- [bible-hybrid-search](https://github.com/neuu-org/bible-hybrid-search) -- Hybrid retrieval research
