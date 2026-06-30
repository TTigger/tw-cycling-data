# tw-cycling-data Open Dataset

A **de-identified**, row-level dataset of Taiwan road-cycling race results: 8 sources normalized into one file — 147,609 rows, 2009–2026. For research and analysis.

- **License**: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Please attribute `tw-cycling-data` (https://github.com/TTigger/tw-cycling-data).
- **Download**: see [GitHub Releases](https://github.com/TTigger/tw-cycling-data/releases) (`tw-cycling-results.csv.gz` / `.json.gz` + `datapackage.json`).
- **中文**:見 [DATASET.md](DATASET.md)。

## Privacy

This is a de-identified aggregation of **already-public race results**: only a masked name `name_masked` (e.g. 李○明) is included; external identifiers (`uci_id`, `tsu_rider_id`, `source_url`) and `bib`, `nationality` are **removed**. If you are a data subject and want your records removed, please open a [GitHub Issue](https://github.com/TTigger/tw-cycling-data/issues).

## Columns

| Column | Type | Description |
|---|---|---|
| `race_key` | string | Race key; shared across years of the same event |
| `year` | integer | Year |
| `date` | string | Race date YYYY-MM-DD (~69% present) |
| `region` | string | County-level region (~38% present) |
| `series` | string | Race series |
| `race_name_canonical` | string | Canonical race name |
| `race_type` | string | road / criterium / KOM / TT, etc. |
| `race_class` | string | Race classification |
| `result_label` | string | Result group label |
| `category_raw` | string | Raw category string |
| `gender` | string | M/F (~52% present) |
| `age_band` | string | Age band U19/19-29/30-39/40-49/50-59/60+ (~36% present) |
| `age_group` | string | Fine-grained age |
| `rank_overall` | integer | Overall rank (often empty for certification rides) |
| `finish_seconds` | number | Finish time in seconds |
| `finish_time` | string | Finish time string |
| `splits` | string | Split times (JSON; ~9% present) |
| `team` | string | Team (~46% present) |
| `name_masked` | string | Masked name (e.g. 李○明) |
| `source_platform` | string | Source platform |

## Load

```python
import pandas as pd
df = pd.read_csv("tw-cycling-results.csv.gz")
```

## Cite

See [CITATION.cff](CITATION.cff) (GitHub "Cite this repository").
