
#!/usr/bin/env bash

set -euo pipefail

cd "$(dirname "$0")/.."

PROJECT="gcp-media-data-platform"
REGION="us-central1"

if [[ "${ALLOW_PAID_CLOUD_JOBS:-false}" != "true" ]]; then
    echo "ERROR: Paid cloud jobs are disabled."
    exit 1
fi

JOB_NAME="${1:?Provide a Dataflow job name}"

ACTIVE_JOBS=$(gcloud dataflow jobs list \
    --project="$PROJECT" \
    --region="$REGION" \
    --status=active \
    --format="value(id)")

if [[ -n "$ACTIVE_JOBS" ]]; then
    echo "ERROR: Another Dataflow job is active."
    exit 1
fi

WORKER_SA=$(terraform \
    -chdir=infrastructure/terraform \
    output -raw dataflow_worker_service_account)

SUBNETWORK=$(terraform \
    -chdir=infrastructure/terraform \
    output -raw dataflow_subnetwork)

TEMPLATE="gs://dataflow-templates/latest/PubSub_Subscription_to_BigQuery"

INPUT_SUB="projects/$PROJECT/subscriptions/media-dev-events-sub"

OUTPUT_TABLE="$PROJECT:media_bronze.raw_streaming_events"

ERROR_TABLE="$PROJECT:media_bronze.streaming_error_records"

gcloud dataflow jobs run "$JOB_NAME" \
    --project="$PROJECT" \
    --region="$REGION" \
    --gcs-location="$TEMPLATE" \
    --staging-location="gs://$PROJECT-dev-staging/streaming" \
    --service-account-email="$WORKER_SA" \
    --subnetwork="$SUBNETWORK" \
    --worker-machine-type=n1-standard-2 \
    --num-workers=1 \
    --max-workers=1 \
    --enable-streaming-engine \
    --parameters="inputSubscription=$INPUT_SUB,outputTableSpec=$OUTPUT_TABLE,outputDeadletterTable=$ERROR_TABLE"

echo "Streaming job submitted: $JOB_NAME"
echo "IMPORTANT: Stop the job after validation."
