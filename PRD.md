# Product Requirements Document

**Product/Feature Name:** Home Water Usage CLI (`home-water-usage.py`)<br>
**Status:** Approved<br>
**Author:** Jeff Irland<br>
**Stakeholders:** Jeff Irland (sole user)<br>
**Date Created:** 2026-06-09<br>
**Last Updated:** 2026-06-09<br>
**Version:** 1.1

---

## Executive Summary

**One-liner:** A Python CLI that pulls daily water-usage alert emails from Gmail, parses consumption data, and renders an interactive, seasonally-annotated line graph.

**Overview:**
Leesburg, VA's water utility emails `waterusagejirland@gmail.com` only when daily water usage exceeds the configured threshold for account `40002423000`. No email is sent on normal (within-threshold) days. Today there is no automated way to visualize trends or seasonal patterns across those alert emails — a user must manually open dozens of messages and transcribe numbers into a spreadsheet.

`home-water-usage.py` eliminates that friction. Given a date range on the command line, the tool authenticates with Gmail via OAuth, fetches the relevant notification emails (plus three buffer messages on each side for delivery-lag tolerance and seasonal average anchoring), parses consumption figures from the email body date (not received date), persists results to a local CSV temp file, then renders a Seaborn line graph overlaid with dotted horizontal lines for annual and per-season (Winter/Spring/Summer/Fall) averages. Days with no email appear as breaks in the line with a legend note explaining the gap. The graph pops up as an interactive window; a date-range-stamped PDF is optionally saved simultaneously.

Every visual and behavioral default lives in `parameter_values.yaml` and can be overridden at the command line, so the tool stays fully customizable without touching source code.

**Quick Facts:**
* **Target Users:** Jeff Irland — single Linux desktop user
* **Problem Solved:** No easy way to visualize household daily water-usage trends or seasonal baselines
* **Key Metric:** Successful end-to-end graph render on every valid invocation
* **Target Launch:** Q3 2026 (nights/weekends pace; no hard deadline)

---

## Table of Contents

