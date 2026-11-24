import argparse
import logging
from datetime import UTC, datetime
from pathlib import Path

import apache_beam as beam
from apache_beam.options.pipeline_options import (
    PipelineOptions,
)
from apache_beam.runners.runner import PipelineState

from media_platform.batch import build_pipeline
from media_platform.settings import Settings


def main():
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="Media analytics batch pipeline")

    parser.add_argument("--input", required=True)
    parser.add_argument("--batch-id", required=True)
    parser.add_argument("--cloud", action="store_true")
    parser.add_argument("--job-name")
    parser.add_argument("--service-account")
    parser.add_argument("--subnetwork")
    parser.add_argument("--wheel")

    args = parser.parse_args()

    timestamp = datetime.now(UTC).isoformat()

    if args.cloud:
        settings = Settings.from_env()
        settings.require_paid_cloud_jobs()

        if settings.environment != "dev":
            raise ValueError("Only DEV deployment is allowed")

        if not all(
            [
                args.job_name,
                args.service_account,
                args.subnetwork,
                args.wheel,
            ]
        ):
            parser.error(
                "Cloud deployment requires job name, "
                "service account, subnetwork and wheel"
            )

        if not Path(args.wheel).is_file():
            raise ValueError("Application wheel not found")

        prefix = f"{settings.project_id}-{settings.environment}"

        if not args.input.startswith(f"gs://{prefix}-raw/"):
            raise ValueError("Unexpected source bucket")

        temp_location = f"gs://{prefix}-temp/dataflow"

        options = PipelineOptions(
            [
                "--runner=DataflowRunner",
                f"--project={settings.project_id}",
                f"--region={settings.region}",
                f"--job_name={args.job_name}",
                f"--temp_location={temp_location}",
                (f"--staging_location=gs://{prefix}-staging/dataflow"),
                (f"--service_account_email={args.service_account}"),
                f"--subnetwork={args.subnetwork}",
                "--machine_type=n1-standard-1",
                "--num_workers=1",
                "--max_num_workers=1",
                "--autoscaling_algorithm=NONE",
                "--disk_size_gb=25",
                f"--extra_package={args.wheel}",
            ]
        )

        pipeline = beam.Pipeline(options=options)

        build_pipeline(
            pipeline=pipeline,
            input_path=args.input,
            batch_id=args.batch_id,
            ingestion_timestamp=timestamp,
            project_id=settings.project_id,
            temp_location=temp_location,
        )

        result = pipeline.run()

        print(
            f"DATAFLOW_JOB_ID={result.job_id()}",
            flush=True,
        )

        print(
            "Job submitted. Monitor until completion.",
            flush=True,
        )

    else:
        if args.input.startswith("gs://"):
            raise ValueError("Local validation requires a local file")

        options = PipelineOptions(
            [
                "--runner=DirectRunner",
            ]
        )

        pipeline = beam.Pipeline(options=options)

        build_pipeline(
            pipeline=pipeline,
            input_path=args.input,
            batch_id=args.batch_id,
            ingestion_timestamp=timestamp,
        )

        result = pipeline.run()
        state = result.wait_until_finish()

        if state != PipelineState.DONE:
            raise RuntimeError(f"Local pipeline failed: {state}")

        print("Local Beam pipeline: SUCCESS")

        for counter in result.metrics().query()["counters"]:
            if counter.key.metric.namespace == "data_quality":
                print(
                    counter.key.metric.name,
                    counter.committed,
                )


if __name__ == "__main__":
    main()
