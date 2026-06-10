# Data Pipeline & Visualization Requirements Checklist: Home Water Usage CLI

**Purpose**: Validate completeness, clarity, consistency, and measurability of data pipeline and visualization requirements before planning
**Created**: 2026-06-09
**Feature**: [spec.md](../spec.md)
**Depth**: Standard | **Audience**: Author self-review | **Timing**: Pre-planning

---

## Data Pipeline — Requirement Completeness

- [x] CHK001 - Is the Gmail search query fully specified — sender filter, date range encoding, and any subject/label constraints the API call will use? [Completeness, Gap, Spec §FR-005]
- [x] CHK002 - Is "3 buffer emails on each side" defined in terms of email body date or Gmail received date — and how are buffers counted when emails are non-contiguous (e.g., gaps of weeks)? [Completeness, Spec §FR-005]
- [x] CHK003 - Are all fields captured in the run-specific temp CSV fully enumerated? The spec states `date,gallons` — is `threshold` or `account` ever needed downstream (e.g., for account-mismatch warnings in FR-007)? [Completeness, Spec §FR-008]
- [x] CHK004 - Is the HistoryCache CSV schema fully specified — field names, deduplication strategy (what happens when a re-fetch returns a record whose date already exists in cache)? [Completeness, Spec §FR-018]
- [x] CHK005 - Are all conditions for a cache "miss" enumerated? The spec covers "date predates earliest cached record" and `--refresh-cache` — is a partially-overlapping range also a miss, or only a gap-fill? [Completeness, Spec §FR-018]

---

## Data Pipeline — Requirement Clarity

- [x] CHK006 - Is the `email_body_pattern` YAML key specified with its required named capture groups (e.g., `month`, `day`, `year`, `gallons`, `threshold`, `account`)? Without this, a user who changes the pattern cannot know which groups the parser expects. [Clarity, Spec §FR-007]
- [x] CHK007 - Is "cache miss" defined precisely for partial overlap — e.g., if cache holds Jan–Mar and user requests Feb–Apr, is only Apr fetched or is the whole range re-fetched? [Clarity, Spec §FR-018]
- [x] CHK008 - Is the behavior specified when `--refresh-cache` is passed but the Gmail API returns zero new emails (cache already up to date)? [Clarity, Spec §FR-018, Gap]
- [x] CHK009 - Does FR-006 ("use body date, not received date") apply to the buffer email selection logic in FR-005, or only to parsing/plotting? The interaction between these two requirements is unspecified. [Clarity, Spec §FR-005/FR-006]

---

## Data Pipeline — Requirement Consistency

- [x] CHK010 - Do FR-016 (run-specific temp CSV deleted by default) and FR-018 (HistoryCache persistent) clearly distinguish the two files — different filenames, different lifecycle, different deletion rules? [Consistency, Spec §FR-016/FR-018]
- [x] CHK011 - Is the relationship between `--no-delete-temp` and the HistoryCache specified? Does `--no-delete-temp` affect only the run CSV, only the cache, or both? [Consistency, Spec §FR-016/FR-018, Gap]
- [x] CHK012 - Are the account-number validation requirements in FR-007 consistent with the account stored in `parameter_values.yaml`? Does a mismatch abort the run or log a warning and continue? [Consistency, Spec §FR-007]

---

## Data Pipeline — Edge Case & Exception Coverage

- [x] CHK013 - Are requirements defined for duplicate emails in Gmail (two messages with the same body date)? Should the parser keep the first, last, or both records? [Coverage, Edge Case, Gap]
- [x] CHK014 - Are requirements defined for malformed date values in otherwise-parseable email bodies (e.g., impossible dates like "June 32")? [Coverage, Edge Case, Gap]
- [x] CHK015 - Are requirements specified when `temp_dir` does not exist or is not writable at runtime? [Coverage, Exception Flow, Gap]
- [x] CHK016 - Are requirements defined when the HistoryCache file exists but is corrupt or unparseable (e.g., truncated file, wrong schema)? [Coverage, Exception Flow, Gap]
- [x] CHK017 - Is behavior specified when `--refresh-cache` is combined with `--no-delete-temp`? These flags interact but their combined behavior is not addressed. [Coverage, Edge Case, Spec §FR-016/FR-018, Gap]

---

## Data Pipeline — Measurability

