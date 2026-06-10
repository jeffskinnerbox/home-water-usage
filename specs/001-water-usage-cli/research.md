# Research: Home Water Usage CLI

**Phase 0 Output** | **Date**: 2026-06-09 | **Plan**: [plan.md](./plan.md)

All decisions below are derived from the spec, constitution, and PRD. No NEEDS CLARIFICATION
items remain — the spec is fully resolved.

---

## 1. Gmail OAuth 2.0 Token Flow

**Decision**: Use `google-auth-oauthlib` `InstalledAppFlow` with `gmail.readonly` scope;
cache token in `~/.config/home-water-usage/token.json`; set `chmod 600` immediately after write.

**Rationale**: `InstalledAppFlow.from_client_secrets_file()` is the standard pattern for
Desktop OAuth apps. `Credentials.to_json()` / `Credentials.from_authorized_user_file()`
handles token serialization. The `600` permission prevents token theft on multi-user Linux
systems (FR-017).

**Implementation pattern**:

```python
# auth.py — simplified flow
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
import os, stat

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def get_credentials(credentials_path: str, token_path: str) -> Credentials:
    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
        creds = flow.run_local_server(port=0)
        with open(token_path, "w") as f:
            f.write(creds.to_json())
        os.chmod(token_path, stat.S_IRUSR | stat.S_IWUSR)  # 600
    return creds
```

**Alternatives considered**: Service account credentials — rejected (requires domain-wide
delegation, not available for personal Gmail); `google-auth` device flow — rejected
(desktop app flow is simpler and standard for single-user tools).

---

## 2. Gmail API Query & Buffer Classification

**Decision**: Single widened-date-window API query using `after:` / `before:` received-date
operators combined with `from:` sender filter. Post-fetch, classify emails by body date only.

**Rationale**: Gmail API does not support querying by email body date. A single widened
query (start − buffer_days to end + buffer_days) minimizes API calls. Body date is then used
to classify: in-range (plot), buffer (cache only), out-of-window (discard). Spec FR-005/FR-006.

**Gmail query format**:

```
from:no-reply@leesburgva.gov after:{widened_start_unix} before:{widened_end_unix}
```

The `after:` and `before:` operators accept Unix timestamps (seconds since epoch).

**Pagination**: `messages.list` returns up to 500 results per page via `nextPageToken`.
All pages must be fetched before classification.

**Alternatives considered**: Separate queries per month — rejected (more API calls, no benefit
when a single widened query covers all needed emails); label-based filtering — rejected
(no guarantee utility emails are labeled).

---

## 3. Exponential Backoff for Gmail API

**Decision**: Use `googleapiclient.errors.HttpError` + manual retry loop with exponential
backoff; respect `max_retries` from Config.

**Pattern**:

```python
import time
from googleapiclient.errors import HttpError

def fetch_with_retry(api_call, max_retries: int):
    for attempt in range(max_retries):
        try:
            return api_call()
        except HttpError as e:
            if e.status_code in (429, 500, 503) and attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                raise
```

**Alternatives considered**: `google-api-python-client`'s built-in retry via
`googleapiclient.http.build_from_document` — available but less transparent; manual
loop is simpler to test and mock.

---

## 4. Email Body Parsing — Regex with Named Capture Groups

**Decision**: Compile the `email_body_pattern` from `parameter_values.yaml` at startup;
validate that required named groups (`month`, `day`, `year`, `gallons`) are present; abort
with `[✗]` if any required group is missing.

**Default pattern** (verbatim from FR-007):

```
On (?P<month>\w+) (?P<day>\d{1,2}), (?P<year>\d{4}), your water usage of (?P<gallons>\d+) exceeded your threshold of (?P<threshold>\d+) for account (?P<account>\d+)\.
```

**Date construction**: Parse `month/day/year` string with `datetime.strptime` using
`"%B %d %Y"` format. Invalid dates (e.g., "June 32") raise `ValueError` → skip + `[!]` warning.

**Alternatives considered**: `email` stdlib for MIME parsing — unnecessary since the
relevant data is in the plain-text body; `dateutil.parser` — adds a dependency for no gain
since the format is fixed.

---

## 5. HistoryCache CSV — Append-Only Merge Strategy

**Decision**: `water-usage-history.csv` with columns `date,gallons`, sorted ascending by
date. On merge: load existing cache into a `dict[date, int]`, add new records (new dates
only — existing dates never overwritten), sort by date, write back. On corrupt/unparseable
file: log `[!]`, delete, rebuild from Gmail.

**Partial-overlap strategy** (FR-018):
- Determine `latest_cached_date` from last row of `water-usage-history.csv`
- Request only dates after `latest_cached_date` from Gmail
- Merge new records; append-only (no overwrite of existing dates)

**Deduplication**: `date` is the unique key. First occurrence wins (matching FR-007 body-date
dedup rule).

