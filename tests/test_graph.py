"""Tests for graph.py and renderers/line.py. Uses Agg backend (set in conftest.py)."""
import dataclasses
from datetime import date
from pathlib import Path
from unittest.mock import patch

import matplotlib.pyplot as plt
import numpy as np
import pytest

from home_water_usage.models import SeasonalAverage, UsageRecord


def _make_records(n=10, start=date(2025, 6, 1), gallons=150):
    from datetime import timedelta
    return [UsageRecord(date=start + timedelta(days=i), gallons=gallons) for i in range(n)]


# ---------------------------------------------------------------------------
# compute_seasonal_averages
# ---------------------------------------------------------------------------

def test_seasonal_averages_computed(base_config, sample_records):
    from home_water_usage.graph import compute_seasonal_averages

    # All sample_records are in June (summer)
    averages = compute_seasonal_averages(sample_records, base_config)
    seasons = {a.season for a in averages}
    assert "summer" in seasons
    assert "annual" in seasons


def test_missing_season_omitted_with_warning(base_config):
    from home_water_usage.graph import compute_seasonal_averages

    # Only summer records (June)
    records = _make_records(n=5, start=date(2025, 6, 1))
    with patch("home_water_usage.graph.status") as mock_status:
        averages = compute_seasonal_averages(records, base_config)

    seasons = {a.season for a in averages}
    # winter, spring, fall should be missing
    for missing in ("winter", "spring", "fall"):
        assert missing not in seasons
    # warning emitted for each missing season
    assert mock_status.warning.call_count >= 3


def test_empty_records_returns_empty(base_config):
    from home_water_usage.graph import compute_seasonal_averages

    assert compute_seasonal_averages([], base_config) == []


# ---------------------------------------------------------------------------
# dispatch_render
# ---------------------------------------------------------------------------

def test_dispatch_render_calls_line_render(base_config, sample_records):
    from home_water_usage.graph import dispatch_render

    with patch("home_water_usage.renderers.line.render") as mock_render, \
         patch("matplotlib.pyplot.show"):
        dispatch_render(sample_records, [], base_config)

    mock_render.assert_called_once()


def test_dispatch_render_unknown_type_exits(base_config, sample_records):
    from home_water_usage.graph import dispatch_render

    config = dataclasses.replace(base_config, chart_type="nonexistent_renderer")
    with pytest.raises(SystemExit) as exc:
        dispatch_render(sample_records, [], config)
    assert exc.value.code == 1


def test_dispatch_render_module_missing_render_fn_exits(base_config, sample_records):
    """Module found but has no render() attribute → [✗] exit 1."""
    import types
    from home_water_usage.graph import dispatch_render

    fake_module = types.ModuleType("home_water_usage.renderers.fake")

    with patch("home_water_usage.graph.importlib.import_module", return_value=fake_module):
        with pytest.raises(SystemExit) as exc:
            dispatch_render(sample_records, [], base_config)
    assert exc.value.code == 1


# ---------------------------------------------------------------------------
# renderers/line.py — figure properties
# ---------------------------------------------------------------------------

def test_figure_has_correct_title_and_labels(base_config, sample_records):
    from home_water_usage.renderers.line import render

    with patch("matplotlib.pyplot.show"):
        render(sample_records, [], base_config)

    ax = plt.gca()
    assert ax.get_title() == base_config.graph_title
    assert ax.get_xlabel() == base_config.x_axis_label
    assert ax.get_ylabel() == base_config.y_axis_label
    plt.close("all")


def test_seasonal_average_lines_in_legend(base_config, sample_records):
    from home_water_usage.renderers.line import render

    averages = [
        SeasonalAverage(season="annual", avg_gallons=160),
        SeasonalAverage(season="summer", avg_gallons=175),
    ]
    with patch("matplotlib.pyplot.show"):
        render(sample_records, averages, base_config)

    ax = plt.gca()
    legend = ax.get_legend()
    labels = [t.get_text() for t in legend.get_texts()]
    assert base_config.annual_avg_label in labels
    assert base_config.summer_avg_label in labels
    plt.close("all")


def test_nan_gaps_in_dataframe(base_config):
    """Renderer builds a full date-range DataFrame with NaN for missing days."""
    import dataclasses
    from home_water_usage.renderers import line as line_module

    # Records for June 1 and June 5 (gap on June 2–4)
    records = [
        UsageRecord(date=date(2025, 6, 1), gallons=100),
        UsageRecord(date=date(2025, 6, 5), gallons=200),
    ]
    # Use y_axis_max to avoid percentile clipping interfering with the assertion
    config = dataclasses.replace(base_config, y_axis_max=500.0)

    with patch("home_water_usage.renderers.line.sns") as mock_sns, \
         patch("matplotlib.pyplot.show"), \
         patch("matplotlib.pyplot.subplots", return_value=(plt.figure(), plt.axes())):
        # Call render; capture what DataFrame was passed to sns.lineplot
        line_module.render(records, [], config)

    call_kwargs = mock_sns.lineplot.call_args[1]
    df = call_kwargs["data"]
    assert df["gallons"].isna().any(), "Expected NaN gaps in rendered DataFrame"
    plt.close("all")


