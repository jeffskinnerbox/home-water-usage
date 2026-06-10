# Feature Specification: Home Water Usage CLI

**Feature Branch**: `001-water-usage-cli`

**Created**: 2026-06-09

**Status**: Draft

**Input**: PRD.md v1.1 — Home Water Usage CLI (`home-water-usage.py`)

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — View Daily Usage Graph Over a Date Range (Priority: P1)

A homeowner wants to understand their household water consumption trends over a chosen
period. They run the tool from a terminal, supply a start and end date, and a line graph
pops up showing every day the utility reported an exceedance, with gaps on days usage
was within threshold. Five horizontal dotted lines overlay the chart showing annual,
winter, spring, summer, and fall average usage computed from all available history.

**Why this priority**: This is the entire raison d'être of the tool. Without it there
is no product.

**Independent Test**: Given at least one water-usage alert email exists in Gmail for the
requested range, running `home-water-usage --start-date X --end-date Y` opens a graph
window that shows the correct data points, correct axis labels, and correct seasonal
average overlays — confirming the full pipeline works end-to-end.

**Acceptance Scenarios**:

1. **Given** valid start/end dates and Gmail history containing exceedance emails,
   **When** the user runs `home-water-usage --start-date 2026-01-01 --end-date 2026-06-09`,
   **Then** an interactive graph window opens with title "Household Water Usage",
   x-axis "Date", y-axis "Household Water Usage", a usage line with breaks on
   no-data days, and up to five seasonal average dotted lines.

2. **Given** some seasons have no historical data,
   **When** the graph is rendered,
   **Then** those seasons' average lines are silently omitted and a terminal status
   message explains each omission (e.g., `[!] No Winter data — skipping Winter average`).

3. **Given** a date range where no exceedance emails exist,
   **When** the user runs the tool,
   **Then** the tool aborts with a `[✗]` error message distinguishing "no emails found
   in range" from "emails found but none could be parsed."

---

### User Story 2 — Override Display Settings via CLI Flags (Priority: P2)

A homeowner wants to tweak the graph's appearance or behavior for a specific run without
editing any configuration file — for example, adjusting the date range, disabling temp
file deletion, or changing the output directory for a PDF.

**Why this priority**: Without CLI override support the tool is only as flexible as the
YAML file, blocking quick one-off customizations.

**Independent Test**: Running `home-water-usage` with a flag that overrides a YAML default
(e.g., `--no-delete-temp`) produces behavior matching the flag value, not the YAML value,
confirming the override mechanism works for at least one key.

**Acceptance Scenarios**:

1. **Given** `delete_temp_files: true` in `parameter_values.yaml`,
   **When** the user passes `--no-delete-temp`,
   **Then** the CSV temp file persists after the run.

2. **Given** any YAML default key,
   **When** a corresponding CLI flag is supplied with a different value,
   **Then** the CLI value takes precedence for that run only; the YAML file is unchanged.

---

### User Story 3 — Export Graph as PDF (Priority: P3)

A homeowner wants to save a printable record of their water usage graph for a specific
date range.

**Why this priority**: Useful but non-blocking; the core value is the interactive graph.

**Independent Test**: Running `home-water-usage --start-date X --end-date Y --save-pdf`
produces a PDF file named `household-water-usage-X-to-Y.pdf` in the current directory
and the terminal prints `[✓] PDF saved to <path>` before the graph window opens.

**Acceptance Scenarios**:

1. **Given** `--save-pdf` is passed,
   **When** the graph is rendered,
   **Then** a PDF file `household-water-usage-{start}-to-{end}.pdf` is saved to
   `pdf_output_dir` (default: current directory) simultaneously with the window opening.

2. **Given** the user supplies `--pdf-path /custom/dir/report.pdf`,
   **When** the graph is rendered,
   **Then** the PDF is saved to the specified path and filename.

---

### Edge Cases

- What happens when Gmail returns a network error mid-fetch?
  → Retry with exponential backoff up to `max_retries`; abort with `[✗]` + "Likely cause" after retries exhausted.
- What happens when `credentials.json` is not found at any of the three discovery locations?
  → Abort with a `[✗]` message listing each path tried and a setup guide.
