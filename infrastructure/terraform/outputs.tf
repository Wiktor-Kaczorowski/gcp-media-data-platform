
output "project_id" {
  description = "Target Google Cloud project."
  value       = var.project_id
}

output "region" {
  description = "Primary deployment region."
  value       = var.region
}

output "environment" {
  description = "Deployment environment."
  value       = var.environment
}

output "bigquery_location" {
  description = "BigQuery dataset location."
  value       = var.bq_location
}

output "required_services" {
  description = "Google Cloud API services managed by Terraform."
  value = sort([
    for service in google_project_service.required :
    service.service
  ])
}


output "storage_bucket_names" {
  description = "Cloud Storage bucket names by data layer."

  value = {
    for layer, bucket in google_storage_bucket.media :
    layer => bucket.name
  }
}

output "storage_bucket_uris" {
  description = "Cloud Storage URIs by data layer."

  value = {
    for layer, bucket in google_storage_bucket.media :
    layer => bucket.url
  }
}


output "bigquery_dataset_ids" {
  description = "BigQuery dataset IDs by medallion layer."

  value = {
    for layer, dataset in google_bigquery_dataset.media :
    layer => dataset.dataset_id
  }
}

output "bigquery_dataset_references" {
  description = "Fully qualified dataset references."

  value = {
    for layer, dataset in google_bigquery_dataset.media :
    layer => "${var.project_id}.${dataset.dataset_id}"
  }
}


output "pubsub_topic_names" {
  description = "Pub/Sub topic names."

  value = {
    events      = google_pubsub_topic.events.name
    dead_letter = google_pubsub_topic.dead_letter.name
  }
}

output "pubsub_topic_ids" {
  description = "Fully qualified Pub/Sub topic IDs."

  value = {
    events      = google_pubsub_topic.events.id
    dead_letter = google_pubsub_topic.dead_letter.id
  }
}

output "pubsub_subscription_names" {
  description = "Pub/Sub subscription names."

  value = {
    events      = google_pubsub_subscription.events.name
    dead_letter = google_pubsub_subscription.dead_letter.name
  }
}

output "pubsub_subscription_ids" {
  description = "Fully qualified Pub/Sub subscription IDs."

  value = {
    events      = google_pubsub_subscription.events.id
    dead_letter = google_pubsub_subscription.dead_letter.id
  }
}
