from datetime import UTC, date, datetime
from typing import Annotated

from fastapi import FastAPI, Query

from media_platform.events import generate_events

app = FastAPI(
    title="Media Analytics Source API",
    description="Synthetic advertising performance data.",
    version="1.0.0",
)


@app.get("/health")
def health() -> dict:
    return {
        "status": "healthy",
        "service": "media-source-api",
    }


@app.get("/campaign-events")
def campaign_events(
    count: Annotated[int, Query(ge=1, le=1000)] = 1000,
    seed: int = 42,
    run_id: Annotated[str, Query(pattern=r"^[a-z0-9-]{1,40}$")] = "demo",
    event_date: date | None = None,
    include_anomalies: bool = True,
) -> dict:
    events = generate_events(
        count=count,
        seed=seed,
        run_id=run_id,
        event_date=event_date or datetime.now(UTC).date(),
        include_anomalies=include_anomalies,
    )

    return {
        "source": "media-source-api",
        "schema_version": 1,
        "run_id": run_id,
        "record_count": len(events),
        "events": events,
    }
