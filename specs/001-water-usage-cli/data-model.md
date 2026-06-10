# Data Model: Home Water Usage CLI

**Phase 1 Output** | **Date**: 2026-06-09 | **Plan**: [plan.md](./plan.md)

---

## Entities

### UsageRecord

A single parsed water-usage data point sourced from one Gmail alert email body.

| Field | Type | Source | Constraints |
|-------|------|--------|-------------|
| `date` | `datetime.date` | Parsed from email body (`month`/`day`/`year` groups) | Valid calendar date; invalid dates skip with `[!]` |
| `gallons` | `int` | Parsed from email body (`gallons` group) | > 0 (implied by "exceeded threshold") |

**CSV representation** (run temp + HistoryCache): `date,gallons` (date as `YYYY-MM-DD`)

**Uniqueness key**: `date` — if two emails share the same body date, keep the first (lowest
Gmail message ID) and log `[!]` warning for each duplicate skipped.

**Relationships**:
- Sourced by `fetch.py` + `parse.py`
- Written to run CSV (`water-usage-run-{start}-{end}.csv`) by `storage.py`
- Accumulated in `HistoryCache` by `storage.py`
- Passed to renderer as `list[UsageRecord]`

---

### SeasonalAverage

Computed mean of all `UsageRecord.gallons` values for a named season across all available
history in the HistoryCache.

| Field | Type | Constraints |
|-------|------|-------------|
| `season` | `str` | One of: `"Annual"`, `"Winter"`, `"Spring"`, `"Summer"`, `"Fall"` |
| `avg_gallons` | `float` | Mean of gallons for all records in the season; ≥ 0 |

**Season definitions** (calendar month, from spec):

| Season | Months |
|--------|--------|
| Winter | December, January, February |
| Spring | March, April, May |
| Summer | June, July, August |
| Fall   | September, October, November |
| Annual | All months |

**Availability rule**: A season is included only if ≥ 1 `UsageRecord` exists for it in
the HistoryCache. Missing seasons are silently omitted with a `[!]` terminal notice per
omission.

**Relationships**:
- Computed by `graph.py` from `HistoryCache`
- Passed to renderer as `list[SeasonalAverage]`

---

### Config

The merged runtime configuration. Single source of truth for all behavior in a given run.
Produced by `cli.py` by merging `parameter_values.yaml` defaults with CLI flag overrides.

**Full key set** (YAML key → Python attribute name, type, default):

#### Date Range

| YAML key | Type | Default | CLI flag |
|----------|------|---------|----------|
| *(required)* | `date` | — | `--start-date` |
| *(required)* | `date` | — | `--end-date` |

#### Gmail

| YAML key | Type | Default | CLI flag |
|----------|------|---------|----------|
| `gmail_query_filter` | `str` | `"from:no-reply@leesburgva.gov"` | `--gmail-query-filter` |
| `buffer_email_count` | `int` | `3` | `--buffer-email-count` |
| `max_retries` | `int` | `3` | `--max-retries` |
| `account_number` | `str` | `"40002423000"` | `--account-number` |
| `email_body_pattern` | `str` | *(default regex — see FR-007)* | `--email-body-pattern` |

#### Credentials

| YAML key | Type | Default | CLI flag |
|----------|------|---------|----------|
| `credentials_path` | `str` | `"~/.config/home-water-usage/credentials.json"` | `--credentials-path` |
| `token_path` | `str` | `"~/.config/home-water-usage/token.json"` | `--token-path` |

#### Storage

| YAML key | Type | Default | CLI flag |
|----------|------|---------|----------|
| `temp_dir` | `str` | `"."` | `--temp-dir` |
| `delete_temp_files` | `bool` | `true` | `--no-delete-temp` (sets false) |
| `refresh_cache` | `bool` | `false` | `--refresh-cache` |

#### Graph Display

| YAML key | Type | Default | CLI flag |
|----------|------|---------|----------|
| `graph_title` | `str` | `"Household Water Usage"` | `--graph-title` |
| `x_axis_label` | `str` | `"Date"` | `--x-axis-label` |
| `y_axis_label` | `str` | `"Household Water Usage"` | `--y-axis-label` |
| `gap_label` | `str` | `"gaps = usage within threshold"` | `--gap-label` |
| `date_format` | `str` | `"%b %Y"` | `--date-format` |
| `chart_type` | `str` | `"line"` | `--chart-type` |
| `y_axis_percentile_cap` | `int` | `99` | `--y-axis-percentile-cap` |
| `y_axis_max` | `float\|None` | `null` | `--y-axis-max` |
| `legend_location` | `str` | `"best"` | `--legend-location` |

#### Seasonal Average Lines (4 properties × 5 seasons = 20 keys)

| YAML key pattern | Type | Default |
|-----------------|------|---------|
| `{season}_avg_color` | `str` | season-specific color |
| `{season}_avg_width` | `float` | `1.5` |
| `{season}_avg_style` | `str` | `"dotted"` |
| `{season}_avg_label` | `str` | `"{Season} avg"` |

*(seasons: `annual`, `winter`, `spring`, `summer`, `fall`)*

#### PDF Export

| YAML key | Type | Default | CLI flag |
|----------|------|---------|----------|
| `save_pdf` | `bool` | `false` | `--save-pdf` |
| `pdf_output_dir` | `str` | `"."` | `--pdf-output-dir` |
| `pdf_filename_pattern` | `str` | `"household-water-usage-{start_date}-to-{end_date}.pdf"` | `--pdf-filename-pattern` |
| `pdf_path` | `str\|None` | `null` | `--pdf-path` (overrides dir+pattern) |

**Total**: 30+ keys. All have CLI overrides. CLI value takes precedence when provided.

**Validation rules**:
- `start_date` ≤ `end_date` (abort if violated)
- `buffer_email_count` ≥ 0
- `y_axis_percentile_cap` ∈ [1, 100]
- `temp_dir` must exist and be writable at runtime
- `email_body_pattern` must compile as valid regex with required named groups

---

### HistoryCache

Not a runtime object but a persistent file. Represented in code as a `pd.DataFrame` or
`list[UsageRecord]` when loaded.

| Attribute | Value |
|-----------|-------|
| Filename | `water-usage-history.csv` |
| Location | `temp_dir` (from Config) |
| Columns | `date` (YYYY-MM-DD), `gallons` (int) |
| Sort order | `date` ascending |
| Dedup key | `date` (first occurrence wins) |
| Lifecycle | Persistent — never deleted by normal operation |
| Rebuild trigger | `--refresh-cache` or cache predates requested start date |
| Corrupt recovery | Log `[!]`, delete, rebuild from Gmail |

---

## State Transitions

```
CLI invoked
    │
    ▼
Config resolved (YAML + CLI merge)
    │
    ▼
Gmail OAuth (credentials → token.json, chmod 600)
    │
    ▼
HistoryCache read
    ├── Cache miss or --refresh-cache → Gmail fetch → parse → merge cache
    └── Partial overlap → fetch uncached tail → merge cache
    │
    ▼
UsageRecords classified:
    ├── Buffer records → cache only (not plotted)
    ├── In-range records → cache + plotted
    └── Out-of-window → discarded
    │
    ▼
SeasonalAverages computed from HistoryCache
    │
    ▼
Run CSV written (water-usage-run-{start}-{end}.csv)
    │
    ▼
Renderer dispatched (chart_type → renderers/{chart_type}.py)
    ├── [save_pdf] → PDF written synchronously
    └── plt.show() → interactive window
    │
    ▼
Run CSV deleted (unless --no-delete-temp)
```
