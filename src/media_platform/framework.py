import argparse
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Literal
from uuid import uuid4

import apache_beam as beam
import yaml
from apache_beam.options.pipeline_options import PipelineOptions
from google.cloud import bigquery
from pydantic import BaseModel, ConfigDict, Field

from media_platform.batch import EVENT_SCHEMA, build_pipeline
from media_platform.ingestion import (
    fetch_events,
    to_jsonl,
    upload_to_gcs,
)
from media_platform.settings import Settings

LOGGER = logging.getLogger(__name__)


# Strict, declarative configuration models.


class StrictModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
    )


class PipelineDefinition(StrictModel):
    name: str = Field(pattern=r"^[a-z0-9-]{1,40}$")
    version: Literal[1]


class SourceConfig(StrictModel):
    type: Literal["rest_api"]
    endpoint: Literal["/campaign-events"]
    count: int = Field(ge=1, le=100)
    seed: int = Field(ge=0, le=100000)


class TargetConfig(StrictModel):
    type: Literal["bigquery"]
    dataset: Literal["media_bronze"]
    table: Literal["citizen_demo_events"]


class QualityConfig(StrictModel):
    max_invalid_records: int = Field(ge=0, le=5)
    max_duplicate_records: int = Field(ge=0, le=5)


class ExecutionConfig(StrictModel):
    mode: Literal["preview", "publish"]
    runner: Literal["DirectRunner"]
    max_workers: Literal[1]


class PipelineConfig(StrictModel):
    pipeline: PipelineDefinition
    source: SourceConfig
    target: TargetConfig
    quality: QualityConfig
    execution: ExecutionConfig


def load_config(path: Path) -> PipelineConfig:
    """Load and validate an approved YAML configuration."""

    if path.stat().st_size > 16384:
        raise ValueError("Configuration exceeds size limit")

    payload = yaml.safe_load(path.read_text(encoding="utf-8"))

    return PipelineConfig.model_validate(payload)


def read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def check_quality(
    valid_records: list[dict],
    invalid_records: list[dict],
    config: QualityConfig,
) -> dict:
    """Enforce quality thresholds before publishing data."""

    unique_ids = {record["event_id"] for record in valid_records}

    duplicates = len(valid_records) - len(unique_ids)

    if not valid_records:
        raise ValueError("No valid records produced")

    if len(invalid_records) > config.max_invalid_records:
        raise ValueError("Invalid record threshold exceeded")

    if duplicates > config.max_duplicate_records:
        raise ValueError("Duplicate threshold exceeded")

    return {
        "status": "PASS",
        "valid_records": len(valid_records),
        "invalid_records": len(invalid_records),
        "duplicate_records": duplicates,
        "unique_events": len(unique_ids),
    }


def publish_to_bigquery(
    path: Path,
    config: PipelineConfig,
    settings: Settings,
) -> dict:
    """Publish a validated snapshot to the approved demo table."""

    destination = f"{settings.project_id}.{config.target.dataset}.{config.target.table}"

    schema = [
        bigquery.SchemaField(*field.split(":", 1)) for field in EVENT_SCHEMA.split(",")
    ]

    job_config = bigquery.LoadJobConfig(
        schema=schema,
        source_format=(bigquery.SourceFormat.NEWLINE_DELIMITED_JSON),
        write_disposition=(bigquery.WriteDisposition.WRITE_TRUNCATE),
        create_disposition=(bigquery.CreateDisposition.CREATE_IF_NEEDED),
        max_bad_records=0,
    )

    client = bigquery.Client(project=settings.project_id)

    with path.open("rb") as data:
        job = client.load_table_from_file(
            data,
            destination,
            location=settings.region,
            job_config=job_config,
        )

        job.result(timeout=120)

    return {
        "destination": destination,
        "job_id": job.job_id,
        "loaded_rows": job.output_rows,
    }


def run_pipeline(
    config: PipelineConfig,
    allow_publish: bool = False,
) -> dict:
    """Execute the approved reusable pipeline."""

    mode = config.execution.mode

    if mode == "publish" and not allow_publish:
        raise ValueError("Publishing requires explicit --publish flag")

    settings = None

    if mode == "publish":
        settings = Settings.from_env()

        if settings.environment != "dev":
            raise ValueError("Only DEV publishing is allowed")

    run_id = f"citizen-{uuid4().hex[:16]}"
    timestamp = datetime.now(UTC)
    event_date = timestamp.date()

    LOGGER.info(
        "Starting pipeline %s in %s mode",
        config.pipeline.name,
        mode,
    )

    events = fetch_events(
        count=config.source.count,
        seed=config.source.seed,
        run_id=run_id,
        event_date=event_date,
    )

    payload = to_jsonl(events)

    with TemporaryDirectory(prefix="media-citizen-") as directory:
        workspace = Path(directory)

        input_file = workspace / "input.jsonl"
        input_file.write_text(
            payload,
            encoding="utf-8",
        )

        output_prefix = workspace / "processed"

        options = PipelineOptions(
            [
                "--runner=DirectRunner",
            ]
        )

        with beam.Pipeline(options=options) as pipeline:
            build_pipeline(
                pipeline=pipeline,
                input_path=str(input_file),
                batch_id=run_id,
                ingestion_timestamp=timestamp.isoformat(),
                local_output=str(output_prefix),
            )

        valid_file = Path(f"{output_prefix}-valid.jsonl")

        invalid_file = Path(f"{output_prefix}-invalid.jsonl")

        valid_records = read_jsonl(valid_file)
        invalid_records = read_jsonl(invalid_file)

        if len(valid_records) + len(invalid_records) != len(events):
            raise ValueError("Record count reconciliation failed")

        quality = check_quality(
            valid_records,
            invalid_records,
            config.quality,
        )

        result = {
            "status": "success",
            "pipeline": config.pipeline.name,
            "run_id": run_id,
            "mode": mode,
            "runner": config.execution.runner,
            "input_records": len(events),
            "quality": quality,
            "gcp_publish": False,
        }

        if mode == "publish":
            bucket = f"{settings.project_id}-{settings.environment}-raw"

            object_name = (
                f"citizen/events/"
                f"event_date={event_date.isoformat()}/"
                f"batch_id={run_id}/events.jsonl"
            )

            result["gcs_uri"] = upload_to_gcs(
                project_id=settings.project_id,
                bucket_name=bucket,
                object_name=object_name,
                payload=payload,
            )

            result["bigquery"] = publish_to_bigquery(
                path=valid_file,
                config=config,
                settings=settings,
            )

            result["gcp_publish"] = True

        return result


def main():
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="Citizen Developer Pipeline Framework")

    parser.add_argument(
        "--config",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--validate-only",
        action="store_true",
    )

    parser.add_argument(
        "--publish",
        action="store_true",
    )

    args = parser.parse_args()

    config = load_config(args.config)

    if args.validate_only:
        print(
            json.dumps(
                {
                    "status": "CONFIG_VALID",
                    "configuration": config.model_dump(),
                },
                indent=2,
            )
        )

        return

    result = run_pipeline(
        config,
        allow_publish=args.publish,
    )

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
