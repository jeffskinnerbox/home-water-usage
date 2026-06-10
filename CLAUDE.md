# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan
at `specs/001-water-usage-cli/plan.md`.
<!-- SPECKIT END -->

For project principles, technology choices, and non-negotiable rules, read `constitution.md` first.

---

## Project Overview

`home-water-usage` is a Python CLI (`uv run home-water-usage`) that pulls daily water-usage alert emails from Gmail, parses consumption data, stores it in two CSVs, and renders an interactive Seaborn line graph with seasonal average overlays.

---

## Commands

```bash
uv sync                                  # install deps
uv run home-water-usage --start-date 2026-01-01 --end-date 2026-06-09
uv run pytest tests/test_cli.py -v       # run one module at a time — full suite loads
uv run pytest tests/test_auth.py -v      # seaborn/numpy/pandas simultaneously and
uv run pytest tests/test_fetch.py -v     # will consume all available RAM
uv run pytest tests/test_parse.py -v
uv run pytest tests/test_storage.py -v
uv run pytest tests/test_graph.py -v
uv run pytest tests/test_integration.py -v
uv run pytest --cov=home_water_usage --cov-report=term-missing  # only if RAM allows
```

---

## Pipeline

`cli.main()` orchestrates a linear pipeline — each step depends on the previous:

```
auth.get_service(config)
  → fetch.fetch_messages / classify_messages / get_message_body
  → parse.parse_messages  →  list[UsageRecord]
  → storage.write_run_csv + update_history_cache
  → graph.compute_seasonal_averages  →  list[SeasonalAverage]
  → graph.dispatch_render  →  renderers/{chart_type}.render()
  → storage.delete_run_csv
```

`graph.dispatch_render` dynamically imports `home_water_usage.renderers.{config.chart_type}` and calls `render(records, averages, config)`. Adding a new chart type means creating `src/home_water_usage/renderers/<type>.py` with that signature.

---

## Configuration

All runtime defaults live in `parameter_values.yaml`. Every key maps 1:1 to a CLI flag. `Config.from_dict()` (`config.py`) handles type coercion (dates, ints, floats, bools, optional fields) when merging YAML defaults with CLI args. No hardcoded defaults anywhere else.

---

## Storage Model

Both files live in `config.temp_dir`:

- `water-usage-run-{start}-{end}.csv` — run-specific (`date,gallons`); deleted after graph by default
- `water-usage-history.csv` — persistent HistoryCache; append-only merge; never deleted; rebuilt with `--refresh-cache`

---

## Testing Conventions

`tests/conftest.py` sets `matplotlib.use("Agg")` globally and provides `base_config` (uses `tmp_path`) and `sample_records` fixtures. All tests use these fixtures — no need to re-declare them.

Graph tests assert figure/axes properties only; they never call `plt.show()`.

Canned Gmail API responses are in `tests/fixtures/` (JSON files matching the Gmail API message list/detail shape).

---

## Gmail Auth

`auth._discover_credentials_path` checks three locations in order:
1. `~/.config/home-water-usage/credentials.json`
2. `$GMAIL_CREDENTIALS_PATH` env var
3. `--credentials-path` CLI flag

Token cached at `~/.config/home-water-usage/token.json` (mode 0o600) after first OAuth flow.

---

## Development Rules (from constitution.md)

- **TDD**: Write tests first, confirm they fail, then implement.
- **No hardcoded values**: All defaults in `parameter_values.yaml`.
- **No silent failures**: Every error must call `status.error(...)` (prints `[✗]` + "Likely cause:" and exits non-zero).
- **100% offline tests**: No live Gmail calls in any test.
