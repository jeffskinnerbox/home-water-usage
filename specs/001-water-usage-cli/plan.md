# Implementation Plan: Home Water Usage CLI

**Branch**: `001-water-usage-cli` | **Date**: 2026-06-09 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/001-water-usage-cli/spec.md`

---

## Summary

Python 3.12+ CLI (`home-water-usage`) that authenticates with Gmail via OAuth 2.0,
fetches water-usage alert emails from `no-reply@leesburgva.gov`, parses gallon
consumption data, caches parsed history in a local CSV, and renders an interactive
Seaborn line graph with seasonal average overlays. Fully configurable via
`parameter_values.yaml` with per-key CLI flag overrides. 100% offline test suite
via pytest + fixture JSON.

---

## Technical Context

**Language/Version**: Python 3.12+

**Primary Dependencies**:
- `google-api-python-client` + `google-auth-oauthlib` — Gmail OAuth 2.0 + API
- `seaborn` + `matplotlib` — line graph rendering, interactive window, PDF export
- `rich` — colored terminal status output
- `PyYAML` — `parameter_values.yaml` loading
- `argparse` (stdlib) — CLI flag parsing
- `pytest` + `pytest-cov` — test runner + coverage

**Storage**: Two CSV files managed by `storage.py`:
- `water-usage-run-{start}-{end}.csv` — run-specific temp (`date,gallons`), deleted by default
- `water-usage-history.csv` — persistent HistoryCache (`date,gallons`), never deleted

**Testing**: `pytest` + `pytest-cov`; `unittest.mock` for all external boundaries;
fixture JSON in `tests/fixtures/`; `matplotlib.use("Agg")` in graph tests

**Target Platform**: Linux desktop terminal with display session (Matplotlib pop-up requires `$DISPLAY`)

**Project Type**: CLI tool (`uv` project, console script entry point via `pyproject.toml`)

**Performance Goals**: Warm-cache run (no Gmail fetch) → graph rendered in < 10 s (SC-007)

**Constraints**:
- 100% offline tests — no live Gmail calls in any test
- Zero hardcoded defaults — all in `parameter_values.yaml`
- OAuth scope: `gmail.readonly` (read-only, minimum privilege)
- token.json permissions: `600` immediately after write
- credentials.json + token.json never committed, never logged

**Scale/Scope**: Single user, single Gmail account, single utility account (`40002423000`);
multi-account and headless use are out of scope

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked post-Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Python on Linux Terminal (NON-NEG) | ✅ PASS | Python 3.12+, `uv` project, Linux terminal only; no GUI frameworks |
| II. Information-Rich Output | ✅ PASS | `rich` for all terminal status; Seaborn+Matplotlib for graphs; every step produces output |
| III. Configuration Over Hardcoding (NON-NEG) | ✅ PASS | All defaults in `parameter_values.yaml`; every key has a CLI override flag |
| IV. TDD (NON-NEG) | ✅ PASS | Tests written first; pytest; ≥80% coverage target; 100% offline; fixture JSON |
| V. Fail Clearly | ✅ PASS | `[✗]` + "Likely cause:" + exit non-zero on every failure path |

**No violations. No Complexity Tracking required.**

---

## Project Structure

### Documentation (this feature)

```text
specs/001-water-usage-cli/
├── plan.md              # This file (/speckit-plan output)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── cli-contract.md  # CLI flag schema
│   └── renderer-interface.md  # Pluggable renderer contract
└── tasks.md             # Phase 2 output (/speckit-tasks — not created here)
```

### Source Code

```text
home-water-usage/
├── pyproject.toml               # uv project config; console_scripts entry point
├── parameter_values.yaml        # All runtime defaults (single source of truth)
├── src/
│   └── home_water_usage/
│       ├── __init__.py
│       ├── cli.py               # argparse; merges YAML defaults + CLI flags → Config
│       ├── auth.py              # Gmail OAuth 2.0; 3-step credentials discovery; token cache
│       ├── fetch.py             # Gmail API query; date-range filter; buffer classification
│       ├── parse.py             # Email body → UsageRecord; account validation; dedup
│       ├── storage.py           # Run CSV + HistoryCache CSV read/write/merge/delete
│       ├── graph.py             # Renderer dispatch; line renderer; seasonal averages
│       ├── renderers/
│       │   └── line.py          # Default renderer: render(records, averages, config) → None
│       └── status.py            # rich-formatted [✓]/[→]/[!]/[✗] helpers
└── tests/
    ├── fixtures/                # Canned Gmail API JSON responses
    │   ├── messages_list.json
    │   ├── message_detail_*.json
    │   └── empty_list.json
    ├── test_cli.py
    ├── test_auth.py
    ├── test_fetch.py
    ├── test_parse.py
    ├── test_storage.py
    ├── test_graph.py
    └── test_integration.py