- [x] CHK018 - Is the measurement boundary for SC-007 ("warm cache run reaches graph render in under 10 seconds") clearly defined — what event starts the clock and what event stops it? [Measurability, Spec §SC-007]
- [x] CHK019 - Is there a measurable success criterion for parse completeness — e.g., "all emails in range whose body matches `email_body_pattern` produce a UsageRecord"? The spec defines error behavior but not a completeness target. [Measurability, Gap]

---

## Visualization — Requirement Completeness

- [x] CHK020 - Are the visual properties of line breaks (gaps) specified beyond "line breaks"? e.g., minimum gap width, whether gaps shorter than one day are rendered differently. [Completeness, Spec §FR-009, Gap]
- [x] CHK021 - Is the legend entry for the gap note fully specified — position relative to seasonal average entries, format, whether it appears when no gaps exist in the displayed range? [Completeness, Spec §FR-009, Gap]
- [x] CHK022 - Are all five seasonal average line visual properties (color, dash style, label text, line width) individually specified, or only collectively via shared YAML keys? [Completeness, Spec §FR-010]
- [x] CHK023 - Are requirements defined for the interactive window itself — window title, resize behavior, zoom/pan support, or minimum window dimensions? [Completeness, Spec §FR-011, Gap]
- [x] CHK024 - Are graph requirements defined for degenerate date ranges — e.g., a single-day range, or a range where all data points have identical gallon values? [Completeness, Edge Case, Gap]

---

## Visualization — Requirement Clarity

- [x] CHK025 - Is "rendered simultaneously" (FR-012, PDF + window) unambiguously defined — does it mean both are initiated before either one blocks execution, or that neither appears until both are fully ready? [Clarity, Spec §FR-012]
- [x] CHK026 - Is the pluggable renderer contract (FR-019) specified in terms of interface — what inputs and outputs must a renderer module accept and return to be considered valid? Without this, "new types can be added" is untestable. [Clarity, Spec §FR-019, Gap]
- [x] CHK027 - Does `--pdf-path` override the full file path (directory + filename) or only the directory? FR-012 specifies a default filename pattern but the override behavior is ambiguous. [Clarity, Spec §FR-012, Gap]
- [x] CHK028 - Is the y-axis auto-scale behavior specified for extreme outlier data points that would compress all other data to near-flat? [Clarity, Gap]

---

## Visualization — Requirement Consistency

- [x] CHK029 - Are the graph default visual properties in FR-009/FR-010 consistent with the YAML key set defined in the PRD's `parameter_values.yaml` sample — specifically axis label text, title text, and gap legend label? [Consistency, Spec §FR-009/FR-010]
- [x] CHK030 - Does the `chart_type` YAML key (FR-019) appear in the full `parameter_values.yaml` key set, and is its default value (`line`) explicitly stated? [Consistency, Spec §FR-019, Gap]

---

## Visualization — Scenario Coverage

- [x] CHK031 - Are display requirements defined for when only one average line is available (e.g., Annual only, no seasonal breakdown yet due to sparse history)? [Coverage, Spec §FR-010]
- [x] CHK032 - Are requirements specified for the graph when the requested date range contains data only in the buffer zone — i.e., all plotted in-range days have no exceedances and the line is entirely absent? [Coverage, Edge Case, Gap]
- [x] CHK033 - Are requirements defined for very long date ranges (e.g., multi-year) where x-axis tick density would become unreadable at the default `date_format`? [Coverage, Edge Case, Gap]

---

## Visualization — Measurability

- [x] CHK034 - Is "valid invocation" in SC-001 ("100% of valid invocations render a graph") precisely defined — what conditions make an invocation valid vs invalid? [Measurability, Spec §SC-001]
- [x] CHK035 - Is SC-006 ("PDF saved before window opens, verifiable by filesystem timestamp") measurable in practice — is there a defined tolerance, or is it strictly atomic (zero gap between save and window open)? [Measurability, Spec §SC-006]

---

## Notes

- Check items off as resolved: `[x]`
- Add inline notes with findings, decisions made, or spec section updated.
- **Gap resolution session 2026-06-09**: 19/19 [Gap] items resolved.
- **Clarity/Consistency/Measurability session 2026-06-09**: 16/16 remaining items resolved.
- **Final status: 35/35 items passing. Spec is ready for `/speckit-plan`.**
