# CTFtime Archive Dataset

A structured dataset of capture the flag (CTF) competition events from [CTFtime.org](https://ctftime.org), covering 2015 through 2025.

The dataset contains 2,477 events scraped from CTFtime's [past events archive](https://ctftime.org/event/list/past). Each event includes its name, date, format, location, and CTFtime weight rating. An enriched version adds 20+ derived variables for temporal analysis, duration categories, COVID-era classification, and more.

---

## Dataset Overview

|  | Raw | Enriched |
|--|-----|----------|
| **File** | `ctftime_archive_all.csv` | `ctftime_archive_all_enriched.csv` |
| **Rows** | 2,477 | 2,380 |
| **Columns** | 8 | 28 |
| **Description** | Parsed directly from CTFtime | Cleaned, standardized, with derived variables |

The enriched file has fewer rows because events with durations over 7 days (training platforms, long-running challenges) were filtered out to focus on traditional CTF competitions.

**Events per year:**

| 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|------|------|------|------|------|------|------|------|------|------|------|
| 81   | 109  | 142  | 157  | 201  | 230  | 241  | 274  | 332  | 351  | 360  |

---

## Files

```
ctftime-archive/
├── data/
│   ├── ctftime_archive_all.csv            # Raw parsed data (8 columns)
│   └── ctftime_archive_all_enriched.csv   # Enriched data (28 columns)
├── data_dictionary.csv                    # Column descriptions and types
├── parse_ctf.py                           # Parser: CTFtime text -> raw CSV
├── enrich_ctf_data.py                     # Enrichment: raw CSV -> enriched CSV
├── requirements.txt
├── CITATION.cff
├── LICENSE
└── README.md
```

---

## How the Data Was Collected

1. Visited each year's archive page on CTFtime (e.g. `ctftime.org/event/list/?year=2022`)
2. Copied the event table into a text file (tab-separated)
3. Ran `parse_ctf.py` to standardize formats, locations, and weights into a clean CSV
4. Ran `enrich_ctf_data.py` to add temporal variables, duration calculations, and categorical flags

The raw text files are not included in this repo, but the parser script documents the expected input format.

---

## Column Reference

The raw CSV has 8 columns:

| Column | Example |
|--------|---------|
| event_id | 1 |
| name | 32C3 CTF |
| year | 2015 |
| date_raw | 27 Dec., 12:00 PST — 29 Dec. 2015, 12:00 PST |
| format | Jeopardy |
| location | On-line |
| weight | 70.00 |
| notes | N/A |

The enriched CSV adds 20 derived columns. See `data_dictionary.csv` for the full list with types and descriptions. Key additions include:

- `start_date`, `end_date`, `duration_hours`, `duration_days`
- `start_quarter`, `season`, `covid_era`
- `is_weekend`, `is_multi_day`, `is_qualifier`, `is_finals`
- `duration_category` (Short/Medium/Long), `weight_category` (Zero/Low/Medium/High)

---

## Usage

**Load the enriched dataset directly** (no scripts needed):

```python
import csv

with open('data/ctftime_archive_all_enriched.csv', 'r') as f:
    reader = csv.DictReader(f)
    events = list(reader)
```

Or with pandas:

```python
import pandas as pd

df = pd.read_csv('data/ctftime_archive_all_enriched.csv')
```

**Rebuild from scratch** (if you want to re-scrape or modify the pipeline):

```bash
pip install -r requirements.txt

# Step 1: Parse a raw text file
python parse_ctf.py 2022_raw.txt --year 2022

# Step 2: Enrich the parsed CSV
python enrich_ctf_data.py 2022_ctf_data.csv
```

---

## Citation

If you use this dataset, please cite:

```bibtex
@misc{jimenez2026ctftime,
  author    = {Jimenez, Jhaell},
  title     = {CTFtime Archive Dataset: 2015-2025},
  year      = {2026},
  url       = {https://github.com/xjhaell/ctftime-archive}
}
```

GitHub also provides a citation button via the `CITATION.cff` file in this repo.

---

## License

MIT. See [LICENSE](LICENSE).

The underlying CTF event data is sourced from [CTFtime.org](https://ctftime.org). This dataset is a structured compilation intended for research and analysis.