```

**Structure Decision**: Single `src/` layout (Option 1) with a `renderers/` sub-package
inside `home_water_usage/` to support the pluggable renderer pattern without adding
a top-level package. Tests mirror the module structure 1:1.

---

## Implementation Phases

### Phase 0 — Project Scaffold & Credentials Setup

**Goal**: Runnable `uv` project skeleton; `parameter_values.yaml` with all keys; Gmail
OAuth working end-to-end; no application logic yet.

**Deliverables**:
- `pyproject.toml` with all dependencies and console script entry point
- `parameter_values.yaml` with all 30+ keys and default values
- `src/home_water_usage/__init__.py`, `cli.py` (stub), `status.py`
- `auth.py` stub (module file + function signatures only — no OAuth logic yet; full TDD implementation is in Phase 3/T017 after T011 test is written and confirmed failing)
- `.gitignore` with `credentials.json` and `token.json`
- Tests: `test_cli.py` (YAML load + flag parity); `test_auth.py` written and confirmed failing (red) — full auth implementation in Phase 3

**Test gate**: `uv run pytest tests/test_cli.py` — passes; `test_auth.py` exists and fails (expected — implementation pending Phase 3)

---

### Phase 1 — Email Fetch & Parse

**Goal**: Fetch emails from Gmail (mocked in tests), parse body into UsageRecords, write
run CSV, update HistoryCache.

**Deliverables**:
- `fetch.py`: Gmail query construction, buffer classification, account-mismatch warning
- `parse.py`: regex parse with named capture groups, duplicate dedup, invalid-date skip
- `storage.py`: run CSV write/delete, HistoryCache append/merge/rebuild
- Tests: `test_fetch.py`, `test_parse.py`, `test_storage.py` with fixture JSON

**Test gate**: `uv run pytest tests/test_fetch.py tests/test_parse.py tests/test_storage.py`

---

### Phase 2 — Graph Rendering

**Goal**: Seaborn line graph with all visual properties, seasonal averages, gaps, y-axis
cap, pluggable renderer dispatch.

**Deliverables**:
- `graph.py`: renderer dispatch via `chart_type`; seasonal average computation; gap detection
- `renderers/line.py`: `render(records, averages, config) → None`; all FR-009/FR-010/FR-020 behavior
- Tests: `test_graph.py` with `matplotlib.use("Agg")`; assert figure properties only

**Test gate**: `uv run pytest tests/test_graph.py`

---

### Phase 3 — Config & CLI Integration

**Goal**: Full `parameter_values.yaml` + argparse merge; every key has a working CLI flag;
end-to-end happy path.

**Deliverables**:
- `cli.py` complete: YAML load, argparse, merge, Config dataclass
- Integration test: `test_integration.py` (mocked Gmail, fixture emails, full pipeline)
- All 30+ YAML keys verified to have working CLI overrides (SC-002 test)

**Test gate**: `uv run pytest` — full suite; ≥ 80% coverage

---

### Phase 4 — PDF Export & Temp File Cleanup

**Goal**: `--save-pdf` writes PDF before window opens; `--no-delete-temp` preserves run
CSV; `--pdf-path` full-path override.

**Deliverables**:
- PDF save logic in `graph.py` / `renderers/line.py` (synchronous write → then `plt.show()`)
- Cleanup logic in `storage.py` / `cli.py`
- Tests: PDF path/filename assertions; temp file delete/preserve behavior

**Test gate**: `uv run pytest` — full suite green

---

### Phase 5 — Hardening & Performance

**Goal**: Exponential-backoff retries; warm-cache timing verification; error messages for
all failure paths; 100% SC coverage.

**Deliverables**:
- Retry logic in `fetch.py` (`max_retries`, exponential backoff)
- `[✗]` + "Likely cause:" messages verified for all failure paths
- Warm-cache timing validated (SC-007: < 10 s excluding Gmail fetch)
- Final coverage report: `uv run pytest --cov=home_water_usage --cov-report=term-missing`

**Test gate**: `uv run pytest` — full suite; ≥ 80% line coverage confirmed
