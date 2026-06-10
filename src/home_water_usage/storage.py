"""CSV storage: run-temp CSV and persistent HistoryCache."""
from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

from home_water_usage import status
from home_water_usage.models import UsageRecord

_HISTORY_CSV = "water-usage-history.csv"
_RUN_CSV_PATTERN = "water-usage-run-{start}-{end}.csv"


def run_csv_path(config) -> Path:
    return Path(config.temp_dir) / _RUN_CSV_PATTERN.format(
        start=config.start_date, end=config.end_date
    )


def history_csv_path(config) -> Path:
    return Path(config.temp_dir) / _HISTORY_CSV


def write_run_csv(records: list[UsageRecord], config) -> Path:
    """Write records to the run-specific temp CSV. Returns the path."""
    path = run_csv_path(config)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["date", "gallons"])
            writer.writeheader()
            for r in records:
                writer.writerow({"date": str(r.date), "gallons": r.gallons})
    except PermissionError:
        status.error(
            f"temp_dir '{config.temp_dir}' is not writable.",
            likely_cause="Directory does not exist or insufficient permissions.",
            remediation=(
                "Create the directory or set a writable path via "
                "--temp-dir or temp_dir in parameter_values.yaml."
            ),
        )
    return path


def read_history_cache(config) -> list[UsageRecord]:
    """Read HistoryCache CSV. Returns sorted records; empty list if missing or corrupt."""
    path = history_csv_path(config)
    if not path.exists():
        return []

    try:
        records = []
        with open(path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(
                    UsageRecord(
                        date=date.fromisoformat(row["date"]),
                        gallons=int(row["gallons"]),
                    )
                )
        return sorted(records, key=lambda r: r.date)
    except Exception as exc:
        status.warning(f"Corrupt HistoryCache at {path} ({exc}) — will rebuild from Gmail.")
        path.unlink(missing_ok=True)
        return []


def update_history_cache(records: list[UsageRecord], config) -> None:
    """Append-only merge of records into HistoryCache. Existing dates are never overwritten."""
    existing = read_history_cache(config)
    existing_dates = {r.date for r in existing}

    new_records = [r for r in records if r.date not in existing_dates]
    if not new_records:
        status.success("Cache already up to date.")
        return

    all_records = sorted(existing + new_records, key=lambda r: r.date)
    path = history_csv_path(config)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "gallons"])
        writer.writeheader()
        for r in all_records:
            writer.writerow({"date": str(r.date), "gallons": r.gallons})


def delete_run_csv(path: Path, config) -> None:
    """Delete the run CSV if config.delete_temp_files is True."""
    if config.delete_temp_files and path.exists():
        path.unlink()
