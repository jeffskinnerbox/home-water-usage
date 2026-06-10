"""Tests for cli.py: YAML key parity, required args, date validation."""
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

YAML_PATH = Path(__file__).parent.parent / "parameter_values.yaml"

# YAML keys whose CLI flag deviates from the standard foo_bar → --foo-bar rule.
SPECIAL_FLAG_MAP = {
    "delete_temp_files": "--no-delete-temp",
}


def _yaml_key_to_flag(key: str) -> str:
    return SPECIAL_FLAG_MAP.get(key, "--" + key.replace("_", "-"))


# ---------------------------------------------------------------------------
# Key parity
# ---------------------------------------------------------------------------

def test_yaml_key_parity():
    """Every key in parameter_values.yaml has a corresponding CLI flag."""
    from home_water_usage.cli import build_parser

    with open(YAML_PATH) as f:
        yaml_defaults = yaml.safe_load(f)

    parser = build_parser()
    option_strings = set(parser._option_string_actions.keys())

    missing = []
    for key in yaml_defaults:
        flag = _yaml_key_to_flag(key)
        if flag not in option_strings:
            missing.append(f"  YAML key '{key}' → expected flag '{flag}' not found")

    assert not missing, "Missing CLI flags:\n" + "\n".join(missing)


# ---------------------------------------------------------------------------
# Required arguments
# ---------------------------------------------------------------------------

def test_start_date_required():
    """--start-date is required; omitting it exits non-zero."""
    from home_water_usage.cli import build_parser

    parser = build_parser()
    with pytest.raises(SystemExit) as exc:
        parser.parse_args(["--end-date", "2025-12-31"])
    assert exc.value.code != 0


def test_end_date_required():
    """--end-date is required; omitting it exits non-zero."""
    from home_water_usage.cli import build_parser

    parser = build_parser()
    with pytest.raises(SystemExit) as exc:
        parser.parse_args(["--start-date", "2025-01-01"])
    assert exc.value.code != 0


# ---------------------------------------------------------------------------
# Date range validation
# ---------------------------------------------------------------------------

def test_start_after_end_exits_nonzero():
    """start_date > end_date must abort with exit code 1."""
    with patch("sys.argv", [
        "home-water-usage",
        "--start-date", "2025-12-31",
        "--end-date", "2025-01-01",
    ]):
        with pytest.raises(SystemExit) as exc:
            from home_water_usage import cli
            cli.main()
    assert exc.value.code == 1


def test_equal_dates_accepted():
    """start_date == end_date is valid (single-day range)."""
    from home_water_usage.cli import build_parser, build_config

    parser = build_parser()
    args = parser.parse_args(["--start-date", "2025-06-15", "--end-date", "2025-06-15"])
    with open(YAML_PATH) as f:
        yaml_defaults = yaml.safe_load(f)
    # Should not raise
    config = build_config(args, yaml_defaults)
    assert config.start_date == config.end_date


# ---------------------------------------------------------------------------
# CLI override beats YAML default
# ---------------------------------------------------------------------------

def test_cli_flag_overrides_yaml_default():
    """A CLI flag value takes precedence over the YAML default."""
    from home_water_usage.cli import build_parser, build_config

    parser = build_parser()
    args = parser.parse_args([
        "--start-date", "2025-01-01",
        "--end-date", "2025-12-31",
        "--graph-title", "My Custom Title",
    ])
    with open(YAML_PATH) as f:
        yaml_defaults = yaml.safe_load(f)
    config = build_config(args, yaml_defaults)
    assert config.graph_title == "My Custom Title"


def test_no_delete_temp_flag_sets_delete_false():
    """--no-delete-temp sets delete_temp_files=False regardless of YAML default."""
    from home_water_usage.cli import build_parser, build_config

    parser = build_parser()
    args = parser.parse_args([
        "--start-date", "2025-01-01",
        "--end-date", "2025-12-31",
        "--no-delete-temp",
    ])
    with open(YAML_PATH) as f:
        yaml_defaults = yaml.safe_load(f)
    config = build_config(args, yaml_defaults)
    assert config.delete_temp_files is False


def test_save_pdf_flag_sets_true():
    """--save-pdf sets save_pdf=True regardless of YAML default."""
    from home_water_usage.cli import build_parser, build_config

    parser = build_parser()
    args = parser.parse_args([
        "--start-date", "2025-01-01",
        "--end-date", "2025-12-31",
        "--save-pdf",
    ])
    with open(YAML_PATH) as f:
        yaml_defaults = yaml.safe_load(f)
    config = build_config(args, yaml_defaults)
    assert config.save_pdf is True


def test_buffer_email_count_type():
    """--buffer-email-count parses as int."""
    from home_water_usage.cli import build_parser, build_config

    parser = build_parser()
    args = parser.parse_args([
        "--start-date", "2025-01-01",
        "--end-date", "2025-12-31",
        "--buffer-email-count", "7",
    ])
    with open(YAML_PATH) as f:
        yaml_defaults = yaml.safe_load(f)
    config = build_config(args, yaml_defaults)
    assert config.buffer_email_count == 7
    assert isinstance(config.buffer_email_count, int)


# ---------------------------------------------------------------------------
# SC-002: every YAML key overrides correctly via its CLI flag (T024)
# ---------------------------------------------------------------------------

_BASE_ARGS = ["--start-date", "2025-01-01", "--end-date", "2025-12-31"]