1. [Problem Statement](#problem-statement)
2. [Goals & Objectives](#goals--objectives)
3. [User Personas](#user-personas)
4. [User Stories & Requirements](#user-stories--requirements)
5. [Success Metrics](#success-metrics)
6. [Scope](#scope)
7. [Technical Considerations](#technical-considerations)
8. [Design & UX Requirements](#design--ux-requirements)
9. [Timeline & Milestones](#timeline--milestones)
10. [Risks & Mitigation](#risks--mitigation)
11. [Dependencies & Assumptions](#dependencies--assumptions)
12. [Open Questions](#open-questions)

---

## Problem Statement

### The Problem

The Leesburg, VA water utility sends an email to `waterusagejirland@gmail.com` only on days when household water consumption exceeds the configured threshold. There is no dashboard, no trend view, and no seasonal comparison from the utility. Identifying unusually high usage, seasonal patterns, or year-over-year trends requires manually reading dozens of emails.

### Current State

No tooling exists to extract or visualize this data. All historical data is locked inside Gmail in unstructured plain-text email bodies.

### Impact

**User Impact:**
* Cannot quickly see whether current usage is above/below seasonal norms
* Cannot identify anomalous usage events (e.g., leaks) at a glance
* No way to track conservation efforts over a date range

**Personal/Financial Impact:**
* Water overages carry financial penalties; early anomaly detection reduces costs
* Understanding seasonal baselines enables proactive conservation planning

### Why Now?

A growing historical corpus of alert emails is accumulating in Gmail. The sooner the tool is built, the richer the retrospective view.

---

## Goals & Objectives

### User Goals

1. **Visualize trends:** See threshold-exceeding usage events plotted over any requested date range
2. **Understand seasonal norms:** Compare daily usage against annual and per-season averages computed from all available history
3. **Detect anomalies:** Spot days that spike far above seasonal baselines
4. **Export results:** Optionally save graphs as date-range-stamped PDFs

### Non-Goals

* Sending alerts or notifications (display-only tool)
* Uploading data to any cloud service or remote database
* Supporting multiple utility accounts simultaneously
* Providing a GUI settings editor
* Automated scheduling or cron integration

---

## User Personas

### Primary Persona: Home Utility Tracker

**Demographics:**
* Role: Homeowner / Linux power-user
* Tech savviness: High
* Environment: Linux terminal session

**Behaviors:**
* Runs CLI tools to automate repetitive tasks
* Prefers configurable defaults over hardcoded behavior
* Expects clear, colorful terminal feedback at every step

**Needs & Motivations:**
* Understand whether household water usage is trending up, down, or stable
* Identify leaks or high-usage events quickly
* Produce a clean PDF for record-keeping

**Pain Points:**
* Gmail UI is slow for bulk message inspection
* No built-in trend view from the water utility portal
* Manually counting gallons is tedious and error-prone

**Quote:** _"Just show me a graph — I don't want to open 90 emails."_

---

## User Stories & Requirements

### Epic 1: Data Acquisition

#### Must-Have Stories (P0)

##### Story 1: Gmail Authentication

```
As a home user,
I want the tool to authenticate with my Gmail account via OAuth,
So that it can securely access water-usage notification emails.
```

**Acceptance Criteria:**
* [ ] Credentials file discovered in order: `~/.config/home-water-usage/credentials.json` → `$GMAIL_CREDENTIALS_PATH` → `--credentials-path` flag
* [ ] If all three fail, tool aborts with a clear error describing each path tried and how to set up credentials
* [ ] First run opens a browser for OAuth consent; token cached to configurable path (default: `~/.config/home-water-usage/token.json`)
* [ ] Cached token refreshed automatically when expired
* [ ] Token never printed to stdout or logs
* [ ] `rich`-formatted status message printed at auth step

**Priority:** P0 | **Effort:** M

---

##### Story 2: Email Fetch by Date Range

```
As a home user,
I want to specify a start and end date,
So that the tool fetches only the relevant water-usage emails plus buffer.
```

**Acceptance Criteria:**
* [ ] `--start-date` and `--end-date` CLI args accepted (format: `YYYY-MM-DD`)
* [ ] Tool fetches matching emails **plus 3 buffer emails before start and 3 after end** (for delivery-lag tolerance and seasonal average anchoring)
* [ ] Buffer emails are parsed and used for averages but **not plotted**
* [ ] Date used for parsing and plotting is the date in the **email body**, not the received date
* [ ] Gmail search scoped to `from:no-reply@leesburgva.gov` (configurable via `gmail_query_filter` in YAML)
* [ ] If zero emails found: abort with message distinguishing "no emails in range" from "emails found but none parsed"
* [ ] On Gmail API failure: retry with exponential backoff (`max_retries`, `retry_backoff_seconds` in YAML); abort with clear error after retries exhausted
* [ ] Status printed: emails found, date range covered, buffer count

**Priority:** P0 | **Effort:** M

---

##### Story 3: Email Parsing

```
As a home user,
I want the tool to extract usage figures from email bodies,
So that I have structured data to plot.
```

**Acceptance Criteria:**
* [ ] Parses body pattern: `"On {month} {day}, {year}, your water usage of {gallons} exceeded your threshold of {threshold} for account {account}."`
* [ ] No email is sent on non-exceed days — parser handles only the "exceeded" format
* [ ] Parsed records saved to temp file as CSV: `date,gallons`
* [ ] Unparseable emails logged as warnings with raw body included
* [ ] Account number validated against `account_number` in YAML; mismatch logged as warning

**Priority:** P0 | **Effort:** S

---

#### Should-Have Stories (P1)

##### Story 4: Temp File Management

```
As a home user,
I want temp files cleaned up after graph generation,
So that I don't accumulate stale data files.
```

**Acceptance Criteria:**
* [ ] `delete_temp_files: true` default in `parameter_values.yaml`
* [ ] `--no-delete-temp` CLI flag overrides default
* [ ] Temp directory path configurable via `temp_dir` in YAML and `--temp-dir` flag
* [ ] Status message printed when temp files are deleted or retained

**Priority:** P1 | **Effort:** XS

---

### Epic 2: Visualization

#### Must-Have Stories (P0)

##### Story 5: Line Graph of Daily Usage

```
As a home user,
I want a line graph of daily water usage over my requested date range,
So that I can see consumption trends at a glance.
```

**Acceptance Criteria:**
* [ ] X-axis labeled "Date"; tick format configurable via `date_format` in YAML (default: `"%b %d"`)
* [ ] Y-axis labeled "Household Water Usage"; scale auto-fit to data by default (`y_axis_min`/`y_axis_max` in YAML default `null`)
* [ ] Overall graph title: "Household Water Usage" (configurable)
* [ ] Days with no email appear as **line breaks** (no interpolation); legend note: _"gaps = usage within threshold"_ (text configurable via `gap_label` in YAML)
* [ ] Graph pops up in an interactive window on execution
* [ ] Line color, width, and style configurable in `parameter_values.yaml`

**Priority:** P0 | **Effort:** M

---

##### Story 6: Seasonal Average Overlays

```
As a home user,
I want horizontal dotted lines showing annual and seasonal usage averages,
So that I can compare daily values against my own historical baseline.
```

**Acceptance Criteria:**
* [ ] Up to five dotted horizontal lines: Annual, Winter, Spring, Summer, Fall
* [ ] Season definitions (calendar months): Winter = Dec/Jan/Feb, Spring = Mar/Apr/May, Summer = Jun/Jul/Aug, Fall = Sep/Oct/Nov
* [ ] Averages computed from **all available Gmail history**, not just the displayed date range
* [ ] If a season has no data, its line is **silently omitted**; terminal status message printed (e.g., `[!] No Winter data — skipping Winter average`)
* [ ] Each line uniquely colored and labeled in the legend
* [ ] Legend placement configurable via `legend_location` in YAML (default: `"best"`)
* [ ] Line colors, widths, and dash style configurable in `parameter_values.yaml`

**Priority:** P0 | **Effort:** M

---

#### Should-Have Stories (P1)

##### Story 7: PDF Export

```
As a home user,
I want to optionally save the graph as a PDF,
So that I have a printable or shareable record.
```

**Acceptance Criteria:**
* [ ] `save_pdf: false` default in `parameter_values.yaml`
* [ ] `--save-pdf` / `--pdf-path` CLI flags override default
* [ ] PDF and interactive window rendered **simultaneously** (not sequentially)
* [ ] Default filename pattern: `household-water-usage-{start_date}-to-{end_date}.pdf` (configurable via `pdf_filename_pattern` in YAML)
* [ ] PDF saved to configurable `pdf_output_dir` (default: current directory)
* [ ] DPI configurable via `figure_dpi` in YAML
* [ ] Status message `[✓] PDF saved to <path>` printed before window opens

**Priority:** P1 | **Effort:** S

---

### Functional Requirements

| Req ID | Description | Priority |
|--------|-------------|----------|
| FR-001 | CLI entry point: `home-water-usage` (console script via `uv`) | Must Have |
| FR-002 | All defaults stored in `parameter_values.yaml` | Must Have |
| FR-003 | Every YAML default overridable via CLI flag | Must Have |
| FR-004 | Gmail OAuth with token caching; credentials discovered via 3-step fallback | Must Have |
| FR-005 | Fetch emails by body date + 3 buffer on each side | Must Have |
| FR-006 | Parse gallons and body-date from "exceeded" email format only | Must Have |
| FR-007 | Persist parsed data to CSV temp file (`date,gallons`) | Must Have |
| FR-008 | Seaborn line graph with broken lines for missing days | Must Have |
| FR-009 | Annual + up to 4 seasonal average overlays (dotted lines); skip seasons with no data | Must Have |
| FR-010 | Interactive pop-up graph window | Must Have |
| FR-011 | Optional PDF export (simultaneous with window) | Should Have |
| FR-012 | Configurable temp file deletion | Should Have |
| FR-013 | `rich`-formatted colored status messages at every workflow step | Must Have |
| FR-014 | Structured error messages with root-cause description on all failures | Must Have |
| FR-015 | Gmail API retry with exponential backoff; abort after `max_retries` | Must Have |

### Non-Functional Requirements

| Req ID | Category | Description | Target |
|--------|----------|-------------|--------|
| NFR-001 | Usability | All status output via `rich` with color and step indicators | Required |
| NFR-002 | Reliability | Clear error + root-cause on any failure path | Required |
| NFR-003 | Testability | TDD via `pytest`; 100% offline (mocked Gmail API + fixture JSON) | Required |
| NFR-004 | Test coverage | ≥ 80% line coverage | Required |
| NFR-005 | Configurability | Zero hardcoded display/behavior values | Required |
| NFR-006 | Portability | Linux terminal; Matplotlib pop-up requires display (not headless) | Required |
| NFR-007 | Security | OAuth token never logged or printed; credentials never committed | Required |

---

## Success Metrics

### Primary Metric

**Metric:** End-to-end successful graph render
**Definition:** `home-water-usage --start-date X --end-date Y` exits 0, renders a graph window, and (when enabled) saves a correctly named PDF
**Target:** 100% of valid invocations succeed

### Secondary Metrics

| Metric | Target |
|--------|--------|
| Test coverage | ≥ 80% line coverage via `pytest` |
| CLI flag / YAML key parity | 100% — every YAML key has a corresponding CLI override |
| Seasonal averages rendered | All seasons with data shown; missing seasons omitted with terminal notice |
| Error messages include root cause | 100% of caught exception paths |
| Retry on transient Gmail failures | Retries before abort on network errors |

---

## Scope

### In Scope — Phase 1 (MVP)

* Gmail OAuth authentication with 3-step credentials discovery and token caching
* Email fetch filtered to Leesburg water-usage notifications for a date range + 3 buffer emails each side
* Body-date parsing and gallon extraction (exceeded-threshold format only)
* CSV temp file persistence
* Seaborn line graph with broken lines for data gaps
* Annual + seasonal average overlays (skip seasons with no data)
* Interactive pop-up graph window
* `parameter_values.yaml` with CLI overrides for all settings
* `rich`-formatted colored status output
* Structured error messages with root-cause descriptions
* Gmail API retry with exponential backoff
* TDD test suite — 100% offline, ≥ 80% coverage

### In Scope — Phase 2

* PDF export (simultaneous with window)
* Temp file auto-deletion option
* Configurable output directory

### Out of Scope

* Push alerts or notifications — tool is display-only
* Multi-account or multi-utility support
* Web or desktop GUI
* Remote or shared data storage
* Automated scheduling / cron integration
* Interpolation across data gaps

### Future Considerations

* Year-over-year comparison view
* Anomaly detection / spike flagging
* Bar chart or box-plot seasonal views

---

## Technical Considerations

### High-Level Architecture

```
home-water-usage/
├── pyproject.toml           uv project; console script entry point
├── parameter_values.yaml    all defaults
├── src/
│   └── home_water_usage/
│       ├── cli.py           argparse; merges YAML defaults + CLI flags
│       ├── auth.py          Gmail OAuth (credentials 3-step discovery, token cache)
│       ├── fetch.py         email fetch, date-range filter, buffer logic
│       ├── parse.py         email body → {date, gallons} records
│       ├── storage.py       CSV temp file read/write/delete
│       ├── graph.py         Seaborn line graph + seasonal overlays
│       └── status.py        rich-formatted status/error output helpers
├── tests/
│   ├── fixtures/            canned Gmail API JSON responses
│   ├── test_parse.py
│   ├── test_storage.py
│   ├── test_graph.py        matplotlib.use("Agg"); property assertions only
│   ├── test_cli.py
│   ├── test_fetch.py        mocked Gmail API
│   └── test_integration.py  full run against local fixture set
└── constitution.md          project principles (referenced by CLAUDE.md)
```

### Technology Stack

* **Language:** Python 3.12+
* **Workflow / env management:** `uv` (`pyproject.toml`, `uv sync`)
* **Graphing:** Seaborn + Matplotlib
* **Gmail access:** `google-api-python-client`, `google-auth-oauthlib`
* **CLI:** `argparse` (stdlib)
* **Config:** `PyYAML`
* **Terminal output:** `rich`
* **Testing:** `pytest`, `pytest-cov`, `unittest.mock`

### `parameter_values.yaml` — Complete Default Key Set

```yaml
# Graph appearance
graph_title: "Household Water Usage"
graph_width: 14
graph_height: 6
data_line_color: "steelblue"
data_line_width: 1.5
data_line_style: "-"
y_axis_min: null
y_axis_max: null
date_format: "%b %d"

# Seasonal average lines
annual_avg_color: "black"
winter_avg_color: "blue"
spring_avg_color: "green"
summer_avg_color: "red"
fall_avg_color: "orange"
avg_line_width: 1.0
avg_line_style: "--"
legend_location: "best"
gap_label: "gaps = usage within threshold"

# Fonts
title_font_size: 16
axis_label_font_size: 12
tick_font_size: 10

# PDF export
save_pdf: false
pdf_output_dir: "."
pdf_filename_pattern: "household-water-usage-{start_date}-to-{end_date}.pdf"
figure_dpi: 150

# Gmail / auth
gmail_query_filter: "from:no-reply@leesburgva.gov"
credentials_path: "~/.config/home-water-usage/credentials.json"
token_path: "~/.config/home-water-usage/token.json"
account_number: "40002423000"
buffer_email_count: 3

# Behavior
delete_temp_files: true
temp_dir: "/tmp/home-water-usage"
max_retries: 3
retry_backoff_seconds: 2
```

### Security Requirements

* Gmail OAuth 2.0 only — no password storage
* Token stored at `token_path` (default: `~/.config/home-water-usage/token.json`)
* Token and credentials never printed to stdout or logs
* `credentials.json` never committed to version control (add to `.gitignore`)

### Testing Strategy

* **100% offline** — no live Gmail calls in any test
* Gmail API responses simulated via fixture JSON files in `tests/fixtures/`
* Graph tests use `matplotlib.use("Agg")` to suppress display; assert figure properties (title, axis labels, line count, line styles)
* No snapshot/pixel tests — property assertions only (resilient to font/DPI changes)

---

## Design & UX Requirements

### Terminal UX Principles

* Every workflow step emits a `rich`-formatted status line
* Success: `[✓]` in green; In-progress: `[→]` in cyan; Warning: `[!]` in yellow; Error: `[✗]` in red
* Errors include a "Likely cause:" line and remediation hint
* No silent failures

### Primary Workflow (Happy Path)

1. `home-water-usage --start-date 2026-01-01 --end-date 2026-06-09`
2. `[→] Locating credentials...` → `[✓] Authenticated with Gmail`
3. `[→] Fetching emails 2026-01-01 to 2026-06-09 (+3 buffer each side)...` → `[✓] 47 emails found (44 in range, 3+3 buffer)`
4. `[→] Parsing email bodies...` → `[✓] 47 records parsed`
5. `[→] Computing seasonal averages...` → `[✓] Annual, Spring, Summer averages computed` + `[!] No Winter data — skipping Winter average`
6. `[→] Rendering graph...` → `[✓] PDF saved to ./household-water-usage-2026-01-01-to-2026-06-09.pdf` (if enabled)
7. Graph window opens
8. User closes window → `[✓] Done`

### Graph Layout

* **Title (top):** "Household Water Usage"
* **Y-axis label:** "Household Water Usage" (gallons); auto-scaled
* **X-axis label:** "Date"; tick format `"%b %d"` by default
* **Primary series:** Daily usage line; breaks where no email exists
* **Legend note:** "gaps = usage within threshold"
* **Overlay lines:** Up to 5 horizontal dotted lines (Annual, Winter, Spring, Summer, Fall); missing seasons omitted
* **Legend placement:** `"best"` (inside, auto-placed) by default; configurable

---

## Timeline & Milestones

Pace: nights/weekends. No hard deadline.

| Phase | Deliverables | Estimated Duration |
|-------|-------------|-------------------|
| **0 — Setup** | Google Cloud project, Gmail API enabled, `credentials.json` obtained, `uv` project scaffolded | 1 session |
| **1 — Auth & Fetch** | OAuth working, emails fetched & parsed, CSV written, tests passing | 1–2 weeks |
| **2 — Graph** | Seaborn line graph with seasonal overlays, gap handling, axes, legend | 1 week |
| **3 — Config & CLI** | Full YAML + CLI override parity, `rich` status output, error handling, retries | 1 week |
| **4 — PDF & Cleanup** | PDF export, temp-file deletion, test coverage ≥ 80% | 3–5 days |
| **5 — Hardening** | End-to-end integration test, `constitution.md`, `CLAUDE.md` updated | 2–3 days |

**Total:** ~6 weeks at casual nights/weekends pace.

> **Note:** Phase 0 (Google Cloud / API setup) can consume a full session before any application code is written. Budget for it explicitly.

---

## Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|------------|------------|
| Gmail API quota exceeded | Medium | Low | Fetch only requested range + buffer; cache CSV to avoid re-fetching |
| Utility changes email body wording | High | Low | Regex parser with clear warning on parse failure; raw body logged |
| OAuth token revoked / expired | Medium | Medium | Auto-refresh logic; clear re-auth instructions on failure |
| Google Cloud / OAuth setup takes longer than expected | Medium | High | Treat Phase 0 as a dedicated session; document setup steps in `CLAUDE.md` |
| Matplotlib window unavailable (headless environment) | Low | Low | Tool is intended for interactive desktop use; document requirement |

---

## Dependencies & Assumptions

### Dependencies

* [ ] Google Cloud project with Gmail API enabled + `credentials.json` obtained
* [ ] `uv` installed on the Linux machine
* [ ] Active Gmail account `waterusagejirland@gmail.com` with historical notification emails
* [ ] Linux desktop with display available (Matplotlib pop-up window)

### Assumptions

* Utility emails only on threshold-exceed days; no email = no data point for that day
* Email body always follows: `"On {month} {day}, {year}, your water usage of {N} exceeded your threshold of {T} for account {A}."`
* Sufficient Gmail history exists to compute at least some seasonal averages (missing seasons silently skipped)
* Single Gmail account; single water account number
* Tool run interactively in a terminal with a display available

---

## Open Questions

All questions resolved. No open items.

---

## Appendix

### Glossary

* **Usage date:** Date in the email body (e.g., "On June 06, 2026") — not the email received date
* **Buffer emails:** 3 emails fetched before the start date and 3 after, used for delivery-lag tolerance and seasonal average anchoring; not plotted
* **Seasonal averages:** Mean daily usage per season (Winter/Spring/Summer/Fall) computed from all available Gmail history; seasons with no data are skipped
* **Temp file:** Local CSV (`date,gallons`) written during a run; deleted by default after graph is displayed
* **Exceeded email:** The only email format sent by the utility — only when daily usage exceeds the configured threshold

### `constitution.md` vs `CLAUDE.md`

* `constitution.md` — stable project charter: principles, software/hardware components, non-negotiable constraints
* `CLAUDE.md` — operational AI-session context: how to run tests, invoke the tool, key file locations; references `constitution.md`

### Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-06-09 | Jeff Irland | Initial draft |
| 1.1 | 2026-06-09 | Jeff Irland | All 20 grilling decisions folded in; Open Questions closed |
