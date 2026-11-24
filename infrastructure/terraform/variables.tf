
variable "project_id" {
  description = "Google Cloud project ID."
  type        = string

  validation {
    condition = can(regex(
      "^[a-z][a-z0-9-]{4,28}[a-z0-9]$",
      var.project_id
    ))

    error_message = "A valid GCP project ID is required."
  }
}

variable "region" {
  description = "Primary Google Cloud deployment region."
  type        = string
  default     = "us-central1"

  validation {
    condition = contains(
      ["us-central1", "us-east1", "us-west1"],
      var.region
    )

    error_message = "Region must be an approved US region."
  }
}

variable "environment" {
  description = "Deployment environment."
  type        = string
  default     = "dev"

  validation {
    condition = contains(
      ["dev", "test", "prod"],
      var.environment
    )

    error_message = "Environment must be dev, test or prod."
  }
}

variable "bq_location" {
  description = "BigQuery dataset location."
  type        = string
  default     = "us-central1"

  validation {
    condition     = var.bq_location == var.region
    error_message = "BigQuery location must match the GCP region."
  }
}

variable "dataflow_submitter_member" {
  description = "IAM principal allowed to run jobs as the Dataflow worker."
  type        = string

  validation {
    condition = can(regex(
      "^(user|serviceAccount):[^@]+@[^@]+$",
      var.dataflow_submitter_member
    ))

    error_message = "Provide a valid IAM user or service account principal."
  }
}
