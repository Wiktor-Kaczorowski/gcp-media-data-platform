
locals {
  bigquery_datasets = {
    bronze = {
      description     = "Raw media data ingested from source systems."
      expiration_days = 30
    }

    silver = {
      description     = "Validated, standardized and deduplicated media data."
      expiration_days = 60
    }

    gold = {
      description     = "Business-ready media analytics and reporting models."
      expiration_days = 90
    }
  }
}

resource "google_bigquery_dataset" "media" {
  for_each = local.bigquery_datasets

  project    = var.project_id
  dataset_id = "media_${each.key}"
  location   = var.bq_location

  friendly_name = "Media ${title(each.key)}"
  description   = each.value.description

  default_table_expiration_ms = (
    each.value.expiration_days * 24 * 60 * 60 * 1000
  )

  delete_contents_on_destroy = false

  labels = merge(local.common_labels, {
    layer = each.key
  })

  lifecycle {
    prevent_destroy = true
  }

  depends_on = [
    google_project_service.required["bigquery.googleapis.com"],
    google_project_service.required["cloudresourcemanager.googleapis.com"],
  ]
}
