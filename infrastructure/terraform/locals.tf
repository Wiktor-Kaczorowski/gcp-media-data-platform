
locals {
  name_prefix = "media-${var.environment}"

  common_labels = {
    project     = "media-data-platform"
    environment = var.environment
    managed_by  = "terraform"
    purpose     = "portfolio"
  }
}
