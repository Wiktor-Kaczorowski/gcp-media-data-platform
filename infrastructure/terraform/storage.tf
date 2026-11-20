
locals {
  storage_buckets = {
    raw = {
      lifecycle_age_days  = 30
      soft_delete_seconds = 604800
    }

    staging = {
      lifecycle_age_days  = 7
      soft_delete_seconds = 0
    }

    temp = {
      lifecycle_age_days  = 3
      soft_delete_seconds = 0
    }
  }
}

resource "google_storage_bucket" "media" {
  for_each = local.storage_buckets

  name          = "${var.project_id}-${var.environment}-${each.key}"
  project       = var.project_id
  location      = upper(var.region)
  storage_class = "STANDARD"

  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"

  force_destroy = false

  labels = merge(local.common_labels, {
    layer = each.key
  })

  versioning {
    enabled = false
  }

  soft_delete_policy {
    retention_duration_seconds = each.value.soft_delete_seconds
  }

  lifecycle_rule {
    condition {
      age = each.value.lifecycle_age_days
    }

    action {
      type = "Delete"
    }
  }

  depends_on = [
    google_project_service.required["storage.googleapis.com"]
  ]
}
