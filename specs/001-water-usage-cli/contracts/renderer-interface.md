# Renderer Interface Contract

**Phase 1 Output** | **Date**: 2026-06-09 | **Data Model**: [data-model.md](../data-model.md)

---

## Interface

Every renderer module in `src/home_water_usage/renderers/` MUST expose exactly one public
function with this signature:

```python
def render(
    records: list[UsageRecord],
    averages: list[SeasonalAverage],
    config: Config,
) -> None:
    ...
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `records` | `list[UsageRecord]` | In-range plotted records only (buffer records excluded). May be empty (averages-only case). |
| `averages` | `list[SeasonalAverage]` | Seasonal averages computed from HistoryCache. May contain 1–5 items; missing seasons already filtered out. |
| `config` | `Config` | Fully merged runtime config. All display properties read from here. |

### Return value

`None`. Side effects only: renders to screen and/or writes PDF.

### Responsibilities

A renderer MUST:
1. Render a Seaborn line graph (or equivalent for the chart type)
2. Apply all visual properties from `config` (title, axis labels, colors, etc.)
3. Overlay seasonal average lines from `averages`
4. Break the usage line on `NaN` gaps (missing days)
5. Apply y-axis cap per `config.y_axis_percentile_cap` (or `config.y_axis_max` if set)
6. Apply `AutoDateLocator` + `DateFormatter(config.date_format)` to x-axis
7. Show gap legend note only when gaps exist in the displayed range
8. Write PDF synchronously (before `plt.show()`) if `config.save_pdf` is true
9. Call `plt.show()` to open the interactive window
10. Emit `[✓] PDF saved to {path}` via `status` module if PDF was written

A renderer MUST NOT:
- Call Gmail API or read/write CSV files
- Print status messages except `[✓] PDF saved` (status is `graph.py`'s responsibility)
- Modify the `config` object

---

## Dispatch

`graph.py` dispatches to the active renderer using `chart_type` from Config:

```python
# graph.py
import importlib

def dispatch_render(records, averages, config):
    module = importlib.import_module(
        f"home_water_usage.renderers.{config.chart_type}"
    )
    module.render(records, averages, config)
```

If the module does not exist or does not expose `render`, `graph.py` aborts with `[✗]`.

---

## Adding a New Chart Type

1. Create `src/home_water_usage/renderers/{chart_type}.py`
2. Implement `render(records, averages, config) → None` per the contract above
3. Add `{chart_type}` as a valid value for `chart_type` in `parameter_values.yaml` docs
4. Write `tests/test_graph.py` test(s) for the new renderer

No changes to existing renderer code or `graph.py` dispatch logic are required.

---

## Default Renderer: `line`

Module: `src/home_water_usage/renderers/line.py`

Selected when `config.chart_type == "line"` (the default).

Renders a Seaborn line plot with:
- One continuous usage line (with `NaN` gaps for missing days)
- Up to 5 horizontal dotted seasonal average overlay lines
- Y-axis percentile cap or explicit max
- AutoDateLocator x-axis
- Interactive Matplotlib toolbar (zoom, pan, save-to-file)
- Optional PDF export (written before `plt.show()`)
