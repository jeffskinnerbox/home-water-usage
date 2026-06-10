<!--
SYNC IMPACT REPORT
==================
Version change: [template/unversioned] → 1.0.0
Modified principles: N/A (initial population from template)
Added sections:
  - Core Principles (I–V)
  - Software & Hardware Stack
  - Development Workflow
  - Governance
Removed sections: none
Templates reviewed:
  - .specify/templates/plan-template.md    ✅ no changes needed (Constitution Check gate is generic)
  - .specify/templates/spec-template.md    ✅ no changes needed
  - .specify/templates/tasks-template.md   ✅ no changes needed
Follow-up TODOs: none — all placeholders resolved
Sources: PRD.md (v1.1), my-vision.md
-->

# Home Water Usage Constitution

## Core Principles

### I. Python on Linux Terminal (NON-NEGOTIABLE)

The solution MUST be written in Python 3.12+ and MUST run in a standard Linux terminal
session. No GUI frameworks, desktop installers, or platform-specific binaries are permitted.
The `uv` tool MUST be used for all dependency management and project environment operations
(`pyproject.toml`, `uv sync`, console script entry points). Bash is permitted only for
infrastructure scripts (setup, CI helpers); all application logic MUST be in Python.

**Rationale**: The sole user operates from a Linux terminal. Portability beyond that context
is out of scope; adding abstraction layers for it would add maintenance burden with zero benefit.

### II. Information-Rich, Visually Appealing Output

The tool MUST communicate status at every step of the workflow using `rich`-formatted,
colored terminal output. The convention is:
- `[✓]` green — success
- `[→]` cyan — in-progress
- `[!]` yellow — warning / skipped
- `[✗]` red — error

Graphs MUST be rendered using the Seaborn library (backed by Matplotlib). All graph
dimensions, colors, fonts, line styles, and layout settings MUST be configurable.
No step in the workflow may be silent — every action MUST produce observable output.

**Rationale**: The vision explicitly requires "information rich for the user but nicely
formatted & visually appealing." Silent tools are undebuggable tools.

### III. Configuration Over Hardcoding (NON-NEGOTIABLE)

Every default value that governs appearance or behavior MUST be declared in
`parameter_values.yaml` at the project root. Zero hardcoded display or behavior values
are permitted in source code. Every key in `parameter_values.yaml` MUST have a
corresponding CLI flag override so the tool can be driven entirely from the command line
without editing YAML.

**Rationale**: The single-user audience demands full control over look-and-feel without
touching source code. A single canonical defaults file also prevents value drift across
modules.

### IV. Test-Driven Development (NON-NEGOTIABLE)

Development MUST follow the Red-Green-Refactor cycle: tests MUST be written and confirmed
failing before any implementation code is written. The test suite MUST:
- Use `pytest` (and `pytest-cov`) as the test runner
- Achieve ≥ 80% line coverage
- Run 100% offline — no live network calls, no live Gmail API access
- Simulate Gmail API responses via fixture JSON files in `tests/fixtures/`
- Use `matplotlib.use("Agg")` in graph tests; assert figure properties only (no pixel/snapshot tests)
- Use `unittest.mock` for all external-service boundaries

**Rationale**: The vision requires TDD with pytest/unittest. Offline-only tests ensure the
suite is deterministic, fast, and runnable without credentials.

### V. Fail Clearly — No Silent Errors

When the tool encounters any failure, it MUST:
1. Print a `[✗]` red error line naming what failed
2. Include a "Likely cause:" line with a human-readable root cause
3. Include a remediation hint where applicable
4. Exit with a non-zero status code

Transient external failures (Gmail API network errors) MUST be retried with exponential
backoff up to `max_retries` before the tool aborts. Partial results MUST NOT be silently
graphed or written — abort cleanly or succeed fully.

**Rationale**: The vision states: "If the solution fails or errors, the solution must write
a clear description and likely root cause of the failure/error." Ambiguous output wastes the
user's time diagnosing phantom issues.

## Software & Hardware Stack

**Language**: Python 3.12+
**Environment**: `uv` (`pyproject.toml`, `uv sync`, console script entry point)
**Graphing**: Seaborn + Matplotlib (interactive pop-up window; optional PDF export)
**Gmail access**: `google-api-python-client`, `google-auth-oauthlib` (OAuth 2.0 only)
**CLI**: `argparse` (stdlib)
**Configuration**: `PyYAML` (`parameter_values.yaml`)
**Terminal output**: `rich`
**Testing**: `pytest`, `pytest-cov`, `unittest.mock`
**Hardware**: No special hardware. Standard Linux desktop with a display (Matplotlib
pop-up requires a display session; headless use is out of scope).

## Development Workflow

1. **Phase 0 — Setup**: Obtain `credentials.json` from Google Cloud (Gmail API enabled);
   scaffold `uv` project. This phase MUST be completed as a dedicated session before
   any application code is written.
2. **Phase 1–5** — Auth & Fetch → Graph → Config & CLI → PDF & Cleanup → Hardening.
   Each phase MUST produce a passing test suite before the next phase begins.
3. **Constitution Check** (per feature/phase): Before implementing any module, verify
   the design satisfies all five principles. Document any necessary deviations in a
   Complexity Tracking table in the plan.
4. **Credentials security**: `credentials.json` and `token.json` MUST be listed in
   `.gitignore`. OAuth tokens MUST never appear in logs or stdout.
5. **Commit discipline**: Commit after each logical unit of work with a message that
   references the phase and module (e.g., `feat(auth): implement 3-step credentials
   discovery`).

## Governance

This constitution supersedes all other guidance for the `home-water-usage` project.
Principles I, III, and IV are non-negotiable and MUST NOT be amended without a major
version bump and written justification.

**Amendment procedure**:
- PATCH (0.0.X): Clarifications, wording, typo fixes — no approval gate
- MINOR (0.X.0): New principle or materially expanded guidance — document rationale
- MAJOR (X.0.0): Removal or redefinition of a non-negotiable principle — requires
  explicit written justification and migration plan

**Compliance**: Every implementation plan (`plan.md`) MUST include a Constitution Check
gate before Phase 0 research. `CLAUDE.md` references this file for AI-session operational
context; `constitution.md` is the authoritative source of project principles.

**Version**: 1.0.0 | **Ratified**: 2026-06-09 | **Last Amended**: 2026-06-09