**Alternatives considered**: SQLite — adds `sqlite3` dependency and schema migration
complexity for a single-table two-column dataset; Parquet — binary format, harder to inspect
and debug manually.

---

## 6. Seaborn Line Graph — Gaps for Missing Days

**Decision**: Build a complete date-indexed `pd.DataFrame` for the requested range; fill
missing days with `NaN`. Seaborn/Matplotlib naturally breaks the line at `NaN` values,
producing the "pure missing segment" behavior specified in FR-009.

**Pattern**:

```python
import pandas as pd
import seaborn as sns

full_range = pd.date_range(start_date, end_date, freq="D")
df = pd.DataFrame({"date": full_range}).merge(records_df, on="date", how="left")
# gallons is NaN for missing days → line breaks automatically
ax = sns.lineplot(data=df, x="date", y="gallons")
```

**Alternatives considered**: Masked arrays — more complex, same visual result; plotting
only present points and connecting them — would NOT produce breaks (lines would span gaps).

---

## 7. Y-Axis 99th Percentile Cap (FR-020)

**Decision**: Compute `np.percentile(gallons_values, config.y_axis_percentile_cap)` as
`y_max`. If any values exceed `y_max`, clip them to `y_max` for display and print `[!]`
notice listing clipped dates/values. If `y_axis_max` is set in Config, skip percentile
computation and use it directly.

**Pattern**:

```python
cap = np.percentile(gallons, config.y_axis_percentile_cap)
clipped = [(d, g) for d, g in zip(dates, gallons) if g > cap]
if clipped:
    df["gallons"] = df["gallons"].clip(upper=cap)
    status.warn(f"Clipped {len(clipped)} outlier(s) to y-axis cap ({cap:.0f} gal)")
ax.set_ylim(top=cap)
```

---

## 8. AutoDateLocator for X-Axis Tick Density

**Decision**: Apply `mdates.AutoDateLocator()` + `mdates.DateFormatter(config.date_format)`
to the x-axis. This auto-selects appropriate tick spacing for any date range length (days,
weeks, months, years) without custom logic.

**Pattern**:

```python
import matplotlib.dates as mdates
ax.xaxis.set_major_locator(mdates.AutoDateLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter(config.date_format))
```

---

## 9. Pluggable Renderer Pattern

**Decision**: `graph.py` dispatches to renderer modules by `chart_type` key using
`importlib.import_module`. Each renderer module in `renderers/` exposes exactly one public
function: `render(records, averages, config) → None`. Default renderer: `line`.

**Pattern**:

```python
import importlib

def dispatch_render(records, averages, config):
    module = importlib.import_module(
        f"home_water_usage.renderers.{config.chart_type}"
    )
    module.render(records, averages, config)
```

**Alternatives considered**: Class-based plugin registry — more complex, no benefit for a
single-function interface; entry points via `pyproject.toml` — appropriate for third-party
plugins, unnecessary for a single-user tool.

---

## 10. argparse + PyYAML Config Merge

**Decision**: Load `parameter_values.yaml` first into a dict; build argparse namespace with
all defaults set to `None`; after parsing, merge: CLI value (if not None) takes precedence
over YAML default. Result is passed to a `Config` dataclass.

**Pattern**:

```python
import yaml, argparse
from dataclasses import dataclass

with open("parameter_values.yaml") as f:
    yaml_defaults = yaml.safe_load(f)

parser = argparse.ArgumentParser()
# all defaults=None so we can detect "was this flag provided?"
parser.add_argument("--start-date", default=None)
# ... all other flags

args = parser.parse_args()
merged = {k: (getattr(args, k) if getattr(args, k) is not None else v)
          for k, v in yaml_defaults.items()}
config = Config(**merged)
```

---

## 11. Offline Test Strategy

**Decision**: All Gmail API interactions mocked via `unittest.mock.patch`. Fixture JSON
files in `tests/fixtures/` represent realistic Gmail `messages.list` and `messages.get`
API responses. Graph tests use `matplotlib.use("Agg")` backend and assert `Figure`/`Axes`
properties (title, axis labels, line count, ylim) — no pixel comparison.

**Fixture structure**:

```
tests/fixtures/
├── messages_list.json        # {"messages": [{"id": "abc", "threadId": "..."}], ...}
├── messages_list_empty.json  # {"messages": [], "resultSizeEstimate": 0}
├── message_detail_1.json     # Full message with body matching default pattern
├── message_detail_2.json     # Duplicate date variant (triggers dedup warning)
└── message_detail_bad.json   # Non-matching body (triggers skip warning)
```

---

## 12. uv Project / Console Script Setup

**Decision**: `pyproject.toml` with `[project.scripts]` entry point:

```toml
[project.scripts]
home-water-usage = "home_water_usage.cli:main"
```

`uv sync` installs in editable mode; `uv run home-water-usage` invokes `cli.main()`.

**Python version constraint**: `requires-python = ">=3.12"` in `pyproject.toml`.
