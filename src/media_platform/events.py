import math
import random
import re
from datetime import UTC, date, datetime, timedelta

CAMPAIGNS = (
    ("CAM-001", "Brand A", "google_ads", "PL"),
    ("CAM-002", "Brand A", "meta_ads", "DE"),
    ("CAM-003", "Brand B", "youtube_ads", "GB"),
    ("CAM-004", "Brand B", "google_ads", "US"),
    ("CAM-005", "Brand C", "tiktok_ads", "PL"),
    ("CAM-006", "Brand C", "meta_ads", "FR"),
)

REQUIRED_FIELDS = (
    "event_id",
    "event_timestamp",
    "campaign_id",
    "brand",
    "platform",
    "country",
    "impressions",
    "clicks",
    "conversions",
    "spend",
    "revenue",
)

MAX_RECORDS = 1000


def generate_events(
    count: int = 1000,
    seed: int = 42,
    run_id: str = "demo",
    event_date: date | None = None,
    include_anomalies: bool = True,
) -> list[dict]:
    """Generate reproducible synthetic media performance events."""
    if not 1 <= count <= MAX_RECORDS:
        raise ValueError("Invalid record count")

    if not re.fullmatch(r"[a-z0-9-]{1,40}", run_id):
        raise ValueError("Invalid run ID")

    rng = random.Random(seed)

    day = event_date or datetime.now(UTC).date()
    base_time = datetime(day.year, day.month, day.day, tzinfo=UTC)

    events = []

    for i in range(count):
        campaign, brand, platform, country = rng.choice(CAMPAIGNS)

        impressions = rng.randint(100, 10000)
        clicks = int(impressions * rng.uniform(0.01, 0.12))
        conversions = int(clicks * rng.uniform(0.01, 0.15))

        spend = round(clicks * rng.uniform(0.2, 2.5), 2)
        revenue = round(conversions * rng.uniform(20, 150), 2)

        event_time = base_time + timedelta(seconds=rng.randint(0, 86399))

        events.append(
            {
                "event_id": f"{run_id}-{i:06d}",
                "event_timestamp": event_time.isoformat(),
                "campaign_id": campaign,
                "brand": brand,
                "platform": platform,
                "country": country,
                "impressions": impressions,
                "clicks": clicks,
                "conversions": conversions,
                "spend": spend,
                "revenue": revenue,
            }
        )

    if include_anomalies:
        # Duplicate business event.
        events.append(events[0].copy())

        # Invalid event for data quality testing.
        invalid = events[0].copy()
        invalid["event_id"] = f"{run_id}-invalid"
        invalid["spend"] = -100.0
        events.append(invalid)

    return events


def validate_event(event: dict) -> None:
    """Raise ValueError when an event violates quality rules."""
    if not isinstance(event, dict):
        raise ValueError("Event must be a JSON object")

    missing = [field for field in REQUIRED_FIELDS if field not in event]

    if missing:
        raise ValueError(f"Missing fields: {missing}")

    for field in (
        "event_id",
        "event_timestamp",
        "campaign_id",
        "brand",
        "platform",
        "country",
    ):
        if not isinstance(event[field], str) or not event[field]:
            raise ValueError(f"Invalid field: {field}")

    timestamp = datetime.fromisoformat(event["event_timestamp"])

    if timestamp.tzinfo is None:
        raise ValueError("Timestamp must include timezone")

    for field in ("impressions", "clicks", "conversions"):
        value = event[field]

        if type(value) is not int or value < 0:
            raise ValueError(f"Invalid metric: {field}")

    for field in ("spend", "revenue"):
        value = event[field]

        if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
            raise ValueError(f"Invalid metric: {field}")

    if event["clicks"] > event["impressions"]:
        raise ValueError("Clicks exceed impressions")

    if event["conversions"] > event["clicks"]:
        raise ValueError("Conversions exceed clicks")
