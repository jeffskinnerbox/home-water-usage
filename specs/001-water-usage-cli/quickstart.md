# Quickstart & Validation Guide: Home Water Usage CLI

**Phase 1 Output** | **Date**: 2026-06-09 | **Plan**: [plan.md](./plan.md)

---

## Prerequisites

1. Linux desktop with a display session (`$DISPLAY` set — required for Matplotlib pop-up)
2. Python 3.12+ installed
3. `uv` installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
4. Gmail API credentials (`credentials.json`) obtained from Google Cloud Console:
   - Create a project → Enable Gmail API → Create OAuth 2.0 credentials (Desktop app)
   - Download `credentials.json` to `~/.config/home-water-usage/credentials.json`

---

## Setup

```bash
# Clone/enter project
cd /path/to/home-water-usage

# Install dependencies
uv sync

# Verify the entry point is available
uv run home-water-usage --help
```

Expected: argparse help text with all flags listed.

---

## Offline Test Suite (no credentials required)

```bash
# Run full suite
uv run pytest

# With coverage
uv run pytest --cov=home_water_usage --cov-report=term-missing
```

Expected: all tests pass, ≥ 80% line coverage, zero network calls.

---

## Validation Scenarios

### Scenario 1 — Happy Path: Graph Renders with Data

**Validates**: FR-001 through FR-013, SC-001, SC-002, SC-003

```bash
uv run home-water-usage --start-date 2025-01-01 --end-date 2026-06-09
```

**Expected terminal output** (in order):

```
[→] Loading configuration...
[✓] Configuration loaded
[→] Authenticating with Gmail...
[✓] Authenticated (token cached)
[→] Fetching emails (2024-12-29 to 2026-06-12)...   # widened by buffer
[✓] Fetched N emails
[→] Parsing email bodies...
[✓] Parsed N records  (or [!] warnings for skipped/duplicate)
[→] Updating history cache...
[✓] History cache updated (water-usage-history.csv)
[→] Computing seasonal averages...
[✓] Seasonal averages: Annual, Winter, Spring, Summer, Fall  (or subset)
[→] Rendering graph...
[✓] Graph rendered
```

**Expected**: Interactive Matplotlib window opens showing usage line with seasonal average overlays.

---

### Scenario 2 — No Exceedances in Range (Averages-Only)

**Validates**: FR-009, FR-010, edge case "emails found but none fall within plotted range"

```bash
uv run home-water-usage --start-date 2020-01-01 --end-date 2020-01-31
```

**Expected**:

```
[!] No threshold exceedances in the requested range — usage line not shown. All days were within threshold.
```

Graph window opens with seasonal average lines only (no usage line).

---

### Scenario 3 — PDF Export

**Validates**: FR-012, SC-006

```bash
uv run home-water-usage --start-date 2025-01-01 --end-date 2025-12-31 --save-pdf
```

**Expected**:

```
[✓] PDF saved to ./household-water-usage-2025-01-01-to-2025-12-31.pdf
```

Verify: `ls -la household-water-usage-2025-01-01-to-2025-12-31.pdf` exists before interactive window appears.

---

### Scenario 4 — Custom PDF Path

**Validates**: FR-012 `--pdf-path` override

```bash
uv run home-water-usage --start-date 2025-01-01 --end-date 2025-12-31 \
  --save-pdf --pdf-path /tmp/my-report.pdf
```

**Expected**: PDF written to `/tmp/my-report.pdf` exactly.

---

### Scenario 5 — Preserve Temp CSV

**Validates**: FR-016, User Story 2

```bash
uv run home-water-usage --start-date 2025-06-01 --end-date 2025-06-30 --no-delete-temp
```

**Expected**: After graph window is closed, `water-usage-run-2025-06-01-2025-06-30.csv`
remains in the current directory.

---

### Scenario 6 — Cache Refresh

**Validates**: FR-018 `--refresh-cache`

```bash
uv run home-water-usage --start-date 2025-01-01 --end-date 2025-12-31 --refresh-cache
```

**Expected**:

```
[→] Refreshing history cache (full Gmail re-fetch)...
[✓] History cache rebuilt
```

Or if already up to date:

```
[✓] Cache already up to date
```

---

### Scenario 7 — CLI Flag Overrides YAML Default

**Validates**: FR-003, SC-002

```bash
uv run home-water-usage --start-date 2025-01-01 --end-date 2025-12-31 \
  --graph-title "My Custom Title" --no-delete-temp
```

**Expected**: Graph title in window reads "My Custom Title"; run CSV persists after close.

---

### Scenario 8 — Warm Cache Performance

**Validates**: SC-007 (< 10 s from CLI entry to `plt.show()`, excluding Gmail fetch)

```bash
# First run populates cache; second run uses it
uv run home-water-usage --start-date 2025-01-01 --end-date 2025-12-31
time uv run home-water-usage --start-date 2025-01-01 --end-date 2025-12-31
```

**Expected**: Second run completes in < 10 seconds (wall clock; Gmail fetch omitted by cache hit).

---

### Scenario 9 — Missing Credentials Failure

**Validates**: FR-004, FR-014, Principle V (Fail Clearly)

```bash
uv run home-water-usage --start-date 2025-01-01 --end-date 2025-12-31 \
  --credentials-path /nonexistent/path.json
```

**Expected**:

```
[✗] credentials.json not found at any discovery location.
Likely cause: credentials.json has not been placed at the expected path.
Tried:
  1. ~/.config/home-water-usage/credentials.json
  2. $GMAIL_CREDENTIALS_PATH (not set)
  3. --credentials-path /nonexistent/path.json
Setup guide: [instructions]
```

Exit code: 1

---

### Scenario 10 — Unwritable temp_dir

**Validates**: FR-015 (exception handling), edge case "temp_dir not writable"

```bash
uv run home-water-usage --start-date 2025-01-01 --end-date 2025-12-31 \
  --temp-dir /root/no-permission
```

**Expected**:

```
[✗] temp_dir '/root/no-permission' is not writable.
Likely cause: Directory does not exist or insufficient permissions.
Remediation: Create the directory or set a writable path via --temp-dir or temp_dir in parameter_values.yaml.
```

Exit code: 1

---

## Key File Locations After a Successful Run

| File | Location | Kept? |
|------|----------|-------|
| `token.json` | `~/.config/home-water-usage/token.json` | Yes (permissions: 600) |
| `water-usage-history.csv` | `{temp_dir}/water-usage-history.csv` | Yes (always) |
| `water-usage-run-{start}-{end}.csv` | `{temp_dir}/...` | No (deleted by default) |
| PDF | `{pdf_output_dir}/household-water-usage-{start}-to-{end}.pdf` | Yes (if `--save-pdf`) |

---

## References

- CLI flags: [contracts/cli-contract.md](./contracts/cli-contract.md)
- Renderer interface: [contracts/renderer-interface.md](./contracts/renderer-interface.md)
- Data model: [data-model.md](./data-model.md)
- Full requirements: [spec.md](./spec.md)
