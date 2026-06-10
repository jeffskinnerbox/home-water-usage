"""Seasonal average computation and renderer dispatch."""
from __future__ import annotations

import importlib

from home_water_usage import status
from home_water_usage.models import SeasonalAverage, UsageRecord

_SEASON_MONTHS = {
    "annual": set(range(1, 13)),
    "winter": {12, 1, 2},
    "spring": {3, 4, 5},
    "summer": {6, 7, 8},
    "fall": {9, 10, 11},
}


def compute_seasonal_averages(records: list[UsageRecord], config) -> list[SeasonalAverage]:
    """Compute mean gallons per season from records. Omits seasons with no data."""
    if not records:
        return []

    averages: list[SeasonalAverage] = []
    for season, months in _SEASON_MONTHS.items():
        season_records = [r for r in records if r.date.month in months]
        if not season_records:
            status.warning(f"No data for {season} season — average line omitted.")
            continue
        avg = sum(r.gallons for r in season_records) / len(season_records)
        averages.append(SeasonalAverage(season=season, avg_gallons=avg))

    return averages


def dispatch_render(records: list[UsageRecord], averages: list[SeasonalAverage], config) -> None:
    """Load renderer by chart_type and call render(records, averages, config)."""
    module_path = f"home_water_usage.renderers.{config.chart_type}"
    try:
        renderer = importlib.import_module(module_path)
    except ModuleNotFoundError:
        status.error(
            f"Renderer module '{module_path}' not found.",
            likely_cause=f"chart_type='{config.chart_type}' has no matching renderer module.",
            remediation="Set --chart-type to 'line' or create a custom renderer at that module path.",
        )

    if not hasattr(renderer, "render"):
        status.error(
            f"Renderer module '{module_path}' has no render() function.",
            likely_cause="The renderer module is missing render(records, averages, config).",
        )

    renderer.render(records, averages, config)
