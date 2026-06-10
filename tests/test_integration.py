"""Integration test: full pipeline with fixture JSONs and mocked Gmail API."""
import csv
import dataclasses
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


def _load_fixture(name):
    return json.loads((FIXTURES / name).read_text())


def _run_main(tmp_path, extra_args=None):
    """Invoke main() with default test argv. Returns after completion."""
    argv = [
        "home-water-usage",
        "--start-date", "2025-06-01",
        "--end-date", "2025-06-30",
        "--credentials-path", str(tmp_path / "credentials.json"),
        "--temp-dir", str(tmp_path),
    ]
    if extra_args:
        argv.extend(extra_args)

    detail_1 = _load_fixture("message_detail_1.json")   # June 15, 2025, 150 gal
    detail_2 = _load_fixture("message_detail_2.json")   # June 15, 2025, 175 gal (dup)

    mock_service = MagicMock()

    def _get(**kwargs):
        detail_map = {"msg001": detail_1, "msg002": detail_2}
        result = MagicMock()
        result.execute.return_value = detail_map.get(kwargs["id"], detail_1)
        return result

    mock_service.users.return_value.messages.return_value.list.return_value.execute.return_value = {
        "messages": [{"id": "msg001"}, {"id": "msg002"}],
        "resultSizeEstimate": 2,
    }
    mock_service.users.return_value.messages.return_value.get.side_effect = _get

    with patch("home_water_usage.auth.get_service", return_value=mock_service), \
         patch("matplotlib.pyplot.show"), \
         patch.object(sys, "argv", argv):
        from home_water_usage.cli import main
        main()


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

def test_full_pipeline_completes(tmp_path):
    """Full pipeline runs end-to-end without error."""
    _run_main(tmp_path)


def test_history_csv_written(tmp_path):
    """water-usage-history.csv written with parsed records."""
    _run_main(tmp_path)

    history_path = tmp_path / "water-usage-history.csv"
    assert history_path.exists()

    rows = list(csv.DictReader(history_path.open()))
    assert len(rows) == 1  # msg001 only (msg002 is a duplicate date)
    assert rows[0]["date"] == "2025-06-15"
    assert rows[0]["gallons"] == "150"


def test_run_csv_deleted_by_default(tmp_path):
    """Run CSV removed after graph display (delete_temp_files default=True)."""
    _run_main(tmp_path)

    run_csvs = list(tmp_path.glob("water-usage-run-*.csv"))
    assert len(run_csvs) == 0


def test_run_csv_preserved_with_no_delete_temp(tmp_path):
    """--no-delete-temp preserves run CSV."""
    _run_main(tmp_path, extra_args=["--no-delete-temp"])

    run_csvs = list(tmp_path.glob("water-usage-run-*.csv"))
    assert len(run_csvs) == 1


# ---------------------------------------------------------------------------
# Status call sequence
# ---------------------------------------------------------------------------

def test_status_progress_called_at_pipeline_stages(tmp_path):
    """status.progress called for auth, fetch, parse, storage, graph stages."""
    progress_messages = []

    def capture_progress(msg):
        progress_messages.append(msg)

    with patch("home_water_usage.status.progress", side_effect=capture_progress):
        _run_main(tmp_path)

    stages = ["auth", "fetch", "pars", "stor", "graph"]
    for stage in stages:
        assert any(stage.lower() in m.lower() for m in progress_messages), \
            f"No progress message for stage '{stage}'. Got: {progress_messages}"
