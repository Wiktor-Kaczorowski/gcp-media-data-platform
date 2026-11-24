import json

import apache_beam as beam
from apache_beam.metrics import Metrics
from apache_beam.pvalue import TaggedOutput

from media_platform.events import REQUIRED_FIELDS, validate_event

EVENT_SCHEMA = (
    "event_id:STRING,"
    "event_timestamp:TIMESTAMP,"
    "campaign_id:STRING,"
    "brand:STRING,"
    "platform:STRING,"
    "country:STRING,"
    "impressions:INTEGER,"
    "clicks:INTEGER,"
    "conversions:INTEGER,"
    "spend:FLOAT,"
    "revenue:FLOAT,"
    "batch_id:STRING,"
    "ingestion_timestamp:TIMESTAMP,"
    "source:STRING"
)

REJECTED_SCHEMA = (
    "raw_record:STRING,"
    "error_reason:STRING,"
    "batch_id:STRING,"
    "ingestion_timestamp:TIMESTAMP"
)


class ParseAndValidate(beam.DoFn):
    """Parse, validate and enrich source records."""

    def __init__(
        self,
        batch_id: str,
        ingestion_timestamp: str,
    ):
        self.batch_id = batch_id
        self.ingestion_timestamp = ingestion_timestamp

        self.received = Metrics.counter("data_quality", "received_records")
        self.valid = Metrics.counter("data_quality", "valid_records")
        self.invalid = Metrics.counter("data_quality", "invalid_records")

    def process(self, line):
        self.received.inc()

        try:
            event = json.loads(line)
            validate_event(event)

            record = {field: event[field] for field in REQUIRED_FIELDS}

        except (ValueError, TypeError, OverflowError) as exc:
            self.invalid.inc()

            yield TaggedOutput(
                "invalid",
                {
                    "raw_record": line,
                    "error_reason": str(exc),
                    "batch_id": self.batch_id,
                    "ingestion_timestamp": (self.ingestion_timestamp),
                },
            )

            return

        record["batch_id"] = self.batch_id
        record["ingestion_timestamp"] = self.ingestion_timestamp
        record["source"] = "batch"

        self.valid.inc()

        yield record


def build_pipeline(
    pipeline,
    input_path: str,
    batch_id: str,
    ingestion_timestamp: str,
    project_id: str | None = None,
    temp_location: str | None = None,
    local_output: str = "/tmp/media-beam",
):
    """Build a pipeline with local or BigQuery output."""

    records = (
        pipeline
        | "Read source JSONL" >> beam.io.ReadFromText(input_path)
        | "Parse and validate"
        >> beam.ParDo(
            ParseAndValidate(
                batch_id,
                ingestion_timestamp,
            )
        ).with_outputs("invalid", main="valid")
    )

    if project_id:
        records.valid | "Write valid events" >> (
            beam.io.WriteToBigQuery(
                table=(f"{project_id}:media_bronze.raw_batch_events"),
                schema=EVENT_SCHEMA,
                create_disposition="CREATE_IF_NEEDED",
                write_disposition="WRITE_APPEND",
                method="FILE_LOADS",
                custom_gcs_temp_location=temp_location,
                additional_bq_parameters={
                    "timePartitioning": {
                        "type": "DAY",
                        "field": "event_timestamp",
                    },
                    "clustering": {
                        "fields": [
                            "campaign_id",
                            "platform",
                        ]
                    },
                },
            )
        )

        records.invalid | "Write rejected events" >> (
            beam.io.WriteToBigQuery(
                table=(f"{project_id}:media_bronze.rejected_events"),
                schema=REJECTED_SCHEMA,
                create_disposition="CREATE_IF_NEEDED",
                write_disposition="WRITE_APPEND",
                method="FILE_LOADS",
                custom_gcs_temp_location=temp_location,
            )
        )

    else:
        (
            records.valid
            | "Serialize valid records" >> beam.Map(json.dumps)
            | "Write local valid records"
            >> beam.io.WriteToText(
                f"{local_output}-valid.jsonl",
                num_shards=1,
                shard_name_template="",
            )
        )

        (
            records.invalid
            | "Serialize rejected records" >> beam.Map(json.dumps)
            | "Write local rejected records"
            >> beam.io.WriteToText(
                f"{local_output}-invalid.jsonl",
                num_shards=1,
                shard_name_template="",
            )
        )
