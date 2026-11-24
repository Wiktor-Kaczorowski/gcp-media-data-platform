import argparse
import json
from datetime import UTC, datetime

from google.cloud import pubsub_v1

from media_platform.events import generate_events, validate_event
from media_platform.settings import Settings


def build_messages(
    count: int,
    run_id: str,
    seed: int = 99,
) -> list[dict]:
    if not 1 <= count <= 100:
        raise ValueError("Streaming limit is 100 events")

    events = generate_events(
        count=count,
        seed=seed,
        run_id=run_id,
        include_anomalies=False,
    )

    messages = []

    for event in events:
        timestamp = datetime.now(UTC).isoformat()

        event["event_timestamp"] = timestamp

        validate_event(event)

        messages.append(
            {
                **event,
                "batch_id": run_id,
                "ingestion_timestamp": timestamp,
                "source": "streaming",
            }
        )

    return messages


def publish_events(
    count: int,
    run_id: str,
    include_invalid: bool = False,
) -> dict:
    settings = Settings.from_env()

    if settings.environment != "dev":
        raise ValueError("Only DEV publishing is allowed")

    messages = build_messages(count, run_id)

    publisher = pubsub_v1.PublisherClient()

    topic = publisher.topic_path(
        settings.project_id,
        f"media-{settings.environment}-events",
    )

    published = []

    try:
        for message in messages:
            payload = json.dumps(
                message,
                allow_nan=False,
            ).encode("utf-8")

            future = publisher.publish(
                topic,
                payload,
                schema_version="1",
                source="media-producer",
                run_id=run_id,
            )

            published.append(future.result(timeout=30))

        if include_invalid:
            future = publisher.publish(
                topic,
                b"invalid-json-test-message",
                schema_version="1",
                source="quality-test",
                run_id=run_id,
            )

            published.append(future.result(timeout=30))

    finally:
        publisher.stop()

    return {
        "status": "success",
        "topic": topic,
        "run_id": run_id,
        "valid_messages": len(messages),
        "invalid_messages": int(include_invalid),
        "published_messages": len(published),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Publish media events to Cloud Pub/Sub"
    )

    parser.add_argument("--count", type=int, default=20)
    parser.add_argument("--run-id", required=True)

    parser.add_argument(
        "--include-invalid",
        action="store_true",
    )

    args = parser.parse_args()

    result = publish_events(
        count=args.count,
        run_id=args.run_id,
        include_invalid=args.include_invalid,
    )

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
