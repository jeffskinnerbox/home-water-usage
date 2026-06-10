"""Config dataclass — merged result of parameter_values.yaml + CLI overrides."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Optional


@dataclass
class Config:
    # Required (no YAML default — must come from CLI)
    start_date: date
    end_date: date

    # Gmail
    gmail_query_filter: str
    buffer_email_count: int
    max_retries: int
    account_number: str
    email_body_pattern: str

    # Credentials
    credentials_path: str
    token_path: str

    # Storage
    temp_dir: str
    delete_temp_files: bool
    refresh_cache: bool

    # Graph display
    graph_title: str
    x_axis_label: str
    y_axis_label: str
    gap_label: str
    date_format: str
    chart_type: str
    y_axis_percentile_cap: int
    y_axis_max: Optional[float]
    legend_location: str

    # Seasonal average lines (4 properties × 5 seasons = 20 keys)
    annual_avg_color: str
    annual_avg_width: float
    annual_avg_style: str
    annual_avg_label: str

    winter_avg_color: str
    winter_avg_width: float
    winter_avg_style: str
    winter_avg_label: str

    spring_avg_color: str
    spring_avg_width: float
    spring_avg_style: str
    spring_avg_label: str

    summer_avg_color: str
    summer_avg_width: float
    summer_avg_style: str
    summer_avg_label: str

    fall_avg_color: str
    fall_avg_width: float
    fall_avg_style: str
    fall_avg_label: str

    # PDF export
    save_pdf: bool
    pdf_output_dir: str
    pdf_filename_pattern: str
    pdf_path: Optional[str]

    @classmethod
    def from_dict(cls, d: dict) -> Config:
        """Build Config from a merged YAML+CLI dict.

        Handles type coercion: dates parsed from YYYY-MM-DD strings, ints/floats
        cast from strings (when supplied via CLI), None preserved for optional fields.
        """
        def _date(v) -> date:
            if isinstance(v, date):
                return v
            return datetime.strptime(str(v), "%Y-%m-%d").date()

        def _int(v) -> int:
            return int(v)

        def _float(v) -> float:
            return float(v)

        def _opt_float(v) -> Optional[float]:
            return None if v is None else float(v)

        def _opt_str(v) -> Optional[str]:
            return None if v is None else str(v)

        def _bool(v) -> bool:
            if isinstance(v, bool):
                return v
            return str(v).lower() in ("true", "1", "yes")

        return cls(
            start_date=_date(d["start_date"]),
            end_date=_date(d["end_date"]),
            gmail_query_filter=str(d["gmail_query_filter"]),
            buffer_email_count=_int(d["buffer_email_count"]),
            max_retries=_int(d["max_retries"]),
            account_number=str(d["account_number"]),
            email_body_pattern=str(d["email_body_pattern"]),
            credentials_path=str(d["credentials_path"]),
            token_path=str(d["token_path"]),
            temp_dir=str(Path(str(d["temp_dir"])).expanduser()),
            delete_temp_files=_bool(d["delete_temp_files"]),
            refresh_cache=_bool(d["refresh_cache"]),
            graph_title=str(d["graph_title"]),
            x_axis_label=str(d["x_axis_label"]),
            y_axis_label=str(d["y_axis_label"]),
            gap_label=str(d["gap_label"]),
            date_format=str(d["date_format"]),
            chart_type=str(d["chart_type"]),
            y_axis_percentile_cap=_int(d["y_axis_percentile_cap"]),
            y_axis_max=_opt_float(d.get("y_axis_max")),
            legend_location=str(d["legend_location"]),
            annual_avg_color=str(d["annual_avg_color"]),
            annual_avg_width=_float(d["annual_avg_width"]),
            annual_avg_style=str(d["annual_avg_style"]),
            annual_avg_label=str(d["annual_avg_label"]),
            winter_avg_color=str(d["winter_avg_color"]),
            winter_avg_width=_float(d["winter_avg_width"]),
            winter_avg_style=str(d["winter_avg_style"]),
            winter_avg_label=str(d["winter_avg_label"]),
            spring_avg_color=str(d["spring_avg_color"]),
            spring_avg_width=_float(d["spring_avg_width"]),
            spring_avg_style=str(d["spring_avg_style"]),
            spring_avg_label=str(d["spring_avg_label"]),
            summer_avg_color=str(d["summer_avg_color"]),
            summer_avg_width=_float(d["summer_avg_width"]),
            summer_avg_style=str(d["summer_avg_style"]),
            summer_avg_label=str(d["summer_avg_label"]),
            fall_avg_color=str(d["fall_avg_color"]),
            fall_avg_width=_float(d["fall_avg_width"]),
            fall_avg_style=str(d["fall_avg_style"]),
            fall_avg_label=str(d["fall_avg_label"]),
            save_pdf=_bool(d["save_pdf"]),
            pdf_output_dir=str(d["pdf_output_dir"]),
            pdf_filename_pattern=str(d["pdf_filename_pattern"]),
            pdf_path=_opt_str(d.get("pdf_path")),
        )