- What happens when an email body does not match the expected "exceeded" pattern?
  → Log a `[!]` warning with the raw body; skip that email; continue parsing remaining emails.
- What happens when an email body matches the pattern but contains an invalid date (e.g., "June 32")?
  → Skip the record; log a `[!]` warning with the raw body and the invalid date value extracted.
- What happens when the requested date range is entirely in the future?
  → Zero emails found in Gmail at all → abort with `[✗]` error: "No water-usage emails found in Gmail for this range."
- What happens when emails exist in Gmail but none fall within the plotted range (all days within threshold)?
  → Render graph with seasonal average lines only (no usage line); print `[!]` notice: "No threshold exceedances in the requested range — usage line not shown. All days were within threshold." This message is distinct from the "no emails found" abort.
- What happens when `temp_dir` does not exist or is not writable?
  → Abort immediately with `[✗]` error stating the path, the problem (missing or not writable), and remediation steps (create the directory or change `temp_dir` in `parameter_values.yaml`).
- What happens when only partial seasonal data exists (e.g., tool run in February for the first time)?
  → Seasons with no data are skipped silently; available seasons (e.g., Annual, Fall) are still shown.
- What happens with degenerate date ranges (single-day range or all data points at identical gallon values)?
  → Render normally — a single-day range shows a single dot, flat data shows a flat line; no special handling required.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The tool MUST expose a `home-water-usage` console entry point invokable from any Linux terminal.
