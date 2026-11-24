
#!/usr/bin/env bash

set -euo pipefail

cd "$(dirname "$0")/.."

PROJECT="gcp-media-data-platform"
REGION="us-central1"

if [[ "${ALLOW_PAID_CLOUD_JOBS:-false}" != "true" ]]; then
    echo "ERROR: Paid cloud jobs are disabled."
    exit 1
fi

BATCH_ID="${1:?Batch ID required}"
EVENT_DATE="${2:?Event date required}"

JOB_NAME="media-$BATCH_ID"

if [[ ! "$BATCH_ID" =~ ^[a-z0-9-]{1,40}$ ]]; then
    echo "ERROR: Invalid batch ID."
    exit 1
fi

ACTIVE_JOBS=$(gcloud dataflow jobs list \
    --project="$PROJECT" \
    --region="$REGION" \
    --status=active \
    --format="value(id)")

if [[ -n "$ACTIVE_JOBS" ]]; then
    echo "ERROR: Another Dataflow job is active."
    exit 1
fi

find_job() {
    gcloud dataflow jobs list \
        --project="$PROJECT" \
        --region="$REGION" \
        --filter="name=$JOB_NAME" \
        --format="value(id)" \
        --limit=1
}

if [[ -n "$(find_job)" ]]; then
    echo "ERROR: Job name already exists."
    exit 1
fi

RAW_URI="gs://$PROJECT-dev-raw/media_events/event_date=$EVENT_DATE/batch_id=$BATCH_ID/events.jsonl"

WORKER_SA=$(terraform \
    -chdir=infrastructure/terraform \
    output -raw dataflow_worker_service_account)

SUBNETWORK=$(terraform \
    -chdir=infrastructure/terraform \
    output -raw dataflow_subnetwork)

DIST_DIR=$(mktemp -d)
SUBMITTED=false

cleanup() {
    local exit_code=$?

    trap - EXIT

    if [[ "$exit_code" != "0" && "$SUBMITTED" == "true" ]]; then
        echo "ERROR: Checking for unfinished Dataflow job."

        local job_id
        job_id=$(find_job) || job_id=""

        if [[ -n "$job_id" ]]; then
            gcloud dataflow jobs cancel "$job_id" \
                --project="$PROJECT" \
                --region="$REGION" || true
        fi

        echo "Verify active Dataflow jobs manually."
    fi

    rm -rf "$DIST_DIR"

    exit "$exit_code"
}

trap cleanup EXIT
trap 'exit 143' TERM
trap 'exit 130' INT

.venv/bin/python -m pip wheel \
    --no-deps \
    --wheel-dir "$DIST_DIR" \
    .

WHEEL=$(find "$DIST_DIR" \
    -maxdepth 1 \
    -name '*.whl' \
    -print -quit)

SUBMITTED=true

timeout 8m .venv/bin/python scripts/run_batch.py \
    --cloud \
    --input "$RAW_URI" \
    --batch-id "$BATCH_ID" \
    --job-name "$JOB_NAME" \
    --service-account "$WORKER_SA" \
    --subnetwork "$SUBNETWORK" \
    --wheel "$WHEEL"

JOB_ID=$(find_job)

if [[ -z "$JOB_ID" ]]; then
    echo "ERROR: Dataflow job ID not found."
    exit 1
fi

echo "DATAFLOW_JOB_ID=$JOB_ID"

DEADLINE=$((SECONDS + 1200))

while (( SECONDS < DEADLINE )); do
    STATE=$(gcloud dataflow jobs describe "$JOB_ID" \
        --project="$PROJECT" \
        --region="$REGION" \
        --format="value(currentState)")

    echo "Dataflow state: $STATE"

    case "$STATE" in
        JOB_STATE_DONE)
            echo "Dataflow batch completed successfully."
            exit 0
            ;;
        JOB_STATE_FAILED|JOB_STATE_CANCELLED|JOB_STATE_DRAINED|JOB_STATE_UPDATED)
            echo "ERROR: Unexpected terminal state."
            exit 1
            ;;
    esac

    sleep 20
done

echo "ERROR: Dataflow monitoring timeout."
exit 1
