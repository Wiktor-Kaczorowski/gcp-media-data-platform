import json

from apache_beam.pvalue import TaggedOutput

from media_platform.batch import ParseAndValidate
from media_platform.events import generate_events


def make_transform():
    return ParseAndValidate(
        batch_id="test-batch",
        ingestion_timestamp="2026-11-24T12:00:00Z",
    )


def test_valid_record():
    event = generate_events(count=1)[0]

    result = list(make_transform().process(json.dumps(event)))

    assert len(result) == 1
    assert result[0]["event_id"] == event["event_id"]
    assert result[0]["batch_id"] == "test-batch"
    assert result[0]["source"] == "batch"


def test_invalid_record():
    event = generate_events(count=1)[-1]

    result = list(make_transform().process(json.dumps(event)))

    assert len(result) == 1
    assert isinstance(result[0], TaggedOutput)
    assert result[0].tag == "invalid"
    assert "spend" in result[0].value["error_reason"]


def test_malformed_json():
    result = list(make_transform().process("invalid-json"))

    assert len(result) == 1
    assert result[0].tag == "invalid"


def test_duplicate_is_preserved():
    events = generate_events(count=1)

    transform = make_transform()

    first = list(transform.process(json.dumps(events[0])))
    duplicate = list(transform.process(json.dumps(events[1])))

    assert first == duplicate