- **FR-002**: The tool MUST read all runtime defaults from `parameter_values.yaml` at project root.
- **FR-003**: Every key in `parameter_values.yaml` MUST have a corresponding CLI flag that overrides it for the current run without modifying the file.
- **FR-004**: The tool MUST authenticate with Gmail via OAuth 2.0, discovering `credentials.json` in order: `~/.config/home-water-usage/credentials.json` → `$GMAIL_CREDENTIALS_PATH` → `--credentials-path`; failing all three MUST produce a clear error with setup instructions. The OAuth scope MUST be `https://www.googleapis.com/auth/gmail.readonly` (read-only, minimum necessary privilege).
- **FR-005**: The tool MUST accept `--start-date` and `--end-date` (format `YYYY-MM-DD`) and fetch alert emails using a single Gmail query: the sender filter from `gmail_query_filter` combined with a received-date window widened by `buffer_email_count` days on each side of the requested range. Post-fetch, emails are classified by body date: emails with body dates within `buffer_email_count` days before `--start-date` or after `--end-date` are buffer records (parsed, added to HistoryCache, not plotted); emails with body dates within the requested range are plotted records; emails outside both windows are discarded.
- **FR-006**: The tool MUST use the date in the email body (not the received date) for all data parsing, plotting, and buffer classification. The Gmail query uses a widened received-date window for fetching; body date is the sole basis for determining whether an email falls within the requested range, is a buffer record, or should be skipped.
- **FR-007**: The tool MUST parse email bodies using the regex pattern defined by `email_body_pattern` in `parameter_values.yaml`. The pattern MUST use named capture groups; required groups are `month`, `day`, `year`, and `gallons`; optional groups are `threshold` and `account` (used only for account-validation warnings). The default pattern matches `"On {month} {day}, {year}, your water usage of {gallons} exceeded your threshold of {threshold} for account {account}."` — the only format currently sent by the utility. Changing `email_body_pattern` in YAML MUST update parsing behavior without code changes. If a custom pattern omits a required group, the tool MUST abort with a `[✗]` error identifying the missing group. If the parsed `account` value does not match `account_number` in `parameter_values.yaml`, the tool MUST skip that record and log a `[!]` warning showing the found vs expected account number, then continue parsing remaining emails. If two emails share the same body date, the tool MUST keep the first occurrence (lowest Gmail message ID) and log a `[!]` warning for each duplicate skipped.
- **FR-008**: Parsed records for the current run MUST be written to a CSV temp file named `water-usage-run-{start_date}-{end_date}.csv` in `temp_dir`, with columns `date,gallons`.
- **FR-009**: The tool MUST render a Seaborn line graph. All display strings are YAML defaults overridable via CLI: graph title (default: `"Household Water Usage"`, key: `graph_title`), x-axis label (default: `"Date"`, key: `x_axis_label`), y-axis label (default: `"Household Water Usage"`, key: `y_axis_label`), and gap legend note (default: `"gaps = usage within threshold"`, key: `gap_label`). The usage line MUST break on days with no data (pure missing segments — blank space, no endpoint markers). The gap legend note MUST appear only when at least one gap exists in the displayed range. X-axis tick density MUST be auto-selected based on date range length (`AutoDateLocator`); `date_format` controls the label format applied to auto-selected ticks.
- **FR-010**: The tool MUST overlay up to five horizontal dotted lines (Annual, Winter, Spring, Summer, Fall) computed from all available Gmail history; seasons with no data MUST be silently omitted with a terminal notice per omitted season. This applies at any granularity — including the Annual-only case (only Annual rendered, all four seasonal lines omitted) and any mix of available seasons. A graph with only the Annual average line is valid output. Each season's line color, width, dash style, and legend label MUST be individually configurable in `parameter_values.yaml` (e.g., `winter_avg_color`, `winter_avg_width`, `winter_avg_style`, `winter_avg_label`) with a corresponding CLI flag per property.
- **FR-011**: The graph MUST open as an interactive pop-up window using Matplotlib's default toolbar (zoom, pan, save-to-file); no toolbar customization is required.
- **FR-012**: When `save_pdf` is enabled, the PDF MUST be saved to disk first (synchronous write), then the interactive window opened — no user interaction is required between the two steps. The PDF filename MUST follow `household-water-usage-{start_date}-to-{end_date}.pdf` by default, saved to `pdf_output_dir`. `--pdf-path` overrides the full output path including filename (e.g., `--pdf-path ~/reports/june.pdf`); when supplied it takes precedence over both `pdf_output_dir` and `pdf_filename_pattern`.
- **FR-013**: The tool MUST emit `rich`-formatted colored status messages at every workflow step using the `[✓]` / `[→]` / `[!]` / `[✗]` convention.
- **FR-014**: Every failure path MUST print a `[✗]` error with a "Likely cause:" line and remediation hint, then exit non-zero.
- **FR-015**: Transient Gmail API failures MUST trigger exponential-backoff retries up to `max_retries` before aborting.
- **FR-016**: The run-specific temp CSV MUST be deleted after graph display by default; `--no-delete-temp` MUST preserve it. `--no-delete-temp` affects only the run-specific CSV — the HistoryCache is always persistent and is never affected by this flag. `--no-delete-temp` and `--refresh-cache` are independent flags that may be combined freely; each applies only to its own target with no interaction.
- **FR-017**: After writing `token.json`, the tool MUST set file permissions to `600` (owner read/write only) to prevent token theft on multi-user systems.
- **FR-018**: The tool MUST maintain a persistent `HistoryCache` CSV in `temp_dir` containing all parsed records across all runs. Seasonal averages MUST be computed from this cache rather than re-fetching all Gmail history on every run. On a partial cache overlap (e.g., cache holds Jan–Mar, user requests Feb–Apr), the tool MUST fetch only the uncached portion (dates after the latest cached entry) and merge new records into the existing cache — it MUST NOT re-fetch already-cached dates. The cache MUST be fully rebuilt when `--refresh-cache` is passed or when a requested date predates the earliest cached record. If `--refresh-cache` is passed but Gmail returns no emails newer than the existing cache, the tool MUST continue normally using the existing cache and print `[✓] Cache already up to date`.
- **FR-019**: The graph module MUST implement a pluggable renderer interface where `chart_type` in `parameter_values.yaml` selects the active renderer (default: `"line"`). Each chart type MUST be implemented as a separate module exposing a single function with signature `render(records: list[UsageRecord], averages: list[SeasonalAverage], config: Config) -> None`. New chart types can be added by creating a new module without modifying existing renderer code. `chart_type` MUST be included in `parameter_values.yaml` with default value `"line"` and MUST have a corresponding `--chart-type` CLI flag override.
- **FR-020**: Y-axis auto-scale MUST cap at a configurable percentile of the data (default: 99th, controlled by `y_axis_percentile_cap` in `parameter_values.yaml`). Data points exceeding the cap MUST still be plotted at the cap boundary; the terminal MUST print a `[!]` notice listing the clipped dates and their values. Users may override with explicit `y_axis_max` to bypass percentile capping entirely.

