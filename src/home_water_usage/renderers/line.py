"""Default line renderer: Seaborn line graph with seasonal average overlays."""
from __future__ import annotations

from datetime import timedelta

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from home_water_usage import status
from home_water_usage.models import SeasonalAverage, UsageRecord


def render(records: list[UsageRecord], averages: list[SeasonalAverage], config) -> None:
    """Render an interactive Seaborn line graph with seasonal average overlays."""
    # Build date range
    if records:
        start = min(r.date for r in records)
        end = max(r.date for r in records)
    else:
        start = config.start_date
        end = config.end_date

    all_dates = pd.date_range(start=start, end=end, freq="D")
    record_map = {r.date: r.gallons for r in records}
    gallons = [float(record_map[d.date()]) if d.date() in record_map else np.nan for d in all_dates]
    df = pd.DataFrame({"date": all_dates, "gallons": gallons})

    # Compute y-axis cap
    valid = df["gallons"].dropna()
    if len(valid) > 0:
        cap = float(np.nanpercentile(valid.values, config.y_axis_percentile_cap))
    else:
        cap = None

    if config.y_axis_max is not None:
        cap = float(config.y_axis_max)

    # Clip outliers and warn
    if cap is not None:
        clipped_mask = df["gallons"] > cap
        if clipped_mask.any():
            for _, row in df[clipped_mask].iterrows():
                status.warning(
                    f"Value {row['gallons']:.0f} gal on {row['date'].date()} clipped to {cap:.0f}."
                )
            df.loc[clipped_mask, "gallons"] = cap

    fig, ax = plt.subplots(figsize=(14, 6))

    if len(valid) > 0:
        sns.lineplot(data=df, x="date", y="gallons", ax=ax)

    # Seasonal average overlays
    for avg in averages:
        ax.axhline(
            avg.avg_gallons,
            color=getattr(config, f"{avg.season}_avg_color"),
            linewidth=getattr(config, f"{avg.season}_avg_width"),
            linestyle=getattr(config, f"{avg.season}_avg_style"),
            label=getattr(config, f"{avg.season}_avg_label"),
        )

    ax.set_title(config.graph_title)
    ax.set_xlabel(config.x_axis_label)
    ax.set_ylabel(config.y_axis_label)

    # Gap note in legend only when gaps are present
    has_gaps = df["gallons"].isna().any()
    if has_gaps:
        ax.plot([], [], " ", label=config.gap_label)

    ax.legend(loc=config.legend_location)

    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter(config.date_format))
    fig.autofmt_xdate()

    plt.tight_layout()
    plt.show()
