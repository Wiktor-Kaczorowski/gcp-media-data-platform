import json
from datetime import date

import pytest

from media_platform.events import (
    generate_events,
    validate_event,
)
from media_platform.ingestion import to_jsonl


def test_generate_expected_record_count():
    events = generate_events(count=100)

    assert len(events) == 102


def test_reproducible_generation():
    options = {
        "count": 10,
        "seed": 42,
        "run_id": "test-run",
        "event_date": date(2026, 11, 24),
    }

    assert generate_events(**options) == generate_events(**options)


def test_valid_events():
    events = generate_events(
        count=100,
        include_anomalies=False,
    )

    for event in events:
        validate_event(event)


def test_duplicate_event():
    events = generate_events(count=10)

    assert events[0] == events[-2]


def test_invalid_negative_spend():
    events = generate_events(count=10)

    with pytest.raises(ValueError, match="spend"):
        validate_event(events[-1])


def test_missing_required_field():
    event = generate_events(count=1)[0]
    del event["campaign_id"]

    with pytest.raises(ValueError, match="Missing fields"):
        validate_event(event)


@pytest.mark.parametrize("count", [0, -1, 1001])
def test_record_limit(count):
    with pytest.raises(ValueError):
        generate_events(count=count)


def test_jsonl_serialization():
    events = generate_events(count=5)

    payload = to_jsonl(events)

    decoded = [json.loads(line) for line in payload.splitlines()]

    assert decoded == events
