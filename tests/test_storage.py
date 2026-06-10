"""Tests for storage.py: run CSV, HistoryCache read/write/merge/delete."""
import csv
import dataclasses
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

from home_water_usage.models import UsageRecord


def _make_records(*date_gallons):
    return [UsageRecord(date=date(*d), gallons=g) for d, g in date_gallons]


# ---------------------------------------------------------------------------
# Run CSV write
# ---------------------------------------------------------------------------

def test_write_run_csv_filename_pattern(base_config, sample_records):
    from home_water_usage.storage import write_run_csv, run_csv_path

    path = write_run_csv(sample_records, base_config)
    expected = run_csv_path(base_config)
    assert path == expected
    assert path.name == f"water-usage-run-{base_config.start_date}-{base_config.end_date}.csv"


def test_write_run_csv_content(base_config, sample_records):
    from home_water_usage.storage import write_run_csv

    path = write_run_csv(sample_records, base_config)
    rows = list(csv.DictReader(path.open()))
    assert len(rows) == len(sample_records)
    assert rows[0]["date"] == str(sample_records[0].date)
    assert int(rows[0]["gallons"]) == sample_records[0].gallons


# ---------------------------------------------------------------------------
# HistoryCache read
# ---------------------------------------------------------------------------

def test_read_history_cache_empty_when_file_missing(base_config):
    from home_water_usage.storage import read_history_cache

    assert read_history_cache(base_config) == []


def test_read_history_cache_returns_sorted_records(base_config, tmp_path):
    from home_water_usage.storage import history_csv_path, read_history_cache, write_run_csv

    records = _make_records(
        ((2025, 6, 20), 200),
        ((2025, 6, 10), 100),  # out of order
    )
    # Write directly via storage
    from home_water_usage.storage import update_history_cache
    update_history_cache(records, base_config)

    result = read_history_cache(base_config)
    assert result[0].date < result[1].date


# ---------------------------------------------------------------------------
# HistoryCache append-only merge
# ---------------------------------------------------------------------------

def test_history_cache_new_dates_appended(base_config):
    from home_water_usage.storage import update_history_cache, read_history_cache

    records1 = _make_records(((2025, 6, 10), 100))
    update_history_cache(records1, base_config)

    records2 = _make_records(((2025, 6, 11), 110))
    update_history_cache(records2, base_config)

    all_records = read_history_cache(base_config)
    assert len(all_records) == 2


def test_history_cache_existing_dates_not_overwritten(base_config):
    from home_water_usage.storage import update_history_cache, read_history_cache

    original = _make_records(((2025, 6, 10), 100))
    update_history_cache(original, base_config)

    overwrite_attempt = _make_records(((2025, 6, 10), 999))
    update_history_cache(overwrite_attempt, base_config)

    result = read_history_cache(base_config)
    assert len(result) == 1
    assert result[0].gallons == 100  # original preserved


def test_partial_overlap_only_new_dates_added(base_config):
    from home_water_usage.storage import update_history_cache, read_history_cache

    first_batch = _make_records(((2025, 6, 10), 100), ((2025, 6, 11), 110))
    update_history_cache(first_batch, base_config)

    # overlap on June 11, new record June 12
    second_batch = _make_records(((2025, 6, 11), 999), ((2025, 6, 12), 120))
    update_history_cache(second_batch, base_config)

    result = read_history_cache(base_config)
    assert len(result) == 3
    june_11 = next(r for r in result if r.date == date(2025, 6, 11))
    assert june_11.gallons == 110  # original, not overwritten


# ---------------------------------------------------------------------------
# Corrupt cache recovery
# ---------------------------------------------------------------------------

def test_corrupt_cache_returns_empty_with_warning(base_config, tmp_path):
    from home_water_usage.storage import history_csv_path, read_history_cache

    path = history_csv_path(base_config)
    path.write_text("not,valid\ncsv,garbage,extra,cols\n")

    with patch("home_water_usage.storage.status") as mock_status:
        result = read_history_cache(base_config)

    assert result == []
    mock_status.warning.assert_called_once()
    # Corrupt file should be deleted to allow rebuild
    assert not path.exists()


