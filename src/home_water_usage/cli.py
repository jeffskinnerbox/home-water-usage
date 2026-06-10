"""CLI entry point: load YAML defaults, parse flags, merge into Config, run pipeline."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

from home_water_usage import auth, fetch, graph, parse, status, storage
from home_water_usage.config import Config

_YAML_PATH = Path(__file__).parent.parent.parent / "parameter_values.yaml"


def build_parser() -> argparse.ArgumentParser:
    """Return the fully-configured ArgumentParser (exported for tests)."""
    p = argparse.ArgumentParser(
        prog="home-water-usage",
        description="Pull Gmail water-usage alert emails and render an interactive usage graph.",
    )

    # Required positional-style date args
    p.add_argument("--start-date", required=True, metavar="YYYY-MM-DD",
                   help="Start of the plotted date range (inclusive)")
    p.add_argument("--end-date", required=True, metavar="YYYY-MM-DD",
                   help="End of the plotted date range (inclusive)")

    # Gmail
    p.add_argument("--gmail-query-filter", default=None, metavar="FILTER")
    p.add_argument("--buffer-email-count", default=None, type=int, metavar="N")
    p.add_argument("--max-retries", default=None, type=int, metavar="N")
    p.add_argument("--account-number", default=None, metavar="ACCT")
    p.add_argument("--email-body-pattern", default=None, metavar="REGEX")

    # Credentials
    p.add_argument("--credentials-path", default=None, metavar="PATH")
    p.add_argument("--token-path", default=None, metavar="PATH")

    # Storage
    p.add_argument("--temp-dir", default=None, metavar="PATH")
    p.add_argument("--no-delete-temp", action="store_true", default=None,
                   help="Keep the run-specific CSV after graph display")
    p.add_argument("--refresh-cache", action="store_true", default=None,
                   help="Force full HistoryCache rebuild from Gmail")

    # Graph display
    p.add_argument("--graph-title", default=None, metavar="TITLE")
    p.add_argument("--x-axis-label", default=None, metavar="LABEL")
    p.add_argument("--y-axis-label", default=None, metavar="LABEL")
    p.add_argument("--gap-label", default=None, metavar="LABEL")
    p.add_argument("--date-format", default=None, metavar="FMT")
    p.add_argument("--chart-type", default=None, metavar="TYPE")
    p.add_argument("--y-axis-percentile-cap", default=None, type=int, metavar="PCT")
    p.add_argument("--y-axis-max", default=None, type=float, metavar="MAX")
    p.add_argument("--legend-location", default=None, metavar="LOC")

    # Seasonal average lines
    for season in ("annual", "winter", "spring", "summer", "fall"):
        p.add_argument(f"--{season}-avg-color", default=None, metavar="COLOR")
        p.add_argument(f"--{season}-avg-width", default=None, type=float, metavar="W")
        p.add_argument(f"--{season}-avg-style", default=None, metavar="STYLE")
        p.add_argument(f"--{season}-avg-label", default=None, metavar="LABEL")

    # PDF export
    p.add_argument("--save-pdf", action="store_true", default=None,
                   help="Save graph as PDF before opening interactive window")
    p.add_argument("--pdf-output-dir", default=None, metavar="PATH")
    p.add_argument("--pdf-filename-pattern", default=None, metavar="PATTERN")
    p.add_argument("--pdf-path", default=None, metavar="PATH",
                   help="Full output path for PDF (overrides --pdf-output-dir and --pdf-filename-pattern)")

    return p


def build_config(args: argparse.Namespace, yaml_defaults: dict) -> Config:
    """Merge parsed CLI args over YAML defaults and return a Config.

    CLI values (non-None / explicitly set booleans) take precedence.
    """
    merged = dict(yaml_defaults)
    args_dict = vars(args)

    for dest, value in args_dict.items():
        if dest == "no_delete_temp":
            continue
        if value is not None:
            merged[dest] = value

    if args_dict.get("no_delete_temp"):
        merged["delete_temp_files"] = False

    merged["start_date"] = args_dict["start_date"]
    merged["end_date"] = args_dict["end_date"]

    return Config.from_dict(merged)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    with open(_YAML_PATH) as f:
        yaml_defaults = yaml.safe_load(f)

    config = build_config(args, yaml_defaults)

    if config.start_date > config.end_date:
        status.error(
            f"Invalid date range: --start-date {config.start_date} is after --end-date {config.end_date}",
            likely_cause="start-date must be less than or equal to end-date.",
            remediation="Re-run with a start date that precedes the end date.",
        )

    # Auth
    status.progress("Authenticating with Gmail...")
    service = auth.get_service(config)
    status.success("Authenticated.")

    # Fetch
    status.progress("Fetching emails from Gmail...")
    raw_messages = fetch.fetch_messages(service, config)
    in_range_msgs, buffer_msgs = fetch.classify_messages(raw_messages, config)
    status.success(
        f"Fetched {len(in_range_msgs)} in-range + {len(buffer_msgs)} buffer emails."
    )

    # Parse
    status.progress("Parsing email bodies...")
    in_range_bodies = [fetch.get_message_body(m) for m in in_range_msgs]
    buffer_bodies = [fetch.get_message_body(m) for m in buffer_msgs]
    records = parse.parse_messages(in_range_bodies, config)
    buffer_records = parse.parse_messages(buffer_bodies, config)
    all_records = records + buffer_records

    if not records:
        status.warning("No exceedance emails in date range — graph shows seasonal averages only.")

    status.success(f"Parsed {len(records)} in-range usage records.")

    # Storage: write run CSV
    status.progress("Writing run CSV...")
    run_path = storage.write_run_csv(records, config)
    status.success(f"Run CSV written to {run_path}.")

    # Storage: update HistoryCache
    status.progress("Updating history cache...")
    storage.update_history_cache(all_records, config)
    status.success("History cache updated.")

    # Graph
    status.progress("Computing seasonal averages...")
    history = storage.read_history_cache(config)
    averages = graph.compute_seasonal_averages(history, config)
    status.success(f"Computed {len(averages)} seasonal average line(s).")

    status.progress("Rendering graph...")
    graph.dispatch_render(records, averages, config)
    status.success("Graph rendered.")

    # Cleanup
    storage.delete_run_csv(run_path, config)