### Key Entities

- **UsageRecord**: A single parsed data point — `{date: date, gallons: int}`. Sourced from one email body. Stored in the run temp CSV and the persistent history cache; plotted on the graph.
- **SeasonalAverage**: Computed mean of all `UsageRecord.gallons` values for a given season across all available history — `{season: str, avg_gallons: float}`. Rendered as a dotted overlay line.
- **Config**: The merged result of `parameter_values.yaml` defaults and CLI flag overrides. Single source of truth for all runtime behavior.
- **HistoryCache**: A persistent local CSV named `water-usage-history.csv` in `temp_dir`, with columns `date,gallons`, sorted by date ascending. Accumulates all parsed `UsageRecord` entries across all runs. Used to compute seasonal averages without re-fetching Gmail history. On merge, only new dates are appended — existing cached dates are never overwritten. Refreshed on cache miss or `--refresh-cache`. If found corrupt or unparseable, the tool logs a `[!]` warning and automatically rebuilds it by re-fetching from Gmail.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The tool successfully renders a graph on 100% of valid invocations. A valid invocation is one where: (1) `--start-date` and `--end-date` are provided in `YYYY-MM-DD` format with start ≤ end, (2) credentials are discoverable via the 3-step lookup, (3) `temp_dir` is writable, and (4) at least one matching email exists in Gmail or the HistoryCache for the requested range (including the no-exceedances case, which renders averages-only).
- **SC-002**: Every YAML configuration key has a working CLI flag override — verified by the test suite with 100% key-parity coverage.
- **SC-003**: The test suite runs to completion with no network calls and achieves ≥ 80% line coverage.
- **SC-004**: On any failure, the user receives a `[✗]` message with a "Likely cause:" line within 3 seconds of the error occurring — no hanging or silent exit.
- **SC-005**: A user unfamiliar with the tool can set it up (Google Cloud credentials + first run) in under 30 minutes by following the instructions printed on credential-discovery failure.
- **SC-006**: When PDF export is enabled, the PDF file MUST exist on disk before `plt.show()` is called (guaranteed by the synchronous write-then-open sequencing in FR-012). Verifiable by comparing the PDF file's filesystem creation timestamp against the window-open event.
- **SC-007**: On a warm cache run (history already cached, no Gmail fetch required), the elapsed time from CLI entry point invocation to `plt.show()` call MUST be under 10 seconds. Gmail API network time is excluded from this measurement as it is network-dependent.
- **SC-008**: 100% of fetched emails whose body matches `email_body_pattern` produce a valid `UsageRecord`. The only legitimate skips are duplicate body dates (keep first, log warning) and invalid date values (log warning); all other matched emails MUST yield a record.

---

## Clarifications

### Session 2026-06-09

- Q: Which Gmail OAuth scope should the tool request? → A: `https://www.googleapis.com/auth/gmail.readonly` (read-only, minimum necessary privilege)
- Q: Should the tool enforce restrictive file permissions on the token file? → A: Yes — tool sets `chmod 600` on `token.json` immediately after writing it
- Q: Should the email body regex pattern be user-configurable or hardcoded? → A: Configurable in `parameter_values.yaml` as `email_body_pattern`
- Q: Should the tool cache full parsed history to avoid re-fetching all emails on every run? → A: Yes — persistent local cache CSV; re-fetch only on cache miss or `--refresh-cache`
- Q: Should `graph.py` be structured to support additional chart types? → A: Yes — pluggable renderer interface; `chart_type` YAML key selects renderer; new types added as new modules

---

## Assumptions

- The Gmail account `waterusagejirland@gmail.com` receives alert emails only when daily usage exceeds the threshold; no email is sent on within-threshold days.
- The email body always follows the exact pattern documented in FR-007; no alternate formats exist.
- Sufficient Gmail history exists to compute at least one seasonal average; missing seasons are silently skipped.
- The tool is always run interactively on a Linux desktop with a display available; headless/server use is out of scope.
- A single Gmail account and a single water account number (`40002423000`) are in use; multi-account support is out of scope.
- The user has `uv` installed and a working Python 3.12+ environment.
- `credentials.json` is obtained by the user from Google Cloud Console before first run; the tool does not automate credential provisioning.
