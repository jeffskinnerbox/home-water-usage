"""Tests for parse.py: body parsing, validation, dedup, skips."""
import dataclasses
from datetime import date
from unittest.mock import patch

import pytest

from home_water_usage.models import UsageRecord


VALID_BODY = (
    "On June 15, 2025, your water usage of 150 exceeded your threshold of 100 "
    "for account 40002423000."
)
WRONG_ACCOUNT_BODY = (
    "On June 16, 2025, your water usage of 200 exceeded your threshold of 100 "
    "for account 99999999999."
)
NO_MATCH_BODY = "Hello, this is a regular email that does not match the pattern."


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

def test_valid_body_returns_usage_record(base_config):
    from home_water_usage.parse import parse_messages
    records = parse_messages([VALID_BODY], base_config)
    assert records == [UsageRecord(date=date(2025, 6, 15), gallons=150)]


def test_multiple_valid_bodies(base_config):
    from home_water_usage.parse import parse_messages
    body2 = (
        "On June 20, 2025, your water usage of 200 exceeded your threshold of 100 "
        "for account 40002423000."
    )
    records = parse_messages([VALID_BODY, body2], base_config)
    assert len(records) == 2
    assert records[0].date == date(2025, 6, 15)
    assert records[1].date == date(2025, 6, 20)


# ---------------------------------------------------------------------------
# Required-group validation
# ---------------------------------------------------------------------------

def test_missing_required_group_aborts(base_config):
    """Regex missing required named groups → [✗] + sys.exit(1)."""
    import dataclasses
    bad_pattern = r"On (?P<month>\w+) (?P<day>\d+), (?P<year>\d{4})"  # missing gallons
    config = dataclasses.replace(base_config, email_body_pattern=bad_pattern)

    from home_water_usage.parse import parse_messages
    with pytest.raises(SystemExit) as exc:
        parse_messages([VALID_BODY], config)
    assert exc.value.code == 1


# ---------------------------------------------------------------------------
# Invalid date → skip + [!]
# ---------------------------------------------------------------------------

def test_invalid_date_skipped_with_warning(base_config):
    """Invalid day value → skip + [!] warning emitted."""
    bad_body = (
        "On June 32, 2025, your water usage of 150 exceeded your threshold of 100 "
        "for account 40002423000."
    )
    from home_water_usage.parse import parse_messages
    with patch("home_water_usage.parse.status") as mock_status:
        records = parse_messages([bad_body], base_config)

    assert records == []
    mock_status.warning.assert_called_once()


# ---------------------------------------------------------------------------
# Duplicate date → keep first + [!]
# ---------------------------------------------------------------------------

def test_duplicate_date_keeps_first(base_config):
    """Two messages with same body date → first kept, second skipped with [!]."""
    dup_body = (
        "On June 15, 2025, your water usage of 999 exceeded your threshold of 100 "
        "for account 40002423000."
    )
    from home_water_usage.parse import parse_messages
    with patch("home_water_usage.parse.status") as mock_status:
        records = parse_messages([VALID_BODY, dup_body], base_config)

    assert len(records) == 1
    assert records[0].gallons == 150  # first wins
    mock_status.warning.assert_called_once()


# ---------------------------------------------------------------------------
# Account mismatch → skip + [!]
# ---------------------------------------------------------------------------

def test_account_mismatch_skipped(base_config):
    """Account in body doesn't match config.account_number → skip + [!]."""
    from home_water_usage.parse import parse_messages
    with patch("home_water_usage.parse.status") as mock_status:
        records = parse_messages([WRONG_ACCOUNT_BODY], base_config)

    assert records == []
    mock_status.warning.assert_called_once()


# ---------------------------------------------------------------------------
# Non-matching body → skip + [!]
# ---------------------------------------------------------------------------

def test_non_matching_body_skipped(base_config):
    """Body doesn't match regex → skip + [!]."""
    from home_water_usage.parse import parse_messages
    with patch("home_water_usage.parse.status") as mock_status:
        records = parse_messages([NO_MATCH_BODY], base_config)

    assert records == []
    mock_status.warning.assert_called_once()


def test_empty_list_returns_empty(base_config):
    from home_water_usage.parse import parse_messages
    assert parse_messages([], base_config) == []
