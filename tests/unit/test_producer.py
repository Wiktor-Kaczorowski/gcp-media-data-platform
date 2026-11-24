import pytest

from media_platform.events import validate_event
from media_platform.producer import build_messages


def test_streaming_message_count():
    messages = build_messages(
        count=20,
        run_id="stream-test",
    )

    assert len(messages) == 20


def test_streaming_message_schema():
    messages = build_messages(
        count=5,
        run_id="stream-test",
    )

    for message in messages:
        validate_event(message)

        assert message["source"] == "streaming"
        assert message["batch_id"] == "stream-test"
        assert "ingestion_timestamp" in message


def test_streaming_unique_events():
    messages = build_messages(
        count=20,
        run_id="stream-test",
    )

    assert len({message["event_id"] for message in messages}) == 20


@pytest.mark.parametrize("count", [0, 101])
def test_streaming_record_limit(count):
    with pytest.raises(ValueError):
        build_messages(count, "stream-test")
