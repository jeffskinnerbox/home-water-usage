"""Gmail fetch: query construction, pagination, message decode, classification, retries."""
from __future__ import annotations

import base64
import time
from datetime import datetime, timedelta, timezone

from googleapiclient.errors import HttpError

from home_water_usage import status

_RETRYABLE_STATUSES = {429, 500, 503}


def _ms_to_date(internal_date_ms: str):
    ts = int(internal_date_ms) / 1000
    return datetime.fromtimestamp(ts, tz=timezone.utc).date()


def get_message_body(message: dict) -> str:
    """Extract and base64url-decode the plain-text body from a Gmail message dict."""
    payload = message.get("payload", {})
    data = payload.get("body", {}).get("data", "")
    if data:
        padding = (4 - len(data) % 4) % 4
        return base64.urlsafe_b64decode(data + "=" * padding).decode("utf-8")
    # Multipart: look in parts
    for part in payload.get("parts", []):
        if part.get("mimeType") == "text/plain":
            data = part.get("body", {}).get("data", "")
            if data:
                padding = (4 - len(data) % 4) % 4
                return base64.urlsafe_b64decode(data + "=" * padding).decode("utf-8")
    return ""


def _list_with_retry(service, query: str, page_token: str | None, config) -> dict:
    """Call messages.list with exponential-backoff retry on transient errors."""
    kwargs = {"userId": "me", "q": query}
    if page_token:
        kwargs["pageToken"] = page_token

    for attempt in range(config.max_retries + 1):
        try:
            return service.users().messages().list(**kwargs).execute()
        except HttpError as exc:
            code = exc.resp.status
            if code in _RETRYABLE_STATUSES and attempt < config.max_retries:
                time.sleep(2 ** attempt)
            elif code in _RETRYABLE_STATUSES:
                status.error(
                    f"Gmail API unavailable after {config.max_retries} retries (HTTP {code}).",
                    likely_cause="Transient Gmail API error (rate limit or server error).",
                    remediation="Wait a few minutes and retry.",
                )
            else:
                status.error(
                    f"Gmail API returned HTTP {code}.",
                    likely_cause=f"Non-retryable API error: {exc}",
                    remediation="Check your Gmail API credentials and OAuth scopes, then retry.",
                )


def fetch_messages(service, config) -> list[dict]:
    """Fetch all Gmail messages matching the widened date-window query.

    Returns a list of full message detail dicts (payload included).
    Exits 1 on empty result or unrecoverable API error.
    """
    widen_start = config.start_date - timedelta(days=config.buffer_email_count)
    after = widen_start.strftime("%Y/%m/%d")
    before = (config.end_date + timedelta(days=1)).strftime("%Y/%m/%d")
    query = f"{config.gmail_query_filter} after:{after} before:{before}"

    message_ids: list[str] = []
    page_token = None

    while True:
        result = _list_with_retry(service, query, page_token, config)
        ids = [m["id"] for m in result.get("messages", [])]
        message_ids.extend(ids)
        page_token = result.get("nextPageToken")
        if not page_token:
            break

    if not message_ids:
        status.error(
            "No emails found in the specified date range.",
            likely_cause="No water-usage alert emails from the utility in this period.",
            remediation="Widen the date range or check the Gmail query filter.",
        )

    details = []
    for msg_id in message_ids:
        detail = service.users().messages().get(userId="me", id=msg_id, format="full").execute()
        details.append(detail)

    return details


def classify_messages(messages: list[dict], config) -> tuple[list[dict], list[dict]]:
    """Split messages into (in_range, buffer). Discards out-of-window messages.

    Classification is by internalDate (received timestamp).
    - in_range: [start_date, end_date]
    - buffer:   [start_date - buffer_email_count, start_date)
    """
    buffer_start = config.start_date - timedelta(days=config.buffer_email_count)
    in_range: list[dict] = []
    buffer: list[dict] = []

    for msg in messages:
        msg_date = _ms_to_date(msg["internalDate"])
        if config.start_date <= msg_date <= config.end_date:
            in_range.append(msg)
        elif buffer_start <= msg_date < config.start_date:
            buffer.append(msg)
        # else: discard

    return in_range, buffer
