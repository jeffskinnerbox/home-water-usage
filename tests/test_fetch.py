"""Tests for fetch.py: Gmail query, pagination, classification, retries."""
import dataclasses
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest
from googleapiclient.errors import HttpError


FIXTURES = Path(__file__).parent / "fixtures"


def _load_fixture(name):
    return json.loads((FIXTURES / name).read_text())


def _date_to_internal_ms(d: date) -> str:
    ts = datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp()
    return str(int(ts * 1000))


def _make_message(msg_id: str, received_date: date) -> dict:
    return {
        "id": msg_id,
        "threadId": f"thread-{msg_id}",
        "internalDate": _date_to_internal_ms(received_date),
        "payload": {
            "mimeType": "text/plain",
            "body": {"data": "dGVzdA=="},  # "test"
        },
    }


def _make_http_error(status_code: int) -> HttpError:
    resp = MagicMock()
    resp.status = status_code
    return HttpError(resp=resp, content=b"error")


def _make_service(list_responses, detail_map=None):
    """Build a mock Gmail service. list_responses is a list of execute() return values."""
    mock_service = MagicMock()
    mock_msgs = mock_service.users.return_value.messages.return_value

    list_execute = MagicMock()
    list_execute.side_effect = list_responses
    mock_msgs.list.return_value.execute = list_execute

    if detail_map:
        def _get(**kwargs):
            result = MagicMock()
            result.execute.return_value = detail_map[kwargs["id"]]
            return result
        mock_msgs.get.side_effect = _get

    return mock_service


# ---------------------------------------------------------------------------
# Query format
# ---------------------------------------------------------------------------

def test_query_includes_filter_and_date_window(base_config):
    from home_water_usage.fetch import fetch_messages

    service = _make_service(
        [{"messages": [], "resultSizeEstimate": 0}],
    )
    with pytest.raises(SystemExit):
        fetch_messages(service, base_config)

    call_kwargs = service.users.return_value.messages.return_value.list.call_args[1]
    query = call_kwargs["q"]
    assert "from:no-reply@leesburgva.gov" in query

    widen_start = base_config.start_date - timedelta(days=base_config.buffer_email_count)
    assert widen_start.strftime("%Y/%m/%d") in query
    end_str = (base_config.end_date + timedelta(days=1)).strftime("%Y/%m/%d")
    assert end_str in query


# ---------------------------------------------------------------------------
# Buffer classification
# ---------------------------------------------------------------------------

def test_in_range_classification(base_config):
    from home_water_usage.fetch import classify_messages

    msg = _make_message("m1", date(2025, 6, 15))  # within June 1–30
    in_range, buffer = classify_messages([msg], base_config)

    assert len(in_range) == 1
    assert len(buffer) == 0


def test_buffer_classification(base_config):
    from home_water_usage.fetch import classify_messages

    # May 30 = 2 days before June 1 (within buffer of 3)
    msg = _make_message("m1", date(2025, 5, 30))
    in_range, buf = classify_messages([msg], base_config)

    assert len(in_range) == 0
    assert len(buf) == 1


def test_discard_classification(base_config):
    from home_water_usage.fetch import classify_messages

    # May 27 = 5 days before June 1 (beyond buffer of 3)
    msg = _make_message("m1", date(2025, 5, 27))
    in_range, buf = classify_messages([msg], base_config)

    assert len(in_range) == 0
    assert len(buf) == 0


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------

def test_pagination_follows_next_page_token(base_config):
    from home_water_usage.fetch import fetch_messages

    msg1 = _make_message("m1", date(2025, 6, 10))
    msg2 = _make_message("m2", date(2025, 6, 11))

    list_responses = [
        {"messages": [{"id": "m1"}], "nextPageToken": "page2"},
        {"messages": [{"id": "m2"}]},
    ]
    detail_map = {"m1": msg1, "m2": msg2}
    service = _make_service(list_responses, detail_map)

    messages = fetch_messages(service, base_config)
    assert len(messages) == 2

    list_calls = service.users.return_value.messages.return_value.list.call_args_list
    assert len(list_calls) == 2
    assert list_calls[1][1].get("pageToken") == "page2"


# ---------------------------------------------------------------------------
# Empty result → exit
# ---------------------------------------------------------------------------

def test_empty_result_exits(base_config):
    from home_water_usage.fetch import fetch_messages

    service = _make_service([{"messages": [], "resultSizeEstimate": 0}])
    with pytest.raises(SystemExit) as exc:
        fetch_messages(service, base_config)
    assert exc.value.code == 1


# ---------------------------------------------------------------------------
# Retry on 429 / 503
# ---------------------------------------------------------------------------

@patch("home_water_usage.fetch.time.sleep")
def test_retry_on_429(mock_sleep, base_config):
    from home_water_usage.fetch import fetch_messages

    msg = _make_message("m1", date(2025, 6, 15))
    list_responses = [
        _make_http_error(429),
        {"messages": [{"id": "m1"}]},
    ]
    service = _make_service(list_responses, {"m1": msg})

    messages = fetch_messages(service, base_config)

    assert len(messages) == 1
    mock_sleep.assert_called_once_with(1)  # 2^0 = 1


@patch("home_water_usage.fetch.time.sleep")
def test_retry_on_503(mock_sleep, base_config):
    from home_water_usage.fetch import fetch_messages

    msg = _make_message("m1", date(2025, 6, 15))
    list_responses = [
        _make_http_error(503),
        {"messages": [{"id": "m1"}]},
    ]
    service = _make_service(list_responses, {"m1": msg})

    messages = fetch_messages(service, base_config)
    assert len(messages) == 1
    mock_sleep.assert_called_once()


# ---------------------------------------------------------------------------
# Retries exhausted → exit
# ---------------------------------------------------------------------------

@patch("home_water_usage.fetch.time.sleep")
def test_retries_exhausted_exits(mock_sleep, base_config):
    from home_water_usage.fetch import fetch_messages

    # max_retries=2 in base_config → 3 total attempts
    list_responses = [
        _make_http_error(429),
        _make_http_error(429),
        _make_http_error(429),
    ]
    service = _make_service(list_responses)

    with pytest.raises(SystemExit) as exc:
        fetch_messages(service, base_config)
    assert exc.value.code == 1


# ---------------------------------------------------------------------------
# Non-retryable error → immediate abort
# ---------------------------------------------------------------------------

@patch("home_water_usage.fetch.time.sleep")
def test_non_retryable_aborts_immediately(mock_sleep, base_config):
    from home_water_usage.fetch import fetch_messages

    service = _make_service([_make_http_error(404)])

    with pytest.raises(SystemExit) as exc:
        fetch_messages(service, base_config)
    assert exc.value.code == 1
    mock_sleep.assert_not_called()


# ---------------------------------------------------------------------------
# get_message_body
# ---------------------------------------------------------------------------

def test_get_message_body_decodes_base64():
    from home_water_usage.fetch import get_message_body

    msg = _load_fixture("message_detail_1.json")
    body = get_message_body(msg)
    assert "150" in body
    assert "June 15, 2025" in body