# ---------------------------------------------------------------------------
# Run CSV deletion
# ---------------------------------------------------------------------------

def test_default_delete_removes_run_csv(base_config, sample_records):
    from home_water_usage.storage import delete_run_csv, write_run_csv

    path = write_run_csv(sample_records, base_config)
    assert path.exists()
    delete_run_csv(path, base_config)
    assert not path.exists()


def test_no_delete_temp_preserves_run_csv(base_config, sample_records):
    from home_water_usage.storage import delete_run_csv, write_run_csv

    config = dataclasses.replace(base_config, delete_temp_files=False)
    path = write_run_csv(sample_records, config)
    delete_run_csv(path, config)
    assert path.exists()


# ---------------------------------------------------------------------------
# Cleanup isolation (T028)
# ---------------------------------------------------------------------------

def test_history_cache_not_deleted_by_delete_run_csv(base_config, sample_records):
    """delete_run_csv never touches water-usage-history.csv."""
    from home_water_usage.storage import (
        delete_run_csv, history_csv_path, update_history_cache, write_run_csv,
    )

    update_history_cache(sample_records, base_config)
    history_path = history_csv_path(base_config)
    assert history_path.exists()

    run_path = write_run_csv(sample_records, base_config)
    delete_run_csv(run_path, base_config)

    assert history_path.exists()


def test_write_run_csv_unwritable_dir_exits(base_config, sample_records, tmp_path):
    """write_run_csv exits [✗] with temp_dir message + likely cause + remediation."""
    import os
    from unittest.mock import patch
    from home_water_usage.storage import write_run_csv
    import home_water_usage.storage as storage_module

    ro_dir = tmp_path / "readonly"
    ro_dir.mkdir()
    os.chmod(str(ro_dir), 0o555)

    config = dataclasses.replace(base_config, temp_dir=str(ro_dir))
    try:
        with patch.object(storage_module, "status") as mock_status:
            mock_status.error.side_effect = SystemExit(1)
            with pytest.raises(SystemExit) as exc:
                write_run_csv(sample_records, config)

        assert exc.value.code == 1
        call_kwargs = mock_status.error.call_args
        msg = call_kwargs[0][0]
        likely_cause = call_kwargs[1].get("likely_cause", "")
        remediation = call_kwargs[1].get("remediation", "")
        assert str(ro_dir) in msg
        assert likely_cause
        assert remediation
    finally:
        os.chmod(str(ro_dir), 0o755)


def test_no_delete_temp_and_refresh_cache_are_independent(base_config, sample_records):
    """--no-delete-temp and --refresh-cache affect separate targets."""
    from home_water_usage.storage import (
        delete_run_csv, history_csv_path, update_history_cache, write_run_csv,
    )

    config = dataclasses.replace(base_config, delete_temp_files=False, refresh_cache=True)

    update_history_cache(sample_records, config)
    run_path = write_run_csv(sample_records, config)

    delete_run_csv(run_path, config)
    assert run_path.exists()           # preserved by delete_temp_files=False
    assert history_csv_path(config).exists()  # history untouched


# ---------------------------------------------------------------------------
# refresh_cache: no new emails
# ---------------------------------------------------------------------------

def test_refresh_cache_no_new_emails_emits_success(base_config):
    from home_water_usage.storage import update_history_cache, read_history_cache

    existing = _make_records(((2025, 6, 10), 100))
    update_history_cache(existing, base_config)

    with patch("home_water_usage.storage.status") as mock_status:
        # Update with same records → no new dates
        update_history_cache(existing, base_config)

    mock_status.success.assert_called_once()
    call_msg = mock_status.success.call_args[0][0]
    assert "up to date" in call_msg.lower()
