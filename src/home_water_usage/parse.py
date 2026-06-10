"""Email body → UsageRecord list: regex parse, validation, dedup, skip logic."""
from __future__ import annotations

import re
from datetime import datetime

from home_water_usage import status
from home_water_usage.models import UsageRecord

_REQUIRED_GROUPS = {"month", "day", "year", "gallons"}


def parse_messages(bodies: list[str], config) -> list[UsageRecord]:
    """Parse email body strings → UsageRecord list.

    Skips non-matches, invalid dates, duplicate dates, and account mismatches.
    """
    pattern = re.compile(config.email_body_pattern)

    missing = _REQUIRED_GROUPS - set(pattern.groupindex.keys())
    if missing:
        status.error(
            f"email_body_pattern is missing required named groups: {sorted(missing)}",
            likely_cause="The regex in parameter_values.yaml or --email-body-pattern lacks required capture groups.",
            remediation="Ensure the pattern includes (?P<month>), (?P<day>), (?P<year>), and (?P<gallons>).",
        )

    seen_dates: dict = {}
    records: list[UsageRecord] = []

    for body in bodies:
        m = pattern.search(body)
        if not m:
            status.warning("Body did not match pattern — skipping.")
            continue

        gd = m.groupdict()

        # Account validation
        if "account" in gd and gd["account"] != config.account_number:
            status.warning(
                f"Account mismatch: got {gd['account']!r}, expected {config.account_number!r} — skipping."
            )
            continue

        # Parse date
        try:
            month_num = datetime.strptime(gd["month"], "%B").month
            record_date = datetime(int(gd["year"]), month_num, int(gd["day"])).date()
        except ValueError as exc:
            status.warning(f"[!] Invalid date in body ({exc}) — skipping.")
            continue

        # Dedup by body date
        if record_date in seen_dates:
            status.warning(
                f"Duplicate date {record_date} — keeping first occurrence, skipping this one."
            )
            continue

        seen_dates[record_date] = True
        records.append(UsageRecord(date=record_date, gallons=int(gd["gallons"])))

    return records
