
# Docker artifact repository.

resource "google_artifact_registry_repository" "images" {
  project       = var.project_id
  location      = var.region
  repository_id = "${local.name_prefix}-images"

  description = "Media platform Docker images"
  format      = "DOCKER"

  labels = local.common_labels

  depends_on = [
    google_project_service.required["artifactregistry.googleapis.com"]
  ]
}

# Dedicated Cloud Build identity.

resource "google_service_account" "cloud_build" {
  project      = var.project_id
  account_id   = "${local.name_prefix}-cloud-build"
  display_name = "Media Platform Cloud Build"

  depends_on = [
    google_project_service.required["iam.googleapis.com"],
    google_project_service.required["cloudbuild.googleapis.com"]
  ]
}

# Allow publishing images to the approved repository.

resource "google_artifact_registry_repository_iam_member" "build_writer" {
  project    = var.project_id
  location   = google_artifact_registry_repository.images.location
  repository = google_artifact_registry_repository.images.repository_id

  role   = "roles/artifactregistry.writer"
  member = "serviceAccount:${google_service_account.cloud_build.email}"
}

# Allow reading staged source archives.

resource "google_storage_bucket_iam_member" "build_source_reader" {
  bucket = google_storage_bucket.media["staging"].name

  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.cloud_build.email}"
}

# Send build logs to Cloud Logging.

resource "google_project_iam_member" "build_logging" {
  project = var.project_id
  role    = "roles/logging.logWriter"

  member = "serviceAccount:${google_service_account.cloud_build.email}"
}

# Allow the developer to submit builds.

resource "google_service_account_iam_member" "build_submitter" {
  service_account_id = google_service_account.cloud_build.name

  role   = "roles/iam.serviceAccountUser"
  member = var.dataflow_submitter_member
}