# (yaml_key, extra_cli_args, config_attr, expected_value)
_OVERRIDE_CASES = [
    ("gmail_query_filter",     ["--gmail-query-filter", "from:test@test.com"],          "gmail_query_filter",     "from:test@test.com"),
    ("buffer_email_count",     ["--buffer-email-count", "10"],                           "buffer_email_count",     10),
    ("max_retries",            ["--max-retries", "5"],                                   "max_retries",            5),
    ("account_number",         ["--account-number", "99999999"],                         "account_number",         "99999999"),
    ("email_body_pattern",     ["--email-body-pattern", "(?P<month>\\w+) (?P<day>\\d+) (?P<year>\\d+) (?P<gallons>\\d+)"],
                                                                                         "email_body_pattern",     "(?P<month>\\w+) (?P<day>\\d+) (?P<year>\\d+) (?P<gallons>\\d+)"),
    ("credentials_path",       ["--credentials-path", "/tmp/creds.json"],               "credentials_path",       "/tmp/creds.json"),
    ("token_path",             ["--token-path", "/tmp/token.json"],                     "token_path",             "/tmp/token.json"),
    ("temp_dir",               ["--temp-dir", "/tmp/testdir"],                          "temp_dir",               "/tmp/testdir"),
    ("delete_temp_files",      ["--no-delete-temp"],                                    "delete_temp_files",      False),
    ("refresh_cache",          ["--refresh-cache"],                                     "refresh_cache",          True),
    ("graph_title",            ["--graph-title", "Test Title"],                         "graph_title",            "Test Title"),
    ("x_axis_label",           ["--x-axis-label", "X Label"],                          "x_axis_label",           "X Label"),
    ("y_axis_label",           ["--y-axis-label", "Y Label"],                          "y_axis_label",           "Y Label"),
    ("gap_label",              ["--gap-label", "No Data"],                              "gap_label",              "No Data"),
    ("date_format",            ["--date-format", "%Y-%m"],                              "date_format",            "%Y-%m"),
    ("chart_type",             ["--chart-type", "bar"],                                 "chart_type",             "bar"),
    ("y_axis_percentile_cap",  ["--y-axis-percentile-cap", "95"],                       "y_axis_percentile_cap",  95),
    ("y_axis_max",             ["--y-axis-max", "500.0"],                               "y_axis_max",             500.0),
    ("legend_location",        ["--legend-location", "upper-left"],                    "legend_location",        "upper-left"),
    ("annual_avg_color",       ["--annual-avg-color", "red"],                           "annual_avg_color",       "red"),
    ("annual_avg_width",       ["--annual-avg-width", "3.0"],                           "annual_avg_width",       3.0),
    ("annual_avg_style",       ["--annual-avg-style", "dashed"],                        "annual_avg_style",       "dashed"),
    ("annual_avg_label",       ["--annual-avg-label", "Annual"],                        "annual_avg_label",       "Annual"),
    ("winter_avg_color",       ["--winter-avg-color", "blue"],                          "winter_avg_color",       "blue"),
    ("winter_avg_width",       ["--winter-avg-width", "2.0"],                           "winter_avg_width",       2.0),
    ("winter_avg_style",       ["--winter-avg-style", "dashed"],                        "winter_avg_style",       "dashed"),
    ("winter_avg_label",       ["--winter-avg-label", "Winter"],                        "winter_avg_label",       "Winter"),
    ("spring_avg_color",       ["--spring-avg-color", "green"],                         "spring_avg_color",       "green"),
    ("spring_avg_width",       ["--spring-avg-width", "2.0"],                           "spring_avg_width",       2.0),
    ("spring_avg_style",       ["--spring-avg-style", "dashed"],                        "spring_avg_style",       "dashed"),
    ("spring_avg_label",       ["--spring-avg-label", "Spring"],                        "spring_avg_label",       "Spring"),
    ("summer_avg_color",       ["--summer-avg-color", "orange"],                        "summer_avg_color",       "orange"),
    ("summer_avg_width",       ["--summer-avg-width", "2.0"],                           "summer_avg_width",       2.0),
    ("summer_avg_style",       ["--summer-avg-style", "dashed"],                        "summer_avg_style",       "dashed"),
    ("summer_avg_label",       ["--summer-avg-label", "Summer"],                        "summer_avg_label",       "Summer"),
    ("fall_avg_color",         ["--fall-avg-color", "purple"],                          "fall_avg_color",         "purple"),
    ("fall_avg_width",         ["--fall-avg-width", "2.0"],                             "fall_avg_width",         2.0),
    ("fall_avg_style",         ["--fall-avg-style", "dashed"],                          "fall_avg_style",         "dashed"),
    ("fall_avg_label",         ["--fall-avg-label", "Fall"],                            "fall_avg_label",         "Fall"),
    ("save_pdf",               ["--save-pdf"],                                          "save_pdf",               True),
    ("pdf_output_dir",         ["--pdf-output-dir", "/tmp/pdfs"],                       "pdf_output_dir",         "/tmp/pdfs"),
    ("pdf_filename_pattern",   ["--pdf-filename-pattern", "test-{start_date}.pdf"],     "pdf_filename_pattern",   "test-{start_date}.pdf"),
    ("pdf_path",               ["--pdf-path", "/tmp/out.pdf"],                          "pdf_path",               "/tmp/out.pdf"),
]


@pytest.mark.parametrize("yaml_key,extra_args,config_attr,expected", _OVERRIDE_CASES,
                         ids=[c[0] for c in _OVERRIDE_CASES])
def test_cli_flag_overrides_yaml_for_each_key(yaml_key, extra_args, config_attr, expected):
    """SC-002: every YAML key can be overridden via its CLI flag and flows into Config."""
    from home_water_usage.cli import build_parser, build_config

    parser = build_parser()
    args = parser.parse_args(_BASE_ARGS + extra_args)
    with open(YAML_PATH) as f:
        yaml_defaults = yaml.safe_load(f)
    config = build_config(args, yaml_defaults)
    assert getattr(config, config_attr) == expected
