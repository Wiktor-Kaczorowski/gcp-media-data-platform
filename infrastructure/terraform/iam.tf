
# Dedicated Dataflow worker identity.

resource "google_service_account" "dataflow_worker" {
  project      = var.project_id
  account_id   = "${local.name_prefix}-dataflow-worker"
  display_name = "Media Platform Dataflow Worker"
  description  = "Worker identity for batch and streaming pipelines."

  depends_on = [
    google_project_service.required["iam.googleapis.com"]
  ]
}

# Project-level execution permissions.

resource "google_project_iam_member" "dataflow_worker_roles" {
  for_each = toset([
    "roles/dataflow.worker",
    "roles/bigquery.jobUser",
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.dataflow_worker.email}"

  depends_on = [
    google_project_service.required["dataflow.googleapis.com"]
  ]
}

# Allow the developer to submit jobs using the worker identity.

resource "google_service_account_iam_member" "dataflow_submitter" {
  service_account_id = google_service_account.dataflow_worker.name
  role               = "roles/iam.serviceAccountUser"
  member             = var.dataflow_submitter_member
}

# Resource-level Cloud Storage permissions.

locals {
  dataflow_storage_roles = {
    raw     = "roles/storage.objectViewer"
    staging = "roles/storage.objectAdmin"
    temp    = "roles/storage.objectAdmin"
  }
}

resource "google_storage_bucket_iam_member" "dataflow_worker" {
  for_each = local.dataflow_storage_roles

  bucket = google_storage_bucket.media[each.key].name
  role   = each.value
  member = "serviceAccount:${google_service_account.dataflow_worker.email}"
}

# BigQuery write access limited to the Bronze dataset.

resource "google_bigquery_dataset_iam_member" "dataflow_bronze" {
  project    = var.project_id
  dataset_id = google_bigquery_dataset.media["bronze"].dataset_id

  role   = "roles/bigquery.dataEditor"
  member = "serviceAccount:${google_service_account.dataflow_worker.email}"
}

# Consume messages from the main subscription.

resource "google_pubsub_subscription_iam_member" "dataflow_subscriber" {
  project      = var.project_id
  subscription = google_pubsub_subscription.events.name

  role   = "roles/pubsub.subscriber"
  member = "serviceAccount:${google_service_account.dataflow_worker.email}"
}

# Read subscription configuration.

resource "google_pubsub_subscription_iam_member" "dataflow_subscription_viewer" {
  project      = var.project_id
  subscription = google_pubsub_subscription.events.name

  role   = "roles/pubsub.viewer"
  member = "serviceAccount:${google_service_account.dataflow_worker.email}"
}

# Read topic configuration.

resource "google_pubsub_topic_iam_member" "dataflow_topic_viewer" {
  project = var.project_id
  topic   = google_pubsub_topic.events.name

  role   = "roles/pubsub.viewer"
  member = "serviceAccount:${google_service_account.dataflow_worker.email}"
}
