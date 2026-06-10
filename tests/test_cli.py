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
