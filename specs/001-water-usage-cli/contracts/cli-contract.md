# CLI Contract: home-water-usage

**Phase 1 Output** | **Date**: 2026-06-09 | **Data Model**: [data-model.md](../data-model.md)

---

## Invocation

```
home-water-usage --start-date YYYY-MM-DD --end-date YYYY-MM-DD [OPTIONS]
```

`--start-date` and `--end-date` are required. All other arguments are optional and override
the corresponding key in `parameter_values.yaml` for the current run only.

---

## Required Arguments

| Flag | Type | Description |
|------|------|-------------|
| `--start-date` | `YYYY-MM-DD` | Start of the plotted date range (inclusive) |
| `--end-date` | `YYYY-MM-DD` | End of the plotted date range (inclusive) |

**Constraint**: `start_date` ≤ `end_date`; violating this aborts with `[✗]`.

---

## Optional Arguments

### Gmail & Credentials

| Flag | YAML key | Type | Default |
|------|----------|------|---------|
| `--credentials-path` | `credentials_path` | path | `~/.config/home-water-usage/credentials.json` |
| `--token-path` | `token_path` | path | `~/.config/home-water-usage/token.json` |
| `--gmail-query-filter` | `gmail_query_filter` | str | `from:no-reply@leesburgva.gov` |
| `--buffer-email-count` | `buffer_email_count` | int | `3` |
| `--max-retries` | `max_retries` | int | `3` |
| `--account-number` | `account_number` | str | `40002423000` |
| `--email-body-pattern` | `email_body_pattern` | str | *(default regex)* |

### Storage & Cache

| Flag | YAML key | Type | Default |
|------|----------|------|---------|
| `--temp-dir` | `temp_dir` | path | `.` (current dir) |
| `--no-delete-temp` | `delete_temp_files` | flag | delete=true → sets false |
| `--refresh-cache` | `refresh_cache` | flag | false → sets true |

### Graph Display

| Flag | YAML key | Type | Default |
|------|----------|------|---------|
| `--graph-title` | `graph_title` | str | `Household Water Usage` |
| `--x-axis-label` | `x_axis_label` | str | `Date` |
| `--y-axis-label` | `y_axis_label` | str | `Household Water Usage` |
| `--gap-label` | `gap_label` | str | `gaps = usage within threshold` |
| `--date-format` | `date_format` | str | `%b %Y` |
| `--chart-type` | `chart_type` | str | `line` |
| `--y-axis-percentile-cap` | `y_axis_percentile_cap` | int (1–100) | `99` |
| `--y-axis-max` | `y_axis_max` | float | `null` (disabled) |
| `--legend-location` | `legend_location` | str | `best` |

### Seasonal Average Lines (per season: annual, winter, spring, summer, fall)

| Flag pattern | YAML key pattern | Type | Default |
|-------------|-----------------|------|---------|
| `--{season}-avg-color` | `{season}_avg_color` | str (color) | season-specific |
| `--{season}-avg-width` | `{season}_avg_width` | float | `1.5` |
| `--{season}-avg-style` | `{season}_avg_style` | str | `dotted` |
| `--{season}-avg-label` | `{season}_avg_label` | str | `{Season} avg` |

### PDF Export

| Flag | YAML key | Type | Default |
|------|----------|------|---------|
| `--save-pdf` | `save_pdf` | flag | false → sets true |
| `--pdf-output-dir` | `pdf_output_dir` | path | `.` (current dir) |
| `--pdf-filename-pattern` | `pdf_filename_pattern` | str | `household-water-usage-{start_date}-to-{end_date}.pdf` |
| `--pdf-path` | `pdf_path` | path | `null` (disabled; overrides dir+pattern when set) |

---

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success — graph rendered (and PDF saved if `--save-pdf`) |
| `1` | Any failure — always accompanied by `[✗]` message with "Likely cause:" |

---

## Terminal Output Convention

Every step produces a status line:

| Symbol | Color | Meaning |
|--------|-------|---------|
| `[✓]` | green | Step succeeded |
| `[→]` | cyan | Step in progress |
| `[!]` | yellow | Warning / skip (non-fatal) |
| `[✗]` | red | Error (fatal; exit 1) |

---

## Key Behaviors

1. **Credentials discovery order**: `~/.config/home-water-usage/credentials.json` →
   `$GMAIL_CREDENTIALS_PATH` → `--credentials-path`. Failure at all three aborts with setup guide.
2. **Buffer emails**: Body dates within `buffer_email_count` days of range edges are parsed
   and cached but NOT plotted.
3. **No exceedances in range**: Render averages-only graph; print `[!]` notice. Do NOT abort.
4. **No emails in Gmail at all**: Abort with `[✗]`.
5. **PDF + window**: PDF written first (synchronous), then `plt.show()` — no user interaction required between.
