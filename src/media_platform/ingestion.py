import argparse
import json
import logging
import re
from datetime import UTC, date, datetime
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

from google.cloud import storage

from media_platform.settings import Settings

LOGGER = logging.getLogger(__name__)

API_URL = "http://127.0.0.1:8000/campaign-events"
MAX_RESPONSE_BYTES = 2_000_000


def fetch_events(
    count: int,
    seed: int,
    run_id: str,
    event_date: date,
) -> list[dict]:
    params = urlencode(
        {
            "count": count,
            "seed": seed,
            "run_id": run_id,
            "event_date": event_date.isoformat(),
            "include_anomalies": "true",
        }
    )

    url = f"{API_URL}?{params}"

    LOGGER.info("Fetching source data: %s", url)

    with urlopen(url, timeout=30) as response:
        raw = response.read(MAX_RESPONSE_BYTES + 1)

    if len(raw) > MAX_RESPONSE_BYTES:
        raise ValueError("API response exceeds safety limit")

    payload = json.loads(raw)

    if payload.get("schema_version") != 1:
        raise ValueError("Unsupported schema version")

    if payload.get("run_id") != run_id:
        raise ValueError("Unexpected run ID")

    events = payload.get("events")

    if not isinstance(events, list):
        raise ValueError("Invalid API response")

    if len(events) != payload.get("record_count"):
        raise ValueError("Record count mismatch")

    if len(events) != count + 2:
        raise ValueError("Unexpected number of records")

    if not all(isinstance(event, dict) for event in events):
        raise ValueError("Invalid event structure")

    LOGGER.info("Fetched %d source records", len(events))

    return events


def to_jsonl(events: list[dict]) -> str:
    return "".join(json.dumps(event, allow_nan=False) + "\n" for event in events)


def upload_to_gcs(
    project_id: str,
    bucket_name: str,
    object_name: str,
    payload: str,
) -> str:
    client = storage.Client(project=project_id)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(object_name)

    blob.upload_from_string(
        payload,
        content_type="application/x-ndjson",
        if_generation_match=0,
        timeout=30,
    )

    uri = f"gs://{bucket_name}/{object_name}"

    LOGGER.info("Uploaded source data: %s", uri)

    return uri


def run_ingestion(
    count: int,
    seed: int,
    run_id: str,
    event_date: date,
    local_output: Path,
) -> dict:
    settings = Settings.from_env()

    if not 1 <= count <= 1000:
        raise ValueError("Record count must be between 1 and 1000")

    if not re.fullmatch(r"[a-z0-9-]{1,40}", run_id):
        raise ValueError("Invalid run ID")

    events = fetch_events(count, seed, run_id, event_date)

    payload = to_jsonl(events)

    local_output.parent.mkdir(parents=True, exist_ok=True)
    local_output.write_text(payload, encoding="utf-8")

    bucket_name = f"{settings.project_id}-{settings.environment}-raw"

    object_name = (
        f"media_events/"
        f"event_date={event_date.isoformat()}/"
        f"batch_id={run_id}/events.jsonl"
    )

    uri = upload_to_gcs(
        project_id=settings.project_id,
        bucket_name=bucket_name,
        object_name=object_name,
        payload=payload,
    )

    return {
        "status": "success",
        "run_id": run_id,
        "record_count": len(events),
        "size_bytes": len(payload.encode("utf-8")),
        "local_file": str(local_output),
        "gcs_uri": uri,
    }


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    parser = argparse.ArgumentParser(
        description="Ingest media events into Cloud Storage"
    )

    parser.add_argument("--count", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--run-id", required=True)

    parser.add_argument(
        "--event-date",
        type=date.fromisoformat,
        default=datetime.now(UTC).date(),
    )

    parser.add_argument(
        "--local-output",
        type=Path,
        default=Path("/tmp/media-batch.jsonl"),
    )

    args = parser.parse_args()

    result = run_ingestion(
        count=args.count,
        seed=args.seed,
        run_id=args.run_id,
        event_date=args.event_date,
        local_output=args.local_output,
    )

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
