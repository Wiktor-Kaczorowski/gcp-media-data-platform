
# Retrieve the GCP project number for service agent IAM.

data "google_project" "current" {
  project_id = var.project_id
}

locals {
  pubsub_service_agent = "service-${data.google_project.current.number}@gcp-sa-pubsub.iam.gserviceaccount.com"
}

# Main and dead-letter topics.

resource "google_pubsub_topic" "events" {
  project = var.project_id
  name    = "${local.name_prefix}-events"

  labels = merge(local.common_labels, {
    component = "streaming"
    type      = "main"
  })

  message_storage_policy {
    allowed_persistence_regions = [var.region]
  }

  depends_on = [
    google_project_service.required["pubsub.googleapis.com"]
  ]
}

resource "google_pubsub_topic" "dead_letter" {
  project = var.project_id
  name    = "${local.name_prefix}-events-dlq"

  labels = merge(local.common_labels, {
    component = "streaming"
    type      = "dead-letter"
  })

  message_storage_policy {
    allowed_persistence_regions = [var.region]
  }

  depends_on = [
    google_project_service.required["pubsub.googleapis.com"]
  ]
}


# Main pull subscription.

resource "google_pubsub_subscription" "events" {
  project = var.project_id
  name    = "${local.name_prefix}-events-sub"
  topic   = google_pubsub_topic.events.id

  ack_deadline_seconds       = 30
  message_retention_duration = "86400s"
  retain_acked_messages      = false

  enable_message_ordering      = false
  enable_exactly_once_delivery = false

  expiration_policy {
    ttl = ""
  }

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "60s"
  }

  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.dead_letter.id
    max_delivery_attempts = 5
  }

  labels = merge(local.common_labels, {
    component = "streaming"
    type      = "main"
  })

  depends_on = [
    google_pubsub_topic_iam_member.dead_letter_publisher,
    google_pubsub_subscription.dead_letter,
  ]
}

# Dead-letter pull subscription.

resource "google_pubsub_subscription" "dead_letter" {
  project = var.project_id
  name    = "${local.name_prefix}-events-dlq-sub"
  topic   = google_pubsub_topic.dead_letter.id

  ack_deadline_seconds       = 30
  message_retention_duration = "86400s"
  retain_acked_messages      = false

  expiration_policy {
    ttl = ""
  }

  labels = merge(local.common_labels, {
    component = "streaming"
    type      = "dead-letter"
  })
}


# Allow the Pub/Sub service agent to publish failed
# messages to the dead-letter topic.

resource "google_pubsub_topic_iam_member" "dead_letter_publisher" {
  project = var.project_id
  topic   = google_pubsub_topic.dead_letter.name

  role   = "roles/pubsub.publisher"
  member = "serviceAccount:${local.pubsub_service_agent}"
}

# Allow the Pub/Sub service agent to acknowledge messages
# on the source subscription when forwarding them.

resource "google_pubsub_subscription_iam_member" "dead_letter_subscriber" {
  project      = var.project_id
  subscription = google_pubsub_subscription.events.name

  role   = "roles/pubsub.subscriber"
  member = "serviceAccount:${local.pubsub_service_agent}"
}
