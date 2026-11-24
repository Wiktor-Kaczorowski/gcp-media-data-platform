import os
from datetime import timedelta
from pathlib import Path

import pendulum
from airflow import DAG
from airflow.models.param import Param
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import BranchPythonOperator

ROOT = Path(__file__).resolve().parents[1]


def choose_mode(**context):
    mode = context["params"]["mode"]

    if mode == "refresh":
        return "use_existing_bronze"

    if mode == "full":
        if os.environ.get("ALLOW_PAID_CLOUD_JOBS") != "true":
            raise ValueError("Paid Dataflow jobs are disabled")

        return "ingest_media_data"

    raise ValueError("Unsupported execution mode")


with DAG(
    dag_id="media_batch_pipeline",
    description="Media analytics batch orchestration",
    start_date=pendulum.datetime(2026, 11, 24, tz="UTC"),
    schedule=None,
    catchup=False,
    max_active_runs=1,
    default_args={
        "owner": "data-engineering",
        "retries": 1,
        "retry_delay": timedelta(seconds=30),
        "execution_timeout": timedelta(minutes=5),
    },
    params={
        "mode": Param(
            "refresh",
            type="string",
            enum=["refresh", "full"],
        )
    },
    tags=["gcp", "dataflow", "bigquery", "media"],
) as dag:
    execution_mode = BranchPythonOperator(
        task_id="choose_execution_mode",
        python_callable=choose_mode,
        retries=0,
    )

    existing_bronze = EmptyOperator(task_id="use_existing_bronze")

    ingest = BashOperator(
        task_id="ingest_media_data",
        cwd=str(ROOT),
        bash_command=(
            "set -e; "
            ".venv/bin/python -m media_platform.ingestion "
            "--count 20 "
            "--seed 123 "
            '--run-id "$BATCH_ID" '
            '--event-date "$EVENT_DATE" '
            '--local-output "/tmp/media-$BATCH_ID.jsonl"'
        ),
        env={
            "BATCH_ID": "af-{{ ts_nodash | lower }}",
            "EVENT_DATE": "{{ ds }}",
        },
        append_env=True,
        retries=0,
    )

    dataflow = BashOperator(
        task_id="run_dataflow_batch",
        cwd=str(ROOT),
        bash_command=('bash scripts/run_airflow_batch.sh "$BATCH_ID" "$EVENT_DATE"'),
        env={
            "BATCH_ID": "af-{{ ts_nodash | lower }}",
            "EVENT_DATE": "{{ ds }}",
        },
        append_env=True,
        retries=0,
        execution_timeout=timedelta(minutes=35),
    )

    silver = BashOperator(
        task_id="transform_silver",
        cwd=str(ROOT),
        bash_command="bash scripts/run_sql.sh silver",
        trigger_rule="none_failed_min_one_success",
    )

    gold = BashOperator(
        task_id="build_gold_models",
        cwd=str(ROOT),
        bash_command="bash scripts/run_sql.sh gold",
    )

    quality = BashOperator(
        task_id="validate_data_quality",
        cwd=str(ROOT),
        bash_command="bash scripts/run_sql.sh quality",
    )

    execution_mode >> existing_bronze >> silver

    execution_mode >> ingest >> dataflow >> silver

    silver >> gold >> quality
