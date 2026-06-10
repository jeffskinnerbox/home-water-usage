# Quickstart & Validation Guide

## Prerequisites

1. Linux desktop with a display session (`$DISPLAY` set — required for Matplotlib pop-up)
2. `uv` installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
3. `credentials.json` from Google Cloud Console:
   - Create a project → Enable Gmail API → Create OAuth 2.0 credentials (Desktop app)
   - Download → `~/.config/home-water-usage/credentials.json`

## Setup

```bash
cd /path/to/home-water-usage
uv sync
uv run home-water-usage --help   # should print all flags, exit 0
```

## Offline Tests (no credentials required)

```bash
uv run pytest --cov=home_water_usage --cov-report=term-missing
```

Expected: all tests pass, ≥ 80% line coverage, zero network calls.

---

## Validation Scenarios

### Scenario 1 — Happy Path

**Validates**: SC-001 (end-to-end graph renders on valid invocation)

```bash
uv run home-water-usage --start-date 2025-01-01 --end-date 2026-06-09
```

Expected terminal output (in order):

```
[→] Authenticating with Gmail...
[✓] Authenticated.
[→] Fetching emails from Gmail...
[✓] Fetched N in-range + M buffer emails.
[→] Parsing email bodies...
[✓] Parsed N in-range usage records.
[→] Writing run CSV...
[✓] Run CSV written to ...
[→] Updating history cache...
[✓] History cache updated.
[→] Computing seasonal averages...
[✓] Computed N seasonal average line(s).
[→] Rendering graph...
[✓] Graph rendered.
```

Expected: interactive Matplotlib window with usage line + seasonal average overlays.

---

### Scenario 2 — No Exceedances in Range (Averages-Only)

**Validates**: FR-009 (seasonal averages still shown when no exceedances in range)

```bash
uv run home-water-usage --start-date 2020-01-01 --end-date 2020-01-31
```

Expected:

```
[!] No exceedance emails in date range — graph shows seasonal averages only.
```

Graph window opens with seasonal average lines only (no usage line).

---

### Scenario 3 — PDF Export

**Validates**: SC-006 (PDF exists on disk before interactive window opens)

```bash
uv run home-water-usage --start-date 2025-01-01 --end-date 2025-12-31 --save-pdf
```

Expected:

```
[✓] PDF saved to ./household-water-usage-2025-01-01-to-2025-12-31.pdf
```

Verify: `ls -la household-water-usage-2025-01-01-to-2025-12-31.pdf`

---

### Scenario 4 — Custom PDF Path

**Validates**: `--pdf-path` overrides `pdf_output_dir` + `pdf_filename_pattern`

```bash
uv run home-water-usage --start-date 2025-01-01 --end-date 2025-12-31 \
  --save-pdf --pdf-path /tmp/my-report.pdf
```

Expected: PDF written to `/tmp/my-report.pdf` exactly.

---

### Scenario 5 — Preserve Temp CSV

**Validates**: `--no-delete-temp` keeps run CSV after graph display

```bash
uv run home-water-usage --start-date 2025-06-01 --end-date 2025-06-30 --no-delete-temp
```

Expected: after closing the graph window, `water-usage-run-2025-06-01-2025-06-30.csv`
remains in the current directory.

---

### Scenario 6 — CLI Flag Overrides YAML Default

**Validates**: SC-002 (100% YAML/CLI key parity — every default is overridable)

```bash
uv run home-water-usage --start-date 2025-01-01 --end-date 2025-12-31 \
  --graph-title "My Custom Title" --summer-avg-color "purple"
```

Expected: graph window title reads "My Custom Title"; summer average line is purple.

---

### Scenario 7 — Seasonal Averages

**Validates**: SC-004 (all seasons with data rendered; missing seasons omitted with notice)

```bash
uv run home-water-usage --start-date 2025-01-01 --end-date 2025-12-31
```

Expected: up to five dotted horizontal lines (Annual, Winter, Spring, Summer, Fall).
For any season with no data:

```
[!] No data for <season> season — average line omitted.
```

---

### Scenario 8 — Warm Cache Performance

**Validates**: SC-007 (pipeline from entry to graph display < 10 s after cache populated)

```bash
# First run: populates history cache
uv run home-water-usage --start-date 2025-01-01 --end-date 2025-12-31

# Second run: measure with warm cache
time uv run home-water-usage --start-date 2025-01-01 --end-date 2025-12-31
```

Expected: second run completes in < 10 seconds wall clock.

---

### Scenario 9 — Missing Credentials

**Validates**: SC-005 (structured `[✗]` error with root cause + remediation on all failures)

```bash
uv run home-water-usage --start-date 2025-01-01 --end-date 2025-12-31 \
  --credentials-path /nonexistent/path.json
```

Expected:

```
[✗] credentials.json not found.
Likely cause: File missing at all 3 discovery locations: ...
```

Exit code: `echo $?` → `1`

---

### Scenario 10 — Unwritable temp_dir

**Validates**: `[✗]` error path for unwritable storage directory

```bash
sudo mkdir -p /tmp/no-perm && sudo chmod 555 /tmp/no-perm
uv run home-water-usage --start-date 2025-01-01 --end-date 2025-12-31 \
  --temp-dir /tmp/no-perm
```

Expected:

```
[✗] Cannot write run CSV to /tmp/no-perm/...
Likely cause: Directory '/tmp/no-perm' is not writable.
Remediation: Set --temp-dir to a writable directory.
```

Exit code: `echo $?` → `1`

---

## Key Files After a Successful Run

| File | Location | Kept? |
|------|----------|-------|
| `token.json` | `~/.config/home-water-usage/token.json` | Yes (mode 600) |
| `water-usage-history.csv` | `{temp_dir}/` | Yes (always) |
| `water-usage-run-{start}-{end}.csv` | `{temp_dir}/` | No (deleted by default) |
| PDF | `{pdf_output_dir}/household-water-usage-{start}-to-{end}.pdf` | Yes (if `--save-pdf`) |

## References

- Full requirements: `PRD.md`
- All CLI flags: `uv run home-water-usage --help`
- Runtime defaults: `parameter_values.yaml`
- Project principles: `constitution.md`
