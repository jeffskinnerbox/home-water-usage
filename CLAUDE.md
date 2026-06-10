# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan
at `specs/001-water-usage-cli/plan.md`.
<!-- SPECKIT END -->

# Home Water Usage — AI Session Context

For project principles, technology choices, and non-negotiable rules, read
`constitution.md` first. This file covers operational context: how to work in
this repo.

---

## Project Overview

`home-water-usage` is a Python CLI that pulls daily water-usage alert emails from
Gmail, parses consumption data, and renders an interactive Seaborn line graph with
seasonal average overlays. See `PRD.md` for full requirements and `constitution.md`
for governing principles.

---

## Key Files

| File | Purpose |
|------|---------|
| `constitution.md` | Project principles — read before implementing anything |
| `PRD.md` | Full product requirements, user stories, acceptance criteria |
| `parameter_values.yaml` | All runtime defaults; every key has a CLI flag override |
| `pyproject.toml` | `uv` project config, dependencies, console script entry point |
| `src/home_water_usage/` | Application source modules |
| `tests/` | pytest test suite |
| `tests/fixtures/` | Canned Gmail API JSON responses for offline testing |

---

## Project Structure

```
home-water-usage/
├── constitution.md
├── CLAUDE.md
├── PRD.md
├── parameter_values.yaml
├── pyproject.toml
├── specs/001-water-usage-cli/   implementation plan + research
├── src/
│   └── home_water_usage/
│       ├── cli.py               argparse; merges YAML defaults + CLI flags → Config
│       ├── config.py            Config dataclass; YAML+CLI merge with type coercion
│       ├── models.py            UsageRecord, SeasonalAverage dataclasses
│       ├── status.py            rich-formatted [✓]/[→]/[!]/[✗] terminal output
│       ├── renderers/           graph renderer subpackage (in progress)
│       ├── auth.py              Gmail OAuth (3-step credentials discovery, token cache) [TODO]
│       ├── fetch.py             email fetch, date-range filter, buffer logic [TODO]
│       ├── parse.py             email body → UsageRecord list [TODO]
│       ├── storage.py           two-CSV scheme: run-temp + persistent HistoryCache [TODO]
│       └── graph.py             Seaborn line graph + seasonal overlays [TODO]
└── tests/
    ├── fixtures/                canned Gmail API JSON responses
    └── test_cli.py
```

### Storage model (two CSV files)

- `water-usage-run-{start}-{end}.csv` — run-specific temp (`date,gallons`); deleted by default after graph display
- `water-usage-history.csv` — persistent HistoryCache (`date,gallons`); never deleted; rebuilt on `--refresh-cache`

---

## Commands

```bash
# Install dependencies
uv sync

# Run the tool
uv run home-water-usage --start-date 2026-01-01 --end-date 2026-06-09

# Run full test suite
uv run pytest

# Run with coverage report
uv run pytest --cov=home_water_usage --cov-report=term-missing

# Run a specific module's tests
uv run pytest tests/test_cli.py -v
```

All tests run 100% offline — no live Gmail credentials required.
Graph tests must use `matplotlib.use("Agg")` and assert figure properties only.

---

## Gmail Credentials Setup

The tool discovers `credentials.json` in this order:

1. `~/.config/home-water-usage/credentials.json`
2. `$GMAIL_CREDENTIALS_PATH` env var
3. `--credentials-path` CLI flag

OAuth token is cached at `~/.config/home-water-usage/token.json` after first run.

---

## CLI Reference

```bash
uv run home-water-usage \
  --start-date YYYY-MM-DD \
  --end-date   YYYY-MM-DD \
  [--save-pdf] \
  [--pdf-path PATH] \
  [--no-delete-temp] \
  [--temp-dir PATH] \
  [--credentials-path PATH]
```

Every key in `parameter_values.yaml` has a corresponding CLI flag. Run
`uv run home-water-usage --help` for the full list.

---

## Development Rules (from constitution.md)

- **TDD**: Write tests first, confirm they fail, then implement. No exceptions.
- **No hardcoded values**: All defaults go in `parameter_values.yaml`.
- **No silent failures**: Every error MUST print `[✗]` + "Likely cause:" + exit non-zero.
- **100% offline tests**: No live Gmail calls in any test.
- **Credentials security**: Never log or print tokens; never commit credentials files.

See `constitution.md` for the full set of non-negotiable principles.
