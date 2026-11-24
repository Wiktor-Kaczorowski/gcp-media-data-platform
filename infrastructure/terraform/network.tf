
# Dedicated VPC for Dataflow workers.

resource "google_compute_network" "dataflow" {
  project = var.project_id
  name    = "${local.name_prefix}-vpc"

  auto_create_subnetworks = false
  routing_mode            = "REGIONAL"

  depends_on = [
    google_project_service.required["compute.googleapis.com"]
  ]
}

# Regional subnet with Private Google Access.

resource "google_compute_subnetwork" "dataflow" {
  project = var.project_id
  name    = "${local.name_prefix}-dataflow-subnet"
  region  = var.region

  network                  = google_compute_network.dataflow.id
  ip_cidr_range            = "10.42.0.0/24"
  private_ip_google_access = true
}

# Internal communication between Dataflow workers.

resource "google_compute_firewall" "dataflow_internal" {
  project = var.project_id
  name    = "${local.name_prefix}-dataflow-internal"

  network   = google_compute_network.dataflow.id
  direction = "INGRESS"
  priority  = 1000

  source_service_accounts = [
    google_service_account.dataflow_worker.email
  ]

  target_service_accounts = [
    google_service_account.dataflow_worker.email
  ]

  allow {
    protocol = "tcp"
    ports    = ["12345", "12346"]
  }
}
