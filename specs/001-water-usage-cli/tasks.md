# Tasks: Home Water Usage CLI

**Input**: Design documents from `specs/001-water-usage-cli/`

**Prerequisites**: plan.md ✅ | spec.md ✅ | research.md ✅ | data-model.md ✅ | contracts/ ✅

**TDD**: Constitution Principle IV is NON-NEGOTIABLE. Every test task MUST be written and
confirmed failing (red) before its implementation task runs (green). No exceptions.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Parallelizable — different files, no incomplete dependencies
- **[Story]**: User story this task serves (US1, US2, US3)
- All test tasks precede their implementation counterparts within each phase

---

## Phase 1: Setup (Project Scaffold)

**Purpose**: Create the runnable `uv` project skeleton, all config files, and fixture data.
No application logic yet.

- [x] T001 Create `pyproject.toml` with all dependencies (`google-api-python-client`, `google-auth-oauthlib`, `seaborn`, `matplotlib`, `rich`, `PyYAML`, `pytest`, `pytest-cov`) and console script entry point `home-water-usage = "home_water_usage.cli:main"`
- [x] T002 Create `parameter_values.yaml` at project root with all 30+ keys and default values (see data-model.md Config table — gmail, credentials, storage, graph display, seasonal lines ×20, PDF export)
- [x] T003 [P] Create full directory structure: `src/home_water_usage/renderers/`, `tests/fixtures/`, `specs/` (as needed)
- [x] T004 [P] Create `.gitignore` with entries for `credentials.json`, `token.json`, `*.csv`, `__pycache__/`, `.venv/`
- [x] T005 [P] Create `tests/fixtures/` JSON files: `messages_list.json` (2 valid messages), `messages_list_empty.json`, `message_detail_1.json` (valid body), `message_detail_2.json` (same date as #1 — duplicate), `message_detail_bad.json` (non-matching body)

**Checkpoint**: `uv sync` succeeds; `uv run home-water-usage --help` exits without error (stub ok)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core shared infrastructure every module depends on. **No user story work
starts until this phase is complete.**

**⚠️ CRITICAL**: All other phases depend on Config, dataclasses, and status helpers.

- [x] T006 Write `tests/test_cli.py`: YAML key parity test — assert every key in `parameter_values.yaml` has a corresponding CLI flag in argparse; assert `--start-date` and `--end-date` are required; assert `start_date > end_date` aborts with exit code 1 — **confirm test FAILS before T009**
- [x] T007 [P] Create `src/home_water_usage/status.py` — `rich`-formatted helpers: `success(msg)`, `progress(msg)`, `warning(msg)`, `error(msg, likely_cause, remediation)` using `[✓]`/`[→]`/`[!]`/`[✗]` convention; `error()` calls `sys.exit(1)`
- [x] T008 [P] Create `src/home_water_usage/models.py` — `UsageRecord(date: datetime.date, gallons: int)` and `SeasonalAverage(season: str, avg_gallons: float)` dataclasses
- [x] T009 Create `src/home_water_usage/config.py` — `Config` dataclass with all 30+ fields matching every key in `parameter_values.yaml` (see data-model.md); include `from_dict(d: dict) -> Config` classmethod
- [x] T010 Create `src/home_water_usage/cli.py` — `main()` entry point: load `parameter_values.yaml` via `yaml.safe_load`, build full argparse with all 30+ flags (all `default=None`), merge YAML defaults + CLI args into `Config`, validate `start_date ≤ end_date`; abort on violation with `[✗]`; stub out pipeline call

**Checkpoint**: `uv run pytest tests/test_cli.py` — all tests pass; `uv run home-water-usage --help` shows all flags

---

## Phase 3: User Story 1 — View Daily Usage Graph (Priority: P1) 🎯 MVP

**Goal**: Full end-to-end pipeline: Gmail auth → email fetch → parse → CSV storage →
HistoryCache → seasonal averages → Seaborn line graph in interactive window.

**Independent Test**: `uv run pytest tests/test_auth.py tests/test_fetch.py tests/test_parse.py tests/test_storage.py tests/test_graph.py tests/test_integration.py` — all pass, zero network calls

### Tests for User Story 1

> **Write each test file, confirm it FAILS, then implement the corresponding module**

- [x] T011 [P] [US1] Write `tests/test_auth.py`: mock `InstalledAppFlow`; test 3-step credentials discovery order (config path → env var → CLI flag); test token written + `chmod 600` applied; test missing credentials at all 3 locations aborts with `[✗]`
- [x] T012 [P] [US1] Write `tests/test_parse.py`: test valid body → `UsageRecord`; test named group validation (missing required group aborts); test invalid date ("June 32") → skip + `[!]`; test duplicate body date → keep first + `[!]`; test account mismatch → skip + `[!]`; test non-matching body → skip + `[!]`
- [x] T013 [P] [US1] Write `tests/test_fetch.py`: mock `googleapiclient.discovery.build`; test Gmail query string format (widened date window, sender filter); test buffer classification (in-range, buffer, discard); test pagination (`nextPageToken`); test empty result → raises appropriate error; test `HttpError` 429/503 triggers retry (mock `time.sleep`, assert called with exponential delay); test retries exhausted → `[✗]` + exit 1; test non-retryable `HttpError` (e.g. 404) → immediate abort
- [x] T014 [P] [US1] Write `tests/test_storage.py`: test run CSV write (`date,gallons` columns, correct filename pattern); test HistoryCache append-only merge (new dates added, existing dates not overwritten); test partial-overlap (only uncached tail fetched); test corrupt HistoryCache → `[!]` + rebuild; test `--no-delete-temp` preserves run CSV; test default delete removes run CSV; test `--refresh-cache` + Gmail returns no new emails → continues with existing cache + emits `[✓] Cache already up to date`
- [x] T015 [P] [US1] Write `tests/test_graph.py` with `matplotlib.use("Agg")`: test figure has correct title + axis labels from Config; test seasonal average lines (count matches available seasons); test NaN gaps produce line breaks (no data → NaN in DataFrame); test y-axis cap at `y_axis_percentile_cap`; test `[!]` notice when values clipped; test missing season → line omitted + `[!]` terminal notice; test Annual-only case renders without error
- [x] T016 [US1] Write `tests/test_integration.py`: full pipeline with fixture JSONs and mocked Gmail API; assert `UsageRecord` list matches fixture data; assert `water-usage-history.csv` written; assert graph figure created (Agg backend); assert run CSV deleted by default; assert `status.progress` and `status.success` called at each pipeline stage (auth, fetch, parse, storage update, graph render) — mock `status` module and verify call sequence (FR-013)

### Implementation for User Story 1

- [x] T017 [US1] Implement `src/home_water_usage/auth.py`: 3-step `credentials.json` discovery (`~/.config/home-water-usage/` → `$GMAIL_CREDENTIALS_PATH` → `--credentials-path`); `InstalledAppFlow` OAuth; write `token.json` + `os.chmod(600)`; token refresh if expired; fail with `[✗]` + setup guide if no credentials found
- [x] T018 [US1] Implement `src/home_water_usage/parse.py`: compile `email_body_pattern` from Config; validate required named groups (`month`, `day`, `year`, `gallons`) — abort `[✗]` if missing; parse body → `UsageRecord`; skip invalid dates with `[!]`; deduplicate by body date (keep first, `[!]` each skip); skip account mismatches with `[!]`
- [x] T019 [US1] Implement `src/home_water_usage/fetch.py`: construct Gmail query (`gmail_query_filter` + widened received-date window in Unix timestamps); paginate `messages.list` to completion; fetch each message body; classify by body date: in-range → plotted, buffer → cache only, out-of-window → discard; raise on empty results
- [x] T020 [US1] Implement `src/home_water_usage/storage.py`: write run CSV `water-usage-run-{start}-{end}.csv` (`date,gallons`); read/write HistoryCache `water-usage-history.csv` (sorted ascending, append-only merge, dedup by date); detect + recover corrupt cache (`[!]` + delete + rebuild trigger); delete run CSV unless `--no-delete-temp`
- [x] T021 [US1] Implement `src/home_water_usage/renderers/line.py`: `render(records, averages, config) → None`; build full-range `pd.DataFrame` with `NaN` for missing days; `sns.lineplot`; overlay seasonal average dotted lines (color/width/style/label per Config); apply y-axis percentile cap (clip + `[!]` notice for each clipped point); `AutoDateLocator` + `DateFormatter(config.date_format)` on x-axis; gap legend note only when gaps exist; `plt.show()`
- [x] T022 [US1] Implement `src/home_water_usage/graph.py`: compute seasonal averages from HistoryCache (group by season, mean gallons); omit seasons with no data (`[!]` per omission); dispatch renderer via `importlib.import_module(f"home_water_usage.renderers.{config.chart_type}")`; abort `[✗]` if renderer module missing or lacks `render`
- [x] T023 [US1] Wire full pipeline in `src/home_water_usage/cli.py` `main()`: `status.progress` at each step → auth → fetch → parse → storage.write_run_csv → storage.update_history_cache → graph.compute_averages → graph.dispatch_render → storage.cleanup; emit `[✓]` at each success; handle no-exceedances case (averages-only + `[!]` notice)

**Checkpoint**: `uv run pytest` passes; `uv run home-water-usage --start-date 2025-01-01 --end-date 2025-12-31` opens a graph window (requires live credentials)

---

## Phase 4: User Story 2 — Override Display Settings via CLI Flags (Priority: P2)

**Goal**: Every `parameter_values.yaml` key has a working CLI flag override; CLI value
always wins over YAML default for that run only.

**Independent Test**: `uv run pytest tests/test_cli.py -v` — 100% key parity confirmed (SC-002)

### Tests for User Story 2

- [x] T024 [US2] Write parametrized test in `tests/test_cli.py`: for each YAML key in `parameter_values.yaml`, assert the corresponding CLI flag exists in argparse AND that passing it overrides the YAML default in the resulting `Config` object — **confirm test FAILS for any missing flag before T025**

### Implementation for User Story 2

- [x] T025 [US2] Audit `src/home_water_usage/cli.py` argparse against `parameter_values.yaml`: add any missing flags; ensure all 20 seasonal-line property flags are present (`--{season}-avg-color`, `--{season}-avg-width`, `--{season}-avg-style`, `--{season}-avg-label` for each of 5 seasons); ensure `--chart-type`, `--y-axis-percentile-cap`, `--y-axis-max`, `--legend-location` all present
- [x] T026 [US2] Run `uv run pytest tests/test_cli.py -v` — confirm SC-002: 100% key parity; fix any remaining gaps

**Checkpoint**: `uv run pytest tests/test_cli.py` passes; `uv run home-water-usage --start-date 2025-01-01 --end-date 2025-12-31 --graph-title "My Title"` shows custom title

---

## Phase 5: User Story 3 — Export Graph as PDF (Priority: P3)

**Goal**: `--save-pdf` writes `household-water-usage-{start}-to-{end}.pdf` to disk before
the interactive window opens; `--pdf-path` overrides full output path.

**Independent Test**: `uv run pytest tests/test_graph.py -v -k pdf` — PDF tests pass;
PDF file exists on disk before `plt.show()` called (SC-006)

### Tests for User Story 3

- [x] T027 [P] [US3] Write PDF tests in `tests/test_graph.py` (Agg backend): assert `--save-pdf` creates file at expected path before `plt.show()` called (mock `plt.show` to intercept); assert filename follows `household-water-usage-{start}-to-{end}.pdf` pattern; assert `--pdf-path` overrides directory + filename; assert `[✓] PDF saved to <path>` emitted
- [x] T028 [P] [US3] Write cleanup tests in `tests/test_storage.py`: assert run CSV deleted after graph by default; assert run CSV preserved with `--no-delete-temp`; assert HistoryCache never deleted regardless of `--no-delete-temp`; assert `--no-delete-temp` + `--refresh-cache` are independent (each affects only its own target)

### Implementation for User Story 3

- [x] T029 [US3] Add PDF save to `src/home_water_usage/renderers/line.py`: before `plt.show()`, if `config.save_pdf`, call `plt.savefig(pdf_path)` synchronously; resolve `pdf_path` from `config.pdf_path` (if set) else `config.pdf_output_dir / formatted_filename`; emit `[✓] PDF saved to {path}` via `status.success()`
- [x] T030 [US3] Implement cleanup in `src/home_water_usage/cli.py` `main()`: after graph returns, delete run CSV if `config.delete_temp_files` is true; never touch `water-usage-history.csv`
- [x] T031 [US3] Verify `--pdf-path`, `--pdf-output-dir`, `--pdf-filename-pattern`, `--save-pdf` flags are wired in `src/home_water_usage/cli.py` and flow through to `Config.pdf_path` / `Config.pdf_output_dir` / `Config.pdf_filename_pattern`

**Checkpoint**: `uv run pytest tests/test_graph.py tests/test_storage.py` — all pass; full suite still green

---

## Phase 6: Polish & Hardening

**Purpose**: Exponential backoff, all error paths verified, coverage gate, quickstart
validation.

- [x] T032 [P] Implement exponential backoff in `src/home_water_usage/fetch.py`: wrap Gmail API calls in retry loop (`max_retries` from Config); catch `googleapiclient.errors.HttpError` with status 429/500/503; sleep `2**attempt` seconds between retries; after retries exhausted, abort `[✗]` with "Likely cause: Gmail API unavailable"
- [x] T033 [P] Audit all `[✗]` error paths against FR-014 and quickstart.md Scenarios 9–10: credentials missing (all 3 paths), `temp_dir` unwritable, invalid date range, corrupt HistoryCache, Gmail API failure, missing renderer module — ensure each has `[✗]` + "Likely cause:" + remediation hint + exit code 1
- [x] T034 Run full test suite with coverage: `uv run pytest --cov=home_water_usage --cov-report=term-missing` — confirm ≥ 80% line coverage (SC-003); add targeted tests to close any gap below threshold
- [x] T035 Write warm-cache timing test in `tests/test_integration.py`: mock Gmail API to return empty (force cache-hit path); pre-populate `water-usage-history.csv` fixture; call `main()` and assert `time.time()` delta from entry to `plt.show()` call is < 10 s (SC-007); mock `plt.show` to capture call time; this test validates that no unexpected I/O blocks the warm-cache path
- [x] T036 Execute `quickstart.md` validation scenarios in order (Scenarios 1–10) with live Gmail credentials to confirm all success criteria (SC-001 through SC-008) are met in real operation — Scenarios 9 & 10 validated headless; Scenarios 1–8 script at `specs/001-water-usage-cli/t036-validation.sh`; Scenario 1 validated live (351 emails, 5 seasonal averages)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Requires Phase 1 complete — **blocks all user stories**
- **Phase 3 (US1)**: Requires Phase 2 complete
- **Phase 4 (US2)**: Requires Phase 2 complete; can overlap with Phase 3 after T010
- **Phase 5 (US3)**: Requires Phase 3 complete (PDF logic is in `renderers/line.py`)
- **Phase 6 (Polish)**: Requires Phases 3, 4, 5 complete (T035 timing test depends on T020 storage being implemented so history CSV fixture can be pre-populated)

### Within Each Phase

- Test tasks (`test_*.py`) MUST be written and confirmed failing (red) before their implementation tasks
- `status.py` (T007) and `models.py` (T008) can be written in parallel
- `config.py` (T009) depends on `models.py` (T008)
- `cli.py` (T010) depends on `config.py` (T009)
- All Phase 3 test tasks (T011–T015) can be written in parallel before any implementation
- T016 (integration test) requires T011–T015 to understand what to assert
- T017–T022 can be written in parallel once T011–T015 are confirmed failing
- T023 (wire pipeline) depends on T017–T022

### User Story Dependencies

- **US1 (P1)**: Depends on Phase 2 only. Independent of US2 and US3.
- **US2 (P2)**: Depends on Phase 2. Can audit/fix cli.py in parallel with US1 implementation.
- **US3 (P3)**: Depends on US1 (PDF goes into `renderers/line.py` which is implemented in T021).

---

## Parallel Execution Examples

### Phase 3 — Test Writing (all parallel)

```
Task T011: Write tests/test_auth.py
Task T012: Write tests/test_parse.py
Task T013: Write tests/test_fetch.py
Task T014: Write tests/test_storage.py
Task T015: Write tests/test_graph.py
```

### Phase 3 — Implementation (parallel after tests confirmed red)

```
Task T017: Implement auth.py
Task T018: Implement parse.py
Task T019: Implement fetch.py
Task T020: Implement storage.py
Task T021: Implement renderers/line.py
Task T022: Implement graph.py
→ then T023: Wire pipeline in cli.py (depends on all above)
```

### Phase 5 — Tests (parallel)

```
Task T027: Write PDF tests in test_graph.py
Task T028: Write cleanup tests in test_storage.py
```

### Phase 6 — Polish (parallel)

```
Task T032: Implement exponential backoff in fetch.py
Task T033: Audit all [✗] error paths
Task T035: Write warm-cache timing test
```

---

## Implementation Strategy

### MVP (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (**critical — blocks everything**)
3. Complete Phase 3: US1 — write tests first (red), then implement (green)
4. **STOP and VALIDATE**: `uv run pytest` passes; interactive graph opens with real Gmail data
5. Full pipeline working — this is the complete core value of the tool

### Incremental Delivery

1. Phase 1 + 2 → scaffold + Config foundation
2. Phase 3 (US1) → working graph from Gmail — **ship MVP**
3. Phase 4 (US2) → all CLI flags verified
4. Phase 5 (US3) → PDF export
5. Phase 6 → hardening, coverage gate, quickstart validation

---

## Notes

- **TDD is non-negotiable** (Constitution Principle IV): always confirm test FAILS before implementing
- `[P]` = different files, no dependency on incomplete tasks — safe to parallelize
- `[Story]` maps task to user story for traceability
- Commit after each test/implementation pair (red → green)
- `uv run pytest` must stay green throughout — never leave the suite broken
- `matplotlib.use("Agg")` MUST be set at the top of `tests/test_graph.py` (before any matplotlib import)
- Never log or print `credentials.json` or `token.json` contents — checked in Phase 6 T033
