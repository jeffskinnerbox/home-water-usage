"""Shared pytest fixtures and one-time setup for all test modules."""
import dataclasses
from datetime import date

import matplotlib
matplotlib.use("Agg")  # must be before any pyplot import

import pytest

from home_water_usage.config import Config


@pytest.fixture
def base_config(tmp_path):
    return Config(
        start_date=date(2025, 6, 1),
        end_date=date(2025, 6, 30),
        gmail_query_filter="from:no-reply@leesburgva.gov",
        buffer_email_count=3,
        max_retries=2,
        account_number="40002423000",
        email_body_pattern=(
            r"On (?P<month>\w+) (?P<day>\d{1,2}), (?P<year>\d{4}), your water usage of "
            r"(?P<gallons>\d+) exceeded your threshold of (?P<threshold>\d+) for account "
            r"(?P<account>\d+)\."
        ),
        credentials_path=str(tmp_path / "credentials.json"),
        token_path=str(tmp_path / "token.json"),
        temp_dir=str(tmp_path),
        delete_temp_files=True,
        refresh_cache=False,
        graph_title="Household Water Usage",
        x_axis_label="Date",
        y_axis_label="Gallons",
        gap_label="gaps = usage within threshold",
        date_format="%b %Y",
        chart_type="line",
        y_axis_percentile_cap=99,
        y_axis_max=None,
        legend_location="best",
        annual_avg_color="black",
        annual_avg_width=2.0,
        annual_avg_style="dotted",
        annual_avg_label="Annual avg",
        winter_avg_color="steelblue",
        winter_avg_width=1.5,
        winter_avg_style="dotted",
        winter_avg_label="Winter avg",
        spring_avg_color="mediumseagreen",
        spring_avg_width=1.5,
        spring_avg_style="dotted",
        spring_avg_label="Spring avg",
        summer_avg_color="tomato",
        summer_avg_width=1.5,
        summer_avg_style="dotted",
        summer_avg_label="Summer avg",
        fall_avg_color="darkorange",
        fall_avg_width=1.5,
        fall_avg_style="dotted",
        fall_avg_label="Fall avg",
        save_pdf=False,
        pdf_output_dir=str(tmp_path),
        pdf_filename_pattern="household-water-usage-{start_date}-to-{end_date}.pdf",
        pdf_path=None,
    )


@pytest.fixture
def sample_records():
    from home_water_usage.models import UsageRecord
    return [
        UsageRecord(date=date(2025, 6, 15), gallons=150),
        UsageRecord(date=date(2025, 6, 20), gallons=200),
        UsageRecord(date=date(2025, 6, 25), gallons=180),
    ]