def test_y_axis_cap_clips_outlier(base_config):
    from home_water_usage.renderers.line import render

    # 9 records at 100, 1 extreme outlier at 10000
    records = [UsageRecord(date=date(2025, 6, d), gallons=100) for d in range(1, 10)]
    records.append(UsageRecord(date=date(2025, 6, 10), gallons=10000))

    config = dataclasses.replace(base_config, y_axis_percentile_cap=90)

    with patch("matplotlib.pyplot.show"):
        with patch("home_water_usage.renderers.line.status") as mock_status:
            render(records, [], config)

    # [!] warning should be emitted for the clipped value
    mock_status.warning.assert_called()
    plt.close("all")


def test_y_axis_max_override(base_config, sample_records):
    from home_water_usage.renderers.line import render

    config = dataclasses.replace(base_config, y_axis_max=500.0)

    with patch("matplotlib.pyplot.show"):
        render(sample_records, [], config)

    plt.close("all")


def test_annual_only_renders_without_error(base_config):
    """Annual-only averages case: no other seasons → render completes."""
    from home_water_usage.renderers.line import render

    records = _make_records(n=5)
    averages = [SeasonalAverage(season="annual", avg_gallons=160)]

    with patch("matplotlib.pyplot.show"):
        render(records, averages, base_config)

    plt.close("all")


def test_empty_records_renders_without_error(base_config):
    """No exceedances → render with just averages (no line data)."""
    from home_water_usage.renderers.line import render

    averages = [SeasonalAverage(season="annual", avg_gallons=160)]

    with patch("matplotlib.pyplot.show"):
        render([], averages, base_config)

    plt.close("all")


def test_gap_label_in_legend_when_gaps_present(base_config):
    """Gap label appears in legend only when there are NaN gaps."""
    from home_water_usage.renderers.line import render

    records = [
        UsageRecord(date=date(2025, 6, 1), gallons=100),
        UsageRecord(date=date(2025, 6, 10), gallons=120),  # 8-day gap
    ]
    with patch("matplotlib.pyplot.show"):
        render(records, [], base_config)

    ax = plt.gca()
    legend = ax.get_legend()
    labels = [t.get_text() for t in legend.get_texts()]
    assert base_config.gap_label in labels
    plt.close("all")


# ---------------------------------------------------------------------------
# PDF export (T027)
# ---------------------------------------------------------------------------

def test_save_pdf_creates_file_before_show(base_config, sample_records):
    """save_pdf=True creates PDF at expected path before plt.show() is called."""
    from home_water_usage.renderers.line import render

    config = dataclasses.replace(base_config, save_pdf=True)
    expected_name = config.pdf_filename_pattern.format(
        start_date=config.start_date, end_date=config.end_date
    )
    expected_path = Path(config.pdf_output_dir) / expected_name
    pdf_exists_at_show = {}

    def _check_at_show():
        pdf_exists_at_show["exists"] = expected_path.exists()

    with patch("matplotlib.pyplot.show", side_effect=_check_at_show):
        render(sample_records, [], config)

    assert pdf_exists_at_show.get("exists"), "PDF must exist before plt.show()"
    plt.close("all")


def test_save_pdf_filename_follows_pattern(base_config, sample_records):
    """PDF filename matches pdf_filename_pattern with start/end dates."""
    from home_water_usage.renderers.line import render

    config = dataclasses.replace(base_config, save_pdf=True)
    expected_name = config.pdf_filename_pattern.format(
        start_date=config.start_date, end_date=config.end_date
    )

    with patch("matplotlib.pyplot.show"):
        render(sample_records, [], config)

    assert (Path(config.pdf_output_dir) / expected_name).exists()
    plt.close("all")


def test_pdf_path_override(base_config, sample_records, tmp_path):
    """pdf_path overrides pdf_output_dir + pdf_filename_pattern."""
    from home_water_usage.renderers.line import render

    custom_path = str(tmp_path / "custom_output.pdf")
    config = dataclasses.replace(base_config, save_pdf=True, pdf_path=custom_path)

    with patch("matplotlib.pyplot.show"):
        render(sample_records, [], config)

    assert Path(custom_path).exists()
    plt.close("all")


def test_save_pdf_emits_success_message(base_config, sample_records):
    """save_pdf emits status.success containing 'PDF saved'."""
    from home_water_usage.renderers.line import render

    config = dataclasses.replace(base_config, save_pdf=True)

    with patch("home_water_usage.renderers.line.status") as mock_status, \
         patch("matplotlib.pyplot.show"):
        render(sample_records, [], config)

    success_calls = [str(c) for c in mock_status.success.call_args_list]
    assert any("PDF saved" in c for c in success_calls)
    plt.close("all")


def test_no_save_pdf_no_file_created(base_config, sample_records):
    """save_pdf=False → no PDF file written."""
    from home_water_usage.renderers.line import render

    # base_config has save_pdf=False
    with patch("matplotlib.pyplot.show"):
        render(sample_records, [], base_config)

    expected_name = base_config.pdf_filename_pattern.format(
        start_date=base_config.start_date, end_date=base_config.end_date
    )
    assert not (Path(base_config.pdf_output_dir) / expected_name).exists()
    plt.close("all")
